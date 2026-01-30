"""
PokeAPI Discovery - Dynamische Erkennung von Pokémon und Generationen.

Verantwortung: Automatische Erkennung neuer Pokémon, Generationen und Listen.
Darf nicht: Daten persistieren, Console-Ausgaben (außer Fehler).
"""

import pokebase as pb
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class GenerationInfo:
    """Information über eine Pokémon-Generation."""
    id: int
    name: str
    region: str
    start_id: int
    end_id: int
    pokemon_species_count: int


class PokeAPIDiscovery:
    """Dynamische Erkennung von PokeAPI-Inhalten."""
    
    @staticmethod
    def get_total_pokemon_count() -> int:
        """
        Ermittle die aktuelle Gesamtzahl der Pokémon von PokeAPI.
        
        Returns:
            Höchste verfügbare Pokémon-ID
        """
        try:
            # Query pokemon-species endpoint for count
            # The API's "count" field tells us the total number
            response = pb.APIResource('pokemon-species', limit=1)
            return response.count
        except Exception:
            # Fallback to known count
            return 1025
    
    @staticmethod
    def discover_generations() -> List[GenerationInfo]:
        """
        Entdecke alle verfügbaren Generationen von PokeAPI.
        
        Returns:
            Liste von GenerationInfo-Objekten
        """
        generations = []
        
        try:
            # Fetch all generations from API
            gen_list = pb.APIResourceList('generation')
            
            for gen_resource in gen_list:
                try:
                    gen = pb.generation(gen_resource.name)
                    
                    # Extract region name (main_region might be None for some)
                    region_name = gen.main_region.name.title() if gen.main_region else ""
                    
                    # Get pokemon species in this generation
                    species_list = gen.pokemon_species
                    
                    if not species_list:
                        continue
                    
                    # Extract IDs from species list
                    species_ids = [s.url.split('/')[-2] for s in species_list]
                    species_ids = [int(id) for id in species_ids if id.isdigit()]
                    
                    if not species_ids:
                        continue
                    
                    start_id = min(species_ids)
                    end_id = max(species_ids)
                    
                    generations.append(GenerationInfo(
                        id=gen.id,
                        name=gen.name.replace('-', ' ').title(),
                        region=region_name,
                        start_id=start_id,
                        end_id=end_id,
                        pokemon_species_count=len(species_ids)
                    ))
                except Exception:
                    continue
            
            # Sort by ID
            generations.sort(key=lambda g: g.id)
            return generations
            
        except Exception:
            # Fallback to hardcoded generations
            return PokeAPIDiscovery._get_fallback_generations()
    
    @staticmethod
    def _get_fallback_generations() -> List[GenerationInfo]:
        """Fallback zu bekannten Generationen wenn API nicht erreichbar."""
        return [
            GenerationInfo(1, "Generation I", "Kanto", 1, 151, 151),
            GenerationInfo(2, "Generation II", "Johto", 152, 251, 100),
            GenerationInfo(3, "Generation III", "Hoenn", 252, 386, 135),
            GenerationInfo(4, "Generation IV", "Sinnoh", 387, 493, 107),
            GenerationInfo(5, "Generation V", "Unova", 494, 649, 156),
            GenerationInfo(6, "Generation VI", "Kalos", 650, 721, 72),
            GenerationInfo(7, "Generation VII", "Alola", 722, 809, 88),
            GenerationInfo(8, "Generation VIII", "Galar", 810, 905, 96),
            GenerationInfo(9, "Generation IX", "Paldea", 906, 1025, 120),
        ]
    
    @staticmethod
    def get_pokemon_ids_for_generation(generation: int) -> List[int]:
        """
        Hole alle Pokémon-IDs für eine bestimmte Generation.
        
        Args:
            generation: Generationsnummer (1-9+)
            
        Returns:
            Liste von Pokémon-IDs in dieser Generation
        """
        try:
            gen = pb.generation(generation)
            species_list = gen.pokemon_species
            
            species_ids = []
            for species in species_list:
                # Extract ID from URL
                id_str = species.url.split('/')[-2]
                if id_str.isdigit():
                    species_ids.append(int(id_str))
            
            return sorted(species_ids)
        except Exception:
            # Fallback zu Ranges
            ranges = {
                1: range(1, 152),
                2: range(152, 252),
                3: range(252, 387),
                4: range(387, 494),
                5: range(494, 650),
                6: range(650, 722),
                7: range(722, 810),
                8: range(810, 906),
                9: range(906, 1026),
            }
            return list(ranges.get(generation, []))
    
    @staticmethod
    def check_pokemon_exists(pokemon_id: int) -> bool:
        """
        Prüfe, ob ein Pokémon mit dieser ID existiert.
        
        Args:
            pokemon_id: Die zu prüfende Pokémon-ID
            
        Returns:
            True wenn Pokémon existiert, False sonst
        """
        try:
            pb.pokemon(pokemon_id)
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_pokemon_in_version_group(version_group: str) -> List[int]:
        """
        Hole alle Pokémon-IDs, die in einer bestimmten Spielversion verfügbar sind.
        
        Beispiele für version_group: 
        - "red-blue", "gold-silver", "ruby-sapphire"
        - "sword-shield", "scarlet-violet"
        
        Args:
            version_group: Name der Version-Group
            
        Returns:
            Liste von Pokémon-IDs in dieser Version
        """
        try:
            vg = pb.version_group(version_group)
            
            # Get pokedexes for this version group
            pokemon_ids = set()
            
            for pokedex in vg.pokedexes:
                dex = pb.pokedex(pokedex.name)
                for entry in dex.pokemon_entries:
                    pokemon_id = entry.pokemon_species.url.split('/')[-2]
                    if pokemon_id.isdigit():
                        pokemon_ids.add(int(pokemon_id))
            
            return sorted(list(pokemon_ids))
        except Exception:
            return []
    
    @staticmethod
    def get_pokemon_by_type(type_name: str) -> List[int]:
        """
        Hole alle Pokémon-IDs eines bestimmten Typs.
        
        Args:
            type_name: Typname (z.B. "fire", "water", "electric")
            
        Returns:
            Liste von Pokémon-IDs mit diesem Typ
        """
        try:
            type_data = pb.type_(type_name)
            pokemon_ids = []
            
            for pokemon in type_data.pokemon:
                # Extract ID from URL
                id_str = pokemon.pokemon.url.split('/')[-2]
                if id_str.isdigit():
                    pokemon_ids.append(int(id_str))
            
            return sorted(pokemon_ids)
        except Exception:
            return []
    
    @staticmethod
    def validate_pokemon_list(pokemon_ids: List[int]) -> Tuple[List[int], List[int]]:
        """
        Validiere eine Liste von Pokémon-IDs gegen PokeAPI.
        
        Args:
            pokemon_ids: Liste zu validierender IDs
            
        Returns:
            Tuple (valid_ids, invalid_ids)
        """
        valid = []
        invalid = []
        
        for pokemon_id in pokemon_ids:
            if PokeAPIDiscovery.check_pokemon_exists(pokemon_id):
                valid.append(pokemon_id)
            else:
                invalid.append(pokemon_id)
        
        return valid, invalid
