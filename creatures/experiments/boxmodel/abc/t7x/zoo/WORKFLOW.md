# Zoo workflow v2: concept sheet to S4, junctions first (2026-10-18)

This is the per-creature procedure for the zoo: the 20 new creatures and the rebuilds of the current 20.
It extends `creatures/experiments/boxmodel/BRIEF.md`; BRIEF stays the base contract.
`HANDOFF.md` owner rules are binding and win over this file.
What changed from v1:
- the junction probe, eye check and membrane check now gate the round (`--junctions`);
- zoomed junction crops are reviewed every round;
- the density rule is fixed;
- there are biped chin/jaw and shoulder checklists.

Paths below are from the repo root. Python: `C:\Users\AZAD\AppData\Local\Programs\Python\Python311\python.exe` (`py -3.11`), with `PYTHONUTF8=1`. Run one Blender process at a time per agent.

## 0. Rules that never bend

- **Technique:** the t7 hand box model only.
  - One spine loft of half rings.
  - Legs, arms, ears, fins and wings are extruded from regions of the loft; detail pieces sit on top.
  - Staged S1 lock, then S2, S3, S4.
  - Rejected: image-to-3D, SDF or voxel remesh as the final mesh, subdivision cages, GLSL implicit, anyCreature engine JSON, the c2 cage.
- **Look:** like `abc/t7x/wolf_base`. Crisp flat planes, flat colour, low-to-mid poly. Shape before colour. The creature reads as its species from every angle.
- **Face:** simple. A small, clear, round lens eye sits in a clean socket. No masks, no liners, no big cartoon eyes. Bipeds have a chin and a jaw.
- **Density:** 2x, mainly on the body loft. Never revert density to fix a problem; fix it inside the dense mesh (section 3).
- **Junctions are the #1 visible flaw.** Probe them and look at them every round (sections 4 and 6).
- **Taste:** owner taste beats AI judge scores. When the owner says something is bad: stop and wait.

## 1. Concept sheet (stage 0)

1. Fresh GPT sheet, through the Codex CLI only.
   - One new session per image, at most 2 at a time, positive wording.
   - Ask for: true orthographic views (side facing left, front, rear, top), a symmetric leg pair, a chunky near-real style, a small round lens eye, plain flat colour.
   - Save it as `refs/gpt/v3/<creature>/sheet_N.png`.
2. Run `kit/refs.py`, which writes `reference/` and `blueprint.json`.
   - Do not redraw the trace; add marks (eye, joints) only.
   - When a plan-view trace splits (dark ears, a slit along the axis), redraw that part by hand from `top.png` and say so in NOTES.
3. Write in NOTES.md the creature's **identity cue** (what makes it this species, not a near neighbour) and put it in the S1 silhouette. The raven_wyvern lesson: pieces cannot rescue a base that says "bird".

## 2. S1: the locked base (loft + extrusions)

- `J` at the top of the program names every root the rig and the guide need: limbs, `earL/earTipL`, `tail0..`, wing roots. The probe finds roots from the rig's bones, so name them: `upperarm.L`, `thigh.L`, `ear.L`, `tail0`, `wing.L`, `fin.L`. A wing or fin built as a piece is found from its object name (`piece_wing`, `piece_fin_*`).
- Extrude each limb from a **broad region** of loft faces: 4–5 faces for a leg or arm, 2 for an ear. Never from one face. Never from a strip one face tall.
- Gates: BRIEF section 3 (IoU, proportions, topology, profiles), plus the round loop below with `--junctions` on the lock round.

## 3. The density rule (2x, fixed inside the mesh)

