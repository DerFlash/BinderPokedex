"""
Tests for TCG Set Transform Module

Tests the transformation of TCG cards to target format, including:
- Variant suffix/prefix determination
- Name dict building
- Pokemon vs Trainer card handling
"""

import sys
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'fetcher'))

from steps.transform_tcg_set import TransformTCGSetStep


class TestVariantSuffixPrefixDetection:
    """Test variant suffix and prefix detection from card names."""
    
    def setup_method(self):
        """Setup test instance."""
        self.step = TransformTCGSetStep("test_suffix_prefix")
    
    def test_modern_ex_detection(self):
        """Test detection of modern lowercase ex (Scarlet & Violet era)."""
        card = {'name': 'Mega Venusaur ex'}
        suffix, prefix = self.step._determine_variant_suffix_and_prefix(card)
        
        assert suffix == '[EX_NEW]'
        assert prefix == 'Mega'
    
    def test_ex_only(self):
        """Test detection of ex suffix without prefix."""
        card = {'name': 'Charizard ex'}
        suffix, prefix = self.step._determine_variant_suffix_and_prefix(card)
        
        assert suffix == '[EX_NEW]'
        assert prefix is None
    
    def test_gx_detection(self):
        """Test detection of GX suffix."""
        card = {'name': 'Pikachu GX'}
        suffix, prefix = self.step._determine_variant_suffix_and_prefix(card)
        
        assert suffix == 'GX'
        assert prefix is None
    
    def test_vmax_detection(self):
        """Test detection of VMAX suffix."""
        card = {'name': 'Charizard VMAX'}
        suffix, prefix = self.step._determine_variant_suffix_and_prefix(card)
        
        assert suffix == 'VMAX'
        assert prefix is None
    
    def test_vstar_detection(self):
        """Test detection of VSTAR suffix."""
        card = {'name': 'Arceus VSTAR'}
        suffix, prefix = self.step._determine_variant_suffix_and_prefix(card)
        
        assert suffix == 'VSTAR'
        assert prefix is None
    
    def test_v_detection(self):
        """Test detection of V suffix."""
        card = {'name': 'Lucario V'}
        suffix, prefix = self.step._determine_variant_suffix_and_prefix(card)
        
        assert suffix == 'V'
        assert prefix is None
    
    def test_mega_only(self):
        """Test detection of Mega prefix only."""
        card = {'name': 'Mega Charizard'}
        suffix, prefix = self.step._determine_variant_suffix_and_prefix(card)
        
        assert suffix is None
        assert prefix == 'Mega'
    
    def test_radiant_prefix(self):
        """Test detection of Radiant prefix."""
        card = {'name': 'Radiant Charizard'}
        suffix, prefix = self.step._determine_variant_suffix_and_prefix(card)
        
        assert suffix is None
        assert prefix == 'Radiant'
    
    def test_shining_prefix(self):
        """Test detection of Shining prefix."""
        card = {'name': 'Shining Mew'}
        suffix, prefix = self.step._determine_variant_suffix_and_prefix(card)
        
        assert suffix is None
        assert prefix == 'Shining'
    
    def test_base_card(self):
        """Test base card without variants."""
        card = {'name': 'Pikachu'}
        suffix, prefix = self.step._determine_variant_suffix_and_prefix(card)
        
        assert suffix is None
        assert prefix is None
    
    def test_hyphenated_ex(self):
        """Test hyphenated ex suffix."""
        card = {'name': 'Venusaur-ex'}
        suffix, prefix = self.step._determine_variant_suffix_and_prefix(card)
        
        assert suffix == '[EX_NEW]'
        assert prefix is None
    
    def test_case_insensitive(self):
        """Test case-insensitive detection."""
        card = {'name': 'Mega CHARIZARD ex'}  # Mixed case
        suffix, prefix = self.step._determine_variant_suffix_and_prefix(card)
        
        assert suffix == '[EX_NEW]'
        assert prefix == 'Mega'
    
    def test_no_name_field(self):
        """Test card with missing name field."""
        card = {}
        suffix, prefix = self.step._determine_variant_suffix_and_prefix(card)
        
        assert suffix is None
        assert prefix is None


