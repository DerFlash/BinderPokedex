# Poster Artwork Feature Status

This document records the current accepted state of the poster-artwork feature.
Operator commands live in [Poster Workflow](POSTER_WORKFLOW.md), durable product
requirements in
[Poster Requirements](POSTER_ARTWORK_REQUIREMENTS.md), and rejected candidate
evidence in
[Poster Experiment Log](POSTER_ARTWORK_EXPERIMENT_LOG.md).

Last audited: 2026-07-31

## Current decision

The production generator has one model family and two deliberately different
modes. `joint_scene` currently has two reference topologies:

| Role | Mode | Contract |
| --- | --- | --- |
| Default/promoted | FLUX.2 `joint_scene` + `spatial_identity_joint` | Spatial cast plus one identity reference per subject, empty target, one sampler, one decode, deterministic 300-dpi Lanczos output |
| Selectable/promoted for Generation III only | FLUX.2 `joint_scene` + `regional_identity_joint` | Reference-free global landscape plus one identity-bound physical-card branch per subject, empty target, one sampler, one decode, deterministic 300-dpi Lanczos output; broader rollout stopped after the 2026-07-30 audit |
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
| `Pokedex/sections/gen7` | `joint_scene` / `spatial_identity_joint` v5 candidate `00018` | Promoted, enabled, 2368 × 3268 px, nine card slices, 300 dpi |
| `Pokedex/sections/gen1` | `joint_scene` / `spatial_identity_joint` v5 candidate `00001` | Promoted, enabled, 2368 × 3268 px, nine card slices, 300 dpi |
| `Pokedex/sections/gen2` | `joint_scene` / `spatial_identity_joint` v5 candidate `00001` | Promoted, enabled, 2368 × 3268 px, nine card slices, 300 dpi |
| `Base1` | `joint_scene` / `spatial_identity_joint` v5 candidate `00001` | Promoted, enabled, 2368 × 3268 px, nine card slices, 300 dpi |
| `ExGen3/sections/mega` | `joint_scene` / `spatial_identity_joint` v5 candidate `00001` | Promoted, enabled, 2368 × 3268 px, nine card slices, 300 dpi |
| `ExGen3/sections/normal` | `joint_scene` / `spatial_identity_joint` v5 candidate `00001` | Promoted, enabled, 2368 × 3268 px, nine card slices, 300 dpi |
| `Pokedex/sections/gen3` | `joint_scene` / `regional_identity_joint` v6 candidate `00001` | Promoted after user review, enabled, 2368 × 3268 px, nine card slices, 300 dpi |
| `SV03.5` | `identity_lock` | Accepted and enabled |
| `Pokedex/sections/gen4`–`gen6`, `gen8`, `gen9` | `identity_lock` | Accepted and enabled after their matching generation covers |

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

Base1 `00001` is the second accepted one-shot poster. It applies the same graph
to Mewtwo/Bulbasaur/Charmander with seed `260726503`; the tall Mewtwo silhouette,
hand anatomy, padding, all three physical card crops, shadows, and grounding
pass review. Its stable generation fingerprint is:

```text
d26549018a20003c0cb961cb5ab76f256c76872114deff3d34db04a17d7ec70a
```

Its promoted raw SHA-256 is
`105efc287a5687bd028ec07bfa90ff516df434db3831c46fb47fbca81b041da2`.
The existing stable PDF paths now resolve to this reviewed joint scene.

ExGen3 Mega `00001` is the third accepted one-shot poster. The unmodified graph
preserves the named Mega Latias, Mega Diancie, and Mega Lucario forms without
per-subject prompt exceptions while passing all three card crops. Its stable
generation fingerprint is:

```text
099b69bd95a6b6a16e1f57e941b136c69acef484c6db6bd077076314f9005216
```

ExGen3 Normal `00001` is the fourth accepted one-shot poster. Koraidon,
Pikachu, and Miraidon validate strongly different body proportions and target
scales with the same graph and no prompt exception. Its stable generation
fingerprint is:

```text
133603d3b0ed6ec6b8fea273ff74dfba1893b8112424099bea786d8ee5d69955
```

Generation I `00001` is the fifth accepted one-shot poster. Bulbasaur,
Charmander, and Squirtle remain complete and recognizable inside their three
physical cards with useful padding, shared morning light, coherent contact
shadows, and an uninterrupted Kanto meadow. Its stable generation fingerprint
is:

```text
3ad057acbcf8f95fd20b1661df5f938c7e06540d9c6275b773524db67b462f8d
```

