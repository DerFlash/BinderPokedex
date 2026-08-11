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
    from .poster_io import POSTER_ASSETS, load_poster_scope_data, poster_bundle
    from .poster_subject import (
        manifest_subject_fields,
        poster_display_name_from_card,
        poster_subject_from_card,
        resolve_poster_subject,
    )
except ImportError:  # Direct script execution
    from layout import build_page_layout
    from poster_io import POSTER_ASSETS, load_poster_scope_data, poster_bundle
    from poster_subject import (
        manifest_subject_fields,
        poster_display_name_from_card,
        poster_subject_from_card,
        resolve_poster_subject,
    )


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
POSTER_ASSETS_DIR = POSTER_ASSETS
OUTPUT_DIR = REPO_ROOT / "data" / "output"
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
    set_id = scope_data.get("set_id")
    normalized_set_id = (
        set_id.lower()
        if isinstance(set_id, str) and set_id
        else None
    )
    for section in scope_data.get("sections", {}).values():
        featured = section.get("featured_elements") or section.get("featured_cards") or []
        if isinstance(featured, list):
            cards = section.get("cards", [])
            cards_by_id = {}
            if isinstance(cards, list):
                for card in cards:
                    if not isinstance(card, dict):
                        continue
                    tcg_card = card.get("tcg_card")
                    card_id = (
                        tcg_card.get("id")
                        if isinstance(tcg_card, dict)
                        else card.get("id")
                    )
                    if isinstance(card_id, str):
                        cards_by_id[card_id] = card
                    local_id = card.get("localId")
                    if (
                        normalized_set_id is not None
                        and isinstance(local_id, str)
                        and local_id
                    ):
                        cards_by_id[
                            f"{normalized_set_id}-{local_id}"
                        ] = card

            for item in featured:
                if not isinstance(item, dict):
                    continue
                resolved = dict(item)
                card_id = resolved.get("card_id")
                source_card = (
                    cards_by_id.get(card_id)
                    if isinstance(card_id, str)
                    else None
                )
                if (
                    isinstance(card_id, str)
                    and cards_by_id
                    and source_card is None
                ):
                    raise ValueError(
                        f"Featured card {card_id!r} does not exist in its "
                        "source section"
                    )
                if isinstance(source_card, dict):
                    poster_subject = poster_subject_from_card(
                        source_card
                    )
                    if "poster_subject" in resolved:
                        explicit = resolve_poster_subject(resolved)
                        derived = resolve_poster_subject(
                            {
                                "pokemon_id": source_card.get("pokemon_id"),
                                "poster_subject": poster_subject,
                            }
                        )
                        if (
                            explicit.species_id != derived.species_id
                            or explicit.selection_key()
                            != derived.selection_key()
                        ):
                            raise ValueError(
                                f"Featured card {card_id!r} poster_subject "
                                "does not match its source card artwork"
                            )
                    else:
                        resolved["poster_subject"] = poster_subject
                    name = resolved.get("pokemon_name")
                    if (
                        poster_subject["official_artwork_id"]
                        != poster_subject["species_id"]
                    ):
                        resolved["pokemon_name"] = (
                            poster_display_name_from_card(
                                source_card,
                                name,
                            )
                        )
                result.append(resolved)
    return result


