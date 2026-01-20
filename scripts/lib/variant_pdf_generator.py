"""
Variant PDF Generator - ReportLab-based

Generates clean, professional PDFs for Pokémon variant collections.
Uses reusable templates for consistent styling with generation PDFs.

Features:
- Variant-specific cover pages with color coding
- 3x3 card layout per page
- Multi-language support via FontManager
- CJK text rendering
- Consistent styling with generation PDFs
"""

import logging
import json
from pathlib import Path

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor

from .fonts import FontManager
from .rendering import CardRenderer, CoverRenderer, PageRenderer, VariantCoverRenderer, VariantCoverStyle
from .cover_template import CoverTemplate
from .utils import TranslationHelper
from .constants import PAGE_WIDTH, PAGE_HEIGHT, PAGE_MARGIN, CARD_WIDTH, CARD_HEIGHT, CARDS_PER_ROW, CARDS_PER_COLUMN, GAP_X, GAP_Y, VARIANT_COLORS

logger = logging.getLogger(__name__)


# ⚠️ DEPRECATED - Use VARIANT_COLORS from constants.py instead
# Keeping for backward compatibility during transition
VARIANT_COLORS_DEPRECATED = {
    'ex_gen1': '#1F51BA',             # Blue for Gen1
    'ex_gen2': '#3D5A80',             # Dark Blue for Gen2
    'ex_gen3': '#6B40D1',             # Purple for Gen3
    'mega_evolution': '#FFD700',      # Gold
    'gigantamax': '#C5283F',          # Red
    'regional_alola': '#FDB927',      # Yellow
    'regional_galar': '#0071BA',      # Blue
    'regional_hisui': '#9D3F1D',      # Brown
    'regional_paldea': '#D3337F',     # Pink
    'primal_terastal': '#7B61FF',     # Purple
    'patterns_unique': '#9D7A4C',     # Orange
    'fusion_special': '#6F6F6F',      # Gray
}


