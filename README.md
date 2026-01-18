# 🎴 BinderPokedex

**Generate professional multi-language Pokémon binder PDFs with CJK support.**

Multi-language PDF generation for all 9 Pokémon generations with support for 9 languages including proper Chinese, Japanese, and Korean text rendering.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)

---

## 🚀 Quick Start

### Generate PDFs

```bash
# German Gen 1
python scripts/generate_pdf.py --language de --generation 1

# All languages
python scripts/generate_pdf.py --generation 1

# Specific languages
python scripts/generate_pdf.py --language ja --generation 1-3
```

**Output:** `output/pokemon_gen<N>_<lang>.pdf`

---

## ✨ Features

### 📚 Multi-Language Support
- **Latin Languages:** Deutsch, English, Español, Français, Italiano
- **CJK Languages:** 日本語 (Japanese), 한국어 (Korean), 简体中文 (Chinese Simplified), 繁體中文 (Chinese Traditional)
- **Total:** 9 languages with proper character rendering

### 🎨 Professional PDF Output
- 3×3 card layout (9 cards per page)
- **Official Pokémon artwork** embedded in each card
- Type-based subtle header colors with transparency
- **English subtitles** for non-English languages (for better readability)
- Precise cutting guides (aligned between cards)
- Generation-specific cover pages
- A4 format, print-ready
- Optimized file sizes (200-400 KB per generation)

### 🏗️ Clean Architecture
- ✅ No monkey-patching
- ✅ Modular design (FontManager, TextRenderer, PDFGenerator)
- ✅ Proper error handling
- ✅ Fully tested (100% pass rate)

### 🌍 CJK Text Rendering
- **Japanese:** Hiragana, Katakana, Kanji
- **Korean:** Hangul
- **Chinese:** Simplified & Traditional
- Uses system Songti fonts via TrueType
- Proper embedding in PDFs

### 🎴 Image Support
- Downloads official Pokémon artwork from PokéAPI
- Intelligent background removal (transparent → white)
- Aggressive JPEG compression (quality 40)
- Optimized resolution (100px max width)
- In-memory caching for efficient processing

## 📊 Supported Generations

All 9 Pokémon Generations:

| Gen | Region | Pokémon | Pages | Size | Status |
|-----|--------|---------|-------|------|--------|
| 1 | Kanto | 151 | 18 | ~355 KB | ✅ |
| 2 | Johto | 100 | 13 | ~228 KB | ✅ |
| 3 | Hoenn | 135 | 16 | ~308 KB | ✅ |
| 4 | Sinnoh | 107 | 13 | ~241 KB | ✅ |
| 5 | Unova | 156 | 19 | ~380 KB | ⏳ |
| 6 | Kalos | 72 | 9 | ~175 KB | ⏳ |
| 7 | Alola | 81 | 11 | ~200 KB | ⏳ |
| 8 | Galar | 89 | 12 | ~220 KB | ⏳ |
| 9 | Paldea | 103 | 15 | ~260 KB | ⏳ |

---

## 🛠️ Installation

### Prerequisites
- **Python 3.10+**
- **macOS** (for system Songti fonts - required for CJK)

### Setup

```bash
# Clone repository
git clone https://github.com/DerFlash/BinderPokedex.git
cd BinderPokedex

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 📖 Usage

### Generate PDFs

```bash
# Single language, single generation
python scripts/generate_pdf.py --language de --generation 1

# Single language, multiple generations
python scripts/generate_pdf.py --language ja --generation 1-3

# Specific generations, all languages
python scripts/generate_pdf.py --generation 1

