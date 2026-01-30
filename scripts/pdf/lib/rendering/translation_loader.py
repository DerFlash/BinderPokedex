"""
Translation Loader - Centralized i18n loading with caching

Provides unified access to type translations and UI strings across all
PDF rendering modules (Generation PDFs, Variant PDFs, etc.).

Features:
- Centralized translation file loading
- Type translation caching for performance
- UI string translation caching
- Robust path resolution using .resolve()
- Fallback to English if translation missing
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TranslationLoader:
    """Centralized translation loading with caching."""
    
    # Class-level cache for translations
    _cache: Dict[str, Dict] = {}
    _translations_path: Optional[Path] = None
    
    @classmethod
    def _get_translations_path(cls) -> Path:
        """
        Get absolute path to translations.json.
        
        Uses .resolve() for robust absolute path resolution that works
        regardless of where the script is executed from.
        
        Returns:
            Path to i18n/translations.json
        """
        if cls._translations_path is None:
            # Get absolute path of this file
            loader_file = Path(__file__).resolve()
            # Navigate: translation_loader.py -> rendering/ -> lib/ -> pdf/ -> scripts/ -> root/
            # Path: ...BinderPokedex/scripts/pdf/lib/rendering/translation_loader.py
            # Need to go up 5 levels to root, then into i18n/
            cls._translations_path = loader_file.parent.parent.parent.parent.parent / 'i18n' / 'translations.json'
            
            logger.debug(f"TranslationLoader path: {loader_file}")
            logger.debug(f"i18n path resolved to: {cls._translations_path}")
        
        return cls._translations_path
    
    @classmethod
    def load_types(cls, language: str = 'en') -> Dict[str, str]:
        """
        Load type translations for a specific language.
        
        Pokémon types (Water, Fire, etc.) are translated to the target language.
        Results are cached for performance.
        
        Args:
            language: Language code (e.g., 'en', 'de', 'fr', 'es', 'it', 'ja', 'ko', 'zh_hans', 'zh_hant')
        
        Returns:
            Dictionary mapping English type names to translated type names
            Returns empty dict if language not found or file doesn't exist
        """
        cache_key = f"types_{language}"
        
        # Return from cache if available
        if cache_key in cls._cache:
            logger.debug(f"TranslationLoader: Using cached type translations for '{language}'")
            return cls._cache[cache_key]
        
        try:
            translations_path = cls._get_translations_path()
            
            if not translations_path.exists():
                logger.warning(f"TranslationLoader: Translations file not found at {translations_path}")
                cls._cache[cache_key] = {}
                return {}
            
            with open(translations_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Get types for language, fallback to 'en' if not found
            types_data = data.get('types', {})
            result = types_data.get(language, types_data.get('en', {}))
            
            # Cache the result
            cls._cache[cache_key] = result
            logger.debug(f"TranslationLoader: Loaded {len(result)} type translations for '{language}'")
            return result
            
        except Exception as e:
            logger.warning(f"TranslationLoader: Error loading type translations: {e}")
            cls._cache[cache_key] = {}
            return {}
    
    @classmethod
    def load_ui(cls, language: str = 'en') -> Dict[str, str]:
        """
        Load UI string translations for a specific language.
        
        UI strings (labels, buttons, etc.) are translated to the target language.
        Results are cached for performance.
        
        Args:
            language: Language code (e.g., 'en', 'de', 'fr', 'es', 'it', 'ja', 'ko', 'zh_hans', 'zh_hant')
        
        Returns:
            Dictionary mapping English UI strings to translated UI strings
            Returns empty dict if language not found or file doesn't exist
        """
        cache_key = f"ui_{language}"
        
        # Return from cache if available
        if cache_key in cls._cache:
            logger.debug(f"TranslationLoader: Using cached UI translations for '{language}'")
            return cls._cache[cache_key]
        
        try:
            translations_path = cls._get_translations_path()
            
            if not translations_path.exists():
                logger.warning(f"TranslationLoader: Translations file not found at {translations_path}")
                cls._cache[cache_key] = {}
                return {}
            
            with open(translations_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Get UI strings for language, fallback to 'en' if not found
            ui_data = data.get('ui', {})
            result = ui_data.get(language, ui_data.get('en', {}))
            
            # Cache the result
            cls._cache[cache_key] = result
            logger.debug(f"TranslationLoader: Loaded {len(result)} UI translations for '{language}'")
            return result
            
        except Exception as e:
            logger.warning(f"TranslationLoader: Error loading UI translations: {e}")
            cls._cache[cache_key] = {}
            return {}
    
    @classmethod
    def get_type_translation(cls, english_type: str, language: str = 'en', fallback: Optional[str] = None) -> str:
        """
        Get translated name for a single Pokémon type.
        
        Convenience method for translating a single type name.
        
        Args:
            english_type: English type name (e.g., 'Water', 'Fire')
            language: Target language code
            fallback: Fallback text if translation not found (defaults to english_type)
        
        Returns:
            Translated type name, or fallback/english_type if not found
        """
        if fallback is None:
            fallback = english_type
        
        type_translations = cls.load_types(language)
        return type_translations.get(english_type, fallback)
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached translations. Useful for testing."""
        cls._cache.clear()
        logger.debug("TranslationLoader: Cache cleared")
