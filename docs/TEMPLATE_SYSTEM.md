# SVG Template System - Technical Specification

**Version:** 1.0  
**Date:** 6. Februar 2026  
**Status:** Design Phase

---

## 1. Übersicht & Ziele

### Motivation
Das aktuelle Kartenlayout ist hart im Code (`CardRenderer`) implementiert. Änderungen am Design erfordern Code-Änderungen. Ziel ist ein flexibles, datengesteuertes Template-System, das verschiedene Layouts ohne Code-Änderungen ermöglicht.

### Ziele
- ✅ **Trennung von Code und Design**: Layout-Änderungen ohne Python-Code
- ✅ **Mehrere Layouts**: Verschiedene Card-Designs (Classic, Compact, Horizontal, etc.)
- ✅ **Visuell editierbar**: Templates in Inkscape/Figma bearbeitbar
- ✅ **Keine zusätzlichen Dependencies**: Nutzung von ReportLab's integrierter `svglib`
- ✅ **Rückwärtskompatibilität**: Bestehende API bleibt funktional

### Nicht-Ziele (v1.0)
- ❌ Komplexe Layout-Engine (bleibt bei SVG-Einfachheit)
- ❌ GUI-basierter Template-Editor
- ❌ Runtime-Template-Generierung

---

## 2. Template-Architektur

### 2.1 Verzeichnisstruktur

```
config/
  templates/
    cards/              # Einzelkarten-Templates (63mm x 88mm)
      classic.svg           # Aktuelles Design (Header oben, Bild mittig, ID unten)
      compact.svg           # Kleiner Header, größeres Bild
      horizontal.svg        # Querformat-Layout
      retro.svg            # Alte Pokemon-Karten-Stil
      
    pages/              # Seiten-Layout-Templates (A4 = 210mm x 297mm)
      grid_3x3.svg          # 9 Karten pro Seite (aktuell)
      grid_4x2.svg          # 8 Karten pro Seite
      grid_2x4.svg          # Alternative Anordnung
      print_ready.svg       # Mit Schnittmarken & Bleed
      
    covers/             # Deckblatt-Templates (A4)
      simple.svg            # Minimalistisch: Title + Set-Info
      detailed.svg          # Mit Artwork & Logo
      set_overview.svg      # Mit Pokemon-Liste
```

### 2.2 Template-Typen

#### **Card Templates** (cards/)
Definiert das **Design einer einzelnen Karte**.

**Größe:** 63mm x 88mm (Standard Trading Card)

