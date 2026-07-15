#!/usr/bin/env python3
"""Build a layout-accurate composition guide for background generation."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFilter

try:
    from .layout import build_page_layout
    from .render_poster import cutout_placements
except ImportError:  # Direct script execution
    from layout import build_page_layout
    from render_poster import cutout_placements


ROOT = Path(__file__).resolve().parents[2]
POSTER_ASSETS_DIR = ROOT / "data" / "poster_assets"


def build_guide(scope: str, width_px: int = 1400) -> Path:
    scope_dir = POSTER_ASSETS_DIR / scope
    manifest_path = scope_dir / "poster.yaml"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Poster manifest not found: {manifest_path}")

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    layout = build_page_layout(manifest.get("layout", {}).get("name"), width_px=width_px)
    guide = Image.new("RGBA", (layout.width_px, layout.height_px), (112, 132, 112, 255))
    draw = ImageDraw.Draw(guide, "RGBA")

    # Calm regions reserved for deterministic text panels.
    text_cells = manifest.get("text_cells", {})
    for key, color in (("title", (70, 145, 220, 150)), ("set_info", (55, 190, 200, 150))):
        config = text_cells[key]
        cell = layout.cell(int(config["row"]), int(config["column"]))
        draw.rounded_rectangle(cell.inset(0.07, 0.12), radius=24, fill=color)

    # Actual cutouts communicate identity, silhouette, scale, and exact placement.
    # A dilated halo marks the region where tall foreground details are forbidden.
    for placement in cutout_placements(layout, scope_dir):
        target = placement["image"]
        x, y = placement["x"], placement["y"]
        alpha = target.getchannel("A")
        halo = alpha.filter(ImageFilter.MaxFilter(41)).filter(ImageFilter.GaussianBlur(5))
        warning = Image.new("RGBA", target.size, (225, 70, 95, 0))
        warning.putalpha(halo.point(lambda value: round(value * 0.42)))
        guide.alpha_composite(warning, (x, y))
        guide.alpha_composite(target, (x, y))

    # The shared contact baseline is explicit and identical to the renderer geometry.
    placements = cutout_placements(layout, scope_dir)
    foot_y_values = []
    for placement in placements:
        bbox = placement["image"].getchannel("A").getbbox()
        if bbox:
            foot_y_values.append(placement["y"] + bbox[3])
    if foot_y_values:
        baseline = max(foot_y_values)
        draw.line((0, baseline, layout.width_px, baseline), fill=(255, 210, 55, 210), width=5)

    # Cell boundaries are planning metadata, never desired artwork.
    for row in range(1, layout.rows + 1):
        for column in range(1, layout.columns + 1):
            cell = layout.cell(row, column)
            draw.rectangle(
                (cell.x, cell.y, cell.x + cell.width, cell.y + cell.height),
                outline=(255, 255, 255, 75),
                width=2,
            )

    out_path = scope_dir / "background" / "composition_guide.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    guide.convert("RGB").save(out_path, format="PNG", optimize=True)
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--width", type=int, default=1400)
    args = parser.parse_args()
    try:
        out_path = build_guide(args.scope, width_px=args.width)
        print(out_path)
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
