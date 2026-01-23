# Featured Pokémon Documentation

## Overview

Featured Pokémon are displayed at the bottom of cover pages for both Pokédex generations and variant collections. They serve as iconic representatives for each collection and must be carefully selected based on availability and thematic appropriateness.

## Critical Requirements

### 1. **Availability Requirement** ⚠️ MANDATORY
Featured Pokémon **MUST exist** in the section's `pokemon` array. The rendering system searches for featured IDs within the section's Pokémon list:
- If a featured ID is not found → **Pokémon will not render**
- This is by design - only Pokémon actually in the collection can be featured

### 2. **Maximum Count**
- Each section can have **2-3 featured Pokémon**
- Displayed as cards at the bottom of the cover page
- Automatically centered on the page

### 3. **Thematic Appropriateness**
Featured Pokémon should:
- Represent the theme/purpose of the section
- Be recognizable and "cool" choices
- Avoid excessive duplication across sections (when possible)

## Selection Criteria

When selecting featured Pokémon for a section:

1. **Check Availability First**
   ```python
   # Example: Check if IDs exist in section
   pokemon_ids = [p['id'] for p in section['pokemon']]
   featured = [150, 144, 145]  # Proposed IDs
   all_exist = all(fid in pokemon_ids for fid in featured)
   ```

2. **Prioritize by Category**
   - Legendary/Mythical Pokémon (if available)
   - Pseudo-Legendary Pokémon (600 base stat total)
   - Popular/Iconic Pokémon (starters, mascots)
   - Thematically relevant Pokémon

3. **Avoid Over-representation**
   - Don't use the same Pokémon across too many sections
   - Acceptable duplicates: 2-3 times max
   - Current duplicates:
     - Mewtwo (150): 2× (Rockets, Mega) - justified by theme
     - Garchomp (445): 2× (EX Gen3 Normal, Tera) - limited options
     - Charizard (6): Only in Mega Evolution variant

## Current Configuration

### Pokédex Generations

| Generation | IDs | Pokémon | Rationale |
|------------|-----|---------|-----------|
| **Gen 1** (Kanto) | `[25, 6, 150]` | Pikachu, Charizard, Mewtwo | Mascot + most popular + legendary |
| **Gen 2** (Johto) | `[249, 250, 251]` | Lugia, Ho-Oh, Celebi | Tower Duo + mythical |
| **Gen 3** (Hoenn) | `[384, 383, 382]` | Rayquaza, Groudon, Kyogre | Weather Trio |
| **Gen 4** (Sinnoh) | `[483, 484, 487]` | Dialga, Palkia, Giratina | Creation Trio |
| **Gen 5** (Unova) | `[643, 644, 646]` | Reshiram, Zekrom, Kyurem | Tao Trio (complete) |
| **Gen 6** (Kalos) | `[716, 717, 718]` | Xerneas, Yveltal, Zygarde | Aura Trio |
| **Gen 7** (Alola) | `[791, 792, 800]` | Solgaleo, Lunala, Necrozma | Light Trio (complete) |
| **Gen 8** (Galar) | `[888, 889, 890]` | Zacian, Zamazenta, Eternatus | Hero Duo + antagonist |
| **Gen 9** (Paldea) | `[1007, 1008, 1024]` | Koraidon, Miraidon, Terapagos | Legendary duo + mythical |

**Pattern:** Pokédex generations prioritize legendary trios/duos that define each generation's narrative.

### Variant Collections

#### EX Generation 1 (variants_ex_gen1.json)

| Section | IDs | Pokémon | Rationale |
|---------|-----|---------|-----------|
| **normal** | `[3, 6, 9]` | Venusaur, Charizard, Blastoise | Gen 1 starter trio - thematically perfect |
| **rockets** | `[150, 144, 145]` | Mewtwo, Articuno, Zapdos | Team Rocket legendaries from movies |
| **special** | `[295, 448]` | Exploud, Lucario | Only 2 unique Pokémon available in section |

**Rockets Note:** Original proposal was Team Rocket's signature Pokémon (Meowth, Arbok, Weezing), but these don't exist in the section. Selected legendaries tied to Team Rocket lore instead (Mewtwo from Giovanni, Birds from Movie 2000).

**Trainer Note:** Limited to 3 Pokémon total (Exploud, Lucario, Lucario) - only 2 unique choices available.

#### EX Generation 2 (variants_ex_gen2.json)

| Section | IDs | Pokémon | Rationale |
|---------|-----|---------|-----------|
| **normal** | `[249, 250, 251]` | Lugia, Ho-Oh, Celebi | Gen 2 legendary trio, fits "Next Destinies" theme |
| **mega** | `[248, 373, 384]` | Tyranitar, Salamence, Rayquaza | Powerful pseudo-legendaries with Mega forms |
| **primal** | `[382, 383]` | Kyogre, Groudon | Only 2 Pokémon in section - Primal Duo |

**Normal Note:** Original proposal was Gen 2 starters (Chikorita, Cyndaquil, Totodile), but they don't exist. Legendary trio is more appropriate for [EX] series.

#### EX Generation 3 (variants_ex_gen3.json)