**Verantwortlichkeit:**
- Header-Bereich mit Type-Color
- Pokemon-Name (multilingual, mit Logos)
- Type-Label
- Pokemon-Bild
- ID-Nummer (#001, #002, ...)
- Border & Styling

**Template-Variablen:**
- `{{name}}` - Pokemon-Name
- `{{type}}` - Pokemon-Typ (übersetzt)
- `{{type_color}}` - Hex-Farbe des Typs
- `{{type_color_dark}}` - Dunklere Variante für ID
- `{{id}}` - Pokemon-ID/Nummer
- `{{image_path}}` - Pfad zum Pokemon-Bild

#### **Page Templates** (pages/)
Definiert das **Layout einer PDF-Seite**.

**Größe:** A4 (210mm x 297mm)

**Verantwortlichkeit:**
- Karten-Positionen (Grid-Layout)
- Schnittmarken (Crop Marks)
- Bleed-Area (Druckrand)
- Seitennummern (optional)
- Wasserzeichen (optional)

**Template-Variablen:**
- `{{page_number}}` - Seitenzahl
- `{{total_pages}}` - Gesamtseitenzahl
- `{{card_positions}}` - Liste von (x, y) Koordinaten für Karten

**Besonderheit:** Page Templates enthalten **Platzhalter für Cards**, keine Card-Daten selbst.

#### **Cover Templates** (covers/)
Definiert das **Deckblatt** eines PDF-Binders.

**Größe:** A4 (210mm x 297mm)

**Verantwortlichkeit:**
- Set-Title (z.B. "National Pokédex")
- Set-Range (z.B. "#001 - #151")
- Language-Info
- Artwork/Logo-Bereich
- Optional: Pokemon-Liste

**Template-Variablen:**
- `{{title}}` - Set-Titel
- `{{subtitle}}` - Untertitel (z.B. "Generation 1")
- `{{range_start}}` - Start-ID
- `{{range_end}}` - End-ID
- `{{language}}` - Sprache
- `{{artwork_path}}` - Pfad zu Section-Artwork

---

## 3. SVG-Template-Format

### 3.1 Variablen-Syntax

Templates verwenden **Mustache-Style Syntax** für Variablen:

```xml
<text>{{variable_name}}</text>
<rect fill="{{type_color}}" />
<image href="{{image_path}}" />
```

**Unterstützte Positionen:**
- Text-Content: `<text>{{name}}</text>`
- Attribute: `<rect fill="{{color}}" />`
- Image-Source: `<image href="{{image_path}}" />`

### 3.2 Spezielle Variablen

#### Dynamische Farben
```xml
<!-- Type-Color mit Opacity -->
<rect fill="{{type_color}}" opacity="0.1" />

<!-- Darkened Type-Color für ID -->
<text fill="{{type_color_dark}}">{{id}}</text>
```

#### Conditional Elements (v1.0: via Python Pre-Processing)
```xml
<!-- Logo-Rendering: Wird in Python durch LogoRenderer ersetzt -->
<text id="pokemon_name">{{name}}</text>
<!-- Wenn Name '[EX]' enthält, wird LogoRenderer.draw_text_with_logos() verwendet -->
```

### 3.3 Beispiel: Card Template

```xml
<!-- config/templates/cards/classic.svg -->
<svg width="63mm" height="88mm" xmlns="http://www.w3.org/2000/svg">
  <!-- Card Border -->
  <rect x="0" y="0" width="63mm" height="88mm" 
        fill="#FFFFFF" stroke="#CCCCCC" stroke-width="0.5"/>
  
  <!-- Header Background (Type Color) -->
  <rect x="0" y="76mm" width="63mm" height="12mm" 
        fill="{{type_color}}" opacity="0.1"/>
  
  <!-- Pokemon Name -->
  <text x="31.5mm" y="82mm" text-anchor="middle" 
        font-family="Helvetica-Bold" font-size="11pt" fill="#2D2D2D">
    {{name}}
  </text>
  
  <!-- Type Label -->
  <text x="60mm" y="82mm" text-anchor="end" 
        font-family="Helvetica" font-size="6pt" fill="#5D5D5D">
    {{type}}
  </text>
  
  <!-- Pokemon Image -->
  <image x="10mm" y="20mm" width="43mm" height="50mm" 
         href="{{image_path}}" preserveAspectRatio="xMidYMid meet"/>
  
  <!-- ID Number -->
  <text x="31.5mm" y="8mm" text-anchor="middle" 
        font-family="Helvetica-Bold" font-size="16pt" fill="{{type_color_dark}}">
    {{id}}
  </text>
</svg>
```

### 3.4 Beispiel: Page Template

```xml
<!-- config/templates/pages/grid_3x3.svg -->
<svg width="210mm" height="297mm" xmlns="http://www.w3.org/2000/svg">
  <!-- Crop Marks (Schnittmarken) -->
  <line x1="10mm" y1="0" x2="10mm" y2="5mm" stroke="#000000" stroke-width="0.25"/>
  <!-- ... weitere Schnittmarken ... -->
  
  <!-- Card Placeholder Positions (werden durch Python ersetzt) -->
  <!-- Position 1: Top-Left -->
  <g id="card_slot_0" transform="translate(15mm, 15mm)">
    <!-- Card wird hier eingefügt -->
  </g>
  
  <!-- Position 2: Top-Center -->
  <g id="card_slot_1" transform="translate(78.5mm, 15mm)">
    <!-- Card wird hier eingefügt -->
  </g>
  
  <!-- ... 7 weitere Positionen ... -->
  
  <!-- Page Number -->
  <text x="105mm" y="290mm" text-anchor="middle" font-size="8pt">
    Seite {{page_number}} von {{total_pages}}
  </text>
</svg>
```

---

## 4. Technische Implementierung

### 4.1 Template Loader

**Datei:** `scripts/pdf/lib/rendering/template_loader.py`

**Aufgaben:**
1. SVG-Template-Datei laden
2. Variablen mit Daten ersetzen
3. Spezielle Logik (Logos, Fonts) integrieren
4. SVG → ReportLab Drawing konvertieren

**API:**
```python
class TemplateLoader:
    @staticmethod
    def load_card_template(template_name: str) -> CardTemplate:
        """Load card template from config/templates/cards/"""
        
    @staticmethod
    def load_page_template(template_name: str) -> PageTemplate:
        """Load page template from config/templates/pages/"""
        
    @staticmethod
    def load_cover_template(template_name: str) -> CoverTemplate:
        """Load cover template from config/templates/covers/"""

class CardTemplate:
    def render(self, canvas, pokemon_data: dict, x: float, y: float) -> None:
        """Render card at position (x, y) on canvas"""

class PageTemplate:
    def get_card_positions(self) -> List[Tuple[float, float]]:
        """Get list of (x, y) positions for cards on page"""
        
    def render_background(self, canvas, page_number: int, total_pages: int) -> None:
        """Render page background, crop marks, page numbers"""

class CoverTemplate:
    def render(self, canvas, title: str, range_start: int, range_end: int, 
               language: str, artwork_path: str = None) -> None:
        """Render cover page"""
```

### 4.2 Variable Substitution

**Einfache Variablen:**
```python
svg_content = svg_template.read()
svg_content = svg_content.replace('{{name}}', pokemon_data['name'])
svg_content = svg_content.replace('{{type_color}}', TYPE_COLORS[pokemon_type])
```

**Komplexe Variablen (Images):**
```python
# Image-Referenz in SVG durch data-URI oder temporäre Datei ersetzen
if '{{image_path}}' in svg_content:
    image_data = image_cache.get_image(pokemon_id)
    # Option 1: Data-URI (base64-encoded)
    image_uri = f"data:image/png;base64,{base64.b64encode(image_data)}"
    svg_content = svg_content.replace('{{image_path}}', image_uri)
```

**Type-Colors:**
```python
# Dynamische Farben
type_color = TYPE_COLORS.get(pokemon_type, TYPE_COLORS['Normal'])
type_color_dark = CardRenderer._darken_color(type_color, factor=0.6)

svg_content = svg_content.replace('{{type_color}}', type_color)
svg_content = svg_content.replace('{{type_color_dark}}', type_color_dark)
```

### 4.3 SVG → PDF Rendering

**Via svglib (ReportLab-integriert):**
```python
from svglib.svglib import renderSVG
from reportlab.graphics import renderPDF
from io import BytesIO

# SVG-String → Drawing-Objekt
svg_io = BytesIO(svg_content.encode('utf-8'))
drawing = renderSVG.svg2rlg(svg_io)

# Drawing → Canvas rendern
renderPDF.draw(drawing, canvas, x, y)
```

### 4.4 Integration in CardRenderer

**Backwards-Compatible API:**
```python
class CardRenderer:
    def __init__(self, language: str = 'en', image_cache=None, 
                 card_template: str = None, **kwargs):
        """
        Args:
            card_template: Optional template name (e.g., 'classic', 'compact')
                          If None, uses legacy rendering code
        """
        self.card_template = card_template
        if card_template:
            self.template_obj = TemplateLoader.load_card_template(card_template)
        
    def render_card(self, canvas_obj, pokemon_data: dict, x: float, y: float, ...):
        if self.card_template:
            # Template-based rendering
            self.template_obj.render(canvas_obj, pokemon_data, x, y)
        else:
            # Legacy rendering (aktueller Code)
            # ... bestehende Implementierung ...
```

---

## 5. CLI Integration

### 5.1 Neue Parameter

```bash
python scripts/pdf/generate.py \
  --scope Pokedex \
  --language de \
  --card-template classic \      # NEU: Card-Template
  --page-template grid_3x3 \     # NEU: Page-Template
  --cover-template simple        # NEU: Cover-Template
```

### 5.2 Defaults & Fallbacks

**Wenn keine Templates angegeben:**
- Verwendet **Legacy-Rendering** (aktueller CardRenderer-Code)
- Keine Breaking Changes

**Wenn Templates angegeben:**
- Lädt Templates aus `config/templates/`
- Fallback auf `classic`/`grid_3x3`/`simple` bei Fehler

### 5.3 Template-Listing

```bash
# Verfügbare Templates anzeigen
python scripts/pdf/generate.py --list-templates

# Output:
# Card Templates:
#   - classic (default)
#   - compact
#   - horizontal
#   - retro
#
# Page Templates:
#   - grid_3x3 (default)
#   - grid_4x2
#   - print_ready
#
# Cover Templates:
#   - simple (default)
#   - detailed
#   - set_overview
```

---

## 6. Migration & Kompatibilität

### 6.1 Phase 1: Template-System aufbauen
- ✅ Template-Loader implementieren
- ✅ `classic.svg` = 1:1 Kopie des aktuellen Designs
- ✅ Template-Rendering parallel zu Legacy-Code
- ✅ Tests mit beiden Rendering-Paths

### 6.2 Phase 2: Default-Templates erstellen
- ✅ `cards/classic.svg`
- ✅ `pages/grid_3x3.svg`
- ✅ `covers/simple.svg`
- ✅ Dokumentation & Beispiele

### 6.3 Phase 3: Zusätzliche Templates
- ✅ Alternative Card-Layouts (compact, horizontal, retro)
- ✅ Alternative Page-Layouts (4x2, print_ready)
- ✅ Alternative Cover-Layouts (detailed, set_overview)

### 6.4 Phase 4: Template-Editor (optional)
- ⚠️ GUI-Tool zum Erstellen/Bearbeiten von Templates
- ⚠️ Live-Preview
- ⚠️ Template-Validator

---

## 7. Technische Anforderungen

### 7.1 Dependencies

**Neue Dependencies:** ❌ Keine!

**Bestehende Dependencies:**
- `reportlab` (bereits vorhanden)
- `svglib` (in ReportLab integriert)

### 7.2 Performance

**Erwartung:**
- SVG-Parsing: ~5-10ms pro Template (einmalig beim Laden)
- SVG→PDF-Rendering: ~1-2ms pro Karte (minimal langsamer als Legacy)
- Caching: Templates werden beim Start geladen, nicht pro Karte

**Optimierungen:**
- Template-Caching in Memory
- Variable-Substitution vor SVG-Parsing (String-Replace)
- Lazy-Loading von Templates

### 7.3 Validierung

**Template-Validierung:**
- SVG-Syntax korrekt?
- Alle Variablen definiert?
- Dimensionen korrekt (63x88mm für Cards, A4 für Pages)?

**Runtime-Validierung:**
- Fehlende Variablen → Warning + Fallback
- Fehlerhafte SVG → Exception + Legacy-Rendering

---

## 8. Beispiel-Workflows

### 8.1 Neues Card-Layout erstellen

```bash
# 1. Template erstellen (Inkscape/Figma → SVG-Export)
# 2. Variablen einfügen ({{name}}, {{type}}, etc.)
# 3. Template speichern
cp my_design.svg config/templates/cards/custom.svg

# 4. Template testen
python scripts/pdf/generate.py \
  --scope Pokedex \
  --card-template custom \
  --output test.pdf

# 5. Template anpassen & iterieren
# 6. Template committen & teilen
```

### 8.2 Print-Ready PDF mit Schnittmarken

```bash
python scripts/pdf/generate.py \
  --scope Pokedex \
  --card-template classic \
  --page-template print_ready \
  --output pokedex_print.pdf

# print_ready.svg enthält:
# - Schnittmarken (Crop Marks)
# - Bleed-Area (3mm)
# - Farbprofil-Info (CMYK)
```

### 8.3 Mix & Match Templates

```bash
# Kompakte Karten auf 4x2 Grid
python scripts/pdf/generate.py \
  --scope ExGen1 \
  --card-template compact \
  --page-template grid_4x2 \
  --cover-template detailed

# Retro-Karten auf Classic Grid
python scripts/pdf/generate.py \
  --scope SV01 \
  --card-template retro \
  --page-template grid_3x3 \
  --cover-template simple
```

---

## 9. Offene Fragen & Diskussionspunkte

### 9.1 Logo-Rendering

**Anforderung:** Pokemon-Namen können Logo-Tokens enthalten (z.B. `"Charizard [EX]"`, `"[M] Venusaur [EX]"`). Diese Tokens sollen als echte Logo-Bilder (PNG/SVG) gerendert werden.

**Design-Prinzip:** Das SVG-Template definiert **nur die Position** des Namens. Die Logo-Ersetzung passiert automatisch durch Python-Logik.

---

#### Finale Lösung: Inline-Logo-Rendering

**Konzept:** Text mit Tokens wird **automatisch geparst**, Logos werden als Bilder **inline eingefügt**.

**Workflow:**
1. SVG-Template definiert **nur Position** des Namens: `<text x="31.5mm" y="82mm">{{name}}</text>`
2. Python parst automatisch: `"Charizard [EX]"` → `["Charizard ", <Logo: ex_gen2>]`
3. Text + Logo-Bilder werden **inline auf Canvas gerendert**

---

#### 1. SVG-Template (einfach)

Das Template definiert nur die Position, nicht das Logo-Handling:

```xml
<!-- config/templates/cards/classic.svg -->
<svg width="63mm" height="88mm" xmlns="http://www.w3.org/2000/svg">
  <!-- Card Border -->
  <rect x="0" y="0" width="63mm" height="88mm" 
        fill="#FFFFFF" stroke="#CCCCCC" stroke-width="0.5"/>
  
  <!-- Header Background -->
  <rect x="0" y="76mm" width="63mm" height="12mm" 
        fill="{{type_color}}" opacity="0.1"/>
  
  <!-- Pokemon Name - wird durch Python gerendert, nicht durch SVG -->
  <!-- Platzhalter für Position -->
  <g id="name_anchor" transform="translate(31.5, 82)">
    <!-- Leer - Python rendert Name hier direkt auf Canvas -->
  </g>
  
  <!-- Type Label -->
  <text x="60mm" y="82mm" text-anchor="end" font-size="6pt">
    {{type}}
  </text>
  
  <!-- Pokemon Image -->
  <image x="10mm" y="20mm" width="43mm" height="50mm" 
         href="{{image_path}}" />
  
  <!-- ID Number -->
  <text x="31.5mm" y="8mm" text-anchor="middle" font-size="16pt">
    {{id}}
  </text>
</svg>
```

**Wichtig:** Der Name-Bereich ist **leer** im SVG. Python übernimmt das komplette Name-Rendering.

---

#### 2. Python: Automatic Inline-Logo-Rendering

**Logo-Dateien-Struktur:**
```
images/logos/
  ex.png          # Gen1 "ex" Logo (8mm × 3mm)
  ex_gen2.png     # Gen2 "EX" Logo (10mm × 5mm)
  ex_gen3.png     # Gen3 "ex" Logo (8mm × 4mm)
  ex_tera.png     # Tera ex Logo (12mm × 5mm)
  mega.png        # Mega Symbol [M] (6mm × 6mm)
```

**Core-Funktion: Text mit Logos rendern**

```python
def render_name_with_inline_logos(canvas, text, x, y, font_name, font_size, 
                                   text_color='#2D2D2D'):
    """
    Rendert Text mit inline Logo-Bildern.
    
    Args:
        canvas: ReportLab Canvas
        text: Pokemon-Name mit Tokens, z.B. "Charizard [EX]"
        x: X-Position (Zentrum)
        y: Y-Position (Baseline)
        font_name: Font-Familie
        font_size: Font-Größe in Points
        text_color: Text-Farbe (Hex)
    
    Beispiele:
        "Charizard [EX]" → "Charizard " + <ex_gen2.png>
        "[M] Venusaur [EX]" → <mega.png> + " Venusaur " + <ex_gen2.png>
        "Rocket's Pikachu" → "Rocket's Pikachu" (kein Logo)
    """
    import re
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.lib.colors import HexColor
    
    # 1. Parse Text: Finde alle Logo-Tokens
    logo_pattern = r'\[(EX_TERA|EX_NEW|EX|M)\]'
    segments = []
    last_end = 0
    
    for match in re.finditer(logo_pattern, text):
        # Text vor Token
        if match.start() > last_end:
            segments.append({
                'type': 'text',
                'content': text[last_end:match.start()]
            })
        
        # Logo-Token
        logo_token = match.group(1)
        logo_type = TOKEN_TO_LOGO_TYPE.get(logo_token, 'ex')
        segments.append({
            'type': 'logo',
            'logo_type': logo_type
        })
        
        last_end = match.end()
    
    # Text nach letztem Token
    if last_end < len(text):
        segments.append({
            'type': 'text',
            'content': text[last_end:]
        })
    
    # Wenn keine Segmente (kein Regex-Match), ist es nur Text
    if not segments:
        segments = [{'type': 'text', 'content': text}]
    
    # 2. Berechne Gesamtbreite für Zentrierung
    total_width_mm = 0
    
    for segment in segments:
        if segment['type'] == 'text':
            # Textbreite in Points
            width_points = stringWidth(segment['content'], font_name, font_size)
            width_mm = width_points * 0.3527778  # Points → mm
            total_width_mm += width_mm
        else:  # logo
            logo_width, _ = get_logo_dimensions(segment['logo_type'])
            total_width_mm += logo_width
    
    # 3. Startposition (zentriert)
    current_x = x - (total_width_mm * mm / 2)
    
    # 4. Rendere Segmente nacheinander
    canvas.setFont(font_name, font_size)
    canvas.setFillColor(HexColor(text_color))
    
    for segment in segments:
        if segment['type'] == 'text':
            # Text rendern
            canvas.drawString(current_x, y, segment['content'])
            
            # Weiter nach rechts
            text_width_points = stringWidth(segment['content'], font_name, font_size)
            current_x += text_width_points
        
        else:  # logo
            # Logo-Bild rendern
            logo_type = segment['logo_type']
            logo_path = Path('images/logos') / f"{logo_type}.png"
            
            if logo_path.exists():
                logo_width, logo_height = get_logo_dimensions(logo_type)
                
                # Logo vertikal zentriert zur Text-Baseline
                # Font-Size ≈ Cap-Height, Logo sollte leicht über Baseline
                logo_y = y + (font_size * 0.2)  # 20% über Baseline
                
                canvas.drawImage(
                    str(logo_path),
                    current_x,
                    logo_y,
                    width=logo_width * mm,
                    height=logo_height * mm,
                    preserveAspectRatio=True,
                    mask='auto'  # PNG-Transparenz
                )
                
                current_x += logo_width * mm
            else:
                # Fallback: Token als Text (falls Logo fehlt)
                fallback_text = f"[{segment['logo_type']}]"
                canvas.drawString(current_x, y, fallback_text)
                text_width = stringWidth(fallback_text, font_name, font_size)
                current_x += text_width


# Token → Logo-Type Mapping
TOKEN_TO_LOGO_TYPE = {
    'EX_TERA': 'ex_tera',   # [EX_TERA] → ex_tera.png
    'EX_NEW': 'ex_gen3',    # [EX_NEW] → ex_gen3.png
    'EX': 'ex_gen2',        # [EX] → ex_gen2.png
    'M': 'mega',            # [M] → mega.png
}

# Logo-Dimensionen (Breite × Höhe in mm)
LOGO_DIMENSIONS = {
    'ex': (8, 3),           # Gen1: klein, lowercase
    'ex_gen2': (10, 5),     # Gen2: größer, uppercase
    'ex_gen3': (8, 4),      # Gen3: neues Design
    'ex_tera': (12, 5),     # Tera: am größten
    'mega': (6, 6),         # Mega: quadratisch
}

def get_logo_dimensions(logo_type):
    """Gibt (width, height) in mm zurück"""
    return LOGO_DIMENSIONS.get(logo_type, (8, 3))
```

---

#### 3. Integration in Template-Rendering

**Template-Loader bereitet SVG vor:**

```python
def render_card_template(canvas, template_path, pokemon_data, x, y):
    """
    Kompletter Workflow: SVG-Template → Canvas mit Logos
    """
    # 1. Template laden
    with open(template_path) as f:
        template_content = f.read()
    
    # 2. Standard-Variablen ersetzen
    template_content = template_content.replace('{{type_color}}', get_type_color(pokemon_data))
    template_content = template_content.replace('{{type}}', get_type_name(pokemon_data))
    template_content = template_content.replace('{{id}}', format_pokemon_id(pokemon_data))
    template_content = template_content.replace('{{image_path}}', get_image_path(pokemon_data))
    
    # Name wird NICHT ersetzt - bleibt leer im SVG
    
    # 3. SVG → Drawing
    svg_io = BytesIO(template_content.encode('utf-8'))
    drawing = renderSVG.svg2rlg(svg_io)
    
    # 4. Drawing → Canvas (ohne Name)
    renderPDF.draw(drawing, canvas, x, y)
    
    # 5. Name mit Logos nachträglich auf Canvas rendern
    name = get_pokemon_name(pokemon_data)  # z.B. "Charizard [EX]"
    
    # Position aus Template (Name-Anchor bei 31.5mm, 82mm)
    name_x = x + 31.5 * mm
    name_y = y + 82 * mm
    
    render_name_with_inline_logos(
        canvas,
        name,
        name_x,
        name_y,
        font_name='Helvetica-Bold',
        font_size=11,
        text_color='#2D2D2D'
    )
```

---

#### 4. Vorteile dieser Lösung

✅ **Template bleibt einfach:** Nur Position definieren, keine Logo-Logik  
✅ **Token überall:** `"[M] Charizard [EX]"` funktioniert automatisch  
✅ **Echte Logo-Bilder:** PNG/SVG-Dateien, nicht Vektorgrafik  
✅ **Automatisches Parsing:** Wie aktueller `LogoRenderer`  
✅ **Fallback-sicher:** Wenn Logo fehlt, wird Token als Text gerendert  
✅ **Mehrere Tokens:** Beliebig viele Logos pro Name möglich  
✅ **Wiederverwendbar:** Gleiche Funktion für Cover, Pages, etc.

---

#### 5. Beispiel-Ergebnisse

| Input (pokemon_data) | Rendering-Ergebnis |
|----------------------|-------------------|
| `"Pikachu"` | `Pikachu` (nur Text) |
| `"Charizard [EX]"` | `Charizard` <img src="ex_gen2.png" height="12"> |
| `"[M] Venusaur [EX]"` | <img src="mega.png" height="12"> `Venusaur` <img src="ex_gen2.png" height="12"> |
| `"Rayquaza [EX_TERA]"` | `Rayquaza` <img src="ex_tera.png" height="16"> |
| `"Rocket's Pikachu [EX]"` | `Rocket's Pikachu` <img src="ex_gen2.png" height="12"> |

---

#### 6. Migration von bestehendem Code

**Aktueller LogoRenderer (Vektorgrafik):**
```python
LogoRenderer.draw_text_with_logos(
    canvas, "Charizard [EX]", x, y, 
    font_name, font_size, context='card'
)
```

**Neuer Inline-Logo-Renderer (Bilder):**
```python
render_name_with_inline_logos(
    canvas, "Charizard [EX]", x, y,
    font_name, font_size, text_color='#2D2D2D'
)
```

→ **Fast identische API**, kann als Drop-in-Replacement verwendet werden!

### 9.2 Font-Handling ✅ ENTSCHIEDEN

**Finale Lösung: Option 2 - Python Font-Mapping via FontManager**

**Konzept:** SVG-Template verwendet **generische Font-Namen**, Python wählt **sprachspezifischen Font**.

**SVG-Template:**
```xml
<!-- Template bleibt sprachneutral -->
<text font-family="{font_placeholder}" font-size="11pt">
  {{name}}
</text>
```

**Python-Logik:**
```python
def render_with_language_font(canvas, text, x, y, language, bold=True):
    """
    Wählt Font basierend auf Sprache (via FontManager)
    """
    # FontManager kennt bereits alle Sprachen
    font_name = FontManager.get_font_name(language, bold=bold)
    canvas.setFont(font_name, font_size)
    canvas.drawString(x, y, text)

# Beispiel:
# language='ja' → font_name='NotoSansJP-Bold'
# language='ko' → font_name='NotoSansKR-Bold'
# language='de' → font_name='Helvetica-Bold'
```

**Vorteile:**
- ✅ **Nutzt bestehenden FontManager** (keine Duplikation)
- ✅ **Template bleibt sprachneutral** (ein Template für alle Sprachen)
- ✅ **Automatische Font-Registrierung** (FontManager macht das bereits)
- ✅ **Konsistent mit Logo-Rendering** (gleicher Ansatz)

**Implementierung:**
Bei Text-Rendering (Name, Type, ID, etc.) wird `FontManager.get_font_name(language)` verwendet, bevor Text auf Canvas gerendert wird. SVG-Template muss keine Font-Details kennen.

### 9.3 Image-Caching ✅ ENTSCHIEDEN

**Finale Lösung: Option 3 - Python Image-Rendering auf Canvas**

**Konzept:** Ähnlich wie Name/Logos wird das Pokemon-Bild **separat auf Canvas gerendert**.

**SVG-Template:**
```xml
<!-- Template definiert nur Position/Größe des Bildes -->
<rect id="image_area" x="10mm" y="20mm" width="43mm" height="50mm" 
      fill="#F0F0F0" />  <!-- Platzhalter-Farbe (optional) -->
```

**Python-Logik:**
```python
def render_pokemon_image(canvas, pokemon_data, image_cache, x, y, width, height):
    """
    Lädt Bild aus Cache und rendert es auf Canvas
    """
    pokemon_id = pokemon_data.get('pokemon_id') or pokemon_data.get('id')
    image_url = pokemon_data.get('image_url')
    
    # Bild aus Cache holen (wie aktuell)
    image_data = image_cache.get_image(pokemon_id, url=image_url)
    
    if image_data:
        # ImageReader für PNG-Transparenz
        from reportlab.lib.utils import ImageReader
        if isinstance(image_data, str):
            image_data = ImageReader(image_data)
        
        # Auf Canvas rendern
        canvas.drawImage(
            image_data,
            x, y,
            width=width,
            height=height,
            preserveAspectRatio=True,
            mask='auto'
        )
```

**Vorteile:**
- ✅ **Nutzt bestehenden image_cache** (keine Änderung nötig)
- ✅ **Keine temporären Dateien**
- ✅ **Konsistent mit Name/Logo-Rendering** (alles auf Canvas)
- ✅ **SVG bleibt klein** (keine eingebetteten Bilder)
- ✅ **PNG-Transparenz funktioniert**

**Workflow:**
1. SVG definiert Bild-Position (Rechteck als Platzhalter)
2. SVG → Canvas rendern (ohne Bild)
3. Python lädt Bild aus Cache
4. Python rendert Bild auf Canvas an definierter Position

### 9.4 Template-Validation ⚠️ NICE-TO-HAVE

**Status:** Nicht für v1.0, optional für v1.1+

**Geplante Features (später):**
- ✅ SVG-Syntax prüfen
- ✅ Variablen-Vollständigkeit prüfen
- ✅ Dimensionen validieren (63x88mm für Cards, A4 für Pages)
- ✅ Preview-PNG generieren
- ✅ Template-Dokumentation generieren

**CLI (geplant für v1.1):**
```bash
python scripts/pdf/validate_template.py config/templates/cards/custom.svg

# Output:
# ✓ SVG-Syntax valid
# ✓ All variables defined: {{name}}, {{type}}, {{type_color}}, {{id}}
# ✓ Dimensions correct: 63mm x 88mm
# ✓ Preview generated: custom_preview.png
```

**Priorität:** Niedrig - Erstmal Basis-System zum Laufen bringen, Validierung kann später hinzugefügt werden.

---

## 10. Zusammenfassung der Entscheidungen

### ✅ Finale Architektur-Entscheidungen:

| Bereich | Entscheidung | Begründung |
|---------|--------------|------------|
| **Logo-Rendering** | Inline-Logo mit Bildern (9.1) | Token-Position flexibel, echte Logo-Bilder |
| **Font-Handling** | Python Font-Mapping (9.2) | Nutzt FontManager, sprachneutrale Templates |
| **Image-Caching** | Python Canvas-Rendering (9.3) | Konsistent, nutzt bestehenden Cache |
| **Template-Validation** | v1.1 (Nice-to-have) (9.4) | Fokus auf Basis-System zuerst |

### 🎯 Template-System-Prinzipien:

1. **SVG definiert nur Positionen** - keine komplexe Logik
2. **Python macht das Rendering** - Name, Logos, Bilder, Fonts
3. **Wiederverwendung** - FontManager, ImageCache, LogoRenderer-Konzept
4. **Zwei-Pass-Rendering:**
   - Pass 1: SVG → Canvas (Struktur, Farben, statische Elemente)
   - Pass 2: Python → Canvas (Dynamische Inhalte: Name+Logos, Bild)

---

## 11. Zeitplan & Aufwand

### 10.1 Aufwandsschätzung

| Phase | Aufgaben | Aufwand | Status |
|-------|----------|---------|--------|
| **Phase 1** | Template-Loader, SVG-Parser, Variable-Substitution | 2-3h | Geplant |
| **Phase 2** | Card-Template (classic.svg) | 1h | Geplant |
| **Phase 3** | Page-Template (grid_3x3.svg) | 1h | Geplant |
| **Phase 4** | Cover-Template (simple.svg) | 1h | Geplant |
| **Phase 5** | CardRenderer-Integration | 1-2h | Geplant |
| **Phase 6** | CLI-Parameter & Tests | 1h | Geplant |
| **Gesamt** | - | **7-9h** | - |

### 10.2 Deliverables

**v1.0 (MVP):**
- ✅ Template-Loader & SVG-Rendering
- ✅ 1 Card-Template (classic)
- ✅ 1 Page-Template (grid_3x3)
- ✅ 1 Cover-Template (simple)
- ✅ CLI-Integration (`--card-template`, etc.)
- ✅ Dokumentation (diese Datei)

**v1.1 (Erweiterung):**
- ⚠️ 2-3 zusätzliche Card-Templates
- ⚠️ 1-2 zusätzliche Page-Templates
- ⚠️ Template-Validator

**v2.0 (Optional):**
- ⚠️ Template-Editor (GUI)
- ⚠️ Template-Marketplace (Community-Templates)

---

## 11. Sicherheit & Validierung

### 11.1 SVG-Sicherheit

**Risiken:**
- SVG kann JavaScript enthalten (`<script>`)
- SVG kann externe Ressourcen laden (`<image href="http://...">`)
- SVG kann XXE-Angriffe enthalten (XML External Entities)

**Gegenmaßnahmen:**
- ✅ Nur lokale Templates (kein User-Upload)
- ✅ SVG-Sanitization (externe Scripts entfernen)
- ✅ Whitelist für erlaubte SVG-Elemente

### 11.2 Variable-Injection

**Risiko:** Böswillige Daten in Variablen (z.B. `{{name}}` enthält SVG-Code)

**Gegenmaßnahmen:**
- ✅ XML-Escaping für alle Variablen
- ✅ Validierung von Pokemon-Daten (bereits vorhanden)

---

## 12. Testing-Strategie

### 12.1 Unit-Tests

**Template-Loader:**
- ✅ SVG-Parsing
- ✅ Variable-Substitution
- ✅ Fehlerhandling (fehlende Dateien, ungültiges SVG)

**Template-Rendering:**
- ✅ SVG → Drawing Konvertierung
- ✅ Drawing → Canvas Rendering
- ✅ Position & Dimensionen korrekt

### 12.2 Integration-Tests

**End-to-End:**
- ✅ Template laden → Daten einfügen → PDF generieren
- ✅ Vergleich Legacy vs. Template-Rendering (visuell)

### 12.3 Visual Regression Tests

**Tool:** `pixelmatch` (Python: `Pillow` + Pixel-Vergleich)

**Workflow:**
1. PDF → PNG konvertieren
2. PNG mit Referenz-Bild vergleichen
3. Differenzen markieren

---

## 13. Dokumentation für User

**Neue Dateien:**
- `docs/TEMPLATE_SYSTEM.md` (diese Datei) - Technische Spezifikation
- `docs/TEMPLATE_GUIDE.md` - User-Guide (Templates erstellen)
- `config/templates/README.md` - Template-Übersicht

**User-Guide Inhalte:**
- Wie erstelle ich ein Template? (Inkscape/Figma Tutorial)
- Welche Variablen gibt es?
- Wie teste ich ein Template?
- Best Practices

---

## 14. Zusammenfassung & Next Steps

### 14.1 Zusammenfassung

Das SVG-Template-System ermöglicht:
- ✅ **Flexibles Design** ohne Code-Änderungen
- ✅ **Mehrere Layouts** (Card, Page, Cover)
- ✅ **Visuell editierbar** (Inkscape/Figma)
- ✅ **Keine zusätzlichen Dependencies**
- ✅ **Rückwärtskompatibel** (Legacy-Code bleibt)

### 14.2 Nächste Schritte

**Nach Review dieser Spezifikation:**
1. ✅ Feedback einarbeiten
2. ✅ Phase 1 implementieren (Template-Loader)
3. ✅ Phase 2-4 implementieren (Default-Templates)
4. ✅ Phase 5-6 implementieren (Integration & CLI)
5. ✅ Testing & Dokumentation

**Freigabe benötigt für:**
- [ ] Verzeichnisstruktur (`config/templates/`)
- [ ] Template-Format (SVG + Variablen-Syntax)
- [ ] CLI-Parameter (`--card-template`, etc.)
- [ ] Logo-Rendering-Strategie (Option 1, 2, oder 3?)
- [ ] Font-Handling-Strategie (Option 1, 2, oder 3?)

---

**Review-Status:** ⏳ Warte auf Feedback

**Fragen? Anmerkungen?** → Bitte in diesem Dokument markieren oder separat kommunizieren.
