# owl (t7) build notes

## Stage 0
Blueprint written from the brief: 0.64 tall, 0.41 long (beak to tail), 0.35 wide; egg body, flat facial disc, tufts to 0.645, wing tips past the tail root.

## Stage 1
- r01 Critique: 300 tris (gate FAIL); legs read as stilts; body a bucket. Diagnosis: 9 rings x 7 half-points too sparse; bottom ring at z 0.085. Fix: ring table rebuilt (11 rings, bottom 0.06), leg in 3 extrusions (trouser, ankle, spread foot), tuft in 2. Result: 380 tris, still under budget.
- r02 Critique: under budget, bucket belly. Diagnosis: no ring between belly underside and wing row. Fix: one lower-belly ring (z 0.13). Result: 404 tris, gates PASS.
- r03 Critique: front view is a column (body as wide as the head, straight sides) and too wide for the brief (0.41 with wings). Diagnosis: RINGS half-widths 0.16-0.17 on rings 2-5. Fix: egg ring table, widest 0.150 at z 0.23, bottom 0.06. Result: egg reads in az000; 404 tris.
- r04 Critique: wings are thin planks on the back quarter (az135, az180), invisible from the side. Diagnosis: wing region only idx3-4, offset 0.024 along +X. Fix: region idx2-4 over bands 3-6, pushed radially 0.028, tip row swept down/back. Result: side view now shows a folded wing covering the flank, tip past tail; 420 tris.
- r05 Critique: tufts read as cat ears (wide triangular base, az045/hero). Diagnosis: first tuft extrusion keeps 75% of the wide root face. Fix: pinch the first ring to 50%/28% and lean the tip out to x 0.158. Result: see r06.
  Result r06: tufts are now narrow feather horns leaning out (az000, top); 420 tris.
- r06 Critique: head is a hexagonal box (hero, top): flat side planes from the disc rim straight back. Diagnosis: head rings 8-10 idx3-5 on the plain ellipse (idx3 at y +0.014). Fix: skull columns overridden forward/full (idx3 y -0.055, idx4 x 0.138, idx5 x 0.078) and a lower, smaller crown. Result r07: rounder skull in top/az135; face disc still a flat plate (intended); 420 tris.
- r07 Critique: legs read as thin sticks under a heavy egg (az000, az180). Diagnosis: ankle quads 0.04 wide. Fix: trouser/ankle quads scaled ~1.35 (feathered pants). Result: see r08.
  Result r08: legs read as feathered pants, feet as spread toe pads; 420 tris; IoU side/front/top 0.897/0.934/0.860.
- r09 lock: reads as an upright horned owl from every view (egg body, flat disc, tufts, folded wings past a short tail). Chin shelf under the disc left for stage 2 vertex moves.
Stage 1 locked at r09: 420 tris, edge sha256 22ccac476a964bfb; min blueprint IoU 0.860 (top).

## Stage 2
- r01 Critique (from the lock): the disc is a flat plate with no eye, the chin a hard shelf (hero). Diagnosis: eye quad (band 8 idx1-2) has no socket; neck ring front recessed 0.012. Fix: inset socket (0.2, depth 0.014) as the one topology change; brow edge 8 mm forward over the socket, chin 8 mm forward, beak-root ridge, crown dome (vertex moves). Result: face reads (V ridge, overhanging brow, sockets); 436 tris; IoU vs s1 min 0.982.

## Stage 3
- r01 Critique: pieces pass all QA (0 hit/float/zfight, 1.2% slivers, 674 tris) and it reads as a horned owl, but the cream disc is a narrow rectangle round the eyes: reads as spectacles, not a facial disc (az000 colour). Diagnosis: body_rule paints only band 8 cream; chin band dark, forehead brown. Fix: chin centre and forehead behind the brows join the disc (cream), rim dark only at the sides. Result: see r02.
  Result r02: disc now a tall cream shield with dark side rims, brows read over cream; 674 tris; all s3 QA PASS.

## Stage 4
- r01: rig from J (root, chest, neck, head, thigh/foot L/R, wing L/R, tail), roll auto; skin above z 0.452 forced 100% head and toes 100% foot so rigid head pieces and talons cannot drift. Clips idle (neck+head turn), move (hop + flap), attack (wings spread, talons forward). Result: see below.
- r01 Result: FAIL drift 1 shell (piece_beak); fold-overs 0.30% tris / 0.11% area; hit/float/zfight 0. Diagnosis: the beak tip (z 0.45) anchors on the disc-bottom ring (z 0.445), below the 0.452 head-force line, so it rides neck-mixed skin. Fix: head-force line to z 0.438 (ring 8 included).
- r02 Result: all s4 gates PASS (drift 0, fold-overs 0.00%). Posed check: head turn holds the neck; wings swing out (+Z on L, -Z on R) and thighs swing forward (+X) in attack; wing spread is a modest lift of a body plate, not a true spread.
- r03: final run with orbit and glbcheck (no change).

Triangles: stage 1 420, stage 2 436 (base), stage 3/4 total 674. Rounds: s1 9 (lock r09), s2 1, s3 2, s4 3. Review packet built.
