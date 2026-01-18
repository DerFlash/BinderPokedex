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
@binderokedex generate PDF binders for all 8 generations in English
```

Or specify a different language:
```
@binderokedex generate PDF binders for Gen 1-3 in German
```

### Available Commands

Simply ask the AI to do things like:

- **"Generate PDFs for generations 1 through 3"**
  → Calls `generate_pdfs` with "1-3", uses English by default

- **"Create binders in French for all generations"**
  → Calls `generate_pdfs` with language parameter "fr"

- **"Fetch the latest Pokémon data"**
  → Calls `fetch_pokemon` for data updates

- **"Show me which generations are ready"**
  → Calls `list_status`

- **"What's the status of the Galar region?"**
  → Calls `list_status` and filters for generation 8

- **"Generate PDFs in German, Spanish, and Japanese"**
  → AI chains multiple tool calls for different languages

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
│   ├── fetch_pokemon_from_pokeapi.py
│   └── ...
├── i18n/
│   ├── __init__.py
│   ├── languages.json
│   └── translations.json
├── data/
│   └── pokemon_gen*.json
└── output/
    └── BinderPokedex_Gen*_*.pdf
```

---

## Tools Available to AI

### `generate_pdfs`
**What it does:** Generate PDF binders with Pokémon card placeholders

**Parameters:**
- `generations`: "1", "1-8", "all", or "1,3,5"
- `language`: "de", "en", "fr", "es", "it", "ja", "ko", "pt", "ru" (default: "en")

**Example:** "Create PDF binders for Gen 1-5 in Japanese"

### `list_status`
**What it does:** Show status of all generations and created PDFs

**Example:** "Which generations do we have?"

---

## Multilingual PDFs

The system supports **9 languages** with full localization:

| Code | Language | Card Names | Type Names | Regions |
|------|----------|-----------|-----------|---------|
| `en` | English | Only English | English | English |
| `de` | Deutsch | German | German | German |
| `fr` | Français | French (+ English) | French | French |
| `es` | Español | Spanish (+ English) | Spanish | Spanish |
| `it` | Italiano | Italian (+ English) | Italian | Italian |
| `ja` | 日本語 | Japanese (+ English) | Japanese | Japanese |
| `ko` | 한국어 | Korean (+ English) | Korean | Korean |
| `pt` | Português | Portuguese (+ English) | Portuguese | Portuguese |
| `ru` | Русский | Russian (+ English) | Russian | Russian |

**Note:** For non-English languages, the English name appears as a secondary label for clarity.

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
2. **Ask Copilot**: "Generate English PDFs for all generations"
3. **Copilot runs**: `generate_pdfs("1-8", "en")`
4. **Minutes later**: All 8 PDFs are ready in `output/BinderPokedex_Gen*_EN.pdf`
5. **Ask again**: "Now create German versions"
6. **Done!** No manual steps needed

---

## Pro Tips

- **Batch operations**: Ask AI to do multiple things at once
  ```
  "Generate PDFs for Gen 1-8 in English, German, and Japanese"
  ```

- **Error recovery**: AI automatically handles and reports issues
  ```
  "Generate Gen 5 PDF - if it fails, fetch the data first"
  ```

- **Status checks**: Quick info gathering
  ```
  "Which PDFs have been created and what languages?"
  ```

- **Language switching**: Easy multi-language support
  ```
  "Generate the same binders in all supported languages"
  ```

---

## Next Steps

1. ✅ Clone the project
2. ✅ Install an MCP-enabled AI extension
3. ✅ Open in VS Code
4. ✅ Start asking!

**That's all. Everything else is automated.** 🎉

---

**Questions?** Check the main [README.md](README.en.md) or [docs/MCP_INTEGRATION.md](docs/MCP_INTEGRATION.md) for more details.
