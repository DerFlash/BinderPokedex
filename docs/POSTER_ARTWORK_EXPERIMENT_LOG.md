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
| `00017` | Pipeline v5: 0.5-MP spatial cast followed by three unscaled 512 px source-identity references before the same single sampler | All three subjects fit their cards; depth, Litten/Popplio ground contact, and landscape intersections are coherent. Litten's front-paw digit structure is simplified, Popplio's eye and two muzzle strokes are reduced, and Rowlet lacks a convincing individual contact shadow | Retained as the second-ranked comparison after the identity tolerance was explicitly relaxed; placement is still too small and too far outward |

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
The product review on 2026-07-28 keeps `identity_lock` unchanged in first place
and reclassifies v5 `00017` as the second-ranked experimental comparison. Its
small front-paw and face-line simplifications are acceptable for continued
evaluation, but a changed defining feature, body-part count, silhouette,
marking, or form still fails. The next v5 candidate changes only the canonical
spatial placement profile: center the outer subjects, enlarge all three toward
the preferred card fill, and keep conservative card padding. It does not alter
the model, seed, scene prompt, reference topology, identity images, sampler, or
one-pass contract. Foreground/background crossings remain a separate review
question and receive their own later prompt-only test only if the placement
candidate contains no meaningful intersection.

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
reproducible evidence; the production `identity_lock` artwork remains
unchanged.

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
