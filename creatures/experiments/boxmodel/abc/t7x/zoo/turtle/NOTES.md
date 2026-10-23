# turtle (t7 hand box model, zoo workflow v2) — NOTES

Concept: refs/gpt/v3/turtle/sheet_1.png (2x2). `kit/refs.py --height 0.9` -> blueprint.json + reference/ (length
1.47 m, width 0.87 m). Template: zoo/elephant/elephant.py (loft, 14-vertex half rings, leg windows, grow()).
Identity cue (land tortoise, not sea turtle/terrapin): a TALL domed carapace of hexagon plates (centre hexagon, a ring
of six, 18 marginals) with a flared rim, four thick short column legs with blunt nails coming out of the shell
openings, a thick wrinkled neck rising from the front opening, a blunt round head with a dark beak, a short cone tail.
Technique: one spine loft of 14-vertex half rings (tail 4 x 6-vertex, rear wall, hind window 5, barrel 6, fore window
5, neck 3, head 6). Under the shell the loft is the body dome (2.5 cm inside the shell top, 3.5 cm inside its rim:
hidden) over a short skin/plastron band; j6 is a placed loop just under the rim (the plastron colour border). Legs from
4 x 4 windows on the plastron edge (j7..j11) through a 45 % transition ring. The carapace is a SEATED piece (stage 3) on
the same analytic dome as the body (ZTOP side line, ZRIM rim height, Wr plan superellipse), with its own hexagon-plate
topology: every plate is a groove ring + a raised plateau, so plate colours follow the plate's own edge loops; a rim
band, an underside band and a hidden inner cap close it inside the body (no slit, no floating rim).
Sheet notes: the side view staggers near/far legs; one symmetric pair (fore y -0.25, hind y 0.555, x 0.275). The plan
view is ~7 % shorter than the side view (refs.py centres each bbox): the side wins.

