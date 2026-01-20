# 🎴 BinderPokedex

**Generate multilingual Pokémon placeholder collection cards (Pokédex-style) for your binder.**

All 9 generations + EX variants, all 9 languages: 117 ready-to-print PDFs with 1,025+ Pokémon.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![v4.0](https://img.shields.io/badge/version-v4.0-green.svg)](https://github.com/DerFlash/BinderPokedex/releases/tag/v4.0)

---

## 🎨 Preview

![BinderPokedex Preview](docs/images/binderdex-preview.png)

---

## 📥 Download Ready-Made PDFs

### For End Users - Just Download & Print!

**Latest (v4.0):** [All 117 PDFs](https://github.com/DerFlash/BinderPokedex/releases/tag/v4.0) ✨ *Section-based featured Pokémon + enhanced typography + unified rendering*

**By Language (v4.0):**
🇩🇪 [Deutsch](https://github.com/DerFlash/BinderPokedex/releases/download/v4.0/binder-pokedex-de.zip) |
🇬🇧 [English](https://github.com/DerFlash/BinderPokedex/releases/download/v4.0/binder-pokedex-en.zip) |
🇫🇷 [Français](https://github.com/DerFlash/BinderPokedex/releases/download/v4.0/binder-pokedex-fr.zip) |
🇪🇸 [Español](https://github.com/DerFlash/BinderPokedex/releases/download/v4.0/binder-pokedex-es.zip) |
🇮🇹 [Italiano](https://github.com/DerFlash/BinderPokedex/releases/download/v4.0/binder-pokedex-it.zip) |
🇯🇵 [日本語](https://github.com/DerFlash/BinderPokedex/releases/download/v4.0/binder-pokedex-ja.zip) |
🇰🇷 [한국어](https://github.com/DerFlash/BinderPokedex/releases/download/v4.0/binder-pokedex-ko.zip) |
🇨🇳 [简体中文](https://github.com/DerFlash/BinderPokedex/releases/download/v4.0/binder-pokedex-zh_hans.zip) |
🇹🇼 [繁體中文](https://github.com/DerFlash/BinderPokedex/releases/download/v4.0/binder-pokedex-zh_hant.zip)

✅ Extract, open PDFs, print, and bind!

---

## ⚖️ Legal Notice

**This is a fan-made, non-commercial project.** Pokémon, Pokédex, and all related trademarks are the property of The Pokémon Company, Nintendo, and GameFreak.

✅ **Permitted:** Personal use, educational purposes, private collections  
❌ **Prohibited:** Commercial use, selling PDFs or printed materials, profit-driven redistribution

For full details, see [LICENSE](LICENSE).

---

## 🚀 For Developers

### Generate Your Own PDFs

```bash
# Clone & setup
git clone https://github.com/DerFlash/BinderPokedex.git
cd BinderPokedex
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Generate PDFs
python scripts/generate_pdf.py --language de --generation 1
```

### Coverage

- **Generations:** All 9 (Kanto → Paldea)
- **Variants:** EX series (Gen1, Gen2, Gen3) + Mega Evolution
- **Languages:** 9 (DE, EN, FR, ES, IT, JA, KO, ZH, ZH-T)
- **Pokémon:** 1,025+ total including variants
- **PDFs:** 117 generated (81 generations + 36 variants)

---

## 📚 Documentation

| Topic | Link |
|-------|------|
| **Usage & Examples** | [docs/USAGE.md](docs/USAGE.md) |
| **Features & Tech** | [docs/FEATURES.md](docs/FEATURES.md) |
| **Installation Guide** | [docs/INSTALLATION.md](docs/INSTALLATION.md) |
| **Printing Tips** | [docs/PRINTING_GUIDE.md](docs/PRINTING_GUIDE.md) |
| **Architecture** | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| **Contribution** | [CONTRIBUTING.md](docs/CONTRIBUTING.md) |
| **🆕 Pokémon Variants Feature** | [docs/VARIANTS_FEATURE_SUMMARY.md](docs/VARIANTS_FEATURE_SUMMARY.md) |
| **🆕 Variants Technical Spec** | [docs/VARIANTS_TECHNICAL_SPEC.md](docs/VARIANTS_TECHNICAL_SPEC.md) |
| **🆕 Variants Research** | [docs/VARIANTS_RESEARCH.md](docs/VARIANTS_RESEARCH.md) |

---

## ✨ Key Features

- **9 Languages** with proper CJK support (Japanese, Korean, Chinese)
  - Fixed CJK type text rendering (no more black boxes!)
- **Official Pokémon artwork** from PokéAPI
- **3×3 card layout** (9 per page)
- **Generation cover pages** with multilingual footer text
- **EX Variant Series** ✨ NEW in v3.0
  - **EX Gen1:** 119 Pokémon-ex cards with special forms
  - **EX Gen2:** 72 Pokémon-EX cards with Mega Evolution support
  - **EX Gen3:** 82 Pokémon ex cards with Tera forms
  - **Mega Evolution:** 76 Pokémon with 79 mega forms
  - Logo rendering: M Pokémon, EX, EX New, EX Tera
- **Pokémon Variants Support** with sectioned PDFs
  - Dynamic form imagery (PokeAPI + Bulbapedia fallback)
  - Live progress bars during generation
- **English subtitles** on non-English cards
- **Print-ready** A4 format with cutting guides
- **Modular, clean architecture** (no workarounds)
- **Fully tested** (15 unit tests passing)

---

## 📋 Supported Generations

| Gen | Region | Pokémon |
|-----|--------|---------|
| 1 | Kanto | 151 |
| 2 | Johto | 100 |
| 3 | Hoenn | 135 |
| 4 | Sinnoh | 107 |
| 5 | Unova | 156 |
| 6 | Kalos | 72 |
| 7 | Alola | 88 |
| 8 | Galar | 96 |
| 9 | Paldea | 120 |

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

**Ready to create your Pokémon binder?** [Download now](https://github.com/DerFlash/BinderPokedex/releases/tag/v3.0) or [build it yourself](docs/INSTALLATION.md)! 🎉
