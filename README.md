# 🎴 BinderPokedex

**Complete your Pokédex... one printable sheet at a time!** 📋✨

Print 1,025+ Pokémon across 9 generations in 9 languages. All variants, all forms, all ready to go. Just download, print, and start collecting.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
![v8.1](https://img.shields.io/badge/version-v8.1-green.svg)

---

## 🎨 Preview

![BinderPokedex Preview](docs/images/binderdex-preview.png)

---

## ✨ Key Features

- **9 Languages** 🌍 with proper CJK support (Japanese, Korean, Chinese)
- **1,025+ Pokémon** across all 9 generations (Kanto → Paldea) in National Pokédex
- **Official artwork** from PokéAPI and TCGdex - authentic images from games and TCG
- **3×3 card layout** (9 per page) - perfect for standard binder sheets
- **Generation & variant covers** with beautiful multilingual design and localized logos
- **Complete TCG Support** 🎴
  - **3 EX Generations:** ExGen1 (2003-2007), ExGen2 (2012-2016), ExGen3 (2023+)
  - **21 Modern Sets:** Full Scarlet & Violet era (SV01-SV10 + specials)
  - **Paldea Era:** ME01, ME02, ME02.5, MEP
  - Auto-discovery and batch generation
- **Scope-Based System** with 25 total scopes
- **Sectioned PDFs** with themed dividers and featured Pokémon headers
- **Modular pipeline** for data fetching with flexible configuration
- **Print-ready A4** - just download, print, and bind! 📎

---

## 📥 Download Ready-Made PDFs

### For End Users - Just Download & Print!


**Latest (v8.1):** [All 225 PDFs](https://github.com/DerFlash/BinderPokedex/releases/tag/v8.1.1) ✨ *New: SVG templates, full CJK fix, localized TCG energy types!*

**By Language (v8.1):**
🇩🇪 [Deutsch](https://github.com/DerFlash/BinderPokedex/releases/download/v8.1.1/binder-pokedex-de.zip) |
🇬🇧 [English](https://github.com/DerFlash/BinderPokedex/releases/download/v8.1.1/binder-pokedex-en.zip) |
🇫🇷 [Français](https://github.com/DerFlash/BinderPokedex/releases/download/v8.1.1/binder-pokedex-fr.zip) |
🇪🇸 [Español](https://github.com/DerFlash/BinderPokedex/releases/download/v8.1.1/binder-pokedex-es.zip) |
🇮🇹 [Italiano](https://github.com/DerFlash/BinderPokedex/releases/download/v8.1.1/binder-pokedex-it.zip) |
🇯🇵 [日本語](https://github.com/DerFlash/BinderPokedex/releases/download/v8.1.1/binder-pokedex-ja.zip) |
🇰🇷 [한국어](https://github.com/DerFlash/BinderPokedex/releases/download/v8.1.1/binder-pokedex-ko.zip) |
🇨🇳 [简体中文](https://github.com/DerFlash/BinderPokedex/releases/download/v8.1.1/binder-pokedex-zh_hans.zip) |
🇹🇼 [繁體中文](https://github.com/DerFlash/BinderPokedex/releases/download/v8.1.1/binder-pokedex-zh_hant.zip)
---

## 📝 What's New

### v8.1 (July 2026)

**CJK Font Fallback & TCG Type Translations** 🐛

🔧 **CJK Fix (Korean & Traditional Chinese):**
- Korean and Traditional Chinese PDFs were empty/broken on Linux/CI due to macOS-exclusive fonts (`AppleGothic`, `STHeitiMedium`) being unavailable
- `FontManager` now automatically falls back to WenQuanYi/Noto on Linux — all 9 languages generate complete PDFs

🌍 **TCG Energy Type Translations:**
- `Colorless`, `Darkness`, `Lightning`, and `Metal` are TCG-exclusive names not covered by PokéAPI — they were always displayed in English
- Now fully translated in all 9 languages (e.g. `Darkness` → `あく` / `Unlicht` / `Ténèbres`)

### v8.0 (July 2026)

**SVG WYSIWYG Template System & MEP Expansion** ✨

🎨 **SVG Template System:**
- Full SVG-based card, page, and cover templates — editable live in any SVG editor (Inkscape, Illustrator, etc.)
- Templates support inline logo embedding and automatic image placement
- New CLI parameters: `--card-template`, `--page-template`, `--cover-template`, `--list-templates`
- Backwards-compatible: existing renders are unchanged when no template flag is passed

📦 **MEP Bulbapedia Supplement:**
- MEP set expanded from 10 → 55 cards via Bulbapedia data supplement
- Covers all missing cards not available in TCGdex

🔧 **Technical:**
- CI: upgraded to Python 3.12 + pip caching for faster builds
- Preserved PNG transparency in image cache and all rendered PDFs
- Fixed TCG multilingual card name handling

📄 **[Full Release Notes & Changelog](CHANGELOG.md)**

---

## 📚 Documentation

| Topic | Link |
|-------|------|
| **Usage & Examples** | [docs/USAGE.md](docs/USAGE.md) |
| **Features & Tech** | [docs/FEATURES.md](docs/FEATURES.md) |
| **Featured Elements** | [docs/FEATURED_ELEMENTS.md](docs/FEATURED_ELEMENTS.md) |
| **Installation Guide** | [docs/INSTALLATION.md](docs/INSTALLATION.md) |
| **Printing Tips** | [docs/PRINTING_GUIDE.md](docs/PRINTING_GUIDE.md) |
| **Architecture** | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| **Data Fetcher** | [docs/DATA_FETCHER.md](docs/DATA_FETCHER.md) |
| **Image Cache** | [docs/IMAGE_CACHE.md](docs/IMAGE_CACHE.md) |
| **Contribution** | [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) |
| **Copilot Customization** | [docs/COPILOT_CUSTOMIZATION.md](docs/COPILOT_CUSTOMIZATION.md) |
| **Pokémon Variants** | [docs/VARIANTS_FEATURE_SUMMARY.md](docs/VARIANTS_FEATURE_SUMMARY.md) |
| **Variants Architecture** | [docs/VARIANTS_ARCHITECTURE.md](docs/VARIANTS_ARCHITECTURE.md) |
| **Variants Quickstart** | [docs/VARIANTS_QUICKSTART.md](docs/VARIANTS_QUICKSTART.md) |

---

## 🚀 For Developers

### Generate Your Own PDFs

```bash
# Clone & setup
git clone https://github.com/DerFlash/BinderPokedex.git
cd BinderPokedex
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# List available scopes (25 total: 1 Pokedex + 3 ExGen + 21 TCG sets)
ls config/scopes/*.yaml

# Fetch data for a scope
python scripts/fetcher/fetch.py --scope Pokedex

# Generate PDF for a specific language and scope
python scripts/pdf/generate_pdf.py --language de --scope Pokedex

# Generate all languages for a scope
python scripts/pdf/generate_pdf.py --scope ME01

# Generate all scopes in all languages
python scripts/pdf/generate_pdf.py --scope all
```

---

## ⚖️ Legal Notice

**This is a fan-made, non-commercial project.** Pokémon, Pokédex, and all related trademarks are the property of The Pokémon Company, Nintendo, and GameFreak.

✅ **Permitted:** Personal use, educational purposes, private collections  
❌ **Prohibited:** Commercial use, selling PDFs or printed materials, profit-driven redistribution

For full details, see [LICENSE](LICENSE).

---


## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🙏 Credits & Acknowledgments

This project couldn't exist without these amazing resources and people:

- **[PokéAPI](https://pokeapi.co/)** 📊 - The backbone of our Pokémon knowledge
- **[TCGdex](https://www.tcgdex.net/)** 🎴 - Comprehensive multilingual TCG card database
- **[Bulbapedia](https://bulbapedia.bulbagarden.net/)** 📚 - The Pokémon fan wiki that never lets us down
- **[The Pokémon Company](https://www.pokemon.com/)** 🎮 - For keeping the dream alive for 30 years
- **ReportLab** 🎨 - For turning data into gorgeous PDFs without breaking a sweat
- **Python Community** 🐍 - For the incredible ecosystem and endless support
- **GitHub Copilot** 🦆 - For rubber-ducking and occasionally knowing what I want before I do 😄
