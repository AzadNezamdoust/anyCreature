# goblin (abc/c1): art-director notes, team round

**Score: 6.5 / 10.  Verdict: FIX.**

It reads as a goblin in one glance from every view (big domed head, long sideways ears, hooked
nose, fanged grin, belt + buckle, tattered cloth, arms to the knees). Tech is clean (hit/float/
drift 0, flips 0.13%). What holds it back is proportion below the belt and the face at close
range: the legs are thick columns with no knee, and the eyes are small hex beads buried under a
cap-like brow. Both are fixable inside stages 2-3; no stage-1 unlock needed.

## Keep (must not regress)
- Head silhouette and identity: ears sideways with the slight back sweep (az000, top view match
  the sheet), hooked nose, domed skull, the hunched az090 profile.
- Colour regions: light belly patch, light inner ear, dark belt + brass buckle, cream fangs,
  mouth slot. 8 colours, borders on loops.
- Tech state: hit/float/drift 0, flips 3 (0.13% / 0.24% area), slivers 1.4%, arms hang clear
  of the flank in every posed frame (4_posed.jpg).

## Must-fix (ordered by visual damage)

1. **Legs are thick, knee-less columns (silhouette vs reference).**
   - Where: 5_reference.jpg side and front rows; 1_beauty.jpg az090, az000; 2_closeups.jpg hind limb.
   - What: the thigh is as deep as the torso and runs straight into the foot; the reference has
     thin thighs and shins (about 40% of the model's width) with a clear forward knee bend. The
     hind-limb close-up shows the thigh as one block fused to the hip at belt width.
   - Stage: 2.
   - Fix: narrow the thigh and shin rings 25-30% in x and y about each leg's centre line
     (shin a touch thinner than the thigh); push the knee ring forward (-y) by ~6% of body
     length and the ankle back so the shin reads as a bent lower leg; pinch the knee ring to
     make a readable joint. Keep the foot as is. IoU stays >0.9 (legs are <15% of any view).
   - Check: 5_reference.jpg side and front rows next to the sheet: thigh width in the side
     view no more than ~45% of the torso depth, a visible knee angle; 2_closeups.jpg hind limb
     shows thigh / knee / shin as three masses.

2. **Eyes too small and set too deep; they do not carry the face.**
   - Where: 1_beauty.jpg hero (the eye is a bead), 2_closeups.jpg fangs crop and head colour;
     5_reference.jpg front row (reference eye ~1/4 of head width, model ~1/8).
   - Stage: 3.
   - Fix: eye lens radius +50% (0.031 -> ~0.047), elongate it 1.4:1 into an almond tilted
     with the outer corner up (the angry look), front face flush with the cheek plane, not
     recessed; pupil as a vertical slit or a smaller dark disc (<35% of the lens). Keep it
     yellow #f2d23c. Bind with body= so it rides the brow in idle.
   - Check: 1_beauty.jpg hero and az000: both eyes readable at thumbnail size, yellow is the
     first thing the face says; 2_closeups.jpg fangs crop shows no dark gap between lens and
     socket rim.

3. **Brow overhang reads as a cap/hood brim.**
   - Where: 1_beauty.jpg hero and az090; 2_closeups.jpg head colour: a hard horizontal shelf
     with a black shadow band under it, the skull looks like a helmet sitting on the face.
   - Stage: 2.
   - Fix: pull the brow ring back (+y) by ~40% of its current overhang (roughly 2-3% of body
     length), so the overhang is a heavy brow not a brim; keep the inner-brow-down tilt;
     flatten the band between brow and skull so the dome flows into the brow instead of
     stepping; lift the cheekbone slightly (+z ~1.5% of height) so the eye socket is framed by
     brow and cheek, not by a shelf.
   - Check: 1_beauty.jpg az090: the forehead-to-nose line is one continuous angle with a bump
     at the brow, no step; hero: the shadow band under the brow is at most the eye height.

4. **Hands are stub mitts: fingers too short, claws barely visible.**
   - Where: 1_beauty.jpg az000 and hero (hand = small paddle with three nubs), 2_closeups.jpg
     front limb; 5_reference.jpg front/rear rows (reference fingers are as long as the hand).
   - Stage: 3.
   - Fix: finger length +60% (0.036+0.026 -> ~0.058+0.040, i.e. finger total ~9% of height),
     spread the three fingers ~20 degrees apart with a slight curl, claws +50% length and
     thickness so they read at hero size. Bind fingers and claws with body= on the palm
     (the earlier drift was from leg heat weights, which arm_clean now removes).
   - Check: 1_beauty.jpg az000: the hand reads as three distinct clawed fingers; techqa.json
     drift stays 0; 4_posed.jpg attack_f006 the fingers follow the swipe without separating.

5. **Belt stands off the body at the back and the back flap is a bib.**
   - Where: 1_beauty.jpg az090 (belt projects behind the butt as a shelf above the flap),
     hero (dark gap under the belt's right rear corner), back34/az180 (back flap covers the
     whole rear from belt to mid-thigh, wider than the hips).
   - Stage: 3.
   - Fix: refit the belt's rear columns to within 5-8 mm of the skin (after item 1 narrows
     the hips there is room; raise the belt's rear edge slightly rather than stepping it out);
     back flap width to ~75% of the hip width, length to ~2/3 of the current, with 3-4 tatters
     like the front; give both flaps a visible thickness edge (>= 8 mm).
   - Check: 1_beauty.jpg az090: belt hugs the body all round, no shelf; back34: flap narrower
     than the hips, belt line continuous over it; techqa.json hit/float 0.

## Should-fix (short)
- Skull pole nub: small point at the top of the head (2_closeups head wire, back34); flatten
  the cap ring (Stage 2).
- Collar shelf: az000 shows a flat T-shirt shoulder line beside the jaw; slope the trapezius
  ring down another ~2% of height and narrow the chest ring 5% (Stage 2).
- Mouth crease runs back under the cheek as a dark seam (hero, fangs crop); flatten the slot
  faces behind the lip corner so the grin ends at the cheek (Stage 2).
- Move clip: 4_posed move_f009/f017 show almost no leg stride; add knee lift and a pelvis
  bob so the sneak reads (Stage 4). Clip warning (74 tris, front flap vs thighs) will shrink
  with item 5.
- Ear slivers (yellow on ear edges in 3_tech.jpg): one loop slide at the ear root (Stage 2).
