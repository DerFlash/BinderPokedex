"""
Fetch Pokémon-EX cards from TCGdex Black & White and XY series.

This step fetches all Pokémon-EX cards (ALL-CAPS logo) from the
Black & White (BW4-BW11) and XY (XY1-XY12) series via the TCGdex API.

The Pokemon-EX format was introduced in Next Destinies (BW4) and
continued through the entire XY series until Sun & Moon.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))
from tcgdex_client import TCGdexClient

from .base import BaseStep, PipelineContext

logger = logging.getLogger(__name__)


class FetchTCGdexBlackWhiteEXStep(BaseStep):
    """Fetch Pokemon-EX cards from TCGdex API (BW & XY series)."""
    
    # Black & White and XY sets that contain EX cards
    # BW series (2012-2013)
    BW_SETS = [
        'bw4',   # Next Destinies (first EX cards)
        'bw5',   # Dark Explorers
        'bw6',   # Dragons Exalted
        'bw7',   # Boundaries Crossed
        'bw8',   # Plasma Storm
        'bw9',   # Plasma Freeze
        'bw10',  # Plasma Blast
        'bw11',  # Legendary Treasures
    ]
    
    # XY series (2014-2016) - Pokemon-EX continued
    XY_SETS = [
        'xy1',   # XY
        'xy2',   # Flashfire
        'xy3',   # Furious Fists
        'xy4',   # Phantom Forces
        'xy5',   # Primal Clash
        'xy6',   # Roaring Skies
        'xy7',   # Ancient Origins
        'xy8',   # BREAKthrough
        'xy9',   # BREAKpoint
        'xy10',  # Fates Collide
        'xy11',  # Steam Siege
        'xy12',  # Evolutions
    ]
    
    def execute(self, context: PipelineContext, params: Dict[str, Any]) -> PipelineContext:
        """
        Execute the fetch step.
        
        Args:
            context: Pipeline context
            params: Step parameters
                - language: Language code (default: en)
                - output_file: Optional path to save raw data
        
        Returns:
            Updated context with fetched cards
        """
        language = params.get('language', 'en')
        output_file = params.get('output_file')
        
        all_sets = self.BW_SETS + self.XY_SETS
        
        print(f"    🔍 Fetching Pokemon-EX cards from TCGdex (BW & XY series)")
        print(f"    📊 Language: {language}")
        print(f"    📦 Sets to fetch: {len(all_sets)} ({len(self.BW_SETS)} BW + {len(self.XY_SETS)} XY)")
        
        client = TCGdexClient(language=language)
        
        all_ex_cards = []
        
        for set_id in all_sets:
            print(f"       Fetching set: {set_id}...")
            
            set_data = client.get_set(set_id)
            if not set_data:
                logger.warning(f"Could not fetch set {set_id}")
                continue
            
            # Filter for EX cards and get full details
            cards = set_data.get('cards', [])
            ex_count = 0
            
            for card_brief in cards:
                name = card_brief.get('name', '')
                # Check for both "-EX" (BW format) and " EX" (XY format)
                # Also check for "M " prefix for Mega Evolution EX cards
                is_ex_card = ('-EX' in name or ' EX' in name)
                
                if not is_ex_card:
                    continue
                
                ex_count += 1
                
                # Get full card details to retrieve dexId
                card_id = card_brief.get('id')
                full_card = client.get_card(card_id)
                
                if not full_card:
                    logger.warning(f"Failed to fetch card {card_id}")
                    continue
                
                # Check if it's a Pokemon card with dexId
                if full_card.get('category') != 'Pokemon':
                    continue
                
                dex_ids = full_card.get('dexId', [])
                if not dex_ids:
                    logger.warning(f"Card {name} has no dexId, skipping")
                    continue
                
                all_ex_cards.append(full_card)
            
            if ex_count > 0:
                print(f"          Found {ex_count} EX cards")
        
        print(f"    ✅ Fetched total: {len(all_ex_cards)} EX cards from {len(all_sets)} sets")
        
        # Save to output file if specified
        if output_file:
            project_root = Path(__file__).parent.parent.parent.parent
            if not Path(output_file).is_absolute():
                output_path = project_root / output_file
            else:
                output_path = Path(output_file)
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            from datetime import datetime
            
            output_data = {
                'cards': all_ex_cards,
                'metadata': {
                    'total_cards': len(all_ex_cards),
                    'series': 'BW & XY',
                    'series_name': 'Pokemon-EX (BW4-BW11, XY1-XY12)',
                    'date_fetched': datetime.now().isoformat(),
                    'source': 'TCGdex API v2',
                    'language': language,
                    'sets_processed': len(all_sets)
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            print(f"    💾 Saved to: {output_file}")
        
        # Store cards in context for next steps
        context.storage['tcg_cards'] = all_ex_cards
        
        return context
