#!/usr/bin/env python3
"""Run the complete local ComfyUI poster pipeline against a running server."""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageStat

try:
    from .create_anima_poster_workflow import (
        DEFAULT_CFG as DEFAULT_ANIMA_CFG,
        DEFAULT_ENCODER as DEFAULT_ANIMA_ENCODER,
        DEFAULT_GENERATION_MODE as DEFAULT_ANIMA_MODE,
        DEFAULT_LORA as DEFAULT_ANIMA_LORA,
        DEFAULT_MODEL as DEFAULT_ANIMA_MODEL,
        DEFAULT_REFERENCE_STRENGTH,
        DEFAULT_STEPS as DEFAULT_ANIMA_STEPS,
        DEFAULT_VAE as DEFAULT_ANIMA_VAE,
        write_workflow as write_anima_workflow,
    )
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
    from .generation_contract import (
        is_joint_scene_generation,
        validate_generation_contract,
    )
    from .generation_options import (
        metadata_from_workflow_options,
        resolve_generation_options,
    )
    from .layout import build_print_layout
    from .prepare_comfyui_poster import prepare
    from .provenance import (
        add_model_artifact_hashes,
        sha256_file,
        write_run_metadata,
    )
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
    from .source_pixel_audit import audit_exact_source_pixels
    from .create_comfyui_upscale_workflow import DEFAULT_UPSCALE_MODEL
    from .upscale_comfyui_poster import upscale
except ImportError:
    from create_anima_poster_workflow import (
        DEFAULT_CFG as DEFAULT_ANIMA_CFG,
        DEFAULT_ENCODER as DEFAULT_ANIMA_ENCODER,
        DEFAULT_GENERATION_MODE as DEFAULT_ANIMA_MODE,
        DEFAULT_LORA as DEFAULT_ANIMA_LORA,
        DEFAULT_MODEL as DEFAULT_ANIMA_MODEL,
        DEFAULT_REFERENCE_STRENGTH,
        DEFAULT_STEPS as DEFAULT_ANIMA_STEPS,
        DEFAULT_VAE as DEFAULT_ANIMA_VAE,
        write_workflow as write_anima_workflow,
    )
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
    from generation_contract import (
        is_joint_scene_generation,
        validate_generation_contract,
    )
    from generation_options import (
        metadata_from_workflow_options,
        resolve_generation_options,
    )
    from layout import build_print_layout
    from prepare_comfyui_poster import prepare
    from provenance import (
        add_model_artifact_hashes,
        sha256_file,
        write_run_metadata,
    )
    from poster_io import POSTER_ASSETS, poster_asset_slug, poster_bundle
    from queue_comfyui_workflow import (
        queue_workflow,
        server_comfyui_root,
        validate_server_input_directory,
    )
    from slice_poster import slice_poster
    from source_pixel_audit import audit_exact_source_pixels
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
    return audit_exact_source_pixels(
        reference_path,
        raw_artwork,
        require_match=True,
    )


def resize_artwork(scope: str, source: Path, destination: Path, megapixels: float) -> Path:
    target_size = page_dimensions(scope, megapixels)
    image = Image.open(source).convert("RGB")
    if image.size != target_size:
        image = image.resize(target_size, Image.Resampling.LANCZOS)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, format="PNG", optimize=True)
    validate_raw_artwork(destination)
    return destination


def resize_artwork_to_dpi(
    scope: str,
    source: Path,
    destination: Path,
    dpi: int,
) -> Path:
    """Resize deterministically to the exact physical card-grid raster."""
    if dpi <= 0:
        raise ValueError("dpi must be positive")
    bundle = poster_bundle(scope, poster_assets=POSTER_ASSETS)
    layout_name = str(
        bundle.manifest.get("layout", {}).get(
            "name",
            "standard_3x3",
        )
    )
    print_layout = build_print_layout(layout_name, dpi)
    target_size = (print_layout.width_px, print_layout.height_px)
    image = Image.open(source).convert("RGB")
    if image.size != target_size:
        image = image.resize(target_size, Image.Resampling.LANCZOS)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(
        destination,
        format="PNG",
        optimize=True,
        dpi=(dpi, dpi),
    )
    validate_raw_artwork(destination)
    return destination


