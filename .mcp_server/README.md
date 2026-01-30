# Binder Pokédex MCP Server

This directory contains the MCP (Model Context Protocol) server wrapper for BinderPokedex.

## Overview

The MCP server exposes the core BinderPokedex functionality as tools that can be used by Claude, GitHub Copilot, and other MCP-compatible clients.

## Available Tools

### `generate_pdfs`
Generate PDF binders with Pokémon card placeholders for any scope (Pokedex, TCG variants, etc.).

**Parameters:**
- `scope` (string): Scope name ("Pokedex", "ExGen1_All", "ExGen1_Single")
- `language` (string): Language code (de, en, fr, es, it, ja, ko, zh_hans, zh_hant)

**Examples:**
```
"Generate the Pokedex PDF in German"
"Create an ExGen1_All binder in English"
"Generate ExGen1_Single in Japanese"
```

### `fetch_data`
Fetch Pokémon data from external APIs (PokéAPI, TCGdex) using the pipeline system.

**Parameters:**
- `scope` (string): Scope name ("Pokedex", "ExGen1_All", "ExGen1_Single")

**Note:** The same scope names work for both fetching and generating!

**Examples:**
```
"Fetch the latest Pokedex data from PokéAPI"
"Update ExGen1_All TCG data"
```

### `list_status`
List all available Pokémon scopes with their status.

Shows which scopes are available, how many Pokémon each contains, and which PDFs have been generated.

**Example:**
```
"Show all available scopes"
"What scopes do we have?"
"List all Pokemon collections"
```

## Available Scopes

The following unified scopes work for both `fetch_data` and `generate_pdfs`:

1. **Pokedex** - National Pokédex with all 9 generations
2. **ExGen1_All** - TCG EX Generation 1 (all cards, including duplicates)
3. **ExGen1_Single** - TCG EX Generation 1 (one card per Pokémon)

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
        ".mcp_server/binder_pokedex_server.py"
      ]
    }
  }
}
```

Replace `/absolute/path/to/BinderPokedex` with your actual project path.

### Using in Claude

Once configured, you can use the tools naturally:

1. **Generate PDFs**: "Create the Pokedex PDF in German"
2. **List Scopes**: "Show me all available scopes"
3. **Generate Variants**: "Generate ExGen1_All in English"

## Usage with Other Clients

### Copilot and Other MCP Clients

Configure the server similar to Claude Desktop using your client's MCP configuration.

### Direct Usage

Run the server directly:

```bash
cd /path/to/BinderPokedex
uv run .mcp_server/binder_pokedex_server.py
```

## Architecture

The MCP server:
- Uses `FastMCP` for simplified Python MCP implementation
- Wraps the existing `scripts/pdf/generate_pdf.py` script
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
