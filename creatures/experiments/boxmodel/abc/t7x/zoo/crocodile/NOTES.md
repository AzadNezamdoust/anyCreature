# crocodile (t9 RECREATE, 2026-10-23) — NOTES

Rebuild from scratch of zoo/crocodile with zoo workflow v2 + proven tricks. Concept refs/gpt/v3/crocodile/sheet_1.png
(the zoo croc was traced from sheet_3). reference/ + blueprint.json from kit/refs.py --height 0.55 (length 2.41 m).
Blueprint top outline scaled x1.194 (the sheet's plan view is drawn at 0.83 x the side scale: refs.py warning; the
traced original is reference/blueprint_traced.json). The plan view also puts the legs 0.3 m further back than the
side view: side wins (BRIEF), so the top IoU is capped (~0.67): INTENDED.
Judge's reason the zoo model fails: stick-thin flat loft, small square scute teeth, tent-splayed legs (front).
Identity cue: a long broad rounded snout with brow bumps carrying the eyes, a deep heavy trunk low to the ground,
a thick tapering tail with a row of round dome scutes, stocky legs straight down beside the belly, cream jaw/belly.
Sheet measurements (side, m): back 0.47-0.50 (+ 0.03 scutes), belly 0.08, trunk half width 0.25 (top), head
0.62 long (y -1.21 .. -0.62), snout half width 0.08 at the tip, jowls 0.19, snout depth 0.12, eye bump top 0.53.
Template: abc/t9/fox/fox.py (grow with the 45 % transition ring, role_pos), leg sections tilted (theta) for the
shoulder turn.

## S1
- r1: 14-vertex half rings, 37 stations, legs from 4 x 3 windows j8-j11 + 45 % transition, tilted shoulder
  section. Gates PASS, 2,704 tris, IoU side/front/top 0.909/0.835/0.665. Critique: az000 + blueprint front — a notch
  and a level shelf between the flank and the leg's outer edge (sheet: the flank flows into a near-vertical leg
  edge). Diagnosis: the window j8-j11 starts below the flank's widest ring vertex, S0 at theta 50 / z 0.19.
  Fix: window j6-j9, S0 theta 40 at z 0.235 ru 0.10, elbow/knee theta 70.
- r2: Result: better, the flank now runs into the leg's outer edge; IoU 0.909/0.851/0.664, 2,704 tris. Critique:
  hero/az090 — the legs read as straight boxy posts (constant section 0.14 -> 0.05, hard corners), no thigh mass, no
  ankle; sheet: round haunch/elbow bulge tapering to a narrow ankle and a broad foot. Diagnosis: FORE/HIND S1-S3
  ru 0.09-0.076, exponent 2.6. Fix: elbow/knee bulge ru 0.10, wrist/ankle 0.065, exponent 2.3 (rounder).
