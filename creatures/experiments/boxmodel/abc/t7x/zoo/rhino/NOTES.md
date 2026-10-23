# rhino (t7 hand box model, zoo workflow v2) — NOTES

Concept: refs/gpt/v3/rhino/sheet_1.png (2x2). `kit/refs.py --height 1.7` -> blueprint.json + reference/ (length 2.87 m, width 1.15 m).
Identity cue (rhino, not hippo/boar): a big upright nose horn plus a small second horn on a long, low-hung wedge head;
a hump over the withers; a deep barrel on four short thick column legs with round three-nailed feet; small tube ears high
on the skull; a thin tail with a dark tuft. The S1 silhouette carries the hump, the low wedge head, the barrel and the
columns; the horns come as S3 pieces (META['later'] masks them in the IoU).
Sheet notes: the side view staggers the near/far legs (two foot pairs per end); the model uses one symmetric pair at the
mean (fore y -0.27, hind y 1.02). The top view puts the hind feet ~0.2 m further forward than the side; the side wins.

Technique: one spine loft of 14-vertex hand-placed half rings (33 stations), the thin tail as a 6-vertex run joined to
the rump by an uneven open-row bridge (no 14-vertex needle rings on the tail), legs extruded from 4 x 3-face windows on
the lower-flank bevel (14-sided legs) through a transition ring that slopes from the window rim toward the leg's first
section (T1 = 0.45), ears from 2-face windows on the skull top.

## Stage 1
- r1: first fit. Gates PASS, 2,536 tris, IoU side/front/top 0.880/0.847/0.867. Critique: az000/hero — the snout ends in a
  big flat 14-gon disc (reads as a pig snout). Diagnosis: the loft stops at H6 (W 0.13, 0.26 m tall) and caps it.
  Fix: H6 slightly wider, one more small ring H7 3 cm ahead (W 0.085) so the muzzle rounds off into a small cap.
- r2: better: the front is a small rounded cap (IoU 0.879/0.847/0.868, 2,588 tris). Critique: hero/az000 — the ears are
  thin flat spikes, not the sheet's tube ears. Diagnosis: EAR rings rx 0.04-0.046 standing straight up from the window.
  Fix: EAR rings rx/ry 0.05-0.06 with a funnel ring, leaning out to x 0.31 at the tip (front view ears at x 0.2-0.36).
- r3: no visible change: the GLB shows the ear tube is 0.08 x 0.10 m, too small for a 1.7 m rhino (sheet ears ~0.15 m
  across a forward cup), so it reads as a spike. Fix (r4): ear window 3 faces (j1-j4, x 0.11-0.27) and cup rings
  rx 0.064-0.076 / ry 0.046-0.05, tip at z 1.745.
- r4: ears a little fuller (IoU 0.878/0.843/0.867, 2,628 tris). Critique: az000/hero — the ears still taper to a needle
  tip, the sheet's ears are broad rounded leaves ~0.2 m across. Fix (r5): cup ring rx 0.088, the tip ring rx 0.072 then a
  0.034 cap ring: a rounded leaf end.
- r6 LOCK (IoU 0.878/0.841/0.867, 2,628 tris), then a minimal S2-S4 pass to probe the junctions (s4 r1): legs PASS
  (fore knife 0.86 r at 93 deg, hind 0 knives, max concave 80 deg: the 4x3 windows + sloped transition ring work);
  FAIL ear (knife 2.76 r, 115 deg), tail (seam strip 1.59 r), eye size 0.05 of head, z-fight 24 (nail soles on the sole).
- r7 (lock deleted and re-made: a base change, logged here). Critique: tail crops/flag tile — yellow strips radiate round
  the tail root; the beauty crop shows a thin pipe stuck on the rump. Diagnosis: Rt was a tiny 14-vertex ring (1.2 cm
  faces on the crease). Fix: Rt a broad 6-vertex ring (W 0.08, h 0.062); the 14 -> 6 uneven bridge now R0 -> Rt.
