# 🎴 BinderPokedex

**Complete your Pokédex... one printable sheet at a time!** 📋✨

Print 1,025+ Pokémon across 9 generations in 9 languages. All variants, all forms, all ready to go. Just download, print, and start collecting.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![v4.1](https://img.shields.io/badge/version-v4.1-green.svg)](https://github.com/DerFlash/BinderPokedex/releases/tag/v4.1)

---

## 🎨 Preview

![BinderPokedex Preview](docs/images/binderdex-preview.png)

---

## 📥 Download Ready-Made PDFs

### For End Users - Just Download & Print!

**Latest (v4.1):** [All 117 PDFs](https://github.com/DerFlash/BinderPokedex/releases/tag/v4.1) ✨ *Unified logging + clean output + verbose mode*

**By Language (v4.1):**
🇩🇪 [Deutsch](https://github.com/DerFlash/BinderPokedex/releases/download/v4.1/binder-pokedex-de.zip) |
🇬🇧 [English](https://github.com/DerFlash/BinderPokedex/releases/download/v4.1/binder-pokedex-en.zip) |
🇫🇷 [Français](https://github.com/DerFlash/BinderPokedex/releases/download/v4.1/binder-pokedex-fr.zip) |
🇪🇸 [Español](https://github.com/DerFlash/BinderPokedex/releases/download/v4.1/binder-pokedex-es.zip) |
🇮🇹 [Italiano](https://github.com/DerFlash/BinderPokedex/releases/download/v4.1/binder-pokedex-it.zip) |
🇯🇵 [日本語](https://github.com/DerFlash/BinderPokedex/releases/download/v4.1/binder-pokedex-ja.zip) |
🇰🇷 [한국어](https://github.com/DerFlash/BinderPokedex/releases/download/v4.1/binder-pokedex-ko.zip) |
🇨🇳 [简体中文](https://github.com/DerFlash/BinderPokedex/releases/download/v4.1/binder-pokedex-zh_hans.zip) |
🇹🇼 [繁體中文](https://github.com/DerFlash/BinderPokedex/releases/download/v4.1/binder-pokedex-zh_hant.zip)

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

- **9 Languages** 🌍 with proper CJK support (Japanese, Korean, Chinese)
- **1,025+ Pokémon** across all 9 generations (Kanto → Paldea) ready to collect
- **Official artwork** from PokéAPI - every card gets the real deal
- **3×3 card layout** (9 per page) - perfect for binder sheets
- **Generation cover pages** with beautiful multilingual design
- **EX Variant Collections** ✨ 
  - EX Gen1: 119 Pokémon with retro flair
  - EX Gen2: 72 Pokémon + Mega Evolution forms
  - EX Gen3: 82 Pokémon + Tera types
  - Classic Mega Evolution: All 76 Pokémon with mega forms
- **Sectioned PDFs** with themed dividers and featured Pokémon headers
- **Print-ready A4** - just download, print, and bind! 📎
- **Fully tested** and production-ready

---


## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🙏 Credits & Acknowledgments

This project couldn't exist without these amazing resources and people:

- **[PokéAPI](https://pokeapi.co/)** 📊 - The backbone of our Pokémon knowledge
- **[Bulbapedia](https://bulbapedia.bulbagarden.net/)** 📚 - The Pokémon fan wiki that never lets us down
- **[The Pokémon Company](https://www.pokemon.com/)** 🎮 - For keeping the dream alive for 30 years
- **ReportLab** 🎨 - For turning data into gorgeous PDFs without breaking a sweat
- **Python Community** 🐍 - For the incredible ecosystem and endless support
- **GitHub Copilot** 🦆 - For rubber-ducking and occasionally knowing what I want before I do 😄