## Stage 1
- r1: first fit. 2,068 tris; IoU side/front/top 0.903/0.850/0.778 (body only: the shell comes in S3, so front/top
  sit low by the rim's 3.5-6.5 cm). FAIL: self-intersection at (0.12, 0.728, 0.21). Critique: the tail root ring Rt
  (tilted 40 deg) puts its bottom seam at y 0.736, z 0.19: ahead of and under the rear wall ring RW (y 0.738), so the
  14 -> 6 bridge folds under. Fix: RW to y 0.745, Rt back to (0.782, 0.232) at 30 deg, tail rings back with it.
- r2 result: gates PASS (0 intersections), 2,068 tris, IoU 0.902/0.850/0.773. Before locking, the front lip moved up
  (ZTOP/ZRIM at y -0.33: 0.64 -> 0.655): the lip's lower edge (Zr - RIMT) must clear the neck top that rises under it.
- r3 LOCK (temporary), then a minimal S2/S3 pass to see the body under the shell (elephant's practice). s3 r1: the
  carapace reads right (centre hexagon, six costals, 18 marginals; plates follow their own loops), 3,372 tris; techqa
  FAIL slivers 2.0 % (68). Lock deleted for base fixes (logged here).
- r4. Critique: s3 r1 hero/az000 TECH QA — yellow needle triangles on the shoulder fronts. Diagnosis: F4 -> N0 quads
  run from a 0.37 m wide ring (shoulders) to the 0.125 m neck ring: long trapezoids that triangulate into needles.
  Fix: a chest-front ring F5 (y -0.408, ws 0.245, bottom 0.275) between them; its bottom columns j11-j13 join the
  plastron set (the sheet's plastron front lobe between the fore legs).
- r4 result: s3 r2 slivers 1.7 % (PASS), 3,424 tris; the chest front reads as a lobe. r5 (no lock). Critique: s3 r1
  az000/az090 colour — the legs read thin under the 0.435 m rim (sheet front view: each leg ~0.26 m wide, the upper leg
  filling under the rim). Fix: FORE/HIND sections rx 0.118 -> 0.132, ry 0.128 -> 0.140, centre x 0.275 -> 0.285.
- r5 result: legs read as the sheet's thick columns (az000), IoU 0.906/0.842/0.759, gates PASS.
- r6. Critique: r5 az090/az180 — the tail is a flat spike pointing back at z 0.2-0.3; the sheet's rear view shows a
  cone hanging down under the rim. Fix: tail rings tilted 20-40 deg, tip at (0.823, 0.10).
- r6 result: the tail hangs as a cone under the rear rim. IoU 0.907/0.838/0.760. LOCK (with orbit). 2,148 tris.

## Stage 3 (pre-junction passes)
- r3. Critique: s3 r2 hero/az090 colour — the creature reads dark and grey: skin #b8a68b renders mud-grey, the shell
  near black-brown; the sheet is a pale beige skin under a mid-brown shell with light tan grooves. Fix: palette skin
  #cbb99c, scute #816947, groove #b09668, plastron #b8975f (mid values, BRIEF §7).

## Stage 4 / junction rounds (S1 base reopened where the probe points at the base; lock re-made each time)
- s4 r1 (first full S4, --junctions): all kit gates PASS (glbcheck OK, slivers 1.7 %, fold-overs 0.06 %, drift 0,
  clip warn 0.43 %); eyes PASS (0.26/0.65/0.62, 26 mm = 0.11 head). Junctions FAIL: upperarm knife 2.11 r (133 deg),
  strip 1.83 r; thigh knife 2.72 r, strip 3.43 r; tail0 knife 5.13 r. Crops: legs read thick and broad; red flags on
  the INNER and front walls of each leg top where they meet the plastron underside; a thin dark line under the rim
  over the thighs (close-up 2); the rear wall under the tail is a fan of creased faces.
- s4 r2. Critique: crops upperarm/thigh C (from below) — knife folds on the leg's inner wall at the plastron.
  Diagnosis: the window j7..j11 spans x 0.17-0.385 but the leg 0.152-0.416: the walls step OUT past the rim, so the
  plastron face and the wall meet at 126-133 deg. Fix: the lower ring part takes placed x fractions (LOWX: window
  0.13-0.39) and the legs move to the window centre (cx 0.262).
- s4 r2 result: no better (upperarm knife 2.6 r, thigh 2.18 r). knifedump.py (my diagnostic: probe knife/strip
  positions) shows the real causes: (a) upperarm: 119-133 deg folds all along ring F5 (y -0.408, z 0.34-0.52): the
  chest ring is a flat front wall behind the neck ring; (b) 92-94 deg folds at the window's inner/rear rims (leg wall
  straight down off the plastron); (c) thigh: a 0.62 m seam strip along j6-j7 (LOWX[0] = 0.985: a 6 mm band the whole
  body length); (d) tail0: the 14 -> 6 bridge triangles of RW -> Rt fold 126 deg.
- s4 r3. Fix (a): F5 becomes a straight vertex-wise in-between of F4 and N0 (t 0.5) instead of a hand ring.
- s4 r3 result: upperarm knife 2.6 r -> 1.31 r (max 94 deg: only the window-rim folds left); 2,120 tris.
- s4 r4. Fix (c): LOWX j7 0.985 -> 0.93 (and j8/j9 eased): the j6-j7 band gets ~2.5 cm wide instead of 6 mm.
- s4 r4 result: thigh strip 3.95 r -> 2.32 r (the body-long j6-j7 band gone); remaining flags: the rear wall/tail
  root (RW -> Rt 14 -> 6 bridge: 0.19 m triangles at 126 deg, thin P4 -> RW triangles), F4/F5/N0 thin bands (strip
  2.4 r), and the 92-94 deg window-rim folds.
- s4 r5. Fix (d): a 14-vertex tail-root ring RX the size of Rt behind RW: RW -> RX is a concentric quad cap, RX -> Rt
  bridges two rings of the same size.
- s4 r5 result: tail0 knife 3.78 r -> 0 (max 74 deg), thigh knife 2.18 -> 0.70 r (PASS on knife); slivers 2.1 %
  (FAIL, RX -> Rt); strips: the rear cap RW -> RX (quads 0.15 m long, 1.3-3.5 cm wide) and the thin P4 -> RW band;
  tail crops: the rump under the rear rim reads as a big folded fan.
- s4 r6. Fix: the rump as concentric steps: RW (y 0.728, ws 0.30) -> RW2 (0.75, 0.19) -> RX (r 0.08) -> Rt (r 0.058):
  near-square faces, every step a 2.5-11 cm ring.
- s4 r6 result: rear strips shorter (thigh strip 2.14 -> 1.71 r), but a new 128 deg fold at RW2's bottom (y 0.75,
  z 0.21): RX tilted 20 deg put its bottom seam 1.2 cm ahead of RW2. 2,224 tris.
- s4 r7. Fix: RX upright (4 deg) and smaller (h 0.06, centre z 0.226), the rump rings spread to y 0.724/0.752/0.772.
- s4 r7 result: tail0 knife 0 (max 77 deg), thigh knife 0.47 r; strips 1.6-2.0 r remain on the rump steps (single
  10-16 cm triangles, seen from behind-low only; checked against the crops below). 2,224 tris.
- s4 r8. Critique: upperarm knife 1.23 r = three 93-94 deg folds on the window's inner (x 0.129) and rear (F0)
  rims: the leg's first section is as big as the window, so its wall drops straight off the plastron. Fix: FORE/HIND
  top section 1 cm inside the window (rx 0.121/0.122, ry 0.127/0.132) plus a full-size ring 2.7 cm lower: the
  90 deg corner becomes two ~45 deg turns, the leg stays thick below.
- s4 r8 result: knife 0 on every junction (max concave 76-82 deg). Only seam strips fail: upperarm 2.47 r (the
  F4 -> F5 -> N0 bands at the neck root, 1.6-2.3 cm deep and 0.3 m round), rump 1.6-2.0 r. 2,352 tris.
- s4 r9. Fix: N0/N1 forward 2.4/1.4 cm (N0 top y -0.442, bottom -0.46): the neck-root bands get 3-4 cm deep.
- s4 r9 result: upperarm strip 2.47 -> 1.55 r (single 18-24 cm triangles of the F4 -> F5 band at the shoulder front,
  a faint light streak in crop B); knife 0 everywhere. Rump strips 1.6-2.0 r unchanged. 2,352 tris. S1 stays locked
  from here (edge sha f49924ad...).
- s4 r10. Critique: crops upperarm A/B, thigh A/B, tail A — tan plastron colour wraps over every leg top, the
  shoulders and the rump: the sheet has skin legs and a tan band only between the legs and on the underside.
  Diagnosis: PLASTRON_V took j6.. of every ring RW2..F4 (window rings too). Fix: j6.. only on the band rings P0..F0
  (between the windows), j11.. (inside the window inner-rim loop) on RW..F5: borders along the j6 and j11 loops and
  the P0 / F0 window-rim rings.
- s4 r10 result: colour borders read like the sheet (tan band between the legs, tan underside, skin legs/shoulders).
  Gates as r9 (strips only).
- s4 r11. Critique: crop upperarm B — a light streak on the shoulder front (strip 1.55 r). Diagnosis: from the wide
  flat-bottomed F4 (x 0.37) to the round 0.124 m neck ring N0, every vertex slides ALONG its ring's tangent: sheared
  quads 9 mm high. Fix: N0 becomes a tall chest/neck-base ring (bottom z 0.262 at the plastron lobe, W 0.205), N1 the
  neck base (W 0.14); the shrink now runs across the rings.
- s4 r11 result: upperarm strip 1.55 -> 2.05 r (worse): the remaining strip runs down F4's straight shoulder line
  (x 0.2-0.37, z 0.3-0.56) whose vertices still slide along it toward the round N0.
- s4 r12. Fix: F4's upper half one elliptical arc (top 0.635 -> the shoulder 0.37 at z 0.30; no straight diagonal):
  a round ring like N0, and the sheet's round shoulders under the front rim.
- s4 r12 result: upperarm strip 2.05 -> 0.52 r (PASS on strips), but a 115-119 deg valley along F3 (y -0.315): F3
  kept the straight shoulder line between the round F4 and F2.
- s4 r13. Fix: F3 one elliptical arc like F4 (top 0.585 under the lip); F2/F1 lose the under-rim tuck and get a
  convex shoulder point (70 % out, 30 % down): the shoulder is convex from the rim to the chest front.
- s4 r13 result: upperarm.L/R PASS (knife 0, strip 0.49 r); shoulders read round. Left: tail0 strip 2.01 r, thigh
  strip 1.61 r, both on the rump rings behind the hind windows (same shear: flat-bottomed rings narrowing along their
  own tangent).
- s4 r14. Fix (same principle as r11-r13): RW's bottom rises (0.198 -> 0.222: the plastron's rear edge curves up),
  RW2 one round ellipse (p 2.0): the rump shrinks across its rings.
