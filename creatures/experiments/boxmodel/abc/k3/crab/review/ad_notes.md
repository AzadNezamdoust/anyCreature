# Art-direction notes, NGO repair pass (reconciled, K=1)

Scores (Fable 5.1 / Opus 5.5): 7 FIX / 6 FIX.

**Stage 1 is locked. No unlock is authorised for this pass.** Every fix below is a stage-2, stage-3 or stage-4 change. Stage-2 IoU against stage 1 must stay above 0.9 in every view; stage 3 never edits the base; all gates pass.

Keep what works: the wide low carapace, two chunky gapped claws with teeth, eight splayed legs with two bends and dark tips, stalk eyes on the front rim, the exact palette, and the clean rig (0 flips, 0 drift, the scuttle and the snap). Both reviewers call the brief fit strong; do not regress it.

Kit gates: none failing. clip_area_pct 0.04 (2 triangles), below the 1.0 threshold: no item. There is no item 0.

Fix the must-fix list in order, then the should-fix items if turns allow. Check every item in your own `--review` packet before you call it done.

## Must-fix, in order

1. **Rim teeth are needle spikes (F major, O major).**
   - Where: 1_beauty hero and back34; 2_closeups front limb (rim by the claw) and hind limb (a radial fan of thin spikes on the rim beside the eye stalk); 3_tech back34 near the rear-left rim. Five thin needles per side, longer than they are wide, read as splinters. 5_reference: the rim is a scalloped edge of blunt bumps.
   - Fix: Stage 3: rebuild piece_rim_teeth as 4 blunt low pyramids per side, base width at least 1.5x the height, height about 6% of the carapace width, each tilted outward along the rim normal and sunk 25% of its height into the rim so it grows from the edge. Space them unevenly (+-20%) and stop them short of the eye sockets (no tooth within one tooth-width of a stalk). No spike may have an apex angle under 45 deg.
   - Check: 2_closeups hind limb colour: blunt scallops on the rim, no needles; teeth hit/float/z-fight 0; slivers unchanged or lower.

2. **Cream belly shows as a flat shield on the front face (O major).**
   - Where: 1_beauty az000 and hero: a large cream oval sits on the front face of the body between the eye stalks and above the claw arms, so the front rim loses its red toothed edge. 5_reference front: the cream is the underside and a low band under the rim; the whole front face above it is red with the dark ridge.
   - Fix: Stage 3 (paint only): restrict the `belly` rule to faces with n.z < -0.2 (underside) plus the front band below the rim's lower edge loop; front-facing faces (n.y < -0.5) above that loop go back to `shell`, and the `ridge` band runs along the front rim edge loop as it does on the sides. Borders must sit on loops.
   - Check: 1_beauty az000: the front is red down to a thin cream band at the bottom; the rim reads as a red toothed edge; 5_reference front matches at a glance.

3. **Eyes are black bicone diamonds on tall thin stalks (AD minor; from the packet and the builder's own s3 r02 note).**
   - Where: 1_beauty az000, hero and az090: each eye is a diamond on a pillar about 3 stalk widths tall. 5_reference: a round black ball on a short stalk.
   - Fix: Stage 3: rebuild piece_eye_bulb as an 8-sided two-ring ball (no single apex top or bottom), diameter about 1.6x the stalk width, and shorten each stalk to about 60% of its current height while thickening it 20%; keep the bulb seated on the stalk with the stalk rooted in its socket.
   - Check: 1_beauty az000: two round black eyes on short stalks; eye hit/float 0.

4. **Walking legs are constant-section tubes with a weak second bend (F minor, O minor).**
   - Where: 2_closeups hind limb colour and wire: femur, tibia and tarsus keep one width; the second bend at the tibia/tarsus is a shallow kink.
   - Fix: Stage 2 (vertex moves): scale the knee (femur/tibia) ring to about 1.2x the femur width, scale the tarsus rings down to about 70% of the tibia, and lower the tibia/tarsus joint ring by about 5% of the leg length so the second bend reads. Legs are thin; IoU will hold.
   - Check: 2_closeups hind limb: a knee swell and two visible bends per leg; IoU > 0.9; move_f007 still plants the B-set legs.

5. **Barnacles are plain prisms glued on one side of the rear rim (F minor, O minor).**
   - Where: 2_closeups barnacles colour and wire; 1_beauty back34: four hexagonal stubs standing proud on the rear rim at one side only.
   - Fix: Stage 3: rebuild each barnacle as a low truncated cone (top diameter 60% of the base, height at most 60% of the base diameter, 6 sides), sink each 30% of its height into the rim, vary the diameters +-40%, and place them in a tight cluster of 4-5 on the rear rim near the centre-line as in 5_reference rear. Keep the `barnacle` colour.
   - Check: 2_closeups barnacles: cones bedded in the shell with no visible base ring; barnacle float/z-fight 0.

## Should-fix

- F/O: none beyond the list. AD: the small yellow sliver lines on the claw palms in 3_tech az000 pass the gate; leave them unless item 1 changes the sliver count.

## Dropped

- None. Every item is reachable in stages 2-4.

## Appendix: both reviews verbatim

### Fable 5.1: FIX 7
- top_issues:
  - Rim teeth are sparse needle spikes on the carapace front edge, read as slivers at close range (2_closeups front limb)
  - Walking legs are constant-section tubes between the two bends; no taper or knee swell
  - Barnacles are plain extruded prisms glued on the rear rim rather than bedded in
- brief_fit / keep: Hits nearly every line: low wide carapace, two chunky gapped claws with teeth, eight legs with two bends and dark tips, eye stalks, barnacle cluster, palette exact

### Opus 5.5: FIX 6
- top_issues:
  - Radial fan of needle spikes on the rear-left carapace rim (hind-limb close-up, back34), a machine tell that reads as splinters
  - Cream belly shows as a flat shield on the front face between the eye stalks (az000), so the front rim loses its red toothed edge
  - Walking legs are constant-section tubes with a weak second bend; barnacles are plain stubby cylinders
- brief_fit / keep: Strong: wide low carapace, chunky claws with teeth and a gap, eight splayed legs with dark tips, stalk eyes on the rim, barnacles on the rear rim.

### Kit gates (this build, current kit)
- kit_gate_fails: none
- kit_warnings:
  - WARN s4 qa: 2 triangles (0.04% of surface) clip through the body in a pose that did not at rest (pink): a limb through a flap, a paw through the cheek
- clip_triangles 2, clip_area_pct 0.04
