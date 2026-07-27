import sys

import pytest

from scripts.poster_assets import run_comfyui_poster as poster_runner
from scripts.poster_assets.create_anima_poster_workflow import (
    DEFAULT_CFG as DEFAULT_ANIMA_CFG,
    DEFAULT_CONTROL_METHOD as DEFAULT_ANIMA_CONTROL_METHOD,
    DEFAULT_ENCODER as DEFAULT_ANIMA_ENCODER,
    DEFAULT_GENERATION_MODE as DEFAULT_ANIMA_MODE,
    DEFAULT_LORA as DEFAULT_ANIMA_LORA,
    DEFAULT_MODEL as DEFAULT_ANIMA_MODEL,
    DEFAULT_REFERENCE_STRENGTH as DEFAULT_ANIMA_REFERENCE_STRENGTH,
    DEFAULT_STEPS as DEFAULT_ANIMA_STEPS,
    DEFAULT_VAE as DEFAULT_ANIMA_VAE,
)
from scripts.poster_assets.generation_options import (
    DEFAULT_FLUX_ENCODER,
    DEFAULT_FLUX_MODEL,
    DEFAULT_FLUX_VAE,
    metadata_from_workflow_options,
    resolve_generation_options,
)


def test_matching_flux_manifest_drives_workflow_and_canonical_metadata():
    configured = {
        "engine": "flux",
        "model": "manifest-model.safetensors",
        "model_sha256": "a" * 64,
        "encoder": "manifest-encoder.safetensors",
        "vae": "manifest-vae.safetensors",
        "mode": "identity_lock",
        "reference_mode": "two_pass_source_pixels",
        "steps": "7",
        "seed": 123,
        "generation_megapixels": 1.0,
    }

    resolved = resolve_generation_options(
        "flux",
        configured,
        {
            "flux_model": None,
            "flux_steps": None,
            "flux_reference_mode": None,
        },
    )

    assert resolved.workflow_options == {
        "flux_model": "manifest-model.safetensors",
        "flux_clip": "manifest-encoder.safetensors",
        "flux_vae": "manifest-vae.safetensors",
        "flux_mode": "identity_lock",
        "flux_steps": 7,
        # The builder accepts edit-reference semantics, not the canonical
        # two-pass provenance label.
        "flux_reference_mode": "identity",
    }
    assert resolved.metadata == {
        "engine": "flux",
        "model": "manifest-model.safetensors",
        "encoder": "manifest-encoder.safetensors",
        "vae": "manifest-vae.safetensors",
        "mode": "identity_lock",
        "steps": 7,
        "reference_mode": "two_pass_source_pixels",
    }
    assert "model_sha256" not in resolved.metadata
    assert "seed" not in resolved.metadata


def test_flux_edit_reference_is_shared_by_workflow_and_metadata():
    resolved = resolve_generation_options(
        "flux",
        {
            "engine": "flux",
            "mode": "edit",
            "reference_mode": "composition",
        },
        {"flux_steps": 12},
    )

    assert resolved.workflow_options["flux_reference_mode"] == "composition"
    assert resolved.metadata["reference_mode"] == "composition"
    assert resolved.metadata["steps"] == 12


def test_flux_mode_override_does_not_reuse_incompatible_manifest_reference():
    resolved = resolve_generation_options(
        "flux",
        {
            "engine": "flux",
            "mode": "identity_lock",
            "reference_mode": "two_pass_source_pixels",
        },
        {"flux_mode": "edit"},
    )

    assert resolved.workflow_options["flux_reference_mode"] == "identity"
    assert resolved.metadata["reference_mode"] == "identity"


