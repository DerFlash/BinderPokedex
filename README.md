# 🎴 BinderPokedex

**Generate multilingual Pokémon placeholder collection cards (Pokédex-style) for your binder.**

All 9 generations, all 9 languages: 81 ready-to-print PDFs with 1,025 Pokémon.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![v2.0](https://img.shields.io/badge/version-v2.0-green.svg)](https://github.com/DerFlash/BinderPokedex/releases/tag/v2.0)

---

## 🎨 Preview

![BinderPokedex Preview](docs/images/binderdex-preview.png)

---

## 📥 Download Ready-Made PDFs

### For End Users - Just Download & Print!

**All 81 PDFs (v2.0):** [All-in-One (12 MB)](https://github.com/DerFlash/BinderPokedex/releases/download/v2.0/binderpokedex-v2.0-all-pdfs.tar.gz)

**By Language:**
🇩🇪 [Deutsch](https://github.com/DerFlash/BinderPokedex/releases/download/v2.0/binderpokedex-v2.0-de.zip) |
🇬🇧 [English](https://github.com/DerFlash/BinderPokedex/releases/download/v2.0/binderpokedex-v2.0-en.zip) |
🇫🇷 [Français](https://github.com/DerFlash/BinderPokedex/releases/download/v2.0/binderpokedex-v2.0-fr.zip) |
🇪🇸 [Español](https://github.com/DerFlash/BinderPokedex/releases/download/v2.0/binderpokedex-v2.0-es.zip) |
🇮🇹 [Italiano](https://github.com/DerFlash/BinderPokedex/releases/download/v2.0/binderpokedex-v2.0-it.zip) |
🇯🇵 [日本語](https://github.com/DerFlash/BinderPokedex/releases/download/v2.0/binderpokedex-v2.0-ja.zip) |
🇰🇷 [한국어](https://github.com/DerFlash/BinderPokedex/releases/download/v2.0/binderpokedex-v2.0-ko.zip) |
🇨🇳 [简体中文](https://github.com/DerFlash/BinderPokedex/releases/download/v2.0/binderpokedex-v2.0-zh_hans.zip) |
🇹🇼 [繁體中文](https://github.com/DerFlash/BinderPokedex/releases/download/v2.0/binderpokedex-v2.0-zh_hant.zip)

✅ Extract, open PDFs, print, and bind!

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
- **Languages:** 9 (DE, EN, FR, ES, IT, JA, KO, ZH, ZH-T)
- **Pokémon:** 1,025 total
- **PDFs:** 81 generated

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

---

## ✨ Key Features

- **9 Languages** with proper CJK support (Japanese, Korean, Chinese)
- **Official Pokémon artwork** from PokéAPI
- **3×3 card layout** (9 per page)
- **Generation cover pages**
- **English subtitles** on non-English cards
- **Print-ready** A4 format
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

**Ready to create your Pokémon binder?** [Download now](https://github.com/DerFlash/BinderPokedex/releases/tag/v2.0) or [build it yourself](docs/INSTALLATION.md)! 🎉
