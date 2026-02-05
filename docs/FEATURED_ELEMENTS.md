# 🎴 Featured Elements

## Overview

Featured Elements is a visual enhancement system that displays 3 iconic Pokémon cards or artwork on each section cover page. The system automatically selects the most important/famous Pokémon and fetches appropriate visual content based on the scope type.

## Visual Examples

### TCG Sets
TCG scopes display actual trading card images from TCGdex:
- **Portrait format** (400×550px)
- High-quality card scans
- Positioned at the bottom of section covers

### National Pokédex
Pokédex scopes display official Pokémon artwork from PokeAPI:
- **Square format** (475×475px)
- Official game artwork
- Generation starters featured

## How It Works

### 1. Priority-Based Selection

Pokémon are ranked by importance using a predefined priority system:

| Priority | Category | Examples |
|----------|----------|----------|
| **100** | Mascots, Cover Legendaries | Pikachu, Mewtwo, Rayquaza, Zacian |
| **95-98** | Major Legendaries | Articuno, Lugia, Dialga, Reshiram |
| **90-95** | Pseudo-Legendaries, Starters (final) | Dragonite, Garchomp, Charizard |
| **0-90** | Regular Pokémon | Most other species |

The top 3 Pokémon per section are automatically selected.

### 2. Content Sources (Auto-Detected)

#### TCG Card Formats

**ExGen Format** (Classic ex series)
```json
{
  "pokemon_id": 150,
  "tcg_card": {
    "id": "ex1-101",
    "set": {"name": "Ruby & Sapphire"},
    "image": "https://assets.tcgdex.net/..."
  }
}
```

**TCG-Set Format** (Modern sets: ME*, SV*)
```json
{
  "pokemon_id": 906,
  "localId": "001",
  "name": {"en": "Sprigatito"}
}
```

**Pokédex Format** (National Pokédex)
```json
{
  "pokemon_id": 1,
  "image_url": "https://raw.githubusercontent.com/PokeAPI/...",
  "name": {"en": "Bulbasaur"}
}
```

### 3. Image Fetching & Caching

**TCGdex Images:**
- Format: `https://assets.tcgdex.net/en/{series}/{set_id}/{local_id}/high.png`
- Series auto-detected: `sv`, `me`, `swsh`, `xy`, `bw`, `ex`, etc.
- Cached in `data/section_artwork/`

**PokeAPI Fallback:**
- Format: `https://raw.githubusercontent.com/PokeAPI/sprites/.../official-artwork/{id}.png`
- Used when TCG images unavailable (e.g., MEP set)
- Seamless fallback with logging

### 4. Unified Data Structure

All featured elements use the same structure regardless of source:

```json
{
  "pokemon_id": 150,
  "pokemon_name": "Mewtwo",
  "card_id": "ex1-101",
  "set_name": "Ruby & Sapphire",
  "image_url": "https://assets.tcgdex.net/...",
  "local_image_path": "data/section_artwork/pokemon_150_ex1-101.png",
  "rarity": "Rare Holo ex",
  "hp": "100"
}
```

## Configuration

### Pipeline Step

Add to any scope's YAML configuration:

```yaml
- step: enrich_featured_elements
  params:
    max_cards: 3           # Number of elements per section (default: 3)
    force: false           # Force regeneration (default: false)
    cache_dir: data/section_artwork  # Image cache directory
```

### Placement in Pipeline

**For TCG Sets:**
```yaml
pipeline:
  - step: fetch_tcgdex_set
  - step: transform_tcg_set
  - step: transform_to_sections_format
  - step: enrich_featured_elements  # After transform
  - step: save_output
```

**For Pokédex:**
```yaml
pipeline:
  - step: group_by_generation
  - step: enrich_featured_elements  # After grouping
  - step: save_output
```

## Scope Coverage

### ✅ Fully Supported (24/25 scopes)

| Scope | Featured Elements | Source |
|-------|-------------------|--------|
| **Pokédex** | 9 generations × 3 starters | PokeAPI artwork |
| **ExGen1** | Mewtwo, Mew, Lugia | TCGdex (ex series) |
| **ExGen2** | Dialga, Palkia, Giratina | TCGdex (bw/xy) |
| **ExGen3** | Rayquaza, Groudon, Kyogre | TCGdex (sv ex) |
| **ME01** | Bulbasaur, Chikorita, Celebi | TCGdex |
| **ME02** | Charizard, Blastoise, Venusaur | TCGdex |
| **ME02.5** | Alakazam, Gengar, Machamp | TCGdex |
| **MEP** | Riolu, Meganium, Inteleon | PokeAPI fallback |
| **SV01-SV10** | Gen 9 starters + legendaries | TCGdex |
| **SVP** | Sprigatito, Fuecoco, Quaxly | TCGdex |
| **Special Sets** | Varies by set | TCGdex |

### ⚠️ Limited Support (1/25 scopes)

