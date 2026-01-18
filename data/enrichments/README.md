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

---

## File Structure

```
data/enrichments/
├── translations_es.json    # Spanish translations
├── translations_it.json    # Italian translations
└── README.md              # This file
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

## Usage

### In Python Code

```python
from data_storage import DataStorage
from pokemon_enricher import PokémonEnricher

# Load Pokémon data
pokemon_list = DataStorage.load_generation(1)

# Enrich with Spanish and Italian translations
pokemon_list = PokémonEnricher.enrich_pokemon_list(
    pokemon_list, 
    languages=['es', 'it']
)

# Pokemon now have optional name_es and name_it fields
print(pokemon_list[0]['name_es'])  # If available
```

### Create Translation Template

```python
from pokemon_enricher import PokémonEnricher

# Create a template file to fill in
pokemon_list = DataStorage.load_generation(1)
template = PokémonEnricher.create_translation_template(pokemon_list, 'es')

# Save template for translators
PokémonEnricher.save_translations(template, 'es')
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

## Integration with Fetch Script

The enricher is automatically integrated into the fetch pipeline:

```bash
# Fetch Gen 1 and auto-load enrichments if available
python fetch_pokemon_from_pokeapi.py --generation 1
```

If `data/enrichments/translations_es.json` exists, Spanish names will be automatically added.

---

## Data Quality

- **Enrichment is optional** - works without additional translations
- **Fallback to English** - missing translations default to English name
- **Community maintained** - translation files can be updated independently
- **Version controlled** - enrichment files can be tracked in Git

---

## Future Expansion

Possible additional enrichments:
- Portuguese (PT) translations
- Russian (RU) translations
- Regional variants (e.g., Latin American Spanish)
- Game-specific names (different across generations)

---

## Example Workflow

```bash
# 1. Fetch base data (5 languages from PokéAPI)
python scripts/fetch_pokemon_from_pokeapi.py --generation 1

# 2. Create Spanish translation template
python -c "
from data_storage import DataStorage
from pokemon_enricher import PokémonEnricher

poke_list = DataStorage.load_generation(1)
template = PokémonEnricher.create_translation_template(poke_list, 'es')
PokémonEnricher.save_translations(template, 'es')
"

# 3. Edit data/enrichments/translations_es.json with real translations

# 4. Enrich the data
python -c "
from data_storage import DataStorage
from pokemon_enricher import PokémonEnricher

poke_list = DataStorage.load_generation(1)
poke_list = PokémonEnricher.enrich_pokemon_list(poke_list, ['es'])

# Use enriched data...
"
```

---

## References

- [Bulbapedia - Spanish Pokémon Names](https://bulbapedia.bulbagarden.net/wiki/List_of_Spanish_Pok%C3%A9mon_names)
- [Pokémon.com Spanish Pokédex](https://www.pokemon.com/es/pokedex/)
- [Official Pokémon Translations](https://bulbapedia.bulbagarden.net/wiki/List_of_Italian_Pok%C3%A9mon_names)