- r7 result: tail0 PASS (knife 0, max concave 69 deg, no strip); 2,596 tris; IoU unchanged.
- r8. Critique: ear crops — a hard dark fold where the ear's front/inner wall stands up off the skull (knife 2.76 r,
  115 deg, red at the front-inner root). Diagnosis: the transition ring was a straight 45 % lerp to E1, and E1 is nearly
  the window's size, so the root walls stand vertical on a skull that slopes away. Fix: the ear transition ring moves
  60 % of the way in but only 20 % of the way up: a flared ear root (two ~45-60 deg folds instead of one 115 deg one).
- r8 result: ear max fold 115 -> 105 deg, knife still 2.7 r. The flag tile shows the red knife faces BEHIND the ear's
  inner-rear wall: the neck top N1 (z 1.545) rises above the skull top H0 (1.495) right behind the ear, so the ear's rear
  wall and the rising neck make a valley.
- r9. Fix: N1 top 1.545 -> 1.515 and H0 1.495 -> 1.50: a level plateau round the ear root, the neck rising from N0 on.
- r9 result: ear knife PASS (1 edge, 0.83 r, 90 deg); strip 2.6 r: the flag tile shows thin yellow faces running down the
  ear's corners. Diagnosis: the grid angles of a 1 x 3 window (45, 72, 108, 135 deg...) leave a 27 deg face at each corner
  and a 90 deg face down each side.
- r10. Fix: grow() maps the window's boundary roles to EVEN angles round each section (ears 8 x 45 deg, legs 14 x 25.7).
- r10 result: ear knife 0 (max 89.6 deg), strip 2.6 -> 1.89 r; legs strip-free now (fore 0, hind 0.92 r); 2,596 tris.
  Remaining yellow: thin triangles in the ear's transition band at its front/back corners (window corners at grid angles,
  the transition ring at even angles: skewed quads split thin).
- r11. Fix: the transition ring keeps the window's grid angles; the even angles start at the first section.
- r11 result: no change (strip 1.91 r, 7.7 mm): the flag tile shows ONE thin triangle at the ear's front-outer root
  corner (and a 90 deg knife edge at the rear corner): the window corner is square, the transition ring's corner (the
  E1 superellipse, n 2.4) is cut in, so the corner quad splits into a needle.
