# N/G/O test: the builder's contract (one creature, one fresh build)

The dispatch gives you:

- `<id>`, a neutral folder name;
- `<creature>`;
- `<dir>`, which is `experiments/boxmodel/abc/<id>/<creature>`.

Build the creature from scratch with the staged box-model protocol.
Everything is the same for every build in this test except whether your
`<dir>` contains a `reference/` folder.

## Read

1. `experiments/boxmodel/BRIEF.md`: the protocol, all stages and the kit.
2. Your design brief: `experiments/boxmodel/refs/briefs/<creature>.md`.
3. **If `<dir>/reference/` exists:**
   - Open `sheet.png`, `side.png`, `front.png`, `rear.png` and `top.png`
     before stage 0. That sheet is the design target: match its proportions,
     masses and silhouette.
   - `<dir>/blueprint.json` was traced from it and is your stage-1 silhouette
     and proportion target. Do not replace it. You may add marks.
   - Stage 1 is a quad cage over the sheet's hull (`BRIEF.md` §3): the hull is
     `carve_guide(k)`, a guide to measure and fit to, not the mesh.
   - If the sheet contradicts the brief, the brief wins on identity, palette
     and clips; the sheet wins on shape. Log any conflict in `NOTES.md`.
4. **If there is no `reference/`:** stage 0 is yours. Write
   `<dir>/blueprint.json` as `BRIEF.md` describes.

## Do not read

- anything under `experiments/boxmodel/opus/`, `experiments/boxmodel/fable/`
  or `experiments/boxmodel/judge/`;
- any other folder under `experiments/boxmodel/abc/`;
- `experiments/boxmodel/refs/` beyond your brief. That means no other sheets
  and no reports.

Other creatures' programs would contaminate the test.

## Build

- **Program:** `<dir>/<creature>.py`, importing the kit like this:
  `sys.path.insert(0, <repo>/experiments/boxmodel/kit)`, then
  `from bmkit import *`. Set `META = dict(creature='<creature>',
  model='opus')`.
- **Stages** follow `BRIEF.md`:
  - blueprint;
  - stage 1 (the cage), with at most 14 rounds, then `--lock`;
  - `--blockout`: read the five sheets of `<dir>/blockout/` yourself, then
    stop for the blockout review. Go on only after its PASS;
  - stage 2;
  - stage 3;
  - stage 4.

  Log one diagnosed fix per round in `<dir>/NOTES.md`, and read the round
  sheet every round.
- **Budget:** about 70 tool calls in total. There is no repair pass after
  you finish, so get it right in the build.
- **Code edits:** at most 250 lines per response.
- **Commands:** run them from the repository root.

  ```
  py -3.11 experiments/boxmodel/kit/run.py <dir>/<creature>.py --blueprint
  py -3.11 experiments/boxmodel/kit/run.py <dir>/<creature>.py --stage N --round R [--lock] [--no-orbit]
  py -3.11 experiments/boxmodel/kit/run.py <dir>/<creature>.py --blockout
  ```
- **Finish:**
  1. Run the final stage-4 round **without** `--no-orbit`, so the orbit and
     glbcheck run.
  2. Then run `--review`.
- **Rules:**
  - do not edit anything under `experiments/boxmodel/kit/`; other builders run
    in parallel;
  - do not commit;
  - use your own scratch files under your `<dir>` or
    `out/boxmodel/abc/<id>/<creature>/`, not a shared temp folder.

## Report (at most 10 lines)

- the final stage-4 gate values: hit, float, z-fight, sliver %, flips as % of
  triangles and % of area, drift, lock, glbcheck;
- the triangle count;
- the rounds used per stage;
- stage 1: the IoU per view, quad share, loops per joint and the largest
  proportion difference;
- the three biggest weaknesses you see;
- PASS or FAIL on the gates.