- s4 r14 result: no better (tail0 strip 2.26 r, thigh 1.62 r). Crop tail A shows it: the steps between the rear rim
  and the tail root read as a crumpled shelf of thin creased facets.
- s4 r15. Fix: RW / RW2 / RX in one plane (y 0.730 / 0.736 / 0.742, RX upright): a flat skin wall round the tail root
  under the rear rim, the tail cone (Rt..T0) leaving it back and down.
- s4 r15 result: worse — tail0 knife 3.19 r (132 deg): the flat wall folded over itself because RX (z 0.168-0.288)
  hung below RW2's bottom (0.206); the wall under the rim is only 8 cm tall for a 12 cm tail root.
- s4 r16. Fix: nest the wall rings with ~2 cm margins: RW2 drops its bottom to 0.165 (the rump bulges down round the
  tail root), RX h 0.045 / W 0.062, the tail cone 15 % slimmer (sheet rear view: ~0.1 m at the root).
- s4 r16 result: tail0 knife 1.72 r (92 deg), thigh knife 0.83 r + strips 1.7 r: RW2 (round) crossed RW's flat top in
  the wall plane, folding the top of the wall.
- s4 r17. Fix: RW / RW2 / RX exactly in one plane (y 0.733), RW2 = the vertex-wise in-between of RW and RX (nested by
  construction), RW's bottom down to 0.17 (the rump bulges under the tail) so RX (r 0.04-0.055) sits with 3 cm
  margins; tail cone 10 % slimmer again.
