# Poster Artwork Requirements and Roadmap

This is the stable product and engineering contract for scope posters. Current
accepted assets are listed in
[Poster Status](POSTER_ARTWORK_STATUS.md), operator commands in
[Poster Workflow](POSTER_WORKFLOW.md), and rejected candidate evidence in
[Poster Experiment Log](POSTER_ARTWORK_EXPERIMENT_LOG.md).

Last reviewed: 2026-08-03

## Decisions

| Decision | Current direction |
| --- | --- |
| Default binder format | `standard_3x3` on A4 portrait at physical card size |
| Wide layouts | Keep `wide_4x3` and `wide_4x4` as artwork extension points; never squeeze them onto A4 |
| Generation timing | Explicit optional post-fetch step, before PDF generation |
| PDF behavior | Consume only promoted local artwork; never launch ComfyUI implicitly |
| Cover fallback | Keep the existing section cover whenever no promoted poster is enabled; currently it also remains before enabled posters until a separately reviewed replacement migration |
| Poster presentation | Render enabled posters as cuttable physical cards by default; optionally render the same localized poster as one continuous physical-grid-sized image centered on its PDF page |
| Generator | FLUX.2 `joint_scene` remains the mode for new candidates with `individual_spatial_joint` v7 as the default; spatial-v5 remains reproducible for its accepted scopes and regional-v6 only for Generation III |
| Fallback | FLUX.2 `identity_lock` remains explicitly selectable when a one-shot cannot pass identity or placement review |
| Prompt ownership | Set-specific creative briefs in one catalog plus one centrally generated identity, placement, depth, and safe-area contract |
| Character identity | Supplied Official Artwork is the authority for form, stature, anatomy, silhouette, pose, color, and markings |
| Form identity | Card/cover imagery and poster subjects are separate; Mega, Primal, X/Y, regional, and other forms keep their exact allowlisted Official Artwork identity |
| Promotion | Human visual review plus deterministic validation is mandatory |
| Missing poster | A scope without an enabled promotion uses its normal cover path; enabled-but-missing promoted artwork is an error; `--skip-poster` explicitly forces the cover-based path |
| CI boundary | Pull requests build and validate a complete release candidate without publishing; only `v*` tags may publish |
| Rejected experiments | Anima, FLUX.1 Canny, Qwen, SDXL, DreamO, direct edit, and direct inpaint remain evidence in the log and Git history, not live production options |

## One-shot acceptance gate

A `joint_scene` candidate is promoted only when one result satisfies all hard
gates at the same time:

| Gate | Priority | Acceptance |
| --- | --- | --- |
| One model-owned final scene | Hard | The final pass starts from an empty target and generates landscape and characters together; no character pixels are composited, restored, moved, or replaced after decode |
| Character identity | Hard | Cast count, exact form, pose, stature, silhouette, defining anatomy, face, colors, and markings match the supplied references without invented or missing traits |
| Physical card containment | Hard | Every complete character and appendage remains inside its assigned bottom-row card in the actual print raster, with visually appropriate padding |
| Coherent scene depth | Hard | Shadows and ground contact agree. A connected landscape element either stays clear of a character or keeps one physically plausible front/behind relationship for its entire visible intersection; ending at a silhouette or switching depth around it fails |
| Deterministic print output | Hard | Text-free output reaches the exact configured 300-dpi dimensions through deterministic resampling; typography, logo, slicing, and PDF use remain deterministic |
| Set-specific scene quality | Preferred | The result is attractive, recognizable for the scope, and preserves the requested text-safe regions |
| Visible foreground overlap | Preferred | Natural foreground overlap may occur, but is not required. Clean separation and one coherent overlap are equally valid; both are preferable to a forced contradictory overlap |

Minor print-scale simplification of a non-defining line may be accepted only
after direct comparison at final card size. A changed body-part count, facial
structure, defining contour, marking, form, or gross proportion always fails.

`identity_lock` uses a different hard gate: every fully opaque source pixel
must be byte-identical after generation. Its weaker local terrain interaction
is the accepted cost of exact identity preservation.

## Experiment and decision rule

1. Record the accepted baseline and every material experiment through focused
   commits and the experiment log.
2. Change one placement, identity, or scene-control mechanism at a time.
3. Give one architecture at most three materially distinct attempts to fix the
   same repeatedly failing hard gate.
4. After the third failure, stop and choose explicitly: retain the baseline,
   relax one named gate, change the mechanism, or accept more implementation
   complexity.
5. Do not silently turn a failed one-shot back into compositing, or a fallback
   into an alleged one-shot.

## Architecture evidence

