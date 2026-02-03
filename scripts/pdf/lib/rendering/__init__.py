"""
Rendering Module - Unified rendering components for PDF generation

This module provides centralized rendering components to eliminate code duplication.

Components:
- TranslationLoader: Centralized i18n loading with caching
- CardRenderer: Unified card rendering
- CoverRenderer: Single canonical cover renderer for Pokédex and Variants
- TitleRenderer: Canonical title/subtitle rendering with multiple modes
- FooterRenderer: Canonical footer rendering
- PageRenderer: Page layout management
"""

from .translation_loader import TranslationLoader
from .card_renderer import CardRenderer, CardStyle
from .cover_renderer import CoverRenderer, CoverStyle
from .title_renderer import TitleRenderer
from .footer_renderer import FooterRenderer
from .page_renderer import PageRenderer, PageStyle

__all__ = ['TranslationLoader', 'CardRenderer', 'CardStyle', 'CoverRenderer', 'CoverStyle',
           'TitleRenderer', 'FooterRenderer', 'PageRenderer', 'PageStyle']
