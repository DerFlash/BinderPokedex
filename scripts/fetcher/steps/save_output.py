"""
Save pipeline output to file.

This is a final step that saves the context data to the target file.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict
from .base import BaseStep, PipelineContext

logger = logging.getLogger(__name__)


class SaveOutputStep(BaseStep):
    """Save context data to output file."""
    
    def execute(self, context: PipelineContext, params: Dict[str, Any]) -> PipelineContext:
        """
        Execute the save step.
        
        Args:
            context: Pipeline context with data to save
            params: Step parameters with 'output_file'
        
        Returns:
            Updated context (unchanged)
        """
        output_file = params.get('output_file')
        if not output_file:
            logger.warning("No output_file specified, skipping save")
            return context
        
        # Get data from context
        data = context.get_data()
        if not data:
            logger.warning("No data in context to save")
            return context
        
        # Make path absolute relative to project root
        project_root = Path(__file__).parent.parent.parent.parent
        if not Path(output_file).is_absolute():
            output_path = project_root / output_file
        else:
            output_path = Path(output_file)
        
        # Create parent directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"    💾 Saved output to: {output_file}")
        logger.info(f"Saved pipeline output to {output_file}")
        
        return context
