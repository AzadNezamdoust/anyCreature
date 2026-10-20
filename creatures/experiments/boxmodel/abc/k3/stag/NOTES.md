# stag (k3) build notes

Reference sheet present: blueprint.json traced from it (not redrawn). Conflict logged: the sheet's
body is 1.42 m long, the brief says 1.8 m; the sheet wins on shape, so the model is 1.42 m long.
Brief says antlers are a stage-3 piece but also that they are the stage-1 silhouette cue: the main
beam and four tines are extruded in the stage-1 base; stage 3 adds only small detail.

## Stage 1
- r01 Critique: the plain antler beams read as gazelle horns (az090, hero); a stag needs tines.
  Diagnosis: A-chain only has the beam. Fix: extrude brow, bez, trez and crown tines from beam side
  faces (Chain matched corners by angle so thin side faces extrude cleanly). Result: better, reads as deer. 576 -> 704 tris.
- r02 Critique: the rump ends in a flat vertical disc (az090, az180) and the thigh has no mass.
  Diagnosis: RINGS R0 is as tall as the rump and R1's low points are narrow. Fix: smaller, tilted R0
  cap and wider low R1 points (thigh). Result: see r03.
  Result r03: rump slightly softer, still 704 tris; the body is still one uniform tube.
- r03 Critique: the torso is a slim uniform tube (az000 a sliver, az090 one flat flank plane); the ref
  has shoulder, ribcage, waist tuck and thigh masses and a deeper chest. Diagnosis: R1-R7 side
  widths nearly equal. Fix: per-ring widths (shoulder blade high on R5, ribs widest on R4, waist R3
  tucked and raised, hip bone high on R2, thigh low on R1), chest bottom 0.52. Result: see r04.
  Result r04: front view no longer a sliver; flank planes vary. 704 tris.
- r04 Critique: legs are uniform sticks (az090, hero): no muscled forearm/thigh tapering to slim
  cannons, so they read as posts. Diagnosis: L/H chain half sizes shrink evenly. Fix: bigger elbow
  and stifle sections, thinner cannons (0.018 x 0.022) and pasterns. Result: see r05.
  Result r05: legs taper (forearm/thigh to slim cannon), better; 704 tris.
- r05 Critique: the head is small and pointed with thin, tiny ears (az000, hero); the ref has a
  chunkier head, a blunt muzzle and big leaf ears. Diagnosis: R9-R12 widths, E chain has one wide
  section. Fix: wider skull/muzzle rings, blunt nose ring, 3-section leaf ear (0.09 wide). Result: see r06.
  Result r06: head chunkier, ears read as leaves from front and 3/4; 720 tris.
- r06 Critique: the back is a dead-level line (az090); the ref rises to the withers and dips
  slightly behind them. Diagnosis: R2-R5 top seam z nearly equal. Fix: R5 top 1.02 (withers),
  R3/R2 top lowered to 0.905/0.895. Lock this round (reads as a stag from every view).
  Result r07: withers read; LOCKED at 720 tris (edge sha256 cbfd02b999a32fd8). Blueprint IoU
  side/front/top 0.721/0.708/0.711 (the traced outline includes mane and full antler spread).
  Note: stage1 uses literal joint positions equal to J; J drives the stage-4 rig.

## Stage 2
- r01 Plan: deformation loops at the shoulder, hip and neck base (walk and grazing bend), an eye
  socket inset on the skull side (kept as a valley), a brow lift over it and a muzzle stop.
  Result r01: gates pass except slivers 38 (4.8%); 788 tris. Critique: needle triangles on the
  tine, beam and ear tips (tip sections 0.003-0.006 on 0.07-0.13 long segments -> < 6 deg).
- r02 Fix: scale each tip quad about its centre to 0.009 half size (ear 1.4x). Result: see r03.
  Result r02: slivers 0 (0.0%), all s2 gates PASS, 788 tris, min IoU vs s1 0.978.
- r03: final stage-2 round with the orbit, no change.

