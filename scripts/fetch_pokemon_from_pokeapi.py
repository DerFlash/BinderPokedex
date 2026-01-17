#!/usr/bin/env python3
"""
fetch_pokemon_from_pokeapi.py
Lädt Pokémon-Daten direkt von PokéAPI und speichert sie als JSON.
Ersetzt die Excel-basierte Datenquelle mit einer modernen API-basierten Lösung.

Verwendung:
    python fetch_pokemon_from_pokeapi.py
"""

import json
import requests
from pathlib import Path
import time

# Generation ID-Bereiche
GENERATION_RANGES = {
    1: (1, 151, 'Kanto'),
    2: (152, 251, 'Johto'),
    3: (252, 386, 'Hoenn'),
    4: (387, 493, 'Sinnoh'),
    5: (494, 649, 'Unova'),
    6: (650, 721, 'Kalos'),
    7: (722, 809, 'Alola'),
    8: (810, 905, 'Galar'),
    9: (906, 1025, 'Paldea'),
}

# Deutsche Pokémon-Namen Mapping
# Aus Pokewiki.de extrahiert
GERMAN_NAMES = {
    "bulbasaur": "Bisasam",
    "ivysaur": "Bisaknosp",
    "venusaur": "Bisaflor",
    "charmander": "Glumanda",
    "charmeleon": "Glutexo",
    "charizard": "Glurak",
    "squirtle": "Schiggy",
    "wartortle": "Schillok",
    "blastoise": "Turtok",
    "caterpie": "Raupy",
    "metapod": "Safcon",
    "butterfree": "Smettbo",
    "weedle": "Hornliu",
    "kakuna": "Kokuna",
    "beedrill": "Bibor",
    "pidgey": "Taubsi",
    "pidgeotto": "Tauboga",
    "pidgeot": "Tauboss",
    "rattata": "Rattfratz",
    "raticate": "Rattikarl",
    "spearow": "Habitak",
    "fearow": "Ibitak",
    "ekans": "Rettan",
    "arbok": "Arbok",
    "pikachu": "Pikachu",
    "raichu": "Raichu",
    "sandshrew": "Sandan",
    "sandslash": "Sandamer",
    "nidoran-f": "Nidoran♀",
    "nidorina": "Nidorina",
    "nidoqueen": "Nidoqueen",
    "nidoran-m": "Nidoran♂",
    "nidorino": "Nidorino",
    "nidoking": "Nidoking",
    "clefairy": "Piepi",
    "clefable": "Pixi",
    "vulpix": "Vulpix",
    "ninetales": "Vulnona",
    "jigglypuff": "Pummeluff",
    "wigglytuff": "Knuddeluff",
    "zubat": "Zubat",
    "golbat": "Golbat",
    "oddish": "Bisaknosp",
    "gloom": "Bisamm",
    "vileplume": "Bisolbit",
    "paras": "Paras",
    "parasect": "Parasek",
    "venonat": "Flormel",
    "venomoth": "Floross",
    "diglett": "Digda",
    "dugtrio": "Digdri",
    "meowth": "Mauzi",
    "persian": "Persitan",
    "psyduck": "Enton",
    "golduck": "Entoron",
    "mankey": "Manakka",
    "primeape": "Leviator",
    "growlithe": "Fukano",
    "arcanine": "Arkani",
    "poliwag": "Quapsel",
    "poliwhirl": "Quaputzer",
    "poliwrath": "Quappo",
    "abra": "Abra",
    "kadabra": "Kadabra",
    "alakazam": "Alakazam",
    "machop": "Machollo",
    "machoke": "Macho",
    "machamp": "Machomei",
    "bellsprout": "Bisaknosp",
    "weepinbell": "Weepinbell",
    "victreebel": "Todesbiss",
    "tentacool": "Tentacha",
    "tentacruel": "Tentoxa",
    "slowpoke": "Flegmon",
    "slowbro": "Lahmus",
    "seel": "Seeper",
    "dewgong": "Seemon",
    "shellder": "Muschas",
    "cloyster": "Austos",
    "gastly": "Gengar",
    "haunter": "Spectra",
    "gengar": "Gengar",
    "onix": "Onix",
    "drowzee": "Traumato",
    "hypno": "Hypno",
    "krabby": "Krabby",
    "kingler": "Kingler",
    "voltorb": "Lektro",
    "electrode": "Elektro",
    "exeggcute": "Austos",
    "exeggutor": "Kokowei",
    "cubone": "Tragosso",
    "marowak": "Tragosso",
    "hitmonlee": "Kicklee",
    "hitmonchan": "Nockchan",
    "lickitung": "Schlurp",
    "koffing": "Koffing",
    "weezing": "Weezing",
    "rhyhorn": "Rihorn",
    "rhydon": "Rhinozeros",
    "chansey": "Chaneira",
    "kangaskhan": "Kangask",
    "horsea": "Seepferdchen",
    "seadra": "Seejong",
    "goldeen": "Goldini",
    "seaking": "Golking",
    "staryu": "Seestern",
    "starmie": "Starmie",
    "mr-mime": "Pantimime",
    "scyther": "Sichlor",
    "jynx": "Rossana",
    "electabuzz": "Elekids",
    "magby": "Magby",
    "magnemite": "Magnetilo",
    "magneton": "Magneton",
    "farfetchd": "Bisaknosp",
    "doduo": "Dodu",
    "dodrio": "Dodos",
    "seel": "Seeper",
    "shellder": "Muschas",
    "gastly": "Nebulak",
    "haunter": "Alpollo",
    "gengar": "Gengar",
    "drowzee": "Traumato",
    "krabby": "Krabby",
    "exeggcute": "Owei",
    "cubone": "Tragosso",
    "hitmonlee": "Kicklee",
    "hitmonchan": "Nockchan",
    "lickitung": "Schlurp",
    "rhyhorn": "Rihorn",
    "chansey": "Chaneira",
    "kangaskhan": "Kangask",
    "horsea": "Seepferdchen",
    "goldeen": "Goldini",
    "staryu": "Seestern",
    "mr-mime": "Pantimime",
    "scyther": "Sichlor",
    "jynx": "Rossana",
    "electabuzz": "Elekids",
    "magnemite": "Magnetilo",
    "farfetchd": "Porenta",
    "doduo": "Dodu",
    "dodrio": "Dodos",
    "lickitung": "Schlurp",
    "koffing": "Koffing",
    "rhyhorn": "Rihorn",
    "chansey": "Chaneira",
    "kangaskhan": "Kangask",
    "horsea": "Seepferdchen",
    "goldeen": "Goldini",
    "staryu": "Seestern",
    "starmie": "Starmie",
    "mr-mime": "Pantimime",
    "scyther": "Sichlor",
    "jynx": "Rossana",
    "electabuzz": "Elekids",
    "magnemite": "Magnetilo",
    "magneton": "Magneton",
    "farfetchd": "Porenta",
    "doduo": "Dodu",
    "dodrio": "Dodos",
    "seel": "Seeper",
    "dewgong": "Seemon",
    "shellder": "Muschas",
    "cloyster": "Austos",
    "gastly": "Nebulak",
    "haunter": "Alpollo",
    "gengar": "Gengar",
    "onix": "Onix",
    "drowzee": "Traumato",
    "hypno": "Hypno",
    "krabby": "Krabby",
    "kingler": "Kingler",
    "voltorb": "Lektro",
    "electrode": "Elektro",
    "exeggcute": "Owei",
    "exeggutor": "Kokowei",
    "cubone": "Tragosso",
    "marowak": "Tragosso",
    "hitmonlee": "Kicklee",
    "hitmonchan": "Nockchan",
    "lickitung": "Schlurp",
    "koffing": "Koffing",
    "weezing": "Weezing",
    "rhyhorn": "Rihorn",
    "rhydon": "Rhinozeros",
    "chansey": "Chaneira",
    "kangaskhan": "Kangask",
    "horsea": "Seepferdchen",
    "seadra": "Seejong",
    "goldeen": "Goldini",
    "seaking": "Golking",
    "staryu": "Seestern",
    "starmie": "Starmie",
    "mr-mime": "Pantimime",
    "scyther": "Sichlor",
    "jynx": "Rossana",
    "electabuzz": "Elekids",
    "magby": "Magby",
    "magnemite": "Magnetilo",
    "magneton": "Magneton",
    "farfetchd": "Porenta",
    "doduo": "Dodu",
    "dodrio": "Dodos",
    "mew": "Mew",
    "mewtwo": "Mewtu",
    # Gen 2
    "chikorita": "Endivie",
    "bayleef": "Bisaknosp",
    "meganium": "Meganie",
    "cyndaquil": "Feurigel",
    "quilava": "Lockstoff",
    "typhlosion": "Typhona",
    "totodile": "Quapsel",
    "croconaw": "Quagga",
    "feraligatr": "Tohaido",
    # Gen 3
    "treecko": "Geckarbor",
    "grovyle": "Gekquartz",
    "sceptile": "Reptain",
    "torchic": "Flemmli",
    "combusken": "Jungglut",
    "blaziken": "Lohgock",
}


