# BinderPokedex Architecture

## Overview

The BinderPokedex project uses a clean modular architecture with a clear separation between:
- **Public API**: Main orchestration scripts in `scripts/`
- **Private Implementation**: Core libraries in `scripts/lib/`

This architecture ensures maintainability, testability, and scalability.

## Directory Structure

```
scripts/
├── fetch_pokemon_from_pokeapi.py  [467 lines] - Main data fetcher script
├── generate_pdf.py                [176 lines] - Main PDF generator script
└── lib/                           [Dictionary of modules]
    ├── __init__.py                [28 lines]  - Central module interface
    ├── data_storage.py            [67 lines]  - JSON storage operations
    ├── image_processor.py         [174 lines] - Font setup and image handling
    ├── pdf_layout.py              [58 lines]  - Layout constants and styling
    ├── pdf_renderer.py            [185 lines] - PDF canvas drawing functions
    └── pokeapi_client.py          [52 lines]  - PokéAPI HTTP client
```

## Module Responsibilities

### Main Scripts (Orchestration Only)

#### `fetch_pokemon_from_pokeapi.py` [467 lines]
**Purpose**: Fetch Pokémon data from PokéAPI with multi-language support
- Parses command-line arguments
- Coordinates data fetching from PokéAPI
- Enriches data with translations
- Stores results to JSON files

**Key Functions**:
- `parse_pokemon_argument()` - Parse ID ranges and lists
- `parse_generation_argument()` - Parse generation selections
- `fetch_generation()` - Fetch and process one generation

**Usage**:
```bash
# Fetch all generations
python fetch_pokemon_from_pokeapi.py

# Fetch specific generation
python fetch_pokemon_from_pokeapi.py -g 1

# Fetch generation range
python fetch_pokemon_from_pokeapi.py -g 1-5

# Fetch specific Pokémon
python fetch_pokemon_from_pokeapi.py -p 1,25,151
```

#### `generate_pdf.py` [176 lines]
**Purpose**: Generate PDF binders for Pokémon collections
- Validates generation/language inputs
- Loads and enriches Pokémon data
- Orchestrates PDF rendering process
- Supports batch PDF generation

**Key Functions**:
- `validate_generations()` - Parse generation selection
- `generate_pdfs()` - Orchestrate PDF generation

**Usage**:
```bash
# Generate Gen 1 PDF (English)
python generate_pdf.py --language en

# Generate multiple generations
python generate_pdf.py --language en --gen 1,3,5

# Generate all generations in all languages
python generate_pdf.py --language all --gen all
```

### Library Modules (Core Implementation)

#### `lib/__init__.py` [28 lines]
**Purpose**: Central module interface - single import point
**Exports**:
- Constants: `GENERATION_INFO`, `CARD_WIDTH`, `CARD_HEIGHT`, `GAP_X`, `GAP_Y`, `UNICODE_FONT`
- Classes: `DataStorage`, `PokéAPIClient`, `PokémonProcessor`, `PokémonEnricher`
- Functions: `draw_cover_page()`, `draw_pokemon_card()`, `setup_fonts()`, `get_font_for_language()`, `process_pokemon_image()`, `draw_pokemon_name_with_symbols()`

**Usage in scripts**:
```python
from lib import GENERATION_INFO, DataStorage, draw_pokemon_card
```

#### `lib/data_storage.py` [67 lines]
**Purpose**: Handle JSON file storage and loading
- `DataStorage.save_generation_data()` - Write JSON files
- `DataStorage.load_generation_data()` - Read JSON files
- Ensures consistent data serialization format

#### `lib/pokeapi_client.py` [52 lines]
**Purpose**: HTTP client for PokéAPI
- `PokéAPIClient.fetch_pokemon()` - Fetch single Pokémon data
- `PokéAPIClient.fetch_species()` - Fetch species information
- Handles retries and error handling
- Implements caching for efficiency

#### `lib/pdf_layout.py` [58 lines]
**Purpose**: Centralized PDF layout constants and styling
**Key Constants**:
- `GENERATION_INFO` - 9 generations with metadata (names, colors, Pokémon ranges)
- `CARD_WIDTH`, `CARD_HEIGHT` - Card dimensions (210mm × 297mm A4 page)
- `GAP_X`, `GAP_Y` - Spacing between cards
- `PAGE_MARGIN` - Page margins
- `CARDS_PER_ROW`, `CARDS_PER_COLUMN` - Layout grid
- Image processing constants (`PARALLEL_WORKERS`, image sources)

