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

**Verdicts:** FIX 5 (F) / FIX 5 (O)

## Must-fix, in order

1. **blocker [both] Webbing.** It is OPEN single-sided plates (paper fins).
   - **Fix (stage 3):** make closed wedges ≥ 30–50% of toe thickness, sunk
     into the toes and sole, or merge the webbing into the foot.
   - **Check:** open 0; the webs show from below.
2. **blocker/major [both] Spots.** They are 84 open decal plates; some are
   rectangular bars or tilted off the skin.
   - **Fix:** REMOVE `piece_spots`, and paint 5–7 spots on body faces. Log small
     insets in stage 2 if needed; none rectangular, none on the thighs.
   - **Check:** no cyan in `3_tech`.
3. **blocker/major [both] Hip/thigh fold-over.**
   - **Measured:** the hip and thigh fold over in the hop and lunge (flip 32
     > 10).
   - **Fix (stage 4):**
     - Blend pelvis and thigh weights over the two flank loops (50/50, then
       80/20).
     - Cap the knee opening at ≤ 150°.
     - Add a logged hip loop in stage 2 if needed.
   - **Check:** flip ≤ the limit; the thigh keeps its section in move_f012.
4. **blocker/major [both] Tympanum z-fight.**
   - **Problem:** the disc lies flush and z-fights; painted dark, it reads as
     a third spot.
   - **Fix:** sink it 50% with a raised rim, or remove it and paint an inset
     face mid-green.
5. **major [both] Eyes.** They are flat gold coins or washers, not bulging
   eyeballs.
   - **Stage 3:** rebuild the eye as a convex gold half-dome (a ball ~ the
     dome's radius) seated ~40% into the green dome.
     - The pupil is a horizontal lozenge set flush on it, and the glint sits
       on the pupil.
   - **Stage 2:** chamfer the turret top so the dome is round.
   - **Check:** no coin edge in az090 or hero.
6. **major/minor [both] The tongue floats as a paper strip.** Make it a
   rounded bar ≥ 0.3× its width, rooted ≥ 20% inside the mouth floor.
7. **minor [both]** Five shape and paint fixes:
   - **Slivers:** merge the slivers along the mouth groove and the foot edges.
   - **Head/back facets [F]:** flatten the brow, cheek and back into 4–6 big
     facets each (target ~1,600 triangles).
   - **Thighs [O]:** taper hip to knee, knee ~60% of the hip loop.
   - **Head lid [O]:** chamfer the lid between the domes and slope the snout
     down.
   - **Belly [O]:** paint it a warmer cream.

## Keep (must not regress)
- squat pear body tilted up, with the folded hind-leg Z
- wide mouth line with the cream jaw
- green/cream/gold palette with the horizontal pupil
