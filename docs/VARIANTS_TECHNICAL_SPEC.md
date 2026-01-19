# Pokémon Variants - Technical Specification

**Version:** 1.0  
**Status:** Mega Evolution (Phase 1) - Production  
**Date:** January 19, 2026  
**Scope:** Implemented features only

---

## Overview

This document specifies the **implemented** technical details of the Pokémon Variants feature.

**Current Implementation:**
- Mega Evolution (76 Pokémon, 79 forms) - Complete

For step-by-step guide to implementing new variants, see [VARIANTS_IMPLEMENTATION_GUIDE.md](VARIANTS_IMPLEMENTATION_GUIDE.md).  
For complete architecture, see [VARIANTS_ARCHITECTURE.md](VARIANTS_ARCHITECTURE.md).

---

## 1. Data Model: Mega Evolution

### 1.1 JSON Schema

**File:** `/data/variants/variants_mega.json`

```json
{
  "variant_type": "mega_evolution",
  "variant_name": "Mega Evolution",
  "variant_name_de": "Mega-Entwicklung",
  "variant_name_fr": "Méga-Évolution",
  "variant_name_es": "Megaevolución",
  "variant_name_it": "Megaevoluzione",
  "variant_name_ja": "メガシンカ",
  "variant_name_ko": "메가진화",
  "variant_name_zh_hans": "超级进化",
  "variant_name_zh_hant": "超級進化",
  "short_code": "MEGA",
  "icon": "⚡",
  "color_hex": "#FFD700",
  "pokemon_count": 76,
  "forms_count": 79,
  "pokemon": [
    {
      "id": "#003_MEGA",
      "pokedex_number": 3,
      "mega_form_id": 10033,
      "name_en": "Venusaur",
      "name_de": "Bisaflor",
      "name_fr": "Florizarre",
      "name_es": "Venusaur",
      "name_it": "Venusaur",
      "name_ja": "フシギバナ",
      "name_ko": "이상해꽃",
      "name_zh_hans": "妙蛙花",
      "name_zh_hant": "妙蛙花",
      "variant_prefix": "Mega",
      "variant_form": "",
      "types": ["Grass", "Poison"],
      "image_url": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/10033.png"
    },
    {
      "id": "#006_MEGA_X",
      "pokedex_number": 6,
      "mega_form_id": 10034,
      "name_en": "Charizard",
      "name_de": "Glurak",
      "name_fr": "Dracaufeu",
      "name_es": "Charizard",
      "name_it": "Charizard",
      "name_ja": "リザードン",
      "name_ko": "리자몽",
      "name_zh_hans": "喷火龙",
      "name_zh_hant": "噴火龍",
      "variant_prefix": "Mega",
      "variant_form": "x",
      "types": ["Fire", "Flying"],
      "image_url": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/10034.png"
    }
  ]
}
```

### 1.2 Field Descriptions

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | string | Unique identifier | `#006_MEGA_X` |
| `pokedex_number` | integer | Base Pokémon number | `6` |
| `mega_form_id` | integer | PokeAPI form ID | `10034` |
| `name_*` | string | Pokémon name in 9 languages | `Glurak` (de) |
| `variant_prefix` | string | Display prefix | `Mega` |
| `variant_form` | string | Form suffix (empty or lowercase) | `x`, `y`, or `` |
| `types` | array | Type array | `["Fire", "Flying"]` |
| `image_url` | string | URL to official artwork | `https://...` |

### 1.3 Naming Schema

```
Format: #{pokedex_number}_{VARIANT_TYPE}[_{FORM_SUFFIX}]

Single Form:
  #003_MEGA           → Mega Venusaur

Multiple Forms:
  #006_MEGA_X         → Mega Charizard X
  #006_MEGA_Y         → Mega Charizard Y
  #150_MEGA_X         → Mega Mewtwo X
  #150_MEGA_Y         → Mega Mewtwo Y
```

---

## 2. File Organization

