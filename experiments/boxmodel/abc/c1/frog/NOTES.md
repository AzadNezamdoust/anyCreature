# frog, setting c1 "carve + detail"

Stage 1 = carve_base (visual hull of reference/) with hand edits of the carve input (masks and a 3D occupancy
cut/union, all keyed in carve_mask.key), then locked. Pattern: abc/c1/wolf (side-mask redraw).

## Stage 1
- r01: carve_base defaults. 1084 tris, IoU .97/.93/.94; FAIL 2 self-hits. Critique: toes and fingers carve into
  spikes (thinner than the 3.3 mm voxel blur), the staggered near/far forelegs fuse into one 7 cm block, the lower
  body is a crate (front view extrudes the legs along Y). Fix: mask hand edits (MASK): toes/fingers cleared in all
  views (stage-3 pieces), side view redrawn as ONE foreleg + hand pad, front view below z 0.135 redrawn (round
  belly, slot to the foreleg column, thigh + foot), top view hand rectangle.
- r02: PASS 1064 tris, IoU .889/.854/.856. Critique (az090): the flank between fore and hind legs is a flat wall as
  wide as the legs; the reference belly is a round ball. Vertex squeeze tried: 86 self-hits (decimated tris fold).
- r03: Fix: a 3D cut of the hull occupancy (BELLY: between the legs below z 0.15 nothing outside the front belly
  profile), applied by wrapping carve.hull_field at runtime in this program (kit file untouched). PASS; az090 shows
  the belly tucked in between the legs.
- r04: Critique: eyes are low bumps (front/side views: the eye is thinner than the mask blur) and the brief's
  silhouette cue is big bulging eyes. Fix: a turret ball unioned into the occupancy (TURRET r 0.030). PASS 1104.
- r05: turret r 0.034, centre z 0.266: turrets stand above the skull in az000. PASS 1096 tris.
- r06: Critique (az000): chest is a flat front plane with a ledge. Fix: knob plan_roundness=2.5. Chest rounder,
  forelegs read as columns; FAIL 2 self-hits.
- r07: Fix: target_tris (900, 1400). PASS 1132 tris.
- r08: Critique (az090): the hind leg is a box with a vertical front face; the reference shows a round knee over a
  long foot lying forward on the ground. Fix: side mask: wedge cleared under the knee, foot paddle drawn
  (y 0.035-0.19, z 0-0.03). Foot reads; FAIL 2 self-hits at the belly-cut front edge (0.063, -0.033, 0.088).
- r09: Fix: belly-cut fade 1.5 -> 2 cm. PASS 1162 tris, IoU .838/.832/.858 (blueprint keeps the far legs and toes).
- r10: LOCK (with orbit). 1162 tris, edge sha256 6ce0b95fd7ad50cd. Remaining for stage 2: flat face front with a
  recessed band under the snout, no mouth line, boxy hand pads.

## Stage 2 (lock 6ce0b95fd7ad50cd)
- r01: three colour-border planes bisected into the base, logged as loops (jaw = the mouth line, throat = the side
  cream border, flank = the front cream border); verts within 4 mm snap onto each plane first. PASS, IoU .999,
  slivers 30 (2.0%, at the limit).
- r02 (run with the stage-3 previews s3 r02-r03): Critique (az000 colour): the throat/chest front is a stair of
  horizontal terraces. Fix: 8 Laplacian passes on the chest-front verts (seam x locked). Then: the throat sides sat
  back under the jaw (dark shelf): verts brought forward onto the seam's front profile (first try moved 0 verts:
  0.9 x^2 / 0.1 rounded back 6 cm, not 6 mm; fixed). PASS, IoU min .989, slivers 26 (1.8%). The shelf under the
  jaw is softer but still reads dark in workbench light (the reference profile itself recedes there).

