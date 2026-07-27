import json
from copy import deepcopy
from pathlib import Path

import pytest
from PIL import Image, ImageChops

from scripts.poster_assets.finalize_comfyui_poster import (
    SUPPORTED_LANGUAGES,
    finalize,
    info_panel_values,
)
from scripts.poster_assets.typography import load_font, wrap_text
from scripts.poster_assets.init_poster_scope import (
    build_section_manifest,
    section_poster_title,
)
from scripts.poster_assets.poster_io import (
    load_poster_scope_data,
    poster_bundle,
    poster_bundles_for_scope,
)
from scripts.poster_assets.poster_config import build_identity_lock_prompt
from scripts.poster_assets.provenance import sha256_file
from scripts.poster_assets.scene_catalog import section_scenes_for_scope
from scripts.poster_assets.validate_promoted_poster import enabled_poster_scopes


ROOT = Path(__file__).resolve().parents[2]
POSTER_ASSETS = ROOT / "data" / "poster_assets"


def test_legacy_poster_manifests_remain_isolated_single_bundles():
    expected_hashes = {
        "Base1": "2499ac743450c51e1496e800d47d14f880ea999dca2aabc4eed68ffee4647e02",
        "SV03.5": "1ef4b42e9c0ac7e7abb7d6a856188f7f126693fc7b9672766844de34d828fcd2",
    }

    for scope, expected_hash in expected_hashes.items():
        bundles = poster_bundles_for_scope(scope)
        assert len(bundles) == 1
        assert bundles[0].asset_key == scope
        assert bundles[0].section_id is None
        assert bundles[0].insertion == "after_first_section_cover"
        assert sha256_file(bundles[0].manifest_path) == expected_hash


def test_pokedex_index_routes_eight_enabled_and_one_disabled_section_bundle():
    expected_starters = {
        "gen1": [1, 4, 7],
        "gen2": [152, 155, 158],
        "gen3": [252, 255, 258],
        "gen4": [387, 390, 393],
        "gen5": [495, 498, 501],
        "gen6": [650, 653, 656],
        "gen7": [722, 725, 728],
        "gen8": [810, 813, 816],
        "gen9": [906, 909, 912],
    }

    bundles = poster_bundles_for_scope("Pokedex")

    assert [bundle.poster_id for bundle in bundles] == list(expected_starters)
    assert len({bundle.manifest_path for bundle in bundles}) == 9
    assert [
        bundle.poster_id for bundle in bundles if bundle.pdf_enabled
    ] == [
        "gen1",
        "gen2",
        "gen3",
        "gen4",
        "gen5",
        "gen6",
        "gen7",
        "gen8",
    ]
    assert [
        bundle.poster_id for bundle in bundles if not bundle.pdf_enabled
    ] == ["gen9"]
    assert all(bundle.insertion == "after_section_cover" for bundle in bundles)
    assert len(
        {
            bundle.manifest["artwork"]["generation"]["seed"]
            for bundle in bundles
        }
    ) == 9
    for bundle in bundles:
        selected = load_poster_scope_data(bundle)
        assert list(selected["sections"]) == [bundle.section_id]
        section = selected["sections"][bundle.section_id]
        assert [
            item["pokemon_id"]
            for item in section["featured_elements"]
        ] == expected_starters[bundle.section_id]


def test_pokedex_leaf_scenes_match_the_reviewed_section_catalog():
    scenes = section_scenes_for_scope("Pokedex")

    for bundle in poster_bundles_for_scope("Pokedex"):
        assert bundle.manifest["artwork"]["scene"] == scenes[bundle.section_id]
        prompt_opening = build_identity_lock_prompt(
            bundle.manifest,
            load_poster_scope_data(bundle),
        ).split("\n\n", 1)[0].lower()
        assert "pokédex" not in prompt_opening
        assert "pokedex" not in prompt_opening
        assert "pokémon" not in prompt_opening
        assert "pokemon" not in prompt_opening


def test_exgen3_leaf_scenes_cover_both_variant_sections_exactly():
    scenes = section_scenes_for_scope("ExGen3")

    assert set(scenes) == {"normal", "mega"}
    assert "Paldea-inspired valley" in scenes["normal"]["setting"]
    assert "distant blue coast" in scenes["normal"]["setting"]
    assert "expansive highland basin" in scenes["mega"]["setting"]
    assert "refracted energy" in scenes["mega"]["setting"]
    assert all("safe_areas" not in scene for scene in scenes.values())


