# troll (t7 hand box-model, hunched biped) - NOTES

Workflow v2 (zoo/WORKFLOW.md) on the BRIEF base. Concept sheet refs/gpt/v3/troll/sheet_1.png, traced with kit/refs.py
(height 2.2 m). The sheet's plan view is not a true ortho (top length 1.57x the side), so blueprint.json's top outline
was removed (the ogre did the same); side marks eye / nose / chin added by hand.

**Identity cue (troll, not ogre):** the hunch - the head hangs forward and low in front of a trapezius hump nearly as
high as the crown; a huge drooping potato nose; very long arms that hang forward with the hands below the knees;
short bowed legs on big flat feet; a bald dome and pointed leaf ears; no tusks, no strap (the ogre is upright with
tusks, a belly patch and a chest strap).

Build: one spine loft of 14-vertex half rings, crotch -> crown. Torso rings flat; from the shoulder line up the rings
tilt (back seam on the hump, front seam on the throat / face), so the loft bends forward over the hump into the low
head. Legs: 2-span x 5-face roots (crotch -> hip underside -> hip side; 14-vertex rings). Arms: 3-span x 4-face roots
(chest -> shoulder line -> chest top -> trapezius; 14-vertex rings). Each limb starts with a hug ring (the root loop
pushed out along the region normal and shrunk) - the broad transition ring. Ears: 2-face leaf extrusions. Nose:
a 2-face seam-column extrusion (seam walls removed).

## Stage 1
- r1: first fit. FAIL self-intersection 22 pairs at the crotch. 2220 tris, IoU side/front 0.863/0.789.
  Critique: the leg tubes butt into the hip underside; the shoulder is a T-pose shelf. Diagnosis: the first leg ring
  (rx 0.19, ry 0.24) is much bigger than its 5-face root, so its walls fold into the crotch faces.
- r2: Fix: leg root made 2 spans tall (crotch -> hip underside -> hip side) + a hug ring + the thigh rings started
  under it; crotch ring lowered/narrowed (R0 W 0.09), R1 made the groin crease. Nose sections redrawn from top/bottom
  profile points (its first section had cut the lip). Result: PASS, 0 intersections, 2244 tris, IoU 0.871/0.799.
- r3: Critique: az000 the shoulder is a flat shelf (the arm leaves the chest horizontally). Fix: arm root 3 spans tall
  (chest -> trapezius) with a hug ring, deltoid ring outer side high. Result: PASS, shoulder slopes, IoU 0.871/0.804.
- r4: Critique: az090 the arm hangs straight down behind the belly; the sheet's arm hangs forward (deltoid y 0.24,
  elbow 0.06, wrist -0.05). Fix: arm centres moved forward, rings set perpendicular to the arm path (ty), the deltoid
  cap ring kept level. Result: PASS, side IoU 0.876, arm reads forward like the sheet.
- r5: Critique: head (zoom crops): a box with a small nose and a flat lid; face features too low vs the sheet
  (eye z 1.99, brow 2.04, chin 1.62). Fix: head rings re-read from the side/front crops (front seam chin -> crown, back
  seam on the skull), bigger potato nose (bulb half width 0.10), wider leaf ears. Result: PASS, 2320 tris.
- r6: Critique: the nose read as a trunk from the brow; ear a spike; the crown a flat lid; jaw as wide as the
  cranium. Fix: nose bridge narrow at the top (0.45 rx), ear a 4-ring leaf, crown cap poked into a low dome, jaw rings
  narrower (H0u 0.195, H0 0.185). Result: PASS, 2348 tris, IoU 0.874/0.806.
- r7: Critique: torso a box in az000/az180 (flat front, straight sides). Diagnosis: BODY profile e 0.8 = a
  super-ellipse box. Fix: BODY e 1.0, HIP 0.9, TRAP 0.95, a slight waist (R5 0.42). Result: PASS, rounder.
