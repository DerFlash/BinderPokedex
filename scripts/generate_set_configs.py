#!/usr/bin/env python3
"""
Auto-generate YAML config files for TCG sets

This script discovers all available TCG sets from the TCGdex API and generates
corresponding YAML configuration files in config/scopes/.

Features:
- Discovers all sets via TCGdex API
- Filters by series (e.g., only 'sv' or 'me' sets)
- Generates standardized YAML configs
- Skips existing configs (use --overwrite to update)
- Dry-run mode to preview changes

Usage:
    # Generate configs for all sets
    python scripts/generate_set_configs.py
    
    # Only Scarlet & Violet series
    python scripts/generate_set_configs.py --series sv
    
    # Preview without writing files
    python scripts/generate_set_configs.py --dry-run
    
    # Overwrite existing configs
    python scripts/generate_set_configs.py --overwrite
    
    # Specific sets only
    python scripts/generate_set_configs.py --sets sv01 sv02 me01
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add fetcher directory to path
sys.path.insert(0, str(Path(__file__).parent / 'fetcher'))

from lib.tcgdex_client import TCGdexClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


YAML_TEMPLATE = """# TCG Set: {set_name} ({set_id})
#
# Fetches the complete {set_id} "{set_name_de}" / "{set_name_en}" set
# from TCGdex API and transforms it to target format for PDF generation.
#
# This is a COMPLETE SET (not a variant), including:
# - All Pokemon cards
# - Trainer cards
# - Energy cards
#
# Pipeline Architecture:
# - fetch_tcgdex_set → writes raw data to data/source/{set_id}.json
# - transform_tcg_set → maps cards to Pokemon, writes to data/{SCOPE}.json
# - cache_pokemon_images → downloads sprites for all Pokemon
# - save_output → final save (already done by transform)
#
# Set Info:
# - ID: {set_id}
# - Name: {set_name_de} (DE) / {set_name_en} (EN)
# - Release: {release_date}
# - Series: {serie_name} ({serie_id})
# - Cards: {card_count}
#
# Auto-generated: {generated_date}

scope: {SCOPE}
description: "TCG Set: {set_name_en} ({set_id}) - Complete set with all cards"
target_file: data/{SCOPE}.json

pipeline:
  # Step 1: Validate that Pokedex exists (required for Pokemon name mapping)
  - step: validate_pokedex_exists
    params:
      pokedex_file: data/output/Pokedex.json

  # Step 2: Fetch set data from TCGdex API (English only - master language)
  - step: fetch_tcgdex_set
    params:
      set_id: {set_id}
      output_file: data/source/{set_id}.json

  # Step 3: Enrich with multilingual names from TCGdex (9 API calls, one per language)
  - step: enrich_tcg_names_multilingual
    params:
      set_id: {set_id}
      input_file: data/source/{set_id}.json

  # Step 4: Enrich cards with Pokemon IDs and types from Pokedex
  - step: enrich_tcg_cards_from_pokedex
    params:
      input_file: data/source/{set_id}.json
      pokedex_file: data/output/Pokedex.json

  # Step 5: Enrich special cards with generic type images
  - step: enrich_special_cards
    params:
      input_file: data/source/{set_id}.json
      images_dir: images/special_cards

  # Step 6: Transform to target format
  - step: transform_tcg_set
    params:
      set_id: {SCOPE}
      source_file: data/source/{set_id}.json
      output_file: data/{SCOPE}.json

  # Step 7: Transform to sections format for PDF generation
  - step: transform_to_sections_format
    params:
      input_file: data/{SCOPE}.json

  # Step 8: Cache Pokemon images
  - step: cache_pokemon_images
    params:
      cache_dir: data/pokemon_images_cache
      skip_existing: true
