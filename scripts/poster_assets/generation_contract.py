"""Cross-cutting invariants for poster generation metadata."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


CANONICAL_REFERENCE_MODES = {
    ("flux", "identity_lock"): "two_pass_source_pixels",
    ("flux", "inpaint"): "source_pixels",
    ("flux", "joint_scene"): "multi_reference_joint",
}


def is_joint_scene_generation(
    generation: Mapping[str, Any],
) -> bool:
    """Return whether metadata describes the unified FLUX scene redraw."""
    return (
        generation.get("engine") == "flux"
        and generation.get("mode") == "joint_scene"
    )


def validate_generation_reference_contract(
    generation: Mapping[str, Any],
) -> None:
    """Require each protected FLUX mode's canonical reference semantics."""
    key = (generation.get("engine"), generation.get("mode"))
    expected = CANONICAL_REFERENCE_MODES.get(key)
    if expected is None:
        return
    actual = generation.get("reference_mode")
    if actual != expected:
        raise ValueError(
            "Generation reference contract is incompatible with "
            f"{key[0]}/{key[1]}: expected {expected!r}, got {actual!r}"
        )


def validate_generation_output_contract(
    generation: Mapping[str, Any],
) -> None:
    """Prevent semantic post-processing after a unified final scene pass."""
    if not is_joint_scene_generation(generation):
        return
    output_method = generation.get("output_method")
    if output_method is None:
        conflicting = tuple(
            field
            for field in (
                "output_dpi",
                "output_megapixels",
                "upscale_model",
                "upscale_model_sha256",
            )
            if generation.get(field) is not None
        )
        if conflicting:
            raise ValueError(
                "flux/joint_scene output fields require output_method: "
                f"{', '.join(conflicting)}"
            )
        return
    if output_method != "lanczos":
        raise ValueError(
            "flux/joint_scene requires deterministic Lanczos output; a "
            "learned model upscaler could alter reviewed character identity"
        )
    output_dpi = generation.get("output_dpi")
    output_megapixels = generation.get("output_megapixels")
    has_dpi = output_dpi is not None
    has_megapixels = output_megapixels is not None
    if has_dpi == has_megapixels:
        raise ValueError(
            "flux/joint_scene Lanczos output requires exactly one of "
            "output_dpi or output_megapixels"
        )
    if has_dpi and (
        not isinstance(output_dpi, int)
        or isinstance(output_dpi, bool)
        or output_dpi <= 0
    ):
        raise ValueError(
            "flux/joint_scene output_dpi must be a positive integer"
        )
    if has_megapixels and (
        not isinstance(output_megapixels, (int, float))
        or isinstance(output_megapixels, bool)
        or output_megapixels <= 0
    ):
        raise ValueError(
            "flux/joint_scene output_megapixels must be positive"
        )
    forbidden = tuple(
        field
        for field in ("upscale_model", "upscale_model_sha256")
        if generation.get(field) is not None
    )
    if forbidden:
        raise ValueError(
            "flux/joint_scene Lanczos output must not select a learned "
            f"upscaler: {', '.join(forbidden)}"
        )


def validate_generation_contract(
    generation: Mapping[str, Any],
) -> None:
    """Validate all generation invariants shared across entry points."""
    if not isinstance(generation, Mapping):
        raise TypeError("generation must be a mapping")
    validate_generation_reference_contract(generation)
    validate_generation_output_contract(generation)


def requires_generation_fingerprint(
    generation: Mapping[str, Any],
) -> bool:
    """Return whether legacy, unfingerprinted provenance is impossible."""
    return is_joint_scene_generation(generation)
