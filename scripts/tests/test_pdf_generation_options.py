from unittest.mock import MagicMock

from scripts.pdf import generate_pdf
from scripts.pdf.lib.generation_options import prepare_variant_data
from scripts.pdf.lib.variant_pdf_generator import VariantPDFGenerator


def _card(card_id: int) -> dict:
    return {
        "pokemon_id": card_id,
        "name": {"en": f"Pokemon {card_id}"},
        "image_url": f"https://example.test/{card_id}.png",
    }


def test_no_options_preserve_original_mapping():
    source = {"sections": {"all": {"cards": [_card(1)]}}}

    assert prepare_variant_data(source) is source


def test_test_mode_limits_cards_globally_in_render_order():
    source = {
        "set_id": "Example",
        "sections": {
            "second": {
                "section_order": 2,
                "cards": [_card(card_id) for card_id in range(7, 13)],
            },
            "first": {
                "section_order": 1,
                "cards": [_card(card_id) for card_id in range(1, 7)],
            },
            "third": {
                "section_order": 3,
                "cards": [_card(card_id) for card_id in range(13, 19)],
            },
        },
    }

    prepared = prepare_variant_data(source, test_mode=True)

    assert list(prepared["sections"]) == ["first", "second"]
    assert [
        card["pokemon_id"]
        for section in prepared["sections"].values()
        for card in section["cards"]
    ] == list(range(1, 10))
    assert len(source["sections"]["second"]["cards"]) == 6
    assert list(source["sections"]) == ["second", "first", "third"]


def test_skip_images_removes_only_remote_card_sources():
    source = {
        "logo_urls": {"en": "https://example.test/logo.png"},
        "sections": {
            "all": {
                "featured_elements": [
                    {"local_image_path": "data/featured-card.png"}
                ],
                "cards": [
                    {
                        **_card(1),
                        "image_path": "data/local-card.png",
                    }
                ],
            }
        },
    }

    prepared = prepare_variant_data(source, skip_images=True)
    card = prepared["sections"]["all"]["cards"][0]

    assert "image_url" not in card
    assert card["image_path"] == "data/local-card.png"
    assert prepared["logo_urls"] == source["logo_urls"]
    assert prepared["sections"]["all"]["featured_elements"] == [
        {"local_image_path": "data/featured-card.png"}
    ]
    assert "image_url" in source["sections"]["all"]["cards"][0]


def test_options_support_legacy_flat_pokemon_data():
    source = {"pokemon": [_card(card_id) for card_id in range(1, 13)]}

    prepared = prepare_variant_data(
        source,
        skip_images=True,
        test_mode=True,
    )

    assert len(prepared["pokemon"]) == 9
    assert all("image_url" not in card for card in prepared["pokemon"])
    assert len(source["pokemon"]) == 12


def test_variant_pdf_generation_applies_cli_options(monkeypatch, tmp_path):
    source = {
        "set_id": "Example",
        "sections": {
            "all": {
                "cards": [_card(card_id) for card_id in range(1, 13)],
            }
        },
    }
    generator = MagicMock()
    generator.generate.return_value = True
    generator_factory = MagicMock(return_value=generator)
    monkeypatch.setattr(generate_pdf, "VariantPDFGenerator", generator_factory)

    result = generate_pdf._generate_variant_pdf(
        variant_data=source,
        language="de",
        output_dir=tmp_path,
        script_dir=tmp_path,
        skip_images=True,
        test_mode=True,
        scope_name="Example",
    )

    prepared = generator_factory.call_args.kwargs["variant_data"]
    assert result is True
    assert len(prepared["sections"]["all"]["cards"]) == 9
    assert all(
        "image_url" not in card
        for card in prepared["sections"]["all"]["cards"]
    )
    generator.generate.assert_called_once_with()


def test_legacy_flat_variant_normalizes_pokemon_to_renderable_cards():
    generator = VariantPDFGenerator.__new__(VariantPDFGenerator)
    generator.variant_data = {
        "variant_name": "Legacy Collection",
        "pokemon": [{"pokemon_id": 1}, {"pokemon_id": 4}],
    }
    generator.pokemon_list = generator.variant_data["pokemon"]

    sections = generator._sections_for_rendering()

    assert len(sections) == 1
    assert sections[0]["title"] == "Legacy Collection"
    assert sections[0]["cards"] == generator.pokemon_list
