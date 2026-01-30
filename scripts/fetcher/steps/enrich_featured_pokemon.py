"""
Enrichment step: Enrich featured Pokemon.

This step reads the featured_pokemon.json file and adds the featured_pokemon
list to each generation section in the target data.
"""

import json
from pathlib import Path
from typing import Any, Dict
from .base import BaseStep, PipelineContext


class EnrichFeaturedPokemonStep(BaseStep):
    """Add featured Pokemon IDs to generation sections or variant sections."""
    
    def execute(self, context: PipelineContext, params: Dict[str, Any]) -> PipelineContext:
        """
        Execute the enrichment step.
        
        Args:
            context: Pipeline context with target data
            params: Step parameters
                - featured_file: Path to featured_pokemon.json
                - mode: 'generation' (default) or 'variant'
                - variant_name: Required if mode='variant' (e.g., 'ExGen1_All')
        
        Returns:
            Updated context with featured Pokemon added
        """
        featured_file = params.get('featured_file')
        if not featured_file:
            print(f"    ⚠️  No featured_file parameter provided")
            return context
        
        featured_path = Path(featured_file)
        if not featured_path.exists():
            print(f"    ⚠️  Featured Pokemon file not found: {featured_file}")
            return context
        
        mode = params.get('mode', 'generation')
        
        print(f"    📝 Loading featured Pokemon from: {featured_file} (mode: {mode})")
        
        # Load featured Pokemon
        with open(featured_path, 'r', encoding='utf-8') as f:
            featured_data = json.load(f)
        
        # Get target data
        target_data = context.get_data()
        if not target_data or 'sections' not in target_data:
            print(f"    ⚠️  No sections found in target data")
            return context
        
        sections = target_data['sections']
        total_featured = 0
        
        if mode == 'variant':
            # Variant mode: lookup by variant_name and section_id
            variant_name = params.get('variant_name')
            if not variant_name:
                print(f"    ⚠️  variant_name parameter required for mode='variant'")
                return context
            
            featured_by_variant = featured_data.get('featured_by_variant', {})
            variant_featured = featured_by_variant.get(variant_name, {})
            
            for section_id, section_data in sections.items():
                featured_ids = variant_featured.get(section_id, [])
                section_data['featured_pokemon'] = featured_ids
                
                if featured_ids:
                    total_featured += len(featured_ids)
                    print(f"       {section_id}: {len(featured_ids)} featured Pokemon")
            
            print(f"    ✅ Added {total_featured} featured Pokemon to variant {variant_name}")
        
        else:
            # Generation mode: lookup by generation key (gen1, gen2, etc.)
            featured_by_gen = featured_data.get('featured_by_generation', {})
            
            for gen_key, gen_data in sections.items():
                featured_ids = featured_by_gen.get(gen_key, [])
                gen_data['featured_pokemon'] = featured_ids
                
                if featured_ids:
                    total_featured += len(featured_ids)
                    print(f"       {gen_key}: {len(featured_ids)} featured Pokemon")
            
            print(f"    ✅ Added {total_featured} featured Pokemon across {len(sections)} generations")
        
        # Update context
        context.set_data(target_data)
        context.set_metadata('featured_added', True)
        context.set_metadata('total_featured', total_featured)
        
        return context