- s4 r17 result: thigh.L/R PASS (knife 0.56 r, strip 0.87 r); upperarm PASS. tail0 FAIL knife 1.2 r: 97-133 deg folds
  along RX's lower edge, where the tail underside (Rt tilted 18 deg, bottom 1.4 cm below RX) drops off the wall.
- s4 r18. Fix: Rt becomes a fillet ring 1.5 cm off the wall (0.78 x RX, tilt 8 deg), the cone bends down after it
  (T2 22, T1 32, T0 40 deg): two ~45 deg turns instead of one hard corner.
- s4 r18 result: tail0 knife 0 (max 72 deg); only strip 1.42 r left: wall triangles between RW2 and the round RX,
  8 mm wide (RW's arc-length vertices slide along the tangent to RX's angle-spaced ones). thighs/upperarms PASS.
- s4 r19. Fix: RX = RW scaled about the tail root (x 0.20, z 0.42; a wide oval tail base 11 x 6 cm), so RW, RW2, RX
  are similar curves and the wall quads are radial trapezoids.
- s4 r19 result: worse (tail0 knife 1.72 r): the flat oval RX against the round 6-vertex Rt.
- s4 r20. Fix: the whole tail in 14-vertex rings that are RW's own shape scaled down and swung back-down (RX, Rt,
  T2, T1, T0): no 14 -> 6 bridge, every ring similar to its neighbour.
