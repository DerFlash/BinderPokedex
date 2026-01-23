# Variants Quick Start - Adding New Variants

**Last Updated:** January 23, 2026

---

## Prerequisites

- Python 3.10+
- Basic knowledge of JSON
- Understanding of Pokémon variant types

---

## Step-by-Step Guide

### 1. Research Your Variant

**Identify:**
- All Pokémon in the variant category
- Special naming patterns (prefix/suffix)
- Section groupings (if multiple)
- Image sources (PokeAPI form IDs or URLs)

**Example: Mega Evolution**
- 79 Pokémon total
- Prefix: "Mega"
- Suffix: "ex"
- Special: X/Y forms for Charizard, Mewtwo
- Images: PokeAPI form IDs 10000+

---

### 2. Create Variant JSON File

**File:** `/data/variants/variants_{type}.json`

**Template:**
```json
{
  "type": "variant",
  "name": "Your Variant Name",
  "sections": {
    "normal": {
      "section_id": "normal",
      "color_hex": "#HEX_COLOR",
      "prefix": "Prefix Text",
      "suffix": "Suffix Text",
      "title": {
        "de": "German Title",
        "en": "English Title",
        "fr": "French Title",
        "es": "Spanish Title",
        "it": "Italian Title",
        "ja": "Japanese Title",
        "ko": "Korean Title",
        "zh_hans": "Chinese Simplified Title",
        "zh_hant": "Chinese Traditional Title"
      },
      "subtitle": {
        "de": "German Subtitle",
        "en": "English Subtitle",
        // ... all 9 languages
      },
      "iconic_pokemon": [1, 25, 150],
      "pokemon": []
    }
  }
}
```

---

### 3. Add Pokémon Entries

**Pokémon Template:**
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
  "image_url": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/25.png"
}
```

**Optional Fields:**
```json
{
  "id": 6,
  "variant_form": "x",           // For special forms: "delta", "x", "y"
  "prefix": "Special Prefix",    // Override section prefix
  "suffix": "Special Suffix",    // Override section suffix
  "name": { ... }
}
```

---

### 4. Update Metadata

**File:** `/data/variants/meta.json`

Add entry to `variant_categories` array:
```json
{
  "id": "your_variant_type",
  "order": 5,
  "json_file": "variants_your_variant_type.json",
  "pokemon_count": 50,
  "description": {
    "de": "German description",
    "en": "English description",
    // ... all 9 languages
  }
}
```

---

### 5. Cache Images (Optional)

**Cache Pokémon images locally:**
```bash
python scripts/cache_pokemon_images.py --type variant --variant your_variant_type
```

**Benefits:**
- Faster PDF generation
- Works offline
- Consistent quality

---

### 6. Generate PDFs

**Test single language:**
```bash
python scripts/generate_pdf.py --type variant --variant your_variant_type --language en
```

**Generate all languages:**
```bash
python scripts/generate_pdf.py --type variant --variant your_variant_type --language all
```

**Output:** `output/{language}/Your_Variant_Name_{LANG}.pdf`

---

## Special Cases

### Multiple Sections

**Example: EX Generation 1** has 3 sections:
```json
{
  "sections": {
    "normal": { "prefix": "", "suffix": "ex", ... },
    "rockets": { "prefix": "Rocket's", "suffix": "ex", ... },
    "special": { "prefix": "", "suffix": "ex", ... }
  }
}
```

**Each section gets its own cover page.**

---

### Delta Species

**Use `variant_form: "delta"` for Δ symbol:**
```json
{
  "id": 149,
  "variant_form": "delta",
  "name": {"en": "Dragonite"}
}
```
**Output:** "Dragonite ex δ"

---

### Mega X/Y Forms

**Use `variant_form: "x"` or `"y"`:**
```json
{
  "id": 6,
  "variant_form": "x",
  "name": {"en": "Charizard"}
}
```
**Output (with section prefix "Mega", suffix "ex"):** "Mega Charizard X ex"

---

### Pokémon-Specific Overrides

**Example: Special trainers:**
```json
{
  "id": 295,
  "prefix": "Imakuni?'s",
  "name": {"en": "Exploud"}
}
```
**Output (with section suffix "ex"):** "Imakuni?'s Exploud ex"

---

## Name Rendering Rules

**Construction Order:**
1. Use pokémon-level `prefix` OR section `prefix`
2. Add base `name`
3. Add `variant_form` ("X", "Y" after name; "δ" in suffix)
4. Use pokémon-level `suffix` OR section `suffix`

**Formula:** `{prefix} {name} {form} {suffix}`

**Examples:**
| Section | Pokémon | Result |
|---------|---------|--------|
| prefix="Mega", suffix="ex" | name="Charizard", variant_form="x" | "Mega Charizard X ex" |
| prefix="", suffix="ex" | name="Dragonite", variant_form="delta" | "Dragonite ex δ" |
| prefix="Rocket's", suffix="ex" | name="Meowth" | "Rocket's Meowth ex" |
| prefix="", suffix="ex" | name="Exploud", prefix="Imakuni?'s" | "Imakuni?'s Exploud ex" |

---

## Testing Checklist

- [ ] JSON validates (no syntax errors)
- [ ] All 9 languages have translations
- [ ] Image URLs accessible
- [ ] PDF generates without errors
- [ ] Names render correctly (check prefix/suffix)
- [ ] Special forms work (delta, X/Y)
- [ ] Cover page displays iconic_pokemon
- [ ] Multiple sections create separate covers

---

## Troubleshooting

**PDF generation fails:**
- Check JSON syntax: `python -m json.tool data/variants/variants_your_variant.json`
- Verify all required fields present
- Check image URLs are accessible

**Names render incorrectly:**
- Verify section prefix/suffix
- Check pokémon-level overrides
- Review variant_form values ("delta", "x", "y" only)

**Missing translations:**
- All title/subtitle must have 9 languages
- All pokémon names must have 9 languages
- Check language codes: de, en, fr, es, it, ja, ko, zh_hans, zh_hant

---

## Reference

**Full Documentation:** [VARIANTS_ARCHITECTURE.md](VARIANTS_ARCHITECTURE.md)  
**Feature Summary:** [VARIANTS_FEATURE_SUMMARY.md](VARIANTS_FEATURE_SUMMARY.md)  
**Existing Examples:** `/data/variants/variants_*.json`
