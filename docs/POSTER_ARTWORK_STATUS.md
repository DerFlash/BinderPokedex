# Poster Artwork Feature Status

This document records the acceptance state of the poster-artwork feature branch.
It complements the implementation-focused
[Poster Artwork](POSTER_ARTWORK_CONCEPT.md) documentation.

Last audited: 2026-07-26

## Current committed baselines

| Scope | Engine | Seed | Artwork verdict | PDF integration |
| --- | --- | ---: | --- | --- |
| `Base1` | FLUX.2 Klein 4B distilled, two-pass source-pixel lock, 2 x 4 steps | `260726503` | accepted | enabled |
| `SV03.5` | FLUX.2 Klein 4B distilled, two-pass source-pixel lock, 2 x 4 steps | `260726101` | accepted | enabled |

Both accepted candidates use the same local ComfyUI graph. Its first FLUX pass
creates a full-bleed landscape with dynamic, latent-aligned overscan. The exact
reviewed source figures are placed on its one continuous lower ground before a
second FLUX pass sees their final composition and completes only the upper
scene. No diffusion or VAE operation may touch the protected lower subject band.
The resulting 1 MP artwork must pass an exact opaque-source-pixel comparison,
is model-upscaled to the exact 300-dpi physical layout, and then receives only
deterministic typography.

This replaces the former Base1 edit baseline. Direct FLUX edits, direct
silhouette inpainting, native-resolution comparisons, FLUX.1 Canny, and Qwen
multi-reference editing all failed the stricter source comparison in different
ways. They remain diagnostic evidence, not promoted artwork.

## Accepted requirements

- Each complete asset is produced in one local ComfyUI workflow. The source
  figures are present at their final position before the final context pass, so
  the generator sees the intended composition instead of placing them blindly
  into a finished scene.
- Reviewed Pokemon pixels are immutable. They are never redrawn by diffusion,
  reconstructed through the VAE, moved, or rescaled inside the identity-lock
  workflow.
- The runner compares every fully opaque source pixel immediately after
  generation. Base1 passes with 52,584 exact pixels and SV03.5 with 62,719;
  both record zero changed pixels in promoted provenance.
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
- Both scopes retain the reviewed character count, anatomy, colors, proportions,
  pose, scale, placement, and source pixels. Mewtwo keeps its narrow face,
  central chest ridges, three digits on each hand, complete limbs, and tail;
  Bulbasaur, Charmander, and Squirtle retain their complete source silhouettes.
- The physical layout uses 63.5 x 88.9 mm cards and 5 mm binder gaps. Each
  featured Pokemon remains wholly inside one bottom-row card, with visible
  landscape padding around its silhouette.
- Identity-lock placement is derived from the shared physical layout. Optional
  model-specific composition compensation remains declarative in each scope
  manifest for the probabilistic edit engines.
- Overscan scales with output dimensions. The protected band defaults to 70
  percent but moves up automatically when a taller silhouette needs it.
- Any individual TCG set with complete generated scope metadata can be
  initialized through `init_poster_scope.py`; layout-driven cast count, stable
  seed, localized logos, model contract, and fallback candidates are generated
  without adding Pokemon or set names to Python.
- The title logo occupies the top-center card. The centered middle-card panel
  contains localized set name, card count, and release date and has a bounded
  maximum width and height.
- `Binder Pokedex` is rendered at the lower-right edge of the final poster.
- All languages available for the promoted scopes (`de`, `en`, `fr`, `es`,
  `it`) are supported by the deterministic overlay.
- The poster is sliced with the same geometry used by preparation and PDF
  rendering and is inserted exactly once after the first section cover.
- Promoted artwork is 2368 x 3268 px, every card crop is 750 x 1050 px, and the
  PDF embeds every poster card at 300 ppi.
- Promotion is transactional and stores hashes for model, encoder, VAE,
  upscaler, prompts, cutouts, references, workflows, and all promoted outputs.
- Diagnostic PDF modes use distinct filenames, and renderer failures propagate
  to a failing scope command.
