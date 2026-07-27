# Poster Artwork Workflow

This is the operator guide for creating, reviewing, promoting, and consuming a
scope poster. The detailed implementation rationale lives in
[POSTER_ARTWORK_CONCEPT.md](POSTER_ARTWORK_CONCEPT.md); tracked requirements and
future work live in
[POSTER_ARTWORK_REQUIREMENTS.md](POSTER_ARTWORK_REQUIREMENTS.md).

## Lifecycle at a glance

```text
fetch scope data
  -> inspect the read-only poster work plan
  -> initialize poster manifest and source assets (optional)
  -> review the set scene brief
  -> generate a local ComfyUI candidate (optional)
  -> visually review and promote the candidate
  -> enable the promoted poster for PDF use
  -> generate the normal PDF (poster may be skipped)
```

Data fetching and PDF rendering never start ComfyUI implicitly. Poster
generation is an explicit post-fetch step because it is GPU-intensive,
probabilistic, and subject to a visual promotion gate. A promoted poster is
generated once and then reused deterministically for every supported language.

CI uses the same boundary. Pull requests run a complete, read-only release
rehearsal that validates promoted posters and builds every PDF, ZIP, and the
release manifest without publishing a GitHub Release. Tagged releases reuse
that candidate build and publish only after it succeeds. See
[Release Workflow](RELEASE_WORKFLOW.md).

## Required and optional phases

| Phase | Required for a normal PDF | Required for a poster PDF | May be repeated |
| --- | --- | --- | --- |
| Fetch scope data | yes | yes | whenever source data changes |
| Inspect poster work plan | no | recommended | after fetch/configuration changes |
| Initialize poster scope | no | yes | only when configuration changes |
| Generate ComfyUI candidate | no | yes | until a candidate passes review |
| Promote candidate | no | yes | once per accepted revision |
| Enable `pdf.enabled` | no | yes | configuration choice |
| Build PDF | yes | yes | as needed |
| `--skip-poster` | optional | bypasses poster use | as needed |

## 1. Fetch the scope

```bash
python scripts/fetcher/fetch.py --scope SV04
```

The fetcher writes `data/output/SV04.json`. It does not create or regenerate a
poster. Featured cover imagery and poster-generation subjects are deliberately
separate:

- `featured_elements.image_url` remains the TCG card or cover image;
- `featured_elements.poster_subject` identifies the exact transparent PokeAPI
  Official Artwork used for the poster;
- the subject records the National-Dex species, concrete base/form artwork ID,
  canonical allowlisted URL, and stable key.

This distinction matters for Mega, Primal, Charizard X/Y, and other forms whose
artwork ID differs from the species ID. Older checked-in ExGen/ME output is
resolved deterministically through the featured `card_id` and its source card.
A form-marked card without exact Official Artwork is an error; the workflow
never substitutes base-species art silently.

Form IDs are checked offline against
`config/pokeapi_form_species.json`, which is pinned to one PokeAPI source
commit. When PokeAPI adds a new species or form, update that registry from
`data/v2/csv/pokemon.csv` and review the mapping before the new subject can
enter a poster run.

## 2. Inspect the read-only work plan

After a fetch, ask the planner what actually changed before downloading assets
or starting ComfyUI:

```bash
python scripts/poster_assets/poster_work_plan.py --scope SV04
python scripts/poster_assets/poster_work_plan.py --scope Pokedex
python scripts/poster_assets/poster_work_plan.py \
  --scope Pokedex/sections/gen3
python scripts/poster_assets/poster_work_plan.py \
  --all-configured \
  --json
```

The planner performs no downloads, writes, GPU work, promotion, or routing
changes. It resolves aggregate routing and compares source data, scene briefs,
cutout selection and pixels, logos, model contracts, effective prompts,
semantic generation fingerprints, overlay fingerprints, and promoted outputs.
Its stable states distinguish missing configuration/assets, readiness to
generate, stale generation, invalid promotion, reviewed-but-disabled promotion,
and a current enabled promotion. Overlay drift is reported with the cheap
`refresh_promoted_overlay` action; it never recommends ComfyUI for text, logo,
translation, panel-design, or `pdf.enabled` changes.

