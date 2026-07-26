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
    from .poster_io import SCOPE_DATA, load_json, load_yaml
except ImportError:
    from layout import build_print_layout, effective_dpi
    from poster_config import build_identity_lock_prompt
    from provenance import ROOT, sha256_file
    from poster_io import SCOPE_DATA, load_json, load_yaml


POSTER_ASSETS = ROOT / "data" / "poster_assets"
REQUIRED_GENERATION_HASHES = (
    "model_sha256",
    "encoder_sha256",
    "vae_sha256",
    "upscale_model_sha256",
)


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


def validate(scope: str) -> dict[str, Any]:
    scope_dir = POSTER_ASSETS / scope
    manifest_path = scope_dir / "poster.yaml"
    manifest = load_yaml(manifest_path)
    artwork_config = manifest.get("artwork", {})
    provenance_file = artwork_config.get(
        "provenance_file",
        "poster-flux2-provenance.json",
    )
    provenance_path = scope_dir / provenance_file
    payload = json.loads(provenance_path.read_text(encoding="utf-8"))
    if payload.get("kind") != "promoted_poster" or payload.get("scope") != scope:
        raise ValueError(f"Invalid promoted provenance: {provenance_path}")

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
        scope_data = load_json(SCOPE_DATA / f"{scope}.json")
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", required=True)
    args = parser.parse_args()
    result = validate(args.scope)
    print(
        f"{result['scope']}: {result['dimensions'][0]}x"
        f"{result['dimensions'][1]}, {result['cards']} cards at "
        f"{result['effective_dpi'][0]:.2f} dpi"
    )
    print(f"Provenance: {result['provenance']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
