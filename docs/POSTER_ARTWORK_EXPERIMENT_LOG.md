# Poster artwork experiment log

This log records local visual experiments and the decision that followed each
one. Most candidates are intentionally not promoted; an entry says explicitly
when one becomes the accepted baseline. The log complements the requirements
and status documents with the variable changed at each useful checkpoint.
Commands and implementation names below describe their historical checkpoints;
rejected builders were removed from the production tree during the 2026-07-29
KISS cleanup and remain recoverable through Git history.

## Non-negotiable review rules

- The final artwork is synthesized by the model as one coherent scene. No
  character cutout is composited or restored after the final model pass.
- Supplied character artwork is the identity and anatomy authority.
- Landscape elements keep a physically coherent front/behind relationship at
  every character intersection.
- Every complete character remains inside its assigned bottom-row card after
  physical poster slicing.
- Generated text, boxes, landing pads, paths, and visible layout guides are not
  part of the artwork.

## Pokédex Generation I / FLUX.2 Klein rollout

The first remaining Pokédex migration applies the unchanged promoted graph and
prompt builder to seed `260782266`, the Kanto scene brief, and the reviewed
Bulbasaur, Charmander, and Squirtle references.

| Candidate | Pipeline change | Result | Decision |
| --- | --- | --- | --- |
| `joint_scene/00001` | Change only the scope seed, scene brief, identities, and shared physical placement derived for Generation I | Exactly the three expected starters appear once and remain complete inside their assigned physical cards with useful padding. Their defining anatomy, faces, colors, markings, silhouettes, and poses match the references within the accepted one-shot print-detail tolerance. Morning light, contact shadows, continuous meadow terrain, and foreground plants remain spatially coherent | Accepted and promoted on 2026-07-29 as the fifth `joint_scene` scope |

The Metal/MPS render completed in 229.93 seconds. Reproducibility evidence:

| Artifact | SHA-256 |
| --- | --- |
| Raw 848 × 1168 candidate | `4d5ed1e63e1f972fc62054261d4e3d9c016f9e89864b1181cae6b443198b8969` |
| Text-free 2368 × 3268 print raster at 300 dpi | `1a4c376d48d4fdde92d9901985f5baf44207909a0088831f5278e65d18b04df2` |

The complete generation fingerprint is:

```text
3ad057acbcf8f95fd20b1661df5f938c7e06540d9c6275b773524db67b462f8d
```

## Pokédex Generation II / FLUX.2 Klein rollout

The unchanged graph and prompt builder use seed `260753030`, the Johto scene
brief, and the reviewed Chikorita, Cyndaquil, and Totodile references.

| Candidate | Pipeline change | Result | Decision |
| --- | --- | --- | --- |
| `joint_scene/00001` | Change only the scope seed, scene brief, identities, and shared physical placement derived for Generation II | Exactly the three expected starters appear once. Chikorita's leaf and body markings, Cyndaquil's side pose and flame, and Totodile's raised-leg pose, jaws, teeth, limbs, and back spikes remain faithful within the accepted one-shot print-detail tolerance. All three physical crops pass with generous padding; shared warm light, shadows, meadow, and foreground vegetation remain coherent | Accepted and promoted on 2026-07-29 as the sixth `joint_scene` scope |

The Metal/MPS render completed in 203.82 seconds. Reproducibility evidence:

| Artifact | SHA-256 |
| --- | --- |
| Raw 848 × 1168 candidate | `668d5d732771529e4bb3ce2ff8cf13b6bb58bede9d49c1eace86f459e3fb5c92` |
| Text-free 2368 × 3268 print raster at 300 dpi | `f9849c301d29c0176a41b611ecc0c4b0ec7abf9051743a86b3bcd144fb5e3a3d` |

The complete generation fingerprint is:

```text
0ca3ebca51b6683e4956a71b7659123e9db312b961ec4a66b0108dcf88628455
```

## Pokédex Generation III / foreground-depth boundary

The unchanged production graph uses the Hoenn scene brief and reviewed Treecko,
Torchic, and Mudkip references. Configured seed `260750880` first produced a
fourth background creature and failed exact count. Seed `260750881` removed the
extra subject and passed identity and card fit, but exposed the requested hard
case: a plant rooted at the lower-right foreground passed behind Mudkip's rear
body and tail.

The subsequent depth test holds model, seed, references, rectangles, sampler,
scene, count rules, identity rules, and all non-depth prompt text fixed.

| Candidate | Sole depth change | Result | Decision |
| --- | --- | --- | --- |
| `depth/original` | Production prompt; depth paragraph begins after 648 whitespace-delimited words | Exactly three faithful, card-safe subjects, but the lower-right foreground plant passes behind Mudkip | Rejected at coherent-depth gate |
| `depth/early` | Move the existing depth paragraph unchanged so it begins after 388 words; total remains 894 words | The same lower-right foreground relationship remains behind Mudkip | Rejected; prompt priority alone does not solve the crossing |
| `depth/binary` | Keep the earlier position and replace only the depth paragraph with a 904-word total that defines bottom-edge vegetation as foreground and clarifies that anatomical completeness does not require every exterior pixel to remain visible | A lower-right blade still passes behind Mudkip's tail; additionally, the lower-left foreground plant passes behind Treecko's foot, body, and tail | Rejected; the contradiction remains and appears at another subject too |

Metal/MPS evidence:

| Candidate | Runtime | Raw 848 × 1168 SHA-256 | Workflow SHA-256 |
| --- | ---: | --- | --- |
| `depth/original` | 243.75 s | `e8103fe2f8e7a1d426f9aa7f9e036251db41cdeb506af0b85c080b1d39083a5e` | `a13685af821a31f409af117a0da77fddbec13420475d11c51be6cde463d93640` |
| `depth/early` | 189.47 s | `3abfbf3c45c3815b58306b759eb341892634afdc820c8876277c76c3cbb0842c` | `a0f70730f9632270ed546841f45c2f87a44b808c0aed3d5bdb1aa9bedaa33a63` |
| `depth/binary` | 206.11 s | `a6339c43c844897704fa251bd32d196347474881e1bd473e70ba3800436ba268` | `0408f3499909f72902879da377c1e51d51ff723fba547073583a49592c83064c` |

The three materially distinct depth variants exhaust the prompt-only stop rule.
No candidate is promoted, no central prompt wording or ordering changes, and
Generation III remains on its accepted `identity_lock` fallback. A future
retry requires a changed control mechanism rather than more prompt emphasis.

### Discarded single-subject prompt retry

On 2026-07-29 the prompt-only question was reopened once as a deliberately
smaller diagnostic: one Mudkip, one forest clearing, 512 x 512 pixels, two
fixed seeds, and an otherwise identical one-shot FLUX.2 Klein graph on
Metal/MPS. A soft request to cross the rear-right area was avoided entirely.
A concrete request for one connected fern frond to cross a named outer tail
edge produced real foreground occlusion in both seeds, but one seed extended
the overlap too far toward the rear body. Abstract depth wording and explicit
contour/topology terminology produced unnatural dark connecting lines.

The useful local wording did not generalize to the real three-character
poster. With the original Generation III references, geometry, and seed held
fixed, both a short generic overlap rule and a conditional rule declaring
bottom-border vegetation as nearest foreground still allowed the connected
lower-right plant to pass behind Mudkip. The retry is therefore discarded:
its temporary workflows and renders are not retained, no production prompt or
artwork is changed, and `identity_lock` remains the Generation III fallback.
Further prompt-only depth variants stay closed.

### Silhouette-free zone-layout A/B

One bounded architecture A/B on 2026-07-29 tested whether the complete,
unoccluded character pixels in `joint_scene_cast_reference.png` were the
remaining structural depth bias. Candidate A reused the existing Generation
III `depth/original` result at seed `260750881`. Candidate B kept the model,
encoder, VAE, seed, 848 x 1168 empty target, four-step Euler sampler, CFG,
identity-reference bytes and order, normalized rectangles, Hoenn scene,
depth wording, and safe areas unchanged.

