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
- restored to the solo carve + detail version (orchestrator, 2026-10-05): both blind reviewers preferred it over the team pass. The team version is commit 923ec33.