```
/data/variants/
├── meta.json                    # Metadata for all variants
├── variants_mega.json           # Mega Evolution (76 Pokémon)
├── README.md                    # Data format documentation
└── IMAGES.md                    # Image sourcing strategies

/scripts/lib/
├── variant_pdf_generator.py     # Main variant PDF engine
├── card_template.py             # Card rendering
├── cover_template.py            # Cover page rendering
└── fonts.py                     # Font management

/output/{language}/variants/
├── variant_mega_de.pdf
├── variant_mega_en.pdf
├── variant_mega_fr.pdf
├── ... (9 languages total)
```

---

## 3. Metadata File Structure

**File:** `/data/variants/meta.json`

```json
{
  "version": "1.0",
  "last_updated": "2026-01-19",
  "variant_categories": [
    {
      "id": "mega_evolution",
      "order": 1,
      "json_file": "variants_mega.json",
      "pokemon_count": 76,
      "forms_count": 79,
      "status": "complete",
      "notes": "76 Pokémon species, 79 unique Mega forms"
    }
  ],
  "statistics": {
    "total_pokemon": 76,
    "total_forms": 79,
    "total_categories": 1,
    "total_pdfs": 9
  }
}
```

---

## 4. PDF Generation System

### 4.1 Main Entry Point

**File:** `/scripts/generate_pdf.py`

**Relevant Arguments:**
```
--type variant          # PDF type selector
--variant mega          # Specific variant category
--variant all           # All variants
--language de           # Target language
--language all          # All 9 languages
--high-res             # High resolution images
--parallel             # Parallel processing
```

### 4.2 Core Classes

#### VariantPDFGenerator

**Location:** `/scripts/lib/variant_pdf_generator.py`

Handles:
- Loading variant data from JSON
- Organizing Pokémon by variant
- Pagination (3×3 cards per page)
- Multi-page PDF generation

**Key Methods:**
```python
__init__(variant_data, language, output_file, image_cache)
generate()                    # Main generation method
_create_cover_page()         # Generate cover page
_add_pokemon_pages()         # Generate card pages
_format_translation(key)     # Apply translations
```

#### CardTemplate

**Location:** `/scripts/lib/card_template.py`

Renders individual Pokémon cards with:
- Image display
- Name (in target language)
- English subtitle
- Type badges with colors
- Professional styling

#### CoverTemplate

**Location:** `/scripts/lib/cover_template.py`

Generates cover pages with:
- Variant icon and name
- Variant-specific color
- Pokémon/form counts
- Professional layout

### 4.3 Variant Color System

**Location:** `/scripts/lib/variant_pdf_generator.py` (VARIANT_COLORS dict)

```python
VARIANT_COLORS = {
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

---

## 5. Image Sourcing

### 5.1 Primary Source: PokeAPI Official Artwork

Format: `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{form_id}.png`

**Advantages:**
- Official quality
- Transparent backgrounds
- Consistent sizing (600x600+)
- Reliable availability

**Implementation:**
- PokeAPI form ID stored in JSON (`mega_form_id` field)
- Direct URL construction from form ID
- Automatic image caching

### 5.2 Fallback: Bulbapedia Scraping

**Source:** `https://bulbapedia.bulbagarden.net/wiki/{pokemon}_(Pokémon)`

**Method:**
- Regex-based image extraction
- URL optimization: Remove `/thumb/` for full resolution
- Used only if PokeAPI unavailable

**Documentation:** `/data/variants/IMAGES.md`

---

## 6. Multilingual Support

**Supported Languages (9 total):**

| Code | Language | Status |
|------|----------|--------|
| de | German (Deutsch) | ✅ Complete |
| en | English | ✅ Complete |
| fr | French (Français) | ✅ Complete |
| es | Spanish (Español) | ✅ Complete |
| it | Italian (Italiano) | ✅ Complete |
| ja | Japanese (日本語) | ✅ Complete |
| ko | Korean (한국어) | ✅ Complete |
| zh_hans | Simplified Chinese | ✅ Complete |
| zh_hant | Traditional Chinese | ✅ Complete |

**i18n Location:** `/i18n/translations.json`

**Font System:** `/scripts/lib/fonts.py`

Handles:
- CJK character rendering
- Automatic font switching
- TrueType font management

---

## 7. Data Validation

### 7.1 Required Fields Check

