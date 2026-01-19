# Pokémon Variants - Technical Specification

**Version:** 2.0  
**Status:** Phase 1 Implementation Complete (Mega Evolution)  
**Date:** January 19, 2026

---

## Overview

This document describes the technical implementation of Pokémon Variants feature, starting with Mega Evolution (Phase 1).

**Implemented:** Mega Evolution (76 Pokémon, 79 forms)  
**Planned:** Gigantamax, Regional Variants, Primal Reversion, Pattern Variations, Fusion forms

---

## 1. Implementation Architecture

### 1.1 Data Flow

```
PokeAPI (Mega-Form-IDs)
         ↓
    [Primary Strategy]
         ↓
   Official Artwork ✓

   Bulbapedia (Fallback)
         ↓
    [Secondary Strategy]
         ↓
   Community Artwork ✓
   (with URL optimization)
```

### 1.2 File Structure

```
/data/variants/
├── meta.json                    # Metadata & statistics
├── variants_mega.json           # ✅ Implemented (76 Pokémon)
├── variants_gigantamax.json     # 🔄 Planned
├── variants_regional_*.json     # 🔄 Planned
├── variants_primal_terastal.json # 🔄 Planned
├── variants_patterns_unique.json # 🔄 Planned
├── variants_fusion_special.json  # 🔄 Planned
├── IMAGES.md                    # Image sourcing documentation
└── README.md                    # Data overview
```

### 1.3 Image Sourcing Strategy

#### Strategy 1: PokeAPI Varieties (Primary)
- Query: `/pokemon-species/{id}`
- Extract: Mega-Form-IDs from variety URLs
- Get: Official artwork from PokeAPI
- Advantage: Official, reliable, consistent

#### Strategy 2: Bulbapedia Scraping (Fallback)
- Source: `https://bulbapedia.bulbagarden.net/wiki/{pokemon}_(Pokémon)`
- Scraping: Regex pattern for `<img alt="Mega X|Y">`
- Optimization: Remove `/thumb/` paths for full resolution
- Advantage: No WAF blocking, community-maintained, form-specific

#### Strategy 3: Manual Mapping (Last Resort)
- Limited hardcoded mappings for special cases
- Used only when both above strategies unavailable

---

## 1. Data Model

### 1.1 JSON Schema for Variants

```json
{
  "variant_id": "mega_001",
  "variant_type": "mega_evolution",
  "variant_category": "transformations",
  "variant_name": "Mega Evolution",
  "variant_name_de": "Mega-Entwicklung",
  "variant_name_es": "Megaevolución",
  "variant_name_fr": "Méga-Évolution",
  "variant_name_it": "Megaevoluzione",
  "variant_name_ja": "メガシンカ",
  "variant_name_ko": "메가진화",
  "variant_name_zh_hans": "超级进化",
  "variant_name_zh_hant": "超級進化",
  "short_code": "mega",
  "icon": "⚡",
  "color_hex": "#FF9900",
  "introduction_generation": 6,
  "introduction_games": ["X", "Y"],
  "description": "Allows Pokémon to temporarily transform during battle, gaining increased stats and sometimes changing type.",
  "description_de": "Ermöglicht es Pokémon, sich während des Kampfes vorübergehend zu verwandeln und dabei verstärkte Statuswerte zu erhalten.",
  "pokemon_count": 96,
  "pokemon": [
    {
      "id": "mega_003",
      "pokedex_number": 3,
      "base_pokemon_name": "Venusaur",
      "base_pokemon_name_de": "Bisakunodon",
      "variant_name": "Mega Venusaur",
      "variant_name_de": "Mega-Bisakunodon",
      "types": ["Grass", "Poison"],
      "types_de": ["Pflanze", "Gift"],
      "description": "Mega Venusaur, the Seed Pokémon...",
      "height": "2.4m",
      "weight": "155.5kg",
      "abilities": ["Thick Fat"],
      "base_stats": {
        "hp": 80,
        "attack": 82,
        "defense": 100,
        "sp_atk": 122,
        "sp_def": 120,
        "speed": 80
      },
      "official_id": null,
      "pokeapi_id": null,
      "image_url": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/3.png",
      "image_url_variant": "https://example.com/mega_venusaur.png",
      "order_in_variant": 1,
      "game_availability": ["X", "Y", "ORAS", "Sun", "Moon", "USUM", "Sword", "Shield", "Legends Z-A"],
      "custom_notes": ""
    }
  ]
}
```

