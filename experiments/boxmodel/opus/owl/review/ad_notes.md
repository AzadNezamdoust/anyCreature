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

**Verdicts:** FIX 7 (F) / FIX 6 (O)

## Must-fix, in order

1. **blocker/major [both] Wing-root fold-over.**
   - **Measured:** flip 31 > 4; dark creased wedges at the shoulders even in
     the beauty renders.
   - **Stage 2:** add one logged loop at each wing root.
   - **Stage 4:**
     - Blend the weights: root loop 50/50 body/wing, the next loop 80/20.
     - Move the wing pivot further into the body.
   - **If it is still > 4:** unlock stage 1 and rest the wings closer to
     folded; log it in `NOTES.md`.
   - **Check:** flip ≤ the limit; no purple.
2. **blocker/major [both] Wing and tail tips.**
   - **Problem:** they are paper-thin needle slivers (2.0%).
   - **Fix (stage 2):**
     - Thicken the tips to ≥ 25% of their width (≥ 6% of body width).
     - Merge each wing's two needle tips into one blunt tip.
     - Shorten the plank tail ~25%.
   - **Check:** sliver ≤ 1%.
3. **major [both] Eye rings and glints float off the face.**
   - **Rings:** seat them 20–30% inside, or make them shallow domes in an
     inset.
   - **Glints:** sink them into the pupil.
   - **Check:** float 0; nothing in front of the face profile in az090.
4. **major [O] The head is a cube** (a flat back and sides; the owl reads only
   from the front).
   - **Fix (stage 2):**
     - Log a chamfer on the 4 vertical edges and the top-back edge.
     - Pull the back corners in 12%.
     - Dish the disc centre back 5% so the eyes sit in a dish.
   - **Check:** back34 shows a dome.
5. **minor [both] Tufts and brow.**
   - **Tufts:** they have sliver tips and read as cat ears. Split each tip
     (logged loop plus notch) and tilt it 10° out.
   - **Brow:** the blades jut out like horns. Tuck them 50–60% in and shorten
     the tips 25%.
6. **minor [both] Feet.** They are boxy mitts with a radial toe fan. Narrow
   the toes to 0.7×, taper them, and root the toes from a short palm edge.
7. **minor [F]** The throat is a straight dark strap: make the disc rim follow
   the cheek loops. Also give the beak a visible hook.

## Keep (must not regress)
- front read: big orange eyes, V brows, beak, pale disc with a dark rim
- the value split between brown and cream; the tufts in the base
- the talon strike in the attack