The promoted raw SHA-256 is
`4d5ed1e63e1f972fc62054261d4e3d9c016f9e89864b1181cae6b443198b8969`.

Generation II `00001` is the sixth accepted one-shot poster. Chikorita,
Cyndaquil, and Totodile retain their distinctive source poses and defining
features while fitting their physical cards with generous padding. The Johto
landscape, warm light, shadows, and foreground vegetation remain coherent. Its
stable generation fingerprint is:

```text
0ca3ebca51b6683e4956a71b7659123e9db312b961ec4a66b0108dcf88628455
```

The promoted raw SHA-256 is
`668d5d732771529e4bb3ce2ff8cf13b6bb58bede9d49c1eace86f459e3fb5c92`.

Generation III previously remained on its accepted `identity_lock` fallback.
A seed change had fixed an extra-subject failure and produced faithful,
card-safe Treecko, Torchic, and Mudkip, but a plant rooted at the lower-right
foreground passed behind Mudkip. Moving the existing depth rule earlier left
the contradiction unchanged. A final binary foreground rule still left a
lower-right blade behind Mudkip and additionally produced the same
front-to-back jump at Treecko's lower-left foreground plant. Prompt-only depth
tuning was therefore closed after three bounded variants; no global prompt
change was adopted.

A later silhouette-free zone-layout A/B kept the Gen III one-shot graph and
three identity references fixed but replaced the complete spatial cast with
three soft neutral occupancy zones. It produced a bipedal Torchic/Mudkip
hybrid and placed all three subjects primarily above their physical bottom-row
cards without proving a foreground crossing. The zone-layout path is rejected.
The complete spatial cast remains the reproducible control for existing v5
promotions.

A subsequent cast-free regional-conditioning candidate binds each unscaled
identity reference directly to its physical bottom-card model branch while a
reference-free default branch generates the global landscape. All branches
contribute to the same empty latent and the same four-step sampler; there is no
later character insertion, mask repair, or composite. The 1-MP Generation III
candidate passes internal visual preflight for count, identity/anatomy, card
fit, padding, grounding, shadows, safe areas, and visible seams. It contains no
contradictory foreground/background switch, although its vegetation mostly
avoids direct character intersections. This is the leading Generation III
depth-bias evaluation candidate. After explicit user review it became the first
promoted `regional_identity_joint` pipeline-v6 asset. The existing spatial-cast
pipeline v5 remains reproducible for its promoted scopes.

The subsequent six-scope rerender audit did not approve another regional-v6
poster. Base1, Generation I, Generation II, and Generation VII produced
generated frames, repeated horizons, or separate lower-card landscapes.
ExGen3 Normal changed defining Koraidon/Miraidon anatomy; ExGen3 Mega cropped
Mega Latias and malformed defining Mega Lucario details. The single allowed
retry for each of the three frame-only near-passes reproduced the structural
lower-row split.

The cause is the actual ComfyUI conditioning semantics, not a missing prompt
sentence. `ConditioningSetDefaultCombine` removes the global default prediction
inside every complete regional card. Each local branch can therefore invent
its own terrain and horizon. An isolated additive-combine test restored one
global scene, but 50/50 global/local prediction averaging destroyed identity;
a final 2:1 local/global test still changed pose and anatomy and began
reintroducing a lower panorama. Both experimental code changes were reverted.
Generation III remains a visually accepted scope-specific result, not evidence
that regional-v6 is safe to migrate mechanically.

## Accepted and candidate one-shot contracts

The promoted spatial-v5 graph:

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

The selectable regional-v6 graph keeps steps 1 and 3–8, replaces the cast with
one reference-free default landscape branch, and binds every individual
identity reference to its complete physical bottom-card conditioning area.
Those branches still update one common latent within one sampler trajectory;
there is no image mask, layout-guide image, second pass, or subject composite.

Human review remains mandatory because a generated one-shot cannot prove
identity with pixel equality. Review covers cast count, exact form, anatomy,
face, markings, silhouette, pose, card fit, grounding, shadows, coherent depth,
safe text cells, and every physical card crop.

Natural foreground overlap is allowed but not forced. At every potential
landscape/character interaction, either the connected landscape object stays
fully clear of the character or it keeps one plausible front/behind order for
its entire visible intersection. Both outcomes pass; a plant that changes
front/behind order or terminates at a subject boundary fails. Candidates
`00019` and `00020` showed that more prompt
pressure did not create reliable crossings and could instead add a duplicate
character. The later Base1 `joint_scene/00002` A/B showed that even conservative
deduplication of repeated authority prose can add a duplicate fourth subject.
The reviewed long prompt therefore remains unchanged.

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

