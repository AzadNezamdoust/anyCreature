# bear (t7) build notes

No reference/: stage 0 is mine. blueprint.json drawn from the brief (1.0 m hump, 1.7 m long, 0.7 m wide).

## Stage 1
- r1: 524 tris, gates PASS, IoU side/front/top 0.901/0.933/0.961. Critique: side view (az090) back line is nearly flat, so the
  shoulder hump (the identity cue) does not read; it looks like a generic quadruped. Diagnosis: ring tops R8 1.00 -> R9 0.98 -> R10 0.91
  fall too gently and the neck ring R6 (0.87) is too close to the hump. Fix: drop R9/R10/R11 tops and R6 so the hump is a distinct peak.
- r2: 524 tris, side IoU 0.878. Result: barely visible; the back still reads flat in az090 because the head top (0.77) and neck (0.84)
  sit too close to the hump (1.0). Critique: the hump has no steep front. Diagnosis: HZ = -0.04 keeps the head high; R6 top 0.84.
  Fix: carry the head lower (HZ -0.04 -> -0.09) and drop the neck ring R6 top to 0.79, so the neck rises steeply into the hump.
- r3: 524 tris, side IoU 0.841 (the blueprint still had the old, higher head). Result: better, the neck now climbs into the hump and
  the head hangs low. Critique: hero/az045 - the legs are thin planks for a bear (0.17 m wide under a 0.66 m body); the brief asks for
  thick legs. Diagnosis: FORE/HIND half-widths 0.085/0.078/0.066. Fix: widen every leg section ~20% (upper 0.10, forearm 0.09,
  wrist 0.075, paws 0.095). Blueprint head redrawn 5 cm lower to match the low carriage (target change, not a model change).
- r4: 524 tris, IoU 0.857/0.917/0.952. Result: better, legs read as pillars now. Critique: top/hero - the muzzle is a thin long
  tube (0.15 m wide) on a head barely wider than the neck: dog/pig, not the broad dished bear face. Diagnosis: rings R0-R2 half
  widths 0.075-0.105 and R3-R5 cheeks 0.17-0.19. Fix: broaden the muzzle (0.085-0.12) and cheeks (0.195-0.215), deepen the brow step.
- r5: 524 tris, IoU 0.855/0.917/0.943. Result: better, a broad head with a clear stop and brow step. Critique: top view - a bottle
  neck: the head joins the shoulders through a pinch (R5 0.19, R6 0.24 half width) where a bear has a thick neck as wide as the skull.
  Diagnosis: rings R5/R6 side and upper verts. Fix: widen R5 to 0.205 and R6 to 0.27 (upper 0.15/0.20), deepen the throat.
- r6: 524 tris, IoU 0.854/0.917/0.941. Result: slightly better, the neck no longer pinches in hero. Critique: az090 - the hind leg is a
  copy of the foreleg, a straight column: no haunch, no heel behind the hock, no long plantigrade sole. Diagnosis: HIND sections keep
  cy near 0.45-0.52 with even depths. Fix: deeper thigh (d 0.15), shin and hock stepping back (cy 0.51 -> 0.55), sole running forward.
- r7: 524 tris, IoU 0.853/0.917/0.939. Result: better, the hind shin angles back to a heel and the sole runs forward. Critique: az090 -
  the underline is one flat plank from chest to groin: no deep chest, no belly tuck, so the body reads as a crate. Diagnosis: ring
  bottoms R7-R11 all 0.39-0.45 with low verts at 0.47-0.50. Fix: deepen the chest (R7-R9 bottoms 0.37-0.385) and tuck R10/R11 (0.49/0.47).
- r8: 524 tris, IoU 0.842/0.916/0.939. Result: better, a deeper chest and a visible tuck in az090 wire. Critique: top view - a bottle:
  the flank is one straight wall at x 0.33 from shoulder to hip, so there is no shoulder mass, waist or haunch. Diagnosis: the side
  verts of R8-R12 all sit at x 0.31-0.33. Fix: shoulder R8 and haunch R12 out to 0.34/0.335, waist R10 in to 0.29 (upper 0.22).
- r9: 524 tris, IoU 0.842/0.926/0.921. Result: mixed - hero now shows a shoulder mass and a haunch, but the top view overshoots into
  a peanut/gourd with a wasp waist, wrong for a heavy bear. Diagnosis: R10 side x 0.29 is 0.05 inside both neighbours. Fix: ease the
  waist to 0.315 (upper 0.23) so the top view keeps a gentle shoulder-waist-haunch line.
- r10: 524 tris, IoU 0.842/0.926/0.932. Result: better, top view is a heavy barrel with soft shoulder/haunch. Critique: hero/az045 -
  the ears are thin slanted blades growing out of the upper cheek, not round ears on the top corners of the skull. Diagnosis: ear()
  offsets the cheek face along its normal. Fix: place the ear's first ring explicitly on top of the skull corner (0.14-0.23 x,
  0.07 m deep, z ~0.78) and round it with a small tip ring.
