# 📖 Pokémon Variants Feature - Terminology & Glossary

**Status:** Clarification & Definition  
**Date:** January 19, 2026  
**Priority:** CRITICAL - Must be clear BEFORE implementation

---

## 🎯 Problem Statement

The following terms are overloaded/unclear:
- **Form** vs **Variant** - What is what?
- **Species** - Does it change?
- **Category** - Difference to Variant?
- **Hierarchy** - How is the structure?

**Consequence:** Without clear definitions, the code will become confused and inconsistent.

---

## 📚 Research: What do the sources say?

### Bulbapedia Definitions

**Form (Forms):**
> "A difference in appearance of a Pokémon that is unattributed to Evolution is known as a form."

**Form change:**
> "The term 'form change' is the process in which a species can alternate between one or more existing forms."

**Forme (French spelling):**
> "Some of these alternate appearances are instead named using the French word Forme."

**Regional form/variant:**
> "Regional forms, formerly known as regional variants, are Pokémon that have adapted specifically to the environment of the region they reside in."

**Species:**
> "The term Pokémon species refers to a member of the genus Pokémon, which is the scientific classification."

---

## 🏗️ Proposed Clear Hierarchy

### Level 1: SPECIES
**Definition:** The base type of Pokémon (by scientific classification)

**Examples:**
- Raichu (Species #026)
- Charizard (Species #006)
- Kyogre (Species #382)

**Properties:**
- Has a unique Pokédex number
- Can undergo Evolution → becomes different Species
- Is NOT the same as a "Form"

---

### Level 2: VARIANT
**Definition:** The MECHANIC/CATEGORY of a form (= type of transformation/differentiation)

**Examples:**
- "Mega Evolution" (Variant)
- "Alolan Form" (Variant)
- "Gigantamax" (Variant)
- "Terastal Phenomenon" (Variant)

**Properties:**
- Describes ONE TYPE of form change
- Can apply to MANY species
- Is mechanically/gameplay-defined
- Example: "Mega Evolution" affects ~87 species

---

### Level 3: FORM
**Definition:** The concrete appearance of a species under a variant

**Examples:**
- "Alolan Raichu" (Form)
- "Mega Charizard X" (Form)
- "Gigantamax Pikachu" (Form)

**Properties:**
- Specific implementation
- May have unique Stats/Types
- Can have images & data

---

### Level 4: CATEGORY
**Definition:** OUR collection groups (for UI/PDF generation)

**Examples (the 9 categories):**
- Category 1: "Mega Evolution"
- Category 2: "Gigantamax"
- Category 3: "Alolan Forms"
- etc.

**Properties:**
- WE define these (not official)
- Structure the output (PDF binders)
- = Practical organization structure

---

## 📊 Concrete Examples for Clarity

### Example 1: Raichu (Alolan)

```
Level 1 - SPECIES: Raichu (#026)
   ↓
Level 2 - VARIANT: Alolan Form
   ↓
Level 3 - FORM: Alolan Raichu
   │
   ├─ Image: alolan_raichu.png
   ├─ Types: Electric, Psychic
   ├─ Stats: different from Raichu
   └─ Moveset: different
   
Level 4 - CATEGORY: "Category 3: Alolan Forms"
```

### Example 2: Charizard (Mega)

```
Level 1 - SPECIES: Charizard (#006)
   ↓
Level 2 - VARIANT: Mega Evolution
   ├─ Form 1: Mega Charizard X
   │  ├─ Image: mega_charizard_x.png
   │  ├─ Types: Fire, Dragon
   │  └─ Stats: boosted
   │
   └─ Form 2: Mega Charizard Y
      ├─ Image: mega_charizard_y.png
      ├─ Types: Fire, Flying
      └─ Stats: boosted

Level 4 - CATEGORY: "Category 1: Mega Evolution"
```

### Example 3: Pikachu (Gigantamax)

```
Level 1 - SPECIES: Pikachu (#025)
   ↓
Level 2 - VARIANT: Gigantamax
   ↓
Level 3 - FORM: Gigantamax Pikachu
   ├─ Image: gigantamax_pikachu.png
   ├─ Size: enormous (height: 21m)
   └─ G-Max Move: G-Max Volt Crash

Level 4 - CATEGORY: "Category 2: Gigantamax"
```

### Example 4: Tauros (Paldean)

```
Level 1 - SPECIES: Tauros (#128)
   ↓
Level 2 - VARIANT: Paldean Form
   ├─ Form 1: Paldean Tauros (Normal)
   ├─ Form 2: Paldean Tauros (Water)
   └─ Form 3: Paldean Tauros (Fire)

Level 4 - CATEGORY: "Category 6: Paldean Forms"
```

---

## 🎯 Clear Definitions (FINAL)

### SPECIES
- **Definition:** The base Pokémon by Pokédex number
- **Immutable:** Yes
- **Examples:** Raichu, Charizard, Kyogre, Pikachu
- **Total Count:** 1,025 (all 9 generations)
- **Changed via Evolution:** No, that becomes a different Species then
- **In Data Structure:** `base_pokemon_id`, `base_pokemon_name`

### VARIANT
- **Definition:** The category/type of form (mechanics-based)
- **Examples:** "Mega Evolution", "Alolan Form", "Gigantamax", "Terastal"
- **Count:** ~9 major variants (= our 9 categories)
- **Properties:** Has Name, Icon, Color, Introduction-Gen
- **In Data Structure:** `variant_type`, `variant_name`

### FORM
- **Definition:** The concrete appearance under a variant
- **Variable:** Yes - can be multiple per species & variant
- **Examples:** "Mega Charizard X", "Alolan Raichu", "Gigantamax Pikachu"
- **Properties:** Own Stats, Types, Moves, Images
- **In Data Structure:** `variant_pokemon` Entry with `variant_name`, `id`, `image_url`, `stats`, `types`

### CATEGORY
- **Definition:** OUR collection structure for PDFs/UI
- **Count:** 9 (= our 9 variants, but structured for output)
- **Examples:** "Category 1: Mega Evolution", "Category 2: Gigantamax"
- **In Data Structure:** `variant_id` in database/config

---

## 🗂️ Data Structure with Clear Terminology

### JSON Structure (correct terms)

```json
{
  "category_id": 1,
  "category_name": "Mega Evolution",
  "category_icon": "⚡",
  
  "variant_type": "mega_evolution",
  "variant_name": "Mega Evolution",
  "introduction_generation": 6,
  
  "pokemon": [
    {
      "form_id": "mega_003",
      "base_pokemon_id": 3,
      "base_pokemon_name": "Venusaur",
      "form_name": "Mega Venusaur",
      "types": ["Grass", "Poison"],
      "base_stats": {...},
      "image_url": "...",
      "variant": "mega_evolution"
    }
  ]
}
```

### Relationship in Code

```python
# SPECIES - The base
SPECIES = {
    "id": 3,
    "name": "Venusaur",
    "generation": 3
}

# VARIANT - The category of form
VARIANT = {
    "type": "mega_evolution",
    "name": "Mega Evolution",
    "category": 1
}

# FORM - The concrete implementation
FORM = {
    "id": "mega_003",
    "species_id": 3,
    "variant_type": "mega_evolution",
    "name": "Mega Venusaur",
    "image_url": "...",
    "stats": {...},
    "types": ["Grass", "Poison"]
}
```

---

## 📝 Terminology in Documentation

### CORRECT ✅

```markdown
"Mega Evolution is a VARIANT that applies to 87 SPECIES.
There are 96 different FORMS of Mega Evolution.
For example, the SPECIES Charizard has two FORMS:
Mega Charizard X and Mega Charizard Y.

These FORMS are organized in CATEGORY 1."
```

### INCORRECT ❌

```markdown
"Mega Evolution is a Form..."
"Charizard is a Variant..."
"There are 96 Species in Mega Evolution..."
```

---

## 🔄 Mapping: Old → New Terminology

| Old (confusing) | New (clear) |
|-----------------|-----------|
| "Pokémon Variants" | "Pokémon Forms" or "Pokémon Variant Categories" |
| "9 Variant Categories" | "9 Variants" |
| "240 Pokémon with Variants" | "~240 Species with Forms" |
| "195 different Forms" | "195 different Forms" ✅ (this was correct) |
| "Variant: Mega Evolution" | "Variant: Mega Evolution" ✅ (this was correct) |

---

## 💡 Convention for Filenames/IDs

To make it clear in code/data:

### File Naming
```
# JSON files: Named by VARIANT
/data/variants/variants_mega.json
/data/variants/variants_gigantamax.json
/data/variants/variants_regional_alola.json

# PDF Output: Named by CATEGORY + VARIANT
/output/{lang}/variants/category_1_mega_evolution/
/output/{lang}/variants/category_2_gigantamax/
```

### ID Naming
```
# Format: {variant_code}_{species_id}[_{form_index}]

mega_003          # Species 003, Mega Evolution, Form 1
mega_006_a        # Species 006, Mega Evolution, Form 1 (X)
mega_006_b        # Species 006, Mega Evolution, Form 2 (Y)
giga_025          # Species 025, Gigantamax, Form 1
alola_026         # Species 026, Alolan Form, Form 1
```

---

## 🎓 Communication Guidelines

### In Documentation:
- **SPECIES:** "Raichu", "Charizard" (concrete type)
- **VARIANT:** "Mega Evolution", "Alolan Form" (the category)
- **FORM:** "Mega Raichu", "Alolan Raichu" (description)
- **CATEGORY:** "Category 1", "Category 3: Alolan Forms" (our structure)

### In Code Comments:
```python
# Get all FORMS of a specific SPECIES under a VARIANT
def get_forms(species_id: int, variant_type: str) -> List[Form]:
    """Returns all Forms for a Species in a given Variant"""
    pass

# Example: Get all Mega Evolution FORMS of Charizard SPECIES
forms = get_forms(species_id=6, variant_type="mega_evolution")
# Result: [MegaCharizardX, MegaCharizardY]
```

### In CLI:
```bash
# Generate all PDFs for a VARIANT
python scripts/generate_pdf.py --type variant --variant mega_evolution

# List all CATEGORIES
python scripts/generate_pdf.py --type variant --list

# Generate FORMS for a SPECIES
python scripts/generate_pdf.py --type variant --species charizard --variant mega_evolution
```

---

## ⚠️ Common Confusion Points (CLARIFY!)

### 1. "Variant list" - What is meant?
❌ **WRONG:** "List of 195 Variants"  
✅ **CORRECT:** "List of 195 Forms" or "9 Variants with a total of 195 Forms"

### 2. Species in Variant list
❌ **WRONG:** "87 Variants have Mega Evolution"  
✅ **CORRECT:** "87 Species have Mega Evolution Forms"

### 3. PDF binder structure
❌ **WRONG:** "Binder for 240 Variants"  
✅ **CORRECT:** "9 Binders for Variants" or "Binders for Forms of 240 Species"

---

## 🚀 Action Items

### IMMEDIATELY (before implementation):
1. [ ] Discuss these definitions with the team
2. [ ] Add glossary to project wiki/docs
3. [ ] Update code style guide (naming conventions)
4. [ ] Review & correct all existing docs

### Before Phase 1:
1. [ ] JSON Schema with correct field names
2. [ ] Variable names in Python (spec → variant, pokemon → species, etc.)
3. [ ] Consistent CLI help text

### Documentation:
1. [ ] Update README
2. [ ] Fix VARIANTS_TECHNICAL_SPEC.md
3. [ ] Update code comments with correct terminology

---

## 📌 FINAL Summary

| Term | Definition | Example |
|------|-----------|---------|
| **SPECIES** | Base Pokémon (Pokédex #) | Raichu, Charizard |
| **VARIANT** | Type of form change | Mega Evolution, Alolan Form |
| **FORM** | Concrete implementation | Mega Raichu, Alolan Raichu |
| **CATEGORY** | Our collection structure | Category 1: Mega Evolution |

**Use Case:**
> "The SPECIES Raichu has under the VARIANT 'Alolan Form' a FORM named 'Alolan Raichu'. This FORM is organized in CATEGORY 3."

---

**CRITICAL:** This clarity MUST be established BEFORE implementation!

