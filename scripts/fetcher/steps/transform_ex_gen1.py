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
        
        1. Load source data
        2. Group by Pokemon (dexId)
        3. Select one card per Pokemon (priority rules)
        4. Fetch Pokemon names from PokeAPI context or use card names
        5. Transform to variant format
        6. Save to output file
        """
        # Make paths absolute relative to project root (4 levels up from this file)
        project_root = Path(__file__).parent.parent.parent.parent
        
        source_path = params.get('source_file', 'data/source/tcg_classic_ex.json')
        if not Path(source_path).is_absolute():
            source_file = project_root / source_path
        else:
            source_file = Path(source_path)
        
        output_path = params.get('output_file', 'data/ExGen1.json')
        if not Path(output_path).is_absolute():
            output_file = project_root / output_path
        else:
            output_file = Path(output_path)
        
        logger.info(f"Starting Classic ex cards transformation (single card per Pokemon)")
        
        # Load source data
        if not source_file.exists():
            raise FileNotFoundError(f"Source file not found: {source_file}")
        
        with open(source_file, 'r', encoding='utf-8') as f:
            source_data = json.load(f)
        
        cards = source_data['cards']
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
        
        # Save to output file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(variant_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Saved variant to {output_file}")
        
        # Store in context for subsequent enrichment steps
        context.set_data(variant_data)
        
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
                'id': dex_id,
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
        
        # Featured Pokemon will be added by enrich_featured_pokemon step
        featured = []
        
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
                    'featured_pokemon': featured,
                    'pokemon': pokemon_list
                }
            }
        }
        
        logger.info(f"Created variant with {len(pokemon_list)} Pokemon, featured: {featured}")
        
        return variant_data
    
    def validate(self, context: PipelineContext) -> bool:
        """Validate the transformation."""
        if not self.output_file.exists():
            logger.error(f"Output file does not exist: {self.output_file}")
            return False
        
        with open(self.output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'sections' not in data or 'normal' not in data['sections']:
            logger.error("Invalid variant structure")
            return False
        
        pokemon = data['sections']['normal']['pokemon']
        
        # Check for duplicates
        dex_ids = [p['id'] for p in pokemon]
        if len(dex_ids) != len(set(dex_ids)):
            logger.error("Duplicate Pokemon found in variant")
            return False
        
        logger.info(f"✅ Validation passed: {len(pokemon)} unique Pokemon")
        return True


if __name__ == '__main__':
    # For testing the step directly
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    step_config = {
        'source_file': 'data/source/tcg_classic_ex.json',
        'output_file': 'data/ExGen1.json'
    }
    
    step = TransformClassicExStep(step_config)
    context = PipelineContext(config={'source_file': None, 'target_file': None})
    
    try:
        context = step.execute(context)
        if step.validate(context):
            print("\n✅ Transformation completed and validated successfully!")
        else:
            print("\n❌ Transformation validation failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Transformation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
