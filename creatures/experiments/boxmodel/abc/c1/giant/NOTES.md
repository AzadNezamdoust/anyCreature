# giant, setting c1 "carve + detail" (continues the carve prototype, rounds s1_r01-r03 / s4_r01-r02)

Owner verdict on the prototype: carved overall shape good, lacks detail. Re-lock: the prototype's
stage1_lock.json was deleted (2026-10-03) because stage 1 now adds hand edits on top of carve_base
(designed head, arm gaps, shoulder/hump fixes, moss-border cut). The carve knobs keep plan_roundness=2.5.

## Stage 1
- r04: Critique: az000/az090, the head is the hull's blind spot, a cube with no face. Diagnosis: a visual
  hull cannot see brow, sockets, muzzle. Fix: shrink the hull's head cube (smooth falloff) and boolean-UNION
  a box-modelled head (stacked z rings: chin, underbite jaw, mouth crease, nose, sockets, brow, skull).
  Result: better, 1268 tris, gates PASS. A face exists but the shoulders still run forward to it.
- r05: Critique: az090, a flat slab at head height in front of the shoulders. Diagnosis: the plan view
  sees the fists far forward, so the hull's shoulders extend to y=-1.0. Fix: soft-clamp shoulder verts
  (z>2.2, |x|>0.36) back to the side view's trapezius line y=-0.55. Result: better, head protrudes, 1260.
- r06: Critique: az000, the face reads as horizontal grille slats. Diagnosis: every ring recessed across its
  whole front. Fix: 8 rings, recesses local (sockets at x=0.19, nose wings, angry V brow via per-point dz,
  wide underbite jaw). Result: better, brow/sockets/nose/mouth/jaw read; 1238.
- r07: Critique: az000, arms fused to the torso. Diagnosis: mask_blur+smoothing close the 0.1-0.3 m
  front-view gap. Fix: boolean DIFFERENCE of a slab per side from the reference front mask (torso edge ->
  arm edge, armpit z 2.32 down to 0.5). Result: gap cut (ortho alpha shows it) but too narrow in perspective.
- r08: Fix: widen the slab ~0.05 each way. Result: FAIL triangles 1510 > 1500.
- r09: Fix: carve target_tris (560, 960) to make room. Result: self-intersection 4 pairs (head side x shoulder)
  from _fix_slivers collapses; fix: the sliver repair is now kept only if it folds nothing. PASS 1224;
  arms read with a clear gap front and rear.
- r10: Critique: hero/az135, the hull's back-outer hump corner stands up as a fin. Fix: soft dome cap
  z <= 3.98 - 0.45x^2 - ... over the upper body. Result: better, hump rolls into the deltoids; 1224.
- r11: Fix (for stage 3 colour): cut the moss-mantle border as an edge path (implicit_cut along a wavy
  z-threshold surface, vertices within 3.5 cm snapped onto it), so the moss paint border is clean.
  Result: 1338 tris, PASS, IoU side/front/top 0.951/0.933/0.904.
- r12: locked (1338 tris), then UNLOCKED again: reading the arm sections showed the hull's arm is a 1.3 m deep
  slab (y -0.8..0.5: the side view sees the torso behind the hanging arm). Re-lock logged here.
- r13: Critique: az135/az090, the arm is a slab glued along the flank from behind. Fix: boolean DIFFERENCE
  behind the arm along the reference side view's arm back edge (z 0.2-2.32, x past the gap; the fist bottom
  as a second cutter clear of the feet). A soft vertex clamp was tried first and folded (10 hits); the cut does
  not. Result: better, the arm hangs forward and reads from the back 3/4; 1322 tris, PASS.
- r14: lock round (orbit).
- r14 locked, then UNLOCKED again: stage 2 r1 failed techqa slivers 106 (8%): the booleans' flat cut faces are
  needle fans and the moss cut adds more. Stage 2 cannot change topology to fix them, so stage 1 was re-opened.
- r15: Fix: after the booleans, dissolve coplanar faces (2.5 deg) and beauty-triangulate them, the kit's
  sliver fix kept only if it folds nothing, then the moss cut, then repair_slivers (per needle: flip,
  collapse at either end / middle, or a tangential relax step of one vertex; each try undone if it
  self-intersects or does not reduce the count; seam and moss-border verts stay put). Result: 2 slivers left
  of 510 half faces, 1238 tris, PASS. (Rounds over the 14 cap: forced by the gate, logged.)
- r16: lock round (orbit).
- r17/r18: (re-locks) r17 triangulated the cut quads on the moss border; r18 triangulated every non-head quad
  left by the coplanar dissolve, so repair_slivers sees them (techqa triangulates them BEAUTY otherwise: 42
  slivers in stage 2). Result: 1 sliver left of 524 half faces, 1154 tris. LOCKED at r18.
  Triangles stage 1: 1154.