#### `lib/image_processor.py` [174 lines]
**Purpose**: Image handling and font management
**Key Functions**:
- `setup_fonts()` - Initialize fonts for all languages (including CJK)
- `get_font_for_language()` - Get appropriate font for language
- `process_pokemon_image()` - Download, resize, and optimize images
- `draw_pokemon_name_with_symbols()` - Render Pokémon names with special symbols

**Features**:
- CJK (Chinese, Japanese, Korean) font support
- Parallel image downloads
- Multiple image source fallbacks
- PNG optimization
- URL-based image cache differentiation for form variants

#### `lib/rendering/logo_renderer.py`
**Purpose**: Render logos and images in PDFs with [image] tag support
**Key Functions**:
- `parse_text_with_logos()` - Parse text with [image]URL[/image] tags
- `download_image()` - Download and cache images from URLs with MD5 hashing
- `draw_text_with_logos()` - Render text and inline images

**Features**:
- [image] tag parsing with regex
- MD5-based URL caching in temp directory
- ImageReader with mask='auto' for PNG transparency
- Inline image rendering with text flow
- Caching prevents re-downloads

#### `lib/rendering/image_cache.py`
**Purpose**: URL image caching system with MD5 hashing
**Key Functions**:
- `get_cached_image()` - Retrieve or download cached image
- `_generate_cache_key()` - MD5 hash of URL
- `_download_image()` - Download to cache directory

**Features**:
- Temporary directory storage
- MD5-based cache keys
- Automatic cache miss handling
- Thread-safe operations

#### Image Cache Architecture

**Purpose**: Efficiently cache Pokémon images while properly handling form variants (Mega X/Y, etc.)

**Key Components**:
- `ImageCache` class in `scripts/pdf/lib/pdf_generator.py`
- `cache_pokemon_images` step in fetcher pipeline
- Unified caching strategy between fetcher and PDF generator

**Cache Key Design**:
- **Old Format**: `pokemon_{id}_{size}` - caused collisions (Charizard ID 6 = normal & Mega X)
- **New Format**: `pokemon_{id}_{url_identifier}_{size}` - properly differentiates forms

**URL Identifier Extraction**:
- **PokeAPI URLs**: Extract numeric ID from path (e.g., `.../10034.png` → `"10034"`)
- **TCGdex URLs**: Extract card ID from path (e.g., `.../me02/013` → `"me02-013"`)

**Disk Cache Structure**:
```
data/pokemon_images_cache/
  pokemon_6/
    6_thumb.jpg         # Normal Charizard (180×180)
    6_featured.jpg      # Normal Charizard (500×500)
    10034_thumb.jpg     # Mega Charizard X (180×180)
    10034_featured.jpg  # Mega Charizard X (500×500)
    10035_thumb.jpg     # Mega Charizard Y (180×180)
    10035_featured.jpg  # Mega Charizard Y (500×500)
```

**Benefits**:
- Prevents cache collisions between base and form variants
- Consistent strategy across fetcher and PDF generator
- Supports both PokeAPI (10033+) and TCGdex (card IDs) image sources

#### `lib/pdf_renderer.py` [185 lines]
**Purpose**: PDF canvas drawing functions
**Key Functions**:
- `draw_cover_page()` - Render generation cover page with title, legend, info
- `draw_pokemon_card()` - Render single Pokémon card with image, stats, info

**Features**:
- Multi-language support
- Accurate type color coding
- Stats display (HP, ATK, DEF, SPD, SA, SD)
- Image handling and fallbacks
- Type legend display

## Data Flow

### PDF Generation Pipeline
```
main (generate_pdf.py)
    ↓
[validate generations/languages]
    ↓
DataStorage.load_generation_data()
    ↓
PokémonEnricher.enrich_generation()
    ↓
PokémonProcessor.process_generation()
    ↓
PokémonProcessor.download_images()
    ↓
[create PDF canvas]
    ↓
draw_cover_page() → image_processor → pdf_layout
    ↓
for each Pokémon:
    draw_pokemon_card() → image_processor → pdf_layout
    ↓
[save PDF]
```

### TCG Set Pipeline
```
fetch.py --scope ME01
    ↓
fetch_tcgdex_set (TCGdex API)
    ↓
enrich_tcg_names_multilingual (9 languages)
    ↓
enrich_tcg_cards_from_pokedex (Pokémon IDs & images)
    ↓
transform_tcg_set (normalize structure)
    ↓
transform_to_sections_format (add metadata)
    ↓
[saves to data/ME01.json]
    ↓
generate_pdf.py --scope ME01
    ↓
logo_renderer parses [image] tags
    ↓
URL image caching (MD5 hashes)
    ↓
[PDF with logos & multilingual metadata]
```

