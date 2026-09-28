# Art-direction notes, round 1 (reconciled)

Two blind reviews ran in parallel against `ART_DIRECTOR.md`: Fable 5.1 and
Opus 5.5. Merged by the orchestrator:

- **[both]** both reviewers flagged it: must fix.
- **[F]** or **[O]** only one flagged it. It is kept because the cited view
  shows it.

Work top-down: blockers first, then majors. Everything on the keep list must
survive. The protocol applies:

- Stage 2 is vertex moves, `flatten` and logged topo ops, with IoU > 0.9.
- Stage 3 is pieces and paint.
- Stage 4 is weights and clips.
- Stage 1 unlocks only where a note says so, logged in `NOTES.md`.

Notes on the gates:

- The kit's tech-QA gates are now part of every stage-4 run and must all
  PASS.
- Z-fighting now counts only same-facing coplanar faces. Face-to-face
  contacts, such as a hoof cap on a leg end, are no longer counted.

**Verdicts:** FIX 6 (F) / FIX 5 (O)

## Must-fix, in order

1. **blocker [both] The ruff plates.**
   - **Problem:** they are paper-thin plates lying on the hump. They read as
     shards or shingles, and from the front they are a second pair of ears.
   - **Stage 3:** REMOVE `piece_ruff`, or rebuild it as 2–3 clumps that are
     ≥ 1/3 as thick as they are long, sunk ≥ 50%.
   - **Stage 2:** raise the shoulder-top loop 6–8% of withers height, peaking
     over the forelegs, so the hump lives in the base.
   - **Check:** the shoulder is the highest point of the back in az090, and no
     plate edge breaks the outline.
2. **major [both] Throat fold-over.**
   - **Measured:** the neck/chest seam folds over in the rear-up (flip 10 > 7).
   - **Fix (stage 4):**
     - Blend the weights across the two throat loops (~50/50 on the seam).
     - Reduce the attack head-lift at f022 by ~15°.
   - **Check:** flip ≤ the limit; no purple at the throat.
3. **major [both] The black nose paint spills down the muzzle as a spike**
   (a spade or fangs).
   - **Fix:** paint black only on the top-front nose pad, bounded by an edge
     loop; log a loop across the muzzle front in stage 2 if needed.
   - **Rest of the muzzle:** paint it pale, with a thin mouth line on the
     lower muzzle loop.
   - **Check:** the nose has a straight bottom edge in az000.
4. **major [both] Ears.** They are pointed, tall, flat planks (canine).
   - **Fix (stage 2):**
     - Lower the tips 35–40% and round the top with a chamfer.
     - Make the depth ≥ 40% of the width.
     - Slide the base out and down the skull corner.
   - **Check:** round half-discs in az000.
5. **minor [both] Eyes.** They are a tiny sliver with a white sclera wedge.
   Make them solid dark beads, 1.5×, with a tiny glint, seated 30%.
6. **minor [O] The forelegs are constant posts.** Narrow the wrist 15%, move
   the elbow back 3%, and flatten the front of the forearm.
7. **minor [F] The body is one flat brown.** Darken the lower legs and paws
   15%, or lighten the chest 10%, on the leg loops.

## Keep (must not regress)
- az090: hump plus head carried low, in the body
- plantigrade paws with toe bumps and dark claws
- broad face with the pale muzzle block; clean base tech
