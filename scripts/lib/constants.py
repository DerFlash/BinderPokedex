"""
Configuration Constants for Binder Pokédex PDF Generation

Centralizes all configuration for cards, languages, fonts, and layout.
"""

from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor

# ============================================================================
# LANGUAGE CONFIGURATION
# ============================================================================

LANGUAGES = {
    'de': {
        'code': 'de',
        'name': 'Deutsch',
        'name_english': 'German',
        'font_group': 'latin',
    },
    'en': {
        'code': 'en',
        'name': 'English',
        'name_english': 'English',
        'font_group': 'latin',
    },
    'es': {
        'code': 'es',
        'name': 'Español',
        'name_english': 'Spanish',
        'font_group': 'latin',
    },
    'fr': {
        'code': 'fr',
        'name': 'Français',
        'name_english': 'French',
        'font_group': 'latin',
    },
    'it': {
        'code': 'it',
        'name': 'Italiano',
        'name_english': 'Italian',
        'font_group': 'latin',
    },
    'ja': {
        'code': 'ja',
        'name': '日本語',
        'name_english': 'Japanese',
        'font_group': 'cjk',
    },
    'ko': {
        'code': 'ko',
        'name': '한국어',
        'name_english': 'Korean',
        'font_group': 'cjk',
    },
    'zh_hans': {
        'code': 'zh_hans',
        'name': '简体中文',
        'name_english': 'Chinese (Simplified)',
        'font_group': 'cjk',
    },
    'zh_hant': {
        'code': 'zh_hant',
        'name': '繁體中文',
        'name_english': 'Chinese (Traditional)',
        'font_group': 'cjk',
    },
}

# ============================================================================
# GENERATION COLORS
# ============================================================================

GENERATION_COLORS = {
    1: '#FF0000',  # Red
    2: '#FFAA00',  # Orange
    3: '#0000FF',  # Blue
    4: '#AA00FF',  # Purple
    5: '#00AA00',  # Green
    6: '#00AAAA',  # Cyan
    7: '#FF00AA',  # Pink
    8: '#AAAA00',  # Yellow
    9: '#666666',  # Gray
}

# ============================================================================
# CARD LAYOUT & DIMENSIONS (Pokémon Card Standards)
# ============================================================================

# Standard Pokémon card size
CARD_WIDTH = 63.5 * mm          # 2.5 inches
CARD_HEIGHT = 88.9 * mm         # 3.5 inches

# Binder layout
CARDS_PER_ROW = 3
CARDS_PER_COLUMN = 3
CARDS_PER_PAGE = CARDS_PER_ROW * CARDS_PER_COLUMN

# Spacing between cards
GAP_X = 5 * mm
GAP_Y = 5 * mm

# Page margins
# Adjusted from 10mm to 4.75mm to prevent right-side cutoff on A4 (210mm width)
# Layout: 3 cards × 63.5mm + 2 gaps × 5mm = 200.5mm, needs 4.75mm margins on each side
PAGE_MARGIN = 4.75 * mm

# Page size (A4)
from reportlab.lib.pagesizes import A4
PAGE_WIDTH, PAGE_HEIGHT = A4

# ============================================================================
# CARD ELEMENT DIMENSIONS
# ============================================================================

# Header section
CARD_HEADER_HEIGHT = 15 * mm
CARD_IMAGE_HEIGHT = 40 * mm

# Text sections
CARD_NAME_SIZE = 11
CARD_TYPE_SIZE = 9
CARD_METADATA_SIZE = 8

# Padding within card elements
CARD_PADDING = 2 * mm

# ============================================================================
# COLORS
# ============================================================================

