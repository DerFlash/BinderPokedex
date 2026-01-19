# Pokémon Variants - Implementation Guide for New Categories

**Purpose:** Step-by-step guide for implementing new variant categories  
**Audience:** Backend developers  
**Prerequisite:** Read [VARIANTS_ARCHITECTURE.md](VARIANTS_ARCHITECTURE.md) first  
**Last Updated:** January 19, 2026

---

## Implementation Checklist Template

Copy this checklist for each new variant category:

```
Category: ________________
Date Started: ____________
Status: [ ] Planning [ ] In Progress [ ] Testing [ ] Complete

Phase 1: Research & Data Collection
  [ ] All Pokémon identified
  [ ] English names confirmed
  [ ] German names confirmed
  [ ] French names confirmed
  [ ] Spanish names confirmed
  [ ] Italian names confirmed
  [ ] Japanese names confirmed
  [ ] Korean names confirmed
  [ ] Simplified Chinese names confirmed
  [ ] Traditional Chinese names confirmed
  [ ] Image URLs collected and verified
  [ ] Types verified
  [ ] Multi-form cases identified

Phase 2: JSON Data File
  [ ] Created /data/variants/variants_{type}.json
  [ ] JSON valid (tested with jsonlint)
  [ ] All Pokémon have all 9 language names
  [ ] All image URLs accessible
  [ ] Icon and color selected
  [ ] Pokemon counts accurate

Phase 3: Code Integration
  [ ] Added color to VARIANT_COLORS in variant_pdf_generator.py
  [ ] Updated meta.json
  [ ] Added i18n strings if needed

Phase 4: Testing
  [ ] Single language generation works
  [ ] All 9 languages generate without errors
  [ ] PDFs render correctly
  [ ] Images display properly
  [ ] Cover page shows correct data
  [ ] No missing or corrupted Pokémon

Phase 5: Documentation
  [ ] Updated VARIANTS_ARCHITECTURE.md
  [ ] Documented any special cases
  [ ] Added example commands
```

---

## Step 1: Research & Data Collection

### 1.1 Identify All Pokémon

