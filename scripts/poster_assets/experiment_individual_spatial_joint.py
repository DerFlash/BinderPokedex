#!/usr/bin/env python3
"""Backward-compatible entry point for the promoted reference topology."""
from __future__ import annotations

import argparse
from pathlib import Path

try:
    from .create_comfyui_poster_workflow import (
        build_individual_spatial_joint_workflow,
        build_individual_spatial_prompt,
        write_workflow,
    )
    from .generation_options import (
        DEFAULT_FLUX_ENCODER,
        DEFAULT_FLUX_MODEL,
        DEFAULT_FLUX_STEPS,
        DEFAULT_FLUX_VAE,
    )
    from .prepare_comfyui_poster import prepare
except ImportError:
    from create_comfyui_poster_workflow import (
        build_individual_spatial_joint_workflow,
        build_individual_spatial_prompt,
        write_workflow,
    )
    from generation_options import (
        DEFAULT_FLUX_ENCODER,
        DEFAULT_FLUX_MODEL,
        DEFAULT_FLUX_STEPS,
        DEFAULT_FLUX_VAE,
    )
    from prepare_comfyui_poster import prepare


REFERENCE_MODE = "individual_spatial_joint"


def build_workflow(
    scope: str,
    seed: int,
    megapixels: float,
    *,
    unet_name: str = DEFAULT_FLUX_MODEL,
    clip_name: str = DEFAULT_FLUX_ENCODER,
    vae_name: str = DEFAULT_FLUX_VAE,
    steps: int = DEFAULT_FLUX_STEPS,
) -> dict[str, object]:
    """Retain the former experiment API while using the production builder."""
    return build_individual_spatial_joint_workflow(
        scope,
        seed,
        megapixels,
        unet_name=unet_name,
        clip_name=clip_name,
        vae_name=vae_name,
        steps=steps,
    )


def prepare_experiment(
    scope: str,
    seed: int,
    megapixels: float,
    *,
    unet_name: str = DEFAULT_FLUX_MODEL,
    clip_name: str = DEFAULT_FLUX_ENCODER,
    vae_name: str = DEFAULT_FLUX_VAE,
    steps: int = DEFAULT_FLUX_STEPS,
) -> Path:
    """Prepare the production references and workflow under the legacy API."""
    work_dir = prepare(
        scope,
        megapixels,
        generation_mode="joint_scene",
        reference_mode=REFERENCE_MODE,
    )
    return write_workflow(
        scope,
        seed,
        megapixels,
        generation_mode="joint_scene",
        reference_mode=REFERENCE_MODE,
        unet_name=unet_name,
        clip_name=clip_name,
        vae_name=vae_name,
        steps=steps,
        output_dir=work_dir,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", default="Pokedex/sections/gen1")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--megapixels", type=float, default=0.25)
    parser.add_argument("--model", default=DEFAULT_FLUX_MODEL)
    parser.add_argument("--clip", default=DEFAULT_FLUX_ENCODER)
    parser.add_argument("--vae", default=DEFAULT_FLUX_VAE)
    parser.add_argument("--steps", type=int, default=DEFAULT_FLUX_STEPS)
    args = parser.parse_args()
    print(
        prepare_experiment(
            args.scope,
            args.seed,
            args.megapixels,
            unet_name=args.model,
            clip_name=args.clip,
            vae_name=args.vae,
            steps=args.steps,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
