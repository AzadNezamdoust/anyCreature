# tiger (t9 RECREATE, 2026-10-23) — NOTES

Rebuild from scratch of zoo/tiger (owner-approved), program built from the t9 fox program (loft / grow / grow_ear).
reference/ + blueprint.json copied from zoo/tiger (sheet refs/gpt/v3/tiger/sheet_1.png, kit/refs.py height 1.1).
Judge's reason the zoo model fails: lanky, small blocky head, evenly spaced vertical bar stripes (barcode).
Identity cue: STOCKY tiger, big round head with a white cheek ruff (front half-width 0.22 at z 0.80-0.86), deep chest
(back 0.83, belly 0.36: 0.47 m deep), heavy forelegs (0.13-0.15 wide) and big cream paws, a thick (0.15 m) tail with a
black club tip, stripes that follow the body form, taper to points and vary (long/short, lean, wedges from the belly).
Sheet measurements (reference masks, m): nose y -0.916 z 0.76-0.80; crown 1.07; ears to 1.10 at x 0.06-0.17; chin 0.665;
withers 0.95 at y -0.38; back 0.83 flat y -0.15..0.25; rump 0.74 at 0.43; legs x 0.03-0.21; paws 0.21 long.
Density: 16-vertex half rings; key stations hand placed (~8.5 cm), torso spans split 3x and tail spans 2x by straight
vertex lerps (co-planar: the planes are the key loft's, the density carries the stripe borders).

## S1
- r1: 5,680 tris, IoU side/front/top 0.845/0.884/0.834 (zoo lock 0.823/0.768/0.819). FAIL self-intersection 20 pairs
  at the fore window's inner rim (x 0.065, z 0.38). Critique (az000/hero): reads stocky with a big head; the fault is
  the fore root. Diagnosis: FORE[0] at z 0.42 sits ABOVE the window's inner rim (j14, z 0.37), so the transition ring's
  inner wall folds back up into the chest bottom. Fix: leg root sections below the inner rim (FORE[0] z 0.36, HIND[0]
  z 0.385, the next stations stepped down with them).
- r2: Result: PASS (self-intersection 0), 5,680 tris, IoU 0.850/0.881/0.834. Critique (ortho front + az000): the
  muzzle is a small round snout tube poking out of a big face (sheet front: a broad flat muzzle with whisker pads
  x +-0.09 and a wide nose). Diagnosis: H4-H7 W 0.145/0.115/0.092/0.062 and MUZ prof(3.0, 2.6) round. Fix: H4-H7 W
  0.155/0.135/0.112/0.082, MUZ prof(3.4, 2.8, 0.90) boxier.
- r3: Result: PASS, 5,680 tris, IoU 0.850/0.881/0.829; the muzzle now a broad box (front). Critique (ortho side +
  az090): the ears read as thin spikes from the side and small knobs from the front (sheet: round cups ~0.10 wide and
  deep). Diagnosis: EAR front-back scales 0.72/0.58/0.32 of a 5 cm root window. Fix: front-back 1.25/1.10/0.62,
  across 1.0/0.88/0.50, tip 1.117.
- r4: Result: PASS, 5,680 tris, IoU 0.850/0.878/0.829; ears now ~8.6 cm wide, a round knob (front). Critique (az180,
  az135): the hind (and fore) legs stand as columns under a ledge: a dark step at z ~0.42 where the leg's outer wall
  sticks out past the flank. Diagnosis: leg outer x 0.212 > the window rim j11 x 0.86 W = 0.19, so the transition ring
  steps OUT under the flank. Fix: a boxier lower flank (BODY j8-j14 out: j11 0.91 W) and the leg sections 5 mm in
  (cx -0.005, rx -0.005 above the paw): outer 0.20 = the rim.
- r5: Result: PASS, IoU 0.850/0.891/0.828 (front up). Critique (az180 + sheet rear measured): the rump reads narrow
  and the hind legs stand as posts under it (sheet rear: haunches 0.24 half-width at z 0.50-0.60, as wide as the
  shoulders; legs 0.21). Diagnosis: R0/B0/B1/B2/B3 W 0.172/0.205/0.220/0.218/0.205. Fix: 0.195/0.226/0.238/0.232/0.214.
- r6: Result: PASS, IoU 0.850/0.892/0.837 (top up), hips now read wide from the rear. Critique (az180/az135): a dark
  down-back facing band across the hind leg tops at z ~0.42 persists. Diagnosis: the thigh's rear wall notches
  forward: HIND[0] rear y 0.422 (z 0.385) -> stifle rear 0.353 (z 0.32) -> gaskin 0.397; sheet: the rear line runs
  straight down from the buttock to the hock (y 0.42-0.50). Fix: stifle cy 0.295 ry 0.108 (rear 0.403), gaskin cy
  0.34 (rear 0.425), hock cy 0.395 (rear 0.463); knee joint with it.
- r7: Result: PASS, IoU 0.852/0.892/0.837; the rear band is gone (az180: haunch flows into the legs). Critique
  (az090/az000): the ears still read small next to the big head (sheet: 0.10 wide cups rising ~0.08 over the skull
  side). Fix: EAR stations higher (1.088/1.118/1.136) and wider (1.05/0.95/0.55 across).
- r8: Result: PASS, IoU 0.851/0.882/0.837. Critique (ortho front): the ears are square posts with flat tops (sheet:
  round cups leaning out). Fix: across 1.00/0.80/0.40 (round top), front-back 1.40/1.25/0.70, centres 4-11 mm outward.
- r9: Result: PASS, IoU 0.851/0.886/0.837; ears now round cups leaning out (front). Remaining S1 view: reads as a
  stocky big-headed tiger from every clay view; the ruff/face come from S2/S3 (paint, tufts). Lock next round.

## S2 (run inside the S3/S4 rounds): eye socket inset (ray at (0.078, -0.752, 0.878) from the front-out), flat muzzle
bridge (j1-j3) and side (j5-j10) planes H4-H7, slanted nose pad cap.

## S3
- r1: FAIL z-fight 4 (piece_ruff), 6,580 tris, 6 colours; borders 72 despeckled, 52 cuts, stairs 148 -> 54.
  Critique (hero/az090 colour): the stripes merge into a dark saddle over the back (and the orange reads red-brown).
  Diagnosis (face grid dump of body_rule over the loft): 14 stripes 0.07 apart with w 0.02-0.032 cover ~50 % of the
  back faces; 1-face gaps get despeckled into the stripes. Fix: 11 + 1 stripes 0.085 apart, long w 0.024 / short
  w 0.017 starting off the spine, wedges re-spaced; fur #d4702a -> #dc8236 (sheet orange; owner pick if it matters).
- r2: FAIL z-fight 4 (ruff). Critique (az090/hero colour): the long stripes read, but the short ones and the leaning
  parts are broken into fragments, fewer stripes than the grid dump. Diagnosis: smooth_borders despeckle (57 faces)
  recolours every stair-step face of a 1-face-wide leaning stripe (3 border edges) back to fur. Fix:
  smooth_borders(despeckle=False) (kit shield, 10-23).
- r3: FAIL z-fight 4. Result: stripes now read as tiger stripes (tapered, leaning, long/short, wedges; top view
  chevrons over the spine), stairs 130 -> ~50. Critique (gate): the ruff tufts' broad faces lie parallel to the
  cheek within 3 mm (z-fight 4 faces). Diagnosis: tuft direction (0.40, 0.80, -0.45) runs along the cheek, so the
  fan's flat side faces +x like the cheek. Fix: d (0.62, 0.62, -0.45) / (0.55, 0.60, -0.60): tufts stand off at ~45 deg.
- r4: PASS (z-fight 0), 6,580 tris, 6 colours. Critique (az000/hero colour crop vs sheet front): the face reads as
  an orange box with a grey jaw and a pig snout (two whisker-pad discs), the eye is lost on the orange, the ruff tufts
  stand out as blocks. Diagnosis: pads piece; lens 32 mm amber on fur with no light around it; cheek cream only below
  v 0.50; cream #f2e4c8 renders grey; tufts 0.028 thick at 45 deg. Fix (the face read): pads removed, lens 38 mm,
  a small cream brow spot over each eye (sheet's white patch; not a ring), cheek cream from v 0.44 on H1-H3, cream
  #f7ead2, tufts longer/thinner swept back-down.
- r5: PASS, 6,492 tris, 6 colours; cheeks cream, brow spots, no pig snout. Critique (az000/hero crop): the eye is
  still a 8 px dot. Diagnosis: the lens disc sits at socket + 4 mm while the socket is sunk 6 mm: the 19 mm rim is
  under the skin, only the pupil cap shows. Fix (carried into S4 r1): lens at socket + 10 mm.

## S4
- r1: kit gates PASS (glbcheck OK, techqa posed clip warn 8 tris 0.10 %), detail PASS, eyes PASS 0.57/0.85/0.64
  (38 mm = 0.084 head), membranes PASS, junctions ears/upperarms/thighs PASS; FAIL tail0 knife 6 (1.37 r, 127 deg).
  Critique (tail0 crops A/B flags): red knife folds at the lower sides of the tail root where the tail underside
  meets the buttock. Diagnosis: the bottom seam zig-zags R0 z 0.452 -> T9 0.478 -> T8 0.413 (the root ring's bottom
  sits above both neighbours). Fix: T9 bottom (0.447, 0.452), a monotonic underside; S1 re-lock (lock f81f3a58 moved
  to scratch). Backup before_fix0/.
- r2: tail0 knife WORSE 8 (1.85 r, 119 deg); other gates as r1. Crops (j4 A/C flags): the fold sits under the tail
  where the tail's underside meets the hind window's rear rim on R0 (the thigh's rear wall), not on the seam.
  Fix: T9 reverted to r1; hind window moved one key forward (B0..B3, R0 left free as the buttock ring between the
  thigh and the tail root), HIND sections and J 6 cm forward (paw y 0.33; sheet paws 0.19/0.39, mean 0.29). Re-lock.
- r3: tail0 knife 6 (1.37 r, 126.9 deg) = r1 exactly: not the window (thighs now 0/0.46 r, upperarms 0/0.61 r, eyes
  0.58/0.87/0.65); IoU 0.842/0.886/0.838. Diagnosis: the fold is the tail's lower side wall against the buttock's
  rear face: R0 W 0.195 -> T9 W 0.10 turns the lower flank inward in one span, then the tail side drops. Fix: T9 W
  0.14 (a broad root blended over the buttock), T8 W 0.076 -> 0.088. Re-lock.
- r4: Result: ALL S4 round gates PASS — kit (glbcheck OK, techqa posed clip warn 8 tris 0.10 %), junction 7/7 PASS
  (tail0 knife 0.85 r, thighs 0/0.46 r, upperarms 0/0.61 r, ears 0.82 r/strip 1.0 r), eyes 0.57/0.85/0.64 (38 mm =
  0.084 head), membranes PASS, detail PASS 8 groups (tail, ear, claws, eye, nose, ruff, cream, stripe).
  --clips --fix-clips: before move pen 5.41/slide 2.59, attack pen 0.68 -> after all PASS (pen <= 0.004, mesh/skin
  identity PASS); --pack PASS (round-trip + LOD gate); --rom audit 8 fails (neck/upperarm/forearm/thigh/shin flex,
  tail0 ext: audit only); separation PASS (tail-hind 0.189 m). IoU 0.842/0.886/0.834. 6,492 tris. Champion 0.
  Backup before_fix1/ (program + stage4).

## Fix loop (WORKFLOW s11), CHECKLIST.md frozen
- Champion 0 (s4 r4) checklist: YES 1,3,4,5,8,9,10,11,12,13,14,15; NO 2 (head + ruff ~0.8 of the chest from the
  front), 6 (stripes still near-even vertical from the side), 7 (top: rows of equal bars). Score 12/15.
- Round 1 target NOs 6+7. v1 (s4 r5): irregular spacing 6-11 cm, varied starts off the spine, two forks, mixed widths.
  v2 (s4 r6): the r4 rhythm with 2x lean / 1.5x bend and the short stripes starting off the spine (v 0.14).
- Round 1 judge (fresh Opus seat per order, sheet referee): v1 AB -> v1, BA -> v1: v1 WINS both orders -> champion
  (gates PASS: junction 7/7, detail, eyes; reasons: forks/taper/varied length vs a barcode). v2 AB -> v2, BA ->
  champion: flip = TIE. v1 score 13/15 (6 YES); new visible flaw: closed loops / letter shapes where a fork or a
  short stripe touches its neighbour (u090/top), so 7 stays NO.
- Round 2 target NO 7. v3 (s4 r7): v1's list painted on the loft's own face grid with a separation pass (a cell
  touching another stripe's cell is dropped from the narrower one). v4 (s4 r8): v3 without the forks.
