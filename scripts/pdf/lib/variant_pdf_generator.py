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
from .rendering import (
    CardRenderer,
    CoverRenderer,
    CoverStyle,
    PageRenderer,
    PosterPageCollection,
)
from .utils import TranslationHelper, RendererInitializer
from .constants import PAGE_WIDTH, PAGE_HEIGHT, PAGE_MARGIN, CARD_WIDTH, CARD_HEIGHT, CARDS_PER_ROW, CARDS_PER_COLUMN, GAP_X, GAP_Y
from .log_formatter import PDFStatus, SectionHeader

logger = logging.getLogger(__name__)


class VariantPDFGenerator:
    """Generate PDFs for Pokémon variant collections using template system."""
    
    def __init__(
        self,
        variant_data: dict,
        language: str,
        output_file: Path,
        image_cache=None,
        type_translations: dict = None,
        card_template: str = None,
        page_template: str = None,
        cover_template: str = None,
        include_poster: bool = True,
        scope_name: str = None,
        poster_source_data: dict = None,
        poster_page_mode: str = "cards",
    ):
        """
        Initialize variant PDF generator.
        
        Args:
            variant_data: Dictionary with variant info - either:
                          - New structure: sections dict with pokemon inside each section
                          - Old structure: flat pokemon list at top level
            language: Language code (de, en, fr, etc.)
            output_file: Path to output PDF file
            image_cache: Optional image cache for loading Pokémon images
            type_translations: Optional type translations dict from API (for multilingual types)
            card_template: Optional SVG template for cards
            page_template: Optional SVG template for pages
            cover_template: Optional SVG template for covers
            include_poster: Include a manifest-enabled poster page
            scope_name: Explicit source filename scope for aggregate data
            poster_source_data: Complete unfiltered data used to validate routing
            poster_page_mode: Render poster as cuttable cards or one full page
        """
        self.variant_data = variant_data
        self.language = language
        self.output_file = output_file
        self.image_cache = image_cache
        self.type_translations = type_translations
        self.card_template = card_template
        self.page_template = page_template
        self.cover_template = cover_template
        
        # Build complete pokemon list based on structure
        self.pokemon_list = []
        sections_dict = variant_data.get('sections', {})
        
        if isinstance(sections_dict, dict) and sections_dict:
            # New hierarchical structure: sections is a dict with cards inside each section
            for section_id in sorted(sections_dict.keys(), key=lambda k: sections_dict[k].get('section_order', 999)):
                section = sections_dict[section_id]
                self.pokemon_list.extend(section.get('cards', []))
        elif isinstance(sections_dict, list) and sections_dict:
            for section in sorted(
                sections_dict,
                key=lambda item: item.get('section_order', 999),
            ):
                self.pokemon_list.extend(section.get('cards', []))
        else:
            # Old/flat structure: pokemon at top level (e.g., variants_mega.json)
            self.pokemon_list = variant_data.get('pokemon', [])
        
        logger.info(f"Loaded {len(self.pokemon_list)} Pokémon from variant data")
        
        # Load translations
        self.translations = TranslationHelper.load_translations(self.language)
        
        # Initialize rendering modules using shared utility
        self.card_renderer, self.page_renderer, self.variant_cover_renderer = \
            RendererInitializer.initialize_renderers(
                language, image_cache, variant_data=variant_data, type_translations=self.type_translations, 
                card_template=self.card_template, cover_template=self.cover_template
            )
        poster_scope = (
            scope_name
            or variant_data.get("set_id")
            or variant_data.get("scope")
        )
        self.poster_pages = PosterPageCollection.from_scope(
            poster_scope,
            (
                poster_source_data
                if poster_source_data is not None
                else variant_data
            ),
            language,
            include_poster=include_poster,
            page_mode=poster_page_mode,
        )
    
    def generate(self) -> bool:
        """Generate the PDF with separator pages for each section."""
        temporary_output = self.output_file.with_name(
            f".{self.output_file.name}.tmp"
        )
        try:
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            temporary_output.unlink(missing_ok=True)
            
            status = PDFStatus(self.output_file.stem, len(self.pokemon_list))
            
            c = canvas.Canvas(
                str(temporary_output),
                pagesize=(PAGE_WIDTH, PAGE_HEIGHT),
            )
            
            # Render all sections
            self._generate_with_sections(c, self._sections_for_rendering(), status)
            
            c.save()
            temporary_output.replace(self.output_file)
            
            # Update summary info
            file_size = self.output_file.stat().st_size / (1024 * 1024)
            status.file_size_mb = file_size
            status.print_summary()
            
            return True
            
        except Exception as e:
            import traceback
            temporary_output.unlink(missing_ok=True)
            logger.error(f"❌ Error generating PDF: {e}")
            logger.error(traceback.format_exc())
            return False
        finally:
            self.poster_pages.cleanup()

    def _sections_for_rendering(self) -> list[dict]:
        """Normalize hierarchical and legacy flat data to renderable sections."""
        sections = self.variant_data.get('sections', {})
        if sections:
            if isinstance(sections, dict):
                sections_list = [
                    {
                        **section,
                        'section_id': section.get('section_id') or section_id,
                    }
                    for section_id, section in sections.items()
                ]
            else:
                sections_list = list(sections)
            return sorted(
                sections_list,
                key=lambda section: section.get('section_order', 999),
            )

        default_title = (
            self.variant_data.get('title')
            or self.variant_data.get('variant_display_name')
            or self.variant_data.get('variant_name')
            or self.variant_data.get('name')
            or 'Collection'
        )
        return [
            {
                'section_id': 'default',
                'section_order': 1,
                'title': default_title,
                'subtitle': self.variant_data.get('subtitle', ''),
                'description': self.variant_data.get('description', {}),
                'color_hex': self.variant_data.get('color_hex', '#999999'),
                'featured_elements': self.variant_data.get(
                    'featured_elements',
                    self.variant_data.get('featured_cards', []),
                ),
                'cards': self.pokemon_list,
            }
        ]
    
    def _generate_with_sections(self, c, sections: list, status: PDFStatus = None):
        """
        Generate PDF with section cover pages and card pages.
        
        Each section now contains its pokemon directly (hierarchical structure).
        """
        logger.info(f"Generating with {len(sections)} sections")
        
        # Calculate total cards for progress tracking
        total_cards = len(self.pokemon_list)
        cards_rendered = 0
        
        for section_index, section in enumerate(sections):
            section_id = section.get('section_id')
            # Cards are now INSIDE the section
            section_pokemon = section.get('cards', [])
            
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
            
            # Draw cover page for this section
            self._draw_section_cover(
                c, section_title, section_subtitle, section.get('color_hex', '#7851A9'),
                section_title_dict=section_title_data,
                section_subtitle_dict=section_subtitle_data,
                section_pokemon=section_pokemon,
                section_description=section.get('description', {}),
                section_data=section  # Pass full section data including featured_elements
            )
            c.showPage()

            for poster_page in self.poster_pages.for_section(
                section_id,
                section_index,
            ):
                poster_page.render_page(c, self.page_renderer)
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
                
                # Calculate section index offset for this page
                section_index_offset = page_idx
                self._draw_cards_page(c, page_pokemon, section_prefix, section_suffix, section_index_offset)
                c.showPage()
    
    def _draw_section_cover(self, c, section_title_str: str, section_subtitle_str: str, color: str, 
                           section_title_dict: dict = None, section_subtitle_dict: dict = None, 
                           section_pokemon: list = None,
                           section_description: dict = None,
                           section_data: dict = None):
        """
        Draw a cover page for a section.
        
        Args:
            c: Canvas object
            section_title_str: Section title string (localized)
            section_subtitle_str: Section subtitle string (localized)
            color: Hex color for the stripe
            section_title_dict: Full multilingual title dict for override
            section_subtitle_dict: Full multilingual subtitle dict for override
            section_pokemon: The pokemon in this section (for featured pokemon lookup)
            section_description: Section description dict
            section_data: Full section data dict (including featured_elements)
        """
        # Create cover data with section-specific title and subtitle
        cover_data = dict(self.variant_data)
        
        # Override title with section-specific title dict
        if section_title_dict:
            cover_data['title'] = section_title_dict
        
        # Override subtitle with section-specific subtitle dict
        if section_subtitle_dict:
            cover_data['subtitle'] = section_subtitle_dict
        
        # Override description with section-specific description
        if section_description:
            cover_data['description'] = section_description
        
        # Add featured_elements from section_data (check both old and new names)
        if section_data and 'featured_elements' in section_data:
            cover_data['featured_elements'] = section_data['featured_elements']
        elif section_data and 'featured_cards' in section_data:  # Backward compatibility
            cover_data['featured_elements'] = section_data['featured_cards']
        
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
    
    def _draw_cards_page(self, c, pokemon_list, section_prefix: str = '', section_suffix: str = '', section_index_offset: int = 0):
        """Draw a page with cards (3x3 grid) with cutting guides and footer."""
        # Create page using unified PageRenderer
        self.page_renderer.create_page(c)
        
        # Draw cards using unified CardRenderer with section prefix/suffix
        for idx, pokemon in enumerate(pokemon_list):
            # Calculate section index (1-based)
            section_index = section_index_offset + idx + 1
            # Add section_index to pokemon data temporarily
            pokemon_with_index = {**pokemon, 'section_index': section_index}
            self.page_renderer.add_card_to_page(
                c, self.card_renderer, pokemon_with_index, idx, 
                variant_mode=True,
                section_prefix=section_prefix,
                section_suffix=section_suffix
            )
        
        # Add footer
        self.page_renderer.add_footer(c)
        # Draw cutting guides last (on top)
        self.page_renderer.draw_cutting_guides(c)
