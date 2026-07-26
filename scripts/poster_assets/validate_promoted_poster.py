#!/usr/bin/env python3
"""Validate a promoted poster bundle against provenance and print geometry."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image

try:
    from .layout import build_print_layout, effective_dpi
    from .poster_config import build_identity_lock_prompt
    from .provenance import ROOT, sha256_file
    from .poster_io import (
        PosterBundle,
        load_poster_scope_data,
        poster_bundle,
        poster_bundles_for_scope,
    )
except ImportError:
    from layout import build_print_layout, effective_dpi
    from poster_config import build_identity_lock_prompt
    from provenance import ROOT, sha256_file
    from poster_io import (
        PosterBundle,
        load_poster_scope_data,
        poster_bundle,
        poster_bundles_for_scope,
    )


POSTER_ASSETS = ROOT / "data" / "poster_assets"
REQUIRED_GENERATION_HASHES = (
    "model_sha256",
    "encoder_sha256",
    "vae_sha256",
    "upscale_model_sha256",
)
POSTER_LANGUAGES = (
    "de",
    "en",
    "fr",
    "es",
    "it",
    "ja",
    "ko",
    "zh_hans",
    "zh_hant",
)


def enabled_poster_bundles(
    poster_assets: Path = POSTER_ASSETS,
) -> list[PosterBundle]:
    """Return every PDF-enabled bundle with its resolved routing intact."""
    enabled: list[PosterBundle] = []
    for scope_dir in sorted(
        (path for path in poster_assets.iterdir() if path.is_dir()),
        key=lambda path: path.name,
    ):
        for bundle in poster_bundles_for_scope(
            scope_dir.name,
            poster_assets=poster_assets,
        ):
            if bundle.pdf_enabled:
                enabled.append(bundle)
    return enabled


def enabled_poster_scopes(
    poster_assets: Path = POSTER_ASSETS,
) -> list[str]:
    """Return stable asset keys for every PDF-enabled poster bundle."""
    return [
        bundle.asset_key
        for bundle in enabled_poster_bundles(poster_assets)
    ]


def _validate_record(record: dict[str, Any]) -> Path:
    path = ROOT / str(record["file"])
    if not path.is_file():
        raise FileNotFoundError(path)
    actual_hash = sha256_file(path)
    if actual_hash != record.get("sha256"):
        raise ValueError(
            f"Hash mismatch for {path}: {actual_hash} != {record.get('sha256')}"
        )
    if path.stat().st_size != record.get("bytes"):
        raise ValueError(f"Size mismatch for {path}")
    if "width" in record or "height" in record:
        with Image.open(path) as image:
            if image.size != (record.get("width"), record.get("height")):
                raise ValueError(
                    f"Dimension mismatch for {path}: {image.size} != "
                    f"{(record.get('width'), record.get('height'))}"
                )
    return path


def _image_dpi(path: Path) -> tuple[float, float]:
    with Image.open(path) as image:
        dpi = image.info.get("dpi")
    if not dpi:
        raise ValueError(f"Missing print dpi metadata: {path}")
    return float(dpi[0]), float(dpi[1])


def _validate_section_source(
    bundle,
    scope_data: dict[str, Any],
) -> None:
    """Keep enabled aggregate overlays and cutouts bound to current source data."""
    if bundle.section_id is None:
        return
    section = next(iter(scope_data.get("sections", {}).values()))
    featured = section.get("featured_elements")
    if not isinstance(featured, list) or not featured:
        raise ValueError(
            f"{bundle.asset_key} source section has no featured_elements"
        )
    expected_ids = [item.get("pokemon_id") for item in featured]
    if (
        any(not isinstance(pokemon_id, int) for pokemon_id in expected_ids)
        or len(set(expected_ids)) != len(expected_ids)
    ):
        raise ValueError(
            f"{bundle.asset_key} source featured_elements are invalid"
        )
    cutout_manifest_path = bundle.asset_dir / "cutouts" / "manifest.json"
    cutout_manifest = json.loads(
        cutout_manifest_path.read_text(encoding="utf-8")
    )
    actual_ids = [
        item.get("pokemon_id")
        for item in cutout_manifest.get("items", [])
    ]
    if actual_ids != expected_ids:
        raise ValueError(
            f"{bundle.asset_key} cutouts {actual_ids} do not match current "
            f"featured_elements {expected_ids}"
        )
    if bundle.scope == "Pokedex":
        for field in ("title", "subtitle", "description"):
            localized = section.get(field)
            missing = [
                language
                for language in POSTER_LANGUAGES
                if not isinstance(localized, dict)
                or not localized.get(language)
            ]
            if missing:
                raise ValueError(
                    f"{bundle.asset_key} lacks {field} translations for "
                    f"{', '.join(missing)}"
                )


def validate(target: str | PosterBundle) -> dict[str, Any]:
    bundle = (
        poster_bundle(target, poster_assets=POSTER_ASSETS)
        if isinstance(target, str)
        else target
    )
    scope = bundle.asset_key
    scope_dir = bundle.asset_dir
    manifest_path = bundle.manifest_path
    manifest = bundle.manifest
    artwork_config = manifest.get("artwork", {})
    provenance_file = artwork_config.get(
        "provenance_file",
        "poster-flux2-provenance.json",
    )
    provenance_path = scope_dir / provenance_file
    payload = json.loads(provenance_path.read_text(encoding="utf-8"))
    if payload.get("kind") != "promoted_poster" or payload.get("scope") != scope:
        raise ValueError(f"Invalid promoted provenance: {provenance_path}")
    if bundle.section_id is not None and (
        payload.get("source_scope") != bundle.scope
        or payload.get("poster_id") != bundle.poster_id
        or payload.get("section_id") != bundle.section_id
    ):
        raise ValueError(
            f"Promoted provenance targets the wrong aggregate section: "
            f"{provenance_path}"
        )
    scope_data = load_poster_scope_data(bundle)
    _validate_section_source(bundle, scope_data)

    configured_generation = artwork_config.get("generation", {})
    recorded_generation = payload.get("run", {}).get("generation", {})
    if recorded_generation != configured_generation:
        raise ValueError(
            f"Generation metadata drift between {manifest_path} and "
            f"{provenance_path}"
        )
    recorded_manifest = (
        payload.get("run", {})
        .get("inputs", {})
        .get("scope_manifest", {})
    )
    if recorded_manifest.get("sha256") != sha256_file(manifest_path):
        raise ValueError(
            f"Scope manifest drift between {manifest_path} and "
            f"{provenance_path}"
        )
    missing_hashes = [
        key for key in REQUIRED_GENERATION_HASHES if not recorded_generation.get(key)
    ]
    if missing_hashes:
        raise ValueError(
            f"Missing promoted model hashes: {', '.join(missing_hashes)}"
        )
    identity_validation = (
        payload.get("run", {})
        .get("validation", {})
        .get("identity_lock")
    )
    if recorded_generation.get("mode") == "identity_lock":
        if not isinstance(identity_validation, dict):
            raise ValueError(
                "Promoted identity-lock artwork lacks its source-pixel "
                "validation record"
            )
        if (
            identity_validation.get("method")
            != "exact_opaque_source_pixels"
            or identity_validation.get("passed") is not True
            or identity_validation.get("changed_pixels") != 0
            or int(identity_validation.get("opaque_pixels", 0)) <= 0
        ):
            raise ValueError(
                "Promoted identity-lock source-pixel validation did not pass"
            )
        prompt_record = (
            payload.get("run", {})
            .get("inputs", {})
            .get("prompt", {})
        )
        current_prompt = (
            build_identity_lock_prompt(manifest, scope_data) + "\n"
        ).encode("utf-8")
        current_prompt_hash = hashlib.sha256(current_prompt).hexdigest()
        if prompt_record.get("sha256") != current_prompt_hash:
            raise ValueError(
                "Generated identity-lock prompt drift between the current "
                f"manifest/code and {provenance_path}"
            )

    output_dpi = int(recorded_generation.get("output_dpi", 0))
    layout = build_print_layout(
        manifest.get("layout", {}).get("name", "standard_3x3"),
        output_dpi,
    )
    outputs = payload.get("outputs", {})
    artwork_path = _validate_record(outputs["artwork"])
    routed_artwork_path = bundle.asset_dir / bundle.artwork_file
    if artwork_path != routed_artwork_path:
        raise ValueError(
            f"{bundle.asset_key} routes PDF artwork to "
            f"{routed_artwork_path}, but promoted provenance validates "
            f"{artwork_path}"
        )
    preview_path = _validate_record(outputs["preview"])
    card_records = outputs.get("cards", [])
    if len(card_records) != layout.rows * layout.columns:
        raise ValueError(
            f"Expected {layout.rows * layout.columns} card records, "
            f"got {len(card_records)}"
        )
    card_paths = [_validate_record(record) for record in card_records]

    for path in (artwork_path, preview_path):
        with Image.open(path) as image:
            if image.size != (layout.width_px, layout.height_px):
                raise ValueError(
                    f"Promoted poster has wrong print dimensions: {path} "
                    f"is {image.size}"
                )
        dpi_x, dpi_y = _image_dpi(path)
        if abs(dpi_x - output_dpi) > 0.1 or abs(dpi_y - output_dpi) > 0.1:
            raise ValueError(f"Wrong dpi metadata for {path}: {(dpi_x, dpi_y)}")

    for path in card_paths:
        with Image.open(path) as image:
            if image.size != (layout.card_width_px, layout.card_height_px):
                raise ValueError(
                    f"Promoted card has wrong dimensions: {path} is {image.size}"
                )
        dpi_x, dpi_y = _image_dpi(path)
        if abs(dpi_x - output_dpi) > 0.1 or abs(dpi_y - output_dpi) > 0.1:
            raise ValueError(f"Wrong dpi metadata for {path}: {(dpi_x, dpi_y)}")

    dpi_x, dpi_y = effective_dpi(layout)
    return {
        "scope": scope,
        "artwork": artwork_path,
        "preview": preview_path,
        "cards": len(card_paths),
        "dimensions": (layout.width_px, layout.height_px),
        "card_dimensions": (layout.card_width_px, layout.card_height_px),
        "effective_dpi": (dpi_x, dpi_y),
        "provenance": provenance_path,
        "identity_pixels": (
            int(identity_validation["opaque_pixels"])
            if identity_validation
            else None
        ),
    }


def _print_result(result: dict[str, Any]) -> None:
    print(
        f"{result['scope']}: {result['dimensions'][0]}x"
        f"{result['dimensions'][1]}, {result['cards']} cards at "
        f"{result['effective_dpi'][0]:.2f} dpi"
    )
    print(f"Provenance: {result['provenance']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--scope")
    target.add_argument(
        "--all-enabled",
        action="store_true",
        help="Validate every poster manifest with pdf.enabled set to true",
    )
    args = parser.parse_args()

    targets: list[str | PosterBundle] = (
        enabled_poster_bundles()
        if args.all_enabled
        else [args.scope]
    )
    for target_value in targets:
        _print_result(validate(target_value))
    if args.all_enabled:
        print(f"Validated {len(targets)} enabled poster bundle(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
