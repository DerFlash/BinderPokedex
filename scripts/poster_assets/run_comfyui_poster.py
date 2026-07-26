#!/usr/bin/env python3
"""Run the complete local ComfyUI poster pipeline against a running server."""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

try:
    from .create_anima_poster_workflow import write_workflow as write_anima_workflow
    from .create_comfyui_poster_workflow import (
        megapixel_marker,
        page_dimensions,
        write_workflow as write_flux_workflow,
    )
    from .create_flux1_canny_poster_workflow import (
        DEFAULT_CANNY_HIGH as DEFAULT_FLUX1_CANNY_HIGH,
        DEFAULT_CANNY_LOW as DEFAULT_FLUX1_CANNY_LOW,
        DEFAULT_CLIP as DEFAULT_FLUX1_CLIP,
        DEFAULT_CONTROLNET as DEFAULT_FLUX1_CONTROLNET,
        DEFAULT_CONTROL_STRENGTH as DEFAULT_FLUX1_CONTROL_STRENGTH,
        DEFAULT_GUIDANCE as DEFAULT_FLUX1_GUIDANCE,
        DEFAULT_MODEL as DEFAULT_FLUX1_MODEL,
        DEFAULT_STEPS as DEFAULT_FLUX1_STEPS,
        DEFAULT_T5 as DEFAULT_FLUX1_T5,
        DEFAULT_VAE as DEFAULT_FLUX1_VAE,
        write_workflow as write_flux1_canny_workflow,
    )
    from .create_qwen_edit_poster_workflow import (
        DEFAULT_CFG as DEFAULT_QWEN_CFG,
        DEFAULT_CLIP as DEFAULT_QWEN_CLIP,
        DEFAULT_LORA as DEFAULT_QWEN_LORA,
        DEFAULT_MODEL as DEFAULT_QWEN_MODEL,
        DEFAULT_SHIFT as DEFAULT_QWEN_SHIFT,
        DEFAULT_STEPS as DEFAULT_QWEN_STEPS,
        DEFAULT_VAE as DEFAULT_QWEN_VAE,
        write_workflow as write_qwen_edit_workflow,
    )
    from .finalize_comfyui_poster import SUPPORTED_LANGUAGES, finalize
    from .prepare_comfyui_poster import prepare
    from .provenance import add_model_artifact_hashes, write_run_metadata
    from .poster_io import (
        POSTER_ASSETS,
        poster_asset_slug,
        poster_bundle,
    )
    from .queue_comfyui_workflow import (
        queue_workflow,
        server_comfyui_root,
        validate_server_input_directory,
    )
    from .slice_poster import slice_poster
    from .create_comfyui_upscale_workflow import DEFAULT_UPSCALE_MODEL
    from .upscale_comfyui_poster import upscale
except ImportError:
    from create_anima_poster_workflow import write_workflow as write_anima_workflow
    from create_comfyui_poster_workflow import (
        megapixel_marker,
        page_dimensions,
        write_workflow as write_flux_workflow,
    )
    from create_flux1_canny_poster_workflow import (
        DEFAULT_CANNY_HIGH as DEFAULT_FLUX1_CANNY_HIGH,
        DEFAULT_CANNY_LOW as DEFAULT_FLUX1_CANNY_LOW,
        DEFAULT_CLIP as DEFAULT_FLUX1_CLIP,
        DEFAULT_CONTROLNET as DEFAULT_FLUX1_CONTROLNET,
        DEFAULT_CONTROL_STRENGTH as DEFAULT_FLUX1_CONTROL_STRENGTH,
        DEFAULT_GUIDANCE as DEFAULT_FLUX1_GUIDANCE,
        DEFAULT_MODEL as DEFAULT_FLUX1_MODEL,
        DEFAULT_STEPS as DEFAULT_FLUX1_STEPS,
        DEFAULT_T5 as DEFAULT_FLUX1_T5,
        DEFAULT_VAE as DEFAULT_FLUX1_VAE,
        write_workflow as write_flux1_canny_workflow,
    )
    from create_qwen_edit_poster_workflow import (
        DEFAULT_CFG as DEFAULT_QWEN_CFG,
        DEFAULT_CLIP as DEFAULT_QWEN_CLIP,
        DEFAULT_LORA as DEFAULT_QWEN_LORA,
        DEFAULT_MODEL as DEFAULT_QWEN_MODEL,
        DEFAULT_SHIFT as DEFAULT_QWEN_SHIFT,
        DEFAULT_STEPS as DEFAULT_QWEN_STEPS,
        DEFAULT_VAE as DEFAULT_QWEN_VAE,
        write_workflow as write_qwen_edit_workflow,
    )
    from finalize_comfyui_poster import SUPPORTED_LANGUAGES, finalize
    from prepare_comfyui_poster import prepare
    from provenance import add_model_artifact_hashes, write_run_metadata
    from poster_io import POSTER_ASSETS, poster_asset_slug, poster_bundle
    from queue_comfyui_workflow import (
        queue_workflow,
        server_comfyui_root,
        validate_server_input_directory,
    )
    from slice_poster import slice_poster
    from create_comfyui_upscale_workflow import DEFAULT_UPSCALE_MODEL
    from upscale_comfyui_poster import upscale


