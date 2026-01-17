#!/usr/bin/env python3
"""
fetch_pokemon_from_pokeapi.py
Lädt Pokémon-Daten von PokeAPI REST API (OPTIMIERT mit Caching)
Macht nur 1 Request pro Pokémon statt 2, mit lokalem Caching

Verwendung:
    python fetch_pokemon_from_pokeapi.py
"""

import json
import requests
import time
from pathlib import Path
from functools import lru_cache

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

# Deutsche Namen Mapping (Top 200, Rest als Fallback)
GERMAN_NAMES = {
    "bulbasaur": "Bisasam", "ivysaur": "Bisaknosp", "venusaur": "Bisaflor",
    "charmander": "Glumanda", "charmeleon": "Glutexo", "charizard": "Glurak",
    "squirtle": "Schiggy", "wartortle": "Schillok", "blastoise": "Turtok",
    "caterpie": "Raupy", "metapod": "Safcon", "butterfree": "Smettbo",
    "weedle": "Hornliu", "kakuna": "Kokuna", "beedrill": "Bibor",
    "pidgey": "Taubsi", "pidgeotto": "Tauboga", "pidgeot": "Tauboss",
    "rattata": "Rattfratz", "raticate": "Rattikarl", "spearow": "Habitak",
    "fearow": "Ibitak", "ekans": "Rettan", "arbok": "Arbok",
    "pikachu": "Pikachu", "raichu": "Raichu", "sandshrew": "Sandan",
    "sandslash": "Sandamer", "nidoran-f": "Nidoran♀", "nidorina": "Nidorina",
    "nidoqueen": "Nidoqueen", "nidoran-m": "Nidoran♂", "nidorino": "Nidorino",
    "nidoking": "Nidoking", "clefairy": "Piepi", "clefable": "Pixi",
    "vulpix": "Vulpix", "ninetales": "Vulnona", "jigglypuff": "Pummeluff",
    "wigglytuff": "Knuddeluff", "zubat": "Zubat", "golbat": "Golbat",
    "oddish": "Bisaknosp", "gloom": "Bisamm", "vileplume": "Bisolbit",
    "paras": "Paras", "parasect": "Parasek", "venonat": "Flormel",
    "venomoth": "Floross", "diglett": "Digda", "dugtrio": "Digdri",
    "meowth": "Mauzi", "persian": "Persitan", "psyduck": "Enton",
    "golduck": "Entoron", "mankey": "Manakka", "primeape": "Leviator",
    "growlithe": "Fukano", "arcanine": "Arkani", "poliwag": "Quapsel",
    "poliwhirl": "Quaputzer", "poliwrath": "Quappo", "abra": "Abra",
    "kadabra": "Kadabra", "alakazam": "Alakazam", "machop": "Machollo",
    "machoke": "Macho", "machamp": "Machomei", "bellsprout": "Bisaknosp",
    "weepinbell": "Weepinbell", "victreebel": "Todesbiss", "tentacool": "Tentacha",
    "tentacruel": "Tentoxa", "slowpoke": "Flegmon", "slowbro": "Lahmus",
    "seel": "Seeper", "dewgong": "Seemon", "shellder": "Muschas",
    "cloyster": "Austos", "gastly": "Nebulak", "haunter": "Alpollo",
    "gengar": "Gengar", "onix": "Onix", "drowzee": "Traumato",
    "hypno": "Hypno", "krabby": "Krabby", "kingler": "Kingler",
    "voltorb": "Lektro", "electrode": "Elektro", "exeggcute": "Owei",
    "exeggutor": "Kokowei", "cubone": "Tragosso", "marowak": "Tragosso",
    "hitmonlee": "Kicklee", "hitmonchan": "Nockchan", "lickitung": "Schlurp",
    "koffing": "Koffing", "weezing": "Weezing", "rhyhorn": "Rihorn",
    "rhydon": "Rhinozeros", "chansey": "Chaneira", "kangaskhan": "Kangask",
    "horsea": "Seepferdchen", "seadra": "Seejong", "goldeen": "Goldini",
    "seaking": "Golking", "staryu": "Seestern", "starmie": "Starmie",
    "mr-mime": "Pantimime", "scyther": "Sichlor", "jynx": "Rossana",
    "electabuzz": "Elekids", "magby": "Magby", "magnemite": "Magnetilo",
    "magneton": "Magneton", "farfetchd": "Porenta", "doduo": "Dodu",
    "dodrio": "Dodos", "lapras": "Lapras", "ditto": "Ditto",
    "eevee": "Evoli", "vaporeon": "Aquana", "jolteon": "Blitza",
    "flareon": "Flamara", "porygon": "Porygon", "omanyte": "Omot",
    "omastar": "Omastar", "kabuto": "Kabuto", "kabutops": "Kabutops",
    "aerodactyl": "Aerodactyl", "snorlax": "Relaxo", "articuno": "Articuno",
    "zapdos": "Zapdos", "moltres": "Moltres", "dratini": "Dratini",
    "dragonair": "Dragonair", "dragonite": "Dragonite", "mewtwo": "Mewtu",
    "mew": "Mew",
    # Gen 2
    "chikorita": "Endivie", "bayleef": "Bisaknosp", "meganium": "Meganie",
    "cyndaquil": "Feurigel", "quilava": "Lockstoff", "typhlosion": "Typhona",
    "totodile": "Quapsel", "croconaw": "Quagga", "feraligatr": "Tohaido",
    # Gen 3
    "treecko": "Geckarbor", "grovyle": "Gekquartz", "sceptile": "Reptain",
    "torchic": "Flemmli", "combusken": "Jungglut", "blaziken": "Lohgock",
}


