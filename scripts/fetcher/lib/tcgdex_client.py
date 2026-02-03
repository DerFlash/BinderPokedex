"""
TCGdex API Client

HTTP client for interacting with the TCGdex API (https://tcgdex.dev).
Provides access to multilingual Pokemon TCG card data.

API Documentation: https://tcgdex.dev/rest
"""

import logging
import time
from typing import Dict, List, Optional, Any
from requests import Session, RequestException, Timeout

logger = logging.getLogger(__name__)


class TCGdexClient:
    """
    Client for the TCGdex API.
    
    TCGdex provides comprehensive Pokemon TCG card data in 10+ languages:
    - International: English, French, Spanish, Italian, Portuguese, German
    - Asian: Japanese, Chinese (Traditional), Indonesian, Thai
    
    Features:
    - Full card information with images
    - Sets, series, and rarities
    - TCG Pocket integration
    - Market prices (via separate API)
    - GraphQL support
    
    Rate limiting: ~10M requests/month free tier
    """
    
    BASE_URL = "https://api.tcgdex.net/v2"
    DEFAULT_TIMEOUT = 10  # seconds
    RATE_LIMIT_DELAY = 0.2  # seconds between requests
    MAX_RETRIES = 3
    
    def __init__(self, language: str = "en"):
        """
        Initialize the TCGdex client.
        
        Args:
            language: Language code (de, en, fr, es, it, pt, ja, zh, id, th)
        """
        self.language = language
        self.session = Session()
        self.session.headers.update({
            'User-Agent': 'BinderPokedex/5.0 (https://github.com/yourusername/BinderPokedex)',
            'Accept': 'application/json'
        })
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """
        Make a rate-limited request to the TCGdex API with retry logic.
        
        Args:
            endpoint: API endpoint path (e.g., "/cards")
            params: Query parameters
            
        Returns:
            Response JSON or None on error
        """
        url = f"{self.BASE_URL}/{self.language}{endpoint}"
        
        for attempt in range(self.MAX_RETRIES):
            try:
                self._rate_limit()
                response = self.session.get(url, params=params, timeout=self.DEFAULT_TIMEOUT)
                response.raise_for_status()
                return response.json()
            
            except Timeout:
                logger.warning(f"Request timeout for {url} (attempt {attempt + 1}/{self.MAX_RETRIES})")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
            except RequestException as e:
                # 404 for sets endpoints means language not available - don't retry
                # Retrying won't make the translation magically appear
                if e.response is not None and e.response.status_code == 404 and '/sets/' in endpoint:
                    logger.debug(f"Set not available in {self.language}: {url}")
                    return None  # Skip retries for missing translations
                
                logger.error(f"Request failed for {url}: {e}")
                
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                    
        return None
    
    def search_cards(self, 
                    name: Optional[str] = None,
                    hp: Optional[str] = None,
                    types: Optional[List[str]] = None,
                    page: int = 1,
                    limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """
        Search for cards with filters.
        
        Args:
            name: Card name to search for
            hp: HP filter (e.g., "gte:100", "lte:50", "100")
            types: List of Pokemon types (e.g., ["Fire", "Water"])
            page: Page number (1-indexed)
            limit: Results per page (max 250)
            
        Returns:
            List of card brief objects or None on error
            
        Example:
            # Search for Charizard cards with HP >= 100
            cards = client.search_cards(name="charizard", hp="gte:100")
        """
        params = {}
        if name:
            params['name'] = name
        if hp:
            params['hp'] = hp
        if types:
            params['types'] = ','.join(types)
        if page > 1:
            params['page'] = page
        if limit != 100:
            params['limit'] = limit
        
        return self._make_request("/cards", params)
    
    def get_card(self, card_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific card by ID.
        
        Args:
            card_id: Card ID (e.g., "base1-4")
            
        Returns:
            Full card object or None on error
        """
        return self._make_request(f"/cards/{card_id}")
    
    def get_card_from_set(self, set_id: str, local_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific card by set ID and local card ID.
        
        Args:
            set_id: Set ID (e.g., "base1")
            local_id: Local card number within set (e.g., "4")
            
        Returns:
            Full card object or None on error
        """
        return self._make_request(f"/sets/{set_id}/{local_id}")
    
    def get_sets(self, page: int = 1, limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """
        Get all TCG sets.
        
        Args:
            page: Page number (1-indexed)
            limit: Results per page (max 250)
            
        Returns:
            List of set brief objects or None on error
        """
        params = {}
        if page > 1:
            params['page'] = page
        if limit != 100:
            params['limit'] = limit
            
        return self._make_request("/sets", params)
    
    def get_set(self, set_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific set by ID.
        
        Args:
            set_id: Set ID (e.g., "base1", "ex1")
            
        Returns:
            Full set object with card list or None on error
        """
        return self._make_request(f"/sets/{set_id}")
    
    def get_series(self, page: int = 1, limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """
        Get all TCG series.
        
        Args:
            page: Page number (1-indexed)
            limit: Results per page (max 250)
            
        Returns:
            List of series brief objects or None on error
        """
        params = {}
        if page > 1:
            params['page'] = page
        if limit != 100:
            params['limit'] = limit
            
        return self._make_request("/series", params)
    
    def get_serie(self, serie_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific series by ID.
        
        Args:
            serie_id: Series ID (e.g., "base", "ex")
            
        Returns:
            Full series object with set list or None on error
        """
        return self._make_request(f"/series/{serie_id}")
    
    def fetch_cards_by_pokedex_range(self, 
                                     start: int = 1, 
                                     end: int = 151,
                                     filters: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        Fetch all cards for Pokemon within a National Pokedex range.
        
        Note: TCGdex doesn't have a direct nationalPokedexNumber filter like Pokemon TCG API.
        This method fetches cards page by page and would need to be filtered client-side
        or by using the card's name to match against known Pokemon.
        
        Args:
            start: Start of Pokedex range (inclusive)
            end: End of Pokedex range (inclusive)
            filters: Additional filters (e.g., {"hp": "gte:100"})
            
        Returns:
            List of matching cards
        """
        logger.info(f"Fetching cards for Pokedex #{start}-{end}")
        logger.warning("TCGdex doesn't support direct Pokedex filtering - consider using Pokemon TCG API instead")
        
        all_cards = []
        page = 1
        
        while True:
            params = {"page": page, "limit": 250}
            if filters:
                params.update(filters)
                
            cards = self._make_request("/cards", params)
            
            if not cards or len(cards) == 0:
                break
                
            all_cards.extend(cards)
            
            # If we got less than 250 results, we've reached the end
            if len(cards) < 250:
                break
                
            page += 1
            logger.info(f"Fetched page {page-1}, {len(all_cards)} cards total")
        
        logger.info(f"Retrieved {len(all_cards)} total cards")
        return all_cards
    
    def fetch_ex_cards(self, language: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch all EX-type cards.
        
        Note: TCGdex uses different data structure. EX cards might be identified
        by suffix in card name (e.g., "Charizard ex", "Charizard-EX").
        
        Args:
            language: Override client language for this request
            
        Returns:
            List of cards with "ex" or "EX" in the name
        """
        original_lang = self.language
        if language:
            self.language = language
        
        try:
            # This is a simplified approach - you may need to refine the search
            all_cards = []
            page = 1
            
            while True:
                cards = self.search_cards(page=page, limit=250)
                
                if not cards or len(cards) == 0:
                    break
                
                # Filter for cards with "ex" or "EX" in name
                ex_cards = [c for c in cards if ' ex' in c.get('name', '').lower() or '-ex' in c.get('name', '').lower()]
                all_cards.extend(ex_cards)
                
                if len(cards) < 250:
                    break
                    
                page += 1
            
            logger.info(f"Retrieved {len(all_cards)} EX cards")
            return all_cards
            
        finally:
            self.language = original_lang
