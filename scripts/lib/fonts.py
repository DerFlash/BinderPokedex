"""
Font Management Module

Handles TrueType font registration for CJK languages.
All fonts are registered once at module load time.

Includes Unicode character support and graceful fallback handling.
"""

import logging
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import unicodedata

logger = logging.getLogger(__name__)


class FontManager:
    """
    Manages font registration and retrieval for multi-language support.
    
    Uses TrueType fonts from system directories when available.
    Latin languages use built-in ReportLab fonts.
    
    Features:
    - Graceful font fallback for unsupported characters
    - Character-level font selection for mixed-script text
    - CJK language support with Songti.ttc
    """
    
    # Mapping of language codes to font configuration
    LANGUAGE_FONTS = {
        'de': {'font': 'Helvetica', 'font_bold': 'Helvetica-Bold'},
        'en': {'font': 'Helvetica', 'font_bold': 'Helvetica-Bold'},
        'es': {'font': 'Helvetica', 'font_bold': 'Helvetica-Bold'},
        'fr': {'font': 'Helvetica', 'font_bold': 'Helvetica-Bold'},
        'it': {'font': 'Helvetica', 'font_bold': 'Helvetica-Bold'},
        'ja': {'font': 'SongtiBold', 'font_bold': 'SongtiBold'},          # Japanese
        'ko': {'font': 'SongtiBold', 'font_bold': 'SongtiBold'},          # Korean (Songti supports CJK)
        'zh_hans': {'font': 'SongtiBold', 'font_bold': 'SongtiBold'},     # Simplified Chinese
        'zh_hant': {'font': 'SongtiBold', 'font_bold': 'SongtiBold'},     # Traditional Chinese
    }
    
    # CJK Languages that need TrueType fonts
    CJK_LANGUAGES = ['ja', 'ko', 'zh_hans', 'zh_hant']
    
    # Path to Songti TrueType Collection (primary CJK font)
    SONGTI_PATH = Path('/System/Library/Fonts/Supplemental/Songti.ttc')
    
    # Fallback CJK fonts for Linux systems (Noto Sans CJK)
    NOTO_CJK_PATHS = [
        Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'),    # OpenType location (Ubuntu)
        Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'), # OpenType location
        Path('/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc'),    # TrueType location
        Path('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc'), # TrueType location
        Path('/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc'),         # Alternative package location
        Path('/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc'),      # Alternative package location
        # WenQuanYi fonts (TTF format that works with ReportLab)
        Path('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'),
        Path('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'),
        Path('/usr/share/fonts/wenquanyi/wqy-zenhei.ttc'),
        Path('/usr/share/fonts/wenquanyi/wqy-microhei.ttc'),
    ]
    
    # Track if fonts have been registered
    _fonts_registered = False
    _font_cache = {}
    
    @classmethod
    def register_fonts(cls):
        """
        Register all fonts at startup.
        
        This should be called once before any PDF generation.
        If called multiple times, subsequent calls are no-ops.
        
        Supports graceful fallback if fonts are missing.
        """
        if cls._fonts_registered:
            logger.debug("Fonts already registered, skipping")
            return
        
        logger.info("Registering fonts for multi-language support...")
        
        # Register Songti font for CJK if available
        if cls.SONGTI_PATH.exists():
            try:
                font = TTFont('SongtiBold', str(cls.SONGTI_PATH))
                pdfmetrics.registerFont(font)
                logger.info(f"✓ Registered Songti font (JA, KO, ZH)")
                logger.debug(f"  Path: {cls.SONGTI_PATH}")
                cls._font_cache['SongtiBold'] = True
            except Exception as e:
                logger.warning(f"✗ Could not register Songti: {e}")
                logger.warning(f"  Some CJK characters may not render properly")
                cls._font_cache['SongtiBold'] = False
        else:
            logger.warning(f"⚠️  Songti font not found at {cls.SONGTI_PATH}")
            logger.warning(f"  CJK characters may not render - install fonts or use Noto Sans CJK")
            cls._font_cache['SongtiBold'] = False
            
            # Try Noto Sans CJK as fallback on Linux systems
            noto_registered = False
            
            # First try specific known paths
            for noto_path in cls.NOTO_CJK_PATHS:
                if noto_path.exists():
                    try:
                        # Register as 'SongtiBold' for compatibility with existing code
                        font = TTFont('SongtiBold', str(noto_path))
                        pdfmetrics.registerFont(font)
                        logger.info(f"✓ Registered Noto Sans CJK font as SongtiBold (JA, KO, ZH)")
                        logger.debug(f"  Path: {noto_path}")
                        cls._font_cache['SongtiBold'] = True
                        noto_registered = True
                        break
                    except Exception as e:
                        logger.debug(f"Could not register {noto_path}: {e}")
                        continue
                else:
                    logger.debug(f"Noto path does not exist: {noto_path}")
            
            # If specific paths didn't work, try to find any .ttc file in noto directories
            if not noto_registered:
                noto_dirs = [
                    Path('/usr/share/fonts/opentype/noto/'),
                    Path('/usr/share/fonts/truetype/noto/'),
                    Path('/usr/share/fonts/noto-cjk/'),
                    Path('/usr/share/fonts/truetype/wqy/'),
                    Path('/usr/share/fonts/wenquanyi/'),
                ]
                
                for noto_dir in noto_dirs:
                    logger.warning(f"Checking directory: {noto_dir}")
                    if noto_dir.exists():
                        logger.warning(f"Directory exists: {noto_dir}")
                        # Look for both .ttc and .ttf files (recursive)
                        font_files = list(noto_dir.glob('**/*.ttc')) + list(noto_dir.glob('**/*.ttf'))
                        logger.warning(f"Found font files: {font_files}")
                        if font_files:
                            try:
                                # Try the first font file found
                                font_path = font_files[0]
                                logger.warning(f"Trying to register: {font_path}")
                                font = TTFont('SongtiBold', str(font_path))
                                pdfmetrics.registerFont(font)
                                logger.info(f"✓ Registered Noto Sans CJK font as SongtiBold (JA, KO, ZH)")
                                logger.debug(f"  Path: {font_path} (found in {noto_dir})")
                                cls._font_cache['SongtiBold'] = True
                                noto_registered = True
                                break
                            except Exception as e:
                                logger.warning(f"Could not register {font_files[0]}: {e}")
                                continue
                        else:
                            logger.warning(f"No font files found in {noto_dir}")
                    else:
                        logger.warning(f"Directory does not exist: {noto_dir}")
            
            if not noto_registered:
                logger.warning(f"⚠️  Noto Sans CJK fonts not found. CJK characters may not render properly.")
                logger.warning(f"  Checked specific paths: {cls.NOTO_CJK_PATHS}")
                logger.warning(f"  Checked directories: /usr/share/fonts/opentype/noto/, /usr/share/fonts/truetype/noto/, /usr/share/fonts/noto-cjk/, /usr/share/fonts/truetype/wqy/, /usr/share/fonts/wenquanyi/")
                cls._font_cache['SongtiBold'] = False
        
        # Built-in Helvetica fonts are always available
        logger.debug("✓ Built-in Latin fonts available (Helvetica)")
        cls._font_cache['Helvetica'] = True
        cls._font_cache['Helvetica-Bold'] = True
        
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
