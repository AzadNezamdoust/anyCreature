---
name: gold-model
description: Run the LLMModeling gold workflow (WF v8) for one subject or a batch in hard_surface — setup (concept, Gemini turnaround sheet + hull repair, gold-auditor, the owner's setup gate), then up to 3 modelling rounds with pinned seats (gold-modeller, gold-critic-opus + gold-critic-sonnet), every step a scripts/v7/gold.mjs command, then the Blender hard-surface look stage (WF v9: gold-hs-modeller build, gold-hs-reviewer-fable review, one polish; `gold.mjs hs`); unattended "marathon" batches included. Use for "model / gold / set up <subject>", "next step", "status", "run them unattended" of LLMModeling subjects.
---

# gold-model — the orchestrator's procedure (WF v8; rationale only: hard_surface/research/WF-V7-GOLD.md)
Work in D:\Git\anyCreature\hard_surface. `node scripts/v7/gold.mjs status [--subject s]` prints the phase and the NEXT
command: type it. Judgment lives in the pinned seats and the scripts: run the commands, launch each seat with the exact
prompt `gold.mjs brief` prints, relay numbers, stop at the owner gates. A REFUSED line says what to do: do that.
`gold.mjs commit --subject s` after every file-changing step (owner's LLMModeling autonomy ruling 2026-09-12; a marathon
commits one subject at a time). `--run <c>,<min>` = the seat's tool uses + minutes from its final message, else wall clock.

## SETUP (phase setup, once per subject)
1. New subject: `gold.mjs new --subject s --class vehicle --desc-file <paragraph.txt> [--gen gpt]` (parts, colours, a
   feature on a hidden face written as hidden, the real size) → concept, its prompt README, the setup files, the state.
2. Run the chain it prints = scripts/v7/README.md "New subject, once" (NEXT names the first unfinished step): camera,
   families, facts, frame, turnaround (`turnaround.mjs gen --subject s --out out/turnaround/s`; `status | repair --view <v>
   | install` take `--dir out/turnaround/s`; repair the view the concept contradicts, else the rear), `families --apply`,
   `hull.mjs --write-frame`, then the start: `scaffold.mjs --subject s --shape sedan|box|bus|pickup|machine` (two fit:
   both, separate `--out`, keep the better step verdict). STOP RULE: after 3 failed sets or 3 failed repairs of one view
   gen / repair refuse — stop regenerating; the auditor rules target-wins.
3. `gold.mjs doctor --subject s` (exit 1 = a BLOCK row: read the verdict line, not the code) → `gold.mjs brief --subject s
   --role auditor` (refused without refs/<s>.README.md's Full prompt) → Agent **gold-auditor** (semantic check first).
   EDIT of a view: a GPT edit inside the audit rects → `turnaround.mjs fix --subject s --dir out/turnaround/s --view v
   --image <png> --why "..." --rects "<audit rects>"` → `install --force`; of the concept: refs/<s>.v2.png + README +
   subject.json paths.target (refs/garbage_truck.v2.README.md). Back to 3. REGENERATE only while the stop rule is unspent.
4. OWNER setup gate: show audit/AUDIT.md, hull.png, the audit sheet; stop until the owner approves.
5. `gold.mjs apply-audit --subject s --owner-approved [--owner-note "<answer>"] [--accept-blocks id,id | audit] --run <c>,<min>`.
   A doctor BLOCK nobody accepted keeps phase setup: NEXT names it as the owner's call — relay it, never pick the ids.

## ROUNDS (cap 3: r1 build ≤ 100 calls · r2 list ≤ 60 · r3 polish ≤ 40 — scripts/v7/gold.config.json)
1. `gold.mjs brief --subject s --role modeller` → Agent **gold-modeller** with the printed prompt.
2. `gold.mjs close --subject s --run <tool uses>,<minutes>`. The cap round's close sets phase owner (no review follows).
3. Both critics IN PARALLEL, blind: `brief --role critic --seat opus|sonnet` → **gold-critic-opus** + **gold-critic-sonnet**
   (fable is a rare tie-break seat only — **gold-critic-fable**, run in parallel at the owner's call, never the default).
4. `gold.mjs merge --subject s --opus <c>,<min> --sonnet <c>,<min>` → `STOP | OWNER | CONTINUE`. CONTINUE → next round;
   MERGE BLOCKED (done:false) → brief that seat again (it resumes), merge. A subject already under a legacy fable + opus
   pairing continues on it (`--fable <c>,<min> --opus <c>,<min>`): NEXT keeps naming fable, not sonnet, until that pair closes.

## Round-boundary eye fixes (only at a boundary: after close before any critic, before the next round's first step, owner)
- A view's registration skewed (the doctor's centring row names it): `gold.mjs shift --subject s --view front --pair
  front,rear --sweep -0.1,-0.15,-0.2 --why "..."` (table of every image; the best is applied, BASE wins ties).
- The chain FAILs on what the target draws: `gold.mjs override --subject s --palette-auto` · `--wheels 6,3,equal --evidence
  "..."` · `--palette z1,z2 --evidence "..."` (each shift / override is an owner ruling pending ratification: the owner
  packet shows them). Owner-approved drift rects: `gold.mjs drift add|rm ... --owner-approved`.

## Items (weapon class, gold pipeline; owner 2026-10-12)
The game items run these gold rounds as class `weapon` with subject.json `pipeline: "gold"` (classes/weapon.json `gold`
block: rules/weapon.mjs — no wheels / running / ground contact / stability; min part 0.008 m; weapon roles and palette
zones; ONE critic seat, Opus). Never `override --wheels/--running` an item. From refs/<s>.png + subjects/<s>/turnaround:
1. `node scripts/v7/gold.mjs pipeline --subject <s> --set gold`
2. only if subjects/<s>/layout.measured.json has no `_frame.quadPx`: `node scripts/v7/hull.mjs --subject <s> --write-frame`
3. `node scripts/v7/scaffold.mjs --subject <s> --from out/ref/gold/<nearest weapon-class gold>/model.mjs` (until one
   exists: `--from out/ref/gold/it_smg_gold/model.mjs` — vehicle roles / zones, so the start's chain FAILs V7_ROLE /
   PALETTE_ZONE until round 1 renames them: receiver, grip, magazine ...; gunmetal, polymer, accent ...)
4. SETUP 3-5 as above (`doctor` → `brief --role auditor` → gold-auditor → owner gate → `apply-audit`)
5. ROUNDS as above with one critic: `brief --subject <s> --role critic --seat opus` → **gold-critic-opus** →
   `merge --subject <s> --opus <c>,<min>` (NEXT names exactly this). it_smg_gold stays class vehicle (switching it
   needs a re-baseline: roles, zones, registration).

## Direct subjects (WF v10: class weapon, and the default for new classes)
One pipeline, no gold rounds: hard_surface/WORKFLOW-V10.md (setup → look → review → function).
`node scripts/v7/gold.mjs hs --subject <s>` names every step and the agent prompt. Image generation = GPT only
(`--gen gpt`); Gemini is refused (owner 2026-10-04).

## HS — the look stage (WF v9; after a subject reaches phase owner / done)
Gold = the measurement stage (silhouette, metres); HS = the look stage: a Blender 5.1 hard-surface rebuild with real
detail (hard_surface/scripts/hs/README.md; outputs out/blender-hs/<s>/). `node scripts/v7/gold.mjs hs [--subject s]`
prints each subject's stage and NEXT — type it:
1. build → Agent **gold-hs-modeller**, prompt `subject: <s>, mode: build` (≥ 4 render-compare passes from the gold
   model's metres, never pre-scaled, ends `--final`).
2. review → Agent **gold-hs-reviewer-fable**, prompt `subject: <s>` — blind (never pass the modeller's report); writes
   review_fable.md only.
3. polish → Agent **gold-hs-modeller**, prompt `subject: <s>, mode: polish` — fixes every review item, the turnaround
   wins over the reviewer; writes POLISH.md. K = 1: no second polish; the residual goes to the owner packet.
4. function → Agent general-purpose (model opus), prompt `Subject s = <s>. Read and follow out/blender-hs/RIG-BRIEF.md`
   — writes rig.json (turret yaw, weapon pitch, wheel spin / steer, suspension, rotor spin, track scroll, doors +
   physics; contract scripts/hs/rig.md) and runs `scripts/hs/rig_pass.py` until RIG PASS: pivots, collision sweeps,
   ground, mass, tip-over, drop / bump / accelerate / brake / lateral sim, look gate re-check, `<s>_rigged.glb` with
   clips. Parts stay where the look stage put them unless a collision forces a documented move. The dispatcher opens
   rig_sheet.png itself (joints on their parts at every pose) — a passing count is not the check.
5. owner → show out/blender-hs/<s>/compare.png + rig_sheet.png (+ POLISH.md `## Owner`, the Fable score, the gate
   line, the rig's failed tests and its stated limits).
Method = scripts/hs/method.md (owner 2026-10-04: build what makes sense, not line-to-line; major masses first).
Gate (run_pass scores with the gold judge's own code): no ortho view's agree more than .04 below the gold model's (the
concept view is a look reference, not gated), tris ≤ budget, topology 0 — a FAIL goes to the owner packet, it is not a reason to loop. A long concept-vs-turnaround conflict
is the owner's call. If the gold-hs-* agent types are not loaded in the session, launch general-purpose with model opus
(builder) / the Fable model (reviewer) and the agent file's body as the prompt — never opus-worker (60-turn cap).
≤ 6 HS agents at once; one modeller per subject. HS outputs live in the gitignored out/: nothing to commit.

## The owner packet
`gold.mjs owner-packet [--subject s]` → OWNER.md per subject (open owner items, proposed drift rects with ready `drift add`
lines, setup rulings, shift / override lines) + out/ref/gold/OWNER-BATCH.md. Show them + view/model-view.png; relay the
call: `gold.mjs owner --subject s --accept | --review | --extra-round`.

## MARATHON (the owner says to run unattended)
- Auditor defaults: `apply-audit --owner-approved --owner-note "owner '<their words>' <date> — auditor defaults"`, plus
  `--accept-blocks audit` ONLY when audit.json has an acceptBlocks list; never name ids yourself — a standing BLOCK the
  auditor did not list parks the subject in setup for the owner packet. A spent stop rule means READY, never regenerate.
- ≤ 6 agents at once, a queue in this order: setup audits → r1 modellers → critic pairs → next modellers …; a free slot
  takes the next NEXT of any subject. Boundary fixes (shift / override) between close and the critics.
- Never stop for an owner item: it lands in the owner packet. At the end: `gold.mjs owner-packet`, commit per subject.

## Never by hand
Merges, worksheets, ledger lines, state.json, LEDGER.md, probes.json, ruleOverrides, drift rects, views.json after the
chain, the eyes files (after an intended eye change `gold.mjs eyes-check` must print clean), existing refs/** (frozen).
No GPT / Gemini / Codex outside SETUP image generation. Never `git add -A`, never a directory pathspec.

## Effort
The seats' model and effort are pinned in .claude/agents (modeller Opus 5.5, critics Opus 5.5 + Sonnet, auditor Opus 5.5;
fable 5.1 is a rare tie-break critic seat only, added in parallel at the owner's call, not the default pair); every rule
is a script. Spend extra effort only on an owner packet or a REFUSED line.
