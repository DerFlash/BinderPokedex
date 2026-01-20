"""
Tests for Data Storage Module

Tests JSON loading and saving of Pokémon data.
"""

import sys
import logging
import json
import tempfile
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from data_storage import DataStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_data_storage_initialization():
    """Test DataStorage initialization with custom directory."""
    logger.info("Testing DataStorage initialization...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = DataStorage(data_dir=Path(tmpdir))
        
        assert storage.data_dir == Path(tmpdir)
        assert storage.data_dir.exists()
        
        logger.info(f"✓ DataStorage initialized with {tmpdir}")


def test_save_and_load_generation():
    """Test saving and loading generation data with consolidated format."""
    logger.info("Testing save and load with consolidated format...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = DataStorage(data_dir=Path(tmpdir))
        
        # Test data - simulate consolidated format
        consolidated_data = {
            "version": "2.0",
            "sections": {
                "gen1": {
                    "id": 1,
                    "name": "Generation I",
                    "region": "Kanto",
                    "range": [1, 3],
                    "iconic_pokemon": [1],
                    "pokemon": [
                        {'id': 1, 'name': 'Bisasam', 'types': ['Pflanze', 'Gift'], 'number': 1},
                        {'id': 2, 'name': 'Bisaknosp', 'types': ['Pflanze', 'Gift'], 'number': 2},
                        {'id': 3, 'name': 'Bisakutor', 'types': ['Pflanze', 'Gift'], 'number': 3},
                    ]
                }
            }
        }
        
        # Write consolidated file
        consolidated_file = Path(tmpdir) / "pokemon.json"
        with open(consolidated_file, 'w', encoding='utf-8') as f:
            json.dump(consolidated_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Saved consolidated: {consolidated_file}")
        
        # Load - this clears cache and reloads
        storage._consolidated_data = None
        loaded_data = storage.load_generation(1)
        assert len(loaded_data) == 3, f"Expected 3 pokemon, got {len(loaded_data)}"
        assert loaded_data[0]['name'] == 'Bisasam', "Name mismatch"
        assert loaded_data[2]['types'] == ['Pflanze', 'Gift'], "Types mismatch"
        
        logger.info(f"✓ Loaded: {len(loaded_data)} pokemon")


def test_load_nonexistent_generation():
    """Test loading non-existent generation returns empty list."""
    logger.info("Testing load non-existent...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = DataStorage(data_dir=Path(tmpdir))
        
        # Try to load generation that doesn't exist
        data = storage.load_generation(99)
        
        assert isinstance(data, list), "Should return list"
        assert len(data) == 0, "Should return empty list for missing file"
        
        logger.info(f"✓ Non-existent generation returns empty list")


def test_save_multiple_generations():
    """Test saving multiple generations."""
    logger.info("Testing multiple generations...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = DataStorage(data_dir=Path(tmpdir))
        
        for gen in range(1, 4):
            pokemon_data = [
                {'id': i, 'name': f'Pokemon {i}', 'generation': gen}
                for i in range(1, 4)
            ]
            storage.save_generation(gen, pokemon_data)
        
        # Verify all files exist
        for gen in range(1, 4):
            gen_file = storage.data_dir / f"pokemon_gen{gen}.json"
            assert gen_file.exists(), f"Gen {gen} file not found"
        
        # Verify data integrity
        for gen in range(1, 4):
            data = storage.load_generation(gen)
            assert all(p['generation'] == gen for p in data), f"Gen {gen}: data corruption"
        
        logger.info(f"✓ All 3 generations saved and verified")


def test_unicode_handling():
    """Test proper handling of Unicode characters in consolidated format."""
    logger.info("Testing Unicode handling...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = DataStorage(data_dir=Path(tmpdir))
        
        # Data with various Unicode characters - in consolidated format
        consolidated_data = {
            "version": "2.0",
            "sections": {
                "gen1": {
                    "id": 1,
                    "name": "Generation I",
                    "region": "Kanto",
                    "range": [1, 4],
                    "iconic_pokemon": [1],
                    "pokemon": [
                        {'id': 1, 'name': 'Bisasam', 'german': 'Bisamanda', 'language': 'de'},
                        {'id': 2, 'name': '草之精靈', 'chinese': '简体中文', 'language': 'zh'},
                        {'id': 3, 'name': 'ポケモン', 'japanese': '日本語', 'language': 'ja'},
                        {'id': 4, 'name': 'Pokémon', 'accent': 'é', 'language': 'fr'},
                    ]
                }
            }
        }
        
        # Write consolidated file
        consolidated_file = Path(tmpdir) / "pokemon.json"
        with open(consolidated_file, 'w', encoding='utf-8') as f:
            json.dump(consolidated_data, f, indent=2, ensure_ascii=False)
        
        # Clear cache and load
        storage._consolidated_data = None
        loaded_data = storage.load_generation(1)
        
        # Verify all Unicode is preserved
        assert loaded_data[1]['name'] == '草之精靈', "Chinese characters corrupted"
        assert loaded_data[2]['name'] == 'ポケモン', "Japanese characters corrupted"
        assert loaded_data[3]['name'] == 'Pokémon', "Accented characters corrupted"
        
        logger.info(f"✓ All Unicode characters preserved")


def test_json_formatting():
    """Test that saved JSON is properly formatted."""
    logger.info("Testing JSON formatting...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = DataStorage(data_dir=Path(tmpdir))
        
        pokemon_data = [
            {'id': 1, 'name': 'Test', 'data': {'nested': 'value'}}
        ]
        
        output_file = storage.save_generation(1, pokemon_data)
        
        # Read raw file to check formatting
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should be readable JSON with indentation
        assert '\n' in content, "JSON not formatted with newlines"
        
        # Should not have escaped unicode
        assert '\\u' not in content, "Unicode should not be escaped"
        
        # Should be valid JSON
        parsed = json.loads(content)
        assert len(parsed) == 1
        
        logger.info(f"✓ JSON properly formatted and readable")


def test_get_data_dir():
    """Test getting data directory."""
    logger.info("Testing get_data_dir...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = DataStorage(data_dir=Path(tmpdir))
        
        retrieved_dir = storage.get_data_dir()
        assert retrieved_dir == Path(tmpdir)
        assert retrieved_dir.exists()
        
        logger.info(f"✓ get_data_dir returns correct path")


def test_empty_generation_save():
    """Test saving empty generation list."""
    logger.info("Testing empty generation save...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = DataStorage(data_dir=Path(tmpdir))
        
        # Save empty list
        output_file = storage.save_generation(1, [])
        assert output_file.exists()
        
        # Load it back
        loaded = storage.load_generation(1)
        assert loaded == [], "Empty list should load as empty"
        
        logger.info(f"✓ Empty generation handled correctly")


def run_all_tests():
    """Run all data storage tests."""
    logger.info("\n" + "="*60)
    logger.info("DATA STORAGE TESTS")
    logger.info("="*60 + "\n")
    
    try:
        test_data_storage_initialization()
        logger.info("")
        
        test_save_and_load_generation()
        logger.info("")
        
        test_load_nonexistent_generation()
        logger.info("")
        
        test_save_multiple_generations()
        logger.info("")
        
        test_unicode_handling()
        logger.info("")
        
        test_json_formatting()
        logger.info("")
        
        test_get_data_dir()
        logger.info("")
        
        test_empty_generation_save()
        
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
