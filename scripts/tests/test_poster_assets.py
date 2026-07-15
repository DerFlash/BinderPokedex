from pathlib import Path

from PIL import Image

from scripts.poster_assets import fetch_cutouts
from scripts.poster_assets.layout import build_page_layout
from scripts.poster_assets.render_poster import cutout_placements


def test_auto_count_uses_layout_columns():
    manifest = {"pokemon": {"count": "auto_from_layout_columns"}}
    assert fetch_cutouts.resolve_requested_count(manifest, build_page_layout("wide_4x3")) == 4


def test_select_pokemon_uses_fallback_candidates():
    manifest = {
        "pokemon": {
            "strategy": "featured_from_scope",
            "fallback_candidates": [{"pokemon_id": 25}],
        }
    }
    scope_data = {
        "sections": {
            "all": {
                "featured_elements": [
                    {"pokemon_id": 150, "pokemon_name": "Mewtwo"},
                    {"pokemon_id": 1, "pokemon_name": "Bulbasaur"},
                    {"pokemon_id": 4, "pokemon_name": "Charmander"},
                ]
            }
        }
    }
    names = {25: {"en": "Pikachu", "de": "Pikachu"}}

    selected = fetch_cutouts.select_pokemon(manifest, scope_data, 4, names)

    assert [item["pokemon_id"] for item in selected] == [150, 1, 4, 25]


def test_validate_png_requires_transparency(tmp_path: Path):
    transparent = tmp_path / "transparent.png"
    img = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    for x in range(100, 300):
        for y in range(100, 300):
            img.putpixel((x, y), (255, 0, 0, 255))
    img.save(transparent)

    validation = fetch_cutouts.validate_png(transparent)

    assert validation["validated_alpha"] is True
    assert validation["alpha_min"] == 0
    assert validation["alpha_max"] == 255


def test_validate_png_rejects_flattened_image(tmp_path: Path):
    flattened = tmp_path / "flattened.png"
    Image.new("RGBA", (400, 400), (255, 255, 255, 255)).save(flattened)

    validation = fetch_cutouts.validate_png(flattened)

    assert validation["validated_alpha"] is False
    assert "image has no transparent pixels" in validation["errors"]


def test_cutout_placements_share_one_foot_baseline():
    scope_dir = Path(__file__).resolve().parents[2] / "data" / "poster_assets" / "Base1"
    placements = cutout_placements(build_page_layout("standard_3x3"), scope_dir)

    foot_positions = []
    for placement in placements:
        alpha_box = placement["image"].getchannel("A").getbbox()
        assert alpha_box is not None
        foot_positions.append(placement["y"] + alpha_box[3])

    assert len(set(foot_positions)) == 1
