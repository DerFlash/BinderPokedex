# Variants Documentation - Quick Start

**Updated:** January 19, 2026

---

## 🎯 Start Here

### What's This About?
The **Variants feature** lets you generate separate PDF binder collections for Pokémon variants.

**Currently Implemented:**
- ✅ Mega Evolution (76 Pokémon with 79 forms)

---

## 📚 5 Documents, Choose Your Path

```
START
  ↓
┌─────────────────────────────────────────────────────┐
│                                                     │
│  I want to:          READ THIS FIRST:             │
│                                                     │
│  📊 Understand       → VARIANTS_README.md          │
│     the feature        (this guides you)            │
│                                                     │
│  🖨️  Generate PDF    → VARIANTS_FEATURE_SUMMARY   │
│                        (usage & commands)           │
│                                                     │
│  🛠️  Understand      → VARIANTS_ARCHITECTURE      │
│     architecture       (technical design)           │
│                                                     │
│  ➕ Add new          → VARIANTS_IMPLEMENTATION    │
│     variants          (step-by-step)              │
│                                                     │
│  🔍 See details      → VARIANTS_TECHNICAL_SPEC    │
│                        (implementation details)    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Commands

Generate Mega Evolution PDFs:

```bash
# German only
python scripts/generate_pdf.py --type variant --variant mega --language de

# All 9 languages
python scripts/generate_pdf.py --type variant --variant mega --language all

# High quality
python scripts/generate_pdf.py --type variant --variant mega --language de --high-res

# Parallel (faster for all languages)
python scripts/generate_pdf.py --type variant --variant mega --language all --parallel
```

PDFs stored in: `output/{language}/variants/variant_mega_*.pdf`

---

## 📋 Document Map

| Document | Size | Purpose | Level |
|----------|------|---------|-------|
| **VARIANTS_README.md** | 9 KB | This document - navigation guide | Beginner |
| **VARIANTS_FEATURE_SUMMARY.md** | 13 KB | What the feature does | Beginner |
| **VARIANTS_ARCHITECTURE.md** | 16 KB | How it's built | Intermediate |
| **VARIANTS_IMPLEMENTATION_GUIDE.md** | 17 KB | How to add new variants | Advanced |
| **VARIANTS_TECHNICAL_SPEC.md** | 12 KB | Implementation details | Advanced |

**Total:** ~67 KB of focused documentation

---

## 🎓 By Role

### 👔 Manager / Product Owner
**Goal:** Understand what's delivered

**Read:**
1. [VARIANTS_FEATURE_SUMMARY.md](VARIANTS_FEATURE_SUMMARY.md) - Overview section
2. [VARIANTS_ARCHITECTURE.md](VARIANTS_ARCHITECTURE.md) - Architecture section
3. Done! ✓

**Time:** ~10 minutes

---

### 🖨️ User / Collector
**Goal:** Generate PDFs for my collection

**Read:**
1. [VARIANTS_FEATURE_SUMMARY.md](VARIANTS_FEATURE_SUMMARY.md) - PDF Generation section
2. Run the commands

**Time:** ~5 minutes

---

### 👨‍💻 Developer (Maintenance)
**Goal:** Maintain and understand the code

**Read:**
1. [VARIANTS_ARCHITECTURE.md](VARIANTS_ARCHITECTURE.md) - Complete
2. [VARIANTS_TECHNICAL_SPEC.md](VARIANTS_TECHNICAL_SPEC.md) - Complete
3. Browse: `/scripts/lib/variant_pdf_generator.py`

**Time:** ~30 minutes

---

### 🚀 Developer (Adding Features)
**Goal:** Implement new variant categories

**Read:**
1. [VARIANTS_IMPLEMENTATION_GUIDE.md](VARIANTS_IMPLEMENTATION_GUIDE.md) - Complete (essential!)
2. [VARIANTS_ARCHITECTURE.md](VARIANTS_ARCHITECTURE.md) - Architecture section
3. Reference: [VARIANTS_TECHNICAL_SPEC.md](VARIANTS_TECHNICAL_SPEC.md)

**Time:** ~45 minutes to understand, ~2-4 hours to implement one variant

---

### 🧪 QA / Tester
**Goal:** Test new variants

**Read:**
1. [VARIANTS_IMPLEMENTATION_GUIDE.md](VARIANTS_IMPLEMENTATION_GUIDE.md) - Step 5 (Testing)
2. [VARIANTS_TECHNICAL_SPEC.md](VARIANTS_TECHNICAL_SPEC.md) - Section 12 (Testing Checklist)

**Time:** ~15 minutes

---

## 🔑 Key Concepts

### What's a Variant?
A Pokémon form that can appear as a separate collection. Currently implemented:
- Mega Venusaur
- Mega Charizard (X & Y forms)
- Mega Mewtwo (X & Y forms)
- And 73 more Mega Evolution forms

### Variant Architecture
The variants feature is designed as an extensible system. New variant categories can be added following the same structure as Mega Evolution.

### How It Works

```
Data (JSON)
    ↓ Has: Pokémon names in 9 languages, image URLs, types
    ↓
