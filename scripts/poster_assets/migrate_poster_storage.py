#!/usr/bin/env python3
"""Migrate promoted poster provenance to the split durable-storage layout."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

try:
    from .poster_io import POSTER_ASSETS, POSTER_CONFIGS, PosterBundle
    from .validate_promoted_poster import enabled_poster_bundles
    from .provenance import sha256_file
except ImportError:
    from poster_io import POSTER_ASSETS, POSTER_CONFIGS, PosterBundle
    from validate_promoted_poster import enabled_poster_bundles
    from provenance import sha256_file


def _rewrite_recorded_path(value: str, bundle: PosterBundle) -> str:
    """Route old repository paths without changing immutable record hashes."""
    old_root = f"data/poster_assets/{bundle.asset_key}/"
    if not value.startswith(old_root):
        return value
    relative = value.removeprefix(old_root)
    if relative == "poster.yaml":
        return f"config/posters/{bundle.asset_key}/poster.yaml"
    if relative.startswith("cutouts/") or relative.startswith("logo"):
        return f"assets/posters/{bundle.asset_key}/{relative}"
    if relative.startswith("comfyui_poster/"):
        return f"tmp/poster-workspaces/{bundle.asset_key}/{relative}"
    return f"assets/posters/{bundle.asset_key}/{relative}"


def _rewrite_paths(value: Any, bundle: PosterBundle) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "file" and isinstance(item, str):
                value[key] = _rewrite_recorded_path(item, bundle)
            else:
                _rewrite_paths(item, bundle)
    elif isinstance(value, list):
        for item in value:
            _rewrite_paths(item, bundle)


def migrate_payload(payload: dict[str, Any], bundle: PosterBundle) -> dict[str, Any]:
    """Return schema v2 provenance containing only the durable master output."""
    if payload.get("kind") != "promoted_poster":
        raise ValueError(f"Not promoted poster provenance: {bundle.asset_key}")
    if payload.get("scope") != bundle.asset_key:
        raise ValueError(f"Provenance scope mismatch: {bundle.asset_key}")
    outputs = payload.get("outputs")
    if not isinstance(outputs, dict) or not isinstance(outputs.get("artwork"), dict):
        raise ValueError(f"Missing artwork output: {bundle.asset_key}")
    artwork_path = bundle.asset_dir / bundle.artwork_file
    artwork_record = outputs["artwork"]
    if artwork_record.get("sha256") != sha256_file(artwork_path):
        raise ValueError(f"Artwork hash mismatch: {artwork_path}")

    _rewrite_paths(payload, bundle)
    artwork_record["file"] = (
        Path("assets") / "posters" / bundle.asset_key / bundle.artwork_file
    ).as_posix()
    payload["schema_version"] = 2
    payload["outputs"] = {"artwork": artwork_record}
    if "preview_language" in payload:
        payload["review_language"] = payload.pop("preview_language")
    payload["storage"] = {
        "schema_version": 1,
        "durable_outputs": ["artwork"],
        "derivatives": "regenerated_in_ignored_workspace",
    }
    return payload


def _atomic_write(path: Path, content: str) -> None:
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def migrate_bundle(bundle: PosterBundle, *, write: bool) -> Path:
    artwork = bundle.manifest.get("artwork", {})
    provenance_name = artwork.get(
        "provenance_file",
        "poster-flux2-provenance.json",
    )
    provenance_path = bundle.asset_dir / str(provenance_name)
    payload = json.loads(provenance_path.read_text(encoding="utf-8"))
    migrated = migrate_payload(payload, bundle)
    encoded = json.dumps(
        migrated,
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    ) + "\n"
    if write:
        _atomic_write(provenance_path, encoded)
    return provenance_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write changes; without this flag only verify migration safety",
    )
    args = parser.parse_args()
    bundles = enabled_poster_bundles(
        poster_assets=POSTER_ASSETS,
        poster_configs=POSTER_CONFIGS,
    )
    for bundle in bundles:
        migrate_bundle(bundle, write=args.write)
    mode = "Migrated" if args.write else "Verified"
    print(f"{mode} {len(bundles)} poster provenance file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
