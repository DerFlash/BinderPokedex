"""
Card Template - Reusable card rendering for both Generation and Variant PDFs

Provides a parametrized template for drawing Pokémon cards with:
- Type-based header colors
- Pokémon name and number
- Image area
- Stats display
"""

from pathlib import Path
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor

from .fonts import FontManager
from .constants import CARD_WIDTH, CARD_HEIGHT

import logging

logger = logging.getLogger(__name__)


# Pokémon type color mapping
TYPE_COLORS = {
    'Normal': '#A8A878', 'Fire': '#F08030', 'Water': '#6890F0',
    'Electric': '#F8D030', 'Grass': '#78C850', 'Ice': '#98D8D8',
    'Fighting': '#C03028', 'Poison': '#A040A0', 'Ground': '#E0C068',
    'Flying': '#A890F0', 'Psychic': '#F85888', 'Bug': '#A8B820',
    'Rock': '#B8A038', 'Ghost': '#705898', 'Dragon': '#7038F8',
    'Dark': '#705848', 'Steel': '#B8B8D0', 'Fairy': '#EE99AC',
}


class CardTemplate:
    """Template for rendering Pokémon cards."""
    
    def __init__(self, language: str = 'en', image_cache=None):
        """
        Initialize card template.
        
        Args:
            language: Language code for text rendering
            image_cache: Optional image cache for loading Pokémon images
        """
        self.language = language
        self.image_cache = image_cache
    
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
    
    def draw_card(self, canvas_obj, pokemon_data: dict, x: float, y: float, 
                  card_width: float = CARD_WIDTH, card_height: float = CARD_HEIGHT,
                  variant_mode: bool = False):
        """
        Draw a Pokémon card.
        
        Args:
            canvas_obj: ReportLab canvas object
            pokemon_data: Dictionary with pokemon info
            x: X position (top-left)
            y: Y position (top-left)
            card_width: Card width in mm
            card_height: Card height in mm
            variant_mode: If True, uses variant data format (id, base_pokemon_name, variant_name)
        """
        header_height = 12 * mm
        
        # Get primary type and its color
        pokemon_type = pokemon_data.get('types', ['Normal'])[0] if pokemon_data.get('types') else 'Normal'
        header_color = TYPE_COLORS.get(pokemon_type, '#A8A878')
        
        # Draw header with type color (10% opaque)
        canvas_obj.setFillColor(HexColor(header_color), alpha=0.1)
        canvas_obj.rect(x, y + card_height - header_height, card_width, header_height, fill=True, stroke=False)
        
        # Card border
        canvas_obj.setLineWidth(0.5)
        canvas_obj.setStrokeColor(HexColor("#CCCCCC"))
        canvas_obj.rect(x, y, card_width, card_height, fill=False, stroke=True)
        
        # Note: Pokédex number moved to bottom of card (see below)
        
        # Type (header right)
        types = pokemon_data.get('types', [])
        if types:
            type_text = types[0]
            canvas_obj.setFont("Helvetica", 5)
            type_width = canvas_obj.stringWidth(type_text, "Helvetica", 5)
            canvas_obj.setFillColor(HexColor("#5D5D5D"))
            canvas_obj.drawString(x + card_width - type_width - 3, y + card_height - header_height + 5, type_text)
        
        # Pokémon name (centered with language support)
        if variant_mode:
            # For variants: translate variant name by combining prefix + translated base name
            # E.g., "Mega Venusaur" → "Mega Bisaflor" (DE), "Mega Charizard X" → "Mega Glurak X" (DE)
            language_key = {
                'de': 'name_de',
                'en': 'name_en',
                'fr': 'name_fr',
                'es': 'name_es',
                'it': 'name_it',
                'ja': 'name_ja',
                'ko': 'name_ko',
                'zh_hans': 'name_zh_hans',
                'zh_hant': 'name_zh_hant',
            }.get(self.language, 'name_en')
            
            base_name_translated = pokemon_data.get(language_key, pokemon_data.get('name_en', 'Unknown'))
            name_en = pokemon_data.get('name_en', 'Unknown')
            
            # Construct translated variant name from structured fields (variant_prefix + variant_form)
            variant_prefix = pokemon_data.get('variant_prefix', '')
            variant_form = pokemon_data.get('variant_form', '')
            
            if variant_prefix and base_name_translated != 'Unknown':
                name = f"{variant_prefix} {base_name_translated}"
                if variant_form:
                    # Capitalize form suffix (x → X, y → Y, etc.)
                    name += f" {variant_form.upper()}"
            else:
                # Fallback if something went wrong
                name = base_name_translated
        else:
            # For generation PDFs
            name = pokemon_data.get('name', 'Unknown')
            name_en = pokemon_data.get('name_en', 'Unknown')
        
        try:
            font_name = FontManager.get_font_name(self.language, bold=True)
            canvas_obj.setFont(font_name, 8)
            canvas_obj.setFillColor(HexColor("#2D2D2D"))
            name_y = y + card_height - header_height + 11
            
            # Check for gender symbols that might need fallback
            if ('♂' in name or '♀' in name) and font_name == 'Helvetica-Bold':
                self._draw_name_with_symbol_fallback(canvas_obj, name, x, card_width, name_y, font_name)
            else:
                canvas_obj.drawCentredString(x + card_width / 2, name_y, name)
            
            # English subtitle for non-English languages
            if self.language != 'en' and name_en != 'Unknown' and name_en != name:
                canvas_obj.setFont("Helvetica", 4)
                canvas_obj.setFillColor(HexColor("#999999"))
                name_en_y = y + card_height - header_height + 3
                canvas_obj.drawCentredString(x + card_width / 2, name_en_y, name_en)
                
        except Exception as e:
            logger.warning(f"Could not render name '{name}': {e}")
            canvas_obj.setFont("Helvetica-Bold", 8)
            canvas_obj.setFillColor(HexColor("#2D2D2D"))
            canvas_obj.drawCentredString(x + card_width / 2, y + card_height - header_height + 11, name)
        
        # Image area
        image_height = card_height - header_height - 4 * mm
        canvas_obj.setFillColor(HexColor("#FFFFFF"))
        canvas_obj.rect(x, y, card_width, image_height, fill=True, stroke=False)
        
        # Draw index number centered at bottom of card
        poke_num = pokemon_data.get('id') or pokemon_data.get('num', '???')
        poke_num_str = f"#{poke_num}" if not str(poke_num).startswith('#') else str(poke_num)
        darkened_type_color = self._darken_color(header_color, factor=0.6)
        canvas_obj.setFont("Helvetica-Bold", 16)
        canvas_obj.setFillColor(HexColor(darkened_type_color))
        canvas_obj.drawCentredString(x + card_width / 2, y + 4 * mm, poke_num_str)
        
        # Draw image if available
        image_source = pokemon_data.get('image_path') or pokemon_data.get('image_url')
        if image_source and self.image_cache:
            self._draw_image(canvas_obj, pokemon_data, x, y, card_width, image_height)
    
    def _draw_image(self, canvas_obj, pokemon_data: dict, x: float, y: float, 
                    card_width: float, image_height: float):
        """Draw Pokémon image on card."""
        image_source = pokemon_data.get('image_path') or pokemon_data.get('image_url')
        
        if not image_source:
            return
        
        try:
            image_to_render = None
            
            if image_source.startswith('http://') or image_source.startswith('https://'):
                pokemon_id = pokemon_data.get('id')
                image_data = self.image_cache.get_image(pokemon_id, url=image_source)
                if image_data:
                    image_to_render = image_data
            else:
                if Path(image_source).exists():
                    image_to_render = image_source
            
            if image_to_render:
                # Center image in card
                img_max_width = card_width * 0.8
                img_max_height = image_height * 0.8
                
                img_x = x + (card_width - img_max_width) / 2
                img_y = y + (image_height - img_max_height) / 2
                
                canvas_obj.drawImage(
                    image_to_render, img_x, img_y,
                    width=img_max_width, height=img_max_height,
                    preserveAspectRatio=True
                )
        except Exception as e:
            logger.debug(f"Could not load image: {e}")
    
    def _draw_name_with_symbol_fallback(self, canvas_obj, name: str, x: float, 
                                        card_width: float, y: float, font_name: str):
        """Draw name with symbol fallback for gender symbols."""
        # This is a helper for rendering names with ♂/♀ symbols
        try:
            # Try rendering the whole thing first
            canvas_obj.drawCentredString(x + card_width / 2, y, name)
        except:
            # Fallback: render without symbol
            name_clean = name.replace('♂', 'M').replace('♀', 'F')
            canvas_obj.drawCentredString(x + card_width / 2, y, name_clean)
