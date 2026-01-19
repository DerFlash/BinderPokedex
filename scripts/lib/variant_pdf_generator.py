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
from .card_template import CardTemplate
from .cover_template import CoverTemplate
from .constants import PAGE_WIDTH, PAGE_HEIGHT, PAGE_MARGIN, CARD_WIDTH, CARD_HEIGHT, CARDS_PER_ROW, CARDS_PER_COLUMN, GAP_X, GAP_Y

logger = logging.getLogger(__name__)


# Variant color scheme (for cover pages)
VARIANT_COLORS = {
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
        
        # Load translations
        self.translations = self._load_translations()
        
        # Sort by ID
        self.pokemon_list.sort(key=lambda x: int(x.get('pokedex_number', 0)))
        
        # Initialize templates with format_translation callback
        self.card_template = CardTemplate(language=language, image_cache=image_cache)
        self.cover_template = CoverTemplate(
            language=language, 
            image_cache=image_cache,
            format_translation=self._format_translation
        )
        
        # Register fonts if not already done
        try:
            FontManager.register_fonts()
        except:
            pass
    
    def _load_translations(self) -> dict:
        """
        Load translations from i18n/translations.json
        
        Returns:
            Dictionary with translations for current language
        """
        try:
            trans_file = Path(__file__).parent.parent.parent / 'i18n' / 'translations.json'
            with open(trans_file, 'r', encoding='utf-8') as f:
                all_trans = json.load(f)
            
            # Return UI translations for the current language, or empty dict if not found
            ui_trans = all_trans.get('ui', {})
            return ui_trans.get(self.language, {})
        except Exception as e:
            logger.warning(f"Could not load translations: {e}")
            return {}
    
    def _format_translation(self, key: str, **kwargs) -> str:
        """
        Get a translated string and format it with provided variables.
        
        Args:
            key: Translation key (e.g., 'variant_species')
            **kwargs: Variables to format into the string
        
        Returns:
            Formatted translation or key if not found
        """
        text = self.translations.get(key, key)
        
        # Simple template replacement
        for var_name, var_value in kwargs.items():
            text = text.replace(f'{{{{{var_name}}}}}', str(var_value))
        
        return text
    
    def generate(self) -> bool:
        """Generate the PDF."""
        try:
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            
            c = canvas.Canvas(str(self.output_file), pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
            
            # Draw cover page
            self._draw_cover_page(c)
            c.showPage()
            
            # Draw card pages (3x3 grid per page)
            cards_per_page = 9
            for page_idx in range(0, len(self.pokemon_list), cards_per_page):
                page_pokemon = self.pokemon_list[page_idx:page_idx + cards_per_page]
                self._draw_cards_page(c, page_pokemon)
                c.showPage()
            
            c.save()
            logger.info(f"✅ Generated: {self.output_file.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error generating PDF: {e}")
            return False
    
    def _draw_cover_page(self, c):
        """Draw the cover page using cover template."""
        variant_type = self.variant_data.get('variant_type', 'unknown')
        color = VARIANT_COLORS.get(variant_type, '#FFD700')
        
        self.cover_template.draw_variant_cover(
            c,
            self.variant_data,
            self.pokemon_list,
            color
        )
    
    def _draw_cards_page(self, c, pokemon_list):
        """Draw a page with cards (3x3 grid) with cutting guides and footer."""
        # White background
        c.setFillColor(HexColor("#FFFFFF"))
        c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=True, stroke=False)
        
        # Draw cutting guides (shared with PDFGenerator)
        from .base_pdf_generator import BasePDFGenerator
        BasePDFGenerator.draw_cutting_guides(c)
        
        # Draw cards in 3x3 grid
        MARGIN = PAGE_MARGIN
        CARD_W = CARD_WIDTH
        CARD_H = CARD_HEIGHT
        
        # Draw cards using template
        for idx, pokemon in enumerate(pokemon_list):
            row = idx // CARDS_PER_ROW
            col = idx % CARDS_PER_ROW
            
            x = MARGIN + col * (CARD_W + GAP_X)
            y = PAGE_HEIGHT - MARGIN - (row + 1) * CARD_H - row * GAP_Y
            
            self.card_template.draw_card(c, pokemon, x, y, CARD_W, CARD_H, variant_mode=True)
        
        # Draw footer before showing page
        c.setFont("Helvetica", 6)
        c.setFillColor(HexColor("#AAAAAA"))
        footer_text = f"Binder Pokédex Project | github.com/BinderPokedex"
        c.drawCentredString(PAGE_WIDTH / 2, 8, footer_text)
