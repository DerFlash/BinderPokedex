"""
Title Renderer - Unified cover title and subtitle rendering

Consolidates title/subtitle rendering logic for both Pokédex and Variant covers.

Features:
- 4 rendering modes: with_subtitle, no_subtitle, separator, separator_with_subtitle
- Logo support (EX, Mega, etc.)
- Multi-language support
- Canonical implementation for both CoverRenderer and VariantCoverRenderer
"""

import logging
from typing import Callable, Optional

from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor

try:
    from ..fonts import FontManager
    from .logo_renderer import LogoRenderer
except ImportError:
    from scripts.lib.fonts import FontManager
    from scripts.lib.rendering.logo_renderer import LogoRenderer

logger = logging.getLogger(__name__)


class TitleRenderer:
    """Canonical title and subtitle rendering for cover pages."""
    
    # Title rendering modes
    MODE_WITH_SUBTITLE = 'with_subtitle'      # title + subtitle (for both Pokédex and Variants)
    MODE_NO_SUBTITLE = 'no_subtitle'          # title only (centered)
    MODE_SEPARATOR = 'separator'              # section_title only (for separators)
    
    @staticmethod
    def draw_title(canvas_obj, cover_data: dict, language: str, page_width: float,
                   page_height: float, translation_getter: Optional[Callable] = None,
                   font_name: str = None, subtitle_font_size: int = 24,
                   title_y_offset: float = 55 * mm, subtitle_y_offset: float = 65 * mm,
                   section_title: Optional[str] = None):
        """
        Draw title and subtitle based on cover_data configuration.
        
        Args:
            canvas_obj: ReportLab canvas object
            cover_data: Dict with title, subtitle, title_mode, logo fields
            language: Language code for text rendering
            page_width: Page width for centering
            page_height: Page height for positioning
            translation_getter: Optional callback for translating keys (for generation covers)
            font_name: Font name to use (defaults to language-appropriate font)
            subtitle_font_size: Font size for title/subtitle
            title_y_offset: Y position for title (from top)
            subtitle_y_offset: Y position for subtitle (from top)
            section_title: Optional section title (for separator pages)
        """
        # Get configuration
        title_dict = cover_data.get('title', {})
        subtitle_dict = cover_data.get('subtitle', {})
        title_mode = cover_data.get('title_mode', 'with_subtitle')
        logo = cover_data.get('logo')
        
        # Get localized strings
        if isinstance(title_dict, dict):
            title_text = title_dict.get(language, title_dict.get('en', ''))
        else:
            title_text = str(title_dict) if title_dict else ''
        
        if isinstance(subtitle_dict, dict):
            subtitle_text = subtitle_dict.get(language, subtitle_dict.get('en', ''))
        else:
            subtitle_text = str(subtitle_dict) if subtitle_dict else ''
        
        # Get font
        if not font_name:
            try:
                font_name = FontManager.get_font_name(language, bold=True)
            except:
                font_name = "Helvetica-Bold"
        
        canvas_obj.setFont(font_name, subtitle_font_size)
        canvas_obj.setFillColor(HexColor("#FFFFFF"))
        
        # ===== MODE: with_subtitle =====
        # Show: title (or variant_name if present) at -55mm, subtitle at -65mm
        # Works for both Pokédex (Generation + Region) and Variants (Name + Series)
        if title_mode == TitleRenderer.MODE_WITH_SUBTITLE:
            # For variants with variant_name: show variant_name at -55mm
            # For Pokédex: show title (Generation) at -55mm
            display_title = cover_data.get('variant_name', title_text)
            
            # Draw title/variant_name at -55mm
            if display_title:
                try:
                    plain_font = FontManager.get_font_name(language, bold=False)
                    canvas_obj.setFont(plain_font, 14)
                except:
                    canvas_obj.setFont("Helvetica", 14)
                canvas_obj.setFillColor(HexColor("#FFFFFF"))
                canvas_obj.drawCentredString(page_width / 2, page_height - 55 * mm, display_title)
            
            # Draw subtitle at -65mm with logo support
            if subtitle_text:
                canvas_obj.setFont(font_name, subtitle_font_size)
                LogoRenderer.draw_text_with_logos(
                    canvas_obj,
                    subtitle_text,
                    page_width / 2,
                    page_height - 65 * mm,
                    font_name,
                    subtitle_font_size,
                    context='subtitle',
                    text_color="#FFFFFF",
                    language=language
                )
        
        # ===== MODE: no_subtitle =====
        # Show: title with logo support at -60mm (centered vertically between -55 and -65)
        elif title_mode == TitleRenderer.MODE_NO_SUBTITLE:
            canvas_obj.setFont(font_name, subtitle_font_size)
            LogoRenderer.draw_text_with_logos(
                canvas_obj,
                title_text,
                page_width / 2,
                page_height - 60 * mm,
                font_name,
                subtitle_font_size,
                context='title',
                text_color="#FFFFFF",
                language=language
            )
        
        # ===== MODE: separator =====
        # Show: section_title with logo support at -65mm
        elif title_mode == TitleRenderer.MODE_SEPARATOR:
            if section_title:
                canvas_obj.setFont(font_name, subtitle_font_size)
                LogoRenderer.draw_text_with_logos(
                    canvas_obj,
                    section_title,
                    page_width / 2,
                    page_height - 65 * mm,
                    font_name,
                    subtitle_font_size,
                    context='separator',
                    text_color="#FFFFFF",
                    language=language
                )
            else:
                # Fallback: show variant_name if no section_title
                variant_name = cover_data.get('variant_name')
                if variant_name:
                    try:
                        plain_font = FontManager.get_font_name(language, bold=False)
                        canvas_obj.setFont(plain_font, 14)
                    except:
                        canvas_obj.setFont("Helvetica", 14)
                    canvas_obj.drawCentredString(page_width / 2, page_height - 55 * mm, variant_name)
