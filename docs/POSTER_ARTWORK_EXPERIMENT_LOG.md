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

## Current checkpoint

Pipeline v3 is deliberately small:

1. Create one empty FLUX.2 target latent.
2. Condition it with one appearance reference per character and the complete
   dynamic scene/placement prompt.
3. Sample and decode exactly once.
4. Apply only deterministic Lanczos resizing and deterministic text/logo
   overlays after the text-free artwork review.

There is no pre-generated landscape reference, inpaint reference, final
character composite, learned post-upscaler, or source-pixel restoration in this
mode. The visual depth problem is resolved in `00014`, but exact card-safe
placement remains open. No Generation VII one-shot candidate is promoted at
this checkpoint.

The next experiment must change only one placement-control mechanism and must
retain the one-shot final sampler. Its result is reviewed first as raw artwork
and then as three independent bottom-row card crops. `00014` and `00015` count
as two failed one-shot placement attempts under the decision rule in
`POSTER_ARTWORK_REQUIREMENTS.md`; one materially distinct KISS placement
experiment remains before the card-containment tradeoff must be brought back
for an explicit product decision.
