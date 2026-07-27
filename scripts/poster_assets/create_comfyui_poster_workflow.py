#!/usr/bin/env python3
"""Create one of the supported FLUX.2 poster workflows."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .layout import latent_canvas_dimensions, page_canvas_dimensions
    from .poster_config import (
        IDENTITY_LOCK_PROMPT_FILE,
        build_identity_lock_prompt,
        build_identity_reference_prompt,
        identity_lock_overscan,
    )
    from .poster_io import (
        load_cutout_items,
        load_poster_scope_data,
        poster_asset_slug,
        poster_bundle,
    )
except ImportError:
    from layout import latent_canvas_dimensions, page_canvas_dimensions
    from poster_config import (
        IDENTITY_LOCK_PROMPT_FILE,
        build_identity_lock_prompt,
        build_identity_reference_prompt,
        identity_lock_overscan,
    )
    from poster_io import (
        load_cutout_items,
        load_poster_scope_data,
        poster_asset_slug,
        poster_bundle,
    )


ROOT = Path(__file__).resolve().parents[2]
POSTER_ASSETS = ROOT / "data" / "poster_assets"


def node(class_type: str, **inputs: object) -> dict[str, object]:
    return {"class_type": class_type, "inputs": inputs}


def megapixel_marker(megapixels: float) -> str:
    return f"{megapixels:g}mp".replace(".", "p")


def output_dimensions(scope: str, megapixels: float) -> tuple[int, int]:
    if megapixels <= 0:
        raise ValueError("megapixels must be positive")
    manifest = poster_bundle(
        scope,
        poster_assets=POSTER_ASSETS,
    ).manifest
    return latent_canvas_dimensions(
        manifest.get("layout", {}).get("name", "standard_3x3"),
        megapixels,
    )


def page_dimensions(scope: str, megapixels: float) -> tuple[int, int]:
    """Return an exact physical card-grid ratio using the latent-aligned width."""
    manifest = poster_bundle(
        scope,
        poster_assets=POSTER_ASSETS,
    ).manifest
    return page_canvas_dimensions(
        manifest.get("layout", {}).get("name", "standard_3x3"),
        megapixels,
    )


def build_workflow(
    scope: str,
    seed: int,
    megapixels: float,
    *,
    unet_name: str = "flux-2-klein-4b-fp8.safetensors",
    clip_name: str = "qwen_3_4b.safetensors",
    vae_name: str = "flux2-vae.safetensors",
    generation_mode: str = "identity_lock",
    steps: int = 4,
    reference_mode: str = "identity",
) -> dict[str, object]:
    if generation_mode not in {"edit", "inpaint", "identity_lock"}:
        raise ValueError(f"Unsupported FLUX generation mode: {generation_mode}")
    if steps <= 0:
        raise ValueError("steps must be positive")
    if reference_mode not in {"composition", "identity"}:
        raise ValueError(f"Unsupported FLUX reference mode: {reference_mode}")
    work_dir = POSTER_ASSETS / scope / "comfyui_poster"
    bundle = poster_bundle(scope, poster_assets=POSTER_ASSETS)
    manifest = bundle.manifest
    if generation_mode == "inpaint":
        prompt_name = "inpaint_prompt.txt"
    elif generation_mode == "identity_lock":
        prompt_name = None
    else:
        prompt_name = "prompt.txt"
    if prompt_name is None:
        prompt = build_identity_lock_prompt(
            manifest,
            load_poster_scope_data(bundle),
        )
    else:
        prompt_path = work_dir / prompt_name
        prompt = prompt_path.read_text(encoding="utf-8").strip()
        if not prompt:
            raise ValueError(f"Prompt is empty: {prompt_path}")
    if generation_mode == "edit" and reference_mode == "identity":
        prompt = "\n\n".join(
            (
                build_identity_reference_prompt(
                    load_cutout_items(POSTER_ASSETS / scope),
                    manifest,
                ),
                prompt,
            )
        )
    width, height = output_dimensions(scope, megapixels)
    workflow = {
        "1": node("UNETLoader", unet_name=unet_name, weight_dtype="default"),
        "2": node("CLIPLoader", clip_name=clip_name, type="flux2", device="default"),
        "3": node("VAELoader", vae_name=vae_name),
        "4": node("CLIPTextEncode", text=prompt, clip=["2", 0]),
        "5": node("ConditioningZeroOut", conditioning=["4", 0]),
        "7": node("Flux2Scheduler", steps=steps, width=width, height=height),
        "8": node("RandomNoise", noise_seed=seed),
        "9": node("CFGGuider", model=["1", 0], positive=["17", 0], negative=["5", 0], cfg=1.0),
        "10": node("KSamplerSelect", sampler_name="euler"),
        "11": node(
            "SamplerCustomAdvanced",
            noise=["8", 0],
            guider=["9", 0],
            sampler=["10", 0],
            sigmas=["7", 0],
            latent_image=["15", 0],
        ),
        "12": node("VAEDecode", samples=["11", 0], vae=["3", 0]),
        "13": node(
            "SaveImage",
            images=["12", 0],
            filename_prefix=(
                f"{poster_asset_slug(scope)}_flux2_{generation_mode}_"
                f"{megapixel_marker(megapixels)}_scene_seed_{seed}"
            ),
        ),
        "14": node(
            "LoadImage",
            image=(
                "inpaint_reference.png"
                if generation_mode in {"inpaint", "identity_lock"}
                else "scene_reference.png"
            ),
        ),
    }
    if generation_mode == "edit":
        # Official edit topology: the reference conditions an independent empty
        # target. Never also use this latent as the sampler target; doing both
        # presents every subject twice and encourages duplicates.
        workflow["15"] = node(
            "EmptySD3LatentImage", width=width, height=height, batch_size=1
        )
        workflow["16"] = node("VAEEncode", pixels=["14", 0], vae=["3", 0])
        if reference_mode == "identity":
            previous_conditioning = ["4", 0]
            reference_names = tuple(
                f"identity_reference_{index}.png"
                for index in range(
                    1,
                    len(load_cutout_items(POSTER_ASSETS / scope)) + 1,
                )
            )
            for index, reference_name in enumerate(reference_names, start=1):
                load_id = str(20 + index * 3)
                encode_id = str(21 + index * 3)
                reference_id = str(22 + index * 3)
                workflow[load_id] = node(
                    "LoadImage", image=reference_name
                )
                workflow[encode_id] = node(
                    "VAEEncode", pixels=[load_id, 0], vae=["3", 0]
                )
                workflow[reference_id] = node(
                    "ReferenceLatent",
                    conditioning=previous_conditioning,
                    latent=[encode_id, 0],
                )
                previous_conditioning = [reference_id, 0]
            workflow["17"] = node(
                "ReferenceLatent",
                conditioning=previous_conditioning,
                latent=["16", 0],
            )
        else:
            workflow["17"] = node(
                "ReferenceLatent", conditioning=["4", 0], latent=["16", 0]
            )
    elif generation_mode == "inpaint":
        # True inpainting topology: the figures are the unmasked source pixels.
        # No ReferenceLatent is added, so the model receives each subject once.
        workflow["15"] = node(
            "VAEEncodeForInpaint",
            pixels=["14", 0],
            vae=["3", 0],
            mask=["14", 1],
            # Identity-lock mode: never grow the generated background into the
            # reviewed character silhouettes.
            grow_mask_by=0,
        )
        workflow["9"]["inputs"]["positive"] = ["4", 0]
        # Even unmasked pixels pass through a lossy VAE encode/decode cycle.
        # Restore them from the image that was present during generation so
        # identity-lock really preserves the reviewed source artwork. The
        # generated image is used only where the same alpha-derived background
        # mask told the sampler to paint.
        workflow["18"] = node(
            "ImageCompositeMasked",
            destination=["14", 0],
            source=["12", 0],
            x=0,
            y=0,
            resize_source=False,
            mask=["14", 1],
        )
        workflow["13"]["inputs"]["images"] = ["18", 0]
    else:
        # Pass one creates a clean, continuous scene without character-shaped
        # context. The reviewed source figures are then placed on that common
        # ground before pass two. Pass two sees their exact final composition
        # but may edit only the upper scene, safely away from every silhouette.
        stage_one_width, stage_one_height = identity_lock_overscan(
            width,
            height,
            manifest,
        )
        workflow["15"] = node(
            "EmptySD3LatentImage",
            width=stage_one_width,
            height=stage_one_height,
            batch_size=1,
        )
        workflow["7"]["inputs"]["width"] = stage_one_width
        workflow["7"]["inputs"]["height"] = stage_one_height
        workflow["9"]["inputs"]["positive"] = ["4", 0]
        workflow["26"] = node(
            "Flux2Scheduler",
            steps=steps,
            width=width,
            height=height,
        )
        workflow["27"] = node(
            "ImageCrop",
            image=["12", 0],
            width=width,
            height=height,
            x=(stage_one_width - width) // 2,
            y=(stage_one_height - height) // 2,
        )
        workflow["18"] = node("InvertMask", mask=["14", 1])
        workflow["19"] = node(
            "ImageCompositeMasked",
            destination=["27", 0],
            source=["14", 0],
            x=0,
            y=0,
            resize_source=False,
            mask=["18", 0],
        )
        workflow["20"] = node(
            "LoadImage", image="upper_context_mask.png"
        )
        workflow["28"] = node(
            "LoadImage",
            image="upper_context_generation_mask.png",
        )
        workflow["21"] = node(
            "VAEEncodeForInpaint",
            pixels=["19", 0],
            vae=["3", 0],
            # Sampling uses a separate binary mask whose latent edge lies
            # below the visible RGB feather. Reusing the feather here lets the
            # VAE switch source images around its midpoint and exposes a
            # horizontal brightness seam.
            mask=["28", 1],
            grow_mask_by=0,
        )
        workflow["22"] = node("RandomNoise", noise_seed=seed + 1)
        workflow["23"] = node(
            "SamplerCustomAdvanced",
            noise=["22", 0],
            guider=["9", 0],
            sampler=["10", 0],
            sigmas=["26", 0],
            latent_image=["21", 0],
        )
        workflow["24"] = node(
            "VAEDecode", samples=["23", 0], vae=["3", 0]
        )
        workflow["25"] = node(
            "ImageCompositeMasked",
            destination=["19", 0],
            source=["24", 0],
            x=0,
            y=0,
            resize_source=False,
            mask=["20", 1],
        )
        workflow["13"]["inputs"]["images"] = ["25", 0]
    return workflow


def write_workflow(
    scope: str,
    seed: int,
    megapixels: float,
    *,
    generation_mode: str = "identity_lock",
    unet_name: str = "flux-2-klein-4b-fp8.safetensors",
    steps: int = 4,
    reference_mode: str = "identity",
    clip_name: str = "qwen_3_4b.safetensors",
    vae_name: str = "flux2-vae.safetensors",
    output_dir: Path | None = None,
) -> Path:
    work_dir = POSTER_ASSETS / scope / "comfyui_poster"
    target_dir = output_dir or work_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / (
        f"workflow_api_{generation_mode}_"
        f"{megapixel_marker(megapixels)}_{seed}.json"
    )
    workflow = build_workflow(
        scope,
        seed,
        megapixels,
        unet_name=unet_name,
        generation_mode=generation_mode,
        steps=steps,
        reference_mode=reference_mode,
        clip_name=clip_name,
        vae_name=vae_name,
    )
    if generation_mode == "identity_lock":
        (target_dir / IDENTITY_LOCK_PROMPT_FILE).write_text(
            str(workflow["4"]["inputs"]["text"]).strip() + "\n",
            encoding="utf-8",
        )
    out_path.write_text(
        json.dumps(
            workflow,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", default="Base1")
    parser.add_argument("--seed", type=int, default=260715201)
    parser.add_argument("--megapixels", type=float, default=1.0)
    parser.add_argument(
        "--mode",
        choices=("edit", "inpaint", "identity_lock"),
        default="identity_lock",
    )
    parser.add_argument("--model", default="flux-2-klein-4b-fp8.safetensors")
    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument(
        "--reference-mode",
        choices=("composition", "identity"),
        default="identity",
    )
    parser.add_argument("--clip", default="qwen_3_4b.safetensors")
    parser.add_argument("--vae", default="flux2-vae.safetensors")
    args = parser.parse_args()
    print(
        write_workflow(
            args.scope,
            args.seed,
            args.megapixels,
            generation_mode=args.mode,
            unet_name=args.model,
            steps=args.steps,
            reference_mode=args.reference_mode,
            clip_name=args.clip,
            vae_name=args.vae,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
