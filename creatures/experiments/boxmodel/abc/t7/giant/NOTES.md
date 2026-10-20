# giant (t7) — build notes

No reference/ folder: stage 0 blueprint written by hand (hunched troll, 4.0 m tall, 2.44 m long, 3.96 m across fists).

## Stage 1
- r01 — Critique: 6 self-intersecting face pairs; side view reads as a trunk: the head is a long tapering tube with no nape dip, and the hump does not rise above it. Front belly is one flat crate plane. Diagnosis: deltoid ring A1 inner verts sit inside the socket (x 1.105 vs socket 1.12) and the upper arm grazes R3/R4 (w 1.08/1.12); R7-R10 back seam runs straight from hump to brow; front ring verts P1 use ff 0.68 (flat front). Fix: (primary) arm root: A1 out to x 1.40, rib rings narrowed to w 1.0/1.02. Result: see r02. 502 tris.
  Result r02: gates PASS (0 intersections), 502 tris. Better; IoU side/front/top 0.918/0.918/0.888.
- r02 — Critique: az090 still reads as a trunk: head+neck is a 1.1 m horizontal sausage (nape -0.38 to face -1.46) at hump height; front view shows a flat coat-hanger shoulder shelf. Diagnosis: R7-R10 span 1.1 m in y and sit at z 2.86-3.68; R6 side vertex at z 3.51 level with the deltoid top. Fix: (primary) head shortened to 0.75 m and dropped 0.15 m in front of the chest (R7-R10 re-placed, nape dip at z 3.52 under the hump); (secondary) R6 lifted 0.12 so the trapezius slopes to the deltoid; torso sides tapered (R1 0.92, R3/R4 0.98).
  Result r03: head now hangs in front of the chest under the hump (better silhouette), but 2 intersecting pairs; IoU 0.891/0.904/0.897. 502 tris.
- r03 — Critique: 2 self-intersections under the chin; front view shows the face cap as a small hexagon inside a hood rim. Diagnosis (debug BVH script): R5-R6 front band hits R6-R7 band at (0.44,-0.7,3.07): the front seam climbs R4 2.80 -> R5/R6 3.00 then drops R7 2.90 -> R8 2.74, folding the throat. Fix: front seam made monotonic (R5 F z 2.90, R6 2.88, R7 2.80, R8 2.72) with R6/R7 ff 0.55/0.6; (secondary) face ring R10 widened 0.30 -> 0.36 so the face fills the head front.
  Result r04: still 2 hits, now R5-R6 front band vs R7-R8 side band; IoU 0.889/0.905/0.895.
- r04 — Critique: same under-chin intersection. Diagnosis: each ring's front seam vertex must lie ahead of the previous ring's plane; R7 F sat 0.016 BEHIND the 45-degree R6 plane and R8 F behind R7, so the throat folded back into the chest shelf. Fix: neck/head rings re-planned so the planes steepen progressively (R6 45, R7 ~49, R8 ~64, R9 ~73 deg, R10 vertical) and every front seam advances ahead of the previous plane (R7 F -1.00, R8 -1.14, R9 -1.28, R10 -1.40); head height trimmed to 0.8 m (1:5).
  Result r05: gates PASS, 0 hits, 502 tris; IoU 0.889/0.904/0.896. Head hangs low in front of the hump; reads as a hunched brute.
- r05 — Critique: az000: the shoulders read as a flat coat-hanger shelf with a dark underside at the arm root; az180: the back is one flat crate plane. Diagnosis: deltoid ring A1 tilted 50 deg with depth 0.46 overhangs the narrower upper arm (dark down-facing band R4->A1 inner verts); back verts P3 use kb 0.86 / bb 0.68 (square back). Fix: (primary) A1 re-tilted to 35 deg and lowered to z 3.02 so the deltoid rolls into the arm; (secondary) back rounded (R3-R6 kb 0.8, bb 0.55) and the pot belly pushed forward (R1 F -0.86, R2 F -1.08).
  Result r06: PASS, 502 tris; IoU 0.88/0.907/0.866. Back now rounded (better); belly bulges in az090. Shelf still there.
- r06 — Critique: az000 top line is still one straight slope from the hump to the arm (a yoke, no deltoid). Diagnosis: A1's outer-top vertex (z 3.23) sits below the R6 side vertex (3.64), so the silhouette is the straight R6->A1 edge; no dip at the R5 side vertex (1.08, 3.30). Fix: deltoid A1 raised and enlarged (c z 3.14, tilt 42, a 0.40) so its top (z 3.41) rises above the R5 dip: trapezius - dip - deltoid ball.
  Result r07: worse: the deltoid tip now turns UP at the outer end (a horn/wing tip in az000). 502 tris; IoU 0.88/0.90/0.866.
