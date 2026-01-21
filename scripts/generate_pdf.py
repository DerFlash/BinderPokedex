#!/usr/bin/env python3
"""
Generate Pokémon Binder PDFs - New Clean Architecture Version

Supports multi-language output (DE, EN, FR, ES, IT, JA, KO, ZH-HANS, ZH-HANT).
Uses clean architecture with FontManager, TextRenderer, and PDFGenerator.

Features:
- CJK text rendering with Songti TrueType fonts
- Cover pages with generation info
- 3x3 card layout per page
- Multi-language support with proper character handling
- Clean, modular architecture (no monkey-patching)

Usage:
    python generate_pdf_new.py --language de --generation 1
    python generate_pdf_new.py --language ja --generation 1-3
    python generate_pdf_new.py --language en
"""

import json
import sys
import argparse
import logging
from pathlib import Path

# Check for required dependencies and provide helpful hint
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor
except ImportError as e:
    print("\n" + "=" * 80)
    print("❌ Missing Python Dependencies")
    print("=" * 80)
    print(f"\nError: {e}")
    print("\n💡 HINT: You need to activate the Python virtual environment first:")
    print("\n   source venv/bin/activate")
    print("\nOr run with the venv Python directly:")
    print("\n   ./venv/bin/python scripts/generate_pdf.py")
    print("\n" + "=" * 80 + "\n")
    sys.exit(1)

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'lib'))

from lib.fonts import FontManager
from lib.pdf_generator import PDFGenerator
from lib.variant_pdf_generator import VariantPDFGenerator
from lib.data_storage import DataStorage
from lib.log_formatter import BatchSummary, SectionHeader
from lib.constants import LANGUAGES, PAGE_WIDTH, PAGE_HEIGHT

# Configure logging - suppress INFO during generation for clean output
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s: %(message)s'
)

# Suppress ReportLab font rendering warnings for known unsupported characters
# These are expected when rendering CJK text with limited font support
logging.getLogger('reportlab.pdfbase.ttfonts').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)


def get_pokemon_name_for_language(pokemon: dict, language: str) -> str:
    """
    Get the Pokémon name for the specified language.
    
    Args:
        pokemon: Pokémon data dictionary (must have 'name' as multilingual object)
        language: Language code (de, en, ja, etc.)
    
    Returns:
        Pokémon name in the specified language
    """
    return pokemon['name'].get(language, pokemon['name'].get('en', 'Unknown'))


def prepare_pokemon_data(pokemon_list: list, language: str, skip_images: bool = False) -> list:
    """
    Prepare Pokémon data for PDF generation.
    
    Args:
        pokemon_list: Raw Pokémon data from JSON (must have unified name object structure)
        language: Target language code
        skip_images: If True, don't include image_url in prepared data
    
    Returns:
        List of prepared Pokémon dictionaries for rendering
    """
    prepared = []
    
    for pokemon in pokemon_list:
        prepared_pokemon = {
            'id': pokemon.get('id'),  # Numeric ID for image cache lookup
            'num': pokemon.get('num', '#???'),
            'name': get_pokemon_name_for_language(pokemon, language),
            'name_en': pokemon['name']['en'],  # English name for subtitle
            'types': [pokemon.get('type1', 'Normal')],
            'generation': pokemon.get('generation', 1),
        }
        
        # Only include image_url if images are enabled
        if not skip_images:
            prepared_pokemon['image_url'] = pokemon.get('image_url')
        
        # Add second type if available
        if pokemon.get('type2'):
            prepared_pokemon['types'].append(pokemon['type2'])
        
        prepared.append(prepared_pokemon)
    
    return prepared




