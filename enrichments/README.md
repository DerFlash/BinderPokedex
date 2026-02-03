# Pokémon Data Enrichment Guide

## Overview

The enrichment system provides cached API data and manual enhancements for Pokémon data.

All Pokémon names and type translations are now fetched automatically from PokeAPI and cached here for faster re-processing.

---

## Enrichment Files

### API-Cached Data

#### `type_translations.json`
- **Source:** PokéAPI `/type/{name}` endpoint
- **Purpose:** Pokemon type translations in all 9 languages
- **Languages:** de, en, es, fr, it, ja, ko, zh_hans, zh_hant
- **Format:** `{"Bug": {"de": "Käfer", "en": "Bug", "zh_hant": "蟲", ...}, ...}`
- **Auto-generated:** Yes (via `enrich_type_translations` step)

### Manual Enrichments

#### `featured_pokemon.json`
- **Purpose:** Highlight specific Pokémon on cover pages
- **Format:** Generation-based list of Pokémon IDs
- **Maintained:** Manually

#### `metadata.json`
- **Purpose:** Generation names, regions, and variant metadata
- **Maintained:** Manually

#### `variant_descriptions.json`
- **Purpose:** Section descriptions for variant collections
- **Maintained:** Manually

---

## File Structure

```
enrichments/
├── type_translations.json        # API-cached type translations (auto)
├── featured_pokemon.json         # Featured Pokémon for covers (manual)
├── metadata.json                 # Generation/variant metadata (manual)
├── variant_descriptions.json     # Variant descriptions (manual)
└── README.md                     # This file
```

---

## Type Translations Format

Auto-generated from PokeAPI. Example structure:

```json
{
  "Bug": {
    "de": "Käfer",
    "en": "Bug",
    "es": "Bicho",
    "fr": "Insecte",
    "it": "Coleottero",
    "ja": "むし",
    "ko": "벌레",
    "zh_hans": "虫",
    "zh_hant": "蟲"
  },
  "Fire": {
    "de": "Feuer",
    "en": "Fire",
    ...
  }
}
```

**Regeneration:** Run `fetch.py --scope Pokedex --start-from enrich_type_translations --stop-after enrich_type_translations`

---

## Featured Pokémon Format

```json
{
  "description": "Featured Pokémon for cover pages",
  "featured_by_generation": {
    "gen1": [25, 6, 150],
    "gen2": [],
    "gen3": []
  }
}
```

---

## Usage in Pipeline

The enrichments are automatically loaded during the fetch pipeline:

```yaml
# In config/scopes/Pokedex.yaml
pipeline:
  - step: enrich_type_translations  # Auto-fetches from PokeAPI
  
  - step: enrich_featured_pokemon
    params:
      featured_file: enrichments/featured_pokemon.json
```

---

## Data Sources

### PokéAPI (Automatic)
- **Pokémon Names:** All 9 languages via `/pokemon-species/{id}` endpoint
- **Type Translations:** All 9 languages via `/type/{name}` endpoint  
- **Cached:** Results cached in `enrichments/type_translations.json`

### Manual Enrichments
- **Featured Pokémon:** Curated list for cover pages
- **Metadata:** Generation names, regions
- **Variant Descriptions:** Section descriptions for variants

---

## Data Quality

- **API-first approach** - Translations from official Pokémon API
- **Automatic caching** - Speeds up subsequent pipeline runs
- **Fallback to English** - Missing translations default to English
- **Version controlled** - Cached data tracked in Git for consistency

---

## Future Expansion

Possible additional enrichments:
- Additional manual metadata as needed
- Custom ordering/grouping rules
- Regional variants (e.g., Latin American Spanish)
- Game-specific names (different across generations)
- Additional featured Pokémon for each generation

---

## References

- [Bulbapedia - Spanish Pokémon Names](https://bulbapedia.bulbagarden.net/wiki/List_of_Spanish_Pok%C3%A9mon_names)
- [Pokémon.com Spanish Pokédex](https://www.pokemon.com/es/pokedex/)
- [Official Pokémon Translations](https://bulbapedia.bulbagarden.net/wiki/List_of_Italian_Pok%C3%A9mon_names)
