# raven_wyvern (k3) build notes

Reference sheet present: blueprint.json traced from it (length 2.755 m vs brief 2.3 m; sheet wins on shape, logged).
Conflict log: the sheet's tail fin fans in both side and top views (a 3D fan); the brief lists the fin as a stage-3 piece but
also asks for a fin tip in the stage-1 silhouette, so the base ends in a flat spade blade and stage 3 adds fin plates.

## Stage 1
- r01: Critique: front/top views show the folded wings as thin sticks; the sheet's folded wing is a panel flaring out to x=0.34.
  Diagnosis: wing blade ring W2 is only 0.07 thick in x and sits at x 0.26-0.33. Fix: widen W2 to x 0.255-0.35 and flare its
  lower corner out (0.32). Result r01: 460 tris, IoU side .795 / front .731 / top .723.
  Result r02: panel reads a little in front view, IoU front .731 / top .728, 460 tris. Better.
- r02: Critique: side/front views read "crow": the folded wing's wrist sits flush with the back line, so the forelimb-wing
  cue is lost; the sheet's wrist knuckle stands above the shoulder beside the neck. Diagnosis: J elbowL/wristL rings at
  z 0.90/0.99. Fix: raise and push forward: elbow (0.24,-0.66,0.93), wrist (0.26,-0.70,1.06).
  Result r03: wrist now stands a little proud; IoU .798/.730/.733, 460 tris. Better, small.
- r03: Critique: front view reads as a narrow penguin torso with a gap to the wings; the sheet's chest fills out to the wing
  panels. Diagnosis: SECS 7-10 half widths .19-.22. Fix: widen to .20/.23/.235/.215 (wing inner face stays at x .255).
  Result r04: chest fills more of the front view; IoU .798/.737/.738, 460 tris. Better. The remaining gaps (horns, spines,
  hackles, fin fan, talons) are stage-3 pieces or stage-2 vertex moves; the body plan (2 legs, wing-forelimbs, long finned
  tail, S-neck) is in the base, so lock.
- r05: lock round with orbit, no geometry change.
Stage 1 locked at r05: 460 tris, edge sha256 d521877471e8fee4; min blueprint IoU 0.737 (front).

## Stage 2
- r01: 4 logged ops (drumstick loop, two hock loops, eye-socket inset), brow pushed out, bill base pinched, tarsus
  thickened, toes fanned, fin spade widened in plan. Result: 524 tris, IoU vs s1 min .94, FAIL slivers 20 (3.8%).
- r02: Critique: yellow needle triangles along the folded wing's long edges and the fin root (az090/back34 tech views).
  Diagnosis: wing tip ring W3 is 0.03 across against 0.25 blade edges; wrist back face 0.07 wide against a 0.6 m blade;
  fin-root section 16 is 0.06 tall. Fix: scale W3 (2,3,3), wrist rings x/y 1.4, section 16 (1.6,1,1.5).
  Result r02: seam broke (section-16 scale pivot had x>0, pulled seam verts off x=0). Fix r03: pivot on x=0.
  Result r03: slivers pass; IoU vs s1 az180 .886 FAIL (the rear view is small, so the widened fin spade dominates it).
- r04: Critique: rear silhouette drifts from the locked base. Diagnosis: fin tip x*6, fin x*2.5. Fix: x*3.5 and x*1.8.
  Result r04: all s2 gates PASS, 524 tris, min IoU vs s1 0.90 (az180). Stage 2 done (4 rounds).

## Stage 3
- r01: palette (7 colours, brief hexes), bill/tip/socket/shank/membrane borders on existing loops (A2 ring, A1 ring,
  hock loop, wing blade). Pieces: eye lens, horns, thumb claw + talons + hallux talon, 13 graded seam spines, 8 hackle tufts.
  Result r01: all s3 gates PASS, 1042 tris, 7 colours. Horns/spines/hackles move it from crow to drake.
- r02: Critique: the folded wing is a flat saturated purple slab from every side (az090/hero); the sheet's membrane is
  broken by dark finger spars. Diagnosis: no spar piece; the blade faces are too big to carry spars in paint.
  Fix: one dark finger spar from inside the wrist knuckle along the blade's leading-lower edge, ending in a free tip.
  Result r02: spar breaks the slab; FAIL slivers 22 (2.0%): the spar's 0.012 tip ring against a 0.36 m point.
