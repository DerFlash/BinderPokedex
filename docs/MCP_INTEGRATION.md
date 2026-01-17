# MCP Server Integration Guide

## Quick Start: Using BinderPokedex with Claude Desktop

This guide shows you how to connect BinderPokedex MCP Server to Claude Desktop so you can delegate PDF generation and data fetching tasks to Claude.

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
        "mcp_server/binder_pokedex_server.py"
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

You should see four tools:
- `generate_pdfs`
- `fetch_pokemon`
- `list_generations`
- `get_generation_info`

---

## Using BinderPokedex in Claude

### Example 1: Generate All PDFs

**You write:**
```
"Generate PDF binders for all 8 generations of Pokémon"
```

**Claude will:**
1. Call `generate_pdfs` with generations "1-8"
2. Execute the PDF generation script
3. Report results and file locations

---

### Example 2: Update Pokémon Data

**You write:**
```
"Update the Pokémon data for generation 5"
```

**Claude will:**
1. Call `fetch_pokemon` for generation 5
2. Fetch fresh data from PokéAPI
3. Cache it for later use
4. Report the count and status

---

### Example 3: Check Generation Status

**You write:**
```
"Show me which generations are ready"
```

**Claude will:**
1. Call `list_generations`
2. Show you which PDFs exist
3. Display generation names and statistics

---

### Example 4: Get Specific Generation Details

**You write:**
```
"What's the status of the Galar region?"
```

**Claude will:**
1. Call `get_generation_info` for generation 8
2. Show file size and path
3. Confirm generation status

---

## Real-World Workflow

You can now use Claude to fully automate your Pokémon binder workflow:

```
"I need fresh PDFs for all generations. First, fetch the latest data 
for generation 9, then generate all 8 generations we have data for."
```

Claude will:
1. Fetch Gen 9 data
2. Generate Gen 1-8 PDFs
3. Report completion and file locations

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
   uv run mcp_server/binder_pokedex_server.py
   ```

4. **Check logs**: Look at `~/Library/Logs/Claude/mcp*.log` (macOS)

### Tools Not Appearing

- Restart Claude completely (Cmd+Q, then reopen)
- Check the MCP indicator again
- Verify the `command` and `args` match your system

### Generation Fails

- Ensure you have internet (for PokéAPI access)
- Check that `output/` directory exists and is writable
- Verify generation numbers are 1-9

---

## Advanced: Testing the Server

Use the MCP Inspector to test without Claude:

```bash
cd /path/to/BinderPokedex
npx @modelcontextprotocol/inspector uv run mcp_server/binder_pokedex_server.py
```

This opens an interactive UI where you can:
- Call tools manually
- See raw JSON-RPC messages
- Debug issues

---

## Next Steps

- **Use Claude to**: Generate entire binder sets, update data, check status
- **Integrate with**: GitHub Copilot, other MCP clients (use same config)
- **Extend the server**: Add new tools like analyzing PDFs, batch operations
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
