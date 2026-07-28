import json
from pathlib import Path

import pytest
from PIL import Image, ImageChops

from scripts.poster_assets import create_dreamo_identity_poster_workflow as dreamo
from scripts.poster_assets.patch_comfyui_dreamo import (
    NEW as PATCHED_DREAMO_WRAPPER,
    OLD as ORIGINAL_DREAMO_WRAPPER,
    patch as patch_dreamo,
)
from scripts.poster_assets.create_comfyui_poster_workflow import (
    output_dimensions,
)
from scripts.poster_assets.poster_io import (
    load_cutout_items,
    poster_bundle,
)


SCOPE = "Pokedex/sections/gen7"
SEED = 260726054


def test_dreamo_graph_has_one_empty_target_sampler_and_decode():
    workflow = dreamo.build_workflow(
        SCOPE,
        seed=SEED,
        megapixels=0.25,
    )

    assert len(workflow) == 23
    assert sum(
        item["class_type"] == "EmptySD3LatentImage"
        for item in workflow.values()
    ) == 1
    assert sum(
        item["class_type"] == "KSampler"
        for item in workflow.values()
    ) == 1
    assert sum(
        item["class_type"] == "VAEDecode"
        for item in workflow.values()
    ) == 1
    assert not any(
        item["class_type"]
        in {
            "VAEEncode",
            "VAEEncodeForInpaint",
            "ImageCompositeMasked",
            "InpaintModelConditioning",
            "SetLatentNoiseMask",
            "ReferenceLatent",
        }
        for item in workflow.values()
    )
    assert workflow["27"]["inputs"] == {
        "width": 432,
        "height": 592,
        "batch_size": 1,
    }
    assert workflow["28"]["inputs"]["latent_image"] == ["27", 0]
    assert workflow["29"]["inputs"]["samples"] == ["28", 0]
    assert workflow["30"]["inputs"]["images"] == ["29", 0]


def test_dreamo_graph_passes_three_separate_references_to_apply_node():
    workflow = dreamo.build_workflow(
        SCOPE,
        seed=SEED,
        megapixels=0.25,
    )

    assert [
        item["inputs"]["image"]
        for item in workflow.values()
        if item["class_type"] == "LoadImage"
    ] == [
        "dreamo_identity_reference_1.png",
        "dreamo_identity_reference_2.png",
        "dreamo_identity_reference_3.png",
    ]
    reference_nodes = [
        item
        for item in workflow.values()
        if item["class_type"] == "DreamORefEncode"
    ]
    assert len(reference_nodes) == 3
    assert all(
        item["inputs"]["vae"] == ["8", 0]
        and item["inputs"]["dreamo_processor"] == ["12", 0]
        and item["inputs"]["resolution"] == 512
        and item["inputs"]["ref_task"] == "ip"
        for item in reference_nodes
    )
    assert workflow["26"]["inputs"] == {
        "model": ["6", 0],
        "ref1": ["21", 0],
        "ref2": ["23", 0],
        "ref3": ["25", 0],
    }
    assert not any(
        "structure" in item["inputs"].get("image", "")
        or "background" in item["inputs"].get("image", "")
        or "cast" in item["inputs"].get("image", "")
        for item in workflow.values()
        if item["class_type"] == "LoadImage"
    )


def test_dreamo_graph_pins_the_official_v1_1_lora_order():
    workflow = dreamo.build_workflow(
        SCOPE,
        seed=SEED,
        megapixels=0.25,
    )

    assert workflow["1"]["inputs"]["unet_name"] == "flux1-dev-Q4_K_S.gguf"
    assert workflow["7"]["inputs"] == {
        "clip_name1": "clip_l.safetensors",
        "clip_name2": "t5-v1_1-xxl-encoder-Q4_K_S.gguf",
        "type": "flux",
    }
    assert workflow["8"]["inputs"]["vae_name"] == "ae.safetensors"
    previous = ["1", 0]
    for node_id, (lora_name, strength) in zip(
        ("2", "3", "4", "5", "6"),
        dreamo.LORA_CHAIN,
        strict=True,
    ):
        assert workflow[node_id]["inputs"] == {
            "model": previous,
            "lora_name": lora_name,
            "strength_model": strength,
        }
        previous = [node_id, 0]
    assert workflow["28"]["inputs"] == {
        "model": ["26", 0],
        "seed": SEED,
        "steps": 12,
        "cfg": 1.0,
        "sampler_name": "euler",
        "scheduler": "simple",
        "positive": ["11", 0],
        "negative": ["10", 0],
        "latent_image": ["27", 0],
        "denoise": 1.0,
    }
    assert workflow["11"]["inputs"]["guidance"] == 4.5


