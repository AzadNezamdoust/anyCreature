# HS look method — build what makes sense, not line-to-line (owner decision 2026-10-04)

The concept and the four turnaround views are AI-generated drawings. They are not projections of one 3D object:
measured on the 10 Generals units they disagree with each other by 0.1–0.45 m, 5–12 % in size, 9–33° in a turret's
yaw. No solid matches all their lines, and a gate that forces it moves parts away from where most views put them.
A 10-unit A/B (strict line matching vs this method, research/WF-V9-HS.md) ended with the owner preferring this one.

Goal: the model a viewer would say IS this unit — the same design, built as one coherent, believable machine.

## Steps (build and polish alike)
1. **Major masses first.** Before any detail, check each big form against the source in every view at full size:
   hull / fuselage section, nose, cab, turret, wheel size against the body, track height against the hull. A nose
   that is a box where the source is a faceted octagon, a windshield that is a slit where the source wraps round, a
   hull slab where the source shows tall tracks — these outweigh every small part. Fix the mass, then detail it.
2. **Feature inventory** → `FEATURES.md`: for every part — present?, count (slats, bolts, wheels, tubes, hatches),
   shape language (boxy / wedge / round, chamfers), size as a ratio of the hull, place relative to its neighbours,
   angle class, colour. Use `scripts/hs/closeups.py` as a magnifier for READING the source, not as a ruler.
3. **Resolve disagreements by sense.** When views disagree, choose what most views show and what a real machine of
   this kind would have (symmetric where it should be, wheels equal and evenly spaced, round things round, the gun
   on the turret centre line, glazing a crew could see through, parts that clear each other). Record each decision
   in `FEATURES.md` ("views disagree on X: chose Y because Z"). Decided facts (`facts.json`, `views.json`) still hold.
4. **Build to the inventory.** Every feature present with the right count, shape language, relative size (within
   about 5 % of the source ratio) and relative place. Do not chase a line that is a few pixels off; do fix a part
   that is the wrong size, the wrong shape, in the wrong place relative to its neighbours, or missing.
5. **Whole-form check each round**: the concept render next to the concept and the four views next to the drawings,
   at full size — stance, mass distribution, proportions — before returning to parts.

## Gates
- Silhouette agree is a sanity check, not the target: no ortho view more than **.04 below** the gold model's. The
  concept view is a look reference, **not gated** (the concept contradicts the turnaround on most units).
- Direct subjects (no gold model): the reference is the BEST earlier pass per view that is not a block-out (run_pass.py
  `--gate-ref mature`, default since 2026-10-10: the folder's first pass and passes under 5 % of the tri budget are never
  a reference; `--gate-ref all` = the old every-earlier-pass rule, which let a solid block-out lock a view against the
  correct hollow part). A mature pass that fills a hollow / see-through feature still sets a reference the correct model
  cannot beat: build hollow features hollow from pass 2; the builder never switches the rule
  (out/blender-hs/BUILD-DIRECT.md "best earlier pass"). Check `SIGMA` after pass 1: outside 0.98 .. 1.03 the registered
  sizes are wrong (< 1 = too big); fix scale before detail.
- Never tune geometry to the judge's raster (a rotor height, a blade angle chosen because the 512 px score jumps).
- Tris ≤ budget, topology 0, riggable rules (out/blender-hs/BRIEF.md "Function stage").

## Render aids
- Shallow facets (creases under 46°) get no ink line and little tone step. Where the source draws a facet line
  there, mark the edge with `hs.mark_edges(ob, edges)` (the harness inks marked edges; Blender 5.1 has no
  `edge.use_freestyle_mark`, the mark is the `freestyle_edge` edge attribute), or make the facet steeper if the form
  allows.
- Stray ink lines mean intersecting or coplanar parts: fix the geometry, do not leave them.

## Lessons from the A/B (2026-10-04)
- Both methods found the same real defects (hidden rear grilles, bores showing the box face, ladder-rung tyres):
  the close-ups find them, the gate does not.
- Polish rounds: every decision (done / partial / conflict, with the measurement) goes into `POLISH.md`; at the end of
  the round update `FEATURES.md` to the build as it now is, or mark the changed lines `STALE (see POLISH.md)`.
  A FEATURES.md that describes the pre-polish build misleads the next reviewer and the rig stage.
- One polish round of either kind does not change base proportions. If the major masses are off (step 1), rebuild
  them; do not polish around them.
- Blind AI judges of X / Y sheets favoured the bottom row (10 / 10 and 8 / 10): judge twice with the order swapped
  and count only picks that hold in both orders. The owner's read of the labelled sheets decides.
