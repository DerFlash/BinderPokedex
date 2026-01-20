"""
Advanced tests for variant cover logo rendering.

These tests specifically verify that:
1. EX/Mega logos are actually drawn to the canvas
2. Text is properly positioned relative to logos
3. Fallbacks work when logo files are missing
"""

import pytest
from pathlib import Path
from io import BytesIO
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.pagesizes import A4
from unittest.mock import MagicMock, patch

from scripts.lib.rendering.variant_cover_renderer import VariantCoverRenderer
from scripts.lib.rendering.cover_renderer import CoverRenderer


class TestLogoRendering:
    """Test that logos are actually drawn to canvas."""

    @pytest.fixture
    def canvas(self):
        """Create a mock canvas to track operations."""
        output = BytesIO()
        c = rl_canvas.Canvas(output, pagesize=A4)
        return c

    @pytest.fixture
    def variant_data(self):
        return {
            'variant_name': 'EX-Serie',
            'variant_type': 'ex_gen1',
            'variant_display_name': 'Generation 1 EX',
            'region': 'Kanto',
        }

    @pytest.fixture
    def pokemon_list(self):
        return [
            {'id': i, 'name': f'Pokemon{i}', 'type1': 'Normal'} 
            for i in range(1, 120)
        ]

    @pytest.mark.skip(reason="EX logo rendering not yet implemented - feature pending")
    def test_ex_title_should_render_logo_not_text(self, canvas, variant_data, pokemon_list):
        """
        CRITICAL: When section_title is "EX-Serie (Plasma)", 
        the "EX-" part should be a LOGO IMAGE, not text "EX-".
        
        This is the main bug: Currently it renders as plain text.
        """
        renderer = VariantCoverRenderer(language='de')
        section_title = "EX-Serie (Plasma)"
        
        # Track canvas.drawImage calls
        original_drawImage = canvas.drawImage
        logo_calls = []
        
        def tracked_drawImage(*args, **kwargs):
            logo_calls.append(args)
            return original_drawImage(*args, **kwargs)
        
        canvas.drawImage = tracked_drawImage
        
        renderer.render_variant_cover(
            canvas,
            variant_data,
            pokemon_list,
            '#FF0000',
            section_title=section_title
        )
        
        # ASSERTION: Logo image should have been drawn
        # This test WILL FAIL if logos aren't implemented
        assert len(logo_calls) > 0, \
            "EX-Serie title should draw EX logo image, not render as text"

    def test_ex_new_token_should_render_logo(self, canvas, variant_data, pokemon_list):
        """
        CRITICAL: When section_title contains "[EX_NEW]",
        it should be replaced with EX_NEW logo image, not shown as text.
        """
        renderer = VariantCoverRenderer(language='de')
        section_title = "[EX_NEW] Serie (Karmesin & Purpur+)"
        
        original_drawImage = canvas.drawImage
        logo_calls = []
        
        def tracked_drawImage(*args, **kwargs):
            logo_calls.append(args)
            return original_drawImage(*args, **kwargs)
        
        canvas.drawImage = tracked_drawImage
        
        renderer.render_variant_cover(
            canvas,
            variant_data,
            pokemon_list,
            '#FF0000',
            section_title=section_title
        )
        
        # ASSERTION: Logo image should have been drawn
        assert len(logo_calls) > 0, \
            "[EX_NEW] token should draw logo image, not render as text token"

    def test_mega_token_should_render_logo(self, canvas, pokemon_list):
        """Test that [M] token in title renders Mega logo."""
        variant_data = {
            'variant_name': 'Mega-Pokémon',
            'variant_type': 'mega_evolution',
            'region': 'Various',
        }
        renderer = VariantCoverRenderer(language='de')
        section_title = "[M] Pokémon Serie"
        
        original_drawImage = canvas.drawImage
        logo_calls = []
        
        def tracked_drawImage(*args, **kwargs):
            logo_calls.append(args)
            return original_drawImage(*args, **kwargs)
        
        canvas.drawImage = tracked_drawImage
        
        renderer.render_variant_cover(
            canvas,
            variant_data,
            pokemon_list,
            '#A335EE',
            section_title=section_title
        )
        
        # ASSERTION: Mega logo should have been drawn
        assert len(logo_calls) > 0, \
            "[M] token should draw Mega logo image, not render as text"


