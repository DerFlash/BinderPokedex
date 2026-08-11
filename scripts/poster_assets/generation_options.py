"""Resolve the effective FLUX.2 poster-generation contract."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

try:
    from .generation_contract import (
        CANONICAL_REFERENCE_MODES,
        SUPPORTED_REFERENCE_MODES,
    )
except ImportError:  # Direct script execution
    from generation_contract import (
        CANONICAL_REFERENCE_MODES,
        SUPPORTED_REFERENCE_MODES,
    )


SUPPORTED_ENGINE = "flux"
SUPPORTED_FLUX_MODES = ("joint_scene", "identity_lock")

DEFAULT_FLUX_MODEL = "flux-2-klein-4b-fp8.safetensors"
DEFAULT_FLUX_ENCODER = "qwen_3_4b.safetensors"
DEFAULT_FLUX_VAE = "flux2-vae.safetensors"
DEFAULT_FLUX_MODE = "joint_scene"
DEFAULT_FLUX_STEPS = 4


@dataclass(frozen=True)
class ResolvedGenerationOptions:
    """Effective builder values and their canonical provenance metadata."""

    workflow_options: dict[str, Any]
    metadata: dict[str, Any]


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty text")
    return value.strip()


def _positive_int(value: object, label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a positive integer")
    try:
        converted = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} must be a positive integer") from error
    if converted <= 0 or (
        isinstance(value, float) and not value.is_integer()
    ):
        raise ValueError(f"{label} must be a positive integer")
    return converted


def _configured_flux(
    configured_generation: Mapping[str, object] | None,
) -> Mapping[str, object]:
    if configured_generation is None:
        return {}
    if not isinstance(configured_generation, Mapping):
        raise TypeError("configured_generation must be a mapping or None")
    engine = configured_generation.get("engine", SUPPORTED_ENGINE)
    if engine != SUPPORTED_ENGINE:
        raise ValueError(
            "Only the FLUX.2 poster engine is supported; "
            f"configured engine was {engine!r}"
        )
    return configured_generation


def _override(
    manifest: Mapping[str, object],
    overrides: Mapping[str, object],
    manifest_key: str,
    override_key: str,
    default: object,
) -> object:
    value = manifest.get(manifest_key, default)
    explicit = overrides.get(override_key)
    return explicit if explicit is not None else value


def resolve_generation_options(
    engine: str = SUPPORTED_ENGINE,
    configured_generation: Mapping[str, object] | None = None,
    overrides: Mapping[str, object] | None = None,
) -> ResolvedGenerationOptions:
    """Resolve the only supported engine and its two reviewed modes."""
    if engine != SUPPORTED_ENGINE:
        raise ValueError(
            f"Unsupported generation engine {engine!r}; only 'flux' is supported"
        )
    if overrides is None:
        overrides = {}
    elif not isinstance(overrides, Mapping):
        raise TypeError("overrides must be a mapping or None")

    manifest = _configured_flux(configured_generation)
    model = _text(
        _override(
            manifest,
            overrides,
            "model",
            "flux_model",
            DEFAULT_FLUX_MODEL,
        ),
        "flux.model",
    )
    encoder = _text(
        _override(
            manifest,
            overrides,
            "encoder",
            "flux_clip",
            DEFAULT_FLUX_ENCODER,
        ),
        "flux.encoder",
    )
    vae = _text(
        _override(
            manifest,
            overrides,
            "vae",
            "flux_vae",
            DEFAULT_FLUX_VAE,
        ),
        "flux.vae",
    )
    mode = _text(
        _override(
            manifest,
            overrides,
            "mode",
            "flux_mode",
            DEFAULT_FLUX_MODE,
        ),
        "flux.mode",
    )
    if mode not in SUPPORTED_FLUX_MODES:
        expected = ", ".join(SUPPORTED_FLUX_MODES)
        raise ValueError(f"flux.mode must be one of: {expected}")
    steps = _positive_int(
        _override(
            manifest,
            overrides,
            "steps",
            "flux_steps",
            DEFAULT_FLUX_STEPS,
        ),
        "flux.steps",
    )
    configured_mode = manifest.get("mode")
    explicit_reference_mode = overrides.get("flux_reference_mode")
    if explicit_reference_mode is not None:
        reference_mode = _text(
            explicit_reference_mode,
            "flux.reference_mode",
        )
    elif configured_mode == mode and manifest.get("reference_mode") is not None:
        reference_mode = _text(
            manifest["reference_mode"],
            "flux.reference_mode",
        )
    else:
        reference_mode = CANONICAL_REFERENCE_MODES[
            (SUPPORTED_ENGINE, mode)
        ]
    supported_reference_modes = SUPPORTED_REFERENCE_MODES[
        (SUPPORTED_ENGINE, mode)
    ]
    if reference_mode not in supported_reference_modes:
        expected = ", ".join(sorted(supported_reference_modes))
        raise ValueError(
            "flux.reference_mode is incompatible with mode "
            f"{mode!r}: expected one of {expected}, got "
            f"{reference_mode!r}"
        )

    return ResolvedGenerationOptions(
        workflow_options={
            "flux_model": model,
            "flux_clip": encoder,
            "flux_vae": vae,
            "flux_mode": mode,
            "flux_reference_mode": reference_mode,
            "flux_steps": steps,
        },
        metadata={
            "engine": SUPPORTED_ENGINE,
            "model": model,
            "encoder": encoder,
            "vae": vae,
            "mode": mode,
            "steps": steps,
            "reference_mode": reference_mode,
        },
    )


def metadata_from_workflow_options(
    engine: str,
    workflow_options: Mapping[str, object],
) -> dict[str, Any]:
    """Rebuild provenance from the exact values passed to the builder."""
    if not isinstance(workflow_options, Mapping):
        raise TypeError("workflow_options must be a mapping")
    required = {
        "flux_model",
        "flux_clip",
        "flux_vae",
        "flux_mode",
        "flux_steps",
    }
    missing = sorted(required - workflow_options.keys())
    if missing:
        raise ValueError(
            "Incomplete flux workflow options; missing: "
            f"{', '.join(missing)}"
        )
    return resolve_generation_options(
        engine,
        configured_generation=None,
        overrides=workflow_options,
    ).metadata
