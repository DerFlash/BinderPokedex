"""
Comprehensive test suite for rendering modules.

Tests CardRenderer, CoverRenderer, PageRenderer, and TranslationLoader.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from reportlab.lib.units import mm

# Import rendering modules
from scripts.pdf.lib.rendering import (
    CardRenderer,
    CardStyle,
    CoverRenderer,
    CoverStyle,
    PageRenderer,
    PageStyle,
    TranslationLoader
)
from scripts.pdf.lib.constants import (
    TYPE_COLORS,
    GENERATION_COLORS,
    VARIANT_COLORS,
    CARD_WIDTH,
    CARD_HEIGHT,
    PAGE_WIDTH,
    PAGE_HEIGHT,
    CARDS_PER_ROW,
    CARDS_PER_COLUMN
)


class TestCardStyle:
    """Test CardStyle constants."""
    
    def test_type_colors_loaded(self):
        """Verify TYPE_COLORS is loaded from constants."""
        assert TYPE_COLORS is not None
        assert len(TYPE_COLORS) == 18
        assert TYPE_COLORS.get('Normal') == '#A8A878'
    
    def test_card_dimensions(self):
        """Verify card dimensions are correct."""
        assert CardStyle.CARD_WIDTH == CARD_WIDTH
        assert CardStyle.CARD_HEIGHT == CARD_HEIGHT


class TestCardRenderer:
    """Test CardRenderer functionality."""
    
    def test_renderer_initialization(self):
        """Test CardRenderer initializes correctly."""
        renderer = CardRenderer(language='en')
        assert renderer.language == 'en'
        assert renderer.style is not None
    
    def test_language_support(self):
        """Test CardRenderer supports multiple languages."""
        for lang in ['de', 'en', 'fr', 'ja']:
            renderer = CardRenderer(language=lang)
            assert renderer.language == lang


class TestCoverStyle:
    """Test CoverStyle constants."""
    
    def test_generation_colors_loaded(self):
        """Verify GENERATION_COLORS is loaded from constants."""
        assert GENERATION_COLORS is not None
        assert len(GENERATION_COLORS) == 9
    
    def test_cover_style_dimensions(self):
        """Verify CoverStyle has correct dimensions."""
        assert CoverStyle.STRIPE_HEIGHT == 100 * mm
        assert CoverStyle.TITLE_FONT_SIZE == 42


class TestCoverRenderer:
    """Test CoverRenderer functionality."""
    
    def test_renderer_initialization(self):
        """Test CoverRenderer initializes correctly."""
        renderer = CoverRenderer(language='en')
        assert renderer.language == 'en'
        assert renderer.style is not None
        assert isinstance(renderer.style, CoverStyle)


class TestPageStyle:
    """Test PageStyle constants."""
    
    def test_page_dimensions(self):
        """Verify page dimensions are correct."""
        assert PageStyle.PAGE_WIDTH == PAGE_WIDTH
        assert PageStyle.PAGE_HEIGHT == PAGE_HEIGHT
    
    def test_card_grid_dimensions(self):
        """Verify card grid constants are correct."""
        assert PageStyle.CARDS_PER_ROW == CARDS_PER_ROW
        assert PageStyle.CARDS_PER_COLUMN == CARDS_PER_COLUMN


class TestPageRenderer:
    """Test PageRenderer functionality."""
    
    def test_renderer_initialization(self):
        """Test PageRenderer initializes correctly."""
        renderer = PageRenderer()
        assert renderer is not None
        assert hasattr(renderer, 'style')


class TestTranslationLoader:
    """Test TranslationLoader functionality."""
    
    def test_loader_initialization(self):
        """Test TranslationLoader initializes correctly."""
        loader = TranslationLoader()
        assert loader is not None
    
    def test_language_support(self):
        """Test TranslationLoader supports multiple languages."""
        loader = TranslationLoader()
        for lang in ['de', 'en', 'fr', 'ja']:
            ui_trans = loader.load_ui(lang)
            assert isinstance(ui_trans, dict)


class TestIntegration:
    """Integration tests for rendering pipeline."""
    
    def test_renderers_importable(self):
        """Test all renderers can be imported."""
        from scripts.pdf.lib.rendering import (
            CardRenderer,
            CoverRenderer,
            PageRenderer,
            TranslationLoader
        )
        assert CardRenderer is not None
        assert CoverRenderer is not None
        assert PageRenderer is not None
        assert TranslationLoader is not None
    
    def test_renderer_instances_creatable(self):
        """Test all renderers can be instantiated."""
        card = CardRenderer(language='en')
        cover = CoverRenderer(language='en')
        page = PageRenderer()
        
        assert card is not None
        assert cover is not None
        assert page is not None
    
    def test_multiple_languages(self):
        """Test renderers support multiple languages."""
        for lang in ['de', 'en', 'fr', 'ja']:
            card = CardRenderer(language=lang)
            cover = CoverRenderer(language=lang)
            
            assert card.language == lang
            assert cover.language == lang


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