COLORS = {
    'background': HexColor('#FFFFFF'),
    'border': HexColor('#000000'),
    'header_bg': HexColor('#E0E0E0'),
    'text_primary': HexColor('#000000'),
    'text_secondary': HexColor('#555555'),
    'type_normal': HexColor('#A8A878'),
    'type_fire': HexColor('#F08030'),
    'type_water': HexColor('#6890F0'),
    'type_grass': HexColor('#78C850'),
    'type_electric': HexColor('#F8D030'),
    'type_ice': HexColor('#98D8D8'),
    'type_fighting': HexColor('#C03028'),
    'type_poison': HexColor('#A040A0'),
    'type_ground': HexColor('#E0C068'),
    'type_flying': HexColor('#A890F0'),
    'type_psychic': HexColor('#F85888'),
    'type_bug': HexColor('#A8B820'),
    'type_rock': HexColor('#B8A038'),
    'type_ghost': HexColor('#705898'),
    'type_dragon': HexColor('#7038F8'),
    'type_dark': HexColor('#705848'),
    'type_steel': HexColor('#B8B8D0'),
    'type_fairy': HexColor('#EE99AC'),
}

# ============================================================================
# POKÉMON TYPE COLORS (Canonical Source)
# ============================================================================
# Used for card header colors. This is the single source of truth for type colors.
# Maps English type names to hex color codes.

TYPE_COLORS = {
    'Normal': '#A8A878',
    'Fire': '#F08030',
    'Water': '#6890F0',
    'Electric': '#F8D030',
    'Grass': '#78C850',
    'Ice': '#98D8D8',
    'Fighting': '#C03028',
    'Poison': '#A040A0',
    'Ground': '#E0C068',
    'Flying': '#A890F0',
    'Psychic': '#F85888',
    'Bug': '#A8B820',
    'Rock': '#B8A038',
    'Ghost': '#705898',
    'Dragon': '#7038F8',
    'Dark': '#705848',
    'Steel': '#B8B8D0',
    'Fairy': '#EE99AC',
}

# ============================================================================
# GENERATION & VARIANT COLORS (Canonical Source)
# ============================================================================

GENERATION_COLORS = {
    1: '#FF0000',      # Red
    2: '#FFAA00',      # Orange
    3: '#0000FF',      # Blue
    4: '#AA00FF',      # Purple
    5: '#00AA00',      # Green
    6: '#00AAAA',      # Cyan
    7: '#FF00AA',      # Pink
    8: '#AAAA00',      # Yellow
    9: '#666666',      # Gray
}

VARIANT_COLORS = {
    'ex_gen1': '#1F51BA',             # Blue for Gen1
    'ex_gen2': '#3D5A80',             # Dark Blue for Gen2
    'ex_gen3': '#6B40D1',             # Purple for Gen3
    'mega_evolution': '#FFD700',      # Gold
    'gigantamax': '#C5283F',          # Red
    'regional_alola': '#FDB927',      # Yellow
    'regional_galar': '#0071BA',      # Blue
    'regional_hisui': '#9D3F1D',      # Brown
    'regional_paldea': '#D3337F',     # Pink
    'primal_terastal': '#7B61FF',     # Purple
    'patterns_unique': '#9D7A4C',     # Orange
    'fusion_special': '#6F6F6F',      # Gray
}

# ============================================================================
# TYPE INFORMATION
# ============================================================================

POKEMON_TYPES = {
    'normal': {'name_de': 'Normal', 'name_en': 'Normal', 'color': COLORS['type_normal']},
    'fire': {'name_de': 'Feuer', 'name_en': 'Fire', 'color': COLORS['type_fire']},
    'water': {'name_de': 'Wasser', 'name_en': 'Water', 'color': COLORS['type_water']},
    'grass': {'name_de': 'Pflanze', 'name_en': 'Grass', 'color': COLORS['type_grass']},
    'electric': {'name_de': 'Elektro', 'name_en': 'Electric', 'color': COLORS['type_electric']},
    'ice': {'name_de': 'Eis', 'name_en': 'Ice', 'color': COLORS['type_ice']},
    'fighting': {'name_de': 'Kampf', 'name_en': 'Fighting', 'color': COLORS['type_fighting']},
    'poison': {'name_de': 'Gift', 'name_en': 'Poison', 'color': COLORS['type_poison']},
    'ground': {'name_de': 'Boden', 'name_en': 'Ground', 'color': COLORS['type_ground']},
    'flying': {'name_de': 'Flug', 'name_en': 'Flying', 'color': COLORS['type_flying']},
    'psychic': {'name_de': 'Psycho', 'name_en': 'Psychic', 'color': COLORS['type_psychic']},
    'bug': {'name_de': 'Käfer', 'name_en': 'Bug', 'color': COLORS['type_bug']},
    'rock': {'name_de': 'Stein', 'name_en': 'Rock', 'color': COLORS['type_rock']},
    'ghost': {'name_de': 'Geist', 'name_en': 'Ghost', 'color': COLORS['type_ghost']},
    'dragon': {'name_de': 'Drache', 'name_en': 'Dragon', 'color': COLORS['type_dragon']},
    'dark': {'name_de': 'Unlicht', 'name_en': 'Dark', 'color': COLORS['type_dark']},
    'steel': {'name_de': 'Stahl', 'name_en': 'Steel', 'color': COLORS['type_steel']},
    'fairy': {'name_de': 'Fee', 'name_en': 'Fairy', 'color': COLORS['type_fairy']},
}

