# Art-direction notes, round 3 (reconciled, K=3 pass)

Round-3 scores (Fable 5.1 / Opus 5.5): 5 FIX / 5 FIX.

**The owner authorised a stage-1 unlock for this pass, for these items only: the hands (knuckles and fingers), the brow shelf and jaw-chest seam topology, and the back.** Follow the unlock procedure in `REPAIR.md`, and change nothing else in stage 1. Every other rule holds: stage-2 IoU > 0.9 against the new stage 1, stage 3 never edits the base, all gates pass.

Fix the must-fix list in order, then the should-fix items if turns allow. Keep everything in both reviewers' keep lists (appendix). Check every item in your own `--review` packet, which shows the idle pose, before you call it done.

## Must-fix, in order

1. **Mitt fists (F major, O major).**
   - Fix: Stage 1 (unlock):
     - Build a knuckle row: four bumps of 3-4 cm at the finger roots.
     - Make the middle finger 10-15% longer and the little finger about 25% shorter.
     - Curl the fingertips about 20 deg toward the palm.
     - Make the finger gaps at least 2 cm wide and chamfered, not slits.
   - Check: fist close-up silhouette: a stepped knuckle row; az000: finger lengths differ; az090: no black lines at the hand; sliver does not rise.
2. **Loincloth flaps stand off in the idle pose (F major, O major).**
   - Fix: Stage 3: rebuild each flap as a 2-3 segment plate:
     - tuck the top segment under the belt;
     - lay the middle segment on the belly and thigh (front flap) or the buttock (back flap), touching over the top half;
     - thin the bottom segment toward the hem, widen it about 15%, and round the corners.
     Use 4-6 quads per flap. Check it IN THE IDLE POSE: the packet shows the idle clip's first frame, and the rest pose hid this last time.
   - Check: your own --review packet, az090 and back34: no daylight between flap and body over the top half; float 0; loincloth sliver <= 2.
3. **Nails read as black slots (F major, O minor).**
   - Fix: Stage 3: rebuild the finger and toe nails as wedges no wider than 1/3 of the digit, sunk 1 cm into it, mid blue-grey with only the front face darker.
   - Check: back34 and hero at thumbnail size: no black rectangles; the nails read as caps; zfight 0.
4. **Sliver cracks at the brow, jaw-chest seam and finger gaps (F major, O minor).**
   - Fix: Fix the needle triangles at their source. The stage-1 unlock covers the brow-shelf and jaw-chest topology; a stage-2 slide is fine if that is enough.
   - Check: head close-up: no black line under the brow; 3_tech: no yellow at the brow, jaw or hand; body sliver <= 4.

## Should-fix

- F+O minor: irregular rocks. Non-uniform scale, flat undersides, separate the pair that touches, lay the back34 rock 30 deg flatter.
- F+O minor: a back with shoulder-blade planes and a spine groove (stage 2, or stage 1 through the unlock).
- F+O minor: an 8-sided pupil at about 65% of the eye, and a thinner amber ring.
- O: end the belt on the body surface.

## Appendix: both round-3 reviews verbatim

### Fable 5.1: FIX 5
- round-2 item "1 pieces drift in poses": **done**. techqa drift 0 on every piece; no blue or brown anywhere in 3_tech.
- round-2 item "2 shoulder fold-over": **done**. body flip 0, no purple in 3_tech; the upper chest stays convex in attack_f010 and f020.
- round-2 item "3 mitt fists": **partly**. the tan knuckle band is gone, but the fist top is still a smooth dome with no knuckle bumps and four identical finger blocks hang in a row (fist close-up, az000).
- round-2 item "4 loincloth planks": **not**. az090 shows both flaps as thin sticks hanging straight from the belt with daylight to the thigh and the buttocks; the close-up shows a flat board with one crease at the top.
- round-2 item "5 sliver cracks": **not**. the black slit still runs the full brow top in the head close-up; the finger gaps are three black hairline strokes at the hip in az090 and 3_tech; the jaw-chest seam is still yellow in 3_tech az000.
- round-2 item "should-fix O4 back blades and groove": **not**. back34 is one smooth rounded slab.
- round-2 item "should-fix O7 rocks": **not**. still regular icosahedra, two touch, and the back34 rock stands up like a horn.
- round-2 item "should-fix F7 toenail wedges": **not**. nails are flat black rectangles that read as slots in back34 and hero.
- **F1** [major/pieces] where: 1_beauty az090 both flaps and hero front flap; 2_closeups belt and loincloth colour/wire
  - what: each flap is a straight rigid plate hanging from the belt's outer edge; edge-on it is a stick with ~10 cm of daylight to the thigh and the buttocks, and the close-up shows a flat board with one crease at the top.
  - fix: Stage 3: rebuild each flap as a two-segment plate bent ~15 deg at 40% of its height: the top segment lies on the belly/thigh (front) and the buttocks (back) with zero gap, the hem segment hangs free; thin from ~4 cm at the belt to ~1.5 cm at the hem; widen the hem 15%.
  - check: az090 and back34 show no daylight between flap and body over the top half; loincloth float 0, sliver <= 2.
