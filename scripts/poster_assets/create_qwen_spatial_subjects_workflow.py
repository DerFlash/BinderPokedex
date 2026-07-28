#!/usr/bin/env python3
"""Create the isolated Qwen three-spatial-subject poster experiment."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

try:
    from .composition import (
        joint_scene_canvas_placements,
        normalized_visible_placement_contract,
        validate_visible_placements,
    )
    from .create_comfyui_poster_workflow import (
        megapixel_marker,
        node,
        output_dimensions,
    )
    from .create_qwen_edit_poster_workflow import (
        DEFAULT_CFG,
        DEFAULT_CLIP,
        DEFAULT_LORA,
        DEFAULT_MODEL,
        DEFAULT_SHIFT,
        DEFAULT_STEPS,
        DEFAULT_VAE,
    )
    from .poster_config import build_qwen_spatial_subject_prompt
    from .poster_io import (
        load_cutout_items,
        load_poster_scope_data,
        poster_asset_slug,
        poster_bundle,
    )
except ImportError:
    from composition import (
        joint_scene_canvas_placements,
        normalized_visible_placement_contract,
        validate_visible_placements,
    )
    from create_comfyui_poster_workflow import (
        megapixel_marker,
        node,
        output_dimensions,
    )
    from create_qwen_edit_poster_workflow import (
        DEFAULT_CFG,
        DEFAULT_CLIP,
        DEFAULT_LORA,
        DEFAULT_MODEL,
        DEFAULT_SHIFT,
        DEFAULT_STEPS,
        DEFAULT_VAE,
    )
    from poster_config import build_qwen_spatial_subject_prompt
    from poster_io import (
        load_cutout_items,
        load_poster_scope_data,
        poster_asset_slug,
        poster_bundle,
    )


ROOT = Path(__file__).resolve().parents[2]
POSTER_ASSETS = ROOT / "data" / "poster_assets"
REFERENCE_MEGAPIXELS = 1.0
REFERENCE_PREFIX = "qwen_spatial_subject_reference"
PROMPT_SNAPSHOT = "qwen_spatial_subjects_prompt.generated.txt"


def spatial_subject_placements(
    scope: str,
) -> tuple[tuple[int, int], list[dict[str, object]]]:
    """Return canonical 1-MP positions used by all Qwen preflight sizes."""
    bundle = poster_bundle(scope, poster_assets=POSTER_ASSETS)
    if len(load_cutout_items(bundle.asset_dir)) != 3:
        raise ValueError(
            "Qwen spatial-subject control requires exactly 3 subjects"
        )
    canvas_size = output_dimensions(scope, REFERENCE_MEGAPIXELS)
    placements = joint_scene_canvas_placements(
        bundle.asset_dir,
        layout_name=str(
            bundle.manifest.get("layout", {}).get(
                "name",
                "standard_3x3",
            )
        ),
        canvas_size=canvas_size,
    )
    validate_visible_placements(
        placements,
        canvas_size=canvas_size,
        description="Qwen spatial-subject",
    )
    return canvas_size, placements


def build_spatial_subject_references(
    scope: str,
    output_dir: Path,
) -> tuple[Path, Path, Path]:
    """Write three opaque poster canvases containing one subject each."""
    bundle = poster_bundle(scope, poster_assets=POSTER_ASSETS)
    neutral_values = (
        bundle.manifest.get("conditioning", {})
        .get("identity_defaults", {})
        .get("neutral_rgb", [226, 224, 211])
    )
    if (
        not isinstance(neutral_values, list)
        or len(neutral_values) != 3
        or not all(
            isinstance(value, int) and 0 <= value <= 255
            for value in neutral_values
        )
    ):
        raise ValueError(
            "conditioning.identity_defaults.neutral_rgb must contain "
            "3 RGB integers"
        )
    neutral = tuple(neutral_values)
    canvas_size, placements = spatial_subject_placements(scope)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for index, placement in enumerate(placements, start=1):
        reference = Image.new("RGBA", canvas_size, (*neutral, 255))
        reference.alpha_composite(
            placement["image"],
            (int(placement["x"]), int(placement["y"])),
        )
        path = output_dir / f"{REFERENCE_PREFIX}_{index}.png"
        reference.convert("RGB").save(path, format="PNG", optimize=True)
        paths.append(path)
    return paths[0], paths[1], paths[2]


def build_workflow(
    scope: str,
    seed: int,
    megapixels: float,
    *,
    unet_name: str = DEFAULT_MODEL,
    clip_name: str = DEFAULT_CLIP,
    vae_name: str = DEFAULT_VAE,
    lora_name: str = DEFAULT_LORA,
    steps: int = DEFAULT_STEPS,
    cfg: float = DEFAULT_CFG,
    shift: float = DEFAULT_SHIFT,
) -> dict[str, object]:
    """Build one empty-target Qwen pass with three unique spatial subjects."""
    if megapixels <= 0:
        raise ValueError("megapixels must be positive")
    if steps <= 0:
        raise ValueError("steps must be positive")
    if cfg <= 0:
        raise ValueError("cfg must be positive")
    if shift <= 0:
        raise ValueError("shift must be positive")

    bundle = poster_bundle(scope, poster_assets=POSTER_ASSETS)
    items = load_cutout_items(bundle.asset_dir)
    canvas_size, placements = spatial_subject_placements(scope)
    prompt = build_qwen_spatial_subject_prompt(
        bundle.manifest,
        load_poster_scope_data(bundle),
        items,
        placement_contract=normalized_visible_placement_contract(
            placements,
            canvas_size=canvas_size,
        ),
    )
    width, height = output_dimensions(scope, megapixels)

    return {
        "1": node("UnetLoaderGGUF", unet_name=unet_name),
        "2": node("ModelSamplingAuraFlow", model=["1", 0], shift=shift),
        "3": node("CFGNorm", model=["2", 0], strength=1.0),
        "4": node(
            "LoraLoaderModelOnly",
            model=["3", 0],
            lora_name=lora_name,
            strength_model=1.0,
        ),
        "5": node(
            "CLIPLoader",
            clip_name=clip_name,
            type="qwen_image",
            device="default",
        ),
        "6": node("VAELoader", vae_name=vae_name),
        "7": node(
            "LoadImage",
            image=f"{REFERENCE_PREFIX}_1.png",
        ),
        "8": node(
            "LoadImage",
            image=f"{REFERENCE_PREFIX}_2.png",
        ),
        "9": node(
            "LoadImage",
            image=f"{REFERENCE_PREFIX}_3.png",
        ),
        "10": node(
            "TextEncodeQwenImageEditPlus",
            clip=["5", 0],
            vae=["6", 0],
            image1=["7", 0],
            image2=["8", 0],
            image3=["9", 0],
            prompt=prompt,
        ),
        "11": node(
            "TextEncodeQwenImageEditPlus",
            clip=["5", 0],
            vae=["6", 0],
            image1=["7", 0],
            image2=["8", 0],
            image3=["9", 0],
            prompt="",
        ),
        "12": node(
            "FluxKontextMultiReferenceLatentMethod",
            conditioning=["10", 0],
            reference_latents_method="index_timestep_zero",
        ),
        "13": node(
            "FluxKontextMultiReferenceLatentMethod",
            conditioning=["11", 0],
            reference_latents_method="index_timestep_zero",
        ),
        "14": node(
            "EmptySD3LatentImage",
            width=width,
            height=height,
            batch_size=1,
        ),
        "15": node(
            "KSampler",
            model=["4", 0],
            positive=["12", 0],
            negative=["13", 0],
            latent_image=["14", 0],
            seed=seed,
            steps=steps,
            cfg=cfg,
            sampler_name="euler",
            scheduler="simple",
            denoise=1.0,
        ),
        "16": node(
            "VAEDecode",
            samples=["15", 0],
            vae=["6", 0],
        ),
        "17": node(
            "SaveImage",
            images=["16", 0],
            filename_prefix=(
                f"{poster_asset_slug(scope)}_qwen2511_spatial_subjects_"
                f"{megapixel_marker(megapixels)}_seed_{seed}"
            ),
        ),
    }


def write_experiment(
    scope: str,
    seed: int,
    megapixels: float,
    *,
    output_dir: Path | None = None,
    **workflow_options: object,
) -> Path:
    """Write the three references, prompt snapshot, and API workflow."""
    bundle = poster_bundle(scope, poster_assets=POSTER_ASSETS)
    work_dir = output_dir or bundle.asset_dir / "comfyui_poster"
    build_spatial_subject_references(scope, work_dir)
    workflow = build_workflow(
        scope,
        seed,
        megapixels,
        **workflow_options,
    )
    marker = megapixel_marker(megapixels)
    workflow_path = (
        work_dir
        / f"workflow_api_qwen_spatial_subjects_{marker}_{seed}.json"
    )
    workflow_path.write_text(
        json.dumps(workflow, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (work_dir / PROMPT_SNAPSHOT).write_text(
        "\n\n".join(
            (
                "QWEN 2511 - THREE UNIQUE SPATIAL SUBJECTS - EMPTY TARGET",
                str(workflow["10"]["inputs"]["prompt"]).strip(),
            )
        )
        + "\n",
        encoding="utf-8",
    )
    return workflow_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", default="Pokedex/sections/gen7")
    parser.add_argument("--seed", type=int, default=260726054)
    parser.add_argument("--megapixels", type=float, default=0.25)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--clip", default=DEFAULT_CLIP)
    parser.add_argument("--vae", default=DEFAULT_VAE)
    parser.add_argument("--lora", default=DEFAULT_LORA)
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    parser.add_argument("--cfg", type=float, default=DEFAULT_CFG)
    parser.add_argument("--shift", type=float, default=DEFAULT_SHIFT)
    args = parser.parse_args()
    print(
        write_experiment(
            args.scope,
            args.seed,
            args.megapixels,
            unet_name=args.model,
            clip_name=args.clip,
            vae_name=args.vae,
            lora_name=args.lora,
            steps=args.steps,
            cfg=args.cfg,
            shift=args.shift,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
