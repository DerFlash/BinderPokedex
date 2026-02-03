"""
Transform step: Group Pokemon by generation.

Transforms the source data (flat list of Pokemon) into the target format
with generation sections matching the PDF generator's expected structure.
"""

from datetime import datetime
from typing import Any, Dict, List
from pathlib import Path
import json
from .base import BaseStep, PipelineContext


# Generation metadata (English names and regions only, translations loaded separately)
class GroupByGenerationStep(BaseStep):
    """Transform flat Pokemon list into generation-grouped structure."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.translations = self._load_translations()
    
    def _load_translations(self) -> Dict:
        """Load translations from i18n/translations.json."""
        translations_path = Path(__file__).parent.parent.parent.parent / 'i18n' / 'translations.json'
        if translations_path.exists():
            with open(translations_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _convert_metadata_format(self, metadata_generations: Dict) -> Dict:
        """Convert gen1-gen9 keys to numeric 1-9 and range lists to tuples."""
        generations = {}
        for gen_key, gen_data in metadata_generations.items():
            gen_num = int(gen_key.replace('gen', ''))
            generations[gen_num] = {
                'name': gen_data['name'],
                'region': gen_data['region'],
                'range': tuple(gen_data['range']),
                'color': gen_data['color']
            }
        return generations
    
    def execute(self, context: PipelineContext, params: Dict[str, Any]) -> PipelineContext:
        """
        Execute the grouping step.
        
        Args:
            context: Pipeline context with source data
            params: Step parameters (unused)
        
        Returns:
            Updated context with grouped data
        """
        print(f"    🔄 Grouping Pokemon by generation")
        
        source_data = context.get_data()
        if not source_data or 'pokemon' not in source_data:
            print(f"    ⚠️  No source data found in context")
            return context
        
        pokemon_list = source_data['pokemon']
        print(f"    📊 Processing {len(pokemon_list)} Pokemon")
        
        # Group by generation
        generations = {}
        for pokemon in pokemon_list:
            gen = pokemon['generation']
            if gen not in generations:
                generations[gen] = []
            
            # Transform to target format
            # Source has types as list, target has type1/type2
            types = pokemon.get('types', [])
            type1 = types[0].capitalize() if len(types) > 0 else None
            type2 = types[1].capitalize() if len(types) > 1 else None
            
            # Transform names from list to dict by language code
            names_dict = {}
            for name_entry in pokemon.get('names', []):
                lang_code = name_entry['language']['name']
                # Map PokeAPI language codes to target format (case-insensitive)
                lang_map = {
                    'en': 'en',
                    'de': 'de',
                    'fr': 'fr',
                    'es': 'es',
                    'it': 'it',
                    'ja': 'ja',
                    'ko': 'ko',
                    'zh-hans': 'zh_hans',
                    'zh-hant': 'zh_hant',
                }
                # Normalize to lowercase for matching
                lang_code_lower = lang_code.lower()
                if lang_code_lower in lang_map:
                    names_dict[lang_map[lang_code_lower]] = name_entry['name']
            
            # Build types array (filter out None)
            types = [t for t in [type1, type2] if t is not None]
            
            # Build target Pokemon entry
            target_entry = {
                'pokemon_id': pokemon['id'],
                'num': f"#{pokemon['id']:03d}",
                'types': types,
                'image_url': pokemon.get('image_url'),
                'generation': gen,
                'name': names_dict,
            }
            
            generations[gen].append(target_entry)
        
        # Build target structure with sections
        sections = {}
        total_count = 0
        
        # Get generation metadata from context
        metadata = context.storage.get('metadata', {})
        metadata_generations = metadata.get('generations', {})
        generation_info = self._convert_metadata_format(metadata_generations)
        
        for gen_num in sorted(generations.keys()):
            pokemon_in_gen = generations[gen_num]
            gen_info = generation_info.get(gen_num, {
                'name': f'Generation {gen_num}',
                'region': 'Unknown',
                'range': (0, 0),
                'color': '#999999'
            })
            
            # Build multilingual title (Generation + roman numeral)
            title_dict = {}
            for lang in ['de', 'en', 'fr', 'es', 'it', 'ja', 'ko', 'zh_hans', 'zh_hant']:
                gen_key = f'generation_{gen_num}'
                title_dict[lang] = self.translations.get(lang, {}).get(gen_key, gen_info['name'])
            
            # Build multilingual subtitle (region name)
            subtitle_dict = {}
            for lang in ['de', 'en', 'fr', 'es', 'it', 'ja', 'ko', 'zh_hans', 'zh_hant']:
                region_key = gen_info['region'].lower()
                subtitle_dict[lang] = self.translations.get(lang, {}).get(region_key, gen_info['region'])
            
            sections[f'gen{gen_num}'] = {
                'section_id': f'gen{gen_num}',
                'id': gen_num,
                'name': gen_info['name'],
                'region': gen_info['region'],
                'title': title_dict,
                'subtitle': subtitle_dict,
                'color_hex': gen_info['color'],
                'pokemon_count': len(pokemon_in_gen),
                'range': list(gen_info['range']),
                'featured_pokemon': [],  # Will be filled by preserve_featured_pokemon step
                'cards': pokemon_in_gen,
            }
            total_count += len(pokemon_in_gen)
        
        # Build final target structure (no root-level description)
        target_data = {
            'version': '2.0',
            'consolidated_date': datetime.now().strftime('%Y-%m-%d'),
            'total_generations': len(sections),
            'sections': sections,
        }
        
        print(f"    ✅ Grouped into {len(sections)} generations")
        for gen_key in sorted(sections.keys()):
            gen_data = sections[gen_key]
            print(f"       {gen_key}: {gen_data['pokemon_count']} Pokemon")
        
        # Update context
        context.set_data(target_data)
        context.set_metadata('grouped', True)
        
        return context
