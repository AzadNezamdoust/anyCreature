# beetle (rhinoceros beetle; t7 hand box model, zoo workflow v2) — NOTES

Concept: refs/gpt/v3/beetle/sheet_1.png (2x2). `kit/refs.py --height 0.6` -> blueprint.json + reference/ (length 0.963 m,
width 0.728 m; refs warning: top width 0.62 vs front 0.73). Measured with a metre grid (scratch grid.py) on each view.
Identity cue (rhinoceros beetle, not stag beetle / scarab / weevil): one big horn rising from the head front and curving up
and back, a second short horn on the pronotum, a broad dark pronotum shield over a bigger domed maroon wing case (elytra)
with a rim, six sturdy segmented legs splayed out from under the shell. The S1 silhouette carries the dome, the shield
step, the head and the head horn (the horn is the front end of the spine loft); the thorax horn, mandibles, eyes and claws
are S3 pieces.
Sheet notes: the top view draws FOUR leg pairs (a generator error); the side view and the brief say six legs: three pairs
at the side view's roots (fore y -0.13, mid 0.055, hind 0.20). The side view shows a third small horn on the head top
that the top view does not; only the thorax horn is built. The side view wins for proportions.

Technique: one spine loft of 16-vertex half rings (33 shell stations elytra tip -> head, 12 horn stations), each shell
section a dome + rim + tuck + boxy under-curve; legs from 4 x 3-face windows on the under-curve (j9-j12, just under the
rim) through a 45 % transition ring, 14-sided legs carried in a parallel-transported frame.

## Stage 1
- r0: FAIL self-intersection 18 pairs near (0.277, 0.02-0.06, 0.142); 4,544 tris; IoU side/front/top 0.86/0.73/0.69.
  Reads as a horned beetle from every view. Critique (gate): the mid leg's knee folds through itself (az000 wire).
  Diagnosis: the knee rings at 0.94 / 0.08 of the femur / tibia straddle a 90 deg bend 1.3 cm apart with a 2.1 cm
  radius: the inner side crosses. Fix: every bend is three rings: in and out rings 3.4 cm (knee) / 2.6 cm (ankle) back
  along their own segment, a third ring on the joint with the bisector tangent.
