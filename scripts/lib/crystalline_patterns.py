"""
Crystal Patterns - Crystalline abstract designs for variant separators

Provides methods to draw decorative crystalline patterns for:
- Tera pages (rainbow crystal fragments)
- Mega pages (gold crystalline sparkles)
"""

from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as canvas_module
import random


class CrystallinePatterns:
    """Generate crystalline abstract patterns for variant pages."""
    
    # Rainbow colors for Tera pattern
    TERA_RAINBOW = [
        "#FF0000",  # Red
        "#FF7F00",  # Orange
        "#FFFF00",  # Yellow
        "#00FF00",  # Green
        "#0000FF",  # Blue
        "#4B0082",  # Indigo
        "#9400D3",  # Violet
        "#FF1493",  # Deep Pink
    ]
    
    # Gold variations for Mega pattern
    MEGA_GOLD = [
        "#FFD700",  # Gold
        "#FFC700",  # Darker Gold
        "#FFED4E",  # Bright Gold
        "#D4AF37",  # Medium Gold
        "#AA8C2C",  # Dark Gold
    ]
    
    # Rocket/Evil theme colors (dark red/purple)
    ROCKET_EVIL = [
        "#8B0000",  # Dark Red
        "#4B0082",  # Indigo
        "#2F004F",  # Dark Purple
        "#8B008B",  # Dark Magenta
        "#DC143C",  # Crimson
    ]
    
    # Trainer Exclusive (green/silver theme)
    TRAINER_EXCLUSIVE = [
        "#2E8B57",  # Sea Green
        "#C0C0C0",  # Silver
        "#90EE90",  # Light Green
        "#B0C4DE",  # Light Steel Blue
        "#D3D3D3",  # Light Gray
    ]
    
    @staticmethod
    def draw_pattern_on_stripe(c, bound_x, bound_y, bound_width, bound_height, 
                               pattern_type: str, primary_color: str = None):
        """
        Draw crystalline pattern on a bounded stripe area.
        
        Args:
            c: Canvas object
            bound_x: Left boundary (x)
            bound_y: Bottom boundary (y)
            bound_width: Width of bounded area
            bound_height: Height of bounded area
            pattern_type: Type of pattern ('crystalline_abstract_rainbow', 'crystalline_abstract_gold', etc.)
            primary_color: Optional override color for the stripe base
        """
        if pattern_type == 'crystalline_abstract_rainbow':
            colors = CrystallinePatterns.TERA_RAINBOW
            density = 20
            opacity = 0.25
            overlay_color = "#A335EE"
            overlay_alpha = 0.08
        elif pattern_type == 'crystalline_abstract_gold' or pattern_type == 'mega_evolution':
            colors = CrystallinePatterns.MEGA_GOLD
            density = 20
            opacity = 0.25
            overlay_color = "#FFD700"
            overlay_alpha = 0.08
        elif pattern_type == 'primal_reversion':
            # Use teal/turquoise colors for Primal
            colors = ["#00897B", "#00A89D", "#26A69A", "#4DB6AC", "#80CBC4"]
            density = 20
            opacity = 0.25
            overlay_color = "#00897B"
            overlay_alpha = 0.08
        elif pattern_type == 'rocket_evil':
            colors = CrystallinePatterns.ROCKET_EVIL
            density = 15
            opacity = 0.2
            overlay_color = "#8B0000"
            overlay_alpha = 0.06
        elif pattern_type == 'trainer_exclusive':
            colors = CrystallinePatterns.TRAINER_EXCLUSIVE
            density = 15
            opacity = 0.2
            overlay_color = "#2E8B57"
            overlay_alpha = 0.06
        else:
            # Default: subtle pattern
            colors = ["#CCCCCC", "#DDDDDD", "#EEEEEE"]
            density = 10
            opacity = 0.15
            overlay_color = "#000000"
            overlay_alpha = 0.05
        
        # Draw crystalline fragments in bounded area
        CrystallinePatterns._draw_crystalline_fragments_bounded(
            c, bound_x, bound_y, bound_width, bound_height,
            colors=colors,
            density=density,
            opacity=opacity
        )
        
        # Add semi-transparent overlay for readability/contrast
        c.setFillColor(HexColor(overlay_color), alpha=overlay_alpha)
        c.rect(bound_x, bound_y, bound_width, bound_height, fill=True, stroke=False)
    
    @staticmethod
    def draw_tera_separator(c, page_width, page_height, title_text: str = "", featured_pokemon: list = None):
        """
        Draw Tera separator page with rainbow crystalline pattern in upper section.
        Layout matches cover page but with crystalline pattern instead of solid bar.
        
        Args:
            c: ReportLab canvas object
            page_width: Page width
            page_height: Page height
            title_text: Optional title text to display
            featured_pokemon: Optional list of 3 Pokémon dicts to display
        """
        # White background
        c.setFillColor(HexColor("#FFFFFF"))
        c.rect(0, 0, page_width, page_height, fill=True, stroke=False)
        
        # Upper section with crystalline pattern (100mm like cover)
        stripe_height = 100 * mm
        
        # Draw crystalline fragments in upper section
        CrystallinePatterns._draw_crystalline_fragments_bounded(
            c, 0, page_height - stripe_height, page_width, stripe_height,
            colors=CrystallinePatterns.TERA_RAINBOW,
            density=20,
            opacity=0.25
        )
        
        # Add semi-transparent overlay for readability
        c.setFillColor(HexColor("#A335EE"), alpha=0.08)
        c.rect(0, page_height - stripe_height, page_width, stripe_height, fill=True, stroke=False)
        
        # Title in upper section (like cover page)
        if title_text:
            c.setFont("Helvetica-Bold", 42)
            c.setFillColor(HexColor("#FFFFFF"))
            title_y = page_height - 30 * mm
            c.drawCentredString(page_width / 2, title_y, title_text)
            
            # Decorative underline
            c.setStrokeColor(HexColor("#FFFFFF"))
            c.setLineWidth(1.5)
            c.line(40 * mm, title_y - 8, page_width - 40 * mm, title_y - 8)
        
        # Lower section - white space with decorative elements
        c.setStrokeColor(HexColor("#A335EE"), alpha=0.3)
        c.setLineWidth(1)
        c.line(30 * mm, 50 * mm, page_width - 30 * mm, 50 * mm)
        
        # Draw featured Pokémon at bottom (3 images)
        if featured_pokemon:
            CrystallinePatterns._draw_featured_pokemon_images(
                c, page_width, page_height, featured_pokemon, accent_color="#A335EE"
            )
    
    @staticmethod
    def draw_mega_separator(c, page_width, page_height, title_text: str = "", featured_pokemon: list = None):
        """
        Draw Mega separator page with gold crystalline pattern in upper section.
        Layout matches cover page but with crystalline pattern instead of solid bar.
        
        Args:
            c: ReportLab canvas object
            page_width: Page width
            page_height: Page height
            title_text: Optional title text to display
            featured_pokemon: Optional list of 3 Pokémon dicts to display
        """
        # White background
        c.setFillColor(HexColor("#FFFFFF"))
        c.rect(0, 0, page_width, page_height, fill=True, stroke=False)
        
        # Upper section with crystalline pattern (100mm like cover)
        stripe_height = 100 * mm
        
        # Draw crystalline fragments in upper section
        CrystallinePatterns._draw_crystalline_fragments_bounded(
            c, 0, page_height - stripe_height, page_width, stripe_height,
            colors=CrystallinePatterns.MEGA_GOLD,
            density=18,
            opacity=0.22
        )
        
        # Add darker overlay for depth and readability
        c.setFillColor(HexColor("#D4AF37"), alpha=0.12)
        c.rect(0, page_height - stripe_height, page_width, stripe_height, fill=True, stroke=False)
        
        # Title in upper section (like cover page)
        if title_text:
            c.setFont("Helvetica-Bold", 42)
            c.setFillColor(HexColor("#1A1A1A"))
            title_y = page_height - 30 * mm
            c.drawCentredString(page_width / 2, title_y, title_text)
            
            # Decorative underline in gold
            c.setStrokeColor(HexColor("#AA8C2C"))
            c.setLineWidth(2)
            c.line(40 * mm, title_y - 8, page_width - 40 * mm, title_y - 8)
        
        # Lower section - white space with decorative gold elements
        c.setStrokeColor(HexColor("#FFD700"), alpha=0.4)
        c.setLineWidth(1.5)
        c.line(30 * mm, 50 * mm, page_width - 30 * mm, 50 * mm)
        
        # Draw featured Pokémon at bottom (3 images)
        if featured_pokemon:
            CrystallinePatterns._draw_featured_pokemon_images(
                c, page_width, page_height, featured_pokemon, accent_color="#FFD700"
            )
    
    @staticmethod
    def _draw_crystalline_fragments(c, page_width, page_height, colors: list, density: int, opacity: float):
        """
        Draw scattered crystalline fragments using geometric shapes.
        
        Creates random polygons to simulate crystal fragments across the page.
        
        Args:
            c: Canvas object
            page_width: Page width
            page_height: Page height
            colors: List of hex colors to use
            density: Number of fragments to draw
            opacity: Fragment opacity (0.0-1.0)
        """
        random.seed(42)  # Consistent pattern
        
        for _ in range(density):
            # Random position
            x = random.uniform(0, page_width)
            y = random.uniform(0, page_height)
            
            # Random size
            size = random.uniform(20 * mm, 80 * mm)
            
            # Random color
            color = random.choice(colors)
            
            # Random number of sides (3-6 = triangle to hexagon)
            sides = random.randint(3, 6)
            
            # Random rotation
            rotation = random.uniform(0, 360)
            
            c.setFillColor(HexColor(color), alpha=opacity)
            c.setStrokeColor(HexColor(color), alpha=opacity * 0.5)
            c.setLineWidth(0.5)
            
            # Draw polygon
            CrystallinePatterns._draw_polygon(c, x, y, sides, size, rotation)
    
    @staticmethod
    def _draw_crystalline_fragments_bounded(c, bound_x, bound_y, bound_width, bound_height,
                                           colors: list, density: int, opacity: float):
        """
        Draw crystalline fragments constrained to a bounded region.
        
        Args:
            c: Canvas object
            bound_x: Left boundary
            bound_y: Bottom boundary
            bound_width: Width of region
            bound_height: Height of region
            colors: List of hex colors to use
            density: Number of fragments to draw
            opacity: Fragment opacity (0.0-1.0)
        """
        random.seed(42)  # Consistent pattern
        
        for _ in range(density):
            # Random position within bounds
            x = random.uniform(bound_x, bound_x + bound_width)
            y = random.uniform(bound_y, bound_y + bound_height)
            
            # Random size (smaller to fit in bounded area)
            size = random.uniform(15 * mm, 60 * mm)
            
            # Random color
            color = random.choice(colors)
            
            # Random number of sides (3-6)
            sides = random.randint(3, 6)
            
            # Random rotation
            rotation = random.uniform(0, 360)
            
            c.setFillColor(HexColor(color), alpha=opacity)
            c.setStrokeColor(HexColor(color), alpha=opacity * 0.5)
            c.setLineWidth(0.5)
            
            # Draw polygon
            CrystallinePatterns._draw_polygon(c, x, y, sides, size, rotation)
    
    @staticmethod
    def _draw_polygon(c, center_x, center_y, sides: int, size: float, rotation: float = 0):
        """
        Draw a regular polygon.
        
        Args:
            c: Canvas object
            center_x: Center X coordinate
            center_y: Center Y coordinate
            sides: Number of sides (3-8)
            size: Approximate radius of polygon
            rotation: Rotation angle in degrees
        """
        import math
        
        # Calculate points
        points = []
        angle_step = 360 / sides
        
        for i in range(sides):
            angle_rad = math.radians(rotation + i * angle_step)
            px = center_x + size * math.cos(angle_rad)
            py = center_y + size * math.sin(angle_rad)
            points.append((px, py))
        
        # Draw polygon
        path = c.beginPath()
        path.moveTo(points[0][0], points[0][1])
        for point in points[1:]:
            path.lineTo(point[0], point[1])
        path.close()
        c.drawPath(path, stroke=True, fill=True)
    
    @staticmethod
    def _draw_corner_sparkles(c, page_width, page_height, sparkle_count: int = 8):
        """
        Draw decorative sparkles in corners.
        
        Args:
            c: Canvas object
            page_width: Page width
            page_height: Page height
            sparkle_count: Number of sparkles per corner
        """
        corners = [
            (30 * mm, 30 * mm),                              # Bottom-left
            (page_width - 30 * mm, 30 * mm),                # Bottom-right
            (30 * mm, page_height - 30 * mm),               # Top-left
            (page_width - 30 * mm, page_height - 30 * mm),  # Top-right
        ]
        
        random.seed(42)
        
        for corner_x, corner_y in corners:
            for _ in range(sparkle_count):
                # Random offset from corner
                offset_x = random.uniform(-15 * mm, 15 * mm)
                offset_y = random.uniform(-15 * mm, 15 * mm)
                
                x = corner_x + offset_x
                y = corner_y + offset_y
                
                # Small star sparkle
                c.setStrokeColor(HexColor("#FFD700"), alpha=0.3)
                c.setLineWidth(0.5)
                
                r = 3 * mm
                # Draw 4-pointed star
                c.line(x - r, y, x + r, y)
                c.line(x, y - r, x, y + r)
    
    @staticmethod
    def _draw_featured_pokemon_images(c, page_width, page_height, featured_pokemon: list, accent_color: str = "#A335EE"):
        """
        Draw 3 featured Pokémon images at the bottom of separator page.
        
        Args:
            c: Canvas object
            page_width: Page width
            page_height: Page height
            featured_pokemon: List of up to 3 Pokémon dicts (must have 'image_url' or 'name_en')
            accent_color: Color for accent elements
        """
        if not featured_pokemon or len(featured_pokemon) == 0:
            return
        
        # Show up to 3 Pokémon
        pokemon_to_show = featured_pokemon[:3]
        
        # Positions for 3 Pokémon at bottom
        spacing = page_width / 4
        base_y = 20 * mm
        
        for idx, pokemon in enumerate(pokemon_to_show):
            x = spacing * (idx + 1)
            
            # Draw small frame box
            box_size = 25 * mm
            c.setStrokeColor(HexColor(accent_color), alpha=0.5)
            c.setLineWidth(1)
            c.rect(x - box_size / 2, base_y - box_size / 2, box_size, box_size, 
                   fill=False, stroke=True)
            
            # Try to display Pokémon name or ID
            pokemon_name = pokemon.get('name_en', pokemon.get('id', f"#{idx+1}"))
            c.setFont("Helvetica", 7)
            c.setFillColor(HexColor("#666666"))
            c.drawCentredString(x, base_y - 15 * mm, pokemon_name[:15])  # Truncate if too long


def add_separator_pages_to_pdf(pdf_generator, sections: list, pokemon_by_section: dict):
    """
    Helper function to add separator pages to variant PDFs.
    
    Args:
        pdf_generator: VariantPDFGenerator instance
        sections: List of section definitions from variant JSON
        pokemon_by_section: Dict mapping section_id to pokemon list
    
    Returns:
        Modified pokemon_list with separator markers
    """
    if not sections:
        return []
    
    # Filter sections that are separator pages
    separator_sections = [s for s in sections if s.get('is_separator_page', False)]
    
    for section in separator_sections:
        section_id = section.get('section_id')
        pattern = section.get('pattern', 'standard')
        
        # Store separator info for later rendering
        if not hasattr(pdf_generator, 'separator_pages'):
            pdf_generator.separator_pages = []
        
        pdf_generator.separator_pages.append({
            'pattern': pattern,
            'section_id': section_id,
            'section_name': section.get(f'section_name_{pdf_generator.language}', section_id),
            'order': section.get('section_order', 999)
        })
    
    return separator_sections
