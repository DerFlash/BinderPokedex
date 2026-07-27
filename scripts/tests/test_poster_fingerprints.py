import copy
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
import yaml
from PIL import Image

from scripts.poster_assets import promote_comfyui_poster as promotion
from scripts.poster_assets import provenance
from scripts.poster_assets import validate_promoted_poster as validator
from scripts.poster_assets.layout import build_print_layout
from scripts.poster_assets.poster_config import (
    IDENTITY_LOCK_PROMPT_FILE,
    build_identity_lock_prompt,
)
from scripts.poster_assets.poster_io import load_json, poster_bundle
from scripts.poster_assets.poster_subject import PosterSubject
from scripts.poster_assets.provenance import (
    build_generation_fingerprint,
    build_overlay_fingerprint,
    current_generation_pipeline_contract_version,
    file_record,
    fingerprint_record_is_valid,
    generation_fingerprint_pipeline_contract_version,
    load_run_metadata,
    required_model_artifact_hashes,
    sha256_file,
    write_run_metadata,
)


def _manifest() -> dict:
    digest = "1" * 64
    return {
        "schema_version": 2,
        "scope": "Example",
        "layout": {"name": "standard_3x3"},
        "text_cells": {
            "title": {"row": 1, "column": 2},
            "set_info": {
                "row": 2,
                "column": 2,
                "max_width_ratio": 0.92,
                "max_height_ratio": 0.68,
            },
        },
        "title_text": {"de": "Beispiel", "en": "Example"},
        "text_content": {"mode": "section_summary"},
        "pdf": {
            "enabled": True,
            "artwork_file": "poster-flux2-artwork.png",
            "insertion": "after_first_section_cover",
        },
        "artwork": {
            "promoted_file": "poster-flux2-artwork.png",
            "preview_file": "poster-flux2.png",
            "provenance_file": "poster-flux2-provenance.json",
            "identity_lock": {
                "overscan_ratio": 0.04,
                "max_protected_start_ratio": 0.70,
                "transition_ratio": 0.10,
                "subject_clearance_ratio": 0.02,
            },
            "scene": {
                "concept": "a quiet example collection",
                "setting": "The artwork contains a broad green valley.",
                "lighting": "Soft daylight enters from the upper left.",
                "rendering": "Use restrained hand-painted cel linework.",
                "ground_noun": "meadow",
            },
            "generation": {
                "engine": "flux",
                "model": "model.safetensors",
                "model_sha256": digest,
                "encoder": "encoder.safetensors",
                "encoder_sha256": digest,
                "vae": "vae.safetensors",
                "vae_sha256": digest,
                "mode": "identity_lock",
                "reference_mode": "two_pass_source_pixels",
                "seed": 123,
                "steps": 4,
                "generation_megapixels": 1.0,
                "output_dpi": 10,
                "output_method": "model_upscale",
                "upscale_model": "upscale.pth",
                "upscale_model_sha256": digest,
            },
        },
        "pokemon": {
            "strategy": "featured_from_scope",
            "count": "auto_from_layout_columns",
            "row": "bottom",
            "cutout_source": "pokeapi_official_artwork",
            "fallback_candidates": [],
        },
        "conditioning": {
            "identity_defaults": {
                "neutral_rgb": [226, 224, 211],
                "canvas_px": 512,
                "min_subject_px": 150,
                "max_subject_px": 350,
                "bottom_padding_px": 24,
            }
        },
    }


def _scope_data() -> dict:
    return {
        "name": "Example",
        "sections": {
            "main": {
                "title": {"de": "Beispielsammlung", "en": "Example Collection"},
                "subtitle": {"de": "Tal", "en": "Valley"},
                "description": {
                    "de": "Nummern #001 – #007",
                    "en": "Numbers #001 – #007",
                },
                "featured_elements": [
                    {"pokemon_id": 1},
                    {"pokemon_id": 4},
                    {"pokemon_id": 7},
                ],
                "cards": [],
            }
        },
    }


