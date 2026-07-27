"""
Transform Scarlet & Violet ex Cards to Variant Format (Single Card per Pokemon)

Transforms TCGdex Scarlet & Violet ex card data from source format to the variant format
expected by the PDF generator. Selects one card per exact Pokemon form
(priority: Base Set first, then alphabetically by set name).

Input: data/source/tcg_sv_ex.json
Output: data/output/ExGen3.json (one representative per exact visual form)
"""

import logging
from pathlib import Path
from typing import List, Dict, Any
import sys
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from steps.base import BaseStep, PipelineContext
from steps.dex_id_utils import (
    build_pokedex_name_lookup,
    resolve_card_dex_id,
)
from steps.pokemon_utils import get_mega_artwork_url
from scripts.poster_assets.poster_subject import (
    OFFICIAL_ARTWORK_URL,
    official_artwork_id_for_card_name,
)

logger = logging.getLogger(__name__)


class TransformScarletVioletEXStep(BaseStep):
    """
    Transform Scarlet & Violet ex cards to variant format per exact form.
    
    Selection priority when multiple cards exist:
    1. Scarlet & Violet Base Set (first SV ex set, sv01)
    2. Alphabetically by set name
    
    Excludes:
    - Tera ex variants (separate Tera crystallization)
    """
    
    def __init__(self, name: str):
        super().__init__(name)
        self._pokedex_lookup: Dict[str, int] | None = None

    def _load_pokedex_lookup(self) -> Dict[str, int]:
        """Load the offline name trust root used to validate TCGdex dexIds."""
        if self._pokedex_lookup is not None:
            return self._pokedex_lookup
        project_root = Path(__file__).resolve().parents[3]
        pokedex_path = project_root / "data" / "output" / "Pokedex.json"
        if not pokedex_path.is_file():
            raise FileNotFoundError(
                f"Pokedex name lookup is required: {pokedex_path}"
            )
        with pokedex_path.open("r", encoding="utf-8") as handle:
            self._pokedex_lookup = build_pokedex_name_lookup(
                json.load(handle)
            )
        if not self._pokedex_lookup:
            raise ValueError("Pokedex name lookup is empty")
        return self._pokedex_lookup

    def _normalize_card_dex_ids(
        self,
        cards: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Correct inconsistent upstream IDs before grouping visual forms."""
        lookup = self._load_pokedex_lookup()
        normalized: List[Dict[str, Any]] = []
        for card in cards:
            name = card.get("name", "")
            dex_ids = card.get("dexId", [])
            resolved_id = resolve_card_dex_id(name, dex_ids, lookup)
            if resolved_id is None:
                normalized.append(card)
                continue
            supplied_id = (
                dex_ids[0]
                if isinstance(dex_ids, list) and dex_ids
                else None
            )
            if supplied_id == resolved_id:
                normalized.append(card)
                continue
            corrected = dict(card)
            corrected["dexId"] = [resolved_id]
            logger.warning(
                "Corrected inconsistent TCGdex dexId for %r: #%s -> #%s",
                name,
                supplied_id if supplied_id is not None else "none",
                resolved_id,
            )
            normalized.append(corrected)
        return normalized
    
    def execute(self, context: PipelineContext, params: Dict[str, Any]) -> PipelineContext:
        """
        Execute the transformation.
        
        1. Load source data from context
        2. Group by exact visual Pokemon form
        3. Select one representative card per form (priority rules)
        4. Transform to variant format
        """
        logger.info(
            "Starting modern ex-card transformation "
            "(one representative per exact visual form)"
        )
        
        # Load cards from context
        cards = context.data.get('tcg_sv_ex_cards')
        if not cards:
            raise ValueError("No SV ex cards found in context. Make sure fetch_tcgdex_ex_gen3 ran before this step.")
        
        logger.info(f"Loaded {len(cards)} cards from source")
        cards = self._normalize_card_dex_ids(cards)
        
        # Group cards by type and exact visual subject. Regional/special
        # forms may share a National-Dex species while requiring distinct
        # Official Artwork IDs.
        # For mega cards, we use a tuple (dexId, form_name) to handle X/Y variants
        normal_cards: Dict[tuple[int, int], List[Dict[str, Any]]] = {}
        mega_cards: Dict[tuple, List[Dict[str, Any]]] = {}
        
        for card in cards:
            dex_ids = card.get('dexId', [])
            if not dex_ids:
                logger.warning(f"Card {card.get('name')} has no dexId")
                continue
            
            dex_id = dex_ids[0]
            name = card.get('name', '')
            
            # Categorize by card type
            if name.startswith('Mega ') or 'Mega' in name:
                # Mega Evolution variant - extract form suffix (e.g., "X", "Y")
                # Name format: "Mega Pokemon X ex" or "Mega Pokemon Y ex"
                form_suffix = ""
                parts = name.replace(' ex', '').split()
                if len(parts) > 2 and parts[-1] in ['X', 'Y']:
                    form_suffix = parts[-1]
                
                # Use (dexId, form_suffix) as key to keep X and Y variants separate
                mega_key = (dex_id, form_suffix)
                if mega_key not in mega_cards:
                    mega_cards[mega_key] = []
                mega_cards[mega_key].append(card)
            else:
                artwork_id = official_artwork_id_for_card_name(dex_id, name)
                normal_key = (dex_id, artwork_id)
                if normal_key not in normal_cards:
                    normal_cards[normal_key] = []
                normal_cards[normal_key].append(card)
        
        logger.info(f"Grouped into normal={len(normal_cards)}, mega={len(mega_cards)} Pokemon")
        
        # Select one representative card per exact form for each type
        selected_normal = self._select_best_cards(normal_cards)
        selected_mega = self._select_best_cards(mega_cards)
        
        logger.info(f"Selected normal={len(selected_normal)}, mega={len(selected_mega)} cards")
        
        # Transform to variant format with 2 sections
        variant_data = self._transform_to_variant_format(selected_normal, selected_mega, context)
        
        # Store in context for subsequent enrichment steps and for save_output step
        context.set_data(variant_data)
        
        logger.info(f"✅ Transformed Scarlet & Violet ex cards to variant format")
        
        return context
    
    def _select_best_cards(self, pokemon_cards: Dict) -> List[Dict[str, Any]]:
        """
        Select one representative card per exact form based on priority rules.
        
        Accepts either:
        - Dict[tuple, List] for normal cards (species + artwork)
        - Dict[tuple, List] for mega cards (grouped by dexId + form_suffix)
        
        Priority:
        1. Scarlet & Violet Base Set (sv01)
        2. Alphabetically by set name
        """
        selected_cards = []

        def stable_card_key(card: Dict[str, Any]) -> tuple[str, int, str]:
            """Order equal-priority cards independently of API response order."""
            local_id = str(card.get("localId") or "")
            try:
                numeric_local_id = int(local_id)
            except ValueError:
                numeric_local_id = sys.maxsize
            return (
                str(card.get("set", {}).get("name") or "").casefold(),
                numeric_local_id,
                str(card.get("id") or ""),
            )
        
        for key in sorted(pokemon_cards.keys()):
            # Extract dex_id from key (either int or tuple)
            dex_id = key if isinstance(key, int) else key[0]
            cards_for_pokemon = pokemon_cards[key]
            
            if len(cards_for_pokemon) == 1:
                selected_cards.append(cards_for_pokemon[0])
            else:
                # Apply priority rules
                # 1. Scarlet & Violet Base Set (sv01)
                sv01_cards = [
                    card
                    for card in cards_for_pokemon
                    if card['set']['id'] == 'sv01'
                ]
                if sv01_cards:
                    selected_cards.append(
                        min(sv01_cards, key=stable_card_key)
                    )
                    logger.debug(f"#{dex_id:03d}: Selected Base Set card")
                    continue
                
                # 2. Alphabetically by set name, then stable local card ID.
                cards_sorted = sorted(cards_for_pokemon, key=stable_card_key)
                selected_cards.append(cards_sorted[0])
                logger.debug(f"#{dex_id:03d}: Selected {cards_sorted[0]['set']['name']} card (alphabetical)")
        
        return selected_cards
    
    def _transform_to_variant_format(self, normal_cards: List[Dict[str, Any]], mega_cards: List[Dict[str, Any]], context: PipelineContext) -> Dict[str, Any]:
        """
        Transform cards to the variant format expected by PDF generator.
        
        Creates 2 sections: normal, mega
        """
        # Get variant metadata from context
        metadata = context.storage.get('metadata', {})
        variant_meta = metadata.get('variants', {}).get('ExGen3', {})
        
        # Transform each card list
        normal_pokemon = self._transform_card_list(normal_cards, suffix='[EX_NEW]', prefix=None)
        mega_pokemon = self._transform_card_list(mega_cards, suffix='[EX_NEW]', prefix='Mega')
        
        # Create 2-section structure
        variant_data = {
            'type': 'variant',
            'name': 'Pokémon ex - Generation 3',
            'sections': {
                'normal': {
                    'section_id': 'normal',
                    'color_hex': variant_meta.get('color', '#6B40D1'),
                    'title': {
                        'de': 'Pokémon [EX_NEW]',
                        'en': 'Pokémon [EX_NEW]',
                        'fr': 'Pokémon [EX_NEW]',
                        'es': 'Pokémon [EX_NEW]',
                        'it': 'Pokémon [EX_NEW]',
                        'ja': 'ポケモン [EX_NEW]',
                        'ko': '포켓몬 [EX_NEW]',
                        'zh_hans': '宝可梦 [EX_NEW]',
                        'zh_hant': '寶可夢 [EX_NEW]'
                    },
                    'subtitle': variant_meta.get('subtitle', {}),
                    'suffix': '',
                    'cards': normal_pokemon
                },
                'mega': {
                    'section_id': 'mega',
                    'color_hex': '#7B2CBF',  # Same as ExGen2 mega
                    'title': {
                        'de': 'Mega-Pokémon [EX_NEW]',
                        'en': 'Mega Pokémon [EX_NEW]',
                        'fr': 'Méga-Pokémon [EX_NEW]',
                        'es': 'Mega-Pokémon [EX_NEW]',
                        'it': 'Mega-Pokémon [EX_NEW]',
                        'ja': 'メガポケモン [EX_NEW]',
                        'ko': '메가 포켓몬 [EX_NEW]',
                        'zh_hans': '超级宝可梦 [EX_NEW]',
                        'zh_hant': '超級寶可夢 [EX_NEW]'
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
                    'cards': mega_pokemon
                }
            }
        }
        
        logger.info(f"Created variant with normal={len(normal_pokemon)}, mega={len(mega_pokemon)} Pokemon")
        
        return variant_data
    
    def _get_pokeapi_artwork_url(self, dex_id: int, pokemon_name: str, is_mega: bool = False, form_suffix: str = None) -> str:
        """
        Generate PokeAPI official artwork URL for a Pokemon.
        
        Args:
            dex_id: National Pokedex ID
            pokemon_name: Pokemon name (e.g., "Charizard")
            is_mega: Whether this is a Mega Evolution
            form_suffix: Form suffix like "X" or "Y" for Mega variants
        
        Returns:
            URL to official artwork PNG
        """
        # Resolve named regional/special forms through the pinned offline
        # registry. Ordinary base forms retain the National-Dex artwork ID.
        if not is_mega:
            artwork_id = official_artwork_id_for_card_name(
                dex_id,
                pokemon_name,
            )
            return OFFICIAL_ARTWORK_URL.format(artwork_id=artwork_id)
        
        # For Mega Evolutions, use shared utility function
        return get_mega_artwork_url(
            pokemon_name=pokemon_name,
            base_id=dex_id,
            form_suffix=form_suffix
        )
    
    def _transform_card_list(self, cards: List[Dict[str, Any]], suffix: str = None, prefix: str = None) -> List[Dict[str, Any]]:
        """Transform a list of cards to Pokemon entries."""
        pokemon_list = []
        
        for card in cards:
            dex_ids = card.get('dexId', [])
            if not dex_ids:
                continue
            
            dex_id = dex_ids[0]
            name = card.get('name', '')
            
            # Extract Pokemon name (remove ex suffix and variants)
            pokemon_name_raw = name.replace(' ex', '').replace('–ex-Tera', '').replace('-ex-Tera', '').replace('Mega ', '').strip()
            
            # Get image URL from PokeAPI official artwork
            # Check if this is a Mega evolution with form suffix
            form_suffix = None
            pokemon_base_name = pokemon_name_raw
            
            if prefix == 'Mega':
                # Extract X/Y suffix if present: "Charizard X" -> base="Charizard", suffix="X"
                parts = pokemon_name_raw.split()
                if len(parts) >= 2 and parts[-1] in ['X', 'Y']:
                    form_suffix = parts[-1]
                    pokemon_base_name = ' '.join(parts[:-1])  # Remove X/Y from name
            
            image_url = self._get_pokeapi_artwork_url(dex_id, pokemon_base_name, is_mega=(prefix == 'Mega'), form_suffix=form_suffix)
            
            pokemon_name = pokemon_name_raw
            
            pokemon_entry = {
                'pokemon_id': dex_id,
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
                'form_code': f"#{dex_id:03d}_EX3",
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
    
