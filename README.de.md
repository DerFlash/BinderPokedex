# 🎴 BinderPokedex

**Vervollständige dein Pokédex... ein druckbares Blatt nach dem anderen!** 📋✨

Drucke 1.025+ Pokémon über 9 Generationen in 9 Sprachen. Alle Varianten, alle Formen, alles startklar. Einfach laden, drucken und sammeln starten.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
![v6.0](https://img.shields.io/badge/Version-v6.0-green.svg)

---

## 🎨 Vorschau

![BinderPokedex Preview](docs/images/binderdex-preview.png)

---

## 📥 Fertige PDFs Herunterladen

### Für normale Nutzer - einfach laden & drucken!


**Aktuelle Version (v6.0):** [Alle 117 PDFs](https://github.com/DerFlash/BinderPokedex/releases/tag/v6.0) ✨ *Major: Image Cache Redesign, mehrsprachige Formen-Unterstützung, umfassende Dokumentation*

**Nach Sprache (v6.0):** 🇩🇪 [DE](https://github.com/DerFlash/BinderPokedex/releases/download/v6.0/binder-pokedex-de.zip) | 🇬🇧 [EN](https://github.com/DerFlash/BinderPokedex/releases/download/v6.0/binder-pokedex-en.zip) | 🇫🇷 [FR](https://github.com/DerFlash/BinderPokedex/releases/download/v6.0/binder-pokedex-fr.zip) | 🇪🇸 [ES](https://github.com/DerFlash/BinderPokedex/releases/download/v6.0/binder-pokedex-es.zip) | 🇮🇹 [IT](https://github.com/DerFlash/BinderPokedex/releases/download/v6.0/binder-pokedex-it.zip) | 🇯🇵 [JA](https://github.com/DerFlash/BinderPokedex/releases/download/v6.0/binder-pokedex-ja.zip) | 🇰🇷 [KO](https://github.com/DerFlash/BinderPokedex/releases/download/v6.0/binder-pokedex-ko.zip) | 🇨🇳 [ZH](https://github.com/DerFlash/BinderPokedex/releases/download/v6.0/binder-pokedex-zh_hans.zip) | 🇹🇼 [ZH-T](https://github.com/DerFlash/BinderPokedex/releases/download/v6.0/binder-pokedex-zh_hant.zip)
---

## 📝 Neu in v6.0

**Major Release - Architektur & Pipeline Redesign** (Januar 2026)

Komplettes Data-Fetcher Redesign mit modularer Pipeline, Image-Cache Überarbeitung zur Vermeidung von Form-Varianten-Kollisionen, und mehrsprachige Formen-Suffix Beibehaltung (X/Y/Primal) für alle 9 Sprachen.

📄 **[Vollständige Release Notes & Changelog](CHANGELOG.md)**

---

## ✨ Hauptfeatures

- **9 Sprachen** 🌍 mit vollständiger CJK-Unterstützung (Japanisch, Koreanisch, Chinesisch)
- **1.025+ Pokémon** über alle 9 Generationen (Kanto → Paldea) im National Pokédex
- **Offizielle Artwork** von PokéAPI und TCGdex - authentische Bilder aus Spielen und TCG
- **3×3 Kartenlayout** (9 pro Seite) - perfekt für Standard-Binderblätter
- **Generations- und Varianten-Cover** mit wunderschönem mehrsprachigem Design und lokalisierten Logos
- **TCG-EX Varianten-Kollektionen** ✨ 
  - ExGen1: Klassische ex-Karten aus der Rubin/Saphir-Ära (2003-2007)
  - ExGen2: Pokémon-EX aus Black & White und XY-Serien (2012-2016)
  - ExGen3: Moderne ex-Karten aus Karmesin & Purpur (2023+)
- **Strukturierte PDFs** mit thematischen Trennern und Featured-Pokémon-Headern
- **Modulare Pipeline** zum Daten-Fetching mit scope-basierter Konfiguration
- **Druckfertig A4** - einfach laden, drucken und binden! 📎

---

## 📚 Dokumentation

| Thema | Link |
|-------|------|
| **Verwendung & Beispiele** | [docs/USAGE.de.md](docs/USAGE.de.md) |
| **Features & Technik** | [docs/FEATURES.md](docs/FEATURES.md) |
| **Installationsanleitung** | [docs/INSTALLATION.md](docs/INSTALLATION.md) |
| **Druckanleitungen** | [docs/PRINTING_GUIDE.de.md](docs/PRINTING_GUIDE.de.md) |
| **Architektur** | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| **Data Fetcher** | [docs/DATA_FETCHER.md](docs/DATA_FETCHER.md) |
| **Image Cache** | [docs/IMAGE_CACHE.md](docs/IMAGE_CACHE.md) |
| **MCP Integration** | [docs/MCP_INTEGRATION.md](docs/MCP_INTEGRATION.md) |
| **Mitwirken** | [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) |

---

## � Für Entwickler

### PDFs selbst generieren

```bash
# Clone & Setup
git clone https://github.com/DerFlash/BinderPokedex.git
cd BinderPokedex
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Verfügbare Scopes anzeigen
ls config/scopes/*.yaml

# Daten für einen Scope holen
python scripts/fetcher/fetch.py --scope Pokedex

# PDFs generieren
python scripts/pdf/generate_pdf.py --language de --scope Pokedex
```

---

## ⚖️ Rechtlicher Hinweis

**Dies ist ein Fan-Projekt ohne kommerzielle Absichten.** Pokémon, Pokédex und alle zugehörigen Marken sind Eigentum von The Pokémon Company, Nintendo und GameFreak.

✅ **Erlaubt:** Persönliche Nutzung, Bildungszwecke, private Sammlungen  
❌ **Verboten:** Kommerzielle Nutzung, Verkauf von PDFs oder gedruckten Materialien, gewinnorientierte Weiterverbreitung

Vollständige Details siehe [LICENSE](LICENSE).

---

## �🙏 Danksagung & Quellen

Dieses Projekt verdankt seinen Erfolg diesen fantastischen Ressourcen und Personen:

- **[PokéAPI](https://pokeapi.co/)** 📊 - Das Rückgrat unseres Pokémon-Wissens
- **[Bulbapedia](https://bulbapedia.bulbagarden.net/)** 📚 - Das Pokémon-Fan-Wiki, das uns nie im Stich lässt
- **[The Pokémon Company](https://www.pokemon.com/)** 🎮 - Für 30 Jahre Traum-Erfüllung
- **ReportLab** 🎨 - Für die Umwandlung von Daten in wunderschöne PDFs ohne Stress
- **Python Community** 🐍 - Für das großartige Ökosystem und endlose Unterstützung
- **GitHub Copilot** 🦆 - Für Rubber-Ducking und dafür, dass er meine Gedanken manchmal vor mir kennt 😄
