"""Compatibility wrapper for legacy text renderer imports."""

try:
    from .utils import TextRenderer
except ImportError:
    from utils import TextRenderer


__all__ = ["TextRenderer"]