#!/usr/bin/env python3
"""Promote one reviewed text-free ComfyUI artwork into stable poster assets."""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

try:
    from .finalize_comfyui_poster import finalize
    from .layout import build_page_layout
    from .render_poster import load_yaml
    from .slice_poster import slice_poster
except ImportError:
    from finalize_comfyui_poster import finalize
    from layout import build_page_layout
    from render_poster import load_yaml
    from slice_poster import slice_poster


ROOT = Path(__file__).resolve().parents[2]
POSTER_ASSETS = ROOT / "data" / "poster_assets"


def promote(
    scope: str,
    artwork: Path,
    *,
    language: str = "en",
    name: str = "flux2",
    force: bool = False,
) -> tuple[Path, Path, list[Path]]:
    """Persist reviewed artwork, deterministic overlay, and physical card crops."""
    if not artwork.is_file():
        raise FileNotFoundError(artwork)

    scope_dir = POSTER_ASSETS / scope
    manifest_path = scope_dir / "poster.yaml"
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    manifest = load_yaml(manifest_path)

    source = Image.open(artwork).convert("RGB")
    layout = build_page_layout(
        manifest.get("layout", {}).get("name", "standard_3x3"),
        width_px=source.width,
    )
    if abs(layout.height_px - source.height) > 16:
        raise ValueError(
            f"Artwork ratio does not match poster layout: {source.size} vs "
            f"{(layout.width_px, layout.height_px)}"
        )

    artwork_path = scope_dir / f"poster-{name}-artwork.png"
    final_path = scope_dir / f"poster-{name}.png"
    cards_dir = scope_dir / f"poster-{name}-cards"
    existing = [path for path in (artwork_path, final_path) if path.exists()]
    if existing and not force:
        raise FileExistsError(
            f"Promoted asset already exists: {existing[0]} (use --force to replace)"
        )

    source.save(artwork_path, format="PNG", optimize=True)
    finalize(scope, artwork_path, final_path, language)
    card_paths = slice_poster(scope, final_path, cards_dir)
    return artwork_path, final_path, card_paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--artwork", required=True, type=Path)
    parser.add_argument("--language", default="en")
    parser.add_argument("--name", default="flux2")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    artwork_path, final_path, cards = promote(
        args.scope,
        args.artwork,
        language=args.language,
        name=args.name,
        force=args.force,
    )
    print(f"Artwork: {artwork_path}")
    print(f"Final poster: {final_path}")
    print(f"Card slices: {cards[0].parent} ({len(cards)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
