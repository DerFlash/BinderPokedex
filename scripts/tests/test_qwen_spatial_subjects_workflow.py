from pathlib import Path

import pytest
from PIL import Image, ImageChops

from scripts.poster_assets import create_qwen_spatial_subjects_workflow
from scripts.poster_assets.create_comfyui_poster_workflow import (
    output_dimensions,
)
from scripts.poster_assets.create_qwen_spatial_subjects_workflow import (
    PROMPT_SNAPSHOT,
    REFERENCE_PREFIX,
    build_spatial_subject_references,
    build_workflow,
    spatial_subject_placements,
    write_experiment,
)


SCOPE = "Pokedex/sections/gen7"
SEED = 260726054
NEUTRAL = (226, 224, 211)


def test_spatial_references_each_contain_one_canonical_subject(
    tmp_path: Path,
):
    paths = build_spatial_subject_references(SCOPE, tmp_path)
    canvas_size, placements = spatial_subject_placements(SCOPE)

    assert len(paths) == 3
    assert canvas_size == output_dimensions(SCOPE, 1.0)
    for index, (path, placement) in enumerate(
        zip(paths, placements, strict=True),
        start=1,
    ):
        assert path.name == f"{REFERENCE_PREFIX}_{index}.png"
        actual = Image.open(path)
        assert actual.mode == "RGB"
        assert actual.size == canvas_size

        expected = Image.new("RGBA", canvas_size, (*NEUTRAL, 255))
        expected.alpha_composite(
            placement["image"],
            (int(placement["x"]), int(placement["y"])),
        )
        assert ImageChops.difference(
            actual,
            expected.convert("RGB"),
        ).getbbox() is None

        visible = ImageChops.difference(
            actual,
            Image.new("RGB", canvas_size, NEUTRAL),
        ).getbbox()
        assert visible is not None
        cell = placement["cell"]
        assert cell.x <= visible[0] < visible[2] <= cell.x + cell.width
        assert cell.y <= visible[1] < visible[3] <= cell.y + cell.height


def test_qwen_spatial_graph_is_one_empty_target_pass():
    workflow = build_workflow(
        SCOPE,
        seed=SEED,
        megapixels=0.25,
    )

    assert [
        workflow[node_id]["inputs"]["image"]
        for node_id in ("7", "8", "9")
    ] == [
        f"{REFERENCE_PREFIX}_1.png",
        f"{REFERENCE_PREFIX}_2.png",
        f"{REFERENCE_PREFIX}_3.png",
    ]
    for conditioning_id in ("10", "11"):
        assert workflow[conditioning_id]["inputs"]["image1"] == ["7", 0]
        assert workflow[conditioning_id]["inputs"]["image2"] == ["8", 0]
        assert workflow[conditioning_id]["inputs"]["image3"] == ["9", 0]
    assert workflow["14"] == {
        "class_type": "EmptySD3LatentImage",
        "inputs": {
            "width": output_dimensions(SCOPE, 0.25)[0],
            "height": output_dimensions(SCOPE, 0.25)[1],
            "batch_size": 1,
        },
    }
    assert workflow["15"]["inputs"]["latent_image"] == ["14", 0]
    assert sum(
        node["class_type"] == "KSampler"
        for node in workflow.values()
    ) == 1
    assert sum(
        node["class_type"] == "VAEDecode"
        for node in workflow.values()
    ) == 1
    assert {
        node["class_type"]
        for node in workflow.values()
    } == {
        "UnetLoaderGGUF",
        "ModelSamplingAuraFlow",
        "CFGNorm",
        "LoraLoaderModelOnly",
        "CLIPLoader",
        "VAELoader",
        "LoadImage",
        "TextEncodeQwenImageEditPlus",
        "FluxKontextMultiReferenceLatentMethod",
        "EmptySD3LatentImage",
        "KSampler",
        "VAEDecode",
        "SaveImage",
    }


def test_qwen_spatial_prompt_binds_picture_name_card_and_coordinates():
    workflow = build_workflow(
        SCOPE,
        seed=SEED,
        megapixels=0.25,
    )
    prompt = workflow["10"]["inputs"]["prompt"]

    assert "PICTURE 1 = Rowlet, left bottom card" in prompt
    assert "PICTURE 2 = Litten, center bottom card" in prompt
    assert "PICTURE 3 = Popplio, right bottom card" in prompt
    assert (
        "Rowlet: x 4.2% to 17.2%, y 85.1% to 96.1%"
        in prompt
    )
    assert (
        "Litten: x 44.3% to 55.7%, y 85.1% to 96.1%"
        in prompt
    )
    assert (
        "Popplio: x 81.5% to 96.8%, y 86.6% to 96.1%"
        in prompt
    )
    assert (
        "Across all source pictures, each character appears exactly once"
        in prompt
    )
    assert "empty target in one unified denoising pass" in prompt
    assert "no later overlay, restoration, mask repair, or composite" in prompt
    assert "Alola-inspired island clearing" in prompt


def test_qwen_spatial_experiment_writes_only_generated_control_files(
    tmp_path: Path,
):
    workflow_path = write_experiment(
        SCOPE,
        seed=SEED,
        megapixels=0.25,
        output_dir=tmp_path,
    )

    assert workflow_path.name == (
        "workflow_api_qwen_spatial_subjects_0p25mp_260726054.json"
    )
    assert (tmp_path / PROMPT_SNAPSHOT).is_file()
    assert len(list(tmp_path.glob(f"{REFERENCE_PREFIX}_*.png"))) == 3
    assert not (tmp_path / "structure_reference.png").exists()
    assert not list(tmp_path.glob("qwen_identity_reference_*.png"))


def test_qwen_spatial_subjects_rejects_non_three_subject_scope(
    monkeypatch,
):
    monkeypatch.setattr(
        create_qwen_spatial_subjects_workflow,
        "load_cutout_items",
        lambda _scope_dir: [{}, {}],
    )
    with pytest.raises(
        ValueError,
        match="requires exactly 3 subjects",
    ):
        spatial_subject_placements(SCOPE)