def _write_fixture(tmp_path: Path):
    repository = tmp_path / "repository"
    assets = repository / "data" / "poster_assets"
    output = repository / "data" / "output"
    scope_dir = assets / "Example"
    cutout_dir = scope_dir / "cutouts"
    cutout_dir.mkdir(parents=True)
    output.mkdir(parents=True)

    manifest = _manifest()
    manifest_path = scope_dir / "poster.yaml"
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    (output / "Example.json").write_text(
        json.dumps(_scope_data(), ensure_ascii=False),
        encoding="utf-8",
    )
    items = []
    for pokemon_id, color in (
        (1, (80, 180, 90, 255)),
        (4, (235, 120, 50, 255)),
        (7, (80, 150, 220, 255)),
    ):
        filename = f"pokemon_{pokemon_id:03d}.png"
        Image.new("RGBA", (18, 18), color).save(cutout_dir / filename)
        items.append(
            {
                "pokemon_id": pokemon_id,
                "url": PosterSubject(pokemon_id, pokemon_id).image_url,
                "file": filename,
            }
        )
    (cutout_dir / "manifest.json").write_text(
        json.dumps(
            {
                "scope": "Example",
                "generated_at": "2026-01-01T00:00:00Z",
                "items": items,
            }
        ),
        encoding="utf-8",
    )
    Image.new("RGBA", (48, 24), (240, 210, 70, 255)).save(
        scope_dir / "logo.png"
    )
    bundle = poster_bundle("Example", poster_assets=assets)
    return repository, assets, output, scope_dir, bundle


def _with_manifest(bundle, manifest):
    return replace(bundle, manifest=manifest)


def test_generation_fingerprint_excludes_routing_and_overlay_only_inputs(
    tmp_path,
):
    _repository, assets, output, scope_dir, bundle = _write_fixture(tmp_path)
    original = build_generation_fingerprint(
        bundle,
        poster_assets=assets,
        scope_data_dir=output,
    )

    changed = copy.deepcopy(bundle.manifest)
    changed["pdf"]["enabled"] = False
    changed["pdf"]["artwork_file"] = "another-promoted-artwork.png"
    changed["title_text"] = {"en": "A New Exact Title"}
    changed["title_logo"] = {"file": "another-logo.png"}
    changed["text_content"] = {"mode": "set_summary"}
    changed["text_cells"]["set_info"]["max_width_ratio"] = 0.74
    changed["text_cells"]["set_info"]["max_height_ratio"] = 0.51
    changed["artwork"]["promoted_file"] = "another-promoted-artwork.png"
    changed["artwork"]["preview_file"] = "another-preview.png"
    changed["artwork"]["provenance_file"] = "another-provenance.json"
    overlay_changed = build_generation_fingerprint(
        _with_manifest(bundle, changed),
        poster_assets=assets,
        scope_data_dir=output,
    )
    assert overlay_changed["sha256"] == original["sha256"]

    cutout_manifest = scope_dir / "cutouts" / "manifest.json"
    cutouts = load_json(cutout_manifest)
    cutouts["generated_at"] = "2099-12-31T23:59:59Z"
    cutout_manifest.write_text(json.dumps(cutouts), encoding="utf-8")
    timestamp_changed = build_generation_fingerprint(
        bundle,
        poster_assets=assets,
        scope_data_dir=output,
    )
    assert timestamp_changed["sha256"] == original["sha256"]


def test_generation_fingerprint_changes_for_generation_inputs(tmp_path):
    _repository, assets, output, scope_dir, bundle = _write_fixture(tmp_path)
    original = build_generation_fingerprint(
        bundle,
        poster_assets=assets,
        scope_data_dir=output,
    )

    mutations = []
    scene = copy.deepcopy(bundle.manifest)
    scene["artwork"]["scene"]["concept"] = "a changed generated scene"
    mutations.append(scene)
    model = copy.deepcopy(bundle.manifest)
    model["artwork"]["generation"]["model"] = "another-model.safetensors"
    mutations.append(model)
    safe_cell = copy.deepcopy(bundle.manifest)
    safe_cell["text_cells"]["title"]["column"] = 1
    mutations.append(safe_cell)
    identity_lock = copy.deepcopy(bundle.manifest)
    identity_lock["artwork"]["identity_lock"]["overscan_ratio"] = 0.08
    mutations.append(identity_lock)
    pokemon = copy.deepcopy(bundle.manifest)
    pokemon["pokemon"]["fallback_candidates"] = [{"pokemon_id": 25}]
    mutations.append(pokemon)
    conditioning = copy.deepcopy(bundle.manifest)
    conditioning["conditioning"]["identity_defaults"]["canvas_px"] = 768
    mutations.append(conditioning)

    for changed in mutations:
        fingerprint = build_generation_fingerprint(
            _with_manifest(bundle, changed),
            poster_assets=assets,
            scope_data_dir=output,
        )
        assert fingerprint["sha256"] != original["sha256"]

    Image.new("RGBA", (18, 18), (1, 2, 3, 255)).save(
        scope_dir / "cutouts" / "pokemon_001.png"
    )
    pixels_changed = build_generation_fingerprint(
        bundle,
        poster_assets=assets,
        scope_data_dir=output,
    )
    assert pixels_changed["sha256"] != original["sha256"]


