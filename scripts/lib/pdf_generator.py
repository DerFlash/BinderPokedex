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
    from .text_renderer import TextRenderer
    from .constants import (
        LANGUAGES, GENERATION_INFO, PAGE_WIDTH, PAGE_HEIGHT, PAGE_MARGIN,
        CARD_WIDTH, CARD_HEIGHT, CARDS_PER_ROW, CARDS_PER_COLUMN, GAP_X, GAP_Y,
        OUTPUT_DIR, PDF_PREFIX, PDF_EXTENSION, COLORS
    )
except ImportError:
    # Fallback for direct imports (testing)
    from fonts import FontManager
    from text_renderer import TextRenderer
    from constants import (
        LANGUAGES, GENERATION_INFO, PAGE_WIDTH, PAGE_HEIGHT, PAGE_MARGIN,
        CARD_WIDTH, CARD_HEIGHT, CARDS_PER_ROW, CARDS_PER_COLUMN, GAP_X, GAP_Y,
        OUTPUT_DIR, PDF_PREFIX, PDF_EXTENSION, COLORS
    )

logger = logging.getLogger(__name__)


# Generation color scheme for cover pages
GENERATION_COLORS = {
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

# Pokémon type color mapping for card headers
TYPE_COLORS = {
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
        if generation not in GENERATION_INFO:
            raise ValueError(f"Invalid generation: {generation}")
        
        self.language = language
        self.generation = generation
        self.pokemon_list = []
        self.current_page_cards = []
        self.page_count = 0
        self.image_cache = ImageCache()  # Initialize image cache
        
        # Load translations
        if translations is None:
            self.translations = self._load_translations()
        else:
            self.translations = translations
        
        logger.info(f"Initialized PDFGenerator for {LANGUAGES[language]['name']} (Gen {generation})")
    
    def _load_translations(self) -> dict:
        """
        Load translations from i18n/translations.json
        
        Returns:
            Dictionary with translations for current language
        """
        try:
            import json
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
            key: Translation key (e.g., 'pokemon_count_text')
            **kwargs: Variables to format into the string (e.g., count=151)
        
        Returns:
            Formatted translation or key if not found
        """
        text = self.translations.get(key, key)
        
        # Simple template replacement
        for var_name, var_value in kwargs.items():
            text = text.replace(f'{{{{{var_name}}}}}', str(var_value))
        
        return text
    
    def set_pokemon_list(self, pokemon_list: list):
        """
        Set the list of Pokémon to render.
        
        Args:
            pokemon_list: List of pokemon data dictionaries
        """
        self.pokemon_list = pokemon_list
        logger.info(f"Set {len(pokemon_list)} Pokémon for rendering")
    
    def _draw_cutting_guides(self, canvas_obj):
        """
        Draw cutting guides as a continuous grid.
        Lines are drawn in the middle of the gaps between cards.
        Outer frame is drawn around all cards with same offset as gaps.
        """
        canvas_obj.setLineWidth(0.5)
        canvas_obj.setStrokeColor(HexColor("#DDDDDD"))
        canvas_obj.setDash(2, 2)
        
        # Calculate outer frame bounds (with GAP offset)
        # Top frame
        frame_top = PAGE_HEIGHT - PAGE_MARGIN + GAP_Y / 2
        # Bottom frame
        frame_bottom = PAGE_HEIGHT - PAGE_MARGIN - CARDS_PER_COLUMN * CARD_HEIGHT - (CARDS_PER_COLUMN - 1) * GAP_Y - GAP_Y / 2
        
        # Left frame
        frame_left = PAGE_MARGIN - GAP_X / 2
        # Right frame
        frame_right = PAGE_MARGIN + CARDS_PER_ROW * CARD_WIDTH + (CARDS_PER_ROW - 1) * GAP_X + GAP_X / 2
        
        # Vertical lines: outer frame left and right, plus lines between cards
        for col in range(CARDS_PER_ROW + 1):
            if col == 0 or col == CARDS_PER_ROW:
                # Outer frame lines
                x = frame_left if col == 0 else frame_right
            else:
                # Lines in middle of gaps between cards
                x = PAGE_MARGIN + col * CARD_WIDTH + (col - 1) * GAP_X + GAP_X / 2
            
            canvas_obj.line(x, frame_bottom, x, frame_top)
        
        # Horizontal lines: outer frame top and bottom, plus lines between cards
        for row in range(CARDS_PER_COLUMN + 1):
            if row == 0 or row == CARDS_PER_COLUMN:
                # Outer frame lines
                y = frame_top if row == 0 else frame_bottom
            else:
                # Lines in middle of gaps between cards
                y = PAGE_HEIGHT - PAGE_MARGIN - row * CARD_HEIGHT - (row - 1) * GAP_Y - GAP_Y / 2
            
            canvas_obj.line(frame_left, y, frame_right, y)
        
        canvas_obj.setDash()
    
    def _load_type_translations(self):
        """Load type translations from i18n/translations.json"""
        try:
            import json
            # Use absolute path from this file's location
            pdf_generator_file = Path(__file__).resolve()
            translations_path = pdf_generator_file.parent.parent.parent / 'i18n' / 'translations.json'
            
            if translations_path.exists():
                with open(translations_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('types', {})
        except Exception as e:
            logger.warning(f"Could not load type translations: {e}")
        return {}
    
    def _calculate_card_position(self, card_index: int) -> tuple:
        """
        Calculate x, y position for a card on the page.
        
        Args:
            card_index: Index of card on current page (0-8)
        
        Returns:
            (x, y) coordinates in points
        """
        row = card_index // CARDS_PER_ROW
        col = card_index % CARDS_PER_ROW
        
        x = PAGE_MARGIN + col * (CARD_WIDTH + GAP_X)
        y = PAGE_HEIGHT - PAGE_MARGIN - (row + 1) * CARD_HEIGHT - row * GAP_Y
        
        return (x, y)
    
    def _draw_name_with_symbol_fallback(self, canvas_obj, name: str, x: float, width: float, y: float, primary_font: str):
        """
        Draw Pokémon name with gender symbol fallback.
        
        If name contains ♂/♀ symbols and primary font is Helvetica (Latin),
        render text parts with Helvetica and symbols with Songti (better Unicode support).
        
        Args:
            canvas_obj: ReportLab canvas
            name: Full name with potential symbols
            x: Card x position
            width: Card width (for centering)
            y: Y position
            primary_font: Primary font name
        """
        # Split name into parts and symbols
        parts = []
        current_part = ""
        
        for char in name:
            if char in '♂♀':
                if current_part:
                    parts.append(('text', current_part))
                    current_part = ""
                parts.append(('symbol', char))
            else:
                current_part += char
        
        if current_part:
            parts.append(('text', current_part))
        
        # Measure total width to center
        total_width = 0
        for part_type, part_text in parts:
            if part_type == 'text':
                total_width += canvas_obj.stringWidth(part_text, primary_font, 8)
            else:  # symbol
                total_width += canvas_obj.stringWidth(part_text, 'SongtiBold', 8)
        
        # Draw centered
        start_x = x + width / 2 - total_width / 2
        current_x = start_x
        
        for part_type, part_text in parts:
            if part_type == 'text':
                canvas_obj.setFont(primary_font, 8)
                canvas_obj.setFillColor(HexColor("#2D2D2D"))
                canvas_obj.drawString(current_x, y, part_text)
                current_x += canvas_obj.stringWidth(part_text, primary_font, 8)
            else:  # symbol
                canvas_obj.setFont('SongtiBold', 8)
                canvas_obj.setFillColor(HexColor("#2D2D2D"))
                canvas_obj.drawString(current_x, y, part_text)
                current_x += canvas_obj.stringWidth(part_text, 'SongtiBold', 8)
    
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
    
    def _draw_card(self, canvas_obj, pokemon_data: dict, x: float, y: float):
        """
        Draw a single Pokémon card.

        Args:
            canvas_obj: ReportLab canvas object
            pokemon_data: Dictionary with pokemon info (name, type, image, etc.)
            x: X position for card top-left
            y: Y position for card top-left
        """
        # Card background
        header_height = 12 * mm
        
        # Get primary type and its color
        pokemon_type = pokemon_data.get('types', ['Normal'])[0] if pokemon_data.get('types') else 'Normal'
        header_color = TYPE_COLORS.get(pokemon_type, '#A8A878')  # Default to Normal type color
        
        # Draw header with type color and 90% transparency (10% opaque)
        canvas_obj.setFillColor(HexColor(header_color), alpha=0.1)
        canvas_obj.rect(x, y + CARD_HEIGHT - header_height, CARD_WIDTH, header_height, fill=True, stroke=False)
        
        # Card border
        canvas_obj.setLineWidth(0.5)
        canvas_obj.setStrokeColor(HexColor("#CCCCCC"))
        canvas_obj.rect(x, y, CARD_WIDTH, CARD_HEIGHT, fill=False, stroke=True)
        
        # Note: Pokédex number moved to bottom of card (see below)
        
        # Type (header right) - with language translation
        # Get type from either 'types' array or 'type1' field (for compatibility)
        types = pokemon_data.get('types', [])
        if not types and pokemon_data.get('type1'):
            types = [pokemon_data.get('type1')]
        
        if types:
            type_english = types[0]  # Use first type (English name)
            # Translate type to current language
            type_translations = self._load_type_translations()
            language_types = type_translations.get(self.language, type_translations.get('en', {}))
            type_text = language_types.get(type_english, type_english)
            
            try:
                # Use same font approach as Pokémon names - this works for CJK!
                type_font = FontManager.get_font_name(self.language, bold=False)
                canvas_obj.setFont(type_font, 5)
            except:
                canvas_obj.setFont("Helvetica", 5)
            
            canvas_obj.setFillColor(HexColor("#5D5D5D"))
            # Use drawRightString for proper right-alignment without overflow
            type_x = x + CARD_WIDTH - 3  # Right edge with margin
            type_y = y + CARD_HEIGHT - header_height + 6
            canvas_obj.drawRightString(type_x, type_y, type_text)
        
        # Pokémon name (centered, using proper font for language)
        name = pokemon_data.get('name', 'Unknown')
        name_en = pokemon_data.get('name_en', 'Unknown')
        
        try:
            font_name = FontManager.get_font_name(self.language, bold=True)
            
            # Render centered Pokémon name
            canvas_obj.setFont(font_name, 8)
            canvas_obj.setFillColor(HexColor("#2D2D2D"))
            name_y = y + CARD_HEIGHT - header_height + 11
            
            # Check if name contains gender symbols that might not render in Latin fonts
            if ('♂' in name or '♀' in name) and font_name == 'Helvetica-Bold':
                # Split name and symbols to render them separately with fallback font
                self._draw_name_with_symbol_fallback(canvas_obj, name, x, CARD_WIDTH, name_y, font_name)
            else:
                # Render normally (CJK fonts handle symbols fine)
                canvas_obj.drawCentredString(x + CARD_WIDTH / 2, name_y, name)
            
            # Add English subtitle for non-English languages
            if self.language != 'en' and name_en != 'Unknown' and name_en != name:
                canvas_obj.setFont("Helvetica", 4)
                canvas_obj.setFillColor(HexColor("#999999"))
                name_en_y = y + CARD_HEIGHT - header_height + 3
                canvas_obj.drawCentredString(x + CARD_WIDTH / 2, name_en_y, name_en)
                
        except Exception as e:
            logger.warning(f"Could not render name '{name}': {e}")
            # Fallback to Helvetica
            canvas_obj.setFont("Helvetica-Bold", 8)
            canvas_obj.setFillColor(HexColor("#2D2D2D"))
            canvas_obj.drawCentredString(x + CARD_WIDTH / 2, y + CARD_HEIGHT - header_height + 11, name)
        
        # Image area (white background)
        image_height = CARD_HEIGHT - header_height - 4 * mm
        canvas_obj.setFillColor(HexColor("#FFFFFF"))
        canvas_obj.rect(x, y, CARD_WIDTH, image_height, fill=True, stroke=False)
        
        # Draw index number centered at bottom of card
        poke_num = pokemon_data.get('id') or pokemon_data.get('num', '???')
        poke_num_str = f"#{poke_num}" if not str(poke_num).startswith('#') else str(poke_num)
        darkened_type_color = self._darken_color(header_color, factor=0.6)
        canvas_obj.setFont("Helvetica-Bold", 16)
        canvas_obj.setFillColor(HexColor(darkened_type_color))
        canvas_obj.drawCentredString(x + CARD_WIDTH / 2, y + 4 * mm, poke_num_str)
        
        # Image (if available - from image_url or image_path)
        image_source = pokemon_data.get('image_path') or pokemon_data.get('image_url')
        
        logger.debug(f"Processing card for {pokemon_data.get('name', '???')}: image_source={image_source is not None}")
        
        if image_source:
            try:
                image_to_render = None
                
                if image_source.startswith('http://') or image_source.startswith('https://'):
                    # It's a URL - load from cache first, fallback to download
                    pokemon_id = pokemon_data.get('id')
                    logger.debug(f"  Getting image for #{pokemon_id}...")
                    image_data = self.image_cache.get_image(pokemon_id, url=image_source)
                    if image_data:
                        logger.debug(f"  ✓ Got image")
                        image_to_render = image_data
                    else:
                        logger.debug(f"  ✗ Failed to get image data")
                else:
                    # It's a local path
                    if Path(image_source).exists():
                        logger.debug(f"  Using local path: {image_source}")
                        image_to_render = image_source
                
                if image_to_render:
                    logger.debug(f"  Drawing image...")
                    padding = 2 * mm
                    max_width = (CARD_WIDTH - 2 * padding) / 2
                    max_height = (image_height - 2 * padding) / 2
                    
                    img_x = x + (CARD_WIDTH - max_width) / 2
                    img_y = y + (image_height - max_height) / 2 + padding
                    
                    canvas_obj.drawImage(
                        image_to_render, img_x, img_y,
                        width=max_width, height=max_height,
                        preserveAspectRatio=True
                    )
                    logger.debug(f"  ✓ Image drawn")
            except Exception as e:
                logger.debug(f"Could not render image from {image_source}: {e}")
                import traceback
                traceback.print_exc()
        
        # Additional metadata could be added here
        # (HP, Dex number, etc.)
    
    def generate(self, pokemon_list: list = None) -> Path:
        """
        Generate the complete PDF with cover page and cards.
        
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
            
            # Draw cover page
            self._draw_cover_page(c)
            c.showPage()
            logger.info(f"  Cover page created")
            
            # Render cards (9 per page)
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
                    # Print progress bar directly without logging to avoid line breaks
                    print(f"\r  [{bar}] {idx}/{total_cards} ({progress_pct:.0f}%)", end='', flush=True)
                
                # Check if we need a new page (9 cards per page)
                if card_count % (CARDS_PER_ROW * CARDS_PER_COLUMN) == 0 and card_count > 0:
                    # Add footer before showing page
                    c.setFont("Helvetica", 6)
                    c.setFillColor(HexColor("#AAAAAA"))
                    footer_text = f"Binder Pokédex Project | github.com/BinderPokedex"
                    c.drawCentredString(PAGE_WIDTH / 2, 8, footer_text)
                    c.showPage()
                    page_number += 1
                    logger.debug(f"  Page {page_number} created ({card_count}/{len(self.pokemon_list)} cards)")
                
                # White background for page
                if card_count % (CARDS_PER_ROW * CARDS_PER_COLUMN) == 0:
                    c.setFillColor(HexColor("#FFFFFF"))
                    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=True, stroke=False)
                    # Draw cutting guides for the new page
                    self._draw_cutting_guides(c)
                
                # Calculate position on page
                card_position = card_count % (CARDS_PER_ROW * CARDS_PER_COLUMN)
                x, y = self._calculate_card_position(card_position)
                
                # Draw the card
                self._draw_card(c, pokemon, x, y)
                card_count += 1
            
            # Add footer to last page before showing it
            c.setFont("Helvetica", 6)
            c.setFillColor(HexColor("#AAAAAA"))
            footer_text = f"Binder Pokédex Project | github.com/BinderPokedex"
            c.drawCentredString(PAGE_WIDTH / 2, 8, footer_text)
            
            # Final page
            c.showPage()
            
            # Save and close the PDF
            c.save()
            
            print()  # Newline after progress bar
            
            file_size_mb = pdf_file_path.stat().st_size / 1024 / 1024
            total_pages = 1 + (card_count + 8) // 9  # +1 for cover page
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
