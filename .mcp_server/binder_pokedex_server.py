#!/usr/bin/env python3
"""
Binder Pokédex MCP Server

Exposes the Pokémon binder PDF generation as tools for Claude and other MCP clients.

Tools:
- generate_pdfs: Generate PDF binders for specified scope (Pokedex, ExGen1_All, ExGen1_Single, etc.)
- list_status: Show status of all available scopes
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

# Suppress ReportLab font rendering warnings for known unsupported characters
logging.getLogger('reportlab.pdfbase.ttfonts').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("BinderPokedex")

# Scope name mapping: Unified name -> (fetch_config, data_file)
# This allows using the same scope name for both fetch and generate operations
# Since configs now use unified names, fetch_config and data_file are the same
SCOPE_MAPPING = {
    "Pokedex": {"fetch_config": "Pokedex", "data_file": "Pokedex"},
    "ExGen1_All": {"fetch_config": "ExGen1_All", "data_file": "ExGen1_All"},
    "ExGen1_Single": {"fetch_config": "ExGen1_Single", "data_file": "ExGen1_Single"},
}

# Also allow lowercase variants for convenience
for scope in list(SCOPE_MAPPING.keys()):
    lower = scope.lower()
    if lower not in SCOPE_MAPPING:
        SCOPE_MAPPING[lower] = SCOPE_MAPPING[scope]


@mcp.tool()
async def generate_pdfs(
    scope: str = "Pokedex",
    language: str = "en",
) -> dict[str, Any]:
    """
    Generate PDF binders for Pokémon collections.
    
    Args:
        scope: Scope name (e.g., "Pokedex", "ExGen1_All", "ExGen1_Single"). Corresponds to JSON files in data/ folder.
        language: Language code (de, en, fr, es, it, ja, ko, zh_hans, zh_hant). Default: en
    
    Returns:
        Dictionary with status and results
    """
    logger.info(f"Starting PDF generation for scope: {scope}, language: {language}")
    
    try:
        # Normalize scope name using mapping
        scope_info = SCOPE_MAPPING.get(scope) or SCOPE_MAPPING.get(scope.lower())
        if not scope_info:
            return {
                "success": False,
                "error": f"Scope '{scope}' not found. Available scopes: {', '.join(SCOPE_MAPPING.keys())}",
            }
        
        data_file = scope_info["data_file"]
        
        # Run the generation script via subprocess
        project_root = Path(__file__).parent.parent
        script_path = project_root / "scripts" / "pdf" / "generate_pdf.py"
        
        # Verify scope file exists
        scope_file = project_root / "data" / f"{data_file}.json"
        if not scope_file.exists():
            return {
                "success": False,
                "error": f"Data file '{data_file}.json' not found. Run fetch_data first.",
            }
        
        # Run the script with scope and language parameter
        result = subprocess.run(
            [sys.executable, str(script_path), "--scope", data_file, "--language", language],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=900,
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            return {
                "success": False,
                "error": f"PDF generation failed: {error_msg[:500]}",
            }
        
        # Check which files were created
        output_dir = project_root / "output" / language
        pdf_files = list(output_dir.glob(f"*{scope}*.pdf"))
        
        generated_files = []
        for pdf_path in pdf_files:
            if pdf_path.exists():
                size_kb = round(pdf_path.stat().st_size / 1024, 1)
                generated_files.append({
                    "file": f"{language}/{pdf_path.name}",
                    "size_kb": size_kb,
                    "scope": scope,
                    "language": language,
                })
        
        logger.info(f"PDF generation completed: {len(generated_files)} file(s)")
        return {
            "success": True,
            "scope": scope,
            "language": language,
            "files_generated": generated_files,
            "output_directory": f"output/{language}/",
        }
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "PDF generation timed out (exceeded 15 minutes)",
        }
    except Exception as e:
        error_msg = f"PDF generation failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "error": error_msg,
        }


@mcp.tool()
async def fetch_data(
    scope: str = "pokedex",
) -> dict[str, Any]:
    """
    Fetch Pokémon data from external APIs using the pipeline system.
    
    Args:
        scope: Scope name (e.g., "pokedex", "tcg_classic_ex"). Corresponds to YAML files in config/scopes/ folder.
    
    Returns:
        Dictionary with status and results
    """
    logger.info(f"Starting data fetch for scope: {scope}")
    
    try:
        # Normalize scope name using mapping
        scope_info = SCOPE_MAPPING.get(scope) or SCOPE_MAPPING.get(scope.lower())
        if not scope_info:
            return {
                "success": False,
                "error": f"Scope '{scope}' not found. Available scopes: {', '.join(SCOPE_MAPPING.keys())}",
            }
        
        fetch_config = scope_info["fetch_config"]
        
        # Run the fetch script via subprocess
        project_root = Path(__file__).parent.parent
        script_path = project_root / "scripts" / "fetcher" / "fetch.py"
        
        # Verify scope config exists
        scope_config = project_root / "config" / "scopes" / f"{fetch_config}.yaml"
        if not scope_config.exists():
            return {
                "success": False,
                "error": f"Fetch config '{fetch_config}.yaml' not found.",
            }
        
        # Run the script
        result = subprocess.run(
            [sys.executable, str(script_path), "--scope", fetch_config],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=900,
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            return {
                "success": False,
                "error": f"Data fetch failed: {error_msg[:500]}",
            }
        
        # Check what was created/updated
        output_msg = result.stdout or ""
        
        logger.info(f"Data fetch completed for scope: {scope}")
        return {
            "success": True,
            "scope": scope,
            "message": "Data fetched successfully",
            "output": output_msg[:1000],  # Truncate for readability
        }
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Data fetch timed out (exceeded 15 minutes)",
        }
    except Exception as e:
        error_msg = f"Data fetch failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "error": error_msg,
        }


@mcp.tool()
async def list_status() -> dict[str, Any]:
    """
    List all available Pokémon scopes with their current status.
    
    Returns:
        Dictionary with scope information and file status
    """
    logger.info("Listing scope status")
    
    try:
        project_root = Path(__file__).parent.parent
        output_dir = project_root / "output"
        data_dir = project_root / "data"
        
        # Find all scope files in data directory
        scope_files = list(data_dir.glob("*.json"))
        scope_files = [f for f in scope_files if not f.name.startswith('.')]
        
        scopes = {}
        for scope_file in sorted(scope_files):
            scope_name = scope_file.stem
            
            try:
                with open(scope_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    pokemon_count = len(data.get("pokemon", []))
            except Exception as e:
                logger.error(f"Failed to read {scope_file}: {e}")
                pokemon_count = 0
            
            # Check for PDFs in all language directories
            pdf_files = list(output_dir.glob(f"*/*{scope_name}*.pdf"))
            
            info = {
                "scope": scope_name,
                "pokemon_count": pokemon_count,
                "pdf_generated": len(pdf_files) > 0,
                "pdf_languages": sorted(list(set([f.parent.name for f in pdf_files]))),
                "data_file": f"data/{scope_file.name}",
            }
            
            if pdf_files:
                total_size_kb = sum(f.stat().st_size for f in pdf_files) / 1024
                info["total_pdf_size_kb"] = round(total_size_kb, 1)
                info["pdf_count"] = len(pdf_files)
            
            scopes[scope_name] = info
        
        # Count generated PDFs
        total_pdfs = sum(s.get("pdf_count", 0) for s in scopes.values())
        
        return {
            "success": True,
            "total_scopes": len(scopes),
            "total_pdfs_generated": total_pdfs,
            "scopes": scopes,
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


if __name__ == "__main__":
    main()
