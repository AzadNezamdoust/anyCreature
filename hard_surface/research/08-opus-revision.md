# 08 — Opus revision after exchange with 07 (Fable)

Position = `06-arch-opus.md`. Citations: `[Rnn:LL]` = research file + line; repo = `file:line`.
Conclusions only.

## 1. AGREE (converged independently — treat as settled)

- LLM emits a relational attachment program in metres, never a world coordinate; a JS compiler owns every transform (06:27-28 / 07:8-11).
- One runtime: JS compile + validate + three.js capture; Blender never in the loop (06:9-12 / 07:16) [R03:222-226].
- Same DSL core: `prim` + `dims` + `attach{to,face,uv,contact}` + `repeat`/`mirror` macros, 5-mode contact vocabulary extended from `blockout-spec.json:31-45`.
- CGA-lite facade splits with `touches`→wall occlusion; windows derived, never placed [R02:133-137].
- Ten headless validators before any pixel; identical repair policy (auto on V2 small gap / V5 thin / V6 duplicate; never auto on V3 orphan or V7 scale).
- Tiered generation massing→facades→props, ≤2 repairs/tier; LISTER once per TARGET and frozen with it; Grounded-SAM measurement spike with operator-clicked-box fallback.
- `manifold-3d` union is a *cross-check* behind the contact graph until a 20-fixture study promotes it [R03:249-252].
- Determinism lives in the cache and the compiler seed, never in the model call [R03:138-143].
- Fork CharacterStudioV2 (`geom.js`, `exporters.js`, the `studio.js:388-416` capture contract); copy, never import across roots.
- Sibling `config.llmmodeling.json` + forked worker adapter; `BLINDLOOP_CONFIG` is owner-gated; TownhouseStudio contributes inventory + palette only.

## 2. DISAGREE — 06 holds

**D1. Judged view stays the single frozen target view; 07's 2×2 `sheet` (07:123-126) must not be the judged artifact.**
The capture viewport is fixed at 900×900 (`config.json:11`), so a 2×2 sheet gives each view 450² — the `MIN_FEAT = 3·PX` floor doubles in world size and the judge goes blind to exactly failure mode 2 [R02:159-162, R01:146-149]. Three of four quadrants have no TARGET counterpart, so the judge is asked to rank content it cannot compare [R04:97-100], against a prompt that assumes "same camera" [R04:190]. Unattached rears are already decided numerically by V3 + V8; keep 06's `npm run qa` sheet as an *offline* artifact.

**D2. The IoU regression guard stays orchestrator-side, out of `npm run check` (against 07:128-131).**
At check time no BASELINE PNG exists inside the worktree — the baseline capture happens in the orchestrator before any worker runs (`orchestrator.mjs:435-440`) and never enters a worktree. Worse, a worker-runnable script that scores against `refs/<t>.mask.png` hands the worker a target proxy to optimise, breaking "the worker never sees the target" (`roles/worker.md:39-40`, `BLIND_LOOP.md` invariants).

**D3. Keep V10 export hygiene as its own blocking validator (06:82).** 07 folds only the tri budget into V8 (07:86) and leaves one-mesh/one-material/no-NaN to the test suite. The budget is an owner-ratified number; it must fail the gate, not only `node --test` — port `character.test.js:104-113` into the validator, not just the tests.

**D4. Hold 06's per-tier seat split with summary hand-off (06:94-96) over 07's one BUILDER re-fed prior tiers verbatim (07:104).** Resending every prior fragment plus `SCHEMA.md` per tier is the growth curve anyCreature named as the actual cost driver — "an identical command costs several times more at round 20" [R01:160-166]. BUILDER-B/C see the previous tier's `solved.json` *summary*.

**D5. `budgetTris` belongs in `limits.json`, not in the LLM-authored spec.** 07 puts it at 07:31 and then declares tri budgets owner-gated at 07:91-92. A number inside the spec is a number the model can raise.

## 3. ADOPT from 07

