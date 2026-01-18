"""
PokéAPI Client - HTTP-Kommunikation mit PokéAPI.

Verantwortung: API-Abfragen mit Rate Limiting und Fehlerbehandlung.
Darf nicht: Daten verarbeiten, Dateien schreiben, Console-Ausgaben machen.
"""

import requests
import time
from typing import Dict, Optional


class PokéAPIClient:
    """HTTP-Client für PokéAPI-Anfragen."""
    
    BASE_URL = "https://pokeapi.co/api/v2"
    RATE_LIMIT_DELAY = 0.05  # Sekunden zwischen Requests
    TIMEOUT = 5  # Sekunden pro Request
    
    def __init__(self):
        """Initialisiere den API-Client."""
        self.session = requests.Session()
        self.last_request_time = 0
    
    def _wait_for_rate_limit(self) -> None:
        """Warte um Rate-Limiting einzuhalten."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def fetch_species_data(self, pokemon_id: int) -> Optional[Dict]:
        """
        Fetch Species-Daten für ein Pokémon (enthält Namen in allen Sprachen).
        
        Args:
            pokemon_id: Die Pokémon-ID (1-1025)
            
        Returns:
            Dict mit Species-Daten oder None bei Fehler
        """
        try:
            self._wait_for_rate_limit()
            response = self.session.get(
                f"{self.BASE_URL}/pokemon-species/{pokemon_id}/",
                timeout=self.TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None
    
    def fetch_pokemon_data(self, pokemon_id: int) -> Optional[Dict]:
        """
        Fetch Pokémon-Daten (Types und Bilder).
        
        Args:
            pokemon_id: Die Pokémon-ID (1-1025)
            
        Returns:
            Dict mit Pokémon-Daten oder None bei Fehler
        """
        try:
            self._wait_for_rate_limit()
            response = self.session.get(
                f"{self.BASE_URL}/pokemon/{pokemon_id}/",
                timeout=self.TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None
