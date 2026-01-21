# 🎴 BinderPokedex

**Vervollständige dein Pokédex... ein druckbares Blatt nach dem anderen!** 📋✨

Drucke 1.025+ Pokémon über 9 Generationen in 9 Sprachen. Alle Varianten, alle Formen, alles startklar. Einfach laden, drucken und sammeln starten.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
![v4.1.1](https://img.shields.io/badge/Version-v4.1.1-green.svg)

---

## 🎨 Vorschau

![BinderPokedex Preview](docs/images/binderdex-preview.png)

---

## 📥 Fertige PDFs Herunterladen

### Für normale Nutzer - einfach laden & drucken!


**Aktuelle Version (v4.1.1):** [Alle 117 PDFs](https://github.com/DerFlash/BinderPokedex/releases/tag/v4.1.1) ✨ *Hotfix: feine gestrichelte Schnittkanten, verbessertes Preview, enthält v4.1 Features*

**Nach Sprache (v4.1.1):** 🇩🇪 [DE](https://github.com/DerFlash/BinderPokedex/releases/download/v4.1.1/binder-pokedex-de.zip) | 🇬🇧 [EN](https://github.com/DerFlash/BinderPokedex/releases/download/v4.1.1/binder-pokedex-en.zip) | 🇫🇷 [FR](https://github.com/DerFlash/BinderPokedex/releases/download/v4.1.1/binder-pokedex-fr.zip) | 🇪🇸 [ES](https://github.com/DerFlash/BinderPokedex/releases/download/v4.1.1/binder-pokedex-es.zip) | 🇮🇹 [IT](https://github.com/DerFlash/BinderPokedex/releases/download/v4.1.1/binder-pokedex-it.zip) | 🇯🇵 [JA](https://github.com/DerFlash/BinderPokedex/releases/download/v4.1.1/binder-pokedex-ja.zip) | 🇰🇷 [KO](https://github.com/DerFlash/BinderPokedex/releases/download/v4.1.1/binder-pokedex-ko.zip) | 🇨🇳 [ZH](https://github.com/DerFlash/BinderPokedex/releases/download/v4.1.1/binder-pokedex-zh_hans.zip) | 🇹🇼 [ZH-T](https://github.com/DerFlash/BinderPokedex/releases/download/v4.1.1/binder-pokedex-zh_hant.zip)
---

## 📝 Release Notes

### v4.1.1 (Hotfix)
- Feine gestrichelte graue Schnittkanten für alle PDFs
- Verbesserter Preview Screenshot
- Enthält alle Features aus v4.1

### v4.1
- Vereinheitlichtes Logging, saubere Ausgabe, Verbose-Modus
- Sektionsbasierte Featured Pokémon
- Verbesserte Typografie und Rendering

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

- **9 Sprachen** 🌍 mit vollständiger CJK-Unterstützung (Japanisch, Koreanisch, Chinesisch)
- **1.025+ Pokémon** über alle 9 Generationen (Kanto → Paldea) ready zum Sammeln
- **Offizielle Artwork** von PokéAPI - jede Karte bekommt die echten Bilder
- **3×3 Kartenlayout** (9 pro Seite) - perfekt für Binderblätter
- **Generations-Deckblätter** mit wunderschönem mehrsprachigem Design
- **EX Varianten-Kollektionen** ✨ 
  - EX Gen1: 119 Pokémon mit Retro-Feeling
  - EX Gen2: 72 Pokémon + Mega Evolution Formen
  - EX Gen3: 82 Pokémon + Tera Typen
  - Klassische Mega Evolution: Alle 76 Pokémon mit Mega Formen
- **Strukturierte PDFs** mit thematischen Trennern und Featured-Pokémon-Headern
- **Druckfertig A4** - einfach laden, drucken und binden! 📎
- **Vollständig getestet** und produktionsreif

---

## 🙏 Danksagung & Quellen

Dieses Projekt verdankt seinen Erfolg diesen fantastischen Ressourcen und Personen:

- **[PokéAPI](https://pokeapi.co/)** 📊 - Das Rückgrat unseres Pokémon-Wissens
- **[Bulbapedia](https://bulbapedia.bulbagarden.net/)** 📚 - Das Pokémon-Fan-Wiki, das uns nie im Stich lässt
- **[The Pokémon Company](https://www.pokemon.com/)** 🎮 - Für 30 Jahre Traum-Erfüllung
- **ReportLab** 🎨 - Für die Umwandlung von Daten in wunderschöne PDFs ohne Stress
- **Python Community** 🐍 - Für das großartige Ökosystem und endlose Unterstützung
- **GitHub Copilot** 🦆 - Für Rubber-Ducking und dafür, dass er meine Gedanken manchmal vor mir kennt 😄
