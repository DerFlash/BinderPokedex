"""
Unified Logo Renderer - Centralized logo rendering for variants

Consolidates all logo rendering logic (EX, M, EX_NEW, EX_TERA) into a single,
reusable component used by both cover pages and card rendering.

This ensures consistent logo placement, sizing, and rendering across all contexts.
"""

import logging
from pathlib import Path
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor

logger = logging.getLogger(__name__)


class LogoRenderer:
    """Unified renderer for variant logos (EX, M, EX_NEW, EX_TERA, MEGA)."""
    
    # Logo file locations (uses logos/ directory structure)
    LOGO_FILES = {
        'ex': "logos/ex",  # Non-localized (default.png)
        'm': "logos/m_pokemon",  # Non-localized (default.png)
        'ex_new': "logos/ex_new",  # Non-localized (default.png)
        'ex_tera': "logos/ex_tera",  # Non-localized (default.png)
        'mega': "logos/mega_evolution",  # Localized (de.png, en.png, ja.png, etc.)
    }
    
    # Standard logo dimensions for different contexts
    LOGO_DIMENSIONS = {
        'title': {  # For cover/section titles
            'ex': (7.3 * mm, 8.8 * mm),
            'm': (6.65 * mm, 5.3 * mm),
            'ex_new': (7.3 * mm, 8.8 * mm),
            'ex_tera': (7.3 * mm, 8.8 * mm),
            'mega': (80 * mm, 40 * mm),  # Mega Evolution logo dimensions (10x larger)
        },
        'card': {  # For card names
            'ex': (6 * mm, 7.2 * mm),
            'm': (5 * mm, 4 * mm),
            'ex_new': (6 * mm, 7.2 * mm),
            'ex_tera': (6 * mm, 7.2 * mm),
            'mega': (65 * mm, 32.5 * mm),  # Mega Evolution logo dimensions for cards (10x larger)
        }
    }
    
    @staticmethod
    def get_logo_path(logo_key: str, language: str = 'en') -> Path:
        """
        Get full path to logo file with localization support.
        
        Fallback chain:
        1. Try localized logo: logos/{logo_key}/{language}.png
        2. Try default logo: logos/{logo_key}/default.png
        
        Args:
            logo_key: Logo identifier ('ex', 'm', 'ex_new', 'ex_tera', 'mega')
            language: Language code (de, en, fr, es, it, ja, ko, zh_hans, zh_hant)
        
        Returns:
            Path to logo file (may not exist)
        """
        # From scripts/pdf/lib/rendering/logo_renderer.py -> project root (4 levels up)
        # Then into images/ directory
        base_path = Path(__file__).parent.parent.parent.parent.parent / "images"
        logo_config = LogoRenderer.LOGO_FILES.get(logo_key, "")
        
        if not logo_config:
            return base_path / "unknown.png"
        
        logo_dir = base_path / logo_config
        
        # Try localized version first
        localized_logo = logo_dir / f"{language}.png"
        if localized_logo.exists():
            return localized_logo
        
        # Fallback to default.png
        default_logo = logo_dir / "default.png"
        if default_logo.exists():
            return default_logo
        
        # If neither exists, return the localized path (caller will handle missing file)
        return localized_logo
    
    @staticmethod
    def parse_text_with_logos(text: str) -> list:
        """
        Parse text into segments of plain text and logo tokens.
        
        Args:
            text: Text that may contain tokens like [M], [EX], [EX_NEW], [EX_TERA]
        
        Returns:
            List of tuples: [('text', 'plain text'), ('logo', 'ex'), ('text', 'more text'), ...]
        """
        segments = []
        remaining = text
        
        while remaining:
            # Check for tokens (longest first)
            if remaining.startswith('[EX_TERA]'):
                segments.append(('logo', 'ex_tera'))
                remaining = remaining[9:].lstrip()
            elif remaining.startswith('[EX_NEW]'):
                segments.append(('logo', 'ex_new'))
                remaining = remaining[8:].lstrip()
            elif remaining.startswith('[MEGA]'):
                segments.append(('logo', 'mega'))
                remaining = remaining[6:].lstrip()
            elif remaining.startswith('[M]'):
                segments.append(('logo', 'm'))
                remaining = remaining[3:].lstrip()
            elif remaining.startswith('[EX]'):
                segments.append(('logo', 'ex'))
                remaining = remaining[4:].lstrip()
            else:
                # Find next token
                token_positions = []
                for token, idx in [('[EX_TERA]', 9), ('[EX_NEW]', 8), ('[MEGA]', 6), ('[M]', 3), ('[EX]', 4)]:
                    pos = remaining.find(token)
                    if pos >= 0:
                        token_positions.append((pos, idx))
                
                if token_positions:
                    next_idx = min(token_positions)[0]
                    text_segment = remaining[:next_idx].rstrip()
                else:
                    text_segment = remaining.rstrip()
                    next_idx = len(remaining)
                
                if text_segment:
                    segments.append(('text', text_segment))
                
                remaining = remaining[next_idx:]
        
        return segments
    
    @staticmethod
    def draw_text_with_logos(canvas_obj, text: str, x_center: float, y: float,
                            font_name: str, font_size: int, context: str = 'title',
                            text_color: str = '#2D2D2D', language: str = 'en') -> None:
        """
        Draw text with embedded logos, centered at x_center.
        
        Args:
            canvas_obj: ReportLab canvas
            text: Text with optional logo tokens
            x_center: X coordinate for centering
            y: Y coordinate (baseline for text)
            font_name: Font name
            font_size: Font size
            context: 'title' or 'card' (determines logo sizing)
            text_color: Hex color for text
            language: Language code for localized logos (de, en, fr, etc.)
        """
        canvas_obj.setFont(font_name, font_size)
        canvas_obj.setFillColor(HexColor(text_color))
        
        # Check if text contains any logo tokens
        if '[EX_TERA]' not in text and '[EX_NEW]' not in text and '[MEGA]' not in text and '[M]' not in text and '[EX]' not in text:
            # No logos - render plain text
            canvas_obj.drawCentredString(x_center, y, text)
            return
        
        # Parse text into segments
        segments = LogoRenderer.parse_text_with_logos(text)
        
        # Get logo dimensions for this context
        dims = LogoRenderer.LOGO_DIMENSIONS.get(context, LogoRenderer.LOGO_DIMENSIONS['title'])
        gap = 1.5 * mm
        
        # Calculate total width
        total_width = 0
        for seg_type, seg_value in segments:
            if seg_type == 'text':
                total_width += canvas_obj.stringWidth(seg_value + ' ', font_name, font_size)
            elif seg_type == 'logo':
                logo_width, _ = dims.get(seg_value, (6 * mm, 7.2 * mm))
                total_width += logo_width + gap
        
        # Draw segments starting from calculated position
        current_x = x_center - total_width / 2
        
        for seg_type, seg_value in segments:
            if seg_type == 'text':
                canvas_obj.drawString(current_x, y, seg_value + ' ')
                current_x += canvas_obj.stringWidth(seg_value + ' ', font_name, font_size)
            elif seg_type == 'logo':
                logo_file = LogoRenderer.get_logo_path(seg_value, language)
                logo_width, logo_height = dims.get(seg_value, (6 * mm, 7.2 * mm))
                logo_y = y - (logo_height / 2) + 1.2 * mm
                
                try:
                    if logo_file.exists():
                        canvas_obj.drawImage(
                            str(logo_file),
                            current_x,
                            logo_y,
                            width=logo_width,
                            height=logo_height,
                            preserveAspectRatio=True,
                            mask='auto'
                        )
                    current_x += logo_width + gap
                except Exception as e:
                    logger.debug(f"Could not draw {seg_value} logo: {e}")
                    current_x += logo_width + gap
    
    @staticmethod
    def draw_text_with_suffix_logo(canvas_obj, text: str, suffix: str, x: float, width: float, y: float,
                                  font_name: str, font_size: int, context: str = 'card',
                                  text_color: str = '#2D2D2D') -> None:
        """
        Draw text with a logo suffix, left-aligned within width.
        
        Args:
            canvas_obj: ReportLab canvas
            text: Plain text (e.g., "Charizard")
            suffix: Suffix token (e.g., " [EX_NEW]" or " EX")
            x: X position (left)
            width: Available width
            y: Y position (baseline)
            font_name: Font name
            font_size: Font size
            context: 'title' or 'card' (determines logo sizing)
            text_color: Hex color for text
        """
        canvas_obj.setFont(font_name, font_size)
        canvas_obj.setFillColor(HexColor(text_color))
        
        # Parse suffix to identify logo type
        logo_type = None
        if '[EX_TERA]' in suffix:
            logo_type = 'ex_tera'
            suffix_text = ' [EX_TERA]'
        elif '[EX_NEW]' in suffix:
            logo_type = 'ex_new'
            suffix_text = ' [EX_NEW]'
        elif ' EX' in suffix or suffix == 'EX':
            logo_type = 'ex'
            suffix_text = ' EX'
        elif ' ex' in suffix or suffix == 'ex':
            logo_type = 'ex'
            suffix_text = ' ex'
        else:
            # No recognized suffix - render as plain text
            canvas_obj.drawString(x, y, text + suffix)
            return
        
        if not logo_type:
            canvas_obj.drawString(x, y, text + suffix)
            return
        
        # Get logo dimensions
        dims = LogoRenderer.LOGO_DIMENSIONS.get(context, LogoRenderer.LOGO_DIMENSIONS['card'])
        logo_width, logo_height = dims.get(logo_type, (6 * mm, 7.2 * mm))
        gap = 1 * mm
        
        # Draw text
        canvas_obj.drawString(x, y, text)
        
        # Draw logo
        logo_file = LogoRenderer.get_logo_path(logo_type)
        logo_x = x + canvas_obj.stringWidth(text, font_name, font_size) + gap
        logo_y = y - (logo_height / 2)
        
        try:
            if logo_file.exists():
                canvas_obj.drawImage(
                    str(logo_file),
                    logo_x,
                    logo_y,
                    width=logo_width,
                    height=logo_height,
                    preserveAspectRatio=True,
                    mask='auto'
                )
        except Exception as e:
            logger.debug(f"Could not draw {logo_type} logo: {e}")
