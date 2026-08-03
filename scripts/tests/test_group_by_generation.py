from scripts.fetcher.steps.base import PipelineContext
from scripts.fetcher.steps.group_by_generation import GroupByGenerationStep


def test_generation_sections_use_nested_ui_and_region_translations():
    context = PipelineContext({})
    context.set_data(
        {
            "pokemon": [
                {
                    "id": 1,
                    "generation": 1,
                    "types": ["grass", "poison"],
                    "image_url": "https://example.test/1.png",
                    "names": [
                        {
                            "language": {"name": "en"},
                            "name": "Bulbasaur",
                        }
                    ],
                }
            ]
        }
    )
    context.storage["metadata"] = {
        "generations": {
            "gen1": {
                "name": "Generation I",
                "region": "Kanto",
                "range": [1, 151],
                "color": "#78C850",
            }
        }
    }

    result = GroupByGenerationStep("group").execute(context, {})
    assert result.get_data()["type"] == "pokedex"
    assert result.get_data()["name"] == "Pokédex"
    section = result.get_data()["sections"]["gen1"]

    assert section["section_order"] == 1
    assert section["title"]["fr"] == "Génération I"
    assert section["title"]["ja"] == "1世代"
    assert section["title"]["zh_hans"] == "第1世代"
    assert section["subtitle"]["ja"] == "カントー"
    assert section["subtitle"]["ko"] == "칸토"
    assert section["subtitle"]["zh_hant"] == "關都"


def test_generation_five_uses_localized_european_region_names():
    context = PipelineContext({})
    context.set_data(
        {
            "pokemon": [
                {
                    "id": 495,
                    "generation": 5,
                    "types": ["grass"],
                    "image_url": "https://example.test/495.png",
                    "names": [
                        {
                            "language": {"name": "en"},
                            "name": "Snivy",
                        }
                    ],
                }
            ]
        }
    )
    context.storage["metadata"] = {
        "generations": {
            "gen5": {
                "name": "Generation V",
                "region": "Unova",
                "range": [494, 649],
                "color": "#A890F0",
            }
        }
    }

    result = GroupByGenerationStep("group").execute(context, {})
    subtitle = result.get_data()["sections"]["gen5"]["subtitle"]

    assert subtitle["de"] == "Einall"
    assert subtitle["en"] == "Unova"
    assert subtitle["fr"] == "Unys"
    assert subtitle["es"] == "Teselia"
    assert subtitle["it"] == "Unima"
