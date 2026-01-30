"""
Enrichment step: Enrich metadata.

This step reads the metadata.json file and makes generation and variant metadata
available in the context for other steps to use.
"""

import json
from pathlib import Path
from typing import Any, Dict
from .base import BaseStep, PipelineContext


class EnrichMetadataStep(BaseStep):
    """Load metadata from metadata.json and store in context."""
    
    def execute(self, context: PipelineContext, params: Dict[str, Any]) -> PipelineContext:
        """
        Execute the enrichment step.
        
        Args:
            context: Pipeline context
            params: Step parameters
                - metadata_file: Path to metadata.json
        
        Returns:
            Updated context with metadata in context storage
        """
        metadata_file = params.get('metadata_file')
        if not metadata_file:
            print(f"    ⚠️  No metadata_file parameter provided")
            return context
        
        metadata_path = Path(metadata_file)
        if not metadata_path.exists():
            print(f"    ⚠️  Metadata file not found: {metadata_file}")
            return context
        
        print(f"    📝 Loading metadata from: {metadata_file}")
        
        # Load metadata
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Store metadata in context for other steps to use
        context.storage['metadata'] = metadata
        
        generations_count = len(metadata.get('generations', {}))
        variants_count = len(metadata.get('variants', {}))
        
        print(f"    ✅ Loaded metadata: {generations_count} generations, {variants_count} variants")
        
        return context
