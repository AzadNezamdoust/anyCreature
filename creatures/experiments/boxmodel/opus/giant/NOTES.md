# Mountain giant (opus) — round notes

Stage 0: blueprint.json drawn (hunched brute, 4.0 m, hump top 3.97, skull top 3.6, fist bottom 0.72 near knee 0.92).

## Stage 1

**r01** — first build: 8-sided trunk chain (5-vert half rings) R0..R5 + head H0..H2, face grid, nose from the grid's
centre column, hex legs from the pelvis underside, hex arms from the rib/shoulder side faces, a 12-ring fist box
with 4 extruded fingers + thumb, a forefoot box with 3 toes. Gates PASS, 906 tris, IoU side/front/top .90/.90/.85.
- Critique: worst = the upper body is an egg with a hood: the arms hang from mid-flank as thin tubes and the
  shoulders slope away (az000, hero). A brute needs square, massive shoulders wider than the gut.
- Diagnosis: R3/R4 side verts (x 1.06 / 0.92, z 3.30 / 3.55) are too low and narrow; deltoid/upper-arm sections
  (hd .36/.27) are thinner than the root they come from.
- Fix: raise and widen the shoulder (R3[2], R4[2]), thicken deltoid, upper arm and forearm sections.
- Result (r02): shoulders square and wider than the gut, arms read as limbs; first try folded the throat fan
  (6 hit pairs: R4-R5 trap face through the jaw) — fixed in the same round by pulling R4's side vert back and
  narrowing/pulling back R5 (the neck ring was as wide as the jaw). 906 tris, gates PASS.

**r02 → r03**
- Critique: head sunk between the shoulders (STYLE avoid list): from az000 the whole head sits inside the chest
  outline with the traps (z 3.88) above the skull (3.63); it reads as a helmet on a chest.
- Diagnosis: H rings and R5 too low relative to the trap ring R4[3].
- Fix: move the head block up/forward (HEAD_OFF +0.16 z, -0.08 y), neck ring R5 halfway, trap corner R4[3] down to 3.80.
- Result: skull now clears the trap line in front view; head readable as a separate mass. 906 tris.

**r03 → r04**
- Critique: side view (az090) the face is a duck bill: a long horizontal jaw ledge under a visor-like brow,
  no vertical face plane; front view the nose is a box on a flat plate.
- Diagnosis: face grid rows n/j (jaw ledge 0.15 m deep, near horizontal); a single brow row gives a ridge, not a bar.
- Fix: rebuild the face grid with a two-row brow bar (top edge + underside/nose root), a vertical chin plane
  (H2[0..1] forward), a thin underbite ledge, nose root under the brow, wider jaw corners.
- Result (r04): brow bar and chin plane read in close-ups; the head is still long in profile but no longer a bill.
  912 tris. (Added a debug close-up hook, GIANT_CLOSE=1, rendering head/fist frames to the scratch folder.)

**r04 → r05**
- Critique: the fists (the signature) read as open paws: four long fingers hang straight down from the knuckle
  row (az000, hero), no fist.
- Diagnosis: finger path in stage1: first segment goes down 0.13-0.24 before turning back.
- Fix: curl at the knuckle: path = knuckle turn (down 0.12) -> flat under the palm (back 0.17) -> tip up behind the palm.
- Result: fingers curl, the side shows a hook; but from the front it is a tall flat box with small teeth. 912 tris.

**r05 → r06**
- Critique: fist = "box with teeth": the back of the hand is 0.38 tall, the finger blocks thin (0.17) and short.
- Diagnosis: knuckle ring K at z 1.04; finger scales (0.74, 0.60).
- Fix: shorter hand block (K up to z 1.12), thicker/wider finger blocks, knuckle section pushed forward, chunkier thumb.
- Result (r06): stubbier fingers; better in 3/4 views, still a comb from az000. 912 tris.

