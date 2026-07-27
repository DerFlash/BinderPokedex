from pathlib import Path

import pytest

from scripts.poster_assets.create_anima_poster_workflow import (
    DEFAULT_CFG,
    DEFAULT_ENCODER,
    DEFAULT_LORA,
    DEFAULT_MODEL,
    DEFAULT_REFERENCE_STRENGTH,
    DEFAULT_STEPS,
    DEFAULT_VAE,
    build_workflow,
    write_workflow,
)


def test_anima_defaults_are_bound_to_the_workflow():
    workflow = build_workflow("Base1", seed=123, megapixels=0.25)

    assert workflow["1"]["inputs"]["unet_name"] == DEFAULT_MODEL
    assert workflow["2"]["inputs"] == {
        "model": ["1", 0],
        "lora_name": DEFAULT_LORA,
        "strength_model": DEFAULT_REFERENCE_STRENGTH,
    }
    assert workflow["3"]["inputs"]["clip_name"] == DEFAULT_ENCODER
    assert workflow["4"]["inputs"]["vae_name"] == DEFAULT_VAE
    assert workflow["11"]["inputs"]["steps"] == DEFAULT_STEPS
    assert workflow["11"]["inputs"]["cfg"] == DEFAULT_CFG


def test_anima_generation_contract_is_fully_parameterized():
    workflow = build_workflow(
        "Base1",
        seed=456,
        megapixels=0.5,
        model_name="custom-model.safetensors",
        lora_name="custom-lora.safetensors",
        encoder_name="custom-encoder.safetensors",
        vae_name="custom-vae.safetensors",
        steps=17,
        cfg=2.75,
        reference_strength=0.65,
        generation_mode="edit",
    )

    assert workflow["1"]["inputs"]["unet_name"] == "custom-model.safetensors"
    assert workflow["2"]["inputs"]["lora_name"] == "custom-lora.safetensors"
    assert workflow["2"]["inputs"]["strength_model"] == 0.65
    assert workflow["3"]["inputs"]["clip_name"] == "custom-encoder.safetensors"
    assert workflow["4"]["inputs"]["vae_name"] == "custom-vae.safetensors"
    assert workflow["7"]["inputs"]["image"] == "anima_scene_reference.png"
    assert workflow["11"]["inputs"]["latent_image"] == ["8", 0]
    assert workflow["11"]["inputs"]["steps"] == 17
    assert workflow["11"]["inputs"]["cfg"] == 2.75


@pytest.mark.parametrize(
    ("option", "value", "message"),
    [
        ("model_name", "", "model_name must not be empty"),
        ("lora_name", "  ", "lora_name must not be empty"),
        ("encoder_name", "", "encoder_name must not be empty"),
        ("vae_name", "", "vae_name must not be empty"),
        ("steps", 0, "steps must be positive"),
        ("cfg", 0, "cfg must be positive"),
        (
            "reference_strength",
            0,
            "reference_strength must be positive",
        ),
        (
            "generation_mode",
            "invalid",
            "Unsupported Anima generation mode",
        ),
    ],
)
def test_anima_generation_contract_rejects_invalid_values(
    option: str,
    value: object,
    message: str,
):
    with pytest.raises(ValueError, match=message):
        build_workflow(
            "Base1",
            seed=123,
            megapixels=0.25,
            **{option: value},
        )


def test_anima_workflow_files_are_unique_by_mode_size_and_seed(
    tmp_path: Path,
):
    generated = write_workflow(
        "Base1",
        123,
        0.25,
        output_dir=tmp_path,
    )
    edited = write_workflow(
        "Base1",
        123,
        0.25,
        DEFAULT_REFERENCE_STRENGTH,
        "edit_lora",
        DEFAULT_MODEL,
        "edit",
        tmp_path,
    )
    other_size = write_workflow(
        "Base1",
        123,
        1.0,
        output_dir=tmp_path,
    )
    other_seed = write_workflow(
        "Base1",
        124,
        0.25,
        output_dir=tmp_path,
    )

    assert generated.name == "anima_workflow_api_generate_0p25mp_123.json"
    assert edited.name == "anima_workflow_api_edit_0p25mp_123.json"
    assert other_size.name == "anima_workflow_api_generate_1mp_123.json"
    assert other_seed.name == "anima_workflow_api_generate_0p25mp_124.json"
    assert len({generated, edited, other_size, other_seed}) == 4
