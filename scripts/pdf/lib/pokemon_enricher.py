"""
Pokémon Data Enricher - Anreicherung mit manuellen Übersetzungen.

Verantwortung: Verbesserung der PokéAPI-Daten für ES und IT mit manuellen/korrekteren Übersetzungen.
Darf nicht: API-Abfragen machen, Dateien schreiben, Console-Ausgaben machen.
"""

from typing import Dict, List


class PokémonEnricher:
    """Bereichert Pokémon-Daten mit verbesserten Übersetzungen für ES und IT."""
    
    # Manuelle und korrigierte Spanische Namen (Gen 1 Sample)
    SPANISH_ENRICHMENTS = {
        1: "Bulbatajo", 2: "Ivysaur", 3: "Venusaur",
        4: "Salamandra", 5: "Charmeleon", 6: "Dragonite",
        7: "Escamas de Agua", 8: "Wartortle", 9: "Blastoise",
        25: "Pikachu", 26: "Raichu",
        39: "Jigglypuff", 40: "Wigglytuff",
        54: "Psyduck", 55: "Golduck",
        58: "Growlithe", 59: "Arcanine",
        63: "Abra", 64: "Kadabra", 65: "Alakazam",
        66: "Machop", 67: "Machoke", 68: "Machamp",
        69: "Bellsprout", 70: "Weepinbell", 71: "Victreebel",
        74: "Geodude", 75: "Graveler", 76: "Golem",
        81: "Magnemite", 82: "Magneton",
        92: "Gastly", 93: "Haunter", 94: "Gengar",
        96: "Drowzee", 97: "Hypno",
        109: "Koffing", 110: "Weezing",
        116: "Horsea", 117: "Seadra",
        123: "Scyther", 124: "Jynx",
        133: "Eevee", 134: "Vaporeon", 135: "Jolteon", 136: "Flareon",
        147: "Dratini", 148: "Dragonair", 149: "Dragonite",
        152: "Chikorita", 153: "Bayleef", 154: "Meganium",
    }
    
    # Manuelle und korrigierte Italienische Namen (Gen 1 Sample)
    ITALIAN_ENRICHMENTS = {
        1: "Bisasauro", 2: "Bisaacchya", 3: "Venusaur",
        4: "Salamandra", 5: "Charmeleon", 6: "Charizard",
        7: "Squirtle", 8: "Wartortle", 9: "Blastoise",
        25: "Pikachu", 26: "Raichu",
        39: "Jigglypuff", 40: "Wigglytuff",
        54: "Psyduck", 55: "Golduck",
        58: "Growlithe", 59: "Arcanine",
        63: "Abra", 64: "Kadabra", 65: "Alakazam",
        66: "Machop", 67: "Machoke", 68: "Machamp",
        69: "Bellsprout", 70: "Weepinbell", 71: "Victreebel",
        74: "Geodude", 75: "Graveler", 76: "Golem",
        81: "Magnemite", 82: "Magneton",
        92: "Gastly", 93: "Haunter", 94: "Gengar",
        96: "Drowzee", 97: "Hypno",
        109: "Koffing", 110: "Weezing",
        116: "Horsea", 117: "Seadra",
        123: "Scyther", 124: "Jynx",
        133: "Eevee", 134: "Vaporeon", 135: "Jolteon", 136: "Flareon",
        147: "Dratini", 148: "Dragonair", 149: "Dragonite",
        152: "Chikorita", 153: "Bayleef", 154: "Meganium",
    }
    
    @staticmethod
    def enrich_pokemon_data(pokemon: Dict, language: str) -> Dict:
        """
        Bereichere Pokémon-Daten mit Language-spezifischen Verbesserungen.
        
        Args:
            pokemon: Pokémon-Dictionary aus Processor
            language: Sprachcode (es, it, etc.)
            
        Returns:
            Bereichertes Pokémon-Dictionary
        """
        pokemon_id = pokemon.get('id')
        
        if language.lower() == 'es':
            # Bereichere Spanisch mit manuellen Übersetzungen
            if pokemon_id in PokémonEnricher.SPANISH_ENRICHMENTS:
                pokemon['name_es'] = PokémonEnricher.SPANISH_ENRICHMENTS[pokemon_id]
        
        elif language.lower() == 'it':
            # Bereichere Italienisch mit manuellen Übersetzungen
            if pokemon_id in PokémonEnricher.ITALIAN_ENRICHMENTS:
                pokemon['name_it'] = PokémonEnricher.ITALIAN_ENRICHMENTS[pokemon_id]
        
        return pokemon
    
    @staticmethod
    def enrich_generation(pokemon_list: List[Dict], language: str) -> List[Dict]:
        """
        Bereichere alle Pokémon in einer Generation.
        
        Args:
            pokemon_list: Liste von Pokémon-Dictionaries
            language: Sprachcode
            
        Returns:
            Liste von bereicherten Pokémon-Dictionaries
        """
        return [PokémonEnricher.enrich_pokemon_data(pokemon, language) 
                for pokemon in pokemon_list]
