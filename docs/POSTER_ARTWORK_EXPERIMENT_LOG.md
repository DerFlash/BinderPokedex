# Poster artwork experiment log

This log records local visual experiments that are intentionally not promoted.
It complements the requirements and status documents with a short history of
what was actually rendered, why it was accepted or rejected, and which single
variable changed between useful checkpoints.

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
| `00017` | Pipeline v5: 0.5-MP spatial cast followed by three unscaled 512 px source-identity references before the same single sampler | All three subjects fit their cards; depth, Litten/Popplio ground contact, and landscape intersections are coherent. Litten's front-paw digit structure is simplified, Popplio's eye and two muzzle strokes are reduced, and Rowlet lacks a convincing individual contact shadow | Rejected; spatial contract passes, but the non-negotiable identity gate fails |

## Current checkpoint

The v3/v4 attempt budget is closed: `00014` and `00015` fail card containment;
`00016` passes containment by violating identity. No Generation VII one-shot
candidate is promoted.

An explicit product decision now authorizes one materially different v5
Spatial+Identity architecture:

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
restoration in this mode. Candidate `00017` proves that graph contract v5 solves
the spatial and scene-integration failures, but it still redraws identity-scale
facial and paw details. Because the identity references already contain the
unscaled source pixels, no second canvas/prompt parameter retry is justified.
The implementation remains selectable and unpromoted; production stays on
`identity_lock` until the product chooses which conflicting invariant may
change or a materially stronger identity-control mechanism becomes available.

## Identity-control successor evaluation

The product decision on 2026-07-28 selects a materially stronger,
object-reference control mechanism without relaxing the existing hard gates.
This is a new architecture family, so it starts a new attempt budget. It does
not reopen prompt-only or reference-canvas tuning for the rejected FLUX.2
`joint_scene` v3-v5 graphs.

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

### Planned single-variable matrix

| Candidate family | Material change | Purpose |
| --- | --- | --- |
| `sdxl_identity` | SDXL plus one identity adapter per subject, regional masks, and source-derived structural control | Test explicit reference-to-region and geometry binding in one final scene pass |
| `sdxl_identity_pokemon` | Same graph, inputs, seed, and controls; add one Pokémon domain LoRA | Measure whether Pokémon domain knowledge improves small canonical details without weakening placement or scene depth |
| `flux2_refcontrol` | FLUX.2 Klein 4B Base reference-plus-depth control | Test the smallest compatible stronger-control option in the existing FLUX ecosystem; stop before rendering if its reference contract cannot bind three distinct subjects safely |

The generic and Pokémon-assisted SDXL candidates are a strict A/B pair. Model
choice is the only intended variable; scene wording, target geometry,
references, masks, structural guide, seed, sampler settings, and output size
must remain identical. The FLUX.2 RefControl candidate is evaluated separately
because it uses a different control contract.

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

### Review record template

Every rendered candidate appends one row containing the exact workflow and
model hashes, raw and deterministic print-size artifact paths, runtime, and
the following result:

| Gate | Automatic evidence | Mandatory visual evidence |
| --- | --- | --- |
| Joint final scene | Empty target, one final sampler/decode, and no post-decode source composite or restoration | The output does not read as separate pasted layers |
| Identity and anatomy | Exact source hashes and one explicit reference-to-region binding per subject | Whole-poster and individual bottom-card comparison against all three supplied cutouts |
| Card containment | Every input mask and structural guide remains inside its physical card envelope; the nine output crops use the exact shared geometry | Every generated silhouette and appendage remains inside its real bottom-card crop with visible padding |
| Coherent depth | The workflow and prompt expose one common scene-depth contract | Contact shadows and every connected landscape/character intersection remain physically consistent |
| Set scene and safe areas | Title and information cells are derived from the shared physical geometry | Whole-poster review before deterministic logo and text overlays |
| Print output | Deterministic Lanczos output has the exact configured 300-dpi dimensions and nine expected crop dimensions | Raw and print-size crops retain the reviewed small identity details |

Geometric crop validation cannot prove that a probabilistically generated
character stayed inside its crop. Similarity, segmentation, CLIP, or DINO
scores may help reject obvious failures but cannot approve anatomy,
containment, grounding, or occlusion.

An architecture stops after three materially distinct attempts at the same
failed hard gate. A Pokémon LoRA is retained only when the controlled A/B
comparison improves identity without introducing a new hard-gate regression.
