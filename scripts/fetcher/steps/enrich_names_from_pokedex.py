"""
Enrich Pokemon Names from Pokedex

Takes TCG card data (or other variant data) and enriches the Pokemon names
with translations from the National Pokedex.

This allows TCG cards (which only have English names from the API) to have
proper multilingual names for PDF generation.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List
import sys
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from steps.base import BaseStep, PipelineContext

logger = logging.getLogger(__name__)


class EnrichNamesFromPokedexStep(BaseStep):
    """
    Enriches Pokemon names in variant data with translations from Pokedex.
    
    Reads the National Pokedex and uses it as a lookup table to add
    multilingual names to Pokemon in the target data structure.
    
    Input: Variant JSON with Pokemon having only English names
    Output: Same structure but with full multilingual names
    """
    
    def execute(self, context: PipelineContext, params: Dict[str, Any]) -> PipelineContext:
        """
        Execute the enrichment.
        
        1. Load Pokedex.json
        2. Build a lookup table: dexId -> multilingual names
        3. Load target file
        4. For each Pokemon in target, enrich names from lookup
        5. Save enriched target file
        """
        # Make paths absolute relative to project root (2 levels up from this file)
        project_root = Path(__file__).parent.parent.parent.parent
        
        pokedex_path = params.get('pokedex_file', 'data/Pokedex.json')
        if not Path(pokedex_path).is_absolute():
            pokedex_file = project_root / pokedex_path
        else:
            pokedex_file = Path(pokedex_path)
        
        # Get target file path (optional - can work with context only)
        target_path = params.get('target_file')
        target_file = None
        
        if target_path:
            if not Path(target_path).is_absolute():
                target_file = project_root / target_path
            else:
                target_file = Path(target_path)
        
        logger.info(f"Enriching names from Pokedex: {pokedex_file}")
        
        # Step 1: Load Pokedex
        if not pokedex_file.exists():
            raise FileNotFoundError(f"Pokedex not found: {pokedex_file}")
        
        with open(pokedex_file, 'r', encoding='utf-8') as f:
            pokedex_data = json.load(f)
        
        # Step 2: Build lookup table
        name_lookup = self._build_name_lookup(pokedex_data)
        logger.info(f"Built lookup table for {len(name_lookup)} Pokemon")
        
        # Step 3: Load target data (from context or file)
        target_data = context.get_data()
        
        if not target_data:
            # Fallback: try to load from file if not in context
            if not target_file.exists():
                raise FileNotFoundError(f"Target file not found: {target_file}")
            
            with open(target_file, 'r', encoding='utf-8') as f:
                target_data = json.load(f)
        
        # Step 4: Enrich names
        enriched_count = 0
        sections = target_data.get('sections', {})
        
        for section_id, section_data in sections.items():
            pokemon_list = section_data.get('pokemon', [])
            
            for pokemon in pokemon_list:
                dex_id = pokemon.get('id')
                
                if dex_id and dex_id in name_lookup:
                    # Replace name with multilingual version
                    old_name = pokemon.get('name', {})
                    new_name = name_lookup[dex_id]
                    
                    # Keep the English name as fallback if it's different
                    # (e.g., "Rocket's Mewtwo" should keep that prefix)
                    if isinstance(old_name, dict):
                        english_old = old_name.get('en', '')
                    else:
                        english_old = str(old_name)
                    
                    # Check if it's a special variant name (has prefix/suffix)
                    english_new = new_name.get('en', '')
                    
                    if english_old and english_old != english_new:
                        # It's a variant name - extract the form suffix (X, Y, etc.)
                        # For example: "Charizard X" -> base="Charizard", suffix=" X"
                        form_suffix = ""
                        if english_old.startswith(english_new):
                            form_suffix = english_old[len(english_new):]
                        
                        # Apply form suffix to all languages
                        pokemon['name'] = {}
                        for lang, base_name in new_name.items():
                            pokemon['name'][lang] = base_name + form_suffix
                        
                        # Special case: Keep full English variant if it doesn't start with base
                        # (e.g., "Rocket's Mewtwo" or other special names)
                        if not english_old.startswith(english_new):
                            pokemon['name']['en'] = english_old
                        
                        pokemon['base_name'] = new_name  # Store base name separately
                    else:
                        # Standard Pokemon, use full translation
                        pokemon['name'] = new_name
                    
                    enriched_count += 1
                    logger.debug(f"Enriched #{dex_id:03d}: {pokemon['name'].get('en')}")
                else:
                    logger.warning(f"No name found for dexId {dex_id}")
        
        logger.info(f"✅ Enriched {enriched_count} Pokemon with multilingual names")
        
        # Update context with enriched data
        context.set_data(target_data)
        
        # Save to file if target_file is specified
        if target_file:
            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(target_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Saved enriched data to {target_file}")
        
        return context
    
    def _build_name_lookup(self, pokedex_data: Dict[str, Any]) -> Dict[int, Dict[str, str]]:
        """
        Build a lookup table from Pokedex data.
        
        Args:
            pokedex_data: Pokedex.json content
            
        Returns:
            Dictionary mapping dexId -> {language: name}
        """
        lookup = {}
        
        # Pokedex has sections (generations)
        sections = pokedex_data.get('sections', {})
        
        for section_id, section_data in sections.items():
            pokemon_list = section_data.get('pokemon', [])
            
            for pokemon in pokemon_list:
                dex_id = pokemon.get('id')
                name = pokemon.get('name')
                
                if dex_id and name:
                    # Store the multilingual name object
                    lookup[dex_id] = name
        
        return lookup
    
    def validate(self, context: PipelineContext, target_file: Path) -> bool:
        """Validate that enrichment succeeded."""
        if not target_file.exists():
            logger.error(f"Target file does not exist after enrichment: {target_file}")
            return False
        
        # Check that we enriched at least some Pokemon
        enriched_count = context.data.get('enriched_pokemon_count', 0) if context.data else 0
        
        if enriched_count == 0:
            logger.warning("No Pokemon were enriched")
            return False
        
        logger.info(f"✅ Validation passed: {enriched_count} Pokemon enriched")
        return True


if __name__ == '__main__':
    # For testing the step directly
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    step_config = {
        'pokedex_file': 'data/Pokedex.json',
        'target_file': 'data/ExGen1_Single.json'
    }
    
    step = EnrichNamesFromPokedexStep(step_config)
    context = PipelineContext(config={'source_file': None, 'target_file': None})
    
    try:
        context = step.execute(context)
        if step.validate(context):
            print("\n✅ Enrichment completed and validated successfully!")
        else:
            print("\n❌ Enrichment validation failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Enrichment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
