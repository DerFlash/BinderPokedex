"""
Featured Pokémon Renderer - Shared featured Pokémon rendering logic

Consolidates featured Pokémon rendering for both Generation and Variant covers.
Provides a single, canonical implementation used by CoverRenderer and VariantCoverRenderer.

Features:
- Unified featured Pokémon layout logic
- Compact spacing for grouped appearance
- Multi-format ID handling (int, string, variant formats)
- Image loading with fallback support
"""

import logging
from pathlib import Path
from typing import List, Dict

from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor

logger = logging.getLogger(__name__)


class FeaturedPokemonRenderer:
    """Unified renderer for featured Pokémon on cover pages."""
    
    # Dimensions
    CARD_WIDTH = 65 * mm
    CARD_HEIGHT = 90 * mm
    CARD_SPACING = 0 * mm  # No spacing - cards directly adjacent
    IMAGE_SCALE = 0.72     # Scale images within card
    Y_POSITION = 10 * mm   # Bottom position on cover
    
    @staticmethod
    def draw_iconic_pokemon(canvas_obj, iconic_ids: List[int], pokemon_list: list, 
                           image_cache, page_width: float):
        """
        Draw featured Pokémon at the bottom of a cover page.
        
        Canonical implementation used by both CoverRenderer and VariantCoverRenderer.
        
        Args:
            canvas_obj: ReportLab canvas object
            iconic_ids: List of Pokémon IDs to display (max 3)
            pokemon_list: List of Pokémon data dictionaries
            image_cache: Image cache instance for loading images
            page_width: Total page width for centering calculation
        """
        if not iconic_ids or not pokemon_list or not image_cache:
            return
        
        # Build pokemon dict by ID - handle different ID formats
        # For variants with duplicate IDs (different forms), keep all occurrences
        pokemon_by_id = {}
        pokemon_by_id_list = {}  # For duplicates, store as list
        for p in pokemon_list:
            try:
                pid = str(p.get('id', p.get('num', '0'))).split('_')[0].lstrip('#')
                pid_int = int(pid)
                
                # Store in single dict (for backward compatibility)
                pokemon_by_id[pid_int] = p
                
                # Also store all occurrences in a list dict
                if pid_int not in pokemon_by_id_list:
                    pokemon_by_id_list[pid_int] = []
                pokemon_by_id_list[pid_int].append(p)
            except (ValueError, AttributeError):
                pass
        
        # Convert iconic_ids to integers - handle different ID formats
        clean_iconic_ids = []
        for poke_id in iconic_ids:
            try:
                if isinstance(poke_id, str):
                    # Handle formats like '#003_EX1' or '003'
                    clean_id = int(poke_id.split('_')[0].lstrip('#'))
                else:
                    clean_id = int(poke_id)
                clean_iconic_ids.append(clean_id)
            except (ValueError, AttributeError):
                pass
        
        # Use compact layout with fixed spacing between cards
        pokemon_count = len(clean_iconic_ids[:3])
        if pokemon_count == 0:
            return
        
        # Calculate total width needed for all cards
        total_cards_width = (FeaturedPokemonRenderer.CARD_WIDTH * pokemon_count + 
                            FeaturedPokemonRenderer.CARD_SPACING * (pokemon_count - 1))
        
        # Center the group on the page
        start_x = (page_width - total_cards_width) / 2
        
        for idx, poke_id in enumerate(clean_iconic_ids[:3]):
            x_center = start_x + idx * (FeaturedPokemonRenderer.CARD_WIDTH + 
                                       FeaturedPokemonRenderer.CARD_SPACING) + FeaturedPokemonRenderer.CARD_WIDTH / 2
            
            # Use the list dict first (handles duplicates), then fall back to single dict
            pokemon = None
            if poke_id in pokemon_by_id_list:
                # Get first occurrence of this Pokemon ID (for variants with duplicates)
                pokemon = pokemon_by_id_list[poke_id][0]
            else:
                pokemon = pokemon_by_id.get(poke_id)
            
            if pokemon:
                image_source = pokemon.get('image_path') or pokemon.get('image_url')
                if image_source:
                    try:
                        image_to_render = None
                        if image_source.startswith('http://') or image_source.startswith('https://'):
                            image_to_render = image_cache.get_image(poke_id, 
                                                                    url=image_source, 
                                                                    timeout=3,
                                                                    size='featured')
                        elif Path(image_source).exists():
                            image_to_render = image_source
                        
                        if image_to_render:
                            img_width = FeaturedPokemonRenderer.CARD_WIDTH * FeaturedPokemonRenderer.IMAGE_SCALE
                            img_height = FeaturedPokemonRenderer.CARD_HEIGHT * FeaturedPokemonRenderer.IMAGE_SCALE
                            img_x = x_center - img_width / 2
                            img_y = FeaturedPokemonRenderer.Y_POSITION
                            canvas_obj.drawImage(image_to_render, img_x, img_y,
                                               width=img_width, height=img_height,
                                               preserveAspectRatio=True)
                    except Exception as e:
                        logger.debug(f"Could not load image for featured Pokémon {poke_id}: {e}")
