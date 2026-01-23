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
from .rendering import CardRenderer, PageRenderer, CoverRenderer, CoverStyle
from .utils import TranslationHelper, RendererInitializer
from .constants import PAGE_WIDTH, PAGE_HEIGHT, PAGE_MARGIN, CARD_WIDTH, CARD_HEIGHT, CARDS_PER_ROW, CARDS_PER_COLUMN, GAP_X, GAP_Y
from .log_formatter import PDFStatus, SectionHeader

logger = logging.getLogger(__name__)


class VariantPDFGenerator:
    """Generate PDFs for Pokémon variant collections using template system."""
    
    def __init__(self, variant_data: dict, language: str, output_file: Path, image_cache=None):
        """
        Initialize variant PDF generator.
        
        Args:
            variant_data: Dictionary with variant info - either:
                          - New structure: sections dict with pokemon inside each section
                          - Old structure: flat pokemon list at top level
            language: Language code (de, en, fr, etc.)
            output_file: Path to output PDF file
            image_cache: Optional image cache for loading Pokémon images
        """
        self.variant_data = variant_data
        self.language = language
        self.output_file = output_file
        self.image_cache = image_cache
        
        # Build complete pokemon list based on structure
        self.pokemon_list = []
        sections_dict = variant_data.get('sections', {})
        
        if isinstance(sections_dict, dict) and sections_dict:
            # New hierarchical structure: sections is a dict with pokemon inside each section
            for section_id in sorted(sections_dict.keys(), key=lambda k: sections_dict[k].get('section_order', 999)):
                section = sections_dict[section_id]
                self.pokemon_list.extend(section.get('pokemon', []))
        else:
            # Old/flat structure: pokemon at top level (e.g., variants_mega.json)
            self.pokemon_list = variant_data.get('pokemon', [])
        
        logger.info(f"Loaded {len(self.pokemon_list)} Pokémon from variant data")
        
        # Load translations
        self.translations = TranslationHelper.load_translations(self.language)
        
        # Initialize rendering modules using shared utility
        self.card_renderer, self.page_renderer, self.variant_cover_renderer = \
            RendererInitializer.initialize_renderers(language, image_cache, variant_data=variant_data)
    
    def generate(self) -> bool:
        """Generate the PDF with separator pages for each section."""
        try:
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            
            status = PDFStatus(self.output_file.stem, len(self.pokemon_list))
            
            c = canvas.Canvas(str(self.output_file), pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
            
            # Get sections - new hierarchical structure
            sections_dict = self.variant_data.get('sections', {})
            
            if not sections_dict:
                # Fallback: create default section with all pokemon
                # Use variant_name as section name (for flat structures like mega_evolution)
                default_name = self.variant_data.get('variant_name', 'Collection')
                sections_dict = {
                    'default': {
                        'section_id': 'default',
                        'section_order': 1,
                        'name': {
                            'en': default_name,
                            'de': default_name,
                            'fr': default_name,
                            'es': default_name,
                            'it': default_name,
                            'ja': default_name,
                            'ko': default_name,
                            'zh_hans': default_name,
                            'zh_hant': default_name
                        },
                        'subtitle': {
                            'en': '',
                            'de': '',
                            'fr': '',
                            'es': '',
                            'it': '',
                            'ja': '',
                            'ko': '',
                            'zh_hans': '',
                            'zh_hant': ''
                        },
                        'color_hex': self.variant_data.get('color_hex', '#999999'),
                        'iconic_pokemon': [],
                        'pokemon': self.pokemon_list
                    }
                }
            
            # Convert dict to list and sort by order
            sections_list = list(sections_dict.values()) if isinstance(sections_dict, dict) else sections_dict
            sections_list = sorted(sections_list, key=lambda s: s.get('section_order', 999))
            
            # Render all sections
            self._generate_with_sections(c, sections_list, status)
            
            c.save()
            
            # Update summary info
            file_size = self.output_file.stat().st_size / (1024 * 1024)
            status.file_size_mb = file_size
            status.print_summary()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error generating PDF: {e}")
            return False
            return False
    
    def _generate_with_sections(self, c, sections: list, status: PDFStatus = None):
        """
        Generate PDF with section cover pages and card pages.
        
        Each section now contains its pokemon directly (hierarchical structure).
        """
        logger.info(f"Generating with {len(sections)} sections")
        
        # Calculate total cards for progress tracking
        total_cards = len(self.pokemon_list)
        cards_rendered = 0
        
        for section in sections:
            section_id = section.get('section_id')
            # Pokemon are now INSIDE the section
            section_pokemon = section.get('pokemon', [])
            
            logger.info(f"  Section: {section_id}, pokemon={len(section_pokemon)}")
            
            # Get section title (multilingual)
            section_title_data = section.get('title', {})
            if isinstance(section_title_data, dict):
                section_title = section_title_data.get(self.language, section_title_data.get('en', section_id))
            else:
                section_title = str(section_title_data)
            
            # Get section subtitle (multilingual)
            section_subtitle_data = section.get('subtitle', {})
            if isinstance(section_subtitle_data, dict):
                section_subtitle = section_subtitle_data.get(self.language, section_subtitle_data.get('en', section_id))
            else:
                section_subtitle = str(section_subtitle_data)
            
            logger.info(f"    Title: {section_title}, Subtitle: {section_subtitle}")
            
            # Get iconic pokemon
            iconic_pokemon_ids = section.get('iconic_pokemon', [])
            
            # Draw cover page for this section
            self._draw_section_cover(
                c, section_title, section_subtitle, section.get('color_hex', '#7851A9'),
                section_title_dict=section_title_data,
                section_subtitle_dict=section_subtitle_data,
                iconic_pokemon_ids=iconic_pokemon_ids,
                section_pokemon=section_pokemon
            )
            c.showPage()
            
            # Draw cards for this section
            # Get section prefix and suffix
            section_prefix = section.get('prefix', '')
            section_suffix = section.get('suffix', '')
            
            cards_per_page = 9
            for page_idx in range(0, len(section_pokemon), cards_per_page):
                page_pokemon = section_pokemon[page_idx:page_idx + cards_per_page]
                
                # Show progress
                cards_rendered += len(page_pokemon)
                progress_pct = (cards_rendered / total_cards) * 100
                if status:
                    status.update(None, progress_pct)
                    status.print_progress()
                else:
                    bar_width = 30
                    filled = int(bar_width * progress_pct / 100)
                    bar = '█' * filled + '░' * (bar_width - filled)
                    print(f"\r  [{bar}] {cards_rendered}/{total_cards} ({progress_pct:.0f}%)", end='', flush=True)
                
                self._draw_cards_page(c, page_pokemon, section_prefix, section_suffix)
                c.showPage()
    
    def _draw_section_cover(self, c, section_title_str: str, section_subtitle_str: str, color: str, 
                           section_title_dict: dict = None, section_subtitle_dict: dict = None, 
                           iconic_pokemon_ids: list = None, section_pokemon: list = None):
        """
        Draw a cover page for a section.
        
        Args:
            c: Canvas object
            section_title_str: Section title string (localized)
            section_subtitle_str: Section subtitle string (localized)
            color: Hex color for the stripe
            section_title_dict: Full multilingual title dict for override
            section_subtitle_dict: Full multilingual subtitle dict for override
            iconic_pokemon_ids: List of Pokémon IDs to display as featured Pokémon
            section_pokemon: The pokemon in this section (for featured pokemon lookup)
        """
        # Create cover data with section-specific title and subtitle
        cover_data = dict(self.variant_data)
        cover_data['iconic_pokemon_ids'] = iconic_pokemon_ids or []
        
        # Override title with section-specific title dict
        if section_title_dict:
            cover_data['title'] = section_title_dict
        
        # Override subtitle with section-specific subtitle dict
        if section_subtitle_dict:
            cover_data['subtitle'] = section_subtitle_dict
        
        # Use unified renderer for section cover pages
        # Pass section_pokemon to allow rendering featured pokemon correctly
        if section_pokemon:
            self.variant_cover_renderer.render_cover(
                c,
                section_pokemon,
                cover_data=cover_data,
                color=color
            )
        else:
            self.variant_cover_renderer.render_cover(
                c,
                self.pokemon_list,
                cover_data=cover_data,
                color=color
            )
    
    def _draw_cards_page(self, c, pokemon_list, section_prefix: str = '', section_suffix: str = ''):
        """Draw a page with cards (3x3 grid) with cutting guides and footer."""
        # Create page using unified PageRenderer
        self.page_renderer.create_page(c)
        
        # Draw cards using unified CardRenderer with section prefix/suffix
        for idx, pokemon in enumerate(pokemon_list):
            self.page_renderer.add_card_to_page(
                c, self.card_renderer, pokemon, idx, 
                variant_mode=True,
                section_prefix=section_prefix,
                section_suffix=section_suffix
            )
        
        # Add footer
        self.page_renderer.add_footer(c)
        # Draw cutting guides last (on top)
        self.page_renderer.draw_cutting_guides(c)
