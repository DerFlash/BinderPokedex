# Poster Artwork Feature Status

This document records the current accepted production state. Operator commands
live in [Poster Workflow](POSTER_WORKFLOW.md), durable product requirements in
[Poster Requirements](POSTER_ARTWORK_REQUIREMENTS.md), architecture details in
[Poster Architecture](POSTER_ARTWORK_CONCEPT.md), and rejected or superseded
evidence in [Poster Experiment Log](POSTER_ARTWORK_EXPERIMENT_LOG.md).

Last audited: 2026-08-03

## Current decision

The production generator supports one model family and two generation modes.
`joint_scene` has three explicit reference topologies:

| Role | Contract | Current use |
| --- | --- | --- |
| Default | FLUX.2 `joint_scene` / `individual_spatial_joint` pipeline v7 | One poster-shaped identity-and-position reference per subject, empty target, one sampler, one decode, deterministic 300-dpi Lanczos output |
| Reproducible legacy | FLUX.2 `joint_scene` / `spatial_identity_joint` pipeline v5 | One shared spatial cast plus unscaled identity references; retained for its accepted promotions |
| Scope-specific legacy | FLUX.2 `joint_scene` / `regional_identity_joint` pipeline v6 | One regional identity branch per physical card; retained only for Generation III |
| Explicit fallback | FLUX.2 `identity_lock` | Two-pass scene, immutable source figures, exact opaque-pixel audit, and 300-dpi model upscale; currently no active scope uses it |

New manifests default to `individual_spatial_joint`. A manifest and provenance
describe exactly one active contract. Switching to a legacy topology or the
fallback requires a deliberate manifest change, a new candidate, human review,
and a new promotion; there is no automatic dual-active registry.

Anima, FLUX.1 Canny, Qwen Edit/spatial, SDXL regional identity, DreamO, direct
FLUX edit, and direct inpaint remain rejected for this feature. Their evidence
is retained in the experiment log and Git history, not the production runner.

## Promoted scope state

All thirteen enabled bundles are current, 2368 x 3268 px, sliced into nine
physical cards, and carry effective 299.99-dpi PNG metadata.

| Active contract | Promoted scopes |
| --- | --- |
| `joint_scene` / `individual_spatial_joint` v7 | `Pokedex/sections/gen4` seed `260734875`; `gen5` seed `260735039`; `gen6` seed `260758584`; `gen7` seed `260726058`; `gen8` seed `260715405`; `gen9` seed `260778637`; `SV03.5` seed `260726101` |
| `joint_scene` / `spatial_identity_joint` v5 | `Base1`; `Pokedex/sections/gen1`; `Pokedex/sections/gen2`; `ExGen3/sections/normal`; `ExGen3/sections/mega` |
| `joint_scene` / `regional_identity_joint` v6 | `Pokedex/sections/gen3` |
| `identity_lock` | none |

The seven v7 promotions are the exact user-reviewed 1-MP candidates. Before
promotion, regenerated production references, prompt snapshots, and workflow
graphs were compared with the isolated experiment runs. All reference and
prompt hashes matched, and every graph was structurally identical except for
the non-semantic `SaveImage` filename prefix. The reviewed raw pixels were then
resized deterministically with Lanczos and bound to explicit visual-review
records during promotion.

Stable `poster-flux2*` filenames keep PDF routing unchanged. Logos, localized
information panels, card slicing, and PDF placement remain deterministic and
are not model-generated.

## Accepted default graph

For each subject, `individual_spatial_joint`:

1. derives the final silhouette bounds, scale, baseline, and padding from the
   same physical layout used for slicing;
2. writes one neutral poster-shaped reference containing only that subject at
   its final position;
3. describes those named reference roles and exact normalized bounds in the
   central prompt;
4. starts from one empty FLUX.2 latent;
5. synthesizes landscape and all subjects together through one sampler and one
   decode;
6. performs no character composite, restoration, movement, inpaint repair, or
   learned upscale after decode;
7. resamples the reviewed text-free result deterministically to the exact
   300-dpi print raster;
8. adds localized logo and information only in deterministic post-processing.

Human review remains mandatory because generated identity cannot be proven by
pixel equality. Review covers exact cast count and form, anatomy, face,
markings, silhouette, pose, card fit, padding, grounding, shadows, coherent
depth, safe text cells, and every physical card crop.

Natural foreground overlap is allowed but not forced. A connected landscape
object must either stay clear of a subject or maintain one physically plausible
front/behind relationship for its complete visible intersection. Abrupt
termination at a silhouette or a front/back switch along the same object is a
hard failure.

## Deferred depth guide

The minimal explicit depth/occlusion guide remains deliberately inactive. It
may be tested only when a bounded normal candidate achieves neither clean
separation nor coherent overlap. Any such test must retain the three positioned
identity references, one empty target, one sampler, and one decode, and may add
only coarse `near`, `subject`, and `far` ownership. It must not contain scene
texture, character pixels, or a post-decode composite.

## PDF, aggregate, and CI boundaries

- Fetching and PDF generation never start ComfyUI.
- Local generation is an optional post-fetch, pre-PDF phase.
- Only promoted, tracked artwork can enter a normal PDF.
- `--skip-poster` remains an explicit build bypass.
- Aggregate scopes route independent section manifests and promotions through
  `posters.yaml`, then insert each poster after its matching section cover.
- Pull requests validate every enabled promotion and build a complete release
  candidate as a temporary artifact only.
- Only a successful `v*` tag job may publish a GitHub Release.

## Remaining work

1. Use `individual_spatial_joint` for new scopes, but keep human review and the
   bounded seed rule; a reviewed seed is not proof of universal stability.
2. Leave accepted v5 and v6 promotions unchanged unless a concrete visual or
   product requirement justifies a reviewed replacement.
3. Trigger the deferred minimal depth guide only under its documented failure
   condition, not merely to force visible foreground overlap.
4. Apply the section workflow to future aggregate variants only after their
   scene briefs and exact subject/form selections are reviewed.
5. Keep `wide_4x3` and `wide_4x4` modeled but disabled for PDF production until
   matching physical page formats, memory tests, and visual QA exist.

## Cleanup boundary

Generated references, workflows, candidates, run metadata, PDF smoke tests, and
rendered QA pages are ignored local scratch. Promoted masters, previews, card
slices, and provenance are versioned. Rejected implementations remain only in
Git history and the experiment log.

## Verification

The branch gate is:

```bash
python -m pytest -q
python -m scripts.poster_assets.validate_promoted_poster --all-enabled
python -m scripts.poster_assets.poster_work_plan --all-configured
```

Verified on 2026-08-03:

- the full suite passes with `479 passed, 1 skipped`;
- all 13 enabled poster bundles validate;
- the planner reports all 13 configured targets as current;
- every v7 production graph matches its reviewed candidate graph except for
  the output filename prefix;
- German Pokédex and `SV03.5` PDFs build successfully with posters enabled;
- rendered poster pages preserve the 3x3 card grid, overlays, card containment,
  and full-bleed scene continuity;
- Python compilation and `git diff --check` pass.
