#!/usr/bin/env python3
"""Export a finished poster as one printable image per binder card cell."""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

try:
    from .layout import build_page_layout
    from .render_poster import load_yaml
except ImportError:
    from layout import build_page_layout
    from render_poster import load_yaml


ROOT = Path(__file__).resolve().parents[2]
POSTER_ASSETS = ROOT / "data" / "poster_assets"


def slice_poster(scope: str, source: Path, output_dir: Path | None = None) -> list[Path]:
    """Crop the card areas and discard the physical binder gaps between them."""
    scope_dir = POSTER_ASSETS / scope
    manifest = load_yaml(scope_dir / "poster.yaml")
    image = Image.open(source).convert("RGB")
    layout = build_page_layout(
        manifest.get("layout", {}).get("name", "standard_3x3"),
        width_px=image.width,
    )
    if abs(layout.height_px - image.height) > 16:
        raise ValueError(
            f"Poster ratio does not match card layout: {image.size} vs "
            f"{(layout.width_px, layout.height_px)}"
        )

    target_dir = output_dir or source.with_name(f"{source.stem}_cards")
    target_dir.mkdir(parents=True, exist_ok=True)
    for stale_path in target_dir.glob("card_r*_c*.png"):
        stale_path.unlink()
    outputs: list[Path] = []
    for row in range(1, layout.rows + 1):
        for column in range(1, layout.columns + 1):
            cell = layout.cell(row, column)
            card = image.crop(
                (
                    cell.x,
                    cell.y,
                    cell.x + cell.width,
                    cell.y + cell.height,
                )
            )
            path = target_dir / f"card_r{row}_c{column}.png"
            card.save(path, format="PNG", optimize=True)
            outputs.append(path)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", default="Base1")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    outputs = slice_poster(args.scope, args.input, args.output_dir)
    print(f"Wrote {len(outputs)} card images to {outputs[0].parent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