## Stage 3
- r01: paint by the cuts only (skin / cream). Cream throat + belly on edge-path borders. 1302 tris.
- r02-r03: stage-2 fixes above, previewed.
- r04: pieces: gold eye balls (12-sided, cap rings) on the front-outer face of each turret with a horizontal
  black pupil bar (paint by normal), a black square-tube mouth line following the jaw cut's edge path across the
  seam (one piece, half sunk), 4 splayed fingers with round pads per hand, 5 long hind toes with pads and web slabs
  (k3's toe/hind_toe/fan/slab), spots = whole carve triangles painted dark green (6 top + 3 flank centres).
  PASS, 2842 tris, 6 colours. Reads as a frog in every view.
- r05: Critique: spots invisible in workbench (lost in the facet shading). Fix: radii x1.2 (52 faces). Marginal.

## Stage 4
- r01: k3's rig and clips (root/chest/head/jaw/eye/tongue1-2, 3-bone legs, roll auto, foot verts rigid to foot,
  tongue bones non-deforming for the skin) on joints read off this base (J); tongue piece added (6-sided tube,
  root rings first, pad tip 0.4 mm inside the snout front at the mouth line). All gates PASS; WARN stretch 14
  (tongue), clip 26 tris (0.26%). 2934 tris.
- r02: spots as 4 big + 2 flank blobs: they merge into a dark X saddle (top). Worse; reverted.
- r03 (final, orbit): all gates PASS (hit 0, float 0, z-fight 0, slivers 0.9%, fold-overs 0, drift 0, lock PASS,
  min stage-2 IoU .989, glbcheck OK, orbit holds). WARN stretch 14 (tongue only), clip 0.26%. --review, --compare.

## Totals
- triangles: s1 1162 (lock 6ce0b95fd7ad50cd), s2 ~1300, s3/s4 2934; 6 colours.
- rounds: s1 10, s2 2, s3 5, s4 3.
- vs abc/k3/frog: rounder, heavier body that follows the sheet (pear belly, chunky folded thighs, feet lying
  forward), a continuous black mouth line, eyes on real turrets. Weaker: noisy decimated facets on the flanks and
  thighs (k3's planes are cleaner), spots read only in EEVEE as patches, the pink tongue tip shows at rest.

## Team repair pass (notes review/ad_notes_team.md, R0 = 11)
- r11 baseline (s4): all gates PASS (no item 0).
- s1 r12 (must-fix 1, STAGE-1 UNLOCK): Critique: rear is a crate (az180 square haunches, vertical outer walls,
  flat back). Diagnosis: front mask x top mask extrude the thigh polygon along Y to the rear wall. Fix: REAR, a 3D
  cut of the hull occupancy behind y 0.035 (rear_cut, the BELLY pattern): nothing outside body egg (plan half-width
  0.11 tapering to the rear, top falling 0.235 -> 0.08 at the rear wall) U thigh lobe ellipse (x between xi 0.095->0.07
  and xo 0.16 at the knee / 0.142 at the hip / 0.10 at the rear, z 0.078 +- 0.08) U foot paddle (x 0.105-0.185,
  z < 0.032). Side mask untouched. Result: az180 round dome, two rounded lobes, light between belly and thigh at
  the floor; PASS 1160 tris, 0 self-hits. Old lock kept as stage1_lock.pre_team.json.
- s1 r13: LOCK, 1160 tris, edge sha256 ae4fe2d3cdd67796. s4 r14: stages 2-4 rerun on it, all PASS, IoU min .989.
- s4 r15-17 (must-fix 2): spots = 6 disc pieces per side (6-sided, r 1.7 cm, every vertex projected onto the skin,
  sunk apex; 3 dorsal row, 2 flank, 1 thigh), painted spot triangles removed. r15 z-fight 16 (1 mm lift) -> 2.5 mm;
  one flank disc's rim ray hit the far side (-249 mm) -> ray distance capped, disc moved up. Budget: hind-toe pads
  3 rings -> prism, eye 12 -> 10 sides. PASS.
- s4 r18 (must-fix 3): eye ball r 0.025 -> 0.037, centre (0.089, -0.116, 0.288): tops the turret by ~1/3 its
  diameter, breaks the skull outline in az000/az090. Pupil bar unchanged. PASS.
- s4 r19-20 (must-fix 4): mouth tube continued on the jaw plane (cast in from +X) to y -0.075 (under the eye back).
  Tongue sunk 8 mm in the mesh -> FAIL float (no contact); instead idle/move key tongue1 back (bone -Y), 14 mm in
  r28 (8 mm left a pink hairline at idle frame 1). Attack f012 still lashes.
- s4 r21-25 (must-fix 5): new stage-2 cuts 'arm' (y -0.042, behind the foreleg) and 'side' ((-0.03,0.19) ->
  (0.035,0.02)); cream also = jaw ^ arm ^ side. Fingers lose their mid ring (budget). r24 tried the edge further
  back: 6 self-hits and cream on the foot front, reverted. Result: one cream edge from the throat down behind the
  foreleg to the belly; partly done: the shoulder top between throat stripe and flank patch stays green, and the
  thigh front wall is green (not on an edge path).
- s4 r26: should-fix toe pads +20% radius. r27/r28 final (orbit): all gates PASS; --review, --compare.
- Totals: s1 1160 (lock ae4fe2d3cdd67796), s3/s4 2994 tris, 6 colours.

## Team repair, second pass (review/verify_team.json: 1 NOT, 2 and 5 PARTLY, tongue stretch), R0 = 29
- s1 r29 (item 1, STAGE-1 UNLOCK again; first-pass lock kept as stage1_lock.pre_team2.json): Critique (az180,
  back34): thighs are still slabs with vertical outer walls as tall as the belly, no groove at the floor.
  Diagnosis: the thigh lobe in rear_cut is an upright ellipse (rx 3.5 cm, rz 8 cm) = two vertical walls; the body
  egg's bottom (bzb 0.09) reaches the foot paddle. Fix: lobe section tilted 28 deg (top leans in against the body,
  outer face slopes down and out), the cut starts at y 0.02 (whole thigh), bzb 0.07, foot inner edge 0.11.
  Result: az180 = dome + two sloped lobes, a dark notch between belly and thigh; side IoU .842 (was .838). PASS.
