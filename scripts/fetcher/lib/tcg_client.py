"""
Pokemon TCG API Client - HTTP communication with Pokemon TCG API.

Responsibility: API queries with rate limiting and error handling.
Must not: Process data, write files, make console outputs.
"""

import requests
import time
from typing import Dict, List, Optional


class PokemonTCGClient:
    """HTTP client for Pokemon TCG API requests via direct REST calls."""
    
    BASE_URL = "https://api.pokemontcg.io/v2"
    RATE_LIMIT_DELAY = 0.2  # Seconds between requests
    REQUEST_TIMEOUT = 30  # Timeout for single requests in seconds (TCG API can be slow)
    MAX_RETRIES = 3  # Maximum retry attempts on failure
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the API client.
        
        Args:
            api_key: Optional API key for higher rate limits
        """
        self.last_request_time = 0
        self.session = requests.Session()
        
        # Add API key to headers if provided
        if api_key:
            self.session.headers.update({
                'X-Api-Key': api_key
            })
    
    def _wait_for_rate_limit(self) -> None:
        """Wait to comply with rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make a request with retry logic.
        
        Args:
            endpoint: API endpoint (e.g., '/cards')
            params: Query parameters
            
        Returns:
            JSON response or None on error
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        for attempt in range(self.MAX_RETRIES):
            try:
                self._wait_for_rate_limit()
                response = self.session.get(
                    url, 
                    params=params,
                    timeout=self.REQUEST_TIMEOUT
                )
                response.raise_for_status()
                return response.json()
            except KeyboardInterrupt:
                raise  # Pass through user Ctrl+C
            except requests.exceptions.Timeout:
                if attempt == self.MAX_RETRIES - 1:
                    return None
                # Wait longer before retry
                time.sleep(2.0 * (attempt + 1))
            except Exception as e:
                if attempt == self.MAX_RETRIES - 1:
                    return None
                # Wait before retry
                time.sleep(1.0 * (attempt + 1))
        return None
    
    def search_cards(
        self, 
        query: str,
        page: int = 1,
        page_size: int = 250,
        order_by: Optional[str] = None,
        select: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Search for cards using query syntax.
        
        Args:
            query: Search query (e.g., 'subtypes:ex nationalPokedexNumbers:[1 TO 151]')
            page: Page number (default: 1)
            page_size: Results per page (max: 250)
            order_by: Field(s) to order by (e.g., 'name,-set.releaseDate')
            select: Comma-delimited fields to return (e.g., 'id,name')
            
        Returns:
            Dict with 'data', 'count', 'totalCount', 'page', 'pageSize' or None on error
        
        Examples:
            # Classic EX cards from Gen 1
            search_cards('subtypes:ex nationalPokedexNumbers:[1 TO 151]')
            
            # Modern EX cards from specific set
            search_cards('subtypes:EX set.id:xy1')
            
            # Cards with specific Pokemon name
            search_cards('name:charizard subtypes:ex')
        """
        params = {
            'q': query,
            'page': page,
            'pageSize': page_size
        }
        
        if order_by:
            params['orderBy'] = order_by
        if select:
            params['select'] = select
        
        return self._make_request('/cards', params)
    
    def get_card(self, card_id: str) -> Optional[Dict]:
        """
        Get a specific card by ID.
        
        Args:
            card_id: Card ID (e.g., 'xy1-1', 'ex1-103')
            
        Returns:
            Dict with card data or None on error
        """
        response = self._make_request(f'/cards/{card_id}')
        if response:
            return response.get('data')
        return None
    
    def fetch_classic_ex_cards(
        self,
        pokedex_range: str = "[1 TO 151]",
        page_size: int = 250
    ) -> List[Dict]:
        """
        Fetch all Classic EX cards (2003-2007) from specified Pokedex range.
        
        Args:
            pokedex_range: Range in format "[start TO end]" (default: Gen 1)
            page_size: Results per page
            
        Returns:
            List of all cards across all pages
        """
        query = f'subtypes:ex set.series:EX nationalPokedexNumbers:{pokedex_range}'
        all_cards = []
        page = 1
        
        while True:
            response = self.search_cards(
                query=query,
                page=page,
                page_size=page_size,
                order_by='nationalPokedexNumbers,set.releaseDate'
            )
            
            if not response or not response.get('data'):
                break
            
            cards = response['data']
            all_cards.extend(cards)
            
            # Check if there are more pages
            total_count = response.get('totalCount', 0)
            if len(all_cards) >= total_count:
                break
            
            page += 1
        
        return all_cards
    
    def fetch_modern_ex_cards(
        self,
        pokedex_range: str = "[1 TO 151]",
        page_size: int = 250
    ) -> List[Dict]:
        """
        Fetch all Modern EX cards (uppercase, XY/Sun&Moon era) from specified Pokedex range.
        
        Args:
            pokedex_range: Range in format "[start TO end]" (default: Gen 1)
            page_size: Results per page
            
        Returns:
            List of all cards across all pages
        """
        query = f'subtypes:EX nationalPokedexNumbers:{pokedex_range}'
        all_cards = []
        page = 1
        
        while True:
            response = self.search_cards(
                query=query,
                page=page,
                page_size=page_size,
                order_by='nationalPokedexNumbers,set.releaseDate'
            )
            
            if not response or not response.get('data'):
                break
            
            cards = response['data']
            all_cards.extend(cards)
            
            # Check if there are more pages
            total_count = response.get('totalCount', 0)
            if len(all_cards) >= total_count:
                break
            
            page += 1
        
        return all_cards
    
    def get_sets(self, page: int = 1, page_size: int = 250) -> Optional[Dict]:
        """
        Get list of card sets.
        
        Args:
            page: Page number
            page_size: Results per page (max: 250)
            
        Returns:
            Dict with 'data', 'count', 'totalCount' or None on error
        """
        params = {
            'page': page,
            'pageSize': page_size
        }
        return self._make_request('/sets', params)
    
    def get_set(self, set_id: str) -> Optional[Dict]:
        """
        Get a specific set by ID.
        
        Args:
            set_id: Set ID (e.g., 'xy1', 'ex1')
            
        Returns:
            Dict with set data or None on error
        """
        response = self._make_request(f'/sets/{set_id}')
        if response:
            return response.get('data')
        return None