### 1.2 Variant Types (9 Main Categories)

```python
VARIANT_TYPES = {
    "mega_evolution": {
        "order": 1,
        "icon": "⚡",
        "color": "#FF9900",
        "count_pokemon": 87,
        "count_forms": 96,
        "removable": False
    },
    "gigantamax": {
        "order": 2,
        "icon": "📏",
        "color": "#FF1493",
        "count_pokemon": 32,
        "count_forms": 32,
        "removable": False
    },
    "regional_alola": {
        "order": 3,
        "icon": "🌴",
        "color": "#FF6B35",
        "count_pokemon": 18,
        "count_forms": 18,
        "removable": False
    },
    "regional_galar": {
        "order": 4,
        "icon": "⚔️",
        "color": "#4A90E2",
        "count_pokemon": 16,
        "count_forms": 16,
        "removable": False
    },
    "regional_hisui": {
        "order": 5,
        "icon": "🎋",
        "color": "#8B4513",
        "count_pokemon": 15,
        "count_forms": 15,
        "removable": False
    },
    "regional_paldea": {
        "order": 6,
        "icon": "🎨",
        "color": "#DA70D6",
        "count_pokemon": 5,
        "count_forms": 8,
        "removable": False
    },
    "primal_terastal": {
        "order": 7,
        "icon": "💎",
        "color": "#00CED1",
        "count_pokemon": 4,
        "count_forms": 6,
        "removable": False
    },
    "patterns_unique": {
        "order": 8,
        "icon": "🎭",
        "color": "#9370DB",
        "count_pokemon": 30,
        "count_forms": 48,
        "removable": False
    },
    "fusion_special": {
        "order": 9,
        "icon": "🔗",
        "color": "#FF4500",
        "count_pokemon": 3,
        "count_forms": 6,
        "removable": False
    }
}
```

---

## 2. File Structure

### 2.1 Folder Structure

```
/data
  /variants/
    meta.json              # Metadata for all variants
    variants_mega.json
    variants_gigantamax.json
    variants_regional_alola.json
    variants_regional_galar.json
    variants_regional_hisui.json
    variants_regional_paldea.json
    variants_primal_terastal.json
    variants_patterns_unique.json
    variants_fusion_special.json
    README.md
    
/output
  /{language}
    /variants
      variant_mega_de.pdf
      variant_mega_en.pdf
      variant_gigantamax_de.pdf
      variant_gigantamax_en.pdf
      ...
      (9 variants × 9 languages = 81 total PDFs)

/i18n
  variant_strings.json    # Translations for variant UI
```

### 2.2 Meta File (`variants/meta.json`)

```json
{
  "version": "1.0",
  "last_updated": "2026-01-19",
  "variant_categories": [
    {
      "id": "mega_evolution",
      "order": 1,
      "json_file": "variants_mega.json",
      "pokemon_count": 87,
      "forms_count": 96,
      "status": "complete",
      "notes": "87 Pokémon species, 96 unique Mega forms (X/Y/Z variants)"
    },
    // ... more categories
  ],
  "statistics": {
    "total_pokemon": 240,
    "total_forms": 195,
    "total_categories": 9
  }
}
```

---

## 3. API Integration (PokeAPI)

### 3.1 Available PokeAPI Endpoints

```
/pokemon-form/          # Form information
/pokemon/{id}           # Base Pokémon info
/item/{id}              # Items (Mega Stone, etc.)
/pokemon-species/{id}   # Species info
```

### 3.2 Data Fetching Strategy

**Problem:** PokeAPI has limited information about variants

**Solution:** Hybrid approach
- Use PokeAPI for available base data
- Bulbapedia scraping/database for variant details
- Fallback to manual definitions for missing data

### 3.3 Data Validation

```python
def validate_variant_pokemon(pokemon_data: dict) -> bool:
    """Validates Pokémon variant data"""
    required_fields = [
        'id', 'pokedex_number', 'base_pokemon_name', 
        'variant_name', 'types', 'image_url', 
        'abilities', 'base_stats'
    ]
    return all(field in pokemon_data for field in required_fields)
```

---

## 4. CLI Interface

### 4.1 Extended `generate_pdf.py` Commands

