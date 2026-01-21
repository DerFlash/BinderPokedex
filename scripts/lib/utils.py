"""
Shared utility functions for PDF generators.

Consolidates common functionality used across pdf_generator.py and variant_pdf_generator.py.
"""

import json
import logging
from pathlib import Path
from typing import List
from reportlab.lib.colors import HexColor

logger = logging.getLogger(__name__)


class TextRenderer:
    """Unified text rendering utilities for handling special characters."""
    
    @staticmethod
    def draw_name_with_symbol_fallback(canvas_obj, name: str, x: float, width: float, 
                                       y: float, primary_font: str, font_size: float = 8,
                                       text_color: str = "#2D2D2D") -> None:
        """
        Draw text with gender symbol fallback.
        
        If name contains ♂/♀ symbols, renders text parts with primary font and 
        symbols with SongtiBold for better Unicode support.
        
        This is the canonical implementation replacing:
        - card_template._draw_name_with_symbol_fallback
        - pdf_generator._draw_name_with_symbol_fallback
        
        Args:
            canvas_obj: ReportLab canvas object
            name: Text with potential ♂/♀ symbols
            x: X position for centering
            width: Width for centering calculation
            y: Y position
            primary_font: Primary font name (e.g., 'Helvetica-Bold')
            font_size: Font size in points (default 8)
            text_color: Hex color for text (default black)
        """
        # Split name into parts and symbols
        parts: List[tuple] = []
        current_part: str = ""
        
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
                total_width += canvas_obj.stringWidth(part_text, primary_font, font_size)
            else:  # symbol
                total_width += canvas_obj.stringWidth(part_text, 'SongtiBold', font_size)
        
        # Draw centered
        start_x = x + width / 2 - total_width / 2
        current_x = start_x
        
        for part_type, part_text in parts:
            if part_type == 'text':
                canvas_obj.setFont(primary_font, font_size)
                canvas_obj.setFillColor(HexColor(text_color))
                canvas_obj.drawString(current_x, y, part_text)
                current_x += canvas_obj.stringWidth(part_text, primary_font, font_size)
            else:  # symbol
                canvas_obj.setFont('SongtiBold', font_size)
                canvas_obj.setFillColor(HexColor(text_color))
                canvas_obj.drawString(current_x, y, part_text)
                current_x += canvas_obj.stringWidth(part_text, 'SongtiBold', font_size)


class TranslationHelper:
    """Helper class for managing translations across PDF generators."""
    
    @staticmethod
    def load_translations(language: str) -> dict:
        """
        Load translations from i18n/translations.json
        
        Args:
            language: Language code (de, en, fr, etc.)
        
        Returns:
            Dictionary with translations for current language
        """
        try:
            trans_file = Path(__file__).parent.parent.parent / 'i18n' / 'translations.json'
            with open(trans_file, 'r', encoding='utf-8') as f:
                all_trans = json.load(f)
            
            # Return UI translations for the current language, or empty dict if not found
            ui_trans = all_trans.get('ui', {})
            return ui_trans.get(language, {})
        except Exception as e:
            logger.warning(f"Could not load translations: {e}")
            return {}
    
    @staticmethod
    def format_translation(translations: dict, key: str, **kwargs) -> str:
        """
        Get a translated string and format it with provided variables.
        
        Args:
            translations: Dictionary with translations for current language
            key: Translation key (e.g., 'variant_species')
            **kwargs: Variables to format into the string
        
        Returns:
            Formatted translation or key if not found
        """
        text = translations.get(key, key)
        
        # Simple template replacement
        for var_name, var_value in kwargs.items():
            text = text.replace(f'{{{{{var_name}}}}}', str(var_value))
        
        return text