B replaced only the first image reference with a silhouette-free 608 x 832
occupancy map. It used the same neutral background as A and three identical,
softly feathered, low-contrast zones at the exact A character bounds. The
three IMAGE-role paragraphs were changed only as required to map Treecko,
Torchic, and Mudkip to the left, center, and right zones and to transfer pose
and orientation authority to their individual identity images.

| Gate | A: complete spatial cast | B: soft occupancy zones |
| --- | --- | --- |
| Count and coarse order | Pass | Three subjects in left/center/right order |
| Identity and anatomy | Pass within accepted one-shot tolerance | Hard fail: the right subject is a bipedal Torchic/Mudkip hybrid with missing Mudkip head fin, wrong limbs, colors, tail, and pose |
| Physical bottom-row cards | Pass | Hard fail: all three subjects are much too high and large; the real bottom-row crops contain only their lowest extremities or no subject |
| Visible control residue | None | No literal zone, box, outline, panel, or landing-pad leak |
| Foreground-depth evidence | Known lower-right contradiction behind Mudkip | Inconclusive: foreground plants avoid every subject silhouette |

Metal/MPS evidence:

| Artifact | Value |
| --- | --- |
| Runtime | `188.31 s` |
| A raw SHA-256 | `e8103fe2f8e7a1d426f9aa7f9e036251db41cdeb506af0b85c080b1d39083a5e` |
| B raw SHA-256 | `172cd2b6191bc7b34c0e2785ba4f45b66f739f712c2125cb6805dba096635603` |
| Zone-reference SHA-256 | `3f44d945163c37d59a35728580f8c270c2ad08e750a612405abb8555d08acef1` |
| B prompt SHA-256 | `ed3e64632deb02e3be7fbb3f42fdfe68828632a5364735f221130af733b2d51f` |
| B workflow SHA-256 | `b1a6e1222421acf58717e05d49bae1dbe557e1862994626dc5f468fb93c8fd17` |
| A/B graph hash after removing prompt, first reference path, and output prefix | `311fb13cfb1df6b91c2088df90e64c4ac5fcb0b9e89288982e446afe52e8ebbe` |

The result reproduces the earlier no-cast placement failure and additionally
breaks identity binding. Making the zones stronger, colored, labeled, or
hard-edged would test new leakage and panel biases rather than repair the
missing reference-to-region control. No second zone variant is justified.
The zone candidate and its temporary assets are discarded, the complete
spatial cast remains the `joint_scene` placement control, and Generation III
remains on its promoted `identity_lock` fallback.

### Cast-strength and regional-conditioning follow-up

On 2026-07-30 a local implementation audit established why the earlier
reference-image variants behaved this way. ComfyUI's `ReferenceLatent` appends
each complete VAE latent to one ordered list. FLUX.2 gives those references
separate sequence indices, but it provides no per-reference target rectangle,
mask, or strength. Prompt roles such as `IMAGE 1` and `IMAGE 2` are therefore
semantic conventions. The complete cast was the only strong placement signal,
and its fully visible subjects also encoded the unwanted visual prior that
every character lies in front of the complete landscape.

One isolated 50-percent-opacity cast A/B kept the original Generation III
prompt, seed `260750881`, graph, model, three identity-reference files, target
geometry, and sampler unchanged. It preserved count, identity, and card fit,
but nearby vegetation again avoided the subjects instead of proving a
foreground crossing. No opacity sweep followed.

The next bounded architecture removed the visible cast and bound each identity
reference through ComfyUI's regional conditioning while retaining one empty
latent, one four-step sampler trajectory, and one decode. A global,
reference-free branch generated the complete Hoenn landscape. Three additional
branches each received exactly one identity reference and were blended only
into the corresponding physical bottom card.

The first 0.25-MP variant used full-canvas branches plus soft masks. It failed
because FLUX still placed each complete subject semantically on the full
canvas; only the body part intersecting its mask survived. The single
diagnostically justified correction used
`ConditioningSetAreaPercentage` instead. Each subject branch then generated
its complete character, local ground, shadow, vegetation, and occlusion inside
the actual physical card region. No mask, box, silhouette, guide pixels, or
post-decode composite entered the graph.

| Candidate | Runtime on Metal/MPS | Raw SHA-256 | Workflow SHA-256 | Result |
| --- | ---: | --- | --- | --- |
| 50% spatial cast, 1 MP | `196.25 s` | `4ebcae043ffb2aead8cbd23e386c40ac5378168d5038337228f63f6cfe099ae2` | `d651828050d2b10abc334bfb7783f6b62ab8d26d4105cc6c23998a9957411878` | Count, identity, and fit pass; depth remains inconclusive; closed |
| Full-context regional masks, 0.25 MP | `169.67 s` | `25451dc72f5b3ed6c55b433f3b43070e950140d4ee13eb4cd3914cf93044ca3a` | `28d0a50398d7797038861280a9e3004f78616420f80a92dd779d196f2680d9b7` | Hard fail: only partial body fragments land inside the masks |
| Physical-card regional areas, 0.25 MP | `120.43 s` | `7aa3a1a4370867b06ef6e7d7ae42e84bf0237c0424aadf0f7592023898d3223c` | `513874c008320c3d144307d608e9480a46b8c22aad150121bc53ca7546d53746` | Coarse pass; earned one 1-MP confirmation |
| Physical-card regional areas, 1 MP | `123.75 s` | `d36592391d59af97a941bbe59c1f54f52a3448d3d97b8452fa2aba869a1e6051` | `6915e98ac26bdc979c42445334a4cc8d4063a5d410b85f871722c3a3e9109863` | Passes count, identity, anatomy, physical crops, padding, grounding, shadows, safe areas, and visible seam review |
| Pipeline-v6 CLI confirmation, 1 MP | `201.38 s` | `800d412c8711f2ae3e4de9afb15a7fcca7e5f08d1c26229142918d20450e25b0` | `6a2671fa3710c625f7240a874a494565518c509b2a2349803919acc1631666cd` | The production prepare → workflow → Metal/MPS sampling → 300-dpi finalization path passes internal preflight; generation fingerprint `78e67a9c93a2be5b5511ee39f5c076b7100602efd289cc49504c04aa4221b8e1` |

The 1-MP candidate contains complete Treecko, Torchic, and Mudkip in the
correct cards with no visible regional boundaries or pasted-layer appearance.
No connected plant changes arbitrarily from behind to in front. Vegetation
mostly avoids direct subject intersections, so this result removes the known
contradiction but does not yet prove reliable foreground occlusion across
different scenes. It is the leading Generation III depth-bias evaluation
candidate. The user approved it on 2026-07-30; it was then promoted
transactionally as the first `regional_identity_joint` pipeline-v6 asset with
the recorded raw, print, prompt, workflow, reference, and source hashes.

## Base1 / FLUX.2 Klein rollout

The first representative rollout of the promoted Generation VII graph keeps
the exact v5 `joint_scene` topology and changes only the scope inputs: seed
`260726503`, the Base Set scene brief, the reviewed Mewtwo/Bulbasaur/Charmander
sources, and their physical card placement. Candidate `00001` was reviewed and
promoted on 2026-07-29; the later prompt-only `00002` failure never changed the
production prompt or active candidate.

| Candidate | Pipeline change | Result | Decision |
| --- | --- | --- | --- |
| `joint_scene/00001` | Apply the reviewed `00018` graph to `Base1`, including the canonical placement profile and additional Mewtwo anatomy/padding constraints | All three subjects remain complete inside their physical cards with useful padding, coherent ground contact, and directionally consistent shadows. Mewtwo retains the defining head, hand, chest, and tail anatomy within the accepted one-shot detail tolerance. The landscape does not intersect a subject, so difficult foreground continuity remains unproven | Accepted and promoted on 2026-07-29 as the second `joint_scene` scope |
| `joint_scene/00002` | Keep the `00001` seed, model, graph, references, geometry, sampler, Mewtwo notes, one-shot paragraph, scene/depth paragraph, safe areas, and exclusions byte-identical; consolidate only repeated spatial, identity, count, and bounds prose | The intended three bottom subjects remain visible, but the model adds a fourth subject behind Bulbasaur: an oversized, upright, cat-eared Mewtwo-like mutation. This violates both exact count and identity before print processing | Rejected; no production prompt change |

