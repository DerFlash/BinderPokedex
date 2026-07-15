#!/usr/bin/env python3
"""
Fetch reviewed poster Pokemon cutouts for a scope.

The pilot source is PokeAPI official artwork. Files are stored as RGBA PNGs
with alpha preserved; the existing JPEG thumbnail cache is intentionally not
used for poster assets.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml
from PIL import Image

try:
    from .layout import build_page_layout
except ImportError:  # Direct script execution
    from layout import build_page_layout


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
POSTER_ASSETS_DIR = REPO_ROOT / "data" / "poster_assets"
OUTPUT_DIR = REPO_ROOT / "data" / "output"
POKEAPI_OFFICIAL_ARTWORK_URL = (
    "https://raw.githubusercontent.com/PokeAPI/sprites/master/"
    "sprites/pokemon/other/official-artwork/{pokemon_id}.png"
)
USER_AGENT = "BinderPokedex poster-assets/1.0"
MIN_SIZE = 350


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def resolve_layout(manifest: dict[str, Any]):
    layout = manifest.get("layout", {})
    name = layout.get("name", "standard_3x3")
    return build_page_layout(name)


def collect_pokedex_names() -> dict[int, dict[str, str]]:
    pokedex_path = OUTPUT_DIR / "Pokedex.json"
    if not pokedex_path.exists():
        return {}

    pokedex = load_json(pokedex_path)
    names: dict[int, dict[str, str]] = {}
    for section in pokedex.get("sections", {}).values():
        for card in section.get("cards", []):
            pokemon_id = card.get("pokemon_id")
            localized = card.get("name")
            if isinstance(pokemon_id, int) and isinstance(localized, dict):
                names[pokemon_id] = localized
    return names


def scope_featured_elements(scope_data: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for section in scope_data.get("sections", {}).values():
        featured = section.get("featured_elements") or section.get("featured_cards") or []
        if isinstance(featured, list):
            result.extend(item for item in featured if isinstance(item, dict))
    return result


def unique_by_pokemon_id(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[int] = set()
    unique: list[dict[str, Any]] = []
    for item in items:
        pokemon_id = item.get("pokemon_id")
        if not isinstance(pokemon_id, int) or pokemon_id in seen:
            continue
        seen.add(pokemon_id)
        unique.append(item)
    return unique


def resolve_requested_count(manifest: dict[str, Any], layout) -> int:
    pokemon_cfg = manifest.get("pokemon", {})
    count = pokemon_cfg.get("count", "auto_from_layout_columns")
    if count == "auto_from_layout_columns":
        return int(layout.columns)
    if isinstance(count, int) and count > 0:
        return count
    raise ValueError("pokemon.count must be a positive integer or 'auto_from_layout_columns'")


def select_pokemon(
    manifest: dict[str, Any],
    scope_data: dict[str, Any],
    count: int,
    names_by_id: dict[int, dict[str, str]],
) -> list[dict[str, Any]]:
    pokemon_cfg = manifest.get("pokemon", {})
    strategy = pokemon_cfg.get("strategy", "featured_from_scope")
    if strategy != "featured_from_scope":
        raise ValueError(f"Unsupported pokemon.strategy '{strategy}'")

    selected = unique_by_pokemon_id(scope_featured_elements(scope_data))
    fallback_candidates = pokemon_cfg.get("fallback_candidates", [])
    for candidate in fallback_candidates:
        pokemon_id = candidate.get("pokemon_id") if isinstance(candidate, dict) else None
        if not isinstance(pokemon_id, int):
            continue
        localized = names_by_id.get(pokemon_id, {})
        selected.append({
            "pokemon_id": pokemon_id,
            "pokemon_name": localized.get("en") or f"pokemon-{pokemon_id}",
        })
    selected = unique_by_pokemon_id(selected)

    if len(selected) < count:
        found = ", ".join(str(item.get("pokemon_id")) for item in selected) or "none"
        raise ValueError(
            f"Layout needs {count} Pokemon, but only {len(selected)} were resolved ({found}). "
            "Add pokemon.fallback_candidates to poster.yaml."
        )
    return selected[:count]


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "pokemon"


def cutout_filename(pokemon_id: int, name_en: str) -> str:
    return f"pokemon_{pokemon_id:03d}_{slugify(name_en)}.png"


def download_bytes(url: str, timeout: int = 20) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as response:
        return response.read()


def validate_png(path: Path) -> dict[str, Any]:
    with Image.open(path) as img:
        mode = img.mode
        width, height = img.size
        rgba = img.convert("RGBA")
        alpha = rgba.getchannel("A")
        alpha_min, alpha_max = alpha.getextrema()
        histogram = alpha.histogram()
        transparent_pixels = sum(histogram[:255])
        opaque_pixels = sum(histogram[1:])

    errors = []
    if width < MIN_SIZE or height < MIN_SIZE:
        errors.append(f"image is too small ({width}x{height}, minimum {MIN_SIZE}x{MIN_SIZE})")
    if alpha_min == 255:
        errors.append("image has no transparent pixels")
    if alpha_max == 0 or opaque_pixels == 0:
        errors.append("image has no opaque subject pixels")

    return {
        "mode": mode,
        "width": width,
        "height": height,
        "alpha_min": alpha_min,
        "alpha_max": alpha_max,
        "transparent_pixels": transparent_pixels,
        "opaque_pixels": opaque_pixels,
        "validated_alpha": not errors,
        "errors": errors,
    }


def save_cutout(image_bytes: bytes, out_path: Path) -> dict[str, Any]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(".tmp.png")
    tmp_path.write_bytes(image_bytes)
    with Image.open(tmp_path) as img:
        img.convert("RGBA").save(out_path, format="PNG")
    tmp_path.unlink(missing_ok=True)
    return validate_png(out_path)


def build_manifest_item(
    pokemon: dict[str, Any],
    names_by_id: dict[int, dict[str, str]],
    file_name: str,
    url: str,
    validation: dict[str, Any],
) -> dict[str, Any]:
    pokemon_id = pokemon["pokemon_id"]
    localized = names_by_id.get(pokemon_id, {})
    name_en = localized.get("en") or pokemon.get("pokemon_name") or f"pokemon-{pokemon_id}"
    name_de = localized.get("de") or name_en
    return {
        "pokemon_id": pokemon_id,
        "name_en": name_en,
        "name_de": name_de,
        "url": url,
        "file": file_name,
        **validation,
    }


def fetch_cutouts(scope: str, force: bool = False) -> int:
    scope_dir = POSTER_ASSETS_DIR / scope
    poster_yaml = scope_dir / "poster.yaml"
    scope_json = OUTPUT_DIR / f"{scope}.json"
    if not poster_yaml.exists():
        raise FileNotFoundError(f"Poster manifest not found: {poster_yaml}")
    if not scope_json.exists():
        raise FileNotFoundError(f"Scope output not found: {scope_json}")

    manifest = load_yaml(poster_yaml)
    scope_data = load_json(scope_json)
    names_by_id = collect_pokedex_names()
    layout = resolve_layout(manifest)
    count = resolve_requested_count(manifest, layout)
    selected = select_pokemon(manifest, scope_data, count, names_by_id)

    cutouts_dir = scope_dir / "cutouts"
    cutouts_dir.mkdir(parents=True, exist_ok=True)
    items: list[dict[str, Any]] = []

    print(f"Scope: {scope}")
    print(f"Layout: {layout.name} ({layout.columns}x{layout.rows})")
    print(f"Pokemon needed: {count}")

    for pokemon in selected:
        pokemon_id = pokemon["pokemon_id"]
        localized = names_by_id.get(pokemon_id, {})
        name_en = localized.get("en") or pokemon.get("pokemon_name") or f"pokemon-{pokemon_id}"
        url = POKEAPI_OFFICIAL_ARTWORK_URL.format(pokemon_id=pokemon_id)
        file_name = cutout_filename(pokemon_id, name_en)
        out_path = cutouts_dir / file_name

        if out_path.exists() and not force:
            validation = validate_png(out_path)
            status = "valid" if validation["validated_alpha"] else "invalid"
            print(f"  - {name_en} #{pokemon_id:03d}: exists ({status})")
        else:
            print(f"  - {name_en} #{pokemon_id:03d}: downloading")
            try:
                image_bytes = download_bytes(url)
                validation = save_cutout(image_bytes, out_path)
            except (HTTPError, URLError, TimeoutError) as exc:
                raise RuntimeError(f"Failed to download {url}: {exc}") from exc

        items.append(build_manifest_item(pokemon, names_by_id, file_name, url, validation))

    manifest_out = {
        "scope": scope,
        "source": "pokeapi_official_artwork",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "layout": {
            "name": layout.name,
            "columns": layout.columns,
            "rows": layout.rows,
        },
        "items": items,
    }
    manifest_path = cutouts_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    invalid = [item for item in items if not item.get("validated_alpha")]
    if invalid:
        names = ", ".join(f"{item['name_en']} #{item['pokemon_id']:03d}" for item in invalid)
        raise RuntimeError(f"Cutout validation failed for: {names}")

    print(f"Wrote {manifest_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch poster cutouts for a scope")
    parser.add_argument("--scope", required=True, help="Scope name, e.g. Base1")
    parser.add_argument("--force", action="store_true", help="Overwrite existing cutouts")
    args = parser.parse_args()

    try:
        return fetch_cutouts(args.scope, force=args.force)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
