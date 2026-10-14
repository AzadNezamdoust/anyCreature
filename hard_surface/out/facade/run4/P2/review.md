# Fable review — P2 ironwork (run 4)
| # | Row | Verdict | Note |
|---|---|---|---|
| 1 | orientation | PASS | unchanged |
| 2 | door side | PASS | unchanged |
| 3 | reads as the target | PASS with residual | roof ladder on the side wall behind the corner, two open landings with a flight between them, drop ladder over the sign band, tall window slots, sign + AC + awning stack — the brick tenement at a glance. Residual (not worth a seat): lower landing iron 0.76× target value (k-means split artefact on the shaded underside), AC hue 33° (grey tint), AC ~1.6× the target's on-screen size. |
Measured: gate PASS (213 parts, 2980 tris), layout PASS (all measured keys), likeness: brick/glass/iron/green families inside ±30 %; 3 minor rows above. Workflow fixes taken this run: pass.mjs refuses items citing unverified keys (fired correctly, 0 seats spent), calibrate-palette now runs before the gate (colour is never the seat's job), thin-role visibility pooled.