- r1: PASS, 4,544 tris, IoU 0.86/0.73/0.69. Critique: az000/az090 vs the sheet — the legs are thin stiff sticks
  (femur 2.8 cm radius vs the sheet's ~5 cm thick bead segments); the lessons say builders drift thin.
  Diagnosis: LR radii. Fix: LR x ~1.35 (coxa 0.040/0.046, femur 0.036/0.040, knee 0.027, tibia 0.032/0.035, ankle 0.022,
  tip 0.020).
- r2: PASS, 4,544 tris, IoU 0.86/0.73/0.66. A metre overlay (scratch ovl.py: the reference view resampled into the
  ortho frame, the model's silhouette edge in red) shows the side outline, body width and horn on the sheet's; leg
  thickness now matches. Critique: hero/az090 — the legs are smooth even tubes (the lofted-tube look); the sheet's legs
  are bead segments (coxa, femur, knee, tibia, tarsus beads). Diagnosis: leg_sections had one radius per segment with a
  mild 25 % knee neck. Fix: 12 sections, every segment swells between narrow necks (knee 0.023 vs femur 0.038, ankle
  0.018 vs tibia 0.034, two tarsus beads); mid knee 1 cm further out (the femur was too short for its beads).
- r3: PASS, 4,880 tris, IoU 0.86/0.72/0.67. Legs read as segmented beetle legs from az090/hero; roots broad.
  Shell, shield step, head and horn on the sheet's outline (overlay). Next: lock and probe the junctions.
- r4 LOCK (4,880 tris, edge sha256 18aa9152...), then a minimal S2-S4 (eye socket, paint, lens, thorax horn,
  mandibles, claws, rig + clips) to probe the junctions (s4 r1): all kit gates PASS (5,566 tris, techqa clean); eyes
  PASS (34 mm, 0.087 head; front/3q/side 0.33/0.74/0.73); all six leg roots FAIL knife: fore 2.1 r / 117 deg, mid
  2.1 r / 128 deg + strip 1.01 r, hind 3.4 r / 157 deg + strip 1.25 r.
- r5 (lock deleted and re-made: a base change, logged here). Critique: junction crops A/B, every leg — a dark crease
  along the top of the leg root, right under the shell rim (red on the flag tile along the window's top row j9).
  Diagnosis: the knees sit at z 0.15-0.17, level with or above the window (z 0.15-0.19), so the femur's upper wall runs
  out under the rim's underside: a deep notch (157 deg at the hind leg, whose knee is behind and above its root).
  Fix: knees down to the side view's height (fore 0.150 -> 0.125, mid 0.170 -> 0.135, hind 0.155 -> 0.120), so each
  femur leaves its window downward and outward, away from the rim.
- r5 result (s4 r2 probe): hind leg 157 -> 123 deg and its strip gone; every root still 4 knife edges ~2.1 r
  (116-126 deg). The flag crops show where: one edge per window span along the window's TOP row (j9, the tuck vertex):
  the tuck face j8-j9 runs inward under the rim and the transition wall leaves j9 outward-down: a 120 deg valley
  right under the rim lip (visible as a dark crease in crops A/B).
- r6 (lock re-made). Fix: leg windows one vertex down the under-curve (j10-j13 instead of j9-j12), so the near-vertical
  j9-j10 face sits between the rim tuck and the leg wall and the turn is split into two folds.
- r6 result: LOCKED (4,880 tris, edge sha256 b0465dbf5d547896). s4 r3 probe: all six leg roots PASS (knife 0; max
  concave fore 72, mid 87, hind 76 deg; strips 0.71/0.84/0.98 r; slit 0, open 0, poke 0); eyes PASS. Crops: broad roots
  that rise out from under the rim in two soft folds, no slit or crease. All kit gates PASS (5,566 tris).

## Stage 2
- r1. Critique: back34/top vs the sheet's rear and top views — the wing case is one smooth dome; the sheet's identity
  detail is the two elytra meeting at a midline suture. Diagnosis: the elytra seam vertices (j0 of E1..M4) sit on the
  dome. Fix: those seam vertices 8 mm down (vertex moves only): a shallow V groove along the midline, flat faces either side.
- r1 result: PASS (lock + logged inset, IoU vs S1 min 0.999), 4,896 tris. The suture reads in top/back34 as a crisp
  midline crease splitting the dome into two wing cases. (--junctions at S2 reports "no eye piece": the lens is an S3
  piece and there is no rig yet; the probe is run from S3/S4 on.) S2 closed: the S1 base already carries the shapes.

## Stage 3
- (s4 r1-r3 above were the S1 probe runs; S3 pieces and colours were written then: palette, lens, thorax horn,
  mandibles, claws.)
- r1. Critique: s4 r3 hero/az090 colour — the charcoal reads near black: the facets vanish and the head, legs and belly
  merge (BRIEF: dark creatures at #3a-#55 value but never black; mid values so facets read). Fix: palette one step
  lighter: chitin #5e5a60, leg #555158, belly #4d4649, shell #7a3a2c.
- r1 result: PASS, 5,566 tris, 6 colours; facets now read on the head, legs and belly, the maroon case still dominant.
  Critique: az090/top vs the sheet — the thorax horn is a small 6 cm spike (a cube from the top); the sheet's pronotum
  horn is a stout forward hook ~7 cm tall on a broad base, the second silhouette cue after the head horn.
  Fix: thorax horn length 0.095 -> 0.13, base radius 0.032 -> 0.046, curve 50 -> 60, base 1 cm further down into the shield.
- r2 result: PASS, 5,566 tris (same piece budget; the horn is resized). The pronotum horn now reads as a stout forward
  hook in az090/hero/top. Critique: az090/hero — the head horn ends in a blunt flat 16-gon disc. The sheet's tip is a
  point that hooks back. Diagnosis: the loft's last ring H15 (W 0.011, h 0.012) is capped flat.
  Fix (an S2 vertex move, run through S3): H15 scaled to 35 % about its centre and moved 1.2 cm back and 1.2 cm up, H14
  moved 5 mm back: a pointed tip curling back.
- r3: first try FAILED the lock (2 locked vertices gone, 6 open edges): scaling the ring's x to 35 % put its j1 vertex
  under 1 mm from the seam. Fixed in the same round: x scaled 0.7 only, y/z 0.35. Result: PASS, 5,566 tris; the horn
  ends in a point hooking back (az090/hero).

## Stage 4
- r4: first full S4 with orbit + junctions. All kit gates PASS (lock, glbcheck, techqa); junctions: six leg roots PASS
  (knife 0, max concave 72/87/76 deg, strips 0.71/0.84/0.98 r), eyes PASS (34 mm = 0.084 head; front/3q/side
  0.33/0.74/0.74), no membranes. 5,566 tris. Posed: move swings the legs in a tripod gait, attack dips then flips the horn.
  orbit advise: az000 head_merged (the horn stands in front of the body: intended for this species). Added checks.py /
  checks_blender.py (from scorpion): orbit18_sheet.jpg + side_by_side_sheet.jpg.
  Owner-style review (orbit18 + crops): (a) az45/az315 — the head horn is a thick cone; the sheet's is slimmer (front
  view half width 3.3 cm at z 0.45, the model 4.1 cm); (b) az180/top — the elytra suture does not read in the beauty
  views (the sheet's rear view is split down the middle); (c) EEVEE washes the charcoal to a light grey. Leg roots,
  eye and pieces: no slit, gap, crease or poke visible.
- r5. Fix (a): horn rings H8-H14 x 0.82 and H7 x 0.9 across (S2 vertex moves; the side outline already matches the sheet).
- r5 result: PASS, 5,566 tris; az000/hero: the horn reads slimmer, front-view width now near the sheet's.
- r6. Fix (b): suture groove 8 -> 15 mm deep (the seam vertices E1..M4), so it reads in EEVEE from the rear and top.
- r6 result: PASS, 5,566 tris; az180/+45 az180: a fine midline line splits the dome (faint under EEVEE's soft light,
  about as fine as the sheet's suture).
- r7. Fix (c): palette half a step back toward the sheet's dark charcoal (EEVEE read the s3 r1 values as light grey):
  chitin #555157, leg #4c484f, belly #453f43, shell #743529.
- r7 FINAL: all kit gates PASS (lock edge sha256 b0465dbf5d547896..., glbcheck, techqa: slivers 0.4 %, z-fight 0,
  hits 0, floats 0, fold-overs 0, drift 0); junction probe PASS: six leg roots knife 0 (max concave 72/87/76 deg),
  strips 0.71/0.84/0.98 r, slit/open/poke/gap/clip 0; eyes PASS (34 mm = 0.083 head; front/3q/side 0.33/0.74/0.74);
  no membranes. 5,566 tris (body 4,896). Palette now mid charcoal in EEVEE, dark in workbench.
  Owner-style review rounds: (a) horn slimmer, (b) suture deeper, (c) palette value: all three done.
  Residuals (side_by_side_sheet.jpg): the pronotum reads narrower and more peaked than the sheet's broad shield in the
  front view; the legs are still a little thinner and less bulbous than the sheet's bead legs; the abdomen underside
  is a flat plate where the sheet shows a rounded segmented belly under the rim; the head/face is one smooth mass (no
  clypeus step over the mandibles); the elytra suture is faint under EEVEE's soft light.