**r06 → r07**
- Critique: at full-body scale the fists are SMALL (0.56 m, as wide as the forearm) — the signature is lost (az000, hero).
- Diagnosis: hand ring xs/yF/yB and finger paths are absolute sizes from r01.
- Fix: one fist scale FS = 1.38 on the hand rings, finger/thumb paths; wrist and forearm sections thickened to carry it.
- Result: fists now as big as the head and read from every view; bottom near knee height. 912 tris.

**r07 → r08**
- Critique: the legs read as thin columns under a 2 m torso (az000, az180): egg on posts.
- Diagnosis: leg sections hw .34/.27/.26/.25/.21 and stance x 0.47-0.52.
- Fix: thicken every leg section (~+18%), widen the stance by 0.04, feet follow.
- Result (r08): legs now carry the torso; stance planted. 912 tris.

**r08 → r09**
- Critique: hero/az090: the hump peak sits far behind the shoulders (y +0.32), so the R4->R5 back faces are
  0.8 m long thin slivers converging on the head — a hood/tube look on the biggest plane of the model.
- Diagnosis: R4[3..4] and R3[3..4] back verts.
- Fix: hump peak forward over the shoulder joint (R4[4] y 0.14, R4[3] y 0.16), R3 back verts follow.
- Result (r09): hump peak over the shoulders, back faces shorter; the fan remains but reads as trapezius planes. 912 tris.

**r09 → r10**
- Critique: az000 fist = a paw: the knuckle segment continues the back of the hand 0.18 m DOWN and the V gaps
  start at the knuckle line, so four fingers seem to hang.
- Diagnosis: finger path point 1 (down 0.13*FS) and width scale 0.78 on the knuckle section.
- Fix: knuckle section bulges forward and only 0.10 down, width 0.93 (a crease, not a gap); gaps open on the
  curled segments (0.78/0.72), where they show from below and behind.
- Result (r10): from az000 the fist is a back-of-hand plane over a row of four knuckle blocks with creases;
  daylight shows between the curled segments from below/behind. 912 tris.

**r11 (lock round)** — reads from every view as a hunched brute with huge fists; remaining issues are
vertex-level (boxy gut front, flat back-of-hand, face planes, eye sockets) and belong to stage 2. Locking.

## Stage 2 (lock edge hash 1c74ca80c63a5c8f…, 912 tris)

**s2 r01** — face.
- Critique (from the lock sheet): the face has no eyes and the brow is a thin shelf; the nose/jaw are flat plates.
- Diagnosis: no socket topology in the eye/cheek plane [H2[3], H2[2], n, e]; brow bar b/sb and H2[3] set back.
- Fix: `inset` eye socket (logged), the inner quad placed high under the brow and pushed 0.05 into the skull;
  brow bar and its temple end forward/down; broad nose bottom; upper lip back, lower jaw forward (underbite).
  First try: the jaw raised into the nose tip (6-8 hits) -> kept the jaw top 4 cm under the nose.
- Result: dark eye slits under a heavy brow read from az000 and hero; gates PASS, 928 tris, IoU min 0.99.

