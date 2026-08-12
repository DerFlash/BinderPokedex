#!/usr/bin/env python3
"""Create an isolated, local poster workspace for a custom card layout."""
from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

try:
    from .layout import LAYOUTS, resolve_layout_name
    from .poster_io import (
        POSTER_INDEX_NAME,
        POSTER_MANIFEST_NAME,
        ROOT,
        load_yaml,
        poster_asset_slug,
        poster_bundle,
        poster_bundles_for_scope,
    )
except ImportError:
    from layout import LAYOUTS, resolve_layout_name
    from poster_io import (
        POSTER_INDEX_NAME,
        POSTER_MANIFEST_NAME,
        ROOT,
        load_yaml,
        poster_asset_slug,
        poster_bundle,
        poster_bundles_for_scope,
    )


TRACKED_POSTER_ASSETS = ROOT / "data" / "poster_assets"
DEFAULT_WORKSPACE_PARENT = ROOT / "tmp" / "custom-poster-layouts"


def _target_root(
    scope: str,
    layout_name: str,
    sections: tuple[str, ...],
    output_root: Path | None,
) -> Path:
    if output_root is not None:
        target = output_root
        if not target.is_absolute():
            target = ROOT / target
    else:
        parts = [poster_asset_slug(scope)]
        if sections:
            parts.append("-".join(sections))
        parts.append(layout_name)
        target = DEFAULT_WORKSPACE_PARENT / "-".join(parts)
    target = target.resolve()
    if not target.is_relative_to(ROOT.resolve()):
        raise ValueError(
            "Custom poster workspaces must stay inside the repository so "
            "generation provenance can use safe repository-relative paths"
        )
    if target == TRACKED_POSTER_ASSETS.resolve():
        raise ValueError("Custom layout output cannot replace tracked poster assets")
    return target


def _selected_bundles(
    scope: str,
    sections: tuple[str, ...],
    source_assets: Path,
):
    if "/" in scope:
        if sections:
            raise ValueError("--section cannot be combined with a leaf asset key")
        return [poster_bundle(scope, poster_assets=source_assets)]

    bundles = poster_bundles_for_scope(scope, poster_assets=source_assets)
    if not bundles:
        raise ValueError(f"No poster configuration exists for scope {scope!r}")
    if not sections:
        return bundles

    requested = set(sections)
    selected = [
        bundle
        for bundle in bundles
        if bundle.section_id in requested or bundle.poster_id in requested
    ]
    found = {
        bundle.section_id or bundle.poster_id
        for bundle in selected
    }
    missing = sorted(requested - found)
    if missing:
        raise ValueError(
            f"Unknown poster sections for {scope}: {', '.join(missing)}"
        )
    return selected


