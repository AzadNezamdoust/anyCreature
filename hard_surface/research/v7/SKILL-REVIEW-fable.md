# gold-model skill — blind usability review (Fable 5.1 seat, 2026-09-28; new subject "cement_mixer", medium orchestrator)

VERDICT: FIX FIRST — the ROUNDS / packet / marathon-round loop walks cleanly (every command and flag in the skill exists in
`gold.mjs --help`; agent names match `.claude/agents/gold-*.md` and gold.config.json `agents`; NEXT lines are typeable), but
SETUP for a subject that has never had a turnaround cannot be completed from the skill + README: items 1–4 stop it or make
the orchestrator self-ratify.

1. BLOCKER · SETUP 2 (`turnaround.mjs gen`) · a first set cannot be generated. turnaround.mjs:679 always passes
   `--like subjects/<s>/turnaround`; normalize-views.mjs `liveSide` (416–428) reads that folder's side image with readRGB and
   throws when it is absent (a new subject has none; `--add-sheet` and `repair` take the same path). The README's "`git mv`
   the old set" assumes a live set. Fix (turnaround.mjs:679): build `base` with `--like` only when
   `fs.existsSync(path.join(ROOT,"subjects",subject,"turnaround",<views.json side file ?? "side.png"))`, else
   `"--side-l","800","--canvas","1024"`; note it in scripts/v7/README.md "turnaround.mjs" ("first set: no `--like`, L 800").
2. BLOCKER · SETUP 2 / 3 · an undocumented required file. registered.mjs:92–94 throws `has no _frame.quadPx` unless
   `subject.json paths.layoutMeasured` names a `layout.measured.json` with `_frame.quadPx` (doctor, hull, frame, step, view
   all go through registration()). Neither SKILL.md:19 nor README.md:70–74 lists it, and no tool writes it for a generic
   vehicle (measure-vehicle.mjs only for its own classes; forklift's was hand-built from the hull bbox). Fix: README.md:70
   + SKILL.md:19 add "`layout.measured.json` (`paths.layoutMeasured`) with `_frame.quadPx` — copy subjects/forklift/
   layout.measured.json's shape (the registered hull's +X quad fitted to the concept bbox)"; better, a `hull.mjs --write-frame`.
3. BLOCKER · SETUP 1 (concept) · no command, and the auditor's semantic check silently loses its input. SKILL.md:14 says
   "GPT, the frozen style" only; make-target.mjs is Antigravity/Gemini (`--model gemini-3.1-pro-high`), imagegen.mjs `--gen
   gpt` needs a prompt file the orchestrator must compose. gold.mjs:471–475 reads the prompt from `refs/<s>.README.md` and
   passes `prompt: null` when it is missing — the auditor's task 0 then runs without the prompt, no warning. Fix SKILL.md:14:
   "`node scripts/v7/imagegen.mjs --gen gpt --prompt-file <scratch>/concept.txt --out refs/<s>.png` (prompt = the parts
   paragraph + stated real size + `STYLE` of scripts/make-target.mjs verbatim), pad to a 1024 square, then write
   `refs/<s>.README.md` in the shape of refs/forklift.README.md with a `## Full prompt` fenced block — the auditor brief reads
   exactly that file." gold.mjs:475: `refuse` (or a printed WARN) when the README is missing.
4. BLOCKER · MARATHON apply-audit line (SKILL.md:47–48) · self-ratification trap. `--accept-blocks audit` REFUSES when
   audit.json has no `acceptBlocks` (gold.mjs:774) — the normal case (the auditor lists it only under a spent stop rule) —
   and the REFUSED text says "name the doctor BLOCK row ids": a medium orchestrator then types `--accept-blocks residual-W`
   itself = an owner ruling by accident. Fix SKILL.md:48: "`--accept-blocks audit` only when audit.json has an acceptBlocks
   list, else omit the flag; never name ids yourself — a standing BLOCK the auditor did not list parks the subject in setup
   and goes to the owner packet." gold.mjs:774 text: "(omit the flag when the auditor listed none; naming ids is the owner's)".
5. GAP · SETUP 2 · the setup files have no order, formats or writers reachable (README.md:70 lists names). The chain:
   concept → subject.json (scripts/subject.mjs header; forklift's as template) → `node scripts/solve-camera.mjs <s> --image
   refs/<s>.png --x-edge left` (positional subject) → views.json (scripts/v6/README.md: vehicle axes, anchor, `families.table`
   sampled off the concept with `measure.mjs sample --view concept`) → facts.json (`dims` "registration measures" is circular
   for a first set: estimate from the prompt's size, re-measure after install) → gen / repair / install → `turnaround.mjs
   families --apply` → layout.measured (item 2) → prior.json (v6 README "bus card") → scaffold → doctor. Fix: a numbered
   "New subject, once" block at README.md:70 with those commands; SKILL.md:19 points at it by name.
6. GAP · SETUP 2 "a start" · scaffold is never named in the skill, needs the installed turnaround + camera + item 2 first,
   and `--shape` (cement mixer: `box` vs `machine`) is left to taste. Fix SKILL.md:19: "after install: `node scripts/v7/
   scaffold.mjs --subject s --shape sedan|box|bus|pickup|machine`; when two fit, run both to separate --out dirs, keep the better step verdict".
7. GAP · SETUP 3 · `gold.mjs doctor` exits 1 in phase setup even on PASS (gold.mjs:332): read as failure → retries. Fix:
   return `rep.verdict === "BLOCK" ? 1 : 0`, or SKILL.md:20 "(exit 1 in setup is normal; read the verdict line)".
8. GAP · SETUP 3 EDIT path · "fix the images" names no tool (NEXT goldlib.mjs:358 says "repair", which regenerates). Fix
   SKILL.md:21: "EDIT of a view: GPT edit inside the rect (refs/garbage_truck.v2.README.md) → `turnaround.mjs fix --subject s
   --dir out/turnaround/s --view v --image <png> --why --rects <audit rects>` → `install --force`; EDIT of the concept:
   refs/<s>.v2.png + README + subject.json paths.target; then doctor, re-brief the auditor."
9. GAP · after apply-audit with an unaccepted doctor BLOCK · phase stays setup and NEXT (goldlib.mjs:359) prints the
   owner gate + apply-audit again: a loop. Fix goldlib.mjs:359: when doctor BLOCK rows remain and the audit is done →
   "OWNER: BLOCK row(s) <ids> stand — the owner accepts them (`apply-audit … --accept-blocks <ids> --owner-note`) or the
   reference is fixed"; marathon: park the subject (SKILL.md:51 already sends it to the packet).
10. GAP · boundary `override` (SKILL.md:37–38, marathon 50) · ruleOverrides on the orchestrator's own `--evidence` are owner
    rulings (gold.config.json "pending ratification") and the packet's setup rulings list only fact:owner-setup /
    fact:accepted-blocks. Fix: owner-packet lists every `override` / `shift` ledger line; SKILL.md:38 "(the packet shows them)".
11. NIT · SKILL.md:16–17 `turnaround.mjs status | repair | install` need `--dir out/turnaround/<s>`; goldlib.mjs:920 close
    refusal names no remedy (append "`step.mjs --subject s --revert`"); SKILL.md:10 `commit` vs the global "only when the
    owner asks": cite the LLMModeling autonomy ruling (owner 2026-09-12), commit serially in a marathon; SKILL.md:23 / 27
    `--run <c>,<min>`: say the numbers come from the seat's final message, else the wall clock.
