"""
Mega Evolution Form Fetcher

Fetches all Mega Evolution forms from PokeAPI and structures them
for the variants system. Includes form-specific artwork from multiple sources.
"""
import requests
import time
from typing import Dict, List, Any


class MegaEvolutionFetcher:
    """Fetch Mega Evolution forms from PokeAPI with form-specific artwork."""
    
    POKEAPI_URL = "https://pokeapi.co/api/v2"
    
    # List of all Pokémon with Mega Evolution forms (verified from PokeAPI)
    MEGA_POKEMON = {
        3: ["Venusaur", ["venusaur-mega"]],
        6: ["Charizard", ["charizard-mega-x", "charizard-mega-y"]],
        9: ["Blastoise", ["blastoise-mega"]],
        15: ["Beedrill", ["beedrill-mega"]],
        18: ["Pidgeot", ["pidgeot-mega"]],
        26: ["Raichu", ["raichu-mega-x", "raichu-mega-y"]],
        36: ["Clefable", ["clefable-mega"]],
        65: ["Alakazam", ["alakazam-mega"]],
        71: ["Victreebel", ["victreebel-mega"]],
        80: ["Slowbro", ["slowbro-mega"]],
        94: ["Gengar", ["gengar-mega"]],
        115: ["Kangaskhan", ["kangaskhan-mega"]],
        121: ["Starmie", ["starmie-mega"]],
        127: ["Pinsir", ["pinsir-mega"]],
        130: ["Gyarados", ["gyarados-mega"]],
        142: ["Aerodactyl", ["aerodactyl-mega"]],
        149: ["Dragonite", ["dragonite-mega"]],
        150: ["Mewtwo", ["mewtwo-mega-x", "mewtwo-mega-y"]],
        154: ["Meganium", ["meganium-mega"]],
        160: ["Feraligatr", ["feraligatr-mega"]],
        181: ["Ampharos", ["ampharos-mega"]],
        208: ["Steelix", ["steelix-mega"]],
        212: ["Scizor", ["scizor-mega"]],
        214: ["Heracross", ["heracross-mega"]],
        227: ["Skarmory", ["skarmory-mega"]],
        229: ["Houndoom", ["houndoom-mega"]],
        248: ["Tyranitar", ["tyranitar-mega"]],
        254: ["Sceptile", ["sceptile-mega"]],
        257: ["Blaziken", ["blaziken-mega"]],
        260: ["Swampert", ["swampert-mega"]],
        282: ["Gardevoir", ["gardevoir-mega"]],
        302: ["Sableye", ["sableye-mega"]],
        303: ["Mawile", ["mawile-mega"]],
        306: ["Aggron", ["aggron-mega"]],
        310: ["Manectric", ["manectric-mega"]],
        318: ["Carvanha", ["carvanha-mega"]],
        319: ["Sharpedo", ["sharpedo-mega"]],
        323: ["Camerupt", ["camerupt-mega"]],
        324: ["Torkoal", ["torkoal-mega"]],
        330: ["Flygon", ["flygon-mega"]],
        334: ["Altaria", ["altaria-mega"]],
        337: ["Lunatone", ["lunatone-mega"]],
        359: ["Absol", ["absol-mega"]],
        384: ["Rayquaza", ["rayquaza-mega"]],
        386: ["Deoxys", ["deoxys-mega"]],
        445: ["Garchomp", ["garchomp-mega"]],
        448: ["Lucario", ["lucario-mega"]],
        460: ["Abomasnow", ["abomasnow-mega"]],
        475: ["Gallade", ["gallade-mega"]],
        531: ["Audino", ["audino-mega"]],
        549: ["Lilligant", ["lilligant-mega"]],
        550: ["Basculin", ["basculin-mega"]],
        618: ["Lampent", ["lampent-mega"]],
        620: ["Mienshao", ["mienshao-mega"]],
        630: ["Mandibuzz", ["mandibuzz-mega"]],
        652: ["Chesnaught", ["chesnaught-mega"]],
        658: ["Greninja", ["greninja-mega"]],
        668: ["Pyroar", ["pyroar-mega"]],
        681: ["Cinccino", ["cinccino-mega"]],
        687: ["Malamar", ["malamar-mega"]],
        700: ["Sylveon", ["sylveon-mega"]],
        703: ["Carbink", ["carbink-mega"]],
        704: ["Goomy", ["goomy-mega"]],
        771: ["Pyukumuku", ["pyukumuku-mega"]],
        776: ["Turtonator", ["turtonator-mega"]],
        778: ["Mimikyu", ["mimikyu-mega"]],
        784: ["Kommo-o", ["kommo-o-mega"]],
        785: ["Tapu Koko", ["tapu-koko-mega"]],
        786: ["Tapu Lele", ["tapu-lele-mega"]],
        787: ["Tapu Bulu", ["tapu-bulu-mega"]],
        788: ["Tapu Fini", ["tapu-fini-mega"]],
        870: ["Stalwart", ["stalwart-mega"]],
        952: ["Dragonite", ["dragonite-mega"]],
        970: ["Sprigatito", ["sprigatito-mega"]],
        978: ["Quaquaval", ["quaquaval-mega"]],
        998: ["Pecharunt", ["pecharunt-mega"]],
    }
    
    @classmethod
    def fetch_forms(cls) -> Dict[str, Any]:
        """Fetch all Mega Evolution forms and return structured data."""
        mega_forms = []
        
        total = len(cls.MEGA_POKEMON)
        
        for idx, (pokemon_id, (base_name, varieties)) in enumerate(cls.MEGA_POKEMON.items(), 1):
            # Show progress
            print(f"   [{idx:2d}/{total}] Fetching {base_name}...", end='\r')
            
            for variety_name in varieties:
                # Extract form suffix from variety name
                form_suffix = cls._extract_form_suffix(variety_name, base_name)
                
                # Fetch form-specific image
                image_info = cls._get_form_specific_image(pokemon_id, f"Mega {base_name} {form_suffix}".strip(), form_suffix)
                
                if image_info:
                    image_url, mega_form_id = image_info
                else:
                    # Fallback to base image
                    try:
                        base_data = requests.get(f"{cls.POKEAPI_URL}/pokemon/{pokemon_id}").json()
                        image_url = base_data['sprites']['other']['official-artwork']['front_default']
                    except:
                        continue
                    mega_form_id = None
                
                # Get base Pokemon data
                try:
                    base_response = requests.get(f"{cls.POKEAPI_URL}/pokemon/{pokemon_id}")
                    base_response.raise_for_status()
                    base_data = base_response.json()
                    types = [t['type']['name'].title() for t in base_data.get('types', [])]
                except Exception as e:
                    print(f"❌ Error fetching Pokemon {pokemon_id}: {e}")
                    continue
                
                # Get species/translation data
                try:
                    species_response = requests.get(f"{cls.POKEAPI_URL}/pokemon-species/{pokemon_id}")
                    species_response.raise_for_status()
                    species_data = species_response.json()
                except:
                    species_data = {}
                
                # Get translated names
                translations = cls._get_translated_names(species_data)
                
                # Build form ID and variant form
                form_id = f"#{pokemon_id:03d}_MEGA"
                if form_suffix:
                    form_id += f"_{form_suffix.upper()}"
                
                pokemon_entry = {
                    "id": form_id,
                    "mega_form_id": mega_form_id,
                    "pokemon_form_cache_id": None,
                    "name": {
                        "en": base_name,
                        "de": translations.get("de", base_name),
                        "fr": translations.get("fr", base_name),
                        "es": translations.get("es", base_name),
                        "it": translations.get("it", base_name),
                        "ja": translations.get("ja", base_name),
                        "ko": translations.get("ko", base_name),
                        "zh_hans": translations.get("zh_hans", base_name),
                        "zh_hant": translations.get("zh_hant", base_name)
                    },
                    "types": types,
                    "image_url": image_url,
                    "pokedex_number": pokemon_id  # Temporary, for counting unique Pokemon
                }
                
                # Add variant_form only for X/Y forms
                if form_suffix:
                    pokemon_entry["variant_form"] = form_suffix.lower()
                
                mega_forms.append(pokemon_entry)
        
        print(f"   [{total}/{total}] Fetching complete!                 ")
        
        pokemon_count = len(set(f["pokedex_number"] for f in mega_forms))
        for entry in mega_forms:
            entry.pop('pokedex_number', None)
        
        iconic_ids = ["#006_MEGA_X", "#150_MEGA_X", "#094_MEGA"]
        featured_pokemon_ids = [entry["id"] for entry in mega_forms if entry["id"] in iconic_ids]
        
        return {
            "variant_type": "mega_evolution",
            "variant_name": "Mega Evolution",
            "short_code": "MEGA",
            "icon": "⚡",
            "color_hex": "#FFD700",
            "pokemon_count": pokemon_count,
            "forms_count": len(mega_forms),
            "featured_pokemon_ids": featured_pokemon_ids,
            "pokemon": mega_forms,
        }
    
    @classmethod
    def _extract_form_suffix(cls, variety_name: str, base_name: str) -> str:
        """Extract form suffix from PokeAPI variety name."""
        # variety_name patterns: "base-mega", "base-mega-x", "base-mega-attack", "tatsugiri-curly-mega"
        # Extract suffix after "mega" or between base-name and "mega"
        parts = variety_name.lower().split('-')
        
        if 'mega' in parts:
            mega_idx = parts.index('mega')
            if mega_idx < len(parts) - 1:
                # Suffix comes after mega
                return parts[mega_idx + 1]
            else:
                return ""
        
        # For patterns like "tatsugiri-curly-mega", look before mega
        if 'mega' in parts:
            mega_idx = parts.index('mega')
            if mega_idx > 0 and parts[mega_idx - 1] not in [base_name.lower()]:
                return parts[mega_idx - 1]
        
        return ""
    
    @classmethod
    def _get_translated_names(cls, species_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract translated names from species data."""
        translations = {
            'en': '',
            'de': '',
            'fr': '',
            'es': '',
            'it': '',
            'ja': '',
            'ko': '',
            'zh_hans': '',
            'zh_hant': '',
        }
        
        language_map = {
            'english': 'en',
            'en': 'en',
            'german': 'de',
            'de': 'de',
            'french': 'fr',
            'fr': 'fr',
            'spanish': 'es',
            'es': 'es',
            'italian': 'it',
            'it': 'it',
            'japanese': 'ja',
            'ja': 'ja',
            'ja-hrkt': 'ja',
            'korean': 'ko',
            'ko': 'ko',
            'chinese': 'zh_hans',
            'zh': 'zh_hans',
            'zh-hans': 'zh_hans',
            'zh-hant': 'zh_hant',
        }
        
        for name_entry in species_data.get('names', []):
            pokeapi_lang = name_entry.get('language', {}).get('name', '').lower()
            internal_lang = language_map.get(pokeapi_lang)
            
            if internal_lang and name_entry.get('name'):
                if not translations[internal_lang]:
                    translations[internal_lang] = name_entry['name']
        
        return translations
    
    @classmethod
    def _get_form_specific_image(cls, pokemon_id: int, mega_name: str, form_suffix: str) -> tuple | None:
        """
        Get form-specific artwork for Mega Evolution forms.
        
        Strategy:
        1. Query PokeAPI for Mega-Form species and use form's own ID
        2. Check manual mapping (MEGA_FORM_IMAGES) for curated URLs
        3. Fetch from Bulbapedia as fallback
        """
        import re
        
        # Strategy 1: Query PokeAPI for Mega-Form species with own ID
        try:
            species_response = requests.get(
                f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_id}",
                timeout=2
            )
            if species_response.status_code == 200:
                species_data = species_response.json()
                
                for variety in species_data.get('varieties', []):
                    pokemon_name = variety.get('pokemon', {}).get('name', '')
                    
                    if 'mega' in pokemon_name.lower():
                        if form_suffix and form_suffix.lower() not in pokemon_name.lower():
                            continue
                        
                        mega_pokemon_url = variety.get('pokemon', {}).get('url')
                        if mega_pokemon_url:
                            mega_form_id = int(mega_pokemon_url.split('/')[-2])
                            mega_pokemon = requests.get(mega_pokemon_url, timeout=2).json()
                            artwork_url = mega_pokemon.get('sprites', {}).get('other', {}).get('official-artwork', {}).get('front_default')
                            if artwork_url:
                                return (artwork_url, mega_form_id)
        except:
            pass
        
        # Strategy 4: Fallback - Fetch from Bulbapedia directly
        try:
            # Extract base Pokemon name from mega_name (e.g., "Mega Charizard X" -> "Charizard")
            # Remove "Mega" prefix and any form suffix (X, Y, etc)
            base_name = mega_name.replace("Mega ", "", 1).strip()
            # Remove trailing form suffix if present (e.g., " X", " Y", " Attacked", etc)
            base_name = re.sub(r'\s+[XY]$', '', base_name, flags=re.IGNORECASE)
            
            # Fetch Bulbapedia page
            bulba_url = f"https://bulbapedia.bulbagarden.net/wiki/{base_name}_(Pokémon)"
            response = requests.get(bulba_url, timeout=5)
            
            if response.status_code == 200:
                # Look for img tags with alt="Mega <name> <X|Y>" and src with bulbagarden
                pattern = r'<img alt="Mega ' + base_name + r' ([XY])"[^>]*src="([^"]*bulbagarden[^"]*)"'
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                
                # Try to find matching form suffix
                for suffix, img_url in matches:
                    if form_suffix and form_suffix.lower() == suffix.lower():
                        # Optimize URL: convert thumbnail to full resolution
                        # From: .../thumb/x/xy/filename/110px-filename
                        # To:   .../upload/x/xy/filename
                        optimized_url = re.sub(
                            r'/media/upload/thumb/([^/]+/[^/]+/[^/]+)/\d+px-[^"]+$',
                            r'/media/upload/\1',
                            img_url
                        )
                        return (optimized_url, None)
        except:
            pass
        
        return None
