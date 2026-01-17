# 🚀 Quick Start: Using BinderPokedex with AI Tools in VS Code

## The Easy Way (Recommended)

### 1️⃣ Clone & Open in VS Code

```bash
git clone https://github.com/DerFlash/BinderPokedex.git
cd BinderPokedex
code .
```

### 2️⃣ Install MCP Extension (if you haven't already)

In VS Code, install one of these extensions:
- **GitHub Copilot Chat** (for GitHub Copilot)
- **Claude for VS Code** (for Claude)
- Or any other AI extension that supports MCP

### 3️⃣ That's it! 🎉

The MCP server is **automatically configured** in `.vscode/mcp.json`. When you open Copilot Chat or Claude chat, the BinderPokedex tools are immediately available.

---

## Using It

### With GitHub Copilot Chat

Open Copilot Chat (Ctrl+Shift+I / Cmd+Shift+I) and just ask:

```
@binderokedex generiere PDF Binder für alle 8 Generationen
```

Or in English:
```
@binderokedex generate PDF binders for all 8 generations
```

### Available Commands

Simply ask the AI to do things like:

- **"Generate PDFs for generations 1 through 3"**
  → Calls `generate_pdfs` with "1-3"

- **"Fetch the latest Pokémon data for generation 5"**
  → Calls `fetch_pokemon` with generation 5

- **"Show me which generations are ready"**
  → Calls `list_generations`

- **"What's the status of the Galar region?"**
  → Calls `get_generation_info` for generation 8

- **"Update all generations and create new PDFs"**
  → AI chains multiple tool calls together

---

## How It Works

1. **`.vscode/mcp.json`** is auto-discovered by VS Code
2. MCP extension reads it on startup
3. **BinderPokedex MCP Server** is launched automatically
4. Tools are available to any AI chat in VS Code
5. You just ask naturally - the AI handles everything

### The Magic Formula

```
Project Structure
├── .vscode/
│   ├── mcp.json          ← Auto-discovered!
│   └── settings.json
├── mcp_server/
│   └── binder_pokedex_server.py
├── scripts/
│   ├── generate_pdf.py
│   └── fetch_pokemon_from_pokeapi.py
└── data/ + output/
```

---

## Tools Available to AI

### `generate_pdfs`
**What it does:** Generate PDF binders with Pokémon card placeholders

**Example:** "Create PDF binders for Gen 1-5"

### `fetch_pokemon`
**What it does:** Download and cache Pokémon data from PokéAPI

**Example:** "Download Gen 9 data"

### `list_generations`
**What it does:** Show status of all generations

**Example:** "Which generations do we have?"

### `get_generation_info`
**What it does:** Get details about a specific generation

**Example:** "Info about generation 3"

---

## Troubleshooting

### Tools not showing up?

1. **Reload VS Code**: Cmd+Shift+P → "Developer: Reload Window"
2. **Check extension installed**: GitHub Copilot Chat or similar
3. **Verify Python works**:
   ```bash
   python --version
   uv --version
   ```

### "Command not found: uv"

Install `uv`:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Server fails to start

Check logs in VS Code terminal:
```bash
cd /path/to/BinderPokedex
uv run mcp_server/binder_pokedex_server.py
```

---

## Advanced: Manual Testing

Test the server without AI using MCP Inspector:

```bash
npx @modelcontextprotocol/inspector uv run mcp_server/binder_pokedex_server.py
```

Opens interactive UI at `http://localhost:6274`

---

## Example Workflow

1. **Morning**: Clone project, open in VS Code
2. **Ask Copilot**: "Generate PDFs for all generations"
3. **Copilot runs**: `generate_pdfs("1-8")`
4. **Minutes later**: All 8 PDFs are ready in `output/`
5. **Ask again**: "Show me the file sizes"
6. **Done!** No manual steps needed

---

## Pro Tips

- **Batch operations**: Ask AI to do multiple things at once
  ```
  "Fetch Gen 9 data, then generate PDFs for Gen 1-8, then show me the results"
  ```

- **Error recovery**: AI automatically handles and reports issues
  ```
  "Generate Gen 5 PDF - if it fails, fetch the data first"
  ```

- **Status checks**: Quick info gathering
  ```
  "Tell me which generations are complete and how many Pokémon we have"
  ```

---

## Next Steps

1. ✅ Clone the project
2. ✅ Install an MCP-enabled AI extension
3. ✅ Open in VS Code
4. ✅ Start asking!

**That's all. Everything else is automated.** 🎉

---

**Questions?** Check the main README.md or docs/MCP_INTEGRATION.md for more details.
