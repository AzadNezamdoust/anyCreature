# raven_wyvern, setting c1 "carve + detail"

Stage 1 = carve_base (visual hull of reference/) for the torso, neck, head and legs, with the carve input redrawn
where a hull cannot work, plus hand-built parts grafted on with bmkit verbs (tail rings, wing branch).
Pattern: goblin (biped; head/neck graft by zip_rows) + wolf (mask redraw, keyed in carve_mask.key) + k3 raven_wyvern
(the wing as a shoulder strut with the membrane blade grown from its back face).

## Stage 1
- r01: carve_base defaults. PASS, 1130 tris, IoU side/front/top 0.718/0.844/0.796. Critique: the tail (the
  identity cue) is gone behind y ~0.5 (top-view width 2-5 cm = 1-3 voxels); the folded wings are slabs as deep as
  the whole body profile (a hull at x 0.3 takes the full side mask); horns are flat plates on the crown.
- r02: Fix (carve input + grafts): side mask cleared for horns, the wing below the belly, the tail behind y 0.42;
  front mask: wings cleared beside the torso (half width per z), horns above z 1.31; tail cut at y 0.30 by
  bisect_plane and zipped (zip_rows) to 8 hand rings out to a vertical spade fin; wing = a socket hole at the
  shoulder zipped to a ring chain socket -> elbow -> wrist -> blade -> tip. Result: FAIL, 2 non-manifold (a loose
  edge left by the hole delete), 6 hits (the chain folds back on itself at the wrist).
- r03: Fix: wing as k3 built it: socket -> wrist strut, the blade grown (extrude) from the strut's BACK face; loose
  edges removed; tail cut moved to y 0.14 (thicker rim, no bulge). PASS, 1208 tris. Critique: az000 torso skinny.
- r04: Fix: top mask clipped to a torso half width per y (the folded wings merge with the flank in the plan).
  PASS 1176. Critique: no wider: the sheet's plan view shows the chest only 0.16 wide (the wings hide the flank).
- r05: Fix: front (z 0.45-1.05) and top (y -0.8..0.15) masks FILLED to the torso half width (0.21-0.225), not only
  clipped. PASS, 1192 tris, IoU 0.819/0.64/0.695 (front/top IoU low on purpose: the blueprint's wings are traced
  as part of the torso outline; the wings now stand as their own blades). Reads as a two-legged bird-dragon with
  wing blades, long tail and fin from every view. Remaining (stage 2): blobby vulture head, slab wing, paddle fin.
- r06: lock (with orbit). 1192 tris, edge sha256 bc3a6f18a329468e.

## Stage 2 (lock edge hash bc3a6f18...)
- r01: face planes (bill tip hooked forward/down, lower mandible tucked, bill base pinched, eye socket inset 12 mm,
  brow out/forward, cheek out), fin trailing edge notched, colour-border cuts (bisect_plane logged as loops: bill
  base, pale bill tip, shank at z 0.30). Result: FAIL slivers 26 (2.0%): needle triangles on the wing blade
  (its long faces taper to the tiny tip ring).
