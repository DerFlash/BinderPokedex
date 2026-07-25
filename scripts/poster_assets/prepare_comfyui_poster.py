#!/usr/bin/env python3
"""Prepare the exact character composition reference for ComfyUI."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter

try:
    from .create_comfyui_poster_workflow import output_dimensions
    from .layout import build_page_layout
    from .render_poster import cutout_placements, load_yaml
except ImportError:
    from create_comfyui_poster_workflow import output_dimensions
    from layout import build_page_layout
    from render_poster import cutout_placements, load_yaml


ROOT = Path(__file__).resolve().parents[2]
POSTER_ASSETS = ROOT / "data" / "poster_assets"


def card_safe_conditioning_placements(
    placements: list[dict[str, object]], tall_scale: float = 0.22
) -> list[dict[str, object]]:
    """Add model-compensation padding around tall subjects in the layout reference."""
    result: list[dict[str, object]] = []
    for placement in placements:
        image = placement["image"]
        alpha_box = image.getchannel("A").getbbox()
        if alpha_box is None:
            raise ValueError("Conditioning placement has no visible pixels")
        alpha_width = alpha_box[2] - alpha_box[0]
        alpha_height = alpha_box[3] - alpha_box[1]
        if alpha_width / alpha_height >= 0.85:
            result.append(placement)
            continue

        resized = image.resize(
            (round(image.width * tall_scale), round(image.height * tall_scale)),
            Image.Resampling.LANCZOS,
        )
        resized_box = resized.getchannel("A").getbbox()
        if resized_box is None:
            raise ValueError("Resized conditioning placement has no visible pixels")
        cell = placement["cell"]
        baseline = placement["y"] + alpha_box[3]
        adjusted = dict(placement)
        adjusted.update(
            image=resized,
            x=(
                cell.x
                + (cell.width - resized.width) // 2
                - round(cell.width * 0.28)
            ),
            y=baseline - resized_box[3] + round(cell.height * 0.10),
        )
        result.append(adjusted)
    return result


def build_identity_references(scope_dir: Path, manifest: dict[str, Any]) -> None:
    """Write compact appearance references without encoding scene placement.

    Position belongs exclusively to ``scene_reference.png``. Neutral-canvas
    padding reinforces the relative scene scale without the large poster-shaped
    reference latents that exhaust unified memory on Apple Silicon.
    """
    layout_name = manifest.get("layout", {}).get("name", "standard_3x3")
    width, _ = output_dimensions(scope_dir.name, 1.0)
    placements = cutout_placements(
        build_page_layout(layout_name, width_px=width), scope_dir
    )
    scene_placements = card_safe_conditioning_placements(placements)
    scene_extents = []
    for placement in scene_placements:
        box = placement["image"].getchannel("A").getbbox()
        if box is None:
            raise ValueError("Scene placement has no visible pixels")
        scene_extents.append(max(box[2] - box[0], box[3] - box[1]))
    largest_scene_extent = max(scene_extents)
    neutral = (226, 224, 211)
    reference_path = scope_dir / "comfyui_poster" / "identity_reference_1.png"
    for index, (placement, scene_extent) in enumerate(
        zip(placements, scene_extents), start=1
    ):
        original = Image.open(
            scope_dir / "cutouts" / placement["item"]["file"]
        ).convert("RGBA")
        original_box = original.getchannel("A").getbbox()
        if original_box is None:
            raise ValueError("Identity reference has no visible pixels")
        original = original.crop(original_box)
        reference_extent = max(
            150, round(350 * scene_extent / largest_scene_extent)
        )
        original.thumbnail(
            (reference_extent, reference_extent), Image.Resampling.LANCZOS
        )
        is_tall = original.width / original.height < 0.85
        canvas_extent = 768 if is_tall else 512
        reference = Image.new(
            "RGB", (canvas_extent, canvas_extent), neutral
        )
        x = (
            24
            if is_tall
            else (reference.width - original.width) // 2
        )
        y = reference.height - original.height - 24
        reference.paste(
            original.convert("RGB"),
            (x, y),
            original.getchannel("A"),
        )
        reference.save(
            reference_path.with_name(f"identity_reference_{index}.png"),
            format="PNG",
            optimize=True,
        )


def build_scene_reference(scope: str, megapixels: float) -> Path:
    """Place exact cutouts and write a protected identity-core mask."""
    scope_dir = POSTER_ASSETS / scope
    manifest = load_yaml(scope_dir / "poster.yaml")
    width, height = output_dimensions(scope, megapixels)
    layout = build_page_layout(manifest.get("layout", {}).get("name", "standard_3x3"), width_px=width)
    reference = Image.new("RGBA", (width, height), (226, 224, 211, 0))
    identity_alpha = Image.new("L", (width, height), 0)
    placements = cutout_placements(layout, scope_dir)
    scene_placements = card_safe_conditioning_placements(placements)
    for placement in scene_placements:
        reference.alpha_composite(placement["image"], (placement["x"], placement["y"]))
        identity_alpha.paste(
            placement["image"].getchannel("A"),
            (placement["x"], placement["y"]),
            placement["image"].getchannel("A"),
        )
    # Latent dimensions are rounded to multiples of 16; match them exactly.
    if reference.height != height:
        reference = reference.crop((0, 0, width, min(reference.height, height)))
        if reference.height < height:
            padded = Image.new("RGBA", (width, height), (226, 224, 211, 0))
            padded.alpha_composite(reference)
            reference = padded
    path = scope_dir / "comfyui_poster" / "scene_reference.png"
    reference.save(path, format="PNG", optimize=True)
    build_identity_references(scope_dir, manifest)
    # AnimaEdit is an image-edit model and strongly retains the source material.
    # Give it only an abstract sky/meadow material scaffold—not prior artwork or
    # layout geometry—so the transparent area is interpreted as landscape.
    anima_reference = Image.new("RGBA", (width, height), (184, 220, 235, 255))
    anima_draw = ImageDraw.Draw(anima_reference)
    # Abstract depth/material bands only. These are deliberately not finished
    # scenery and contain no semantic objects for the edit model to copy.
    anima_draw.polygon(
        (
            (0, round(height * 0.53)),
            (round(width * 0.18), round(height * 0.43)),
            (round(width * 0.38), round(height * 0.52)),
            (round(width * 0.62), round(height * 0.40)),
            (round(width * 0.82), round(height * 0.51)),
            (width, round(height * 0.44)),
            (width, round(height * 0.62)),
            (0, round(height * 0.62)),
        ),
        fill=(124, 154, 158, 255),
    )
    anima_draw.rectangle(
        (0, round(height * 0.57), width, round(height * 0.69)),
        fill=(64, 105, 76, 255),
    )
    anima_draw.rectangle(
        (0, round(height * 0.67), width, height), fill=(126, 170, 82, 255)
    )
    for placement in placements:
        anima_reference.alpha_composite(
            placement["image"], (placement["x"], placement["y"])
        )
    anima_reference.save(
        path.with_name("anima_scene_reference.png"), format="PNG", optimize=True
    )
    # Preserve the recognizable interior exactly while leaving a narrow contour
    # available to the model for coherent occlusion, lighting, and ground contact.
    erosion = max(3, round(width / 220) | 1)
    identity_core = identity_alpha.filter(ImageFilter.MinFilter(erosion))
    identity_core.convert("RGB").save(
        path.with_name("identity_core.png"), format="PNG", optimize=True
    )
    return path


def prepare(scope: str, megapixels: float = 1.0) -> Path:
    scope_dir = POSTER_ASSETS / scope
    work_dir = scope_dir / "comfyui_poster"
    required = (scope_dir / "poster.yaml", work_dir / "prompt.txt", scope_dir / "cutouts" / "manifest.json")
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(path)

    cutout_manifest = json.loads(required[-1].read_text(encoding="utf-8"))
    cutout_files = [scope_dir / "cutouts" / item["file"] for item in cutout_manifest.get("items", [])]
    if not cutout_files:
        raise ValueError(f"No cutouts listed in {required[-1]}")
    for path in cutout_files:
        if not path.is_file():
            raise FileNotFoundError(path)

    work_dir.mkdir(parents=True, exist_ok=True)
    for pattern in ("pokemon_*.png", "structure_guide.png"):
        for stale_path in work_dir.glob(pattern):
            stale_path.unlink()
    build_scene_reference(scope, megapixels)
    return work_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", default="Base1")
    parser.add_argument("--megapixels", type=float, default=1.0)
    args = parser.parse_args()
    print(prepare(args.scope, args.megapixels))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