ENGINES = ("flux", "anima", "flux1_canny", "qwen_edit")
DEFAULT_GENERATION_MEGAPIXELS = 0.5
DEFAULT_OUTPUT_DPI = 300


def configured_generation(scope: str) -> dict[str, object]:
    """Load the reviewed generation contract used as production CLI defaults."""
    bundle = poster_bundle(scope, poster_assets=POSTER_ASSETS)
    manifest_path = bundle.manifest_path
    generation = bundle.manifest.get("artwork", {}).get("generation")
    if not isinstance(generation, dict) or not generation:
        raise ValueError(
            f"Poster scope has no artwork.generation contract: {manifest_path}"
        )
    return generation


def validate_raw_artwork(path: Path) -> None:
    image = Image.open(path).convert("RGB")
    extrema = image.getextrema()
    variation = ImageStat.Stat(image).stddev
    if max(high for _low, high in extrema) < 12 or max(variation) < 2.0:
        raise RuntimeError(f"ComfyUI produced blank or near-constant artwork: {path}")


def validate_identity_lock_pixels(
    scope: str,
    raw_artwork: Path,
    reference_path: Path | None = None,
) -> dict[str, int | str | bool]:
    """Require every fully opaque source pixel to survive diffusion unchanged."""
    reference_path = reference_path or (
        Path(__file__).resolve().parents[2]
        / "data"
        / "poster_assets"
        / scope
        / "comfyui_poster"
        / "inpaint_reference.png"
    )
    reference = Image.open(reference_path).convert("RGBA")
    artwork = Image.open(raw_artwork).convert("RGB")
    if artwork.size != reference.size:
        raise ValueError(
            "Identity-lock source and raw artwork dimensions differ: "
            f"{reference.size} != {artwork.size}"
        )

    alpha = reference.getchannel("A")
    opaque_pixels = alpha.histogram()[255]
    if opaque_pixels <= 0:
        raise ValueError(
            f"Identity-lock reference has no fully opaque source pixels: "
            f"{reference_path}"
        )
    opaque_mask = alpha.point(lambda value: 255 if value == 255 else 0)
    difference = ImageChops.difference(
        artwork,
        reference.convert("RGB"),
    )
    opaque_difference = Image.new("RGB", artwork.size)
    opaque_difference.paste(difference, mask=opaque_mask)
    changed_box = opaque_difference.getbbox()
    if changed_box is not None:
        raise RuntimeError(
            "Identity-lock output changed fully opaque source pixels inside "
            f"{changed_box}: {raw_artwork}"
        )
    return {
        "method": "exact_opaque_source_pixels",
        "opaque_pixels": opaque_pixels,
        "changed_pixels": 0,
        "passed": True,
    }


def resize_artwork(scope: str, source: Path, destination: Path, megapixels: float) -> Path:
    target_size = page_dimensions(scope, megapixels)
    image = Image.open(source).convert("RGB")
    if image.size != target_size:
        image = image.resize(target_size, Image.Resampling.LANCZOS)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, format="PNG", optimize=True)
    validate_raw_artwork(destination)
    return destination


