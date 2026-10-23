# gorilla - t7 box model, zoo workflow v2

Sheet: refs/gpt/v3/gorilla/sheet_1.png (side TL, front TR, rear BL, top BR). refs.py --height 1.5 (crest), length 1.62,
width 1.09. Marks added to blueprint.json by hand (eye, ear, shoulder, elbow, wrist, hip, knee, ankle). The plan view
trace carries contact-shadow specks along the flanks (y 0.12-0.24); not redrawn (IoU only).
- Identity cue (gorilla, not bear / ape-man): knuckle-walk stance - the torso slopes UP from the rump to huge
  shoulders; very long, massive arms planted on knuckle pads in front; short bent hind legs; a high sagittal crest on a
  head hung low and forward between the shoulders; a muzzle that juts under a heavy brow; a clear jaw; silver saddle.
- Plan: ONE spine loft of 14-vertex half rings rump -> crest (ventral seam under the belly, up the chest front, under
  the jaw and up the face; dorsal seam along the back, up the trapezius slope to the crest). Rings level-axis over the
  haunch and belly, tilting up through the chest into the head (troll hunch layout). Arms: minotaur/troll shoulder
  method translated to a sloped torso (below). Legs: rhino window method (4 x 3 faces of the haunch underside, a
  transition ring, level rounded-box sections). Hands: knuckle pads in the arm chain + finger pieces (S3). Ears:
  ear_cup pieces (S3). Eye: inset socket (S2) + lens piece (S3).
- Shoulder translation: with tilted rings a RING runs up the torso side (belly -> back), so the line along the top of
  the arm root is a ring COLUMN. The deltoid line = column j8 of C0..C2, hand-placed as each ring's widest point
  (CH profile); the arm region is 2 spans (C0 -> C2) x 3 faces (j5 -> j8) whose top edge is that j8 line; the chest
  keel j1-j4 stays under 0.4 W so the hanging arm clears it; the trapezius (j9-j12) rounds over to the dorsal seam.

## Stage 1
- r01 Critique: gate FAIL, 64 self-intersecting pairs at the arm root front (0.33, -0.48, 0.93). Also: the head a
  tilted "top hat" (az000), the rump a flat oval cap (az135/180). IoU side/front/top 0.929/0.892/0.880, 2168 tris.
  Diagnosis: the arm's front wall (ring 0 front at y -0.59, x 0.21-0.53, z 0.9) runs through the chest's ventral faces
  (C2 j3-j4 at x 0.30, y -0.52): the CHEST profile was 0.6 W wide at j4.
- r02 Fix: hand-placed CH profile on R10-C2 (keel <= 0.40 W at j1-j4, widest 0.98 W at j8 = the deltoid line) and the
  region roles' e1 from the j5 column to the j8 column (inner -> outer), e2 = y. Result: still FAIL, 40 pairs near
  (0.28, -0.50, 0.95).
- r03 Fix: upper-arm ring 0 back 2 cm, ry 0.22 -> 0.18. Result: FAIL 28 pairs. A scratch probe (isect.py on s1.glb,
  doubles merged) put every pair INSIDE the arm root (hug ring vs ring 0, inner wall), not arm vs chest.
- r04 Diagnosis: the region slopes 45 deg (its lower edge runs z 0.80 at C0 -> 0.95 at C2); ring 0 at z 0.90 sat above
  the region's rear-low corner, so the hug band folded back over it. Fix: ring 0 down to z 0.80 (one upper-arm ring
  fewer: 0.80 / 0.69 / elbow 0.58). Result: ALL S1 gates PASS, 2128 tris, IoU 0.929/0.892/0.879.
- r05 Critique (az000/az045 own clay views, scratch views.py): the head a tilted drum ("top hat") - every head ring
  round and ~0.2 wide. Fix: hand-placed pear JAW/HEAD profiles (face side full, skull tapering dorsally to the crest).
  Result: PASS, 2128 tris, IoU 0.929/0.898/0.881; the head now a bullet, still a horizontal "brim" groove at H3.