The MPS render completed in 201.83 seconds. Reproducibility evidence:

| Artifact | SHA-256 |
| --- | --- |
| Raw 848 × 1168 candidate | `105efc287a5687bd028ec07bfa90ff516df434db3831c46fb47fbca81b041da2` |
| Text-free 2368 × 3268 print raster at 300 dpi | `dc5a1773c8f135d2f9b6adb9468cbda3a710bbbcc2936059cc5b29ca58fa08ea` |
| Effective prompt | `63f7b1a2a24c53f070446cf442161a6affcca6212c8276cf6603aff1e7b302ea` |
| ComfyUI API workflow | `890ff01dce52370b42c29d38e26407b522a9881c4c67e30315093e9349b51561` |

The complete generation fingerprint is:

```text
d26549018a20003c0cb961cb5ab76f256c76872114deff3d34db04a17d7ec70a
```

Promotion binds the raw and text-free print hashes above to an explicit
joint-scene visual review, nine 300-dpi physical card crops, and the stable
`poster-flux2*` PDF assets. A German test PDF with poster enabled rendered
successfully after promotion.

### Prompt complexity audit

The saved `00001` provenance snapshot contains 947 whitespace-delimited words,
6,340 bytes including its final newline, and 1,300 Qwen tokens. Its decorative
snapshot heading is not sent to the model. The actual workflow prompt contains
941 words, 6,299 bytes, and 1,286 tokens; the exact ComfyUI Klein chat template
raises the effective model input to 1,298 tokens. ComfyUI does not truncate this
input, but it is substantially above the nominal 512-token FLUX.2 conditioning
budget. The 512-token boundary falls inside the Mewtwo-specific paragraph; the
one-shot integration, depth, and safe-area rules follow later.

The length is not caused by one unavoidable requirement. The effective prompt
defines the spatial authority twice, the identity authority three times, and
repeats count, bounds, padding, and no-composite constraints in multiple
sections. Those repetitions can compete with the late scene and depth
instructions even though this particular render succeeds.

The reviewed candidate remains the immutable comparison baseline. The bounded
A/B was defined before changing any production prompt:

- Change only repeated spatial-authority, identity-authority, count, and bounds
  prose.
- Keep byte-identical: Mewtwo-specific anatomy and padding, the Base Set scene
  brief, single-pass synthesis, depth behavior, safe areas, and the concrete
  exclusion list.
- Do not target the earlier 510-token form. Candidate `00020` combined
  aggressive compression with a depth-rule change and failed the exact-count
  gate, so it cannot establish a safe minimal prompt.
- Use the same seed, model, references, geometry, and sampler. A compact form
  may replace the current wording only after side-by-side identity, card-fit,
  grounding, depth, and count review.

Candidate `00002` performs the conservative A/B with the exact same non-prompt
inputs as `00001`. It reduces the actual model prompt from 1,286 to 995 Qwen
tokens, or 22.6 percent; the complete chat-templated input falls from 1,298 to
1,007 tokens. Despite retaining every requirement class and leaving the
Mewtwo-specific, one-shot, scene/depth, safe-area, and exclusion paragraphs
unchanged, it repeats the same structural failure class as the earlier
aggressive `00020`: a duplicate fourth subject.

The MPS render completed in 205.29 seconds. Candidate evidence:

| Artifact | SHA-256 |
| --- | --- |
| Raw 848 × 1168 candidate | `c2797654d6eac5268b6c40503127cddcd5c6433a3625164b10df93b0caaf7934` |
| 995-token model prompt | `a3094cddb5ca1e768caca6e92c83b58816b89b2603e2a7dc689f464b6c980ec8` |
| ComfyUI API workflow | `dda583199798d5775fa93e086f33d04f72a3d10272940d42c1e5500be8e34c58` |

No print raster, overlays, or card slices were produced after the hard gate
failed. The exact `00001` prompt remains the Base1 comparison baseline. Prompt
deduplication is closed rather than followed by more near-identical variants:
for this four-reference conditioning topology, the apparently redundant count
and authority wording is behaviorally significant.

## ExGen3 Mega / FLUX.2 Klein rollout

The first `joint_scene` candidate uses seed `260751034`, the unchanged reviewed
prompt builder and graph, the highland-basin scene brief, and exact Official
Artwork form references for Mega Latias, Mega Diancie, and Mega Lucario.

| Candidate | Pipeline change | Result | Decision |
| --- | --- | --- | --- |
| `joint_scene/00001` | Apply the promoted v5 graph to the aggregate Mega section without subject-specific prompt exceptions | Exactly the three named Mega forms appear once. Their defining silhouettes, Mega-form appendages, crystal/ribbon structures, colors, markings, and poses remain within the accepted one-shot detail tolerance. All three physical card crops pass; the shared wall, terrain, lighting, and shadows are coherent | Accepted and promoted on 2026-07-29 as the third `joint_scene` scope |

The stone wall remains behind all three subjects and the nearest grass stays
clear of their defining silhouettes. The result contains no contradictory
depth transition, but it does not prove a connected natural foreground
intersection. As with the first two promotions, open terrain is accepted over a
forced or inconsistent crossing.

The MPS render completed in 197.38 seconds. Reproducibility evidence:

| Artifact | SHA-256 |
| --- | --- |
| Raw 848 × 1168 candidate | `7d3ecebc6e1eaec5a55869da011459265bae350ef3a94a191c7a77bf1ac4259b` |
| Text-free 2368 × 3268 print raster at 300 dpi | `65bfabaf28dc711a907f7b692a7d26f75d85076374e24ee31c0ebc6367167dd4` |
| Prompt snapshot | `62313ccf86f596d9871d23fcb7384d947eb2893318f3080333379adb38ec062f` |
| ComfyUI API workflow | `694105167526465b00b5d8eda10a29c6293b3d5b1b6d736a91bc74a274969d91` |

The complete generation fingerprint is:

```text
099b69bd95a6b6a16e1f57e941b136c69acef484c6db6bd077076314f9005216
```

## ExGen3 Normal / FLUX.2 Klein rollout

The representative proportional-diversity test uses seed `260711318`, the
unchanged v5 graph and prompt builder, the Paldea valley brief, and Koraidon,
Pikachu, and Miraidon. It deliberately combines two large complex bodies with
one small compact subject.

| Candidate | Pipeline change | Result | Decision |
| --- | --- | --- | --- |
| `joint_scene/00001` | Apply the promoted graph to the non-Mega ExGen3 section without subject-specific prompt exceptions | Exactly three subjects appear. Pikachu remains intentionally smaller while Koraidon and Miraidon retain their defining crests, segmented chest/body structures, limbs, tails, colors, and markings within the accepted print-detail tolerance. All physical card crops pass and the cast shares coherent light and shadows | Accepted and promoted on 2026-07-29 as the fourth `joint_scene` scope |

Foreground plants frame the outer card edges without producing a contradictory
intersection. As in the other accepted candidates, the result proves that the
graph can preserve very different proportions and card fill, but not that it
can reliably create connected natural foreground crossings.

The MPS render completed in 181.15 seconds. Reproducibility evidence:

| Artifact | SHA-256 |
| --- | --- |
| Raw 848 × 1168 candidate | `f53c44c20905886a95cd6a0a54a6731b6209bfd5f73bbb7c006382acd9206fae` |
| Text-free 2368 × 3268 print raster at 300 dpi | `5ed638ed90f00ca24120cbc6138bb20206e641f29ccec2ae92c241f1a4cf38b3` |
| Prompt snapshot | `29519877d8a1ac56f4994a156b74d2e8432fe3210945a6b1613e9df17d127aeb` |
| ComfyUI API workflow | `4988865cc16b8fe2530dc00e5863b5e95bdbb359523dc43e26cd776b157e7ec1` |

The complete generation fingerprint is:

```text
133603d3b0ed6ec6b8fea273ff74dfba1893b8112424099bea786d8ee5d69955
```

## Generation VII / FLUX.2 Klein

