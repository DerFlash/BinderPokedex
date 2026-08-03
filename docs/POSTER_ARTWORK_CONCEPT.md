# Poster Artwork Architecture

This document describes the implementation contract behind generated binder
posters. Use [Poster Workflow](POSTER_WORKFLOW.md) for commands,
[Poster Requirements](POSTER_ARTWORK_REQUIREMENTS.md) for acceptance criteria,
[Poster Status](POSTER_ARTWORK_STATUS.md) for the current rollout, and
[Poster Experiment Log](POSTER_ARTWORK_EXPERIMENT_LOG.md) for rejected
approaches.

## Goal

Create one set-specific, full-bleed scene that can be cut into physical card
pages while:

- keeping each supplied Pokémon recognizable and inside its assigned card;
- letting the landscape, lighting, shadows, and depth feel jointly authored;
- reserving safe cells for deterministic logo and information overlays;
- producing exact print geometry and auditable provenance;
- remaining optional for fetching and PDF generation.

## Design principles

1. **One active contract per scope.** `poster.yaml` is the source of truth for
   model, mode, reference topology, seed, layout, output, scene, and subjects.
2. **One preferred model family.** The production runtime supports FLUX.2
   `joint_scene` plus FLUX.2 `identity_lock` as fallback.
3. **Human review is a gate.** Automation can prove geometry, hashes, graph
   shape, and exact fallback pixels; it cannot approve anatomy or coherent
   depth in a generated one-shot.
4. **Candidates are disposable.** ComfyUI references, workflows, raw outputs,
   print candidates, and run metadata remain ignored until promotion.
5. **Promotions are deterministic inputs.** PDFs and CI consume only tracked
   masters, previews, slices, and provenance.
6. **No hidden generation.** Fetching, PDF rendering, and CI never start
   ComfyUI.

## Files

An individual scope or aggregate leaf owns:

```text
data/poster_assets/<asset-key>/
  poster.yaml
  cutouts/
    manifest.json
    pokemon_*.png
  logos/
    manifest.json
    ...
  comfyui_poster/                 # ignored local workspace
    individual_spatial_reference_*.png # default v7 topology
    individual_spatial_joint_prompt.generated.txt # default v7 topology
    joint_scene_cast_reference.png # legacy spatial_identity_joint only
    identity_reference_*.png       # legacy spatial/regional topologies
    joint_scene_prompt.generated.txt # legacy spatial topology only
    joint_scene_regional_identity_prompt.generated.txt # regional only
    workflow_api_*.json
    output/
    temp/
  poster-flux2-artwork.png        # promoted text-free master
  poster-flux2.png                # deterministic preview with overlay
  poster-flux2-cards/             # promoted physical crops
  poster-flux2-provenance.json
```

An aggregate root additionally owns `posters.yaml`. It binds stable section IDs
to independent leaf manifests and PDF insertion points. Generation and
promotion never occur against the aggregate root as one ambiguous image.

## Layout contract

`standard_3x3` is the A4 production default. The same layout object drives:

- safe title and information cells;
- subject card envelopes and visible padding;
- reference and conditioning placement;
- generated prompt coordinates;
- output raster dimensions;
- promotion validation;
- physical card slicing;
- PDF placement.

At 300 dpi the current 3×3 text-free master is 2368 × 3268 px and each card
crop is 750 × 1050 px. Cumulative physical endpoints close exactly on the real
canvas even when latent alignment creates one-pixel differences between source
cells.

`wide_4x3` and `wide_4x4` remain modeled extension points. They must use matching
physical page formats and must not be squeezed onto A4.

The normal cast size equals the layout column count. Aggregate sections may
declare fewer canonical subjects when that is the complete source set. Those
subjects are distributed across the bottom row without duplication; for
example, the two Primal Reversions occupy the outer cards of a 3×3 poster.

## Scope manifest

The default generation contract for a new scope is:

```yaml
artwork:
  scene:
    concept: ...
    setting: ...
    lighting: ...
    rendering: ...
    ground_noun: ...
  generation:
    engine: flux
    model: flux-2-klein-4b-fp8.safetensors
    encoder: qwen_3_4b.safetensors
    vae: flux2-vae.safetensors
    mode: joint_scene
    reference_mode: individual_spatial_joint
    seed: ...
    steps: 4
    generation_megapixels: 1.0
    output_dpi: 300
    output_method: lanczos
```

