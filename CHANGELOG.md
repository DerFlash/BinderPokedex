# Changelog

All notable changes to BinderPokedex are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [7.1.0] - 2026-02-03

### 🐛 Bug Fixes

**TCG Images Fixed**
- **Critical Fix:** Fixed missing Pokémon images in all TCG sets
- Resolved pipeline architecture flaw in `fix_missing_dex_ids` step
- All Pokémon cards now display correct artwork in generated PDFs
- Regenerated all 225 PDFs with complete images

### 🔧 Technical Details
- Made `fix_missing_dex_ids` step consistent with pipeline architecture
- Now uses `context.data['tcg_set_source']` instead of file I/O
- `source_path` parameter is now optional (only for debugging/caching)
- Updated ME02.5.yaml config to remove redundant `source_path` parameter
- 26 files updated with fixed pipeline and regenerated data

### Impact
**All TCG Sets** now show Pokémon artwork correctly in PDFs (previously only trainer/energy cards had images)

---

## [7.0.0] - 2026-02-02

### 🎯 Major Changes

**Complete TCG Support & Scope System**
- **25 Scopes Total:** National Pokédex + 24 TCG sets
  - 3 EX Generation sets (ExGen1, ExGen2, ExGen3)
  - 21 Modern TCG sets (ME01, ME02, ME02.5, MEP, SV01-SV10, SVP)
- All Scarlet & Violet TCG sets (SV01-SV10 + special sets)
- Paldea Era support (ME01, ME02, ME02.5, MEP)
- Auto-discovery system with batch generation
- Logo validation with automatic fallback
- Multilingual TCG metadata (up to 9 languages)

**System Improvements**
- Scope-based configuration for flexible data fetching
- Extended Pokemon image cache (1025+ Pokemon)
- Type translation enrichment system
- Batch PDF generation with `--scope all`
- Improved pipeline error handling and validation

**PDF Generation**
- 225 total PDFs across all scopes and languages
- Per-language ZIP archives for easy distribution
- Optimized file sizes and generation speed

### 📊 Statistics
- **Pokémon Coverage:** 1,025 Pokémon (all 9 generations)
- **TCG Sets:** 24 complete sets with multilingual support
- **Languages:** 9 (DE, EN, FR, ES, IT, JA, KO, ZH-Hans, ZH-Hant)
- **Total PDFs:** 225 (9 for Pokedex + EX sets, 5 for most TCG sets)

### 🔧 Technical Details
- Enhanced scope system with YAML configuration
- TCGdex API integration for all modern sets
- Automatic dexId fixing for trainer-owned and special Pokémon
- Section-based data format for TCG sets
- Logo embedding with fallback handling

---

## [6.0.0] - 2026-01-30

### 🎯 Major Changes
- **Complete Data Fetcher Redesign** - New modular pipeline architecture
  - Step-based processing with clear separation of concerns
  - Context-driven data flow between pipeline steps
  - Scope-based configuration (Pokedex, ExGen1, ExGen2, ExGen3, ME01)
  - Comprehensive documentation: DATA_FETCHER.md

- **TCG Set Support** - Complete TCGdex integration
  - Multilingual card names from TCGdex API (5 languages: DE, EN, FR, ES, IT)
  - Set logos embedded in PDFs with [image] tag support
  - Release dates in set descriptions with localized labels
  - New pipeline steps: fetch_tcgdex_set, enrich_tcg_names_multilingual, transform_to_sections_format
  - Example scope: ME01 (Miraidon ex Starter Deck)

- **URL Image Caching** - MD5-based external image caching
  - Temporary directory caching for logos and external images
  - MD5 hash of URL as cache key
  - ImageReader with mask='auto' for PNG transparency
  - New logo_renderer module for [image] tag parsing
  - Prevents duplicate downloads across PDF generation

- **Image Cache Redesign** - URL-based identifiers prevent collisions
  - New format: `pokemon_{id}_{url_identifier}_{size}.jpg`
  - Prevents collisions for form variants (Mega X/Y, Primal forms)
  - Unified caching between fetcher and PDF generator
  - Complete specification: IMAGE_CACHE.md

- **Multilingual Form Suffix Preservation** - X/Y/Primal suffixes across all 9 languages
  - Extract suffix from English name (e.g., " X", " Y", "-Primal")
  - Apply to all language translations automatically
  - Example: "Mega Glurak X" (German) instead of just "Mega Glurak"

- **Project Restructuring** - Clear separation of concerns
  - `scripts/fetcher/` - Data fetching and pipeline processing
  - `scripts/pdf/` - PDF generation and rendering
  - Removed obsolete configuration options