def test_checked_in_pokedex_output_has_localized_section_overlay_values():
    bundle = next(
        bundle
        for bundle in poster_bundles_for_scope("Pokedex")
        if bundle.section_id == "gen1"
    )
    source_data = load_poster_scope_data(bundle)

    assert info_panel_values(
        source_data,
        "fr",
        "section_summary",
    ) == (
        "Génération I",
        "151 cartes",
        "Pokédex #001 – #151",
    )
    assert info_panel_values(
        source_data,
        "ja",
        "section_summary",
    ) == (
        "1世代",
        "151 枚",
        "ポケモン図鑑 #001 – #151",
    )


def test_section_overlay_uses_localized_title_count_and_description():
    values = info_panel_values(
        {
            "sections": {
                "gen1": {
                    "title": {"en": "Generation I", "fr": "Génération I"},
                    "subtitle": {"en": "Kanto", "ja": "カントー"},
                    "description": {
                        "en": "Pokédex #001 – #151",
                        "ja": "ポケモン図鑑 #001 – #151",
                    },
                    "cards": [{}, {}],
                }
            }
        },
        "ja",
        "section_summary",
    )

    assert values == (
        "Generation I",
        "2 枚",
        "ポケモン図鑑 #001 – #151",
    )


def test_section_manifest_and_overlay_hide_internal_variant_tokens():
    languages = (
        "de",
        "en",
        "fr",
        "es",
        "it",
        "ja",
        "ko",
        "zh_hans",
        "zh_hant",
    )
    section = {
        "title": {
            language: "Mega-Pokémon [EX_NEW]"
            for language in languages
        },
        "subtitle": {
            language: "[EX_NEW] Series"
            for language in languages
        },
        "description": {
            language: "[M] Evolution with [EX_TERA] and [EX]"
            for language in languages
        },
        "featured_elements": [
            {"pokemon_id": pokemon_id}
            for pokemon_id in (25, 150, 151)
        ],
        "cards": [{}, {}, {}],
    }
    source = deepcopy(section)
    manifest = build_section_manifest(
        "ExGen3/sections/mega",
        "ExGen3",
        "mega",
        section,
        "standard_3x3",
        {"engine": "flux"},
        {
            "concept": "example",
            "setting": "example",
            "lighting": "example",
            "rendering": "example",
            "ground_noun": "grass",
        },
    )

    assert manifest["title_text"]["en"] == "Mega-Pokémon ex"
    assert info_panel_values(
        {"sections": {"mega": section}},
        "en",
        "section_summary",
    ) == (
        "Mega-Pokémon ex",
        "3 cards",
        "Mega Evolution with Tera ex and EX",
    )
    assert section == source


def test_pokedex_section_poster_title_remains_backward_compatible():
    assert section_poster_title(
        "Pokedex",
        {"title": {"en": "Generation I"}},
    ) == "Pokédex"


@pytest.mark.parametrize("language", SUPPORTED_LANGUAGES)
def test_section_poster_finalizes_in_every_pdf_language(tmp_path, language):
    raw_path = tmp_path / f"raw-{language}.png"
    final_path = tmp_path / f"final-{language}.png"
    Image.new("RGB", (432, 608), (70, 130, 90)).save(raw_path)

    finalize(
        "Pokedex/sections/gen1",
        raw_path,
        final_path,
        language,
    )

    assert final_path.is_file()
    assert Image.open(final_path).size == (432, 608)
    assert (
        ImageChops.difference(
            Image.open(raw_path).convert("RGB"),
            Image.open(final_path).convert("RGB"),
        ).getbbox()
        is not None
    )


@pytest.mark.parametrize("language", SUPPORTED_LANGUAGES)
@pytest.mark.parametrize(
    "scope",
    (
        "ExGen3/sections/normal",
        "ExGen3/sections/mega",
    ),
)
def test_exgen3_posters_finalize_real_copy_in_every_language(
    tmp_path,
    language,
    scope,
):
    leaf = scope.rsplit("/", 1)[-1]
    raw_path = tmp_path / f"raw-{leaf}-{language}.png"
    final_path = tmp_path / f"final-{leaf}-{language}.png"
    Image.new("RGB", (432, 608), (70, 130, 90)).save(raw_path)

    finalize(scope, raw_path, final_path, language)

    assert final_path.is_file()
    assert Image.open(final_path).size == (432, 608)


