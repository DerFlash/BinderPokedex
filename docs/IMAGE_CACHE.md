# Image Cache Architecture

**Last Updated:** January 30, 2026  
**Purpose:** Document the URL-based image caching system for proper form variant handling

---

## Overview

The BinderPokedex uses a sophisticated image caching system to efficiently store Pokémon artwork while properly handling form variants (Mega X/Y, Primal, etc.). The system prevents cache collisions between base forms and their variants through URL-based cache keys.

### Cache Types

**1. Pokémon Artwork Cache** (`data/pokemon_images_cache/`)
- Form-specific cache with URL identifier differentiation
- Prevents collisions between base and variant forms
- Stores as `pokemon_{id}_{url_id}_{size}.jpg`

**2. External URL Cache** (`tempfile.gettempdir()`)
- MD5-based caching for external images (TCG logos, etc.)
- Temporary storage with automatic cleanup
- Used by logo_renderer for [image] tag support

## The Problem

**Before (Cache Collision):**
- Cache Key: `pokemon_{id}_{size}`
- Issue: Normal Charizard (ID 6, artwork URL .../6.png) and Mega Charizard X (ID 6, artwork URL .../10034.png) shared the same cache key
- Result: Wrong images displayed (Mega X showed normal Charizard)

**After (URL-Based Differentiation):**
- Cache Key: `pokemon_{id}_{url_identifier}_{size}`
- Solution: Extract unique identifier from image URL
- Result: Each form variant has its own cache files

---

## Architecture

### Cache Key Format

```
pokemon_{pokemon_id}_{url_identifier}_{size}
```

**Components:**
- `pokemon_id`: National Pokédex ID (1-1025)
- `url_identifier`: Unique identifier extracted from image URL
- `size`: Image dimensions (`thumb` = 180×180, `featured` = 500×500)

**Examples:**
- `pokemon_6_6_thumb` - Normal Charizard thumbnail
- `pokemon_6_10034_thumb` - Mega Charizard X thumbnail
- `pokemon_6_10035_thumb` - Mega Charizard Y thumbnail

### URL Identifier Extraction

#### PokeAPI URLs
Pattern: `https://raw.githubusercontent.com/PokeAPI/sprites/.../official-artwork/{id}.png`

```python
def _extract_url_identifier(url):
    # Extract: .../10034.png → "10034"
    return url.rstrip('/').split('/')[-1].replace('.png', '')
```

**IDs:**
- Normal Pokémon: 1-1025
- Mega Evolutions: 10033+ (e.g., 10034 = Mega Charizard X)
- Regional Forms: 10091+ (e.g., 10091 = Alolan Rattata)

#### TCGdex URLs
Pattern: `https://assets.tcgdex.net/en/sv1/013/high.webp`

```python
def _extract_url_identifier(url):
    # Extract: .../sv1/013/... → "sv1-013"
    parts = url.split('/')
    return f"{parts[-3]}-{parts[-2]}"
```

---

## Disk Cache Structure

```
data/pokemon_images_cache/
├── pokemon_6/
│   ├── 6_thumb.jpg           # Normal Charizard (5,896 bytes)
│   ├── 6_featured.jpg        # Normal Charizard (25,498 bytes)
│   ├── 10034_thumb.jpg       # Mega Charizard X (6,279 bytes)
│   ├── 10034_featured.jpg    # Mega Charizard X (25,450 bytes)
│   ├── 10035_thumb.jpg       # Mega Charizard Y (6,158 bytes)
│   └── 10035_featured.jpg    # Mega Charizard Y (25,302 bytes)
├── pokemon_150/
│   ├── 150_thumb.jpg         # Normal Mewtwo
│   ├── 150_featured.jpg      # Normal Mewtwo
│   ├── 10045_thumb.jpg       # Mega Mewtwo X
│   ├── 10045_featured.jpg    # Mega Mewtwo X
│   ├── 10046_thumb.jpg       # Mega Mewtwo Y
│   └── 10046_featured.jpg    # Mega Mewtwo Y
└── ...
```

