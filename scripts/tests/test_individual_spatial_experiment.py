from scripts.poster_assets.experiment_individual_spatial_joint import (
    build_individual_spatial_prompt,
    build_workflow,
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
