# Poster Artwork

Poster artwork is a reviewed, scope-specific asset. It is generated separately
from the normal data pipeline so PDF generation can eventually consume a stable
PNG without downloading or generating images during a build.

The branch acceptance matrix, remaining production requirements, and cleanup
boundary are tracked in [Poster Artwork Feature Status](POSTER_ARTWORK_STATUS.md).
For commands, use the concise [Poster Workflow](POSTER_WORKFLOW.md). Stable
product decisions and roadmap IDs live in
[Poster Requirements](POSTER_ARTWORK_REQUIREMENTS.md).

The promoted scopes currently are:

- `Base1`: Mewtwo, Bulbasaur, and Charmander in a late-1990s research meadow.
- `SV03.5`: Bulbasaur, Charmander, and Squirtle in a Kanto coastal meadow for
  Scarlet & Violet - 151.

Both use the same `3x3` physical-card layout and the same generator code. Scene
briefs, technical identity-lock bounds, and any rare subject-specific
compensation live in the scope manifest. New `3x3`, `4x3`, and `4x4` scopes use
the same artwork code path. Production PDF output remains `3x3`/A4 until
matching A3 page renderers are implemented for the wide layouts.

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
  flux1_canny_prompt.txt
  qwen_edit_prompt.txt
cutouts/
  manifest.json
  pokemon_<id>_<name>.png
  pokemon_<species-id>_artwork_<form-id>_<name>.png
```

Only reviewed source assets and the final render belong in this directory.
Generator previews, masks, model workflows, and other iteration artifacts are
local scratch data and must not be committed.

The legacy experimental engines keep their reviewed prompts in
`comfyui_poster/`. The production identity-lock prompt is built from the
reviewed `artwork.scene` brief in `poster.yaml` plus one central immutable-source
contract. Its exact `identity_lock_prompt.generated.txt` snapshot is hashed into
run provenance but ignored as local scratch. Generated scene references,
identity references, API workflows, masks, temporary files, raw artwork, and
iteration previews are also ignored. A candidate enters source control only
through the explicit transactional promotion step, together with its provenance
record.

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
- `standard_3x3` is the A4 production default. `wide_4x3` and `wide_4x4`
  retain full physical card size and advertise A3 landscape and A3 portrait as
  their future matching PDF page families.

The `Base1` layout is:

```text
[ background ][ set title  ][ background ]
[ background ][ set info   ][ background ]
[  Mewtwo    ][ Bulbasaur  ][ Charmander ]
```

## Workflow

Initialize another individual TCG set directly from
`data/output/<scope>.json`:

```bash
python scripts/poster_assets/init_poster_scope.py \
  --scope SV04 --layout standard_3x3 --fetch
```

The initializer creates an identity-lock manifest from the reviewed Base1 model
contract, copies the scope's explicit creative brief from
`config/poster_scenes.yaml`, derives a stable scope seed, configures every
available localized logo, selects the layout column count, and optionally
fetches the transparent featured Pokemon and logos. It rejects aggregate scopes
that cannot provide one unambiguous set name and publication date. PDF
integration starts disabled and is enabled only after promotion.

After fetching all data, missing individual-set manifests can be prepared
without overwriting reviewed manifests:

```bash
python scripts/poster_assets/init_poster_scope.py --all-tcg-sets --fetch
```

Every current individual TCG set must have a catalog entry; exact coverage is
enforced by tests. A scope owns only the creative fields while the source-pixel,
continuous-ground, safe-area, no-text, no-path, and no-landing-pad rules remain
central:

```yaml
artwork:
  scene:
    concept: a Kanto collection
    setting: >-
      A quiet coastal meadow with layered woodland, distant hills, weathered
      coastal forms, and a glimpse of a calm blue bay.
    lighting: Warm late-afternoon sunlight enters from the upper left.
    rendering: >-
      Use clean linework, restrained natural colors, and gentle atmospheric
      depth.
    ground_noun: meadow