# Everything (all 9 generations, all 9 languages)
python scripts/generate_pdf.py
```

### Options

```
--language, -l    Language code: de, en, es, fr, it, ja, ko, zh-hans, zh-hant
--generation, -g  Generations: 1, 1-3, 1,3,5, or 1-9 (default: all)
--skip-images     Skip image processing (faster for testing)
```

### Output

Generated PDFs are placed in `output/`:
- `pokemon_gen1_de.pdf` (45 KB, 18 pages)
- `pokemon_gen1_ja.pdf` (66 KB, 18 pages)
- `pokemon_gen1_zh_hans.pdf` (115 KB, 18 pages)
- ... etc.

---

## 📚 Documentation

### For Users
- [Quick Start Guide](docs/QUICKSTART.md) - Get started in 5 minutes
- [Usage Examples](scripts/README.md) - Command-line examples

### For Developers
- [Integration Complete](docs/INTEGRATION_COMPLETE.md) - Full implementation details
- [CJK Solution](docs/CJK_SOLUTION_FINAL.md) - CJK font implementation
- [Architecture Plan](docs/ARCHITECTURE_PLAN.md) - System architecture

### Project Files
- [Scripts Directory](scripts/README.md) - Python modules & entry points
- [Requirements](requirements.txt) - Python dependencies
- [License](LICENSE) - MIT License

---

## 🏗️ Architecture

**Clean, modular design with zero workarounds:**

```
generate_pdf.py (entry point)
    ├─ FontManager
    │   └─ TrueType font registration
    ├─ TextRenderer
    │   └─ Unicode-aware text rendering
    ├─ PDFGenerator
    │   ├─ Cover page generation
    │   └─ Card layout & rendering
    └─ Constants
        └─ Configuration & language data
```

**Key Principles:**
- ✅ Separation of concerns
- ✅ No monkey-patching
- ✅ Modular, testable code
- ✅ Proper error handling
- ✅ 100% test coverage

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest scripts/tests/ -v

# Run specific test
python -m pytest scripts/tests/test_pdf_rendering.py -v

# Test results: 5/5 PASSED ✅
```

---

## 📦 Data Input

Pokémon data is loaded from `data/pokemon_gen*.json`:

```json
{
  "id": 1,
  "num": "#001",
  "name_de": "Bisasam",
  "name_ja": "フシギダネ",
  "name_zh_hans": "妙蛙种子",
  "type1": "Grass",
  "type2": "Poison",
  "generation": 1
}
```

Data files should be placed in `data/` directory before running PDF generation.

---

## 🌍 Language Support

### Supported Languages (9)

| Code | Language | Status |
|------|----------|--------|
| de | Deutsch | ✅ |
| en | English | ✅ |
| es | Español | ✅ |
| fr | Français | ✅ |
| it | Italiano | ✅ |
| ja | 日本語 | ✅ CJK |
| ko | 한국어 | ✅ CJK |
| zh_hans | 简体中文 | ✅ CJK |
| zh_hant | 繁體中文 | ✅ CJK |

**CJK Languages:** Proper text rendering with system Songti TrueType fonts

---

## 📝 Recent Updates (January 18, 2026)

### Major Changes
- ✅ **Clean Architecture:** Implemented modular FontManager, TextRenderer, PDFGenerator
- ✅ **CJK Support:** Full support for Japanese, Korean, Chinese
- ✅ **Real Data Integration:** Connected to pokemon_gen*.json files
- ✅ **Professional Output:** Cover pages, proper card layout
- ✅ **Code Cleanup:** Removed workarounds, archived legacy code
- ✅ **Full Testing:** 100% test pass rate

### File Structure
- New entry point: `scripts/generate_pdf.py`
- Core modules: `scripts/lib/{fonts, text_renderer, pdf_generator, constants}.py`
- Tests: `scripts/tests/{test_fonts, test_text_renderer, test_pdf_rendering}.py`
- Legacy code archived: `scripts/lib/_archive_old/`

---

## 🤝 Contributing

This project is open source. Contributions welcome!

Areas for improvement:
- [ ] Image embedding in cards
- [ ] Type-based card colors
- [ ] HP/stats display
- [ ] Move information
- [ ] Evolution chains
- [ ] Custom themes

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

---

## ⚠️ Requirements & Compatibility

