#!/usr/bin/env python3
"""
Pokédex PDF Generator (Section-based)

Generates a single comprehensive PDF with selected generations as sections.
Uses the same section-based architecture as VariantPDFGenerator.

Each generation is a section with:
- Section separator page (using CoverTemplate)
- All Pokémon cards in 3x3 layout
"""

import logging
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

from .fonts import FontManager
from .data_storage import DataStorage
from .rendering.card_renderer import CardRenderer
from .rendering.page_renderer import PageRenderer
from .rendering.cover_renderer import CoverRenderer
from .utils import TranslationHelper, RendererInitializer
from .log_formatter import PDFStatus
from .constants import (
    PAGE_WIDTH, PAGE_HEIGHT, PAGE_MARGIN, CARD_WIDTH, CARD_HEIGHT,
    CARDS_PER_ROW, CARDS_PER_COLUMN, GAP_X, GAP_Y, GENERATION_COLORS
)

logger = logging.getLogger(__name__)


class PokedexGenerator:
    """Generate Pokédex PDF with selected generations as sections."""
    
    def __init__(self, language: str, output_file: Path, image_cache=None, generations=None):
        """
        Initialize Pokédex generator.
        
        Args:
            language: Language code (de, en, fr, etc.)
            output_file: Path to output PDF file
            image_cache: Optional image cache for loading Pokémon images
            generations: Optional list of generation numbers to include (e.g., [1, 2]). 
                        If None, loads all 9 generations.
        """
        self.language = language
        self.output_file = output_file
        self.image_cache = image_cache
        
        # Default to all generations if not specified
        if generations is None:
            generations = list(range(1, 10))
        
        # Load specified generations using DataStorage
        storage = DataStorage()
        self.generations = {}
        for gen in generations:
            if 1 <= gen <= 9:
                pokemon_list = storage.load_generation(gen)
                gen_info = storage.load_generation_info(gen)
                if pokemon_list and gen_info:
                    self.generations[gen] = {
                        'info': gen_info,
                        'pokemon': pokemon_list
                    }
        
        logger.info(f"Loaded {len(self.generations)} generations for Pokédex")
        
        # Load translations (same as VariantPDFGenerator)
        self.translations = TranslationHelper.load_translations(language)
        
        # Initialize rendering components using shared utility
        self.card_renderer, self.page_renderer, self.cover_renderer = \
            RendererInitializer.initialize_renderers(language, image_cache)
    
    def generate(self) -> bool:
        """
        Generate Pokédex PDF using section-based architecture.
        
        Returns:
            True if successful, False otherwise
        """
        import time
        
        try:
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            
            c = canvas.Canvas(str(self.output_file), pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
            
            total_pokemon = sum(len(gen['pokemon']) for gen in self.generations.values())
            
            status = PDFStatus(self.output_file.stem, total_pokemon)
            status.current_message = f"Generating Pokédex with {len(self.generations)} generations"
            
            logger.info(f"Generating Pokédex with {total_pokemon} Pokémon across {len(self.generations)} generations")
            
            cards_rendered = 0
            gen_start_time = None
            
            # Generate each generation section (like variant sections)
            for gen_num in sorted(self.generations.keys()):
                gen_start_time = time.time()
                gen_data = self.generations[gen_num]
                gen_info = gen_data['info']
                pokemon_list = gen_data['pokemon']
                
                # Generation section separator (using cover_template, like variants do)
                # Pass full pokemon_list for count display, but featured_pokemon for featured display
                self._draw_generation_separator(c, gen_num, gen_info, pokemon_list, pokemon_list[:3])
                c.showPage()
                
                # Generation Pokémon cards (3x3 per page, like variants do)
                cards_per_page = CARDS_PER_ROW * CARDS_PER_COLUMN
                for page_idx in range(0, len(pokemon_list), cards_per_page):
                    page_pokemon = pokemon_list[page_idx:page_idx + cards_per_page]
                    
                    cards_rendered += len(page_pokemon)
                    progress_pct = (cards_rendered / total_pokemon) * 100
                    status.update(None, progress_pct)
                    status.print_progress()
                    
                    self._draw_cards_page(c, page_pokemon)
                    c.showPage()
            
                # Log per-generation timing
                gen_elapsed = time.time() - gen_start_time
                gen_pokemon_count = len(gen_data['pokemon'])
                avg_time_per_pokemon = (gen_elapsed / gen_pokemon_count * 1000) if gen_pokemon_count else 0
                print(f"  ⚡ Gen {gen_num}: {gen_elapsed:.2f}s ({gen_pokemon_count} Pokémon, {avg_time_per_pokemon:.1f}ms/Pokémon)")
            
            c.save()
            
            # Update summary info
            file_size_mb = self.output_file.stat().st_size / (1024 * 1024)
            status.file_size_mb = file_size_mb
            status.print_summary()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error generating Pokédex: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _draw_generation_separator(self, c, gen_num, gen_info, pokemon_list, featured_pokemon=None):
        """
        Draw generation separator page using unified CoverRenderer.
        
        Displays:
        - "Binder Pokédex" title
        - "Generation X" subtitle  
        - Region name
        - Pokédex ID range
        - Pokémon count
        - Iconic Pokémon images
        
        Args:
            c: ReportLab canvas
            gen_num: Generation number (1-9)
            gen_info: Generation info dict
            pokemon_list: Full list of Pokémon in this generation (for count display)
            featured_pokemon: Optional featured Pokémon to display (currently unused)
        """
        # Use cover renderer in Pokédex mode (generation parameter)
        renderer = CoverRenderer(language=self.language, image_cache=self.image_cache)
        renderer.render_cover(c, pokemon_list, generation=gen_num)
    
    def _draw_cards_page(self, c, pokemon_list):
        """
        Draw a page of Pokémon cards (3x3 layout).
        
        Same as VariantPDFGenerator._draw_cards_page.
        """
        for idx, pokemon in enumerate(pokemon_list):
            row = idx // CARDS_PER_ROW
            col = idx % CARDS_PER_ROW
            
            x = PAGE_MARGIN + (col * (CARD_WIDTH + GAP_X))
            y = PAGE_HEIGHT - PAGE_MARGIN - ((row + 1) * CARD_HEIGHT) - (row * GAP_Y)
            
            # Normalize Pokemon data: add 'name' field with language-specific name
            pokemon_normalized = self._normalize_pokemon_data(pokemon)
            
            self.card_renderer.render_card(c, pokemon_normalized, x, y)

        # Always draw cutting guides after cards
        self.page_renderer.draw_cutting_guides(c)
    
    def _normalize_pokemon_data(self, pokemon: dict) -> dict:
        """
        Normalize Pokemon data for the current language.
        
        Ensures the 'name' field contains the name in the current language,
        Ensures the 'name' field contains the name in the current language,
        and 'name_en' field contains the English name for subtitle display.
        
        The 'name' field in the raw Pokemon dict must have multilingual structure:
        'name': {'en': '...', 'de': '...', 'fr': '...', etc.}
        
        Args:
            pokemon: Raw Pokemon dict from JSON (must have unified name object structure)
            
        Returns:
            Normalized dict with 'name' and 'name_en' fields
        """
        normalized = pokemon.copy()
        
        # Get the name for current language from unified name object
        normalized['name'] = pokemon['name'].get(self.language, pokemon['name'].get('en', 'Unknown'))
        
        # Ensure name_en is set for subtitle display
        normalized['name_en'] = pokemon['name']['en']
        
        return normalized
