# Art-direction notes, round 2 (reconciled, K=2 pass)

Round-2 scores (Fable 5.1 / Opus 5.5): 7 FIX / 6 FIX. Fix the must-fix list in order, then the should-fix items if turns allow. Keep everything in both keep lists (appendix) and in round 1 (`ad_notes.md`). Stage 1 stays locked; the stage-2 IoU floor stays > 0.9.

## Must-fix, in order

1. **Buckle shard (F1 blocker, O1 blocker).**
   - Fix: Stage 3: rebuild the buckle as a chunky bevelled block, at least half as deep as it is wide, seated half into the belt.
   - Check: az090/hero: no white blade; no slivers on the buckle.
2. **Belt drift, unbound claw (O2 major, F4 minor; now gated).**
   - Fix: Stage 4: bind the belt with body=, and bind the loose claw to its finger bone with bone=.
   - Check: techqa drift 0.
3. **Pot belly (F2 major, O4 major).**
   - Fix: Stage 2: push the belly front forward into a rounded pot belly that clearly passes the belt in az090, and round the underside. Stage 3: repaint the belly border as a curved U along a loop, with no straight top.
   - Check: az090: a convex belly; no tube-top border; IoU > 0.9.
4. **Asymmetric shoulder fold-over (F3 minor, O6 minor).**
   - Fix: Stage 4: make the left shoulder weights match the right (mirror them).
   - Check: heatmap: no purple at either shoulder.

## Should-fix (a minor from one reviewer)

- O5: curve and seat the loincloth flaps, and remove the slivers on their side edges.
- O8: vary the nose section: a wider bridge and a narrower tip.

## Dropped (the other reviewer's keep list contradicts it)

- O3 (flat skull lid): contradicted by the Fable keep list ("domed green skull").
- O7 (grin reads as a strap): contradicted by the Fable keep list ("fanged grin").

## Appendix: both reviews verbatim

### Fable 5.1: FIX 7
- **F1** [blocker/technical] where: 1_beauty hero and az090, belt front; 2_closeups front limb colour and belt colour, belt front; 3_tech az090 yellow line at the belt front; techqa piece_buckle sliver 2
  - what: The buckle is a thin cream plate projecting roughly 3-4 cm forward from the belt: edge-on it reads as a white shard sticking out of the waist in every side and 3/4 view.
  - fix: Stage 3: rebuild piece_buckle as a box 1.5x the belt height and >= half the belt thickness deep, sunk half its depth into the belt front; nothing projects past the belt by more than its own thickness.
  - check: hero and az090 show a cream block on the belt, no fin; buckle sliver 0; az000 still shows the buckle.
- **F2** [major/form] where: 1_beauty az090 torso profile; hero and az000 belly paint
  - what: The pot belly is weak in the base: the torso front is a near-straight wall that barely passes the belt, and the pale belly paint is still a straight-topped rectangle (tube top). Round-1 item 6 half done.
  - fix: Stage 2: push the belly loops at belt level forward 10-15% of torso depth so the belly overhangs the belt by ~1/3 belt height, and round the top. Stage 3: paint the pale colour on the lower belly only with its top border curved on a loop.
  - check: az090: belly point protrudes past the belt front; az000: pale patch has a curved top border, no straight edge; IoU > 0.9.
- **F3** [minor/technical] where: 3_tech hero and az000: purple at the left shoulder/neck; techqa body flip 7
  - what: Fold-over remains at the left shoulder only (0.34%, gate met); the right shoulder is clean, so the weights are asymmetric.
  - fix: Stage 4: mirror the right shoulder's chest/upper-arm blend onto the left seam loop.
  - check: No purple in 3_tech; flip 0.
- **F4** [minor/animation] where: 3_tech all views: belt blue; hero and az000: one claw on the left hand blue; techqa drift belt 1, claws 1
  - what: The belt lifts off the waist in a pose and one left-hand claw leaves its finger.
  - fix: Stage 4: bind piece_belt with bone=pelvis (same as the loincloth) and each claw with its finger/hand bone.
  - check: drift 0; no blue in 3_tech.
- keep: face at thumbnail: brow, hook nose in profile, fanged grin, glint eyes | big head, long ears, crouch, arms to the knees; domed green skull | three-digit clawed hands and feet; belt and loincloth solid (open 0, hit 0, zfight 0)

