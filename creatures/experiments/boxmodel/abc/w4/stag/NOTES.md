# stag (w4) build notes

Reference present: side/front/rear/top read before stage 0; blueprint.json kept as traced.
Conflict: brief lists antlers as a stage-3 piece but also as a stage-1 silhouette cue. Choice: the two
main beams are extruded from the skull in the stage-1 base (the cue); tines, crown and brow tines are stage-3 pieces.

## Stage 1
- r01: 604 tris, gates PASS, IoU side .83 / front .648 / top .789. Critique: front view, the neck is a thin
  stalk (reference has a thick maned neck, trace runs x .09 at the jaw to .19 at the chest). Diagnosis: ring
  widths R6/N1/N2 = .13/.105/.09. Fix: widen them to .16/.135/.11.
  Result r02: front IoU .648 -> .671, top .78; 604 tris. Better (neck reads thicker from the front).
- r02: Critique: hero/az090, the antler beams are two straight spikes leaning back: antelope horns, not a
  stag's lyre. Diagnosis: BEAM sections on one straight line. Fix: bend the beam: out and back low, then
  vertical at the top (A2 .16/-.27/1.36, A3 .25/-.20/1.44, A4 .29/-.16/1.55, A5 .30/-.13/1.66), thicker root.
  Result r03: side .836, front .674, top .782; 604 tris. Better: beams now bend out low and rise (lyre).
- r03: Critique: az090/hero, the muzzle tapers to a needle point (gazelle), the reference has a blunt
  square muzzle with a nose block. Diagnosis: H6/H7 half widths .05/.032 and H7 only .06 tall.
  Fix: H6 .056, H7 .046 and 1.08..0.995 tall so the nose end is a blunt block.
  Result r04: side .834, front .674, top .779; 604 tris. Better: muzzle ends in a blunt nose block.
- r04: Critique: az000, the ears are small thin paddles hidden behind the antler roots; the reference has
  big leaf ears standing out sideways and a little up. Diagnosis: EAR sections hv .042/.05, tip at x .235.
  Fix: longer, broader leaf: E1 hv .038, E2 at x .195 hv .058, tip at (.255, -.31, 1.27).
  Result r05: side .835, front .667, top .781; 604 tris. Better: leaf ears stand out past the head in front.
- r05: Critique: az090/hero, the torso is a straight slab, equal depth chest to hip; the reference swells
  at the chest and tucks at the waist before the thigh. Diagnosis: R3/R4/R5 bottoms .52/.47/.45, widths
  .155/.165/.17. Fix: waist R3 bottom .545 w .145; ribcage R4 bottom .45 w .172; chest R5 bottom .435.
  Result r06: side .83, front .671, top .785; 604 tris. Better: chest swells and the waist tucks before the thigh.
- r07 (lock): reads as a stag base from every view (maned-neck mass, deep chest, slender legs, lyre beams,
  leaf ears). Remaining in stage 2: brow/stop/eye sockets, jaw line, joint loops. Lock with the orbit.
- Stage 1 locked at r07: 604 tris, edge sha256 99a9f850ef2645b5, min blueprint IoU at lock .671 (front).

## Stage 2
- r01: brow/cheek/stop/jaw vertex moves; eye-socket inset, nose-pad inset, mid-neck loop, second hock loop.
  All gates PASS, min IoU vs s1 .993, 672 tris, slivers 12 (1.8%, limit 2%). Critique: tech QA flags the
  antler beam tips and ear tips (yellow) as slivers: long needle quads. Diagnosis: last BEAM/EAR sections
  are .006/.004 half size. Fix: vertex move: scale the tip sections x2.2 about their centres.
  Result r02: slivers 2 (0.3%), min IoU .987, 672 tris. Better.
- r02: Critique: hero, the head reads small against the deep chest (STYLE: size the head up; it is the
  medium mass). Diagnosis: head rings H2-H7 sized to the traced sheet. Fix: vertex move: scale the head,
  ears and beams x1.08 about the skull base (0, -.35, 1.12). Final stage-2 round with the orbit.
  Result r03 (final, orbit): min IoU vs s1 .914, 672 tris, slivers 0.3%. Better: bigger head reads.

## Stage 3
- r01: paint (6 colours: body, mane, cream, antler, hoof/nose, eye), eyes, 6 tines per side, 19 mane
  tufts per side, tail. All gates PASS, 1004 tris. Critique: hero/az000, the mane reads as thorns: thin
  square spikes standing off the neck. Diagnosis: spike() square roots .026 and dirn = .6 normal + down.
  Fix: tufts become flat shards (thin .013 along the normal, .04 across), lie along the neck (.3 normal)
  and hang longer toward the V point.
  Result r02: 1004 tris, gates PASS. Better: the mane reads as a shaggy dark mass hanging to a V on the chest.
- r02: Critique: az090/hero, the tines are needle-thin and read dark and spiky, not like the chunky pale
  tines of the reference. Diagnosis: tine root half .008-.012. Fix: roots .015-.02 (brow tine thickest).
  (Bug found by a GLB check: the half-built tail shell came out inside-out; it is now built whole, mirror off.)
  Result r03 (final, orbit): 1004 tris, slivers 0.2%, all gates PASS. Better: tines read as pale antler points.

## Stage 4
- r01: rig (16 bones + .R mirrors, roll auto), skin, pieces bound with body= weights; idle graze + ear
  flick, 4-beat walk, head-down charge (signs checked on the posed renders: neck +X lowers the head,
  antlers come forward in the charge). FAIL: posed flips 44 (4.38% of tris, 0.25% area), all in the mane.
  Diagnosis: each thin mane shard gets per-vertex transferred weights, so its root and tip twist apart
  when the neck bends. Fix: after bind, make each mane/tine shell rigid with the mean weights of its shell.
  Result r02: flips 0 (0% tris, 0% area), drift 0, hit 0, all gates PASS; posed walk shows the knee
  folding back and the hock flexing, the neck lowers without collapse. 1004 tris.
- r03: final round with the orbit and glbcheck; no geometry change.
- --review run: review/ packet built.

Triangles: stage 1 604, stage 2 672, stage 3/4 total 1004. Rounds: s1 7 (lock r07), s2 3, s3 3, s4 3.
