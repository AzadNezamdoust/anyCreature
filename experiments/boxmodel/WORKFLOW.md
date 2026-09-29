# Box-model creature workflow: medium and high effort

This is how to produce a stylised low-poly game creature that reads as
hand-made. It is proven on 10 creatures across two batches; the numbers are
in `RESULTS.md`.

The parts it uses:

- the protocol: `BRIEF.md`;
- the kit: `kit/` (`bmkit.py`, `techqa.py`, `run.py`, `render_glb.py`);
- the art-director contract: `ART_DIRECTOR.md`;
- the repair-pass contract for builders: `REPAIR.md`;
- the agents in `.claude/agents/`: `boxmodel-builder` (Opus 5.5, 200 turns)
  and `art-director` (Fable 5.1, read-only).

## Roles

| role | model | job |
|---|---|---|
| orchestrator | the main session | picks the tier, writes the target and the accepted identity words, dispatches, reconciles reviews, owns the gates |
| builder | `boxmodel-builder` (Opus 5.5) | one creature: blueprint → stage 1 → lock → 2 → 3 → 4, one diagnosed fix per round |
| art director | `art-director` (Fable 5.1); plus an Opus 5.5 seat at high effort | reviews the packet (`run.py --review`) and returns ranked, protocol-actionable notes plus a verdict |
| blind reader | Fable 5.1, no context | identity from silhouettes (`judge/prepare.py` sheets), scored by `harness/identity.py` |

## The pipeline

1. **Brief.** Write the design target: size, silhouette cue, head, limbs,
   pieces, a 5–8 colour palette, and the three clips. Write the accepted
   identity words to `judge/<creature>.brief.md` **before any geometry
   exists.**
2. **Reference sheet** (the default since 2026-09-28).
   - `refs/gen_refs.py --provider gpt` makes a 2 × 2 turnaround (side,
     front, rear, top) with Codex on the owner's subscription.
   - `refs/select_sheets.py` then fixes the view directions and fits the
     views into one orthographic set. It also stretches the side and plan
     views to the brief's length.
   - `kit/refs.py` traces `blueprint.json` and `reference/`, and the builder
     follows `refs/BUILD.md`.
   - Details: `refs/SHEETS.md`.
3. **Build.** The builder runs `BRIEF.md` §3/§5. The gates are in the kit and
   cannot be skipped:
   - stage 1 is one closed shell, frozen after the lock;
   - stage 2 changes topology only through logged ops, with IoU > 0.9;
   - stage 3 never touches the base, 4–8 colours;
   - stage 4 has idle/move/attack, full weights and passes glbcheck;
   - **tech QA** from stage 2 on:
     - pinched folds are turned outward automatically;
     - gated to zero: pass-through, floating pieces, z-fighting (a small
       allowance);
     - gated by share: slivers ≤ 2%, posed fold-overs ≤ 0.5% of triangles
       and of area;
     - gated to zero in poses: drift (a piece leaving the body);
     - posed checks run on every keyed frame of each clip, plus 20/40/60/80%;
     - warned: open plates, and posed clipping (pink: a part passing through
       another in a pose but not at rest). Clipping has no limit until the
       owner sets one.
4. **Packet.** `run.py <prog> --review` writes `review/`:
   - beauty in four views;
   - close-ups (head, a front limb, a hind limb, the largest piece), colour
     next to wire;
   - the tech heatmap;
   - posed wires;
   - `techqa.json`;
   - with a `reference/` (settings G/O), `5_reference.jpg`: each reference
     view next to the model's beauty render from the matching angle.
5. **Art direction.** The art director reviews the packet against
   `ART_DIRECTOR.md`: SHIP, FIX or REBUILD, with at most 8 ranked issues and
   a keep list.
6. **Repair.**
   - The orchestrator (or a Fable seat) writes the reconciled notes: a must-fix list in order,
     a should-fix list, the dropped items with their reasons, and both
     reviews verbatim. They go to `review/ad_notes_r<k>.md`.
   - One builder per creature follows `REPAIR.md`. It runs a baseline on the
     current kit first, fixes the list in order, keeps the keep lists, and
     leaves a fresh packet.
   - Stage 1 is unlocked only for a blocker that stages 2–4 cannot fix, and
     the unlock is logged.
   - After the repair, a blind review compares each build before and after,
     with the order shuffled.
7. **Final.**
   - Tech QA passes.
   - The blind identity read passes.
   - The art director's verdict is SHIP.
   - Otherwise the residual goes to the owner in one compressed packet.

## Tiers

