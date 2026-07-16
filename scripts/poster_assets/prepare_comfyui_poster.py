#!/usr/bin/env python3
"""Prepare the exact character composition reference for ComfyUI."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

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


def build_scene_reference(scope: str, megapixels: float) -> Path:
    """Place exact cutouts and write a protected identity-core mask."""
    scope_dir = POSTER_ASSETS / scope
    manifest = load_yaml(scope_dir / "poster.yaml")
    width, height = output_dimensions(scope, megapixels)
    layout = build_page_layout(manifest.get("layout", {}).get("name", "standard_3x3"), width_px=width)
    reference = Image.new("RGBA", (width, height), (226, 224, 211, 0))
    identity_alpha = Image.new("L", (width, height), 0)
    for placement in cutout_placements(layout, scope_dir):
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
    for placement in cutout_placements(layout, scope_dir):
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
