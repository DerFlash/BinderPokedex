# Poster Artwork Feature Status

This document records the acceptance state of the poster-artwork feature branch.
It complements the implementation-focused
[Poster Artwork](POSTER_ARTWORK_CONCEPT.md) documentation. Operator commands
live in [Poster Workflow](POSTER_WORKFLOW.md); durable requirement IDs live in
[Poster Requirements](POSTER_ARTWORK_REQUIREMENTS.md).

Last audited: 2026-07-29

## Current accepted baselines

| Scope | Engine | Seed | Artwork verdict | PDF integration |
| --- | --- | ---: | --- | --- |
| `Base1` | FLUX.2 Klein 4B distilled, source-pixel lock v1, 2 x 4 steps | `260726503` | accepted | enabled |
| `Pokedex/sections/gen1` | FLUX.2 Klein 4B distilled, source-pixel lock v1, 2 x 4 steps | `260782266` | accepted | enabled after Generation I cover |
| `Pokedex/sections/gen2` | FLUX.2 Klein 4B distilled, source-pixel lock v1, 2 x 4 steps | `260753030` | accepted | enabled after Generation II cover |
| `Pokedex/sections/gen3` | FLUX.2 Klein 4B distilled, source-pixel lock v2, 2 x 4 steps | `260750880` | accepted | enabled after Generation III cover |
| `Pokedex/sections/gen4` | FLUX.2 Klein 4B distilled, source-pixel lock v2, 2 x 4 steps | `260734875` | accepted | enabled after Generation IV cover |
| `Pokedex/sections/gen5` | FLUX.2 Klein 4B distilled, source-pixel lock v2, 2 x 4 steps | `260735038` | accepted | enabled after Generation V cover |
| `Pokedex/sections/gen6` | FLUX.2 Klein 4B distilled, source-pixel lock v2, 2 x 4 steps | `260758583` | accepted | enabled after Generation VI cover |
| `Pokedex/sections/gen7` | FLUX.2 Klein 4B distilled, source-pixel lock v2, 2 x 4 steps | `260726054` | accepted baseline; grounding refinement tracked | enabled after Generation VII cover |
| `Pokedex/sections/gen8` | FLUX.2 Klein 4B distilled, source-pixel lock v2, 2 x 4 steps | `260715405` | accepted | enabled after Generation VIII cover |
| `Pokedex/sections/gen9` | FLUX.2 Klein 4B distilled, source-pixel lock v2, 2 x 4 steps | `260778637` | accepted | enabled after Generation IX cover |
| `SV03.5` | FLUX.2 Klein 4B distilled, source-pixel lock v1, 2 x 4 steps | `260726101` | accepted | enabled |
| `ExGen3/sections/normal` | FLUX.2 Klein 4B distilled, source-pixel lock v2, 2 x 4 steps | `260711318` | accepted | enabled after the Pokémon ex cover |
| `ExGen3/sections/mega` | FLUX.2 Klein 4B distilled, source-pixel lock v2, 2 x 4 steps | `260751034` | accepted | enabled after the Mega Pokémon ex cover |

All thirteen accepted candidates use the same two-pass source-pixel-lock family.
Its first FLUX pass creates a full-bleed landscape with dynamic, latent-aligned
overscan. The exact reviewed source figures are placed on its one continuous
lower ground before a second FLUX pass sees their final composition and
completes only the upper scene. No diffusion or VAE operation may touch the
protected lower subject band. The resulting 1 MP artwork must pass an exact
opaque-source-pixel comparison, is model-upscaled to the exact 300-dpi physical
layout, and then receives only deterministic typography.

Generations III through IX and both ExGen3 sections use historical graph
contract v2. That graph uses two distinct upper-context masks. A binary,
latent-aligned sampling mask extends below the visible transition, while a
separate soft RGB feather restores the continuous first-pass scene before the
protected figure band. This prevents ComfyUI's internal inpaint-mask rounding
from exposing a horizontal VAE transition seam. Base1, SV03.5, Generation I,
and Generation II remain accepted under their historically accurate v1
contract after visual review.

The current FLUX identity-lock graph contract is v3. It retains the v2 two-mask
topology and adds raster geometry contract v2: cumulative physical endpoints
are mapped to both real canvas axes and recorded with the exact
generation/output dimensions and cell spans. Existing v1/v2 promotions remain
accepted legacy artifacts because their 300-dpi cells are unchanged; the
planner exposes a non-blocking upgrade action instead of relabeling or
regenerating them.

