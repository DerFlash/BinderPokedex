#!/usr/bin/env python3
"""
BinderPokedex MCP Server

Exposes the Pokémon binder PDF generation as tools for Claude and other MCP clients.

Tools:
- generate_pdfs: Generate PDF binders for specified generations
- list_status: Show status of all generations
"""

import asyncio
import logging
import sys
import subprocess
import json
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

# Configure logging to stderr (not stdout which breaks MCP communication)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("BinderPokedex")

# Constants
GENERATIONS = {
    1: ("Kanto", 151),
    2: ("Johto", 100),
    3: ("Hoenn", 135),
    4: ("Sinnoh", 107),
    5: ("Unova", 156),
    6: ("Kalos", 72),
    7: ("Alola", 88),
    8: ("Galar", 96),
    9: ("Paldea", 0),
}


@mcp.tool()
async def generate_pdfs(
    generations: str = "1-8",
) -> dict[str, Any]:
    """
    Generate PDF binders for Pokémon collections.
    
    Args:
        generations: Comma-separated or range notation (e.g., "1", "1,3,5", "1-8", "all")
    
    Returns:
        Dictionary with status and results
    """
    logger.info(f"Starting PDF generation for generations: {generations}")
    
    try:
        # Determine which generations to generate
        if generations.lower() == "all":
            gen_list = list(range(1, 9))
        elif "-" in generations:
            parts = generations.split("-")
            start, end = int(parts[0].strip()), int(parts[1].strip())
            gen_list = list(range(start, end + 1))
        else:
            gen_list = [int(g.strip()) for g in generations.split(",")]
        
        # Validate generations (only 1-8 are available)
        gen_list = [g for g in gen_list if 1 <= g <= 8]
        if not gen_list:
            return {
                "success": False,
                "error": "Invalid generations. Valid options are: 1-8 or 'all'",
            }
        
        logger.info(f"Generating PDFs for generations: {gen_list}")
        
        # Run the generation script via subprocess
        project_root = Path(__file__).parent.parent
        script_path = project_root / "scripts" / "generate_pdf.py"
        
        # Run the script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=600,
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            return {
                "success": False,
                "error": f"PDF generation failed: {error_msg[:500]}",
            }
        
        # Check which files were created
        output_dir = project_root / "output"
        generated_files = {}
        for gen in gen_list:
            pdf_path = output_dir / f"BinderPokedex_Gen{gen}.pdf"
            if pdf_path.exists():
                size_mb = round(pdf_path.stat().st_size / (1024 * 1024), 2)
                generated_files[gen] = {
                    "file": f"BinderPokedex_Gen{gen}.pdf",
                    "size_mb": size_mb,
                    "region": GENERATIONS[gen][0],
                }
        
        logger.info(f"PDF generation completed: {generated_files}")
        return {
            "success": True,
            "generations_requested": gen_list,
            "files_generated": generated_files,
            "output_directory": "output/",
        }
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "PDF generation timed out (exceeded 10 minutes)",
        }
    except Exception as e:
        error_msg = f"PDF generation failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "error": error_msg,
        }


@mcp.tool()
async def list_status() -> dict[str, Any]:
    """
    List all available Pokémon generations with their current status.
    
    Returns:
        Dictionary with generation information and file status
    """
    logger.info("Listing generation status")
    
    try:
        project_root = Path(__file__).parent.parent
        output_dir = project_root / "output"
        data_dir = project_root / "data"
        
        generations = {}
        for gen_num, (region_name, pokemon_count) in GENERATIONS.items():
            pdf_path = output_dir / f"BinderPokedex_Gen{gen_num}.pdf"
            cache_path = data_dir / f"gen_{gen_num:02d}.json"
            
            info = {
                "region": region_name,
                "pokemon_count": pokemon_count,
                "pdf_generated": pdf_path.exists(),
                "data_cached": cache_path.exists(),
            }
            
            if pdf_path.exists():
                size_mb = round(pdf_path.stat().st_size / (1024 * 1024), 2)
                info["pdf_size_mb"] = size_mb
            
            generations[gen_num] = info
        
        # Count generated PDFs
        generated_count = sum(1 for g in generations.values() if g["pdf_generated"])
        
        return {
            "success": True,
            "total_generations": len(GENERATIONS),
            "generations_with_pdfs": generated_count,
            "generations": generations,
        }
    
    except Exception as e:
        error_msg = f"Failed to list status: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "error": error_msg,
        }


def main() -> None:
    """Main entry point for the MCP server."""
    logger.info("Starting BinderPokedex MCP Server")
    try:
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()


def main() -> None:
    """Main entry point for the MCP server."""
    logger.info("Starting BinderPokedex MCP Server")
    try:
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
