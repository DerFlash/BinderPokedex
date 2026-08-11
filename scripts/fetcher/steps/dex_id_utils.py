"""
DexID Lookup Utilities

Shared utilities for looking up Pokemon dexIds when TCGdex API doesn't provide them.
Used across multiple steps to avoid code duplication.

WORKAROUND for TCGdex API limitation:
The TCGdex API returns empty dexId[] arrays for certain card types:
- Trainer-owned Pokemon (e.g., "Erika's Oddish", "Team Rocket's Mewtwo")
- Mega Pokemon (e.g., "Mega Charizard Y", "Mega Dragonite")
- Regional forms (e.g., "Galarian Zigzagoon", "Alolan Raichu")
- Special forms (e.g., "Fan Rotom", "Wash Rotom")
"""

import re
from typing import Any, Mapping, Optional


def extract_base_pokemon_name(card_name: str) -> Optional[str]:
    """
    Extract base Pokemon name from TCG card name.
    
    Examples:
        "Erika's Oddish" -> "Oddish"
        "Lillie's Clefairy ex" -> "Clefairy"
        "Mega Charizard Y" -> "Charizard"
        "Mega Charizard Y ex" -> "Charizard"
        "Galarian Zigzagoon" -> "Zigzagoon"
        "Fan Rotom" -> "Rotom"
        "Pikachu ex" -> "Pikachu"
    
    Args:
        card_name: Full TCG card name
        
    Returns:
        Base Pokemon name or None if couldn't extract
    """
    # Remove common suffixes
    name = card_name.replace(' ex', '').replace('-ex', '').strip()
    
    # Pattern 1: Trainer's Pokemon (e.g., "Erika's Oddish", "Team Rocket's Mewtwo")
    trainer_match = re.match(r"^.+?'s\s+(.+)$", name)
    if trainer_match:
        pokemon_name = trainer_match.group(1)
        # Remove any form suffixes (X, Y, etc.)
        pokemon_name = re.sub(r'\s+[XY]$', '', pokemon_name)
        return pokemon_name.strip()
    
    # Pattern 2: Mega Evolution (e.g., "Mega Charizard Y")
    if name.startswith('Mega '):
        pokemon_name = name[5:]  # Remove "Mega "
        # Remove form suffixes (X, Y)
        pokemon_name = re.sub(r'\s+[XY]$', '', pokemon_name)
        return pokemon_name.strip()
    
    # Pattern 3: Regional forms (e.g., "Galarian Zigzagoon")
    regional_prefixes = ['Galarian', 'Alolan', 'Hisuian', 'Paldean']
    for prefix in regional_prefixes:
        if name.startswith(f'{prefix} '):
            pokemon_name = name[len(prefix)+1:]  # Remove prefix + space
            return pokemon_name.strip()
    
    # Pattern 4: Rotom forms (e.g., "Fan Rotom")
    if ' Rotom' in name:
        return 'Rotom'
    
    # Pattern 5: Regular Pokemon - return as is
    return re.sub(r'\s+[XY]$', '', name).strip()


def build_pokedex_name_lookup(
    pokedex_data: Mapping[str, Any],
) -> dict[str, int]:
    """Build one case-insensitive English-name to National-Dex lookup."""
    lookup: dict[str, int] = {}
    sections = pokedex_data.get("sections", {})
    if not isinstance(sections, Mapping):
        return lookup
    for section in sections.values():
        if not isinstance(section, Mapping):
            continue
        cards = section.get("cards", [])
        if not isinstance(cards, list):
            continue
        for pokemon in cards:
            if not isinstance(pokemon, Mapping):
                continue
            pokemon_id = pokemon.get("pokemon_id")
            names = pokemon.get("name")
            english_name = (
                names.get("en")
                if isinstance(names, Mapping)
                else None
            )
            if (
                type(pokemon_id) is int
                and pokemon_id > 0
                and isinstance(english_name, str)
                and english_name.strip()
            ):
                lookup[english_name.strip().casefold()] = pokemon_id
    return lookup


def resolve_card_dex_id(
    card_name: str,
    dex_ids: object,
    name_lookup: Mapping[str, int],
) -> Optional[int]:
    """Prefer the card-name identity over a missing or inconsistent API ID."""
    base_name = extract_base_pokemon_name(card_name)
    if base_name:
        resolved = name_lookup.get(base_name.casefold())
        if type(resolved) is int and resolved > 0:
            return resolved
    if isinstance(dex_ids, list) and dex_ids:
        provided = dex_ids[0]
        if type(provided) is int and provided > 0:
            return provided
    return None


def identify_card_pattern(card_name: str) -> str:
    """
    Identify which pattern was matched for statistics.
    
    Returns:
        Pattern name: 'trainer_owned', 'mega', 'regional', 'rotom', 'other'
    """
    if "'s " in card_name:
        return 'trainer_owned'
    if card_name.startswith('Mega '):
        return 'mega'
    if any(card_name.startswith(f'{p} ') for p in ['Galarian', 'Alolan', 'Hisuian', 'Paldean']):
        return 'regional'
    if ' Rotom' in card_name:
        return 'rotom'
    return 'other'
