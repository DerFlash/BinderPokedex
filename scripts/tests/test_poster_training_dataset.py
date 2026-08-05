from __future__ import annotations

import json
from pathlib import Path

from PIL import Image
import pytest

from scripts.poster_assets.provenance import image_pixel_record, sha256_file
from scripts.poster_assets.training_dataset import (
    compose_aligned_teacher_target,
    immutable_image_record,
    materialize_gold_dataset,
    pair_status,
    validate_audit_manifest,
)


REQUIRED_GATES = [
    "exact_cast_count",
    "identity_and_form",
    "silhouette_and_stature",
    "anatomy_and_face",
    "colors_and_markings",
    "placement_and_card_safety",
    "natural_scene_integration",
    "coherent_landscape_occlusion",
    "text_free_safe_areas",
]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def write_image(path: Path, color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (16, 16), color)
    image.putpixel((0, 0), tuple(255 - value for value in color))
    image.save(path)


def fixture_manifest(tmp_path: Path, *, status: str = "gold") -> Path:
    config_path = tmp_path / "config.json"
    config = {
        "schema_version": 1,
        "profile": "test",
        "image_contract": {
            "width": 16,
            "height": 16,
            "divisible_by": 16,
            "minimum_channel_stddev": 1.0,
        },
        "dataset_contract": {"required_review_gates": REQUIRED_GATES},
        "caption_variants": ["Integrate without changing the subjects."],
    }
    write_json(config_path, config)
    input_path = tmp_path / "input.png"
    target_path = tmp_path / "target.png"
    write_image(input_path, (10, 20, 30))
    write_image(target_path, (30, 40, 50))
    manifest_path = tmp_path / "audit.json"
    manifest = {
        "format_version": 1,
        "kind": "poster_edit_training_audit",
        "profile": "test",
        "config": {
            "file": "config.json",
            "sha256": sha256_file(config_path),
        },
        "summary": {},
        "samples": [
            {
                "id": "scene__input01",
                "scene_key": "scene",
                "scope": "scene",
                "proposed_split": "train_candidate",
                "review_status": status,
                "occlusion_class": "avoid",
                "input": immutable_image_record(input_path, root=tmp_path),
                "target": immutable_image_record(target_path, root=tmp_path),
                "target_visual_review_passed": True,
                "source_pixel_audit": {
                    "passed": True,
                    "input_sha256": sha256_file(input_path),
                },
                "review": {gate: True for gate in REQUIRED_GATES},
            }
        ],
    }
    write_json(manifest_path, manifest)
    return manifest_path


def test_pair_status_never_auto_approves_a_pair() -> None:
    assert pair_status(
        target_exists=True,
        target_review=True,
        target_excluded=False,
        input_errors=[],
        source_pixel_match=True,
    ) == "candidate_pair_review"


def test_pair_status_requires_a_fresh_exact_input() -> None:
    assert pair_status(
        target_exists=True,
        target_review=True,
        target_excluded=False,
        input_errors=[],
        source_pixel_match=False,
    ) == "needs_fresh_exact_input"


def test_compose_aligned_teacher_target_restores_exact_subjects(
    tmp_path: Path,
) -> None:
    scene_path = tmp_path / "scene.png"
    reference_path = tmp_path / "source.png"
    output_path = tmp_path / "target.png"
    Image.new("RGB", (16, 16), (20, 30, 40)).save(scene_path)
    source = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for x in range(6, 10):
        for y in range(5, 11):
            source.putpixel((x, y), (200, 100, 50, 255))
    source.save(reference_path)

    result = compose_aligned_teacher_target(
        scene_path,
        reference_path,
        output_path,
    )

    assert result["source_pixel_audit"]["passed"] is True
    assert result["source_pixel_audit"]["changed_pixels"] == 0
    with Image.open(output_path) as output:
        assert output.getpixel((0, 0)) == (20, 30, 40)
        assert output.getpixel((7, 7)) == (200, 100, 50)


def test_compose_aligned_teacher_target_is_immutable(tmp_path: Path) -> None:
    scene_path = tmp_path / "scene.png"
    reference_path = tmp_path / "source.png"
    output_path = tmp_path / "target.png"
    Image.new("RGB", (16, 16), (20, 30, 40)).save(scene_path)
    Image.new("RGBA", (16, 16), (200, 100, 50, 255)).save(reference_path)
    Image.new("RGB", (16, 16), (0, 0, 0)).save(output_path)

    with pytest.raises(FileExistsError, match="already exists"):
        compose_aligned_teacher_target(
            scene_path,
            reference_path,
            output_path,
        )


def test_materialize_gold_uses_ai_toolkit_pair_direction(tmp_path: Path) -> None:
    manifest_path = fixture_manifest(tmp_path)

    output_manifest = materialize_gold_dataset(
        manifest_path,
        tmp_path / "dataset",
        root=tmp_path,
    )

    value = json.loads(output_manifest.read_text(encoding="utf-8"))
    assert value["ai_toolkit"] == {
        "folder_path": "target",
        "control_path_1": "reference",
        "caption_ext": "txt",
        "match_target_res": True,
    }
    assert (tmp_path / "dataset/reference/scene__input01.png").is_file()
    assert (tmp_path / "dataset/target/scene__input01.png").is_file()
    assert (tmp_path / "dataset/target/scene__input01.txt").read_text(
        encoding="utf-8"
    ).startswith("Integrate")


def test_materialize_refuses_unreviewed_candidates(tmp_path: Path) -> None:
    manifest_path = fixture_manifest(
        tmp_path,
        status="candidate_pair_review",
    )

    with pytest.raises(ValueError, match="No gold samples"):
        materialize_gold_dataset(
            manifest_path,
            tmp_path / "dataset",
            root=tmp_path,
        )


def test_validation_accepts_an_explicitly_rejected_pair(tmp_path: Path) -> None:
    manifest_path = fixture_manifest(tmp_path, status="rejected_pair")

    result = validate_audit_manifest(manifest_path, root=tmp_path)

    assert result["samples"][0]["review_status"] == "rejected_pair"


def test_validation_rejects_changed_training_pixels(tmp_path: Path) -> None:
    manifest_path = fixture_manifest(tmp_path)
    Image.new("RGB", (16, 16), (200, 210, 220)).save(tmp_path / "input.png")

    with pytest.raises(ValueError, match="Stale sha256"):
        validate_audit_manifest(manifest_path, root=tmp_path)


def test_validation_rejects_exact_pixels_with_wrong_occlusion(
    tmp_path: Path,
) -> None:
    manifest_path = fixture_manifest(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sample = manifest["samples"][0]
    assert sample["source_pixel_audit"]["passed"] is True
    sample["review"]["coherent_landscape_occlusion"] = False
    write_json(manifest_path, manifest)

    with pytest.raises(
        ValueError,
        match="coherent_landscape_occlusion",
    ):
        validate_audit_manifest(manifest_path, root=tmp_path)


def test_validation_rejects_scene_leakage(tmp_path: Path) -> None:
    manifest_path = fixture_manifest(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    duplicate = dict(manifest["samples"][0])
    duplicate["id"] = "scene__input02"
    duplicate["proposed_split"] = "holdout"
    manifest["samples"].append(duplicate)
    write_json(manifest_path, manifest)

    with pytest.raises(ValueError, match="leaks across splits"):
        validate_audit_manifest(manifest_path, root=tmp_path)
