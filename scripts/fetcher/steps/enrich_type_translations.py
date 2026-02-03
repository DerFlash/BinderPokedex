"""
Enrichment step: Fetch Pokemon type translations from PokeAPI.

This step fetches official type name translations for all 18 Pokemon types
from PokeAPI and adds them to the output data for use in PDF generation.

Example output structure:
{
    "type_translations": {
        "Normal": {"de": "Normal", "en": "Normal", "ja": "ノーマル", ...},
        "Fire": {"de": "Feuer", "en": "Fire", "ja": "ほのお", ...},
        ...
    }
}
"""

from typing import Dict, Any
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from steps.base import BaseStep
from lib.pokeapi_client import PokéAPIClient

logger = logging.getLogger(__name__)


class EnrichTypeTranslations(BaseStep):
    """Fetch Pokemon type translations from PokeAPI."""
    
    # All 18 Pokemon types
    POKEMON_TYPES = [
        'normal', 'fire', 'water', 'electric', 'grass', 'ice',
        'fighting', 'poison', 'ground', 'flying', 'psychic', 'bug',
        'rock', 'ghost', 'dragon', 'dark', 'steel', 'fairy'
    ]
    
    # Map PokeAPI language codes to our language codes
    LANGUAGE_MAP = {
        'de': 'de',
        'en': 'en',
        'es': 'es',
        'fr': 'fr',
        'it': 'it',
        'ja': 'ja',           # ja-Hrkt in PokeAPI
        'ko': 'ko',
        'zh-hans': 'zh_hans', # roomaji in PokeAPI
        'zh-hant': 'zh_hant'
    }
    
    def execute(self, context: 'PipelineContext', params: Dict[str, Any]) -> 'PipelineContext':
        """
        Fetch type translations from PokeAPI.
        
        Args:
            context: Pipeline context
            params: Step parameters
                - output_file: Optional path to save translations (default: enrichments/type_translations.json)
        
        Returns:
            Updated context with type_translations in data
        """
        logger.info("🎨 Fetching Pokemon type translations from PokeAPI...")
        
        # Check if translations file exists and use_cache is enabled
        output_file = params.get('output_file', 'enrichments/type_translations.json')
        output_path = Path(output_file)
        
        if output_path.exists():
            logger.info(f"   📂 Loading cached translations from {output_file}")
            import json
            with open(output_path, 'r', encoding='utf-8') as f:
                type_translations = json.load(f)
            logger.info(f"✅ Loaded {len(type_translations)} types from cache")
            context.data['type_translations'] = type_translations
            return context
        
        # Fetch from API
        api_client = PokéAPIClient()
        type_translations = {}
        
        for type_name in self.POKEMON_TYPES:
            try:
                # Fetch type data from PokeAPI
                type_data = api_client.fetch_type_data(type_name)
                
                # Extract translations
                translations = self._extract_translations(type_data)
                
                # Store with capitalized key (Normal, Fire, etc.)
                type_key = type_name.capitalize()
                type_translations[type_key] = translations
                
                logger.debug(f"  ✓ {type_key}: {translations.get('en')}")
                
            except Exception as e:
                logger.warning(f"  ✗ Failed to fetch {type_name}: {e}")
                # Fallback: use English name
                type_key = type_name.capitalize()
                type_translations[type_key] = {lang: type_key for lang in self.LANGUAGE_MAP.values()}
        
        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(type_translations, f, indent=2, ensure_ascii=False)
        logger.info(f"   💾 Saved translations to {output_file}")
        
        # Add to context
        context.data['type_translations'] = type_translations
        
        logger.info(f"✅ Loaded translations for {len(type_translations)} types")
        
        return context
    
    def _extract_translations(self, type_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract type name translations from PokeAPI type data.
        
        Args:
            type_data: Type data from PokeAPI
        
        Returns:
            Dict mapping language code to translated name
        """
        translations = {}
        
        for name_entry in type_data.get('names', []):
            lang_data = name_entry.get('language', {})
            lang_name = lang_data.get('name', '')
            translated_name = name_entry.get('name', '')
            
            # Map PokeAPI language codes to our codes (case-insensitive)
            lang_lower = lang_name.lower()
            if lang_lower == 'de':
                translations['de'] = translated_name
            elif lang_lower == 'en':
                translations['en'] = translated_name
            elif lang_lower == 'es':
                translations['es'] = translated_name
            elif lang_lower == 'fr':
                translations['fr'] = translated_name
            elif lang_lower == 'it':
                translations['it'] = translated_name
            elif lang_lower in ['ja', 'ja-hrkt']:
                translations['ja'] = translated_name
            elif lang_lower == 'ko':
                translations['ko'] = translated_name
            elif lang_lower in ['zh-hans', 'roomaji']:
                translations['zh_hans'] = translated_name
            elif lang_lower == 'zh-hant':
                translations['zh_hant'] = translated_name
        
        return translations
