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
    from ..constants import CARD_WIDTH, CARD_HEIGHT
    from .translation_loader import TranslationLoader
except ImportError:
    # Fallback for direct imports
    from scripts.lib.fonts import FontManager
    from scripts.lib.constants import CARD_WIDTH, CARD_HEIGHT
    from scripts.lib.rendering.translation_loader import TranslationLoader

logger = logging.getLogger(__name__)


class CardStyle:
    """Unified card styling constants."""
    
    # Pokémon type color mapping
    TYPE_COLORS = {
        'Normal': '#A8A878',
        'Fire': '#F08030',
        'Water': '#6890F0',
        'Electric': '#F8D030',
        'Grass': '#78C850',
        'Ice': '#98D8D8',
        'Fighting': '#C03028',
        'Poison': '#A040A0',
        'Ground': '#E0C068',
        'Flying': '#A890F0',
        'Psychic': '#F85888',
        'Bug': '#A8B820',
        'Rock': '#B8A038',
        'Ghost': '#705898',
        'Dragon': '#7038F8',
        'Dark': '#705848',
        'Steel': '#B8B8D0',
        'Fairy': '#EE99AC',
    }
    
    # Card dimensions
    CARD_WIDTH = CARD_WIDTH
    CARD_HEIGHT = CARD_HEIGHT
    HEADER_HEIGHT = 12 * mm
    IMAGE_PADDING = 2 * mm
    
    # Colors
    CARD_BORDER_COLOR = '#CCCCCC'
    CARD_BACKGROUND = '#FFFFFF'
    TEXT_DARK = '#2D2D2D'
    TEXT_GRAY = '#5D5D5D'
    TEXT_LIGHT_GRAY = '#999999'
    
    # Fonts
    FONT_SIZE_NAME = 8
    FONT_SIZE_TYPE = 5
    FONT_SIZE_ID = 16
    FONT_SIZE_SUBTITLE = 4


