#!/usr/bin/env python3
"""Create the isolated SDXL regional identity-control experiment."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .create_comfyui_poster_workflow import (
        megapixel_marker,
        node,
        output_dimensions,
    )
    from .poster_config import build_sdxl_identity_control_prompt
    from .poster_io import (
        load_cutout_items,
        load_poster_scope_data,
        poster_asset_slug,
        poster_bundle,
    )
    from .prepare_comfyui_poster import build_sdxl_identity_references
except ImportError:
    from create_comfyui_poster_workflow import (
        megapixel_marker,
        node,
        output_dimensions,
    )
    from poster_config import build_sdxl_identity_control_prompt
    from poster_io import (
        load_cutout_items,
        load_poster_scope_data,
        poster_asset_slug,
        poster_bundle,
    )
    from prepare_comfyui_poster import build_sdxl_identity_references


ROOT = Path(__file__).resolve().parents[2]
POSTER_ASSETS = ROOT / "data" / "poster_assets"

DEFAULT_CHECKPOINT = "sd_xl_base_1.0.safetensors"
DEFAULT_CONTROLNET = "xinsir-controlnet-union-sdxl-1.0.safetensors"
DEFAULT_IPADAPTER_WEIGHT = 1.0
DEFAULT_CONTROLNET_STRENGTH = 0.72
NEGATIVE_PROMPT = (
    "text, letters, numbers, logo, watermark, UI, panel, plaque, frame, "
    "border, crop marks, guide lines, visible masks, visible control lines, "
    "extra character, duplicate character, merged characters, human, trainer, "
    "statue, creature-shaped scenery, redesigned anatomy, changed markings, "
    "missing limb, extra limb, malformed face, cropped character, character "
    "outside its assigned bottom card, flat sticker, pasted cutout, isolated "
    "halo, landing pad, inconsistent shadow, broken occlusion, plant ending "
    "at a character silhouette"
)


def build_workflow(
    scope: str,
    seed: int,
    megapixels: float,
    *,
    checkpoint_name: str = DEFAULT_CHECKPOINT,
    controlnet_name: str = DEFAULT_CONTROLNET,
    steps: int = 30,
    cfg: float = 6.0,
    ipadapter_weight: float = DEFAULT_IPADAPTER_WEIGHT,
    controlnet_strength: float = DEFAULT_CONTROLNET_STRENGTH,
    pokemon_lora_name: str | None = None,
    pokemon_lora_strength: float = 0.30,
) -> dict[str, object]:
    """Build one empty-target sampler with regional identity and structure."""
    if steps <= 0:
        raise ValueError("steps must be positive")
    if cfg <= 0:
        raise ValueError("cfg must be positive")
    if not 0 < ipadapter_weight <= 3:
        raise ValueError("ipadapter_weight must be in the range (0, 3]")
    if not 0 < controlnet_strength <= 10:
        raise ValueError("controlnet_strength must be in the range (0, 10]")
    if pokemon_lora_name is not None and not pokemon_lora_name.strip():
        raise ValueError("pokemon_lora_name must be non-empty when supplied")

    bundle = poster_bundle(scope, poster_assets=POSTER_ASSETS)
    manifest = bundle.manifest
    items = load_cutout_items(bundle.asset_dir)
    if len(items) not in {3, 4}:
        raise ValueError("SDXL regional identity control supports 3-4 subjects")
    width, height = output_dimensions(scope, megapixels)
    positive_prompt = build_sdxl_identity_control_prompt(
        manifest,
        load_poster_scope_data(bundle),
        items,
    )
    variant = "pokemon" if pokemon_lora_name else "generic"

    workflow = {
        "1": node("CheckpointLoaderSimple", ckpt_name=checkpoint_name),
        "4": node("CLIPTextEncode", text=positive_prompt, clip=["1", 1]),
        "5": node("CLIPTextEncode", text=NEGATIVE_PROMPT, clip=["1", 1]),
    }
    model_source: list[object] = ["1", 0]
    if pokemon_lora_name is not None:
        workflow["2"] = node(
            "LoraLoaderModelOnly",
            model=model_source,
            lora_name=pokemon_lora_name,
            strength_model=pokemon_lora_strength,
        )
        model_source = ["2", 0]

    workflow["3"] = node(
        "IPAdapterUnifiedLoader",
        model=model_source,
        preset="PLUS (high strength)",
    )

    regional_params: list[list[object]] = []
    for index in range(1, len(items) + 1):
        load_image_id = str(10 + (index - 1) * 4)
        load_mask_id = str(11 + (index - 1) * 4)
        image_to_mask_id = str(12 + (index - 1) * 4)
        regional_id = str(13 + (index - 1) * 4)
        workflow[load_image_id] = node(
            "LoadImage",
            image=f"identity_reference_{index}.png",
        )
        workflow[load_mask_id] = node(
            "LoadImage",
            image=f"sdxl_identity_region_{index}.png",
        )
        workflow[image_to_mask_id] = node(
            "ImageToMask",
            image=[load_mask_id, 0],
            channel="red",
        )
        workflow[regional_id] = node(
            "IPAdapterRegionalConditioning",
            image=[load_image_id, 0],
            image_weight=ipadapter_weight,
            prompt_weight=1.0,
            weight_type="linear",
            start_at=0.0,
            end_at=0.90,
            mask=[image_to_mask_id, 0],
        )
        regional_params.append([regional_id, 0])

    if len(regional_params) == 1:
        combined_params = regional_params[0]
    else:
        combine_inputs = {
            f"params_{index}": value
            for index, value in enumerate(regional_params, start=1)
        }
        workflow["30"] = node("IPAdapterCombineParams", **combine_inputs)
        combined_params = ["30", 0]

    workflow.update(
        {
            "31": node(
                "IPAdapterFromParams",
                model=["3", 0],
                ipadapter=["3", 1],
                ipadapter_params=combined_params,
                combine_embeds="concat",
                embeds_scaling="K+V w/ C penalty",
            ),
            "40": node(
                "LoadImage",
                image="sdxl_identity_structure.png",
            ),
            "41": node(
                "Canny",
                image=["40", 0],
                low_threshold=0.20,
                high_threshold=0.55,
            ),
            "42": node(
                "ControlNetLoader",
                control_net_name=controlnet_name,
            ),
            "43": node(
                "SetUnionControlNetType",
                control_net=["42", 0],
                type="canny/lineart/anime_lineart/mlsd",
            ),
            "44": node(
                "ControlNetApplyAdvanced",
                positive=["4", 0],
                negative=["5", 0],
                control_net=["43", 0],
                image=["41", 0],
                strength=controlnet_strength,
                start_percent=0.0,
                end_percent=0.82,
            ),
            "50": node(
                "EmptyLatentImage",
                width=width,
                height=height,
                batch_size=1,
            ),
            "51": node(
                "KSampler",
                model=["31", 0],
                seed=seed,
                steps=steps,
                cfg=cfg,
                sampler_name="dpmpp_2m",
                scheduler="karras",
                positive=["44", 0],
                negative=["44", 1],
                latent_image=["50", 0],
                denoise=1.0,
            ),
            "52": node(
                "VAEDecode",
                samples=["51", 0],
                vae=["1", 2],
            ),
            "53": node(
                "SaveImage",
                images=["52", 0],
                filename_prefix=(
                    f"{poster_asset_slug(scope)}_sdxl_identity_{variant}_"
                    f"{megapixel_marker(megapixels)}_seed_{seed}"
                ),
            ),
        }
    )
    return workflow


def write_experiment(
    scope: str,
    seed: int,
    megapixels: float,
    *,
    output_dir: Path | None = None,
    pokemon_lora_name: str | None = None,
    **workflow_options: object,
) -> Path:
    """Prepare deterministic references and write one API workflow snapshot."""
    bundle = poster_bundle(scope, poster_assets=POSTER_ASSETS)
    work_dir = output_dir or bundle.asset_dir / "comfyui_poster"
    work_dir.mkdir(parents=True, exist_ok=True)
    build_sdxl_identity_references(
        scope,
        work_dir,
        megapixels=megapixels,
    )
    workflow = build_workflow(
        scope,
        seed,
        megapixels,
        pokemon_lora_name=pokemon_lora_name,
        **workflow_options,
    )
    marker = megapixel_marker(megapixels)
    workflow_path = (
        work_dir
        / f"workflow_api_sdxl_identity_{variant}_{marker}_{seed}.json"
    )
    workflow_path.write_text(
        json.dumps(workflow, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    prompt_path = (
        work_dir
        / f"sdxl_identity_{variant}_prompt.generated.txt"
    )
    prompt_path.write_text(
        "\n\n".join(
            (
                "SDXL REGIONAL IDENTITY CONTROL - EMPTY TARGET",
                str(workflow["4"]["inputs"]["text"]).strip(),
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
    parser.add_argument("--megapixels", type=float, default=1.0)
    parser.add_argument("--checkpoint", default=DEFAULT_CHECKPOINT)
    parser.add_argument("--controlnet", default=DEFAULT_CONTROLNET)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--cfg", type=float, default=6.0)
    parser.add_argument("--ipadapter-weight", type=float, default=1.0)
    parser.add_argument("--controlnet-strength", type=float, default=0.72)
    parser.add_argument("--pokemon-lora")
    parser.add_argument("--pokemon-lora-strength", type=float, default=0.30)
    args = parser.parse_args()
    path = write_experiment(
        args.scope,
        args.seed,
        args.megapixels,
        checkpoint_name=args.checkpoint,
        controlnet_name=args.controlnet,
        steps=args.steps,
        cfg=args.cfg,
        ipadapter_weight=args.ipadapter_weight,
        controlnet_strength=args.controlnet_strength,
        pokemon_lora_name=args.pokemon_lora,
        pokemon_lora_strength=args.pokemon_lora_strength,
    )
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