def test_generation_fingerprint_is_base_compatible_and_form_sensitive(
    tmp_path,
):
    _repository, assets, output, scope_dir, bundle = _write_fixture(tmp_path)
    original = build_generation_fingerprint(
        bundle,
        poster_assets=assets,
        scope_data_dir=output,
    )
    source_path = output / "Example.json"
    cutout_manifest_path = scope_dir / "cutouts" / "manifest.json"
    source = load_json(source_path)
    cutouts = load_json(cutout_manifest_path)

    source["sections"]["main"]["featured_elements"][0][
        "poster_subject"
    ] = PosterSubject(1, 1).as_mapping()
    cutouts["items"][0]["poster_subject"] = PosterSubject(
        1,
        1,
    ).as_mapping()
    source_path.write_text(json.dumps(source), encoding="utf-8")
    cutout_manifest_path.write_text(json.dumps(cutouts), encoding="utf-8")

    explicit_base = build_generation_fingerprint(
        bundle,
        poster_assets=assets,
        scope_data_dir=output,
    )
    assert explicit_base["sha256"] == original["sha256"]
    assert explicit_base["components"]["source_subject_ids"][0] == 1
    assert "poster_subject" not in explicit_base["components"]["cutouts"][0]

    source["sections"]["main"]["featured_elements"][0] = {
        "pokemon_id": 6,
        "poster_subject": PosterSubject(6, 10034).as_mapping(),
    }
    cutouts["items"][0]["pokemon_id"] = 6
    cutouts["items"][0]["url"] = PosterSubject(6, 10034).image_url
    cutouts["items"][0]["poster_subject"] = PosterSubject(
        6,
        10034,
    ).as_mapping()
    source_path.write_text(json.dumps(source), encoding="utf-8")
    cutout_manifest_path.write_text(json.dumps(cutouts), encoding="utf-8")
    first_form = build_generation_fingerprint(
        bundle,
        poster_assets=assets,
        scope_data_dir=output,
    )

    source["sections"]["main"]["featured_elements"][0][
        "poster_subject"
    ] = PosterSubject(6, 10035).as_mapping()
    cutouts["items"][0]["url"] = PosterSubject(6, 10035).image_url
    cutouts["items"][0]["poster_subject"] = PosterSubject(
        6,
        10035,
    ).as_mapping()
    source_path.write_text(json.dumps(source), encoding="utf-8")
    cutout_manifest_path.write_text(json.dumps(cutouts), encoding="utf-8")
    second_form = build_generation_fingerprint(
        bundle,
        poster_assets=assets,
        scope_data_dir=output,
    )

    assert first_form["sha256"] != original["sha256"]
    assert second_form["sha256"] != first_form["sha256"]
    assert first_form["components"]["source_subject_ids"][0] == {
        "pokemon_id": 6,
        "poster_subject": {
            "source": "pokeapi_official_artwork",
            "official_artwork_id": 10034,
        },
    }
    assert first_form["components"]["cutouts"][0]["poster_subject"] == {
        "source": "pokeapi_official_artwork",
        "official_artwork_id": 10034,
    }


