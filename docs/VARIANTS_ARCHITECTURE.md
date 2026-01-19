# Pokémon Variants - Architecture & Implementation Guide

**Current Status:** Mega Evolution (Phase 1) ✅  
**Last Updated:** January 19, 2026  
**Purpose:** Document the implementation and architecture for maintaining and extending variants

---

## Overview

The Variants feature enables generation of separate collection binders for Pokémon variants, analogous to generation-based binders. The architecture is designed to support multiple variant categories through a unified framework.

**Currently Implemented:**
- **Mega Evolution:** 76 Pokémon with 79 unique forms
- Full 9-language support
- Professional PDF generation with cutting guides

---

## Architecture

### High-Level Data Flow

```
Data Layer (JSON)
    ↓
    Variant JSON Files (/data/variants/)
    ├── meta.json
    └── variants_mega.json
    
Processing Layer
    ↓
    generate_pdf.py --type variant --variant mega --language de
    ├── VariantPDFGenerator
    ├── CardTemplate
    └── CoverTemplate
    
Output Layer
    ↓
    PDF Files (/output/{language}/variants/)
    ├── variant_mega_de.pdf
    ├── variant_mega_en.pdf
    └── ...
```

### Core Components

#### 1. Data Files Structure

**Location:** `/data/variants/`

```
variants/
├── meta.json
│   └── Metadata about all variant categories
│       - Variant counts and statistics
│       - Status information
│       - File references
│
├── variants_mega.json
│   └── Complete data for Mega Evolution variant
│       - 76 Pokémon species
│       - 79 unique forms (X/Y/Z variants)
│       - Full multilingual support (9 languages)
│       - Image URLs from PokeAPI
│
├── README.md
│   └── Overview of variant data structure
│
└── IMAGES.md
    └── Documentation on image sourcing strategies
```

#### 2. Data Schema for Variant JSON Files

**File Structure:** `variants_{type}.json`

```json
{
  "variant_type": "mega_evolution",
  "variant_name": "Mega Evolution",
  "variant_name_de": "Mega-Entwicklung",
  "variant_name_fr": "Méga-Évolution",
  // ... other languages
  "short_code": "MEGA",
  "icon": "⚡",
  "color_hex": "#FFD700",
  "pokemon_count": 76,
  "forms_count": 79,
  "pokemon": [
    {
      "id": "#003_MEGA",
      "mega_form_id": 10033,
      "name_en": "Venusaur",
      "name_de": "Bisaflor",
      // ... other languages
      "variant_prefix": "Mega",
      "variant_form": "",
      "types": ["Grass", "Poison"],
      "image_url": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/10033.png"
    },
    {
      "id": "#006_MEGA_X",
      "mega_form_id": 10034,
      "name_en": "Charizard",
      "name_de": "Glurak",
      // ... other languages
      "variant_prefix": "Mega",
      "variant_form": "x",
      "types": ["Fire", "Flying"],
      "image_url": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/10034.png"
    }
  ]
}
```

**Key Fields:**
- `id`: Unique identifier format: `#{pokedex_number}_{VARIANT_TYPE}[_{FORM_SUFFIX}]`
- `mega_form_id`: PokeAPI form ID (for image URLs)
- Names in 9 languages: `name_en`, `name_de`, `name_fr`, `name_es`, `name_it`, `name_ja`, `name_ko`, `name_zh_hans`, `name_zh_hant`
- `variant_prefix`: Prefix for display (e.g., "Mega", "Alolan")
- `variant_form`: Optional suffix for multi-form variants (x, y, water, fire)
- `types`: Pokémon type array
- `image_url`: Full URL to official artwork from PokeAPI

#### 3. Naming Schema

The ID system follows this pattern:

```
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
- German (de): `name_de`
- English (en): `name_en`
- French (fr): `name_fr`
- Spanish (es): `name_es`
- Italian (it): `name_it`
- Japanese (ja): `name_ja`
- Korean (ko): `name_ko`
- Simplified Chinese (zh_hans): `name_zh_hans`
- Traditional Chinese (zh_hant): `name_zh_hant`

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
2. Gather English, German, French, Spanish, Italian, Japanese, Korean, Simplified Chinese, Traditional Chinese names
3. Determine image sources (PokeAPI form IDs or alternative URLs)
4. Define variant icon and color code

#### 2. Create Variant JSON File

**File:** `/data/variants/variants_{type}.json`

Template:
```json
{
  "variant_type": "your_variant_type",
  "variant_name": "English Name",
  "variant_name_de": "Deutscher Name",
  "variant_name_fr": "Nom Français",
  "variant_name_es": "Nombre Español",
  "variant_name_it": "Nome Italiano",
  "variant_name_ja": "日本語名",
  "variant_name_ko": "한국어 이름",
  "variant_name_zh_hans": "简体中文",
  "variant_name_zh_hant": "繁體中文",
  "short_code": "SHORTCODE",
  "icon": "🔣",
  "color_hex": "#XXXXXX",
  "pokemon_count": N,
  "forms_count": N,
  "pokemon": [
    {
      "id": "#NNN_TYPE[_FORM]",
      "pokedex_number": NNN,
      "name_en": "English Name",
      "name_de": "Deutscher Name",
      "name_fr": "Nom Français",
      "name_es": "Nombre Español",
      "name_it": "Nome Italiano",
      "name_ja": "日本語名",
      "name_ko": "한국어 이름",
      "name_zh_hans": "简体中文",
      "name_zh_hant": "繁體中文",
      "variant_prefix": "Variant Prefix",
      "variant_form": "",
      "types": ["Type1", "Type2"],
      "image_url": "https://..."
    }
  ]
}
```

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