```

Fetch transparent official-artwork cutouts:

```bash
venv/bin/python scripts/poster_assets/fetch_cutouts.py --scope Base1
```

The fetcher selects `featured_elements` from `data/output/<scope>.json`, then
uses the explicit fallback list in `poster.yaml` if the layout needs more
Pokemon. Existing reviewed cutouts are not overwritten unless `--force` is
passed. The cover/card `image_url` is not a cutout source. The fetcher consumes
the separate validated `poster_subject`, whose canonical PokeAPI Official
Artwork ID distinguishes base species, Mega/Primal forms, and X/Y variants.
Legacy ExGen/ME featured records recover that identity through their `card_id`
and source card. Form cutout filenames include both species and artwork IDs;
missing or inconsistent form artwork is a hard error with no base fallback.
The form-to-species relationship is verified offline against the pinned
`config/pokeapi_form_species.json` registry.

Fetch every localized title logo configured in `poster.yaml`:

```bash
venv/bin/python scripts/poster_assets/fetch_title_logos.py --scope SV03.5
```

The fetcher resolves the language URLs from `data/output/<scope>.json`, writes
stable local RGBA PNGs, and never leaves PDF generation dependent on the network.

## Local ComfyUI workflow

The production flow creates a complete scene with FLUX.2 Klein while protecting
the reviewed Pokemon source pixels, then adds panels and typography
deterministically. The retired generated-background layout guide and its visible
landing-pad composition have been removed.

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

The experimental structure-controlled FLUX.1 path additionally uses
[ComfyUI-GGUF](https://github.com/city96/ComfyUI-GGUF) and these external files:

```text
unet/flux1-dev-Q4_K_S.gguf
clip/clip_l.safetensors
clip/t5-v1_1-xxl-encoder-Q4_K_S.gguf
vae/ae.safetensors
controlnet/instantx_flux_canny.safetensors
```

It is intentionally a separate engine. It does not replace or mutate the FLUX.2
or Anima workflows.

The Qwen multi-reference experiment uses the same GGUF loader and these external
files:

```text
unet/qwen-image-edit-2511-Q3_K_M.gguf
text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors
vae/qwen_image_vae.safetensors
loras/Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors
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
  --engine flux --flux-mode identity_lock --scope Base1 \
  --seed 260726503 --megapixels 1.0 --language en
```

The default `identity_lock` mode runs two four-step FLUX passes at 1 MP, applies
the configured Real-ESRGAN illustration upscaler, and normalizes the complete
text-free artwork to the exact 300-dpi physical layout before deterministic
typography. This produces a 2368 x 3268 px poster and nine 750 x 1050 px cards.
The exact figures enter the ComfyUI graph between the two passes; the final pass
sees their composition but cannot edit their protected lower band.

Overscan scales with the target dimensions and remains latent-aligned. The
second-pass protection band normally reaches 70 percent of the image height; if
an unusually tall reviewed subject begins above that boundary, the mask moves
up automatically and retains configurable clearance above its silhouette.

The FLUX and Anima branches are independent and can be compared with identical
inputs. `both` runs them sequentially and keeps engine-specific final filenames:

```bash
venv/bin/python scripts/poster_assets/run_comfyui_poster.py \
  --engine both --scope Base1 --seed 260716204 --megapixels 0.25 --language de
```

| Engine | Prompt | Scene input | Workflow | Final filename marker |
| --- | --- | --- | --- | --- |
| FLUX.2 Klein edit | `prompt.txt` | `scene_reference.png` | `workflow_api_edit_<size>_<seed>.json` | `_flux_edit_..._poster_` |
| FLUX.2 Klein inpaint | `inpaint_prompt.txt` | `inpaint_reference.png` | `workflow_api_inpaint_<size>_<seed>.json` | `_flux_inpaint_..._poster_` |
| FLUX.2 source-pixel lock | generated from `poster.yaml` | `inpaint_reference.png`, `upper_context_mask.png` | `workflow_api_identity_lock_<size>_<seed>.json` | `_flux_identity_lock_..._poster_` |
| AnimaEdit | `anima_prompt.txt` | `anima_scene_reference.png` | `anima_workflow_api.json` | `_anima_poster_` |
| FLUX.1 Dev Canny | `flux1_canny_prompt.txt` | `structure_reference.png` | `flux1_canny_workflow_api_<size>_<seed>.json` | `_flux1_canny_..._poster_` |
| Qwen Image Edit 2511 | `qwen_edit_prompt.txt` | composition plus two identity sheets | `qwen_edit_workflow_api_<size>_<seed>.json` | `_qwen_edit_..._poster_` |

Run the FLUX.1 experiment independently:

```bash
venv/bin/python scripts/poster_assets/run_comfyui_poster.py \
  --engine flux1_canny --scope Base1 \
  --seed 260726201 --megapixels 1.0 \
  --flux1-steps 20 --flux1-control-strength 0.75 \
  --language en
