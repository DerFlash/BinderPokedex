# 🎯 Bedienungsanleitung

Schnellreferenz für die Generierung von BinderPokedex-PDFs mit dem Scope-basierten System.

## 📦 Verfügbare Scopes

**25 Scopes insgesamt:**
- **Pokedex**: Kompletter National Pokédex (1025 Pokémon)
- **ExGen1-3**: TCG EX Varianten-Kollektionen (94/324/366 Karten)
- **ME01-MEP**: Pokémon TCG Karmesin & Purpur - Mew-Serie (4 Sets)
- **SV01-SVP**: Pokémon TCG Karmesin & Purpur Hauptserie (17 Sets)

Alle verfügbaren Scopes auflisten:
```bash
ls config/scopes/*.yaml
```

## Grundlegende Verwendung

### Ein Scope, eine Sprache

```bash
# Deutschen Pokedex generieren
python scripts/pdf/generate_pdf.py --scope Pokedex --language de

# Englisches TCG-Set generieren
python scripts/pdf/generate_pdf.py --scope ME01 --language en
```

### Ein Scope, alle Sprachen

`--language` weglassen, um alle 9 unterstützten Sprachen zu generieren:

```bash
# Pokedex in allen Sprachen generieren
python scripts/pdf/generate_pdf.py --scope Pokedex

# TCG-Set in allen Sprachen generieren
python scripts/pdf/generate_pdf.py --scope SV01
```

### Alle Scopes, alle Sprachen

`--scope all` verwenden, um alles zu generieren:

```bash
# Alle 25 Scopes in allen 9 Sprachen generieren
python scripts/pdf/generate_pdf.py --scope all
```

**Ausgabe:** ~225 PDFs (25 Scopes × 9 Sprachen, wo verfügbar)
**Dauer:** 10-20 Minuten (mit gecachten Daten)
**Größe:** ~377 MB gesamt

## Unterstützte Sprachen

```bash
de      # Deutsch
en      # English
fr      # Français
es      # Español
it      # Italiano
ja      # 日本語
ko      # 한국어
zh-hans # 简体中文
zh-hant # 繁體中文
```

**Hinweis:** Nicht alle TCG-Sets sind in allen Sprachen verfügbar. Der Generator überspringt nicht verfügbare Sprachen automatisch.

### Im Hintergrund ausführen und überwachen

```bash
# Generierung starten
nohup python scripts/generate_pdf.py --language all > pdf_all.log 2>&1 &

# Fortschritt verfolgen
tail -f pdf_all.log

# Status überprüfen
ls -lh output/*.pdf | wc -l    # Anzahl generierter PDFs
du -sh output/                  # Gesamtgröße
```

### Parallele Ausführung (Manuell)

Mehrere Sprachen gleichzeitig generieren:

```bash
# Terminal 1: Deutsch
python scripts/generate_pdf.py --language de &

# Terminal 2: Französisch
python scripts/generate_pdf.py --language fr &

# Terminal 3: Japanisch
python scripts/generate_pdf.py --language ja &

# Auf Abschluss aller warten
wait
```

## Ausgabedateien

PDFs werden in `output/` mit folgendem Muster gespeichert:
```
BinderPokedex_Gen{1-9}_{SPRACHE}.pdf
```

### Dateigröße (Ungefähre Werte)

| Generation | Pokémon | Gen 1 Größe | Dateigröße-Muster |
|------------|---------|-----------|-------------------|
| 1 | 151 | 25 MB | Größte |
| 2 | 100 | 15 MB | Klein |
| 3 | 135 | 21 MB | Groß |
| 4 | 107 | 16 MB | Klein-Mittel |
| 5 | 156 | 23 MB | Groß |
| 6 | 72 | 10 MB | Klein |
| 7 | 88 | 11 MB | Klein |
| 8 | 96 | 10 MB | Klein |
| 9 | 120 | 15 MB | Klein-Mittel |

**Gesamtgröße für alle Sprachen:** ~1,1 TB (wenn alle 81 Dateien generiert werden)

## 📝 Beispiele

### Beispiel 1: Kompletter Pokédex auf Deutsch

