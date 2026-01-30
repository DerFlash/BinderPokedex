"""
Transform Black & White EX Cards to Variant Format (Single Card per Pokemon)

Transforms TCGdex Black & White EX card data from source format to the variant format
expected by the PDF generator. Selects ONE card per Pokemon (priority: Next Destinies first,
then alphabetically by set name).

Input: data/source/tcg_bw_ex.json (99 cards)
Output: data/ExGen2_Single.json (~41 unique Pokemon)
"""

import logging
from pathlib import Path
from typing import List, Dict, Any
import sys
import json
import requests

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from steps.base import BaseStep, PipelineContext

logger = logging.getLogger(__name__)


class TransformBlackWhiteEXStep(BaseStep):
    """
    Transform Black & White EX cards to variant format - ONE card per Pokemon.
    
    Selection priority when multiple cards exist:
    1. BW - Next Destinies (first BW EX set, bw2)
    2. Alphabetically by set name
    
    Excludes:
    - Mega EX variants (M-EX)
    - Primal variants
    """
    
    def __init__(self, name: str):
        super().__init__(name)
    
    def execute(self, context: PipelineContext, params: Dict[str, Any]) -> PipelineContext:
        """
        Execute the transformation.
        
        1. Load source data
        2. Group by Pokemon (dexId)
        3. Select one card per Pokemon (priority rules)
        4. Transform to variant format
        5. Save to output file
        """
        # Make paths absolute relative to project root (4 levels up from this file)
        project_root = Path(__file__).parent.parent.parent.parent
        
        source_path = params.get('source_file', 'data/source/tcg_bw_ex.json')
        if not Path(source_path).is_absolute():
            source_file = project_root / source_path
        else:
            source_file = Path(source_path)
        
        output_path = params.get('output_file', 'data/ExGen2.json')
        if not Path(output_path).is_absolute():
            output_file = project_root / output_path
        else:
            output_file = Path(output_path)
        
        logger.info(f"Starting BW EX cards transformation (single card per Pokemon)")
        
        # Load source data
        if not source_file.exists():
            raise FileNotFoundError(f"Source file not found: {source_file}")
        
        with open(source_file, 'r', encoding='utf-8') as f:
            source_data = json.load(f)
        
        cards = source_data['cards']
        logger.info(f"Loaded {len(cards)} cards from source")
        
        # Group cards by type (normal, mega, primal)
        # For mega cards, use tuple (dexId, form_suffix) to handle X/Y variants
        normal_cards: Dict[int, List[Dict[str, Any]]] = {}
        mega_cards: Dict[tuple, List[Dict[str, Any]]] = {}
        primal_cards: Dict[int, List[Dict[str, Any]]] = {}
        
        for card in cards:
            dex_ids = card.get('dexId', [])
            if not dex_ids:
                logger.warning(f"Card {card.get('name')} has no dexId")
                continue
            
            dex_id = dex_ids[0]
            name = card.get('name', '')
            
            # Categorize by type
            if 'Primal' in name:
                if dex_id not in primal_cards:
                    primal_cards[dex_id] = []
                primal_cards[dex_id].append(card)
            elif 'M ' in name or 'Mega' in name or name.startswith('M-'):
                # Mega Evolution - extract form suffix (X or Y)
                # Name formats: "M Charizard EX (X)" or similar
                form_suffix = ""
                # Check for X or Y in parentheses or at end
                if '(X)' in name or ' X ' in name or name.endswith(' X'):
                    form_suffix = "X"
                elif '(Y)' in name or ' Y ' in name or name.endswith(' Y'):
                    form_suffix = "Y"
                
                mega_key = (dex_id, form_suffix)
                if mega_key not in mega_cards:
                    mega_cards[mega_key] = []
                mega_cards[mega_key].append(card)
            else:
                if dex_id not in normal_cards:
                    normal_cards[dex_id] = []
                normal_cards[dex_id].append(card)
        
        logger.info(f"Grouped: {len(normal_cards)} normal, {len(mega_cards)} mega, {len(primal_cards)} primal Pokemon")
        
        # Select one card per Pokemon for each category
        selected_normal = self._select_best_cards(normal_cards)
        selected_mega = self._select_best_cards(mega_cards)
        selected_primal = self._select_best_cards(primal_cards)
        
        logger.info(f"Selected: {len(selected_normal)} normal, {len(selected_mega)} mega, {len(selected_primal)} primal")
        
        # Transform to variant format
        variant_data = self._transform_to_variant_format(selected_normal, selected_mega, selected_primal, context)
        
        # Save to output file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(variant_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Saved variant to {output_file}")
        
        # Store in context for subsequent enrichment steps
        context.set_data(variant_data)
        
        return context
    
    def _select_best_cards(self, pokemon_cards: Dict) -> List[Dict[str, Any]]:
        """
        Select one card per Pokemon (or form) based on priority rules.
        
        Accepts either:
        - Dict[int, List] for normal/primal cards (grouped by dexId)
        - Dict[tuple, List] for mega cards (grouped by dexId + form_suffix)
        """
        selected_cards = []
        
        for key in sorted(pokemon_cards.keys()):
            # Extract dex_id from key (either int or tuple)
            dex_id = key if isinstance(key, int) else key[0]
            cards_for_pokemon = pokemon_cards[key]
            
            if len(cards_for_pokemon) == 1:
                selected_cards.append(cards_for_pokemon[0])
            else:
                # Apply priority rules
                # 1. Next Destinies (bw4)
                nd_cards = [c for c in cards_for_pokemon if c['set']['id'] == 'bw4']
                if nd_cards:
                    selected_cards.append(nd_cards[0])
                    continue
                
                # 2. Alphabetically by set name
                cards_sorted = sorted(cards_for_pokemon, key=lambda c: c['set']['name'])
                selected_cards.append(cards_sorted[0])
        
        return selected_cards
    
    def _transform_to_variant_format(self, normal_cards: List[Dict[str, Any]], 
                                     mega_cards: List[Dict[str, Any]],
                                     primal_cards: List[Dict[str, Any]],
                                     context: PipelineContext) -> Dict[str, Any]:
        """
        Transform cards to the variant format expected by PDF generator.
        
        Format matches existing variant structure with multiple sections.
        """
        # Get variant metadata from context
        metadata = context.storage.get('metadata', {})
        variant_meta = metadata.get('variants', {}).get('ExGen2', {})
        
        # Transform each section
        normal_pokemon = self._transform_card_list(normal_cards, 'normal')
        mega_pokemon = self._transform_card_list(mega_cards, 'mega')
        primal_pokemon = self._transform_card_list(primal_cards, 'primal')
        
        variant_data = {
            'type': 'variant',
            'name': 'Pokémon EX - Generation 2',
            'sections': {
                'normal': {
                    'section_id': 'normal',
                    'color_hex': variant_meta.get('color', '#3D5A80'),
                    'title': variant_meta.get('title', {}),
                    'subtitle': variant_meta.get('subtitle', {}),
                    'suffix': '',
                    'featured_pokemon': [],
                    'pokemon': normal_pokemon
                },
                'mega': {
                    'section_id': 'mega',
                    'color_hex': '#7B2CBF',
                    'title': {
                        'de': '[M] Pokémon [EX]',
                        'en': '[M] Pokémon [EX]',
                        'fr': '[M] Pokémon [EX]',
                        'es': '[M] Pokémon [EX]',
                        'it': '[M] Pokémon [EX]',
                        'ja': '[M] ポケモン [EX]',
                        'ko': '[M] 포켓몬 [EX]',
                        'zh_hans': '[M] 宝可梦 [EX]',
                        'zh_hant': '[M] 寶可夢 [EX]'
                    },
                    'subtitle': {
                        'de': 'Mega-Entwicklung',
                        'en': 'Mega Evolution',
                        'fr': 'Méga-Évolution',
                        'es': 'Megaevolución',
                        'it': 'Megaevoluzione',
                        'ja': 'メガシンカ',
                        'ko': '메가진화',
                        'zh_hans': '超级进化',
                        'zh_hant': '超級進化'
                    },
                    'suffix': '',
                    'featured_pokemon': [],
                    'pokemon': mega_pokemon
                },
                'primal': {
                    'section_id': 'primal',
                    'color_hex': '#C1121F',
                    'title': {
                        'de': 'Primal Pokémon [EX]',
                        'en': 'Primal Pokémon [EX]',
                        'fr': 'Pokémon Primo [EX]',
                        'es': 'Pokémon Primigenio [EX]',
                        'it': 'Pokémon Archeo [EX]',
                        'ja': 'ゲンシポケモン [EX]',
                        'ko': '원시포켓몬 [EX]',
                        'zh_hans': '原始宝可梦 [EX]',
                        'zh_hant': '原始寶可夢 [EX]'
                    },
                    'subtitle': {
                        'de': 'Urform-Reversion',
                        'en': 'Primal Reversion',
                        'fr': 'Primo-Résurgence',
                        'es': 'Regresión Primigenia',
                        'it': 'Archeorisveglio',
                        'ja': 'ゲンシカイキ',
                        'ko': '원시회귀',
                        'zh_hans': '原始回归',
                        'zh_hant': '原始回歸'
                    },
                    'suffix': '',
                    'featured_pokemon': [],
                    'pokemon': primal_pokemon
                }
            }
        }
        
        logger.info(f"Created variant with {len(normal_pokemon)} normal, {len(mega_pokemon)} mega, {len(primal_pokemon)} primal")
        
        return variant_data
    
    def _get_pokeapi_artwork_url(self, dex_id: int, pokemon_name: str, section: str, form_suffix: str = None) -> str:
        """
        Generate PokeAPI official artwork URL for a Pokemon.
        
        Args:
            dex_id: National Pokedex ID
            pokemon_name: Pokemon name (e.g., "Charizard")
            section: 'normal', 'mega', or 'primal'
            form_suffix: Form suffix like "X" or "Y" for Mega variants
        
        Returns:
            URL to official artwork PNG
        """
        # For normal Pokemon, use direct artwork URL
        if section == 'normal':
            return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{dex_id}.png"
        
        # For Mega Evolutions and Primal forms, need to fetch the form-specific Pokemon ID
        try:
            # Construct form name
            base_name = pokemon_name.lower().replace(' ', '-')
            
            if section == 'primal':
                form_name = f"{base_name}-primal"
            elif section == 'mega':
                form_name = f"{base_name}-mega"
                if form_suffix:
                    form_name += f"-{form_suffix.lower()}"
            else:
                form_name = base_name
            
            # Query PokeAPI for this form
            response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{form_name}", timeout=10)
            if response.status_code == 200:
                form_data = response.json()
                form_id = form_data.get('id')
                if form_id:
                    return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{form_id}.png"
            
            logger.warning(f"Could not fetch PokeAPI form data for {form_name}, using base artwork")
        except Exception as e:
            logger.warning(f"Error fetching PokeAPI artwork for {pokemon_name}: {e}")
        
        # Fallback to base Pokemon artwork
        return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{dex_id}.png"
    
    def _transform_card_list(self, cards: List[Dict[str, Any]], section: str) -> List[Dict[str, Any]]:
        """Transform a list of cards to Pokemon entries."""
        pokemon_list = []
        
        for card in cards:
            dex_ids = card.get('dexId', [])
            if not dex_ids:
                continue
            
            dex_id = dex_ids[0]
            name = card.get('name', '')
            
            # Extract Pokemon name and determine prefix/suffix
            if section == 'primal':
                # Primal cards: "Primal Kyogre EX" -> prefix="Primal", name="Kyogre", suffix="[EX]"
                pokemon_name = name.replace('Primal ', '').replace(' EX', '').replace('-EX', '').strip()
                prefix = 'Primal'
                suffix = '[EX]'
            elif section == 'mega':
                # Mega cards: "M Charizard EX" -> prefix="[M]", name="Charizard", suffix="[EX]"
                pokemon_name = name.replace('M ', '').replace('Mega ', '').replace(' EX', '').replace('-EX', '').strip()
                
                # Check for X/Y form variants: "M Charizard EX (X)" or "M Charizard EX (Y)"
                form_variant = None
                if '(X)' in pokemon_name or ' X' in pokemon_name:
                    pokemon_name = pokemon_name.replace('(X)', '').replace(' X', '').strip()
                    form_variant = 'X'
                elif '(Y)' in pokemon_name or ' Y' in pokemon_name:
                    pokemon_name = pokemon_name.replace('(Y)', '').replace(' Y', '').strip()
                    form_variant = 'Y'
                
                prefix = '[M]'
                suffix = '[EX]'
            else:
                # Normal EX cards: no prefix, suffix="[EX]"
                if '-EX' in name:
                    pokemon_name = name.replace('-EX', '').strip()
                elif ' EX' in name:
                    pokemon_name = name.replace(' EX', '').strip()
                else:
                    pokemon_name = name.strip()
                prefix = None
                suffix = '[EX]'
                form_variant = None
            
            # Get image URL from PokeAPI official artwork
            image_url = self._get_pokeapi_artwork_url(dex_id, pokemon_name, section, form_variant if section == 'mega' else None)
            
            form_suffix = f"_EX2_{section.upper()[:3]}"
            
            pokemon_entry = {
                'id': dex_id,
                'types': card.get('types', []),
                'image_url': image_url,
                'name': {
                    'en': pokemon_name,
                    'de': pokemon_name,
                    'fr': pokemon_name,
                    'es': pokemon_name,
                    'it': pokemon_name,
                    'ja': pokemon_name,
                    'ko': pokemon_name,
                    'zh_hans': pokemon_name,
                    'zh_hant': pokemon_name
                },
                'prefix': prefix,
                'suffix': suffix,
                'form_code': f"#{dex_id:03d}{form_suffix}",
                'tcg_card': {
                    'id': card.get('id'),
                    'localId': card.get('localId'),
                    'set': card.get('set'),
                    'hp': card.get('hp'),
                    'rarity': card.get('rarity')
                }
            }
            
            pokemon_list.append(pokemon_entry)
        
        return pokemon_list
    
    def validate(self, context: PipelineContext) -> bool:
        """Validate the transformation."""
        if not self.output_file.exists():
            logger.error(f"Output file does not exist: {self.output_file}")
            return False
        
        with open(self.output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'sections' not in data or 'normal' not in data['sections']:
            logger.error("Invalid variant structure")
            return False
        
        pokemon = data['sections']['normal']['pokemon']
        
        # Check for duplicates
        dex_ids = [p['id'] for p in pokemon]
        if len(dex_ids) != len(set(dex_ids)):
            logger.error("Duplicate Pokemon found in variant")
            return False
        
        logger.info(f"✅ Validation passed: {len(pokemon)} unique Pokemon")
        return True


if __name__ == '__main__':
    # For testing the step directly
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    step_config = {
        'source_file': 'data/source/tcg_bw_ex.json',
        'output_file': 'data/ExGen2.json'
    }
    
    step = TransformBlackWhiteEXStep(step_config)
    context = PipelineContext(config={'source_file': None, 'target_file': None})
    
    try:
        context = step.execute(context)
        if step.validate(context):
            print("\n✅ Transformation completed and validated successfully!")
        else:
            print("\n❌ Transformation validation failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Transformation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
