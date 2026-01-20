# Rendering Module - Unified PDF Rendering Components

This module provides unified, centralized rendering components for all PDF generation in the Binder Pokédex project.

## Architecture Overview

The rendering module consolidates duplicated code from `pdf_generator.py` and `card_template.py` into a modular, reusable architecture:

```
rendering/
├── __init__.py                  # Module exports
├── translation_loader.py        # ✨ NEW: Centralized i18n loading
├── card_renderer.py             # ✨ NEW: Unified card rendering
├── cover_renderer.py            # ✨ NEW: Unified cover rendering
└── page_renderer.py             # ✨ NEW: Page layout & structure
```

## Components

### TranslationLoader
**Purpose:** Centralized translation loading with caching

**Features:**
- Loads type translations (Water → Wasser, Fire → Feuer)
- Loads UI translations (labels, buttons, messages)
- Caches translations for performance
- Robust path resolution using `.resolve()`

**Usage:**
```python
from scripts.lib.rendering import TranslationLoader

# Load type translations for German
types_de = TranslationLoader.load_types('de')
water_de = types_de['Water']  # 'Wasser'

# Load UI translations
ui_de = TranslationLoader.load_ui('de')
```

### CardRenderer
**Purpose:** Unified card rendering for both Generation and Variant PDFs

**Features:**
- Type-based header colors (consistent with CardStyle)
- Pokémon name rendering with language support
- Gender symbol fallback (♂/♀)
- Type translation rendering
- Image handling with cache integration
- Variant-specific formatting (EX, Mega, etc.)

**Usage:**
```python
from scripts.lib.rendering import CardRenderer

renderer = CardRenderer('de', image_cache=cache, variant='ex_gen1')
renderer.render_card(canvas, pokemon_data, x, y, variant_mode=True)
```

### CoverRenderer
**Purpose:** Unified cover page rendering

**Features:**
- Generation-based color schemes
- Region and generation information display
- Iconic Pokémon display at bottom
- Multi-language support
- Consistent styling across all generations

**Usage:**
```python
from scripts.lib.rendering import CoverRenderer

renderer = CoverRenderer('de', generation=1, image_cache=cache)
renderer.render_cover(canvas, pokemon_list)
```

### PageRenderer
**Purpose:** Page layout and structure management

**Features:**
- Page background and styling
- Card grid layout (3x3 per page)
- Cutting guides generation
- Footer rendering
- Card position calculations
- Page number/count calculations

**Usage:**
```python
from scripts.lib.rendering import PageRenderer

renderer = PageRenderer()
renderer.create_page(canvas)
renderer.add_card_to_page(canvas, card_renderer, pokemon_data, card_index)
renderer.add_footer(canvas)
```

## Style Classes

Each renderer has an associated **Style** class containing all styling constants:

- **CardStyle**: Colors, fonts, dimensions for cards
- **CoverStyle**: Colors, fonts, dimensions for cover pages
- **PageStyle**: Page layout dimensions, gaps, margins

```python
from scripts.lib.rendering import CardStyle, CoverStyle, PageStyle

# Access style constants
color = CardStyle.TYPE_COLORS['Fire']        # '#F08030'
header_height = CardStyle.HEADER_HEIGHT      # 12 * mm
```

## Migration from Old Components

### Old (Deprecated) → New (Unified)

| Old Component | Location | Replacement |
|---------------|----------|-------------|
| `_draw_card()` | pdf_generator.py | `CardRenderer.render_card()` |
| `CardTemplate.draw_card()` | card_template.py | `CardRenderer.render_card()` |
| `_draw_cover_page()` | pdf_generator.py | `CoverRenderer.render_cover()` |
| `_draw_cutting_guides()` | pdf_generator.py | `PageRenderer.draw_cutting_guides()` |
| `_calculate_card_position()` | pdf_generator.py | `PageRenderer.calculate_card_position()` |
| `_load_type_translations()` | pdf_generator.py | `TranslationLoader.load_types()` |

### Example Migration

**Before (pdf_generator.py):**
```python
def _draw_card(self, canvas_obj, pokemon_data, x, y):
    # ... 100+ lines of card rendering code
    type_translations = self._load_type_translations()
    type_text = type_translations.get(self.language, {}).get(type_english, type_english)
    # ... more code
```

**After (using CardRenderer):**
```python
self.card_renderer = CardRenderer(self.language, self.image_cache)
self.card_renderer.render_card(canvas_obj, pokemon_data, x, y)
```

## Benefits of This Architecture

| Problem | Before | After |
|---------|--------|-------|
| **Type translations forgot in one place** | Had to update 2+ files | Update only TranslationLoader |
| **Styling changes** | Duplicated in pdf_generator + card_template | Single CardStyle class |
| **Path loading bugs** | Multiple implementations with `.parent.parent` | One robust `.resolve()` in TranslationLoader |
| **Feature parity** | Gen PDFs vs Variant PDFs inconsistent | Automatically identical via shared renderers |
| **Code duplication** | ~200 lines of duplicated rendering code | Single, unified implementations |
| **Testing burden** | Had to test both implementations | Test only new modules |

## Implementation Details

### Paths and Resolution
All path calculations use `.resolve()` for robust absolute path resolution:

```python
# Correct (uses .resolve())
loader_file = Path(__file__).resolve()
translations_path = loader_file.parent.parent.parent.parent / 'i18n' / 'translations.json'

# Wrong (relative paths can break)
translations_path = Path(__file__).parent.parent.parent / 'i18n' / 'translations.json'
```

### Caching Strategy
- TranslationLoader caches translations in memory (with `.clear()` method)
- ImageCache handled separately by PDFGenerator
- No circular dependencies

### Language Support
Supports all 9 languages:
- `en` (English)
- `de` (German)
- `fr` (French)
- `es` (Spanish)
- `it` (Italian)
- `ja` (Japanese)
- `ko` (Korean)
- `zh_hans` (Chinese Simplified)
- `zh_hant` (Chinese Traditional)

## Future Enhancements

Potential areas for further refinement:

1. **VariantCoverRenderer** - Custom cover rendering for variant-specific designs
2. **ThemeSystem** - Allow custom color themes and styling
3. **LayoutPlugins** - Support alternative card layouts (2x2, 4x4, etc.)
4. **ExportFormats** - Support for PNG, SVG exports in addition to PDF

## Related Documentation

- [ARCHITECTURE.md](../ARCHITECTURE.md) - Overall project architecture
- [ARCHITECTURE_REFACTORING_PLAN.md](../ARCHITECTURE_REFACTORING_PLAN.md) - Original refactoring plan
- [VARIANTS_ARCHITECTURE.md](../VARIANTS_ARCHITECTURE.md) - Variant system architecture
