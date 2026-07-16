#!/usr/bin/env python3
"""Create the reference-guided one-shot ComfyUI poster workflow."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

try:
    from .layout import build_page_layout
    from .render_poster import load_yaml
except ImportError:
    from layout import build_page_layout
    from render_poster import load_yaml


ROOT = Path(__file__).resolve().parents[2]
POSTER_ASSETS = ROOT / "data" / "poster_assets"


def node(class_type: str, **inputs: object) -> dict[str, object]:
    return {"class_type": class_type, "inputs": inputs}


def output_dimensions(scope: str, megapixels: float) -> tuple[int, int]:
    if megapixels <= 0:
        raise ValueError("megapixels must be positive")
    scope_dir = POSTER_ASSETS / scope
    manifest = load_yaml(scope_dir / "poster.yaml")
    layout = build_page_layout(manifest.get("layout", {}).get("name", "standard_3x3"))
    ratio = layout.width_px / layout.height_px
    height = math.sqrt(megapixels * 1_000_000 / ratio)
    width = height * ratio
    return max(16, round(width / 16) * 16), max(16, round(height / 16) * 16)


def build_workflow(
    scope: str,
    seed: int,
    megapixels: float,
    *,
    unet_name: str = "flux-2-klein-4b-fp8.safetensors",
    clip_name: str = "qwen_3_4b.safetensors",
    vae_name: str = "flux2-vae.safetensors",
) -> dict[str, object]:
    work_dir = POSTER_ASSETS / scope / "comfyui_poster"
    prompt = (work_dir / "prompt.txt").read_text(encoding="utf-8").strip()
    if not prompt:
        raise ValueError(f"Prompt is empty: {work_dir / 'prompt.txt'}")
    width, height = output_dimensions(scope, megapixels)
    return {
        "1": node("UNETLoader", unet_name=unet_name, weight_dtype="default"),
        "2": node("CLIPLoader", clip_name=clip_name, type="flux2", device="default"),
        "3": node("VAELoader", vae_name=vae_name),
        "4": node("CLIPTextEncode", text=prompt, clip=["2", 0]),
        "5": node("ConditioningZeroOut", conditioning=["4", 0]),
        "7": node("Flux2Scheduler", steps=4, width=width, height=height),
        "8": node("RandomNoise", noise_seed=seed),
        "9": node("CFGGuider", model=["1", 0], positive=["17", 0], negative=["5", 0], cfg=1.0),
        "10": node("KSamplerSelect", sampler_name="euler"),
        "11": node("SamplerCustomAdvanced", noise=["8", 0], guider=["9", 0], sampler=["10", 0], sigmas=["7", 0], latent_image=["15", 0]),
        "12": node("VAEDecode", samples=["11", 0], vae=["3", 0]),
        "13": node("SaveImage", images=["20", 0], filename_prefix=f"{scope.lower()}_flux2_scene_seed_{seed}"),
        "14": node("LoadImage", image="scene_reference.png"),
        "15": node("VAEEncodeForInpaint", pixels=["14", 0], vae=["3", 0], mask=["14", 1], grow_mask_by=8),
        "17": node("ReferenceLatent", conditioning=["4", 0], latent=["15", 0]),
        "18": node("LoadImageMask", image="identity_core.png", channel="red"),
        "20": node("ImageCompositeMasked", destination=["12", 0], source=["14", 0], x=0, y=0, resize_source=False, mask=["18", 0]),
    }


def write_workflow(scope: str, seed: int, megapixels: float) -> Path:
    work_dir = POSTER_ASSETS / scope / "comfyui_poster"
    work_dir.mkdir(parents=True, exist_ok=True)
    out_path = work_dir / "workflow_api.json"
    out_path.write_text(json.dumps(build_workflow(scope, seed, megapixels), indent=2) + "\n", encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", default="Base1")
    parser.add_argument("--seed", type=int, default=260715201)
    parser.add_argument("--megapixels", type=float, default=1.0)
    args = parser.parse_args()
    print(write_workflow(args.scope, args.seed, args.megapixels))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
