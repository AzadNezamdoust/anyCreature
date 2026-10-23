# manta_ray (t7x zoo, wave-new) — NOTES

Sheet: refs/gpt/v3/manta_ray/sheet_1.png, refs.py --height 0.55 (span ~2.5 m, length 2.94 m with the whip tail).
refs warnings: front rescaled 1.16x and rear 1.64x to the side height (the sheet's views disagree on scale; the
top plan has a shorter, more swept span than the front). Side view wins for proportions.
LIFT: blueprint.json is the floor trace moved up rigidly by +0.45 m in z (original kept in
reference/blueprint_traced_floor.json) so the manta swims off the floor; the model is built at the same lift.

Identity cue: a wide flat diamond of wings that grow out of a domed body with broad thick roots, two forward
cephalic lobes curling in front of a wide terminal mouth, a thin whip tail, small dorsal fin, dark back / white belly.
Not a stingray (no round disc, no thick tail), not a bird (no neck, no separate wing arm).

Build plan: 12-vertex half-ring spine loft (mouth -> rear body, 22 stations, 7 cm apart) + 6 -> 3 vertex tail
whip; wings = the equator faces under the whole root opened and bridged out section by section (a hug ring,
then constant-span airfoil slabs with fewer chord segments towards the tip, rim vertices at the leading and
trailing edge = the colour-border loop); lobes = a 3-face region on the head's front corner extruded along a
curled path; dorsal = 4 top-seam faces extruded.

## Stage 1
- r00: first build. PASS gates, 2026 tris, IoU side 0.889 / front 0.722 / top 0.917.
  Critique: (hero, az045, top) the body reads as a fat round capsule with the wings butted into a 13 cm slot at
  its mid flank: a steep dome side (55 deg) meets a flat wing top in a crease along the whole root; the sheet front
  has a low roof sloping into ~0.2 m thick wing roots.
  Diagnosis: 12-ring superellipse dome (pu 2.4) too round at the side; root region only faces 5-6 (13 cm);
  wing sections 0.095 -> 0.02 thick (sheet front reads ~0.2 at the root, ~0.1 at mid span).
- r01: Fix: explicit roof profile (UPPER/LOWER tables), root region v4..v8 (4 faces, ~0.2 m), the hug ring and
  sections carry 3 rim vertices at the root ends, wing thickness 0.15 -> 0.022, camber 0.15 t.
  Result: better: the dome slopes into the wing with no crease (hero); front IoU 0.722 -> 0.814; side 0.889,
  top 0.912; 1938 tris.
- r02: Critique: (top) the lobes are straight prongs; the sheet's plan shows a "C" pair curling in to x ~0.06 in
  front of the mouth. Diagnosis: LOBE path x stayed 0.2-0.24 to the tip. Fix: path curls in to x 0.08, lower edge
  rolls in (curl 0.02-0.055). Result: better (top view hooks), side 0.877, top 0.920, 1938 tris.
- r03: Critique: (front overlay) wings read as thin sticks at mid span; the sheet front band is ~0.1 deep there.
  Diagnosis: WING thickness 0.112-0.026 and a flat chord. Fix: thickness 0.125 -> 0.028 plus a nose-up chord pitch
  (0.06 x span left). Result: better, front IoU 0.814 -> 0.827, 1938 tris.
- r04: Critique: (side overlay) the lobe scroll stops short of the sheet's C (front y -1.47, bottom z 0.03).
  Fix: LOBE levels 2-6 further forward and lower. Result: side 0.877 -> 0.890, top 0.909.
- r05: Critique: (top) no pelvic fins: the sheet's plan has two small flaps by the tail root. Fix: grown from faces
  4..7 of the R0-R1 span, two levels out/back. Result: present in top view; 2018 tris; IoU 0.890/0.827/0.912.