- r06 Critique (az135/az180): the rump a flat oval lid (R0 cap 0.30 x 0.24). Fix: R0/R1 smaller and closer to the
  end, the rump cap poked 2.2 cm out (a low dome, like the crest). Result: PASS, 2132 tris, rump reads round.
- r07 Critique (rear views): hind legs read as posts under a big haunch (window 3 faces, 0.22 m across). Fix: leg
  window 4 x 4 faces (j1-j5, 0.11-0.42 m), sections rx 0.17/ry 0.22 at the knee. Result: PASS, 2196 tris, side IoU 0.938.
- r08 Critique (head crops): the H3 eye ring set back 3 cm made a groove round the whole head. Fix: the face seam
  smooth through H3 (-0.765), HEAD profile with a flat face front (j0-j2 within 2 % of the chord). Result: PASS; head
  still a capsule with a neck crease at T2 -> H0u (W 0.33 -> 0.24).
- r09 Fix: ring widths fall smoothly T1 0.44 -> crest 0.07 (head and trapezius one mass, no neck), the head ring's
  middle wider than the face front. Result: PASS, IoU 0.937/0.889/0.884; the neck crease is gone.
- r10 Critique (blueprint front overlay): the trapezius bulged into a round dome past the sheet's straight
  shoulder -> crest line (x 0.30 at z 1.3 vs 0.20). Fix: TRAPP profile on T1/T2 (dorsal half falls in a straight
  line). Result: PASS, front IoU 0.889 -> 0.903.
- r11 Fix: broad flat back (BODY back 0.12, CH dorsal flatter). Result: PASS, front IoU 0.893; +45 az180 then showed a
  level shoulder shelf with a vertical outer wall (T-bar risk).
- r12 Fix: CH dorsal slopes again from the j8 deltoid line to the spine (0.90/0.74/0.52/0.27); T1 continues the chest
  keel and the j8 shoulder line (T1P; the TRAPP T1 bulged out at j5 over the arm front: a dark wedge). Result: PASS,
  IoU 0.937/0.903/0.883; the wedge is smaller.
- r13 Critique (az060 crop): a dark slit between the upper arm's back wall and the rib flank (arm ring 0 back at
  y -0.17 against R10's side at -0.20). Fix: upper-arm rings forward (-0.40/-0.44) and shallower (ry 0.175/0.185),
  R10 W 0.42. Result: PASS, 2196 tris; the elbow back stays at -0.28 (sheet -0.285).
- r14 LOCK (+ junction probe: body open 0 / non-manifold 0 PASS; eye FAIL "no piece named eye", expected before S3;
  no rig at S1 so no limb roots). LOCKED: 1100 verts, 2196 tris, edge sha256 9fe4cff059c46f71, IoU
  side/front/top 0.937/0.903/0.882. Biped/primate checklist at lock: chin/jaw - jaw-line ring H0u (F -0.725) 5 cm
  ahead of the throat T2 (-0.675), chin H0 ahead again, step chin -> throat from az090 yes; shoulders - deltoid line =
  the chest rings' widest column j8, arm region 2 x 3 faces with its top edge on it, first ring = root loop pushed out
  unshrunk yes; trapezius slopes straight shoulder -> crest (front overlay) yes; knuckle stance: arms planted, legs
  bent, belly clear yes. Open at lock (for S2 vertex moves): a collar step C2 -> T1 -> T2 seen from the top; the face
  is a broad flat plate (brow, eye, muzzle still to shape); forearms slimmer than the sheet's.
