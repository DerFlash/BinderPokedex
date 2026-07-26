#!/usr/bin/env python3
"""Create a model-based ComfyUI poster-upscale workflow."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .create_comfyui_poster_workflow import node
    from .layout import build_print_layout
    from .poster_io import load_yaml
except ImportError:
    from create_comfyui_poster_workflow import node
    from layout import build_print_layout
    from poster_io import load_yaml


ROOT = Path(__file__).resolve().parents[2]
POSTER_ASSETS = ROOT / "data" / "poster_assets"
DEFAULT_UPSCALE_MODEL = "RealESRGAN_x4plus_anime_6B.pth"


def build_workflow(
    scope: str,
    input_name: str,
    *,
    dpi: int = 300,
    model_name: str = DEFAULT_UPSCALE_MODEL,
    filename_prefix: str | None = None,
) -> dict[str, object]:
    scope_dir = POSTER_ASSETS / scope
    manifest = load_yaml(scope_dir / "poster.yaml")
    layout_name = manifest.get("layout", {}).get("name", "standard_3x3")
    layout = build_print_layout(layout_name, dpi)
    prefix = filename_prefix or f"{scope.lower()}_poster_{dpi}dpi"
    return {
        "1": node("LoadImage", image=input_name),
        "2": node("UpscaleModelLoader", model_name=model_name),
        "3": node(
            "ImageUpscaleWithModel",
            upscale_model=["2", 0],
            image=["1", 0],
        ),
        "4": node(
            "ImageScale",
            image=["3", 0],
            upscale_method="lanczos",
            width=layout.width_px,
            height=layout.height_px,
            crop="disabled",
        ),
        "5": node("SaveImage", images=["4", 0], filename_prefix=prefix),
    }


def write_workflow(
    scope: str,
    input_name: str,
    *,
    dpi: int = 300,
    model_name: str = DEFAULT_UPSCALE_MODEL,
    filename_prefix: str | None = None,
    output_dir: Path | None = None,
) -> Path:
    work_dir = POSTER_ASSETS / scope / "comfyui_poster"
    target_dir = output_dir or work_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    output = target_dir / f"workflow_api_upscale_{dpi}dpi.json"
    output.write_text(
        json.dumps(
            build_workflow(
                scope,
                input_name,
                dpi=dpi,
                model_name=model_name,
                filename_prefix=filename_prefix,
            ),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--input-name", required=True)
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--model", default=DEFAULT_UPSCALE_MODEL)
    parser.add_argument("--filename-prefix")
    args = parser.parse_args()
    print(
        write_workflow(
            args.scope,
            args.input_name,
            dpi=args.dpi,
            model_name=args.model,
            filename_prefix=args.filename_prefix,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