1. Treat the spatial-v5 representative rollout as complete: Gen VII, Base1,
   named Mega forms, and a strongly proportionally diverse subject set pass.
2. Keep the six spatial-v5 promotions unchanged. Do not run additional
   regional-v6 seed, prompt, or strength sweeps; the complete representative
   rerender audit failed to generalize the topology.
3. Use future requested renders to observe natural near/far landscape
   intersections. Generation III demonstrates that stronger or earlier prose
   can relocate rather than solve a contradictory crossing; do not reopen
   prompt-only depth stress unless new evidence changes the mechanism.
4. Review the individual-spatial Generation-I, Generation-VII, and Base1
   candidates together. Generation I passes its agent gate. Generation VII's
   first seed `260726054` has one user-found foreground blade ending at
   Popplio; retry `260726055` improves it but retains a smaller plant-depth
   discontinuity in human review. The second bounded seed-only retry
   `260726056` preserves count, anatomy, card fit, and one global scene, but
   human review still finds a lower-right blade slipping behind Popplio. There
   was no accepted individual-spatial Gen-VII successor at that point. A
   reciprocal 1-MP scene swap then rendered Popplio cleanly in the Generation-I
   meadow and Squirtle cleanly in Alola, proving that neither scene language
   nor subject alone is sufficient to cause the failure. After clean separation
   was explicitly accepted as coherent depth, seed `260726057` failed at 1 MP
   by adding a fourth Litten-like subject; seed `260726058` passes the complete
   agent gate with exactly three faithful, card-safe subjects and no broken
   landscape intersection. It is the preferred Generation-VII review candidate
   but still needs direct human confirmation before promotion. Base1 passes
   only after one bounded seed retry; compare its Mewtwo crop with the larger,
   currently promoted spatial-v5 crop before considering production
   integration.
5. Treat seed stability as an explicit review property. A scope may select a
   reviewed seed, but unbounded seed searching is not an acceptable substitute
   for reliable count, identity, card containment, one global scene, and
   coherent depth. The clarified-depth continuation is closed at seed
   `260726058`; do not continue Gen-VII seed searching unless human review
   rejects that candidate for a new, concrete hard-gate defect.
6. Treat the reciprocal scene swap as a diagnostic, not a prompt candidate.
   Scene wording can move broad foreground objects away from the character
   band, but this avoids a collision rather than controlling its z-order. If a
   bounded normal candidate can achieve neither clean separation nor a
   consistent overlap, the next experiment may add the minimal depth/occlusion
   guide defined in the experiment log. The guide remains deferred and must
   preserve one global scene, the existing identity inputs, and one final
   sampler; treat it as a materially different mechanism, not another prompt
   tweak.
7. Continue the legacy-scope rollout one reviewed scope at a time. Generation
   IV seed `260734875` passes with exactly Turtwig, Chimchar, and Piplup in one
   Sinnoh scene. Generation V seeds `260735038` and `260735039` both pass after
   enlarged source comparison; `260735039` is preferred for clearer Snivy and
   Oshawott details. Generation VI seed `260758583` duplicates Fennekin only at
   1 MP and fails; adjacent seed `260758584` passes count, identity, cards, and
   dense flower-depth review. Generation VIII seed `260715405` passes directly
   with exactly Grookey, Scorbunny, and Sobble in one coherent Galar scene.
   Generation IX seed `260778637` likewise passes directly with all defining
   details of Sprigatito, Fuecoco, and Quaxly. `SV03.5` seed `260726101` also
   passes with the Kanto trio, coastal set scene, clear logo area, and verified
   deterministic German logo/info overlay. Every previously remaining
   `identity_lock` scope now has a preferred individual-spatial candidate ready
   for direct human review; all promoted assets remain unchanged.
8. Apply the section workflow to future aggregate variant sections only after
   their scene briefs and curated subject/reference sets are reviewed.
9. Keep `wide_4x3` and `wide_4x4` modeled but disabled for PDF production until
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

Verified on 2026-07-31:

- `476 passed, 1 skipped`;
- all 13 enabled poster bundles validate;
- the planner reports all 13 configured targets as current;
- the Generation VII prompt and workflow still reproduce the reviewed `00018`
  hashes;
- a German `Pokedex` test PDF without card downloads was built successfully;
- Python compilation and `git diff --check` pass.
