"""
Rendering Module - Unified rendering components for PDF generation

This module provides centralized rendering components to eliminate code duplication
between pdf_generator.py and card_template.py.

Components:
- TranslationLoader: Centralized i18n loading with caching
- CardRenderer: Unified card rendering
- CoverRenderer: Unified cover rendering
- PageRenderer: Page layout management
"""

from .translation_loader import TranslationLoader
from .card_renderer import CardRenderer, CardStyle
from .cover_renderer import CoverRenderer, CoverStyle
from .page_renderer import PageRenderer, PageStyle

__all__ = ['TranslationLoader', 'CardRenderer', 'CardStyle', 'CoverRenderer', 'CoverStyle', 'PageRenderer', 'PageStyle']
