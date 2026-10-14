# Art-direction notes, repair round 2 (reconciled, K=2)

Scores (Fable 5.1 / Opus 5.5): 7 FIX / 6 FIX.

**Stage 1 is locked. No unlock is authorised for this pass.** Every fix below is a stage-2, stage-3 or stage-4 change. Stage-2 IoU against stage 1 must stay above 0.9 in every view (minimum is 0.961 now); stage 3 never edits the base; all gates pass.

Keep what works (round 1 fixed these; do not regress):
- Clip cut from 2.46% to 0.29% (r10-r14: elbows out in the wind-up, torso pitch from the chest, loin_front hanging steeper). Keep those keys.
- Brow overhang, thick short tusks rising from the jaw, dark mouth V (r15-r16).
- Moss as draped plates with bedded rocks over the hump (r20-r22), drift 0.
- Ankles narrower than knees (r12); unequal toes with the big toe inside.
- The hunched-troll silhouette: small sunk head, massive shoulders, arms to the knees, short legs (5_reference front match).

Fix the must-fix list in order, then the should-fix items if turns allow. Check every item in your own `--review` packet before you call it done.

## Must-fix, in order

0. **Kit gates.** No FAIL on the current kit. clip_area_pct 0.29 (moss 10 tris at the wind-up, belt 4), stretch 0. Under 1.0; item 4 must not raise it.

1. **Fists are dark boxes with a row of stone blocks stuck on the front (F major, O major; round 1 item 1 partly done).**
   - Where: 1_beauty az000 and hero: each fist is a near-black box with four pale stone cubes in a straight row across its middle; 2_closeups front limb colour: the cubes sit on the surface like dice. 5_reference front and side: blue-grey fists the same colour as the arm, four thick curled fingers across the bottom front with small stone nails at the tips.
   - Fix: Stage 3 (paint): paint the fists the skin colour (or one step darker than the forearm, not near-black), so the r17 finger grooves read. Stage 3 (pieces): replace the four stone knuckle caps with four finger pieces in skin colour: each a 2-segment curled box (width about 22% of the fist width, middle two widest, depth about 30% of the fist depth), rooted 30% into the fist's lower front below the knuckle ridge, curling back under the fist; a small stone nail (about 40% of finger width, flat) on the front tip of each. Keep the thumb block on the inside, skin coloured with a stone nail.
   - Check: 1_beauty az000: fists the arm's colour with four fingers and pale nails at the bottom like 5_reference front; hit/float 0; drift 0 (bind the fingers to the hand bone).

2. **Face is a dark recessed mask; the eyes are tiny chips in shadow (F major, O major).**
   - Where: 1_beauty az000 and hero: the face is a dark pentagon sunk in the head, the eyes are two small amber flecks; 2_closeups head colour: the brow overhang casts the eyes into shadow and the cheek and nose read as one dark plane. 5_reference front: a lit face with a broad nose, cheek planes, a heavy brow and bright amber eyes under it.
   - Fix: Stage 2 (vertex moves): pull the nose ridge and the two cheek-top verts forward by about 3% of head length and up 1%, and `flatten` a cheek plane each side, so the face catches light below the brow; keep the brow verts where r15 put them. Stage 3: eyes 1.4x wider again (about 0.11 x 0.06), front face 0.02 proud, a brighter amber (keep the palette slot, raise its value); paint the face front (nose, cheeks) the main skin colour, not `dark`.
   - Check: 1_beauty az000 at thumbnail size: two amber eyes and a nose read under the brow; 2_closeups head colour: brow, cheek and nose are three planes with different values; IoU > 0.9; eye float 0.

3. **Loincloth is a single flat paper triangle (F major, O major).**
   - Where: 1_beauty az000: one narrow tan triangle hanging from the belt; az090: the back flap is a thin strip edge-on; back34: a flat plate. 5_reference front and rear: a wide brown cloth front and back reaching the hips, with a jagged hem.
   - Fix: Stage 3: rebuild loin_front and loin_back as slabs with thickness about 5% of their width (closed shells), width about 70% of the hip width at the belt, length to mid-thigh, hem cut into 3-4 uneven points; a darker brown than the belt (use an existing palette colour). Keep the r14 hang angle for the front flap so it clears the belly; hang the back flap 10 deg off the buttocks. Bind both `body=` to the pelvis area.
   - Check: 1_beauty az090 and back34: both flaps have visible thickness and a jagged hem; az000: the cloth covers the hips like 5_reference front; clip stays under 1%; drift 0.

4. **Forearms pass through the head in the overhead slam (O major).**
   - Where: 4_posed attack_f010 and attack_f020: the near forearm and fist swing across the face, crossing the snout and brow.
   - Fix: Stage 4 (clip keys): in the wind-up and slam keys, add about 12 deg more upper-arm abduction (elbows wider) and lift the upper arms 10 deg more so the forearms pass above and outside the head, then come down in front of the chest; keep the r11 chest pitch. If the fists still meet the face, pull the head bone back 8 deg on those keys.
   - Check: 4_posed attack_f010 and attack_f020: a gap between the forearms and the head; fold-overs 0; clip not above 0.29%.

## Should-fix

- Moss is still separate patches from az000/hero (round 1 item 3 partly done): Stage 3, add two draped plates bridging the crest and shoulder plates on each side so the moss reads as one mantle as in 5_reference rear.
- Belly (round 1 item 4 partly done): Stage 3 paint a lighter belly plane on the R2 front faces so the pot belly reads in az000.

## Dropped

- None. Nothing needs stage 1.

## Appendix: both reviews verbatim

### Fable 5.1: FIX 7
- top_issues:
  - 2_closeups head colour: face is still a dark block with little plane separation; eyes are small chips deep in shadow.
  - 1_beauty az090: loincloth back flap is a paper-thin strip with no thickness.
  - 1_beauty az000: fists show a knuckle row of identical flat stone blocks; no separate fingers as the brief asks.

### Opus 5.5: FIX 6
- top_issues:
  - 4_posed attack_f010/attack_f020: the forearms pass through the head during the overhead slam
  - 1_beauty az000/hero: fists are dark boxes with a row of stone knuckle blocks stuck mid-front, not separate fingers
  - 1_beauty az000: loincloth is a single flat triangle plate; eyes are tiny amber dots barely readable

### Kit gates (this build, current kit)
- kit_gate_fails: none
- kit_warnings:
  - WARN s4 qa: 14 triangles (0.29% of surface) clip through the body in a pose that did not at rest (pink): a limb through a flap, a paw through the cheek
- clip_area_pct 0.29, stretch 0
