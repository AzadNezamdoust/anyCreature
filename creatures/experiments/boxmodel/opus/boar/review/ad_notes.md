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

**Verdicts:** FIX 6 (F) / FIX 6 (O)

## Must-fix, in order

1. **blocker [both] The tusks pass through the lip and cheek (hit 2),** and
   no tusk shows in the silhouette.
   - **Fix (stage 3):**
     - Root each tusk INSIDE the lower jaw at the mouth corner, with a base
       ≥ 3 cm.
     - Curve it up and out, rotated ~15° outward, so it clears the upper lip
       by ≥ 1 cm and the tip clears the muzzle by ~4 cm.
     - A stage-2 lip notch is optional.
   - **Check:** hit 0; no magenta; the tusk curve shows in the az090
     silhouette.
2. **major [F] Ears.** They are tall and narrow, deer/donkey-like, with sliver
   tips.
   - **Fix (stage 2):**
     - Move the tips down 40% of ear height and angle them out 30°.
     - Widen the base 30% and thicken the root.
   - **Check:** az000 ears stay inside the head width; the ear slivers are
     gone.
3. **major [both] Bristle crest.** It is evenly spaced cones or saw plates (a
   stegosaurus row).
   - **Fix (stage 3):** rebuild it as ONE ridge strip.
     - 6–8 overlapping clumps of varied height, the tallest over the hump,
       leaning back ~30°.
     - Each clump is ≥ 40% as wide as it is tall.
     - Fuse the bases and sink them 1 cm into the spine.
   - **Check:** az090 reads as a mane, and az000 shows width.
4. **minor [both] Face.**
   - **Mouth:** there is no mouth line. Stage 2: inset a crease from the snout
     disc back 1/3 of the head length.
   - **Eye:** it is a flat dot with no brow. Stage 2: pull 2–3 brow verts out
     ~1 cm. Stage 3: scale the eye 1.2×.
5. **minor [O] The snout disc is bright pink** and reads as a domestic pig.
   Paint it dusky grey-mauve (~35% value), with the nostrils near-black.
6. **minor [O] The shoulder saddle is a hard rectangle.** Move its border onto
   loops that taper down from the crest in a V.
7. **minor [both] Underline and legs.**
   - **Stage 2:** drop the brisket 8% and raise the groin 8% (the underline
     rises).
   - **Forearm:** +15% at the elbow and pinched 10% at the pastern.
8. **minor [F] The base brown is muddy in shadow.** Lighten it 10–15%, and
   keep the saddle dark.

## Keep (must not regress)
- front-heavy hump in the base and the long wedge head (az090)
- cloven hooves and hock angles
- clean deformation (flip 0)