`joint_scene` also supports the accepted `spatial_identity_joint` legacy
topology and the deliberately selected `regional_identity_joint` topology for
Generation III. Existing promoted manifests remain unchanged and reproducible;
the reference topology is part of generation metadata and the fingerprint
rather than a separate generation mode.

The fallback changes the active mode/output contract to:

```yaml
mode: identity_lock
reference_mode: two_pass_source_pixels
output_dpi: 300
output_method: model_upscale
upscale_model: RealESRGAN_x4plus_anime_6B.pth
upscale_model_sha256: <from the matching run metadata>
```

The runner records the hashes for the FLUX model, encoder, VAE, and upscaler.
Before IL promotion, its complete `generation` object becomes the active
manifest contract; every hash is mandatory. No promoted scope currently uses
IL, but the fallback remains reproducible and explicitly selectable.

## Prompt ownership

Full prompts are generated, not maintained per scope. They combine:

1. the exact creative scene from `config/poster_scenes.yaml`;
2. scope metadata;
3. layout-safe title/information cells;
4. normalized subject rectangles, baselines, and padding;
5. supplied subject identity and anatomy rules;
6. coherent lighting, grounding, shadow, and depth rules;
7. exclusions for generated text, boxes, landing pads, paths, extra
   characters, and layout guides.

Text and logos are deliberately absent from model output. They are localized
and rendered after the text-free artwork has passed review.

The overlay has two semantic profiles. `set_summary` renders the localized set
name, card count, release label/date, localized logo where available, and the
project mark. `section_summary` renders localized subtitle or region, card
count, description/range, and the project mark. It also includes the section
title when the separate upper title represents a collection, as on Pokédex
posters; Ex-generation posters omit that row because their upper title already
is the section title. Every current aggregate section provides all nine PDF
translations; an individual TCG set follows only the languages advertised by
its fetched set data.
Section titles with one supported trailing logo token preserve that token and
render the tracked transparent logo inline with the localized title, directly
on the artwork. Text-only section titles keep the bounded title panel, while a
set with a complete title logo continues to use that logo by itself.

## Default individual-spatial `joint_scene` graph

Preparation writes one neutral poster-shaped reference per subject. Each
reference contains only that reviewed subject, positioned at the final
layout-derived scale, baseline, and card-safe coordinates. The generated
prompt names each reference and repeats its normalized target bounds.

The ComfyUI graph then:

1. loads the FLUX.2 model, encoder, and VAE;
2. appends the ordered positioned identity references to one conditioning;
3. starts from one `EmptyFlux2LatentImage`;
4. samples once;
5. decodes once;
6. saves the jointly generated scene directly.

There is no shared cast, separate identity-detail view, input landscape,
inpaint target, second sampler, post-decode character composite, mask repair,
source restoration, or learned upscaler. The accepted raw image is resized
with deterministic Lanczos to the exact 300-dpi physical raster.

This topology is pipeline contract v7 and the default for new manifests. Its
seven promoted scopes are Generations IV through IX and `SV03.5`.

## Reproducible spatial `joint_scene` graph

Preparation writes:

- one neutral poster-shaped spatial cast, capped at 0.5 MP, containing the
  reviewed subjects at their final layout-derived positions;
- one neutral 512 px identity reference per subject, retaining the original
  Official Artwork pixels without source resampling;
- one generated prompt snapshot.

The ComfyUI graph then:

1. loads the FLUX.2 model, encoder, and VAE;
2. appends the spatial cast and ordered identity references to conditioning;
3. starts from one `EmptyFlux2LatentImage`;
4. samples once;
5. decodes once;
6. saves the decoded scene directly.

There is no input landscape, inpaint target, second sampler, post-decode
character composite, mask repair, source restoration, or learned upscaler.
The accepted raw image is resized with deterministic Lanczos to the exact
300-dpi physical raster.

Because all pixels are generated, identity approval is visual and fail-closed.
Promotion binds the approval to the exact raw and print pixel hashes, exact
source identities, generation fingerprint, references, prompt, workflow, and
model artifacts.

## Selectable regional `joint_scene` graph

`regional_identity_joint` removes the visible spatial cast. Preparation writes
only the unscaled identity references and a sectioned prompt snapshot. The
graph contains:

