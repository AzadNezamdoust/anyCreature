# hs.py stress test — findings (2026-10-10)

Harness: `fuzz_helpers.py` (Blender), `run_fuzz.py` (8 workers), `report.py`, `compare.py`. Data: `out/fuzz/` (git-ignored).
Runs: main 4000 (Freestyle probed), safe_a / safe_b / safe_b_fx 4000 each, fx_* fix trials 4000 each (fx_weld2 1900, fx_dissolve 3700).
0 crashes, 0 hangs. Topology counters = run_pass.topology_report (lifted by ast).

## Failure rates (main)
- true defect 26.8 % (strict run_pass incl. its 1e-8 m2 zero-area rule: 56.1 %; that rule flags legit small triangles on 10-50 mm parts)
- empty material slot after a boolean: 90.2 % (95.4 % of cases with a boolean)
- nonmanifold 10.8 %, edges>2 7.9 %, boundary 3.9 %, loose 3.4 %, negative volume 2.6 %, Freestyle "edge appears twice" 15.4 %

## Top findings
1. Every boolean leaves an empty material slot (`hs.cut` cutter has no slots). Fix: cutter carries the target's slots, drop None slots after apply: 3607 -> 0, 200 defects fixed, 0 broken.
2. bevel_mod after booleans is the main breaker: 16.6 % defects after a boolean vs 2.5 % on a primitive. Bevel-then-cut 19.2 % vs cut-then-bevel 26.8 %. Segments 1: 7.7 %, 2-3: ~20 %. Grows with tris before bevel (<=100: 5.5 %, >1000: 60 %) and width / thinnest dim (>0.4: 19.6 %).
3. mirror_x with the inner face within 0.01 mm of x=0: 75 % defective (doubled inner wall).
4. Near-coplanar cutters: defect 9.5-12.4 % within 1e-5 m of a face, 2.9 % beyond 1 cm. Tangent cylinders 11.5 %.
5. Primitive cliffs: box chamfer >= 0.49 x thinnest side (77/84 dirty); tyre hw < 0.045 (74-92 %); wire_cage thickness > 0.4 width (71 %); collapsed loft end ring (100 %).

## Builder rules (safe ranges; safe_b cut true defects 25.9 % -> 6.2 %)
| rule | value |
|---|---|
| cutter vs each target face | >= 1 mm past (or short of) the surface; no tangent cylinders |
| bevel width / thinnest dimension | <= 0.25 on an uncut primitive, <= 0.1 after a boolean (never >= 0.45); >= 0.3 mm per segment; 1 segment (2026-10-11 per-step re-read below) |
| order | bevel the primitive first, then cut; one hs.cut per boolean, no stacked boolean + bevel |
| mirror_x | inner face >= 1 mm from x=0, or crossing it by >= 1 mm |
| box(chamfer=) | <= 0.4 x thinnest side |
| tyre | hw >= 0.05 |
| wire_cage thickness | <= 0.1 x width |
| loft | no collapsed ring |
| materials | give cutters the target's slots |

## Fix trials (paired, baseline 25.9 %)
cutmats+popnone 20.9 % (200 fixed / 0 broken) · mirrorfix 21.2 % (203/16) · precut 21.0 % (201/4) · all four (fx_combo) 19.5 % (277/20, recommended) · bigger weld trades slivers for nonmanifold (no).
Proposed hs.py guards: `out/fuzz/proposed_hs_guards.diff` (material / mirror / weld logic = tested fixes; bevel clamp, chamfer clamp, tyre scaling NOT run as code).
Caveats: Freestyle probed only in main; single-object cases; finish-time cleanup changes vertex counts of existing builds (re-run --final before trusting stored numbers).

## Applied (2026-10-10)
All guards of `proposed_hs_guards.diff` are in `scripts/hs/hs.py` behind `hs.begin(..., guards=True)` (default off; `HS_GUARDS=1` forces on).
The material fix is guarded too: 7 finished builds fill the empty slot themselves after a cut, so dropping it would change their slot lists.
- Guards off: `matfix_all.py` -> all 30 finished builds identical to the pre-guard hs.py (order-invariant `canon`, slot lists); `regress.py` -> apc_8x8, main_battle_tank, transport_heli, pistol, gatling_gun, ray_pistol reproduce stats.json exactly (tris, topology per object, iou / agree per view). Builds are not face-order deterministic run to run (orig vs orig: 22 parts reordered, same coordinates).
- Guards on vs off, 1000 paired cases (`g_off` / `g_on`, no Freestyle): true defect 20.8 % -> 16.7 % (53 fixed / 12 broken), material fails 90.1 % -> 0, neg volume 2.4 -> 0.5 %, nonmanifold 10.1 -> 7.9 %. Per guard (`guards_report.py`, `out/fuzz/guards_report.md`): bevel clamp fired 159x, 30.8 -> 25.2 % (13/4); box chamfer clamp 30x, 30.0 -> 13.3 % (6/1); tyre hw < 0.045 94.7 -> 36.8 % (12/1), tyre 0.045-0.2 32.5 -> 30.0 % (5/4); mirror_x 26.0 -> 16.8 % (28/5).
- Guards on, apc_8x8 run_pass: tris, topology and every iou / agree identical; 3 empty slots dropped; rear_door's own normal-based tone split picks other faces after the guarded finish() weld.

## Bevel width re-read (2026-10-11, main + safe_a + safe_b + g_off + g_on, per evaluated step from a clean state)
1-segment bevel_mod on a primitive (no boolean yet): ratio 0.00-0.05 0.2 % (n 2243), 0.05-0.10 0.7 % (1146), 0.10-0.15 0.9 %
(2466), 0.15-0.20 1.7 % (60), 0.20-0.30 0 % (80), 0.30-0.45 0 % (54), >= 0.45 3.1 % (131). After a boolean: 8.1 / 9.1 / 7.5 /
12.6 / 11.2 / 16.0 / 10.6 %. The width is not what breaks a bevel; the boolean before it is. hs.bevel_mod's safe range is
now 0.25 x thinnest on an uncut primitive (BEVEL_SAFE_PRIM), 0.1 after a boolean (BEVEL_SAFE_CUT).
`test_big_chamfer.py` (12-20 mm main-mass chamfers, seeds 7 / 11 / 23, n 400 each): 0 defects on 596 bevelled primitives,
300 box(chamfer=), 604 bevel-then-cut cases.
