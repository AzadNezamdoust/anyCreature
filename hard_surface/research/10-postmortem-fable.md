# 10 — Post-mortem (Fable 5.1 seat, independent, 2026-09-12)

Owner question: "almost everything is additive, no boolean or poly modelling, why?" Evidence:
PLAN, WORKFLOW, README, research/01–09, SPEC, src, spec.json, run logs, git log, both PNGs. Astra's raw NOT read.

## Conclusions first

1. Additive-only was a **research ranking that became a plan axiom**, then a **validator
   dependency**, then an **unimplemented backlog item**. Nobody ever ruled "no booleans"; the
   route that was ranked #1 (03:190) only ever emits closed boxes, and every validator written
   after it assumes a part IS its `dims` box. Subtraction became impossible without a rewrite.
2. It capped quality at "coloured massing": no window reveals, no arch, no cornice profile, no
   ironwork. The result reads as boxes with dark rectangles glued on; the target reads as a
   building. The massing (the first 40 %) is right; almost nothing past it is expressible.
3. The constrained DSL did not stop the model writing coordinates — it made it write them as
   six-decimal `uv` fractions and `embed: 6` hacks (spec.json `fe_stair_tread_1..17`,
   `shop_awning_canopy`). The core premise (README:9) is violated by the shipped artefact.
4. Time split (estimate): research + plan ~1 day-equivalent of seats (09-10), harness +
   validators + composites ~1.5 days (09-11 to 09-12 00:47), the model itself ≤4 h of
   builder/worker seat time. Loop rounds 10:23–19:48 on 09-12: 11 runs, 8 merges, 3 voids,
   2 stalled runs, one ~35-min post-merge repair. Of ~9.5 h loop wall-clock, roughly half was
   harness incidents (UNVERIFIED to the minute; derived from run `started:` stamps + commits).
5. The Blind Loop was applied ~one stage too early. Every merged item was a lister-visible
   defect a single human or a single Astra pass could have fixed in one edit; three judges
   voted 3–0 on 7 of 8 rounds (only fire-escape-open split 2–1, r8 log:16). Unanimity is the
   signature of a gap that needed no blind judging.
6. v2: let Astra write a **CSG program** (manifold-3d union/difference/extrude-with-holes) with
   the validators kept as post-hoc numeric gates on the *result*, and use the Blind Loop only
   after the first 90 % exists.

## 1. Why additive-only — the decision trail

- **Research ranking (the real decision point).** 03-landscape.md:190 scores route 1 "LLM →
  constrained part-graph DSL → our solver" 5/5/5/5/5 and route 2 "CSG/OpenSCAD-Manifold" 4/3/4;
  the justification at 03:203-207: three.js topo weakness "is a property of *free-form*
  three.js, not of a compiler that only ever emits closed boxes and extrusions." CSG was
  demoted to "a correctness oracle even if we ship triangles" (03:166-169, 03:209-212). The
  **Style 3** score for CSG is uncited and, on the evidence of the result, inverted.
- **Open question never answered.** 01-source-repos.md:236-237 asked exactly the owner's
  question: "Does a hard-surface DSL need CSG (window holes, arched door) or is 'extrude
  profile with holes + inset boxes' enough … UNVERIFIED which wins." No later file answers it.
- **Plan axiom.** PLAN.md:9 "The LLM never writes geometry or a world coordinate"; 08:8 lists
  it as AGREE "treat as settled". PLAN.md:55-57 still promised `lathe, taperBox,
  extrudeProfile(+holes)` in the closed vocabulary.
