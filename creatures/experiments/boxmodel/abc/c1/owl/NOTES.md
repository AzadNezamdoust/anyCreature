# owl, setting c1 "carve + detail"

Stage 1 = carve_base (visual hull of reference/, copied from abc/k3/owl with blueprint.json) plus hand edits.
Pattern: goblin (biped, carve knobs) for stage 1, k3/owl for pieces and rig.

## Stage 1
- r01: carve_base defaults. PASS, 1134 tris, IoU side/front/top 0.903/0.920/0.961. Critique: the ear tufts are round
  bear-ear nubs (az000, az180, hero): the owl's identity cue is a pointed tuft. Body egg, legs, tail and head read.
  Diagnosis: thin parts blurred by mask_blur 3 + blur 1. Fix: knobs mask_blur 1, blur 0 (the goblin's crisper setting).
- r02 result: PASS, 1134 tris, IoU 0.918/0.929/0.968; crisper, a wing edge now shows at the flank (az000). Critique:
  tufts still blunt nubs (front tip z .620 vs blueprint .642). Diagnosis: the 7 mm voxel truncates the tuft blade.
  Fix r03: hand edit: the tuft's top vert to the blueprint tip (0.118, -0.064, 0.648), the outer vert under it out,
  the inner vert down into the V between tufts.
- r03 result: PASS, 1134 tris, IoU 0.920/0.931/0.968. Tufts now pointed blades (az000, hero, az180): reads as an
  eared owl from every view. Remaining (stage 2 work): a vertical ridge down the face centre (the side view's beak and
  disc front), no eye sockets, the folded wing only a soft step on the flank. Locking.
- Lock: r04 (orbit), 1134 tris, edge sha256 bdb3e4cf292c48ac. 4 rounds, no re-lock.

## Stage 2
- r01: face dish (the prow seam back 6-14 mm, the eye-column rim 5-10 mm forward); planar border loops: wing front
  edge (side view line shoulder -> tail root), wing inner edge x .135 (front view), bib line z .345. Result: PASS,
  min IoU 0.99, 1198 tris, slivers 8 (0.7%), all yellow on the x .135 cut along the flank (az000 TECH). The "nose"
  wedge in az000 is the side view's beak at z .44: the beak piece covers it in stage 3.
  Fix r02: cut snap distance 8 -> 12 mm (the bear's value), so the near-parallel flank cut snaps to existing verts.
- r02 result: PASS, 1178 tris, slivers 4 (0.3%). Next stage-2 change rides with stage 3 r01 (logged there).

## Stage 3
- r01: stage 2 adds a leg border loop (z .075) and pulls the carved beak bump on the seam back 12-20 mm (the beak
  piece replaces it). Paint by rules on the loops, colours from colour_from_sheet mapped to brief roles (bear's rule).
  Pieces (k3's, re-seated on the carve by raycast): eye dome + pupil + hidden blink lid, facial disc (cream dish, dark
  rim), hooked beak, V brows into the tufts, 3+1 talons per foot; new: a folded-wing feather plate per side (grid in
  the side view between the wing loop and the back outline, raycast onto the flank, 9 mm thick, scalloped primaries
  over the tail root).
- r01 result: PASS, 2380 tris, 7 colours, zfight 2, slivers 16 (0.7%). Critique: the owl is nearly black (hero, az135
  colour): the sheet clusters carry the render's shading, and brown took #5a473e (dE 37 < 40 from the brief's
  #7a5a3c). Owl reads (tufts, disc, eyes, beak, talons) but the values are crushed. Fix r02: a sheet colour replaces a
  brief role only within 16 (else the brief hex); tan lifted to #b08a64.
- r02 result: PASS, 2380 tris. Brief values now, but the whole flank and back read near-black (az090, az135): the rule
  paints every face behind the wing loop 'dark', so the wing plate (brown/dark) sits on a dark field and vanishes.
  Fix r03: the flank under the plate and the front-view wing strip paint brown; dark stays on tufts, tail, primaries.
- r03 result: PASS, 2380 tris. Reads as a horned owl from every view (tufts, disc, orange eyes, hooked beak, cream
  belly, talons). Critique: the wing plate is invisible in az090/hero: plate and flank are the same brown, only its
  dark primaries show as a patch. Reference: the folded wing is darker than the body. Fix r04: plate coverts 'dark'
  #4a3424, primaries a new 8th colour #35251a, on the brown flank.
- r04 result: PASS, 2380 tris, 8 colours. The folded wing now reads in az090/az135 (dark coverts, darker primaries
  over the tail root). Critique: brown skin speckles poke through the wing plate (az090, az135). Diagnosis: the plate
  front is 6 mm over the skin only at the grid points; the carved flank bulges between them. Fix r05: each front
  point clears the skin's highest point over its cell (9 ray samples), +5 mm.
- r05 result: PASS, 2380 tris, 8 colours. Clean dark wing plates with no skin poking through; az090 now matches the
  reference side (dark folded wing over a brown flank, cream belly, primaries over the tail root). Stage 3: 5 rounds.

## Stage 4
- r01: k3's rig (root/spine/head/tail/thigh/foot/wing, roll auto, eye bones after skinning for the blink), joints on
  the carve; every piece body= bound (lid's head share handed to the eye bones). Wing swings smaller than k3 (flap 18,
  spread 25, raise 20) because the carved wing is fused to the flank.
- r01 result: FAIL fold-overs 10 (0.42% tris, 0.52% area: disc 8, body 2); WARN stretch 20 (body, 2.49x), clip 13
  (wing, 1.34% of surface). Diagnosis (hypothesis): the 35 deg idle head turn shears the disc, whose lower rim sits on
  the head/spine weight blend (the carve's chin is low, z .44). Fix r02: head turn 35/-25 -> 25/-18.
- r02 result: PASS (fold-overs 9: disc 7, body 2, under both limits); WARN stretch 20 (body flank, 2.49x), clip 12
  (wing plate, 1.23% of surface). Posed: blink closes (idle f24), hop reads, attack is a forward lunge with the
  wings only lifting a little (the carved wing is fused to the flank). Critique: the pink clip on the wing plate.
  Diagnosis: the wing bone drags the flank skin under the plate while the plate's borrowed weights average it, so
  skin crosses the plate in the flap/spread frames. Fix r03: wing swings flap 18 -> 12, raise 20 -> 14, spread 25 -> 18.
- r03 result: PASS; clip 6 (0.53% of surface, was 1.23%), stretch 6 (2.1x), fold-overs 9. Critique (look): the feet
  are 10 cm tan slabs (az000, hero): the hull of the sheet's spread talons. Fix r04 (stage-2 vertex moves): foot
  verts (z < .045) narrowed to 72% about the leg line x .067, outer front corners pulled back 35% of their offset so
  the middle toe leads; talon roots moved in to x .045/.067/.089. Final candidate, orbit on.
- r04 result (final, orbit on): all gates PASS (lock, s2 connectivity, s3/s4 lock assertions, hit 0, float 0,
  z-fight 0, slivers 12 (0.5%), fold-overs 9 (0.38% tris / <0.5% area), drift 0, glbcheck OK). WARN clip 6 tris
  (0.54% of surface, wing plate), stretch 6 (2.1x, flank). Feet narrower with a leading middle toe. --review, --compare.

Triangles: s1 1134, s2 1178, s3/s4 2380 total. Rounds: s1 4 (lock r04, no re-lock), s2 2, s3 5, s4 4.
Lock edge sha256 bdb3e4cf292c48ac.
Remaining: the attack's "wings spread" is only a lift (the carved wing is fused to the flank; the plate rides it);
feet are still chunky tan blocks; the belly's cream border is a coarse triangle saw, not the reference chevrons;
the carved tail is a short dark wedge under the primaries, no fan.

## Team repair pass (review/ad_notes_team.md, R0 = 6; stage 1 untouched, lock bdb3e4cf292c48ac)
- r06 baseline (stage 4): all gates PASS; no item 0.
- r07 M1: Critique: brow a 5 mm dark slab hovering over the eye ring, tips past the head, 8 slivers. Diagnosis: the
  9-station brow sat on the disc front with no sink, 4-7 mm section. Fix: brow_piece, a 6-station wedge (4-vert
  section: base pair 9 mm under the skin, front pair 10->6 mm proud), 24->16 mm tall, x .012 -> .092 (pulled in),
  z .528 -> .585 into the tuft base. Result: PASS, brow slivers 0; mostly buried under the old raised disc rim.
- r08 M2: Critique: two goggle rings. Fix: disc_piece rebuilt as ONE heart (half outline DISC_OUT in the front view,
  x <= .121 = 90% of head width, top on the brow line, bottom at the beak tip, open on the seam so the mirror joins
  it), 16 directions round the eye, dark rim 10 mm on the outer edge only. Result: one cream heart, brow now shows on
  its top edge; FAIL hit 2 (beak root sunk 12 mm crosses the disc's front AND back).
- r09 M2 cont.: Fix: beak root raised 20 mm between the eyes, seated 1 mm into the skin; disc bottom raised to the new
  tip. Result: PASS, hit 0.
- r10 M2 cont.: eye dome r .032 -> .027 (-15%), profile flatter (apex 8 -> 6 mm), pupil and lid scaled to match.
  Result: PASS; eyes sit inside the disc, no dome past the head outline (az000) or brow line (az090).
- r11 M3: Critique: tan foot bricks. Fix (stage 2): foot verts narrowed to 50% about x .067, squashed to top z .030,
  front verts 15 mm forward; talons moved to x .054/.067/.080. Result: PASS, min IoU 0.963; flat toe plates.
- r12 M3 cont.: LEG loop .075 -> .036 (ankle) so the leg paints cream down to the ankle, tan only on the toes. PASS.
- r13 M4: Critique: tail a lump, no fan. Fix: fan_piece, a 9 mm dark plate fanned 0-30 deg per half (60 total),
  pitched 20 deg down, scalloped tip (5 feathers), body= bound; the carved tail wedge painted dark before the toe rule.
  Result: PASS but 16 fan slivers (point root).
- r14 M4 cont.: fan root a 40 mm line, rows at 0/.4/.75/1. Result: slivers 0 on the fan; fan short in az090.
- r15 M4 cont.: fan length .125 -> .145. Result: PASS; scalloped fan in back34/top; edge-on stick in az090.
- r16 M5: Critique: one cream blob, saw border. Fix: CHEST loop z .40 (logged), bib/chest loops snapped at 6 mm,
  rule: cream below the bib loop, mid tan between the loops (front), brown above. Result: PASS, three bands.
- r17 final (orbit): all gates PASS: hit 0, float 0, z-fight 0, slivers 22 (0.9%), fold-overs 2 (0.08% tris / 0.09%
  area), drift 0, lock OK, min IoU 0.963, glbcheck OK. WARN clip 16 (1.14%: wing 8, disc 4, fan 4), stretch 14.
  --review, --compare rebuilt. Triangles s1 1134, s3/s4 2576 total.
Remaining: the fan is flat so az090 shows it edge-on as a stick (a downward-curved or stepped fan would read from the
side); feet are flat toe plates, not three separate toes; should-fix items (attack wing spread, head width, beak root
width, crown patch) not done.

## Team repair, second pass (review/verify_team.json: M3 PARTLY, M4 PARTLY; R0 = 18; stage 1 untouched)
- r18 baseline (stage 4): all gates PASS; no item 0.
- r19 M3: Critique: each foot one flat tan plate, not toes. Diagnosis: the carved foot is a single hull; vertex moves
  cannot split it. Fix: stage 2 narrows the plate 50% -> 30% (front verts x0.7 more) so it is the middle + rear toe
  only; stage 3 adds a 'toes' piece: two side toes per foot (3-section tan boxes, root inside the plate, splayed
  +-30 deg, 75 mm), talons moved to the three toe tips. Result: PASS, min IoU 0.953; three separate toes (az000, hero).
- r20 M4: Critique: fan small, a stick in az090, teal (stretch) at the tail root. Fix: fan length .145 -> .165, spread
  60 -> 80 deg, outer feathers drop .35 x |x| (a roof, so the side view shows area); bound rigid to the tail bone.
  Result: FAIL drift 1 (fan), clip 36.
- r21-r22: fan on its root-centre weights (= tail .97), dihedral .35 -> .20. Result: FAIL drift 1, fan clip 32.
- r23: plain body= weights: PASS, drift 0, but fan stretch 16. Diagnosis (weights printed): the fused wing's bone
  (tip at y .17, z .12, beside the tail) owns .1-.47 of the rump skin, so the fan's two halves follow opposite wings
  while its centre follows the tail; the drift check needs the fan to follow that skin.
- r24 fix: wing bone tip pulled up the flank (.11,.17,.12) -> (.12,.125,.18) so the wing lets go of the rump; the
  fan's remaining wing share x0.85 (FAN_WING), renormalised. Result: PASS; fan stretch 0, drift 0, fan clip 4; body
  stretch 6 -> 2, wing clip 8 -> 6, fold-overs 2 -> 0. (Tip at z .19-.20: stretch 0 but wing clip 14-16; rejected.)
  Fan reads as a dark wedge with area in az090 and a wide scalloped fan in back34.
- r25 final (orbit): all gates PASS: hit 0, float 0, z-fight 0, slivers 34 (1.3%; the narrowed foot plate adds 12),
  fold-overs 0, drift 0, lock OK, min IoU 0.953, glbcheck OK. WARN stretch 2 (body, 2.06x), clip 14 (0.98%: wing 6,
  disc 4, fan 4). --review, --compare rebuilt. Triangles s3/s4 2656.
Remaining: two teal body triangles beside the fan root and 4 pink fan triangles in the flap frames; the fan is still
shallower in az090 than the reference's; should-fix items not done (out of scope for the second pass).
