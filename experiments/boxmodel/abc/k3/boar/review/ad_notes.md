# Art-direction notes, NGO repair pass (reconciled, K=1)

Scores (Fable 5.1 / Opus 5.5): 6 FIX / 7 FIX.

**Stage 1 is locked. No unlock is authorised for this pass.** Every fix below is a stage-2, stage-3 or stage-4 change. Stage-2 IoU against stage 1 must stay above 0.9 in every view; stage 3 never edits the base; all gates pass.

Keep what works: the front-heavy hump, the low wedge head with a flat pink snout disc, the chunky cream tusks curving up from the jaw, the hock angles and the trot. Both reviewers call this the best brief match of its group; do not regress it.

Kit gates: none failing. clip_area_pct 0.0. There is no item 0.

Fix the must-fix list in order, then the should-fix items if turns allow. Check every item in your own `--review` packet before you call it done.

## Must-fix, in order

1. **Crest is a stegosaurus comb of identical spikes (F major, O major).**
   - Where: 1_beauty hero, az090, back34; 3_tech az090: seven identical sharp triangles at equal spacing along the spine. Brief: blunt bristle clumps. 5_reference side: a low dark ridge of uneven clumps that leans back and sits in the form.
   - Fix: Stage 3: rebuild piece_crest as 4-5 clumps of unequal height (vary +-30%; tallest at the nape, shortest at mid-back), each a blunt wedge with a flat or two-vert top (no single apex), base width about 1.5x the current spike so neighbours overlap, thickness at the base at least 30% of the clump height, and every clump leaning back 20-30 deg. Sink each base 15% of its height into the spine so no ledge shows.
   - Check: 1_beauty az090: no two crest bumps have the same outline; no needle tips. 3_tech: crest hit/float/z-fight 0.

2. **Dark saddle is a hard rectangle on the flank (O major).**
   - Where: 1_beauty az090 and hero: the saddle is a dark box with straight vertical edges at the shoulder and at mid-back, sitting on the flank below the crest. 5_reference side: the dark is a mantle hugging the crest along the top of the body and fading into the shoulder.
   - Fix: Stage 3 (paint only): restrict the `bristle` rule to faces whose top edge lies within about 25% of the hump height below the spine line (n.z > 0.25 or z above roughly 70% of the hump height), running from the nape to mid-back, and let the front edge follow the shoulder loop rather than a fixed y. The border must sit on edge loops, not across faces.
   - Check: 1_beauty az090: the dark reads as a mantle over the shoulders and spine, with no vertical edge on the flank; 5_reference side matches at a glance.

3. **Tail is a paper plate and the tuft is a fan of dark slivers (F major, O none).**
   - Where: 1_beauty back34 and az090: the tail reads as a thin flat plate edge-on. 2_closeups hind limb wire: a dense triangle fan at the rump/tail root.
   - Fix: Stage 2 (vertex moves): widen the tail tube rings to about 1.5x their current radius at the root, tapering to 1.2x at the tip, so the tail has a section from every angle. Stage 3: rebuild piece_tail_tuft as one 6-sided blunt wedge (thickness at least 40% of its width, 4-6 faces per side, no radial fan), rooted 20% into the tail tip.
   - Check: 2_closeups hind limb wire: no fan at the tail root, under 12 triangles for the tuft; 1_beauty back34: the tail has visible thickness. IoU > 0.9.

4. **Eye is a tiny flat diamond with no brow (F major, O none).**
   - Where: 1_beauty hero and az000; 2_closeups head: the eye is a small black diamond on a flat cheek about 1/10 of the head width. 5_reference front: a larger dark eye under a brow ridge.
   - Fix: Stage 3: scale piece_eye to 1.5x (about 1/7 of the head width), keep it a lens seated proud in the socket (the r02 fold fix). Stage 2 (vertex moves): pull the 2 verts above each socket outward by 3% of head width and forward 2% so a brow ridge shades the eye.
   - Check: 1_beauty az000 at thumbnail size: two eyes visible; 2_closeups head: a brow overhang above the eye; eye flips 0.

5. **Nostrils are tall rectangular boxes (O minor).**
   - Where: 2_closeups head and tusk colour; 1_beauty az000: two tall dark rectangles standing on the disc. 5_reference front: two round dark holes.
   - Fix: Stage 3: rebuild each nostril piece as a 6-sided disc about as wide as it is tall (diameter about 25% of the snout disc), inset into the disc face rather than standing proud (front face at most 10% of its width above the disc).
   - Check: 2_closeups head colour: two round dark nostrils flush with the disc; nostril float/z-fight 0.

## Should-fix

- F: ears are flat slabs. Stage 2: move the 2 back-face verts of each ear rearward 2% of head length so the ear has thickness edge-on. Keep the wide-set position (the reference has it).
- F/O: 2 flipped body faces (0.28%) pass the gate. Check them in the posed heatmap after item 3; a widened tail root may change them.

## Dropped

- F "ears set far apart on top of the head": 5_reference front shows the ears set at the skull corners exactly as ours; only the slab thickness stands (should-fix).

## Appendix: both reviews verbatim

### Fable 5.1: FIX 6
- top_issues:
  - Crest is a sawtooth of identical sharp triangles, stegosaurus-like, where the brief asks for blunt bristle clumps
  - Tail is a paper-thin plate seen edge-on in back34, and a dense dark triangle fan sits at the rump/tail root (hind-limb wire); 2 flipped faces on the body
  - Ears are slabs set far apart on top of the head; eyes are flat diamonds with no brow, so the face is only the snout
- brief_fit / keep: Strongest hump and front-heavy mass, good snout disc with nostrils and chunky tusks; crest and tail miss the brief.

### Opus 5.5: FIX 7
- top_issues:
  - the crest is a row of identical sharp spikes in a regular comb, not blunt clumps (1_beauty az090)
  - the dark saddle is a hard rectangular block on the flank, with its border cutting across faces rather than following a loop (1_beauty az090/back34)
  - nostrils are tiny rectangular boxes on the disc; 2 flipped faces on the body are under the limit but should be checked
- brief_fit / keep: Best match to the brief: low wedge head, a flat snout disc with nostrils, cream tusks curving up from the lower jaw, a front-heavy hump, hock angles and a tufted tail.

### Kit gates (this build, current kit)
- kit_gate_fails: none
- kit_warnings: none
- clip_triangles 0, clip_area_pct 0.0
