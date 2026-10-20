# hippo (t7 hand box model, zoo workflow v2) — NOTES

Concept: refs/gpt/v3/hippo/sheet_1.png (2x2). `kit/refs.py --height 1.6` -> blueprint.json + reference/ (length 3.22 m,
width 1.40 m). Template: zoo/rhino/rhino.py (loft, 4 x 3 leg windows, grow() with the 45 % transition ring = leg-root
trick), elephant's greedy bridge_rows.
Identity cue (hippo, not rhino/pig): a huge low barrel on four very short thick columns; a massive WIDE SQUARE muzzle box
(flat top, flat sides, flat front, wider than the skull behind it), a steep stop up to eye bumps and small ears on the
skull TOP; a short flat tail. The S1 silhouette carries barrel, short columns, square muzzle, stop and ears.
Sheet notes: refs warns top width 1.23 m vs front 1.40 m; the top view is ~0.92 x the side scale overall (length 2.96 vs
3.22 m). Side wins for length; widths follow the front (the round barrel is the identity view), so top IoU stays ~0.8.
Technique: 14-vertex half rings (33 stations: tail 6 x 6-vertex, rump 2 + tail root, hind window 5, barrel 6, fore
window 5, neck 2, head 4 + muzzle 6), legs from 4 x 3 lower-flank windows, ears from 1 x 2 windows on the skull top.

