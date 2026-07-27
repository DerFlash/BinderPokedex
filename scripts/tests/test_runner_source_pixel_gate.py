from pathlib import Path

from PIL import Image
import pytest

from scripts.poster_assets import run_comfyui_poster as runner


def _stub_generation_run(
    tmp_path: Path,
    monkeypatch,
) -> tuple[Path, dict[str, object]]:
    work_dir = tmp_path / "poster" / "comfyui_poster"
    output_dir = work_dir / "output"
    output_dir.mkdir(parents=True)

    reference = Image.new("RGBA", (8, 8), (20, 100, 180, 0))
    reference.putpixel((3, 4), (40, 120, 210, 255))
    reference.save(work_dir / "inpaint_reference.png")

    raw_path = output_dir / "candidate.png"
    raw = Image.new("RGB", reference.size, (80, 140, 90))
    raw.putpixel((3, 4), (41, 120, 210))
    raw.save(raw_path)

    workflow_path = work_dir / "workflow.json"
    workflow_path.write_text("{}\n", encoding="utf-8")
    captured: dict[str, object] = {}

    monkeypatch.setattr(runner, "prepare", lambda *_args: work_dir)
    monkeypatch.setattr(
        runner,
        "validate_server_input_directory",
        lambda *_args: None,
    )
    monkeypatch.setattr(
        runner,
        "server_comfyui_root",
        lambda *_args: tmp_path / "ComfyUI",
    )
    monkeypatch.setattr(
        runner,
        "write_engine_workflow",
        lambda *_args, **_kwargs: workflow_path,
    )
    monkeypatch.setattr(
        runner,
        "queue_workflow",
        lambda *_args, **_kwargs: [
            {
                "type": "output",
                "subfolder": "",
                "filename": raw_path.name,
            }
        ],
    )
    monkeypatch.setattr(runner, "validate_raw_artwork", lambda *_args: None)
    monkeypatch.setattr(
        runner,
        "resize_artwork",
        lambda _scope, source, _destination, _megapixels: source,
    )
    monkeypatch.setattr(runner, "finalize", lambda *_args: None)
    monkeypatch.setattr(runner, "slice_poster", lambda *_args: [])
    monkeypatch.setattr(
        runner,
        "add_model_artifact_hashes",
        lambda _root, generation: generation,
    )

    def fake_write_run_metadata(
        _scope,
        _artwork,
        _workflow,
        generation,
        **kwargs,
    ):
        captured["generation"] = generation
        captured["validation"] = kwargs["validation"]
        return tmp_path / "candidate.run.json"

    monkeypatch.setattr(
        runner,
        "write_run_metadata",
        fake_write_run_metadata,
    )
    return raw_path, captured


def test_alternative_engine_records_failed_source_audit_without_hiding_output(
    tmp_path: Path,
    monkeypatch,
):
    raw_path, captured = _stub_generation_run(tmp_path, monkeypatch)

    result = runner.run(
        "Example",
        123,
        0.25,
        "http://example.test",
        30,
        "en",
        engine="qwen_edit",
        output_megapixels=0.25,
        output_dpi=None,
    )

    assert result[0] == raw_path
    audit = captured["validation"]["source_pixels"]
    assert {
        key: audit[key]
        for key in (
            "method",
            "opaque_pixels",
            "changed_pixels",
            "changed_bbox",
            "passed",
            "stage",
            "width",
            "height",
        )
    } == {
        "method": "exact_opaque_source_pixels",
        "opaque_pixels": 1,
        "changed_pixels": 1,
        "changed_bbox": (3, 4, 4, 5),
        "passed": False,
        "stage": "raw_generation",
        "width": 8,
        "height": 8,
    }
    assert audit["artwork_sha256"] == runner.sha256_file(raw_path)
    assert audit["reference_sha256"] == runner.sha256_file(
        raw_path.parent.parent / "inpaint_reference.png"
    )
    assert captured["generation"]["engine"] == "qwen_edit"


def test_production_identity_lock_aborts_on_the_same_changed_source_pixel(
    tmp_path: Path,
    monkeypatch,
):
    _stub_generation_run(tmp_path, monkeypatch)

    with pytest.raises(RuntimeError, match="1 of 1 fully opaque pixels changed"):
        runner.run(
            "Example",
            123,
            0.25,
            "http://example.test",
            30,
            "en",
            engine="flux",
            output_megapixels=0.25,
            output_dpi=None,
        )