def write_engine_workflow(
    engine: str,
    scope: str,
    seed: int,
    megapixels: float,
    *,
    reference_strength: float = 1.0,
    anima_model: str = "AnimaYume_tuned_v05.safetensors",
    anima_mode: str = "generate",
    flux_mode: str = "identity_lock",
    flux_model: str = "flux-2-klein-4b-fp8.safetensors",
    flux_steps: int = 4,
    flux_reference_mode: str = "identity",
    flux_clip: str = "qwen_3_4b.safetensors",
    flux1_model: str = DEFAULT_FLUX1_MODEL,
    flux1_clip: str = DEFAULT_FLUX1_CLIP,
    flux1_t5: str = DEFAULT_FLUX1_T5,
    flux1_vae: str = DEFAULT_FLUX1_VAE,
    flux1_controlnet: str = DEFAULT_FLUX1_CONTROLNET,
    flux1_steps: int = DEFAULT_FLUX1_STEPS,
    flux1_guidance: float = DEFAULT_FLUX1_GUIDANCE,
    flux1_control_strength: float = DEFAULT_FLUX1_CONTROL_STRENGTH,
    flux1_canny_low: float = DEFAULT_FLUX1_CANNY_LOW,
    flux1_canny_high: float = DEFAULT_FLUX1_CANNY_HIGH,
    qwen_model: str = DEFAULT_QWEN_MODEL,
    qwen_clip: str = DEFAULT_QWEN_CLIP,
    qwen_vae: str = DEFAULT_QWEN_VAE,
    qwen_lora: str = DEFAULT_QWEN_LORA,
    qwen_steps: int = DEFAULT_QWEN_STEPS,
    qwen_cfg: float = DEFAULT_QWEN_CFG,
    qwen_shift: float = DEFAULT_QWEN_SHIFT,
    workflow_output_dir: Path | None = None,
) -> Path:
    if engine == "flux":
        return write_flux_workflow(
            scope,
            seed,
            megapixels,
            generation_mode=flux_mode,
            unet_name=flux_model,
            steps=flux_steps,
            reference_mode=flux_reference_mode,
            clip_name=flux_clip,
            output_dir=workflow_output_dir,
        )
    if engine == "anima":
        return write_anima_workflow(
            scope,
            seed,
            megapixels,
            reference_strength,
            model_name=anima_model,
            generation_mode=anima_mode,
            output_dir=workflow_output_dir,
        )
    if engine == "flux1_canny":
        return write_flux1_canny_workflow(
            scope,
            seed,
            megapixels,
            unet_name=flux1_model,
            clip_name=flux1_clip,
            t5_name=flux1_t5,
            vae_name=flux1_vae,
            controlnet_name=flux1_controlnet,
            steps=flux1_steps,
            guidance=flux1_guidance,
            control_strength=flux1_control_strength,
            canny_low=flux1_canny_low,
            canny_high=flux1_canny_high,
            output_dir=workflow_output_dir,
        )
    if engine == "qwen_edit":
        return write_qwen_edit_workflow(
            scope,
            seed,
            megapixels,
            unet_name=qwen_model,
            clip_name=qwen_clip,
            vae_name=qwen_vae,
            lora_name=qwen_lora,
            steps=qwen_steps,
            cfg=qwen_cfg,
            shift=qwen_shift,
            output_dir=workflow_output_dir,
        )
    raise ValueError(f"Unsupported engine: {engine}")


