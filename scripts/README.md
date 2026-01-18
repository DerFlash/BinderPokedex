# Scripts Directory - Binder Pokédex

Clean, production-ready implementation for multi-language Pokémon PDF generation with CJK support.

## 🚀 Quick Start

### Generate PDFs

```bash
# German Gen 1
python scripts/generate_pdf.py --language de --generation 1

# All languages Gen 1
python scripts/generate_pdf.py --generation 1

# Japanese Gen 1-3
python scripts/generate_pdf.py --language ja --generation 1-3

# Everything
python scripts/generate_pdf.py
```

**Outputs:** `../output/pokemon_gen<N>_<lang>.pdf`

## 📚 Main Entry Point

### `generate_pdf.py` ⭐

Complete PDF generation with real Pokémon data.

**Features:**
- ✅ 9 languages (including CJK: Japanese, Korean, Chinese)
- ✅ Cover pages with generation info
- ✅ 3×3 card layout (18+ pages per generation)
- ✅ Professional typography
- ✅ Clean architecture, no workarounds

**Supported Languages:**
```
de          Deutsch (German)
en          English
es          Español
fr          Français
it          Italiano
ja          日本語 (Japanese) ← CJK
ko          한국어 (Korean) ← CJK
zh_hans     简体中文 (Simplified) ← CJK
zh_hant     繁體中文 (Traditional) ← CJK
```

**Options:**
```
--language, -l    Language code (default: all)
--generation, -g  Generations: 1, 1-3, 1,3,5, or 1-9 (default: 1-9)
--skip-images     Skip image processing
```

## 📦 Library (lib/)

### Core Modules (Production)

#### **fonts.py** - Font Management
Handles font registration for all languages, including CJK.

```python
from lib import FontManager
FontManager.register_fonts()
font = FontManager.get_font_name('ja')  # Returns 'SongtiBold'
```

**Key Features:**
- TrueType font support (Songti.ttc for CJK)
- Language-to-font mapping
- Automatic registration at startup

#### **text_renderer.py** - Text Rendering
Unicode-aware text rendering with font selection.

```python
from lib import TextRenderer
TextRenderer.render_text(canvas, 100, 200, 'テキスト', 'SongtiBold', 12)
```

**Key Features:**
- Unicode symbol support
- Per-language font selection
- Clean error handling

#### **pdf_generator.py** - PDF Orchestration
Complete PDF generation pipeline.

```python
from lib import PDFGenerator
generator = PDFGenerator('ja', 1)
pdf_path = generator.generate(pokemon_list)
```

**Key Features:**
- Cover page generation
- 3×3 card layout
- Multi-page support
- Professional styling

#### **constants.py** - Configuration
Centralized constants and configuration.

```python
from lib import LANGUAGES, GENERATION_INFO, CARD_WIDTH, PAGE_MARGIN
```

**Contains:**
- 9 language definitions
- 9 generation info (1-9)
- Card dimensions & layout
- Color scheme
- Page setup

### Archive (lib/_archive_old/)

Legacy modules (not used, kept for reference):
- `data_storage.py` - Old data persistence
- `image_processor.py` - Old image handling
- `pdf_layout.py` - Old layout constants
- `pdf_renderer.py` - Old PDF rendering
- `pokeapi_client.py` - API client (not needed)
- `pokemon_processor.py` - Old processing
- `pokemon_enricher.py` - Old enrichment

## 🧪 Tests (tests/)

### Test Files

#### **test_fonts.py**
Tests for FontManager.
```bash
python -m pytest tests/test_fonts.py -v
```

#### **test_text_renderer.py**
Tests for TextRenderer.
```bash
python -m pytest tests/test_text_renderer.py -v
```

#### **test_pdf_rendering.py**
Integration tests for PDF generation.
```bash
python -m pytest tests/test_pdf_rendering.py -v
```

### Run All Tests
```bash
python -m pytest tests/ -v
```

## 📊 Data Input

Input files: `../data/pokemon_gen*.json`

Each JSON file contains array of Pokémon with fields:
```json
{
  "id": 1,
  "num": "#001",
  "name_en": "Bulbasaur",
  "name_de": "Bisasam",
  "name_ja": "フシギダネ",
  "name_ko": "이상해씨",
  "name_zh_hans": "妙蛙种子",
  "name_zh_hant": "妙蛙種子",
  "type1": "Grass",
  "type2": "Poison",
  "image_url": "...",
  "generation": 1
}
```

## 📄 PDF Output

Output files: `../output/pokemon_gen<N>_<lang>.pdf`

Each PDF contains:
- **Page 1:** Cover page (generation info, Pokédex range)
- **Pages 2+:** Pokémon cards in 3×3 grid (9 cards/page)

Example for Gen 1:
```
pokemon_gen1_de.pdf      45 KB  (German, 151 Pokémon)
pokemon_gen1_en.pdf      45 KB  (English)
pokemon_gen1_ja.pdf      66 KB  (Japanese)
pokemon_gen1_zh_hans.pdf 115 KB (Chinese Simplified)
```