def test_wrong_engine_manifest_is_ignored_as_one_contract():
    resolved = resolve_generation_options(
        "anima",
        {
            "engine": "flux",
            "model": "must-not-leak.safetensors",
            "encoder": "must-not-leak.safetensors",
            "vae": "must-not-leak.safetensors",
            "mode": "identity_lock",
            "steps": 999,
        },
        {"anima_model": None, "anima_steps": None},
    )

    assert resolved.workflow_options == {
        "anima_model": DEFAULT_ANIMA_MODEL,
        "anima_lora": DEFAULT_ANIMA_LORA,
        "anima_encoder": DEFAULT_ANIMA_ENCODER,
        "anima_vae": DEFAULT_ANIMA_VAE,
        "anima_mode": DEFAULT_ANIMA_MODE,
        "reference_strength": DEFAULT_ANIMA_REFERENCE_STRENGTH,
        "anima_steps": DEFAULT_ANIMA_STEPS,
        "anima_cfg": DEFAULT_ANIMA_CFG,
        "anima_control_method": DEFAULT_ANIMA_CONTROL_METHOD,
    }
    assert resolved.metadata == {
        "engine": "anima",
        "model": DEFAULT_ANIMA_MODEL,
        "lora": DEFAULT_ANIMA_LORA,
        "encoder": DEFAULT_ANIMA_ENCODER,
        "vae": DEFAULT_ANIMA_VAE,
        "mode": DEFAULT_ANIMA_MODE,
        "reference_strength": DEFAULT_ANIMA_REFERENCE_STRENGTH,
        "steps": DEFAULT_ANIMA_STEPS,
        "cfg": DEFAULT_ANIMA_CFG,
        "control_method": DEFAULT_ANIMA_CONTROL_METHOD,
        "reference_mode": "cosmos",
    }


def test_explicit_anima_overrides_win_and_are_converted():
    resolved = resolve_generation_options(
        "anima",
        {
            "engine": "anima",
            "model": "manifest-model.safetensors",
            "lora": "manifest-lora.safetensors",
            "encoder": "manifest-encoder.safetensors",
            "vae": "manifest-vae.safetensors",
            "mode": "generate",
            "reference_mode": "cosmos",
            "reference_strength": 0.5,
            "steps": 20,
            "cfg": 3.0,
            "control_method": DEFAULT_ANIMA_CONTROL_METHOD,
        },
        {
            "anima_model": " cli-model.safetensors ",
            "anima_lora": "cli-lora.safetensors",
            "anima_encoder": "cli-encoder.safetensors",
            "anima_vae": "cli-vae.safetensors",
            "anima_mode": "edit",
            "reference_strength": "0.75",
            "anima_steps": "17",
            "anima_cfg": "2.5",
        },
    )

    assert resolved.workflow_options == {
        "anima_model": "cli-model.safetensors",
        "anima_lora": "cli-lora.safetensors",
        "anima_encoder": "cli-encoder.safetensors",
        "anima_vae": "cli-vae.safetensors",
        "anima_mode": "edit",
        "reference_strength": 0.75,
        "anima_steps": 17,
        "anima_cfg": 2.5,
        "anima_control_method": DEFAULT_ANIMA_CONTROL_METHOD,
    }
    assert resolved.metadata == {
        "engine": "anima",
        "model": "cli-model.safetensors",
        "lora": "cli-lora.safetensors",
        "encoder": "cli-encoder.safetensors",
        "vae": "cli-vae.safetensors",
        "mode": "edit",
        "reference_strength": 0.75,
        "steps": 17,
        "cfg": 2.5,
        "control_method": DEFAULT_ANIMA_CONTROL_METHOD,
        "reference_mode": "cosmos",
    }


def test_matching_anima_manifest_records_its_control_method():
    resolved = resolve_generation_options(
        "anima",
        {
            "engine": "anima",
            "control_method": DEFAULT_ANIMA_CONTROL_METHOD,
        },
    )

    assert (
        resolved.workflow_options["anima_control_method"]
        == DEFAULT_ANIMA_CONTROL_METHOD
    )
    assert (
        resolved.metadata["control_method"]
        == DEFAULT_ANIMA_CONTROL_METHOD
    )


