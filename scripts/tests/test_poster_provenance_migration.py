import json
from pathlib import Path

import pytest

from scripts.poster_assets import migrate_poster_provenance as migration
from scripts.poster_assets.poster_io import PosterBundle
from scripts.poster_assets.provenance import fingerprint_record, sha256_file


def _fixture(tmp_path: Path):
    asset_dir = tmp_path / "Scope"
    cutout_dir = asset_dir / "cutouts"
    cutout_dir.mkdir(parents=True)
    cutout = cutout_dir / "pokemon_001.png"
    cutout.write_bytes(b"reviewed-cutout")
    (cutout_dir / "manifest.json").write_text(
        json.dumps(
            {
                "items": [
                    {
                        "pokemon_id": 1,
                        "file": cutout.name,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    manifest_path = asset_dir / "poster.yaml"
    manifest_path.write_text("scope: Scope\n", encoding="utf-8")
    bundle = PosterBundle(
        asset_key="Scope",
        scope="Scope",
        poster_id="Scope",
        section_id=None,
        asset_dir=asset_dir,
        manifest_path=manifest_path,
        manifest={
            "artwork": {
                "provenance_file": "poster-flux2-provenance.json",
            }
        },
        pdf_enabled=True,
        insertion="after_first_section_cover",
        artwork_file="poster-flux2-artwork.png",
    )
    provenance_path = asset_dir / "poster-flux2-provenance.json"
    provenance_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "kind": "promoted_poster",
                "scope": "Scope",
                "preview_language": "de",
                "run": {
                    "generation": {
                        "engine": "flux",
                        "mode": "identity_lock",
                    },
                    "inputs": {
                        "cutouts": [
                            {
                                "file": f"some/old/root/{cutout.name}",
                                "sha256": sha256_file(cutout),
                            }
                        ],
                        "references": [
                            {
                                "file": (
                                    "some/old/root/inpaint_reference.png"
                                ),
                            },
                            {
                                "file": (
                                    "some/old/root/"
                                    "upper_context_mask.png"
                                ),
                            },
                        ],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    return bundle, provenance_path, cutout


def _legacy_validation():
    return {
        "artwork": Path("artwork.png"),
        "preview": Path("preview.png"),
        "generation_fingerprint_current": None,
        "overlay_fingerprint_current": None,
    }


def test_migration_is_transactional_and_idempotent(tmp_path, monkeypatch):
    bundle, provenance_path, _cutout = _fixture(tmp_path)
    generation = fingerprint_record(
        {
            "kind": "generation",
            "pipeline_contract": {
                "name": "poster_generation",
                "version": 1,
            },
        }
    )
    overlay = fingerprint_record({"kind": "overlay"})

    def fake_validate(_bundle):
        payload = json.loads(provenance_path.read_text(encoding="utf-8"))
        inputs = payload["run"]["inputs"]
        if "generation_fingerprint" in inputs:
            return {
                **_legacy_validation(),
                "generation_fingerprint_current": True,
                "overlay_fingerprint_current": True,
            }
        return _legacy_validation()

    monkeypatch.setattr(migration, "validate", fake_validate)
    monkeypatch.setattr(
        migration,
        "_verify_current_overlay",
        lambda *_args: None,
    )
    monkeypatch.setattr(
        migration,
        "build_generation_fingerprint",
        lambda _bundle, **_kwargs: generation,
    )
    monkeypatch.setattr(
        migration,
        "build_overlay_fingerprint",
        lambda _bundle: overlay,
    )

    first = migration.migrate(bundle)
    after_first = provenance_path.read_bytes()
    second = migration.migrate(bundle)

    assert first["status"] == "migrated"
    assert second["status"] == "already_current"
    assert provenance_path.read_bytes() == after_first
    stored = json.loads(after_first)
    assert stored["run"]["inputs"]["generation_fingerprint"] == generation
    assert stored["run"]["inputs"]["overlay_fingerprint"] == overlay
    assert stored["run"]["inputs"]["semantic_fingerprint_migration"] == {
        "schema_version": 1,
        "origin": "backfilled_legacy",
        "generation_pipeline_contract_version": 1,
        "inferred_from": "recorded_reference_topology",
    }


def test_cutout_drift_refuses_migration_without_writing(tmp_path, monkeypatch):
    bundle, provenance_path, cutout = _fixture(tmp_path)
    before = provenance_path.read_bytes()
    cutout.write_bytes(b"changed-after-review")
    monkeypatch.setattr(
        migration,
        "validate",
        lambda _bundle: _legacy_validation(),
    )

    with pytest.raises(ValueError, match="Cutout record 1 differs"):
        migration.migrate(bundle)

    assert provenance_path.read_bytes() == before


def test_legacy_manifest_drift_refuses_migration_without_writing(
    tmp_path,
    monkeypatch,
):
    bundle, provenance_path, _cutout = _fixture(tmp_path)
    before = provenance_path.read_bytes()

    def reject_manifest_drift(_bundle):
        raise ValueError("Scope manifest drift")

    monkeypatch.setattr(migration, "validate", reject_manifest_drift)

    with pytest.raises(ValueError, match="Scope manifest drift"):
        migration.migrate(bundle)

    assert provenance_path.read_bytes() == before


def test_unknown_reference_topology_refuses_migration_without_writing(
    tmp_path,
    monkeypatch,
):
    bundle, provenance_path, _cutout = _fixture(tmp_path)
    payload = json.loads(provenance_path.read_text(encoding="utf-8"))
    payload["run"]["inputs"]["references"].append(
        {"file": "some/old/root/unreviewed_mask.png"}
    )
    provenance_path.write_text(json.dumps(payload), encoding="utf-8")
    before = provenance_path.read_bytes()
    monkeypatch.setattr(
        migration,
        "validate",
        lambda _bundle: pytest.fail("validation must not be reached"),
    )

    with pytest.raises(ValueError, match="unknown identity-lock"):
        migration.migrate(bundle)

    assert provenance_path.read_bytes() == before


def test_mislabeled_current_contract_is_rebuilt_as_historical_v1(
    tmp_path,
    monkeypatch,
):
    bundle, provenance_path, _cutout = _fixture(tmp_path)
    payload = json.loads(provenance_path.read_text(encoding="utf-8"))
    payload["run"]["inputs"]["generation_fingerprint"] = fingerprint_record(
        {
            "pipeline_contract": {
                "name": "poster_generation",
                "version": 2,
            }
        }
    )
    payload["run"]["inputs"]["overlay_fingerprint"] = fingerprint_record(
        {"kind": "overlay"}
    )
    provenance_path.write_text(json.dumps(payload), encoding="utf-8")
    corrected = fingerprint_record(
        {
            "pipeline_contract": {
                "name": "poster_generation",
                "version": 1,
            }
        }
    )
    monkeypatch.setattr(
        migration,
        "validate",
        lambda _bundle: {
            **_legacy_validation(),
            "generation_fingerprint_current": True,
            "overlay_fingerprint_current": True,
        },
    )
    monkeypatch.setattr(
        migration,
        "_verify_current_overlay",
        lambda *_args: None,
    )
    monkeypatch.setattr(
        migration,
        "build_generation_fingerprint",
        lambda _bundle, **_kwargs: corrected,
    )
    monkeypatch.setattr(
        migration,
        "build_overlay_fingerprint",
        lambda _bundle: fingerprint_record({"kind": "overlay"}),
    )

    result = migration.migrate(bundle)
    stored = json.loads(provenance_path.read_text(encoding="utf-8"))

    assert result["status"] == "migrated"
    assert (
        stored["run"]["inputs"]["generation_fingerprint"]
        ["components"]["pipeline_contract"]["version"]
        == 1
    )


def test_failed_post_write_validation_restores_legacy_record(
    tmp_path,
    monkeypatch,
):
    bundle, provenance_path, _cutout = _fixture(tmp_path)
    before = provenance_path.read_bytes()
    calls = 0

    def fake_validate(_bundle):
        nonlocal calls
        calls += 1
        if calls > 1:
            raise ValueError("post-write validation failed")
        return _legacy_validation()

    monkeypatch.setattr(migration, "validate", fake_validate)
    monkeypatch.setattr(
        migration,
        "_verify_current_overlay",
        lambda *_args: None,
    )
    monkeypatch.setattr(
        migration,
        "build_generation_fingerprint",
        lambda _bundle, **_kwargs: fingerprint_record(
            {
                "kind": "generation",
                "pipeline_contract": {
                    "name": "poster_generation",
                    "version": 1,
                },
            }
        ),
    )
    monkeypatch.setattr(
        migration,
        "build_overlay_fingerprint",
        lambda _bundle: fingerprint_record({"kind": "overlay"}),
    )

    with pytest.raises(ValueError, match="post-write validation failed"):
        migration.migrate(bundle)

    assert provenance_path.read_bytes() == before


def test_all_enabled_cli_uses_resolved_bundles(tmp_path, monkeypatch, capsys):
    bundle, provenance_path, _cutout = _fixture(tmp_path)
    monkeypatch.setattr(
        migration,
        "enabled_poster_bundles",
        lambda: [bundle],
    )
    monkeypatch.setattr(
        migration,
        "migrate",
        lambda selected: {
            "scope": selected.asset_key,
            "status": "already_current",
            "provenance": provenance_path,
        },
    )

    assert migration.main(["--all-enabled"]) == 0
    output = capsys.readouterr().out
    assert "Scope: already_current" in output
    assert str(provenance_path) in output
