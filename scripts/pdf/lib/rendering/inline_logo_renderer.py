"""
Inline Logo Renderer - Renders text with embedded logo images

Replaces logo tokens ([EX], [M], etc.) with actual PNG/SVG logo images
inline with the text. Similar to LogoRenderer but uses image files.
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Tuple

from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from PIL import Image

logger = logging.getLogger(__name__)


# Token → Logo file mapping
TOKEN_TO_LOGO_TYPE = {
    'EX_TERA': 'ex_tera',   # [EX_TERA] → ex_tera.png
    'EX_NEW': 'ex_gen3',    # [EX_NEW] → ex_gen3.png
    'EX': 'ex_gen2',        # [EX] → ex_gen2.png
    'M': 'mega',            # [M] → mega.png
}

# Logo dimensions (width × height in mm)
LOGO_DIMENSIONS = {
    'ex': (8, 3),           # Gen1: small, lowercase
    'ex_gen2': (10, 5),     # Gen2: larger, uppercase
    'ex_gen3': (8, 4),      # Gen3: new design
    'ex_tera': (12, 5),     # Tera: largest
    'mega': (6, 6),         # Mega: square
}


class InlineLogoRenderer:
    """Renders text with inline logo images."""
    
    @staticmethod
    def get_logo_dimensions(logo_type: str) -> Tuple[float, float]:
        """
        Get logo dimensions in mm.
        
        Args:
            logo_type: Logo type (e.g., 'ex_gen2', 'mega')
        
        Returns:
            (width, height) tuple in mm
        """
        return LOGO_DIMENSIONS.get(logo_type, (8, 3))
    
    @staticmethod
    def get_logo_path(logo_type: str) -> Path:
        """
        Get path to logo image file.
        
        Args:
            logo_type: Logo type
        
        Returns:
            Path to logo PNG file
        """
        # Assuming logos are in images/logos/
        base_dir = Path(__file__).parent.parent.parent.parent.parent
        logo_path = base_dir / 'images' / 'logos' / f"{logo_type}.png"
        return logo_path
    
    @classmethod
    def parse_text_with_logos(cls, text: str) -> List[Dict]:
        """
        Parse text and extract logo tokens.
        
        Args:
            text: Text with logo tokens (e.g., "Charizard [EX]")
        
        Returns:
            List of segments: [{'type': 'text'|'logo', 'content': '...', ...}]
        
        Example:
            "Charizard [EX]" →
            [
                {'type': 'text', 'content': 'Charizard '},
                {'type': 'logo', 'logo_type': 'ex_gen2'}
            ]
        """
        logo_pattern = r'\[(EX_TERA|EX_NEW|EX|M)\]'
        segments = []
        last_end = 0
        
        for match in re.finditer(logo_pattern, text):
            # Text before token
            if match.start() > last_end:
                segments.append({
                    'type': 'text',
                    'content': text[last_end:match.start()]
                })
            
            # Logo token
            logo_token = match.group(1)
            logo_type = TOKEN_TO_LOGO_TYPE.get(logo_token, 'ex')
            segments.append({
                'type': 'logo',
                'logo_type': logo_type,
                'token': match.group(0)  # For fallback
            })
            
            last_end = match.end()
        
        # Text after last token
        if last_end < len(text):
            segments.append({
                'type': 'text',
                'content': text[last_end:]
            })
        
        # If no matches, entire text is one segment
        if not segments:
            segments = [{'type': 'text', 'content': text}]
        
        return segments
    
    @classmethod
    def calculate_total_width(cls, segments: List[Dict], font_name: str, 
                             font_size: float) -> float:
        """
        Calculate total width of text + logos in points.
        
        Args:
            segments: Parsed segments from parse_text_with_logos()
            font_name: Font name for text
            font_size: Font size in points
        
        Returns:
            Total width in points
        """
        total_width = 0.0
        
        for segment in segments:
            if segment['type'] == 'text':
                # Measure text width
                text_width = stringWidth(segment['content'], font_name, font_size)
                total_width += text_width
            else:  # logo
                # Logo width in mm → points (1mm = ~2.83465 points)
                logo_width, _ = cls.get_logo_dimensions(segment['logo_type'])
                total_width += logo_width * mm
        
        return total_width
    
    @classmethod
    def render_text_with_inline_logos(cls, canvas, text: str, x: float, y: float,
                                     font_name: str, font_size: float,
                                     text_color: str = '#2D2D2D',
                                     centered: bool = True) -> bool:
        """
        Render text with inline logo images.
        
        Args:
            canvas: ReportLab canvas
            text: Text with logo tokens (e.g., "Charizard [EX]")
            x: X position (center if centered=True, left otherwise)
            y: Y position (text baseline)
            font_name: Font name
            font_size: Font size in points
            text_color: Text color (hex)
            centered: If True, text+logos are centered at x
        
        Returns:
            True if successful
        
        Example:
            render_text_with_inline_logos(
                canvas, "Charizard [EX]", 31.5*mm, 82*mm,
                'Helvetica-Bold', 11, centered=True
            )
        """
        try:
            # 1. Parse text into segments
            segments = cls.parse_text_with_logos(text)
            
            # 2. Calculate total width for centering
            total_width = cls.calculate_total_width(segments, font_name, font_size)
            
            # 3. Determine starting X position
            if centered:
                current_x = x - (total_width / 2)
            else:
                current_x = x
            
            # 4. Set up canvas for text
            canvas.setFont(font_name, font_size)
            canvas.setFillColor(HexColor(text_color))
            
            # 5. Render segments
            for segment in segments:
                if segment['type'] == 'text':
                    # Render text
                    canvas.drawString(current_x, y, segment['content'])
                    
                    # Move cursor
                    text_width = stringWidth(segment['content'], font_name, font_size)
                    current_x += text_width
                
                else:  # logo
                    # Get logo info
                    logo_type = segment['logo_type']
                    logo_path = cls.get_logo_path(logo_type)
                    
                    if logo_path.exists():
                        # Render logo image
                        logo_width, logo_height = cls.get_logo_dimensions(logo_type)
                        
                        # Vertical alignment: center logo relative to text
                        # Font size ≈ cap height, logo should align with text
                        logo_y = y + (font_size * 0.2)  # 20% above baseline
                        
                        try:
                            # Open image to check for transparency
                            pil_image = Image.open(logo_path)
                            
                            # Check if image has alpha channel (PNG transparency)
                            if pil_image.mode in ('RGBA', 'LA') or (pil_image.mode == 'P' and 'transparency' in pil_image.info):
                                # Convert to RGBA for consistent handling
                                if pil_image.mode != 'RGBA':
                                    pil_image = pil_image.convert('RGBA')
                                
                                # Create ImageReader with PIL image
                                from io import BytesIO
                                img_buffer = BytesIO()
                                pil_image.save(img_buffer, format='PNG')
                                img_buffer.seek(0)
                                
                                canvas.drawImage(
                                    ImageReader(img_buffer),
                                    current_x,
                                    logo_y,
                                    width=logo_width * mm,
                                    height=logo_height * mm,
                                    preserveAspectRatio=True,
                                    mask='auto'
                                )
                            else:
                                # No transparency, draw directly
                                canvas.drawImage(
                                    str(logo_path),
                                    current_x,
                                    logo_y,
                                    width=logo_width * mm,
                                    height=logo_height * mm,
                                    preserveAspectRatio=True
                                )
                        except Exception as e:
                            logger.warning(f"Failed to render logo {logo_path}: {e}")
                            # Fallback to token text
                            fallback_text = segment.get('token', '[?]')
                            canvas.drawString(current_x, y, fallback_text)
                            text_width = stringWidth(fallback_text, font_name, font_size)
                            current_x += text_width
                            continue
                        
                        # Move cursor
                        current_x += logo_width * mm
                    else:
                        # Logo file not found - fallback to token text
                        logger.warning(f"Logo file not found: {logo_path}")
                        fallback_text = segment.get('token', '[?]')
                        canvas.drawString(current_x, y, fallback_text)
                        text_width = stringWidth(fallback_text, font_name, font_size)
                        current_x += text_width
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to render text with inline logos: {e}")
            return False
