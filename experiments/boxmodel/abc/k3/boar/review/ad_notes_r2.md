# Art-direction notes, repair round 2 (reconciled, K=2)

Scores (Fable 5.1 / Opus 5.5): 7 FIX / 6 FIX.

**Stage 1 is locked. No unlock is authorised for this pass.** Every fix below is a stage-2, stage-3 or stage-4 change. Stage-2 IoU against stage 1 must stay above 0.9 in every view; stage 3 never edits the base; all gates pass.

Keep what works (round 1 fixed these; do not regress):
- Front-heavy hump, low wedge head, flat pink snout disc with two round flush nostrils (az000).
- Crest is one ridge of blunt, combed-back tufts, no needle tips (r10-r12).
- Tail with section and a blunt dark tuft (az090, back34).
- Eyes visible at thumbnail size with a slight brow (az000).
- Hock angles and the trot; clean tech, clip 0, stretch 0.

Fix the must-fix list in order, then the should-fix items if turns allow. Check every item in your own `--review` packet before you call it done.

## Must-fix, in order

0. **Kit gates.** No FAIL on the current kit; clip_area_pct 0.0, stretch 0. Nothing to do; keep it that way.

1. **Shoulder saddle is still a hard dark block (O major; round 1 item 2 partly done).**
   - Where: 1_beauty hero: a dark vertical rectangle on the shoulder with straight edges; az090: a dark parallelogram under the crest with a straight lower edge and a vertical back edge at mid-back; 5_reference model top: a dark rectangle on the back. 5_reference side and top: the dark is a mantle along the spine that frays into the brown, widest at the nape, narrowing to a point at mid-back.
   - Fix: Stage 3 (paint only): make the `bristle` region taper: at the nape it reaches down to about 30% of the hump height below the spine; at the withers 20%; from mid-back on only the spine faces (|n.x| < 0.35, n.z > 0.6). Drop the "upper flank between the neck loop and the raked edge" band from r13, which is the rectangle. Use per-face tests on face centre z relative to the local spine height, so the lower border steps along existing edges and slants back, not a straight horizontal line. Keep the border on edges, never across a face.
   - Check: 1_beauty az090 and hero: no vertical dark edge on the flank; the dark narrows from nape to mid-back; 5_reference top: a dark wedge along the spine, not a box. Colour count unchanged.

2. **Tusks stand off the cheek like horns (O major, F major).**
   - Where: 1_beauty hero and az000; 2_closeups head colour: each tusk starts on the side of the snout above the lip line and points up as a separate horn, short, low contrast against the pale snout. 5_reference front and side: the tusk comes out of the lower lip corner just behind the snout disc, curves out then up, and its tip clears the top of the snout.
   - Fix: Stage 3: move the tusk root down to the lower jaw corner, about 15% of head length behind the snout disc and at the mouth line; sink the root 25% of tusk length into the jaw. Lengthen the tusk by about 30%, curve it outward about 20 deg then up, with the tip ending just above snout-top height and slightly forward. Keep the base thick (about 1/3 of its length) so it is a tusk, not a needle.
   - Check: 1_beauty az000: tusks rise from beside the lower snout and curve up past the disc like 5_reference front; az090: tusk visible as a curve from the lip; hit and float 0.

3. **Crest clumps are equal in height and pitch (F major).**
   - Where: 2_closeups crest colour/wire and 1_beauty az090: five tufts of nearly the same height and spacing, reading as a castellated comb. 5_reference side and front: the crest starts low between the ears, peaks over the withers and falls away, clumps uneven, all swept back.
   - Fix: Stage 3: re-space the crest clumps unevenly (gaps vary +-35%) and set heights to a curve: nape 0.6, withers 1.0, then 0.8, 0.55, 0.35 of the tallest. Lean the back three clumps further back (35-40 deg) than the front two (20 deg). Add one small low clump on the nape between the ears so the crest starts at the head as in 5_reference front. Keep the r11 valley heights and the two-vert tops.
   - Check: 1_beauty az090: the crest silhouette is a ridge that rises to the withers and falls away, no two clumps alike; slivers stay under 2%.

4. **Attack has no tusk toss (O major).**
   - Where: 4_posed attack_f008 and attack_f016: the head is a little lower than idle; the silhouette barely changes. Brief: a charge.
   - Fix: Stage 4 (clip keys): key a wind-up and toss: at about 30% of the clip, head and neck down 20 deg, chest down 5% of height, hind legs gathered; at about 55%, root forward 10% of body length, head snapped up 25 deg and rolled 10 deg (the tusk hook); settle back by the last frame (first = last). Keep the feet planted until the lunge.
   - Check: 4_posed attack frames: one frame head-down, one head-up with the tusks above the snout line; fold-overs stay under 0.5%; drift 0; clip warning does not grow.

5. **Forelegs are hourglass tubes at the wrist (F major).**
   - Where: 2_closeups front limb colour and wire: the forearm pinches to a narrow waist at the knee/wrist ring, then flares into the hoof block. 5_reference side: forearm, a knee bump, a slim straight pastern, then the hoof.
   - Fix: Stage 2 (vertex moves): widen the narrowest ring (the wrist waist) to about 85% of the forearm ring and push its front verts forward about 10% of leg width to make a knee bump; scale the ring just above the hoof to about 80% of the wrist ring so the pastern is a slim straight segment; keep the hoof size. Same on the hind cannon if it pinches.
   - Check: 2_closeups front limb wire: no waist-then-flare; a knee then a pastern; IoU > 0.9.

## Should-fix

- F: tusk contrast: if the tusk colour is near the snout pink, darken the snout disc one step or lighten the tusk so they separate at az000.
- Ears are fine at the skull corners; keep the r21 back-vert thickness.

## Dropped

- None. Nothing needs stage 1.

## Appendix: both reviews verbatim

### Fable 5.1: FIX 7
- top_issues:
  - 2_closeups crest colour: the crest is a row of near-identical blunt clumps of equal height and spacing; vary height and pitch so it reads as bristle, not a comb.
  - 1_beauty hero/az000: tusks are short and tucked against the snout with weak contrast; they should curve up and out of the lower jaw more.
  - 2_closeups front limb wire: the foreleg pinches to a waist at the wrist then flares into the hoof block, an hourglass tube rather than a knee and pastern.

### Opus 5.5: FIX 6
- top_issues:
  - 1_beauty az090/hero: the dark shoulder saddle is a hard rectangular block whose border cuts across faces instead of following loops
  - 1_beauty hero/az000: tusks stand off the side of the snout like separate horns stuck on the cheek, not rising from the lower jaw
  - 4_posed attack_f008: head-down charge has barely any tusk toss; silhouette nearly identical to idle

### Kit gates (this build, current kit)
- kit_gate_fails: none
- kit_warnings: none
- clip_area_pct 0.0, stretch 0
