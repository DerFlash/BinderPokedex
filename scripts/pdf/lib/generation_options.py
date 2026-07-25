"""Prepare scope data for optional PDF generation modes."""

from copy import deepcopy
from typing import Any


TEST_CARD_LIMIT = 9


def prepare_variant_data(
    variant_data: dict[str, Any],
    *,
    skip_images: bool = False,
    test_mode: bool = False,
    test_card_limit: int = TEST_CARD_LIMIT,
) -> dict[str, Any]:
    """Return data adjusted for the requested PDF generation options.

    Test mode limits the complete PDF to ``test_card_limit`` cards, following
    the same section order as the renderer. Image skipping removes remote card
    image URLs while leaving deterministic local assets such as cover artwork,
    set logos, and poster artwork available.

    The input mapping is returned unchanged when no option is active. If an
    option is active, a deep copy is prepared so callers can safely reuse the
    loaded source data for additional languages or full-size PDFs.
    """
    if not skip_images and not test_mode:
        return variant_data
    if test_card_limit < 1:
        raise ValueError("test_card_limit must be at least 1")

    prepared = deepcopy(variant_data)
    sections = prepared.get("sections")

    if isinstance(sections, dict) and sections:
        if test_mode:
            ordered_sections = sorted(
                sections.items(),
                key=lambda item: item[1].get("section_order", 999),
            )
            remaining = test_card_limit
            limited_sections = {}

            for section_id, section in ordered_sections:
                cards = section.get("cards", [])
                if not isinstance(cards, list) or not cards or remaining == 0:
                    continue

                selected_cards = cards[:remaining]
                _remove_remote_image_urls(selected_cards, skip_images)
                section["cards"] = selected_cards
                limited_sections[section_id] = section
                remaining -= len(selected_cards)

            prepared["sections"] = limited_sections
        elif skip_images:
            for section in sections.values():
                cards = section.get("cards", [])
                if isinstance(cards, list):
                    _remove_remote_image_urls(cards, True)

        return prepared

    pokemon = prepared.get("pokemon")
    if isinstance(pokemon, list):
        if test_mode:
            pokemon = pokemon[:test_card_limit]
            prepared["pokemon"] = pokemon
        _remove_remote_image_urls(pokemon, skip_images)

    return prepared


def _remove_remote_image_urls(cards: list[dict[str, Any]], enabled: bool) -> None:
    """Remove remote image sources from card records in place when enabled."""
    if not enabled:
        return

    for card in cards:
        if isinstance(card, dict):
            card.pop("image_url", None)
