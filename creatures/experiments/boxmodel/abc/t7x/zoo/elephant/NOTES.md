# elephant (t7 hand box model, zoo workflow v2) — NOTES

Concept: refs/gpt/v3/elephant/sheet_1.png (2x2). `kit/refs.py --height 3.0` -> blueprint.json + reference/ (length
4.64 m incl. tusks and tail, width 2.53 m across the ears). Template: zoo/rhino/rhino.py (loft, leg windows, grow()).
Identity cue (elephant, not mammoth/rhino/hippo): huge fan ears standing out from the side of the skull, a long trunk
hanging from the face to the ground, a tall domed head over a deep barrel on four thick column legs with round
three-nailed feet, a thin tail with a dark tuft, tusks curving forward. The S1 silhouette carries ears, trunk, dome
head, barrel and columns; tusks and toenails come as S3 pieces.
Sheet notes: the side view staggers near/far legs; the model uses one symmetric pair (fore y -0.30..-0.37, hind y 1.55,
x 0.40). The plan view is shifted ~0.45 m forward against the side view (refs.py centres each bbox; the plan bbox ends at
the trunk, the side bbox at the tusk tip), so the top IoU stays low (0.68): the side wins.
Technique: one spine loft of 14-vertex half rings (44 stations: tail 8 x 6-vertex, rump 3, hind window 5, barrel 5,
fore window 5, neck 2, head 5, trunk 10 rings turning from upright to level and a small curl), legs from 4 x 3 lower-
flank windows through a 45 % transition ring (rhino's leg-root trick), ears from a 1 x 6 window on the side of the skull
(j2-j8 of H0-H1: a 0.7 m tall root) as a slab (14-vertex stations: front row / back row, thickness 40-100 mm).
Rig: neck -> skull -> head (cranium only, for the eye check's head length) and skull -> trunk0..3, skull -> ear.L.

## Stage 1
- r1: first fit. Gates PASS, 3,284 tris, IoU side/front/top 0.868/0.887/0.682. Reads as an elephant from every view.
  Critique: az000/top — the ears are narrow slabs swept back like flippers; the sheet's ears are broad discs seen
  face-on from the front (x 0.3-1.27), lowest at the front lobe (z 1.62 near y -0.7), top 3.0, and show as lobes from
  above. Diagnosis: EAR stations run back at ~33 deg to x 1.17 and are tallest at the outer stations.
  Fix: ear path more open (out to x 1.27), lower lobe on E2, outer stations shorter, the top rim leaning out (lean).
- r2 result: ears wider in front (to x 1.25) but still flat boards: front view top rim level and outer edge vertical
  (IoU 0.865/0.865/0.680). Diagnosis: the outer stations (x 1.18-1.27) are as tall as the middle ones, and in front
  view the outer stations set the outline. Fix (r3): plan path curving back in at the back edge.
- r3 result: no better (front 0.875): curving back in hides nothing, the outer edge is still a 1 m vertical line.
- r4. Fix: station heights read off the FRONT view per station x (E2 x 0.84 [1.66, 2.98] ... E6 x 1.28 [2.26, 2.46]),
  r2's path (out at ~45 deg, then back), no lean. Result: front IoU 0.905, the ear outline is a rounded fan from the
  front and az045; side 0.856: the side outline tapers to a rounded point at the back (y 0.22) where the sheet's back
  edge is a round D at y 0.3-0.45 (the sheet's side and front ears cannot both be met by a flat slab; front wins:
  it is the identity view). 3,284 tris.
  Critique (side overlay): the legs are uniform columns (ry 0.285) narrower than the sheet's broad upper legs, which
  merge into chest and haunch (fore near leg 0.65 m deep at the top, thigh ~0.75). Fix: deeper top sections.
- r5 result: upper legs broader (side IoU 0.862), 3,284 tris. r6 LOCK (edge sha ce2f9c99...), then a minimal S2-S4
  pass to probe the junctions (s4 r1, rhino's practice): eyes PASS (80 mm = 0.073 head; 0.61/0.94/0.70), ear membranes
  PASS (p10 41.8 mm, floor 18.7). FAIL: fore leg root knife 1.4 r at 96 deg (flag dump: the REAR rim of the fore
  window, y 0.02-0.08, z 1.13-1.30); ear knife 1.18 r at 130 deg (rear-top root corner and front-bottom corner);
  slit 2.8 % (ear back face vs neck side at E1, x 0.53-0.67 y -0.7..-0.8); tail strip 1.13 r (every tail face: 6-sided
  tail with rings 0.25 m apart = faces 5:1 on 60 deg creases; thighs fail only on these tail faces); posed clip
  ear.R vs upperarm.R 1.6-2.1 % in attack. Crops: tail reads as a thin pipe, a dark crease behind the ear root; the
  fore leg root reads broad.
- r7 (lock deleted and re-made: base changes, logged here). Critique: fore leg root knife (crops upperarm A/B: red
  faces behind the leg). Diagnosis: r5's FORE top ry 0.32 at cy -0.30 fills the whole 0.64 m window (rear wall stands
  on the rim) and the leg leans forward, so its rear wall faces back-up into the belly bevel. Fix: FORE top cy -0.32,
  ry 0.30, second section ry 0.28: a 6 cm margin at the rear rim for the transition to slope.
- r7 result: fore leg knife 1.4 r -> 0.25 r (PASS on knife); IoU 0.860/0.905/0.681; 3,284 tris. upperarm still FAILs
  on the ear: slit 2.8 % and the ear's lower-rim strip lie in the shoulder's 2 r region.
- r8. Critique: crops ear B / upperarm B — the ear's back face presses on the neck side behind the root (a dark slit)
  and a crease where it rises off the skull's rear-top. Diagnosis: E1 (0.62, -0.80, g 0.90/0.44) puts the back face
  at x 0.60, y -0.755: on the N0/N1 neck side (x 0.55-0.60). Fix: E1 (0.66, -0.88, g 0.95/0.31), E2 (0.88, -0.70):
  the ear root leaves the skull square and forward, clear of the neck.
- r8 result: slit 2.8 % -> 0 on both ear and shoulder, the attack ear-vs-arm clip gone; ear knife worse 1.18 -> 1.73 r
  (135 deg). Flag dump: every knife edge lies on the window's REAR rim (H0, y -0.78..-0.83, z 2.37-2.71): N1 (W 0.54)
  is wider than H0 (W 0.47), so the neck right behind the ear root bulges out and faces forward into the ear's back wall.
- r9. Fix: neck no wider than the skull behind the ear: N1 W 0.54 -> 0.48, N0 0.62 -> 0.57 (hidden by the ear).
- r9 result: ear.L/R PASS (knife 0.92 r at 102 deg, strip 0.83 r, slit 0); IoU 0.859/0.902/0.681.
- r10. Critique: tail crops A/B — the tail reads as a thin pipe with yellow strips down its whole upper half (tail0 and
  both thighs fail on them). Diagnosis: 6-sided tail rings 0.20-0.25 m apart: 37 mm wide faces 6:1 long on 60 deg
  creases. Fix: straight in-between rings (centre/tilt/size lerped, density rule 3.2) in Rt-T7, T7-T6, T6-T5 (x2),
  T5-T4 (x2): ring spacing ~0.09 m, faces under 3:1.
- r10 result: no gain (tail strip 1.58 r of a smaller r 0.139): the flag dump shows the tail faces are 22-24 mm wide
  (a 33-43 mm radius over 5 half-ring segments) and still 3.5:1 at 0.08 m spacing. 3,404 tris. The sheet's tail is
  0.08-0.10 m thick (side view 12-15 px), ours 0.066-0.086: the tail is thinner than the sheet.
- r11. Fix: tail T3-T7 and Rt half sizes x 1.35 (sheet thickness), so faces are ~31 mm wide (< 3:1 at 0.08 m).
- r11 LOCK (3,404 tris, edge sha c97c207c...; IoU 0.860/0.902/0.681). s4 r6 probe: thighs PASS (strip 0.45 r), ears
  PASS; tail0 strip 1.53 r = one needle of the R0 -> Rt 14 -> 6 fan; upperarm strip 1.9 r = the ear's lower RIM faces
  (yellow along the ear edge in crops j2 A/B/C; the beauty crops show a clean ear edge: rim of a slab, not a seam ->
  noise per rule 6.3, kept under watch). Crops j4 A/B/C: dark creases RADIATE from the tail root over the rump — the
  fan from R0 (W 0.26, 14 verts) into Rt (W 0.115, 6 verts) is visible. S1 rounds used: 11 of 14.

## Stage 2
- r1: eye socket inset (logged). Fix (tail-root fan, crops j4): S2 vertex moves — R0 pulled toward the tail root
  (x 0.77, height 0.84 about its centre), Rt widened (x 1.22, height 1.19): a 1.4:1 bridge instead of 2.3:1, the
  root ring broad over the rump.
- r1 result (s4 r7): tail0 strip 1.53 -> 1.13 r, knife 1.11 r at 99 deg; thighs PASS. Dump: the knife is UNDER the tail
  root: Rt (tilt 25) tucks its bottom 3 cm ahead of R0's bottom (y 2.05 vs 2.08), a notch (rhino s4 r19's notch).
- r2. Fix: Rt re-placed at tilt 10 (same centre, the r1 sizes): its bottom at y 2.08, level with R0's, one slope.
- r2 result: WORSE (2 self-intersections, tail knife 1.72 r): reverted.
- r3. Fix (rhino s4 r19's notch fix, kept r1's scale): Rt's bottom verts (j4, j5) 3 cm back and 1 cm down, R0's bottom
  verts (j12, j13) 2.5 cm up: the tail's underside runs into the rump in one slope.
- r3 result: tail knife 0 (max concave 82 deg) but 4 self-intersections: Rt's bottom 3 cm back crosses the in-between
  ring T7_1 behind it. Strip 1.12 r.
- r4. Fix: Rt's bottom only 1 cm back, 1.2 cm down (R0's bottom stays 2.5 cm up).
- r4 result: tail knife 0 (max 83 deg), no intersections, thighs knife 0; tail strip 1.12 r = ONE needle: R0's j8/j9
  (3 cm apart: BODY's close flank-bottom spacing at R0's small size) fanned to one Rt vertex 15 cm away. Crops j4 A/B:
  a hooded lip with a dark slit at each side of the tail root (visible).
