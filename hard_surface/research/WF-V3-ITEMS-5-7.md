# WORKFLOW-V3 items 5–7 — two Opus jobs, disjoint files (Opus 5 plan, 2026-09-13)

Authority: `WORKFLOW-V3.md` §2, §3, §7 items 5, 6, 7. Routing: Opus 5 implements and reviews; GPT Astra
high is the geometry author (Codex CLI). Working dir `D:\Git\checkout\tools\LLMModeling`. Never touch
`refs/**`, `src/validate/limits.json`, `tools/BlindLoop/**`, `tools/CharacterStudioV2`. No commits (the
orchestrator commits). `npm run check` must be green at the end (175 tests today); every behaviour change
gets a test. Dev server: port 4210 is already running (launch config "llmmodeling"); do not start another.

Already written by the orchestrator (read them first, extend, do not rename):
- `scripts/subject.mjs` — `loadSubject(id)` → `{id, klass, subject, cls, rel, paths, readJson}`,
  `subjectIdFromArgv()` (`--subject`, `LLMM_SUBJECT`, default `facade_brick`). Node-only.
- `subjects/facade_brick/subject.json` — class, `paths{target,camera,module,passes,census,layout,
  layoutMeasured,regions,missingKeys}`, `outDir`, `missingKeyPolicy`, `deferredByRuling`.
- `classes/building.json` — `roles`, `bearingRoles`, `triBudget`, `styleFloorKey`, `rules`,
  `authorRules`, and four `TODO-LIFT` keys.

Acceptance for BOTH jobs: with no flags every script behaves exactly as today on `facade_brick`
(prove it: `node scripts/pass.mjs 2 --gate-only --no-repair` still ends `[verdict] P2
ACCEPTED_WITH_RESIDUALS` with the same three residuals, and `capture2` stills are byte-identical to
before your change); a grep for the literal `facade_brick` / `tenement-iso` in the files you own
returns only comments, tests and the default in `subject.mjs`.

## Job D1 — class prior, subject paths, inferred contact
Owns: `classes/building.json`, `src/validate/kernel-chain.mjs`, new `src/validate/rules/building.mjs`,
`scripts/likeness.mjs`, `scripts/calibrate-palette.mjs`, `scripts/compare-still.mjs`,
`scripts/capture2.mjs`, `scripts/measure-target.mjs` (paths only), `src/app.js`, `test/**` for these.
1. **Lift constants into `classes/building.json`** and delete them from code: CENSUS_RULES (serialisable
   fields), ROLE_ID_COLOURS, AREA_FAMILIES / DROPPED_AREA_ZONES / CENSUS_ROLES / CENSUS_INSTANCES /
   IRON_ROLES (make CENSUS_INSTANCES data: role → census key or sum), calibrate ZONES. ROLES and
   BEARING_ROLES come from the class file. Anything that is a FUNCTION (LAYOUT_RULES measures, the V11
   validators, V7 building rows) moves to `src/validate/rules/building.mjs`, which exports
   `{ layoutRules, validators }`; kernel-chain receives the class prior through `validateParts(meta,
   parts, limits, { census, layout, cls, rules })` and falls back to importing building rules only when
   `cls` is absent (keeps old tests valid). No building word may remain in kernel-chain outside comments.
2. **Subject paths**: likeness, calibrate-palette, compare-still, capture2, measure-target read
   `loadSubject(subjectIdFromArgv())`; remove SUBJECT/TARGET constants and capture2's absolute
   `D:/Git/checkout` path (derive from ROOT). `src/app.js` fetches `subjects/<s>/subject.json` and
   `classes/<class>.json` for the `.mjs` branch (census, layout, role id colours) instead of hard-coded
   paths/tables. measure-target keeps its building scan logic (subject-specific by design) but takes its
   file paths from the manifest.
3. **Harness-inferred contact** (WORKFLOW-V3 §3): a part's effective `touches` = declared ∪ inferred,
   where inferred = every other part within `epsAbs` surface distance OR penetrating by ≤
   `inferredContactFrac` (new KERNEL_LIMIT_DEFAULTS key, 0.02) of the smaller volume. V2/V3 use the
   effective set; V6_CLASH_UNDECLARED still fires above 0.02 unless the pair is declared with
   `embed:true`. Report inferred pairs count in `measurements`. Tests: a module with NO `touches` at all
   that is flush-assembled passes V2/V3; a 10 % undeclared penetration still fails V6.
   Then remove the author's AABB auto-`touches` loop need from README wording only if you own it — you
   do not (Job D2 owns README); leave a note in your report.

