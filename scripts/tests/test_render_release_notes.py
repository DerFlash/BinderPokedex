import json
from pathlib import Path

import yaml

from scripts.release.build_manifest import LANGUAGES, main as build_manifest
from scripts.release.render_release_notes import render_release_notes


def test_render_release_notes_builds_bilingual_versioned_body():
    manifest = {
        "tag": "v9.0",
        "languages": LANGUAGES,
        "release_notes": {
            "summary": {
                "en": "Every binder now has poster artwork.",
                "de": "Jeder Binder besitzt jetzt Poster-Artwork.",
            },
            "hero": {
                "path": "docs/images/key.png",
                "alt": "Binder key visual",
            },
            "preview": {
                "path": "docs/images/output.png",
                "alt": "Actual output",
            },
            "whats_new": {
                "en": {
                    "title": "Poster Artwork for Every Binder",
                    "body": ["All scopes covered."],
                },
                "de": {
                    "title": "Poster-Artwork für jeden Binder",
                    "body": ["Alle Scopes abgedeckt."],
                },
            },
        },
    }

    result = render_release_notes(manifest)

    assert result.startswith("# Binder Pokédex v9.0\n")
    assert "/v9.0/docs/images/key.png" in result
    assert "/v9.0/docs/images/output.png" in result
    assert "Poster Artwork for Every Binder" in result
    assert "Poster-Artwork für jeden Binder" in result
    for info in LANGUAGES.values():
        assert info["zip"] in result


def test_build_manifest_can_exercise_planned_news_for_a_pr(tmp_path: Path, monkeypatch):
    (tmp_path / "config/scopes").mkdir(parents=True)
    (tmp_path / "config/scopes/Base1.yaml").write_text("scope: Base1\n")
    (tmp_path / "config/release_notes").mkdir(parents=True)
    (tmp_path / "config/release_notes/v9.0.yaml").write_text(
        yaml.safe_dump({"summary": {"en": "Poster artwork"}}),
        encoding="utf-8",
    )
    (tmp_path / "data/output").mkdir(parents=True)
    (tmp_path / "data/output/Base1.json").write_text(
        json.dumps({"sections": {"main": {"cards": [1, 2]}}}),
        encoding="utf-8",
    )
    output = tmp_path / "manifest.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "build_manifest.py",
            "--tag",
            "pr-7-deadbeef",
            "--release-notes-tag",
            "v9.0",
            "--project-dir",
            str(tmp_path),
            "--output",
            output.name,
        ],
    )

    assert build_manifest() == 0
    manifest = json.loads(output.read_text(encoding="utf-8"))
    assert manifest["tag"] == "pr-7-deadbeef"
    assert manifest["release_notes_tag"] == "v9.0"
    assert manifest["release_notes"]["summary"]["en"] == "Poster artwork"