Use reliable sources:
- **Primary:** Bulbapedia (https://bulbapedia.bulbagarden.net)
- **Secondary:** Official Pokémon Games
- **Tertiary:** PokeAPI (https://pokeapi.co)

**Research Process:**
```
1. Go to Bulbapedia page for your variant category
2. Extract all Pokémon listed
3. Verify with PokeAPI /pokemon endpoint
4. Confirm official artwork availability
```

### 1.2 Gather Multilingual Names

**Spreadsheet Template:**

| # | English | Deutsch | Français | Español | Italiano | 日本語 | 한국어 | 简体 | 繁體 | Image URL |
|---|---------|---------|----------|---------|----------|--------|--------|------|------|-----------|
| 25 | Pikachu | Pikachu | Pikachu | Pikachu | Pikachu | ピカチュウ | 피카츄 | 皮卡丘 | 皮卡丘 | https://... |

**Name Sources:**
- **English/German/French/Spanish/Italian:** Bulbapedia (language tabs)
- **Japanese:** PokeAPI or official Japanese Pokémon site
- **Korean:** PokeAPI or Korean fan sites
- **Chinese:** PokeAPI, Bulbapedia Chinese version

### 1.3 Determine Image Sources

**Priority Order:**

1. **PokeAPI Official Artwork** (Primary)
   - Format: `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{form_id}.png`
   - Endpoint: `GET /pokemon-form/{form_id}` or `GET /pokemon/{name}`
   - Check: `forms` array → `official_artwork` URL
   - Verify: Images must be accessible and high-quality

2. **Bulbapedia Images** (Fallback)
   - Source: Pokemon info pages
   - Method: Extract from `<img>` tags
   - URL optimization: Remove `/thumb/` for full resolution
   - Example: `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/10033.png`

3. **Manual Mapping** (Last Resort)
   - Use only for unavailable images
   - Document in variant JSON with special note

### 1.4 Collect Type Information

Use PokeAPI endpoint: `GET /pokemon/{name}`

```bash
curl https://pokeapi.co/api/v2/pokemon/pikachu | jq '.types[] | .type.name'
# Output: electric
```

---

## Step 2: Create Variant JSON File

### 2.1 File Naming & Location

```
Location: /data/variants/variants_{type_slug}.json
Naming: Use snake_case
Example: variants_{category_name}.json
```

### 2.2 Complete JSON Schema

```json
{
  "variant_type": "gigantamax",
  "variant_name": "Gigantamax",
  "variant_name_de": "Gigadynamax",
  "variant_name_fr": "Gigantamax",
  "variant_name_es": "Gigantamax",
  "variant_name_it": "Gigantamax",
  "variant_name_ja": "ギガンタマックス",
  "variant_name_ko": "기가맥스",
  "variant_name_zh_hans": "极巨化",
  "variant_name_zh_hant": "極巨化",
  "short_code": "GIGANTAMAX",
  "icon": "📏",
  "color_hex": "#C5283F",
  "pokemon_count": 32,
  "forms_count": 32,
  "pokemon": [
    {
      "id": "#003_GIGANTAMAX",
      "pokedex_number": 3,
      "name_en": "Venusaur",
      "name_de": "Bisakunodon",
      "name_fr": "Florizarre",
      "name_es": "Venusaur",
      "name_it": "Venusaur",
      "name_ja": "フシギバナ",
      "name_ko": "이상해꽃",
      "name_zh_hans": "妙蛙花",
      "name_zh_hant": "妙蛙花",
      "variant_prefix": "Gigantamax",
      "variant_form": "",
      "types": ["Grass", "Poison"],
      "image_url": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/10052.png"
    }
  ]
}
```

### 2.3 Important Details

**ID Format:**
```
#{POKEDEX_NUMBER}_{VARIANT_TYPE}[_{FORM_SUFFIX}]

Single Form (most common):
#025_GIGANTAMAX

Multiple Forms (when applicable):
#104_PALDEA_WATER
#104_PALDEA_FIRE
#104_PALDEA_ELECTRIC

Special Characters (escape for filename safety):
#201_UNOWN_?     (Question Mark Unown)
#201_UNOWN_!     (Exclamation Mark Unown)
```

**Pokedex Numbers:**
- Use the BASE Pokémon's pokedex number
- Examples:
  - Mega Charizard X: `#006` (Charizard's number)
  - Alolan Raichu: `#026` (Raichu's number)
  - Gigantamax Pikachu: `#025` (Pikachu's number)

**Types Array:**
- Must be array of valid type names
- Valid types: Normal, Fire, Water, Electric, Grass, Ice, Fighting, Poison, Ground, Flying, Psychic, Bug, Rock, Ghost, Dragon, Dark, Steel, Fairy
- Get from PokeAPI if unsure

**Variant Form:**
- Empty string `""` for single form variants
- Lowercase suffix for multi-form variants: `"x"`, `"y"`, `"water"`, `"fire"`, etc.
- Used for display in card generation

**Image URL:**
- Must be direct URL to PNG image
- Must be accessible (test with curl)
- Should be high-resolution (600x600 or larger)
- Transparent background preferred

### 2.4 Data Validation

After creating JSON file, validate:

```bash
# Check JSON syntax
python3 -m json.tool /data/variants/variants_gigantamax.json > /dev/null && echo "Valid JSON"

# Verify all required fields
python3 << 'EOF'
import json
with open('/data/variants/variants_gigantamax.json') as f:
    data = json.load(f)
    
required_pokemon_fields = [
    'id', 'pokedex_number', 'name_en', 'name_de', 'name_fr', 'name_es', 'name_it',
    'name_ja', 'name_ko', 'name_zh_hans', 'name_zh_hant',
    'variant_prefix', 'variant_form', 'types', 'image_url'
]

for pokemon in data['pokemon']:
    for field in required_pokemon_fields:
        if field not in pokemon:
            print(f"Missing '{field}' in {pokemon['id']}")

print(f"Total Pokémon: {len(data['pokemon'])}")
print(f"Pokemon count field: {data['pokemon_count']}")
print(f"Forms count field: {data['forms_count']}")
EOF
```

---

## Step 3: Update Metadata

### 3.1 Update `meta.json`

**Location:** `/data/variants/meta.json`

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
      "notes": "76 Pokémon species, 79 unique forms"
    },
    {
      "id": "gigantamax",
      "order": 2,
      "json_file": "variants_gigantamax.json",
      "pokemon_count": 32,
      "forms_count": 32,
      "status": "complete",
      "notes": "32 Pokémon with Gigantamax form"
    }
  ],
  "statistics": {
    "total_pokemon": 108,
    "total_forms": 111,
    "total_categories": 2
  }
}
```

**Order Field:** Sequential number for generation order (1-9)
**Status Values:** `"complete"`, `"in_progress"`, `"planned"`

---

## Step 4: Code Integration

### 4.1 Add Color to PDF Generator

**File:** `/scripts/lib/variant_pdf_generator.py`

```python
# Around line 35
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

### 4.2 i18n Strings (if UI-facing)

**File:** `/i18n/translations.json`

Add variant names if needed for user-facing UI:

```json
{
  "variant.gigantamax": "Gigantamax",
  "variant.gigantamax.de": "Gigadynamax",
  "variant.gigantamax.fr": "Gigantamax",
  "variant.gigantamax.es": "Gigantamax",
  "variant.gigantamax.it": "Gigantamax",
  "variant.gigantamax.ja": "ギガンタマックス",
  "variant.gigantamax.ko": "기가맥스",
  "variant.gigantamax.zh_hans": "极巨化",
  "variant.gigantamax.zh_hant": "極巨化"
}
```

---

## Step 5: Testing

### 5.1 Single-Language Test

```bash
# Generate one PDF to verify data
python scripts/generate_pdf.py --type variant --variant gigantamax --language de

# Check output
ls -lh output/de/variants/variant_gigantamax_de.pdf
```

**Expected:**
- File created in `/output/de/variants/`
- Size: 2-5 MB
- No errors in console output

### 5.2 Multi-Language Test

```bash
# Generate all language variants
python scripts/generate_pdf.py --type variant --variant gigantamax --language all

# Verify all files created
ls output/*/variants/variant_gigantamax_*.pdf | wc -l
# Should output: 9
```

### 5.3 Visual Inspection

Open generated PDF and verify:

- [ ] Cover page displays correctly
- [ ] Variant name is correct
- [ ] Variant icon and color are correct
- [ ] Pokémon count is accurate
- [ ] All Pokémon cards render properly
- [ ] Text in correct language
- [ ] Images display without issues
- [ ] Cutting guides are visible
- [ ] No text overflow or layout issues

### 5.4 Data Verification

```bash
# Verify PDF generation logs
python scripts/generate_pdf.py --type variant --variant gigantamax --language en 2>&1 | grep -E "(ERROR|WARNING)"

# Should have no errors, only progress messages
```

---

## Step 6: Special Cases & Edge Cases

### Regional Forms with Multiple Sub-Variants

**Example: Paldean Tauros**

Tauros has 3 distinct Paldean forms:

```json
[
  {
    "id": "#104_PALDEA",
    "name_en": "Tauros",
    "variant_form": "",
    "types": ["Normal"]
  },
  {
    "id": "#104_PALDEA_WATER",
    "name_en": "Tauros (Water)",
    "variant_form": "water",
    "types": ["Water", "Fighting"]
  },
  {
    "id": "#104_PALDEA_FIRE",
    "name_en": "Tauros (Fire)",
    "variant_form": "fire",
    "types": ["Fire", "Fighting"]
  }
]
```

**Implementation Note:**
- Use empty `variant_form` for the base form
- Suffix subsequent forms with lowercase descriptors
- Include the form in the card display during rendering

### Forms with Special Characters

**Example: Unown**

Unown has 28 forms (A-Z, ?, !):

```json
[
  {
    "id": "#201_UNOWN_A",
    "name_en": "Unown (A)",
    "variant_form": "a"
  },
  {
    "id": "#201_UNOWN_?",
    "name_en": "Unown (?)",
    "variant_form": "?"
  },
  {
    "id": "#201_UNOWN_!",
    "name_en": "Unown (!)",
    "variant_form": "!"
  }
]
```

**Implementation Note:**
- Characters are safe in JSON strings (escaped if needed)
- Card rendering handles special characters automatically
- Use as-is in variant_form field

### Gender Differences

For Pokémon with visually distinct female forms:

```json
{
  "id": "#025_FEMALE",
  "name_en": "Pikachu",
  "variant_form": "female",
  "types": ["Electric"]
}
```

---

## Step 7: Documentation

### 7.1 Document Variant-Specific Information

Add to [VARIANTS_ARCHITECTURE.md](VARIANTS_ARCHITECTURE.md):

```markdown
## [Variant Name] Reference Implementation

**Statistics:**
- **Pokémon:** X species
- **Forms:** Y unique forms
- **Data File:** `/data/variants/variants_{type}.json`
- **PDFs:** 9 languages × 1 variant = 9 PDF files

**Special Features:**
- List any unique characteristics
- Document non-standard implementations
- Note any deviations from schema

**Example CLI:**
\`\`\`bash
python scripts/generate_pdf.py --type variant --variant {type} --language de
\`\`\`
```

### 7.2 Update Quick Reference

Update table in this guide with new variant status.

---

## Common Issues & Solutions

### Issue: Image URLs Not Found

**Symptom:** PDF generation fails or images missing from cards

**Solutions:**
1. Verify URL is accessible: `curl -I "https://..."`
2. Check URL format (should end in `.png`)
3. Verify PokeAPI form ID is correct
4. Use Bulbapedia scraping as fallback

### Issue: Missing Translation in One Language

**Symptom:** PDF generated but shows `[MISSING]` or blank name

**Solution:**
1. Verify JSON has 9-language names for all Pokémon
2. Check for typos in language keys: `name_de`, `name_en`, etc.
3. Ensure no special characters causing encoding issues

### Issue: Type Not Recognized

**Symptom:** Card styling appears wrong or error on type processing

**Solution:**
1. Verify types against valid type list (see Step 2.3)
2. Check for typos in type name
3. Ensure types are in lowercase in PokeAPI query

### Issue: JSON Validation Fails

**Symptom:** Generation fails with JSON error

**Solutions:**
1. Validate with: `python3 -m json.tool variants_xxx.json`
2. Check for unescaped quotes or special characters
3. Ensure all required fields present
4. Use online JSON validator (jsonlint.com)

---

## Performance Tips

### Parallel Generation

For faster multi-language PDF generation:

```bash
python scripts/generate_pdf.py --type variant --variant all --language all --parallel
```

Estimated time: 15-20 minutes for all 9 variants × 9 languages (vs. 45-60 minutes sequential)

### Image Caching

Images are automatically cached. For subsequent runs with same variant:
- First run (uncached): 3-5 minutes per variant
- Subsequent runs (cached): 30-60 seconds per variant

### Memory Considerations

For large variant categories:
- Keep Python process memory usage < 500MB
- ReportLab handles PDF generation efficiently
- No special optimization needed for < 50 Pokémon per variant

---

## Troubleshooting Checklist

Before reporting issues:

- [ ] JSON validates: `python3 -m json.tool variants_xxx.json > /dev/null`
- [ ] All 9 language names present for each Pokémon
- [ ] Image URLs tested and accessible
- [ ] meta.json updated correctly
- [ ] Color added to VARIANT_COLORS
- [ ] Single language test successful
- [ ] Read [VARIANTS_ARCHITECTURE.md](VARIANTS_ARCHITECTURE.md) completely
- [ ] Checked logs for specific error messages

---

## Reference Data

### Valid Type Names

```
Normal, Fire, Water, Electric, Grass, Ice, Fighting, Poison,
Ground, Flying, Psychic, Bug, Rock, Ghost, Dragon, Dark, Steel, Fairy
```

### Language Codes

```
de = German (Deutsch)
en = English
fr = French (Français)
es = Spanish (Español)
it = Italian (Italiano)
ja = Japanese (日本語)
ko = Korean (한국어)
zh_hans = Simplified Chinese (简体中文)
zh_hant = Traditional Chinese (繁體中文)
```

### Variant Color Palette

```
Gold      #FFD700  (Template for new variants)
```

For each new variant category, define a unique color code to distinguish it visually.

---

## Next Steps After Implementation

1. **Testing Phase:** Verify all 9 languages with visual inspection
2. **Documentation:** Update README files with implementation notes
3. **Release:** Include in next version release notes
4. **Feedback:** Collect user feedback on card layout and information
5. **Refinement:** Adjust based on feedback for next variant

---

