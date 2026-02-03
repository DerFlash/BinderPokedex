"""
Pokemon Utility Functions

Shared utility functions for Pokemon data processing across different pipeline steps.
"""

import logging
import requests

logger = logging.getLogger(__name__)


def get_mega_artwork_url(
    pokemon_name: str, 
    base_id: int, 
    form_suffix: str = None,
    original_card_name: str = None
) -> str:
    """
    Get artwork URL for Mega Evolution forms from PokeAPI.
    
    Mega evolutions have special IDs in PokeAPI (e.g., Mega Charizard X = 10034).
    Query PokeAPI to find the correct form ID.
    
    Args:
        pokemon_name: English Pokemon base name (e.g., "Charizard")
        base_id: Base Pokemon ID (e.g., 6 for Charizard)
        form_suffix: Optional explicit form suffix (e.g., "X", "Y")
        original_card_name: Optional TCG card name to extract form suffix from
    
    Returns:
        URL to form-specific artwork, or base artwork if form not found
    """
    # If form_suffix not provided, try to extract from original_card_name
    if form_suffix is None and original_card_name:
        # Extract X or Y suffix from original card name
        # Examples: "Mega Charizard X ex" -> "x", "Mega Lopunny ex" -> None
        if ' X ' in original_card_name or original_card_name.endswith(' X'):
            form_suffix = 'x'
        elif ' Y ' in original_card_name or original_card_name.endswith(' Y'):
            form_suffix = 'y'
    
    # Normalize form_suffix to lowercase
    if form_suffix:
        form_suffix = form_suffix.lower()
    
    # For Mega Evolutions, need to fetch the form-specific Pokemon ID
    try:
        # Construct form name: "charizard-mega-x" or "lopunny-mega"
        base_name = pokemon_name.lower().replace(' ', '-')
        form_name = f"{base_name}-mega"
        if form_suffix:
            form_name += f"-{form_suffix}"
        
        # Query PokeAPI for this form
        response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{form_name}", timeout=10)
        if response.status_code == 200:
            form_data = response.json()
            form_id = form_data.get('id')
            if form_id:
                logger.debug(f"Found Mega form ID {form_id} for {form_name}")
                return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{form_id}.png"
        
        logger.warning(f"Could not fetch PokeAPI form data for {form_name}, using base artwork")
    except Exception as e:
        logger.warning(f"Error fetching PokeAPI artwork for {pokemon_name}: {e}")
    
    # Fallback to base Pokemon artwork
    return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{base_id}.png"