All candidates below use seed `260726054` and the `standard_3x3` layout. They
remain local review artifacts unless a later entry explicitly records
promotion.

| Candidate | Pipeline change | Result | Decision |
| --- | --- | --- | --- |
| `00003` | Early joint-scene experiment biased by a flat combined draft | Characters read as a layer placed over the landscape | Rejected |
| `00004` | Independent final latent with three identity references and one subject-free landscape reference | Strong identity and integration; Litten and Popplio crossed card boundaries | Rejected |
| `00005` | Smaller source figures inside the identity-reference canvases | Popplio gained an invented orange head detail | Rejected; source-detail reduction reverted |
| `00006` | Larger identity-reference canvases while retaining the landscape reference | Black output under unified-memory pressure | Rejected |
| `00007`–`00012` | Conservative normalized bounds and outward placement tuning | Card placement improved, but connected plants still switched inconsistently between foreground and background around Rowlet and Popplio | Rejected; landscape reference identified as the remaining structural bias |
| `00013` | Pipeline v3: one empty target, one sampler, three identity references, no landscape image | Coherent landscape depth; an over-specific generic prompt list invented a flame on Litten's tail | Rejected; feature-name list removed |
| `00014` | Reference-neutral identity wording | Coherent depth and faithful character designs | Rejected because all three characters extend above their bottom-row cards |
| `00015` | Same v3 graph with 768 px neutral identity canvases instead of 512 px | Placement remained too high and too large; render cost increased | Rejected; 512 px default restored |
| `00016` | Pipeline v4: replace the three global identity references with one neutral, poster-shaped cast layout containing the exact source figures inside their cards | All figures fit their real card crops with padding and the scene has coherent shadows/depth; Litten gains a large pale flank/hindquarter marking absent from the source | Rejected; third one-shot placement attempt fails identity and triggers the stop rule |
| `00017` | Pipeline v5: 0.5-MP spatial cast followed by three unscaled 512 px source-identity references before the same single sampler | All three subjects fit their cards and the scene contains no contradictory intersections, but plants avoid the silhouettes and therefore prove no real foreground crossing. Litten's front-paw digit structure is simplified, Popplio's eye and two muzzle strokes are reduced, and Rowlet lacks a convincing individual contact shadow | Retained as the second-ranked comparison after the identity tolerance was explicitly relaxed; placement is still too small and too far outward |
| `00018` | Reuse the exact canonical `identity_lock` placement profile; model, seed, scene wording, reference topology, identity images, and sampler remain fixed | All three subjects now have nearly the preferred card fill, remain complete inside their physical card crops, and receive clear directionally coherent grounding shadows. No gross identity regression beyond the accepted v5 print-detail tolerance is apparent. Plants again avoid the silhouettes, so true foreground continuity remains unproven | Accepted and promoted on 2026-07-29 as the first `joint_scene` default |
| `00019` | Add an explicit prompt-only stress rule requiring connected front and rear landscape crossings in every occupied bottom card; all non-prompt inputs remain byte-identical to `00018` | Card fit, accepted identity tolerance, and shadows still pass. Rowlet, Litten, and Popplio each have zero actual foreground crossings and zero connected rear elements visibly interrupted by the character. There is no contradictory z-order because the model avoids every requested intersection | Fails as depth evidence; `00018` remains the preferred v5 placement checkpoint |
| `00020` | Compact the effective prompt to 510 Qwen tokens including its chat template, move the depth rule to token 211, and request front/rear crossings in exactly one suitable bottom card; all image, model, geometry, seed, and sampling inputs remain fixed | The intended bottom cast stays recognizable, but the model renders a fourth character: a second, oversized Litten in the middle of the poster. No requested connected front/rear crossing is present | Rejected on hard character-count failure; prompt tuning closed and both experimental prompt changes reverted |

## Current checkpoint

The v3/v4 attempt budget is closed: `00014` and `00015` fail card containment;
`00016` passes containment by violating identity. The later v5
Spatial+Identity architecture is now the accepted default:

1. Create one empty 1-MP FLUX.2 target latent.
2. Condition it first with one neutral 0.5-MP poster-shaped cast reference as
   the sole authority for count, pose, scale, baseline, and card position.
3. Condition it next with one neutral 512 px identity reference per subject.
   Each contains the original 475 × 475 cutout without resampling and is the
   sole authority for anatomy, face, silhouette, colors, and markings.
4. Sample and decode exactly once.
5. Apply only deterministic Lanczos resizing and deterministic text/logo
   overlays after the text-free artwork review.

There is no pre-generated landscape reference, inpaint reference, second
sampler, final character composite, learned post-upscaler, or source-pixel
restoration in this mode. Candidate `00017` proves the v5 graph topology while
still redrawing print-scale facial and paw details. The product review on
2026-07-28 accepted those small simplifications for continued evaluation; a
changed defining feature, body-part count, silhouette, marking, or form still
fails. The later visual review on 2026-07-29 prefers `00018` over the composited
appearance of `identity_lock`. Candidate `00018` was then promoted with its
complete generation fingerprint and explicit raw/print visual approval.
`identity_lock` remains the exact-source fallback.

Candidate `00018` changes only the canonical spatial placement profile. It
delegates to the already accepted `identity_lock` placement helper instead of
maintaining separate shrink, lower-baseline, and outer-shift parameters. The
result passes physical card containment and preferred-fill review without a
new gross identity regression. Its raw SHA-256 is
`fc1375f75ef771d6f1aac05bcd27ef67288597bdf3dd8d2f4baf60a908db5e98`;
the MPS render completed in 180.43 seconds. Because no plant, leaf, flower, or
other connected landscape element actually crosses a subject, `00018` does
not prove foreground continuity. The subsequent `00019` candidate therefore
changes only the generic foreground-depth wording. It inherited neither
promotion nor approval from this placement result.

Candidate `00019` applies that isolated wording change. Its raw SHA-256 is
`2fa1b35df5f240e5396de7c8a3faeb3e41dcd516f86de6c7be8719de04b4832a`;
the MPS render completed in 180.20 seconds. Independent review confirms that
all three physical card crops retain the `00018` fit and accepted identity
tolerance, but not one requested front or rear crossing exists. A tokenizer
audit justified one final bounded retry: the actual
prompt contains 1,350 Qwen tokens and places the explicit stress rule after
token 1,034. ComfyUI does not truncate it, but the official FLUX.2
conditioning budget is 512 tokens.

Candidate `00020` performs that final bounded retry at 510 tokens, with the
depth rule at token 211. Its raw SHA-256 is
`610499556249a965cac52ea3ecea54fd206dd71487185fc967054282df31431c`;
the MPS render completed in 174.18 seconds. It does not produce a controlled
crossing and instead violates the hard count gate by adding a second, oversized
Litten above the intended bottom cast. The compact-prompt refactor and the
preceding stress wording are reverted in dedicated commits, returning the code
exactly to the `00018` prompt behavior. Prompt-only depth tuning is closed:
`00018` is the visually preferred candidate, `identity_lock` remains the
exact-source fallback, and any successor now requires a materially different
control mechanism.

### Anima empty-target preflight

The existing Anima adapter was evaluated without changing either FLUX.2
workflow. The Generation VII preflight uses the same seed `260726054`, reviewed
Rowlet/Litten/Popplio positions, and Alola brief at 432 × 592 px (0.25 MP).
`AnimaYume_tuned_v05`, `AnimaEditV1`, 22 `er_sde`/simple steps, CFG 3.4, and
Cosmos reference conditioning completed on Metal/MPS in 165.57 seconds. The raw
SHA-256 is
`a4ff08c593f385b8d37ce4c0311c36f152a3702efee591d028edcd207fd53922`.

All three subjects are complete and card-safe, but they remain visibly isolated
on a broad flat lawn. There are no convincing contact or cast shadows, local
terrain responses, foreground overlaps, or occlusions. The raw source audit
also records 1,680 changed pixels among 9,461 fully opaque reference pixels.
More importantly, the graph composites an eroded exact identity core back over
the decoded result. It therefore samples from an empty latent but is not a
single unified final synthesis under the joint-scene requirement. A 1-MP retry
cannot remove that structural limitation and is not justified. The adapter was
removed from the production runtime during the 2026-07-29 KISS cleanup;
its evidence remains here and in Git history. `00018` remains decisively
preferred.

