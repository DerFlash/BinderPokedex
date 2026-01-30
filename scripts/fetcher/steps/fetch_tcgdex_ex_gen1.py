"""
Fetch Classic ex Cards from TCGdex API

Fetches Classic ex cards (lowercase "ex") from the EX series (2003-2007)
from TCGdex API and stores them in source format.

The EX series includes sets like:
- Ruby & Sapphire (ex1)
- FireRed & LeafGreen (ex6)
- Emerald (ex9)
- And 15 more sets from 2003-2007

Classic ex cards are identified by:
- Card name ending with " ex" (lowercase)
- From sets in the "ex" series (series_id: "ex")
- Have National Pokedex numbers (dexId field)
"""

import logging
from pathlib import Path
from typing import List, Dict, Any
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from steps.base import BaseStep, PipelineContext
from lib.tcgdex_client import TCGdexClient

logger = logging.getLogger(__name__)


class FetchTCGdexClassicExStep(BaseStep):
    """
    Fetches Classic ex cards from TCGdex API (EX series 2003-2007).
    
    Output format (source):
    {
        "cards": [
            {
                "id": "ex1-100",
                "localId": "100",
                "name": "Magmar ex",
                "dexId": [126],
                "hp": 90,
                "types": ["Fire"],
                "image": "https://assets.tcgdex.net/en/ex/ex1/100",
                "category": "Pokemon",
                "set": {
                    "id": "ex1",
                    "name": "Ruby & Sapphire",
                    "serie": "ex"
                }
            },
            ...
        ],
        "metadata": {
            "total_cards": 103,
            "series": "ex",
            "date_fetched": "2026-01-24T12:00:00Z",
            "source": "TCGdex API v2"
        }
    }
    """
    
    def execute(self, context: PipelineContext, params: Dict[str, Any]) -> PipelineContext:
        """
        Execute the fetch step.
        
        1. Initialize TCGdex client
        2. Get all sets from EX series
        3. For each set, fetch all cards ending with " ex"
        4. Filter for Pokemon cards with dexId
        5. Store in source format
        """
        language = params.get('language', 'en')
        
        # Make path absolute relative to project root (4 levels up from this file)
        project_root = Path(__file__).parent.parent.parent.parent
        output_path = params.get('output_file', 'data/source/tcg_classic_ex.json')
        
        if not Path(output_path).is_absolute():
            output_file = project_root / output_path
        else:
            output_file = Path(output_path)
        
        logger.info(f"Starting Classic ex cards fetch (language: {language})")
        
        client = TCGdexClient(language=language)
        
        # Step 1: Get EX series info
        logger.info("Fetching EX series information...")
        ex_series = client.get_serie('ex')
        
        if not ex_series:
            raise RuntimeError("Failed to fetch EX series from TCGdex API")
        
        sets = ex_series.get('sets', [])
        logger.info(f"Found {len(sets)} sets in EX series")
        
        # Step 2: Fetch ex cards from all sets
        all_ex_cards = []
        
        for set_info in sets:
            set_id = set_info['id']
            set_name = set_info['name']
            
            logger.info(f"Processing set: {set_name} ({set_id})...")
            
            # Get full set with cards
            full_set = client.get_set(set_id)
            
            if not full_set:
                logger.warning(f"Failed to fetch set {set_id}, skipping")
                continue
            
            cards = full_set.get('cards', [])
            
            # Filter for ex cards (cards ending with " ex")
            ex_cards_in_set = [
                card for card in cards 
                if card.get('name', '').endswith(' ex')
            ]
            
            logger.info(f"  Found {len(ex_cards_in_set)} ex cards in {set_name}")
            
            # Step 3: Fetch full details for each ex card
            for card_brief in ex_cards_in_set:
                card_id = card_brief['id']
                
                # Get full card details
                full_card = client.get_card(card_id)
                
                if not full_card:
                    logger.warning(f"Failed to fetch card {card_id}, skipping")
                    continue
                
                # Check if it's a Pokemon card with dexId
                if full_card.get('category') != 'Pokemon':
                    continue
                
                dex_ids = full_card.get('dexId', [])
                if not dex_ids:
                    logger.warning(f"Card {card_id} ({full_card.get('name')}) has no dexId, skipping")
                    continue
                
                # Extract relevant fields
                card_data = {
                    'id': full_card['id'],
                    'localId': full_card.get('localId'),
                    'name': full_card.get('name'),
                    'dexId': dex_ids,
                    'hp': full_card.get('hp'),
                    'types': full_card.get('types', []),
                    'image': full_card.get('image'),
                    'category': full_card.get('category'),
                    'set': {
                        'id': full_card.get('set', {}).get('id'),
                        'name': full_card.get('set', {}).get('name'),
                        'serie': 'ex'  # We know it's from EX series
                    }
                }
                
                all_ex_cards.append(card_data)
                logger.debug(f"  Added: {card_data['name']} (#{dex_ids[0]:03d})")
        
        # Step 4: Sort by first dexId, then by card name
        all_ex_cards.sort(key=lambda c: (c['dexId'][0], c['name']))
        
        logger.info(f"Total Classic ex cards fetched: {len(all_ex_cards)}")
        
        # Step 5: Store in source format
        from datetime import datetime
        import json
        
        output_data = {
            'cards': all_ex_cards,
            'metadata': {
                'total_cards': len(all_ex_cards),
                'series': 'ex',
                'series_name': 'Classic EX (2003-2007)',
                'date_fetched': datetime.now().isoformat(),
                'source': 'TCGdex API v2',
                'language': language,
                'sets_processed': len(sets)
            }
        }
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Saved {len(all_ex_cards)} Classic ex cards to {output_file}")
        
        # Store in context for next steps
        if context.data is None:
            context.data = {}
        context.data['tcg_classic_ex_cards'] = all_ex_cards
        context.data['tcg_classic_ex_metadata'] = output_data['metadata']
        
        return context
    
    def validate(self, context: PipelineContext, output_file: Path) -> bool:
        """
        Validate the step execution.
        
        Checks:
        - Output file exists
        - Has cards array
        - Has metadata
        - Cards have required fields
        """
        if not output_file.exists():
            logger.error(f"Output file does not exist: {output_file}")
            return False
        
        import json
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'cards' not in data:
            logger.error("Output data missing 'cards' field")
            return False
        
        if 'metadata' not in data:
            logger.error("Output data missing 'metadata' field")
            return False
        
        cards = data['cards']
        if not cards:
            logger.error("No cards in output data")
            return False
        
        # Check first card has required fields
        first_card = cards[0]
        required_fields = ['id', 'name', 'dexId', 'set']
        for field in required_fields:
            if field not in first_card:
                logger.error(f"Card missing required field: {field}")
                return False
        
        logger.info(f"✅ Validation passed: {len(cards)} cards")
        return True


if __name__ == '__main__':
    # For testing the step directly
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    step_config = {
        'language': 'en',
        'output_file': 'data/source/tcg_classic_ex.json'
    }
    
    step = FetchTCGdexClassicExStep(step_config)
    context = PipelineContext(config={'source_file': None, 'target_file': None})
    
    try:
        context = step.execute(context)
        if step.validate(context):
            print("\n✅ Step executed and validated successfully!")
        else:
            print("\n❌ Step validation failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Step failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
