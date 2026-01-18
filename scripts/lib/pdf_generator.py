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
from pathlib import Path
from datetime import datetime
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
    """Image cache returning ImageReader objects for ReportLab's drawImage."""
    
    def __init__(self):
        self.cache = {}
    
    def get_image(self, url: str, timeout: int = 5, max_width: int = 100):
        """
        Get ImageReader object from cache or download from URL.
        
        Args:
            url: Image URL
            timeout: Download timeout in seconds
            max_width: Max width in pixels for resizing (to reduce file size)
        
        Returns:
            ImageReader object if successful, None otherwise
        """
        if url in self.cache:
            # Reset position for ImageReader
            self.cache[url].seek(0)
            logger.debug(f"✓ Image cached (size so far: {len(self.cache)} unique images)")
            return self.cache[url]
        
        try:
            logger.debug(f"⬇ Downloading image: {url.split('/')[-1]}")
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'BinderPokedex/2.0'}
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                image_data = BytesIO(response.read())
                image_data.seek(0)
                
                # Load with PIL
                pil_image = Image.open(image_data)
                
                # Convert to RGBA to access alpha channel
                if pil_image.mode != 'RGBA':
                    pil_image = pil_image.convert('RGBA')
                
                # Replace transparent pixels with white (card background color)
                # Create new image with white background
                background = Image.new('RGB', pil_image.size, (255, 255, 255))
                background.paste(pil_image, mask=pil_image.split()[3] if pil_image.mode == 'RGBA' else None)
                pil_image = background
                
                # Resize to reduce file size (keep aspect ratio)
                if pil_image.width > max_width:
                    ratio = max_width / pil_image.width
                    new_height = int(pil_image.height * ratio)
                    pil_image = pil_image.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
                # Save to BytesIO with JPEG compression
                output = BytesIO()
                pil_image.save(output, format='JPEG', quality=40, optimize=True)
                output.seek(0)
                
                # Wrap in ImageReader for ReportLab
                image_reader = ImageReader(output)
                self.cache[url] = image_reader
                logger.debug(f"✓ Downloaded & cached (total: {len(self.cache)} images)")
                return image_reader
        except (urllib.error.URLError, urllib.error.HTTPError, Exception) as e:
            logger.debug(f"✗ Failed to download image from {url}: {e}")
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
    
    def __init__(self, language: str, generation: int):
        """
        Initialize PDF generator.
        
        Args:
            language: Language code (e.g., 'de', 'ja', 'zh_hans')
            generation: Pokémon generation (1-9)
        
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
        
        logger.info(f"Initialized PDFGenerator for {LANGUAGES[language]['name']} (Gen {generation})")
    
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
        Lines are drawn at exact positions where cards should be cut.
        """
        cut_offset = 2 * mm
        canvas_obj.setLineWidth(0.5)
        canvas_obj.setStrokeColor(HexColor("#DDDDDD"))
        canvas_obj.setDash(2, 2)
        
        # Vertical lines
        for col in range(CARDS_PER_ROW + 1):
            x = PAGE_MARGIN + col * (CARD_WIDTH + GAP_X) - cut_offset
            canvas_obj.line(x, PAGE_MARGIN - cut_offset, x, PAGE_HEIGHT - PAGE_MARGIN + cut_offset)
        
        # Horizontal lines
        for row in range(CARDS_PER_COLUMN + 1):
            y = PAGE_HEIGHT - PAGE_MARGIN - row * (CARD_HEIGHT + GAP_Y) + cut_offset
            canvas_obj.line(PAGE_MARGIN - cut_offset, y, PAGE_WIDTH - PAGE_MARGIN + cut_offset, y)
        
        canvas_obj.setDash()
    
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
        Draw a cover page for the generation.
        
        Args:
            canvas_obj: ReportLab canvas object
        """
        # White background
        canvas_obj.setFillColor(HexColor("#FFFFFF"))
        canvas_obj.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=True, stroke=False)
        
        # Get generation color
        gen_color = GENERATION_COLORS.get(self.generation, '#999999')
        
        # Colored stripe
        stripe_height = PAGE_HEIGHT * 0.4
        canvas_obj.setFillColor(HexColor(gen_color))
        canvas_obj.rect(0, PAGE_HEIGHT - stripe_height, PAGE_WIDTH, stripe_height, fill=True, stroke=False)
        
        # Title
        canvas_obj.setFont("Helvetica-Bold", 48)
        canvas_obj.setFillColor(HexColor("#FFFFFF"))
        title_y = PAGE_HEIGHT - stripe_height + (stripe_height * 0.55)
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, title_y, "BinderPokedex")
        
        # Generation number
        canvas_obj.setFont("Helvetica", 28)
        canvas_obj.setFillColor(HexColor(gen_color))
        gen_y = PAGE_HEIGHT / 2 + 50 * mm
        gen_text = f"Generation {self.generation}"
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, gen_y, gen_text)
        
        # Get generation info
        gen_info = GENERATION_INFO[self.generation]
        
        # Region name (use Helvetica for now - can be enhanced with CJK support)
        canvas_obj.setFont("Helvetica", 32)
        canvas_obj.setFillColor(HexColor(gen_color))
        region_y = gen_y - 40
        region_name = gen_info.get('region', f'Generation {self.generation}')
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, region_y, region_name)
        
        # ID range
        canvas_obj.setFont("Helvetica", 18)
        canvas_obj.setFillColor(HexColor("#666666"))
        count_y = region_y - 40
        start_id, end_id = gen_info['range']
        id_range_text = f"Pokédex #{start_id:03d} - #{end_id:03d}"
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, count_y, id_range_text)
        
        # Pokémon count
        canvas_obj.setFont("Helvetica", 16)
        pokemon_text = f"{len(self.pokemon_list)} Pokémon"
        count_text_y = count_y - 30
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, count_text_y, pokemon_text)
        
        # Decorative line
        canvas_obj.setStrokeColor(HexColor(gen_color))
        canvas_obj.setLineWidth(2)
        line_y = count_text_y - 50
        canvas_obj.line(50 * mm, line_y, PAGE_WIDTH - 50 * mm, line_y)
        
        # Footer
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(HexColor("#CCCCCC"))
        date_text = f"Generated: {datetime.now().strftime('%Y-%m-%d')}"
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, 20, date_text)
    
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
        
        # Pokédex number (header left)
        poke_num = pokemon_data.get('num', '#???')
        canvas_obj.setFont("Helvetica-Bold", 9)
        canvas_obj.setFillColor(HexColor("#3D3D3D"))
        canvas_obj.drawString(x + 3, y + CARD_HEIGHT - header_height + 5, poke_num)
        
        # Type (header right)
        types = pokemon_data.get('types', [])
        if types:
            type_text = types[0]  # Use first type
            canvas_obj.setFont("Helvetica", 5)
            type_width = canvas_obj.stringWidth(type_text, "Helvetica", 5)
            canvas_obj.setFillColor(HexColor("#5D5D5D"))
            canvas_obj.drawString(x + CARD_WIDTH - type_width - 3, y + CARD_HEIGHT - header_height + 5, type_text)
        
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
        
        # Image (if available - from image_url or image_path)
        image_source = pokemon_data.get('image_path') or pokemon_data.get('image_url')
        
        logger.debug(f"Processing card for {pokemon_data.get('name', '???')}: image_source={image_source is not None}")
        
        if image_source:
            try:
                image_to_render = None
                
                if image_source.startswith('http://') or image_source.startswith('https://'):
                    # It's a URL - download via cache
                    logger.debug(f"  Downloading from URL: {image_source[:60]}...")
                    image_data = self.image_cache.get_image(image_source)
                    if image_data:
                        logger.debug(f"  ✓ Got PIL Image object")
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
