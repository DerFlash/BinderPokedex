"""Configuration helpers shared by local poster-generation engines."""
from __future__ import annotations

from typing import Any

try:
    from .layout import resolve_layout_name
    from .poster_subject import resolve_poster_subject
except ImportError:
    from layout import resolve_layout_name
    from poster_subject import resolve_poster_subject


IDENTITY_LOCK_PROMPT_FILE = "identity_lock_prompt.generated.txt"
JOINT_SCENE_PROMPT_FILE = "joint_scene_prompt.generated.txt"
DEFAULT_IDENTITY_LOCK = {
    "overscan_ratio": 0.04,
    "max_protected_start_ratio": 0.70,
    "transition_ratio": 0.10,
    "subject_clearance_ratio": 0.02,
}


def _mapping(value: object, path: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{path} must be a mapping")
    return value


def _text(value: object, path: str, *, default: str = "") -> str:
    if value is None:
        return default
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path} must be a non-empty string")
    return value.strip()


def _scene_constraints(scene: dict[str, Any]) -> list[str]:
    """Return validated scope-specific constraints for every scene pass."""
    constraints = scene.get("constraints", [])
    if isinstance(constraints, str):
        constraints = [constraints]
    if not isinstance(constraints, list) or not all(
        isinstance(item, str) and item.strip() for item in constraints
    ):
        raise ValueError(
            "artwork.scene.constraints must be a string or list of strings"
        )
    return [item.strip() for item in constraints]


def identity_lock_config(manifest: dict[str, Any]) -> dict[str, float]:
    """Return validated, scope-overridable source-pixel-lock geometry."""
    artwork = _mapping(manifest.get("artwork"), "artwork")
    configured = _mapping(
        artwork.get("identity_lock"),
        "artwork.identity_lock",
    )
    result = {
        key: float(configured.get(key, default))
        for key, default in DEFAULT_IDENTITY_LOCK.items()
    }
    if not 0.0 < result["overscan_ratio"] <= 0.20:
        raise ValueError(
            "artwork.identity_lock.overscan_ratio must be between 0 and 0.20"
        )
    if not 0.45 <= result["max_protected_start_ratio"] <= 0.85:
        raise ValueError(
            "artwork.identity_lock.max_protected_start_ratio must be "
            "between 0.45 and 0.85"
        )
    if not 0.02 <= result["transition_ratio"] <= 0.25:
        raise ValueError(
            "artwork.identity_lock.transition_ratio must be between 0.02 and 0.25"
        )
    if not 0.0 <= result["subject_clearance_ratio"] <= 0.10:
        raise ValueError(
            "artwork.identity_lock.subject_clearance_ratio must be "
            "between 0 and 0.10"
        )
    if (
        result["transition_ratio"]
        >= result["max_protected_start_ratio"]
    ):
        raise ValueError(
            "artwork.identity_lock.transition_ratio must be smaller than "
            "max_protected_start_ratio"
        )
    return result


def identity_lock_overscan(
    width: int,
    height: int,
    manifest: dict[str, Any],
) -> tuple[int, int]:
    """Return latent-aligned stage-one dimensions for any poster layout."""
    if width <= 0 or height <= 0:
        raise ValueError("Poster dimensions must be positive")
    ratio = identity_lock_config(manifest)["overscan_ratio"]

    def expanded(value: int) -> int:
        result = round((value * (1.0 + ratio)) / 16) * 16
        if result <= value:
            result = value + 16
        return result

    return expanded(width), expanded(height)


def _layout_region(
    row: int,
    column: int,
    rows: int,
    columns: int,
) -> str:
    if not 1 <= row <= rows or not 1 <= column <= columns:
        raise ValueError(
            f"Text cell ({row}, {column}) lies outside {columns}x{rows} layout"
        )

    if rows == 1:
        vertical = ""
    elif row == 1:
        vertical = "upper"
    elif row == rows:
        vertical = "lower"
    elif rows == 3 and row == 2:
        vertical = "middle"
    else:
        vertical = f"row-{row}"

    if columns == 1:
        horizontal = "center"
    elif columns == 2:
        horizontal = ("left", "right")[column - 1]
    elif columns == 3:
        horizontal = ("left", "center", "right")[column - 1]
    else:
        horizontal = f"column-{column}"
    return "-".join(part for part in (vertical, horizontal) if part)


