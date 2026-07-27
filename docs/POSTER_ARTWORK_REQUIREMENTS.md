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
| Form identity | Card/cover imagery and poster subjects are separate; Mega, Primal, X/Y, and other forms keep their exact allowlisted Official Artwork identity |
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
| `PA-009` | Artwork matches later typography and card cuts | Done | Prompt safe areas and figure placement derive from the same physical layout used by finalization and slicing; visible source and conditioning pixels are also checked against the real generation canvas before composition |
| `PA-010` | Only promoted artwork enters a normal PDF | Done | `pdf.enabled` plus a local promoted file gates automatic inclusion |
| `PA-011` | Poster use is optional per build | Done | `--skip-poster` bypasses discovery/loading and writes a separate `_NO_POSTER.pdf` |
| `PA-012` | Every promoted poster is reproducible and auditable | Done | Promotion records model, prompt, source, workflow, validation, and output hashes |
| `PA-013` | Multiple posters can be assigned to aggregate sections | Done | A routing index binds isolated poster bundles to stable section IDs; PDFs insert every enabled bundle after its matching cover, while legacy single posters retain their first-cover behavior |
| `PA-014` | 4×3/4×4 PDFs use matching page renderers | Open | Add A3/custom page styles, templates, cutting guides, and rendered-PDF QA |
| `PA-015` | Aggregate variant scopes receive section-specific scene briefs | Ongoing | ExGen3 `normal` and `mega` are accepted section-local bundles; apply the same explicit scene, cast, and routing contract to `primal` and future sections instead of treating an aggregate as one unambiguous TCG set |
| `PA-015A` | Variant poster subjects retain their exact form | Done | Featured selection, cutout files/manifests, planner checks, promotion validation, conditioning, and generation fingerprints use a validated Official Artwork subject identity; distinct forms of one species remain distinct and special forms never fall back silently to base artwork |
| `PA-016` | Post-fetch orchestration detects stale poster inputs | Done | A read-only planner compares routing, scope data, scene catalog, cutout selection/pixels, logos, dynamic model contracts, effective prompts, semantic generation/overlay fingerprints, and promoted outputs; it separates expensive regeneration from cheap overlay or routing work |
| `PA-017` | Natural foreground occlusion may cross subjects safely | Research | Accept only a deterministic depth-aware method that retains exact identity and does not invent anatomy |
| `PA-018` | Alternative engines remain selectable but gated | Ongoing | Anima, FLUX.1 Canny, and Qwen candidates must pass the same promotion checks as FLUX.2 |
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
- All thirteen enabled 1-MP source and conditioning compositions fit within
  their real 848 × 1168 generation canvases. Cumulative physical endpoints
  close exactly at every real canvas edge, even where latent alignment makes
  the card widths or heights differ by one pixel. New generation fingerprints
  record raster geometry v2; new FLUX identity-lock fingerprints use graph
  contract v3, while the reviewed v1/v2 promotions remain valid as accepted
  legacy artifacts.
- Pull requests and tagged releases use the same release-candidate build.
  Publication is a separate write-enabled job available only to `v*` tags.

## Change rule

When a requirement changes:

1. update its row and acceptance statement here;
2. update the implementation guide when operator behavior changes;
3. add or adapt an automated test for deterministic behavior;
4. update the GitHub tracking issue with the affected requirement IDs;
5. record candidate-specific evidence in `POSTER_ARTWORK_STATUS.md`.
