"""
Font Management Module

Handles TrueType font registration for CJK languages.
All fonts are registered once at module load time.
"""

import logging
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)


class FontManager:
    """
    Manages font registration and retrieval for multi-language support.
    
    Uses TrueType fonts from system directories when available.
    Latin languages use built-in ReportLab fonts.
    """
    
    # Mapping of language codes to font configuration
    LANGUAGE_FONTS = {
        'de': {'font': 'Helvetica', 'font_bold': 'Helvetica-Bold'},
        'en': {'font': 'Helvetica', 'font_bold': 'Helvetica-Bold'},
        'es': {'font': 'Helvetica', 'font_bold': 'Helvetica-Bold'},
        'fr': {'font': 'Helvetica', 'font_bold': 'Helvetica-Bold'},
        'it': {'font': 'Helvetica', 'font_bold': 'Helvetica-Bold'},
        'ja': {'font': 'SongtiBold', 'font_bold': 'SongtiBold'},          # Japanese
        'ko': {'font': 'AppleGothicRegular', 'font_bold': 'AppleGothicRegular'},  # Korean (AppleGothic TTF)
        'zh_hans': {'font': 'SongtiBold', 'font_bold': 'SongtiBold'},     # Simplified Chinese
        'zh_hant': {'font': 'SongtiBold', 'font_bold': 'SongtiBold'},     # Traditional Chinese
    }
    
    # CJK Languages that need TrueType fonts
    CJK_LANGUAGES = ['ja', 'ko', 'zh_hans', 'zh_hant']
    
    # Path to Songti TrueType Collection
    SONGTI_PATH = Path('/System/Library/Fonts/Supplemental/Songti.ttc')
    
    # Path to AppleGothic for Korean (TTF, not TTC)
    APPLE_GOTHIC_PATH = Path('/System/Library/Fonts/Supplemental/AppleGothic.ttf')
    
    # Track if fonts have been registered
    _fonts_registered = False
    
    @classmethod
    def register_fonts(cls):
        """
        Register all fonts at startup.
        
        This should be called once before any PDF generation.
        If called multiple times, subsequent calls are no-ops.
        """
        if cls._fonts_registered:
            logger.debug("Fonts already registered, skipping")
            return
        
        logger.info("Registering fonts for multi-language support...")
        
        successful = 0
        
        # Register Songti font for CJK if available
        if cls.SONGTI_PATH.exists():
            try:
                font = TTFont('SongtiBold', str(cls.SONGTI_PATH))
                pdfmetrics.registerFont(font)
                logger.info(f"✓ Registered Songti font (JA, ZH)")
                logger.debug(f"  Path: {cls.SONGTI_PATH}")
                successful += 1
            except Exception as e:
                logger.warning(f"✗ Could not register Songti: {e}")
        else:
            logger.warning(f"⚠️  Songti font not found at {cls.SONGTI_PATH}")
        
        # Register AppleGothic for Korean
        if cls.APPLE_GOTHIC_PATH.exists():
            try:
                font = TTFont('AppleGothicRegular', str(cls.APPLE_GOTHIC_PATH))
                pdfmetrics.registerFont(font)
                logger.info(f"✓ Registered AppleGothic font (KO)")
                logger.debug(f"  Path: {cls.APPLE_GOTHIC_PATH}")
                successful += 1
            except Exception as e:
                logger.warning(f"✗ Could not register AppleGothic: {e}")
        else:
            logger.warning(f"⚠️  AppleGothic font not found")
        
        # Built-in Helvetica fonts are always available
        logger.debug("✓ Built-in Latin fonts available (Helvetica)")
        successful += 1
        
        cls._fonts_registered = True
        logger.info(f"Font registration complete")
    
    @classmethod
    def get_font_name(cls, language: str, bold: bool = False) -> str:
        """
        Get the appropriate font name for a language.
        
        Args:
            language: Language code (e.g., 'de', 'ja', 'zh_hans')
            bold: If True, returns bold variant (if available)
        
        Returns:
            Font name suitable for ReportLab
        
        Raises:
            ValueError: If language is not supported
        """
        if language not in cls.LANGUAGE_FONTS:
            raise ValueError(f"Unsupported language: {language}. "
                           f"Supported: {', '.join(cls.LANGUAGE_FONTS.keys())}")
        
        font_info = cls.LANGUAGE_FONTS[language]
        font_key = 'font_bold' if bold else 'font'
        return font_info[font_key]
    
    @classmethod
    def get_supported_languages(cls) -> list:
        """Get list of all supported languages."""
        return list(cls.LANGUAGE_FONTS.keys())
    
    @classmethod
    def is_cjk_language(cls, language: str) -> bool:
        """Check if language is CJK."""
        return language in cls.CJK_LANGUAGES


# Register fonts when module is imported
FontManager.register_fonts()
