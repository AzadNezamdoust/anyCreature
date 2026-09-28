# Repair pass: the builder's contract

A repair pass follows an art-direction review (`WORKFLOW.md` step 5). One
builder repairs one creature.

The orchestrator's dispatch gives you:

- the creature folder `<dir>`;
- the program `<prog>`;
- the reconciled notes `<notes>`, which hold the must-fix list in order, the
  should-fix list, the dropped items, and both reviews verbatim with their keep
  lists;
- the first round number `R0`.

Your job: fix the must-fix list inside the protocol, keep what works, and
leave a fresh review packet.

## Read first

Read only what you need, in this order:

1. `experiments/boxmodel/BRIEF.md`: the protocol. §3 and §5 cover the stages
   and verbs, §7 the lessons, §8 the tech QA and its gates.
2. `<notes>`: your list.
3. `<dir>/review/ad_notes.md`, if it is not `<notes>`: the earlier keep list.
4. `<dir>/NOTES.md`: what has been done so far.
5. The program `<prog>`.
6. The current packet, `<dir>/review/`: `1_beauty.jpg`, `2_closeups.jpg`,
   `3_tech.jpg`, `4_posed.jpg`. Look at it before you change anything.

## Rules

- **Stage 1 is locked.** Do not change it, unless the owner authorised an
  unlock for named items (see "Unlocking stage 1" below). If the lock assertion fails although you did not touch stage 1:
  - Run once more. Older locks can have a non-deterministic vertex order.
  - If it fails again, stop and report it.
  - Never re-lock.
- **Stage 2** allows:
  - vertex moves, `flatten`, and loop slides;
  - logged loops, partial loops, insets and chamfers, inside `topo` blocks.

  The silhouette IoU against stage 1 must stay above 0.9 in every view. That
  number is owner-ratified. If a note needs more, do what fits and log the
  note as partly done.
- **Stage 3** never touches the base, and uses 4–8 colours.
- **Stage 4** changes are made with:
  - `bind(piece, rig, bone=..., body=...)`: `body=` makes a piece follow the
    skin under it, which is the cure for drift;
  - armature rolls;
  - clip keys.
- **The kit gates every tech-QA check at stage 4.** These run on the
  heatmap:

  | check | heatmap colour | limit |
  |---|---|---|
  | a part passing through twice | magenta | 0 |
  | a floating piece | blue | 0 |
  | a piece that drifts off the body in a pose | brown | 0 |
  | z-fight | green | small allowance |
  | slivers | yellow | ≤ 2% |
  | posed fold-overs | purple | ≤ 0.5% of triangles **and** ≤ 0.5% of surface area |
  | clipping through the body in a pose | pink | warning only: fix what the review packet shows |

  A creature last run on an older kit can fail drift or fold-overs without
  any change. Since 2026-09-28 posed QA checks every keyed frame, so a
  blink or a snap between the old 20/40/60/80% samples is now seen.
- **The kit is shared.** Other builders run in parallel. Do not edit anything
  under `experiments/boxmodel/kit/`, and do not touch another creature's
  folder. If the kit blocks you, stop that item and report the exact failing
  line.
- **One diagnosed fix per round:** critique, diagnosis, fix, result.
  - Log each round in `<dir>/NOTES.md` under a new heading for this pass.
  - Read the round's sheet image every round.
- **Keep code edits small:** at most 250 lines per response. A whole-program
  rewrite in one response hits the output limit.

## Unlocking stage 1 (only when the owner authorised it for named items)

Some notes need the base itself, and stages 2–4 cannot reach them: leg
length, a hand's knuckle row, a pole of spokes. If the dispatch or the notes
say the owner authorised an unlock for named items, follow these steps:

1. Rename `<dir>/stage1_lock.json` to `<dir>/stage1_lock.pre_unlock.json`.
   Do not delete it: it is the record of the old base.
2. Change `stage1()` for the named items only. Keep the identity cue and the
   silhouette everywhere else.
3. Run `--stage 1 --round R --lock`. The stage-1 gates must pass: one
   closed shell, no self-intersection, the triangle budget, mirrored. The
   new lock gets the canonical vertex order.
4. Re-run stage 2, then 3, then 4. Your stage-2 code must still work on the
   new base; it is measured against the new stage 1 (IoU > 0.9).
5. In `NOTES.md`, log what changed in stage 1 and which note needed it.

## Commands

Run from the repository root. Python is `py -3.11`.

1. **Baseline:**

   ```
   py -3.11 experiments/boxmodel/kit/run.py <prog> --stage 4 --round R0 --no-orbit
   ```

   Every FAIL it prints becomes must-fix item 0.
2. **Rounds:** run `--stage N --round R --no-orbit` with R = R0+1, R0+2, and
   so on. N is the stage you changed. The gates that matter run at stage 4, so
   run stage 4 as soon as a stage-2 or stage-3 change looks right.
3. **Final:**
   1. `--stage 4 --round <next>`, **without** `--no-orbit`, so the orbit and
      glbcheck run.
   2. `--review`, which rebuilds `review/`.
   3. `--compare`, which rebuilds `side_by_side.jpg`.

**Before you mark an item done,** run `--review` and check it in the packet
the art director will see. There, the beauty views are posed at the idle
clip's first frame, not the rest pose. Hanging pieces and folds that looked
right at rest have failed there. The reviewers check every item against the
packet, not against your report.

## Done when

- Every gate passes on the final stage-4 run.
- Each must-fix item is done, or honestly marked partly done or not done,
  with the reason.
- The review packet has been regenerated.

## Final report

At most 15 lines, and no transcript:

- the final stage-4 values:
  - hit, float and z-fight;
  - sliver %;
  - flips, as a % of triangles and a % of area;
  - drift;
  - the lock result;
  - the minimum stage-2 IoU;
  - glbcheck;
- each must-fix item: done, partly done or not done, with a one-line reason;
- the should-fix items you did;
- the triangle count and the rounds used;
- any kit problem you hit.
