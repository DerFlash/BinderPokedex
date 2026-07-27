"""Resolve effective, engine-specific poster generation options.

The resolver is deliberately independent from argparse, poster I/O, ComfyUI,
and provenance hashing.  It has two outputs:

* ``workflow_options`` uses the parameter names accepted by the poster runner.
* ``metadata`` uses the canonical names stored below ``artwork.generation``.

Only a manifest whose configured ``engine`` matches the requested engine is
considered.  An override wins only when its value is not ``None``.  Builder
defaults are the final fallback.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable, Mapping

try:
    from .create_anima_poster_workflow import (
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
    from .create_flux1_canny_poster_workflow import (
        DEFAULT_CANNY_HIGH as DEFAULT_FLUX1_CANNY_HIGH,
        DEFAULT_CANNY_LOW as DEFAULT_FLUX1_CANNY_LOW,
        DEFAULT_CLIP as DEFAULT_FLUX1_CLIP,
        DEFAULT_CONTROLNET as DEFAULT_FLUX1_CONTROLNET,
        DEFAULT_CONTROL_STRENGTH as DEFAULT_FLUX1_CONTROL_STRENGTH,
        DEFAULT_GUIDANCE as DEFAULT_FLUX1_GUIDANCE,
        DEFAULT_MODEL as DEFAULT_FLUX1_MODEL,
        DEFAULT_STEPS as DEFAULT_FLUX1_STEPS,
        DEFAULT_T5 as DEFAULT_FLUX1_T5,
        DEFAULT_VAE as DEFAULT_FLUX1_VAE,
    )
    from .create_qwen_edit_poster_workflow import (
        DEFAULT_CFG as DEFAULT_QWEN_CFG,
        DEFAULT_CLIP as DEFAULT_QWEN_CLIP,
        DEFAULT_LORA as DEFAULT_QWEN_LORA,
        DEFAULT_MODEL as DEFAULT_QWEN_MODEL,
        DEFAULT_SHIFT as DEFAULT_QWEN_SHIFT,
        DEFAULT_STEPS as DEFAULT_QWEN_STEPS,
        DEFAULT_VAE as DEFAULT_QWEN_VAE,
    )
    from .generation_contract import (
        validate_generation_reference_contract,
    )
except ImportError:  # Direct script execution
    from create_anima_poster_workflow import (
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
    from create_flux1_canny_poster_workflow import (
        DEFAULT_CANNY_HIGH as DEFAULT_FLUX1_CANNY_HIGH,
        DEFAULT_CANNY_LOW as DEFAULT_FLUX1_CANNY_LOW,
        DEFAULT_CLIP as DEFAULT_FLUX1_CLIP,
        DEFAULT_CONTROLNET as DEFAULT_FLUX1_CONTROLNET,
        DEFAULT_CONTROL_STRENGTH as DEFAULT_FLUX1_CONTROL_STRENGTH,
        DEFAULT_GUIDANCE as DEFAULT_FLUX1_GUIDANCE,
        DEFAULT_MODEL as DEFAULT_FLUX1_MODEL,
        DEFAULT_STEPS as DEFAULT_FLUX1_STEPS,
        DEFAULT_T5 as DEFAULT_FLUX1_T5,
        DEFAULT_VAE as DEFAULT_FLUX1_VAE,
    )
    from create_qwen_edit_poster_workflow import (
        DEFAULT_CFG as DEFAULT_QWEN_CFG,
        DEFAULT_CLIP as DEFAULT_QWEN_CLIP,
        DEFAULT_LORA as DEFAULT_QWEN_LORA,
        DEFAULT_MODEL as DEFAULT_QWEN_MODEL,
        DEFAULT_SHIFT as DEFAULT_QWEN_SHIFT,
        DEFAULT_STEPS as DEFAULT_QWEN_STEPS,
        DEFAULT_VAE as DEFAULT_QWEN_VAE,
    )
    from generation_contract import validate_generation_reference_contract


SUPPORTED_ENGINES = ("flux", "anima", "flux1_canny", "qwen_edit")

DEFAULT_FLUX_MODEL = "flux-2-klein-4b-fp8.safetensors"
DEFAULT_FLUX_ENCODER = "qwen_3_4b.safetensors"
DEFAULT_FLUX_VAE = "flux2-vae.safetensors"
DEFAULT_FLUX_MODE = "identity_lock"
DEFAULT_FLUX_STEPS = 4
DEFAULT_FLUX_WORKFLOW_REFERENCE_MODE = "identity"

Converter = Callable[[object, str], object]


@dataclass(frozen=True)
class ResolvedGenerationOptions:
    """Effective values for one workflow and its provenance metadata."""

    workflow_options: dict[str, Any]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class FieldSpec:
    """Map one canonical manifest field to a runner parameter."""

    manifest_key: str
    override_key: str | None
    workflow_key: str | None
    default: object
    converter: Converter
    metadata_key: str | None = None
    include_metadata: bool = True


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def _positive_int(value: object, label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a positive integer")
    if isinstance(value, float) and not value.is_integer():
        raise ValueError(f"{label} must be a positive integer")
    try:
        converted = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} must be a positive integer") from error
    if converted <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return converted


def _positive_float(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a positive number")
    try:
        converted = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} must be a positive number") from error
    if not math.isfinite(converted) or converted <= 0:
        raise ValueError(f"{label} must be a positive number")
    return converted


def _unit_float(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be between 0 and 1")
    try:
        converted = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} must be between 0 and 1") from error
    if not math.isfinite(converted) or not 0 <= converted <= 1:
        raise ValueError(f"{label} must be between 0 and 1")
    return converted


def _choice(*allowed: str) -> Converter:
    choices = frozenset(allowed)

    def convert(value: object, label: str) -> str:
        converted = _string(value, label)
        if converted not in choices:
            expected = ", ".join(sorted(choices))
            raise ValueError(f"{label} must be one of: {expected}")
        return converted

    return convert


FLUX_FIELDS = (
    FieldSpec(
        "model",
        "flux_model",
        "flux_model",
        DEFAULT_FLUX_MODEL,
        _string,
    ),
    FieldSpec(
        "encoder",
        "flux_clip",
        "flux_clip",
        DEFAULT_FLUX_ENCODER,
        _string,
    ),
    FieldSpec(
        "vae",
        "flux_vae",
        "flux_vae",
        DEFAULT_FLUX_VAE,
        _string,
    ),
    FieldSpec(
        "mode",
        "flux_mode",
        "flux_mode",
        DEFAULT_FLUX_MODE,
        _choice("edit", "inpaint", "identity_lock", "joint_scene"),
    ),
    FieldSpec(
        "steps",
        "flux_steps",
        "flux_steps",
        DEFAULT_FLUX_STEPS,
        _positive_int,
    ),
)

ANIMA_FIELDS = (
    FieldSpec(
        "model",
        "anima_model",
        "anima_model",
        DEFAULT_ANIMA_MODEL,
        _string,
    ),
    FieldSpec(
        "lora",
        "anima_lora",
        "anima_lora",
        DEFAULT_ANIMA_LORA,
        _string,
    ),
    FieldSpec(
        "encoder",
        "anima_encoder",
        "anima_encoder",
        DEFAULT_ANIMA_ENCODER,
        _string,
    ),
    FieldSpec(
        "vae",
        "anima_vae",
        "anima_vae",
        DEFAULT_ANIMA_VAE,
        _string,
    ),
    FieldSpec(
        "mode",
        "anima_mode",
        "anima_mode",
        DEFAULT_ANIMA_MODE,
        _choice("generate", "edit"),
    ),
    FieldSpec(
        "reference_strength",
        "reference_strength",
        "reference_strength",
        DEFAULT_ANIMA_REFERENCE_STRENGTH,
        _positive_float,
    ),
    FieldSpec(
        "steps",
        "anima_steps",
        "anima_steps",
        DEFAULT_ANIMA_STEPS,
        _positive_int,
    ),
    FieldSpec(
        "cfg",
        "anima_cfg",
        "anima_cfg",
        DEFAULT_ANIMA_CFG,
        _positive_float,
    ),
    FieldSpec(
        "control_method",
        "anima_control_method",
        "anima_control_method",
        DEFAULT_ANIMA_CONTROL_METHOD,
        _choice(DEFAULT_ANIMA_CONTROL_METHOD),
    ),
)

FLUX1_CANNY_FIELDS = (
    FieldSpec(
        "model",
        "flux1_model",
        "flux1_model",
        DEFAULT_FLUX1_MODEL,
        _string,
    ),
    FieldSpec(
        "encoder",
        "flux1_clip",
        "flux1_clip",
        DEFAULT_FLUX1_CLIP,
        _string,
    ),
    FieldSpec(
        "encoder_2",
        "flux1_t5",
        "flux1_t5",
        DEFAULT_FLUX1_T5,
        _string,
    ),
    FieldSpec(
        "vae",
        "flux1_vae",
        "flux1_vae",
        DEFAULT_FLUX1_VAE,
        _string,
    ),
    FieldSpec(
        "controlnet",
        "flux1_controlnet",
        "flux1_controlnet",
        DEFAULT_FLUX1_CONTROLNET,
        _string,
    ),
    FieldSpec(
        "steps",
        "flux1_steps",
        "flux1_steps",
        DEFAULT_FLUX1_STEPS,
        _positive_int,
    ),
    FieldSpec(
        "guidance",
        "flux1_guidance",
        "flux1_guidance",
        DEFAULT_FLUX1_GUIDANCE,
        _positive_float,
    ),
    FieldSpec(
        "control_strength",
        "flux1_control_strength",
        "flux1_control_strength",
        DEFAULT_FLUX1_CONTROL_STRENGTH,
        _positive_float,
    ),
    FieldSpec(
        "canny_low",
        "flux1_canny_low",
        "flux1_canny_low",
        DEFAULT_FLUX1_CANNY_LOW,
        _unit_float,
    ),
    FieldSpec(
        "canny_high",
        "flux1_canny_high",
        "flux1_canny_high",
        DEFAULT_FLUX1_CANNY_HIGH,
        _unit_float,
    ),
)

QWEN_EDIT_FIELDS = (
    FieldSpec(
        "model",
        "qwen_model",
        "qwen_model",
        DEFAULT_QWEN_MODEL,
        _string,
    ),
    FieldSpec(
        "encoder",
        "qwen_clip",
        "qwen_clip",
        DEFAULT_QWEN_CLIP,
        _string,
    ),
    FieldSpec(
        "vae",
        "qwen_vae",
        "qwen_vae",
        DEFAULT_QWEN_VAE,
        _string,
    ),
    FieldSpec(
        "lora",
        "qwen_lora",
        "qwen_lora",
        DEFAULT_QWEN_LORA,
        _string,
    ),
    FieldSpec(
        "steps",
        "qwen_steps",
        "qwen_steps",
        DEFAULT_QWEN_STEPS,
        _positive_int,
    ),
    FieldSpec(
        "cfg",
        "qwen_cfg",
        "qwen_cfg",
        DEFAULT_QWEN_CFG,
        _positive_float,
    ),
    FieldSpec(
        "shift",
        "qwen_shift",
        "qwen_shift",
        DEFAULT_QWEN_SHIFT,
        _positive_float,
    ),
)

ENGINE_FIELD_MAPS = {
    "flux": FLUX_FIELDS,
    "anima": ANIMA_FIELDS,
    "flux1_canny": FLUX1_CANNY_FIELDS,
    "qwen_edit": QWEN_EDIT_FIELDS,
}

FIXED_METADATA = {
    "anima": {
        "reference_mode": "cosmos",
    },
    "flux1_canny": {
        "mode": "generate",
        "reference_mode": "canny",
    },
    "qwen_edit": {
        "mode": "edit",
        "reference_mode": "multi_reference",
    },
}


def _matching_manifest(
    engine: str,
    configured_generation: Mapping[str, object] | None,
) -> Mapping[str, object]:
    if configured_generation is None:
        return {}
    if not isinstance(configured_generation, Mapping):
        raise TypeError("configured_generation must be a mapping or None")
    if configured_generation.get("engine") != engine:
        return {}
    return configured_generation


def _resolve_fields(
    engine: str,
    specs: tuple[FieldSpec, ...],
    manifest: Mapping[str, object],
    overrides: Mapping[str, object],
) -> tuple[dict[str, Any], dict[str, Any]]:
    workflow: dict[str, Any] = {}
    metadata: dict[str, Any] = {"engine": engine}
    for spec in specs:
        value = spec.default
        if spec.manifest_key in manifest:
            value = manifest[spec.manifest_key]
        if (
            spec.override_key is not None
            and overrides.get(spec.override_key) is not None
        ):
            value = overrides[spec.override_key]
        converted = spec.converter(value, f"{engine}.{spec.manifest_key}")
        if spec.workflow_key is not None:
            workflow[spec.workflow_key] = converted
        metadata_key = spec.metadata_key or spec.manifest_key
        if spec.include_metadata:
            metadata[metadata_key] = converted
    return workflow, metadata


def _validate_fixed_metadata(
    engine: str,
    manifest: Mapping[str, object],
    metadata: dict[str, Any],
) -> None:
    for key, expected in FIXED_METADATA.get(engine, {}).items():
        if key in manifest:
            actual = _string(manifest[key], f"{engine}.{key}")
            if actual != expected:
                raise ValueError(
                    f"{engine}.{key} must be {expected!r}, got {actual!r}"
                )
        metadata[key] = expected


def _resolve_flux_reference_mode(
    manifest: Mapping[str, object],
    overrides: Mapping[str, object],
    workflow: dict[str, Any],
    metadata: dict[str, Any],
) -> None:
    mode = str(metadata["mode"])
    configured_mode = manifest.get("mode")
    explicit_reference = overrides.get("flux_reference_mode")

    if mode == "joint_scene":
        if explicit_reference not in {None, "identity"}:
            raise ValueError(
                "flux.reference_mode must be 'identity' for joint_scene"
            )
        workflow["flux_reference_mode"] = "identity"
        metadata_reference = "cast_layout_joint"
        if configured_mode == mode and "reference_mode" in manifest:
            configured_reference = _string(
                manifest["reference_mode"],
                "flux.reference_mode",
            )
            if configured_reference != metadata_reference:
                raise ValueError(
                    "flux.reference_mode is incompatible with mode "
                    f"{mode!r}: expected {metadata_reference!r}, "
                    f"got {configured_reference!r}"
                )
        metadata["reference_mode"] = metadata_reference
        return

    reference_source: object = DEFAULT_FLUX_WORKFLOW_REFERENCE_MODE
    if (
        explicit_reference is None
        and mode == "edit"
        and configured_mode == "edit"
        and "reference_mode" in manifest
    ):
        reference_source = manifest["reference_mode"]
    elif explicit_reference is not None:
        reference_source = explicit_reference
    workflow_reference = _choice("composition", "identity")(
        reference_source,
        "flux.reference_mode",
    )
    workflow["flux_reference_mode"] = workflow_reference

    if mode == "identity_lock":
        metadata_reference = "two_pass_source_pixels"
    elif mode == "inpaint":
        metadata_reference = "source_pixels"
    else:
        metadata_reference = workflow_reference

    # A matching manifest describes the canonical production contract.  When
    # its mode is not being replaced, reject a contradictory reference mode
    # instead of silently recording a different workflow.
    if configured_mode == mode and "reference_mode" in manifest:
        configured_reference = _string(
            manifest["reference_mode"],
            "flux.reference_mode",
        )
        if explicit_reference is None and configured_reference != metadata_reference:
            raise ValueError(
                "flux.reference_mode is incompatible with "
                f"mode {mode!r}: expected {metadata_reference!r}, "
                f"got {configured_reference!r}"
            )
    metadata["reference_mode"] = metadata_reference


def resolve_generation_options(
    engine: str,
    configured_generation: Mapping[str, object] | None = None,
    overrides: Mapping[str, object] | None = None,
) -> ResolvedGenerationOptions:
    """Return validated workflow and metadata values for ``engine``.

    ``configured_generation`` is ignored wholesale when its ``engine`` does
    not match the requested engine.  ``overrides`` may safely be ``vars()`` of
    an argparse namespace: irrelevant keys and keys whose value is ``None``
    have no effect.
    """
    if engine not in SUPPORTED_ENGINES:
        supported = ", ".join(SUPPORTED_ENGINES)
        raise ValueError(f"Unsupported generation engine {engine!r}: {supported}")
    if overrides is None:
        overrides = {}
    elif not isinstance(overrides, Mapping):
        raise TypeError("overrides must be a mapping or None")

    manifest = _matching_manifest(engine, configured_generation)
    workflow, metadata = _resolve_fields(
        engine,
        ENGINE_FIELD_MAPS[engine],
        manifest,
        overrides,
    )
    if engine == "flux":
        _resolve_flux_reference_mode(
            manifest,
            overrides,
            workflow,
            metadata,
        )
    else:
        _validate_fixed_metadata(engine, manifest, metadata)
    validate_generation_reference_contract(metadata)

    if engine == "flux1_canny":
        low = float(metadata["canny_low"])
        high = float(metadata["canny_high"])
        if low >= high:
            raise ValueError(
                "flux1_canny thresholds must satisfy canny_low < canny_high"
            )

    return ResolvedGenerationOptions(
        workflow_options=workflow,
        metadata=metadata,
    )


def metadata_from_workflow_options(
    engine: str,
    workflow_options: Mapping[str, object],
) -> dict[str, Any]:
    """Build canonical metadata from one fully resolved runner option set.

    Requiring every runner field prevents provenance from being reconstructed
    from a second, partially defaulted set of values.  The returned mapping is
    therefore guaranteed to describe the same effective options that are sent
    to the workflow writer.
    """
    if not isinstance(workflow_options, Mapping):
        raise TypeError("workflow_options must be a mapping")
    if engine not in SUPPORTED_ENGINES:
        supported = ", ".join(SUPPORTED_ENGINES)
        raise ValueError(f"Unsupported generation engine {engine!r}: {supported}")
    required = {
        spec.workflow_key
        for spec in ENGINE_FIELD_MAPS[engine]
        if spec.workflow_key is not None
    }
    if engine == "flux":
        required.add("flux_reference_mode")
    missing = sorted(key for key in required if key not in workflow_options)
    if missing:
        raise ValueError(
            f"Incomplete {engine} workflow options; missing: {', '.join(missing)}"
        )
    return resolve_generation_options(
        engine,
        configured_generation=None,
        overrides=workflow_options,
    ).metadata
