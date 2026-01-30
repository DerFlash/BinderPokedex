#!/usr/bin/env python3
"""
Fetch and process Pokémon data using a pipeline configuration.

This script loads a scope configuration and executes the defined pipeline
to fetch, enrich, and transform Pokémon data.

Usage:
    python scripts/fetch.py --scope pokedex
    python scripts/fetch.py --scope pokedex --dry-run
"""

import argparse
import sys
import yaml
from pathlib import Path

# Add parent directory to path for lib imports
sys.path.insert(0, str(Path(__file__).parent))

from engine import PipelineEngine, StepRegistry
from steps.fetch_pokeapi_national_dex import FetchPokeAPIStep
from steps.group_by_generation import GroupByGenerationStep
from steps.enrich_featured_pokemon import EnrichFeaturedPokemonStep
from steps.enrich_metadata import EnrichMetadataStep
from steps.enrich_translations_es_it import EnrichTranslationsESITStep
from steps.fetch_tcgdex_ex_gen1 import FetchTCGdexClassicExStep
from steps.transform_ex_gen1 import TransformClassicExStep
from steps.validate_pokedex_exists import ValidatePokedexExistsStep
from steps.enrich_names_from_pokedex import EnrichNamesFromPokedexStep
from steps.enrich_section_descriptions import EnrichSectionDescriptionsStep
from steps.cache_pokemon_images import CachePokemonImages
from steps.fetch_tcgdex_ex_gen2 import FetchTCGdexBlackWhiteEXStep
from steps.fetch_tcgdex_ex_gen3 import FetchTCGdexScarletVioletEXStep
from steps.transform_ex_gen2 import TransformBlackWhiteEXStep
from steps.transform_ex_gen3 import TransformScarletVioletEXStep
from steps.save_output import SaveOutputStep


def load_config(scope: str) -> dict:
    """Load scope configuration from YAML file."""
    # Look in root config directory
    config_path = Path(__file__).parent.parent.parent / "config" / "scopes" / f"{scope}.yaml"
    
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def validate_config(config: dict) -> bool:
    """Validate the configuration structure."""
    required_fields = ['scope', 'pipeline', 'target_file']
    
    for field in required_fields:
        if field not in config:
            print(f"❌ Missing required field in config: {field}")
            return False
    
    if not isinstance(config['pipeline'], list):
        print(f"❌ Pipeline must be a list of steps")
        return False
    
    return True


def create_registry() -> StepRegistry:
    """Create and populate the step registry with all available steps."""
    registry = StepRegistry()
    
    # Register PokeAPI steps
    registry.register('fetch_pokeapi_national_dex', FetchPokeAPIStep)
    registry.register('group_by_generation', GroupByGenerationStep)
    registry.register('enrich_featured_pokemon', EnrichFeaturedPokemonStep)
    registry.register('enrich_translations_es_it', EnrichTranslationsESITStep)
    
    # Register enrichment steps
    registry.register('enrich_metadata', EnrichMetadataStep)
    registry.register('enrich_section_descriptions', EnrichSectionDescriptionsStep)
    
    # Register TCG steps
    registry.register('fetch_tcgdex_ex_gen1', FetchTCGdexClassicExStep)
    registry.register('transform_ex_gen1', TransformClassicExStep)
    registry.register('fetch_tcgdex_ex_gen2', FetchTCGdexBlackWhiteEXStep)
    registry.register('transform_ex_gen2', TransformBlackWhiteEXStep)
    registry.register('fetch_tcgdex_ex_gen3', FetchTCGdexScarletVioletEXStep)
    registry.register('transform_ex_gen3', TransformScarletVioletEXStep)
    registry.register('validate_pokedex_exists', ValidatePokedexExistsStep)
    registry.register('enrich_names_from_pokedex', EnrichNamesFromPokedexStep)
    
    # Register caching steps
    registry.register('cache_pokemon_images', CachePokemonImages)
    
    # Register utility steps
    registry.register('save_output', SaveOutputStep)
    
    # TODO: Register more steps as they are implemented
    # registry.register('enrich_from_pokeapi', EnrichPokeAPIStep)
    # etc.
    
    return registry


def main():
    parser = argparse.ArgumentParser(description='Fetch Pokémon data using pipeline')
    parser.add_argument('--scope', required=True, help='Scope name (e.g., pokedex)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    parser.add_argument('--limit', type=int, help='Limit Pokemon per generation (test mode)')
    parser.add_argument('--generations', type=str, help='Comma-separated list of generations (e.g., 1,2,3)')
    
    args = parser.parse_args()
    
    # Load and validate config
    print(f"📋 Loading scope: {args.scope}")
    config = load_config(args.scope)
    
    if not validate_config(config):
        sys.exit(1)
    
    # Apply CLI overrides to config
    if args.limit or args.generations:
        print(f"🔧 Applying CLI overrides:")
        if args.limit:
            print(f"   --limit {args.limit}")
        if args.generations:
            print(f"   --generations {args.generations}")
        
        # Apply overrides to relevant steps
        for step_config in config['pipeline']:
            step_name = step_config['step']
            params = step_config.get('params', {})
            
            # Apply limit to fetch steps
            if args.limit and 'fetch' in step_name:
                params['limit'] = args.limit
            
            # Apply generations to PokeAPI fetch
            if args.generations and step_name == 'fetch_pokeapi_national_dex':
                gens = [int(g.strip()) for g in args.generations.split(',')]
                params['generations'] = gens
            
            step_config['params'] = params
    
    print(f"✅ Config loaded: {config['description']}")
    if 'source_file' in config:
        print(f"📁 Source: {config['source_file']}")
    print(f"📁 Target: {config['target_file']}")
    print(f"🔧 Pipeline steps: {len(config['pipeline'])}")
    
    # Show pipeline
    print("\n📋 Pipeline:")
    for i, step in enumerate(config['pipeline'], 1):
        step_name = step['step']
        params = step.get('params', {})
        param_str = f" with {len(params)} params" if params else ""
        print(f"  {i}. {step_name}{param_str}")
    
    if args.dry_run:
        print("\n🏃 Dry run mode - not executing")
        return
    
    # Create step registry and pipeline engine
    registry = create_registry()
    engine = PipelineEngine(config, registry)
    
    # Execute pipeline
    success = engine.execute()
    
    if not success:
        print("\n❌ Pipeline failed")
        sys.exit(1)
    
    print(f"\n✅ Pipeline completed successfully!")
    print(f"📄 Output written to: {config['target_file']}")


if __name__ == '__main__':
    main()