- r02: Fix: tip ring scaled 2/3/3 (k3's fix). PASS, slivers 18 (1.4%), min IoU 0.947.
- r03: Critique: az090 the hull's throat is a vertical wall chin -> chest (no S-neck). Fix: throat verts between
  z 0.68-0.98 pulled back up to 7 cm (sine bump at z 0.83), neck narrowed 15% there. PASS, min IoU 0.939.
- r04: Fix: wing membrane: two cross loops on the blade (loopcut on its quad ring), the two trailing-edge verts
  raised 4 cm into bays (k3). PASS, 1320 tris. r05: final with orbit, PASS.

## Stage 3
- r01: sheet palette (colour_from_sheet clusters, a brief role takes the nearest sheet colour within dE 40:
  plumage #424653, shank #7c6f6d from the sheet; the rest brief), rule paint on the stage-2 loops (7 colours).
  Pieces: amber hex eye lens, swept horns, wrist thumb hook + 3 talons + hallux per foot (rooted by rays),
  3 finger spars on the blade, fin ribs, 13 graded dorsal spines with horn tips, 5 broad hackle wedges per side
  (throat and nape; fewer, larger, rooted). Result: FAIL hit 4 / z-fight 4 (spars), open edge (fin ribs crossed x 0).
- r02: Fix: thinner flat spars/ribs. Worse: slivers 4.6% (thin rods).
- r03: Fix: fin ribs dropped (sliver-prone on a 1 cm fin), spars staggered roots. Slivers 3.8%.
- r04: Fix: spars as triangular sections, one corner sunk (no face parallel to the blade), 7 rings. Slivers fixed;
  hit 2 / z-fight 6 at the wrist fold.
- r05: Fix: spar roots start 26-34% along (off the fold). PASS, 2202 tris, z-fight 2 (limit).
  Critique: the wing reads as one purple slab; the spars barely show (dark on dark-purple); fin plain.

## Stage 4
- r01: k3's rig and clips (no base S-neck: it is in the mesh). FAIL flips 0.64% (hackles 12), drift 4 (spars).
- r02: Fix: hackles rigid per shell (root weights), spars bind(body=). Worse: spar drift 6, stretch 35.
- r03: Fix: spars pinned to hand again, the wrist ring weighted to hand with the blade. Drift 6 (spars 4, hackles 2).
- r04: Fix: spar roots moved further out, hackle root weights averaged. No change: diagnosis: the blade's root
  faces span the shoulder socket (chest/arm) and the wrist (hand), so a wrist bend shears them under the spars.
- r05: Fix: the mantle turns the whole wing on the arm bone (hand straight on it), smaller (Z 30, roll 20; the
  sign flipped after the first try swung the blade into the flank, 22% clip). Spar drift 0; hackles drift 2.
- r06: Fix: hackles shorter (0.11-0.13) and broader. Still drift 2.
- r07: Fix: hackles back to bind(body=) (per vertex). PASS: flips 0.27% / 0.14% area, drift 0, clip WARN 0.96%.
- r08: final with orbit + glbcheck; --review; --compare. Over budget: stage 4 took 8 rounds (the wing's
  socket-to-wrist blade faces cost 4).

## Team repair pass (review/ad_notes_team.md, Fable 5.1, 5.5/10 FIX)
- r09 baseline (stage 4, no change): all gates PASS (hit 0, float 0, z-fight 2, slivers 0.8%, flips 0.27%/0.14%, drift 0).
- r10 (s2) must-fix 1, the wing slab. Critique: az090 the blade is a parallelogram slab shoulder -> past the hip; az000
  boards stand 6-9 cm off the flank. Diagnosis: the stage-1 diamond + tip ring sit low (front-bottom z 0.36, tip z 0.20)
  and at x 0.31-0.385. Fix: the blade verts mapped piecewise-affine in (y, z) (wrist kept; front-bottom -> under the
  shoulder, tip up/back beside the tail base), tucked in 4-6.5 cm. Result: FAIL IoU az000 0.835, top 0.846, bottom 0.788.
- r11 (s2) Fix: tip (0.30, 0.45) -> (0.26, 0.38), front-bottom (-0.45, 0.47), tuck top edge only 3.5 cm (taper alone
  gave 0.89 in the back views). PASS, min IoU 0.906. Partly: the owner-ratified IoU 0.9 caps the tuck, a gap stays in az000.
- r12-r14 (s3) Fix: each blade ring's outer/inner points slid up onto the arm-band border (top 36% of the blade
  height), paint dark above it, purple below; spars re-aimed from the wrist to the trailing edge. r12/13 diagnosis of a
  wrong paint: the rings are slanted, sorted by z instead (r13); root strut points count as arm (r14).
- r15-r16 (s3) Critique: spars short and buried at the root. Diagnosis: the root quad is non-planar (socket point at x 0.24
  vs 0.36), the render splits it the other way than the BVH. Fix: spars run to the last blade hit and ride the outermost of
  the quad's splits. Result: three spars radiate wrist -> trailing edge over purple bays; z-fight 0, hit 0.
- r17 (s4): PASS, flips 0.27%/0.14%, drift 0, z-fight 0, clip WARN 1.01%.
- r18 (s1) must-fix 2, STAGE-1 UNLOCK (the notes' named item: the legs). Critique: side pair, belly at 22% of height,
  the leg a stump. Diagnosis: the hull carries the sheet's short leg. Fix: the carved hull's z remapped in front of the
  tail cut (leg_z: feet kept to 0.035, 0.035-0.31 -> 0.035-0.46, torso 0.31-0.90 -> 0.46-0.90, head/tail/socket kept),
  leg_dy shears the shank back up to a hock at 0.34 (8 cm lean) and the thigh forward again to the belly. Gates PASS,
  1192 tris; blueprint IoU side 0.799 (the sheet's leg is shorter: the notes' choice).
- r19 lock: old lock renamed stage1_lock.pre_team.json; new lock e11f339996f57491. Kit snag (worked round in the
  program, kit untouched): the lock dumps META to JSON and a function in META['keep_valleys'] failed; it is now a
  callable str subclass.
- r20 (s4): FAIL s2 IoU side views 0.884: the stage-1 blade now hangs below the raised belly, so lifting it in stage 2
  shows in the side views too. r21-r24 (s2): wing lift reduced (front-bottom z 0.42, tip (0.24, 0.28)), shank colour
  cut moved to z 0.40 (the old z 0.30 cut sat on the hock: slivers 2.1%). PASS min IoU 0.902, slivers 1.7%.
- r25-r26 (s4): rig legs re-jointed on the new leg (hip 0.66, knee 0.48, hock 0.34 behind the foot, ankle 0.06),
  hips/chest raised. PASS flips 0.36%/0.21%, drift 0; move_f009/f017 feet plant.
- r27-r31 (s2+s3) must-fix 3, the eyes. Critique: head close-up, amber studs on the crown's front edge facing up.
  Diagnosis: EYE (z 1.232) sat 5 cm under the crown top (1.28); the socket face there faces up. Fix: EYE moved to the
  side of the head at the bill's top line (0.10, -1.115, 1.185); the socket inset lands on the side triangle; its top
  corner pulled 1.2 cm out and forward (brow ledge); the lens (25% larger, facing out and ~30 deg forward) sits on the
  stage-2 socket face, tucked under the ledge. Result: an amber eye under a brow on the side of the head; z-fight 0.
- r32 (s3) must-fix 4, hackles. Fix: 3 wedges per side at the throat only (11-12 cm long, 7 cm wide, rooted), nape
  wedges removed, colour 'ruff' #4e5262 (8th colour). Result: hackles clip 0, flips 0 (total flips 0.09%/0.07%).
- r33 (s2+s3) must-fix 5, the bill. Fix: tip ring 4 cm forward, 1 cm down, half width; tip point 1.5 cm further down
  (hook), mandible 2 cm forward; the pale border plane moved to the tip ring (front ~30% of the bill). IoU min 0.900.
- r34 (s2): wing tip z 0.28 -> 0.265 for IoU margin (min 0.902).
- r35 (s4, should-fix): attack lunge longer (neck0 26, neck1 20, chest 11 at f20). PASS, clip WARN 6 tris (0.22%).
- Not done (should-fix): fin rays, spine grading/lean, cheek/chest flatten.
- Partly (must-fix 1): the taper and the tuck are capped by the s2 IoU > 0.9 gate (measured against the re-locked
  stage 1, whose blade is unchanged): tip raised 6.5 cm / back 9 cm (asked ~30 / 15), top edge tucked 3.5 cm (asked 5).

## Team repair, second pass (review/verify_team.json: must-fix 1 and 2 PARTLY)
- r37 baseline (stage 4, no change): all gates PASS, lock e11f3399.
- r38 (s1) must-fix 2, STAGE-1 UNLOCK again (the same named item, the legs). Critique: az090, the belly reads at 28-30%:
  the stage-1 blade (front-bottom z 0.36, tip 0.20) hangs below the raised belly and hides the leg top, and the belly
  itself was 0.46. Diagnosis: the blade is built from fixed points after the hull's z remap, so it did not rise with
  the torso. Fix (stage 1, only this): LEG_B1 0.46 -> 0.50 (belly at 0.501 = 36% of 1.4 m), WING_BLADE z raised with
  the torso (diamond 0.74/0.62/0.525/0.635, tip ring +0.12 z, +0.05 y); x, head, tail, socket, feet kept. Gates PASS,
  1192 tris.
- r39 lock: old lock renamed stage1_lock.pre_team2.json (pre_team.json is the first one); new lock c030dd88.
- r40 (s2): the wing map re-based on the new blade (FB (-0.45, 0.53), TB (-0.02, 0.74), tip (0.27, 0.37)); with the
  lift now in stage 1 the top-edge tuck goes to the asked 5 cm. A plan-view convergence of the blade on the tail
  (WING_CONV) fails IoU (top/bottom 0.82-0.87 at 4-10 cm): left at 0.
- r41 (s4): PASS. Packet az000: the boards still stand off, daylight below the shoulder strut.
- r42 (s2) must-fix 1, the daylight. Diagnosis: the leading edge drops straight from the wrist (x 0.30) while the
  flank is at x 0.21. Fix: the blade's front-bottom corner 12 cm in (x 0.245), and the strut's front lower shoulder
  point slid down the flank to z 0.66 (a web from the flank to the wrist; both points and a lower z gave
  self-intersections with the flank). Shank colour cut 0.40 -> 0.47 (the dark thigh read as belly). Result: PASS, min
  IoU 0.901; az000: the wing's inner face meets the flank from the shoulder down to z ~0.6.
- r43 (s3/s4): the web painted plumage (it is the arm). PASS: flips 0, drift 0, slivers 1.1%, clip WARN 4 tris.
- r44 final with orbit, --review, --compare.
- Must-fix 2: done (belly 0.50 m = 36%, shank grey to 0.47, hock visible, move_f009/f017 feet plant).
- Must-fix 1: partly. Taper, dark arm band, purple bays, three spars, tip beside the tail base, top edge tucked 5 cm,
  inner face on the flank down to z 0.6. Left: the wing tips hang ~10 cm off the thighs below that (the s2 IoU > 0.9
  gate, owner-ratified, caps a plan-view convergence; it needs a stage-1 blade change, which the notes did not unlock).