- r3: Result: slightly better taper, IoU 0.905/0.831/0.663, 2,704 tris. Critique (EEVEE hero + reference crop of the
  sheet's legs): the legs sit 0.1 m too far forward (fore) and their roots are 0.30 m long slabs; the sheet's near
  shoulder spans y -0.44..-0.26 and the thigh 0.03..0.25 as round balls high on the flank. Diagnosis: window rings
  0.075 apart at F -0.30..-0.60 / B 0.02..0.32; S0 rs 0.125-0.15. Fix: trunk stations from a sheet KEY table, the
  window rings 0.055 apart centred on the sheet's legs (fore -0.36, hind 0.14), S0 rs 0.10 at theta 32 (a ball).
- r4: Result: legs at the sheet's positions, IoU 0.899/0.827/0.709 (top up), 2,860 tris. Critique: az090/az000 clay
  — the legs read as thin box posts (rectangular in side view, 0.16 m forearm) beside a massive trunk; the sheet's
  legs are ovoid masses (big round elbow/thigh bulge, then a taper). Diagnosis: FORE/HIND S1-S3 ru 0.078-0.095,
  exponent 2.3 (boxy corners). Fix: S0/S1 exponent 2.0 (round), elbow/knee bulge ru 0.11 rs 0.115, forearm 0.095,
  wrist 0.08, foot 0.10.
- r5: Result: rounder ovoid legs, IoU 0.901/0.820/0.708, 2,860 tris. Critique: az000 clay — the "tent" look: each
  leg goes out level from the flank (a shelf) to an elbow at x 0.41 and leaves a 9 cm dark gap to a keeled belly;
  sheet front: the flank curves into a leg edge <= 0.37 and the round cream belly almost touches the legs.
  Diagnosis: S1 centre x 0.31 ru 0.11 at theta 62 (outer 0.407); BODY j10-j12 keel (fx 0.60/0.34).
  Fix: legs in under the flank (S1 outer 0.37, column x 0.20-0.37), belly fx 0.70/0.42 at fh -0.81/-0.94.
- r6: Result: better — the legs stand beside the round belly, no tent; IoU 0.901/0.871/0.710 (front up), 2,860
  tris. Critique: az090/az045 clay — each leg is a straight-walled pillar (outer wall flat at x ~0.37 from the
  shoulder to the foot); the sheet's thigh/shoulder is a big ball that tapers to a narrow ankle with the foot
  flaring out. Diagnosis: S0-S3 outer edges 0.36-0.37 constant. Fix: S0 ru 0.11 / rs 0.115, elbow-knee ru 0.10
  rs 0.12, wrist/ankle pulled in (x 0.282, ru 0.066).
- r7: Result: better — a thigh/shoulder mass, a pulled-in ankle and a flaring foot; IoU 0.899/0.851/0.714, 2,860
  tris. Critique: az000/hero — the head reads as a pig/anteater snout: the tip is a flat round disc (H8 W 0.05
  capped) and the brow bumps are invisible (sheet front: two domes 0.05 over the skull carry the eyes).
  Diagnosis: H8 cap, BUMP lifts <= 0.036. Fix: tip rounds over H8/H9 (W 0.062 / 0.036), bumps 0.052 peak at H0.
- r8: Result: the brow domes read from the front and side, the tip rounds; IoU 0.902/0.857/0.713, 2,912 tris.
  Critique: az000 — the head reads small and narrow against the trunk (sheet front: jowls 0.21 half width, the head
  nearly as wide as the body). Diagnosis: C0/C1 W 0.205/0.195, H0 0.178. Fix: C0 0.218, C1 0.212, H0 0.19,
  H0b 0.17, H1 0.148.
- r9: Result: better — the jowls read as the head's broad back, the head no longer a thin wedge on the trunk; IoU
  0.902/0.853/0.710, 2,912 tris. Reads as the sheet's chunky croc from every clay view (top IoU capped by the
  sheet's plan view, INTENDED). Fix: none, lock r10 (same program).

## S1 lock r10 (aa05f257), 2,912 tris, IoU 0.902/0.853/0.710

## S2 (run inside the S3 rounds)
- eye socket inset on the brow dome's outer face (ray aimed at (0.13, -0.775, 0.488) from out-up), flat snout top
  (j0-j3, H2-H6). s2 IoU vs s1 0.997.

## S3
- r1: ray miss fixed (eye aim). r2: FAIL float 4 (right claws had no toes: parts are not mirrored) -> toes built
  per side with side=-1. r3: FAIL z-fight 21 (toe soles 3 mm over the foot sole, limit 3.6 mm) -> lift 6 mm.
- r3: all gates PASS, 4,944 tris, 7 colours, detail PASS 7 groups, borders stairs 30 -> 2. Critique (colour
  az090/hero vs sheet): reads as a dark green gator, the cream only a thin under-band; sheet: khaki olive with a
  big cream belly + lower flank to ~45 % height, cream jaw/jowl. Diagnosis: PAL olive #74774a (green), body_rule
  cream at fh < -0.28 (down-facing faces only). Fix: palette sampled off the sheet (olive #7a7656, cream #ead6a0,
  scute #68644a; owner pick needed on palette), cream to fh < -0.10 on the trunk (j8 border), -0.22 on the tail.
- r4: Result: khaki olive matches the sheet; the cream border stays on j8 (faces j7-j8 centre fh -0.07, so the
  threshold change moved nothing: the extent was already the sheet's, it reads small because the lower flank
  faces down into shade). 4,944 tris, gates PASS. Critique: hero/az045 — toes read as thin spiky splayed fingers
  (sheet: fat round cream-olive toes with dark claws). Diagnosis: digits_splayed width 0.030 height 0.024 length
  0.062 + long claws. Fix: toes 0.042 x 0.030, length 0.046-0.054, claws shorter (0.024) and taller.
- r5: (r5a: a comment swallowed the forward/side args -> rerun.) Result: fat toes read as round toes with dark
  claws; gates PASS, 4,944 tris, detail PASS 7 groups. Residual for S4/fix loop: teeth read as thin white pegs
  in the head close-up; the lower-jaw cream band on the snout sits in shade. Stage 3 round cap reached.

## S4
- r1: kit gates PASS (glbcheck OK), eyes PASS (0.48/0.85/0.68, 38 mm = 0.075 head), tail0 PASS, detail PASS (8
  groups). FAIL upperarm.L/R knife 5 (2.24 r, 136 deg) + shoulder shelf 0.88 r^2 / 1.88 r wide; thigh.L/R knife 4
  (1.68 r). Crop B (flags): the leg's rear/front walls meet the flank square (a box set into the side) and the leg
  top is a level ledge. Diagnosis: the 4 x 3 window j6-j9 is as long as S0 (0.22 vs 0.224), so the transition
  walls run perpendicular to the flank; the window top j6 sits level with S0's top. Fix (S1 re-lock; lock r10 kept
  in before_s4r2/): 5 x 4 windows j5-j9 (0.275 long, top on the back bevel) at 0.055 ring spacing, S0 unchanged:
  the walls now slope into the flank. s1 r11: PASS, 3,240 tris, IoU 0.902/0.847/0.708.
- r2 (lock r12 55?): Result: better — shelf gone (0.0), the walls slope into the flank in crops A/B; knife
  upperarm 1.32 r (136 deg), thigh 1.03 r (152 deg), strips 0.93-0.96 r (PASS), eyes PASS, all kit gates PASS.
  Critique: crop C / flags — small red folds at the window's lower front/rear corners (armpit/groin, the leg's inner
  wall meeting the belly). Diagnosis: the transition ring goes 45 % of the way to S0's inner edge in one step.
  Fix: T1_LEG 0.45 -> 0.33 (the turn spread over the transition + S0 rings; S1 re-lock).
