from pathlib import Path

from PIL import Image
import pytest

from scripts.poster_assets import run_comfyui_poster as runner


def _stub_generation_run(
    tmp_path: Path,
    monkeypatch,
    *,
    changed_source_pixel: bool = True,
) -> tuple[Path, dict[str, object]]:
    work_dir = tmp_path / "poster" / "comfyui_poster"
    output_dir = work_dir / "output"
    output_dir.mkdir(parents=True)

    reference = Image.new("RGBA", (8, 8), (20, 100, 180, 0))
    reference.putpixel((3, 4), (40, 120, 210, 255))
    reference.save(work_dir / "inpaint_reference.png")

    raw_path = output_dir / "candidate.png"
    raw = Image.new("RGB", reference.size, (80, 140, 90))
    raw.putpixel(
        (3, 4),
        (41 if changed_source_pixel else 40, 120, 210),
    )
    raw.save(raw_path)

    workflow_path = work_dir / "workflow.json"
    workflow_path.write_text("{}\n", encoding="utf-8")
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        runner,
        "prepare",
        lambda *_args, **_kwargs: work_dir,
    )
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
        lambda _root, generation: {
            **generation,
            **{
                f"{field}_sha256": "a" * 64
                for field in (
                    "model",
                    "encoder",
                    "vae",
                    "upscale_model",
                )
                if generation.get(field)
            },
        },
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
        captured["additional_workflows"] = kwargs.get(
            "additional_workflows"
        )
        return tmp_path / "candidate.run.json"

    monkeypatch.setattr(
        runner,
        "write_run_metadata",
        fake_write_run_metadata,
    )
    return raw_path, captured


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
            flux_mode="identity_lock",
            output_megapixels=0.25,
            output_dpi=None,
        )


def test_identity_lock_300dpi_uses_model_upscale_and_records_it(
    tmp_path: Path,
    monkeypatch,
):
    raw_path, captured = _stub_generation_run(
        tmp_path,
        monkeypatch,
        changed_source_pixel=False,
    )
    upscale_workflow = tmp_path / "upscale-workflow.json"
    upscale_calls = []

    def fake_upscale(scope, source, **kwargs):
        upscale_calls.append((scope, source, kwargs))
        return raw_path, upscale_workflow

    monkeypatch.setattr(runner, "upscale", fake_upscale)
    monkeypatch.setattr(
        runner,
        "resize_artwork_to_dpi",
        lambda *_args, **_kwargs: pytest.fail(
            "identity_lock must not use Lanczos for its 300-dpi output"
        ),
    )

    runner.run(
        "Example",
        123,
        0.25,
        "http://example.test",
        30,
        "en",
        engine="flux",
        flux_mode="identity_lock",
        output_megapixels=None,
        output_dpi=300,
        upscale_model="anime-upscaler.pth",
    )

    assert len(upscale_calls) == 1
    generation = captured["generation"]
    assert generation["output_method"] == "model_upscale"
    assert generation["output_dpi"] == 300
    assert generation["upscale_model"] == "anime-upscaler.pth"
    assert generation["upscale_model_sha256"] == "a" * 64
    assert captured["additional_workflows"] == {
        "upscale_workflow": upscale_workflow
    }