The production baseline is the two-pass source-pixel-lock flow. Direct FLUX
edits, direct silhouette inpainting, native-resolution comparisons, FLUX.1
Canny, and Qwen multi-reference editing remain diagnostic evidence rather than
promoted artwork because their candidates do not satisfy the source comparison
and visual acceptance gate.

## Experimental Generation VII joint-scene

`joint_scene` is an experimental FLUX.2 mode, not an accepted baseline. It uses
the same Generation VII seed `260726054`, distilled FLUX.2 Klein 4B model,
four-step sampling, 1-MP generation canvas, reviewed Rowlet/Litten/Popplio
sources, layout, and scene brief as the current comparison target.

Joint-scene v5 is a true one-shot graph: one empty FLUX.2 target, one sampler,
one neutral 0.5-MP spatial cast, one unscaled 512 px identity reference per
subject, one dynamic scene/identity/placement prompt, and no landscape image.
The spatial cast and normalized rectangles share the physical card
coordinates. No full-scene/cutout draft, `inpaint_reference.png`, post-decode
character composite, source restoration, or learned upscaler belongs to this
mode.

The identity-only graph fixes the contradictory depth ordering seen when a
pre-generated landscape was supplied as a strong final-pass reference.
Candidate `00014` has coherent landscape depth and faithful designs, but all
three figures extend above their bottom-row cards. Candidate `00015` proves
that increasing the neutral identity canvas from 512 to 768 px does not fix
that placement and only increases render cost. v4 candidate `00016` replaces
the separate references with one common poster-shaped cast reference. It puts
all three figures fully inside their card crops and keeps coherent depth, but
invents a large pale marking on Litten's flank/hindquarter. All are rejected
and exhausted the prior v3/v4 one-shot attempt budget.

No Generation VII manifest value, promoted file, Pokédex routing entry, or PDF
binding points to an experimental candidate. The enabled poster remains the
accepted `identity_lock` artwork. Full candidate history, isolated changes, and
rejection reasons live in
[POSTER_ARTWORK_EXPERIMENT_LOG.md](POSTER_ARTWORK_EXPERIMENT_LOG.md). A future
promotion is allowed only after one candidate passes every hard gate in
[POSTER_ARTWORK_REQUIREMENTS.md](POSTER_ARTWORK_REQUIREMENTS.md) and carries a
complete current fingerprint plus explicit review bound to both raw and
print-size pixels. The explicitly selected v5 experiment uses a 0.5-MP spatial
cast plus one unscaled 512 px identity reference per subject before the single
sampler. Product review explicitly tolerates the small print-scale paw and
facial-line simplifications for continued v5 evaluation while retaining gross
anatomy and design as hard gates. Candidate `00018` reuses the canonical
Option-1 placement profile, passes all three physical card crops with preferred
fill, and adds clear coherent grounding shadows. It remains unpromoted because
the landscape again avoids real foreground crossings. `00019` explicitly
requests both connected front and rear crossings, but produces none in any
card. Compact `00020` moves that rule inside the intended 512-token budget but
adds a second oversized Litten and still produces no controlled crossing. Both
prompt experiments are reverted to the `00018` behavior. The graph has no hard
three-subject limit, but four-subject layouts still need separate memory and
visual review.

The earlier successor search was a materially different
identity-control successor, not another FLUX.2 prompt or reference-canvas
retry. The first successor family used one joint SDXL pass with separate
identity adapters, regional subject masks, and source-derived structural
control. Whole-card, exact-silhouette, and tight-box masks all failed subject
identity, grounding, and global scene quality, so that family is closed after
three candidates. Its planned Pokémon-domain-LoRA A/B is intentionally skipped:
a style/domain prior cannot repair a base graph that does not bind the three
references to recognizable bodies.

MS-Diffusion was then reviewed because its published architecture assigns
separate references to explicit bounding boxes. The available ComfyUI port
builds a hidden Diffusers SDXL pipeline, invokes xFormers and CUDA-specific
cleanup paths, samples internally, and returns a final image. Making that port
MPS-safe and exposing the required empty-target, one-sampler, one-decode audit
would be a substantial fork rather than a small compatibility fix. The
technical preflight therefore stops before model installation.