### Opus 5.5: FIX 6
- **O1** [blocker/technical] where: 1_beauty az090 (belt front) and hero (belt front, left of the flap); 2_closeups front limb and belt colour (top-left corner of the flap)
  - what: The cream buckle stands off the belt as a thin plate. Edge-on it reads as a white blade about 2–3 cm proud of the belt in az090 and as a white shard in hero and both close-ups. techqa counts it only as 2 slivers; the eye is right.
  - fix: Stage 3: rebuild piece_buckle as a box at least 1 cm deep (≥ 1/3 of its height), aligned to the normal of the belt's front face and sunk 2 mm into the belt.
  - check: az090 shows no white spike beyond the belt's front edge; buckle sliver 0
- **O2** [major/technical] where: 3_tech all views: the whole belt is blue, plus one claw on the viewer's-left hand (hero, az000); techqa drift belt 1, claws 1
  - what: The belt sits on the belly at rest but leaves it in poses, because it is bound rigidly to the pelvis while the belly follows the spine. One claw is not bound to its finger.
  - fix: Stage 4: rebind piece_belt and piece_buckle with bind(body=) to the waist loop under them, and keep the flaps on bone=pelvis. Rebind the drifting claw with bone= set to its finger or hand bone.
  - check: no blue in 3_tech; techqa has no drift key on belt or claws; the belt stays on the belly in attack_f008
- **O3** [major/form] where: 1_beauty back34, az090 and hero crown; every 4_posed frame (flat cap ring)
  - what: The skull top is still a flat lid. The paint was fixed but there is no dome, so the head reads as a tin can in back34.
  - fix: Stage 2: raise the top-centre verts +12% of head height along the midline, and pull the top rim ring in ~8% with a logged chamfer, so the crown becomes a dome of 3–4 planes.
  - check: back34 and az090 show a curved crown with no flat cap; IoU > 0.9
- **O4** [major/form] where: 1_beauty hero and az000 torso; az090 belly front
  - what: The belly is still a lighter rectangular panel with a straight horizontal top border, so it reads as a tube top. In profile its front is a flat vertical plane, not a pot belly.
  - fix: Stage 2: push the belly-centre verts below the navel loop forward ~10% of torso depth and down 3%, so the bulge overhangs the belt. Stage 3: paint the light green on the lower belly only, with the border on the curved loop above the navel.
  - check: az090 shows a convex belly outline over the belt; hero and az000 show no straight horizontal colour border across the torso
- **O5** [minor/pieces] where: 1_beauty az090 flaps; 3_tech az090 (yellow flap edges)
  - what: The flaps are now closed solids, but they hang as rigid planks. The front flap juts off the thigh line, and both flaps have sliver side edges.
  - fix: Stage 3: bend the front flap 10–15° to follow the thighs and the back flap to follow the buttocks, and chamfer or merge the side-edge strips.
  - check: in az090 the flaps follow the body; loincloth sliver 0
- **O6** [minor/technical] where: 3_tech hero and az000, top of the shoulder on the viewer's left (purple)
  - what: A small posed fold-over wedge remains on one shoulder (flip 7 = 0.34%, under the limit).
  - fix: Stage 4: blend the shoulder seam loop 50/50 between chest and upper arm, and add clavicle weight to the shoulder-top verts.
  - check: no purple in 3_tech; body flip 0
- **O7** [minor/face] where: 1_beauty az000 mouth; az090 and 2_closeups head colour
  - what: The grin is still a straight band, and in profile it runs back to the jaw corner like a strap.
  - fix: Stage 2: raise the mouth-corner verts by 1/3 of the band height and pull each end 10% forward so the mouth stops at the cheek.
  - check: in az000 the mouth curves up at both ends; in az090 the band ends ahead of the ear
- **O8** [minor/form] where: 1_beauty az090 nose
  - what: The nose now hooks down, but it keeps one section along its length, like a bent pipe.
  - fix: Stage 2: narrow the bridge verts ~20% at the root and swell the tip loop ~10%.
  - check: in az090 the nose widens from bridge to tip
- keep: the face reads at thumbnail size: heavy brow, yellow glint eyes, hooked nose, fanged mouth with larger outer fangs | proportions: big head, long horizontal ears, crouch, big clawed hands and three-toed feet | palette: green skin, dark-brown belt, brown tattered loincloth, cream fangs

