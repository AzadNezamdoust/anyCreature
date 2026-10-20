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

**Verdicts:** FIX 7 (F) / FIX 5 (O)

## Must-fix, in order

1. **blocker [both] Loincloth, belt and buckle.**
   - **Problem:**
     - They are OPEN zero-thickness plates (open 66).
     - The belt cuts through the loincloth (hit 1) and z-fights the belly.
   - **Fix (stage 3):** rebuild all three as closed solids.
     - Flaps ~2 cm (1.5% of height) thick.
     - The belt a closed band ≥ 3× thicker, offset 2–5 mm from the belly.
     - The buckle a box.
     - Tuck the flap tops fully under the belt, and rest the back flap on the
       buttocks.
   - **Check:** open 0, hit 0, zfight ≤ 2.
2. **blocker [both] Posed fold-over.**
   - **Measured:** the flaps and the left shoulder fold over (flip 15 =
     0.97%).
   - **Fix (stage 4):**
     - Bind the loincloth rigidly to the pelvis/hip bone, not the thighs.
     - Blend the shoulder weights between chest and upper arm.
   - **Check:** flip ≤ 0.5%.
3. **major [F+O] Hands are mitts with spikes** (the feet likewise), and they
   are undersized.
   - **Stage 2:** scale the hands 1.3× about the wrist by lengthening the
     fingers, and cut finger gaps (two per hand, one per foot).
   - **Stage 3:** rebuild the claws as digit wedges with claw tips, rooted
     1 cm in.
   - **Check:** three separated digits, and hand width ≥ 1.6× the wrist.
4. **major [O] In profile the nose is a straight pipe.**
   - **Fix (stage 2):** pull the tip down ~30% of the nose's length and back
     10%, and taper the bridge so it hooks over the lip.
   - **Keep:** the face must still read.
5. **major [O] The skull top is a flat darker lid** (a tin can in back34).
   - **Stage 2:** dome it, raising the top-centre +12% of head height, and
     chamfer the rim.
   - **Stage 3:** paint the lid skin green.
6. **major [O] The pot belly is a pale rectangular block** (a tube top).
   - **Stage 2:** push the belly centre forward 10% and round the top border.
   - **Stage 3:** paint the pale colour on the lower belly only, with a curved
     border on a loop.
7. **minor [both]** Four small face and limb fixes:
   - **Ears:** thicken the root to 2× and round the back plane.
   - **Mouth:** curve a grin by moving the corners up 1/3 of the mouth's
     height.
   - **Fangs:** scale the outer two 1.5–2×.
   - **Arms:** widen the forearm 15% and add an elbow plane.

## Keep (must not regress)
- the face (brow, hook nose, fanged grin, glint eyes) reads at thumbnail size: improve it, don't lose it
- proportions: big head, long ears, crouch, arms to the knees
- palette: green skin, brown cloth, cream buckle