- r03: Fix: spar gets a fourth ring and thicker radii (0.026 -> 0.016), tip 0.15 from the last ring.
  Result r03: all s3 gates PASS, 1102 tris, 7 colours. Stage 3 done (3 rounds).

## Stage 4
- r01: rig from J (spine/neck/head, 4 tail, bird leg thigh/shin/tarsus/toe, wing arm/hand), roll auto, heat skin,
  every piece bound with body= weights; idle 48f, move 33f, attack 40f, all loop.
  Result r01: all s4 gates PASS (hit 0, float 0, zfight 0, slivers 6, flips 0, drift 0). Posed checks: neck coils and
  lunges without collapse, hock folds the right way on the lifted leg, arm +X lifts the folded wing (mantle).
- r02: Critique: attack f20 (az090) the bill stabs straight down, so the lunge reads as a peck at its feet rather than
  a forward strike. Diagnosis: head -12 at f20 on top of neck0/neck1 +18/+14. Fix: head -4. Final round with orbit.
  Result r02: all s4 gates PASS, glbcheck OK (attack/idle/move). 1102 tris total. Review packet built.

## Triangles per stage
s1 460 (locked, edge d521877471e8fee4) | s2 524 | s3 1102 | s4 1102. Rounds: s1 5, s2 4, s3 3, s4 2.
Weaknesses seen in review/1_beauty.jpg: the folded wing is one flat purple slab with a single spar (no scalloped
membrane/finger rhythm); the fin is a solid spade, not the sheet's ribbed fan; the toes are a paddle with talons.

