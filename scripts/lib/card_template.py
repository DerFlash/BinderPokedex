"""
⚠️  DEPRECATED - Use scripts.lib.rendering.CardRenderer instead

Card Template - Reusable card rendering for both Generation and Variant PDFs

This module is deprecated and will be removed in a future version.
All card rendering functionality has been consolidated into the unified
CardRenderer class in the rendering module for better code organization
and consistency.

Migration Guide:
  Old: from card_template import CardTemplate
  New: from rendering import CardRenderer

  Old: template.draw_card(canvas, pokemon_data, x, y)
  New: renderer.render_card(canvas, pokemon_data, x, y)

See: scripts/lib/rendering/README.md for migration details.

Provides a parametrized template for drawing Pokémon cards with:
- Type-based header colors
- Pokémon name and number
- Image area
- Stats display
"""

import json
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

# Load type translations
def _load_type_translations():
    """Load type translations from i18n/translations.json"""
    try:
        # Use absolute path from card_template.py location
        card_template_file = Path(__file__).resolve()  # Get absolute path
        translations_path = card_template_file.parent.parent.parent / 'i18n' / 'translations.json'
        
        if translations_path.exists():
            with open(translations_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('types', {})
    except Exception as e:
        logger.warning(f"Could not load type translations: {e}")
    return {}

TYPE_TRANSLATIONS = _load_type_translations()


class CardTemplate:
    """Template for rendering Pokémon cards."""
    
    def __init__(self, language: str = 'en', image_cache=None, variant: str = None):
        """
        Initialize card template.
        
        Args:
            language: Language code for text rendering
            image_cache: Optional image cache for loading Pokémon images
            variant: Optional variant ID (ex_gen1, ex_gen2, ex_gen3, etc.) for suffix formatting
        """
        self.language = language
        self.image_cache = image_cache
        self.variant = variant
    
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
        types = pokemon_data.get('types', [])
        if not types:
            raise ValueError(f"Pokémon '{pokemon_data.get('name_en', 'Unknown')}' (ID: {pokemon_data.get('pokemon_id', 'N/A')}) has no types defined. This is required for card rendering.")
        
        pokemon_type = types[0]
        if pokemon_type not in TYPE_COLORS:
            raise ValueError(f"Unknown Pokémon type '{pokemon_type}' for '{pokemon_data.get('name_en', 'Unknown')}'. Valid types: {', '.join(sorted(TYPE_COLORS.keys()))}")
        
        header_color = TYPE_COLORS[pokemon_type]
        
        # Draw header with type color (10% opaque)
        canvas_obj.setFillColor(HexColor(header_color), alpha=0.1)
        canvas_obj.rect(x, y + card_height - header_height, card_width, header_height, fill=True, stroke=False)
        
        # Card border
        canvas_obj.setLineWidth(0.5)
        canvas_obj.setStrokeColor(HexColor("#CCCCCC"))
        canvas_obj.rect(x, y, card_width, card_height, fill=False, stroke=True)
        
        # Note: Pokédex number moved to bottom of card (see below)
        
        # Type (header right)
        # Get type from either 'types' array or 'type1' field
        types = pokemon_data.get('types', [])
        if not types and pokemon_data.get('type1'):
            types = [pokemon_data.get('type1')]
        
        if types:
            type_english = types[0]
            # Translate type to current language
            language_types = TYPE_TRANSLATIONS.get(self.language, TYPE_TRANSLATIONS.get('en', {}))
            type_text = language_types.get(type_english, type_english)
            
            try:
                # Use same font approach as Pokémon names - this works for CJK!
                type_font = FontManager.get_font_name(self.language, bold=False)
                canvas_obj.setFont(type_font, 5)
            except:
                canvas_obj.setFont("Helvetica", 5)
            
            canvas_obj.setFillColor(HexColor("#5D5D5D"))
            # Use drawRightString for proper right-alignment without overflow
            type_x = x + card_width - 3  # Right edge with margin
            type_y = y + card_height - header_height + 6
            canvas_obj.drawRightString(type_x, type_y, type_text)
        
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
            
            # Construct translated variant name based on variant_form and trainer
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
            
            # Map variant forms to language-specific prefixes and suffixes
            # For Gen2: 'M' (short form), for Gen3: 'Mega' (full form)
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
            
            # Determine suffix based on variant (Gen1: "ex", Gen2: "EX", Gen3: "[EX_NEW]" or "[EX_TERA]")
            if self.variant == 'ex_gen2':
                default_suffix = 'EX'  # Gen2: uppercase
            elif self.variant == 'ex_gen3':
                default_suffix = '[EX_NEW]'  # Gen3: new logo token
            else:
                default_suffix = 'ex'  # Gen1: lowercase
            
            # For Gen3, Tera Pokémon get [EX_TERA] instead of [EX_NEW]
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
            name = base_name_translated
            
            # Add trainer prefix first (Rocket's, Imakuni?'s, etc.)
            trainer_prefixes_map = trainer_prefixes.get(self.language, {})
            if trainer and trainer in trainer_prefixes_map:
                name = f"{trainer_prefixes_map[trainer]} {name}"
            
            # Add prefix for Mega/Primal
            prefixes_map = variant_prefixes.get(self.language, {})
            if variant_form in prefixes_map:
                name = f"{prefixes_map[variant_form]} {name}"
            
            # Add suffix ex/EX for all variants
            if base_name_translated != 'Unknown':
                suffix_form = variant_form if variant_form else 'normal'
                suffixes_map = variant_suffixes.get(self.language, {})
                suffix = suffixes_map.get(suffix_form, default_suffix)
                
                # Add delta symbol for delta variants
                if variant_form == 'delta':
                    suffix = f"{suffix} δ"
                
                name = f"{name} {suffix}"
        else:
            # For generation PDFs
            name = pokemon_data.get('name', 'Unknown')
            name_en = pokemon_data.get('name_en', 'Unknown')
        
        try:
            font_name = FontManager.get_font_name(self.language, bold=True)
            canvas_obj.setFont(font_name, 8)
            canvas_obj.setFillColor(HexColor("#2D2D2D"))
            name_y = y + card_height - header_height + 11
            
            # Check for M prefix and EX suffix in Gen2, or tokens in Gen3, and draw with logos
            if self.variant == 'ex_gen2' and name.startswith('M ') and name.endswith(' EX'):
                self._draw_card_name_with_ex_logo(canvas_obj, name, x, card_width, name_y, font_name, logo_type='m_ex')
            elif self.variant == 'ex_gen2' and name.endswith(' EX'):
                self._draw_card_name_with_ex_logo(canvas_obj, name, x, card_width, name_y, font_name, logo_type='ex')
            elif self.variant == 'ex_gen3' and '[EX_TERA]' in name:
                self._draw_card_name_with_ex_logo(canvas_obj, name, x, card_width, name_y, font_name, logo_type='ex_tera')
            elif self.variant == 'ex_gen3' and '[EX_NEW]' in name:
                self._draw_card_name_with_ex_logo(canvas_obj, name, x, card_width, name_y, font_name, logo_type='ex_new')
            # Check for gender symbols that might need fallback
            elif ('♂' in name or '♀' in name) and font_name == 'Helvetica-Bold':
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

    def _draw_card_name_with_ex_logo(self, canvas_obj, name, x, card_width, name_y, font_name, logo_type='ex'):
        """
        Draw Pokémon name with M/EX logos for Gen2/Gen3 variants.
        Supports combinations: M + EX logos, single logos, or tokens.
        
        Args:
            logo_type: 'ex' for Gen2 EX logo, 'm_ex' for Gen2 M+EX logos, 'ex_new' for Gen3 EX_NEW, 'ex_tera' for Gen3 EX_TERA
        """
        import os
        
        if logo_type == 'm_ex':
            # Gen2 Mega: Remove "M " prefix and " EX" suffix, draw with M logo + name + EX logo
            if not (name.startswith('M ') and name.endswith(' EX')):
                canvas_obj.drawCentredString(x + card_width / 2, name_y, name)
                return
            name_without_prefix_suffix = name[2:-3]  # Remove "M " and " EX"
            m_logo_file = os.path.join(
                os.path.dirname(__file__),
                "../../data/variants/M_Pokémon.png"
            )
            ex_logo_file = os.path.join(
                os.path.dirname(__file__),
                "../../data/variants/EXLogoBig.png"
            )
            
            if not os.path.exists(m_logo_file) or not os.path.exists(ex_logo_file):
                # Fallback if logos missing
                canvas_obj.drawCentredString(x + card_width / 2, name_y, name)
                return
            
            # Measure the name text width
            canvas_obj.setFont(font_name, 8)
            name_width = canvas_obj.stringWidth(name_without_prefix_suffix, font_name, 8)
            
            # Logo dimensions
            m_logo_width = 4.5 * mm
            m_logo_height = 4.5 * mm * (664/1070)  # Maintain aspect ratio
            ex_logo_width = 5.95 * mm
            ex_logo_height = 5.95 * mm * (664/1070)  # Maintain aspect ratio
            spacing = 0.5 * mm
            
            total_width = m_logo_width + spacing + name_width + spacing + ex_logo_width
            
            center_x = x + card_width / 2
            start_x = center_x - total_width / 2
            
            # Draw M logo
            m_logo_x = start_x
            m_logo_y = name_y - (m_logo_height / 2) + 1 * mm
            canvas_obj.drawImage(
                m_logo_file,
                m_logo_x,
                m_logo_y,
                width=m_logo_width,
                height=m_logo_height,
                preserveAspectRatio=True,
                mask='auto'
            )
            
            # Draw name part
            current_x = m_logo_x + m_logo_width + spacing
            canvas_obj.setFont(font_name, 8)
            canvas_obj.setFillColor(HexColor("#2D2D2D"))
            canvas_obj.drawString(current_x, name_y, name_without_prefix_suffix)
            
            # Draw EX logo
            ex_logo_x = current_x + name_width + spacing
            ex_logo_y = name_y - (ex_logo_height / 2) + 1 * mm
            canvas_obj.drawImage(
                ex_logo_file,
                ex_logo_x,
                ex_logo_y,
                width=ex_logo_width,
                height=ex_logo_height,
                preserveAspectRatio=True,
                mask='auto'
            )
            
        elif logo_type == 'ex':
            # Gen2: Remove " EX" suffix
            if not name.endswith(' EX'):
                canvas_obj.drawCentredString(x + card_width / 2, name_y, name)
                return
            name_without_ex = name[:-3]  # Remove " EX"
            logo_file = os.path.join(
                os.path.dirname(__file__),
                "../../data/variants/EXLogoBig.png"
            )
        elif logo_type == 'ex_tera':
            # Gen3 Tera: Remove "[EX_TERA]" token
            if '[EX_TERA]' not in name:
                canvas_obj.drawCentredString(x + card_width / 2, name_y, name)
                return
            name_without_ex = name.replace(' [EX_TERA]', '').replace('[EX_TERA]', '')
            logo_file = os.path.join(
                os.path.dirname(__file__),
                "../../data/variants/EXTeraLogo.png"
            )
        else:  # ex_new
            # Gen3: Remove "[EX_NEW]" token
            if '[EX_NEW]' not in name:
                canvas_obj.drawCentredString(x + card_width / 2, name_y, name)
                return
            name_without_ex = name.replace(' [EX_NEW]', '').replace('[EX_NEW]', '')
            logo_file = os.path.join(
                os.path.dirname(__file__),
                "../../data/variants/EXLogoNew.png"
            )
        
        # Only for single-logo cases (ex, ex_tera, ex_new)
        if logo_type != 'm_ex':
            if not os.path.exists(logo_file):
                # Fallback if logo missing
                canvas_obj.drawCentredString(x + card_width / 2, name_y, name)
                return
            
            # Measure the name text width
            canvas_obj.setFont(font_name, 8)
            name_width = canvas_obj.stringWidth(name_without_ex, font_name, 8)
            
            # Calculate positions for centered layout
            logo_width = 5.95 * mm  # 15% smaller than cover (7mm → 5.95mm)
            logo_height = 5.95 * mm * (664/1070)  # Maintain aspect ratio (1070/664)
            spacing = 0.6 * mm  # Increased spacing for more room
            total_width = name_width + logo_width + spacing
            
            center_x = x + card_width / 2
            start_x = center_x - total_width / 2
            
            # Draw name part
            canvas_obj.setFont(font_name, 8)
            canvas_obj.setFillColor(HexColor("#2D2D2D"))
            canvas_obj.drawString(start_x, name_y, name_without_ex)
            
            # Draw logo
            logo_x = start_x + name_width + spacing
            logo_y = name_y - (logo_height / 2) + 1 * mm  # Center vertically with text, then shift up 1mm
            
            canvas_obj.drawImage(
                logo_file,
                logo_x,
                logo_y,
                width=logo_width,
                height=logo_height,
                preserveAspectRatio=True,
                mask='auto'
            )