- r11: 524 tris, IoU 0.840/0.926/0.933. Result: better placed (top corners, facing forward) but overshot: tall posts ~0.11 m above
  the skull, reading as horns/rabbit. Critique: az045/hero ears. Diagnosis: ear ring 1 at z 0.77-0.80 plus a 0.04 tip. Fix: lower
  ring 1 to z 0.735-0.765, widen it front-to-back, flatten the tip ring (scale z 0.5, +0.028) for a low round ear.
- r12: 524 tris, IoU 0.842/0.926/0.932. Result: better, low blocky round ears on the skull corners. It reads as a bear from every
  view (hump highest, head low, heavy barrel, pillar legs). Remaining: flank planes are large and flat; left for stage 2.
- r13: lock round (orbit on). Minimum stage-1 blueprint IoU over the rounds: 0.840 (side, r11).
Stage 1 locked at r13: 524 tris, edge sha256 becc00d675549d95.

## Stage 2
- r1: 540 tris, all gates PASS, IoU vs s1 min 1.0. Fix: eye socket = inset in the brow-cheek face (R3-R4 upper-side), floor pushed
  0.014 in; kept as a valley via META keep_valleys. Critique after: az045/hero - the brow does not overhang the socket; the forehead
  meets the stop in a flat slope. Diagnosis: R3 top/upper verts sit straight above the stop ring.
- r2 fix: pull the R3 brow row (top + upper verts) 0.018 forward and 0.012 up so it overhangs the eye and the stop reads as a step.
- r2: 540 tris, all gates PASS (orbit on), IoU vs s1 min 0.997. Result: better, a small brow shelf over the socket in az045/hero.
  Stage 2 closed here (the base reads; remaining weakness is the large flat flank planes, which the lock fixes).

## Stage 3
- r1 plan: paint 7 regions (fur, dark lower legs below the z 0.24 leg ring, pale muzzle ahead of the stop ring R2, black nose cap,
  lighter chest plane, claw, eye); pieces: hex eye lenses proud of the socket, a nose-pad block, four claws per paw.
- r1: 808 tris, 7 colours, all gates PASS. Result: reads as a brown bear (pale muzzle, black nose block, dark lower legs on the
  z 0.24 ring). Critique: hero/az000 colour - the claws are specks (0.026 x 0.024 x 0.04 m); STYLE says small things are few and bold.
  Diagnosis: _claw() sizes. Fix: three larger claws per paw (0.036 wide, 0.03 tall, 0.06 long) spaced across the paw front.
- r2: 752 tris, all gates PASS. Result: better, three bold dark claws read per paw in hero. Critique: hero/az000 colour - no lighter
  chest plane shows at all. Diagnosis: body_rule's chest test (n.y < -0.35, y -0.40..-0.20) matches almost no face: the chest faces
  between R5 and R7 face down/out more than forward. Fix: chest = faces between rings R5 and R7 (y -0.47..-0.24), z < 0.66,
  |x| < 0.22, n.y < -0.1, so the border runs on the R5 and R7 loops.
- r3: 752 tris, 7 colours, all gates PASS (orbit on). Result: the chest faces now take the lighter colour, but with the head carried
  low it is mostly hidden from the front; only a hint shows in 3/4 views. Accepted; stage 3 closed.

## Stage 4
- r1 plan: 12-bone rig (hips/spine/chest/neck/head/tail + 3-bone legs, roll auto) on J; skin; all pieces bind(body=) so they
  cannot drift; idle 48f breathe+sniff, move 33f diagonal walk, attack 40f lunge + left paw swipe.
- r1: all gates PASS (0 flips, 0 drift, glbcheck OK). Posed side renders: no neck or shoulder collapse; walk swings the diagonal
  pairs the right way (+X = tip forward with roll auto). Critique: attack f010/f020 az090 - the "swipe" never lifts the paw: the
  left foreleg only leans forward with the paw still on the ground, so it reads as a stumble, not a strike. Diagnosis: upperarm.L
  32 deg with forearm.L -25 folds the paw back down. Fix: raise upperarm.L to 50 deg with forearm.L +15 (reach), then swing it
  down-and-in (-10, 0, 18) at f20; chest pitch -10 on the wind-up.
- r2 (final, orbit on): all gates PASS; 0 fold-overs, 0 drift, glbcheck OK. Result: better, attack f010 now lifts the left paw
  forward and high into a strike and f020 swings it down-in. Residual: at the top of the wind-up the raised forearm passes close
  in front of the cheek (side view overlap), and the chest pitch drops the head slightly.

Triangles: stage 1 524, stage 2 540, stage 3/4 752 total (body 540 + eyes, nose block, 12 claws).
