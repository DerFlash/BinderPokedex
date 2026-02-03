"""
Pokémon Data Storage - Persistente Speicherung in JSON.

Verantwortung: Laden und Speichern von Pokémon-Daten als JSON.
Darf nicht: API-Abfragen machen, Daten verarbeiten, Console-Ausgaben machen.

Format: Unified consolidated format with pokemon.json containing all generations as sections.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional


class DataStorage:
    """Verwaltet Persistierung von Pokémon-Daten in JSON-Dateien."""
    
    def __init__(self, data_dir: Path = None):
        """
        Initialisiere Storage mit Datenverzeichnis.
        
        Args:
            data_dir: Pfad zum data-Verzeichnis. Wenn None, wird data/ neben diesem Script verwendet.
        """
        if data_dir is None:
            # Standard: data/output/ Verzeichnis im Projekt-Root
            # scripts/pdf/lib/data_storage.py -> data/output/
            script_dir = Path(__file__).parent.parent.parent.parent
            data_dir = script_dir / "data" / "output"
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._consolidated_data = None  # Cache for consolidated pokemon.json
    
    def get_data_dir(self) -> Path:
        """
        Gib das Datenverzeichnis zurück.
        
        Returns:
            Path zum data-Verzeichnis
        """
        return self.data_dir
    
    def _load_consolidated(self) -> Optional[dict]:
        """
        Load consolidated Pokedex.json file (cached).
        
        Returns:
            Consolidated data dict or None if not found
        """
        if self._consolidated_data is not None:
            return self._consolidated_data
        
        consolidated_file = self.data_dir / "Pokedex.json"
        if not consolidated_file.exists():
            return None
        
        try:
            with open(consolidated_file, 'r', encoding='utf-8') as f:
                self._consolidated_data = json.load(f)
            return self._consolidated_data
        except (json.JSONDecodeError, IOError):
            return None
    
    def load_generation(self, generation: int) -> List[Dict]:
        """
        Lade Pokémon-Daten für eine Generation aus konsolidierter Datei.
        
        Args:
            generation: Generationsnummer (1-9)
            
        Returns:
            Liste von Pokémon-Dictionaries oder leere Liste wenn nicht vorhanden
        """
        consolidated = self._load_consolidated()
        if not consolidated:
            return []
        
        section_key = f'gen{generation}'
        if section_key in consolidated.get('sections', {}):
            section = consolidated['sections'][section_key]
            return section.get('cards', [])
        
        return []
    
    def load_generation_info(self, generation: int) -> Dict:
        """
        Lade Generation Metadaten (name, region, range, iconic_pokemon).
        
        Args:
            generation: Generationsnummer (1-9)
            
        Returns:
            Dict mit generation_info oder leeres Dict wenn nicht vorhanden
        """
        consolidated = self._load_consolidated()
        if not consolidated:
            return {}
        
        section_key = f'gen{generation}'
        if section_key in consolidated.get('sections', {}):
            section = consolidated['sections'][section_key]
            # Build generation_info from section metadata
            cards = section.get('cards', [])
            pokemon_count = len(cards)
            return {
                'name': section.get('name', f'Generation {generation}'),
                'region': section.get('region', ''),
                'count': pokemon_count,  # Calculated from actual pokemon list
                'range': section.get('range', [0, 0]),
                'featured_pokemon': section.get('featured_pokemon', [])
            }
        
        return {}
    
    def save_generation(self, generation: int, pokemon_list: List[Dict]) -> Path:
        """
        Speichere Pokémon-Daten für eine Generation.
        
        Args:
            generation: Generationsnummer (1-9)
            pokemon_list: Liste von Pokémon-Dictionaries
            
        Returns:
            Path zur gespeicherten Datei
        """
        output_file = self.data_dir / f"pokemon_gen{generation}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(pokemon_list, f, indent=2, ensure_ascii=False)
        
        return output_file