DreamO v1.1 was the next isolated successor experiment. Its native ComfyUI
node accepts three separate VAE-based object references and patches a normal
FLUX model before the common sampler. The pinned graph now completes twelve
steps on Metal/MPS from one empty target to one sampler and one decode. Its
first 0.25-MP preflight renders a clean landscape but omits all three subjects.
DreamO's own post-BEN2 debug outputs retain complete, recognizable Rowlet,
Litten, and Popplio references, which localizes the failure after preprocessing.
The original 765-token prompt also leaves every Pokémon outside FLUX's first
pooled CLIP chunk. A compact, 501-T5-token prompt-binding preflight therefore
kept source images, seed, scene, geometry, model chain, and sampler fixed.
That second output contains Rowlet and Litten but redesigns and oversizes both,
places them outside their required silhouettes, and omits Popplio. It fails
count, identity/anatomy, and card containment before a 1-MP candidate is
justified. DreamO is closed without adding masks, per-subject passes, or
restoration. FLUX.2 RefControl remains unsuitable as a direct fallback because
its single-reference contract does not independently bind three subjects.

The final bounded local reuse test corrected Qwen's old duplicated-subject
topology. It supplied three separate canonical poster-shaped inputs containing
Rowlet, Litten, and Popplio exactly once each at their target card positions,
then used one empty target, one sampler, and one decode. The 0.25-MP Metal
preflight completed in 14:38, but retained the neutral field and rendered only
one oversized Litten across almost the whole canvas. Rowlet, Popplio, the
three-card placement, and the Alola landscape are absent. It therefore fails
multiple coarse hard gates before identity-detail review and receives no 1-MP
or prompt follow-up.

The isolated Anima `generate` preflight uses the same Generation VII seed and
canonical placements at 432 × 592 px. It completes on Metal/MPS in 165.57
seconds with exactly three complete, card-safe subjects, but leaves them on a
flat lawn without convincing contact shadows, terrain response, vegetation
interaction, or occlusion. Its `ImageCompositeMasked` node restores an eroded
identity core after decode, so empty-target sampling still does not produce one
unified final scene. This topology is closed before 1 MP and remains diagnostic
only.

The latest product review prefers FLUX.2 v5 `00018` visually over the
composited `identity_lock` baseline. The small Litten-paw and Popplio face-line
simplifications first measured in
`00017` are acceptable for continued comparison; gross anatomy, silhouette,
marking, or form changes remain hard failures. `00018` removes the separate v5
shrink and outer-shift logic and passes preferred card fit by reusing the exact
canonical Option-1 placement helper. Because it contains no meaningful
foreground crossing, `00019` changes only generic occlusion wording. The model
still avoids every requested intersection. A tokenizer audit finds 1,350
encoded prompt tokens with the decisive instruction after token 1,034.
`00020` compacts it to 510 tokens and moves the rule to token 211, but creates
a fourth character and still no crossing. The experimental prompt commits are
reverted. Prompt tuning is closed; a new attempt requires materially different
control. `00018` remains unpromoted, and `identity_lock` remains the accepted
exact-source fallback until a separate promotion.

The generated artwork must still begin from an empty target and finish all
characters, terrain, lighting, shadows, and occlusions in one common model
pass. A Pokémon model is domain guidance only; it cannot replace the supplied
source artwork as identity and anatomy authority. Production configuration,
promoted artwork, PDF routing, and release inputs remain unchanged throughout
this comparison.

## Accepted requirements

- In the accepted `identity_lock` workflow, each complete asset is produced in
  one local ComfyUI workflow. The source figures are present at their final
  position before the final context pass, so the generator sees the intended
  composition instead of placing them blindly into a finished scene.
- In the accepted `identity_lock` workflow, reviewed Pokemon pixels are
  immutable. They are never redrawn by diffusion, reconstructed through the
  VAE, moved, or rescaled.
- Card/cover imagery and poster subjects have separate contracts. The poster
  subject records the National-Dex species plus the exact allowlisted PokeAPI
  Official Artwork form ID and URL. Featured selection, cutout filenames and
  manifests, conditioning, planner checks, promotion validation, and
  generation fingerprints preserve that identity. Mega/Primal forms and
  Charizard X/Y cannot silently collapse to a base species or to one another.
