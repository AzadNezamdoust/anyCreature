# Art-direction notes, repair round 2 (reconciled, K=2)

Scores (Fable 5.1 / Opus 5.5): 7 FIX / 6 FIX.

**Stage 1 is locked. No unlock is authorised for this pass.** Every fix below is a stage-2, stage-3 or stage-4 change. Stage-2 IoU against stage 1 must stay above 0.9 in every view (minimum is 0.931 now); stage 3 never edits the base; all gates pass.

Keep what works (round 1 fixed these; do not regress):
- Fold-overs 0 and drift 0 in every pose (r09-r13: no foot key in the launch, thigh -8). Do not re-key the hind foot.
- A continuous black V mouth line across the snout front (r14-r15), two small nostril dots, no chevrons (r17).
- Pupil bar on the front of the gold eye only, no goggle stripe (r18).
- Green webbing between the hind toes (r22); belly widened to a keel (r23).
- Squat sitting silhouette tilted up at the front, matching 5_reference side.

Fix the must-fix list in order, then the should-fix items if turns allow. Check every item in your own `--review` packet before you call it done.

## Must-fix, in order

0. **Kit gates.** No FAIL on the current kit. clip_area_pct 0.91 (spots 0.66%, tongue 0.26%) is under 1.0 but close; item 2 takes the spot pieces off the body and should cut it to about 0.3%. Do not let it reach 1.0. stretch 8 triangles (worst 5.57x): the tongue stretches by design; if after item 1 any teal triangle sits outside the tongue, it is a stray weight on a toe or leg: fix it with `bind(..., bone=foot.L/R)`.

1. **Tongue pokes out under the chin in the hop and is a flat plank in the attack (O major).**
   - Where: 4_posed move_f012: a flat tongue plate sticks out below the chin, beside the front leg, during the hop; attack_f012: the tongue shoots out as a thin flat board.
   - Fix: Stage 4 (clip keys): key the tongue bone at its rest (retracted) transform on every key of the move and idle clips, so the jaw/chest pose cannot carry it out. Stage 3: rebuild the tongue as a 6-sided tube (depth at least 50% of its width) with a wider round pad at the tip (1.6x the shaft width), pink, rooted in the mouth floor exactly as now (r26: pulling it back fails float; keep its contact).
   - Check: 4_posed move_f006 and move_f012: no tongue outside the mouth; attack_f012: a round-section tongue with a pad tip; float 0; teal stretch only on the tongue.

2. **Back spots are small flat dome pieces of one size and shape (F major).**
   - Where: 1_beauty back34 and az090: the spots are similar-sized dark hexagonal plates pasted on the back; 5_reference top and rear: large irregular dark spots of mixed size, some on the thighs, part of the surface. The spot pieces are also 0.66% of the clip warning.
   - Fix: Stage 3 (paint): delete the spot pieces and paint the spots onto base faces instead: 7-9 groups of 2-5 adjacent back faces each (pick by face-centre distance from 8 seed points), one group of 1 face, two groups of 6 faces, two groups on each thigh top; colour the existing `dark green`. Borders then follow edges by construction.
   - Check: 1_beauty back34 and 5_reference top: irregular spots of mixed size, flush with the surface; clip_area_pct drops to about 0.3%; colour count unchanged.

3. **Cream belly is a flat-sided box from the front (F major; round 1 item 5 partly done).**
   - Where: 1_beauty az000: the cream panel has straight vertical sides and square bottom corners, filling the whole front; 5_reference front: the cream throat and belly is an oval with green wrapping round its sides.
   - Fix: Stage 3 (paint only, no IoU cost): paint the outermost column of front belly faces each side green from the shoulder down to two-thirds of the belly height, and the two bottom corner faces green, so the cream reads as an oval. Stage 2 (optional, inside the IoU floor): pull the belly's lowest centre seam verts down 0.5% of height more and the lower corner verts in 2% of body width.
   - Check: 1_beauty az000: a rounded cream oval with green sides, no box corners; borders on edges.

4. **Hind-foot toes are needle sticks (F major).**
   - Where: 2_closeups hind limb colour and toes: the long hind toes are thin square sticks with tiny cube tips; edge-on they read as slivers. 5_reference side and top: long toes with round pads at the tips.
   - Fix: Stage 3: thicken the hind toes to 1.5x their width and 1.3x their depth (the r28 front-toe change, applied to the hind feet), and replace the cube tips with 6-sided pad discs about 2x the toe width, slightly flattened, sunk 30% into the toe tip. Keep them rigid to foot.L/R; keep the r22 web edge on the thicker toes.
   - Check: 2_closeups hind limb colour: toes with visible thickness and round pads like 5_reference; drift 0, slivers under 1%.

5. **Eyes are octagonal gold nuts, not domes (O minor).**
   - Where: 1_beauty az000 and 2_closeups head colour: each eye is an 8-sided bulb with a flat top and straight sides; 5_reference front: round gold domes.
   - Fix: Stage 3: give the eye lens 10-12 sides and two cap rings (at 0.7 and 0.95 of the radius) so the top is rounded; keep the r21 seat (proud on a low green rim) and the front-only pupil bar.
   - Check: 1_beauty az000 and hero: round gold domes; eye hit/float/z-fight 0; blink causes no fold-overs.

## Should-fix

- O: thighs read as wide boxes in az180 (5_reference rear: rounded masses). Stage 2: pull the 4 outer corner verts of each thigh in by about 8% of thigh width, inside the IoU floor.
- Back34 still shows a small green lid behind each eye (r21 residual): Stage 2, lower the rear turret verts 5 mm more without moving the lens.

## Dropped

- O "no visible webbing between the long toes": the web is there since r22 (hero, toes close-up); item 4's thicker toes will make it read better.
- O "eyes sit at the head sides, not on top": 5_reference front and top place them at the top corners of the head as ours; only the shape (item 5) stands.
- Nothing needs stage 1.

## Appendix: both reviews verbatim

### Fable 5.1: FIX 7
- top_issues:
  - 2_closeups hind limb colour / toes: hind-foot toes are thin needle sticks that read as slivers edge-on.
  - 1_beauty back34: back spots are small flat dark polygons pasted on the surface, identical in size and shape.
  - 1_beauty az000: the cream belly border on the throat is a hard straight line across faces rather than following an edge loop.

### Opus 5.5: FIX 6
- top_issues:
  - 4_posed attack_f012/move_f012: tongue is a flat plank and pokes out under the chin during the hop
  - 1_beauty az090/2_closeups hind limb: hind legs are thick blocky tubes; no visible webbing between the long toes
  - 1_beauty az000: eyes sit at the head sides as gold octagon nuts, not domes bulging on top

### Kit gates (this build, current kit)
- kit_gate_fails: none
- kit_warnings:
  - WARN s4 qa: 8 triangles stretch past 2x their rest length in a pose (teal, worst 5.57x): a stray weight, unless the part stretches by design (a tongue)
  - WARN s4 qa: 29 triangles (0.91% of surface) clip through the body in a pose that did not at rest (pink): a limb through a flap, a paw through the cheek
- clip_area_pct 0.91, stretch 8
