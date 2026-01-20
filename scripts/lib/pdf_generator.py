"""
PDF Generator Module - Enhanced

Orchestrates the complete PDF generation process.
Uses FontManager for font handling and TextRenderer for text rendering.

Features:
- Multi-language support with CJK rendering
- Cover pages with generation info
- Pokémon card layout (3x3 per page)
- Image embedding with fallback
- Clean architecture - no monkey-patching
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
import urllib.request
import urllib.error
from io import BytesIO
from PIL import Image

try:
    from .fonts import FontManager
    from .utils import TranslationHelper, TextRenderer
    from .constants import (
        LANGUAGES, PAGE_WIDTH, PAGE_HEIGHT, PAGE_MARGIN,
        CARD_WIDTH, CARD_HEIGHT, CARDS_PER_ROW, CARDS_PER_COLUMN, GAP_X, GAP_Y,
        OUTPUT_DIR, PDF_PREFIX, PDF_EXTENSION, COLORS, TYPE_COLORS, GENERATION_COLORS
    )
    from .rendering import CardRenderer, CoverRenderer, PageRenderer
except ImportError:
    # Fallback for direct imports (testing)
    from fonts import FontManager
    from utils import TranslationHelper, TextRenderer
    from constants import (
        LANGUAGES, PAGE_WIDTH, PAGE_HEIGHT, PAGE_MARGIN,
        CARD_WIDTH, CARD_HEIGHT, CARDS_PER_ROW, CARDS_PER_COLUMN, GAP_X, GAP_Y,
        OUTPUT_DIR, PDF_PREFIX, PDF_EXTENSION, COLORS, TYPE_COLORS, GENERATION_COLORS
    )
    from rendering import CardRenderer, CoverRenderer, PageRenderer

logger = logging.getLogger(__name__)


# ⚠️ DEPRECATED - Use TYPE_COLORS from constants.py instead
# Keeping for backward compatibility during transition
GENERATION_COLORS_DEPRECATED = {
    1: '#FF0000',  # Red
    2: '#FFAA00',  # Orange
    3: '#0000FF',  # Blue
    4: '#AA00FF',  # Purple
    5: '#00AA00',  # Green
    6: '#00AAAA',  # Cyan
    7: '#FF00AA',  # Pink
    8: '#AAAA00',  # Yellow
    9: '#666666',  # Gray
}

# ⚠️ DEPRECATED - Use TYPE_COLORS from constants.py instead
# Keeping for backward compatibility during transition
TYPE_COLORS_DEPRECATED = {
    'Normal': '#A8A878',
    'Fire': '#F08030',
    'Water': '#6890F0',
    'Electric': '#F8D030',
    'Grass': '#78C850',
    'Ice': '#98D8D8',
    'Fighting': '#C03028',
    'Poison': '#A040A0',
    'Ground': '#E0C068',
    'Flying': '#A890F0',
    'Psychic': '#F85888',
    'Bug': '#A8B820',
    'Rock': '#B8A038',
    'Ghost': '#705898',
    'Dragon': '#7038F8',
    'Dark': '#705848',
    'Steel': '#B8B8D0',
    'Fairy': '#EE99AC',
}


class ImageCache:
    """Image cache with fallback to network downloads."""
    
    def __init__(self):
        self.cache = {}
        self.disk_cache_dir = Path(__file__).parent.parent.parent / 'data' / 'pokemon_images_cache'
    
    def _get_cached_file(self, pokemon_id: int, variant: str = 'default') -> Optional[Path]:
        """Get path to cached image file if it exists."""
        cache_file = self.disk_cache_dir / f'pokemon_{pokemon_id}' / f'{variant}.jpg'
        if cache_file.exists():
            return cache_file
        return None
    
    def get_image(self, pokemon_id: int, url: Optional[str] = None, timeout: int = 5):
        """
        Get ImageReader object from disk cache, RAM cache, or download.
        
        Args:
            pokemon_id: Pokémon ID for disk cache lookup
            url: Fallback URL if not cached
            timeout: Download timeout in seconds
        
        Returns:
            ImageReader object if successful, None otherwise
        """
        # Check RAM cache first
        cache_key = f'pokemon_{pokemon_id}'
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Try disk cache
        cached_file = self._get_cached_file(pokemon_id)
        if cached_file:
            try:
                logger.debug(f"✓ Loading from disk cache: {cached_file.name}")
                image_reader = ImageReader(str(cached_file))
                self.cache[cache_key] = image_reader
                return image_reader
            except Exception as e:
                logger.debug(f"✗ Failed to load cached file: {e}")
        
        # Fallback to network download if URL provided
        if url:
            try:
                logger.debug(f"⬇ Downloading image: {url.split('/')[-1]}")
                req = urllib.request.Request(
                    url,
                    headers={'User-Agent': 'Binder Pokédex/2.0'}
                )
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    image_data = BytesIO(response.read())
                    image_data.seek(0)
                    
                    # Load with PIL
                    pil_image = Image.open(image_data)
                    
                    # Convert to RGB
                    if pil_image.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', pil_image.size, (255, 255, 255))
                        if pil_image.mode == 'P':
                            pil_image = pil_image.convert('RGBA')
                        background.paste(pil_image, mask=pil_image.split()[-1] if pil_image.mode in ('RGBA', 'LA') else None)
                        pil_image = background
                    elif pil_image.mode != 'RGB':
                        pil_image = pil_image.convert('RGB')
                    
                    # Save to BytesIO with JPEG compression
                    output = BytesIO()
                    pil_image.save(output, format='JPEG', quality=85, optimize=True)
                    output.seek(0)
                    
                    # Wrap in ImageReader for ReportLab
                    image_reader = ImageReader(output)
                    self.cache[cache_key] = image_reader
                    logger.debug(f"✓ Downloaded & cached (total: {len(self.cache)} images)")
                    return image_reader
            except (urllib.error.URLError, urllib.error.HTTPError, Exception) as e:
                logger.debug(f"✗ Failed to download image: {e}")
        
        return None


class PDFGenerator:
    """
    Generates Pokémon binder PDFs in multiple languages.
    
    Handles:
    - Language selection and validation
    - PDF creation and page management
    - Card layout and rendering
    - File output
    """
    
    def __init__(self, language: str, generation: int, translations: dict = None):
        """
        Initialize PDF generator.
        
        Args:
            language: Language code (e.g., 'de', 'ja', 'zh_hans')
            generation: Pokémon generation (1-9)
            translations: Optional translations dictionary. If None, will be loaded from file.
        
        Raises:
            ValueError: If language or generation is invalid
        """
        if language not in LANGUAGES:
            raise ValueError(f"Unsupported language: {language}")
        if generation not in range(1, 10):
            raise ValueError(f"Invalid generation: {generation}")
        
        self.language = language
        self.generation = generation
        self.pokemon_list = []
        self.current_page_cards = []
        self.page_count = 0
        self.image_cache = ImageCache()  # Initialize image cache
        
        # Initialize new rendering modules
        self.card_renderer = CardRenderer(language, self.image_cache)
        self.cover_renderer = CoverRenderer(language, generation, self.image_cache)
        self.page_renderer = PageRenderer()
        
        # Load translations
        if translations is None:
            self.translations = TranslationHelper.load_translations(self.language)
        else:
            self.translations = translations
        
        logger.info(f"Initialized PDFGenerator for {LANGUAGES[language]['name']} (Gen {generation})")
    
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
            key: Translation key (e.g., 'pokemon_species')
            **kwargs: Variables to format into the string
        
        Returns:
            Formatted translation or key if not found
        """
        return TranslationHelper.format_translation(self.translations, key, **kwargs)
    
    def set_pokemon_list(self, pokemon_list: list):
        """
        Set the list of Pokémon to render.
        
        Args:
            pokemon_list: List of pokemon data dictionaries
        """
        self.pokemon_list = pokemon_list
        logger.info(f"Set {len(pokemon_list)} Pokémon for rendering")
    
    
    def _draw_cover_page(self, canvas_obj):
        """
        Draw a cover page for the generation with iconic Pokémon.
        
        Features:
        - Colored top stripe with generation info
        - Large region name and generation number
        - Three iconic Pokémon displayed at the bottom
        - Clean, modern design
        - Multi-language support for all text
        
        Args:
            canvas_obj: ReportLab canvas object
        """
        # White background
        canvas_obj.setFillColor(HexColor("#FFFFFF"))
        canvas_obj.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=True, stroke=False)
        
        # Get generation color
        gen_color = GENERATION_COLORS.get(self.generation, '#999999')
        
        # ===== TOP COLORED STRIPE (Header section) =====
        stripe_height = 100 * mm
        canvas_obj.setFillColor(HexColor(gen_color))
        canvas_obj.rect(0, PAGE_HEIGHT - stripe_height, PAGE_WIDTH, stripe_height, fill=True, stroke=False)
        
        # Subtle gradient effect with semi-transparent overlay
        canvas_obj.setFillColor(HexColor("#000000"), alpha=0.05)
        canvas_obj.rect(0, PAGE_HEIGHT - stripe_height, PAGE_WIDTH, stripe_height, fill=True, stroke=False)
        
        # Binder Pokédex title
        canvas_obj.setFont("Helvetica-Bold", 42)
        canvas_obj.setFillColor(HexColor("#FFFFFF"))
        title_y = PAGE_HEIGHT - 30 * mm
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, title_y, "Binder Pokédex")
        
        # Decorative underline for title
        canvas_obj.setStrokeColor(HexColor("#FFFFFF"))
        canvas_obj.setLineWidth(1.5)
        canvas_obj.line(40 * mm, title_y - 8, PAGE_WIDTH - 40 * mm, title_y - 8)
        
        # Generation and Region info in header
        get_info = GENERATION_INFO[self.generation]
        region_name = get_info.get('region', f'Generation {self.generation}')
        
        # Use translations for Generation text
        gen_text = self._format_translation('generation_num', gen=self.generation)
        if not gen_text or gen_text == 'generation_num':
            # Fallback to English if translation not found
            gen_text = f"Generation {self.generation}"
        
        # Use appropriate font for generation text
        try:
            gen_font_name = FontManager.get_font_name(self.language, bold=False)
            canvas_obj.setFont(gen_font_name, 14)
        except:
            canvas_obj.setFont("Helvetica", 14)
        canvas_obj.setFillColor(HexColor("#FFFFFF"))
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 55 * mm, gen_text)
        
        canvas_obj.setFont("Helvetica-Bold", 18)
        canvas_obj.setFillColor(HexColor("#FFFFFF"))
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 65 * mm, region_name)
        
        # ===== MIDDLE CONTENT SECTION =====
        # ID range with translation
        start_id, end_id = get_info['range']
        id_range_text = self._format_translation('pokedex_range', start=f"#{start_id:03d}", end=f"#{end_id:03d}")
        if not id_range_text or id_range_text == 'pokedex_range':
            # Fallback if translation not found
            id_range_text = f"Pokédex #{start_id:03d} – #{end_id:03d}"
        
        # Use appropriate font for ID range text
        try:
            id_font_name = FontManager.get_font_name(self.language, bold=False)
            canvas_obj.setFont(id_font_name, 16)
        except:
            canvas_obj.setFont("Helvetica", 16)
        canvas_obj.setFillColor(HexColor("#333333"))
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, 120 * mm, id_range_text)
        
        # Pokémon count and info with translation
        pokemon_text = self._format_translation('pokemon_count_text', count=len(self.pokemon_list))
        if not pokemon_text or pokemon_text == 'pokemon_count_text':
            # Fallback if translation not found
            pokemon_text = f"{len(self.pokemon_list)} Pokémon in this collection"
        
        # Use appropriate font for pokemon count text
        try:
            count_font_name = FontManager.get_font_name(self.language, bold=False)
            canvas_obj.setFont(count_font_name, 14)
        except:
            canvas_obj.setFont("Helvetica", 14)
        canvas_obj.setFillColor(HexColor("#666666"))
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, 110 * mm, pokemon_text)
        
        # Decorative elements
        canvas_obj.setStrokeColor(HexColor(gen_color))
        canvas_obj.setLineWidth(1)
        canvas_obj.line(40 * mm, 105 * mm, PAGE_WIDTH - 40 * mm, 105 * mm)
        
        # ===== BOTTOM SECTION: ICONIC POKÉMON IN A CLEAN ROW =====
        iconic_ids = get_info.get('iconic_pokemon', [])
        
        if iconic_ids:
            pokemon_by_id = {int(p.get('id', p.get('num', '0').lstrip('#'))): p for p in self.pokemon_list}
            
            # Calculate positions for 3 Pokémon in a horizontal line
            pokemon_count = len(iconic_ids[:3])
            total_width = PAGE_WIDTH - (30 * mm)
            spacing_per_pokemon = total_width / pokemon_count
            
            for idx, poke_id in enumerate(iconic_ids[:3]):
                # Center position for this Pokémon
                x_center = 15 * mm + spacing_per_pokemon * (idx + 0.5)
                
                # Pokemon dimensions - large and prominent
                card_width = 65 * mm
                card_height = 90 * mm
                x = x_center - card_width / 2
                y = 10 * mm  # Lower position
                
                pokemon = pokemon_by_id.get(poke_id)
                
                if pokemon:
                    # Try to draw image - that's it
                    image_source = pokemon.get('image_path') or pokemon.get('image_url')
                    if image_source:
                        try:
                            image_to_render = None
                            if image_source.startswith('http://') or image_source.startswith('https://'):
                                image_to_render = self.image_cache.get_image(poke_id, url=image_source, timeout=3)
                            elif Path(image_source).exists():
                                image_to_render = image_source
                            
                            if image_to_render:
                                img_width = card_width * 0.72
                                img_height = card_height * 0.72
                                img_x = x_center - img_width / 2
                                img_y = y
                                canvas_obj.drawImage(
                                    image_to_render, img_x, img_y,
                                    width=img_width, height=img_height,
                                    preserveAspectRatio=True
                                )
                        except Exception as e:
                            logger.debug(f"Could not load image for iconic Pokémon {poke_id}: {e}")
        
        # Bottom info - single line with print instructions (multilingual)
        try:
            font_name = FontManager.get_font_name(self.language, bold=False)
            canvas_obj.setFont(font_name, 6)
        except:
            canvas_obj.setFont("Helvetica", 6)
        
        canvas_obj.setFillColor(HexColor("#CCCCCC"))
        
        # Build footer text with translations
        footer_parts = [
            self._format_translation('cover_print_borderless'),
            self._format_translation('cover_follow_cutting'),
            "Binder Pokédex Project",  # Keep project name in English
            datetime.now().strftime('%Y-%m-%d')
        ]
        footer_text = " • ".join(footer_parts)
        text_width = canvas_obj.stringWidth(footer_text, canvas_obj._fontname, 6) if hasattr(canvas_obj, '_fontname') else len(footer_text) * 2
        x_pos = (PAGE_WIDTH - text_width) / 2
        canvas_obj.drawString(x_pos, 2.5 * mm, footer_text)
    
    @staticmethod
    def _darken_color(hex_color: str, factor: float = 0.6) -> str:
        """Darken a hex color by multiplying RGB values by factor."""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"
    
    
    def generate(self, pokemon_list: list = None) -> Path:
        """
        Generate the complete PDF with cover page and cards.
        
        Uses unified rendering modules (CardRenderer, CoverRenderer, PageRenderer)
        for consistent quality across all PDF types.
        
        Args:
            pokemon_list: List of Pokémon to render (optional, uses self.pokemon_list if not provided)
        
        Returns:
            Path to generated PDF file
        
        Raises:
            ValueError: If no Pokémon list is available
            IOError: If PDF cannot be written
        """
        if pokemon_list:
            self.set_pokemon_list(pokemon_list)
        
        if not self.pokemon_list:
            raise ValueError("No Pokémon list provided")
        
        # Create output directory structure: output/{language}/
        output_path = Path(OUTPUT_DIR)
        lang_output_path = output_path / self.language
        lang_output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate PDF filename
        lang_code = self.language
        gen_code = self.generation
        pdf_filename = f"{PDF_PREFIX}{gen_code}_{lang_code}{PDF_EXTENSION}"
        pdf_file_path = lang_output_path / pdf_filename
        
        logger.info(f"Starting PDF generation: {pdf_file_path}")
        
        try:
            # Create canvas
            c = canvas.Canvas(str(pdf_file_path), pagesize=A4)
            
            # Draw cover page using unified CoverRenderer
            self.cover_renderer.render_cover(c, self.pokemon_list)
            c.showPage()
            logger.info(f"  Cover page created")
            
            # Render cards (9 per page) using unified CardRenderer and PageRenderer
            card_count = 0
            page_number = 1
            total_cards = len(self.pokemon_list)
            
            for idx, pokemon in enumerate(self.pokemon_list, 1):
                # Progress indicator every 10 cards
                if idx % 10 == 0 or idx == 1:
                    progress_pct = (idx / total_cards) * 100
                    bar_width = 30
                    filled = int(bar_width * progress_pct / 100)
                    bar = '█' * filled + '░' * (bar_width - filled)
                    print(f"\r  [{bar}] {idx}/{total_cards} ({progress_pct:.0f}%)", end='', flush=True)
                
                # Check if we need a new page
                if self.page_renderer.should_start_new_page(card_count):
                    # Add footer before showing page
                    self.page_renderer.add_footer(c)
                    c.showPage()
                    page_number += 1
                    logger.debug(f"  Page {page_number} created ({card_count}/{total_cards} cards)")
                
                # Create new page if needed
                if self.page_renderer.get_card_index_on_page(card_count) == 0:
                    self.page_renderer.create_page(c)
                
                # Calculate position on page
                card_position = self.page_renderer.get_card_index_on_page(card_count)
                
                # Draw the card using unified CardRenderer
                self.page_renderer.add_card_to_page(c, self.card_renderer, pokemon, card_position)
                card_count += 1
            
            # Add footer to last page before showing it
            self.page_renderer.add_footer(c)
            
            # Final page
            c.showPage()
            
            # Save and close the PDF
            c.save()
            
            print()  # Newline after progress bar
            
            file_size_mb = pdf_file_path.stat().st_size / 1024 / 1024
            total_pages = self.page_renderer.get_total_pages(card_count, include_cover=True)
            self.page_count = total_pages  # Store for testing/reporting
            
            logger.info(f"✓ PDF generated successfully: {pdf_file_path}")
            logger.info(f"  - Pages: {total_pages} (with cover)")
            logger.info(f"  - Cards: {card_count}")
            logger.info(f"  - Size: {file_size_mb:.2f} MB")
            
            return pdf_file_path
        
        except IOError as e:
            logger.error(f"Failed to write PDF: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during PDF generation: {e}")
            import traceback
            traceback.print_exc()
            raise


def generate_pdf_for_generation(generation: int, language: str = 'de', 
                               pokemon_data: list = None) -> Path:
    """
    Convenience function to generate a PDF for a specific generation.
    
    Args:
        generation: Pokémon generation (1-9)
        language: Language code (default: 'de')
        pokemon_data: List of pokemon data (if None, uses sample data)
    
    Returns:
        Path to generated PDF
    """
    generator = PDFGenerator(language, generation)
    
    if pokemon_data is None:
        # Generate sample data for testing
        pokemon_data = [
            {'name': f'Pokemon {i}', 'types': ['Normal']}
            for i in range(1, GENERATION_INFO[generation]['count'] + 1)
        ]
    
    return generator.generate(pokemon_data)
