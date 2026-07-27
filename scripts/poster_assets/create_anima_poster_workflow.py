#!/usr/bin/env python3
"""Create the experimental Anima reference-editing poster workflow."""
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
    from .poster_io import poster_asset_slug
except ImportError:
    from create_comfyui_poster_workflow import (
        megapixel_marker,
        node,
        output_dimensions,
    )
    from poster_io import poster_asset_slug


ROOT = Path(__file__).resolve().parents[2]
POSTER_ASSETS = ROOT / "data" / "poster_assets"

DEFAULT_MODEL = "AnimaYume_tuned_v05.safetensors"
DEFAULT_LORA = "AnimaEditV1.safetensors"
DEFAULT_ENCODER = "qwen_3_06b_base.safetensors"
DEFAULT_VAE = "qwen_image_vae.safetensors"
DEFAULT_STEPS = 22
DEFAULT_CFG = 3.4
DEFAULT_REFERENCE_STRENGTH = 1.0
DEFAULT_CONTROL_METHOD = "edit_lora"
DEFAULT_GENERATION_MODE = "generate"


def _validate_model_artifact(name: str, option: str) -> None:
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"{option} must not be empty")


def build_workflow(
    scope: str,
    seed: int,
    megapixels: float,
    *,
    reference_strength: float = DEFAULT_REFERENCE_STRENGTH,
    control_method: str = DEFAULT_CONTROL_METHOD,
    model_name: str = DEFAULT_MODEL,
    lora_name: str = DEFAULT_LORA,
    encoder_name: str = DEFAULT_ENCODER,
    vae_name: str = DEFAULT_VAE,
    steps: int = DEFAULT_STEPS,
    cfg: float = DEFAULT_CFG,
    generation_mode: str = DEFAULT_GENERATION_MODE,
) -> dict[str, object]:
    if control_method != DEFAULT_CONTROL_METHOD:
        raise ValueError(f"Unsupported Anima control method: {control_method}")
    if generation_mode not in {"generate", "edit"}:
        raise ValueError(f"Unsupported Anima generation mode: {generation_mode}")
    if reference_strength <= 0:
        raise ValueError("reference_strength must be positive")
    if steps <= 0:
        raise ValueError("steps must be positive")
    if cfg <= 0:
        raise ValueError("cfg must be positive")
    _validate_model_artifact(model_name, "model_name")
    _validate_model_artifact(lora_name, "lora_name")
    _validate_model_artifact(encoder_name, "encoder_name")
    _validate_model_artifact(vae_name, "vae_name")

    work_dir = POSTER_ASSETS / scope / "comfyui_poster"
    prompt_path = work_dir / "anima_prompt.txt"
    prompt = prompt_path.read_text(encoding="utf-8").strip()
    if not prompt:
        raise ValueError(f"Prompt is empty: {prompt_path}")
    width, height = output_dimensions(scope, megapixels)
    # Both modes use the exact-position Anima scaffold so its identity-core
    # mask and source pixels share one coordinate system. ``generate`` still
    # differs by sampling from the empty target latent below.
    reference_image = "anima_scene_reference.png"
    target_latent = ["10", 0] if generation_mode == "generate" else ["8", 0]
    negative = (
        "worst quality, low quality, blurry, jpeg artifacts, bad anatomy, "
        "extra limbs, extra ears, duplicate character, additional character, "
        "human, trainer, text, logo, watermark, frame, border, landing pad, path"
    )
    return {
        "1": node("UNETLoader", unet_name=model_name, weight_dtype="default"),
        "2": node(
            "LoraLoaderModelOnly",
            model=["1", 0],
            lora_name=lora_name,
            strength_model=reference_strength,
        ),
        "3": node(
            "CLIPLoader",
            clip_name=encoder_name,
            type="cosmos",
            device="default",
        ),
        "4": node("VAELoader", vae_name=vae_name),
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
            steps=steps,
            cfg=cfg,
            sampler_name="er_sde",
            scheduler="simple",
            denoise=1.0,
        ),
        "12": node("VAEDecode", samples=["11", 0], vae=["4", 0]),
        "13": node("SaveImage", images=["15", 0], filename_prefix=f"{poster_asset_slug(scope)}_anima_{generation_mode}_{reference_strength:.2f}_seed_{seed}"),
        "14": node("LoadImageMask", image="identity_core.png", channel="red"),
        "15": node("ImageCompositeMasked", destination=["12", 0], source=["7", 0], x=0, y=0, resize_source=False, mask=["14", 0]),
    }


def write_workflow(
    scope: str,
    seed: int,
    megapixels: float,
    reference_strength: float = DEFAULT_REFERENCE_STRENGTH,
    control_method: str = DEFAULT_CONTROL_METHOD,
    model_name: str = DEFAULT_MODEL,
    generation_mode: str = DEFAULT_GENERATION_MODE,
    output_dir: Path | None = None,
    *,
    lora_name: str = DEFAULT_LORA,
    encoder_name: str = DEFAULT_ENCODER,
    vae_name: str = DEFAULT_VAE,
    steps: int = DEFAULT_STEPS,
    cfg: float = DEFAULT_CFG,
) -> Path:
    work_dir = POSTER_ASSETS / scope / "comfyui_poster"
    target_dir = output_dir or work_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    out = target_dir / (
        "anima_workflow_api_"
        f"{generation_mode}_{megapixel_marker(megapixels)}_{seed}.json"
    )
    out.write_text(
        json.dumps(
            build_workflow(
                scope,
                seed,
                megapixels,
                reference_strength=reference_strength,
                control_method=control_method,
                model_name=model_name,
                lora_name=lora_name,
                encoder_name=encoder_name,
                vae_name=vae_name,
                steps=steps,
                cfg=cfg,
                generation_mode=generation_mode,
            ),
            indent=2,
            ensure_ascii=False,
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
    parser.add_argument(
        "--reference-strength",
        type=float,
        default=DEFAULT_REFERENCE_STRENGTH,
    )
    parser.add_argument(
        "--control-method",
        choices=(DEFAULT_CONTROL_METHOD,),
        default=DEFAULT_CONTROL_METHOD,
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--lora", default=DEFAULT_LORA)
    parser.add_argument("--encoder", default=DEFAULT_ENCODER)
    parser.add_argument("--vae", default=DEFAULT_VAE)
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    parser.add_argument("--cfg", type=float, default=DEFAULT_CFG)
    parser.add_argument(
        "--mode",
        choices=("generate", "edit"),
        default=DEFAULT_GENERATION_MODE,
    )
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
            lora_name=args.lora,
            encoder_name=args.encoder,
            vae_name=args.vae,
            steps=args.steps,
            cfg=args.cfg,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
