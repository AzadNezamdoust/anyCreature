# dragon (t7 hand box-model) — NOTES

Technique: wolf_base's t7 look. One spine loft of 6-vertex half rings from the spade tip to the nose. The spade is two loft sections: a tall barb ring and a tip ring. The legs are 2-face extrusions from the lower flank (spans C0 and R1). The horns are 1-face extrusions from the H0 skull span, in place of ears. The wings are a stage-3 piece. Stage 0: refs.py traced reference/sheet.png into blueprint.json (height 1.6 m to the horn tips, length 3.71 m). Sections were read off a 0.1 m grid over the side and front views.

## Stage 1
- r1: first fit. PASS, 748 tris. Blueprint IoU side/front/top 0.520/0.569/0.548. The IoU is low because the traced outline includes the wings, which are a stage-3 piece. Critique az000/top: the body and legs are slim next to the ref's heavy chest and limbs.
- r2: Fix: body widths +10-15% (C0 0.32, R1 0.29), neck wider, foreleg and hind-leg sections thicker. PASS, IoU 0.528/0.617/0.564.
- r3 (LOCK): Critique hero: the horns read as thin ears. Fix: horn base 5 x 5.5 cm, mid 3.4 cm. PASS, locked: 376 verts, 748 tris.

## Stage 2
- r1: elbow, stifle and neck-skull rings; eye socket inset in the H0b-H1 stop face; brow, cheekbone, flat muzzle planes and nose. FAIL: slivers 5.8%. A GLB probe shows them on the long tail spans (33-36 cm long on 4-7 cm rings), the spade tip and the horn tips.
- r2: Fix: tail loops in T2-T3, T3-T4 and T4-T5; the spade-tip ring scaled x3 and the horn-tip ring x2.5 (blunt tips). PASS: 892 tris, slivers 1.8%, min IoU vs s1 0.989.

