from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.poster_assets.render_job import (
    COMFYUI_COMMIT,
    prepare_job,
    sha256_file,
    validate_job,
)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def test_prepare_and_validate_portable_render_job(tmp_path: Path) -> None:
    workflow = tmp_path / "source_workflow.json"
    write_json(
        workflow,
        {
            "1": {
                "class_type": "LoadImage",
                "inputs": {"image": "scene.png"},
            }
        },
    )
    source = tmp_path / "scene.png"
    source.write_bytes(b"exact input")
    models_root = tmp_path / "models"
    model = models_root / "diffusion_models" / "model.safetensors"
    model.parent.mkdir(parents=True)
    model.write_bytes(b"exact model")

    job_dir = tmp_path / "job"
    manifest_path = prepare_job(
        workflow,
        job_dir,
        [f"{source}=scene.png"],
        [f"diffusion_models/model.safetensors={sha256_file(model)}"],
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["format_version"] == 1
    assert manifest["comfyui_commit"] == COMFYUI_COMMIT
    assert manifest["inputs"] == [
        {"path": "scene.png", "sha256": sha256_file(source)}
    ]
    assert validate_job(job_dir, models_root) == manifest


def test_validate_rejects_changed_render_input(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.json"
    write_json(
        workflow,
        {"1": {"class_type": "SaveImage", "inputs": {}}},
    )
    source = tmp_path / "scene.png"
    source.write_bytes(b"before")
    job_dir = tmp_path / "job"
    prepare_job(workflow, job_dir, [str(source)], [])
    (job_dir / "input" / "scene.png").write_bytes(b"after")

    with pytest.raises(ValueError, match="input SHA-256 mismatch"):
        validate_job(job_dir, tmp_path / "models")


def test_prepare_requires_every_load_image_input(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.json"
    write_json(
        workflow,
        {
            "1": {
                "class_type": "LoadImage",
                "inputs": {"image": "scene.png"},
            }
        },
    )

    with pytest.raises(ValueError, match="missing LoadImage inputs: scene.png"):
        prepare_job(workflow, tmp_path / "job", [], [])


@pytest.mark.parametrize(
    "spec",
    (
        "source.png=../escape.png",
        "source.png=/absolute.png",
    ),
)
def test_prepare_rejects_unsafe_input_destination(
    tmp_path: Path,
    spec: str,
) -> None:
    workflow = tmp_path / "workflow.json"
    write_json(
        workflow,
        {"1": {"class_type": "SaveImage", "inputs": {}}},
    )
    source = tmp_path / "source.png"
    source.write_bytes(b"input")
    expanded_spec = spec.replace("source.png", str(source), 1)

    with pytest.raises(ValueError, match="safe relative path"):
        prepare_job(workflow, tmp_path / "job", [expanded_spec], [])


def test_prepare_does_not_overwrite_existing_job(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.json"
    write_json(
        workflow,
        {"1": {"class_type": "SaveImage", "inputs": {}}},
    )
    job_dir = tmp_path / "job"
    prepare_job(workflow, job_dir, [], [])

    with pytest.raises(FileExistsError, match="already exists"):
        prepare_job(workflow, job_dir, [], [])
