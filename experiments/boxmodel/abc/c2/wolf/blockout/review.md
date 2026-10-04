# wolf blockout review

Verdict: **FIX**

It is the wolf of the sheet: side silhouette (IoU 0.964) and all six proportion
ratios are inside the limits, head size and the ruff-to-tail exaggeration are
kept. What fails is primary construction below the body line and the hind
joint deformation; the cage reads as a traced outline with tube legs, not yet
a designed one.

```json
{"verdict": "FIX", "issues": [
 {"kind": "limbs", "title": "Hind leg has no thigh / stifle / hock construction"},
 {"kind": "limbs", "title": "Knee and hock loops collapse in fold and crouch"},
 {"kind": "limbs", "title": "Forelegs are untapered vertical tubes"},
 {"kind": "mass",  "title": "Ruff is two stacked collar shelves, not one mane wedge"},
 {"kind": "mass",  "title": "Top view: hips narrower than the sheet, skull/cheek block too wide"}
]}
```

## Fixes (max 5, in order of weight)

1. **Hind leg has no thigh / stifle / hock construction** (limbs)
   - Where: az090 side, back34.
   - What: the thigh is a flat flap fused into the flank and the lower leg drops as a vertical column; the sheet has a wide thigh mass, a forward knee and a hock set clearly back with a slanted metatarsus.
   - Direction / amount: widen the thigh in side view by about 5% of body length at its top and taper it to the knee; move the hock point back by about 3-4% of body length and up by about 3% of body height so tibia and metatarsus form a visible Z; in back34 push the thigh outward about 10% of body width so it separates from the belly.

2. **Knee and hock loops collapse in fold and crouch** (limbs, deformation)
   - Where: 5_rom fold hero, crouch hero / az090 (hind leg curls into a self-intersecting knot; 39 flipped triangles, 4.06% of area, all at the hind limb).
   - What: the two loops at knee and hock sit too close to each other and to the body junction, so 80-90 degrees of bend has no material on the outside of the joint.
   - Direction / amount: spread each pair to roughly 4-5% of body height apart, centred on the joint, add a third (holding) loop at the knee, and move the knee joint about 3% of body height down out of the flank so the bend happens in the limb, not in the belly skin. Target: flipped area below 1%.

3. **Forelegs are untapered vertical tubes** (limbs)
   - Where: az090 side, az000 front, hero.
   - What: constant section from chest to paw, no elbow, no wrist break; in the front view the two legs are parallel posts. Sheet and concept show a broad upper arm tapering to a thin wrist, then a paw.
   - Direction / amount: thicken the upper arm in side view by about 25% of its current depth at the elbow and narrow the wrist by about 20%; put the elbow point back by about 2% of body length; in front view set the paws about 10% of body width further apart than the elbows so the stance has a slight A-frame instead of posts.

4. **Ruff is two stacked collar shelves, not one mane wedge** (mass, big planes)
   - Where: az090 side, back34, hero.
   - What: two hard horizontal steps wrap the neck like armour plates; the concept is one big mass that is widest behind the jaw and falls as a bib to the elbow line.
   - Direction / amount: merge the two bands into one wedge with a single back edge; drop the chest bib point about 4% of body height lower and forward about 2% of body length; keep one step at the withers only (about 2% of body height), remove the second.

5. **Top view: hips narrower than the sheet, skull/cheek block too wide** (mass separation)
   - Where: 2_silhouette top (blue at hips, red along head and neck), az000 front (red at cheeks, blue at ear tips).
   - What: head-neck-ruff run together as one wide block and the pelvis does not read as a second mass, so the body has no chest / waist / hip rhythm from above.
   - Direction / amount: narrow the skull and cheek by about 10% of body width per side, keeping the ruff as the widest point; widen the hips about 8% of body width per side; raise the ear tips about 3% of body height and tilt them out slightly to recover the front outline.

Stage 1 reopens; stage 2 does not start until these are in and the ROM flip area is re-measured.
