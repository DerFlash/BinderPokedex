#!/usr/bin/env python3
"""
Generate PDF with 3x3 Pokemon card layout for binder pages
Alle Generationen mit Deckblättern zur sauberen Trennung
"""

import json
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
import subprocess
import sys
import tempfile
import shutil
from datetime import datetime
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import io


TYPE_NAMES_DE = {
    'Normal': 'Normal', 'Fire': 'Feuer', 'Water': 'Wasser', 'Electric': 'Elektro',
    'Grass': 'Pflanze', 'Ice': 'Eis', 'Fighting': 'Kampf', 'Poison': 'Gift',
    'Ground': 'Boden', 'Flying': 'Flug', 'Psychic': 'Psycho', 'Bug': 'Käfer',
    'Rock': 'Stein', 'Ghost': 'Spuk', 'Dragon': 'Drachen', 'Dark': 'Unlicht',
    'Steel': 'Stahl', 'Fairy': 'Fee',
}

def draw_pokemon_name_with_symbols(canvas_obj, name, x, y, font_name, font_size, color_hex):
    """Zeichnet einen Namen mit Geschlechtssymbolen korrekt (ASCII-Version)."""
    # Ersetze Unicode-Symbole durch ASCII-Alternativen
    if '♀' in name:
        name = name.replace('♀', ' (w)')  # Weiblich
    if '♂' in name:
        name = name.replace('♂', ' (m)')  # Männlich
    
    canvas_obj.setFont(font_name, font_size)
    canvas_obj.setFillColor(HexColor(color_hex))
    canvas_obj.drawString(x, y, name)

# Registriere DejaVu Font für Unicode-Unterstützung (Geschlechtszeichen)
def setup_fonts():
    """Registriert DejaVu Font für Unicode-Unterstützung."""
    try:
        import pkg_resources
        font_path = pkg_resources.resource_filename('reportlab', 'fonts/DejaVuSansMono.ttf')
        if Path(font_path).exists():
            pdfmetrics.registerFont(TTFont('DejaVu', font_path))
            return 'DejaVu'
    except:
        pass
    
    # Fallback: Versuch system fonts
    common_paths = [
        '/System/Library/Fonts/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        'C:\\Windows\\Fonts\\dejaVuSans.ttf',
    ]
    
    for path in common_paths:
        if Path(path).exists():
            try:
                pdfmetrics.registerFont(TTFont('DejaVu', path))
                return 'DejaVu'
            except:
                pass
    
    # Fallback auf Helvetica
    return 'Helvetica'

UNICODE_FONT = setup_fonts()

GENERATION_INFO = {
    1: {'name': 'Kanto', 'color': '#FF6B6B', 'range': (1, 151)},
    2: {'name': 'Johto', 'color': '#4ECDC4', 'range': (152, 251)},
    3: {'name': 'Hoenn', 'color': '#45B7D1', 'range': (252, 386)},
    4: {'name': 'Sinnoh', 'color': '#FFA07A', 'range': (387, 493)},
    5: {'name': 'Unova', 'color': '#98D8C8', 'range': (494, 649)},
    6: {'name': 'Kalos', 'color': '#F7DC6F', 'range': (650, 721)},
    7: {'name': 'Alola', 'color': '#BB8FCE', 'range': (722, 809)},
    8: {'name': 'Galar', 'color': '#85C1E2', 'range': (810, 905)},
}