- **A1. `align ∈ {bottom,center,top}` on side attachments (07:59).** 06's `uv` fixes a point on the *parent* face and never says which point of the *child* is anchored. Required — see G4.
- **A2. Composite prims as spec fragments** (railing, stairFlight, landing, vent, awning, pipe) authored once and library-learned (07:54-56). This is the concrete form of 06's abstract "library learning" (06:168).
- **A3. 20 broken fixtures, each failing exactly its V-code, as the M1 acceptance criterion (07:188-191).** Strictly better than 06's `report.pass == true`; it is the only evidence a validator actually bites.
- **A4. `src/validate/limits.json` as the single owner-number file, added to frozenFiles (07:91-92).** 06 scattered the same constants across §2 and §8.
- **A5. The human-modeler loop is a deliverable, not a by-product (07:147-150):** spec hot-reload, in-page violation overlay (orphan red, thin yellow, gap vectors), knob panel. Brief priority 3; 06 under-served it.
- **A6. M2 owner taste gate on the still, and an M5 generality milestone (vehicle/robot, V9 live)** (07:194, 07:201-202).
- **A7. `rot` restricted to one axis about the attach normal in v0 (07:60-61)** — narrower than 06's free `rot:[rx,ry,rz]`; revisit at M5. Closes [R02:233-235] instead of deferring it.

## 4. GAPS — neither proposal covers these, and M0–M1 hits every one

**G1. The judge contract is already frozen and neither proposal matches it.** Both copy [R04:189-199]'s `PICK:`/`WHY:`. The parser requires `PICK:` then `WORSE: <letter|none>` then the sentence on the next line (`orchestrator.mjs:333-345`), and `roles/judge.md:48-49,:61` — a frozen file (`config.json:38-40`) — already states it. Use the existing role prompt verbatim; criteria ordering can only enter through the item brief.

**G2. Candidates are serial and candidate ports are hardcoded.** `orchestrator.mjs:446-479` runs worker→capture in one sequential `for` loop, and `captureWorktree(wt, 4200 + n, png)` fixes candidate ports at **4201–4203** regardless of the project's own port. So 06's "ports 4211–4213, parallel" and 07's "3 candidates in parallel … <90 s" are both wrong: a round costs 3 × (worker + dev-server cold start + capture), and two BlindLoop runs can never overlap even with sibling configs. Port 4210 only ever serves the human's `npm run dev`. Re-budget M0's timing target on the serial figure.

**G3. Nothing currently runs the validators as a gate.** `worker-claude.mjs:55` is prose inside the worker prompt, and `orchestrator.mjs:419` computes `ok` from the adapter's exit status but the round loop never reads it (`:464-474` branches only on frozen-file touch and empty diff). The one mechanism that works without touching a frozen file: the **forked adapter** runs `npm --prefix tools/LLMModeling run check` itself and, on FAIL, reverts its worktree (`git checkout -- . && git clean -fd`) so `diffPaths` is empty and the orchestrator records `no change produced - lost`. Adapters are not frozen (`config.json:32-42`).