- `config/pokeapi_form_species.json` pins all 326 non-default form-to-species
  mappings from PokeAPI commit
  `286d7a071bc50ec4a57e3f3f506a13220ce6f903`. Unknown forms and cross-species
  artwork assignments fail offline before generation.
- Legacy checked-in ExGen and ME output resolves the source Official Artwork
  through the featured `card_id`; new enrichment writes `poster_subject`
  explicitly while retaining the TCG card image in
  `featured_elements.image_url`. Base-only bundles retain their historical
  fingerprint representation and all thirteen accepted promotions remain current.
- The runner compares every fully opaque source pixel immediately after
  generation. Base1 passes with 52,584 exact pixels; SV03.5 and Pokédex
  Generation I each pass with 62,719; Pokédex Generation II passes with
  39,572; Pokédex Generation III passes with 41,641; Pokédex Generation IV
  passes with 43,050; Pokédex Generation V passes with 52,186; Pokédex
  Generation VI passes with 48,362; Pokédex Generation VII passes with
  39,935; Pokédex Generation VIII passes with 34,011; Pokédex Generation IX
  passes with 47,676; ExGen3 normal passes with 32,151; and ExGen3 Mega passes
  with 40,461. All record zero changed pixels in promoted provenance.
- Generation starts from freshly prepared source, mask, composition, and
  engine-specific identity references. It does not consume the legacy poster,
  background, or layout-reference result.
- The production prompt is generated from each manifest's creative scene brief,
  scope metadata, text-cell locations, and one central identity contract. No
  tracked scope-specific identity-lock prompt can drift from the implementation.
- No visible landing pads, safe-area boxes, paths, radial walkways, artificial
  clearings, poster frames, text, or logos are part of the generated artwork.
- The protected lower band is one continuous, low-detail ground plane.
  It has no per-character clearing or landing pad and prevents scenery from
  tracing or extending a silhouette. Freely generated foreground occlusion is
  intentionally disabled in this exact-identity mode.
- All accepted scopes retain the reviewed character count, anatomy, colors,
  proportions, pose, scale, placement, and source pixels. Mewtwo keeps its
  narrow face, central chest ridges, three digits on each hand, complete limbs,
  and tail; Bulbasaur, Charmander, and Squirtle retain their complete source
  silhouettes.
- The physical layout uses 63.5 x 88.9 mm cards and 5 mm binder gaps. Each
  featured Pokemon remains wholly inside one bottom-row card, with visible
  landscape padding around its silhouette.
- Preparation validates the visible alpha bounds of both exact source
  placements and model-compensated conditioning placements against the
  assigned card and the real latent canvas. Cumulative cell endpoints close
  exactly at every canvas edge, and the independent real-canvas guard remains
  fail-closed.
- Identity-lock placement is derived from the shared physical layout. Optional
  model-specific composition compensation remains declarative in each scope
  manifest for the probabilistic edit engines.
- Overscan scales with output dimensions. The protected band defaults to 70
  percent but moves up automatically when a taller silhouette needs it.
- Any individual TCG set with complete generated scope metadata can be
  initialized through `init_poster_scope.py`; layout-driven cast count, stable
  seed, localized logos, model contract, and fallback candidates are generated
  without adding Pokemon or set names to Python.
- Every current individual TCG set has explicit creative scene direction in one
  versioned catalog. Exact catalog-to-generated-scope coverage is enforced by
  tests, while the immutable-subject contract remains central.
- Missing individual-set manifests can be initialized in one explicit
  post-fetch batch without overwriting reviewed manifests.
- The production ComfyUI CLI takes engine, model, seed, steps, generation size,
  output dpi, and upscaler defaults from each scope manifest, so a newly
  initialized scope can produce promotion-compatible provenance without
  repeating configuration flags manually.
- The title logo occupies the top-center card. The centered middle-card panel
  contains localized set name, card count, and release date and has a bounded
  maximum width and height.
- `Binder Pokedex` is rendered at the lower-right edge of the final poster.
- Deterministic overlays support all nine PDF languages. CJK output requires a
  matching system font and fails explicitly rather than silently substituting
  an incapable bitmap font.
- Aggregate overlays show the localized section title, a localized dynamic
  card count, and the localized section description. These values are
  deterministic overlay inputs and do not alter the generated scene.
- Posters are sliced with the same geometry used by preparation and PDF
  rendering. Legacy bundles follow the first section cover; aggregate bundles
  follow the exact configured section cover.