- r5. Fix: R0 pulled further in (x 0.615, height 0.78: W 0.16, h 0.125) to about Rt's size (W 0.14, h 0.12): the
  rump's rear is a broad face R1 -> R0 and the 14 -> 6 bridge has no long fans.
- r5 result: WORSE (tail knife 1.23 r, strip 1.71 r): reverted to r4's 0.77 / 0.84.
- r6 (last S2 round). Diagnosis of r4's needle: R0's vertices follow BODY's profile, bunched 3 cm apart on the flank
  bottom (j6-j10) at R0's small size, while Rt's 6 are even: bridge_rows fans two bunched R0 verts to a Rt vertex
  15 cm above. Fix: R0's 14 vertices re-placed on an EVEN-angle superellipse (prof(2.2, 2.2, 0.9)) of the same
  centre, tilt and r1 size; the j12/j13 bottom lift kept.
- r6 result: tail knife 0, thighs PASS, tail strip 1.13 r unchanged: the dump shows the needle is a bridge_rows
  triangle that joins R0's j7-j8 (z 1.76/1.73) to Rt's j2 12 cm ABOVE them (index matching lags on the 14 -> 6 bridge);
  crops j4 A/B still show a hooded lip with a dark side slit. S2 rounds used up (6/6).
- S1 r12 (lock deleted and re-made, logged; S1 rounds 12/14). Fix: bridge_rows picks, wherever it must place a
  triangle, the one whose new edge is shorter (greedy shortest diagonal) instead of index order; quads unchanged.
  S2's moves are position-based and re-apply.
