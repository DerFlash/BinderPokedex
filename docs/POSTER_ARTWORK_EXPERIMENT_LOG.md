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
