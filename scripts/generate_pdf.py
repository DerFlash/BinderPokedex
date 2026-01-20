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
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'lib'))

from lib.fonts import FontManager
from lib.pdf_generator import PDFGenerator
from lib.variant_pdf_generator import VariantPDFGenerator
from lib.constants import LANGUAGES, GENERATION_INFO, PAGE_WIDTH, PAGE_HEIGHT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_pokemon_name_for_language(pokemon: dict, language: str) -> str:
    """
    Get the Pokémon name for the specified language.
    
    Args:
        pokemon: Pokémon data dictionary
        language: Language code (de, en, ja, etc.)
    
    Returns:
        Pokémon name in the specified language
    """
    # Map language codes to JSON keys
    language_map = {
        'de': 'name_de',
        'en': 'name_en',
        'fr': 'name_fr',
        'es': 'name_es',
        'it': 'name_it',
        'ja': 'name_ja',
        'ko': 'name_ko',
        'zh_hans': 'name_zh_hans',
        'zh_hant': 'name_zh_hant',
    }
    
    key = language_map.get(language, 'name_en')
    return pokemon.get(key, pokemon.get('name_en', 'Unknown'))


def prepare_pokemon_data(pokemon_list: list, language: str, skip_images: bool = False) -> list:
    """
    Prepare Pokémon data for PDF generation.
    
    Args:
        pokemon_list: Raw Pokémon data from JSON
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
            'name_en': pokemon.get('name_en', 'Unknown'),  # Fallback
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


def generate_pdfs_for_generation(
    generation: int,
    language: str,
    data_dir: Path,
    skip_images: bool = True,
    test_mode: bool = False
) -> bool:
    """
    Generate PDFs for a specific generation in a specific language.
    
    Args:
        generation: Pokémon generation number (1-9)
        language: Language code
        data_dir: Path to data directory with pokemon_gen*.json files
        skip_images: If True, skip image download (for faster testing)
    
    Returns:
        True if successful, False otherwise
    """
    input_file = data_dir / f"pokemon_gen{generation}.json"
    
    if not input_file.exists():
        logger.warning(f"⏭️  Generation {generation}: Data file not found at {input_file}")
        return False
    
    gen_info = GENERATION_INFO[generation]
    start_id, end_id = gen_info['range']
    lang_name = LANGUAGES.get(language, {}).get('name', language.upper())
    
    print(f"\n{'=' * 80}")
    print(f"📊 Generation {generation} → {lang_name}")
    print(f"   Pokédex #{start_id:03d} - #{end_id:03d}")
    print(f"{'=' * 80}")
    
    try:
        # Load Pokémon data
        with open(input_file, 'r', encoding='utf-8') as f:
            pokemon_list = json.load(f)
        
        logger.info(f"📋 Loaded {len(pokemon_list)} Pokémon from {input_file.name}")
        
        # Test mode: use first 9 Pokémon + iconic Pokémon for cover display
        if test_mode:
            iconic_ids = gen_info.get('iconic_pokemon', [])
            # Keep first 9
            test_pokemon = pokemon_list[:9]
            # Add iconic Pokémon if not already included
            for iconic_id in iconic_ids:
                if iconic_id > 9:  # Only add if not in first 9
                    # Find and add the iconic Pokémon
                    iconic_pokemon = next((p for p in pokemon_list if int(p.get('id', p.get('num', '0').lstrip('#'))) == iconic_id), None)
                    if iconic_pokemon and iconic_pokemon not in test_pokemon:
                        test_pokemon.append(iconic_pokemon)
            pokemon_list = test_pokemon
            logger.info(f"🧪 Test mode: using first 9 + {len(iconic_ids)} iconic Pokémon = {len(pokemon_list)} total")
        
        # Prepare data for rendering
        prepared_data = prepare_pokemon_data(pokemon_list, language, skip_images=skip_images)
        logger.info(f"✅ Prepared {len(prepared_data)} Pokémon for rendering")
        
        # Create and run PDF generator
        generator = PDFGenerator(language, generation)
        pdf_path = generator.generate(prepared_data)
        
        # Summary
        file_size_mb = pdf_path.stat().st_size / 1024 / 1024
        logger.info(f"\n✅ PDF successfully created!")
        logger.info(f"   File: {pdf_path.name}")
        logger.info(f"   Size: {file_size_mb:.2f} MB")
        
        return True
    
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error parsing JSON from {input_file.name}: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error generating PDF for generation {generation}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Parse arguments and generate PDFs."""
    parser = argparse.ArgumentParser(
        description="Generate multi-language Pokémon binder PDFs with CJK support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all PDFs (generations + variants) for all languages
  python generate_pdf.py
  
  # Generate German PDFs for Gen 1
  python generate_pdf.py --type generation --language de --generation 1
  
  # Generate Japanese PDFs for Gen 1-3
  python generate_pdf.py --type generation --language ja --generation 1-3
  
  # Generate Mega Evolution variants in English
  python generate_pdf.py --type variant --variant mega --language en
  
  # Generate all variant categories for a language
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
        choices=["generation", "variant", "all"],
        help="Type of PDF to generate: 'generation', 'variant', or 'all' (default: all if no args provided)"
    )
    
    parser.add_argument(
        "--language",
        "-l",
        type=str,
        default=None,
        help="Language code (de, en, fr, es, it, ja, ko, zh-hans, zh-hant). If not specified, generates all languages."
    )
    
    parser.add_argument(
        "--generation",
        "-g",
        type=str,
        default="1-9",
        help="Generation(s) to generate: '1', '1-3', '1,3,5', or '1-9' (default: 1-9). Only for --type generation"
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
    
    args = parser.parse_args()
    
    # Get workspace directories
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    data_dir = project_dir / "data"
    variants_dir = data_dir / "variants"
    
    if not data_dir.exists():
        logger.error(f"❌ Data directory not found: {data_dir}")
        return 1
    
    # Determine generation mode if not specified
    if args.type is None:
        # Default: generate both if no args, or infer from other args
        if len(sys.argv) == 1:  # No arguments at all
            args.type = "all"
        else:
            # Check for variant-specific args
            if "--variant" in sys.argv or "--list" in sys.argv:
                args.type = "variant"
            else:
                args.type = "generation"
    
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
        # Generate both generations and variants
        result_gen = handle_generation_mode(args, script_dir, project_dir, data_dir)
        result_var = handle_variant_mode(args, script_dir, project_dir, data_dir, variants_dir)
        return result_gen | result_var  # 0 if both succeed, 1 if either fails
    elif args.type == "generation":
        return handle_generation_mode(args, script_dir, project_dir, data_dir)
    elif args.type == "variant":
        return handle_variant_mode(args, script_dir, project_dir, data_dir, variants_dir)
    else:
        logger.error(f"❌ Unknown type: {args.type}")
        return 1


def handle_generation_mode(args, script_dir, project_dir, data_dir):
    """Handle generation-based PDF generation."""
    # Validate and normalize language
    if args.language:
        if args.language not in LANGUAGES:
            logger.error(f"❌ Unsupported language: {args.language}")
            logger.info(f"   Supported: {', '.join(LANGUAGES.keys())}")
            return 1
        languages = [args.language]
    else:
        languages = list(LANGUAGES.keys())
    
    # Parse generation argument
    try:
        gen_str = args.generation.lower()
        generations = []
        
        if ',' in gen_str:
            # Comma-separated: 1,3,5
            generations = sorted(set(int(x.strip()) for x in gen_str.split(',')))
        elif '-' in gen_str:
            # Range: 1-5 or 1-9
            parts = gen_str.split('-')
            start = int(parts[0].strip())
            end = int(parts[1].strip())
            generations = list(range(start, end + 1))
        else:
            # Single: 1
            generations = [int(gen_str.strip())]
        
        # Validate
        valid_gens = set(GENERATION_INFO.keys())
        generations = [g for g in generations if g in valid_gens]
        if not generations:
            logger.error(f"❌ No valid generations specified")
            return 1
    
    except (ValueError, IndexError):
        logger.error(f"❌ Invalid generation format. Use: '1', '1-5', or '1,3,5'")
        return 1
    
    # Register fonts
    try:
        FontManager.register_fonts()
        logger.info("✅ Fonts registered successfully")
    except Exception as e:
        logger.error(f"❌ Failed to register fonts: {e}")
        return 1
    
    # Generate PDFs
    print(f"\n{'=' * 80}")
    print(f"PDF Generation - Pokédex (Generations)")
    print(f"{'=' * 80}")
    print(f"Generations: {', '.join(str(g) for g in generations)}")
    print(f"Languages:   {', '.join(languages)}")
    print(f"Output dir:  {project_dir / 'output'}")
    
    total_generated = 0
    total_failed = 0
    
    for language in languages:
        for generation in generations:
            success = generate_pdfs_for_generation(
                generation,
                language,
                data_dir,
                skip_images=args.skip_images,
                test_mode=args.test
            )
            if success:
                total_generated += 1
            else:
                total_failed += 1
    
    # Summary
    print(f"\n{'=' * 80}")
    print(f"Summary")
    print(f"{'=' * 80}")
    print(f"✅ Generated: {total_generated}")
    print(f"❌ Failed:    {total_failed}")
    print(f"{'=' * 80}\n")
    
    if total_failed == 0:
        logger.info("✅ All PDFs generated successfully!")
        return 0
    else:
        logger.warning(f"⚠️  {total_failed} PDFs failed to generate")
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
        # Default: generate all variants if not in mode where --variant is required
        if args.type == "variant":
            logger.error(f"❌ --variant argument required for --type variant")
            logger.info(f"   Use --variant mega|gigantamax|regional_alola|... or --variant all")
            logger.info(f"   Use --list to see all available variants")
            return 1
        else:
            # In "all" mode, generate all variants
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



if __name__ == "__main__":
    sys.exit(main())
