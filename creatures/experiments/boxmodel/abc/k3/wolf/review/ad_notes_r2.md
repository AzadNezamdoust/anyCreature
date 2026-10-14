# Art-direction notes, repair round 2 (reconciled, K=2)

Scores (Fable 5.1 / Opus 5.5): 7 FIX / 6 FIX.

**Stage 1 is locked. No unlock is authorised for this pass.** Every fix below is a stage-2, stage-3 or stage-4 change. Stage-2 IoU against stage 1 must stay above 0.9 in every view (minimum is 0.985 now); stage 3 never edits the base; all gates pass.

Keep what works (round 1 fixed these; do not regress):
- No ruff plates on the shoulder or foreleg, no shards; the plates lie down along the neck (r12, r17); clip 0.
- No spine comb; the dark saddle is paint only (r13).
- Throat fold-over fixed: flips 0 (r14). Keep the ring-5 move.
- Grey brush tail with a dark tip (r15); paws taper to a leading toe (r16); larger amber eye (r18).
- Wedge head, tall ears, cream bib, tan legs: the palette and identity match 5_reference.

Fix the must-fix list in order, then the should-fix items if turns allow. Check every item in your own `--review` packet before you call it done.

## Must-fix, in order

0. **Kit gates.** No FAIL on the current kit; clip_area_pct 0.0, stretch 0. Nothing to do; keep it that way.

1. **Ruff is a few flat slabs stacked on the neck (F major, O major).**
   - Where: 2_closeups ruff colour/wire and head colour: about six large flat plates around the neck, each a separate slab with a hard edge, sitting on the surface; 1_beauty az090 and hero: lumps behind the head. 5_reference side and front: a thick mane of many pointed clumps in layers, pale at the throat and cheeks, grey on the nape, sweeping back and down.
   - Fix: Stage 3: rebuild the ruff as 3 rows of `shingle()` clumps per side (cheek row 3, mid row 4, rear row 3; 10 per side), each about 60% of the current plate size, pointed tips sweeping back and down, overlapping 30% with the row behind; keep the r17 direction (0.25 normal) and sink each root 30% of its thickness. Paint the cheek and throat row cream (the bib colour), the rear row grey; no clump on the shoulder band (the r12 lesson).
   - Check: 2_closeups ruff colour: a layered, pointed mane that grows out of the neck; 1_beauty az090: shaggy ruff silhouette like 5_reference side; hit/float 0; clip 0; slivers <= 2%.

2. **Toe claws are needle slivers on a plain block paw (F major).**
   - Where: 2_closeups front limb and hind limb colour: thin black needle claws on the front face of a tan block paw; 1_beauty az000: barely visible specks. 5_reference front: dark toe tips and short thick claws, middle toes leading.
   - Fix: Stage 3: rebuild the claws 2x thicker at the base (about 1/5 of the paw width) and 70% of the current length, curved down so the tips touch the ground line; keep the r16 placement (middle claws leading, outer splayed). Paint the toe-front faces of the paw (the faces the claws root in) dark grey so the toes read, as in 5_reference front.
   - Check: 2_closeups front limb colour: four short dark claws on dark toe tips, middle two leading; hit/float 0.

3. **Eye is a small amber triangle with no brow (F major).**
   - Where: 2_closeups head colour: the eye is an amber triangle chip on a flat side plane; 1_beauty az000: it reads, but as a triangle, with no brow above it. 5_reference front and side: an almond eye with a dark rim under a slight brow.
   - Fix: Stage 2 (vertex moves): move the skull verts just above each socket outward about 3% of head width and forward 2% so a brow overhangs the eye. Stage 3: give the eye lens an almond outline (6 points: two sharp corners front and back, flatter top and bottom) instead of the triangle; paint the socket ring faces dark grey as a rim; keep the r18 size.
   - Check: 2_closeups head colour: an almond eye with a dark rim under a brow; 1_beauty az000 at thumbnail: two eyes under brows; z-fight 0; IoU > 0.9.

4. **Weak tuck-up; the belly line runs straight to the hind legs (O major).**
   - Where: 1_beauty az090: the underline drops only a little from chest to flank; the waist is as deep as the chest at the rear. Brief and 5_reference side: a deep chest with a clear tuck-up at the waist.
   - Fix: Stage 2 (vertex moves): raise the bottom verts of the two waist rings (between the elbow and the stifle) by about 6% of the body height, graded (most at the ring in front of the thigh), and pull their low-side verts in about 3% of body width. Keep the brisket where it is.
   - Check: 1_beauty az090: the underline rises clearly from the chest to the flank; IoU > 0.9; flips 0.

5. **A cube tab behind the ears and a dark "pendant" between the forelegs (O minor).**
   - Where: 2_closeups ruff colour and 4_posed attack_f016: a small block sticks up on the nape behind the ears; 1_beauty az000: a dark grey shape hangs between the forelegs: it is the tail's dark tip seen through the leg gap (NOTES r19), but it reads as a pendant.
   - Fix: Stage 3: find the nape tab (a ruff or saddle piece corner) and delete or sink it below the skin line; item 1's rebuild may remove it. Stage 4 (clip keys): pitch the tail root back about 12 deg on every idle key, keeping it low, so the dark tip sits behind the hind legs and out of the front leg gap in az000.
   - Check: 1_beauty az000: nothing dark between the forelegs; 4_posed attack_f016: no tab on the nape; fold-overs 0.

## Should-fix

- O: legs are box tubes. Stage 2: scale the pastern rings to about 80% of the forearm ring (front) and 80% of the hock ring (hind), keeping the paws.

## Dropped

- None. Nothing needs stage 1.

## Appendix: both reviews verbatim

### Fable 5.1: FIX 7
- top_issues:
  - 2_closeups head colour: the eye is a tiny amber triangle chip with no brow; it does not read at thumbnail in 1_beauty az000.
  - 2_closeups front limb colour: toe claws are thin black needle slivers on a plain block paw; no middle toes leading.
  - 2_closeups ruff colour: the ruff clumps are a few flat slabs stacked on the neck, they sit on the surface rather than in it.

### Opus 5.5: FIX 6
- top_issues:
  - 1_beauty az090/4_posed attack_f016: ruff chunks sit as separate lumps on the neck, with a small cube tab sticking up behind the ears
  - 1_beauty az000: a dark grey pendant hangs between the front legs under the chest
  - 1_beauty az090: weak tuck-up; legs are box tubes with blocky paws

### Kit gates (this build, current kit)
- kit_gate_fails: none
- kit_warnings: none
- clip_area_pct 0.0, stretch 0