| Scope | Status | Reason |
|-------|--------|--------|
| **MEP** | PokeAPI fallback | TCGdex has no images for this set |

## Technical Architecture

### Format Detection Logic

```python
def _fetch_card_image_from_any_card(pokemon_id, card, cache_dir, set_info):
    # 1. Check for ExGen format (tcg_card sub-object)
    if 'tcg_card' in card and card['tcg_card']:
        return _fetch_card_image_from_exgen_card(...)
    
    # 2. Check for TCG-Set format (localId + set_info)
    elif 'localId' in card and set_info:
        return _fetch_card_image_from_tcg_set_card(...)
    
    # 3. Check for Pokédex format (image_url from PokeAPI)
    elif 'image_url' in card:
        return _fetch_card_image_from_pokedex_card(...)
    
    # 4. Unknown format
    else:
        return None
```

### Fallback Chain

For TCG-Set cards:
```
1. Try TCGdex image URL
   ↓ (404 Not Found)
2. Try PokeAPI official artwork
   ↓ (Success)
3. Cache as fallback variant
   ↓
4. Return element data
```

### Caching Strategy

**Cache File Naming:**
- TCG: `pokemon_{id}_{card_id}.png` (e.g., `pokemon_150_ex1-101.png`)
- Fallback: `pokemon_{id}_{card_id}_fallback.png`
- Pokédex: `pokemon_{id}_pokedex.png`

**Cache Size:**
- TCG cards: ~800KB-1MB per image
- Pokédex artwork: ~400-600KB per image
- Total for 25 scopes: ~50-100MB

## CLI Usage

### Force Regeneration

```bash
# Regenerate featured elements for specific scope
python scripts/fetcher/fetch.py --scope Pokedex --skip-fetch --force-featured-cards

# Regenerate for all scopes
python scripts/fetcher/fetch.py --scope all --skip-fetch --force-featured-cards
```

### Check Results

```bash
# View featured elements in JSON
jq '.sections.gen1.featured_elements' data/output/Pokedex.json

# Check cache directory
ls -lh data/section_artwork/pokemon_*_pokedex.png
```

## PDF Rendering

### Cover Layout

Featured elements are rendered at the bottom of section cover pages:

- **Position:** 35mm from bottom
- **Size:** 45mm × 63mm per element
- **Spacing:** 8-10mm between elements
- **Alignment:** Centered horizontally
- **Max:** 3 elements per cover

### Aspect Ratio Handling

- **TCG cards:** Portrait orientation preserved
- **Pokédex artwork:** Square format, scaled proportionally
- **preserveAspectRatio:** Always enabled

## Troubleshooting

### No Featured Elements Generated

**Possible causes:**
1. No Pokémon with priority > 0 in section
2. Image download failures (check network)
3. Missing `set_info` for TCG-Set cards

**Solutions:**
- Check priority rankings in `FEATURED_POKEMON_PRIORITY`
- Verify API accessibility (TCGdex, PokeAPI)
- Ensure scope config includes proper set metadata

### Images Not Displaying in PDF

**Possible causes:**
1. Cache file missing or corrupted
2. File path incorrect in JSON
3. Image format incompatible

**Solutions:**
- Delete cache and regenerate: `rm data/section_artwork/pokemon_*`
- Re-run with `--force-featured-cards`
- Check `local_image_path` in output JSON

### Wrong Pokémon Selected

**Cause:**
- Priority rankings need adjustment for specific scope

**Solution:**
- Update `FEATURED_POKEMON_PRIORITY` dict in `enrich_featured_cards.py`
- Increase priority for desired Pokémon (0-100 scale)

## Future Enhancements

### Planned Features
- [ ] Custom priority overrides per scope in YAML config
- [ ] Support for 1-5 elements (currently fixed at 3)
- [ ] Variant-specific featured elements (Mega, Gmax, etc.)
- [ ] Alternative layouts (grid, horizontal)
- [ ] User-selectable featured elements via config

### API Considerations
- TCGdex completeness varies by set
- PokeAPI fallback ensures universal support
- Image quality consistent across sources

## Contributing

### Adding New Card Format

1. Create handler method: `_fetch_card_image_from_{format}_card()`
2. Add detection logic to `_fetch_card_image_from_any_card()`
3. Implement image URL construction
4. Add tests for new format

### Adjusting Priorities

Edit `FEATURED_POKEMON_PRIORITY` dict:
```python
FEATURED_POKEMON_PRIORITY = {
    1: 100,   # Bulbasaur - Starter
    150: 100, # Mewtwo - Legendary
    # ... add more
}
```

## References

- **TCGdex API:** https://api.tcgdex.net/v2/en
- **PokeAPI:** https://pokeapi.co/api/v2
- **Implementation:** `scripts/fetcher/steps/enrich_featured_cards.py`
- **Renderer:** `scripts/pdf/lib/rendering/cover_renderer.py`
