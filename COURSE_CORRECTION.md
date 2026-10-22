# Course correction (2026-10-22, two independent Opus audits)

## CAD app (hard_surface/cad) — alignment 5/10
Goal: Plasticity-class modelling capability, clean-room, ideal for LLMs; replicate REAL products.
Drift: game/bake pipeline (parked, frozen); parity-row counting (75 "works" but replicas 1-3/10);
first L1-L5 ladder was invented designs (superseded by replica ladder).
New gate per model (all required): IoU on every ortho view; named-feature checklist within +-1 mm;
fillets at requested radius (silent shrink = fail); 0 Manifold fallbacks, valid B-rep; zebra G2 on
main surfaces; blind Opus side-by-side >= 7/10. Judge every round, not at the end.
Order: 1 kernel robustness (fillet radius, booleans w/o mesh fallback, no twisted lofts; L3/L4/L5
failures as regression tests) -> 2 class-A surfacing (network surfaces, G2 blends) -> 3 gate ->
4 ONE product (G502 or DCD777) with proper ortho refs to 7/10 -> 5 feature ops (lip, boss, rib,
split line) + attempts-per-feature metric. Car last.
STOP: baking work, parity counting, IoU-only claims, 5 parallel replicas, global worker kills,
local kit forks. One kit owner; replica lanes file gap tickets.

## Creatures (creatures/) — alignment 6/10
Drift: too many shape challengers (all lost to Hunyuan3D-2.1); box-model track stalled though Azad
called it best; recent time went to CAD.
Process: judge noise ~0.7 (same r9 meshes 5.5 vs 6.0) -> settings sweeps under that are noise; no
fixed AAA anchor; boxmodel r20 judging leaked titles + used Fable readers (redo with Opus);
8 GB is EMULATED only, never say verified.
Biggest blocker: reference images (HunyuanDiT fails anatomy, e.g. roach -> bee).
Order: 1 ref stage: commercial-safe local image models + Opus anatomy-critic gate (roach test) ->
2 real 8 GB / 2070M run of the wolf -> 3 box-model: list Azad's technical errors as kit gates, fix,
rerun r20 blind with Opus, compare vs Hunyuan -> 4 hybrid lane (box-model blockout <-> Hunyuan
detail) -> 5 judging: fixed AAA anchor + control in every round, report delta; albedo-lighting check.
STOP: new shape-generator challengers (close D3D-S2 tuning when it ends), sub-noise sweeps.
