#!/usr/bin/env python3
"""
Prepare a generated poster background request for a scope.

Actual image generation happens outside the repository code, for example via
Codex's built-in image generation tool. This script makes the prompt and target
paths explicit so generated output can be imported consistently.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

try:
    from .prepare_background_guide import build_guide
except ImportError:  # Direct script execution
    from prepare_background_guide import build_guide


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
POSTER_ASSETS_DIR = REPO_ROOT / "data" / "poster_assets"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def prepare_generation(scope: str) -> int:
    scope_dir = POSTER_ASSETS_DIR / scope
    poster_yaml = scope_dir / "poster.yaml"
    if not poster_yaml.exists():
        raise FileNotFoundError(f"Poster manifest not found: {poster_yaml}")

    manifest = load_yaml(poster_yaml)
    background_cfg = manifest.get("background", {})
    prompt_path = scope_dir / background_cfg.get("prompt_file", "background/prompt.txt")
    output_path = scope_dir / background_cfg.get("file", "background/background.png")
    manifest_path = scope_dir / background_cfg.get("manifest_file", "background/manifest.json")

    if not prompt_path.exists():
        raise FileNotFoundError(f"Background prompt not found: {prompt_path}")

    prompt = prompt_path.read_text(encoding="utf-8").strip()
    guide_path = build_guide(scope)

    print(f"Scope: {scope}")
    print(f"Prompt: {prompt_path}")
    print(f"Target image: {output_path}")
    print(f"Target manifest: {manifest_path}")
    print(f"Composition guide: {guide_path}")
    print()
    print("Generation prompt:")
    print(prompt)
    print()
    print("Use the composition guide as a planning reference, not as artwork.")
    print()
    print("After generating an image, import it with:")
    print(
        "venv/bin/python scripts/poster_assets/import_background.py "
        f"--scope {scope} --mode generated --tool <tool-or-model> --file <generated-image> --force"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare background image generation for a scope")
    parser.add_argument("--scope", required=True, help="Scope name, e.g. Base1")
    args = parser.parse_args()

    try:
        return prepare_generation(args.scope)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
