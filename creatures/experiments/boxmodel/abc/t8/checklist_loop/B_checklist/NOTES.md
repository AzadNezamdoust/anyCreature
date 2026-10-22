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

## B arm: checklist loop + version tree (t8, 2026-10-22)
Frozen CHECKLIST.md (16 Q). Views: stage4 colour renders + junction/detail sheets + beauty review set
(versions/TAG/rv: az000, el045, az090, az180, top, hero, el180, el270 via scratch render_glb wrapper). Snapshots of every
build (GLB, renders, program) in versions/TAG/; programs also as versions/gorilla_TAG.py.
- r12 baseline = unchanged copy of zoo gorilla (s4 r11). All gates PASS, 2796 tris, eyes 0.47/0.73/0.42.
  Answers (Y = yes): Q1 N (az000 flat face plate) Q2 N (az090 smooth arc) Q3 N (hero: helmet + dark visor) Q4 N (az090
  dome) Q5 Y (eye crops, gate PASS) Q6 N (az090 rectangle down the flanks) Q7 N (az180 no taper) Q8 Y (top: behind the
  shoulders, clean line) Q9 N (az090 straight tube) Q10 N (az000 columns) Q11 Y Q12 N (detail sheet 192 px: dark lumps,
  fingers not countable) Q13 Y (junction crops) Q14 Y Q15 Y Q16 Y. Score 7 -> CHAMPION r12.
- Round 1 (from NOs Q6/Q7 and Q1/Q2):
  - r13a (stage3 body_rule): per-ring saddle column limit SADDLE_J (R0 3, R1-R4 5, R5 6, R6 7, R7 8, R8 9, R9 11,
    R10 12) + smooth_borders(fur/saddle, hip roots guarded). Gates PASS (borders: 8 cuts, stair corners 16 -> 2),
    2796 tris. Q6 Y (az090 diagonal patch on lower back + rump) Q7 Y (el180 narrows to the shoulders, dark shoulders) Q8 Y
    (top rounded front border, behind the shoulders); others as r12. Score 9.
  - r14b (stage2 face): H3 j0 nose bridge back 2 cm, H2 nose 1.5 cm / H1 lips 3.5 cm forward (j0-j1, j2 0.7), H1/H2 j3
    back 1 cm, H2/H3 j4 cheekbone out 1.2 cm, H4/H5 j4-j5 temple in 1 cm. Gates PASS, eyes 0.47/0.73/0.42, 2796 tris.
    Q1 Y (az000 nose wedge + lip shelf) Q2 Y (az090 brow > recess > lips > chin) Q3 N (still a visor plate). Score 9.
  - Pairwise (beauty set, both orders): r13a beats r12 in both (side/rear/top saddle reads like the sheet); r14b beats
    r12 in both (el045/hero lip block; small). Both qualify; tie on score -> r13a vs r14b: r13a is the bigger read at game
    distance (3 views change). DECISION: champion = r13a (score 9). The r14b face edit stays a candidate for round 2.
- Round 2 (champion r13a, NOs Q1 Q2 Q3 Q4 Q9 Q10 Q12):
  - r15a (stage2 face, Q1/Q2/Q3): the r14b face block + brow arches (H4 j1/j2 up 0.8 cm, H4 j0 down 0.5 cm). Gates PASS,
    eyes 0.46/0.73/0.42, 2796 tris. Q1 Y Q2 Y Q3 N (hero: still a visor plate; the arches barely read); rest as r13a.
    Score 11. Pairwise vs r13a: r15a wins both orders (el045/hero/az000 lip block juts).
  - r16b (stage2 arm rings, Q9/Q10): each arm ring scaled about its centre in its frame (elbow 0.90/0.92, forearm top
    1.15/1.10, mid 1.06/1.04, low 0.96, wrist 0.88/0.90; 10 verts each), elbow-loop rear verts back 2 cm (knob). Gates
    PASS, junction numbers unchanged (upperarm knife 0 / 79 deg), eyes 0.48/0.74/0.43, 2796 tris. Q9 Y (az090 forearm
    swells below the elbow) Q10 Y (az000 elbow pinch, forearm bulge) Q11 Y; rest as r13a. Score 11. Pairwise vs r13a:
    r16b wins both orders (massive forearms like the sheet in all four views).
  - DECISION: both qualify; tie 11/11 -> r16b (the change reads in every view at game distance; r15a only up close).
    Champion = r16b (score 11). The r15a face block is independent (other edit target) -> round 3 variant a.
- Round 3 (champion r16b, NOs Q1 Q2 Q3 Q4 Q12):
  - r17a (stage2 face, Q1/Q2): the r15a face block (r14b moves + brow arches) on r16b. Gates PASS, eyes 0.46/0.73/0.42,
    IoU vs S1 min 0.981, 2796 tris. Q1 Y Q2 Y; rest as r16b. Score 13. Pairwise vs r16b: wins both orders.
  - r18b (stage2 head, Q1/Q2/Q4): r17a + sagittal crest ridge - dorsal seam j13 of H1-H6 up 0.5/1.2/2/3/3/2.5 cm, j12
    x 0.7 (+ half the lift), j11 x 0.9, crest poke vertex +2.5 cm. Gates PASS, eyes 0.46/0.72/0.42 (diam 0.069 head),
    junction unchanged, 2796 tris. Q4 Y (az000/hero peaked crown like the sheet front, az090 a peak, not a dome); Q3 N
    (dark visor plate remains); rest as r17a. Score 14. Pairwise vs r16b: wins both orders (crown + muzzle).
  - DECISION: champion = r18b (14 > 13). Budget (3 rounds, 6 variant builds) spent. Final = s4 r18 build, no rebuild.
- FINAL r18b: all kit gates PASS (glbcheck OK, techqa PASS, warn posed clip 0.65 %), junction probe PASS (upperarm knife
  0 / 79 deg / strip 0.86 r; thigh knife 0.89 r / 91 deg / strip 0.62 r), detail gate PASS (6 groups), eyes PASS
  0.46/0.72/0.42, 2796 tris (body 2316), S1 lock 84dfdc7687a2c855 PASS, IoU vs S1 min 0.981. orbit18_sheet.jpg.
  Open: Q3 face still a dark visor plate (paint j0-j2 rectangle); Q12 fingers not countable at 192 px; az135/az225 the
  haunch saddle border is a saw-tooth (guarded hip-root verts not relaxed) - seen only on the final orbit18.
