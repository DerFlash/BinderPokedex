# Pokémon Variants Data

This directory contains JSON data for all Pokémon variant categories.

## Implementation Status

✅ **Phase 1 Complete: Mega Evolution**
- 76 Pokémon species with 79 Mega forms
- Full PDF generation in 9 languages (DE, EN, ES, FR, IT, JA, KO, ZH-HANS, ZH-HANT)
- Form-specific imagery (PokeAPI + Bulbapedia fallback)
- Card index with darkened type colors
- Cutting guides and professional layout

🔄 **Phase 2 Planned: Additional Variants**
- Gigantamax forms (32+ Pokémon)
- Regional variants (Alola, Galar, Hisui, Paldea)
- Primal Reversion & Terastal forms
- Pattern variations (Unown, Vivillon, etc.)
- Fusion forms (Calyrex, Zamazenta, Zaacian)

## Files

- **meta.json** - Metadata for all variant categories, versioning, and statistics
- **logos/** - Logo assets for variant categories (localized and default)
  - **mega_evolution/** - Localized Mega Evolution logos (de.png, en.png, ja.png, etc.)
  - **ex/**, **ex_new/**, **ex_tera/**, **m_pokemon/** - Default logos for EX variants
- **variants_mega.json** - Mega Evolution forms (76 Pokémon, 79 forms) ✅ COMPLETE
- **variants_gigantamax.json** - Gigantamax forms (32+ Pokémon)
- **variants_regional_alola.json** - Alolan regional forms (18 Pokémon)
- **variants_regional_galar.json** - Galarian regional forms (16 Pokémon)
- **variants_regional_hisui.json** - Hisuian regional forms (15 Pokémon)
- **variants_regional_paldea.json** - Paldean regional forms (8 Pokémon)
- **variants_primal_terastal.json** - Primal Reversion & Terastal forms (6 Pokémon)
- **variants_patterns_unique.json** - Unown, Vivillon, Castform, Oricorio, Gender Differences (130+ Pokémon)
- **variants_fusion_special.json** - Fusion forms (3 Pokémon, 6 forms)

## Data Structure

Each variant file follows this schema:

```json
{
  "variant_type": "mega_evolution",
  "variant_name": "Mega Evolution",
  "short_code": "MEGA",
  "icon": "⚡",
  "color_hex": "#FF9900",
  "pokemon_count": 87,
  "forms_count": 96,
  "pokemon": [
    {
      "id": "#003_MEGA",
      "pokedex_number": 3,
      "base_pokemon_name": "Venusaur",
      "variant_name": "Mega Venusaur",
      "types": ["Grass", "Poison"],
      "base_stats": { ... },
      "image_url": ""
    }
  ]
}
```

## Numbering Schema

Format: `#{pokemon_id}_{VARIANT_TYPE}[_{FORM_SUFFIX}]`

Examples:
- `#003_MEGA` - Single variant (Mega Venusaur)
- `#006_MEGA_X` - Multiple variants (Mega Charizard X)
- `#006_MEGA_Y` - Multiple variants (Mega Charizard Y)
- `#104_PALDEA` - Paldean Tauros (default form, new)
- `#104_PALDEA_WATER` - Paldean Tauros (water form)
- `#201_UNOWN_?` - Special character suffix (Unown Question Mark)
- `#012_FEMALE` - Gender difference (Butterfree female)

## Implementation Status

All files are prepared with schema templates. Population with actual Pokémon data happens in Phase 2 (MVP - Mega Evolution).