def draw_cover_page(canvas_obj, generation, total_pokemon):
    """Zeichnet ein Deckblatt für eine Generation."""
    page_width, page_height = A4
    
    canvas_obj.setFillColor(HexColor("#FFFFFF"))
    canvas_obj.rect(0, 0, page_width, page_height, fill=1)
    
    gen_info = GENERATION_INFO[generation]
    gen_color = gen_info['color']
    
    stripe_height = page_height * 0.4
    canvas_obj.setFillColor(HexColor(gen_color))
    canvas_obj.rect(0, page_height - stripe_height, page_width, stripe_height, fill=1)
    
    canvas_obj.setFont("Helvetica-Bold", 48)
    canvas_obj.setFillColor(HexColor("#FFFFFF"))
    title_y = page_height - stripe_height + (stripe_height * 0.55)
    canvas_obj.drawCentredString(page_width / 2, title_y, "BinderPokedex")
    
    canvas_obj.setFont("Helvetica", 28)
    canvas_obj.setFillColor(HexColor(gen_color))
    gen_y = page_height / 2 + 50 * mm
    canvas_obj.drawCentredString(page_width / 2, gen_y, f"Generation {generation}")
    
    canvas_obj.setFont("Helvetica", 32)
    canvas_obj.setFillColor(HexColor(gen_color))
    region_y = gen_y - 40
    canvas_obj.drawCentredString(page_width / 2, region_y, gen_info['name'])
    
    canvas_obj.setFont("Helvetica", 18)
    canvas_obj.setFillColor(HexColor("#666666"))
    count_y = region_y - 40
    start_id, end_id = gen_info['range']
    id_range_text = f"Pokédex #{start_id:03d} - #{end_id:03d}"
    canvas_obj.drawCentredString(page_width / 2, count_y, id_range_text)
    
    canvas_obj.setFont("Helvetica", 16)
    count_text = f"{total_pokemon} Pokémon"
    count_text_y = count_y - 30
    canvas_obj.drawCentredString(page_width / 2, count_text_y, count_text)
    
    canvas_obj.setStrokeColor(HexColor(gen_color))
    canvas_obj.setLineWidth(2)
    line_y = count_text_y - 50
    canvas_obj.line(50 * mm, line_y, page_width - 50 * mm, line_y)
    
    canvas_obj.setFont("Helvetica", 10)
    canvas_obj.setFillColor(HexColor("#999999"))
    canvas_obj.drawCentredString(page_width / 2, 40, "Bitte entlang der gestrickelten Linien ausschneiden")
    
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(HexColor("#CCCCCC"))
    date_text = f"Erstellt: {datetime.now().strftime('%d.%m.%Y')}"
    canvas_obj.drawCentredString(page_width / 2, 20, date_text)


def process_pokemon_image(pokemon, images_dir, temp_dir):
    """Prozessiere ein einzelnes Pokémon-Bild (für parallele Verarbeitung)."""
    num = pokemon['num'].lstrip('#')
    
    # Versuche zuerst lokale Datei
    image_path = images_dir / f"pokemon_{num}.png"
    if image_path.exists():
        try:
            img = PILImage.open(image_path)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            white_bg = PILImage.new('RGB', img.size, (255, 255, 255))
            white_bg.paste(img, (0, 0), img)
            
            temp_path = Path(temp_dir) / f"pokemon_{num}.png"
            white_bg.save(temp_path, 'PNG')
            return (num, str(temp_path))
        except:
            pass
    
    # Versuche verschiedene URLs (Fallback-Quellen)
    urls_to_try = [
        pokemon.get('image_url'),  # Primary: API URL
        f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{num}.png",  # Fallback 1: Github
        f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{num}.png",  # Fallback 2: Official Art
        f"http://www.serebii.net/art/{num}.png",  # Fallback 3: Serebii
    ]
    
    for url in urls_to_try:
        if not url:
            continue
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                img = PILImage.open(io.BytesIO(response.content))
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                white_bg = PILImage.new('RGB', img.size, (255, 255, 255))
                white_bg.paste(img, (0, 0), img)
                
                temp_path = Path(temp_dir) / f"pokemon_{num}.png"
                white_bg.save(temp_path, 'PNG')
                return (num, str(temp_path))
        except:
            continue
    
    return (num, None)