Apply that cheap action directly from the stable promoted artwork and its
embedded generation run:

```bash
python scripts/poster_assets/promote_comfyui_poster.py \
  --scope Pokedex/sections/gen3 \
  --artwork data/poster_assets/Pokedex/sections/gen3/poster-flux2-artwork.png \
  --run-metadata data/poster_assets/Pokedex/sections/gen3/poster-flux2-provenance.json \
  --name flux2 \
  --force
```

Using promoted provenance as `--run-metadata` is an overlay-only refresh. It
revalidates the unchanged generation inputs against their recorded supported
graph contract, then rebuilds the localized preview, card slices, overlay
fingerprint, and output hashes without starting ComfyUI.

Legacy promotions can be upgraded while their original full-manifest,
cutout-hash, output, and regenerated-overlay checks still pass:

```bash
python scripts/poster_assets/migrate_poster_provenance.py --scope Base1
python scripts/poster_assets/migrate_poster_provenance.py --all-enabled
```

Migration adds only semantic provenance metadata. It neither regenerates the
text-free artwork nor changes promoted preview/card files, and it refuses
ambiguous legacy drift instead of guessing. The migration infers only audited
reference topologies and records their historical graph contract; it never
relabels a v1/v2 run as current v3. Such a reviewed promotion remains usable,
while the planner reports the optional `upgrade_generation_pipeline` action.

## 3. Initialize poster configuration and source assets

Initialize one individual TCG set after its data has been fetched:

```bash
python scripts/poster_assets/init_poster_scope.py \
  --scope SV04 \
  --layout standard_3x3 \
  --fetch
```

`standard_3x3` is the default and should normally be omitted. The initializer:

- copies the reviewed model and identity-lock contract;
- embeds the set-specific creative brief from `config/poster_scenes.yaml`;
- derives a stable per-scope seed;
- selects three featured Pokemon for the bottom row;
- keeps different visual forms of one species as distinct poster subjects;
- configures available localized logos;
- fetches exact transparent source cutouts and logos with `--fetch`;
- leaves `pdf.enabled` false until an artwork is reviewed.

After fetching all scopes, every still-missing individual TCG poster manifest
can be prepared in one explicit batch:

```bash
python scripts/poster_assets/init_poster_scope.py \
  --all-tcg-sets \
  --fetch
```

The batch command never overwrites an existing reviewed manifest.

Aggregate scopes use an ordered routing index plus one isolated leaf manifest
per section. Initialize all configured Pokédex generation bundles after its
data fetch with:

```bash
python scripts/poster_assets/init_poster_scope.py \
  --scope Pokedex \
  --all-sections \
  --fetch
```

This keeps `data/poster_assets/Pokedex/posters.yaml` separate from the nine
generation manifests below `Pokedex/sections/`. New bindings begin disabled;
reviewed bindings can then be enabled independently. Each has its own seed and
provenance boundary and selects only that generation's three starter
`featured_elements`. Adding or promoting one generation therefore does not
invalidate another generation's generation fingerprint. Other aggregate scopes
can use the same structure once their section scene briefs are reviewed.

ExGen3 uses the same aggregate lifecycle for its `normal` and `mega` sections:

```bash
python scripts/fetcher/fetch.py --scope ExGen3
python scripts/poster_assets/init_poster_scope.py \
  --scope ExGen3 \
  --all-sections \
  --fetch
python scripts/poster_assets/poster_work_plan.py --scope ExGen3
```

Ordered casts are declared as `section_featured_card_ids` in the scope
configuration. ExGen3 selects Koraidon, Pikachu, and Miraidon for its normal
section and Mega Latias, Mega Diancie, and Mega Lucario for its Mega section.
ExGen2 keeps its reviewed Mega cast at Mewtwo X, Rayquaza, and Latios while
still retaining Mewtwo Y as a separate card and form in the section. A
configured card ID that is missing, duplicated, ambiguous, or assigned to an
unknown section is a hard fetch error. This keeps source updates deterministic
instead of silently changing a reviewed composition.

