#!/usr/bin/env python3
"""Upscale a reviewed text-free poster to its exact physical print resolution."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from PIL import Image, ImageStat

try:
    from .create_comfyui_upscale_workflow import (
        DEFAULT_UPSCALE_MODEL,
        write_workflow,
    )
    from .layout import build_page_layout, build_print_layout
    from .queue_comfyui_workflow import (
        queue_workflow,
        validate_server_input_directory,
    )
    from .poster_io import poster_asset_slug, poster_bundle
except ImportError:
    from create_comfyui_upscale_workflow import (
        DEFAULT_UPSCALE_MODEL,
        write_workflow,
    )
    from layout import build_page_layout, build_print_layout
    from queue_comfyui_workflow import (
        queue_workflow,
        validate_server_input_directory,
    )
    from poster_io import poster_asset_slug, poster_bundle


ROOT = Path(__file__).resolve().parents[2]
POSTER_ASSETS = ROOT / "data" / "poster_assets"


def safe_marker(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value).strip("._") or "poster"


def normalize_upscale_input(
    scope: str,
    source: Path,
    destination: Path,
) -> Path:
    """Normalize latent rounding to the exact physical aspect ratio."""
    manifest = poster_bundle(
        scope,
        poster_assets=POSTER_ASSETS,
    ).manifest
    image = Image.open(source).convert("RGB")
    layout = build_page_layout(
        manifest.get("layout", {}).get("name", "standard_3x3"),
        width_px=image.width,
    )
    if image.size != (layout.width_px, layout.height_px):
        image = image.resize(
            (layout.width_px, layout.height_px),
            Image.Resampling.LANCZOS,
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, format="PNG", optimize=True)
    return destination


def validate_upscaled_artwork(
    scope: str,
    path: Path,
    dpi: int,
) -> None:
    manifest = poster_bundle(
        scope,
        poster_assets=POSTER_ASSETS,
    ).manifest
    expected = build_print_layout(
        manifest.get("layout", {}).get("name", "standard_3x3"),
        dpi,
    )
    image = Image.open(path).convert("RGB")
    if image.size != (expected.width_px, expected.height_px):
        raise ValueError(
            f"Upscaler returned {image.size}; expected "
            f"{(expected.width_px, expected.height_px)} at {dpi} dpi"
        )
    if max(ImageStat.Stat(image).stddev) < 2.0:
        raise RuntimeError(f"Upscaler produced blank or near-constant artwork: {path}")


def stamp_print_dpi(source: Path, destination: Path, dpi: int) -> Path:
    """Persist explicit physical-resolution metadata on a validated PNG."""
    image = Image.open(source).convert("RGB")
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(
        destination,
        format="PNG",
        optimize=True,
        dpi=(dpi, dpi),
    )
    return destination


def upscale(
    scope: str,
    source: Path,
    *,
    server: str = "http://127.0.0.1:8188",
    timeout: int = 1800,
    dpi: int = 300,
    model_name: str = DEFAULT_UPSCALE_MODEL,
) -> tuple[Path, Path]:
    if not source.is_file():
        raise FileNotFoundError(source)
    scope_dir = poster_bundle(
        scope,
        poster_assets=POSTER_ASSETS,
    ).asset_dir
    work_dir = scope_dir / "comfyui_poster"
    work_dir.mkdir(parents=True, exist_ok=True)
    validate_server_input_directory(server, work_dir)

    input_name = (
        f"temp/upscale_input_{safe_marker(source.stem)}_{dpi}dpi.png"
    )
    normalized_input = normalize_upscale_input(
        scope,
        source,
        work_dir / input_name,
    )
    prefix = (
        f"{poster_asset_slug(scope)}_print_{dpi}dpi_"
        f"{safe_marker(Path(model_name).stem)}"
    )
    workflow_path = write_workflow(
        scope,
        input_name,
        dpi=dpi,
        model_name=model_name,
        filename_prefix=prefix,
    )
    outputs = queue_workflow(workflow_path, server=server, timeout=timeout)
    images = [
        item
        for item in outputs
        if item.get("type") == "output" and item.get("filename")
    ]
    if len(images) != 1:
        raise RuntimeError(f"Expected exactly one upscaled image, got: {outputs}")
    output = images[0]
    result = (
        work_dir
        / "output"
        / str(output.get("subfolder", ""))
        / str(output["filename"])
    )
    if not result.is_file():
        raise FileNotFoundError(
            f"ComfyUI reported an upscale output that does not exist: {result}"
        )
    validate_upscaled_artwork(scope, result, dpi)
    print_artwork = stamp_print_dpi(
        result,
        work_dir / "temp" / f"{result.stem}_print.png",
        dpi,
    )
    return print_artwork, workflow_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--server", default="http://127.0.0.1:8188")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--model", default=DEFAULT_UPSCALE_MODEL)
    args = parser.parse_args()
    result, workflow = upscale(
        args.scope,
        args.input,
        server=args.server,
        timeout=args.timeout,
        dpi=args.dpi,
        model_name=args.model,
    )
    print(f"Upscaled artwork: {result}")
    print(f"Workflow: {workflow}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
