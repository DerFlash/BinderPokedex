# Data Fetcher - Feature Documentation

**Status**: ✅ Implemented & Production-Ready

The Data Fetcher is a config-driven, step-based system for fetching and processing Pokémon data from multiple sources (PokeAPI, manual enrichments) into the target format required by the PDF generator.

## Features

**✅ Implemented:**
- Complete National Dex fetching (1025 Pokémon, 9 generations)
- Config-driven pipeline with YAML scopes
- Automatic retry logic with exponential backoff
- Rate limiting for API stability (0.2s between requests)
- Source/Target data separation
- Translation enrichments (ES/IT with 52 entries each)
- Featured Pokémon enrichment
- Generation-based grouping
- Test scopes for development

**User Stories:**

**US1: Kompletter Pokédex laden**
- Alle Pokémon in einem Befehl laden
- Selten benötigt (Setup + Updates)

**US2: Neue Pokémon nachladen**
- Nur neue Pokémon laden bei neuer Generation
- System erkennt was neu ist

**US3: Einzelne Pokémon aktualisieren**
- Gezieltes Neuladen für Fehlerkorrekturen

**US4: Source und Target trennen**
- Rohdaten (Source) getrennt von finaler Struktur (Target)
- Rohdaten können überschrieben werden
- Target hat Anreicherungen und bleibt stabil

**US5: Manuelle Anpassungen erhalten**
- Nur API-generierte Daten werden aktualisiert

## Architecture: Fetcher Pattern

**Implementation**: Config → Fetcher Steps → Target

**Location**: `scripts/fetcher/`

### Data Sources

The fetcher supports multiple API sources for different data types:

| API | Purpose | Languages | Client | Status |
|-----|---------|-----------|--------|--------|
| **PokeAPI** | National Pokédex data (species, forms, stats, sprites) | 8 languages (DE, EN, FR, ES, IT, JA, KO, ZH) | `pokeapi_client.py` | ✅ Production |
| **Pokémon TCG API** | TCG cards (EX, GX, V, VMAX, etc.) | English only | `tcg_client.py` | ✅ Ready |
| **TCGdex** | TCG cards (multilingual, complete) | 10+ languages (DE, EN, FR, ES, IT, PT, JA, ZH, ID, TH) | `tcgdex_client.py` | ✅ Ready |

**API Details:**
- **PokeAPI**: Rate limit 100/min, comprehensive Pokémon data, official source
- **Pokémon TCG API**: 20k/day (200k with key), Lucene query syntax, English-focused
- **TCGdex**: ~10M/month, GraphQL support, TCG Pocket integration, multilingual

**Usage Strategy:** 
- Use PokeAPI for National Dex scopes
- Use TCGdex for multilingual TCG card scopes (preferred)
- Use Pokémon TCG API for English-only TCG scopes or specific query needs

### Directory Structure

```
scripts/fetcher/
├── fetch.py                                  # CLI entry point
├── engine.py                                 # Execution engine
├── config/scopes/
│   ├── pokedex.yaml                         # Full National Dex (1025 Pokémon)
│   ├── ExGen1.yaml                          # Classic ex cards
│   ├── ExGen2.yaml                          # BW/XY EX cards
│   ├── ExGen3.yaml                          # SV ex cards
│   ├── ME01.yaml                            # TCG set example
│   ├── test_fetch.yaml                      # Test scope (3 per gen)
│   └── test.yaml                            # Engine test
├── steps/
│   ├── base.py                              # BaseStep, PipelineContext
│   ├── fetch_pokeapi_national_dex.py        # ✅ Implemented
│   ├── fetch_tcgdex_set.py                  # ✅ Implemented
│   ├── enrich_tcg_names_multilingual.py     # ✅ Implemented
│   ├── enrich_tcg_cards_from_pokedex.py     # ✅ Implemented
│   ├── transform_tcg_set.py                 # ✅ Implemented
│   ├── transform_to_sections_format.py      # ✅ Implemented
│   ├── group_by_generation.py               # ✅ Implemented
│   └── enrich_translations_es_it.py         # ✅ Implemented
├── lib/
│   ├── pokeapi_client.py                    # ✅ PokeAPI client
│   ├── tcg_client.py                        # ✅ Pokémon TCG API client
│   └── tcgdex_client.py                     # ✅ TCGdex client
└── data/enrichments/
    ├── translations_es.json                  # Spanish overrides (52)
    └── translations_it.json                  # Italian overrides (52)

data/
├── source/
│   └── pokedex.json                  # Raw API data (flat list)
└── Pokedex.json                      # Final target (generation-grouped)
```

**Key Principle**: Target structure is fixed (PDF Generator requirement). Fetcher transforms Source → Target, never reverse.

### Fetcher Steps

**✅ Implemented Steps:**

**fetch_pokeapi_national_dex** - Fetch from PokeAPI
- Fetches species + pokemon data for all National Dex entries
- Supports generation filtering: `generations: [1, 2, 3]`
- Optional limit per generation: `limit: 3` (for testing)
- Retry logic: 3 attempts with 1s, 2s, 3s backoff
- Rate limiting: 0.2s between requests
- Timeout: 10s per request
- Saves to: `data/source/{scope}.json`

