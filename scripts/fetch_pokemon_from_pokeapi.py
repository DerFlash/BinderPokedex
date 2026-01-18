#!/usr/bin/env python3
"""
Fetch Pokémon data from PokéAPI and save as JSON.

Unterstützt folgende Sprachen (10 insgesamt):
  - en (English)
  - de (German)
  - fr (French)
  - es (Spanish) - mit Enrichment-Verbesserungen
  - it (Italian) - mit Enrichment-Verbesserungen
  - ja (Japanese - echte Schriftzeichen)
  - ko (Korean)
  - zh-Hans (Chinesisch vereinfacht)
  - zh-Hant (Chinesisch traditionell)

Fetch-Modi:
  - Nach Generationen: --generation 1 (oder 1-5, 1,3,5)
  - Nach Pokémon-IDs: --pokemon 1 (oder 1-10, 1,25,151)

Usage:
    python fetch_pokemon_from_pokeapi.py                 # Alle Gen 1-9
    python fetch_pokemon_from_pokeapi.py --generation 1  # Nur Gen 1
    python fetch_pokemon_from_pokeapi.py --pokemon 1-10  # Pokémon #1-10
"""

import json
import argparse
import sys
import time
from pathlib import Path
from typing import List, Tuple

# Add parent directory to path for lib imports
sys.path.insert(0, str(Path(__file__).parent))

from lib.pokeapi_client import PokéAPIClient
from lib.pokemon_processor import PokémonProcessor
from lib.pokemon_enricher import PokémonEnricher
from lib.data_storage import DataStorage


# Generation ranges
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


def parse_generation_argument(gen_arg: str) -> List[int]:
    """
    Parse --generation Argument (1, 1-5, 1,2,3).
    
    Args:
        gen_arg: Generation argument string
        
    Returns:
        List von Generation-Nummern
    """
    result = []
    
    # Comma-separated: 1,2,3
    if ',' in gen_arg:
        for part in gen_arg.split(','):
            gen = int(part.strip())
            if 1 <= gen <= 9:
                result.append(gen)
    # Range: 1-5
    elif '-' in gen_arg:
        start, end = gen_arg.split('-')
        start, end = int(start.strip()), int(end.strip())
        for gen in range(start, end + 1):
            if 1 <= gen <= 9:
                result.append(gen)
    # Single: 1
    else:
        gen = int(gen_arg.strip())
        if 1 <= gen <= 9:
            result.append(gen)
    
    return sorted(set(result))  # Remove duplicates and sort


def parse_pokemon_argument(poke_arg: str) -> List[int]:
    """
    Parse --pokemon Argument (1, 1-10, 1,25,151).
    
    Args:
        poke_arg: Pokemon argument string
        
    Returns:
        List von Pokémon-IDs
    """
    result = []
    
    # Comma-separated: 1,25,151
    if ',' in poke_arg:
        for part in poke_arg.split(','):
            pokemon_id = int(part.strip())
            if 1 <= pokemon_id <= 1025:
                result.append(pokemon_id)
    # Range: 1-10
    elif '-' in poke_arg:
        start, end = poke_arg.split('-')
        start, end = int(start.strip()), int(end.strip())
        for pokemon_id in range(start, end + 1):
            if 1 <= pokemon_id <= 1025:
                result.append(pokemon_id)
    # Single: 1
    else:
        pokemon_id = int(poke_arg.strip())
        if 1 <= pokemon_id <= 1025:
            result.append(pokemon_id)
    
    return sorted(set(result))  # Remove duplicates and sort


def print_progress_bar(current: int, total: int, width: int = 40) -> None:
    """
    Zeige Progress-Bar an (einzeilig, überschreibt sich selbst).
    
    Args:
        current: Aktueller Progress
        total: Gesamtanzahl
        width: Breite der Bar in Zeichen
    """
    if total == 0:
        return
    
    percent = current / total
    filled = int(width * percent)
    bar = '█' * filled + '░' * (width - filled)
    percent_str = f"{percent * 100:.1f}%"
    status = f"  [{bar}] {current}/{total} ({percent_str})"
    
    # Überlagere die Zeile komplett
    print(f"\r{status:<80}", end='', flush=True)


