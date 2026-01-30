"""
Enrichment step: Enrich ES/IT translations.

This step reads the translation enrichment files for Spanish and Italian
and updates the Pokemon names with better translations where available.
"""

import json
from pathlib import Path
from typing import Any, Dict
from .base import BaseStep, PipelineContext


class EnrichTranslationsESITStep(BaseStep):
    """Enrich Spanish and Italian translations with curated names."""
    
    def execute(self, context: PipelineContext, params: Dict[str, Any]) -> PipelineContext:
        """
        Execute the enrichment step.
        
        Args:
            context: Pipeline context with target data
            params: Step parameters with 'es_file' and 'it_file' paths
        
        Returns:
            Updated context with enriched translations
        """
        es_file = params.get('es_file')
        it_file = params.get('it_file')
        
        if not es_file or not it_file:
            print(f"    ⚠️  Missing es_file or it_file parameter")
            return context
        
        print(f"    📝 Loading translation enrichments")
        
        # Load translation files
        translations = {}
        
        for lang, file_path in [('es', es_file), ('it', it_file)]:
            path = Path(file_path)
            if not path.exists():
                print(f"       ⚠️  File not found: {file_path}")
                continue
            
            with open(path, 'r', encoding='utf-8') as f:
                translations[lang] = json.load(f)
            
            print(f"       ✅ Loaded {len(translations[lang])} {lang.upper()} translations")
        
        if not translations:
            print(f"    ⚠️  No translation files loaded")
            return context
        
        # Get target data
        target_data = context.get_data()
        if not target_data or 'sections' not in target_data:
            print(f"    ⚠️  No sections found in target data")
            return context
        
        # Enrich translations for each Pokemon
        sections = target_data['sections']
        total_enriched = {'es': 0, 'it': 0}
        
        for gen_key, gen_data in sections.items():
            pokemon_list = gen_data.get('pokemon', [])
            
            for pokemon in pokemon_list:
                pokemon_id = str(pokemon['id'])
                names = pokemon.get('name', {})
                
                # Update Spanish translation if available
                if 'es' in translations and pokemon_id in translations['es']:
                    old_name = names.get('es')
                    new_name = translations['es'][pokemon_id]
                    if old_name != new_name:
                        names['es'] = new_name
                        total_enriched['es'] += 1
                
                # Update Italian translation if available
                if 'it' in translations and pokemon_id in translations['it']:
                    old_name = names.get('it')
                    new_name = translations['it'][pokemon_id]
                    if old_name != new_name:
                        names['it'] = new_name
                        total_enriched['it'] += 1
        
        print(f"    ✅ Enriched {total_enriched['es']} ES + {total_enriched['it']} IT translations")
        
        # Update context
        context.set_data(target_data)
        context.set_metadata('translations_enriched', True)
        context.set_metadata('es_enriched', total_enriched['es'])
        context.set_metadata('it_enriched', total_enriched['it'])
        
        return context
