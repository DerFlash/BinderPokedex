# 🎯 Usage Guide

Quick reference for generating BinderPokedex PDFs.

## Basic Usage

### Single Language PDFs

```bash
# German (default)
python scripts/generate_pdf.py --language de

# Specific language and generation
python scripts/generate_pdf.py --language de --generation 1
```

### Supported Languages

```bash
python scripts/generate_pdf.py --language de    # Deutsch
python scripts/generate_pdf.py --language en    # English
python scripts/generate_pdf.py --language fr    # Français
python scripts/generate_pdf.py --language es    # Español
python scripts/generate_pdf.py --language it    # Italiano
python scripts/generate_pdf.py --language ja    # 日本語
python scripts/generate_pdf.py --language ko    # 한국어
python scripts/generate_pdf.py --language zh-s  # 简体中文
python scripts/generate_pdf.py --language zh-t  # 繁體中文
```

## 🌍 Advanced: All Languages

### Generate All Languages At Once

```bash
python scripts/generate_pdf.py --language all
```

This creates **81 PDF files** (9 languages × 9 generations).

**Features:**
- Automatic image download & caching from PokéAPI
- Progressive compression (100px width, quality 40 JPEG)
- Type-based header colors with subtle transparency
- English subtitles on non-English language cards for context
- Aligned cutting guides for precise card cutting

**File Sizes:** 200-400 KB per PDF (Generation-dependent)
**Expected Duration:** 10-15 minutes (with image caching)

### Background Execution

Run in background and monitor:

```bash
# Start generation
nohup python scripts/generate_pdf.py --language all > pdf_all.log 2>&1 &

# Monitor progress
tail -f pdf_all.log

# Check status
ls -lh output/*.pdf | wc -l    # Count generated PDFs
du -sh output/                  # Total size
```

### Parallel Execution (Manual)

Generate multiple languages in parallel:

```bash
# Terminal 1: German
python scripts/generate_pdf.py --language de &

# Terminal 2: French
python scripts/generate_pdf.py --language fr &

# Terminal 3: Japanese
python scripts/generate_pdf.py --language ja &

# Wait for all to complete
wait
```

## Output Files

PDFs are saved to `output/` with naming:
```
BinderPokedex_Gen{1-9}_{LANGUAGE}.pdf
```

### File Sizes (Approximate)

| Generation | Pokémon | Gen 1 Size | File Size Pattern |
|------------|---------|-----------|-------------------|
| 1 | 151 | 25 MB | Largest |
| 2 | 100 | 15 MB | Small |
| 3 | 135 | 21 MB | Large |
| 4 | 107 | 16 MB | Small-Medium |
| 5 | 156 | 23 MB | Large |
| 6 | 72 | 10 MB | Small |
| 7 | 88 | 11 MB | Small |
| 8 | 96 | 10 MB | Small |
| 9 | 120 | 15 MB | Small-Medium |

**Total for all languages:** ~1.1 TB (if you generate all 81 files)

## Examples

### Scenario 1: Print only English Gen 1

```bash
python scripts/generate_pdf.py --language en
# Use: output/BinderPokedex_Gen1_EN.pdf
```

### Scenario 2: Print German & French binders

```bash
# Terminal 1
python scripts/generate_pdf.py --language de &
# Terminal 2  
python scripts/generate_pdf.py --language fr &
wait

# Check results
ls output/*_{DE,FR}.pdf
```

### Scenario 3: Full multilingual collection

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