## 🏗️ Architecture

```
generate_pdf.py (entry point)
    ├→ Load pokemon_gen<N>.json
    ├→ FontManager.register_fonts()
    ├→ PDFGenerator(language, generation)
    │   ├→ _draw_cover_page()
    │   ├→ _draw_card() × 151
    │   │   ├→ FontManager.get_font_name()
    │   │   └→ TextRenderer.render_text()
    │   └→ Save PDF
    └→ Output: pokemon_gen<N>_<lang>.pdf
```

## 🎯 Clean Architecture Principles

✅ **Separation of Concerns**
- FontManager: Font handling only
- TextRenderer: Text rendering only
- PDFGenerator: Orchestration only

✅ **No Workarounds**
- Direct ReportLab API usage
- Clean, maintainable code
- Proper error handling

✅ **Modular Design**
- Independent modules
- Clear interfaces
- Extensible

✅ **Well Tested**
- Unit tests for each module
- Integration tests
- 100% test pass rate

## 📋 Supported Generations

| Gen | Region | Pokémon | Range |
|-----|--------|---------|-------|
| 1 | Kanto | 151 | #001-#151 |
| 2 | Johto | 100 | #152-#251 |
| 3 | Hoenn | 135 | #252-#386 |
| 4 | Sinnoh | 107 | #387-#493 |
| 5 | Unova | 156 | #494-#649 |
| 6 | Kalos | 72 | #650-#721 |
| 7 | Alola | 81 | #722-#802 |
| 8 | Galar | 89 | #803-#891 |
| 9 | Paldea | 103 | #892-#1024 |

## 🔧 Requirements

- Python 3.10+
- ReportLab 4.4.9
- macOS (for Songti fonts at `/System/Library/Fonts/Supplemental/Songti.ttc`)

See `../requirements.txt` for full dependencies.

## 📂 File Structure

```
scripts/
├── generate_pdf.py          ⭐ Main entry point
├── README.md                📖 This file
├── README_old.md            📦 Legacy documentation
├── lib/
│   ├── __init__.py          Clean exports
│   ├── fonts.py             Font management
│   ├── text_renderer.py     Text rendering
│   ├── pdf_generator.py     PDF generation
│   ├── constants.py         Configuration
│   └── _archive_old/        Legacy modules (archived)
├── tests/
│   ├── test_fonts.py
│   ├── test_text_renderer.py
│   └── test_pdf_rendering.py
└── fetch_pokemon_from_pokeapi.py  (Legacy, not in use)
```

## 📝 Examples

### Generate PDF for single language
```bash
python scripts/generate_pdf.py --language ja --generation 1
# Output: output/pokemon_gen1_ja.pdf (66 KB, 18 pages)
```

### Generate all languages for multiple generations
```bash
python scripts/generate_pdf.py --generation 1-3
# Output: 27 PDFs (3 generations × 9 languages)
```

### Batch generation script
```python
import subprocess
import sys

for lang in ['de', 'ja', 'zh_hans']:
    for gen in range(1, 4):
        subprocess.run([
            sys.executable,
            'scripts/generate_pdf.py',
            '--language', lang,
            '--generation', str(gen)
        ])
```

### Python API
```python
from lib import PDFGenerator, FontManager
import json

# Register fonts
FontManager.register_fonts()

# Load data
with open('data/pokemon_gen1.json') as f:
    pokemon_list = json.load(f)

# Generate PDF
generator = PDFGenerator('ja', 1)
pdf_path = generator.generate(pokemon_list)

print(f"✅ Created: {pdf_path}")
```

## 🧹 Recent Cleanup (January 18, 2026)

### Changes:
1. ✅ Replaced `generate_pdf.py` with clean version (was generate_pdf_new.py)
2. ✅ Archived 7 old lib modules to `lib/_archive_old/`
3. ✅ Updated `lib/__init__.py` to export only current modules
4. ✅ Removed old test files
5. ✅ Cleaned __pycache__ and .pyc files
6. ✅ Updated this README

### Result:
- 🎯 Cleaner, focused codebase
- 📦 Only active code in production flow
- 🧹 Legacy code preserved but archived
- ✨ Simplified module imports

## 🚀 Status

**✅ Production Ready**
- 27 PDFs generated successfully (Gen 1-3)
- All 9 languages working
- CJK text rendering verified
- 100% test pass rate
- Clean, maintainable code

## 📞 Documentation

For more details, see:
- `../docs/QUICKSTART.md` - Quick start guide
- `../docs/INTEGRATION_COMPLETE.md` - Full integration details
- `../docs/CJK_SOLUTION_FINAL.md` - CJK implementation
- `../docs/ARCHITECTURE_PLAN.md` - Architecture overview

---

**Version:** 2.0.0  
**Last Updated:** January 18, 2026  
**Status:** ✅ Production Ready