- r12 result: tail0 PASS (knife 0, strip 0.76 r), thighs PASS (knife 0, strip 0.52 r), ears PASS; 3,404 tris.
  Left: upperarm.L/R strip 1.9 r = the ear's lower RIM band (25.6 mm wide: rim verts at 0.6 of the slab thickness,
  t 22-34 mm) inside the shoulder's 2 r region.
- r13 (lock re-made, S1 13/14). Fix: the ear slab's rim no longer pinched (k = 0.9 + 0.1 sqrt(1 - v^2), was 0.6 + 0.4)
  and the outer stations a little thicker (t E2-E6 0.036 / 0.032 / 0.030 / 0.028 / 0.026): rim faces 47-65 mm wide.
- r13 result: rim faces 48 mm wide and still flagged (the shoulder region's median face is ~0.2 m: a rim would need
  > 80 mm). upperarm strip 1.9 r is the ear's own lower rim, ~0.8 m from the leg root; crops j2/j3 A/B/C show a clean
  ear edge, no seam, no slit, no fold at the shoulder -> NOISE (rule 6.3, rhino precedent). Kept r13 (ear membrane
  p10 56.7 mm, reads less like a board edge). LOCK r13: 1,704 verts, 3,404 tris, edge sha 825866791bee4dfd.
  Every other junction PASS: ears (knife 0.92 r), tail0 (knife 0, strip 0.76 r), thighs (knife 0), fore knife 0.53 r.
  Note: S2's six moves (eye socket, R0 even-angle ring, Rt widened, tail-root notch) re-apply by position after relocks.

## Stage 3
- r1 (built with the s4 probes): lens eye 80 mm (0.075 of the 1.1 m head) with pupil disc; tusks: library `horn`
  (6 sides, one per side, side=-1 mirrored); 3 toenails per foot (rhino's hand-built arched nail: no library elephant
  nail; `hoof_cloven` replaces the limb end); palette skin #94877b, feet #a8978a, tuft #4b4642, ivory #ece2cf,
  eye #3a2a1e (5 colours). EEVEE orbit18: mid warm grey like the sheet, not washed out. Separation PASS (tail-hind
  0.45 m, fore L/R 0.29, hind L/R 0.29). 3,996 tris.
  Critique (orbit18 az0/az90, face_34): the tusks are thin pointed spikes running straight forward; the sheet's are
  thick ivory (~0.15 m at the lip) with a blunt tip, sweeping down-forward and curving up at the end.
