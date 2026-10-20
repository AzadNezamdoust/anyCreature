# frog (sitting bullfrog; t7 hand box model, zoo workflow v2) — NOTES

Concept: refs/gpt/v3/frog/sheet_1.png (2x2). `kit/refs.py --height 0.30` -> blueprint.json + reference/
(length 0.479 m, width 0.428 m incl. the drumsticks). refs WARNING: the plan view is 0.76 x as wide as the front view
(the top render is not to scale across); the side and front views win for widths, the plan view only gives the
snout taper (relative widths).
Identity cue (bullfrog, not toad/newt): a wide flat head with two raised round eye domes on the skull's top edges, a
wide mouth line over a pale bulging throat, a squat pear body whose belly sags to the ground, short thick front legs
under the chest, and big folded hind legs lying as egg-shaped drumsticks along the rear flanks, long feet forward.
S1 carries the domes, the throat, the squat body, the short arms and the drumsticks; feet/fingers come as S3 pieces.

Technique: one spine loft of 14-vertex hand-placed half rings (24 vertical stations, snout tip -> rump cap). Limbs
are extruded from broad loft windows by `grow()`: the window's boundary vertices keep their angular order and are
spread at even angles round each limb section (any section frame: level rings for arms and domes, flank-parallel
rings for the drumsticks), interior window vertices go to a Coons patch (the cap); the first new ring is a sloped
transition ring (45 %). Front legs: 3 x 3 window on the lower chest (C0-C3, j6-j9). Drumsticks: 5 x 6 window on the
rear lower flank (B0-R0, j4-j10), sections parallel to the flank pushed 3-9 cm out. Eye domes: 3 x 3 window on the
skull's top edge (H0-H3, j1-j4), level rings going up.

## Stage 1
- r1: first fit. 1,996 tris, IoU side/front/top 0.872/0.886/0.721; FAIL self-intersection (36 pairs at the hind
  window). Critique: az135/az180 — the hind leg is a flat disc wheel with dark notches in its outer face.
  Diagnosis: grow()'s interior (cap) vertices were placed at 0.8 x their window coordinates and folded over the
  evenly re-spaced boundary. Fix: interior vertices by a Coons patch of the boundary in grid index space.
- r2: cap folds gone, 2,068 tris; still FAIL (52 pairs). Critique: az180/top — the drumstick is a wheel on a narrow
  stalk. Diagnosis: the 4 x 5 window (0.10 x 0.10 m) is much smaller than the drumstick (0.20 x 0.13) and its first
  section overhangs the flank above it. Fix (r3): tuck the rear lower flank, 5 x 5 window, near-full first section.