def _copy_relative_file(
    source_dir: Path,
    target_dir: Path,
    relative_value: object,
) -> None:
    if not isinstance(relative_value, str) or not relative_value:
        return
    relative = Path(relative_value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Unsafe manifest asset path: {relative_value!r}")
    source = source_dir / relative
    if not source.is_file():
        return
    destination = target_dir / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _copy_inputs(source_dir: Path, target_dir: Path, manifest: dict[str, Any]) -> int:
    cutouts_source = source_dir / "cutouts"
    if not cutouts_source.is_dir():
        raise FileNotFoundError(cutouts_source)
    shutil.copytree(cutouts_source, target_dir / "cutouts")

    logos_source = source_dir / "logos"
    if logos_source.is_dir():
        shutil.copytree(logos_source, target_dir / "logos")

    title_logo = manifest.get("title_logo", {})
    if isinstance(title_logo, dict):
        _copy_relative_file(source_dir, target_dir, title_logo.get("file"))
        files = title_logo.get("files", {})
        if isinstance(files, dict):
            for relative_file in files.values():
                _copy_relative_file(source_dir, target_dir, relative_file)

    cutout_manifest_path = target_dir / "cutouts" / "manifest.json"
    cutout_manifest = json.loads(cutout_manifest_path.read_text(encoding="utf-8"))
    items = cutout_manifest.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError(f"Custom layout source has no cutouts: {cutout_manifest_path}")
    return len(items)


def _custom_manifest(
    source_manifest: dict[str, Any],
    layout_name: str,
    cutout_count: int,
    *,
    enable_pdf: bool,
    fallback_pokemon: tuple[int, ...] = (),
) -> dict[str, Any]:
    manifest = copy.deepcopy(source_manifest)
    layout = resolve_layout_name(layout_name)
    columns = int(layout["columns"])
    if cutout_count > columns:
        raise ValueError(
            f"Layout {layout_name} has {columns} columns but the source has "
            f"{cutout_count} subject cutouts"
        )
    manifest["layout"] = {"name": layout_name}

    pokemon = manifest.setdefault("pokemon", {})
    configured_count = pokemon.get("count", "auto_from_layout_columns")
    if (
        configured_count != "auto_from_layout_columns"
        and int(configured_count) > columns
    ):
        raise ValueError(
            f"Configured subject count {pokemon['count']} exceeds {layout_name}"
        )

    source_layout = resolve_layout_name(
        source_manifest.get("layout", {}).get("name")
    )
    expands_bottom_row = columns > int(source_layout["columns"])
    missing_count = columns - cutout_count if expands_bottom_row else 0
    if missing_count:
        if len(fallback_pokemon) != missing_count:
            raise ValueError(
                f"Layout {layout_name} expands the bottom row to {columns} "
                f"cards and needs {missing_count} additional Pokemon. Pass "
                "--fallback-pokemon once for every missing card."
            )
        if cutout_count == 1:
            occupied_slots = {columns // 2 + 1}
        else:
            last = columns - 1
            divisor = cutout_count - 1
            occupied_slots = {
                (index * last + divisor // 2) // divisor + 1
                for index in range(cutout_count)
            }
        missing_slots = [
            slot
            for slot in range(1, columns + 1)
            if slot not in occupied_slots
        ]
        candidates = pokemon.setdefault("fallback_candidates", [])
        candidates.extend(
            {"pokemon_id": pokemon_id, "slot": slot}
            for pokemon_id, slot in zip(
                fallback_pokemon,
                missing_slots,
                strict=True,
            )
        )
        pokemon["count"] = "auto_from_layout_columns"

    if layout_name == "wide_4x3":
        text_cells = manifest.setdefault("text_cells", {})
        text_cells.setdefault("title", {}).update({"row": 2, "column": 2})
        text_cells.setdefault("set_info", {}).update({"row": 2, "column": 3})

    if enable_pdf:
        pdf = manifest.setdefault("pdf", {})
        pdf["enabled"] = True
        pdf.setdefault("artwork_file", "poster-flux2-artwork.png")
        pdf.setdefault("insertion", "after_first_section_cover")
    return manifest


def _write_yaml(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            value,
            allow_unicode=True,
            sort_keys=False,
            width=88,
        ),
        encoding="utf-8",
    )


def _parse_section_fallbacks(values: list[str]) -> dict[str, tuple[int, ...]]:
    """Parse repeatable SECTION=POKEMON_ID fallback assignments."""
    parsed: dict[str, list[int]] = {}
    for value in values:
        section, separator, pokemon_id_text = value.partition("=")
        if not separator or not section or not pokemon_id_text:
            raise ValueError(
                "Section fallbacks must use SECTION=POKEMON_ID"
            )
        try:
            pokemon_id = int(pokemon_id_text)
        except ValueError as exc:
            raise ValueError(
                f"Invalid Pokemon ID in section fallback: {value!r}"
            ) from exc
        if pokemon_id <= 0:
            raise ValueError(
                f"Pokemon IDs must be positive in section fallback: {value!r}"
            )
        parsed.setdefault(section, []).append(pokemon_id)
    return {
        section: tuple(pokemon_ids)
        for section, pokemon_ids in parsed.items()
    }


def create_custom_layout_workspace(
    scope: str,
    layout_name: str,
    *,
    sections: tuple[str, ...] = (),
    output_root: Path | None = None,
    source_assets: Path = TRACKED_POSTER_ASSETS,
    fallback_pokemon: tuple[int, ...] = (),
    section_fallback_pokemon: dict[str, tuple[int, ...]] | None = None,
    include_unselected_promotions: bool = False,
) -> Path:
    """Clone custom inputs and optionally retain other aggregate promotions."""
    resolve_layout_name(layout_name)
    source_assets = source_assets.resolve()
    target = _target_root(scope, layout_name, sections, output_root)
    if target.exists():
        raise FileExistsError(
            f"Custom layout workspace already exists: {target}. "
            "Choose another --output or remove that ignored workspace first."
        )

    bundles = _selected_bundles(scope, sections, source_assets)
    section_fallback_pokemon = section_fallback_pokemon or {}
    if fallback_pokemon and section_fallback_pokemon:
        raise ValueError(
            "Use either fallback_pokemon or section_fallback_pokemon, not both"
        )
    selected_section_ids = {
        bundle.section_id or bundle.poster_id
        for bundle in bundles
    }
    unknown_fallback_sections = (
        set(section_fallback_pokemon) - selected_section_ids
    )
    if unknown_fallback_sections:
        raise ValueError(
            "Fallback Pokemon configured for unselected sections: "
            + ", ".join(sorted(unknown_fallback_sections))
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{target.name}-", dir=target.parent))
    try:
        aggregate = "/" not in scope and (
            source_assets / scope / POSTER_INDEX_NAME
        ).is_file()
        index_items: list[dict[str, Any]] = []
        custom_index_items: dict[str, dict[str, Any]] = {}

        source_index_by_id: dict[str, dict[str, Any]] = {}
        if aggregate:
            source_index = load_yaml(source_assets / scope / POSTER_INDEX_NAME)
            source_index_by_id = {
                str(item.get("id")): item
                for item in source_index.get("posters", [])
                if isinstance(item, dict)
            }

        for bundle in bundles:
            section_id = bundle.section_id or bundle.poster_id
            relative_asset = Path(*bundle.asset_key.split("/"))
            target_dir = stage / relative_asset
            target_dir.mkdir(parents=True, exist_ok=True)
            cutout_count = _copy_inputs(bundle.asset_dir, target_dir, bundle.manifest)
            manifest = _custom_manifest(
                bundle.manifest,
                layout_name,
                cutout_count,
                enable_pdf=not aggregate,
                fallback_pokemon=section_fallback_pokemon.get(
                    section_id,
                    fallback_pokemon,
                ),
            )
            _write_yaml(target_dir / POSTER_MANIFEST_NAME, manifest)

            cutout_manifest_path = target_dir / "cutouts" / "manifest.json"
            cutout_manifest = json.loads(
                cutout_manifest_path.read_text(encoding="utf-8")
            )
            layout = resolve_layout_name(layout_name)
            cutout_manifest["layout"] = {
                "name": layout_name,
                "columns": int(layout["columns"]),
                "rows": int(layout["rows"]),
            }
            cutout_manifest_path.write_text(
                json.dumps(cutout_manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            if aggregate:
                item = copy.deepcopy(source_index_by_id[bundle.poster_id])
                pdf = item.setdefault("pdf", {})
                pdf["enabled"] = True
                pdf["artwork_file"] = manifest.get("artwork", {}).get(
                    "promoted_file",
                    "poster-flux2-artwork.png",
                )
                pdf["insertion"] = "after_section_cover"
                custom_index_items[bundle.poster_id] = item

        if aggregate:
            if include_unselected_promotions:
                selected_ids = set(custom_index_items)
                for source_bundle in poster_bundles_for_scope(
                    scope,
                    poster_assets=source_assets,
                ):
                    if source_bundle.poster_id in selected_ids:
                        continue
                    relative_asset = Path(*source_bundle.asset_key.split("/"))
                    shutil.copytree(
                        source_bundle.asset_dir,
                        stage / relative_asset,
                        ignore=shutil.ignore_patterns(
                            ".DS_Store",
                            "__pycache__",
                            "comfyui_poster",
                        ),
                    )
                index_items = [
                    custom_index_items.get(
                        str(item.get("id")),
                        copy.deepcopy(item),
                    )
                    for item in source_index.get("posters", [])
                    if isinstance(item, dict)
                ]
            else:
                index_items = [
                    custom_index_items[bundle.poster_id]
                    for bundle in bundles
                ]
            _write_yaml(
                stage / scope / POSTER_INDEX_NAME,
                {
                    "schema_version": 1,
                    "scope": scope,
                    "posters": index_items,
                },
            )

        _write_yaml(
            stage / "workspace.yaml",
            {
                "schema_version": 1,
                "source_scope": scope,
                "layout": layout_name,
                "sections": [
                    bundle.section_id or bundle.poster_id
                    for bundle in bundles
                ],
                "included_unselected_promotions": (
                    include_unselected_promotions
                ),
                "section_fallback_pokemon": {
                    section: list(pokemon_ids)
                    for section, pokemon_ids in sorted(
                        section_fallback_pokemon.items()
                    )
                },
                "note": "Ignored local workspace; do not use as release input.",
            },
        )
        stage.replace(target)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--layout", choices=tuple(sorted(LAYOUTS)), required=True)
    parser.add_argument(
        "--section",
        action="append",
        default=[],
        help="Limit an aggregate scope to one section; may be repeated",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Poster-assets root (default: tmp/custom-poster-layouts/...)",
    )
    parser.add_argument(
        "--fallback-pokemon",
        action="append",
        type=int,
        default=[],
        help=(
            "Pokemon ID for one newly added bottom-row card; repeat once "
            "for every column added by the custom layout"
        ),
    )
    parser.add_argument(
        "--section-fallback-pokemon",
        action="append",
        default=[],
        metavar="SECTION=POKEMON_ID",
        help=(
            "Additional bottom-row Pokemon for one aggregate section; "
            "repeat for each section or missing card"
        ),
    )
    parser.add_argument(
        "--include-unselected-promotions",
        action="store_true",
        help=(
            "For a partial aggregate workspace, copy the other existing "
            "promoted bundles so their artwork pages remain in local PDFs"
        ),
    )
    args = parser.parse_args()
    try:
        section_fallback_pokemon = _parse_section_fallbacks(
            args.section_fallback_pokemon
        )
        target = create_custom_layout_workspace(
            args.scope,
            args.layout,
            sections=tuple(args.section),
            output_root=args.output,
            fallback_pokemon=tuple(args.fallback_pokemon),
            section_fallback_pokemon=section_fallback_pokemon,
            include_unselected_promotions=args.include_unselected_promotions,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Created ignored custom-layout workspace: {target}")
    print(f'export BINDER_POKEDEX_POSTER_ASSETS="{target}"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
