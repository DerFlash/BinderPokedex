#!/usr/bin/env python3
"""Create a FLUX.1 Dev GGUF poster workflow with Canny structure control."""
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

DEFAULT_MODEL = "flux1-dev-Q4_K_S.gguf"
DEFAULT_CLIP = "clip_l.safetensors"
DEFAULT_T5 = "t5-v1_1-xxl-encoder-Q4_K_S.gguf"
DEFAULT_VAE = "ae.safetensors"
DEFAULT_CONTROLNET = "instantx_flux_canny.safetensors"
DEFAULT_STEPS = 20
DEFAULT_GUIDANCE = 3.5
DEFAULT_CONTROL_STRENGTH = 0.75
DEFAULT_CANNY_LOW = 0.2
DEFAULT_CANNY_HIGH = 0.3


def build_workflow(
    scope: str,
    seed: int,
    megapixels: float,
    *,
    unet_name: str = DEFAULT_MODEL,
    clip_name: str = DEFAULT_CLIP,
    t5_name: str = DEFAULT_T5,
    vae_name: str = DEFAULT_VAE,
    controlnet_name: str = DEFAULT_CONTROLNET,
    steps: int = DEFAULT_STEPS,
    guidance: float = DEFAULT_GUIDANCE,
    control_strength: float = DEFAULT_CONTROL_STRENGTH,
    canny_low: float = DEFAULT_CANNY_LOW,
    canny_high: float = DEFAULT_CANNY_HIGH,
) -> dict[str, object]:
    if steps <= 0:
        raise ValueError("steps must be positive")
    if guidance <= 0:
        raise ValueError("guidance must be positive")
    if control_strength <= 0:
        raise ValueError("control_strength must be positive")
    if not 0 <= canny_low < canny_high <= 1:
        raise ValueError("Canny thresholds must satisfy 0 <= low < high <= 1")

    work_dir = POSTER_ASSETS / scope / "comfyui_poster"
    prompt_path = work_dir / "flux1_canny_prompt.txt"
    prompt = prompt_path.read_text(encoding="utf-8").strip()
    if not prompt:
        raise ValueError(f"Prompt is empty: {prompt_path}")

    width, height = output_dimensions(scope, megapixels)
    return {
        "1": node("UnetLoaderGGUF", unet_name=unet_name),
        "2": node(
            "DualCLIPLoaderGGUF",
            clip_name1=clip_name,
            clip_name2=t5_name,
            type="flux",
        ),
        "3": node("VAELoader", vae_name=vae_name),
        "4": node("CLIPTextEncode", text=prompt, clip=["2", 0]),
        "5": node("CLIPTextEncode", text="", clip=["2", 0]),
        "6": node("FluxGuidance", conditioning=["4", 0], guidance=guidance),
        "7": node("LoadImage", image="structure_reference.png"),
        "8": node(
            "Canny",
            image=["7", 0],
            low_threshold=canny_low,
            high_threshold=canny_high,
        ),
        "9": node("ControlNetLoader", control_net_name=controlnet_name),
        "10": node(
            "ControlNetApplySD3",
            positive=["6", 0],
            negative=["5", 0],
            control_net=["9", 0],
            vae=["3", 0],
            image=["8", 0],
            strength=control_strength,
            start_percent=0.0,
            end_percent=1.0,
        ),
        "11": node(
            "EmptySD3LatentImage",
            width=width,
            height=height,
            batch_size=1,
        ),
        "12": node(
            "KSampler",
            model=["1", 0],
            positive=["10", 0],
            negative=["10", 1],
            latent_image=["11", 0],
            seed=seed,
            steps=steps,
            cfg=1.0,
            sampler_name="euler",
            scheduler="normal",
            denoise=1.0,
        ),
        "13": node("VAEDecode", samples=["12", 0], vae=["3", 0]),
        "14": node(
            "SaveImage",
            images=["13", 0],
            filename_prefix=(
                f"{poster_asset_slug(scope)}_flux1_canny_"
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
    output = destination / f"flux1_canny_workflow_api_{marker}_{seed}.json"
    output.write_text(
        json.dumps(workflow, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", default="Base1")
    parser.add_argument("--seed", type=int, default=260726201)
    parser.add_argument("--megapixels", type=float, default=1.0)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--clip", default=DEFAULT_CLIP)
    parser.add_argument("--t5", default=DEFAULT_T5)
    parser.add_argument("--vae", default=DEFAULT_VAE)
    parser.add_argument("--controlnet", default=DEFAULT_CONTROLNET)
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    parser.add_argument("--guidance", type=float, default=DEFAULT_GUIDANCE)
    parser.add_argument(
        "--control-strength",
        type=float,
        default=DEFAULT_CONTROL_STRENGTH,
    )
    args = parser.parse_args()
    print(
        write_workflow(
            args.scope,
            args.seed,
            args.megapixels,
            unet_name=args.model,
            clip_name=args.clip,
            t5_name=args.t5,
            vae_name=args.vae,
            controlnet_name=args.controlnet,
            steps=args.steps,
            guidance=args.guidance,
            control_strength=args.control_strength,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
