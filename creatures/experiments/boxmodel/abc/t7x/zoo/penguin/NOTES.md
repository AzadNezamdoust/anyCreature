# emperor penguin (t7x zoo, workflow v2)

Sheet: refs/gpt/v3/penguin/sheet_1.png (2x2). refs.py --height 1.1 --thresh 14: at the default threshold 40 the cream
belly (241,235,226 on 253 white) dropped out of the side trace (the front edge ran through the belly); 14 traces it.
The plan view is not a true ortho (top length 1.66x the side): blueprint.json's top outline removed; side marks eye /
shoulder / beak tip added by hand. Side wins for proportions.

**Identity cue (emperor penguin, not king penguin / auk):** a tall upright egg body with a narrow black hooded head, a
long slim slightly decurved beak, flat flippers hanging close along the flanks, a white front wrapping far back low on
the body, an orange ear patch flowing into a pale-yellow upper chest, short legs with broad black webbed feet, a stiff
tail wedge touching the ground. All of it except the colours is in the S1 loft.

Build (template: zoo/owl colour/piece code + zoo/imp vertical loft): one loft of 17-vertex half rings, 25 stations
bottom seat -> crown (front seam down the belly, back seam down the back; head rings tilt so the front seam rides the
chin and the beak root). Colour borders on placed loops: vertex column NB = 9 of every ring sits at the border angle
TB(z) (125 deg low -> 77 deg at the shoulder -> 96 deg at the ear patch), so the white/black border is an edge line.
Flippers: 2 spans x 3 faces of the shoulder side (C0 inner -> N0 outer: the shoulder ring runs on into the flipper top),
9 flat rounded-box sections, the plane turned 15 deg (front edge out). Legs: 1 span x 4 faces of the flat bottom seat
(R0-R1) + hug ring, pants, ankle, foot block. Beak: the front-seam face of the H1-H2 span (seam walls removed),
4 hexagonal sections. Tail: the 2 back-seam faces of the R2-R3 span down to the ground.

## Stage 1
- r00: FAIL self-intersection 8 pairs at the flipper inner root (0.16-0.18, 0-0.07, 0.77-0.79); 2396 tris, IoU
  side/front 0.931/0.912. Reads as a penguin from every view already. Diagnosis: the first flipper section's inner
  side sat on the C0 root ring (x 0.168 at z 0.80) and the next ones ran down the body side. Fix: flipper sections
  1.5-3 cm further out (inner face >= 1.2 cm off the body).
- r01: PASS, 2396 tris, IoU 0.931/0.892. Critique (az090, hero): the flipper top is a flat shelf 4 cm wider than the
  sheet's shoulder (sheet: flipper outer edge 0.198 at z 0.80, it IS the shoulder there). Diagnosis: body shoulder
  rings W 0.168-0.20 + flipper outside them. Fix: shoulder rings narrower (R13..N0 W 0.193/0.173/0.156/0.146/0.138),
  flipper hugs them (rot 20 -> 15 deg), flipper width narrow at the root (5.5 cm) widening to 7.5 cm mid (sheet).
- r02: PASS, IoU 0.931/0.910. Critique (az090 crop): a dark notch at the flipper root's back-top corner. Diagnosis:
  S1's corners pulled in to 0.5 (a lens corner) right at the root. Fix: corner 0.85 (S1) / 0.7 (S2).
- r03: FAIL 2 pairs (the rounder back-inner corner touched the body). r04: S1 1.2 cm out: PASS, notch smaller.
- r05: Critique: the notch stays: S1's back edge (y 0.063) sat 3-4 cm in front of the root's back column (y 0.094-0.108),
  so the back wall turned forward. Fix: S1 centre y 0.03, half width 0.066 = the root's (an unshrunk first ring).
  Result: notch gone (az090 crop); the top reads as a box shoulder pad from the hero view.
- r06: Fix: S1 lower and in (z 0.778, half thickness 0.021, dz -0.012): the top slopes ~46 deg like the body's own
  shoulder. Result: the flipper top blends (hero crop); IoU 0.931/0.911.
- r07: Critique (hero crop): the beak root is a collar: a 1.6 cm hug wall then a cone 2 cm narrower than its 2-column
  root (6.4 cm wide). Fix tried: hug (0.016, 0.92), first section wider: still a step.