- r3 (lock r13 6424a8e4 superseded): T1 0.33 -> no help (upperarm 1.32 r, thigh 1.33 r worse). Crops A/B: a
  dark vertical crease where the leg's front/rear wall meets the flank, flagged at its lower end. Diagnosis: the
  lerp transition rises off the flank as fast as it narrows, so the wall leaves the flank at ~70 deg. Fix: fillet
  transition — narrow 55 % along the flank, rise only 18 % off it (TS/TN), S0 does the rest.
- r4 (lock r14): Result: better — the legs rise out of the flank through a fillet in crops A/B; knife upperarm 1.05 r,
  thigh 1.03 r (limit 1.0), shelf 0.26 r^2 (PASS), eyes PASS. Critique: flags only at the 4 window lower
  corners (tiny triangles in the armpit/groin shade). Fix (stage 2 vertex move, lock kept): the corner root vertex
  and the flank vertex under it ease out 14 / 7 mm along the flank normal.
- r5: Result: junction probe PASS (upperarm knife 0.87 r, thigh 0.82 r) but FAIL s2 self-intersection 12 hits
  (the eased flank vertex under the corner crosses the transition ring). Fix: ease only the corner root vertex.
- s2 r1-r2 (checks only): corner ease 14 / 7 mm still self-intersects (12 / 2 hits): the TN 0.18 transition ring
  sits within ~1 cm of the flank at the corners. Fix: TN_LEG 0.18 -> 0.26 (S1 re-lock r15; r14 kept in
  before_s4r2/) + corner ease 7 mm. s2 r3: PASS (closed, no hits).
- r6 (lock r15): ALL S4 gates PASS — kit (glbcheck OK, techqa hit/float/zfight 0, slivers 1.3 %, posed 0, drift
  0), junction probe 5/5 PASS (upperarm knife 0.61 r strip 0.79 r shelf 0; thigh knife 0.60 r strip 0.97 r; tail0
  0), eyes PASS (0.48/0.84/0.68, 38 mm = 0.075 head), detail PASS 8 groups, clips PASS after --clips --fix-clips
  (move pen 10.07 -> 0.011, slide 1.05 -> 0.000), --pack PASS (LOD IoU 0.992/0.979/0.953, round-trip PASS), --rom
  audit 51/60 (upperarm/forearm/thigh/shin/foot extremes: audit only), separation PASS (tail-hind 0.19 m).
  5,272 tris. Champion 0 of the fix loop; backup before_fix1/, renders review_r6/.

## Fix loop (WORKFLOW s11), CHECKLIST.md frozen before round 1
- Champion (r6) checklist: YES 1-8, 11-15; NO 9 (teeth read as thin flat white tabs, face_34), 10 (claws not
  countable at 192 px). Score 13/15.
- Round 1 target NOs 9+10. v1 (s4 r7): 4 chunky cone teeth a side (r 12 mm, 24-32 mm) + bigger claws (34 x 28 mm).
  v2 (s4 r8): 3 big cone teeth a side (r 15 mm, 32-38 mm) + cream toes (claw contrast) + bigger claws.
  Fast path (2026-10-24): v1 adopted as the program default (CROC_VAR default 'v1'); v2 not built (no 2-variant rounds).
- s4 r8 (final gates, v1): kit FAIL qa hit 8 shells (2 claws + their toe per foot, tech crop: magenta on the claw
  roots). Diagnosis: the bigger v1 claw (34 x 28 mm) root row sinks 26 mm into the tapering toe tip at full section,
  so it exits the toe sides. r9: claw floor +5 mm -> no change (reverted). Fix r10: root row 10 mm in at 75 % section.
- s4 r10: Result: ALL S4 gates PASS — kit (glbcheck OK, hit/float/zfight 0, slivers 1.3 %, posed 0, drift 0),
  junction 5/5 PASS (upperarm knife 0.61 r, thigh 0.60 r, tail0 0), eyes PASS, detail PASS, clips PASS after
  --clips --fix-clips (identity PASS), --pack round-trip + LOD PASS, --rom audit (shin/foot extremes). 5,432 tris.
- A/B vs zoo/crocodile champion (same orbit renderer, final/ vs zoo_champ/), fresh Opus seat per order: new as A ->
  A wins; new as B -> B wins. Both orders pick new: ADOPT (candidate for promotion, zoo untouched). Both seats: the
  winner's biggest flaw is boxy hard-edged leg columns (no rounded thigh/shoulder bulge). ab_vs_zoo.jpg, orbit18_sheet.jpg.