def test_generation_fingerprint_rejects_stale_form_cutout_selection(tmp_path):
    _repository, assets, output, scope_dir, bundle = _write_fixture(tmp_path)
    source_path = output / "Example.json"
    manifest_path = scope_dir / "cutouts" / "manifest.json"
    source = load_json(source_path)
    cutouts = load_json(manifest_path)

    source["sections"]["main"]["featured_elements"][0] = {
        "pokemon_id": 6,
        "poster_subject": PosterSubject(6, 10034).as_mapping(),
    }
    cutouts["items"][0]["pokemon_id"] = 6
    cutouts["items"][0]["url"] = PosterSubject(6, 6).image_url
    source_path.write_text(json.dumps(source), encoding="utf-8")
    manifest_path.write_text(json.dumps(cutouts), encoding="utf-8")

    with pytest.raises(ValueError, match="do not match current source"):
        build_generation_fingerprint(
            bundle,
            poster_assets=assets,
            scope_data_dir=output,
        )


def test_generation_fingerprint_rejects_duplicate_cutout_subjects(tmp_path):
    _repository, assets, output, scope_dir, bundle = _write_fixture(tmp_path)
    manifest_path = scope_dir / "cutouts" / "manifest.json"
    original = load_json(manifest_path)

    duplicate = copy.deepcopy(original)
    duplicate["items"].append(copy.deepcopy(duplicate["items"][0]))
    manifest_path.write_text(json.dumps(duplicate), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate poster subject"):
        build_generation_fingerprint(
            bundle,
            poster_assets=assets,
            scope_data_dir=output,
        )

    wrong_url = copy.deepcopy(original)
    wrong_url["items"][0]["url"] = PosterSubject(4, 4).image_url
    manifest_path.write_text(json.dumps(wrong_url), encoding="utf-8")
    with pytest.raises(ValueError, match="URL does not match poster subject"):
        build_generation_fingerprint(
            bundle,
            poster_assets=assets,
            scope_data_dir=output,
        )


def test_required_model_hashes_follow_the_selected_engine_artifacts():
    assert required_model_artifact_hashes(
        {
            "model": "model.gguf",
            "encoder": "clip.safetensors",
            "encoder_2": "t5.gguf",
            "vae": "vae.safetensors",
            "controlnet": "controlnet.safetensors",
            "lora": "lightning.safetensors",
            "upscale_model": "upscale.pth",
        }
    ) == (
        "model_sha256",
        "encoder_sha256",
        "encoder_2_sha256",
        "vae_sha256",
        "controlnet_sha256",
        "lora_sha256",
        "upscale_model_sha256",
    )


def test_pipeline_contract_versions_are_family_specific_and_strict():
    identity_generation = {"engine": "flux", "mode": "identity_lock"}
    edit_generation = {"engine": "qwen_edit", "mode": "edit"}

    assert current_generation_pipeline_contract_version(
        identity_generation
    ) == 2
    assert current_generation_pipeline_contract_version(edit_generation) == 1
    accepted_legacy = provenance.fingerprint_record(
        {
            "pipeline_contract": {
                "name": "poster_generation",
                "version": 1,
            }
        }
    )
    assert generation_fingerprint_pipeline_contract_version(
        accepted_legacy,
        identity_generation,
    ) == 1
    unsupported = provenance.fingerprint_record(
        {
            "pipeline_contract": {
                "name": "poster_generation",
                "version": 3,
            }
        }
    )
    with pytest.raises(ValueError, match="Unsupported generation pipeline"):
        generation_fingerprint_pipeline_contract_version(
            unsupported,
            identity_generation,
        )


def test_run_metadata_records_generation_and_overlay_fingerprints(
    tmp_path,
    monkeypatch,
):
    repository, assets, output, scope_dir, bundle = _write_fixture(tmp_path)
    work_dir = scope_dir / "comfyui_poster"
    work_dir.mkdir()
    Image.new("RGBA", (18, 18), (10, 20, 30, 255)).save(
        work_dir / "inpaint_reference.png"
    )
    Image.new("RGBA", (18, 18), (0, 0, 0, 0)).save(
        work_dir / "upper_context_mask.png"
    )
    Image.new("RGBA", (18, 18), (0, 0, 0, 0)).save(
        work_dir / "upper_context_generation_mask.png"
    )
    scope_data = load_json(output / "Example.json")
    (work_dir / IDENTITY_LOCK_PROMPT_FILE).write_text(
        build_identity_lock_prompt(bundle.manifest, scope_data) + "\n",
        encoding="utf-8",
    )
    workflow = work_dir / "workflow.json"
    workflow.write_text("{}\n", encoding="utf-8")
    artwork = tmp_path / "artwork.png"
    Image.new("RGB", (79, 109), (40, 120, 80)).save(artwork)
    monkeypatch.setattr(provenance, "POSTER_ASSETS", assets)
    monkeypatch.setattr(provenance, "SCOPE_DATA", output)
    monkeypatch.setattr(provenance, "ROOT", repository)

    metadata_path = write_run_metadata(
        "Example",
        artwork,
        workflow,
        bundle.manifest["artwork"]["generation"],
    )
    metadata = load_json(metadata_path)

    assert fingerprint_record_is_valid(
        metadata["inputs"]["generation_fingerprint"]
    )
    assert fingerprint_record_is_valid(
        metadata["inputs"]["overlay_fingerprint"]
    )


def test_overlay_fingerprint_tracks_text_and_logo_but_not_pdf_routing(
    tmp_path,
):
    _repository, assets, output, scope_dir, bundle = _write_fixture(tmp_path)
    original = build_overlay_fingerprint(
        bundle,
        poster_assets=assets,
        scope_data_dir=output,
    )

    routing = copy.deepcopy(bundle.manifest)
    routing["pdf"]["enabled"] = False
    routing_changed = build_overlay_fingerprint(
        _with_manifest(bundle, routing),
        poster_assets=assets,
        scope_data_dir=output,
    )
    assert routing_changed["sha256"] == original["sha256"]

    title = copy.deepcopy(bundle.manifest)
    title["title_text"]["en"] = "Changed Exact Title"
    title_changed = build_overlay_fingerprint(
        _with_manifest(bundle, title),
        poster_assets=assets,
        scope_data_dir=output,
    )
    assert title_changed["sha256"] != original["sha256"]

    source_path = output / "Example.json"
    source = load_json(source_path)
    source["sections"]["main"]["description"]["en"] = "Changed range text"
    source_path.write_text(json.dumps(source), encoding="utf-8")
    localized_changed = build_overlay_fingerprint(
        bundle,
        poster_assets=assets,
        scope_data_dir=output,
    )
    assert localized_changed["sha256"] != original["sha256"]

    logo_manifest = copy.deepcopy(bundle.manifest)
    logo_manifest["title_logo"] = {"file": "logo.png"}
    logo_bundle = _with_manifest(bundle, logo_manifest)
    logo_original = build_overlay_fingerprint(
        logo_bundle,
        poster_assets=assets,
        scope_data_dir=output,
    )
    Image.new("RGBA", (48, 24), (20, 40, 220, 255)).save(
        scope_dir / "logo.png"
    )
    logo_changed = build_overlay_fingerprint(
        logo_bundle,
        poster_assets=assets,
        scope_data_dir=output,
    )
    assert logo_changed["sha256"] != logo_original["sha256"]


def test_overlay_fingerprint_tracks_the_rendering_contract(
    tmp_path,
    monkeypatch,
):
    _repository, assets, output, _scope_dir, bundle = _write_fixture(
        tmp_path
    )
    current = build_overlay_fingerprint(
        bundle,
        poster_assets=assets,
        scope_data_dir=output,
    )

    assert current["components"]["pipeline_contract"] == {
        "name": "poster_overlay",
        "version": 2,
    }
    monkeypatch.setattr(
        provenance,
        "OVERLAY_PIPELINE_CONTRACT_VERSION",
        1,
    )
    legacy = build_overlay_fingerprint(
        bundle,
        poster_assets=assets,
        scope_data_dir=output,
    )

    assert legacy["sha256"] != current["sha256"]


def test_load_run_metadata_accepts_promoted_provenance_for_overlay_refresh(
    tmp_path,
):
    artwork = tmp_path / "artwork.png"
    Image.new("RGB", (10, 10), (20, 30, 40)).save(artwork)
    run = {
        "schema_version": 1,
        "kind": "poster_generation_run",
        "source_artwork": {"sha256": sha256_file(artwork)},
    }
    provenance_path = tmp_path / "poster-provenance.json"
    provenance_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "kind": "promoted_poster",
                "run": run,
            }
        ),
        encoding="utf-8",
    )

    assert load_run_metadata(provenance_path, artwork) == run


