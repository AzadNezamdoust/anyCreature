# Griffin (zoo new20), t7 hand box model, workflow v2

Sheet: `refs/gpt/v3/griffin/sheet_1.png` (2x2: side, front, rear, top). `kit/refs.py --height 1.5`: length 2.245 m, width 0.83 m.
Reference notes:
- The side trace splits at the crown (white feathers on a white ground) and the plan-view head trace is ragged for the same reason; blueprint.json is kept as traced (IoU is info only, non-cage build), the head is read off `side.png`/`front.png` by eye on a metre grid.
- The top view is 1.11x longer than the side (refs warning): the side wins for every y; the top only gives widths.
- The sheet's side shows a walking stance (far hind leg forward); built symmetric on the near leg (paw y 0.33-0.60). Rear view puts the hind paws at x +-0.25, wider than the front view suggests; the rear view wins.

**Identity cue:** an eagle's head on a lion's body: big white domed head with a hooked yellow beak over a white feather ruff that hangs to the chest; eagle forelegs (feathered trousers, yellow scaled tarsi, four-toed talons); lion hindquarters (round haunch, hock, cream paws) and a tufted lion tail; wings folded along the back, tips past the rump. Not a bird (four legs, lion rump and tail), not a lion (head, ruff, talons, wings).

## Stage 1
- r01: first loft (40 stations, 13-point half rings = 2x density on flat profile midpoints; legs extruded from 3 spans x 3 faces of the lower flank, 12-vertex rounded-box rings, a transition ring 45 % toward the first leg section). FAIL 44 self-intersecting pairs at the foreleg top front (0.21, -0.665, 0.63): the region C0b-C2 sat behind the leg, so the leg front ran up into the chest. 2788 tris.
- r02: fore region C1-C3, hind region R0b-R2 (centred over the legs). FAIL 50 pairs: the leg's front-top (y -0.70) still under the hanging chest (N0 bottom).
- r03: fore top sections back/slimmer (ry 0.10). FAIL 44 pairs at the inner front corner: the first leg section (z 0.64) sat above the region's lower edge (z 0.56), the inner wall folded up into the belly.
- r04: first leg sections below the region (fore z 0.55, hind z 0.555). FAIL 18: the leg's inner side (x 0.09-0.11) under the belly that the region (points 7-10, inner edge x 0.16) did not include.
- r05: regions on points 8-11 (inner edge x 0.08, at the leg's inner side). FAIL 8 at the foreleg's inner rear corner over the C0b belly.
- r06: fore top ry 0.09, centre y -0.595. FAIL 4 under the tail root: T5's bottom seam point sat forward of R0t's (a fold).
- r07: T5 a tilted root ring behind R0t. PASS, 1396 verts, 2788 tris. IoU side/front/top 0.616/0.625/0.658 (wings, tuft, feet and the far hind leg come later or are not built).
- r08: HEAD profile with a flat cheek plane and a domed crown, head stations 8-20 % wider (the head read as a narrow hood). PASS, 2788 tris; small change in the views, the colour pass carries the head/ruff split.
- r09: lion hind leg off the sheet's near leg (deep thigh from buttock to stifle, stifle forward, hock back); hind region R0-R1b. PASS.
- r10: HAUNCH profile (low wide lower flank) on R0-R2. PASS; rear view still showed the thighs as posts outside a narrow rump.
- r11: thigh centre in (x 0.20 at the top, 0.24 at the hock), haunch W +0.01-0.015: rear view now reads as round haunches over the legs. PASS.
- r12 LOCK: 1396 verts, 2788 tris, edge sha 85b41efc9e42e17d. Orbit holds.

## Stage 2
- r01: eye face (H2-H3, points 6-7) opened 45 % along the ring, one inset (0.2) sunk 12 mm, brow point over it out/forward 12 mm. All s2 gates PASS, IoU vs s1 0.999, slivers 0.4 %. 2804 tris.

## Stage 3 / 4 first pass
- s4 r01 (first full build: lens eye, folded wing slabs 15 stations x 5-point arc, 42 mm thick, eagle feet = parts bird_foot, lion claws, tail tuft, rig + clips): all kit gates PASS (4022 tris, 7 colours, posed fold-overs 0.20 %). Junction probe FAIL: tail0 knife 2.0 r at 106 deg (under the tail root, crop C); wing roots seam strip 1.23 r (crops: a blunt box end of the wing standing out of the shoulder in front of the ruff, plus a thin crease face on the ruff behind the neck); eyes side 0.29 < 0.40. Shoulders PASS (knife 0, max 88 deg), thighs PASS (0.94 r).
- s3 r01: eye look direction less forward. Eye side 0.28: no change -> not the angle.
- s3 r02: Critique: the lens sat 19 mm deep, the socket walls hid it from the side. Fix: socket 12 -> 7 mm, lens 3 mm proud of the floor. Eye PASS front/3q/side 0.58/0.85/0.59, diam 44 mm (10 % of head).
- s3 r03: Critique: the wing's front end is a box standing out of the shoulder in front of the ruff (wing crops A-C). Fix: root station 10 cm forward and inside the ruff (y -0.60). Crops: the wing now comes out from under the ruff, no box end. Strip 1.16 r remains, on the ruff crease (body), not the wing.
- s3 r04: Critique: the white bib ran down the foreleg tops, and the wing colour border stepped across faces. Fix (one colour pass): bib limited to |x| < 0.17 below z 0.82; wing coverts/primaries by station and arc span (border on edges); tan lighter #d29e60.
- s3 r05: Critique: the tail tuft read as a small dark knob (sheet: a 0.45 m brush). Fix: tail_tuft kind brush, 0.46 m, radius 0.12, base one station earlier. Reads as the sheet's brush. 4034 tris.

## Stage 1 re-locks (junction fixes inside the dense mesh; old lock in before_relock1/)
- r13: Critique: tail0 knife 2.0 r at 106 deg under the tail root (s4 r01 crop C). Diagnosis: R0t (W 0.09) a narrow step between the stem and the 0.19 rump, its bottom seam above the stem's line. Fix: R0t W 0.13, T5/R0t/R0 bottoms on one line. PASS 2788.
- r14: nape top seam spread (C1b-C3). LOCK. s4 r02: wing strip unchanged 1.16 r; tail knife now 2.26 r / 140 deg -> the probe's knife was not at the tail ring.
  Located with a fold script on the GLB: the folds sit in the groin behind the thighs (x 0.07-0.10, z 0.57, y 0.45-0.575: the hind region's inner and rear edges), the thin strip triangles at the back of the neck (x 0.16, y -0.55..-0.61, z 1.07-1.19, 21-24 mm wide, 31-33 deg crease).
- r15: Critique: thin quads at the back of the ruff (wing-root strip). Fix: the nape's top seam bulges back like the sheet's ruff, C1b-H0 top points ~0.055 apart (were 0.036-0.05). PASS.
- r16: thigh back no further than the R0 ring. s4 r03: wing roots PASS (strip 0), tail 1.46 r / 118 deg (still the groin).
- r17-r20: Critique: 140-150 deg crease where the belly between the hind legs meets the thigh's inner wall (crop C, fold script). Fix: the first thigh ring lower (z 0.49) with its inner side out to x 0.115 and its back in line with R0, so the groin slopes into the leg. Fold script on s1: max 91 deg over 0.07 m. r21 LOCK; s4 r04: tail PASS (max 76 deg), thigh FAIL 1.48 r / 133 deg along the R1b ring = the thigh's front wall forward of the 3-span region.
- r22: Fix: hind region 4 spans (R0..R2 = the thigh's full depth; 14-vertex hind rings). s1 folds max 83 deg. r23 LOCK: 1432 verts, 2860 tris, edge sha 4836cc132bd50f54.
- s4 r05: every kit gate PASS (4106 tris, 7 colours, slivers 0.3 %, posed fold-overs 0 %, drift 0, hit 0, float 0); junction probe PASS: shoulders knife 0 (max 88 deg) strip 0.78 r; tail0 knife 0 (max 76 deg); thighs knife 0 (max 78 deg) strip 0; wing roots knife 0 strip 0; eyes 0.57/0.84/0.58, diam 10 % of head; wing membrane p10 20.6 mm (floor 9.2). Posed clip 0 % everywhere.

## Owner-style review (zoomed junction crops + orbit18, s4 r05)
Flaws seen: (1) the wing colour border stepped face by face across the slab (a tetris pattern in az090/az225); (2) a soft horizontal crease at the foreleg top under the bib (crop B, not flagged, folds <= 88 deg); (3) the wings read as planks from +45 az90/az270; (4) body longer/thinner and head smaller than the sheet's chunky barrel and big head; (5) the cream belly reads as a straight band in az090. Probe flags not visible in crops: the teal thin-membrane marks on the wing tip edge (membrane PASS, p10 18 mm).
- s4 r06 (fix round 1): Critique: flaw 1. Fix: a covert layer, a second closed tan slab 6 mm over the wing's upper front, its lower edge zig-zagging station to station and tapering at station 9, root inside the ruff; the wing slab itself all brown. Orbit/side: reads as the sheet's layered coverts over dark flight feathers. Every kit gate PASS (4394 tris, slivers 0.4 %, posed fold-overs 0 %, hit/float/drift/z-fight 0), glbcheck OK, junction probe PASS (all knife 0, strip <= 0.78 r, wing max concave 48 deg), eyes PASS, membrane p10 18.0 mm. Separation tail-hind 18.7 cm, fore L-R 20.6 cm, hind L-R 24.6 cm PASS.
- Not fixed (round caps reached: S4 ran 6 rounds against the brief's 4, the extra two were junction re-lock checks): flaws 2-5.
- Deliverables: orbit18_sheet.jpg, side_by_side.jpg (reference | model, checks.py), compare_engine_grey_final.jpg (run.py --compare), review/, rounds/s4_r06_junctions.jpg.

## Border pass (night 2026-10-23, s4 r07)
- kit/smooth_borders(body, k=k, iters=8) after the body paint: 12 cuts, 59 relaxed (max 28.9 mm, 13 undone); stair
  corners 18 -> 7, 3-to-1 quads 17 -> 0. Kit gates, junction probe PASS; clips PASS (after --fix-clips). Detail gate
  FAIL pre-existing (claw tips short). The wing piece's tan/brown covert zig-zag is a separate piece, not touched
  (owner pick: smooth it too, or keep as a feather edge).
- A/B (fresh Opus seat per order, blind): after wins both orders (belly patch a rounded oval). ADOPT.
- Files: border_before_after.jpg, before_borders/.

## Detail pass (2026-10-23 night; backup before_detail/)
- s4 r08: hind lion claws with blunt chunky tips (tip ring 19.6 x 19.5 mm; was 10 x 7 mm, t 17.0 < 18.2 mm). ALL
  gates PASS (kit, junction, eyes, detail). A/B Opus both orders: variant won BOTH -> ADOPT.
