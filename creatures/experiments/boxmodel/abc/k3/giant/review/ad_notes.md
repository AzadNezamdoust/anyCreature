# Art-direction notes, NGO repair pass (reconciled, K=1)

Scores (Fable 5.1 / Opus 5.5): 6 FIX / 6 FIX.

**Stage 1 is locked. No unlock is authorised for this pass.** Every fix below is a stage-2, stage-3 or stage-4 change. Stage-2 IoU against stage 1 must stay above 0.9 in every view; stage 3 never edits the base; all gates pass.

Keep what works: the hunched mountain-troll silhouette with the small head sunk under massive shoulders, arms to the knees, the belt and loincloth, the moss-green and stone palette, and the cleanest tech sheet in the batch (0 flips, 0 drift, 0 hit at rest). Do not regress the shoulder-joint fix from s4 r01.

Fix the must-fix list in order, then the should-fix items if turns allow. Check every item in your own `--review` packet before you call it done.

## Must-fix, in order

0. **Posed clipping warning at 2.46% of surface (kit warning).**
   - `WARN s4 qa: 38 triangles (2.46% of surface) clip through the body in a pose that did not at rest (pink): a limb through a flap, a paw through the cheek`
   - No gate fails, but 2.46% is above the 1.0 threshold. Likely cause: the two-handed slam (4_posed attack_f010 wind-up, f020 follow-through), where the forearms and fists sweep through the chest plane and the front loincloth flap, and the walk (move_f009/f017) where the long arms swing through the loincloth side flaps.
   - Fix: Stage 4: rebuild the slam so the fists travel outside the torso: more clavicle and chest pitch, elbows out 15 deg, and stop the follow-through when the fists reach the belt line in front of the belly, not through it; in the walk, cut the arm swing until the fists clear the loincloth. Bind both loincloth pieces with `body=` weights so the flaps follow the thighs rather than staying rigid on the belt. Rerun and read the pink in 3_tech: any remaining pink on the belly is the fist path, any on the flaps is the bind.
   - Check: stage-4 run prints the clip warning under 1.0% or none; 4_posed attack_f020 shows the fists in front of the body, not inside it.

1. **Fists and toes are rows of identical stone blocks (F major, O major).**
   - Where: 1_beauty az000 and hero: each fist is a dark mitt with five equal rectangular nail slabs in a row like piano keys; each foot has four equal toe blocks. 2_closeups front limb: no knuckle row, no finger gaps. 5_reference: a knuckle row on top, fingers of unequal size curled under, a thumb.
   - Fix: Stage 2 (logged partial loops plus vertex moves): on each fist, add two partial loops across the front face of the mitt and pull their verts in by about 5% of the fist width to cut three finger grooves; add one loop around the top of the fist and push its verts out 4% to make the knuckle ridge. Stage 3: replace the five nail slabs with four nails of unequal width (middle two widest, +-20%), seated on the knuckle ridge, plus one thumb block on the inside of each fist rooted 30% into the mitt; on the feet, three toe blocks of unequal width instead of four equal ones, the big toe inside.
   - Check: 1_beauty az000: fists read as knuckles over fingers, no keyboard; nails hit/float 0; IoU > 0.9.

2. **The face is a small inset with two amber chips, overlong tusks and no brow or mouth (F major, O major).**
   - Where: 2_closeups head colour and wire: the face is a recessed panel; the eyes are tiny amber cubes; the tusks are thin cones that run up past the eyes; there is no mouth plane. 5_reference front: heavy brow overhanging the eyes, short thick tusks beside the nose, a wide mouth.
   - Fix: Stage 2 (vertex moves): pull the brow ridge verts above the eye sockets forward by 4% of head depth and down 2% so the brow overhangs the eyes; `flatten` the lower jaw front as one plane. Stage 3: rebuild the tusks at about 50% of their current height (the tip stops at the nose line, below the eyes), base 1.6x thicker, curving outward; rebuild each eye as an amber lens 1.4x wider than the current cube, no deeper than 1/3 of its width, set flush under the brow; paint a dark-hide mouth band along the top edge loop of the lower jaw (one face row wide) so the mouth reads at thumbnail size.
   - Check: 1_beauty az000 at thumbnail size: brow, two eyes, two short tusks and a mouth line read; 2_closeups head: no tusk reaches eye height; eye and tusk hit/float 0.

3. **Moss and rocks are flat chips glued on the hump (F major, O minor).**
   - Where: 1_beauty hero, az000, back34 and 2_closeups moss: the moss is bright flat slabs sitting on the surface with a visible edge all round; the rocks are small chips. 5_reference: a moss mantle draped over the whole hump and shoulders with rocks bedded into it.
   - Fix: Stage 3: rebuild the moss as three irregular mantle plates (7-9 sided outlines, no two alike) that follow the hump curvature, sunk 40% of their thickness into the surface with tapered edges, covering about 60% of the hump top from the crest to both shoulders; enlarge the rocks 2x and sink them 50% into the moss or hide so no base ring shows. Keep the s4 r01 rule: no rock across the clavicle/upper-arm weight seam.
   - Check: 1_beauty back34: the moss reads as one mantle, not chips; moss and rock float/z-fight/drift 0.

4. **Flat-fronted belly and constant-section legs (O minor).**
   - Where: 1_beauty az090 and 5_reference side: the reference has a pot belly in front of the belt; ours is a flat plane from chest to belt. The calves keep one width to the ankle.
   - Fix: Stage 2 (vertex moves): push the belly ring verts between the chest and the belt forward by about 5% of body depth and out 2% each side; scale the ankle rings to about 80% of the calf rings.
   - Check: 1_beauty az090: a belly curve in front of the belt; IoU > 0.9.

## Should-fix

- O/AD: the slam wind-up raises the fists only to chest height (NOTES s4 r02). Stage 4: try 10 deg more chest pitch before the upper arm; keep the fold gate at 0.

## Dropped

- None. The knuckle row and finger gaps, which usually need stage 1, are reachable here with logged loops and vertex moves on the mitt (item 1).

## Appendix: both reviews verbatim

### Fable 5.1: FIX 6
- top_issues:
  - Fists are dark mitts with five parallel nail slabs in a row (1_beauty az000), no knuckle row or separate fingers
  - Face is a small inset with two cube eyes and no brow or mouth plane (2_closeups head)
  - Moss and rocks are glued on the hump top as flat chips
- brief_fit / keep: Cleanest tech and a strong hunched profile, but the sunken head has no face and the fists are mitts

### Opus 5.5: FIX 6
- top_issues:
  - Fingers and toes are rows of identical rectangular stone blocks like piano keys (az000), and the dark mitt fists have no knuckle row
  - Tusks are overlong and run up past the eyes; the eyes are tiny amber chips under the brow
  - Pot belly is flat-fronted and the legs are constant-section; the tech sheet is clean, which my eye confirms
- brief_fit / keep: Best: a hunched mountain troll with a small head sunk low under massive shoulders, brow, jaw tusks, arms to the knees, irregular moss pads and bedded rocks, belt and loincloth.

### Kit gates (this build, current kit)
- kit_gate_fails: none
- kit_warnings:
  - WARN s4 qa: 38 triangles (2.46% of surface) clip through the body in a pose that did not at rest (pink): a limb through a flap, a paw through the cheek
- clip_triangles 38, clip_area_pct 2.46
