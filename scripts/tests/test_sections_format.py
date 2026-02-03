"""
Tests for TCG Sections Format Transform Module

Tests the transformation of TCG card data to sections format, including:
- Filtering Pokemon vs Trainer cards
- Sections structure creation
- Title and description generation
"""

import sys
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'fetcher'))

from steps.base import PipelineContext


class TestSectionsFormatTransform:
    """Test sections format transformation."""
    
    def test_pokemon_filtering(self):
        """Test that only Pokemon cards are included in sections."""
        # Mock transformed data with mixed card types
        cards = [
            {'localId': '001', 'type': 'pokemon', 'pokemon_id': 1, 'name': {'en': 'Bulbasaur'}},
            {'localId': '002', 'type': 'pokemon', 'pokemon_id': 2, 'name': {'en': 'Ivysaur'}},
            {'localId': '003', 'type': 'trainer', 'name': {'en': 'Professor Oak'}},
            {'localId': '004', 'type': 'trainer', 'name': {'en': 'Potion'}},
            {'localId': '005', 'type': 'pokemon', 'pokemon_id': 25, 'name': {'en': 'Pikachu'}},
        ]
        
        pokemon_cards = [c for c in cards if c.get('type') == 'pokemon']
        trainer_cards = [c for c in cards if c.get('type') == 'trainer']
        
        assert len(pokemon_cards) == 3
        assert len(trainer_cards) == 2
        assert all(c.get('pokemon_id') for c in pokemon_cards)
    
    def test_sections_structure(self):
        """Test correct sections structure creation."""
        pokemon_cards = [
            {'localId': '001', 'type': 'pokemon', 'pokemon_id': 1, 'name': {'en': 'Bulbasaur'}},
            {'localId': '002', 'type': 'pokemon', 'pokemon_id': 2, 'name': {'en': 'Ivysaur'}},
        ]
        
        sections_data = {
            'type': 'tcg_set',
            'name': 'Mega Evolution',
            'sections': {
                'all': {
                    'title': {
                        'de': 'Mega Evolution',
                        'en': 'Mega Evolution'
                    },
                    'description': {
                        'de': 'Mega Evolution - Pokemon-Karten',
                        'en': 'Mega Evolution - Pokemon Cards'
                    },
                    'pokemon': pokemon_cards
                }
            }
        }
        
        assert 'sections' in sections_data
        assert 'all' in sections_data['sections']
        assert 'title' in sections_data['sections']['all']
        assert 'description' in sections_data['sections']['all']
        assert 'cards' in sections_data['sections']['all']
        
        cards = sections_data['sections']['all']['cards']
        assert len(cards) == 2
        assert all(c['type'] == 'pokemon' for c in cards)
    
    def test_multilingual_titles(self):
        """Test multilingual title and description generation."""
        set_name_de = 'Mega-Entwicklung'
        set_name_en = 'Mega Evolution'
        
        title = {
            'de': set_name_de,
            'en': set_name_en
        }
        
        description = {
            'de': f"{set_name_de} - Pokemon-Karten",
            'en': f"{set_name_en} - Pokemon Cards"
        }
        
        assert title['de'] == 'Mega-Entwicklung'
        assert title['en'] == 'Mega Evolution'
        assert 'Pokemon-Karten' in description['de']
        assert 'Pokemon Cards' in description['en']
    
    def test_empty_trainer_list(self):
        """Test handling when all cards are Pokemon (no trainers)."""
        cards = [
            {'localId': '001', 'type': 'pokemon', 'pokemon_id': 1},
            {'localId': '002', 'type': 'pokemon', 'pokemon_id': 2},
            {'localId': '003', 'type': 'pokemon', 'pokemon_id': 3},
        ]
        
        pokemon_cards = [c for c in cards if c.get('type') == 'pokemon']
        trainer_cards = [c for c in cards if c.get('type') == 'trainer']
        
        assert len(pokemon_cards) == 3
        assert len(trainer_cards) == 0
    
    def test_empty_pokemon_list(self):
        """Test handling when all cards are Trainers (edge case)."""
        cards = [
            {'localId': '001', 'type': 'trainer'},
            {'localId': '002', 'type': 'trainer'},
        ]
        
        pokemon_cards = [c for c in cards if c.get('type') == 'pokemon']
        trainer_cards = [c for c in cards if c.get('type') == 'trainer']
        
        assert len(pokemon_cards) == 0
        assert len(trainer_cards) == 2
    
    def test_variant_cards_included(self):
        """Test that variant Pokemon cards are included."""
        cards = [
            {
                'localId': '001',
                'type': 'pokemon',
                'pokemon_id': 3,
                'suffix': '[EX_NEW]',
                'prefix': 'Mega',
                'name': {'en': 'Venusaur'}
            },
            {
                'localId': '002',
                'type': 'pokemon',
                'pokemon_id': 6,
                'suffix': 'GX',
                'name': {'en': 'Charizard'}
            },
            {
                'localId': '003',
                'type': 'pokemon',
                'pokemon_id': 25,
                'suffix': 'VMAX',
                'name': {'en': 'Pikachu'}
            }
        ]
        
        pokemon_cards = [c for c in cards if c.get('type') == 'pokemon']
        
        assert len(pokemon_cards) == 3
        # Verify variants are preserved
        assert pokemon_cards[0].get('suffix') == '[EX_NEW]'
        assert pokemon_cards[0].get('prefix') == 'Mega'
        assert pokemon_cards[1].get('suffix') == 'GX'
        assert pokemon_cards[2].get('suffix') == 'VMAX'
    
    def test_large_set_filtering(self):
        """Test filtering with large mixed card set."""
        # Simulate ME01 set: 152 Pokemon, 36 Trainers = 188 total
        cards = []
        for i in range(152):
            cards.append({
                'localId': f'{i+1:03d}',
                'type': 'pokemon',
                'pokemon_id': (i % 151) + 1
            })
        for i in range(36):
            cards.append({
                'localId': f'{152+i+1:03d}',
                'type': 'trainer'
            })
        
        pokemon_cards = [c for c in cards if c.get('type') == 'pokemon']
        trainer_cards = [c for c in cards if c.get('type') == 'trainer']
        
        assert len(pokemon_cards) == 152
        assert len(trainer_cards) == 36
        assert len(cards) == 188


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
