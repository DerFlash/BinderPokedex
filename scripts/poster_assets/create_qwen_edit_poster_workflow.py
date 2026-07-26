#!/usr/bin/env python3
"""Create a Qwen-Image-Edit-2511 multi-reference poster workflow."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .create_comfyui_poster_workflow import megapixel_marker, node
except ImportError:
    from create_comfyui_poster_workflow import megapixel_marker, node


ROOT = Path(__file__).resolve().parents[2]
POSTER_ASSETS = ROOT / "data" / "poster_assets"

DEFAULT_MODEL = "qwen-image-edit-2511-Q3_K_M.gguf"
DEFAULT_CLIP = "qwen_2.5_vl_7b_fp8_scaled.safetensors"
DEFAULT_VAE = "qwen_image_vae.safetensors"
DEFAULT_LORA = "Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors"
DEFAULT_STEPS = 4
DEFAULT_CFG = 1.0
DEFAULT_SHIFT = 3.1


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
    if megapixels <= 0:
        raise ValueError("megapixels must be positive")
    if steps <= 0:
        raise ValueError("steps must be positive")
    if cfg <= 0:
        raise ValueError("cfg must be positive")
    if shift <= 0:
        raise ValueError("shift must be positive")

    work_dir = POSTER_ASSETS / scope / "comfyui_poster"
    prompt_path = work_dir / "qwen_edit_prompt.txt"
    prompt = prompt_path.read_text(encoding="utf-8").strip()
    if not prompt:
        raise ValueError(f"Prompt is empty: {prompt_path}")

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
        "7": node("LoadImage", image="structure_reference.png"),
        "8": node("LoadImage", image="qwen_identity_reference_1.png"),
        "9": node("LoadImage", image="qwen_identity_reference_2.png"),
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
        "14": node("VAEEncode", pixels=["7", 0], vae=["6", 0]),
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
        "16": node("VAEDecode", samples=["15", 0], vae=["6", 0]),
        "17": node(
            "SaveImage",
            images=["16", 0],
            filename_prefix=(
                f"{scope.lower()}_qwen2511_edit_"
                f"{megapixel_marker(megapixels)}_scene_seed_{seed}"
            ),
        ),
    }


def write_workflow(
    scope: str,
    seed: int,
    megapixels: float,
    *,
    output_dir: Path | None = None,
    **workflow_options: object,
) -> Path:
    workflow = build_workflow(
        scope,
        seed,
        megapixels,
        **workflow_options,
    )
    marker = megapixel_marker(megapixels).replace("mp", "")
    destination = output_dir or POSTER_ASSETS / scope / "comfyui_poster"
    destination.mkdir(parents=True, exist_ok=True)
    output = destination / f"qwen_edit_workflow_api_{marker}_{seed}.json"
    output.write_text(
        json.dumps(workflow, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", default="Base1")
    parser.add_argument("--seed", type=int, default=260726301)
    parser.add_argument("--megapixels", type=float, default=1.0)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--clip", default=DEFAULT_CLIP)
    parser.add_argument("--vae", default=DEFAULT_VAE)
    parser.add_argument("--lora", default=DEFAULT_LORA)
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    parser.add_argument("--cfg", type=float, default=DEFAULT_CFG)
    parser.add_argument("--shift", type=float, default=DEFAULT_SHIFT)
    args = parser.parse_args()
    print(
        write_workflow(
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