| Section | IDs | Pokémon | Rationale |
|---------|-----|---------|-----------|
| **normal** | `[149, 445, 373]` | Dragonite, Garchomp, Salamence | Pseudo-legendary dragons from Gens 1, 4, 3 |
| **tera** | `[384, 445, 130]` | Rayquaza, Garchomp, Gyarados | Legendary + pseudo + fan favorite with Tera forms |
| **mega** | `[150, 65, 248]` | Mewtwo, Alakazam, Tyranitar | Iconic Pokémon with powerful Mega Evolutions |

**Normal Note:** Gen 3 starters not available. Chose diverse pseudo-legendaries.

**Tera Note:** Paradox Pokémon from Gen 9 not available. Selected Pokémon with notable Tera forms.

**Mega Note:** Gengar (94) not available despite being iconic Mega. Tyranitar substituted.

#### Mega Evolution (variants_mega.json)

| Section | IDs | Pokémon | Rationale |
|---------|-----|---------|-----------|
| **normal** | `[6, 150, 384]` | Charizard, Mewtwo, Rayquaza | Top 3 most iconic Mega Evolutions |

**Note:** Charizard has 2 Mega forms (X/Y), Mewtwo has 2 (X/Y), Rayquaza has Mega evolution.

## Update Process

When section contents change (new Pokémon added/removed):

### Step 1: Identify Changes
```bash
# Check current featured_pokemon configuration
grep -A 3 '"featured_pokemon"' data/pokemon.json data/variants/*.json
```

### Step 2: Verify Availability
```python
import json

# For each section, verify featured Pokémon exist
with open('data/variants/variants_ex_gen1.json') as f:
    data = json.load(f)
    for section_name, section in data['sections'].items():
        featured = section.get('featured_pokemon', [])
        pokemon_ids = [p['id'] for p in section['pokemon']]
        missing = [fid for fid in featured if fid not in pokemon_ids]
        if missing:
            print(f"Section {section_name}: Missing IDs {missing}")
```

### Step 3: Select Replacements
If Pokémon are missing:
1. List all available IDs in the section
2. Identify legendary/pseudo-legendary/popular Pokémon
3. Check for theme appropriateness
4. Avoid duplicates with other sections
5. Update `featured_pokemon` array

### Step 4: Test
```bash
# Generate PDFs to verify rendering
python scripts/generate_pdf.py --type variant --language de
```

## Technical Implementation

### Data Structure
```json
{
  "sections": {
    "section_name": {
      "featured_pokemon": [150, 144, 145],
      "pokemon": [
        {"id": 150, "name": {...}},
        {"id": 144, "name": {...}},
        // ... must contain all featured IDs
      ]
    }
  }
}
```

### Rendering Logic
Located in: `scripts/lib/rendering/featured_pokemon_renderer.py`

The renderer:
1. Loads `featured_pokemon` array from section
2. Searches for each ID in section's `pokemon` array
3. Loads featured-size images from cache
4. Renders up to 3 cards centered at bottom of cover

**Key Point:** If ID not found in pokemon array → **skipped silently** (no error, just not rendered)

## Field Naming History

- **2026-01-23:** Renamed from `iconic_pokemon` to `featured_pokemon` for clarity
- Previous references: `iconic_pokemon_ids`, `IconicPokemonRenderer`
- Current: `featured_pokemon`, `FeaturedPokemonRenderer`

## Validation Script

Create a validation script to check featured Pokémon:

```python
#!/usr/bin/env python3
"""Validate featured_pokemon configuration."""
import json
from pathlib import Path

def validate_featured_pokemon():
    """Check all featured_pokemon exist in their sections."""
    issues = []
    
    # Check Pokédex
    with open('data/pokemon.json') as f:
        data = json.load(f)
        for gen_name, gen_data in data['sections'].items():
            featured = gen_data.get('featured_pokemon', [])
            pokemon_ids = [p['id'] for p in gen_data.get('pokemon', [])]
            missing = [fid for fid in featured if fid not in pokemon_ids]
            if missing:
                issues.append(f"Pokédex {gen_name}: Missing {missing}")
    
    # Check Variants
    for variant_file in Path('data/variants').glob('*.json'):
        with open(variant_file) as f:
            data = json.load(f)
            for section_name, section in data['sections'].items():
                featured = section.get('featured_pokemon', [])
                pokemon_ids = [p['id'] for p in section.get('pokemon', [])]
                missing = [fid for fid in featured if fid not in pokemon_ids]
                if missing:
                    issues.append(f"{variant_file.name}/{section_name}: Missing {missing}")
    
    if issues:
        print("❌ Issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ All featured_pokemon are valid!")
        return True

if __name__ == '__main__':
    validate_featured_pokemon()
```

## References

- Rendering implementation: [scripts/lib/rendering/featured_pokemon_renderer.py](../scripts/lib/rendering/featured_pokemon_renderer.py)
- Cover rendering: [scripts/lib/rendering/cover_renderer.py](../scripts/lib/rendering/cover_renderer.py)
- Variant generator: [scripts/lib/variant_pdf_generator.py](../scripts/lib/variant_pdf_generator.py)
- Commit history: 
  - `feat: update featured_pokemon selections` (2026-01-23)
  - `fix: update featured_pokemon to use actually available Pokemon` (2026-01-23)
  - `refactor: rename iconic_pokemon to featured_pokemon` (2026-01-23)
