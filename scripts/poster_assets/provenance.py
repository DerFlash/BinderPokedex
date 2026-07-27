"""Reproducible metadata for generated and promoted poster artwork."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image

try:
    from .layout import build_page_layout
    from .poster_config import (
        IDENTITY_LOCK_PROMPT_FILE,
        build_identity_lock_prompt,
        build_identity_reference_prompt,
        identity_lock_config,
    )
    from .poster_io import (
        SCOPE_DATA,
        PosterBundle,
        load_json,
        load_poster_scope_data,
        poster_bundle,
    )
except ImportError:
    from layout import build_page_layout
    from poster_config import (
        IDENTITY_LOCK_PROMPT_FILE,
        build_identity_lock_prompt,
        build_identity_reference_prompt,
        identity_lock_config,
    )
    from poster_io import (
        SCOPE_DATA,
        PosterBundle,
        load_json,
        load_poster_scope_data,
        poster_bundle,
    )


ROOT = Path(__file__).resolve().parents[2]
POSTER_ASSETS = ROOT / "data" / "poster_assets"
FINGERPRINT_SCHEMA_VERSION = 1
GENERATION_PIPELINE_CONTRACT_VERSION = 2
OVERLAY_PIPELINE_CONTRACT_VERSION = 1
SUPPORTED_GENERATION_PIPELINE_CONTRACT_VERSIONS = {
    ("flux", "identity_lock"): frozenset({1, 2}),
    ("flux", "edit"): frozenset({1}),
    ("flux", "generate"): frozenset({1}),
    ("flux", "inpaint"): frozenset({1}),
    ("anima", "edit"): frozenset({1}),
    ("anima", "generate"): frozenset({1}),
    ("flux1_canny", "generate"): frozenset({1}),
    ("qwen_edit", "edit"): frozenset({1}),
}
MODEL_DIRECTORIES = {
    "model": ("diffusion_models", "unet"),
    "encoder": ("text_encoders", "clip"),
    "encoder_2": ("text_encoders", "clip"),
    "vae": ("vae",),
    "controlnet": ("controlnet",),
    "lora": ("loras",),
    "upscale_model": ("upscale_models",),
}


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Return the SHA-256 digest of a file without loading it into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def model_artifact_path(
    comfy_root: Path,
    artifact: str,
    filename: str,
) -> Path:
    """Resolve one model exactly as a standard ComfyUI loader would."""
    relative = Path(filename)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Unsafe ComfyUI model filename: {filename!r}")
    model_root = (comfy_root / "models").resolve()
    candidates = [
        (model_root / directory / relative).resolve()
        for directory in MODEL_DIRECTORIES[artifact]
        if (model_root / directory / relative).is_file()
    ]
    candidates = [
        path for path in candidates if path.is_relative_to(model_root)
    ]
    if len(candidates) != 1:
        raise FileNotFoundError(
            f"Expected exactly one ComfyUI {artifact} named {filename!r}, "
            f"found {len(candidates)} below {model_root}"
        )
    return candidates[0]


def add_model_artifact_hashes(
    comfy_root: Path,
    generation: dict[str, Any],
) -> dict[str, Any]:
    """Hash the actual local model files selected for one workflow."""
    enriched = dict(generation)
    for artifact in MODEL_DIRECTORIES:
        filename = enriched.get(artifact)
        if filename:
            path = model_artifact_path(comfy_root, artifact, str(filename))
            enriched[f"{artifact}_sha256"] = sha256_file(path)
    return enriched


def required_model_artifact_hashes(
    generation: dict[str, Any],
) -> tuple[str, ...]:
    """Return hash fields for every model artifact the engine selects."""
    return tuple(
        f"{artifact}_sha256"
        for artifact in MODEL_DIRECTORIES
        if generation.get(artifact)
    )


def display_path(path: Path) -> str:
    """Use a repository-relative path without leaking machine-specific roots."""
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.name


def file_record(path: Path, *, image: bool = False) -> dict[str, Any]:
    """Describe one immutable input or output file."""
    if not path.is_file():
        raise FileNotFoundError(path)
    record: dict[str, Any] = {
        "file": display_path(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }
    if image:
        with Image.open(path) as loaded:
            record["width"] = loaded.width
            record["height"] = loaded.height
            dpi = loaded.info.get("dpi")
            if dpi:
                record["dpi"] = [round(float(value), 4) for value in dpi]
    return record


def _canonical_value(value: Any) -> Any:
    """Return a JSON-safe value with stable mapping-key semantics."""
    if isinstance(value, dict):
        normalized = {}
        for key, item in value.items():
            canonical_key = str(key)
            if canonical_key in normalized:
                raise ValueError(
                    "Canonical fingerprint mapping contains colliding keys: "
                    f"{key!r}"
                )
            normalized[canonical_key] = _canonical_value(item)
        return normalized
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(
        f"Unsupported canonical fingerprint value: {type(value).__name__}"
    )


def fingerprint_record(
    components: dict[str, Any],
    *,
    schema_version: int = FINGERPRINT_SCHEMA_VERSION,
) -> dict[str, Any]:
    """Build one versioned SHA-256 record from semantic components."""
    if not isinstance(schema_version, int) or schema_version <= 0:
        raise ValueError("Fingerprint schema_version must be positive")
    normalized = _canonical_value(components)
    payload = {
        "schema_version": schema_version,
        "components": normalized,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return {
        "schema_version": schema_version,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "components": normalized,
    }


def fingerprint_record_is_valid(record: object) -> bool:
    """Return whether a stored fingerprint is internally well formed."""
    if not isinstance(record, dict):
        return False
    schema_version = record.get("schema_version")
    components = record.get("components")
    expected = record.get("sha256")
    if (
        not isinstance(schema_version, int)
        or not isinstance(components, dict)
        or not isinstance(expected, str)
    ):
        return False
    try:
        rebuilt = fingerprint_record(
            components,
            schema_version=schema_version,
        )
    except (TypeError, ValueError):
        return False
    return rebuilt["sha256"] == expected


def current_generation_pipeline_contract_version(
    generation: dict[str, Any],
) -> int:
    """Return the current graph contract for the selected engine and mode."""
    if (
        generation.get("engine") == "flux"
        and generation.get("mode") == "identity_lock"
    ):
        return GENERATION_PIPELINE_CONTRACT_VERSION
    return 1


def validate_generation_pipeline_contract_version(
    generation: dict[str, Any],
    version: int,
) -> None:
    """Reject contracts outside the explicit compatibility policy."""
    family = (
        str(generation.get("engine", "")),
        str(generation.get("mode", "")),
    )
    supported = SUPPORTED_GENERATION_PIPELINE_CONTRACT_VERSIONS.get(family)
    if supported is None or version not in supported:
        raise ValueError(
            "Unsupported generation pipeline contract "
            f"{family[0]}/{family[1]} v{version}"
        )


def generation_fingerprint_pipeline_contract_version(
    record: dict[str, Any],
    generation: dict[str, Any] | None = None,
) -> int:
    """Read the historical graph contract represented by a fingerprint."""
    contract = record.get("components", {}).get("pipeline_contract")
    version = contract.get("version") if isinstance(contract, dict) else None
    if (
        not isinstance(version, int)
        or version <= 0
        or contract.get("name") != "poster_generation"
    ):
        raise ValueError(
            "Generation fingerprint lacks a valid pipeline contract"
        )
    if generation is not None:
        validate_generation_pipeline_contract_version(generation, version)
    return version


def image_pixel_record(
    path: Path,
    *,
    mode: str = "RGBA",
) -> dict[str, Any]:
    """Hash decoded image pixels instead of incidental PNG serialization."""
    if not path.is_file():
        raise FileNotFoundError(path)
    with Image.open(path) as loaded:
        image = loaded.convert(mode)
        width, height = image.size
        pixels = image.tobytes()
    header = json.dumps(
        {
            "height": height,
            "mode": mode,
            "width": width,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    digest = hashlib.sha256(
        b"binder-pokedex-image-pixels-v1\0"
        + header
        + b"\0"
        + pixels
    ).hexdigest()
    return {
        "mode": mode,
        "width": width,
        "height": height,
        "pixel_sha256": digest,
    }


def _bundle_and_scope_data(
    target: str | PosterBundle,
    *,
    poster_assets: Path | None,
    scope_data_dir: Path | None,
) -> tuple[PosterBundle, dict[str, Any]]:
    bundle = (
        target
        if isinstance(target, PosterBundle)
        else poster_bundle(
            target,
            poster_assets=poster_assets or POSTER_ASSETS,
        )
    )
    scope_data = load_poster_scope_data(
        bundle,
        scope_data_dir=scope_data_dir or SCOPE_DATA,
    )
    return bundle, scope_data


def _layout_generation_contract(
    manifest: dict[str, Any],
) -> dict[str, Any]:
    layout_name = str(
        manifest.get("layout", {}).get("name", "standard_3x3")
    )
    layout = build_page_layout(layout_name)
    text_cells = manifest.get("text_cells", {})
    if not isinstance(text_cells, dict):
        raise ValueError("text_cells must be a mapping")
    title = text_cells.get(
        "title",
        {"row": 1, "column": max(1, (layout.columns + 1) // 2)},
    )
    information = text_cells.get(
        "set_info",
        {
            "row": min(2, layout.rows),
            "column": max(1, (layout.columns + 1) // 2),
        },
    )
    if not isinstance(title, dict) or not isinstance(information, dict):
        raise ValueError("Poster text-cell configuration must be mappings")
    return {
        "name": layout.name,
        "columns": layout.columns,
        "rows": layout.rows,
        # Only positions condition the generated safe areas. Panel dimensions
        # are deterministic overlay inputs and intentionally live elsewhere.
        "safe_cells": {
            "title": {
                "row": int(title["row"]),
                "column": int(title["column"]),
            },
            "set_info": {
                "row": int(information["row"]),
                "column": int(information["column"]),
            },
        },
    }


def _featured_pokemon_ids(scope_data: dict[str, Any]) -> list[int]:
    selected: list[int] = []
    seen: set[int] = set()
    sections = scope_data.get("sections", {})
    values = (
        sections.values()
        if isinstance(sections, dict)
        else sections
        if isinstance(sections, list)
        else ()
    )
    for section in values:
        if not isinstance(section, dict):
            continue
        featured = (
            section.get("featured_elements")
            or section.get("featured_cards")
            or []
        )
        if not isinstance(featured, list):
            continue
        for item in featured:
            pokemon_id = (
                item.get("pokemon_id")
                if isinstance(item, dict)
                else None
            )
            if isinstance(pokemon_id, int) and pokemon_id not in seen:
                selected.append(pokemon_id)
                seen.add(pokemon_id)
    return selected


def _expected_subject_ids(
    manifest: dict[str, Any],
    scope_data: dict[str, Any],
) -> list[int]:
    pokemon = manifest.get("pokemon", {})
    if not isinstance(pokemon, dict):
        raise ValueError("pokemon must be a mapping")
    strategy = pokemon.get("strategy", "featured_from_scope")
    if strategy != "featured_from_scope":
        raise ValueError(f"Unsupported pokemon.strategy {strategy!r}")
    layout = build_page_layout(
        manifest.get("layout", {}).get("name", "standard_3x3")
    )
    count = pokemon.get("count", "auto_from_layout_columns")
    if count == "auto_from_layout_columns":
        requested = layout.columns
    elif isinstance(count, int) and count > 0:
        requested = count
    else:
        raise ValueError(
            "pokemon.count must be a positive integer or "
            "'auto_from_layout_columns'"
        )
    selected = _featured_pokemon_ids(scope_data)
    seen = set(selected)
    fallback = pokemon.get("fallback_candidates", [])
    if not isinstance(fallback, list):
        raise ValueError("pokemon.fallback_candidates must be a list")
    for item in fallback:
        pokemon_id = (
            item.get("pokemon_id")
            if isinstance(item, dict)
            else None
        )
        if isinstance(pokemon_id, int) and pokemon_id not in seen:
            selected.append(pokemon_id)
            seen.add(pokemon_id)
    if len(selected) < requested:
        raise ValueError(
            f"Layout needs {requested} Pokemon, but only "
            f"{len(selected)} were resolved"
        )
    return selected[:requested]


def _cutout_components(
    bundle: PosterBundle,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cutout_dir = bundle.asset_dir / "cutouts"
    manifest_path = cutout_dir / "manifest.json"
    payload = load_json(manifest_path)
    items = payload.get("items", [])
    if not isinstance(items, list) or not items:
        raise ValueError(f"No cutouts listed in {manifest_path}")
    normalized_items: list[dict[str, Any]] = []
    raw_items: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError(f"Invalid cutout item in {manifest_path}")
        pokemon_id = item.get("pokemon_id")
        filename = item.get("file")
        if not isinstance(pokemon_id, int) or not isinstance(filename, str):
            raise ValueError(f"Invalid cutout identity in {manifest_path}")
        relative = Path(filename)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Unsafe cutout file in {manifest_path}: {filename}")
        image_path = (cutout_dir / relative).resolve()
        if not image_path.is_relative_to(cutout_dir.resolve()):
            raise ValueError(f"Cutout escapes its asset directory: {filename}")
        normalized_items.append(
            {
                "pokemon_id": pokemon_id,
                **image_pixel_record(image_path),
            }
        )
        raw_items.append(item)
    return normalized_items, raw_items


def _effective_generation_prompt(
    bundle: PosterBundle,
    scope_data: dict[str, Any],
    generation: dict[str, Any],
    cutout_items: list[dict[str, Any]],
) -> str:
    engine = str(generation.get("engine", ""))
    mode = str(generation.get("mode", ""))
    if engine == "flux" and mode == "identity_lock":
        return build_identity_lock_prompt(bundle.manifest, scope_data)

    prompt_path = prompt_path_for_generation(
        bundle.asset_dir / "comfyui_poster",
        generation,
    )
    prompt = prompt_path.read_text(encoding="utf-8").strip()
    if not prompt:
        raise ValueError(f"Prompt is empty: {prompt_path}")
    if (
        engine == "flux"
        and mode == "edit"
        and generation.get("reference_mode") == "identity"
    ):
        prompt = "\n\n".join(
            (
                build_identity_reference_prompt(
                    cutout_items,
                    bundle.manifest,
                ),
                prompt,
            )
        )
    return prompt


def build_generation_fingerprint(
    target: str | PosterBundle,
    *,
    poster_assets: Path | None = None,
    scope_data_dir: Path | None = None,
    generation: dict[str, Any] | None = None,
    pipeline_contract_version: int | None = None,
) -> dict[str, Any]:
    """Fingerprint only inputs capable of changing generated poster pixels."""
    bundle, scope_data = _bundle_and_scope_data(
        target,
        poster_assets=poster_assets,
        scope_data_dir=scope_data_dir,
    )
    manifest = bundle.manifest
    artwork = manifest.get("artwork", {})
    if not isinstance(artwork, dict):
        raise ValueError("artwork must be a mapping")
    configured_generation = artwork.get("generation", {})
    effective_generation = (
        generation
        if generation is not None
        else configured_generation
    )
    if not isinstance(effective_generation, dict):
        raise ValueError("artwork.generation must be a mapping")
    contract_version = (
        current_generation_pipeline_contract_version(effective_generation)
        if pipeline_contract_version is None
        else pipeline_contract_version
    )
    if not isinstance(contract_version, int) or contract_version <= 0:
        raise ValueError("Pipeline contract version must be positive")
    validate_generation_pipeline_contract_version(
        effective_generation,
        contract_version,
    )
    cutouts, raw_cutout_items = _cutout_components(bundle)
    prompt = _effective_generation_prompt(
        bundle,
        scope_data,
        effective_generation,
        raw_cutout_items,
    )
    components = {
        "pipeline_contract": {
            "name": "poster_generation",
            "version": contract_version,
        },
        "layout": _layout_generation_contract(manifest),
        "scene": artwork.get("scene", {}),
        "identity_lock": identity_lock_config(manifest),
        "generation": effective_generation,
        "pokemon": manifest.get("pokemon", {}),
        "conditioning": manifest.get("conditioning", {}),
        "effective_prompt": {
            "encoding": "utf-8",
            "sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        },
        "source_subject_ids": _expected_subject_ids(manifest, scope_data),
        "cutouts": cutouts,
    }
    return fingerprint_record(components)


def _safe_overlay_asset(bundle: PosterBundle, filename: str) -> Path:
    relative = Path(filename)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Unsafe poster overlay asset: {filename!r}")
    path = (bundle.asset_dir / relative).resolve()
    if not path.is_relative_to(bundle.asset_dir.resolve()):
        raise ValueError(f"Poster overlay asset escapes its scope: {filename!r}")
    return path


def build_overlay_fingerprint(
    target: str | PosterBundle,
    *,
    poster_assets: Path | None = None,
    scope_data_dir: Path | None = None,
) -> dict[str, Any]:
    """Fingerprint cheap deterministic overlay inputs independently."""
    try:
        from .finalize_comfyui_poster import (
            SUPPORTED_LANGUAGES,
            info_panel_values,
            localized_value,
            title_logo_file,
        )
        from .typography import scope_title
    except ImportError:
        from finalize_comfyui_poster import (
            SUPPORTED_LANGUAGES,
            info_panel_values,
            localized_value,
            title_logo_file,
        )
        from typography import scope_title

    bundle, scope_data = _bundle_and_scope_data(
        target,
        poster_assets=poster_assets,
        scope_data_dir=scope_data_dir,
    )
    manifest = bundle.manifest
    content = manifest.get("text_content", {})
    if not isinstance(content, dict):
        raise ValueError("text_content must be a mapping")
    content_mode = str(content.get("mode", "set_summary"))
    configured_title = manifest.get("title_text")
    language_components: dict[str, Any] = {}
    logo_records: dict[str, Any] = {}
    for language in SUPPORTED_LANGUAGES:
        logo_file = title_logo_file(manifest, language)
        if logo_file:
            logo_path = _safe_overlay_asset(bundle, str(logo_file))
            logo_record = image_pixel_record(logo_path)
            logo_records[language] = logo_record
            title: dict[str, Any] = {
                "kind": "logo",
                "pixel_sha256": logo_record["pixel_sha256"],
            }
        else:
            title_value = (
                localized_value(configured_title, language)
                if configured_title is not None
                else scope_title(scope_data)
            )
            title = {"kind": "text", "value": title_value}
        language_components[language] = {
            "title": title,
            "information": list(
                info_panel_values(
                    scope_data,
                    language,
                    content_mode,
                )
            ),
        }
    components = {
        "pipeline_contract": {
            "name": "poster_overlay",
            "version": OVERLAY_PIPELINE_CONTRACT_VERSION,
        },
        "layout_name": manifest.get("layout", {}).get(
            "name",
            "standard_3x3",
        ),
        "text_cells": manifest.get("text_cells", {}),
        "text_content": content,
        "languages": language_components,
        "logo_pixels": logo_records,
    }
    return fingerprint_record(components)


def prompt_path_for_generation(
    work_dir: Path,
    generation: dict[str, Any],
    workflow_path: Path | None = None,
) -> Path:
    engine = str(generation.get("engine", ""))
    mode = str(generation.get("mode", ""))
    if engine == "anima":
        return work_dir / "anima_prompt.txt"
    if engine == "flux1_canny":
        return work_dir / "flux1_canny_prompt.txt"
    if engine == "qwen_edit":
        return work_dir / "qwen_edit_prompt.txt"
    if engine == "flux" and mode == "identity_lock":
        prompt_dir = workflow_path.parent if workflow_path is not None else work_dir
        return prompt_dir / IDENTITY_LOCK_PROMPT_FILE
    if engine == "flux" and mode == "inpaint":
        return work_dir / "inpaint_prompt.txt"
    if engine == "flux":
        return work_dir / "prompt.txt"
    raise ValueError(f"Unsupported provenance engine: {engine!r}")


def generation_input_records(
    scope: str,
    workflow_path: Path,
    generation: dict[str, Any],
) -> dict[str, Any]:
    """Collect the exact lightweight files that conditioned one generation."""
    scope_dir = POSTER_ASSETS / scope
    work_dir = scope_dir / "comfyui_poster"
    cutout_manifest_path = scope_dir / "cutouts" / "manifest.json"
    cutout_manifest = json.loads(cutout_manifest_path.read_text(encoding="utf-8"))
    cutouts = [
        file_record(scope_dir / "cutouts" / str(item["file"]), image=True)
        for item in cutout_manifest.get("items", [])
    ]
    if not cutouts:
        raise ValueError(f"No cutouts listed in {cutout_manifest_path}")

    if generation.get("engine") == "flux1_canny":
        references = [
            file_record(work_dir / "structure_reference.png", image=True),
        ]
    elif generation.get("engine") == "qwen_edit":
        references = [
            file_record(work_dir / "structure_reference.png", image=True),
            file_record(
                work_dir / "qwen_identity_reference_1.png",
                image=True,
            ),
            file_record(
                work_dir / "qwen_identity_reference_2.png",
                image=True,
            ),
        ]
    elif (
        generation.get("engine") == "flux"
        and generation.get("mode") == "identity_lock"
    ):
        references = [
            file_record(work_dir / "inpaint_reference.png", image=True),
            file_record(work_dir / "upper_context_mask.png", image=True),
            file_record(
                work_dir / "upper_context_generation_mask.png",
                image=True,
            ),
        ]
    elif generation.get("engine") == "flux" and generation.get("mode") == "inpaint":
        references = [
            file_record(work_dir / "inpaint_reference.png", image=True),
        ]
    else:
        references = [
            file_record(work_dir / "scene_reference.png", image=True)
        ]
    if (
        generation.get("engine") == "flux"
        and generation.get("mode") == "edit"
        and generation.get("reference_mode") == "identity"
    ):
        references.extend(
            file_record(path, image=True)
            for path in sorted(work_dir.glob("identity_reference_*.png"))
        )
    elif generation.get("engine") == "anima":
        if generation.get("mode") == "edit":
            references[0] = file_record(
                work_dir / "anima_scene_reference.png",
                image=True,
            )
        references.append(file_record(work_dir / "identity_core.png", image=True))

    return {
        "scope_manifest": file_record(scope_dir / "poster.yaml"),
        "prompt": file_record(
            prompt_path_for_generation(
                work_dir,
                generation,
                workflow_path,
            ),
        ),
        "cutout_manifest": file_record(cutout_manifest_path),
        "cutouts": cutouts,
        "references": references,
        "workflow": file_record(workflow_path),
    }


def write_run_metadata(
    scope: str,
    artwork_path: Path,
    workflow_path: Path,
    generation: dict[str, Any],
    output_path: Path | None = None,
    *,
    raw_artwork_path: Path | None = None,
    additional_workflows: dict[str, Path] | None = None,
    validation: dict[str, Any] | None = None,
) -> Path:
    """Write a sidecar for one generated, text-free candidate."""
    bundle = poster_bundle(scope, poster_assets=POSTER_ASSETS)
    output_path = output_path or artwork_path.with_suffix(".run.json")
    inputs = generation_input_records(scope, workflow_path, generation)
    inputs["generation_fingerprint"] = build_generation_fingerprint(
        bundle,
        generation=generation,
    )
    inputs["overlay_fingerprint"] = build_overlay_fingerprint(bundle)
    for label, path in (additional_workflows or {}).items():
        inputs[label] = file_record(path)
    payload = {
        "schema_version": 1,
        "kind": "poster_generation_run",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scope": scope,
        "source_scope": bundle.scope,
        "poster_id": bundle.poster_id,
        "section_id": bundle.section_id,
        "generation": generation,
        "inputs": inputs,
        "source_artwork": file_record(artwork_path, image=True),
    }
    if raw_artwork_path is not None:
        payload["raw_artwork"] = file_record(raw_artwork_path, image=True)
    if validation:
        payload["validation"] = validation
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def load_run_metadata(path: Path, artwork_path: Path) -> dict[str, Any]:
    """Load a run sidecar and verify that it belongs to the reviewed artwork."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1 or payload.get("kind") != (
        "poster_generation_run"
    ):
        raise ValueError(f"Unsupported poster run metadata: {path}")
    expected_hash = payload.get("source_artwork", {}).get("sha256")
    actual_hash = sha256_file(artwork_path)
    if expected_hash != actual_hash:
        raise ValueError(
            f"Run metadata does not describe {artwork_path}: "
            f"expected {expected_hash}, got {actual_hash}"
        )
    return payload


