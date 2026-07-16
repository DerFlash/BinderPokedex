# Poster Artwork

Poster artwork is a reviewed, scope-specific asset. It is generated separately
from the normal data pipeline so PDF generation can eventually consume a stable
PNG without downloading or generating images during a build.

The current pilot is `Base1` with a `3x3` layout and three featured Pokemon:
Mewtwo, Bulbasaur, and Charmander.

## Files

Each scope stores its poster inputs and output below
`data/poster_assets/<scope>/`:

```text
poster.yaml
poster.png
background/
  background.png
  composition_guide.png
  manifest.json
  prompt.txt
cutouts/
  manifest.json
  pokemon_<id>_<name>.png
```

Only reviewed source assets and the final render belong in this directory.
Generator previews, masks, model workflows, and other iteration artifacts are
local scratch data and must not be committed.

The optional local ComfyUI flow keeps its prompt in
`comfyui_poster/prompt.txt`. Its generated scene reference, API workflow,
temporary files, raw artwork, and final previews are ignored.

## Layout rules

- Layout geometry is defined in `scripts/poster_assets/layout.py`.
- Manifest rows and columns are 1-based.
- The Pokemon count follows the number of layout columns.
- Pokemon occupy the bottom row, one per column.
- Title and set information stay inside the cells configured in `poster.yaml`.
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

Prepare the configured background prompt and target paths:

```bash
venv/bin/python scripts/poster_assets/generate_background.py --scope Base1
```

This also rebuilds `background/composition_guide.png` from the real cutouts and
the renderer's exact placement geometry. Background generation must use that
image as a planning reference. It communicates character identity, silhouette,
scale, contact baseline, text regions, and foreground-detail exclusion halos;
none of the guide overlays or characters belong in the generated background.

Import a reviewed generated or curated background:

```bash
venv/bin/python scripts/poster_assets/import_background.py \
  --scope Base1 \
  --mode generated \
  --tool <tool-or-model> \
  --file <generated-image>
```

For curated images, use `--mode curated` and provide source, author, and license
metadata. The importer validates dimensions, normalizes the image to RGB PNG,
and records provenance in `background/manifest.json`.

Render the poster:

```bash
venv/bin/python scripts/poster_assets/render_poster.py --scope Base1 --force
```

The renderer is deterministic for a given Python/Pillow/font environment. It
fits the reviewed background, adds title and set information, then applies
restrained relighting, contact shadows, and foreground grass to the cutouts.

The guide and final render share `cutout_placements()`, so background planning
and compositing use the same pixel geometry. If cutouts, layout, or placement
rules change, regenerate the guide and background before rendering the poster.

## Local ComfyUI hybrid workflow

The preferred experimental flow creates the complete scene and Pokemon artwork
with FLUX.2 Klein, then adds panels and typography deterministically. It does not
use `poster.png`, the reviewed background, or any previous generated poster as a
reference.

Start the local Metal-enabled ComfyUI server:

```bash
scripts/poster_assets/start_comfyui_poster.sh
```

In another terminal, run preparation, workflow creation, generation, and final
text compositing with one command:

```bash
venv/bin/python scripts/poster_assets/run_comfyui_poster.py \
  --engine flux --flux-mode edit --scope Base1 \
  --seed 260715201 --megapixels 1.0 --language en
```

The FLUX and Anima branches are independent and can be compared with identical
inputs. `both` runs them sequentially and keeps engine-specific final filenames:

```bash
venv/bin/python scripts/poster_assets/run_comfyui_poster.py \
  --engine both --scope Base1 --seed 260716204 --megapixels 0.25 --language de
```

| Engine | Prompt | Scene input | Workflow | Final filename marker |
| --- | --- | --- | --- | --- |
| FLUX.2 Klein edit | `prompt.txt` | `scene_reference.png` | `workflow_api.json` | `_flux_edit_poster_` |
| FLUX.2 Klein inpaint | `inpaint_prompt.txt` | `scene_reference.png` | `workflow_api.json` | `_flux_inpaint_poster_` |
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

Preparation creates one clean scene reference from the three reviewed cutouts at
their exact intended positions, sizes, and shared ground level. It contains no
layout grid, landing pads, paths, text boxes, or previous generated artwork.
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
and is therefore the default, although Mewtwo's head silhouette still requires a
better identity-conditioning solution. These experiments show that additional
steps alone do not solve reference-identity hallucinations.

The promoted local candidate is `poster-flux2.png`, generated at 1 MP with seed
`260716303`, distilled FLUX.2 Klein 4B, four steps, `edit` mode, and `identity`
reference mode. Identity mode supplies IMAGE 1 as the sole layout authority and
then appends one high-resolution original cutout per character. The prompt labels
those roles explicitly so the close-ups strengthen anatomy without becoming extra
subjects. Generated identity references are derived from the original 475 px
cutouts, never from their already reduced poster placements.

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

## Current boundary

The standalone Base1 poster asset is implemented and reviewed. PDF integration
and a layout model shared with the PDF renderer are follow-up work; the current
poster layout helper is not yet used by `scripts/pdf/generate_pdf.py`.
