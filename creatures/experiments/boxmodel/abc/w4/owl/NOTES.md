# owl (w4) build notes

## Stage 1
- r1: first blockout, 448 tris, IoU side/front/top 0.912/0.922/0.941. Gates PASS.
- r2 critique: front view reads as a snowman: a deep waist between head and body at z 0.45 (the reference head runs straight into the shoulders with only a small notch).
  diagnosis: R5 half-width 0.130 against R4 0.155 and R6 0.142. fix: R4 0.160, R5 0.148, R6 0.150.
  result r2: better, head flows into the shoulders; IoU 0.910/0.912/0.941, 448 tris.
- r3 critique: side/3-4 views: the wing is a rectangular box panel stuck on the flank (reference: a diagonal leading edge from the shoulder back to a tip that drops over the tail).
  diagnosis: wing region = rings R1-R4 x theta 75-152 on a uniform grid, extruded by one constant offset. fix: per-ring thetas push the leading-edge column back on lower rings (68 -> 108 deg); wing verts taper (thin at shoulder, thick and dropped 3.5 cm at the tip).
  result r3: better, the wing now has a diagonal leading edge and drops over the tail; IoU 0.910/0.902/0.908, 448 tris.
- r4 critique: front/side: the legs are thin stilts under a wide egg, with a long wedge foot (reference: short thick feathered legs, compact foot; toes and talons come as stage-3 pieces).
  diagnosis: leg rects 0.044 x 0.052 (top) and 0.030 x 0.034 (ankle); toe push 5 cm. fix: leg top 0.060 x 0.072, ankle 0.040 x 0.040, foot pad 0.078 x 0.094, toe push 3.5 cm.
  result r4: better, legs read as short feathered trousers on a pad foot; IoU 0.910/0.901/0.908, 448 tris.
- r5 (lock): the base reads as an owl from every view (egg body, continuous head with corner tufts, diagonal folded wings, fan tail wedge). The flat facial disc, eye sockets and brow go in stage 2 as vertex moves / insets. Locked with the orbit.
  lock: 448 tris, edge sha256 fc4760307ce436c9; min stage-1 blueprint IoU 0.901 (front).

## Stage 2
- r1 critique: hero/front: the face is the round front of a dome (reference: a flat facial disc with a rim, sockets for big eyes).
  diagnosis: head rings R5-R8 are ellipses; no socket. fix: disc verts (theta 0-38) onto one plane leaning 0.3 back, centre ridge +1 cm, eye socket inset; wing panel flattened to two planes.
  result r1: FAIL: 2 self-intersecting face pairs, slivers 3.0%; the disc reads, but a shelf juts out under it at z 0.45; 464 tris.
- r2 critique: hero/side: a horizontal shelf under the face (reference: the disc's lower rim sits back, flush with the chest).
  diagnosis: the disc selection took ring R5 (z 0.45), pulling its theta-41 verts forward 5 cm over R4. fix: disc selection starts at z 0.47 (R6-R8 only); R5 stays as the lower rim.
  result r2: shelf gone, IoU min 0.952, but still 2 hits + 3.0% slivers. Diagnostic (out/.../diag.py): every hit and sliver sits on the wing leading edge: the flattened wing plane cuts the belly column, and the 1-2 cm extrusion step makes needle triangles.
- r3 critique: hero: the wing's leading edge is a thin smear, not an edge (and it breaks the gates).
  diagnosis: stage-1 wing offset only 0.010-0.022 m at the leading column; flatten() pulled verts through the body. fix: drop the wing flatten; push the leading-edge column of wing verts out 1.4 cm and the shoulder row 0.8 cm.
  result r3: PASS all stage-2 gates; min IoU 0.956; 464 tris; the wing now has a crisp leading edge. Final stage-2 round (r4) re-run with the orbit.

## Stage 3
- r1: palette on the body (disc cream + dark rim on existing head columns, belly cream on the theta-45 column / R1-R4 rings, dark wing and tail tips), pieces: octagon eyes + pupils, hooked beak, V brows, ear-tuft blades, toes with talon tips.
  result r1: reads as a horned owl (disc, orange octagon eyes, V brows, tufts, beak, talons); 732 tris, 6 colours. FAIL: slivers 6.6% (brow 8, tuft 8, toes 32) and 6 z-fighting toe faces.
- r2 critique: tech heatmap: needle triangles along every blade tip; toe tops lie on the foot's toe block.
  diagnosis: blade() ends in a 12%-wide quad whose diagonals make < 6 deg triangles; toe bases at z 0.011 run parallel to the toe block top. fix: blades end in one apex vertex; toes start higher (z 0.017) and slope down to the talon, so no face lies on the block.
  result r2: PASS (0 slivers, 0 z-fight, 0 hits/floats); 660 tris, 6 colours. r3 = same build with the orbit (final stage-3 round).

## Stage 4
- r1: rig on J (hips/chest/neck/head, eye, thigh/shin/foot, wing, tail; roll auto); body skinned, face pieces and toes bound with body= weights, lenses/pupils on eye bones; idle head turn + blink (eye scale), move hop + wing flap, attack talon strike with wings out.
  result r1: every gate PASS except drift: 5 shells (eyes 2, brows 2, beak 1); fold-overs 0.30% tris / 0.24% area.
- r2 critique: posed idle (head turn): the eyes, brows and beak slide off the disc.
  diagnosis: bone heat blends head/neck/chest weights across the face, so the skin shears under the twist while rigid/offset pieces follow a different blend. fix: every body vertex with z >= 0.465 is 100% head before the pieces are bound; head turn 38 -> 32 deg.
  result r2: eyes and brows seated; drift 1 shell left (beak); fold-overs 0.30% / 0.24%.
- r3 critique: posed idle: the beak's chin end slides on the lower rim ring R5 (z 0.45), which is still a head/neck blend.
  diagnosis: the rigid-skull threshold z 0.465 sits above R5. fix: threshold 0.44, so R5 (the disc's lower rim) is skull too; the neck bends between R4 and R5.
  result r3: all stage-4 gates PASS: drift 0, fold-overs 0.30% tris / 0.24% area. Posed wires: the neck bends between R4 and R5 without collapsing; the wing spread in attack is modest (32-36 deg), kept so the side skin does not fold.
- r4 (final): same build with the orbit + glbcheck, then --review.

Triangles: stage 1 448, stage 2 464 (base), stage 3/4 660 total.
