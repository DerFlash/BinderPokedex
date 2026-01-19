#!/usr/bin/env python3
"""
Cache Pokémon images locally for fast PDF generation.

This script downloads and caches the image for each Pokémon (one per Pokémon from JSON),
storing them as compressed JPEGs to minimize storage while maintaining quality.

Run once to populate cache, then PDF generation will be ~100x faster.
"""

import sys
import json
import logging
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from PIL import Image
from io import BytesIO

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add scripts/lib to path
sys.path.insert(0, str(Path(__file__).parent))
from lib.constants import GENERATION_INFO

# Configuration
CACHE_DIR = Path(__file__).parent.parent / 'data' / 'pokemon_images_cache'
DATA_DIR = Path(__file__).parent.parent / 'data'
TIMEOUT = 5
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'


def ensure_directory(pokemon_id: int) -> Path:
    """Create directory for a Pokémon."""
    pokemon_dir = CACHE_DIR / f'pokemon_{pokemon_id}'
    pokemon_dir.mkdir(parents=True, exist_ok=True)
    return pokemon_dir


def fetch_image_url(url: str) -> bytes | None:
    """Fetch image from URL."""
    try:
        headers = {'User-Agent': USER_AGENT}
        req = Request(url, headers=headers)
        with urlopen(req, timeout=TIMEOUT) as response:
            return response.read()
    except Exception:
        return None


def is_valid_image(image_data: bytes) -> bool:
    """Validate image data."""
    try:
        img = Image.open(BytesIO(image_data))
        img.verify()
        return True
    except Exception:
        return False


def process_and_cache_image(image_data: bytes, pokemon_id: int) -> bool:
    """Convert to JPEG and cache."""
    try:
        img = Image.open(BytesIO(image_data))
        
        # Convert to RGB (remove alpha, handle transparent backgrounds)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Save as compressed JPEG
        pokemon_dir = ensure_directory(pokemon_id)
        output_file = pokemon_dir / 'default.jpg'
        img.save(output_file, format='JPEG', quality=85, optimize=True)
        return True
    except Exception as e:
        logger.warning(f"  Failed to process image for #{pokemon_id}: {e}")
        return False


def cache_pokemon_image(pokemon_id: int, image_url: str) -> bool:
    """Cache a single Pokémon image."""
    pokemon_dir = ensure_directory(pokemon_id)
    cached_file = pokemon_dir / 'default.jpg'
    
    # Check if already cached
    if cached_file.exists():
        return True
    
    # Download and cache
    image_data = fetch_image_url(image_url)
    if image_data and is_valid_image(image_data):
        if process_and_cache_image(image_data, pokemon_id):
            return True
    
    return False


def cache_all_pokemon():
    """Cache all Pokémon from all generations."""
    logger.info("="*80)
    logger.info("Binder Pokédex - Simple Image Cache Builder")
    logger.info("="*80)
    logger.info(f"Cache directory: {CACHE_DIR}\n")
    
    total_pokemon = 0
    cached_count = 0
    failed_count = 0
    
    # Process each generation
    for gen_num in sorted(GENERATION_INFO.keys()):
        gen_info = GENERATION_INFO[gen_num]
        region = gen_info['region']
        
        logger.info(f"Generation {gen_num} - {region}")
        
        # Load JSON for this generation
        json_file = DATA_DIR / f'pokemon_gen{gen_num}.json'
        if not json_file.exists():
            logger.warning(f"  ✗ File not found: {json_file}")
            continue
        
        try:
            with open(json_file) as f:
                pokemon_list = json.load(f)
        except Exception as e:
            logger.error(f"  ✗ Failed to load {json_file}: {e}")
            continue
        
        gen_cached = 0
        gen_failed = 0
        
        for pokemon in pokemon_list:
            pokemon_id = pokemon.get('id')
            image_url = pokemon.get('image_url')
            
            if not pokemon_id or not image_url:
                continue
            
            total_pokemon += 1
            
            if cache_pokemon_image(pokemon_id, image_url):
                cached_count += 1
                gen_cached += 1
            else:
                failed_count += 1
                gen_failed += 1
                logger.debug(f"    ✗ Failed to cache #{pokemon_id}")
        
        logger.info(f"  ✓ {gen_cached} cached, {gen_failed} failed\n")
    
    # Process variants (e.g., Mega Evolution)
    variants_dir = DATA_DIR / 'variants'
    if variants_dir.exists():
        for variant_file in sorted(variants_dir.glob('variants_*.json')):
            logger.info(f"Variant: {variant_file.stem}")
            
            try:
                with open(variant_file) as f:
                    variant_data = json.load(f)
            except Exception as e:
                logger.error(f"  ✗ Failed to load {variant_file}: {e}")
                continue
            
            pokemon_list = variant_data.get('pokemon', [])
            var_cached = 0
            var_failed = 0
            
            for pokemon in pokemon_list:
                # Use mega_form_id if available, otherwise use pokemon_form_cache_id (for Pokemon.com forms)
                # Otherwise use pokemon_id from ID
                pokemon_id = pokemon.get('mega_form_id') or pokemon.get('pokemon_form_cache_id')
                if not pokemon_id:
                    pokemon_id = pokemon.get('id')
                    if isinstance(pokemon_id, str):
                        pokemon_id = int(pokemon_id.lstrip('#').split('_')[0])
                
                image_url = pokemon.get('image_url')
                
                if not pokemon_id or not image_url:
                    continue
                
                total_pokemon += 1
                
                if cache_pokemon_image(pokemon_id, image_url):
                    cached_count += 1
                    var_cached += 1
                else:
                    failed_count += 1
                    var_failed += 1
                    logger.debug(f"    ✗ Failed to cache #{pokemon_id}")
            
            logger.info(f"  ✓ {var_cached} cached, {var_failed} failed\n")
    
    # Summary
    logger.info(f"{'='*80}")
    logger.info("Cache Summary")
    logger.info(f"{'='*80}")
    logger.info(f"Total Pokémon/Forms: {total_pokemon}")
    logger.info(f"Successfully cached: {cached_count}")
    logger.info(f"Failed: {failed_count}")
    
    total_size = sum(f.stat().st_size for f in CACHE_DIR.rglob('*.jpg')) / 1024 / 1024
    logger.info(f"Cache size: {total_size:.1f} MB")
    
    logger.info(f"\nCache location: {CACHE_DIR}")
    logger.info(f"✅ Image cache ready for PDF generation!")
    logger.info(f"   Run 'python scripts/generate_pdf.py' for fast generation")
    logger.info("="*80)


if __name__ == '__main__':
    cache_all_pokemon()
