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
    section = result.get_data()["sections"]["gen1"]

    assert section["section_order"] == 1
    assert section["title"]["fr"] == "Génération I"
    assert section["title"]["ja"] == "1世代"
    assert section["title"]["zh_hans"] == "第1世代"
    assert section["subtitle"]["ja"] == "カントー"
    assert section["subtitle"]["ko"] == "칸토"
    assert section["subtitle"]["zh_hant"] == "關都"
