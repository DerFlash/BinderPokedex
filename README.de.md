# 🎴 BinderPokedex

Generiere **Pokémon-Platzhalter-Karten** (Pokédex-Stil) in 9 Sprachen!

Alle 9 Generationen + EX Varianten, alle 9 Sprachen: 117 druckfertige PDFs mit 1.025+ Pokémon.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![v3.0](https://img.shields.io/badge/Version-v3.0-green.svg)](https://github.com/DerFlash/BinderPokedex/releases/tag/v3.0)

---

## 🎨 Vorschau

![BinderPokedex Preview](docs/images/binderdex-preview.png)

---

## 📥 Fertige PDFs Herunterladen

### Für normale Nutzer - einfach laden & drucken!

**Aktuelle Version (v3.0):** [Alle 117 PDFs](https://github.com/DerFlash/BinderPokedex/releases/tag/v3.0) ✨ *Mit EX Varianten + CJK-Fixes + Live-Progress*

**Nach Sprache (v3.0):** 🇩🇪 [DE](https://github.com/DerFlash/BinderPokedex/releases/download/v3.0/binder-pokedex-de.zip) | 🇬🇧 [EN](https://github.com/DerFlash/BinderPokedex/releases/download/v3.0/binder-pokedex-en.zip) | 🇫🇷 [FR](https://github.com/DerFlash/BinderPokedex/releases/download/v3.0/binder-pokedex-fr.zip) | 🇪🇸 [ES](https://github.com/DerFlash/BinderPokedex/releases/download/v3.0/binder-pokedex-es.zip) | 🇮🇹 [IT](https://github.com/DerFlash/BinderPokedex/releases/download/v3.0/binder-pokedex-it.zip) | 🇯🇵 [JA](https://github.com/DerFlash/BinderPokedex/releases/download/v3.0/binder-pokedex-ja.zip) | 🇰🇷 [KO](https://github.com/DerFlash/BinderPokedex/releases/download/v3.0/binder-pokedex-ko.zip) | 🇨🇳 [ZH](https://github.com/DerFlash/BinderPokedex/releases/download/v3.0/binder-pokedex-zh_hans.zip) | 🇹🇼 [ZH-T](https://github.com/DerFlash/BinderPokedex/releases/download/v3.0/binder-pokedex-zh_hant.zip)

✅ Entpacken, öffnen, drucken!

---

## 🚀 Für Entwickler

### PDFs selbst generieren

```bash
# Clone & Setup
git clone https://github.com/DerFlash/BinderPokedex.git
cd BinderPokedex
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# PDFs generieren
python scripts/generate_pdf.py --language de --generation 1
```

### Abdeckung

- **Generationen:** Alle 9 (Kanto → Paldea)
- **Varianten:** EX-Serie (Gen1, Gen2, Gen3) + Mega Evolution
- **Sprachen:** 9 (DE, EN, FR, ES, IT, JA, KO, ZH, ZH-T)
- **Pokémon:** 1.025+ insgesamt inkl. Varianten
- **PDFs:** 117 generiert (81 Generationen + 36 Varianten)

---

## 📚 Dokumentation

| Thema | Link |
|-------|------|
| **Verwendung & Beispiele** | [docs/USAGE.de.md](docs/USAGE.de.md) |
| **Features & Technik** | [docs/FEATURES.md](docs/FEATURES.md) |
| **Installationsanleitung** | [docs/INSTALLATION.md](docs/INSTALLATION.md) |
| **Druckanleitungen** | [docs/PRINTING_GUIDE.de.md](docs/PRINTING_GUIDE.de.md) |
| **Architektur** | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |

---

## ✨ Hauptfeatures

- **9 Sprachen** mit CJK-Unterstützung
- **Offizielle Pokémon-Grafiken** von PokéAPI
- **3×3 Kartenlayout** (9 pro Seite)
- **Generations-Deckblätter**
- **Druckerfreundlich** A4-Format
- **Modulare Architektur**
- **Vollständig getestet**

---

## 📋 Unterstützte Generationen

| Gen | Region | Pokémon |
|-----|--------|---------|
| 1-9 | Kanto bis Paldea | 1.025 |

---

**Bereit, deinen Pokémon-Binder zu erstellen?** [Jetzt herunterladen](https://github.com/DerFlash/BinderPokedex/releases/tag/v2.0) oder [selbst bauen](docs/INSTALLATION.md)! 🎉