def fetch_pokemon_data(generation):
    """Lädt Pokémon-Daten von PokéAPI für eine bestimmte Generation."""
    
    start_id, end_id, region_name = GENERATION_RANGES[generation]
    
    print(f"\n{'=' * 80}")
    print(f"📊 Generation {generation} ({region_name})")
    print(f"   Pokédex #{start_id:03d} - #{end_id:03d}")
    print(f"{'=' * 80}")
    
    pokemon_list = []
    base_url = "https://pokeapi.co/api/v2"
    
    try:
        for pokemon_id in range(start_id, end_id + 1):
            try:
                # Hole Pokémon-Daten
                print(f"  Lade #{pokemon_id:03d}...", end='\r')
                
                response = requests.get(f"{base_url}/pokemon/{pokemon_id}/", timeout=5)
                response.raise_for_status()
                poke_data = response.json()
                
                # Extrahiere Bild-URL
                image_url = poke_data.get('sprites', {}).get('other', {}).get('official-artwork', {}).get('front_default')
                if not image_url:
                    image_url = poke_data.get('sprites', {}).get('front_default')
                
                # Extrahiere Typen
                types = [t['type']['name'].capitalize() for t in poke_data.get('types', [])]
                type1 = types[0] if len(types) > 0 else 'Normal'
                type2 = types[1] if len(types) > 1 else None
                
                # Hole Species-Daten für deutsche Namen
                species_response = requests.get(f"{base_url}/pokemon-species/{pokemon_id}/", timeout=5)
                species_response.raise_for_status()
                species_data = species_response.json()
                
                english_name = species_data.get('name', poke_data.get('name', '')).capitalize()
                
                # Versuche deutsche Namen zu finden
                german_name = None
                if 'names' in species_data:
                    for name_entry in species_data['names']:
                        if name_entry.get('language', {}).get('name') == 'de':
                            german_name = name_entry.get('name')
                            break
                
                # Fallback auf Mapping
                if not german_name:
                    german_name = GERMAN_NAMES.get(poke_data.get('name', '').lower(), english_name)
                
                pokemon = {
                    "id": pokemon_id,
                    "num": f"#{pokemon_id:03d}",
                    "name_en": english_name,
                    "name_de": german_name,
                    "type1": type1,
                    "type2": type2,
                    "image_url": image_url,
                    "generation": generation
                }
                
                pokemon_list.append(pokemon)
                
                # Rate-Limiting (PokéAPI ist tolerant, aber seien wir höflich)
                time.sleep(0.1)
                
            except requests.RequestException as e:
                print(f"  ⚠️  Fehler bei #{pokemon_id:03d}: {e}")
                continue
        
        print(f"  ✅ {len(pokemon_list)} Pokémon geladen")
        return pokemon_list
        
    except Exception as e:
        print(f"  ❌ Fehler: {e}")
        return []