- **F2** [major/technical] where: 2_closeups head colour, brow top; 1_beauty az090 hand at the hip; 3_tech az000 chest under the jaw and az090 hand
  - what: a black hairline slit runs the length of the brow shelf; the finger gaps read as three black scratch strokes edge-on; a sliver strip runs along the jaw-chest seam.
  - fix: Stage 2: slide the brow-top loop fully onto the brow edge and merge it; widen each finger gap to >= 2 cm and chamfer its edges so it reads as a groove; slide the jaw-chest seam loop onto the chest edge.
  - check: head close-up shows no black line on the brow; az090 shows no dark strokes at the hand; body sliver <= 4 and no yellow at the brow, jaw or hand in 3_tech.
- **F3** [major/form] where: 2_closeups fist colour and wire; 1_beauty az000 both fists
  - what: the fist top is a smooth featureless dome with no knuckle ridge and four identical finger blocks hang below it like a comb; only the thumb reads.
  - fix: Stage 2: raise four knuckle bumps 3-4 cm at the finger roots with vertex moves; lengthen the middle finger +15% and shorten the little finger -25%; curl all fingertips 20 deg toward the palm.
  - check: fist close-up silhouette shows a knuckle row and staggered fingertips; az000 shows no comb of equal blocks; IoU > 0.9.
- **F4** [major/pieces] where: 1_beauty back34 far foot and near hand; hero both feet; az090 near foot
  - what: toenails and fingernails are flat black rectangles on the digit fronts and read as a grille of slots at thumbnail size.
  - fix: Stage 3: rebuild each nail as a wedge <= 1/3 of the digit width sunk 1 cm into the digit front, painted mid blue-grey (~35% value) with only the front face darker.
  - check: back34 at 128 px shows no black rectangles; nails read as caps on the toes; toenails zfight 0.
- **F5** [minor/pieces] where: 2_closeups moss and rocks colour/wire; 1_beauty back34 top rock
  - what: the rocks are regular icosahedra (d20 dice), two touch on the shoulder, and the top rock in back34 stands upright like a horn.
  - fix: Stage 3: scale each rock non-uniformly (1.0/0.7/0.5), rotate each differently, lay the back34 rock 30 deg flatter with its base sunk 1/3 into the moss, and separate the touching pair by >= 5 cm.
  - check: rocks close-up shows three different silhouettes with no contact; back34 shows no vertical spike; rocks float 0.
- **F6** [minor/form] where: 1_beauty back34 back
  - what: the back is one smooth rounded slab with no spine groove or shoulder blades.
  - fix: Stage 2: sink the spine-line verts 3-4 cm from the moss to the belt and flatten two shoulder-blade planes angled ~15 deg outward.
  - check: back34 shows a groove and two blade planes; IoU > 0.9.
- **F7** [minor/face] where: 2_closeups head colour eyes; 1_beauty az000
  - what: each eye is a thick amber hexagonal ring around a hexagonal pupil and reads as a hex nut at close range.
  - fix: Stage 3: rebuild piece_pupil 8-sided at ~65% of the eye width and thin the amber ring to ~1/6 of the eye width.
  - check: az000 thumbnail: the pupils read first, the ring second; eye float 0.
- keep: hunched troll mass: small sunken head under massive shoulders, arms to the knees | moss clumps and rocks now stay bedded on the shoulders in every pose (drift 0, float 0) and the shoulders no longer fold in the raise (flip 0) | brow-shadowed amber eyes, cream tusks, and the blue-grey / olive / tan palette

### Opus 5.5: FIX 5
- round-2 item "Pieces drift off the body in poses": **done**. techqa drift is 0, and 3_tech has no blue or brown.
- round-2 item "Shoulder fold-over in the attack raise": **done**. techqa flip is 0, 3_tech has no purple, and the chest stays convex in attack_f010.
- round-2 item "Mitt fists": **partly**. The tan knuckle band is gone. But the back of the hand is still a smooth dome with no knuckle row, the four finger tabs are near-identical (az000), and back34 shows black nail slots like a grille.
- round-2 item "Loincloth flaps are rigid planks": **not**. az090: both flaps hang as straight sticks with daylight between them and the belly and buttocks. Close-up: a flat grid board with a kinked top segment.
- round-2 item "Sliver cracks": **not**. The head close-up still shows a black crack along the whole brow shelf. 3_tech az000 and hero show a yellow strip under the jaw, and the az090 fist shows black slit lines.
- round-2 item "should: O4 shoulder blades and spine groove": **not**. back34: the back is still one flat slab.
- round-2 item "should: O7 irregular rocks": **not**. The rocks are still regular icosahedra. Two of them touch, and the back34 rock stands up like a horn.
- round-2 item "should: F7 toenail wedges": **not**. hero: the nails read as dark holes or blocks in the toe fronts.
- **O1** [major/form] where: 2_closeups fist colour and wire; 1_beauty az000 both hands, back34 both hands, az090 hand at the hip
  - what: The fists still read as mitts. The back of the hand is a smooth faceted dome with no knuckle row; in wire it is a lampshade of long triangles. Four near-identical finger tabs hang from its rim like a fringe (az000). In back34 the nails show as four black slots per hand, like a grille, and in az090 the finger gaps render as black scratch lines.
  - fix: Stage 2: raise four knuckle bumps on the fist top by moving the finger-root verts up and out 3-4 cm each, alternating. Shorten the little finger 25% and lengthen the middle finger 10%. Curl the fingertips about 20 deg under toward the palm so the fist closes. Widen each finger gap to at least 2 cm with a chamfer. Stage 3: rebuild the nails as wedges no wider than 1/3 of the finger, sunk into the fingertip, with only the tip face dark.
  - check: Fist close-up silhouette: a stepped knuckle row. az000: the finger lengths differ. back34: no black slots. az090: no black lines at the hand. Body sliver does not rise.
