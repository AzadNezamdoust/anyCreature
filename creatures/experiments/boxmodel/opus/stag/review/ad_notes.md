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

1. **blocker/major [both] Hooves.**
   - **Problem:** the hoof walls are coplanar with the leg end; brown slivers
     show on the hoof walls in the close-ups.
   - **Fix (stage 3):** make each hoof 8–10% wider than the leg end in X and
     Z so no wall is coplanar, and sink the leg's end cap one wall thickness
     inside the hoof.
   - **Check:** solid black hooves in the close-ups; zfight 0 on the hooves.
2. **major [both] Mane.**
   - **Problem:**
     - It is a zero-thickness cape offset from the neck, and the inner face of
       the hem shows.
     - The top rim lies flush (z-fight) with 6 slivers.
     - From the front it is a flat breastplate that hides the neck.
   - **Fix (stage 3):** rebuild `piece_mane` as a CLOSED shell ≥ 5% of neck
     width thick.
     - Sink the attachment rim 1–2% under the surface.
     - Break the lower edge into 3–5 unequal thick clumps, shortening the hem
       points to ≤ 1/3.
     - Narrow the front ~20% so the throat line shows.
   - **Check:** zfight and sliver 0 on the mane; the neck is visible in az000.
3. **major [both] Antlers.**
   - **Problem:** the tines are glued-on cones with dark caps at their roots,
     and they form a COMB of identical parallel spikes. The lowest tine lies
     across the ear in hero.
   - **Fix (stage 3):** rebuild `piece_antlers`.
     - The beam sweeps back, then up, and curves in at the top.
     - Put the brow tine low at the burr, pointing forward over the face (the
       longest), the bez tine just above it, the trez at mid-beam, and a
       crown cup of 3–4 points.
     - Lengths 100/80/70/40–60%; splay ±15°.
     - Each tine grows from a widened node: base sunk 30–40% of its radius and
       flared 1.3×.
     - Keep ≥ 1 tine width of clearance from the ear in hero.
     - Keep the overall height and spread.
   - **Check:** varied tines in az090, a lyre with crowns in az000, nothing
     crossing an ear.
4. **major/minor [both] The eye floats.** Seat it with 1/3 of its depth
   inside; float 0.
5. **minor [both] Rump.**
   - **Problem:** the tail block stands proud of the rump (F), and the hams
     are a rectangular slab (O).
   - **Fix (stage 2):**
     - Pull the tail in 50% and hang it.
     - Slide the stifle loop forward 3%.
     - Chamfer the top of the rump and drop it 2%.
   - **Check:** IoU > 0.9.
6. **minor [both] A pale belly bar shows between the front legs.** Move the
   border back one loop, behind the elbows.

## Keep (must not regress)
- side silhouette: rack, deep chest, slender legs with knees and hocks, small hooves
- long head with a black nose and pale jaw; the rump patch; the palette
- the head-down antler charge (flip 0)