def test_dreamo_prompt_keeps_identity_position_and_scene_contracts():
    workflow = dreamo.build_workflow(
        SCOPE,
        seed=SEED,
        megapixels=1.0,
    )
    prompt = workflow["9"]["inputs"]["text"]

    assert "cheerful Alola island landscape" in prompt
    for index, name in enumerate(("Rowlet", "Litten", "Popplio"), start=1):
        assert (
            f"REFERENCE IMAGE {index} is the sole identity and anatomy "
            f"authority for {name}"
        ) in prompt
    assert "Rowlet: x " in prompt
    assert "Litten: x " in prompt
    assert "Popplio: x " in prompt
    assert "inside its named bottom card" in prompt
    assert "one empty target in one unified denoising pass" in prompt
    assert "There is no supplied landscape" in prompt
    assert "rather than pasted over it" in prompt
    assert "must keep the same front-or-behind relationship" in prompt
    assert "source-derived structural guide" not in prompt
    assert "sole spatial cast-layout reference" not in prompt


def test_dreamo_writer_creates_only_its_three_unscaled_rgb_inputs(
    tmp_path: Path,
):
    workflow_path = dreamo.write_experiment(
        SCOPE,
        seed=SEED,
        megapixels=0.25,
        output_dir=tmp_path,
    )

    assert workflow_path.name == (
        "workflow_api_dreamo_v1_1_0p25mp_260726054.json"
    )
    assert set(path.name for path in tmp_path.iterdir()) == {
        "dreamo_identity_reference_1.png",
        "dreamo_identity_reference_2.png",
        "dreamo_identity_reference_3.png",
        "dreamo_v1_1_prompt.generated.txt",
        workflow_path.name,
    }
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    assert (
        workflow["30"]["inputs"]["filename_prefix"]
        == "pokedex__sections__gen7_dreamo_v1_1_0p25mp_seed_260726054"
    )

    bundle = poster_bundle(SCOPE)
    items = load_cutout_items(bundle.asset_dir)
    for index, item in enumerate(items, start=1):
        source = Image.open(
            bundle.asset_dir / "cutouts" / item["file"]
        ).convert("RGBA")
        reference = Image.open(
            tmp_path / f"dreamo_identity_reference_{index}.png"
        ).convert("RGB")
        assert reference.size == (512, 512)
        x = (reference.width - source.width) // 2
        y = (reference.height - source.height) // 2
        expected = Image.new("RGB", reference.size, (226, 224, 211))
        expected.paste(
            source.convert("RGB"),
            (x, y),
            source.getchannel("A"),
        )
        assert ImageChops.difference(reference, expected).getbbox() is None


def test_dreamo_graph_rejects_unsupported_reference_count(monkeypatch):
    monkeypatch.setattr(dreamo, "load_cutout_items", lambda _path: [{}, {}])

    with pytest.raises(ValueError, match="exactly 3 subject references"):
        dreamo.build_workflow(
            SCOPE,
            seed=SEED,
            megapixels=0.25,
        )


@pytest.mark.parametrize("resolution", [511, 513, 1025])
def test_dreamo_graph_rejects_invalid_reference_resolution(resolution):
    with pytest.raises(ValueError, match="reference_resolution"):
        dreamo.build_workflow(
            SCOPE,
            seed=SEED,
            megapixels=0.25,
            reference_resolution=resolution,
        )


def test_dreamo_preflight_dimensions_are_latent_aligned():
    width, height = output_dimensions(SCOPE, 0.25)

    assert (width, height) == (432, 592)
    assert width % 16 == 0
    assert height % 16 == 0


def test_dreamo_compatibility_patch_forwards_new_sampler_keywords(
    tmp_path: Path,
):
    dreamo_py = tmp_path / "dreamo.py"
    dreamo_py.write_text(ORIGINAL_DREAMO_WRAPPER, encoding="utf-8")

    assert patch_dreamo(dreamo_py) is True
    assert patch_dreamo(dreamo_py) is False
    patched = dreamo_py.read_text(encoding="utf-8")
    assert patched == PATCHED_DREAMO_WRAPPER
    assert "seed=None, **kwargs" in patched
    assert "seed, **kwargs)" in patched
    assert dreamo_py.with_suffix(".py.pre-comfy-0.28").read_text(
        encoding="utf-8"
    ) == ORIGINAL_DREAMO_WRAPPER


def test_dreamo_compatibility_patch_rejects_unknown_source(tmp_path: Path):
    dreamo_py = tmp_path / "dreamo.py"
    dreamo_py.write_text("def unrelated():\n    pass\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="not found exactly once"):
        patch_dreamo(dreamo_py)
