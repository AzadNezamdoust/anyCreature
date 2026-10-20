# Art-direction notes, repair round 2 (reconciled, K=2)

Scores (Fable 5.1 / Opus 5.5): 7 FIX / 6 FIX.

**Stage 1 is locked. No unlock is authorised for this pass.** Every fix below is a stage-2, stage-3 or stage-4 change. Stage-2 IoU against stage 1 must stay above 0.9 in every view (minimum is 0.976 now); stage 3 never edits the base; all gates pass.

Keep what works (round 1 fixed these; do not regress):
- Drift 0 with a working blink: lid lens inside each eye, scale on the eye bones (r10-r13). Do not seat new face pieces in a way that breaks it.
- Round domed orange eyes with a smooth pupil (r11).
- Brows lie on the head, clip 0 (r14); talons come out of the toe front, no slits (r15).
- 6 colours, brown sides of the head, cream legs (r16, r20); tail wedge and slivers 0 (r17-r18).
- Upright egg body with two ear tufts: reads as an owl in every view.

Fix the must-fix list in order, then the should-fix items if turns allow. Check every item in your own `--review` packet before you call it done.

## Must-fix, in order

0. **Kit gates.** No FAIL on the current kit; clip_area_pct 0.0, stretch 0. Nothing to do; keep it that way.

1. **Facial disc is a square cream mask with square eye boxes; the beak barely projects (O major, F major).**
   - Where: 1_beauty az000 and hero: a flat cream rectangle across the face, each eye in a square cream box, a brown band under it; 2_closeups head colour: the face is one flat panel and the tan beak is a small wedge flush with it. 5_reference front and side: two round pale discs that meet at the beak, each with a dark rim, and a dark hooked beak that sticks out and curves down.
   - Fix: Stage 3: add a facial-disc piece per side: a shallow 12-sided cream dish centred on the eye, outer radius about 1.6x the eye radius, with a dark-brown outer ring (about 12% of the radius) as the rim, the two discs meeting at the beak line; seat it 2 mm proud of the face, its back sunk into the skin, with a hole the eye fits through (the eye and lid stay as they are). Bind it `body=` with the face skin weights so the head turn carries it (drift). Paint the square socket corners outside the disc brown. Rebuild the beak 1.4x longer, projecting forward about 60% of its length out of the disc, tip hooked down 30 deg; colour it dark (the talon colour) as in 5_reference.
   - Check: 1_beauty az000: two round pale discs with dark rims and a dark hooked beak; az090: the beak sticks out of the profile; drift 0, z-fight 0, float 0; 4_posed idle_f024 blink still closes over the eyes.

2. **Attack is a lean with folded wings (O major).**
   - Where: 4_posed attack_f008 and attack_f016: the wings stay folded on the sides; the body tips forward; nothing reads as a strike.
   - Fix: Stage 4 (clip keys): at the strike key (about 40-60% of the clip) raise and open both wings: rotate the wing bones up and out about 60 deg (if the folded wings are not on their own bones, add wing.L/R bones on the wing faces and weight them with `bind(body=)`), and swing both legs forward about 35 deg with the talons spread; ease back to the fold by the last frame (first = last). If fold-overs pass 0.5% at 60 deg, use 45 deg.
   - Check: 4_posed attack frames: open wings on both sides and talons forward in one frame; fold-overs <= 0.5% (tris and area); drift 0.

3. **Talons are thin black needles on a flat cream foot plate (F major).**
   - Where: 2_closeups hind limb colour: thin black spikes sticking out of a broad flat cream foot; 1_beauty az090: needles. 5_reference front and side: thick curved black talons on separate feathered toes.
   - Fix: Stage 3: rebuild each talon with a base 2x as thick (about 1/4 of the toe width), length the same, tip curved down 40 deg so it hooks toward the ground; keep the r15 root (inside the toe front). Stage 2: pull the verts between the toes back about 20% of the foot length so the foot reads as three toes, not one plate.
   - Check: 2_closeups hind limb colour: thick hooked talons on separate toes; hit/float 0; IoU > 0.9.

4. **Tail and wings are single flat slabs with no feather groups (O major, F minor).**
   - Where: 1_beauty az090 and back34: the tail is one dark slab with a square end; the wing is one brown plane; 2_closeups front limb: the wing tip is a thin plate edge-on. 5_reference side and rear: the folded wing shows rows of covert and primary feathers; the tail has a fanned, notched tip.
   - Fix: Stage 2 (vertex moves): move the tail tip's middle vert back about 15% of the tail length so the end is a shallow notched V; push the wing tip's underside verts down about 30% of the tip depth so it has thickness. Stage 3 (paint): paint the folded wing in two values: a lighter covert band on the top third, the darker brown for the primaries below, borders on existing edges; paint the tail's top faces in alternating dark/brown bands along its length (2-3 bands).
   - Check: 1_beauty az090 and back34: wing and tail read as feather groups; the tail end is notched; colour count stays at 6-7; slivers 0.

5. **Brows are straight planks sitting slightly off the head (F minor).**
   - Where: 2_closeups head wire and lid wire: each brow is a straight bar lying over the curve with a small gap at the outer end. 5_reference front: dark V brows that sweep up into the ear tufts.
   - Fix: Stage 3: after item 1, re-raycast the brow stations onto the new disc rim (5 stations, half sunk, as r14) and extend the outer end up and back toward the ear tuft base by about 30% of its length, so the brow joins the tuft.
   - Check: 2_closeups head wire: no gap under the brow; 1_beauty az000: a V that runs into the tufts; clip 0.

## Should-fix

- Belly border: paint the top edge of the cream belly as a row of V chevrons on existing edges (5_reference front), instead of a straight line.

## Dropped

- None. Nothing needs stage 1.

## Appendix: both reviews verbatim

### Fable 5.1: FIX 7
- top_issues:
  - 2_closeups head wire: brow bars still sit slightly off the head as separate pieces.
  - 2_closeups hind limb colour: talons are thin black spikes on a flat cream foot plate; the wing tip is a paper-thin plate edge-on.
  - 1_beauty hero: the face is a flat panel; the beak is a small wedge that barely projects from the disc.

### Opus 5.5: FIX 6
- top_issues:
  - 4_posed attack_f008/attack_f016: wings stay folded; the attack reads as a lean, not a talon strike
  - 1_beauty az000: facial disc and eye sockets are square boxes, not a round disc with a rim
  - 1_beauty az090/back34: tail is a single flat slab; the body has no feather-group planes

### Kit gates (this build, current kit)
- kit_gate_fails: none
- kit_warnings: none
- clip_area_pct 0.0, stretch 0
