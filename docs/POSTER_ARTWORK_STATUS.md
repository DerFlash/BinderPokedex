# Poster Artwork Feature Status

This document records the current accepted production state. Operator commands
live in [Poster Workflow](POSTER_WORKFLOW.md), durable product requirements in
[Poster Requirements](POSTER_ARTWORK_REQUIREMENTS.md), architecture details in
[Poster Architecture](POSTER_ARTWORK_CONCEPT.md), and rejected or superseded
evidence in [Poster Experiment Log](POSTER_ARTWORK_EXPERIMENT_LOG.md).

Last audited: 2026-08-05

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

ExGen2 Normal now has one explicitly reviewed FLUX.2 Dev 32B promotion using
the same 1-MP `individual_spatial_joint` contract. It is kept PDF-disabled
until its deterministic overlay is reviewed. Native Klein 4B/9B, Base 4B,
corrected Kontext BF16, 2-MP spatial references, and an abstract box guide
remain experiment evidence rather than competing active contracts.

Anima, FLUX.1 Canny, FLUX.1 Kontext, Qwen Edit/spatial, SDXL regional identity,
DreamO, direct FLUX edit, and direct inpaint remain rejected for this feature.
Their evidence is retained in the experiment log and Git history, not the
production runner.

An isolated FLUX.2 Klein 4B paired edit-LoRA experiment is now in its dataset
phase. Its versioned contract and audit tool do not add a production mode. The
first inventory found fourteen promoted raw targets and eighteen historical
`identity_lock` inputs: four inputs are blank, thirteen nonblank inputs no
longer match the current exact-source placement/pixel contract, and the one
historically exact input belongs to the deliberately excluded ExGen2 Normal
target. A fresh Generation I MPS/BF16 identity-lock render passes all 62,563
opaque source pixels. A bounded full-composite FLUX.2 teacher pass keeps the
scene geometry and card placement substantially aligned and adds common contact
shadows, but its raw character repaint still changes small anatomy. Restoring
the canonical positioned RGBA subjects produces zero changed opaque source
pixels, but human card-crop review rejects Generation I and the original Base
Set scene as well as
two bounded Generation-VII seeds: grass or leaves rooted in the foreground run
behind one or more restored subjects. Exact pixels prove anatomy and placement,
not depth. There are therefore zero surviving pair candidates from the original
scope scenes and no training checkpoint. One training-only Base Set
augmentation on a natural sand beach is the first human-approved gold holdout:
its
surface has no upright occluder, all 52,343 opaque source pixels remain exact,
and the teacher adds shared directional shadows. Three further clear-surface
gold train pairs use Generation II on snow, Generation III on black sand, and
Generation IV on pale stone; the user approved all three complete targets and
their physical card crops on 2026-08-05. A fourth gold train pair places the
Generation-V cast on a natural red-clay badlands floor; its complete target and
card crops were approved the same day. A sterile
smooth-earth control and the first wall-like Generation-IV stone background are
rejected. The simple recipe is
restricted to genuinely clean avoidance or entirely behind-subject landscape;
foreground crossings need an explicit reviewed foreground layer. See
[Poster Artwork Integration LoRA](POSTER_ARTWORK_TRAINING.md).

## Promoted scope state

All thirteen enabled bundles and the additional disabled ExGen2 Normal
promotion are current, 2368 x 3268 px, sliced into nine physical cards, and
carry effective 299.99-dpi PNG metadata.

| Active contract | Promoted scopes |
| --- | --- |
| `joint_scene` / `individual_spatial_joint` v7 | `Pokedex/sections/gen4` seed `260734875`; `gen5` seed `260735039`; `gen6` seed `260758584`; `gen7` seed `260726058`; `gen8` seed `260715405`; `gen9` seed `260778637`; `SV03.5` seed `260726101` |
| `joint_scene` / `individual_spatial_joint` Dev 32B | `ExGen2/sections/normal` seed `260737078` (promoted, PDF disabled pending overlay review) |
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

## Configured target and language coverage

Every current target has a checked-in manifest and a configured creative brief.
Unreviewed targets remain disabled, so configuration coverage never implies
visual approval.

| Scope family | Configured | Promoted and enabled | Disabled / awaiting activation |
| --- | ---: | ---: | ---: |
| Individual TCG sets | 26 | 2 | 24 |
| Pokédex generations | 9 | 9 | 0 |
| ExGen1 sections | 1 | 0 | 1 |
| ExGen2 sections | 3 | 0 | 3 |
| ExGen3 sections | 2 | 2 | 0 |
| **Total** | **41** | **13** | **28** |

One of the 28 disabled targets is the promoted ExGen2 Normal poster; the other
27 targets still require generation and review.

