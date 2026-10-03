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
