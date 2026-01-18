"""
Tests for Font Management Module

Tests font registration, retrieval, and CID font support.
"""

import sys
import logging
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from fonts import FontManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_fonts_registered():
    """Test that fonts are registered at module load."""
    logger.info("Testing font registration...")
    
    # All supported languages should work
    languages = FontManager.get_supported_languages()
    assert len(languages) > 0, "No supported languages found"
    assert 'ja' in languages, "Japanese not in supported languages"
    assert 'zh_hans' in languages, "Simplified Chinese not in supported languages"
    assert 'de' in languages, "German not in supported languages"
    
    logger.info(f"✓ All {len(languages)} languages supported: {languages}")


def test_get_font_names():
    """Test retrieving font names for each language."""
    logger.info("Testing font name retrieval...")
    
    test_cases = [
        ('de', False, 'Helvetica'),
        ('de', True, 'Helvetica-Bold'),
        ('en', False, 'Helvetica'),
        ('ja', False, 'SongtiBold'),
        ('ko', False, 'AppleGothicRegular'),  # TrueType font for Korean (not PostScript)
        ('zh_hans', False, 'SongtiBold'),
        ('zh_hant', False, 'SongtiBold'),
    ]
    
    for language, bold, expected_font in test_cases:
        font = FontManager.get_font_name(language, bold)
        assert font == expected_font, f"For {language} (bold={bold}): expected {expected_font}, got {font}"
        logger.info(f"✓ {language}: {font}")



def test_cid_fonts():
    """Test CJK language detection."""
    logger.info("Testing CJK language detection...")
    
    # CJK languages
    cjk_languages = ['ja', 'ko', 'zh_hans', 'zh_hant']
    for lang in cjk_languages:
        is_cjk = FontManager.is_cjk_language(lang)
        assert is_cjk, f"{lang} should be CJK"
        logger.info(f"✓ {lang} is CJK")
    
    # Latin languages
    latin_languages = ['de', 'en', 'es', 'fr', 'it']
    for lang in latin_languages:
        is_cjk = FontManager.is_cjk_language(lang)
        assert not is_cjk, f"{lang} should not be CJK"
        logger.info(f"✓ {lang} is not CJK")


def test_invalid_language():
    """Test error handling for unsupported languages."""
    logger.info("Testing error handling...")
    
    try:
        FontManager.get_font_name('invalid_lang')
        assert False, "Should have raised ValueError for invalid language"
    except ValueError as e:
        assert "Unsupported language" in str(e)
        logger.info(f"✓ Correctly raised error: {e}")


def run_all_tests():
    """Run all font tests."""
    logger.info("\n" + "="*60)
    logger.info("FONT MANAGER TESTS")
    logger.info("="*60 + "\n")
    
    try:
        test_fonts_registered()
        test_get_font_names()
        test_cid_fonts()
        test_invalid_language()
        
        logger.info("\n" + "="*60)
        logger.info("✓ ALL TESTS PASSED!")
        logger.info("="*60 + "\n")
        return True
    except AssertionError as e:
        logger.error(f"\n✗ TEST FAILED: {e}")
        return False
    except Exception as e:
        logger.error(f"\n✗ UNEXPECTED ERROR: {e}")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
