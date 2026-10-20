# goblin (t7 hand box-model, biped) - NOTES

Technique from wolf_base (t7r line). One spine loft of 6-vertex half rings runs crotch -> crown, with the rings lying flat (back seam -> front seam). The legs are 2-face regions of the crotch-hip span, extruded down as horizontal hexagons. The arms are 2-face regions of the chest side, extruded out and down. The ears are 1-face extrusions of the skull side. The hooked nose is a 1-face extrusion of the face front, with its seam wall removed so the mirror closes it. Stage 0: blueprint.json was traced from reference/sheet.png with kit/refs.py (height 1.0 m). The sheet's top view is unreliable (refs warns that the top length is 1.48x the side length), so the fit uses the side and front views only.

## Stage 1
- r0: first fit. Gate FAIL: 3 open edges. IoU side/front 0.82/0.753.
- r1: Critique: the open edges. Diagnosis: deleting the nose's seam walls with FACES_ONLY left the old seam edges loose. Fix: delete with FACES. Result: PASS, 648 tris.
- r2: Critique: az000. The arms and hands are thin sticks next to the ref's chunky forearms and broad hands. Diagnosis: the ARM radii are below the widths read off the ref. Fix: forearm 0.052-0.055, hand 0.042/0.055. Result: better, IoU 0.823/0.753.
- r3: Critique: front overlay. The arms stand about 3 cm outside the ref arm line from the elbow down. Diagnosis: the A-pose spread is too wide. Fix: elbow, forearm, wrist and hand moved in by 2-2.5 cm. Result: better, front 0.778.
- r4: Critique: side overlay. The nose sits high and does not droop to the ref's hooked tip at z 0.75. Diagnosis: the NOSE centres are 1-1.3 cm too high. Fix: lower them. Result: better, side 0.828.
- r5: Critique: az000. The crown narrows to a point, while the ref has a round dome. Diagnosis: H3/H4 W 0.115/0.055. Fix: W 0.13/0.085. Result: dome reads round; front 0.773, because the traced polygon is coarse at the crown.
- r6: Critique: front overlay. The ear root is short, while the ref's ear base drops to z 0.77. Diagnosis: the first ear section is 0.13 tall. Fix: first section wide 0.08, centre 1.5 cm lower; mid section 0.048. Result: better, IoU 0.816/0.794.
- r7 (LOCK): 326 verts, 648 tris, edge sha256 00018eb13e87fa73.

## Stage 2
- r1: Joint rings at the shoulder, elbow, wrist, hip, knee, waist and neck. Eye socket inset into the stop face and pushed 9 mm in; brow corner forward; firmer jaw corner. All gates PASS, 824 tris, min IoU vs s1 0.991.

## Stage 3
- r1: Plan: 7 colours (skin, dark ear tip, warm inner ear, leather, rope, yellow eye, black pupil/nails). Pieces: lens eyes; a vest (solid panels rooted along their rim, open at the front, back and front strips over the shoulder, pointed hem); a loincloth (front and back flaps with ragged hems, plus a sunk rope belt per side); 4 fingers + a thumb per hand; 5 toes per foot with dark nails. Gates PASS, 1780 tris.
- r2: Critique: hero colour. The skin reads dark saturated green, while the ref is a light olive. Fix: skin #a3b56c, ear tip #4a6644. Gates PASS.

## Stage 4
- r1: Biped rig: 12 bones plus .R mirrors, roll auto. Clips: idle 48 (breath, head turn, ear twitch, arm sway); move 33 (a walk: opposed leg swing, knee fold, arm counter-swing, hip bob); attack 32 (left arm wind-up, then a forward swipe with a lean). All gates PASS: hit/float 0, zfight 2 (limit 2), slivers 1.7%, fold-overs 0.06%, drift 0. Clip warning: 1.16% of the surface clips in a pose.

Checks: orbit18_sheet.jpg shows all 18 views reading, with no hole or collapse. Separation on the rest mesh: leg L-R 9.0 cm, each arm vs the torso 8.4 cm, arm vs leg 8.6 cm, so nothing is fused (PASS). side_by_side.jpg shows the reference side/front/rear next to the model.

Triangles: stage 1 648, stage 2 824, total 1780.
Weaknesses: the vest reads as strips, not a full ragged vest; the rope belt reads as a thin band; the torso is slimmer than the ref; the fingers are small.

## Fix pass (both reviews merged)
- Fix list, shape first: ears 0.6x length, tilted up/back, single skin colour (both reviews; drops the two-tone mask); nose shorter and pointed forward (opus); arms ~12% shorter with an elbow bend back (both); feet ~25% shorter (both); bigger finger mitts (both); loincloth flaps 6 mm further off the pelvis (fable).
- Base change: stage 1 re-locked. r1 FAIL self-intersection (ear root folded into the skull at the steeper tilt); r2 ear tilt eased, PASS, 648 tris, IoU side/front 0.78/0.766. Stage 2 log and the lock assertion re-run PASS.
- Stage 4: all gates PASS; separation PASS (leg L-R 9.0 cm, arm vs torso 8.8 cm). Renders, orbit18_sheet.jpg, side_by_side.jpg and before_after.jpg refreshed.
- Not fixed: vest still reads as strips; torso slimmer than the ref.