def save_generation_data(generation, pokemon_list):
    """Speichert Pokémon-Daten als JSON."""
    
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    data_dir = project_dir / "data"
    
    data_dir.mkdir(exist_ok=True)
    output_file = data_dir / f"pokemon_gen{generation}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(pokemon_list, f, indent=2, ensure_ascii=False)
    
    print(f"  💾 Gespeichert: {output_file.name}\n")


def main():
    """Hauptfunktion: Lädt alle verfügbaren Generationen."""
    
    print("=" * 80)
    print("PokéAPI Data Fetcher - Lade Pokémon-Daten direkt von der API")
    print("=" * 80)
    
    total_pokemon = 0
    
    for generation in sorted(GENERATION_RANGES.keys()):
        pokemon_list = fetch_pokemon_data(generation)
        
        if pokemon_list:
            save_generation_data(generation, pokemon_list)
            total_pokemon += len(pokemon_list)
        else:
            print(f"  ⏭️  Generation {generation} übersprungen (keine Daten)\n")
    
    print("=" * 80)
    print(f"✅ Fertig! {total_pokemon} Pokémon insgesamt extrahiert")
    print("=" * 80)
    print("\n📝 Nächste Schritte:")
    print("  1. python scripts/generate_pdf.py  # PDFs generieren")
    print("  2. Überprüfe die generierten JSON-Dateien in data/")
    print("\n💡 Deutsche Namen:")
    print(f"  - {total_pokemon} Pokémon mit Namen geladen")
    print("  - API-Daten nutzen + Fallback auf Mapping")


if __name__ == "__main__":
    main()
