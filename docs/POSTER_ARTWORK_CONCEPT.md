# Poster Artwork

Poster artwork is a reviewed, scope-specific asset. It is generated separately
from the normal data pipeline so PDF generation can eventually consume a stable
PNG without downloading or generating images during a build.

The branch acceptance matrix, remaining production requirements, and cleanup
boundary are tracked in [Poster Artwork Feature Status](POSTER_ARTWORK_STATUS.md).

The promoted scopes currently are:

- `Base1`: Mewtwo, Bulbasaur, and Charmander in a late-1990s research meadow.
- `SV03.5`: Bulbasaur, Charmander, and Squirtle in a Kanto coastal meadow for
  Scarlet & Violet - 151.

Both use the same `3x3` physical-card layout and the same generator code. Any
subject-specific compensation lives in the scope manifest.

## Files

Each scope stores its poster inputs and output below
`data/poster_assets/<scope>/`:

```text
poster.yaml
poster-flux2-artwork.png
poster-flux2.png
poster-flux2-cards/
poster-flux2-provenance.json
logos/
  logo-<language>.png
comfyui_poster/
  prompt.txt
  inpaint_prompt.txt
  anima_prompt.txt
cutouts/
  manifest.json
  pokemon_<id>_<name>.png
```

Only reviewed source assets and the final render belong in this directory.
Generator previews, masks, model workflows, and other iteration artifacts are
local scratch data and must not be committed.

The local ComfyUI flow keeps its reviewed prompts in `comfyui_poster/`. Generated
scene references, identity references, API workflows, temporary files, raw
artwork, and iteration previews are ignored. A candidate enters source control
only through the explicit transactional promotion step, together with its
provenance record.

## Layout rules

- Layout geometry is defined in `scripts/poster_assets/layout.py`.
- Manifest rows and columns are 1-based.
- The Pokemon count follows the number of layout columns.
- Pokemon occupy the bottom row, one per column.
- Title and set information stay inside the cells configured in `poster.yaml`.
- The information panel is centered in its cell and capped by
  `max_height_ratio`; longer localized names wrap and shrink inside their
  assigned row instead of growing the panel toward another card.
- Pokemon silhouettes stay inside their card cells; the continuous background
  may cross cut lines.
- Missing layout-required Pokemon or source assets are hard errors.

The `Base1` layout is:

```text
[ background ][ set title  ][ background ]
[ background ][ set info   ][ background ]
[  Mewtwo    ][ Bulbasaur  ][ Charmander ]
```

## Workflow

Fetch transparent official-artwork cutouts:

```bash
venv/bin/python scripts/poster_assets/fetch_cutouts.py --scope Base1
```

The fetcher selects `featured_elements` from `data/output/<scope>.json`, then
uses the explicit fallback list in `poster.yaml` if the layout needs more
Pokemon. Existing reviewed cutouts are not overwritten unless `--force` is
passed.

Fetch every localized title logo configured in `poster.yaml`:

```bash
venv/bin/python scripts/poster_assets/fetch_title_logos.py --scope SV03.5
```

The fetcher resolves the language URLs from `data/output/<scope>.json`, writes
stable local RGBA PNGs, and never leaves PDF generation dependent on the network.

## Local ComfyUI workflow

The production flow creates the complete scene and Pokemon artwork with FLUX.2
Klein, then adds panels and typography deterministically. The retired
background-compositing flow and its generated layout guide have been removed.

Start the local Metal-enabled ComfyUI server:

```bash
scripts/poster_assets/start_comfyui_poster.sh
```

Model weights remain outside this repository. The promoted FLUX flow expects
these files below the ComfyUI `models/` directory:

```text
diffusion_models/flux-2-klein-4b-fp8.safetensors
text_encoders/qwen_3_4b.safetensors
vae/flux2-vae.safetensors
upscale_models/RealESRGAN_x4plus_anime_6B.pth
```

