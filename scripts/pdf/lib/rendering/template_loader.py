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
from PIL import Image

try:
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPDF
    SVG_AVAILABLE = True
except ImportError:
    svg2rlg = None
    renderPDF = None
    SVG_AVAILABLE = False
    logging.warning("svglib not available - template rendering disabled")

from .inline_logo_renderer import InlineLogoRenderer

logger = logging.getLogger(__name__)


class TemplateLoader:
    """Loads and processes SVG templates."""
    
    # Template base directory - from scripts/pdf/lib/rendering/ → project root
    # template_loader.py is at: project_root/scripts/pdf/lib/rendering/
    # So we need 4 levels up: rendering → lib → pdf → scripts → project_root
    TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / 'config' / 'templates'
    
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
        if not SVG_AVAILABLE or not svg2rlg:
            logger.error("svglib not available")
            return False
        
        try:
            # SVG string → Drawing object
            svg_io = BytesIO(svg_content.encode('utf-8'))
            drawing = svg2rlg(svg_io)
            
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
        # Template should define anchor point for name (e.g., at 31.5mm, 20mm from top)
        # SVG bottom info section at y=15-25mm from top
        # ReportLab: y from bottom = 88mm - 20mm = 68mm
        pokemon_name = pokemon_data.get('name', '???')
        
        # Handle multi-language name format (dict) vs simple string
        if isinstance(pokemon_name, dict):
            pokemon_name = pokemon_name.get(language, pokemon_name.get('en', '???'))
        
        InlineLogoRenderer.render_text_with_inline_logos(
            canvas,
            pokemon_name,
            x + 31.5 * mm,  # Center of card (63mm / 2)
            y + (88 * mm - 20 * mm),  # Name at 20mm from top = 68mm from bottom
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
                    # ImageCache.get_image returns ImageReader, not Path
                    # We need to use it directly or get the image from data
                    image_url = pokemon_data.get('image_url')
                    image_reader = image_cache.get_image(pokemon_id, image_url, size='card')
                    
                    if image_reader:
                        # Image area: 63mm × 88mm card, 50mm × 50mm image area
                        # SVG rect at y=30mm from top, height=50mm (30-80mm from top)
                        # ReportLab: y from bottom = 88mm - (30mm + 50mm) = 8mm
                        image_width = 50 * mm
                        image_height = 50 * mm
                        image_x = x + (63 * mm - image_width) / 2  # Center horizontally
                        image_y = y + (88 * mm - 80 * mm)  # 8mm from bottom (SVG y=30mm + height=50mm from top)
                        
                        # For better transparency support, extract PIL image and alpha channel
                        try:
                            # Get PIL image from ImageReader
                            pil_image = image_reader._image if hasattr(image_reader, '_image') else Image.open(image_reader.fp)
                            
                            # Check if image has alpha channel
                            if pil_image.mode in ('RGBA', 'LA') or (pil_image.mode == 'P' and 'transparency' in pil_image.info):
                                # Convert to RGBA if needed
                                if pil_image.mode != 'RGBA':
                                    pil_image = pil_image.convert('RGBA')
                                
                                # Draw with explicit alpha mask
                                canvas.drawImage(
                                    image_reader,
                                    image_x,
                                    image_y,
                                    width=image_width,
                                    height=image_height,
                                    preserveAspectRatio=True,
                                    mask='auto'
                                )
                            else:
                                # No transparency, draw normally
                                canvas.drawImage(
                                    image_reader,
                                    image_x,
                                    image_y,
                                    width=image_width,
                                    height=image_height,
                                    preserveAspectRatio=True
                                )
                        except:
                            # Fallback: draw without special transparency handling
                            canvas.drawImage(
                                image_reader,
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
