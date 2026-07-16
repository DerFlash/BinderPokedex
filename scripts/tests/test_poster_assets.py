from pathlib import Path

from PIL import Image, ImageChops

from scripts.poster_assets import fetch_cutouts
from scripts.poster_assets.create_comfyui_poster_workflow import build_workflow
from scripts.poster_assets.create_anima_poster_workflow import build_workflow as build_anima_workflow
from scripts.poster_assets.finalize_comfyui_poster import finalize
from scripts.poster_assets.layout import build_page_layout
from scripts.poster_assets.render_poster import cutout_placements
from scripts.poster_assets.run_comfyui_poster import write_engine_workflow


def test_auto_count_uses_layout_columns():
    manifest = {"pokemon": {"count": "auto_from_layout_columns"}}
    assert fetch_cutouts.resolve_requested_count(manifest, build_page_layout("wide_4x3")) == 4


def test_select_pokemon_uses_fallback_candidates():
    manifest = {
        "pokemon": {
            "strategy": "featured_from_scope",
            "fallback_candidates": [{"pokemon_id": 25}],
        }
    }
    scope_data = {
        "sections": {
            "all": {
                "featured_elements": [
                    {"pokemon_id": 150, "pokemon_name": "Mewtwo"},
                    {"pokemon_id": 1, "pokemon_name": "Bulbasaur"},
                    {"pokemon_id": 4, "pokemon_name": "Charmander"},
                ]
            }
        }
    }
    names = {25: {"en": "Pikachu", "de": "Pikachu"}}

    selected = fetch_cutouts.select_pokemon(manifest, scope_data, 4, names)

    assert [item["pokemon_id"] for item in selected] == [150, 1, 4, 25]


def test_validate_png_requires_transparency(tmp_path: Path):
    transparent = tmp_path / "transparent.png"
    img = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    for x in range(100, 300):
        for y in range(100, 300):
            img.putpixel((x, y), (255, 0, 0, 255))
    img.save(transparent)

    validation = fetch_cutouts.validate_png(transparent)

    assert validation["validated_alpha"] is True
    assert validation["alpha_min"] == 0
    assert validation["alpha_max"] == 255


def test_validate_png_rejects_flattened_image(tmp_path: Path):
    flattened = tmp_path / "flattened.png"
    Image.new("RGBA", (400, 400), (255, 255, 255, 255)).save(flattened)

    validation = fetch_cutouts.validate_png(flattened)

    assert validation["validated_alpha"] is False
    assert "image has no transparent pixels" in validation["errors"]


def test_cutout_placements_share_one_foot_baseline():
    scope_dir = Path(__file__).resolve().parents[2] / "data" / "poster_assets" / "Base1"
    placements = cutout_placements(build_page_layout("standard_3x3"), scope_dir)

    foot_positions = []
    for placement in placements:
        alpha_box = placement["image"].getchannel("A").getbbox()
        assert alpha_box is not None
        foot_positions.append(placement["y"] + alpha_box[3])

    assert len(set(foot_positions)) == 1


def test_comfyui_inpaint_uses_source_once_without_reference_conditioning():
    workflow = build_workflow(
        "Base1", seed=123, megapixels=0.25, generation_mode="inpaint"
    )
    loaded_images = {
        node["inputs"]["image"]
        for node in workflow.values()
        if node["class_type"] == "LoadImage"
    }

    assert loaded_images == {"scene_reference.png"}
    assert not any(node["class_type"] == "ReferenceLatent" for node in workflow.values())
    assert any(node["class_type"] == "VAEEncodeForInpaint" for node in workflow.values())
    assert not any(node["class_type"] == "ImageCompositeMasked" for node in workflow.values())
    assert workflow["9"]["inputs"]["positive"] == ["4", 0]