- r15/r16 RE-LOCK (junction, logged; old lock in old_locks/lock_r14): probe s4 r01 put a 138 deg armpit fold at x 0.23-0.30
  (the hug ring pushed out-forward-DOWN along the region normal, then the arm's inner wall turned back in under it).
  Fix: the hug ring's inner half is pushed straight out sideways (direction lerped normal -> +x by the role's -a), the
  deltoid half stays along the normal; CH keel j4/j5 0.33/0.40; ring 0 x 0.39, rx 0.15. Result: armpit max 88 deg
  (scratch folds.py), PASS. LOCKED r16: 1100 verts, 2196 tris, edge sha256 84dfdc7687a2c855, IoU 0.937/0.903/0.883.

## Stage 2
- r1: elbow + knee loops, eye socket (inset H3-H4 col 1), brow ridge forward. PASS, 2316 tris, IoU vs S1 0.996.
- r2 Critique (top / az000): a collar step C2 -> T1 -> T2. Fix: those rings relaxed along the loft columns 5-12 (2x).
  Result: PASS; the top view shows one sloping trapezius mass, no collar.
- r3 Fix (probe s4 r01, thigh 135 deg groin): knee section inner verts out 4 cm, front back 2 cm (transition ring half).
  Result: groin 98 deg.
- r4 Critique (probe s4 r02): 112 deg fold at the shoulder front (C2 j5-j6) - T1 j4/j5 stood past the arm region's
  front-lower corner and the relax was pulling C2 region-edge verts toward deleted C1 verts (vert_near hit hug verts).
  Fix: relax starts at C2 (C2 fixed), T1 j4/j5 drawn in 3/5 cm. Two tries that re-aimed the hug band forward made it
  worse (122-152 deg) and were dropped. Result: max 87 deg; probe s4 r03 upperarm PASS (knife 0, max 79 deg).
- (via s4 r04-r07, S2 code) groin: the ventral seam between the thighs dropped 3 cm (R1-R5) - knife 0.89 r / 91 deg,
  thigh PASS; socket 3 mm deep, brow 1.3 cm (eye side view); muzzle forward (H1 2 cm, H0 1.5, H2 1) and face columns j3
  1.5 cm back (the face was a flat box plate).

## Stage 3 / Stage 4
- s3 r1: palette fur/saddle/skin + eye/pupil (5 colours); lens eyes; ear_cup ears; finger rolls and toes (box chains).
  Hands: the parts-library `fist` was tried on paper and rejected - it is a 0.25 m tall punch block on a wrist, the
  sheet's knuckle-walk hand is a 0.16 m weight-bearing pad, so the pad is in the arm chain and the four curled finger
  rolls are pieces (no library knuckle-walk hand).
- s4 r01: all kit gates PASS; probe FAIL: arm knife 1.96 r, thigh 2.61 r, attack clip 13 % (upperarm.R swung BACK into
  the thigh: with roll auto +X swings forward), eye side 0.03 and 0.053 of the head, ear membrane p10 3.3 mm.
- s4 r02-r07: attack sign fixed (clip 0.65 % warn only); lens 46 mm, normal turned out (n0 + 1.9 x), 15 mm out; ears
  became closed 13 mm slabs (ear_cup rim was paper); paint by loft quad (ring, column) instead of height (stepped saddle).
  r07: junction probe PASS.

## Owner-style review (orbit18_sheet, s4 r08 junction crops)
Flaws seen: (1) the saddle border stepped face by face on the haunch (thigh crops B, az135/az225); (2) after fix 1, one
big zig-zag notch where the rump-end rule met the back rule; (3) the face a brown flat plate (reads as a mask); shoulder
crops: no shelf from +45 az180 or the top, no slit, the armpit reads as a soft crease.
- fix 1 (r09): one border column for back + haunch (j >= 6) -> clean band, but (2) appeared.
- fix 2 (r10): j >= 5 on R0-R9, no rump exception -> one clean border line; rump silver from behind like the sheet.
- fix 3 (r11): face skin charcoal #3d3a3b (was brown #46403d), face paint only the front columns j0-j2 of H0-H3.
- FINAL s4 r11: ALL kit gates PASS (glbcheck OK; warn: posed clip 0.65 % of surface), junction probe PASS (upperarm knife
  0 / max 79 deg / strip 0.86 r; thigh knife 0.89 r / 91 deg / strip 0.62 r), eyes PASS 0.47/0.73/0.42, ears membrane
  PASS 13 mm, separation PASS (legs 21.5 cm, forearm-body 11 cm). 2796 tris (body 2316), 5 colours.
