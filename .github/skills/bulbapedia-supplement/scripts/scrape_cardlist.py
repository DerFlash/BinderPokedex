#!/usr/bin/env python3
"""
scrape_cardlist.py — Scrape a Bulbapedia TCG card list page and produce a supplement JSON.

The supplement file contains only the cards NOT already present in the TCGdex source,
so it can be merged into the pipeline via the merge_tcg_supplement step.

Usage:
    python scrape_cardlist.py --set-id mep \
        --url "https://bulbapedia.bulbagarden.net/wiki/MEP_Black_Star_Promos_(TCG)"

    # Only emit cards starting at card number 11 (i.e. TCGdex already has 001–010):
    python scrape_cardlist.py --set-id mep \
        --url "https://bulbapedia.bulbagarden.net/wiki/MEP_Black_Star_Promos_(TCG)" \
        --from-card 11

    # Specify output directory (default: data/source relative to project root):
    python scrape_cardlist.py --set-id mep \
        --url "https://bulbapedia.bulbagarden.net/wiki/MEP_Black_Star_Promos_(TCG)" \
        --output-dir data/source
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

POKEMON_TYPES = {
    "Grass", "Fire", "Water", "Lightning", "Fighting", "Psychic",
    "Darkness", "Metal", "Dragon", "Colorless", "Fairy",
}

# Bulbapedia abbreviations for trainer subtypes found in the type <th> cell.
TRAINER_TYPE_ABBREVS = {
    "I": "Item",
    "Su": "Supporter",
    "St": "Supporter",   # older Bulbapedia notation
    "Se": "Supporter",
    "Ta": "Tool",
    "TM": "Technical Machine",
    "Stadium": "Stadium",
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


# ---------------------------------------------------------------------------
# HTML parser
# ---------------------------------------------------------------------------

class _CardTableParser(HTMLParser):
    """Extract card rows from a Bulbapedia card-list page."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cards: list[dict] = []

        # Per-row state
        self._in_tr = False
        self._cells: list[dict] = []          # accumulated cells for current row
        self._current: dict | None = None     # cell being built

    # -- SAX-style callbacks --------------------------------------------------

    def handle_starttag(self, tag: str, attrs: list[tuple]) -> None:
        attrs_d = dict(attrs)

        if tag == "tr":
            self._in_tr = True
            self._cells = []

        elif tag in ("td", "th") and self._in_tr:
            self._current = {"tag": tag, "text": "", "img_alts": [], "link_title": None}

        elif self._current is not None:
            if tag == "img":
                alt = attrs_d.get("alt", "").strip()
                if alt:
                    self._current["img_alts"].append(alt)
            elif tag == "a" and self._current["link_title"] is None:
                title = attrs_d.get("title", "").strip()
                if title:
                    self._current["link_title"] = title

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self._current is not None:
            self._current["text"] = self._current["text"].strip()
            self._cells.append(self._current)
            self._current = None

        elif tag == "tr" and self._in_tr:
            self._in_tr = False
            self._process_row()

    def handle_data(self, data: str) -> None:
        if self._current is not None:
            self._current["text"] += data

    # -- Row processing -------------------------------------------------------

    def _process_row(self) -> None:
        cells = self._cells
        # Need at least: number, mark, name, type
        if len(cells) < 4:
            return

        # Cell 0: card number (must be digits only)
        num_text = cells[0]["text"]
        if not re.fullmatch(r"\d+", num_text):
            return
        local_id = num_text.zfill(3)

        # Cell 2: card name
        # Prefer the link title "Name (Set Promo NN)" — strip the parenthetical suffix.
        name = self._extract_name(cells[2])
        if not name:
            return  # empty row (unreleased slot)

        # Cell 3 (th): type
        category, types, trainer_type = self._extract_type(cells[3])

        self.cards.append({
            "localId": local_id,
            "name": name,
            "category": category,
            "types": types,
            "trainerType": trainer_type,
        })

    @staticmethod
    def _extract_name(cell: dict) -> str:
        # Use link title when available — it contains the canonical name.
        # The title may have multiple trailing parentheticals, e.g.:
        #   "Toxel (MEP Promo 78) (page does not exist)"
        # Strip ALL of them greedily.
        if cell["link_title"]:
            name = re.sub(r"(\s*\([^)]*\))+\s*$", "", cell["link_title"]).strip()
            if name:
                return name

        # Fallback: plain text with annotations and promo suffixes removed
        text = re.sub(r"\[.*?\]", "", cell["text"]).strip()
        # Take the first non-empty line (name is sometimes doubled for display)
        parts = [p.strip() for p in text.splitlines() if p.strip()]
        name = parts[0] if parts else ""
        return re.sub(r"(\s*\([^)]*\))+\s*$", "", name).strip()

    @staticmethod
    def _extract_type(cell: dict) -> tuple[str, list[str], str]:
        # A Pokémon type is always rendered as an image with its type name as alt text.
        for alt in cell["img_alts"]:
            if alt in POKEMON_TYPES:
                return "Pokemon", [alt], ""

        # Trainer type is plain text (abbreviation or full word).
        type_text = cell["text"].strip()
        if type_text and type_text != "—":
            trainer_type = TRAINER_TYPE_ABBREVS.get(type_text, type_text)
            return "Trainer", [], trainer_type

        # Unknown / empty
        return "Pokemon", [], ""


# ---------------------------------------------------------------------------
# Pokédex name → dexId lookup
# ---------------------------------------------------------------------------

# Prefixes that are stripped to find the base Pokémon name for dexId lookup.
_VARIANT_PREFIXES = ("Mega ", "Radiant ", "Shining ", "Dark ", "Rocket's ")
# Suffixes that are stripped (case-insensitive match against the end of the name).
_VARIANT_SUFFIXES_RE = re.compile(
    r"\s+(?:ex|EX|GX|V|VMAX|VSTAR|VUNION)$", re.IGNORECASE
)