## Stage 2
- r01: Critique: hero, forearm a straight column into the fist. Fix: pinch the wrist (z 0.85-1.4, scale x/y
  0.84 at z 1.10 about the arm axis). Result: fist reads bigger; IoU 0.993; sliver gate PASS after r18. 1154.
- r02: Critique: az000/hero, the belly is a flat front with no pec shelf. Fix: belly verts (z 1.4-2.0) forward
  0.07, the under-pec row (z 2.22) back 0.05. Result: pot belly + shelf read; IoU 0.993, PASS. 1154.

## Stage 3
- r01: pieces: amber eye lenses + dark slit pupils proud of the sockets, tusks from the underbite jaw, pointed
  ears, nose bulb with dark nostrils, 4 moss clumps + 4 bedded rocks, belt, loincloth front/back, 4 curled
  fingers with stone nails + thumbs per fist, 3 toes with stone nails per foot. Paint: palette = colour_from_sheet
  clusters (hide #697078, moss #69733f, cloth #71604d) + brief stone/leather/tusk/eye/dark; body regions by
  rules: moss on moss_f > 0 (border = the stage-1 cut edge path, so no saw-tooth), mouth crease and soles dark.
  Result: FAIL hit 3 (belt sunk half into the body crosses it along two loops; buckle through cloth+belt).
- r02: Fix: belt 3-10 cm off the surface (32 samples, touches only its pieces), cloth top row inside the belt
  band, lower rows hang flat clear of the body (ray sign bug fixed: flaps were swapped), buckle replaced by one
  stone toggle per hip. Result: PASS, 2730 tris, 8 colours.
- r03: Critique: az090, the back flap hangs 0.4 m off the buttocks (cleared the legs below its hem). Fix:
  clear only the flap's own height; back flap shortened to z 1.04. Result: flaps sit close; PASS, 2730 tris.

## Stage 4
- r03: rig re-fitted to the carved base (arm forward, legs centred), k3 clips at 0.8 amplitude, pieces bound
  with body=. FAIL posed folds 0.59% + toggle stretch 19x (nearest-skin weights reached the arm).
- r04: Fix: the toggles ride the hips bone rigidly (they touch only the belt, so no drift). Result: PASS
  (folds 6 tris, clip warning 8.4% of area: arms through belt/flank in the slam).
- r05: final (orbit), --review, --compare: all gates PASS. Triangles: s1 1154, s2 1154, s3/s4 2730.
  Look vs abc/k3/giant review/1_beauty: stronger hump/shoulder mass and arm gap; face reads (brow, sockets, amber
  eyes, nose, tusks, ears). Weaker: moss is the sheet's dull olive, the belt stands visibly off the belly, the
  loincloth flaps read as thin rods in profile, toes are small.

## Team repair pass (Fable AD notes review/ad_notes_team.md; rounds r19-r40; stage 1 stays locked)
- r19: baseline, all gates PASS (2730 tris), clip warning 8.4%.
- r20 (item 1 belt): Critique: hero/az000, the belt is a wire hoop 3-10 cm off the belly. Diagnosis: one centre sample per
  column + a fixed 3/10 cm offset, band 0.12 tall. Fix: band 0.24 tall x 0.07 thick, 28 columns x 6 rings, each row
  sampled at its own height 1.4 cm proud, front dipping 0.10 m, one stone toggle front-centre. Result: FAIL hit 5 (the
  band's faces cut the belly between rows).
- r21: Fix: each row clears the fullest skin within +-0.07 m in z and half a column in angle. Result: PASS; the band hugs.
- r22: Fix: the toggle is seated on the band's own outer face (it was buried), 0.19 m wide. Result: PASS, reads in az000.
- r23 (item 2 moss): Critique: back34/top, one dull olive sheet, pebbles. Diagnosis: sheet_palette snapped moss to the
  sheet's #69733f; rocks r 0.17-0.24 on top of 4 pancake clumps. Fix: moss keeps the brief's #6f8f3a; 5 clumps
  0.3-0.4 m, 0.10 proud; rocks 0.46-0.54 m, 40% sunk, one on each shoulder cap. Result: PASS, green reads.
- r24: Fix: rocks to 0.52-0.60 m with a flatter top (0.78). Result: FAIL hit 2 (rocks cut two clumps each).
- r25: Fix: rocks and clumps re-laid so they do not overlap (4 clumps, 4 rocks per side). Result: FAIL z-fight 6.
- r26/r27: sinking the clump rims and moving two clumps did not clear it; r28 debug print: the clump at
  (0.98, 0.78) lay flat on a skin ridge. r29/r30: Fix: that clump to (1.06, 0.70, 3.05). Result: PASS, 2730 tris.
- r31 (item 3 loincloth): Critique: az090, both flaps are sticks 0.2 m off the body. Diagnosis: every lower row hung at
  one plane 0.10 m in front of the most forward point below the hem. Fix: flaps 0.07 m thick, each row 3 cm off the
  fullest skin at its own height, front flap rows widened (0.80/0.76/0.68/0.58 m). Result: PASS.
- r32 (item 4 belly, stage 2): Fix: belly verts z 1.3-2.0, |x| < 0.6 a further 0.13 m forward (falloff to 0 at 1.1 /
  2.15 and by |x| 0.8), the under-pec row 0.03 back. Result: PASS, IoU min 0.991; the belt and flap re-fit by sampling.
- r33 (item 5 toes): Fix: three abutting toes 0.24 m long, 0.15-0.18 m tall, six-sided rounded section, chamfered
  front top, stone nail over the front 0.08-0.10 m. Result: PASS, 2922 tris; new stretch warning (8 tris, 2.42x, toes).
- r34: Fix tried: toes rigid on the nearest bone to remove the stretch. Result: FAIL drift 6; reverted (r35, body=).
- r36: Fix: nail paint per toe (the inner toe sits 0.1 m back and was left hide). Result: PASS, three toes read.
- r37 (should-fix ears): laid back along the skull at half size. Result: PASS, no cat ears in az000.
- r38 (should-fix attack arc): slam upper arm raised 13 deg and out 10: clip warning 9.5% -> 9.7%, no gain; reverted.
- r39: final (orbit) + --review: az090 in the packet still showed the flaps as slabs off the thigh (rows eased only
  half way in below the belly). r40: Fix: rows ease in 80%. Result: flaps lie on the thigh/buttock; all gates PASS,
  glbcheck OK, --review, --compare. Triangles: s1 1154, s2 1154, s3/s4 2922. IoU min 0.991.
  Left: clip warning 9.75% of area (the wider belt rides the bending waist; arms in the slam), stretch warning 8 toe
  tris; no hide strip down the centre of the back (the moss border is the stage-1 cut); should-fix face paint and
  knuckles not done.

## Team repair, second pass (verifier review/verify_team.json: items 2-5 PARTLY/NOT; rounds r41-r51)
- r41: baseline, all gates PASS (2922 tris).
- r42 (item 2 moss): Critique: top pair, a smooth green sheet, no hide down the back, mild lumps. Diagnosis: body_rule
  paints all of moss_f > 0; clumps 0.15 proud. Fix: a hide strip down the centre of the back (stage-3 paint only,
  the cut stays), clumps 0.24 thick; belt columns 28 -> 20 to free triangles. Result: FAIL hit 1 + folds 0.53%
  (the coarser belt). r43: belt back to 28 columns: PASS. r44: strip widened (0.30 m half-width at the top, 0.60 low):
  hide reads down the spine with a moss diamond in the middle, as the reference rear; clumps read as lumps. PASS.
- r45 (item 4 belly, stage 2): Critique: az090, chest to knee nearly straight. Fix: a further cosine bump, 0.12 m
  forward at z 1.62 (zero at 1.12 / 2.12, full to |x| 0.65). Result: the belly stands in front of the arm and thigh
  line in az090; IoU min 0.982; PASS. Total belly move 0.32 m at the peak.
- r46 (item 3 loincloth): Critique: az090, both flaps are straight sticks off the body. Diagnosis: every column of a
  row sat at the row's fullest point, so the flap was a flat board. Fix: each column drapes on the skin under it
  (40% bridged to the row's fullest point). r47: flaps widened so the edges wrap the thighs/hips (front 1.0 m at the
  belt, back 1.36 m). Result: PASS; a skirt lying on the body in hero/back34; in az090 it follows the belly and
  buttock curve (still seen edge-on there: a cloth 0.07 thick is a narrow stroke in pure profile).
- r48 (item 5 toes): bigger toes: FAIL hit 2. r49 probe: the carved foot is a wedge whose front overhangs the sole by
  0.45 m above z 0.2, so the toes sat hidden under it. Fix: each toe runs low (0.12) under the overhang and rises
  to 0.22-0.27 m tall, 0.30 m in front of the wedge, 0.21-0.25 wide, abutting. Result: hit 0, the stretch warning
  is gone, 3066 tris (over). r50: one toe ring dropped: 2994 tris, PASS; three big toes with stone nails read in az000.
- r51: final (orbit), --review, --compare.
