# WORKFLOW v3 — hard-surface modelling by any LLM, measured end to end (Fable merge, 2026-09-13)

Inputs: `out/wf-loop/general/fable-general.md` (Fable 5.1 seat) and `out/wf-loop/general/astra-general.md`
(GPT Astra high, 496 s, 191 182 tokens; one earlier attempt died mid-read). Owner: "this is the best so
far, small improvements can be done … set up in a way that will create great results on any hard-surface
modelling … optimize workflow for any llm." Where the seats disagree it is marked; otherwise both say it.

## 1. What produced the result (causal spine, both seats)

1. **Representation.** A closed kernel with real booleans and profiles (`src/kernel/`) instead of the v1
   box DSL. v1 spent 59 loop-minutes and never made a reveal, arch or cornice; v2 made all of them in five
   passes with zero repairs. Nothing else works without this.
2. **True colour.** Flat, unlit capture (`src/material.js` captureMaterial, `app.js`). Until r2 the
   renderer darkened the populated face to 0.51× and the palette seat took the blame.
3. **True numbers.** `scripts/measure-target.mjs` measures the target on the rectified front plane and
   writes every layout key with evidence; the gate enforces measurements, not audit guesses. Run 3 passed
   every rule while windows were 1.75× too wide; run 4, built to the measured keys, is the accepted one.
4. **Buildability gates** (closed roles, staged census, bearing, contact on real surfaces, undeclared
   penetration = 0, ladder access, deck gap) turned run 1's 13 impossible constructions into impossible
   outputs. They cost repairs when they had bugs (staging, ladder head zone, census pad).
5. **Author sees the target and its own render**; refusals (camera, `--check`, unverified keys) stop
   seats being spent on a workflow that cannot be satisfied.
6. **The audit loop** found what each round froze wrong (r1 recess rule, r2 guessed layout, r3 fallback
   quad). Each round also introduced its own defect — the loop is the correction, not a guarantee.

Not demonstrated: pass merging saved tokens (run 4 cost 350 k vs run 1's 219 k — repairs and repo
reading, not passes, dominate); images vs the numeric table in the repair (arrived together).

## 2. Generic vs per-subject

**Generic:** kernel + profiles, `check-module`, V1/V5/V2/V3/V6/V4/V10, capture contract + idpass, flat
paint, Codex runner + header assertion, K=1 repair slot, measure.mjs, likeness mechanics (mask, k-means
zone split, quad classifier). Astra caveat: MIN_FEAT 0.06, V5 and bearing on AABBs, closed roles and
census rules are still *building* constants inside those "generic" files.

**Per subject (files):** `subjects/<s>/{census,regions,layout,layout.measured,passes}.json`,
`refs/<s>.png`, `refs/<s>.camera.json`.

**Per subject but hard-coded, must be lifted before subject two (Fable §2 list, Astra concurs):**
`SUBJECT`/`TARGET` constants in pass/likeness/compare, absolute repo path in capture2, ROLES /
BEARING_ROLES / CENSUS_RULES / LAYOUT_RULES in kernel-chain, ROLE_ID_COLOURS in app.js, ZONES in
calibrate-palette, AREA_FAMILIES/CENSUS_ROLES/IRON_ROLES in likeness, every scan range and zone name in
measure-target, the building rules in the kernel README.

**Hand work that remains and its replacement (with evidence):**
| hand work today | replacement |
|---|---|
| census counted by seats at 2× zoom | one vision call returns `{count, bbox px per instance}`; a count without boxes is refused |
| regions.json rects seeded from an audit | committed placer script emits patches with purity + provenance + family |
| front-face contract chosen by audit | camera solve emits `faces[]` quads; author declares `meta.front` per face |
| face quad fallback in likeness | `measure-target` emits `faceQuadPx` (the fix is ~10 lines at `frameRecord`) |
| `MISSING KEY` write-only | consumer appends to a measure backlog; an item citing a key reported missing twice is refused |
| author guesses where a key is unverified | class template default marked MVP-STUB, never a seat |

**Reference packet** (`refs/<s>/packet.json`, generated, versioned): `class`, `camera` {θ, φ, mX, mZ,
residual, provisional:false}, `scale` {status observed|inferred|unknown}, `faces[]` {quadPx, W, H,
visibleMask}, `silhouette`, `landmarks[]` {px, family, evidence}, `families[]`, `zones[]` {patches,
median, purity}, `census[]` {role, count, instances[] {bboxPx}}, `layout{}` {value, unit, tol,
evidence | unverified+reason}, `relations[]` {contact | mirror | joint | clearance}, `passes[]`
{requiresKeys, introducesInstances}, `deferredByRuling[]`. A class prior `classes/<class>.json`
supplies roles, contact/bearing rules, census kinds, measured keys, camera preset, symmetry rule,
style floor, V7 bands. Priors select rules; they never fabricate observations (Astra).

## 3. Author-model agnosticism

What binds today: the runner is `codex exec` with a hard model assertion; the seat is a shell agent that
reads the repo at will (15–18 shell calls per seat, 80–90 % of billed tokens are self-directed reading,
not the contract); the author invents an AABB auto-`touches` crutch to survive V6; frame idioms are
learned by trial; `meta.census:false` / `meta.layout:false` / `triBudget` let the author relax gates.

Contract that fits any model (both seats):
- **Text-in, text-out seat.** Inputs: class README subset (≤120 lines), current module, item citing keys
  only, previous FAIL rows, ≤3 images. Output: whole module + `CHANGE:` + `MISSING KEY`. The harness runs
  check-module, the chain, capture and likeness — the author never runs anything. Adapter signature
  `{prompt, images, workspace, limits} → {artifact, change, missingKeys, usage, failureClass}`; verify the
  requested model's identity per adapter, no global provider.
