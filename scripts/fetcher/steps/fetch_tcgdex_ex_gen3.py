"""
Fetch Pokémon-ex cards from TCGdex Scarlet & Violet series.

This step fetches all Pokémon-ex cards (lowercase logo) from the
Scarlet & Violet era TCG sets via the TCGdex API.
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


class FetchTCGdexScarletVioletEXStep(BaseStep):
    """Fetch Scarlet & Violet ex series cards from TCGdex API."""
    
    # Scarlet & Violet sets (all contain ex cards)
    SV_SETS = [
        'sv01',    # Scarlet & Violet
        'sv02',    # Paldea Evolved
        'sv03',    # Obsidian Flames
        'sv03.5',  # 151
        'sv04',    # Paradox Rift
        'sv04.5',  # Paldean Fates
        'sv05',    # Temporal Forces
        'sv06',    # Twilight Masquerade
        'sv06.5',  # Shrouded Fable
        'sv07',    # Stellar Crown
        'sv08',    # Surging Sparks
        'sv08.5',  # Blooming Waters
        'sv09',    # Journey Together
        'sv10',    # Prismatic Evolutions
    ]
    
    # Mega Evolution sets (2025+)
    ME_SETS = [
        'me01',    # Mega Evolution
        'me02',    # Phantasmal Flames
        'me03',    # Ascending Heroes
        'mep',     # MEP Black Star Promos
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
        
        all_sets = self.SV_SETS + self.ME_SETS
        
        print(f"    🔍 Fetching Scarlet & Violet ex cards from TCGdex")
        print(f"    📊 Language: {language}")
        print(f"    📦 Sets to fetch: {len(all_sets)} (SV: {len(self.SV_SETS)}, ME: {len(self.ME_SETS)})")
        
        client = TCGdexClient(language=language)
        
        all_ex_cards = []
        
        for set_id in all_sets:
            print(f"       Fetching set: {set_id}...")
            
            set_data = client.get_set(set_id)
            if not set_data:
                logger.warning(f"Could not fetch set {set_id}")
                continue
            
            # Filter for ex cards and get full details
            cards = set_data.get('cards', [])
            
            for card_brief in cards:
                name = card_brief.get('name', '')
                # Match " ex" suffix (with space, lowercase)
                if not name.endswith(' ex'):
                    continue
                
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
            
            print(f"          Found {len([c for c in cards if c.get('name', '').endswith(' ex')])} ex cards")
        
        print(f"    ✅ Fetched total: {len(all_ex_cards)} ex cards")
        
        # Save to output file if specified
        if output_file:
            project_root = Path(__file__).parent.parent.parent.parent
            if not Path(output_file).is_absolute():
                output_path = project_root / output_file
            else:
                output_path = Path(output_file)
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({'cards': all_ex_cards}, f, indent=2, ensure_ascii=False)
            
            print(f"    💾 Saved to: {output_file}")
        
        # Store cards in context for next steps
        context.storage['tcg_cards'] = all_ex_cards
        
        return context
