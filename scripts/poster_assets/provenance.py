"""Reproducible metadata for generated and promoted poster artwork."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
POSTER_ASSETS = ROOT / "data" / "poster_assets"
MODEL_DIRECTORIES = {
    "model": ("diffusion_models", "unet"),
    "encoder": ("text_encoders", "clip"),
    "vae": ("vae",),
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


def prompt_path_for_generation(
    work_dir: Path,
    generation: dict[str, Any],
) -> Path:
    engine = str(generation.get("engine", ""))
    mode = str(generation.get("mode", ""))
    if engine == "anima":
        return work_dir / "anima_prompt.txt"
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

    references = [file_record(work_dir / "scene_reference.png", image=True)]
    if generation.get("engine") == "flux" and generation.get(
        "reference_mode"
    ) == "identity":
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
            prompt_path_for_generation(work_dir, generation),
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
) -> Path:
    """Write a sidecar for one generated, text-free candidate."""
    output_path = output_path or artwork_path.with_suffix(".run.json")
    inputs = generation_input_records(scope, workflow_path, generation)
    for label, path in (additional_workflows or {}).items():
        inputs[label] = file_record(path)
    payload = {
        "schema_version": 1,
        "kind": "poster_generation_run",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scope": scope,
        "generation": generation,
        "inputs": inputs,
        "source_artwork": file_record(artwork_path, image=True),
    }
    if raw_artwork_path is not None:
        payload["raw_artwork"] = file_record(raw_artwork_path, image=True)
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
        "asset_name": name,
        "preview_language": language,
        "run": run_metadata,
        "outputs": {
            "artwork": artwork_record,
            "preview": preview_record,
            "cards": card_records,
        },
    }
