# SVG Templates

This directory contains SVG templates for rendering Pokémon cards, pages, and covers.

## Structure

```
templates/
  cards/    - Individual card templates (63mm × 88mm)
  pages/    - Page layout templates (A4, 210mm × 297mm)
  covers/   - Cover page templates (A4)
```

## Template Types

### Card Templates (`cards/`)
Define the design of individual Pokémon cards.

**Available:**
- `classic.svg` - Current design (header, centered name, image, ID at bottom)

**Dimensions:** 63mm × 88mm (standard trading card size)

### Page Templates (`pages/`)
Define the layout of cards on an A4 page.

**Available:**
- `grid_3x3.svg` - 9 cards per page (3 columns × 3 rows)

**Dimensions:** 210mm × 297mm (A4)

### Cover Templates (`covers/`)
Define the cover page design for PDF binders.

**Available:**
- `simple.svg` - Minimalist cover with title and range

**Dimensions:** 210mm × 297mm (A4)

## Template Variables

Templates use `{{variable}}` syntax for dynamic content:

### Card Templates
- `{{name}}` - Pokémon name (rendered by Python with logos)
- `{{type}}` - Pokémon type (translated)
- `{{type_color}}` - Type color (hex)
- `{{type_color_dark}}` - Darkened type color (hex)
- `{{id}}` - Pokémon ID/number

### Page Templates
- `{{page_number}}` - Current page number
- `{{total_pages}}` - Total page count

### Cover Templates
- `{{title}}` - Set title (e.g., "National Pokédex")
- `{{subtitle}}` - Subtitle (e.g., "Generation 1")
- `{{range_start}}` - Start ID
- `{{range_end}}` - End ID
- `{{language}}` - Language name

## Creating Custom Templates

1. **Design in Inkscape/Figma** - Use mm as unit
2. **Add template variables** - Use `{{variable_name}}` syntax
3. **Save as Plain SVG** - Remove Inkscape/editor metadata
4. **Test with validator** - `python scripts/pdf/validate_template.py` (v1.1+)
5. **Use in generation** - `--card-template your_template`

See [TEMPLATE_SYSTEM.md](../../docs/TEMPLATE_SYSTEM.md) for detailed documentation.
