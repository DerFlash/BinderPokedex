"""
Fetch National Pokedex data from PokeAPI.

This step loads Pokemon data from PokeAPI for specified generations
and stores it as source data (raw format).
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from lib.pokeapi_client import PokéAPIClient
from .base import BaseStep, PipelineContext


# Generation ranges (Pokemon ID ranges)
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


class FetchPokeAPIStep(BaseStep):
    """Fetch Pokemon data from PokeAPI for specified generations."""
    
    def execute(self, context: PipelineContext, params: Dict[str, Any]) -> PipelineContext:
        """
        Execute the fetch step.
        
        Args:
            context: Pipeline context
            params: Step parameters with 'generations' list
        
        Returns:
            Updated context with fetched Pokemon data
        """
        generations = params.get('generations', [1])
        limit = params.get('limit')  # Optional: limit per generation for testing
        
        print(f"    🔍 Fetching from PokeAPI")
        print(f"    📊 Generations: {generations}")
        if limit:
            print(f"    ⚠️  Limit: {limit} per generation (test mode)")
        
        # Collect all Pokemon IDs to fetch
        pokemon_ids = []
        for gen in generations:
            if gen not in GENERATION_RANGES:
                print(f"    ⚠️  Unknown generation: {gen}, skipping")
                continue
            
            start, end, region = GENERATION_RANGES[gen]
            if limit:
                end = min(start + limit - 1, end)
            
            pokemon_ids.extend(range(start, end + 1))
        
        print(f"    📝 Total Pokemon to fetch: {len(pokemon_ids)}")
        
        # Fetch data
        api_client = PokéAPIClient()
        pokemon_data = []
        failed = []
        
        for i, pokemon_id in enumerate(pokemon_ids, 1):
            # Progress indicator
            if i % 10 == 0 or i == len(pokemon_ids):
                print(f"    Progress: {i}/{len(pokemon_ids)}", end='\r')
            
            # Fetch species data (names, generation)
            species = api_client.fetch_species_data(pokemon_id)
            if not species:
                failed.append(pokemon_id)
                continue
            
            # Fetch pokemon data (types, sprites)
            pokemon = api_client.fetch_pokemon_data(pokemon_id)
            if not pokemon:
                failed.append(pokemon_id)
                continue
            
            # Combine data in source format (minimal)
            # Generation: 'generation-i' -> 1, 'generation-ii' -> 2, etc.
            gen_name = species['generation']['name']
            gen_map = {'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5, 'vi': 6, 'vii': 7, 'viii': 8, 'ix': 9}
            gen_roman = gen_name.split('-')[-1]
            generation = gen_map.get(gen_roman, 1)
            
            entry = {
                'id': pokemon_id,
                'name': species['name'],
                'names': species['names'],
                'types': [t['type']['name'] for t in pokemon['types']],
                'image_url': pokemon['sprites']['other']['official-artwork']['front_default'],
                'generation': generation,
                'is_legendary': species.get('is_legendary', False),
                'is_mythical': species.get('is_mythical', False),
            }
            
            pokemon_data.append(entry)
        
        print(f"    Progress: {len(pokemon_ids)}/{len(pokemon_ids)}")  # Clear line
        
        if failed:
            print(f"    ⚠️  Failed to fetch: {len(failed)} Pokemon")
        
        print(f"    ✅ Fetched: {len(pokemon_data)} Pokemon")
        
        # Store in context
        context.set_data({'pokemon': pokemon_data})
        context.set_metadata('total_pokemon', len(pokemon_data))
        context.set_metadata('failed_ids', failed)
        
        # Save to output file if specified
        output_file = params.get('output_file')
        if output_file:
            # Make path absolute relative to project root
            project_root = Path(__file__).parent.parent.parent.parent
            if not Path(output_file).is_absolute():
                output_path = project_root / output_file
            else:
                output_path = Path(output_file)
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({'pokemon': pokemon_data}, f, indent=2, ensure_ascii=False)
            
            print(f"    💾 Saved to: {output_file}")
        
        return context
