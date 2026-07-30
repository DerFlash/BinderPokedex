#!/usr/bin/env python3
"""Prepare an isolated FLUX.2 preflight with one spatial image per subject."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image

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
    from .generation_options import (
        DEFAULT_FLUX_ENCODER,
        DEFAULT_FLUX_MODEL,
        DEFAULT_FLUX_STEPS,
        DEFAULT_FLUX_VAE,
    )
    from .poster_config import (
        build_joint_scene_prompt,
        build_spatial_identity_reference_prompt,
        subject_prompt_notes,
    )
    from .poster_io import (
        load_cutout_items,
        load_poster_scope_data,
        poster_asset_slug,
        poster_bundle,
    )
    from .prepare_comfyui_poster import prepare
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
    from generation_options import (
        DEFAULT_FLUX_ENCODER,
        DEFAULT_FLUX_MODEL,
        DEFAULT_FLUX_STEPS,
        DEFAULT_FLUX_VAE,
    )
    from poster_config import (
        build_joint_scene_prompt,
        build_spatial_identity_reference_prompt,
        subject_prompt_notes,
    )
    from poster_io import (
        load_cutout_items,
        load_poster_scope_data,
        poster_asset_slug,
        poster_bundle,
    )
    from prepare_comfyui_poster import prepare


ROOT = Path(__file__).resolve().parents[2]
POSTER_ASSETS = ROOT / "data" / "poster_assets"
PROMPT_FILE = "individual_spatial_joint_prompt.generated.txt"
REFERENCE_PREFIX = "individual_spatial_reference_"


def _percentage(value: int) -> str:
    if not isinstance(value, int) or not 0 <= value <= 1000:
        raise ValueError(
            "Individual spatial coordinates must be per-mille integers "
            "between 0 and 1000"
        )
    return f"{value / 10:.1f}%"


def build_individual_reference_prompt(
    items: list[dict[str, Any]],
    manifest: dict[str, Any],
    *,
    placement_contract: list[dict[str, int]],
) -> str:
    """Describe ordered spatial/detail pairs without a combined cast image."""
    if not items:
        raise ValueError("Individual spatial preflight needs at least one subject")
    if len(items) != len(placement_contract):
        raise ValueError("Every subject needs one placement contract")

    roles = []
    bounds = []
    for subject_index, (item, contract) in enumerate(
        zip(items, placement_contract, strict=True),
        start=1,
    ):
        name = str(
            item.get("name_en")
            or f"Pokemon #{item.get('pokemon_id', '?')}"
        )
        spatial_image = subject_index * 2 - 1
        detail_image = subject_index * 2
        roles.append(
            (
                f"IMAGE {spatial_image} is the poster-shaped spatial reference "
                f"for {name}; it contains exactly one complete {name} at the "
                "required final pose, orientation, scale, baseline, and poster "
                f"position. IMAGE {detail_image} is the unscaled identity and "
                f"anatomy detail for the same {name}."
            )
        )
        bounds.append(
            (
                f"{name}: x {_percentage(contract['left_per_mille'])} to "
                f"{_percentage(contract['right_per_mille'])}, y "
                f"{_percentage(contract['top_per_mille'])} to "
                f"{_percentage(contract['bottom_per_mille'])}"
            )
        )

    paragraphs = [
        (
            f"The {len(items) * 2} supplied images form {len(items)} ordered "
            "spatial-and-detail pairs. "
            f"{' '.join(roles)} Each pair describes one member of the same "
            "final cast, not two subjects. Across all pairs, render exactly "
            f"{len(items)} characters once each."
        ),
        (
            "Every poster-shaped spatial reference is authoritative only for "
            "its named character's pose, orientation, target scale, baseline, "
            "poster coordinates, and outer placement bounds. Every paired "
            "unscaled detail is authoritative only for that same character's "
            "exact silhouette, stature, anatomy, face, colors, markings, "
            "appendages, and defining details. The flat neutral fields are "
            "empty coordinate space, not sky, terrain, separate pictures, "
            "panels, cards, or a background plate. Do not paste any reference "
            "as a foreground layer; redraw all scene and character edges "
            "together from the empty target."
        ),
        (
            "The mandatory normalized final silhouette bounds are "
            f"{'; '.join(bounds)}. Match every complete silhouette, baseline, "
            "and surrounding landscape clearance within two percent of the "
            "full canvas. Keep every appendage inside its named bounds. The "
            "coordinates and invisible regions must never be drawn."
        ),
    ]
    specific_notes = subject_prompt_notes(items, manifest)
    if specific_notes:
        paragraphs.append(" ".join(specific_notes))
    return "\n\n".join(paragraphs)


def build_individual_spatial_prompt(
    scope: str,
    *,
    megapixels: float,
) -> str:
    """Reuse the accepted scene contract with only its reference roles changed."""
    bundle = poster_bundle(scope, poster_assets=POSTER_ASSETS)
    manifest = bundle.manifest
    items = load_cutout_items(bundle.asset_dir)
    width, height = output_dimensions(scope, megapixels)
    layout_name = str(
        manifest.get("layout", {}).get("name", "standard_3x3")
    )
    placement_contract = normalized_visible_placement_contract(
        joint_scene_canvas_placements(
            bundle.asset_dir,
            layout_name=layout_name,
            canvas_size=(width, height),
        ),
        canvas_size=(width, height),
    )
    accepted_reference_prompt = build_spatial_identity_reference_prompt(
        items,
        manifest,
        placement_contract=placement_contract,
    )
    replacement_reference_prompt = build_individual_reference_prompt(
        items,
        manifest,
        placement_contract=placement_contract,
    )
    prompt = build_joint_scene_prompt(
        manifest,
        load_poster_scope_data(bundle),
        items,
        placement_contract=placement_contract,
    )
    if accepted_reference_prompt not in prompt:
        raise RuntimeError("Accepted reference paragraph was not found")
    prompt = prompt.replace(
        accepted_reference_prompt,
        replacement_reference_prompt,
        1,
    )
    accepted_authority = (
        "IMAGE 1 is the strict authority for count, pose, orientation, "
        "target scale, baseline, and poster position. The corresponding "
        "individual identity image is the strict authority for each "
        "character's exact silhouette shape, stature, anatomy, facial "
        "features, colors, markings, and defining design details."
    )
    replacement_authority = (
        "The ordered poster-shaped references jointly control cast count, "
        "pose, orientation, target scale, baseline, and poster position. "
        "Each corresponding unscaled detail image controls only that named "
        "character's exact silhouette shape, stature, anatomy, facial "
        "features, colors, markings, and defining design details."
    )
    if accepted_authority not in prompt:
        raise RuntimeError("Accepted authority paragraph was not found")
    return prompt.replace(
        accepted_authority,
        replacement_authority,
        1,
    )


def write_individual_spatial_references(
    scope: str,
    work_dir: Path,
    *,
    megapixels: float,
) -> list[Path]:
    """Write one neutral poster-shaped final-position reference per subject."""
    bundle = poster_bundle(scope, poster_assets=POSTER_ASSETS)
    manifest = bundle.manifest
    width, height = output_dimensions(scope, megapixels)
    layout_name = str(
        manifest.get("layout", {}).get("name", "standard_3x3")
    )
    placements = joint_scene_canvas_placements(
        bundle.asset_dir,
        layout_name=layout_name,
        canvas_size=(width, height),
    )
    neutral = manifest.get("conditioning", {}).get(
        "identity_defaults",
        {},
    ).get("neutral_rgb", [226, 224, 211])
    if (
        not isinstance(neutral, list)
        or len(neutral) != 3
        or not all(
            isinstance(value, int) and 0 <= value <= 255
            for value in neutral
        )
    ):
        raise ValueError(
            "conditioning.identity_defaults.neutral_rgb must contain "
            "3 RGB integers"
        )

    for stale in work_dir.glob(f"{REFERENCE_PREFIX}*.png"):
        stale.unlink()
    outputs = []
    for index, placement in enumerate(placements, start=1):
        reference = Image.new(
            "RGBA",
            (width, height),
            (*neutral, 255),
        )
        reference.alpha_composite(
            placement["image"],
            (int(placement["x"]), int(placement["y"])),
        )
        path = work_dir / f"{REFERENCE_PREFIX}{index}.png"
        reference.convert("RGB").save(path, format="PNG", optimize=True)
        outputs.append(path)
    return outputs


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
    """Build one full-frame sampler with paired position and detail references."""
    if steps <= 0:
        raise ValueError("steps must be positive")
    items = load_cutout_items(
        poster_bundle(scope, poster_assets=POSTER_ASSETS).asset_dir
    )
    width, height = output_dimensions(scope, megapixels)
    prompt = build_individual_spatial_prompt(
        scope,
        megapixels=megapixels,
    )
    workflow: dict[str, object] = {
        "1": node("UNETLoader", unet_name=unet_name, weight_dtype="default"),
        "2": node(
            "CLIPLoader",
            clip_name=clip_name,
            type="flux2",
            device="default",
        ),
        "3": node("VAELoader", vae_name=vae_name),
        "4": node("CLIPTextEncode", text=prompt, clip=["2", 0]),
        "5": node("ConditioningZeroOut", conditioning=["4", 0]),
        "6": node(
            "EmptyFlux2LatentImage",
            width=width,
            height=height,
            batch_size=1,
        ),
        "7": node(
            "Flux2Scheduler",
            steps=steps,
            width=width,
            height=height,
        ),
        "8": node("RandomNoise", noise_seed=seed),
        "10": node("KSamplerSelect", sampler_name="euler"),
    }

    reference_names = []
    for index in range(1, len(items) + 1):
        reference_names.extend(
            (
                f"{REFERENCE_PREFIX}{index}.png",
                f"identity_reference_{index}.png",
            )
        )
    positive_conditioning: list[object] = ["4", 0]
    negative_conditioning: list[object] = ["5", 0]
    for index, reference_name in enumerate(reference_names):
        load_id = str(30 + index * 4)
        encode_id = str(31 + index * 4)
        positive_id = str(32 + index * 4)
        negative_id = str(33 + index * 4)
        workflow[load_id] = node("LoadImage", image=reference_name)
        workflow[encode_id] = node(
            "VAEEncode",
            pixels=[load_id, 0],
            vae=["3", 0],
        )
        workflow[positive_id] = node(
            "ReferenceLatent",
            conditioning=positive_conditioning,
            latent=[encode_id, 0],
        )
        workflow[negative_id] = node(
            "ReferenceLatent",
            conditioning=negative_conditioning,
            latent=[encode_id, 0],
        )
        positive_conditioning = [positive_id, 0]
        negative_conditioning = [negative_id, 0]

    workflow["70"] = node(
        "CFGGuider",
        model=["1", 0],
        positive=positive_conditioning,
        negative=negative_conditioning,
        cfg=1.0,
    )
    workflow["71"] = node(
        "SamplerCustomAdvanced",
        noise=["8", 0],
        guider=["70", 0],
        sampler=["10", 0],
        sigmas=["7", 0],
        latent_image=["6", 0],
    )
    workflow["72"] = node(
        "VAEDecode",
        samples=["71", 0],
        vae=["3", 0],
    )
    workflow["73"] = node(
        "SaveImage",
        images=["72", 0],
        filename_prefix=(
            f"{poster_asset_slug(scope)}_flux2_experiment_"
            f"individual_spatial_joint_{megapixel_marker(megapixels)}_"
            f"seed_{seed}"
        ),
    )
    return workflow


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
    """Prepare ignored references, prompt, and API workflow for one preflight."""
    work_dir = prepare(
        scope,
        megapixels,
        generation_mode="joint_scene",
        reference_mode="spatial_identity_joint",
    )
    (work_dir / "joint_scene_cast_reference.png").unlink(missing_ok=True)
    write_individual_spatial_references(
        scope,
        work_dir,
        megapixels=megapixels,
    )
    prompt = build_individual_spatial_prompt(
        scope,
        megapixels=megapixels,
    )
    (work_dir / PROMPT_FILE).write_text(
        "INDIVIDUAL SPATIAL JOINT - ISOLATED PREFLIGHT\n\n"
        f"{prompt.strip()}\n",
        encoding="utf-8",
    )
    workflow = build_workflow(
        scope,
        seed,
        megapixels,
        unet_name=unet_name,
        clip_name=clip_name,
        vae_name=vae_name,
        steps=steps,
    )
    workflow_path = (
        work_dir
        / (
            "workflow_api_experiment_individual_spatial_joint_"
            f"{megapixel_marker(megapixels)}_{seed}.json"
        )
    )
    workflow_path.write_text(
        json.dumps(workflow, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return workflow_path


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
