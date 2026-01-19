"""
Form Fetchers Module

Each form type (Mega Evolution, Gigantamax, Regional Forms, etc.)
has its own fetcher module for clean, modular design.
"""

from .mega_evolution_fetcher import MegaEvolutionFetcher

__all__ = ['MegaEvolutionFetcher']
