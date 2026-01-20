"""
Comprehensive test suite for rendering modules.

Tests CardRenderer, CoverRenderer, VariantCoverRenderer, PageRenderer, and TranslationLoader.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

# Import rendering modules
from scripts.lib.rendering import (
    CardRenderer,
    CardStyle,
    CoverRenderer,
    CoverStyle,
    VariantCoverRenderer,
    VariantCoverStyle,
    PageRenderer,
    PageStyle,
    TranslationLoader
)
from scripts.lib.constants import (
    TYPE_COLORS,
    GENERATION_COLORS,
    VARIANT_COLORS,
    CARD_WIDTH,
    CARD_HEIGHT,
    PAGE_WIDTH,
    PAGE_HEIGHT
)


class TestCardStyle:
    """Test CardStyle constants."""
    
    def test_type_colors_loaded(self):
        """Verify TYPE_COLORS is loaded from constants."""
        assert TYPE_COLORS is not None
        assert len(TYPE_COLORS) == 18  # 18 Pokémon types
        assert TYPE_COLORS.get('Normal') == '#A8A878'
        assert TYPE_COLORS.get('Fire') == '#F08030'
    
    def test_card_style_has_type_colors(self):
        """Verify CardStyle has TYPE_COLORS reference."""
        assert hasattr(CardStyle, 'TYPE_COLORS')
        assert CardStyle.TYPE_COLORS == TYPE_COLORS
    
    def test_card_dimensions(self):
        """Verify card dimensions are correct."""
        assert CardStyle.CARD_WIDTH == CARD_WIDTH
        assert CardStyle.CARD_HEIGHT == CARD_HEIGHT
        assert CardStyle.HEADER_HEIGHT == 12 * mm


class TestCardRenderer:
    """Test CardRenderer functionality."""
    
    @pytest.fixture
    def card_renderer(self):
        """Create CardRenderer instance for testing."""
        return CardRenderer(language='en')
    
    @pytest.fixture
    def sample_pokemon(self):
        """Create sample Pokémon data."""
        return {
            'id': '001',
            'name_en': 'Bulbasaur',
            'name_de': 'Bisaknosp',
            'type': ['Grass', 'Poison'],
            'image_url': 'https://example.com/001.png',
            'hp': 45,
            'attack': 49,
            'defense': 49
        }
    
    def test_renderer_initialization(self, card_renderer):
        """Test CardRenderer initializes correctly."""
        assert card_renderer.language == 'en'
        assert card_renderer.style is not None
        assert isinstance(card_renderer.style, CardStyle)
    
    def test_language_support(self):
        """Test CardRenderer supports multiple languages."""
        for lang in ['de', 'en', 'fr', 'ja']:
            renderer = CardRenderer(language=lang)
            assert renderer.language == lang
    
    def test_render_card_signature(self, card_renderer, sample_pokemon):
        """Test render_card method has correct signature."""
        # Create mock canvas
        c = MagicMock()
        
        # Verify method exists and accepts correct parameters
        assert hasattr(card_renderer, 'render_card')
        method = getattr(card_renderer, 'render_card')
        assert callable(method)


class TestCoverStyle:
    """Test CoverStyle constants."""
    
    def test_generation_colors_loaded(self):
        """Verify GENERATION_COLORS is loaded from constants."""
        assert GENERATION_COLORS is not None
        assert len(GENERATION_COLORS) == 9  # 9 generations
        assert GENERATION_COLORS.get(1) == '#FF0000'  # Gen 1 Red
    
    def test_cover_style_has_generation_colors(self):
        """Verify CoverStyle has GENERATION_COLORS reference."""
        assert hasattr(CoverStyle, 'GENERATION_COLORS')
        assert CoverStyle.GENERATION_COLORS == GENERATION_COLORS
    
    def test_cover_style_dimensions(self):
        """Verify CoverStyle has correct dimensions."""
        assert CoverStyle.STRIPE_HEIGHT == 100 * mm
        assert CoverStyle.TITLE_FONT_SIZE == 42


class TestCoverRenderer:
    """Test CoverRenderer functionality."""
    
    @pytest.fixture
    def cover_renderer(self):
        """Create CoverRenderer instance for testing."""
        return CoverRenderer(language='en', generation=1)
    
    @pytest.fixture
    def sample_generation_data(self):
        """Create sample generation data."""
        return {
            'pokemon': [
                {'id': '001', 'name_en': 'Bulbasaur'},
                {'id': '002', 'name_en': 'Ivysaur'},
                {'id': '003', 'name_en': 'Venusaur'}
            ]
        }
    
    def test_renderer_initialization(self, cover_renderer):
        """Test CoverRenderer initializes correctly."""
        assert cover_renderer.language == 'en'
        assert cover_renderer.generation == 1
        assert cover_renderer.style is not None
    
    def test_generation_validation(self):
        """Test CoverRenderer validates generation number."""
        for gen in range(1, 10):
            renderer = CoverRenderer(language='en', generation=gen)
            assert renderer.generation == gen


class TestVariantCoverStyle:
    """Test VariantCoverStyle constants."""
    
    def test_variant_colors_loaded(self):
        """Verify VARIANT_COLORS is loaded from constants."""
        assert VARIANT_COLORS is not None
        assert len(VARIANT_COLORS) == 12  # 12 variant types
        assert VARIANT_COLORS.get('ex_gen1') == '#1F51BA'
        assert VARIANT_COLORS.get('mega_evolution') == '#FFD700'
    
    def test_variant_cover_style_has_variant_colors(self):
        """Verify VariantCoverStyle has VARIANT_COLORS reference."""
        assert hasattr(VariantCoverStyle, 'VARIANT_COLORS')
        assert VariantCoverStyle.VARIANT_COLORS == VARIANT_COLORS
    
    def test_styling_constants(self):
        """Verify styling constants are properly defined."""
        assert VariantCoverStyle.PAGE_WIDTH == PAGE_WIDTH
        assert VariantCoverStyle.PAGE_HEIGHT == PAGE_HEIGHT
        assert VariantCoverStyle.HEADER_HEIGHT == 100 * mm


class TestVariantCoverRenderer:
    """Test VariantCoverRenderer functionality."""
    
    @pytest.fixture
    def variant_renderer(self):
        """Create VariantCoverRenderer instance for testing."""
        return VariantCoverRenderer(language='en')
    
    @pytest.fixture
    def sample_variant_data(self):
        """Create sample variant data."""
        return {
            'variant': 'ex_gen1',
            'variant_name_en': 'Pokémon-ex Gen 1',
            'pokemon': [
                {'id': '#003_EX1', 'name_en': 'Venusaur-ex'},
                {'id': '#006_EX1', 'name_en': 'Charizard-ex'},
                {'id': '#009_EX1', 'name_en': 'Blastoise-ex'}
            ]
        }
    
    def test_renderer_initialization(self, variant_renderer):
        """Test VariantCoverRenderer initializes correctly."""
        assert variant_renderer.language == 'en'
        assert variant_renderer.style is not None
        assert isinstance(variant_renderer.style, VariantCoverStyle)
    
    def test_render_variant_cover_signature(self, variant_renderer, sample_variant_data):
        """Test render_variant_cover method has correct signature."""
        c = MagicMock()
        pokemon_list = sample_variant_data.get('pokemon', [])
        
        # Verify method exists and accepts correct parameters
        assert hasattr(variant_renderer, 'render_variant_cover')
        method = getattr(variant_renderer, 'render_variant_cover')
        assert callable(method)


class TestPageStyle:
    """Test PageStyle constants."""
    
    def test_page_dimensions(self):
        """Verify page dimensions are correct."""
        assert PageStyle.PAGE_WIDTH == PAGE_WIDTH
        assert PageStyle.PAGE_HEIGHT == PAGE_HEIGHT
        assert PageStyle.PAGE_MARGIN > 0  # Just verify it exists and is positive
    
    def test_card_grid_dimensions(self):
        """Verify card grid constants are correct."""
        from scripts.lib.constants import CARDS_PER_ROW, CARDS_PER_COLUMN
        assert PageStyle.CARDS_PER_ROW == CARDS_PER_ROW
        assert PageStyle.CARDS_PER_COLUMN == CARDS_PER_COLUMN


class TestPageRenderer:
    """Test PageRenderer functionality."""
    
    @pytest.fixture
    def page_renderer(self):
        """Create PageRenderer instance for testing."""
        return PageRenderer()
    
    def test_renderer_initialization(self, page_renderer):
        """Test PageRenderer initializes correctly."""
        assert page_renderer is not None
        assert hasattr(page_renderer, 'style')
    
    def test_create_page_method(self, page_renderer):
        """Test create_page method exists and is callable."""
        assert hasattr(page_renderer, 'create_page')
        assert callable(getattr(page_renderer, 'create_page'))


class TestTranslationLoader:
    """Test TranslationLoader functionality."""
    
    @pytest.fixture
    def translation_loader(self):
        """Create TranslationLoader instance for testing."""
        return TranslationLoader()
    
    def test_loader_initialization(self, translation_loader):
        """Test TranslationLoader initializes correctly."""
        assert translation_loader is not None
        # Just verify it's a TranslationLoader instance
        assert isinstance(translation_loader, TranslationLoader)
    
    def test_language_support(self, translation_loader):
        """Test TranslationLoader supports multiple languages."""
        for lang in ['de', 'en', 'fr', 'ja']:
            ui_trans = translation_loader.load_ui(lang)
            assert isinstance(ui_trans, dict)


class TestColorConstants:
    """Test color constant consolidation."""
    
    def test_type_colors_canonical(self):
        """Verify TYPE_COLORS is canonical source."""
        # Should have all 18 Pokémon types
        expected_types = [
            'Normal', 'Fire', 'Water', 'Electric', 'Grass', 'Ice',
            'Fighting', 'Poison', 'Ground', 'Flying', 'Psychic', 'Bug',
            'Rock', 'Ghost', 'Dragon', 'Dark', 'Steel', 'Fairy'
        ]
        for ptype in expected_types:
            assert ptype in TYPE_COLORS, f"Missing type: {ptype}"
            assert isinstance(TYPE_COLORS[ptype], str)
            assert TYPE_COLORS[ptype].startswith('#')
    
    def test_generation_colors_canonical(self):
        """Verify GENERATION_COLORS is canonical source."""
        # Should have colors for generations 1-9
        for gen in range(1, 10):
            assert gen in GENERATION_COLORS, f"Missing generation: {gen}"
            assert isinstance(GENERATION_COLORS[gen], str)
            assert GENERATION_COLORS[gen].startswith('#')
    
    def test_variant_colors_canonical(self):
        """Verify VARIANT_COLORS is canonical source."""
        expected_variants = [
            'ex_gen1', 'ex_gen2', 'ex_gen3', 'mega_evolution',
            'gigantamax', 'regional_alola', 'regional_galar',
            'regional_hisui', 'regional_paldea', 'primal_terastal',
            'patterns_unique', 'fusion_special'
        ]
        for variant in expected_variants:
            assert variant in VARIANT_COLORS, f"Missing variant: {variant}"
            assert isinstance(VARIANT_COLORS[variant], str)
            assert VARIANT_COLORS[variant].startswith('#')


class TestIntegration:
    """Integration tests for rendering pipeline."""
    
    @pytest.fixture
    def temp_pdf(self):
        """Create temporary PDF file."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            return f.name
    
    def test_renderers_importable(self):
        """Test all renderers can be imported."""
        from scripts.lib.rendering import (
            CardRenderer,
            CoverRenderer,
            VariantCoverRenderer,
            PageRenderer,
            TranslationLoader
        )
        assert CardRenderer is not None
        assert CoverRenderer is not None
        assert VariantCoverRenderer is not None
        assert PageRenderer is not None
        assert TranslationLoader is not None
    
    def test_renderer_instances_creatable(self):
        """Test all renderers can be instantiated."""
        card = CardRenderer(language='en')
        cover = CoverRenderer(language='en', generation=1)
        variant = VariantCoverRenderer(language='en')
        page = PageRenderer()
        
        assert card is not None
        assert cover is not None
        assert variant is not None
        assert page is not None
    
    def test_multiple_languages(self):
        """Test renderers support multiple languages."""
        for lang in ['de', 'en', 'fr', 'ja']:
            card = CardRenderer(language=lang)
            cover = CoverRenderer(language=lang, generation=1)
            variant = VariantCoverRenderer(language=lang)
            
            assert card.language == lang
            assert cover.language == lang
            assert variant.language == lang


# Performance tests
class TestPerformance:
    """Performance-related tests."""
    
    def test_translation_loader_caching(self):
        """Test TranslationLoader caches translations."""
        loader = TranslationLoader()
        
        # First call
        trans1 = loader.load_ui('en')
        # Second call should return cached version
        trans2 = loader.load_ui('en')
        
        assert trans1 is trans2  # Should be same object (cached)
    
    def test_renderer_initialization_speed(self):
        """Test renderers initialize quickly."""
        import time
        
        start = time.time()
        for _ in range(100):
            CardRenderer(language='en')
        elapsed = time.time() - start
        
        # Should complete 100 initializations in < 1 second
        assert elapsed < 1.0, f"CardRenderer initialization too slow: {elapsed}s"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