- r2. Fix: tusk radius 0.078 -> 0.092, taper 1.3 -> 2.0 (stays thick), 8 sides, curve 38 -> 48, start more downward.
- r2 result: PASS, 4,056 tris, 5 colours; the tusks read thick and ivory with a slight upward sweep (az090, hero).
  The workbench sheet renders the palette darker than EEVEE (rhino's note); the EEVEE orbit is the colour check.

## Stage 4
(s4 r1-r14 were junction probes of the build during S1/S2, as on rhino.)
- r15: full S4 with orbit + junctions (final).
- r15 result: every kit gate PASS (lock, glbcheck OK, techqa: slivers 10 = 0.2 %, z-fight 0, fold-overs 0, drift 0);
  4,056 tris. Junctions: ears, tail0, thighs PASS; eyes PASS (0.57/0.88/0.66, 83 mm = 0.075 head); membranes PASS
  (p10 56.7 mm); upperarm.L/R FAIL on the ear-rim strip only (noise, see S1 r13). WARN posed clip 2.76 % (pink on the
  trunk in az000/hero tech QA). Critique (attack_f008/f016 hero): the trunk curls BACK between the tusks toward the
  chest; an attack should raise it forward. Diagnosis: roll='auto' makes +X swing a hanging chain's tip forward (BRIEF
  §8); the attack keys used -15/-25/-25 on trunk0-2. Fix: attack trunk signs flipped (+12/+22/+18, recoil -6/-8).
- r16 result: all kit gates PASS, the posed-clip WARN gone (root clip 0); attack raises the trunk forward and lifts the
  ears, move steps cleanly, no neck/trunk collapse (posed clay/wire). Junctions as r15 (upperarm ear-rim strip = noise).
  Owner-style review (orbit18 EEVEE + crops s4_r16): (1) the EEVEE skin reads a touch light and pinkish next to the
  sheet's warm grey #938274; (2) from above the ears are thin flippers, the sheet's are lobes (a flat slab cannot be
  both: residual); (3) a long hard shoulder-bevel line runs the length of the back (BODY j2-j5 planes: the crisp-plane
  style, kept); (4) faint facets at the tail root sides (crops j4, minor); ear/leg/thigh roots broad, no slit/fold.
- r17. Fix (1): skin #94877b -> #8e8073, feet #a8978a -> #a08f81 (sheet sample #938274 / legs #a6917f).
- r17 FINAL: all kit gates PASS (lock edge sha256 825866791bee4dfd..., glbcheck OK, techqa: hits 0, floats 0,
  z-fight 0, slivers 0.2 %, fold-overs 0, drift 0, no posed-clip warning); 4,056 tris (body 3,412 incl. eye socket).
  Junction probe: ear.L/R, tail0, thigh.L/R PASS; eyes PASS; ear membranes PASS (p10 56.7 mm >= 18.5); upperarm.L/R
  FAIL on the seam-strip metric only (the ear's lower rim inside the shoulder's 2 r region; knife 0.53 r, slit 0,
  poke 0) — not a seam in any crop: noise (rule 6.3). Separation PASS (tail-hind 0.45 m, fore/hind L-R 0.29 m).
  EEVEE colour now matches the sheet's warm grey (side_by_side_sheet.jpg). --review and --compare run.
  Residuals: ears are flat slabs (thin flippers from above, rounded fans from the front); the rump reads as a flat
  oval cap with a rim from the rear (R2-R0 close rings) where the sheet's rump is a tall split dome; long hard
  shoulder-bevel line down the back; eye socket is a rhombic inset (lens itself round and clear).

## Detail pass (2026-10-23 night, tier 3: 6 -> 12+ groups; backup before_detail/)
- r18 (S4): trunk rings (5 STEP wrinkle arcs), knee folds, brow, tail brush, shoulder fold, inner-ear paint +
  smooth_borders. ALL gates PASS (detail 12 groups, eyes, junction). Critique (hero/az090): the ear face reads pink
  (not on the sheet: ears are grey); knee arcs read as cuffs. Fix r19: ear face a lighter grey (#a39488), knee arcs
  replaced by a lower-lip mound under the trunk root.
- r19 crashed: the lip ray missed (empty piece). Fix: four fallback points down the cheek; no piece if none hits.
- r19 Result: ALL gates PASS (kit, junction, eyes 0.58/0.89/0.66, detail 12 groups: trunk rings, shoulder fold, brow,
  lower lip, tail brush, lighter ear face + tusks, nails, ears, tail, pale feet). A/B Opus both orders: variant won
  BOTH (trunk wrinkles read at 160 px) -> ADOPT. Residual: the tail brush reads smaller than the sheet's leaf tuft.
