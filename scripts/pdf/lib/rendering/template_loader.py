"""
Template Loader - SVG Template System

Loads and processes SVG templates for card rendering.
Handles variable substitution, XML manipulation, and coordinates rendering pipeline.
"""

import logging
import re
import xml.etree.ElementTree as ET
import base64
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
    def manipulate_svg_xml(svg_content: str, replacements: Dict[str, any]) -> str:
        """
        Manipulate SVG content via XML DOM (WYSIWYG approach).
        
        Finds elements by ID and replaces their content/attributes directly.
        This preserves the SVG coordinate system (no Y-axis conversion needed).
        
        Args:
            svg_content: SVG content with elements having id attributes
            replacements: Dict of {element_id: content/dict}
                For text elements: element_id -> string (replaces text content)
                For image elements: element_id -> {'href': data_uri} or {'href': data_uri, 'x': x, 'y': y, ...}
                For other attributes: element_id -> {'attr_name': 'value'}
        
        Returns:
            Modified SVG content as string
        
        Example:
            replacements = {
                'pokemon_name': 'Bulbasaur',
                'pokemon_image': {'href': 'data:image/png;base64,...'},
                'section_title': 'Generation II'
            }
        """
        try:
            # Register SVG namespace to preserve namespace prefixes
            ET.register_namespace('', 'http://www.w3.org/2000/svg')
            
            # Parse SVG as XML
            root = ET.fromstring(svg_content.encode('utf-8'))
            
            # Namespaces for XPath queries
            ns = {'svg': 'http://www.w3.org/2000/svg'}
            
            # Process each replacement
            for element_id, content in replacements.items():
                # Find element by ID (search in both default namespace and without namespace)
                element = root.find(f".//*[@id='{element_id}']", ns)
                if element is None:
                    # Try without namespace
                    element = root.find(f".//*[@id='{element_id}']")
                
                if element is None:
                    logger.warning(f"Element with id='{element_id}' not found in SVG")
                    continue
                
                # Handle different element types
                if isinstance(content, dict):
                    # Dictionary: set attributes
                    for attr_name, attr_value in content.items():
                        if attr_name == 'href':
                            # Special handling for href (use xlink:href or href)
                            # SVG 2.0 uses href, older uses xlink:href
                            element.set('{http://www.w3.org/1999/xlink}href', str(attr_value))
                            element.set('href', str(attr_value))
                        else:
                            element.set(attr_name, str(attr_value))
                elif isinstance(content, str):
                    # String: replace text content
                    element.text = content
                else:
                    # Other types: convert to string and set as text
                    element.text = str(content)
            
            # Convert back to string
            return ET.tostring(root, encoding='unicode', method='xml')
        
        except Exception as e:
            logger.error(f"Failed to manipulate SVG XML: {e}", exc_info=True)
            return svg_content  # Return original on error
    
    @staticmethod
    def image_to_data_uri(image_path: Path, format: str = 'PNG') -> str:
        """
        Convert image file to data URI for embedding in SVG.
        
        Args:
            image_path: Path to image file
            format: Image format (PNG, JPEG, etc.)
        
        Returns:
            Data URI string (data:image/png;base64,...)
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB/RGBA as needed
                if format.upper() == 'PNG' and img.mode not in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGBA')
                elif format.upper() in ('JPEG', 'JPG') and img.mode == 'RGBA':
                    # JPEG doesn't support alpha, convert to RGB
                    bg = Image.new('RGB', img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
                    img = bg
                
                # Save to bytes
                buffer = BytesIO()
                img.save(buffer, format=format)
                encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                # Create data URI
                mime_type = f"image/{format.lower()}"
                return f"data:{mime_type};base64,{encoded}"
        
        except Exception as e:
            logger.error(f"Failed to convert image to data URI: {e}")
            return ""
    
    @staticmethod
    def pil_image_to_data_uri(pil_image: Image.Image, format: str = 'PNG') -> str:
        """
        Convert PIL Image to data URI for embedding in SVG.
        
        Args:
            pil_image: PIL Image object
            format: Image format (PNG, JPEG, etc.)
        
        Returns:
            Data URI string (data:image/png;base64,...)
        """
        try:
            # Convert to appropriate mode
            if format.upper() == 'PNG' and pil_image.mode not in ('RGBA', 'LA', 'P'):
                pil_image = pil_image.convert('RGBA')
            elif format.upper() in ('JPEG', 'JPG') and pil_image.mode == 'RGBA':
                # JPEG doesn't support alpha, convert to RGB
                bg = Image.new('RGB', pil_image.size, (255, 255, 255))
                bg.paste(pil_image, mask=pil_image.split()[3] if len(pil_image.split()) == 4 else None)
                pil_image = bg
            
            # Save to bytes
            buffer = BytesIO()
            pil_image.save(buffer, format=format)
            encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Create data URI
            mime_type = f"image/{format.lower()}"
            return f"data:{mime_type};base64,{encoded}"
        
        except Exception as e:
            logger.error(f"Failed to convert PIL image to data URI: {e}")
            return ""
    
    @staticmethod
    def extract_placeholder_positions(svg_content: str) -> Dict[str, Dict[str, float]]:
        """
        Extract positions from placeholder elements in SVG.
        
        Args:
            svg_content: SVG content with id="placeholder_name" elements
        
        Returns:
            Dict of {placeholder_name: {'x': value, 'y': value}}
        """
        import re
        from reportlab.lib.units import mm
        
        positions = {}
        
        # Find text/rect elements with id attributes: <text id="name" x="105" y="242" ...>
        pattern = r'<(?:text|rect)\s+id="([^"]+)"[^>]*\s+x="([^"]+)"[^>]*\s+y="([^"]+)"'
        
        for match in re.finditer(pattern, svg_content):
            element_id = match.group(1)
            x_str = match.group(2)
            y_str = match.group(3)
            
            try:
                # SVG coordinates are in mm, convert to points
                x = float(x_str) * mm
                # SVG y is from top, ReportLab y is from bottom
                # A4 height = 297mm
                y = (297 - float(y_str)) * mm
                
                positions[element_id] = {'x': x, 'y': y}
            except ValueError:
                continue
        
        # Find line elements with id attributes: <line id="name" x1="40" y1="152" ...>
        line_pattern = r'<line\s+id="([^"]+)"[^>]*\s+x1="([^"]+)"[^>]*\s+y1="([^"]+)"[^>]*\s+x2="([^"]+)"[^>]*\s+y2="([^"]+)"'
        
        for match in re.finditer(line_pattern, svg_content):
            element_id = match.group(1)
            x1_str = match.group(2)
            y1_str = match.group(3)
            x2_str = match.group(4)
            y2_str = match.group(5)
            
            try:
                # Store line coordinates
                x1 = float(x1_str) * mm
                y1 = (297 - float(y1_str)) * mm
                x2 = float(x2_str) * mm
                y2 = (297 - float(y2_str)) * mm
                
                positions[element_id] = {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}
            except ValueError:
                continue
        
        return positions
    
    @staticmethod
    def remove_placeholders(svg_content: str) -> str:
        """
        Remove placeholder elements from SVG before rendering.
        
        Args:
            svg_content: SVG content with placeholder elements
        
        Returns:
            SVG content without placeholder elements
        """
        import re
        
        # Remove placeholder elements (text, rect, line with IDs)
        # Match opening tag and content until closing tag
        svg_content = re.sub(r'<text\s+id="[^"]+\"[^>]*>.*?</text>', '', svg_content)
        svg_content = re.sub(r'<rect\s+id="[^"]+\"[^>]*/>', '', svg_content)
        svg_content = re.sub(r'<line\s+id="[^"]+\"[^>]*/>', '', svg_content)
        
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
        Render card at position using XML manipulation (WYSIWYG approach).
        
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
        from ..constants import TYPE_COLORS
        
        # Get type and color
        types = pokemon_data.get('types', [])
        if not types and pokemon_data.get('type1'):
            types = [pokemon_data.get('type1')]
        if not types:
            types = ['Normal']
        
        pokemon_type = types[0]
        type_color = TYPE_COLORS.get(pokemon_type, TYPE_COLORS['Normal'])
        
        # Prepare variables (basic ones for {{variable}} substitution)
        variables = {
            'type': pokemon_type,  # Will be translated later
            'type_color': type_color,
            'type_color_dark': self._darken_color(type_color),
            'id': self._format_id(pokemon_data),
        }
        
        # Substitute variables in SVG (for colors, type text, etc.)
        svg_content = TemplateLoader.substitute_variables(
            self.template_content,
            variables
        )
        
        # Prepare Pokemon name
        pokemon_name = pokemon_data.get('name', '???')
        
        # Handle multi-language name format (dict) vs simple string
        if isinstance(pokemon_name, dict):
            pokemon_name = pokemon_name.get(language, pokemon_name.get('en', '???'))
        
        # Check if name contains inline logo tokens
        has_inline_logos = '[' in pokemon_name and ']' in pokemon_name
        
        # For names without inline logos, we can put them in SVG directly
        # For names with inline logos, we'll render them with Python overlay after SVG
        if not has_inline_logos:
            # Get Pokemon image as data URI if available
            image_data_uri = None
            if image_cache:
                pokemon_id = pokemon_data.get('id') or pokemon_data.get('num')
                if pokemon_id:
                    try:
                        image_url = pokemon_data.get('image_url')
                        image_reader = image_cache.get_image(pokemon_id, image_url, size='card')
                        
                        if image_reader:
                            # Get PIL image from ImageReader
                            pil_image = image_reader._image if hasattr(image_reader, '_image') else Image.open(image_reader.fp)
                            # Convert to data URI for embedding in SVG
                            image_data_uri = TemplateLoader.pil_image_to_data_uri(pil_image, format='PNG')
                    except Exception as e:
                        logger.warning(f"Failed to load Pokemon image for {pokemon_id}: {e}")
            
            # Manipulate SVG XML to replace placeholder content
            replacements = {
                'pokemon_name': pokemon_name,
            }
            
            # Only add image if we have one (otherwise keeps dummy placeholder)
            if image_data_uri:
                replacements['pokemon_image'] = {'href': image_data_uri}
            
            svg_content = TemplateLoader.manipulate_svg_xml(svg_content, replacements)
            
            # Render complete SVG to canvas
            success = TemplateLoader.render_svg_to_canvas(svg_content, canvas, x, y)
        else:
            # Name has inline logos - need Python overlay
            # First, render SVG without name (remove name element)
            replacements = {
                'pokemon_name': '',  # Empty text = invisible
            }
            
            # Get image if available
            image_data_uri = None
            if image_cache:
                pokemon_id = pokemon_data.get('id') or pokemon_data.get('num')
                if pokemon_id:
                    try:
                        image_url = pokemon_data.get('image_url')
                        image_reader = image_cache.get_image(pokemon_id, image_url, size='card')
                        
                        if image_reader:
                            pil_image = image_reader._image if hasattr(image_reader, '_image') else Image.open(image_reader.fp)
                            image_data_uri = TemplateLoader.pil_image_to_data_uri(pil_image, format='PNG')
                    except Exception as e:
                        logger.warning(f"Failed to load Pokemon image for {pokemon_id}: {e}")
            
            if image_data_uri:
                replacements['pokemon_image'] = {'href': image_data_uri}
            
            svg_content = TemplateLoader.manipulate_svg_xml(svg_content, replacements)
            
            # Render SVG structure
            success = TemplateLoader.render_svg_to_canvas(svg_content, canvas, x, y)
            
            # Overlay name with inline logos using Python
            # SVG coordinate: x=31.5mm (center), y=20mm (from top)
            # ReportLab: y = 88mm - 20mm = 68mm (from bottom)
            InlineLogoRenderer.render_text_with_inline_logos(
                canvas,
                pokemon_name,
                x + 31.5 * mm,  # Center of card
                y + 68 * mm,     # 20mm from top in SVG = 68mm from bottom in ReportLab
                font_name='Helvetica-Bold',
                font_size=11,
                text_color='#2D2D2D',
                centered=True
            )
        
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