def fetch_pokemon_data(api_client: PokéAPIClient, pokemon_ids: List[int]) -> Tuple[dict, List[int]]:
    """
    Fetch Daten für mehrere Pokémon (alle Sprachen + ES/IT Enrichments).
    
    Args:
        api_client: PokéAPIClient instance
        pokemon_ids: Liste von Pokémon-IDs
        
    Returns:
        Tuple (grouped_by_generation, failed_ids)
    """
    result = {gen: [] for gen in range(1, 10)}
    failed_ids = []
    
    for idx, pokemon_id in enumerate(pokemon_ids):
        # Fetch species und pokemon data
        species_data = api_client.fetch_species_data(pokemon_id)
        pokemon_data = api_client.fetch_pokemon_data(pokemon_id)
        
        if not species_data or not pokemon_data:
            failed_ids.append(pokemon_id)
            print_progress_bar(idx + 1, len(pokemon_ids))
            continue
        
        # Determine generation
        generation = PokémonProcessor.get_generation_for_pokemon(pokemon_id)
        
        # Build record
        record = PokémonProcessor.build_pokemon_record(
            pokemon_id, species_data, pokemon_data, generation
        )
        
        # Always apply ES/IT enrichments if available
        record = PokémonEnricher.enrich_pokemon_data(record, 'es')
        record = PokémonEnricher.enrich_pokemon_data(record, 'it')
        
        result[generation].append(record)
        print_progress_bar(idx + 1, len(pokemon_ids))
    
    print()  # Newline after progress bar
    return result, failed_ids


def main():
    """CLI Entry Point."""
    
    parser = argparse.ArgumentParser(
        description="Fetch Pokémon data from PokéAPI with multi-language support"
    )
    parser.add_argument(
        "--generation", "-g",
        type=str,
        help="Generation(s) to fetch (1, 1-5, 1,2,3). Default: 1-9 (all)"
    )
    parser.add_argument(
        "--pokemon", "-p",
        type=str,
        help="Pokémon ID(s) to fetch (1, 1-10, 1,25,151)"
    )
    
    args = parser.parse_args()
    
    # Determine what to fetch
    if args.generation and args.pokemon:
        print("Error: Cannot use both --generation and --pokemon at the same time")
        return
    
    if args.generation:
        try:
            generations = parse_generation_argument(args.generation)
        except (ValueError, IndexError):
            print(f"Error: Invalid generation format. Use: 1, 1-5, or 1,2,3")
            return
    elif args.pokemon:
        try:
            pokemon_ids = parse_pokemon_argument(args.pokemon)
        except (ValueError, IndexError):
            print(f"Error: Invalid pokémon format. Use: 1, 1-10, or 1,25,151")
            return
    else:
        # Default: all generations
        generations = list(range(1, 10))
    
    # Determine pokemon IDs to fetch
    if args.generation:
        pokemon_ids = []
        for gen in generations:
            start, end, _ = GENERATION_RANGES[gen]
            pokemon_ids.extend(range(start, end + 1))
    
    print("=" * 80)
    print(f"PokéAPI Pokémon Data Fetcher")
    print("=" * 80)
    print(f"Mode: {'Generation' if args.generation else 'Pokémon-IDs'}")
    print(f"Count: {len(pokemon_ids)} Pokémon to fetch")
    print(f"Fetches: All 10 languages (EN, DE, FR, ES, IT, JA, KO, ZH-Hans, ZH-Hant)")
    print(f"         + ES/IT enrichments auto-applied")
    print(f"Estimated time: ~{len(pokemon_ids) // 10} minutes")
    print("=" * 80)
    
    # Initialize
    api_client = PokéAPIClient()
    storage = DataStorage()
    
    # Fetch data
    print("\n🎨 Fetching Pokémon data from PokéAPI...\n")
    start_time = time.time()
    
    try:
        grouped_data, failed_ids = fetch_pokemon_data(api_client, pokemon_ids)
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        return
    
    # Save data
    print("\n💾 Saving data...\n")
    saved_generations = []
    
    for generation in range(1, 10):
        if grouped_data[generation]:
            storage.save_generation(generation, grouped_data[generation])
            saved_generations.append(generation)
            print(f"  ✅ Gen {generation}: {len(grouped_data[generation])} Pokémon saved")
    
    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    
    # Summary
    print("\n" + "=" * 80)
    print(f"✅ Done!")
    print("=" * 80)
    print(f"Total Pokémon fetched: {sum(len(grouped_data[g]) for g in range(1, 10))}")
    print(f"Generations saved: {', '.join(str(g) for g in saved_generations)}")
    print(f"Time elapsed: {minutes}m {seconds}s")
    
    if failed_ids:
        print(f"⚠️  Failed Pokémon: {len(failed_ids)}")
        print(f"   IDs: {failed_ids[:10]}{'...' if len(failed_ids) > 10 else ''}")
        print(f"   Retry with: python fetch_pokemon_from_pokeapi.py --pokemon {','.join(str(id) for id in failed_ids[:5])}")
    
    print("\n📝 Next steps:")
    if saved_generations:
        print(f"  1. python scripts/generate_pdf.py --language [de|en|fr|es|it|ja|ko|zh-hans|zh-hant]")
        print(f"  2. Check generated PDFs in output/")


if __name__ == "__main__":
    main()
