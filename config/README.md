# Configuration Directory

This directory contains centralized configuration for all BinderPokedex operations.

## Structure

```
config/
└── scopes/          # Scope configurations (YAML)
    ├── Pokedex.yaml
    ├── ExGen1_All.yaml
    └── ExGen1_Single.yaml

enrichments/         # Static enrichment data
├── translations_es.json
├── translations_it.json
└── README.md

data/                # Generated/temporary data
├── Pokedex.json
├── ExGen1_All.json
└── ExGen1_Single.json
```

## Scopes

Each scope is defined by a YAML configuration file that specifies:

- **scope**: Unique identifier (matches filename without extension)
- **description**: Human-readable description
- **pipeline**: List of processing steps for data fetching
- **source_file**: Where raw data is stored
- **target_file**: Where processed data is saved

### Available Scopes

| Scope | Description | Source | Target |
|-------|-------------|--------|--------|
| **Pokedex** | National Pokédex, all 9 generations | PokéAPI | data/output/Pokedex.json |
| **ExGen1_All** | TCG EX Gen 1 - all cards | TCGdex API | data/ExGen1_All.json |
| **ExGen1_Single** | TCG EX Gen 1 - one per Pokémon | TCGdex API | data/ExGen1_Single.json |

## Usage

### With Fetch Script

```bash
python scripts/fetcher/fetch.py --scope Pokedex
python scripts/fetcher/fetch.py --scope ExGen1_All
```

### With PDF Generator

```bash
python scripts/pdf/generate_pdf.py --scope Pokedex --language de
python scripts/pdf/generate_pdf.py --scope ExGen1_Single --language en
```

## Pipeline Steps

Scopes define a pipeline of steps that process data. Available steps:

- `fetch_pokeapi_national_dex` - Fetch from PokéAPI
- `fetch_tcgdex_classic_ex` - Fetch from TCGdex API
- `enrich_translations_es_it` - Add ES/IT translations
- `group_by_generation` - Organize by generation
- `validate_pokedex_exists` - Ensure dependency exists
- `transform_classic_ex_single` - One card per Pokémon
- `enrich_names_from_pokedex` - Add multilingual names

See [../enrichments/README.md](../enrichments/README.md) for enrichment data documentation.

## Creating New Scopes

1. Create a new YAML file in `config/scopes/`
2. Define the scope name, description, and pipeline
3. Test with fetch script: `python scripts/fetcher/fetch.py --scope YourScope`