- r06 LOCK (orbit + --junctions): 1011 verts, 2018 tris, edge sha256 226b398289f3c08b. IoU 0.890/0.827/0.912.
  Orbit holds. Junction probe at S1: no rig yet, eye FAIL (no lens until S3) -> roots measured at S4 (re-open the
  lock if a root fault shows there, logged here).

## Stage 2
- r01: one logged change: the eye socket (inset 0.30 of face 4 of the H1-H2 span, floor 8 mm in), kept as a valley.
  PASS: lock assert, IoU vs S1 1.0, tech QA hit/float/zfight 0; a few slivers at the wing tip cap. 2034 tris.

## Stage 3
- r01: paint (back #47505a, belly #e8e7e2, fin/tail #3a4149, mouth #2a2e34, eye #0e0f11 = 5 colours; the border is
  the wing rim vertex loop and the body equator loop: faces above dark, below white) + lens eye (8-sided, r 19 mm,
  9 mm proud, bound later with body weights). PASS, 2098 tris.
  Critique: (az000 colour) the head front reads as a grey box; the sheet front has a white chin under the mouth.
- r02: Fix: head-front faces below the mouth line -> belly. Result: white chin band in az000. PASS.
- r03: Critique: (hero colour) lobe paint by n.x alone gives stripes on the curled plate. Fix: inner = faces turned
  to the C's centre (0.13, -1.27), top/bottom edge faces by n.z. Result: small change at this size; re-check in S4
  close-ups. PASS, 2098 tris.

## Stage 4
- r01: rig (root/chest/head trunk, tail0-2 with a short tail0, wing.L + wing1.L from the root, lobe.L + lobe1.L
  from the head; roll auto, wing flap = local Z, signs checked on attack@8: both tips up) + clips idle 48 / move 32
  (root->tip wave, body heave) / attack 32 (wind-up, power stroke + lunge, lobes flare). Kit gates PASS (glbcheck,
  tech QA 0, slivers 32 = 1.5%). Probe: wings PASS (knife 0, max 50 deg; membrane p10 37 mm vs 11.7 floor);
  FAIL lobes strip 1.15 r, tail0 strip 4.5 r, eyes front 0.08 + size 0.059 head.
  Critique: (eye crops) the lens hides behind the lobe root from the front and is too small.
- r02: Fix: socket one span back/out (H2-W00 face 4), lens r 23 mm, looking forward. Result: eyes PASS
  (0.34/0.70/0.58, 0.071 head); lobes/tail unchanged.
- relock 1 + r03: Critique: (tail0 flags A/B) a yellow needle band at the rear flank. Fix tried: 12->6 n-gon bridges
  as walked quads/triangles. Result: no change (strip 4.5 r) -> the band is the rear 12-rings' 8 mm equator faces.
- relock 2 + r04: Fix: R2/R3 as 6-vertex rings (12 -> 6 walked at R1-R2). Result: tail0 PASS (strip 0); 1970 tris.
- r05: Critique: lobe strip = 2.8 mm needles in the mouth-floor fan (thin.py on the GLB: lip v6-v8 near collinear).
  Fix tried (S2): lip corner out 15 mm. Result: worse (knife 1.24 r at the creased lip edge) -> reverted.
- relock 3 + r06: Fix: mouth recess 25 -> 6 mm (lip edge no longer a crease). Result: ALL GATES PASS, junction
  probe PASS on all 7 roots, eyes PASS (0.34/0.70/0.58 and 0.38/0.76/0.63). Lock edge sha e7d8... superseded:
  see stage1_lock.json. 2050 tris.

## Owner-style review (orbit18_sheet.jpg, face_34, s4_r06 junction crops)
Reads as a manta from every view, swimming 0.45 m off the floor. Junction crops: wing roots broad, no slit/knife/
strip; tail root clean; lobe roots clean. Visible flaws: (1) the near lobe's outer face has a hard white block
(face_34) = colour stairs; (2) the head front is a flat vertical wall (az0); (3) blunt wing-tip caps vs the sheet's
swept points.
- f1 (S3/S4 r07): lobe paint: white only on faces turned to the C centre or facing straight down. Result: no change
  (face_34 identical) -> the block came from the chin rule (x < 0.21, facing forward, low) catching the lobe tips.
