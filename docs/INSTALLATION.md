# 🛠️ Installation Guide

## Prerequisites

- **Python 3.10+** (3.11+ recommended)
- **macOS** (required for system fonts - CJK support)
- **Git**
- **~500 MB** disk space (with dependencies)
- **Internet connection** (first run only)

## Quick Start (5 minutes)

### 1. Clone Repository

```bash
git clone https://github.com/DerFlash/BinderPokedex.git
cd BinderPokedex
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Generate PDFs

```bash
python scripts/generate_pdf.py --language de --generation 1
```

**Output:** PDFs saved to `output/pokemon_gen1_de.pdf`

---

## Detailed Setup

### Check Python Version

```bash
python3 --version
# Should output: Python 3.10.x or higher
```

### Virtual Environment

**Why?** Isolates project dependencies from system Python.

```bash
# Create
python3 -m venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Verify (should show .venv prefix)
which python
```

### Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install from requirements
pip install -r requirements.txt

# Verify installation
python -c "import reportlab; print(reportlab.Version)"
```

### Verify Installation

```bash
# Check all imports work
python -c "import reportlab, PIL, requests; print('✅ All dependencies installed')"

# Check fonts available
python scripts/lib/fonts.py
```

---

## Troubleshooting

### Python Version Too Old

**Error:** `python: command not found`

**Solution:**
```bash
# Use Python 3 explicitly
python3 -m venv .venv
python3 -m pip install -r requirements.txt
```

### Virtual Environment Not Activated

**Symptom:** `python: command not found` or dependencies missing

**Solution:**
```bash
source .venv/bin/activate
# Verify with: which python (should show .venv path)
```

### Missing System Fonts (CJK Languages)

**Error:** `CJK languages won't render properly`

**Solution:** Install system fonts

```bash
# macOS
# Songti.ttc should already be installed
# If missing, download from: http://support.apple.com/downloads/

# Verify fonts
ls /Library/Fonts/Songti.ttc
ls /System/Library/Fonts/AppleGothic.ttf
```

### Permission Denied

**Error:** `Permission denied` when activating venv

**Solution:**
```bash
chmod +x .venv/bin/activate
source .venv/bin/activate
```

### Pip Installation Fails

**Error:** `ERROR: Could not install packages...`

**Solution:**
```bash
# Clear pip cache
pip cache purge

# Try again
pip install -r requirements.txt
```

### OutOfMemory Error

**Error:** `MemoryError` during PDF generation

**Solution:**
```bash
# Generate one generation at a time
python scripts/generate_pdf.py --generation 1
python scripts/generate_pdf.py --generation 2
# ... etc
```

---

## Configuration

### Python Path Issues

If you have multiple Python versions:

```bash
# Use explicit path
/usr/local/bin/python3 -m venv .venv
```

### Pip Issues

If pip is slow or times out:

```bash
pip install --default-timeout=1000 -r requirements.txt
```

---

## Next Steps

- **Generate PDFs:** See [Usage Guide](USAGE.md)
- **Printing Tips:** See [Printing Guide](PRINTING_GUIDE.md)
- **Development:** See [Architecture](ARCHITECTURE.md)

---

## System Information

### Verified On

- macOS 13.x, 14.x, 15.x
- Python 3.10, 3.11, 3.12
- Intel & Apple Silicon (M1/M2/M3)

### Known Limitations

- **macOS only** - CJK fonts required (Windows/Linux fonts differ)
- **Python 3.10+** - Older versions not supported
- **Internet connection** - Required for first PDF generation (API calls)

---

Need help? Check [KNOWN_ISSUES.md](../KNOWN_ISSUES.md) or open an [issue](https://github.com/DerFlash/BinderPokedex/issues).
