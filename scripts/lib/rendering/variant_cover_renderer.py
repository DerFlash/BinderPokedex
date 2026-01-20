"""
Variant Cover Renderer - Unified variant cover page rendering

Consolidates variant cover rendering logic from cover_template.py.
Provides consistent styling for variant collections (ex_gen1, mega_evolution, etc.)

Features:
- Variant-specific color schemes
- Section separators with featured Pokémon
- Multi-language support
- Clean, modern design
- CJK text rendering support
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor

try:
    from ..fonts import FontManager
    from ..constants import PAGE_WIDTH, PAGE_HEIGHT, VARIANT_COLORS
    from ..utils import TranslationHelper
    from .translation_loader import TranslationLoader
    from .logo_renderer import LogoRenderer
except ImportError:
    # Fallback for direct imports
    from scripts.lib.fonts import FontManager
    from scripts.lib.constants import PAGE_WIDTH, PAGE_HEIGHT, VARIANT_COLORS
    from scripts.lib.utils import TranslationHelper
    from scripts.lib.rendering.translation_loader import TranslationLoader
    from scripts.lib.rendering.logo_renderer import LogoRenderer

logger = logging.getLogger(__name__)


class VariantCoverStyle:
    """Variant cover styling constants."""
    
    # Variant color scheme - imported from constants.py
    VARIANT_COLORS = VARIANT_COLORS
    
    # Dimensions
    PAGE_WIDTH = PAGE_WIDTH
    PAGE_HEIGHT = PAGE_HEIGHT
    PAGE_MARGIN = 10 * mm
    
    # Header
    HEADER_HEIGHT = 100 * mm
    TITLE_FONT_SIZE = 42
    SUBTITLE_FONT_SIZE = 18
    
    # Fonts
    HEADER_FONT = "Helvetica-Bold"
    CONTENT_FONT = "Helvetica"
    
    # Colors
    BACKGROUND_COLOR = '#FFFFFF'
    TEXT_WHITE = '#FFFFFF'
    TEXT_DARK = '#333333'
    TEXT_GRAY = '#666666'
    TEXT_LIGHT_GRAY = '#CCCCCC'


class VariantCoverRenderer:
    """Renderer for variant collection cover pages."""
    
    def __init__(self, language: str = 'en', image_cache=None):
        """
        Initialize variant cover renderer.
        
        Args:
            language: Language code for text rendering (de, en, fr, etc.)
            image_cache: Optional image cache for loading Pokémon images
        """
        self.language = language
        self.image_cache = image_cache
        self.style = VariantCoverStyle()
        self.translation_loader = TranslationLoader()
        self.translations = TranslationHelper.load_translations(language)
    
    def render_variant_cover(self, canvas_obj, variant_data: dict, pokemon_list: list, 
                            color: str, section_title: Optional[str] = None,
                            section_id: Optional[str] = None):
        """
        Render a variant collection cover page.
        
        Args:
            canvas_obj: ReportLab canvas object
            variant_data: Variant collection metadata
            pokemon_list: List of Pokémon in collection
            color: Hex color for header stripe
            section_title: Optional section title (for separator pages)
            section_id: Optional section identifier (mega, primal, tera, etc.)
        """
        # White background
        canvas_obj.setFillColor(HexColor(self.style.BACKGROUND_COLOR))
        canvas_obj.rect(0, 0, self.style.PAGE_WIDTH, self.style.PAGE_HEIGHT, 
                       fill=True, stroke=False)
        
        # ===== TOP COLORED STRIPE =====
        canvas_obj.setFillColor(HexColor(color))
        canvas_obj.rect(0, self.style.PAGE_HEIGHT - self.style.HEADER_HEIGHT, 
                       self.style.PAGE_WIDTH, self.style.HEADER_HEIGHT, 
                       fill=True, stroke=False)
        
        # Subtle overlay effect
        canvas_obj.setFillColor(HexColor("#000000"), alpha=0.05)
        canvas_obj.rect(0, self.style.PAGE_HEIGHT - self.style.HEADER_HEIGHT,
                       self.style.PAGE_WIDTH, self.style.HEADER_HEIGHT,
                       fill=True, stroke=False)
        
        # ===== TITLE =====
        canvas_obj.setFont(self.style.HEADER_FONT, self.style.TITLE_FONT_SIZE)
        canvas_obj.setFillColor(HexColor(self.style.TEXT_WHITE))
        title_y = self.style.PAGE_HEIGHT - 30 * mm
        canvas_obj.drawCentredString(self.style.PAGE_WIDTH / 2, title_y, "Binder Pokédex")
        
        # Decorative underline
        canvas_obj.setStrokeColor(HexColor(self.style.TEXT_WHITE))
        canvas_obj.setLineWidth(1.5)
        canvas_obj.line(40 * mm, title_y - 8, self.style.PAGE_WIDTH - 40 * mm, title_y - 8)
        
        # ===== VARIANT NAME / TITLE =====
        variant_type = variant_data.get('variant_type', 'unknown')
        variant_name = variant_data.get('variant_name', variant_type)
        
        # Get localized title from title dict
        title_dict = variant_data.get('title', {})
        localized_title = title_dict.get(self.language) if isinstance(title_dict, dict) else variant_name
        if not localized_title:
            localized_title = variant_name
        
        # Check if there's a subtitle
        has_subtitle = variant_data.get('subtitle') is not None
        
        # Use appropriate font for text
        try:
            font_name = FontManager.get_font_name(self.language, bold=False)
            canvas_obj.setFont(font_name, 14)
        except:
            canvas_obj.setFont(self.style.CONTENT_FONT, 14)
        
        canvas_obj.setFillColor(HexColor(self.style.TEXT_WHITE))
        
        # On cover page without section_title: show localized title
        # On separator page with section_title: show variant_name + section title
        if section_title:
            # Separator page: show variant_name at -55mm
            canvas_obj.drawCentredString(self.style.PAGE_WIDTH / 2, 
                                         self.style.PAGE_HEIGHT - 55 * mm, variant_name)
        else:
            # Cover page: show localized title at -55mm (only if has_subtitle is False)
            # If has_subtitle is True, show variant_name at -55mm and subtitle at -65mm
            if not has_subtitle:
                # No subtitle: show localized title only (with logo support)
                try:
                    font_name = FontManager.get_font_name(self.language, bold=True)
                    canvas_obj.setFont(font_name, self.style.SUBTITLE_FONT_SIZE)
                except:
                    canvas_obj.setFont(self.style.HEADER_FONT, self.style.SUBTITLE_FONT_SIZE)
                canvas_obj.setFillColor(HexColor(self.style.TEXT_WHITE))
                
                # Use logo-aware rendering for localized title
                self._draw_section_title_with_logos(
                    canvas_obj,
                    localized_title,
                    self.style.PAGE_WIDTH / 2,
                    self.style.PAGE_HEIGHT - 60 * mm,
                    self.style.SUBTITLE_FONT_SIZE
                )
            else:
                # Has subtitle: show variant_name at -55mm and subtitle at -65mm
                try:
                    font_name = FontManager.get_font_name(self.language, bold=False)
                    canvas_obj.setFont(font_name, 14)
                except:
                    canvas_obj.setFont(self.style.CONTENT_FONT, 14)
                canvas_obj.setFillColor(HexColor(self.style.TEXT_WHITE))
                canvas_obj.drawCentredString(self.style.PAGE_WIDTH / 2, 
                                             self.style.PAGE_HEIGHT - 55 * mm, variant_name)
                
                # Draw subtitle at -65mm
                try:
                    font_name = FontManager.get_font_name(self.language, bold=True)
                    canvas_obj.setFont(font_name, self.style.SUBTITLE_FONT_SIZE)
                except:
                    canvas_obj.setFont(self.style.HEADER_FONT, self.style.SUBTITLE_FONT_SIZE)
                subtitle_dict = variant_data.get('subtitle', {})
                localized_subtitle = subtitle_dict.get(self.language) if isinstance(subtitle_dict, dict) else ''
                if localized_subtitle:
                    canvas_obj.setFillColor(HexColor(self.style.TEXT_WHITE))
                    
                    # Use logo-aware rendering for subtitle too
                    self._draw_section_title_with_logos(
                        canvas_obj,
                        localized_subtitle,
                        self.style.PAGE_WIDTH / 2,
                        self.style.PAGE_HEIGHT - 65 * mm,
                        self.style.SUBTITLE_FONT_SIZE
                    )
        
        # ===== SECTION TITLE (for separator pages) =====
        if section_title:
            # Separator page with section title
            # Try to render with logos (EX, Mega, etc.)
            self._draw_section_title_with_logos(
                canvas_obj,
                section_title,
                self.style.PAGE_WIDTH / 2,
                self.style.PAGE_HEIGHT - 65 * mm,
                self.style.SUBTITLE_FONT_SIZE
            )
        
        # ===== COLLECTION INFO =====
        pokemon_count = len(pokemon_list)
        
        try:
            font_name = FontManager.get_font_name(self.language, bold=False)
            canvas_obj.setFont(font_name, 14)
        except:
            canvas_obj.setFont(self.style.CONTENT_FONT, 14)
        
        canvas_obj.setFillColor(HexColor(self.style.TEXT_DARK))
        # Use translation-aware text
        count_key = f"{pokemon_count}_pokemon_collection"
        # Fallback to translated template or English
        if self.language != 'en':
            # Build translation for each language
            lang_texts = {
                'de': f"{pokemon_count} Pokémon in dieser Sammlung",
                'fr': f"{pokemon_count} Pokémon dans cette collection",
                'es': f"{pokemon_count} Pokémon en esta colección",
                'it': f"{pokemon_count} Pokémon in questa collezione",
                'ja': f"{pokemon_count} Pokémon",
                'ko': f"{pokemon_count} 포켓몬",
                'zh_hans': f"{pokemon_count} 宝可梦",
                'zh_hant': f"{pokemon_count} 寶可夢",
            }
            count_text = lang_texts.get(self.language, f"{pokemon_count} Pokémon in this collection")
        else:
            count_text = f"{pokemon_count} Pokémon in this collection"
        canvas_obj.drawCentredString(self.style.PAGE_WIDTH / 2, 120 * mm, count_text)
        
        # Decorative separator
        canvas_obj.setStrokeColor(HexColor(color))
        canvas_obj.setLineWidth(1)
        canvas_obj.line(40 * mm, 105 * mm, self.style.PAGE_WIDTH - 40 * mm, 105 * mm)
        
        # ===== FEATURED POKÉMON =====
        # Check both 'iconic_pokemon' (from variant main level) and 'iconic_pokemon_ids' (from section separators)
        iconic_ids = variant_data.get('iconic_pokemon_ids') or variant_data.get('iconic_pokemon', [])
        if not iconic_ids:
            # Use first 3 Pokémon as featured - handle variant IDs like '#003_EX1'
            iconic_ids = []
            for p in pokemon_list[:3]:
                try:
                    pid = str(p.get('id', p.get('num', '0'))).split('_')[0].lstrip('#')
                    iconic_ids.append(int(pid))
                except (ValueError, AttributeError):
                    pass
        
        if iconic_ids:
            self._draw_featured_pokemon(canvas_obj, iconic_ids, pokemon_list)
        
        # ===== FOOTER =====
        self._draw_footer(canvas_obj, color)
    
    def _draw_featured_pokemon(self, canvas_obj, iconic_ids: List[int], pokemon_list: list):
        """Draw featured Pokémon at the bottom of cover."""
        # Build pokemon dict by ID - handle different ID formats
        pokemon_by_id = {}
        for p in pokemon_list:
            try:
                pid = str(p.get('id', p.get('num', '0'))).split('_')[0].lstrip('#')
                pokemon_by_id[int(pid)] = p
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
        
        if not clean_iconic_ids:
            # Fallback to first 3 Pokémon
            clean_iconic_ids = [int(str(p.get('id', 0)).split('_')[0].lstrip('#')) for p in pokemon_list[:3]]
        
        pokemon_count = len(clean_iconic_ids[:3])
        total_width = self.style.PAGE_WIDTH - (30 * mm)
        spacing_per_pokemon = total_width / pokemon_count
        
        for idx, poke_id in enumerate(clean_iconic_ids[:3]):
            x_center = 15 * mm + spacing_per_pokemon * (idx + 0.5)
            
            card_width = 65 * mm
            card_height = 90 * mm
            x = x_center - card_width / 2
            y = 10 * mm
            
            pokemon = pokemon_by_id.get(poke_id)
            
            if pokemon and self.image_cache:
                image_source = pokemon.get('image_path') or pokemon.get('image_url')
                if image_source:
                    try:
                        image_to_render = None
                        if image_source.startswith('http://') or image_source.startswith('https://'):
                            image_to_render = self.image_cache.get_image(poke_id, 
                                                                         url=image_source, 
                                                                         timeout=3)
                        elif Path(image_source).exists():
                            image_to_render = image_source
                        
                        if image_to_render:
                            img_width = card_width * 0.72
                            img_height = card_height * 0.72
                            img_x = x_center - img_width / 2
                            img_y = y
                            canvas_obj.drawImage(image_to_render, img_x, img_y,
                                               width=img_width, height=img_height,
                                               preserveAspectRatio=True)
                    except Exception as e:
                        logger.debug(f"Could not load image for featured Pokémon {poke_id}: {e}")
    
    def _draw_section_title_with_logos(self, canvas_obj, section_title: str, 
                                       x_center: float, y: float, font_size: int):
        """
        Draw section title with embedded logos for special tokens.
        
        Delegates to LogoRenderer for unified logo handling.
        
        Supports tokens:
        - [M] for Mega Evolution logo
        - [EX] for EX logo  
        - [EX_NEW] for EX NEW logo (Gen 3+)
        - [EX_TERA] for EX TERA logo
        
        Args:
            canvas_obj: ReportLab canvas
            section_title: Title text (may contain tokens)
            x_center: X coordinate for centering
            y: Y coordinate for text baseline
            font_size: Font size for text
        """
        # Set font and color
        try:
            font_name = FontManager.get_font_name(self.language, bold=True)
            canvas_obj.setFont(font_name, font_size)
        except:
            canvas_obj.setFont(self.style.HEADER_FONT, font_size)
        
        canvas_obj.setFillColor(HexColor(self.style.TEXT_WHITE))
        
        # Use unified LogoRenderer for consistent rendering
        LogoRenderer.draw_text_with_logos(
            canvas_obj,
            section_title,
            x_center,
            y,
            canvas_obj._fontname,
            font_size,
            context='title',
            text_color=self.style.TEXT_WHITE
        )
    
    def _draw_footer(self, canvas_obj, color: str):
        """Draw footer with print instructions."""
        try:
            font_name = FontManager.get_font_name(self.language, bold=False)
            canvas_obj.setFont(font_name, 6)
        except:
            canvas_obj.setFont(self.style.CONTENT_FONT, 6)
        
        canvas_obj.setFillColor(HexColor(self.style.TEXT_LIGHT_GRAY))
        
        # Footer text with translations
        ui_trans = self.translation_loader.load_ui(self.language)
        
        print_text = ui_trans.get('cover_print_borderless', 'Print borderless')
        cutting_text = ui_trans.get('cover_follow_cutting', 'Follow cutting guides')
        
        footer_parts = [
            print_text,
            cutting_text,
            "Binder Pokédex Project",
            datetime.now().strftime('%Y-%m-%d')
        ]
        footer_text = " • ".join(footer_parts)
        
        text_width = canvas_obj.stringWidth(footer_text, canvas_obj._fontname, 6) \
            if hasattr(canvas_obj, '_fontname') else len(footer_text) * 2
        x_pos = (self.style.PAGE_WIDTH - text_width) / 2
        canvas_obj.drawString(x_pos, 2.5 * mm, footer_text)
