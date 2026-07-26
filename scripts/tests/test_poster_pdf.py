import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PIL import Image

from scripts.pdf.lib.rendering.page_renderer import PageRenderer
from scripts.pdf.lib.rendering.poster_page_renderer import (
    PosterPageCollection,
    PosterPageRenderer,
)
from scripts.pdf.lib.variant_pdf_generator import VariantPDFGenerator
from scripts.poster_assets.poster_io import PosterBundle


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


def test_skip_poster_bypasses_aggregate_discovery(monkeypatch):
    def fail_discovery(*_args, **_kwargs):
        raise AssertionError("poster assets were accessed")

    monkeypatch.setattr(
        "scripts.pdf.lib.rendering.poster_page_renderer.poster_bundles_for_scope",
        fail_discovery,
    )

    collection = PosterPageCollection.from_scope(
        "Pokedex",
        {},
        "de",
        include_poster=False,
    )

    assert collection.renderers == []


def test_pokedex_enabled_generation_bundles_need_no_set_id():
    scope_data = json.loads(
        (ROOT / "data" / "output" / "Pokedex.json").read_text(
            encoding="utf-8"
        )
    )
    collection = PosterPageCollection.from_scope(
        "Pokedex",
        scope_data,
        "de",
    )

    try:
        assert [
            renderer.poster_id for renderer in collection.renderers
        ] == ["gen1", "gen2"]
        assert [
            renderer.section_id for renderer in collection.renderers
        ] == ["gen1", "gen2"]
    finally:
        collection.cleanup()


