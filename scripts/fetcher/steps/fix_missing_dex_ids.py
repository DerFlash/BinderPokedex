"""
Fix Missing DexIDs

WORKAROUND for TCGdex API limitation:
The TCGdex API returns empty dexId[] arrays for certain card types:
- Trainer-owned Pokemon (e.g., "Erika's Oddish", "Team Rocket's Mewtwo")
- Mega Pokemon (e.g., "Mega Charizard Y", "Mega Dragonite")
- Regional forms (e.g., "Galarian Zigzagoon", "Alolan Raichu")
- Special forms (e.g., "Fan Rotom", "Wash Rotom")

This step fixes these missing dexIds by:
1. Extracting the base Pokemon name from the card name
2. Looking up the dexId in the Pokedex
3. Adding the dexId to the card data

NOTE: This is a TEMPORARY WORKAROUND. If TCGdex fixes their API to include
proper dexIds for these cards, this step can be removed from the pipeline.
The step will show a warning if no cards needed fixing, indicating the API
may have been fixed.
"""

import logging
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from steps.base import BaseStep, PipelineContext
from steps.dex_id_utils import extract_base_pokemon_name, identify_card_pattern

logger = logging.getLogger(__name__)


class FixMissingDexIdsStep(BaseStep):
    """Pipeline step to fix missing dexIds in TCG cards."""
    
    def execute(self, context: PipelineContext, params: Dict[str, Any]) -> PipelineContext:
        """
        Fix missing dexIds in TCG card data.
        
        Required params:
            - source_path: Path to TCG set source JSON (e.g., data/source/me02.5.json)
            - pokedex_path: Path to Pokedex JSON (e.g., data/output/Pokedex.json)
            
        Returns:
            Updated context with statistics
        """
        logger.info("🔧 Fixing missing dexIds in TCG cards (TCGdex API workaround)")
        
        source_path = params.get('source_path')
        pokedex_path = params.get('pokedex_path')
        
        # Load data
        source_file = Path(source_path)
        if not source_file.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        with open(source_file, 'r', encoding='utf-8') as f:
            source_data = json.load(f)
        
        # Load Pokedex for name lookup
        pokedex_lookup = self._load_pokedex_lookup(pokedex_path)
        
        if not pokedex_lookup:
            logger.warning("⚠️  Pokedex lookup is empty, cannot fix dexIds")
            context.metadata['fix_missing_dex_ids'] = {
                'status': 'skipped',
                'reason': 'Pokedex lookup failed'
            }
            return context
        
        # Process cards
        cards = source_data.get('cards', [])
        cards_processed = 0
        cards_fixed = 0
        fixes_by_pattern = {
            'trainer_owned': 0,
            'mega': 0,
            'regional': 0,
            'rotom': 0,
            'other': 0
        }
        
        logger.info(f"📋 Processing {len(cards)} cards")
        
        for card in cards:
            # Only process Pokemon cards with empty dexId
            if card.get('category') != 'Pokemon':
                continue
            
            dex_ids = card.get('dexId', [])
            if dex_ids:  # Card already has dexId
                continue
            
            cards_processed += 1
            card_name = card.get('name', '')
            
            # Try to extract base Pokemon name and find dexId
            base_name = extract_base_pokemon_name(card_name)
            if not base_name:
                continue
            
            # Look up in Pokedex
            dex_id = pokedex_lookup.get(base_name.lower())
            if dex_id:
                card['dexId'] = [dex_id]
                cards_fixed += 1
                
                # Track which pattern was fixed
                pattern = identify_card_pattern(card_name)
                fixes_by_pattern[pattern] += 1
                
                logger.info(f"✓ Fixed '{card_name}' -> #{dex_id} {base_name} ({pattern})")
        
        # Save fixed data
        with open(source_file, 'w', encoding='utf-8') as f:
            json.dump(source_data, f, indent=2, ensure_ascii=False)
        
        # Report results
        logger.info(f"✅ Fixed {cards_fixed}/{cards_processed} cards with missing dexIds")
        
        if cards_fixed > 0:
            logger.info("📊 Fixes by pattern:")
            for pattern, count in fixes_by_pattern.items():
                if count > 0:
                    logger.info(f"   - {pattern}: {count} cards")
        
        # Warning if no fixes needed (API may have been fixed)
        if cards_processed == 0:
            logger.warning("⚠️  No cards with missing dexIds found!")
            logger.warning("⚠️  The TCGdex API may have been fixed - consider removing this step from the pipeline.")
        
        # Update context
        context.metadata['fix_missing_dex_ids'] = {
            'status': 'success',
            'cards_processed': cards_processed,
            'cards_fixed': cards_fixed,
            'fixes_by_pattern': fixes_by_pattern,
            'saved_to': str(source_file)
        }
        
        return context
    
    def _load_pokedex_lookup(self, pokedex_path: str) -> Dict[str, int]:
        """
        Load Pokedex and create name -> dexId lookup.
        
        Args:
            pokedex_path: Path to Pokedex.json
            
        Returns:
            Dict mapping lowercase English name to dexId
        """
        try:
            with open(pokedex_path, 'r', encoding='utf-8') as f:
                pokedex = json.load(f)
            
            lookup = {}
            
            # Pokedex format: sections is a dict {gen1: {...}, gen2: {...}, ...}
            sections = pokedex.get('sections', {})
            
            if isinstance(sections, dict):
                # Iterate over each generation section
                for section_key, section_data in sections.items():
                    # Try both 'pokemon' and 'cards' keys for compatibility
                    pokemon_list = section_data.get('cards', section_data.get('pokemon', []))
                    
                    for pokemon in pokemon_list:
                        if not isinstance(pokemon, dict):
                            continue
                        
                        dex_id = pokemon.get('pokemon_id')
                        # Try both 'names' and 'name' for English name
                        names_dict = pokemon.get('names') or pokemon.get('name', {})
                        en_name = names_dict.get('en', '') if isinstance(names_dict, dict) else ''
                        
                        if dex_id and en_name:
                            lookup[en_name.lower()] = dex_id
            
            logger.info(f"📚 Loaded {len(lookup)} Pokemon from Pokedex for name lookup")
            return lookup
            
        except Exception as e:
            logger.error(f"❌ Failed to load Pokedex: {e}")
            import traceback
            traceback.print_exc()
            return {}