```bash
python scripts/fetcher/fetch.py --scope Pokedex
python scripts/pdf/generate_pdf.py --scope Pokedex --language de
# Ausgabe: output/de/Pokedex_DE.pdf (~60 MB)
```

### Beispiel 2: Alle TCG Mew-Sets auf Englisch

```bash
# Alle Mew-Sets fetchen
for scope in ME01 ME02 ME02.5 MEP; do
    python scripts/fetcher/fetch.py --scope $scope
done

# Englische PDFs generieren
for scope in ME01 ME02 ME02.5 MEP; do
    python scripts/pdf/generate_pdf.py --scope $scope --language en
done

# Ergebnisse prüfen
ls output/en/ME*.pdf
```

### Beispiel 3: Komplette Sammlung (Alle Scopes, alle Sprachen)

```bash
# Dies generiert alle 225 PDFs (~377 MB gesamt)
python scripts/pdf/generate_pdf.py --scope all

# Ergebnisse prüfen
for lang in de en fr es it ja ko zh-hans zh-hant; do
    echo "$lang: $(ls output/$lang/*.pdf 2>/dev/null | wc -l) PDFs"
done
```
# Alle Sprachen starten
python scripts/generate_pdf.py --language all

# Fertigstellung überwachen
watch 'ls -1 output/*.pdf | wc -l'
```

### Szenario 4: Fehlerhafte Sprache erneut generieren

Wenn eine Sprache während `--language all` fehlschlägt:

```bash
# Nur diese Sprache erneut generieren
python scripts/generate_pdf.py --language ja
```

## Performance-Tipps

1. **Andere Apps schließen** - Spart Speicher für parallele Verarbeitung
2. **Stabile Internetverbindung** - Schnellere Bilddownloads
3. **SSD-Speicher** - Schnelleres PDF-Schreiben (output/ Verzeichnis)
4. **Morgens generieren** - Zeitplan für Off-Peak-Zeiten bei Generierung aller Sprachen
5. **Speicherplatz überprüfen** - Mindestens 2 GB freier Speicher erforderlich

## Fehlerbehebung

### "Only X out of Y images processed"
- Normalerweise ein vorübergehendes Netzwerkproblem
- Befehl erneut ausführen (Bilder werden nach dem ersten Download zwischengespeichert)
- Internetverbindung überprüfen

### "Font not found" Fehler
- CJK-Fonts für asiatische Sprachen fehlen
- **macOS:** STHeiti-Schrift installieren
- **Linux:** `sudo apt install fonts-noto-cjk`
- **Windows:** Von Google Fonts herunterladen und installieren

### Langsame Generierung
- Internetgeschwindigkeit überprüfen
- Andere Anwendungen schließen
- CPU-/Speicherauslastung überprüfen
- Zuerst eine einzelne Sprache versuchen

### Fehler bei Speicherplatz
- Alte PDFs löschen: `rm output/*.pdf`
- Speicherplatz freigeben
- Weniger Generationen auf einmal

## Fortgeschrittene Optionen

### Hilfetext anzeigen
```bash
python scripts/generate_pdf.py --help
```

### Alle Sprachen überwachen
```bash
# PDF-Anzahl wachsen sehen
watch 'ls output/*.pdf | wc -l'

# Dateigrößen überwachen
watch 'du -sh output/'

# Anzahl nach Sprache zählen
for lang in DE EN FR ES IT JA KO PT RU; do
  count=$(ls output/*_$lang.pdf 2>/dev/null | wc -l)
  echo "  $lang: $count"
done
```

## Umgebungsvariablen

Keine speziellen Umgebungsvariablen erforderlich.

Python Virtual Environment sollte aktiviert sein:
```bash
source .venv/bin/activate  # macOS/Linux
# oder
.venv\Scripts\activate      # Windows
```

## Unterstützte Python-Versionen

- Python 3.8+
- Python 3.9+
- Python 3.10+
- Python 3.11+ (empfohlen)
- Python 3.12+

Version überprüfen:
```bash
python --version
```

---

**[← Zurück zu README](../README.md)** | **[Script-Dokumentation](../scripts/README.md)**

