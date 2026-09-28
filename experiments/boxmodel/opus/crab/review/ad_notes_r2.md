# Art-direction notes, round 2 (reconciled, K=2 pass)

Round-2 scores (Fable 5.1 / Opus 5.5): 7 FIX / 5 FIX. Fix the must-fix list in order, then the should-fix items if turns allow. Keep everything in both keep lists (appendix) and in round 1 (`ad_notes.md`). Stage 1 stays locked; the stage-2 IoU floor stays > 0.9.

## Must-fix, in order

1. **Crown pie lid (F1 major, O2 major).**
   - Fix: Stage 2, because the topology is locked and a major does not unlock stage 1: flatten() the crown into 5-7 large planes by sector (a front plateau, two front sides, two back sides, the back, the centre), so the colour shows carapace planes, not spokes or ring bands. Slide the vertices of the side-wall pleats so its triangles are wider. The valence check from round 1 is waived.
   - Check: hero/top colour: a few big planes, no spoke or ring shading.
2. **Spidery legs (O1 major, F2 minor).**
   - Fix: Stage 2: shorten the below-knee segments about 15% and angle the dactyls out and down with a second bend; vary the lengths front to back. If the IoU gate blocks it, stage 4: lower the stance in every clip with more knee bend, the body about 10% lower.
   - Check: az090: splayed legs, not stakes; the body closer to the ground.
3. **Barnacles (F4 minor, O4 minor).**
   - Fix: Stage 3: 3-5 low cones with a dark hole on top and a darker tint, bases sunk, clustered at the rear edge and none on the top centre.
   - Check: no pale nuts; the top reads clean.

## Should-fix (a minor from one reviewer)

- F3: key an alternating gait with a visible leg lift of about 3-4 cm and a body sway.

## Dropped (the other reviewer's keep list contradicts it)

- O3 (toothed front edge missing): contradicted by the Fable keep list ("toothed front edge").

## Appendix: both reviews verbatim

### Fable 5.1: FIX 7
- **F1** [major/form] where: 2_closeups barnacles wire (apex) and front limb wire (carapace top); faint converging facet lines near the apex in the barnacles colour close-up
  - what: The carapace crown is unchanged from round 1: one pole vertex with ~30 radial spokes and two concentric rings (pie lid). The round-1 check (no vertex with > 8 edges on top) fails.
  - fix: Stage 2: log two insets at the apex to replace the fan with a central plate and one ring, then flatten into 5-6 big planes with a soft mid ridge.
  - check: No vertex on the top with more than 8 edges; barnacles wire shows a plate plus one ring.
- **F2** [minor/form] where: 1_beauty hero and az090, all walking legs below the knee
  - what: Knees and paddled merus are in, but the segments below the knee are still long straight tapered cones; the stance is tall and spidery in hero.
  - fix: Stage 2: shorten the lower segments 15-20% and add a slight bend at 60% of their length (propodus/dactyl); unlock stage 1 only if IoU breaks, and log it.
  - check: az090: leg tips fall within 1.6× the carapace width; a second bend visible below the knee.
- **F3** [minor/animation] where: 4_posed move_f006/f007/f012/f013
  - what: The four move frames read as idle at this size: no visible leg lift or body shift, so the alternating gait cannot be confirmed.
  - fix: Stage 4: key the tetrapod gait with tips lifted 15% of leg length and a body sway; keep planted tips fixed in world space.
  - check: Tip heights differ ≥ 10% of leg length between f006 and f012; planted tips do not move between consecutive frames.
- **F4** [minor/pieces] where: 2_closeups barnacles colour; 1_beauty back34
  - what: Barnacles are high-contrast pale grey polyhedra sitting on the surface with visible base edges.
  - fix: Stage 3: sink them a further 20% and tint them 15% toward the shell colour.
  - check: No visible base edge in the barnacles close-up.
- keep: wide low shell with the toothed front edge and the claws held in front: reads as a crab in all four views | chunky claws with the open finger gap that snap in the attack | clean tech (hit/float/zfight/flip 0): keep it clean

### Opus 5.5: FIX 5
- **O1** [major/form] where: 1_beauty hero, right side, and az090; 3_tech az090
  - what: The walking legs are still long, straight, identical tapered spikes below a small knee. In az090 they stand as a row of vertical stakes that hold the body about a third of its height off the ground. The silhouette reads as a spider or harvestman, not a crab.
  - fix: Stage 2: shorten each lower segment 20–25%. Add a second bend at ~70% of the leg so the tip angles back in under the body. Vary the splay: front pair 20° forward, rear pair 25° back, the middle two ≥ 10° apart. If IoU breaks, unlock stage 1 to drop the body until the underside clears the ground by ≤ 10% of height, and log it.
  - check: az090: every leg shows an angle and none is a stake; hero: the four right legs are not parallel; az000: the body sits low between the knees.
- **O2** [major/form] where: 2_closeups front-limb wire and barnacles wire, carapace top; the crown in every 4_posed frame; 1_beauty back34
  - what: The carapace crown is still a radial fan of about 30 spokes on one pole, now circled by concentric rings. In colour it reads as a pot lid with ring bands, and the side wall is a pleated skirt of long thin triangles.
  - fix: Stage 2: log two insets at the crown (a central plate and a ring) and dissolve the spokes so no top vertex has more than 8 edges. Flatten the ring into 5–6 big planes with a soft mid ridge. Merge the side-wall pleats into 6–8 wide planes.
  - check: wire: no top vertex with more than 8 edges and no concentric bands; back34 and hero show a few big shell planes; IoU > 0.9.
- **O3** [major/silhouette] where: 1_beauty hero and back34; 2_closeups front-limb colour, carapace rim
  - what: The toothed front edge is still missing: the rim outline is smooth in every view. The dark pleat triangles on the side wall are shading only and do not break the outline.
  - fix: Stage 2: log a rim loop across the front third, then move alternate rim verts outward 4–6% of carapace width to cut 4–5 teeth per side, running from behind the eye stalks to the widest point.
  - check: hero: 4–5 notches per side in the front rim outline; az000: teeth visible between the claws and the eye stalks; hit 0.
- **O4** [minor/pieces] where: 1_beauty back34; 2_closeups barnacles colour
  - what: The barnacles are hexagonal prisms that read as nuts or bolts, and some are still spread over the top.
  - fix: Stage 3: rebuild them as 3–4 truncated cones with a dark inset top, in mixed sizes (1–1.8×), clustered on the rear rim and sunk 30%.
  - check: back34: one cluster on the rear edge that reads as barnacles; float 0.
- keep: chunky claws with a real gap between the fingers, which snap in the attack | az000: the wide low shell with the claws in front reads as a crab; eye stalks with bulb eyes | clean tech (hit, float, zfight and flip all 0)