def test_poster_wrapping_only_splits_unspaced_cjk_text_inside_words():
    font = load_font(48, language="ja")
    max_width = 100

    assert wrap_text("Pokémon ex", font, max_width) == [
        "Pokémon",
        "ex",
    ]
    cjk_lines = wrap_text("現代のポケモン時代", font, max_width)
    assert len(cjk_lines) > 1
    assert all(
        font.getbbox(line)[2] - font.getbbox(line)[0] <= max_width
        for line in cjk_lines
    )


def test_aggregate_index_rejects_unsafe_manifest_paths(tmp_path):
    scope_dir = tmp_path / "Aggregate"
    scope_dir.mkdir()
    (scope_dir / "posters.yaml").write_text(
        (
            "schema_version: 1\n"
            "scope: Aggregate\n"
            "posters:\n"
            "  - id: first\n"
            "    section_id: first\n"
            "    manifest: ../poster.yaml\n"
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unsafe relative poster asset path"):
        poster_bundles_for_scope("Aggregate", poster_assets=tmp_path)


@pytest.mark.parametrize("scope", [".", ".."])
def test_poster_scope_rejects_path_traversal_segments(tmp_path, scope):
    with pytest.raises(ValueError, match="poster scope"):
        poster_bundles_for_scope(scope, poster_assets=tmp_path)


def test_aggregate_index_rejects_duplicate_section_bindings(tmp_path):
    scope_dir = tmp_path / "Aggregate"
    target_dir = scope_dir / "first"
    target_dir.mkdir(parents=True)
    (target_dir / "poster.yaml").write_text(
        (
            "asset_key: Aggregate/first\n"
            "scope: Aggregate\n"
            "poster_id: first\n"
            "source:\n"
            "  scope: Aggregate\n"
            "  section_id: first\n"
        ),
        encoding="utf-8",
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
            "      insertion: after_section_cover\n"
            "  - id: second\n"
            "    section_id: first\n"
            "    manifest: second/poster.yaml\n"
            "    pdf:\n"
            "      insertion: after_section_cover\n"
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate poster section_id"):
        poster_bundles_for_scope("Aggregate", poster_assets=tmp_path)


def test_section_source_must_exist_in_aggregate_data(tmp_path):
    assets = tmp_path / "assets"
    data = tmp_path / "data"
    target_dir = assets / "Aggregate" / "missing"
    target_dir.mkdir(parents=True)
    data.mkdir()
    (target_dir / "poster.yaml").write_text(
        (
            "asset_key: Aggregate/missing\n"
            "scope: Aggregate\n"
            "poster_id: missing\n"
            "source:\n"
            "  scope: Aggregate\n"
            "  section_id: missing\n"
        ),
        encoding="utf-8",
    )
    (data / "Aggregate.json").write_text(
        json.dumps({"sections": {"known": {"cards": []}}}),
        encoding="utf-8",
    )
    bundle = poster_bundle(
        "Aggregate/missing",
        scope="Aggregate",
        section_id="missing",
        poster_assets=assets,
    )

    with pytest.raises(KeyError, match="missing"):
        load_poster_scope_data(bundle, scope_data_dir=data)


def test_enabled_discovery_includes_nested_aggregate_targets(tmp_path):
    legacy = tmp_path / "Legacy"
    nested = tmp_path / "Aggregate" / "first"
    legacy.mkdir()
    nested.mkdir(parents=True)
    (legacy / "poster.yaml").write_text(
        (
            "scope: Legacy\n"
            "pdf:\n"
            "  enabled: true\n"
        ),
        encoding="utf-8",
    )
    (nested / "poster.yaml").write_text(
        (
            "asset_key: Aggregate/first\n"
            "scope: Aggregate\n"
            "poster_id: first\n"
            "source:\n"
            "  scope: Aggregate\n"
            "  section_id: first\n"
        ),
        encoding="utf-8",
    )
    (tmp_path / "Aggregate" / "posters.yaml").write_text(
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
        ),
        encoding="utf-8",
    )

    assert enabled_poster_scopes(tmp_path) == [
        "Aggregate/first",
        "Legacy",
    ]
