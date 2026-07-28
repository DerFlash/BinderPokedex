# Poster Artwork Feature Status

This document records the current accepted state of the poster-artwork feature.
Operator commands live in [Poster Workflow](POSTER_WORKFLOW.md), durable product
requirements in
[Poster Requirements](POSTER_ARTWORK_REQUIREMENTS.md), and rejected candidate
evidence in
[Poster Experiment Log](POSTER_ARTWORK_EXPERIMENT_LOG.md).

Last audited: 2026-07-29

## Current decision

The production generator has one model family and two deliberately different
modes:

| Role | Mode | Contract |
| --- | --- | --- |
| Default | FLUX.2 `joint_scene` | Spatial cast plus one identity reference per subject, empty target, one sampler, one decode, deterministic 300-dpi Lanczos output |
| Fallback | FLUX.2 `identity_lock` | Two-pass scene construction, immutable source figures, exact opaque-pixel audit, 300-dpi model upscale |

`joint_scene` is the default for new scope manifests. Existing accepted
`identity_lock` scopes remain valid until a reviewed one-shot replacement is
promoted for that scope. A manifest and its provenance describe exactly one
active contract; the fallback is selected explicitly rather than through an
automatic or dual-active asset registry.

Anima, FLUX.1 Canny, Qwen Edit/spatial, SDXL regional identity, DreamO, direct
FLUX edit, and direct inpaint are rejected for this feature. Their results stay
in the experiment log and Git history, not in the production runner.

## Promoted scope state

| Scope group | Active mode | Status |
| --- | --- | --- |
| `Pokedex/sections/gen7` | `joint_scene` v5 candidate `00018` | Promoted, enabled, 2368 × 3268 px, nine card slices, 300 dpi |
| `Base1`, `SV03.5` | `identity_lock` | Accepted and enabled |
| `Pokedex/sections/gen1`–`gen6`, `gen8`, `gen9` | `identity_lock` | Accepted and enabled after their matching generation covers |
| `ExGen3/sections/normal`, `ExGen3/sections/mega` | `identity_lock` | Accepted and enabled after their matching section covers |

Generation VII `00018` is the first accepted one-shot poster. It uses seed
`260726054`, the reviewed Rowlet/Litten/Popplio sources, the Alola scene brief,
FLUX.2 Klein 4B distilled at four steps and 1 MP, then deterministic Lanczos
resampling to the exact physical print raster. Its stable generation
fingerprint is:

```text
0d2ba93bb0a2e391964887f2e546a9b2d37c67a00307fa7551f6280489fe87cb
```

The raw candidate SHA-256 is:

```text
fc1375f75ef771d6f1aac05bcd27ef67288597bdf3dd8d2f4baf60a908db5e98
```

The promotion records explicit visual approval bound to the reviewed raw,
print-size artwork, source identities, prompt, workflow, and reference hashes.
Stable `poster-flux2*` filenames keep PDF routing unchanged.

## Accepted one-shot contract

The preferred graph:

1. derives subject rectangles and baselines from the same physical layout used
   for slicing;
2. supplies a neutral poster-shaped cast for count, pose, scale, and placement;
3. supplies one unscaled 512 px identity reference per subject for anatomy,
   silhouette, color, and markings;
4. starts from one empty FLUX.2 latent;
5. synthesizes landscape and subjects together through one sampler and one
   decode;
6. performs no character composite, restoration, movement, or mask repair
   after decode;
7. resamples the accepted text-free result deterministically to the configured
   300-dpi raster;
8. adds localized logo and information only in deterministic post-processing.

Human review remains mandatory because a generated one-shot cannot prove
identity with pixel equality. Review covers cast count, exact form, anatomy,
face, markings, silhouette, pose, card fit, grounding, shadows, coherent depth,
safe text cells, and every physical card crop.

Natural foreground overlap is allowed but not forced. A coherent open patch of
terrain is preferable to a plant that changes front/behind order or terminates
at a subject boundary. Candidates `00019` and `00020` showed that more prompt
pressure did not create reliable crossings and could instead add a duplicate
character; their prompt changes were reverted.

## Fallback contract

`identity_lock` remains the accepted answer when a one-shot candidate changes a
defining trait or cannot meet card placement. It preserves the exact reviewed
source pixels and fails immediately if any fully opaque source pixel changes.
Its weaker scene integration is an explicit tradeoff, not a hidden post-process.

Switching a scope to the fallback requires a deliberate manifest contract and a
new promotion. The pre-Gen-VII-one-shot state is also recoverable from Git; no
second tracked active bundle is maintained.

## PDF, aggregate, and CI boundaries

- Fetching and PDF generation never start ComfyUI.
- Local generation is an optional post-fetch, pre-PDF phase.
- Only promoted, tracked artwork can enter a normal PDF.
- `--skip-poster` remains an explicit build bypass.
- Aggregate scopes route independent section manifests and promotions through
  `posters.yaml`, then insert each poster after its matching section cover.
- Pull requests validate all enabled promotions and build the complete release
  candidate as a temporary artifact only.
- Only a successful `v*` tag job may publish a GitHub Release.

## Next production work

1. Review the local `Base1 joint_scene/00001` rollout candidate. It passes the
   initial Mewtwo anatomy, padding, card-fit, and grounding review but is not
   promoted; the active `Base1` manifest remains on `identity_lock`.
2. After that review, continue the scope-by-scope rollout with
   `ExGen3/sections/mega` for exact named-form identity and one additional cast
   with strongly different body proportions.
3. Keep the same human identity/card/depth gate; do not mass-switch manifests
   before their replacements pass.
4. Use those renders to test natural near/far landscape intersections. Do not
   reopen prompt-only depth stress unless new evidence changes the mechanism.
5. Apply the section workflow to remaining aggregate variant sections only
   after their scene briefs and curated casts are reviewed.
6. Keep `wide_4x3` and `wide_4x4` modeled but disabled for PDF production until
   matching physical page formats, memory tests, and visual QA exist.

## Cleanup boundary

The production implementation contains only the two FLUX.2 modes above.
Generated references, workflows, candidates, run metadata, and PDF renders are
ignored local scratch. Promoted masters, previews, card slices, and provenance
are versioned. Rejected engine implementations are retained only by Git history
and the experiment log.

## Verification

The branch gate is:

```bash
python -m pytest -q scripts/tests
python -m scripts.poster_assets.validate_promoted_poster --all-enabled
python -m scripts.poster_assets.poster_work_plan --all-configured
```

Verified on 2026-07-29:

- `464 passed, 1 skipped`;
- all 13 enabled poster bundles validate;
- the planner reports all 13 configured targets as current;
- the Generation VII prompt and workflow still reproduce the reviewed `00018`
  hashes;
- a German `Pokedex` test PDF without card downloads was built successfully;
- Python compilation and `git diff --check` pass.