- r3: worse (72 pairs, still a wheel). Fix (r4): the rear rings' widest level dropped low (f 0.32) so the lower
  rear flank stands out at x 0.14; 5 x 6 window B0-R0 j4-j10 (the drumstick's footprint).
- r4: still a detached-looking wheel and 72 pairs. A ring dump (DEBUG prints) showed the transition ring collapsed to
  a 4 x 4 cm patch: every section was turned 180 deg against its window. Diagnosis: the even-angle offset was an
  arithmetic mean of wrapped angles (-pi and +pi averaged to 0). Fix (r5): circular mean (atan2 of summed sin/cos).
- r5: the drumstick now leaves the flank broadly (az180) and the arms face the right way; 2,148 tris; 10 pairs left at
  the arm's rear wall (y -0.04) against M0's flank. Fix (r6): tuck the chest/belly bottom (C1-M2) and move the arm
  window up one vertex (j6-j9, the shoulder).
- r6: PASS (0 pairs), 2,148 tris. Critique: az135/az180 — the drumstick is a cylinder with a flat outer face.
  Fix (r7): five sections that swell then round off over three rings to a domed end; axis pitched 10 deg, yawed.
- r7: PASS, 2,236 tris: an egg from the side. Critique: az000/hero — the head is a box with a flat face; the snout
  front shows a radial fan. Fix (r8): snout taper from the plan view (0.32/0.56/0.72 of the body width at
  4/8/10 cm), throat bottoms 1-2 cm lower; dome window moved back one ring (H1-H3) to the sheet's eye y.
- r8: PASS, IoU 0.888/0.892/0.727: a rounded wedge snout and a bulging throat. Critique: az000 — the front legs are
  thin stilts on the body's sides. Fix (r9): thick arms set in to x 0.13 (they overlap the chest in the front view),
  the chest tucked below so the arm clears it; arm moved 6 mm forward (r9a: its rear wall cut M0, 16 pairs).
- r9: PASS, IoU 0.893/0.896/0.735. Critique: hero/az090 — the eye domes are small octagonal turrets.
  Fix (r10): 3 x 3 dome window (H0-H3, j1-j4: x 0.04-0.10 as the sheet), 12-vertex elliptical rings, 4 closing rings.
- r10: PASS, 2,348 tris: round domes. Critique: az180 — the drumstick reads as a short cylinder from behind, the rump
  as wide as the legs. Fix (r11): tuck the rump's underside (B0-R2, tuck 0.08-0.30).
- r11: little visible change (the window centre moved 1 cm in). Fix (r12): fuller, deeper drumstick sections
  (r 0.094-0.10 x 0.064-0.07), yaw 0.24 -> 0.14 rad, starting 2.6 cm out.
- r12: PASS, 2,348 tris, IoU 0.904/0.888/0.718 (top is low by design: the plan view is 0.76 x scale): the rear view
  reads as two lumps either side of the rump. Lock next round.
- r13 LOCK (2,348 tris), then a minimal S2-S4 build to probe the junctions (s4 r1), as the rhino did.

## Stage-1 re-locks driven by the junction probe (lock deleted and re-made each time; old locks in old_locks/)
- s4 r1 probe: thighs knife 1.36 r (144 deg) along the window's rear edge R0 (the drumstick's rear wall leaned back
  over the rump); arms knife 2.35 r (172 deg) where the level first arm ring sat 1.5 cm under the window centre;
  feet toes = separate shells = probe gaps; z-fight 16 (finger soles on the hand's sole cap); eyes PASS.
- r14 lock: hind window B0-R1 (6 spans, rear edge 2 cm further back), R1/R2 fuller. Result s4 r2: thigh knife 0.67 r
  PASS; arm still 2.23 r (159 deg under the shoulder: the level first ring folded the armpit wall back up).
- r15 lock: first two arm rings tilted (outer side up 42/19 deg). s4 r3: arm knife 0.89 r PASS, strip 1.63 r (0.8 mm).
- r16/r17/r18 locks (smaller ring / flared collar / lower j7-j10 window): each worse (knife 1.65 / 1.89 / 2.86 r);
  flag dumps (scratch flagdump.py) showed the arm (6.4 x 6 cm) was as big as its 3 x 3 window, so no transition band.
- r19 lock: 4 x 3 arm window C0-M0 j6-j9 (the proven leg root); knife 1.06 r. r20: arm rings 1 cm back so the rear
  wall drops straight from the rim: knife 0.74 r, strip 1.47 r (7 mm band at the rim's rear-bottom corner and armpit).
- r21 LOCK (final, 2,452 tris, edge sha256 108165445d564e59): arm transition ring 60 % in-plane / 50 % out (was 45/45):
  the rim band widened; arm strip 0.81 r PASS. Junction probe PASS.

## Stage 2 (vertex moves + one logged inset)
- eye socket: `inset` in the dome face hit by a ray along (0.78, -0.50, 0.30), sunk 1.5 mm (keep_valleys there).
- s4 r14: drumstick outer end domed out 9 mm (orbit az135/az225 showed a flat disc with concentric rings).
- s4 r16: head 14 % wider ahead of y -0.15, easing to 1.0 at the chest (side_by_side: the sheet's head is ~0.75 of
  the body width at the mouth, ours ~0.6, the domes stood up like ears). IoU vs S1 min 0.948.

## Stage 3
- Pieces: lens eyes (10-sided, 22.9 mm = 0.092 head, gold iris, black pupil; front/3q/side 0.54/0.88/0.71);
  fingers (4 per hand, tapered boxes with bulb tips, hand-built: `hand_three_finger`/`hand_mitten` are palm+finger
  hands for a hanging biped hand, not splayed frog fingers on the ground); hind feet hand-built (no library frog
  foot: `bird_foot` toes are thin claws without bulbs): one closed shell per foot, a slender slanted-sided shank
  embedded in the drumstick's underside, its front split in five quads swept forward as toes with knobs.
- Colours 5: olive skin, cream throat/belly (border on the mouth line, then down behind the arm), toe tips, iris,
  pupil. s4 r13: olive not lime; the darker 'back' patches dropped (rectangular blocks on the back).
- s4 r9: feet one shell (gaps 0), fingers lifted 2 mm off the hand's sole cap (z-fight 16 -> 0), feet bound per
  vertex to the nearest bone (body weights stretched the toes 7x in the hop). r10/r12: sole rows 3 -> 9 (slivers
  3-4 % -> 1.6 %); r12: the sole a slender shank (it read as a board in the orbit).

## Stage 4
- Rig: hips/spine/chest/head trunk, upperarm/forearm/hand, thigh/shin/foot (thigh hip -> knee forward through the
  drumstick, shin back along it, foot forward on the ground), roll='auto'. Clips: idle (throat/chest breath), move
  (a short hop: crouch, thighs/shins extend, hips up 3 cm), attack (lunge, head up).
- s4 r16 FINAL: every kit gate PASS (lock, glbcheck OK, techqa: hit 0, float 0, z-fight 0, slivers 1.6 %, fold-overs
  0, drift 0; warn: none failing). Junction probe PASS: upperarm knife 0.74 r / strip 0.81 r; thigh knife 0.66 r /
  strip 0.87 r; slit 0, open 0, gaps 0, clip 0. Eyes PASS. Separation PASS (fore L/R 0.205 m, hind 0.262 m).
  3,580 tris (body 2,468, feet 744, fingers 288, eyes 80).
- Owner-style review (orbit18 + zoomed crops): arm roots broad and blended, a mild crease where the arm's rear wall
  meets the belly (crop B); drumsticks rise broadly out of the rear flank (no knife at the thigh/body join), small
  folds behind the drumstick's rear (crop B, below the knife limit). Residuals: hind feet read as thin sticks with
  small toes; front legs thinner/more stilt-like than the sheet's; the body side is a long smooth plane (sheet has
  a hump behind the head); the drumstick has no visible thigh/shin fold line.

## Border pass (s4 r17-r18, 2026-10-21)
- Owner redline: cream belly / green thigh border underneath (bottom, -45 views) and the belly/forelimb border at the
  arm roots stair-step along the quad grid. Fix: new kit step `kit/smooth_borders.py` called right after `paint()` in
  stage 3: 2 despeckled faces, 10 anti-stair diagonal cuts at 3-to-1 colour corners (logged topo op, lock PASS),
  38 border verts relaxed tangentially on the original surface (Taubin, <= 0.5 edge, no face thinner than 0.8x;
  21 moves halved/undone by that guard). Stair corners 25 -> 3, 3-to-1 quads 16 -> 0. r17a without the width guard:
  upper-arm seam strip 1.16 r FAIL (a relaxed border vertex thinned a triangle at the arm root) -> guard added.
- Front legs toward the sheet (stage-2 vertex moves, no re-lock): arm rings scaled in their own planes
  1.08/1.12/1.24/1.36/1.36/1.12/1.08 (transition .. sole), +x 0-6 mm; upper arm 1.18 gave knife 1.28 r FAIL.
  Root band (transition ring + loft rim) relaxed 2 x 0.3. Including the first arm ring removed the knife entirely
  (max concave 87 deg) but left a 1.07-1.11 r seam strip FAIL, so it is excluded.
- r18 FINAL: all gates PASS (lock, IoU min 0.936, techqa slivers 1.5 %, z-fight 2 (limit 2, was 0), posed folds 0),
  junction probe PASS (upperarm knife 0.78 r / 146 deg, strip 0.86 r; thigh knife 0.47 r, strip 0.67 r), eyes PASS,
  separation PASS. Files: orbit18_sheet.jpg (before: orbit18_sheet_before.jpg), border_before_after.jpg,
  before_borders/ (old GLB, checks, frog.py).
- Residual: one rule corner left under the rump (the leg/belly rule's rear end turns 90 deg); front legs still
  slimmer than the sheet's; the root fold is unchanged in angle (only the rim is relaxed).
