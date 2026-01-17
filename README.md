# 🎴 BinderPokedex

Generiere professionelle **Pokémon-Platzhalter-Karten** als druckbare PDFs - für alle 9 Generationen mit farbigen Deckblättern zum Ausdrucken und Einfügen in deinen Binder!

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Ko-fi](https://img.shields.io/badge/Support-Ko--fi-FF5E5B.svg?logo=kofi)](https://ko-fi.com/derflash)

---

**💰 Gefällt dir BinderPokedex? Unterstütze die Entwicklung mit einem Trinkgeld!**

<a href='https://ko-fi.com/derflash' target='_blank'><img height='36' style='border:0px;height:36px;' src='https://storage.ko-fi.com/cdn/kofi6.png?v=6' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>

---

## 🎯 Features

✨ **Multi-Generation Support**
- Alle 9 Pokémon-Generationen (Kanto bis Paldea)
- 1000+ Pokémon mit offiziellen Sprites
- PokéAPI Integration mit automatischem Caching

📄 **Professionelle PDF-Vorlagen**
- 3×3 Platzhalter-Kartenlayout (9 pro Seite)
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

## 📸 Vorschau

![BinderPokedex Preview - Gen1 Deckblatt und Kartenseite](docs/images/binderdex-preview.png)

## 🚀 Quick Start

### Mit AI-Tools in VS Code (Empfohlen!) 🤖

```bash
git clone https://github.com/DerFlash/BinderPokedex.git
cd BinderPokedex
code .
```

Öffne **GitHub Copilot Chat** oder **Claude** und sag einfach:
```
"generiere PDF Binder für alle 8 Generationen"
```

Die KI nutzt automatisch die BinderPokedex-Tools! → [QUICKSTART_AI.md](QUICKSTART_AI.md)

### Klassisch mit Kommandozeile

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
# Generiere alle PDFs (mit automatischem Daten-Download bei Bedarf)
python scripts/generate_pdf.py

# Optional: Pokémon-Daten aktualisieren (falls manuell nötig)
python scripts/fetch_pokemon_from_pokeapi.py
```

**Output:** `output/BinderPokedex_Gen*.pdf`

## 🤖 MCP Server (AI Integration)

Das Projekt beinhaltet einen MCP-Server für nahtlose Integration mit AI-Tools:

- **Automatisch geladen** in VS Code via `.vscode/mcp.json`
- **Tools:** generiere PDFs, fetche Daten, überprüfe Status
- **Unterstützt:** GitHub Copilot, Claude, und alle MCP-kompatiblen Clients
- **Lokal & Sicher:** Läuft auf deinem Rechner, keine externe Kommunikation

[Mehr über MCP Integration →](docs/MCP_INTEGRATION.md)

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
Pillow>=10.0.0
requests==2.31.0
mcp[cli]>=0.7.0
```

## 🤝 Beitragen

Siehe [CONTRIBUTING.md](docs/CONTRIBUTING.md)

**Aktuelle Prioritäten:**
- [ ] Unicode-Geschlechtszeichen-Rendering verbessern (siehe KNOWN_ISSUES.md)
- [ ] Gen 9+ Support
- [ ] Alternative Kartenlayouts (2×2, 4×4)
- [ ] Mehrsprachige Unterstützung

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
