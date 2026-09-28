# Art-direction notes, NGO repair pass (reconciled, K=1)

Scores (Fable 5.1 / Opus 5.5): 5 FIX / 6 FIX.

**Stage 1 is locked. No unlock is authorised for this pass.** Every fix below is a stage-2, stage-3 or stage-4 change. Stage-2 IoU against stage 1 must stay above 0.9 in every view; stage 3 never edits the base; all gates pass.

Keep what works: the heavy body mass, the hump-highest silhouette in az090, the boxed muzzle with a black nose pad, the paws with rooted claws, and the clean tech sheet (hit/float/z-fight/flip/drift all 0, 0.2% slivers). Both reviewers agree these must not regress.

Kit gates: none failing. clip_area_pct 0.0. There is no item 0.

Fix the must-fix list in order, then the should-fix items if turns allow. Check every item in your own `--review` packet before you call it done.

## Must-fix, in order

1. **Pale muzzle floods the whole face; bib is missing (F major, O major).**
   - Where: 1_beauty az000 and hero: the pale colour runs from the nose up past the eyes to the brow, so the head reads as a koala mask. 5_reference front: the pale block stops under the eyes and a separate pale bib sits between the forelegs. Our az000 shows no bib at all; az090 shows a pale stripe along the jaw and down the throat instead.
   - Fix: Stage 3 (paint only). Restrict the `muzzle` rule to faces in front of ring H2 **and** below the eye-socket line (z below the socket's lower verts); the stop, brow and cheeks go back to `fur`. Cut the jaw/throat stripe: exclude side-facing throat faces (|n.x| > 0.5) from the pale rule between the jaw and the chest. Then widen the chest window so a pale bib shows between the forelegs from the front: z 0.30-0.58, x < 0.20, front-facing (n.y < -0.3), keep the |n.x| < 0.75 guard so it does not leak onto the forelegs (the s3 r02 lesson).
   - Check: 1_beauty az000: pale block ends under the eyes with brown between eyes and ears; a pale bib is visible between the forelegs. az090: no pale stripe along the jaw; the pale ends at the muzzle stop. Colour count stays at 6.

2. **Pointed ears, vanishing eyes (F major, O major).**
   - Where: 1_beauty hero, az090, az000: the ears are pointed cat/wolf blades. 2_closeups head colour: the eye is a tiny black chip about 1/12 of the muzzle width. 5_reference: round stub ears, small but readable eyes.
   - Fix: Stage 2 (vertex moves): on each ear, pull the tip vertex/top ring down about 40% of the ear height and push the top ring outward so the ear becomes a rounded cup about as wide as it is tall; `flatten` the ear's front plane. IoU will not move (ears are tiny). Stage 3: scale piece_eye to about 1.6x its current width (target about 1/7 of the muzzle width), keep it seated in the socket with the front face proud by half its thickness; paint the socket inset a dark brown (the `dark fur` colour) so the eye reads as a dot in a shadow, not a chip on flat fur.
   - Check: 1_beauty hero and az000 at thumbnail size: two round ear stubs and two visible eyes. 2_closeups head: the eye fills at least 2/3 of the socket; eye float 0.

3. **Hump reads as one long arch (O major).**
   - Where: 1_beauty az090 and 5_reference side: the reference back is highest at the withers and falls steadily to the rump; ours is a long arch with the high point at mid-back and the rump nearly as high as the withers.
   - Fix: Stage 2 (vertex moves): raise the top verts of the withers loop (T0-T1) by about 4% of the hump height, and lower the top verts of T4-T7 by 2-3% so the back falls from the withers to the rump. Keep the rump mass (r07) as it is. If the 0.9 IoU floor blocks the full amount, do what fits and log it partly done.
   - Check: 1_beauty az090: the highest point of the silhouette sits over the forelegs; the back line drops by at least 5% of body height from withers to rump. IoU > 0.9.

4. **Dark creases in the armpit and chest under the forelegs (F minor).**
   - Where: 2_closeups front limb colour and wire: a fan of dark thin triangles between the chest underside and the inner face of each foreleg's top ring; the leg's top ring also kinks where it meets the flank.
   - Fix: Stage 2 (vertex moves / loop slide): slide the foreleg's top ring down by about 5% of the leg length and pull its inner (chest-side) verts in toward the leg axis by 3-4% of body width so the flank-to-leg faces meet at one clean angle instead of a fan; move the 2-3 chest-underside verts between the forelegs up to their neighbours' level to remove the pinched triangles.
   - Check: 2_closeups front limb colour: the armpit is one shaded plane with no dark triangles; slivers stay under 0.5%; valley 0.

5. **Legs are constant-section box tubes (O minor, F minor).**
   - Where: 2_closeups front and hind limb: the forearm keeps its full width to the wrist; the hind cannon is a straight block. Brief: thick legs tapering to the wrist.
   - Fix: Stage 2 (vertex moves): scale the wrist ring to about 80% of the elbow ring width, and the hind cannon ring to about 85% of the stifle ring; leave the paw rings as they are so the paw stays wider than the pastern. The dark lower-leg colour band stays (brief: darker lower legs; the reference has it too).
   - Check: 1_beauty az090: forelegs visibly narrow from elbow to wrist. IoU > 0.9.

## Should-fix

- O: the black nose pad is fine; do not enlarge it. F/O agree the claws are good; keep the current claw size.
- Consider a `flatten` on the muzzle's front face so the nose pad sits on one plane (2_closeups head wire shows a slight kink at the nose end).

## Dropped

- O "legs have a hard dark band": dropped. The brief asks for darker lower legs and the reference has the same band; the band is on an edge loop already.
- F "front legs are tube sections with a kink": the kink at the elbow is the elbow angle the reference has; the taper part is covered by item 5.

## Appendix: both reviews verbatim

### Fable 5.1: FIX 5
- top_issues:
  - Pale muzzle spreads up over the whole front of the face to the brow, so the head reads as a koala/sloth-bear mask instead of a pale muzzle block
  - Ears are pointed wolf-style blades, and the eyes are so small they vanish at thumbnail: the face has no read
  - Dark triangular creases and slivers in the armpit/chest under the front legs (front-limb close-up, 2 slivers flagged); front legs are tube sections with a kink
- brief_fit / keep: Body mass and hump are the strongest of the three, but round ears, small readable eyes and a muzzle block are all missed.

### Opus 5.5: FIX 6
- top_issues:
  - pale muzzle colour floods the whole front of the face up past the eyes, and a stray pale stripe runs along the jaw and neck in side view (1_beauty az000/az090)
  - ears are pointed cat ears, not round; the eyes are tiny slits almost lost in the facets (2_closeups head)
  - the hump is weak: the back is one long arch with the highest point mid-back; legs are thick box tubes with a hard dark band
- brief_fit / keep: Heavy, organic bear mass with good paws and claws and clean deformation, but the ears, the muzzle and the hump deviate from the brief.

### Kit gates (this build, current kit)
- kit_gate_fails: none
- kit_warnings: none
- clip_triangles 0, clip_area_pct 0.0
