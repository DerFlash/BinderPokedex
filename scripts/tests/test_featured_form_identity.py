import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.fetcher.steps.enrich_featured_cards import (
    EnrichFeaturedElementsStep,
)
from scripts.fetcher.steps import pokemon_utils
from scripts.poster_assets.poster_subject import (
    PosterSubject,
    resolve_poster_subject,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _card(
    pokemon_id: int,
    artwork_id: int,
    name: str,
    card_id: str,
) -> dict:
    return {
        "pokemon_id": pokemon_id,
        "name": {"en": name},
        "prefix": "Mega",
        "image_url": PosterSubject(pokemon_id, artwork_id).image_url,
        "tcg_card": {"id": card_id},
    }


def test_featured_enrichment_preserves_cover_and_exact_form_subject(
    monkeypatch,
    tmp_path: Path,
):
    step = EnrichFeaturedElementsStep("featured")

    def fake_cover(pokemon_id, card, _cache_dir, _set_info):
        return {
            "pokemon_id": pokemon_id,
            "pokemon_name": card["name"]["en"],
            "card_id": card["tcg_card"]["id"],
            "image_url": (
                f"https://assets.tcgdex.net/en/test/{card['tcg_card']['id']}"
                "/high.png"
            ),
        }

    monkeypatch.setattr(step, "_fetch_card_image_from_any_card", fake_cover)
    elements = step._identify_and_fetch_featured_elements(
        [
            _card(380, 10062, "Latias", "me01-100"),
            _card(6, 10034, "Charizard X", "me02-013"),
            _card(6, 10035, "Charizard Y", "me02-022"),
        ],
        3,
        tmp_path,
    )

    assert [item["pokemon_name"] for item in elements] == [
        "Mega Latias",
        "Mega Charizard X",
        "Mega Charizard Y",
    ]
    assert all(
        item["image_url"].startswith("https://assets.tcgdex.net/")
        for item in elements
    )
    assert [
        resolve_poster_subject(item).official_artwork_id
        for item in elements
    ] == [10062, 10034, 10035]


def test_featured_enrichment_rejects_artwork_species_mismatch(
    tmp_path: Path,
):
    step = EnrichFeaturedElementsStep("featured")
    with pytest.raises(ValueError, match="belongs to Pokemon #6"):
        step._identify_and_fetch_featured_elements(
            [
                {
                    "pokemon_id": 1,
                    "name": {"en": "Wrong Bulbasaur"},
                    "prefix": "Mega",
                    "image_url": PosterSubject(6, 10034).image_url,
                    "tcg_card": {"id": "a"},
                }
            ],
            1,
            tmp_path,
        )


def test_mega_artwork_resolution_never_falls_back_to_base(monkeypatch):
    monkeypatch.setattr(
        pokemon_utils.requests,
        "get",
        lambda *_args, **_kwargs: SimpleNamespace(status_code=404),
    )

    with pytest.raises(RuntimeError, match="did not resolve"):
        pokemon_utils.get_mega_artwork_url(
            pokemon_name="Latias",
            base_id=380,
        )


def _checked_in_subjects(scope: str, section_id: str):
    payload = json.loads(
        (REPO_ROOT / "data" / "output" / f"{scope}.json").read_text(
            encoding="utf-8"
        )
    )
    payload["sections"] = {
        section_id: payload["sections"][section_id],
    }
    from scripts.poster_assets.fetch_cutouts import scope_featured_elements

    return [
        (
            subject.species_id,
            subject.official_artwork_id,
        )
        for subject in (
            resolve_poster_subject(item)
            for item in scope_featured_elements(payload)
        )
    ]


def test_checked_in_variant_scopes_resolve_their_exact_form_artwork():
    assert _checked_in_subjects("ExGen3", "mega") == [
        (380, 10062),
        (719, 10075),
        (448, 10059),
    ]
    assert _checked_in_subjects("ExGen2", "mega") == [
        (150, 10043),
        (384, 10079),
        (381, 10063),
    ]
    assert _checked_in_subjects("ExGen2", "primal") == [
        (382, 10077),
        (383, 10078),
    ]
    assert _checked_in_subjects("ME03", "all") == [
        (495, 495),
        (722, 722),
        (718, 10301),
    ]
    assert _checked_in_subjects("MEP", "all") == [
        (888, 888),
        (1, 1),
        (4, 4),
    ]
