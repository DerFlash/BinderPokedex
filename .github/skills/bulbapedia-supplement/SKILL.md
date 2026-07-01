---
name: bulbapedia-supplement
description: "Create a Bulbapedia card supplement when TCGdex is missing cards for a set. Use when: a set has fewer cards than expected, TCGdex returns 404 for card numbers above N, supplement file needed, incomplete TCGdex data."
argument-hint: "[set-id] [bulbapedia-url]"
---

# Bulbapedia Supplement

Use this skill when a TCGdex set is missing cards that are listed on Bulbapedia.

## When to Use

- TCGdex API returns fewer cards than the set's known card count
- `curl https://api.tcgdex.net/v2/en/cards/<set-id>-NNN` returns 404 for known card numbers
- `data/source/<set-id>.json` is stale and does not cover recently released cards

## Procedure

### 1. Confirm the gap

```bash
# Check how many cards TCGdex has
curl -s "https://api.tcgdex.net/v2/en/sets/<SET_ID>" | python3 -c "import json,sys; d=json.load(sys.stdin); print('TCGdex:', d.get('cardCount'))"
```

Find the Bulbapedia page for the set. URL pattern:
`https://bulbapedia.bulbagarden.net/wiki/<Set_Name>_(TCG)`

Example: `https://bulbapedia.bulbagarden.net/wiki/MEP_Black_Star_Promos_(TCG)`

### 2. Run the scraper

From the project root, with the venv active:

```bash
python .github/skills/bulbapedia-supplement/scripts/scrape_cardlist.py \
  --set-id <set-id> \
  --url "<bulbapedia-url>" \
  --from-card <first-missing-card-number>
```

The script writes `data/source/<set-id>_supplement.json`.

**Example for MEP (TCGdex has 010, Bulbapedia has 079+):**
```bash
python .github/skills/bulbapedia-supplement/scripts/scrape_cardlist.py \
  --set-id mep \
  --url "https://bulbapedia.bulbagarden.net/wiki/MEP_Black_Star_Promos_(TCG)" \
  --from-card 11
```

### 3. Review the output

The script prints a summary table. Verify:
- Card names look correct (no stray annotations)
- Types are populated for Pokémon cards
- Trainer cards have a non-empty `trainerType`

Inspect the file: `data/source/<set-id>_supplement.json`

### 4. Wire into the scope YAML

The `merge_tcg_supplement` step is already implemented and registered in
`scripts/fetcher/fetch.py`. You only need to add it to the scope YAML.

In `config/scopes/<SET>.yaml`, add the step after `fetch_tcgdex_set`:

```yaml
- step: fetch_tcgdex_set
  params:
    set_id: <set-id>
    output_file: data/source/<set-id>.json
- step: merge_tcg_supplement
  params:
    supplement_file: data/source/<set-id>_supplement.json
- step: enrich_tcg_names_multilingual
  ...
```

The step implementation lives in
`scripts/fetcher/steps/merge_tcg_supplement.py`. It accepts a
`supplement_file` path relative to the project root, skips silently if the
file does not exist, and only appends cards whose `localId` is not already
present in the TCGdex source.

### 5. Run and validate

```bash
python scripts/fetcher/fetch.py --scope <SCOPE_NAME>
```

Check `data/output/<SCOPE_NAME>.json` for the full card count.

## Schema Reference

See [supplement_schema.md](./references/supplement_schema.md) for:
- Full JSON structure of the supplement file
- Card object field definitions
- Pokémon type value list
- Pipeline integration details

## Notes

- Supplement cards use `"image": ""` — they will not have card artwork in the PDF.
- The `dexId` field is left empty and filled in by `enrich_tcg_cards_from_pokedex`.
- When TCGdex later adds a card, the merge step ignores the supplement entry for
  that `localId` automatically — no manual cleanup needed.
- Supplement files are committed to `data/source/` just like other source files.