## Identity-control successor evaluation

The earlier product decision on 2026-07-28 selected a materially stronger,
object-reference control mechanism without relaxing the then-current hard
gates. That successor search remains closed under its recorded results. The
later explicit review tolerance for v5 `00017` reopens only the FLUX.2
placement and occlusion questions described above; it does not reopen SDXL,
DreamO, Qwen, prompt-only identity tuning, or reference-canvas tuning.

### Frozen comparison fixture

| Input | Frozen value |
| --- | --- |
| Scope | `Pokedex/sections/gen7` |
| Layout | `standard_3x3` with the real physical card raster |
| Seed | `260726054` |
| Subjects | Reviewed Rowlet, Litten, and Popplio Official Artwork cutouts |
| Scene | Existing Alola scene brief from the promoted scope manifest |
| Target | One text-free joint scene; deterministic print resize and overlays remain outside model evaluation |
| Production effect | None until a candidate passes every hard gate and is promoted explicitly |

### Successor matrix

| Candidate family | Material change | Result or next gate |
| --- | --- | --- |
| `sdxl_identity` | SDXL plus one identity adapter per subject, regional masks, and source-derived structural control | Closed after whole-card, exact-silhouette, and tight-box masks all fail identity, grounding, and scene quality |
| `sdxl_identity_pokemon` | Same graph plus one Pokémon domain LoRA | Not rendered: the base graph fails reference binding and anatomy too broadly for a domain/style A/B to isolate |
| `ms_diffusion` | SDXL multi-subject adapter with explicit reference-to-box assignment | Stopped at technical preflight: the available ComfyUI port hides its own Diffusers sampler and requires a substantial MPS/audit refactor |
| `dreamo` | FLUX.1-dev plus three VAE-based DreamO object references before one common sampler | Closed after preflight B binds only two redesigned subjects, omits the third, and misses the fixed card bounds |
| `flux2_refcontrol` | FLUX.2 Klein 4B Base reference-plus-depth control | Stopped at contract preflight: one reference input cannot independently bind three subjects to three boxes |

The intended generic/Pokémon-assisted SDXL A/B was conditional on a viable base
graph. That condition is false, so no Pokémon LoRA is added to a broken
regional binding path. Every later family is evaluated as a new architecture
against the same frozen fixture and hard gates rather than compared as a
single-variable model swap.

### SDXL implementation checkpoint

The first isolated SDXL graph is implemented but not yet visually accepted or
connected to the production runner. It prepares a full-resolution
source-derived structure guide, one exact source identity image per Pokémon,
and initially one invisible regional mask per physical bottom-row card. The
generated ComfyUI graph contains one empty target, three region-bound
IP-Adapter conditions, one shared structural ControlNet condition, one
sampler, and one decode. It contains no background plate, image-to-image
target, inpaint stage, post-decode character composite, or source-pixel
restoration.

The generic graph and its optional Pokémon-LoRA variant differ only at the
single model-LoRA edge. The existing production engine registry, runner,
promotion, manifest, PDF routing, and promoted artwork remain unchanged.
All 163 poster-asset tests pass after this checkpoint. Visual identity,
containment, grounding, and occlusion remain untested until the first local
model render is recorded below.

### SDXL pre-render review checkpoint

A parallel KISS review verified the installed ComfyUI node schemas and found no
production-path changes, but identified that the initial graph reused an
834-word FLUX/Qwen prompt. SDXL's CLIP conditioning should not carry that much
duplicated geometry prose, because the regional masks and structural
ControlNet already own placement. The next workflow snapshot therefore uses a
dedicated 362-word SDXL prompt containing only the scene, named regional cast,
identity invariants, empty-target contract, coherent depth rule, safe areas,
and exclusions. Generic and Pokémon-assisted output prefixes are also explicit
so their artifacts cannot be confused.

The review deliberately leaves the full source-derived Canny guide and hard
per-card masks unchanged until candidate `sdxl_identity/00001` shows whether
they actually cause rigid cutout edges or vertical conditioning seams. These
are visual hypotheses, not reasons to add feathering or another control stage
preemptively. The complete repository test suite passes with 518 tests and one
expected skip.

The first runtime preflight used the 2.5-GB Xinsir Union-ControlNet on the
16-GB M4. ComfyUI remained on Metal and did not report an out-of-memory error
or CPU fallback, but completed only 5 of 30 sampler steps in 11 minutes 15
seconds, with the running estimate exceeding one hour. It was interrupted
before decode and produced no candidate image. This is an operational
rejection, not a visual identity result. The next graph replaces only that
oversized structural model with the official 545-MB FP16 SDXL Canny-mid
ControlNet. The source guide, regional identity adapters, empty target, seed,
resolution, sampler family, and one-pass contract remain unchanged.

### SDXL candidate record

| Candidate | Single changed variable | Runtime and automatic result | Visual result | Decision |
| --- | --- | --- | --- | --- |
| `sdxl_identity/00001` | Replace the rejected Union-ControlNet preflight with SDXL Canny-mid; the effective CLI strength is `0.72` | `253.74 s`; Metal/MPS; one empty target, sampler, and decode; no post-decode composite | Upper scene is a plausible Alola landscape, but the complete bottom row becomes a flat beige strip. All three Pokémon are tiny and visibly redesigned; Litten is severely malformed. No believable ground contact or scene integration remains | Rejected |
| `sdxl_identity/00002` | Keep the effective `00001` graph, including strength `0.72`, fixed and restrict each IP-Adapter mask from its complete card to the exact placed source silhouette | `255.50 s`; Metal/MPS; same one-pass graph and workflow bytes as `00001` | The beige bottom-row seam disappears, but the whole landscape collapses into blurred, segmented color fields. Rowlet is simplified, Litten becomes an unrecognizable red floating body, and Popplio's face and anatomy change. None has credible ground contact | Rejected |
| `sdxl_identity/00003` | Keep `00002` fixed and replace each sparse alpha mask with its tight, continuous visible-subject bounding box | `282.13 s`; Metal/MPS; same one-pass graph and workflow bytes | The scene remains blurred and heavily color-segmented. All subjects are undersized and floating; Rowlet and Popplio lose canonical details, while Litten remains unrecognizable | Rejected; close generic SDXL regional-mask family |

Candidate `00001` strongly indicates the pre-render review risk: a hard
whole-card identity mask does not merely bind a subject to a card. Together
with the neutral identity reference, it appears to condition the card
background itself and creates the exact horizontal seam at the top of the
bottom row. This points to a control-scope failure, not evidence that the scene
prompt needs more detail. The next attempt therefore changes only the masks.
It does not add feathering, another sampler, inpainting, source compositing, or
new prompt clauses.

The mask-only `00002` result confirms that the whole-card conditioning caused
the beige strip: changing only the three mask images removes that exact
boundary. It also shows that exact alpha silhouettes are too sparse for this
regional attention path. They do not retain canonical anatomy and destabilize
the global image despite unchanged structure, prompt, seed, model, and sampler.
This is still a control-scope failure; neither result justifies prompt tuning.
Candidate `00003` tests the simplest midpoint supported by the same node: one
continuous tight region around each visible subject. It adds no padding,
feathering, model, node, or sampler. If canonical identity still fails, the
generic SDXL regional architecture stops rather than adding mask heuristics.

`00003` fails that identity gate by a wide margin and does not recover the
scene. Whole-card, exact-silhouette, and tight-box regions are now three
materially distinct attempts with the same hard-gate failure. Further mask,
weight, prompt, or ControlNet-strength tuning on this generic SDXL regional
graph is closed. The planned public Pokémon-domain-LoRA A/B is not run on a
base graph that already fails subject binding, anatomy, global scene quality,
and ground contact; a domain/style prior cannot isolate which reference owns
which non-human body.

