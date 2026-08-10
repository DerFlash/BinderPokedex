import json
from pathlib import Path

from scripts.release.announce_release import main


def test_announcement_updates_current_readmes_once(tmp_path, monkeypatch):
    project_dir = Path(__file__).resolve().parents[2]
    for name in ("README.md", "README.de.md"):
        (tmp_path / name).write_text(
            (project_dir / name).read_text(encoding="utf-8"), encoding="utf-8"
        )

    manifest = json.loads((project_dir / "release-manifest.json").read_text(encoding="utf-8"))
    manifest.update({"tag": "v9.0", "scope_count": 30})
    manifest["pdfs"]["total"] = 167
    manifest["scope_groups"]["mega"] = ["ME01", "ME02", "ME02.5", "ME03", "ME04", "MEP"]
    manifest["release_notes"] = {
        "display_date": {"en": "August 2026", "de": "August 2026"},
        "summary": {"en": "Poster artwork", "de": "Poster-Artwork"},
        "whats_new": {
            "en": {"title": "Poster Artwork for Every Binder", "body": ["Added poster pages"]},
            "de": {"title": "Poster-Artwork für jeden Binder", "body": ["Poster-Seiten ergänzt"]},
        },
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    args = [
        "announce_release.py", "--manifest", str(manifest_path),
        "--release-url", "https://github.com/DerFlash/BinderPokedex/releases/tag/v9.0",
        "--project-dir", str(tmp_path),
    ]

    monkeypatch.setattr("sys.argv", args)
    assert main() == 0
    monkeypatch.setattr("sys.argv", args)
    assert main() == 0

    readme_en = (tmp_path / "README.md").read_text(encoding="utf-8")
    readme_de = (tmp_path / "README.de.md").read_text(encoding="utf-8")
    assert readme_en.count("### v9.0 (August 2026)") == 1
    assert readme_de.count("### v9.0 (August 2026)") == 1
    assert "**Latest (v9.0):** [All 167 PDFs]" in readme_en
    assert "**Aktuelle Version (v9.0):** [Alle 167 PDFs]" in readme_de
    assert "**30 Scarlet & Violet Sets:**" not in readme_en
    assert "**Scope-Based System** with 30 total scopes" in readme_en
