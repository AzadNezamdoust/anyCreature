# Kraken hound (r20, opus)
Design: a wolf-sized sea-green hound, chunky with a big blocky head, slit yellow eyes and finned ears.
Identity cues: two purple shoulder tentacles arching over its back, a beard of jaw tentacles, coral dorsal fins.

Build: r20lib chain of 5-vertex half rings nose -> tail; legs extruded from two lower-flank quads; ears pulled from a skull quad. PARAMS block at the top. No reference sheet / blueprint (no downloads allowed); judged by eye.
## Stage 1 (6 render rounds)
- r01 584 tris PASS. Critique: slim greyhound, thin legs (az090). Fix: CHUNK torso (1.30, 1.12), head (1.25, 1.15).
- r02 FAIL self-intersection (legs inside the wider chest). Fix: LEG_X fore/hind +0.07, LEG_S 1.2. PASS.
- r03 Critique: head small, muzzle long. Fix: head CHUNK (1.45, 1.35), nose rings 4 cm back, ear tip out. PASS 584.
- r04 lock (edge 9f0c8379). r05/r06: re-lock after a kit-side determinism fix in r20lib (limb border order); same edge hash, re-run confirms.
## Stage 2 (1): elbow/wrist/stifle/hock loops, neck loop, brow + jaw moves. min IoU 0.99+.
## Stage 3 (1): 8 colours, tentacles, beard, fins, eyes, claws. 1264 tris.
## Stage 4 (3)
- r01 PASS; claws floated ahead of the paws (used unshifted leg x). Fix: claws use LEG_X/LEG_S.
- r02 PASS. Critique: tentacles too thin to read. Fix: TENT_R x1.4, beard x1.5.
- r03 final with orbit + glbcheck: all gates PASS. Weakness: straight cone tail; legs plain (no paw shape).
