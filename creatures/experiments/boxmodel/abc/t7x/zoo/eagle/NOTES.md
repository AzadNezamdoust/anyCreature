# Eagle (zoo new wave), t7 hand box model, workflow v2

Sheet: `refs/gpt/v3/eagle/sheet_1.png` (2x2: side, front, rear, top). The side and front figures touch (tail tip vs wing tip, no white gutter), so `sheet_src/sheet_gutter.png` re-spaces the four views with 60 px gutters (no scaling) and `kit/refs.py --height 0.85` traced it: length 0.845 m, span 1.82 m (front), 1.53 m (top). One scale (2.285 mm/px) for all views.
Reference notes:
- The sheet's SIDE view shows folded wings (wrong for this pose): it gives the body, head, beak, legs and tail only; the back line under the folded wing is estimated. FRONT and TOP give the spread wings (span, dihedral, planform, fingered tip, fan tail). Side IoU is info only (non-cage build).
- The front and rear views show the wing surface face-on, the top view shows it in plan: the wing chord is tilted back-down (48 deg at the root, 30 deg at the tip) so both read; half span 0.85 m + 0.13 m primaries (rear view span 1.70 m).

**Identity cue:** a big-shouldered raptor standing upright with broad plank wings spread wide (fingered primaries at the tips, feather-tip trailing edge), a fan tail to the ground, golden crown and nape over a dark brown body, a heavy hooked yellow-and-dark beak under a flat brow, feathered trousers over yellow taloned feet. Not a hawk (bulk, golden nape), not a vulture (feathered head), not a generic bird (the spread wing span and fingers).

