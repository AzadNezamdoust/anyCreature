# Art-direction notes, repair round 2 (reconciled, K=2)

Scores (Fable 5.1 / Opus 5.5): 7 FIX / 5 FIX.

**Stage 1 is locked. No unlock is authorised for this pass.** Every fix below is a stage-2, stage-3 or stage-4 change. Stage-2 IoU against stage 1 must stay above 0.9 in every view (minimum is 0.914 at az180 now: leg moves have little room); stage 3 never edits the base; all gates pass.

Keep what works (round 1 fixed these; do not regress):
- Front wall red down to a thin cream band; cream only on the underside (az000).
- Rim teeth are blunt lobes from above, no needles in the top view (r09-r10).
- Round eye bulbs on short stalks, not diamonds (r13).
- Knee swell on the walking legs, second bend reads in az000 (r14-r15).
- Wide low carapace, two claws in front, eight splayed legs (5_reference top match); slivers 0.3%, flips 0, drift 0.

Fix the must-fix list in order, then the should-fix items if turns allow. Check every item in your own `--review` packet before you call it done.

## Must-fix, in order

0. **Kit gates.** No FAIL on the current kit. clip_area_pct 0.03 (2 barnacle triangles, below 1.0 and not visible in the packet); stretch 0. Do not let the claw or leg changes grow it.

1. **Claws are boxy palms with thin spike fingers (O major).**
   - Where: 2_closeups front limb colour and wire: a big round palm block with two thin pointed fingers and tiny spur spikes; 1_beauty az000 and hero: the fingers read as black needles hanging off a red box. 5_reference front and top: chunky curved fingers almost as thick at the root as a third of the palm, dark tips, a clear gap.
   - Fix: Stage 2 (vertex moves): on both fingers (fixed and moving), push the verts out from the finger axis so the root section is about 35% of the palm height (about 1.6x now) and the finger tapers to a blunt tip at 40% of the root; curve the fixed finger's tip up and the moving finger's tip down about 15 deg each so the gap is a lens, about 25% of the palm height at its widest. Shave the palm's bottom ring in by 8% of palm height so palm and fingers read as one pincer. Stage 3: drop the small spur spikes or make them 2-3 blunt bumps on the inner finger edge, sunk 30%; paint only the last 30% of each finger dark (the brief's dark tips), not the whole finger.
   - Check: 2_closeups front limb colour: a thick pincer with a visible gap and dark tips like 5_reference front; 1_beauty az000: no black needles; IoU > 0.9; hit 0.

2. **Body rides high on stilt legs with an inverted-V bend (O major).**
   - Where: 1_beauty az090 and 5_reference side: our knees peak above the carapace and the legs drop straight down to tall points, lifting the cream underside clear; the reference legs go out and down from a low body, knees at about carapace height.
   - Fix: Stage 2 (vertex moves), within the IoU floor: lower the knee rings of every walking leg by about 6% of the creature height and push them outward (along the leg's reach) by about 4% of the leg span, so the leg splays instead of peaking; shorten the dark tip cone by moving its tip vertex up by about 20% of the tip length so the tips do not read as stilts. Move the J knee joints to match. Lowering the body itself needs stage 1 (see Dropped); this item only flattens the legs. Stop at what keeps IoU > 0.9 and log it partly done.
   - Check: 1_beauty az090: knee tops at or below the carapace top; legs splay outward; IoU > 0.9 every view; 4_posed move frames: tips stay on the ground, no fold-overs.

3. **Carapace front teeth are thin flat slivers edge-on (F major, O minor).**
   - Where: 2_closeups front limb colour/wire: the rim teeth beside the claw joint are thin horizontal wedges with dark undersides, reading as slivers stuck on the rim; 1_beauty az000: a few tiny wedges. 5_reference front and top: a row of many small teeth along the front and anterolateral rim, cut into the rim.
   - Fix: Stage 3: rebuild piece_rim_teeth as 6 teeth per side (front edge to the claw joint), each a 4-sided pyramid with a base depth (vertical) at least 60% of its base width, height 70% of the base width, the tip tilted 15 deg down so it continues the rim's slope; sink each base 35% into the rim. Grade size: largest at the anterolateral corner, 70% at the eyes. Keep them red (shell colour), no dark faces.
   - Check: 2_closeups front limb colour: a saw-tooth rim with thickness, no thin dark wedges; 1_beauty az000: teeth read along the front edge as in 5_reference front; slivers <= 2%, hit/float 0.

4. **Eye bulbs read as hex nuts on stubs (O minor).**
   - Where: 2_closeups front limb and hind limb colour: the bulbs are flat-capped octagonal blocks; 1_beauty az000: black nuts. 5_reference front: round black balls on thin stalks about two bulb diameters tall.
   - Fix: Stage 3: replace the flat octagon caps of `ball()` with a pointed or two-ring cap (equator 10 sides, rings at 0.7 and 0.95 of the radius) so the bulb is round in every view; make the stalk 1.4x its current height and 0.8x its radius. Keep the bulb size and the r13 sink.
   - Check: 1_beauty az000 and hero: round black balls on thin stalks; eye hit/float 0.

5. **Walking legs are constant-section tubes (F major).**
   - Where: 2_closeups hind limb colour and wire: the segment between the knee and the dark tip is one straight box of constant width, then a long cone. 5_reference side: each segment swells at the joint and tapers toward the tip.
   - Fix: Stage 2 (vertex moves): scale the ring just above the dark tip to about 75% of the knee ring, and the mid-segment ring to about 88%, across the leg plane only (the r15 lesson: scaling in the bend plane pinches the knee). Leave the femur ring at the body.
   - Check: 2_closeups hind limb wire: taper from knee to tip; slivers stay under 1%; IoU > 0.9.

## Should-fix

- F: barnacles read as glued hex cones. Stage 3: give them 8 sides, a cream colour (5_reference rear: pale barnacles with a dark crater), and sink the two smallest 45% so the cluster sits in the shell.

## Dropped

- O "body rides high" (body height part): lowering the carapace onto the ground means moving the whole body and the leg roots, which is stage 1 and blows the IoU. Item 2 does the leg part.
- Nothing else needs stage 1.

## Appendix: both reviews verbatim

### Fable 5.1: FIX 7
- top_issues:
  - 2_closeups front limb colour/wire: the carapace teeth beside the claw joint are thin needle slivers rather than a toothed edge cut into the rim.
  - 2_closeups hind limb wire: walking legs are constant-section tubes with two bends; no thickening at the knee or taper toward the tip.
  - 2_closeups barnacles: the cluster is three small hex prisms of the same size sitting on the rim, reads as glued-on, not bedded in.

### Opus 5.5: FIX 5
- top_issues:
  - 1_beauty az090/az000: body rides high on stilt legs with a single inverted-V bend, not a low crab with two bends per leg
  - 2_closeups front limb: claw is a boxy palm with thin spike fingers and small spurs, no chunky pincer with a real gap
  - 1_beauty az000: carapace front rim teeth are a few tiny wedges; eye bulbs are large hex nuts on stub stalks

### Kit gates (this build, current kit)
- kit_gate_fails: none
- kit_warnings:
  - WARN s4 qa: 2 triangles (0.03% of surface) clip through the body in a pose that did not at rest (pink): a limb through a flap, a paw through the cheek
- clip_area_pct 0.03, stretch 0
