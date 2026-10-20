# wolf (w4) build notes

Reference sheet present: blueprint.json kept as traced; marks added (eye, shoulder, elbow, wrist, hip, knee, hock).
Section choice: 6-vertex half rings (10-sided full) so the ear and the legs extrude from quads clear of the seam;
the dorsal pair of quads is kept near-planar so the back reads as one plane.

## Stage 1
- r01: first loft (19 rings, nose to tail tip) + 2 legs + ear. 584 tris, IoU side/front/top 0.842/0.874/0.884. Reads as a canine already.
  Critique: the tail is a straight stick angled back (side view); the reference hangs it near-vertical off the rump and sweeps back only at the bottom.
  Diagnosis: tail rings 14-18 (tsec centres) run on one diagonal. Fix: re-path the tail centres (0.425,0.49)->(0.452,0.36)->(0.51,0.25)->(0.595,0.198)->tip.
  Result r02: better; the tail hangs low behind the thigh then sweeps back. IoU 0.921/0.867/0.879, 584 tris.
- r02 critique: front and top views, the head and neck ruff are too narrow (0.14-0.18 vs the sheet's 0.19); the wolf reads as a greyhound from the front.
  Diagnosis: ring 4 v3 (cheek), rings 5-6 v2/v3 (neck ruff), ring 7 v2 (shoulder). Fix: widen them to 0.165 / 0.16-0.19 / 0.178-0.192 / 0.175.
  Result r03: front IoU 0.883 (from 0.867); the ruff now fills the front silhouette. 584 tris.
- r03 critique: top and front views, the skull is a narrow spike: the brow and cheeks are 0.10-0.12 half-width, so the head reads as a rat's, not a wolf's broad wedge.
  Diagnosis: rings 2-4 v2/v3 and the ear taper centres. Fix: brow 0.112, cheek 0.137, stop 0.076/0.092, skull 0.13; ear centres out 6 mm.
  Result r04: better; the head is a broad wedge from the top, front IoU 0.889, top 0.884. 584 tris.
- r04 critique: front view (az000), the chest front is one flat plate from throat to brisket; the sheet has a keel that points forward (the bib V).
  Diagnosis: rings 5-6 v4 sit level with the bottom seam vertex. Fix: pull v4 back and up (0.118,-0.355,0.53) and (0.115,-0.405,0.675), push the ring-6 seam vertex forward, so the brisket is a V keel.
  Result r05: better; az000 now shows a forward keel instead of a plate, side IoU 0.919, 584 tris.
- r06: lock round. The base reads as a wolf from every view (wedge head, tall ears, ruff, deep chest and tuck-up, low brush tail). Remaining shape work (muzzle planes, brow, eye socket) goes to stage 2.
LOCKED at r06: 294 verts, 288 faces, 584 tris, edge sha256 2267bf80e850077a. Min blueprint IoU at lock 0.884 (top); side 0.919, front 0.889.

## Stage 2
- r01 critique: the face is blank (hero, az045): no nose block, no eye, no brow. Diagnosis: the head rings carry only the wedge. Fix: loop round the muzzle behind the nose pad (topo #1), inset eye socket on the side-of-face quad (topo #2, kept as a valley), brow corner pushed forward-out 12 mm.
  Result: better; socket and nose step read in the close views. 620 tris, IoU vs s1 0.996, slivers 1.6%.
- r02 critique: hero view, the muzzle is a soft twisted tube and the tail tip shows needle triangles (yellow in the tech map). Diagnosis: the muzzle's v2/v3 verts are not coplanar; the last tail ring is 12 mm wide. Fix: flatten the muzzle side and bridge planes; open the tail tip ring x1.9.
  Attempt 1 failed the lock: scaling the tip about its centroid pushed the seam vertices to x<0 (mirror merged them). Re-run with the pivot on the seam.
  Result r02: better; the muzzle reads as a tapered box with a flat bridge; tail slivers 0 (0.0%). 620 tris, IoU vs s1 0.993.
- r03 critique: hero close-up, the eye socket barely dents the face, so a lens would sit on a flat cheek. Diagnosis: the inset (topo #2) has depth 0. Fix: sink the inner eye quad 14 mm along its normal. Final stage-2 round, with orbit.
  Result r03: better; the socket reads as a dent under the brow. 620 tris, IoU vs s1 0.993, orbit holds.

## Stage 3
- r01: paint 6 colours (grey, saddle, tan, cream, amber, black) on edges placed in stage 1/2 (nose loop, v3 lip line, v1 saddle line, leg levels); pieces: eye lenses, neck ruff clumps, cream bib clumps, dark tail-brush blade, toe claws.
  Result r01: FAIL float (2 ruff shells) and the ruff reads as thorns standing off the head and neck (hero, az000); the whole muzzle front is black.
- r02 critique: hero view, the ruff clumps are small upright spikes, two of them on the crown between the ears read as horns. Diagnosis: one clump per face centre with the tip along the normal; non-planar face centres left two shells off the surface. Fix: six big blades placed on the true surface (BVH nearest), raked back and down, sunk 20 mm; no crown clumps. (Paint: nose black only above the lip line, wider cream bib, saddle only on the dorsal plane.)
  Attempt 1: 4 float shells, the raked tips sank back under the convex neck (tangent run 0.096 m drops ~30 mm below the surface). Re-run with the tip lifted 50 mm off the surface and a 12 mm sink.
  Result r02: PASS; the ruff reads as raked shingles, no crown spikes. 770 tris.
- r03 critique: az000 colour, the muzzle front is a black disc (koala nose): the nose cap is one n-gon and paint cannot split it. Diagnosis: nose rule paints the whole cap. Fix: cap and lip cream, muzzle top grey, and a separate black nose-pad block on the top front of the muzzle. Final stage-3 round, with orbit.
  Result r03: PASS; black nose block over a cream lip, amber eye, cream bib, tan legs, dark saddle and tail tip. 782 tris, orbit holds.

## Stage 4
- r01: armature from J (16 bones + .R mirrors, roll auto), automatic weights, every piece bound with body= weights; idle 48 f (breath, ear twitch, tail), move 25 f (diagonal-pair trot), attack 32 f (gather, head-down lunge, snap, recover).
  Result r01: all gates PASS (0 flips, 0 drift). Posed side renders: the trot pairs are diagonal (f13: L fore back, L hind forward), the lunge drops the head forward and down, the neck bends without collapsing; limb signs correct with roll auto.
- r02: final round with orbit + glbcheck; no code change (nothing in the posed renders needed a fix within the budget).
  Result r02: all gates PASS; glbcheck OK (attack/idle/move); orbit holds. Review packet built.

Triangles: s1 584, s2 620, s3/s4 782 total. Rounds: s1 6 (lock on r06), s2 3, s3 3, s4 2.
Honest weaknesses: the grey ruff blades read as flat shards pasted over the cream bib; the saddle is a small patch on the dorsal plane only (too faint vs the sheet); the ear fronts paint cream whole, so the ears read white from the front.
