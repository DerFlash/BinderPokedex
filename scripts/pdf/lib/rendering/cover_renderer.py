"""
Cover Renderer - Consolidates all cover page rendering

Provides a single, data-driven renderer for both Pokédex and Variant covers.
All differences are driven by data structures, not code branching.

Features:
- Generation-based (Pokédex) and variant-based covers
- Unified styling system
- Data-driven title modes and colors
- Multi-language support
- Featured Pokémon display
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
    from ..constants import PAGE_WIDTH, PAGE_HEIGHT, GENERATION_COLORS
    from ..utils import TranslationHelper
    from .translation_loader import TranslationLoader
    from .title_renderer import TitleRenderer
    from .footer_renderer import FooterRenderer
except ImportError:
    # Fallback for direct imports
    from scripts.lib.fonts import FontManager
    from scripts.lib.constants import PAGE_WIDTH, PAGE_HEIGHT, GENERATION_COLORS
    from scripts.lib.utils import TranslationHelper
    from scripts.lib.rendering.translation_loader import TranslationLoader
    from scripts.lib.rendering.title_renderer import TitleRenderer
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
    POKEDEX_RANGE_Y = 160 * mm     # Pokédex ID range (optional, above count)
    POKEMOM_COUNT_Y = 150 * mm     # Pokémon count (always above decorative line)
    DECORATIVE_LINE_Y = 145 * mm   # Decorative line position
    ICONIC_POKEMON_Y = 10 * mm
    FOOTER_Y = 2.5 * mm
    
    # Featured Pokémon sizing
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
    
    def render_cover(self, canvas_obj, pokemon_list: List[Dict], cover_data: Dict, 
                    color: Optional[str] = None) -> None:
        """
        Draw a cover page for any scope (unified for all types).
        
        Args:
            canvas_obj: ReportLab canvas object
            pokemon_list: List of Pokémon to display
            cover_data: Section data dict with title, subtitle, color_hex, description, featured_elements
            color: Optional color override for header stripe. If None, uses color_hex from cover_data.
        """
        # Get color from cover_data or use provided override
        if color is None:
            color = cover_data.get('color_hex', '#999999')
        
        # White background
        canvas_obj.setFillColor(HexColor(self.style.BACKGROUND_COLOR))
        canvas_obj.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=True, stroke=False)
        
        # ===== TOP COLORED STRIPE =====
        self._draw_header_stripe(canvas_obj, color)
        
        # ===== MIDDLE CONTENT SECTION =====
        self._draw_title_section(canvas_obj, cover_data)
        self._draw_pokemon_count(canvas_obj, len(pokemon_list), cover_data, color)
        
        # ===== FEATURED CARDS =====
        self._draw_featured_elements(canvas_obj, cover_data)
        
        # ===== FOOTER =====
        self._draw_footer(canvas_obj)
    
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
        """Draw Pokémon count, description, and decorative line."""
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
        
        # Description text (below the line)
        description = cover_data.get('description', {})
        if isinstance(description, dict):
            description_text = description.get(self.language, description.get('en', ''))
        else:
            description_text = str(description) if description else ''
        
        if description_text:
            try:
                desc_font_name = FontManager.get_font_name(self.language, bold=False)
            except Exception:
                desc_font_name = "Helvetica"
            
            # Use LogoRenderer to handle [EX], [EX_NEW] tokens in description
            from .logo_renderer import LogoRenderer
            LogoRenderer.draw_text_with_logos(
                canvas_obj,
                description_text,
                PAGE_WIDTH / 2,
                self.style.DECORATIVE_LINE_Y - 8 * mm,
                desc_font_name,
                11,
                context='title',
                text_color=self.style.TEXT_GRAY,
                language=self.language
            )
    
    def _draw_featured_elements(self, canvas_obj, cover_data: Dict) -> None:
        """Draw featured element images in the lower section of the cover."""
        # Support both old and new field names for backward compatibility
        featured_elements = cover_data.get('featured_elements') or cover_data.get('featured_cards', [])
        
        if not featured_elements:
            return
        
        # Position for featured elements (lower section, above footer)
        card_y_base = 35 * mm
        card_width = 45 * mm
        card_height = 63 * mm
        
        num_elements = len(featured_elements)
        
        # Calculate spacing to center elements horizontally
        if num_elements == 1:
            spacing = 0
            start_x = (PAGE_WIDTH - card_width) / 2
        elif num_elements == 2:
            spacing = 10 * mm
            total_width = 2 * card_width + spacing
            start_x = (PAGE_WIDTH - total_width) / 2
        else:  # 3 elements
            spacing = 8 * mm
            total_width = 3 * card_width + 2 * spacing
            start_x = (PAGE_WIDTH - total_width) / 2
        
        # Draw each featured element
        for i, element in enumerate(featured_elements[:3]):  # Max 3 elements
            element_x = start_x + i * (card_width + spacing)
            
            # Get local image path
            image_path = element.get('local_image_path')
            if not image_path or not Path(image_path).exists():
                logger.warning(f"Featured element image not found: {image_path}")
                continue
            
            try:
                # Draw element image
                canvas_obj.drawImage(
                    str(image_path),
                    element_x,
                    card_y_base,
                    width=card_width,
                    height=card_height,
                    preserveAspectRatio=True,
                    mask='auto'
                )
            except Exception as e:
                logger.error(f"Failed to draw featured element image {image_path}: {e}")
    
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