def test_alternative_engine_maps_are_complete_and_canonical():
    flux1 = resolve_generation_options(
        "flux1_canny",
        {
            "engine": "flux1_canny",
            "model": "flux1.gguf",
            "encoder": "clip.safetensors",
            "encoder_2": "t5.gguf",
            "vae": "ae.safetensors",
            "controlnet": "canny.safetensors",
            "mode": "generate",
            "reference_mode": "canny",
            "steps": 21,
            "guidance": 4,
            "control_strength": 0.8,
            "canny_low": 0.1,
            "canny_high": 0.4,
        },
    )
    qwen = resolve_generation_options(
        "qwen_edit",
        {
            "engine": "qwen_edit",
            "model": "qwen.gguf",
            "encoder": "qwen-clip.safetensors",
            "vae": "qwen-vae.safetensors",
            "lora": "qwen-lora.safetensors",
            "mode": "edit",
            "reference_mode": "multi_reference",
            "steps": 5,
            "cfg": 1.25,
            "shift": 2.75,
        },
    )

    assert flux1.workflow_options == {
        "flux1_model": "flux1.gguf",
        "flux1_clip": "clip.safetensors",
        "flux1_t5": "t5.gguf",
        "flux1_vae": "ae.safetensors",
        "flux1_controlnet": "canny.safetensors",
        "flux1_steps": 21,
        "flux1_guidance": 4.0,
        "flux1_control_strength": 0.8,
        "flux1_canny_low": 0.1,
        "flux1_canny_high": 0.4,
    }
    assert flux1.metadata["mode"] == "generate"
    assert flux1.metadata["reference_mode"] == "canny"
    assert qwen.workflow_options == {
        "qwen_model": "qwen.gguf",
        "qwen_clip": "qwen-clip.safetensors",
        "qwen_vae": "qwen-vae.safetensors",
        "qwen_lora": "qwen-lora.safetensors",
        "qwen_steps": 5,
        "qwen_cfg": 1.25,
        "qwen_shift": 2.75,
    }
    assert qwen.metadata == {
        "engine": "qwen_edit",
        "model": "qwen.gguf",
        "encoder": "qwen-clip.safetensors",
        "vae": "qwen-vae.safetensors",
        "lora": "qwen-lora.safetensors",
        "steps": 5,
        "cfg": 1.25,
        "shift": 2.75,
        "mode": "edit",
        "reference_mode": "multi_reference",
    }


@pytest.mark.parametrize(
    ("engine", "configured", "overrides", "message"),
    [
        (
            "flux",
            {
                "engine": "flux",
                "mode": "identity_lock",
                "reference_mode": "identity",
            },
            {},
            "incompatible",
        ),
        (
            "anima",
            {
                "engine": "anima",
                "reference_mode": "wrong",
            },
            {},
            "must be 'cosmos'",
        ),
        (
            "flux1_canny",
            {
                "engine": "flux1_canny",
                "canny_low": 0.7,
                "canny_high": 0.2,
            },
            {},
            "canny_low < canny_high",
        ),
        (
            "qwen_edit",
            {"engine": "qwen_edit"},
            {"qwen_steps": 2.5},
            "positive integer",
        ),
    ],
)
def test_invalid_generation_contracts_fail_closed(
    engine,
    configured,
    overrides,
    message,
):
    with pytest.raises(ValueError, match=message):
        resolve_generation_options(engine, configured, overrides)


def test_none_overrides_preserve_flux_defaults():
    resolved = resolve_generation_options(
        "flux",
        None,
        {
            "flux_model": None,
            "flux_clip": None,
            "flux_vae": None,
            "flux_mode": None,
            "flux_steps": None,
            "flux_reference_mode": None,
        },
    )

    assert resolved.metadata["model"] == DEFAULT_FLUX_MODEL
    assert resolved.metadata["encoder"] == DEFAULT_FLUX_ENCODER
    assert resolved.metadata["vae"] == DEFAULT_FLUX_VAE
    assert resolved.metadata["reference_mode"] == "two_pass_source_pixels"