## Stage 3
- r1: paint (red; tan throat, chest, belly and tail underside; ivory horns). Pieces: small amber lens eyes with a pupil; 16 half spikes on the seam from the nape to the spade (the Mirror closes each one); folded wings (arm and 3 finger spars, a flat slab membrane, thumb and finger claws); 4 claws per paw. FAIL: slivers 6.7% (the membrane's thin side walls and the long spar prisms), and 4 z-fighting faces (the claw undersides sat 6 mm above the sole).
- r2: Fix: a lens membrane (rim vertices shared by both sides, so it has no side walls) fanned on rays from the wrist in 8 steps; spars split into 12 cm segments; claw undersides raised. z-fight fixed; slivers still 4.0% (the fan apexes at the wrist, where the rays are 6 deg apart).
- r3: Fix: the scallops become rim points of the outer row instead of their own rays. PASS: 2,408 tris, 6 colours, hit/float/zfight 0.

## Stage 4
- r1: rig with 17 bones + .R mirrors (4 tail bones, horn); the wing is bound rigid to the spine bone, and the other pieces take the body's weights. Clips: idle 48, move 24 trot, attack 32 (neck rears back, then a lunge and bite). All gates PASS, glbcheck OK. Warnings only: 6 tris (0.21%) clip in poses, and 2 open edges on pieces.

Checks: orbit18_sheet.jpg (18 views, EEVEE): every view reads, with no collapse. Separation on the rest mesh: tail to hind legs 0.47 m, fore L-R 0.30 m, hind L-R 0.29 m: PASS. side_by_side.jpg shows the reference views next to the model views.

Triangles: s1 748, s2 892, total 2,408.
Weaknesses: the wings are folded tighter and lie lower than the ref's raised wings, which spread wide in the front view; the membrane has no finger scallop depth; the cream belly plates are plain colour regions; the 2 open edges on pieces are not located.

## Fix pass 1 (review_fable + review_opus, merged)
Fix list (shape first): neck short, head on chest; wings low and flat with one spar; thin thighs and shallow chest; many small back spikes.
- Base change, stage 1 re-locked (old lock kept in before/): neck rings N0-N2 (neck about +45%, a third ring), head sections moved 0.18 m forward and 0.20 m up, horns follow; C0/C1/M0 bottoms 4-6 cm lower (deeper chest and belly); thigh sections +30%. s1 PASS, 768 tris, blueprint IoU 0.514/0.611/0.546.
- Stage 2: the neck-skull loop now sits in N2-H0. Paint rules follow the raised head.
- Stage 3: the wing gets an elbow (upper arm and forearm spars), the wrist is raised to 1.44 m and set out to x 0.44, and the fingers open down and out (the tall front/rear silhouette of the sheet). Spikes go from 16 to 10, about 1.4x larger.
- Stage 4: all gates PASS, glbcheck OK; warnings: 4 tris clip in poses, 4 open edges on pieces. Total 2,352 tris. Separation PASS (tail-hind 0.45 m, fore L-R 0.30 m, hind L-R 0.27 m).
- Not fixed: the membrane is still one fan (no separate arm panel), and the belly plates are still a colour region.

## Fix pass 2 (review2_fable + review2_opus, merged; concept sheet as referee)
Fix list (shape first): head small for the chest; wings small, folded low and rooted over the mid back; legs thin under the heavy chest. Skipped (moves away from the sheet): shorter tail and fewer tail spikes (the sheet has a long tail with many small spikes); a longer neck (lengthened in pass 1, the sheet's neck matches).
- Base change, stage 1 re-locked (old lock kept in before2/): head sections H0-H1 W x1.2, H2 x1.1, horns 2 cm out; fore-leg rings x1.2; thigh rings ry x1.15 (rx x1.03: x1.15 made the inner thighs cross the seam, self-intersection FAIL). s1 PASS, 768 tris, IoU 0.521/0.634/0.540.
- Stage 3: wing root forward to y -1.10, wrist raised to 1.66 m and out to x 0.55, fingers spread to x 0.68-0.74 (taller, wider wings in front/rear, as on the sheet). The wrist sits at y -0.76, not further forward: a wrist over the neck made the rigid spine-bound wing drift in the attack pose (drift FAIL x3; a body-weights bind folded 2.5%).
- Stage 4: all gates PASS, glbcheck OK; warnings: 8 tris clip in poses, 2 open edges on pieces. Total 2,432 tris. Separation PASS (tail-hind 0.46 m, fore L-R 0.26 m, hind L-R 0.25 m).
- Not fixed: wing root is 0.15 m behind the reviewed target (drift limit); membrane still one fan; belly plates still a colour region.

## Density pass 3 (owner: denser main mesh, ~2x tris, same t7 technique)
- Old lock, script and hero/orbit/side sheets kept in before3/.
- Base change, stage 1 re-locked. Half rings 6 -> 14 vertices (Catmull-Rom points on the seam-mirrored ring: 1 in the top and bottom spans, 2 in each side span). Spine stations 23 -> 50: the tail refitted to the sheet's side columns (lower, 15-40 % thicker) with stations about 1.35 radii apart, spade blade T0b/T0c (wider diamond, fuller underside), tail root R0t, rump R0b, belly tuck R2b, belly W0b (deeper, sheet 0.39 m), ribcage M0b, chest front C1b, neck N0b/N1b, brow H1b, muzzle bridge H2b. End caps poked from a centre. Legs: 6-face root strip, 14-vertex elliptical rings, plus forearm, pastern, gaskin and cannon stations (fore 7, hind 8); knee section 1 cm out (inner thigh hit the belly). Horns from the 3 faces of the old skull face, one extra tip station, blunt tips built in.
- r6: FAIL, 4 self-intersecting pairs at the inner hind-leg root; knee section moved out. PASS. r7-r8 (LOCK): slivers at s4 4.0 % then 2.0 % (spade tip and underside, horn tips, tail quads); fixed by the tail spacing, the poked caps, the spade profile and the horn tip station. PASS: 1710 verts, 3416 tris, IoU 0.531/0.645/0.551 (was 0.521/0.634/0.540).
- Stage 2: the s2 r2 tail loops and tip scales are gone (now s1 stations); elbow, stifle and neck-skull rings kept; eye socket inset 0.3 in the middle of the three H0b-H1 stop faces; muzzle flats over H2-H4 incl. H2b. Stage 2-4 r10: all gates PASS, lock assert PASS, glbcheck OK, s2 min IoU vs s1 0.998; warnings: 4 tris clip in poses, 2 open edges on pieces.
- Triangles: body 892 -> 3596, pieces 1540 -> 1520 (eye 48, spikes 140, wing 1012, claws 320), total 2432 -> 5116 (2.1x); all of the increase is in the body loft. Budgets: stage 1 2400-3800, total 3800-6000.
- Checks: separation tail-hind 0.30 m (thicker tail), fore L-R 0.26 m, hind L-R 0.25 m: PASS. orbit18_sheet.jpg, side_by_side.jpg, before_after3.jpg rebuilt.

## Owner fix pass 5 (owner: dragon too bad relative to others)
Old hero, orbit and side sheets, the head close-up, the pass-3 script and the old lock kept in before5/.
Diagnosis (zoomed, against the sheet and bear/golem/crab/knight):
1. Mass: torso and legs thin and spindly next to the sheet's heavy chest, barrel and pillar legs; the front view read narrow.
2. Head: long, narrow horse/goat skull, horns crowding the skull side.
3. Eye: a tiny hexagonal lens in a 3 cm stop face, unreadable at hero distance.
4. Colour blocking: the throat-chest cream band broke into ragged stair-step patches on the neck.
5. Wings: big flat tan sails dominate the hero (not changed this pass).
Fixes:
- Base change, stage 1 re-locked (r11): torso W x1.2 (R0t-C1b), neck N0-N1 +10 %; legs 5 cm out and 20-30 % thicker (rig leg joints follow); head W +12 %, muzzle 2 cm shorter; the eye face takes 70 % of the upper head side span; horns 2 cm out and 1 cm up (r9 FAIL: 8 self-intersecting pairs at the horn root, fixed by that move). s1 PASS, 3416 tris, IoU side/front/top 0.541/0.699/0.525 (was 0.531/0.645/0.551).
- Stage 2: eye socket inset 0.16 (was 0.3): one wide clean socket.
- Stage 3: lens eye r 2.4 cm (was 2.0), 10 sides (round), pupil r 1.1 cm; throat-chest band is one ventral-facing rule (x < 0.12), no stair patches.
- Stage 4 r13: all gates PASS, lock assert PASS, glbcheck OK, hit/float 0; warnings: 6 tris clip in poses, 2 open edges on pieces. Total 5148 tris. Separation PASS (tail-hind 0.31 m, fore L-R 0.30 m, hind L-R 0.28 m).
- orbit18_sheet.jpg, side_by_side.jpg and before_after5.jpg (hero and head, before5 | after) rebuilt.
Not fixed: wings still large flat sails; the neck still reads long for the head.

## Owner crop pass 6 (2 crops: wing, legs)
Old orbit/side sheets, stage 4, script and lock kept in before6/.
1. Wing (front view, wrist/elbow spar): probe found the upper-arm and forearm were two separate butted prisms with differently-rolled square sections, leaving a stepped notch at the elbow; the membrane rim was zero-thickness (shared rim verts), a paper edge. Fix: one bent spar along root-elbow-wrist sharing a mitred ring at the elbow; every membrane rim point split +-6 mm and closed with a wall strip (12 mm edge).
2. Legs (front, wrist/hock): wrist ring (rx 0.114) and hock ring (0.085) were the narrowest rings above flared paws, a pinched band. Fix: fore forearm-pastern rings filled to a steady taper (0.134/0.126/0.122/0.12), hind hock rings 0.10/0.097/0.096. Stage 1 re-locked (r15): s1 PASS 3416 tris, IoU 0.543/0.700/0.525.
- Stage 4 r15: all gates PASS, glbcheck OK; warning 8 tris clip in poses. Separation PASS (tail-hind 0.31 m, fore L-R 0.30 m, hind L-R 0.28 m). Parts unfused.
- orbit18_sheet.jpg, side_by_side.jpg, crop_fix.jpg rebuilt.

## Owner pass 7 (legs too heavy; wing-root hole, owner crop 3)
Old stage 4, orbit/side sheets, hero, script and lock kept in before7/ (with before crops).
1. Legs: passes 5-6 made them 20-30 % thicker and filled the wrist/hock, so they read as pillars. Fix: explicit per-ring (rx, ry); elbow and thigh rings kept, forearm/shin and wrist/hock slimmed 10-20 % (fore 0.190 -> 0.150 -> 0.136 -> 0.128, hind 0.200 -> 0.160 -> 0.120 -> 0.107), rings below the wrist/hock only widen into the unchanged paw (no pinch). Stage 1 re-locked (r16): s1 PASS 3416 tris, IoU 0.539/0.694/0.525.
2. Wing hole: the membrane's leading edge ran straight W-Rf while the arm spar bends W-E-root, leaving an open triangle between spar and membrane at the root. Fix: a last fan ray W-E plus a rim point Q half way down the spar, so the rim follows W-E-Q-Rf inside the spar; that rim is 26 mm thick (inside the 35-40 mm spar) and the Q end is a quad + triangle, not a 5-gon (r16-r19: sliver gate 2.0-2.04 %, fixed by both). Checked at hero, az30, az90, az150 and top: no see-through gap.
- Stage 4 r20: all gates PASS, glbcheck OK, slivers 104/5304, hit/float/drift 0; warning 8 tris clip in poses. Separation PASS (tail-hind 0.31 m, fore L-R 0.30 m, hind L-R 0.30 m). Parts unfused.
- orbit18_sheet.jpg, side_by_side.jpg, fix7.jpg (hero, legs, wing root at the owner's crop angle: before | after) rebuilt.
