# Art-direction notes, NGO repair pass (reconciled, K=1)

Scores (Fable 5.1 / Opus 5.5): 7 FIX / 7 FIX.

**Stage 1 is locked. No unlock is authorised for this pass.** Every fix below is a stage-2, stage-3 or stage-4 change. Stage-2 IoU against stage 1 must stay above 0.9 in every view; stage 3 never edits the base; all gates pass.

Keep what works: the egg body with a rounded head, solid cone tufts, folded wings, fan tail, big orange eyes, cream disc and belly, feathered legs with dark talons, and the wing-spread strike. Both reviewers say every brief cue is present; do not regress it.

Fix the must-fix list in order, then the should-fix items if turns allow. Check every item in your own `--review` packet before you call it done.

## Must-fix, in order

0. **Kit gate FAIL and the clipping warning (current kit, every keyed frame sampled).**
   - `FAIL s4 qa: no piece comes off the body in a pose (drift) — 1 shells — bind them with body= weights (or the bone under them)`
   - `WARN s4 qa: 13 triangles (1.00% of surface) clip through the body in a pose that did not at rest (pink): a limb through a flap, a paw through the cheek`
   - Likely cause of the drift: one eye disc on a blink frame (idle, eye bones added after skinning; NOTES s4 r03 already saw "the eye drifted (1 shell)" once). The old 20/40/60/80% samples skipped the blink; now every keyed frame is checked. Likely cause of the pink: the strike (attack_f016, thighs 55 deg forward, feet -30) pushing the talons or feet through the belly, or the flap (move_f006) pushing the wing root through the flank.
   - Fix: Stage 4. Keep the blink inside the socket: drive it as a z-only scale of the eye bone to no less than 0.35 with the disc centre fixed (no translation into the head), and bind the pupils with the same bone so they stay on the disc; if the eye still drifts, bind eye and pupil with `body=` weights and blink with a brow drop instead (brow pieces rotated down 25 deg over the eye on the blink frames). For the pink: cut the strike's thigh angle until the feet stay in front of the belly, and cut the flap's wing-root rotation 20%; rerun and read where the pink sits in 3_tech.
   - Check: stage-4 run: drift 0, no clip warning at or above 1.0%; 4_posed idle blink frame shows both eyes on the face.

1. **Brows are rectangular sticks jutting past the head and floating over it (F major, O major).**
   - Where: 1_beauty hero and az000: both brow bars stick out past the head silhouette at their outer ends; 2_closeups head wire (top-left): the near brow stands off the head with a visible gap. 5_reference: the brows are a V of dark feathers lying on the top edge of the disc.
   - Fix: Stage 3: rebuild piece_brow.L/R as flat wedge plates (thick at the inner end, tapering to the outer end) that lie on the disc's upper rim, sunk 50% of their thickness into the head, angled 15 deg down toward the centre for the V, and with the outer end stopping at least 5% of head width inside the head silhouette in az000. Keep `dark brown`. Alternative that also works: delete the pieces and paint the top edge row of the disc `dark brown` as a V.
   - Check: 1_beauty az000: no brow past the head outline; 2_closeups head wire: no gap under either brow; brow float 0.

2. **Talons poke through the top of the foot as dark slits (F major).**
   - Where: 2_closeups hind limb colour and wire: black triangles show through the top face of the foot where the talon roots sit above the foot surface.
   - Fix: Stage 3: lower every talon root so its top sits below the foot's upper face (root centre at 40% of foot height), rooted 30% of the talon length into the toe, tip forward and down; keep the back talon rooted inside the heel. Keep the `body=` bind from s4 r04.
   - Check: 2_closeups hind limb colour: no black on the foot top; talon hit 0 (they must not pass through twice), drift 0.

3. **Facial disc is a square mask with no rim, and the tan bib is an off-palette colour (O major).**
   - Where: 1_beauty az000 and 2_closeups head: the cream disc has square corners and no dark rim; a tan band sits between the disc and the cream belly. 5_reference front: a round disc with a thin dark rim, brown chest feathers above the cream belly. The brief lists 6 colours; the packet uses 7 (NOTES: tan bib + legs).
   - Fix: Stage 3 (paint only): paint the outer face row of the disc `dark brown` as a rim, and paint the disc's corner faces brown so the cream reads round; repaint the bib the `brown feathers` colour with the border on the chest loop, and the legs `cream`; keep tan (`beak and talon`) only on the beak. Colour count 6.
   - Check: 1_beauty az000: a round cream disc with a dark rim; 6 colours in the stage-3 gate.

4. **Tail is a thin plate with a sliver seam on its underside (F minor, O minor).**
   - Where: 3_tech az090: a yellow sliver along the tail underside; 1_beauty az090 and back34: the tail reads as a flat plate edge-on.
   - Fix: Stage 2 (vertex moves): move the tail's underside verts down by about 3% of body height at the root tapering to 1.5% at the tip so the tail has a wedge section, and slide the sliver's apex vert along the tail edge to the midpoint of the long edge so the thin triangle is split evenly.
   - Check: 3_tech az090: no yellow on the tail; 1_beauty az090: the tail shows a visible thickness; IoU > 0.9.

5. **Eye rings are flat octagons with a stepped inset (O minor).**
   - Where: 2_closeups eye colour and wire: the orange ring is a flat octagon with a visible step down to the pupil.
   - Fix: Stage 3: rebuild each eye as a 12-sided shallow dome (centre raised about 15% of its diameter), with the pupil a smaller dome seated on the front, no step; keep the disc seated in the socket, float 0.
   - Check: 2_closeups eye: a round orange eye with a smooth pupil; eye float/z-fight 0.

## Should-fix

- F: the eyes look unequal in hero. That is the idle head turn plus perspective; confirm both eye pieces are mirrored at the same z and radius, and leave them if they are.

## Dropped

- None. Every item is reachable in stages 2-4.

## Appendix: both reviews verbatim

### Fable 5.1: FIX 7
- top_issues:
  - brow slabs float above the head surface with a visible gap (head wire, top-left)
  - black talon pieces poke through the top of the foot as dark slits (hind-limb close-up), reading as holes
  - tail underside has a sliver seam (yellow, az090) and the eyes sit slightly unequal in the hero view
- brief_fit / keep: All cues present: egg body, solid cone tufts, folded wings, fan tail, feathered legs with dark talons, cream disc and belly, orange eyes.

### Opus 5.5: FIX 7
- top_issues:
  - The brows are rectangular sticks that jut past the head silhouette in hero and the head close-up, reading as glued-on planks
  - The facial disc is a square mask with no dark rim; the tan chest band adds an off-palette colour
  - The eye rings are flat octagons with a visible stepped inset in the wire, and the tail fan is a thin plate (sliver on the tail underside in az090)
- brief_fit / keep: Good match: egg body, folded wings with a fan tail, big orange eyes, tufts, feathered brown thighs and dark talons.

### Kit gates (this build, current kit)
- kit_gate_fails:
  - FAIL s4 qa: no piece comes off the body in a pose (drift) — 1 shells — bind them with body= weights (or the bone under them)
- kit_warnings:
  - WARN s4 qa: 13 triangles (1.00% of surface) clip through the body in a pose that did not at rest (pink): a limb through a flap, a paw through the cheek
- clip_triangles 13, clip_area_pct 1.0
