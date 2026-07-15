#!/usr/bin/env python3
"""Render a standalone poster preview PNG from reviewed poster assets."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

try:
    from .layout import PageLayout, build_page_layout
except ImportError:  # Direct script execution
    from layout import PageLayout, build_page_layout


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
POSTER_ASSETS_DIR = REPO_ROOT / "data" / "poster_assets"
OUTPUT_DIR = REPO_ROOT / "data" / "output"

FONT_CANDIDATES = [
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


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


def cover_resize(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    scale = max(target_w / img.width, target_h / img.height)
    resized = img.resize((round(img.width * scale), round(img.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - target_w) // 2
    top = (resized.height - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def fit_image(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
    scale = min(max_w / img.width, max_h / img.height)
    return img.resize((round(img.width * scale), round(img.height * scale)), Image.Resampling.LANCZOS)


def load_cutout_items(scope_dir: Path) -> list[dict[str, Any]]:
    manifest_path = scope_dir / "cutouts" / "manifest.json"
    cutout_manifest = load_json(manifest_path)
    return list(cutout_manifest.get("items", []))


def cutout_placements(layout: PageLayout, scope_dir: Path) -> list[dict[str, Any]]:
    prepared: list[tuple[Any, dict[str, Any], Image.Image]] = []
    for cell, item in zip(layout.bottom_row_cells(), load_cutout_items(scope_dir)):
        cutout_path = scope_dir / "cutouts" / item["file"]
        cutout = Image.open(cutout_path).convert("RGBA")
        target = fit_image(cutout, round(cell.width * 0.84), round(cell.height * 0.68))
        prepared.append((cell, item, target))

    placements: list[dict[str, Any]] = []
    baseline = layout.bottom_row_cells()[0].y + round(layout.bottom_row_cells()[0].height * 0.80)
    for cell, item, target in prepared:
        x = cell.x + (cell.width - target.width) // 2
        alpha_box = target.getchannel("A").getbbox()
        if alpha_box is None:
            raise ValueError(f"Cutout has no visible pixels: {item['file']}")
        y = baseline - alpha_box[3]
        placements.append({"cell": cell, "item": item, "image": target, "x": x, "y": y})
    return placements


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
    line_heights = [bbox[3] - bbox[1] for bbox in line_boxes]
    total_h = sum(line_heights) + max(0, len(lines) - 1) * round(font.size * 0.28)
    y = top + ((bottom - top) - total_h) // 2
    for line, bbox, line_h in zip(lines, line_boxes, line_heights):
        line_w = bbox[2] - bbox[0]
        x = left + ((right - left) - line_w) // 2
        if shadow_fill:
            draw.text((x + 2, y + 2), line, font=font, fill=shadow_fill)
        draw.text((x, y), line, font=font, fill=fill)
        y += line_h + round(font.size * 0.28)


def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
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
    draw.rounded_rectangle(shadow_box, radius=radius, fill=(15, 24, 20, 95))
    overlay = overlay.filter(ImageFilter.GaussianBlur(5))
    draw = ImageDraw.Draw(overlay, "RGBA")
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=3)
    inner = (box[0] + 6, box[1] + 6, box[2] - 6, box[3] - 6)
    draw.rounded_rectangle(inner, radius=max(4, radius - 6), outline=(255, 255, 255, 105), width=2)
    canvas.alpha_composite(overlay)


def scope_title(scope_data: dict[str, Any]) -> str:
    name = scope_data.get("name")
    if isinstance(name, dict):
        return name.get("en") or next(iter(name.values()))
    if isinstance(name, str):
        return name
    sections = scope_data.get("sections", {})
    for section in sections.values():
        title = section.get("title")
        if isinstance(title, dict):
            return title.get("en") or next(iter(title.values()))
    return "Poster"


def set_info_parts(scope_data: dict[str, Any]) -> list[str]:
    set_id = scope_data.get("set_id") or ""
    release_date = str(scope_data.get("release_date") or "")
    year = release_date[:4] if release_date else ""
    total_cards = 0
    for section in scope_data.get("sections", {}).values():
        cards = section.get("cards")
        if isinstance(cards, list):
            total_cards += len(cards)
    return [part for part in (set_id, year, f"{total_cards} cards" if total_cards else "") if part] or ["Base Set"]


def draw_text_cells(canvas: Image.Image, layout: PageLayout, manifest: dict[str, Any], scope_data: dict[str, Any]) -> None:
    text_cells = manifest.get("text_cells", {})
    title_cfg = text_cells.get("title", {"row": 1, "column": 2})
    info_cfg = text_cells.get("set_info", {"row": 2, "column": 2})

    title_cell = layout.cell(int(title_cfg["row"]), int(title_cfg["column"]))
    info_cell = layout.cell(int(info_cfg["row"]), int(info_cfg["column"]))

    title_box = title_cell.inset(0.09, 0.27)
    info_box = info_cell.inset(0.12, 0.34)
    composite_panel(canvas, title_box, fill=(253, 244, 202, 226), outline=(44, 84, 52, 235), radius=24)
    composite_panel(canvas, info_box, fill=(247, 236, 190, 224), outline=(44, 84, 52, 235), radius=20)

    draw = ImageDraw.Draw(canvas, "RGBA")
    draw_text_centered(
        draw,
        scope_title(scope_data),
        title_box,
        load_font(max(34, title_cell.height // 8), bold=True),
        (35, 65, 42, 255),
        shadow_fill=(255, 255, 238, 170),
    )

    parts = set_info_parts(scope_data)
    primary = parts[0]
    secondary = " / ".join(parts[1:]) if len(parts) > 1 else ""
    mid_y = (info_box[1] + info_box[3]) // 2
    primary_box = (info_box[0], info_box[1] + 8, info_box[2], mid_y)
    secondary_box = (info_box[0], mid_y - 2, info_box[2], info_box[3] - 8)
    draw_text_centered(
        draw,
        primary,
        primary_box,
        load_font(max(18, info_cell.height // 18), bold=True),
        (39, 74, 48, 255),
        shadow_fill=(255, 255, 238, 150),
    )
    if secondary:
        draw_text_centered(
            draw,
            secondary,
            secondary_box,
            load_font(max(17, info_cell.height // 20), bold=False),
            (57, 82, 62, 255),
            shadow_fill=(255, 255, 238, 135),
        )


def draw_cutouts(canvas: Image.Image, layout: PageLayout, scope_dir: Path) -> None:
    for placement in cutout_placements(layout, scope_dir):
        cell = placement["cell"]
        target = relight_cutout(placement["image"], cell)
        x = placement["x"]
        y = placement["y"]

        draw_ground_shadow(canvas, cell, x, y, target)
        draw_contact_occlusion(canvas, cell, x, y, target)
        canvas.alpha_composite(target, (x, y))
        draw_foreground_grass(canvas, cell, x, y, target)


def relight_cutout(target: Image.Image, cell) -> Image.Image:
    alpha = target.getchannel("A")
    rgb = target.convert("RGB")
    rgb = ImageEnhance.Color(rgb).enhance(0.94)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.04)
    lit = rgb.convert("RGBA")
    lit.putalpha(alpha)

    w, h = target.size
    light_mask = Image.new("L", target.size, 0)
    light_px = light_mask.load()
    for yy in range(h):
        for xx in range(w):
            top_left = 1.0 - ((xx / max(1, w - 1)) * 0.45 + (yy / max(1, h - 1)) * 0.55)
            light_px[xx, yy] = max(0, min(72, round(72 * top_left)))
    light_mask = ImageChops.multiply(light_mask, alpha.point(lambda p: int(p * 0.78)))
    warm = Image.new("RGBA", target.size, (255, 232, 164, 0))
    warm.putalpha(light_mask.filter(ImageFilter.GaussianBlur(max(2, cell.width // 120))))
    lit.alpha_composite(warm)

    shadow_mask = Image.new("L", target.size, 0)
    shadow_px = shadow_mask.load()
    for yy in range(h):
        for xx in range(w):
            bottom_right = (xx / max(1, w - 1)) * 0.42 + (yy / max(1, h - 1)) * 0.58
            shadow_px[xx, yy] = max(0, min(58, round(58 * bottom_right)))
    shadow_mask = ImageChops.multiply(shadow_mask, alpha.point(lambda p: int(p * 0.72)))
    cool_shadow = Image.new("RGBA", target.size, (21, 53, 38, 0))
    cool_shadow.putalpha(shadow_mask.filter(ImageFilter.GaussianBlur(max(2, cell.width // 120))))
    lit = Image.alpha_composite(lit, cool_shadow)
    lit.putalpha(alpha)
    return lit


def draw_ground_shadow(canvas: Image.Image, cell, x: int, y: int, target: Image.Image) -> None:
    alpha = target.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        return
    left, top, right, bottom = bbox
    foot_y = y + bottom
    shadow_w = max(round((right - left) * 0.82), round(cell.width * 0.30))
    shadow_h = max(round(cell.height * 0.10), 24)
    center_x = x + (left + right) // 2 + round(cell.width * 0.035)
    center_y = min(cell.y + round(cell.height * 0.82), foot_y - round(shadow_h * 0.12))

    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    ellipse = (
        center_x - shadow_w // 2,
        center_y - shadow_h // 2,
        center_x + shadow_w // 2,
        center_y + shadow_h // 2,
    )
    draw.ellipse(ellipse, fill=(14, 30, 20, 118))
    core = (
        center_x - round(shadow_w * 0.32),
        center_y - round(shadow_h * 0.25),
        center_x + round(shadow_w * 0.32),
        center_y + round(shadow_h * 0.23),
    )
    draw.ellipse(core, fill=(8, 20, 13, 76))
    canvas.alpha_composite(overlay.filter(ImageFilter.GaussianBlur(max(8, cell.width // 35))))


def draw_contact_occlusion(canvas: Image.Image, cell, x: int, y: int, target: Image.Image) -> None:
    alpha = target.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        return
    mask = Image.new("L", target.size, 0)
    bottom_band = Image.new("L", target.size, 0)
    draw = ImageDraw.Draw(bottom_band)
    band_top = max(0, bbox[3] - round(target.height * 0.24))
    draw.rectangle((0, band_top, target.width, target.height), fill=255)
    mask = ImageChops.multiply(alpha, bottom_band)
    mask = mask.filter(ImageFilter.GaussianBlur(max(5, cell.width // 60))).point(lambda p: int(p * 0.30))
    occlusion = Image.new("RGBA", target.size, (9, 26, 15, 0))
    occlusion.putalpha(mask)
    canvas.alpha_composite(occlusion, (x + round(cell.width * 0.015), y + round(cell.height * 0.016)))


def draw_foreground_grass(canvas: Image.Image, cell, x: int, y: int, target: Image.Image) -> None:
    """Add subtle foreground grass strokes to ground cutouts in the scene."""
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    baseline = min(cell.y + round(cell.height * 0.82), y + target.height - round(target.height * 0.03))
    left = max(cell.x + round(cell.width * 0.11), x - round(cell.width * 0.03))
    right = min(cell.x + round(cell.width * 0.89), x + target.width + round(cell.width * 0.03))
    colors = [(25, 75, 36, 120), (91, 138, 56, 100), (20, 56, 31, 112), (136, 164, 74, 76)]
    step = max(10, (right - left) // 22)
    for index, gx in enumerate(range(left, right, step)):
        height = round(cell.height * (0.024 + 0.018 * ((index % 5) / 4)))
        lean = [-8, 5, -4, 9, 2][index % 5]
        root_y = baseline + [0, -4, 3, -2, 5][index % 5]
        draw.line((gx, root_y, gx + lean, root_y - height), fill=colors[index % len(colors)], width=2)
        if index % 5 == 0:
            draw.line((gx + 3, root_y + 1, gx - lean, root_y - round(height * 0.58)), fill=colors[(index + 1) % len(colors)], width=1)
    canvas.alpha_composite(overlay.filter(ImageFilter.GaussianBlur(0.55)))


def render_poster(scope: str, width_px: int = 1400, force: bool = False) -> int:
    scope_dir = POSTER_ASSETS_DIR / scope
    poster_yaml = scope_dir / "poster.yaml"
    scope_json = OUTPUT_DIR / f"{scope}.json"
    if not poster_yaml.exists():
        raise FileNotFoundError(f"Poster manifest not found: {poster_yaml}")
    if not scope_json.exists():
        raise FileNotFoundError(f"Scope output not found: {scope_json}")

    manifest = load_yaml(poster_yaml)
    scope_data = load_json(scope_json)
    layout = build_page_layout(manifest.get("layout", {}).get("name", "standard_3x3"), width_px=width_px)

    bg_path = scope_dir / manifest.get("background", {}).get("file", "background/background.png")
    if not bg_path.exists():
        raise FileNotFoundError(f"Background not found: {bg_path}")

    out_path = scope_dir / "poster.png"
    if out_path.exists() and not force:
        raise FileExistsError(f"Poster already exists: {out_path} (use --force to overwrite)")

    background = Image.open(bg_path).convert("RGBA")
    canvas = cover_resize(background, (layout.width_px, layout.height_px))
    draw_text_cells(canvas, layout, manifest, scope_data)
    draw_cutouts(canvas, layout, scope_dir)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path, format="PNG", optimize=True)
    print(f"Rendered poster: {out_path} ({canvas.width}x{canvas.height})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a standalone poster PNG")
    parser.add_argument("--scope", required=True, help="Scope name, e.g. Base1")
    parser.add_argument("--width", type=int, default=1400, help="Output width in pixels")
    parser.add_argument("--force", action="store_true", help="Overwrite existing poster")
    args = parser.parse_args()

    try:
        return render_poster(args.scope, width_px=args.width, force=args.force)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