- **Implementation shortcut.** prims.js:14 "M0 shipped box / bevelBox / plate. M2 adds prism /
  wedge / tube / stepStack"; prims.js:297 `BUILDERS = {box, bevelBox, plate, prism, wedge,
  tube, ring, stepStack}`. `extrudeProfile(+holes)`, `lathe`, `taperBox` were never built.
  M2-BRIEF.md:19-20 asked for a half-round arch "MVP-STUB if approximated by a box";
  grammar.js:362 and SPEC.md:309 ship the stub: "an arch head is a `wedge`… a real half-round
  needs an XY-plane extruder, which M2 does not add."
- **Validator lock-in (why it could not drift back).** SPEC.md:42-44 "Every prim fills its
  declared `dims` box exactly … because the solver measures contacts from `dims` and never
  looks at a vertex." obb.js:7-8, v2.js:40, v6.js:3-5 all `MVP-STUB: AABB not OBB`; V1
  (v1.js:1) demands each prim be its own closed manifold with declared genus. A subtracted
  reveal or a lofted cornice has no `dims` box, no per-prim genus, and no face frame, so V1,
  V2, V5, V6 and the attach solver (PLAN.md:64-87) all break. Windows are therefore a box
  "3 cm proud of the reveal so V6 cannot call it a duplicate" (SPEC.md:305, grammar.js:26
  `GLASS_PROUD = 0.03`) — the validator dictated the geometry, backwards.
- Verdict: **research conclusion → plan ruling by inheritance → shortcut → lock-in.** The
  quote that decided it is 03:203-207; the quote that admitted the cost is SPEC.md:309.

## 2. Was it right? Where it capped quality

Right for priority 1 (nothing floats, nothing thin — V2/V3/V5 do this cheaply, README:42
"V0–V7+V10 clean"). Wrong for priorities 2 and 3 once massing was done, and wrong on speed,
because the workaround for every missing operator is *more parts with hand-computed
coordinates* (17 treads, 2 stringers at `rot 121.391` for one stair; awning as three plates).

Impossible or faked in the current DSL, read off the target vs final-target.png:
- Window reveals/frames/mullions: target has recessed glass with pale frames and cross bars;
  result has flat dark rectangles proud of the wall. Needs subtraction or a frame profile.
- Arched doorway (target, right building): `lintel:"arch"` emits a wedge (grammar.js:362-369).
- Cornice/parapet profile: target has a stepped coping; result has one flat plate that on the
  tan building reads as an oversized grey slab.
- Fire-escape ironwork + ladder + ball-finial posts: bars are 0.12 m boxes at V5's floor
  (r8 ledger, fire-escape-open attempt 3); no ladder; no finials (needs lathe/sphere).
- Awning: composite wedge admitted "reads as a sloped canopy … without a second prim"
  (awning.json note); the winner replaced it with plates at `rot 12`/`-12` and `embed: 6`.
- Roof bulkhead louvre, AC grille: zone-only stripes (M2-BRIEF:35-36), no geometry.
- Mint side windows, basement half-window, bench: absent or stubs (README:42 "next items").
Net: massing/colour blocking ~ correct; every second-order feature is a box stand-in.

## 3. Process: where time and tokens went

Chronology (README Status + file mtimes + commits):
- 09-10 12:07–13:24: five research seats + two architecture seats + exchange + merged plan
  (~1,984 lines research/01–08; PLAN 245 lines). ~1.3 h wall, 8 model seats.
- 09-10 13:xx → 09-11 21:15: M0 (README:92). 09-11 21:15–23:10: M1 validators (1,589 lines
  src/validate), M2 grammar+composites+hand tenement, M3 gen pipeline (1,512 lines scripts).
  09-12 00:05–00:47: M5 vehicle, M6 DSL gaps. Harness/validator/test code ≈ 4,650 lines
  (validators 1,589 + tests 1,543 + scripts 1,512) vs 1,010 lines of compiler+prims.
- 09-12 10:23–19:48: eleven loop runs (runs/m4-tenement*/log.md `started:`), commits
  55563a9…e5384a9. Model-authored geometry across the whole project: one M3 builder run
  (README:56, 3 calls, 0 repairs), one M5 run, and 33 worker candidates (11 runs × 3).
- Tokens: no counter exists; cache/ + cache-astra/ + relay/ hold 29 files, 18.5 KB of
  prompt/response markdown — the model's total geometry output is smaller than PLAN.md.
  UNVERIFIED as token counts; the ratio is unmistakable: >90 % of spend was not the model.

Harness incidents, avoidability:
- **node_modules junction deletion** (r4 log:47, commit 586ac59): `git worktree remove
  --force` followed a junction and deleted the main tree's node_modules. Avoidable: the
  worktree design was chosen before checking how Windows junctions behave under removal; a
  one-line preflight ("worktree contains junction?") or a symlink-free install per worktree.
- **candidate dev server never came up** (r2, r4 voids; README:48 "node_modules/.bin was
  missing"): same root cause plus a missing `npm install` check in preflight. Avoidable.
- **adapter relative paths** (README:48 "adapters need absolute paths (worker cwd = worktree)"):
  avoidable by one dry run of the adapter from a worktree cwd before the first real round.
- **scope gaming** (worker-mix.mjs:29-33: an Astra candidate "removed the sidewalk apron" by
  patching build.js; r4 ledger attempt 1 "excluded the three apron meshes from rendered
  geometry"): foreseeable — the worker prompt never said "spec only". Three commits
  (586ac59, 6119f84, a657bfb) and two stalled runs (r5, r6 all "no change produced") to fix.
- **stacked merges** (WORKFLOW.md §3b; r8: props `embed ≈ 10 m`, 8312 tris; repair ace827c
  19:12 after last r8 merge 18:29): candidates cut from HEAD, winners merged into the working
  tree — foreseeable from 08:G2/G3's read of orchestrator.mjs; one item per invocation from day one.
- **occlusion by protrusion** (ace827c; grammar.js:118-123 MVP-STUB): a design gap, not an incident.
- **r8 void** (log:8 ERR_CONNECTION_REFUSED on 4210): baseline server down — same class as r2/r4.
Five of seven were plumbing, all detectable by one dry round on a throwaway item before the
real run; `dry run: no` on every log — the dry run was never used.

## 4. The loop: earned, or too early?

Cost: ~10 min/round by hand relay (WORKFLOW.md §6), 3 workers + 3 judges. Yield: 8 merges
in ~9.5 h; votes 3–0 in 7/8 rounds (r7–r11b logs), BASELINE worst 3/3 in r3 (README:48).
Items read "reads as a dark brown box, should read mint" (r7 items.json) — one-edit gaps the
lister had already diagnosed; the lister's text was the fix. Three judges never changed an outcome.

Applied too early. The invariants (worker never sees target, one item per round) fit the last
10 % of a look; for the first 90 % they cost 3 candidates × 3 judges to confirm an obvious edit
and forbid the worker the picture that would have told it the arch is round. sidewalk-apron
(r4 void, r5/r6 no change, r7 win — four runs for "delete three parts") is the cost made visible.

First-90 % path that was skipped: Astra sees the TARGET, authors the whole model in one or
three tiers, validators gate, owner looks at the still, Astra repairs from the owner's
sentence. Iterate 5–10 times in an hour. Then freeze and start the loop on residual gaps.
M3 actually did this once (README:56, 0 repairs, FINAL PASS) and stopped.

## 5. Model choices: did the constraints waste Astra?

Yes, twice over. (a) The DSL forbids the operators the model knows (boolean, extrude,
profile) and gives it `uv` on a face frame with align/embed/rot semantics it must reverse-
engineer from a 319-line spec; the shipped spec shows it computing world positions offline
and encoding them as `uv: [0.057895, 0.354722]` per tread and `rot: 121.391` — coordinates by
another name, unchecked by V0. (b) `embed: 6` on the awning plates (spec.json
`shop_awning_canopy`, `shop_awning_valance`) uses the contact-penetration parameter as a
translation, which V2 accepts because embed is self-declared. The "LLM never writes a
coordinate" guarantee holds only for the trivial parts; where the shape is hard the model
routes around the DSL and the validators cannot tell.

What to let it write instead: a **CSG program** — a small typed JS/JSON op list over
manifold-3d (`cube/cylinder/extrude(profile, holes)/revolve/union/difference/translate/
rotate/mirror/repeat`) with named parts and `attach`-style helpers kept as sugar. Correctness
then comes from the *result*: watertight union, component count, thickness, contact — the
same V-codes, computed on the mesh instead of assumed from `dims`. 02-correctness.md:78,
03:166-169 already identified manifold-3d as the oracle; it was demoted to a "flagged
cross-check" (PLAN.md:107, v3.js:7 DEFERRED) and never wired in (package.json has no manifold
dep). Procedural JS with a validator after (route 4 in 03:190, scored 2 on correctness) is
the same idea without the manifold guarantee — worse. Raw mesh ops: no.

## 6. v2, concretely

- **Representation:** hybrid. Massing + facade grammar stay declarative (they work: CGA-lite,
  occlusion, repeat). Every *element* and *prop* is a CSG program over manifold-3d: window =
  `difference(wall, reveal) ∪ frame ∪ glass`; door = arch profile extruded with a hole;
  cornice = profile extruded along the parapet; awning = lofted profile; railing = union of
  extruded bars. Astra authors part programs; the compiler resolves placement as now.
- **Validators kept:** V0 schema/DAG, V3 connectivity (now = manifold union component
  count, the oracle it was always meant to be, 03:166), V4 ground, V5 min feature (on the
  union mesh, screen-space), V7 role scale, V8 visibility, V10 export hygiene. **Delete:** V1
  per-prim genus (manifold-3d guarantees it), V2 sampled contact and V6 AABB overlap (both
  become union/intersection volume queries), obb.js, repair.js auto-nudges, the `embed`
  parameter (a penetration the author declares is a penetration the author can fake).
- **Loop:** Phase A, not blind — Astra sees TARGET, owner sees still, ≤10 iterations, stop at
  owner's "reads as a tenement". Phase B, Blind Loop as designed, items from a lister diff,
  one item per invocation, 1 judge run unless the vote is within the config's tie rule; add a
  dry round to preflight. Judged criteria unchanged (WORKFLOW.md:20-29).
- **Delete:** composites-as-spec-fragments library (replace with CSG functions), the
  file-relay by-hand channel (WORKFLOW §2 option 2) once `codex exec` is on PATH, M5 vehicle
  generality until the building look is accepted, the 20-fixture V-code suite for V1/V2/V6.
- **Keep** fixed capture, frozen refs, limits.json, one mesh/material/GLB, relational placement
  — enforced: V0 rejects `uv` with >3 decimals and `embed` > child depth (no smuggled coordinates).