- **Harness infers `touches`** from the measured contact graph V3 already builds; author declares `embed`
  only. Gate-relaxing flags move to harness config.
- **Kernel helpers for repeated topology** (`K.grate`, `K.flight`, `K.ladder`, `K.frame`): the r1 trigger
  ("author fails the rows twice") has fired (runs 3 and 4 iron rows).
- **Prompt constraints generated from the same config the gates read** — the 0.04 m bars vs MIN_FEAT 0.06
  contradiction cost 171 V5 rows and a repair.
- **Token line:** README 10 KB + module 16 KB + item ≈ 8 k in, ≈ 4 k out; repair prompt carries a diff,
  not the module twice. Report input / cached / output / reasoning separately (the `tokens used` scalar
  hides this). 15 k/pass stays unratified; ≈ 20 k is the realistic line.
- **Rows that catch a weaker author** (all measured): V7_ROLE, V12_CENSUS, V12_LAYOUT, V6 undeclared,
  V11 bearing, V5, LK_VISIBLE per instance, LK_AREA on a measured quad, V10, check-module bans.

## 4. Seat waste (run 4, both seats)

350 478 tokens, 1 571 seat-seconds, 3 repairs. Deterministic work done by seats: sideTint (P0 repair),
glazing/AC hex (P1 repair), iron colour + bar size (P2 repair). Three identical preflight refusals were
retried (stop retrying deterministic failures). LK_AREA ran on a fallback quad. `PASS with residual`
is not a verdict the harness recognises: define `FAIL | REVIEW_PENDING | ACCEPTED_WITH_RESIDUALS |
PASS`, bound to artifact + packet + capture hashes. Template candidates (no seat): massing, openings +
frames + sills, bands (sign/awning/AC), palette, sideTint, fixtures as boxes. Judgement stays for:
ironwork topology, fixture shapes, hidden geometry, unverified keys.

## 5. Next subjects (seats disagree on order; ruling below)

Fable: mint corner → pickup → vending machine. Astra: pickup → robot → mint corner.
**Ruling:** pickup truck first (a second CLASS proves the packet + class prior; v1's truck "passed" with
hidden wheels — the wheel-exposure contract retires that), then mint corner (two faces, mitre, per-face
census), then vending machine (single-material prop; first subject whose packet is 100 % scripted),
robot last (joint frames + mirror after the packet is proven scriptable).

| subject | packet additions | new rules | retiring check |
|---|---|---|---|
| pickup | wheel instances (centre, radius), axle frames, symmetry plane, wheelbase, clearance | ground contact = wheel bottoms; V9 mirror blocking; wheel diameter band measured | 3 wheel instances ≥ 50 px visible + `wheel.diameterOverL` in tol |
| mint corner | `faces[]` ×2, per-face census/centreX | V12 scoped by face; V6 on mitred coping | both quads emitted by script on an unseen target; `--check` PASS |
| vending | one quad, zones == families | LK_AREA on front quad; geometry masks where colour cannot split parts | packet produced with zero hand-placed rect |
| robot | joint graph, limb frames, mirror pairs | joint coincidence, pose-aware contact | mirrored-limb pair test |

## 6. Target-state workflow (one page)

| stage | owner | in → out | gate |
|---|---|---|---|
| S0 Scope + intake | owner + script (`make-target`, `solve-camera`) | target PNG, class, exclusions → packet {camera, faces[], silhouette} | camera solved, residual ≤ 1 px, quads present, else refuse |
| S1 Measure | script (`measure-target --class`) + ONE vision call for counts | packet → regions, census (with instance boxes), layout {evidence \| unverified} | `--check PASS`; no key without evidence; count without boxes refused |
| S2 Template | script (`template-<class>.mjs`) | layout + census + palette → BASELINE module | chain PASS, colour rows PASS, 3× capture identical; **no seat** |
| S3 Author | author model via adapter (any vendor) | README(class) + module + item(keys) + failing rows + 3 images → module + CHANGE + MISSING KEY | check-module → chain → capture → likeness; K=1 repair with own stills; ≥3 blocking rows after repair → back to S2 with the item split |
| S4 Review | judge model (Fable) + owner still | front-quad compare + likeness table → `review.md` row 3 with the cited parameter | numeric PASS never overrules a visible mismatch; FAIL reopens the parameter, never adds a feature |
| S5 Workflow loop | author-family audit + judge audit → Fable merge → Opus → fixture test → rerun | audits on finished stills | ONE harness change per round with a fixture; no harness edit mid-run (a mid-run fix voids the run, restart at S2) |

Cadence: S5 after every subject. Done for a subject: S4 row 3 PASS + owner sentence + ≤ 1 repair per
seat. Done for the workflow: two consecutive new subjects reach that with zero harness edits during the
run and ≤ 60 k seat tokens per subject (unratified). Budgets: 15 min per seat, 3 seats per subject, 1
repair per seat; a hit ends the run and hands off.

## 7. Implementer list, in order (small improvements first, as the owner said)
1. `measure-target` emits `faceQuadPx` (kills the likeness fallback).
2. `passes.json` P1/P2: mangled sentence; 0.04 m → cite MIN_FEAT from config.
3. calibrate-palette writes `meta.shade.sideTint` from `sideOverFront`; runs after every author mutation.
4. Verdict states + hash binding in pass.mjs; stop retrying deterministic refusals.
5. Lift SUBJECT/paths/constants into packet + class prior (`classes/building.json`).
6. `MISSING KEY` consumer + backlog.
7. Text-only seat contract + adapter; harness-inferred `touches`.
8. `template-building.mjs` from run 4's generic loops; face-aspect key.
9. Kernel helpers `K.grate/flight/ladder/frame`.
10. Pickup packet + class prior; wheel-exposure test.