@pytest.mark.parametrize(
    "engine",
    ("flux", "anima", "flux1_canny", "qwen_edit"),
)
def test_metadata_is_rebuilt_from_the_exact_resolved_workflow_options(engine):
    resolved = resolve_generation_options(engine)

    rebuilt = metadata_from_workflow_options(
        engine,
        resolved.workflow_options,
    )

    assert rebuilt == resolved.metadata


def test_metadata_rebuild_rejects_partial_workflow_options():
    with pytest.raises(ValueError, match="missing:.*flux_vae"):
        metadata_from_workflow_options(
            "flux",
            {
                key: value
                for key, value in resolve_generation_options(
                    "flux"
                ).workflow_options.items()
                if key != "flux_vae"
            },
        )


@pytest.mark.parametrize(
    "generation",
    (
        {
            "engine": "anima",
            "model": "anima.safetensors",
            "lora": "anima-edit.safetensors",
            "encoder": "anima-encoder.safetensors",
            "vae": "anima-vae.safetensors",
            "mode": "edit",
            "reference_mode": "cosmos",
            "reference_strength": 0.7,
            "steps": 18,
            "cfg": 2.8,
            "control_method": DEFAULT_ANIMA_CONTROL_METHOD,
        },
        {
            "engine": "flux1_canny",
            "model": "flux1.gguf",
            "encoder": "clip.safetensors",
            "encoder_2": "t5.gguf",
            "vae": "ae.safetensors",
            "controlnet": "canny.safetensors",
            "mode": "generate",
            "reference_mode": "canny",
            "steps": 21,
            "guidance": 3.6,
            "control_strength": 0.8,
            "canny_low": 0.1,
            "canny_high": 0.4,
        },
        {
            "engine": "qwen_edit",
            "model": "qwen.gguf",
            "encoder": "qwen-clip.safetensors",
            "vae": "qwen-vae.safetensors",
            "lora": "qwen-lora.safetensors",
            "mode": "edit",
            "reference_mode": "multi_reference",
            "steps": 5,
            "cfg": 1.25,
            "shift": 2.75,
        },
    ),
)
def test_runner_cli_passes_alternative_manifest_values_to_the_workflow(
    generation,
    monkeypatch,
    tmp_path,
):
    configured = {
        **generation,
        "seed": 321,
        "generation_megapixels": 0.25,
        "output_method": "lanczos",
        "output_megapixels": 0.25,
    }
    captured = {}

    def fake_run(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return (
            tmp_path / "raw.png",
            tmp_path / "artwork.png",
            tmp_path / "final.png",
            tmp_path / "run.json",
        )

    monkeypatch.setattr(
        poster_runner,
        "configured_generation",
        lambda _scope: configured,
    )
    monkeypatch.setattr(poster_runner, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_comfyui_poster.py", "--scope", "Example"],
    )

    assert poster_runner.main() == 0

    resolved = resolve_generation_options(
        str(generation["engine"]),
        configured,
    )
    assert captured["args"][1:3] == (321, 0.25)
    assert captured["kwargs"]["engine"] == generation["engine"]
    for key, value in resolved.workflow_options.items():
        assert captured["kwargs"][key] == value
    assert captured["kwargs"]["output_megapixels"] == 0.25
    assert captured["kwargs"]["output_dpi"] is None


def test_unsupported_engine_and_non_mapping_inputs_are_rejected():
    with pytest.raises(ValueError, match="Unsupported generation engine"):
        resolve_generation_options("unknown")
    with pytest.raises(TypeError, match="configured_generation"):
        resolve_generation_options("flux", configured_generation=[])
    with pytest.raises(TypeError, match="overrides"):
        resolve_generation_options("flux", overrides=[])
    with pytest.raises(TypeError, match="workflow_options"):
        metadata_from_workflow_options("flux", [])
