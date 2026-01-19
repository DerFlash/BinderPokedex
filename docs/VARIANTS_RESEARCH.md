# Pokémon Variants - Research & Planning Document

**Date:** January 19, 2026  
**Status:** Feature planning

---

## 1. Overview of Pokémon Variants

Based on Bulbapedia research, there are the following main categories of Pokémon variants:

### 1.1 Transformations & Dynamic Forms

These variants are **battle-bound** or **temporary**:

#### A) **Mega Evolution** (Gen VI+)
- **Introduction:** Pokémon X/Y (2013)
- **Current Count:** ~87 Pokémon with a total of 96 Mega forms
- **Characteristics:**
  - Charizard, Mewtwo: 2x Mega forms (X/Y)
  - Lucario, Absol: Z-Mega forms (Gen IX - Legends: Z-A)
  - **Total different forms:** 96
- **Sources:** Mega Stone + Key Stone (Gen VI/VII), Dragon Ascent (Rayquaza)
- **Status in Games:** Gen VI, VII, Legends: Z-A + DLC

#### B) **Primal Reversion** (Gen VI+)
- **Introduction:** Omega Ruby/Alpha Sapphire (2014)
- **Pokémon:** Kyogre, Groudon (2 forms)
- **Characteristic:** Red/Blue Orb as item
- **Status in Games:** Gen VI/VII, Legends: Z-A

#### C) **Gigantamax** (Gen VIII+)
- **Introduction:** Pokémon Sword/Shield (2019)
- **Current Count:** 32+ species with Gigantamax forms
- **Characteristics:**
  - Urshifu: 2 different Gigantamax forms
  - Flapple/Appletun: Share a Gigantamax form
  - Some can use G-Max Moves
- **Status in Games:** Sword/Shield, Isle of Armor, Legends: Z-A DLC

#### D) **Dynamax** (Gen VIII)
- **Count:** All Pokémon in certain zones
- **Characteristic:** Only size change, no form change (except Gigantamax)
- **Status:** Sword/Shield only

#### E) **Terastal Phenomenon** (Gen IX+)
- **Introduction:** Pokémon Scarlet/Violet (2022)
- **Count:** All Pokémon (anytime possible)
- **Characteristic:** Tera-type changeable (except Ogerpon, Terapagos)
- **Unique States:**
  - Ogerpon: 4 mask variants
  - Terapagos: Stellar form (unique)

---

### 1.2 Permanent Regional Variants

These variants are **permanent** and non-switchable:

#### A) **Alolan Forms** (Gen VII)
- **Region:** Alola
- **Count:** 18 Pokémon
- **Examples:** Alolan Raichu, Alolan Exeggutor, Alolan Vulpix
- **Characteristic:** Type changes possible
- **Status:** Sun/Moon, Ultra Sun/Ultra Moon, Let's Go Pikachu/Eevee, Sword/Shield (selected), Legends: Arceus, Scarlet/Violet

#### B) **Galarian Forms** (Gen VIII)
- **Region:** Galar
- **Count:** 16 Pokémon
- **Examples:** Galarian Meowth, Galarian Weezing, Galarian Rapidash
- **Characteristic:** New types & evolutions
- **Status:** Sword/Shield

#### C) **Hisuian Forms** (Gen VIII/IX)
- **Region:** Hisui (historical Sinnoh)
- **Count:** 15 Pokémon
- **Examples:** Hisuian Growlithe, Hisuian Zoroark, Hisuian Samurott
- **Characteristic:** New evolutions, alternative types
- **Status:** Legends: Arceus, Scarlet/Violet (selected)

#### D) **Paldean Forms** (Gen IX)
- **Region:** Paldea
- **Count:** 5+ Pokémon
- **Examples:** Paldean Wooper, Paldean Tauros (3 forms)
- **Characteristic:** Paldean Tauros has 3 forms (Normal, Water, Fire)
- **Status:** Scarlet/Violet

---

### 1.3 Gender Differences & Special Forms

#### A) **Gender Differences**
- **Count:** 102+ Pokémon with visual differences
- **Characteristics:**
  - Mostly cosmetic
  - Meowstic, Indeedee, Oinkologne: Different stats/moves
  - Basculegion: Different stats
- **Status:** Since Gen IV

#### B) **Shiny Pokémon**
- **Count:** Technically all
- **Characteristic:** Only color difference
- **Rarity:** 1/4000 (1/8000 before Gen V)

#### C) **Unique Individuals** (single specimens)
- Cosplay Pikachu (5 forms)
- Pikachu in Caps (various)
- Spiky-eared Pichu
- Ash-Greninja (Bond Phenomenon)
- Eternal Flower Floette
- Dada Zarude
- Bloodmoon Ursaluna

#### D) **Other Form Differences**
- **Unown:** 28 forms (A-Z + question mark + exclamation mark)
- **Vivillon:** 20 patterns
- **Castform:** 4 forms (weather-based)
- **Oricorio:** 4 forms (flower-based)

---

### 1.4 Fusion & Configurable Forms

#### A) **Pokémon Fusion**
- **Kyurem:** Black Kyurem, White Kyurem (absorption with Reshiram/Zekrom)
- **Necrozma:** Dusk Mane, Dawn Wings (attachment with Solgaleo/Lunala)
- **Calyrex:** Ice Rider, Shadow Rider (rides on Glastrier/Spectrier)

