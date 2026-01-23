# Pokémon Variants - Architecture & Data Structure

**Current Status:** Mega Evolution + EX Generations 1-3 ✅  
**Last Updated:** January 23, 2026  
**Purpose:** Complete architecture and data structure specification for Pokémon variant collections

---

## Table of Contents

1. [Overview](#overview)
2. [Design Principles](#design-principles)
3. [Data Structure Specification](#data-structure-specification)
4. [Architecture & Data Flow](#architecture--data-flow)
5. [Rendering Logic](#rendering-logic)
6. [Multilingual Support](#multilingual-support)
7. [Adding New Variants](#adding-new-variants)

---

## Overview

The Variants feature enables generation of separate collection binders for Pokémon variants. The system uses a unified, data-driven architecture that works identically for both Pokédex (Generations) and Variants (EX, Mega, etc.).

**Currently Implemented:**
- **Mega Evolution:** 79 Pokémon with X/Y forms
- **EX Generation 1:** 119 Pokémon including Delta Species
- **EX Generation 2:** 166 Pokémon with Mega/Primal forms
- **EX Generation 3:** 40 Pokémon with Tera forms
- Full 9-language support
- Professional PDF generation with cutting guides

---

## Design Principles

1. **Top-Level nur Metadaten** - keine Deckblatt-Informationen
2. **Jede Section selbstbeschreibend** - title, subtitle, color_hex, prefix, suffix, iconic_pokemon
3. **Daten-gesteuert** - keine Code-Sonderlocken oder Typ-Checks
4. **Vollständig mehrsprachig** - alle Texte in allen 9 Sprachen
5. **Einheitliche Struktur** - Pokédex und Variants verwenden identisches Schema

---

## Data Structure Specification

### Top-Level Structure

```json
{
  "type": "generation|variant",        // Typ der Collection
  "name": "string",                    // Allgemeiner Name (PDF-Metadaten)
  "sections": { ... }                  // Alle Section-Daten
}
```

**NICHT auf Top-Level:**
- title, subtitle, iconic_pokemon
- color_hex, prefix, suffix (→ in Sections)

### Section Structure

**Jede Section ist völlig selbstständig und identisch aufgebaut:**

```json
"section_id": {
  "section_id": "string",              // "normal", "rockets", "mega", "primal", etc.
  "color_hex": "string",               // Header-Farbe (z.B. "#FFD700")
  "prefix": "string",                  // Name-Präfix für ALLE Pokémon (z.B. "Mega", "Rocket's")
  "suffix": "string",                  // Name-Suffix für ALLE Pokémon (z.B. "ex", "[EX]")
  
  "title": {
    "de": "string",                    // Kann Logo-Tags enthalten: [EX], [M], etc.
    "en": "string",
    "fr": "string",
    "es": "string",
    "it": "string",
    "ja": "string",
    "ko": "string",
    "zh_hans": "string",
    "zh_hant": "string"
  },
  
  "subtitle": {
    "de": "string",                    // Kann Logo-Tags enthalten
    "en": "string",
    // ... alle Sprachen
  },
  
  "iconic_pokemon": [1, 6, 9],         // Poster-Pokémon für Deckblatt (IDs)
  "pokemon": [ ... ]                   // Array mit Pokémon-Daten
}
```

### Pokémon Entry Structure

**Basis-Struktur (alle erforderlich):**

```json
{
  "id": 25,                            // Pokédex-Nummer
  "name": {
    "de": "Pikachu",
    "en": "Pikachu",
    "fr": "Pikachu",
    "es": "Pikachu",
    "it": "Pikachu",
    "ja": "ピカチュウ",
    "ko": "피카츄",
    "zh_hans": "皮卡丘",
    "zh_hant": "皮卡丘"
  },
  "types": ["Electric"],
  "image_url": "https://raw.githubusercontent.com/.../25.png"
}
```

**Optional - Überschreiben von Section-Werten:**

```json
{
  "id": 295,
  "prefix": "Imakuni?'s",              // OPTIONAL: Überschreibt Section-prefix
  "suffix": "",                        // OPTIONAL: Überschreibt Section-suffix
  "variant_form": "delta",             // OPTIONAL: Spezialform ("delta", "x", "y")
  "name": { ... }
}
```

### variant_form Spezialfälle

**Verwendung:**
- Section-Prefix/Suffix gelten für **ALLE** Pokémon in der Section
- Pokémon-Prefix/Suffix überschreiben Section-Werte **nur für spezifische Pokémon**
- `variant_form` wird für Spezial-Rendering verwendet

**Unterstützte Werte:**

| Wert | Verwendung | Beispiel-Output |
|------|------------|-----------------|
| `"delta"` | Delta Species (Δ Symbol an suffix) | "Dragoran ex δ" |
| `"x"` | Mega Evolution X Form | "Mega Glurak X ex" |
| `"y"` | Mega Evolution Y Form | "Mega Glurak Y ex" |

**Rendering-Reihenfolge:**
1. Prefix wird vor den Namen gestellt (falls vorhanden)
2. variant_form "x"/"y" wird nach dem Namen eingefügt (falls vorhanden)
3. Suffix wird am Ende angehängt (falls vorhanden)
4. variant_form "delta" fügt δ an den Suffix an (falls vorhanden)

**Beispiele:**

```json
// Delta Species
{
  "id": 149,
  "variant_form": "delta",
  "name": {"de": "Dragoran"}
}
// Section: prefix="", suffix="ex"
// → Output: "Dragoran ex δ"

// Mega X/Y
{
  "id": 6,
  "variant_form": "x",
  "name": {"de": "Glurak"}
}
// Section: prefix="Mega", suffix="ex"
// → Output: "Mega Glurak X ex"

// Pokémon-Override
{
  "id": 295,
  "prefix": "Imakuni?'s",
  "name": {"de": "Krawumms"}
}
// Section: prefix="", suffix="ex"
// → Output: "Imakuni?'s Krawumms ex"
```

### Complete Example: variants_mega.json

```json
{
  "type": "variant",
  "name": "Mega Evolution",
  "sections": {
    "normal": {
      "section_id": "normal",
      "color_hex": "#FFD700",
      "prefix": "Mega",
      "suffix": "ex",
      "title": {
        "de": "Mega Entwicklung",
        "en": "Mega Evolution",
        "fr": "Méga-Évolution",
        // ... other languages
      },
      "subtitle": {
        "de": "[MEGA]",
        "en": "[MEGA]",
        // ... other languages
      },
      "iconic_pokemon": [6, 150, 384],
      "pokemon": [
        {
          "id": 3,
          "name": {
            "en": "Venusaur",
            "de": "Bisaflor",
            // ... other languages
          },
          "types": ["Grass", "Poison"],
          "image_url": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/10033.png",
          "form_id": 10033,
          "form_code": "#003_MEGA"
        },
        {
          "id": 6,
          "variant_form": "x",
          "name": {
            "en": "Charizard",
            "de": "Glurak",
            // ... other languages
          },
          "types": ["Fire", "Flying"],
          "image_url": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/10034.png",
          "form_id": 10034,
          "form_code": "#006_MEGA_X"
        }
      ]
    }
  }
}
```

**Key Fields:**
- **Top-Level:**
  - `type`: Always "variant"
  - `name`: Collection name (for PDF metadata)
  - `sections`: Object with section definitions

- **Section-Level:**
  - `section_id`: Identifier (e.g., "normal", "mega", "rockets")
  - `color_hex`: Header color
  - `prefix`: Name prefix for all Pokémon (e.g., "Mega", "Rocket's")
  - `suffix`: Name suffix for all Pokémon (e.g., "ex", "[EX]")
  - `title`, `subtitle`: Multilingual cover page text
  - `iconic_pokemon`: Pokémon IDs for cover page
  - `pokemon`: Array of Pokémon entries

- **Pokémon-Level:**
  - `id`: Base Pokémon ID
  - `name`: Multilingual name object
  - `types`: Type array
  - `image_url`: Official artwork URL
  - `form_id`, `form_code`: Form identifiers
  - `variant_form`: Optional ("delta", "x", "y") for special rendering
  - `prefix`, `suffix`: Optional overrides for section values

### Pokédex vs. Variants Unterschiede

| Aspekt | Pokédex (Generationen) | Variants (EX, Mega, etc.) |
|--------|------------------------|---------------------------|
| **type** | `"generation"` | `"variant"` |
| **sections** | Nur `"normal"` Section | Mehrere möglich: normal, rockets, mega, etc. |
| **prefix** | Leer | "Mega", "Rocket's", etc. |
| **suffix** | Leer oder "Gen N" | Logo-Tags: "ex", "[EX]", "[M]", etc. |
| **title** | Generation + Region | Serienname (z.B. "Klassische ex Serie") |
| **subtitle** | Pokédex Range (#001 – #151) | Serienuntertitel mit ggf. Logo-Tag |

**Wichtig:** Beide Typen verwenden die identische Section-Struktur. Der Renderer benötigt keine Typ-Checks.

---

## Architecture & Data Flow

### High-Level Data Flow

```
Data Layer (JSON)
    ↓
    Variant JSON Files (/data/variants/)
    ├── meta.json              → Metadata über alle Kategorien
    ├── variants_mega.json     → 79 Pokémon (Mega Evolution)
    ├── variants_ex_gen1.json  → 119 Pokémon (EX Gen1 + Delta Species)
    ├── variants_ex_gen2.json  → 166 Pokémon (EX Gen2)
    └── variants_ex_gen3.json  → 40 Pokémon (EX Gen3)
    
Processing Layer
    ↓
    generate_pdf.py --type variant [--variant mega_evolution] [--language de]
    ├── VariantPDFGenerator    → Liest sections, generiert cover + cards
    ├── CardRenderer           → Konstruiert Namen: prefix + name + variant_form + suffix
    ├── CoverTemplate          → Rendert Deckblätter mit title/subtitle/iconic_pokemon
    └── LogoRenderer           → Konvertiert [EX], [M] Tags in Bilder
    
Output Layer
    ↓
    PDF Files (/output/{language}/)
    ├── Mega_Evolution_DE.pdf
    ├── Pokemon_EX_Generation_1_DE.pdf
    └── ...
```

### Core Components

**Data Files:** `/data/variants/`
- `meta.json`: Übersicht über alle Variant-Kategorien
- `variants_*.json`: Einzelne Variant-Sammlungen

**Processing:** `/scripts/lib/`
- `variant_pdf_generator.py`: Section-basierter PDF-Generator
- `rendering/card_renderer.py`: Daten-gesteuertes Name-Rendering mit variant_form Support
- `cover_template.py`: Deckblatt-Generator mit Logo-Tag Support

**Output:** `/output/{language}/`
- Separates PDF pro Variant-Kategorie und Sprache

---

## Rendering Logic

### Section Processing (Data-Driven)

```python
for section in sections.values():  # JSON-Reihenfolge garantiert (JSON 7.3+)
    # 1. Deckblatt aus Section-Metadaten rendern
    render_cover(
        title=section['title'][language],
        subtitle=section['subtitle'][language],
        color=section['color_hex'],
        iconic_pokemon=section['iconic_pokemon']
    )
    
    # 2. Kartenseiten aus Pokémon-Array rendern
    for page in paginate(section['pokemon']):
        for pokemon in page:
            name = construct_variant_name(
                pokemon, 
                section['prefix'], 
                section['suffix']
            )
            render_card(pokemon, name)
```

### Name Construction (Fully Data-Driven)

```python
def construct_variant_name(pokemon, section_prefix, section_suffix):
    # 1. Get base name
    name = pokemon['name'][language]
    
    # 2. Override-Logik: Pokémon > Section
    prefix = pokemon.get('prefix', section_prefix)
    suffix = pokemon.get('suffix', section_suffix)
    
    # 3. Add prefix
    if prefix:
        name = f"{prefix} {name}"
    
    # 4. Handle variant_form
    variant_form = pokemon.get('variant_form')
    if variant_form == 'delta':
        # Delta Species: δ an suffix anhängen
        suffix = f"{suffix} δ"
    elif variant_form in ['x', 'y']:
        # Mega X/Y: Form nach Name einfügen
        name = f"{name} {variant_form.upper()}"
    
    # 5. Add suffix
    if suffix:
        name = f"{name} {suffix}"
    
    return name
```

**Beispiele:**
- Input: `{"name": {"de": "Glurak"}, "variant_form": "x"}`, Section: `prefix="Mega", suffix="ex"`
  - Output: **"Mega Glurak X ex"**
- Input: `{"name": {"de": "Dragoran"}, "variant_form": "delta"}`, Section: `prefix="", suffix="ex"`
  - Output: **"Dragoran ex δ"**
- Input: `{"name": {"de": "Krawumms"}, "prefix": "Imakuni?'s"}`, Section: `prefix="", suffix="ex"`
  - Output: **"Imakuni?'s Krawumms ex"**

### Logo-Tag Support

**Logo-Tags werden automatisch in Bilder konvertiert:**

- **In prefix/suffix:** `[EX]`, `[M]`, `[EX_NEW]`, `[EX_TERA]` auf Karten
- **In title/subtitle:** Logo-Tags auf Deckblättern und Separator-Pages

**Beispiel:**
```json
"subtitle": {"de": "[EX_NEW] Serie (ab Karmesin & Purpur"}
```
→ Wird gerendert als: `[echtes EXLogoNew-Bild] Serie (ab Karmesin & Purpur)`

**Keine Sonderlocken:** Der Renderer benötigt keine Typ-Checks oder Speziallogik. Alles ist datengesteuert.

---

## Multilingual Support
#{pokedex_number}_{VARIANT_TYPE}[_{FORM_SUFFIX}]

Examples:
#003_MEGA           → Mega Venusaur (single form)
#006_MEGA_X         → Mega Charizard X (multi-form)
#006_MEGA_Y         → Mega Charizard Y (multi-form)
#025_ALOLA          → Alolan Pikachu (single form)
#104_PALDEA_WATER   → Paldean Tauros (Water form)
#201_UNOWN_?        → Unown (Question Mark)
#741_ORICORIO_BAILE → Oricorio (Baile Style)
```

---

## PDF Generation System

### Entry Point: `generate_pdf.py`

**Location:** `/scripts/generate_pdf.py`

**CLI Commands:**

```bash
# Generate single variant for specific language
python scripts/generate_pdf.py --type variant --variant mega --language de

# Generate all variants for a language
python scripts/generate_pdf.py --type variant --variant all --language en

# Generate all languages for a variant
python scripts/generate_pdf.py --type variant --variant mega --language all

# Generate all variants in all languages
python scripts/generate_pdf.py --type variant --variant all --language all

# High-resolution output
python scripts/generate_pdf.py --type variant --variant mega --language de --high-res

# With parallel processing
python scripts/generate_pdf.py --type variant --variant mega --language de --parallel

# List available variants
python scripts/generate_pdf.py --type variant --list
```

### Processing Classes

#### VariantPDFGenerator

**Location:** `/scripts/lib/variant_pdf_generator.py`

Core class for generating variant PDFs. Responsible for:
- Loading variant data from JSON
- Organizing Pokémon by variant category
- Creating multi-page PDFs with cover page
- Delegating to CardTemplate for card rendering

**Key Methods:**
```python
__init__(variant_data, language, output_file, image_cache)
generate()                          # Main method
_create_cover_page()               # Generate cover page
_add_pokemon_pages()               # Generate card pages
_load_translations()               # Load i18n strings
_format_translation(key, **kwargs) # Apply translations
```

**Color Scheme (VARIANT_COLORS):**
```python
{
    'mega_evolution': '#FFD700',      # Gold
    'gigantamax': '#C5283F',          # Red
    'regional_alola': '#FDB927',      # Yellow
    'regional_galar': '#0071BA',      # Blue
    'regional_hisui': '#9D3F1D',      # Brown
    'regional_paldea': '#D3337F',     # Pink
    'primal_terastal': '#7B61FF',     # Purple
    'patterns_unique': '#9D7A4C',     # Orange
    'fusion_special': '#6F6F6F',      # Gray
}
```

#### CardTemplate

**Location:** `/scripts/lib/card_template.py`

Renders individual Pokémon cards with:
- Pokémon image (with transparent background handling)
- Pokémon name in selected language
- English name as subtitle (small, 4pt)
- Type icons and colors
- Professional styling with generation-consistent design

#### CoverTemplate

**Location:** `/scripts/lib/cover_template.py`

Generates variant cover pages with:
- Variant name and icon
- Variant-specific color coding
- Pokémon count and forms count
- Language-specific content
- Professional layout matching generation binders

### Output Structure

```
/output/{language}/variants/
├── variant_mega_de.pdf
├── variant_mega_en.pdf
├── variant_mega_fr.pdf
├── variant_mega_es.pdf
├── variant_mega_it.pdf
├── variant_mega_ja.pdf
├── variant_mega_ko.pdf
├── variant_mega_zh_hans.pdf
└── variant_mega_zh_hant.pdf
```

**Naming Convention:** `variant_{short_code}_{language}.pdf`

---

## Image Sourcing Strategy

**Source:** `/data/variants/IMAGES.md`

Three-tier approach:

### Tier 1: PokeAPI Official Artwork (Primary)
- **Endpoint:** `/pokemon/{form_id}`
- **URL Format:** `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{form_id}.png`
- **Advantages:**
  - Official, consistent quality
  - Reliable availability
  - Transparent backgrounds
  - Large resolution (600x600+)
- **Method:** Direct URL in JSON data

### Tier 2: Bulbapedia Scraping (Fallback)
- **Source:** `https://bulbapedia.bulbagarden.net/wiki/{pokemon}_(Pokémon)`
- **Method:** Regex-based image extraction
- **Optimization:** Remove `/thumb/` from URLs for full resolution
- **Advantages:**
  - Covers edge cases not in PokeAPI
  - Community-maintained and reliable
  - No WAF (Web Application Firewall) blocking
- **Implementation:** In `fetch_forms.py` or dedicated scrapers

### Tier 3: Manual Mapping (Last Resort)
- **Use Case:** Extremely rare forms without data source
- **Implementation:** Hardcoded mapping in JSON

---

## Multilingual Support

**Languages:** 9 languages supported
- German (de)
- English (en)
- French (fr)
- Spanish (es)
- Italian (it)
- Japanese (ja)
- Korean (ko)
- Simplified Chinese (zh_hans)
- Traditional Chinese (zh_hant)

**Data Structure:** All names stored in nested objects:
```json
"name": {
  "de": "Glurak",
  "en": "Charizard",
  "fr": "Dracaufeu",
  // ... other languages
}
```

**Font System:** `/scripts/lib/fonts.py`

Handles CJK (Chinese, Japanese, Korean) text rendering:
- Uses TrueType font collection for proper character support
- Automatic font switching based on character type
- Registered fonts: Songti, Dejavu, Calibri

**i18n Location:** `/i18n/translations.json`

Contains UI strings for variant categories, cover pages, etc.

---

## Adding a New Variant Category

### Step-by-Step Implementation

#### 1. Research & Data Collection

1. Identify all Pokémon in the variant category
2. Gather all 9 language names
3. Determine image sources (PokeAPI form IDs or alternative URLs)
4. Define section color, prefix, and suffix

#### 2. Create Variant JSON File

**File:** `/data/variants/variants_{type}.json`

Template:
```json
{
  "type": "variant",
  "name": "Display Name",
  "sections": {
    "normal": {
      "section_id": "normal",
      "color_hex": "#HEX_COLOR",
      "prefix": "Prefix Text",
      "suffix": "ex",
      "title": {
        "de": "Deutscher Titel",
        "en": "English Title",
        // ... all 9 languages
      },
      "subtitle": {
        "de": "Untertitel",
        "en": "Subtitle",
        // ... all 9 languages
      },
      "iconic_pokemon": [1, 25, 150],
      "pokemon": []
    }
  }
}
```

**Pokemon Entry Template:**
```json
{
  "id": 25,
  "name": {
    "de": "Pikachu",
    "en": "Pikachu",
    "fr": "Pikachu",
    "es": "Pikachu",
    "it": "Pikachu",
    "ja": "ピカチュウ",
    "ko": "피카츄",
    "zh_hans": "皮卡丘",
    "zh_hant": "皮卡丘"
  },
  "types": ["Electric"],
  "image_url": "https://raw.githubusercontent.com/.../25.png"
}
```

**Optional Fields:**
- `variant_form`: "delta", "x", "y" for special rendering
- `prefix`, `suffix`: Override section-level values
- `form_id`, `form_code`: Form identifiers

#### 3. Update Metadata File

**File:** `/data/variants/meta.json`

Add entry to `variant_categories` array:
```json
{
  "id": "your_variant_type",
  "order": N,
  "json_file": "variants_your_variant_type.json",
  "pokemon_count": X,
  "forms_count": Y,
  "status": "complete|in_progress|planned",
  "notes": "Description..."
}
```

Update `statistics` section with total counts.

#### 4. Add Variant Color Code

**Location:** `/scripts/lib/variant_pdf_generator.py`

Update `VARIANT_COLORS` dictionary:
```python
VARIANT_COLORS = {
    # ... existing entries ...
    'your_variant_type': '#XXXXXX',
}
```

#### 5. Add i18n Strings (if UI-facing)

**Location:** `/i18n/translations.json`

Add variant name translations if needed for UI display.

#### 6. Test Generation

```bash
# Generate for one language to test
python scripts/generate_pdf.py --type variant --variant your_type --language de

# Generate for all languages
python scripts/generate_pdf.py --type variant --variant your_type --language all
```

#### 7. Validation Checklist

- [ ] All Pokémon have 9-language names
- [ ] All image URLs are valid and accessible
- [ ] PDF generates without errors
- [ ] Card layout looks correct
- [ ] Cover page displays correctly
- [ ] Type colors match Pokémon types
- [ ] No missing or corrupted data

---

## Code Organization

```
/scripts/
├── generate_pdf.py                    # Main entry point
├── lib/
│   ├── variant_pdf_generator.py      # Variant PDF generation
│   ├── card_template.py              # Card rendering
│   ├── cover_template.py             # Cover page rendering
│   ├── fonts.py                      # Font management (CJK support)
│   ├── constants.py                  # Page dimensions, margins
│   ├── pdf_generator.py              # Base PDF generation
│   ├── pokeapi_client.py            # API interaction
│   ├── pokemon_processor.py          # Data processing
│   └── form_fetchers/                # Form-specific data fetchers
│
/data/
├── variants/
│   ├── meta.json                     # Variant metadata
│   ├── variants_mega.json            # Mega Evolution data
│   ├── README.md                     # Data structure docs
│   └── IMAGES.md                     # Image sourcing docs
│
/output/
├── de/variants/                      # German PDFs
├── en/variants/                      # English PDFs
└── ... (7 more languages)
```

---

## Testing Strategy

### Data Validation

1. **JSON Schema Validation:**
   - All Pokémon have required fields
   - All image URLs are properly formatted
   - Type arrays contain valid types

2. **Data Completeness:**
   - All Pokémon have names in all 9 languages
   - No duplicate IDs
   - Correct pokemon counts match actual data

### PDF Generation

1. **Rendering Tests:**
   - PDFs generate without errors
   - All pages render correctly
   - Images display properly

2. **Multilingual Tests:**
   - Text renders in correct language
   - CJK characters display properly
   - English subtitles appear on non-English PDFs

3. **Visual Tests:**
   - Cover page layout matches variant type
   - Card layout is 3x3 with proper spacing
   - Cutting guides are present and accurate

### CLI Interface

1. **Command Tests:**
   ```bash
   pytest tests/test_variant_cli.py
   ```

---

## Performance Considerations

### Image Caching

- Images are cached during generation
- Cache stored in `/data/pokemon_images_cache/`
- Reduces download time for subsequent runs

### Parallel Processing

Use `--parallel` flag for multi-language generation:

```bash
python scripts/generate_pdf.py --type variant --variant all --language all --parallel
```

Processing time estimate:
- Single variant, single language: ~30-60 seconds
- All 9 variants, all 9 languages: ~15-20 minutes (parallel)

---

## Known Limitations & Future Improvements

### Current Limitations

1. **Variant Categories:** Only 1 of 9 planned categories implemented (Mega Evolution)
2. **Gender Variants:** Not yet included in any variant category
3. **Shiny Forms:** Not included (potential future category)

### Future Extension Points

When implementing additional variant categories (Gigantamax, Regional Forms, etc.):

1. **Follow JSON Schema:** Maintain consistency with existing `variants_mega.json` structure
2. **Naming Convention:** Use established ID format for new variants
3. **Color Scheme:** Add to `VARIANT_COLORS` in `variant_pdf_generator.py`
4. **Testing:** Validate all data before PDF generation
5. **Documentation:** Update this file with new variant specifics

---

## Reference: Mega Evolution Implementation

As the first implemented variant category, Mega Evolution serves as the reference implementation.

**Statistics:**
- **Pokémon:** 76 species
- **Forms:** 79 unique forms (includes X/Y variants)
- **Naming:** `#NNN_MEGA` or `#NNN_MEGA_X`/`#NNN_MEGA_Y`
- **Data File:** `/data/variants/variants_mega.json`
- **PDFs:** 9 languages × 1 variant = 9 PDF files

**Key Features:**
- Multi-form support (Charizard, Mewtwo, etc.)
- Consistent type support
- Full multilingual naming
- Professional card layout

Use this as a template when implementing new variant categories.

---

## Related Documentation

- [VARIANTS_FEATURE_SUMMARY.md](VARIANTS_FEATURE_SUMMARY.md) - Feature overview
- [VARIANTS_TECHNICAL_SPEC.md](VARIANTS_TECHNICAL_SPEC.md) - Detailed specifications
- [/data/variants/README.md](/data/variants/README.md) - Data format details
- [/data/variants/IMAGES.md](/data/variants/IMAGES.md) - Image sourcing details
- [ARCHITECTURE.md](ARCHITECTURE.md) - Overall project architecture

