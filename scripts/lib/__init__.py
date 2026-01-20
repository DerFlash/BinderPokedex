"""
Binder Pokédex Library - Clean Architecture

Core Modules:
- fonts: Font management for multi-language support (including CJK)
- text_renderer: Unicode-aware text rendering
- pdf_generator: Complete PDF generation orchestration
- constants: Centralized configuration and constants

Usage:
    from lib.fonts import FontManager
    from lib.pdf_generator import PDFGenerator
    
    FontManager.register_fonts()
    generator = PDFGenerator('ja', 1)
    pdf_path = generator.generate(pokemon_list)
"""

from .fonts import FontManager
from .text_renderer import TextRenderer
from .pdf_generator import PDFGenerator
from .constants import (
    LANGUAGES,
    CARD_WIDTH,
    CARD_HEIGHT,
    GAP_X,
    GAP_Y,
    PAGE_MARGIN,
    CARDS_PER_ROW,
    CARDS_PER_COLUMN,
    PAGE_WIDTH,
    PAGE_HEIGHT,
    COLORS,
)

__all__ = [
    # Font Management
    'FontManager',
    
    # Text Rendering
    'TextRenderer',
    
    # PDF Generation
    'PDFGenerator',
    
    # Constants & Configuration
    'LANGUAGES',
    'CARD_WIDTH',
    'CARD_HEIGHT',
    'GAP_X',
    'GAP_Y',
    'PAGE_MARGIN',
    'CARDS_PER_ROW',
    'CARDS_PER_COLUMN',
    'PAGE_WIDTH',
    'PAGE_HEIGHT',
    'COLORS',
]

__version__ = '2.0.0'
__author__ = 'BinderPokedex Team'
__description__ = 'Multi-language Pokémon Binder PDF Generation with CJK Support'