- f2 (r08): chin rule limited to the head-front plane (-1.105 < y < -1.07).
- f3 (r09): Critique: (az0, face_34) the head front is a flat vertical wall. Fix (S2 moves): front ring v0..v3 back 25 mm, v0..v2 down 12 mm (sloped forehead).
  Result (S4 r09, final): ALL GATES PASS (S1 shell/closed/no self-intersection/budget, lock assert, S2 IoU vs S1,
  S3 colours 5, glbcheck idle/move/attack, tech QA hit/float/zfight/drift/fold 0, slivers 0.8%); junction probe PASS
  on all 7 roots (wing L/R knife 0 / max 50 deg, membrane p10 37 mm vs 11.7 floor; tail0; lobes), eyes PASS.
  Lock edge sha 83c27f43c719d391 (relock 3). Rounds: S1 10 (r00-r09 incl. 3 relocks), S2 1, S3 3, S4 9 (4 + junction
  relock checks + 3 fix rounds).
Residual (visible, fix budget used):
1. Lobes are flat boxy plates: the sheet's rolled scroll / C in the side view reads as a paddle (az090, face 3/4).
2. Wings read thinner and flatter than the sheet front (no strong tip curl-up), tips blunt caps not swept points.
3. Head front / mouth: a shallow painted slot (6 mm recess), the sheet has a deep open mouth with a white lip.
Outputs: orbit18_sheet.jpg, side_by_side_sheet.jpg (checks.py), side_by_side.jpg (--compare), review/,
rounds/s4_r09_junctions.jpg.

## Weakfix 2026-10-23 (night, backup before_weakfix/)
- s4 r10. Critique: (face 3/4, az090) the cephalic lobes are flat boxy vertical plates; the wing tips are blunt caps; the sheet renders put the ground under the belly so it read as lying on the floor. Fix (stage 2 vertex moves, lock kept): each lobe cross-section placed as a J-scroll (straight outer face, the lower edge rolled in and up, ROLL per level); wing x > 0.95 narrows, sweeps back 10 cm into a point, tip +3.5 cm up, span +7 cm; checks_blender ground at the real z 0.
- r10 result: FAIL s2 46 self-hits + slivers 2.5 % (the rolled lobe's inner side crosses itself), lobe junction knife 1.44 r / poke 14; clip gate FAIL move/attack pen 3.9/5.2 % H (the longer tips dip under the rest floor in the flap). Top view: tips now swept points, lobes read as C hooks.
- s4 r11. Fix: gentler roll (ROLL 0.2-0.85, R 5 cm, rolled edge 30 % thinner), no span extension, tip curl +5 cm.
- r11 result: still FAIL s2 22 hits at (0.23, -1.11, 0.63-0.71) = the lobe's first level crossing its head root; slivers 2.2 %; lobe junction knife 1.44 r, poke 10; clip gate PASS (no span extension fixed the flap dip).
- s4 r12. Fix: ROLL[0] = 0 (the root level stays a plate), level 1 0.45.
- r12 result: still 22 s2 hits, now at y -1.19 (between lobe levels 0 and 1) -> the cause is not the roll: scroll_pt put the 'r' side at -n (the original lobe_place has 'r' at +n), so every level was mirrored through its centre plane and the lobe twisted between the head root and level 0.
- s4 r13. Fix: side sign corrected.
- r13 result: s2 hits 22 -> 12 (now where the rolled lower edges of levels 1-3 cross as the lobe path turns in plan, z ~0.53); lobe junctions PASS (knife 0.52 r, slit 0); slivers 2.2 % FAIL (body 46 vs champion 16); clip gate PASS.
- s4 r14. Fix: ROLL max 0.55; wing-tip chord squeeze 0.5 -> 0.3.
