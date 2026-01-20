"""
Tests for Constants Module

Validates configuration data structure and completeness.
"""

import sys
import logging
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from constants import LANGUAGES, PAGE_WIDTH, PAGE_HEIGHT, CARD_WIDTH, CARD_HEIGHT, GENERATION_COLORS

# Import TYPE_COLORS from pdf_generator (where it's defined for PDF color scheme)
from pdf_generator import TYPE_COLORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_languages_structure():
    """Test that all languages have required fields."""
    logger.info("Testing language structure...")
    
    required_fields = {'code', 'name', 'name_english', 'font_group'}
    
    for lang_code, lang_data in LANGUAGES.items():
        assert isinstance(lang_data, dict), f"{lang_code}: language data must be dict"
        
        missing = required_fields - set(lang_data.keys())
        assert not missing, f"{lang_code}: missing fields {missing}"
        
        # Code should match key
        assert lang_data['code'] == lang_code, f"{lang_code}: code mismatch"
        
        # Font group should be valid
        assert lang_data['font_group'] in ['latin', 'cjk'], f"{lang_code}: invalid font_group"
        
        logger.info(f"✓ {lang_code}: {lang_data['name']}")


def test_languages_count():
    """Test that all 9 languages are defined."""
    logger.info("Testing language count...")
    
    expected_languages = {'de', 'en', 'es', 'fr', 'it', 'ja', 'ko', 'zh_hans', 'zh_hant'}
    actual_languages = set(LANGUAGES.keys())
    
    assert actual_languages == expected_languages, f"Language set mismatch: {actual_languages ^ expected_languages}"
    assert len(LANGUAGES) == 9, f"Expected 9 languages, got {len(LANGUAGES)}"
    
    logger.info(f"✓ All 9 languages present")


def test_cjk_vs_latin():
    """Test proper CJK/Latin classification."""
    logger.info("Testing CJK vs Latin classification...")
    
    cjk_langs = {'ja', 'ko', 'zh_hans', 'zh_hant'}
    latin_langs = {'de', 'en', 'es', 'fr', 'it'}
    
    for lang_code in cjk_langs:
        font_group = LANGUAGES[lang_code]['font_group']
        assert font_group == 'cjk', f"{lang_code}: should be CJK"
        logger.info(f"✓ {lang_code}: CJK")
    
    for lang_code in latin_langs:
        font_group = LANGUAGES[lang_code]['font_group']
        assert font_group == 'latin', f"{lang_code}: should be latin"
        logger.info(f"✓ {lang_code}: Latin")


def test_generations_structure():
    """Test that all generations have required fields."""
    logger.info("Testing generation structure...")
    
    from data_storage import DataStorage
    storage = DataStorage()
    
    required_fields = {'name', 'count', 'range', 'region', 'iconic_pokemon'}
    
    for gen_num in range(1, 10):
        gen_data = storage.load_generation_info(gen_num)
        assert isinstance(gen_data, dict), f"Gen {gen_num}: data must be dict"
        
        if not gen_data:
            logger.warning(f"⚠ Gen {gen_num}: no data found")
            continue
        
        missing = required_fields - set(gen_data.keys())
        assert not missing, f"Gen {gen_num}: missing fields {missing}"
        
        # Range should be valid
        range_start, range_end = gen_data['range']
        assert range_start < range_end, f"Gen {gen_num}: invalid range"
        assert gen_data['count'] == range_end - range_start + 1, f"Gen {gen_num}: count mismatch"
        
        # Iconic pokemon should be list
        assert isinstance(gen_data['iconic_pokemon'], list), f"Gen {gen_num}: iconic_pokemon must be list"
        assert len(gen_data['iconic_pokemon']) > 0, f"Gen {gen_num}: must have iconic pokemon"
        
        logger.info(f"✓ Gen {gen_num}: {gen_data['name']}")


def test_generations_count():
    """Test that generations 1-9 are defined."""
    logger.info("Testing generation count...")
    
    from data_storage import DataStorage
    storage = DataStorage()
    
    for gen_num in range(1, 10):
        pokemon = storage.load_generation(gen_num)
        assert isinstance(pokemon, list), f"Gen {gen_num}: pokemon must be list"
        assert len(pokemon) > 0, f"Gen {gen_num}: must have pokemon"
        logger.info(f"✓ Gen {gen_num}: {len(pokemon)} pokemon")
    
    logger.info(f"✓ All 9 generations present (1-9)")


def test_type_colors():
    """Test that all types have valid color codes."""
    logger.info("Testing type colors...")
    
    expected_types = {
        'Normal', 'Fire', 'Water', 'Electric', 'Grass', 'Ice',
        'Fighting', 'Poison', 'Ground', 'Flying', 'Psychic', 'Bug',
        'Rock', 'Ghost', 'Dragon', 'Dark', 'Steel', 'Fairy'
    }
    
    actual_types = set(TYPE_COLORS.keys())
    assert actual_types == expected_types, f"Type set mismatch"
    
    for type_name, color_code in TYPE_COLORS.items():
        # Check hex color format
        assert color_code.startswith('#'), f"{type_name}: color must start with #"
        assert len(color_code) == 7, f"{type_name}: color must be #RRGGBB format"
        
        # Validate hex digits
        try:
            int(color_code[1:], 16)
            logger.info(f"✓ {type_name}: {color_code}")
        except ValueError:
            assert False, f"{type_name}: invalid hex color {color_code}"


def test_page_dimensions():
    """Test that page dimensions are sensible."""
    logger.info("Testing page dimensions...")
    
    # Should be A4 (210mm x 297mm)
    assert PAGE_WIDTH > 200, "Page width too small"
    assert PAGE_HEIGHT > 290, "Page height too small"
    
    assert CARD_WIDTH < PAGE_WIDTH, "Card width > page width"
    assert CARD_HEIGHT < PAGE_HEIGHT, "Card height > page height"
    
    logger.info(f"✓ Page: {PAGE_WIDTH}x{PAGE_HEIGHT}")
    logger.info(f"✓ Card: {CARD_WIDTH}x{CARD_HEIGHT}")


def run_all_tests():
    """Run all constant tests."""
    logger.info("\n" + "="*60)
    logger.info("CONSTANTS MODULE TESTS")
    logger.info("="*60 + "\n")
    
    try:
        test_languages_structure()
        test_languages_count()
        test_cjk_vs_latin()
        logger.info("")
        
        test_generations_structure()
        test_generations_count()
        logger.info("")
        
        test_type_colors()
        logger.info("")
        
        test_page_dimensions()
        
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
