#!/usr/bin/env python3
"""Create the experimental Anima reference-editing poster workflow."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .create_comfyui_poster_workflow import node, output_dimensions
except ImportError:
    from create_comfyui_poster_workflow import node, output_dimensions


ROOT = Path(__file__).resolve().parents[2]
POSTER_ASSETS = ROOT / "data" / "poster_assets"


def build_workflow(
    scope: str,
    seed: int,
    megapixels: float,
    *,
    reference_strength: float = 1.0,
    control_method: str = "edit_lora",
    model_name: str = "AnimaYume_tuned_v05.safetensors",
    generation_mode: str = "generate",
) -> dict[str, object]:
    work_dir = POSTER_ASSETS / scope / "comfyui_poster"
    prompt = (work_dir / "anima_prompt.txt").read_text(encoding="utf-8").strip()
    width, height = output_dimensions(scope, megapixels)
    reference_image = (
        "scene_reference.png"
        if generation_mode == "generate"
        else "anima_scene_reference.png"
    )
    target_latent = ["10", 0] if generation_mode == "generate" else ["8", 0]
    negative = (
        "worst quality, low quality, blurry, jpeg artifacts, bad anatomy, "
        "extra limbs, extra ears, duplicate character, additional character, "
        "human, trainer, text, logo, watermark, frame, border, landing pad, path"
    )
    return {
        "1": node("UNETLoader", unet_name=model_name, weight_dtype="default"),
        "2": node("LoraLoaderModelOnly", model=["1", 0], lora_name="AnimaEditV1.safetensors", strength_model=reference_strength),
        "3": node("CLIPLoader", clip_name="qwen_3_06b_base.safetensors", type="cosmos", device="default"),
        "4": node("VAELoader", vae_name="qwen_image_vae.safetensors"),
        "5": node("CLIPTextEncode", text=prompt, clip=["3", 0]),
        "6": node("CLIPTextEncode", text=negative, clip=["3", 0]),
        "7": node("LoadImage", image=reference_image),
        "8": node("VAEEncode", pixels=["7", 0], vae=["4", 0]),
        "9": node("ApplyCosmosReferenceLatent", model=["2", 0], latent=["8", 0]),
        "10": node("EmptyLatentImage", width=width, height=height, batch_size=1),
        "11": node(
            "KSampler",
            model=["9", 0],
            positive=["5", 0],
            negative=["6", 0],
            latent_image=target_latent,
            seed=seed,
            steps=22,
            cfg=3.4,
            sampler_name="er_sde",
            scheduler="simple",
            denoise=1.0,
        ),
        "12": node("VAEDecode", samples=["11", 0], vae=["4", 0]),
        "13": node("SaveImage", images=["15", 0], filename_prefix=f"{scope.lower()}_anima_{generation_mode}_{reference_strength:.2f}_seed_{seed}"),
        "14": node("LoadImageMask", image="identity_core.png", channel="red"),
        "15": node("ImageCompositeMasked", destination=["12", 0], source=["7", 0], x=0, y=0, resize_source=False, mask=["14", 0]),
    }


def write_workflow(
    scope: str,
    seed: int,
    megapixels: float,
    reference_strength: float = 1.0,
    control_method: str = "edit_lora",
    model_name: str = "AnimaYume_tuned_v05.safetensors",
    generation_mode: str = "generate",
) -> Path:
    work_dir = POSTER_ASSETS / scope / "comfyui_poster"
    out = work_dir / "anima_workflow_api.json"
    out.write_text(
        json.dumps(
            build_workflow(
                scope,
                seed,
                megapixels,
                reference_strength=reference_strength,
                control_method=control_method,
                model_name=model_name,
                generation_mode=generation_mode,
            ),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", default="Base1")
    parser.add_argument("--seed", type=int, default=260716201)
    parser.add_argument("--megapixels", type=float, default=0.25)
    parser.add_argument("--reference-strength", type=float, default=1.0)
    parser.add_argument("--control-method", choices=("edit_lora",), default="edit_lora")
    parser.add_argument("--model", default="AnimaYume_tuned_v05.safetensors")
    parser.add_argument("--mode", choices=("generate", "edit"), default="generate")
    args = parser.parse_args()
    print(
        write_workflow(
            args.scope,
            args.seed,
            args.megapixels,
            args.reference_strength,
            args.control_method,
            args.model,
            args.mode,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