def test_comfyui_edit_uses_reference_with_independent_empty_target():
    workflow = build_workflow(
        "Base1",
        seed=123,
        megapixels=0.25,
        generation_mode="edit",
        reference_mode="composition",
    )

    assert workflow["15"]["class_type"] == "EmptySD3LatentImage"
    assert workflow["16"]["class_type"] == "VAEEncode"
    assert workflow["17"]["class_type"] == "ReferenceLatent"
    assert workflow["17"]["inputs"]["latent"] == ["16", 0]
    assert workflow["11"]["inputs"]["latent_image"] == ["15", 0]
    assert not any(node["class_type"] == "VAEEncodeForInpaint" for node in workflow.values())
    assert not any(node["class_type"] == "ImageCompositeMasked" for node in workflow.values())


def test_comfyui_identity_mode_appends_three_identity_references():
    workflow = build_workflow(
        "Base1",
        seed=123,
        megapixels=0.25,
        generation_mode="edit",
        reference_mode="identity",
    )

    loaded_images = [
        node["inputs"]["image"]
        for node in workflow.values()
        if node["class_type"] == "LoadImage"
    ]
    assert loaded_images == [
        "scene_reference.png",
        "identity_reference_1.png",
        "identity_reference_2.png",
        "identity_reference_3.png",
    ]
    assert sum(
        node["class_type"] == "ReferenceLatent" for node in workflow.values()
    ) == 4


def test_anima_workflow_uses_cosmos_reference_without_changing_flux_workflow():
    workflow = build_anima_workflow("Base1", seed=123, megapixels=0.25)
    assert any(node["class_type"] == "ApplyCosmosReferenceLatent" for node in workflow.values())
    assert any(node["class_type"] == "LoraLoaderModelOnly" for node in workflow.values())
    assert any(node["class_type"] == "ImageCompositeMasked" for node in workflow.values())
    assert {node["inputs"]["image"] for node in workflow.values() if node["class_type"] == "LoadImage"} == {"scene_reference.png"}
    sampler = next(node for node in workflow.values() if node["class_type"] == "KSampler")
    assert sampler["inputs"]["latent_image"] == ["10", 0]


def test_engine_workflows_have_separate_files():
    flux = write_engine_workflow("flux", "Base1", 123, 0.25)
    anima = write_engine_workflow("anima", "Base1", 123, 0.25)
    assert flux.name == "workflow_api_edit_0p25mp_123.json"
    assert anima.name == "anima_workflow_api.json"


def test_flux_workflow_files_are_unique_per_seed():
    first = write_engine_workflow("flux", "Base1", 123, 0.25)
    second = write_engine_workflow("flux", "Base1", 124, 0.25)
    full_size = write_engine_workflow("flux", "Base1", 123, 1.0)

    assert first != second
    assert first != full_size


def test_flux_model_and_steps_are_selectable():
    workflow = build_workflow(
        "Base1",
        seed=123,
        megapixels=0.25,
        unet_name="flux-2-klein-base-4b-fp8.safetensors",
        generation_mode="inpaint",
        steps=24,
        clip_name="qwen_3_8b_fp4mixed.safetensors",
    )

    assert workflow["1"]["inputs"]["unet_name"] == "flux-2-klein-base-4b-fp8.safetensors"
    assert workflow["7"]["inputs"]["steps"] == 24
    assert workflow["2"]["inputs"]["clip_name"] == "qwen_3_8b_fp4mixed.safetensors"


def test_finalizer_preserves_size_and_adds_deterministic_panels(tmp_path: Path):
    raw_path = tmp_path / "raw.png"
    final_path = tmp_path / "final.png"
    Image.new("RGB", (432, 608), (80, 140, 90)).save(raw_path)

    finalize("Base1", raw_path, final_path)

    raw = Image.open(raw_path).convert("RGB")
    final = Image.open(final_path).convert("RGB")
    assert final.size == raw.size
    assert ImageChops.difference(raw, final).getbbox() is not None
    # The lower character area belongs exclusively to the generated artwork.
    assert final.getpixel((raw.width // 4, raw.height * 5 // 6)) == raw.getpixel(
        (raw.width // 4, raw.height * 5 // 6)
    )