## Stage 3
- r01 Plan: 6 colours (body, mane, cream, antler, hoof+nose, eye) on edge-bounded regions (belly
  on the keel loop, rump cap, jaw underside, hooves above the hoof-top loop, dark lower legs);
  pieces: eye lens in the socket, pyramid points on the blunt tines, 36 blade tufts for the mane
  with long tufts making the chest V, a short hanging tail.
  Result r01: all s3 gates PASS, 1196 tris, 6 colours.
- r01 Critique: the mane reads as porcupine quills (az090, az000): narrow blades sticking out
  sideways; the ref mane is shaggy shingles hanging down. Diagnosis: tuft direction n*0.8+down*0.6,
  base half width 0.035. Fix: hang them (n*0.55 + down*0.83, slight back lean on the nape), base
  half width 0.055, thicker. Result: see r02.
  Result r02 (read s3_az090_colour.png): mane hangs as shaggy shingles, reads as a mane; 1196 tris.
- r02 Critique: no cream belly band in side view (az090); the ref shows a pale underline from chest
  to thigh. Diagnosis: belly rule only takes the down-facing keel strip (n.z < -0.6). Fix: take the
  lower-flank band too (bounded by the v3 edge loop: n.z < -0.25, z < 0.74), not the leg tops.
  Final stage-3 round with orbit.
  Result r03: pale underline and rump patch read; all s3 gates PASS; 1196 tris (body 788).

## Stage 4
- r01 Plan: rig on J (roll auto): hips/spine/neck/head, ear and antler bones, 4-bone legs; skin,
  bind all pieces with body weights; idle graze + ear flick (48f), diagonal walk (25f), charge (32f).
  Result r01: all gates PASS except drift: 4 mane tuft shells lift off the neck in a pose. Posed
  renders: graze and charge read, legs swing, neck bends without collapse; 0 fold-overs.
- r01 Diagnosis: the neck bone takes 40-48 deg alone in graze/charge; linear-blend skinning shrinks
  the long tufts' 0.1-0.16 m offsets from the skin by more than 0.01 L. Fix: move part of the pitch
  to the head (neck 34/head -26 graze, neck 30/head -32..-38 charge) and shorten tufts 10-15%.
  Result r02: still 4 drifting shells; the tech heatmap flags the long chest-V tufts, whose tips hang
  over the fore-leg tops and follow the leg swing. 2 fold-overs (0.17%).
- r02 Fix: start the mane rows at ring 5.8 (off the shoulder) and cut the V extension to 0.02.
  Result r03: 2 drifting shells left (heatmap: the lowest chest tuft pair, rooted below z 0.78 just
  in front of the fore-leg top). 2 fold-overs (0.17%).
- r03 Fix: skip tufts rooted below z 0.78. Final round with orbit + glbcheck, then --review.
  Result r04: ALL s4 gates PASS (hit 0, float 0, z-fight 0, sliver 0, flips 2 = 0.17% tris /
  0.15% area, drift 0, lock PASS, glbcheck OK). Final 1180 tris (base 788 + pieces). --review run.

## Triangles per stage
s1 720 (locked) | s2 788 | s3 1196 | s4 1180 (mane lost its lowest tuft row in s4 r03)

## Repair pass (K=1, notes: review/ad_notes.md; stage 1 locked, no unlock)
- s4 r08 Baseline on the 2026-09-28 kit: all gates PASS; WARN clip 16 tris (1.17% area). techqa.json
  puts all 16 clip tris on piece_mane (not the antlers, as item 0 guessed) and the 2 flips on the body
  at the throat under the jaw (3_tech az000 purple). 1180 tris.
- s4 r09 Critique (item 1): the mane is 36 thin blades, a spiky pile in the close-ups. Fix: stage 3,
  rebuild it as 7 shingle plates per side (14 total) in nape / side / throat rows, each a thick
  diamond-section plate rooted 0.03 inside the neck, hung down-back along the skin. Result: clip
  12 tris 0.52%, but FAIL drift 2 shells (the long throat-V pair hangs over the fore-leg tops), side
  plates stick out as fins in az000 and the plates are too small to cover the neck. 1188 tris.
