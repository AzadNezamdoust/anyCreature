# fox (t9 RECREATE, 2026-10-23) — NOTES

Rebuild from scratch of zoo/fox with the zoo workflow v2 + proven tricks (HANDOFF "Wave-new status"). Concept:
refs/gpt/v3/fox/sheet_1.png; reference/ + blueprint.json copied from zoo/fox (same sheet, kit/refs.py --height 1.1).
Template code: zoo/hippo/hippo.py (grow() with the 45 % transition ring, role_pos), fox palette from the champion.
Identity cue: long pointed muzzle + big upright dark-backed ears + a fat white-tipped brush + dark stockings.
Sheet measurements (blueprint, m): body top 0.762 flat, belly 0.39-0.43, chest half-width 0.19 (front z 0.55),
cheek ruff 0.19 (front z 0.80), legs x 0.045-0.145 (chunky 0.10 socks), brush 0.26 wide / 0.27 deep.

## S1
- r1: first fit, loft 14-vertex half rings (2x), legs from 4 x 3 lower-flank windows (j9-j12) + 45 % transition
  ring, ears 1 x 2 skull windows (ring morph). Gates PASS, 2,704 tris, IoU side/front/top 0.797/0.859/0.859
  (champion lock 0.770/0.802/0.761). Critique: az000/az090 — ears small and thin vs the sheet's broad ears.
  Diagnosis: the 2-face window j1-j3 is only 0.065 m across (sheet 0.10). Fix: 3-face window j1-j4.
- r2: Result: 2,736 tris, IoU 0.797/0.874/0.859 (front up). Critique: az000 — the ears still taper to a spike too
  early (sheet: broad triangles). Fix: ear ring scales 1.0/0.9/0.6/0.16 across (was 0.95/0.78/0.48/0.14).
  (S1 junction probe: no rig at S1, so the probe finds no roots; it gates from S4.)
- r3 (LOCK c412c222): 2,736 tris, IoU 0.797/0.874/0.859. Critique: az000 clay — ears 0.085 wide, set inboard; the
  sheet's ear base is 0.10 and reaches the head's outer edge. Diagnosis: window j1-j4 ends at x 0.149. Fix (re-lock
  r4): 4-face window j1-j5 (onto the skull side: "ears leave the head side"), ring morph kept.
  Lock r3 removed (moved to scratch) for the r4 ear re-lock.

## S2 (run inside the S3 rounds)
- eye socket inset (ray at y -0.64 z 0.845), flat muzzle bridge (j1-j3) and side (j5-j8) planes H4-H7, slanted
  nose pad cap.

## S3
- r1: gates PASS (6 colours, 3,360 tris, borders: stairs 32 -> 14, 3-to-1 22 -> 1), junction PASS; detail FAIL
  count 4 < 6. Critique: hero/az090 colour — the cream band covers the whole lower flank and leg tops (reads grey),
  cheeks orange (sheet: white cheeks). Fix: paint rule — belly underside only (fh < -0.88), forward-facing bib,
  cheeks/muzzle cream below the eye line; plus details: nose knob, 2 cheek-ruff tufts, brush-tip tuft.
- r2: detail PASS (7 groups), junction PASS, 3,624 tris. Critique: hero/az090 — a cream band across the hind thigh
  tops (the leg-root transition ring fell outside the leg test, so the belly rule painted it); cheek tufts read as
  ear-muffs. Fix: leg test up to z 0.47 outboard of x 0.06; tufts flatter, laid back along the cheek; smaller tip tuft.
- s3 r3 folded into S4 r1.

## S4
- r1: kit gates PASS (glbcheck OK, posed clip warn 4 tris 0.02 %), detail PASS (7 groups), eyes PASS
  (0.70/0.84/0.52, 33.6 mm = 0.097 head), legs/tail junctions PASS (upperarm knife 0 strip 0.6 r; thigh 0/0;
  tail0 knife 2 deg-cases 0 r), membranes PASS. FAIL ear.L/R seam strip 1.91 r, 12.5 mm wide: crop B shows the
  thin band on the ear's back root. Diagnosis: ring 1 a fixed station 3 cm over the root. Fix: ring 1 = the 45 %
  transition ring toward the next station (proven trick); S1 re-lock (lock r4 83a959bb removed).
- r2 (champion 0 of the fix loop; S1 lock c560fd87): ALL gates PASS — kit (glbcheck OK, techqa posed clip warn
  4 tris 0.02 %), junction probe 7/7 PASS (ear strip fixed), eyes PASS, membranes PASS, detail PASS (7 groups:
  eye, claws, nose, ruff, tuft, cream, sock), clips PASS after --clips --fix-clips (move pen 3.50 -> 0.010, slide
  2.75 -> 0.003), --rom audit (thigh flex +60 stretch 2.3, shin flex -90 vol 0.74: audit only), --pack PASS (LOD
  IoU 0.995/0.983/0.964, round-trip PASS), separation PASS (tail-hind 0.080 m). 3,624 tris. Backup before_fix1/.

## Fix loop (WORKFLOW s11), CHECKLIST.md frozen 06:45
- Champion (r2) checklist: YES 1,2,3,8,9,10,11,12,13,14,15; NO 4 (ear a flat spike from the side), 5 (brush narrow
  from the rear), 6 (white tip small), 7 (boxy hind stifle cuff, az225). Score 11/15.
- Round 1 target NOs 5+6. v1 (s4 r3): tip cream from y 0.655 + brush x1.16 across (stage-2 ramp from the root).
  v2 (s4 r4): tip cream y 0.655 + brush section x1.12 across and x1.08 in depth about each station centre.
- Round 1 judge (fresh Opus seat per order, sheet referee): v1 AB -> v1, BA -> champion: flip = TIE -> champion;
  v2 AB -> v2, BA -> v2: v2 WINS both orders -> champion (gates all PASS: junction 7/7, detail, clips, separation
  tail-hind 0.081 m). Score v2 13/15 (5, 6 YES). Remaining NOs: 4 (ear spike from the side), 7 (stifle cuff).
- Round 2 target NO 4. v3 (s4 r5): ear rings above the root x1.4 front-back about the ear axis; v4 (s4 r6): x1.25
  front-back + x1.1 across.