- Preparation, finalization, slicing, promotion, and validation use the same
  cumulative physical endpoint rasterization. Per-cell dimensions are
  authoritative when latent alignment or an odd dpi distributes a one-pixel
  remainder; no crop can extend beyond or stop short of the real canvas.
- The artwork pipeline models 3x3, 4x3, and 4x4 grids. The PDF renderer checks
  for a matching page grid and carries A3 landscape/portrait extension hints
  for the wide layouts instead of assuming nine cells universally.
- The regular scope PDF command includes manifest-enabled posters automatically;
  `--skip-poster` bypasses poster discovery and asset loading for an isolated
  `_NO_POSTER.pdf` build.
- Pull requests use the same read-only release-candidate build as tagged
  releases. The build validates every enabled promoted poster before producing
  all PDFs, language archives, and the release manifest; only the separate
  `v*`-tag publish job has write access.
- Promoted artwork is 2368 x 3268 px, every card crop is 750 x 1050 px, and the
  PDF embeds every poster card at 300 ppi.
- Promotion is transactional and stores hashes for model, encoder, VAE,
  upscaler, prompts, cutouts, references, workflows, and all promoted outputs.
- New runs additionally store semantic generation and overlay fingerprints.
  Generation fingerprints include the scene, safe-cell positions, model
  contract, effective prompt, source IDs, and decoded cutout pixels. Overlay
  fingerprints independently cover localized text, logo pixels, and panel
  configuration, so those cheap changes never imply a new ComfyUI render.
- Backfilled provenance preserves the graph contract recorded by the original
  reference topology. It marks the migration origin explicitly and never
  claims that a v1/v2 artwork was rendered by the current v3 geometry graph.
- The read-only post-fetch planner resolves individual and aggregate targets,
  checks current inputs and promoted outputs, and reports stable states,
  reasons, actions, and optional commands without mutating files or starting
  ComfyUI.
- Diagnostic and poster-skipped PDF modes use distinct filenames, and renderer
  failures propagate to a failing scope command.
- Local ComfyUI sampling runs on Apple Metal/MPS. CPU is used only for the
  narrowly scoped dequantization and offload operations required by unsupported
  MPS tensor conversions.
- FLUX.2, Anima, FLUX.1 Canny, and Qwen Edit remain separate selectable
  engines. The promoted implementation is scope-driven and has been exercised
  with two individual sets plus eleven aggregate section bundles.
- All four engine adapters now resolve their complete model and sampling
  contract from a matching manifest, with explicit CLI values acting only as
  overrides. Anima records its model, LoRA, encoder, VAE, steps, CFG, reference
  strength, and control method exactly; its workflow files are unique by mode,
  size, and seed. Exact-source modes record an opaque-source-pixel audit against
  the raw ComfyUI output and require zero changed pixels for promotion.
  `joint_scene` intentionally redraws the subjects and has no equality audit;
  promotion instead requires complete fingerprint provenance and an explicit
  review bound to both raw and deterministic Lanczos print pixels.

## Partially satisfied requirements

| Requirement | Current boundary | Acceptance criterion |
| --- | --- | --- |
| Natural grounding and occlusion | Accepted `identity_lock` keeps exact pixels but can read as composited. v5 `00018` gives all three subjects coherent grounding and preferred card fill but avoids crossings; `00019` ignores explicit crossings; compact `00020` duplicates Litten | Treat `00018` as visually preferred and `identity_lock` as the promoted fallback. Keep promotion explicit and do not add more prompt complexity |
| Engine extensibility | FLUX.2, Anima, FLUX.1 Canny, and Qwen Edit are selectable through one manifest-driven runner and share the promotion gate | Keep architecture-specific workflow construction isolated when adding another engine |
| Alternative models | FLUX.1 Canny changed Mewtwo's face, chest, colors, and hand. Old Qwen duplicated a giant fourth Mewtwo; corrected spatial inputs instead collapse to one oversized Litten on the neutral field | Retain the adapters as diagnostic code, but do not render or promote another candidate without a materially new control mechanism |
| Anima candidates | The 0.25-MP empty-target preflight passes count and card fit but uses a post-decode identity-core composite and fails grounding, terrain interaction, occlusion, and the exact-source audit | Keep the adapter as selectable diagnostic code; do not spend a 1-MP render on the same topology |
| New set art direction | Every current individual set has an explicit catalog brief copied into its manifest | Review or refine the brief before spending the production render; catalog coverage does not replace visual art direction |
| Wide PDF layouts | 4x3 and 4x4 artwork, placement, prompting, upscale, promotion, validation, slicing, and matching-grid rendering are modeled | Add physical A3 page styles/templates and rendered-PDF QA |
| Aggregate scopes | The generic index, isolated leaf manifests, section filtering, PDF routing, cleanup, nested validation, nine Pokédex generation configs, and form-aware poster-subject contract are implemented; Pokédex Generations I through IX and both ExGen3 sections are promoted and enabled | Prepare reviewed section scenes and casts for the remaining aggregate variants |