Generator Script
    ↓ Reads JSON, loads images, renders cards
    ↓
ReportLab
    ↓ Creates PDF with proper layout
    ↓
Output PDF
    ↓ Professional, print-ready binder collection
```

### Naming System
Each Pokémon variant has a unique ID:

```
Format: #{number}_{TYPE}[_{FORM}]

Examples:
#003_MEGA               → Mega Venusaur
#006_MEGA_X             → Mega Charizard X
#006_MEGA_Y             → Mega Charizard Y
#201_UNOWN_?            → Unown (Question Mark)
```

---

## 📊 Current Status

**Mega Evolution:** ✅ Complete
- 76 Pokémon
- 79 forms (X/Y variants)
- 9 languages
- PDF generation working
- Professional quality
- Released in v2.2

---

## 📁 Where Things Are

```
Project Structure:
├── /docs/
│   ├── VARIANTS_README.md              ← You are here
│   ├── VARIANTS_FEATURE_SUMMARY.md     ← Feature overview
│   ├── VARIANTS_ARCHITECTURE.md        ← Technical design
│   ├── VARIANTS_IMPLEMENTATION_GUIDE.md ← How to extend
│   └── VARIANTS_TECHNICAL_SPEC.md      ← Implementation details
│
├── /data/variants/
│   ├── meta.json                       ← Metadata for all variants
│   ├── variants_mega.json              ← Mega Evolution data
│   ├── README.md                       ← Data format docs
│   └── IMAGES.md                       ← Image sourcing
│
├── /scripts/lib/
│   ├── variant_pdf_generator.py        ← Main engine
│   ├── card_template.py                ← Card rendering
│   ├── cover_template.py               ← Cover page
│   └── fonts.py                        ← Text rendering
│
└── /output/{language}/variants/
    └── variant_mega_*.pdf              ← Generated PDFs
```

---

## 🎯 Common Tasks

### "How do I generate Mega PDFs?"
→ [VARIANTS_FEATURE_SUMMARY.md](VARIANTS_FEATURE_SUMMARY.md) § PDF Generation

### "How do I add Gigantamax?"
→ [VARIANTS_IMPLEMENTATION_GUIDE.md](VARIANTS_IMPLEMENTATION_GUIDE.md) § Step 1-7

### "How many Pokémon are in Mega Evolution?"
→ 76 Pokémon with 79 forms

### "What languages are supported?"
→ 9 languages: DE, EN, FR, ES, IT, JA, KO, ZH-HANS, ZH-HANT

### "Where's the code?"
→ `/scripts/lib/variant_pdf_generator.py`

### "How's the data organized?"
→ [VARIANTS_TECHNICAL_SPEC.md](VARIANTS_TECHNICAL_SPEC.md) § Data Model

### "What if an image is missing?"
→ [VARIANTS_ARCHITECTURE.md](VARIANTS_ARCHITECTURE.md) § Image Sourcing (3-tier strategy)

---

## 🏃 Quick Start (5 Minutes)

1. **Generate a test PDF:**
   ```bash
   python scripts/generate_pdf.py --type variant --variant mega --language de
   ```

2. **Check the output:**
   ```bash
   open output/de/variants/variant_mega_de.pdf
   ```

3. **Review the data:**
   ```bash
   cat data/variants/variants_mega.json | head -50
   ```

4. **Learn more:**
   → Read [VARIANTS_FEATURE_SUMMARY.md](VARIANTS_FEATURE_SUMMARY.md)

---

## ✅ Next Steps

- **For Users:** Jump to [VARIANTS_FEATURE_SUMMARY.md](VARIANTS_FEATURE_SUMMARY.md)
- **For Developers:** Start with [VARIANTS_ARCHITECTURE.md](VARIANTS_ARCHITECTURE.md)
- **For Extending:** Go to [VARIANTS_IMPLEMENTATION_GUIDE.md](VARIANTS_IMPLEMENTATION_GUIDE.md)

---

## 📞 Questions?

**Q: Where's the Gigantamax documentation?**
A: Not yet implemented. See [VARIANTS_IMPLEMENTATION_GUIDE.md](VARIANTS_IMPLEMENTATION_GUIDE.md) to build it!

**Q: Can I use this for other Pokémon variants?**
A: Yes! Follow [VARIANTS_IMPLEMENTATION_GUIDE.md](VARIANTS_IMPLEMENTATION_GUIDE.md)

**Q: How do I contribute?**
A: See docs/CONTRIBUTING.md and then follow the implementation guide

**Q: Is the feature complete?**
A: Mega Evolution is complete. The architecture supports additional variant categories.

---

**Ready?** → Start with [VARIANTS_FEATURE_SUMMARY.md](VARIANTS_FEATURE_SUMMARY.md) 🚀