1. one global, reference-free landscape conditioning marked as the default;
2. one local conditioning branch per subject with exactly one identity
   reference;
3. one `ConditioningSetAreaPercentage` per branch, derived from that subject's
   complete physical bottom-card cell;
4. one empty FLUX.2 latent, one sampler trajectory, and one decode.

The regional areas are sampler controls, not image inputs, so they cannot be
drawn as boxes, landing pads, or silhouettes. Each local branch jointly
generates its character, ground, shadow, vegetation, and intersections inside
the card while the default branch fills only pixels outside those complete
card areas. That mechanical coverage does not guarantee one continuous scene
prediction across the lower row. There is no mask image, character composite,
inpaint target, or post-decode repair.

This topology is pipeline contract v6. Individual-spatial v7 remains the
default for new manifests. Regional v6 remains selectable so the reviewed
Generation III promotion is reproducible, but it is not a general migration
target.

The 2026-07-30 representative rerender audit closed that broader rollout.
ComfyUI's default-combine semantics exclude the global landscape prediction
inside each complete card area, so a local branch can generate a second
horizon or card-sized scene. Making the global condition additive removed the
split but averaged away subject identity even after one bounded 2:1
local/global test. Those experimental changes were reverted. Generation III
remains the sole reviewed regional-v6 promotion; individual-spatial v7 remains
the production default, and further seed or prompt sweeps are not justified.

## `identity_lock` fallback

The fallback intentionally chooses exact identity over full scene integration.
It builds the background and source-aware upper context in two FLUX.2 passes,
keeps the reviewed figures immutable, and verifies every fully opaque source
pixel against the raw ComfyUI result. It then uses the configured illustration
upscaler to reach the same physical print raster.

The fallback is not automatic. If a scope cannot pass one-shot review, its
manifest is switched deliberately and a matching candidate is promoted. This
avoids two competing active contracts or silent degradation.

## Promotion

Promotion is transactional:

1. validate that candidate generation metadata equals `poster.yaml`;
2. rebuild and compare the semantic generation fingerprint;
3. require either bound `joint_scene` visual approval or the IL exact-pixel
   audit;
4. validate print dimensions;
5. install the text-free master;
6. render the deterministic localized preview;
7. slice every physical card;
8. write provenance containing input, review/audit, and output hashes;
9. replace the stable bundle atomically.

Changing scene, reference topology or inputs, model, mode, layout, prompt
contract, or source pixels invalidates the generation fingerprint. Changing
only localized overlay inputs can refresh preview/slices from the stable
text-free master without ComfyUI.

## PDF and CI integration

The PDF layer discovers only enabled, promoted bundles. For each language it
applies the localized title/logo and information block, then either slices with
the shared layout (`cards`, default) or draws the complete physical-grid image
once (`full-page`). Both presentations insert the poster after the configured
cover. `--skip-poster` bypasses discovery and keeps the established cover-based
PDF path available.

Presentation is not a second asset contract. Both modes consume the same
promoted text-free master and deterministic overlay. For `standard_3x3`, the
continuous image remains 200.5 × 276.7 mm and is centered on A4; it is not
stretched to page edges and receives no cutting guides. A distinct filename
prevents it from overwriting the normal cuttable build.

Keeping the cover is currently deliberate. The poster now carries its semantic
information, but removing covers changes pagination and the visual contract for
every scope. That migration requires an explicit renderer option plus
multilingual rendered-PDF review after the affected posters are promoted; it is
not coupled to artwork generation or promotion.

Pull requests run the same validator and PDF/release-candidate builders as a
release, but upload only a temporary Actions artifact. A separate tag-only job
may publish after a successful `v*` build.

## Extension boundary

Adding a model family is not the current extension mechanism. First prove that
the existing one-shot fails a hard gate across the bounded experiment budget.
Only then may a new workflow writer be considered, and it must still preserve:

- empty-target joint synthesis;
- separate identity authority for every subject;
- layout-driven placement;
- one final sampler/decode;
- no post-decode subject replacement;
- deterministic print output;
- complete promotion provenance.

Rejected Anima, FLUX.1, Qwen, SDXL, and DreamO implementations are intentionally
not retained as runnable production code. Their evidence is available in the
experiment log and Git history.