```

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

The FLUX.1 Canny adapter uses a fourth prepared representation:
`structure_reference.png` flattens the exact final-size cutouts on opaque white.
The workflow derives Canny edges from it and applies those edges for the full
sampling interval. This constrains both outer silhouettes and visible internal
lines such as Mewtwo's face, chest, fingers, limbs, and tail while the scene and
all three subjects are still drawn in one diffusion pass. It is not a
post-generation character composite.

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
The three FLUX modes deliberately use separate conditioning topologies.
`edit` uses an independent empty target latent and supplies the compensated
composition through `ReferenceLatent`. It remains useful for fully generative
experiments but can reinterpret anatomy. Direct `inpaint` keeps the figures as
unmasked source pixels and restores them after VAE decoding; testing showed that
FLUX can still extend a visible contour into the generated background.

The production `identity_lock` path therefore separates scene invention from
composition context:

1. A first four-step pass generates a full-bleed, character-free landscape with
   latent overscan; only the landscape is center-cropped.
2. The exact final-size reviewed cutouts are placed together on that one
   continuous ground inside the ComfyUI graph.
3. A second four-step pass sees this complete composition but its soft edit mask
   ends above the entire bottom subject band.
4. The protected lower band is restored exactly after decoding, so neither
   diffusion, the VAE, nor the upstage context pass can change a source pixel.

This is not blind placement into a finished scene: the final generative pass sees
where every figure stands and completes the upper environment accordingly. It
does intentionally give up free landscape occlusion across the protected
silhouettes. The lower band is one shared, low-detail ground plane rather than
three clearings, so that tradeoff does not reintroduce landing pads.

Immediately after ComfyUI returns the 1 MP artwork, the runner compares every
fully opaque source pixel with `inpaint_reference.png`. A one-value RGB
difference is a hard failure before upscaling, typography, or promotion. The
validation method, compared pixel count, and zero-change result are stored in
the run provenance and required again by `validate_promoted_poster.py`.

FLUX.2 Klein 4B generation remains stochastic in `edit` and direct `inpaint`
modes. It can invent anatomy adjacent to a silhouette or reinterpret a supplied
subject even at higher resolution. Those candidates remain hard rejects; source
pixel locking is the production answer when authenticity outranks generative
reinterpretation.

Character authenticity outranks background detail. A candidate fails review if
even one protected subject changes its head or face, chest geometry, digit count,
limbs, tail, body proportions, pose, colors, or defining silhouette. A generated
shape immediately beside a contour also fails if it can be read as an extra body
part. Review is performed against the source cutout at the final bottom-card crop
size, not only against the complete poster.

The default remains the distilled 4-step model. The undistilled Base model can be
evaluated without changing the workflow architecture:

```bash
venv/bin/python scripts/poster_assets/run_comfyui_poster.py \
  --engine flux --flux-mode inpaint \
  --flux-model flux-2-klein-base-4b-fp8.safetensors --flux-steps 24 \
  --scope Base1 --seed 260715201 --megapixels 0.25 --language en
