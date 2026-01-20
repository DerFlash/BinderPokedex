"""
Cover Renderer - Unified cover page rendering

Consolidates cover page rendering logic from pdf_generator.py.

Features:
- Generation-based color schemes
- Region and generation information
- Iconic Pokémon display
- Multi-language support
- Clean, modern design
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor

try:
    from ..fonts import FontManager
    from ..constants import PAGE_WIDTH, PAGE_HEIGHT, GENERATION_INFO
    from .translation_loader import TranslationLoader
except ImportError:
    # Fallback for direct imports
    from scripts.lib.fonts import FontManager
    from scripts.lib.constants import PAGE_WIDTH, PAGE_HEIGHT, GENERATION_INFO
    from scripts.lib.rendering.translation_loader import TranslationLoader

logger = logging.getLogger(__name__)


class CoverStyle:
    """Unified cover styling constants."""
    
    # Generation color scheme
    GENERATION_COLORS = {
        1: '#FF0000',  # Red
        2: '#FFAA00',  # Orange
        3: '#0000FF',  # Blue
        4: '#AA00FF',  # Purple
        5: '#00AA00',  # Green
        6: '#00AAAA',  # Cyan
        7: '#FF00AA',  # Pink
        8: '#AAAA00',  # Yellow
        9: '#666666',  # Gray
    }
    
    # Dimensions
    STRIPE_HEIGHT = 100 * mm
    TITLE_FONT_SIZE = 42
    GENERATION_FONT_SIZE = 14
    REGION_FONT_SIZE = 18
    POKEMON_COUNT_FONT_SIZE = 14
    POKEDEX_RANGE_FONT_SIZE = 16
    FOOTER_FONT_SIZE = 6
    
    # Colors
    BACKGROUND_COLOR = '#FFFFFF'
    STRIPE_OVERLAY_ALPHA = 0.05
    TITLE_COLOR = '#FFFFFF'
    TEXT_DARK = '#333333'
    TEXT_MEDIUM = '#666666'
    FOOTER_COLOR = '#CCCCCC'
    DECORATIVE_LINE_WIDTH = 1.0
    
    # Positions
    TITLE_Y_OFFSET = 30 * mm
    GENERATION_Y_OFFSET = 55 * mm
    REGION_Y_OFFSET = 65 * mm
    POKEMOM_COUNT_Y = 110 * mm
    POKEDEX_RANGE_Y = 120 * mm
    ICONIC_POKEMON_Y = 10 * mm
    FOOTER_Y = 2.5 * mm
    
    # Iconic Pokémon sizing
    ICONIC_CARD_WIDTH = 65 * mm
    ICONIC_CARD_HEIGHT = 90 * mm
    ICONIC_IMAGE_SCALE = 0.72
    
    # Margins
    MARGIN_HORIZONTAL = 15 * mm
    MARGIN_VERTICAL = 30 * mm


class CoverRenderer:
    """Unified renderer for cover pages."""
    
    def __init__(self, language: str = 'en', generation: int = 1, image_cache=None):
        """
        Initialize cover renderer.
        
        Args:
            language: Language code (e.g., 'en', 'de', 'fr')
            generation: Pokémon generation (1-9)
            image_cache: Optional image cache for loading Pokémon images
        """
        self.language = language
        self.generation = generation
        self.image_cache = image_cache
        self.style = CoverStyle()
        
        # Load UI translations
        self.translations = TranslationLoader.load_ui(language)
    
    def render_cover(self, canvas_obj, pokemon_list: List[Dict]) -> None:
        """
        Draw a cover page for a generation.
        
        Args:
            canvas_obj: ReportLab canvas object
            pokemon_list: List of Pokémon to display (used for getting count and iconic species)
        """
        # White background
        canvas_obj.setFillColor(HexColor(self.style.BACKGROUND_COLOR))
        canvas_obj.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=True, stroke=False)
        
        # ===== TOP COLORED STRIPE =====
        self._draw_header_stripe(canvas_obj)
        
        # ===== MIDDLE CONTENT SECTION =====
        self._draw_generation_info(canvas_obj)
        self._draw_pokemon_count(canvas_obj, len(pokemon_list))
        
        # ===== BOTTOM SECTION: ICONIC POKÉMON =====
        if pokemon_list:
            self._draw_iconic_pokemon(canvas_obj, pokemon_list)
        
        # ===== FOOTER =====
        self._draw_footer(canvas_obj)
    
    def _draw_header_stripe(self, canvas_obj) -> None:
        """Draw the colored top stripe with title."""
        gen_color = self.style.GENERATION_COLORS.get(self.generation, '#999999')
        stripe_height = self.style.STRIPE_HEIGHT
        
        # Fill with generation color
        canvas_obj.setFillColor(HexColor(gen_color))
        canvas_obj.rect(0, PAGE_HEIGHT - stripe_height, PAGE_WIDTH, stripe_height, 
                       fill=True, stroke=False)
        
        # Semi-transparent overlay for subtle effect
        canvas_obj.setFillColor(HexColor("#000000"), alpha=self.style.STRIPE_OVERLAY_ALPHA)
        canvas_obj.rect(0, PAGE_HEIGHT - stripe_height, PAGE_WIDTH, stripe_height, 
                       fill=True, stroke=False)
        
        # Binder Pokédex title
        canvas_obj.setFont("Helvetica-Bold", self.style.TITLE_FONT_SIZE)
        canvas_obj.setFillColor(HexColor(self.style.TITLE_COLOR))
        title_y = PAGE_HEIGHT - self.style.TITLE_Y_OFFSET
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, title_y, "Binder Pokédex")
        
        # Decorative underline
        canvas_obj.setStrokeColor(HexColor(self.style.TITLE_COLOR))
        canvas_obj.setLineWidth(1.5)
        canvas_obj.line(40 * mm, title_y - 8, PAGE_WIDTH - 40 * mm, title_y - 8)
    
    def _draw_generation_info(self, canvas_obj) -> None:
        """Draw generation and region information."""
        get_info = GENERATION_INFO[self.generation]
        region_name = get_info.get('region', f'Generation {self.generation}')
        
        # Generation text (with translation)
        gen_text = self._get_translation('generation_num', gen=self.generation)
        if not gen_text or gen_text == 'generation_num':
            gen_text = f"Generation {self.generation}"
        
        try:
            gen_font_name = FontManager.get_font_name(self.language, bold=False)
            canvas_obj.setFont(gen_font_name, self.style.GENERATION_FONT_SIZE)
        except Exception:
            canvas_obj.setFont("Helvetica", self.style.GENERATION_FONT_SIZE)
        
        canvas_obj.setFillColor(HexColor(self.style.TITLE_COLOR))
        gen_y = PAGE_HEIGHT - self.style.GENERATION_Y_OFFSET
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, gen_y, gen_text)
        
        # Region name
        canvas_obj.setFont("Helvetica-Bold", self.style.REGION_FONT_SIZE)
        canvas_obj.setFillColor(HexColor(self.style.TITLE_COLOR))
        region_y = PAGE_HEIGHT - self.style.REGION_Y_OFFSET
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, region_y, region_name)
    
    def _draw_pokemon_count(self, canvas_obj, count: int) -> None:
        """Draw Pokémon count information."""
        # ID range
        get_info = GENERATION_INFO[self.generation]
        start_id, end_id = get_info['range']
        
        id_range_text = self._get_translation('pokedex_range', 
                                             start=f"#{start_id:03d}", 
                                             end=f"#{end_id:03d}")
        if not id_range_text or id_range_text == 'pokedex_range':
            id_range_text = f"Pokédex #{start_id:03d} – #{end_id:03d}"
        
        try:
            id_font_name = FontManager.get_font_name(self.language, bold=False)
            canvas_obj.setFont(id_font_name, self.style.POKEDEX_RANGE_FONT_SIZE)
        except Exception:
            canvas_obj.setFont("Helvetica", self.style.POKEDEX_RANGE_FONT_SIZE)
        
        canvas_obj.setFillColor(HexColor(self.style.TEXT_DARK))
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, self.style.POKEDEX_RANGE_Y, id_range_text)
        
        # Pokémon count text
        pokemon_text = self._get_translation('pokemon_count_text', count=count)
        if not pokemon_text or pokemon_text == 'pokemon_count_text':
            pokemon_text = f"{count} Pokémon in this collection"
        
        try:
            count_font_name = FontManager.get_font_name(self.language, bold=False)
            canvas_obj.setFont(count_font_name, self.style.POKEMON_COUNT_FONT_SIZE)
        except Exception:
            canvas_obj.setFont("Helvetica", self.style.POKEMON_COUNT_FONT_SIZE)
        
        canvas_obj.setFillColor(HexColor(self.style.TEXT_MEDIUM))
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, self.style.POKEMOM_COUNT_Y, pokemon_text)
        
        # Decorative line
        gen_color = self.style.GENERATION_COLORS.get(self.generation, '#999999')
        canvas_obj.setStrokeColor(HexColor(gen_color))
        canvas_obj.setLineWidth(self.style.DECORATIVE_LINE_WIDTH)
        canvas_obj.line(40 * mm, 105 * mm, PAGE_WIDTH - 40 * mm, 105 * mm)
    
    def _draw_iconic_pokemon(self, canvas_obj, pokemon_list: List[Dict]) -> None:
        """Draw iconic Pokémon at the bottom of the cover."""
        get_info = GENERATION_INFO[self.generation]
        iconic_ids = get_info.get('iconic_pokemon', [])
        
        if not iconic_ids:
            return
        
        # Create lookup by ID
        pokemon_by_id = {
            int(p.get('id', p.get('num', '0').lstrip('#'))): p 
            for p in pokemon_list
        }
        
        # Position 3 Pokémon horizontally
        pokemon_count = min(len(iconic_ids), 3)
        total_width = PAGE_WIDTH - (30 * mm)
        spacing_per_pokemon = total_width / pokemon_count
        
        for idx, poke_id in enumerate(iconic_ids[:3]):
            x_center = self.style.MARGIN_HORIZONTAL + spacing_per_pokemon * (idx + 0.5)
            
            card_width = self.style.ICONIC_CARD_WIDTH
            card_height = self.style.ICONIC_CARD_HEIGHT
            x = x_center - card_width / 2
            y = self.style.ICONIC_POKEMON_Y
            
            pokemon = pokemon_by_id.get(poke_id)
            
            if pokemon:
                self._draw_iconic_pokemon_image(canvas_obj, pokemon, x_center, y)
    
    def _draw_iconic_pokemon_image(self, canvas_obj, pokemon: Dict, x_center: float, y: float) -> None:
        """Draw a single iconic Pokémon image."""
        image_source = pokemon.get('image_path') or pokemon.get('image_url')
        
        if not image_source:
            return
        
        try:
            image_to_render = None
            poke_id = pokemon.get('id')
            
            if image_source.startswith(('http://', 'https://')):
                # URL - try to load from cache
                if self.image_cache:
                    image_to_render = self.image_cache.get_image(poke_id, url=image_source, timeout=3)
            else:
                # Local path
                if Path(image_source).exists():
                    image_to_render = image_source
            
            if image_to_render:
                img_width = self.style.ICONIC_CARD_WIDTH * self.style.ICONIC_IMAGE_SCALE
                img_height = self.style.ICONIC_CARD_HEIGHT * self.style.ICONIC_IMAGE_SCALE
                img_x = x_center - img_width / 2
                img_y = y
                
                canvas_obj.drawImage(
                    image_to_render, img_x, img_y,
                    width=img_width, height=img_height,
                    preserveAspectRatio=True
                )
        
        except Exception as e:
            logger.debug(f"Could not load image for iconic Pokémon {pokemon.get('id')}: {e}")
    
    def _draw_footer(self, canvas_obj) -> None:
        """Draw footer with project info and date."""
        try:
            font_name = FontManager.get_font_name(self.language, bold=False)
            canvas_obj.setFont(font_name, self.style.FOOTER_FONT_SIZE)
        except Exception:
            canvas_obj.setFont("Helvetica", self.style.FOOTER_FONT_SIZE)
        
        canvas_obj.setFillColor(HexColor(self.style.FOOTER_COLOR))
        
        # Build footer text with translations
        footer_parts = [
            self._get_translation('cover_print_borderless', 'Print borderless'),
            self._get_translation('cover_follow_cutting', 'Follow cutting guides'),
            "Binder Pokédex Project",  # Keep project name in English
            datetime.now().strftime('%Y-%m-%d')
        ]
        footer_text = " • ".join(footer_parts)
        
        # Calculate centered position
        text_width = canvas_obj.stringWidth(footer_text, canvas_obj._fontname, 
                                           self.style.FOOTER_FONT_SIZE) if hasattr(canvas_obj, '_fontname') else len(footer_text) * 2
        x_pos = (PAGE_WIDTH - text_width) / 2
        
        canvas_obj.drawString(x_pos, self.style.FOOTER_Y, footer_text)
    
    def _get_translation(self, key: str, fallback: str = None, **kwargs) -> str:
        """
        Get a translated string and format it with provided variables.
        
        Args:
            key: Translation key
            fallback: Fallback text if translation not found
            **kwargs: Variables to format into the string
        
        Returns:
            Formatted translation or fallback/key
        """
        text = self.translations.get(key, fallback or key)
        
        # Simple template replacement for kwargs
        for var_name, var_value in kwargs.items():
            text = text.replace(f'{{{{{var_name}}}}}', str(var_value))
        
        return text
