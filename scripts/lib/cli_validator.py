"""
CLI argument validation for PDF generation.

Centralizes validation logic for:
- Generation ranges (1-9, 1-3, etc.)
- Language codes
- Variant IDs
- Directory existence checks
"""

import json
import logging
from pathlib import Path
from typing import List, Set, Dict, Tuple, Optional

from .messages import ValidationMessages, format_message

logger: logging.Logger = logging.getLogger(__name__)


class GenerationValidator:
    """Validates and parses generation specifications."""
    
    MIN_GENERATION: int = 1
    MAX_GENERATION: int = 9
    
    @classmethod
    def parse_generation_range(cls, gen_spec: str) -> List[int]:
        """
        Parse generation specification string.
        
        Args:
            gen_spec: Generation specification (e.g., "1", "1-3", "1-9")
        
        Returns:
            List of valid generation numbers
        
        Raises:
            ValueError: If specification is invalid
        """
        gen_spec = gen_spec.strip()
        
        if '-' in gen_spec:
            parts = gen_spec.split('-')
            if len(parts) != 2:
                raise ValueError(format_message(ValidationMessages.INVALID_GENERATION_RANGE, range=gen_spec))
            
            try:
                start = int(parts[0].strip())
                end = int(parts[1].strip())
            except ValueError:
                raise ValueError(format_message(ValidationMessages.INVALID_GENERATION_FORMAT, value=gen_spec))
            
            if start < cls.MIN_GENERATION or end > cls.MAX_GENERATION:
                raise ValueError(
                    format_message(ValidationMessages.GENERATION_OUT_OF_BOUNDS, 
                                  min=cls.MIN_GENERATION, max=cls.MAX_GENERATION)
                )
            
            if start > end:
                raise ValueError(format_message(ValidationMessages.INVALID_GENERATION_RANGE, range=gen_spec))
            
            return list(range(start, end + 1))
        
        else:
            try:
                gen = int(gen_spec)
            except ValueError:
                raise ValueError(format_message(ValidationMessages.INVALID_GENERATION_FORMAT, value=gen_spec))
            
            if gen < cls.MIN_GENERATION or gen > cls.MAX_GENERATION:
                raise ValueError(
                    format_message(ValidationMessages.GENERATION_OUT_OF_BOUNDS,
                                  min=cls.MIN_GENERATION, max=cls.MAX_GENERATION)
                )
            
            return [gen]


class LanguageValidator:
    """Validates language codes."""
    
    # Supported languages
    SUPPORTED_LANGUAGES: Dict[str, str] = {
        'de': 'German',
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'it': 'Italian',
        'ja': 'Japanese',
        'ko': 'Korean',
        'zh-hans': 'Chinese (Simplified)',
        'zh-hant': 'Chinese (Traditional)',
    }
    
    @classmethod
    def validate(cls, language: str) -> bool:
        """
        Check if language code is supported.
        
        Args:
            language: Language code to validate
        
        Returns:
            True if valid, False otherwise
        """
        return language.lower() in cls.SUPPORTED_LANGUAGES
    
    @classmethod
    def get_supported(cls) -> Dict[str, str]:
        """Get all supported languages."""
        return cls.SUPPORTED_LANGUAGES.copy()
    
    @classmethod
    def normalize(cls, language: str) -> str:
        """
        Normalize language code to standard format.
        
        Args:
            language: Language code (may have underscores or mixed case)
        
        Returns:
            Normalized language code
        """
        # Convert underscores to hyphens for Chinese variants
        normalized = language.lower().replace('_', '-')
        return normalized


class VariantValidator:
    """Validates variant categories."""
    
    @classmethod
    def validate_variant_id(cls, variant_id: str, valid_ids: Set[str]) -> bool:
        """
        Check if variant ID is valid.
        
        Args:
            variant_id: Variant ID to validate
            valid_ids: Set of valid variant IDs
        
        Returns:
            True if valid, False otherwise
        """
        return variant_id.lower() in valid_ids
    
    @classmethod
    def parse_variant_spec(cls, variant_spec: str, valid_ids: Set[str]) -> Tuple[List[str], Optional[str]]:
        """
        Parse variant specification.
        
        Args:
            variant_spec: Variant specification ("all", "mega", "mega,gigantamax", etc.)
            valid_ids: Set of valid variant IDs
        
        Returns:
            Tuple of (variant_ids_to_generate, error_message)
            - First element is list of variant IDs if valid
            - Second element is None if valid, error message if invalid
        """
        if variant_spec.lower() == 'all':
            return list(sorted(valid_ids)), None
        
        # Parse comma-separated list
        variant_ids = [v.strip() for v in variant_spec.lower().split(',')]
        invalid_ids = [vid for vid in variant_ids if vid not in valid_ids]
        
        if invalid_ids:
            error = f"Unknown variant(s): {', '.join(invalid_ids)}"
            return [], error
        
        return variant_ids, None


class DirectoryValidator:
    """Validates directory and file existence."""
    
    @classmethod
    def check_data_dir(cls, data_dir: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate data directory exists.
        
        Args:
            data_dir: Path to data directory
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not data_dir.exists():
            return False, format_message(ValidationMessages.DATA_DIR_NOT_FOUND, path=data_dir)
        return True, None
    
    @classmethod
    def check_variants_dir(cls, variants_dir: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate variants directory and metadata.
        
        Args:
            variants_dir: Path to variants directory
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not variants_dir.exists():
            return False, format_message(ValidationMessages.VARIANTS_DIR_NOT_FOUND, path=variants_dir)
        
        meta_file = variants_dir / "meta.json"
        if not meta_file.exists():
            return False, format_message(ValidationMessages.VARIANTS_METADATA_NOT_FOUND, path=meta_file)
        
        return True, None
    
    @classmethod
    def load_variant_metadata(cls, variants_dir: Path) -> Tuple[Optional[dict], Optional[str]]:
        """
        Load and validate variant metadata.
        
        Args:
            variants_dir: Path to variants directory
        
        Returns:
            Tuple of (metadata_dict, error_message)
        """
        meta_file = variants_dir / "meta.json"
        
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            return meta, None
        except json.JSONDecodeError as e:
            return None, format_message(ValidationMessages.INVALID_JSON, path=meta_file, error=e)
        except Exception as e:
            return None, format_message(ValidationMessages.FILE_NOT_FOUND, file_type="Metadata file", path=meta_file)


class ValidationResult:
    """Container for validation results with error messages."""
    
    def __init__(self, is_valid: bool, error: Optional[str] = None) -> None:
        """
        Initialize validation result.
        
        Args:
            is_valid: Whether validation passed
            error: Error message if validation failed
        """
        self.is_valid: bool = is_valid
        self.error: Optional[str] = error
    
    def __bool__(self) -> bool:
        """Allow use in boolean context."""
        return self.is_valid
