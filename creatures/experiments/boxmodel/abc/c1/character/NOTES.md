# character, setting c1 "carve + detail"

Stage 1 = carve_base (visual hull of reference/, default knobs) for the torso, arms and legs; the head, hands and
feet are hand-built and zipped onto cuts of the hull (the parts a silhouette hull cannot see).
Pattern: abc/c1/goblin (head replacement, zip_rows). Comparison: abc/k3/character.

## Stage 1
- r01: carve_base defaults. PASS, 1122 tris, IoU side/front/top 0.937/0.918/0.855. Critique: overall shape and
  proportions follow the reference well (T-pose arms clear in front view); the head is a decimated blob of random
  triangles (no clean facets, no place for the face); hands are paddles with a knob; feet short clubs, no sole.
  Fix: replace the head.
- r02: Fix: hull bisected at z 1.185 (neck), faces above deleted, the neck band pulled onto the reference's thin round
  neck (half width 0.060), a 16-gon latitude sphere (r 0.198, 8 rings + pole) zipped onto the neck rim.
  Result: PASS, 1096 tris, IoU 0.935/0.921/0.830. The head is the reference's faceted sphere.
- r03: Fix: hull cut at the wrist (x 0.552), forearm tapered to the wrist, a mitten of 6-gon rings (flat palm,
  fingers curling down) zipped on by angle, a 2-step thumb from the palm's lower-front face. First try FAIL (the rim
  finder picked the open x = 0 seam loop); filtered to x > 0.5. PASS, 1252 tris.
- r04: Critique: front view, the hand a thin hook. Fix: hand rings thicker (palm 0.027, tip 0.015), less curl.
  Result: PASS; mitten reads in top view, thumb forward.
- r05: Fix: feet: hull cut at the ankle (z 0.125), a hand-built foot (sole outline from the reference side view: toe
  y -0.206, heel 0.066; instep ring sloping to the toe) zipped onto the ankle rim; thumb fatter.
  Result: PASS, 1328 tris, IoU 0.946/0.905/0.801 (top drops: the longer feet show past the head in plan, the side
  view wins). Critique: the foot reads as a boot (vertical heel wall).
- r06: sliver diagnostic (techqa rule) added: 10/1328 (0.75%), all at the neck and ankle cuts.
- r07: Fix: a sole-edge ring at z 0.016 (widest), the sole inset under it, heel lower: the foot rolls under.
  Result: PASS, 1372 tris.
- r08: lock round (orbit). Lock: 1372 tris, edge sha256 55c366ee0f37d841. No re-locks.
  Triangles stage 1: 1372.

## Stage 2
- r01: Critique: the carve's triangles cross the knee and elbow at random (no hinge line for the bend, no knee cap).
  Fix: planar loops (bisect_plane in k.topo 'loop', dist 0.006 so no sliver cuts) at the knee (z 0.35) and the
  elbow (x 0.35); knee-cap verts on the loop forward 6 mm, back of the knee 3 mm back, elbow point 5 mm back.
  Result: PASS, min IoU 0.999, slivers 12 (0.9%), 1392 tris. No colour borders needed: the brief's body is one flat
  skin colour (the other colours live on the face pieces). The head stays the reference's plain faceted sphere.

