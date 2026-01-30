# MCP Server Integration Guide

## Overview

The BinderPokedex MCP Server enables seamless integration with Claude, GitHub Copilot, and other AI assistants. Generate multilingual PDF collections through natural conversation.

### Features
- � **Scope-Based Architecture**: Generate any collection (Pokedex, TCG variants, etc.)
- 🌍 **9 Language Support**: DE, EN, FR, ES, IT, JA, KO, ZH-HANS, ZH-HANT
- 🤖 **AI-Native**: Talk to Claude or Copilot naturally
- ⚡ **Local & Fast**: Runs on your machine
- 🔄 **Seamless**: Automatic image download and processing

---

## Quick Start: Using BinderPokedex with Claude Desktop

This guide shows you how to connect BinderPokedex MCP Server to Claude Desktop so you can delegate PDF generation tasks to Claude.

---

## Step 1: Get Your Project Path

First, find the absolute path to your BinderPokedex project:

```bash
cd /path/to/BinderPokedex
pwd
```

Example output: `/Volumes/Daten/Entwicklung/BinderPokedex`

---

## Step 2: Configure Claude Desktop

1. **Open Claude Desktop settings**
   - Click the Claude menu in the top menu bar
   - Select "Settings..."

2. **Go to Developer settings**
   - Look for the "Developer" tab on the left sidebar
   - Click "Edit Config" button

3. **Add the BinderPokedex server**

Replace your existing config with this (update the path):

```json
{
  "mcpServers": {
    "binderokedex": {
      "command": "uv",
      "args": [
        "--directory",
        "/Volumes/Daten/Entwicklung/BinderPokedex",
        "run",
        ".mcp_server/binder_pokedex_server.py"
      ]
    }
  }
}
```

**On Windows**, replace the path with backslashes:
```json
"C:\\Users\\YourUsername\\path\\to\\BinderPokedex"
```

4. **Restart Claude Desktop**
   - Completely quit Claude (Cmd+Q or Ctrl+Alt+Q)
   - Reopen Claude

---

## Step 3: Verify Installation

Once Claude restarts, look for an MCP indicator in the bottom-right corner of the chat input area. Click it to see available tools.

You should see three tools:
- `generate_pdfs`
- `fetch_data`
- `list_status`

---

## Using BinderPokedex in Claude

### Example 1: Generate Pokedex PDF

**You write:**
```
"Generate the Pokedex PDF in German"
```

**Claude will:**
1. Call `generate_pdfs` with scope "Pokedex" and language "de"
2. Execute the PDF generation script
3. Report results and file locations

### Example 2: Generate TCG Variant PDFs

**You write:**
```
"Create the ExGen1_All PDF binder in English"
```

**Claude will:**
1. Call `generate_pdfs` with scope "ExGen1_All" and language "en"
2. Generate the TCG EX Generation 1 collection
3. Report file size and location

### Example 3: Fetch Fresh Data

**You write:**
```
"Fetch the latest Pokedex data from PokéAPI"
```

**Claude will:**
1. Call `fetch_data` with scope "Pokedex"
2. Execute the fetch pipeline
3. Report completion and what was updated

### Example 4: Complete Workflow

**You write:**
```
"Fetch ExGen1_All data and then generate the PDF in English"
```

**Claude will:**
1. Call `fetch_data` with scope "ExGen1_All"
2. Call `generate_pdfs` with scope "ExGen1_All" and language "en"
3. Report both operations completed

### Example 5: Check Available Scopes

**You write:**
```
"Show me all available scopes"
```

**Claude will:**
1. Call `list_status`
2. Show you all available scopes from data/ folder
3. Display which PDFs exist and their languages

---

### Example 6: Generate Multiple Languages

**You write:**
```
"Generate the Pokedex in Japanese and Korean"
```

**Claude will:**
1. Call `generate_pdfs` with scope "Pokedex" and language "ja"
2. Call `generate_pdfs` with scope "Pokedex" and language "ko"
3. Report completion for both languages

---

## Real-World Workflow

You can now use Claude to fully automate your Pokémon binder workflow:

```
"Fetch fresh Pokedex data, then generate the Pokedex PDF in German and English."
```

Claude will:
1. Call `fetch_data` to update Pokedex data from PokéAPI
2. Generate Pokedex PDF in German
3. Generate Pokedex PDF in English
4. Report completion and file locations

---

## Troubleshooting

### MCP Server Not Showing Up

1. **Check the path**: Verify your absolute path is correct
   ```bash
   pwd
   ```

2. **Ensure `uv` is installed**:
   ```bash
   uv --version
   ```

3. **Test the server directly**:
   ```bash
   cd /path/to/BinderPokedex
   uv run .mcp_server/binder_pokedex_server.py
   ```

4. **Check logs**: Look at `~/Library/Logs/Claude/mcp*.log` (macOS)

### Tools Not Appearing

- Restart Claude completely (Cmd+Q, then reopen)
- Check the MCP indicator again
- Verify the `command` and `args` match your system

### Generation Fails

- Ensure you have internet (for image downloads)
- Check that `output/` directory exists and is writable
- Verify scope names match JSON files in data/ folder

---

## Advanced: Testing the Server

Use the MCP Inspector to test without Claude:

```bash
cd /path/to/BinderPokedex
npx @modelcontextprotocol/inspector uv run .mcp_server/binder_pokedex_server.py
```

This opens an interactive UI where you can:
- Call tools manually
- See raw JSON-RPC messages
- Debug issues

---

## Next Steps

- **Use Claude to**: Generate entire binder sets, check status, manage collections
- **Integrate with**: GitHub Copilot, other MCP clients (use same config)
- **Extend the server**: Add new tools like batch operations, custom filters
- **Share your setup**: Document your workflow for others

---

## Security Notes

The MCP server:
- ✅ Runs locally on your machine
- ✅ Only has access to the BinderPokedex directory
- ✅ Cannot access files outside the project
- ✅ User controls all operations via Claude

---

**You're all set!** Start chatting with Claude and delegating your Pokémon binder tasks! 🎴✨

---

## Available Scopes

The following unified scopes work for both `fetch_data` and `generate_pdfs`:

| Scope | Description | Source |
|-------|-------------|--------|
| **Pokedex** | National Pokédex, all 9 generations | PokéAPI |
| **ExGen1_All** | TCG EX Gen 1 - all cards (128 cards) | TCGdex API |
| **ExGen1_Single** | TCG EX Gen 1 - one per Pokémon (~94) | TCGdex API |

**Pro Tip:** You can use these scope names interchangeably. For example:
- "Fetch Pokedex data" → fetches from PokéAPI
- "Generate Pokedex PDF" → uses the fetched data
