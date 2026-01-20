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
# GENERATION INFORMATION
# ============================================================================

GENERATION_INFO = {
    1: {
        'name': 'Generation I',
        'count': 151,
        'range': (1, 151),
        'region': 'Kanto',
        'iconic_pokemon': [25, 6, 9],  # Pikachu, Charizard, Blastoise
    },
    2: {
        'name': 'Generation II',
        'count': 100,
        'range': (152, 251),
        'region': 'Johto',
        'iconic_pokemon': [249, 250, 155],  # Lugia, Ho-Oh, Cyndaquil
    },
    3: {
        'name': 'Generation III',
        'count': 135,
        'range': (252, 386),
        'region': 'Hoenn',
        'iconic_pokemon': [384, 383, 382],  # Rayquaza, Groudon, Kyogre
    },
    4: {
        'name': 'Generation IV',
        'count': 107,
        'range': (387, 493),
        'region': 'Sinnoh',
        'iconic_pokemon': [483, 484, 487],  # Dialga, Palkia, Giratina
    },
    5: {
        'name': 'Generation V',
        'count': 156,
        'range': (494, 649),
        'region': 'Unova',
        'iconic_pokemon': [643, 644, 645],  # Reshiram, Zekrom, Landorus
    },
    6: {
        'name': 'Generation VI',
        'count': 72,
        'range': (650, 721),
        'region': 'Kalos',
        'iconic_pokemon': [658, 653, 650],  # Greninja, Fennekin, Chespin
    },
    7: {
        'name': 'Generation VII',
        'count': 81,
        'range': (722, 802),
        'region': 'Alola',
        'iconic_pokemon': [791, 792, 784],  # Solgaleo, Lunala, Kommo-o
    },
    8: {
        'name': 'Generation VIII',
        'count': 89,
        'range': (803, 891),
        'region': 'Galar',
        'iconic_pokemon': [888, 889, 890],  # Zacian, Zamazenta, Eternatus
    },
    9: {
        'name': 'Generation IX',
        'count': 103,
        'range': (892, 994),
        'region': 'Paldea',
        'iconic_pokemon': [906, 909, 912],  # Sprigatito line, Fuecoco line, Quaxly line
        'region': 'Paldea',
        'iconic_pokemon': [1005, 1006, 1007],  # Koraidon, Miraidon, Pecharunt
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