### 🐛 Fixes
- Fixed image cache collisions for form variants (Mega X/Y)
- Corrected ExGen3 featured Pokémon list (Mega section: 150→448)
- Removed obsolete `use_pokeapi_artwork` configuration
- Fixed Python syntax errors in docstrings (Unicode arrows, malformed strings)

### 🔧 Technical Details
- New pipeline engine with step-based processing
- Enhanced name enrichment preserving form suffixes
- GitHub Actions workflow fixes for automated releases
- Updated all scopes to use new pipeline architecture
- Logo rendering with inline image support
- MD5-based URL caching in temp directory

### 📚 Documentation
- Added `docs/DATA_FETCHER.md` - Pipeline architecture and usage
- Added `docs/IMAGE_CACHE.md` - Cache specification and design
- Updated `docs/ARCHITECTURE.md` - Overall project architecture
- Updated `docs/VARIANTS_ARCHITECTURE.md` - Variant system details
- Updated `docs/FEATURES.md` - TCG set features and URL caching
- Updated `README.md` - TCGdex integration and usage examples
- Comprehensive README updates with v6.0 information

### Impact
**Mega Charizard X** now displays correct image and name ("Mega Glurak X" in German, not just "Mega Glurak")
**TCG Sets** now have proper multilingual metadata with logos and release dates

### Migration from 5.0
1. Delete old cache: `rm -rf data/pokemon_images_cache/`
2. Re-fetch all data using new scopes:
   ```bash
   python scripts/fetcher/fetch.py --scope Pokedex
   python scripts/fetcher/fetch.py --scope ExGen1
   python scripts/fetcher/fetch.py --scope ExGen2
   python scripts/fetcher/fetch.py --scope ExGen3
   python scripts/fetcher/fetch.py --scope ME01
   ```
3. Generate PDFs with new paths:
   ```bash
   python scripts/pdf/generate_pdf.py --language de --scope Pokedex
   python scripts/pdf/generate_pdf.py --language de --scope ME01
   ```

---

## [5.0.0] - 2026-01-23

### 🐛 Bug Fixes

**CJK Font Rendering**
- Fixed font warnings and missing CJK characters in GitHub Actions
- Added Noto Sans CJK font installation for Linux environments
- Implemented automatic font fallback support
- Japanese, Korean, and Chinese characters now render properly in all PDFs

### 🔧 Technical Details

**Cross-Platform Font Support**
- macOS: Songti SC/TC (system fonts)
- Linux: Noto Sans CJK (auto-installed)
- Automatic font fallback detection
- Proper CJK character rendering in PDF generation

### 📊 Stats
- **Total PDFs:** 117 (81 generations + 36 variants)
- **Total Pokémon:** 1,025+ including variants
- **Languages:** 9 (DE, EN, FR, ES, IT, JA, KO, ZH, ZH-T)
- **Size per PDF:** 5-8 MB with embedded images

---

## [4.3.0] - 2026-01-30

### Fixed
- **Image Cache Collision Bug** - Mega Evolution forms (X/Y) and other variants now display correct images
  - Root cause: Cache used only `pokemon_{id}_{size}` format, causing collisions
  - Example: Charizard (ID 6) cache was shared between normal and Mega X/Y forms
  - Solution: Redesigned cache to use `pokemon_{id}_{url_identifier}_{size}` format
  - Impact: All 17 Mega variants in ExGen3 now show correct artwork
  
- **Form Suffix Preservation** - X/Y/Primal suffixes now appear correctly in all 9 languages
  - Root cause: Name enrichment step stripped form suffixes during translation
  - Example: "Mega Charizard X" became "Mega Glurak" (German) instead of "Mega Glurak X"
  - Solution: Extract suffix from English name, apply to all language translations
  - Impact: All form variants properly labeled in DE, EN, FR, ES, IT, JA, KO, ZH_HANS, ZH_HANT

- **ExGen3 Featured Pokémon** - Corrected Mega section featured list
  - Issue: Mewtwo (ID 150) was configured but doesn't exist in ExGen3 Mega section
  - Changed: 150 (Mewtwo) → 448 (Lucario)
  - Current: Charizard X (6), Gengar (94), Lucario (448)

### Changed
- **Code Cleanup** - Removed obsolete `use_pokeapi_artwork` configuration option
  - Reason: TCGdex images include card frames, unsuitable for binder layout
  - PokeAPI official artwork is now always used for all variants
  - Files updated: 3 YAML configs, 3 transform steps
  