All Pokémon must have:
- `id`: Unique identifier
- `pokedex_number`: Valid integer
- 9-language names: `name_en`, `name_de`, `name_fr`, `name_es`, `name_it`, `name_ja`, `name_ko`, `name_zh_hans`, `name_zh_hant`
- `types`: Array with 1-2 valid type names
- `image_url`: Valid URL
- `variant_form`: String (empty or lowercase suffix)

### 7.2 Validation Script

```bash
# Validate JSON syntax
python3 -m json.tool /data/variants/variants_mega.json > /dev/null

# Verify completeness
python3 << 'EOF'
import json
with open('/data/variants/variants_mega.json') as f:
    data = json.load(f)
    
required_fields = [
    'id', 'pokedex_number', 'name_en', 'name_de', 'name_fr', 
    'name_es', 'name_it', 'name_ja', 'name_ko', 
    'name_zh_hans', 'name_zh_hant', 'types', 'image_url'
]

for pokemon in data['pokemon']:
    for field in required_fields:
        assert field in pokemon, f"Missing {field} in {pokemon['id']}"

print(f"✓ {len(data['pokemon'])} Pokémon validated")
EOF
```

---

## 8. CLI Reference

### 8.1 Common Commands

```bash
# Generate single variant in one language
python scripts/generate_pdf.py --type variant --variant mega --language de

# Generate in all languages
python scripts/generate_pdf.py --type variant --variant mega --language all

# High-resolution generation
python scripts/generate_pdf.py --type variant --variant mega --language de --high-res

# Parallel generation (all languages)
python scripts/generate_pdf.py --type variant --variant mega --language all --parallel

# List available variants
python scripts/generate_pdf.py --type variant --list
```

### 8.2 Output Location

```
Generated files stored in:
  output/{language}/variants/variant_{short_code}_{language}.pdf

Examples:
  output/de/variants/variant_mega_de.pdf
  output/en/variants/variant_mega_en.pdf
  output/fr/variants/variant_mega_fr.pdf
  output/ja/variants/variant_mega_ja.pdf
```

---

## 9. Performance Characteristics

### 9.1 Generation Time

- **Single variant, single language:** 30-60 seconds
- **Single variant, all 9 languages:** 5-10 minutes
- **All 9 variants, all languages:** 15-20 minutes (parallel)

### 9.2 File Sizes

- **Per PDF:** 2-5 MB
- **Cached images:** ~26.5 MB for Mega Evolution
- **Total output:** 9 PDFs × ~3 MB = ~27 MB

### 9.3 Optimization

- Image caching reduces download time
- Parallel processing available via `--parallel` flag
- ReportLab efficiently handles PDF generation

---

## 10. Known Limitations

1. **Current Scope:** Only Mega Evolution implemented
2. **Gender Variants:** Not yet included
3. **Shiny Forms:** Not included in any category
4. **Official Form IDs:** Creative numbering for non-PokeAPI forms

---

## 11. Future Extension Points

When implementing additional variant categories:

1. **Create JSON File:** Follow `/data/variants/variants_mega.json` structure
2. **Update meta.json:** Add category entry
3. **Add Color Code:** Insert into VARIANT_COLORS in `variant_pdf_generator.py`
4. **Test Generation:** Single-language test before full deployment
5. **Document:** Reference [VARIANTS_IMPLEMENTATION_GUIDE.md](VARIANTS_IMPLEMENTATION_GUIDE.md)

---

## 12. Testing Checklist

- [ ] JSON validates with `python3 -m json.tool`
- [ ] All Pokémon have 9-language names
- [ ] All image URLs are accessible
- [ ] PDF generates without errors
- [ ] All 9 languages generate successfully
- [ ] Cover page displays correctly
- [ ] Card layout is 3×3
- [ ] No missing or corrupted images
- [ ] Cutting guides are visible

---

## References

- [VARIANTS_ARCHITECTURE.md](VARIANTS_ARCHITECTURE.md) - Overall design
- [VARIANTS_IMPLEMENTATION_GUIDE.md](VARIANTS_IMPLEMENTATION_GUIDE.md) - Adding new variants
- [VARIANTS_FEATURE_SUMMARY.md](VARIANTS_FEATURE_SUMMARY.md) - Feature overview
- [/data/variants/README.md](/data/variants/README.md) - Data format details
- [/data/variants/IMAGES.md](/data/variants/IMAGES.md) - Image sourcing