**G4. The attach solver must be written down before M1.** Needed: the six parent-face frames (origin, u-axis, v-axis, outward normal, handedness) for ±X/±Y/±Z; which child point is anchored (`align` selects the child's extreme along the face-tangent, `uv` places it on the parent face, `contact` selects the child face that touches); and the order of operations — child scale → `rot` about the attach normal → align/uv translate → parent world matrix → `embed`/socket shift along −normal. One table plus one worked example per contact mode. Ambiguity here re-admits failure mode 1 through the compiler itself.

**G5. `uv` and `repeat.axis` on a rotated parent.** Both proposals say `uv` evaluates in the parent's local frame; neither says what `repeat{axis:"+Y"}` means on a stair flight carrying `rot`. Rule: repeat axes are parent-local, and the compiler writes the resolved **world** direction into `solved.json` so V5's screen-space test measures the real one.

**G6. repeat × facade occlusion is order-dependent.** A balcony repeated up +Y must suppress the facade tiles it touches, so the grammar has to run after expansion and read the *expanded* contact set. Fix the compile order explicitly: resolve attach → expand repeat/mirror → build contact table → run facade grammar with occlusion → merge. 06 states no order; 07's layout implies grammar before repeat.

**G7. V8 cannot run inside `check`, and the manifest is not `check`'s to write.** 07:146 has `check` reporting `v8:skipped` "in the manifest" — but `check` is a node process and `__CAPTURE_MANIFEST__` exists only in the capture page (`studio.js:404-416`). Split it: V0–V7 + V10 blocking in node (the G3 gate); V8's id-buffer runs inside the capture page and writes `validatorPass`/`violationCount` into the manifest as an export-time drop plus a recorded advisory. Do not gate a round on V8.

**G8. vite does not HMR a JSON spec, and the overlay must not reach the pixels.** `import spec from './spec.json'` triggers a full page reload, not a hot update; and the A5 overlay must be hard-disabled under `?capture=1` or it enters the frozen capture and voids the round (`studio.js:10-12`). Load specs by `fetch()` in dev with an explicit `import.meta.hot` handler, and inline them at build so `preview` — the path `capture-candidate.mjs:15-19` uses — has no network dependency.

**G9. The sibling config must freeze itself.** `config.json:33` lists `config.json` in its own `frozenFiles`; `config.llmmodeling.json`, `refs/<t>.*` and `limits.json` need the same or a worker can edit its own gate. Also `urlForOrigin` (`orchestrator.mjs:276-281`) fills the URL from `capture.defaults` alone with no per-candidate override — **one run = one subject, one view**; more subjects means more configs and more runs.

**G10. There is no glTF import path into Unity — the stated consumer.** `TheCheckout/Packages/manifest.json` has `com.unity.formats.fbx` 5.1.6 and **no** glTF importer (no `com.unity.cloud.gltfast` / UnityGLTF). Both proposals rule FBX out of scope on the grounds that the JS side has no FBX exporter [R05:167] — true, but it leaves the GLB with nothing to open it. Either the Unity-side package pin is added (a package-tree change = owner validation zone) or the export AC must read "opens in a glTF viewer with COLOR_0 intact", not "lands in Unity". Also unstated: URP Lit ignores COLOR_0 without a vertex-colour shader — UNVERIFIED which material the ingest would use. Decide at M0, before the export milestone claims Unity delivery.

## 5. Factual errors in 07

1. **07's worked example fails 07's own V0.** `balcony_R2` attaches to `mass_R`, `facades[0]` is `on:"mass_M"` with `door:"door_M"`, and `unit.part` is `door_L` — none of `mass_R`, `door_M`, `door_L` exist in `parts[]` (07:33-48 vs the V0 rule at 07:78). This example is meant to ship in-context as a worked example [R03:170-172]; fix before it teaches the model an invalid program.
2. **"The worker adapter's gate line runs it, so a FAIL candidate is a lost attempt" (07:130-132) is false.** That line is prompt prose (`worker-claude.mjs:55`); nothing verifies it and the orchestrator ignores the adapter's exit status (G3).
3. **"`check` … reports `v8:skipped` in the manifest" (07:146)** conflates a node process with a browser global (G7).
4. **"per-prim watertight + winding (χ=2)" (07:79) is wrong for 07's own prim vocabulary.** χ = 2 is genus-0 only; `ring`, `tube` and closed `lathe` (07:53-54) are genus-1 (χ = 0). The check must compare against a per-prim declared genus, not the constant 2 [R04:167].
5. **`budgetTris` in `spec.json` (07:31) contradicts 07:91-92**, which places tri budgets in owner-gated `limits.json` (D5).
6. **"3 candidates in parallel worktrees … <90 s" (07:152-153)** — the orchestrator is a sequential loop (G2).
7. **Judge output "PICK/WHY" (07:106, :135)** — the frozen contract is PICK/WORSE (G1). *06 carries this same error and is corrected here.*
8. **"2:1 iso ⇒ θ 30°, φ 45°" (07:122) is stated as fact**; [R04:122] marks Tapped Out's own angle UNVERIFIED. The value must be *measured* off the frozen TARGET with the two-slope solve, never assumed — same for 06's use of it.
