# Poster Artwork Requirements and Roadmap

This document is the stable product and engineering contract for scope posters.
It separates accepted behavior from prepared extension points and open work.
Detailed evidence for promoted candidates is recorded in
[POSTER_ARTWORK_STATUS.md](POSTER_ARTWORK_STATUS.md). Rejected local renders
and isolated experiment changes are recorded in
[POSTER_ARTWORK_EXPERIMENT_LOG.md](POSTER_ARTWORK_EXPERIMENT_LOG.md).

Last reviewed: 2026-07-28

## Decisions

| Decision | Current direction |
| --- | --- |
| Default binder format | `standard_3x3` on A4 portrait at physical card size |
| Wide layouts | Keep `wide_4x3` and `wide_4x4` as supported artwork layouts and future matching PDF formats; never squeeze them onto A4 |
| Generation timing | Explicit optional post-fetch step, before PDF generation |
| PDF behavior | Consume only promoted local artwork; never launch ComfyUI implicitly |
| Prompt ownership | Set-specific creative briefs in one catalog plus one centrally generated technical/identity contract |
| Character identity | The accepted `identity_lock` path keeps reviewed source pixels immutable. A `joint_scene` candidate may redraw pixels only in one unified scene pass; identity, anatomy, markings, pose, scale, and card-safe placement remain strict visual invariants |
| Form identity | Card/cover imagery and poster subjects are separate; Mega, Primal, X/Y, and other forms keep their exact allowlisted Official Artwork identity |
| Promotion | Human visual review plus deterministic validation remains mandatory |
| Missing poster | Normal PDF remains possible; enabled-but-missing promoted artwork is an error; `--skip-poster` is an explicit bypass |
| CI boundary | Pull requests build and validate the complete release candidate with read-only permissions; only `v*` tags may publish it |

## Successor acceptance gate

The accepted `identity_lock` posters remain valid production baselines. A new
integrated-artwork successor is promoted only when one candidate satisfies all
hard gates below at the same time:

| Gate | Priority | Acceptance |
| --- | --- | --- |
| One model-owned final scene | Hard | The final model pass starts from an empty target and generates landscape and characters together; no character pixels are composited, restored, moved, or replaced after its decode |
| Character identity | Hard | Cast count, form, pose, stature, silhouette, anatomy, face, colors, and markings match the supplied references without invented or missing traits |
| Physical card containment | Hard | Every complete character and appendage remains inside its assigned bottom-row card in the actual sliced 3×3 print raster |
| Coherent scene depth | Hard | Shadows and ground contact agree; every connected landscape element keeps a physically plausible front/behind relationship instead of ending at or weaving around a character silhouette |
| Deterministic print output | Hard | Text-free output reaches the exact configured physical 300-dpi dimensions through deterministic resampling; typography, logo, slicing, and PDF use remain deterministic |
| Set-specific scene quality | Preferred | The result is attractive, recognizable for the scope, and preserves the requested text-safe regions |
| Visible foreground overlap | Preferred | Natural foreground overlap may occur, but is not required. A coherent open patch of terrain is preferable to a forced or contradictory overlap |

No hard gate is weakened implicitly. If a candidate meets some gates by
violating another, it is rejected and the tradeoff is logged.

## Experiment and decision rule

1. A checkpoint commit records each architecture change before the next
   material experiment.
2. Each new render changes one placement, identity, or scene-control mechanism
   at a time and is reviewed against the same hard gates.
3. An architecture gets at most three materially distinct single-variable
   attempts to fix one repeatedly failing hard gate.
4. After the third failed attempt, generation stops. The unresolved conflict,
   evidence, and available product choices are presented for an explicit
   decision: retain the production baseline, relax one named gate, change
   model/architecture, or accept additional implementation complexity.
5. A later retry starts only when new evidence or a deliberately selected
   mechanism makes it materially different from the logged failures.

This prevents silent switching between `identity_lock`, landscape-referenced
joint generation, and true one-shot generation.

## Architecture evidence

