#!/bin/bash
# GitHub Release Setup für BinderPokedex v1.0

set -e

echo "════════════════════════════════════════════════════════"
echo "🚀 BinderPokedex - GitHub Release v1.0 Setup"
echo "════════════════════════════════════════════════════════"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# 1. Git initialisieren
echo ""
echo "📍 Schritt 1: Git Repository initialisieren..."
git init
git config user.email "dev@example.com"  # ANPASSEN!
git config user.name "BinderPokedex"

# 2. Alle Dateien adden
echo "📍 Schritt 2: Dateien zum Index hinzufügen..."
git add .

# 3. Initial Commit
echo "📍 Schritt 3: Initial Commit..."
git commit -m "🎉 Initial Release: BinderPokedex v1.0

- ✅ Multi-Generation Support (Gen 1-8, 1025 Pokémon)
- ✅ Professionelle PDFs mit Deckblättern
- ✅ PokéAPI Integration
- ✅ Deutsche Lokalisierung
- ✅ Parallele Bildverarbeitung
- ✅ 8 vollständige PDF-Generationen
- ✅ Ausführliche Dokumentation"

# 4. Tag für Release erstellen
echo "📍 Schritt 4: Release v1.0 Tag erstellen..."
git tag -a v1.0 -m "BinderPokedex v1.0 - Multi-Generation PDF Generator

## Features
- 8 Pokémon-Generationen (1025 Pokémon)
- Professionelle PDF-Generierung mit Deckblättern
- PokéAPI Integration mit Caching
- Deutsche & englische Namen
- Parallele Bildverarbeitung mit Fallback-Quellen
- Detaillierte Dokumentation & Benutzerhandbuch

## Downloads
- 8 generierte PDFs (~1.67 MB gesamt)
- Sofort druckbar (A4, 3×3 Kartenlayout)

## Installation
\`\`\`bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_pdf.py
\`\`\`

Siehe README.md für Details."

# 5. Status anzeigen
echo ""
echo "✅ Git Repository vorbereitet!"
echo ""
echo "════════════════════════════════════════════════════════"
echo "📝 NÄCHSTE SCHRITTE auf GitHub:"
echo "════════════════════════════════════════════════════════"
echo ""
echo "1️⃣ Erstelle ein neues Repository auf GitHub:"
echo "   → https://github.com/new"
echo "   → Name: BinderPokedex"
echo "   → Beschreibung: Pokémon Card Binder Generator"
echo ""
echo "2️⃣ Füge Remote hinzu und pushe:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/BinderPokedex.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo "   git push origin v1.0"
echo ""
echo "3️⃣ Erstelle Release auf GitHub:"
echo "   → https://github.com/YOUR_USERNAME/BinderPokedex/releases/new"
echo "   → Tag: v1.0"
echo "   → Title: BinderPokedex v1.0"
echo "   → Lade PDFs aus output/ hoch"
echo ""
echo "════════════════════════════════════════════════════════"
echo "💡 TIPPS:"
echo "════════════════════════════════════════════════════════"
echo ""
echo "✏️ Ersetze YOUR_USERNAME mit deinem GitHub-Benutzernamen"
echo "✏️ Stelle sicher, dass git global konfiguriert ist:"
echo "   git config --global user.email 'email@example.com'"
echo "   git config --global user.name 'Your Name'"
echo ""
echo "📚 Dokumentation:"
echo "   - README.md: Hauptdokumentation"
echo "   - PROJEKTPLAN.md: Technische Details"
echo "   - docs/DRUCKANLEITUNG.md: Druck-Guide"
echo "   - docs/CONTRIBUTING.md: Developer-Guide"
echo ""
echo "🎉 Viel Erfolg beim Release!"
echo "════════════════════════════════════════════════════════"