The reviewed SHA-256 values live in each scope's `poster.yaml`. Every new run
resolves the actual ComfyUI installation from its reported absolute `main.py`
path and hashes the selected local model files; it does not trust filenames
alone. The illustration upscaler is the official
[RealESRGAN x4plus anime 6B release](https://github.com/xinntao/Real-ESRGAN/releases/tag/v0.2.2.4).

The server is scope-specific because ComfyUI resolves `LoadImage` nodes relative
to its configured input directory. Pass the same scope that will be generated:

```bash
scripts/poster_assets/start_comfyui_poster.sh --scope SV03.5
```

In another terminal, run preparation, workflow creation, generation, and final
text compositing with one command:

```bash
venv/bin/python scripts/poster_assets/run_comfyui_poster.py \
  --engine flux --flux-mode edit --scope Base1 \
  --seed 260716311 --megapixels 0.5 --language en
```

The default generates the cohesive scene at 0.5 MP, applies the configured
Real-ESRGAN illustration upscaler, and normalizes the complete text-free artwork
to the exact 300-dpi physical layout before deterministic typography. This keeps
the reliable card-safe FLUX character scale while producing a 2368 x 3268 px
poster and nine 750 x 1050 px cards. It does not composite or move Pokemon after
sampling.

The FLUX and Anima branches are independent and can be compared with identical
inputs. `both` runs them sequentially and keeps engine-specific final filenames:

```bash
venv/bin/python scripts/poster_assets/run_comfyui_poster.py \
  --engine both --scope Base1 --seed 260716204 --megapixels 0.25 --language de
```

| Engine | Prompt | Scene input | Workflow | Final filename marker |
| --- | --- | --- | --- | --- |
| FLUX.2 Klein edit | `prompt.txt` | `scene_reference.png` | `workflow_api_edit_<size>_<seed>.json` | `_flux_edit_..._poster_` |
| FLUX.2 Klein inpaint | `inpaint_prompt.txt` | `scene_reference.png` | `workflow_api_inpaint_<size>_<seed>.json` | `_flux_inpaint_..._poster_` |
| AnimaEdit | `anima_prompt.txt` | `anima_scene_reference.png` | `anima_workflow_api.json` | `_anima_poster_` |

Anima defaults to `AnimaYume_tuned_v05.safetensors`; another compatible
backbone can be selected with `--anima-model` without changing the engine API.
Its default `--anima-mode generate` uses an empty target latent while supplying
the exact character composition through Cosmos reference conditioning. The
diagnostic `edit` mode retains the abstract material scaffold and is not the
preferred poster path.

Anima is currently frozen as an experimental engine. The validated edit path
preserves the three protected identity cores and avoids duplicate characters,
but tends to retain abstract source geometry too literally. The empty-target
`generate` path is implemented for the next experiment but has not yet been
promoted or rendered at production resolution.

Preparation creates one clean scene reference from every reviewed cutout at its
exact intended position, size, and shared ground level. It also creates one compact
neutral-canvas identity reference per subject. The workflow derives their count,
order, English names, and invisible left-to-right print regions from the cutout
manifest; no Pokemon name or fixed three-image chain remains in Python code.
Position comes only from the combined scene image. Individual references preserve
anatomy while their padding reinforces relative scale. None of these references
contains a layout grid, landing pads, paths, text boxes, or previous generated
artwork.

Rare model-specific compensation is explicit and reviewable in `poster.yaml`.
For example, Base1 makes Mewtwo smaller and left-biased in the conditioning image,
while all SV03.5 subjects use the defaults:

```yaml
conditioning:
  identity_defaults:
    canvas_px: 512
    min_subject_px: 150
    max_subject_px: 350
  subjects:
    150:
      composition:
        scale: 0.22
        x_offset_cell: -0.28
        baseline_offset_cell: 0.10
      identity:
        canvas_px: 768
        align_x: left
      prompt_notes:
        - Preserve the reviewed head contour and complete silhouette.
```

This replaces the former aspect-ratio heuristic that treated every tall subject
like Mewtwo.
The two FLUX modes deliberately use mutually exclusive conditioning topologies.
`inpaint` keeps the Pokemon as the unmasked source of `VAEEncodeForInpaint` and
does not add a `ReferenceLatent`. `edit` uses an independent empty target latent
and supplies the composition only through `ReferenceLatent`. Feeding the same
composition through both paths presents every subject twice and is prohibited by
tests because it encourages duplicates and anatomy adjacent to silhouettes. The
FLUX finalizer no longer composites identity pixels after sampling. Every
landscape element follows one camera-space depth order: elements may occlude a
Pokemon only when they are genuinely closer to the camera. This is a general
perspective rule, not a special case for grass, feet, or the lower edge.

FLUX.2 Klein 4B generation remains stochastic. At higher resolutions it can
occasionally invent anatomy adjacent to a silhouette or duplicate a referenced
subject. Such candidates must be rejected during visual review; neither FLUX mode
uses a post-sampling identity composite to conceal these failures.

The default remains the distilled 4-step model. The undistilled Base model can be
evaluated without changing the workflow architecture:

```bash
venv/bin/python scripts/poster_assets/run_comfyui_poster.py \
  --engine flux --flux-mode inpaint \
  --flux-model flux-2-klein-base-4b-fp8.safetensors --flux-steps 24 \
  --scope Base1 --seed 260715201 --megapixels 0.25 --language en
```

The initial controlled 0.25 MP comparison used seed `260716301`. True inpainting
avoided duplicates but reinterpreted all three Pokemon as generic animals. Base 4B
with 24 steps produced richer scenery but increased character drift. The correctly
wired distilled 4-step `edit` mode produced exactly three correctly placed subjects
and is therefore the default. Compact scale-aware identity references preserve
Mewtwo's head anatomy without promoting it beyond its bottom-left print region.
Generating at 0.5 MP also gives the model enough spatial precision to keep the
wide pose inside that region. These experiments show that additional diffusion
steps alone do not solve reference-identity hallucinations.

The promoted Base1 candidate is `poster-flux2.png`, generated with seed
`260716311`, distilled FLUX.2 Klein 4B, four steps, `edit` mode, and `identity`
reference mode. The cohesive scene was sampled at 0.5 MP and upscaled as a whole
to the exact 300-dpi layout before the deterministic overlay. Identity mode supplies three
compact appearance references followed by the combined scene composition. The
prompt labels those roles explicitly so anatomy and invisible print-safe geometry
reinforce each other rather than competing.

The promoted SV03.5 candidate uses the same model and topology with seed
`260726101`. It was sampled at 0.5 MP, upscaled as one complete text-free scene
to 300 dpi, and visually checked both as a whole and as the three separate bottom-card
crops. No Base1 conditioning override is applied.

FLUX.2 Klein 9B FP8 with the 8B FP4-mixed encoder was also validated technically
on MPS after adding CPU-side NVFP4 dequantization. On a 16 GB M4, however, prompt
encoding plus model loading consumed roughly 12.7 GB of swap and took about ten
minutes before sampling began. BFL documents the KV variant for approximately
29 GB VRAM, so neither 9B path is considered a practical local poster engine on
this machine. The failed 9B weights are not retained locally.

The finalizer never adds or alters Pokemon. It only draws the set logo, localized
set name, card count, release date, project signature, and deterministic panel
design. Exact spelling and typography therefore remain independent from the image
model without breaking the integrity of the generated scene.

After review, promote the exact text-free 300-dpi candidate. This transaction
installs the stable artwork, deterministic localized preview, all physical card
crops, and a complete provenance record only after every output succeeds:

```bash
venv/bin/python scripts/poster_assets/promote_comfyui_poster.py \
  --scope SV03.5 \
  --artwork data/poster_assets/SV03.5/comfyui_poster/temp/<candidate>_print.png \
  --run-metadata data/poster_assets/SV03.5/comfyui_poster/temp/<candidate>_print.run.json \
  --language de
```

Promotion also requires the candidate's generation metadata to match the
reviewed `artwork.generation` block exactly. A changed seed, model, encoder,
upscaler, or output method therefore fails before any stable file is replaced.

Validate the committed bundle, hashes, dimensions, and embedded dpi metadata:

```bash
venv/bin/python scripts/poster_assets/validate_promoted_poster.py --scope SV03.5
```

Every finalized poster is then exported into one PNG per physical card cell. The
card crops use the same `PageLayout` geometry that prepared the references and
discard the binder gaps between cells. For `standard_3x3`, this produces nine
files named `card_r1_c1.png` through `card_r3_c3.png`; the three Pokemon must each
remain completely inside one of the three bottom-row files.

## PDF and binder integration

An optional `pdf` block in `poster.yaml` enables a poster page for a scope. The
configured file is the text-free generated artwork, not a language-specific final
poster:

```yaml
pdf:
  enabled: true
  artwork_file: poster-flux2-artwork.png
  insertion: after_first_section_cover
```

During PDF generation, `PosterPageRenderer` applies the deterministic logo and
localized text for the requested language, slices the result with the shared
`PageLayout`, and draws all nine images at the existing physical card positions.
The page therefore uses the same 63.5 x 88.9 mm cards, 5 mm binder gaps, and
cutting guides as normal collection pages. It is inserted exactly once after the
first section cover.

## Current boundary

Base1 and SV03.5 now both have promoted text-free artwork, deterministic localized
overlays, card-slice exports, and complete PDF integration. Additional scopes opt
in through their own `poster.yaml` only after a text-free artwork passes the same
whole-poster, per-card, and rendered-PDF review.
