# Code Maintenance Checklist

**For developers maintaining and enhancing the BinderPokedex PDF generators**

---

## ✅ Pre-Phase Checklist (Before Starting New Work)

- [ ] All tests passing: `pytest scripts/tests/`
- [ ] No uncommitted changes: `git status` clean
- [ ] Latest main branch: `git pull origin main`
- [ ] Python environment active: `source venv/bin/activate`
- [ ] Dependencies up-to-date: `pip list | grep reportlab`

---

## ✅ Code Review Checklist (When Reviewing PRs)

### Error Handling
- [ ] No `bare except:` without specific exception type
- [ ] Generic `Exception` catches have proper logging
- [ ] Critical sections have `exc_info=True` in error logs
- [ ] Recovery strategies documented for expected errors

### Type Hints
- [ ] All public functions have return type hints (`-> Type`)
- [ ] Complex types use `Union`, `Optional`, `List`, `Dict`
- [ ] No `Any` types without explicit comment explaining why

### Logging
- [ ] Uses centralized logger (after Phase 6)
- [ ] Appropriate log level (DEBUG vs INFO vs WARNING)
- [ ] No sensitive data logged (passwords, API keys)
- [ ] Error logs include context for debugging

### Testing
- [ ] New functions have corresponding tests
- [ ] Edge cases covered (empty input, None, negative numbers)
- [ ] Tests pass locally before committing
- [ ] Coverage not decreased (check with pytest)