def write_engine_workflow(
    engine: str,
    scope: str,
    seed: int,
    megapixels: float,
    *,
    reference_strength: float = DEFAULT_REFERENCE_STRENGTH,
    anima_model: str = DEFAULT_ANIMA_MODEL,
    anima_lora: str = DEFAULT_ANIMA_LORA,
    anima_encoder: str = DEFAULT_ANIMA_ENCODER,
    anima_vae: str = DEFAULT_ANIMA_VAE,
    anima_steps: int = DEFAULT_ANIMA_STEPS,
    anima_cfg: float = DEFAULT_ANIMA_CFG,
    anima_mode: str = DEFAULT_ANIMA_MODE,
    anima_control_method: str = "edit_lora",
    flux_mode: str = "identity_lock",
    flux_model: str = "flux-2-klein-4b-fp8.safetensors",
    flux_steps: int = 4,
    flux_reference_mode: str = "identity",
    flux_clip: str = "qwen_3_4b.safetensors",
    flux_vae: str = "flux2-vae.safetensors",
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
            vae_name=flux_vae,
            output_dir=workflow_output_dir,
        )
    if engine == "anima":
        return write_anima_workflow(
            scope,
            seed,
            megapixels,
            reference_strength,
            control_method=anima_control_method,
            model_name=anima_model,
            lora_name=anima_lora,
            encoder_name=anima_encoder,
            vae_name=anima_vae,
            steps=anima_steps,
            cfg=anima_cfg,
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
    reference_strength: float = DEFAULT_REFERENCE_STRENGTH,
    anima_model: str = DEFAULT_ANIMA_MODEL,
    anima_lora: str = DEFAULT_ANIMA_LORA,
    anima_encoder: str = DEFAULT_ANIMA_ENCODER,
    anima_vae: str = DEFAULT_ANIMA_VAE,
    anima_steps: int = DEFAULT_ANIMA_STEPS,
    anima_cfg: float = DEFAULT_ANIMA_CFG,
    anima_mode: str = DEFAULT_ANIMA_MODE,
    anima_control_method: str = "edit_lora",
    flux_mode: str = "identity_lock",
    flux_model: str = "flux-2-klein-4b-fp8.safetensors",
    flux_steps: int = 4,
    flux_reference_mode: str = "identity",
    flux_clip: str = "qwen_3_4b.safetensors",
    flux_vae: str = "flux2-vae.safetensors",
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
    workflow_options = {
        "reference_strength": reference_strength,
        "anima_model": anima_model,
        "anima_lora": anima_lora,
        "anima_encoder": anima_encoder,
        "anima_vae": anima_vae,
        "anima_steps": anima_steps,
        "anima_cfg": anima_cfg,
        "anima_mode": anima_mode,
        "anima_control_method": anima_control_method,
        "flux_mode": flux_mode,
        "flux_model": flux_model,
        "flux_steps": flux_steps,
        "flux_reference_mode": flux_reference_mode,
        "flux_clip": flux_clip,
        "flux_vae": flux_vae,
        "flux1_model": flux1_model,
        "flux1_clip": flux1_clip,
        "flux1_t5": flux1_t5,
        "flux1_vae": flux1_vae,
        "flux1_controlnet": flux1_controlnet,
        "flux1_steps": flux1_steps,
        "flux1_guidance": flux1_guidance,
        "flux1_control_strength": flux1_control_strength,
        "flux1_canny_low": flux1_canny_low,
        "flux1_canny_high": flux1_canny_high,
        "qwen_model": qwen_model,
        "qwen_clip": qwen_clip,
        "qwen_vae": qwen_vae,
        "qwen_lora": qwen_lora,
        "qwen_steps": qwen_steps,
        "qwen_cfg": qwen_cfg,
        "qwen_shift": qwen_shift,
    }
    engine_generation = metadata_from_workflow_options(
        engine,
        workflow_options,
    )
    joint_scene = is_joint_scene_generation(engine_generation)
    if joint_scene:
        work_dir = prepare(
            scope,
            megapixels,
            generation_mode="joint_scene",
        )
    else:
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
        **workflow_options,
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
    if not joint_scene:
        source_reference = work_dir / "inpaint_reference.png"
        source_pixel_audit = audit_exact_source_pixels(
            source_reference,
            raw_path,
            require_match=(
                engine == "flux"
                and flux_mode == "identity_lock"
            ),
        )
        with Image.open(raw_path) as audited_artwork:
            audit_width, audit_height = audited_artwork.size
        source_pixel_audit.update(
            {
                "stage": "raw_generation",
                "reference_sha256": sha256_file(source_reference),
                "artwork_sha256": sha256_file(raw_path),
                "width": audit_width,
                "height": audit_height,
            }
        )
        validation["source_pixels"] = source_pixel_audit
    final_megapixels = output_megapixels or megapixels
    if engine == "flux":
        if flux_mode == "identity_lock":
            effective_reference_mode = "two_pass_source_pixels"
        elif flux_mode == "joint_scene":
            effective_reference_mode = "multi_reference_joint"
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
        if joint_scene:
            artwork_path = resize_artwork_to_dpi(
                scope,
                raw_path,
                work_dir
                / "temp"
                / f"{raw_path.stem}_to_{output_dpi}dpi.png",
                output_dpi,
            )
        else:
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
    generation = {
        **engine_generation,
        "seed": seed,
        "generation_megapixels": megapixels,
    }
    if output_dpi is not None:
        if joint_scene:
            generation.update(
                {
                    "output_dpi": output_dpi,
                    "output_method": "lanczos",
                }
            )
        else:
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
    validate_generation_contract(generation)
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
        help=(
            "Write this exact physical print raster; joint_scene uses "
            "deterministic Lanczos, legacy modes use their configured "
            "model-upscale path (default: 300)"
        ),
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
        help="AnimaEdit LoRA strength; ignored by FLUX",
    )
    parser.add_argument(
        "--anima-model",
        help="Anima-compatible diffusion model; ignored by FLUX",
    )
    parser.add_argument("--anima-lora")
    parser.add_argument("--anima-encoder")
    parser.add_argument("--anima-vae")
    parser.add_argument("--anima-steps", type=int)
    parser.add_argument("--anima-cfg", type=float)
    parser.add_argument(
        "--anima-control-method",
        choices=("edit_lora",),
    )
    parser.add_argument(
        "--anima-mode",
        choices=("generate", "edit"),
        help="Generate from an empty target or edit the material scaffold",
    )
    parser.add_argument(
        "--flux-mode",
        choices=("edit", "inpaint", "identity_lock", "joint_scene"),
        help=(
            "Use the two-pass exact-source lock (default), generate a "
            "subject-free draft followed by one unified whole-image pass, "
            "use direct inpainting, or an independent reference edit"
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
        help=(
            "Append one identity close-up per character or use only the "
            "scene composition; applies to edit mode"
        ),
    )
    parser.add_argument(
        "--flux-clip",
        help="FLUX.2 text encoder matching the selected model size",
    )
    parser.add_argument("--flux-vae")
    parser.add_argument("--flux1-model")
    parser.add_argument("--flux1-clip")
    parser.add_argument("--flux1-t5")
    parser.add_argument("--flux1-vae")
    parser.add_argument("--flux1-controlnet")
    parser.add_argument("--flux1-steps", type=int)
    parser.add_argument(
        "--flux1-guidance",
        type=float,
    )
    parser.add_argument(
        "--flux1-control-strength",
        type=float,
    )
    parser.add_argument(
        "--flux1-canny-low",
        type=float,
    )
    parser.add_argument(
        "--flux1-canny-high",
        type=float,
    )
    parser.add_argument("--qwen-model")
    parser.add_argument("--qwen-clip")
    parser.add_argument("--qwen-vae")
    parser.add_argument("--qwen-lora")
    parser.add_argument("--qwen-steps", type=int)
    parser.add_argument("--qwen-cfg", type=float)
    parser.add_argument("--qwen-shift", type=float)
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
    upscale_model = str(
        args.upscale_model
        or configured.get("upscale_model", DEFAULT_UPSCALE_MODEL)
    )
    if selected_engine == "both":
        engines = ("flux", "anima")
    elif selected_engine == "all":
        engines = ENGINES
    else:
        engines = (selected_engine,)
    for engine in engines:
        resolved = resolve_generation_options(
            engine,
            configured,
            vars(args),
        )
        output_megapixels = args.output_megapixels
        output_dpi = args.output_dpi
        if output_megapixels is None and output_dpi is None:
            if is_joint_scene_generation(resolved.metadata):
                if (
                    configured.get("output_method") == "lanczos"
                    and configured.get("output_megapixels") is not None
                    and configured.get("output_dpi") is None
                ):
                    output_megapixels = float(
                        configured.get("output_megapixels", megapixels)
                    )
                else:
                    output_dpi = int(
                        configured.get("output_dpi")
                        or DEFAULT_OUTPUT_DPI
                    )
            elif configured.get("output_method") == "lanczos":
                output_megapixels = float(
                    configured.get("output_megapixels", megapixels)
                )
            else:
                output_dpi = int(
                    configured.get("output_dpi", DEFAULT_OUTPUT_DPI)
                )
        raw_path, artwork_path, final_path, run_metadata_path = run(
            args.scope,
            seed,
            megapixels,
            args.server,
            args.timeout,
            args.language,
            engine=engine,
            **resolved.workflow_options,
            output_megapixels=output_megapixels,
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
