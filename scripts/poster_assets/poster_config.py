"""Configuration helpers shared by local poster-generation engines."""
from __future__ import annotations

from typing import Any

try:
    from .generation_contract import (
        JOINT_SCENE_CAST_MAX_MEGAPIXELS,
        JOINT_SCENE_IDENTITY_CANVAS_PX,
    )
    from .layout import resolve_layout_name
    from .poster_subject import resolve_poster_subject
except ImportError:
    from generation_contract import (
        JOINT_SCENE_CAST_MAX_MEGAPIXELS,
        JOINT_SCENE_IDENTITY_CANVAS_PX,
    )
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


def _safe_area_regions(manifest: dict[str, Any]) -> tuple[str, str]:
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
    return title_region, information_region


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

    title_region, information_region = _safe_area_regions(manifest)
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


def _compact_safe_area_sentence(
    manifest: dict[str, Any],
    scene: dict[str, Any],
) -> str:
    explicit = scene.get("safe_areas")
    if explicit is not None:
        return _text(
            explicit,
            "artwork.scene.safe_areas",
        )

    title_region, information_region = _safe_area_regions(manifest)
    if title_region == information_region:
        return (
            f"Keep the {title_region} cell open, low-detail, and low-contrast "
            "for its later overlay."
        )
    return (
        f"Keep the {title_region} and {information_region} cells open, "
        "low-detail, and low-contrast for later overlays."
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
    """Build one final-scene prompt from spatial and identity references."""
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
            build_spatial_identity_reference_prompt(
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
                "IMAGE 1 is the strict authority for count, pose, orientation, "
                "target scale, baseline, and poster position. The corresponding "
                "individual identity image is the strict authority for each "
                "character's exact silhouette shape, stature, anatomy, facial "
                "features, colors, markings, and defining design details. "
                "Permitted "
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
                "detail, and appendage from that character's individual identity "
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
    return format_joint_prompt_snapshot(
        build_joint_scene_prompt(
            manifest,
            scope_data,
            items,
            placement_contract=placement_contract,
        )
    )


def format_joint_prompt_snapshot(prompt: str) -> str:
    """Add the stable heading shared by saved and fingerprinted prompts."""
    return "\n\n".join(
        ("JOINT SCENE - ONE-SHOT FINAL SYNTHESIS", prompt.strip())
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
    if not items:
        raise ValueError("Joint-scene conditioning needs at least one subject")
    conditioning = manifest.get("conditioning", {})
    if not isinstance(conditioning, dict):
        raise ValueError("conditioning must be a mapping")
    identity_defaults = conditioning.get("identity_defaults", {})
    if not isinstance(identity_defaults, dict):
        raise ValueError("conditioning.identity_defaults must be a mapping")
    neutral = identity_defaults.get(
        "neutral_rgb",
        [226, 224, 211],
    )
    if (
        not isinstance(neutral, list)
        or len(neutral) != 3
        or not all(
            isinstance(value, int) and 0 <= value <= 255
            for value in neutral
        )
    ):
        raise ValueError(
            "conditioning.identity_defaults.neutral_rgb must contain "
            "3 RGB integers"
        )
    return {
        "reference_strategy": "spatial_cast_plus_unscaled_identity",
        "reference_neutral_rgb": neutral,
        "cast_max_megapixels": JOINT_SCENE_CAST_MAX_MEGAPIXELS,
        "identity_canvas_px": JOINT_SCENE_IDENTITY_CANVAS_PX,
        "identity_source_resampling": "none",
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
) -> str:
    """Describe the legacy edit workflow's identity and scene references."""
    if not items:
        raise ValueError("Identity reference mode needs at least one cutout")

    subject_count = len(items)
    scene_image_number = subject_count + 1
    descriptions = []
    regions = []

    for index, item in enumerate(items):
        image_number = index + 1
        name = item.get("name_en") or f"Pokemon #{item.get('pokemon_id', '?')}"
        region = reference_region_label(index, subject_count)
        regions.append(region)
        descriptions.append(
            f"IMAGE {image_number} is the exact appearance and anatomy reference "
            f"for {name} in the {region} region."
        )

    if subject_count == 1:
        region_summary = regions[0]
    else:
        region_summary = ", ".join(regions[:-1]) + f", or {regions[-1]}"

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
    specific_notes = subject_prompt_notes(items, manifest)
    if specific_notes:
        paragraphs.append(" ".join(specific_notes))
    return "\n\n".join(paragraphs)


def subject_prompt_notes(
    items: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> list[str]:
    """Return validated per-subject constraints in cast order."""
    specific_notes = []
    for item in items:
        name = item.get("name_en") or f"Pokemon #{item.get('pokemon_id', '?')}"
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
    return specific_notes


def build_spatial_identity_reference_prompt(
    items: list[dict[str, Any]],
    manifest: dict[str, Any],
    *,
    placement_contract: list[dict[str, int]],
) -> str:
    """Assign distinct spatial and identity roles to the joint references."""
    if not items:
        raise ValueError("Joint scene generation needs at least one cutout")
    if len(placement_contract) != len(items):
        raise ValueError(
            "Joint-scene placement contract must describe every subject"
        )

    regions = [
        reference_region_label(index, len(items))
        for index in range(len(items))
    ]
    region_summary = (
        regions[0]
        if len(regions) == 1
        else ", ".join(regions[:-1]) + f", or {regions[-1]}"
    )

    def percentage(value: int) -> str:
        if not isinstance(value, int) or not 0 <= value <= 1000:
            raise ValueError(
                "Joint-scene placement coordinates must be per-mille "
                "integers between 0 and 1000"
            )
        return f"{value / 10:.1f}%"

    coordinates = []
    identity_descriptions = []
    for index, (item, contract) in enumerate(
        zip(items, placement_contract, strict=True),
        start=2,
    ):
        if not isinstance(contract, dict):
            raise ValueError(
                "Joint-scene placement contract entries must be mappings"
            )
        name = item.get("name_en") or f"Pokemon #{item.get('pokemon_id', '?')}"
        identity_descriptions.append(
            f"IMAGE {index} is the exact identity and anatomy reference "
            f"for {name}."
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
            "IMAGE 1 is the sole spatial cast-layout reference. It contains exactly "
            f"{len(items)} complete characters on a flat neutral field, "
            f"ordered across the {region_summary} bottom-row regions. The "
            "reference is the authority only for character count, pose, "
            "orientation, relative scale, shared baseline, poster coordinates, "
            "and outer placement bounds. Its "
            "neutral field is empty reference space, not sky, terrain, a "
            "background plate, or a style request. Do not paste the "
            "characters as a foreground layer; redraw the complete scene "
            "and all character edges together from the empty target."
        ),
        (
            f"{' '.join(identity_descriptions)} Each identity image is the sole "
            "authority for that character's exact silhouette shape, stature, "
            "anatomy, facial features, colors, markings, appendages, and defining "
            "design details. Its centered position and scale on the neutral "
            "canvas carry no placement meaning and must not override IMAGE 1. "
            "These are detail views of the same cast already present in IMAGE 1, "
            "not additional subjects. Their neutral fields are empty reference "
            "space, not scenery."
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
    specific_notes = subject_prompt_notes(items, manifest)
    if specific_notes:
        paragraphs.append(" ".join(specific_notes))
    return "\n\n".join(paragraphs)


def build_sdxl_identity_control_prompt(
    manifest: dict[str, Any],
    scope_data: dict[str, Any],
    items: list[dict[str, Any]],
) -> str:
    """Build a compact CLIP prompt for regional SDXL identity control."""
    if not items:
        raise ValueError("SDXL identity control needs at least one subject")
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
            "linework, restrained natural colors, and atmospheric depth."
        ),
    )
    assignments = []
    for index, item in enumerate(items):
        name = item.get("name_en") or f"Pokemon #{item.get('pokemon_id', '?')}"
        assignments.append(
            f"{name} in the {reference_region_label(index, len(items))} "
            "bottom card"
        )

    paragraphs = [
        (
            f"Create one cohesive full-bleed illustration for {concept}. "
            f"{setting} {lighting} {rendering} "
            f"Render exactly {len(items)} complete characters once: "
            f"{'; '.join(assignments)}."
        ),
        (
            "The source-derived structural guide fixes character count, pose, "
            "orientation, scale, baseline, and card placement. Each regional "
            "identity reference belongs only to its named character and fixes "
            "that character's exact silhouette, stature, anatomy, face, "
            "colors, markings, appendages, and defining details. Preserve "
            "every referenced feature; never add, remove, merge, simplify, or "
            "reshape anatomy or markings. Keep every complete silhouette and "
            "appendage inside its assigned bottom-row card with visible "
            "landscape padding. The neutral reference fields, guide, masks, "
            "and card divisions are invisible controls, not scene content."
        ),
        (
            "Generate the final landscape and all characters together from an "
            "empty target in one unified denoising pass. There is no supplied "
            "background plate and no later character overlay, restoration, or "
            "composite. Ground contact, directional cast shadows, reflected "
            "light, perspective, color grading, and scene depth must agree "
            "naturally so the characters look native to the landscape."
        ),
        (
            "Use one physically coherent depth order. A genuinely nearer "
            "landscape element may continue naturally in front of a small "
            "non-defining exterior character edge, while farther scenery "
            "stays behind. A connected plant or branch must keep the same "
            "depth relationship along its visible length. Move or shorten "
            "scenery instead of hiding an identity-critical face, marking, "
            "limb, appendage, or silhouette detail."
        ),
        (
            f"{_safe_area_sentence(manifest, scene)} Fill every image edge "
            "naturally. Keep one continuous natural ground plane without "
            "character-specific clearings, paths, platforms, circles, halos, "
            "or landing pads. Draw no extra creature, person, trainer, "
            "character-shaped scenery, text, letters, numbers, logo, title "
            "art, box, plaque, panel, card border, UI, watermark, guide, or "
            "crop mark."
        ),
    ]
    constraints = _scene_constraints(scene)
    if constraints:
        paragraphs.append(" ".join(constraints))
    specific_notes = subject_prompt_notes(items, manifest)
    if specific_notes:
        paragraphs.append(" ".join(specific_notes))
    return "\n\n".join(paragraphs)


def build_dreamo_identity_prompt(
    manifest: dict[str, Any],
    scope_data: dict[str, Any],
    items: list[dict[str, Any]],
    *,
    placement_contract: list[dict[str, int]],
) -> str:
    """Build the isolated DreamO multi-reference poster prompt."""
    if not items:
        raise ValueError("DreamO identity control needs at least one subject")
    if len(placement_contract) != len(items):
        raise ValueError(
            "DreamO placement contract must describe every subject"
        )

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
            "linework, restrained natural colors, and atmospheric depth."
        ),
    )

    def percentage(value: object) -> str:
        if not isinstance(value, int) or not 0 <= value <= 1000:
            raise ValueError(
                "DreamO placement coordinates must be per-mille integers "
                "between 0 and 1000"
            )
        return f"{value / 10:.1f}%"

    placements = []
    references = []
    for index, (item, contract) in enumerate(
        zip(items, placement_contract, strict=True),
        start=1,
    ):
        if not isinstance(contract, dict):
            raise ValueError(
                "DreamO placement contract entries must be mappings"
            )
        name = item.get("name_en") or f"Pokemon #{item.get('pokemon_id', '?')}"
        region = reference_region_label(index - 1, len(items))
        references.append(
            f"REFERENCE {index} = {name}, {region} bottom card"
        )
        placements.append(
            (
                f"{name}: x {percentage(contract.get('left_per_mille'))} to "
                f"{percentage(contract.get('right_per_mille'))}, y "
                f"{percentage(contract.get('top_per_mille'))} to "
                f"{percentage(contract.get('bottom_per_mille'))}"
            )
        )

    paragraphs = [
        (
            f"References, fixed order: {'; '.join(references)}. Render exactly "
            f"one of each. Each image fixes its character's identity and "
            "complete design: pose, proportions, anatomy, silhouette, face, "
            "colors, markings, and appendages. Do not alter, add, or remove "
            "features. Neutral fields are empty."
        ),
        (
            f"Create {concept}. {setting} {lighting} {rendering}"
        ),
        (
            f"Bounds: {'; '.join(placements)}. Keep every complete silhouette, "
            "appendage, and visible landscape padding inside its respective "
            "bottom 3x3 card, below the row top and within its column. The "
            "grid and coordinates are invisible."
        ),
        (
            "Generate landscape and characters together from empty noise in "
            "one denoising pass; no plate, overlay, restoration, or composite. "
            "Use coherent ground contact, cast shadows, reflected light, "
            "perspective, linework, color, and depth so they belong there."
        ),
        (
            "Use consistent depth: near scenery may cover only a non-defining "
            "outer edge; far scenery stays behind. A plant, branch, or rock "
            "stays entirely in front or behind. Move it rather than hide a "
            "face, marking, limb, appendage, or defining silhouette."
        ),
        (
            f"{_compact_safe_area_sentence(manifest, scene)} Fill every edge "
            "with one "
            "continuous ground plane, without character-specific clearings, "
            "paths, platforms, halos, or landing pads. Draw no extra character "
            "or character-shaped scenery, text, logo, title, box, panel, "
            "border, watermark, guide, or crop mark."
        ),
    ]
    constraints = _scene_constraints(scene)
    if constraints:
        paragraphs.append(" ".join(constraints))
    specific_notes = subject_prompt_notes(items, manifest)
    if specific_notes:
        paragraphs.append(" ".join(specific_notes))
    return "\n\n".join(paragraphs)


def build_qwen_spatial_subject_prompt(
    manifest: dict[str, Any],
    scope_data: dict[str, Any],
    items: list[dict[str, Any]],
    *,
    placement_contract: list[dict[str, int]],
) -> str:
    """Build the isolated Qwen prompt for three spatial subject images."""
    if len(items) != 3:
        raise ValueError(
            "Qwen spatial-subject control requires exactly 3 subjects"
        )
    if len(placement_contract) != len(items):
        raise ValueError(
            "Qwen spatial-subject placement must describe every subject"
        )

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
            "linework, restrained natural colors, and atmospheric depth."
        ),
    )

    def percentage(value: object) -> str:
        if not isinstance(value, int) or not 0 <= value <= 1000:
            raise ValueError(
                "Qwen placement coordinates must be per-mille integers "
                "between 0 and 1000"
            )
        return f"{value / 10:.1f}%"

    assignments = []
    bounds = []
    for image_number, (item, contract) in enumerate(
        zip(items, placement_contract, strict=True),
        start=1,
    ):
        if not isinstance(contract, dict):
            raise ValueError(
                "Qwen placement contract entries must be mappings"
            )
        name = item.get("name_en") or f"Pokemon #{item.get('pokemon_id', '?')}"
        region = reference_region_label(image_number - 1, len(items))
        assignments.append(
            f"PICTURE {image_number} = {name}, {region} bottom card"
        )
        bounds.append(
            (
                f"{name}: x {percentage(contract.get('left_per_mille'))} to "
                f"{percentage(contract.get('right_per_mille'))}, y "
                f"{percentage(contract.get('top_per_mille'))} to "
                f"{percentage(contract.get('bottom_per_mille'))}"
            )
        )

    paragraphs = [
        (
            f"Three source pictures are supplied in fixed order: "
            f"{'; '.join(assignments)}. Each picture contains exactly one "
            "member of the same final cast, already at its required poster "
            "position and scale. Across all source pictures, each character "
            "appears exactly once. Combine them into one final image and "
            "render exactly these three characters once each. The identical "
            "plain neutral fields are empty coordinate space, not scenery, "
            "panels, cards, or separate backgrounds."
        ),
        (
            "Each source picture is the strict authority for its named "
            "character's pose, orientation, stature, proportions, silhouette, "
            "anatomy, face, colors, markings, appendages, and position. "
            "Preserve every defining feature. Do not add, remove, merge, "
            "simplify, enlarge, reshape, duplicate, or redesign any body part "
            "or marking."
        ),
        (
            f"Mandatory visible silhouette bounds: {'; '.join(bounds)}. Keep "
            "every complete character and appendage within its assigned "
            "bottom-row card with visible landscape padding. Match the shown "
            "baseline and scale. The coordinates and 3x3 card divisions are "
            "invisible and must never be drawn."
        ),
        (
            f"Create one cohesive full-bleed vertical illustration for "
            f"{concept}. {setting} {lighting} {rendering}"
        ),
        (
            "Generate the complete landscape and all three characters together "
            "from an empty target in one unified denoising pass. There is no "
            "background plate and no later overlay, restoration, mask repair, "
            "or composite. Use coherent ground contact, cast shadows, reflected "
            "light, perspective, linework, color grading, and depth so the "
            "characters look native to the landscape."
        ),
        (
            "Use one consistent depth order. Genuinely nearer scenery may cross "
            "only a small non-defining outer edge; farther scenery stays behind. "
            "A connected plant, leaf, branch, rock, or water edge must keep the "
            "same plausible front-or-behind relationship along its visible "
            "length. Move or shorten scenery instead of hiding a face, marking, "
            "limb, appendage, or defining silhouette."
        ),
        (
            f"{_compact_safe_area_sentence(manifest, scene)} Fill every edge "
            "with one continuous natural ground plane, without "
            "character-specific clearings, paths, platforms, circles, halos, "
            "or landing pads. Draw no extra creature, person, trainer, "
            "character-shaped scenery, text, letters, numbers, logo, title, "
            "box, plaque, panel, card border, UI, watermark, guide, or crop "
            "mark."
        ),
    ]
    constraints = _scene_constraints(scene)
    if constraints:
        paragraphs.append(" ".join(constraints))
    specific_notes = subject_prompt_notes(items, manifest)
    if specific_notes:
        paragraphs.append(" ".join(specific_notes))
    return "\n\n".join(paragraphs)
