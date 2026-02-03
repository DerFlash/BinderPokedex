"""
Bulbagarden Trainer Sprite Downloader

Downloads VS trainer sprites from Bulbagarden Archives for use in PDFs.
Implements caching to avoid repeated downloads.

Usage:
    from lib.trainer_sprite_downloader import TrainerSpriteDownloader
    
    downloader = TrainerSpriteDownloader()
    sprite_path = downloader.get_sprite("Acerola's Mischief")
"""

import logging
import re
import requests
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from trainer_sprite_mapper import get_trainer_sprite_url, normalize_trainer_name

logger = logging.getLogger(__name__)


class TrainerSpriteDownloader:
    """Downloads and caches trainer sprites from Bulbagarden Archives."""
    
    DEFAULT_CACHE_DIR = Path("data/trainer_sprites_cache")
    USER_AGENT = "BinderPokedex/1.0 (https://github.com/yourusername/BinderPokedex)"
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the downloader.
        
        Args:
            cache_dir: Directory to cache downloaded sprites (default: data/trainer_sprites_cache/)
        """
        self.cache_dir = cache_dir or self.DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.USER_AGENT
        })
    
    def get_sprite(self, card_name: str, force_download: bool = False) -> Optional[Path]:
        """
        Get the trainer sprite file path, downloading if necessary.
        
        Args:
            card_name: TCG trainer card name (e.g., "Acerola's Mischief")
            force_download: If True, re-download even if cached
            
        Returns:
            Path to the sprite file, or None if download fails
        """
        trainer_name = normalize_trainer_name(card_name)
        
        if not trainer_name:
            logger.warning(f"Could not normalize trainer name: {card_name}")
            return None
        
        sprite_filename = f"VS{trainer_name}.png"
        cache_path = self.cache_dir / sprite_filename
        
        # Return cached file if it exists
        if cache_path.exists() and not force_download:
            logger.debug(f"Using cached sprite: {sprite_filename}")
            return cache_path
        
        # Download sprite
        logger.info(f"Downloading trainer sprite: {sprite_filename}")
        
        wiki_url = get_trainer_sprite_url(card_name)
        if not wiki_url:
            logger.warning(f"No sprite URL for: {card_name}")
            return None
        
        try:
            # Fetch the wiki page to extract the actual image URL
            image_url = self._get_image_url_from_wiki(wiki_url)
            
            if not image_url:
                logger.warning(f"Could not extract image URL from: {wiki_url}")
                return None
            
            # Download the image
            response = self.session.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Save to cache
            with open(cache_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✅ Downloaded: {sprite_filename} ({len(response.content)} bytes)")
            return cache_path
            
        except Exception as e:
            logger.error(f"Failed to download sprite for {card_name}: {e}")
            return None
    
    def _get_image_url_from_wiki(self, wiki_url: str) -> Optional[str]:
        """
        Extract the actual image URL from a Bulbagarden wiki file page.
        
        Args:
            wiki_url: URL to the wiki file page
            
        Returns:
            Direct URL to the image file
        """
        try:
            response = self.session.get(wiki_url, timeout=10)
            response.raise_for_status()
            
            # Extract image URL from the page
            # Look for: <div class="fullImageLink"><a href="https://archives.bulbagarden.net/media/upload/...">
            match = re.search(r'<div class="fullImageLink"[^>]*><a href="([^"]+)"', response.text)
            
            if match:
                return match.group(1)
            
            # Alternative pattern: <meta property="og:image" content="...">
            meta_match = re.search(r'<meta property="og:image" content="([^"]+)"', response.text)
            if meta_match:
                return meta_match.group(1)
            
            # Try direct file link pattern
            file_match = re.search(r'href="(https://archives\.bulbagarden\.net/media/upload/[^"]+\.png)"', response.text)
            if file_match:
                return file_match.group(1)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch wiki page {wiki_url}: {e}")
            return None
    
    def batch_download(self, card_names: list[str], quiet: bool = False) -> dict[str, Optional[Path]]:
        """
        Download multiple trainer sprites in batch.
        
        Args:
            card_names: List of TCG trainer card names
            quiet: If True, suppress progress logging
            
        Returns:
            Dict mapping card names to sprite file paths (or None if failed)
        """
        results = {}
        
        total = len(card_names)
        for i, card_name in enumerate(card_names, 1):
            if not quiet:
                print(f"[{i}/{total}] {card_name}...")
            
            sprite_path = self.get_sprite(card_name)
            results[card_name] = sprite_path
        
        # Summary
        successful = sum(1 for path in results.values() if path is not None)
        failed = total - successful
        
        if not quiet:
            print(f"\n✅ Downloaded: {successful} | ❌ Failed: {failed}")
        
        return results
    
    def clear_cache(self):
        """Remove all cached sprites."""
        count = 0
        for sprite_file in self.cache_dir.glob("VS*.png"):
            sprite_file.unlink()
            count += 1
        
        logger.info(f"Cleared {count} cached sprites")


if __name__ == "__main__":
    # Test the downloader
    logging.basicConfig(level=logging.INFO)
    
    downloader = TrainerSpriteDownloader()
    
    test_cards = [
        "Acerola's Mischief",
        "Iono",
        "Boss's Orders (Giovanni)",
    ]
    
    print("Trainer Sprite Downloader - Test")
    print("=" * 60)
    
    results = downloader.batch_download(test_cards)
    
    print("\nResults:")
    for card_name, sprite_path in results.items():
        status = "✅" if sprite_path else "❌"
        print(f"{status} {card_name}: {sprite_path}")
