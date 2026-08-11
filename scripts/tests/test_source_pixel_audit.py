from pathlib import Path

from PIL import Image
import pytest

from scripts.poster_assets.source_pixel_audit import audit_exact_source_pixels
from scripts.poster_assets.provenance import (
    require_exact_source_pixel_validation,
)


def _write_reference_and_artwork(tmp_path: Path) -> tuple[Path, Path]:
    reference_path = tmp_path / "reference.png"
    artwork_path = tmp_path / "artwork.png"
    reference = Image.new("RGBA", (6, 5), (20, 30, 40, 0))
    reference.putpixel((1, 1), (10, 20, 30, 255))
    reference.putpixel((2, 1), (40, 50, 60, 255))
    reference.putpixel((3, 2), (70, 80, 90, 255))
    reference.putpixel((4, 3), (100, 110, 120, 128))
    reference.save(reference_path)

    artwork = Image.new("RGB", reference.size, (200, 210, 220))
    artwork.paste(reference.convert("RGB"), mask=reference.getchannel("A"))
    # A partial-alpha pixel is outside the exact-source contract.
    artwork.putpixel((4, 3), (1, 2, 3))
    artwork.save(artwork_path)
    return reference_path, artwork_path


def test_exact_source_pixel_audit_passes_and_ignores_non_opaque_pixels(
    tmp_path: Path,
):
    reference_path, artwork_path = _write_reference_and_artwork(tmp_path)

    result = audit_exact_source_pixels(reference_path, artwork_path)

    assert result == {
        "method": "exact_opaque_source_pixels",
        "opaque_pixels": 3,
        "changed_pixels": 0,
        "passed": True,
    }


def test_exact_source_pixel_audit_counts_each_changed_pixel_and_reports_bbox(
    tmp_path: Path,
):
    reference_path, artwork_path = _write_reference_and_artwork(tmp_path)
    artwork = Image.open(artwork_path).convert("RGB")
    # Exercise single-channel one-step differences so no changed pixel can be
    # lost through grayscale rounding.
    artwork.putpixel((1, 1), (10, 20, 31))
    artwork.putpixel((3, 2), (71, 80, 90))
    artwork.save(artwork_path)

    result = audit_exact_source_pixels(reference_path, artwork_path)

    assert result == {
        "method": "exact_opaque_source_pixels",
        "opaque_pixels": 3,
        "changed_pixels": 2,
        "changed_bbox": (1, 1, 4, 3),
        "passed": False,
    }


def test_exact_source_pixel_audit_can_require_a_match(tmp_path: Path):
    reference_path, artwork_path = _write_reference_and_artwork(tmp_path)
    artwork = Image.open(artwork_path).convert("RGB")
    artwork.putpixel((2, 1), (40, 51, 60))
    artwork.save(artwork_path)

    with pytest.raises(
        RuntimeError,
        match=r"1 of 3 fully opaque pixels changed inside \(2, 1, 3, 2\)",
    ):
        audit_exact_source_pixels(
            reference_path,
            artwork_path,
            require_match=True,
        )


def test_exact_source_pixel_audit_rejects_mismatched_dimensions(tmp_path: Path):
    reference_path = tmp_path / "reference.png"
    artwork_path = tmp_path / "artwork.png"
    Image.new("RGBA", (4, 4), (10, 20, 30, 255)).save(reference_path)
    Image.new("RGB", (5, 4), (10, 20, 30)).save(artwork_path)

    with pytest.raises(ValueError, match="dimensions differ"):
        audit_exact_source_pixels(reference_path, artwork_path)


def test_exact_source_pixel_audit_rejects_reference_without_opaque_pixels(
    tmp_path: Path,
):
    reference_path = tmp_path / "reference.png"
    artwork_path = tmp_path / "artwork.png"
    Image.new("RGBA", (4, 4), (10, 20, 30, 254)).save(reference_path)
    Image.new("RGB", (4, 4), (10, 20, 30)).save(artwork_path)

    with pytest.raises(ValueError, match="no fully opaque pixels"):
        audit_exact_source_pixels(reference_path, artwork_path)