def main():
    """Parse arguments and generate PDFs."""
    parser = argparse.ArgumentParser(
        description="Generate multi-language Pokémon binder PDFs with CJK support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all PDFs (consolidated pokedex + variants) for all languages
  python generate_pdf.py
  
  # Generate German consolidated Pokédex
  python generate_pdf.py --type pokedex --language de
  
  # Generate Japanese consolidated Pokédex for Gen 1-3 only
  python generate_pdf.py --type pokedex --language ja --generations 1-3
  
  # Generate Mega Evolution variants in English
  python generate_pdf.py --type variant --variant mega --language en
  
  # Generate all variant categories for German
  python generate_pdf.py --type variant --variant all --language de
  
  # List available variants
  python generate_pdf.py --type variant --list
        """
    )
    
    parser.add_argument(
        "--type",
        "-t",
        type=str,
        default=None,
        choices=["pokedex", "variant", "all"],
        help="Type of PDF to generate: 'pokedex' (consolidated Pokédex), 'variant' (themed collections), or 'all'"
    )
    
    parser.add_argument(
        "--language",
        "-l",
        type=str,
        default=None,
        help="Language code (de, en, fr, es, it, ja, ko, zh-hans, zh-hant). If not specified, generates all languages."
    )
    
    parser.add_argument(
        "--generations",
        type=str,
        default="1-9",
        help="Generation(s) for pokedex mode: '1', '1-2', '1-5', etc. Default: 1-9. Only for --type pokedex"
    )
    
    parser.add_argument(
        "--variant",
        "-v",
        type=str,
        default=None,
        help="Variant category(s) to generate: 'mega', 'gigantamax', 'regional_alola', 'regional_galar', 'regional_hisui', 'regional_paldea', 'primal_terastal', 'patterns_unique', 'fusion_special', or 'all'. Only for --type variant"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        default=False,
        help="List all available variants and their status"
    )
    
    parser.add_argument(
        "--skip-images",
        action="store_true",
        default=False,
        help="Skip image processing (faster for testing)"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        default=False,
        help="Test mode: only use 9 Pokémon for faster generation"
    )
    
    parser.add_argument(
        "--verbose",
        "-vv",
        action="store_true",
        default=False,
        help="Verbose mode: show detailed logs during generation"
    )
    
    args = parser.parse_args()
    
    # Configure logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
        logging.getLogger().handlers[0].setFormatter(
            logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        )
    
    # Get workspace directories
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    data_dir = project_dir / "data"
    variants_dir = data_dir / "variants"
    
    if not data_dir.exists():
        logger.error(f"❌ Data directory not found: {data_dir}")
        return 1
    
    # Determine mode if not specified
    if args.type is None:
        # Default: if ONLY --language is specified, generate everything
        # Otherwise, default to pokedex mode
        type_specified = "--type" in sys.argv
        variant_specified = "--variant" in sys.argv
        generations_specified = "--generations" in sys.argv
        list_specified = "--list" in sys.argv
        
        if len(sys.argv) == 1:
            # No arguments at all
            args.type = "all"  # Generate everything: pokedex + variants
        elif not type_specified and not variant_specified and not generations_specified and not list_specified:
            # Only --language or no type-related args -> generate all
            args.type = "all"
        elif variant_specified or list_specified:
            # Variant-specific arguments
            args.type = "variant"
        else:
            # Default to consolidated pokedex
            args.type = "pokedex"
    
    # Handle --list for variants
    if args.list and args.type in ["variant", "all"]:
        if not variants_dir.exists():
            logger.error(f"❌ Variants directory not found: {variants_dir}")
            return 1
        
        meta_file = variants_dir / "meta.json"
        if not meta_file.exists():
            logger.error(f"❌ Variants metadata not found: {meta_file}")
            return 1
        
        with open(meta_file, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        
        print(f"\n{'=' * 80}")
        print(f"Available Pokémon Variant Categories")
        print(f"{'=' * 80}")
        
        for cat in meta['variant_categories']:
            status_icon = "🟢" if cat['status'] == 'complete' else "🟡" if cat['status'] == 'in-progress' else "⚪"
            print(f"{status_icon} {cat['id']:20s} | {cat['pokemon_count']:3d} Pokémon, {cat['forms_count']:3d} Forms | {cat['icon']} {cat.get('short_code', 'N/A')}")
        
        print(f"\n{meta['statistics']['total_categories']} categories | {meta['statistics']['total_pokemon']} Pokémon | {meta['statistics']['total_forms']} Forms")
        print(f"{'=' * 80}\n")
        return 0
    
    # Route based on type
    if args.type == "all":
        # Generate all types: consolidated pokedex + variants
        result_con = handle_pokedex_mode(args, script_dir, project_dir, data_dir)
        result_var = handle_variant_mode(args, script_dir, project_dir, data_dir, variants_dir)
        return result_con | result_var  # 0 if all succeed, 1 if any fails
    elif args.type == "pokedex":
        return handle_pokedex_mode(args, script_dir, project_dir, data_dir)
    elif args.type == "variant":
        return handle_variant_mode(args, script_dir, project_dir, data_dir, variants_dir)
    else:
        logger.error(f"❌ Unknown type: {args.type}")
        return 1




def handle_variant_mode(args, script_dir, project_dir, data_dir, variants_dir):
    """Handle variant-based PDF generation."""
    # Validate variant directory
    if not variants_dir.exists():
        logger.error(f"❌ Variants directory not found: {variants_dir}")
        logger.info(f"   Please run Phase 1 setup first to create variant infrastructure")
        return 1
    
    meta_file = variants_dir / "meta.json"
    if not meta_file.exists():
        logger.error(f"❌ Variants metadata not found: {meta_file}")
        return 1
    
    # Load variant metadata
    with open(meta_file, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    # Determine which variants to generate
    if args.variant is None:
        # Default: generate all variants
        variants_to_generate = [cat['id'] for cat in meta['variant_categories']]
    elif args.variant.lower() == 'all':
        variants_to_generate = [cat['id'] for cat in meta['variant_categories']]
    else:
        # Parse comma-separated list
        variant_ids = [v.strip() for v in args.variant.lower().split(',')]
        valid_ids = {cat['id'] for cat in meta['variant_categories']}
        
        variants_to_generate = []
        for vid in variant_ids:
            if vid not in valid_ids:
                logger.error(f"❌ Unknown variant: {vid}")
                logger.info(f"   Valid variants: {', '.join(sorted(valid_ids))}")
                return 1
            variants_to_generate.append(vid)
    
    # Validate language
    if args.language:
        if args.language not in LANGUAGES:
            logger.error(f"❌ Unsupported language: {args.language}")
            logger.info(f"   Supported: {', '.join(LANGUAGES.keys())}")
            return 1
        languages = [args.language]
    else:
        languages = list(LANGUAGES.keys())
    
    # Register fonts
    try:
        FontManager.register_fonts()
        logger.info("✅ Fonts registered successfully")
    except Exception as e:
        logger.error(f"❌ Failed to register fonts: {e}")
        return 1
    
    # Generate variant PDFs
    print(f"\n{'=' * 80}")
    print(f"PDF Generation - Pokémon Variants (v3.0)")
    print(f"{'=' * 80}")
    print(f"Variants:  {', '.join(variants_to_generate)}")
    print(f"Languages: {', '.join(languages)}")
    print(f"Output dir: {project_dir / 'output'}")
    print(f"Data dir:  {variants_dir}")
    
    total_generated = 0
    total_failed = 0
    
    for variant_id in variants_to_generate:
        variant_meta = next((cat for cat in meta['variant_categories'] if cat['id'] == variant_id), None)
        if not variant_meta:
            logger.error(f"❌ Variant metadata not found: {variant_id}")
            total_failed += 1
            continue
        
        variant_file = variants_dir / variant_meta['json_file']
        
        if not variant_file.exists():
            logger.warning(f"⏭️  Variant not yet implemented: {variant_id} (file: {variant_file.name})")
            continue
        
        for language in languages:
            try:
                logger.info(f"\n📊 Generating {variant_id} → {LANGUAGES.get(language, {}).get('name', language.upper())}")
                
                # Load variant data
                with open(variant_file, 'r', encoding='utf-8') as f:
                    variant_data = json.load(f)
                
                # Generate PDF
                _generate_variant_pdf(
                    variant_data=variant_data,
                    language=language,
                    output_dir=project_dir / 'output' / language,
                    script_dir=script_dir
                )
                
                total_generated += 1
                logger.info(f"   ✅ Generated: {variant_id}_{language}.pdf")
            except Exception as e:
                logger.error(f"❌ Error generating variant PDF: {e}")
                total_failed += 1
    
    # Summary
    print(f"\n{'=' * 80}")
    print(f"Summary")
    print(f"{'=' * 80}")
    print(f"✅ Generated: {total_generated}")
    print(f"❌ Failed:    {total_failed}")
    print(f"{'=' * 80}\n")
    
    return 0 if total_failed == 0 else 1


def _generate_variant_pdf(variant_data, language, output_dir, script_dir):
    """Generate a PDF for a variant category."""
    from lib.pdf_generator import ImageCache
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract variant info
    variant_type = variant_data.get('variant', variant_data.get('variant_type', 'unknown'))
    
    # Generate output filename
    output_file = output_dir / f"Variant_{variant_type}_{language.upper()}.pdf"
    
    # Initialize image cache for loading Pokémon images
    image_cache = ImageCache()
    
    # Create and generate PDF
    pdf_gen = VariantPDFGenerator(
        variant_data=variant_data,
        language=language,
        output_file=output_file,
        image_cache=image_cache
    )
    
    return pdf_gen.generate()


def handle_pokedex_mode(args, script_dir, project_dir, data_dir):
    """Handle Pokédex PDF generation."""
    from lib.pdf_generator import ImageCache
    from lib.pokedex_generator import PokedexGenerator
    
    # Parse generation range
    gen_range = args.generations.split('-')
    try:
        gen_start = int(gen_range[0])
        gen_end = int(gen_range[1]) if len(gen_range) > 1 else gen_start
    except (ValueError, IndexError):
        logger.error(f"❌ Invalid generation range: {args.generations}")
        return 1
    
    generations = list(range(gen_start, min(gen_end + 1, 10)))  # Cap at 9
    
    # Validate and normalize language
    if args.language:
        if args.language not in LANGUAGES:
            logger.error(f"❌ Unsupported language: {args.language}")
            logger.info(f"   Supported: {', '.join(LANGUAGES.keys())}")
            return 1
        languages = [args.language]
    else:
        languages = list(LANGUAGES.keys())
    
    # Register fonts
    try:
        FontManager.register_fonts()
        logger.info("✅ Fonts registered successfully")
    except Exception as e:
        logger.error(f"❌ Failed to register fonts: {e}")
        return 1
    
    # Generate PDFs
    gen_label = f"Gen {gen_start}-{gen_end}" if gen_start != gen_end else f"Gen {gen_start}"
    print(f"\n{'=' * 80}")
    print(f"PDF Generation - Pokédex ({gen_label})")
    print(f"{'=' * 80}")
    print(f"Languages:   {', '.join(languages)}")
    print(f"Generations: {', '.join(map(str, generations))}")
    print(f"Output dir:  {project_dir / 'output'}")
    
    total_generated = 0
    total_failed = 0
    
    for language in languages:
        try:
            output_dir = project_dir / 'output' / language
            output_dir.mkdir(parents=True, exist_ok=True)
            
            if gen_start == gen_end:
                output_file = output_dir / f"Pokedex_Gen{gen_start}_{language.upper()}.pdf"
            else:
                output_file = output_dir / f"Pokedex_Gen{gen_start}-{gen_end}_{language.upper()}.pdf"
            
            lang_name = LANGUAGES.get(language, {}).get('name', language.upper())
            logger.info(f"\n📊 Generating Pokédex {gen_label} → {lang_name}")
            
            # Initialize image cache
            image_cache = ImageCache()
            
            # Create and generate Pokédex PDF
            pdf_gen = PokedexGenerator(
                language=language,
                output_file=output_file,
                image_cache=image_cache,
                generations=generations
            )
            
            if pdf_gen.generate():
                total_generated += 1
                logger.info(f"   ✅ Generated: {output_file.name}")
            else:
                total_failed += 1
                logger.error(f"   ❌ Failed to generate Pokédex")
        
        except Exception as e:
            logger.error(f"❌ Error generating Pokédex: {e}")
            import traceback
            traceback.print_exc()
            total_failed += 1
    
    # Summary
    print(f"\n{'=' * 80}")
    print(f"Summary")
    print(f"{'=' * 80}")
    print(f"✅ Generated: {total_generated}")
    print(f"❌ Failed:    {total_failed}")
    print(f"{'=' * 80}\n")
    
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
