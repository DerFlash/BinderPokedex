import json
import shutil
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image, ImageChops

from scripts.poster_assets import fetch_cutouts
from scripts.poster_assets import promote_comfyui_poster as poster_promotion
from scripts.poster_assets import run_comfyui_poster as poster_runner
from scripts.poster_assets.fetch_title_logos import resolve_logo_downloads
from scripts.poster_assets.create_comfyui_poster_workflow import build_workflow
from scripts.poster_assets.create_comfyui_upscale_workflow import (
    build_workflow as build_upscale_workflow,
)
from scripts.poster_assets.create_anima_poster_workflow import (
    build_workflow as build_anima_workflow,
)
from scripts.poster_assets.create_flux1_canny_poster_workflow import (
    build_workflow as build_flux1_canny_workflow,
)
from scripts.poster_assets.create_qwen_edit_poster_workflow import (
    build_workflow as build_qwen_edit_workflow,
)
from scripts.poster_assets.finalize_comfyui_poster import (
    draw_title_text_panel,
    finalize,
    fitted_font,
    info_panel_box,
    title_logo_file,
)
from scripts.poster_assets.layout import (
    build_page_layout,
    build_print_layout,
    effective_dpi,
    pdf_page_hint,
)
from scripts.poster_assets.init_poster_scope import (
    available_tcg_scopes,
    build_default_manifest,
    init_scope,
    stable_scope_seed,
)
from scripts.poster_assets.poster_io import poster_bundle
from scripts.poster_assets.poster_subject import (
    PosterSubject,
    official_artwork_id_from_url,
    poster_subject_from_card,
    resolve_poster_subject,
)
from scripts.poster_assets.poster_config import (
    IDENTITY_LOCK_PROMPT_FILE,
    build_identity_lock_prompt,
    build_identity_reference_prompt,
    identity_lock_config,
    identity_lock_overscan,
)
from scripts.poster_assets.provenance import (
    add_model_artifact_hashes,
    generation_input_records,
    sha256_file,
)
from scripts.poster_assets.queue_comfyui_workflow import (
    server_comfyui_root,
    server_input_directory,
    validate_server_input_directory,
)
from scripts.poster_assets.prepare_comfyui_poster import (
    build_identity_references,
    build_scene_reference,
    build_upper_context_mask,
    card_safe_conditioning_placements,
)
from scripts.poster_assets.composition import cutout_placements
from scripts.poster_assets.typography import wrap_text
from scripts.poster_assets.run_comfyui_poster import (
    configured_generation,
    resize_artwork,
    validate_identity_lock_pixels,
    validate_raw_artwork,
    write_engine_workflow,
)
from scripts.poster_assets.slice_poster import slice_poster
from scripts.poster_assets import upscale_comfyui_poster as poster_upscale
from scripts.poster_assets.scene_catalog import (
    load_scene_catalog,
    scene_for_scope,
    validate_catalog_coverage,
)
from scripts.poster_assets.validate_promoted_poster import (
    enabled_poster_scopes,
    validate as validate_promoted_poster,
)
from scripts.poster_assets import validate_promoted_poster as poster_validator


def test_auto_count_uses_layout_columns():
    manifest = {"pokemon": {"count": "auto_from_layout_columns"}}
    assert fetch_cutouts.resolve_requested_count(manifest, build_page_layout("wide_4x3")) == 4


@pytest.mark.parametrize("scope", [".", ".."])
def test_poster_initializer_rejects_path_traversal_scope(scope):
    with pytest.raises(ValueError, match="Unsafe scope name"):
        init_scope(scope)


def test_standard_print_layout_is_300_dpi_at_physical_card_size():
    layout = build_print_layout("standard_3x3", 300)

    assert (layout.width_px, layout.height_px) == (2368, 3268)
    assert (layout.card_width_px, layout.card_height_px) == (750, 1050)
    dpi_x, dpi_y = effective_dpi(layout)
    assert abs(dpi_x - 300) < 0.1
    assert abs(dpi_y - 300) < 0.1


def test_wide_layouts_are_modeled_for_future_matching_pdf_renderers():
    layout_4x3 = build_print_layout("wide_4x3", 300)
    layout_4x4 = build_print_layout("wide_4x4", 300)

    assert (layout_4x3.columns, layout_4x3.rows) == (4, 3)
    assert (layout_4x4.columns, layout_4x4.rows) == (4, 4)
    assert pdf_page_hint("wide_4x3") == ("A3", "landscape")
    assert pdf_page_hint("wide_4x4") == ("A3", "portrait")


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


def test_select_pokemon_keeps_distinct_forms_of_one_species():
    scope_data = {
        "sections": {
            "mega": {
                "featured_elements": [
                    {
                        "pokemon_id": 6,
                        "pokemon_name": "Mega Charizard X",
                        "poster_subject": PosterSubject(6, 10034).as_mapping(),
                    },
                    {
                        "pokemon_id": 6,
                        "pokemon_name": "Mega Charizard Y",
                        "poster_subject": PosterSubject(6, 10035).as_mapping(),
                    },
                    {
                        "pokemon_id": 380,
                        "pokemon_name": "Mega Latias",
                        "poster_subject": PosterSubject(
                            380,
                            10062,
                        ).as_mapping(),
                    },
                ]
            }
        }
    }
    selected = fetch_cutouts.select_pokemon(
        {
            "pokemon": {
                "strategy": "featured_from_scope",
                "fallback_candidates": [],
            }
        },
        scope_data,
        3,
        {},
    )

    assert [
        resolve_poster_subject(item).official_artwork_id
        for item in selected
    ] == [10034, 10035, 10062]
    assert (
        fetch_cutouts.cutout_filename(6, "Mega Charizard X", 10034)
        == "pokemon_006_artwork_10034_mega_charizard_x.png"
    )


def test_legacy_featured_element_recovers_form_from_its_source_card():
    scope_data = {
        "sections": {
            "mega": {
                "cards": [
                    {
                        "pokemon_id": 380,
                        "image_url": PosterSubject(380, 10062).image_url,
                        "prefix": "Mega",
                        "tcg_card": {"id": "me01-100"},
                    }
                ],
                "featured_elements": [
                    {
                        "pokemon_id": 380,
                        "pokemon_name": "Latias",
                        "card_id": "me01-100",
                        "image_url": (
                            "https://assets.tcgdex.net/en/me/me01/100/high.png"
                        ),
                    }
                ],
            }
        }
    }

    featured = fetch_cutouts.scope_featured_elements(scope_data)

    assert featured[0]["image_url"].startswith(
        "https://assets.tcgdex.net/"
    )
    assert featured[0]["pokemon_name"] == "Mega Latias"
    subject = resolve_poster_subject(featured[0])
    assert (subject.species_id, subject.official_artwork_id) == (380, 10062)


def test_explicit_featured_subject_must_match_its_source_card():
    scope_data = {
        "sections": {
            "mega": {
                "cards": [
                    {
                        "pokemon_id": 380,
                        "image_url": PosterSubject(380, 10062).image_url,
                        "prefix": "Mega",
                        "tcg_card": {"id": "me01-100"},
                    }
                ],
                "featured_elements": [
                    {
                        "pokemon_id": 380,
                        "card_id": "me01-100",
                        "poster_subject": PosterSubject(
                            380,
                            380,
                        ).as_mapping(),
                    }
                ],
            }
        }
    }

    with pytest.raises(ValueError, match="does not match its source card"):
        fetch_cutouts.scope_featured_elements(scope_data)


