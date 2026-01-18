# 🎯 Bedienungsanleitung

Schnellreferenz für die Generierung von BinderPokedex-PDFs.

## Grundlegende Verwendung

### PDFs für eine Sprache

```bash
# Englisch (Standard)
python scripts/generate_pdf.py

# Mit expliziter Sprache
python scripts/generate_pdf.py --language en
python scripts/generate_pdf.py -l en
```

### Einzelne Sprachen

```bash
python scripts/generate_pdf.py --language de    # Deutsch
python scripts/generate_pdf.py --language fr    # Französisch
python scripts/generate_pdf.py --language es    # Spanisch
python scripts/generate_pdf.py --language it    # Italienisch
python scripts/generate_pdf.py --language ja    # Japanisch
python scripts/generate_pdf.py --language ko    # Koreanisch
python scripts/generate_pdf.py --language pt    # Portugiesisch
python scripts/generate_pdf.py --language ru    # Russisch
```

## 🌍 Fortgeschrittenes Thema: Alle Sprachen

### Alle Sprachen auf einmal generieren

```bash
python scripts/generate_pdf.py --language all
```

Dies erstellt **81 PDF-Dateien** (9 Sprachen × 9 Generationen):
- Englisch (EN): 9 PDFs
- Deutsch (DE): 9 PDFs
- Französisch (FR): 9 PDFs
- Spanisch (ES): 9 PDFs
- Italienisch (IT): 9 PDFs
- Japanisch (JA): 9 PDFs
- Koreanisch (KO): 9 PDFs
- Portugiesisch (PT): 9 PDFs
- Russisch (RU): 9 PDFs

**Erwartete Dauer:** 2-3 Stunden (je nach Internetverbindung)

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

## Beispiele

### Szenario 1: Nur englische Gen 1 drucken

```bash
python scripts/generate_pdf.py --language en
# Datei: output/BinderPokedex_Gen1_EN.pdf
```

### Szenario 2: Deutsche & französische Binder

```bash
# Terminal 1
python scripts/generate_pdf.py --language de &
# Terminal 2  
python scripts/generate_pdf.py --language fr &
wait

# Ergebnisse überprüfen
ls output/*_{DE,FR}.pdf
```

### Szenario 3: Komplette mehrsprachige Sammlung

```bash
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

