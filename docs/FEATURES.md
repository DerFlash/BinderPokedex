# ✨ Features & Technical Details

## Language Support

### 9 Languages Supported

| Language | Code | Font | Type |
|----------|------|------|------|
| Deutsch | `de` | Helvetica | Latin |
| English | `en` | Helvetica | Latin |
| Español | `es` | Helvetica | Latin |
| Français | `fr` | Helvetica | Latin |
| Italiano | `it` | Helvetica | Latin |
| 日本語 | `ja` | Songti | CJK |
| 한국어 | `ko` | AppleGothic | CJK |
| 简体中文 | `zh_hans` | Songti | CJK |
| 繁體中文 | `zh_hant` | Songti | CJK |

### CJK Rendering

- **Proper text rendering** for Japanese (Hiragana, Katakana, Kanji)
- **Korean Hangul** support with TrueType fonts
- **Chinese** (Simplified & Traditional) with full Unicode support
- **Gender symbols** (♂/♀) working correctly in all languages
- **English subtitles** on non-English cards for readability

## PDF Features

### Layout
- **3×3 card grid** (9 cards per page)
- **Cover page** for each generation
- **A4 format** (210 × 297 mm)
- **Print-ready** with precise measurements
- **Type-based header colors** with transparency

### Content
- **Official Pokémon artwork** from PokéAPI
- **Species names** in target language
- **Type information** with type colors
- **National Pokédex number**
- **Height & weight** in metric units
- **Cutting guides** for easy card extraction

### Optimization
- **File sizes:** 200-400 KB per generation
- **Image compression:** JPEG quality 40
- **Image resolution:** 100px max width
- **In-memory caching:** Efficient batch processing

## Architecture

### Modular Design

```
scripts/lib/
├── __init__.py              # Package initialization
├── constants.py             # Language configs & URLs
├── fonts.py                 # Font management & registration
├── text_renderer.py         # Unicode-aware text rendering
├── pdf_generator.py         # Core PDF orchestration
├── pokeapi_client.py        # PokéAPI data fetching
├── pokemon_processor.py     # Data preprocessing
├── pokemon_enricher.py      # Language enrichment
└── data_storage.py          # File I/O & caching
```

### Key Principles

- ✅ **No monkey-patching** - Clean code without hacks
- ✅ **Proper error handling** - Graceful fallbacks
- ✅ **Type hints** - Better IDE support
- ✅ **Modular design** - Testable, reusable components
- ✅ **Separation of concerns** - Each module has clear responsibility

## Testing

### Test Coverage
- 15 unit tests
- 100% pass rate
- Tests for:
  - Font registration and availability
  - PDF rendering with CJK text
  - Text rendering with symbols
  - Image processing
  - Data enrichment

### Running Tests

```bash
python -m pytest scripts/tests/ -v
```

## Performance

### Generation Times

- **Gen 1 (151 Pokémon):** ~37 seconds
- **Gen 2 (100 Pokémon):** ~1m 7s
- **Gen 3-9 (774 Pokémon):** ~7m 47s
- **All 9 generations:** ~10 minutes
- **All 81 PDFs (9 gen × 9 lang):** ~1.5 hours

### Data Caching

- Pokémon data cached locally in JSON
- Cached data included in repository
- No API calls required after first fetch
- Reproducible builds from cache

## Image Processing

### Smart Handling

1. **Download** from PokéAPI official artwork
2. **Remove background** (transparent → white)
3. **Compress** aggressively (quality 40)
4. **Optimize** resolution (100px max)
5. **Cache** in memory for batch processing

### Fallback Strategy

- Primary source: Official Pokémon artwork
- Fallback: Alternative image sources
- Last resort: Type-based placeholder colors

## System Requirements

### Minimum

- **Python 3.10+**
- **macOS** (for system fonts - required for CJK)
- **2 GB RAM**
- **Internet connection** (first run only, for API & images)

### Recommended

- **Python 3.11+**
- **4 GB RAM**
- **SSD** (faster processing)

## Dependencies

- **ReportLab 4.0.7** - PDF generation
- **Pillow 12.1.0** - Image processing
- **requests 2.31.0** - HTTP requests
- **urllib3** - Connection pooling

See [requirements.txt](../requirements.txt) for full list.