Form-specific cutout filenames include both species and Official Artwork ID.
The cutout manifest, read-only planner, promotion validator, and generation
fingerprint all verify the same identity. Changing Mega X to Mega Y therefore
requires new cutouts and artwork even though the National-Dex species is
unchanged. Ordinary base-form manifests and fingerprints remain compatible
with already promoted posters. The runner and promotion fingerprint boundary
also reject stale source/cutout selections, so skipping the planner cannot
turn a form back into its base species.

## 4. Review the creative brief

Review `data/poster_assets/<scope>/poster.yaml` for an individual set, or the
selected aggregate leaf such as
`data/poster_assets/Pokedex/sections/gen1/poster.yaml`, especially:

- `artwork.scene`;
- the selected cutouts;
- text-cell locations;
- the generation model, seed, and output settings.

Every current individual TCG set has an explicit seed brief in
`config/poster_scenes.yaml`. The initializer copies that brief into the
manifest. The final production prompt is then generated from four inputs:

1. the set-specific creative scene;
2. scope name, series, and release metadata;
3. the configured card layout and text-safe cells;
4. one central immutable-subject and continuous-ground contract.

This avoids tracked, duplicated full prompts drifting apart. The generated
prompt snapshot is written to the scope's ignored `comfyui_poster/` workspace
when the candidate is prepared. The experimental `joint_scene` mode records its
one-shot scene/identity/placement prompt in the same way; no full prompt is
maintained per scope by hand.

## 5. Start local ComfyUI

```bash
scripts/poster_assets/start_comfyui_poster.sh --scope SV04
```

The project launcher applies the required Apple Metal/MPS compatibility patch
and binds the selected scope's isolated input, output, and temporary
directories.

For one aggregate section, pass its stable asset key:

```bash
scripts/poster_assets/start_comfyui_poster.sh \
  --scope Pokedex/sections/gen1
```

## 6. Generate a candidate

```bash
python scripts/poster_assets/run_comfyui_poster.py --scope SV04
```

The corresponding aggregate command is:

```bash
python scripts/poster_assets/run_comfyui_poster.py \
  --scope Pokedex/sections/gen1
```

For ExGen3, generate each isolated section independently:

```bash
python scripts/poster_assets/run_comfyui_poster.py \
  --scope ExGen3/sections/normal
python scripts/poster_assets/run_comfyui_poster.py \
  --scope ExGen3/sections/mega
```

The production runner reads the complete engine-specific model and sampling
contract, seed, generation size, and output contract from the scope's
`poster.yaml`. Exact-source modes may select a learned illustration upscaler;
`joint_scene` requires deterministic Lanczos output. This includes all Anima
model/LoRA/encoder/VAE/steps/CFG/reference-strength/control-method fields and
the corresponding FLUX.1 Canny or Qwen fields. Only a manifest whose `engine`
matches the selected adapter supplies those values; CLI flags remain explicit
experiment overrides. The default FLUX identity-lock flow:

- generates one cohesive set-specific environment in ComfyUI;
- places exact source figures at their final card-safe positions;
- allows the final context pass to complete only the protected upper scene;
- uses separate latent sampling and soft RGB feather masks so ComfyUI's binary
  inpaint threshold cannot create a horizontal transition seam;
- verifies that every fully opaque source pixel remains unchanged;
- model-upscales to the physical print dimensions;
- writes a localized preview, card crops, workflow, and run metadata.

The command prints the exact candidate and metadata paths needed for promotion.
Exact-source modes write an opaque-source-pixel audit bound to the raw ComfyUI
output and the audit reference. FLUX identity-lock stops immediately if it
changes a source pixel. An experimental Anima, FLUX.1, or Qwen run may finish
with `passed: false` so its visual result can be compared, but that metadata
cannot pass promotion. `joint_scene` has no equality audit because all pixels
are generated; it uses a human review bound to the actual raw and deterministic
print-size files instead.

