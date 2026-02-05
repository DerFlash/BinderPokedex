"""
Load TCG set data from local file.

This step loads previously fetched TCG set data from the source directory.
Used in --skip-fetch mode to load cached TCG set data.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict
from .base import BaseStep, PipelineContext

logger = logging.getLogger(__name__)


class LoadTCGSetStep(BaseStep):
    """Load TCG set data from local file."""
    
    def execute(self, context: PipelineContext, params: Dict[str, Any]) -> PipelineContext:
        """
        Load TCG set data from file and store in context.
        
        Args:
            context: Pipeline context
            params: Step parameters with 'source_file'
        
        Returns:
            Updated context with loaded TCG set data
        """
        source_file = params.get('source_file')
        if not source_file:
            logger.error("No source_file parameter provided")
            return context
        
        # Make path absolute relative to project root
        project_root = Path(__file__).parent.parent.parent.parent
        source_path = project_root / source_file if not Path(source_file).is_absolute() else Path(source_file)
        
        if not source_path.exists():
            logger.warning(f"TCG set source file not found: {source_file}")
            print(f"    ⚠️  TCG set source file not found: {source_file}")
            return context
        
        # Load TCG set data
        with open(source_path, 'r', encoding='utf-8') as f:
            tcg_data = json.load(f)
        
        # Store in context under 'tcg_set_source' key (expected by enrich steps)
        current_data = context.get_data() or {}
        current_data['tcg_set_source'] = tcg_data
        context.set_data(current_data)
        
        set_info = tcg_data.get('set_info', {})
        cards_count = len(tcg_data.get('cards', []))
        set_name = set_info.get('name', 'Unknown')
        set_id = set_info.get('id', 'unknown')
        
        print(f"    📦 Loaded TCG set '{set_name}' ({set_id}) with {cards_count} cards")
        logger.info(f"Loaded TCG set {set_id} with {cards_count} cards from {source_file}")
        
        return context
