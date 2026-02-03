"""
CLI output formatter for consistent, clean command-line presentation.

Provides utilities for:
- Section headers with separators
- Progress messages
- Status messages (success, error, warning)
- Formatted lists and tables
- Verbose/quiet output modes
"""

from typing import List, Optional
from enum import Enum


class MessageLevel(Enum):
    """Message severity levels."""
    INFO = "ℹ️"
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    DEBUG = "🔧"


class CLIFormatter:
    """Utilities for consistent CLI output formatting."""
    
    # Standard separator width
    SEPARATOR_WIDTH = 80
    SEPARATOR_CHAR = "="
    
    @classmethod
    def section_header(cls, title: str, subtitle: Optional[str] = None) -> None:
        """
        Print a formatted section header with separator lines.
        
        Args:
            title: Main title text
            subtitle: Optional subtitle to display below title
        """
        sep = cls.SEPARATOR_CHAR * cls.SEPARATOR_WIDTH
        print(f"\n{sep}")
        print(f"{title}")
        if subtitle:
            print(f"{subtitle}")
        print(f"{sep}")
    
    @classmethod
    def section_footer(cls) -> None:
        """Print a footer separator."""
        print(f"{cls.SEPARATOR_CHAR * cls.SEPARATOR_WIDTH}\n")
    
    @classmethod
    def message(cls, level: MessageLevel, text: str, indent: int = 0) -> None:
        """
        Print a formatted message with icon and indentation.
        
        Args:
            level: Message severity level (determines icon)
            text: Message text
            indent: Number of spaces to indent
        """
        prefix = "  " * indent
        print(f"{prefix}{level.value} {text}")
    
    @classmethod
    def success(cls, text: str, indent: int = 0) -> None:
        """Print success message."""
        cls.message(MessageLevel.SUCCESS, text, indent)
    
    @classmethod
    def error(cls, text: str, indent: int = 0) -> None:
        """Print error message."""
        cls.message(MessageLevel.ERROR, text, indent)
    
    @classmethod
    def warning(cls, text: str, indent: int = 0) -> None:
        """Print warning message."""
        cls.message(MessageLevel.WARNING, text, indent)
    
    @classmethod
    def info(cls, text: str, indent: int = 0) -> None:
        """Print info message."""
        cls.message(MessageLevel.INFO, text, indent)
    
    @classmethod
    def debug(cls, text: str, indent: int = 0) -> None:
        """Print debug message."""
        cls.message(MessageLevel.DEBUG, text, indent)
    
    @classmethod
    def key_value(cls, key: str, value: str, indent: int = 0) -> None:
        """
        Print a key-value pair.
        
        Args:
            key: Key name
            value: Value to display
            indent: Number of spaces to indent
        """
        prefix = "  " * indent
        print(f"{prefix}{key:15s} {value}")
    
    @classmethod
    def list_items(cls, title: str, items: List[str], indent: int = 0) -> None:
        """
        Print a formatted list of items.
        
        Args:
            title: List title
            items: Items to display
            indent: Number of spaces to indent
        """
        prefix = "  " * indent
        print(f"{prefix}{title}")
        for item in items:
            print(f"{prefix}  • {item}")
    
    @classmethod
    def inline_list(cls, title: str, items: List[str]) -> str:
        """
        Create an inline comma-separated list.
        
        Args:
            title: List title
            items: Items to include
        
        Returns:
            Formatted string like "Title: item1, item2, item3"
        """
        return f"{title}: {', '.join(items)}"
    
    @classmethod
    def progress_summary(cls, generated: int, failed: int) -> None:
        """
        Print a summary of generation results.
        
        Args:
            generated: Number of successfully generated items
            failed: Number of failed items
        """
        cls.section_header("Summary")
        cls.success(f"Generated: {generated}")
        if failed > 0:
            cls.error(f"Failed: {failed}")
        else:
            cls.success(f"Failed: {failed}")
        cls.section_footer()
