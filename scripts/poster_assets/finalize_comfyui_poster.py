#!/usr/bin/env python3
"""Add deterministic poster panels and typography to ComfyUI artwork."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

try:
    from .layout import build_page_layout
    from .render_poster import OUTPUT_DIR, composite_panel, draw_text_centered, load_font, load_json, load_yaml, scope_title
except ImportError:
    from layout import build_page_layout
    from render_poster import OUTPUT_DIR, composite_panel, draw_text_centered, load_font, load_json, load_yaml, scope_title


ROOT = Path(__file__).resolve().parents[2]
POSTER_ASSETS = ROOT / "data" / "poster_assets"
SUPPORTED_LANGUAGES = ("de", "en", "fr", "es", "it")
CARD_LABELS = {"de": "Karten", "en": "cards", "fr": "cartes", "es": "cartas", "it": "carte"}
RELEASE_LABELS = {
    "de": "Veröffentlicht",
    "en": "Released",
    "fr": "Sortie",
    "es": "Publicado",
    "it": "Pubblicato",
}
MONTHS = {
    "de": ("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"),
    "en": ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"),
    "fr": ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"),
    "es": ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"),
    "it": ("gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"),
}


def draw_title_logo(canvas: Image.Image, cell, logo_path: Path) -> None:
    logo = Image.open(logo_path).convert("RGBA")
    scale = min((cell.width * 0.94) / logo.width, (cell.height * 0.62) / logo.height)
    logo = logo.resize(
        (max(1, round(logo.width * scale)), max(1, round(logo.height * scale))),
        Image.Resampling.LANCZOS,
    )
    x = cell.x + (cell.width - logo.width) // 2
    y = cell.y + (cell.height - logo.height) // 2
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_alpha = logo.getchannel("A").filter(ImageFilter.GaussianBlur(max(2, canvas.width // 280)))
    shadow_shape = Image.new("RGBA", logo.size, (8, 18, 28, 105))
    shadow_shape.putalpha(shadow_alpha.point(lambda value: round(value * 0.42)))
    shadow.alpha_composite(shadow_shape, (x + max(2, canvas.width // 280), y + max(3, canvas.width // 220)))
    canvas.alpha_composite(shadow)
    canvas.alpha_composite(logo, (x, y))


def localized_set_name(scope_data: dict, language: str) -> str:
    for section in scope_data.get("sections", {}).values():
        title = section.get("title")
        if isinstance(title, dict):
            return title.get(language) or title.get("en") or next(iter(title.values()))
    return scope_title(scope_data)


def card_count(scope_data: dict) -> int:
    return sum(
        len(section.get("cards", []))
        for section in scope_data.get("sections", {}).values()
        if isinstance(section.get("cards"), list)
    )


def localized_date(value: str, language: str) -> str:
    parsed = date.fromisoformat(value)
    month = MONTHS[language][parsed.month - 1]
    if language == "en":
        return f"{month} {parsed.day}, {parsed.year}"
    return f"{parsed.day}. {month} {parsed.year}" if language == "de" else f"{parsed.day} {month} {parsed.year}"


def draw_info_panel(canvas: Image.Image, cell, scope_data: dict, language: str) -> None:
    box = cell.inset(0.04, 0.18)
    scale = canvas.width / 1400
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    radius = max(8, round(24 * scale))
    shadow_box = (box[0] + max(3, round(8 * scale)), box[1] + max(4, round(10 * scale)), box[2] + max(3, round(8 * scale)), box[3] + max(4, round(10 * scale)))
    draw.rounded_rectangle(shadow_box, radius=radius, fill=(4, 15, 14, 115))
    overlay = overlay.filter(ImageFilter.GaussianBlur(max(2, round(5 * scale))))
    draw = ImageDraw.Draw(overlay, "RGBA")
    draw.rounded_rectangle(box, radius=radius, fill=(18, 50, 43, 226), outline=(224, 190, 98, 245), width=max(2, round(3 * scale)))
    inner = (box[0] + max(3, round(7 * scale)), box[1] + max(3, round(7 * scale)), box[2] - max(3, round(7 * scale)), box[3] - max(3, round(7 * scale)))
    draw.rounded_rectangle(inner, radius=max(5, radius - 5), outline=(255, 244, 190, 75), width=max(1, round(2 * scale)))
    canvas.alpha_composite(overlay)

    name = localized_set_name(scope_data, language)
    count = f"{card_count(scope_data)} {CARD_LABELS[language]}"
    release_label = RELEASE_LABELS[language]
    release_date = localized_date(str(scope_data["release_date"]), language)
    text_draw = ImageDraw.Draw(canvas, "RGBA")
    height = box[3] - box[1]
    rows = (
        (name, (box[0] + 5, box[1] + round(height * 0.06), box[2] - 5, box[1] + round(height * 0.34)), max(11, cell.height // 13), True, (255, 244, 190, 255)),
        (count, (box[0] + 5, box[1] + round(height * 0.34), box[2] - 5, box[1] + round(height * 0.57)), max(9, cell.height // 18), True, (232, 213, 151, 255)),
        (release_label, (box[0] + 5, box[1] + round(height * 0.57), box[2] - 5, box[1] + round(height * 0.76)), max(8, cell.height // 24), False, (185, 210, 190, 255)),
        (release_date, (box[0] + 5, box[1] + round(height * 0.75), box[2] - 5, box[3] - 4), max(8, cell.height // 21), False, (244, 238, 207, 255)),
    )
    for text, text_box, size, bold, color in rows:
        draw_text_centered(text_draw, text, text_box, load_font(size, bold=bold), color, shadow_fill=None)


def draw_project_signature(canvas: Image.Image) -> None:
    text = "Binder Pokedex"
    font = load_font(max(8, canvas.width // 72), bold=True)
    bbox = font.getbbox(text)
    width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    margin = max(8, round(canvas.width * 0.018))
    x = canvas.width - margin - width
    y = canvas.height - margin - height
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.text((x + 1, y + 1), text, font=font, fill=(8, 20, 16, 175))
    draw.text((x, y), text, font=font, fill=(246, 239, 207, 215))


def draw_final_text_cells(canvas, layout, manifest, scope_data, scope_dir: Path, language: str) -> None:
    text_cells = manifest.get("text_cells", {})
    title_cfg = text_cells.get("title", {"row": 1, "column": 2})
    info_cfg = text_cells.get("set_info", {"row": 2, "column": 2})
    title_cell = layout.cell(int(title_cfg["row"]), int(title_cfg["column"]))
    info_cell = layout.cell(int(info_cfg["row"]), int(info_cfg["column"]))
    logo_file = manifest.get("title_logo", {}).get("file")
    if logo_file:
        logo_path = scope_dir / logo_file
        if not logo_path.is_file():
            raise FileNotFoundError(f"Title logo not found: {logo_path}")
        draw_title_logo(canvas, title_cell, logo_path)
    else:
        title_box = title_cell.inset(0.09, 0.27)
        composite_panel(canvas, title_box, fill=(253, 244, 202, 238), outline=(44, 84, 52, 245), radius=max(8, round(24 * canvas.width / 1400)))
        draw = ImageDraw.Draw(canvas, "RGBA")
        draw_text_centered(draw, scope_title(scope_data), title_box, load_font(max(14, title_cell.height // 8), bold=True), (35, 65, 42, 255), shadow_fill=None)
    draw_info_panel(canvas, info_cell, scope_data, language)
    draw_project_signature(canvas)


def finalize(scope: str, input_path: Path, output_path: Path | None = None, language: str = "en") -> Path:
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")
    scope_dir = POSTER_ASSETS / scope
    manifest = load_yaml(scope_dir / "poster.yaml")
    scope_data = load_json(OUTPUT_DIR / f"{scope}.json")

    canvas = Image.open(input_path).convert("RGBA")
    layout = build_page_layout(
        manifest.get("layout", {}).get("name", "standard_3x3"),
        width_px=canvas.width,
    )
    # ComfyUI aligns latent dimensions to multiples of 16, so a few pixels of
    # aspect-ratio rounding are expected at preview sizes.
    if abs(layout.height_px - canvas.height) > 16:
        raise ValueError(
            f"Artwork ratio does not match poster layout: {canvas.size} vs "
            f"{(layout.width_px, layout.height_px)}"
        )

    draw_final_text_cells(canvas, layout, manifest, scope_data, scope_dir, language)
    if output_path is None:
        output_path = input_path.with_name(f"{input_path.stem}_final.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output_path, format="PNG", optimize=True)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", default="Base1")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--language", choices=SUPPORTED_LANGUAGES, default="en")
    args = parser.parse_args()
    print(finalize(args.scope, args.input, args.output, args.language))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
