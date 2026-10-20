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

1. **blocker [both] Ruff.**
   - **Problem:**
     - It is a flat jagged bib: a shard beside the neck in back34 and a flap
       in hero.
     - Its points hang below the chest like a comb.
     - A hood peak behind the ears breaks the neck line.
   - **Fix (stage 3):** rebuild `piece_ruff` as a THICK collar (≥ 25% of
     neck width) that wraps the sides of the neck.
     - End it in 3–4 blunt clumps at the chest, not a row of points.
     - Put its top edge below the ear base, remove the side flap, and offset
       it 2–3 mm where it lies on the chest.
   - **Check:** no shard in back34, no bump behind the ears in az090, all
     zeros for the ruff in `techqa`.
2. **blocker [both] Toes.**
   - **Problem:** each toe is a black cube glued flat on the paw, and the toes
     z-fight.
   - **Fix (stage 3):** make each toe a wedge that grows out of the paw.
     - Sink the base 1 cm along the toe axis and lift it 3 mm off the sole
       plane.
     - Paint black only on the front 40% (the claw).
     - Keep no face coplanar and same-facing with a paw face.
   - **Check:** `techqa` zfight ≤ 2; the toe close-up shows a tan toe with a
     black tip.
3. **major [both] Tail.** It is a thin tube, not the bushy mass the target
   asks for.
   - **Stage 3:** rebuild `piece_tail_brush` as a sleeve from 25% of the tail
     length to the tip.
     - It is widest at 1/2–2/3 of the length, at 1.8–2× the root width.
     - Give it a blunt taper and 2–3 offset clumps underneath.
     - The dark colour covers only the last 20%.
   - **Stage 2:** widen the tail-root loops 30%.
   - **Check:** az090 reads as a brush at 128 px.
4. **major [both] Eyes are invisible from the front (az000), and the eye
   pieces float.**
   - **Stage 2:** flatten the eye plane, rotated 15–20° toward the front.
   - **Stage 3:** scale the eye 1.2–1.3× and seat it 1 mm into the socket.
   - **Check:** az000 shows two amber eyes; `techqa` float = 0.
5. **major [both] Legs.** They are stilts of constant section, with a hem
   step ring where the body meets each leg; the grey/tan colour border sits on
   that ring ("trousers").
   - **Stage 2:**
     - Slide the body's bottom loop in to meet each leg's top ring flush.
     - Widen the forearm 25% at the elbow and the lower hind leg 15%, tapering
       to the pastern.
     - Flatten an elbow plane at the back of each foreleg.
     - Make the paws 20% wider and flatter.
   - **Stage 3:** repaint the grey down the outer upper leg, and move the tan
     border to the wrist/hock on an existing loop.
   - **Check:** az000 leg width ≥ 1/4 of chest width; no ring at the top of
     the legs; IoU > 0.9.
6. **major [O] The underline is a straight box.**
   - **Fix (stage 2):** drop the sternum loop ~10% of body depth, and raise
     the belly loop in front of the stifle ~15% (a tuck-up).
   - **Check:** az090 chest depth ≥ 1.3× waist depth.
7. **minor [both] Nose and mouth.**
   - **Problem:** the nose is a black square covering the whole muzzle end,
     and there is no mouth line.
   - **Fix:** paint the nose on the top half of the muzzle tip. Add a logged
     partial loop or inset as a mouth line, 1/3 of the muzzle length back
     from the nose.
8. **minor [O] Ears.**
   - **Problem:** they are as tall as the head (fox/jackal).
   - **Fix:** move the tips down to 0.8× and widen the base 10%.
9. **minor [both] The move clip has no stride.** Swing shoulders and hips
   ±20–25° in diagonal pairs, add a body bob of 3–5% of height, and keep the
   paws planted through contact.

## Keep (must not regress)
- side silhouette in az090: wedge head, ears, tuck and hock read as a wolf
- palette: grey with a dark saddle, cream, tan legs, amber eye
- stepped brow and long muzzle; the body mesh is tech-clean
