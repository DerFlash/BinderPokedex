"""Engine-independent audits for exact preservation of source pixels."""
from __future__ import annotations

from pathlib import Path
from typing import TypeAlias

from PIL import Image, ImageChops


AuditValue: TypeAlias = bool | int | str | tuple[int, int, int, int]
SourcePixelAudit: TypeAlias = dict[str, AuditValue]


def audit_exact_source_pixels(
    reference_path: Path,
    artwork_path: Path,
    *,
    require_match: bool = False,
) -> SourcePixelAudit:
    """Compare fully opaque RGBA reference pixels with an RGB artwork.

    Transparent and partially transparent reference pixels are deliberately
    excluded: only source pixels with alpha 255 form the preservation
    contract. Invalid inputs cannot produce a passing audit.
    """
    with Image.open(reference_path) as opened_reference:
        if "A" not in opened_reference.getbands():
            raise ValueError(
                "Source-pixel reference must contain an alpha channel: "
                f"{reference_path}"
            )
        reference = opened_reference.convert("RGBA")

    with Image.open(artwork_path) as opened_artwork:
        artwork = opened_artwork.convert("RGB")

    if artwork.size != reference.size:
        raise ValueError(
            "Source-pixel reference and artwork dimensions differ: "
            f"{reference.size} != {artwork.size}"
        )

    alpha = reference.getchannel("A")
    opaque_mask = alpha.point(lambda value: 255 if value == 255 else 0)
    opaque_pixels = opaque_mask.histogram()[255]
    if opaque_pixels <= 0:
        raise ValueError(
            "Source-pixel reference has no fully opaque pixels: "
            f"{reference_path}"
        )

    difference = ImageChops.difference(artwork, reference.convert("RGB"))
    red, green, blue = difference.split()
    changed_any_channel = ImageChops.lighter(
        ImageChops.lighter(
            red.point(lambda value: 255 if value else 0),
            green.point(lambda value: 255 if value else 0),
        ),
        blue.point(lambda value: 255 if value else 0),
    )
    changed_mask = ImageChops.multiply(changed_any_channel, opaque_mask)
    changed_pixels = changed_mask.histogram()[255]
    changed_bbox = changed_mask.getbbox()

    result: SourcePixelAudit = {
        "method": "exact_opaque_source_pixels",
        "opaque_pixels": opaque_pixels,
        "changed_pixels": changed_pixels,
        "passed": changed_pixels == 0,
    }
    if changed_bbox is not None:
        result["changed_bbox"] = changed_bbox

    if require_match and changed_pixels:
        raise RuntimeError(
            "Source-pixel audit failed: "
            f"{changed_pixels} of {opaque_pixels} fully opaque pixels changed "
            f"inside {changed_bbox}: {artwork_path}"
        )

    return result