def run(
    scope: str,
    seed: int,
    megapixels: float,
    server: str,
    timeout: int,
    language: str,
    *,
    engine: str = "flux",
    reference_strength: float = 1.0,
    anima_model: str = "AnimaYume_tuned_v05.safetensors",
    anima_mode: str = "generate",
    flux_mode: str = "identity_lock",
    flux_model: str = "flux-2-klein-4b-fp8.safetensors",
    flux_steps: int = 4,
    flux_reference_mode: str = "identity",
    flux_clip: str = "qwen_3_4b.safetensors",
    flux1_model: str = DEFAULT_FLUX1_MODEL,
    flux1_clip: str = DEFAULT_FLUX1_CLIP,
    flux1_t5: str = DEFAULT_FLUX1_T5,
    flux1_vae: str = DEFAULT_FLUX1_VAE,
    flux1_controlnet: str = DEFAULT_FLUX1_CONTROLNET,
    flux1_steps: int = DEFAULT_FLUX1_STEPS,
    flux1_guidance: float = DEFAULT_FLUX1_GUIDANCE,
    flux1_control_strength: float = DEFAULT_FLUX1_CONTROL_STRENGTH,
    flux1_canny_low: float = DEFAULT_FLUX1_CANNY_LOW,
    flux1_canny_high: float = DEFAULT_FLUX1_CANNY_HIGH,
    qwen_model: str = DEFAULT_QWEN_MODEL,
    qwen_clip: str = DEFAULT_QWEN_CLIP,
    qwen_vae: str = DEFAULT_QWEN_VAE,
    qwen_lora: str = DEFAULT_QWEN_LORA,
    qwen_steps: int = DEFAULT_QWEN_STEPS,
    qwen_cfg: float = DEFAULT_QWEN_CFG,
    qwen_shift: float = DEFAULT_QWEN_SHIFT,
    output_megapixels: float | None = None,
    output_dpi: int | None = DEFAULT_OUTPUT_DPI,
    upscale_model: str = DEFAULT_UPSCALE_MODEL,
) -> tuple[Path, Path, Path, Path]:
    if output_megapixels is not None and output_dpi is not None:
        raise ValueError("Choose either output_megapixels or output_dpi, not both")
    if output_dpi is not None and output_dpi <= 0:
        raise ValueError("output_dpi must be positive")
    work_dir = prepare(scope, megapixels)
    validate_server_input_directory(server, work_dir)
    comfy_root = server_comfyui_root(server)
    if comfy_root is None:
        raise RuntimeError(
            "ComfyUI did not report an absolute main.py path; start it with "
            "scripts/poster_assets/start_comfyui_poster.sh"
        )
    workflow_path = write_engine_workflow(
        engine,
        scope,
        seed,
        megapixels,
        reference_strength=reference_strength,
        anima_model=anima_model,
        anima_mode=anima_mode,
        flux_mode=flux_mode,
        flux_model=flux_model,
        flux_steps=flux_steps,
        flux_reference_mode=flux_reference_mode,
        flux_clip=flux_clip,
        flux1_model=flux1_model,
        flux1_clip=flux1_clip,
        flux1_t5=flux1_t5,
        flux1_vae=flux1_vae,
        flux1_controlnet=flux1_controlnet,
        flux1_steps=flux1_steps,
        flux1_guidance=flux1_guidance,
        flux1_control_strength=flux1_control_strength,
        flux1_canny_low=flux1_canny_low,
        flux1_canny_high=flux1_canny_high,
        qwen_model=qwen_model,
        qwen_clip=qwen_clip,
        qwen_vae=qwen_vae,
        qwen_lora=qwen_lora,
        qwen_steps=qwen_steps,
        qwen_cfg=qwen_cfg,
        qwen_shift=qwen_shift,
    )
    outputs = queue_workflow(workflow_path, server=server, timeout=timeout)
    images = [item for item in outputs if item.get("type") == "output" and item.get("filename")]
    if len(images) != 1:
        raise RuntimeError(f"Expected exactly one output image, got: {outputs}")

    raw_path = (
        work_dir
        / "output"
        / str(images[0].get("subfolder", ""))
        / str(images[0]["filename"])
    )
    if not raw_path.is_file():
        raise FileNotFoundError(f"ComfyUI reported an output that does not exist: {raw_path}")
    validate_raw_artwork(raw_path)
    validation: dict[str, object] = {}
    if engine == "flux" and flux_mode == "identity_lock":
        validation["identity_lock"] = validate_identity_lock_pixels(
            scope,
            raw_path,
        )
    final_megapixels = output_megapixels or megapixels
    if engine == "flux":
        if flux_mode == "identity_lock":
            effective_reference_mode = "two_pass_source_pixels"
        elif flux_mode == "inpaint":
            effective_reference_mode = "source_pixels"
        else:
            effective_reference_mode = flux_reference_mode
        if "9b" in flux_model.lower():
            model_variant = "distilled9b"
        elif "base-4b" in flux_model:
            model_variant = "base4b"
        else:
            model_variant = "distilled4b"
        run_marker = (
            f"{flux_mode}_{effective_reference_mode}_{model_variant}_"
            f"{flux_steps}step_{megapixel_marker(megapixels)}"
        )
        if output_dpi is not None:
            run_marker += f"_to_{output_dpi}dpi"
        elif final_megapixels != megapixels:
            run_marker += f"_to_{megapixel_marker(final_megapixels)}"
    elif engine == "anima":
        run_marker = anima_mode
        if output_dpi is not None:
            run_marker += f"_to_{output_dpi}dpi"
        elif final_megapixels != megapixels:
            run_marker += f"_to_{megapixel_marker(final_megapixels)}"
    elif engine == "flux1_canny":
        strength_marker = f"{flux1_control_strength:g}".replace(".", "p")
        run_marker = (
            f"{flux1_steps}step_canny{strength_marker}_"
            f"{megapixel_marker(megapixels)}"
        )
        if output_dpi is not None:
            run_marker += f"_to_{output_dpi}dpi"
        elif final_megapixels != megapixels:
            run_marker += f"_to_{megapixel_marker(final_megapixels)}"
    elif engine == "qwen_edit":
        run_marker = f"{qwen_steps}step_{megapixel_marker(megapixels)}"
        if output_dpi is not None:
            run_marker += f"_to_{output_dpi}dpi"
        elif final_megapixels != megapixels:
            run_marker += f"_to_{megapixel_marker(final_megapixels)}"
    else:
        raise ValueError(f"Unsupported engine: {engine}")
    final_path = (
        work_dir
        / "output"
        / f"{poster_asset_slug(scope)}_{engine}_{run_marker}_poster_{language}_seed_{seed}_final.png"
    )
    upscale_workflow_path = None
    if output_dpi is not None:
        artwork_path, upscale_workflow_path = upscale(
            scope,
            raw_path,
            server=server,
            timeout=timeout,
            dpi=output_dpi,
            model_name=upscale_model,
        )
    else:
        artwork_marker = (
            f"to_{megapixel_marker(final_megapixels)}"
            if final_megapixels != megapixels
            else "page"
        )
        artwork_path = resize_artwork(
            scope,
            raw_path,
            work_dir / "temp" / f"{raw_path.stem}_{artwork_marker}.png",
            final_megapixels,
        )
    finalize(scope, artwork_path, final_path, language)
    slice_poster(scope, final_path)
    if engine == "flux":
        generation = {
            "engine": engine,
            "model": flux_model,
            "encoder": flux_clip,
            "vae": "flux2-vae.safetensors",
            "mode": flux_mode,
            "reference_mode": effective_reference_mode,
            "seed": seed,
            "steps": flux_steps,
            "generation_megapixels": megapixels,
        }
    elif engine == "anima":
        generation = {
            "engine": engine,
            "model": anima_model,
            "encoder": "qwen_3_06b_base.safetensors",
            "vae": "qwen_image_vae.safetensors",
            "mode": anima_mode,
            "reference_mode": "cosmos",
            "reference_strength": reference_strength,
            "seed": seed,
            "steps": 22,
            "generation_megapixels": megapixels,
        }
    elif engine == "flux1_canny":
        generation = {
            "engine": engine,
            "model": flux1_model,
            "encoder": flux1_clip,
            "encoder_2": flux1_t5,
            "vae": flux1_vae,
            "controlnet": flux1_controlnet,
            "mode": "generate",
            "reference_mode": "canny",
            "seed": seed,
            "steps": flux1_steps,
            "guidance": flux1_guidance,
            "control_strength": flux1_control_strength,
            "canny_low": flux1_canny_low,
            "canny_high": flux1_canny_high,
            "generation_megapixels": megapixels,
        }
    elif engine == "qwen_edit":
        generation = {
            "engine": engine,
            "model": qwen_model,
            "encoder": qwen_clip,
            "vae": qwen_vae,
            "lora": qwen_lora,
            "mode": "edit",
            "reference_mode": "multi_reference",
            "seed": seed,
            "steps": qwen_steps,
            "cfg": qwen_cfg,
            "shift": qwen_shift,
            "generation_megapixels": megapixels,
        }
    else:
        raise ValueError(f"Unsupported engine: {engine}")
    if output_dpi is not None:
        generation.update(
            {
                "output_dpi": output_dpi,
                "output_method": "model_upscale",
                "upscale_model": upscale_model,
            }
        )
    else:
        generation.update(
            {
                "output_megapixels": final_megapixels,
                "output_method": "lanczos",
            }
        )
    generation = add_model_artifact_hashes(comfy_root, generation)
    run_metadata_path = write_run_metadata(
        scope,
        artwork_path,
        workflow_path,
        generation,
        raw_artwork_path=raw_path,
        additional_workflows=(
            {"upscale_workflow": upscale_workflow_path}
            if upscale_workflow_path is not None
            else None
        ),
        validation=validation or None,
    )
    return raw_path, artwork_path, final_path, run_metadata_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", default="Base1")
    parser.add_argument(
        "--seed",
        type=int,
        help="Override the stable seed configured in poster.yaml",
    )
    parser.add_argument(
        "--megapixels",
        type=float,
        help="Override artwork.generation.generation_megapixels",
    )
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--output-dpi",
        type=int,
        help="Model-upscale the text-free artwork to this physical print dpi (default: 300)",
    )
    output_group.add_argument(
        "--output-megapixels",
        type=float,
        help="Legacy preview output using a regular Lanczos resize",
    )
    parser.add_argument(
        "--upscale-model",
        help="Override the ComfyUI upscale model configured in poster.yaml",
    )
    parser.add_argument("--server", default="http://127.0.0.1:8188")
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument(
        "--language",
        choices=SUPPORTED_LANGUAGES,
        default="en",
    )
    parser.add_argument(
        "--engine",
        choices=(*ENGINES, "both", "all"),
        help="Override artwork.generation.engine",
    )
    parser.add_argument(
        "--reference-strength",
        type=float,
        default=1.0,
        help="AnimaEdit LoRA strength; ignored by FLUX",
    )
    parser.add_argument(
        "--anima-model",
        default="AnimaYume_tuned_v05.safetensors",
        help="Anima-compatible diffusion model; ignored by FLUX",
    )
    parser.add_argument(
        "--anima-mode",
        choices=("generate", "edit"),
        default="generate",
        help="Generate from an empty target or edit the material scaffold",
    )
    parser.add_argument(
        "--flux-mode",
        choices=("edit", "inpaint", "identity_lock"),
        help=(
            "Use the two-pass exact-source lock (default), direct inpainting, "
            "or an independent reference edit"
        ),
    )
    parser.add_argument("--flux-model")
    parser.add_argument(
        "--flux-steps",
        type=int,
        help="Use 4 for distilled Klein; typically 20-28 for Klein Base",
    )
    parser.add_argument(
        "--flux-reference-mode",
        choices=("composition", "identity"),
        default="identity",
        help=(
            "Append one identity close-up per character or use only the "
            "scene composition; applies to edit mode"
        ),
    )
    parser.add_argument(
        "--flux-clip",
        help="FLUX.2 text encoder matching the selected model size",
    )
    parser.add_argument("--flux1-model", default=DEFAULT_FLUX1_MODEL)
    parser.add_argument("--flux1-clip", default=DEFAULT_FLUX1_CLIP)
    parser.add_argument("--flux1-t5", default=DEFAULT_FLUX1_T5)
    parser.add_argument("--flux1-vae", default=DEFAULT_FLUX1_VAE)
    parser.add_argument("--flux1-controlnet", default=DEFAULT_FLUX1_CONTROLNET)
    parser.add_argument("--flux1-steps", type=int, default=DEFAULT_FLUX1_STEPS)
    parser.add_argument(
        "--flux1-guidance",
        type=float,
        default=DEFAULT_FLUX1_GUIDANCE,
    )
    parser.add_argument(
        "--flux1-control-strength",
        type=float,
        default=DEFAULT_FLUX1_CONTROL_STRENGTH,
    )
    parser.add_argument(
        "--flux1-canny-low",
        type=float,
        default=DEFAULT_FLUX1_CANNY_LOW,
    )
    parser.add_argument(
        "--flux1-canny-high",
        type=float,
        default=DEFAULT_FLUX1_CANNY_HIGH,
    )
    parser.add_argument("--qwen-model", default=DEFAULT_QWEN_MODEL)
    parser.add_argument("--qwen-clip", default=DEFAULT_QWEN_CLIP)
    parser.add_argument("--qwen-vae", default=DEFAULT_QWEN_VAE)
    parser.add_argument("--qwen-lora", default=DEFAULT_QWEN_LORA)
    parser.add_argument("--qwen-steps", type=int, default=DEFAULT_QWEN_STEPS)
    parser.add_argument("--qwen-cfg", type=float, default=DEFAULT_QWEN_CFG)
    parser.add_argument("--qwen-shift", type=float, default=DEFAULT_QWEN_SHIFT)
    args = parser.parse_args()
    configured = configured_generation(args.scope)
    seed = (
        args.seed
        if args.seed is not None
        else int(configured.get("seed", 260715201))
    )
    megapixels = (
        args.megapixels
        if args.megapixels is not None
        else float(
            configured.get(
                "generation_megapixels",
                DEFAULT_GENERATION_MEGAPIXELS,
            )
        )
    )
    selected_engine = str(args.engine or configured.get("engine", "flux"))
    flux_mode = str(args.flux_mode or configured.get("mode", "identity_lock"))
    flux_model = str(
        args.flux_model
        or configured.get("model", "flux-2-klein-4b-fp8.safetensors")
    )
    flux_steps = (
        args.flux_steps
        if args.flux_steps is not None
        else int(configured.get("steps", 4))
    )
    flux_clip = str(
        args.flux_clip
        or configured.get("encoder", "qwen_3_4b.safetensors")
    )
    upscale_model = str(
        args.upscale_model
        or configured.get("upscale_model", DEFAULT_UPSCALE_MODEL)
    )
    output_dpi = args.output_dpi
    if output_dpi is None and args.output_megapixels is None:
        if configured.get("output_method") == "lanczos":
            args.output_megapixels = float(
                configured.get("output_megapixels", megapixels)
            )
        else:
            output_dpi = int(
                configured.get("output_dpi", DEFAULT_OUTPUT_DPI)
            )
    if selected_engine == "both":
        engines = ("flux", "anima")
    elif selected_engine == "all":
        engines = ENGINES
    else:
        engines = (selected_engine,)
    for engine in engines:
        raw_path, artwork_path, final_path, run_metadata_path = run(
            args.scope,
            seed,
            megapixels,
            args.server,
            args.timeout,
            args.language,
            engine=engine,
            reference_strength=args.reference_strength,
            anima_model=args.anima_model,
            anima_mode=args.anima_mode,
            flux_mode=flux_mode,
            flux_model=flux_model,
            flux_steps=flux_steps,
            flux_reference_mode=args.flux_reference_mode,
            flux_clip=flux_clip,
            flux1_model=args.flux1_model,
            flux1_clip=args.flux1_clip,
            flux1_t5=args.flux1_t5,
            flux1_vae=args.flux1_vae,
            flux1_controlnet=args.flux1_controlnet,
            flux1_steps=args.flux1_steps,
            flux1_guidance=args.flux1_guidance,
            flux1_control_strength=args.flux1_control_strength,
            flux1_canny_low=args.flux1_canny_low,
            flux1_canny_high=args.flux1_canny_high,
            qwen_model=args.qwen_model,
            qwen_clip=args.qwen_clip,
            qwen_vae=args.qwen_vae,
            qwen_lora=args.qwen_lora,
            qwen_steps=args.qwen_steps,
            qwen_cfg=args.qwen_cfg,
            qwen_shift=args.qwen_shift,
            output_megapixels=args.output_megapixels,
            output_dpi=output_dpi,
            upscale_model=upscale_model,
        )
        print(f"[{engine}] Raw artwork: {raw_path}")
        print(f"[{engine}] Text-free artwork: {artwork_path}")
        print(f"[{engine}] Final poster: {final_path}")
        print(f"[{engine}] Card slices: {final_path.with_name(f'{final_path.stem}_cards')}")
        print(f"[{engine}] Run metadata: {run_metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
