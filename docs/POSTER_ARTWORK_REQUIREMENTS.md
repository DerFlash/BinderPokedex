# Poster Artwork Requirements and Roadmap

This document is the stable product and engineering contract for scope posters.
It separates accepted behavior from prepared extension points and open work.
Detailed evidence for promoted candidates is recorded in
[POSTER_ARTWORK_STATUS.md](POSTER_ARTWORK_STATUS.md).

Last reviewed: 2026-07-27

## Decisions

| Decision | Current direction |
| --- | --- |
| Default binder format | `standard_3x3` on A4 portrait at physical card size |
| Wide layouts | Keep `wide_4x3` and `wide_4x4` as supported artwork layouts and future matching PDF formats; never squeeze them onto A4 |
| Generation timing | Explicit optional post-fetch step, before PDF generation |
| PDF behavior | Consume only promoted local artwork; never launch ComfyUI implicitly |
| Prompt ownership | Set-specific creative briefs in one catalog plus one centrally generated technical/identity contract |
| Character identity | Reviewed source pixels are immutable; any changed anatomy is a hard rejection |
| Promotion | Human visual review plus deterministic validation remains mandatory |
| Missing poster | Normal PDF remains possible; enabled-but-missing promoted artwork is an error; `--skip-poster` is an explicit bypass |
| CI boundary | Pull requests build and validate the complete release candidate with read-only permissions; only `v*` tags may publish it |

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
| `PA-008` | Figures remain authentic | Done | Exact source cutouts are placed before final context generation and opaque source pixels are verified unchanged |
| `PA-009` | Artwork matches later typography and card cuts | Done | Prompt safe areas and figure placement derive from the same physical layout used by finalization and slicing |
| `PA-010` | Only promoted artwork enters a normal PDF | Done | `pdf.enabled` plus a local promoted file gates automatic inclusion |
| `PA-011` | Poster use is optional per build | Done | `--skip-poster` bypasses discovery/loading and writes a separate `_NO_POSTER.pdf` |
| `PA-012` | Every promoted poster is reproducible and auditable | Done | Promotion records model, prompt, source, workflow, validation, and output hashes |
| `PA-013` | Multiple posters can be assigned to aggregate sections | Done | A routing index binds isolated poster bundles to stable section IDs; PDFs insert every enabled bundle after its matching cover, while legacy single posters retain their first-cover behavior |
| `PA-014` | 4×3/4×4 PDFs use matching page renderers | Open | Add A3/custom page styles, templates, cutting guides, and rendered-PDF QA |
| `PA-015` | Aggregate variant scopes receive section-specific scene briefs | Open | Model `normal`, `mega`, `primal`, and future sections without pretending they are one unambiguous TCG set |
| `PA-016` | Post-fetch orchestration detects stale poster inputs | Open | Compare scope data, scene catalog, cutouts, logo, model contract, and promoted provenance before deciding whether work is needed |
| `PA-017` | Natural foreground occlusion may cross subjects safely | Research | Accept only a deterministic depth-aware method that retains exact identity and does not invent anatomy |
| `PA-018` | Alternative engines remain selectable but gated | Ongoing | Anima, FLUX.1 Canny, and Qwen candidates must pass the same promotion checks as FLUX.2 |
| `PA-019` | Pull requests prove that a complete release can be built without publishing it | Done | PRs reuse the read-only release-candidate workflow, validate all enabled posters, build every PDF and language archive, verify the manifest, and stop after a temporary Actions artifact |

## Current production boundary

- `Base1` and `SV03.5` have accepted, promoted 3×3 artwork and enabled PDF
  integration.
- Every current individual TCG set can now be initialized with a set-specific
  scene brief and the same production contract.
- The Pokédex has nine isolated, section-specific bundles with distinct seeds,
  regional scene briefs, deterministic nine-language section overlays, and
  exactly the three starter `featured_elements` from each generation.
- All nine Pokédex bindings remain disabled until their artwork is generated,
  reviewed, promoted, and validated. That product rollout remains tracked in
  [#2](https://github.com/DerFlash/BinderPokedex/issues/2).
- The default workflow deliberately stops before automatic promotion. Semantic
  scene quality, character boundary quality, and natural grounding still need
  human review.
- Further aggregate variant scopes and wide PDF pages remain explicit roadmap
  work rather than hidden assumptions.
- Pull requests and tagged releases use the same release-candidate build.
  Publication is a separate write-enabled job available only to `v*` tags.

## Change rule

When a requirement changes:

1. update its row and acceptance statement here;
2. update the implementation guide when operator behavior changes;
3. add or adapt an automated test for deterministic behavior;
4. update the GitHub tracking issue with the affected requirement IDs;
5. record candidate-specific evidence in `POSTER_ARTWORK_STATUS.md`.
