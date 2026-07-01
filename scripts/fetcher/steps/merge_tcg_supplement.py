"""
Merge a Bulbapedia supplement file into the TCG set source data.

This step appends cards from a supplement JSON to the cards already loaded
by fetch_tcgdex_set (or load_tcg_set), filling in card numbers that TCGdex
has not yet indexed.

Supplement files are produced by:
  .github/skills/bulbapedia-supplement/scripts/scrape_cardlist.py

The supplement schema is documented in:
  .github/skills/bulbapedia-supplement/references/supplement_schema.md
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

from .base import BaseStep, PipelineContext

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class MergeTCGSupplementStep(BaseStep):
    """Append supplemental cards (from Bulbapedia) to the TCG set source data."""

    def execute(self, context: PipelineContext, params: Dict[str, Any]) -> PipelineContext:
        supplement_file = params.get("supplement_file")
        if not supplement_file:
            logger.error("No supplement_file parameter provided")
            return context

        supplement_path = (
            Path(supplement_file)
            if Path(supplement_file).is_absolute()
            else PROJECT_ROOT / supplement_file
        )

        if not supplement_path.exists():
            logger.warning(f"Supplement file not found, skipping: {supplement_file}")
            print(f"    ⚠️  Supplement file not found, skipping: {supplement_file}")
            return context

        with open(supplement_path, "r", encoding="utf-8") as f:
            supplement = json.load(f)

        current_data = context.get_data() or {}
        tcg_source = current_data.get("tcg_set_source")

        if not tcg_source:
            logger.warning("No tcg_set_source in context, skipping supplement merge")
            print("    ⚠️  No TCG set source loaded yet — run load_tcg_set or fetch_tcgdex_set first")
            return context

        existing_ids = {c["localId"] for c in tcg_source.get("cards", [])}
        supplement_cards = supplement.get("cards", [])

        added = 0
        for card in supplement_cards:
            if card["localId"] not in existing_ids:
                tcg_source["cards"].append(card)
                existing_ids.add(card["localId"])
                added += 1

        if added:
            # Sort the merged list by localId so downstream steps see a consistent order.
            tcg_source["cards"].sort(key=lambda c: c["localId"])
            # Update the metadata total so later steps report the right count.
            if "metadata" in tcg_source:
                tcg_source["metadata"]["total_cards"] = len(tcg_source["cards"])

        current_data["tcg_set_source"] = tcg_source
        context.set_data(current_data)

        set_id = supplement.get("set_id", "?")
        source = supplement.get("source", "supplement")
        skipped = len(supplement_cards) - added

        print(
            f"    📋 Merged {added} cards from {source} into {set_id}"
            + (f" ({skipped} already present in TCGdex, skipped)" if skipped else "")
        )
        logger.info(f"Supplement merge: +{added} cards for {set_id} from {supplement_file}")

        return context
