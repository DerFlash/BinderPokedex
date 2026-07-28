#!/usr/bin/env python3
"""Patch the pinned DreamO sampler wrapper for current ComfyUI keywords."""
from __future__ import annotations

import argparse
import py_compile
import shutil
from pathlib import Path


OLD = """def dreamo_outer_sample_wrappers_with_override(wrapper_executor, noise, latent_image, sampler, sigmas, denoise_mask=None, callback=None, disable_pbar=False, seed=None):
    cfg_guider = wrapper_executor.class_obj
    diffusion_model = cfg_guider.model_patcher.model.diffusion_model
    set_hook(diffusion_model, dreamo_forward_orig, dreamo_forward)
    try :
        out = wrapper_executor(noise, latent_image, sampler, sigmas, denoise_mask, callback, disable_pbar, seed)
    finally:
        clean_hook(diffusion_model)

    return out
"""

NEW = """def dreamo_outer_sample_wrappers_with_override(wrapper_executor, noise, latent_image, sampler, sigmas, denoise_mask=None, callback=None, disable_pbar=False, seed=None, **kwargs):
    cfg_guider = wrapper_executor.class_obj
    diffusion_model = cfg_guider.model_patcher.model.diffusion_model
    set_hook(diffusion_model, dreamo_forward_orig, dreamo_forward)
    try :
        out = wrapper_executor(noise, latent_image, sampler, sigmas, denoise_mask, callback, disable_pbar, seed, **kwargs)
    finally:
        clean_hook(diffusion_model)

    return out
"""


def patch(path: Path) -> bool:
    """Apply the keyword-forwarding patch once and compile the result."""
    path = path.resolve()
    source = path.read_text(encoding="utf-8")
    if NEW in source:
        return False
    if source.count(OLD) != 1:
        raise RuntimeError(
            f"Expected DreamO wrapper not found exactly once: {path}"
        )

    backup = path.with_suffix(path.suffix + ".pre-comfy-0.28")
    if not backup.exists():
        shutil.copy2(path, backup)
    path.write_text(source.replace(OLD, NEW), encoding="utf-8")
    py_compile.compile(str(path), doraise=True)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dreamo_py", type=Path)
    args = parser.parse_args()
    changed = patch(args.dreamo_py)
    action = "Patched" if changed else "Already patched"
    print(f"{action}: {args.dreamo_py.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