- r07 — Critique: az000 shoulder line rises toward the arm tip (wing); it should fall away from the hump arch in a convex slope (gorilla shoulders). Diagnosis: the hump arch (R6 side x 0.95, z 3.64) is narrower than the arm root, and A1's outer vertex at z 3.44 is nearly level with it. Fix: R6 widened to w 1.10 so the arch reaches the arm root, and A1 lowered/flattened (c z 3.02, tilt 30, a 0.38): top outer vertex z 3.21, slope 0.43 m down over 0.67 m.
  Result r08: better: the shoulder line now falls from the hump arch to the arm in az000 (no wing tip); hero reads as a hunched troll (hump over a low head, pot belly, fists at the knees, short legs). 502 tris; IoU 0.88/0.897/0.87 (min 0.87).
- r09 — lock round (orbit on). Remaining for stage 2: the face is a flat cap on a tube end (no brow, jaw or nose planes); chest-to-shoulder underside reads as a dark wedge in az000.
  Result r09: LOCKED, 253 verts / 502 tris, edge sha256 65f9f1732562ec9b; orbit rc=0 (holds, no collapse). Min blueprint IoU over stage 1 = 0.866 (top, r06/r07).

## Stage 2
- r01 — Critique (from the lock): face is a flat cap on a tube end (no brow, socket, jaw). Diagnosis: R10 cap pentagon is planar, R9-R10 band has no loop to hold an eye. Fix: one head loop behind the face (t 0.4), an eye-socket inset in the upper-side face quad, brow/jaw/cheek vertex moves (brow +0.09 forward, underbite chin +0.09 forward), hump back plane flattened.
  Result r01: all gates PASS; 534 tris; IoU vs stage 1 min 0.988; slivers 6 (1.1%) at the neck-chest underside and ankles. Eye socket reads as a dark notch under a forward brow in hero; jaw juts. Better.
- r02 — final stage-2 round with the orbit on; no geometry change (remaining face read is carried by stage-3 brow, eyes, nose, tusks).
  Result r02: orbit rc=0 (advisories only: az225/az315 outline 'blob', limbs fold into the body from the rear obliques).

## Stage 3
- r01 — pieces: amber eyes with dark pupils in the sockets, dark scowl brow, nose wedge, cream tusks from the lower jaw, 2 moss clumps + 2 flat rocks bedded on hump/shoulders, leather belt + loincloth, 4 fingers per fist (knuckle row) with stone nails, 3 stone toenails per foot. Paint: hide, dark saddle/fists/feet, stone pot belly. Result: all gates PASS, 1266 tris, 7 colours.
- r02 — Critique: az000 the two moss clumps on the hump top read as bear ears. Diagnosis: moss_a at (0.55, 0.45) sits on the hump crown, symmetric. Fix: moss_a moved down the back (0.50, 0.76), rock_a to the crown near the seam (0.15, 0.30) so the top reads as a rock pile. Final stage-3 round with orbit.
  Result r02: PASS, 1266 tris, 7 colours; orbit advisories only (rear obliques 'blob').

## Stage 4
- r01 — rig from J (hips, spine, chest, neck, head, clavicle/upperarm/forearm/hand, thigh/shin/foot; roll auto), skin, body= binds, loincloth rigid to hips; clips idle 1-48, move 1-33, attack 1-40. Result: all gates PASS except drift: 3 shells (rock_b x2 on the deltoids, loincloth). Flips 0.32% tris / 0.39% area, z-fight 2, slivers 0.5%.
- r02 — Critique: drift. Diagnosis: rock_b sits on the deltoid, where the 120-degree overhead swing moves the skin under a rigid slab; the loincloth is seated on the belly but rigid to hips while the skin under it follows the thighs. Fix: rock_b moved onto the hump (0.72, 0.32); loincloth bound with body= weights. Final round with orbit + glbcheck.
  (stage-3 r03: re-run of the stage-3 gates after the rock_b move, no-orbit; PASS 1266 tris, 7 colours.)
  Result r02: ALL stage-4 gates PASS: hit 0, float 0, z-fight 2, slivers 6 (0.5%), flips 4 (0.32% tris / 0.39% area), drift 0, lock PASS, glbcheck OK. Posed wire: neck holds; the attack wind-up (upperarm 120 deg) stretches the deltoid/armpit into long facets but does not collapse. Orbit advises head hidden from az180/az225 (by design: sunk head under the hump).

Triangles: stage 1 502, stage 2 534, stage 3/4 total 1266.