| Architecture | No post-composite | Identity | Card containment | Coherent occlusion | Current role |
| --- | --- | --- | --- | --- | --- |
| Two-pass `identity_lock` | No | Exact source pixels | Reliable | Weak: protected lower band can read as a layer | Accepted production baseline |
| Subject-free landscape reference plus joint final pass | Yes | Usually strong | Tunable but inconsistent | Failed: retained plants can weave behind/in front of subjects | Rejected Generation VII experiment |
| FLUX.2 identity-only/cast-only true one-shot | Yes | v3 strong; v4 cast layout invents a Litten marking | v3 fails; v4 `00016` passes with padding | Strong: landscape is invented around the cast | Historical attempts closed |
| FLUX.2 Spatial+Identity v5 true one-shot | Yes | Unscaled identity references are explicit anatomy authority, but `00017` still simplifies Litten's paw and Popplio's face details | `00017` passes all three card crops | Strong in `00017` | Implemented and rejected under the hard identity gate |
| Regional SDXL identity control | Yes | Fails all three mask scopes; Litten becomes unrecognizable | Subjects remain too small and ungrounded | Scene collapses into blurred color regions | Closed after three rejected candidates |
| DreamO v1.1 multi-reference control | Yes, by the isolated graph contract | Three separate VAE-based object references | Must pass the unchanged physical-card gate | Must be resolved in the common final pass | Selected for the next MPS preflight; not a production engine |

## Requirement register

| ID | Requirement | Status | Acceptance |
| --- | --- | --- | --- |
| `PA-001` | A4 production defaults to a 3×3 physical card grid | Done | All regular poster manifests and CLI initialization default to `standard_3x3` |
| `PA-002` | 4×3 and 4×4 remain first-class artwork layouts | Prepared | Layout geometry, subject count, prompts, upscale, promotion, validation, slicing, PDF hints, and matching-grid rendering are layout-driven |
| `PA-003` | Wide layouts preserve physical card dimensions | Prepared | 4×3 targets A3 landscape and 4×4 targets A3 portrait; no A4 scaling fallback |
| `PA-004` | Every individual TCG set has explicit scene direction | Done | `config/poster_scenes.yaml` has exact one-to-one coverage with generated `tcg_set` scopes, enforced by tests |
| `PA-005` | Full prompts cannot drift per set | Done | Creative scene is scope-specific; identity, safe-area, continuous-ground, no-path, no-text, and no-landing-pad rules are generated centrally |
| `PA-006` | Poster preparation is an optional post-fetch phase | Done | One-scope and missing-all-scope initialization commands exist; batch mode preserves reviewed manifests |
| `PA-007` | Production generation follows the scope contract | Done | ComfyUI runner reads seed, engine, model, steps, resolution, dpi, and upscaler defaults from `poster.yaml` |
| `PA-008` | Figures remain authentic | Done | The accepted `identity_lock` path restores exact source cutouts and verifies every opaque source pixel; any fully generated `joint_scene` successor requires a complete generation fingerprint plus explicit bound review of both raw and print-size artwork |
| `PA-009` | Artwork matches later typography and card cuts | Done | Prompt safe areas and figure placement derive from the same physical layout used by finalization and slicing; visible source and conditioning pixels are also checked against the real generation canvas before composition |
| `PA-010` | Only promoted artwork enters a normal PDF | Done | `pdf.enabled` plus a local promoted file gates automatic inclusion |
| `PA-011` | Poster use is optional per build | Done | `--skip-poster` bypasses discovery/loading and writes a separate `_NO_POSTER.pdf` |
| `PA-012` | Every promoted poster is reproducible and auditable | Done | Promotion records model, prompt, source, workflow, validation, and output hashes |
| `PA-013` | Multiple posters can be assigned to aggregate sections | Done | A routing index binds isolated poster bundles to stable section IDs; PDFs insert every enabled bundle after its matching cover, while legacy single posters retain their first-cover behavior |
| `PA-014` | 4×3/4×4 PDFs use matching page renderers | Open | Add A3/custom page styles, templates, cutting guides, and rendered-PDF QA |
| `PA-015` | Aggregate variant scopes receive section-specific scene briefs | Ongoing | ExGen3 `normal` and `mega` are accepted section-local bundles; apply the same explicit scene, cast, and routing contract to `primal` and future sections instead of treating an aggregate as one unambiguous TCG set |
| `PA-015A` | Variant poster subjects retain their exact form | Done | Featured selection, cutout files/manifests, planner checks, promotion validation, conditioning, and generation fingerprints use a validated Official Artwork subject identity; distinct forms of one species remain distinct and special forms never fall back silently to base artwork |
| `PA-016` | Post-fetch orchestration detects stale poster inputs | Done | A read-only planner compares routing, scope data, scene catalog, cutout selection/pixels, logos, dynamic model contracts, effective prompts, semantic generation/overlay fingerprints, and promoted outputs; it separates expensive regeneration from cheap overlay or routing work |
| `PA-017` | Natural grounding may be generated jointly without losing identity or card safety | Identity-control successor evaluation in progress | Production remains on `identity_lock`. Generic regional SDXL control is closed after three hard-gate failures, and its Pokémon-LoRA A/B is skipped because the base graph does not bind or preserve the subjects. The available MS-Diffusion ComfyUI port is rejected at technical preflight because its hidden Diffusers sampler, unconditional xFormers/CUDA paths, and final-image node would require a substantial MPS/audit refactor. The next isolated candidate is DreamO v1.1 with three separate object references, one empty target, one common sampler, one decode, and no post-decode character compositing or restoration |
| `PA-018` | Alternative engines and generation modes remain selectable but gated | Done | FLUX.2, Anima, FLUX.1 Canny, and Qwen resolve model/sampling options from the matching manifest and record the exact effective contract. Exact-source modes require their passed raw-pixel audit; fully generated `joint_scene` candidates instead require a complete fingerprint and explicit identity/scene review bound to raw and deterministic print pixels |
| `PA-019` | Pull requests prove that a complete release can be built without publishing it | Done | PRs reuse the read-only release-candidate workflow, validate all enabled posters, build every PDF and language archive, verify the manifest, and stop after a temporary Actions artifact |
| `PA-020` | Rasterized card geometry remains inside the real generation canvas at every supported resolution | Done | Card cells come from cumulative physical endpoints rasterized against both real canvas axes; preparation, finalization, slicing, promotion, and validation share those exact bounds, and new runs record raster geometry contract v2 |