def test_poster_subject_rejects_mismatched_or_untrusted_artwork_urls():
    subject = PosterSubject(380, 10062).as_mapping()
    subject["image_url"] = PosterSubject(380, 380).image_url

    with pytest.raises(ValueError, match="does not match"):
        resolve_poster_subject(
            {"pokemon_id": 380, "poster_subject": subject}
        )
    with pytest.raises(ValueError, match="canonical"):
        official_artwork_id_from_url(
            "https://example.test/official-artwork/10062.png"
        )
    with pytest.raises(ValueError, match="belongs to Pokemon #719"):
        PosterSubject(380, 10075)
    with pytest.raises(ValueError, match="not present in the pinned"):
        PosterSubject(380, 10999)
    with pytest.raises(ValueError, match="without an exact"):
        poster_subject_from_card(
            {
                "pokemon_id": 380,
                "prefix": "Mega",
                "image_url": "https://assets.tcgdex.net/card.png",
            }
        )
    with pytest.raises(ValueError, match="without an exact"):
        poster_subject_from_card(
            {
                "pokemon_id": 150,
                "prefix": "[M]",
                "image_url": "https://assets.tcgdex.net/card.png",
            }
        )
    for pokemon_id, marker in ((380, "Mega"), (150, "[M]")):
        with pytest.raises(ValueError, match="without an exact"):
            poster_subject_from_card(
                {
                    "pokemon_id": pokemon_id,
                    "prefix": marker,
                    "image_url": PosterSubject(
                        pokemon_id,
                        pokemon_id,
                    ).image_url,
                }
            )


def test_featured_card_link_must_resolve_before_base_fallback():
    with pytest.raises(ValueError, match="does not exist"):
        fetch_cutouts.scope_featured_elements(
            {
                "sections": {
                    "mega": {
                        "cards": [
                            {
                                "pokemon_id": 380,
                                "image_url": PosterSubject(
                                    380,
                                    10062,
                                ).image_url,
                                "tcg_card": {"id": "me01-100"},
                            }
                        ],
                        "featured_elements": [
                            {
                                "pokemon_id": 380,
                                "card_id": "me01-typo",
                            }
                        ],
                    }
                }
            }
        )