### Generator Code
- [ ] Uses shared utilities from `scripts/lib/utils.py`
- [ ] Uses shared constants from `scripts/lib/constants.py`
- [ ] Renders via modern Renderer classes (not deprecated templates)
- [ ] Respects DRY principle (Don't Repeat Yourself)

### Documentation
- [ ] Docstrings for all functions (Google style)
- [ ] Complex logic commented
- [ ] Architecture decisions documented
- [ ] README updated if behavior changed

---

## ✅ Common Patterns (Copy-Paste Ready)

### Error Handling (Do's & Don'ts)

```python
# ❌ DON'T: Bare except
try:
    load_image(path)
except:
    pass

# ✅ DO: Specific exceptions
try:
    load_image(path)
except FileNotFoundError:
    logger.warning(f"Image not found at {path}, using placeholder")
except IOError as e:
    logger.error(f"Cannot read image: {e}", exc_info=True)
except Exception as e:
    logger.error(f"Unexpected error loading image: {e}", exc_info=True)
    raise
```

### Adding New Generator Type

```python
# 1. Create class inheriting from base (after Phase 8)
class MyNewGenerator(GeneratorBase):
    def __init__(self, language: str = 'en'):
        super().__init__(language)
        # Custom initialization
    
    def generate(self, output_path: Path) -> bool:
        try:
            # Generate logic
            return True
        except Exception as e:
            logger.error(f"Generation failed: {e}", exc_info=True)
            return False

# 2. Register in generate_pdf.py
if args.type == 'my_type':
    gen = MyNewGenerator(args.language)
    gen.generate(output_path)

# 3. Add tests
class TestMyNewGenerator:
    def test_init(self):
        gen = MyNewGenerator()
        assert gen is not None
    
    def test_generate(self):
        result = gen.generate(Path('/tmp/test.pdf'))
        assert result is True
```

### Adding Translations

```python
# 1. Update i18n/translations.json
{
  "types": {
    "de": {
      "Water": "Wasser",
      "Fire": "Feuer"
    }
  }
}

# 2. Use via TranslationLoader (Phase 2+)
from scripts.lib.rendering.translation_loader import TranslationLoader

types = TranslationLoader.load_types('de')
water_de = types.get('Water', 'Water')  # Falls back to English
```

### Adding New Constants

```python
# ✅ GOOD: Add to scripts/lib/constants.py
MY_NEW_CONSTANT = "value"
NEW_COLORS = {
    'primary': '#FF0000',
    'secondary': '#00FF00',
}

# ✅ Then import everywhere
from .constants import MY_NEW_CONSTANT, NEW_COLORS

# ❌ AVOID: Defining constants in multiple files
```

---

## ✅ Known Limitations & Workarounds

| Issue | Workaround | Ticket |
|-------|-----------|--------|
| Large image sets slow generation | Use `--skip-images` during testing | See Phase 12 |
| Some fonts not rendering CJK | FontManager auto-falls back to Songti | Working as designed |
| card_template.py deprecated but still used | Keep for backward compatibility | ROADMAP Phase 8 |
| `bare except` in legacy code | Planned for Phase 5 | MAINTENANCE_ROADMAP.md |

---

## ✅ Regular Maintenance Tasks

### Weekly
- [ ] Monitor GitHub issues (if public)
- [ ] Check failed test runs in CI/CD
- [ ] Review latest commits for quality

### Monthly
- [ ] Update dependencies: `pip list --outdated`
- [ ] Re-run all tests with coverage: `pytest --cov=scripts`
- [ ] Check for new Python security updates
- [ ] Review and close old TODOs/FIXMEs

### Quarterly
- [ ] Performance benchmark (measure generation time)
- [ ] Review MAINTENANCE_ROADMAP.md progress
- [ ] Plan next phase improvements
- [ ] Update documentation as needed

---

## ✅ Useful Commands

```bash
# Testing
pytest scripts/tests/                           # Run all tests
pytest scripts/tests/test_rendering.py -v      # Verbose mode
pytest --cov=scripts                            # Coverage report
pytest --cov=scripts --cov-report=html          # HTML coverage

# Linting & Format
pylint scripts/lib/*.py                         # Check code quality
black scripts/lib/                              # Auto-format
mypy scripts/lib/                               # Type checking (after Phase 7)

# PDF Generation
python scripts/generate_pdf.py --type generation --generation 1 --language de
python scripts/generate_pdf.py --type variant --list
python scripts/generate_pdf.py --test                    # Dry run

# Git
git log --oneline -n 10                         # Recent commits
git diff HEAD~1                                 # What changed recently
git show <commit>                               # Inspect specific commit

# Analysis
grep -r "TODO\|FIXME" scripts/lib/              # Find TODOs
wc -l scripts/lib/**/*.py                       # Count lines of code
```

---

## ✅ Architecture Layers (Understand Before Coding)

```
generate_pdf.py (Entry point)
    ↓
PDFGenerator / VariantPDFGenerator (Orchestration)
    ↓
CardRenderer / CoverRenderer / VariantCoverRenderer (Rendering logic)
    ↓
FontManager, TranslationLoader, TextRenderer (Utilities)
    ↓
reportlab, PIL (External libraries)
```

**Rule:** Don't skip layers. Always use the highest abstraction available.

---

## ✅ Phase Progress

| Phase | Status | Lines Changed | Key Achievement |
|-------|--------|---------------|-----------------|
| 1 | ✅ Done | -300 | Deprecated code archived |
| 2 | ✅ Done | +180 | Modern renderers created |
| 3 | ✅ Done | -558 | Dead code removed |
| 4 | ✅ Done | -94 | Utilities consolidated |
| 5 | 📋 Planned | ~150 | Error handling improved |
| 6 | 📋 Planned | ~80 | Logger config centralized |
| 7 | 📋 Planned | ~50 | Type hints completed |
| 8 | 📋 Planned | +200 | Generator base class |
| 9 | 📋 Planned | ~40 | Config management |
| 10 | 📋 Planned | +500 | Test suite expanded |
| 11 | 📋 Planned | ~100 | Documentation |
| 12 | 📋 Planned | ~50 | Performance optimized |

---

## ✅ Questions to Answer Before Coding

1. **Is there a utility for this already?** Check `scripts/lib/utils.py`, `scripts/lib/constants.py`, and rendering modules
2. **Is this duplicated elsewhere?** Search codebase with `grep -r`
3. **Does this need error handling?** What exceptions are possible?
4. **Is this tested?** Write tests as you code
5. **Is this documented?** Add docstrings
6. **Is this logged?** Add appropriate log statements
7. **Is this type-hinted?** All functions should have type hints

---

## ✅ When You're Stuck

1. **Check existing code** - 95% of patterns already exist
2. **Read MAINTENANCE_ROADMAP.md** - Captures all known issues
3. **Review Phase 4 commit** - See what changed in last refactor
4. **Run tests** - They often show what's broken
5. **Add debug logging** - Insert `logger.debug()` to trace execution
6. **Ask in git commits** - Other maintainers can search commit history

---

## ✅ Definition of "Done"

A feature/fix is done when:

- [ ] Code written and reviewed
- [ ] Tests pass (all tests, not just new ones)
- [ ] Type hints added
- [ ] Error handling implemented
- [ ] Logging added (DEBUG or INFO level)
- [ ] Docstrings written
- [ ] No new warnings (Pylance, type checkers)
- [ ] MAINTENANCE_ROADMAP.md updated if applicable
- [ ] Git commit has clear message
- [ ] Related documentation updated

---

**Last Updated:** 2026-01-20
**Maintainer:** Current Developer
**Next Review:** 2026-02-20

Good luck! Ask questions in the code. 🚀
