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

## Current boundary

The standalone Base1 poster asset is implemented and reviewed. PDF integration
and a layout model shared with the PDF renderer are follow-up work; the current
poster layout helper is not yet used by `scripts/pdf/generate_pdf.py`.