def _promotion_fixture(tmp_path: Path, monkeypatch):
    repository, assets, output, scope_dir, bundle = _write_fixture(tmp_path)
    layout = build_print_layout("standard_3x3", 10)
    candidate = tmp_path / "candidate.png"
    Image.new(
        "RGB",
        (layout.width_px, layout.height_px),
        (40, 120, 80),
    ).save(candidate)

    generation_fingerprint = build_generation_fingerprint(
        bundle,
        poster_assets=assets,
        scope_data_dir=output,
    )
    overlay_fingerprint = build_overlay_fingerprint(
        bundle,
        poster_assets=assets,
        scope_data_dir=output,
    )
    scope_data = load_json(output / "Example.json")
    prompt_hash = hashlib.sha256(
        (build_identity_lock_prompt(bundle.manifest, scope_data) + "\n").encode(
            "utf-8"
        )
    ).hexdigest()
    run_metadata = tmp_path / "candidate.run.json"
    run_metadata.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "kind": "poster_generation_run",
                "scope": "Example",
                "source_scope": "Example",
                "poster_id": "Example",
                "section_id": None,
                "generation": bundle.manifest["artwork"]["generation"],
                "inputs": {
                    "scope_manifest": file_record(
                        scope_dir / "poster.yaml"
                    ),
                    "prompt": {"sha256": prompt_hash},
                    "generation_fingerprint": generation_fingerprint,
                    "overlay_fingerprint": overlay_fingerprint,
                },
                "source_artwork": {"sha256": sha256_file(candidate)},
                "validation": {
                    "identity_lock": {
                        "method": "exact_opaque_source_pixels",
                        "opaque_pixels": 123,
                        "changed_pixels": 0,
                        "passed": True,
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    def fake_finalize(_scope, source, destination, _language):
        Image.open(source).convert("RGB").save(
            destination,
            format="PNG",
            dpi=(10, 10),
        )
        return destination

    def fake_slice(_scope, _source, output_dir):
        output_dir.mkdir(parents=True)
        paths = []
        for row in range(1, 4):
            for column in range(1, 4):
                path = output_dir / f"card_r{row}_c{column}.png"
                Image.new(
                    "RGB",
                    (layout.card_width_px, layout.card_height_px),
                    (40, 120, 80),
                ).save(path, format="PNG", dpi=(10, 10))
                paths.append(path)
        return paths

    monkeypatch.setattr(promotion, "POSTER_ASSETS", assets)
    monkeypatch.setattr(promotion, "finalize", fake_finalize)
    monkeypatch.setattr(promotion, "slice_poster", fake_slice)
    monkeypatch.setattr(provenance, "POSTER_ASSETS", assets)
    monkeypatch.setattr(provenance, "SCOPE_DATA", output)
    monkeypatch.setattr(provenance, "ROOT", repository)
    monkeypatch.setattr(validator, "POSTER_ASSETS", assets)
    monkeypatch.setattr(validator, "ROOT", repository)
    monkeypatch.setattr(
        validator,
        "load_poster_scope_data",
        lambda _bundle: load_json(output / "Example.json"),
    )
    return (
        repository,
        assets,
        output,
        scope_dir,
        candidate,
        run_metadata,
        overlay_fingerprint,
    )


def test_promotion_rebinds_overlay_and_validator_prefers_fingerprints(
    tmp_path,
    monkeypatch,
):
    (
        _repository,
        _assets,
        _output,
        scope_dir,
        candidate,
        run_metadata,
        old_overlay,
    ) = _promotion_fixture(tmp_path, monkeypatch)

    manifest_path = scope_dir / "poster.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["title_text"]["en"] = "Changed after expensive generation"
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    _artwork, _preview, _cards, provenance_path = promotion.promote(
        "Example",
        candidate,
        language="en",
        run_metadata_path=run_metadata,
    )
    promoted = load_json(provenance_path)
    generation_record = promoted["run"]["inputs"]["generation_fingerprint"]
    overlay_record = promoted["run"]["inputs"]["overlay_fingerprint"]
    assert fingerprint_record_is_valid(generation_record)
    assert fingerprint_record_is_valid(overlay_record)
    assert overlay_record["sha256"] != old_overlay["sha256"]

    current = validator.validate("Example")
    assert current["generation_fingerprint_current"] is True
    assert current["overlay_fingerprint_current"] is True

    manifest["pdf"]["enabled"] = False
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    routing_only = validator.validate("Example")
    assert routing_only["generation_fingerprint_current"] is True
    assert routing_only["overlay_fingerprint_current"] is True

    manifest["title_text"]["en"] = "Another cheap overlay change"
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    overlay_stale = validator.validate("Example")
    assert overlay_stale["generation_fingerprint_current"] is True
    assert overlay_stale["overlay_fingerprint_current"] is False

    manifest["title_text"]["en"] = "Changed after expensive generation"
    manifest["artwork"]["scene"]["concept"] = "a different generated scene"
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Generation input fingerprint drift"):
        validator.validate("Example")


def test_validator_accepts_audited_v1_inputs_without_calling_them_v2(
    tmp_path,
    monkeypatch,
):
    (
        _repository,
        assets,
        output,
        scope_dir,
        candidate,
        run_metadata,
        _old_overlay,
    ) = _promotion_fixture(tmp_path, monkeypatch)
    _artwork, _preview, _cards, provenance_path = promotion.promote(
        "Example",
        candidate,
        language="en",
        run_metadata_path=run_metadata,
    )
    promoted = load_json(provenance_path)
    bundle = poster_bundle("Example", poster_assets=assets)
    promoted["run"]["inputs"]["generation_fingerprint"] = (
        build_generation_fingerprint(
            bundle,
            poster_assets=assets,
            scope_data_dir=output,
            pipeline_contract_version=1,
        )
    )
    provenance_path.write_text(json.dumps(promoted), encoding="utf-8")

    result = validator.validate("Example")

    assert result["generation_inputs_current"] is True
    assert result["generation_pipeline_contract_version"] == 1
    assert (
        result["generation_pipeline_contract_status"]
        == "accepted_legacy"
    )


def test_validator_rejects_an_unknown_pipeline_contract(
    tmp_path,
    monkeypatch,
):
    (
        _repository,
        assets,
        output,
        scope_dir,
        candidate,
        run_metadata,
        _old_overlay,
    ) = _promotion_fixture(tmp_path, monkeypatch)
    _artwork, _preview, _cards, provenance_path = promotion.promote(
        "Example",
        candidate,
        language="en",
        run_metadata_path=run_metadata,
    )
    promoted = load_json(provenance_path)
    bundle = poster_bundle("Example", poster_assets=assets)
    unsupported_components = copy.deepcopy(
        promoted["run"]["inputs"]["generation_fingerprint"]["components"]
    )
    unsupported_components["pipeline_contract"]["version"] = 3
    promoted["run"]["inputs"]["generation_fingerprint"] = (
        provenance.fingerprint_record(unsupported_components)
    )
    provenance_path.write_text(json.dumps(promoted), encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported generation pipeline"):
        validator.validate("Example")


def test_validator_keeps_legacy_full_manifest_fallback(tmp_path, monkeypatch):
    (
        _repository,
        _assets,
        _output,
        scope_dir,
        candidate,
        run_metadata,
        _old_overlay,
    ) = _promotion_fixture(tmp_path, monkeypatch)
    _artwork, _preview, _cards, provenance_path = promotion.promote(
        "Example",
        candidate,
        language="en",
        run_metadata_path=run_metadata,
    )
    promoted = load_json(provenance_path)
    del promoted["run"]["inputs"]["generation_fingerprint"]
    del promoted["run"]["inputs"]["overlay_fingerprint"]
    provenance_path.write_text(json.dumps(promoted), encoding="utf-8")

    manifest_path = scope_dir / "poster.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["pdf"]["enabled"] = False
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Scope manifest drift"):
        validator.validate("Example")