```bash
# Generate single variant
python scripts/generate_pdf.py --type variant --variant mega --language de

# All variants for one language
python scripts/generate_pdf.py --type variant --variant all --language de

# With options
python scripts/generate_pdf.py \
  --type variant \
  --variant gigantamax \
  --language en \
  --output-dir ./custom_output \
  --high-res

# List all available variants
python scripts/generate_pdf.py --type variant --list
```

### 4.2 Config Structure (`config.yaml` Update)

```yaml
variants:
  enabled: true
  categories:
    - mega_evolution
    - gigantamax
    - regional_alola
    - regional_galar
    - regional_hisui
    - regional_paldea
    - primal_terastal
    - patterns_unique
    - fusion_special
  
  pdf_settings:
    cover_template: "variant_cover.html"
    page_template: "variant_page.html"
    cards_per_page: 6
    include_pokedex_number: true
    include_stats: true
    high_res: false
  
  data_sources:
    - pokeapi
    - manual_definitions
```

---

## 5. PDF Generation

### 5.1 Cover Page Template (`variant_cover.html`)

```html
<div class="cover variant-cover">
  <div class="variant-header">
    <span class="variant-icon">{{ variant.icon }}</span>
    <h1>{{ variant.variant_name }}</h1>
  </div>
  
  <div class="variant-meta">
    <p class="introduction">
      Introduced in Generation {{ variant.introduction_generation }}
      ({{ variant.introduction_games|join(', ') }})
    </p>
    <p class="count">
      {{ variant.pokemon_count }} Pokémon  |  {{ variant.count_forms }} Forms
    </p>
  </div>
  
  <div class="variant-description">
    {{ variant.description }}
  </div>
  
  <div class="project-footer">
    {{ "Print borderless. Follow cutting lines." }}
  </div>
</div>
```

### 5.2 Card Page Template (`variant_page.html`)

```html
<div class="pokemon-card variant-card">
  <div class="card-header">
    <span class="variant-badge">{{ pokemon.variant_type }}</span>
    <span class="pokemon-number">#{{ pokemon.pokedex_number }}</span>
  </div>
  
  <div class="card-image">
    <img src="{{ pokemon.image_url_variant }}" alt="{{ pokemon.variant_name }}"/>
  </div>
  
  <div class="card-info">
    <h2>{{ pokemon.variant_name }}</h2>
    <p class="base-pokemon">Base: {{ pokemon.base_pokemon_name }}</p>
    
    <div class="types">
      {% for type in pokemon.types %}
        <span class="type-badge type-{{ type|lower }}">{{ type }}</span>
      {% endfor %}
    </div>
    
    {% if pokemon.base_stats %}
    <div class="stats">
      <div class="stat-bar">
        <label>HP</label>
        <div class="bar"><div style="width: {{ pokemon.base_stats.hp / 2.5 }}%"></div></div>
        <span>{{ pokemon.base_stats.hp }}</span>
      </div>
      <!-- more stats -->
    </div>
    {% endif %}
  </div>
</div>
```

---

## 6. Numbering Schema

### 6.1 ID Generation Format

```
#{pokemon_id}_{VARIANT_TYPE}[_{FORM_SUFFIX}]

Rules:
1. Single form variant: No suffix
   Example: #003_MEGA (Mega Venusaur)

2. Multiple forms: Add suffix for non-default forms
   Example: #006_MEGA_X, #006_MEGA_Y (Mega Charizard X/Y)
   
3. Default form ignored (already in main Pokédex)
   Example: Oricorio Baile (default) is not included
   Only: #741_ORICORIO_POM_POM, #741_ORICORIO_SENSU, etc.

4. Special characters allowed in suffixes
   Example: #201_UNOWN_? (Question Mark), #201_UNOWN_! (Exclamation)
   Fallback: #201_UNOWN_QUESTION if "?" causes issues

5. Gender differences: Female forms only (visually distinct)
   Example: #012_FEMALE (Butterfree), #025_FEMALE (Pikachu)
   Note: Male forms already in main Pokédex, female only if distinct

6. Shiny forms get ID if included
   Example: #001_SHINY (Shiny Bulbasaur)
```

### 6.2 ID Generation Code