| Architecture | Final scene jointly generated | Identity | Card containment | Scene integration | Role |
| --- | --- | --- | --- | --- | --- |
| FLUX.2 Individual Spatial v7 `joint_scene` | Yes | One positioned identity reference per subject passes the accepted print-detail tolerance for Generations IV-IX and `SV03.5` | All seven promotions pass their physical crops with useful padding | Joint landscape generation, coherent grounding, shadows, and either clean separation or consistent overlap pass review | Default; seven scopes promoted |
| FLUX.2 Spatial+Identity v5 `joint_scene` | Yes | Gen I `00001`, Gen II `00001`, Base1 `00001`, ExGen3 Mega `00001`, and ExGen3 Normal `00001` pass the accepted print-detail tolerance | All five promotions pass their physical crops with preferred fill | Coherent grounding and shadows; retained as an accepted reproducible topology | Reproducible legacy; five scopes promoted |
| FLUX.2 Regional Identity v6 `joint_scene` | Yes | The promoted Generation III candidate keeps all three supplied identities within normal one-shot tolerance | All three complete subjects pass their physical bottom-card crops | The reviewed promotion passes, but the six-scope audit exposes independent lower-card scene predictions and fails to generalize | Generation III reproduction only; broader rollout stopped |
| Two-pass `identity_lock` | No | Exact source pixels | Reliable | Protected lower band can read as a layer | Explicit fallback; no active promoted scope |
| Landscape reference plus joint final pass | Final pass only | Usually strong | Inconsistent | Retained plants can switch depth at silhouettes | Rejected |
| Direct FLUX edit/inpaint | No | Inconsistent | Inconsistent | Retains cutout/composite artifacts | Rejected |
| Anima with restored identity core | No | Recognizable only because pixels are restored after decode | Card-safe in preflight | Flat lawn and weak contact | Rejected |
| FLUX.1 Canny / Qwen | Varies | Redesigns, duplicates, or drops subjects | Fails | Does not satisfy the scene contract | Rejected |
| SDXL regional identity / DreamO | Yes in their isolated graphs | Fails reference binding or anatomy | Fails | Insufficient for the required cast | Rejected |

## Requirement register