The deterministic overlay contract is complete for all 266 language outputs
currently implied by those targets. Aggregate sections contain title,
subtitle/region, Pokémon count, and description/range in all nine PDF languages.
Individual TCG sets define localized set copy and logo routes for every
language advertised by their fetched source data. Missing TCG languages are
not invented and are not PDF targets.

Scope JSON is the only semantic copy source for both covers and posters.
Poster manifests no longer copy titles or select title/deduplication styles.
The overlay infers complete logo, inline token logo, or text rendering and
draws plain text directly without a title panel. It removes an identical title
row automatically. Cover count labels use the scope
type, so TCG-set totals are cards while Pokédex and variant totals are Pokémon.

The poster now contains all semantic cover information: collection/set title,
section title where applicable, subtitle/region, collection count, description or
release date, representative Pokémon, and the `Binder Pokedex` project mark.
The existing cover is nevertheless still rendered before the poster. Its
build-time footer (cutting hint and build date) is operational metadata, not
scope content, and is intentionally not duplicated on the artwork. Removing
the cover is a separate future renderer migration after all affected posters
are promoted and representative multilingual PDFs have been reviewed.

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
- A disabled or absent poster route leaves the existing section cover and card
  pages intact.
- Enabled A4 posters default to nine physical cards; `--poster-page-mode
  full-page` emits the same localized poster once at 200.5 × 276.7 mm, centered
  on A4 without cutting guides.
- Aggregate scopes route independent section manifests and promotions through
  `posters.yaml`, then insert each poster after its matching section cover.
- All 41 current individual and aggregate targets are configured; 14 are
  promoted and 13 of those are enabled.
- Pull requests validate every enabled promotion and build a complete release
  candidate as a temporary artifact only.
- Only a successful `v*` tag job may publish a GitHub Release.

## Remaining work

1. Run the bounded 100-step BF16/MPS plumbing overfit on the four approved
   Generation II-V train pairs. Base1 remains an unseen holdout. Inspect finite
   loss and saved weights before any holdout render or longer LoRA run.
2. Use `individual_spatial_joint` for new scopes, but keep human review and the
   bounded seed rule; a reviewed seed is not proof of universal stability.
3. Leave accepted v5 and v6 promotions unchanged unless a concrete visual or
   product requirement justifies a reviewed replacement.
4. Trigger the deferred minimal depth guide only under its documented failure
   condition, not merely to force visible foreground overlap.
5. Review the promoted ExGen2 Normal overlay, then enable it if the localized
   composition passes. The first Dev candidates for Mega and Primal failed
   exact count/placement; retry only after a material control change, not with
   a seed sweep.
6. Generate, review, promote, and then enable the remaining 27 unpromoted
   targets. The planner reports 25 as `needs_assets`; ExGen2 Mega and Primal
   remain technically renderable but blocked on a new placement/count-control
   hypothesis.
7. Decide on and implement explicit cover replacement only after the affected
   target family is fully promoted and its multilingual PDFs pass visual QA.
8. Keep `wide_4x3` and `wide_4x4` modeled but disabled for PDF production until
   matching physical page formats, memory tests, and visual QA exist.

## Cleanup boundary

Generated references, workflows, candidates, run metadata, PDF smoke tests, and
rendered QA pages are ignored local scratch. Promoted masters, previews, card
slices, and provenance are versioned. Rejected implementations remain only in
Git history and the experiment log. Production tests call the canonical
workflow builders directly; retired experiment entry points are not retained.

## Verification

The branch gate is:

```bash
python -m pytest -q
python -m scripts.poster_assets.validate_promoted_poster --all-enabled
python -m scripts.poster_assets.poster_work_plan --all-configured
```

Core branch verification rerun on 2026-08-04:

- the full suite passes with `522 passed, 1 skipped`;
- all 13 enabled poster bundles validate;
- the planner reports 41 configured targets: 13 current, 3 ready to generate,
  and 25 needing assets;
- Python compilation and `git diff --check` pass.

The following production and visual checks remain current from 2026-08-03:

- every v7 production graph matches its reviewed candidate graph except for
  the output filename prefix;
- a full German Pokédex PDF plus Japanese Pokédex and German ExGen3 smoke PDFs
  build successfully with posters enabled;
- fresh German Base1, Pokédex, and ExGen3 smoke PDFs confirm the shared title,
  count-unit, description, and poster-insertion data flow;
- rendered poster pages preserve the 3x3 card grid, overlays, card containment,
  and full-bleed scene continuity;
- rendered Base1 smoke PDFs verify both the default cuttable page and the
  continuous full-page presentation; a Base2 smoke PDF verifies the unchanged
  cover fallback when no poster is enabled.