- s4 r10 Fix (item 1, placement): throat-V pair moved up (roots u 6.9/7.6, s 0.80, tips above z 0.8),
  plates wider (half 0.075-0.10) and longer (0.15-0.22), lift off the skin 0.35 -> 0.2, crown 0.028.
  Result: ALL gates PASS, clip 2 tris (0.09%), drift 0; az000 now reads dark mane over one cream V;
  plates read as shingles but lie flat (less ruff volume than the sheet). 1188 tris.
- s4 r11 Critique (item 0): 2 body flips at the throat under the jaw (3_tech az000 purple) in the
  graze and charge. Diagnosis: the head counter-pitches up against the bent neck (graze head -26,
  charge -32..-38), closing the jaw-throat angle. Fix: head graze -18/-14, charge -22/-25 (neck
  unchanged). Result: flips 0, drift 0, clip 2 tris (0.09%); charge still drops the antlers forward.
- s4 r12 Critique (item 2): every tine ends in a darker cone standing on a ledge (the 0.0075 pyramid
  base sat inside the 0.009 blunt tip ring). Fix: stage 3, each point is built on the tine's own last
  ring (read from the base): a collar 1.06x that ring, a back point sunk into the tine and a tip
  leaning 7 deg outward; visible lengths brow 0.034 < bez < trez < crown < beam 0.066. Result: FAIL
  z-fight 16 (the sunk frustum ran parallel to the tine sides).
- s4 r13 Fix: collapse the sunk ring to one back point. Result: z-fight 4 (crown tine, which flares:
  back faces dot 0.99 at 1.6 mm from its sides, found with a stage-3 debug probe, round s3 r99 discarded).
- s4 r14 Fix: back point depth capped at 0.015 (steeper). Result: ALL gates PASS, z-fight 0; the head
  close-up shows tine and point as one taper in the antler colour, no ledge. 1208 tris.
- s4 r15 Critique (item 3): the ear is a thin cream slab in front of the antler base and over the
  eye (head close-up). Fix: stage 2 vertex moves on the ear's three sections: rear-face verts back
  0.012 / 0.009 / 0.003 (a section), sections turned back 6 / 12 / 12 deg about the vertical through
  the ear root, tip up 0.01. Result: gates PASS, IoU min 0.972; the ear edge now shows a thickness but
  from the hero close-up it still covers the back of the eye.
- s4 r16 Fix (item 3, same note): turn the ear sections 10 / 22 / 22 deg. Result: gates PASS, IoU
  min 0.958; hero close-up: the ear stands beside the antler base, behind the eye, with a visible edge.
- s4 r17 Critique (item 4): the eye is a tiny chip (1/15 of the head). Fix: stage 3, eye lens 1.6x
  across (depth +-0.012, front proud of the socket face), socket faces painted dark mane. Result:
  gates PASS (hit/float/z-fight 0); az090 the eye reads at thumbnail size.
- s4 r18 Critique (item 5): dark facet behind the near fore-leg top (front-limb close-up). Diagnosis
  (stage-2 debug probe, round s2 r99 discarded): the only concave vertex there is the waist ring's low
  side point (0.10, 0.15, 0.646), dented -0.006 against its neighbours. Fix: move it out 0.015.
  Result: gates PASS, valley 0, flips 0, but the close-up is unchanged: the dark plane is the
  down-facing cream belly strip in shadow, not a dent.
- s4 r19 Fix (item 5): drop the strip's outer edge (that waist vertex -0.025 z, the rib-ring low side
  vertex behind the leg out 0.008 / down 0.02) so the strip faces the side. Result: the band reads as
  lit cream, but FAIL s2 self-intersection (2 hits: the rib-ring vertex runs into the leg root).
- s4 r20 Fix: keep only the waist-vertex drop (rib-ring move reverted). Result: ALL gates PASS, s2
  shell clean, IoU min 0.958; front-limb close-up: the strip behind the leg reads as a lit cream plane.