1. Put the 2x on the **body loft**: more spine stations and more vertices per half ring (6 to 10 and up). Limbs get more stations only where they taper or bend (forearm, gaskin, hock).
2. **Rings sit on clean flat planes.** An inserted station is a straight in-between of its two neighbours: centre, tilt, top, bottom and width lerped, and the section a flat lerp. Every split face then stays co-planar. This is the fox pass-9 fix: the shoulder (C0) and hip (R1) breaks stayed crisp. Never use a Catmull-Rom bulge on big masses: it makes rib bands and lumps (bear, boar, golem, ogre, knight, croc).
3. **Density goes where the outline bends:** neck curve, tail taper, the shoulder and hip turn, a snout taper, the belly tuck. Keep big flat masses (head planes, a golem's rock blocks, armour) at one plane per form; split them co-planar if the budget needs the vertices.
4. **Never revert density** to fix a problem: no "verdict mix/revert" (pass 5 lost the density). Fix the problem inside the dense mesh: move rings, flatten groups (`flatten`, `planarize`), slide a loop.
5. Lock the head, eye and brow geometry during a density pass, then re-run the eye check. Re-lofting the head shrank and hid eyes on the goblin, ogre and octopus.

## 4. Junction rules (build them right, then probe them)

What the owner circles:
- slits, holes and white specks;
- knife folds and pinches;
- narrow seam strips;
- paper-thin membranes;
- pieces poking through;
- strap gaps.

Build rules:

- **Broad, blended joins.** The limb's first ring is a wide transition ring that hugs the torso side. The torso planes run across it into the limb. Two to three rings make the turn, and no single fold is sharper than about 60 deg.
- **The shoulder sits over the ribcage.** The torso carries the shoulder line: the chest rings widen up and out into a deltoid cap, and the cap steps down into the upper arm. The arm is never a tube butted against the chest side; the ogre redline was exactly that.
- **The leg rises out of the flank.** The thigh's root region takes the flank faces from the hip bone down to the belly line. The haunch planes continue into the thigh. There is no slot between the thigh's rear wall and the haunch: the fox and dragon hind roots show 150–170 deg concave folds there.
- **Ears, horns and tails:**
  - an ear base takes 2 faces, set on a flat skull plane, with no fold-back where the ear's front meets the skull;
  - a tail root is a ring at least as wide as the tail's first station, blended over the rump.
- **No narrow seam strips.** No band of faces much thinner than its neighbours along a join. Where one appears, slide its loop until the faces are near-square, or merge it into the neighbouring ring.
- **No slits.** Two surfaces never run parallel closer than 10% of the limb radius (an arm resting on the chest, a thigh against the belly). Move them apart or merge them.
- **Pieces sit on the body, never through it.**
  - Bands, straps and belts: the outer face is evened out and the inner face hugs the skin, sunk about 1 cm (ogre crop pass 6).
  - A piece that crosses a crease takes one shared radius over the crease; never a ray hit per segment.
- **Membranes have thickness.** Wings, fins, sails, frills, capes and flaps are closed slabs at least `max(6 mm, 0.4% of the creature's size)` thick, with a rim. Never an open plate. The dragon's wing failed this: p10 5 mm on a 3.8 m dragon.
- **Posed:** a tail sits outside the hind legs' swing. An arm swing clears the other arm. Check the clip numbers at S4.

## 5. Face rules: eye, chin and jaw

**Eye** (all creatures):
- S2 cuts a socket: one inset in a flat face under the brow, sunk a little.
- S3 adds a separate lens piece named `piece_eye`: round, part inside the socket, part proud (≥ 0.5 mm; 8–18 mm on the current zoo).
- The pupil is a darker disc on the lens.
- Size: lens diameter 6–24% of the head's length (the current zoo sits at 6–11%).
- It must show in the front, 3/4 and side views. The eye check measures the visible lens area against the lens disc: front ≥ 0.15, 3/4 ≥ 0.35, side ≥ 0.40.
- A brow that hides the lens from the side fails: ogre before8 was 0.35 from the side.

**Biped checklist** (ogre, goblin, knight, golem and any humanoid). Tick each in NOTES at S1 lock and S4:
1. **Chin and jaw:**
   - A jaw-line ring under the lower jaw (the ogre's H0u), its front 2–3 cm ahead of the neck.
   - The lower jaw plane has a visible underside.
   - The neck ring sits back and narrower than the jaw.
   - From az090 there is a step between the chin and the throat. The head never flows straight into the chest.
2. **Shoulders:**
   - The trapezius steps down from the neck to the shoulder.
   - The chest rings widen up and out into the deltoid; the deltoid bulge is wider than the upper arm.
   - The arm root takes 5 faces of the chest span and its first ring hugs the chest.
   - From the hero and az000 views, the shoulder reads as part of the chest ("connected"), not a separate block.
3. **Arms:** they hang slightly forward of the torso, A-pose, with ≥ 4% of height clear of the torso (separation check).
4. **Legs:** knees slightly bent, weight over the feet, and a groin blend with no slit between the thighs.
5. **Hands:** a parts-library hand (`hand_mitten`, `fist`, `hand_three_finger`), not a plain block, unless NOTES says why.

## 6. The round loop (every round, S1–S4)

```
py -3.11 creatures/experiments/boxmodel/kit/run.py <prog> --stage N --round R --junctions [--no-orbit] [--lock]
```

Use `--junctions` every round from the S1 lock on. It writes:
- `stageN/junctions/sN_rRR_*`: one crop per junction root from three angles (A: out-front-high, B: out-rear-high, C: from below, the armpit/groin view), plus a flag heatmap;
- the eye crops (front, 3/4, side);
- `sN_rRR_junctions.json`;
- `rounds/sN_rRR_junctions.jpg`.

A junction FAIL makes the round NOT OK. To probe the latest build without rebuilding: `run.py <prog> --junctions`. For any GLB: `py -3.11 creatures/experiments/boxmodel/kit/junction_gate.py <glb> <outdir> --tag x`.

**Review by zoomed crops** (what the owner does; do it before writing NOTES):
1. Open `rounds/sN_rRR.jpg` (whole creature) **and** `rounds/sN_rRR_junctions.jpg`.
2. For each junction row, look at the three beauty crops first, as the owner would. Look for:
   - slits and specks (background showing through);
   - knife folds (a hard dark line along a join);
   - narrow seam strips;
   - pinches;
   - pieces through skin;
   - gaps under straps.
3. Then read the flag tile:
   - red knife fold, yellow seam strip, orange slit, cyan open edge, magenta poke-through, blue gap, pink posed clip, teal thin membrane, purple pinch (warn);
   - off-white is the probed region.
   A flag the crop does not show is noise. Note it and move on; do not chase numbers the eye cannot see.
4. Eye row: the lens reads as a small round lens in all three crops.
5. NOTES.md, 3–5 lines per round: **Critique** (the single worst visible flaw, which crop or view shows it), **Diagnosis** (which rings or vertices), **Fix** (one change), **Result** (better or worse, the gate numbers that moved, tris).

Round limits are as in the BRIEF (S1 14, S2 6, S3 5, S4 4). One diagnosed fix per round. If the same gate fails 3 times for the same reason, stop and report.

## 7. Stages, with the new gates

| stage | build | must pass |
|---|---|---|
| S1 | loft + extrusions, `--lock` | BRIEF S1 gates; junction probe: open 0, no knife folds over 1.0 r, no seam strip over 1.0 r, slit ≤ 1.5%, poke 0 |
| S2 | joint loops, eye socket (`inset`), brow/cheek moves, `flatten` planes | lock hash, IoU > 0.9; junction probe as S1 |
| S3 | pieces: lens eye, claws, bands, membranes; 4–8 flat colours; `smooth_borders()` right after `paint()` | techqa; junction probe as S1 + gaps 0; eye check; membrane check; band seat (warn); detail gate (`--details`, section 10) |
| S4 | rig, idle/move/attack | glbcheck, techqa posed; junction probe + posed clip ≤ 1.0% of each chain's area vs any other chain; detail gate PASS |

`judge()` in `kit/junctions.py` holds the exact rules and `LIMITS` the numbers.

## 8. The probe's numbers (kit/junctions.py), and what they mean

Junction roots come from the rig:
- every bone whose parent is a trunk bone (central, not a tail) and which is not trunk itself: limbs, ears, horns, tails, tentacles;
- every piece named wing, fin, sail, membrane, frill, dorsal or pectoral, one per side.

- centre-line bones named like an appendage (fin_dorsal, crest, a centre horn) are junctions, not trunk.

`r` is the chain's radius at its root (a mirrored pair shares one r). The region excludes other chains' faces (an ear rim inside a shoulder's 2r). The eye check's head length is the skull without ears, horns, tufts or lobes. The region is within 2r of the root and down the first bone at most 0.6 of its length. Folds and strips count only on faces a review camera sees: ≥ 2 of 17 views, 8 azimuths level and at +35 deg, plus the top.

| measure | gate | meaning |
|---|---|---|
| open / non-manifold edges | 0 (body and region) | holes, slits, white specks |
| knife | exposed concave folds > 90 deg, total length ≤ 1.0 r | a hard crease at the join (the ogre redline: 103 deg, 2.0 r) |
| strip | no seam strip longer than 1.0 r | a creased band of thin faces (width < 0.4 x median face, aspect > 3, on a fold > 30 deg) |
| slit | ≤ 1.5% of region area | a face whose normal hits a non-neighbouring face within 0.1 r |
| poke | 0 | the body crosses itself near the root at rest |
| gaps | none | a piece shell near the root hovering off the body (no contact, gap < r) |
| pinch | warn only | a vertex whose angle sum is off 2 pi by > 2.2 rad |
| shelf | level patch ≤ 0.5 r², or ≤ 0.8 r wide | (hanging arm roots) the troll T-bar: faces outboard of the arm root, within 20 deg of level, seen from the top (added 2026-10-23; zoo/kit_bug_audit.md) |
| clip (S4) | ≤ 1.0% of the chain's area | the chain crosses another chain in any sampled frame of idle/move/attack (not crossing at rest); crossings with the trunk are `root_clip` (warn) |
| eye | visible front ≥ 0.15, 3/4 ≥ 0.35, side ≥ 0.40; diameter 6–24% of head length; round ≥ 0.70; seated (embedded > 0) and proud ≥ 0.5 mm | small, clear, round lens in a socket |
| membrane | area-weighted p10 thickness ≥ max(6 mm, 0.4% of size), no open edges | no paper-thin wings or fins |

The thresholds were calibrated on the current zoo (section 9). Tune `LIMITS` only with before/after evidence on a creature whose flaw the owner named, and record the change here.

## 9. Calibration and validation (2026-10-18, stage-4 GLBs, posed clips included)

| GLB | junctions FAIL / total | eye | membrane | worst numbers |
|---|---|---|---|---|
| ogre `before8` (owner redline state) | 2/4 (both shoulders) | FAIL side 0.35 | flaps PASS | upperarm knife 2.04 r at 103 deg + strip 1.3-1.8 r, flagged on the front of the shoulder join where the red line is |
| ogre current (pass 8c, copy) | 4/4 | FAIL side 0.08 (the side crop confirms: the brow hides the lens) | PASS | shoulder knife 0-0.44 r (fixed); strip 1.13-1.16 r; thigh knife 1.05 r at 104 deg; posed clip: arm.R through thigh.R in attack 3.8-6.7% |
| fox | 7/7 | PASS (0.40/0.67/0.55) | ears PASS | tail vs thighs posed clip 7.1-7.9% in move (the known 5.8% techqa warning); hind root knife 3.8 r at 160 deg; ear root 164 deg folds; foreleg strip 3.1 r |
| dragon | 7/9 (wing roots PASS) | PASS | wing FAIL p10 5.0 mm < 15.3 mm, 68% of area thin | horn/shoulder/hip knife 2.8-4.8 r at 137-157 deg |

- Most quadrupeds fail the knife rule at the hind leg and shoulder roots: 130-178 deg exposed folds where a leg wall meets the flank or haunch (also bear, boar, tiger, crab, stag on a rest-pose sweep). This is HANDOFF step 3's rebuild work, but check the crops before trusting a number.
- The band seat check (straps, belts) is WARN only: the owner-accepted ogre belt reads 40-60% lifted. Calibrate it before gating.
- The seam-strip metric is the noisiest. A strip the crops do not show is noise (rule 6.3).

## 10. Chunky details for game distance (owner 2026-10-21)

The creatures are for GAMES. Every detail must be chunky, visible and understandable at game camera distance. That covers fingers, toes, claws, nails, horns, spines, antennae, tail tips, fin rays, beak tips and teeth. Thin sticks vanish at a 200 px creature, and 3-4 fat toes beat 5 sticks.

**Gate:** `run.py <prog> --stage N --round R --junctions --details` (S3 and S4), or `kit/detail_gate.py <glb> <outdir>`.
- It finds every protrusion: persistent geodesic branches from where a piece is buried in the body, or from the trunk on the body itself.
- It slices each branch's cross-sections perpendicular to its axis and reports per detail: thickness (p10 of the minimum caliper width), length, and length / thickness.
- It writes game-distance thumbnails (192 px, 12 views) and a pass/fail flag render.
- Numbers live in `LIMITS` at the top of the file.

**Rules:**
1. **Thickness:** at least `1.2% H` and at least 3 px at a 256 px creature height (H = creature height).
   - Tier-1 (small) creatures double the % rule: `2.4% H`.
   - Pointed kinds (horn, claw, tooth, beak) are measured over their first 70%; blunt kinds over their first 85%.
2. **Fingers and toes:**
   - visible length at least `4% H`;
   - length / thickness at most 4.5 (tier 1) or 6 (tiers 2-3). Above that a digit is a stick: make it fatter and shorter, not longer.
3. **Fewer, bigger digits.** Tier 1 uses at most 4 fat digits per hand or foot (the gate warns above 4). Merge or drop digits before thinning them to fit.
4. **Plates** (ears, fins, wings, feathers) gate on mean width. Their thickness stays the membrane check's job (section 8).
5. **Detail tiers** (bigger creature = seen bigger = more details), counted as readable feature groups. A group is each piece once (mirrored pairs once), each body appendage kind, the eye, and each body paint region beyond the base colour.

   | tier | creatures | features |
   |---|---|---|
   | 1, small | frog, imp, insects, koi, crab, owl, seahorse, chameleon, spider, snake | 3-6 very chunky, exaggerated details (gate: 3-8) |
   | 2, medium | fox, wolf, goblin, knight, tiger, bear, croc, shark, yeti | 6-12 (gate: 6-16): claws, nails, a few skin/fur/scale bands, teeth, horn rings |
   | 3, large/heavy | hippo, elephant, rhino, troll, ogre, golem, dragon | 12-25 (gate: 12-30): skin folds and wrinkle planes, toenails per toe, warts and bumps, teeth and tusks, ear and eye detail, bristles, plate seams |

   - The method does not change: still chunky, flat colour, geometry steps, extrusions and seated pieces. No noise, no sculpt.
   - **Auto tier** comes from the body's mass size `cbrt(volume)`: under 0.45 m is tier 1, over 1.0 m is tier 3.
   - **Override:** `META = dict(..., detail_tier=N)` in the creature `.py`, when the species' tier differs from its model scale.
6. **Parts library:** call `parts.set_style('game')` once in stage 3, or pass `style='game'` per part.
   - It gives fatter, shorter toes and fingers, 4 toes by default on `paw_bear`, and thicker claws, horns and tusks. The `classic` default keeps old builds unchanged.
   - New chunky-first parts:
     - `foot_webbed`: frog, toad, newt or duck foot with a thick web and fat knobbed toes;
     - `digits_splayed`: fat splayed fingers on the ground.
7. **Review at game size.** Open the gate sheet's 192 px thumbnails at native size. Can you count the toes and see the claws? If a detail only reads in the zoomed crop, it is too small.
8. **Colour borders:** call `smooth_borders(ob, k=k)` (kit/smooth_borders.py) right after every `paint()` of a body with region colours. This is owner-approved 2026-10-21. The borders then follow the form instead of stair-stepping along the quad grid. Re-run the junction probe after it: a relaxed border vertex can thin a strip at a limb root.

`zoo/detail_audit.md` holds the first sweep: 10 of 40 PASS, every tier-3 creature short on detail count, and per-creature lists of missing details vs the sheet.

## 11. Fix loop (adopted 2026-10-22)

Source: `abc/t8/checklist_loop/RESULT.md` (gorilla A/B, free-form vs checklist + champion) and the frozen list `abc/t8/checklist_loop/B_checklist/CHECKLIST.md`. The checklist arm beat free-form review in both judge orders, so every fix pass (an art-director FIX, an owner redline, a rebuild round) now runs this loop instead of free-form critique.

1. **Frozen per-species checklist, written before the first edit.**
   - 10-20 yes/no questions, each tied to one named view (az000 front, az090 side, az180 rear, top, hero/az045, a junction crop, a 192 px thumbnail).
   - Each question says what YES looks like, with the reference sheet as referee, and names the edit target if the answer is NO (the loop, ring, region or param in `<creature>.py`: for example "stage2 H0-H2 j0-j2 y", "ARM_R forearm rings", "stage3 body_rule").
   - The last question is always the gate row: kit gates + junction + detail gate PASS, tris inside META range. A NO there rejects the variant whatever else it scores.
   - The list is frozen for the run. Do not edit a question mid-run; a wrong question is noted and fixed in the next run.
   - Score = number of YES, answered per variant with the image cited. Record the baseline score first.
2. **Every critique is a concrete edit.** A NO is not prose; it becomes a change to the named loop / param in the program. No "improve the head" notes.
3. **Two variants per round.** Each variant is a different edit for the same worst NO(s); build both.
4. **Champion loop.** The current best build is the champion (the baseline at round 0).
   - One Opus seat judges each variant against the champion, pairwise, blind, in **both orders**, with the owner rules and the reference sheet in the prompt.
   - A variant becomes champion only if it wins both orders. A flip (one order each way) is a tie, and a tie goes to the champion.
   - Never judge a variant on its own checklist score alone, and never let the builder be the judge.
5. **Revert regressions.** A variant that fails any gate, drops a YES that the champion had, or moves the S1 lock is reverted, not patched forward. Never revert density to do it (section 3).
6. **At most 5 rounds per stage.** Stop earlier when the checklist is all YES or two rounds in a row end in ties. Residual NOs go to the owner packet.
7. **Open every image** before reporting (a numeric pass is not a visual pass). **Owner taste is final**: the owner's pick or redline beats the judge and the checklist score.
8. Log per round in NOTES.md: checklist score for champion and variants, judge result in both orders, which edit won.

## 12. Standard S4 gates and the game export rule

**S4 gates run on every stage-4 build:**
- `run.py <prog> --stage 4 --round R --junctions --details`: glbcheck, techqa, junction probe, detail gate (sections 6-10).
- `run.py <prog> --rom`: range-of-motion check. Being added by another agent; not implemented in this file's change.
- `run.py <prog> --clips`: clip QA (foot slide, ground penetration, loop continuity). Being added by another agent; not implemented in this file's change.
- `run.py <prog> --pack`: the game pack on the stage-4 GLB (below). Added with this section (`kit/run.py`, runs `kit/game_pack.py`; writes `<creature>/game_pack/`, exit 0 only when the LOD gates and the round-trip pass).

Until `--rom` and `--clips` land, the equivalents are the BRIEF's ROM packet and the clip QA inside `game_pack.py`.

**Rule: game export = game pack.** A creature is exported for a game only as a game pack, never as the bare stage-4 GLB:
- **LOD0-3 at 100 / 50 / 25 / 15 % of LOD0 triangles** (small pieces floored at 24 tris); silhouette IoU of each LOD vs LOD0 over 8 views >= 0.90;
- **hurtboxes**: one capsule per bone (`HB_<bone>`, bone-parented, radius / height in glTF extras);
- **colliders**: `UCX_<name>_00` convex hull of LOD3 and a `CAP_root` capsule proxy;
- **sockets**: mouth, hand_L / hand_R (or claw / paw), back empties, bone-parented;
- **formats**: glTF (Y-up, m) and FBX for Unity (Y-up, m), FBX for Unreal (Z-up, cm);
- **round-trip verified**: every export is re-imported and checked for bone count, bind pose, unit scale, clip lengths, socket names, LOD names and hurtbox count. A pack with any FAIL is not shippable.
