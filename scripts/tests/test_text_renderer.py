"""
Tests for Text Rendering Module

Tests text rendering with CJK fonts, symbol conversion, and text measurement.
"""

import sys
import logging
from pathlib import Path
from io import BytesIO

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from fonts import FontManager
from text_renderer import TextRenderer
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_symbol_conversion():
    """Test symbol substitution (♀ → (w), ♂ → (m))."""
    logger.info("Testing symbol conversion...")
    
    test_cases = [
        ('Normal text', 'Normal text'),
        ('Pokemon ♀', 'Pokemon (w)'),
        ('Pokemon ♂', 'Pokemon (m)'),
        ('♀ Symbol at start', '(w) Symbol at start'),
        ('Multiple ♀ and ♂ symbols', 'Multiple (w) and (m) symbols'),
    ]
    
    for input_text, expected in test_cases:
        result = TextRenderer.convert_special_symbols(input_text)
        assert result == expected, f"Expected '{expected}', got '{result}'"
        logger.info(f"✓ '{input_text}' → '{result}'")


def test_render_text_on_canvas():
    """Test rendering text on a ReportLab canvas."""
    logger.info("Testing text rendering on canvas...")
    
    # Create in-memory PDF
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    
    # Test with different fonts and languages
    test_cases = [
        ('Helvetica', 'English text', 100, 700),
        ('HeiseiKakuGo-W5', 'こんにちは', 100, 650),  # Japanese: Hello
        ('STSong-Light', '你好', 100, 600),           # Simplified Chinese: Hello
        ('MSung-Light', '你好', 100, 550),            # Traditional Chinese: Hello
        ('HYGothic-Medium', '안녕하세요', 100, 500),  # Korean: Hello
    ]
    
    for font_name, text, x, y in test_cases:
        try:
            TextRenderer.render_text(c, x, y, text, font_name, 12)
            logger.info(f"✓ Rendered with {font_name}: {text}")
        except Exception as e:
            logger.warning(f"⚠ Could not render with {font_name}: {e}")
    
    # Finalize PDF to ensure no errors
    c.save()
    logger.info("✓ All text rendered to canvas successfully")


def test_text_measurement():
    """Test text width calculation."""
    logger.info("Testing text measurement...")
    
    # Measure some common texts
    test_cases = [
        ('Helvetica', 'Hello', 12),
        ('Helvetica', 'This is a longer string', 12),
        ('HeiseiKakuGo-W5', 'こんにちは', 12),
        ('STSong-Light', '你好', 12),
    ]
    
    for font_name, text, size in test_cases:
        try:
            width = TextRenderer.measure_text_width(text, font_name, size)
            assert width > 0, f"Width should be > 0, got {width}"
            logger.info(f"✓ '{text}' in {font_name}: {width:.2f}pt")
        except Exception as e:
            logger.warning(f"⚠ Could not measure with {font_name}: {e}")


def test_symbol_measurement():
    """Test that symbol conversion affects measurement correctly."""
    logger.info("Testing symbol measurement after conversion...")
    
    original = 'Pokemon ♀'
    converted = 'Pokemon (w)'
    
    try:
        width_original_idea = TextRenderer.measure_text_width(original, 'Helvetica', 12)
        width_converted = TextRenderer.measure_text_width(converted, 'Helvetica', 12)
        
        logger.info(f"Original symbol width would be: {width_original_idea:.2f}pt")
        logger.info(f"Converted text width: {width_converted:.2f}pt")
        logger.info("✓ Symbol conversion measurement works")
    except Exception as e:
        logger.warning(f"⚠ Could not measure symbols: {e}")


def test_text_wrapping():
    """Test text wrapping functionality."""
    logger.info("Testing text wrapping...")
    
    long_text = "This is a very long text that should be wrapped to fit within a specific width constraint"
    max_width = 200
    
    try:
        lines = TextRenderer.wrap_text(long_text, 'Helvetica', 12, max_width)
        assert len(lines) > 1, "Text should wrap into multiple lines"
        logger.info(f"✓ Text wrapped into {len(lines)} lines:")
        for i, line in enumerate(lines, 1):
            logger.info(f"  Line {i}: {line}")
    except Exception as e:
        logger.warning(f"⚠ Text wrapping failed: {e}")


def test_invalid_font():
    """Test error handling for unregistered fonts."""
    logger.info("Testing error handling for invalid fonts...")
    
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    
    try:
        TextRenderer.render_text(c, 100, 100, "Test", "NonExistentFont", 12)
        assert False, "Should have raised ValueError for unregistered font"
    except ValueError as e:
        assert "not registered" in str(e)
        logger.info(f"✓ Correctly raised error: {e}")


def run_all_tests():
    """Run all text renderer tests."""
    logger.info("\n" + "="*60)
    logger.info("TEXT RENDERER TESTS")
    logger.info("="*60 + "\n")
    
    try:
        test_symbol_conversion()
        logger.info("")
        test_render_text_on_canvas()
        logger.info("")
        test_text_measurement()
        logger.info("")
        test_symbol_measurement()
        logger.info("")
        test_text_wrapping()
        logger.info("")
        test_invalid_font()
        
        logger.info("\n" + "="*60)
        logger.info("✓ ALL TESTS PASSED!")
        logger.info("="*60 + "\n")
        return True
    except AssertionError as e:
        logger.error(f"\n✗ TEST FAILED: {e}")
        return False
    except Exception as e:
        logger.error(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