def test_exact_source_pixel_audit_requires_an_alpha_reference(tmp_path: Path):
    reference_path = tmp_path / "reference.png"
    artwork_path = tmp_path / "artwork.png"
    Image.new("RGB", (4, 4), (10, 20, 30)).save(reference_path)
    Image.new("RGB", (4, 4), (10, 20, 30)).save(artwork_path)

    with pytest.raises(ValueError, match="must contain an alpha channel"):
        audit_exact_source_pixels(reference_path, artwork_path)


def test_promotion_gate_accepts_the_legacy_identity_lock_record():
    record = require_exact_source_pixel_validation(
        {
            "generation": {
                "engine": "flux",
                "mode": "identity_lock",
            },
            "validation": {
                "identity_lock": {
                    "method": "exact_opaque_source_pixels",
                    "opaque_pixels": 42,
                    "changed_pixels": 0,
                    "passed": True,
                }
            }
        },
        allow_legacy=True,
    )

    assert record["opaque_pixels"] == 42


def test_new_candidates_cannot_use_the_unbound_legacy_record():
    with pytest.raises(
        ValueError,
        match="require the bound source-pixel validation record",
    ):
        require_exact_source_pixel_validation(
            {
                "generation": {
                    "engine": "flux",
                    "mode": "identity_lock",
                },
                "validation": {
                    "identity_lock": {
                        "method": "exact_opaque_source_pixels",
                        "opaque_pixels": 42,
                        "changed_pixels": 0,
                        "passed": True,
                    }
                },
            }
        )
def test_promotion_gate_binds_a_current_audit_to_raw_artwork_and_reference():
    artwork_hash = "a" * 64
    reference_hash = "b" * 64
    record = {
        "method": "exact_opaque_source_pixels",
        "opaque_pixels": 42,
        "changed_pixels": 0,
        "passed": True,
        "stage": "raw_generation",
        "reference_sha256": reference_hash,
        "artwork_sha256": artwork_hash,
        "width": 80,
        "height": 110,
    }

    accepted = require_exact_source_pixel_validation(
        {
            "raw_artwork": {
                "sha256": artwork_hash,
                "width": 80,
                "height": 110,
            },
            "inputs": {
                "source_pixel_audit_reference": {
                    "sha256": reference_hash,
                    "width": 80,
                    "height": 110,
                }
            },
            "validation": {"source_pixels": record},
        }
    )

    assert accepted == record


def test_promotion_gate_rejects_an_unbound_current_audit():
    with pytest.raises(ValueError, match="raw-stage image binding"):
        require_exact_source_pixel_validation(
            {
                "validation": {
                    "source_pixels": {
                        "method": "exact_opaque_source_pixels",
                        "opaque_pixels": 42,
                        "changed_pixels": 0,
                        "passed": True,
                    }
                }
            }
        )


def test_promotion_gate_rejects_non_mapping_inputs_cleanly():
    artwork_hash = "a" * 64
    reference_hash = "b" * 64
    with pytest.raises(
        ValueError,
        match="does not match its recorded audit reference",
    ):
        require_exact_source_pixel_validation(
            {
                "raw_artwork": {
                    "sha256": artwork_hash,
                    "width": 80,
                    "height": 110,
                },
                "inputs": [],
                "validation": {
                    "source_pixels": {
                        "method": "exact_opaque_source_pixels",
                        "opaque_pixels": 42,
                        "changed_pixels": 0,
                        "passed": True,
                        "stage": "raw_generation",
                        "reference_sha256": reference_hash,
                        "artwork_sha256": artwork_hash,
                        "width": 80,
                        "height": 110,
                    }
                },
            }
        )


@pytest.mark.parametrize(
    "record",
    (
        {
            "method": "exact_opaque_source_pixels",
            "opaque_pixels": True,
            "changed_pixels": 0,
            "passed": True,
        },
        {
            "method": "exact_opaque_source_pixels",
            "opaque_pixels": 42,
            "changed_pixels": False,
            "passed": True,
        },
        {
            "method": "exact_opaque_source_pixels",
            "opaque_pixels": 42,
            "changed_pixels": 1,
            "passed": False,
        },
    ),
)
def test_promotion_gate_rejects_malformed_or_failed_audits(record):
    with pytest.raises(ValueError, match="did not pass"):
        require_exact_source_pixel_validation(
            {"validation": {"source_pixels": record}}
        )
