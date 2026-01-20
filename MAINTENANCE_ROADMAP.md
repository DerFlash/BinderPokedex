# Maintenance & Enhancement Roadmap

**Last Updated:** 2026-01-20 (nach Phase 4 Refactoring)
**Current State:** Production-ready, 680+ lines cleaned, all tests passing

---

## 📋 Overview

Nach Phase 1-4 ist die Codebase hochgradig konsolidiert. Diese Roadmap identifiziert **generator-übergreifende Verbesserungen** für bessere Wartbarkeit und zukünftige Features.

---

## 🎯 Phase 5: Error Handling & Robustness

### Priority: HIGH ⭐⭐⭐

**Current Issues:**
- ⚠️ 56 `bare except` und `generic Exception` Catches verteilt über 15+ Dateien
- ⚠️ cover_template.py: 13x bare except (Legacy-Code)
- ⚠️ variant_cover_renderer.py: 5x bare except (Modern-Code)

**Why Important:**
- Schwer zu debuggen bei Fehlern
- Versteckt kritische Issues
- Macht Error-Recovery unmöglich

**Scope:**

| File | Issue | Action | Effort |
|------|-------|--------|--------|
| `cover_template.py` | 13x bare except | Replace with specific exception handling | 🔴 HIGH |
| `card_renderer.py` | 3x generic Exception | Add specific error types | 🟡 MED |
| `variant_cover_renderer.py` | 5x bare except | Refactor error handling | 🟡 MED |
| `pdf_generator.py` | 4x bare except | Use logging + specific errors | 🟡 MED |
| `cover_renderer.py` | 5x generic Exception | Typed exception handling | 🟡 MED |
| `fonts.py` | 2x generic Exception | Add fallback strategies | 🟢 LOW |

**Implementation Pattern:**
```python
# ❌ Current
except:
    logger.warning(f"Could not load: {e}")

# ✅ Target
except FileNotFoundError:
    logger.warning(f"File not found, using fallback")
except ValueError as e:
    logger.error(f"Invalid value: {e}", exc_info=True)
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise
```

**Benefits:**
- ✅ Clearer error types in logs
- ✅ Better debugging (stack traces)
- ✅ Proper error recovery strategies

---

## 🎯 Phase 6: Logger Configuration & Consistency

### Priority: HIGH ⭐⭐⭐

**Current Issues:**
- ⚠️ `card_renderer.py`: Uses logger but no initialization
- ⚠️ `page_renderer.py`: Initializes logger but never uses it
- ⚠️ Inconsistent log levels across modules

**Solution:**
1. Create centralized logger configuration in `scripts/lib/logging_config.py`
2. Import from there in all modules
3. Define log levels per module:
   - Core generators: INFO (progress bars, completion)
   - Utils/Renderers: DEBUG (detailed rendering steps)
   - Data fetchers: DEBUG (API calls, caching)

**Files to Update:**
- pdf_generator.py (20+ logger calls)
- variant_pdf_generator.py (15+ logger calls)
- card_renderer.py (add logger init)
- cover_renderer.py (12+ logger calls)
- variant_cover_renderer.py (8+ logger calls)

**Benefits:**
- ✅ Consistent log format
- ✅ Easy to enable/disable DEBUG mode
- ✅ Better structured logging

---

## 🎯 Phase 7: Type Hints Completion

### Priority: MEDIUM ⭐⭐

**Current Issues:**
- 📊 `crystalline_patterns.py`: 0/1 functions with return type hints
- 📊 Several helper functions missing `-> None` annotations
- 📊 Some complex types need `Union` or `Optional`

**Target:** 100% coverage for all public functions

**Files to Review:**
- `crystalline_patterns.py` (+5 type hints)
- `fonts.py` (+3 type hints)
- `utils.py` (+2 type hints)
- All rendering modules (✅ already done in Phase 2)

**Pattern:**
```python
# ❌ Current
def get_color_for_type(pokemon_type, brightness=1.0):
    return darkened_color

# ✅ Target
def get_color_for_type(pokemon_type: str, brightness: float = 1.0) -> str:
    return darkened_color
```

**Benefits:**
- ✅ IDE auto-completion
- ✅ Type checking with Pylance/mypy
- ✅ Better documentation

---

## 🎯 Phase 8: Generator Unification

### Priority: MEDIUM ⭐⭐

**Current State:**
Both `pdf_generator.py` and `variant_pdf_generator.py` exist independently.

**Opportunity:**
Create unified `GeneratorBase` class to extract common logic:

```
GeneratorBase
├── PDFGenerator (extends)
└── VariantGenerator (extends)
```

**Candidates for Extraction:**
1. **Image handling** - Both need image caching + fallback
2. **Progress bars** - Both use similar progress tracking
3. **File output** - Both write to `output/` directory
4. **Metadata** - Both add generation/variant info
5. **Font management** - Both use FontManager identically

**Estimated Impact:**
- 📉 Reduce code duplication by 15-20%
- ✅ Easier to add new generator types (Mega Evolution, Regional Variants)
- ✅ Centralized configuration

