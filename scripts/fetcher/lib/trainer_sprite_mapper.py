"""
Trainer Sprite Mapper - Maps TCG trainer card names to Bulbagarden VS sprites

Bulbagarden Archives provides high-quality VS trainer sprites from the games.
This module maps TCG trainer card names to their corresponding sprite URLs.

Examples:
- "Acerola's Mischief" → "VSAcerola.png"
- "Professor's Research [Professor Sada]" → "VSSada.png"
- "Iono" → "VSIono.png"

Sprite URL pattern: https://archives.bulbagarden.net/wiki/File:VS{Name}.png
Direct image: https://archives.bulbagarden.net/media/upload/{hash}/VS{Name}.png
"""

import re
from typing import Optional

# Manual mappings for TCG card names to Bulbagarden sprite names
# Format: "TCG Card Name" → "Bulbagarden Sprite Name (without VS prefix and .png)"
TRAINER_SPRITE_MAP = {
    # Supporter cards from various sets
    "Acerola's Mischief": "Acerola",
    "Acerola": "Acerola",
    "Marnie": "Marnie",
    "Professor's Research (Professor Magnolia)": "Magnolia",
    "Professor's Research (Professor Sada)": "Sada",
    "Professor's Research (Professor Turo)": "Turo",
    "Professor's Research (Professor Rowan)": "Rowan",
    "Professor's Research (Professor Juniper)": "Juniper",
    "Professor's Research (Professor Oak)": "Oak",
    "Professor's Research (Professor Kukui)": "Kukui",
    "Professor Sada's Vitality": "Sada",
    "Professor Turo's Scenario": "Turo",
    "Iono": "Iono",
    "Nemona": "Nemona",
    "Arven": "Arven",
    "Penny": "Penny",
    "Clavell": "Clavell",
    "Giacomo": "Giacomo",
    "Mela": "Mela",
    "Atticus": "Atticus",
    "Ortega": "Ortega",
    "Eri": "Eri",
    "Boss's Orders (Ghetsis)": "Ghetsis",
    "Boss's Orders (Giovanni)": "Giovanni",
    "Boss's Orders (Cyrus)": "Cyrus",
    "Boss's Orders (Lysandre)": "Lysandre",
    "Boss's Orders (Maxie)": "Maxie",
    "Boss's Orders (Archie)": "Archie",
    "Cynthia": "Cynthia",
    "Cynthia's Ambition": "Cynthia",
    "N's Resolve": "N",
    "N": "N",
    "Colress's Experiment": "Colress",
    "Colress": "Colress",
    "Guzma": "Guzma",
    "Lillie": "Lillie",
    "Lusamine": "Lusamine",
    "Gladion": "Gladion",
    "Hau": "Hau",
    "Kukui": "Kukui",
    "Mallow": "Mallow",
    "Lana": "Lana",
    "Kiawe": "Kiawe",
    "Sophocles": "Sophocles",
    "Olivia": "Olivia",
    "Nanu": "Nanu",
    "Kahili": "Kahili",
    "Plumeria": "Plumeria",
    "Ilima": "Ilima",
    "Molayne": "Molayne",
    "Hapu": "Hapu",
    "Mina": "Mina",
    "Red": "Red",
    "Blue": "Blue",
    "Brock": "Brock",
    "Misty": "Misty",
    "Lt. Surge": "Surge",
    "Erika": "Erika",
    "Koga": "Koga",
    "Sabrina": "Sabrina",
    "Blaine": "Blaine",
    "Giovanni": "Giovanni",
    "Lance": "Lance",
    "Lorelei": "Lorelei",
    "Bruno": "Bruno",
    "Agatha": "Agatha",
}


