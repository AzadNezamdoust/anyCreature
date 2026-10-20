# yeti (t7 hand box-model, shaggy upright biped) - NOTES

Workflow v2 (zoo/WORKFLOW.md) on the BRIEF base. Concept sheet refs/gpt/v3/yeti/sheet_1.png, traced with kit/refs.py
(height 2.4 m) at --thresh 20: the default 40 lost the white fur on the white ground (the side trace zig-zagged
through the body). Hand edits to blueprint.json: the ground-shadow points (side y +-0.67, front x 0.91 at z 0.03)
removed; the top outline removed (the plan view is not a true ortho: 1.34x the side length, as troll/ogre); marks
(eye, nose, chin, shoulder, wrist, knee, hip) added from metric-grid crops of side.png / front.png.

**Identity cue (yeti, not gorilla / troll):** white shaggy fur over everything; a hooded head sunk forward in a fur
mantle that slopes from the crown peak straight down to the shoulders; a barrel torso as deep as it is wide; massive
arms that WIDEN downward into fur cuffs over big grey hands; grey face mask, hands and big flat feet; upright stance.

Build: one spine loft of 13-vertex half rings (werewolf ring13: 5 control points per ring), crotch -> crown; the
head rings run back into the hump (head, hood and mantle one mass). Arms: minotaur trick (2 x 3 region C1 -> C1~ ->
C2, top edge = the widest ring C2, root loop pushed out unshrunk). Legs: 3 x 6 region L0 -> L1 through a 45 %
transition ring, level rings to a flat foot. Hands: parts-library hand_three_finger(fingers=4) welded at the lock.
Fur: loft steps (forearm cuff over the hand, shin skirt over the foot) + big S3 clumps.

## Stage 1
- r1: first loft. FAIL self-intersection 4 pairs at the wrist (0.88, -0.05, 0.82). 2328 tris, IoU side/front
  0.884/0.810. Critique: hands tiny vs the sheet's huge grey hands; the hand root fights the cuff step.
  Diagnosis: round 0.12 m wrist ring bridged to a flat 0.20 x 0.17 hand root right under the 0.24 m cuff.
