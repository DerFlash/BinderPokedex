#!/usr/bin/env python3
"""Initialize a local identity-lock poster scope from generated set data."""
from __future__ import annotations

import argparse
import copy
import hashlib
import re
from pathlib import Path
from typing import Any

import yaml

try:
    from .fetch_cutouts import fetch_cutouts
    from .fetch_title_logos import fetch_title_logos
    from .layout import DEFAULT_LAYOUT_NAME, LAYOUTS, resolve_layout_name
    from .poster_io import POSTER_ASSETS, SCOPE_DATA, load_json, load_yaml
    from .scene_catalog import scene_for_scope
except ImportError:
    from fetch_cutouts import fetch_cutouts
    from fetch_title_logos import fetch_title_logos
    from layout import DEFAULT_LAYOUT_NAME, LAYOUTS, resolve_layout_name
    from poster_io import POSTER_ASSETS, SCOPE_DATA, load_json, load_yaml
    from scene_catalog import scene_for_scope


SUPPORTED_LANGUAGES = ("de", "en", "fr", "es", "it")
FALLBACK_POKEMON = (25, 1, 4, 7, 133, 6)


def stable_scope_seed(scope: str) -> int:
    """Return a stable, scope-specific seed in the project's date namespace."""
    digest = hashlib.sha256(scope.encode("utf-8")).digest()
    return 260700000 + int.from_bytes(digest[:4], "big") % 100000


def _title_logo_config(scope_data: dict[str, Any]) -> dict[str, Any] | None:
    urls = scope_data.get("logo_urls")
    if not isinstance(urls, dict):
        return None
    advertised = scope_data.get("available_languages", SUPPORTED_LANGUAGES)
    if not isinstance(advertised, list):
        raise ValueError("available_languages must be a list")
    languages = [
        language
        for language in SUPPORTED_LANGUAGES
        if language in advertised and urls.get(language)
    ]
    if not languages:
        return None
    return {
        "files": {
            language: f"logos/logo-{language}.png"
            for language in languages
        }
    }