- Residual: the face is still a flat plate with the eyes at its top corners (no nose or lip planes); the arms are long
  straight tubes (no forearm swell or elbow knob from the side); the trapezius/head from the side reads as one smooth
  dome (crest ridge soft).

## FACE pass (2026-10-22): checklist + champion loop (FACE_CHECKLIST.md, frozen), start = B_checklist r18b
Backup of the zoo state: before_face/. Code = abc/t8/checklist_loop/B_checklist/gorilla.py. Views per build:
versions/TAG/fc (head close-ups front/3q/side + 192 px whole creature). Judge = Opus art-director seats, blind, one per
order; a variant must win BOTH orders vs the champion. Builds: run.py --stage 4 --junctions --details --no-orbit.
- r19 baseline (B r18b rebuilt on the latest kit; face moves refactored onto S1 vertex handles `hv()` - vert_near on
  moved verts had raised a socket vertex instead of the brow arch: eyes 0.46/0.73 -> 0.47/0.75). All gates PASS, 2796
  tris. Face checklist: Q1 N (front: brow a flat bar) Q2 Y Q3 N (lens 27 mm proud at the plate's top corners) Q4 N Q5 N
  Q6 N Q7 Y Q8 N (rectangular dark plate) Q9 Y Q10 N Q11 Y = 4. CHAMPION r19.
- Round 1. Critique: the face is a flat visor plate (front/3q), eyes on its top edge.
  - r20a (S2): brow H4 j0-j4 forward 2-3 cm as one shelf, forehead H5 back 1 cm, eye band H3 j1/j2 back 1 cm, outer orbit
    open, nose H2 j0 forward 1.5 cm; socket cut AFTER the face moves (6 mm deep), lens offset 15 -> 8 mm. Gates PASS,
    eyes 0.43/0.67/0.45. Q1 Y Q3 Y; score 6. Pairwise: lost order 1, won order 2 = flip -> no preference (ties to the
    champion). Judge: the continuous shelf makes ONE dark eye band = a visor slot at 192 px.
  - r21b (S3 paint): skin as a shield (eye band + brow top + cheeks), lighter warm #4b4645. Lost both orders (a pale
    mask). Result: champion stays r19; dark skin kept (#3d3a3b).
- Round 2 (champion r19; NOs Q1 Q3 Q4 Q5 Q6 Q8 Q10).
  - r22c (S3): a hand-built chunky nose pad (8-point sections, 3 rows, back buried; widest at the nostril line, narrowing
    up between the eyes) with two nostrils on its down-facing lower band (pupil colour, no new colour). Two tries at the
    nostrils first (vertical dark slots read as teeth). Gates PASS (hit 0, float 0), 5 colours. Q4 Y Q5 Y Q10 Y; score 7.
    Pairwise: won BOTH orders (nose + muzzle mass step forward).
  - r23d (S2): r20a's brow turned into two ARCHES (glabella H4 j0 only 0.5 cm fwd and 0.8 cm down: a V into the bridge,
    separate sockets) + a mouth-line loop (loopcut H0->H1, front j0-j3 creased back 0.8-2.2 cm) with the lower lip/chin H0
    j0-j2 1-1.5 cm forward. Gates PASS, eyes 0.42/0.67/0.43, junctions unchanged. Q1 Y Q3 Y Q5 Y Q10 Y; score 8.
    Pairwise: won BOTH orders (V brow shelf over sunken sockets, stepped brow-muzzle-lip-chin profile).
  - DECISION: both qualify; 8 > 7 -> CHAMPION r23d. r22c's nose (independent, S3) goes to round 3 as variant e.
