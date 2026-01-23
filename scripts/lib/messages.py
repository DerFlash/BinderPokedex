"""
Centralized message strings for consistent error and status messaging.

Consolidates commonly repeated messages across the codebase to ensure
consistency and simplify future updates to messaging.
"""

from typing import Optional


class ValidationMessages:
    """Messages for validation errors and warnings."""
    
    # Directory validation
    DATA_DIR_NOT_FOUND = "Data directory not found: {path}"
    VARIANTS_DIR_NOT_FOUND = "Variants directory not found: {path}"
    VARIANTS_METADATA_NOT_FOUND = "Variants metadata not found: {path}"
    VARIANT_METADATA_NOT_FOUND = "Variant metadata not found: {variant_id}"
    OUTPUT_DIR_CREATION_FAILED = "Failed to create output directory: {path}"
    
    # Language validation
    UNSUPPORTED_LANGUAGE = "Unsupported language: {language}"
    SUPPORTED_LANGUAGES = "Supported: {languages}"
    INVALID_LANGUAGE_CODE = "Invalid language code format: {code}"
    
    # Generation validation
    INVALID_GENERATION_RANGE = "Invalid generation range: {range}"
    GENERATION_OUT_OF_BOUNDS = "Generations must be between {min} and {max}"
    INVALID_GENERATION_FORMAT = "Generation must be integer or range (e.g., '1', '1-3'): {value}"
    
    # Variant validation
    UNKNOWN_VARIANT = "Unknown variant: {variant}"
    VALID_VARIANTS = "Valid variants: {variants}"
    INVALID_VARIANT_FORMAT = "Invalid variant specification: {spec}"
    
    # File validation
    FILE_NOT_FOUND = "{file_type} not found: {path}"
    INVALID_JSON = "Invalid JSON in {path}: {error}"
    PERMISSION_DENIED = "Permission denied: {path}"


class GenerationMessages:
    """Messages for PDF generation progress and results."""
    
    # Generation status
    GENERATING_POKÉDEX = "Generating Pokédex PDF"
    GENERATING_VARIANTS = "Generating variant PDFs"
    GENERATION_STARTED = "Generation started for {name}"
    GENERATION_COMPLETED = "Generation completed for {name}"
    GENERATION_FAILED = "Generation failed for {name}"
    GENERATION_SKIPPED = "Generation skipped for {name}"
    
    # Progress indicators
    PROCESSING_LANGUAGE = "Processing language: {language}"
    PROCESSING_VARIANT = "Processing variant: {variant}"
    PROCESSING_GENERATION = "Processing generation: {generation}"
    
    # Results
    TOTAL_GENERATED = "✅ Generated: {count}"
    TOTAL_FAILED = "❌ Failed: {count}"
    TOTAL_SKIPPED = "⏭️ Skipped: {count}"
    GENERATION_SUMMARY = "{generated} generated, {failed} failed"


class SystemMessages:
    """Messages for system-level operations."""
    
    # Font operations
    FONTS_REGISTERED = "Fonts registered successfully"
    FONT_REGISTRATION_FAILED = "Failed to register fonts: {error}"
    FONT_NOT_FOUND = "Font not found: {font}"
    FONT_RENDERING_WARNING = "Font rendering issue: {issue}"
    
    # Translation operations
    TRANSLATIONS_LOADED = "Translations loaded for language: {language}"
    TRANSLATION_LOAD_FAILED = "Failed to load translations: {error}"
    TRANSLATION_NOT_FOUND = "Translation not found for key: {key}"
    
    # Image operations
    IMAGE_CACHE_INITIALIZED = "Image cache initialized with {count} cached images"
    IMAGE_PROCESSING_FAILED = "Failed to process image for Pokémon {pokemon_id}: {error}"
    IMAGE_SKIPPED = "Skipped image processing"
    
    # Logging
    VERBOSE_MODE_ENABLED = "Verbose logging enabled"
    DEBUG_MODE_ENABLED = "Debug mode enabled"


class SuccessMessages:
    """Messages for successful operations."""
    
    PDF_GENERATED = "✅ PDF generated successfully: {filename}"
    VARIANTS_GENERATED = "✅ All variant PDFs generated successfully"
    ALL_LANGUAGES_GENERATED = "✅ All languages generated successfully"
    OPERATION_COMPLETED = "✅ Operation completed successfully"
    FILES_CREATED = "✅ Created {count} files"


class ErrorMessages:
    """Messages for error conditions."""
    
    UNEXPECTED_ERROR = "❌ Unexpected error: {error}"
    OPERATION_FAILED = "❌ Operation failed: {reason}"
    FILE_OPERATION_FAILED = "❌ File operation failed: {operation}"
    DEPENDENCY_MISSING = "❌ Missing dependency: {package}"
    CONFIGURATION_ERROR = "❌ Configuration error: {detail}"


class WarningMessages:
    """Messages for warnings."""
    
    PERFORMANCE_WARNING = "⚠️ Performance warning: {detail}"
    COMPATIBILITY_WARNING = "⚠️ Compatibility issue: {detail}"
    MISSING_OPTIONAL = "⚠️ Missing optional feature: {feature}"
    FALLBACK_USED = "⚠️ Using fallback: {fallback}"


def format_message(template: str, **kwargs) -> str:
    """
    Format a message template with provided arguments.
    
    Args:
        template: Message template with {placeholder} style formatting
        **kwargs: Values to substitute into template
    
    Returns:
        Formatted message string
    """
    try:
        return template.format(**kwargs)
    except KeyError as e:
        return f"[Format Error - Missing key {e}]: {template}"
    except Exception as e:
        return f"[Format Error - {e}]: {template}"
