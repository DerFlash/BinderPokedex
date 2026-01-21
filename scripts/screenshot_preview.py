"""
Screenshot Preview Generator for Pokédex PDF

- Extracts cover page and first card page from the English Pokédex PDF
- Merges them into a preview image: cover top-left, card bottom-right, shadow, overlap 1/4
- Saves result to output/preview_pokedex_en.png
"""
import os
from pathlib import Path
from PIL import Image, ImageFilter, ImageOps
from pdf2image import convert_from_path

PDF_PATH = Path("output/en/Pokedex_Gen1-9_EN.pdf")
PREVIEW_PATH = Path("docs/images/binderdex-preview.png")

# Step 1: Extract cover and first card page as images
pages = convert_from_path(str(PDF_PATH), dpi=200, first_page=1, last_page=2)
cover_img, card_img = pages[0], pages[1]

# Step 2: Resize images for preview (optional: scale down for faster preview)

cover_img = cover_img.resize((int(cover_img.width * 0.7), int(cover_img.height * 0.7)), Image.LANCZOS)
card_img = card_img.resize((int(card_img.width * 0.7), int(card_img.height * 0.7)), Image.LANCZOS)

# Add a single pixel border around the cover page screenshot
border_color = (40, 40, 40)
cover_img = ImageOps.expand(cover_img, border=1, fill=border_color)

# Step 3: Create shadow for card page

# Create a proper drop shadow for the card page

shadow_offset = 32  # px
shadow_blur = 24    # px
shadow_color = (0, 0, 0, 120)

# Shadow canvas is much larger than card_img to allow for full blur
shadow_margin = shadow_offset + shadow_blur * 2
shadow_canvas = Image.new('RGBA', (card_img.width + shadow_margin, card_img.height + shadow_margin), (0,0,0,0))
shadow_layer = Image.new('RGBA', card_img.size, shadow_color)
shadow_canvas.paste(shadow_layer, (shadow_margin//2, shadow_margin//2))
shadow_canvas = shadow_canvas.filter(ImageFilter.GaussianBlur(shadow_blur))

# Step 4: Compose preview image

# Card page position: bottom-right, overlapping 1/4 of cover
cover_w, cover_h = cover_img.size
card_w, card_h = card_img.size
card_x = int(cover_w * 0.55)
card_y = int(cover_h * 0.55)


# Calculate required canvas size to fit both images and the shadow


shadow_w, shadow_h = shadow_canvas.size
# Margin is at least half the shadow margin, plus a base margin
base_margin = 48
margin = max(base_margin, shadow_margin//2)
max_w = max(cover_w + margin * 2, card_x + shadow_w + margin)
max_h = max(cover_h + margin * 2, card_y + shadow_h + margin)

# Create preview canvas with margin
preview = Image.new('RGBA', (max_w, max_h), (255,255,255,255))
preview.paste(cover_img, (margin, margin))

# Paste drop shadow first
preview.alpha_composite(shadow_canvas, (card_x - shadow_margin//2 + margin, card_y - shadow_margin//2 + margin))
# Paste card page
preview.alpha_composite(card_img.convert('RGBA'), (card_x + margin, card_y + margin))

# Step 5: Save preview image
preview = preview.convert('RGB')
PREVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
preview.save(str(PREVIEW_PATH), quality=95)
print(f"✅ Preview saved: {PREVIEW_PATH}")
