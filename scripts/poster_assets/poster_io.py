"""Shared paths and structured-file readers for poster assets."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
POSTER_ASSETS = ROOT / "data" / "poster_assets"
SCOPE_DATA = ROOT / "data" / "output"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_cutout_items(scope_dir: Path) -> list[dict[str, Any]]:
    manifest = load_json(scope_dir / "cutouts" / "manifest.json")
    return list(manifest.get("items", []))
