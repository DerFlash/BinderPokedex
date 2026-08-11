#!/usr/bin/env python3
"""Patch comfy-kitchen so FP8 checkpoints can be dequantized for Apple MPS.

MPS can store FP8 tensors but cannot cast them directly. Preserve the raw bytes,
perform the dtype conversion on CPU, and return the converted tensor to MPS.
"""

from __future__ import annotations

import argparse
import py_compile
import shutil
from pathlib import Path


OLD = """def dequantize_per_tensor_fp8(
    x: torch.Tensor, scale: torch.Tensor, output_type: torch.dtype = torch.bfloat16
) -> torch.Tensor:
    dq_tensor = x.to(dtype=output_type) * scale.to(dtype=output_type)
    return dq_tensor
"""

NEW = """def dequantize_per_tensor_fp8(
    x: torch.Tensor, scale: torch.Tensor, output_type: torch.dtype = torch.bfloat16
) -> torch.Tensor:
    # Apple MPS can store FP8 values but cannot cast FP8 directly. Move the raw
    # bytes to CPU, restore the FP8 view there, dequantize, then return the
    # supported output dtype to MPS. Model operations still execute on Metal.
    if x.device.type == \"mps\" and x.dtype in (torch.float8_e4m3fn, torch.float8_e5m2):
        target_device = x.device
        cpu_x = x.view(torch.uint8).cpu().view(x.dtype)
        cpu_scale = scale.cpu()
        return (cpu_x.to(dtype=output_type) * cpu_scale.to(dtype=output_type)).to(target_device)

    dq_tensor = x.to(dtype=output_type) * scale.to(dtype=output_type)
    return dq_tensor
"""

MM_OLD = """def text_encoder_device():
    if args.gpu_only:
        return get_torch_device()
    elif vram_state in (VRAMState.HIGH_VRAM, VRAMState.NORMAL_VRAM) or comfy.memory_management.aimdo_enabled:
"""

MM_NEW = """def text_encoder_device():
    if args.gpu_only:
        return get_torch_device()
    # MPS uses unified memory. Execute text encoding on Metal, while retaining
    # CPU as the offload target so the diffusion model still has working room.
    elif get_torch_device().type == \"mps\":
        return get_torch_device()
    elif vram_state in (VRAMState.HIGH_VRAM, VRAMState.NORMAL_VRAM) or comfy.memory_management.aimdo_enabled:
"""

NVFP4_OLD = """    @classmethod
    def dequantize(cls, qdata: torch.Tensor, params: Params) -> torch.Tensor:
        return ck.dequantize_nvfp4(qdata, params.scale, params.block_scale, params.orig_dtype)
"""

NVFP4_NEW = """    @classmethod
    def dequantize(cls, qdata: torch.Tensor, params: Params) -> torch.Tensor:
        # MPS cannot operate on the FP8 block-scale dtype used by NVFP4. Move
        # the packed raw bytes to CPU without asking MPS to cast FP8, perform
        # dequantization there, then return the supported output dtype to Metal.
        if qdata.device.type == \"mps\":
            target_device = qdata.device
            cpu_qdata = qdata.cpu()
            block_dtype = params.block_scale.dtype
            cpu_block_scale = params.block_scale.view(torch.uint8).cpu().view(block_dtype)
            cpu_scale = params.scale.cpu()
            return ck.dequantize_nvfp4(
                cpu_qdata, cpu_scale, cpu_block_scale, params.orig_dtype
            ).to(target_device)
        return ck.dequantize_nvfp4(qdata, params.scale, params.block_scale, params.orig_dtype)
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("quantization_py", type=Path)
    parser.add_argument("--model-management-py", type=Path)
    parser.add_argument("--nvfp4-py", type=Path)
    args = parser.parse_args()
    path = args.quantization_py.resolve()
    source = path.read_text()

    if NEW in source:
        print(f"Already patched: {path}")
    elif source.count(OLD) != 1:
        raise SystemExit(f"Expected function body not found exactly once: {path}")
    else:
        backup = path.with_suffix(path.suffix + ".pre-mps-fp8")
        if not backup.exists():
            shutil.copy2(path, backup)
        path.write_text(source.replace(OLD, NEW))
        py_compile.compile(str(path), doraise=True)
        print(f"Patched: {path}")
        print(f"Backup:  {backup}")

    if args.model_management_py:
        mm_path = args.model_management_py.resolve()
        mm_source = mm_path.read_text()
        if MM_NEW in mm_source:
            print(f"Already patched: {mm_path}")
            pass
        else:
            if mm_source.count(MM_OLD) != 1:
                raise SystemExit(f"Expected text encoder function not found exactly once: {mm_path}")
            mm_backup = mm_path.with_suffix(mm_path.suffix + ".pre-mps-text-encoder")
            if not mm_backup.exists():
                shutil.copy2(mm_path, mm_backup)
            mm_path.write_text(mm_source.replace(MM_OLD, MM_NEW))
            py_compile.compile(str(mm_path), doraise=True)
            print(f"Patched: {mm_path}")
            print(f"Backup:  {mm_backup}")

    if args.nvfp4_py:
        nvfp4_path = args.nvfp4_py.resolve()
        nvfp4_source = nvfp4_path.read_text()
        if NVFP4_NEW in nvfp4_source:
            print(f"Already patched: {nvfp4_path}")
        elif nvfp4_source.count(NVFP4_OLD) != 1:
            raise SystemExit(f"Expected NVFP4 function not found exactly once: {nvfp4_path}")
        else:
            nvfp4_backup = nvfp4_path.with_suffix(nvfp4_path.suffix + ".pre-mps-nvfp4")
            if not nvfp4_backup.exists():
                shutil.copy2(nvfp4_path, nvfp4_backup)
            nvfp4_path.write_text(nvfp4_source.replace(NVFP4_OLD, NVFP4_NEW))
            py_compile.compile(str(nvfp4_path), doraise=True)
            print(f"Patched: {nvfp4_path}")
            print(f"Backup:  {nvfp4_backup}")


if __name__ == "__main__":
    main()
