# Binder Pokédex MCP Server

This directory contains the MCP (Model Context Protocol) server wrapper for BinderPokedex.

## Overview

The MCP server exposes the core BinderPokedex functionality as tools that can be used by Claude, GitHub Copilot, and other MCP-compatible clients.

## Available Tools

### `generate_pdfs`
Generate PDF binders with Pokémon card placeholders across specified generations.

**Parameters:**
- `generations` (string): Generations to generate ("1", "1-8", "1,3,5", or "all")
- `verbose` (boolean): Show detailed progress

**Example:**
```
"Generate PDFs for generations 1 through 8"
"Create a Pokémon binder for just generation 5"
```

### `fetch_pokemon`
Fetch and cache Pokémon data from PokéAPI.

**Parameters:**
- `generation` (integer): Generation number (1-9)
- `force_refresh` (boolean): Force re-download even if cached

**Example:**
```
"Fetch Gen 9 data"
"Update generation 5 with latest PokéAPI data"
```

### `list_generations`
List all available Pokémon generations with their status.

**Example:**
```
"Show all available generations"
"What generations do we have?"
```

### `get_generation_info`
Get detailed information about a specific generation.

**Parameters:**
- `generation` (integer): Generation number (1-8)

**Example:**
```
"What's the status of generation 3?"
"Show info for Galar generation"
```

## Installation

The MCP server is automatically configured when you install BinderPokedex. No additional setup is needed.

## Usage with Claude Desktop

### Configuration

Add the server to your Claude Desktop configuration at `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "binderokedex": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/BinderPokedex",
        "run",
        "mcp_server/binder_pokedex_server.py"
      ]
    }
  }
}
```

Replace `/absolute/path/to/BinderPokedex` with your actual project path.

### Using in Claude

Once configured, you can use the tools naturally:

1. **Generate PDFs**: "Create PDF binders for all 8 generations"
2. **Fetch Data**: "Update the Pokémon data for generation 5"
3. **Check Status**: "Show me which generations have been generated"
4. **Get Info**: "Tell me about generation 7"

## Usage with Other Clients

### Copilot and Other MCP Clients

Configure the server similar to Claude Desktop using your client's MCP configuration.

### Direct Usage

Run the server directly:

```bash
cd /path/to/BinderPokedex
uv run mcp_server/binder_pokedex_server.py
```

## Architecture

The MCP server:
- Uses `FastMCP` for simplified Python MCP implementation
- Wraps the existing `generate_pdf.py` and `fetch_pokemon_from_pokeapi.py` scripts
- Logs to stderr to avoid interfering with MCP JSON-RPC communication
- Supports async operations for better performance
- Returns structured responses for each tool call

## Development

### Testing

Test the MCP server with the MCP Inspector:

```bash
cd /path/to/BinderPokedex
npx @modelcontextprotocol/inspector uv --directory . run mcp_server/binder_pokedex_server.py
```

### Logging

All server logs are written to stderr and can be monitored for debugging.

## Security

The MCP server:
- Only exposes read operations (fetch) and local file generation
- Does not require authentication (runs locally via stdio)
- Operates with user permissions only
- Can be easily sandboxed by the client application

## Next Steps

1. Configure the server in your MCP client
2. Use Claude or Copilot to delegate BinderPokedex tasks
3. Monitor progress through the client interface

## License

MIT - See LICENSE in project root