def build_default_manifest(
    scope: str,
    scope_data: dict[str, Any],
    layout_name: str,
    generation_template: dict[str, Any],
    scene: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a manifest from the shared generation contract and creative scene."""
    layout = resolve_layout_name(layout_name)
    if scope_data.get("type") != "tcg_set":
        raise ValueError(
            f"{scope} is not an individual TCG set and cannot supply one "
            "unambiguous set name, card count, and publication date"
        )
    if not scope_data.get("name") or not scope_data.get("release_date"):
        raise ValueError(f"{scope} lacks a set name or publication date")
    if not isinstance(generation_template, dict) or not generation_template:
        raise ValueError("A reviewed artwork.generation template is required")

    generation = copy.deepcopy(generation_template)
    generation.update(
        {
            "mode": "identity_lock",
            "reference_mode": "two_pass_source_pixels",
            "seed": stable_scope_seed(scope),
            "steps": 4,
            "generation_megapixels": 1.0,
            "output_dpi": 300,
            "output_method": "model_upscale",
        }
    )
    center_column = max(1, (int(layout["columns"]) + 1) // 2)
    manifest: dict[str, Any] = {
        "scope": scope,
        "layout": {"name": layout_name},
        "text_cells": {
            "title": {"row": 1, "column": center_column},
            "set_info": {
                "row": min(2, int(layout["rows"])),
                "column": center_column,
                "max_width_ratio": 0.92,
                "max_height_ratio": 0.68,
            },
        },
        "pdf": {
            "enabled": False,
            "artwork_file": "poster-flux2-artwork.png",
            "insertion": "after_first_section_cover",
        },
        "artwork": {
            "promoted_file": "poster-flux2-artwork.png",
            "preview_file": "poster-flux2.png",
            "provenance_file": "poster-flux2-provenance.json",
            "identity_lock": {
                "overscan_ratio": 0.04,
                "max_protected_start_ratio": 0.70,
                "transition_ratio": 0.10,
                "subject_clearance_ratio": 0.02,
            },
            "generation": generation,
        },
        "pokemon": {
            "strategy": "featured_from_scope",
            "count": "auto_from_layout_columns",
            "row": "bottom",
            "cutout_source": "pokeapi_official_artwork",
            "fallback_candidates": [
                {"pokemon_id": pokemon_id}
                for pokemon_id in FALLBACK_POKEMON
            ],
        },
        "conditioning": {
            "identity_defaults": {
                "neutral_rgb": [226, 224, 211],
                "canvas_px": 512,
                "min_subject_px": 150,
                "max_subject_px": 350,
                "bottom_padding_px": 24,
            }
        },
    }
    if scene is not None:
        manifest["artwork"]["scene"] = copy.deepcopy(scene)
    logo_config = _title_logo_config(scope_data)
    if logo_config is not None:
        manifest["title_logo"] = logo_config
    return manifest


def init_scope(
    scope: str,
    *,
    layout_name: str = DEFAULT_LAYOUT_NAME,
    force: bool = False,
    fetch: bool = False,
) -> Path:
    """Write one manifest and optionally fetch its deterministic source assets."""
    if not re.fullmatch(r"[A-Za-z0-9._-]+", scope):
        raise ValueError(f"Unsafe scope name: {scope!r}")
    scope_data_path = SCOPE_DATA / f"{scope}.json"
    if not scope_data_path.is_file():
        raise FileNotFoundError(scope_data_path)
    template_path = POSTER_ASSETS / "Base1" / "poster.yaml"
    if not template_path.is_file():
        raise FileNotFoundError(
            f"Reviewed generation template not found: {template_path}"
        )

    scope_data = load_json(scope_data_path)
    generation_template = load_yaml(template_path).get(
        "artwork",
        {},
    ).get("generation", {})
    scene = (
        scene_for_scope(scope)
        if scope_data.get("type") == "tcg_set"
        else None
    )
    manifest = build_default_manifest(
        scope,
        scope_data,
        layout_name,
        generation_template,
        scene,
    )
    scope_dir = POSTER_ASSETS / scope
    manifest_path = scope_dir / "poster.yaml"
    if manifest_path.exists() and not force:
        raise FileExistsError(
            f"Poster manifest already exists: {manifest_path} "
            "(use --force to replace it)"
        )
    scope_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        yaml.safe_dump(
            manifest,
            allow_unicode=True,
            sort_keys=False,
            width=88,
        ),
        encoding="utf-8",
    )
    if fetch:
        fetch_cutouts(scope, force=force)
        if manifest.get("title_logo"):
            fetch_title_logos(scope, force=force)
    return manifest_path


def available_tcg_scopes() -> list[str]:
    """Return generated individual TCG sets in stable CLI order."""
    scopes = []
    for path in sorted(SCOPE_DATA.glob("*.json")):
        if load_json(path).get("type") == "tcg_set":
            scopes.append(path.stem)
    return scopes


def init_missing_tcg_scopes(
    *,
    layout_name: str = DEFAULT_LAYOUT_NAME,
    fetch: bool = False,
) -> tuple[list[Path], list[Path]]:
    """Initialize every missing individual set and preserve reviewed manifests."""
    created = []
    skipped = []
    for scope in available_tcg_scopes():
        manifest_path = POSTER_ASSETS / scope / "poster.yaml"
        if manifest_path.exists():
            skipped.append(manifest_path)
            continue
        created.append(
            init_scope(
                scope,
                layout_name=layout_name,
                fetch=fetch,
            )
        )
    return created, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--scope")
    target.add_argument(
        "--all-tcg-sets",
        action="store_true",
        help="Initialize every missing individual TCG set after data fetching",
    )
    parser.add_argument(
        "--layout",
        choices=tuple(sorted(LAYOUTS)),
        default=DEFAULT_LAYOUT_NAME,
    )
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="Also fetch reviewed transparent cutouts and localized set logos",
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.all_tcg_sets:
        if args.force:
            parser.error(
                "--force cannot be combined with --all-tcg-sets; reviewed "
                "manifests are never overwritten by the batch initializer"
            )
        created, skipped = init_missing_tcg_scopes(
            layout_name=args.layout,
            fetch=args.fetch,
        )
        for path in created:
            print(f"Created: {path}")
        for path in skipped:
            print(f"Kept existing: {path}")
        print(f"Created {len(created)}, kept {len(skipped)} existing manifests")
        return 0
    print(
        init_scope(
            args.scope,
            layout_name=args.layout,
            force=args.force,
            fetch=args.fetch,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