def unique_by_poster_subject(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    seen: set[tuple[str, int, int]] = set()
    artwork_species: dict[tuple[str, int], int] = {}
    unique: list[dict[str, Any]] = []
    for item in items:
        subject = resolve_poster_subject(item)
        key = subject.selection_key()
        previous_species = artwork_species.get(subject.artwork_key())
        if (
            previous_species is not None
            and previous_species != subject.species_id
        ):
            raise ValueError(
                f"{subject.subject_key} is assigned to both Pokemon "
                f"#{previous_species} and #{subject.species_id}"
            )
        artwork_species[subject.artwork_key()] = subject.species_id
        if key in seen:
            continue
        seen.add(key)
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

    selected = unique_by_poster_subject(scope_featured_elements(scope_data))
    fallback_candidates = pokemon_cfg.get("fallback_candidates", [])
    slotted_candidates: list[tuple[int, dict[str, Any]]] = []
    appended_candidates: list[dict[str, Any]] = []
    for candidate in fallback_candidates:
        pokemon_id = candidate.get("pokemon_id") if isinstance(candidate, dict) else None
        if not isinstance(pokemon_id, int):
            continue
        localized = names_by_id.get(pokemon_id, {})
        resolved_candidate = dict(candidate)
        resolved_candidate.setdefault(
            "pokemon_name",
            localized.get("en") or f"pokemon-{pokemon_id}",
        )
        slot = candidate.get("slot")
        if slot is None:
            appended_candidates.append(resolved_candidate)
        elif (
            isinstance(slot, int)
            and not isinstance(slot, bool)
            and 1 <= slot <= count
        ):
            slotted_candidates.append((slot, resolved_candidate))
        else:
            raise ValueError(
                "pokemon.fallback_candidates slot must be between "
                f"1 and {count}"
            )
    for slot, candidate in sorted(
        slotted_candidates,
        key=lambda item: item[0],
    ):
        selected.insert(slot - 1, candidate)
    selected.extend(appended_candidates)
    selected = unique_by_poster_subject(selected)

    if len(selected) < count:
        found = ", ".join(
            resolve_poster_subject(item).subject_key for item in selected
        ) or "none"
        raise ValueError(
            f"Layout needs {count} Pokemon, but only {len(selected)} were resolved ({found}). "
            "Add pokemon.fallback_candidates to poster.yaml."
        )
    return selected[:count]


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "pokemon"


def cutout_filename(
    pokemon_id: int,
    name_en: str,
    official_artwork_id: int | None = None,
) -> str:
    if (
        official_artwork_id is not None
        and official_artwork_id != pokemon_id
    ):
        return (
            f"pokemon_{pokemon_id:03d}_artwork_{official_artwork_id}_"
            f"{slugify(name_en)}.png"
        )
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
    subject = resolve_poster_subject(pokemon)
    localized = names_by_id.get(pokemon_id, {})
    supplied_name = pokemon.get("pokemon_name")
    name_en = (
        supplied_name
        if subject.is_special_form and isinstance(supplied_name, str)
        else localized.get("en") or supplied_name or f"pokemon-{pokemon_id}"
    )
    name_de = localized.get("de") or name_en
    return {
        "pokemon_id": pokemon_id,
        "name_en": name_en,
        "name_de": name_de,
        "url": url,
        "file": file_name,
        **manifest_subject_fields(pokemon),
        **validation,
    }


def fetch_cutouts(scope: str, force: bool = False) -> int:
    bundle = poster_bundle(scope, poster_assets=POSTER_ASSETS_DIR)
    scope_dir = bundle.source_dir
    manifest = bundle.manifest
    scope_data = load_poster_scope_data(
        bundle,
        scope_data_dir=OUTPUT_DIR,
    )
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
        subject = resolve_poster_subject(pokemon)
        localized = names_by_id.get(pokemon_id, {})
        supplied_name = pokemon.get("pokemon_name")
        name_en = (
            supplied_name
            if subject.is_special_form and isinstance(supplied_name, str)
            else localized.get("en")
            or supplied_name
            or f"pokemon-{pokemon_id}"
        )
        url = subject.image_url
        file_name = cutout_filename(
            pokemon_id,
            name_en,
            subject.official_artwork_id,
        )
        out_path = cutouts_dir / file_name

        if out_path.exists() and not force:
            validation = validate_png(out_path)
            status = "valid" if validation["validated_alpha"] else "invalid"
            print(
                f"  - {name_en} #{pokemon_id:03d} "
                f"[artwork {subject.official_artwork_id}]: "
                f"exists ({status})"
            )
        else:
            print(
                f"  - {name_en} #{pokemon_id:03d} "
                f"[artwork {subject.official_artwork_id}]: downloading"
            )
            try:
                image_bytes = download_bytes(url)
                validation = save_cutout(image_bytes, out_path)
            except (HTTPError, URLError, TimeoutError) as exc:
                raise RuntimeError(f"Failed to download {url}: {exc}") from exc

        items.append(build_manifest_item(pokemon, names_by_id, file_name, url, validation))

    manifest_out = {
        "scope": scope,
        "source_scope": bundle.scope,
        "poster_id": bundle.poster_id,
        "section_id": bundle.section_id,
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