def test_fetch_cutouts_downloads_exact_form_artwork_without_base_fallback(
    tmp_path: Path,
    monkeypatch,
):
    asset_dir = tmp_path / "ExGen3" / "sections" / "mega"
    bundle = SimpleNamespace(
        asset_dir=asset_dir,
        asset_key="ExGen3/sections/mega",
        scope="ExGen3",
        poster_id="mega",
        section_id="mega",
        manifest={
            "layout": {"name": "standard_3x3"},
            "pokemon": {
                "strategy": "featured_from_scope",
                "count": "auto_from_layout_columns",
                "fallback_candidates": [],
            },
        },
    )
    scope_data = {
        "sections": {
            "mega": {
                "featured_elements": [
                    {
                        "pokemon_id": 380,
                        "pokemon_name": "Mega Latias",
                        "poster_subject": PosterSubject(
                            380,
                            10062,
                        ).as_mapping(),
                    },
                    {
                        "pokemon_id": 719,
                        "pokemon_name": "Mega Diancie",
                        "poster_subject": PosterSubject(
                            719,
                            10075,
                        ).as_mapping(),
                    },
                    {
                        "pokemon_id": 448,
                        "pokemon_name": "Mega Lucario",
                        "poster_subject": PosterSubject(
                            448,
                            10059,
                        ).as_mapping(),
                    },
                ]
            }
        }
    }
    requested_urls = []

    monkeypatch.setattr(
        fetch_cutouts,
        "poster_bundle",
        lambda *_args, **_kwargs: bundle,
    )
    monkeypatch.setattr(
        fetch_cutouts,
        "load_poster_scope_data",
        lambda *_args, **_kwargs: scope_data,
    )
    monkeypatch.setattr(fetch_cutouts, "collect_pokedex_names", lambda: {})

    def fake_download(url):
        requested_urls.append(url)
        return b"fixture"

    def fake_save(_payload, path):
        image = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
        for x in range(100, 300):
            for y in range(100, 300):
                image.putpixel((x, y), (30, 120, 220, 255))
        image.save(path)
        return fetch_cutouts.validate_png(path)

    monkeypatch.setattr(fetch_cutouts, "download_bytes", fake_download)
    monkeypatch.setattr(fetch_cutouts, "save_cutout", fake_save)

    assert fetch_cutouts.fetch_cutouts("ExGen3/sections/mega") == 0

    assert requested_urls == [
        PosterSubject(380, 10062).image_url,
        PosterSubject(719, 10075).image_url,
        PosterSubject(448, 10059).image_url,
    ]
    assert PosterSubject(380, 380).image_url not in requested_urls
    payload = json.loads(
        (asset_dir / "cutouts" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["items"][0]["poster_subject"] == PosterSubject(
        380,
        10062,
    ).as_mapping()
    assert (
        payload["items"][0]["file"]
        == "pokemon_380_artwork_10062_mega_latias.png"
    )


def test_individual_promotion_rejects_source_form_cutout_mismatch(
    tmp_path: Path,
):
    asset_dir = tmp_path / "ME03"
    cutout_dir = asset_dir / "cutouts"
    cutout_dir.mkdir(parents=True)
    bundle = SimpleNamespace(
        asset_key="ME03",
        scope="ME03",
        section_id=None,
        asset_dir=asset_dir,
        manifest={
            "layout": {"name": "standard_3x3"},
            "pokemon": {
                "strategy": "featured_from_scope",
                "count": "auto_from_layout_columns",
                "fallback_candidates": [],
            },
        },
    )
    scope_data = {
        "sections": {
            "all": {
                "featured_elements": [
                    {
                        "pokemon_id": 718,
                        "poster_subject": PosterSubject(
                            718,
                            10301,
                        ).as_mapping(),
                    },
                    {"pokemon_id": 495},
                    {"pokemon_id": 722},
                ]
            }
        }
    }
    (cutout_dir / "manifest.json").write_text(
        json.dumps(
            {
                "items": [
                    {
                        "pokemon_id": 718,
                        "url": PosterSubject(718, 718).image_url,
                        "file": "pokemon_718_zygarde.png",
                    },
                    {
                        "pokemon_id": 495,
                        "url": PosterSubject(495, 495).image_url,
                        "file": "pokemon_495_snivy.png",
                    },
                    {
                        "pokemon_id": 722,
                        "url": PosterSubject(722, 722).image_url,
                        "file": "pokemon_722_rowlet.png",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="do not match"):
        poster_validator._validate_source_subjects(bundle, scope_data)


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


def test_cutout_placements_stay_inside_bottom_card_cells():
    scope_dir = Path(__file__).resolve().parents[2] / "data" / "poster_assets" / "Base1"
    placements = cutout_placements(build_page_layout("standard_3x3"), scope_dir)

    for placement in placements:
        alpha_box = placement["image"].getchannel("A").getbbox()
        assert alpha_box is not None
        left = placement["x"] + alpha_box[0]
        top = placement["y"] + alpha_box[1]
        right = placement["x"] + alpha_box[2]
        bottom = placement["y"] + alpha_box[3]
        cell = placement["cell"]
        assert cell.x <= left < right <= cell.x + cell.width
        assert cell.y <= top < bottom <= cell.y + cell.height


def test_tall_conditioning_subjects_gain_card_safe_padding():
    scope_dir = Path(__file__).resolve().parents[2] / "data" / "poster_assets" / "Base1"
    placements = cutout_placements(build_page_layout("standard_3x3"), scope_dir)
    manifest = fetch_cutouts.load_yaml(scope_dir / "poster.yaml")
    conditioned = card_safe_conditioning_placements(placements, manifest)

    assert conditioned[0]["image"].height < placements[0]["image"].height
    assert conditioned[1]["image"].size == placements[1]["image"].size
    assert conditioned[2]["image"].size == placements[2]["image"].size
    original_box = placements[0]["image"].getchannel("A").getbbox()
    conditioned_box = conditioned[0]["image"].getchannel("A").getbbox()
    assert original_box is not None and conditioned_box is not None
    cell = placements[0]["cell"]
    assert (
        placements[0]["y"] + original_box[3] + round(cell.height * 0.10)
        == conditioned[0]["y"] + conditioned_box[3]
    )


def test_sv035_uses_default_conditioning_without_base1_offsets():
    scope_dir = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "poster_assets"
        / "SV03.5"
    )
    placements = cutout_placements(
        build_page_layout("standard_3x3"),
        scope_dir,
    )
    manifest = fetch_cutouts.load_yaml(scope_dir / "poster.yaml")

    conditioned = card_safe_conditioning_placements(placements, manifest)

    assert [
        (item["x"], item["y"], item["image"].size)
        for item in conditioned
    ] == [
        (item["x"], item["y"], item["image"].size)
        for item in placements
    ]


def test_inpaint_reference_uses_exact_final_placements(tmp_path: Path):
    scope_dir = Path(__file__).resolve().parents[2] / "data" / "poster_assets" / "Base1"
    build_scene_reference("Base1", 0.25, tmp_path)

    actual = Image.open(tmp_path / "inpaint_reference.png").convert("RGBA")
    layout = build_page_layout("standard_3x3", width_px=actual.width)
    expected = Image.new("RGBA", actual.size, (226, 224, 211, 0))
    for placement in cutout_placements(layout, scope_dir):
        expected.alpha_composite(
            placement["image"],
            (placement["x"], placement["y"]),
        )

    assert ImageChops.difference(actual, expected).getbbox() is None
    assert ImageChops.difference(
        actual,
        Image.open(tmp_path / "scene_reference.png").convert("RGBA"),
    ).getbbox() is not None


def test_identity_lock_mask_generates_only_above_the_bottom_subject_band(
    tmp_path: Path,
):
    build_scene_reference("Base1", 0.25, tmp_path)

    mask = Image.open(tmp_path / "upper_context_mask.png").convert("RGBA")
    alpha = mask.getchannel("A")
    generation_alpha = Image.open(
        tmp_path / "upper_context_generation_mask.png"
    ).convert("RGBA").getchannel("A")

    assert alpha.getpixel((mask.width // 2, 0)) == 0
    assert 0 < alpha.getpixel((mask.width // 2, round(mask.height * 0.65))) < 255
    assert alpha.getpixel((mask.width // 2, mask.height - 1)) == 255
    assert generation_alpha.getpixel((mask.width // 2, 0)) == 0
    assert generation_alpha.getpixel(
        (mask.width // 2, round(mask.height * 0.70))
    ) == 0
    assert generation_alpha.getpixel(
        (mask.width // 2, mask.height - 1)
    ) == 255


def test_identity_lock_mask_moves_up_for_an_unusually_tall_subject(
    tmp_path: Path,
):
    subject = Image.new("RGBA", (20, 30), (40, 80, 120, 255))
    transition_start, protected_start = build_upper_context_mask(
        100,
        100,
        [{"image": subject, "x": 40, "y": 55}],
        {"artwork": {"identity_lock": {"subject_clearance_ratio": 0.02}}},
        tmp_path,
    )

    assert protected_start == 53
    assert transition_start == 43
    alpha = Image.open(
        tmp_path / "upper_context_mask.png"
    ).convert("RGBA").getchannel("A")
    assert alpha.getpixel((50, transition_start - 1)) == 0
    assert alpha.getpixel((50, protected_start)) == 255
    generation_alpha = Image.open(
        tmp_path / "upper_context_generation_mask.png"
    ).convert("RGBA").getchannel("A")
    assert generation_alpha.getpixel((50, protected_start)) == 0
    assert generation_alpha.getpixel((50, 55)) == 255


def test_canny_structure_reference_flattens_exact_placements_on_white(
    tmp_path: Path,
):
    scope_dir = Path(__file__).resolve().parents[2] / "data" / "poster_assets" / "Base1"
    build_scene_reference("Base1", 0.25, tmp_path)

    actual = Image.open(tmp_path / "structure_reference.png").convert("RGB")
    layout = build_page_layout("standard_3x3", width_px=actual.width)
    expected = Image.new("RGBA", actual.size, (255, 255, 255, 255))
    for placement in cutout_placements(layout, scope_dir):
        expected.alpha_composite(
            placement["image"],
            (placement["x"], placement["y"]),
        )

    assert ImageChops.difference(
        actual,
        expected.convert("RGB"),
    ).getbbox() is None


def test_qwen_identity_references_prioritize_first_subject_detail(
    tmp_path: Path,
):
    build_scene_reference("Base1", 0.25, tmp_path)

    first = Image.open(
        tmp_path / "qwen_identity_reference_1.png"
    ).convert("RGB")
    remaining = Image.open(
        tmp_path / "qwen_identity_reference_2.png"
    ).convert("RGB")
    assert first.size == (512, 640)
    assert remaining.size == (1024, 640)

    first_box = ImageChops.difference(
        first,
        Image.new("RGB", first.size, (226, 224, 211)),
    ).getbbox()
    remaining_box = ImageChops.difference(
        remaining,
        Image.new("RGB", remaining.size, (226, 224, 211)),
    ).getbbox()
    assert first_box is not None
    assert remaining_box is not None
    assert first_box[2] - first_box[0] >= 300
    assert first_box[3] - first_box[1] >= 400


def test_identity_references_use_scale_aware_appearance_canvases(tmp_path: Path):
    scope_dir = Path(__file__).resolve().parents[2] / "data" / "poster_assets" / "Base1"
    manifest = fetch_cutouts.load_yaml(scope_dir / "poster.yaml")

    build_identity_references(scope_dir, manifest, tmp_path)

    layout = build_page_layout("standard_3x3", width_px=848)
    extents = []
    for index in range(1, layout.pokemon_count + 1):
        image = Image.open(
            tmp_path / f"identity_reference_{index}.png"
        ).convert("RGB")
        expected_size = (768, 768) if index == 1 else (512, 512)
        assert image.size == expected_size
        neutral = Image.new("RGB", image.size, (226, 224, 211))
        bbox = ImageChops.difference(image, neutral).getbbox()
        assert bbox is not None
        assert bbox[0] > 0
        assert bbox[1] > 0
        assert bbox[2] < image.width
        assert bbox[3] <= image.height - 24
        assert bbox[2] - bbox[0] <= 350
        assert bbox[3] - bbox[1] <= 350
        extents.append(max(bbox[2] - bbox[0], bbox[3] - bbox[1]))
    assert extents[0] < extents[1]
    assert extents[0] < extents[2]
    assert extents[2] == 350


def test_identity_references_use_explicit_nested_asset_key(
    tmp_path: Path,
    monkeypatch,
):
    scope_dir = Path(__file__).resolve().parents[2] / "data" / "poster_assets" / "Base1"
    manifest = fetch_cutouts.load_yaml(scope_dir / "poster.yaml")
    requested_assets = []

    def fake_output_dimensions(asset_key, _megapixels):
        requested_assets.append(asset_key)
        return 848, 1168

    monkeypatch.setattr(
        "scripts.poster_assets.prepare_comfyui_poster.output_dimensions",
        fake_output_dimensions,
    )

    build_identity_references(
        scope_dir,
        manifest,
        tmp_path,
        asset_key="Pokedex/sections/gen1",
    )

    assert requested_assets == ["Pokedex/sections/gen1"]


def test_identity_prompt_is_manifest_driven():
    items = [
        {"pokemon_id": 1, "name_en": "Alpha"},
        {"pokemon_id": 2, "name_en": "Beta"},
    ]
    manifest = {
        "conditioning": {
            "subjects": {
                2: {
                    "prompt_notes": [
                        "Keep the crescent marking unchanged.",
                    ]
                }
            }
        }
    }

    prompt = build_identity_reference_prompt(items, manifest)

    assert "IMAGE 1" in prompt and "left region" in prompt
    assert "IMAGE 2" in prompt and "right region" in prompt
    assert "IMAGE 3 is the sole and final authority" in prompt
    assert "Beta-specific constraints" in prompt
    assert "crescent marking" in prompt
    assert "Mewtwo" not in prompt


def test_identity_lock_scene_prompt_is_scope_and_layout_driven():
    manifest = {
        "scope": "Example",
        "layout": {"name": "wide_4x4"},
        "text_cells": {
            "title": {"row": 1, "column": 3},
            "set_info": {"row": 2, "column": 3},
        },
        "artwork": {
            "scene": {
                "ground_noun": "shore",
                "constraints": [
                    "Distant basalt arches echo the expansion theme.",
                ],
            }
        },
    }
    scope_data = {
        "name": "Aurora Archive",
        "serie_name": "Example Series",
        "release_date": "2024-02-03",
    }

    prompt = build_identity_lock_prompt(manifest, scope_data)

    assert "Aurora Archive expansion" in prompt
    assert "from the Example Series" in prompt
    assert "released in 2024" in prompt
    assert "upper-column-3" in prompt
    assert "row-2-column-3" in prompt
    assert "uninterrupted, low-detail atmosphere" in prompt
    assert "later exact set logo" not in prompt
    assert "later deterministic set information" not in prompt
    assert "continuous low shore surface" in prompt
    assert "basalt arches" in prompt
    assert "source pixel as immutable" in prompt
    assert "landing pads" in prompt
    assert "Mewtwo" not in prompt


def test_identity_lock_geometry_defaults_scale_with_output_size():
    manifest: dict = {}

    assert identity_lock_config(manifest) == {
        "overscan_ratio": 0.04,
        "max_protected_start_ratio": 0.70,
        "transition_ratio": 0.10,
        "subject_clearance_ratio": 0.02,
    }
    assert identity_lock_overscan(848, 1168, manifest) == (880, 1216)
    assert identity_lock_overscan(1696, 2336, manifest) == (1760, 2432)


def test_new_tcg_set_manifest_bootstraps_the_dynamic_identity_lock_flow():
    scope_data = {
        "type": "tcg_set",
        "name": "Aurora Archive",
        "release_date": "2024-02-03",
        "available_languages": ["de", "en", "fr"],
        "logo_urls": {
            "de": "https://example.test/de.png",
            "en": "https://example.test/en.png",
            "fr": "https://example.test/fr.png",
        },
    }
    generation_template = {
        "engine": "flux",
        "model": "model.safetensors",
        "model_sha256": "model-hash",
        "encoder": "encoder.safetensors",
        "encoder_sha256": "encoder-hash",
        "vae": "vae.safetensors",
        "vae_sha256": "vae-hash",
        "upscale_model": "upscale.pth",
        "upscale_model_sha256": "upscale-hash",
    }

    manifest = build_default_manifest(
        "EX42",
        scope_data,
        "wide_4x3",
        generation_template,
    )

    assert manifest["scope"] == "EX42"
    assert manifest["layout"]["name"] == "wide_4x3"
    assert manifest["pokemon"]["count"] == "auto_from_layout_columns"
    assert manifest["artwork"]["generation"]["mode"] == "identity_lock"
    assert (
        manifest["artwork"]["generation"]["reference_mode"]
        == "two_pass_source_pixels"
    )
    assert manifest["artwork"]["generation"]["seed"] == stable_scope_seed(
        "EX42"
    )
    assert manifest["pdf"]["enabled"] is False
    assert manifest["title_logo"]["files"] == {
        "de": "logos/logo-de.png",
        "en": "logos/logo-en.png",
        "fr": "logos/logo-fr.png",
    }
    prompt = build_identity_lock_prompt(manifest, scope_data)
    assert "Aurora Archive expansion" in prompt
    assert "upper-column-2" in prompt
    assert "middle-column-2" in prompt


def test_every_current_tcg_set_bootstraps_without_set_specific_python():
    root = Path(__file__).resolve().parents[2]
    generation_template = fetch_cutouts.load_yaml(
        root / "data" / "poster_assets" / "Base1" / "poster.yaml"
    )["artwork"]["generation"]
    checked = []
    for scope_path in sorted((root / "data" / "output").glob("*.json")):
        scope_data = fetch_cutouts.load_json(scope_path)
        if scope_data.get("type") != "tcg_set":
            continue
        scene = scene_for_scope(scope_path.stem)
        manifest = build_default_manifest(
            scope_path.stem,
            scope_data,
            "standard_3x3",
            generation_template,
            scene,
        )
        selected = fetch_cutouts.select_pokemon(
            manifest,
            scope_data,
            3,
            {},
        )
        prompt = build_identity_lock_prompt(manifest, scope_data)

        assert len(selected) == 3
        assert len({item["pokemon_id"] for item in selected}) == 3
        assert scene["concept"] in prompt
        assert manifest["artwork"]["scene"]["setting"] in prompt
        assert "source pixel as immutable" in prompt
        checked.append(scope_path.stem)

    assert len(checked) >= 24
    assert "Base1" in checked
    assert "SV03.5" in checked


def test_scene_catalog_covers_every_current_individual_tcg_set_exactly():
    missing, stale = validate_catalog_coverage()
    scenes = load_scene_catalog()

    assert missing == set()
    assert stale == set()
    assert set(available_tcg_scopes()) == set(scenes)
    assert all(scene["setting"] for scene in scenes.values())
    assert all("safe_areas" not in scene for scene in scenes.values())


def test_runner_uses_the_scope_generation_contract_as_its_defaults():
    root = Path(__file__).resolve().parents[2]
    manifest = fetch_cutouts.load_yaml(
        root / "data" / "poster_assets" / "Base1" / "poster.yaml"
    )

    assert configured_generation("Base1") == manifest["artwork"]["generation"]


def test_runner_cli_resolves_production_defaults_from_the_scope(
    monkeypatch,
    tmp_path,
):
    captured = {}

    def fake_run(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return (
            tmp_path / "raw.png",
            tmp_path / "artwork.png",
            tmp_path / "final.png",
            tmp_path / "run.json",
        )

    monkeypatch.setattr(poster_runner, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_comfyui_poster.py", "--scope", "Base1"],
    )

    assert poster_runner.main() == 0

    generation = configured_generation("Base1")
    assert captured["args"][1] == generation["seed"]
    assert captured["args"][2] == generation["generation_megapixels"]
    assert captured["kwargs"]["engine"] == generation["engine"]
    assert captured["kwargs"]["flux_mode"] == generation["mode"]
    assert captured["kwargs"]["flux_model"] == generation["model"]
    assert captured["kwargs"]["flux_steps"] == generation["steps"]
    assert captured["kwargs"]["flux_clip"] == generation["encoder"]
    assert captured["kwargs"]["output_dpi"] == generation["output_dpi"]
    assert captured["kwargs"]["upscale_model"] == generation["upscale_model"]


def test_localized_title_logo_falls_back_to_english():
    manifest = {
        "title_logo": {
            "files": {
                "en": "logo-en.png",
                "de": "logo-de.png",
            }
        }
    }

    assert title_logo_file(manifest, "de") == "logo-de.png"
    assert title_logo_file(manifest, "fr") == "logo-en.png"


def test_title_logo_downloads_use_scope_language_urls():
    manifest = {
        "title_logo": {
            "files": {
                "de": "logos/logo-de.png",
                "en": "logos/logo-en.png",
            }
        }
    }
    scope_data = {
        "logo_urls": {
            "de": "https://example.test/de.png",
            "en": "https://example.test/en.png",
        }
    }

    assert resolve_logo_downloads(manifest, scope_data) == [
        ("de", "logos/logo-de.png", "https://example.test/de.png"),
        ("en", "logos/logo-en.png", "https://example.test/en.png"),
    ]


def test_info_panel_is_centered_and_height_limited():
    cell = build_page_layout("standard_3x3", width_px=848).cell(2, 2)

    box = info_panel_box(
        cell,
        {"max_width_ratio": 0.92, "max_height_ratio": 0.68},
    )

    assert abs((box[0] + box[2]) / 2 - cell.center[0]) <= 0.5
    assert abs((box[1] + box[3]) / 2 - cell.center[1]) <= 0.5
    assert box[3] - box[1] <= round(cell.height * 0.68)


def test_info_panel_shrinks_long_set_names_to_their_row():
    box = (0, 0, 180, 52)
    text = "A Very Long Localized Trading Card Expansion Name"

    font = fitted_font(
        text,
        box,
        preferred_size=28,
        minimum_size=10,
        bold=True,
    )
    lines = wrap_text(text, font, box[2] - box[0])
    line_heights = [
        bounds[3] - bounds[1]
        for bounds in (font.getbbox(line) for line in lines)
    ]
    total_height = sum(line_heights) + max(0, len(lines) - 1) * round(
        font.size * 0.28
    )

    assert font.size < 28
    assert total_height <= box[3] - box[1]


def test_long_localized_title_stays_inside_its_panel():
    canvas = Image.new("RGBA", (848, 1168), (0, 0, 0, 0))
    title_cell = build_page_layout(
        "standard_3x3",
        width_px=canvas.width,
    ).cell(1, 2)

    panel_box = draw_title_text_panel(
        canvas,
        title_cell,
        "Mega Pokémon ex",
        "en",
    )

    pixels = canvas.load()
    text_points = [
        (x, y)
        for y in range(canvas.height)
        for x in range(canvas.width)
        if pixels[x, y][:3] == (35, 65, 42)
        and pixels[x, y][3] == 255
    ]
    assert text_points
    assert min(x for x, _y in text_points) >= panel_box[0]
    assert max(x for x, _y in text_points) < panel_box[2]
    assert min(y for _x, y in text_points) >= panel_box[1]
    assert max(y for _x, y in text_points) < panel_box[3]


def test_comfyui_inpaint_uses_source_once_without_reference_conditioning():
    workflow = build_workflow(
        "Base1", seed=123, megapixels=0.25, generation_mode="inpaint"
    )
    loaded_images = {
        node["inputs"]["image"]
        for node in workflow.values()
        if node["class_type"] == "LoadImage"
    }

    assert loaded_images == {"inpaint_reference.png"}
    assert not any(node["class_type"] == "ReferenceLatent" for node in workflow.values())
    assert any(node["class_type"] == "VAEEncodeForInpaint" for node in workflow.values())
    assert workflow["18"] == {
        "class_type": "ImageCompositeMasked",
        "inputs": {
            "destination": ["14", 0],
            "source": ["12", 0],
            "x": 0,
            "y": 0,
            "resize_source": False,
            "mask": ["14", 1],
        },
    }
    assert workflow["13"]["inputs"]["images"] == ["18", 0]
    assert workflow["9"]["inputs"]["positive"] == ["4", 0]
    assert workflow["15"]["inputs"]["grow_mask_by"] == 0


def test_comfyui_identity_lock_uses_clean_ground_then_upper_context_pass():
    workflow = build_workflow(
        "Base1",
        seed=123,
        megapixels=0.25,
        generation_mode="identity_lock",
    )

    assert {
        node["inputs"]["image"]
        for node in workflow.values()
        if node["class_type"] == "LoadImage"
    } == {
        "inpaint_reference.png",
        "upper_context_generation_mask.png",
        "upper_context_mask.png",
    }
    assert workflow["15"]["class_type"] == "EmptySD3LatentImage"
    assert workflow["15"]["inputs"]["width"] > workflow["27"]["inputs"]["width"]
    assert workflow["15"]["inputs"]["height"] > workflow["27"]["inputs"]["height"]
    assert workflow["11"]["inputs"]["latent_image"] == ["15", 0]
    assert workflow["26"]["class_type"] == "Flux2Scheduler"
    assert workflow["26"]["inputs"]["width"] == workflow["27"]["inputs"]["width"]
    assert workflow["26"]["inputs"]["height"] == workflow["27"]["inputs"]["height"]
    assert workflow["27"]["class_type"] == "ImageCrop"
    assert workflow["27"]["inputs"]["image"] == ["12", 0]
    assert workflow["19"]["class_type"] == "ImageCompositeMasked"
    assert workflow["19"]["inputs"]["destination"] == ["27", 0]
    assert workflow["19"]["inputs"]["source"] == ["14", 0]
    assert workflow["21"]["class_type"] == "VAEEncodeForInpaint"
    assert workflow["21"]["inputs"]["pixels"] == ["19", 0]
    assert workflow["21"]["inputs"]["mask"] == ["28", 1]
    assert workflow["22"]["inputs"]["noise_seed"] == 124
    assert workflow["23"]["inputs"]["latent_image"] == ["21", 0]
    assert workflow["23"]["inputs"]["sigmas"] == ["26", 0]
    assert workflow["25"]["inputs"]["destination"] == ["19", 0]
    assert workflow["25"]["inputs"]["source"] == ["24", 0]
    assert workflow["25"]["inputs"]["mask"] == ["20", 1]
    assert workflow["13"]["inputs"]["images"] == ["25", 0]
    assert not any(
        node["class_type"] == "ReferenceLatent"
        for node in workflow.values()
    )


def test_comfyui_edit_uses_reference_with_independent_empty_target():
    workflow = build_workflow(
        "Base1",
        seed=123,
        megapixels=0.25,
        generation_mode="edit",
        reference_mode="composition",
    )

    assert workflow["15"]["class_type"] == "EmptySD3LatentImage"
    assert workflow["16"]["class_type"] == "VAEEncode"
    assert workflow["17"]["class_type"] == "ReferenceLatent"
    assert workflow["17"]["inputs"]["latent"] == ["16", 0]
    assert workflow["11"]["inputs"]["latent_image"] == ["15", 0]
    assert not any(node["class_type"] == "VAEEncodeForInpaint" for node in workflow.values())
    assert not any(node["class_type"] == "ImageCompositeMasked" for node in workflow.values())


def test_comfyui_identity_mode_appends_three_scale_aware_identity_references():
    workflow = build_workflow(
        "Base1",
        seed=123,
        megapixels=0.25,
        generation_mode="edit",
        reference_mode="identity",
    )

    loaded_images = [
        node["inputs"]["image"]
        for node in workflow.values()
        if node["class_type"] == "LoadImage"
    ]
    assert loaded_images == [
        "scene_reference.png",
        "identity_reference_1.png",
        "identity_reference_2.png",
        "identity_reference_3.png",
    ]
    assert sum(
        node["class_type"] == "ReferenceLatent" for node in workflow.values()
    ) == 4
    assert workflow["25"]["inputs"]["conditioning"] == ["4", 0]
    assert workflow["28"]["inputs"]["conditioning"] == ["25", 0]
    assert workflow["31"]["inputs"]["conditioning"] == ["28", 0]
    assert workflow["17"]["inputs"]["conditioning"] == ["31", 0]
    assert workflow["9"]["inputs"]["positive"] == ["17", 0]


def test_sv035_workflow_uses_its_own_dynamic_cast_contract():
    workflow = build_workflow(
        "SV03.5",
        seed=123,
        megapixels=0.25,
        generation_mode="edit",
        reference_mode="identity",
    )
    prompt = workflow["4"]["inputs"]["text"]

    assert "Bulbasaur" in prompt
    assert "Charmander" in prompt
    assert "Squirtle" in prompt
    assert "Mewtwo" not in prompt
    assert {
        node["inputs"]["image"]
        for node in workflow.values()
        if node["class_type"] == "LoadImage"
    } == {
        "scene_reference.png",
        "identity_reference_1.png",
        "identity_reference_2.png",
        "identity_reference_3.png",
    }


def test_anima_workflow_uses_cosmos_reference_without_changing_flux_workflow():
    workflow = build_anima_workflow("Base1", seed=123, megapixels=0.25)
    assert any(node["class_type"] == "ApplyCosmosReferenceLatent" for node in workflow.values())
    assert any(node["class_type"] == "LoraLoaderModelOnly" for node in workflow.values())
    assert any(node["class_type"] == "ImageCompositeMasked" for node in workflow.values())
    assert {
        node["inputs"]["image"]
        for node in workflow.values()
        if node["class_type"] == "LoadImage"
    } == {"scene_reference.png"}
    sampler = next(node for node in workflow.values() if node["class_type"] == "KSampler")
    assert sampler["inputs"]["latent_image"] == ["10", 0]


def test_flux1_canny_workflow_binds_original_structure():
    workflow = build_flux1_canny_workflow(
        "Base1",
        seed=123,
        megapixels=1.0,
        control_strength=0.8,
    )

    assert workflow["1"] == {
        "class_type": "UnetLoaderGGUF",
        "inputs": {"unet_name": "flux1-dev-Q4_K_S.gguf"},
    }
    assert workflow["2"]["class_type"] == "DualCLIPLoaderGGUF"
    assert workflow["7"]["inputs"]["image"] == "structure_reference.png"
    assert workflow["8"]["class_type"] == "Canny"
    assert workflow["9"]["class_type"] == "ControlNetLoader"
    assert workflow["10"]["class_type"] == "ControlNetApplySD3"
    assert workflow["10"]["inputs"]["strength"] == 0.8
    assert workflow["12"]["inputs"]["steps"] == 20
    assert workflow["12"]["inputs"]["cfg"] == 1.0
    assert not any(
        node["class_type"] in {"ReferenceLatent", "ImageCompositeMasked"}
        for node in workflow.values()
    )


def test_qwen_edit_workflow_separates_composition_and_detail_references():
    workflow = build_qwen_edit_workflow(
        "Base1",
        seed=123,
        megapixels=1.0,
    )

    assert workflow["1"]["class_type"] == "UnetLoaderGGUF"
    assert workflow["5"]["inputs"]["type"] == "qwen_image"
    assert [
        workflow[node_id]["inputs"]["image"]
        for node_id in ("7", "8", "9")
    ] == [
        "structure_reference.png",
        "qwen_identity_reference_1.png",
        "qwen_identity_reference_2.png",
    ]
    assert workflow["10"]["class_type"] == "TextEncodeQwenImageEditPlus"
    assert workflow["10"]["inputs"]["image1"] == ["7", 0]
    assert workflow["10"]["inputs"]["image2"] == ["8", 0]
    assert workflow["10"]["inputs"]["image3"] == ["9", 0]
    assert "Mewtwo" in workflow["10"]["inputs"]["prompt"]
    assert workflow["12"]["inputs"]["reference_latents_method"] == (
        "index_timestep_zero"
    )
    assert workflow["15"]["inputs"]["steps"] == 4
    assert workflow["15"]["inputs"]["cfg"] == 1.0
    assert workflow["15"]["inputs"]["latent_image"] == ["14", 0]


def test_engine_workflows_have_separate_files(tmp_path: Path):
    flux = write_engine_workflow(
        "flux", "Base1", 123, 0.25, workflow_output_dir=tmp_path
    )
    anima = write_engine_workflow(
        "anima", "Base1", 123, 0.25, workflow_output_dir=tmp_path
    )
    flux1 = write_engine_workflow(
        "flux1_canny",
        "Base1",
        123,
        0.25,
        workflow_output_dir=tmp_path,
    )
    qwen = write_engine_workflow(
        "qwen_edit",
        "Base1",
        123,
        0.25,
        workflow_output_dir=tmp_path,
    )
    assert flux.name == "workflow_api_identity_lock_0p25mp_123.json"
    assert anima.name == "anima_workflow_api.json"
    assert flux1.name == "flux1_canny_workflow_api_0p25_123.json"
    assert qwen.name == "qwen_edit_workflow_api_0p25_123.json"


def test_flux_workflow_files_are_unique_per_seed(tmp_path: Path):
    first = write_engine_workflow(
        "flux", "Base1", 123, 0.25, workflow_output_dir=tmp_path
    )
    second = write_engine_workflow(
        "flux", "Base1", 124, 0.25, workflow_output_dir=tmp_path
    )
    full_size = write_engine_workflow(
        "flux", "Base1", 123, 1.0, workflow_output_dir=tmp_path
    )

    assert first != second
    assert first != full_size


def test_comfyui_server_scope_is_read_from_input_directory(monkeypatch, tmp_path):
    expected = tmp_path / "scope" / "comfyui_poster"
    main_path = tmp_path / "ComfyUI" / "main.py"
    monkeypatch.setattr(
        "scripts.poster_assets.queue_comfyui_workflow.request_json",
        lambda _url: {
            "system": {
                "argv": [
                    str(main_path),
                    "--input-directory",
                    str(expected),
                ]
            }
        },
    )

    assert server_input_directory("http://example.test") == expected.resolve()
    assert server_comfyui_root("http://example.test") == main_path.parent.resolve()
    validate_server_input_directory("http://example.test", expected)


def test_comfyui_server_rejects_another_scope(monkeypatch, tmp_path):
    actual = tmp_path / "Base1" / "comfyui_poster"
    expected = tmp_path / "SV03.5" / "comfyui_poster"
    monkeypatch.setattr(
        "scripts.poster_assets.queue_comfyui_workflow.request_json",
        lambda _url: {
            "system": {
                "argv": [f"--input-directory={actual}"],
            }
        },
    )

    try:
        validate_server_input_directory("http://example.test", expected)
    except RuntimeError as error:
        assert "input directory mismatch" in str(error)
        assert "same --scope" in str(error)
    else:
        raise AssertionError("scope mismatch was accepted")


def test_flux_model_and_steps_are_selectable():
    workflow = build_workflow(
        "Base1",
        seed=123,
        megapixels=0.25,
        unet_name="flux-2-klein-base-4b-fp8.safetensors",
        generation_mode="inpaint",
        steps=24,
        clip_name="qwen_3_8b_fp4mixed.safetensors",
    )

    assert workflow["1"]["inputs"]["unet_name"] == "flux-2-klein-base-4b-fp8.safetensors"
    assert workflow["7"]["inputs"]["steps"] == 24
    assert workflow["2"]["inputs"]["clip_name"] == "qwen_3_8b_fp4mixed.safetensors"


def test_upscale_workflow_uses_model_then_exact_print_dimensions():
    workflow = build_upscale_workflow(
        "Base1",
        "temp/candidate.png",
        dpi=300,
        model_name="example-upscaler.pth",
    )

    assert workflow["1"]["inputs"]["image"] == "temp/candidate.png"
    assert workflow["2"]["inputs"]["model_name"] == "example-upscaler.pth"
    assert workflow["3"]["class_type"] == "ImageUpscaleWithModel"
    assert workflow["4"]["inputs"]["width"] == 2368
    assert workflow["4"]["inputs"]["height"] == 3268
    assert workflow["4"]["inputs"]["crop"] == "disabled"


def test_upscale_input_normalizes_to_physical_aspect_ratio(
    tmp_path: Path,
    monkeypatch,
):
    assets_root = tmp_path / "poster_assets"
    scope_dir = assets_root / "Example"
    scope_dir.mkdir(parents=True)
    (scope_dir / "poster.yaml").write_text(
        "layout:\n  name: standard_3x3\n",
        encoding="utf-8",
    )
    source = tmp_path / "source.png"
    destination = tmp_path / "normalized.png"
    Image.new("RGB", (608, 832), (40, 90, 140)).save(source)
    monkeypatch.setattr(poster_upscale, "POSTER_ASSETS", assets_root)

    poster_upscale.normalize_upscale_input(
        "Example",
        source,
        destination,
    )

    assert Image.open(destination).size == (
        608,
        build_page_layout("standard_3x3", width_px=608).height_px,
    )


def test_print_dpi_survives_finalization_and_card_slicing(tmp_path: Path):
    raw_path = tmp_path / "raw.png"
    final_path = tmp_path / "final.png"
    card_dir = tmp_path / "cards"
    layout = build_print_layout("standard_3x3", 300)
    Image.new(
        "RGB",
        (layout.width_px, layout.height_px),
        (80, 140, 90),
    ).save(raw_path, dpi=(300, 300))

    finalize("Base1", raw_path, final_path)
    cards = slice_poster("Base1", final_path, card_dir)

    assert abs(Image.open(final_path).info["dpi"][0] - 300) < 0.1
    assert len(cards) == 9
    assert all(
        abs(Image.open(path).info["dpi"][0] - 300) < 0.1
        for path in cards
    )


def test_finalizer_preserves_size_and_adds_deterministic_panels(tmp_path: Path):
    raw_path = tmp_path / "raw.png"
    final_path = tmp_path / "final.png"
    Image.new("RGB", (432, 608), (80, 140, 90)).save(raw_path)

    finalize("Base1", raw_path, final_path)

    raw = Image.open(raw_path).convert("RGB")
    final = Image.open(final_path).convert("RGB")
    assert final.size == raw.size
    assert ImageChops.difference(raw, final).getbbox() is not None
    # The lower character area belongs exclusively to the generated artwork.
    assert final.getpixel((raw.width // 4, raw.height * 5 // 6)) == raw.getpixel(
        (raw.width // 4, raw.height * 5 // 6)
    )


def test_raw_artwork_validation_rejects_blank_output(tmp_path: Path):
    blank = tmp_path / "blank.png"
    Image.new("RGB", (64, 64), (0, 0, 0)).save(blank)

    try:
        validate_raw_artwork(blank)
    except RuntimeError as error:
        assert "blank or near-constant" in str(error)
    else:
        raise AssertionError("blank artwork was accepted")


def test_identity_lock_validation_requires_exact_opaque_source_pixels(
    tmp_path: Path,
):
    reference_path = tmp_path / "inpaint_reference.png"
    raw_path = tmp_path / "raw.png"
    reference = Image.new("RGBA", (12, 12), (0, 0, 0, 0))
    for y in range(3, 9):
        for x in range(2, 10):
            reference.putpixel((x, y), (40, 120, 210, 255))
    reference.save(reference_path)
    raw = Image.new("RGB", reference.size, (230, 220, 180))
    raw.paste(reference.convert("RGB"), mask=reference.getchannel("A"))
    raw.save(raw_path)

    validation = validate_identity_lock_pixels(
        "Example",
        raw_path,
        reference_path,
    )

    assert validation == {
        "method": "exact_opaque_source_pixels",
        "opaque_pixels": 48,
        "changed_pixels": 0,
        "passed": True,
    }

    raw.putpixel((4, 5), (41, 120, 210))
    raw.save(raw_path)
    try:
        validate_identity_lock_pixels(
            "Example",
            raw_path,
            reference_path,
        )
    except RuntimeError as error:
        assert "changed fully opaque source pixels" in str(error)
    else:
        raise AssertionError("Changed identity-lock source pixel was accepted")


def test_resize_artwork_uses_requested_poster_dimensions(tmp_path: Path):
    source = tmp_path / "source.png"
    destination = tmp_path / "resized.png"
    artwork = Image.new("RGB", (64, 96), (40, 120, 80))
    artwork.paste((120, 180, 220), (0, 0, 64, 48))
    artwork.save(source)

    resize_artwork("Base1", source, destination, 0.25)

    assert Image.open(destination).size == (432, 596)


def test_generation_hashes_describe_selected_comfyui_model_files(
    tmp_path: Path,
):
    model = tmp_path / "models" / "diffusion_models" / "matching.safetensors"
    encoder = tmp_path / "models" / "text_encoders" / "encoder.safetensors"
    encoder_2 = tmp_path / "models" / "clip" / "encoder.gguf"
    controlnet = tmp_path / "models" / "controlnet" / "canny.safetensors"
    lora = tmp_path / "models" / "loras" / "identity.safetensors"
    model.parent.mkdir(parents=True)
    encoder.parent.mkdir(parents=True)
    encoder_2.parent.mkdir(parents=True)
    controlnet.parent.mkdir(parents=True)
    lora.parent.mkdir(parents=True)
    model.write_bytes(b"model")
    encoder.write_bytes(b"encoder")
    encoder_2.write_bytes(b"encoder-2")
    controlnet.write_bytes(b"controlnet")
    lora.write_bytes(b"lora")

    enriched = add_model_artifact_hashes(
        tmp_path,
        {
            "model": "matching.safetensors",
            "encoder": "encoder.safetensors",
            "encoder_2": "encoder.gguf",
            "controlnet": "canny.safetensors",
            "lora": "identity.safetensors",
        },
    )

    assert enriched["model_sha256"] == sha256_file(model)
    assert enriched["encoder_sha256"] == sha256_file(encoder)
    assert enriched["encoder_2_sha256"] == sha256_file(encoder_2)
    assert enriched["controlnet_sha256"] == sha256_file(controlnet)
    assert enriched["lora_sha256"] == sha256_file(lora)


def test_identity_lock_provenance_excludes_unused_edit_references(
    tmp_path: Path,
    monkeypatch,
):
    scope_dir = tmp_path / "Example"
    work_dir = scope_dir / "comfyui_poster"
    cutout_dir = scope_dir / "cutouts"
    work_dir.mkdir(parents=True)
    cutout_dir.mkdir()
    (scope_dir / "poster.yaml").write_text("scope: Example\n", encoding="utf-8")
    (cutout_dir / "manifest.json").write_text(
        json.dumps({"items": [{"file": "subject.png"}]}),
        encoding="utf-8",
    )
    Image.new("RGBA", (8, 8), (10, 20, 30, 255)).save(
        cutout_dir / "subject.png"
    )
    Image.new("RGBA", (8, 8), (10, 20, 30, 255)).save(
        work_dir / "inpaint_reference.png"
    )
    Image.new("RGBA", (8, 8), (0, 0, 0, 0)).save(
        work_dir / "upper_context_mask.png"
    )
    Image.new("RGBA", (8, 8), (0, 0, 0, 0)).save(
        work_dir / "upper_context_generation_mask.png"
    )
    Image.new("RGB", (8, 8), (10, 20, 30)).save(
        work_dir / "identity_reference_1.png"
    )
    (work_dir / IDENTITY_LOCK_PROMPT_FILE).write_text(
        "scene",
        encoding="utf-8",
    )
    workflow = work_dir / "workflow.json"
    workflow.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(
        "scripts.poster_assets.provenance.POSTER_ASSETS",
        tmp_path,
    )

    records = generation_input_records(
        "Example",
        workflow,
        {
            "engine": "flux",
            "mode": "identity_lock",
            "reference_mode": "two_pass_source_pixels",
        },
    )

    assert [record["file"] for record in records["references"]] == [
        "inpaint_reference.png",
        "upper_context_mask.png",
        "upper_context_generation_mask.png",
    ]


def test_slice_poster_exports_every_card_without_binder_gaps(tmp_path: Path):
    source = tmp_path / "poster.png"
    layout = build_page_layout("standard_3x3", width_px=848)
    Image.new("RGB", (layout.width_px, layout.height_px), (40, 120, 80)).save(source)

    outputs = slice_poster("Base1", source, tmp_path / "cards")

    assert len(outputs) == 9
    assert [path.name for path in outputs] == [
        f"card_r{row}_c{column}.png"
        for row in range(1, 4)
        for column in range(1, 4)
    ]
    assert all(
        Image.open(path).size == (layout.card_width_px, layout.card_height_px)
        for path in outputs
    )


def _promotion_fixture(tmp_path: Path, monkeypatch):
    assets_root = tmp_path / "poster_assets"
    scope_dir = assets_root / "Example"
    scope_dir.mkdir(parents=True)
    (scope_dir / "poster.yaml").write_text(
        (
            "scope: Example\n"
            "layout:\n"
            "  name: standard_3x3\n"
            "artwork:\n"
            "  generation:\n"
            "    engine: test\n"
        ),
        encoding="utf-8",
    )
    layout = build_page_layout("standard_3x3", width_px=200)
    artwork = tmp_path / "candidate.png"
    Image.new(
        "RGB",
        (layout.width_px, layout.height_px),
        (40, 120, 80),
    ).save(artwork)
    run_metadata = tmp_path / "candidate.run.json"
    run_metadata.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "kind": "poster_generation_run",
                "scope": "Example",
                "generation": {"engine": "test"},
                "source_artwork": {"sha256": sha256_file(artwork)},
            }
        ),
        encoding="utf-8",
    )

    def fake_finalize(_scope, source, destination, _language):
        shutil.copyfile(source, destination)
        return destination

    def fake_slice(_scope, source, output_dir):
        output_dir.mkdir(parents=True)
        image = Image.open(source)
        outputs = []
        for row in range(1, 4):
            for column in range(1, 4):
                path = output_dir / f"card_r{row}_c{column}.png"
                image.crop((0, 0, 32, 32)).save(path)
                outputs.append(path)
        return outputs

    monkeypatch.setattr(poster_promotion, "POSTER_ASSETS", assets_root)
    monkeypatch.setattr(poster_promotion, "finalize", fake_finalize)
    monkeypatch.setattr(poster_promotion, "slice_poster", fake_slice)
    return scope_dir, artwork, run_metadata


def test_promotion_installs_complete_bundle_with_stable_provenance(
    tmp_path: Path,
    monkeypatch,
):
    scope_dir, artwork, run_metadata = _promotion_fixture(
        tmp_path,
        monkeypatch,
    )

    promoted, preview, cards, provenance = poster_promotion.promote(
        "Example",
        artwork,
        language="de",
        force=False,
        run_metadata_path=run_metadata,
    )

    assert promoted.is_file()
    assert preview.is_file()
    assert len(cards) == 9 and all(path.is_file() for path in cards)
    payload = json.loads(provenance.read_text(encoding="utf-8"))
    assert payload["scope"] == "Example"
    assert payload["preview_language"] == "de"
    assert payload["outputs"]["artwork"]["file"] == (
        "data/poster_assets/Example/poster-flux2-artwork.png"
    )
    assert not list(scope_dir.glob(".poster-promotion-*"))


def test_promotion_rejects_generation_metadata_drift(
    tmp_path: Path,
    monkeypatch,
):
    scope_dir, artwork, run_metadata = _promotion_fixture(
        tmp_path,
        monkeypatch,
    )
    payload = json.loads(run_metadata.read_text(encoding="utf-8"))
    payload["generation"] = {"engine": "another-model"}
    run_metadata.write_text(json.dumps(payload), encoding="utf-8")

    try:
        poster_promotion.promote(
            "Example",
            artwork,
            run_metadata_path=run_metadata,
        )
    except ValueError as error:
        assert "does not match" in str(error)
    else:
        raise AssertionError("generation metadata drift was accepted")

    assert not (scope_dir / "poster-flux2-artwork.png").exists()
    assert not list(scope_dir.glob(".poster-promotion-*"))


def test_failed_promotion_keeps_existing_bundle(
    tmp_path: Path,
    monkeypatch,
):
    scope_dir, artwork, run_metadata = _promotion_fixture(
        tmp_path,
        monkeypatch,
    )
    existing = scope_dir / "poster-flux2-artwork.png"
    Image.new("RGB", (16, 16), (220, 30, 20)).save(existing)
    existing_hash = sha256_file(existing)

    def fail_slice(_scope, _source, _output_dir):
        raise RuntimeError("synthetic crop failure")

    monkeypatch.setattr(poster_promotion, "slice_poster", fail_slice)

    try:
        poster_promotion.promote(
            "Example",
            artwork,
            force=True,
            run_metadata_path=run_metadata,
        )
    except RuntimeError as error:
        assert "synthetic crop failure" in str(error)
    else:
        raise AssertionError("failed promotion unexpectedly succeeded")

    assert sha256_file(existing) == existing_hash
    assert not list(scope_dir.glob(".poster-promotion-*"))


def test_promoted_production_posters_match_provenance_and_print_geometry():
    for scope in (
        "Base1",
        "Pokedex/sections/gen1",
        "Pokedex/sections/gen2",
        "Pokedex/sections/gen3",
        "Pokedex/sections/gen4",
        "Pokedex/sections/gen5",
        "Pokedex/sections/gen6",
        "SV03.5",
        "ExGen3/sections/normal",
        "ExGen3/sections/mega",
    ):
        result = validate_promoted_poster(scope)
        assert result["dimensions"] == (2368, 3268)
        assert result["card_dimensions"] == (750, 1050)
        assert result["cards"] == 9


def test_validation_rejects_pdf_artwork_not_named_by_provenance():
    bundle = poster_bundle("Base1")
    mismatched_bundle = replace(
        bundle,
        artwork_file="unreviewed.png",
    )

    with pytest.raises(
        ValueError,
        match="routes PDF artwork.*promoted provenance validates",
    ):
        validate_promoted_poster(mismatched_bundle)


def test_enabled_poster_scopes_only_returns_pdf_enabled_manifests(
    tmp_path: Path,
):
    for scope, enabled in (
        ("EnabledB", True),
        ("Disabled", False),
        ("EnabledA", True),
    ):
        scope_dir = tmp_path / scope
        scope_dir.mkdir()
        (scope_dir / "poster.yaml").write_text(
            f"pdf:\n  enabled: {str(enabled).lower()}\n",
            encoding="utf-8",
        )

    assert enabled_poster_scopes(tmp_path) == ["EnabledA", "EnabledB"]