```

The initial controlled 0.25 MP comparison used seed `260716301`. Its inpaint
workflow accidentally reused the edit-compensated composition, so the model saw
undersized or apparently missing subjects and generated generic replacements.
The corrected inpaint topology uses exact final-size cutouts and does not grow
the background mask into their silhouettes. At 0.5 MP, however, small details
still degrade during VAE reconstruction and upscaling. A fresh 2 MP run recovered
more background detail and more of the source linework, but FLUX.2 still generated
subject-like shapes next to open contours. The native edit comparison also
changed Mewtwo's face, chest geometry, and finger count. All of those experimental
candidates are rejected. These experiments show that more pixels and additional
diffusion steps alone do not solve reference-identity hallucinations.

The FLUX.1 Dev Q4_K_S Canny run used seed `260726201`, 20 steps, 1 MP, and
ControlNet strength `0.75`. It retained the broad composition but turned Mewtwo
purple, changed its face and chest, and simplified its hand. The MPS run took
about 34 minutes. Canny constrains geometry, not source identity, so this
candidate is rejected.

The Qwen Image Edit 2511 Q3_K_M run used seed `260726301`, the four-step
Lightning LoRA, and three explicitly labeled references. It produced a detailed
landscape but interpreted the large Mewtwo detail sheet as a giant fourth
character. The 1 MP MPS run took 29:54 and used roughly 18 GB of swap on the
16 GB machine. The adapter remains selectable, but this candidate is also
rejected.

The accepted Base1 baseline is `poster-flux2.png`, generated with seed
`260726503`, distilled FLUX.2 Klein 4B, the two-pass `identity_lock` mode, and
`two_pass_source_pixels` reference mode. Both passes use four steps at 1 MP.
The reviewed cutouts retain their exact 1 MP pixels and card-safe composition
inside the workflow; the whole text-free scene is then model-upscaled to the
exact 300-dpi layout before the deterministic overlay.

The final review checked the complete poster and all three 750 x 1050 bottom
cards. Mewtwo keeps the reviewed face, chest ridges, three digits on each hand,
complete limbs and tail, with additional clear space above and to the right.
No adjacent generated shape reads as extra anatomy.

The promoted SV03.5 candidate uses the same model and topology with seed
`260726101`. Both passes run at 1 MP before the complete text-free scene is
model-upscaled to 300 dpi. Its 62,719 fully opaque source pixels compare exactly,
and the complete poster plus all three bottom-card crops were visually checked.
No Base1 subject-conditioning override is applied.

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

An individual scope keeps its optional `pdf` block in `poster.yaml`. An
aggregate scope instead uses `posters.yaml` as a routing-only index and points
to one isolated leaf `poster.yaml` per section. In both cases the configured
file is the text-free generated artwork, not a language-specific final poster:

```yaml
pdf:
  enabled: true
  artwork_file: poster-flux2-artwork.png
  insertion: after_first_section_cover
```

During 3x3 PDF generation, `PosterPageRenderer` applies the deterministic logo
and localized text for the requested language, slices the result with the shared
`PageLayout`, and draws all nine images at the existing physical card positions.
The page therefore uses the same 63.5 x 88.9 mm cards, 5 mm binder gaps, and
cutting guides as normal collection pages. Legacy single posters are inserted
once after the first section cover. Aggregate bindings use
`after_section_cover`, so each enabled artwork follows its matching cover before
that section's cards. This is normal `scripts/pdf/generate_pdf.py` behavior; no
poster-specific PDF command is needed.

The renderer now matches poster rows and columns against the supplied PDF page
renderer rather than treating nine cards as a universal poster invariant. The
current page renderer is 3x3/A4. A future matching 4x3 or 4x4 page renderer can
reuse the poster renderer; until then, a wide manifest produces an actionable
A3 page-family error instead of being silently scaled or misrendered.

The PDF build consumes only reviewed, promoted local artwork and never starts an
expensive ComfyUI generation implicitly. A one-off build can bypass poster
discovery and asset loading with `--skip-poster`. Its `_NO_POSTER.pdf` suffix
keeps the result separate from the normal PDF. For a persistent per-scope
opt-out, leave `pdf.enabled` false or omit the `pdf` block entirely. For an
aggregate target, leave its routing-index binding disabled.

## Current boundary

Base1 and SV03.5 now both have promoted identity-lock artwork, exact-source-pixel
validation, deterministic localized overlays, card-slice exports, and complete
PDF integration. Every current individual TCG set has cataloged scene direction
and can be initialized from existing scope data, but opts into PDF generation
only after its text-free artwork passes the same whole-poster, per-card, and
rendered-PDF review. The Pokédex now provides nine disabled generation bundles,
regional briefs, section-local starter selection, nine-language overlays, and
section-aware PDF routing. Their artworks still require generation and
promotion under [#2](https://github.com/DerFlash/BinderPokedex/issues/2).
Further aggregate variants and matching wide PDF pages remain roadmap items.
