"""
Pokémon Data Storage - Persistente Speicherung in JSON.

Verantwortung: Laden und Speichern von Pokémon-Daten als JSON.
Darf nicht: API-Abfragen machen, Daten verarbeiten, Console-Ausgaben machen.
"""

import json
from pathlib import Path
from typing import List, Dict


class DataStorage:
    """Verwaltet Persistierung von Pokémon-Daten in JSON-Dateien."""
    
    def __init__(self, data_dir: Path = None):
        """
        Initialisiere Storage mit Datenverzeichnis.
        
        Args:
            data_dir: Pfad zum data-Verzeichnis. Wenn None, wird data/ neben diesem Script verwendet.
        """
        if data_dir is None:
            # Standard: data/ Verzeichnis neben dem Script
            script_dir = Path(__file__).parent.parent
            data_dir = script_dir.parent / "data"
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def get_data_dir(self) -> Path:
        """
        Gib das Datenverzeichnis zurück.
        
        Returns:
            Path zum data-Verzeichnis
        """
        return self.data_dir
    
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
    
    def load_generation(self, generation: int) -> List[Dict]:
        """
        Lade Pokémon-Daten für eine Generation.
        
        Args:
            generation: Generationsnummer (1-9)
            
        Returns:
            Liste von Pokémon-Dictionaries oder leere Liste wenn nicht vorhanden
        """
        input_file = self.data_dir / f"pokemon_gen{generation}.json"
        
        if not input_file.exists():
            return []
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
