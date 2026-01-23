"""
Cover Renderer - Consolidates all cover page rendering

Provides a single, data-driven renderer for both Pokédex and Variant covers.
All differences are driven by data structures, not code branching.

Features:
- Generation-based (Pokédex) and variant-based covers
- Unified styling system
- Data-driven title modes and colors
- Multi-language support
- Iconic Pokémon display
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
    from ..constants import PAGE_WIDTH, PAGE_HEIGHT, GENERATION_COLORS, get_generation_info
    from ..utils import TranslationHelper
    from .translation_loader import TranslationLoader
    from .title_renderer import TitleRenderer
    from .iconic_pokemon_renderer import IconicPokemonRenderer
    from .footer_renderer import FooterRenderer
except ImportError:
    # Fallback for direct imports
    from scripts.lib.fonts import FontManager
    from scripts.lib.constants import PAGE_WIDTH, PAGE_HEIGHT, GENERATION_COLORS, get_generation_info
    from scripts.lib.utils import TranslationHelper
    from scripts.lib.rendering.translation_loader import TranslationLoader
    from scripts.lib.rendering.title_renderer import TitleRenderer
    from scripts.lib.rendering.iconic_pokemon_renderer import IconicPokemonRenderer
    from scripts.lib.rendering.footer_renderer import FooterRenderer

logger = logging.getLogger(__name__)


class CoverStyle:
    """Cover styling constants for both Pokédex and Variant covers."""
    
    # Generation color scheme
    GENERATION_COLORS = GENERATION_COLORS
    
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
    TEXT_GRAY = '#666666'
    TEXT_LIGHT_GRAY = '#CCCCCC'
    FOOTER_COLOR = '#CCCCCC'
    DECORATIVE_LINE_WIDTH = 1.0
    
    # Positions
    TITLE_Y_OFFSET = 30 * mm
    GENERATION_Y_OFFSET = 55 * mm
    REGION_Y_OFFSET = 65 * mm
    POKEDEX_RANGE_Y = 110 * mm     # Pokédex ID range (optional, above count)
    POKEMOM_COUNT_Y = 100 * mm     # Pokémon count (always above decorative line)
    DECORATIVE_LINE_Y = 95 * mm    # Decorative line position
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
    """Renderer for both Pokédex and Variant cover pages."""
    
    def __init__(self, language: str = 'en', image_cache=None):
        """
        Initialize cover renderer.
        
        Args:
            language: Language code (e.g., 'en', 'de', 'fr')
            image_cache: Optional image cache for loading Pokémon images
        """
        self.language = language
        self.image_cache = image_cache
        self.style = CoverStyle()
        self.translation_loader = TranslationLoader()
        self.translations = TranslationHelper.load_translations(language)
    
    def render_cover(self, canvas_obj, pokemon_list: List[Dict], cover_data: Optional[Dict] = None, 
                    generation: Optional[int] = None, color: Optional[str] = None) -> None:
        """
        Draw a cover page (works for both Pokédex and Variant).
        
        Args:
            canvas_obj: ReportLab canvas object
            pokemon_list: List of Pokémon to display
            cover_data: Optional variant data dict. If None, generation must be provided.
            generation: Optional Pokédex generation (1-9). If None, uses variant mode.
            color: Optional color for header stripe (variant mode). If None, uses generation color.
        """
        # Determine mode and load data
        if cover_data is None and generation is not None:
            # Pokédex mode: generate cover_data from generation info
            cover_data = self._get_pokedex_cover_data(generation)
            color = self.style.GENERATION_COLORS.get(generation, '#999999')
        elif cover_data is None:
            raise ValueError("Either cover_data (variant) or generation (Pokédex) must be provided")
        elif color is None:
            # Variant mode without explicit color - try to get from cover_data
            color = cover_data.get('color_hex', '#999999')
        
        # White background
        canvas_obj.setFillColor(HexColor(self.style.BACKGROUND_COLOR))
        canvas_obj.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=True, stroke=False)
        
        # ===== TOP COLORED STRIPE =====
        self._draw_header_stripe(canvas_obj, color)
        
        # ===== MIDDLE CONTENT SECTION =====
        self._draw_title_section(canvas_obj, cover_data)
        self._draw_pokemon_count(canvas_obj, len(pokemon_list), cover_data, color)
        
        # ===== BOTTOM SECTION: ICONIC POKÉMON =====
        iconic_ids = cover_data.get('iconic_pokemon_ids') or cover_data.get('iconic_pokemon', [])
        if iconic_ids and pokemon_list:
            self._draw_iconic_pokemon(canvas_obj, iconic_ids, pokemon_list)
        
        # ===== FOOTER =====
        self._draw_footer(canvas_obj)
    
    def _get_pokedex_cover_data(self, generation: int) -> Dict:
        """Convert Pokédex generation to cover_data format."""
        gen_info = get_generation_info(generation)
        return {
            'title': gen_info.get('title', {'en': f'Generation {generation}', 'de': f'Generation {generation}'}),
            'subtitle': gen_info.get('subtitle', {'en': gen_info.get('region', ''), 'de': gen_info.get('region', '')}),
            'title_mode': gen_info.get('title_mode', 'with_subtitle'),
            'iconic_pokemon': gen_info.get('iconic_pokemon', []),
            'range': gen_info.get('range', (1, 151)),
        }
    
    def _draw_header_stripe(self, canvas_obj, color: str) -> None:
        """Draw the colored top stripe with title."""
        stripe_height = self.style.STRIPE_HEIGHT
        
        # Fill with color
        canvas_obj.setFillColor(HexColor(color))
        canvas_obj.rect(0, PAGE_HEIGHT - stripe_height, PAGE_WIDTH, stripe_height, 
                       fill=True, stroke=False)
        
        # Semi-transparent overlay
        canvas_obj.setFillColor(HexColor("#000000"), alpha=self.style.STRIPE_OVERLAY_ALPHA)
        canvas_obj.rect(0, PAGE_HEIGHT - stripe_height, PAGE_WIDTH, stripe_height, 
                       fill=True, stroke=False)
        
        # Title
        canvas_obj.setFont("Helvetica-Bold", self.style.TITLE_FONT_SIZE)
        canvas_obj.setFillColor(HexColor(self.style.TITLE_COLOR))
        title_y = PAGE_HEIGHT - self.style.TITLE_Y_OFFSET
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, title_y, "Binder Pokédex")
        
        # Decorative underline
        canvas_obj.setStrokeColor(HexColor(self.style.TITLE_COLOR))
        canvas_obj.setLineWidth(1.5)
        canvas_obj.line(40 * mm, title_y - 8, PAGE_WIDTH - 40 * mm, title_y - 8)
    
    def _draw_title_section(self, canvas_obj, cover_data: Dict) -> None:
        """Draw title and subtitle using TitleRenderer."""
        try:
            font_name = FontManager.get_font_name(self.language, bold=True)
        except Exception:
            font_name = "Helvetica-Bold"
        
        TitleRenderer.draw_title(
            canvas_obj,
            cover_data,
            self.language,
            PAGE_WIDTH,
            PAGE_HEIGHT,
            translation_getter=self._get_translation,
            font_name=font_name,
            subtitle_font_size=18,
            title_y_offset=55 * mm,
            subtitle_y_offset=65 * mm,
            section_title=None
        )
    
    def _draw_pokemon_count(self, canvas_obj, count: int, cover_data: Dict, color: str) -> None:
        """Draw Pokémon count and decorative line."""
        # Optional: Pokédex ID range (only for Pokédex, not variants)
        if 'range' in cover_data:
            start_id, end_id = cover_data['range']
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
        canvas_obj.setStrokeColor(HexColor(color))
        canvas_obj.setLineWidth(self.style.DECORATIVE_LINE_WIDTH)
        canvas_obj.line(40 * mm, self.style.DECORATIVE_LINE_Y, PAGE_WIDTH - 40 * mm, self.style.DECORATIVE_LINE_Y)
    
    def _draw_iconic_pokemon(self, canvas_obj, iconic_ids: List[int], pokemon_list: List[Dict]) -> None:
        """Draw iconic Pokémon at the bottom of the cover."""
        IconicPokemonRenderer.draw_iconic_pokemon(
            canvas_obj, iconic_ids, pokemon_list, self.image_cache, PAGE_WIDTH
        )
    
    def _draw_footer(self, canvas_obj) -> None:
        """Draw footer using canonical renderer."""
        try:
            font_name = FontManager.get_font_name(self.language, bold=False)
        except Exception:
            font_name = "Helvetica"
        
        FooterRenderer.draw_footer(
            canvas_obj,
            page_width=PAGE_WIDTH,
            language=self.language,
            translation_getter=self._get_translation,
            font_size=6,
            y_position=2.5 * mm,
            color=self.style.TEXT_LIGHT_GRAY,
            font_name=font_name
        )
    
    def _get_translation(self, key: str, fallback: str = None, **kwargs) -> str:
        """Get translated text from UI translations."""
        text = self.translation_loader.load_ui(self.language).get(key, fallback or key)
        
        # Replace placeholders
        for k, v in kwargs.items():
            text = text.replace(f"{{{{{k}}}}}", str(v))
        
        return text
