"""Character-placement helpers shared by poster conditioning workflows."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image

try:
    from .layout import PageLayout, build_source_layout
    from .poster_io import load_cutout_items
except ImportError:
    from layout import PageLayout, build_source_layout
    from poster_io import load_cutout_items


JOINT_SCENE_MAX_WIDTH_RATIO = 0.58
JOINT_SCENE_MAX_HEIGHT_RATIO = 0.52
JOINT_SCENE_BASELINE_RATIO = 0.88
JOINT_SCENE_OUTER_SHIFT_RATIO = 0.16


def fit_image(image: Image.Image, max_width: int, max_height: int) -> Image.Image:
    scale = min(max_width / image.width, max_height / image.height)
    return image.resize(
        (round(image.width * scale), round(image.height * scale)),
        Image.Resampling.LANCZOS,
    )


def validate_visible_placements(
    placements: list[dict[str, Any]],
    *,
    canvas_size: tuple[int, int] | None = None,
    description: str = "Character",
) -> None:
    """Reject visible pixels outside their card or the real image canvas."""
    if canvas_size is not None:
        canvas_width, canvas_height = canvas_size
        if canvas_width <= 0 or canvas_height <= 0:
            raise ValueError("Placement canvas dimensions must be positive")

    for placement in placements:
        image = placement["image"]
        alpha_box = image.getchannel("A").getbbox()
        if alpha_box is None:
            raise ValueError(f"{description} placement has no visible pixels")
        left = placement["x"] + alpha_box[0]
        top = placement["y"] + alpha_box[1]
        right = placement["x"] + alpha_box[2]
        bottom = placement["y"] + alpha_box[3]
        cell = placement["cell"]
        if not (
            cell.x <= left < right <= cell.x + cell.width
            and cell.y <= top < bottom <= cell.y + cell.height
        ):
            raise ValueError(
                f"{description} for Pokemon "
                f"#{placement['item'].get('pokemon_id')} moves its visible "
                "silhouette outside the assigned print-safe region"
            )
        if canvas_size is not None and not (
            0 <= left < right <= canvas_width
            and 0 <= top < bottom <= canvas_height
        ):
            raise ValueError(
                f"{description} for Pokemon "
                f"#{placement['item'].get('pokemon_id')} moves its visible "
                "silhouette outside the real generation canvas"
            )


def normalized_visible_placement_contract(
    placements: list[dict[str, Any]],
    *,
    canvas_size: tuple[int, int],
) -> list[dict[str, int]]:
    """Describe target silhouettes as stable per-mille canvas coordinates."""
    validate_visible_placements(
        placements,
        canvas_size=canvas_size,
    )
    width, height = canvas_size
    contract: list[dict[str, int]] = []
    for placement in placements:
        alpha_box = placement["image"].getchannel("A").getbbox()
        if alpha_box is None:
            raise ValueError("Character placement has no visible pixels")
        left = int(placement["x"]) + alpha_box[0]
        top = int(placement["y"]) + alpha_box[1]
        right = int(placement["x"]) + alpha_box[2]
        bottom = int(placement["y"]) + alpha_box[3]
        contract.append(
            {
                "left_per_mille": round(left * 1000 / width),
                "top_per_mille": round(top * 1000 / height),
                "right_per_mille": round(right * 1000 / width),
                "bottom_per_mille": round(bottom * 1000 / height),
            }
        )
    return contract


def cutout_placements(
    layout: PageLayout,
    scope_dir: Path,
    *,
    max_width_ratio: float = 0.84,
    max_height_ratio: float = 0.68,
    baseline_ratio: float = 0.80,
) -> list[dict[str, Any]]:
    """Place one complete cutout inside each bottom-row physical card."""
    for name, value in (
        ("max_width_ratio", max_width_ratio),
        ("max_height_ratio", max_height_ratio),
        ("baseline_ratio", baseline_ratio),
    ):
        if not 0 < value <= 1:
            raise ValueError(f"{name} must be in the range (0, 1]")
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
            round(cell.width * max_width_ratio),
            round(cell.height * max_height_ratio),
        )
        prepared.append((cell, item, target))

    placements = []
    baseline = cells[0].y + round(cells[0].height * baseline_ratio)
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
    validate_visible_placements(
        placements,
        canvas_size=(layout.width_px, layout.height_px),
    )
    return placements


def joint_scene_cutout_placements(
    layout: PageLayout,
    scope_dir: Path,
) -> list[dict[str, Any]]:
    """Return conservative generative bounds with ample crop tolerance."""
    placements = cutout_placements(
        layout,
        scope_dir,
        max_width_ratio=JOINT_SCENE_MAX_WIDTH_RATIO,
        max_height_ratio=JOINT_SCENE_MAX_HEIGHT_RATIO,
        baseline_ratio=JOINT_SCENE_BASELINE_RATIO,
    )
    count = len(placements)
    if count == 1:
        directions = (0.0,)
    else:
        midpoint = (count - 1) / 2
        directions = tuple(
            (index - midpoint) / midpoint
            for index in range(count)
        )
    adjusted = []
    for placement, direction in zip(
        placements,
        directions,
        strict=True,
    ):
        item = dict(placement)
        item["x"] = int(item["x"]) + round(
            item["cell"].width
            * JOINT_SCENE_OUTER_SHIFT_RATIO
            * direction
        )
        adjusted.append(item)
    validate_visible_placements(
        adjusted,
        canvas_size=(layout.width_px, layout.height_px),
        description="Joint-scene",
    )
    return adjusted


def joint_scene_canvas_placements(
    scope_dir: Path,
    *,
    layout_name: str,
    canvas_size: tuple[int, int],
) -> list[dict[str, Any]]:
    """Build the canonical joint-scene placements for one raster canvas."""
    width, height = canvas_size
    layout = build_source_layout(
        layout_name,
        width_px=width,
        height_px=height,
    )
    return joint_scene_cutout_placements(layout, scope_dir)
