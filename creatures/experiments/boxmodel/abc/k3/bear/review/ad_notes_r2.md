# Art-direction notes, repair round 2 (reconciled, K=2)

Scores (Fable 5.1 / Opus 5.5): 7 FIX / 6 FIX.

**Stage 1 is locked. No unlock is authorised for this pass.** Every fix below is a stage-2, stage-3 or stage-4 change. Stage-2 IoU against stage 1 must stay above 0.9 in every view; stage 3 never edits the base; all gates pass.

Keep what works (round 1 fixed these; do not regress):
- Pale muzzle stops under the eyes, brown between eyes and ears; small pale bib under the chin (az000).
- Round cup ears (az000, hero, az090).
- Eyes read as dark dots at thumbnail size (hero, az000); size stays.
- Withers are the highest point, back falls to the rump (az090 matches 5_reference side).
- Forelegs narrow from elbow to wrist; darker lower legs.
- Clean tech: all gates PASS, clip 0, stretch 0.

Fix the must-fix list in order, then the should-fix items if turns allow. Check every item in your own `--review` packet before you call it done.

## Must-fix, in order

0. **Kit gates.** No FAIL on the current kit; clip_area_pct 0.0, stretch 0. Nothing to do; keep it that way.

1. **Eye is a proud octahedron gem (O major).**
   - Where: 2_closeups head wire: the eye is a pointed 8-face gem standing out of the socket; head colour: a faceted black lump on the brow edge, not a dot set in.
   - Fix: Stage 3: rebuild piece_eye as a low dome (6-8 sides, one ring plus a flat or slightly domed front cap), depth about 35% of its width, same width as now (r16 size). Seat it so the front cap is proud of the socket by about 30% of its depth and the rest is inside the head. Keep the lens normal turned toward -Y (r17). Keep the `dark` socket paint.
   - Check: 2_closeups head wire: no point on the eye, a flat-fronted dot in the socket; 1_beauty hero and az000: eyes still read; float and z-fight 0.

2. **Claws are a comb of identical needle spikes (F major, O major).**
   - Where: 2_closeups front limb, hind limb and claws colour/wire: 5 thin, equal, evenly spaced spikes along the paw edge on every paw; 1_beauty hero: a saw edge at each paw front. 5_reference front: short, thick, curved dark claws.
   - Fix: Stage 3: rebuild each claw as a thicker curved hook: base width about 1/7 of the paw width (about 2x now), length about 60% of the current length, tip bent down about 30 deg so it touches the ground line. Grade them: the middle three equal, the two outer ones about 80% length; root each claw into the toe front by about 25% of its length (no gap). Fan them out by about 8 deg so they do not read as a comb. Hind claws 70% of the front size.
   - Check: 2_closeups front limb colour: separate blunt hooks, not a saw edge; 1_beauty az000: claws read as short dark nubs like 5_reference front; hit and float 0.

3. **Muzzle is a flat wedge with no brow step (F major).**
   - Where: 2_closeups head colour: the pale muzzle is one flat sloping plane from brow to nose; 1_beauty az090: the profile runs straight from forehead to nose. 5_reference side: a clear stop (dish) where the forehead meets the muzzle, and a rounded muzzle top.
   - Fix: Stage 2 (vertex moves): lower the top verts of the ring at the muzzle stop (between and just in front of the eyes) by about 4% of head height and move them back about 2% of head length, so the forehead stands as a step above the muzzle; raise the top verts of the muzzle's front ring by about 2% so the nose end does not droop. `flatten` the muzzle's front face so the nose pad sits on one plane. Head is a small share of the silhouette; IoU holds.
   - Check: 1_beauty az090: a visible dip in the profile between eye and muzzle; 2_closeups head colour: the brow overhangs the muzzle; muzzle paint still stops under the eyes.

4. **Tail is a disc with a radial fan on the rump (F major).**
   - Where: 1_beauty back34 and 5_reference model az180: a flat round disc with spokes in the middle of the rump. 5_reference rear: a short stub tail that hangs out and down.
   - Fix: Stage 2 (vertex moves): pull the fan's centre vert back by about 5% of body length and down by about 3% of body height so the disc becomes a stub cone; pull the fan's first ring back by about 2% so the stub has a base. If the pole pull alone reads as a spike, Stage 3 instead: a 6-sided stub piece (length about 7% of body length, width about the disc's width, pointing back and 30 deg down), rooted into the rump by 30% of its length, bound `body=`.
   - Check: 1_beauty back34 and 5_reference az180: a stub tail reads; no spokes on a flat disc; IoU > 0.9, hit and float 0.

## Should-fix

- O: legs are tubes onto box paws. Stage 2: scale the paw's top ring to about 90% of the wrist ring and pull the paw's front-top verts down about 15% of paw height so the paw slopes to the toes instead of a step-sided box.
- Far armpit fan (round 1 item 4, partly done): Stage 2, pull the far-side elbow ring's inner verts out to the flank line as done on the near side, if it still shows in 2_closeups front limb.

## Dropped

- O "a thin stray sliver line sticks out above the ear/brow in every posed frame": dropped. The packet was rendered 2026-09-28, before the kit's wire overlay lost its even offset (2026-09-29), which drew needle spikes at sharp corners; the colour views show no such piece. Re-check in the new packet's 4_posed; if it is still there, it is a stray weight on the brow and goes to should-fix.
- Nothing needs stage 1.

## Appendix: both reviews verbatim

### Fable 5.1: FIX 7
- top_issues:
  - 2_closeups front limb colour/wire: claws are still a comb of identical needle spikes on the paw edge.
  - 1_beauty back34: radial fan around the tail stub on the rump; the tail itself is a small disc, not a stub.
  - 2_closeups head colour: the muzzle is a flat pale wedge with the nose pad sitting on the flat front plane, no dished brow-to-muzzle step.

### Opus 5.5: FIX 6
- top_issues:
  - 2_closeups head: eye is a protruding octahedron gem sitting proud of the brow instead of set into the socket
  - 4_posed attack_f010/idle_f012/idle_f024: a thin stray sliver line sticks out above the ear/brow in every posed frame
  - 2_closeups claws: comb of identical needle claws; legs are constant-section tubes onto box paws (same as X)

### Kit gates (this build, current kit)
- kit_gate_fails: none
- kit_warnings: none
- clip_area_pct 0.0, stretch 0
