#!/usr/bin/env python3
"""
Download Pokemon images from serebii.net
Speichert 151 Pokemon-Bilder von Generation 1
"""

import json
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


def download_images():
    """
    Laden Sie Bilder für alle 151 Gen 1 Pokemon herunter.
    """
    
    # Pfade
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    data_dir = project_dir / "data"
    input_file = data_dir / "pokemon_gen1.json"
    images_dir = data_dir / "images"
    
    print("=" * 80)
    print("Pokemon-Bilder herunterladen")
    print("=" * 80)
    
    # Input prüfen
    if not input_file.exists():
        print(f"\n❌ Input-Datei nicht gefunden: {input_file}")
        print("   Bitte erst add_german_names.py ausführen!")
        return False
    
    # Images-Verzeichnis erstellen
    images_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📂 Input:   {input_file.name}")
    print(f"📁 Ausgabe: {images_dir.name}/")
    
    try:
        # JSON laden
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📄 Geladen: {len(data)} Pokemon\n")
        
        # Statistik
        downloaded = 0
        skipped = 0
        failed = 0
        
        # Für jedes Pokemon
        for i, pokemon in enumerate(data, 1):
            name = pokemon['name_en']
            image_url = pokemon['image_url']
            num = pokemon['num']
            
            # Dateiname: pokemon_XXX.png
            filename = f"pokemon_{num.lstrip('#')}.png"
            filepath = images_dir / filename
            
            # Status
            progress = f"[{i:3d}/{len(data)}]"
            
            # Wenn bereits vorhanden, überspringen
            if filepath.exists():
                print(f"{progress} ⏭️  {name:<15} → {filename} (existiert)")
                skipped += 1
                continue
            
            # Herunterladen
            try:
                # Header mit User-Agent (serebii.net braucht das)
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
                req = Request(image_url, headers=headers)
                
                with urlopen(req, timeout=10) as response:
                    image_data = response.read()
                
                # Speichern
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                
                print(f"{progress} ✅ {name:<15} → {filename}")
                downloaded += 1
                
                # Kurze Pause, um nicht zu schnell zu viele Anfragen zu machen
                time.sleep(0.1)
                
            except (HTTPError, URLError) as e:
                print(f"{progress} ❌ {name:<15} → FEHLER: {e}")
                failed += 1
                
        # Zusammenfassung
        print("\n" + "=" * 80)
        print("Statistik:")
        print(f"  Heruntergeladen: {downloaded}/{len(data)}")
        print(f"  Übersprungen:    {skipped}/{len(data)}")
        print(f"  Fehler:          {failed}/{len(data)}")
        print("=" * 80)
        
        if failed > 0:
            print(f"\n⚠️  {failed} Bilder konnten nicht heruntergeladen werden")
            return False
        
        print("\n✅ Alle Bilder erfolgreich heruntergeladen!")
        return True
        
    except Exception as e:
        print(f"\n❌ Fehler beim Verarbeiten: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = download_images()
    exit(0 if success else 1)
