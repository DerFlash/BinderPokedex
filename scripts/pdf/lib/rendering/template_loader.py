"""
Template Loader - SVG Template System

Loads and processes SVG templates for card rendering.
Handles variable substitution and coordinates rendering pipeline.
"""

import logging
import re
from pathlib import Path
from typing import Dict, Optional, Tuple
from io import BytesIO

from reportlab.lib.units import mm

try:
    from svglib.svglib import renderSVG
    from reportlab.graphics import renderPDF
except ImportError:
    renderSVG = None
    renderPDF = None
    logging.warning("svglib not available - template rendering disabled")

from .inline_logo_renderer import InlineLogoRenderer

logger = logging.getLogger(__name__)


class TemplateLoader:
    """Loads and processes SVG templates."""
    
    # Template base directory
    TEMPLATE_DIR = Path(__file__).parent.parent.parent.parent / 'config' / 'templates'
    
    @classmethod
    def load_card_template(cls, template_name: str) -> Optional[str]:
        """
        Load card template SVG content.
        
        Args:
            template_name: Template name (e.g., 'classic', 'compact')
                          Extension (.svg) is optional
        
        Returns:
            SVG content as string, or None if not found
        """
        if not template_name.endswith('.svg'):
            template_name = f"{template_name}.svg"
        
        template_path = cls.TEMPLATE_DIR / 'cards' / template_name
        
        if not template_path.exists():
            logger.error(f"Card template not found: {template_path}")
            return None
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load card template {template_path}: {e}")
            return None
    
    @classmethod
    def load_page_template(cls, template_name: str) -> Optional[str]:
        """Load page template SVG content."""
        if not template_name.endswith('.svg'):
            template_name = f"{template_name}.svg"
        
        template_path = cls.TEMPLATE_DIR / 'pages' / template_name
        
        if not template_path.exists():
            logger.error(f"Page template not found: {template_path}")
            return None
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load page template {template_path}: {e}")
            return None
    
    @classmethod
    def load_cover_template(cls, template_name: str) -> Optional[str]:
        """Load cover template SVG content."""
        if not template_name.endswith('.svg'):
            template_name = f"{template_name}.svg"
        
        template_path = cls.TEMPLATE_DIR / 'covers' / template_name
        
        if not template_path.exists():
            logger.error(f"Cover template not found: {template_path}")
            return None
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load cover template {template_path}: {e}")
            return None
    
    @staticmethod
    def substitute_variables(svg_content: str, variables: Dict[str, str]) -> str:
        """
        Replace template variables with values.
        
        Args:
            svg_content: SVG content with {{variable}} placeholders
            variables: Dict of variable_name -> value
        
        Returns:
            SVG content with substituted values
        """
        for var_name, value in variables.items():
            placeholder = f"{{{{{var_name}}}}}"  # {{variable}}
            svg_content = svg_content.replace(placeholder, str(value))
        
        return svg_content
    
    @staticmethod
    def render_svg_to_canvas(svg_content: str, canvas, x: float, y: float) -> bool:
        """
        Render SVG content to ReportLab canvas.
        
        Args:
            svg_content: SVG as string
            canvas: ReportLab canvas object
            x: X position (bottom-left)
            y: Y position (bottom-left)
        
        Returns:
            True if successful, False otherwise
        """
        if not renderSVG or not renderPDF:
            logger.error("svglib not available")
            return False
        
        try:
            # SVG string → Drawing object
            svg_io = BytesIO(svg_content.encode('utf-8'))
            drawing = renderSVG.svg2rlg(svg_io)
            
            if not drawing:
                logger.error("Failed to parse SVG")
                return False
            
            # Drawing → Canvas
            renderPDF.draw(drawing, canvas, x, y)
            return True
        
        except Exception as e:
            logger.error(f"Failed to render SVG to canvas: {e}")
            return False


