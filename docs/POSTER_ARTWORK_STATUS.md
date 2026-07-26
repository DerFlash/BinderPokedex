# Poster Artwork Feature Status

This document records the acceptance state of the poster-artwork feature branch.
It complements the implementation-focused
[Poster Artwork](POSTER_ARTWORK_CONCEPT.md) documentation.

Last audited: 2026-07-26

## Current production candidates

| Scope | Engine | Seed | Artwork | PDF integration |
| --- | --- | ---: | --- | --- |
| `Base1` | FLUX.2 Klein 4B distilled, edit/identity, 4 steps | `260716311` | reviewed | enabled |
| `SV03.5` | FLUX.2 Klein 4B distilled, edit/identity, 4 steps | `260726101` | reviewed | enabled |

Both candidates were sampled as one cohesive scene at 0.5 MP, model-upscaled to
the exact 300-dpi physical layout, and then finalized with deterministic
typography. The finalizer never composites, moves, or redraws Pokemon.

## Accepted requirements

- The complete landscape and all Pokemon are generated together in one diffusion
  pass. Only the exact set logo, localized metadata, and project signature are
  added afterward.
- Generation starts from freshly prepared composition and identity references.
  It does not consume the legacy poster, background, or layout-reference result.
- No visible landing pads, safe-area boxes, paths, radial walkways, artificial
  clearings, poster frames, text, or logos are part of the generated artwork.
- Environmental occlusion follows one camera-space depth order. Landscape
  elements may cover a character only when they plausibly lie in front of it.
- Reference silhouettes are treated as observed geometry. Character count,
  anatomy, colors, proportions, pose, scale, and placement must not be
  reinterpreted.
- The physical layout uses 63.5 x 88.9 mm cards and 5 mm binder gaps. Each
  featured Pokemon remains wholly inside one bottom-row card, with visible
  landscape padding around its silhouette.
- Mewtwo-specific scale, placement, and anatomy reinforcement are declarative in
  the `Base1` scope manifest rather than hard-coded into the generator.
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
- FLUX and Anima remain separate selectable engines. The promoted implementation
  is scope-driven and has been exercised with two independent sets.

## Partially satisfied requirements

| Requirement | Current boundary | Acceptance criterion |
| --- | --- | --- |
| Character identity | Strong reference conditioning and manual review; diffusion remains stochastic | Keep mandatory visual review or add a reliable silhouette/anatomy validator |
| Card-safe output | Source references are validated; generated silhouettes are reviewed manually | Add generated-artwork boundary validation before promotion |
| Natural occlusion | Prompted and visually reviewed | Keep as a visual-review item unless a dependable depth check becomes available |
| Engine extensibility | FLUX and Anima are selectable through a shared runner | Replace hard-coded engine branching before adding a third architecture |
| Alternative models | FLUX.2 model and encoder are selectable | Add a dedicated adapter for FLUX.1 Dev GGUF if that experiment is resumed |
| Anima | Workflow is retained and runnable | Promote only after it produces a candidate that passes the same review gate |

## Remaining production requirements

- Keep the mandatory visual review for character identity, anatomy, natural
  occlusion, and generated silhouette boundaries.
- Add an automated generated-artwork silhouette validator only if it can avoid
  false confidence around natural foreground occlusion.
- Replace hard-coded engine branching before adding a third model architecture.
- Keep Anima and any future FLUX.1 Dev GGUF adapter experimental until a candidate
  passes the same promotion gate.

## Cleanup boundary

The legacy generated-background composition, `poster.png`, layout guide, and
background import commands have been removed. Shared IO, placement, and
typography helpers now live in neutral modules used by the production flow.

Ignored ComfyUI outputs, workflows, references, PDF builds, and temporary renders
are local scratch data. They may be deleted after reviewed candidates and their
provenance have been promoted.

## Verification record

Completed on 2026-07-26:

- The complete suite passes: 159 tests passed and one unrelated, pre-existing
  EX-logo feature test remains explicitly skipped.
- Python compilation and `git diff --check` pass.
- Both promoted bundles pass `validate_promoted_poster.py`, including manifest
  equality, provenance hashes, 2368 x 3268 artwork, nine 750 x 1050 card crops,
  and 300-dpi metadata.
- The configured model, encoder, VAE, and Real-ESRGAN hashes match the actual
  files in the local ComfyUI installation.
- All ten Base1/SV03.5 overlays for `de`, `en`, `fr`, `es`, and `it` render at
  2368 x 3268 px with 300-dpi metadata.
- The complete German Base1 and SV03.5 PDFs were generated and visually
  inspected. Their poster page embeds exactly nine 750 x 1050 images at
  300 x 300 ppi.
- The complete Base1 and SV03.5 artwork and bottom-row character crops were
  visually reviewed, including Mewtwo's identity and top/right card padding.

For every future candidate, the same whole-poster, per-card, localized-overlay,
and rendered-PDF review remains the promotion gate. The stochastic identity,
anatomy, silhouette-boundary, and natural-occlusion checks deliberately remain
human visual checks; the code does not claim false confidence for them.
