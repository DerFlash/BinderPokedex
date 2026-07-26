"""Character-placement helpers shared by poster conditioning workflows."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image

try:
    from .layout import PageLayout
    from .poster_io import load_cutout_items
except ImportError:
    from layout import PageLayout
    from poster_io import load_cutout_items


def fit_image(image: Image.Image, max_width: int, max_height: int) -> Image.Image:
    scale = min(max_width / image.width, max_height / image.height)
    return image.resize(
        (round(image.width * scale), round(image.height * scale)),
        Image.Resampling.LANCZOS,
    )


def cutout_placements(
    layout: PageLayout,
    scope_dir: Path,
) -> list[dict[str, Any]]:
    """Place one complete cutout inside each bottom-row physical card."""
    cells = layout.bottom_row_cells()
    items = load_cutout_items(scope_dir)
    if len(items) != len(cells):
        raise ValueError(
            f"Layout '{layout.name}' needs {len(cells)} character cutouts, "
            f"but {scope_dir / 'cutouts' / 'manifest.json'} contains {len(items)}"
        )
    prepared = []
    for cell, item in zip(cells, items):
        cutout_path = scope_dir / "cutouts" / item["file"]
        cutout = Image.open(cutout_path).convert("RGBA")
        target = fit_image(
            cutout,
            round(cell.width * 0.84),
            round(cell.height * 0.68),
        )
        prepared.append((cell, item, target))

    placements = []
    baseline = cells[0].y + round(cells[0].height * 0.80)
    for cell, item, target in prepared:
        x = cell.x + (cell.width - target.width) // 2
        alpha_box = target.getchannel("A").getbbox()
        if alpha_box is None:
            raise ValueError(f"Cutout has no visible pixels: {item['file']}")
        y = baseline - alpha_box[3]
        placements.append(
            {
                "cell": cell,
                "item": item,
                "image": target,
                "x": x,
                "y": y,
            }
        )
    return placements