- r2: Fix: flat wrist ring (0.09 x 0.13) + a bigger hand (width 0.30). Result: 6 pairs, still FAIL.
- r3: Fix: hand back faces +x (width along y). Result: 14 pairs: the weld's bridge twists the palm into the cuff.
- r4: Fix: no S1 weld; the hand becomes an S3 piece rooted in the wrist ring under the fur cuff (troll method; a
  hand emerging from a fur cuff is the sheet's read anyway). Result: PASS, 1976 tris, IoU 0.838/0.770 (no hands).
  Critique (az000 vs sheet front): the head is a narrow peaked trapezoid on a box; the sheet's hair hood slopes
  from (0.34, 2.11) to (0.68, 1.88) into the shoulders.
- r5: Fix: the hood/mantle widths read off the front outline: C2 0.73, C3 0.70, T0 0.66, J0 0.56, M0 0.44, N1 0.35.
  Result: PASS, IoU 0.838/0.790; az000 now has the sloping hood-to-shoulder mantle. Critique: the face is not a
  face: the front corner runs in one curve back to the hood side, so face and hood are one slab (hero, az000).
- r6: Fix: ring13 takes hand-placed vertices (werewolf muzzle trick): on M0/N1/E0/F0 vertex 4 runs the face side
  straight back (x 0.17-0.19, y -0.33..-0.38) and vertex 5 is the hood rim (x 0.24-0.30, y -0.25..-0.27): a face
  box set inside the hair hood.
  Result: PASS, 1976 tris; hero/az000: a face block now stands in the hood. Critique: the torso is a crate (az000:
  flat front plane 0.62 W wide, straight sides; az090: a straight back where the sheet hollows at z 1.3).
- r7: Fix: torso5 rounder (front corner 0.52 W at 13 % depth, back corner 0.70 W), lower-back hollow B1/B2 back
  0.44/0.45 (sheet side outline 0.42-0.45 at z 1.29-1.37).
  Result: FAIL self-intersection 22 pairs: forearm cuff inner-front (0.71, -0.23, 0.94) and upper-arm inner side
  vs chest (0.60, -0.06, 1.29) (the rounder torso and the re-phased root roles exposed both).
- r8: Fix (the intersection gate): the cuff and wrist rings LEVEL (frame_chain tilted the 0.24 m cuff 28 deg with
  the forearm: its front fell 11 cm, under the wrist ring); upper arm 2-3 cm out (x 0.72/0.755/0.775).
  Result: still 22 pairs. A vertex dump showed the culprit: the FOREARM ring (z 1.04) tilted 27 deg by frame_chain
  (its neighbours elbow -> cuff), its front at z 0.94, under the level cuff (0.95): the cuff's front faces fold.
- r9: Fix: forearm, cuff and wrist rings all level (a fur cuff hangs level).
  Result: still 20 pairs. Role dump of the arm region: the angle sort put the C1 side vertex (x 0.63, bulging out
  along the region's e1) between the front corner and the front-mid: the role order crossed = a twisted arm.
- r10: Fix: region_roles walks the region rim topologically (angle phase fit kept), so roles always follow the rim.
  Result: PASS, 0 intersections, 1976 tris, IoU 0.842/0.776. Critique (az000): a dark flat shelf under the belly
  (L0b front -0.26 -> L0 front -0.12 is a near-horizontal underside); the sheet's belly drops in a V to the crotch.
- r11: Fix: crotch front forward and lower (L0 z 0.72, front -0.20; L0b front -0.29): the underside turns to face
  forward-down.
  Result: PASS, IoU 0.846/0.777; the belly shelf is gone (az000). Critique: blueprint front overlay: the legs sit
  well inside the sheet outline (sheet leg x 0.08-0.51 at z 0.6; model 0.09-0.49 thin column).
- r12: Fix: legs wider and deeper (thigh 0.225 x 0.26, knee 0.20 x 0.245, skirt 0.225 x 0.28), 1 cm out.
  Result: PASS, 1976 tris, IoU 0.848/0.793. Orbit (r11 orbit_sheet) top / az135 / az225: the mantle slopes round
  from the hood into the arms, no flat shoulder shelf; soles read as big flat ellipses from below.
- r13 LOCK (no change).
  Biped checklist at lock: chin/jaw - J0 (z 1.95) is the jaw-line ring, its front 12 cm ahead of the throat (T0 front
  -0.35), the jaw underside a visible plane from az090 (the beard piece hangs from the chin front in S3) - OK.
  Shoulders - the mantle steps down from the hood (J0 0.56) over C3 0.70 to the deltoid line C2 0.73 (the widest
  ring); the arm root is 2 x 3 faces with its top edge on C2, first ring unshrunk, 4 cm out - OK; reads connected
  in az000/hero. Arms hang forward and out (A-pose), forearm 10+ cm clear of the torso - OK. Legs: straight
  columns, a groin cap between them with no slit - OK. Hands: parts-library hand_three_finger(fingers=4) in S3.
- LOCK r13: 990 verts, 1976 tris, edge sha256 4026fa21b68dbb0e, IoU side/front 0.848/0.793.

## Stage 2
- r1: elbow + knee loops, eye socket (inset 0.25 in the E0-F0 column-1 face, floor 5 mm in), brow ridge F0 cols
  1-3 12 mm forward. PASS, min IoU vs s1 1.0, slivers 0.2 %. Critique (az000): a dark notch in the brow at the seam
  (the seam vertex not moved with the brow).
- r2: Fix: the brow move takes the seam vertex too.
- s2 r2 Result: PASS, no brow notch.

## Stage 3
- r1: palette (6): fur, shade (lock tips), grey skin (face mask, hands, feet), nail, eye, ear inner. Pieces: lens
  eyes, parts-library 4-finger hands bridged to the wrist, 5 toes per foot, round ear cups, 9 fur clumps + beard.
  FAIL hit 4 (fur clumps on the shoulder cap, chest, mid back). 4128 tris. Critique (hero/az000): a dark strap runs
  from hand to hand across the groin. Diagnosis: wrist_ring() looked for an n-gon >= 8 verts near the wrist, but
  the arm end is the root region carried down (6 faces): it found the crotch cap and bridged both hands to it.
- r2: Fix: wrist_ring() walks the rim of the arm's end faces (10-vertex ordered loop).
  Result: the hands hang from the cuffs, no strap. Still FAIL hit 4. Critique (hero/az090 colour): the 5-lock 0.2 m
  clumps read as scattered small spikes (noise), not shaggy fur.
- r3: Fix: fur as BIG shingles: 3 locks per clump, 0.26-0.42 m long, 0.26-0.44 m wide, wrap radius = the local body
  radius (0.26 arm/thigh .. 0.6 back/chest); beard 3 locks 0.28 m.
  Result: FAIL hit 3 (chest, mid back). Critique (hero/az090): fur_clump locks have a ridge section and a point: at
  any size they read as crystal spikes on a smooth body, not shag.
- r4: Fix: fur_clump dropped (tried n 5 -> n 3 big; the part's look, not its size, fails). Fur = 7 jagged fur
  TIERS (hand-built: no library part makes a skirt of locks): shoulder mantle (back + sides), hood, beard, hip skirt,
  upper-arm and elbow skirts, thigh skirt; each a closed band, top edge sunk 1.2 cm, hanging straight to a zig-zag
  hem (alternate tips 6-8 cm). Fur colour brighter (#e6e3dc, hem underside #c4bfb4).
  Result: FAIL hit 2 (mantle, hood) + z-fight 6 (mantle). The tiers read as the sheet's shag (az000/hero/az180).
  Diagnosis: the section's inner mid vertex sat rmax + 0.55 flare - 2.8 cm thick: on the hood (flare 3.5 cm) 0.9 cm
  INSIDE the skin (a second crossing), on the mantle 0.5 cm off it, face to face (z-fight).
- r5: Fix: the mid row stands at least thickness + 1.2 cm off the skin, the hem thickness + 1.5 cm.
  Result: still hit 2 / z-fight 4. Tech heatmap (hero, back34): the hood and the mantle stand off the sloping skin as
  big cone lids (every row hung at the max radius of the whole run), the mantle teeth bite the deltoid.
- r6: Fix: each tier row follows the skin above it (max radius from the top down to that row only); the hem's max
  includes its tooth tips.
  Result: hits 0; the hood and mantle hug the head and shoulders (hero/az090), shaggy and jagged. FAIL z-fight 8
  (mantle hem on the back hump, back34 tech: green). Diagnosis: one mid row at 0.45 L: the outer face from it to the
  hem skims the hump bulging out below it.
- r7: Fix: a third tier row at 0.75 L (follows the skin to 0.8 L); sections 7 vertices.
  Result: z-fight 14, all on the mantle's ROOT faces at the back (back34 tech: green just under the hood): the face
  from the sunk top edge to the first row runs almost tangent to the hump.
- r8: Fix: top edge sunk 2.5 cm (was 1.2), first row 1.5 cm further out: the root face crosses the skin steeply.
  Result: z-fight 6 (same faces).
- r9: Fix: top edge sunk 4 cm, first row +2.5 cm. Result: PASS (hit 0, float 0, z-fight 0), 5190 tris, 6 colours.
  Critique (az090 colour): the hands are flat paddles with straight fingers; the sheet's hands hang heavy and curled.
- r10: Fix: hand curl 0.38 -> 0.62, thumb curl 0.45, fingers 0.62 x width.
  Result: PASS. Critique (s3 r10 sheet, az000/az180): the tiers now read as stacked belts/rings (the 4 cm sink +
  2.5 cm lifted first row = a ledge on every tier; teeth 6 cm on 0.2 m bands are too small).
- r11: Fix: deep sink + lift on the mantle only; teeth 7-10 cm with notches 30 % up, tips splayed 3 cm, fewer teeth.
  Result: FAIL slivers 3.6 % (176). The silhouette now reads shaggy (az000/az180: jagged locks on mantle, arms, hips,
  thighs). Diagnosis: the notches (30 % up) sit just under the 0.75 L row: needle triangles in the tooth faces.
- r12: Fix: the second row at 0.6 L.
  Result: PASS (slivers 0.6 %, hit/float/z-fight 0), 4854 tris, 6 colours.

## Stage 4
- r1: rig 11 bones + .R (roll auto); clips idle 48, move 33 (heavy walk), attack 34 (double-arm overhead smash). Kit
  gates PASS (glbcheck OK; warn stretch 24 tris, posed clip 0.21 %). Junction probe FAIL: thighs knife 5 (1.92 r,
  115 deg), eyes side 0.02 + size 0.054 of head, ear membrane p10 3.1 mm. Arms PASS (knife 0, max fold 61 deg).
  Critique (thigh row, flag tile C): a red fold along the inner thigh where the flat crotch cap (z 0.72) meets the
  leg's transition ring.
- r2: Fix (S2): the crotch cap domes up toward the seam (L0 verts 0-3 / 10-12 up 1.2-3.5 cm).
  Result: knife 1.92 -> 1.83 r: not the place. A fold dump of the s4 GLB (merged, concave > 60 deg near the hip):
  115-117 deg edges at z 0.72, x 0.11-0.13, y -0.04..0.17 = the crotch cap's SIDE edge (L0 verts 4-8).
- r3: Fix (S2): the cap side drawn in 45 % (x 0.13 -> 0.07, the thigh's inner wall line), so the wall runs straight
  up into the cap instead of tucking under it.
  Result: knife 2 (96 deg) left, fold dump: one long diagonal (0.29 m) at the FRONT groin (0.20, -0.06, 0.77): the
  belly underside vs the thigh front, made worse by drawing in L0 verts 3-4 (was 91 deg before).
- r4: Fix (S2): only L0 verts 5-9 drawn in; the belly's lower front (L0b verts 3-4) 3 cm down, 1 cm forward.
  Result: 113.8 deg (worse). r5 (transition front verts 5 cm forward): 143.6 deg, worse again (the selection also
  caught L0 v5). Fold dump: the edge's faces are the belly col-4 face (normal -y, a touch UP) and the down-back
  transition wall.
- r6: Fix: r4/r5 reverted; the crotch front (L0 v3-v5) recedes 3-6 cm so the col-4 face turns down-forward.
  Result: FAIL s2 self-intersection 2 + knife 171 deg: v5 is the rim itself; moving it back folds the transition.
- r7: Fix: r6 reverted; only the col-4 face's free lower corner L0 v4 recedes 2.5 cm (v3 1.2 cm).
  Result: 128 deg: the fold's col-4 triangle faces down-back because v5 was drawn in past v4. Groin kept at the r3
  state (96 deg, 2 edges, under the hip fur skirt; crops checked at the end).
- r8: Fix (eye: side 0.02, size 0.054 of head): the socket moves to column 2 (x 0.11-0.16, by the face corner), the
  lens normal turned out (n + 0.9 x), lens r 20 -> 24 mm.
  Result: eye 0.51/0.59/0.23, diam 0.069 head (size now PASS); side still < 0.40.
- r9: Fix: lens turned further out (n + 1.8 x).
  Result: side 0.30/0.35. Eye crops: the lens sits on the face box's FRONT plane, the box corner a hard 90 deg: from
  az090 the lens is seen edge-on.
- r10: Fix (S2): the face box's front corner (E0/F0 vertex 3) bevelled 4 cm back, 1 cm in (N1 v3 2 cm): the eye face
  turns forward-out.
  Result: eyes PASS 0.38/0.62/0.58 (L), 0.40/0.66/0.62 (R), diam 0.068 head, proud 11.6 mm.
- r11: Fix (ear membrane p10 3.1 mm < 9.6): ear_cup thickness 0.16 -> 0.55, cup 0.15, rim band 0.22.
  Result: ear p10 2.7 mm (the cup rim is thin by design).
- r12: Fix: the ear is a solid round puck (8 sides, 3 rings, a slight dip in the outer face, inner colour there);
  ear_cup tried and dropped (thin rim fails the membrane floor at any thickness).
- r13-r14: the transition ring's front vertices 4 cm forward (clean selection: no loft vertex): 132 / 127 deg, worse;
  the dump shows the fold's faces are the belly UNDERSIDE (col 4, facing down) and the leg wall (forward).
- r15: Fix: r13 reverted; the crotch front corner L0 v4 4 cm FORWARD (v3 2 cm): the underside tips forward-down.
- r15 Result: 114 deg, the fold moved to the crotch front (v3). Diagnosis: the fold is real form: the belly bottom
  (L0b front -0.29) overhangs the thigh front (-0.09) by 20 cm.
- r16: Fix: r15 reverted; the belly bottom recedes toward the thigh line (L0b front verts 0-4 back 3-8 cm).
- r16 Result: unchanged 96 deg (the moved verts are not on the fold's faces). Dump: the fold joins the triangle
  (L0 v4, L0 v5, L0b v5) = belly underside facing DOWN, to the leg wall facing FORWARD.
- r17: Fix: r16 reverted; L0 v4 drops 6 cm (v3 3 cm): that triangle faces forward-down.
- r17 Result: 150 deg: dropping v4 turned the triangle to face BACK (v4 sits in front of the rim edge, not below).
- r18: Fix: L0 v4 RAISED 6 cm (v3 3 cm).
- r18 Result: thigh knife 0 (max concave 85.6 deg). Left: seam strip 1.03 r / 14.5 mm (flag tile B: the back-inner
  thigh by the crotch). Diagnosis: the crotch dome lifted L0 v10-v11, which are leg-rim vertices: the transition
  faces under them were squeezed to 14 mm.
- r19: Fix: the dome only on the cap-only vertices (L0 v0-v3, v12).
  Result: ALL junctions PASS: thighs knife 0 (max concave 85.6 deg), strip 1.0 r; arms knife 0 (max 61 deg).
- r20 (full run + orbit): ALL kit gates PASS (glbcheck OK; warn stretch 24 tris, posed clip 0.21 %), junction probe
  PASS, eyes PASS, ear membrane PASS. Separation (checks/): arm-torso 12.1 cm, legs 21 cm, hand-leg 52 cm.

## Owner-style review (checks/orbit18_sheet.jpg, junction crops r20)
Junction crops: shoulders hidden under the mantle, no slit / speck / knife; thighs clean under the hip and thigh
skirts; groin dark but closed. Flaws seen: (1) the grey ear pucks stand off the hood as knobs (az135, top, +45 az90);
(2) the chest between the mantle hem and the hip skirt is bare smooth plating, and the hip skirt reads as a belt
(az0); (3) the brow is painted white, so the mask stops at the eye (eye crops) - the sheet's mask includes the brow.
- fix 1 (r21): ears sunk 2 cm and 15 % smaller.
  Result: PASS; ear membrane 54.7 mm.
- fix 2 (r22): a chest bib (z 1.70 -> 1.44, +-52 deg of the front, under the beard) and a belly bib (1.42 -> 1.20,
  +-40 deg): the bare front gets the sheet's layered chest shag, and the hip skirt is no longer the only band.
  Result: PASS; az000/hero: layered chest shag, the hip skirt now one tier among many (no belt read).
- fix 3 (r23): the face mask paint takes the brow (z < 2.285, x < 0.20).
  Result (r23, full run): ALL kit gates PASS (glbcheck OK; warn stretch 24 tris / posed clip 0.21 %), junction
  probe PASS (arms knife 0 / max fold 61 deg / strip 1.0 r; thighs knife 0 / 85.6 deg / strip 1.0 r), eyes PASS
  0.38/0.62/0.58 and 0.40/0.66/0.62, ear membrane PASS 54.7 mm; separation PASS.
- Final orbit18 (orbit18_sheet.jpg): white shaggy biped, hood sloping into a broad round mantle (top view round, no
  shoulder shelf from top or +45 az180), layered jagged tiers on chest, arms, hips, thighs, grey mask / hands / feet.
- Residual: the face is a grey box (no muzzle or nose shape, the brow a straight edge); the rear and flanks below
  the mantle are smooth (tiers mostly read from the front); the ears still show as small grey knobs from above; the
  thigh seam strip sits exactly at the gate (1.0 r); review/ (run.py --review), side_by_side.jpg (--compare),
  side_by_side_sheet.jpg (sheet vs model, checks.py).
