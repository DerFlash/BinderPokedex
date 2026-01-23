"""
Card Renderer - Unified card rendering for all PDF types

Consolidates card rendering logic from pdf_generator.py and card_template.py
into a single, unified implementation. This eliminates code duplication and ensures
consistent card rendering across Generation PDFs and Variant PDFs.

Features:
- Unified card rendering with type-based header colors
- Pokémon name and number rendering
- Image area handling
- Language-aware font selection
- Type translation support
- Gender symbol fallback rendering
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader

try:
    from ..fonts import FontManager
    from ..constants import CARD_WIDTH, CARD_HEIGHT, TYPE_COLORS
    from ..utils import TextRenderer
    from .translation_loader import TranslationLoader
    from .logo_renderer import LogoRenderer
except ImportError:
    # Fallback for direct imports
    from scripts.lib.fonts import FontManager
    from scripts.lib.constants import CARD_WIDTH, CARD_HEIGHT, TYPE_COLORS
    from scripts.lib.utils import TextRenderer
    from scripts.lib.rendering.translation_loader import TranslationLoader
    from scripts.lib.rendering.logo_renderer import LogoRenderer

logger: logging.Logger = logging.getLogger(__name__)


class CardStyle:
    """Unified card styling constants."""
    
    # Pokémon type color mapping - NOW IMPORTED FROM constants.py (canonical source)
    TYPE_COLORS: Dict[str, str] = TYPE_COLORS
    
    # Card dimensions
    CARD_WIDTH: float = CARD_WIDTH
    CARD_HEIGHT: float = CARD_HEIGHT
    HEADER_HEIGHT: float = 12 * mm
    IMAGE_PADDING: float = 2 * mm
    
    # Colors
    CARD_BORDER_COLOR = '#CCCCCC'
    CARD_BACKGROUND = '#FFFFFF'
    TEXT_DARK = '#2D2D2D'
    TEXT_GRAY = '#5D5D5D'
    TEXT_LIGHT_GRAY = '#999999'
    
    # Fonts - Increased sizes for better readability on printed A4
    FONT_SIZE_NAME = 11          # Increased from 8
    FONT_SIZE_TYPE = 6           # Increased from 5
    FONT_SIZE_ID = 16
    FONT_SIZE_SUBTITLE = 7       # Increased from 4


class CardRenderer:
    """Unified renderer for Pokémon cards."""
    
    def __init__(self, language: str = 'en', image_cache=None, variant: str = None, variant_data: dict = None) -> None:
        """
        Initialize card renderer.
        
        Args:
            language: Language code for text rendering (e.g., 'en', 'de', 'fr')
            image_cache: Optional image cache for loading Pokémon images
            variant: Optional variant ID (ex_gen1, ex_gen2, etc.) for variant-specific rendering
            variant_data: Optional variant data dict for accessing variant-level config (suffix, etc.)
        """
        self.language: str = language
        self.image_cache = image_cache
        self.variant: str = variant
        self.variant_data = variant_data or {}
        self.style = CardStyle()
        
        # Load type translations for this language
        self.type_translations: Dict[str, str] = TranslationLoader.load_types(language)
    
    @staticmethod
    def _darken_color(hex_color: str, factor: float = 0.6) -> str:
        """Darken a hex color by multiplying RGB values by factor."""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _draw_card_name_with_ex_logo(self, canvas_obj, name: str, x: float, card_width: float,
                                     name_y: float, font_name: str, logo_type: str = 'ex') -> None:
        """
        Draw card name with EX or special variant logos.
        
        Handles Gen1 'ex' suffix, Gen2 'M EX' and 'EX' variants, Gen3 '[EX_NEW]' and '[EX_TERA]' tokens.
        
        Delegates to LogoRenderer for unified logo handling.
        
        Args:
            canvas_obj: ReportLab canvas
            name: Full name with suffix/prefix
            x: Card x position
            card_width: Card width
            name_y: Y position for name
            font_name: Font to use
            logo_type: Type of logo ('ex', 'm_ex', 'ex_new', 'ex_tera')
        """
        canvas_obj.setFont(font_name, self.style.FONT_SIZE_NAME)
        canvas_obj.setFillColor(HexColor(self.style.TEXT_DARK))
        
        # Use unified LogoRenderer with card context
        LogoRenderer.draw_text_with_logos(
            canvas_obj,
            name,
            x + card_width / 2,
            name_y,
            font_name,
            self.style.FONT_SIZE_NAME,
            context='card',
            text_color=self.style.TEXT_DARK
        )
    
    def render_card(self, canvas_obj, pokemon_data: dict, x: float, y: float,
                   card_width: float = None, card_height: float = None,
                   variant_mode: bool = False, section_prefix: str = None, 
                   section_suffix: str = None) -> None:
        """
        Draw a Pokémon card.
        
        Unified rendering method that handles both Generation PDFs and Variant PDFs.
        
        Args:
            canvas_obj: ReportLab canvas object
            pokemon_data: Dictionary with pokemon info (name, type, image, id, etc.)
            x: X position (top-left)
            y: Y position (top-left)
            card_width: Card width (default: CARD_WIDTH from constants)
            card_height: Card height (default: CARD_HEIGHT from constants)
            variant_mode: If True, uses variant data format (variant_name, trainer, etc.)
            section_prefix: Prefix from section-level data (e.g., "Mega", "Rocket's")
            section_suffix: Suffix from section-level data (e.g., "[EX]", "ex")
        """
        if card_width is None:
            card_width = self.style.CARD_WIDTH
        if card_height is None:
            card_height = self.style.CARD_HEIGHT
        
        header_height: float = self.style.HEADER_HEIGHT
        
        # ===== HEADER SETUP =====
        # Get primary type and its color
        types = pokemon_data.get('types', [])
        if not types and pokemon_data.get('type1'):
            types = [pokemon_data.get('type1')]
        
        if not types:
            raise ValueError(
                f"Pokémon '{pokemon_data.get('name', 'Unknown')}' "
                f"(ID: {pokemon_data.get('id', 'N/A')}) has no types defined"
            )
        
        pokemon_type = types[0]
        header_color = self.style.TYPE_COLORS.get(pokemon_type, self.style.TYPE_COLORS['Normal'])
        
        # ===== DRAW CARD STRUCTURE =====
        
        # Header background with type color (10% opaque)
        canvas_obj.setFillColor(HexColor(header_color), alpha=0.1)
        canvas_obj.rect(x, y + card_height - header_height, card_width, header_height, 
                       fill=True, stroke=False)
        
        # Card border
        canvas_obj.setLineWidth(0.5)
        canvas_obj.setStrokeColor(HexColor(self.style.CARD_BORDER_COLOR))
        canvas_obj.rect(x, y, card_width, card_height, fill=False, stroke=True)
        
        # ===== TYPE DISPLAY =====
        type_english = types[0]
        type_translated = self.type_translations.get(type_english, type_english)
        
        try:
            type_font: str = FontManager.get_font_name(self.language, bold=False)
            canvas_obj.setFont(type_font, self.style.FONT_SIZE_TYPE)
        except Exception:
            canvas_obj.setFont("Helvetica", self.style.FONT_SIZE_TYPE)
        
        canvas_obj.setFillColor(HexColor(self.style.TEXT_GRAY))
        type_x: float = x + card_width - 3  # Right edge with margin
        type_y: float = y + card_height - header_height + 6
        canvas_obj.drawRightString(type_x, type_y, type_translated)
        
        # ===== NAME RENDERING =====
        if variant_mode:
            # For variant PDFs - construct full variant name
            name: str = self._construct_variant_name(pokemon_data, section_prefix, section_suffix)
        else:
            # For generation PDFs
            name = pokemon_data.get('name', 'Unknown')
        
        try:
            font_name: str = FontManager.get_font_name(self.language, bold=True)
            canvas_obj.setFont(font_name, self.style.FONT_SIZE_NAME)
            canvas_obj.setFillColor(HexColor(self.style.TEXT_DARK))
            # Position Pokémon name centered vertically in header area
            # Header goes from (y + card_height - header_height) to (y + card_height)
            # Center name vertically in header
            name_y: float = y + card_height - header_height / 2 - 1 * mm
            
            # Check for special rendering needs (logo tokens in name)
            if '[EX_TERA]' in name:
                self._draw_card_name_with_ex_logo(canvas_obj, name, x, card_width, name_y, font_name, logo_type='ex_tera')
            elif '[EX_NEW]' in name:
                self._draw_card_name_with_ex_logo(canvas_obj, name, x, card_width, name_y, font_name, logo_type='ex_new')
            elif '[M]' in name and '[EX]' in name:
                self._draw_card_name_with_ex_logo(canvas_obj, name, x, card_width, name_y, font_name, logo_type='m_ex')
            elif '[EX]' in name:
                self._draw_card_name_with_ex_logo(canvas_obj, name, x, card_width, name_y, font_name, logo_type='ex')
            elif '[M]' in name:
                self._draw_card_name_with_ex_logo(canvas_obj, name, x, card_width, name_y, font_name, logo_type='ex')
            elif ('♂' in name or '♀' in name) and font_name == 'Helvetica-Bold':
                TextRenderer.draw_name_with_symbol_fallback(canvas_obj, name, x, card_width, name_y, font_name, 
                                                           self.style.FONT_SIZE_NAME, self.style.TEXT_DARK)
            else:
                canvas_obj.drawCentredString(x + card_width / 2, name_y, name)
        
        except Exception as e:
            logger.warning(f"Could not render name '{name}': {e}")
            # Fallback to Helvetica
            canvas_obj.setFont("Helvetica-Bold", self.style.FONT_SIZE_NAME)
            canvas_obj.setFillColor(HexColor(self.style.TEXT_DARK))
            canvas_obj.drawCentredString(x + card_width / 2, y + card_height - header_height + 11, name)
        
        # ===== IMAGE AREA =====
        image_height: float = card_height - header_height - 4 * mm
        canvas_obj.setFillColor(HexColor(self.style.CARD_BACKGROUND))
        canvas_obj.rect(x, y, card_width, image_height, fill=True, stroke=False)
        
        # Draw index number at bottom
        poke_num = pokemon_data.get('id') or pokemon_data.get('num', '???')
        poke_num_str: str = f"#{poke_num}" if not str(poke_num).startswith('#') else str(poke_num)
        darkened_color: str = self._darken_color(header_color, factor=0.6)
        canvas_obj.setFont("Helvetica-Bold", self.style.FONT_SIZE_ID)
        canvas_obj.setFillColor(HexColor(darkened_color))
        canvas_obj.drawCentredString(x + card_width / 2, y + 4 * mm, poke_num_str)
        
        # ===== IMAGE RENDERING =====
        image_source = pokemon_data.get('image_path') or pokemon_data.get('image_url')
        if image_source and self.image_cache:
            self._draw_image(canvas_obj, pokemon_data, x, y, card_width, image_height)
    
    def _construct_variant_name(self, pokemon_data: dict, section_prefix: str = None, 
                                section_suffix: str = None) -> str:
        """
        Construct translated variant name from pokemon_data.
        
        Fully data-driven approach using section-level prefix/suffix.
        
        Args:
            pokemon_data: Pokemon variant data dict
            section_prefix: Prefix from section data (e.g., "Mega", "Rocket's", "[M]")
            section_suffix: Suffix from section data (e.g., "[EX]", "ex", "[EX_NEW]")
        
        Returns:
            Fully formatted variant name with prefix/suffix
        """
        # Get base name in target language (unified name object structure - required)
        base_name = pokemon_data['name'][self.language]
        
        # Get pokemon-specific prefix/suffix (can override section defaults)
        pokemon_prefix = pokemon_data.get('prefix', None)
        pokemon_suffix = pokemon_data.get('suffix', None)
        
        # Use pokemon-specific values if present, otherwise use section values
        prefix = pokemon_prefix if pokemon_prefix is not None else (section_prefix or '')
        suffix = pokemon_suffix if pokemon_suffix is not None else (section_suffix or '')
        
        # Build name with prefix and suffix
        name = base_name
        
        # Add prefix (if present)
        if prefix:
            name = f"{prefix} {name}"
        
        # Handle variant_form (delta, x, y)
        variant_form = pokemon_data.get('variant_form', None)
        if variant_form:
            if variant_form == 'delta':
                # Delta Species: add δ symbol to suffix
                if suffix:
                    suffix = f"{suffix} δ"
            elif variant_form in ['x', 'y']:
                # Mega X/Y forms: add X or Y after name, before suffix
                name = f"{name} {variant_form.upper()}"
        
        # Add suffix (if present)
        if suffix:
            name = f"{name} {suffix}"
        
        return name
    
    def _draw_image(self, canvas_obj, pokemon_data: dict, x: float, y: float,
                   card_width: float, image_height: float) -> None:
        """Draw Pokémon image on card."""
        image_source = pokemon_data.get('image_path') or pokemon_data.get('image_url')
        
        if not image_source:
            return
        
        try:
            image_to_render = None
            
            if image_source.startswith(('http://', 'https://')):
                # URL - load from cache or download
                pokemon_id = pokemon_data.get('id')
                logger.debug(f"Getting image for #{pokemon_id}...")
                image_data = self.image_cache.get_image(pokemon_id, url=image_source)
                if image_data:
                    logger.debug(f"✓ Got image")
                    image_to_render = image_data
                else:
                    logger.debug(f"✗ Failed to get image data")
            else:
                # Local path
                if Path(image_source).exists():
                    logger.debug(f"Using local path: {image_source}")
                    image_to_render = image_source
            
            if image_to_render:
                logger.debug(f"Drawing image...")
                padding: float = self.style.IMAGE_PADDING
                max_width: float = (card_width - 2 * padding) / 2
                max_height: float = (image_height - 2 * padding) / 2
                
                img_x: float = x + (card_width - max_width) / 2
                img_y: float = y + (image_height - max_height) / 2 + padding
                
                canvas_obj.drawImage(
                    image_to_render, img_x, img_y,
                    width=max_width, height=max_height,
                    preserveAspectRatio=True
                )
                logger.debug(f"✓ Image drawn")
        
        except Exception as e:
            logger.debug(f"Could not render image from {image_source}: {e}")
