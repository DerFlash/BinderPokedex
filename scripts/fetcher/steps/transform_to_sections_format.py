"""
Transform TCG Set to Sections Format

Transforms a TCG set with 'cards' array into the unified 'sections' format
used by the PDF generator. This allows TCG sets to be generated the same way
as variant scopes (ExGen1, ExGen2, etc.).

Features:
- Extracts multilingual set names from set_names dict
- Builds multilingual descriptions with release dates
- Generates subtitle with [image]logo.png[/image] tags for each language
- Creates single 'all' section containing all cards (Pokemon + Trainer)

Input format (from transform_tcg_set):
{
    "type": "tcg_set",
    "set_id": "ME01",
    "name": "Mega Evolution",
    "release_date": "2025-09-26",
    "set_names": {"de": "Mega-Entwicklung", "en": "Mega Evolution", ...},
    "available_languages": ["de", "en", "fr", "es", "it"],
    "cards": [...]
}

Output format (for PDF generator):
{
    "type": "tcg_set",
    "name": "Mega Evolution",
    "available_languages": ["de", "en", "fr", "es", "it"],
    "sections": {
        "all": {
            "title": {"de": "Mega-Entwicklung", "en": "Mega Evolution", ...},
            "description": {"de": "Mega-Entwicklung - Veröffentlichung: 2025-09-26", ...},
            "subtitle": {"de": "[image]https://assets.tcgdex.net/de/me/me01/logo.png[/image]", ...},
            "cards": [...]
        }
    }
}
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from steps.base import BaseStep, PipelineContext

logger = logging.getLogger(__name__)


class TransformToSectionsFormatStep(BaseStep):
    """
    Transform TCG set data to sections format for PDF generation.
    
    Generates multilingual metadata from TCGdex API data:
    - Title: Set name in each language
    - Description: Set name + release date
    - Subtitle: Logo image URL with [image] tag
    
    Converts the flat 'cards' array into a 'sections' structure with a single
    section containing all cards. This makes TCG sets compatible with the
    unified PDF generator.
    """
    
    def execute(self, context: PipelineContext, params: Dict[str, Any]) -> PipelineContext:
        """
        Execute the transform step.
        
        Reads TCG set data from context (set by transform_tcg_set) and converts
        it to sections format.
        
        No parameters required - reads from context.
        """
        logger.info(f"🔄 Transforming to sections format")
        
        # Load data from context (set by transform_tcg_set step)
        tcg_data = context.data.get('tcg_set_target')
        if not tcg_data:
            raise ValueError("No TCG set data found in context. Make sure transform_tcg_set ran before this step.")
        
        # Check if already in sections format
        if 'sections' in tcg_data:
            logger.info(f"✅ Already in sections format, skipping transform")
            return context
        
        # Transform to sections format
        cards = tcg_data.get('cards', [])
        logger.info(f"📋 Converting {len(cards)} cards to sections format")
        
        # Count card types
        pokemon_cards = [c for c in cards if c.get('type') == 'pokemon']
        trainer_cards = [c for c in cards if c.get('type') == 'trainer']
        
        logger.info(f"   - Pokemon cards: {len(pokemon_cards)}")
        logger.info(f"   - Trainer/Energy cards: {len(trainer_cards)}")
        
        # Include ALL cards (Pokemon + Trainer) in sections format
        all_cards = cards
        
        # Build subtitle with logo image tags for each language
        # Prefer language-specific logo URLs from multilingual enrichment
        logo_urls_by_lang = tcg_data.get('logo_urls', {})
        
        # Fallback: Use base logo URL and replace language code
        base_logo_url = tcg_data.get('logo', '')
        
        # Generate language-specific subtitle with image tag
        subtitle = {}
        for lang in tcg_data.get('available_languages', ['en']):
            # Map language codes to TCGdex format
            lang_code_map = {
                'de': 'de',
                'en': 'en',
                'fr': 'fr',
                'es': 'es',
                'it': 'it',
                'ja': 'ja',
                'ko': 'ko',
                'zh_hans': 'zh-Hans',
                'zh_hant': 'zh-Hant'
            }
            tcgdex_lang = lang_code_map.get(lang, 'en')
            
            # Try to get language-specific logo URL first
            logo_url = logo_urls_by_lang.get(lang)
            
            # Fallback: Replace language in base URL
            if not logo_url and base_logo_url:
                logo_url = base_logo_url.replace('/en/', f'/{tcgdex_lang}/')
            
            if logo_url:
                subtitle[lang] = f"[image]{logo_url}[/image]"
        
        # Create sections structure
        set_names = tcg_data.get('set_names', {})
        available_languages = tcg_data.get('available_languages', ['en'])
        release_date = tcg_data.get('release_date', '')
        
        # Build title dict with set names from API
        title = {}
        for lang in available_languages:
            if lang in set_names:
                title[lang] = set_names[lang]
            else:
                # Fallback to default name
                title[lang] = tcg_data.get('name', 'Unknown Set')
        
        # Build description dict with release date
        description = {}
        for lang in available_languages:
            set_name = set_names.get(lang, tcg_data.get('name', 'Unknown Set'))
            if release_date:
                # Format: "Set Name - Release: YYYY-MM-DD"
                if lang == 'de':
                    description[lang] = f"{set_name} - Veröffentlichung: {release_date}"
                elif lang == 'en':
                    description[lang] = f"{set_name} - Release: {release_date}"
                elif lang == 'fr':
                    description[lang] = f"{set_name} - Sortie: {release_date}"
                elif lang == 'es':
                    description[lang] = f"{set_name} - Lanzamiento: {release_date}"
                elif lang == 'it':
                    description[lang] = f"{set_name} - Uscita: {release_date}"
                else:
                    description[lang] = f"{set_name} - Release: {release_date}"
            else:
                # Fallback if no release date available
                description[lang] = set_name
        
        sections_data = {
            'type': tcg_data.get('type', 'tcg_set'),
            'name': tcg_data.get('name', 'Unknown Set'),
            'available_languages': available_languages,
            'serie': tcg_data.get('serie', ''),  # Keep serie for reference
            'serie_name': tcg_data.get('serie_name', ''),
            'set_id': tcg_data.get('set_id', ''),
            'release_date': tcg_data.get('release_date', ''),
            'logo_urls': tcg_data.get('logo_urls', {}),  # Keep multilingual logo URLs for reference
            'sections': {
                'all': {
                    'title': title,
                    'description': description,
                    'subtitle': subtitle,  # Language-specific logo URLs with [image] tags
                    'cards': all_cards  # All cards including trainers
                }
            }
        }
        
        logger.info(f"✅ Transformed to sections format with {len(all_cards)} cards total")
        
        # Store in context for save_output step
        context.set_data(sections_data)
        
        return context