### Experimental unified scene A/B

`identity_lock` remains the configured production mode. To create a local
comparison without changing the manifest or any PDF binding, override only the
FLUX mode:

```bash
python scripts/poster_assets/run_comfyui_poster.py \
  --scope Pokedex/sections/gen7 \
  --engine flux \
  --flux-mode joint_scene \
  --language en
```

With no output-size flag, the runner inherits the configured 300-dpi target.
`--output-dpi 300` may also be passed explicitly. In `joint_scene` both forms
derive the exact physical raster dimensions through `build_print_layout` and
create the text-free print candidate with deterministic Lanczos scaling; they
never select a learned upscaler. For `standard_3x3`, the 1-MP raw artwork is
848 × 1168 px and the print candidate is exactly 2368 × 3268 px.

The current `joint_scene` graph:

1. derives each target silhouette rectangle from the shared physical layout
   and cutout alpha bounds, then writes its normalized canvas coordinates into
   the one-shot prompt;
2. supplies one neutral 0.5-MP poster-shaped cast as the sole authority for
   count, pose, scale, baseline, and shared card-safe coordinates;
3. supplies one neutral 512 px reference per subject with the original cutout
   at source resolution as the sole identity and anatomy authority;
4. starts from one `EmptyFlux2LatentImage`, invents the complete landscape and
   all characters together, and samples exactly once;
5. decodes and saves that result directly, with no character
   composite, mask repair, or source-pixel restoration afterwards.

The scene brief controls camera, terrain, atmosphere, palette, and broad
composition. The normalized rectangles request position, size, baseline,
visible padding, and card-safe regions. The cast controls only the common
spatial frame; the per-subject references control identity, anatomy,
silhouette, colors, and markings. The model synthesizes landscape and Pokémon
together and resolves z-order, shadows, reflected light, and physically
plausible edge occlusion. A changed body part, face, marking, defining contour,
scale, or placement remains a hard visual rejection. Joint-scene preparation
produces `joint_scene_cast_reference.png` followed by
`identity_reference_1.png` through the current subject count. It neither
produces nor records `inpaint_reference.png`, scene references, identity-lock
masks, or references for unrelated experimental engines.

The graph has no hard three-subject limit. `standard_3x3` remains the default;
four-subject `wide_4x3` and `wide_4x4` candidates need their own memory and
visual review before promotion.

Because `joint_scene` deliberately redraws all pixels, an opaque-source-pixel
equality audit is not applicable. Its hard gates are a complete generation
fingerprint and explicit human review of both the actual raw file and the
deterministically scaled text-free print artwork. The CLI
override above does not make the candidate production artwork: Generation VII
still points to its promoted `identity_lock` result. Candidates through `00017`
are rejected. v5 `00017` passes the spatial, card, shadow, and depth checks but
fails the hard identity gate on Litten's paw and Popplio's facial details. The
v5 graph remains selectable, but it does not become production until a
materially different identity-control mechanism passes every review gate.
Review evidence lives in
`POSTER_ARTWORK_EXPERIMENT_LOG.md` and
`POSTER_ARTWORK_REQUIREMENTS.md`.

## 7. Review and promote

Review all of the following before promotion:

- complete text-free artwork;
- raw ComfyUI artwork before any resize;
- all bottom-row card crops;
- character identity, anatomy, colors, pose, scale, and padding;
- grounding and scenery at every silhouette boundary;
- logo and localized information overlay;
- absence of landing pads, paths, generated text, boxes, or extra creatures.

Promote only an accepted candidate:

```bash
python scripts/poster_assets/promote_comfyui_poster.py \
  --scope SV04 \
  --artwork <printed-text-free-artwork.png> \
  --run-metadata <matching.run.json> \
  --name flux2

python scripts/poster_assets/validate_promoted_poster.py --scope SV04
```

For an aggregate target, use the same asset key for promotion and validation,
for example `Pokedex/sections/gen1`.

