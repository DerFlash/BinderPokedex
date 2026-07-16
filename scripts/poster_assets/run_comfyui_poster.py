#!/usr/bin/env python3
"""Run the complete local ComfyUI poster pipeline against a running server."""
from __future__ import annotations

import argparse
from pathlib import Path

try:
    from .create_anima_poster_workflow import write_workflow as write_anima_workflow
    from .create_comfyui_poster_workflow import write_workflow as write_flux_workflow
    from .finalize_comfyui_poster import finalize
    from .prepare_comfyui_poster import prepare
    from .queue_comfyui_workflow import queue_workflow
except ImportError:
    from create_anima_poster_workflow import write_workflow as write_anima_workflow
    from create_comfyui_poster_workflow import write_workflow as write_flux_workflow
    from finalize_comfyui_poster import finalize
    from prepare_comfyui_poster import prepare
    from queue_comfyui_workflow import queue_workflow


ENGINES = ("flux", "anima")


def write_engine_workflow(
    engine: str,
    scope: str,
    seed: int,
    megapixels: float,
    reference_strength: float = 1.0,
    anima_model: str = "AnimaYume_tuned_v05.safetensors",
    anima_mode: str = "generate",
) -> Path:
    if engine == "flux":
        return write_flux_workflow(scope, seed, megapixels)
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
) -> tuple[Path, Path]:
    work_dir = prepare(scope, megapixels)
    workflow_path = write_engine_workflow(
        engine, scope, seed, megapixels, reference_strength, anima_model, anima_mode
    )
    outputs = queue_workflow(workflow_path, server=server, timeout=timeout)
    images = [item for item in outputs if item.get("type") == "output" and item.get("filename")]
    if len(images) != 1:
        raise RuntimeError(f"Expected exactly one output image, got: {outputs}")

    raw_path = work_dir / "output" / str(images[0]["filename"])
    if not raw_path.is_file():
        raise FileNotFoundError(f"ComfyUI reported an output that does not exist: {raw_path}")
    final_path = (
        work_dir
        / "output"
        / f"{scope.lower()}_{engine}_poster_{language}_seed_{seed}_final.png"
    )
    finalize(scope, raw_path, final_path, language)
    return raw_path, final_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", default="Base1")
    parser.add_argument("--seed", type=int, default=260715201)
    parser.add_argument("--megapixels", type=float, default=1.0)
    parser.add_argument("--server", default="http://127.0.0.1:8188")
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--language", choices=("de", "en", "fr", "es", "it"), default="en")
    parser.add_argument("--engine", choices=(*ENGINES, "both"), default="flux")
    parser.add_argument("--reference-strength", type=float, default=1.0, help="AnimaEdit LoRA strength; ignored by FLUX")
    parser.add_argument("--anima-model", default="AnimaYume_tuned_v05.safetensors", help="Anima-compatible diffusion model; ignored by FLUX")
    parser.add_argument("--anima-mode", choices=("generate", "edit"), default="generate", help="Generate from an empty target or edit the abstract material scaffold")
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
        )
        print(f"[{engine}] Raw artwork: {raw_path}")
        print(f"[{engine}] Final poster: {final_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