def promoted_provenance(
    *,
    scope: str,
    name: str,
    language: str,
    run_metadata: dict[str, Any],
    artwork_path: Path,
    preview_path: Path,
    card_paths: list[Path],
) -> dict[str, Any]:
    """Build the stable audit record for a complete promotion bundle."""
    stable_root = Path("data") / "poster_assets" / scope
    artwork_record = file_record(artwork_path, image=True)
    artwork_record["file"] = (
        stable_root / f"poster-{name}-artwork.png"
    ).as_posix()
    preview_record = file_record(preview_path, image=True)
    preview_record["file"] = (stable_root / f"poster-{name}.png").as_posix()
    card_records = []
    for card_path in card_paths:
        record = file_record(card_path, image=True)
        record["file"] = (
            stable_root / f"poster-{name}-cards" / card_path.name
        ).as_posix()
        card_records.append(record)
    return {
        "schema_version": 1,
        "kind": "promoted_poster",
        "promoted_at": datetime.now(timezone.utc).isoformat(),
        "scope": scope,
        "source_scope": run_metadata.get("source_scope", scope),
        "poster_id": run_metadata.get("poster_id", scope),
        "section_id": run_metadata.get("section_id"),
        "asset_name": name,
        "preview_language": language,
        "run": run_metadata,
        "outputs": {
            "artwork": artwork_record,
            "preview": preview_record,
            "cards": card_records,
        },
    }
