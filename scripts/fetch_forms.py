"""
Fetch Pokémon Forms from PokeAPI

Main script to fetch and populate variant data files.
Delegates to specialized form_fetchers for each variant type.

Usage:
    python fetch_forms.py --type mega_evolution
    python fetch_forms.py --type all
"""
import json
import sys
import argparse
from pathlib import Path
import time

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / 'lib'))

from lib.form_fetchers import MegaEvolutionFetcher


def main():
    parser = argparse.ArgumentParser(description='Fetch Pokémon variant forms from PokeAPI')
    parser.add_argument('--type', '-t', choices=['mega_evolution', 'all'], default='mega_evolution',
                       help='Type of forms to fetch')
    args = parser.parse_args()
    
    data_dir = Path(__file__).parent.parent / 'data' / 'variants'
    
    # Fetch Mega Evolution forms
    if args.type in ['mega_evolution', 'all']:
        print("\n🔄 Fetching Mega Evolution forms from PokeAPI...")
        print("   (This may take a minute - fetching 87 Pokémon with form-specific artwork)")
        
        start_time = time.time()
        forms_data = MegaEvolutionFetcher.fetch_forms()
        elapsed = time.time() - start_time
        
        output_file = data_dir / 'variants_mega.json'
        
        # Load existing data to preserve custom fields like iconic_pokemon_ids
        existing_data = {}
        if output_file.exists():
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except:
                pass
        
        # Prepare new data with PokeAPI fetched content
        data = {
            "variant_type": "mega_evolution",
            "variant_name": "Mega Evolution",
            "short_code": "MEGA",
            "icon": "⚡",
            "color_hex": "#FFD700",
            **forms_data  # Includes pokemon_count, forms_count, iconic_pokemon_ids, pokemon
        }
        
        # Note: iconic_pokemon_ids is now provided by the fetcher and included via forms_data
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Successfully populated {output_file}")
        print(f"   • {data['pokemon_count']} Pokémon species")
        print(f"   • {data['forms_count']} Mega forms")
        if "iconic_pokemon_ids" in data:
            print(f"   • {len(data['iconic_pokemon_ids'])} iconic Pokémon defined")
        print(f"   • Completed in {elapsed:.1f}s")


if __name__ == '__main__':
    main()

