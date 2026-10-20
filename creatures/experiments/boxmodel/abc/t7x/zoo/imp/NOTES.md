# imp (t7x zoo, workflow v2)

Sheet: refs/gpt/v3/imp/sheet_1.png (2x2), refs.py --height 0.8 (horn tips) -> side length 0.595 m (wings + tail).
The plan view is not a true ortho (top length 1.35x the side): blueprint.json's top outline removed (troll/ogre did the
same); side marks eye / nose / chin / shoulder / hip added by hand. Side wins for proportions.

**Identity cue (imp, not goblin/gremlin):** a big round head with two short dark horns and huge pointed leaf ears on a
small pot-bellied body; bat wings from the shoulder blades; a thin tail ending in a flat spade. In the S1 loft: head,
ears, pot belly, tail + spade. Wings (closed slabs with spar ridges) and horns are S3 pieces (wing listed in
META['later'] for the IoU). Eyes: small round lens in a socket (not the sheet's big cartoon eyes).

Build: one loft of 14-vertex half rings, 20 stations crotch -> crown (11 torso/neck, 9 head; head rings tilt: front seam
down the jaw underside and face, back seam up the skull). Legs 2 spans x 5 faces of the crotch-hip underside, arms
2 spans x 4 faces of the chest side (C0 armpit -> C2 shoulder top), ears 2 faces (one column, two spans) of the skull
side, tail 2 back-seam faces of the R1-R2 span (seam wall removed: the mirror closes it), 12 stations, the last 5 the
spade. Limb rings: flat front/back rounded boxes.

## Stage 1
- r00: PASS, 2156 tris, IoU side/front 0.65/0.59 (no wings yet). Reads as a big-headed biped with ears and a spade tail.
  Critique: the ears read as thin spikes from the front and top (az000, top); the sheet's ear is a big broad triangle
  seen broad from the front, the rear AND the top (a cup facing front-up), base ~12 cm tall. Diagnosis: ear_frame puts
  the leaf width vertical so its normal is level (out-front): edge-on from above; EAR widths 0.046 half, widest mid.
  Fix: ear leaf normal set to (0.55, -0.65, 0.5) (front-out-up), width = n x d; EAR widest at the base (0.06 half)
  tapering to the tip.
- r01: PASS, 2156 tris, IoU 0.64/0.60. The leaf normal tilt changed little on the sheet: the ear base hides under the
  cranium overhang (head half width 0.125, ear root x 0.10), so only the narrow outer half shows from the front and
  top. Critique: ear still reads small/thin (az000 base ~6 cm tall vs the sheet's 12 cm, az180, top). Fix: EAR widths
  up: 0.075 / 0.060 / 0.038 / 0.017 half at t 0.12 / 0.40 / 0.68 / 0.88.
- r02: PASS, 2156 tris, IoU 0.64/0.61. Ears broader (az000/az180 read as the sheet's big leaves; top still shows only
  the outer half: the sheet's plan view is not a true ortho). Critique: the arms are planks (az090: 6 cm deep, straight,
  they hide the torso; az000: a square deltoid block); the sheet's arms are slim (~4.5 cm), taper to the wrist and bend a
  little at the elbow. Diagnosis: ARM rx/ry 0.025-0.034 constant-ish, all centres on one straight line. Fix: ARM radii
  down (deltoid 0.029/0.031, upper arm 0.025-0.023, elbow 0.021/0.023, wrist 0.017/0.019), elbow 4 mm back, wrist forward.
- r03: PASS, 2156 tris, IoU 0.64/0.61. Arms now slim and tapered (az000, az090), slight elbow bend.
  Critique: the head is a dome cut flat underneath (az000/az045: a wide dark under-plane from cheek to cheek); the
  sheet's cheeks round in to a narrower chin (half width ~0.08 at z 0.49, ~0.05 at the chin bottom). Diagnosis: H0u /
  H0 / H1 W 0.076 / 0.098 / 0.112 (as wide as the cheeks). Fix: H0u 0.058, H0 0.080, H1 0.103.
- r04: PASS, 2156 tris, IoU 0.64/0.60 (the traced outlines are coarse - the side trace cuts through the belly and arm,
  the front one notches the legs - so IoU is read only as a trend; the sheet images are the referee).
  The cheeks now round in to the chin. Critique: front (az000/az180) the torso is a straight-sided box with square
  coat-hanger shoulders; the sheet's torso is a pear (chest half 0.085, belly 0.105) with low sloped shoulders.
  Diagnosis: C0/C1 W 0.097/0.094 vs belly 0.105; deltoid cap centre x 0.128 at z 0.388. Fix: chest rings narrower
  (R6 0.096, C0 0.090, C1 0.086, C2 0.076), belly R3/R4 0.108/0.107, cap centre x 0.122, z 0.384.
- r05: FAIL self-intersection 6 pairs at (0.101, -0.09, 0.351): the deltoid cap's inner (armpit) point (x 0.093,
  z 0.362) now sits inside the narrower R6 ring. Fix: cap ((0.126, -0.09, 0.384), rx 0.026, ry 0.029, dz -0.012):
  armpit point (0.100, 0.372), 6 mm off the torso; outer point (0.152, 0.396), still lower/narrower than r04.
- r06: PASS, 2156 tris, IoU 0.64/0.59. Pear torso and low sloped shoulders now match the sheet front; armpit clear.
  Reads as the sheet's imp body plan from every view (big head, leaf ears, pot belly, stubby legs, spade tail); face
  detail (socket, brow) is S2, horns/wings/eyes S3. Lock next.

## Stage 2
- r01: PASS (lock assert, IoU vs S1 1.0, tech QA 0, slivers 1.0%), 2276 tris. Elbow + knee loops; eye socket inset
  (0.28) in the face nearest (0.068, -0.236, 0.59), floor 6 mm in: it sits at the sheet's eye height on the front-side
  corner (az000, hero). Critique: the face is a flat vertical plate: no brow over the socket (hero, az045). Fix: brow
  ridge - the H4 ring verts j 1-4 forward 5 mm and up 2 mm.
- r02: PASS, 2276 tris. Brow ridge in (small: the side eye check must stay >= 0.40).

## Stage 3
- r01: FAIL zfight 6 (hands), 3352 tris, 7 colours. Pieces: lens eyes (22.6 mm, in the sockets), a button nose lens,
  parts-library horns, parts-library 3-finger clawed hands bridged to the wrist rings, 3 toe claws per foot, bat wings
  (closed fan slab from the wrist hub: membrane 10 mm, spar ridges 21 mm, root R and attach A sunk ~1 cm in the back,
  scalloped trailing edge). Now reads as the sheet's imp from every view. --junctions: eyes PASS 0.59/0.91/0.59,
  membrane wings PASS p10 9.9 mm (floor 6). Critique (gate): green z-fight specks on the wrist bridge strip (az090 tech).
  Diagnosis: the hand root ring (0.034 x 0.030) as big as the wrist ring, forward 12 deg off the forearm: the bridge
  faces lie on the forearm's last faces. (r02 probe: claw_len 0 -> still 6, not the claws.)
- r03: Fix: hand root ring 0.027 x 0.023 (steps in from the wrist), forward along the forearm (0.2, -0.2, -1).
  Result: PASS (zfight 0), 3352 tris. Critique: palette reads dark brick/maroon (hero, az000 colour) vs the sheet's
  bright red-orange skin and salmon belly. Fix next: palette one step lighter and warmer.
- r04: PASS, 3352 tris. Palette lighter/warmer (skin #dc5a42, belly #f0977b, wing #8e3430): reads red, not brick.
  Critique: the horns are thin needles (az000, az090, hero); the sheet's horns are thick cones (base ~5-6 cm wide)
  curving a little back. Diagnosis: horn radius 0.023, taper 1. Fix: radius 0.029, length 0.11, taper 1.5, curve 30.
- r05 (orbit + junctions): PASS, 3352 tris, 7 colours. Horns now thick dark cones curving back (hero). Eyes PASS
  0.59/0.91/0.59 (22.6 mm, round 1.0, proud 10 mm); wing membranes PASS p10 9.9 mm. Eye crops: a small dark round
  lens under the brow. S3 done; S4 next.

## Stage 4
- r01: S4 gates FAIL drift 2 (both wings); glbcheck/clips/weights/folds PASS; tech-QA clip warn 0.06%.
  Probe FAIL: ear knife 4.15 r (140 deg) + strip 1.62 r; thigh knife 6.94 r (148 deg) + strip 1.45 r; tail0 knife
  1.57 r (92 deg) + strip 1.63 r; wing.L/R bone junction knife 1.01 r (the flags sit on the neck and armpit, inside its
  2 r = 13 cm region; the wing crops are clean); upperarm, piece wing roots PASS; eyes visible 0.57/0.88/0.57 but size
  FAIL 0.048 of "head length" (the probe measures the head-bone subtree extent = ear tip to ear tip, 0.48 m: >= 29 mm
  needed); membranes PASS (wings p10 9.9 mm, ears 8.7 mm). Crops: the crotch C-view shows a red knife ring where the
  inner thigh meets the crotch cap; the ear root a flared collar; the tail root a folded W around the first ring.
  Critique (worst gate): the wing roots slide in the back when the wings beat (drift). Diagnosis: wing.L runs root ->
  wrist and the flaps rotate about it, so the attach line R-A (10 cm long, sunk in the back) swings out of the skin.
  Fix: wing bone = a hinge along the attach line (head at A, through R), the beat keyed as twist (bone-local Y).
- r02: hinge wing bone: drift still 2 (the wing rides the chest bone while the skin at the low attach point A follows
  the spine: 9 deg chest pitch in the attack moves A ~8 mm = 1% L), and the probe's wing-bone radius became 240 mm
  (piece verts far from the hinge axis): a region over half the body. Fix: no wing bones; the wings bind with the
  body's weights (bind(body=)), so the sunk root follows the back skin exactly. The wings no longer beat on their own
  (they ride the chest/spine motion); the piece-wing junctions stay probed.
- r03: drift 0, but posed folds FAIL 1.67% (3.4% area) + stretch 9.3x: nearest-surface weights gave the wing tips
  the tail/ear weights. Fix: bind_wing - every wing vertex copies the skin weights of the body vertex nearest its
  projection on the sunk attach line A-R (rigid sheet riding the back).
- r04: drift 2 again. r05: shoulder-blade skin (|x| < 0.085, back, z 0.28-0.47) stripped of upperarm weights: drift 2.
  Diagnosis (debug replay of techqa's drift test inside the build): techqa anchors a seated piece on its FIRST 12
  vertices; with the fan built tip-first those included wing vertices 11-12 cm off the skin (nearest skin = head
  underside / ear), which "drift" 10-16 mm when the head tilts. The real near-skin vertices move <= 1.1 mm (GLB replay).
  KIT NOTE: techqa drift anchors are the first 12 vertex indices of a shell, not its seated vertices.
- r06: Fix: the 12 vertices of the sunk attach line (A, 4 points, R; scallop A-R now 4 points) are created first.
  Result: ALL S4 gates PASS (drift 0; max anchor growth 5.6 mm < 8 mm). Debug hook removed.
  Next (gate): eye size 0.048 of "head length" (the probe's head = head-bone subtree extent incl. the ears, 0.48 m).
  Fix: lens radius 0.0148 (29.6 mm = 0.062; still ~12% of the 0.25 m face width, small next to the sheet's eyes),
  socket inset 0.20 so the socket fits it.
- r07: eyes PASS 0.57/0.88/0.54, 29.5 mm = 0.062 head, proud 10.7 mm. All S4 gates PASS. Probe FAIL: thigh, ear, tail0.
  Critique (worst): thigh root knife 6.94 r at 148 deg + strip 1.45 r: crops A/B show a hard groin crease where the
  thigh's first ring (front y -0.167) juts forward of the root region's front edge (y -0.148) under the pot belly, and
  a crease at the back/crotch. Diagnosis: the leg region (R0-R2 cols 4-8) is narrower front-back than the thigh ring.
  Fix (S2, vertex moves): root fillet - Laplacian relax (3 x 0.5, smooth falloff) of the verts within 6.5 cm of the
  thigh root.
- r08: thigh fillet: thigh knife 6.94 -> 4.22 r but max still 147.6 deg, and tail0 now 6.37 r at the same 147.6 deg.
  The C (below) crops show where: the crotch cap n-gon (yellow fan strips) between the legs, folded hard against the
  inner thigh walls and the buttock crease; both the thigh and the tail regions reach it. Diagnosis: R0 (crotch ring)
  is a flat horizontal cap at z 0.15, 3 cm wide, and the inner thigh walls drop from it vertically/undercut.
  Fix (S2): R0 ring down 1.2 cm and x halved: a narrow rounded crotch, the inner walls slope down-out.
- r09: crotch drop: thigh 6.54 r (150 deg), slivers 2.3% FAIL. Reverted. Debug (concave folds on the welded GLB):
  the 147.6 deg fold is a 41 mm edge at (0.082, -0.035, 0.205) = the leg region's back edge under the buttock (the
  butt overhangs the thigh's back wall); 119 deg at the region's front edge under the pot belly; 140 deg at the ear
  root's back edge; 155-161 deg at the armpit (hidden: upperarm passes).
- r10 (= r08 state) PASS gates. Fix next (S2): the thigh's first ring back verts 1.8 cm back + 0.8 cm up (b-weighted)
  so the thigh's back wall continues into the buttock (positions recorded per role in stage 1, moved in stage 2).
- r11: thigh ring back verts back+up: thigh 4.2 r, max 147.9 (no better). Debug normals: the fold's wall face behind the
  hip faces INWARD (-0.97, -0.09, 0.22) next to a buttock face (0.76, 0.6, -0.26): the thigh's first ring sits out of
  line with its root loop, so the wall folds under the hip edge. Fix (S2): ring 1 takes 60% of the plan position of
  the root-loop vertex with the same role (walls drop near-vertically from the root edges); r11's back move removed.
- r12: ring-1 blend: thigh max fold 147.9 -> 122.5 deg, knife 4.12 r; tail0 back to 1.57 r. Still FAIL. The located
  folds all sit on the leg root region's edges (back edge under the butt 122 deg, crotch cap 93-103, front 98): the
  thigh ring is bigger front-back (14 cm) than its 5-face root (11 cm), so its walls fold out over the root edges.
  Fix: RE-OPEN THE S1 LOCK (old lock + program in before_relock/): leg root 3 spans x 7 faces (R0 crotch -> R3 hip
  side, cols 3-9: y -0.167..-0.013, the thigh ring now fits inside it, walls narrow down); thigh rings 4 mm narrower
  front-back; the S2 ring-1 blend dropped.

## Stage 1 re-lock
- r08-r09 (S4 r13): legs from 3 spans x 7 faces: thigh 4.9 r, max 115 deg; tail0 6.9 r (its region reaches the crotch).
  The flagged walls on the leg region's front/back edges are long vertical slivers: the region sits on the lower
  FLANK (its front/back edges run vertically up the hip), so the leg leaves along its own edges.
  Fix: a flat hip "seat": R1 (z 0.16, W 0.098) nearly level with the crotch ring R0 (z 0.15), so the R0-R1 faces face
  down; the leg root = that seat (1 span x 7 faces, a near-horizontal loop); first ring = the root loop pushed 1.2 cm
  along its normal and shrunk 0.92 (walls lean in, folds < 90 deg); the thigh rings start inside it. R2 z 0.207.
- r10/r11 LOCK (edge sha256 6f51dfa8caa1dfb5, 2300 tris). S4 r14 probe: THIGHS PASS (knife 0.21 r, max 101.6,
  strip 0.51 r). tail0 knife 2.32 r (102 deg: its top wall leaves the vertical rump level), ears unchanged.
  Fix (same diagnosis as the thigh: root smaller than the first ring, walls fold out): re-lock with lean-in hug rings
  on the tail (root loop 1.5 cm out, x0.85) and the ears (root 3 spans tall ~11 cm, hug 1.5 cm x0.9, the leaf never
  wider than its root: 0.050 half at t 0.16-0.40).
- r12/r13 LOCK (f173c6868095cf04, 2392 tris). S4 r15 probe: TAIL0 PASS (knife 0.36 r, strip 0.87 r), thighs PASS,
  ears 1.66 r (108 deg) + strip 1.73 r. Located: two edges at (0.084-0.093, -0.027, 0.575-0.604), the ear root's back
  edge: the leaf heads 40 deg back from the root face's normal, so its back wall folds onto the skull behind it.
  Fix (re-lock): ear root 1.5 cm further back on the skull (y -0.035: the root face turns out-back) and the tip 2 cm
  more lateral (0.245, 0.055, 0.672): the leaf leaves closer to its root normal.
- r14 LOCK (02fd415a): ears no better (2.91 r, 107.6 deg) and the eye fell to 0.059 of "head length" (the ear tip moved
  out). Located the folds: NOT on the ear: a 8 mm-wide head column BEHIND the ear root (y -0.027..-0.035), where the
  tilted head rings crowd their back columns; the ear root region itself was a 2.5 cm-wide strip on that crowded back.
  Crop A also shows the ear base as a thin square flange. Fix (re-lock): ear root on the head side (J ear y -0.075:
  the root strip 3.5 cm wide, normal (0.86, 0.5)), same tip.
- r15 LOCK (1e9d7a45): ears 2.29 r at 132 deg. Located: the root's back-edge hug wall folds against the leaf's
  first section, which sits 2 cm BEHIND the hug ring (the sections run on the straight root->tip line, 40 deg back
  from the root normal, over a 3.5 cm-wide root). Fix (re-lock): the leaf centres follow a quadratic path that leaves
  along the root normal (control point 6 cm out) and turns to the tip. Eye lens r 15.6 mm (head extent grew with the
  ear tip: 0.058 < 0.06).
- r16: S1 self-intersection at the ear root (0.121, -0.055, 0.625): the first leaf section now sat on the hug ring. Fix: first leaf station t 0.24 (2.3 cm out), hug 1.0 cm.
- r17 LOCK (e8898f03): eyes PASS (30-31 mm = 0.061-0.062). Ears 2.29 r at 118 deg. Located: the edge is the HUG ring's
  back edge: the first leaf section is thinner front-back (half 13 mm) than the 3.5 cm root strip, so its back wall
  turns forward (folds 118 deg); crop A shows the matching thin seam strip on the front edge. Fix (re-lock): leaf
  thickness tapers from the root: half 18 / 12 / 8 mm at t 0.24 / 0.45 / 0.68.
- r18 LOCK (56de8b3b): ears 2.19 r at 114 deg + strip 2.25 r: no hug/leaf size tuning removes the step where the
  root strip's shape changes into the leaf ellipse. Fix (re-lock): no hug ring; each ear ring MORPHS from the root
  loop's own shape (x0.94) to the leaf ellipse (morph 0.25 / 0.6 / 0.9 / 1 at t 0.14 / 0.34 / 0.56 / 0.76) along the
  normal-then-tip path, one more ring. Eye lens r 16.5 mm (R side measured 0.059).
- r19 LOCK (df9bb2e8): eyes PASS 0.064-0.067; ears 2.47 r but max fold down to 100.5 deg (from 114-140), strip 1.29 r.
  Located: the root's back edge, between the skull behind (normal (0.72, 0.69)) and the ear's back face (normal
  (-0.78, 0.57)): the leaf's thickness axis EAR_N (0.55, -0.65, 0.5) has a big +x part, so its back face leans in
  over the skull. Fix (re-lock): EAR_N (0.30, -0.85, 0.43): the leaf faces front-up, its back face turns back.
- r20 LOCK (19a39c33): ears unchanged (2.47 r, 102.5 deg): the first ring (morph 0.25) already leaned in through
  the leaf frame's e1 x-part. Fix (re-lock): first ear ring = the root loop's own shape x0.90 (morph 0: a short
  lean-in neck along the normal path), the morph to the leaf starts on ring 2 (0.45 / 0.85 / 1).
- r21 LOCK (133eb8d2): EARS knife 0 (max fold 75.5 deg): the root reads as a broad neck in crop A. Left: strip 1.52 r,
  9.4 mm wide - crop C shows it on the ear's lower edge 3-6 cm out (the flat leaf ellipse's end faces, creased).
  Fix (re-lock): leaf thicker mid-ear (half 18 / 15 / 11 / 7 mm at t 0.30 / 0.50 / 0.72 / 0.88): rounder ends.
- r22 LOCK (8c9dad55): strip 1.51 r / 10.1 mm (the threshold is 0.4 x median, ~10 mm: borderline thin end faces). Fix (re-lock): half thickness 22 / 18 / 12 mm at t 0.30 / 0.50 / 0.72.
- r23 LOCK (fc3e47c4): strip unchanged (1.49 r). Located (strip_dbg: the probe's sqrt(2A) median 28 mm): ONE needle triangle 57 x 10.7 mm on the SKULL behind the ear root (0.099..0.123, -0.047..-0.029, 0.556..0.605), creased 49 deg: the head rings' back columns are crowded by the HEAD profile's backward widest point (w -0.12). Fix (re-lock): HEAD profile w -0.05 (columns evenly spaced front to back).
- r24 LOCK (478f5957): eyes PASS; ear strip 1.7 r: the same 57 mm needle. Located exactly (vertex match): it spans ear ring 1 -> ring 2 on the back-bottom: ellipse_roles re-spaces the root's 8 vertices evenly round the leaf ellipse, so ring 2 is rotated against ring 1 (a twist). Fix (re-lock): ear roles = each root vertex's own normalised position in the leaf frame (no re-spacing).
- r25 LOCK (48104208): ear strip 1.15 r (needle gone). Located: a 38 x 11 mm triangle on the root -> ring-1 wall at the ear's top corner (crease 90): ring 1 sits only 1.3 cm out, so the whole root band is a ring of 1.3 cm strips. Fix (re-lock): ring 1 at t 0.22 (~2.4 cm out), the morph rings at t 0.38 / 0.55.
- r26 LOCK (23f55d41): strip 1.18 r: now a 38 x 10 mm triangle on the ear's flat TOP face (ring 1 -> 2), creased 85 deg at the rectangular root section's corners. Fix (re-lock): leaf positions on the ellipse at each root vertex's own angle (corners round off, no re-spacing), ring 1 morph 0.2.
- r27 LOCK (49c3a603, 1198 verts, 2392 tris). S4 r29: EARS PASS (knife 0.96 r at 92 deg, strip 0), JUNCTION PROBE PASS
  on every root (ears, upperarms, thighs, tail0, wing pieces), eyes PASS, membranes PASS, all kit S4 gates PASS.
  Lessons (imp): (1) a limb root must be at least as big as its first ring and the walls must lean in - the
  leg works from a flat hip "seat" (R0-R1 nearly level) with a 1.2 cm hug ring; (2) an ear morphs from its root
  loop's own shape to the leaf - keep each root vertex's angle (ellipse_roles' even re-spacing twists ring 2 into
  needles); (3) locate flags by exact vertex match before moving anything (4 blind moves did nothing).

## Owner-style review (s4_r30: round sheet, junction crops, close-ups, back34)
Visible flaws: (1) the wing finger spars painted skin red read as three light "arrows" on the membrane (hero, az090,
back34) - the sheet's fingers are dark ridges in the membrane colour; (2) the ears read as slim back-swept cones and
their flat root back face shows as a dark slab on the skull from back34 (sheet: a broad cupped leaf); (3) the far
wing seen edge-on from back34 reads as a plank down the back (inherent to a 45 deg swept bat wing; the sheet's
rear view shows the same plane); (4) the hands are small. No slit, speck, knife fold, seam strip, pinch,
poke-through or floating piece is visible at the shoulder, hip, tail or wing roots; the eye reads as a small round
dark lens in a clean socket in all three eye crops.
- fix 1 (r31): wing paint: only the arm bone (W-R) in skin red; the finger ridges in the membrane colour.
- fix 1 result (r31): PASS; spars now dark ridges, only the arm bone red. fix 2 (S1 re-lock, r28): ear leaf broader past the root (half width 56 / 52 / 38 / 20 mm at t 0.38 / 0.55 / 0.72 / 0.88; was 50 / 44 / 30 / 16) toward the sheet's broad leaf.
- fix 2 result (r32, lock e4d2e62d): probe PASS (ears knife 0.95 r, strip 0), eyes PASS. fix 3 (r33): hands 0.050 -> 0.062 wide (the sheet's hands are bigger, they read as stubs).
- fix 3 result (S1-S4 r33 with orbit, lock e4d2e62d202caf28): ALL GATES PASS - S1 (2392 tris), S2 (lock assert, IoU
  0.997), S3 (7 colours, 3644 tris), S4 (clips, weights, glbcheck OK idle/move/attack, tech QA hit/float/zfight/drift/
  folds 0, slivers 1.8%, posed clip warn 0.20%), junction probe PASS on all 9 roots, eyes PASS (0.59/0.84/0.47,
  32.5 mm = 0.066 head, round 1.0, proud 10.7 mm), membranes PASS (wings p10 9.9 mm, ears 12-15 mm). Separation:
  arms 35 mm clear of the torso (4.4% of height), legs 35 mm apart. --review and --compare run; the sheet comparison
  is side_by_side_sheet.jpg (checks.py), --compare's engine/grey/final strip is side_by_side.jpg.
Biped checklist (S4): chin/jaw - H0u jaw ring 4.5 cm ahead of the neck front, step chin->throat in az090 - OK;
shoulders - chest rings widen into a low sloped deltoid cap over the ribcage (2 spans x 4 faces) - OK; arms A-pose,
35 mm clear - OK; legs from a hip seat, groin blended (thigh probe 0.21 r) - OK; hands parts-library hand_three_finger
with claws - OK.
Residual (fix budget used): the ear root is a boxy neck with a flat back face (dark slab from back34) and the leaf is
slimmer than the sheet's cupped ear; the far wing edge-on from az135/225 reads as a plank on the back; the belly
colour border steps along quad edges; body slimmer / legs a bit longer than the sheet's chubby proportions.
