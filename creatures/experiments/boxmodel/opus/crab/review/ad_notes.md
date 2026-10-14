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

1. **major [both] Walking legs.** They are identical straight tapered spikes
   with no knee (pencils or spider legs), the repeated-spike tell.
   - **Fix (stage 2):**
     - Log a loop at ~40% of each leg's length and raise it so the upper
       segment climbs ~10% of body height above the rim before the lower
       segment drops.
     - Make the merus a paddle: 1.5× thicker, twice as wide as deep, and
       shorten the leg 20%.
     - Fan the pairs: the front pair 20° forward, the rear pair 25° back,
       each elbow angle varied ±10°.
     - Paint black only on the last 15%.
   - **If IoU breaks:** unlock stage 1 and log it.
   - **Check:** a knee above the rim in az000; varied splay.
2. **major [both] Carapace crown.**
   - **Problem:** it is a radial fan of ~30 spokes on one pole, which reads as
     a pie lid.
   - **Fix (stage 2):** log two insets to replace the fan with a central plate
     and a ring.
     - Flatten the ring into 5–6 big planes with a soft mid ridge.
     - Remove the clusters of small triangles on the front plates.
   - **Check:** no vertex with more than 8 edges on top.
3. **major [O] The toothed front edge is missing.**
   - **Fix:** move alternate rim verts outward 4–6% to cut 4–5 teeth per
     side; log a rim loop first if there are too few verts.
4. **major [O] The move clip has no steps.**
   - **Fix:** key an alternating tetrapod gait: L1, R2, L3 and R4 swing while
     the others stay planted.
     - Lift the tips 15% of leg length and move the body sideways.
     - Keep planted tips fixed in world space.
5. **minor [F] Claws.**
   - **Gap:** open a ~15° gap between the fixed and movable fingers.
   - **Hinge:** seat the movable finger's root 20% deeper in the palm.
   - **Palm:** flatten its outer face into 2 planes.
6. **minor [both] Eye stalks.**
   - **Stalks:** they are pins with slivers at the roots. Make them 1.5×
     thicker at the base and tilt them 15° out.
   - **Eyes:** rounded bulbs 1.3× the stalk width.
   - **Roots:** chamfer the socket rims.
7. **minor [O] The barnacles are scattered pebbles.** Cluster them near the
   rear edge, scale them 1.5–2×, and sink them 30%.

## Keep (must not regress)
- chunky claws that snap in the attack
- the wide low shell with the claws in front reads as a crab
- clean tech (hit/float/zfight/flip 0): keep it clean
