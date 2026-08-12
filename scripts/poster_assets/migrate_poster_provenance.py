#!/usr/bin/env python3
"""Safely add semantic fingerprints to a validated legacy poster promotion.

The migration never regenerates artwork and never changes promoted outputs.
Before writing metadata it requires the existing provenance/output gate, the
recorded cutout byte hashes, and a freshly rendered overlay preview to match.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image

try:
    from .finalize_comfyui_poster import SUPPORTED_LANGUAGES, finalize
    from .poster_io import PosterBundle, load_json, poster_bundle
    from .provenance import (
        build_generation_fingerprint,
        build_overlay_fingerprint,
        generation_fingerprint_pipeline_contract_version,
        fingerprint_record_is_valid,
        sha256_file,
    )
    from .validate_promoted_poster import (
        POSTER_ASSETS,
        enabled_poster_bundles,
        validate,
    )
except ImportError:  # Direct script execution
    from finalize_comfyui_poster import SUPPORTED_LANGUAGES, finalize
    from poster_io import PosterBundle, load_json, poster_bundle
    from provenance import (
        build_generation_fingerprint,
        build_overlay_fingerprint,
        generation_fingerprint_pipeline_contract_version,
        fingerprint_record_is_valid,
        sha256_file,
    )
    from validate_promoted_poster import (
        POSTER_ASSETS,
        enabled_poster_bundles,
        validate,
    )


def _promotion_path(bundle: PosterBundle) -> Path:
    configured = bundle.manifest.get("artwork", {})
    if not isinstance(configured, dict):
        raise ValueError("artwork must be a mapping")
    filename = configured.get(
        "provenance_file",
        "poster-flux2-provenance.json",
    )
    if not isinstance(filename, str) or not filename:
        raise ValueError("artwork.provenance_file must be a relative path")
    relative = Path(filename)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Unsafe provenance path: {filename!r}")
    path = (bundle.asset_dir / relative).resolve()
    if not path.is_relative_to(bundle.asset_dir.resolve()):
        raise ValueError(f"Provenance escapes poster scope: {filename!r}")
    return path


def _recorded_pipeline_contract_version(
    provenance: dict[str, Any],
) -> int:
    """Infer a known historical contract from immutable run input topology."""
    run = provenance.get("run")
    if not isinstance(run, dict):
        raise ValueError("Promoted provenance has no run mapping")
    generation = run.get("generation")
    inputs = run.get("inputs")
    if not isinstance(generation, dict) or not isinstance(inputs, dict):
        raise ValueError("Promoted provenance lacks generation inputs")
    family = (
        str(generation.get("engine", "")),
        str(generation.get("mode", "")),
    )
    if family != ("flux", "identity_lock"):
        raise ValueError(
            "Legacy semantic migration only supports the audited "
            "flux/identity_lock reference topology"
        )
    records = inputs.get("references")
    if not isinstance(records, list):
        raise ValueError("Promoted provenance has no reference records")
    names: list[str] = []
    for record in records:
        filename = record.get("file") if isinstance(record, dict) else None
        if not isinstance(filename, str) or not filename:
            raise ValueError("Promoted provenance has an invalid reference")
        names.append(Path(filename).name)
    if len(names) != len(set(names)):
        raise ValueError("Promoted provenance has duplicate references")
    topology = frozenset(names)
    legacy = frozenset(
        {
            "inpaint_reference.png",
            "upper_context_mask.png",
        }
    )
    current = frozenset(
        {
            *legacy,
            "upper_context_generation_mask.png",
        }
    )
    if topology == legacy:
        return 1
    if topology == current:
        return 2
    raise ValueError(
        "Promoted provenance has an unknown identity-lock reference topology"
    )


def _current_cutouts(bundle: PosterBundle) -> list[tuple[str, Path]]:
    cutout_dir = (bundle.source_dir / "cutouts").resolve()
    payload = load_json(cutout_dir / "manifest.json")
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("Current cutout manifest has no items")
    current: list[tuple[str, Path]] = []
    for item in items:
        filename = item.get("file") if isinstance(item, dict) else None
        if not isinstance(filename, str) or not filename:
            raise ValueError("Current cutout manifest contains an invalid file")
        relative = Path(filename)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Unsafe cutout path: {filename!r}")
        path = (cutout_dir / relative).resolve()
        if not path.is_relative_to(cutout_dir):
            raise ValueError(f"Cutout escapes its asset directory: {filename!r}")
        if not path.is_file():
            raise FileNotFoundError(path)
        current.append((relative.name, path))
    return current


def _verify_recorded_cutouts(
    bundle: PosterBundle,
    provenance: dict[str, Any],
) -> None:
    records = (
        provenance.get("run", {})
        .get("inputs", {})
        .get("cutouts")
    )
    if not isinstance(records, list):
        raise ValueError("Promoted provenance has no cutout records")
    current = _current_cutouts(bundle)
    if len(records) != len(current):
        raise ValueError(
            "Recorded and current cutout counts differ; refusing migration"
        )
    for index, (record, (filename, path)) in enumerate(
        zip(records, current, strict=True),
        start=1,
    ):
        if not isinstance(record, dict):
            raise ValueError(f"Cutout record {index} is invalid")
        recorded_file = record.get("file")
        recorded_hash = record.get("sha256")
        if (
            not isinstance(recorded_file, str)
            or Path(recorded_file).name != filename
            or not isinstance(recorded_hash, str)
            or recorded_hash != sha256_file(path)
        ):
            raise ValueError(
                f"Cutout record {index} differs from {path}; "
                "refusing migration"
            )


def _same_rgb_pixels(left: Path, right: Path) -> bool:
    with Image.open(left) as left_image, Image.open(right) as right_image:
        left_rgb = left_image.convert("RGB")
        right_rgb = right_image.convert("RGB")
        return (
            left_rgb.size == right_rgb.size
            and left_rgb.tobytes() == right_rgb.tobytes()
        )


def _verify_current_overlay(
    bundle: PosterBundle,
    provenance: dict[str, Any],
    validation: dict[str, Any],
) -> None:
    language = provenance.get("preview_language", "de")
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported promoted preview language: {language!r}")
    artwork = Path(validation["artwork"])
    preview = Path(validation["preview"])
    with tempfile.TemporaryDirectory(
        prefix=".poster-provenance-migration-",
        dir=bundle.asset_dir,
    ) as temporary:
        regenerated = Path(temporary) / "preview.png"
        finalize(bundle.asset_key, artwork, regenerated, language)
        if not _same_rgb_pixels(regenerated, preview):
            raise ValueError(
                "Current overlay inputs do not reproduce the promoted preview; "
                "refresh the deterministic overlay before migration"
            )


def _atomic_write(path: Path, payload: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def migrate(target: str | PosterBundle) -> dict[str, Any]:
    """Migrate one promotion transactionally and return its stable status."""
    bundle = (
        target
        if isinstance(target, PosterBundle)
        else poster_bundle(target, poster_assets=POSTER_ASSETS)
    )
    provenance_path = _promotion_path(bundle)
    original = provenance_path.read_bytes()
    provenance = json.loads(original.decode("utf-8"))
    inputs = provenance.get("run", {}).get("inputs")
    if not isinstance(inputs, dict):
        raise ValueError("Promoted provenance has no run.inputs mapping")
    recorded_generation = provenance.get("run", {}).get("generation")
    if not isinstance(recorded_generation, dict):
        raise ValueError("Promoted provenance has no run.generation mapping")
    historical_contract = _recorded_pipeline_contract_version(provenance)

    validation = validate(bundle)
    generation = inputs.get("generation_fingerprint")
    overlay = inputs.get("overlay_fingerprint")
    if generation is not None and not fingerprint_record_is_valid(generation):
        raise ValueError("Stored generation fingerprint is malformed")
    if overlay is not None and not fingerprint_record_is_valid(overlay):
        raise ValueError("Stored overlay fingerprint is malformed")
    stored_contract = (
        generation_fingerprint_pipeline_contract_version(
            generation,
            recorded_generation,
        )
        if isinstance(generation, dict)
        else None
    )
    if (
        generation is not None
        and overlay is not None
        and stored_contract == historical_contract
    ):
        if validation.get("generation_fingerprint_current") is not True:
            raise ValueError("Stored generation fingerprint is stale")
        if validation.get("overlay_fingerprint_current") is not True:
            raise ValueError("Stored overlay fingerprint is stale")
        return {
            "scope": bundle.asset_key,
            "status": "already_current",
            "provenance": provenance_path,
        }

    _verify_recorded_cutouts(bundle, provenance)
    _verify_current_overlay(bundle, provenance, validation)
    inputs["generation_fingerprint"] = build_generation_fingerprint(
        bundle,
        pipeline_contract_version=historical_contract,
    )
    inputs["overlay_fingerprint"] = build_overlay_fingerprint(bundle)
    inputs["semantic_fingerprint_migration"] = {
        "schema_version": 1,
        "origin": "backfilled_legacy",
        "generation_pipeline_contract_version": historical_contract,
        "inferred_from": "recorded_reference_topology",
    }
    encoded = (
        json.dumps(
            provenance,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")

    try:
        _atomic_write(provenance_path, encoded)
        migrated = validate(bundle)
        if migrated.get("generation_fingerprint_current") is not True:
            raise ValueError("Migrated generation fingerprint did not validate")
        if migrated.get("overlay_fingerprint_current") is not True:
            raise ValueError("Migrated overlay fingerprint did not validate")
    except Exception:
        _atomic_write(provenance_path, original)
        raise

    return {
        "scope": bundle.asset_key,
        "status": "migrated",
        "provenance": provenance_path,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--scope")
    target.add_argument(
        "--all-enabled",
        action="store_true",
        help="Migrate every currently PDF-enabled promoted bundle",
    )
    args = parser.parse_args(argv)
    targets: list[str | PosterBundle] = (
        enabled_poster_bundles()
        if args.all_enabled
        else [args.scope]
    )
    for selected in targets:
        result = migrate(selected)
        print(
            f"{result['scope']}: {result['status']} "
            f"({result['provenance']})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
