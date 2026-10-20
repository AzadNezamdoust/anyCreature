# stag (t7 hand box model) — NOTES

Technique: wolf_base's t7 look. One spine loft of 6-vertex half rings (tail tip -> nose, 20 sections read off reference/side.png as top/bottom seam points, W from the front view), legs extruded from 2-face lower-flank regions, ears and antler main beams extruded from 1-face skull regions; tines, neck mane and eyes are stage-3 pieces.

Stage 0: blueprint.json traced from reference/sheet.png with kit/refs.py (height 2.0 m incl. antlers). The sheet draws the plan view 1.13x the side scale (refs.py warning), so the top outline was scaled x0.885 by hand. The tail hangs: its three rings run from the rump end down, kept behind the rump surface.

## Stage 1
- r1: first fit. Gates PASS, 812 tris, IoU side/front/top 0.754/0.674/0.764.
- r2: Critique front/side overlay — the antler beam rises as one steep spike; the ref beam runs out nearly level then sweeps up. Fix: BEAM re-fit (out to x 0.30 at z 1.67, then up to 1.97), thicker. IoU 0.760/0.697/0.756.
- r3: Critique az000 — ears small flat flags; ref ears are big leaves pointing out and up. Fix: ear mid section wider (dz 0.068), tip out to x 0.36, z 1.585. IoU 0.761/0.707/0.754.
- r4: Critique az090/az000 — the legs are sticks next to the ref's. Fix: fore and hind sections thicker (forearm rx 0.06, gaskin 0.06/0.085). IoU 0.765/0.711/0.753.
- r5 (LOCK): 408 verts, 812 tris, edge sha256 acefa5caa0519690. Remaining IoU gap is the tines (stage 3) and the staggered leg pairs of the ref side.

## Stage 2
- r1: elbow, stifle and neck rings; eye-socket inset in the H0b-H1 stop face, brow corner, flat muzzle planes, slanted nose pad. FAIL: the loops and inset were not wrapped in topo() (unlogged vertices).
- r2: wrapped in topo(). Gates PASS, 896 tris, min IoU vs s1 0.999, slivers 1.1%.

## Stage 3
- r1: paint along existing loops (rufous coat, dark neck mane/chest and legs, cream belly band, rump patch, chin, inner ear; black hooves and nose; antler brown), small dark lens eyes, 8 mane clumps/side, 4 tines/side. FAIL: 1424 tris under the 1500 floor.
- r2: 4 more crest/throat clumps and 2 more tines. PASS, 1664 tris, 6 colours. Critique: the cream underline climbs onto the shoulder behind the mane.
## Stage 4
- r1: belly band limited to y > -0.2, z < 0.72; rig 14 bones + .R mirrors, idle / move (trot) / attack (antler lowering thrust). FAIL drift 7 shells (tines bound rigid to head while the beams were auto-weighted across head/ear/neck).
- r2-r3: beams forced to the head bone, tines rigid on head: tines clean; 2 mane shells still drift.
- r4: tried the neck clumps rigid on the neck bone: worse (8). Reverted.
- r5: dropped the two lowest brisket clumps (they rode the upper-arm swing). All gates PASS: 1584 tris total, hit/float/zfight 0, slivers 1.8%, drift 0, lock OK, glbcheck OK; clip warning only (0.74%).

Checks: orbit18_sheet.jpg (8 azimuths, top, bottom, 4 at +45, 4 at -45; EEVEE) — every view reads. Fusion on the rest pose (bone-group vertex gaps): tail to hind legs 0.26 m, fore L/R 0.19 m, hind L/R 0.16 m: nothing fused. side_by_side.jpg: sheet views next to the matching model views.

Weaknesses: one symmetric pair per leg where the ref side staggers them; antler is a 4-sided beam with 6 tines per side, sparser than the ref crown; ears read large and pale from the front; slivers near the 2% limit.