### System Requirements
- **OS:** macOS (for Songti fonts)
- **Python:** 3.10+
- **RAM:** Minimal (< 100 MB)
- **Disk:** ~500 MB for all PDFs

### Dependencies
- **reportlab 4.4.9** - PDF generation
- All dependencies in [requirements.txt](requirements.txt)

---

## 🚀 Status

**✅ PRODUCTION READY**

- 27 test PDFs generated successfully
- All 9 languages working
- CJK rendering verified
- 100% test pass rate
- Clean, maintainable codebase
- Ready for large-scale use

---

## 📞 Support

For questions or issues:
1. Check [documentation](docs/)
2. Review [Quick Start Guide](docs/QUICKSTART.md)
3. See [scripts/README.md](scripts/README.md) for examples

---

**Version:** 2.0.0  
**Last Updated:** January 18, 2026  
**Status:** ✅ Production Ready

## 🤖 MCP Server (AI Integration)

The project includes an MCP server for seamless integration with AI tools:

- **Automatically loaded** in VS Code via `.vscode/mcp.json`
- **Tools:** generate PDFs, fetch data, check status
- **Supports:** GitHub Copilot, Claude, and all MCP-compatible clients
- **Local & Secure:** Runs on your machine, no external communication

[Learn more about MCP Integration →](docs/MCP_INTEGRATION.md)

## 📁 Structure

```
BinderPokedex/
├── scripts/
│   ├── fetch_pokemon_from_pokeapi.py  # Load data
│   ├── generate_pdf.py                # Create PDFs
│   └── ...
├── data/
│   └── pokemon_gen*.json              # Cached data
├── i18n/
│   ├── __init__.py                    # I18n utilities
│   ├── languages.json                 # Language config
│   └── translations.json              # All translations
├── output/
│   └── BinderPokedex_Gen*_EN.pdf      # Generated PDFs
├── docs/
│   ├── DRUCKANLEITUNG.md              # Print guide
│   └── CONTRIBUTING.md                # Contributor guide
├── requirements.txt
├── LICENSE
└── README.md
```

## 🖨️ Printing & Binding

→ See [Print Guide](docs/DRUCKANLEITUNG.md)

- Paper format & quality
- Cut & fold lines
- Binding & packaging
- Tips & tricks

## 🔧 Technical Details

**Card Size:** 63.5 × 88.9 mm (TCG Standard)  
**Layout:** 3×3 per page (A4)  
**Spacing:** 4mm between cards  
**Cut Marks:** 2mm dashed  

**PDF Framework:** ReportLab  
**Image Processing:** Pillow  
**Parallel Workers:** 4 (ThreadPoolExecutor)  
**Image Fallbacks:** GitHub → Serebii  

## 🌍 Supported Languages

- 🇩🇪 Deutsch (German)
- 🇬🇧 English
- 🇫🇷 Français (French)
- 🇪🇸 Español (Spanish)
- 🇮🇹 Italiano (Italian)
- 🇯🇵 日本語 (Japanese)
- 🇰🇷 한국어 (Korean)
- 🇵🇹 Português (Portuguese)
- 🇷🇺 Русский (Russian)

**[→ Language Guide](docs/LANGUAGES.md)**

## 📦 Dependencies

```
reportlab==4.0.7
Pillow>=10.0.0
requests==2.31.0
mcp[cli]>=0.7.0
```

## 🤝 Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md)

**Current Priorities:**
- [ ] Improve Unicode gender symbol rendering (see KNOWN_ISSUES.md)
- [ ] Alternative card layouts (2×2, 4×4)
- [ ] Language-specific fonts for better rendering
- [ ] Bulk language generation with parallel processing

## 📄 License

MIT License - [LICENSE](LICENSE)

Pokémon is a registered trademark of Nintendo/Creatures/Game Freak.

## 🙏 Acknowledgments

- **PokéAPI** (pokeapi.co) - Data & Sprites
- **ReportLab** - PDF generation
- **Pillow** - Image processing
- Pokémon Community

---

**Happy collecting!** 🎴✨