- s1 r30: LOCK 1244 tris, edge sha256 92218c26c2f97e90. s4 r31: FAIL s2 2 self-hits, FAIL 3080 tris.
- s4 r32 (item 2): spots = one planar regular hexagon each (plane fitted to the skin under the rim, lifted clear
  of every facet, sunk apex cone below) instead of per-vertex projection (uneven sizes, slivers under the skin).
  Budget: hind toes lose the mid ring. s2 r33-34: the hit was the throat move at the shoulder (x ~0.105) folding
  one tri on the new base; the move now fades out over x 0.085-0.105. PASS, IoU min .99.
- s4 r35 (item 5): 'side' cut dropped; the flank patch = arm ^ throat ^ jaw up to the belly/thigh crease: one
  straight diagonal edge (the throat plane's edge path) from the mouth corner to the thigh, no green wedge. Two
  spots moved off the y 0.03 step (hover 14 -> 6 mm).
- s4 r36 (tongue stretch): graded weights over the four ring gaps behind the pad, lash 0.085/0.057: worst 2.76x
  (was 5.55x). r37 (orbit): two pink pixels at az000 idle f1. r38/r39 TONGUE_IN 24 / 18 mm:
  FAIL drift (tongue leaves the body); back to 14 mm and the pad's wide rings narrowed 14.5 -> 12 mm instead.
  r40 final (orbit): all gates PASS; --review, --compare.
- Totals: s1 1244 (lock 92218c26c2f97e90; the 900-1400 gate is the stage-1 budget, the total budget is 500-3000),
  s3/s4 2944 tris, 6 colours. Left: thigh lobes are angular wedges, not round; green shoulder between throat and
  flank cream; clip warning 0.36%.
