#!/usr/bin/env python3
"""Create the isolated DreamO v1.1 three-subject identity experiment."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .composition import (
        joint_scene_canvas_placements,
        normalized_visible_placement_contract,
    )
    from .create_comfyui_poster_workflow import (
        megapixel_marker,
        node,
        output_dimensions,
    )
    from .poster_config import build_dreamo_identity_prompt
    from .poster_io import (
        load_cutout_items,
        load_poster_scope_data,
        poster_asset_slug,
        poster_bundle,
    )
    from .prepare_comfyui_poster import build_dreamo_identity_references
except ImportError:
    from composition import (
        joint_scene_canvas_placements,
        normalized_visible_placement_contract,
    )
    from create_comfyui_poster_workflow import (
        megapixel_marker,
        node,
        output_dimensions,
    )
    from poster_config import build_dreamo_identity_prompt
    from poster_io import (
        load_cutout_items,
        load_poster_scope_data,
        poster_asset_slug,
        poster_bundle,
    )
    from prepare_comfyui_poster import build_dreamo_identity_references


ROOT = Path(__file__).resolve().parents[2]
POSTER_ASSETS = ROOT / "data" / "poster_assets"

DEFAULT_UNET = "flux1-dev-Q4_K_S.gguf"
DEFAULT_CLIP = "clip_l.safetensors"
DEFAULT_T5 = "t5-v1_1-xxl-encoder-Q4_K_S.gguf"
DEFAULT_VAE = "ae.safetensors"
DEFAULT_STEPS = 12
DEFAULT_GUIDANCE = 4.5
DEFAULT_REFERENCE_RESOLUTION = 512
LORA_CHAIN = (
    ("flux-turbo.safetensors", 1.0),
    ("dreamo_comfyui.safetensors", 1.0),
    ("dreamo_cfg_distill_comfyui.safetensors", 1.0),
    ("dreamo_sft_lora.safetensors", 1.0),
    ("dreamo_dpo_lora.safetensors", 1.2),
)


def build_workflow(
    scope: str,
    seed: int,
    megapixels: float,
    *,
    unet_name: str = DEFAULT_UNET,
    clip_name: str = DEFAULT_CLIP,
    t5_name: str = DEFAULT_T5,
    vae_name: str = DEFAULT_VAE,
    steps: int = DEFAULT_STEPS,
    guidance: float = DEFAULT_GUIDANCE,
    reference_resolution: int = DEFAULT_REFERENCE_RESOLUTION,
) -> dict[str, object]:
    """Build one empty-target DreamO pass with three identity references."""
    if steps <= 0:
        raise ValueError("steps must be positive")
    if guidance <= 0:
        raise ValueError("guidance must be positive")
    if not 512 <= reference_resolution <= 1024:
        raise ValueError(
            "reference_resolution must be between 512 and 1024"
        )
    if reference_resolution % 16:
        raise ValueError("reference_resolution must be divisible by 16")

    bundle = poster_bundle(scope, poster_assets=POSTER_ASSETS)
    items = load_cutout_items(bundle.asset_dir)
    if len(items) != 3:
        raise ValueError(
            "The pinned DreamO node supports exactly 3 subject references"
        )
    width, height = output_dimensions(scope, megapixels)
    placements = joint_scene_canvas_placements(
        bundle.asset_dir,
        layout_name=bundle.manifest.get("layout", {}).get(
            "name",
            "standard_3x3",
        ),
        canvas_size=(width, height),
    )
    prompt = build_dreamo_identity_prompt(
        bundle.manifest,
        load_poster_scope_data(bundle),
        items,
        placement_contract=normalized_visible_placement_contract(
            placements,
            canvas_size=(width, height),
        ),
    )

    workflow: dict[str, object] = {
        "1": node("UnetLoaderGGUF", unet_name=unet_name),
        "7": node(
            "DualCLIPLoaderGGUF",
            clip_name1=clip_name,
            clip_name2=t5_name,
            type="flux",
        ),
        "8": node("VAELoader", vae_name=vae_name),
        "9": node("CLIPTextEncode", text=prompt, clip=["7", 0]),
        "10": node("CLIPTextEncode", text="", clip=["7", 0]),
        "11": node(
            "FluxGuidance",
            conditioning=["9", 0],
            guidance=guidance,
        ),
        "12": node("DreamOProcessorLoader"),
    }

    model_source: list[object] = ["1", 0]
    for node_id, (lora_name, strength) in zip(
        ("2", "3", "4", "5", "6"),
        LORA_CHAIN,
        strict=True,
    ):
        workflow[node_id] = node(
            "LoraLoaderModelOnly",
            model=model_source,
            lora_name=lora_name,
            strength_model=strength,
        )
        model_source = [node_id, 0]

    encoded_references = []
    for index, (load_id, encode_id) in enumerate(
        (("20", "21"), ("22", "23"), ("24", "25")),
        start=1,
    ):
        workflow[load_id] = node(
            "LoadImage",
            image=f"dreamo_identity_reference_{index}.png",
        )
        workflow[encode_id] = node(
            "DreamORefEncode",
            pixels=[load_id, 0],
            vae=["8", 0],
            dreamo_processor=["12", 0],
            resolution=reference_resolution,
            ref_task="ip",
        )
        encoded_references.append([encode_id, 0])

    workflow.update(
        {
            "26": node(
                "ApplyDreamO",
                model=model_source,
                ref1=encoded_references[0],
                ref2=encoded_references[1],
                ref3=encoded_references[2],
            ),
            "27": node(
                "EmptySD3LatentImage",
                width=width,
                height=height,
                batch_size=1,
            ),
            "28": node(
                "KSampler",
                model=["26", 0],
                seed=seed,
                steps=steps,
                cfg=1.0,
                sampler_name="euler",
                scheduler="simple",
                positive=["11", 0],
                negative=["10", 0],
                latent_image=["27", 0],
                denoise=1.0,
            ),
            "29": node(
                "VAEDecode",
                samples=["28", 0],
                vae=["8", 0],
            ),
            "30": node(
                "SaveImage",
                images=["29", 0],
                filename_prefix=(
                    f"{poster_asset_slug(scope)}_dreamo_v1_1_"
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
    **workflow_options: object,
) -> Path:
    """Write unscaled RGB subject references and one auditable API graph."""
    bundle = poster_bundle(scope, poster_assets=POSTER_ASSETS)
    work_dir = output_dir or bundle.asset_dir / "comfyui_poster"
    work_dir.mkdir(parents=True, exist_ok=True)
    build_dreamo_identity_references(scope, work_dir)
    workflow = build_workflow(
        scope,
        seed,
        megapixels,
        **workflow_options,
    )
    marker = megapixel_marker(megapixels)
    workflow_path = (
        work_dir
        / f"workflow_api_dreamo_v1_1_{marker}_{seed}.json"
    )
    workflow_path.write_text(
        json.dumps(workflow, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    prompt_path = work_dir / "dreamo_v1_1_prompt.generated.txt"
    prompt_path.write_text(
        "\n\n".join(
            (
                "DREAMO V1.1 THREE-REFERENCE IDENTITY - EMPTY TARGET",
                str(workflow["9"]["inputs"]["text"]).strip(),
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
    parser.add_argument("--unet", default=DEFAULT_UNET)
    parser.add_argument("--clip", default=DEFAULT_CLIP)
    parser.add_argument("--t5", default=DEFAULT_T5)
    parser.add_argument("--vae", default=DEFAULT_VAE)
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    parser.add_argument("--guidance", type=float, default=DEFAULT_GUIDANCE)
    parser.add_argument(
        "--reference-resolution",
        type=int,
        default=DEFAULT_REFERENCE_RESOLUTION,
    )
    args = parser.parse_args()
    print(
        write_experiment(
            args.scope,
            args.seed,
            args.megapixels,
            unet_name=args.unet,
            clip_name=args.clip,
            t5_name=args.t5,
            vae_name=args.vae,
            steps=args.steps,
            guidance=args.guidance,
            reference_resolution=args.reference_resolution,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
