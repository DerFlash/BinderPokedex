# ✨ Pokémon Variants Feature - Implementation Status

**Project:** BinderPokedex v2.2  
**Feature:** Pokémon Variants as separate binder categories  
**Status:** 🟢 Phase 1 Complete (Mega Evolution), Phase 2+ Planned  
**Date:** January 19, 2026

---

## 🎯 Executive Summary

This feature enables the generation of **separate collection binders for Pokémon variants** analogous to the existing 9 generations.

**Phase 1 Completed:**
- **Mega Evolution:** 76 Pokémon with 79 form-specific images
- Full 9-language support
- Professional PDF generation with cutting guides

**Future Phases:**
- Gigantamax forms (32+ Pokémon)
- Regional variants (Alola, Galar, Hisui, Paldea)
- Primal Reversion & Terastal forms
- Pattern variations & Fusion forms

---

## 📊 Implementation Status

### ✅ Phase 1: Mega Evolution (COMPLETE)
```
✓ 76 Pokémon species
✓ 79 form-specific forms (X/Y variants with distinct images)
✓ PokeAPI + Bulbapedia image sources
✓ Full PDF generation (9 languages)
✓ 2.5 MB per PDF, ~26.5 MB total cached images
✓ Professional card layout with type-based styling
✓ Cutting guides and print-ready format
✓ Released as part of v2.2
```

### 🔄 Phase 2: Gigantamax (Planned)

### Category 7: Primal & Terastal 💎
```
🔹 Primal Reversion: Kyogre, Groudon (2 forms)
🔹 Terastal Phenomenon: Ogerpon (4 masks), Terapagos (Stellar)
🔹 Available in: Scarlet/Violet+
```

### Category 8: Patterns & Unique Forms 🎭
```
🔹 Unown: 28 forms (A-Z, ?, !)
🔹 Vivillon: 20 patterns
🔹 Castform: 4 weather forms
🔹 Oricorio: 4 blossom forms
🔹 Gender Differences: 102+ Pokémon (female forms only, visually distinct)
🔹 Total: 30+ Pokémon with 48+ forms, 102+ gender variants
```

### Category 9: Fusion & Special 🔗
```
🔹 Kyurem: Black Kyurem, White Kyurem
🔹 Necrozma: Dusk Mane, Dawn Wings
🔹 Calyrex: Ice Rider, Shadow Rider
🔹 Total: 3 Pokémon with 6 forms
```

---

## 🏗️ Architecture Overview

### Data Structure
```
/data/variants/
├── meta.json                          # Metadata for all variants
├── variants_mega.json                 # 96 Mega Evolution forms
├── variants_gigantamax.json           # 32 Gigantamax forms
├── variants_regional_alola.json       # 18 Alolan forms
├── variants_regional_galar.json       # 16 Galarian forms
├── variants_regional_hisui.json       # 15 Hisuian forms
├── variants_regional_paldea.json      # 8 Paldean forms
├── variants_primal_terastal.json      # 6 Primal/Terastal forms
├── variants_patterns_unique.json      # 48 Patterns & Unique
└── variants_fusion_special.json       # 6 Fusion forms
```

### PDF Output Structure
```
/output/{language}/variants/
├── variant_mega_de.pdf
├── variant_mega_en.pdf
├── variant_mega_fr.pdf
├── ...
├── variant_gigantamax_de.pdf
├── variant_gigantamax_en.pdf
└── [continues for all 9 variants × 9 languages]
```

### Numbering Schema
```
Format: #{pokemon_id}_{VARIANT_TYPE}[_{FORM_SUFFIX}]

Single Variant:
  #003_MEGA           → Mega Venusaur
  #025_GIGANTAMAX     → Gigantamax Pikachu
  #026_ALOLA          → Alolan Raichu

Multiple Variants (with suffix):
  #006_MEGA_X         → Mega Charizard X
  #006_MEGA_Y         → Mega Charizard Y
  #104_PALDEA         → Paldean Tauros (Normal, new form)
  #104_PALDEA_WATER   → Paldean Tauros (Water, new form)
  #104_PALDEA_FIRE    → Paldean Tauros (Fire, new form)

Special Cases:
  #201_UNOWN_?        → Unown (Question Mark)
  #201_UNOWN_!        → Unown (Exclamation Mark)
  #201_UNOWN_A        → Unown (Letter A)
  #741_ORICORIO_BAILE      → Oricorio (Baile Style)
  #741_ORICORIO_POM_POM    → Oricorio (Pom-Pom Style)
  #741_ORICORIO_PAU        → Oricorio (Pau Style)
  #741_ORICORIO_SENSU      → Oricorio (Sensu Style)
  #012_FEMALE         → Butterfree (Female form, visually distinct)
  #025_FEMALE         → Pikachu (Female form)
  #001_SHINY          → Shiny Bulbasaur (if included)
```

---

## 🖨️ CLI Interface

### Command Syntax
```bash
# Generate single variant
python scripts/generate_pdf.py --type variant --variant mega --language de

# Generate all variants for a language
python scripts/generate_pdf.py --type variant --variant all --language en

# With all options
python scripts/generate_pdf.py \
  --type variant \
  --variant gigantamax \
  --language es \
  --high-res \
  --parallel

# List available variants
python scripts/generate_pdf.py --type variant --list
```