## Fix pass (reviews fable 7 / opus 7)
Merged list, shape first: (1) antlers thin flat sticks, tines short and disconnected, all one side; (2) neck mane a noisy cluster of small spikes; (3) legs spindly, no hock angle; (4) orbit sheet had blank bottom / -45 views.
- Base change, stage 1 re-locked: hind leg re-cut with a reverse hock (hock moved back to y 1.06, cannon drops forward to the hoof), fore and hind sections ~10% thicker, antler beam ~1.35x thicker. LOCK: 408 verts, 812 tris, edge sha256 7fbd1c60088b025a, IoU 0.769/0.732/0.736. The 3-sided beam (fable) was not taken: the sheet beams are round and thick (opus fix).
- Stage 3: mane 10 small clumps -> 5 large flat wedges. Tines thicker and longer (6 per side), roots sunk in the beam, alternating out/in of the beam plane. r6 FAIL hit (2 tine roots through the thin beam end: root depth -> 0.45 r0); r8 FAIL slivers 4.3% (6-sided long tines: back to square, 4 bands); r9 PASS.
- Stage 4: all gates PASS, lock OK, glbcheck OK; clip warning only (0.58%). Separation PASS: tail-hind 27 cm, fore L-R 18 cm, hind L-R 15 cm.
- checks.py / checks_blender.py rebuilt on the crab template: ground removed and low views rendered last, so bottom and -45 views now render in colour. before_after.jpg added.
- Triangles: stage 1 812, total 1576.
Not fixed: tines are straight spikes (the ref's curve); one symmetric leg pair per side.

## Fix pass 2 (reviews fable 8 / opus 7)
Merged list, shape first, concept sheet as referee: (1) torso a straight tube (opus): chest drop and rump rise; (2) head small for the antlers (fable); (3) cannons thin (fable); (4) antler thicket (opus): 5 tines per side, beam thicker; (5) mane bib too deep (fable, shape half only; the colour lift was skipped, the sheet mane is dark brown); (6) rump patch a hard rectangle (opus).
- Base change, stage 1 re-locked: C0/C1 bottom 0.58 (chest drop), R1/R2 top +0.03 and belly tuck at W0/R2, H0-Hk W 0.135, H0b 0.13, H1 0.095, fore/hind cannon ring +0.008, beam 1.15x. LOCK: 408 verts, 812 tris, edge sha256 2829f212ba9794fa, IoU 0.765/0.746/0.731.
- Stage 3: smallest crown tine dropped (5 per side); mane wedge length x0.55; rump patch an ellipse round the tail; ear paint threshold moved out with the wider skull.
- Stage 4: all gates PASS, lock OK, glbcheck OK, drift 0, slivers 1.1%, clip warning only (0.49%). Separation PASS (tail-hind 27 cm, fore 18 cm, hind 15 cm). Total 1504 tris.
- before2/ holds the pre-pass hero, orbit and side-by-side; before_after2.jpg added.
Not fixed: rump patch still follows the coarse ring faces (reads blocky at az180); tines still straight; mane still busy from the front.

## Poly pass 3 (owner: denser main mesh, same t7 technique)
- Body loft: 20 -> 35 stations (new: tail root, rump round-over, hip, flank, belly, girth, chest, shoulder, brisket, neck base, throat, nape, stop, muzzle side, nose), heights and belly line re-read off the side trace; half rings 6 -> 10 vertices (rounded points on back, upper flank, lower flank, belly). Legs: root 3x2 faces, 10-vertex round rings, 9 sections (forearm, knee knob, slim cannon, gaskin). Beam: 6-vertex round ring, radii x1.2.
- Stage 1 re-locked (r34; earlier locks in before3/): 1078 verts, 2152 tris, edge sha256 8dc013efaa45b18e, IoU 0.761/0.749/0.741 (was 0.765/0.746/0.731).
- Stage 2: elbow, stifle, neck rings re-aimed at the new rings; new knee and hock rings; eye socket in the lower stop face; muzzle flats cover the new muzzle stations. Stage 3: tine root ring 0.75 r0 (r33 FAIL hit: 2 tine roots through the round beam).
- Stage 4 r35: all gates PASS, lock OK, glbcheck OK, slivers 1.3%, drift 0; stretch/clip warnings only. Separation PASS (tail-hind 26 cm, fore 17, hind 15).
- Tris 1504 -> 2972: body 896 -> 2364, details 608 unchanged (100% of the increase in the body). before3/, before_after3.jpg, orbit18_sheet.jpg, side_by_side.jpg rebuilt.

## Poly 2x review: REVERT (mild)
Review: the 2x pass lost the faceted torso muscle planes (a generic tube) and added nothing that reads. Reverted to before3.
- pass3/ keeps the 2x-pass hero, orbit18, side_by_side, lock and program (stag_poly.py).
- stag.py and stage1_lock.json restored from before3/ (20 stations, 6-vertex half rings, 6-section legs, square beam). Stage 1 r36: matches lock (408 verts, 812 tris, edge sha256 2829f212ba9794fa), IoU 0.765/0.746/0.731.
- Stage 4 r36: all gates PASS, lock OK, glbcheck OK; clip warning only (0.49%). Separation PASS (tail-hind 27 cm, fore 18, hind 15). Hero render pixel-identical to before3.
- Tris 2972 -> 1504. orbit18_sheet.jpg, side_by_side.jpg rebuilt; before_after4.jpg = before3 | 2x pass | now.

## Fix pass 9 (owner: keep the dense mesh, fix its problems inside it)
- before9/ holds the pre-pass (low-poly revert) hero, orbit18, side_by_side, program and lock.
- stag.py restored from pass3/stag_poly.py (35 stations, 10-vertex half rings, 9-section legs, round beam; tine-root and eye fixes kept).
- Review WORSE item (torso lost its faceted muscle planes, a generic tube): torso, neck and tail half rings now put their 4 in-between points ON the old facets (linear midpoints) instead of Catmull-Rom bulges, so each old facet is a co-planar pair of faces and every old vertex stays a crisp ridge. Head rings keep the rounded points (eye, brow and muzzle unchanged).
- Stage 1 re-locked r37: 1078 verts, 2152 tris, edge sha256 c8e5692f70240a7e, IoU 0.761/0.752/0.741.
- Stage 4 r37: all gates PASS, lock OK, glbcheck OK; stretch/clip warnings only (clip 0.41%). Separation PASS (tail-hind 26 cm, fore 17, hind 15). Orbit: no holes, specks or slits at leg, ear, neck or tail junctions.
- Tris 2972 (2x level). orbit18_sheet.jpg, side_by_side.jpg rebuilt; fix9.jpg = before9 | after hero plus torso and shoulder close-ups.
