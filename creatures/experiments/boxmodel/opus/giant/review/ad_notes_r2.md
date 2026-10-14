# Art-direction notes, round 2 (reconciled, K=2 pass)

Round-2 scores (Fable 5.1 / Opus 5.5): 6 FIX / 5 FIX. Fix the must-fix list in order, then the should-fix items if turns allow. Keep everything in both keep lists (appendix) and in round 1 (`ad_notes.md`). Stage 1 stays locked; the stage-2 IoU floor stays > 0.9.

## Must-fix, in order

1. **Pieces drift off the body in poses (F2 major, O2 major; now gated).**
   - Fix: Stage 4: bind the moss, rocks, belt and loincloth with body= (weights from the skin under them), not bone=chest.
   - Check: techqa drift 0.
2. **Shoulder fold-over in the attack raise (O1 blocker, F4 minor).**
   - Fix: Stage 4: blend the chest and upper-arm weights on the deltoid ring (the raven fix used 60/40), and cap the raise if needed. If weights alone cannot clear it, add a logged stage-2 loop around the deltoid.
   - Check: heatmap and 4_posed: no purple on the pec-deltoid; flip_area close to 0.
3. **Mitt fists (F3 major, O3 major).**
   - Fix: Stage 2: carve a knuckle ridge of 4 separate bumps on the fist top with vertex moves. Vary the finger lengths: the middle longest, the little finger about 20% shorter. Stage 3: remove the uniform tan knuckle band, painting only the knuckle tops or nothing.
   - Check: fist close-up: four fingers with knuckles, not a mitt or a lampshade; az000: no comb of identical blocks.
4. **Loincloth flaps are rigid planks (F1 major, O8 minor).**
   - Fix: Stage 3: reshape the flaps as curved two-segment plates that follow the thighs and buttocks, seated on the body with no daylight, and thinning toward the hem.
   - Check: az090: no gap behind the flaps; close-up: the flaps drape.
5. **Sliver cracks (F5 minor: finger gaps; O5 minor: brow shelf, jaw-chest seam).**
   - Fix: Stage 2: widen the needle triangles at the finger gaps, the brow shelf and the jaw-chest seam with vertex moves.
   - Check: close-ups: no black crack lines; the sliver count goes down.

## Should-fix (a minor from one reviewer)

- O4: shoulder blades and a spine groove on the back slab (stage 2 vertex moves).
- O7: give the rocks irregular shapes (non-uniform scale, vertex jitter), separate the two that intersect, and lay the back34 rock down.
- F7: make the toenails wedges instead of cubes.

## Dropped (the other reviewer's keep list contradicts it)

- F6 (no mouth line, gash sockets): contradicted by the Opus keep list ("eyes sunk in dark sockets, cream tusks rising from a mouth line").
- O6 (hex-nut eyes): contradicted by the Fable keep list ("brow-shadowed amber eyes").

## Appendix: both reviews verbatim

### Fable 5.1: FIX 6
- **F1** [major/pieces] where: 1_beauty az090 (both flaps) and hero (front flap); 2_closeups belt and loincloth colour
  - what: The loincloth flaps hang as stiff planks from the belt's outer edge. In az090 the back flap has clear daylight (~10 cm at giant scale) between it and the buttocks and the front flap stands off the thighs; neither drapes on the body (round-1 item 2: thickness done, seating not).
  - fix: Stage 3: rotate each flap about its top edge so its top half lies on the body: back flap draped on the buttocks (touching from belt to mid-buttock), front flap on the belly/thigh below the belt; widen the back flap to ~70% of the front flap; keep the wedge thickness.
  - check: az090 and back34 show no daylight between flap and body over the top half; float 0; loincloth sliver <= 2.
- **F2** [major/animation] where: 3_tech all four views: belt, loincloth, every moss clump and rock are blue; techqa drift moss 4, rocks 3, loincloth 3
  - what: Every attached piece leaves the surface it rests on in a pose: moss and rocks lift off the shoulders in the attack raise, belt and loincloth come off the waist.
  - fix: Stage 4: bind each piece to the bone that drives the surface under it: belt and loincloth with bone=pelvis; each moss clump and rock with the shoulder/clavicle bone beneath it (the round-1 spine binding is what makes them drift when the shoulders rotate).
  - check: techqa drift 0 for all pieces; no blue in 3_tech; attack_f010 shows moss and rocks seated on the shoulders.