## Stage 1
- r1: first fit. Gates PASS, 2,600 tris, IoU side/front/top 0.963/0.925/0.794. Reads as a hippo (square muzzle box,
  short columns). Critique: front overlay / az000 — the barrel is square-shouldered and too narrow low down: grey wider
  than the sheet at z 1.2-1.4, red outside grey at z 0.5-0.8; the sheet's barrel is domed on top and widest low (z 0.87).
  Diagnosis: BODY profile (rhino's) widest at fh 0.0 with a broad shoulder bevel. Fix: BODY re-placed from the front
  outline (fx 0.47 @ 0.90, 0.82 @ 0.55, 1.0 @ -0.13, 0.89 @ -0.58), barrel W +4 % (M2/M3 0.69).
- r2 result: front IoU 0.925 -> 0.962 (side 0.963, top 0.778: the plan view is 0.92 x scale, see sheet notes); 2,600
  tris; az000 barrel now domed and widest low. No new worst flaw in the clay views.
- r3 LOCK (no geometry change; edge sha 263edf6c...), then a minimal S2-S4 pass to probe the junctions (s4 r1, rhino's
  practice): legs PASS (fore knife 0, max concave 50 deg; hind knife 0.26 r), tail0 PASS (knife 0.75 r), eyes PASS
  (60 mm = 0.062 head; 0.49/0.75/0.58), ear membranes PASS; FAIL ear.L/R seam strip 1.87 r.
- r4 (lock deleted and re-made: a base change). Critique: ear crops A/B/C — the ear is a tall pointed spike (a horn, not
  the sheet's small round cup) and yellow needles sit at the root's front/rear corners. Diagnosis: E1 (rx 0.048) is a
  third of the 0.155 m window and the transition goes 70 % in / 20 % up: a thin creased band; E3/E4 taper to a point.
  Fix: the ear rings re-placed: broader root (E1 0.060 x 0.050), a short round cup with a blunt top (tip z 1.622), the
  transition sloping 45 % like the legs'.
- r4 result: the ear reads as a short round cup (crops), legs/tail/eyes unchanged; strip WORSE 1.87 -> 2.38 r: one 10 mm
  yellow band down the ear's outer transition side. Diagnosis: E1 (0.06 x 0.05) nearly fills the window (1 cm outer
  margin, rhino's lesson) and sits level with the rim, so the 45 % ring is a 1 cm sliver.
- r5 (lock re-made). Fix: E1 0.046 x 0.036 centred on the window (3 cm margin each side) and 4-6 cm above the rim; the
  cup flares to 0.058 above it (E2), blunt top at z 1.638.
- r5 result: every junction PASS (s4 r3): ear knife 0 (max 64 deg), strip 0.73 r; legs, tail, eyes, membranes as r1.
  IoU 0.963/0.960/0.778, 2,600 tris. LOCK r5: 1,302 verts, edge sha 45cf899081ee773b. S1 rounds used: 5 of 14.

## Stage 2
- r1: eye socket inset (logged). Critique: close-up 0 / hero — the eye sits flush in the flat skull side; the sheet's
  eyes stand on raised mounds above the forehead (front view). Diagnosis: the skull rings H1-H2 carry no eye mass.
  Fix: verts within 9 cm of the eye point raised 3 cm (falloff) along the head normal + up, before the inset.
- r1 result: PASS (slivers 0.3 %); the eye mounds show in top/az000. Critique: az000/hero — the muzzle top is one flat
  plate; the sheet's nostrils sit on two raised mounds at the muzzle's top front (x 0.19). Diagnosis: H7/H8 top verts
  flat. Fix: verts within 8 cm of the nostril point (0.18, -1.52, top) raised 2.2 cm (falloff), slightly forward.
- r2 result: PASS; nostril mounds faint but present (top/hero). Critique: hero — a collar ridge rings the neck behind the
  head (the head looks set into a collar). Diagnosis: F4 (BODY profile, domed) -> N0 (NECK prof 2.6) in one span: the
  section shape changes abruptly. Fix: N0 re-placed as the straight in-between of F4 and N1.
- r3 result: PASS; the collar is softer but a step remains (the sheet has a neck fold there; F3/F4 shoulder W 0.53
  over a 0.43 neck is the sheet's top view): kept, watched. S2 rounds used 3 of 6.

## Stage 3
- r1: pieces: small round lens eye (60 mm) + pupil disc; 4 toenails per foot (rhino's arched nail: the library has no
  hippo nail, `hoof_cloven` replaces the limb end). Paint: mid purple-grey skin #8f8191, pink #c69a9c on the belly
  (border = leg-window top loop BODY j9), jaw/throat (HEAD j8) and muzzle box (H4 ring loop + its top-plane loop), dark
  tail tip and nostril faces, nails #cfc6bc.
- r1 result: PASS, 3,192 tris, 5 colours. Critique: az090/hero colour — the belly pink is a thin strip on the underside;
  the sheet's pink covers the lower third of the flank (from z ~0.7 down). Diagnosis: belly border on BODY j9 (z 0.58).
  Fix: belly border one loop up, on BODY j8 (fh -0.35).
- r2 result: PASS. EEVEE (checks.py -> side_by_side_sheet.jpg, orbit18/): Critique: az90/az180 — the pink is one hard
  stripe from throat to rump, across the haunch and the rump's rear (az180 band); the sheet's pink is the belly
  between the legs, chest, throat and muzzle, the haunch/rump grey. Diagnosis: one fh rule along the whole loft (the
  tilted rump rings put fh off too). Fix: belly border j8 only between the leg windows (F0..B4 ring loops), chest j9
  ahead of them, haunch and rump all skin.
- r3 result: PASS; the pink now sits on the belly between the legs, chest, throat and muzzle; haunch/rump grey as on the
  sheet (side_by_side_sheet.jpg). The belly patch has vertical ends on the F0/B4 loops (a saddle-cloth read: watched).
  Critique: side_by_side_sheet az90/top — EEVEE renders the skin a pale lavender, lighter than the sheet's mid purple-
  grey. Fix: skin #8f8191 -> #7e7081, pink #c69a9c -> #b9888d.
- r4 result: PASS; EEVEE orbit18 now mid purple-grey with a pink muzzle/belly like the sheet; reads as a hippo from all
  18 views. Critique: orbit18 -45 az90 / bottom — the belly pink is a rectangle with square ends on the F0/B4 loops.
  Fix: the ring spans next to the legs (F0-M5, M0-B4) take the border one loop lower (j9): a stepped taper.
- r5 result: PASS (3,192 tris, 5 colours); the stepped ends read blocky (pixel steps) in az090.

## Stage 4
(s4 r1-r3 were junction probes of the build during S1, rhino's practice.)
- r4: full S4 with orbit + junctions. Every kit gate PASS (lock, glbcheck OK, techqa: hits 0, floats 0, z-fight 0,
  slivers 0.3 %, fold-overs 0, drift 0); junction probe PASS (ears knife 0 / strip 0.72 r, upperarm knife 0 / max
  concave 50 deg, thighs knife 0.26 r, tail0 knife 0.75 r); eyes PASS (0.58/0.76/0.49, 58-60 mm = 0.060 head);
  membranes PASS. Separation PASS (tail-hind 0.50 m, fore/hind L-R 0.26 m). 3,192 tris.
  Owner-style review (review/1_beauty.jpg, orbit18, crops s4_r04): (1) az090 — the belly pink is a stepped block
  (pixel steps at M0/M5), plus a second step at the chest; (2) a step ring at the neck behind the head (the sheet's
  neck fold, kept); (3) faint creases either side of the tail root (crops j4 A/B, red flags at the R0 -> Rt bridge,
  hardly visible); ear, leg, thigh roots broad and blended, no slit, fold, strip or poke in any crop; eyes small round
  lenses on mounds.
- r5 (fix round 1). Fix (1): belly + chest pink on ONE loop, BODY j9 (the leg-window top) from the neck to B4: one
  continuous border running into the leg tops.
- r5 result: PASS, junctions PASS; az90 belly is one continuous band from chest to hind leg on the j9 loop (orbit18).
  Remaining: eye R 58.0 mm = 0.060 of the head (the gate floor, measured with the ears in the head bbox).
- r6: re-run of r5 (the eye edit did not apply: a sed error); identical numbers, round OK.
- r7 (fix round 2). Critique: eye crops — the lens reads as a dark pin-dot at hero distance and sits on the size floor.
  Fix: lens radius 30 -> 33 mm (pupil disc 15 mm).
- r7 FINAL (fix round 2 result): all kit gates PASS (lock edge sha256 45cf899081ee773b..., glbcheck OK, techqa: hits 0,
  floats 0, z-fight 0, slivers 8 = 0.3 %, fold-overs 0, drift 0); 3,192 tris (body 2,604 incl. eye socket).
  Junction probe PASS: ear.L/R (knife 0, strip 0.72 r), upperarm.L/R (knife 0, max concave 50 deg), thigh.L/R (knife
  0.26 r), tail0 (knife 0.75 r); eyes PASS (66 mm = 0.068 head; front/3q/side 0.56/0.74/0.48); membranes PASS.
  Separation PASS (tail-hind 0.50 m, fore/hind L-R 0.26 m). Posed wire (review/4_posed.jpg): neck, legs and tail bend
  without collapse. --review, --compare (side_by_side.jpg), checks.py (orbit18_sheet.jpg, side_by_side_sheet.jpg) run.
  Residuals: (1) a step ring at the neck behind the head (F3/F4 shoulder over a narrower neck; the sheet's fold, but it
  reads a little like a collar); (2) faint creases either side of the tail root (R0 -> Rt bridge, red flags in the
  probe, barely visible); (3) top IoU 0.78 (the plan view is drawn at ~0.92 x the side scale); the rump reads as a plain
  dome from the rear without the sheet's split haunches; the pink border is hard-edged flat colour (style).