## Remaining production requirements

- Keep the mandatory visual review for character identity, anatomy, natural
  grounding, and generated silhouette boundaries.
- Treat any changed digit count, head/face, chest geometry, limb, tail, pose,
  color, or defining contour as a hard rejection even if the background improves.
- Reject generated scenery beside a subject when it reads as an additional body
  part.
- Keep exact opaque-pixel validation mandatory for exact-source modes, but do
  not apply that equality claim to `joint_scene`, which redraws the complete
  image. Its raw and print identity checks remain explicit human review bound
  to deterministic provenance.
- Keep v5 changes isolated. Placement-only `00018` is complete, full-length
  depth-stress `00019` fails, and compact `00020` fails count. Their prompt
  changes are reverted. Do not resume prompt tuning; any successor must use a
  materially different control mechanism and inherits no approval.
- Review memory and output separately before promoting `joint_scene` with the
  four subjects required by `wide_4x3` or `wide_4x4`.
- Keep Anima and FLUX.1 Canny experimental. The current Anima topology and both
  Qwen binding topologies are closed; do not render another candidate without a
  materially different common-pass or binding mechanism.
- Apply the demonstrated ExGen3 section workflow to remaining aggregate
  variants only after their section briefs and curated casts are reviewed.
- Implement matching A3/custom PDF page renderers before enabling 4x3 or 4x4
  poster manifests for PDF output.
- Keep any future mutating `ensure-poster` command separate from the completed
  read-only planner and preserve the human promotion gate.

## Cleanup boundary

The production flow contains one text-free full-scene artwork contract and no
tracked layout-reference image, visible placement guide, generated-text stage,
or background-import command. Shared IO, placement, and typography helpers live
in neutral modules used by the production flow.

Ignored ComfyUI outputs, generated prompt snapshots, workflows, references, PDF
builds, and temporary renders are local scratch data. They may be deleted after
reviewed candidates and their provenance have been promoted.

## Verification record

Completed on 2026-07-27:

- The complete suite passes with 515 tests; one unrelated EX-logo feature test
  remains explicitly skipped.
- PA-018 regressions cover manifest-to-workflow resolution for every engine,
  exact Anima model/LoRA/encoder/VAE/sampling/control metadata, unique Anima
  workflow files, soft audit recording for rejected experimental output, hard
  failure for production identity-lock, engine-independent promotion
  rejection, and a complete passing Qwen run-metadata-to-promotion-to-validator
  contract test.
- Joint-scene v5 regressions cover one empty target, one sampler, and one decode;
  ordered spatial-cast then per-subject identity references; unscaled opaque
  source pixels; normalized silhouette rectangles; absence of
  landscape/full-scene/inpaint conditioning and any post-decode composite;
  dynamic prompts, deterministic Lanczos output, complete generation
  fingerprints, and the explicit raw/print visual gate.
- Python compilation and `git diff --check` pass.
- All thirteen promoted bundles pass `validate_promoted_poster.py`, including
  semantic input equality, historically accurate and explicitly supported
  graph-contract status, provenance hashes, 2368 x 3268 artwork, nine
  750 x 1050 card crops, 300-dpi metadata, and exact opaque-source-pixel
  records.
- PA-020 endpoint regressions cover 3×3, 4×3, and 4×4 layouts at latent
  canvases and 72/150/299/300/301/600 dpi. The standard 848 × 1168 bounds are
  exactly x `(0,269)/(290,558)/(579,848)` and
  y `(0,375)/(396,772)/(793,1168)`; synthetic 12- and 16-cell slices contain
  no edge padding.