class CardTemplateRenderer:
    """Renders card templates with dynamic content."""
    
    def __init__(self, template_name: str = 'classic'):
        """
        Initialize card template renderer.
        
        Args:
            template_name: Card template to use (default: 'classic')
        """
        self.template_name = template_name
        self.template_content = TemplateLoader.load_card_template(template_name)
        
        if not self.template_content:
            raise ValueError(f"Could not load card template: {template_name}")
    
    def render(self, canvas, pokemon_data: dict, x: float, y: float,
               language: str = 'en', image_cache=None) -> bool:
        """
        Render card at position.
        
        Args:
            canvas: ReportLab canvas
            pokemon_data: Pokemon data dict
            x: X position (bottom-left)
            y: Y position (bottom-left)
            language: Language code for translations
            image_cache: Image cache for Pokemon images
        
        Returns:
            True if successful
        """
        # This will be implemented with inline logo renderer
        # For now, just prepare the SVG structure
        
        from ..constants import TYPE_COLORS
        
        # Get type and color
        types = pokemon_data.get('types', [])
        if not types and pokemon_data.get('type1'):
            types = [pokemon_data.get('type1')]
        if not types:
            types = ['Normal']
        
        pokemon_type = types[0]
        type_color = TYPE_COLORS.get(pokemon_type, TYPE_COLORS['Normal'])
        
        # Prepare variables (basic ones, name/image handled separately)
        variables = {
            'type': pokemon_type,  # Will be translated later
            'type_color': type_color,
            'type_color_dark': self._darken_color(type_color),
            'id': self._format_id(pokemon_data),
        }
        
        # Substitute variables
        svg_content = TemplateLoader.substitute_variables(
            self.template_content,
            variables
        )
        
        # Render SVG structure (without name/image - those are rendered separately)
        success = TemplateLoader.render_svg_to_canvas(svg_content, canvas, x, y)
        
        # Render name with inline logos
        # Template should define anchor point for name (e.g., at 31.5mm, 82mm)
        # For now, use hardcoded positions (will be extracted from template later)
        pokemon_name = pokemon_data.get('name', '???')
        InlineLogoRenderer.render_text_with_inline_logos(
            canvas,
            pokemon_name,
            x + 31.5 * mm,  # Center of card (63mm / 2)
            y + 82 * mm,    # Name position from bottom
            font_name='Helvetica-Bold',  # Will use FontManager later
            font_size=11,
            text_color='#2D2D2D',
            centered=True
        )
        
        # Render Pokemon image from cache
        if image_cache:
            # Get Pokemon ID for image cache
            pokemon_id = pokemon_data.get('id') or pokemon_data.get('num')
            if pokemon_id:
                try:
                    image_path = image_cache.get_pokemon_image(pokemon_id)
                    if image_path and image_path.exists():
                        # Image area: 63mm × 88mm card, ~50mm × 50mm image area
                        # Centered at x + 31.5mm, positioned at y + 30mm
                        image_width = 50 * mm
                        image_height = 50 * mm
                        image_x = x + (63 * mm - image_width) / 2  # Center horizontally
                        image_y = y + 30 * mm  # Position from bottom
                        
                        canvas.drawImage(
                            str(image_path),
                            image_x,
                            image_y,
                            width=image_width,
                            height=image_height,
                            preserveAspectRatio=True,
                            mask='auto'
                        )
                except Exception as e:
                    logger.warning(f"Failed to render Pokemon image for {pokemon_id}: {e}")
        
        return success
    
    @staticmethod
    def _darken_color(hex_color: str, factor: float = 0.6) -> str:
        """Darken hex color."""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"
    
    @staticmethod
    def _format_id(pokemon_data: dict) -> str:
        """Format Pokemon ID for display."""
        poke_num = pokemon_data.get('section_index') or pokemon_data.get('id') or pokemon_data.get('num', '???')
        if isinstance(poke_num, int):
            return f"#{poke_num:03d}"
        elif not str(poke_num).startswith('#'):
            return f"#{poke_num}"
        return str(poke_num)
