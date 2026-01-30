"""
Enrich Section Descriptions

Adds multilingual description text to each section based on its metadata.
For Pokedex sections: Adds Pokédex ID range
For Variant sections: Adds variant-specific information
"""

import logging
from pathlib import Path
from typing import Dict, Any
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from steps.base import BaseStep, PipelineContext

logger = logging.getLogger(__name__)


class EnrichSectionDescriptionsStep(BaseStep):
    """
    Enriches sections with multilingual descriptions.
    """
    
    def __init__(self, name: str):
        super().__init__(name)
    
    def execute(self, context: PipelineContext, params: Dict[str, Any]) -> PipelineContext:
        """
        Add description field to each section.
        
        Args:
            context: Pipeline context with data
            params: Step parameters (mode, variant_name, descriptions_file, target_file)
        
        Returns:
            Updated context with descriptions added
        """
        mode = params.get('mode', 'pokedex')  # 'pokedex' or 'variant'
        variant_name = params.get('variant_name')
        descriptions_file = params.get('descriptions_file')
        target_file = params.get('target_file')  # For loading data if not in context
        
        print(f"    🔖 Enriching section descriptions (mode: {mode})")
        print(f"       target_file param: {target_file}")
        
        data = context.get_data()
        print(f"       data in context: {data is not None}")
        print(f"       has sections: {'sections' in data if data else 'no data'}")
        
        # If no data or no sections in context, try to load from target_file parameter
        if target_file and (not data or 'sections' not in data or not data.get('sections')):
            import json
            # Make path absolute if relative
            if not Path(target_file).is_absolute():
                target_path = Path(__file__).parent.parent.parent.parent / target_file
            else:
                target_path = Path(target_file)
            
            if target_path.exists():
                print(f"       📁 Loading data from {target_file}")
                with open(target_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                context.set_data(data)
                print(f"       ✓ Loaded: has sections = {'sections' in data}")
        
        if not data:
            print("    ⚠️  No data found in context or file")
            return context
        
        # Check if we have sections
        if 'sections' not in data or not data['sections']:
            print("    ⚠️  No sections found - data might not be grouped yet")
            return context
        
        # Load variant descriptions if needed
        all_variant_descriptions = {}
        if mode == 'variant' and descriptions_file and variant_name:
            import json
            desc_path = Path(__file__).parent.parent.parent.parent / descriptions_file
            if desc_path.exists():
                with open(desc_path, 'r', encoding='utf-8') as f:
                    all_descriptions = json.load(f)
                    all_variant_descriptions = all_descriptions.get(variant_name, {})
                    print(f"       ✅ Loaded descriptions for {variant_name}")
            else:
                print(f"       ⚠️  Descriptions file not found: {desc_path}")
        
        enriched_count = 0
        
        for section_key, section in data['sections'].items():
            if mode == 'pokedex':
                # Generate Pokédex ID range description
                description = self._generate_pokedex_description(section)
            elif mode == 'variant':
                # Use section-specific description from loaded variant descriptions
                description = all_variant_descriptions.get(section_key, {})
            else:
                logger.warning(f"Unknown mode: {mode}")
                continue
            
            if description:
                section['description'] = description
                enriched_count += 1
                desc_preview = description.get('en', '')[:50] if isinstance(description, dict) else str(description)[:50]
                print(f"       ✓ {section_key}: {desc_preview}...")
        
        print(f"    ✅ Enriched {enriched_count} sections with descriptions")
        
        # Update context with enriched data (context-only, no file writing)
        context.set_data(data)
        
        return context
    
    def _generate_pokedex_description(self, section: Dict) -> Dict[str, str]:
        """Generate Pokédex ID range description."""
        range_data = section.get('range', [])
        if not range_data or len(range_data) != 2:
            return {}
        
        start_id, end_id = range_data
        
        # Multilingual templates
        templates = {
            'de': f"Pokédex #{start_id:03d} – #{end_id:03d}",
            'en': f"Pokédex #{start_id:03d} – #{end_id:03d}",
            'fr': f"Pokédex #{start_id:03d} – #{end_id:03d}",
            'es': f"Pokédex #{start_id:03d} – #{end_id:03d}",
            'it': f"Pokédex #{start_id:03d} – #{end_id:03d}",
            'ja': f"ポケモン図鑑 #{start_id:03d} – #{end_id:03d}",
            'ko': f"포켓몬 도감 #{start_id:03d} – #{end_id:03d}",
            'zh_hans': f"宝可梦图鉴 #{start_id:03d} – #{end_id:03d}",
            'zh_hant': f"寶可夢圖鑑 #{start_id:03d} – #{end_id:03d}",
        }
        
        return templates