The `00001` snapshot also exposed a configuration drift: the Python workflow
default had already been changed to the Canny-mid recommendation `0.5`, while
the CLI parser still supplied `0.72`. The parser is corrected for future
experiments. Candidate `00002` explicitly keeps `0.72` so its direct comparison
with `00001` changes only the mask pixels; a later `0.5` run would be a
separate candidate.

The exact `00002` preparation command is:

```text
python scripts/poster_assets/create_sdxl_identity_poster_workflow.py \
  --scope Pokedex/sections/gen7 --seed 260726054 --megapixels 1.0 \
  --controlnet-strength 0.72
```

Its three subject-mask SHA-256 values are
`cdc1aeb492aeb5400a61cd4d15b1becb0f95108591127090b11db8620975fc9c`,
`c413d9a56dd33f9b80de3949859542603218013559a4edc6d178d1577c29060f`,
and `13b6fc73075878b81ee9d3125fce31ab6e780b8b8f2bee9aa71af78e9823cf0c`.
Both candidate workflow snapshots remain byte-identical at SHA-256
`5989dcfb41b0bd0dd92419ca0a84d35230bcc7e2484f7c5c7232c740f03d8556`;
only those three input images change.

The `00001` evidence is reproducible from:

- workflow SHA-256
  `5989dcfb41b0bd0dd92419ca0a84d35230bcc7e2484f7c5c7232c740f03d8556`;
- raw `848 × 1168` artwork SHA-256
  `f43d62a9f92fb0e9948399434f5710f46ab7cbfda2956848e1c2c43d23700c10`;
- deterministic `2368 × 3268` 300-dpi print resize SHA-256
  `03aa35e1c2d2a9d4cc62ba17317e4783a936653b714bc5df6c913448065b7439`;
- nine deterministic `750 × 1050` card crops below
  `data/poster_assets/Pokedex/sections/gen7/comfyui_poster/output/`
  `sdxl_identity_generic_00001_cards/`.

The local model fingerprint for this comparison is SDXL Base
`31e35c80…f7e5b`, CLIP Vision `6ca9667d…7b030`, IP-Adapter Plus SDXL
`3f5062b8…e6581`, and Canny-mid `15d4d3dd…b844fe`. The IP-Adapter custom node
is pinned to commit `b188a6cb39b512a9c6da7235b880af42c78ccd0d`. The
print artifact is a deterministic resize of the reviewed model output, not a
second generative or learned upscaling pass.

The rejected `00002` raw artwork SHA-256 is
`4d1172e6ec97e926236f689a7ef8fc97bee58186b69be331b80df29067209d2a`.
Its deterministic 300-dpi print resize is
`f76125b162d984535f082c35a74fcb4835ab228ddf84f7a88f2593e14ed8ba4a`;
the nine review crops are below
`data/poster_assets/Pokedex/sections/gen7/comfyui_poster/output/`
`sdxl_identity_generic_00002_cards/`.

The rejected `00003` evidence uses the unchanged workflow SHA-256
`5989dcfb41b0bd0dd92419ca0a84d35230bcc7e2484f7c5c7232c740f03d8556`
and subject-region SHA-256 values
`b951b8d0fa4e7317001e59940b6a2be383e5163eba4fea847d18f3364d0091fe`,
`6910097bc0962463dc8776cfb1be5fbaf8b0ebf8386a81b6a8501322db4fa08f`,
and `c582e3672cc9fbe718b3240ead67be26a5cbcf6346bdda51c9efc039a3f39b8a`.
Its raw artwork SHA-256 is
`a3b14362bebf378b182d50606e98f02942e975816cd7f9c8dbba68a5d705ed43`;
the deterministic 300-dpi print resize is
`221d071df8027ccb80bd0005f0e09e36e9d890f8635560ecac3dcee3ce2a3144`.
The nine review crops are below
`data/poster_assets/Pokedex/sections/gen7/comfyui_poster/output/`
`sdxl_identity_generic_00003_cards/`.

### Successor technical preflight

