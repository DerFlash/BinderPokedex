"""Deterministic typography primitives for localized poster overlays."""
from __future__ import annotations

from PIL import ImageDraw, ImageFont


FONT_CANDIDATES = [
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]
CJK_FONT_CANDIDATES = {
    "ja": [
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
    ],
    "ko": [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
    ],
    "zh_hans": [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
    ],
    "zh_hant": [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
    ],
}
CJK_FALLBACK_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttf",
]


def load_font(
    size: int,
    bold: bool = False,
    language: str | None = None,
) -> ImageFont.ImageFont:
    candidates = list(FONT_CANDIDATES)
    if language in CJK_FONT_CANDIDATES:
        candidates = (
            CJK_FONT_CANDIDATES[language]
            + CJK_FALLBACK_CANDIDATES
            + candidates
        )
    if bold:
        if language not in CJK_FONT_CANDIDATES:
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
    if language in CJK_FONT_CANDIDATES:
        raise OSError(
            f"No CJK-capable poster font is available for language {language!r}"
        )
    return ImageFont.load_default()


def wrap_text(
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    def contains_cjk(value: str) -> bool:
        return any(
            "\u3040" <= character <= "\u30ff"
            or "\u3400" <= character <= "\u9fff"
            or "\uac00" <= character <= "\ud7af"
            for character in value
        )

    def text_width(value: str) -> int:
        bounds = font.getbbox(value)
        return bounds[2] - bounds[0]

    def split_oversize_token(token: str) -> list[str]:
        chunks: list[str] = []
        current_chunk = ""
        for character in token:
            candidate = current_chunk + character
            if current_chunk and text_width(candidate) > max_width:
                chunks.append(current_chunk)
                current_chunk = character
            else:
                current_chunk = candidate
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        if text_width(word) > max_width and contains_cjk(word):
            if current:
                lines.append(current)
                current = ""
            chunks = split_oversize_token(word)
            lines.extend(chunks[:-1])
            current = chunks[-1]
            continue
        candidate = word if not current else f"{current} {word}"
        if text_width(candidate) <= max_width:
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
    *,
    stroke_width: int = 0,
    stroke_fill: tuple[int, int, int, int] | None = None,
    shadow_offset: int = 2,
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
        # Pillow's default text anchor places ``(x, y)`` at the font origin,
        # while getbbox() commonly reports a positive top bearing. Offset by
        # both bearings so the measured glyph box, not the invisible origin,
        # is what gets centered and bounded.
        x = left + ((right - left) - line_width) // 2 - bounds[0]
        draw_y = y - bounds[1]
        if shadow_fill:
            draw.text(
                (x + shadow_offset, draw_y + shadow_offset),
                line,
                font=font,
                fill=shadow_fill,
            )
        draw.text(
            (x, draw_y),
            line,
            font=font,
            fill=fill,
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
        )
        y += line_height + round(font.size * 0.28)