### Data Fetching Pipeline
```
main (fetch_pokemon_from_pokeapi.py)
    ↓
[parse generation/pokémon arguments]
    ↓
PokéAPIClient.fetch_pokemon()
    ↓
PokémonProcessor.process_generation()
    ↓
PokémonEnricher.enrich_generation()
    ↓
DataStorage.save_generation_data()
    ↓
[JSON file saved]
```

## Import Pattern

All scripts import from the central `lib` module:

```python
from lib import (
    # Constants
    GENERATION_INFO,
    CARD_WIDTH, CARD_HEIGHT,
    
    # Classes
    DataStorage,
    PokéAPIClient,
    PokémonProcessor,
    PokémonEnricher,
    
    # Functions
    draw_cover_page,
    draw_pokemon_card,
)
```

This ensures:
- **Single point of entry**: All public APIs exported from `lib/__init__.py`
- **Clean dependencies**: Scripts don't import directly from lib submodules
- **Easy refactoring**: Internal changes don't affect script imports
- **Maintainability**: Clear what's public vs. private

## Language Support

### Core Languages (Built-in)
- English (EN)
- German (DE)
- French (FR)
- Japanese (JA)
- Korean (KO)
- Chinese Simplified (ZH_CHS)
- Chinese Traditional (ZH_CHT)

### Optional Languages (Enrichment)
- Spanish (ES) - Added via enrichment
- Italian (IT) - Added via enrichment

## Key Design Decisions

### 1. Modularization
- **Before**: Single 659-line `generate_pdf.py`
- **After**: 176-line main + 8 library modules (58-185 lines each)
- **Benefit**: Better testability, reusability, maintainability

### 2. Centralized Constants
All layout and styling constants in `pdf_layout.py`:
- Easy to maintain style consistency
- Single source of truth for dimensions
- Simplified parameter passing

### 3. Separation of Concerns
Each module has a single responsibility:
- `data_storage` - File I/O
- `pokeapi_client` - API communication
- `image_processor` - Image/font handling
- `pdf_renderer` - PDF rendering
- `pdf_layout` - Constants and styling

### 4. Parallel Processing
Image downloading uses parallel workers for performance:
- `PARALLEL_WORKERS` constant in `pdf_layout.py`
- Configurable batch processing
- Thread-safe operations

### 5. Multi-language Support
Language handling at multiple levels:
- Core languages: 7 built-in (PokéAPI)
- Enhanced languages: 2 additional (ES, IT enrichment)
- Font selection: Automatic based on language
- PDF rendering: All text translated and formatted correctly

## Testing & Validation

### Validation Performed
✅ All 9 generations supported
✅ All languages generate correctly
✅ Image processing pipeline verified
✅ PDF rendering tested
✅ Import structure validated
✅ No circular dependencies

### How to Test

```bash
# Test single generation, single language
python scripts/generate_pdf.py --language en --gen 1

# Test all generations
python scripts/generate_pdf.py --language en --gen all

# Test multi-language
python scripts/generate_pdf.py --language all --gen 1

# Test data fetching
python scripts/fetch_pokemon_from_pokeapi.py -g 1
```

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Fetch Gen 1 (151 Pokémon) | ~30-60s | API calls + image downloads |
| Generate Gen 1 PDF (4 cards/page) | ~10-15s | Image processing + rendering |
| Full pipeline (fetch + generate) | ~1-2min | All 9 gens, all languages |

## Future Improvements

1. **Caching**: Cache PokéAPI responses to speed up refetching
2. **Incremental updates**: Only fetch/generate changed generations
3. **Configuration files**: Move magic numbers to config files
4. **Database backend**: Optional SQLite for structured storage
5. **Web interface**: Flask/FastAPI wrapper for generation
6. **Async operations**: Full async/await support for I/O operations

## Troubleshooting

### Import Errors
- Ensure you're running scripts from `scripts/` directory
- Check Python path includes `scripts/` folder
- Verify `lib/` folder exists with all modules

### Missing Fonts
- CJK fonts must be installed on system
- Run `install_fonts()` from `image_processor`
- Set `UNICODE_FONT` path in `pdf_layout.py`

### Image Download Issues
- Check internet connection
- Verify image source URLs in `pdf_layout.py`
- Adjust `PARALLEL_WORKERS` if rate-limited

## Version History

### v1.0 - Initial Modularization
- Split monolithic 659-line script into 8 focused modules
- Created centralized `lib/` package structure
- Established clean import patterns
- Maintained 100% backward compatibility
