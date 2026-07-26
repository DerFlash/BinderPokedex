from pathlib import Path
from unittest.mock import MagicMock

from scripts.pdf.lib.rendering.page_renderer import PageRenderer
from scripts.pdf.lib.rendering.poster_page_renderer import PosterPageRenderer
from scripts.pdf.lib.variant_pdf_generator import VariantPDFGenerator


ROOT = Path(__file__).resolve().parents[2]


def test_base1_poster_page_draws_all_nine_physical_cards():
    renderer = PosterPageRenderer.from_variant_data({"set_id": "Base1"}, "de")
    assert renderer is not None
    canvas = MagicMock()
    page_renderer = PageRenderer()
    try:
        renderer.render_page(canvas, page_renderer)
    finally:
        renderer.cleanup()

    assert canvas.drawImage.call_count == 9
    for call in canvas.drawImage.call_args_list:
        assert call.kwargs["width"] == page_renderer.style.CARD_WIDTH
        assert call.kwargs["height"] == page_renderer.style.CARD_HEIGHT


def test_scope_without_enabled_poster_has_no_poster_page():
    assert PosterPageRenderer.from_variant_data({"set_id": "missing"}, "de") is None


def test_enabled_poster_can_be_skipped_before_loading_its_assets():
    assert (
        PosterPageRenderer.from_variant_data(
            {"set_id": "Base1"},
            "de",
            include_poster=False,
        )
        is None
    )


def test_base1_poster_source_is_text_free_artwork():
    renderer = PosterPageRenderer.from_variant_data({"set_id": "Base1"}, "en")
    assert renderer is not None
    try:
        assert renderer.artwork_path == (
            ROOT / "data" / "poster_assets" / "Base1" / "poster-flux2-artwork.png"
        )
        assert renderer.insertion == "after_first_section_cover"
    finally:
        renderer.cleanup()


def test_sv035_poster_source_is_text_free_artwork():
    renderer = PosterPageRenderer.from_variant_data({"set_id": "SV03.5"}, "de")
    assert renderer is not None
    try:
        assert renderer.artwork_path == (
            ROOT
            / "data"
            / "poster_assets"
            / "SV03.5"
            / "poster-flux2-artwork.png"
        )
        assert renderer.insertion == "after_first_section_cover"
    finally:
        renderer.cleanup()


def test_variant_generator_inserts_poster_only_after_first_section_cover():
    generator = VariantPDFGenerator.__new__(VariantPDFGenerator)
    generator.pokemon_list = []
    generator.language = "de"
    generator.variant_data = {}
    generator.page_renderer = MagicMock()
    generator.poster_page_renderer = MagicMock()
    generator._draw_section_cover = MagicMock()
    generator._draw_cards_page = MagicMock()
    canvas = MagicMock()
    sections = [
        {"section_id": "first", "section_order": 1, "cards": []},
        {"section_id": "second", "section_order": 2, "cards": []},
    ]

    generator._generate_with_sections(canvas, sections)

    generator.poster_page_renderer.render_page.assert_called_once_with(
        canvas, generator.page_renderer
    )
    assert canvas.showPage.call_count == 3
