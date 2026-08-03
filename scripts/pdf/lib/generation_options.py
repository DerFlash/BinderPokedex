"""Prepare scope data for optional PDF generation modes."""

from copy import deepcopy
from typing import Any


TEST_CARD_LIMIT = 9
POSTER_PAGE_MODES = ("cards", "full-page")


def validate_poster_page_mode(value: str) -> None:
    """Reject unsupported poster PDF presentation modes."""
    if value not in POSTER_PAGE_MODES:
        raise ValueError(
            f"poster_page_mode must be one of {', '.join(POSTER_PAGE_MODES)}"
        )


def pdf_output_filename(
    filename_base: str,
    language: str,
    *,
    skip_images: bool = False,
    skip_poster: bool = False,
    poster_page_mode: str = "cards",
    test_mode: bool = False,
) -> str:
    """Return a mode-specific filename that cannot replace a normal PDF."""
    validate_poster_page_mode(poster_page_mode)
    parts = [filename_base, language.upper()]
    if test_mode:
        parts.append("TEST")
    if skip_images:
        parts.append("NO_IMAGES")
    if poster_page_mode == "full-page" and not skip_poster:
        parts.append("POSTER_FULL_PAGE")
    if skip_poster:
        parts.append("NO_POSTER")
    return "_".join(parts) + ".pdf"


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