**fetch_tcgdex_set** - Fetch TCG Set
- Fetches complete TCG set from TCGdex API (e.g., ME01)
- Retrieves set metadata including logos and release dates
- English card names and localIds
- Saves to: `data/source/{set_id}.json`

**fetch_tcgdex_ex_gen{1,2,3}** - Fetch TCG ex/EX Cards
- ExGen1: Classic ex series (Ruby/Sapphire era, 2003-2006)
- ExGen2: Pokemon-EX from BW & XY series (2012-2016) 
- ExGen3: Scarlet & Violet ex series (2023-present)
- Fetches from TCGdex API with set-specific filtering
- Handles Mega Evolution and Primal Reversion variants
- Saves to: `data/source/tcg_{classic,bw,sv}_ex.json`

**transform_ex_gen{1,2,3}** - Transform TCG Cards
- Selects ONE card per Pokemon (priority: first set > alphabetical)
- Groups Mega variants by (dexId, form_suffix) for X/Y separation
- Extracts form variants (X/Y for Mega, Primal for primals)
- **PokeAPI Artwork Integration**:
  - Always uses PokeAPI official artwork (TCG images include card frames)
  - Normal Pokemon: Direct artwork URL with dex_id
  - Mega X/Y: Queries PokeAPI for form-specific IDs (10034/10035 for Charizard)
  - Primal forms: Uses `{name}-primal` pattern
  - Fallback to base Pokemon artwork if form not found
- Saves to: `data/ExGen{1,2,3}.json`

**group_by_generation** - Transform to Target Format
- Converts flat Pokemon list to generation-grouped structure
- Matches PDF generator's expected format
- Maps language codes (ja, ko, zh_hans, zh_hant)
- Converts types array to type1/type2 fields
- Adds generation metadata (name, region, range)

**enrich_translations_es_it** - Translation Enrichment
- Loads: `scripts/fetcher/data/enrichments/translations_es.json` (52 entries)
- Loads: `scripts/fetcher/data/enrichments/translations_it.json` (52 entries)
- Overwrites Pokemon names where better translations exist
- Applied before grouping (on source data)

- Works for both Pokedex (generations) and Variants (sections)
- Example: ExGen3 mega section has [6, 94, 150] (Charizard, Gengar, Mewtwo)
- Applied after grouping (on target data)

**enrich_names_from_pokedex** - Pokemon Name Enrichment
- Enriches variant Pokemon names from Pokedex data
- Replaces TCG card names with canonical multilingual names
- Preserves form-specific names (e.g., "Charizard X")
- Applied after transformation (on target variant data)

**enrich_section_descriptions** - Section Description Enrichment  
- Adds descriptive text to generation/variant sections
- Loads from enrichments/section_descriptions.json
- Provides context about each Pokemon group (era, features, etc.)
- Applied after grouping (on target data)

**enrich_metadata** - Metadata Enrichment
- Adds metadata like titles, subtitles, colors to variants
- Loads from enrichments/metadata.json
- Supports all 9 languages
- Applied at pipeline start (before other steps)

**enrich_tcg_names_multilingual** - TCG Multilingual Names
- Fetches set data in all 9 languages from TCGdex API
- Enriches card names with translations (name_{lang} fields)
- Extracts set names in all languages
- Much more efficient than individual card fetching
- Applied after fetch_tcgdex_set

**transform_to_sections_format** - TCG Set to Sections
- Converts flat TCG cards array to sections format
- Generates multilingual metadata (title, description, subtitle)
- Embeds set logos with [image] tag in subtitles
- Formats release dates with localized labels
- Applied after transform_tcg_set

**cache_pokemon_images** - Image Caching
- Downloads Pokemon images to local cache
- Stores in scripts/data/pokemon_images_cache/
- Organizes by pokemon_id folders
- Enables offline PDF generation
- Applied as final pipeline step

**📋 Planned Steps** (not yet implemented):
- `fetch_tcg_ex_pokemon` - Pokemon TCG API
- `load_manual_list` - JSON File loader
- `enrich_from_tcg_api` - TCG data enrichment
- `group_by_tcg_set` - TCG set grouping

### Configuration Example

**Full National Dex** (`scripts/fetcher/config/scopes/pokedex.yaml`):
```yaml
scope: pokedex
description: "National Pokédex with all 9 generations"

pipeline:
  - step: fetch_pokeapi_national_dex
    params:
      generations: [1, 2, 3, 4, 5, 6, 7, 8, 9]
  
  - step: enrich_translations_es_it
    params:
      es_file: scripts/fetcher/data/enrichments/translations_es.json
      it_file: scripts/fetcher/data/enrichments/translations_it.json
  
  - step: group_by_generation
  
    params:

target_file: data/output/Pokedex.json
source_file: data/source/pokedex.json
```

