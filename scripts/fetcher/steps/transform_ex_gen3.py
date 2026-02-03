"""
Transform Scarlet & Violet ex Cards to Variant Format (Single Card per Pokemon)

Transforms TCGdex Scarlet & Violet ex card data from source format to the variant format
expected by the PDF generator. Selects ONE card per Pokemon (priority: Base Set first,
then alphabetically by set name).

Input: data/source/tcg_sv_ex.json (366 cards)
Output: data/output/ExGen3.json (~130 unique Pokemon)
"""

import logging
from pathlib import Path
from typing import List, Dict, Any
import sys
import json
import requests

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from steps.base import BaseStep, PipelineContext
from steps.pokemon_utils import get_mega_artwork_url

logger = logging.getLogger(__name__)


class TransformScarletVioletEXStep(BaseStep):
    """
    Transform Scarlet & Violet ex cards to variant format - ONE card per Pokemon.
    
    Selection priority when multiple cards exist:
    1. SV - Base Set (first SV ex set, sv1)
    2. Alphabetically by set name
    
    Excludes:
    - Tera ex variants (separate Tera crystallization)
    """
    
    def __init__(self, name: str):
        super().__init__(name)
    
    def execute(self, context: PipelineContext, params: Dict[str, Any]) -> PipelineContext:
        """
        Execute the transformation.
        
        1. Load source data from context
        2. Group by Pokemon (dexId)
        3. Select one card per Pokemon (priority rules)
        4. Transform to variant format
        """
        logger.info(f"Starting SV ex cards transformation (single card per Pokemon)")
        
        # Load cards from context
        cards = context.data.get('tcg_sv_ex_cards')
        if not cards:
            raise ValueError("No SV ex cards found in context. Make sure fetch_tcgdex_ex_gen3 ran before this step.")
        
        logger.info(f"Loaded {len(cards)} cards from source")
        
        # Group cards by type (normal, mega) and dexId
        # For mega cards, we use a tuple (dexId, form_name) to handle X/Y variants
        normal_cards: Dict[int, List[Dict[str, Any]]] = {}
        mega_cards: Dict[tuple, List[Dict[str, Any]]] = {}
        
        for card in cards:
            dex_ids = card.get('dexId', [])
            if not dex_ids:
                logger.warning(f"Card {card.get('name')} has no dexId")
                continue
            
            dex_id = dex_ids[0]
            name = card.get('name', '')
            
            # Categorize by card type
            if name.startswith('Mega ') or 'Mega' in name:
                # Mega Evolution variant - extract form suffix (e.g., "X", "Y")
                # Name format: "Mega Pokemon X ex" or "Mega Pokemon Y ex"
                form_suffix = ""
                parts = name.replace(' ex', '').split()
                if len(parts) > 2 and parts[-1] in ['X', 'Y']:
                    form_suffix = parts[-1]
                
                # Use (dexId, form_suffix) as key to keep X and Y variants separate
                mega_key = (dex_id, form_suffix)
                if mega_key not in mega_cards:
                    mega_cards[mega_key] = []
                mega_cards[mega_key].append(card)
            else:
                # Normal ex variant (all other ex cards are tera by default in SV era)
                if dex_id not in normal_cards:
                    normal_cards[dex_id] = []
                normal_cards[dex_id].append(card)
        
        logger.info(f"Grouped into normal={len(normal_cards)}, mega={len(mega_cards)} Pokemon")
        
        # Select one card per Pokemon for each type
        selected_normal = self._select_best_cards(normal_cards)
        selected_mega = self._select_best_cards(mega_cards)
        
        logger.info(f"Selected normal={len(selected_normal)}, mega={len(selected_mega)} cards")
        
        # Transform to variant format with 2 sections
        variant_data = self._transform_to_variant_format(selected_normal, selected_mega, context)
        
        # Store in context for subsequent enrichment steps and for save_output step
        context.set_data(variant_data)
        
        logger.info(f"✅ Transformed Scarlet & Violet ex cards to variant format")
        
        return context
    
    def _select_best_cards(self, pokemon_cards: Dict) -> List[Dict[str, Any]]:
        """
        Select one card per Pokemon (or form) based on priority rules.
        
        Accepts either:
        - Dict[int, List] for normal cards (grouped by dexId)
        - Dict[tuple, List] for mega cards (grouped by dexId + form_suffix)
        
        Priority:
        1. SV - Base Set (sv1)
        2. Alphabetically by set name
        """
        selected_cards = []
        
        for key in sorted(pokemon_cards.keys()):
            # Extract dex_id from key (either int or tuple)
            dex_id = key if isinstance(key, int) else key[0]
            cards_for_pokemon = pokemon_cards[key]
            
            if len(cards_for_pokemon) == 1:
                selected_cards.append(cards_for_pokemon[0])
            else:
                # Apply priority rules
                # 1. SV - Base Set (sv1)
                sv1_cards = [c for c in cards_for_pokemon if c['set']['id'] == 'sv1']
                if sv1_cards:
                    selected_cards.append(sv1_cards[0])
                    logger.debug(f"#{dex_id:03d}: Selected Base Set card")
                    continue
                
                # 2. Alphabetically by set name
                cards_sorted = sorted(cards_for_pokemon, key=lambda c: c['set']['name'])
                selected_cards.append(cards_sorted[0])
                logger.debug(f"#{dex_id:03d}: Selected {cards_sorted[0]['set']['name']} card (alphabetical)")
        
        return selected_cards
    
    def _transform_to_variant_format(self, normal_cards: List[Dict[str, Any]], mega_cards: List[Dict[str, Any]], context: PipelineContext) -> Dict[str, Any]:
        """
        Transform cards to the variant format expected by PDF generator.
        
        Creates 2 sections: normal, mega
        """
        # Get variant metadata from context
        metadata = context.storage.get('metadata', {})
        variant_meta = metadata.get('variants', {}).get('ExGen3', {})
        
        # Transform each card list
        normal_pokemon = self._transform_card_list(normal_cards, suffix='[EX_NEW]', prefix=None)
        mega_pokemon = self._transform_card_list(mega_cards, suffix='[EX_NEW]', prefix='Mega')
        
        # Create 2-section structure
        variant_data = {
            'type': 'variant',
            'name': 'Pokémon ex - Generation 3',
            'sections': {
                'normal': {
                    'section_id': 'normal',
                    'color_hex': variant_meta.get('color', '#6B40D1'),
                    'title': {
                        'de': 'Pokémon [EX_NEW]',
                        'en': 'Pokémon [EX_NEW]',
                        'fr': 'Pokémon [EX_NEW]',
                        'es': 'Pokémon [EX_NEW]',
                        'it': 'Pokémon [EX_NEW]',
                        'ja': 'ポケモン [EX_NEW]',
                        'ko': '포켓몬 [EX_NEW]',
                        'zh_hans': '宝可梦 [EX_NEW]',
                        'zh_hant': '寶可夢 [EX_NEW]'
                    },
                    'subtitle': variant_meta.get('subtitle', {}),
                    'suffix': '',
                    'cards': normal_pokemon
                },
                'mega': {
                    'section_id': 'mega',
                    'color_hex': '#7B2CBF',  # Same as ExGen2 mega
                    'title': {
                        'de': 'Mega-Pokémon [EX_NEW]',
                        'en': 'Mega Pokémon [EX_NEW]',
                        'fr': 'Méga-Pokémon [EX_NEW]',
                        'es': 'Mega-Pokémon [EX_NEW]',
                        'it': 'Mega-Pokémon [EX_NEW]',
                        'ja': 'メガポケモン [EX_NEW]',
                        'ko': '메가 포켓몬 [EX_NEW]',
                        'zh_hans': '超级宝可梦 [EX_NEW]',
                        'zh_hant': '超級寶可夢 [EX_NEW]'
                    },
                    'subtitle': {
                        'de': 'Mega-Entwicklung',
                        'en': 'Mega Evolution',
                        'fr': 'Méga-Évolution',
                        'es': 'Megaevolución',
                        'it': 'Megaevoluzione',
                        'ja': 'メガシンカ',
                        'ko': '메가진화',
                        'zh_hans': '超级进化',
                        'zh_hant': '超級進化'
                    },
                    'suffix': '',
                    'cards': mega_pokemon
                }
            }
        }
        
        logger.info(f"Created variant with normal={len(normal_pokemon)}, mega={len(mega_pokemon)} Pokemon")
        
        return variant_data
    
    def _get_pokeapi_artwork_url(self, dex_id: int, pokemon_name: str, is_mega: bool = False, form_suffix: str = None) -> str:
        """
        Generate PokeAPI official artwork URL for a Pokemon.
        
        Args:
            dex_id: National Pokedex ID
            pokemon_name: Pokemon name (e.g., "Charizard")
            is_mega: Whether this is a Mega Evolution
            form_suffix: Form suffix like "X" or "Y" for Mega variants
        
        Returns:
            URL to official artwork PNG
        """
        # For normal Pokemon, use direct artwork URL
        if not is_mega:
            return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{dex_id}.png"
        
        # For Mega Evolutions, use shared utility function
        return get_mega_artwork_url(
            pokemon_name=pokemon_name,
            base_id=dex_id,
            form_suffix=form_suffix
        )
    
    def _transform_card_list(self, cards: List[Dict[str, Any]], suffix: str = None, prefix: str = None) -> List[Dict[str, Any]]:
        """Transform a list of cards to Pokemon entries."""
        pokemon_list = []
        
        for card in cards:
            dex_ids = card.get('dexId', [])
            if not dex_ids:
                continue
            
            dex_id = dex_ids[0]
            name = card.get('name', '')
            
            # Extract Pokemon name (remove ex suffix and variants)
            pokemon_name_raw = name.replace(' ex', '').replace('–ex-Tera', '').replace('-ex-Tera', '').replace('Mega ', '').strip()
            
            # Get image URL from PokeAPI official artwork
            # Check if this is a Mega evolution with form suffix
            form_suffix = None
            pokemon_base_name = pokemon_name_raw
            
            if prefix == 'Mega':
                # Extract X/Y suffix if present: "Charizard X" -> base="Charizard", suffix="X"
                parts = pokemon_name_raw.split()
                if len(parts) >= 2 and parts[-1] in ['X', 'Y']:
                    form_suffix = parts[-1]
                    pokemon_base_name = ' '.join(parts[:-1])  # Remove X/Y from name
            
            image_url = self._get_pokeapi_artwork_url(dex_id, pokemon_base_name, is_mega=(prefix == 'Mega'), form_suffix=form_suffix)
            
            pokemon_name = pokemon_name_raw
            
            pokemon_entry = {
                'pokemon_id': dex_id,
                'types': card.get('types', []),
                'image_url': image_url,
                'name': {
                    'en': pokemon_name,
                    'de': pokemon_name,
                    'fr': pokemon_name,
                    'es': pokemon_name,
                    'it': pokemon_name,
                    'ja': pokemon_name,
                    'ko': pokemon_name,
                    'zh_hans': pokemon_name,
                    'zh_hant': pokemon_name
                },
                'prefix': prefix,
                'suffix': suffix,
                'form_code': f"#{dex_id:03d}_EX3",
                'tcg_card': {
                    'id': card.get('id'),
                    'localId': card.get('localId'),
                    'set': card.get('set'),
                    'hp': card.get('hp'),
                    'rarity': card.get('rarity')
                }
            }
            
            pokemon_list.append(pokemon_entry)
        
        return pokemon_list
    