## Job D2 — seat contract, MISSING KEY consumer, prompt from class files
Owns: `scripts/pass.mjs`, new `scripts/seats/{codex,relay,fake}.mjs`, new `scripts/missing-keys.mjs`,
`src/kernel/README.md`, new `classes/building.md`, `subjects/facade_brick/passes.json`,
`scripts/measure.mjs`, `test/**` for these.
1. **Subject paths in pass.mjs**: `--subject` via `subject.mjs`; remove SUBJECT/MODULE_REL/PASSES_REL/
   CENSUS_REL/CAMERA_REL/TARGET_IMAGE constants and the `out/facade` literal (use `subject.outDir`).
2. **Seat adapters** `scripts/seats/<name>.mjs` each exporting `async function runSeat({prompt, images,
   workspace, timeoutMs, tag, mode}) → {answer, change, missingKeys:string[], artifact:string|null,
   usage:{input?,cached?,output?,reasoning?,total}, seconds, model, effort, failureClass:
   null|"transport"|"timeout"|"contract", transcript}`. `codex.mjs` = today's runCodex moved verbatim
   (header assertion kept; `failureClass:"transport"` for "Unable to verify model access"/stream drops so
   pass.mjs exits 2). `relay.mjs` = writes `relay/pending/<tag>.prompt.md` + copies images, waits for
   `relay/done/<tag>.answer.md` (for Claude/Gemini/any chat UI). `fake.mjs` = returns a module from
   `LLMM_FAKE_MODULE` (tests). `pass.mjs --seat codex|relay|fake` (default codex).
3. **Text-only mode** `--seat-mode text|agent` (default **text**): the prompt carries everything
   (class author rules + kernel API + module + item + previous FAIL rows) and ends with the contract:
   "Do not run commands or read files. Reply with the COMPLETE module in one ```js fence, then one line
   `CHANGE: …`, then optionally one line `MISSING KEY: k1, k2`." The harness extracts the fence, writes
   the module, runs check-module → chain → capture → likeness. A reply without a fence →
   `failureClass:"contract"` → counts as the pass's repair-eligible FAIL, not exit 2. For codex in text
   mode use `-s read-only` and drop the "run check-module" instruction. `agent` keeps today's behaviour.
   Repair prompt in text mode carries the failing rows + a unified diff of what the seat changed, not the
   module twice.
4. **Author rules from the class**: split `src/kernel/README.md` into the generic kernel API (stays)
   and `classes/building.md` (roles, projections, frames/sills/crown rules, three-pass order, layout-key
   sentence, MISSING KEY sentence); prompt = README + `cls.authorRules` file. Remove the instruction that
   makes authors hand-declare every `touches` (D1 infers contact); keep `embed:true` for deep seating.
   Pass items use `{MIN_FEAT}`-style tokens from config, never restated numbers.
5. **MISSING KEY consumer** `scripts/missing-keys.mjs`: parse `MISSING KEY` lines from `last.md` and
   `repair.md` after every seat; merge into `subject.paths.missingKeys` JSON `{key:{count, passes[],
   firstSeen}}`; preflight prints the backlog; with `missingKeyPolicy:"refuse"` a pass whose item is
   re-run while any key has count ≥ 2 and is still absent from layout.json throws RefusalError (exit 3).
   Default policy "report". Seed the backlog from run 4 (`out/facade/run4/P*/last.md`).
6. **Usage split** in `measure.mjs`/timings: input / cached / output / reasoning when the adapter
   provides them, else total only.
7. **Proof**: one LIVE Astra pass in text mode — back up `subjects/facade_brick/facade.mjs` and
   `out/facade/P0` to `out/wf-loop/v3-items5-7/backup/`, reset the module to
   `test/fixtures/kernel/smoke.mjs` (import path fixed), run `node scripts/pass.mjs 0 --seat codex
   --seat-mode text`, record seconds/tokens/verdict and copy `out/facade/P0` to
   `out/wf-loop/v3-items5-7/P0-text/`, then RESTORE the module and `out/facade/P0` from the backup. If
   Codex is unreachable after two tries report it and finish everything else.