- Round 3 (champion r23d; NOs Q4 Q6 Q8).
  - r24e: r23d + the r22c nose pad (S3). Gates PASS. Q4 Y; score 9. Pairwise: won BOTH orders (nose wedge + mouth slit
    read at 192 px front).
  - r25f (S2): cheek H2 j2 back 1.5 cm, cheekbone H2 j3 out 0.8 cm, muzzle corners H1 j2/j3 back 1.2/0.5 cm. Gates PASS.
    Q6 Y; score 9. Pairwise: won BOTH orders (rounded, faceted muzzle turning into the cheeks; modest).
  - DECISION: tie 9/9 -> r24e (its change reads at game distance; r25f only close up). Champion r24e; r25f to round 4.
- Round 4 (champion r24e; NOs Q6 Q8).
  - r26g: r24e + the r25f cheek block. Pairwise: won one order, lost the other (judge 2: the muzzle becomes a sharp
    beak wedge in profile) = flip -> no preference, ties to the champion.
  - r27h (S3 paint): skin out to the muzzle sides (H1/H2 j3). Lost both orders (indistinguishable / squarer plate).
  - DECISION: champion stays r24e. Budget (4 rounds, 8 variants) spent.
- FINAL r24e (s4 r28 full run + orbit): ALL kit gates PASS (glbcheck OK; warn posed clip 0.65 %, as before), junction
  probe PASS (upperarm knife 0 / 79 deg / strip 0.86 r; thigh knife 0.89 r / 91 deg / strip 0.62 r), detail gate PASS
  (6 groups), eyes PASS 0.42/0.67/0.43 (diam 0.068 head), S1 lock PASS, IoU vs S1 min 0.981, separation PASS.
  2892 tris (S1 2196), 5 colours. Face checklist 9/11 (r19 baseline 4). Still NO: Q6 cheek planes (r25f's gain flipped
  when stacked on the nose), Q8 at 192 px the dark skin area still reads as a rectangular plate in front view.
  orbit18_sheet.jpg (old: orbit18_sheet_before_face.jpg), face_before_after.jpg, versions/ (every variant: program,
  GLB, face renders).

## HEAD rebuild pass (2026-10-22/23): the face in the loft (HEAD_CHECKLIST.md, frozen), champion at start r24e
Backup: before_head/ (program, locks, logs, sheets, stage1/, stage4 GLB); old lock old_locks/lock_r16_face_r24e.json.
Builds: re-lock S1 then run.py --stage 4 --junctions --details --no-orbit (scratch hbuild.sh); views versions/TAG/fc.
- S1 RE-LOCK (logged): two new head rings in the spine loft - Hm (mouth line, lerp H0->H1 0.8) and He (upper lid, lerp
  H3->H4 0.6) - and hand-placed face vertices j0-j4 (FACE dict) on H0u..H4; the r24e S2 face moves (muzzle forward,
  brow shelf/arches, mouth loopcut + crease, cheek moves) are replaced by them. Body, arms, legs, density unchanged
  (1100 -> 1152 S1 verts, 2196 -> 2300 tris: the two head rings only). S2 keeps elbow/knee loops, collar relax, crest
  (Hm/He added to the crest list), groin, socket (now H3->He col 1). S3: skin by (span, column) SKIN_J (shield: chin
  j0, lower lip j0-1, mouth j0-2, muzzle/eye band/brow underside j0-3) + smooth_borders fur/skin; nose = a pad lying on
  the muzzle surface (ray-cast rows, lifted 0.7-2 cm), not the r22c wedge.