def draw_pokemon_card(canvas_obj, pokemon, x, y, width, height, processed_images, missing_images):
    """Zeichnet eine einzelne Pokémon-Karte."""
    
    type1 = pokemon.get('type1', 'Normal')
    
    # Kopfzeile mit Hintergrund
    header_height = 12 * mm
    header_color = '#F8F8F0'
    
    canvas_obj.setFillColor(HexColor(header_color))
    canvas_obj.rect(x, y + height - header_height, width, header_height, fill=1, stroke=0)
    
    # Rahmen
    canvas_obj.setLineWidth(0.5)
    canvas_obj.setStrokeColor(HexColor("#CCCCCC"))
    canvas_obj.rect(x, y, width, height)
    
    # Gestrichelte Schnittlinie (Cutting guide)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.setStrokeColor(HexColor("#DDDDDD"))
    canvas_obj.setDash(2, 2)
    cut_offset = 2 * mm
    canvas_obj.rect(x - cut_offset, y - cut_offset, width + 2*cut_offset, height + 2*cut_offset)
    canvas_obj.setDash()
    
    # Text in Kopfzeile
    canvas_obj.setFont("Helvetica-Bold", 9)
    canvas_obj.setFillColor(HexColor("#3D3D3D"))
    canvas_obj.drawString(x + 3, y + height - header_height + 5, pokemon['num'])
    
    canvas_obj.setFont("Helvetica", 5)
    type_text = TYPE_NAMES_DE.get(type1, type1)
    type_width = canvas_obj.stringWidth(type_text, "Helvetica", 5)
    canvas_obj.setFillColor(HexColor("#5D5D5D"))
    canvas_obj.drawString(x + width - type_width - 3, y + height - header_height + 5, type_text)
    
    german_name = pokemon.get('name_de', pokemon['name_en'])
    name_y = y + height - header_height + 11
    
    # Berechne x Position für zentrierten Text (ungefähre Breite)
    approx_width = canvas_obj.stringWidth(german_name.replace('♀', 'o').replace('♂', 'o'), f"{UNICODE_FONT}-Bold", 8)
    name_x = x + (width - approx_width) / 2
    
    draw_pokemon_name_with_symbols(canvas_obj, german_name, name_x, name_y, f"{UNICODE_FONT}-Bold", 8, "#2D2D2D")
    
    english_name = pokemon['name_en']
    canvas_obj.setFont("Helvetica", 5)
    en_width = canvas_obj.stringWidth(english_name, "Helvetica", 5)
    en_x = x + (width - en_width) / 2
    canvas_obj.setFillColor(HexColor("#666666"))
    canvas_obj.drawString(en_x, y + height - header_height + 5, english_name)
    
    image_height = height - header_height - 4 * mm
    num = pokemon['num'].lstrip('#')
    image_path = processed_images.get(num)
    
    canvas_obj.setFillColor(HexColor("#FFFFFF"))
    canvas_obj.setLineWidth(0)
    canvas_obj.rect(x, y, width, image_height, fill=1, stroke=0)
    
    if image_path:
        try:
            padding = 2 * mm
            max_width = (width - 2 * padding) / 2
            max_height = (image_height - 2 * padding) / 2
            
            img_x = x + (width - max_width) / 2
            img_y = y + (image_height - max_height) / 2 + padding
            
            canvas_obj.drawImage(
                image_path, img_x, img_y,
                width=max_width, height=max_height,
                preserveAspectRatio=True
            )
        except:
            pass
    else:
        if pokemon['name_en'] not in missing_images:
            missing_images.append(pokemon['name_en'])


