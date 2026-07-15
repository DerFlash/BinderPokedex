#!/usr/bin/env python3
"""
Import a reviewed poster background image for a scope.

This tool is intentionally source-agnostic. The image may come from a curated
licensed asset or from an external image-generation workflow. The renderer only
consumes the local reviewed background/background.png written here.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from PIL import Image


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
POSTER_ASSETS_DIR = REPO_ROOT / "data" / "poster_assets"
MIN_WIDTH = 900
MIN_HEIGHT = 900


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def resolve_scope_dir(scope: str) -> Path:
    scope_dir = POSTER_ASSETS_DIR / scope
    manifest = scope_dir / "poster.yaml"
    if not manifest.exists():
        raise FileNotFoundError(f"Poster manifest not found: {manifest}")
    return scope_dir


def validate_background(path: Path) -> dict[str, Any]:
    with Image.open(path) as img:
        width, height = img.size
        mode = img.mode

    errors = []
    if width < MIN_WIDTH or height < MIN_HEIGHT:
        errors.append(f"image is too small ({width}x{height}, minimum {MIN_WIDTH}x{MIN_HEIGHT})")

    return {
        "mode": mode,
        "width": width,
        "height": height,
        "validated": not errors,
        "errors": errors,
    }


def import_background(
    scope: str,
    source_file: Path,
    mode: str,
    force: bool = False,
    source_url: str | None = None,
    author: str | None = None,
    license_name: str | None = None,
    tool: str | None = None,
    notes: str | None = None,
) -> int:
    if mode not in {"generated", "curated"}:
        raise ValueError("mode must be 'generated' or 'curated'")
    if not source_file.exists():
        raise FileNotFoundError(f"Source image not found: {source_file}")

    scope_dir = resolve_scope_dir(scope)
    poster_manifest = load_yaml(scope_dir / "poster.yaml")
    background_cfg = poster_manifest.get("background", {})
    out_rel = background_cfg.get("file", "background/background.png")
    manifest_rel = background_cfg.get("manifest_file", "background/manifest.json")
    prompt_rel = background_cfg.get("prompt_file", "background/prompt.txt")

    out_path = scope_dir / out_rel
    manifest_path = scope_dir / manifest_rel
    prompt_path = scope_dir / prompt_rel

    if out_path.exists() and not force:
        raise FileExistsError(f"Background already exists: {out_path} (use --force to overwrite)")

    validation = validate_background(source_file)
    if not validation["validated"]:
        raise ValueError(f"Background validation failed: {', '.join(validation['errors'])}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source_file) as img:
        img.convert("RGB").save(out_path, format="PNG", optimize=True)

    manifest = {
        "scope": scope,
        "mode": mode,
        "file": out_rel,
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "source_file": str(source_file),
        "validation": validation,
    }

    if mode == "generated":
        manifest["tool"] = tool or "unknown"
        manifest["prompt_file"] = prompt_rel if prompt_path.exists() else None
    else:
        manifest["source_url"] = source_url
        manifest["author"] = author
        manifest["license"] = license_name

    if notes:
        manifest["notes"] = notes

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Imported background: {out_path}")
    print(f"Wrote manifest: {manifest_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Import a reviewed poster background image")
    parser.add_argument("--scope", required=True, help="Scope name, e.g. Base1")
    parser.add_argument("--file", required=True, type=Path, help="Source image file to import")
    parser.add_argument("--mode", choices=["generated", "curated"], required=True)
    parser.add_argument("--force", action="store_true", help="Overwrite existing background")
    parser.add_argument("--source-url", help="Curated source URL")
    parser.add_argument("--author", help="Curated image author")
    parser.add_argument("--license", dest="license_name", help="Curated image license")
    parser.add_argument("--tool", help="Generated image tool/model")
    parser.add_argument("--notes", help="Additional manifest notes")
    args = parser.parse_args()

    try:
        return import_background(
            scope=args.scope,
            source_file=args.file,
            mode=args.mode,
            force=args.force,
            source_url=args.source_url,
            author=args.author,
            license_name=args.license_name,
            tool=args.tool,
            notes=args.notes,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
