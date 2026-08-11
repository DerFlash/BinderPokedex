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
    if pokemon.get("count", "auto_from_layout_columns") == "auto_from_layout_columns":
        if cutout_count != columns:
            pokemon["count"] = cutout_count
    elif int(pokemon["count"]) > columns:
        raise ValueError(
            f"Configured subject count {pokemon['count']} exceeds {layout_name}"
        )

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


def create_custom_layout_workspace(
    scope: str,
    layout_name: str,
    *,
    sections: tuple[str, ...] = (),
    output_root: Path | None = None,
    source_assets: Path = TRACKED_POSTER_ASSETS,
) -> Path:
    """Clone configuration and source inputs without copying promoted artwork."""
    resolve_layout_name(layout_name)
    source_assets = source_assets.resolve()
    target = _target_root(scope, layout_name, sections, output_root)
    if target.exists():
        raise FileExistsError(
            f"Custom layout workspace already exists: {target}. "
            "Choose another --output or remove that ignored workspace first."
        )

    bundles = _selected_bundles(scope, sections, source_assets)
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{target.name}-", dir=target.parent))
    try:
        aggregate = "/" not in scope and (
            source_assets / scope / POSTER_INDEX_NAME
        ).is_file()
        index_items: list[dict[str, Any]] = []

        source_index_by_id: dict[str, dict[str, Any]] = {}
        if aggregate:
            source_index = load_yaml(source_assets / scope / POSTER_INDEX_NAME)
            source_index_by_id = {
                str(item.get("id")): item
                for item in source_index.get("posters", [])
                if isinstance(item, dict)
            }

        for bundle in bundles:
            relative_asset = Path(*bundle.asset_key.split("/"))
            target_dir = stage / relative_asset
            target_dir.mkdir(parents=True, exist_ok=True)
            cutout_count = _copy_inputs(bundle.asset_dir, target_dir, bundle.manifest)
            manifest = _custom_manifest(
                bundle.manifest,
                layout_name,
                cutout_count,
                enable_pdf=not aggregate,
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
                index_items.append(item)

        if aggregate:
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
    args = parser.parse_args()
    try:
        target = create_custom_layout_workspace(
            args.scope,
            args.layout,
            sections=tuple(args.section),
            output_root=args.output,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Created ignored custom-layout workspace: {target}")
    print(f'export BINDER_POKEDEX_POSTER_ASSETS="{target}"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
