"""
Text Rendering Module

Handles text rendering for all languages including CJK with proper Unicode support.
Direct ReportLab API usage - no escaping or manipulation needed.
"""

import logging
from reportlab.pdfbase import pdfmetrics

logger = logging.getLogger(__name__)


class TextRenderer:
    """
    Renders text in multi-language PDFs with proper CJK support.
    
    Strategy:
    - Use ReportLab's direct canvas methods
    - Let ReportLab handle UTF-16-BE encoding internally
    - No escaping, no manipulation, no monkey-patching
    - Unicode special characters (♀/♂) converted to text alternatives
    """
    
    # Symbol substitutions for Unicode characters that may not render
    SYMBOL_SUBSTITUTIONS = {
        '♀': '(w)',  # Female symbol
        '♂': '(m)',  # Male symbol
    }
    
    @staticmethod
    def convert_special_symbols(text: str, font_name: str = None) -> str:
        """
        Convert Unicode symbols to text alternatives based on font support.
        
        CJK fonts (Songti, AppleGothic) fully support Unicode gender symbols.
        Latin fonts (Helvetica) may not render them properly, so convert to (w)/(m).
        
        Args:
            text: Input text with potential special symbols
            font_name: Font name to determine conversion strategy
        
        Returns:
            Text with symbols converted (or not, depending on font)
        """
        # CJK fonts have full Unicode support - keep symbols
        if font_name and any(cjk in font_name.lower() for cjk in ['songti', 'applegothic']):
            return text
        
        # Latin fonts - convert symbols to text alternatives
        result = text
        for symbol, replacement in TextRenderer.SYMBOL_SUBSTITUTIONS.items():
            result = result.replace(symbol, replacement)
        return result
    
    @staticmethod
    def render_text(canvas, x: float, y: float, text: str, font_name: str, 
                   font_size: float, fill_color=None, text_anchor='start'):
        """
        Render text on a ReportLab canvas with proper encoding handling.
        
        Args:
            canvas: ReportLab canvas object
            x: X position
            y: Y position
            text: Text to render
            font_name: Font name (must be registered)
            font_size: Font size in points
            fill_color: Color tuple (r, g, b) or Color object
            text_anchor: 'start', 'middle', or 'end' for alignment
        
        Raises:
            ValueError: If font is not registered
        """
        if not text:
            return
        
        # Verify font is registered - fail if not
        try:
            font_obj = pdfmetrics.getFont(font_name)
        except Exception as e:
            logger.error(f"Font not registered: {font_name}")
            raise ValueError(f"Font '{font_name}' not registered. "
                           f"Make sure all fonts are properly registered at startup.") from e
        
        # Convert special symbols (based on font capability)
        processed_text = TextRenderer.convert_special_symbols(text, font_name)
        
        # Set font and color
        canvas.setFont(font_name, font_size)
        if fill_color:
            canvas.setFillColor(*fill_color) if isinstance(fill_color, tuple) else canvas.setFillColor(fill_color)
        
        # Handle text alignment
        if text_anchor == 'middle':
            canvas.drawCentredString(x, y, processed_text)
        elif text_anchor == 'end':
            canvas.drawRightString(x, y, processed_text)
        else:  # 'start' (default)
            canvas.drawString(x, y, processed_text)
    
    @staticmethod
    def measure_text_width(text: str, font_name: str, font_size: float) -> float:
        """
        Measure the width of text when rendered in a specific font.
        
        Args:
            text: Text to measure
            font_name: Font name (must be registered)
            font_size: Font size in points
        
        Returns:
            Width in points
        
        Raises:
            ValueError: If font is not registered
        """
        if not text:
            return 0
        
        # Verify font is registered
        try:
            font_obj = pdfmetrics.getFont(font_name)
        except Exception as e:
            logger.error(f"Font not registered: {font_name}")
            raise ValueError(f"Font '{font_name}' not registered") from e
        
        # Convert special symbols (based on font capability)
        processed_text = TextRenderer.convert_special_symbols(text, font_name)
        
        # Calculate width
        width = font_obj.stringWidth(processed_text, font_size)
        return width
    
    @staticmethod
    def wrap_text(text: str, font_name: str, font_size: float, 
                  max_width: float, separator: str = ' ') -> list:
        """
        Wrap text to fit within a maximum width.
        
        Handles word wrapping for multi-line text rendering.
        
        Args:
            text: Text to wrap
            font_name: Font name
            font_size: Font size
            max_width: Maximum width in points
            separator: Word separator (default: space)
        
        Returns:
            List of text lines that fit within max_width
        """
        if not text:
            return []
        
        try:
            font_obj = pdfmetrics.getFont(font_name)
        except Exception as e:
            logger.error(f"Font not registered: {font_name}")
            raise ValueError(f"Font '{font_name}' not registered") from e
        
        words = text.split(separator)
        lines = []
        current_line = []
        
        for word in words:
            test_line = separator.join(current_line + [word])
            width = font_obj.stringWidth(test_line, font_size)
            
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(separator.join(current_line))
                    current_line = [word]
                else:
                    # Word is too long, add it anyway
                    lines.append(word)
        
        if current_line:
            lines.append(separator.join(current_line))
        
        return lines