Promotion is transactional and records hashes for models, prompts, source
figures, references, workflows, and outputs. Exact-source modes require a
passed `exact_opaque_source_pixels` record; changing the manifest engine or
supplying otherwise matching hashes cannot bypass that gate.

A `joint_scene` candidate follows a separate fail-closed review contract. Its
run must contain the complete current generation fingerprint, exact source
identity records, raw-artwork hashes, and deterministic text-free print hashes.
After comparing both artifacts and every subject crop with the reviewed
cutouts, the reviewer must opt in explicitly:

```bash
python scripts/poster_assets/promote_comfyui_poster.py \
  --scope <scope> \
  --artwork <lanczos-scaled-text-free-artwork.png> \
  --run-metadata <matching.run.json> \
  --name flux2 \
  --approve-joint-scene
```

This flag records a timestamped approval bound to those exact pixels and source
identities; it is not a generic bypass. Promotion still rejects a candidate
whose recorded generation contract differs from `poster.yaml`. The Generation
VII A/B currently has no approval or manifest adoption: candidates through
`00017` are rejected and unpromoted, and neither its promoted artwork nor its
PDF routing has changed.

## 8. Enable and consume the poster

After promotion, review and enable the manifest:

```yaml
pdf:
  enabled: true
  artwork_file: poster-flux2-artwork.png
  insertion: after_first_section_cover
```

For an aggregate scope, enable the matching binding in the root
`posters.yaml` instead. Its leaf manifest remains the immutable generation and
provenance boundary:

```yaml
- id: gen1
  section_id: gen1
  manifest: sections/gen1/poster.yaml
  pdf:
    enabled: true
    artwork_file: poster-flux2-artwork.png
    insertion: after_section_cover
```

The ordinary PDF command then consumes the promoted local artwork:

```bash
python scripts/pdf/generate_pdf.py --scope SV04 --language de
```

The PDF step adds the exact localized logo/information, slices the result, and
embeds it at physical card size. A legacy poster follows the first section
cover; aggregate posters follow their respective configured section covers.
The step does not contact ComfyUI or regenerate the background.

To bypass the poster for one isolated build:

```bash
python scripts/pdf/generate_pdf.py \
  --scope SV04 \
  --language de \
  --skip-poster
```

The output receives a `_NO_POSTER.pdf` suffix.

## Layout policy

| Layout | Subjects | Physical grid | Intended PDF family | Current PDF status |
| --- | ---: | --- | --- | --- |
| `standard_3x3` | 3 | 200.5 × 276.7 mm | A4 portrait | supported and default |
| `wide_4x3` | 4 | 269 × 276.7 mm | A3 landscape | artwork-ready; matching PDF renderer open |
| `wide_4x4` | 4 | 269 × 370.6 mm | A3 portrait | artwork-ready; matching PDF renderer open |

The artwork, placement, prompt, upscale, promotion, validation, and slicing
layers understand all three layouts. The current production PDF renderer remains
3×3/A4. It reports the required matching page family instead of treating wide
layouts as invalid. Wide PDF output must preserve physical card size; it must
not squeeze four binder cards onto A4.

Every raster cell is derived from cumulative physical start and end positions,
not from repeatedly adding independently rounded card and gap widths. Generation
references use both dimensions of the real latent-aligned canvas; finalization,
slicing, promotion, and validation reconstruct the same exact per-cell bounds
from the image itself. At small resolutions, adjacent cards may intentionally
differ by one pixel. At 300 dpi, all layouts retain exact 750 × 1050 card
crops. New runs bind these dimensions and bounds to raster geometry contract v2
inside their engine-specific generation fingerprint.

## Adding a new individual TCG set

Before initializing the new scope:

1. add its regular fetch configuration;
2. fetch its generated `data/output/<scope>.json`;
3. add one explicit creative brief to `config/poster_scenes.yaml`;
4. run the tests, which require exact catalog coverage with no missing or stale
   TCG-set entries;
5. follow the lifecycle above.

No Pokemon names, layout contract, or identity rules should be added to
model-specific Python code.
