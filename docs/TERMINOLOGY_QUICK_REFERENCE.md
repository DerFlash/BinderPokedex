# 🔑 Quick Terminology Reference Card

**For quick term clarification**

---

## 📚 The 4 Levels (HIERARCHY)

```
┌─────────────────────────────────────────────────────┐
│ LEVEL 1: SPECIES                                    │
│ = The base Pokémon by Pokédex number                │
│ Example: Raichu (#026), Charizard (#006)           │
│ Count: 1,025 (all 9 generations)                    │
│ Immutable: Yes                                       │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ LEVEL 2: VARIANT                                    │
│ = The category/type of form change (mechanic)       │
│ Example: "Mega Evolution", "Alolan Form"           │
│ Count: 9 (our categories)                           │
│ Properties: Name, Icon, Gen, Description            │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ LEVEL 3: FORM                                       │
│ = The concrete appearance of a Species              │
│ Example: "Alolan Raichu", "Mega Charizard X"      │
│ Count: ~195 different forms                         │
│ Properties: Image, Stats, Types, Moveset            │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ LEVEL 4: CATEGORY                                   │
│ = Our collection structure for PDF binders          │
│ Example: "Category 1: Mega Evolution"              │
│ Count: 9 (structured for output)                    │
│ Used in: CLI, PDF generation, UI                    │
└─────────────────────────────────────────────────────┘
```

---

## ✅ Correct / ❌ Wrong

| Statement | Correct? | Explanation |
|-----------|----------|-----------|
| "Mega Evolution is a Form" | ❌ | No, it's a VARIANT (form change category) |
| "There are 96 Forms in Mega Evolution" | ✅ | Yes - 87 Species × 1-2 Forms = 96 Forms |
| "Raichu is a Species" | ✅ | Yes - Base Pokémon #026 |
| "Alolan Raichu is a Variant" | ❌ | No, it's a FORM (under VARIANT "Alolan") |
| "Charizard has 2 Variants" | ❌ | No, Charizard (1 Species) has multiple FORMS under the VARIANT "Mega Evolution" |
| "There are 9 Variants" | ✅ | Yes - Mega, Gigantamax, Alolan, Galarian, Hisuian, Paldean, Primal/Terastal, Patterns, Fusion |
| "240+ Species have Forms" | ✅ | Yes - of the 1,025 Species, ~240 have a Variant |

---

## 🎯 Concrete Examples

### Example 1: Raichu (Alolan)
```
SPECIES:   Raichu (#026)
VARIANT:   Alolan Form
FORM:      Alolan Raichu
           ├─ Types: Electric/Psychic
           ├─ Image: alolan_raichu.png
           └─ Stats: Custom
CATEGORY:  Category 3: Alolan Forms
```

### Example 2: Charizard (Mega)
```
SPECIES:     Charizard (#006)
VARIANT:     Mega Evolution
FORMS (2):   
  ├─ Mega Charizard X
  │  ├─ Types: Fire/Dragon
  │  └─ Stats: Boosted
  │
  └─ Mega Charizard Y
     ├─ Types: Fire/Flying
     └─ Stats: Boosted

CATEGORY:    Category 1: Mega Evolution
```

### Example 3: Pikachu (Gigantamax)
```
SPECIES:   Pikachu (#025)
VARIANT:   Gigantamax
FORM:      Gigantamax Pikachu
           ├─ Size: Enormous
           └─ G-Max Move: G-Max Volt Crash
CATEGORY:  Category 2: Gigantamax
```

---

## 💬 Using in Code

### ✅ CORRECT
```python
# Get all FORMS of Charizard under Mega Evolution VARIANT
def get_forms(species: str, variant: str) -> List[Form]:
    """Returns all Forms of a Species in a Variant"""
    pass

# Get all SPECIES under Alolan VARIANT  
def get_species_by_variant(variant: str) -> List[Species]:
    """Returns all Species with Forms in this Variant"""
    pass

# Iterate through CATEGORIES
for category in VARIANT_CATEGORIES:  # 9 categories
    for variant in category.variants:  # VARIANTS in category
        for species_id in variant.species_list:  # SPECIES with this variant
            for form in get_forms(species_id, variant.type):  # FORMS of species
                generate_pdf(form)
```

### ❌ WRONG
```python
# Confusing variable names
forms = get_variants()  # What? Variants or Forms?
variants = get_pokemon()  # Confusing!
pokemon_variants = data['forms']  # Mixed up!
```

---

## 📝 Writing in Documentation

### ✅ CORRECT
```markdown
**Mega Evolution** is a VARIANT under which ~87 SPECIES 
have a total of 96 different FORMS.

For example, the SPECIES Charizard has two FORMS 
under this VARIANT: Mega Charizard X and Y.

These FORMS are organized in CATEGORY 1.
```

### ❌ WRONG
```markdown
The Pokémon Variants are 95 Forms...
There are 9 Species with Mega Evolution...
Charizard is a Variant...
```

---

## 🎓 Memory Aids

**SPECIES** = The base Pokémon  
**VARIANT** = THE TYPE of transformation (Mega, Alolan, Gigantamax, etc.)  
**FORM** = HOW it looks (the concrete result)  
**CATEGORY** = How we structure it (for binders/PDFs)

---

## 📊 Number Chart

| Level | Term | Count | Example |
|-------|------|-------|---------|
| 1 | Species | 1,025 | Raichu, Charizard, Pikachu |
| 2 | Variant | 9 | Mega Evolution, Alolan Form, ... |
| 3 | Form | ~195 | Alolan Raichu, Mega Charizard X, ... |
| 4 | Category | 9 | Cat 1: Mega, Cat 2: Gigantamax, ... |

---

## 🚀 For Implementation

**JSON Structure:**
```json
{
  "category_id": 1,
  "category_name": "Mega Evolution",
  "variant_type": "mega_evolution",
  "pokemon": [
    {
      "species_id": 3,
      "species_name": "Venusaur",
      "form_name": "Mega Venusaur",
      "form_id": "mega_003",
      "image_url": "..."
    }
  ]
}
```

**CLI Commands:**
```bash
# List all CATEGORIES
--list-categories

# Generate PDFs for a VARIANT
--variant mega_evolution

# For a specific SPECIES under VARIANT
--species charizard --variant mega_evolution

# All FORMS of a SPECIES across all VARIANTS
--species raichu --all-variants
```

---

**GOLDEN RULE:**  
✨ **1 SPECIES → Multiple VARIANTS → Multiple FORMS per VARIANT** ✨

When this hierarchy is clear, the entire implementation is clear! 🎯

