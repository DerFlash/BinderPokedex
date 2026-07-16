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
  --engine flux --scope Base1 --seed 260715201 --megapixels 1.0 --language en
```

The FLUX and Anima branches are independent and can be compared with identical
inputs. `both` runs them sequentially and keeps engine-specific final filenames:

```bash
venv/bin/python scripts/poster_assets/run_comfyui_poster.py \
  --engine both --scope Base1 --seed 260716204 --megapixels 0.25 --language de
```

| Engine | Prompt | Scene input | Workflow | Final filename marker |
| --- | --- | --- | --- | --- |
| FLUX.2 Klein | `prompt.txt` | `scene_reference.png` | `workflow_api.json` | `_flux_poster_` |
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
The exact Pokemon pixels are present in the initial inpainting latent before
sampling and are also supplied as a `ReferenceLatent` so FLUX.2 can plan the full
scene around them. A generated identity-core mask protects the recognizable
interior of each official Pokemon exactly, while a narrow contour permits natural
occlusion, edge lighting, and contact with the environment. Every
landscape element follows one camera-space depth order: elements may occlude a
Pokemon only when they are genuinely closer to the camera. This is a general
perspective rule, not a special case for grass, feet, or the lower edge.

FLUX.2 Klein 4B reference editing remains stochastic outside the protected core.
At higher resolutions it can occasionally invent anatomy adjacent to a silhouette
or duplicate a referenced subject. Such candidates must be rejected during visual
review and must never be promoted merely because their protected pixels match.

The finalizer never adds or alters Pokemon. It only draws the set logo, localized
set name, card count, release date, project signature, and deterministic panel
design. Exact spelling and typography therefore remain independent from the image
model without breaking the integrity of the generated scene.

## Current boundary

The standalone Base1 poster asset is implemented and reviewed. PDF integration
and a layout model shared with the PDF renderer are follow-up work; the current
poster layout helper is not yet used by `scripts/pdf/generate_pdf.py`.