## Current production boundary

- `Base1`, `SV03.5`, Pokédex Generations I through IX, and both ExGen3 sections
  have accepted, promoted 3×3 artwork and enabled PDF integration.
- Every current individual TCG set can now be initialized with a set-specific
  scene brief and the same production contract.
- The Pokédex has nine isolated, section-specific bundles with distinct seeds,
  regional scene briefs, deterministic nine-language section overlays, and
  exactly the three starter `featured_elements` from each generation.
- Aggregate overlays deterministically show the localized section title,
  dynamic card count, and localized section description.
- The Generation I through IX Pokédex bindings are enabled after visual
  whole-poster, card-cut, and rendered-PDF review. The German build has 135
  pages with all nine posters versus 126 with `--skip-poster`; Generation IX
  appears as cover page 120, poster page 121, and cards from page 122. In the
  skip build it appears as cover page 112 followed directly by cards from page
  113. The rollout and its final release-candidate gate are complete and
  recorded in [#2](https://github.com/DerFlash/BinderPokedex/issues/2).
- ExGen3 routes two independent posters after their matching section covers.
  The normal bundle uses Koraidon, Pikachu, and Miraidon in its
  Paldea-inspired scene. The Mega bundle uses the exact Mega Latias, Mega
  Diancie, and Mega Lucario forms in its highland scene. Both bindings are
  enabled and validated for normal PDF generation.
- The default workflow deliberately stops before automatic promotion. Semantic
  scene quality, character boundary quality, and natural grounding still need
  human review.
- Poster casts model National-Dex identity and exact visual form separately.
  `featured_elements.image_url` remains the cover/card image, while a separate
  `poster_subject` binds species ID, exact PokeAPI Official Artwork ID,
  canonical URL, and stable subject key. ExGen/ME records can resolve this
  identity through the featured `card_id`, and current enrichment persists the
  explicit contract. The pinned PokeAPI registry verifies every form-to-species
  relationship and explicitly maps named normal-card forms such as Alolan
  Exeggutor, Black Kyurem, Bloodmoon Ursaluna, and the four Ogerpon masks.
  Base-only bundles retain their compatible integer fingerprint
  representation.
- The read-only post-fetch planner reports stable states, reasons, actions, and
  optional commands without downloading assets, mutating routing, starting
  ComfyUI, or promoting a candidate. Generation and overlay fingerprints keep
  text, logo, translation, panel, and `pdf.enabled` changes out of the
  expensive regeneration path. Backfilled records preserve their audited
  historical graph contract; accepted v1/v2 artwork remains usable while an
  optional current-v3 upgrade is reported explicitly.
- Aggregate sections beyond the accepted ExGen3 section implementation and
  wide PDF pages remain explicit roadmap work rather than hidden assumptions.
- Every generation engine records the raw ComfyUI output, dimensions, and
  hashes. Exact-source modes additionally record an audit reference and use the
  engine-neutral opaque-pixel audit as a promotion gate. Production FLUX
  `identity_lock` still aborts immediately on a changed pixel, and existing
  promotions remain compatible through their legacy
  `validation.identity_lock` record. `joint_scene` intentionally redraws every
  final pixel and therefore has no source-pixel equality claim. Its promotion
  gate instead binds an explicit human review to the complete generation
  fingerprint, source identities, raw artwork, and deterministic print-size
  text-free artwork.
- The accepted identity-lock topology deliberately protects the complete lower
  subject band. The final context pass sees the figures, but has little freedom
  to improve ground contact around them; Generation VII demonstrates that this
  can read as a composited layer. The experimental `joint_scene` topology
  addresses that tradeoff with one FLUX.2 pass from an
  `EmptyFlux2LatentImage`; no landscape image, generated scene, or
  `inpaint_reference.png` enters conditioning. Normalized visible-silhouette
  rectangles derived from the physical layout communicate each target
  position, scale, baseline, padding, and card-safe region. The selected v5
  topology gives one 0.5-MP cast spatial authority and one unscaled 512 px
  source reference per subject identity and anatomy authority. All references
  enter the same conditioning chain before the single sampler. The one pass
  invents landscape and subjects together and may resolve z-order, ground
  contact, shadow, and depth while subject identity and complete bottom-card
  containment remain hard review gates.
- Joint-scene print output is a deterministic Lanczos resize to the exact
  configured 300-dpi `build_print_layout` dimensions. A learned upscaler is not
  part of this mode.
- The v5 graph derives the reference count from the layout and does not
  categorically exclude four subjects. `standard_3x3` remains the default;
  four-subject `wide_4x3` and `wide_4x4` generation still needs a separate
  memory and visual review before promotion.
- The Generation VII `joint_scene` candidates are local evidence only.
  Candidates through `00017` are rejected and unpromoted; no poster manifest,
  promoted artwork, aggregate routing, or PDF binding has switched away from
  the accepted `identity_lock` baseline. Every later candidate starts a new
  review record rather than inheriting approval.
- All thirteen enabled 1-MP source and conditioning compositions fit within
  their real 848 × 1168 generation canvases. Cumulative physical endpoints
  close exactly at every real canvas edge, even where latent alignment makes
  the card widths or heights differ by one pixel. New generation fingerprints
  record raster geometry v2; new FLUX identity-lock and identity-only one-shot
  `joint_scene` Spatial+Identity fingerprints use graph contract v5, while the
  reviewed v1/v2 identity-lock promotions remain valid as accepted legacy
  artifacts.
- Pull requests and tagged releases use the same release-candidate build.
  Publication is a separate write-enabled job available only to `v*` tags.

## Change rule

When a requirement changes:

1. update its row and acceptance statement here;
2. update the implementation guide when operator behavior changes;
3. add or adapt an automated test for deterministic behavior;
4. update the GitHub tracking issue with the affected requirement IDs;
5. record candidate-specific evidence in `POSTER_ARTWORK_STATUS.md`.
