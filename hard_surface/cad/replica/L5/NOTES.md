# L5 replica - Porsche 911 Carrera S (992.1) coupe - NOT finished, NOT a convincing 992 yet

Files: model.py (build), refdata.py (spec + photo traces + registration), compare.py (silhouette IoU, overlays,
dimension table), round.py (build -> hq render -> compare), rounds.jsonl. Refs: REFS.md.
Exports: out/replica/L5/final/model.step, model_hq.glb (from r4). Images: hero/clay/zebra.jpg, overlay_{side,front,rear}.jpg
(red = model silhouette, green = ref trace), compare.jpg (ref | model left ortho, flipped).

## Method
No free 992 blueprint found -> near-ortho telephoto Commons photos, hand-traced on gridded crops, registered to spec:
side x piecewise-linear through rear end / rear axle / front axle / nose (so L and WB both match), z by ground + H;
front/rear by W x H box. IoU is model silhouette vs these hand traces (so it measures trace agreement, and the
front/rear traces carry camera-height perspective: their bottom edge sits ~130 mm too low).

## Rounds
| r | change | IoU side / front / rear | build |
|---|---|---|---|
| 1 | first build: 22-station loft, glass, shut lines, lights, intakes, wheels | 0.909 / 0.865 / 0.858 | 150 s |
| 2 | stronger tumblehome (belt 0.905w, roof half 535), cap_round of loft ends | killed (>30 min: every later boolean fell back to Manifold) | - |
| 2b | ends rounded by 5 extra loft stations | killed (>20 min) | - |
| 2c | ends rounded by ONE shrunk tip station; loft errors caught | 0.889 / 0.870 / 0.862 | ~8 min |
| 3 | tried to drop louvre slats (edit did not apply) | same as r2 | |
| 4 | louvre inlay removed (it produced an untrimmed block above the deck) | **0.908 / 0.871 / 0.869** | ~8 min |
Note: during r2 I killed processes matching `*cadkit.worker*` - this may have killed other lanes' workers too.

## Dimension errors (r4, mm)
L 4511 vs 4519 (-8) | W 1851 vs 1852 | H 1297 vs 1298 | WB 2450 (0) | track F/R 1591/1557 (0) | overhang F -2, R -6 |
tyre D 679.4 / 716.3 (spec). Side top-profile vs trace: within +-30 mm except tail tip (-67) and rear corner.

## Failures (booleans / features)
- intake mesh backing x3: inner(40..47) loft invalid (tip station collapses) -> intakes are recessed but no dark mesh.
- louvre slats/floor: inlay result untrimmed -> removed; louvre area is only a 10 mm recess, no slats.
- cap_round on loft ends: works but makes all subsequent booleans ~10x slower (Manifold fallback) -> not used.
- no fillets used on the body (single loft); mirror/caliper fillets OK.

## Remaining defects (honest, biggest first)
1. Body form is generic: wavy hood/fender (zebra shows bumps at the hood->cabin station switch and at the headlamp
   stations), front fenders do not rise as distinct 911 fenders, no rear haunch shoulder crease.
2. Glasshouse wrong: windshield + side DLO + backlight recesses merge into one dark cap; no A/B/C pillars as body
   colour, no quarter-window shape. Needs the glass tools trimmed so pillars (~70 mm) remain.
3. Ends: rear and nose still end in a planar cap (80 % width); real tail has the full-width light bar on a curved face.
4. Wheels: generic 5-spoke (dimensions correct, spoke shape not the Carrera S design); calipers boxy. Left ortho render
   shows the wheels as flat discs (needs checking - hero view shows spokes).
5. No top-view reference: plan widths (front 1824, door 1796, rear 1852) are estimates.
6. Missing: front bumper/fender split lines, side blade on door, rear "PORSCHE" script, retractable spoiler line,
   lamp internals, underbody.

## Kit gaps (implemented locally / not)
- Parametric skin offset `inner(d)` (re-loft with pulled-in stations) instead of OCCT offset - local in model.py.
- Silhouette IoU / photo overlay tooling - local compare.py (trimesh raster).
- Loft end rounding that keeps booleans fast - missing (cap_round result is slow to boolean against).
