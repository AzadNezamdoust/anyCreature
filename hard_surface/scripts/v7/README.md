# WF v7 — the modeller's shared toolkit

Subject-parameterized helpers for a modeller building a module against `refs/<s>.png` + `subjects/<s>/turnaround/`.
Run from `hard_surface`. Every command takes `--subject <s>` and/or `--module <m.mjs>`; nothing is hard-coded to
a subject, so do not write your own copies in your subject folder. The gold seats never edit scripts/ (WF v8: a missing
flag or tool goes into the modeller's report and the orchestrator extends the tool between rounds). The eyes stay
`node scripts/v6/view.mjs --subject <s> --module <m.mjs> --out <dir> --zoom`; these tools turn what you see there into
numbers (px -> metres) and try changes cheaply.

## gold.mjs — the orchestrator's only interface (WF v8 WP5; the procedure: D:\Git\anyCreature\hard_surface\.claude\skills\gold-model\SKILL.md)
`out/ref/gold/<s>/state.json` is the source of truth (research/v7/WF-V8-PLAN.md "Shared data"); every state write regenerates
LEDGER.md from it (never edit either by hand). Every subcommand prints the NEXT command; `status` is where a session starts.
  `node scripts/v7/gold.mjs new --subject s --class vehicle --desc-file <paragraph.txt> [--gen gpt|gemini] [--dry]` (a new subject: below)
  `node scripts/v7/gold.mjs status [--subject s] [--json]` · `doctor --subject s` (doctor.mjs + hull.mjs --png, recorded; exit 1 only on a BLOCK)
  `brief --subject s --role modeller | critic --seat opus|sonnet|fable | auditor` (writes brief/, prints the Agent call; auditor: refused
  without the concept prompt `refs/<s>.README.md` `## Full prompt` block unless `--no-prompt`)
  `close --subject s --run <calls>,<min> [--force]` · `merge --subject s --opus <c>,<m> --sonnet <c>,<m> [--fable <c>,<m>]` · `commit --subject s [--dry]`
  `apply-audit --subject s --owner-approved [--owner-note "..."]` · `drift add|rm ... --owner-approved` · `owner --subject s --accept|--review|--extra-round`
  `eyes-check [--subject s] [--update]` · `migrate --subject s --phase owner|setup [--rounds 1=<commit>,...]` (a v7 subject)
  `note --subject s --text "setup ..."` (one ledger line for a step done outside gold.mjs — turnaround.mjs, a semantic fix;
  its role is its first word, e.g. setup / audit / eyes / drift / note)
  `shift --subject s --view v (--sweep a,b,c | --right x | --up x) [--axis right|up] [--pair front,rear] --why "..."` ·
  `override --subject s (--wheels count,axles,equal|per-axle[,lo,hi] [--running tracks|skids] --evidence "..." | --running skids --evidence "..." | --palette-auto | --palette z1,z2 --evidence "..." | --roles r1,r2 --evidence "..." | --tris n --evidence "...") [--note "..."]` ·
  `owner-packet [--subject s]` · `ledger-repair --subject s [--dry]` (2026-09-28: the marathon's hand steps as commands)
- Eye changes at a round boundary (goldlib eyeBoundary): `shift` and `override` run only in setup, in phase model before
  the round's first saved step (briefed + no step: the round start is re-baselined — re-brief the modeller), in phase review
  before any critic brief / critique of the round (the round end + the critics' pages are re-made) and in owner / done
  (the round end + OWNER.md re-made); anywhere else REFUSED. Both re-record the eyes reference (= `eyes-check --update` of
  that subject), set the state's eyes hash and write one ledger line.
- `shift`: view.mjs per candidate on the current model (setup: start.mjs) with the candidate written into the live
  views.json (restored byte for byte after the sweep; `--pair front,rear` gives the other view the mirrored value), the
  agree table of EVERY image (a common-scale side effect on the side shows) with Δ vs BASE (the current value, always a
  candidate); the winner = the highest sum of agree over every image, BASE on a tie within 0.001 (`--right x` / `--up x`
  applies x regardless); applied with a `_shift` evidence note per view; BASE winning = a ledger line, views.json unchanged.
- `override`: subject.json `ruleOverrides` in the WP2 shape (`{value, evidence}`, `_comment` added when absent) —
  `--wheels` (kernel-chain wheelsOverride's value), `--palette z1,z2` (joins an existing paletteZones list; the evidence
  grows), `--palette-auto` (the zones of the chain's `VIOLATION PALETTE_ZONE <part> "zone \"<z>\" on N part(s)"` rows on the
  current model, their parts as the evidence), `--roles r1,r2` (the closed role table + these roles, e.g. turret,gun or
  rotor; joins an existing list), `--tris n` (the subject's V10 triangle budget, an integer 1..12000 = kernel-chain
  TRIS_OVERRIDE_CAP; replaces the class triBudget and a module's meta.triBudget — limits.json unchanged; owner 2026-09-29:
  the detailed Generals units run at 8000); the chain re-run (a value it rejects restores subject.json). At setup before
  the scaffold (no start.mjs) the override is written with only its shape checked ("chain not run").
  Non-wheeled units (2026-09-29): `--running tracks` with `--wheels <road wheels>,<stations>[,equal]` (`0,0` when skirts
  hide them) — two role "track" assemblies stand on y = 0, the road wheels skip the road-car diameter band unless `,lo,hi`
  is given; `--running skids` (no --wheels) — two role "skid" assemblies on y = 0 and no wheel part. Both add their runner
  role to the role table and switch the chassis clearance band off. A helicopter parked on wheels stays `--wheels` (with
  its measured `,lo,hi`). Rotor / track colours are `--palette rotor,track` zones like any other.
- `owner-packet`: OWNER.md per subject (the owner's open items; every PROPOSED drift rect not yet in views.json — the
  critiques' drift:* items, the modeller reports' `drift` lists, the auditor's views.drift.json — deduplicated (IoU >= 0.5
  or one >= 80 % inside the other; the latest round's rect, every source listed) with a ready `gold.mjs drift add ...
  --owner-approved` line; the setup rulings on record: fact:owner-setup / fact:accepted-blocks, and every applied `override` /
  `shift` ledger line — owner rulings pending ratification) + `out/ref/gold/OWNER-BATCH.md`
  (one row per subject; written by a run over every subject). close / merge write the same OWNER.md when the phase becomes owner.
- `commit`: the round's files + the subject's setup files (subject.json, camera / prior, turnaround/views.json, facts.json,
  README.md, every turnaround/*.png, probes.json); the headline = the newest ledger line the commit adds (against the
  committed state.json), the other new lines in the body, a files-only commit named by what changed.
- Briefs state each seat's turn budget (.claude/agents/gold-*.md maxTurns; critics.maxTurns the fallback): "write each item
  to the JSON as you go; stop measuring at 75 % of the budget; finish with done:true" (the modeller: the round's calls).
- The setup stop rule (gold.config.json setupStop; turnaround.mjs below): the auditor brief states it and whether it is spent;
  NEXT re-briefs the auditor instead of "fix the images" when an audit asks to regenerate under a spent rule;
  `apply-audit --accept-blocks audit` accepts the auditor's `acceptBlocks` list (with --owner-note); without such a list the flag
  is refused — naming BLOCK ids is the owner's. A BLOCK nobody accepted leaves the subject in setup with an open owner item
  `setup:doctor-block` (the owner packet shows it) and NEXT names the owner's call, never the gate again.
- LEDGER.md lines are one line each (saveState one-lines every entry; extraLedgerLines compares one-lined text) —
  `ledger-repair` drops the copies the old comparison re-imported (forklift: 23).
- Phases: setup → (apply-audit, doctor not BLOCK) model r1 → (brief, gold-modeller, close) review → (both critics, merge)
  CONTINUE: model r+1 | STOP / OWNER: owner; the cap round's close goes straight to owner (no review after the last
  round) → (owner --accept) done. Round types by round: r1 build, the cap round polish, else list (budgets: gold.config.json).
- brief (modeller): the round-start baseline (`step.mjs --json` → `baseline/rN-start.json`, state.json `baseline`, which
  step.mjs then compares against), `model-r(N-1).mjs` as the start snapshot, the eyes hash; a second brief of an open round
  is a RESUME (no new baseline). brief (critic): the close numbers, the keys / part tables, the facts; never another seat's
  critique (critique/ lines of the ledger are left out); a partial rN-<seat>.json is resumed.
- close refuses on a changed eyes file (the hash recorded at brief: scripts/v6 judge / ortho / view / rules, registered,
  project, subject, check-module, v7 lib / step / steplib, the kernel, the gate, subjects/<s>/** + the concept + the class:
  gold.config.json `eyes`), on model.mjs edits after the last saved step, and on a REVERT vs the round start (--force
  records the override); then `model-rN.mjs`, `baseline/rN-end.json`, the critics' pages (view.mjs --zoom into view/),
  modelHash, the ledger line from the numbers + `report/rN-modeller.json`, eyes.json.
- merge = merge.mjs runMerge (bar and cap from gold.config.json) + state: stateAdd tried / parked, CONFLICTs settled by
  the variants table → decided, the owner packet → open (owner); OWNER.md is written whenever the phase becomes owner.
- eyes-check re-renders every subject's eyes reference (eyes.json: the snapshot, the view.mjs JSON minus `module` and the
  sheet, sha256) and must print `clean`; `--update` records a new reference after an intended eye change at a boundary.
- `--dir <gold dir>` runs on a copy (a replay; keep it 4 levels under hard_surface, e.g. out/replay/gold/<s>, so the
  modules' `../../../../src/kernel` import resolves), `--config <file>` on other numbers. Tests: `node --test scripts/v7/gold.test.mjs`.
### New subject, once (the setup chain; `gold.mjs new` prints it, `gold.mjs status` NEXT names the first unfinished step)
0. `node scripts/v7/gold.mjs new --subject s --class vehicle --desc-file <paragraph.txt> [--style cartoon|generals] [--gen gpt|gemini]` — the paragraph
   names the parts, their colours, a feature on a face the view cannot show as hidden, and the real size ("About 3.2 m long,
   1.2 m wide and 2.2 m tall"). Refuses when refs/<s>.png exists. Writes refs/<s>.png (imagegen.mjs text to image, padded
   to a 1024 square), refs/<s>.README.md (`## Full prompt` = description + the hidden-face rule + the style's STYLE block:
   scripts/v7/styles.json, default `cartoon` = the frozen make-target.mjs STYLE, `generals` = the early-2000s RTS unit look;
   a non-default style is written to subject.json + facts.json `style`, and turnaround.mjs prompts with it; the auditor brief reads it), subjects/<s>/subject.json, turnaround/views.json (vehicle axes, anchor W, families
   PROPOSED from the concept's colour clusters, spanOpen 2), turnaround/facts.json (from the description), prior.json,
   out/ref/gold/<s>/state.json (phase setup). `--dry` generates nothing and writes into a temp root (`--root`, `--concept <png>`).
1. camera: `node scripts/solve-camera.mjs <s> --image refs/<s>.png` (the concepts are orthographic).
2. families: rename views.json `families.table` after the parts, `families.body` = the body colour, replace its `_table`
   note (`node scripts/v7/measure.mjs sample --image refs/<s>.png x,y,w,h`); enclosedFg / per-view shift / scale are the
   doctor's + the auditor's, never guessed.
3. facts: `sides` / `asymmetric` / `faces` (hidden faces) in facts.json (research/v7/TURNAROUND-PROMPT.md); `turnaround.mjs
   prompt --subject <s>` prints the filled sheet prompt. `dims` are the stated size until step 8.
4. provisional frame: `node scripts/v7/hull.mjs --subject <s> --write-frame --from facts` (the facts dims box → layout.measured.json).
5. turnaround: `turnaround.mjs gen --subject <s> --out out/turnaround/<s>` → `status --subject <s> --dir out/turnaround/<s>` →
   `repair … --view <v>` until status meets its targets (the setup stop rule) → `install --subject <s> --dir out/turnaround/<s>`
   (a first set: nothing to `git mv`).
6. per-view colours: `node scripts/v7/turnaround.mjs families --subject <s> --apply`.
7. frame: `node scripts/v7/hull.mjs --subject <s> --write-frame` (the registered hull's extent fitted to the concept bbox →
   `_frame.quadPx`, the shape registered.mjs registration reads).
8. dims + prior: `hull.mjs --subject <s> --aniso` prints the registered dims → facts.json `dims`, prior.json stylisation
   (LoverW, HoverW, wheelDoverH; scripts/v6/README.md "bus card").
9. start: `node scripts/v7/scaffold.mjs --subject <s> --shape sedan|box|bus|pickup|machine` (the class shape below; when two
   fit, both with `--out out/tmp/<s>-<shape>`, keep the better step verdict + agree as out/ref/gold/<s>/start.mjs).
10. `gold.mjs doctor --subject <s>` → `gold.mjs brief --subject <s> --role auditor` → the gold-model skill SETUP 3-5;
   `gold.mjs commit --subject <s>` takes every file above (the concept, its README and layout.measured.json included).

### Items: class weapon on the gold pipeline (owner 2026-10-12)
subject.json `pipeline: "gold"` (`gold.mjs pipeline --subject <s> --set gold`, before round 1 only) makes scripts/subject.mjs
apply classes/weapon.json `gold` over the class: `rules` src/validate/rules/weapon.mjs (no class validators, no layout keys;
frame = muzzle +z, left flank +x, y = 0 lowest point), `grounded: false` (kernel-chain V3 load path + V4 stability footprint
off; V4 min y = 0 kept), `minFeat` 0.008 m (the class floor; limits.json is frozen), weapon `paletteZones`, and
`critics.seats ["opus"]` (gold.mjs brief / NEXT / merge use one seat; merge.mjs `runMerge({seats})`). registered.mjs anchors
a weapon on the +X flank of facts.json dims (as conceptreg.mjs). A direct (`pipeline: "direct"`) subject is unchanged.
Chain from refs/<s>.png + subjects/<s>/turnaround: `gold.mjs pipeline --subject <s> --set gold` → (no `_frame.quadPx`:
`hull.mjs --subject <s> --write-frame`) → `scaffold.mjs --subject <s> --from out/ref/gold/<weapon gold>/model.mjs` →
`gold.mjs doctor` → `brief --role auditor` → owner gate → `apply-audit` → rounds (`brief --role critic --seat opus`,
`merge --opus <c>,<min>`). Tests: scripts/v7/weapon.test.mjs.

## step.mjs — one call per iteration (WF v8 WP3)
Edit the module, then ONE command: build + check-module + the validator chain (only rows new vs the baseline) + floats /
clips + tris vs budget + the concept frame refit (no grid; WARN when the scale moves > 1 % or a shift > 6 px) + raw and
agree IoU per view vs the round baseline + the blob table (top 5 per view) + probes — <= 40 lines, <= 15 s — and ONE
verdict line: `KEEP` or `REVERT: <reasons>` (an agree drop > 0.01 in any view — drift px never count —, a new float or
clip, a new chain row, check-module FAIL, tris over budget; rules in steplib.mjs `stepVerdict`). Exit 0 KEEP, 1 REVERT.
  `node scripts/v7/step.mjs --subject taxi [--module <m.mjs>] [--save [--note "mirror head +0.04"]] [--revert] [--pages side,concept]`
- Module default `out/ref/gold/<s>/model.mjs`; `<dir>` = its folder. Baseline: `--baseline <view or step JSON>` (`none`:
  no comparison), else `<dir>/state.json` `baseline`, else `<dir>/view/model-view.json`; `--json <file>` writes this
  step's record (views, checks, chain rows, blobs, probes) — a round-start baseline with chain rows.
- `--save` (KEEP only): `<dir>/steps/model-vNN.mjs` (next number) + `<dir>/model.mjs`, the refitted frame knobs written in
  (`view.mjs` on the saved module then reproduces the step's numbers), + a line in `<dir>/steps/steps.jsonl`.
  `--revert`: the module (and `model.mjs`) back to the last saved step. `--pages`: only those view.mjs critic pages, into
  `<dir>/steps/pages` (`--out`). Read-only without these flags. (A `view.mjs --out <dir>/view` run moves the default
  baseline to the current state: look through `--pages`.)
- Probes: `subjects/<s>/probes.json` = `[{id, view, axis: "row" | "col", index, from, to, what?}]` (or `{"probes": [...]}`),
  that image's px (view = a turnaround view or `concept`; a row probe runs x = from..to on y = index); each prints
  `probe P1 side row 600 [0..1023] (hub row): ref 112..911 | model 111..911 | d -1/+0` (model - reference edge px, per
  run pair, else the outer edges). `--probes <file>` reads another list (an auditor's proposal).

## view.mjs blob lines — the biggest differences, as numbers (WF v8)
view.mjs ends with the BLOB TABLE (also `blobs` in the view JSON), one line per blob:
`[view] blob <view> missing|extra <px> px <share> % · <where> · part|nearest part <id>`. Per view (orthos + concept) the
5 largest reference-only ("missing") and the 5 largest model-only ("extra") components after a 1 px opening (outline
halos drop out), >= 20 px, outside the drift rects. Orthos: `right a..b up c..d m · at (r, u)` in reference metres along
the view's right / up axes (as `comps`; the JSON adds `bboxPx` for `grid`); concept: `px x a..b y c..d · at (x, y)`.
`part` = the part covering an extra blob; `nearest part` = the model part a missing blob grows into first. With
views.json drift rects view.mjs also prints `[view] agree ...` / `[view] drift ...` (and `WARN drift` over 5 %) after
the IoU line, hatches the rects green, and the tile notes read `IoU .918 · agree .962 · drift 3.1 %`.

## measure.mjs — numbers off the references
- `comps` — each colour family's connected components in the ortho views, bboxes in metres along the view's right/up axes:
  `node scripts/v7/measure.mjs comps --subject school_bus --view side --family glass [--min-px 40] [--top 20]`
- `project` — author-frame point -> concept px (solved camera + the module's frame knobs, or `--frame s,tx,ty`, e.g. a
  variants.mjs row's fitted frame, to score a candidate's key points without writing it):
  `node scripts/v7/measure.mjs project --subject school_bus --module out/ref/gold/school_bus/model.mjs 1.2,0.5,3.1`
- `unproject` — concept px -> the author point on the plane axis = value (`--frame s,tx,ty` as for `project`):
  `node scripts/v7/measure.mjs unproject --subject school_bus --module <m.mjs> 400,500,x,1.22`
- `sample` — median colour (and the subject's family) of rects `x,y,w,h`; `--view concept|side|front|...` or `--image <png>`:
  `node scripts/v7/measure.mjs sample --subject delivery_truck --view side 300,500,10,10`
- `grid` — crop `x0,y0,x1,y1`, nearest upscale, 10/50 px grid with image-px labels; `--module` adds the model's cel
  render of the same window (concept, or the ortho at the judge's sigma) on the right:
  `node scripts/v7/measure.mjs grid --subject delivery_truck --view side 100,300,900,700 --scale 2 --module <m.mjs> --out g.png`
  `--diff` adds a third panel: the filled silhouette diff against the JUDGED reference mask (fgMax / enclosedFg / holes
  as the judge builds it; blue = reference only, red = model only) — shows where IoU is lost, including mask artefacts
  such as an outline's anti-alias halo or an enclosed see-through gap counted as foreground (added round 3, truck)
- `runs` — colour runs along a row/column (raw RGB within `--tol 18`, or `--family` runs of the subject's families):
  `node scripts/v7/measure.mjs runs --subject school_bus --family col 400 100 900`
- `profile` — an ortho view's foreground extents per row (or `--axis col`) in metres, with `--module` the model's
  silhouette on the same line (added by a modeller, round 4):
  `node scripts/v7/measure.mjs profile --subject school_bus --view front --step 0.05 --module <m.mjs>`
  `--view concept` gives the same runs in concept PIXELS (`--from`/`--to`/`--step` in px) against the judged target and
  the model through its frame knobs — silhouette landmarks (tyre bottoms, roof apex, edges) on both images at once
  (added round 4, tractor): `node scripts/v7/measure.mjs profile --subject tractor --view concept --axis col --from 300 --to 500 --step 10 --module <m.mjs>`

Use them when an A/B/C item or a CONFLICT needs a measured number before you edit (gold-modeller loop, step 2): `comps`
for ortho sizes and positions, `unproject`/`project` for what only the concept shows, `grid` + `sample`/`runs` to read
edges and colours exactly.

## frame.mjs — the concept registration only
- Fit frameScale/frameX/frameY on the concept IoU (coarse grid, then coordinate search), geometry fixed; `--write`
  rewrites the three KNOBS values (4 dp), nothing else:
  `node scripts/v7/frame.mjs --subject school_bus --module <m.mjs> [--no-grid] [--start 1,0,0] [--stages 0.02:8,...] [--write]`
- `--sigma [from:to:step]` — per-view ortho IoU vs the uniform model scale sigma (the judge's sigma printed first):
  `node scripts/v7/frame.mjs --subject delivery_truck --module <m.mjs> --sigma`

Use after any change to the body's proportions, before reading the concept IoU as a shape signal; `--sigma` when one
ortho view disagrees with the others on scale.

## variants.mjs — try values without editing
- Build the module with JSON overrides (KNOB names set that knob; other keys go to `buildWith(o)`, objects merged into
  `DEFAULTS`), re-fit the frame, judge; table best score first, BASE (`{}`) always included, ties keep BASE on top:
  `node scripts/v7/variants.mjs --subject school_bus --module <m.mjs> '{"R":0.5}' '{"bf":{"top":0.6}}' [--no-fit] [--grid]`

Rows are numbered `#n` (the n-th variant argument); labels cut to the column are printed in full under the table.
Use when a dimension is uncertain: run 2-5 candidate values in one call, keep the winner only if it also looks better.
- A subject with views.json drift rects adds agree columns `a.<view>` (agree = IoU in a view without rects).
- `--rule concept-first` (lib.mjs `conceptFirst`) decides the table on agree: a variant that drops any ortho agree by
  more than 0.01 vs BASE is disqualified (`DQ #n: ...`); the best concept agree wins; variants within 0.002 of the best
  are tied and the higher minimum ortho agree wins; a remaining tie goes to BASE (then the lowest #n). The last line is
  `WINNER BASE` or `WINNER #n`:
  `node scripts/v7/variants.mjs --subject taxi --module <m.mjs> --rule concept-first '{"W":1.80}' '{"W":1.95}'`

## inspect.mjs — the module's own structure
- `parts` — per-part role, zone, tris, aabb, LUMPS, THIN; tris per part family; total:
  `node scripts/v7/inspect.mjs parts --module <m.mjs> [--filter mirror]`
- `contacts` — contact graph (overlap or face contact within 2 mm) -> FLOATING components, deep overlaps (declared seats
  skipped), non-ground-role parts on the ground:
  `node scripts/v7/inspect.mjs contacts --module <m.mjs> [--deep 0.02] [--ground-roles wheel,tyre]`
- `chain` — the kernel validator chain under the subject's class gate config (pass, tris/budget, violations, advisories):
  `node scripts/v7/inspect.mjs chain --module <m.mjs> --subject school_bus [--layout] [--skip V6,V12]` (`--skip` takes chain step names)

Floats, clips, the triangle budget and the gate in one place (step.mjs runs them on every iteration).

## doctor.mjs, scaffold.mjs — the setup (WF v8 WP3)
- `doctor` — everything about a subject's references and start that must be decided before round 1 (rules: the header
  of doctor.mjs, numbers in steplib.mjs `DOCTOR`): files, check-module + the gate on start.mjs (class-config rows WARN
  until the subject's WP2 overrides exist), registration residuals W / L / H > +-3 % BLOCK naming the view (bbox > 5 %
  WARN), enclosed near-white per image (undecided `enclosedFg` >= 0.5 % BLOCK), body colour vs fgMax, symmetric-axis
  centring (shift candidates), camera.json, drift <= 5 % per image, audit / probes present, the `hull` row (WF v8 WP5:
  hull.mjs on the live set — a view's viewOnly or the concept's conceptOnlyBlob above gold.config.json `setupHull` warn
  3 % / 2.5 % WARN, above block 6 % / 4 % BLOCK), the `aspect` row (the same hull, hull.mjs --aniso: |aspect| H/W or L/W
  above `setupHull.aspect` warn 3 % WARN, above block 6 % BLOCK; hull.mjs aspectRows) and a smoke run of every
  measure / inspect / frame / variants subcommand. Exit 1 on any BLOCK; JSON `out/ref/gold/<s>/doctor.json`:
  `node scripts/v7/doctor.mjs --subject forklift [--module <start.mjs>] [--json <file> | --no-json] [--no-tools]`
  `--drift <views.drift.json> --probes <probes.json>` checks the auditor's proposal (research/v7/AUDITOR.md) instead.
- `scaffold` — a start from the nearest gold of the class shape (sedan -> taxi, box truck -> delivery_truck, cab-over /
  bus body -> school_bus, pickup -> pickup, machine -> tractor): the gold module copied to `out/ref/gold/<s>/start.mjs`
  (`--out <dir>`, `--force` to replace), its L / W / H / wheel-radius KNOBS or DEFAULTS (or `const L`) scaled by the
  target / source registered dims (dropped when the result fails check-module), the palette remapped family by family
  from the subject's `families.table`, the header rewritten, `frame.mjs --write`, then the `step.mjs` verdict:
  `node scripts/v7/scaffold.mjs --subject <s> (--from out/ref/gold/<g>/model.mjs | --shape sedan|box|bus|pickup|machine)`
  The absolute-metre golds (delivery_truck, tractor) have no size knobs: their scaffold keeps the gold's size and is a
  code skeleton more than a shape start — compare its step numbers with a blockout before choosing.

## hull.mjs — do the views describe one object, and is it the concept's? (visual hull)
No module: the turnaround alone (as the eyes register it; `--views-dir <dir>` reads the views.json file names from another
folder and ignores the per-view shift / scale / drift / holes measured on the live images) -> the registration residuals
(the doctor's residual-* rows) + the visual hull H (a voxel grid at `--res` keeps a voxel whose centre is 1-px-dilated
foreground in EVERY view; surface cells refined to <= 1 view px) -> per view H re-projected: IoU, `viewOnly` (foreground the
other views carve away: a cross-view contradiction), `hullOnly`, top 5 viewOnly blobs -> the concept: H splatted through the
registered concept camera, ONLY the frame knobs fitted (fitFrame, concept IoU), `conceptOnly` (concept foreground outside H —
H contains every object consistent with the views: the key contradiction number; `(in blobs)` = its share in >= 20 px blobs
after the 1 px opening, robust to outline halos and the IoU fit's slight shrink of a superset), `hullOnly` (> 0: concavities
no axis view carves), top 5 conceptOnly blobs. ~3-5 s; baseline and reading: research/v7/HULL-BASELINE.md.
  `node scripts/v7/hull.mjs --subject tractor [--views-dir subjects/<s>/turnaround-0-drifted] [--res 0.02] [--aniso] [--json <f>] [--png <f>] [--no-concept]`
- `--write-frame [<file>] [--from hull|facts] [--dry]`: the concept frame (layout.measured.json `_frame.quadPx`; New subject
  steps 4 / 7): the object's camera-plane extent (hull: the refined surface points ± a sub-cell; facts: the dims box) fitted
  to the concept foreground bbox (s = mean of the x / y px per metre, centres matched), the class anchor face placed with it
  (registration() recovers it, rms 0). Equivalent to the hand script the 2026-09-26 subjects were built with (tractor, same
  inputs: s -0.5 %, quad <= 5 px; that script clipped its box at the body span ± 0.1 m, the hull does not).
- `--aniso` (always with `--json`): conceptOnly is one-sided — a hull too big or too tall covers the concept and hides
  there. The per-axis fit scales the SAME hull to the concept: s = {W, H, L}, the views' object over the concept's per author
  axis (H's coordinates divided by them about its bbox centre; frameScale 1, frameX / frameY free), the regularised concept
  IoU (lambda 0.25) maximised by Nelder-Mead on point splats (hull.mjs ANISO; ~2-6 s) -> `aspect` = {HoverW, LoverW, HoverL}
  = sH / sW - 1, sL / sW - 1 (+ = the views draw it taller / longer than the concept) + the aniso concept IoU / conceptOnlyBlob
  (JSON `concept.aniso`, a second concept tile in the PNG). Read it to about +-2 pts: the golds' own views vs their own
  concept renders give -1.7 .. +0.1 % (truth 0), a set stretched 10 % in H gives +10.0 % (synthetic) / +8.5 % (taxi), and an
  oblique camera leaves W against (H, L) weakly determined (research/v7/HULL-BASELINE.md "aspect"). A warm start (`from`:
  the set before a repair) holds sigma (the W scale) — the before -> after aspect change is then the new view's.
`--png`: one row, per view grey agree / blue view-only / red hull-only, then the concept (blue concept-only). Extra flags:
`--max-voxels 6e6`, `--refine <f>`. Tests (synthetic subject in a temp dir): `node --test scripts/v7/hull.test.mjs`.

## turnaround.mjs — generate and repair a subject's turnaround (setup: the gold-model skill, SETUP step 2)
The IMAGEGEN-AB.md decision as one tool: ONE 2 × 2 sheet generated from the concept (Gemini by default, `--gen gpt` the
second generator), normalised like the live sets (normalize-views.mjs `--like subjects/<s>/turnaround`; a first set — no live
side view — `--side-l 800 --canvas 1024`, the live sets' rule; the concept target then comes from views.json alone; stray marks outside
the drawing — labels — re-normalise with `--keep-main 10`, noted), hull.mjs per attempt, then ONE view repaired per call.
Prompt = research/v7/TURNAROUND-PROMPT.md filled from `subjects/<s>/turnaround/facts.json` (parts, colours, measured
L : W : H, the flank of every asymmetric part, per-view face sentences, `dims` for the proportion draft).
  `node scripts/v7/turnaround.mjs gen --subject <s> --out out/turnaround/<s> [--gen gemini|gpt] [--attempts 1] [--add-sheet <png> [--add-provenance <json>]] [--mirror <view,...>]`
  `node scripts/v7/turnaround.mjs repair --subject <s> --dir out/turnaround/<s> --view rear [--gen gemini|gpt] [--draft mirror|proportion]`
  `node scripts/v7/turnaround.mjs status --subject <s> --dir out/turnaround/<s> [--loo] [--blobs] [--mark <label>]`
  `node scripts/v7/turnaround.mjs families --subject <s> [--views-dir <images>] [--apply]` · `rejudge --subject <s> --dir <d> --repair <id> [--again]`
  `node scripts/v7/turnaround.mjs verdict --subject <s> --dir <d> --repair <id> --revert --why "<feature error>" | --keep --ruling "<audit ruling>"` · `fix --subject <s> --dir <d> --view <v> --image <png> --why "..." [--rects "x0,y0,x1,y1;..."]`
- `gen` adds attempts (in parallel, `--concurrency 2`; `--add-sheet` registers an existing raw sheet), prints the attempt
  table and copies the best one to `<dir>/current/`: the lowest conceptOnlyBlob + worst viewOnly (not re-chosen once a
  repair was KEPT, unless `--rechoose`). A side / top that matches the live view better mirrored or flipped is a WARN.
- `repair`: image 1 = the current view, image 2 = a draft — `mirror` (front ↔ rear: the other end view mirrored; keep this
  view's face details, match the mirrored OUTLINE) or `proportion` (the view stretched on the registration's own spans —
  front / rear W / H, side L / H, top W / L — to the CONCEPT's proportions when the set's |aspect| is above the target (the
  registered dims with H / (1 + aspect H/W), L / (1 + aspect L/W)), else to facts `dims`). The new view is normalised onto
  the current set's targets, checked for a COPY of either reference (fg IoU >= 0.985 and mean RGB diff <= 6), and the WHOLE
  set measured (the aniso fit warm-started from the set before). The KEEP rule is set-level (2026-09-28; numbers:
  gold.config.json `setupHull` — defaults, owner ratification pending): a copy never; KEEP when the repaired set meets every
  target; else KEEP only when the set's worst viewOnly drops >= `keep.viewOnlyDrop` (0.3 pts) AND conceptOnlyBlob rises <=
  `keep.conceptOnlyBlobRise` (0.25 pts) AND no |aspect| ratio grows by > `keep.aspectGrow` (0.5 pts) AND no residual BLOCK
  (D, view) appears that the set before did not have; else REVERT (current/ untouched). It prints the set before / after
  lines and the verdict; a KEEP backs current/ up into the repair folder. LOOK at a kept view: a feature error you can see (a
  part on the wrong flank, a missing part) is a REVERT regardless of the numbers — `verdict --repair <id> --revert --why`
  restores the set before (the last kept repair only). Which of front / rear: the one whose viewOnly blobs the concept
  contradicts; when unsure the rear (the concept shows the front face). A whole-set proportion error (|aspect| over the
  target) is out of reach of one-view repairs: the normaliser keeps the side's length (and front / rear follow its height),
  so a stretched view comes back as a residual the rule reverts, or the generator redraws the view as it was — regenerate
  the sheet.
- `rejudge`: an earlier repair's candidate judged again under the current rule against current/ now (refused when current/
  changed since in a view it did not replace; `--again` after a tool fix — both records stay); KEEP applies it.
- `fix`: a view edited outside the tool (a semantic fix: a GPT edit composited into its region only — the procedure of
  refs/garbage_truck.v2.README.md) registered as a repair: same canvas, no normalisation, the set measured before / after,
  kept regardless of the numbers unless it moves the view's foreground by > 0.5 %. `--rects` (the audit's EDIT rects, that
  image's px, half-open like drift rects): a part added / removed — the foreground may move, but any px changed outside the
  rects is a REVERT (turnaround.mjs fixVerdict; added 2026-09-28 for the fire_truck lamp blocks).
- `verdict --keep --ruling "<text>"`: a setup-audit REGENERATE ruling for one view (with its own acceptance numbers, e.g. a
  measured proportion) keeps a candidate the set rule REVERTed because its worst viewOnly / aspect sits elsewhere; refused
  for a copy, a fix / rejudge record, a KEEP, or when current/ changed since in another view (keepOverrideRefusal); the
  set rule's reasons and the ruling are recorded, README.md says so, `verdict --revert` undoes it.
- `families`: per view the foreground colour clusters (>= 1 %) matched to the concept's families with ONE colour offset (a
  view drawn lighter / darker; |offset| <= 20 RGB), per family the share of the view's foreground with the table -> with the
  proposal vs the concept's share, AMBIGUOUS clusters (runner-up family within 12 RGB) and FAR ones (> 40) flagged ->
  `<dir>/families.proposal.json`; `--apply` writes views.json `families.viewTable` (+ `_viewTable`; scripts/v6/README.md):
  every family's colours moved by the offset plus the view's own unambiguous clusters. Once a subject has one, every
  turnaround.mjs measurement re-derives it for the images it measures (attempts, candidates) and `install` writes it for
  the installed set.
- `status`: the current hull + residual + aspect summary, the targets (gold.config.json setupHull: every viewOnly <= 3 %,
  conceptOnlyBlob <= 2.5 %, |aspect| <= 3 % per ratio, no residual BLOCK), the history; `--mark <label>` records the
  measured set in state.json (README.md prints "before the pass <label> -> this set"); `--loo` = per view the concept px the
  hull gains without it at the same frame (supported = concept foreground that view alone carves away: it contradicts the
  concept there).
- `prompt` prints a filled prompt; `install` (after `git mv` of the old set to `turnaround-1-gpt/`, or `--force` over the set
  it installed before) copies current/ into `subjects/<s>/turnaround/`, drops views.json's per-view shift / scale / drift /
  holes (+ `_note`), writes the installed set's viewTable (when the subject has one), rebuilds `sheet.png` (concept + 4
  views, 480 px tiles) and writes README.md (every repair with its rule and verdict, the marks, `--note "<paragraph>"`
  kept in state.json); `sheet` only rebuilds sheet.png.
- The setup STOP RULE (gold.config.json `setupStop` {sets 3, view 3}; goldlib setupStopOf): after 3 failed whole-set
  regenerations (attempts that errored or missed a target) or 3 failed repairs of one view (REVERT / FAILED repair-* records;
  rejudge / fix records do not count), `gen` / that view's `repair` REFUSE — `--owner-override "<the owner's words>"`
  records an explicit exception (state.json stopOverrides) — and `status` prints the rule's state; the setup audit then
  rules target-wins: READY with drift rects, decided facts and audit.json `acceptBlocks` instead of REGENERATE.
Work folder: `state.json`, `attempt-<k>/` (raw sheet + provenance, views, normalize.json, hull.json / .png), `current/`,
`repair-<n>-<view>-<gen>-<draft>/` (draft, prompt, raw + provenance, candidate set, hull). Then the semantic audit
(research/v7/AUDITOR.md task 0, a separate Opus seat) and the owner setup gate. Tests: `node --test scripts/v7/turnaround.test.mjs`.

## imagegen.mjs — one image from GPT or Gemini (generation only)
`node scripts/v7/imagegen.mjs --gen gemini|gpt [--ref <png> ...] --prompt-file <txt> --out <png> [--aspect 1:1|16:9|...]` (no
`--ref`: text to image — a concept, `gold.mjs new`)
(also `generateImage()`). Gemini: `agy --print` (gemini-3.8-flash-high) in a clean temp dir holding only copies of the refs;
ONE generate_image call with ImagePaths = the refs and the prompt verbatim, the agent copies the JPEG it wrote and replies
with the path; the original JPEG is kept (`<out>.orig.jpg`) and converted to the PNG by sharp. GPT: `codex exec -m
gpt-6-astra` with the refs as `-i`, the instruction on stdin (closed); the image_gen PNG from `$CODEX_HOME/generated_images`.
Both: a timeout, ONE retry on a transport failure only (never for what the image shows), `<out base>.provenance.json`
(CLI + version, agent model, C2PA, argv + the instruction verbatim, prompt / ref / output sha256, wall time, the agent's
tool calls: generate_image count, refs passed, prompt verbatim). Tests: `node --test scripts/v7/imagegen.test.mjs`.

## merge.mjs — the round's worksheet from the two critiques (WF v8 WP4)
Critics write `critique/rN-<seat>.json` per `critique.schema.json` (<= 10 items; keys `knob:` / `def:` / `part:<family>.<param>`
/ `drift:<view>` from the packet's tables; `at` = {image, rect in that image's own px, claim}; rewrite after every item,
`done:true` at the end). The merge classifies every item and prints the STOP line first; nobody writes a merge by hand:
`node scripts/v7/merge.mjs --subject taxi --round 2 [--dir out/ref/gold/taxi] [--module <dir>/model.mjs] [--cap 3] [--no-variants]`
-> `critique/rN-merged.md` + `.json` (`runMerge()` for gold.mjs). Rules in order (header of merge.mjs): schema (a missing
file / `done:false` blocks, exit 2) · evidence (the model's raster of at.image vs the judged reference inside the rect:
ref-only / model-only >= 10 % of its px, colour = another family AND the reference shows want's / the model now's family,
edge >= 1 px; fail -> REJECTED; an edge / colour claim whose differing px are < 10 % of the rect AND < `edgeMinPx` 250 px is
WEAK: unverified, a MAJOR merges as MINOR — the marathon's r1 / r2 replayed: 1 of 111 rows changes, garbage_truck r1 B6
B -> C, 190 px of 4888) · drift (at >= 50 % inside a rect whose `decides` != basis -> REJECTED-DRIFT) · DECIDED ·
TRIED / PARKED (state.json, K = 2; `dir` = + / - / add / remove / =<want>) · pairing (exact key, then a part family named
in a knob's comment on the same axis, then pos ~ size of one part family on one axis) into A / CONFLICT / X / B / C (a
MAJOR without a verified `at` merges as MINOR) ·
variants (A / B / CONFLICT with a knob / def key: `variants.mjs --rule concept-first` in-process vs one BASE; CONFLICTs
settled by the WINNER; the applied row losing > 0.01 agree on its basis view -> VERIFY VISUALLY) · STOP / OWNER / CONTINUE.
Display only: actionable items whose `at` rects share an image and overlap or have centres within 20 px get a link id
(L1 ...) and sit next to each other, "same area — do together"; classes never change (orchestrator 2026-09-27).
State additions (TRIED / PARKED lines for state.json) and the owner packet ride in the JSON. `--validate <file>` checks
a critique; `--keys --module <m.mjs>` prints the key table (values, comments, axis). A hand-written `rN-merged.md` is never
replaced without `--force`. Tests: `node --test test/wf-v8-merge.test.js`.

Tests for the pure helpers: `node --test scripts/v7/lib.test.mjs scripts/v7/steplib.test.mjs` (+ `scripts/v7/hull.test.mjs`,
`scripts/v7/turnaround.test.mjs`, `scripts/v7/imagegen.test.mjs`, `scripts/v7/gold.test.mjs`); all of them: `node --test scripts/v7/*.test.mjs`.

## WF v10 (2026-10-04) — the direct pipeline and the weapon class (the one page: `WORKFLOW-V10.md`)
- `node scripts/v7/gold.mjs hs [--subject s] [--json]` — the HS stage of every subject from the files in
  `out/blender-hs/<s>/` (read-only): a gold subject wait → build → review → polish → function → owner (WF v9); a
  `pipeline: "direct"` subject setup → build → review → polish → function → owner, each with its NEXT.
- `gold.mjs new --class weapon --style fps` (classes/weapon.json, classes/weapon.md; newsubject.mjs DIRECT_CLASSES): writes
  subject.json with `"pipeline": "direct"` + `ruleOverrides.tris` 8000, `camera.json` = the fixed style isometric (30 / 45),
  views.json with `anchor {dim: "L"}` and ONE family (`body` = every concept colour cluster), facts.json, prior.json — and
  NO gold state (`out/ref/gold/<s>` is not created; `status` / `doctor` / `brief` / `commit` do not apply). It prints the
  direct chain: facts → `hull.mjs --write-frame --from facts` → `turnaround.mjs gen … --gen gpt` → status / repair →
  install → `solve-camera-hull.mjs` → `hull.mjs --write-frame` → `scripts/hs/dump_frame.mjs` + `dump_concept_cam.mjs` →
  `gold.mjs hs`. Descriptions of the ten weapons: `subjects/_weapons/<id>.txt`.
- Style `fps` (styles.json, a new key): stylised first-person-shooter weapon, gunmetal / black polymer / one accent.
- Generators (owner 2026-10-04 "stop trying to use gemini"): `gpt` is the default of `gold.mjs new`, `turnaround.mjs gen` /
  `repair` and `imagegen.mjs` (`--gen` may be omitted); `--gen gemini` is REFUSED with the ruling's text unless
  `--allow-gemini` is passed (imagegen.mjs `geminiRefusal`, `generateImage({allowGemini})`). The sections above that say
  "Gemini by default" describe the state before this ruling.
- `conceptreg.mjs` — `conceptRegistration(subject)`: project.mjs `subjectRegistration` for a vehicle / building; for a
  direct class the same shape built from `camera.json` + `layout.measured.json _frame.fit` (registered.mjs has no anchor
  for a third class and is an eyes file: it is not edited). hull.mjs and turnaround.mjs read the concept through it.
- `solve-camera-hull.mjs --subject s [--dry]` — a direct subject's concept camera after install: (theta, phi) of an
  orthographic camera without roll, best silhouette IoU of the views' visual hull against the concept (5° grid → 1° →
  0.25°); writes camera.json with the fixed isometric's IoU for comparison (assault_rifle: .426 → .743 at 27° / 60.5°).
- `hull.mjs`: a small object at many px per metre (a weapon at ~900 px/m) gets 3-view-px cells instead of the 0.02 m
  default that exceeded the refine cap (a note line says so; a vehicle's hull is unchanged); `--write-frame` for a direct
  class also fits the frame similarity on the hull's concept IoU and stores `_frame.fit {s, ox, oy, refined}`.
- Tests that are pure (safe on a live tree): `node --test scripts/v7/newsubject.test.mjs scripts/v7/imagegen.test.mjs
  scripts/v7/turnaround.test.mjs scripts/v7/normalize-views.test.mjs scripts/v7/hull.test.mjs`. NOT `gold.test.mjs`.
