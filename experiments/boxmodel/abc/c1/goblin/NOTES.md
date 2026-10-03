# goblin, setting c1 "carve + detail"

Stage 1 = carve_base (visual hull of reference/) for the body, legs and arms, plus hand edits: the hull's head is
replaced (the hull fused the long ear blade and the skull into a shelf over the shoulders and read the face as a hood).

## Stage 1
- r01: carve_base defaults. 1126 tris, IoU side/front/top 0.913/0.868/0.876. Critique: the head is a hood with a beak,
  the ears a flat shelf over the back (az090/az180); body, legs and arms read. Fix: replace the head.
- r02: Fix: bisect at a neck plane, hand-built 8-point head rings H1-H11 zipped to the cut rim. Result: FAIL 32
  intersections (the hull's chin below the plane survives; the zip folds).
- r03: Fix: delete hull faces above a side-view cut line (chin, head, ear shelf). Result: 18 hits: the rim spans the full
  shoulder width (x 0.2), the resampled neck ring folds against the jaw ring.
- r04: Fix: a narrow hand neck ring (half width 0.088) above the wide rim (the zip band is the trapezius slope), cut line
  lowered at the neck, jaw-side points of H1 raised. Result: PASS, 0 hits, 1128 tris. No ears yet.
- r05: Fix: ears extruded from the two side faces H6-H8 P4-P5, four lens sections to the tip. Result: PASS; front IoU
  0.796 -> 0.845; but top view: ears swept back ~55 deg (the side view's tip y 0.29) read as wings; top IoU 0.742.
- r06: Fix: ear tip to (0.44, 0.17, 0.955) (~35 deg back, the front and top views' sideways ear; side view loses
  length, noted: the generated sheet's side and top views disagree), mid section taller (0.095).
- r06 result: top view still reads the ears swept back ~50 deg (wings); top IoU 0.749.
- r07: knob plan_roundness=2.5 to round the box flank. Result: FAIL closed (a seam fin, 3 open edges) and the flank
  barely changes. Reverted.
- r08: Fix: ear tip to (0.45, 0.09, 0.955): sideways with a slight back sweep, as the front, rear and top views show.
- r08 result: ears read sideways in front/rear; PASS, 1214 tris, IoU 0.85/0.847/0.765.
- r09: Fix: the back-top corner pulled onto a quarter ellipse (hunch). Result: no visible change: the hull back is
  already round; the flat "table" in az090/az000 is the shoulder tops at neck height. Kept (harmless).
- r10: Fix: shoulder tops (x > 0.09) pressed onto a trapezius slope z = 0.76 - 0.8 (x - 0.08).
- r10 result: PASS; the collar shelf is lower, but hero shows the real problem: the arms are slabs 0.16 deep (the
  torso's side-view depth) and 0.06 wide, so they read as a cape.
- r11: Fix: arm vertices (x > 0.19, or > 0.26 below the knee) squeezed to half depth about the arm's centre line.
- r11 result: PASS; az090 now shows a thin arm hanging forward of the torso; hero still a wide sack torso and a
  T-shirt collar shelf around the jaw (az000).
- r12: Fix (upper-body proportion): trapezius slope lowered to z = 0.72 - (x - 0.08); torso between hips and armpit
  narrowed to 86% in x (more gap to the arm in front view).
Lock: r13, 1214 tris, edge sha256 70471d60241baeef, IoU vs blueprint 0.847/0.819/0.753 (ears turned sideways on purpose).

## Stage 2
- r01: grin loop in band H2-H3 (front pushed in 0.028, lip corners climb), hooked nose tip down + nostril flare,
  angry brow (inner brow down, ring forward), cheekbone and jaw corner out, eye-socket inset, pot belly forward.
  Result: PASS, min IoU 0.975, slivers 22 (1.7%), 1258 tris. Clay reads beak + brow; the face needs eyes/teeth/colour.

## Stage 3
- r01: paint by rules + 3-pass majority filter (mouth, inner ear, belly, cloth, skin); belt ray-cast onto the hull in
  the tilted belt plane; brass buckle; front/back tattered flaps; hex eye lens + pupil in the socket; upper teeth row,
  lower corner fangs; 3 curled fingers + claws per hand; 3 toes + claws per foot.
- r01 result: FAIL hit 1 (the belt cuts the lumpy hull at the back of the skirt), slivers 3.2% (the eye lens was
  degenerate: the inset face's normal was stale, zero).
- r02: Fix: belt columns step out 5 mm until no band face cuts the skin (two back columns +35 mm); socket normal
  refreshed. Result: PASS, slivers 28 (1.2%), 2390 tris. Critique: the eyes sit behind the socket rim, invisible at
  hero/az000 size (the reference's big yellow eyes carry the face).
- r03: Fix: lens 5 mm prouder (front of the pupil 23 mm off the socket floor), radius 0.027 -> 0.031.
- r03 result: PASS; az000 now reads goblin (yellow eyes under an angry brow, hooked nose, toothy grin, ears with a
  light inner face, belt + buckle, tattered cloth). Critique: hero shows the dark mouth band running back under the
  ear like a strap (MOUTH took every slot face with y < -0.10); the reference grin ends at the cheek.
- r04: Fix: mouth faces only where y < -0.165 (the lip corner), the rest of the slot stays skin as a crease.
- r04 result: PASS; the dark band left in hero is the slot's shading, not paint (acceptable: it reads as a wide grin).

## Stage 4
- r01: k3's rig and clips, joints moved onto the carved legs/arms (J). Result: FAIL flips 22 (0.92% tris, 1.2% area:
  body 19 at the arm/flank junction, belt 3), drift 2 (fingers); stretch 27 (forearm, teal), clip 56 (warn).
- r02: Fix: arm-bone rotations at 60% (the hull arm hangs 2-4 cm off the flank and shares its heat weights).
- r02 result: no change (21 flips). Diagnosis (GOB_DBG flip dump): every flip is on the hand's inner face
  (x 0.25-0.27, z 0.21-0.32), in move/attack frames where the thigh swings: the hand hangs beside the knee and took leg
  heat weights; the fingers' root weights (finger_rigid) inherit it -> drift.
- r03: Fix: arm_clean(): hand/forearm vertices (|x| > 0.25, z < 0.42) drop leg/hip weights, renormalised to arm bones.
- r03 result: worse (62 flips): the |x| > 0.25 box also caught the feet. Narrowed to the hand: still 30, so not leg
  weights. Dropped arm_clean.
- r04: Fix: smooth_weights(): 10 passes moving each vertex's weights halfway to its neighbours' mean (the carved
  mesh's irregular triangles gave weight jumps across the thin wrist faces). Result: flips 11 (0.46% tris, 0.54% area:
  still over on area), all in attack f006 (the chest twist swings both hands) plus one skirt face; drift 2 (fingers).
- r05: Fix: attack chest twist 18/16 -> 10 deg; fingers shortened (0.045+0.03 -> 0.036+0.026) so their tips are
  nearer the palm than the foot top (the drift anchor).
- r05 result: flips 10 (0.42% / 0.55% area), drift 1. r06 (hand.R counter-bend at attack f7 dropped): no change.
  Diagnosis (GOB_DBG weight dump): the right hand's verts carry thigh.R 0.18-0.28 + shin.R 0.1 (heat bleed from the
  knee beside it), so the chest twist pulls the hand against the leg.
- r07: Fix: arm_clean (hand/forearm |x| > 0.25, 0.11 < z < 0.42 drop leg/hip weights) BEFORE the weight smoothing.
- r07 result: drift 0, but flips 22. Diagnosis (mesh walk on carve_base.json): the carved hand/forearm is FUSED to the
  knee by a web of faces at z 0.2-0.3 (the occupancy blur closed the ~3 cm front-view gap between forearm and knee).
  No stage-2/4 weight trick can bend a web; it is a stage-1 defect.

## Stage 1 re-lock (logged: the r13 lock is deleted, backup kept outside the folder)
- r14: Fix: carve knobs mask_blur 3 -> 1, blur 1 -> 0: the hand walks up the arm without reaching the leg (mesh walk:
  the hand's component below z 0.6 never comes nearer than x 0.20). PASS, 1122 + head = 1122 tris (body),
  IoU 0.851/0.817/0.754; the silhouette is the same, slightly crisper. Over the 14-round stage-1 budget by one (the lock).
Lock: r15, 1122 tris, edge sha256 78576a9075a21571.
- stage 2 r02 (re-run on the new lock, same moves): PASS, min IoU 0.975, slivers 20 (1.7%), 1166 tris.
- stage 3 r05 (re-run): PASS, 2298 tris, slivers 32 (1.4%), hit/float/zfight 0, 8 colours.
- stage 4 r08 (re-run, arm_clean + smooth_weights kept): PASS: flips 3 (0.13% / 0.24% area), drift 0, hit 0;
  clip WARN 74 tris (4.2% area: the front flap against the thighs in move). Over budget: stage 4 took 8 rounds
  (the hull's hand-knee web cost 6).
- stage 4 r09: final with orbit + glbcheck, --review, --compare.