- **F3** [major/form] where: 2_closeups fist colour and wire; 1_beauty az000 both fists
  - what: The fist top is a smooth featureless dome with no knuckle ridge, and the four fingers are identical blocks of one length; only paint suggests knuckles. Target asks for separate fingers AND knuckles; round-1 item 5 half done (paint, nails, thumb yes; geometry no).
  - fix: Stage 2: chamfer a knuckle ridge across the fist top at the finger roots and raise four knuckle bumps 3-4 cm; vary finger lengths (middle longest, little finger ~30% shorter). Keep the thumb.
  - check: Fist close-up silhouette shows a knuckle row; the four nail faces do not line up; IoU > 0.9.
- **F4** [minor/technical] where: 3_tech hero, az090 and az000: purple triangles at both front armpit seams; techqa body flip 4
  - what: Four fold-over triangles remain where the pec meets the deltoid in the overhead raise (36 -> 4; gate met at 0.21%, but round-1 asked for no purple).
  - fix: Stage 4: push the seam-loop blend to 50/50 chest/upper-arm on those faces, or cap shoulder flexion at ~130 deg; if it persists, stage 2: the logged loop 5 cm below the armpit.
  - check: No purple in 3_tech; flip 0.
- **F5** [minor/technical] where: 1_beauty az090 near fist; 3_tech az090 same fist
  - what: The finger gaps are needle slits that read as three black scratch lines across the fist edge-on.
  - fix: Stage 2: widen each finger gap to >= 2 cm and chamfer its edges so the separation reads as a groove, not a cut.
  - check: az090 shows grooves between the fingers, no hairline black lines; body sliver count does not rise.
- **F6** [minor/face] where: 2_closeups head colour; 1_beauty az000 face
  - what: No mouth line: the tusks rise from the cheek beside the nose, not from a mouth. The socket recess is one full-width black slot under the brow and reads as a gash.
  - fix: Stage 2: inset a mouth line between the tusk roots ~3 cm below the nose; raise the brow underside between the eyes so the slot splits into two sockets. Stage 3: paint the sockets dark blue-grey (~30% value), not black.
  - check: az000 thumbnail: tusks rise from a mouth line; two separate shadowed sockets.
- **F7** [minor/pieces] where: 1_beauty back34 far foot and hero both feet
  - what: Toenails are dark cubes stacked on the toe fronts.
  - fix: Stage 3: make each nail a wedge sunk 1 cm into the toe with only its front face dark.
  - check: back34: nails read as caps on the toes, not blocks on them; toenails zfight 0.
- keep: hunched mass: small sunken head, massive shoulders, arms to the knees (troll read) | moss as lumpy clumps and boulders bedded on the shoulders (sliver 0, float 0) | brow-shadowed amber eyes, cream tusks, blue-grey fists with thumb and nails

### Opus 5.5: FIX 5
- **O1** [blocker/technical] where: 3_tech hero, az090 and az000: purple on both upper chests, from the neck base to the deltoid
  - what: The shoulders still fold over in the attack raise. techqa passes (flip 4 = 0.21%), but the four flipped triangles are the largest on the torso and cover the pectoral–deltoid plane on both sides. The heatmap is right: the % gate undercounts large triangles. The round-1 check 'no purple in 3_tech' fails.
  - fix: Stage 4: on the verts of those triangles, blend chest/clavicle and upper arm 50/50, give the neck-base verts ~30% neck weight, and cap the overhead raise at ~140°. If any flip remains, stage 2 (logged): add a loop from the neck base to the armpit that splits those long triangles.
  - check: no purple in 3_tech; techqa body flip 0; the upper chest stays convex in attack_f010 and attack_f020
- **O2** [major/technical] where: 3_tech all four views: moss, rocks, belt and both loincloth flaps are blue; techqa drift moss 4, rocks 3, loincloth 3
  - what: Every piece sits on the body at rest and comes off it in poses. techqa says ok:true only because drift is not gated; the heatmap is right. The round-1 bone=chest bind does not follow the shoulder skin in the raise.
  - fix: Stage 4: rebind piece_moss, the belt and the top rows of the flaps with bind(body=), so they take the skin weights under them. Bind each rock with bone= set to the bone that dominates the skin under it (clavicle or upper arm, not chest). Sink the moss and rock bases by 1/3 so any remaining motion stays inside the surface.
  - check: no blue in 3_tech; techqa has no drift key on moss, rocks or loincloth; the moss stays on the shoulder in attack_f020
