from __future__ import annotations

import pytest

from scripts.poster_assets.create_lora_eval_workflow import (
    build_lora_eval_workflow,
)


def base_workflow() -> dict:
    return {
        "1": {"class_type": "UNETLoader", "inputs": {}},
        "70": {
            "class_type": "CFGGuider",
            "inputs": {"model": ["1", 0]},
        },
        "73": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": "before"},
        },
    }


def test_build_lora_eval_workflow_changes_only_model_route_and_prefix() -> None:
    source = base_workflow()

    result = build_lora_eval_workflow(
        source,
        lora_name="integration.safetensors",
        strength=0.9,
        filename_prefix="holdout_strength_0p9",
    )

    assert source["70"]["inputs"]["model"] == ["1", 0]
    assert result["74"] == {
        "class_type": "LoraLoaderModelOnly",
        "inputs": {
            "lora_name": "integration.safetensors",
            "model": ["1", 0],
            "strength_model": 0.9,
        },
    }
    assert result["70"]["inputs"]["model"] == ["74", 0]
    assert result["73"]["inputs"]["filename_prefix"] == (
        "holdout_strength_0p9"
    )


@pytest.mark.parametrize("strength", [0, -0.1])
def test_build_lora_eval_workflow_rejects_non_positive_strength(
    strength: float,
) -> None:
    with pytest.raises(ValueError, match="strength must be positive"):
        build_lora_eval_workflow(
            base_workflow(),
            lora_name="integration.safetensors",
            strength=strength,
            filename_prefix="holdout",
        )


def test_build_lora_eval_workflow_requires_direct_unet_route() -> None:
    workflow = base_workflow()
    workflow["70"]["inputs"]["model"] = ["99", 0]

    with pytest.raises(ValueError, match="does not consume"):
        build_lora_eval_workflow(
            workflow,
            lora_name="integration.safetensors",
            strength=1.0,
            filename_prefix="holdout",
        )
