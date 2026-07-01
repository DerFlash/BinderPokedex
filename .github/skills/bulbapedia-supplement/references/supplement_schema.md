# Supplement JSON Schema

A supplement file provides card data for cards that TCGdex has not yet indexed.
It lives at `data/source/<set-id>_supplement.json` and is merged into the
pipeline by the `merge_tcg_supplement` step.

## Top-Level Structure

```json
{
  "set_id": "mep",
  "source": "Bulbapedia",
  "source_url": "https://bulbapedia.bulbagarden.net/wiki/MEP_Black_Star_Promos_(TCG)",
  "date_fetched": "2026-04-01T10:00:00+00:00",
  "from_card": 11,
  "cards": [ ... ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `set_id` | string | Must match the `set_id` in `config/scopes/<SET>.yaml` |
| `source` | string | Human-readable source name |
| `source_url` | string | Page that was scraped |
| `date_fetched` | string | ISO-8601 UTC timestamp |
| `from_card` | integer | Lowest card number included (cards below this are in TCGdex) |
| `cards` | array | List of card objects (see below) |

## Card Object

```json
{
  "id": "mep-011",
  "localId": "011",
  "name": "Mega Latias ex",
  "image": "",
  "category": "Pokemon",
  "types": ["Dragon"],
  "dexId": [],
  "trainerType": ""
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | `<set-id>-<localId>` |
| `localId` | string | Zero-padded card number, e.g. `"011"` |
| `name` | string | Card name as on Bulbapedia (canonical form) |
| `image` | string | Always `""` — no TCGdex image available |
| `category` | string | `"Pokemon"`, `"Trainer"`, or `"Energy"` |
| `types` | array | List of type strings for Pokémon; `[]` for Trainer/Energy |
| `dexId` | array | Always `[]` — filled in by `enrich_tcg_cards_from_pokedex` |
| `trainerType` | string | Trainer sub-type (e.g. `"Item"`, `"Supporter"`, `"Stadium"`); `""` for Pokémon |

## Pokémon Type Values

Use the TCGdex canonical names (same as Bulbapedia image alt text):

`Grass` `Fire` `Water` `Lightning` `Fighting` `Psychic`
`Darkness` `Metal` `Dragon` `Colorless` `Fairy`

## Pipeline Integration

After generating the supplement, wire it into the scope YAML with the
`merge_tcg_supplement` step inserted **after** `fetch_tcgdex_set` and **before**
`enrich_tcg_names_multilingual`:

```yaml
- step: fetch_tcgdex_set
  params:
    set_id: mep
    output_file: data/source/mep.json
- step: merge_tcg_supplement        # ← add this
  params:
    supplement_file: data/source/mep_supplement.json
- step: enrich_tcg_names_multilingual
  ...
```

The `merge_tcg_supplement` step must:
1. Read `context.data["tcg_set_source"]`
2. Determine which card `localId` values are already present
3. Append supplement cards whose `localId` is not already present
4. Update `metadata.total_cards`
5. Persist the merged result back to `context.data["tcg_set_source"]`

## Notes

- Empty rows (unreleased slots) are skipped automatically by the scraper.
- Jumbo (`[Jumbo]`) designation is stripped from the card name.
- Variant annotations (`[Staff]`, `[Pokémon Center]`) are stripped — the base
  card name is stored.
- When TCGdex later adds a card, the supplement entry for that `localId` is
  simply ignored by the merge step (TCGdex data takes precedence).