## Fix pass 2 (review2 fable + opus merged, concept sheet as referee)
- Fix list, shape first: nose shorter with a down-turned tip (both; the sheet nose hooks down); shins/ankles thinner, LEG rings 1-3 ~0.82x (both).
- Skipped: ears 0.75x + droop (opus) - the sheet ears are long and level, shrinking moves away from it; vest open front (fable) - already open at the front like the sheet; smaller feet (opus) - the sheet feet are big.
- Base change: stage 1 re-locked. r8 FAIL self-intersection (first nose ring too close to the root); r9 first ring kept, tip shortened and dropped, PASS, 648 tris, IoU side/front 0.774/0.763.
- Stage 4: all gates PASS, 1780 tris; separation PASS (leg L-R 10.3 cm, arm vs torso 8.8 cm). Renders, orbit18_sheet.jpg, side_by_side.jpg, before_after2.jpg refreshed.
- Not fixed: torso slimmer than the ref; nose still thinner than the sheet's bulb.

## Density pass 3 (owner: denser main mesh, ~2x tris, same t7 technique)
- before3/ holds the pass-2 hero, orbit, side-by-side, script and lock.
- Body loft: half rings 6 -> 10 vertices (a Catmull-Rom rounding vertex, pushed out 4 %, in each span from the back seam to the lower front; the belly/chin plane stays one flat face). Spine stations 14 -> 23: R1b hip round-over, R2b belly tuck, R3b ribs, R5b shoulder round-over, R6b neck base, N0b throat, H0b chin, H1a upper lip, H2b forehead, H3b dome; front/back points read off the side trace, W off the front trace.
- Limbs: 10-vertex rings from a 4-face root strip, roles spread round the root loop in its own order. Legs 6 -> 11 stations (thigh, calf, low shin, heel, ball); arms 6 -> 11 (upper arm, biceps, forearm swell, low forearm, palm). Ear 6-gon from 2 faces; nose unchanged.
- r10-r14 FAIL self-intersection: r10-r11 arm rings folded (projection-sorted roles misordered the root loop; fixed by loop order); r12-r14 ear root wall into the forehead (ear root roles scaled down, H2b W 0.124). r15 LOCK: 926 verts, 1848 tris, edge sha256 514e2d19be51a1a3, IoU side/front 0.778/0.764 (was 0.774/0.763).
- Stage 2 follows: joint rings re-aimed at the new limb stations, waist ring R2b-R3, neck ring N0b-H0, eye socket in the front half of the old eye face (inset 0.26), brow/jaw moves on the new ring indices. Stage 3: vest and belt rebuilt on the 10-vertex rings (still rooted); other details unchanged. Budgets: stage 1 1200-3000, total 2600-4800.
- Stage 4 r16: all gates PASS, lock OK, glbcheck OK, slivers 0.7 %, drift 0; stretch/clip warnings only (clip 0.32 %). Separation PASS (leg L-R 10.4 cm, arm vs torso 7.8 cm).
- Triangles 1780 -> 3300 (1.85x): body 824 -> 2136, details 956 -> 1164 (vest/belt follow the new rings); 86 % of the increase in the body loft. stage4, orbit18_sheet.jpg, side_by_side.jpg, before_after3.jpg rebuilt.
- Not fixed: eye lens reads smaller in the narrower socket face; torso still slimmer than the sheet.

## Review MIX pass (review_poly2x: keep the new body, restore the before3 head/brow and eye)
- pass3/ holds the 2x-pass hero, orbit, side-by-side, script and r15 lock.
- Body, limbs, head rings unchanged (the dense loft stays). Eye: in the nose-root -> brow span the rounding column 7 is set flat on the 6-8 chords and its edge dissolved, so the eye face is the whole before3 face again (one flat plane); eye_face_centre back to its full face; socket inset 0.26 -> 0.36 (the before3 value); brow move back to the single before3 corner vertex (the second brow vertex pushed the overhang over the eye).
- Base changed, so stage 1 re-locked as r18 (r15 lock in pass3/): 926 verts, 1848 tris, edge sha256 acbce9e1971ddbdd, IoU side/front 0.778/0.764.
- Stage 4 r19: all gates PASS, lock assert PASS, glbcheck OK, 3308 tris; separation PASS (leg L-R 10.4 cm, arm vs torso 7.8 cm); stretch/clip warnings only (clip 0.32 %). orbit18_sheet.jpg, side_by_side.jpg, before_after4.jpg (before3 | 2x pass | now) rebuilt.

## Fix pass 9 (dense mesh kept, problems fixed inside it)
- Owner: fixes must not drop density. Start: the MIX script was already the dense 2x mesh (pass-3 loft, 10-vertex rings, 23 stations) with the before3 eye face; kept as is. before9/ holds the MIX renders, script and r18 lock.
- review_poly2x WORSE parts: small eye under the brow; brow overhang. Fixes: eye lens radius 0.015 -> 0.019 (pupil 0.0065 -> 0.0085), larger than before3; brow corner move halved (0.004, -0.005, 0.002) so it no longer shades the eye. Arm rib banding: elbow/forearm/wrist ring radii smoothed (elbow 0.042 -> 0.044, forearm swell 0.052 -> 0.049, wrist 0.04 -> 0.042), so no pinch-swell-pinch bands.
- Junctions (legs, arms, ears, neck) checked in the 18-view orbit: no holes, specks, slits or folds.
- Stage 1 re-locked in the stage-4 r20 run: 926 verts, 1848 tris, edge sha256 3faa300f2ea5e294. All gates PASS, lock assert PASS, glbcheck OK, 3308 tris; separation PASS (leg L-R 10.4 cm, arm vs torso 7.6 cm); stretch/clip warnings only (clip 0.32 %). orbit18_sheet.jpg, side_by_side.jpg, fix9.jpg (before9 | after, head and arm close-ups) rebuilt.
