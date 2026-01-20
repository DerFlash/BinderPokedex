"""
Cover Template - Reusable cover page rendering for both Generation and Variant PDFs

Provides parametrized templates for drawing cover pages with:
- Colored header stripe
- Title and subtitle
- Featured Pokémon
- Multi-language support
"""

from datetime import datetime
from pathlib import Path
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor

from .fonts import FontManager
from .constants import PAGE_WIDTH, PAGE_HEIGHT

import logging

logger = logging.getLogger(__name__)


class CoverTemplate:
    """Template for rendering cover pages."""
    
    def __init__(self, language: str = 'en', format_translation=None, image_cache=None):
        """
        Initialize cover template.
        
        Args:
            language: Language code for text rendering
            format_translation: Optional function to format translated text
            image_cache: Optional image cache for featured Pokémon
        """
        self.language = language
        self.format_translation = format_translation
        self.image_cache = image_cache
    
    def draw_generation_cover(self, canvas_obj, generation: int, pokemon_list: list,
                             color: str, generation_info: dict, generation_colors: dict):
        """
        Draw a generation cover page.
        
        Args:
            canvas_obj: ReportLab canvas object
            generation: Generation number (1-9)
            pokemon_list: List of Pokémon in this generation
            color: Color hex for header stripe
            generation_info: Generation metadata (region, range, iconic_pokemon)
            generation_colors: Dict mapping generation to color
        """
        self._draw_cover_base(canvas_obj, color)
        
        # Header content
        canvas_obj.setFont("Helvetica-Bold", 42)
        canvas_obj.setFillColor(HexColor("#FFFFFF"))
        title_y = PAGE_HEIGHT - 30 * mm
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, title_y, "Binder Pokédex")
        
        # Decorative underline
        canvas_obj.setStrokeColor(HexColor("#FFFFFF"))
        canvas_obj.setLineWidth(1.5)
        canvas_obj.line(40 * mm, title_y - 8, PAGE_WIDTH - 40 * mm, title_y - 8)
        
        # Generation text with translation support
        if self.format_translation:
            gen_text = self.format_translation('generation_num', gen=generation)
            if not gen_text or gen_text == 'generation_num':
                gen_text = f"Generation {generation}"
        else:
            gen_text = f"Generation {generation}"
        
        try:
            gen_font_name = FontManager.get_font_name(self.language, bold=False)
            canvas_obj.setFont(gen_font_name, 14)
        except:
            canvas_obj.setFont("Helvetica", 14)
        
        canvas_obj.setFillColor(HexColor("#FFFFFF"))
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 55 * mm, gen_text)
        
        # Region name
        region_name = generation_info.get('region', f'Generation {generation}')
        canvas_obj.setFont("Helvetica-Bold", 18)
        canvas_obj.setFillColor(HexColor("#FFFFFF"))
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 65 * mm, region_name)
        
        # Content section: ID range
        start_id, end_id = generation_info.get('range', (1, 151))
        if self.format_translation:
            id_range_text = self.format_translation('pokedex_range', start=f"#{start_id:03d}", end=f"#{end_id:03d}")
            if not id_range_text or id_range_text == 'pokedex_range':
                id_range_text = f"Pokédex #{start_id:03d} – #{end_id:03d}"
        else:
            id_range_text = f"Pokédex #{start_id:03d} – #{end_id:03d}"
        
        try:
            id_font_name = FontManager.get_font_name(self.language, bold=False)
            canvas_obj.setFont(id_font_name, 16)
        except:
            canvas_obj.setFont("Helvetica", 16)
        
        canvas_obj.setFillColor(HexColor("#333333"))
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, 120 * mm, id_range_text)
        
        # Pokémon count
        if self.format_translation:
            pokemon_text = self.format_translation('pokemon_count_text', count=len(pokemon_list))
            if not pokemon_text or pokemon_text == 'pokemon_count_text':
                pokemon_text = f"{len(pokemon_list)} Pokémon in this collection"
        else:
            pokemon_text = f"{len(pokemon_list)} Pokémon in this collection"
        
        try:
            count_font_name = FontManager.get_font_name(self.language, bold=False)
            canvas_obj.setFont(count_font_name, 14)
        except:
            canvas_obj.setFont("Helvetica", 14)
        
        canvas_obj.setFillColor(HexColor("#666666"))
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, 110 * mm, pokemon_text)
        
        # Decorative line
        canvas_obj.setStrokeColor(HexColor(color))
        canvas_obj.setLineWidth(1)
        canvas_obj.line(40 * mm, 105 * mm, PAGE_WIDTH - 40 * mm, 105 * mm)
        
        # Featured Pokémon
        iconic_ids = generation_info.get('iconic_pokemon', [])
        self._draw_featured_pokemon(canvas_obj, pokemon_list, iconic_ids)
        
        # Footer
        self._draw_cover_footer(canvas_obj, color)
    
    def draw_variant_cover(self, canvas_obj, variant_data: dict, pokemon_list: list, color: str, pattern: str = None, section_title: str = None, section_id: str = None):
        """
        Draw a variant cover page (similar to generation cover with featured images).
        Also used for separator pages when section_title is provided.
        
        Args:
            canvas_obj: ReportLab canvas object
            variant_data: Variant metadata (variant_type, variant_name, icon, etc.)
            pokemon_list: List of Pokémon for this variant
            color: Color hex for header stripe
            pattern: Optional pattern type for the background
            section_title: If provided, draw as separator page with this section title (e.g., "Pokémon-EX Mega")
            section_id: Section identifier for special logos (e.g., "mega", "primal")
        """
        self._draw_cover_base(canvas_obj, color, pattern)
        
        # Get variant type early for multiple uses
        variant = variant_data.get('variant', '')
        is_gen2_ex = variant == 'ex_gen2'
        
        # Header content
        canvas_obj.setFont("Helvetica-Bold", 42)
        canvas_obj.setFillColor(HexColor("#FFFFFF"))
        title_y = PAGE_HEIGHT - 30 * mm
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, title_y, "Binder Pokédex")
        
        # Decorative underline
        canvas_obj.setStrokeColor(HexColor("#FFFFFF"))
        canvas_obj.setLineWidth(1.5)
        canvas_obj.line(40 * mm, title_y - 8, PAGE_WIDTH - 40 * mm, title_y - 8)
        
        # Subtitle - either section name (for separators) or variant subtitle (for main cover)
        if section_title:
            # Separator mode: use section title as subtitle
            # Check if this section has a special logo (Mega, Primal, etc.)
            if section_id and section_id in ['mega', 'primal', 'tera']:
                # Use logo-enhanced subtitle for special sections: "<M> Pokémon <EX>"
                self._draw_subtitle_with_logos(canvas_obj, PAGE_WIDTH / 2, PAGE_HEIGHT - 55 * mm, section_id, section_title, font_size=14)
            else:
                # Regular subtitle for other sections
                try:
                    subtitle_font_name = FontManager.get_font_name(self.language, bold=False)
                    canvas_obj.setFont(subtitle_font_name, 14)
                except:
                    canvas_obj.setFont("Helvetica", 14)
                
                canvas_obj.setFillColor(HexColor("#FFFFFF"))
                canvas_obj.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 55 * mm, section_title)
        else:
            # Main cover mode: use variant subtitle (or skip if null)
            subtitle_dict = variant_data.get('subtitle', {})
            if subtitle_dict is not None:  # Only draw if subtitle is not None
                if isinstance(subtitle_dict, dict):
                    subtitle_text = subtitle_dict.get(self.language, subtitle_dict.get('en', 'Variant Series'))
                else:
                    subtitle_text = str(subtitle_dict) if subtitle_dict else 'Variant Series'
                
                # Check if this is Gen2 (ex_gen2) or Gen3 (ex_gen3) to render EX logo in subtitle
                if (is_gen2_ex and subtitle_text.startswith('EX-')) or ('[EX_NEW]' in subtitle_text):
                    # Draw with EX logo prefix: "<EX-Logo>-Serie (...)" or "<EX_NEW> Serie (...)"
                    self._draw_subtitle_with_ex_logo(canvas_obj, PAGE_WIDTH / 2, PAGE_HEIGHT - 55 * mm, subtitle_text, font_size=14)
                else:
                    # Regular subtitle
                    try:
                        subtitle_font_name = FontManager.get_font_name(self.language, bold=False)
                        canvas_obj.setFont(subtitle_font_name, 14)
                    except:
                        canvas_obj.setFont("Helvetica", 14)
                    
                    canvas_obj.setFillColor(HexColor("#FFFFFF"))
                    canvas_obj.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 55 * mm, subtitle_text)
        
        # Title (e.g., "Pokemon ex · Gen 1") - where Region would be
        title_dict = variant_data.get('title', {})
        if isinstance(title_dict, dict):
            title_text = title_dict.get(self.language, title_dict.get('en', 'Pokémon EX'))
        else:
            title_text = str(title_dict) if title_dict else 'Pokémon EX'
        
        try:
            title_font_name = FontManager.get_font_name(self.language, bold=True)
            canvas_obj.setFont(title_font_name, 18)
        except:
            canvas_obj.setFont("Helvetica-Bold", 18)
        
        canvas_obj.setFillColor(HexColor("#FFFFFF"))
        
        # Draw regular title (EX logo now in subtitle, not in title)
        canvas_obj.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 65 * mm, title_text)
        
        # Note: "Variants" text is intentionally omitted for EX PDFs
        
        # Content section: stats (omitted for EX variants to keep clean layout)
        
        # Featured Pokémon with images (use iconic_pokemon_ids if available)
        iconic_ids = variant_data.get('iconic_pokemon_ids', [])
        self._draw_featured_pokemon(canvas_obj, pokemon_list, iconic_ids)
        
        # Footer
        self._draw_cover_footer(canvas_obj, color)
    
    def _draw_cover_base(self, canvas_obj, color: str, pattern: str = None):
        """
        Draw base cover background.
        
        Args:
            canvas_obj: ReportLab canvas object
            color: Color hex for the stripe
            pattern: Optional pattern type ('crystalline_abstract_rainbow', 'crystalline_abstract_gold', etc.)
                    If None, draws solid color stripe with subtle overlay
        """
        # White background
        canvas_obj.setFillColor(HexColor("#FFFFFF"))
        canvas_obj.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=True, stroke=False)
        
        # Top colored stripe
        stripe_height = 100 * mm
        canvas_obj.setFillColor(HexColor(color))
        canvas_obj.rect(0, PAGE_HEIGHT - stripe_height, PAGE_WIDTH, stripe_height, fill=True, stroke=False)
        
        # Draw pattern if specified, otherwise use subtle overlay
        self._draw_background_pattern(canvas_obj, color, stripe_height, pattern_type=pattern)
    
    def _draw_background_pattern(self, canvas_obj, color: str, stripe_height: float, pattern_type: str = None):
        """
        Draw decorative pattern on the stripe background.
        
        Args:
            canvas_obj: ReportLab canvas object
            color: Color hex for the stripe base
            stripe_height: Height of the stripe
            pattern_type: Type of crystalline pattern ('crystalline_abstract_rainbow', 'crystalline_abstract_gold', etc.)
        """
        from .crystalline_patterns import CrystallinePatterns
        
        if pattern_type:
            # Use crystalline pattern
            stripe_bottom_y = PAGE_HEIGHT - stripe_height
            CrystallinePatterns.draw_pattern_on_stripe(
                canvas_obj, 0, stripe_bottom_y, PAGE_WIDTH, stripe_height,
                pattern_type=pattern_type,
                primary_color=color
            )
        # else: No pattern - just solid color (already drawn in _draw_cover_base)
    
    def _draw_title_with_ex_logo(self, canvas_obj, x_center, y, title_text, font_size=18):
        """
        Draw title with EX logo replacing "EX" text.
        E.g., "Pokémon EX · Gen 2" becomes "Pokémon [EX-LOGO] · Gen 2"
        
        Args:
            canvas_obj: ReportLab canvas
            x_center: X coordinate of text center
            y: Y coordinate of text
            title_text: Full title text including "EX"
            font_size: Font size to use (default 18pt)
        """
        # Replace "EX" with placeholder token to calculate layout
        logo_placeholder = "[EX]"
        display_text = title_text.replace("EX", logo_placeholder)
        
        # Measure text width to position logo correctly
        try:
            title_font_name = FontManager.get_font_name(self.language, bold=True)
            canvas_obj.setFont(title_font_name, font_size)
        except:
            canvas_obj.setFont("Helvetica-Bold", font_size)
        
        full_width = canvas_obj.stringWidth(display_text, canvas_obj._fontname, font_size)
        
        # Logo dimensions (proportional to 18pt font)
        logo_width = 10 * mm
        logo_height = 12 * mm
        
        # Calculate starting position for left-aligned text
        start_x = x_center - full_width / 2
        
        # Draw text parts around logo
        parts = display_text.split(logo_placeholder)
        current_x = start_x
        
        canvas_obj.setFillColor(HexColor("#FFFFFF"))
        
        # Part before logo
        if parts[0]:
            canvas_obj.drawString(current_x, y, parts[0])
            current_x += canvas_obj.stringWidth(parts[0], canvas_obj._fontname, font_size)
        
        # Draw EX logo from image file
        import os
        from PIL import Image
        
        logo_file = os.path.join(
            os.path.dirname(__file__),
            "../../data/variants/EXLogoBig.png"
        )
        
        logo_x = current_x
        logo_width = 11.05 * mm
        logo_height = 14.45 * mm
        
        # Center logo vertically with text, then shift upward
        logo_y = y - (logo_height / 2) + 2 * mm  # Center plus 2mm upward offset
        
        if os.path.exists(logo_file):
            canvas_obj.drawImage(
                logo_file,
                logo_x,
                logo_y,
                width=logo_width,
                height=logo_height,
                preserveAspectRatio=True,
                mask='auto'
            )
            current_x += logo_width + 0.5 * mm
        else:
            # Fallback: draw simple EX if logo file missing
            canvas_obj.setFillColor(HexColor("#FFD700"))
            canvas_obj.rect(logo_x, logo_y, 11*mm, 14*mm, fill=True, stroke=False)
            canvas_obj.setFont("Helvetica-Bold", 11)
            canvas_obj.setFillColor(HexColor("#FFFFFF"))
            canvas_obj.drawCentredString(logo_x + 5.5*mm, logo_y + 7*mm, "EX")
            current_x += 11 * mm + 0.5 * mm
        
        # Part after logo
        try:
            title_font_name = FontManager.get_font_name(self.language, bold=True)
            canvas_obj.setFont(title_font_name, font_size)
        except:
            canvas_obj.setFont("Helvetica-Bold", font_size)
        
        canvas_obj.setFillColor(HexColor("#FFFFFF"))
        
        if len(parts) > 1 and parts[1]:
            canvas_obj.drawString(current_x, y, parts[1])
    
    def _draw_subtitle_with_ex_logo(self, canvas_obj, x_center, y, subtitle_text, font_size=14):
        """
        Draw subtitle with EX logo prefix for Gen2/Gen3 covers.
        E.g., "EX-Serie (Next Destinies+)" becomes "[EX-LOGO]-Serie (Next Destinies+)"
        E.g., "[EX_NEW] Serie (Karmesin & Purpur+)" becomes "[EX_NEW_LOGO] Serie (...)"
        
        Args:
            canvas_obj: ReportLab canvas
            x_center: X coordinate of text center
            y: Y coordinate of text
            subtitle_text: Subtitle text (must start with "EX-" or contain "[EX_NEW]")
            font_size: Font size to use
        """
        import os
        
        # Check for EX_NEW token (Gen3)
        if '[EX_NEW]' in subtitle_text:
            ex_logo_file = os.path.join(
                os.path.dirname(__file__),
                "../../data/variants/EXLogoNew.png"
            )
            remaining_text = subtitle_text.replace('[EX_NEW] ', '')
            use_new_logo = True
        elif subtitle_text.startswith('EX-'):
            ex_logo_file = os.path.join(
                os.path.dirname(__file__),
                "../../data/variants/EXLogoBig.png"
            )
            remaining_text = subtitle_text[3:]  # Remove "EX-"
            use_new_logo = False
        else:
            # Fallback to plain text
            try:
                subtitle_font_name = FontManager.get_font_name(self.language, bold=False)
                canvas_obj.setFont(subtitle_font_name, font_size)
            except:
                canvas_obj.setFont("Helvetica", font_size)
            canvas_obj.setFillColor(HexColor("#FFFFFF"))
            canvas_obj.drawCentredString(x_center, y, subtitle_text)
            return
        
        if not os.path.exists(ex_logo_file):
            # Fallback to plain text
            try:
                subtitle_font_name = FontManager.get_font_name(self.language, bold=False)
                canvas_obj.setFont(subtitle_font_name, font_size)
            except:
                canvas_obj.setFont("Helvetica", font_size)
            canvas_obj.setFillColor(HexColor("#FFFFFF"))
            canvas_obj.drawCentredString(x_center, y, subtitle_text)
            return
        
        # Measure dimensions
        try:
            subtitle_font_name = FontManager.get_font_name(self.language, bold=False)
            canvas_obj.setFont(subtitle_font_name, font_size)
        except:
            canvas_obj.setFont("Helvetica", font_size)
        
        text_width = canvas_obj.stringWidth(remaining_text, canvas_obj._fontname, font_size)
        logo_width = 8.8 * mm
        logo_height = 11 * mm
        gap = 1 * mm
        
        total_width = logo_width + gap + text_width
        start_x = x_center - total_width / 2
        
        # Draw logo
        logo_x = start_x
        logo_y = y - (logo_height / 2) + 1.5 * mm
        
        canvas_obj.drawImage(
            ex_logo_file,
            logo_x,
            logo_y,
            width=logo_width,
            height=logo_height,
            preserveAspectRatio=True,
            mask='auto'
        )
        
        # Draw text
        text_x = logo_x + logo_width + gap
        canvas_obj.setFillColor(HexColor("#FFFFFF"))
        canvas_obj.drawString(text_x, y, remaining_text)
        canvas_obj.drawString(text_x, y, remaining_text)
    
    def _draw_subtitle_with_logos(self, canvas_obj, x_center, y, section_id, section_title, font_size=14):
        """
        Draw subtitle with token-based logos for special sections.
        Supports tokens like [M] for Mega logo and [EX] for EX logo.
        E.g., "[M] Pokémon [EX] Serie" becomes "[M-LOGO] Pokémon [EX-LOGO] Serie"
        
        Args:
            canvas_obj: ReportLab canvas
            x_center: X coordinate of text center
            y: Y coordinate of text
            section_id: Section identifier ('mega', 'primal', 'tera', etc.)
            section_title: Section title text with potential tokens
            font_size: Font size to use
        """
        import os
        
        # Check if section_title contains tokens
        if '[M]' not in section_title and '[EX]' not in section_title and '[EX_NEW]' not in section_title and '[EX_TERA]' not in section_title:
            # No special rendering needed, use plain text
            try:
                subtitle_font_name = FontManager.get_font_name(self.language, bold=False)
                canvas_obj.setFont(subtitle_font_name, font_size)
            except:
                canvas_obj.setFont("Helvetica", font_size)
            canvas_obj.setFillColor(HexColor("#FFFFFF"))
            canvas_obj.drawCentredString(x_center, y, section_title)
            return
        
        # Get logo files
        m_logo_file = os.path.join(
            os.path.dirname(__file__),
            "../../data/variants/M_Pokémon.png"
        )
        ex_logo_file = os.path.join(
            os.path.dirname(__file__),
            "../../data/variants/EXLogoBig.png"
        )
        ex_new_logo_file = os.path.join(
            os.path.dirname(__file__),
            "../../data/variants/EXLogoNew.png"
        )
        ex_tera_logo_file = os.path.join(
            os.path.dirname(__file__),
            "../../data/variants/EXTeraLogo.png"
        )
        
        if not os.path.exists(m_logo_file) or not os.path.exists(ex_logo_file):
            # Fallback to plain text
            try:
                subtitle_font_name = FontManager.get_font_name(self.language, bold=False)
                canvas_obj.setFont(subtitle_font_name, font_size)
            except:
                canvas_obj.setFont("Helvetica", font_size)
            canvas_obj.setFillColor(HexColor("#FFFFFF"))
            canvas_obj.drawCentredString(x_center, y, section_title)
            return
        
        # Parse section_title for tokens and text segments
        # E.g., "[M] Pokémon [EX] Serie" -> segments: [("[M]", logo), ("Pokémon ", text), ("[EX]", logo), ("Serie", text)]
        try:
            subtitle_font_name = FontManager.get_font_name(self.language, bold=False)
            canvas_obj.setFont(subtitle_font_name, font_size)
        except:
            canvas_obj.setFont("Helvetica", font_size)
        
        # Calculate total width
        total_width = 0
        segments = []
        remaining_title = section_title
        
        m_logo_width = 6.65 * mm
        m_logo_height = 5.3 * mm
        ex_logo_width = 7.3 * mm
        ex_logo_height = 8.8 * mm
        ex_new_logo_width = 7.3 * mm
        ex_new_logo_height = 8.8 * mm
        ex_tera_logo_width = 7.3 * mm
        ex_tera_logo_height = 8.8 * mm
        gap = 1.5 * mm
        
        # Parse tokens (check longest tokens first: [EX_TERA], [EX_NEW], then shorter ones)
        while remaining_title:
            if remaining_title.startswith('[EX_TERA]'):
                segments.append(('logo', 'ex_tera'))
                total_width += ex_tera_logo_width + gap
                remaining_title = remaining_title[9:].lstrip()
            elif remaining_title.startswith('[EX_NEW]'):
                segments.append(('logo', 'ex_new'))
                total_width += ex_new_logo_width + gap
                remaining_title = remaining_title[8:].lstrip()
            elif remaining_title.startswith('[M]'):
                segments.append(('logo', 'm'))
                total_width += m_logo_width + gap
                remaining_title = remaining_title[3:].lstrip()
            elif remaining_title.startswith('[EX]'):
                segments.append(('logo', 'ex'))
                total_width += ex_logo_width + gap
                remaining_title = remaining_title[4:].lstrip()
            else:
                # Find next token or end of string
                m_idx = remaining_title.find('[M]')
                ex_idx = remaining_title.find('[EX]')
                ex_new_idx = remaining_title.find('[EX_NEW]')
                ex_tera_idx = remaining_title.find('[EX_TERA]')
                next_idx = len(remaining_title)
                
                if m_idx >= 0:
                    next_idx = min(next_idx, m_idx)
                if ex_idx >= 0:
                    next_idx = min(next_idx, ex_idx)
                if ex_new_idx >= 0:
                    next_idx = min(next_idx, ex_new_idx)
                if ex_tera_idx >= 0:
                    next_idx = min(next_idx, ex_tera_idx)
                
                text_segment = remaining_title[:next_idx].rstrip()
                if text_segment:
                    segments.append(('text', text_segment))
                    text_width = canvas_obj.stringWidth(text_segment + ' ', canvas_obj._fontname, font_size)
                    total_width += text_width
                
                remaining_title = remaining_title[next_idx:]
        
        # Draw with calculated positions
        start_x = x_center - total_width / 2
        current_x = start_x
        
        canvas_obj.setFillColor(HexColor("#FFFFFF"))
        
        for seg_type, seg_value in segments:
            if seg_type == 'text':
                canvas_obj.drawString(current_x, y, seg_value + ' ')
                current_x += canvas_obj.stringWidth(seg_value + ' ', canvas_obj._fontname, font_size)
            elif seg_type == 'logo':
                if seg_value == 'm':
                    logo_file = m_logo_file
                    logo_width = m_logo_width
                    logo_height = m_logo_height
                    logo_y = y - (logo_height / 2) + 1.2 * mm
                elif seg_value == 'ex':
                    logo_file = ex_logo_file
                    logo_width = ex_logo_width
                    logo_height = ex_logo_height
                    logo_y = y - (logo_height / 2) + 1.5 * mm
                elif seg_value == 'ex_new':
                    logo_file = ex_new_logo_file
                    logo_width = ex_new_logo_width
                    logo_height = ex_new_logo_height
                    logo_y = y - (logo_height / 2) + 1.5 * mm
                elif seg_value == 'ex_tera':
                    logo_file = ex_tera_logo_file
                    logo_width = ex_tera_logo_width
                    logo_height = ex_tera_logo_height
                    logo_y = y - (logo_height / 2) + 1.5 * mm
                
                canvas_obj.drawImage(
                    logo_file,
                    current_x,
                    logo_y,
                    width=logo_width,
                    height=logo_height,
                    preserveAspectRatio=True,
                    mask='auto'
                )
                current_x += logo_width + gap
    
    def _draw_featured_pokemon(self, canvas_obj, pokemon_list: list, iconic_ids: list):
        """Draw featured Pokémon at bottom of cover. If iconic_ids is empty, draw nothing."""
        if not pokemon_list or not iconic_ids:
            # Don't draw featured pokemon if iconic_ids is not provided
            return
        
        # OPTIMIZATION: Skip featured pokemon if image_cache not available
        # (avoids expensive HTTP requests during PDF generation)
        if not self.image_cache:
            return
        
        # Use provided iconic_ids (max 3)
        featured_ids = iconic_ids[:3]
        
        # Create lookup maps: both by integer ID and by full ID string
        # (for variants like "#006_MEGA_X")
        pokemon_by_int_id = {}
        pokemon_by_str_id = {}
        for p in pokemon_list:
            poke_id = p.get('id', p.get('num', '0'))
            
            # Map by full ID string (e.g., "#006_MEGA_X")
            pokemon_by_str_id[poke_id] = p
            
            # Map by integer ID (e.g., 6)
            if isinstance(poke_id, str):
                # Extract base integer from ID
                int_id = int(poke_id.lstrip('#').split('_')[0])
            else:
                int_id = int(poke_id)
            pokemon_by_int_id[int_id] = p
        
        pokemon_count = min(len(featured_ids), 3)
        if pokemon_count == 0:
            return
        
        total_width = PAGE_WIDTH - (30 * mm)
        spacing_per_pokemon = total_width / pokemon_count
        
        for idx, poke_id in enumerate(featured_ids[:3]):
            # Try to find pokemon first by full ID (for variants), then by integer ID
            pokemon = None
            
            # First try exact match (for variants like "#006_MEGA_X")
            if isinstance(poke_id, str) and poke_id in pokemon_by_str_id:
                pokemon = pokemon_by_str_id[poke_id]
            
            # Fall back to integer lookup if exact match not found
            if not pokemon:
                if isinstance(poke_id, str):
                    lookup_id = int(poke_id.lstrip('#').split('_')[0])
                else:
                    lookup_id = int(poke_id) if poke_id else 0
                pokemon = pokemon_by_int_id.get(lookup_id)
            
            if not pokemon:
                continue
            
            x_center = 15 * mm + spacing_per_pokemon * (idx + 0.5)
            card_width = 65 * mm
            card_height = 90 * mm
            x = x_center - card_width / 2
            y = 10 * mm
            
            image_source = pokemon.get('image_path') or pokemon.get('image_url')
            if image_source and self.image_cache:
                try:
                    image_to_render = None
                    # Use mega_form_id if available (PokeAPI), otherwise pokemon_form_cache_id (Pokemon.com)
                    img_lookup_id = pokemon.get('mega_form_id') or pokemon.get('pokemon_form_cache_id')
                    if not img_lookup_id:
                        img_lookup_id = pokemon.get('id', pokemon.get('num', 0))
                        if isinstance(img_lookup_id, str):
                            img_lookup_id = int(img_lookup_id.lstrip('#').split('_')[0])
                        else:
                            img_lookup_id = int(img_lookup_id)
                    else:
                        img_lookup_id = int(img_lookup_id) if img_lookup_id else 0
                    
                    if image_source.startswith('http://') or image_source.startswith('https://'):
                        image_to_render = self.image_cache.get_image(img_lookup_id, url=image_source, timeout=3)
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
                    logger.debug(f"Could not load featured image {lookup_id}: {e}")
    
    def _draw_cover_footer(self, canvas_obj, color: str):
        """Draw footer on cover page."""
        try:
            font_name = FontManager.get_font_name(self.language, bold=False)
            canvas_obj.setFont(font_name, 6)
        except:
            canvas_obj.setFont("Helvetica", 6)
        
        canvas_obj.setFillColor(HexColor("#CCCCCC"))
        
        # Build footer text
        footer_parts = []
        
        if self.format_translation:
            footer_parts.append(self.format_translation('cover_print_borderless'))
            footer_parts.append(self.format_translation('cover_follow_cutting'))
        else:
            footer_parts.append("Print borderless")
            footer_parts.append("Follow cutting lines")
        
        footer_parts.append("Binder Pokédex Project")
        footer_parts.append(datetime.now().strftime('%Y-%m-%d'))
        
        footer_text = " • ".join(footer_parts)
        text_width = canvas_obj.stringWidth(footer_text, canvas_obj._fontname, 6) if hasattr(canvas_obj, '_fontname') else len(footer_text) * 2
        x_pos = (PAGE_WIDTH - text_width) / 2
        canvas_obj.drawString(x_pos, 2.5 * mm, footer_text)
