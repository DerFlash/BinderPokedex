# Variant Image Sourcing

## Current Solution ✅

Mega Evolution forms now display **correct form-specific artwork** using a hybrid approach:

### Image Source Strategy (Fallback Chain)

1. **PokeAPI Official Mega-Form-IDs** (Primary)
   - For Pokémon with dedicated Mega-Form-IDs in PokeAPI
   - Examples: Charizard, Mewtwo, Gengar, Rayquaza
   - Source: Official artwork from PokeAPI
   - Result: Distinct images for X/Y forms ✅

2. **Bulbapedia Scraping** (Fallback)
   - For Pokémon without dedicated Mega-Form-IDs
   - Examples: Raichu, Alakazam, Gengar, etc.
   - Source: Dynamic scraping of Bulbapedia pages
   - Result: Form-specific images from community database ✅
   - No WAF blocking (unlike Pokemon.com)

3. **Manual Override Mapping** (Edge Cases)
   - Pre-configured URLs in `MEGA_FORM_IMAGES` dict
   - Use for problematic or special cases
   - Format: `(pokemon_id, form_suffix): url`

### Logo System ✅

**Location:** `data/variants/logos/`

**Structure:**
```
logos/
  ├── mega_evolution/       # Localized Mega Evolution TCG logos
  │   ├── de.png          # German: "MEGA"
  │   ├── en.png          # English: "MEGA"
  │   ├── fr.png          # French: "MEGA"
  │   ├── es.png          # Spanish: "MEGA"
  │   ├── it.png          # Italian: "MEGA"
  │   ├── ja.png          # Japanese: "メガ"
  │   ├── ko.png          # Korean: "메가"
  │   ├── zh_hans.png     # Chinese Simplified: "超级"
  │   └── zh_hant.png     # Chinese Traditional: "超級"
  ├── ex/
  │   └── default.png     # EX logo (not localized)
  ├── ex_new/
  │   └── default.png     # EX New logo (not localized)
  ├── ex_tera/
  │   └── default.png     # EX Tera logo (not localized)
  └── m_pokemon/
      └── default.png     # M Pokémon logo (not localized)
```

**Token System:**
- `[MEGA]` - Renders localized Mega Evolution logo
- `[EX]` - Renders EX logo
- `[EX_NEW]` - Renders EX New logo (Scarlet & Violet era)
- `[EX_TERA]` - Renders EX Tera logo
- `[M]` - Renders M Pokémon logo

**Fallback Chain:**
1. Try localized logo: `logos/{type}/{language}.png`
2. Try default logo: `logos/{type}/default.png`
3. Try legacy location: `data/variants/{legacy_filename}.png`

**Implementation:** `scripts/lib/rendering/logo_renderer.py`

### Implementation Details

**File:** [mega_evolution_fetcher.py](../../scripts/lib/form_fetchers/mega_evolution_fetcher.py)

**Method:** `_get_form_specific_image(pokemon_id, mega_name, form_suffix)`

```python
# Strategy 1: Query PokeAPI for Mega-Form species with own ID
try:
    # Fetch pokemon-species/{id}, find Mega varieties
    # Extract mega_form_id from URL (e.g., 10034 for Charizard X)
    # Get official-artwork URL
    return (artwork_url, mega_form_id)

# Strategy 2: Check manual mapping (MEGA_FORM_IMAGES)
# Return curated URL if available

# Strategy 3: Fallback - Fetch from Bulbapedia directly
# Extract base name, fetch Bulbapedia page
# Regex: <img alt="Mega <name> <X|Y>" src="...bulbagarden...">
# Optimize URL: convert thumbnail to full resolution
# Return (optimized_url, None)
```

### Bulbapedia URL Optimization

- **Original**: `.../thumb/x/xy/filename/110px-filename`
- **Optimized**: `.../upload/x/xy/filename` (full resolution)

## Results

### Verified Working ✅

- **Raichu X vs Y**: Different Bulbapedia images
- **Charizard X vs Y**: Different PokeAPI official artwork
- **Mewtwo X vs Y**: Different PokeAPI official artwork
- **Gengar Mega**: Correct PokeAPI artwork
- **Rayquaza Mega**: Correct PokeAPI artwork
- Total: **76 Pokémon, 79 Mega forms** with distinct imagery

### PDF Generation

- All variant PDFs generated with form-specific images
- 9 languages supported
- Performance: ~15 seconds per language (optimized)

## Architecture Benefits

1. ✅ **No hardcoded heuristics** - Uses actual form data
2. ✅ **No WAF blocking** - Bulbapedia works, Pokemon.com doesn't
3. ✅ **No manual form-index mapping** - Dynamic discovery
4. ✅ **Scalable** - Works for any new Pokémon/forms
5. ✅ **Maintainable** - Clean fallback chain

## Removed Obsolete Files

- ❌ `pokemon_form_index_mapping.json` - Unreliable hardcoded mappings
- ❌ `scrape_bulbapedia.py` - Integrated into fetcher
- ❌ `scrape_form_indices.py` - Pokemon.com form index detection (failed)
- ❌ `test_*.py` - Test scripts for failed approaches

## Future Improvements

- [ ] Cache Bulbapedia responses to reduce API calls
- [ ] Pre-scrape all Bulbapedia forms at startup
- [ ] Add image quality/resolution selector
- [ ] Support Gigantamax and regional variants
- [ ] Add form labels (X, Y, Attack, Defense, etc.)