**Test Scope** (`scripts/fetcher/config/scopes/test_fetch.yaml`):
```yaml
scope: test_fetch
description: "Test fetching Pokemon from PokeAPI (Gen1+2, first 3 per gen)"

pipeline:
  - step: fetch_pokeapi_national_dex
    params:
      generations: [1, 2]
      limit: 3  # Only first 3 per generation
  
  - step: group_by_generation
  
  - step: enrich_translations_es_it
    params:
      es_file: scripts/fetcher/data/enrichments/translations_es.json
      it_file: scripts/fetcher/data/enrichments/translations_it.json
  
    params:

target_file: data/test_fetch_output.json
source_file: data/source/test_fetch.json
```

### Data Sources

**✅ Implemented:**
- **PokeAPI** (v2) - National Dex, species, pokemon data
  - Direct REST API calls via `requests` library
  - Endpoints: `/api/v2/pokemon-species/{id}`, `/api/v2/pokemon/{id}`
  - Rate limited: 0.2s between requests
  - Retry logic: 3 attempts with exponential backoff
  - Timeout: 10s per request

- **Manual JSON Files** - Curated enrichments
  - `translations_es.json` - Spanish name overrides (52)
  - `translations_it.json` - Italian name overrides (52)

**📋 Planned:**
- **Pokemon TCG API** - Trading Cards, EX Pokemon, Sets

### Usage

**Fetch complete National Dex** (1025 Pokemon, 9 generations):
```bash
python scripts/fetcher/fetch.py --scope pokedex
```

**Test with small dataset** (3 Pokemon per generation):
```bash
python scripts/fetcher/fetch.py --scope test_fetch
```

**Dry-run** (show what would be executed):
```bash
python scripts/fetcher/fetch.py --scope pokedex --dry-run
```

**Output:**
```
📋 Loading scope: pokedex
✅ Config loaded: National Pokédex with all 9 generations
📁 Source: data/source/pokedex.json
📁 Target: data/output/Pokedex.json
🔧 Pipeline steps: 4

📋 Pipeline:
  1. fetch_pokeapi_national_dex with 1 params
  2. enrich_translations_es_it with 2 params
  3. group_by_generation

🚀 Starting pipeline with 4 steps

[1/4] Executing: fetch_pokeapi_national_dex
    🔍 Fetching from PokeAPI
    📊 Generations: [1, 2, 3, 4, 5, 6, 7, 8, 9]
    📝 Total Pokemon to fetch: 1025
    Progress: 1025/1025
    ✅ Fetched: 1025 Pokemon
    💾 Saved to: data/source/pokedex.json
    ✅ Completed

[2/4] Executing: enrich_translations_es_it
    📝 Loading translation enrichments
       ✅ Loaded 52 ES translations
       ✅ Loaded 52 IT translations
    ✅ Enriched 52 ES + 52 IT translations
    ✅ Completed

[3/4] Executing: group_by_generation
    🔄 Grouping Pokemon by generation
    📊 Processing 1025 Pokemon
    ✅ Grouped into 9 generations
       gen1: 151 Pokemon
       gen2: 100 Pokemon
       gen3: 135 Pokemon
       gen4: 107 Pokemon
       gen5: 156 Pokemon
       gen6: 72 Pokemon
       gen7: 88 Pokemon
       gen8: 96 Pokemon
       gen9: 120 Pokemon
    ✅ Completed

💾 Saved final output to: data/output/Pokedex.json
✅ Pipeline completed successfully!
```

## Implementation Details

### Core Properties

- **✅ Idempotent**: Multiple executions produce same result
- **✅ Serial**: Steps execute sequentially (simplicity over speed)
- **✅ Consistent**: Source = source of truth, target synchronized
- **✅ Extensible**: New steps/scopes via config files
- **✅ Target-Driven**: PDF Generator defines target structure
- **✅ Resilient**: Retry logic, timeout handling, rate limiting
- **✅ Testable**: Test scopes with limited datasets

### Error Handling

**API Failures:**
- 3 retry attempts with exponential backoff (1s, 2s, 3s)
- 10 second timeout per request
- 0.2s rate limiting between requests
- Graceful degradation on persistent failures

**Data Validation:**
- Missing enrichment files: warning + continue
- Malformed source data: error + stop
- Missing required parameters: error + stop

### Performance

**Full National Dex (1025 Pokemon):**
- Fetch time: ~6-8 minutes (with rate limiting)
- Source file size: ~1.2 MB
- Target file size: ~604 KB

**Test Scope (6 Pokemon):**
- Fetch time: ~3 seconds
- Ideal for development/testing

## Future Enhancements

**Planned Features:**
- TCG API integration for card-based collections
- Incremental updates (fetch only new Pokemon)
- Parallel fetching with worker pool
- Progress persistence for resume capability
- Additional enrichment sources

**Potential Scopes:**
- `tcg_ex_gen1` - EX Pokemon from TCG Gen1
- `tcg_ex_gen2` - EX Pokemon from TCG Gen2
- `mega_evolution` - Mega Evolution forms
- `regional_forms` - Regional variants (Alola, Galar, etc.)

## Related Documentation

- [scripts/README.md](../scripts/README.md) - Complete scripts documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - Overall system architecture
- [FEATURES.md](FEATURES.md) - Feature overview
