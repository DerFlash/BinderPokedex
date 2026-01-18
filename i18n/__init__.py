#!/usr/bin/env python3
"""
Language/Internationalization utilities for Binder Pokédex.

Handles multi-language support for Pokémon names, types, regions, and UI text.
Supported languages: DE, EN, FR, ES, IT, JA, KO, ZH-Hans, ZH-Hant
"""

import json
from pathlib import Path
from typing import Optional


class I18nManager:
    """Manages translations and language-specific formatting."""

    def __init__(self):
        """Initialize the translation manager by loading JSON files."""
        i18n_dir = Path(__file__).parent
        
        with open(i18n_dir / "languages.json", "r", encoding="utf-8") as f:
            self.languages_config = json.load(f)
        
        with open(i18n_dir / "translations.json", "r", encoding="utf-8") as f:
            self.translations = json.load(f)

    def get_supported_languages(self) -> list[str]:
        """Return list of supported language codes."""
        return self.languages_config["supported_languages"]

    def get_pokemon_name(
        self, pokemon: dict, language: str, include_english_fallback: bool = False
    ) -> str:
        """
        Get Pokémon name in specified language.

        Args:
            pokemon: Pokemon data dictionary with name fields
            language: Language code (de, en, fr, es, it, ja, ko, zh-hans, zh-hant)
            include_english_fallback: If True and name not available, include English name

        Returns:
            Pokémon name in requested language
        """
        language = language.lower()
        
        # Validate language
        if language not in self.get_supported_languages():
            language = "en"
        
        # Map language codes to JSON keys in pokemon data
        name_field_map = {
            "de": "name_de",
            "en": "name_en",
            "fr": "name_fr",
            "es": "name_es",
            "it": "name_it",
            "ja": "name_ja",
            "ko": "name_ko",
            "zh-hans": "name_zh_hans",
            "zh-hant": "name_zh_hant",
        }
        
        field = name_field_map.get(language, "name_en")
        name = pokemon.get(field, "")
        
        # Fallback to English if not available
        if not name:
            name = pokemon.get("name_en", "")
        
        # Optional: include English name for non-English languages
        if include_english_fallback and language != "en" and name:
            english_name = pokemon.get("name_en", "")
            if english_name and english_name != name:
                name = f"{name} ({english_name})"
        
        return name

    def get_pokemon_names_for_card(
        self, pokemon: dict, language: str
    ) -> tuple[str, Optional[str]]:
        """
        Get Pokémon name(s) for card display.

        For English: only English name
        For other languages: language name (with English fallback in parentheses if different)

        Args:
            pokemon: Pokemon data dictionary
            language: Language code

        Returns:
            Tuple of (primary_name, secondary_name or None)
        """
        language = language.lower()
        
        if language not in self.get_supported_languages():
            language = "en"
        
        if language == "en":
            # English: only show English name
            return pokemon.get("name_en", ""), None
        else:
            # Other languages: show localized name and English as fallback
            primary = self.get_pokemon_name(pokemon, language, include_english_fallback=False)
            english = pokemon.get("name_en", "")
            
            if primary and english and primary != english:
                return primary, english
            return primary or english, None

    def get_type_name(self, type_en: str, language: str) -> str:
        """
        Get type name translated to specified language.

        Args:
            type_en: Type name in English (e.g., 'Fire', 'Water')
            language: Language code

        Returns:
            Type name in requested language
        """
        language = language.lower()
        
        if language not in self.get_supported_languages():
            language = "en"
        
        types = self.translations.get("types", {}).get(language, {})
        return types.get(type_en, type_en)

    def get_ui_text(self, key: str, language: str) -> str:
        """
        Get UI text translated to specified language.

        Args:
            key: Translation key (e.g., 'title', 'generation', 'pokemon_count')
            language: Language code

        Returns:
            Translated text or key if translation not found
        """
        language = language.lower()
        
        if language not in self.get_supported_languages():
            language = "en"
        
        ui_texts = self.translations.get("ui", {}).get(language, {})
        return ui_texts.get(key, key)

    def get_region_name(self, generation: int, language: str) -> str:
        """
        Get region name for a generation in specified language.

        Args:
            generation: Generation number (1-9)
            language: Language code

        Returns:
            Region name in requested language
        """
        language = language.lower()
        
        if language not in self.get_supported_languages():
            language = "en"
        
        regions = self.translations.get("regions", {}).get(language, {})
        return regions.get(str(generation), f"Generation {generation}")

    def normalize_language_code(self, language: str) -> str:
        """
        Normalize language code to valid supported language.

        Args:
            language: Language code (case-insensitive)

        Returns:
            Normalized language code
        """
        language = language.lower()
        
        if language not in self.get_supported_languages():
            return "en"
        
        return language


# Global instance for convenience
_i18n_instance: Optional[I18nManager] = None


def get_i18n() -> I18nManager:
    """Get or create global I18nManager instance."""
    global _i18n_instance
    
    if _i18n_instance is None:
        _i18n_instance = I18nManager()
    
    return _i18n_instance