"""


class SetConfigGenerator:
    """Generator for TCG set YAML configurations."""
    
    def __init__(self, dry_run: bool = False, overwrite: bool = False):
        """
        Initialize the generator.
        
        Args:
            dry_run: If True, don't write files, just preview
            overwrite: If True, overwrite existing configs
        """
        self.dry_run = dry_run
        self.overwrite = overwrite
        self.client = TCGdexClient(language='en')
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / 'config' / 'scopes'
        
    def fetch_all_sets(self) -> List[Dict[str, Any]]:
        """
        Fetch all available sets from TCGdex API.
        
        Returns:
            List of set objects with id, name, serie, etc.
        """
        logger.info("🔍 Discovering available TCG sets...")
        
        # TCGdex returns all sets in a single request (no pagination)
        # Don't pass limit parameter - API doesn't support it for /sets endpoint
        sets = self.client.get_sets()
        
        if sets is None:
            logger.error("❌ API request returned None - check network connection")
            return []
        
        if not isinstance(sets, list):
            logger.error(f"❌ Unexpected response type: {type(sets)}")
            return []
        
        logger.info(f"✅ Discovered {len(sets)} total sets")
        return sets
    
    def filter_sets(self, 
                   sets: List[Dict[str, Any]], 
                   series: Optional[List[str]] = None,
                   set_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Filter sets by series or specific IDs.
        
        Args:
            sets: All available sets
            series: List of series IDs to include (e.g., ['sv', 'me'])
            set_ids: List of specific set IDs to include
            
        Returns:
            Filtered list of sets
        """
        filtered = sets
        
        if series:
            # Extract series from logo URL (e.g., 'https://assets.tcgdex.net/en/me/me01/logo')
            # Series ID is the path segment before set ID
            def get_serie_from_set(s: Dict[str, Any]) -> Optional[str]:
                logo = s.get('logo', '')
                if logo:
                    parts = logo.split('/')
                    if len(parts) >= 3:
                        return parts[-3]  # e.g., 'me' from [.../me/me01/logo]
                # Fallback: extract from set_id (e.g., 'sv01' → 'sv', 'me01' → 'me')
                set_id = s.get('id', '')
                for prefix in series:
                    if set_id.startswith(prefix):
                        return prefix
                return None
            
            filtered = [s for s in filtered if get_serie_from_set(s) in series]
            logger.info(f"🔽 Filtered to series: {', '.join(series)} ({len(filtered)} sets)")
        
        if set_ids:
            filtered = [s for s in filtered if s.get('id') in set_ids]
            logger.info(f"🔽 Filtered to specific sets: {', '.join(set_ids)} ({len(filtered)} sets)")
        
        return filtered
    
    def get_set_details(self, set_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed information for a specific set.
        
        Args:
            set_id: Set ID (e.g., 'sv01')
            
        Returns:
            Full set object with all metadata
        """
        return self.client.get_set(set_id)
    
    def generate_config(self, set_data: Dict[str, Any]) -> str:
        """
        Generate YAML config content for a set.
        
        Args:
            set_data: Set object from TCGdex API
            
        Returns:
            YAML config file content
        """
        set_id = set_data.get('id', 'unknown')
        scope = set_id.upper().replace('-', '_')
        
        # Get multilingual names
        set_name_en = set_data.get('name', 'Unknown Set')
        
        # Fetch German name from API
        client_de = TCGdexClient(language='de')
        set_data_de = client_de.get_set(set_id)
        set_name_de = set_data_de.get('name', set_name_en) if set_data_de else set_name_en
        
        # Extract metadata
        serie = set_data.get('serie', {})
        serie_id = serie.get('id', 'unknown')
        serie_name = serie.get('name', 'Unknown Series')
        
        release_date = set_data.get('releaseDate', 'Unknown')
        card_count = set_data.get('cardCount', {})
        total_cards = card_count.get('total', 0)
        
        # Generate config
        config = YAML_TEMPLATE.format(
            set_id=set_id,
            SCOPE=scope,
            set_name=set_name_en,
            set_name_en=set_name_en,
            set_name_de=set_name_de,
            serie_id=serie_id,
            serie_name=serie_name,
            release_date=release_date,
            card_count=total_cards,
            generated_date=datetime.now().strftime('%Y-%m-%d')
        )
        
        return config
    
    def write_config(self, set_id: str, content: str) -> bool:
        """
        Write config file to disk.
        
        Args:
            set_id: Set ID (e.g., 'sv01')
            content: YAML config content
            
        Returns:
            True if written, False if skipped
        """
        scope = set_id.upper().replace('-', '_')
        config_file = self.config_dir / f"{scope}.yaml"
        
        # Check if exists
        if config_file.exists() and not self.overwrite:
            logger.info(f"   ⏭️  Skipping {config_file.name} (already exists)")
            return False
        
        if self.dry_run:
            logger.info(f"   📄 Would write: {config_file.name}")
            return True
        
        # Write file
        config_file.write_text(content, encoding='utf-8')
        action = "Updated" if config_file.exists() else "Created"
        logger.info(f"   ✅ {action}: {config_file.name}")
        return True
    
    def generate_all(self, 
                    series: Optional[List[str]] = None,
                    set_ids: Optional[List[str]] = None) -> Dict[str, int]:
        """
        Generate configs for all matching sets.
        
        Args:
            series: Filter by series IDs
            set_ids: Filter by specific set IDs
            
        Returns:
            Statistics dict with counts
        """
        # Fetch all sets
        all_sets = self.fetch_all_sets()
        
        # Filter
        sets = self.filter_sets(all_sets, series=series, set_ids=set_ids)
        
        if not sets:
            logger.warning("⚠️  No sets match the filter criteria")
            return {'total': 0, 'written': 0, 'skipped': 0}
        
        logger.info(f"\n📝 Generating configs for {len(sets)} sets...\n")
        
        stats = {'total': len(sets), 'written': 0, 'skipped': 0}
        
        for i, set_brief in enumerate(sets, 1):
            set_id = set_brief.get('id')
            set_name = set_brief.get('name', 'Unknown')
            
            logger.info(f"[{i}/{len(sets)}] {set_id} - {set_name}")
            
            # Fetch full details
            set_data = self.get_set_details(set_id)
            if not set_data:
                logger.warning(f"   ⚠️  Failed to fetch details for {set_id}")
                stats['skipped'] += 1
                continue
            
            # Generate config
            config = self.generate_config(set_data)
            
            # Write to disk
            if self.write_config(set_id, config):
                stats['written'] += 1
            else:
                stats['skipped'] += 1
        
        return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Auto-generate YAML configs for TCG sets',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all sets
  python scripts/generate_set_configs.py
  
  # Only Scarlet & Violet series
  python scripts/generate_set_configs.py --series sv
  
  # Multiple series
  python scripts/generate_set_configs.py --series sv me
  
  # Specific sets
  python scripts/generate_set_configs.py --sets sv01 sv02 me01
  
  # Preview without writing
  python scripts/generate_set_configs.py --dry-run
  
  # Overwrite existing configs
  python scripts/generate_set_configs.py --overwrite --series me
        """
    )
    
    parser.add_argument(
        '--series',
        nargs='+',
        help='Filter by series IDs (e.g., sv, me, swsh)'
    )
    
    parser.add_argument(
        '--sets',
        nargs='+',
        help='Generate configs for specific set IDs only (e.g., sv01 me01)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without writing files'
    )
    
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing config files'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create generator
    generator = SetConfigGenerator(
        dry_run=args.dry_run,
        overwrite=args.overwrite
    )
    
    # Generate configs
    stats = generator.generate_all(
        series=args.series,
        set_ids=args.sets
    )
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("📊 Summary:")
    logger.info(f"   Total sets:    {stats['total']}")
    logger.info(f"   ✅ Written:    {stats['written']}")
    logger.info(f"   ⏭️  Skipped:    {stats['skipped']}")
    
    if args.dry_run:
        logger.info("\n💡 This was a dry-run. Run without --dry-run to write files.")
    
    logger.info("="*60)


if __name__ == '__main__':
    main()
