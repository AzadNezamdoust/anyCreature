# blueprint_fit A/B: griffin (2026-10-22)

**Technique:** a typed parametric blueprint, `griffin/griffin_bp.py` plus `blueprint_typed_base.json` and `blueprint_fit.json`. It holds:
- spine samples, with named rings, centre, tilt, top and bottom, width and profile;
- the limb graph, with the root region and the leg sections;
- the wing keys;
- ratios.

**Fitter:** `tools/fit_griffin.py` is a silhouette-fitting optimizer. It runs a pattern search on 30 parameters:
- 9 knots for each of W, T and B along the spine;
- the fore and hind leg radius;
- the wing lift.

Topology is fixed. It fits against masks taken from the sheet (`tools/sheet_masks.py`). The silhouettes it optimizes are a surrogate: hulls of the sections plus the fixed pieces. Real IoU is measured on the GLB at rest pose, at 5 mm, with `tools/glb_iou.py`.

**Inputs:** A = `t7x/zoo/griffin` (untouched), B = `t8/blueprint_fit/griffin`. Same sheet, same code apart from the tables, same S2–S4 and the same render settings.

| measure | A baseline | B blueprint_fit (r2) |
|---|---|---|
| IoU side / front / top (S4 GLB vs sheet mask) | 0.745 / 0.798 / 0.837 | 0.759 / 0.790 / 0.821 |
| mean IoU | **0.793** | **0.790** (-0.003) |
| surrogate IoU mean (what the fitter optimized) | 0.769 | 0.797 (+0.028, did not carry over to the GLB) |
| kit gates S1–S4 | PASS | PASS (S1 r1 failed: 14 self-intersecting pairs, a fat foreleg in the belly; fixed by growing legs outward) |
| junction probe S4 | PASS (all) | **FAIL** tail0 seam strip 1.75 r (r1 also had a shoulder knife of 1.26 r at 119 deg, fixed in r2) |
| detail gate | FAIL: 4 hind claws 17 mm < 18.2 mm | same 4 (claws unchanged) |
| eye | PASS 0.57/0.85/0.59 | same |
| tris S4 | 4394 | 4394 |
| rounds | n/a | fit plus 2 full S1–S4 rounds (one repair) |
| cost | n/a | about 2.5 h wall time, most of it the first Powell attempts (stalled on the flat raster objective) plus a shared, loaded machine. Final fit 270 s, S1–S4 about 2 min |

**Fitted params (r2):**
- kW = 1.0, 1.025, 1.075, 1.075, 1.05, 1.0, 0.975, 0.975, 0.975;
- kT and kB stayed at 1.0;
- fr = 1.0 (set by the repair), hr = 0.9;
- wing lift +8 cm, at its bound.

**Judge:** one fresh Opus seat, owner rules plus the sheet as referee.
- Order 1: TIE. Order 2: TIE.
- The sheets look almost identical. B is a touch broader in the rear views, but its wing step is more visible.
- Result: no preference, so the tie goes to the baseline.

**My read:**
- B's wings sit higher and wider, and the torso is about 5–7 % wider mid-body.
- The thin, long barrel the owner flagged is NOT fixed. The fitter did not move T/B: the side gap is mostly the unbuilt far hind leg and the low belly.
- The surrogate overestimates gains: its top view is +0.018, but the real top view is -0.016.

**Verdict: REJECT.** It brought no IoU gain on the real mesh, broke a junction gate (tail strip), and the judge tied in both orders.

**Reusable:** the sheet-mask extractor and the GLB IoU tool. A fit would need the real Blender silhouette in the loop, or a better surrogate with junction constraints, to be worth retrying.

The eagle was not run (budget).

Files:
- `ab_compare.jpg`: orbit18, game 192 px and the silhouette overlays for A and B;
- `griffin_ref/` (masks, overlays, fit.log, r1 blueprint);
- `griffin/`.