```python
def generate_variant_id(pokemon_id: int, variant_type: str, form_suffix: str = None) -> str:
    """
    Generates variant IDs
    
    Examples:
    - generate_variant_id(3, "MEGA") → "#003_MEGA"
    - generate_variant_id(6, "MEGA", "X") → "#006_MEGA_X"
    - generate_variant_id(201, "UNOWN", "?") → "#201_UNOWN_?"
    - generate_variant_id(12, "FEMALE") → "#012_FEMALE"
    - generate_variant_id(104, "PALDEA", "WATER") → "#104_PALDEA_WATER"
    """
    base_id = str(pokemon_id).zfill(3)
    
    if form_suffix:
        return f"#{base_id}_{variant_type}_{form_suffix}"
    return f"#{base_id}_{variant_type}"
```

---

## 7. Internationalization

### 7.1 New Translation Keys

```json
{
  "variant.mega_evolution": "Mega Evolution",
  "variant.mega_evolution_de": "Mega-Entwicklung",
  "variant.gigantamax": "Gigantamax",
  "variant.gigantamax_de": "Gigadynamax",
  "variant.regional_alola": "Alolan Form",
  "variant.regional_alola_de": "Alola-Form",
  // ... more keys
  
  "ui.select_variant": "Select Variant",
  "ui.select_variant_de": "Variante auswählen",
  "ui.generate_variant": "Generate Variant PDF",
  "ui.generate_variant_de": "Varianten-PDF generieren"
}
```

---

## 8. Testing Strategy

### 8.1 Unit Tests

```python
def test_variant_id_generation():
    assert generate_variant_id("mega", 3) == "mega_003"
    assert generate_variant_id("mega", 6, 1) == "mega_006_a"
    assert generate_variant_id("mega", 6, 2) == "mega_006_b"

def test_variant_validation():
    valid_variant = {...}  # complete data
    assert validate_variant_pokemon(valid_variant) == True
    
    invalid_variant = {...}  # missing fields
    assert validate_variant_pokemon(invalid_variant) == False

def test_variant_loading():
    variants = load_variants("mega")
    assert len(variants['pokemon']) == 96
    assert variants['pokemon'][0]['id'].startswith('mega_')
```

### 8.2 Integration Tests

- [ ] PDF generation for all variants
- [ ] Validate multilingual output
- [ ] Validate image URLs (no 404)
- [ ] Validate stats calculation

---

## 9. Performance Considerations

### 9.1 Caching Strategy

```python
# Cache variant data to speed up multiple generations
VARIANT_CACHE = {}

def get_variants(variant_type: str, force_reload: bool = False) -> dict:
    if variant_type in VARIANT_CACHE and not force_reload:
        return VARIANT_CACHE[variant_type]
    
    variants = load_variants_from_json(variant_type)
    VARIANT_CACHE[variant_type] = variants
    return variants
```

### 9.2 Batch Processing

```bash
# Generate all 9 variants in parallel
python scripts/generate_pdf.py --type variant --variant all --parallel
```

---

## 10. Implementation Order (MVP)

### Phase 1: Core Infrastructure (Week 1)
- [ ] Define variant JSON schemas
- [ ] Build metadata structure
- [ ] Extend CLI arguments
- [ ] Update configuration

### Phase 2: Mega Evolution MVP (Week 2)
- [ ] Fetch/define Mega Evolution data
- [ ] Create PDF templates
- [ ] Test generation (all languages)
- [ ] Validate cover & pages

### Phase 3: Gigantamax (Week 3)
- [ ] Gigantamax data
- [ ] Analogous process to Mega

### Phase 4: Regional Forms (Week 4)
- [ ] Alola, Galar, Hisui, Paldea in parallel
- [ ] Unified structure

### Phase 5: Remaining Variants (Week 5)
- [ ] Primal, Terastal, Patterns, Fusion
- [ ] Full QA & deployment

---

## 11. Known Challenges

1. **Missing official numbers:** Creative numbering required
2. **Image availability:** Not all variant images available
3. **Data consistency:** Multiple unofficial sources needed
4. **Performance:** Generating 200+ PDFs can take time
5. **Multilingual support:** Translations for all variant names needed

---

## 12. References

- **Project Architecture:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Current PDF Generation:** [scripts/lib/pdf_generator.py](scripts/lib/pdf_generator.py)
- **CLI Structure:** [scripts/generate_pdf.py](scripts/generate_pdf.py)

