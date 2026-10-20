# wolf c3: stage-1 cage on the part guide (form and topology only, not locked)

Why c2 failed: limbs left the torso at the elbow (root loop below the joint, root poles inside the elbow / knee band),
8-sided torso of a few huge faces against dense legs (edge ratio head 6.4, torso 4.4; 7.6% faces over 5:1), paws welded
with n-gons, head one lofted wedge (profile RMS 5.95%), fore leg taper +35%.

J: c2's joints plus a `chest` spine joint and the neck joint 4 cm forward (-0.41, 0.73): the neck band no longer covers
the shoulder loop's corners. Guide rebuilt from this J (part_guide.npz here).

- r1 Critique: rump ring folded onto the thigh (24 intersections), tail tip a needle (24:1), knee and neck 1 loop, front IoU 0.825, head RMS 5.4%.
  Diagnosis: R fitted against the haunch mass; tail end ring sized at t 1.12; ruff read 10% narrower from the guide than the sheet. 792 tris.
- r2 Fix: rump collar from the tail's own root station, tail rings off the tail1 dip, blunt end; neck rings swelled to the sheet; B forward. Result: stack, ratio, aspect, neck loops pass; knee 1 loop; front 0.848.
- r3 Fix: hip patch 4 cm forward (thigh front was through the flank), thigh ring deeper, shin ring thinner, muzzle rings wider. Result: hind form passes; head RMS 3.9%.
- r4 Fix: N1 back to neck t 0.70 at the sheet's width, ear back edge raked back, brow ring shallower. Result: head RMS 2.71% PASS, proportions PASS.
- r5 Tried full bisector mitres at every joint: shin +30% thick, RMS 6% — reverted. Knee loop: the inner back edge between the two knee rings was 2.4 cm and ran across the axis; no shear on the thigh ring, lower knee ring 1 cm down. Result: knee 2 loops.
- r6 Critique: armpit wedge (limb from the mid-flank face, bent 90 degrees) = sliver faces and 6-14 intersections. Fix: limbs grow straight down out of the LOWER-flank faces (col 3), no shoulder slab ring. Result: no fore intersection, 744 tris; root loop t 0.27 / 0.25 (just below the joint).
- r7 Fix: patch rings' upper vertex raised (angles 68 / 101): the loop's centre over the joint. Result: root loops PASS.
- r8 Fix: rump collar leaned 30, shorter, lower vertices by design (they were dragged onto the thigh). Result: no intersection; front 0.848.
- r9 Fix: paws at the sheet's width, ruff rings A / N2 a little wider. Result: ALL GATES PASS, 744 tris; blockout packet built.

Not waived: nothing in META['intended'], no iou_floor override.
Kit notes: (1) joint_loops merges two rings into one component when one short lengthwise edge between them runs under 0.6 along the axis: a 2.4 cm edge behind the knee cost a loop although topology() counted 2 rings there. (2) The front blueprint has no tail between the legs (the sheet's front view does not draw it); the side view does, so the model loses about 4-5% front IoU there (0.852 against a 0.85 floor). (3) part_guide's tail has a width dip (0.06 m) at the tail1 joint. (4) fit_to_guide drags rump / chest vertices onto the limb masses; those vertices are placed by design.

## Rebuild on the new part base + review_topology.md fixes (r10-r21)

- r10 Critique: the r9 program on the new base fails 8 gates (rings B / D1 / D2 collapsed, 7 open edges, 10 intersections). Diagnosis: the new torso part reads width 0.001 where a limb root or the ruff covers the plan view (y > 0.27, y < -0.34).
- r11 Fix (rebuild): torso width under 0.15 replaced by a design width (0.30 rear / 0.35 front), the guide fit sets it. Review fixes in the same pass: J chest back to y -0.19 (neck band 0.048 -> 0.092) and neck rings A / B 0.125 m apart (0.28 x width, was 0.16); third ring at elbow and stifle plus an upper-arm / thigh ring between root loop and joint; hip patch 6 cm forward (one plain face before the tail collar); shoulder patch's front corner raised; fore J 1.2 cm wider; jaw step on the muzzle rings; landmarks. Result: closed, no intersection, 856 tris; head edge ratio 4.43, front IoU 0.807, head RMS 3.85%.
- r12 Fix: old ruff swells back. Result: worse (neck / head width +26%, head RMS 4.9%): the new base already reads the ruff, the swells were for the old one.
- r13 Fix: swells cut to 1.02-1.17, N2 ring back, skull 1.14 wide. Result: proportions pass, head RMS 3.17%; D3 ring cut the thigh, tail stack.
- r14 Fix: B 1.10, brow ring 1.02, stifle ring thinner. Result: head RMS 2.35% PASS. Eye-loop inset made valence-6 fans at the stop corners and head edge ratio 4.1.
- r15 Fix: inset removed (the eye loop is a stage-2 inset by the protocol), extra rump ring removed (stack), shoulder corner raise halved (0.08 m made a sliver face to the keel). Result: all gates but front IoU 0.838; waived to 0.83 (sheet front view draws the cheek ruff 0.40 m wide, the top view 0.345 m; no tail in the front view). ROM 3.02%.
- r16-r18 Tried joint rings fanned OPEN on the flexion side and spread wider: ROM 2.6-3.1%, hind profile fails. The crease faces of an 80 degree bend fold whatever their size; bigger faces = more folded area. Reverted.
- r19 Fix: joint rings TIGHT on the flexion side (fan the other way), third ring at the hock. Result: ROM 2.23%, all gates pass, 864 tris.
- r20 Tried the lower stifle ring untilted, hock rings thinner: ROM 1.86% but hind thickness +14.5% FAIL.
- r21 Fix: lower stifle ring tilted again, 0.93 deep. Result: ALL GATES PASS, 864 tris, ROM 2.26%. LOCKED.

Waivers: iou_floor front 0.83 (reason above, in META). Nothing in META['intended'].
Not followed: suggested 8-sided torso / 7-ring budget. Kept 10 sides: the limb grows out of one lower-flank column, an 8-sided ring makes that column twice the limb's face size and the torso density drops under 0.6.
Still weak: ROM 2.26% (elbow front, hock front, stifle back crease faces, one flank face over the shoulder in swing); eye loop absent; one 18:1 face behind the stifle; shoulder pole raised 4 cm, not 8-10; the face from that pole to the keel is long; muzzle short and thin against the concept; cheek ruff narrower than the sheet's front view.
Kit notes: (5) part base: torso stations have width 0.001 under limb roots and the ruff ('src: top'), so part_rings gives collapsed torso rings there. (6) The neck-loop gate needs both rings inside 0.4 x the shorter neighbouring bone: with a short chest-neck bone the review's 0.4-0.5 x width spacing cannot pass; the joint had to move. (7) A stage-1 eye-loop inset on any face of the stop gives valence-6 corners (cap corners are already 5). (8) ROM folds are dominated by flexion-crease faces; the number rewards small crease faces, not slack.
