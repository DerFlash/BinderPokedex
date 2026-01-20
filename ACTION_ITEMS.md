# ACTION ITEMS - Next Developer Tasks

**Document Created:** 2026-01-20
**Based On:** Systematic audit of codebase
**For:** Next maintainer to prioritize work

---

## 🎯 IMMEDIATE (This Week)

### ✅ Phase 6: Logger Configuration (2-3 hours)

**Why:** Enables single point of control for debugging

**Files to Create:**
- [ ] Create `scripts/lib/logging_config.py`
  - Centralized logger setup
  - Support DEBUG/INFO/WARNING/ERROR levels
  - Format consistency across modules

**Files to Update:**
- [ ] `scripts/lib/card_renderer.py` - add logger initialization
- [ ] `scripts/lib/page_renderer.py` - remove unused logger or use it
- [ ] All modules using logger - import from logging_config

**Validation:**
- [ ] All loggers use same format
- [ ] Can set global LOG_LEVEL
- [ ] Tests still pass

---

## 🎯 SHORT-TERM (Next 2 Weeks)

### ✅ Phase 5: Error Handling (4-5 hours)

**Why:** Prevent silent failures, improve debugging

**Priority Files (13+ bare excepts):**
- [ ] `scripts/lib/cover_template.py` (13x bare except)
  - Replace with `FileNotFoundError`, `ValueError`, etc.
  - Add proper logging with `exc_info=True`
  
- [ ] `scripts/lib/variant_cover_renderer.py` (5x bare except)
  - Same pattern
  
- [ ] `scripts/lib/pdf_generator.py` (4x bare except)
  - Same pattern

**Validation Pattern:**
```python
# Before: except:
# After:  except FileNotFoundError: ...
#         except ValueError: ...
```

- [ ] Run tests: `pytest scripts/tests/`
- [ ] No reduction in test count
- [ ] All tests still pass

---

### ✅ Phase 7: Type Hints (1-2 hours)

**Why:** IDE auto-completion, future-proofing

**Single Critical File:**
- [ ] `scripts/lib/crystalline_patterns.py`
  - Add return type hints to all functions
  - Use `-> None`, `-> str`, `-> Dict[str, int]`, etc.

**Pattern:**
```python
# Before:
def _draw_polygon(c, center_x, center_y, sides: int, size: float, rotation: float = 0):

# After:
def _draw_polygon(c, center_x, center_y, sides: int, size: float, rotation: float = 0) -> None:
```

**Validation:**
- [ ] Pylance/mypy happy: `mypy scripts/lib/crystalline_patterns.py`
- [ ] Tests pass
- [ ] No IDE warnings

---

## 📅 MEDIUM-TERM (Next Month)

### ✅ Phase 8: Generator Unification (8-10 hours)

**Why:** Reduce duplication, easier to maintain

**Analysis First:**
- [ ] Identify duplicate code in `pdf_generator.py` and `variant_pdf_generator.py`
- [ ] List common methods:
  - Image loading/caching
  - Progress bar management
  - File output handling
  - Metadata generation

**Extract to New Class:**
- [ ] Create `scripts/lib/base_generator.py`
  - `class GeneratorBase`
  - Common methods for both generators

**Refactor Existing:**
- [ ] `pdf_generator.py` → inherit from `GeneratorBase`
- [ ] `variant_pdf_generator.py` → inherit from `GeneratorBase`

**Testing:**
- [ ] All tests still pass
- [ ] PDF output identical to before
- [ ] Variant PDFs identical to before

---

### ✅ Phase 9: Configuration Management (3-4 hours)

**Why:** Easy customization, environment-specific configs

**Create:**
- [ ] `scripts/lib/config.py`
  - `class GeneratorConfig`
  - Load from environment vars or config file
  - Provide sensible defaults

**Example:**
```python
class GeneratorConfig:
    DATA_DIR = Path.home() / ".binderokedex" / "data"
    OUTPUT_DIR = Path.cwd() / "output"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    CACHE_SIZE = int(os.getenv("CACHE_SIZE", 500))
```

**Update Generators:**
- [ ] Use `GeneratorConfig` instead of hardcoded paths

---

## 🔬 LONG-TERM (2+ Months)

### ✅ Phase 10: Test Coverage (10-15 hours)

**Why:** Catch bugs before production, easier refactoring

**Target:** 60%+ coverage (currently 32%)

**New Test Files:**
- [ ] `scripts/tests/test_error_handling.py`
  - Missing files, corrupt data, invalid types
  - 20+ tests

