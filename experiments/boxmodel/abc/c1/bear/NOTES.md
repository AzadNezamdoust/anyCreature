# bear (c1, carve + detail)

Owner verdict on the prototype: carved overall shape good, lacks detail. This pass keeps the carved base and adds detail.

## Stage 1
- Kept the prototype lock (carve_base defaults, 1094 tris, edge hash 7ec16f7b...). Why no re-lock: the quadruped hull already
  separates the four legs with clear gaps in front and side views; the missing ears are added as stage-3 pieces (the brief's
  own route for "ears where the hull lacks them"), and face planes are vertex moves, which stage 2 allows freely.

## Stage 2
- r01: Critique: the face is a smooth hull wedge: no eye socket, no brow, no stop (hero, az090). Diagnosis: the carve only
  sees silhouettes, so the face front is one blurred slope (seam verts y -0.72..-0.65). Fix: inset socket in the eye face
  (0.114, -0.656, 0.560) sunk 0.010; socket-top vert out/forward/up into a brow; forehead forward 0.014; stop verts down
  0.018-0.020; muzzle top flattened. Result: gates PASS, IoU min 0.997, 1106 tris; socket and stop read in hero (small).
- r02: Critique: colour borders on the prototype were saw-tooth (dark legs, muzzle) because colour followed noisy triangles.
  Diagnosis: no edge ran along any colour border in the decimated hull. Fix: planar border loops (bisect_plane inside
  k.topo 'loop', new verts on base edges only, dist 0.012 so no sliver cuts): legs z 0.30, muzzle plane, bib planes.
  Result: lock collapse PASS, IoU 0.997, slivers 1.3%, 1242 tris.
- (later stage-2 tweaks were driven from stage-3 renders, logged under s3 r08-r10.)

## Stage 3 (rounds s3_r05..r10; r01-r04 were the prototype's)
- r05: pieces: eye domes in the socket, round cup ears seated by a ray on the skull, nose pad on the snout tip, 5 graded
  hooked claws per paw rooted by rays, stub tail; paint by rules on the stage-2 loops with colour_from_sheet's clusters
  mapped to the brief roles (nearest sheet colour per role, brief hex where none is near: nose/claw/eye). 1720 tris.
  Result: ears read as thin fins in az090, socket paint a goggle ring.
- r06: Critique: ears tiny fins (az090). Fix: r 0.046->0.056, thicker 0.034, turned out 0.6. Result: ears read front+side.
- r07: Critique: dark inner ear read as a second eye (hero); palette dull. Fix: ear all fur (cup reads by shading),
  chroma 1.35, ears turned 0.45. Result: better; palette fur #6e5240, dark #403832, muzzle #b29780.
- r08: Critique: pale muzzle a thin band in az090. Fix: muzzle plane back 0.025, bib V wider. Result: WORSE: fang-shaped
  saw-tooth border, because faces outside the cut box crossed the plane and were painted by centroid.
- r09: Fix: region test by the face's VERTICES (all on the region's side within the cut tolerance), bigger cut boxes, a
  third bib cut (top edge). Result: borders clean in every view; 1774 tris.
- r10: Critique: eye a dark slit, pale mask up between the eyes, bib a pale collar across the shoulders (beauty).
  Diagnosis: lens front sat below the sunk socket rim; muzzle/bib planes too generous. Fix: lens raised 0.009 along the
  socket normal, muzzle plane forward 0.01, bib V x 0.13 at z 0.44, top 0.45. Result: dot eyes read in front/hero/side,
  muzzle stops under the eyes, a V bib under the chin. 1750 tris. All gates PASS.

## Stage 4
- r03: k3-style rig from J, skin, every piece bound with body= weights. All gates PASS, drift 0, flips 0.
- r04 final (orbit + glbcheck): all gates PASS; hit 0, float 0, z-fight 0, slivers 12 (0.7%), flips 0.00%/0.00% area,
  drift 0, lock PASS (edge hash 7ec16f7b...), IoU min 0.997, glbcheck OK. Orbit advisories: head merged az000, hidden
  az180 (same as k3). Review packet and side_by_side rebuilt.

## Triangles per stage
s1 1094 | s2 1242 | s3 1750 (body 1242 + eyes, ears, nose, claws, tail) | s4 1750.

