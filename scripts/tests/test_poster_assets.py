from pathlib import Path

from PIL import Image, ImageChops

from scripts.poster_assets import fetch_cutouts
from scripts.poster_assets.create_comfyui_poster_workflow import build_workflow
from scripts.poster_assets.create_anima_poster_workflow import build_workflow as build_anima_workflow
from scripts.poster_assets.finalize_comfyui_poster import finalize
from scripts.poster_assets.layout import build_page_layout
from scripts.poster_assets.prepare_comfyui_poster import (
    build_identity_references,
    card_safe_conditioning_placements,
)
from scripts.poster_assets.render_poster import cutout_placements
from scripts.poster_assets.run_comfyui_poster import resize_artwork, validate_raw_artwork, write_engine_workflow
from scripts.poster_assets.slice_poster import slice_poster


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


def test_cutout_placements_stay_inside_bottom_card_cells():
    scope_dir = Path(__file__).resolve().parents[2] / "data" / "poster_assets" / "Base1"
    placements = cutout_placements(build_page_layout("standard_3x3"), scope_dir)

    for placement in placements:
        alpha_box = placement["image"].getchannel("A").getbbox()
        assert alpha_box is not None
        left = placement["x"] + alpha_box[0]
        top = placement["y"] + alpha_box[1]
        right = placement["x"] + alpha_box[2]
        bottom = placement["y"] + alpha_box[3]
        cell = placement["cell"]
        assert cell.x <= left < right <= cell.x + cell.width
        assert cell.y <= top < bottom <= cell.y + cell.height


def test_tall_conditioning_subjects_gain_card_safe_padding():
    scope_dir = Path(__file__).resolve().parents[2] / "data" / "poster_assets" / "Base1"
    placements = cutout_placements(build_page_layout("standard_3x3"), scope_dir)
    conditioned = card_safe_conditioning_placements(placements)

    assert conditioned[0]["image"].height < placements[0]["image"].height
    assert conditioned[1]["image"].size == placements[1]["image"].size
    assert conditioned[2]["image"].size == placements[2]["image"].size
    original_box = placements[0]["image"].getchannel("A").getbbox()
    conditioned_box = conditioned[0]["image"].getchannel("A").getbbox()
    assert original_box is not None and conditioned_box is not None
    assert placements[0]["y"] + original_box[3] == conditioned[0]["y"] + conditioned_box[3]


def test_identity_references_use_poster_coordinates():
    scope_dir = Path(__file__).resolve().parents[2] / "data" / "poster_assets" / "Base1"
    manifest = {"layout": {"name": "standard_3x3"}}

    build_identity_references(scope_dir, manifest)

    layout = build_page_layout("standard_3x3", width_px=848)
    for index, cell in enumerate(layout.bottom_row_cells(), start=1):
        image = Image.open(
            scope_dir / "comfyui_poster" / f"identity_reference_{index}.png"
        ).convert("RGB")
        assert image.size == (848, 1168)
        neutral = Image.new("RGB", image.size, (226, 224, 211))
        bbox = ImageChops.difference(image, neutral).getbbox()
        assert bbox is not None
        assert bbox[0] >= cell.x
        assert bbox[1] >= cell.y
        assert bbox[2] <= cell.x + cell.width
        assert bbox[3] <= cell.y + cell.height
        if index == 1:
            assert bbox[2] <= cell.x + round(cell.width * 0.86)


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
    assert workflow["25"]["inputs"]["conditioning"] == ["4", 0]
    assert workflow["28"]["inputs"]["conditioning"] == ["25", 0]
    assert workflow["31"]["inputs"]["conditioning"] == ["28", 0]
    assert workflow["17"]["inputs"]["conditioning"] == ["31", 0]
    assert workflow["9"]["inputs"]["positive"] == ["17", 0]


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


def test_raw_artwork_validation_rejects_blank_output(tmp_path: Path):
    blank = tmp_path / "blank.png"
    Image.new("RGB", (64, 64), (0, 0, 0)).save(blank)

    try:
        validate_raw_artwork(blank)
    except RuntimeError as error:
        assert "blank or near-constant" in str(error)
    else:
        raise AssertionError("blank artwork was accepted")


def test_resize_artwork_uses_requested_poster_dimensions(tmp_path: Path):
    source = tmp_path / "source.png"
    destination = tmp_path / "resized.png"
    artwork = Image.new("RGB", (64, 96), (40, 120, 80))
    artwork.paste((120, 180, 220), (0, 0, 64, 48))
    artwork.save(source)

    resize_artwork("Base1", source, destination, 0.25)

    assert Image.open(destination).size == (432, 596)


def test_slice_poster_exports_every_card_without_binder_gaps(tmp_path: Path):
    source = tmp_path / "poster.png"
    layout = build_page_layout("standard_3x3", width_px=848)
    Image.new("RGB", (layout.width_px, layout.height_px), (40, 120, 80)).save(source)

    outputs = slice_poster("Base1", source, tmp_path / "cards")

    assert len(outputs) == 9
    assert [path.name for path in outputs] == [
        f"card_r{row}_c{column}.png"
        for row in range(1, 4)
        for column in range(1, 4)
    ]
    assert all(
        Image.open(path).size == (layout.card_width_px, layout.card_height_px)
        for path in outputs
    )
