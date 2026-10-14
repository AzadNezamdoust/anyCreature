# character (t7) build notes

No reference/ folder: stage 0 blueprint drawn by hand (1.6 m, head 0.365 m = 1:4.4 incl. flat underside, span 1.5 m).

## Stage 1
- r01: 718 tris, IoU side/front/top 0.934/0.974/0.911. Critique: head reads as a tall egg in az000/hero (the cheek and brow rings both at full width 0.18, a vertical cylinder band, narrow crown); it should be a big round faceted sphere. Diagnosis: rings hB/hC/hD/hE radii. Fix: widen cheek/brow to 0.19, deepen to -0.178, widen crown ring to 0.145 and top to 0.068 (a dome, not a point).
  Result r02: slightly better (head 0.38 wide x 0.365 tall, reads round-ish; the vertical cheek-brow band is the 8-segment faceted sphere), 718 tris.
- r02 critique: the hands are tiny flat paddles (az000, hero) and the thumb barely shows; a toon needs readable mitten hands. Diagnosis: palm/knuckle/finger rows ry 0.045-0.048, rz 0.02; thumb rows 0.02 wide. Fix: palm/knuckle rows to ry 0.052-0.056, rz 0.028-0.03, finger tip curled lower (cz-0.03), thumb rows 30% bigger and 0.1 m forward.
  Result r03: better; top view shows a mitten with a clear thumb, 718 tris.
- r03 critique: the feet read as thin skis in hero/az045 (0.09 wide, 0.05 tall at the ball); a toon bare foot is chunkier with a distinct toe block. Diagnosis: the three foot extrusion rows. Fix: ball row 0.10 wide x 0.058 tall, toe-crease row lower (0.048) so the toe block steps down; then lock.
  Result r04: better, the foot has a ball and a stepped toe block. LOCKED: 361 verts, 718 tris, edge sha256 d8e8712d526de542. Min blueprint IoU over stage 1: 0.911 (top, r01).

## Stage 2
- r01 critique: the face is a blank faceted ball (az000); the eyes have no socket and the eye facet is not a plane. Diagnosis: the hC-hD front quad beside the seam. Fix: flatten that quad and inset it (12%, 4 mm deep) as the eye socket; the nose, brows and mouth come as stage-3 pieces.
  Result r01: FAIL slivers 16 tris (2.2%): exactly the 4 socket wall quads per side, 12% of a 0.13 m facet = 1.5 cm walls.
- r02 critique: sliver gate (tech heatmap, hero/az000) on the socket walls. Diagnosis: inset amount 0.12. Fix: inset 0.25 (3 cm walls); the eye disc will overlap the rim.
  Result r02: PASS all stage-2 gates, 0 slivers, silhouette IoU vs stage 1 = 1.0, 734 tris. The socket rim reads as a visor band until the eyes cover it.

## Stage 3
- r01 plan (from the stage-2 critique: the face has no features): pieces = eye_L/eye_R (black outline disc, white sclera, black pupil nudged in/down, rooted 3 mm in the socket floor, proud 3.5 mm of the rim), brows (dark bar strip raycast onto the brow facet), mouth (short bar across the seam), nose (tiny skin pyramid on the seam). Palette skin/white/black/brow.
  Result r01: PASS (hit 0, float 0, z-fight 0, slivers 0), 4 colours, 1016 tris. Reads as a toon figure from the front; face has eyes, brows, nose, mouth.
- r02 critique: in az000 colour the eyes read as ordinary, not "big round cartoon eyes" (sclera 8 cm on a 38 cm head). Diagnosis: prism radii in stage3(). Fix: outline 0.052 x 0.055, sclera 0.046 x 0.049, pupil 0.021 x 0.024 nudged 1 cm toward the nose.
  Result r02: better, the eyes now fill the eye facets; PASS all gates, 1016 tris.

## Stage 4
- r01 plan: armature from J (hips/spine/chest/neck/head, thigh/shin/foot, clavicle/upper_arm/forearm/hand, eye bones for the blink), roll auto. Eye bones are removed from the skin (the head keeps those verts); eyes rigid on eye bones and blink by bone Y-scale (frames 40-44 of idle); brows/mouth/nose borrow body weights. idle 48 f breathing + blink, move 32 f walk with arm swing and hip bob, attack 32 f right punch with chest twist.
  Result r01: PASS all gates; fold-overs 2 tris (0.20% tris / 0.19% area, left armpit when the arms drop), drift 0. Posed wires: knees bend forward-correct, the neck holds, the punch arm reaches forward.
- r02 critique: in the head close-up the eyes look slightly outward (wall-eyed): each eye facet faces 22 deg off the axis and the pupil sat only 1 cm inward. Diagnosis: pupil offset in stage3(). Fix: pupil 1.5 cm toward the nose and 0.8 cm down; final round with orbit and glbcheck.
  Result r02: PASS all gates, unchanged QA (fold-overs 0.20% tris / 0.19% area, drift 0); pupils sit slightly more inward. glbcheck OK (attack/idle/move). Final: 1016 tris total (body 734 after stage 2; stage 1 718).
  Note: the blink is a bone Y-scale on frames 40-44 of idle; the drift gate samples idle at frames 10/20/29/39, so it does not see the squash (the eyes shrink in their own plane, they do not lift off).
Triangles per stage: s1 718, s2 734, s3 1016, s4 1016. Rounds: s1 4, s2 2, s3 2, s4 2.