## Remaining weaknesses
- Head still merges with the body in the front view; the stop/brow are subtle at game distance.
- Hind legs are hull pillars (no hock/heel shape); paws are blobby boots under the claws.
- Palette from the sheet is slightly grey; dark legs (#403832) are cooler than the brief's warm dark brown.

## Team repair pass (review/ad_notes_team.md; R0 = 11; stage 1 untouched, no unlock item)
- r11 baseline (s4): all gates PASS; nothing for item 0.
- r12-13 (s2, must-fix 1): Critique: back/flank/rump a crumpled hull (back34, az090). Diagnosis: decimated
  visual-hull triangles each tilted a little differently. Fix: `facet()`: torso faces (z > 0.33, y > -0.45) clustered
  into 14 planes (normal + position k-means), each vertex moved to the least-squares meet of its regions' planes
  (pull-back 0.03, cap 0.03 m, moves shortened where a triangle would go under 8 deg), two passes. r12 (K16, one
  pass) too weak; r13 first try 2.8% slivers -> added the needle guard. Result: big facets on flank/back, IoU 0.973, slivers 0.9%.
- r14-15 (s2, must-fix 2): Critique: hind leg a vertical slab (az090). Diagnosis: the outer rear of the leg is two
  tall triangles from rump to floor; no vertex to bend. Fix: two logged loops on the hind leg (z 0.37 hock, z 0.19
  shin), hock ring rear +0.065 y, shin ring rear -0.05 y, toes forward 0.045, foot top flattened. Result: a hock
  bulge and angled lower leg in az090; the leg loop at z 0.30 now cuts the rear leg completely (border straight).
- r16 (s3, must-fix 3): Critique: dark socks grey (#403832). Fix: dark = brief #4a3222. Border: straight z 0.30 on
  all four legs (the r14 loops split the tall rear faces, so the z 0.30 loop now runs all the way round). 6 colours.
- r17-18 (s2, must-fix 4): Critique: front leg one block with the chest; armpit slivers. Fix: chest floor up 0.03,
  armpit verts in 0.02, brisket back 0.035, shoulder plane out 0.012; leg loop no longer cuts the raised chest floor
  (the horizontal armpit slivers). Floor +0.05 self-intersected (r18 first try) -> 0.03. Result: a cleft between
  the legs in hero, no armpit yellow in az000; slivers 0.7%.
- r19-20 (s4, must-fix 5): Critique: attack frames looked idle. Fix: lunge spine loc forward 0.10-0.13 / down,
  head up, left paw raised (upperarm 40, forearm 25) and swept across (Z +10 -> -14), chest roll 8 (right shoulder
  drops), thighs and right arm back -13..-17 so planted feet stay. r19 (arm 62 deg) folded the chest skin (0.98%
  FAIL) -> r20 gentler: fold-overs 0.41%/0.19% PASS. Paw reaches ~0.3 m, not the asked 0.45 (skin folds beyond).
- r21 final (orbit + glbcheck): all gates PASS; hit 0, float 0, z-fight 0, slivers 10 (0.5%), flips 0.41% tris /
  0.19% area, drift 0, lock PASS (stage 1 untouched), IoU min 0.963, glbcheck OK; 1938 tris. Review packet and
  side_by_side rebuilt. Should-fix list not attempted. Remaining: the raised forearm in attack stretches the chest
  skin into a broad flap (auto weights); paw height ~0.3 m rather than 0.45.

## Team repair pass, second pass (review/verify_team.json: items 1, 2, 5 PARTLY, 4 NOT; R0 = 22; stage 1 untouched)
- r22 baseline (s4): all gates PASS.
- r23-24 (s2, item 1): Critique: flank/back still speckled (verifier). Diagnosis, measured with `speckle()` (share
  of torso edge length by dihedral): flat 33% / speckle (4-18 deg) 37% after the first pass; the planes were refit
  from a new clustering only twice, and results changed from run to run (set order in the needle guard, k-means
  seeds on an unsorted face list). Tried and dropped: fewer bigger planes (K 10, deeper creases, r23), bilateral
  normal denoise (no gain, IoU 0.92), fixed-label refit (cap blocks it). Kept: 12 facet passes at lam 0.002, cap
  0.02, deterministic order, and a guard that undoes any move making two faces cross. Result: flat 46% / speckle
  29%; az090 and back34 flank read as large planes. Still triangles in the wire (the lock forbids dissolving edges).
- r25 (s2, item 2): Critique: stepped rear edge but the shin a vertical slab. Diagnosis: only the rear edge moved; the
  reference's angle is at the FRONT (knee forward, ankle back, foot out). Fix: shin front edge back up to 0.06 at
  the ankle, fading to the hock loop (0.08 crossed faces). Result: thigh tapers to an ankle, hock point behind,
  foot sticks out forward.
- r26 (s2, item 4): Critique: legs flush with the chest. Diagnosis: chest front and leg front were one sheet of
  triangles from breastbone to outer leg, and the raised chest floor crammed its vertices into pleats. Fix: a
  vertical loop at x 0.10 (sunk 0.02: the armpit line), a loop round the leg at z 0.355 (ring out x1.06), the leg
  below it narrowed about its axis x0.84 down to the wrist, chest-floor raise removed. Tried and dropped: removing
  the armpit/brisket moves (step lost), flattening the brisket (more slivers). Result: shoulder shelf over a
  narrower column in az000/hero, clean brisket band, slivers 1.0% at s2.
- r27 (s4): gates PASS with the new stage 2; fold-overs 0.10%.
- r28 (s4, item 5): Critique: paw low, head not raised. Diagnosis: the arm cannot go higher without folding the
  chest skin, so the body has to bring it up. Fix: the spine rears 18 deg about the pelvis at f010 (thighs counter
  it, hind feet planted), 11 deg at f020 with the paw swept across (Z -16) and the chest rolled. Arm 46-56 deg
  failed or neared the fold gate (0.63% / 0.43% area), kept 40. Result: head and chest up, both front paws off the
  ground at f010, left paw across the chest at f020; fold-overs 0.10% / 0.20% area.
- r29 final (orbit + glbcheck): all gates PASS; hit 0, float 0, z-fight 0, slivers 16 (0.8%), flips 0.10% tris /
  0.20% area, drift 0, lock PASS (stage 1 untouched), IoU min 0.944, glbcheck OK. Warnings: 4 stretch (2.38x), 9
  clip triangles (0.12%) in attack. Orbit advisories unchanged (head merged az000, hidden az180). Review packet and
  side_by_side rebuilt. Remaining: torso wire is still the hull's triangles (planes by shading only); the front
  leg's inner seam with the chest is a step, not a full gap; attack paw reaches chest height by rearing, arm 40 deg.
