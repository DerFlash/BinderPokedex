"""
Transform Classic ex Cards to Variant Format (Single Card per Pokemon)

Transforms TCGdex Classic ex card data from source format to the variant format
expected by the PDF generator. Selects ONE card per Pokemon (priority: FireRed & LeafGreen,
then Ruby & Sapphire, then alphabetically by set name).

Input: data/source/tcg_classic_ex.json (128 cards)
Output: data/variants/variants_ex_gen1_single.json (103 unique Pokemon)
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

logger = logging.getLogger(__name__)


class TransformClassicExStep(BaseStep):
    """
    Transform Classic ex cards to variant format - ONE card per Pokemon.
    
    Selection priority when multiple cards exist:
    1. FireRed & LeafGreen (iconic Gen1 set)
    2. Ruby & Sapphire (first EX set)
    3. Alphabetically by set name
    
    Excludes:
    - Rocket's variants (e.g., "Rocket's Mewtwo ex")
    - Delta Species variants (δ suffix)
    """
    
    def __init__(self, name: str):
        super().__init__(name)
    
    def execute(self, context: PipelineContext, params: Dict[str, Any]) -> PipelineContext:
        """
        Execute the transformation.
        
        1. Load source data from context
        2. Group by Pokemon (dexId)
        3. Select one card per Pokemon (priority rules)
        4. Fetch Pokemon names from PokeAPI context or use card names
        5. Transform to variant format
        """
        logger.info(f"Starting Classic ex cards transformation (single card per Pokemon)")
        
        # Load cards from context
        cards = context.data.get('tcg_classic_ex_cards')
        if not cards:
            raise ValueError("No Classic ex cards found in context. Make sure fetch_tcgdex_ex_gen1 ran before this step.")
        
        logger.info(f"Loaded {len(cards)} cards from source")
        
        # Group cards by dexId
        pokemon_cards: Dict[int, List[Dict[str, Any]]] = {}
        
        for card in cards:
            dex_id = card['dexId'][0]
            
            # Skip Rocket's variants
            if "Rocket's" in card['name']:
                logger.debug(f"Skipping Rocket's variant: {card['name']}")
                continue
            
            # Skip Delta Species (δ)
            if 'δ' in card['name'] or 'delta' in card['name'].lower():
                logger.debug(f"Skipping Delta Species: {card['name']}")
                continue
            
            if dex_id not in pokemon_cards:
                pokemon_cards[dex_id] = []
            
            pokemon_cards[dex_id].append(card)
        
        logger.info(f"Grouped into {len(pokemon_cards)} unique Pokemon")
        
        # Select one card per Pokemon
        selected_cards = []
        
        for dex_id in sorted(pokemon_cards.keys()):
            cards_for_pokemon = pokemon_cards[dex_id]
            
            if len(cards_for_pokemon) == 1:
                selected_cards.append(cards_for_pokemon[0])
            else:
                # Apply priority rules
                # 1. FireRed & LeafGreen
                frlg_cards = [c for c in cards_for_pokemon if c['set']['id'] == 'ex6']
                if frlg_cards:
                    selected_cards.append(frlg_cards[0])
                    logger.debug(f"#{dex_id:03d}: Selected FireRed & LeafGreen card")
                    continue
                
                # 2. Ruby & Sapphire
                rs_cards = [c for c in cards_for_pokemon if c['set']['id'] == 'ex1']
                if rs_cards:
                    selected_cards.append(rs_cards[0])
                    logger.debug(f"#{dex_id:03d}: Selected Ruby & Sapphire card")
                    continue
                
                # 3. Alphabetically by set name
                cards_sorted = sorted(cards_for_pokemon, key=lambda c: c['set']['name'])
                selected_cards.append(cards_sorted[0])
                logger.debug(f"#{dex_id:03d}: Selected {cards_sorted[0]['set']['name']} card (alphabetical)")
        
        logger.info(f"Selected {len(selected_cards)} cards (one per Pokemon)")
        
        # Transform to variant format
        variant_data = self._transform_to_variant_format(selected_cards, context)
        
        # Store in context for subsequent enrichment steps and for save_output step
        context.set_data(variant_data)
        
        logger.info(f"✅ Transformed {len(selected_cards)} Classic ex cards to variant format")
        
        return context
    
    def _transform_to_variant_format(self, cards: List[Dict[str, Any]], context: PipelineContext) -> Dict[str, Any]:
        """
        Transform cards to the variant format expected by PDF generator.
        
        Format matches existing variants_ex_gen1.json structure.
        """
        # Get variant metadata from context
        metadata = context.storage.get('metadata', {})
        variant_meta = metadata.get('variants', {}).get('ExGen1', {})
        
        pokemon_list = []
        
        for card in cards:
            dex_id = card['dexId'][0]
            
            # Extract Pokemon name and prefix/suffix
            # Classic ex cards have " ex" suffix (lowercase, e.g., "Charizard ex")
            # Some have prefixes like "Rocket's Mewtwo ex"
            pokemon_name = card['name'].replace(' ex', '')
            
            prefix = None
            if "Rocket's" in pokemon_name:
                # Extract Rocket's prefix
                prefix = "Rocket's"
                pokemon_name = pokemon_name.replace("Rocket's ", '')
            
            suffix = 'ex'  # Classic ex uses lowercase text "ex" (not a logo)
            
            # Get image URL from PokeAPI official artwork
            # ExGen1 only has normal ex cards, no Mega/Primal variants
            image_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{dex_id}.png"
            
            pokemon_entry = {
                'pokemon_id': dex_id,
                'types': card['types'] if card['types'] else [],
                'image_url': image_url,
                'name': {
                    'en': pokemon_name,
                    'de': pokemon_name,  # TODO: Could be enriched later
                    'fr': pokemon_name,
                    'es': pokemon_name,
                    'it': pokemon_name,
                    'ja': pokemon_name,
                    'ko': pokemon_name,
                    'zh_hans': pokemon_name,
                    'zh_hant': pokemon_name
                },
                'prefix': prefix,  # Store prefix for rendering (e.g., "Rocket's")
                'suffix': suffix,  # Store suffix for rendering ("ex")
                'form_code': f"#{dex_id:03d}_EX1",
                'tcg_card': {
                    'id': card['id'],
                    'localId': card['localId'],
                    'set': card['set'],
                    'hp': card['hp']
                }
            }
            
            pokemon_list.append(pokemon_entry)
        
        variant_data = {
            'type': 'variant',
            'name': 'Pokémon EX - Generation 1',
            'sections': {
                'normal': {
                    'section_id': 'normal',
                    'color_hex': variant_meta.get('color', '#1F51BA'),
                    'title': variant_meta.get('title', {}),
                    'subtitle': variant_meta.get('subtitle', {}),
                    'suffix': '',  # Suffix is stored per Pokemon, not at section level
                    'subtitle': variant_meta.get('subtitle', {}),
                    'cards': pokemon_list
                }
            }
        }
        
        logger.info(f"Created variant with {len(pokemon_list)} Pokemon")
        
        return variant_data
