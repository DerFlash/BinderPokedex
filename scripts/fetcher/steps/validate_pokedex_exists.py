"""
Validate that Pokedex.json exists

This step ensures that the National Pokedex has been fetched before
processing scopes that depend on it (e.g., TCG cards that need Pokemon names).

If Pokedex.json doesn't exist, the pipeline is aborted with a helpful error message.
"""

import logging
from pathlib import Path
from typing import Dict, Any
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from steps.base import BaseStep, PipelineContext

logger = logging.getLogger(__name__)


class ValidatePokedexExistsStep(BaseStep):
    """
    Validates that Pokedex.json exists.
    
    This step is used as a dependency check for scopes that require
    Pokemon name translations or other data from the National Pokedex.
    """
    
    def __init__(self, name: str):
        """
        Initialize the step.
        """
        super().__init__(name)
        self.pokedex_file = None
    
    def execute(self, context: PipelineContext, params: Dict[str, Any]) -> PipelineContext:
        """
        Execute the validation.
        
        Checks if Pokedex.json exists. If not, raises an error with instructions.
        """
        pokedex_path = params.get('pokedex_file', 'data/output/Pokedex.json')
        
        # Make path absolute relative to project root (3 levels up from this file)
        if not Path(pokedex_path).is_absolute():
            project_root = Path(__file__).parent.parent.parent.parent
            self.pokedex_file = project_root / pokedex_path
        else:
            self.pokedex_file = Path(pokedex_path)
        
        logger.info(f"Validating Pokedex exists: {self.pokedex_file}")
        
        if not self.pokedex_file.exists():
            error_msg = f"""
❌ Pokedex not found: {self.pokedex_file}

This scope requires the National Pokedex to be fetched first.
The Pokedex provides Pokemon names and translations that are needed
for enriching TCG card data.

Please run the following command first:

    python scripts/fetcher/fetch.py --scope pokedex

This will fetch all Pokemon from PokeAPI and create {self.pokedex_file}

After that, you can run this scope again.
"""
            logger.error(error_msg)
            raise RuntimeError("Pokedex.json not found - please fetch it first")
        
        logger.info(f"✅ Pokedex exists: {self.pokedex_file}")
        
        # Store path in context for next steps
        if context.data is None:
            context.data = {}
        context.data['pokedex_file'] = str(self.pokedex_file)
        
        return context
    
    def validate(self, context: PipelineContext) -> bool:
        """Validate that the step executed successfully."""
        return self.pokedex_file.exists()


if __name__ == '__main__':
    # For testing the step directly
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    step_config = {
        'pokedex_file': 'data/output/Pokedex.json'
    }
    
    step = ValidatePokedexExistsStep(step_config)
    context = PipelineContext(config={'source_file': None, 'target_file': None})
    
    try:
        context = step.execute(context)
        if step.validate(context):
            print("\n✅ Validation passed!")
        else:
            print("\n❌ Validation failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        sys.exit(1)