def _build_dexid_index(pokedex_path: Path) -> dict[str, int]:
    """
    Build a mapping  {lowercase_english_name: national_dex_id}  from the project Pokédex.
    Returns an empty dict if the file does not exist.
    """
    if not pokedex_path.exists():
        return {}
    with open(pokedex_path, "r", encoding="utf-8") as f:
        pokedex = json.load(f)
    index: dict[str, int] = {}
    for section in pokedex.get("sections", {}).values():
        for pokemon in section.get("cards", []):
            dex_id = pokemon.get("pokemon_id")
            if not dex_id:
                continue
            name_field = pokemon.get("name", {})
            en_name = (
                name_field.get("en", "") if isinstance(name_field, dict) else str(name_field)
            )
            if en_name:
                index[en_name.lower()] = dex_id
    return index


def _resolve_dex_id(card_name: str, dexid_index: dict[str, int]) -> list[int]:
    """
    Return a 1-element list with the dexId for card_name, or [] if not found.
    Tries:
    1. Exact lowercase match
    2. After stripping known variant prefixes ("Mega ", etc.)
    3. After also stripping known variant suffixes (" ex", " GX", etc.)
    """
    if not dexid_index:
        return []

    def _lookup(name: str) -> int | None:
        return dexid_index.get(name.lower())

    # 1. Direct lookup
    result = _lookup(card_name)
    if result:
        return [result]

    # 2. Strip prefix
    base = card_name
    for pfx in _VARIANT_PREFIXES:
        if base.startswith(pfx):
            base = base[len(pfx):]
            break
    result = _lookup(base)
    if result:
        return [result]

    # 3. Also strip suffix
    base_no_suffix = _VARIANT_SUFFIXES_RE.sub("", base).strip()
    if base_no_suffix != base:
        result = _lookup(base_no_suffix)
        if result:
            return [result]

    return []


# ---------------------------------------------------------------------------
# Scraper
# ---------------------------------------------------------------------------

def scrape(url: str, set_id: str, from_card: int, dexid_index: dict[str, int]) -> list[dict]:
    """Fetch the Bulbapedia page and return card dicts with number >= from_card."""
    headers = {"User-Agent": "BinderPokedex/1.0 (supplement scraper; contact via GitHub)"}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    parser = _CardTableParser()
    parser.feed(response.text)

    cards = []
    for card in parser.cards:
        num = int(card["localId"])
        if num < from_card:
            continue
        card_id = f"{set_id}-{card['localId']}"
        dex_ids = _resolve_dex_id(card["name"], dexid_index) if card["category"] == "Pokemon" else []
        cards.append({
            "id": card_id,
            "localId": card["localId"],
            "name": card["name"],
            "image": "",
            "category": card["category"],
            "types": card["types"],
            "dexId": dex_ids,
            "trainerType": card["trainerType"],
        })

    return cards


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--set-id", required=True, help="Set identifier, e.g. mep")
    p.add_argument("--url", required=True, help="Full Bulbapedia URL of the card list page")
    p.add_argument(
        "--from-card", type=int, default=1, metavar="N",
        help="Only include cards with number >= N (default: 1, i.e. all cards)",
    )
    p.add_argument(
        "--output-dir", default=None, metavar="DIR",
        help="Directory to write <set-id>_supplement.json (default: <project-root>/data/source)",
    )
    p.add_argument(
        "--pokedex-file", default=None, metavar="FILE",
        help="Path to Pokedex JSON for dexId lookup (default: <project-root>/data/output/Pokedex.json)",
    )
    return p


def main() -> None:
    args = build_parser().parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else PROJECT_ROOT / "data" / "source"
    output_dir = output_dir if output_dir.is_absolute() else PROJECT_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{args.set_id}_supplement.json"

    pokedex_path = (
        Path(args.pokedex_file) if args.pokedex_file
        else PROJECT_ROOT / "data" / "output" / "Pokedex.json"
    )
    pokedex_path = pokedex_path if pokedex_path.is_absolute() else PROJECT_ROOT / pokedex_path

    dexid_index = _build_dexid_index(pokedex_path)
    if dexid_index:
        print(f"Loaded {len(dexid_index)} Pokémon from Pokédex for dexId lookup.")
    else:
        print("⚠️  Pokédex not found — dexId fields will be empty.")

    print(f"Fetching {args.url} …")
    cards = scrape(args.url, args.set_id, args.from_card, dexid_index)

    if not cards:
        print("No cards found (all filtered out or page could not be parsed).")
        sys.exit(0)

    supplement = {
        "set_id": args.set_id,
        "source": "Bulbapedia",
        "source_url": args.url,
        "date_fetched": datetime.now(timezone.utc).isoformat(),
        "from_card": args.from_card,
        "cards": cards,
    }

    output_path.write_text(json.dumps(supplement, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(cards)} cards to {output_path}")

    # Print a summary table
    resolved = sum(1 for c in cards if c["dexId"])
    print(f"\n{'#':>4}  {'Category':<9}  {'dexId':>7}  {'Type':>12}  Name")
    print("-" * 68)
    for c in cards:
        t = ", ".join(c["types"]) or c["trainerType"] or "?"
        dex = str(c["dexId"][0]) if c["dexId"] else "—"
        print(f"{int(c['localId']):>4}  {c['category']:<9}  {dex:>7}  {t:>12}  {c['name']}")
    print(f"\ndexId resolved: {resolved}/{len(cards)}")


if __name__ == "__main__":
    main()
