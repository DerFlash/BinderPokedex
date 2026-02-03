"""
PokéAPI Client - HTTP-Kommunikation mit PokéAPI via direkte Requests.

Verantwortung: API-Abfragen mit Rate Limiting und Fehlerbehandlung.
Darf nicht: Daten verarbeiten, Dateien schreiben, Console-Ausgaben machen.
"""

import requests
import time
from typing import Dict, Optional


class PokéAPIClient:
    """HTTP-Client für PokéAPI-Anfragen via direkte REST calls."""
    
    BASE_URL = "https://pokeapi.co/api/v2"
    RATE_LIMIT_DELAY = 0.2  # Sekunden zwischen Requests
    REQUEST_TIMEOUT = 10  # Timeout für einzelne Requests in Sekunden
    MAX_RETRIES = 3  # Maximale Anzahl Wiederholungen bei Fehler
    
    def __init__(self):
        """Initialisiere den API-Client."""
        self.last_request_time = 0
        self.session = requests.Session()
    
    def _wait_for_rate_limit(self) -> None:
        """Warte um Rate-Limiting einzuhalten."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, url: str) -> Optional[Dict]:
        """
        Mache einen Request mit Retry-Logik.
        
        Args:
            url: Die URL für den Request
            
        Returns:
            JSON Response oder None bei Fehler
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                self._wait_for_rate_limit()
                response = self.session.get(url, timeout=self.REQUEST_TIMEOUT)
                response.raise_for_status()
                return response.json()
            except KeyboardInterrupt:
                raise  # User Ctrl+C durchlassen
            except Exception as e:
                if attempt == self.MAX_RETRIES - 1:
                    return None
                # Warte länger vor Retry
                time.sleep(1.0 * (attempt + 1))
        return None
    
    def fetch_species_data(self, pokemon_id: int) -> Optional[Dict]:
        """
        Fetch Species-Daten für ein Pokémon (enthält Namen in allen Sprachen).
        
        Args:
            pokemon_id: Die Pokémon-ID (1-1025)
            
        Returns:
            Dict mit Species-Daten oder None bei Fehler
        """
        url = f"{self.BASE_URL}/pokemon-species/{pokemon_id}"
        data = self._make_request(url)
        
        if not data:
            return None
        
        # Extrahiere relevante Daten
        return {
            'id': data['id'],
            'name': data['name'],
            'names': data.get('names', []),
            'genera': data.get('genera', []),
            'generation': data.get('generation', {}),
            'is_legendary': data.get('is_legendary', False),
            'is_mythical': data.get('is_mythical', False),
        }
    
    def fetch_pokemon_data(self, pokemon_id: int) -> Optional[Dict]:
        """
        Fetch Pokémon-Daten (Types und Bilder).
        
        Args:
            pokemon_id: Die Pokémon-ID (1-1025)
            
        Returns:
            Dict mit Pokémon-Daten oder None bei Fehler
        """
        url = f"{self.BASE_URL}/pokemon/{pokemon_id}"
        data = self._make_request(url)
        
        if not data:
            return None
        
        # Extrahiere relevante Daten
        return {
            'id': data['id'],
            'name': data['name'],
            'types': data.get('types', []),
            'sprites': data.get('sprites', {}),
        }
    
    def fetch_type_data(self, type_name: str) -> Optional[Dict]:
        """
        Fetch Pokemon type data including translations.
        
        Args:
            type_name: Type name in English (e.g., 'fire', 'water')
        
        Returns:
            Dict with type data including names array, or None on error
        """
        url = f"{self.BASE_URL}/type/{type_name}"
        return self._make_request(url)