- s4 r20 result: tail0 knife 0; strip 1.88 r = one 8 cm x 5 mm wall triangle per side at the tail root's equator
  (RW's j5 -> j6 runs nearly horizontal, the same direction as the scaling toward the root: sheared); slivers 2.7 %
  FAIL (the tail tip's 14-gon cap).
- s4 r21. Fix: RW an oval (dome edge out to x 0.27 at z 0.262, a short 45 deg step to the flank point) so its sides
  run across the radial direction; the tail tip closed with a fan round a centre vertex.
- s4 r21 result: tail0 strip 1.5 r, slivers 2.5 % FAIL: the tiny 14-vertex tail rings and the wall next to them.
  Five rounds (r17-r21) on the lofted tail root; each removed one cause and left thin wall triangles at the next.
- s4 r22. Fix (structural): the rump closes as one flat skin wall (RW / RW2 / RX = RW x 0.25, all in y 0.733, fan
  centre); the tail becomes a short blunt 8-sided cone PIECE seated 1 cm into that wall (like a horn on a skull).
  The tail bones stay (rig, probe root).
- s4 r22 result: JUNCTION PROBE PASS (upperarm knife 0 / strip 0.49 r; thigh knife 0.79 r / strip 0.66 r; tail0 0/0;
  eyes 0.26/0.65/0.62, 26 mm = 0.11 head); all kit gates PASS; 2,274 body tris. Owner-style crop review: (1) thigh
  A/B — a thin dark line between the rim's lower edge and the thigh tops (the rim hovers 1-3 cm over the skin: reads
  as a slit); (2) thigh B / tail A — the rump's flank points (RW x 0.30) poke back past the thighs as pointed wedges.
- s4 r23 (stage 3 only). Fix (1): each rim lower-edge vertex rays down onto the skin (mirrored body); within 4.5 cm
  it is seated 4 mm into the skin, so the rim rests ON the shoulders and thighs instead of hovering over them.
- s4 r23 result: the rim now rests on the shoulder and thigh tops (crop thigh A: no dark line); probe PASS, kit gates
  PASS (posed clip warn 0.92 %, not gated).
- s4 r24. Critique: close-up 3 / thigh B — the rump's flank corners (RW x 0.30) stick out behind the thighs as flat
  pointed shelves under the rear rim. Fix: RW narrower (ws 0.30 -> 0.262, dome edge 0.235); with it a warmer skin
  #d2bd9b and a lighter shell #8a7049 / #b39a6a (side_by_side: the model read greyer and darker than the sheet).
- s4 r24 result: thigh strip 1.13 r FAIL (the P4 -> RW band shears again when RW narrows 0.355 -> 0.262 in 3.3 cm).
- s4 r25. Fix: RW halfway (ws 0.28, dome edge 0.252).
- s4 r25 result: probe PASS (thigh strip 0.76 r), kit gates PASS. s4 r26: final-style round with orbit: all gates
  PASS, glbcheck OK, separation PASS (tail-hind 0.17 m, fore/hind L-R 0.26 m).
- Owner-style review of orbit18_sheet.jpg / side_by_side_sheet.jpg (EEVEE) — flaws: (a) az135/az180/az225: the
  thighs and rump corners stick out behind the shell as broad crumpled skin shelves, and the seated rim makes a
  ragged saw-tooth light edge over them; (b) plan view is a box (shoulders and front body as wide as the legs);
  (c) EEVEE washes the palette out: cream skin, yellow groove grid too wide (KI 0.24), the shell reads tan, not the
  sheet's mid brown.
- s4 r27 (fix round 1). Fix (a, the cause): the shell plan is too narrow at the rear (rear exponent 2.4: half-width
  0.33 m at the thighs); the sheet's shell is full to the back and its rim covers the thighs. Rear exponent 3.2
  (half-width 0.364 at y 0.55, 0.238 at 0.70).
- s4 r27 result: probe PASS (thigh knife 0.35 r, strip 0.72 r; posed root clip 0.87 %), kit gates PASS.
- s4 r28 (fix round 2, stage 3). Fix (a, the saw-tooth): rim seating with a smooth falloff (full seat under 2.5 cm,
  fading out by 6 cm) instead of all-or-nothing drops within 4.5 cm.
- s4 r28 result: the rim rests smoothly on the hind legs (h135: no saw-tooth), probe PASS.
- s4 r29 (fix round 3, stage 3). Fix (c): palette for EEVEE (it reads ~15 % lighter than the hex): skin #b49e80,
  scute #6f5638, groove #9e8253, plastron #a8874f; groove ring KI 0.24 -> 0.15 (the sheet's grooves are thin lines).
- s4 r29 result: FAIL slivers 2.6 % (the 0.15 groove quads triangulate into needles); probe PASS.
- s4 r30. Fix: KI 0.19.
- s4 r30 result: slivers 1.4 % PASS, all kit gates PASS, probe PASS; colours now read close to the sheet in EEVEE.
- s4 r31. Critique: side_by_side az0/az180 — the carapace reads as a peaked roof, narrow at the shoulders; the
  sheet's is a full round dome whose sides stay wide down to the rim. Diagnosis: dome section exponent PD 1.8 (< 2 is
  a pointed superellipse). Fix: PD 2.3 (shell and the hidden body dome under it).