- r8-r9: Fix: leg first ring moved out (x 0.305) so the crotch has no notch; forearm swell up (rx 0.15) - the
  sheet's forearms are massive. Result: PASS, 2304 tris.
- r10: Tried a hug ring (root loop pushed out along the region normal): it made a 90 deg collar step round each
  root (shoulder A crop: knife fold; hip B: a lip). Removed: the limbs leave the root region directly. Hip crops clean.
- r11: Critique: shoulder crops: the deltoid a box with sharp corners. Fix: arm rings with rounder corners (apos,
  corner 0.78). Result: shoulder front crop blends; small concave notch at the deltoid front remains.
- r12 LOCK: 1120 verts, 2236 tris, edge sha256 778c201d86a6f16b, IoU side/front 0.874/0.807 (moved to lock_r12/).
- r13 RE-LOCK (after s3 r3 showed horizontal rib bands on the belly): torso stations smoothed (front y, back y and W
  of R3..C1 now a smooth convex run, no alternating ring widths). 2236 tris, edge sha256 5b7fc0922e7ec3d8,
  IoU 0.873/0.806. Belly bands gone in s3 r4.

Biped checklist at lock: chin/jaw - H0u jaw-line ring under the jaw, its front 9 cm ahead of the throat (N0), the
jaw underside reads from az090 (throat/chin crop: a clear step) - OK. Shoulders - trapezius steps down from the
hump to the deltoid cap; the arm root takes 3 spans x 4 faces of the chest side, the deltoid ring wider than the
upper arm - OK. Arms hang forward/out (A-pose), forearm 20+ cm clear of the torso - OK. Legs short, knees under
the hips, groin without slit - OK. Hands: parts-library hand_three_finger(fingers=4) at stage 3.

## Stage 2
- r1: elbow and knee loops, eye socket (inset 0.30 in the H3-H4 column-2 face, floor 14 mm in), brow ridge 16 mm
  forward. PASS, 2364 tris, min IoU vs s1 0.997.

## Stage 3
- r1: palette (8): olive skin, tan chest-belly, pink nose, leather, rope, nail, eye, pupil. Pieces: lens eyes, two
  parts-library 4-finger hands bridged to the wrist rings, 5 toes per foot with nails, a rope belt band, front and
  back loincloth flaps (18 mm slabs). FAIL: hit 1 (belt sunk on both edges: crosses the skin twice), zfight 12.
- r2: belt lower edge sunk, upper edge proud; flap tops moved under the belt (they crossed it); toe soles lifted
  6 mm off the foot sole (z-fight). PASS, 3676 tris, 8 colours. Critique: belly patch stripes, saturated green.
