from PIL import Image, ImageChops

from scripts.poster_assets.create_comfyui_poster_workflow import (
    build_individual_spatial_prompt,
    build_workflow,
    output_dimensions,
)
from scripts.poster_assets.prepare_comfyui_poster import (
    build_individual_spatial_joint_references,
)


SCOPE = "Pokedex/sections/gen1"


def test_individual_spatial_prompt_assigns_one_identity_position_image_per_subject():
    prompt = build_individual_spatial_prompt(SCOPE, megapixels=0.25)

    assert "IMAGE 1 is the sole poster-shaped identity and position reference for Bulbasaur" in prompt
    assert "IMAGE 2 is the sole poster-shaped identity and position reference for Charmander" in prompt
    assert "IMAGE 3 is the sole poster-shaped identity and position reference for Squirtle" in prompt
    assert "render exactly these 3 characters once each" in prompt
    assert "unscaled identity" not in prompt
    assert "sole spatial cast-layout reference" not in prompt
    assert "No supplied landscape image" not in prompt
    assert "There is no supplied landscape image" in prompt


def test_individual_spatial_workflow_has_one_full_frame_sampler_without_regions():
    workflow = build_workflow(
        SCOPE,
        seed=260782266,
        megapixels=0.25,
        generation_mode="joint_scene",
        reference_mode="individual_spatial_joint",
    )

    assert [
        node["inputs"]["image"]
        for node in workflow.values()
        if node["class_type"] == "LoadImage"
    ] == [
        "individual_spatial_reference_1.png",
        "individual_spatial_reference_2.png",
        "individual_spatial_reference_3.png",
    ]
    assert workflow["6"]["inputs"] == {
        "width": 432,
        "height": 592,
        "batch_size": 1,
    }
    assert sum(
        node["class_type"] == "ReferenceLatent"
        for node in workflow.values()
    ) == 6
    assert sum(
        node["class_type"] == "SamplerCustomAdvanced"
        for node in workflow.values()
    ) == 1
    assert sum(
        node["class_type"] == "VAEDecode"
        for node in workflow.values()
    ) == 1
    assert not any(
        node["class_type"]
        in {
            "ConditioningSetAreaPercentage",
            "ConditioningSetDefaultCombine",
            "ConditioningSetMask",
            "ImageCompositeMasked",
            "VAEEncodeForInpaint",
        }
        for node in workflow.values()
    )


def test_flux2_dev_uses_official_positive_reference_guider_profile():
    workflow = build_workflow(
        SCOPE,
        seed=260782266,
        megapixels=0.25,
        generation_mode="joint_scene",
        reference_mode="individual_spatial_joint",
        unet_name="flux2_dev_fp8mixed.safetensors",
        clip_name="mistral_3_small_flux2_bf16.safetensors",
        steps=20,
    )

    assert workflow["7"]["inputs"]["steps"] == 20
    assert workflow["60"] == {
        "class_type": "FluxGuidance",
        "inputs": {"conditioning": ["4", 0], "guidance": 4.0},
    }
    assert workflow["70"] == {
        "class_type": "BasicGuider",
        "inputs": {"model": ["1", 0], "conditioning": ["40", 0]},
    }
    assert sum(
        node["class_type"] == "ReferenceLatent"
        for node in workflow.values()
    ) == 3
    assert not any(
        node["class_type"] in {"CFGGuider", "ConditioningZeroOut"}
        for node in workflow.values()
    )


def test_production_reference_writer_emits_one_positioned_identity_per_subject(
    tmp_path,
):
    paths = build_individual_spatial_joint_references(SCOPE, tmp_path)

    assert [path.name for path in paths] == [
        "individual_spatial_reference_1.png",
        "individual_spatial_reference_2.png",
        "individual_spatial_reference_3.png",
    ]
    expected_size = output_dimensions(SCOPE, 0.5)
    neutral = Image.new("RGB", expected_size, (226, 224, 211))
    for path in paths:
        with Image.open(path) as loaded:
            reference = loaded.convert("RGB")
        assert reference.size == expected_size
        assert reference.getpixel((0, 0)) == (226, 224, 211)
        assert ImageChops.difference(reference, neutral).getbbox() is not None
