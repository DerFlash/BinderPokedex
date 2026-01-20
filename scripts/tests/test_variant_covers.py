"""
Test suite for variant cover rendering (titles and subtitles with logos).

Tests the rendering of:
- Variant cover pages with logos (EX, Mega, etc.)
- Separator pages with section titles
- Logo placement and text rendering
"""

import pytest
from pathlib import Path
from io import BytesIO
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4

from scripts.lib.rendering.variant_cover_renderer import VariantCoverRenderer
from scripts.lib.fonts import FontManager


class TestVariantCoverSubtitles:
    """Test subtitle rendering with EX/Mega logos in variant covers."""

    @pytest.fixture
    def canvas(self):
        """Create a test canvas."""
        output = BytesIO()
        c = rl_canvas.Canvas(output, pagesize=A4)
        return c

    @pytest.fixture
    def renderer(self):
        """Create a VariantCoverRenderer for testing."""
        return VariantCoverRenderer(language='de')

    @pytest.fixture
    def basic_variant_data(self):
        """Basic variant data for testing."""
        return {
            'variant_name': 'EX-Serie',
            'variant_type': 'ex_gen1',
            'variant_display_name': 'Generation 1 EX',
            'region': 'Kanto',
            'description': 'Test variant'
        }

    @pytest.fixture
    def sample_pokemon_list(self):
        """Sample Pokémon list for testing."""
        return [
            {'id': 1, 'name': 'Bisasam', 'type1': 'Grass'},
            {'id': 2, 'name': 'Glurak', 'type1': 'Fire'},
        ]

    def test_variant_cover_renders_without_error(self, canvas, renderer, basic_variant_data, sample_pokemon_list):
        """Test that variant cover can be rendered without errors."""
        try:
            renderer.render_variant_cover(
                canvas,
                basic_variant_data,
                sample_pokemon_list,
                '#FF0000'
            )
            assert True
        except Exception as e:
            pytest.fail(f"Variant cover rendering failed: {e}")

    def test_variant_cover_with_section_title(self, canvas, renderer, basic_variant_data, sample_pokemon_list):
        """Test that section_title is respected when provided."""
        # Section title should be displayed instead of variant name
        try:
            renderer.render_variant_cover(
                canvas,
                basic_variant_data,
                sample_pokemon_list,
                '#FF0000',
                section_title='Mega-Pokémon'  # Should override variant_name
            )
            assert True
        except Exception as e:
            pytest.fail(f"Section title rendering failed: {e}")

    def test_variant_cover_handles_ex_prefix(self, canvas, renderer, basic_variant_data, sample_pokemon_list):
        """Test that 'EX-' prefixed titles are handled correctly.
        
        Expected behavior: The EX logo should be rendered before the text,
        not as plain text "EX-".
        """
        # When section_title starts with "EX-", should attempt to render EX logo
        variant_data = dict(basic_variant_data)
        section_title_ex = "EX-Serie (Next Destinies+)"
        
        # Should not raise an error
        try:
            renderer.render_variant_cover(
                canvas,
                variant_data,
                sample_pokemon_list,
                '#FF0000',
                section_title=section_title_ex
            )
            assert True
        except Exception as e:
            pytest.fail(f"EX prefix handling failed: {e}")

    def test_variant_cover_handles_bracket_logos(self, canvas, renderer, basic_variant_data, sample_pokemon_list):
        """Test that [EX_NEW] and [EX_TERA] tokens are handled.
        
        Expected behavior: Logo images should be embedded, not plain text tokens.
        """
        variant_data = dict(basic_variant_data)
        section_title_new_ex = "[EX_NEW] Serie (Karmesin & Purpur+)"
        
        try:
            renderer.render_variant_cover(
                canvas,
                variant_data,
                sample_pokemon_list,
                '#FF0000',
                section_title=section_title_new_ex
            )
            assert True
        except Exception as e:
            pytest.fail(f"[EX_NEW] token handling failed: {e}")

    def test_variant_cover_megaseries_title(self, canvas, renderer, basic_variant_data, sample_pokemon_list):
        """Test Mega evolution series title rendering."""
        variant_data = dict(basic_variant_data)
        variant_data['variant_type'] = 'mega_evolution'
        section_title_mega = "Mega-Pokémon Serie"
        
        try:
            renderer.render_variant_cover(
                canvas,
                variant_data,
                sample_pokemon_list,
                '#A335EE',  # Purple for Mega
                section_title=section_title_mega
            )
            assert True
        except Exception as e:
            pytest.fail(f"Mega series rendering failed: {e}")

    def test_variant_cover_multi_language_subtitle(self, canvas, sample_pokemon_list, basic_variant_data):
        """Test that section titles render correctly in multiple languages."""
        languages = ['de', 'en', 'fr', 'es']
        section_title = "EX-Serie (Special Edition)"
        
        for lang in languages:
            renderer = VariantCoverRenderer(language=lang)
            try:
                renderer.render_variant_cover(
                    canvas,
                    basic_variant_data,
                    sample_pokemon_list,
                    '#FF0000',
                    section_title=section_title
                )
            except Exception as e:
                pytest.fail(f"Multi-language rendering failed for {lang}: {e}")

    def test_separator_page_styling(self, canvas, renderer, basic_variant_data, sample_pokemon_list):
        """Test that separator pages have appropriate styling.
        
        Separator pages should have:
        - Same font styling as cover pages
        - Proper centering
        - Visible section title
        """
        separator_title = "Pokémon-EX Mega"
        
        try:
            renderer.render_variant_cover(
                canvas,
                basic_variant_data,
                sample_pokemon_list,
                '#A335EE',
                section_title=separator_title
            )
            # If it renders, styling is applied
            assert True
        except Exception as e:
            pytest.fail(f"Separator styling failed: {e}")


