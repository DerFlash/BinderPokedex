# Poster Artwork Requirements and Roadmap

This is the stable product and engineering contract for scope posters. Current
accepted assets are listed in
[Poster Status](POSTER_ARTWORK_STATUS.md), operator commands in
[Poster Workflow](POSTER_WORKFLOW.md), and rejected candidate evidence in
[Poster Experiment Log](POSTER_ARTWORK_EXPERIMENT_LOG.md).

Last reviewed: 2026-07-29

## Decisions

| Decision | Current direction |
| --- | --- |
| Default binder format | `standard_3x3` on A4 portrait at physical card size |
| Wide layouts | Keep `wide_4x3` and `wide_4x4` as artwork extension points; never squeeze them onto A4 |
| Generation timing | Explicit optional post-fetch step, before PDF generation |
| PDF behavior | Consume only promoted local artwork; never launch ComfyUI implicitly |
| Generator | FLUX.2 `joint_scene` is the default for new candidates |
| Fallback | FLUX.2 `identity_lock` remains explicitly selectable when a one-shot cannot pass identity or placement review |
| Prompt ownership | Set-specific creative briefs in one catalog plus one centrally generated identity, placement, depth, and safe-area contract |
| Character identity | Supplied Official Artwork is the authority for form, stature, anatomy, silhouette, pose, color, and markings |
| Form identity | Card/cover imagery and poster subjects are separate; Mega, Primal, X/Y, regional, and other forms keep their exact allowlisted Official Artwork identity |
| Promotion | Human visual review plus deterministic validation is mandatory |
| Missing poster | Normal PDF remains possible; enabled-but-missing promoted artwork is an error; `--skip-poster` is an explicit bypass |
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
| Coherent scene depth | Hard | Shadows and ground contact agree; every connected landscape element keeps a physically plausible front/behind relationship instead of ending at or weaving around a character |
| Deterministic print output | Hard | Text-free output reaches the exact configured 300-dpi dimensions through deterministic resampling; typography, logo, slicing, and PDF use remain deterministic |
| Set-specific scene quality | Preferred | The result is attractive, recognizable for the scope, and preserves the requested text-safe regions |
| Visible foreground overlap | Preferred | Natural foreground overlap may occur, but is not required. A coherent open patch is preferable to a forced contradictory overlap |

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
| FLUX.2 Spatial+Identity v5 `joint_scene` | Yes | Gen VII `00018`, Gen I `00001`, Gen II `00001`, Base1 `00001`, ExGen3 Mega `00001`, and ExGen3 Normal `00001` pass the accepted print-detail tolerance | All six promotions pass their physical crops with preferred fill | Coherent grounding and shadows; natural foreground crossings remain unproven | Default; six scopes promoted |
| Two-pass `identity_lock` | No | Exact source pixels | Reliable | Protected lower band can read as a layer | Explicit fallback; seven promoted scopes remain valid |
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
| `PA-007` | Generation follows the scope contract | Done | Runner reads FLUX.2 model, mode, seed, steps, generation size, output method, and dpi from `poster.yaml`; explicit overrides are recorded |
| `PA-008` | Figures remain authentic | Done with human gate | One-shot promotion binds review to raw/print pixels and exact source identities; fallback enforces exact opaque pixels |
| `PA-009` | Artwork matches typography and card cuts | Done | Prompt safe cells and subject placement derive from the same physical layout used by finalization and slicing |
| `PA-010` | Only promoted artwork enters a normal PDF | Done | `pdf.enabled` plus a local tracked promoted file gates inclusion |
| `PA-011` | Poster use is optional per build | Done | `--skip-poster` bypasses poster discovery and writes a separate build |
| `PA-012` | Every promotion is reproducible and auditable | Done | Provenance records model, prompt, source, references, workflow, review/audit, and output hashes |
| `PA-013` | Aggregate sections can own separate posters | Done | `posters.yaml` routes isolated leaf manifests and inserts each enabled poster after its matching cover |
| `PA-014` | 4×3/4×4 PDFs use matching page renderers | Open | Add physical page styles, templates, cutting guides, memory checks, and rendered-PDF QA |
| `PA-015` | Aggregate variants receive section-specific scenes and casts | Ongoing | ExGen3 `normal` and `mega` are accepted; repeat only for reviewed future sections |
| `PA-015A` | Variant subjects retain their exact form | Done | Selection, cutouts, planner, fingerprints, promotion, and validation bind exact Official Artwork identity |
| `PA-016` | Post-fetch orchestration detects stale inputs | Done | Read-only planner separates expensive generation drift from cheap overlay/routing changes |
| `PA-017` | Joint generation can provide natural grounding without losing identity or card safety | Done for six reviewed scopes; rollout ongoing | Gen VII `00018`, Gen I `00001`, Gen II `00001`, Base1 `00001`, ExGen3 Mega `00001`, and ExGen3 Normal `00001` are promoted; each additional scope must pass independently |
| `PA-018` | Runtime remains KISS after experiments | Done | Production exposes only FLUX.2 `joint_scene` and `identity_lock`; rejected adapters are removed from the runner |
| `PA-019` | Pull requests prove a release can be built without publishing | Done | PRs validate promotions, build every PDF/archive/manifest, and upload only a temporary artifact |
| `PA-020` | Raster card geometry closes exactly on every real canvas | Done | Cumulative physical endpoints drive preparation, finalization, slicing, promotion, and validation |
| `PA-021` | Default and fallback cannot become ambiguous | Done | One manifest owns one active generation contract; fallback selection and promotion are explicit |

## Current production boundary

- Thirteen promoted 3×3 bundles are enabled.
- Generation VII `00018`, Generation I `00001`, Generation II `00001`, Base1
  `00001`, ExGen3 Mega `00001`, and ExGen3 Normal `00001` are the six promoted
  `joint_scene` bundles.
- The other seven bundles remain accepted `identity_lock` fallbacks until
  reviewed one-shot replacements exist.
- New manifests start with `joint_scene`; existing manifests are never
  mechanically switched because that would invalidate accepted provenance.
- Fetching, planning, PDF building, and CI do not start ComfyUI.
- Generated candidates are local scratch; only promotion creates tracked input
  for deterministic PDF and release jobs.
- The representative rollout is complete. Future migrations remain
  scope-by-scope and review-gated rather than broad or mechanical.
- Wide PDF formats and remaining aggregate variant sections are explicit
  roadmap items.

## Change rule

When a requirement changes:

1. update its row and acceptance statement here;
2. update the operator guide when behavior or commands change;
3. add or adapt a deterministic regression test;
4. update the related GitHub tracking issue;
5. record candidate-specific evidence in the status or experiment log.