**Directory Naming:** `pokemon_{pokemon_id}/`  
**File Naming:** `{url_identifier}_{size}.jpg`

---

## Implementation

### 1. Fetcher Pipeline (cache_pokemon_images.py)

**Purpose:** Pre-cache all images during data fetching

```python
class CachePokemonImagesStep(BaseStep):
    def _extract_url_identifier(self, url: str) -> str:
        """Extract unique identifier from image URL."""
        if not url:
            return "default"
        
        # PokeAPI: .../10034.png → "10034"
        if "raw.githubusercontent.com" in url or "pokeapi.co" in url:
            return url.rstrip('/').split('/')[-1].replace('.png', '')
        
        # TCGdex: .../sv1/013/... → "sv1-013"
        if "tcgdex.net" in url:
            parts = url.split('/')
            if len(parts) >= 3:
                return f"{parts[-3]}-{parts[-2]}"
        
        return "default"
    
    def _collect_pokemon_ids(self, data: Dict) -> Dict[str, tuple]:
        """Returns: {cache_key: (pokemon_id, image_url, url_identifier)}"""
        pokemon_ids_to_cache = {}
        
        for section in sections.values():
            for pokemon in section.get('pokemon', []):
                pokemon_id = pokemon['id']
                image_url = pokemon.get('image_url')
                url_identifier = self._extract_url_identifier(image_url)
                
                # Cache both sizes
                cache_key_thumb = f"pokemon_{pokemon_id}_{url_identifier}_thumb"
                cache_key_featured = f"pokemon_{pokemon_id}_{url_identifier}_featured"
                
                pokemon_ids_to_cache[cache_key_thumb] = (pokemon_id, image_url, url_identifier)
                pokemon_ids_to_cache[cache_key_featured] = (pokemon_id, image_url, url_identifier)
        
        return pokemon_ids_to_cache
```

### 2. PDF Generator (ImageCache class)

**Purpose:** Load cached images during PDF generation with RAM cache

```python
class ImageCache:
    def __init__(self, cache_dir: str, max_cache_size: int = 500):
        self.cache_dir = Path(cache_dir)
        self.ram_cache = {}  # LRU cache in memory
        self.max_cache_size = max_cache_size
    
    def _extract_url_identifier(self, url: str) -> str:
        """Same logic as fetcher for consistency."""
        # ... (identical implementation)
    
    def get_image(self, pokemon_id: int, image_url: str, size: tuple) -> Optional[ImageReader]:
        """Get cached image or download and cache it."""
        url_identifier = self._extract_url_identifier(image_url)
        size_str = "thumb" if size == self.CARD_SIZE else "featured"
        
        # Cache key for RAM
        cache_key = f"pokemon_{pokemon_id}_{url_identifier}_{size_str}"
        
        # Check RAM cache first
        if cache_key in self.ram_cache:
            return self.ram_cache[cache_key]
        
        # Check disk cache
        disk_path = self._get_cached_file(pokemon_id, url_identifier, size_str)
        if disk_path and disk_path.exists():
            img = ImageReader(str(disk_path))
            self._add_to_ram_cache(cache_key, img)
            return img
        
        # Download, process, and cache
        return self._download_and_cache(pokemon_id, image_url, url_identifier, size, size_str)
```

---

## Unified Caching Strategy

**Key Principle:** Fetcher and PDF generator use **identical** cache key generation logic

### Consistency Checks

1. **URL Identifier Extraction:**
   - Both implementations use same patterns
   - PokeAPI: Extract numeric ID from filename
   - TCGdex: Extract set-cardnumber combination

2. **Directory Structure:**
   - Both create: `pokemon_{id}/` directories
   - Both write: `{url_identifier}_{size}.jpg` files

3. **Cache Key Format:**
   - Both use: `pokemon_{id}_{url_identifier}_{size}`
   - Ensures fetcher-cached images are found by PDF generator

### Benefits

