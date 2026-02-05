"""
Load EX cards data from local file.

This step loads previously fetched EX cards data from the source directory.
Used in --skip-fetch mode to load cached EX cards data.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict
from .base import BaseStep, PipelineContext

logger = logging.getLogger(__name__)


class LoadExCardsStep(BaseStep):
    """Load EX cards data from local file."""
    
    def execute(self, context: PipelineContext, params: Dict[str, Any]) -> PipelineContext:
        """
        Load EX cards data from file and store in context.
        
        Args:
            context: Pipeline context
            params: Step parameters with 'source_file' and 'context_key'
        
        Returns:
            Updated context with loaded EX cards data
        """
        source_file = params.get('source_file')
        context_key = params.get('context_key')
        
        if not source_file:
            logger.error("No source_file parameter provided")
            return context
        
        if not context_key:
            logger.error("No context_key parameter provided")
            return context
        
        # Make path absolute relative to project root
        project_root = Path(__file__).parent.parent.parent.parent
        source_path = project_root / source_file if not Path(source_file).is_absolute() else Path(source_file)
        
        if not source_path.exists():
            logger.warning(f"EX cards source file not found: {source_file}")
            print(f"    ⚠️  EX cards source file not found: {source_file}")
            return context
        
        # Load EX cards data
        with open(source_path, 'r', encoding='utf-8') as f:
            ex_data = json.load(f)
        
        # Extract cards array if data is a dict with 'cards' key
        if isinstance(ex_data, dict) and 'cards' in ex_data:
            cards = ex_data['cards']
        elif isinstance(ex_data, list):
            cards = ex_data
        else:
            logger.error(f"Unexpected data format in {source_file}")
            print(f"    ⚠️  Unexpected data format in {source_file}")
            return context
        
        # Store in context under specified key
        current_data = context.get_data() or {}
        current_data[context_key] = cards
        context.set_data(current_data)
        
        cards_count = len(cards)
        
        print(f"    📦 Loaded {cards_count} EX cards into context['{context_key}']")
        logger.info(f"Loaded {cards_count} EX cards from {source_file} into {context_key}")
        
        return context