The next architecture review starts before downloading another multi-gigabyte
model. [MS-Diffusion](https://github.com/MS-Diffusion/MS-Diffusion) is
conceptually attractive because it assigns multiple image references to
explicit target boxes. The reviewed
[ComfyUI port](https://github.com/smthemex/ComfyUI_MS_Diffusion) at commit
`a5b97bb7cea2ad31d471ed51bb54f210a183ea82` does not expose that mechanism as a
normal Comfy model condition, however. Its loader constructs a complete
Diffusers `StableDiffusionXLPipeline`, unconditionally enables xFormers, and
contains CUDA-only cache calls. Its sampler performs diffusion internally and
returns an `IMAGE`, so the repository cannot statically verify one shared empty
target, one final sampler, and one decode.

Removing those assumptions and converting the hidden pipeline into auditable
Comfy model/conditioning nodes would be a substantial fork. That contradicts
the KISS boundary selected for this experiment, so `ms_diffusion` stops at
technical preflight without installing its adapter or rendering a candidate.
This is an integration rejection of the available port, not evidence against
the published architecture itself.

[DreamO v1.1](https://github.com/bytedance/DreamO) is selected next. The
reviewed
[native ComfyUI integration](https://github.com/ToTheBeginning/ComfyUI-DreamO)
at commit `622f393a13b9e083ab3945d7534b8b3fe38d609e` exposes three optional
reference latents, applies them to a normal FLUX model, and leaves the final
sampling and decode visible in the graph. The upstream project documents
Apple M1-M4/MPS operation and object/animal identity conditioning. The first
candidate therefore has this fixed contract:

1. three separate reviewed Official Artwork references, in left-to-right card
   order;
2. one empty target at the existing Generation VII fixture geometry;
3. one shared scene prompt and one final sampler/decode;
4. no target image encoding, inpainting, character composite, source-pixel
   restoration, or second generative pass;
5. a low-resolution MPS technical preflight before a 1-MP visual candidate;
6. at most one higher-reference-resolution follow-up, and only when the first
   result already passes count, binding, coarse anatomy, and placement.

DreamO is still an experiment, not a new production engine. Its lack of an
explicit three-box input is a known risk: natural-language left/center/right
placement must pass the unchanged physical card-containment gate before any
identity-detail tuning is justified. The accepted `identity_lock` artwork,
manifests, PDF routing, and release inputs remain unchanged.

#### DreamO installation and MPS preflight A

The local installation is pinned rather than following moving upstream heads:
ComfyUI `87d23b81765161624889febfb3b81f19f3c8435b`,
ComfyUI-GGUF `6ea2651e7df66d7585f6ffee804b20e92fb38b8a`,
ComfyUI-DreamO `622f393a13b9e083ab3945d7534b8b3fe38d609e`, and the
DreamO facexlib fork
`5e6c76170f8a9f9c5b4df62d8679f4f769230383`. The graph uses
FLUX.1-dev Q4_K_S
`75bb19459b5240c9f373b5af527584af15b675867fa142efadf7478d6abbf62b`,
then the official v1.1 LoRA chain:

| Model | SHA-256 |
| --- | --- |
| FLUX Turbo | `77f7523a5e9c3da6cfc730c6b07461129fa52997ea06168e9ed5312228aa0bff` |
| DreamO base | `27f01aed81d0c6d4549309ec5ca0d5c96eef6f76cb47bdb370645780f304b90a` |
| DreamO CFG distill | `dc7cb5b503829ab6ab765cf07abf972cef65d5c11bd04de1d17f1f4f0fae2c80` |
| DreamO SFT | `596ce2e45175b07553c7f7051ced1ae940ec2860258e9232385974504f056c54` |
| DreamO DPO | `e66b08922bbfdb0eb15e790160c2709ba5693c1ee59808e48e5cbb9d0d467551` |

The closed SDXL experiment's base checkpoint, CLIP Vision, IP-Adapter, and two
ControlNets were hash-checked against their existing log before deletion.
Their recorded total is 13,371,197,431 bytes (about 12.45 GiB); no production
model is touched.

The first unchanged 0.25-MP graph reached the sampler only after a bounded
compatibility patch forwarded ComfyUI's new `latent_shapes` keyword through
DreamO's outer sampler wrapper. No model logic, conditioning, or sampler
parameter changed. It then completed on Metal/MPS in 11:34 with 12 Euler/simple
steps, CFG 1, guidance 4.5, one empty 432×592 target, one sampler, and one
decode. Workflow SHA-256 before the prompt diagnostic was
`beb2349e78b18ee215ba2d948aa9d849a3aa95f97dbbeb08991a90cd6f236860`.

The raw preflight image SHA-256 is
`46d8020099dff811ce0ade71c8eed3873c5d927bf4f04bdcce3e9f500893dffa`.
It renders a coherent Alola landscape but omits Rowlet, Litten, and Popplio
entirely, so it is not candidate `dreamo/00001` and no upscale, card crops, or
promotion evidence is produced. A cheap diagnostic saved DreamO's own
post-BEN2 reference outputs; all three remain complete and recognizable. The
binding failure is therefore downstream of reference preparation.

The only next variable is prompt conditioning. The preflight prompt contained
765 T5 tokens, beyond the tokenizer's declared 512-token envelope, while the
first pooled 77-token CLIP chunk contained scenery but none of the Pokémon.
The compact replacement puts all three reference/name/card assignments in
that first CLIP chunk and measures 501 T5 tokens for this scope. Its workflow
SHA-256 is
`ab0781ac2b47f8ab2a1e377255ccf8cdb74a3533e1acf1d8eee7c292c4a2bb51`.
The same seed, resolution, references, model chain, sampler, and scene contract
remain fixed for preflight B. Only if subjects appear does DreamO earn a 1-MP
visual candidate.

Preflight B completed on Metal/MPS in 10:11. Its raw output SHA-256 is
`6e027309f1e46bce0b21c40a1fc7d79bf12e00b5bca60dc34c51a5146ad8abb1`.
The compact prompt changes binding, proving that the first result was not
solely an empty-reference failure: Rowlet and Litten now appear. Both are
substantially redesigned, oversized, and outside their target silhouettes;
Popplio is absent. Rowlet gains a costume-like head outline and altered body,
while Litten gains a white chest/muzzle design and altered markings and
proportions. Count, identity/anatomy, and card containment therefore all fail
before detailed grounding review.

DreamO receives no 1-MP candidate. Raising resolution cannot supply the missing
explicit reference-to-box control, and it is not justified while coarse count,
identity, and placement already fail. Adding masks, per-subject passes, or a
post-decode restoration would reintroduce the layered architecture this
experiment is intended to replace. The pinned graph and prompt builder remain
available as reproducible negative evidence, but `identity_lock` remains the
production engine.

#### Selected Qwen spatial-subject preflight

No new model is downloaded for the next bounded experiment. The existing
Qwen-Image-Edit-2511 candidate had a concrete input-topology defect: its first
image already contained all three positioned subjects, then Mewtwo appeared
again on one detail sheet while Bulbasaur and Charmander appeared again on a
second sheet. The model therefore saw the same cast both as composition and as
additional image content. Its giant fourth Mewtwo is consistent with that
ambiguity and does not isolate Qwen's actual three-subject binding ability.

The replacement changes only that topology:

1. exactly three poster-shaped neutral reference images are supplied;
2. each image contains exactly one reviewed source subject, once, at that
   subject's normalized final bottom-card position and scale;
3. no subject appears in any other input image;
4. one empty target, one common sampler, and one decode generate the complete
   landscape and cast together;
5. there is no background plate, structure image, inpaint target, mask,
   post-decode composite, source restoration, or second generative pass.

This is an isolated `qwen_spatial_subjects` preflight, not a production-engine
change. The accepted artwork, manifest, PDF routing, and promotion state remain
untouched. It reuses the already installed Qwen model, encoder, VAE, Lightning
LoRA, fixed Generation VII seed `260726054`, and existing physical placement
geometry.

The stop rule is deliberately cheaper than another tuning branch. First run
one 0.25-MP Metal/MPS binding preflight. Stop immediately on CPU fallback,
memory failure, a missing or duplicate subject, a subject assigned to the
wrong card, or gross anatomy change. Only a preflight that binds all three
distinct subjects to the correct cards earns exactly one 1-MP candidate. A
second 1-MP run is allowed only for a genuine near-pass that already satisfies
count, placement, depth, and coarse anatomy; its sole changed variable may be
the official native non-Lightning sampling preset. Any remaining anatomy
change closes this Qwen topology.

The preparation checkpoint implements that graph without changing the existing
`qwen_edit` runner or its promotion semantics. That separation is intentional:
the current runner treats Qwen as an exact-source edit, while this experiment
is a complete unified redraw and must not inherit or weaken that source-pixel
gate before it proves useful. All three opaque references use the canonical
`848 × 1168` 1-MP poster canvas even for the 0.25-MP target. Qwen normalizes
every reference to roughly 1 MP internally, so preparing a smaller reference
would discard identity detail without reducing that conditioning cost.

The prepared Generation VII evidence is:

| Input | SHA-256 |
| --- | --- |
| Rowlet spatial reference | `bb9f28900c1d91639744c4de3c61570932d9c2201697906414416381ff9cd3f1` |
| Litten spatial reference | `0b6ca1efa05c4d6421a9d361212a74edca899075c4075322c4331ae251d37733` |
| Popplio spatial reference | `11d6a6936532509b40c37530e86e768504f3b8ccc97f3d79e2b43bb6decc9010` |
| Dynamic prompt snapshot | `948e45849b8f9369a0ffc1e55513772fdd0b82b7f6b835ceac3ca09e0ecbdc32` |
| 0.25-MP API workflow | `c0aa0af2322fa1acb11f07966f7c292edbd30ebc924e3c29a4555514cd762ce8` |

The installed model contract is Qwen-Image-Edit-2511 Q3_K_M
`5631fd3a…4e9e9`, Qwen 2.5 VL 7B FP8 `cb5636d8…5c0b4`, Qwen image VAE
`a70580f0…23d1f`, and the four-step Lightning LoRA `22226e8d…a904f`.
Automated tests compare every reference pixel against exactly one expected
source placement, verify the prompt's picture/name/card order and normalized
bounds, and reject any graph containing a source VAE target, inpaint, control,
or composite node. The new focused tests and the existing poster workflow,
generation-option, and provenance suites pass together with 230 tests. The
complete repository suite passes with 536 tests and one expected skip.

The 0.25-MP preflight completed on Metal/MPS with `--lowvram` in 14:38;
four Euler/simple sampling steps took 12:45. The Qwen text encoder, VAE, and
GGUF denoiser all reported MPS loading, while macOS swap reached approximately
15.4 GiB. The resulting `432 × 592` raw image has SHA-256
`d97a81d346dd3ff07f8fa0f2d79dbd0c7987fdb0f30f8688550db932b793b797`.

The result retains the plain neutral reference field, renders one oversized
Litten across almost the complete poster, omits Rowlet and Popplio, and creates
no Alola landscape. Litten remains broadly recognizable, but count, distinct
reference binding, target scale, card containment, final-scene synthesis, and
set-specific scenery all fail at the cheapest gate. Because several coarse
hard gates fail simultaneously, neither a 1-MP run nor a prompt/sampling
follow-up is justified. The isolated topology is closed and retained only as
reproducible evidence. It did not change the then-current `identity_lock`
artwork and does not belong to the later `joint_scene` production runtime.

## Regional-v6 representative rerender audit

After Generation III regional-v6 passed visual review, every existing
spatial-v5 promotion received one 1-MP Metal/MPS candidate with the same model,
prompt builder, physical placement contract, scope seed, four-step sampler, and
empty-target topology. No candidate replaced its existing promotion.

| Scope | Candidate result | Decision |
| --- | --- | --- |
| `Base1` | Mewtwo and Bulbasaur remain close, but Charmander changes pose and detail; a generated edge frame and pseudo-signature are visible | Rejected; one new-seed retry also creates a separate lower panorama and frame |
| `ExGen3/sections/normal` | Scene integration is strong, but Miraidon's defining open tail becomes a compact loop and Koraidon loses hand detail | Rejected on anatomy |
| `ExGen3/sections/mega` | Mega Latias is cropped; Mega Lucario's chest spike and foot anatomy are malformed | Rejected on containment and anatomy |
| `Pokedex/sections/gen1` | Count, identity, card fit, shadows, and local depth pass, but a generated paper/frame strip survives into the cards | Rejected; the single seed retry creates a second lower landscape and frame |
| `Pokedex/sections/gen2` | Count, identity, card fit, and grounding pass, but a generated outer frame is visible | Rejected; the single retry splits the lower row into three framed landscapes and changes Cyndaquil/Totodile details |
| `Pokedex/sections/gen7` | Rowlet, Litten, and Popplio are highly faithful and card-safe, but a second tropical lagoon begins below a full-width horizontal scene boundary | Rejected on global perspective |

The failures exposed a deterministic topology risk. Every local branch owns a
complete bottom-card `ConditioningSetAreaPercentage`. The subsequent
`ConditioningSetDefaultCombine` marks the reference-free landscape as a
default, and ComfyUI subtracts the local multipliers from that default. The
global scene therefore has zero weight throughout the interiors of the lower
cards; the local branches independently predict their own terrain, horizon,
and foreground. Edge feathering hides some boundaries but cannot share scene
geometry.

Two same-seed Generation-I KISS tests changed only that combine behavior:

| Test | Effective regional/global mix | Result | Decision |
| --- | --- | --- | --- |
| Ordinary additive `ConditioningCombine`, strength `1.0` | 50/50 inside each subject card | One continuous landscape, but all subjects become underconditioned; Charmander turns around and defining colors/anatomy collapse | Rejected |
| Same additive graph, local strength `2.0` | 2:1 regional/global | More subject color returns, but pose/anatomy remain wrong and a lower panorama begins to reappear | Rejected; stop strength tuning |

ComfyUI computes the additive result per latent pixel as
`sum(output * strength) / sum(strength)`. Higher local strength would approach
the original independent-card behavior; lower strength already fails identity.
The additive experiment and its tests were reverted, leaving production code
byte-equivalent to regional-v6 before this audit.

Outcome:

- Generation III keeps its explicitly reviewed regional-v6 promotion.
- All six spatial-v5 promotions remain unchanged and approved.
- No rerender receives a new approval.
- Further regional-v6 seed, prompt, or strength sweeps are closed.
- A successor must bind each identity and position while retaining one shared
  full-frame scene prediction inside the subject zones; that is a new control
  mechanism, not prompt tuning.

## Individual spatial-reference successor preflight

The next bounded experiment removes both known sources of conflicting scene
geometry: the combined three-character cast image from spatial v5 and the
per-card conditioning branches from regional v6. Each subject instead receives
one neutral, poster-shaped reference containing only its supplied source
cutout at the canonical final position. All references condition one shared
text prompt and one empty full-frame FLUX.2 target through a single sampler and
decode. There are no area conditions, masks, inpainting, decoded composites, or
post-generation source restoration.

The model, encoder, VAE, four-step sampler, Generation-I seed `260782266`,
prompt contract, and physical placement profile remained fixed. The experiment
uses `flux-2-klein-4b-fp8.safetensors`
(`97ed34fe0567e436200f2faee3939b88f2b5d99f8af2a4dc16532c4245c0ccb6`),
`qwen_3_4b.safetensors`
(`6c671498573ac2f7a5501502ccce8d2b08ea6ca2f661c458e708f36b36edfc5a`),
and `flux2-vae.safetensors`
(`d64f3a68e1cc4f9f4e29b6e0da38a0204fe9a49f2d4053f0ec1fa1ca02f9c4b5`).
Every render ran on Metal/MPS.

| Attempt | Isolated change | Result | Decision |
| --- | --- | --- | --- |
| Six references, 0.25 MP | Three 0.25-MP poster-position references plus three separate 0.25-MP identity-detail references | The `432 × 592` render completes in `195.95 s` but contains five creatures: the intended three plus an extra green biped and a second Charmander. Raw SHA-256: `ab451373bd2a2d109a9b7391e76c958eb3ef877ad10ebe55eed02d11711df495` | Hard count failure. Commit `131d0ae` retains the reproducible topology; no larger render |
| Three references, 0.25 MP | Remove the duplicate detail channel and give each subject one 0.5-MP identity-and-position reference | Exactly Bulbasaur, Charmander, and Squirtle appear once in the correct bottom cards. The landscape, contact shadows, and foreground/rear vegetation are continuous. Runtime `150.96 s`; workflow SHA-256 `e09b231268f64c1068e7ecf38338a9bd5d2e91e10adb7cd3a7012a8a65aa4f32`; raw SHA-256 `7323d0d490ea787971c6eeb9569230349a46ea6d009865b2c938b182dfedc746` | Coarse gate passes and earns one 1-MP confirmation |
| Three references, 1 MP | Keep the successful topology, seed, prompt, reference resolution, model, and sampler unchanged; enlarge only the empty target to `848 × 1168` | Exactly three recognizable starters remain complete with useful card padding. Defining anatomy, markings, poses, and silhouettes remain within the current one-shot tolerance. Foreground blades overlap Bulbasaur and Squirtle while separate rear vegetation remains behind them; shadows and terrain are jointly synthesized. Runtime `206.38 s`; workflow SHA-256 `a09f52d73f44b7a70654c6f96d37d24cf31805c108f14a9ef97427415382b182`; raw SHA-256 `cf80fd3f0a2f909bb1d58ecc7f43c015431e074ff25adb86fdf4bdee785642ae` | Agent preflight passes; user review and representative-scope validation remain required before production integration |

The three successful 0.5-MP references have SHA-256 values
`b589d1e80fb63ba393a5f7de3bd996c211f1d2bd8d6a4d121f65a8f459236c5d`,
`ebef71bdc22632759f9e5752e30d43d5850522b544a25b5372b9eeec25e4a921`,
and `1ce381cbdcb3c6a2d1e39d088472881d2c491aa9d3b1146f3c275bc1c816d5c5`.
They are deterministic derivatives of the tracked source cutouts and canonical
placement profile, so they remain ignored scratch files.

This is positive evidence for the materially different control mechanism
required by the regional-v6 audit, not yet a new default. Spatial v5 remains
the production default and Generation III remains the sole regional-v6
promotion. If the Generation-I candidate passes user review, the next bounded
validation is the unchanged topology on Generation VII (known depth stress)
and Base1 (Mewtwo anatomy stress). Production integration is justified only if
both preserve count, identity, card containment, and one global scene.

### Review record template

Every rendered candidate appends one row containing the exact workflow and
model hashes, raw and deterministic print-size artifact paths, runtime, and
the following result:

| Gate | Automatic evidence | Mandatory visual evidence |
| --- | --- | --- |
| Joint final scene | Empty target, one final sampler/decode, and no post-decode source composite or restoration | The output does not read as separate pasted layers |
| Identity and anatomy | Exact source hashes and one explicit reference input per subject; record any architecture-specific spatial binding or control | Whole-poster and individual bottom-card comparison against all three supplied cutouts |
| Card containment | Any supplied mask or structural guide remains inside its physical card envelope; all candidates produce the exact nine shared-geometry crops | Every generated silhouette and appendage remains inside its real bottom-card crop with visible padding |
| Coherent depth | The workflow and prompt expose one common scene-depth contract | Contact shadows and every connected landscape/character intersection remain physically consistent |
| Set scene and safe areas | Title and information cells are derived from the shared physical geometry | Whole-poster review before deterministic logo and text overlays |
| Print output | Deterministic Lanczos output has the exact configured 300-dpi dimensions and nine expected crop dimensions | Raw and print-size crops retain the reviewed small identity details |

Geometric crop validation cannot prove that a probabilistically generated
character stayed inside its crop. Similarity, segmentation, CLIP, or DINO
scores may help reject obvious failures but cannot approve anatomy,
containment, grounding, or occlusion.

An architecture stops after three materially distinct attempts at the same
failed hard gate. A domain or training adapter is tested only after the base
graph demonstrates correct per-subject binding, and is retained only when a
controlled A/B improves identity without introducing a new hard-gate
regression.