**s2 r02** — torso.
- Critique: hero/az000: chest and gut are one flat box front; the back is one smooth dome (no spine).
- Diagnosis: only rings R0/R1/R2 define the belly; back seam verts sit on the hull.
- Fix: a full loop in the R1-R2 band (the gut's upper curve), gut sags (R1 front down, R0 front forward),
  pecs forward, spine groove (back seam verts in), front corners pulled toward the keel.
- Result (s2 r02): gut rounds forward under the rib line, spine groove, pec shelf (first try folded the throat,
  2 hits; smaller R3 moves). 944 tris, IoU min 0.983.

(Orchestrator review after s2 r02: reads as a GORILLA — face buried in the shoulders and protruding like a muzzle;
the top view shows the shoulders as a flat disc.)

**s2 r03** — humanoid face.
- Critique: the face grid sticks 0.3 m out of the face ring like an ape muzzle; head low in the shoulders; top view
  shows a flat deltoid plate.
- Diagnosis: face grid/nose y spread; head verts; the deltoid ring's lateral vertex level with the shoulder root.
- Fix: compress the face toward a flatter plane (x0.62, nose x0.80 so it stays proud), lift the head 0.09 with a
  falloff into the neck; deltoid cap raised/rounded (R3[2] +0.09 z, lateral tip in and up).
- Result: flatter, humanoid profile (forehead-brow-nose-underbite), IoU min 0.965. 944 tris.

**s2 r04** — limbs.
- Critique: the back of the hand is a flat rectangle; knees and calves are straight.
- Fix: hand ring tapers to the wrist (x0.84), knuckle row arches forward/down; knee verts forward, calf back.
- Result: gates PASS, 944 tris, IoU min 0.958 (final stage 2, orbit run).

## Stage 3

**s3 r01** — paint (hide/jaw/brow+socket/fist) + pieces: eyes (gold 6-gon iris + pupil), tusks (4-sided horns
from the jaw ledge), toenails, moss slabs, rocks. 1272 tris, 8 colours.
- Critique: eyes are big round goggles (monkey read); moss = flat floating plates; rocks too small to register;
  still reads ape-like from the front (nothing humanoid).
- Fix: smaller eyes set back under the brow; moss slabs with a raised lumpy top; bigger, sunk rocks;
  a leather belt + front/back loincloth (the humanoid read), palette values lifted.
**s3 r02** — 1398 tris. Loincloth reads (giant/ogre, not ape). Critique: rocks vanish against the dark hide
(same value as the brow/feet stone colour). Fix (s3 r03): rocks get their own light rock grey; brow bar + socket
go near-black (frames the gold eye), feet take the darker jaw hide.
- Result (s3 r03): rocks read; but the near-black brow+socket band is a bandit mask across the face.
**s3 r04** — Fix: only the socket's back face is black; socket walls and brow bar take the darker jaw hide.
- Result (s3 r04): gold eyes in dark sockets under a darker brow, tusks, moss + light rocks on the hump and shoulders,
  leather belt/loincloth. 1398 tris total (body 944), 8 colours. Stage 3 final.

## Stage 4

**s4 r01** — rig from J (hips/spine/chest/neck/head, clav/arm/fore/hand, thigh/shin/foot, .L mirrored to .R),
automatic weights, eyes/pupils/tusks rigid to head, loincloth rigid to hips, moss/rocks/toenails borrow body weights.
Clips: idle 48f (breath: spine/chest back, clavicles up, head sway), move 32f (stride +-24, knees, arms in
opposition, chest roll, hip bob), attack 40f (arms -150 overhead with torso back, slam to -55 with torso/knees
forward, hips drop). Gates PASS, glbcheck OK.
- Critique of the posed renders: neck and elbows hold; overhead arms stretch the shoulder band (the arm root is
  one wide band) but do not collapse; walk opposition reads. Accepted; r02 = the orbit/final run.
- s4 r02 (final, orbit + glbcheck): all gates PASS; orbit advises head_hidden at az180/az225 (the hump hides the
  low-set head from behind — by design). `--compare` written: side_by_side.jpg.

## Triangles per stage
stage 1: 912 · stage 2: 944 · stage 3/4 total: 1398 (body 944 + pieces 454) · 8 colours.
Rounds: stage 1 = 11 (lock r11, edge sha256 1c74ca80c63a5c8f…), stage 2 = 4, stage 3 = 4, stage 4 = 2.
Kit/harness note: the harness orbit renders every view empty for stage-1 GLBs (all builders), fine from stage 3.

## Repair pass (art-director notes, review/ad_notes.md), rounds 60+

Stage 1 stays locked (no note required an unlock). Default bone rolls kept; weights and clip keys fixed instead.
`GIANT_QA=1` prints where every tech-QA flag sits (debug, on copies).

- **r60 — note 1 (blocker, shoulder fold-over).** Laplacian blend of all bone weights over the shoulder region
  (deltoid/trap/armpit, 4 passes), overhead raise capped -150 -> -125 (clav 12 -> 16), moss/rocks rigid to `chest`.
  Result: flip 36 -> 12 (0.86 %), 4 faces left at the front armpit. Sliver 55 (3.9 %), loincloth float 1: FAIL.
- **r61 — note 1 + note 2.** Blend 8 passes / wider region, raise -115, clav 20: flip 4 (0.22 %) PASS.
  Belt rebuilt on the body's own exported section (`body_section`): a closed 3 cm strap 1 cm off the skin;
  flaps rebuilt as solid tapered wedges (4.2 -> 2 cm, 6 rows) tucked into the belt, back flap 70 % wide on the
  buttocks. Float 0, zfight 0; belt slivers where section crossings bunched: 47 (2.6 %) FAIL.
- **r62 — note 2 fix + note 3 + note 6.** Belt crossings closer than 7 cm merged, long spans split (<=16 cm);
  flaps planar 4 mm off the skin. Moss rebuilt as 4 draped clumps (7-sided mound, base projected onto the body
  and sunk 4.5 cm, lumpy 3-peak top); rocks = 3 different stones (boulder, spire, slab) on the surface normal,
  sunk 30 %. All gates PASS (sliver 0.9 %, flip 0.21 %), 1880 tris. Clumps/rocks read too small.
- **r63 — note 4 + size.** Socket inner quad shrunk to ~1.2x the eye and pushed 3 cm deeper; socket back,
  pupil and mouth ledge in dark blue-grey #343b46 (was #121212); pupil r 0.024 -> 0.033 (thin amber ring);
  nose plane +3 cm; clumps/rocks x1.3. Hit 1: two rocks bedded in the hump clump. FAIL.
- **r64 — note 3/6 layout.** Each stone beds into exactly one clump. All gates PASS. Moss reads as mounds
  from az090/back34; eyes read as dark sockets under the brow with a dominant pupil.
- **r65/r66 — note 5 + note 8.** Hands repainted in the body blue-grey, knuckle fronts 'stone', finger-tip
  nails dark; finger sections re-placed (little 0.80, ring 0.98, middle 1.10, index 0.96 on top of the
  stage-1 curl). Thumb: first try (whole thumb across the front) self-intersected (2, then 10 hits);
  kept the stage-1 first section and swung the tip section rigidly forward-down in front of the index corner
  (no twist): 0 hits, IoU 0.945. Note 8: socket top dropped 4 cm so the brow's top wall is no longer an
  edge-on hairline (the (0.23,-1.36,3.56) sliver is gone). Knee loop limited to x < 0.95 (it had moved thumb verts).
- **r67 — note 7.** Stage 2: shoulder-blade corners out/back (R3[3], R2[3]), lumbar in (R1[3], R1[4]),
  trapezius corner up (R4[3]). Stage 4: idle pitches spine/chest +12 deg with neck/head -12 (gaze level),
  move +8 / -8. Explicit close-ups (head, fist, moss+rocks, belt+loincloth). All gates PASS: hit 0, float 0,
  zfight 0, sliver 15 (0.8 %), flip 4 (0.21 %); IoU min 0.936; 1888 tris (body 944 + pieces 944).
- **r68 — final** (orbit + glbcheck): every gate PASS, glbcheck OK; orbit advises head_hidden at az180/az225
  (by design). `--review` and `--compare` rebuilt. Honest read of the beauty sheet: with the hands in the body
  blue-grey the fist no longer separates from the forearm, and from az000 the pale knuckle strip over the
  finger fronts still reads as hanging fingers (note 5 partly); the thumb only swings forward, not across.
Triangles after repair: body 944 + pieces 944 = 1888. Rounds: 60-68 (9, plus 2 stage-2 hit diagnostics).

## Repair pass K=2 (review/ad_notes_r2.md), rounds 90+

- **r90 — baseline** on the current kit: drift FAIL (10 shells: moss, rocks, belt, loincloth, all rigid to
  chest/hips); flip 4 = 0.21 % of tris but 0.49 % of area (two 0.12 m² chest triangles). Item 0 = item 1.
- **r91 — item 1 (drift).** Critique: every shoulder/waist piece leaves its seat in poses (3_tech blue).
  Diagnosis: bone=chest / bone=hips binds while the skin under them follows clav/arm/thigh. Fix: bind(body=).
  Result: moss/rocks pass; loincloth drift 1 and 17 flips (the flap corners take thigh weights and shear).
- **r92 — item 1.** Diagnosis (GIANT_DRIFT per-vertex seat gaps): DATA_TRANSFER interpolates over the body's
  quads, the gate measures on the exported convex triangulation, so big hip quads give a different blend.
  Fix: `seat_weights()` = barycentric skin weights of the nearest point on the exported triangulation
  (moss, rocks, belt, flap tops); flap rows below the belt take one averaged weight set per row
  (`even_weights`, no shear across a flap). Result: drift 0, loincloth flips 0. 1888 tris.
- **r93–r101 — item 2 (shoulder fold-over), diagnostics.** GIANT_FLIPF (techqa's fold test per frame) shows
  ONE triangle per side, (R2[1], deltoid front-low, deltoid front-top), flipping in frames 7–21 of the raise.
  Tried: a logged stage-2 deltoid loop (r93/95/97: flips moved to the back armpit, 0.6–1.15 % area: reverted),
  blend radius 1.0 (no change), clav ±Z (no change), a 6.5 cm front-deltoid bulge to turn the split diagonal
  (the other half flipped instead), deltoid-cap weights to clav (no change alone). Sweep of the raise: the fold
  is geometric (the deltoid front face rotates past the chest corner) and clears at arm -85, returns at -95.
- **r102 — item 2 fix.** Kept the deltoid bulge (stage 2, one vertex/side, IoU min 0.936) and the cap weights
  (verts above the joint keep 30 % arm, rest to clav); raise capped -115 -> -85 (fore -35, torso lean kept, so
  the fists still come up to head height); slam arm -55 -> -40 (a 0.026 m² armpit triangle flipped in the slam).
  Result: all gates PASS, flip 0 (0.00 % tris, 0.00 % area), drift 0; 3_tech has no purple and no blue. 1888 tris.
- **r103–r105 — item 3 (mitt fists).** Critique: fist close-up = a smooth dome over a uniform tan band; az000 a
  comb of equal blocks. Diagnosis: the knuckle sections are the full width of the finger roots; paint key 'stone'
  on every front knuckle face. Fix: stage 2 knuckle sections 18 % narrower (grooves between them), front verts
  3.5–4.5 cm proud and tipped up, per-finger prominence (middle 1.3, little 0.7) and drop (middle lowest);
  finger-root verts between the knuckles sunk 1.5 cm; stage 3 tan knuckle band removed (hands all blue-grey,
  nails dark). Result: four separate knuckle bumps with grooves, uneven row; IoU min 0.935; gates PASS.
- **r106–r108 — item 4 (flap planks).** Fix: each flap row is placed by ray casts on the body (row plane on
  the most outward skin point, receding at most 4 cm per row, edge columns curl <= 1.5 cm toward the skin),
  thickness 4.0 -> 1.6 cm toward the hem. r106: the front flap cut the crotch (hit 1) -> ignore skin > 15 cm
  behind the previous row; r107 dropping the per-row weight averaging brought back drift/flips -> restored.
  Result r108: flaps follow belly/thighs and buttocks in az090, no daylight; all gates PASS.
- **r109–r110 — item 5 (slivers).** Brow shelf already clear (r66). Jaw-chest seam: dropping the pec-shelf
  row (R3[0]/R3[1]) 5 cm re-created a pec fold-over (0.61 % area); 2 cm left the slivers. Reverted: not done.
  Finger-gap strokes not attempted (turn budget).
- **r111 — final** (orbit + glbcheck): every gate PASS (hit 0, float 0, zfight 0, sliver 17 = 0.9 %,
  flip 0 = 0 % tris / 0 % area, drift 0); IoU min 0.936; glbcheck OK; orbit advises head_hidden az180/az225
  (by design). `--review` and `--compare` rebuilt. 1888 tris (body 944 + pieces 944). Rounds 90–111.

## Repair pass K=3 (review/ad_notes_r3.md), rounds 130+

Stage-1 unlock (owner-authorised: hands, brow/jaw-chest topology, back). The old lock is kept as
`stage1_lock.pre_unlock.json`; relocked at r134 (edge sha256 006673f7…, 1144 tris, was 912).
- **r130 — baseline**: every gate PASS (sliver 17 = 0.9 %; body 13: jaw-chest 4, knee 4, fingers/wrist 5).
- **r131–r134 — item 1 (mitt fists), stage 1.** Critique: fist = smooth dome + comb of four equal finger tabs
  on one shared root (V slits). Diagnosis: the finger roots shared edges on the palm bottom; stage-2 knuckle
  nudges could not open real gaps. Fix (`build_fist`): wrist -> back-of-hand ring W -> knuckle-ridge ring M
  (sunk 1.5 cm behind the bumps) -> palm bottom with separate 6-vert finger roots (4 cm gaps, front 62 % of
  the palm; a palm-heel strip behind), fingers swept knuckle -> first phalanx -> tip, front corners chamfered
  3.5 cm (V grooves), knuckle front 3.5–5 cm proud, knuckle drop -4.5/0/+3.5/+1.2 cm, lengths 0.76/1.0/1.13/0.97
  (little/ring/middle/index), tips curled 40/58/62/58 deg (was 45; capped clear of the palm heel), explicit
  wrist fans (no n-gon fans), thumb tip swing baked in. Stage-2 finger code removed. r131/r133 self-hits
  (little/middle tips into their own knuckle / the heel) fixed by the curl cap. Result: stepped knuckle row,
  staggered fingers, 0 hand slivers.
- **r136–r144 — item 2 (flaps), checked in the idle `--review`.** Each flap: 4 columns x 4 segments, every
  vertex 6 mm off the skin it covers (ray cast), top row tucked under the belt; front follows the belly and
  slants toward the thighs (<= 7 cm back a row), back hangs from the buttocks (<= 3 cm a row); hem 15 % wider,
  corners lifted/pulled in; 3.6 -> 3.0 cm thick. Weights: seat weights, rows below 1.40 blended 50 % with their
  row average (r136 pure seat weights: 13 flap flips in the walk). Old flaps drifted in `move` on the new kit
  (r135). r141–r144: side-wall/hem needles removed (extra row, per-row recession limit, thicker hem).
  Result: az090/back34 show no stick and no daylight over the top half; flip 0, drift 0.
- **r140 — item 3 (nails).** Black painted finger tips removed; `nails` piece = one wedge per toe and finger,
  1/3 digit wide, back sunk 1 cm, front 1.2 cm proud, 'jaw' blue-grey with only the front face 'black';
  seat-weighted. zfight 0.
- **r140 — item 4 (slivers).** Brow: the bar's underside (e/se) came 10 cm forward in stage 2, so the brow front
  faces forward (the black line was a down-facing strip). Jaw-chest: stage-2 moves, R4[1] +9 cm up onto the
  neck, R4[0]/R5[0] 5 cm forward, so the seam row no longer sits on the pec-shelf line. Body sliver 13 -> 4
  (the 4 left are behind the knees). No pec or shoulder fold-over (flip 0).
- **r145–r146 — should-fix rocks.** Scales ~1.0/0.7/0.5-0.6 (the back spire is no longer a horn). A reversed tilt
  on the back rock drifted in `attack` (r145); the old tilt kept (r146), drift 0. Pupil 8-sided at 66 % (ring 1/6).
- Not done: back blades/spine groove (turn budget), belt end (O7), the 4 belt-top slivers (loincloth 4).
- **r147 — final** (orbit + glbcheck): every gate PASS (hit 0, float 0, zfight 0, sliver 8 = 0.4 %, flip 0 %
  tris / 0 % area, drift 0); IoU min 0.948; glbcheck OK; orbit advises head_hidden az180/az225 (by design).
  `--review` and `--compare` rebuilt. Triangles: stage 1 1144, total 2112. Rounds 130–147.
