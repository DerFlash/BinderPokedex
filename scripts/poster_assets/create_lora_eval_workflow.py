#!/usr/bin/env python3
"""Add one model-only LoRA to an existing ComfyUI API workflow."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


def _single_node_id(workflow: dict[str, Any], class_type: str) -> str:
    matches = [
        node_id
        for node_id, node in workflow.items()
        if node.get("class_type") == class_type
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one {class_type} node, found {len(matches)}"
        )
    return matches[0]


def _next_node_id(workflow: dict[str, Any]) -> str:
    numeric_ids = [int(node_id) for node_id in workflow if node_id.isdigit()]
    return str(max(numeric_ids, default=0) + 1)


def build_lora_eval_workflow(
    workflow: dict[str, Any],
    *,
    lora_name: str,
    strength: float,
    filename_prefix: str,
) -> dict[str, Any]:
    """Return a copy with one model-only LoRA inserted before the guider."""
    if not lora_name.strip():
        raise ValueError("lora_name must not be empty")
    if strength <= 0:
        raise ValueError("strength must be positive")
    if not filename_prefix.strip():
        raise ValueError("filename_prefix must not be empty")

    patched = copy.deepcopy(workflow)
    model_id = _single_node_id(patched, "UNETLoader")
    guider_id = _single_node_id(patched, "CFGGuider")
    save_id = _single_node_id(patched, "SaveImage")

    guider_inputs = patched[guider_id].get("inputs", {})
    if guider_inputs.get("model") != [model_id, 0]:
        raise ValueError("CFGGuider does not consume the single UNETLoader")

    lora_id = _next_node_id(patched)
    patched[lora_id] = {
        "class_type": "LoraLoaderModelOnly",
        "inputs": {
            "lora_name": lora_name,
            "model": [model_id, 0],
            "strength_model": strength,
        },
    }
    guider_inputs["model"] = [lora_id, 0]
    patched[save_id]["inputs"]["filename_prefix"] = filename_prefix
    return patched


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lora-name", required=True)
    parser.add_argument("--strength", type=float, required=True)
    parser.add_argument("--filename-prefix", required=True)
    args = parser.parse_args()

    workflow = json.loads(args.workflow.read_text(encoding="utf-8"))
    patched = build_lora_eval_workflow(
        workflow,
        lora_name=args.lora_name,
        strength=args.strength,
        filename_prefix=args.filename_prefix,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(patched, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
