# raven_wyvern (Fable rebuild): art-director notes, reconciled

Two reviewers (Fable 5.1, Opus 5.5) each saw two packets labelled only
"candidate A" and "candidate B", in parallel. This build was B; the Opus
rebuild (`opus/raven_wyvern_v2`) was A. Both reviewers preferred B by a clear
margin. The orchestrator reconciled the notes per `WORKFLOW.md`.

| | Fable 5.1 | Opus 5.5 | reconciled |
|---|---|---|---|
| verdict | FIX | FIX | **FIX** |
| score | 6 | 6 | **6.0** |

## Must-fix (both reviewers flagged it)

1. **Hackles (stage 3).** One reviewer rated this a blocker, the other a
   major.
   - What: `piece_hackles` are 5–6 flat chips scattered over the neck side
     and the chest. They read as damage or glued-on tiles, and as splinters
     edge-on.
   - Fix: rebuild them as 2–3 bold overlapping clumps hanging from the throat
     under the jaw.
     - Each clump is about 2× the current chip length, with a wedge section
       about 3× as thick.
     - Sink the bases about 0.3 of the depth into the neck.
     - Point the tips down and back, tilted ≤ 20° from the surface.
     - Delete the chips on the chest and the neck side.
   - Check:
     - head close-up: lit top faces and no gap at the roots;
     - hero: the chest reads as one clean plane;
     - az090: the ruff shows in the silhouette.
2. **Wing fingers (stage 3, optional stage 2).** One major, one minor.
   - What: `piece_wingbones` are constant-section square tubes with sharp Z
     kinks, so they read as lightning bolts or staples. The wrist end is an
     open pipe with the claw stuck in it, and the rear finger runs past the
     membrane onto the tail.
   - Fix:
     - Taper each finger to about 40% of its base width at the tip.
     - Give each finger one soft bend (about 140°) at a single, solid wrist
       knuckle that seats the thumb claw.
     - Use a 3-sided section, so the finger casts a shadow line on the
       membrane.
     - End every fingertip on the membrane edge.
     - Optional, stage 2: pull the trailing-edge vertices in by about 5% of
       the wing length between the fingertips, so the edge scallops.
   - Check: no kink sharper than about 45°, no open tube end, no rod past the
     membrane edge; stage-2 IoU stays above 0.9.
3. **Legs (stage 3 + stage 2).** One major, one minor.
   - What: thigh, shank and foot are all one near-black. They merge with the
     dark underside, so the knee and the hock don't read. From the front the
     legs stand out like stilts.
   - Fix:
     - Stage 3: repaint the thigh to the body slate, and the shank and foot
       two value steps lighter (grey-brown). The claws stay black.
     - Stage 2: widen the thigh top about 15% and tuck it into the belly with
       a loop slide; narrow the shank about 30% below the knee; sharpen the
       hock with a vertex move.
   - Check:
     - hind-limb close-up: at least 3 distinct values;
     - az000: the legs separate from the body and taper at least 30% from
       thigh to shank;
     - IoU stays above 0.9.
4. **Dorsal spines (stage 3).** Minor from both reviewers.
   - What: small lilac blades are crowded into the gap between the neck and
     the wing. They add a 7th colour and read as crushed paper, or as a comb.
   - Fix:
     - 4–5 spines graded large to small along the ridge, from the neck base to
       the tail root.
     - Vary the spacing by about 20% and rake each spine back about 30°.
     - Sink the bases into the ridge and raise the spines above the wing line.
     - Paint them the wing-frame near-black. The Fable reviewer suggested the
       membrane purple instead. The Opus rebuild's reviews showed that purple
       spines between the wings read as torn membrane, so near-black it is.
   - Check:
     - hero: no light-purple patch at the shoulder;
     - az090: 4–5 distinct, graded spines on the ridge.

## Kept from one reviewer

5. **Tail (stage 2).** From Fable, a major.
   - What: the tail is about 0.9 of the body length and has a hard elbow at
     mid-length.
   - Fix: slide the mid-tail ring so the outline is one continuous curve.
   - Dropped: lengthening the tail by 25–30%. That needs a stage-1 unlock,
     which is reserved for blockers, and the Opus reviewer's keep list cites
     the tail carried out behind as part of the wyvern read. It stays as a
     residual.
6. **The head from the front (stage 3 + stage 2).** A minor from each
   reviewer, on different parts.
   - What:
     - the pale cheek spurs read as tusks or a second pair of horns (Fable);
     - head-on, the upright horns read as ears, so the face reads as an owl
       or a cat (Opus).
   - Fix:
     - shorten the spurs by 50% and repaint them horn-black, or remove them;
     - rake the horns back about 25° with the tips bent outward;
     - stage 2: chamfer the flat skull-top edges.
   - Check: az000 shows one horn pair sweeping back.
7. **Eye ring (stage 3).** From Opus, a minor.
   - What: the ring stands proud of the cheek in back34.
   - Fix: move `piece_eye` inward by its own thickness. Keep the design; both
     reviewers' keep lists cite it.
8. **Throat (stage 2).** From Fable, a minor.
   - What: a notch where the neck enters the chest.
   - Fix: loop-slide and flatten the throat ring.
   - Check: in az090 the throat is one convex curve.
9. **Wing root in the attack (stage 4).** From Opus, a minor.
   - What: at attack f016 the far wing's upper arm pops up above the back as
     a post, and the wing root crumples.
   - Fix: rebind the wing root with `body=` so the shoulder blends the chest
     and upper-arm weights, and cut the far-wing raise at f016 by about 15°.
   - Check: `flip_area` stays under its limit.

## Keep

- The forward-pitched crouch, with the long S-neck and the tail carried out
  behind: the wyvern read comes from the base.
- The eye: amber ring, black pupil and catchlight under a heavy black brow.
- The heavy raven bill with its pale tip; the attack lunge with the wing
  mantle; the alternating stride.