- s4 r21 Should-fix (rump border): the rump rule cut across the R0-R1 band faces (y > 0.62); it now
  takes the whole band (y > 0.585, n.y > 0.25), so the border runs on the R1 loop. back34: one clean
  patch. Gates PASS.
- s4 r22 Final with orbit + glbcheck, then --review and --compare. ALL gates PASS: hit 0, float 0,
  z-fight 0, sliver 0%, flips 0 (0% tris / 0% area), drift 0, lock PASS, IoU min 0.958, glbcheck OK;
  clip WARN 3 tris (0.10% of area, mane). Repair pass: 1208 tris (base 788 + pieces), rounds r08-r22.

## Repair pass 2 (K=2, notes: review/ad_notes_r2.md; stage 1 locked, no unlock)
- s4 r23 Baseline: all gates PASS; WARN clip 3 tris (0.10%, mane). 1208 tris.
- s4 r24 Critique (item 1): side plates flare as wings in az000; clumps random. Diagnosis: each plate was a
  straight slab along the root's tangent plane, lifted 0.2 L, so over the widening shoulder its edges stood
  proud. Fix: stage 3, three graded rows per side (nape / side / throat, largest at mid-throat), tips down
  and 25 deg in toward the centre line, every section's centre and side corners laid on the skin (BVH
  nearest point) and lifted along its normal, tip lift 0.1 L; lowest throat pair 25% longer (0.24).
  Result: gates PASS, no flaps in az000, clip 18 tris 0.49%.
- s4 r25 Fix: mid lift 0.026 -> 0.032, side corners 0.8 of the lift. Result: clip 2 tris 0.04%.
- s4 r26 Critique (item 2): flank cream rectangle and chest shield. Fix: stage 3 paint: belly only n.z < -0.6;
  chest cream only under the mane V tip (z < 0.78) and inner half (|x| < 0.09). Result: az090 thin underline.
- s4 r27 Fix: a tapered V bound (|x| < 0.025 + ...): the chest faces are too coarse, no cream left.
- s4 r28 Fix: z < 0.74, |x| < 0.07. Result: a small cream V under the dark mane in az000.
- s4 r29 Critique (item 1): thin spikes at the neck sides in az000. Diagnosis (stage-3 debug, round s3 r99
  discarded): nape tips crossed x = 0 and were clamped onto the midline; the low side plate sat on the
  shoulder bulge (x 0.208). Fix: nape row hangs straight back; side row u 6.3/7.0/7.7, s 0.40.
- s4 r30 Fix: plate mid lift 0.022, crown 0.010 (edges less proud). Result: clip 4 tris 0.07%, az000 clean.
- s4 r31 Critique (item 3): ears are large flat pale paddles. Fix: stage 2, outer two ear sections scaled
  0.8 toward the root; a logged partial loop down the ear front face, its verts pushed back 25% of the ear
  depth (cup); paint: pale only on front faces (n.y < -0.55), back and rim body brown. Result: IoU min 0.951;
  az000 small brown ears with pale inners, clear of the antlers.
- s4 r32 Critique (item 4): brow tine a pin, tines identical. Fix: stage 2 vertex moves (TINE_EDIT): brow tine
  rotated 35 deg up about X, 1.5x long, base 1.2x; bez 0.8x, trez 1.05x, crown 1.25x; stage-3 points read the
  moved ends, lengths 0.05/0.034/0.046/0.058/0.075 and leans 4/9/3/7/12 deg. Result: IoU min 0.902 (too
  close), the brow tine reads as a second beam.
- s4 r33 Fix: brow tine 25 deg up, 1.35x. Result: IoU min 0.916; forward-up brow tines, uneven crown.
- s4 r34 Should-fix: tail 1.2x thicker. Gates PASS.
- s4 r35 Final with orbit + glbcheck, then --review and --compare. ALL gates PASS: hit 0, float 0, z-fight 0,
  sliver 1.1%, flips 0, drift 0, lock PASS, IoU min 0.916, glbcheck OK; clip WARN 4 tris (0.07%). 1256 tris.