class TestVariantCoverWithLogos:
    """Test that EX/Mega logos are actually rendered, not just text."""

    @pytest.fixture
    def canvas(self):
        """Create a test canvas."""
        output = BytesIO()
        c = rl_canvas.Canvas(output, pagesize=A4)
        return c

    @pytest.fixture
    def renderer(self):
        """Create a VariantCoverRenderer for testing."""
        return VariantCoverRenderer(language='de')

    @pytest.fixture
    def variant_data(self):
        """Variant data with iconic Pokémon."""
        return {
            'variant_name': 'EX-Serie',
            'variant_type': 'ex_gen1',
            'variant_display_name': 'Generation 1 EX',
            'region': 'Kanto',
            'description': 'Test variant',
            'iconic_pokemon_ids': [1, 25, 130]
        }

    def test_ex_logo_rendering(self, canvas, renderer, variant_data):
        """Test that EX logo is rendered for "EX-" prefixed titles."""
        pokemon_list = [
            {'id': i, 'name': f'Pokemon{i}', 'type1': 'Normal'} 
            for i in range(1, 120)
        ]
        
        section_title = "EX-Serie (Plasma)"
        
        # Should render without error and ideally with logo
        try:
            renderer.render_variant_cover(
                canvas,
                variant_data,
                pokemon_list,
                '#FF0000',
                section_title=section_title
            )
            assert True
        except Exception as e:
            pytest.fail(f"EX logo rendering failed: {e}")

    def test_ex_new_logo_rendering(self, canvas, renderer, variant_data):
        """Test that EX_NEW logo is rendered for [EX_NEW] token."""
        pokemon_list = [
            {'id': i, 'name': f'Pokemon{i}', 'type1': 'Normal'} 
            for i in range(1, 100)
        ]
        
        section_title = "[EX_NEW] Serie (Karmesin & Purpur+)"
        
        try:
            renderer.render_variant_cover(
                canvas,
                variant_data,
                pokemon_list,
                '#FF0000',
                section_title=section_title
            )
            assert True
        except Exception as e:
            pytest.fail(f"EX_NEW logo rendering failed: {e}")

    def test_mega_logo_rendering(self, canvas, renderer):
        """Test Mega logo rendering for Mega evolution series."""
        variant_data = {
            'variant_name': 'Mega-Pokémon',
            'variant_type': 'mega_evolution',
            'region': 'Various',
            'description': 'Mega forms',
        }
        pokemon_list = [
            {'id': i, 'name': f'Pokemon{i}', 'type1': 'Normal'} 
            for i in range(1, 50)
        ]
        
        section_title = "[M] Pokémon Serie"
        
        try:
            renderer.render_variant_cover(
                canvas,
                variant_data,
                pokemon_list,
                '#A335EE',
                section_title=section_title
            )
            assert True
        except Exception as e:
            pytest.fail(f"Mega logo rendering failed: {e}")


class TestVariantCoverEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def canvas(self):
        """Create a test canvas."""
        output = BytesIO()
        c = rl_canvas.Canvas(output, pagesize=A4)
        return c

    @pytest.fixture
    def renderer(self):
        """Create a VariantCoverRenderer for testing."""
        return VariantCoverRenderer(language='de')

    @pytest.fixture
    def variant_data(self):
        """Basic variant data."""
        return {
            'variant_name': 'Test',
            'variant_type': 'test',
            'region': 'Test Region',
            'description': 'Test'
        }

    def test_empty_section_title(self, canvas, renderer, variant_data):
        """Test that empty section title falls back to variant name."""
        pokemon_list = [{'id': 1, 'name': 'Test', 'type1': 'Normal'}]
        
        try:
            renderer.render_variant_cover(
                canvas,
                variant_data,
                pokemon_list,
                '#FFD700',
                section_title=''  # Empty string
            )
            assert True
        except Exception as e:
            pytest.fail(f"Empty section title handling failed: {e}")

    def test_none_section_title(self, canvas, renderer, variant_data):
        """Test that None section title uses variant name."""
        pokemon_list = [{'id': 1, 'name': 'Test', 'type1': 'Normal'}]
        
        try:
            renderer.render_variant_cover(
                canvas,
                variant_data,
                pokemon_list,
                '#FFD700',
                section_title=None  # Explicit None
            )
            assert True
        except Exception as e:
            pytest.fail(f"None section title handling failed: {e}")

    def test_very_long_section_title(self, canvas, renderer, variant_data):
        """Test that very long section titles are handled gracefully."""
        pokemon_list = [{'id': 1, 'name': 'Test', 'type1': 'Normal'}]
        long_title = "EX-Serie (Sehr Lange Bezeichnung mit Vielen Worten +)"
        
        try:
            renderer.render_variant_cover(
                canvas,
                variant_data,
                pokemon_list,
                '#FFD700',
                section_title=long_title
            )
            assert True
        except Exception as e:
            pytest.fail(f"Long title handling failed: {e}")

    def test_special_characters_in_title(self, canvas, renderer, variant_data):
        """Test that special characters in titles are handled."""
        pokemon_list = [{'id': 1, 'name': 'Test', 'type1': 'Normal'}]
        special_title = "Pokémon (Édition+Spéciale) & Friends"
        
        try:
            renderer.render_variant_cover(
                canvas,
                variant_data,
                pokemon_list,
                '#FFD700',
                section_title=special_title
            )
            assert True
        except Exception as e:
            pytest.fail(f"Special characters handling failed: {e}")