## Stage 1
- r01: first loft (39 stations, 13-point half rings, 2x from T2 to H2), wings extruded from the 10 x 2 shoulder region M1..C3 (24-vertex rings, 11 span stations + a 45 % transition ring, trailing edge stepping back on odd stations, covert column zig-zag), legs from the 4 x 3 lower-belly region R2..M1. PASS, 3660 tris, IoU side/front/top 0.70/0.44/0.72 (front: the sheet's face-on wing).
- r02: Critique: az090: the body is a thin diagonal plank (back to breast 0.25 m at z 0.5; sheet 0.41 incl. the folded wing). Diagnosis: back seam points R0..C3 sat on the sheet's wing-covered outline guess. Fix: back seam points 2-4.5 cm out along the cut lines (chunky back under the wing root).
- r02 Result: PASS 3660 tris, IoU 0.713/0.437/0.722; ortho side now a chunky barrel (breast to back 0.31 m at z 0.5).
- r03: Critique: top/az000: the wing is a constant-chord plank (plan chord 0.23 root to tip, trailing edge straight); the sheet's top view has a secondary bulge at mid wing and a hand narrowing to the fingers. Fix: chords 0.34/0.37/0.39/0.39/0.37 to the wrist, then 0.33 -> 0.19 at the tip.
- r03 Result: PASS 3660 tris, IoU 0.716/0.425/0.738; top view: the wing narrows to the tip, secondaries bulge.
- r04: Critique: hero/az045: the fan tail reads as a thin spike from the side and 3/4 (14-40 mm half thickness). Fix: tail half thickness 16-50 mm (root = undertail coverts), tip W 0.19.
- r04 Result: PASS 3660 tris, IoU 0.725/0.426/0.737; the fan root reads thicker from az045/az090 (still a thin fan from the side, as a real fan tail).
- r05 LOCK (no change): reads as a spread-winged raptor from every round view; junctions are probed from the S4 rig (no rig at S1).

## Stage 2
- r01: eye socket: one inset (0.2) in the side face nearest the sheet eye (y -0.33, z 0.805), sunk 5 mm. All s2 gates PASS, IoU vs s1 1.0, slivers 1.5 %, 3676 tris.

## Stage 3
- r01: pieces: lens eye (12 mm radius, amber-brown, dark pupil), six primary "fingers" fanning out of each wing tip, three rounded tail-feather tips per side past the fan, parts bird_foot raptor feet (yellow scales, dark talons); 7 colours, border on the wing's covert column (zig-zag) and the N0 ring / mid-head column (golden nape). PASS, 4556 tris. Critique: the colour renders read near-black (body #5c4231 under the studio light); the covert band barely shows.
- r02: Fix: mid-value palette (body #7a573c, coverts #a07a55, flight #503b2c, gold #d69c55).

## Stage 4 first pass
- s4 r01 (rig hips/spine/chest/neck/head, tail0, wing/wing1/wing2, thigh/shin/foot; idle head turn, move = hop with wing beats, attack = mantle + lunge + talon strike): all kit gates PASS, glbcheck OK, WARN 0.64 % posed clip vs body. Junction probe FAIL: thighs knife 2.83 r at 178 deg (crops A/B: a slot between the two thighs' inner walls and the one-face belly seam strip); wing roots knife 1.21 r at 137 deg (crop C: a crease along the region's lower edge under the wing). Tail PASS. Eyes PASS 0.25/0.66/0.68, diam 13.7 % of head. Membrane PASS p10 18.2 mm (floor 7.7).

## Stage 1 re-locks (junction fixes inside the dense mesh; old lock in before_relock1/)
- r06: Critique: groin slot (thigh knife 178 deg, s4 r01 crops A/B). Diagnosis: leg region on ring points 8..11, its inner edge one face from the belly seam, so the two inner walls fold into a narrow slot. Fix: region on points 7..10 (2-face belly strip between the thighs).
  - first try FAIL 4 self-intersecting pairs (leg inner wall x 0.018 inside the belly strip at R2). Region moved to R2b..M1b (centred over the leg, y -0.1), leg centre x 0.078 -> 0.088, rx 0.052 (inner side 0.036).
  - second try FAIL 4 pairs: the thigh's rear wall (y -0.03) behind the region's rear edge (y -0.075), under the R2 belly. Thigh top centre y -0.135, ry 0.072.
- r06 Result (r07 LOCK a50f9260a9cfeb07; s4 r02 probe): groin slot gone; thigh knife 2.77 r at 161 deg now on the thigh's REAR wall (crop B): the belly behind the legs (R1/R2 bottoms z 0.22-0.245) hangs level with the thigh top (z 0.25), a slot between thigh back and vent. Wing roots unchanged (1.21 r).
- r08: Fix: vent tucked up behind the legs: R0/R1/R2 bottom seam points to z 0.23/0.258/0.278 (and 1-2 cm back), so the underside slopes up from the thigh's rear wall to the tail root.
- r08 Result (LOCK 0f242b5b; s4 r03): thigh knife 2.77 -> 2.06 r (157 deg). A fold script on the GLB puts the folds on the region's rim edges (x 0.07-0.11, y -0.18..-0.01, z 0.30-0.36): the 0.19 x 0.17 m belly patch is pulled in and down to a 0.10 x 0.14 m thigh top, so the transition ring sinks below the rim (knife all round).
- r09: Fix: the transition ring stands out of the body: region vertices pushed 3 cm out along the region's mean normal, then 30 % toward a broader thigh top (rx 0.058, ry 0.088, centre y -0.125, z 0.255): the trouser feathers puff out of the belly.
- r09 Result (LOCK ffbf9838; s4 r04): thigh max fold 157 -> 118 deg but knife length 4.1 r: the folds are still the region rim (fold script: R2b rear rim and inner rim, 100-118 deg): the root patch (points 7..10) reaches up the side to the widest point (z 0.36-0.45), so the thigh's outer-rear wall leaves the flank high and turns down at a fold.
- r10: Fix: root region points 8..10 (4 x 2, 12-vertex leg rings; inner edge still 2 faces from the seam), puff 2 cm, transition 35 %.
- r10 Result (LOCK df21e286; s4 r05): thigh knife 2.4 r at max 119 deg, no strip. Fold script + crop B: the folds are now the INNER rim (x 0.072-0.079): the thigh's inner wall drops vertically from a flat, down-facing belly strip (110-130 deg groin corner).
- r11: Fix: KEEL profile on R2/M0/M1 (bottom seam 20 % lower, p11 slightly in): the belly between the thighs is a V, its faces lean toward the inner walls.
- r11 Result (LOCK e4353955; s4 r06): thigh.L PASS 1.0 r, thigh.R 1.01 r (max 132 deg, inner rim). Wing roots unchanged: fold script puts the 127-137 deg folds on the region's LOWER rim (x 0.10-0.114, z 0.56-0.69): the underwing leaves the flank level and the flank drops away below it (an armpit knife).
- r12: Fix: shoulder region 10 x 3 faces (points 2..5): the underwing root starts one face lower on the flank, so the transition ring is a sloped fillet from the flank into the underwing (26-vertex wing rings).
- r12 Result (LOCK f89343f9; s4 r07): wing roots PASS (knife 0.9 r, max 100 deg, strip 0.47 r); new kit FAIL: slivers 2.2 % (102): the trailing-edge teeth skew the last chord column's faces between a short and a long station, now 3 faces deep.
- r13: Fix: the tooth step is shared by the last two chord columns (half at column 9), so the skewed faces are half as sheared.
- r13 Result: no change in slivers (102): a sliver script on the GLB puts 28 on the beak hook (B3-B4 quads, 2 x 19 mm) and ~65 on the wing's blunt trailing-edge end faces (thickness/3 = 5 mm wide, 70-120 mm long), not on the teeth.
- r14: Fix: trailing-edge corners at 94 % of the chord (were 97.5 %): the end faces become ~20 mm wide bevels.
- r14 Result (LOCK 4086c92b; s4 r09): slivers 1.7 % PASS (76); wing roots PASS 0.92 r; membrane p10 17.2 mm PASS; thigh.L PASS 1.0 r, thigh.R FAIL 1.01 r (inner rim, 132 deg).
- r15: Fix: deeper keel between the thighs (bottom seam 30 % below, p11 a little lower), the belly faces lean further toward the thighs' inner walls.
- r15 Result (LOCK ccdfb42e; s4 r10): worse: thigh max 138 deg, thigh.R 1.02 r. Keel reverted to -1.2.
- r16: Diagnosis (fold script): the inner-rim folds come from the transition ring's puff: the inner rim verts are pushed out (+x) along the region's mean normal, so the inner wall first steps out then turns in. Fix: puff scaled by (u+1)/2: full on the outer rim, none on the inner rim (the belly strip runs straight on into the inner wall).
  - first try FAIL 4 self-intersecting pairs (x 0.05, z 0.28): without the puff the inner wall runs under the keel strip. Inner rim now pushed straight DOWN by the puff (outer rim along the normal, blended by u).
  - second try (inner rim pushed down): LOCK f7f9dfb5, s4 r11 worse (max 153-166 deg). Diagnosis (normals): the thigh's top inner side (x 0.032) sits INSIDE the region's inner rim (x 0.072), so the inner wall slants in under the belly and faces UP: 139+ deg against the down-facing belly strip, whatever the puff does.
  - final r16 fix: uniform puff restored; the first two thigh sections get an inner half width of their own (x 0.068 at the top, 0.048 at the next): the inner wall drops from the rim and slopes in BELOW it (faces down-in, no overhang).
- r16 Result (LOCK 796bd3a5; s4 r11): thigh max fold 153 -> 115 deg (knife 1.5 r); remaining folds on the REAR rim (R2b, y -0.035..-0.06, 112-115 deg) and the inner rim (100-109 deg).
- r17: Fix: same rule at the rear: the first two thigh sections get a rear half depth of their own (0.06 / 0.055, rear at y -0.065), inner half width 0.012 at the top (inner side x 0.078, at the rim).
- r17 Result (LOCK 9b7fbae7; s4 r12): thigh max fold 115 -> 105 deg; crops: the root reads blended in A/C, a mild crease at the rear top (B). Folds left (fold script): the FRONT rim (M1b, y -0.16..-0.18, 103-105 deg), the rear rim 97-100.
- r18: Fix: thigh top front half depth 0.088 -> 0.072 (front at y -0.197, under the M1b rim instead of ahead of it).
- r18 Result (LOCK 9b7fbae7 same topology; s4 r13): max fold 102 deg but r shrank to 64-68 mm (slimmer thigh top), knife 1.7 r. The section-shaping route stalls: a wall that leaves the body along its normal folds ~90-105 deg at the rim whatever its size.
- r19: Fix (WORKFLOW 4: two to three rings make the turn): a two-ring fillet at the thigh root: ring 1 = region vertex 1.2 cm out along the normal + 1.8 cm along the surface away from the region centre (the root flares on the belly), ring 2 = 2.4 cm out, 45 % toward the thigh top. Topology +1 ring per leg.
- r19 Result (LOCK 69e94902; s4 r14): much worse: thigh knife 4.3 r at 139 deg (the flared ring steps out on the belly and the second ring turns back in: two folds instead of one). Reverted.
- r20 RE-LOCK of the r18 base (sha 9b7fbae7 expected). The rim fold (93-105 deg on 3 edges) moves to stage 2: a vertex relax on the thigh root rim and the transition ring (vertex moves only).

## Stage 2 (after the r20 re-lock)
- r02: Critique: thigh root rim fold 93-105 deg on 3 edges (s4 r13). Fix: Laplacian relax (4 x 0.5) of the vertices within 8.5 cm of the thigh root (rim, transition ring, first trouser ring; seam verts stay on x = 0).
- r02 Result (s4 r15): thigh knife 0 (max concave 76 deg, was 105); wing/tail/eye PASS; new FAIL seam strip 1.18-1.41 r (14 mm wide): the relax squeezed the transition ring's faces into a thin band; r 58-69 mm (thigh top slimmer).
- r03: Fix: relax 2 passes instead of 4.
- r03 Result (s4 r16): knife 0 (max 82 deg); the strip is unchanged (1.2-1.4 r, 13.6 mm): crops A/B show it as a thin vertical band on the thigh's inner front: the r17 inner half width (0.012) squeezes the inner column of the first trouser rings.

## Stage 1 re-lock r21
- r21: Fix: thigh inner half widths 0.012/0.035 -> 0.026/0.042 (the s2 relax now rounds the rim fold, so the inner wall no longer has to hide under the rim).
- r21 Result (LOCK 356310d9; s4 r17): thigh knife 0.5-0.6 r (max 92 deg) PASS-level, strip 1.04-1.22 r (11 mm). A strip script finds it: one 11 x 73 mm triangle at the thigh's FRONT rim (y -0.17, z 0.29), outside the relax radius.

## Stage 2 (on the r21 lock)
- r04: Fix: the relax reaches the front rim: centre 1.5 cm forward (y -0.13), radius 0.085 -> 0.10.
- r04 Result (s4 r18): no change (strip 1.09-1.22 r): the flag crops put the strip on the thigh's inner column next to the keel, made by the r17-r21 asymmetric inner half widths, not by the rim.

## Stage 1 re-lock r22
- r22: Fix: thigh rings back to the r14 symmetric sections (strip 0 there; its only fault, the 1.0 r rim knife, is now handled by the s2 relax).
- r22 Result (LOCK 4086c92b = the r14 base; s4 r19, relax 2 x 0.5 r 0.10): thigh knife 1.04-1.14 r at max 97 deg, strip 1.02-1.12 r (13 mm): close on both, on the symmetric rings.

## Stage 2 (on the r22 lock)
- r05: Fix: relax 3 passes at 0.35 (gentler per pass, a little further overall).
- r05 Result (s4 r20): knife 1.06-1.08 r, strip 1.04-1.06 r. Fold script: the worst folds (116-123 deg) are the INNER rim (x 0.063, ring point 10): the symmetric thigh top's inner side (x 0.032) overhangs it.
- r06: Fix: the inner rim vertices (point 10 of R2b..M1b) 1.2 cm in and 1.2 cm down (the keel strip slopes into a vertical inner wall), then the relax.
- r06 Result (s4 r21): worse (knife 1.56 r at 101 deg). Reverted.

## Stage 1 re-lock r23
- r23: Critique: the trousers read thinner than the sheet's fluffy feathered thighs (sheet front: x 0.03-0.13 at z 0.3), and the thigh root sits at the probe limits (knife/strip 1.04-1.08 r). Fix: fuller trouser rings: top rx 0.064 / ry 0.094 (centre x 0.092), second rx 0.058 / ry 0.076.
- r23 Result (LOCK b98b975f; s4 r22): knife 1.01-1.07 r (max 102 deg), strip 1.0-1.06 r; r 73-78 mm. Strip script: the thin triangles are on the REAR rim (R2b, y -0.036..-0.06, crease 98-106 deg): the thigh's rear wall (y -0.031) overhangs the rim.
- r24: Fix: rear half depth of the first two trouser rings 0.094/0.076 -> 0.064/0.062 (rear wall at y -0.061, under the rim); inner/outer/front unchanged (the r17 inner squeeze made the strip).
- r24 Result (LOCK b98b975f same edges; s4 r23): thigh knife PASS (0.54 r, max 100 deg); strip 1.09-1.1 r. Strip script: two needle triangles at the inner-rear corner sharing a 16 mm edge between the rim corner (0.065, -0.072, 0.291) and the transition ring's corner (0.070, -0.077, 0.277).

## Stage 2 (on the r24 lock)
- r07: Fix: that transition-ring corner vertex slid 1.3 cm on down the leg (vertex move).
- r07 Result (s4 r24): no change in the strip, knife back to 1.12 r. Reverted. A script on the probe's own strip rule (width < 0.4 x median sqrt(2A) = 15.6 mm, aspect > 3, crease > 30 deg) puts the strip on the thigh's REAR wall (2 triangles, y -0.04..-0.08, crease 102 deg): the r24 rear half depth (0.064) makes the rear wall a narrow band.

## Stage 1 re-lock r25
- r25: Fix: rear half depth between the two tried values: 0.074 / 0.068 (r23 0.094: knife 1.07 r; r24 0.064: strip 1.1 r).
- r25 Result (LOCK b98b975f; s4 r25): knife PASS 0.52-0.54 r (max 100 deg), strip 1.05-1.09 r (min width 14.0 mm, same component).

## Stage 2 (on the r25 lock)
- r08: Fix: relax 1 pass x 0.5 (the 3-pass relax narrows the rear-wall faces the strip is made of).
- r08 Result (s4 r26): worse (knife 1.03-1.06 r at 122 deg). Back to 3 x 0.35.
- Thigh root status: the knife/strip pair has failed 3+ rounds running for the same reason (the rim fold vs the thin rear/inner wall faces trade off at ~1.0-1.1 r). Per WORKFLOW 6, stopped chasing it; best state = r25 lock + 3 x 0.35 relax: knife 0.52 r PASS, strip 1.05-1.09 r FAIL (14 mm wide, rear wall).

## Stage 3/4 colour + review rounds
- s3 r03: Critique: a dark 'flight' square on the back behind the wing root (junction crops C, s4 r01-r25). Diagnosis: station_of returned the FIRST station pair whose cut planes bracket the point; the tail stations' planes, extended, bracket points on the back. Fix: the bracketing span whose interpolated centre is nearest.
- s4 r27 (s3 r03 colour fix): the dark square remains (orbit az090/az270, hero): one flank face at the body's widest ring (x 0.126) passed the wing rule (x > 0.125) and took the flight colour. All kit gates PASS, glbcheck OK; junctions: wings/tail/eyes PASS, thighs strip 1.05-1.09 r FAIL (knife PASS). Separation PASS (legs 6.4 cm, tail-legs 22 cm, wing-torso 24 cm).
- s3 r04: Fix: wing colour rule from x > 0.138.
- s4 r28 Result: flank square gone (colour 7, all kit gates PASS).

## Stage 1 re-lock r26
- r26: Critique: thigh strip 1.05-1.09 r = the rear-wall quads between the rim and the transition ring, 14 mm wide (the ring sits only 35 % of the way to the thigh top). Fix: transition ring 50 % of the way (positions only).
- r26 Result (LOCK 6847c24f; s4 r29): thigh.L PASS (knife 0.53 r, strip 1.0 r); thigh.R strip 1.04 r (7 mm, the inner front rim: the relax pulls two inner-rim faces thin); r differs L/R (72 vs 69 mm, skin weights).

## Stage 2 (on the r26 lock)
- r09: Fix: relax 2 passes x 0.35 (the 50 % transition ring already spreads the rim).
- r09 Result (s4 r30): worse (knife 1.08-1.12 r at 130 deg, strip 1.01-1.03 r).
- r10: Fix: relax 4 passes x 0.35.
- r10 Result (s4 r31): thigh.L PASS (knife 0.55 r, strip 0.96 r); thigh.R strip 1.03 r: same mirrored geometry, but its root radius reads 67.4 mm vs 72.2 mm: the automatic weights are left/right asymmetric.
- s4 r32: Fix (rig): symmetric skin weights: every x < 0 vertex copies its mirror twin's weights with .L/.R swapped.
- s4 r32 Result: no change at all (thigh.R r still 67.4 mm vs L 72.2 mm, strip 0.96 / 1.03 r): the weights were not the cause; removed. The L and R root regions are mirror copies (live Mirror applied), so the 0.96 vs 1.03 r split is the probe's root radius reading differently per side (reported as a kit quirk).

## Final (s4 r33, lock 6847c24f37fd9da1)
- Kit gates: all PASS (s1 3700 tris, total 4596, 7 colours, slivers 1.7 %, posed fold-overs 0 %, hit/float/drift 0, z-fight 2), glbcheck OK; WARN 2 posed-clip tris (0.16 %).
- Junction probe: wings PASS (knife 0.92 r, max 100 deg), tail PASS, thigh.L PASS (knife 0.55 r, strip 0.96 r), thigh.R FAIL strip 1.03 r (the same mirrored geometry; the probe reads its root radius 67.4 vs 72.2 mm); eyes PASS 0.26/0.67/0.69, 13.6 % of head; membrane PASS p10 17.2 mm (floor 7.7). Separation PASS.
- Owner-style review (orbit18 + crops): fixed: groin slot, thigh rim knife, armpit knife under the wing, wing trailing-edge slivers, near-black palette, dark flank/back colour squares. Residual: the thin seam band on the thigh's inner/rear root (crop B, faint); wings read as thin bands in az000 (chord tilted 30-48 deg; the sheet draws them face-on); the fan tail is a thin spike from the side; head all gold (sheet: browner face).
- Deliverables: orbit18_sheet.jpg, side_by_side_sheet.jpg (reference | model), side_by_side.jpg (--compare), review/, rounds/s4_r33_junctions.jpg.
