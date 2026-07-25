"""Configuration helpers shared by local poster-generation engines."""
from __future__ import annotations

from typing import Any


def subject_conditioning(
    manifest: dict[str, Any], item: dict[str, Any]
) -> dict[str, Any]:
    """Return explicit conditioning overrides for one cutout-manifest item."""
    subjects = manifest.get("conditioning", {}).get("subjects", {})
    if not isinstance(subjects, dict):
        raise ValueError("conditioning.subjects must be a mapping")

    pokemon_id = item.get("pokemon_id")
    config = subjects.get(pokemon_id)
    if config is None:
        config = subjects.get(str(pokemon_id))
    if config is None:
        return {}
    if not isinstance(config, dict):
        raise ValueError(
            f"Conditioning for Pokemon #{pokemon_id} must be a mapping"
        )
    return config


def reference_region_label(index: int, count: int) -> str:
    """Describe a subject's invisible horizontal print-safe region."""
    if count == 1:
        return "center"
    if count == 2:
        return ("left", "right")[index]
    if count == 3:
        return ("left", "center", "right")[index]
    return f"column {index + 1} of {count}"


def build_identity_reference_prompt(
    items: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> str:
    """Build a model-facing reference contract without set-specific Python."""
    if not items:
        raise ValueError("Identity reference mode needs at least one cutout")

    subject_count = len(items)
    scene_image_number = subject_count + 1
    descriptions = []
    regions = []
    specific_notes = []

    for index, item in enumerate(items):
        image_number = index + 1
        name = item.get("name_en") or f"Pokemon #{item.get('pokemon_id', '?')}"
        region = reference_region_label(index, subject_count)
        regions.append(region)
        descriptions.append(
            f"IMAGE {image_number} is the exact appearance and anatomy reference "
            f"for {name} in the {region} region."
        )

        notes = subject_conditioning(manifest, item).get("prompt_notes", [])
        if isinstance(notes, str):
            notes = [notes]
        if not isinstance(notes, list) or not all(
            isinstance(note, str) for note in notes
        ):
            raise ValueError(
                f"prompt_notes for Pokemon #{item.get('pokemon_id')} "
                "must be a string or list of strings"
            )
        if notes:
            specific_notes.append(
                f"{name}-specific constraints: {' '.join(notes)}"
            )

    if subject_count == 1:
        region_summary = regions[0]
    else:
        region_summary = ", ".join(regions[:-1]) + f", or {regions[-1]}"

    paragraphs = [
        (
            f"{scene_image_number} reference images are supplied in a fixed "
            f"sequence. {' '.join(descriptions)} Their relative sizes on the "
            "neutral canvases reinforce, but never override, the scene scale "
            f"shown in IMAGE {scene_image_number}. Their plain backgrounds are "
            "empty reference space, not scenery."
        ),
        (
            f"IMAGE {scene_image_number} is the sole and final authority for the "
            "combined character count, poses, placement, scale, shared ground "
            "level, and invisible print-safe regions. Render each character "
            f"exactly once at IMAGE {scene_image_number}'s location. Every "
            "character, including its complete silhouette, must remain wholly "
            f"inside its assigned {region_summary} region of the bottom row. No "
            "character may cross above the bottom row or cross an invisible "
            "vertical region division. These divisions are coordinates only and "
            "must never be drawn. Leave visible landscape padding around every "
            "silhouette. The individual images are identity references, not "
            "additional subjects."
        ),
    ]
    if specific_notes:
        paragraphs.append(" ".join(specific_notes))
    return "\n\n".join(paragraphs)