**Implementation Strategy:**
```
Phase 8a: Extract common patterns into GeneratorBase
Phase 8b: Refactor PDFGenerator to inherit from GeneratorBase
Phase 8c: Refactor VariantGenerator to inherit from GeneratorBase
Phase 8d: Add tests for GeneratorBase contract
```

---

## 🎯 Phase 9: Configuration Management

### Priority: MEDIUM ⭐⭐

**Current State:**
- Constants hardcoded in `scripts/lib/constants.py`
- Config paths scattered through code
- No central config file

**Solution:**
Create `scripts/lib/config.py` with:
```python
class GeneratorConfig:
    # Paths
    DATA_DIR: Path
    OUTPUT_DIR: Path
    CACHE_DIR: Path
    
    # PDF Generation
    CARDS_PER_PAGE: int
    DEFAULT_LANGUAGE: str
    SUPPORTED_LANGUAGES: List[str]
    
    # Performance
    IMAGE_CACHE_SIZE: int
    USE_PARALLEL_PROCESSING: bool
    
    # Logging
    LOG_LEVEL: str
```

**Benefits:**
- ✅ Easy to configure via environment variables
- ✅ Support for config files (YAML/JSON)
- ✅ Better CI/CD integration

---

## 🎯 Phase 10: Test Coverage Expansion

### Priority: MEDIUM ⭐⭐

**Current State:**
- 30 tests for rendering
- 32% coverage
- Missing: generator integration tests, error scenarios

**Target:** 60%+ coverage

**Areas to Add:**
1. **Error scenarios** (missing images, corrupt data, invalid types)
2. **Generator integration** (full PDF generation, file I/O)
3. **Variant handling** (mega evolution, regional variants)
4. **Multi-language** (edge cases, missing translations)
5. **Performance** (large generation sets)

**Test Categories to Add:**
```
scripts/tests/
├── test_error_handling.py (20+ tests)
├── test_generator_integration.py (15+ tests)
├── test_variants.py (10+ tests)
├── test_languages.py (10+ tests)
└── test_performance.py (5+ tests)
```

**Tools:** pytest (✅ already set up)

---

## 🎯 Phase 11: Documentation

### Priority: LOW ⭐

**Current Docs:**
- ✅ Architecture docs
- ✅ Installation guide
- ❌ Code generation API docs
- ❌ Developer maintenance guide
- ❌ Architecture decisions log

**To Add:**
1. **API Documentation** - Docstring generation with Sphinx
2. **Contributing Guide** - How to add new features/generators
3. **Architecture Decision Log** - Why certain choices were made
4. **Troubleshooting** - Common issues and solutions
5. **Performance Tuning** - Tips for large datasets

---

## 🎯 Phase 12: Performance Optimization

### Priority: LOW ⭐

**Current Bottlenecks:**
- Image loading from cache (could parallel-process)
- PDF rendering per page (could batch operations)
- Translation loading (already cached ✅)

**Opportunities:**
1. **Async image loading** - Load multiple images in parallel
2. **Canvas batching** - Render multiple cards before page break
3. **Font caching** - Currently loaded per card
4. **Memory optimization** - Stream large image files instead of loading all

**Estimated Improvement:**
- 5-10% faster generation for large sets (500+ cards)
- Lower memory usage for variant generation

---

## 📊 Summary & Dependency Chain

```
Phase 5 (Error Handling)
    ↓
Phase 6 (Logger Config)
    ├─→ Phase 10 (Better test error scenarios)
    └─→ Phase 12 (Monitor performance)
    
Phase 7 (Type Hints)
    ↓
Phase 8 (Generator Unification)
    ├─→ Phase 9 (Configuration)
    └─→ Phase 10 (Integration Tests)

Phase 11 (Documentation)
    └─→ Depends on: Phases 5-9 stable
```

---

## 🚀 Quick Wins (Start Here!)

If you want **immediate impact**, prioritize:

1. **Phase 6 (Logger Config)** - 2-3 hours, high impact
   - Centralized logging makes debugging 10x easier
   
2. **Phase 5 (Error Handling)** - 4-5 hours, high impact
   - Prevent silent failures
   - Better stack traces

3. **Phase 7 (Type Hints)** - 1-2 hours, medium impact
   - IDE improvements
   - Future-proofing

---

## 📈 Metrics to Track

Track improvements after each phase:

```bash
# Code Quality
lines_of_code_removed
test_coverage_percent
type_hints_coverage_percent
error_handling_score

# Performance
average_pdf_generation_time
memory_usage_peak
cache_hit_rate

# Maintainability
cyclomatic_complexity
average_function_length
documentation_coverage
```

---

## Notes

- **card_template.py** kept for backward compatibility (deprecated)
- **Phase 1-4** removed 680+ lines of dead/duplicate code ✅
- All rendering modules now use modern architecture ✅
- PDF generation is robust and multi-language capable ✅

Next maintainer: Use this roadmap for prioritization!