class VariantPDFGenerator:
    """Generate PDFs for Pokémon variant collections using template system."""
    
    def __init__(self, variant_data: dict, language: str, output_file: Path, image_cache=None):
        """
        Initialize variant PDF generator.
        
        Args:
            variant_data: Dictionary with variant info and pokemon list
            language: Language code (de, en, fr, etc.)
            output_file: Path to output PDF file
            image_cache: Optional image cache for loading Pokémon images
        """
        self.variant_data = variant_data
        self.language = language
        self.output_file = output_file
        self.pokemon_list = variant_data.get('pokemon', [])
        self.image_cache = image_cache
        
        logger.info(f"Loaded {len(self.pokemon_list)} Pokémon from variant data")
        
        # Load translations
        self.translations = TranslationHelper.load_translations(self.language)
        
        # DO NOT SORT HERE - respect the order in the variant data
        # The pokemon list order matters for section indices to work correctly
        
        # Initialize new unified rendering modules
        self.card_renderer = CardRenderer(language=language, image_cache=image_cache, variant=variant_data.get('variant_type'), variant_data=variant_data)
        # Modern VariantCoverRenderer for variant covers
        self.variant_cover_renderer = VariantCoverRenderer(language=language, image_cache=image_cache)
        self.page_renderer = PageRenderer()
        
        # Register fonts if not already done
        try:
            FontManager.register_fonts()
        except:
            pass
    
    def _load_translations(self) -> dict:
        """
        ⚠️ DEPRECATED - Use TranslationHelper.load_translations() instead.
        Kept for backward compatibility.
        
        Load translations from i18n/translations.json
        
        Returns:
            Dictionary with translations for current language
        """
        return TranslationHelper.load_translations(self.language)
    
    def _format_translation(self, key: str, **kwargs) -> str:
        """
        ⚠️ DEPRECATED - Use TranslationHelper.format_translation() instead.
        Kept for backward compatibility.
        
        Get a translated string and format it with provided variables.
        
        Args:
            key: Translation key (e.g., 'variant_species')
            **kwargs: Variables to format into the string
        
        Returns:
            Formatted translation or key if not found
        """
        return TranslationHelper.format_translation(self.translations, key, **kwargs)
    
    def generate(self) -> bool:
        """Generate the PDF with optional separator pages for sections."""
        try:
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            
            c = canvas.Canvas(str(self.output_file), pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
            
            # Draw cover page
            self._draw_cover_page(c)
            c.showPage()
            
            # Check if this variant has sections (like ex_gen3 with Normal/Tera/Mega)
            sections = self.variant_data.get('sections', [])
            
            if sections:
                # Render with section separators
                self._generate_with_sections(c, sections)
            else:
                # Simple rendering without sections
                cards_per_page = 9
                total_cards = len(self.pokemon_list)
                for page_idx in range(0, len(self.pokemon_list), cards_per_page):
                    page_pokemon = self.pokemon_list[page_idx:page_idx + cards_per_page]
                    # Show progress
                    cards_rendered = min(page_idx + cards_per_page, total_cards)
                    progress_pct = (cards_rendered / total_cards) * 100
                    bar_width = 30
                    filled = int(bar_width * progress_pct / 100)
                    bar = '█' * filled + '░' * (bar_width - filled)
                    print(f"\r  [{bar}] {cards_rendered}/{total_cards} ({progress_pct:.0f}%)", end='', flush=True)
                    
                    self._draw_cards_page(c, page_pokemon)
                    c.showPage()
            
            c.save()
            print()  # Newline after progress bar
            logger.info(f"✅ Generated: {self.output_file.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error generating PDF: {e}")
            return False
    
    def _generate_with_sections(self, c, sections: list):
        """Generate PDF with section separators and crystalline patterns."""
        # Sort sections by order
        sections = sorted(sections, key=lambda s: s.get('section_order', 999))
        
        logger.info(f"Generating with {len(sections)} sections")
        
        # Calculate total cards for progress tracking
        total_cards = len(self.pokemon_list)
        cards_rendered = 0
        
        for section in sections:
            section_id = section.get('section_id')
            is_separator = section.get('is_separator_page', False)
            pattern = section.get('pattern', 'standard')
            pokemon_indices = section.get('pokemon_indices', [])
            
            logger.info(f"  Section: {section_id}, separator={is_separator}, indices={pokemon_indices}")
            
            # Get section Pokémon
            section_pokemon = [self.pokemon_list[i] for i in pokemon_indices if i < len(self.pokemon_list)]
            logger.info(f"    Found {len(section_pokemon)} Pokémon for section")
            
            # Draw separator page if needed
            if is_separator:
                section_name = section.get(f'section_name_{self.language}', section_id)
                
                # Get featured pokémon from iconic_pokemon field in section
                iconic_pokemon_ids = section.get('iconic_pokemon', [])
                
                # Build featured_pokemon list from IDs
                featured_pokemon = []
                if iconic_pokemon_ids:
                    for pid in iconic_pokemon_ids:
                        for p in section_pokemon:
                            if p.get('pokemon_id') == pid or p.get('id') == pid:
                                featured_pokemon.append(p)
                                break
                
                # Fallback to first 3 if no iconic_pokemon defined
                if not featured_pokemon:
                    featured_pokemon = section_pokemon[:3] if section_pokemon else []
                
                logger.info(f"    Featured Pokémon: {[p.get('name_en', 'Unknown') for p in featured_pokemon]}")
                
                # Use _draw_simple_separator for all patterns (which uses draw_variant_cover)
                # This ensures consistent header styling across all variants
                iconic_ids = [p.get('id') for p in featured_pokemon] if featured_pokemon else []
                self._draw_simple_separator(
                    c, section_name, section.get('color_hex', '#7851A9'),
                    iconic_pokemon_ids=iconic_ids,
                    pattern=pattern if pattern != 'standard' else None,
                    section_id=section_id
                )
                
                c.showPage()
            
            # Draw cards for this section
            cards_per_page = 9
            for page_idx in range(0, len(section_pokemon), cards_per_page):
                page_pokemon = section_pokemon[page_idx:page_idx + cards_per_page]
                
                # Show progress
                cards_rendered += len(page_pokemon)
                progress_pct = (cards_rendered / total_cards) * 100
                bar_width = 30
                filled = int(bar_width * progress_pct / 100)
                bar = '█' * filled + '░' * (bar_width - filled)
                print(f"\r  [{bar}] {cards_rendered}/{total_cards} ({progress_pct:.0f}%)", end='', flush=True)
                
                self._draw_cards_page(c, page_pokemon)
                c.showPage()
    
    def _draw_simple_separator(self, c, title: str, color: str, iconic_pokemon_ids: list = None, pattern: str = None, section_id: str = None):
        """
        Draw a separator page using VariantCoverRenderer.
        Uses render_variant_cover() with section_title parameter for consistency.
        
        Args:
            c: Canvas object
            title: Section title (e.g., "Pokémon-EX Mega") - displayed as subtitle
            color: Hex color for the stripe
            iconic_pokemon_ids: Optional list of Pokémon IDs to display as featured Pokémon
            pattern: Optional pattern type for the background
            section_id: Optional section identifier for special logos (e.g., 'mega', 'primal')
        """
        # Create separator data by adding featured Pokémon to variant data
        separator_data = dict(self.variant_data)
        separator_data['iconic_pokemon_ids'] = iconic_pokemon_ids or []
        
        # Use VariantCoverRenderer.render_variant_cover() with section_title parameter
        # This ensures identical spacing and styling to the main cover page
        self.variant_cover_renderer.render_variant_cover(
            c,
            separator_data,
            self.pokemon_list,
            color,
            section_title=title  # Mark this as a separator with the section name
        )
    
    def _draw_cover_page(self, c):
        """Draw the cover page using VariantCoverRenderer."""
        variant_type = self.variant_data.get('variant_type', 'unknown')
        color = VARIANT_COLORS.get(variant_type, '#FFD700')
        
        self.variant_cover_renderer.render_variant_cover(
            c,
            self.variant_data,
            self.pokemon_list,
            color
        )
    
    
    def _draw_cards_page(self, c, pokemon_list):
        """Draw a page with cards (3x3 grid) with cutting guides and footer."""
        # Create page using unified PageRenderer
        self.page_renderer.create_page(c)
        
        # Draw cards using unified CardRenderer
        for idx, pokemon in enumerate(pokemon_list):
            self.page_renderer.add_card_to_page(c, self.card_renderer, pokemon, idx, variant_mode=True)
        
        # Add footer
        self.page_renderer.add_footer(c)