class CardRenderer:
    """Unified renderer for Pokémon cards."""
    
    def __init__(self, language: str = 'en', image_cache=None, variant: str = None):
        """
        Initialize card renderer.
        
        Args:
            language: Language code for text rendering (e.g., 'en', 'de', 'fr')
            image_cache: Optional image cache for loading Pokémon images
            variant: Optional variant ID (ex_gen1, ex_gen2, etc.) for variant-specific rendering
        """
        self.language = language
        self.image_cache = image_cache
        self.variant = variant
        self.style = CardStyle()
        
        # Load type translations for this language
        self.type_translations = TranslationLoader.load_types(language)
    
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
    
    def _draw_name_with_symbol_fallback(self, canvas_obj, name: str, x: float, width: float, 
                                       y: float, primary_font: str):
        """
        Draw Pokémon name with gender symbol fallback.
        
        If name contains ♂/♀ symbols and primary font is Helvetica (Latin),
        render text parts with Helvetica and symbols with Songti (better Unicode support).
        
        Args:
            canvas_obj: ReportLab canvas
            name: Full name with potential symbols
            x: Card x position
            width: Card width (for centering)
            y: Y position
            primary_font: Primary font name
        """
        # Split name into parts and symbols
        parts = []
        current_part = ""
        
        for char in name:
            if char in '♂♀':
                if current_part:
                    parts.append(('text', current_part))
                    current_part = ""
                parts.append(('symbol', char))
            else:
                current_part += char
        
        if current_part:
            parts.append(('text', current_part))
        
        # Measure total width to center
        total_width = 0
        for part_type, part_text in parts:
            if part_type == 'text':
                total_width += canvas_obj.stringWidth(part_text, primary_font, self.style.FONT_SIZE_NAME)
            else:  # symbol
                total_width += canvas_obj.stringWidth(part_text, 'SongtiBold', self.style.FONT_SIZE_NAME)
        
        # Draw centered
        start_x = x + width / 2 - total_width / 2
        current_x = start_x
        
        for part_type, part_text in parts:
            if part_type == 'text':
                canvas_obj.setFont(primary_font, self.style.FONT_SIZE_NAME)
                canvas_obj.setFillColor(HexColor(self.style.TEXT_DARK))
                canvas_obj.drawString(current_x, y, part_text)
                current_x += canvas_obj.stringWidth(part_text, primary_font, self.style.FONT_SIZE_NAME)
            else:  # symbol
                canvas_obj.setFont('SongtiBold', self.style.FONT_SIZE_NAME)
                canvas_obj.setFillColor(HexColor(self.style.TEXT_DARK))
                canvas_obj.drawString(current_x, y, part_text)
                current_x += canvas_obj.stringWidth(part_text, 'SongtiBold', self.style.FONT_SIZE_NAME)
    
    def _draw_card_name_with_ex_logo(self, canvas_obj, name: str, x: float, card_width: float,
                                     name_y: float, font_name: str, logo_type: str = 'ex'):
        """
        Draw card name with EX or special variant logos.
        
        Handles Gen2 EX logos (M/EX), Gen3 EX logos ([EX_NEW], [EX_TERA]), etc.
        
        Args:
            canvas_obj: ReportLab canvas
            name: Full name with suffix
            x: Card x position
            card_width: Card width
            name_y: Y position for name
            font_name: Font to use
            logo_type: Type of logo ('ex', 'm_ex', 'ex_new', 'ex_tera')
        """
        # For now, just render the name normally
        # In a full implementation, this would render special logos for the suffixes
        canvas_obj.drawCentredString(x + card_width / 2, name_y, name)
    
    def render_card(self, canvas_obj, pokemon_data: dict, x: float, y: float,
                   card_width: float = None, card_height: float = None,
                   variant_mode: bool = False):
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
        """
        if card_width is None:
            card_width = self.style.CARD_WIDTH
        if card_height is None:
            card_height = self.style.CARD_HEIGHT
        
        header_height = self.style.HEADER_HEIGHT
        
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
            type_font = FontManager.get_font_name(self.language, bold=False)
            canvas_obj.setFont(type_font, self.style.FONT_SIZE_TYPE)
        except Exception:
            canvas_obj.setFont("Helvetica", self.style.FONT_SIZE_TYPE)
        
        canvas_obj.setFillColor(HexColor(self.style.TEXT_GRAY))
        type_x = x + card_width - 3  # Right edge with margin
        type_y = y + card_height - header_height + 6
        canvas_obj.drawRightString(type_x, type_y, type_translated)
        
        # ===== NAME RENDERING =====
        if variant_mode:
            # For variant PDFs - construct full variant name
            name = self._construct_variant_name(pokemon_data)
        else:
            # For generation PDFs
            name = pokemon_data.get('name', 'Unknown')
        
        try:
            font_name = FontManager.get_font_name(self.language, bold=True)
            canvas_obj.setFont(font_name, self.style.FONT_SIZE_NAME)
            canvas_obj.setFillColor(HexColor(self.style.TEXT_DARK))
            name_y = y + card_height - header_height + 11
            
            # Check for special rendering needs
            if self.variant == 'ex_gen2' and name.startswith('M ') and name.endswith(' EX'):
                self._draw_card_name_with_ex_logo(canvas_obj, name, x, card_width, name_y, font_name, logo_type='m_ex')
            elif self.variant == 'ex_gen2' and name.endswith(' EX'):
                self._draw_card_name_with_ex_logo(canvas_obj, name, x, card_width, name_y, font_name, logo_type='ex')
            elif self.variant == 'ex_gen3' and '[EX_TERA]' in name:
                self._draw_card_name_with_ex_logo(canvas_obj, name, x, card_width, name_y, font_name, logo_type='ex_tera')
            elif self.variant == 'ex_gen3' and '[EX_NEW]' in name:
                self._draw_card_name_with_ex_logo(canvas_obj, name, x, card_width, name_y, font_name, logo_type='ex_new')
            elif ('♂' in name or '♀' in name) and font_name == 'Helvetica-Bold':
                self._draw_name_with_symbol_fallback(canvas_obj, name, x, card_width, name_y, font_name)
            else:
                canvas_obj.drawCentredString(x + card_width / 2, name_y, name)
            
            # English subtitle for non-English languages
            name_en = pokemon_data.get('name_en', 'Unknown')
            if self.language != 'en' and name_en != 'Unknown' and name_en != name:
                canvas_obj.setFont("Helvetica", self.style.FONT_SIZE_SUBTITLE)
                canvas_obj.setFillColor(HexColor(self.style.TEXT_LIGHT_GRAY))
                name_en_y = y + card_height - header_height + 3
                canvas_obj.drawCentredString(x + card_width / 2, name_en_y, name_en)
        
        except Exception as e:
            logger.warning(f"Could not render name '{name}': {e}")
            # Fallback to Helvetica
            canvas_obj.setFont("Helvetica-Bold", self.style.FONT_SIZE_NAME)
            canvas_obj.setFillColor(HexColor(self.style.TEXT_DARK))
            canvas_obj.drawCentredString(x + card_width / 2, y + card_height - header_height + 11, name)
        
        # ===== IMAGE AREA =====
        image_height = card_height - header_height - 4 * mm
        canvas_obj.setFillColor(HexColor(self.style.CARD_BACKGROUND))
        canvas_obj.rect(x, y, card_width, image_height, fill=True, stroke=False)
        
        # Draw index number at bottom
        poke_num = pokemon_data.get('id') or pokemon_data.get('num', '???')
        poke_num_str = f"#{poke_num}" if not str(poke_num).startswith('#') else str(poke_num)
        darkened_color = self._darken_color(header_color, factor=0.6)
        canvas_obj.setFont("Helvetica-Bold", self.style.FONT_SIZE_ID)
        canvas_obj.setFillColor(HexColor(darkened_color))
        canvas_obj.drawCentredString(x + card_width / 2, y + 4 * mm, poke_num_str)
        
        # ===== IMAGE RENDERING =====
        image_source = pokemon_data.get('image_path') or pokemon_data.get('image_url')
        if image_source and self.image_cache:
            self._draw_image(canvas_obj, pokemon_data, x, y, card_width, image_height)
    
    def _construct_variant_name(self, pokemon_data: dict) -> str:
        """
        Construct translated variant name from pokemon_data.
        
        Handles Mega, Primal, Tera, Trainer variants with proper translations.
        
        Args:
            pokemon_data: Pokemon variant data dict
        
        Returns:
            Fully formatted variant name with prefix/suffix
        """
        # Get base name in target language
        language_key = {
            'de': 'name_de', 'en': 'name_en', 'fr': 'name_fr',
            'es': 'name_es', 'it': 'name_it', 'ja': 'name_ja',
            'ko': 'name_ko', 'zh_hans': 'name_zh_hans', 'zh_hant': 'name_zh_hant',
        }.get(self.language, 'name_en')
        
        base_name = pokemon_data.get(language_key, pokemon_data.get('name_en', 'Unknown'))
        
        # Get variant form and trainer
        variant_form = pokemon_data.get('variant_form', '')
        trainer = pokemon_data.get('trainer', '')
        
        # Map trainer names to language-specific prefixes
        trainer_prefixes = {
            'en': {'Rocket': "Rocket's", 'Imakuni': "Imakuni?'s", 'Aura': "Aura's", 'Folklore': "Folklore's"},
            'de': {'Rocket': "Rockets", 'Imakuni': "Imakuni?", 'Aura': "Auras", 'Folklore': "Folkores"},
            'fr': {'Rocket': "De Rocket", 'Imakuni': "D'Imakuni?", 'Aura': "D'Aura", 'Folklore': "De Folklore"},
            'es': {'Rocket': "De Rocket", 'Imakuni': "De Imakuni?", 'Aura': "De Aura", 'Folklore': "De Folklore"},
            'it': {'Rocket': "Di Rocket", 'Imakuni': "Di Imakuni?", 'Aura': "Di Aura", 'Folklore': "Di Folklore"},
            'ja': {'Rocket': "ロケット団の", 'Imakuni': "イマクニ?の", 'Aura': "アウラの", 'Folklore': "フォークロアの"},
            'ko': {'Rocket': "로켓단의", 'Imakuni': "이마쿠니의", 'Aura': "아우라의", 'Folklore': "포크로아의"},
            'zh_hans': {'Rocket': "火箭队的", 'Imakuni': "伊玛库尼的", 'Aura': "光环的", 'Folklore': "民俗的"},
            'zh_hant': {'Rocket': "火箭隊的", 'Imakuni': "伊瑪庫尼的", 'Aura': "光環的", 'Folklore': "民俗的"},
        }
        
        # Map variant forms to language-specific prefixes
        mega_prefix = 'Mega' if self.variant == 'ex_gen3' else 'M'
        
        variant_prefixes = {
            'en': {'mega': mega_prefix, 'primal': 'Primal'},
            'de': {'mega': mega_prefix, 'primal': 'Primal'},
            'fr': {'mega': 'Méga' if self.variant == 'ex_gen3' else 'Méga', 'primal': 'Primaire'},
            'es': {'mega': mega_prefix, 'primal': 'Primordial'},
            'it': {'mega': mega_prefix, 'primal': 'Primordiale'},
            'ja': {'mega': 'メガ', 'primal': 'プリメア'},
            'ko': {'mega': '메가', 'primal': '시원한'},
            'zh_hans': {'mega': '超级', 'primal': '原始'},
            'zh_hant': {'mega': '超級', 'primal': '原始'},
        }
        
        # Determine suffix based on variant
        if self.variant == 'ex_gen2':
            default_suffix = 'EX'
        elif self.variant == 'ex_gen3':
            default_suffix = '[EX_NEW]'
        else:
            default_suffix = 'ex'
        
        tera_suffix = '[EX_TERA]' if self.variant == 'ex_gen3' else default_suffix
        
        variant_suffixes = {
            'en': {'normal': default_suffix, 'mega': default_suffix, 'primal': default_suffix, 'tera': tera_suffix},
            'de': {'normal': default_suffix, 'mega': default_suffix, 'primal': default_suffix, 'tera': tera_suffix},
            'fr': {'normal': default_suffix, 'mega': default_suffix, 'primal': default_suffix, 'tera': tera_suffix},
            'es': {'normal': default_suffix, 'mega': default_suffix, 'primal': default_suffix, 'tera': tera_suffix},
            'it': {'normal': default_suffix, 'mega': default_suffix, 'primal': default_suffix, 'tera': tera_suffix},
            'ja': {'normal': default_suffix, 'mega': default_suffix, 'primal': default_suffix, 'tera': tera_suffix},
            'ko': {'normal': default_suffix, 'mega': default_suffix, 'primal': default_suffix, 'tera': tera_suffix},
            'zh_hans': {'normal': default_suffix, 'mega': default_suffix, 'primal': default_suffix, 'tera': tera_suffix},
            'zh_hant': {'normal': default_suffix, 'mega': default_suffix, 'primal': default_suffix, 'tera': tera_suffix},
        }
        
        # Build name with appropriate prefix and suffix
        name = base_name
        
        # Add trainer prefix first
        trainer_prefixes_map = trainer_prefixes.get(self.language, {})
        if trainer and trainer in trainer_prefixes_map:
            name = f"{trainer_prefixes_map[trainer]} {name}"
        
        # Add prefix for Mega/Primal
        prefixes_map = variant_prefixes.get(self.language, {})
        if variant_form in prefixes_map:
            name = f"{prefixes_map[variant_form]} {name}"
        
        # Add suffix
        if base_name != 'Unknown':
            suffix_form = variant_form if variant_form else 'normal'
            suffixes_map = variant_suffixes.get(self.language, {})
            suffix = suffixes_map.get(suffix_form, default_suffix)
            
            # Add delta symbol for delta variants
            if variant_form == 'delta':
                suffix = f"{suffix} δ"
            
            name = f"{name} {suffix}"
        
        return name
    
    def _draw_image(self, canvas_obj, pokemon_data: dict, x: float, y: float,
                   card_width: float, image_height: float):
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
                padding = self.style.IMAGE_PADDING
                max_width = (card_width - 2 * padding) / 2
                max_height = (image_height - 2 * padding) / 2
                
                img_x = x + (card_width - max_width) / 2
                img_y = y + (image_height - max_height) / 2 + padding
                
                canvas_obj.drawImage(
                    image_to_render, img_x, img_y,
                    width=max_width, height=max_height,
                    preserveAspectRatio=True
                )
                logger.debug(f"✓ Image drawn")
        
        except Exception as e:
            logger.debug(f"Could not render image from {image_source}: {e}")