| ID | Requirement | Status | Acceptance |
| --- | --- | --- | --- |
| `PA-001` | A4 production defaults to a 3×3 physical card grid | Done | Initializer and active A4 manifests use `standard_3x3` |
| `PA-002` | 4×3 and 4×4 remain first-class artwork layouts | Prepared | Geometry, placement, prompting, promotion, validation, and slicing are layout-driven |
| `PA-003` | Wide layouts preserve physical card dimensions | Prepared | Future 4×3 targets A3 landscape and 4×4 targets A3 portrait; no A4 scaling fallback |
| `PA-004` | Every individual TCG set has explicit scene direction | Done | `config/poster_scenes.yaml` has exact one-to-one catalog coverage enforced by tests |
| `PA-005` | Full prompts cannot drift per set | Done | Creative scene is scope-specific; technical requirements are generated centrally |
| `PA-006` | Poster preparation is an optional post-fetch phase | Done | One-scope and batch initialization exist and preserve reviewed manifests |
| `PA-007` | Generation follows the scope contract | Done | Runner reads FLUX.2 model, mode, reference topology, seed, steps, generation size, output method, and dpi from `poster.yaml`; explicit overrides are recorded |
| `PA-008` | Figures remain authentic | Done with human gate | One-shot promotion binds review to raw/print pixels and exact source identities; fallback enforces exact opaque pixels |
| `PA-009` | Artwork matches typography and card cuts | Done | Prompt safe cells and subject placement derive from the same physical layout used by finalization and slicing |
| `PA-010` | Only promoted artwork enters a normal PDF | Done | `pdf.enabled` plus a local tracked promoted file gates inclusion |
| `PA-011` | Poster use is optional per build | Done | `--skip-poster` bypasses poster discovery and writes a separate build |
| `PA-012` | Every promotion is reproducible and auditable | Done | Provenance records model, prompt, source, references, workflow, review/audit, and output hashes |
| `PA-013` | Aggregate sections can own separate posters | Done | `posters.yaml` routes isolated leaf manifests and inserts each enabled poster after its matching cover |
| `PA-014` | 4×3/4×4 PDFs use matching page renderers | Open | Add physical page styles, templates, cutting guides, memory checks, and rendered-PDF QA |
| `PA-015` | Aggregate variants receive section-specific scenes and curated subject/reference sets | Prepared | All 15 current aggregate sections have exact catalog coverage and initializable leaf manifests; 11 are promoted and four await artwork review |
| `PA-015A` | Variant subjects retain their exact form | Done | Selection, cutouts, planner, fingerprints, promotion, and validation bind exact Official Artwork identity |
| `PA-016` | Post-fetch orchestration detects stale inputs | Done | Read-only planner separates expensive generation drift from cheap overlay/routing changes |
| `PA-017` | Joint generation can provide natural grounding without losing identity or card safety | Done for all thirteen promoted scopes | Seven individual-v7, five spatial-v5, and one regional-v6 bundles pass their reviewed identity, card, and scene gates |
| `PA-018` | Runtime remains KISS after experiments | Done | Production exposes only FLUX.2 `joint_scene` and `identity_lock`; all three reference topologies use the canonical joint workflow builder and common empty-target sampler path, with no separate experiment entry point |
| `PA-019` | Pull requests prove a release can be built without publishing | Done | PRs validate promotions, build every PDF/archive/manifest, and upload only a temporary artifact |
| `PA-020` | Raster card geometry closes exactly on every real canvas | Done | Cumulative physical endpoints drive preparation, finalization, slicing, promotion, and validation |
| `PA-021` | Default and fallback cannot become ambiguous | Done | One manifest owns one active generation contract; fallback selection and promotion are explicit |
| `PA-022` | Poster copy works in every language emitted for its scope | Done | Tests cover all 266 current target/language combinations; aggregate copy is complete in all nine PDF languages and TCG sets follow their advertised language inventory |
| `PA-023` | A poster carries the semantic information of its preceding cover | Done | Set posters show localized set name, card count, release date, title/logo, and project identity; aggregate posters show section title, subtitle/region, card count, description/range, collection title, and project identity; the cover-only cutting hint/build timestamp remains operational metadata |
| `PA-024` | Removing a preceding cover is an explicit gated migration | Open | Covers remain enabled; add an explicit renderer option only after every affected target is promoted and representative PDFs pass multilingual visual review |
| `PA-025` | Every current set and subsection is represented in the poster work plan | Done | 41 checked-in manifests cover 26 individual sets and 15 aggregate sections; tests reject missing or stale scene and manifest coverage |
| `PA-026` | A scope with fewer canonical subjects is not padded with duplicates or unrelated forms | Done | Section manifests accept one to the layout column count; two-subject `ExGen2/primal` uses the two outer bottom cards while the normal 3×3 default remains three subjects |
| `PA-027` | The existing cover path remains available when no poster can be consumed | Done | Missing or disabled poster routes leave the section cover and normal card pages intact; `--skip-poster` bypasses poster discovery before asset loading |
| `PA-028` | One promoted poster can be emitted either as physical cards or as a continuous page | Done for A4 3×3 | `cards` remains the default with nine 63.5 × 88.9 mm images and cutting guides; `--poster-page-mode full-page` draws one 200.5 × 276.7 mm image centered on A4 without cutting guides and writes a distinct filename |

## Current production boundary

- Thirteen promoted 3×3 bundles are enabled.
- All 41 current poster targets are configured: 13 are promoted and enabled;
  28 remain disabled until their source assets, generation, and human review
  are complete.
- All thirteen enabled bundles now use a reviewed `joint_scene` promotion:
  seven individual-v7, five spatial-v5, and one regional-v6.
- `identity_lock` remains an explicit fallback but has no active promoted scope.
- New manifests start with `joint_scene` / `individual_spatial_joint` v7.
  Accepted v5 and v6 manifests remain reproducible and are not mechanically
  migrated merely to make topology labels uniform.
- `regional_identity_joint` remains an explicit v6 option only to reproduce
  Generation III; broader regional migration is closed unless a materially
  different control mechanism changes the evidence.
- Fetching, planning, PDF building, and CI do not start ComfyUI.
- Generated candidates are local scratch; only promotion creates tracked input
  for deterministic PDF and release jobs.
- The individual-v7 rollout is complete for the seven user-reviewed
  replacements. Spatial-v5 remains accepted for five scopes; regional-v6
  remains promoted only for its reviewed Generation III result.
- Existing section covers remain in the PDF immediately before enabled posters.
  Poster copy now has semantic cover parity, but cover removal is a separate
  gated roadmap item rather than an implicit side effect.
- Enabled A4 posters use the cuttable `cards` presentation by default. The
  explicit `full-page` presentation keeps the complete localized poster at its
  200.5 × 276.7 mm physical grid size, centered on A4 without cutting guides.
- Wide PDF formats and promotion of the remaining 28 configured targets are
  explicit roadmap items.

## Change rule

When a requirement changes:

1. update its row and acceptance statement here;
2. update the operator guide when behavior or commands change;
3. add or adapt a deterministic regression test;
4. update the related GitHub tracking issue;
5. record candidate-specific evidence in the status or experiment log.
