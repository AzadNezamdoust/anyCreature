# giant (w4) build notes

Reference sheet present: blueprint.json is the traced target (not redrawn). Sheet vs brief: the sheet's fists hang to
z ~0.2 (ankle height) where the brief says "to the knees" -> sheet wins on shape. The sheet's top view shows the
arms swung forward in a crescent that the side and front views contradict -> side view wins (arms hang at the sides).

## Stage 1
- r01: 532 tris, IoU side/front/top 0.895/0.849/0.782, gates PASS. Critique: the head is a drum with a flat octagon
  disc for a face (az000, az090, hero) - reads as a cylinder, not a troll head. Diagnosis: R7-R9 use the torso PROF
  (round, as wide at the cranium as at the jaw) and R9 is capped flat. Fix: a head profile - wide jaw corners,
  narrow cranium - and slightly narrower head rings.
- r02: 532 tris, IoU unchanged (0.895/0.849/0.782). Result: head now a wedge with a wide jaw base - slightly better,
  still big and round-faced but that is stage-2 face work. Critique (next): the arms are thin posts next to the
  sheet's massive arms (az000, az180; front IoU 0.849, the sheet's forearm spans x 1.11-1.81). Diagnosis: ARM_RINGS
  hw/hd 0.20-0.31. Fix: thicken every arm ring ~15-20% (deltoid 0.34/0.40, forearm 0.35/0.33, fist 0.34/0.36).
- r03: 532 tris, IoU 0.892/0.871/0.798. Result: better - the arms now carry the mass of the sheet's arms and the
  fists read as clubs. Critique (next): the legs read as thin posts on small feet (az000, az045, az135) where the
  sheet has short, thick legs on big flat feet. Diagnosis: LEG_RINGS knee 0.28/0.36, ankle 0.24/0.29, foot 0.32/0.55.
  Fix: thicker knee (0.31/0.40) and ankle (0.28/0.34), a broader, longer foot (0.36/0.60).
- r04: 532 tris, IoU 0.894/0.868/0.801. Result: better - legs stand as short thick columns on broad feet.
  Critique: remaining problems are surface planes (flat chest front, disc face, no brow/jaw), which are stage-2 vertex
  work on the existing rings; the masses (hump over a low forward head, club arms to the ankles, short legs) read
  from every view. Fix: none to the base - lock as is (r05, with orbit).
- r05 LOCK: 268 verts, 266 faces, 532 tris, edge sha256 6c22ef566b929b71. IoU side/front/top 0.894/0.868/0.801
  (min 0.801, top: the sheet's crescent arms). Orbit advises az225/az315 close up (limbs fold into the body obliquely).

## Stage 2
- r01: 572 tris, min IoU vs s1 0.986, qa PASS (4 slivers, 0.7%). Topo: head loop behind the face, eye-socket inset.
  Result: the face now has a brow shelf, nose bridge, cheek and socket - reads as a heavy-browed head. Critique (next):
  the torso front and back are stacked equal horizontal bands (az000, az180) - the tube look; no pot belly, no waist
  taper under the hump. Diagnosis: R1-R3 front and back verts sit on the stage-1 sweep. Fix: belly bulge (R2 front
  forward/down, R1 front tucked under it) and a back taper (R2/R3 back-side verts in).
- r02: 572 tris, min IoU 0.986, qa PASS. Result: better - a low belly facet hangs over the tucked underbelly and the
  back narrows toward the belt (az000, az180). Critique (next): the hump is a round dome from the side (az090) where
  the sheet peaks at a crest over the shoulders. Diagnosis: R6 B1 sits on the sweep. Fix: raise R6 B1 0.06 (crest).
- r03 (final, orbit): 572 tris, min IoU vs s1 0.980, qa PASS. Result: slightly better - the hump has a crest in
  profile. Orbit still advises the obliques close up (arms against the body) - accepted: the sheet's arms hang there.

## Stage 3
- r01: 1504 tris, 7 colours. FAIL: belt 1 hit shell; slivers 2.8% (belt 26, loincloth 12). Critique: the belt's
  bottom face (2.5 cm deep over 26 cm segments) and the loincloth's 4.5 cm side walls over 80 cm edges are needles;
  the loincloth top sits on the belt's inner face so the belt is crossed twice. Diagnosis: belt offsets
  (+0.045/+0.07) and loincloth outline (5 pts, 4.5 cm thick, back face at yf-0.01). Fix: belt bottom-in +0.035,
  bottom-out +0.10; loincloth outline with mid-side points, 6 cm thick, hung from inside the belt's outer lip.
- r02: 1520 tris. Slivers PASS now (body 4 + loincloth 4). FAIL hit 1: the belt meets the front AND back flap, which
  are one object, so the belt is crossed in two patches per side (magenta at both flap roots, az000/back34 tech).
  Critique (look): the moss is a scatter of small hex nuts with bolt-head rocks (top, az180) - the sheet has one
  continuous moss mantle over hump and shoulders with a few flat stones. Fix: flaps as two objects (gate, mechanical)
  + the one look fix: fewer, larger, flatter, irregular 7-sided moss pads that overlap into a mantle, rocks flatter.
- r03: 1620 tris, 7 colours, all qa gates PASS (slivers: body 4, flaps 2+2). Result: better - the moss reads as a
  mantle over hump and shoulders (hero, az135 colour), flat stones on it; the hit is gone. Critique (next): the
  tusks, the face's defining troll cue, are two faint slits at the mouth (az000 colour). Diagnosis: tusk base 8x7 cm,
  tip only 10 cm proud and 25 cm up. Fix: a thick tusk (14x10 cm base) rising 32 cm and 16 cm proud, flaring out.
- r04 (final, orbit): 1620 tris (body 572), 7 colours, qa PASS. Result: better - two cream tusks stand proud of the
  jaw from front and 3/4 (az000, hero colour). Left as is: the hide reads darker than the sheet under the kit light
  (brief hexes kept), and the moss pads still show their hexagon rims from the top.

## Stage 4
- r01: all gates PASS except posed fold-overs: 9 tris (0.56% of tris, 0.45% of area) - 8 on the body, magenta in the
  armpit / inner shoulder (az000 tech), plus 1 moss tri. Diagnosis: the attack wind-up swings upperarm 115 deg on a
  shoulder whose skin only follows the upperarm bone, so the armpit faces fold over. Fix: raise 95 deg on the
  upperarm and shrug the clavicles 20 deg (clav.L +Z, clav.R -Z) so the shoulder mass rises as a block.
- r02: all gates PASS; fold-overs 4 (0.25% tris, 0.25% area). Result: better - attack f010 lifts both fists over the
  head with the shoulders shrugged, f020 slams them down in front; idle/move bend without collapse (the head/neck
  keeps its volume). Critique left: the armpit still carries the flagged triangles in the wind-up. r03 = final run
  with orbit + glbcheck, no change.
- r03 (final, orbit): unchanged program; all gates PASS, glbcheck OK (attack/idle/move). Orbit advises az180/az225
  hide the head behind the hump - by design (sunken head under the hump). --review packet built in review/.

Triangles: stage 1 532, stage 2 572, stage 3/4 1620 total (body 572). Rounds: s1 5 (lock r05), s2 3, s3 4, s4 3.