- r12. Fix: E1 section exponent 2.4 -> 3.6 (a boxy ear root that matches the square window corners).
- r12: worse (knife 1.57 r): reverted. A flag dump (scratch flagdump.py: the probe's flagged faces with positions) shows
  the strip is the ear's front/rear TRANSITION BAND: the window is only 0.11 m long (H0-H1) and E1 (ry 0.05) fills it,
  so the transition ring sits 1 cm inside the rim (a 1 cm band on a crease); the knife edges are at the outer-rear corner
  where the H0-N1 face drops behind it.
- r13. Fix: H0/H1 spread to y -0.765 / -0.925 (a 0.16 m ear window), E1 ry 0.046, ear transition 70 % in / 20 % up.
- r13 result: ear knife 0 (max 89 deg), but strip 2.94 r: the dump puts it on the ear's OUTER transition band now. The
  skull top slopes 0.64 down to the outside, the ear rings were level: E1 sat 4 cm over the inner rim and 14 cm over the
  outer one, so the outer band is a thin creased sliver.
- r14. Fix: the ear root rings tip with the skull slope (z drops 0.55 / 0.35 / 0.15 x (x - cx) on E1 / E2 / E3).
- r14 LOCK: 1,300 verts, 2,596 tris, IoU 0.878/0.838/0.866. Ear knife 0 (max 88 deg); strip 2.23 r remains on the
  ear's outer transition band (the ear root is as wide as the window: 1 cm outer margin). S1 rounds used up: the rest is
  vertex moves in S2.

## Stage 2
- r1: eye socket inset (logged), plus the S1 carry-over: the ear root (transition ring + E1) scaled x 0.8 across about
  the ear axis, so its outer side clears the window's outer rim by ~3 cm.
- r1 result: s2 gates PASS (2,612 tris, min IoU 0.999). Ear strip 2.39 r: the dump shows the rear/front bands now
  (rim -> transition 2.5 cm in y on a 7 cm long wall).
- r2. Fix: the ear root layers found topologically (rim = H0/H1 window verts, transition = their ear neighbours, E1 the
  next ring): transition y x 0.65 and E1 y x 0.75 about the ear centre (both keep x 0.8).
- r2 result: WORSE: ear knife 4.23 r at 157 deg (E1 squeezed alone, the cup above flares out of a waist).
- r3. Fix: the whole ear above the transition scaled y x 0.75 (a thinner cup, no waist); transition y x 0.65 kept.
- r3 result: identical knife (4.23 r): the dump shows the folds on the ear's OUTER side: the skull side drops to z 1.30-1.40
  there, the level rings put the transition 2 cm inside the rim and E1 straight above it: a step, not a slope.
- r4. Fix (replaces r1-r3): transition ring = rim pulled 30 % to the window centre + 2 cm along the window normal (SVD
  of the rim); E1 = rim pulled 42 % in + 7.5 cm along the normal. The ear root now follows the sloping skull.
- r4 result: ear max concave 157 -> 59 deg, knife 0; strip 1.54 r: one long thin triangle on the ear's OUTER transition
  face (the 1-span window side is one 16 cm edge, the band 2.4 cm wide) and one in the E1 -> E2 band above it.
- r5. Fix: transition pulled 45 % in (+2.5 cm lift), E1 56 % in (+8 cm): a ~4 cm band on every side.
- r5 result: max concave 65 deg, knife 0; strip 1.88 r now in the E1 -> E2 band: E1 is 7 cm across (verts 2.3 cm apart)
  and was slid 4 cm forward by the window normal's -y part, E2 is 17.6 cm across: a skewed band of needles.
- r6. Fix: lift along the normal without its y part; E1 pulled 40 % in across (wider), 50 % front/back; E2 x 0.85.
- r6 result: worse (knife 0.49 r at 103 deg, strip 2.44 r): r5/r6 placement reverted to r4's. Diagnosis of what is
  left: the strip metric counts triangles < 0.4 x the region's median width (~55 mm, the big head faces) with aspect > 3;
  the ear window's outer/inner sides are single 15-16 cm faces (one 0.16 m span), so any band there is a needle.
- r7 (one round over the S2 limit of 6, logged: the last open junction gate). Fix: r4 placement + a full head loop
  (logged `loop`) through the H0-H1 span, which halves the window's long sides and runs up the ear walls.
- r7 result: strip 2.81 r (worse), knife 0, max concave 59 deg. Crop review (s4_r13 vs s4_r16 ear rows A/B/C): both show a
  broad flared ear root, no slit, no knife fold; the yellow flags are slim facets on the ear's rear corner that the
  beauty crops barely show. Per the brief (probe flags not visible in crops are noise) the ear strip is accepted as
  noise; the head loop is dropped again (no visible gain), the r4 placement kept. Ear junction: knife 0, max concave 59 deg.

## Stage 3
- r1 (first build of the pieces): small round lens eye 68 mm (eye check: >= 0.06 of the 1.0 m head), dark pupil; front
  and rear horns (library `horn`, one midline shell each, mirror off); 3 toenails per foot (hand-built arched nails:
  the library has no rhino nail; `hoof_cloven` replaces the whole limb end with two toes), sole edge 8 mm off the ground
  (they z-fought the foot sole: 24 faces); palette one step lighter (the s4 colour read near black).
- r1 result: gates PASS, 3,164 tris, 5 colours; reads as a rhino from every view (hump, low wedge head, horns, columns).
  Critique: hero/az090 colour — the skin still renders dark charcoal; the sheet is a light warm grey.
- r2. Fix: palette skin #bdb8b0, legs #d2cbc0, nails/tuft #5a5550, horn #e2d9c8.
- r2 result: mid warm grey, facets read. Critique: hero/az090 — the front horn is a thin spike; the sheet's is a massive
  cone (~0.2 m base) that dominates the head.
- r3. Fix: front horn radius 0.085 -> 0.11, taper 1.5 (stays thick longer), length 0.40; rear horn radius 0.07.
- r3 result: PASS, 3,164 tris; the front horn now dominates the head as on the sheet.

## Stage 4
(Stage-4 round numbers continue from the s4 probe runs used during S1/S2: s4 r1-r16 were junction probes of the build.)
- r17 (first full S4): all kit gates PASS (lock, glbcheck, techqa: slivers 0, z-fight 0, fold-overs 0, drift 0); junction
  probe: legs/tail PASS, ear seam strip 1.54 r (crop-invisible: noise), eyes PASS (68 mm, front/3q/side 0.36/0.84/0.83),
  membranes PASS. Separation PASS (tail-hind 39 cm, fore L/R 17.6 cm, hind L/R 18.6 cm). 3,164 tris.
  Owner-style review (orbit18 + zoomed crops): (1) EEVEE orbit washed out to a pale cream (palette too light);
  (2) a small dark notch facet under the tail root (j4 crops A/B: the R0 -> Rt triangle fan); (3) az0: the muzzle front
  reads as a round disc; legs: broad blended roots, no slit, fold or strip at either root (crops j2/j5).
- r18. Fix (1): palette skin #aba69f, legs #c6bfb4.
- r18 result: PASS; EEVEE orbit now mid warm grey (workbench sheet still reads darker). Separation PASS.
- r19. Fix (2): tail-root notch: Rt j4-j5 2.5 cm down, R0 j11-j13 2 cm up / 1 cm back (S2 vertex moves).
- r19 result: PASS; tail0 PASS (max concave 78 deg, strip 0.52 r). Crops j4: the underside notch is softer; a small
  darker facet remains on the side of the tail hook (the R0 -> Rt 14 -> 6 fan) — residual, minor.
- r20: final stage-4 run with orbit + junctions, then --review, --compare, checks.py (orbit18, separation, side_by_side).
- r20 FINAL: all kit gates PASS (lock edge sha256 57438054a7feadac..., glbcheck OK, techqa: slivers 0, z-fight 0,
  fold-overs 0, drift 0); 3,164 tris (body 2,612). Junction probe: fore/hind leg roots, tail PASS; eyes PASS; membranes
  PASS; ear.L/R FAIL on the seam-strip metric only (1.54 r; knife 0, max concave 59 deg), not visible in the beauty crops.
  Separation PASS. Residuals: ear seam-strip flag (metric), muzzle front reads as a round disc at az0, small facet on the
  side of the tail hook, smooth barrel without the sheet's neck/shoulder skin folds.

## Detail pass (2026-10-23 night, tier 3: 7 -> 12+ readable feature groups; backup before_detail/)
- r21 (S4): added seated chunky pieces via detail_pieces.py (keel-sunk ridge bands, knobs, fan): fold_neck, fold_shoulder,
  fold_flank, fold_ankle, fold_rump, brow, mouth, nostril, tuft + paint 'belly'; smooth_borders after paint. Detail gate
  PASS 17 groups. Critique: every new piece rendered near-black (hero/az090). Diagnosis: all pieces shared one material
  named 'c', the last paint (mouth, dark) recoloured it. Fix: palette keys as material names. Also z-fight 10.
- r22: Result: colours right (6 colours), detail PASS; FAIL z-fight 8 (mouth 6, ankle 2), slivers 2.2% (band end fans).
  Critique (az090): the shoulder and flank folds stand as vertical hoops mid-barrel; ankle folds read as cuffs.
  Fix r23: folds lean per the sheet (shoulder from over the shoulder y -0.17 back to behind the elbow y 0.03; flank
  fold from mid flank into the thigh front; neck fold), ankle folds a front-outer arc, mouth 22 mm tall, blunt band ends.
- r23 Result: kit gates OK (techqa 0 z-fight, slivers OK), detail PASS (17 groups), junction FAIL ear strip 1.54 r only
  (unchanged from the champion). A/B (Opus, both orders): champion won BOTH: the raised bands read as straps/harness,
  a collar round the face (az000) and ankle cuffs. -> variant rejected.
- r24 Fix (one change: the fold method): folds side-only (no back crossing, no collar), broad (18-22 cm) and low
  (3.5-4 cm) with a gentle front slope and one rear overhang step (STEP profile); ankle cuffs and rump ridges dropped.
