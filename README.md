# 🎴 BinderPokedex

Generiere professionelle **Pokémon-Kartensammlungen** als druckbare PDFs - für alle 9 Generationen mit farbigen Deckblättern!

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)

## 🎯 Features

✨ **Multi-Generation Support**
- Alle 9 Pokémon-Generationen (Kanto bis Paldea)
- 1000+ Pokémon mit offiziellen Sprites
- PokéAPI Integration mit automatischem Caching

📄 **Professionelle PDFs**
- 3×3 Kartenlayout (9 pro Seite)
- Generationsspezifisches Deckblatt mit Branding
- Gestrichelte Schnittlinien für Zuschnitt
- Deutsche & englische Namen
- A4-Format, druckeroptimiert

⚡ **Optimiert**
- Parallele Bildverarbeitung (4 Worker)
- Automatische Fallback-Quellen
- Detaillierte Progress-Updates
- Generiert alle 8 Generationen in ~2 Minuten

## 📊 Generationen-Übersicht

| Gen | Region | Pokémon | PDF-Seiten | Status |
|-----|--------|---------|-----------|--------|
| 1 | Kanto | 151 | 18 | ✅ |
| 2 | Johto | 100 | 13 | ✅ |
| 3 | Hoenn | 135 | 16 | ✅ |
| 4 | Sinnoh | 107 | 13 | ✅ |
| 5 | Unova | 156 | 19 | ✅ |
| 6 | Kalos | 72 | 9 | ✅ |
| 7 | Alola | 88 | 11 | ✅ |
| 8 | Galar | 96 | 12 | ✅ |

**Gesamt: 1025 Pokémon**

## 🚀 Quick Start

### Installation

```bash
# Repository klonen
cd BinderPokedex

# Virtual Environment
python3 -m venv .venv
source .venv/bin/activate  # Mac/Linux
# oder: .venv\Scripts\activate  # Windows

# Dependencies
pip install -r requirements.txt
```

### Verwendung

```bash
# Generiere alle PDFs
python scripts/generate_pdf.py

# Oder nur eine Generation
python scripts/fetch_pokemon_from_pokeapi.py 1  # Gen 1 fetchen
python scripts/generate_pdf.py                   # PDF generieren
```

**Output:** `output/BinderPokedex_Gen*.pdf`

## 📁 Struktur

```
BinderPokedex/
├── scripts/
│   ├── fetch_pokemon_from_pokeapi.py  # Daten laden
│   ├── generate_pdf.py                # PDFs erstellen
│   └── ...
├── data/
│   └── pokemon_gen*.json              # Gekachte Daten
├── output/
│   └── BinderPokedex_Gen*.pdf         # Generierte PDFs
├── docs/
│   ├── DRUCKANLEITUNG.md              # Druck-Guide
│   └── CONTRIBUTING.md                # Contributor-Guide
├── requirements.txt
├── LICENSE
└── README.md
```

## 🖨️ Druck & Bindung

→ Siehe [DRUCKANLEITUNG.md](docs/DRUCKANLEITUNG.md)

- Papierformat & Qualität
- Schnitt- & Falzlinien
- Bindung & Verpackung
- Tipps & Tricks

## 🔧 Technische Details

**Kartengröße:** 63.5 × 88.9 mm (TCG Standard)  
**Layout:** 3×3 pro Seite (A4)  
**Spacing:** 4mm zwischen Karten  
**Schnittmarken:** 2mm gestrichelt  

**PDF-Framework:** ReportLab  
**Bildverarbeitung:** Pillow  
**Parallele Worker:** 4 (ThreadPoolExecutor)  
**Bild-Fallbacks:** GitHub → Serebii  

## 📦 Dependencies

```
reportlab==4.0.7
Pillow==10.1.0
requests==2.31.0
```

## 🤝 Beitragen

Siehe [CONTRIBUTING.md](docs/CONTRIBUTING.md)

Ideen:
- [ ] Gen 9+ Support
- [ ] Alternative Layouts (2×2, 4×4)
- [ ] Shiny-Versionen
- [ ] Web-Interface

## 📄 Lizenz

MIT License - [LICENSE](LICENSE)

Pokémon ist eine eingetragene Marke von Nintendo/Creatures/Game Freak.

## 🙏 Danksagungen

- **PokéAPI** (pokeapi.co) - Daten & Sprites
- **ReportLab** - PDF-Generierung
- **Pillow** - Bildverarbeitung
- Pokémon Community

---

**Viel Spaß beim Sammeln!** 🎴✨