- Re-finalizing all thirteen enabled posters and slicing their 117 cards
  produced pixel-identical RGB output. The 300-dpi production geometry remains
  2368 × 3268 with nine 750 × 1050 cells, so no promoted asset or provenance
  file required rewriting.
- The German Pokédex Generation IX poster page was rendered through Poppler
  after the change. It remains A4, visually unclipped, and contains exactly
  nine 750 × 1050 images reported at 300 × 300 ppi.
- Form-identity regressions cover real ExGen3 Mega Latias/Diancie/Lucario,
  distinct ExGen2 Charizard X/Y and Mewtwo X/Y cards plus its reviewed
  Mewtwo X/Rayquaza/Latios poster cast, ME03 Mega Zygarde, and the unaffected
  MEP base-form cast. The TCG enrichment also corrects the inconsistent
  upstream ME01 Mega Absol ID before artwork resolution. Synthetic checks
  reject missing or conflicting X/Y evidence, species/artwork collisions, and
  untrusted URLs; download only the exact form artwork; detect same-species
  form drift in both the planner and runner/promotion fingerprint boundary;
  and prove that base fingerprints stay unchanged while form IDs affect
  generation fingerprints.
- The configured model, encoder, VAE, and Real-ESRGAN hashes match the actual
  files in the local ComfyUI installation.
- All ten Base1/SV03.5 overlays for `de`, `en`, `fr`, `es`, and `it` render at
  2368 x 3268 px with 300-dpi metadata.
- The complete German Base1 and SV03.5 PDFs were generated and visually
  inspected. Their poster page embeds exactly nine 750 x 1050 images at
  300 x 300 ppi.
- A German Base1 test PDF was generated through the regular command both with
  and without `--skip-poster`. The default build has three pages and nine
  750 x 1050 poster images at 300 x 300 ppi on page two; the isolated
  `_NO_POSTER.pdf` build has two pages and proceeds directly to the card grid.
- The scene catalog has exact coverage for all 26 current individual TCG sets,
  including explicit Jungle (`Base2`) and Fossil (`Base3`) briefs. The batch
  initializer regression creates every missing standard-3x3 manifest while
  preserving the existing reviewed Base1 manifest.
- The thirteen enabled source and conditioning compositions were checked
  read-only at their real 848 x 1168 latent canvas. Their cumulative cells now
  close on x=848 and y=1168 exactly, while a separate regression proves that
  any explicitly out-of-canvas visible pixels are still rejected before
  `alpha_composite` can clip them.
- The Pokédex resolver loads nine isolated generation bundles with unique seeds
  and section-local source data. Generations I through IX are enabled. Its
  checked-in output contains localized section titles, card counts, and range
  descriptions for all nine PDF languages.
- A complete German Pokédex build with Generations I through IX enabled
  produces 135 A4 pages. Generation IX appears as cover page 120 followed by
  its poster on page 121 and cards from page 122. The `--skip-poster`
  countercheck produces 126 pages; Generation IX then appears as cover page
  112 followed directly by cards from page 113 without an empty gap. Poster
  page 121 embeds exactly nine 750 x 1050 images at 300 x 300 ppi. Nested
  preparation resolves the full asset key instead of falling back to a
  leaf-directory basename.
- ExGen3 uses two isolated and enabled section bundles. The normal section
  contains the curated Koraidon, Pikachu, and Miraidon cast; the Mega section
  contains the exact Mega Latias, Mega Diancie, and Mega Lucario forms.
  Both use section-specific creative briefs and deterministic localized
  overlays.
- The complete English ExGen3 PDF has 29 A4 pages. The normal poster follows
  the normal section cover, and the Mega poster follows the Mega section
  cover; each poster page contains exactly nine 750 x 1050 card images at the
  existing physical card positions.
- Release validation carries the resolved routing bundle through provenance
  checks and rejects any PDF artwork path other than the promoted, hashed
  output.
- All thirteen accepted artworks and all thirty-nine 750 x 1050 bottom character
  cards were visually compared with the reviewed cutouts after model
  upscaling. Character anatomy, card padding, the continuous lower ground, and
  absence of adjacent body-like shapes pass.
- The accepted Generation IV candidate contains Turtwig, Chimchar, and Piplup,
  uses seed `260734875` and graph contract v2, and preserves all 43,050 fully
  opaque source pixels with zero changes.