- r08: Fix: the beak from ONE front column (3.2 cm wide root = the sheet's slim beak base), hexagonal sections, hug
  (0.008, 0.97). Result: the beak leaves the face cleanly (hero, az090 crops), IoU 0.932/0.911, 2340 tris.
- r09: Critique (az180, az090 crops): the tail is a thin spike. Fix: tail sections wider (half width 5.6 -> 1.2 cm).
- r10: Critique (az090 crop): the tail leaves the rump high and stands off it (a fin, 11 cm behind the rump at z 0.10;
  the sheet's tail is a wedge under the rump). Fix: tail root on the R1-R2 span (the rump bottom), path closer, R2/R3
  back seams 1 / 0.6 cm further back. Result: side IoU 0.932 -> 0.944.
- r11: Critique (hero/az000 crops): the feet are 2.4 cm boots. Fix: foot rings flatter and wider at the toes (lpos taper
  0.35-0.4: front half width x1.4). Result: flat webbed paddles; IoU 0.942/0.913.
- r12 (LOCK): 1180 verts, 2356 tris, edge sha256 acb380ea155390d1; IoU 0.942/0.913; harness orbit holds.
- r13: per-face tags (part/span/column) recorded in stage 1 for the colour borders (lock unchanged).
- r14 (RE-LOCK, old lock in before_relock1/): S2 r01 failed slivers 2.6% (yellow along every flipper rim: the rim
  faces were 4-6 mm wide on 8 cm). Fix: flipper corners 0.5 -> 0.75 of the half thickness, corner b 0.94 -> 0.86 of the
  half width: wider rim faces. Lock 95b9cfba4561963e; IoU 0.942/0.918.
- r15-r16 (trial, lock e27df376 in before_relock2/): leg root from 2 spans (R0-R2) + hug 0.85 -> knife 154 deg / 2.1 r
  (the tilted root ring met the level pants ring: the inner wall folded back). Reverted.
- r17 (RE-LOCK, the final S1): S4 r01 probe FAIL thigh knife 128 deg / 1.26 r; S4 r02 fillet (S2 Laplacian at the leg
  root) made it worse (135 deg, strip 1.5 r), dropped. Diagnosis (own fold scan of the GLB): the folds ring the leg at
  z 0.069, the pants ring only 4 mm below the seat's inner (R0) edge, so the inner wall was nearly flat. Fix: seat R0
  0.072 -> 0.080, hug (0.008, 0.92), pants 0.058 -> 0.050, ankle 0.034. Lock 596dc412c3e1c2e3, 2356 tris, IoU 0.941/0.916.

## Stage 2
- r01: flipper shoulder + wrist loops, ankle loop, neck loop (logged), eye socket inset (the face a side ray hits at the
  sheet eye; 28x38 mm, its floor 5 mm in). FAIL slivers 2.6% -> S1 r14. r02: PASS (slivers 0.2%, IoU vs S1 1.0).

## Stage 3
- r01-r02: paint: tags lost (a stage-1 bmesh face layer does not survive the kit's lock/commit path: 649/649 untagged)
  -> r03: tags from the nearest stage-1 face centre (KD tree): 0 untagged. FAIL z-fighting 10 (the toe undersides 1.5 mm
  above the sole). r04: toe undersides at 5 mm: PASS (7 colours, 2776 tris).
- r05: Critique (colour renders): the chest yellow is a strong collar and the ear patch a tall 4-column slab reaching
  far back. Fix: yellow paler (#f4e1ad), patch 3 columns, 2 on the neck span (a narrow tail into the throat yellow).

## Stage 4
- Rig: hips/spine/chest/neck/head, wing.L + wingtip.L (flippers, so the membrane check runs on them), thigh.L + foot.L,
  tail0 (short) + tail1. Clips: idle 48 (breath, neck turn, flipper settle), move 33 (waddle: hips roll 6 deg, feet
  shuffle, flippers out 12-16 deg), attack 32 (rear up flippers raised 30, beak jab).
- r01: all kit gates PASS; probe FAIL thigh knife 1.26 r (wings, tail, eyes, membranes PASS). r02: fillet worse.
  r03: 2-span root worse (see S1 r15-16).
- r04: probe PASS on all 5 roots (thigh knife 0.8 r at 100 deg, strip 0.96 r; wing knife 0; tail knife 0), eyes PASS
  (0.42/0.86/0.66, 26 mm = 0.064 head), membranes PASS (flippers p10 18.4 mm), all kit gates PASS.

## Owner-style review (s4_r04: round sheet, orbit18_sheet.jpg, junction crops A/B/C)
Visible flaws: (1) az000 / h000: a black speck (one quad) in the white inner face of each flipper near the top, and the
white inner face runs up into the shoulder band (C crop of wing.L shows it as a white sliver in the armpit); (2) the
toes read as thin bird talons (hero, close-up 2), the sheet has thick black webbed toes; (3) the ear patch is a
blocky 3-column rectangle (sheet: a comma) - taste, kept; (4) from below (-45 az180, tail crop C) a dark pocket where
the tail underside meets the rump - probe knife 0, seen only from below, kept. No slit, hole, white speck, knife fold,
seam strip, pinch or poke-through visible at the flipper, leg or tail roots; the eye reads as a small round brown
lens in a clean socket in all three eye crops. Separation: legs 13.9 cm apart, flippers 3.7 cm off the torso. PASS.
- fix 1 (s4 r05 / s3 r06): flipper paint from the face normal (inward > 0.35) and below z 0.70 (the S2-S3 ring), not
  from the inherited tag: the loop-cut half that inherited a rim tag was the speck. Result: specks gone, the white
  starts on a ring line under the black shoulder band (az000 crop).
- fix 2 (s3 r07): toes 2.6 -> 3.6 cm wide, 1.4 -> 1.7 cm tall: thick webbed toes (hero crop).
- final (S4 r06 with orbit + --junctions, lock 596dc412c3e1c2e3): ALL GATES PASS - S1 2356 tris (IoU side/front
  0.941/0.916), S2 lock assert + IoU 1.0, S3 7 colours / 2776 tris, S4 clips + weights + lock + glbcheck OK, tech QA
  hit/float/zfight/drift/fold-overs 0, slivers 0.3%; probe PASS on all 5 roots, eyes PASS, membranes PASS (p10 18.4 mm).
  --review and --compare run (side_by_side.jpg); the sheet comparison is side_by_side_sheet.jpg (checks.py).
Triangles: S1 2356, S2 2468 (loops + socket), total 2776. Rounds: S1 18 (r00-r17; 2 re-locks logged), S2 2, S3 7, S4 6.
Residual: the head is narrower than the sheet's from the front; the ear patch is a rectangle, not the sheet's comma;
the chest yellow is a uniform band (no fade); the tail meets the rump with a dark pocket seen from below.
