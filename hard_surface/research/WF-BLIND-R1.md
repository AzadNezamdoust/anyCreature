# Blind-test round 1 — examiner merge (Opus 5, 2026-09-13)

Owner rule: the workflow passes only if blind TEST models (Gemini 3.8 Flash High, GPT 5.6 Terra) produce good
models through it. Examiners (Opus 5, GPT Astra high) fix the WORKFLOW; never tune for one model.

Run examined: pickup P1 details, Gemini, blind, text contract — FAIL. Evidence `out/blind/pickup/agy/P1-run1/`,
`out/blind/pickup/agy/first-seat-P1.mjs`. Examiner audits: Opus (in-session diagnosis) and
`out/blind/exam/astra-pickup-P1-run1.md` (GPT Astra high).

## Already fixed or in progress (examiner job 1)
- Repair guard: a module that does not load is worse than any loading module (pushed 57a1f91).
- V3 report names every lump and the closest gap between the two largest.
- Syntax pre-check of a text reply with one syntax-only retry that does not consume the repair.
- Vehicle groove rule `{GROOVE_DEPTH_MAX}`: panel lines are shallow grooves, never cuts through a base or seat.
- Template wheel visibility matches the target's visible wheel count; new frozen start `out/blind/pickup/start-P1.mjs`.
- Dot-aware key-list parser in pass.mjs.

## Examiner job 2 (after job 1), ranked
| # | Gap (evidence) | Change |
|---|---|---|
| B1 | Panes seated 1 mm behind the recess floor pass contact (≤ epsAbs) yet fail V3's one-component union (Astra 1; F:80–101) | Author rule in the class files + kernel README contact section: "Every structural part must join the solid union; a positive gap fails V3 even within contact tolerance. Seat a part with a positive overlap no greater than {INFERRED_CONTACT_FRAC} of its volume." Expose the token. Add a pane-in-recess example to classes/vehicle.md. |
| B2 | P1 cites measured keys only for lamp height/spacing and mirror height; window bounds, lamp diameter, mirror head size, arm length, grille size absent → guessed, lamps and mirrors undersized (Astra 2) | (a) measure-vehicle: add the appearance keys the target supports (window bounds per pane, lamp diameter, grille w/h, mirror head w/h) with evidence; freeze. (b) passes.json gains explicit `requiredLayoutKeys` per pass (replaces substring discovery in pass.mjs) and optional `constructionDefaults` (labelled numbers for non-appearance construction such as recess depth). The prompt prints both. Rule sentence: "Use supplied measurements for appearance and labelled defaults for construction; if a required appearance dimension is absent, return MISSING KEY." |
| B3 | Handoff contradictions: template header "Do not hand-edit: re-run the template" vs a pass that edits; missing P0 review indistinguishable from a clean one (Astra 3) | Template header for author-facing modules: "Generated starting point; edits required by this pass or its LOOK failures are allowed." pass.mjs: a missing previous review is printed as `PREVIOUS REVIEW: UNREVIEWED`; a review with no FAIL rows prints `PREVIOUS REVIEW: no failed rows`. |
| B4 | Hidden acceptance: visible-instance counts, 50-px threshold, LK value/hue/area bands never shown; LK_VISIBLE suppressed until the final pass even for roles already built (Astra 4) | pass.mjs prints a compact `# ACCEPTANCE` table generated from the same likeness config (per due role: census count, visible instances, px threshold; value/hue/area bands). likeness staging: LK_VISIBLE for a role is judged from the pass where its census key becomes due, not only at the final pass. |
| B5 | Prompt clutter/contradictions: generic README `meta.front "-Z"` then vehicle override; "no literal vertex arrays" vs documented profile points; `touches` only with `embed` vs helpers using bare touches; architecture assemblies with building roles shown to a vehicle author (Astra 6); prompt 23 kB | Class-selective author README: kernel API core + class file; building-only sections (frame −Z, assemblies with building roles) only for class building. Array-ban sentence → "No raw 3D mesh vertices or indices; numeric 2D profiles for K.profile.poly, K.extrude and K.revolve are allowed." One touches policy stated once and templates normalised to it. Report prompt bytes in timings. |
| B6 | Evidence loss: only the final module is kept; after a capture refusal the report cannot certify the repaired candidate (Astra 7) | pass.mjs keeps every attempt under one identity: `attempt-1/{module, report.json, stills, likeness.json}`, `attempt-2/…`; a capture refusal marks likeness UNVERIFIED for that attempt instead of repeating stale measurements. |
| B7 | Lamps/mirrors poorly measured (off the flank quad; mirrors share glass family) (Astra 5) | Deferred to job 3: subject-defined measurement faces + per-feature silhouette checks. For now, LOOK rows for lamp size, mirror shape, window borders, panel-line readability in classes/vehicle.json. |

## Protect (what the blind model got right — regression expectations)
Orientation `+X`, palette zones, open bed, three recessed panes, symmetric round lamps, slotted grille, mirrored
arm+head assemblies; 30 parts / 2392 tris; window/lamp/mirror visibility and colour rows passed.

## Rerun plan after jobs 1–2
Blind Gemini then blind Terra, pickup P1 from `out/blind/pickup/start-P1.mjs`, via `scripts/blind-test.mjs`.
Blind Gemini then blind Terra, building P2 from `out/blind/facade_brick/start-P2.mjs`. Examiner review of each
(Opus look + Astra audit on failure). Verdict per owner rule reported with side-by-sides.