def normalize_trainer_name(card_name: str) -> str:
    """
    Normalize a TCG trainer card name to extract the trainer's name.
    
    Examples:
        "Acerola's Mischief" → "Acerola"
        "Professor's Research [Professor Sada]" → "Sada"
        "Boss's Orders (Giovanni)" → "Giovanni"
        "Iono" → "Iono"
    
    Args:
        card_name: Full TCG card name
        
    Returns:
        Normalized trainer name
    """
    # Check manual mapping first
    if card_name in TRAINER_SPRITE_MAP:
        return TRAINER_SPRITE_MAP[card_name]
    
    # Extract from brackets/parentheses: "Professor's Research [Professor Sada]"
    bracket_match = re.search(r'\[([^\]]+)\]', card_name)
    if bracket_match:
        full_name = bracket_match.group(1)
        # Extract last name from "Professor Sada"
        if full_name.startswith("Professor "):
            return full_name.replace("Professor ", "").strip()
        return full_name
    
    paren_match = re.search(r'\(([^\)]+)\)', card_name)
    if paren_match:
        return paren_match.group(1)
    
    # Extract from possessive: "Acerola's Mischief" → "Acerola"
    possessive_match = re.match(r"^([A-Z][a-zA-Z]+)'s\s", card_name)
    if possessive_match:
        return possessive_match.group(1)
    
    # Return as-is for simple names like "Iono", "Arven"
    return card_name.strip()


def get_trainer_sprite_url(card_name: str) -> Optional[str]:
    """
    Get the Bulbagarden VS sprite URL for a trainer card.
    
    Args:
        card_name: TCG trainer card name (e.g., "Acerola's Mischief")
        
    Returns:
        URL to the sprite file page on Bulbagarden, or None if not found
        
    Example:
        >>> get_trainer_sprite_url("Acerola's Mischief")
        'https://archives.bulbagarden.net/wiki/File:VSAcerola.png'
    """
    trainer_name = normalize_trainer_name(card_name)
    
    if not trainer_name:
        return None
    
    # Build sprite filename: VS{Name}.png
    sprite_filename = f"VS{trainer_name}.png"
    
    # Bulbagarden file page URL
    return f"https://archives.bulbagarden.net/wiki/File:{sprite_filename}"


def get_direct_sprite_url(card_name: str, generation: str = "VII") -> Optional[str]:
    """
    Get a direct image URL pattern for the trainer sprite.
    
    Note: The actual hash in the URL path varies. This returns a predictable
    pattern, but the actual file may need to be fetched via MediaWiki API
    or by scraping the wiki page.
    
    Args:
        card_name: TCG trainer card name
        generation: Pokemon generation (default: VII for Sun/Moon style)
        
    Returns:
        Approximate direct image URL pattern
        
    Example:
        For production use, fetch the actual URL by:
        1. Get wiki page: get_trainer_sprite_url(card_name)
        2. Extract actual image URL from the page
    """
    trainer_name = normalize_trainer_name(card_name)
    
    if not trainer_name:
        return None
    
    sprite_filename = f"VS{trainer_name}.png"
    
    # Note: The /X/XX/ hash path varies per file
    # This is a template - actual implementation should fetch from wiki
    return f"https://archives.bulbagarden.net/media/upload/VS{trainer_name}.png"


# Reverse lookup: Bulbagarden sprite name → TCG card names
SPRITE_TO_CARD_MAP = {}
for card_name, sprite_name in TRAINER_SPRITE_MAP.items():
    if sprite_name not in SPRITE_TO_CARD_MAP:
        SPRITE_TO_CARD_MAP[sprite_name] = []
    SPRITE_TO_CARD_MAP[sprite_name].append(card_name)


if __name__ == "__main__":
    # Test examples
    test_cases = [
        "Acerola's Mischief",
        "Professor's Research [Professor Sada]",
        "Boss's Orders (Giovanni)",
        "Iono",
        "Marnie",
        "N's Resolve"
    ]
    
    print("Trainer Sprite Mapper - Test Cases")
    print("=" * 60)
    
    for card_name in test_cases:
        trainer_name = normalize_trainer_name(card_name)
        sprite_url = get_trainer_sprite_url(card_name)
        
        print(f"\nCard: {card_name}")
        print(f"  → Trainer: {trainer_name}")
        print(f"  → Sprite: VS{trainer_name}.png")
        print(f"  → URL: {sprite_url}")