- r3: palette greyer (sheet's grey-olive), belly patch by front columns. Bands remained: they were shading bands
  from uneven torso rings (fixed by the r13 re-lock).
- r4: after the re-lock: PASS, belly patch one clean panel.
- r5 (re-run after the r13 re-lock, see below): PASS.

## Stage 1 re-locks driven by the stage-4 junction probe (logged; over the 14-round budget)
- r14: ear tip moved out (0.35, -0.13, 2.09). r15: determinism fix - the ear root centre summed a Python set (the
  vertex order changed c0 in the last bits, so the lock hash flipped run to run); the root verts are now sorted.
- r16-r36: the ear root (probe: knife 4.8 r at 150 deg, then seam strips). Steps that held: ear root moved up the
  skull (J ear z 2.04) where the 2 root faces sit flatter; the leaf leaves the skull along the root's own normal on a
  bezier to the tip (the straight root->tip axis overhung the skull: the 150 deg fold); a hug ring (root loop
  pushed out 4.5 cm, drawn in to 0.74) as a short cone base; leaf rings keep the root loop's own layout
  (root_roles; even-angle roles sheared the quads into thin triangles) with the rim held at >= 0.85 of the
  thickness; the ear axis turned to 28 deg off the root normal; first leaf ring at t 0.38 (wide 64, thin 30 mm).
  Tried and dropped: an S2 stalk shrink (concave waist), flattening the skull round the ear (made a fin), a
  mid ring (rings too close: thin faces), a ring at t 0.32 + 0.6 (knife back). Final lock r36:
  1120 verts, 2236 tris, IoU side/front 0.873/0.804.

## Stage 4
- r1: rig 12 bones + .R (roll auto), ear.L bone on the head; clips idle 48, move 33 (heavy walk, long arm swing),
  attack 32 (right-arm clubbing swipe). Kit gates PASS. Junction probe FAIL: ears (knife 4.8 r), eye side 0.28;
  arms PASS (knife 0.44 r), thighs PASS.
- r2-r24: ear root work (above) and eye: lens normal turned out (n + 1.1 x), lens r 26 mm; side view 0.28 -> 0.43.
- r25: all gates + junction probe PASS (ear strip 0.99 r, knife 0).

## Owner-style review (orbit18, junction crops, close-ups)
Flaws seen: (1) the shoulders read as a flat T-bar from +45 az180 / top (deltoid shelf with a vertical outer
wall); (2) the eye a dark rectangular slot (deep 14 mm socket + 16 mm brow), lens barely visible in close-up 0;
(3) a sawtooth of folded triangles on the deltoid front (close-up 1); (4) the chest-belly panel too bright, reads
as a vest.
- fix 1 (S2): the deltoid cap ring's outer half dropped 8 cm and drawn in 2.5 cm, upper-arm ring 2.5 cm. Gates PASS;
  the corner is lower but the +45 rear view still shows a shelf (residual).
- fix 2 (S2/S3): socket 6 mm deep (inset 0.22), brow 10 mm, lens seated 6 mm out. Eye 0.51/0.83/0.62, a clear round
  lens with a pupil in all three crops. Belly colour toned to #b9b493.
- fix 3 (S2): planarize the shoulder faces - made a 1.71 r seam strip (probe FAIL); reverted (residual sawtooth).
- Final s4 r30: all kit gates PASS, glbcheck OK, junction probe PASS (ears knife 0 / strip 0.99 r, arms knife
  0.44 r, thighs knife 0), eyes PASS, membranes PASS (flaps p10 12.9/14.1 mm, ears 27.9 mm), separation PASS
  (arm-torso 13.4 cm, leg L-R 25 cm). Warnings: belt seat 75% lifted (warn-only, uncalibrated), posed clip 0.03%.
  3676 tris (body 2364), 8 colours. checks/ holds the 18-view renders; orbit18_sheet.jpg, side_by_side.jpg
  (sheet vs model), compare_engine_s1_final.jpg (run.py --compare), review/ (run.py --review).
- Residual: shoulder shelf from above/behind and a deltoid-front sawtooth; the torso still reads as a barrel
  (straight sides); the nose is a boxy wedge, not a round bulb; ear root strip at the gate's edge (0.99 r).

## Repair pass (2026-10-18): shoulder T-bar shelf -> minotaur shoulder (S1 re-locked r37-r41, logged)
Owner flaw (orbit18 top / +45 az180 / az45): the shoulders a flat horizontal T-bar shelf out of the torso side, a
sawtooth of folded faces on the deltoid front. Diagnosis: the arm root was 3 spans x 4 faces from C0 up to T1
(the trapezius), so the arm's outer side WAS the shoulder top, levelled out to x 0.80 over a torso 0.55 wide.
Old lock moved to old_locks/lock_r36; old sheet kept as orbit18_sheet_before.jpg.
- r37 Fix (minotaur method): the deltoid is the torso's own widest ring: C0/C1/C2 W 0.53/0.62/0.66, C2 profile
  BODY (was TRAP 0.52); the arm grows from a 2 x 3 region right under it (C0 -> C1 -> C2, columns 5-7, top edge on
  C2), roles on the unit circle (phase-fitted), first ring = the root loop pushed out unshrunk (k 1.0), then
  frame_chain rings (ARM_C/ARM_R). The S2 cap-ring drop (old review fix 1) removed; elbow loop by limb_edge.
  Result: PASS, 2164 tris, IoU 0.875/0.822. Critique: the side T-bar is gone but the C2 ring now juts past a narrow
  T1 (0.49): a 28 deg plate on the shoulder top (top view: a flat disc).
- r38 Fix: the trapezius as a rounded mass: T1 W 0.58 with a side-widest profile TRAP2 (0.9, -0.10, 0.12), T2 0.45,
  N0 0.31, C2 0.645. Result: PASS, IoU 0.875/0.828; orbit (scratch) +45 az180 and top: round shoulders sloping from
  the neck into the arms, no shelf.
- r39 lock, then r40 RE-LOCK (density): the 10-vertex arm rings cost 72 tris against the old 14-vertex arm, so two
  straight in-between (lerp) arm rings: upper arm -> elbow and the wrist taper. 2244 tris (old lock 2236).
- s2 r06 / s3 r06 PASS (2356 / 3652 tris, 8 colours). s4 r31: kit gates PASS, junction probe FAIL upperarm.L/R
  seam strip 1.25 r / 20 mm: the hug band (root loop out 2.5 cm) is a thin crease band round the arm root
  (flag tile: yellow along the shoulder top). Ears, thighs, eyes PASS.
- r41 RE-LOCK Fix: hug ring out 4.5 cm along the region normal (the normal points out-and-down, so the band carries
  the trapezius slope down onto the deltoid instead of stepping). LOCK r41: 1124 verts, 2244 tris, edge sha256
  811bab8ca67a1bae, IoU 0.875/0.828.
- s4 r32 Result: ALL kit gates PASS (glbcheck OK, tech QA; warn posed clip 0.03%, belt seat 75% warn-only), junction
  probe PASS: upperarm knife 0 (max fold 85.9 deg) strip 0.91 r; ears knife 0 / strip 0.99 r; thighs strip 0.38 r;
  eyes 0.46/0.74/0.56; membranes PASS; separation PASS (arm-torso 12.4 cm, legs 27.6 cm). Total 3652 tris
  (S2 body 2356, was 2364 / 3676: the 10-vertex elbow loop and wrist ring; S1 base denser than before).
- Crops (own look, orbit18 top / +45 az180 / az45 / shoulder close-up): the T-bar shelf and its vertical outer wall
  are gone; the shoulder is one round mass from the neck over the deltoid into the arm; no sawtooth on the deltoid
  front. Residual: a dark concave wedge at the front armpit (arm front wall meets the pec, probe 0 knife); a soft
  horizontal clavicle crease from the throat to the shoulder (az45); the top view reads as a round disc (wide yoke);
  the hand cuff sits inside the wrist ring with a dark lip (close-up 2).
- Biped checklist (shoulders, S4): trapezius slopes down neck -> deltoid as a round mass yes; deltoid = the torso's
  widest ring, arm root 2x3 faces with its top edge on it yes; shoulder reads connected from hero/az000 yes. Hunch,
  nose, ears, eye and palette unchanged (head rings, N0 back seam and stage 3 untouched; N0 width 0.27 -> 0.31).

## Detail pass (2026-10-23 night, tier 3: 8 -> 12+ groups; backup before_detail/)
- r33 (S4): seated chunky pieces (detail_pieces.py): brow, nostril (dark cap), kneecap, wart x3, navel, pec fold,
  mouth line; big toe fatter. Colours stay 8. Kit gates OK, junctions PASS, detail count 15 PASS, but detail FAIL:
  toes_L/R big toe 'stick' L/t 6.7 (len 181 mm: it overlaps toe 2 and reads as one long branch).
  Critique (az000/hero): the pec fold reads as a curved strap/necklace across the chest.
- r34 Fix: pec fold dropped (strap look); big toe moved clear of toe 2 (x -0.136, w 42 mm, L 66 mm, h 88 mm).