- [ ] `scripts/tests/test_generator_integration.py`
  - Full PDF generation, file I/O
  - 15+ tests

- [ ] `scripts/tests/test_variants.py`
  - Mega evolution, regional variants
  - 10+ tests

- [ ] `scripts/tests/test_languages.py`
  - All 9 languages, missing translations
  - 10+ tests

**Validation:**
- [ ] `pytest --cov=scripts --cov-report=html`
- [ ] Coverage at 60%+
- [ ] HTML report shows uncovered code

---

### ✅ Phase 11: Documentation (8-10 hours)

**Why:** Help future maintainers, enable feature contributions

**Add:**
- [ ] **API Docs** → `docs/API.md`
  - How to call generators
  - Parameter documentation
  - Return types

- [ ] **Contributing Guide** → `docs/CONTRIBUTING.md`
  - How to add new generator types
  - Code style guidelines
  - Review process

- [ ] **Architecture Decisions Log** → `docs/ADR.md`
  - Why CardRenderer exists
  - Why TranslationLoader was created
  - Why card_template.py kept

- [ ] **Troubleshooting** → `docs/TROUBLESHOOTING.md`
  - Common errors and solutions
  - Performance tuning
  - Debug tips

---

### ✅ Phase 12: Performance (6-8 hours)

**Why:** Faster PDF generation for large datasets

**Optimization Ideas:**
- [ ] Parallel image loading (currently sequential)
- [ ] Async rendering (use concurrent.futures)
- [ ] Font caching (currently reloaded per card)
- [ ] Memory streaming for large images

**Benchmark Before/After:**
```bash
time python scripts/generate_pdf.py --type generation --generation 1
# Before: ~15 seconds
# After:  ~12 seconds (5-10% improvement)
```

---

## 📋 General Guidelines for All Phases

### Before Starting
- [ ] Read `MAINTENANCE_ROADMAP.md`
- [ ] Read `DEVELOPER_CHECKLIST.md`
- [ ] Verify tests passing: `pytest scripts/tests/`
- [ ] Git status clean: `git status`

### During Development
- [ ] Follow code review checklist
- [ ] Write tests for new code
- [ ] Add type hints
- [ ] Add docstrings
- [ ] Add logging (where appropriate)

### Before Committing
- [ ] All tests pass: `pytest scripts/tests/`
- [ ] No new Pylance warnings
- [ ] Commit message clear and descriptive
- [ ] No accidental file changes (check `git diff`)

### After Committing
- [ ] Push to main (after review if applicable)
- [ ] Verify CI/CD passes (if configured)
- [ ] Mark phase complete in this document

---

## ✅ Completion Checklist (Per Phase)

When starting a phase:

- [ ] Create git branch: `git checkout -b phase-X-description`
- [ ] Read phase description in MAINTENANCE_ROADMAP.md
- [ ] List all files to modify
- [ ] Write tests for new behavior
- [ ] Implement changes
- [ ] Run full test suite
- [ ] Update commit message
- [ ] Create PR (if team-based)
- [ ] Merge to main after review
- [ ] Update MAINTENANCE_ROADMAP.md (mark complete)
- [ ] Update this ACTION_ITEMS.md (delete completed item)

---

## 📊 Progress Tracker

```
Phase 1-4: ✅ COMPLETE (680+ lines removed)
Phase 5:   ⏸️  NOT STARTED (4-5 hours)
Phase 6:   ⏸️  NOT STARTED (2-3 hours) ← START HERE
Phase 7:   ⏸️  NOT STARTED (1-2 hours)
Phase 8:   ⏸️  NOT STARTED (8-10 hours)
Phase 9:   ⏸️  NOT STARTED (3-4 hours)
Phase 10:  ⏸️  NOT STARTED (10-15 hours)
Phase 11:  ⏸️  NOT STARTED (8-10 hours)
Phase 12:  ⏸️  NOT STARTED (6-8 hours)
```

**Total Estimated Effort:** 43-61 hours across all phases

---

## 🚀 Quick Reference

**Need to know where to start?**
→ Start with Phase 6 (2-3 hours, highest ROI)

**Want to make biggest code improvement?**
→ Phase 5 + Phase 8 (fixes issues + reduces duplication)

**Want fastest completion?**
→ Phase 7 (1-2 hours, immediate IDE improvement)

**Want to make code production-perfect?**
→ Phases 5, 6, 7 (quick wins that prevent bugs)

---

**Document Version:** 1.0
**Last Updated:** 2026-01-20
**Next Review:** 2026-02-20

Good luck! The roadmap is clear. Tackle one phase at a time. 🎯
