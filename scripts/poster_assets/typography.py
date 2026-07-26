"""Deterministic typography primitives for localized poster overlays."""
from __future__ import annotations

from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont


FONT_CANDIDATES = [
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = list(FONT_CANDIDATES)
    if bold:
        candidates = [
            "/System/Library/Fonts/HelveticaNeue.ttc",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ] + candidates
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def wrap_text(
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if font.getbbox(candidate)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [text]


def draw_text_centered(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: tuple[int, int, int, int],
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int, int],
    shadow_fill: tuple[int, int, int, int] | None = (0, 0, 0, 150),
) -> None:
    left, top, right, bottom = box
    lines = wrap_text(text, font, max_width=right - left)
    line_boxes = [font.getbbox(line) for line in lines]
    line_heights = [bounds[3] - bounds[1] for bounds in line_boxes]
    total_height = sum(line_heights) + max(0, len(lines) - 1) * round(
        font.size * 0.28
    )
    y = top + ((bottom - top) - total_height) // 2
    for line, bounds, line_height in zip(lines, line_boxes, line_heights):
        line_width = bounds[2] - bounds[0]
        x = left + ((right - left) - line_width) // 2
        if shadow_fill:
            draw.text((x + 2, y + 2), line, font=font, fill=shadow_fill)
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height + round(font.size * 0.28)


def composite_panel(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    fill: tuple[int, int, int, int] = (250, 242, 202, 218),
    outline: tuple[int, int, int, int] = (54, 82, 56, 230),
    radius: int = 20,
) -> None:
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    shadow_box = (box[0] + 8, box[1] + 10, box[2] + 8, box[3] + 10)
    draw.rounded_rectangle(
        shadow_box,
        radius=radius,
        fill=(15, 24, 20, 95),
    )
    overlay = overlay.filter(ImageFilter.GaussianBlur(5))
    draw = ImageDraw.Draw(overlay, "RGBA")
    draw.rounded_rectangle(
        box,
        radius=radius,
        fill=fill,
        outline=outline,
        width=3,
    )
    inner = (box[0] + 6, box[1] + 6, box[2] - 6, box[3] - 6)
    draw.rounded_rectangle(
        inner,
        radius=max(4, radius - 6),
        outline=(255, 255, 255, 105),
        width=2,
    )
    canvas.alpha_composite(overlay)


def scope_title(scope_data: dict[str, Any]) -> str:
    name = scope_data.get("name")
    if isinstance(name, dict):
        return name.get("en") or next(iter(name.values()))
    if isinstance(name, str):
        return name
    for section in scope_data.get("sections", {}).values():
        title = section.get("title")
        if isinstance(title, dict):
            return title.get("en") or next(iter(title.values()))
    return "Poster"
