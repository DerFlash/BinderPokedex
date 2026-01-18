# Known Issues & TODOs

## ✅ Resolved in v2.0.0

### Unicode Gender Symbols
- Gender symbols (♀/♂) are correctly displayed as `(w)` / `(m)`
- Works reliably on all systems

### CJK Text Rendering
- Japanese, Korean, Simplified & Traditional Chinese fully supported
- Uses Songti TrueType fonts
- All 9 languages tested

### Image Support
- Official Pokémon artwork downloaded from PokéAPI
- Transparent backgrounds intelligently removed
- Aggressive compression results in small file sizes (200-400 KB per generation)

### English Subtitles
- English name displayed as small subtitle (4pt) on non-English language cards
- Improves readability for international collectors
- Properly centered and positioned below main name

---

## Current Limitations

No known critical issues. If you find one, please create an Issue! 🐛

---

## Possible Future Improvements

- [ ] Test WebP format for even better compression
- [ ] Add more languages
- [ ] CLI options for image quality / size
- [ ] Batch processing for multiple languages simultaneously
- [ ] MCP Server improvements
