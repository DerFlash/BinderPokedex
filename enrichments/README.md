# Pokémon Data Enrichment Guide

## Overview

The enrichment system allows optional enhancement of Pokémon data with additional languages and translations that are not available via PokéAPI.

This keeps the core data clean and minimal while enabling community contributions for expanded language support.

---

## Supported Enrichments

### Spanish (ES)
- **Source:** [Bulbapedia - Spanish Pokémon Names](https://bulbapedia.bulbagarden.net/wiki/List_of_Spanish_Pok%C3%A9mon_names)
- **Status:** Available for community contribution
- **Note:** Most Gen 1-8 Pokémon names are identical to English (official names)

### Italian (IT)
- **Status:** Available for community contribution
- **Note:** Limited official Italian translations available

### Featured Pokémon
- **Purpose:** Highlight specific Pokémon on cover pages
- **Format:** Generation-based list of Pokémon IDs

---

## File Structure

```
enrichments/
├── translations_es.json      # Spanish translations
├── translations_it.json      # Italian translations
├── featured_pokemon.json     # Featured Pokémon for covers
└── README.md                 # This file
```

---

## Translation File Format

Each translation file is a simple JSON mapping:

```json
{
  "1": "Bisasaur",
  "2": "Ivysaur",
  "3": "Venusaur",
  "4": "Charmander",
  "25": "Pikachu",
  "151": "Mew"
}
```

**Format Rules:**
- Keys are Pokémon IDs as strings (e.g., `"1"`, `"25"`)
- Values are the translated Pokémon names
- Only include Pokémon that differ from English names
- For identical names, you can omit them or include them

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
  - step: enrich_translations_es_it
    params:
      es_file: enrichments/translations_es.json
      it_file: enrichments/translations_it.json
  
  - step: enrich_featured_pokemon
    params:
      featured_file: enrichments/featured_pokemon.json
```

---

## Contributing Translations

### For Spanish (ES)

1. Reference: [Bulbapedia Spanish List](https://bulbapedia.bulbagarden.net/wiki/List_of_Spanish_Pok%C3%A9mon_names)
2. For most Pokémon (Gen 1-8), the English name is the official Spanish name
3. Include different names for:
   - Type: Null → `"Código Cero"`
   - Paradox Pokémon (Gen 9)

### For Italian (IT)

1. Reference official Pokémon game localization
2. Most Pokémon may not have official Italian translations
3. Use English as fallback when not available

---

## Data Quality

- **Enrichment is optional** - works without additional translations
- **Fallback to English** - missing translations default to English name
- **Community maintained** - translation files can be updated independently
- **Version controlled** - enrichment files are tracked in Git
- **Static configuration** - not generated, manually curated

---

## Future Expansion

Possible additional enrichments:
- Portuguese (PT) translations
- Russian (RU) translations
- Regional variants (e.g., Latin American Spanish)
- Game-specific names (different across generations)
- Additional featured Pokémon for each generation

---

## References

- [Bulbapedia - Spanish Pokémon Names](https://bulbapedia.bulbagarden.net/wiki/List_of_Spanish_Pok%C3%A9mon_names)
- [Pokémon.com Spanish Pokédex](https://www.pokemon.com/es/pokedex/)
- [Official Pokémon Translations](https://bulbapedia.bulbagarden.net/wiki/List_of_Italian_Pok%C3%A9mon_names)
