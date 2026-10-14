# LLMModeling — target workflow (three models, one loop)

Owner directive 2026-09-12: Fable 5.1 (medium effort) + GPT Astra (high effort) + Opus 5
(medium effort) work together. This file is the operating design. PLAN.md stays the
architecture; this is who does what, through which channel, with which gates.

## 1. Roles by lane (never crossed)

| Seat | Model | Effort | Sees | Produces |
|---|---|---|---|---|
| LISTER | Fable 5.1 | medium | TARGET (+ BASELINE capture for item lists) | `refs/<t>.parts.json`, `runs/<run>/items.json` |
| BUILDER A/B/C | GPT Astra | high | DSL doc + examples + plan + previous-tier summary | spec fragment |
| REPAIR | GPT Astra | high | fragment + ≤8-line validator text | corrected fragment |
| WORKER (Blind Loop) | GPT Astra ×2 + Opus 5 ×1 per round | high / medium | item text + ledger lines + own worktree | diff + one `CHANGE:` line |
| JUDGE | Fable 5.1 | medium | TARGET + anonymised A/B/C/D | `PICK` / `WORSE` / one sentence |
| IMPLEMENTER (harness, validators, prims) | Opus 5 | medium | brief + repo | code + tests + evidence |
| REVIEW / RULINGS | Fable 5.1 | medium | receipts, diffs, stills | PASS/FAIL, owner-gate hand-offs |
| ORCHESTRATOR | script (`orchestrator.mjs`) | — | exit codes, counters | worktrees, captures, ledger |

**What the TARGET means (owner ruling 2026-09-12):** the reference image sets the overall
style and the model — proportions, massing, colour blocking, part vocabulary, cartoon
flatness. It is never a wireframe to trace. Listers write items as style/model gaps
("reads brown, should read mint"; "fire escape reads as a slab, should read as open
ironwork"), never pixel or outline alignment. Judges rank overall likeness. Silhouette
overlap, edge maps and pixel metrics are never rankers; at most a regression guard.
Owner ruling 2026-09-12: assets and captures stay outline-free (flat vertex colours only);
the reference's ink outlines are style context, not a feature to reproduce.
Generated targets (make-target) are style references too — a busy or over-detailed
generation is a prompt failure, not something to copy detail-for-detail.

Invariants (from BLIND_LOOP.md, unchanged): doer never judges; worker never sees the
target; judge never sees authorship; BASELINE always competes; ties to BASELINE; one item
per round; artifacts only cross seats; every seat starts empty.

Why this split: geometry authoring is where Astra is strongest, so it owns every seat that
emits a spec. Judgement seats (lister, judge, review) stay on Fable so the model that
authors is never the model that scores. Opus keeps the code lanes and one candidate per
round so no round is a single-model monoculture — the ledger shows which family wins per
item class, and the split can be re-weighted from evidence, not opinion.

## 2. One channel for every model call: the relay

`tools/BlindLoop/relay/pending/<seat>-<stamp>.prompt.md` + `.meta.json` → the seat edits
(worker) or answers (builder/judge) → `<same>.response.md`. Adapters:
`adapters/worker-relay.mjs`, `adapters/judge-relay.mjs`; `scripts/gen.mjs --runner file`
for builder/repair. Any model that can read a file, edit a worktree and write a file can
take a seat. Absolute paths always (worker cwd is the worktree).

Astra channels, in order of preference:
1. `codex exec` CLI adapter (`adapters/worker-codex.mjs`, `--runner codex` in gen.mjs):
   unattended, `--model gpt-astra --reasoning high`. Needs the CLI on PATH + login.
2. Codex app / Cursor pointed at the relay folder: Astra opens the pending prompt, does the
   work, saves the response. Human-clicked, still artifact-only.
3. OpenAI API key → `--runner api`. Not present on this machine.

Claude seats: Agent tool seats in this session (today), or `claude -p` once the CLI is
logged in. Effort per seat: Fable medium and Opus medium are the Agent-tool defaults here;
Astra high is set on its own channel.

## 3. The loop, per subject

```
TARGET.png (frozen) ──► LISTER (Fable) ──► parts.json ──► BUILDER A/B/C (Astra) ──► validators
      │                                                    │ FAIL ≤2 → REPAIR (Astra)
      │                                                    ▼
      │                                          subjects/<s>_llm/spec.json = BASELINE
      ▼
LISTER (Fable): TARGET vs BASELINE capture → items.json (one difference each, by weight)
      ▼
ORCHESTRATOR: per item → 3 worktrees → WORKERS (Astra, Astra, Opus) → gate (`npm run check`)
      → captures on 4201–4203 → shuffle → JUDGE ×3 (Fable) → majority → merge or BASELINE
      → ledger → stall/park rules → next item
      ▼
REVIEW (Fable): merged stills + ledger → owner taste gate → commit (owner)
```

Budgets (config.llmmodeling.json, frozen per run): 3 workers, 3 judge runs, 3 rounds/item,
4 passes, 90 min, stall K=2.

## 3b. Merge stacking rule (learned 2026-09-12, run r8)

The orchestrator cuts candidate worktrees from HEAD but merges winners into the working
tree. Two rounds in one invocation therefore validate candidates against a base that lacks
the previous merge, and the stacked result can fail (r8: three props left floating with
`embed` ≈ 10 m, tri count 8312 > 8000). Rules:
- **One item per orchestrator invocation** (`--item <id>`), commit the merged spec, then
  the next item. Never a multi-item run until the orchestrator re-validates after merge.
- After every merge: `node scripts/check-spec.mjs subjects/<s>/spec.json` on the main tree
  before committing. A FAIL here is a REPAIR seat task, not a new loop item.

## 4. Gates, in order, no exceptions

1. `npm run check` (V0–V7, V9, V10, fixtures) in the worker's worktree — FAIL reverts the
   candidate, ledger says `no change produced - lost`.
2. Capture determinism (preflight: 3 identical captures) before any run.
3. Frozen files clean and committed (preflight).
4. Judge majority; tie → BASELINE.
5. Fable review of the merged diff + still before the owner sees it.

## 5. What "perfect" still needs (ordered)

1. **Reference PNG on disk** (`refs/tenement-iso.png`). Until then the loop judges against
   the hand render, which proves mechanics, not taste.
2. **Astra channel 1** (Codex CLI on PATH, logged in) so builder + worker seats run without
   a human relaying. Same for `claude /login` on the Claude side.
3. **Relay watcher script** (`scripts/relay-serve.mjs`): polls `relay/pending`, dispatches
   each prompt to the right model channel by `meta.role`, writes the response. Removes the
   per-prompt human step entirely.
4. **Measure pass** (Grounded SAM or clicked boxes) so builders get metres, not guesses.
5. **Limits ratified** (`src/validate/limits.json`), then frozen.
6. **Per-family scorecard** from the ledger: wins per model per item class. Re-weight the
   worker split from it after ~10 rounds.
7. **Turn-cap hygiene** for Claude seats: briefs ≤ one milestone, `npm run check` once,
   logs to file. Continuation seats cost a full rebrief.

## 6. Round cost today vs target

| | today (relay by hand) | target (channels 1 + watcher) |
|---|---|---|
| worker candidate | ~2 min seat + gate | ~1 min |
| judge run | ~20 s | ~20 s |
| round (3+3) | ~10 min | ~4 min |
| object from image (3 tiers) | ~15 min | ~3 min |
