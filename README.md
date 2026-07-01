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


**Latest (v7.2):** [All 225 PDFs](https://github.com/DerFlash/BinderPokedex/releases/tag/v7.2) ✨ *New: Featured Elements on section covers!*

**By Language (v7.2):**
🇩🇪 [Deutsch](https://github.com/DerFlash/BinderPokedex/releases/download/v7.2/binder-pokedex-de.zip) |
🇬🇧 [English](https://github.com/DerFlash/BinderPokedex/releases/download/v7.2/binder-pokedex-en.zip) |
🇫🇷 [Français](https://github.com/DerFlash/BinderPokedex/releases/download/v7.2/binder-pokedex-fr.zip) |
🇪🇸 [Español](https://github.com/DerFlash/BinderPokedex/releases/download/v7.2/binder-pokedex-es.zip) |
🇮🇹 [Italiano](https://github.com/DerFlash/BinderPokedex/releases/download/v7.2/binder-pokedex-it.zip) |
🇯🇵 [日本語](https://github.com/DerFlash/BinderPokedex/releases/download/v7.2/binder-pokedex-ja.zip) |
🇰🇷 [한국어](https://github.com/DerFlash/BinderPokedex/releases/download/v7.2/binder-pokedex-ko.zip) |
🇨🇳 [简体中文](https://github.com/DerFlash/BinderPokedex/releases/download/v7.2/binder-pokedex-zh_hans.zip) |
🇹🇼 [繁體中文](https://github.com/DerFlash/BinderPokedex/releases/download/v7.2/binder-pokedex-zh_hant.zip)
---

## 📝 What's New

### v7.2 (February 2026)

**Featured Elements - Visual Highlights on Covers** 🎨

✨ **New Feature:**
- Beautiful featured elements (cards/artwork) on every section cover
- 3 most iconic Pokémon automatically selected per section
- Smart content detection:
  - TCG Sets: Trading card images from TCGdex
  - Pokédex: Official artwork from PokeAPI  
- Automatic fallback to PokeAPI when TCG images unavailable
- Priority-based selection (starters, legendaries, pseudo-legendaries)

🔧 **Technical:**
- Format-agnostic architecture with 3 card handlers
- Unified `featured_elements` data structure
- ~800KB-1MB cached images per element
- Works across all 25 scopes (Pokédex + 24 TCG sets)

### v7.1 (February 2026)

**Bug Fix Release - TCG Images**

🐛 **Critical Fix:**
- Fixed missing Pokemon images in all TCG sets
- Resolved pipeline architecture flaw in `fix_missing_dex_ids` step
- All Pokemon cards now display correct artwork in PDFs
- Regenerated all 225 PDFs with complete images

### v7.0 (February 2026)

**Major Release - Complete TCG Support & Scope System**

🎴 **25 Scopes Total:** National Pokédex + 24 TCG sets (3 EX generations + 21 modern sets)

**New TCG Features:**
- Complete support for all Scarlet & Violet TCG sets (SV01-SV10 + special sets)
- Paldea Era support (ME01, ME02, MEP)
- Auto-discovery system with batch generation
- Logo validation with automatic fallback
- Multilingual TCG metadata

**System Improvements:**
- Scope-based configuration for flexible data fetching
- Enhanced Pokemon image cache (1025+ Pokemon)
- Type translations enrichment system
- Batch PDF generation with `--scope all`

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
