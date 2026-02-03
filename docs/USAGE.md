# 🎯 Usage Guide

Quick reference for generating BinderPokedex PDFs using the scope-based system.

## 📦 Available Scopes

**25 Total Scopes:**
- **Pokedex**: Complete National Pokédex (1025 Pokémon)
- **ExGen1-3**: TCG EX variant collections (94/324/366 cards)
- **ME01-MEP**: Pokémon TCG Scarlet & Violet - Mew series (4 sets)
- **SV01-SVP**: Pokémon TCG Scarlet & Violet main series (17 sets)

List all available scopes:
```bash
ls config/scopes/*.yaml
```

## Basic Usage

### Single Scope, Single Language

```bash
# Generate German Pokedex
python scripts/pdf/generate_pdf.py --scope Pokedex --language de

# Generate English TCG set
python scripts/pdf/generate_pdf.py --scope ME01 --language en
```

### Single Scope, All Languages

Omit `--language` to generate all 9 supported languages:

```bash
# Generate Pokedex in all languages
python scripts/pdf/generate_pdf.py --scope Pokedex

# Generate TCG set in all languages
python scripts/pdf/generate_pdf.py --scope SV01
```

### All Scopes, All Languages

Use `--scope all` to generate everything:

```bash
# Generate all 25 scopes in all 9 languages
python scripts/pdf/generate_pdf.py --scope all
```

**Output:** ~225 PDFs (25 scopes × 9 languages, where available)
**Duration:** 10-20 minutes (with cached data)
**Size:** ~377 MB total

## Supported Languages

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

**Note:** Not all TCG sets are available in all languages. The generator will skip unavailable languages automatically.

## 🔄 Data Fetching

Before generating PDFs, you need to fetch the data:

```bash
# Fetch single scope
python scripts/fetcher/fetch.py --scope Pokedex
python scripts/fetcher/fetch.py --scope ME01

# Fetch all scopes (takes ~5 minutes)
for scope in Pokedex ExGen1 ExGen2 ExGen3 ME01 ME02 ME02.5 MEP SV01 SV02 SV03 SV03.5 SV04 SV04.5 SV05 SV06 SV06.5 SV07 SV08 SV08.5 SV09 SV10 SV10.5B SV10.5W SVP; do
    python scripts/fetcher/fetch.py --scope $scope
done
```

## 💾 Output Files

PDFs are organized by language in subdirectories:
```
output/
  de/
    Pokedex_DE.pdf
    ME01_DE.pdf
    ...
  en/
    Pokedex_EN.pdf
    ME01_EN.pdf
    ...
  fr/
  ...
```

### File Sizes (Approximate)

| Scope | Type | Cards/Pokémon | Size per Language |
|-------|------|----------------|-------------------|
| Pokedex | Pokédex | 1025 | ~60 MB |
| ExGen1 | TCG | 94 | ~2 MB |
| ExGen2 | TCG | 324 | ~5 MB |
| ExGen3 | TCG | 366 | ~6 MB |
| ME01 | TCG | 165 | ~2 MB |
| SV01 | TCG | 198 | ~2.5 MB |

**Total for all scopes & languages:** ~377 MB

## 📝 Examples

### Example 1: Complete Pokédex in German

```bash
python scripts/fetcher/fetch.py --scope Pokedex
python scripts/pdf/generate_pdf.py --scope Pokedex --language de
# Output: output/de/Pokedex_DE.pdf (~60 MB)
```

### Example 2: All TCG Mew Sets in English

```bash
# Fetch all Mew sets
for scope in ME01 ME02 ME02.5 MEP; do
    python scripts/fetcher/fetch.py --scope $scope
done

# Generate English PDFs
for scope in ME01 ME02 ME02.5 MEP; do
    python scripts/pdf/generate_pdf.py --scope $scope --language en
done

# Check results
ls output/en/ME*.pdf
```

### Example 3: Complete Collection (All Scopes, All Languages)

```bash
# This generates all 225 PDFs (~377 MB total)
python scripts/pdf/generate_pdf.py --scope all

# Check results
for lang in de en fr es it ja ko zh-hans zh-hant; do
    echo "$lang: $(ls output/$lang/*.pdf 2>/dev/null | wc -l) PDFs"
done
```

```bash
# Start all languages
python scripts/generate_pdf.py --language all

# Monitor completion
watch 'ls -1 output/*.pdf | wc -l'
```

### Scenario 4: Rerun failed language

If a language fails during `--language all`:

```bash
# Rerun just that language
python scripts/generate_pdf.py --language ja
```

## Performance Tips

1. **Close other apps** - Frees up memory for parallel processing
2. **Stable internet** - Faster image downloads
3. **SSD storage** - Faster PDF writing (output/ directory)
4. **Morning run** - Schedule for off-peak hours if generating all languages
5. **Monitor space** - Ensure 2 GB free disk space

## Troubleshooting

### "Only X out of Y images processed"
- Usually temporary network issue
- Rerun the command (images are cached after first download)
- Check internet connection

### "Font not found" error
- Missing CJK fonts for Asian languages
- **macOS:** Install STHeiti font
- **Linux:** `sudo apt install fonts-noto-cjk`
- **Windows:** Download and install from Google Fonts

### Slow generation
- Check internet speed
- Close other applications
- Check CPU/memory usage
- Try running single language first

### Disk space error
- Delete old PDFs: `rm output/*.pdf`
- Free up disk space
- Reduce generations at once

## Advanced Options

### View help text
```bash
python scripts/generate_pdf.py --help
```

### Monitor all languages
```bash
# Watch PDF count grow
watch 'ls output/*.pdf | wc -l'

# Watch file sizes
watch 'du -sh output/'

# Count by language
for lang in DE EN FR ES IT JA KO PT RU; do
  count=$(ls output/*_$lang.pdf 2>/dev/null | wc -l)
  echo "  $lang: $count"
done
```

## Environment Variables

No special environment variables needed.

Python virtual environment should be activated:
```bash
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate      # Windows
```

## Supported Python Versions

- Python 3.8+
- Python 3.9+
- Python 3.10+
- Python 3.11+ (recommended)
- Python 3.12+

Check version:
```bash
python --version
```

---

**[← Back to README](../README.md)** | **[Scripts Documentation](../scripts/README.md)**

