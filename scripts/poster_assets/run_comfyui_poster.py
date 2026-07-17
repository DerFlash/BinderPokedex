#!/usr/bin/env python3
"""Run the complete local ComfyUI poster pipeline against a running server."""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageStat

try:
    from .create_anima_poster_workflow import write_workflow as write_anima_workflow
    from .create_comfyui_poster_workflow import megapixel_marker, page_dimensions, write_workflow as write_flux_workflow
    from .finalize_comfyui_poster import finalize
    from .prepare_comfyui_poster import prepare
    from .queue_comfyui_workflow import queue_workflow
    from .slice_poster import slice_poster
except ImportError:
    from create_anima_poster_workflow import write_workflow as write_anima_workflow
    from create_comfyui_poster_workflow import megapixel_marker, page_dimensions, write_workflow as write_flux_workflow
    from finalize_comfyui_poster import finalize
    from prepare_comfyui_poster import prepare
    from queue_comfyui_workflow import queue_workflow
    from slice_poster import slice_poster


ENGINES = ("flux", "anima")
DEFAULT_GENERATION_MEGAPIXELS = 0.25
DEFAULT_OUTPUT_MEGAPIXELS = 1.0


def validate_raw_artwork(path: Path) -> None:
    image = Image.open(path).convert("RGB")
    extrema = image.getextrema()
    variation = ImageStat.Stat(image).stddev
    if max(high for _low, high in extrema) < 12 or max(variation) < 2.0:
        raise RuntimeError(f"ComfyUI produced blank or near-constant artwork: {path}")


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
    reference_strength: float = 1.0,
    anima_model: str = "AnimaYume_tuned_v05.safetensors",
    anima_mode: str = "generate",
    flux_mode: str = "edit",
    flux_model: str = "flux-2-klein-4b-fp8.safetensors",
    flux_steps: int = 4,
    flux_reference_mode: str = "identity",
    flux_clip: str = "qwen_3_4b.safetensors",
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
        )
    if engine == "anima":
        return write_anima_workflow(
            scope,
            seed,
            megapixels,
            reference_strength,
            model_name=anima_model,
            generation_mode=anima_mode,
        )
    raise ValueError(f"Unsupported engine: {engine}")


def run(
    scope: str,
    seed: int,
    megapixels: float,
    server: str,
    timeout: int,
    language: str,
    engine: str = "flux",
    reference_strength: float = 1.0,
    anima_model: str = "AnimaYume_tuned_v05.safetensors",
    anima_mode: str = "generate",
    flux_mode: str = "edit",
    flux_model: str = "flux-2-klein-4b-fp8.safetensors",
    flux_steps: int = 4,
    flux_reference_mode: str = "identity",
    flux_clip: str = "qwen_3_4b.safetensors",
    output_megapixels: float | None = None,
) -> tuple[Path, Path]:
    work_dir = prepare(scope, megapixels)
    workflow_path = write_engine_workflow(
        engine,
        scope,
        seed,
        megapixels,
        reference_strength,
        anima_model,
        anima_mode,
        flux_mode,
        flux_model,
        flux_steps,
        flux_reference_mode,
        flux_clip,
    )
    outputs = queue_workflow(workflow_path, server=server, timeout=timeout)
    images = [item for item in outputs if item.get("type") == "output" and item.get("filename")]
    if len(images) != 1:
        raise RuntimeError(f"Expected exactly one output image, got: {outputs}")

    raw_path = work_dir / "output" / str(images[0]["filename"])
    if not raw_path.is_file():
        raise FileNotFoundError(f"ComfyUI reported an output that does not exist: {raw_path}")
    validate_raw_artwork(raw_path)
    final_megapixels = output_megapixels or megapixels
    if engine == "flux":
        if "9b" in flux_model.lower():
            model_variant = "distilled9b"
        elif "base-4b" in flux_model:
            model_variant = "base4b"
        else:
            model_variant = "distilled4b"
        run_marker = f"{flux_mode}_{flux_reference_mode}_{model_variant}_{flux_steps}step_{megapixel_marker(megapixels)}"
        if final_megapixels != megapixels:
            run_marker += f"_to_{megapixel_marker(final_megapixels)}"
    else:
        run_marker = anima_mode
    final_path = (
        work_dir
        / "output"
        / f"{scope.lower()}_{engine}_{run_marker}_poster_{language}_seed_{seed}_final.png"
    )
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
    return raw_path, final_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", default="Base1")
    parser.add_argument("--seed", type=int, default=260715201)
    parser.add_argument(
        "--megapixels", type=float, default=DEFAULT_GENERATION_MEGAPIXELS
    )
    parser.add_argument(
        "--output-megapixels",
        type=float,
        default=DEFAULT_OUTPUT_MEGAPIXELS,
        help="Upscale the complete generated artwork before deterministic typography",
    )
    parser.add_argument("--server", default="http://127.0.0.1:8188")
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--language", choices=("de", "en", "fr", "es", "it"), default="en")
    parser.add_argument("--engine", choices=(*ENGINES, "both"), default="flux")
    parser.add_argument("--reference-strength", type=float, default=1.0, help="AnimaEdit LoRA strength; ignored by FLUX")
    parser.add_argument("--anima-model", default="AnimaYume_tuned_v05.safetensors", help="Anima-compatible diffusion model; ignored by FLUX")
    parser.add_argument("--anima-mode", choices=("generate", "edit"), default="generate", help="Generate from an empty target or edit the abstract material scaffold")
    parser.add_argument("--flux-mode", choices=("edit", "inpaint"), default="edit", help="Use an independent reference edit or preserve figures as the inpaint source")
    parser.add_argument("--flux-model", default="flux-2-klein-4b-fp8.safetensors")
    parser.add_argument("--flux-steps", type=int, default=4, help="Use 4 for distilled Klein; typically 20-28 for Klein Base")
    parser.add_argument("--flux-reference-mode", choices=("composition", "identity"), default="identity", help="Append one identity close-up per character (recommended) or use only the scene composition")
    parser.add_argument("--flux-clip", default="qwen_3_4b.safetensors", help="FLUX.2 text encoder matching the selected model size")
    args = parser.parse_args()
    engines = ENGINES if args.engine == "both" else (args.engine,)
    for engine in engines:
        raw_path, final_path = run(
            args.scope,
            args.seed,
            args.megapixels,
            args.server,
            args.timeout,
            args.language,
            engine,
            args.reference_strength,
            args.anima_model,
            args.anima_mode,
            args.flux_mode,
            args.flux_model,
            args.flux_steps,
            args.flux_reference_mode,
            args.flux_clip,
            args.output_megapixels,
        )
        print(f"[{engine}] Raw artwork: {raw_path}")
        print(f"[{engine}] Final poster: {final_path}")
        print(f"[{engine}] Card slices: {final_path.with_name(f'{final_path.stem}_cards')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