## Stage 3
- r01: pieces (abc/k3/character's face kit, re-seated on the new head): eye outline torus, sclera dome, pupil disc,
  brows, mouth line, pointed nose; plus toe blocks (4 per foot, bevelled boxes rooted in the sole front). Skin =
  colour_from_sheet's cluster nearest the brief peach (#f5b06f); 4 colours. Result: FAIL hit 4 (sclera/pupil),
  z-fight 6 (toe bottoms coplanar with the sole).
- r02: Fix: eye rings on the smooth sphere instead of the 16-gon facets; toe bottoms 3 mm up. Result: z-fight 0,
  hit still 4.
- r03: Fix: pupil back shallower (-1.2 mm). Result: hit still 4. Diagnosis: the sclera is a thin lens (back at
  +11.5 mm, chord sag ~4 mm): the pupil's back cap exits through the sclera's back.
- r04: Fix: sclera back ring/vertex lower (+8.5 / +6.5 mm off the sphere, still clear of the skin). Result: PASS,
  2194 tris, slivers 12, hit/float/zfight 0, 4 colours.

## Stage 4
- r01: k3's rig and clips (idle breathe + blink, walk with arm swing, punch), J moved onto the carved arm axis.
  Result: PASS first try: flips 3 (0.14%, body), drift 0, clip 0, stretch 0. The hull's arms are clear of the body
  in the T-pose, so no weight cleanup was needed (unlike the goblin).
- r02: final with orbit + glbcheck, then --review, --compare.

## Team repair pass (ad_notes_team.md), R0 = 9
- s4 r09 baseline: all gates PASS (hit/float/zfight 0, slivers 12 0.5%, flips 3 0.14%, drift 0). No item 0.
### Item 1 hands (STAGE-1 UNLOCK, owner-authorised in the notes): stage1_lock.json -> stage1_lock.pre_team.json
- s1 r10: Critique: front limb close-up, the hand a flat paddle with a back-pointing hook. Diagnosis: HAND was a
  stack of 6-gon rings, no knuckle row; THUMB extruded from the lower-front face pointing down/back. Fix: 8-gon
  rounded-rectangle rings (superellipse), knuckle ring at ~50% length, finger block curling down beyond it; thumb
  rooted on the front (-Y) quad between the wrist ring and the palm base (picked by ring index, not by normal).
  Result: PASS 1420 tris; hand too short (AD's 0.10 m), blueprint front/top IoU 0.891/0.766 (was 0.905/0.801).
- r11: Fix: hand length back to ~0.15 m (tip x 0.698), palm 0.096 wide (1.4x the wrist's 0.07). Result: IoU
  0.898/0.792; thumb hidden behind the palm in the front view.
- r12: Fix: thumb offsets more -Z (sits under the palm plane, shows in az000). Result: visible lump in front view.
- (lock attempt r13 crashed in kit json: META['keep_valleys'] lambda is not serialisable; moved the assignment
  into stage3() as KEEP_VALLEYS, behaviour unchanged. The half-written lock was removed.)
- r14: Critique: from the front the hand thinner than the wrist. Fix: palm half thickness 0.019 -> 0.023-0.024.
- r15/r16: Critique: thumb a thin plank (sheared: offset had +X while the root face normal points -Y,-X). Fix:
  offsets along the root normal, shorter (2 x ~0.02 m), scale 1.0/0.8. Result: a chunky two-block thumb.
- r17: re-lock: 1420 tris, edge sha256 8a43f3d8c24a022c, gates PASS. r18 stage 4: all PASS, IoU min 0.999.
  Packet: hero/az090 read as a mitten with a forward thumb; posed attack_f007 fist reads as a hand.
### Item 2 eye pieces (stage 3/4)
- s4 r19: Critique: az090 goggles, back34 black crescent. Fix: outline band 40% thinner and ~8 mm lower, sclera
  stack sunk ~7 mm with its back under the skin. Result: FAIL drift 2 (eye.L/R): a seated sclera squashed by the
  old blink (z 0.35, rim moves 36 mm) counts as drift; that is why s3 r04 had raised it.
- r20-r23: tried the opposite (sclera kept >= 6.8 mm off the skin, so not seated; outline lowered; dome/pupil
  retuned). r22 hit 4: pupil back cap exited the thinner sclera; r23 PASS but the eye still ~12 mm proud and the
  pupil centre covered by the sclera dome. r21 also pinned skin to #f5b06f (the sheet clustering on the new hands
  drifted to a dull #d8a475; the palette is on the keep list).
- r24: Diagnosis: the blink, not the geometry, forced the lift. Fix: r19 geometry (sunk, seated) + the blink sinks
  the eye along its normal (eye bone scale (1, 0.2, 0.85)) so seated verts move < 1% of height. Result: all gates
  PASS; clip WARN 26 tris (eye/pupil sinking under the skin at the blink frames 41-45, by design: the skin closes
  over the eye; no packet frame shows it). Packet: az090 eye barely proud, thin outline; back34 crescent down to a
  1-2 px line.
### Item 3 nose (stage 3)
- r25: Critique: no nose in hero/az000, a 3 mm spike in az090. Fix: cone 0.058 m long (was 0.026), base ~0.035 m,
  base pushed ~4 mm into the skin, same seat (10 deg below the equator, midline). Result: PASS; a clear point in
  az090 and in the model top view like the reference top.
### Item 4 shoulder wedge / sternum crease (stage 2)
- r26: Critique: hero, a knife ridge from the shoulder point down the chest, a sternum crease, a flat-faced
  deltoid. Diagnosis: the carve's random triangles, no ring to move. Fix: shoulders(): vertex moves only: a
  weighted Laplacian relax of the upper torso and arm root (neck band untouched, seam kept on x = 0), deltoid cap
  out 8 mm / down 4 mm, armpit up 6 mm. Result: PASS, IoU min 0.990; flips 3 -> 6 (0.27% tris, 0.39% area,
  under the 0.5% limit: upper arm). Packet: rounded cap, ridge and crease gone in hero / az000.
### Item 5 idle arms (stage 4)
- r27: Critique: hero, the idle arms stand out in an A and the hand reads as a hook. Diagnosis: the elbow key
  was already 12 deg and there is no wrist key; the hook was the old hand's curl plus the 40 deg spread. Fix: idle
  keys only: upper arms -60 (breath -57), elbows 8 deg, both arms the same. Result: PASS; hands hang by the
  thighs, one gentle bend, in hero, az090, idle_f012/f024.
### Should-fix
- r28: toes ~1.7x longer, spread to the outer edge of the foot. PASS.
- r29 (final, orbit + glbcheck OK): brow inner end ~4 mm up (gentler arch). All gates PASS: hit/float/zfight 0,
  slivers 12 (0.5%), flips 6 (0.27% tris, 0.39% area), drift 0, clip WARN 26 (the blink), lock PASS
  (8a43f3d8c24a022c), stage-2 IoU min 0.990, 2242 tris. --review and --compare rebuilt.
- Not done: feet toe-in (stage 2), second elbow loops.

## Team repair pass 2 (review/verify_team.json: items 1, 2, 4 PARTLY; flips 3 -> 6), R0 = 30
- s4 r30 baseline: all gates PASS (flips 6, clip WARN 26).
### Item 1 hands (STAGE-1 UNLOCK again: stage1_lock.json -> stage1_lock.pre_team2.json, then .pre_team3.json)
- s1 r31/r32 (lock 8a43f3d8c24a022c): Critique: front-limb close-up, the thumb a peg hanging down. Diagnosis: THUMB
  offsets -Z 10 mm per segment and only ~0.04 m long. Fix: ~0.055 m, forward (-Y) and out, 5/3 mm down, each cap
  turned about Z (no shear), scale 1.15/0.8. Result: PASS 1420 tris; a forward thumb in the top view, thin.
- s4 r33: Critique: az000, the hanging hands show their thin edge (flippers). Diagnosis: palm faces the thigh, so
  the front sees the 46 mm thickness. Fix (idle keys only): forearm and hand twist 22 deg each (pronation).
  Result: PASS; az000 shows a mitten wider than the wrist with the thumb lump on its forward-inner edge.
- s1 r34/r35 (re-lock, edge sha256 737d36f39a95aa51): thumb leaned ~40 deg toward the fingers (offsets +X 18/20 mm,
  caps turned 30 + 12 deg) so the front view reads a thumb, not a down peg. r36 stage 4: all PASS.
### Item 2 eye pieces (stage 2 vertex moves + stage 3)
- r37: Critique: az090, the eye ~25 mm ahead of the head outline; back34 a black sliver. Diagnosis: the stack was
  built on the smooth sphere, up to 7 mm over the 16-gon facets, plus a 7 mm dome. Fix: socket() sinks the two
  head verts under each eye (stage 2, vertex moves; keep_valleys already covers it); outline and sclera rim
  projected onto the real skin at +0.8..2.8 mm; sclera a shallow lens over its rim plane; eye bone head deeper
  (EYE_B) so the blink still sinks it. Result: FAIL z-fight 46 (lens 3 mm off the skin).
- r38-r40: lens 5.5/7.2 mm, socket 10 mm, rim +2.6 mm (z-fight 6, all on the brow over the socket slope), brow
  +1.4 mm. Result: all PASS, clip WARN gone. Packet: az090 eye nearly flush, thin outline; back34 nothing black.
### Item 4 sternum crease / arm-root wedges (stage 2) and the flip regression
- r41/r42: Critique: az000 faint sternum line, flat wedge planes under the arm root, purple at the armpit.
  Fix: relax 4 -> 8 passes; the chest front (x < 0.10) eased onto the seam profile's y per height. Result: PASS,
  IoU min 0.981; flips 6 -> 3 (0.13% tris, 0.22% area), the armpit and shoulder patches gone (upper arm 1-2, shin
  1 remain, the pre-team count). The arm root is still low-poly faceted in the close-up: partly.
- r43: tried moving the punch from the clavicle to the upper arm to clear the last upper-arm flip: flips 5, reverted.
- r44 (final, orbit + glbcheck OK): hit/float/zfight 0, slivers 16 (0.7%), flips 3, drift 0, lock PASS
  (737d36f39a95aa51), stage-2 IoU min 0.981, 2242 tris. --review and --compare rebuilt.