## Repair pass (NGO notes, K=1, R0=6; stage 1 locked, no unlock)
- r06 baseline s4 (kit 2026-09-28): all gates PASS; WARN clip 8 tris, 3.56% of surface (must-fix 0).
- r07 diagnosis (no fix; RW_DIAG probe of the kit's clip test per clip/frame): body clip is the WALK, not the mantle:
  move f1/f13-20/f33 the shoulder face (wing root vert 0.235,-0.514,0.665, heat weight 0.76 thigh) is shoved by the
  thigh swing into the blade face; plus 2 hackle tris at the throat (0.08,-1.06,0.96) in every clip.
- r08: Critique: pink clip on the flank behind the wing arm (az090 tech). Diagnosis: wing-root flank verts weighted to
  the thigh. Fix: pin_blade(): blade verts 100% to hand.L/R; thigh weight on the wing-root flank moved to chest.
  Result: clip 4 tris, 0.04% of surface (only the hackles, item 2); all s4 gates PASS, 1102 tris.
- r09 (s2, item 1): Critique: the blade's trailing edge is one straight line (no membrane bays). Diagnosis: B->tip
  segment has no verts on the edge. Fix: two logged cross loops on the blade (t .68 / .34 of edge 133->131), their
  bottom verts pulled up 0.035 (7% of blade height). Tried moving the outer ridge vert up/out for a thinner arm band
  and edge thickness: az180 IoU 0.878-0.896 (floor 0.9, the rear view was already at 0.90): thickening NOT done.
  Result: s2 PASS, IoU min 0.90, slivers 1.1%, 540 tris.
- r10 (s3, item 1): Critique: az090 the blade is a purple cape with one spar. Diagnosis: no arm band, one spar.
  Fix: blade faces above the outer-ridge line painted plumage; three finger spars fanning from the wrist knuckle,
  ring centres ray-cast onto the blade's outer face, 30% of the diameter sunk; thumb claw rebuilt 2x as a
  forward-down hook. Result: first try 54 slivers (spar rings twisted: around() switched frames on steep spars);
  fixed frame (up=X) and 6 rings -> slivers 6. But az090 read ~75% dark (band + fat spars).
- r11 (s3): Fix: band only from the wrist to the second cross loop (the rear membrane stays purple), spars 7 rings,
  radii .026->.015. Result: az090 dark arm over a purple membrane with three spars; s3 PASS, 1414 tris.
- r12 (s4): first try: claws 6 fold-overs (hook tip took neck/head weights from the nearest face) -> spars and
  thumb hook pinned 100% to the hand bone; then spar clip 12 tris: the front spar ran in front of the blade's
  leading edge, so its rays hit the flank. Fix: knuckle K (-0.62,1.0), front spar ends at (-0.34,0.36) on the
  trailing edge. Result: all s4 gates PASS, flips 0, clip 4 tris 0.04% (hackles only), 1414 tris.
- r13 (s3, item 2): Critique: close-up head: dozens of needle hackles splinter. Diagnosis: 8 tufts/side, tube flat .45,
  radii .035/.024 against 0.11-0.15 length. Fix: 6 wedge tufts/side, width .45 L, thickness .35 W, L .10-.18,
  root sunk .03, framed on the surface normal; dropped the under-jaw tuft that clipped when the head turned.
  Result: clumps, not needles (close_0); s3/s4 PASS, 1358 tris; clip 4 hackle tris 0.02%.
- r14 (s4, items 0+3 mantle): Critique: attack f20 the wings barely lift. Fix tries: arm X35 + arm Z40 (either
  sign): clip 4.6-17% (the stubby humerus pinches through the shoulder and the thumb into the coiled neck).
  Diagnosis: large arm rotations collapse the heat-weighted shoulder. Fix: arm X stays 22 (known clean); the
  mantle comes from the HAND bone (blade 100% hand): Z 45 outward, X 22 up, held f17-23; thumb hook pinned to
  the arm bone, hook tip pulled back. Result: attack f20 blades spread up and out beyond the body behind the
  head; all s4 PASS, flips 0, clip 4 tris 0.02% (hackles).
- r15 (s2, item 3 neck): Critique: az090 the neck runs straight from the chest to the skull. Fix: mid-neck ring (sec 6)
  back, skull/throat ring (sec 4) forward (y only), hackles follow via surf(). 0.08/0.03 gave az180 IoU 0.899;
  settled on 0.07/0.02: az180 0.900. Result: a concave throat under the head, a mild S; s4 PASS, clip 2 tris 0.08%.
  Partly done: the bend is mild because the rear view sits on the 0.9 floor.
- r16 (s2, item 4): Critique: az090 the tail keeps one section to a solid spade. Fix: taper rings 13-16 to 55%:
  slivers 32 (5.8%) and az180 IoU 0.897 (the fin-root ring was already widened 1.6x in s2 r02 to cure slivers);
  settled on a taper to 80% at the fin root. Fin trailing edge: the two verts between top/middle/bottom pulled
  forward 0.04 (10% of the fin length) -> a notched fan. Result: s2 PASS, IoU min 0.90, slivers 1.1%. Taper partly done.
- r17 (s3, item 4): three dark fin ribs (4 rings, ray-cast onto the fin side face, 30% sunk) fanning from the fin
  root to the trailing-edge points; the fin's front third painted blue-black. Result: s3 PASS, 1538 tris.
- r18 (s3+s4, item 5): Critique: close-ups: tiny talons on a paddle, the eye a small diamond. Fix: talons 2x as
  3-ring hooks curling down (plus the hallux talon); eye a 6-sided lens 0.08 x 0.06 (1.3x wider, depth 0.024),
  in the bill-black socket. Toe split into three points NOT done: the toe paddle's front face has only two
  corner columns, a third point needs a loop through the foot. Result: all s4 PASS, 1610 tris, clip 2 tris.
- r19 (s3, should-fix): dorsal spine tips lean +-10 deg (sin pattern). s4 PASS.
- r20 final: s4 with orbit: every gate PASS (hit 0, float 0, zfight 0, slivers 6 = 0.4%, flips 0, drift 0, lock OK,
  s2 IoU min 0.90 az180), glbcheck OK; clip warning 2 hackle tris, 0.08% of surface. --review and --compare rebuilt.
  Triangles: s1 460 (locked) | s2 ~544 | s3/s4 1610. Rounds this pass: r06-r20 (15 runs incl. 1 diagnostic).
  Checked in review/ (idle f1): dark arm + purple membrane + 3 spars + thumb hook (az090), wedge hackles (head),
  hooked talons and bigger eye (close-ups), mantle spread (4_posed attack_f020).
