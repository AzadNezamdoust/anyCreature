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

1. **blocker [both] The shoulders fold over in the overhead attack raise.**
   - **Measured:** flip 36 = 2.6% against a limit of 0.5%.
   - **Fix (stage 4):**
     - Blend the deltoid and trapezius weights between the chest/clavicle and
       the upper arm, about 50/50 on the seam loop.
     - Cap the raise at ~110–150° of shoulder flexion.
     - Bind the moss and rocks with `bone=` spine or chest so they stop
       shearing.
   - **If it still folds (stage 2):** add a logged loop around each shoulder,
     ~5 cm below the armpit.
   - **Check:** flip ≤ 0.5%; no purple in `3_tech`.
2. **blocker [both] Loincloth and belt.**
   - **Problem:**
     - The loincloth is a thin plate.
     - The back flap floats with a gap.
     - The belt z-fights the waist.
     - The strap edges produce 28 slivers.
   - **Fix (stage 3):**
     - Make the loincloth a SOLID wedge, ≥ 4 cm thick at the belt, tapering to
       2 cm.
     - Tuck its top 2 cm inside the belt.
     - Rest the back flap on the buttocks, at ~70% of the front flap's width.
     - Make the belt a closed 3 cm strap offset 1 cm from the body.
   - **Check:** float 0, zfight ≤ 2, slivers ≤ 2%.
3. **blocker [both] Moss.**
   - **Problem:** it is paper-thin planks; edge-on (az090) the pieces are
     green sticks.
   - **Fix (stage 3):** rebuild as 3–4 lumpy clumps, each ≥ 25% as thick as
     it is wide (≥ 6 cm).
     - Sink each 1/3 into the shoulder and drape it over the shoulder edge.
     - Break the top into 3–5 lumps, and bed one rock into a clump.
   - **Check:** the moss reads as mounds in az090; moss sliver 0 and flip 0.
4. **major [both] Eyes read as goggles or a welding mask.**
   - **Problem:** yellow hexagons in black rectangles.
   - **Stage 3:** repaint the sockets dark blue-grey (~30% value), shrunk to
     1.2× the eye. Reseat the eye so the pupil dominates and the amber ring
     is thinner.
   - **Stage 2:** inset the socket and push it back under the brow. Add a
     mouth line between the tusk roots and push the nose plane out 3 cm.
   - **Check:** az000 thumbnail shows eyes in the brow's shadow, and the
     tusks rise from a mouth.
5. **major [both] Fists read as tan mitts or boxing gloves.**
   - **Stage 3:** repaint the hands in the body's blue-grey, knuckles a little
     lighter and nails dark.
   - **Stage 2:** vary the finger lengths (middle longest, little finger ~30%
     shorter) and chamfer a knuckle ridge.
   - **Thumb:** add a thumb crossing the front of each fist (a stage-3 piece
     is OK).
6. **minor [both] Rocks are pebbles.** Scale them 1.8×, vary the three
   shapes, and sink each 30%.
7. **minor [both] The back is a flat slab and the side view a box.**
   - **Stage 2:** flatten shoulder-blade planes with a spine groove between,
     and round a trapezius hump.
   - **Stage 4:** pitch the spine 10–15° forward in idle and move, with the
     neck counter-rotated so the gaze stays level.
8. **minor [F] A hairline sliver runs along the top of the brow shelf.** Slide
   or merge that loop.

## Keep (must not regress)
- the hunched mass: small sunken head, massive shoulders, arms to the knees (troll read)
- separate finger blocks, knuckle row and thumb: improve them, don't remove them
- the heavy brow shelf and the upward tusks; green moss and cream tusks