- The accepted Generation V candidate contains Snivy, Tepig, and Oshawott,
  uses seed `260735038` and graph contract v2, and preserves all 52,186 fully
  opaque source pixels with zero changes.
- The accepted Generation VI candidate contains Chespin, Fennekin, and
  Froakie, uses seed `260758583` and graph contract v2, and preserves all
  48,362 fully opaque source pixels with zero changes. The Kalos flower-country
  scene, complete poster, and three lower card cuts pass visual review.
- The enabled Generation VII baseline contains Rowlet, Litten, and Popplio,
  uses seed `260726054` and graph contract v2, and preserves all 39,935 fully
  opaque source pixels with zero changes. Later visual review identified that
  its completely protected lower band makes the three figures read as layered
  over the Alola scene. This is a grounding/integration limitation rather than
  an identity regression and is tracked under PA-017.
- The unpromoted Generation VII joint-scene experiments use the same seed and
  sources. Candidates through `00016` remain rejected. The identity-only v3
  graph resolves the earlier landscape-depth conflict, but `00014` and `00015`
  cross the upper boundary of all three bottom cards. The v4 common cast
  reference fixes card containment and coherent depth in `00016`, but invents
  a pale Litten marking. The v5 Spatial+Identity candidate `00017` demonstrates
  the accepted print-detail identity tolerance but is undersized. `00018`
  reuses the canonical Option-1 placement and passes preferred card fit,
  containment, and grounding review. `00019` fails to create requested
  intersections; compact `00020` duplicates Litten and also has no crossing.
  Their prompt changes are reverted. `00018` is the visually preferred
  experimental comparison and remains unpromoted; `identity_lock` remains the
  accepted fallback. None changes the manifest or PDF output; the full
  chronology is kept in the experiment log.
- The accepted Generation VIII candidate contains Grookey, Scorbunny, and
  Sobble, uses seed `260715405` and graph contract v2, and preserves all 34,011
  fully opaque source pixels with zero changes. The Galar upland lake, moor,
  village, and stone-wall scene, complete poster, and three lower card cuts
  pass visual review; Scorbunny's tall pose retains clear padding above its
  ears and below its feet.
- The accepted Generation IX candidate contains Sprigatito, Fuecoco, and
  Quaxly, uses seed `260778637` and graph contract v2, and preserves all 47,676
  fully opaque source pixels with zero changes. The Paldea valley, olive
  woodland, ochre hills, coast, and distant academy scene, complete poster,
  and three lower card cuts pass visual review; Fuecoco's high flame retains
  clear padding inside the middle card.
- The accepted ExGen3 normal candidate uses seed `260711318`, preserves all
  32,151 fully opaque source pixels, and keeps each subject inside its bottom
  card with reviewed padding.
- The accepted ExGen3 Mega candidate uses seed `260751034`, preserves all
  40,461 fully opaque source pixels, and keeps the exact form identity of Mega
  Latias, Mega Diancie, and Mega Lucario.
- Generation V through IX overlay localization deterministically renders
  their respective 156-, 72-, 88-, 96-, and 120-card counts and Pokédex ranges
  in all nine supported PDF languages. All nine Generation IX previews retain
  2368 x 3268 px and 300-dpi metadata; Traditional Chinese passes visual
  typography review.
- The Generation III rerender uses the separate binary VAE sampling mask and
  soft final-composite mask. The former full-width transition jump at row 759
  dropped from a mean luminance delta of -7.95 to -2.16; the relocated binary
  edge is hidden below the completed feather and remains visually absent.
- One Generation III retry and the first Generation VI attempt produced
  non-finite MPS results. The runner's blank-output guard rejected both before
  upscaling or promotion; restarting ComfyUI and rerunning the same reviewed
  seed produced each accepted candidate.
- Repeating the complete SV03.5 generation with the same inputs produced
  bit-identical raw and model-upscaled PNG hashes.
- The rejected FLUX.1 Canny and Qwen candidates remain local diagnostics only;
  neither was promoted.

For every future candidate, the same whole-poster, per-card, localized-overlay,
and rendered-PDF review remains the promotion gate. Identity-lock topology is
covered by exact-pixel tests. Joint-scene promotion additionally binds explicit
human review to the exact raw and deterministic text-free print artifacts,
their source identities, and their generation fingerprint; the code does not
claim false confidence from generative similarity.