#### B) **Form Selection**
- Paldean Tauros: 3 base forms
- Urshifu: Single Strike vs. Rapid Strike
- Tornadus/Tornasus: Incarnate vs. Therian

---

## 2. Quantitative Overview

| Category | Number of Pokémon | Number of Forms |
|----------|------------------|-----------------|
| Mega Evolution | 87 | 96 |
| Primal Reversion | 2 | 2 |
| Gigantamax | 32+ | 32+ |
| Dynamax | All | (size only) |
| Terastal | All | (type-variable) |
| Alolan | 18 | 18 |
| Galarian | 16 | 16 |
| Hisuian | 15 | 15 |
| Paldean | 5+ | 8+ |
| **Gender Differences** | 102+ | (mostly cosmetic) |
| **Unique Individuals** | ~10 | ~20+ |

**Total Pokémon involved:** ~240+  
**Total different forms:** 200+

---

## 3. Feature Requirements

### 3.1 Data Structure

New category: **"Variants"** (similar to generations)

```json
{
  "variant_type": "mega",
  "variant_name": "Mega Evolution",
  "short_code": "mega",
  "icon": "⚡",
  "color": "#FF9900",
  "pokemon": [
    {
      "base_pokemon_id": 3,
      "base_pokemon_name": "Venusaur",
      "variant_name": "Mega Venusaur",
      "new_id": "mega_001",
      "types": ["Grass", "Poison"],
      "image_url": "...",
      "description": "..."
    }
  ]
}
```

### 3.2 Numbering Schema

For variants without official numbers:

**Format:** `{variant_code}_{base_id}_{variant_index}`

**Examples:**
- `mega_003_a` → Mega Venusaur
- `mega_006_a` → Mega Charizard X
- `mega_006_b` → Mega Charizard Y
- `giga_025_a` → Gigantamax Pikachu
- `alola_025_a` → Alolan Raichu

### 3.3 Categorization for Binders

Proposal: **9 separate variant binders** (analogous to 9 generations)

1. **Mega Evolution** (~96 forms)
2. **Gigantamax** (~32 forms)
3. **Regional Forms - Alola/Galar** (~34 forms)
4. **Regional Forms - Hisui/Paldea** (~20 forms)
5. **Primal Reversion & Terastal** (~2-X forms)
6. **Gender Differences & Unique Forms** (~50+ forms)
7. **Unown & Vivillon Patterns** (28 + 20 forms)
8. **Form Variations** (Castform, Oricorio, etc.)
9. **Fusion & Special Forms** (Kyurem, Necrozma, Calyrex)

---

## 4. Architecture Proposal

### 4.1 File Structure

```
/data
  /variants
    variants_mega.json (96 forms)
    variants_gigantamax.json (32 forms)
    variants_regional.json (68 forms: Alola, Galar, Hisui, Paldea)
    variants_primal_terastal.json
    variants_gender_unique.json
    variants_patterns.json (Unown, Vivillon)
    variants_forms.json (Castform, Oricorio, etc.)
    variants_fusion.json (Kyurem, Necrozma, Calyrex)
    variants_special.json (Other)
```

### 4.2 Generation

```bash
python scripts/generate_pdf.py --type variant --variant mega
python scripts/generate_pdf.py --type variant --variant gigantamax
python scripts/generate_pdf.py --type variant --variant regional
...
```

### 4.3 PDF Output

```
/output/{language}/
  variant_mega_cover.pdf
  variant_mega_pages.pdf
  variant_gigantamax_cover.pdf
  variant_gigantamax_pages.pdf
  ...
```

---

## 5. Implementation Phases

### Phase 1: Data & API
- [ ] Define variant JSON structure
- [ ] Fetch data from PokeAPI/Bulbapedia
- [ ] Data validation

### Phase 2: CLI & Configuration
- [ ] Extend `generate_pdf.py` with `--variant` argument
- [ ] Prepare config for all variants

### Phase 3: PDF Logic
- [ ] Adjust cover page for variants
- [ ] Implement numbering schema in PDF
- [ ] Multilingual support (like generations)

### Phase 4: Prioritization & Testing
- [ ] Start MVP with top 3 variants (Mega, Gigantamax, Regional)
- [ ] Complete generation & QA

---

## 6. Open Questions & Design Decisions

1. **Should variants be printed together or separately?**
   - Option A: Each variant → separate binder
   - Option B: All variants → 1 large collection binder
   - **Recommendation:** Option A (clearer structure)

2. **How do we handle Pokémon with multiple variants?**
   - Charizard has: Mega X, Mega Y, Gigantamax
   - **Solution:** List in correct category each time

3. **Use official numbering or custom?**
   - PokeAPI has partial variant IDs
   - **Recommendation:** Hybrid: official where available, custom otherwise

4. **Ordering within a variant?**
   - Sort by base Pokémon ID
   - **Example:** Mega Venusaur (#3), Mega Charizard (#6), ...

---

## 7. Sources & References

- **Bulbapedia:** https://bulbapedia.bulbagarden.net/wiki/Form
- **Mega Evolution:** https://bulbapedia.bulbagarden.net/wiki/Mega_Evolution
- **Gigantamax:** https://bulbapedia.bulbagarden.net/wiki/Gigantamax
- **Regional Forms:** https://bulbapedia.bulbagarden.net/wiki/Regional_form

---

**Next Steps:**
1. Discuss categorization with user (9 vs. other division?)
2. Test data fetching from PokeAPI
3. Start MVP phase (Mega Evolution as proof of concept)