- **O3** [major/form] where: 1_beauty az000 and back34 hands; 2_closeups fist; 1_beauty az090 hand at the hip; 3_tech az090 same spot
  - what: The fists still read as mitts. The knuckle row is one uniform tan band around the whole hand, which looks like a lampshade in the fist close-up. Four identical finger blocks hang below it like a comb (az000). The black nail plates read as a grille of slots in back34 and as dark hairline strokes in az090, where 3_tech also marks a sliver.
  - fix: Stage 3: repaint the tan band to the body's blue-grey, leaving one lighter facet on each knuckle top. Rebuild the nails as small wedges ≤ 1/3 of the finger width, sunk 5 mm into each fingertip. Stage 2: vary finger length (middle +15%, little −30%), curl the tips 20° toward the palm, and chamfer a groove between the knuckles.
  - check: back34 shows no black slots; az090 shows no dark strokes at the hand; az000 finger lengths differ; the fist close-up shows four knuckle bumps, not a band
- **O4** [minor/form] where: 1_beauty back34 back; az090 back line
  - what: The back is still one flat slab and the side view a box, with no shoulder blades, spine groove or trapezius hump (round-1 item 7).
  - fix: Stage 2: flatten two shoulder-blade planes angled ~15° outward, sink the spine-line verts 3–4 cm into a groove, and round a trapezius hump between the neck and the moss. Stage 4: pitch the spine 10–15° forward in idle and move, counter-rotating the neck.
  - check: back34 shows two blade planes and a groove; the az090 back line curves; IoU > 0.9
- **O5** [minor/technical] where: 2_closeups head colour (black slit along the brow top); 3_tech hero brow, and az000/az090 under the jaw (yellow)
  - what: The hairline sliver along the brow shelf is still there and renders as a black crack. A second sliver strip runs along the jaw–chest seam.
  - fix: Stage 2: slide or merge the brow-top loop onto the brow edge, and do the same for the jaw–chest seam loop.
  - check: head close-up shows no black slit over the brow; no yellow at the brow or under the jaw in 3_tech; body sliver ≤ 4
- **O6** [minor/face] where: 2_closeups head colour; 1_beauty az000 eyes
  - what: The goggles are gone, but each eye is a thick amber hexagonal ring around a small hexagonal pupil, which reads as a hex nut.
  - fix: Stage 3: rebuild piece_pupil with 8 sides at ~65% of the eye width, and thin the amber ring to about 1/6 of the eye width.
  - check: at az000 thumbnail size the pupils read first and the ring second
- **O7** [minor/pieces] where: 2_closeups moss and rocks colour/wire; 1_beauty back34, rock on the shoulder
  - what: The rocks are regular icosahedra, like d20 dice. Two of them pass into each other on the shoulder, and the back34 rock stands up like a horn.
  - fix: Stage 3: scale each rock non-uniformly (e.g. 1.0/0.7/0.5), flatten its underside and rotate each one differently. Merge the overlapping pair into one rock or separate them, and lay the back34 rock 30° flatter.
  - check: moss and rocks close-up shows three distinct rock silhouettes with no overlap; back34 shows no horn
- **O8** [minor/pieces] where: 1_beauty az090 front and back flaps; 2_closeups belt and loincloth
  - what: The loincloth is now solid and seated, but the flaps hang as straight rigid planks: thin sticks edge-on in az090 and a flat board in the close-up.
  - fix: Stage 3: bend the front flap 10–15° to follow the thighs and the back flap to follow the curve of the buttocks. Widen both bottoms 15% and round the bottom corners.
  - check: in az090 the flaps follow the body's curve; float 0; loincloth sliver ≤ 2
- keep: hunched troll mass: small sunken head under massive shoulders, arms to the knees | moss as lumpy green mounds with a rock bedded in one; it reads as mounds in az090 | face: heavy brow, eyes sunk in dark sockets, cream tusks rising from a mouth line

