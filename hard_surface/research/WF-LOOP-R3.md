# Workflow loop — round 3 merge (Fable final, 2026-09-13)

Inputs: `out/wf-loop/r3/fable-audit.md`, `out/wf-loop/r3/astra-audit.md` (434 s, 112 775 tokens).
Run 3 passed every measured row and both seats still rank likeness gaps above minor. Both say the same
thing: **the numbers the gate enforces were never measured.** Round 2's `layout.json` was seeded from an
audit that read pixels over the front-PLUS-side box (261 px) instead of the front plane (208 px), so every
fraction along W is wrong; the orchestrator (me) typed a depth of 1.8 W with no evidence and cost two seats;
the gate then made the author match the guesses to ±0.05. Fable measured (scan numbers, camera-rectified):
window glass 0.09 W × 0.13 H at 0.24 / 0.815 W from street-right, head 0.035 H, pitch 0.28 H; sign box
0.07 H tall, top 0.365 H; awning band 0.16–0.28 H; storefront 0.145 H; door ≈ 0.17 H; landing tops 0.085 H
BELOW the window bottoms; crown 0.027 H; depth 0.89 W; roof ladder on the SIDE wall 0.18 W behind the front
plane; iron 6.2 % of the front quad vs ours 12.7 %; side/front value 0.786.

Rule of round 3 (Fable M2, Astra C1/C10): **a layout key without evidence is invalid; no hand-typed number
enters a frozen file mid-run; a numeric PASS never overrules a visible mismatch.**

## Job C1 — measure the target (owns: scripts/measure-target.mjs, subjects/facade_brick/layout.json, subjects/facade_brick/layout.measured.json, src/validate/kernel-chain.mjs, subjects/facade_brick/passes.json, src/kernel/README.md, test/**)
| # | Change |
|---|---|
| C1.1 | `scripts/measure-target.mjs`: inputs target, `refs/facade_brick.camera.json`, `regions.json` medians. (a) front face x0,x1 = longest brick_front run over ≥5 scanlines; wall top / ground at x0 → H px; (b) glass-family components inside the face → per-window centreX/W, w/W, h/H, headBelowCoping, rowPitch; (c) green family → awning top/bottom H, signbox h/top; (d) iron row histogram → deck lines → landing.rowY vs nearest window bottom; (e) coping walk from the front-left top corner along slope mZ → D/W; (f) ink/iron px inside the front quad → iron share; (g) side-strip ladder centre → ladder.roof.backFromCorner/W; (h) side vs front brick medians → sideOverFront. Writes `layout.measured.json`: every key `{value, unit, evidence:{scan|component, px}}`; keys it cannot resolve → `unverified:true` with the reason. `--check` compares the frozen layout to the measurement and exits 1 on any key off by > tol. Must reproduce the Fable numbers above within 0.01 or say why. |
| C1.2 | `layout.json` REGENERATED from `layout.measured.json` (a `--freeze` flag copies value + evidence + tol). No hand numbers. Tolerances feature-relative: `tol = max(0.02, 0.15 × value)` in the key's unit (Astra B2). `max`-only keys become value ± tol (crown 0.027 ± 0.01). New keys: `landing.rowY −0.085 H`, `ladder.roof.face: "side"`, `ladder.roof.backFromCorner 0.18 W`, `iron.frontShare 0.062`, `massing.depthOverW 0.89`, `sideOverFront 0.786`. |
| C1.3 | V12_LAYOUT: window.w/h on the glass pane (done), centreX measured from the STREET-RIGHT edge of the face (author −x is right, so centre fraction = (x1 − cx)/W); `ladder.roof.*` rule: roof-ladder assembly must have x beyond the face's street-left edge (on the +x side wall) and z centre 0.18 W ± tol behind the front plane; `landing.rowY` measured deck top vs window bottom; keys with `unverified` are SKIPPED and reported as UNVERIFIED (never enforced). |
| C1.4 | passes.json P2 sentences (Fable M5/M6): "The roof ladder stands on the street-left SIDE wall, 0.18 W behind the front plane, never in front of the face." "Bars are 0.04 m; a deck is an open grate — the wall must show through it." V11_DECK_GAP slot limit 0.10 → 0.20 m (`KERNEL_LIMIT_DEFAULTS.deckGapMax`). P0/P1 items cite `layout.json` keys by name; remove every numeric adjective that a key covers. README ≤ 140 lines; add: "A layout key is a measurement with evidence; if a key you need is missing, say MISSING KEY in your CHANGE line — do not guess." |
| C1.5 | tests: measure-target on the target reproduces the frozen layout within tol (golden test); `--check` fails on a tampered copy; V12_LAYOUT fixtures updated to the new numbers; ladder-on-side fixture. |

## Job C2 — commensurable likeness, visual authority (owns: scripts/likeness.mjs, scripts/compare-still.mjs, src/app.js, scripts/pass.mjs, scripts/measure.mjs)
| # | Change |
|---|---|
| C2.1 | app.js capture manifest emits the massing front-face corners projected to px (`frontQuad`) and the side-face corners (`sideQuad`); the code that frames the AABB corners already projects (`frameTarget`). |
| C2.2 | LK_AREA rebuilt and BLOCKING: classify BOTH stills by the same nearest-median rule (target.png, not idpass) INSIDE the front quad only (target quad from `layout.measured.json` face px; render quad from the manifest). Families: brick, glass, frame+iron, green, grey. Threshold ±30 % of the target share; rows roof/parapet/sill dropped. LK_VISIBLE per INSTANCE: each census assembly ≥ 50 visible idpass px (sign box hidden behind a deck fails). `sideOverFront` band = measured target ratio ± 0.05 at runtime, not frozen. Report PASS / FAIL / UNVERIFIED per row; advisories printed, never "clean" when any advisory exists. |
| C2.3 | compare-still: front quads side by side at equal px per W (crop + scale), plus the whole stills below, so the human row judges the face the target shows. |
| C2.4 | pass.mjs: refuse to run when `measure-target.mjs --check` fails or any pass-item key is `unverified`; final pass runs one autonomous image review row: the Fable LOOK table row 3 sentence becomes mandatory input to the verdict — "A numeric PASS cannot overrule a visible mismatch; cite the mismatch and reopen its parameter or mark the measurement invalid." (pass.mjs prints the sentence and the verdict is `PASS-numeric, review pending` until review.md row 3 says PASS). |

## Run-4 plan
Reset module to smoke → P0 → P1 → P2 (seats) → calibrate-palette → final capture → Fable review with
the front-quad compare → round-4 audits only if the owner asks; otherwise report: seats, tokens, wall,
likeness rows, and the residual list (deferred by ruling: ink, decals, glass strokes, fixture shapes, bench).