# ============================================================================
# PDF OUTPUT CONFIGURATION
# ============================================================================

from pathlib import Path

# Output directory: {project_root}/output/
# Calculate relative to this file's location: scripts/lib/constants.py
OUTPUT_DIR = Path(__file__).parent.parent.parent / 'output'
PDF_PREFIX = 'pokemon_gen'
PDF_EXTENSION = '.pdf'

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_language_name(language_code: str, english: bool = False) -> str:
    """Get language name for display."""
    if language_code not in LANGUAGES:
        raise ValueError(f"Unknown language: {language_code}")
    
    key = 'name_english' if english else 'name'
    return LANGUAGES[language_code][key]


def get_type_name(pokemon_type: str, language_code: str) -> str:
    """Get translated type name."""
    if pokemon_type not in POKEMON_TYPES:
        raise ValueError(f"Unknown type: {pokemon_type}")
    
    if language_code not in LANGUAGES:
        raise ValueError(f"Unknown language: {language_code}")
    
    key = f'name_{language_code}'
    return POKEMON_TYPES[pokemon_type].get(key, pokemon_type)


def get_type_color(pokemon_type: str):
    """Get color for a Pokémon type."""
    if pokemon_type not in POKEMON_TYPES:
        raise ValueError(f"Unknown type: {pokemon_type}")
    
    return POKEMON_TYPES[pokemon_type]['color']


def get_generation_info(generation: int) -> dict:
    """Load generation info from consolidated pokemon.json or fallback to pokemon_gen*.json."""
    import json
    from pathlib import Path
    
    data_dir = OUTPUT_DIR.parent / 'data'
    
    # Try consolidated format first
    consolidated_file = data_dir / 'pokemon.json'
    if consolidated_file.exists():
        try:
            with open(consolidated_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            section_key = f'gen{generation}'
            if section_key in data.get('sections', {}):
                section = data['sections'][section_key]
                # Build generation_info from section metadata
                return {
                    'name': section.get('name', f'Generation {generation}'),
                    'region': section.get('region', ''),
                    'count': len(section.get('pokemon', [])),  # Calculate from actual list
                    'range': section.get('range', [0, 0]),
                    'iconic_pokemon': section.get('iconic_pokemon', []),
                    'title_mode': 'with_subtitle',  # Unified title rendering mode
                    'title': {'en': f'Generation {generation}', 'de': f'Generation {generation}'},
                    'subtitle': {'en': section.get('region', ''), 'de': section.get('region', '')},
                }
        except (json.JSONDecodeError, IOError):
            pass
    
    # Fall back to old format
    gen_file = data_dir / f'pokemon_gen{generation}.json'
    if not gen_file.exists():
        raise FileNotFoundError(f"Generation data file not found: {gen_file}")
    
    with open(gen_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    gen_info = data.get('generation_info', {})
    
    # Ensure title_mode is set for consistent rendering
    if 'title_mode' not in gen_info:
        gen_info['title_mode'] = 'with_subtitle'
    if 'title' not in gen_info:
        gen_info['title'] = {'en': f'Generation {generation}', 'de': f'Generation {generation}'}
    if 'subtitle' not in gen_info:
        gen_info['subtitle'] = {'en': gen_info.get('region', ''), 'de': gen_info.get('region', '')}
    
    return gen_info