- Local ComfyUI sampling runs on Apple Metal/MPS. CPU is used only for the
  narrowly scoped dequantization and offload operations required by unsupported
  MPS tensor conversions.
- FLUX.2, Anima, FLUX.1 Canny, and Qwen Edit remain separate selectable
  engines. The promoted implementation is scope-driven and has been exercised
  with two independent sets.

## Partially satisfied requirements

| Requirement | Current boundary | Acceptance criterion |
| --- | --- | --- |
| Natural occlusion | Exact identity-lock prevents scenery from crossing source pixels; one low continuous ground avoids contradictory depth | Add depth-aware foreground masks only if they preserve identity deterministically |
| Engine extensibility | FLUX.2, Anima, FLUX.1 Canny, and Qwen Edit are selectable through one runner | Keep architecture-specific workflow construction and provenance isolated when adding another engine |
| Alternative models | FLUX.1 Canny changed Mewtwo's face, chest, colors, and hand; Qwen created a giant fourth Mewtwo | Retain both adapters for controlled comparison, but do not promote either rejected candidate |
| Anima | Workflow is retained and runnable | Promote only after it produces a candidate that passes the same review gate |
| New set art direction | Any individual set now runs from metadata and a default scene; semantic set-specific scenery still benefits from a short manifest brief | Review or refine `artwork.scene` before spending the production render |

## Remaining production requirements

- Keep the mandatory visual review for character identity, anatomy, natural
  grounding, and generated silhouette boundaries.
- Treat any changed digit count, head/face, chest geometry, limb, tail, pose,
  color, or defining contour as a hard rejection even if the background improves.
- Reject generated scenery beside a subject when it reads as an additional body
  part.
- Keep exact opaque-pixel validation mandatory, but do not misrepresent it as
  semantic depth or foreground-occlusion validation.
- Keep Anima, FLUX.1 Canny, and Qwen Edit experimental until a candidate passes
  the same promotion gate.

## Cleanup boundary

The legacy generated-background composition, `poster.png`, layout guide, and
background import commands have been removed. Shared IO, placement, and
typography helpers now live in neutral modules used by the production flow.

Ignored ComfyUI outputs, generated prompt snapshots, workflows, references, PDF
builds, and temporary renders are local scratch data. They may be deleted after
reviewed candidates and their provenance have been promoted.

## Verification record

Completed on 2026-07-26:

- The complete suite passes: 173 tests passed and one unrelated, pre-existing
  EX-logo feature test remains explicitly skipped.
- Python compilation and `git diff --check` pass.
- Both promoted bundles pass `validate_promoted_poster.py`, including manifest
  equality, provenance hashes, 2368 x 3268 artwork, nine 750 x 1050 card crops,
  300-dpi metadata, and exact opaque-source-pixel records.
- The configured model, encoder, VAE, and Real-ESRGAN hashes match the actual
  files in the local ComfyUI installation.
- All ten Base1/SV03.5 overlays for `de`, `en`, `fr`, `es`, and `it` render at
  2368 x 3268 px with 300-dpi metadata.
- The complete German Base1 and SV03.5 PDFs were generated and visually
  inspected. Their poster page embeds exactly nine 750 x 1050 images at
  300 x 300 ppi.
- Both accepted artworks and all six 750 x 1050 bottom character cards were
  visually compared with the reviewed cutouts after model upscaling. Character
  anatomy, card padding, the continuous lower ground, and absence of adjacent
  body-like shapes pass.
- Repeating the complete SV03.5 generation with the same inputs produced
  bit-identical raw and model-upscaled PNG hashes.
- The rejected FLUX.1 Canny and Qwen candidates remain local diagnostics only;
  neither was promoted.

For every future candidate, the same whole-poster, per-card, localized-overlay,
and rendered-PDF review remains the promotion gate. Identity-lock topology is
covered by tests, but final anatomy, grounding, and silhouette-boundary review
deliberately remains human visual QA; the code does not claim false confidence.