def test_enabled_aggregate_bindings_create_one_renderer_per_section(
    tmp_path,
    monkeypatch,
):
    assets = tmp_path / "poster_assets"
    scope_dir = assets / "Aggregate"
    for section_id in ("first", "second"):
        target_dir = scope_dir / section_id
        target_dir.mkdir(parents=True)
        (target_dir / "poster.yaml").write_text(
            (
                f"asset_key: Aggregate/{section_id}\n"
                "scope: Aggregate\n"
                f"poster_id: {section_id}\n"
                "source:\n"
                "  scope: Aggregate\n"
                f"  section_id: {section_id}\n"
                "layout:\n"
                "  name: standard_3x3\n"
            ),
            encoding="utf-8",
        )
        Image.new("RGB", (2, 2)).save(
            target_dir / "poster-flux2-artwork.png"
        )
    (scope_dir / "posters.yaml").write_text(
        (
            "schema_version: 1\n"
            "scope: Aggregate\n"
            "posters:\n"
            "  - id: first\n"
            "    section_id: first\n"
            "    manifest: first/poster.yaml\n"
            "    pdf:\n"
            "      enabled: true\n"
            "      insertion: after_section_cover\n"
            "  - id: second\n"
            "    section_id: second\n"
            "    manifest: second/poster.yaml\n"
            "    pdf:\n"
            "      enabled: true\n"
            "      insertion: after_section_cover\n"
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "scripts.pdf.lib.rendering.poster_page_renderer.POSTER_ASSETS",
        assets,
    )

    collection = PosterPageCollection.from_scope(
        "Aggregate",
        {
            "sections": {
                "first": {"cards": []},
                "second": {"cards": []},
            }
        },
        "de",
    )
    try:
        assert [
            (renderer.poster_id, renderer.section_id)
            for renderer in collection.renderers
        ] == [("first", "first"), ("second", "second")]
    finally:
        collection.cleanup()


def test_base1_poster_source_is_text_free_artwork():
    renderer = PosterPageRenderer.from_variant_data({"set_id": "Base1"}, "en")
    assert renderer is not None
    try:
        assert renderer.artwork_path == (
            ROOT / "data" / "poster_assets" / "Base1" / "poster-flux2-artwork.png"
        )
        assert renderer.insertion == "after_first_section_cover"
        assert renderer.layout_name == "standard_3x3"
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


def test_wide_poster_reports_the_matching_future_pdf_page_requirement():
    renderer = PosterPageRenderer.__new__(PosterPageRenderer)
    renderer.layout_name = "wide_4x3"
    renderer._prepare_cards = MagicMock(
        return_value=[Path(f"card-{index}.png") for index in range(12)]
    )

    with pytest.raises(ValueError, match="A3 landscape renderer"):
        renderer.render_page(MagicMock(), PageRenderer())


def test_wide_poster_renderer_accepts_a_matching_page_grid(tmp_path):
    card_paths = []
    for index in range(12):
        card_path = tmp_path / f"card-{index}.png"
        Image.new("RGB", (2, 2), (index, index, index)).save(card_path)
        card_paths.append(card_path)

    renderer = PosterPageRenderer.__new__(PosterPageRenderer)
    renderer.layout_name = "wide_4x3"
    renderer._prepare_cards = MagicMock(return_value=card_paths)
    page_renderer = MagicMock()
    page_renderer.style = SimpleNamespace(
        CARDS_PER_ROW=4,
        CARDS_PER_COLUMN=3,
        CARDS_PER_PAGE=12,
        CARD_WIDTH=10,
        CARD_HEIGHT=20,
    )
    page_renderer.calculate_card_position.side_effect = [
        (index * 10, 0) for index in range(12)
    ]
    canvas = MagicMock()

    renderer.render_page(canvas, page_renderer)

    assert canvas.drawImage.call_count == 12
    page_renderer.draw_cutting_guides.assert_called_once_with(canvas)


def test_variant_generator_inserts_poster_only_after_first_section_cover():
    generator = VariantPDFGenerator.__new__(VariantPDFGenerator)
    generator.pokemon_list = []
    generator.language = "de"
    generator.variant_data = {}
    generator.page_renderer = MagicMock()
    poster_page = MagicMock()
    generator.poster_pages = MagicMock()
    generator.poster_pages.for_section.side_effect = [[poster_page], []]
    generator._draw_section_cover = MagicMock()
    generator._draw_cards_page = MagicMock()
    canvas = MagicMock()
    sections = [
        {"section_id": "first", "section_order": 1, "cards": []},
        {"section_id": "second", "section_order": 2, "cards": []},
    ]

    generator._generate_with_sections(canvas, sections)

    poster_page.render_page.assert_called_once_with(
        canvas, generator.page_renderer
    )
    assert canvas.showPage.call_count == 3


def test_variant_generator_inserts_matching_poster_after_each_section_cover():
    generator = VariantPDFGenerator.__new__(VariantPDFGenerator)
    generator.pokemon_list = []
    generator.language = "de"
    generator.variant_data = {}
    generator.page_renderer = MagicMock()
    first = SimpleNamespace(
        insertion="after_section_cover",
        section_id="first",
        render_page=MagicMock(),
    )
    second = SimpleNamespace(
        insertion="after_section_cover",
        section_id="second",
        render_page=MagicMock(),
    )
    generator.poster_pages = PosterPageCollection([first, second])
    generator._draw_section_cover = MagicMock()
    generator._draw_cards_page = MagicMock()
    canvas = MagicMock()
    sections = [
        {"section_id": "first", "section_order": 1, "cards": []},
        {"section_id": "second", "section_order": 2, "cards": []},
    ]

    generator._generate_with_sections(canvas, sections)

    first.render_page.assert_called_once_with(canvas, generator.page_renderer)
    second.render_page.assert_called_once_with(canvas, generator.page_renderer)
    assert canvas.showPage.call_count == 4


def test_aggregate_posters_render_into_a_real_four_page_pdf(tmp_path):
    card_paths = []
    for index in range(9):
        card_path = tmp_path / f"card-{index}.png"
        Image.new(
            "RGB",
            (24, 34),
            (40 + index * 10, 90, 130),
        ).save(card_path)
        card_paths.append(card_path)

    renderers = []
    for section_id in ("first", "second"):
        bundle = PosterBundle(
            asset_key=f"Aggregate/{section_id}",
            scope="Aggregate",
            poster_id=section_id,
            section_id=section_id,
            asset_dir=tmp_path,
            manifest_path=tmp_path / "poster.yaml",
            manifest={"layout": {"name": "standard_3x3"}},
            pdf_enabled=True,
            insertion="after_section_cover",
            artwork_file="unused.png",
        )
        renderer = PosterPageRenderer(
            bundle,
            "de",
            tmp_path / "unused.png",
        )
        renderer._prepare_cards = MagicMock(return_value=card_paths)
        renderers.append(renderer)

    output_path = tmp_path / "aggregate.pdf"
    generator = VariantPDFGenerator.__new__(VariantPDFGenerator)
    generator.output_file = output_path
    generator.pokemon_list = []
    generator.language = "de"
    generator.variant_data = {
        "sections": {
            "first": {"section_order": 1, "cards": []},
            "second": {"section_order": 2, "cards": []},
        }
    }
    generator.page_renderer = PageRenderer()
    generator.poster_pages = PosterPageCollection(renderers)
    generator._draw_section_cover = MagicMock()
    generator._draw_cards_page = MagicMock()

    assert generator.generate() is True
    assert output_path.read_bytes().count(b"/Type /Page\n") == 4
    assert all(
        renderer._prepare_cards.call_count == 1
        for renderer in renderers
    )


def test_failed_pdf_build_preserves_previous_output_and_cleans_temp(
    tmp_path,
    monkeypatch,
):
    output_path = tmp_path / "existing.pdf"
    output_path.write_bytes(b"accepted")
    temporary_output = tmp_path / ".existing.pdf.tmp"

    def fake_canvas(path, **_kwargs):
        Path(path).write_bytes(b"partial")
        return MagicMock()

    monkeypatch.setattr(
        "scripts.pdf.lib.variant_pdf_generator.canvas.Canvas",
        fake_canvas,
    )
    generator = VariantPDFGenerator.__new__(VariantPDFGenerator)
    generator.output_file = output_path
    generator.pokemon_list = []
    generator.poster_pages = MagicMock()
    generator._sections_for_rendering = MagicMock(return_value=[])
    generator._generate_with_sections = MagicMock(
        side_effect=RuntimeError("second poster failed"),
    )

    assert generator.generate() is False
    assert output_path.read_bytes() == b"accepted"
    assert not temporary_output.exists()
    generator.poster_pages.cleanup.assert_called_once_with()


def test_section_dict_key_is_used_when_section_id_is_missing():
    generator = VariantPDFGenerator.__new__(VariantPDFGenerator)
    generator.variant_data = {
        "sections": {
            "gen2": {"section_order": 2, "cards": []},
            "gen1": {"section_order": 1, "cards": []},
        }
    }

    sections = generator._sections_for_rendering()

    assert [section["section_id"] for section in sections] == ["gen1", "gen2"]
