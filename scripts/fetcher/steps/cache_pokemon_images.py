"""
Cache Pokemon Images Step

Downloads and caches Pokemon images in both card and featured sizes.
Should run as the final step in the fetch pipeline to ensure all images are cached.

Sizes:
- Card (180x180px): For Pokemon cards in binder
- Featured (500x500px): For large featured Pokemon on cover pages
"""

import logging
from pathlib import Path
from typing import Dict, Any, List
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from PIL import Image
from io import BytesIO

from .base import BaseStep

logger = logging.getLogger(__name__)


class CachePokemonImages(BaseStep):
    """Cache Pokemon images in multiple sizes for fast PDF generation."""
    
    CARD_SIZE = (180, 180)
    FEATURED_SIZE = (500, 500)
    JPEG_QUALITY = 75
    TIMEOUT = 5
    USER_AGENT = 'Binder Pokédex/2.0'
    
    def execute(self, context, params: Dict[str, Any]):
        """
        Cache images for all Pokemon in the dataset.
        
        Args:
            context: Pipeline context with data
            params: Step parameters
                - skip_existing: bool - Skip if images already cached (default: True)
        
        Returns:
            Updated context (caching is a side effect)
        """
        skip_existing = params.get('skip_existing', True)
        cache_dir = self._get_cache_dir()
        
        # Get data from context
        data = context.get_data()
        if not data:
            logger.warning("   ⚠️  No data in context, skipping image caching")
            return context
        
        logger.info("🖼️  Caching Pokemon images...")
        
        # Collect all unique Pokemon IDs from all sections
        pokemon_ids_to_cache = self._collect_pokemon_ids(data)
        
        total = len(pokemon_ids_to_cache)
        cached = 0
        skipped = 0
        failed = 0
        
        logger.info(f"   📊 Found {total} unique Pokemon to cache")
        
        for idx, (cache_key, (pokemon_id, image_url, url_identifier)) in enumerate(pokemon_ids_to_cache.items(), 1):
            if idx % 50 == 0 or idx == total:
                logger.info(f"   Progress: {idx}/{total} ({cached} cached, {skipped} skipped, {failed} failed)")
            
            # Check if already cached
            if skip_existing and self._is_cached(cache_dir, pokemon_id, url_identifier):
                skipped += 1
                continue
            
            # Download and cache
            if self._cache_image(cache_dir, pokemon_id, image_url, url_identifier):
                cached += 1
            else:
                failed += 1
        
        logger.info(f"   ✅ Caching complete:")
        logger.info(f"      • Cached: {cached}")
        logger.info(f"      • Skipped: {skipped}")
        logger.info(f"      • Failed: {failed}")
        
        return context
    
    def _get_cache_dir(self) -> Path:
        """Get the image cache directory."""
        # Relative to scripts/fetcher/steps, go up to project root, then data/pokemon_images_cache
        cache_dir = Path(__file__).parent.parent.parent.parent / 'data' / 'pokemon_images_cache'
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir
    
    def _collect_pokemon_ids(self, data: Dict[str, Any]) -> Dict[str, tuple]:
        """
        Collect all unique Pokemon IDs and their image URLs.
        
        Returns:
            Dict mapping "pokemon_id_url_identifier" -> (pokemon_id, image_url, url_identifier)
        """
        pokemon_map = {}
        
        # Handle different data structures
        if 'sections' in data:
            # Variant or Pokedex structure with sections
            for section_name, section in data['sections'].items():
                # Get cards list
                pokemon_list = section.get('cards')
                
                if pokemon_list and isinstance(pokemon_list, list):
                    for pokemon in pokemon_list:
                        pokemon_id = self._extract_pokemon_id(pokemon)
                        image_url = pokemon.get('image_url') or pokemon.get('image_path')
                        
                        if pokemon_id and image_url:
                            url_identifier = self._extract_url_identifier(image_url)
                            cache_key = f"{pokemon_id}_{url_identifier}"
                            pokemon_map[cache_key] = (pokemon_id, image_url, url_identifier)
        elif 'pokemon' in data and isinstance(data['pokemon'], list):
            # Flat pokemon list
            for pokemon in data['pokemon']:
                pokemon_id = self._extract_pokemon_id(pokemon)
                image_url = pokemon.get('image_url') or pokemon.get('image_path')
                
                if pokemon_id and image_url:
                    url_identifier = self._extract_url_identifier(image_url)
                    cache_key = f"{pokemon_id}_{url_identifier}"
                    pokemon_map[cache_key] = (pokemon_id, image_url, url_identifier)
        
        return pokemon_map
    
    def _extract_pokemon_id(self, pokemon: Dict[str, Any]) -> int:
        """Extract numeric Pokemon ID from various formats."""
        pokemon_id = pokemon.get('pokemon_id')
        
        if isinstance(pokemon_id, int):
            return pokemon_id
        elif isinstance(pokemon_id, str):
            # Handle formats like "#003", "003", "3_MEGA_X"
            clean_id = pokemon_id.lstrip('#').split('_')[0]
            try:
                return int(clean_id)
            except ValueError:
                return None
        
        return None
    
    def _extract_url_identifier(self, url: str) -> str:
        """
        Extract unique identifier from URL to differentiate forms.
        
        Examples:
            - .../10034.png -> "10034" (Mega Charizard X)
            - .../6.png -> "6" (Normal Charizard)
            - .../me02/013 -> "me02-013" (TCGdex card)
        
        Returns:
            URL identifier or "default"
        """
        if not url:
            return "default"
        
        url_parts = url.rstrip('/').split('/')
        if not url_parts:
            return "default"
        
        # Get last part and remove extensions
        last_part = url_parts[-1].replace('.png', '').replace('.jpg', '')
        
        # Check if it's a numeric ID or card identifier
        if last_part.isdigit() or '-' in last_part:
            return last_part
        
        # For TCGdex URLs like .../me02/013, combine last two parts
        if len(url_parts) >= 2:
            second_last = url_parts[-2]
            if second_last and not second_last.startswith('http'):
                combined = f"{second_last}-{last_part}"
                if '-' in combined or combined.replace('-', '').isalnum():
                    return combined
        
        return "default"
    
    def _is_cached(self, cache_dir: Path, pokemon_id: int, url_identifier: str) -> bool:
        """Check if both card and featured images are cached."""
        pokemon_dir = cache_dir / f'pokemon_{pokemon_id}'
        
        card_file = pokemon_dir / f'{url_identifier}_thumb.jpg'
        featured_file = pokemon_dir / f'{url_identifier}_featured.jpg'
        
        return card_file.exists() and featured_file.exists()
    
    def _cache_image(self, cache_dir: Path, pokemon_id: int, image_url: str, url_identifier: str) -> bool:
        """
        Download and cache a Pokemon image in both sizes.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Download image
            image_data = self._download_image(image_url)
            if not image_data:
                return False
            
            # Process and save
            return self._process_and_save(cache_dir, pokemon_id, image_data, url_identifier)
            
        except Exception as e:
            logger.debug(f"Failed to cache #{pokemon_id} ({url_identifier}): {e}")
            return False
    
    def _download_image(self, url: str) -> bytes:
        """Download image from URL."""
        try:
            req = Request(url, headers={'User-Agent': self.USER_AGENT})
            with urlopen(req, timeout=self.TIMEOUT) as response:
                return response.read()
        except (URLError, HTTPError) as e:
            logger.debug(f"Download failed: {e}")
            return None
    
    def _process_and_save(self, cache_dir: Path, pokemon_id: int, image_data: bytes, url_identifier: str) -> bool:
        """
        Process image and save in both card and featured sizes.
        
        Args:
            cache_dir: Base cache directory
            pokemon_id: Pokemon ID
            image_data: Raw image bytes
            url_identifier: URL identifier for variant differentiation
        
        Returns:
            True if successful
        """
        try:
            # Load image with PIL
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
            
            # Create pokemon directory
            pokemon_dir = cache_dir / f'pokemon_{pokemon_id}'
            pokemon_dir.mkdir(parents=True, exist_ok=True)
            
            # Save card-size (180x180px) for binder cards
            img_card = img.resize(self.CARD_SIZE, Image.Resampling.LANCZOS)
            card_file = pokemon_dir / f'{url_identifier}_thumb.jpg'
            img_card.save(card_file, format='JPEG', quality=self.JPEG_QUALITY, optimize=True)
            
            # Save featured-size (500x500px) for cover displays
            img_featured = img.resize(self.FEATURED_SIZE, Image.Resampling.LANCZOS)
            featured_file = pokemon_dir / f'{url_identifier}_featured.jpg'
            img_featured.save(featured_file, format='JPEG', quality=self.JPEG_QUALITY, optimize=True)
            
            return True
            
        except Exception as e:
            logger.debug(f"Processing failed for #{pokemon_id} ({url_identifier}): {e}")
            return False