def _safe_area_sentence(
    manifest: dict[str, Any],
    scene: dict[str, Any],
) -> str:
    explicit = scene.get("safe_areas")
    if explicit is not None:
        return _text(
            explicit,
            "artwork.scene.safe_areas",
        )

    layout_name = _mapping(manifest.get("layout"), "layout").get(
        "name",
        "standard_3x3",
    )
    layout = resolve_layout_name(str(layout_name))
    rows = int(layout["rows"])
    columns = int(layout["columns"])
    text_cells = _mapping(manifest.get("text_cells"), "text_cells")
    title = _mapping(
        text_cells.get("title", {"row": 1, "column": max(1, (columns + 1) // 2)}),
        "text_cells.title",
    )
    information = _mapping(
        text_cells.get(
            "set_info",
            {"row": min(2, rows), "column": max(1, (columns + 1) // 2)},
        ),
        "text_cells.set_info",
    )
    title_region = _layout_region(
        int(title["row"]),
        int(title["column"]),
        rows,
        columns,
    )
    information_region = _layout_region(
        int(information["row"]),
        int(information["column"]),
        rows,
        columns,
    )
    if title_region == information_region:
        return (
            f"Keep the entire {title_region} cell as uninterrupted, "
            "low-detail atmosphere with no object, emblem, signage, "
            "lettering, or high-contrast focal detail."
        )
    return (
        f"Keep the entire {title_region} cell as uninterrupted, low-detail "
        "atmosphere with no object, emblem, signage, lettering, or "
        f"high-contrast focal detail. Keep the {information_region} cell "
        "open and low contrast with no foreground object, structure, or "
        "focal subject."
    )


def _default_scene_concept(
    manifest: dict[str, Any],
    scope_data: dict[str, Any],
) -> str:
    set_name = str(
        scope_data.get("name")
        or manifest.get("scope")
        or "this card set"
    ).strip()
    series = str(
        scope_data.get("serie_name")
        or scope_data.get("serie")
        or ""
    ).strip()
    release_date = str(scope_data.get("release_date") or "").strip()
    year = release_date[:4] if len(release_date) >= 4 else ""
    details = f"the {set_name} expansion"
    if series and series.lower() not in set_name.lower():
        series_label = (
            series
            if series.lower().endswith("series")
            else f"{series} series"
        )
        details += f" from the {series_label}"
    if year.isdigit():
        details += f", released in {year}"
    return f"a creature-collecting card-set collection inspired by {details}"


def build_identity_lock_prompt(
    manifest: dict[str, Any],
    scope_data: dict[str, Any],
) -> str:
    """Build the production landscape prompt from one scope's creative brief.

    The manifest controls only the creative scene. The source-pixel contract,
    layout-safe regions, continuous-ground rule, and graphic exclusions remain
    centralized so a newly initialized scope cannot silently omit them.
    """
    artwork = _mapping(manifest.get("artwork"), "artwork")
    scene = _mapping(artwork.get("scene"), "artwork.scene")
    concept = _text(
        scene.get("concept"),
        "artwork.scene.concept",
        default=_default_scene_concept(manifest, scope_data),
    )
    setting = _text(
        scene.get("setting"),
        "artwork.scene.setting",
        default=(
            "The artwork contains a broad natural landscape whose terrain, "
            "flora, distant landmarks, and atmosphere subtly echo the set's "
            "theme without copying existing card art."
        ),
    )
    lighting = _text(
        scene.get("lighting"),
        "artwork.scene.lighting",
        default="Soft directional daylight enters from the upper left.",
    )
    rendering = _text(
        scene.get("rendering"),
        "artwork.scene.rendering",
        default=(
            "Use polished trading-card illustration, clean cel-painted "
            "linework, restrained natural colors, and gentle atmospheric depth."
        ),
    )
    ground_noun = _text(
        scene.get("ground_noun"),
        "artwork.scene.ground_noun",
        default="ground",
    )
    safe_areas = _safe_area_sentence(manifest, scene)
    additional = _scene_constraints(scene)

    opening = " ".join(
        part.strip()
        for part in (setting, lighting, rendering, *additional)
        if part.strip()
    )
    return "\n\n".join(
        (
            (
                "Create one cohesive full-bleed vertical scene for "
                f"{concept}. {opening}"
            ),
            (
                "The complete protected lower subject band is one continuous "
                f"low {ground_noun} surface with only short, low-contrast "
                "texture and soft horizontal shadows. It is a single natural "
                "ground plane, never separate clearings, halos, platforms, "
                "circles, or landing pads. Put no tall plants, flowers, rocks, "
                "bushes, branches, strong color patches, hard-edged shadows, "
                "vertical strokes, or isolated foreground objects in this "
                "lower band."
            ),
            (
                "If finished opaque source subjects are visible, they are the "
                "exact final cast and their final composition. Treat every "
                "source pixel as immutable. Build one consistent environment "
                "for them without replacing, continuing, tracing, redrawing, "
                "echoing, duplicating, or adding anatomy to them. Draw no "
                "additional living subject, face, eyes, body, mascot, animal, "
                "creature, person, trainer, statue, silhouette, or "
                "character-shaped plant anywhere."
            ),
            (
                "Fill the image naturally to every edge with no margin, page, "
                f"frame, or border. {safe_areas} The {ground_noun} is "
                "continuous, with no path or route. Do not draw text, letters, "
                "numbers, logos, title art, boxes, plaques, panels, cards, "
                "borders, UI, watermarks, or crop marks."
            ),
        )
    )


def build_joint_scene_prompt(
    manifest: dict[str, Any],
    scope_data: dict[str, Any],
    items: list[dict[str, Any]],
    *,
    placement_contract: list[dict[str, int]],
) -> str:
    """Build a one-shot whole-image prompt from appearance references only."""
    if not items:
        raise ValueError("Joint scene generation needs at least one subject")
    artwork = _mapping(manifest.get("artwork"), "artwork")
    scene = _mapping(artwork.get("scene"), "artwork.scene")
    concept = _text(
        scene.get("concept"),
        "artwork.scene.concept",
        default=_default_scene_concept(manifest, scope_data),
    )
    setting = _text(
        scene.get("setting"),
        "artwork.scene.setting",
        default=(
            "Build a broad natural landscape whose terrain, flora, distant "
            "landmarks, and atmosphere subtly echo the set's theme."
        ),
    )
    lighting = _text(
        scene.get("lighting"),
        "artwork.scene.lighting",
        default="Soft directional daylight enters from the upper left.",
    )
    rendering = _text(
        scene.get("rendering"),
        "artwork.scene.rendering",
        default=(
            "Use polished trading-card illustration, clean cel-painted "
            "linework, restrained natural colors, and gentle atmospheric depth."
        ),
    )
    ground_noun = _text(
        scene.get("ground_noun"),
        "artwork.scene.ground_noun",
        default="ground",
    )
    safe_areas = _safe_area_sentence(manifest, scene)
    additional = _scene_constraints(scene)
    final_scene_description = " ".join(
        part.strip()
        for part in (setting, lighting, rendering, *additional)
        if part.strip()
    )
    cast_names = [
        str(
            item.get("name_en")
            or f"Pokemon #{item.get('pokemon_id', '?')}"
        )
        for item in items
    ]
    if len(cast_names) == 1:
        cast = cast_names[0]
    else:
        cast = ", ".join(cast_names[:-1]) + f", and {cast_names[-1]}"

    return "\n\n".join(
        (
            build_identity_reference_prompt(
                items,
                manifest,
                placement_contract=placement_contract,
            ),
            (
                "Generate the complete final image in one unified denoising "
                "pass from an empty target. There is no supplied landscape "
                "image and no pre-generated background plate. Invent the "
                "landscape around the referenced characters from the first "
                "noise step, and synthesize every final landscape and character "
                "pixel together. There is no later character overlay, mask "
                "repair, silhouette restore, or cutout compositing. Ground "
                "contact, cast shadows, reflected light, color grading, "
                "perspective, and depth must therefore agree naturally."
            ),
            (
                f"Render exactly these {len(items)} characters once: {cast}. "
                "The individual reference images are the strict authority for "
                "identity, pose, stature, silhouette, anatomy, facial features, "
                "colors, markings, and defining design details. Permitted "
                "changes are limited to scene lighting, reflected color, cast "
                "shadow, and small physically plausible edge occlusions. Do "
                "not redesign, restyle, humanize, merge, duplicate, simplify, "
                "add, remove, enlarge, or reshape any referenced body part, "
                "appendage, marking, eye, or facial feature. Never invent a "
                "design trait that is absent from that subject's reference."
            ),
            (
                "Match every character's complete silhouette to the normalized "
                "bounding rectangle, scale, baseline, and visible landscape "
                "padding specified above; do not move or enlarge a character "
                "to fill its region. Copy every "
                "visible color boundary, marking contour, small anatomical "
                "detail, and appendage from that character's individual "
                "reference. Preserve every open negative "
                "space between limbs, body parts, or appendages: continuous "
                "landscape may remain visible through that gap, but do not "
                "enclose, outline, or fill it as a new body patch. When a small "
                "feature is ambiguous, preserve the reference instead of "
                "simplifying or inventing it."
            ),
            (
                f"Create one cohesive full-bleed scene for {concept}. "
                f"{final_scene_description} The characters and the {ground_noun} "
                "share one camera space and one globally coherent depth order. "
                "Resolve depth ordering explicitly at every "
                "landscape-character intersection. A blade, leaf, branch, rock, "
                "water edge, or other landscape element that is genuinely "
                "closer to the camera must continue naturally in front of the "
                "corresponding small exterior part of the character; never "
                "truncate that element exactly at the character silhouette and "
                "never paint the character as a flat top layer. A connected "
                "plant, leaf cluster, stem, branch, or other continuous object "
                "must keep the same physically plausible depth relationship "
                "along its visible length instead of arbitrarily switching from "
                "behind a character to in front of it. Landscape elements that "
                "are farther away remain naturally behind. If a closer element "
                "would hide an identity-critical body part, marking, facial "
                "feature, or silhouette detail, bend, move, shorten, lower, or "
                "regenerate that "
                "landscape element instead of placing the character over it. "
                "Keep defining anatomy and the print-safe silhouette readable."
            ),
            (
                f"{safe_areas} Keep one continuous natural {ground_noun} plane "
                "with no character-specific clearings, circles, platforms, "
                "landing pads, spotlight patches, or paths. Fill the image "
                "naturally to every edge. Do not draw extra creatures, people, "
                "trainers, character-shaped scenery, text, letters, numbers, "
                "logos, title art, boxes, plaques, panels, cards, borders, UI, "
                "watermarks, or crop marks."
            ),
        )
    )


def build_joint_prompt_snapshot(
    manifest: dict[str, Any],
    scope_data: dict[str, Any],
    items: list[dict[str, Any]],
    *,
    placement_contract: list[dict[str, int]],
) -> str:
    """Return the one-shot prompt as a stable provenance snapshot."""
    return "\n\n".join(
        (
            "JOINT SCENE - ONE-SHOT FINAL SYNTHESIS",
            build_joint_scene_prompt(
                manifest,
                scope_data,
                items,
                placement_contract=placement_contract,
            ),
        )
    )


def subject_conditioning(
    manifest: dict[str, Any], item: dict[str, Any]
) -> dict[str, Any]:
    """Return explicit conditioning overrides for one cutout-manifest item."""
    subjects = manifest.get("conditioning", {}).get("subjects", {})
    if not isinstance(subjects, dict):
        raise ValueError("conditioning.subjects must be a mapping")

    pokemon_id = item.get("pokemon_id")
    subject = resolve_poster_subject(item)
    keys: tuple[object, ...] = (
        subject.subject_key,
        subject.official_artwork_id,
        str(subject.official_artwork_id),
        pokemon_id,
        str(pokemon_id),
    )
    config = None
    for key in keys:
        if key in subjects:
            config = subjects[key]
            break
    if config is None:
        return {}
    if not isinstance(config, dict):
        raise ValueError(
            f"Conditioning for Pokemon #{pokemon_id} must be a mapping"
        )
    return config


def joint_scene_conditioning_contract(
    manifest: dict[str, Any],
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return only conditioning fields that affect joint-scene pixels."""
    conditioning = manifest.get("conditioning", {})
    if not isinstance(conditioning, dict):
        raise ValueError("conditioning must be a mapping")
    identity_defaults = conditioning.get("identity_defaults", {})
    if not isinstance(identity_defaults, dict):
        raise ValueError("conditioning.identity_defaults must be a mapping")
    effective_defaults = {
        "neutral_rgb": identity_defaults.get(
            "neutral_rgb",
            [226, 224, 211],
        ),
        "min_subject_px": int(
            identity_defaults.get("min_subject_px", 150)
        ),
        "max_subject_px": int(
            identity_defaults.get("max_subject_px", 350)
        ),
        "canvas_px": int(identity_defaults.get("canvas_px", 512)),
    }
    subjects = []
    for item in items:
        subject = resolve_poster_subject(item)
        config = subject_conditioning(manifest, item)
        identity = config.get("identity", {})
        if not isinstance(identity, dict):
            raise ValueError(
                f"Identity conditioning for {subject.subject_key} must be a "
                "mapping"
            )
        subjects.append(
            {
                "subject_key": subject.subject_key,
                "identity": {
                    "canvas_px": int(
                        identity.get(
                            "canvas_px",
                            effective_defaults["canvas_px"],
                        )
                    )
                },
            }
        )
    return {
        "identity_defaults": effective_defaults,
        "subjects": subjects,
    }


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
    *,
    placement_contract: list[dict[str, int]] | None = None,
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

    if placement_contract is None:
        paragraphs = [
            (
                f"{scene_image_number} reference images are supplied in a fixed "
                f"sequence. {' '.join(descriptions)} Their relative sizes on "
                "the neutral canvases reinforce, but never override, the scene "
                f"scale shown in IMAGE {scene_image_number}. Their plain "
                "backgrounds are empty reference space, not scenery."
            ),
            (
                f"IMAGE {scene_image_number} is the sole and final authority for "
                "the combined character count, poses, placement, scale, shared "
                "ground level, and invisible print-safe regions. Render each "
                f"character exactly once at IMAGE {scene_image_number}'s "
                "location. Every character, including its complete silhouette, "
                f"must remain wholly inside its assigned {region_summary} region "
                "of the bottom row. No character may cross above the bottom row "
                "or cross an invisible vertical region division. These "
                "divisions are coordinates only and must never be drawn. Leave "
                "visible landscape padding around every silhouette. The "
                "individual images are identity references, not additional "
                "subjects."
            ),
        ]
    else:
        if len(placement_contract) != subject_count:
            raise ValueError(
                "Joint-scene placement contract must describe every subject"
            )

        def percentage(value: int) -> str:
            if not isinstance(value, int) or not 0 <= value <= 1000:
                raise ValueError(
                    "Joint-scene placement coordinates must be per-mille "
                    "integers between 0 and 1000"
                )
            return f"{value / 10:.1f}%"

        coordinates = []
        for item, contract in zip(
            items,
            placement_contract,
            strict=True,
        ):
            if not isinstance(contract, dict):
                raise ValueError(
                    "Joint-scene placement contract entries must be mappings"
                )
            name = (
                item.get("name_en")
                or f"Pokemon #{item.get('pokemon_id', '?')}"
            )
            coordinates.append(
                (
                    f"{name}: x {percentage(contract['left_per_mille'])} to "
                    f"{percentage(contract['right_per_mille'])}, y "
                    f"{percentage(contract['top_per_mille'])} to "
                    f"{percentage(contract['bottom_per_mille'])}"
                )
            )
        paragraphs = [
            (
                f"{subject_count} identity reference images are supplied in a "
                "fixed "
                f"sequence. {' '.join(descriptions)} Their neutral canvases are "
                "identity and pose evidence with deliberately generous empty "
                "padding that reinforces a restrained final scale. The "
                "normalized rectangles below remain the final authority. No "
                "scene, background, or combined character composition image is "
                "supplied."
            ),
            (
                "The following normalized target silhouette rectangles are the "
                "mandatory placement and scale contract: "
                f"{'; '.join(coordinates)}. Match every complete silhouette, "
                "baseline, and surrounding landscape clearance to these bounds "
                "within two percent of the full canvas. Each rectangle is a "
                "hard outer limit for every visible pixel of that character, "
                "including every outermost referenced detail and appendage; do "
                "not crop or extend any part beyond it. Render each character "
                f"exactly once in its assigned {region_summary} bottom-row "
                "region. No character may cross above the bottom row or an "
                "invisible vertical region division. The coordinates and "
                "divisions must never be drawn."
            ),
        ]
    if specific_notes:
        paragraphs.append(" ".join(specific_notes))
    return "\n\n".join(paragraphs)