TYPE_NAMES_DE = {
    "normal": "Normal",
    "fighting": "Kampf",
    "flying": "Flug",
    "poison": "Gift",
    "ground": "Boden",
    "rock": "Gestein",
    "bug": "Käfer",
    "ghost": "Spuk",
    "steel": "Stahl",
    "fire": "Feuer",
    "water": "Wasser",
    "grass": "Pflanze",
    "electric": "Elektro",
    "psychic": "Psycho",
    "ice": "Eis",
    "dragon": "Drache",
    "dark": "Unlicht",
    "fairy": "Fee",
}

# Request-Cache für Effizienz
_request_cache = {}


def fetch_pokemon_data(generation):
    """Lädt Pokémon-Daten von PokeAPI (OPTIMIERT - nur 1 Request pro Pokémon)."""
    
    start_id, end_id, region_name = GENERATION_RANGES[generation]
    
    print(f"\n{'=' * 80}")
    print(f"📊 Generation {generation} ({region_name})")
    print(f"   Pokédex #{start_id:03d} - #{end_id:03d}")
    print(f"{'=' * 80}")
    
    pokemon_list = []
    count = end_id - start_id + 1
    
    for idx, pokemon_id in enumerate(range(start_id, end_id + 1), 1):
        # Lade einzeln mit Caching
        url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}/"
        
        try:
            # Cache Check
            if url in _request_cache:
                data = _request_cache[url]
            else:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                data = response.json()
                _request_cache[url] = data  # Cache
            
            name_en = data.get("name", "").capitalize()
            name_de = GERMAN_NAMES.get(data.get("name", "").lower(), name_en)
            
            # Typen
            types = [t["type"]["name"] for t in data.get("types", [])]
            type1 = TYPE_NAMES_DE.get(types[0] if types else "normal", types[0] if types else "Normal")
            type2 = TYPE_NAMES_DE.get(types[1], types[1]) if len(types) > 1 else None
            
            # Bild
            sprites = data.get("sprites", {})
            image_url = sprites.get("front_default") or f"http://www.serebii.net/xy/pokemon/{pokemon_id:03d}.png"
            
            pokemon = {
                "id": pokemon_id,
                "num": f"#{pokemon_id:03d}",
                "name_en": name_en,
                "name_de": name_de,
                "type1": type1,
                "type2": type2,
                "image_url": image_url,
                "generation": generation
            }
            
            pokemon_list.append(pokemon)
            
            # Progress-Anzeige
            bar_length = 40
            progress = idx / count
            filled = int(bar_length * progress)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"\r  [{bar}] {idx}/{count} ({progress*100:.0f}%)", end="", flush=True)
            
            # Rate Limiting (respektvoll gegenüber API)
            time.sleep(0.05)  # 50ms pro Request
            
        except requests.RequestException as e:
            print(f"\n❌ Fehler bei Pokémon #{pokemon_id}: {e}")
            continue
    
    print(f"\n✅ {len(pokemon_list)} Pokémon geladen")
    return pokemon_list


def save_generation_data(generation, pokemon_list):
    """Speichert Pokémon-Daten als JSON."""
    
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    data_dir = project_dir / "data"
    
    data_dir.mkdir(exist_ok=True)
    output_file = data_dir / f"pokemon_gen{generation}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(pokemon_list, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Gespeichert: {output_file.name}")


def main():
    """Hauptfunktion: Lädt Generationen (alle oder einzeln)."""
    import sys
    
    print("=" * 80)
    print("🚀 PokéAPI Data Fetcher (OPTIMIERT - Mit Caching & Progress)")
    print("=" * 80)
    
    # Prüfe auf Kommandozeilen-Argument
    if len(sys.argv) > 1:
        try:
            target_gen = int(sys.argv[1])
            if target_gen not in GENERATION_RANGES:
                print(f"❌ Generation {target_gen} existiert nicht (1-9)")
                sys.exit(1)
            generations = [target_gen]
            print(f"📍 Lade nur Generation {target_gen}\n")
        except ValueError:
            print(f"❌ Ungültige Eingabe: {sys.argv[1]}")
            print(f"   Verwendung: python fetch_pokemon_from_csv.py [1-9]")
            sys.exit(1)
    else:
        generations = sorted(GENERATION_RANGES.keys())
        print("📍 Lade alle Generationen\n")
    
    total_pokemon = 0
    start_time = time.time()
    
    for generation in generations:
        gen_start = time.time()
        pokemon_list = fetch_pokemon_data(generation)
        gen_duration = time.time() - gen_start
        
        if pokemon_list:
            save_generation_data(generation, pokemon_list)
            total_pokemon += len(pokemon_list)
            print(f"  ⏱️  {gen_duration:.1f}s")
        else:
            print(f"⏭️  Generation {generation} übersprungen\n")
    
    total_duration = time.time() - start_time
    
    print(f"\n{'=' * 80}")
    print(f"✅ Fertig! {total_pokemon} Pokémon in {total_duration:.1f}s")
    print(f"{'=' * 80}")
    print("\n📝 Nächste Schritte:")
    print("  python scripts/generate_pdf.py  # Generiere PDFs")


if __name__ == "__main__":
    main()