### New Config Options
```yaml
variants:
  enabled: true
  categories:
    - mega_evolution
    - gigantamax
    - regional_alola
    - regional_galar
    - regional_hisui
    - regional_paldea
    - primal_terastal
    - patterns_unique
    - fusion_special
```

---

## 📋 Implementation Plan (5 Weeks)

### ✅ Phase 0: Planning (COMPLETED)
- [x] Complete Bulbapedia research
- [x] Categorization into 9 variants
- [x] Technical specification created
- [x] Numbering schema defined

### 🔄 Phase 1: Core Infrastructure (Week 1-2)
- [ ] Create JSON schemas in `/data/variants/`
- [ ] Implement meta-file structure
- [ ] Extend CLI with `--type variant`
- [ ] Update configuration

### 🟡 Phase 2: MVP - Mega Evolution (Week 2-3)
- [ ] Fetch data (PokeAPI + Manual)
- [ ] Mega JSON with 96 forms
- [ ] Create PDF templates
- [ ] Complete generation testing

### 🟡 Phase 3: Gigantamax (Week 3)
- [ ] Prepare Gigantamax data
- [ ] Parallel generation with Mega

### 🟡 Phase 4: Regional Forms (Week 4)
- [ ] Alola (18) + Galar (16) + Hisui (15) + Paldea (8)
- [ ] Adjust unified template

### 🟡 Phase 5: Final Variants & QA (Week 5)
- [ ] Primal, Terastal, Patterns, Fusion
- [ ] Complete multilingual QA
- [ ] Performance testing (parallel generation)
- [ ] Prepare release

---

## 💾 Data Sources

### Primary
- **PokeAPI** (https://pokeapi.co/) - available base data
- **Bulbapedia** - detailed variant information
- **Official Pokémon Resources** - artwork & official data

### Fallback
- **Manual Definitions** - for incomplete data
- **GitHub Collections** - community data

---

## 🎨 Design Highlights

### Cover Page per Variant
```
┌─────────────────────────────────────┐
│            ⚡                       │
│       MEGA EVOLUTION               │
│                                    │
│  Introduced in Generation VI       │
│  (Pokémon X & Y)                   │
│                                    │
│  87 Pokémon | 96 Forms             │
│                                    │
│  Allows Pokémon to temporarily    │
│  transform during battle, gaining  │
│  increased stats and sometimes     │
│  changing type.                    │
│                                    │
│ Print borderless. Follow lines.   │
└─────────────────────────────────────┘
```

### Card Layout (per Pokémon)
```
┌──────────────────────┐
│ [MEGA BADGE] #003   │
│                     │
│   [VARIANT IMAGE]   │
│                     │
│  Mega Venusaur     │
│  Base: Venusaur    │
│  [Grass][Poison]   │
│                     │
│  HP: 80  ATK: 82   │
│  DEF: 100 SpA: 122 │
│  SpD: 120 SPE: 80  │
└──────────────────────┘
```

---

## 🌍 Multilingual Support

Full support for all 9 languages:
- 🇩🇪 Deutsch (DE)
- 🇬🇧 English (EN)
- 🇫🇷 Français (FR)
- 🇪🇸 Español (ES)
- 🇮🇹 Italiano (IT)
- 🇯🇵 日本語 (JA)
- 🇰🇷 한국어 (KO)
- 🇨🇳 简体中文 (ZH-HANS)
- 🇹🇼 繁体中文 (ZH-HANT)

---

## 📈 Expected Outputs

### Per Variant (~9 categories)
- **1 Cover Page** (German, English, etc.)
- **20-100 Pokémon Pages** per language
- **~2-5 MB** per PDF (all languages)

### Total
- **~90 PDFs** (9 variants × ~10 average)
- **~150-200 MB** total size
- **~1-2 hours** generation (sequential)
- **~15-30 min** generation (parallel)

---

## ⚠️ Known Challenges

| Challenge | Solution |
|-----------|----------|
| Missing official numbers | Independent numbering schema |
| Image availability | Hybrid: PokeAPI + Bulbapedia scraping |
| Data consistency | Manual verification + QA pass |
| Performance | Parallel processing + caching |
| Multilingual translations | Crowdsourced + Bulbapedia dictionary |

---

## 🚀 Next Steps

### For Users
1. **Review** this planning (feedback?)
2. **Validate** the 9 variant categories (OK?)
3. **Set priorities** (MVP first?)

### For Development
1. Create JSON schemas
2. Phase 1: Core infrastructure
3. Phase 2: Mega Evolution MVP
4. Iteratively proceed with further phases

---

## 📚 Detailed Documentation

See also:
- **[VARIANTS_RESEARCH.md](VARIANTS_RESEARCH.md)** - Detailed research & categorization
- **[VARIANTS_TECHNICAL_SPEC.md](VARIANTS_TECHNICAL_SPEC.md)** - Technical specification

---

## 💬 Feedback Points

**Please review the following points:**

1. ✅ Are the **9 variant categories** sensible?
2. ✅ Should Mega & Gigantamax be separate or together?
3. ✅ Is the **numbering schema** sufficient?
4. ✅ Priority: **Mega first** or different?
5. ✅ Do we need **high-res variant** or standard?

---

**Status:** 🟢 Ready for Phase 1 Implementation  
**Estimated Duration:** 5-6 weeks (with tests)  
**Complexity:** Medium-High (lots of data, multilingual, PDF performance)

