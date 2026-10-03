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