- **Unified Caching Strategy** - Synchronized cache implementation across components
  - `cache_pokemon_images.py` (fetcher) and `pdf_generator.py` (PDF) use identical logic
  - Both extract URL identifiers the same way (PokeAPI IDs, TCGdex card IDs)
  - Ensures fetcher-cached images are properly found by PDF generator

### Technical Details

#### Image Cache Redesign
**Old Format:**
```
data/pokemon_images_cache/pokemon_6/default_thumb.jpg  # Collision!
```

**New Format:**
```
data/pokemon_images_cache/
  pokemon_6/
    6_thumb.jpg         # Normal Charizard
    10034_thumb.jpg     # Mega Charizard X
    10035_thumb.jpg     # Mega Charizard Y
```

**URL Identifier Extraction:**
- PokeAPI: `.../10034.png` → `"10034"` (Mega form ID)
- TCGdex: `.../sv1/013/high.webp` → `"sv1-013"` (card ID)

#### Name Enrichment Enhancement
```python
# Extract suffix from English name
english_name = "Charizard X"
base_name = "Charizard"
suffix = " X"  # Extracted

# Apply to all languages
german_translation = "Glurak"
final_german = german_translation + suffix  # "Glurak X"
```

**Affected Languages:** All 9 (de, en, fr, es, it, ja, ko, zh_hans, zh_hant)

### Documentation
- Added `docs/IMAGE_CACHE.md` - Complete cache architecture specification
- Updated `docs/ARCHITECTURE.md` - Added image cache section
- Updated `docs/DATA_FETCHER.md` - Removed obsolete artwork options
- Updated `docs/VARIANTS_ARCHITECTURE.md` - Updated variant counts and features
- Updated `docs/FEATURED_POKEMON.md` - Corrected ExGen3 featured list
- Updated `README.md` and `README.de.md` - Added v4.3 release notes

### Migration from 4.2
1. Delete old cache: `rm -rf data/pokemon_images_cache/`
2. Re-fetch all data: 
   ```bash
   python scripts/fetcher/fetch.py --scope Pokedex
   python scripts/fetcher/fetch.py --scope ExGen1
   python scripts/fetcher/fetch.py --scope ExGen2
   python scripts/fetcher/fetch.py --scope ExGen3
   ```
3. Regenerate PDFs as needed

**Data Size:** ~45 MB for 1,439 Pokémon entries (2,878 cache files)

---

## [4.2.0] - 2026-01-15

### Added
- **Comprehensive CJK Font Support** - WenQuanYi font integration
- **Enhanced Font Detection** - Fallback mechanisms for Noto and system fonts
- **Korean Rendering Improvements** - Using SongtiBold for better coverage

### Fixed
- Font path resolution for Ubuntu/Linux systems (OpenType fonts)
- ReportLab font warnings suppressed (expected behavior)
- PDF generation across all 9 languages in CI/CD environments

### Changed
- Consolidated font configuration with single source of truth
- Verified Japanese, Chinese, Korean PDF generation

**Result:** All 1,025+ Pokémon render correctly in all 9 languages

---

## [4.1.1] - 2026-01-10

### Added
- Fine dashed gray cutting guides for all PDFs
- Improved preview screenshot

### Fixed
- Minor rendering issues

---

## [4.1.0] - 2026-01-05

### Added
- Unified logging system with clean output
- Verbose mode for debugging
- Section-based featured Pokémon support

### Changed
- Improved typography and rendering quality
- Better error messages and progress indicators

---

## [4.0.0] - 2025-12-20

### Added
- **Variant Collections System** - Support for EX generations and Mega Evolution
- **Pipeline Architecture** - Modular fetch/transform/enrich/save system
- **Multi-Section Support** - Variants with different sections (normal/mega/primal)
- **Featured Pokémon** - Configurable featured Pokémon per section

### Changed
- Complete rewrite of data fetching system
- Unified data structure for Pokédex and variants
- New JSON schema for flexibility

### Documentation
- Added comprehensive architecture documentation
- Added variant system specification
- Added pipeline step documentation

---

## [3.x] - Legacy Versions

Earlier versions focused on basic Pokédex generation without variant support.
See git history for details.

---

## Version Numbering

**Format:** MAJOR.MINOR.PATCH

- **MAJOR:** Breaking changes, incompatible data formats
- **MINOR:** New features, backwards compatible
- **PATCH:** Bug fixes, documentation updates

**Current:** 4.3.0
- Major version 4: Current architecture with pipeline system
- Minor version 3: Image cache and name enrichment fixes
- Patch version 0: Initial release of this version
