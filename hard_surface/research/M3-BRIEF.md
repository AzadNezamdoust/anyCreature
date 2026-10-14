# M3 brief — LLM authors the spec (implementer seat, Opus 5)

Read: `PLAN.md` §3 (seats), §1.3 (report contract), §5 (cache), §7 M3; `research/04-image-and-judge.md`
§T6 (lister prompt) + §T7 (repair re-prompt); `research/02-correctness.md` §T5 (tiered
generation); `dsl/SPEC.md`; `src/validate/index.js` (validateSpec, report.text), `src/validate/repair.js`;
`subjects/tenement_block/spec.json` (the hand BASELINE — never overwrite); `refs/README.md`.
M0–M2 green (66 tests). No commits. No CS2 / BlindLoop-frozen edits. No skills.

## Constraint discovered
No API key on this machine and the standalone CLI `C:/Users/AZAD/AppData/Roaming/Claude/claude-code/2.1.260/claude.exe`
is not logged in (owner must `/login` once). So the model call must be **pluggable**:

- `--runner cli` → spawns `${CLAUDE_BIN:-claude} -p <prompt> --model <id> --output-format json`
  with env `CLAUDECODE`, `CLAUDE_CODE_ENTRYPOINT`, `CLAUDE_CODE_SSE_PORT` removed (nested-session
  guard). Parse `.result` text; log `.usage` tokens + `duration_api_ms`.
- `--runner file` → writes `cache/pending/<hash>.prompt.md` and `<hash>.meta.json`
  ({model, seat, subject, tier}) then exits 3 with a one-line instruction; a later invocation
  finds `cache/pending/<hash>.response.md` (written by a human/agent), moves both into
  `cache/specs/<hash>.json` and continues. Idempotent: rerunning resumes at the first missing
  response.
- `--runner fake` → for tests: a JS module path that maps prompt hash/seat → canned response.

Model ids pinned exactly: lister/judge `claude-fable-5-1`, builder/repair `claude-opus-5`.

## Files
1. `prompts/lister.md` — from 04:T6, plus: if `refs/<subject>.png` is absent, the runner passes
   `refs/README.md`'s inventory text instead of an image and the prompt says so (**DEVIATION
   until the PNG lands**). Output JSON `{parts:[{name,parent,attach_face,rel_size,count_uncertain}],
   unit:{name,unit_m}}`.
2. `prompts/builder-a.md` (massing), `builder-b.md` (facades), `builder-c.md` (attached props +
   composites). Each embeds: full `dsl/SPEC.md`, two valid worked examples (`dsl/examples/crate.json`,
   `facade-demo.json`), the lister `parts.json`, the **summary** of previous tiers (part ids,
   dims, faces, bounds — not the full JSON, 08:D4), the tier's allowed prim/composite subset,
   and the hard rules: JSON only, no world coordinates, every non-ground part has `attach`,
   ids snake_case, metres, ≤ N parts for the tier (A ≤ 10, B ≤ 4 facades, C ≤ 40 parts).
   Output = a JSON fragment `{parts:[…], facades:[…]}` merged onto the running spec.
3. `prompts/repair.md` — input: the tier fragment + `report.text` only (≤8 lines). Output: the
   corrected fragment. Cap 2 per tier.
4. `scripts/gen.mjs <subject> [--runner cli|file|fake] [--out subjects/<subject>_llm]`:
   lister → (skip MEASURE, note deviation) → builder A → validate (V0–V3 only after A, full
   chain after C) → auto-repair (repair.js) → if still FAIL, repair prompt (≤2) → next tier.
   Writes `subjects/<subject>_llm/{spec.json, solved.json, report.json, run.json}`; `run.json`
   = per-call {seat, model, hash, cached, tokensIn, tokensOut, ms, pass, violations}. Cache key
   `sha256(promptTemplateHash + inputsHash + dslVersion + seat + tier)`; hit = zero calls.
   Never writes into `subjects/tenement_block/`.
5. `test/gen.test.js` with `--runner fake`: canned lister + A/B/C fragments where B is
   deliberately broken once (a floating balcony) → gen repairs via the repair seat (fake returns
   a fixed fragment on the second call) → final PASS; assert cache hit on rerun makes zero
   runner calls; assert `subjects/tenement_block/spec.json` untouched (sha).
6. `README.md` Status → "M3 pipeline built <date>; live run pending CLI login / file runner".

## Evidence
`npm run check` tail (all green); `node scripts/gen.mjs tenement_block --runner file` run once
→ show the pending prompt path + meta; `node scripts/gen.mjs tenement_block --runner fake` full
run → `run.json` summary line. Do not attempt `--runner cli` (not logged in). No dev server needed.
Report: PASS/FAIL per item, deviations, evidence paths, one failing excerpt.