class TestCardTransformation:
    """Test full card transformation logic."""
    
    def setup_method(self):
        """Setup test instance."""
        self.step = TransformTCGSetStep("test_transformation")
    
    def test_transform_base_pokemon_card(self):
        """Test transformation of base Pokemon card."""
        cards = [{
            'localId': '001',
            'name': 'Bulbasaur',
            'card_type': 'pokemon',
            'pokemon_id': 1,
            'types': ['Grass'],
            'image': 'https://example.com/image.png',
            'name_de': 'Bisasam',
            'name_en': 'Bulbasaur',
            'name_fr': 'Bulbizarre'
        }]
        
        result = self.step._transform_cards(cards)
        
        assert len(result) == 1
        card = result[0]
        
        assert card['localId'] == '001'
        assert card['type'] == 'pokemon'
        assert card['pokemon_id'] == 1
        assert card['types'] == ['Grass']
        assert isinstance(card['name'], dict)
        assert card['name']['de'] == 'Bisasam'
        assert card['name']['en'] == 'Bulbasaur'
        assert card['name']['fr'] == 'Bulbizarre'
        assert 'suffix' not in card  # No suffix for base card
        assert 'prefix' not in card
    
    def test_transform_variant_pokemon_card(self):
        """Test transformation of variant Pokemon card."""
        cards = [{
            'localId': '003',
            'name': 'Mega Venusaur ex',  # Original TCGdex name
            'card_type': 'pokemon',
            'pokemon_id': 3,
            'types': ['Grass'],
            'image': 'https://example.com/image.png',
            'name_de': 'Bisaflor',  # Base name from Pokedex
            'name_en': 'Venusaur',
            'name_fr': 'Florizarre'
        }]
        
        result = self.step._transform_cards(cards)
        
        assert len(result) == 1
        card = result[0]
        
        assert card['type'] == 'pokemon'
        assert card['pokemon_id'] == 3
        # Base names only
        assert card['name']['de'] == 'Bisaflor'
        assert card['name']['en'] == 'Venusaur'
        # Variants as separate fields
        assert card['suffix'] == '[EX_NEW]'
        assert card['prefix'] == 'Mega'
    
    def test_transform_trainer_card(self):
        """Test transformation of trainer card."""
        cards = [{
            'localId': '113',
            'name': "Acerola's Mischief",
            'card_type': 'trainer',
            'types': [],
            'image': 'https://example.com/image.png',
            'name_de': "Acerola's Mischief",
            'name_en': "Acerola's Mischief"
        }]
        
        result = self.step._transform_cards(cards)
        
        assert len(result) == 1
        card = result[0]
        
        assert card['type'] == 'trainer'
        assert card['types'] == []
        assert card['image_url'] is None
        assert isinstance(card['name'], dict)
        assert card['name']['de'] == "Acerola's Mischief"
    
    def test_transform_multiple_cards(self):
        """Test transformation of multiple cards."""
        cards = [
            {
                'localId': '001',
                'name': 'Bulbasaur',
                'card_type': 'pokemon',
                'pokemon_id': 1,
                'types': ['Grass'],
                'image': 'https://example.com/1.png',
                'name_de': 'Bisasam',
                'name_en': 'Bulbasaur'
            },
            {
                'localId': '002',
                'name': 'Pikachu ex',
                'card_type': 'pokemon',
                'pokemon_id': 25,
                'types': ['Electric'],
                'image': 'https://example.com/2.png',
                'name_de': 'Pikachu',
                'name_en': 'Pikachu'
            },
            {
                'localId': '003',
                'name': 'Professor Oak',
                'card_type': 'trainer',
                'types': [],
                'image': 'https://example.com/3.png',
                'name_de': 'Professor Oak',
                'name_en': 'Professor Oak'
            }
        ]
        
        result = self.step._transform_cards(cards)
        
        assert len(result) == 3
        assert result[0]['type'] == 'pokemon'
        assert result[1]['type'] == 'pokemon'
        assert result[1]['suffix'] == '[EX_NEW]'
        assert result[2]['type'] == 'trainer'
    
    def test_transform_all_variant_types(self):
        """Test transformation of all variant types."""
        variant_cards = [
            {'name': 'Pikachu ex', 'expected_suffix': '[EX_NEW]'},
            {'name': 'Charizard GX', 'expected_suffix': 'GX'},
            {'name': 'Lucario V', 'expected_suffix': 'V'},
            {'name': 'Charizard VMAX', 'expected_suffix': 'VMAX'},
            {'name': 'Arceus VSTAR', 'expected_suffix': 'VSTAR'},
            {'name': 'Mega Charizard', 'expected_prefix': 'Mega'},
            {'name': 'Radiant Greninja', 'expected_prefix': 'Radiant'},
            {'name': 'Shining Mew', 'expected_prefix': 'Shining'}
        ]
        
        for variant in variant_cards:
            cards = [{
                'localId': '001',
                'name': variant['name'],
                'card_type': 'pokemon',
                'pokemon_id': 1,
                'types': ['Fire'],
                'image': 'https://example.com/image.png',
                'name_en': 'Test'
            }]
            
            result = self.step._transform_cards(cards)
            card = result[0]
            
            if 'expected_suffix' in variant:
                assert card.get('suffix') == variant['expected_suffix'], \
                    f"Expected suffix {variant['expected_suffix']} for {variant['name']}"
            
            if 'expected_prefix' in variant:
                assert card.get('prefix') == variant['expected_prefix'], \
                    f"Expected prefix {variant['expected_prefix']} for {variant['name']}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
