import json
import zipfile
from pathlib import Path

import pytest

from scripts.release.build_manifest import LANGUAGES
from scripts.release.verify_release_candidate import verify


def _release_candidate(tmp_path: Path) -> Path:
    assets = []
    pdf_counts = {}
    for language, info in LANGUAGES.items():
        output_dir = tmp_path / "output" / language
        output_dir.mkdir(parents=True)
        pdf_path = output_dir / "scope.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")

        archive_path = tmp_path / info["zip"]
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.write(pdf_path, f"{language}/{pdf_path.name}")

        pdf_counts[language] = 1
        assets.append(
            {
                "language": language,
                "name": info["zip"],
                "exists": True,
                "size_bytes": archive_path.stat().st_size,
            }
        )

    manifest = {
        "schema_version": 1,
        "tag": "pr-42-deadbeef",
        "scopes": ["Base1"],
        "scope_count": 1,
        "card_counts": {"Base1": 102},
        "pdfs": {
            "total": len(LANGUAGES),
            "by_language": pdf_counts,
        },
        "assets": assets,
    }
    manifest_path = tmp_path / "release-manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def test_verify_release_candidate_checks_every_language_archive(
    tmp_path: Path,
):
    manifest_path = _release_candidate(tmp_path)

    assert verify(manifest_path) == {
        language: 1 for language in LANGUAGES
    }


def test_verify_release_candidate_rejects_missing_archive(
    tmp_path: Path,
):
    manifest_path = _release_candidate(tmp_path)
    (tmp_path / LANGUAGES["de"]["zip"]).unlink()

    with pytest.raises(ValueError, match="Missing or invalid release archive"):
        verify(manifest_path)
