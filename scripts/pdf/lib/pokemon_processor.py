"""
Pokémon Data Processor - Daten-Verarbeitung und Normalisierung.

Verantwortung: Rohdata von API → standardisiertes Format mit allen 9 Sprachen.
Darf nicht: API-Abfragen machen, Dateien schreiben, Console-Ausgaben machen.
"""

from typing import Dict, Optional


class PokémonProcessor:
    """Verarbeitet Pokémon-Daten von der API in standardisiertes Format."""
    
    # PokéAPI Sprachnamen zu unseren Sprachcodes
    # Tatsächlich verfügbar: en, de, fr, es, it, ja, ja-Hrkt, ko, zh-Hans, zh-Hant
    LANGUAGE_CODES = {
        'en': 'English',
        'de': 'German',
        'fr': 'French',
        'es': 'Spanish',       # Wird durch Enrichment verbessert
        'it': 'Italian',       # Wird durch Enrichment verbessert
        'ja': 'Japanese',      # Echte Schriftzeichen (bevorzugt vor ja-Hrkt)
        'ko': 'Korean',
        'zh-Hans': 'zh-Hans',  # Vereinfachtes Chinesisch
        'zh-Hant': 'zh-Hant',  # Traditionelles Chinesisch
    }
    
    # Fallback-Reihenfolge für Japanisch wenn nicht verfügbar
    JAPANESE_FALLBACKS = ['Japanese', 'ja-Hrkt']
    
    @staticmethod
    def extract_all_names(species_data: Dict) -> Dict[str, str]:
        """
        Extrahiere alle Namen in 10 Sprachen aus Species-Daten.
        
        Args:
            species_data: Species-Daten von PokéAPI
            
        Returns:
            Dict mit name_XX Feldern (name_en, name_de, etc.)
        """
        names = {
            'name_en': species_data.get('name', 'Unknown').capitalize(),
            'name_de': None,
            'name_fr': None,
            'name_es': None,
            'name_it': None,
            'name_ja': None,
            'name_ko': None,
            'name_zh_hans': None,  # Vereinfachtes Chinesisch
            'name_zh_hant': None,  # Traditionelles Chinesisch
        }
        
        if 'names' not in species_data:
            return names
        
        for entry in species_data['names']:
            lang_name = entry.get('language', {}).get('name', '')
            name_value = entry.get('name', '')
            
            # Spezialbehandlung für Japanisch: bevorzuge echte Schriftzeichen
            if lang_name == 'ja':
                names['name_ja'] = name_value
            elif lang_name == 'ja-Hrkt' and names['name_ja'] is None:
                names['name_ja'] = name_value
            # Deutsche und andere europäische Sprachen
            elif lang_name == 'de':
                names['name_de'] = name_value
            elif lang_name == 'fr':
                names['name_fr'] = name_value
            elif lang_name == 'es':
                names['name_es'] = name_value
            elif lang_name == 'it':
                names['name_it'] = name_value
            # Koreanisch und Chinesisch (mit Code-Format)
            elif lang_name == 'ko':
                names['name_ko'] = name_value
            elif lang_name == 'zh-Hans':
                names['name_zh_hans'] = name_value
            elif lang_name == 'zh-Hant':
                names['name_zh_hant'] = name_value
        
        return names
    
    @staticmethod
    def extract_types(pokemon_data: Dict) -> tuple:
        """
        Extrahiere Type1 und Type2 aus Pokémon-Daten.
        
        Args:
            pokemon_data: Pokémon-Daten von PokéAPI
            
        Returns:
            Tuple (type1, type2) oder (type1, None)
        """
        types = [t['type']['name'].capitalize() for t in pokemon_data.get('types', [])]
        type1 = types[0] if len(types) > 0 else 'Normal'
        type2 = types[1] if len(types) > 1 else None
        return type1, type2
    
    @staticmethod
    def extract_image_url(pokemon_data: Dict) -> str:
        """
        Extrahiere Official-Artwork Image-URL.
        
        Args:
            pokemon_data: Pokémon-Daten von PokéAPI
            
        Returns:
            Image URL oder leerer String
        """
        image_url = (pokemon_data.get('sprites', {})
                     .get('other', {})
                     .get('official-artwork', {})
                     .get('front_default'))
        
        if not image_url:
            image_url = pokemon_data.get('sprites', {}).get('front_default')
        
        return image_url or ''
    
    @staticmethod
    def build_pokemon_record(pokemon_id: int, species_data: Dict, pokemon_data: Dict, generation: int) -> Dict:
        """
        Baue kompletten Pokémon-Record mit allen Feldern.
        
        Args:
            pokemon_id: Die Pokémon-ID
            species_data: Species-Daten von PokéAPI
            pokemon_data: Pokémon-Daten von PokéAPI
            generation: Die Generation (1-9)
            
        Returns:
            Kompletter Pokémon-Record
        """
        names = PokémonProcessor.extract_all_names(species_data)
        type1, type2 = PokémonProcessor.extract_types(pokemon_data)
        image_url = PokémonProcessor.extract_image_url(pokemon_data)
        
        return {
            'id': pokemon_id,
            'num': f'#{pokemon_id:03d}',
            **names,  # Spread all name_XX fields
            'type1': type1,
            'type2': type2,
            'image_url': image_url,
            'generation': generation,
        }
    
    @staticmethod
    def get_generation_for_pokemon(pokemon_id: int) -> int:
        """
        Bestimme die Generation für eine Pokémon-ID.
        
        Args:
            pokemon_id: Die Pokémon-ID (1-1025)
            
        Returns:
            Generation (1-9)
        """
        generation_ranges = {
            1: (1, 151), 2: (152, 251), 3: (252, 386),
            4: (387, 493), 5: (494, 649), 6: (650, 721),
            7: (722, 809), 8: (810, 905), 9: (906, 1025)
        }
        
        for gen, (start, end) in generation_ranges.items():
            if start <= pokemon_id <= end:
                return gen
        
        return 1  # Fallback
