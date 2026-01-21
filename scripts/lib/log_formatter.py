"""
Unified Logging & Status Formatter

Provides consistent, readable output formatting for all PDF generators.
Used by PDFGenerator, VariantPDFGenerator, and PokedexGenerator.

Features:
- Single-line live progress updates with carriage return
- Clean status markers (✅ ❌ ⏳ 📊)
- Section headers with visual separators
- Consistent indentation and alignment
- Summary reports
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PDFStatus:
    """Track and format PDF generation status and progress with live updates."""
    
    def __init__(self, name: str, total_items: int):
        """
        Initialize status tracker.
        
        Args:
            name: Name of the generation (e.g., "Pokédex Gen 1-9")
            total_items: Total Pokémon to process
        """
        self.name = name
        self.total_items = total_items
        self.processed = 0
        self.failed = 0
        self.file_size_mb = 0.0
        self.page_count = 0
    
    def update(self, message_or_count=None, progress_pct=None):
        """
        Update progress.
        
        Args:
            message_or_count: Count (int) to add to progress
            progress_pct: Optional progress percentage (0-100) - sets absolute progress
        """
        if progress_pct is not None and isinstance(progress_pct, (int, float)):
            self.processed = int((progress_pct / 100) * self.total_items)
        elif isinstance(message_or_count, (int, float)):
            self.processed = min(self.processed + int(message_or_count), self.total_items)
    
    def progress_bar(self, width: int = 25) -> str:
        """
        Get progress bar string.
        
        Returns:
            "[████░░░░] 50%" format
        """
        if self.total_items == 0:
            pct = 100
        else:
            pct = int((self.processed / self.total_items) * 100)
        
        filled = int(width * self.processed / self.total_items) if self.total_items > 0 else width
        bar = '█' * filled + '░' * (width - filled)
        return f"[{bar}] {pct:3d}%"
    
    def print_progress(self):
        """Print single-line progress update (overwrites with carriage return)."""
        bar = self.progress_bar()
        # Compact format: 📊 Name | [progress] X/Total | Size
        size_str = f"{self.file_size_mb:.1f} MB" if self.file_size_mb > 0 else ""
        name_short = self.name[:28]
        msg = f"\r  📊 {name_short:<28}  {bar}  {self.processed:4d}/{self.total_items:<4d}  {size_str}"
        print(msg, end='', flush=True)
    
    def print_summary(self) -> dict:
        """
        Print final summary, replacing the progress line.
        
        Returns:
            Summary dict with status info
        """
        # Clear the progress line and replace with summary (pad to clear old bar)
        clearpad = " " * 100
        print(f"\r  ✅ {self.name:<50}{clearpad}")
        if self.processed > 0:
            print(f"     Pokémon: {self.processed}")
        if self.page_count > 0:
            print(f"     Pages: {self.page_count}")
        if self.file_size_mb > 0:
            print(f"     Size: {self.file_size_mb:.2f} MB")
        
        return {
            'name': self.name,
            'pokemon': self.processed,
            'pages': self.page_count,
            'size_mb': self.file_size_mb,
            'failed': self.failed
        }


class SectionHeader:
    """Format section headers with visual styling."""
    
    @staticmethod
    def main(text: str, width: int = 80):
        """
        Print main section header.
        
        Example:
        ================================================================================
        PDF Generation - Pokédex (Gen 1-9)
        ================================================================================
        """
        line = '=' * width
        print('')
        print(line)
        print(text)
        print(line)
    
    @staticmethod
    def sub(text: str):
        """
        Print sub-section header.
        
        Example:
        📊 Generating Pokédex Gen 1-9 → Deutsch
        """
        print('')
        print(f"📊 {text}")
    
    @staticmethod
    def section(text: str, indent: int = 0):
        """
        Print indented section.
        
        Example:
          Section: normal, separator=False, 103 Pokémon
        """
        prefix = "  " * indent
        print(f"{prefix}  {text}")


class BatchSummary:
    """Format summary of batch generation results."""
    
    def __init__(self):
        """Initialize batch summary."""
        self.generated = 0
        self.failed = 0
        self.items = []  # List of (name, status, size_mb)
    
    def add(self, name: str, success: bool, size_mb: float = 0):
        """Add item to summary."""
        if success:
            self.generated += 1
            status = "✅"
        else:
            self.failed += 1
            status = "❌"
        self.items.append((name, status, size_mb))
    
    def print_summary(self, width: int = 80):
        """Print final summary."""
        line = '=' * width
        print('')
        print(line)
        print("Summary")
        print(line)
        print(f"✅ Generated: {self.generated}")
        print(f"❌ Failed:    {self.failed}")
        print(line)


def format_key_value(key: str, value: str, indent: int = 0) -> str:
    """Format key-value pair for logging."""
    prefix = "  " * indent
    return f"{prefix}{key}: {value}"


def format_metric(label: str, value, unit: str = "", indent: int = 1) -> str:
    """Format a metric for display."""
    prefix = "  " * indent
    if unit:
        return f"{prefix}{label}: {value} {unit}"
    else:
        return f"{prefix}{label}: {value}"