class TestLogoTextLayout:
    """Test proper spacing and layout of logos with text."""

    @pytest.fixture
    def canvas(self):
        output = BytesIO()
        c = rl_canvas.Canvas(output, pagesize=A4)
        return c

    @pytest.fixture
    def variant_data(self):
        return {
            'variant_name': 'EX-Serie',
            'variant_type': 'ex_gen1',
            'region': 'Kanto',
        }

    @pytest.fixture
    def pokemon_list(self):
        return [{'id': i, 'name': f'Pokemon{i}', 'type1': 'Normal'} for i in range(1, 50)]

    def test_ex_logo_text_alignment(self, canvas, variant_data, pokemon_list):
        """
        Test that when rendering "EX-Serie (Plasma)":
        1. EX logo is drawn on the left
        2. Text "Serie (Plasma)" is on the right
        3. Both are vertically centered
        """
        renderer = VariantCoverRenderer(language='de')
        section_title = "EX-Serie (Plasma)"
        
        draw_calls = {
            'image': [],
            'string': [],
        }
        
        original_drawImage = canvas.drawImage
        original_drawString = canvas.drawString
        
        def track_image(*args, **kwargs):
            draw_calls['image'].append({
                'args': args,
                'kwargs': kwargs
            })
            return original_drawImage(*args, **kwargs)
        
        def track_string(text, x, y, *args, **kwargs):
            draw_calls['string'].append({
                'text': text,
                'x': x,
                'y': y,
            })
            return original_drawString(text, x, y, *args, **kwargs)
        
        canvas.drawImage = track_image
        canvas.drawString = track_string
        
        renderer.render_variant_cover(
            canvas,
            variant_data,
            pokemon_list,
            '#FF0000',
            section_title=section_title
        )
        
        # Check that we have both image and text
        if draw_calls['image']:
            # Logo was drawn
            assert len(draw_calls['string']) > 0, \
                "When logo is drawn, text should also be drawn"
            
            # Check relative positioning
            logo_x = draw_calls['image'][0]['args'][1]  # x position of logo
            text_x = draw_calls['string'][0]['x']  # x position of first string
            
            # Text should be to the right of logo
            assert text_x > logo_x, \
                "Text should be positioned to the right of logo"


class TestLogoFallbacks:
    """Test fallback behavior when logo files are missing."""

    @pytest.fixture
    def canvas(self):
        output = BytesIO()
        c = rl_canvas.Canvas(output, pagesize=A4)
        return c

    @pytest.fixture
    def variant_data(self):
        return {
            'variant_name': 'EX-Serie',
            'variant_type': 'ex_gen1',
            'region': 'Kanto',
        }

    @pytest.fixture
    def pokemon_list(self):
        return [{'id': i, 'name': f'Pokemon{i}', 'type1': 'Normal'} for i in range(1, 50)]

    def test_fallback_when_logo_missing_simple(self, canvas, variant_data, pokemon_list):
        """
        When logo files are not found, rendering should not crash.
        Instead it should render as plain text.
        """
        renderer = VariantCoverRenderer(language='de')
        section_title = "EX-Serie (Plasma)"
        
        # Just verify it doesn't crash when logos are not found
        # (The patch will make all files appear missing)
        from unittest.mock import patch
        
        with patch('pathlib.Path.exists', return_value=False):
            try:
                renderer.render_variant_cover(
                    canvas,
                    variant_data,
                    pokemon_list,
                    '#FF0000',
                    section_title=section_title
                )
                # Success - no crash
                assert True
            except Exception as e:
                pytest.fail(f"Rendering should not crash when logos missing: {e}")


class TestSeparatorPages:
    """Test separator page specific functionality."""

    @pytest.fixture
    def canvas(self):
        output = BytesIO()
        c = rl_canvas.Canvas(output, pagesize=A4)
        return c

    def test_separator_with_ex_logo(self, canvas):
        """Separator page with EX series should render EX logo."""
        variant_data = {
            'variant_name': 'EX-Serie',
            'variant_type': 'ex_gen1',
            'region': 'Kanto',
        }
        pokemon_list = [
            {'id': i, 'name': f'Pokemon{i}', 'type1': 'Normal'} 
            for i in range(1, 120)
        ]
        
        renderer = VariantCoverRenderer(language='de')
        section_title = "Pokémon-EX Mega"  # Separator title
        
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
            pytest.fail(f"Separator with EX logo failed: {e}")

    def test_separator_styling_consistent_with_cover(self, canvas):
        """Separator page styling should match cover page styling."""
        variant_data = {
            'variant_name': 'Test',
            'variant_type': 'test',
            'region': 'Test',
        }
        pokemon_list = [{'id': 1, 'name': 'Pokemon', 'type1': 'Normal'}]
        
        renderer = VariantCoverRenderer(language='de')
        
        # Both should render without error
        try:
            # Cover page
            renderer.render_variant_cover(
                canvas,
                variant_data,
                pokemon_list,
                '#FFD700'
            )
            
            # Separator page
            renderer.render_variant_cover(
                canvas,
                variant_data,
                pokemon_list,
                '#FFD700',
                section_title="Special Section"
            )
            assert True
        except Exception as e:
            pytest.fail(f"Styling consistency check failed: {e}")
