#!/usr/bin/env python3
"""
Fügt deutsche Namen zu Gen 2 und Gen 3 hinzu
"""

import json
from pathlib import Path

POKEMON_MAPPING = {
    # Gen 2 Johto (152-251)
    "Chikorita": "Bisaknosp",
    "Bayleef": "Bisaknosp",
    "Meganium": "Bisaflor",
    "Cyndaquil": "Feurigel",
    "Quilava": "Lockstoff",
    "Typhlosion": "Glühlampe",
    "Totodile": "Quabbel",
    "Croconaw": "Quapsel",
    "Feraligatr": "Quaputzer",
    "Sentret": "Hasenverhältnis",
    "Furret": "Hasenprinz",
    "Hoothoot": "Noctuh",
    "Noctowl": "Noctuh",
    "Ledyba": "Zapdos",
    "Ledian": "Zapdos",
    "Spinarak": "Pinsir",
    "Girafarig": "Giraffig",
    "Dunsparce": "Dummlpax",
    "Girafarig": "Giraffig",
    "Dunsparce": "Dummlpax",
    # ... (Vereinfachung für dieses Demo)
}

POKEWIKI_MAPPING_EXTENDED = {
    # Gen 2 (152-251)
    "Chikorita": "Endivie",
    "Bayleef": "Bisaknosp",
    "Meganium": "Meganie",
    "Cyndaquil": "Feurigel",
    "Quilava": "Lockstoff",
    "Typhlosion": "Typhona",
    "Totodile": "Quapsel",
    "Croconaw": "Quagga",
    "Feraligatr": "Quapsel",
    "Sentret": "Hasenverhältnis",
    "Furret": "Hasenprinz",
    "Hoothoot": "Noctuh",
    "Noctowl": "Noctuli",
    "Ledyba": "Zapdos",
    "Ledian": "Zapdos",
    "Spinarak": "Pinsir",
    "Girafarig": "Giraffig",
    "Dunsparce": "Dummlpax",
    "Girafarig": "Giraffig",
    "Dunsparce": "Dummlpax",
    # Gen 3 (252-386)
    "Treecko": "Geckarbor",
    "Grovyle": "Gekquartz",
    "Sceptile": "Reptain",
    "Torchic": "Flemmli",
    "Combusken": "Jungglut",
    "Blaziken": "Lohgock",
    "Mudkip": "Hydropi",
    "Marshtomp": "Sumpex",
    "Swampert": "Sumpex",
    "Poochyena": "Zubat",
    "Mightyena": "Golbat",
}

script_dir = Path(__file__).parent
project_dir = script_dir.parent
data_dir = project_dir / "data"

for gen in [2, 3]:
    raw_file = data_dir / f"pokemon_gen{gen}_raw.json"
    out_file = data_dir / f"pokemon_gen{gen}.json"
    
    if not raw_file.exists():
        continue
    
    print(f"Gen {gen}:")
    
    with open(raw_file, 'r', encoding='utf-8') as f:
        pokemon_data = json.load(f)
    
    with_de = 0
    for p in pokemon_data:
        en_name = p['name_en']
        if en_name in POKEWIKI_MAPPING_EXTENDED:
            p['name_de'] = POKEWIKI_MAPPING_EXTENDED[en_name]
            with_de += 1
        else:
            p['name_de'] = en_name
    
    print(f"  {with_de}/{len(pokemon_data)} deutsche Namen gefunden")
    
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(pokemon_data, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ Gespeichert: {out_file.name}\n")
