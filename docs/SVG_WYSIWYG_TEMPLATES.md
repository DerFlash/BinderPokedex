# SVG WYSIWYG Template System

## Overview

The template system now uses **XML manipulation** for a true **WYSIWYG (What You See Is What You Get)** workflow. SVG templates contain real dummy content that matches the final PDF output exactly, making it easy to design templates visually in any SVG editor.

## Key Principles

### 1. **WYSIWYG Preview**
- SVG templates contain **real dummy content** (e.g., "Pikachu", placeholder images)
- What you see in the SVG preview is what you get in the PDF
- No coordinate system conversion needed
- SVG coordinate system (top-left origin) is preserved throughout

### 2. **XML DOM Manipulation**
- Python uses `xml.etree.ElementTree` to parse SVG as XML
- Elements are identified by `id` attribute
- Content is replaced directly in the XML before rendering
- No position extraction or Y-axis flipping

### 3. **Mustache Variables Still Supported**
- `{{variable}}` syntax for static values (colors, text that doesn't change per card)
- Substituted before XML manipulation
- Used for: type colors, stripe colors, etc.

## How It Works

### Workflow

```
1. Load SVG template with dummy content
   ↓
2. Substitute {{variable}} placeholders (colors, etc.)
   ↓
3. Parse SVG as XML (ElementTree)
   ↓
4. Find elements by ID (e.g., id="pokemon_name")
   ↓
5. Replace text content or attributes directly
   ↓
6. Convert XML back to string
   ↓
7. Render complete SVG to PDF (svglib)
   ↓
8. Optional: Python overlay for special cases (inline logos)
```

### Template Structure

#### Cover Template Example (`simple.svg`)

```xml
<!-- Static content (never changes) -->
<rect x="0" y="0" width="210" height="100" fill="{{stripe_color}}" />
<text x="105" y="30" text-anchor="middle" font-size="42" fill="#FFFFFF">
  Binder Pokédex
</text>

<!-- Dynamic content (replaced by Python) -->
<text id="section_title" x="105" y="120" text-anchor="middle" font-size="24" fill="#333333">
  Generation I
</text>

<text id="section_subtitle" x="105" y="130" text-anchor="middle" font-size="18" fill="#666666">
  Kanto
</text>

<text id="pokemon_count" x="105" y="147" text-anchor="middle" font-size="14" fill="#666666">
  151 Pokémon in this collection
</text>

<line id="decorative_line" x1="40" y1="151.5" x2="170" y2="151.5" 
      stroke="{{stripe_color}}" stroke-width="1.0" />

<text id="description" x="105" y="158" text-anchor="middle" font-size="11" fill="#666666">
  Pokédex #001 – #151
</text>
```

#### Card Template Example (`classic.svg`)

```xml
<!-- Static structure with {{variables}} -->
<rect x="0" y="0" width="63" height="88" fill="#FFFFFF" />
<rect x="3" y="3" width="57" height="10" fill="{{type_color}}" />

<!-- Dynamic content (replaced by Python) -->
<text id="pokemon_name" x="31.5" y="20" text-anchor="middle" 
      font-family="Helvetica-Bold" font-size="11" fill="#2D2D2D">
  Pikachu
</text>

<image id="pokemon_image" x="6.5" y="30" width="50" height="50" 
       href="data:image/png;base64,..." 
       preserveAspectRatio="xMidYMid meet"/>
```

### Python Code Example

```python
from template_loader import TemplateLoader

# Load SVG
svg_content = TemplateLoader.load_cover_template('simple')

# Substitute {{variables}}
svg_content = TemplateLoader.substitute_variables(svg_content, {
    'stripe_color': '#4A90E2'
})

# Manipulate XML to replace dynamic content
replacements = {
    'section_title': 'Generation II',
    'section_subtitle': 'Johto',
    'pokemon_count': '100 Pokémon in this collection',
    'description': 'Pokédex #152 – #251'
}
svg_content = TemplateLoader.manipulate_svg_xml(svg_content, replacements)

# Render to PDF
TemplateLoader.render_svg_to_canvas(svg_content, canvas, 0, 0)
```

## Template Element Types

### 1. Text Elements

Replace text content:

```python
replacements = {
    'pokemon_name': 'Bulbasaur',
    'section_title': 'Generation I'
}
```

XML manipulation:
```python
element = root.find(".//*[@id='pokemon_name']")
element.text = 'Bulbasaur'
```

### 2. Image Elements

Replace image with data URI:

```python
replacements = {
    'pokemon_image': {
        'href': 'data:image/png;base64,iVBORw0KG...'
    }
}
```

XML manipulation:
```python
element = root.find(".//*[@id='pokemon_image']")
element.set('href', data_uri)
element.set('{http://www.w3.org/1999/xlink}href', data_uri)  # SVG 1.x compat
```

### 3. Attribute Replacement

Replace any attribute:

```python
replacements = {
    'header_rect': {
        'fill': '#FF5733',
        'width': '100'
    }
}
```

## Benefits of This Approach

### ✅ **WYSIWYG Design**
- Preview in Inkscape, Figma, VS Code shows exact final result
- No guessing about coordinate conversions
- Designers see real content, not `{{placeholders}}`

### ✅ **No Coordinate System Issues**
- SVG uses top-left origin (y+ down)
- No Y-axis flipping: `y_pdf = (297 - y_svg) * mm`
- Positions in preview match positions in PDF

### ✅ **Simpler Code**
- No position extraction with regex
- No placeholder removal
- Direct XML manipulation
- Single-stage rendering (SVG contains everything)

### ✅ **Better Maintainability**
- Templates are self-documenting (dummy content shows intent)
- Less magic (no hidden coordinate conversions)
- KISS principle (Keep It Simple, Stupid)

## Special Cases

### Inline Logo Rendering

For Pokemon names with tokens like `[EX]`, `[M]` that need special logo rendering:

1. SVG renders with empty name: `<text id="pokemon_name"></text>`
2. Python overlays name with inline logos using `InlineLogoRenderer`
3. Position calculated from SVG coordinates: `y_reportlab = 88mm - y_svg`

This is a **minimal exception** for functionality that can't be in SVG.

### Dynamic Images (Featured Pokemon)

Cover templates have placeholder rects for featured Pokemon:

```xml
<g id="featured_area">
  <rect x="52.5" y="199" width="45" height="63" fill="#F0F0F0" />
  <rect x="105" y="199" width="45" height="63" fill="#F0F0F0" />
  <rect x="157.5" y="199" width="45" height="63" fill="#F0F0F0" />
</g>
```

Python overlays actual images at these positions using `drawImage()`.

## Migration from Old System

### Old Approach (Position Extraction)
```python
# 1. Extract positions with regex
positions = extract_placeholder_positions(svg_content)  # {'title': {'x': 105mm, 'y': 177mm}}

# 2. Remove placeholders
svg_content = remove_placeholders(svg_content)

# 3. Render empty SVG structure
render_svg_to_canvas(svg_content, canvas, 0, 0)

# 4. Python renders content at extracted positions
canvas.drawString(positions['title']['x'], positions['title']['y'], 'Generation I')
```

**Problems:**
- Y-axis flip: `y = (297 - y_svg) * mm`
- Preview shows empty placeholders
- Two-stage rendering (SVG + Python overlay)
- Complex coordinate conversions

### New Approach (XML Manipulation)
```python
# 1. Substitute {{variables}}
svg_content = substitute_variables(svg_content, {'stripe_color': '#4A90E2'})

# 2. Manipulate XML to replace content
replacements = {'section_title': 'Generation I'}
svg_content = manipulate_svg_xml(svg_content, replacements)

# 3. Render complete SVG
render_svg_to_canvas(svg_content, canvas, 0, 0)
```

**Benefits:**
- No Y-axis conversion
- Preview shows real content
- Single-stage rendering
- Simple direct replacement

## Template Design Guidelines

### 1. Use Real Dummy Content

❌ **Don't:**
```xml
<text id="pokemon_name">{{name}}</text>
```

✅ **Do:**
```xml
<text id="pokemon_name" x="31.5" y="20" text-anchor="middle" 
      font-family="Helvetica-Bold" font-size="11" fill="#2D2D2D">
  Pikachu
</text>
```

### 2. Use IDs for Dynamic Elements

All content that changes per card/page needs an `id` attribute:

```xml
<text id="section_title">Generation I</text>
<text id="pokemon_count">151 Pokémon</text>
<image id="pokemon_image" href="dummy.png" />
```

### 3. Use {{variables}} for Static Substitution

Colors, dimensions, and other static values:

```xml
<rect fill="{{type_color}}" />
<line stroke="{{stripe_color}}" />
```

### 4. SVG Coordinate System

- Origin: **top-left** corner
- X-axis: left (0) → right (210mm for A4)
- Y-axis: top (0) → bottom (297mm for A4)

No conversion needed - this matches the final PDF!

### 5. Preserve Aspect Ratio for Images

```xml
<image id="pokemon_image" 
       preserveAspectRatio="xMidYMid meet"
       ... />
```

## API Reference

### TemplateLoader Methods

#### `manipulate_svg_xml(svg_content, replacements)`

Manipulate SVG via XML DOM.

**Parameters:**
- `svg_content` (str): SVG content as string
- `replacements` (dict): Element replacements
  - Keys: element IDs
  - Values: 
    - `str` for text content
    - `dict` for attributes (e.g., `{'href': '...'}`)

**Returns:** Modified SVG content (str)

**Example:**
```python
replacements = {
    'pokemon_name': 'Bulbasaur',
    'pokemon_image': {'href': 'data:image/png;base64,...'},
    'header_rect': {'fill': '#FF5733'}
}
svg_content = TemplateLoader.manipulate_svg_xml(svg_content, replacements)
```

#### `pil_image_to_data_uri(pil_image, format='PNG')`

Convert PIL Image to data URI for SVG embedding.

**Parameters:**
- `pil_image` (PIL.Image): Image object
- `format` (str): Image format ('PNG', 'JPEG')

**Returns:** Data URI string

**Example:**
```python
data_uri = TemplateLoader.pil_image_to_data_uri(pil_image, 'PNG')
# → 'data:image/png;base64,iVBORw0KGgoAAAANS...'
```

#### `substitute_variables(svg_content, variables)`

Replace Mustache-style {{variable}} placeholders.

**Parameters:**
- `svg_content` (str): SVG content
- `variables` (dict): Variable name → value

**Returns:** SVG with substituted variables (str)

**Example:**
```python
svg_content = TemplateLoader.substitute_variables(svg_content, {
    'type_color': '#F08030',
    'stripe_color': '#4A90E2'
})
```

## Troubleshooting

### SVG Not Rendering

**Issue:** `Failed to render SVG to canvas`

**Solutions:**
1. Check SVG syntax is valid XML
2. Ensure namespace is correct: `xmlns="http://www.w3.org/2000/svg"`
3. Check svglib compatibility (no unsupported features)

### Element Not Found

**Issue:** `Element with id='...' not found in SVG`

**Solutions:**
1. Check element has `id` attribute: `<text id="pokemon_name">`
2. Check spelling matches exactly (case-sensitive)
3. Use XPath to debug: `root.find(".//*[@id='pokemon_name']")`

### Data URI Too Large

**Issue:** SVG file becomes very large with base64 images

**Solutions:**
1. Use smaller images (resize before encoding)
2. Use JPEG for photos (smaller than PNG)
3. Consider external image overlay instead of embedding

### Coordinate Mismatch

**Issue:** Element position in PDF doesn't match SVG preview

**Solutions:**
1. Check you're not using old Y-axis conversion code
2. Verify SVG coordinate system is preserved
3. Check parent transformations don't affect position

## Future Enhancements

- **Inline logo embedding**: Convert `[EX]` tokens to embedded SVG logos
- **Font embedding**: Include custom fonts in SVG for special characters
- **Template validation**: Check SVG has required element IDs before rendering
- **Live preview**: Real-time PDF preview while editing SVG

---

**Last Updated:** 2025-01-XX
**Version:** 2.0 (XML Manipulation / WYSIWYG)
