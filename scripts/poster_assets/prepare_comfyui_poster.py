#!/usr/bin/env python3
"""Prepare the exact character composition reference for ComfyUI."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter

try:
    from .composition import cutout_placements, validate_visible_placements
    from .create_comfyui_poster_workflow import output_dimensions
    from .layout import build_page_layout
    from .poster_config import (
        IDENTITY_LOCK_PROMPT_FILE,
        build_identity_lock_prompt,
        identity_lock_config,
        subject_conditioning,
    )
    from .poster_io import (
        load_poster_scope_data,
        poster_bundle,
    )
except ImportError:
    from composition import cutout_placements, validate_visible_placements
    from create_comfyui_poster_workflow import output_dimensions
    from layout import build_page_layout
    from poster_config import (
        IDENTITY_LOCK_PROMPT_FILE,
        build_identity_lock_prompt,
        identity_lock_config,
        subject_conditioning,
    )
    from poster_io import load_poster_scope_data, poster_bundle


ROOT = Path(__file__).resolve().parents[2]
POSTER_ASSETS = ROOT / "data" / "poster_assets"


def card_safe_conditioning_placements(
    placements: list[dict[str, object]],
    manifest: dict[str, Any],
    *,
    canvas_size: tuple[int, int],
) -> list[dict[str, object]]:
    """Apply explicit, per-subject composition-reference compensation."""
    result: list[dict[str, object]] = []
    for placement in placements:
        config = subject_conditioning(
            manifest, placement["item"]
        ).get("composition", {})
        if not isinstance(config, dict):
            raise ValueError("Subject composition conditioning must be a mapping")
        scale = float(config.get("scale", 1.0))
        x_offset = float(config.get("x_offset_cell", 0.0))
        baseline_offset = float(config.get("baseline_offset_cell", 0.0))
        if scale <= 0:
            raise ValueError("Subject composition scale must be positive")
        if scale == 1.0 and x_offset == 0.0 and baseline_offset == 0.0:
            result.append(placement)
            continue

        image = placement["image"]
        alpha_box = image.getchannel("A").getbbox()
        if alpha_box is None:
            raise ValueError("Conditioning placement has no visible pixels")

        resized = image.resize(
            (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
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
                + round(cell.width * x_offset)
            ),
            y=baseline
            - resized_box[3]
            + round(cell.height * baseline_offset),
        )
        result.append(adjusted)
    validate_visible_placements(
        result,
        canvas_size=canvas_size,
        description="Conditioning",
    )
    return result


def build_identity_references(
    scope_dir: Path,
    manifest: dict[str, Any],
    output_dir: Path | None = None,
    *,
    asset_key: str | None = None,
) -> None:
    """Write compact appearance references without encoding scene placement.

    Position belongs exclusively to ``scene_reference.png``. Neutral-canvas
    padding reinforces the relative scene scale without the large poster-shaped
    reference latents that exhaust unified memory on Apple Silicon.
    """
    layout_name = manifest.get("layout", {}).get("name", "standard_3x3")
    width, height = output_dimensions(asset_key or scope_dir.name, 1.0)
    layout = build_page_layout(layout_name, width_px=width)
    placements = cutout_placements(
        layout, scope_dir
    )
    validate_visible_placements(
        placements,
        canvas_size=(width, height),
    )
    scene_placements = card_safe_conditioning_placements(
        placements,
        manifest,
        canvas_size=(width, height),
    )
    scene_extents = []
    for placement in scene_placements:
        box = placement["image"].getchannel("A").getbbox()
        if box is None:
            raise ValueError("Scene placement has no visible pixels")
        scene_extents.append(max(box[2] - box[0], box[3] - box[1]))
    largest_scene_extent = max(scene_extents)
    conditioning = manifest.get("conditioning", {})
    identity_defaults = conditioning.get("identity_defaults", {})
    neutral_values = identity_defaults.get("neutral_rgb", [226, 224, 211])
    if (
        not isinstance(neutral_values, list)
        or len(neutral_values) != 3
        or not all(isinstance(value, int) and 0 <= value <= 255 for value in neutral_values)
    ):
        raise ValueError("conditioning.identity_defaults.neutral_rgb must contain 3 RGB integers")
    neutral = tuple(neutral_values)
    min_subject_px = int(identity_defaults.get("min_subject_px", 150))
    max_subject_px = int(identity_defaults.get("max_subject_px", 350))
    default_canvas_px = int(identity_defaults.get("canvas_px", 512))
    default_bottom_padding_px = int(identity_defaults.get("bottom_padding_px", 24))
    reference_dir = output_dir or scope_dir / "comfyui_poster"
    reference_dir.mkdir(parents=True, exist_ok=True)
    reference_path = reference_dir / "identity_reference_1.png"
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
            min_subject_px,
            round(max_subject_px * scene_extent / largest_scene_extent),
        )
        original.thumbnail(
            (reference_extent, reference_extent), Image.Resampling.LANCZOS
        )
        identity_config = subject_conditioning(
            manifest, placement["item"]
        ).get("identity", {})
        if not isinstance(identity_config, dict):
            raise ValueError("Subject identity conditioning must be a mapping")
        canvas_extent = int(
            identity_config.get("canvas_px", default_canvas_px)
        )
        bottom_padding = int(
            identity_config.get(
                "bottom_padding_px", default_bottom_padding_px
            )
        )
        reference = Image.new(
            "RGB", (canvas_extent, canvas_extent), neutral
        )
        align_x = identity_config.get("align_x", "center")
        x_padding = int(identity_config.get("x_padding_px", 24))
        if align_x == "left":
            x = x_padding
        elif align_x == "right":
            x = reference.width - original.width - x_padding
        elif align_x == "center":
            x = (reference.width - original.width) // 2
        else:
            raise ValueError("identity.align_x must be left, center, or right")
        y = reference.height - original.height - bottom_padding
        if x < 0 or y < 0 or x + original.width > canvas_extent:
            raise ValueError(
                f"Identity canvas is too small for Pokemon "
                f"#{placement['item'].get('pokemon_id')}"
            )
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


def build_qwen_identity_references(
    scope_dir: Path,
    placements: list[dict[str, object]],
    output_dir: Path,
) -> None:
    """Write two detail sheets for Qwen's three-image edit interface."""
    groups = (
        placements[: max(1, len(placements) // 2)],
        placements[max(1, len(placements) // 2) :],
    )
    neutral = (226, 224, 211)
    cell_width = 512
    canvas_height = 640
    for sheet_index, group in enumerate(groups, start=1):
        sheet = Image.new(
            "RGB",
            (cell_width * max(1, len(group)), canvas_height),
            neutral,
        )
        for column, placement in enumerate(group):
            item = placement["item"]
            original = Image.open(
                scope_dir / "cutouts" / str(item["file"])
            ).convert("RGBA")
            alpha_box = original.getchannel("A").getbbox()
            if alpha_box is None:
                raise ValueError("Qwen identity reference has no visible pixels")
            original = original.crop(alpha_box)
            original.thumbnail(
                (cell_width - 72, canvas_height - 96),
                Image.Resampling.LANCZOS,
            )
            x = column * cell_width + (cell_width - original.width) // 2
            y = (canvas_height - original.height) // 2
            sheet.paste(
                original.convert("RGB"),
                (x, y),
                original.getchannel("A"),
            )
        sheet.save(
            output_dir / f"qwen_identity_reference_{sheet_index}.png",
            format="PNG",
            optimize=True,
        )


def build_upper_context_mask(
    width: int,
    height: int,
    placements: list[dict[str, object]],
    manifest: dict[str, Any],
    output_dir: Path,
) -> tuple[int, int]:
    """Write separate sampling and feather masks for identity-lock pass two."""
    config = identity_lock_config(manifest)
    subject_tops = []
    for placement in placements:
        visible_box = placement["image"].getchannel("A").getbbox()
        if visible_box is None:
            raise ValueError("Identity-lock placement has no visible pixels")
        subject_tops.append(int(placement["y"]) + visible_box[1])

    if not subject_tops:
        raise ValueError("Identity lock needs at least one subject placement")
    subject_top = min(subject_tops)
    clearance = round(height * config["subject_clearance_ratio"])
    configured_limit = round(
        height * config["max_protected_start_ratio"]
    )
    protected_start = min(configured_limit, subject_top - clearance)
    transition_height = max(
        1,
        round(height * config["transition_ratio"]),
    )
    transition_start = protected_start - transition_height
    if transition_start < 0 or protected_start <= transition_start:
        raise ValueError(
            "Identity-lock subjects leave no safe upper context region; "
            "reduce their size or artwork.identity_lock transition/clearance"
        )
    if subject_top < protected_start + clearance:
        raise ValueError(
            "Identity-lock subject clearance could not be preserved"
        )

    alpha = Image.new("L", (width, height), 255)
    alpha_draw = ImageDraw.Draw(alpha)
    alpha_draw.rectangle((0, 0, width, transition_start), fill=0)
    for y in range(transition_start, protected_start):
        value = round(255 * (y - transition_start) / transition_height)
        alpha_draw.line((0, y, width, y), fill=value)
    mask_image = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    mask_image.putalpha(alpha)
    mask_image.save(
        output_dir / "upper_context_mask.png",
        format="PNG",
        optimize=True,
    )

    # VAEEncodeForInpaint thresholds/quantizes a soft mask in latent space.
    # Feeding it the same feather that is used for the final RGB composite can
    # therefore switch source images around the feather midpoint and create a
    # straight exposure seam. Let sampling continue beyond the visible feather
    # instead. Its hard latent boundary then lies where the final composite is
    # already fully restored from the continuous first-pass scene.
    latent_overlap = max(16, round(height * 0.02))
    aligned_generation_end = (
        (protected_start + latent_overlap + 15) // 16
    ) * 16
    generation_end = min(
        height - 1,
        subject_top - 1,
        aligned_generation_end,
    )
    generation_alpha = Image.new("L", (width, height), 255)
    ImageDraw.Draw(generation_alpha).rectangle(
        (0, 0, width, generation_end),
        fill=0,
    )
    generation_mask = Image.new(
        "RGBA",
        (width, height),
        (0, 0, 0, 255),
    )
    generation_mask.putalpha(generation_alpha)
    generation_mask.save(
        output_dir / "upper_context_generation_mask.png",
        format="PNG",
        optimize=True,
    )
    return transition_start, protected_start


def build_scene_reference(
    scope: str,
    megapixels: float,
    output_dir: Path | None = None,
) -> Path:
    """Write model-compensated edit and exact identity-lock references."""
    bundle = poster_bundle(scope, poster_assets=POSTER_ASSETS)
    scope_dir = bundle.asset_dir
    manifest = bundle.manifest
    reference_dir = output_dir or scope_dir / "comfyui_poster"
    reference_dir.mkdir(parents=True, exist_ok=True)
    width, height = output_dimensions(scope, megapixels)
    layout = build_page_layout(
        manifest.get("layout", {}).get("name", "standard_3x3"),
        width_px=width,
    )
    reference = Image.new("RGBA", (width, height), (226, 224, 211, 0))
    placements = cutout_placements(layout, scope_dir)
    validate_visible_placements(
        placements,
        canvas_size=(width, height),
    )
    scene_placements = card_safe_conditioning_placements(
        placements,
        manifest,
        canvas_size=(width, height),
    )
    for placement in scene_placements:
        reference.alpha_composite(placement["image"], (placement["x"], placement["y"]))
    # Latent dimensions are rounded to multiples of 16; match them exactly.
    if reference.height != height:
        reference = reference.crop((0, 0, width, min(reference.height, height)))
        if reference.height < height:
            padded = Image.new("RGBA", (width, height), (226, 224, 211, 0))
            padded.alpha_composite(reference)
            reference = padded
    path = reference_dir / "scene_reference.png"
    reference.save(path, format="PNG", optimize=True)

    # Inpainting is not a semantic redraw. It needs the reviewed cutouts at
    # their final size and position; edit-only compensation would make the
    # model see missing or undersized subjects and invent replacements.
    inpaint_reference = Image.new(
        "RGBA", (width, height), (226, 224, 211, 0)
    )
    for placement in placements:
        inpaint_reference.alpha_composite(
            placement["image"], (placement["x"], placement["y"])
        )
    inpaint_reference.save(
        path.with_name("inpaint_reference.png"),
        format="PNG",
        optimize=True,
    )
    build_upper_context_mask(
        width,
        height,
        placements,
        manifest,
        reference_dir,
    )
    scope_data = load_poster_scope_data(bundle)
    (reference_dir / IDENTITY_LOCK_PROMPT_FILE).write_text(
        build_identity_lock_prompt(manifest, scope_data) + "\n",
        encoding="utf-8",
    )
    # FLUX.1 Canny uses the exact reviewed figures only as line geometry. A
    # white opaque canvas prevents the LoadImage alpha channel from turning the
    # entire background into an unintended inpaint mask or black image.
    structure_reference = Image.new(
        "RGBA", (width, height), (255, 255, 255, 255)
    )
    structure_reference.alpha_composite(inpaint_reference)
    structure_reference.convert("RGB").save(
        path.with_name("structure_reference.png"),
        format="PNG",
        optimize=True,
    )
    build_qwen_identity_references(
        scope_dir,
        placements,
        reference_dir,
    )

    build_identity_references(
        scope_dir,
        manifest,
        reference_dir,
        asset_key=bundle.asset_key,
    )
    # AnimaEdit is an image-edit model and strongly retains the source material.
    # Give it only an abstract sky/meadow material scaffold—not prior artwork or
    # layout geometry—so the transparent area is interpreted as landscape.
    anima_reference = Image.new("RGBA", (width, height), (184, 220, 235, 255))
    anima_identity_alpha = Image.new("L", (width, height), 0)
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
        anima_identity_alpha.paste(
            placement["image"].getchannel("A"),
            (placement["x"], placement["y"]),
            placement["image"].getchannel("A"),
        )
    anima_reference.save(
        path.with_name("anima_scene_reference.png"), format="PNG", optimize=True
    )
    # Preserve the recognizable interior exactly while leaving a narrow contour
    # available to the model for coherent occlusion, lighting, and ground contact.
    erosion = max(3, round(width / 220) | 1)
    identity_core = anima_identity_alpha.filter(ImageFilter.MinFilter(erosion))
    identity_core.convert("RGB").save(
        path.with_name("identity_core.png"), format="PNG", optimize=True
    )
    return path


def prepare(scope: str, megapixels: float = 1.0) -> Path:
    bundle = poster_bundle(scope, poster_assets=POSTER_ASSETS)
    scope_dir = bundle.asset_dir
    work_dir = scope_dir / "comfyui_poster"
    required = (
        scope_dir / "poster.yaml",
        scope_dir / "cutouts" / "manifest.json",
    )
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(path)

    cutout_manifest = json.loads(required[-1].read_text(encoding="utf-8"))
    cutout_files = [
        scope_dir / "cutouts" / item["file"]
        for item in cutout_manifest.get("items", [])
    ]
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