- s4 r31 result (FINAL): all kit gates PASS (lock edge sha256 8ff62df31f00992d..., glbcheck OK, slivers 1.4 %,
  fold-overs 0, drift 0, hit 0, float 0, z-fight 0; posed clip WARN 0.88 %); junction probe PASS (upperarm knife 0 /
  strip 0.49 r, thigh knife 0.35 r / strip 0.72 r, tail0 0 / 0); eyes PASS (0.26/0.65/0.62, 26 mm = 0.113 head);
  no membranes; separation PASS. IoU side/front/top 0.909/0.899/0.777 (body only). 3,656 tris (body 2,290, shell 648,
  nails 576, tail 78, eyes 64). 7 colours. Stage rounds: S1 30 (re-locked from S4 junction rounds, each logged), S2 1,
  S3 3, S4 31. --review and --compare run (side_by_side.jpg = kit compare; side_by_side_sheet.jpg = sheet | EEVEE).
- Residuals: the plan view is boxy at the front (shoulders / chest block as wide as the legs, a slim neck rises from
  it), the rump corners still show as small skin shelves behind the hind legs under the rear rim (az135/az225), the
  head is a plain rounded loft with a dark beak cap (no jaw line or beak hook, sheet's neck folds absent); the tail is
  a seated piece, not lofted (five lofted tail roots left thin creased wall triangles).

## Weakfix 2026-10-23 (night, backup before_weakfix/)
- s4 r32. Critique: hero/close_0 — the neck is a smooth pale tube, the head a plain capsule with a dark nose blob (sheet: wrinkled neck, mouth line, hooked beak). Diagnosis: N0-N2 / K1-K5 are plain lofted rings, no fold or jaw rows. Fix (stage 2 only, lock unchanged): two logged neck loops (N0-N1, N1-N2) pushed out 11 mm as fold ridges (stronger on the throat), N1/N2 sunk 4 mm as grooves; chin step (K1-K3 underside -6..-8 mm, N2 throat up/back); jaw crease on row j8 of K1-K4 + a dark mouth band (j8-j9, K2-K5); upper beak sheared forward over the lower jaw (planar shear on K4/K5), dark paint on the upper beak only.
- s4 r32 result: kit gates PASS except drift FAIL (piece_shell, 1 shell) — the kit's techqa drift anchors changed tonight (02:05, skin-contact anchors), not this edit; junction probe PASS (upperarm knife 0 / strip 0.49 r, thigh knife 0.35 r / strip 0.88 r, tail0 0/0, eyes 0.26/0.65/0.62); detail gate FAIL 5 groups (tier 2 wants 6; pre-existing). 3,760 tris. A/B vs champion (2 fresh Opus seats): AB order -> B (variant), BA order -> A (variant): ADOPT. Judges: the mouth line reads a little dark/deep. Rump shelves not addressed (time).

## Night clip fix 2026-10-23 (backup before_tailclip/)
- Gate re-run on the 03:18 GLB: junction FAIL tail0 posed clip 3.3% with thigh.L/R at move@7/@19 (thighs 1.54/1.55%), detail FAIL 5 groups (pre-existing), clips PASS, techqa drift 1 piece_shell (pre-existing). Crops: the pink faces are rump skin weighted to tail0 just behind the thigh roots, under the shell rim; the authored clips pass (r33 pre-fix probe: tail0 clip 0) - the --fix-clips leg aim IK in move pushes the thigh roots back into them.
- Kit gotcha found: --fix-clips reads the AUTHORED clips from stage4/before_clips/<c>.glb whenever the joint rest is unchanged (clip_gate.same_rest compares joints only), so a re-authored clip in the .py is ignored; each round below copies the fresh build into before_clips/ first.
- r33: tail0 sideways swing 0 in move: no change (3.3%) -> not the swing. r34: tail carried lifted, tail0 X -12 in every move key: 4.21% (worse). r35: X +12.
- r35: tail0 X +12 (tail lifted the other way): tail0 clip 0.89% PASS, thigh.L/R still 1.54/1.55% (their crossing faces do not move with the tail).
- r36: stride A 12 -> 9 + tail lift X +18: junction probe PASS (tail0 clip 0%, thigh.L/R 0.3%), clips PASS after --fix-clips (move pen 0.132), eyes PASS; residual FAILs pre-existing: techqa drift piece_shell 1 (kit anchors), detail count 5 < 6. Posed A/B at move@19 (hero + rear 3/4), fresh Opus seats: AB -> variant, BA -> variant: ADOPT (rear: champion's hind leg crumpled under the rim; variant lifts the hind foot clear).