| | **medium** (a creature a day, many creatures) | **high** (hero creatures, owner-reviewed) |
|---|---|---|
| reference | GPT 2 × 2 sheet, fitted to the brief (step 2) | GPT 2 × 2 sheet, fitted to the brief (step 2) |
| builder | 1 × `boxmodel-builder` | 1 × `boxmodel-builder` |
| stage-1 rounds | ≤ 10 | ≤ 14 |
| art-director review | 1 × Fable 5.1, after stage 4 | Fable 5.1 **and** Opus 5.5 in parallel, blind, reconciled by the orchestrator: at the stage-1 lock (silhouette only) and after stage 4 |
| repair rounds after review | K = 1, then a blind before/after check | K = 2, with a blind before/after re-review after each (GPT sheet + K = 2 is not yet measured) |
| identity read | silhouettes, 1 Fable seat | silhouettes + colour, 1 Fable seat each |
| made-by-a-person test | — | pairwise vs a CC0 hand-made reference, both orders, Fable + Opus |
| owner gate | the gallery sheet | the gallery sheet + close-ups + the residual packet |

Reconciling two art directors:

- **Both flag it:** a must-fix.
- **One flags a blocker:** the orchestrator looks at the cited view and keeps
  it or drops it, with a one-line reason.
- **Majors from one reviewer:** kept unless the other reviewer's keep list
  contradicts them.

Verdict and score: the verdict is the stricter of the two; the score is the
mean.

## Commands

```
py -3.11 experiments/boxmodel/refs/gen_refs.py --provider gpt --creatures a,b [--attempt N] [--ref concept.png]
py -3.11 experiments/boxmodel/refs/select_sheets.py                 # after the direction audit (refs/audit.json) -> chosen.json, fitted_<n>.png
py -3.11 experiments/boxmodel/kit/refs.py <sheet.png> <creature_dir> --height <m> [--length <m>]   # settings G/O: 2 x 2 (side|front / rear|top) or 1 x 4 sheet -> reference/ + traced blueprint.json
py -3.11 experiments/boxmodel/kit/run.py <prog> --blueprint
py -3.11 experiments/boxmodel/kit/run.py <prog> --stage N --round R [--lock] [--no-orbit]
py -3.11 experiments/boxmodel/kit/run.py <prog> --review
py -3.11 experiments/boxmodel/kit/run.py <prog> --compare
py -3.11 experiments/boxmodel/judge/prepare.py --creatures a,b --blind <dir> --key <file>
py -3.11 experiments/boxmodel/kit/regress.py <tag> [path filter]    # after any kit change: every locked build to stage 4, no renders; diff two tags
```

## Budgets seen so far (Opus 5.5 builders, 2026-09)

- A full build takes about 11–14 stage-1 rounds.
- A repair pass takes about 10–20 rounds.
- One art-director seat can review five creatures in one pass.

## Lessons from the first art-direction loop (2026-09-27)

- **One repair pass moved the mean art-director score from 5.7 to 6.6**, and
  it cleared every round-1 blocker. Round 2 also ran on a stricter kit, so
  expect a second repair pass (K = 2) to be needed at high effort for a SHIP
  verdict.
- **What the reviewers disagree on:**
  - The Opus 5.5 art director is consistently harsher by about 1 point.
  - They disagreed on a few visual facts, such as whether the goblin's skull
    reads as domed or the crab's teeth are visible. The orchestrator settles
    these by looking at the cited view.
- **Promote review findings into gates.** When both reviewers call something
  major on several creatures, that is a missing gate:
  - area-weighted fold-overs;
  - posed drift;
  - same-facing z-fight.
  The kit grows from the reviews.
- **The IoU > 0.9 floor on stage 2** blocks some legitimate secondary work,
  such as widening the wolf's legs (az000 dropped to 0.869). Its
  owner-ratified value stays until the owner changes it. When a note needs
  more, the builder logs it as partly fixed; stage 1 is not unlocked for it.
- **Turn budgets.** Builders on the 60-turn `opus-worker` cap needed resumes
  in about half the passes. Use `boxmodel-builder` (200 turns) in new
  sessions.
- **Output limit.** A Fable builder failed once on the 64k output-token limit
  by writing a whole program in one response. Tell every builder to write
  programs in ≤ 250-line pieces.
- **Rebuilds.** A creature that fails identity is rebuilt from a new stage 1
  with the silhouette cue in the base: the raven-wyvern needed an S-neck, a
  reptile tail and wing forelimbs. Pieces cannot rescue identity.
