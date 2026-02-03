"""
Load source data from local file.

This step loads previously fetched data from the source directory.
Used in --skip-fetch mode to load cached source data.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict
from .base import BaseStep, PipelineContext

logger = logging.getLogger(__name__)


class LoadLocalSourceStep(BaseStep):
    """Load source data from local file."""
    
    def execute(self, context: PipelineContext, params: Dict[str, Any]) -> PipelineContext:
        """
        Load source data from file.
        
        Args:
            context: Pipeline context
            params: Step parameters with 'source_file'
        
        Returns:
            Updated context with loaded data
        """
        source_file = params.get('source_file', 'data/source/pokedex.json')
        
        # Make path absolute relative to project root
        project_root = Path(__file__).parent.parent.parent.parent
        if not Path(source_file).is_absolute():
            source_path = project_root / source_file
        else:
            source_path = Path(source_file)
        
        if not source_path.exists():
            logger.warning(f"Source file not found: {source_file}")
            print(f"    ⚠️  Source file not found: {source_file}")
            return context
        
        # Load source data
        with open(source_path, 'r', encoding='utf-8') as f:
            source_data = json.load(f)
        
        # Set in context
        context.set_data(source_data)
        
        pokemon_count = len(source_data.get('pokemon', []))
        print(f"    📂 Loaded {pokemon_count} Pokemon from: {source_file}")
        logger.info(f"Loaded {pokemon_count} Pokemon from {source_file}")
        
        return context