def generate_all_generations():
    """Generiert PDFs für alle verfügbaren Generationen."""
    
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    data_dir = project_dir / "data"
    output_dir = project_dir / "output"
    images_dir = project_dir / "images"
    
    output_dir.mkdir(exist_ok=True)
    images_dir.mkdir(exist_ok=True)
    
    print("=" * 80)
    print("PDF-Generierung - Alle Generationen mit Deckblättern")
    print("=" * 80)
    
    all_success = True
    temp_dir = tempfile.mkdtemp()
    
    try:
        for generation in sorted(GENERATION_INFO.keys()):
            input_file = data_dir / f"pokemon_gen{generation}.json"
            if not input_file.exists():
                print(f"\n⏭️  Generation {generation}: Datei nicht gefunden\n")
                continue
            
            output_file = output_dir / f"BinderPokedex_Gen{generation}.pdf"
            
            gen_info = GENERATION_INFO[generation]
            start_id, end_id = gen_info['range']
            
            print(f"\n{'=' * 80}")
            print(f"📊 Generation {generation} ({gen_info['name']})")
            print(f"   Pokédex #{start_id:03d} - #{end_id:03d}")
            print(f"{'=' * 80}")
            
            try:
                with open(input_file, 'r', encoding='utf-8') as f:
                    pokemon_list = json.load(f)
                
                print(f"📋 Geladen: {len(pokemon_list)} Pokémon")
                print(f"🎨 Verarbeite Bilder (parallel)...\n")
                
                processed_images = {}
                # Parallele Verarbeitung mit ThreadPoolExecutor (4 Worker)
                with ThreadPoolExecutor(max_workers=4) as executor:
                    futures = [
                        executor.submit(process_pokemon_image, poke, images_dir, temp_dir)
                        for poke in pokemon_list
                    ]
                    
                    completed = 0
                    for future in as_completed(futures):
                        num, path = future.result()
                        if path:
                            processed_images[num] = path
                        completed += 1
                        
                        # Progress Bar
                        progress = completed / len(pokemon_list)
                        bar_length = 40
                        filled = int(bar_length * progress)
                        bar = "█" * filled + "░" * (bar_length - filled)
                        print(f"\r  [{bar}] {completed}/{len(pokemon_list)} ({progress*100:.0f}%)", end="", flush=True)
                
                print(f"\n✅ {len(processed_images)}/{len(pokemon_list)} Bilder verarbeitet\n")
                
                # PDF erstellen
                print(f"📄 Generiere PDF...")
                c = canvas.Canvas(str(output_file), pagesize=A4)
                page_width, page_height = A4
                margin = 5 * mm
                card_width = 63.5 * mm
                card_height = 88.9 * mm
                gap_x = 4 * mm
                gap_y = 4 * mm
                
                cards_per_row = 3
                cards_per_column = 3
                
                available_width = page_width - 2 * margin
                available_height = page_height - 2 * margin
                
                total_card_width = (card_width * cards_per_row) + (gap_x * (cards_per_row - 1))
                total_card_height = (card_height * cards_per_column) + (gap_y * (cards_per_column - 1))
                
                start_x = margin + (available_width - total_card_width) / 2
                start_y = page_height - margin
                
                missing_images = []
                total_cards_processed = 0
                
                # DECKBLATT
                draw_cover_page(c, generation, len(pokemon_list))
                c.showPage()
                print(f"  📑 Deckblatt erstellt")
                
                # Karten
                current_page = 1
                for idx, pokemon in enumerate(pokemon_list):
                    if idx % 9 == 0 and idx > 0:
                        c.showPage()
                        current_page += 1
                        print(f"  📄 Seite {current_page} erstellt ({idx}/{len(pokemon_list)} Karten)")
                    
                    if idx % 9 == 0:
                        c.setFillColor(HexColor("#FFFFFF"))
                        c.rect(0, 0, page_width, page_height, fill=1)
                    
                    position_on_page = idx % 9
                    row = position_on_page // cards_per_row
                    col = position_on_page % cards_per_row
                    
                    x = start_x + col * (card_width + gap_x)
                    y = start_y - row * (card_height + gap_y) - card_height
                    
                    draw_pokemon_card(
                        c, pokemon, x, y, card_width, card_height, 
                        processed_images, missing_images
                    )
                    
                    total_cards_processed += 1
                
                c.showPage()
                c.save()
                
                file_size_mb = output_file.stat().st_size / 1024 / 1024
                total_pages = (total_cards_processed + 8) // 9 + 1
                
                print(f"\n✅ PDF erfolgreich erstellt!")
                print(f"   Datei:  {output_file.name}")
                print(f"   Größe:  {file_size_mb:.2f} MB")
                print(f"   Seiten: {total_pages} (mit Deckblatt)")
                
                if missing_images:
                    print(f"   ⚠️  {len(missing_images)} Bilder nicht gefunden")
                
            except Exception as e:
                print(f"❌ Fehler bei Generation {generation}: {e}")
                import traceback
                traceback.print_exc()
                all_success = False
        
        print(f"\n{'=' * 80}")
        print("Zusammenfassung:")
        print(f"{'=' * 80}\n")
        
        generated = list(data_dir.glob("BinderPokedex_Gen*.pdf"))
        if generated:
            print(f"✅ {len(generated)} PDFs generiert:")
            for pdf in sorted(generated):
                size_mb = pdf.stat().st_size / 1024 / 1024
                print(f"   📄 {pdf.name} ({size_mb:.2f} MB)")
        
        if all_success:
            print(f"\n✅ Alle Generationen erfolgreich!")
        else:
            print(f"\n⚠️  Einige Generationen hatten Fehler")
        
    finally:
        # Cleanup temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    generate_all_generations()