- **Parallel rebuilds pay off at high effort.** Fable 5.1 and Opus 5.5 each
  rebuilt the raven-wyvern, and both passed identity. The two art directors
  then saw the packets as "candidate A" and "candidate B" and picked the same
  one by a clear margin, 6 against 4. A REBUILD verdict at high effort is
  worth two builders and one blind A/B review.
- **Save every review the moment it arrives.** Write it to `judge/results/`
  as JSON. The round-2 reviews reached only the chat, so the K=2 notes had to
  be recovered from the session transcript.
- **Blind means neutral paths too.** A reader sees the file path. Sheets
  saved in a folder named after the creature primed the read, and it had to
  be rerun. Blind material goes in a neutral folder under neutral names
  (`judge/prepare.py --blind` does this; ad-hoc scripts must too).
- **A second repair pass (K=2) is where verdicts turn to SHIP.** Before it,
  no creature had SHIP from both reviewers; after it, five of ten did. The
  mean score barely moved (6.56 to 6.67). What is left needs the base mesh or
  the owner's IoU floor, not more passes.
- **Builders over-claim.** On two creatures a builder reported a fix as done
  that both reviewers saw as not done. They had checked the rest pose; the
  packet shows the idle pose. `REPAIR.md` now makes the builder check each
  item in its own `--review` packet. The reviewers' `must_fix_check`, not the
  builder's report, is the record.
- **Give the builder a GPT turnaround sheet (N/G/O test, 2026-09-28).** A
  blind test on 11 creatures × 3 settings found:
  - **GPT sheet:** 12 of 22 first places, mean 6.07, identity 11/11;
  - **no image:** 5 first places, mean 5.64, identity 10/11;
  - **Gemini sheet:** 5 first places, mean 5.55.

  The owner confirmed it by eye: GPT is better on 9 of 11, all but the boar and
  the bear. Default for the medium and high tiers: generate a 2 × 2 sheet with
  `refs/gen_refs.py --provider gpt`, then `select_sheets.py` (orientation fix
  and fit), then `kit/refs.py`. Build under `refs/BUILD.md`. The
  proportion drift (sheets scaled by height came out 15–45% short) is fixed:
  the fit now stretches to the brief's length.
- **One repair pass on the GPT builds added a full point (2026-09-28).**
  - Reconciled notes plus a K=1 repair took the mean from 5.36 to 6.36. The
    repaired build was preferred in 20 of 22 blind calls.
  - Clipping dropped below 1% on every build that had been above it.
  - One build lost the blind vote (the character), partly to a render
    artifact. The wire overlay's even offset drew needle spikes at sharp
    corners such as thumb tips. The model has no such triangles, and the
    overlay is fixed. The other reason was a heavier eye ring.
- **Before you blame the model for a spike, check the renderer.** This is
  the second overlay artifact reviewers read as geometry, after the
  per-object outline. Find the triangle in the exported GLB first.
- **Repair loops plateau around 6.5-7.5.** After three passes the five
  hardest creatures moved only from 6.2 to 6.5. Anatomy the base got wrong
  (hands, paws, a tail) resists notes. The next lever is the target: a
  multi-view reference before stage 1 (`refs/PLAN.md`).
- **Put an independent check between the builder and the review.** Builders
  said "done" on items both reviewers saw as not done, in three passes out of
  three. A cheap Fable seat that checks only the must-fix items against the
  new packet, before the builder may report, would catch it.
- **Never let a set of names set an order.** Blender's Python randomises
  string hashes per process. A clip order taken from a set made the
  fold-over gate read 8 or 16 on identical input. Each clip is now also
  sampled alone from rest.
- **Renderer artifacts become review notes.** Workbench's per-object outline
  looked like a glued-on edge, and a shared heatmap colour made drift look
  like floating. When two reviewers flag the same odd look on many
  creatures, check the renderer before the model.
- **Sample poses where the animator put them.** Posed QA read each clip at
  20/40/60/80% only. Blinks keyed on frames 40-44 were never checked, and
  one builder noted it without being able to fix the gate. It now samples
  every keyed frame. On the next sweep, 8 of 46 builds failed drift or
  fold-overs that had always been there: the blinks and the character's
  arm drop from the T-pose.
- **Regress the kit on every build before shipping a kit change.**
  `BMK_NORENDER=1` runs gates and QA without pictures, so all 46 builds
  run to stage 4 in one short sweep. It showed that the extrude and normal fixes left every
  stage-1 lock intact.
- **Every heatmap flag has its own legend entry.** Drift was painted in the
  floating blue, and both reviewers misreported it as floating. Drift is
  brown now.