- dev d29: flatter than r24e (muzzle only -0.828; nostril cells = teeth). d30: stronger forms, nostril band = mouth,
  z-fight 4 (nose). d31 (profile measured off the sheet side view: upper lip 12 cm ahead of the eye, brow 6 cm, nose
  9 cm; mouth at 78 % of the face height; eyes +-0.064): all gates PASS, eyes 0.46/0.71/0.40, 2976 tris.
- Round 1 (champion r24e, score 5/12 by builder): h1a = d31; h1b = h1a + a mid-tone blend band (skin2) round the face.
  h1a: won BOTH orders (judges 8/11, 8/11). h1b: won both orders (9/11, 6/11). DECISION: CHAMPION h1a (higher mean,
  one colour fewer). Shared NOs: the dark nostril cells read as a slot / grille mouth (Q4), nose wedge in profile (Q5),
  flat muzzle front with a vertical edge (Q3).
- Round 2 (champion h1a): h2a nostrils only under the outer wings + rounder bulb: flip (won order 1, lost order 2) =
  tie. h2b muzzle 1-2.4 cm further forward, rounder in plan: flip = tie. Judges (all four): every nostril paint reads
  as a grille mouth; brow still a straight visor (Q6); the upper lip/nose meet in a wedge tip in profile (Q5).
  Champion stays h1a.
- Round 3 (champion h1a; NOs Q4 nostril grille, Q5 wedge, Q6 visor brow, Q3 flat front). Both variants on h2b's
  rounder, more forward muzzle, no painted nostrils.
  - h3a: + brow ARCHES on the S1 brow ring (H4 j0 glabella down 1 cm / back, j1-j2 up 0.8 cm, j3 outer corner down
    1 cm). Gates PASS (eyes 0.46/0.71/0.40, junctions + details PASS, 2976 tris). Won BOTH orders (8/11, 8/11:
    lip line instead of the grille, two arches). CHAMPION h3a.
  - h3b: + the muzzle top H2 forward to the lip line (blunt upright front) and a lower nose pad (1.0-1.3 cm). Gates
    PASS. Won BOTH orders (7/11, 6/11: lip line, no grille). Both qualify; 8 > 6.5 -> CHAMPION h3a; h3b to round 4.
- Round 4 (champion h3a; NOs Q1 straight vertical cheek edges, Q3 flat front, Q5 wedge nose): h4a = h3a + h3b
  (stacked); h4b = h3a + a curved outline (cheekbone j3 out 1 cm, lower-face j3 in, skin column steps in below the
  muzzle top: H1/Hm j0-2, H0 j0-1).
  - h4a (r3a + r3b stacked): lost BOTH orders (a boxy forward snout / duck-bill in profile, weaker chin) -> reverted.
  - h4b (r3a + curved outline): won BOTH orders (8/11, 8/11: straighter wide lip line, outline). CHAMPION h4b.
- FINAL h4b (4 rounds, 8 variants spent). Residual NOs (all judges): Q1/Q10 at 192 px front the darker face still has
  straight-ish vertical sides (a soft panel, no longer a rectangle with a slot), Q3 the muzzle front is one plane with
  a side crease, Q5 the nose reads as a small wedge tip in profile and has no readable nostrils (every painted
  nostril variant read as a grille mouth, so they were dropped).
- FINAL RUN (s4 r39, orbit, h4b code): S1 re-lock 1152 verts / 2300 tris, edge sha256 747e26af982ef8cf; ALL kit gates
  PASS (glbcheck OK; warn posed clip 0.91 %), junction probe PASS, detail gate PASS, eyes 0.46/0.71/0.40, IoU vs S1 min
  0.983, 2976 tris, 5 colours. --review, --compare (compare_engine.jpg), --clips --fix-clips then --clips: clip gate
  PASS (move pen 6.6 -> 0.08, attack 4.5 -> 0). face_before_after_head.jpg, orbit18_sheet.jpg (old:
  orbit18_sheet_before_head.jpg; underside tiles rendered clay).
