# Art-direction notes, repair round 2 (reconciled, K=2)

Scores (Fable 5.1 / Opus 5.5): 7 FIX / 6 FIX.

**Stage 1 is locked. No unlock is authorised for this pass.** Every fix below is a stage-2, stage-3 or stage-4 change. Stage-2 IoU against stage 1 must stay above 0.9 in every view (minimum is 0.958 now); stage 3 never edits the base; all gates pass.

Keep what works (round 1 fixed these; do not regress):
- Mane is thick shingle plates, not 36 needle blades; clip from 1.17% to 0.10%, drift 0 (r09-r10).
- No throat fold-overs: head graze -18/-14, charge -22/-25 (r11). Keep those keys.
- Tine points are one taper with the tine, no ledge, z-fight 0 (r12-r14).
- Ears turned back beside the antler base, behind the eye (r16); eye readable at thumbnail size (r17).
- Cream rump patch with its border on the R1 loop (r21); slender legs, deep chest, tall antlers (5_reference side match).

Fix the must-fix list in order, then the should-fix items if turns allow. Check every item in your own `--review` packet before you call it done.

## Must-fix, in order

0. **Kit gates.** No FAIL on the current kit. clip_area_pct 0.10 (3 mane triangles), stretch 0. Item 1 rebuilds the mane placement: keep the throat-V roots above z 0.8 (the r09 drift lesson) and do not let clip pass 0.5%.

1. **Mane side plates flare out like small wings; clumps look random and stuck on (O major, F major).**
   - Where: 1_beauty az000: the side plates stick out sideways at the shoulders as flat flaps, past the neck outline; hero and 2_closeups mane colour: plates of mixed size at random angles, lumps on the neck rather than a hanging mane. 5_reference front and side: a dark mane hanging straight down the throat and front of the neck to the chest, tips pointing down and to the centre, forming a V bib.
   - Fix: Stage 3: re-place the plates in three tidy rows per side (nape, side, throat), sizes graded (largest at mid-throat, smaller at the nape), all tips pointing down and toward the neck centre line (rotate each side plate 20-30 deg inward about the neck axis), lift off the skin cut from 0.2 to 0.1 of the plate length so no plate edge stands proud of the neck outline in az000. Lengthen the lowest throat pair 25% so the mane ends in a V on the upper chest. Bind `body=` as now.
   - Check: 1_beauty az000: no flap past the neck outline; the mane narrows to a V on the chest like 5_reference front; az090: a hanging mane down the throat; clip <= 0.5%; drift 0.

2. **Cream belly stripe and chest shield are hard rectangles (O major).**
   - Where: 1_beauty az090: a long cream rectangle along the lower flank with straight top edges, and a big cream block on the chest below the mane; az000: a large cream shield fills the chest. 5_reference side: the belly cream is only a thin line underneath; front: the chest is dark mane with a small pale V at its bottom.
   - Fix: Stage 3 (paint only): paint the belly cream only on faces that face down (n.z < -0.6), so from the side it shows as a thin line under the body; the side-facing strip from r19-r20 goes back to the body brown (that also removes the old shadowed-cream plane behind the foreleg). On the chest, keep cream only on the faces below the mane's V tip and within the inner half of the chest width; the rest is body brown.
   - Check: 1_beauty az090: no cream rectangle on the flank; az000: a dark mane over a small cream V, as 5_reference front; borders on edges; colour count unchanged.

3. **Ears are oversized flat pale paddles (F major, O major).**
   - Where: 1_beauty az000 and hero; 2_closeups head colour: each ear is a large cream leaf, flat, as wide as the head and as bright as the antlers, so ears and antler bases merge in az000. 5_reference front: smaller leaf ears, brown outside with a pale inner face.
   - Fix: Stage 2 (vertex moves): scale each ear's outer two sections toward the ear root by about 0.8 (the ear about 20% shorter and narrower); push the front-face centre verts back about 25% of ear depth so the ear is a cupped leaf with thickness (rear faces keep the r15 offset). Stage 3 (paint): ear back and edge faces body brown, only the inner (front-facing) faces pale.
   - Check: 1_beauty az000: two brown leaf ears with pale insides, clearly separate from the antlers; IoU > 0.9.

4. **Antler tips are identical cones; brow tines are small pins (F major, O major).**
   - Where: 2_closeups head colour/wire: every tine ends in a same-length point and the crown tines fan at even spacing; the brow tine is a short pin. Brief: brow tines pointing forward, crowned tips. 5_reference side and front: long forward-curving brow tines, tines that grow from the beam and vary in length.
   - Fix: Stage 3: lengthen the brow tine about 1.7x and angle it forward and up (about 35 deg above horizontal), base width 1.2x so it grows out of the beam; vary the other tine lengths +-25% (bez shortest, trez middle, crown points unequal, longest at the back of the crown), and tilt each crown point 5-10 deg differently. Keep the r14 point build (one taper, back point depth <= 0.015).
   - Check: 1_beauty az090 and hero: forward brow tines and uneven crown points; z-fight 0, slivers <= 2%.

## Should-fix

- Tail: a short dark tail sits on the rump patch as in 5_reference rear; keep it, but if turns allow, thicken it 1.2x so it does not read as a flap in back34.

## Dropped

- None. Nothing needs stage 1.

## Appendix: both reviews verbatim

### Fable 5.1: FIX 7
- top_issues:
  - 2_closeups mane colour: mane clumps are blunt but randomly placed and sized; they read as lumps stuck on rather than a hanging mane with a V bib.
  - 2_closeups head colour: ears are flat pale paddles with no thickness.
  - 2_closeups head wire: antler tines end in thin slivers; brow tines are small pins.

### Opus 5.5: FIX 6
- top_issues:
  - 1_beauty az000: the mane's side clumps flare out as flat flaps at the shoulders, like small wings
  - 1_beauty az090: cream belly stripe is a hard rectangle with borders across faces
  - 2_closeups head: identical ringed cone antler tips; oversized cream ear paddles

### Kit gates (this build, current kit)
- kit_gate_fails: none
- kit_warnings:
  - WARN s4 qa: 3 triangles (0.10% of surface) clip through the body in a pose that did not at rest (pink): a limb through a flap, a paw through the cheek
- clip_area_pct 0.1, stretch 0