- **No Re-downloads:** PDF generator reuses fetcher-cached images
- **Form Separation:** Different variants never collide
- **Consistency:** Single source of truth for cache keys
- **Debuggability:** Filenames clearly show what they contain

---

## Mega Evolution Examples

### Charizard (ID 6)

| Form | URL ID | Cache File | PokeAPI ID |
|------|--------|------------|------------|
| Normal | 6 | `pokemon_6/6_thumb.jpg` | 6 |
| Mega X | 10034 | `pokemon_6/10034_thumb.jpg` | 10034 |
| Mega Y | 10035 | `pokemon_6/10035_thumb.jpg` | 10035 |

### Mewtwo (ID 150)

| Form | URL ID | Cache File | PokeAPI ID |
|------|--------|------------|------------|
| Normal | 150 | `pokemon_150/150_thumb.jpg` | 150 |
| Mega X | 10045 | `pokemon_150/10045_thumb.jpg` | 10045 |
| Mega Y | 10046 | `pokemon_150/10046_thumb.jpg` | 10046 |

### Groudon/Kyogre (Primal Reversion)

| Pokémon | Form | URL ID | Cache File | PokeAPI ID |
|---------|------|--------|------------|------------|
| Groudon | Normal | 383 | `pokemon_383/383_thumb.jpg` | 383 |
| Groudon | Primal | 10078 | `pokemon_383/10078_thumb.jpg` | 10078 |
| Kyogre | Normal | 382 | `pokemon_382/382_thumb.jpg` | 382 |
| Kyogre | Primal | 10077 | `pokemon_382/10077_thumb.jpg` | 10077 |

---

## Cache Statistics

From a complete fetch (January 2026):

```
Total Pokémon Entries: 1,439
  - Pokedex: 1,025
  - ExGen1: 94
  - ExGen2: 125 (including Mega/Primal variants)
  - ExGen3: 195 (including Mega variants)

Cache Files: 2,878 (1,439 × 2 sizes)
  - Thumbnails: 1,439 × 180×180px
  - Featured: 1,439 × 500×500px

Total Cache Size: ~45 MB
  - Average thumb: ~6 KB
  - Average featured: ~25 KB
```

---

## Troubleshooting

### Problem: Wrong image displayed for form variant

**Diagnosis:**
```bash
# Check cache files
ls -la data/pokemon_images_cache/pokemon_6/

# Expected: Multiple files (6, 10034, 10035)
# If only one file exists: Cache collision occurred
```

**Solution:** Delete cache and regenerate
```bash
rm -rf data/pokemon_images_cache/pokemon_6/
python scripts/fetcher/fetch.py --scope ExGen3
```

### Problem: Cache files not reused by PDF generator

**Diagnosis:**
- Check that both fetcher and PDF generator use same `_extract_url_identifier()` logic
- Verify cache key format matches in both implementations

**Solution:** Ensure code consistency in:
- `scripts/fetcher/steps/cache_pokemon_images.py`
- `scripts/pdf/lib/pdf_generator.py` (ImageCache class)

---

## Migration Notes

### From Old Format (v4.2 and earlier)

**Old Files:** `data/pokemon_images_cache/pokemon_6/default_thumb.jpg`  
**New Files:** `data/pokemon_images_cache/pokemon_6/6_thumb.jpg`, `10034_thumb.jpg`, etc.

**Migration Steps:**
1. Delete old cache: `rm -rf data/pokemon_images_cache/`
2. Re-fetch data: `python scripts/fetcher/fetch.py --scope <all>`
3. Verify: Check that form variants have separate cache files

**No Data Loss:** All images can be re-downloaded from APIs

---

## Future Enhancements

- **Cache Versioning:** Add version to cache directory for easier migrations
- **Cache Validation:** Verify file integrity (checksums)
- **Selective Cache Clearing:** Clear only specific Pokémon or sizes
- **Cache Compression:** Use WebP format for smaller file sizes
- **Cache Statistics Tool:** Report cache size, usage, missing entries