- **O2** [major/pieces] where: 1_beauty az090 both flaps, back34 back flap; 2_closeups belt and loincloth colour/wire
  - what: The loincloth flaps are still rigid boards. In az090 both hang as straight vertical sticks, with daylight between them and the belly, thighs and buttocks. The front flap is a flat plate with a uniform triangle grid, and its top segment kinks over the belt.
  - fix: Stage 3: rebuild each flap as a 2-3 segment plate. Tuck the top segment under the belt. Rotate the middle segment 10-15 deg so it lies on the belly and thigh (front flap) or the buttock (back flap), touching over the top half. Thin the bottom segment toward the hem. Widen the bottoms 15%, round the corners, and drop the uniform grid; 4-6 quads per flap is enough.
  - check: az090 and back34: no daylight between flap and body over the top half. float 0. Loincloth sliver <= 2.
- **O3** [minor/technical] where: 2_closeups head colour (under the brow ledge); 3_tech az000 and hero (yellow strip under the jaw)
  - what: A black crack still runs the full length of the brow shelf. A sliver strip also remains along the jaw-chest seam.
  - fix: Stage 2: slide the brow-underside loop onto the brow edge, or merge those verts, so no needle triangle remains. Do the same for the jaw-chest seam loop.
  - check: Head close-up: no black line under the brow. 3_tech: no yellow at the brow or jaw. Body sliver <= 4.
- **O4** [minor/pieces] where: 2_closeups moss and rocks colour/wire; 1_beauty back34 and hero, shoulder tops
  - what: The rocks are regular icosahedra, like d20 dice. Two of them touch, and the back34 rock stands upright like a horn.
  - fix: Stage 3: scale each rock non-uniformly (about 1.0/0.7/0.5), flatten its underside, rotate each one differently and jitter 2-3 verts. Separate or merge the touching pair. Lay the back34 rock about 30 deg flatter and sink its base by 1/3.
  - check: Moss and rocks close-up: three distinct rock silhouettes, none touching. back34: no rock standing up like a horn.
- **O5** [minor/form] where: 1_beauty back34 back; az090 back line
  - what: The back is one flat slab, with no shoulder blades, spine groove or trapezius.
  - fix: Stage 2: flatten two shoulder-blade planes angled about 15 deg outward, sink the spine-line verts 3-4 cm into a groove, and round a trapezius hump between the neck and the moss.
  - check: back34: two blade planes and a groove. IoU > 0.9.
- **O6** [minor/face] where: 2_closeups head colour, both eyes
  - what: Each eye is a hexagonal amber ring round a hexagonal black pupil. At close range it reads as a hex nut.
  - fix: Stage 3: rebuild piece_pupil with 8 sides at about 65% of the eye width, and thin the amber ring to about 1/6 of the eye width. Keep the brow shadow.
  - check: Head close-up: the pupil reads first and the ring second.
- **O7** [minor/pieces] where: 2_closeups belt and loincloth colour, left end of the belt
  - what: The end of the belt runs past the flank into the air as a thin strap, with daylight under it.
  - fix: Stage 3: end the belt on the body surface by pulling its last segment in onto the flank.
  - check: Belt close-up: the belt ends on the body, with no strap edge against the background.
- **O8** [minor/pieces] where: 1_beauty hero feet, az090 near foot
  - what: The toenails read as dark square holes or blocks in the fronts of the toes.
  - fix: Stage 3: rebuild piece_toenails as wedges sunk 1 cm into each toe, with only the front face dark.
  - check: hero: the nails read as caps on the toes. Toenails zfight stays 0.
- keep: Hunched troll mass: a small sunken head under massive shoulders, arms to the knees, and short thick legs | Palette: blue-grey skin, green moss clumps, a tan belt and loincloth, cream tusks and amber eyes | Tech is now clean in poses: drift and flip are 0, and the overhead raise keeps the chest convex

