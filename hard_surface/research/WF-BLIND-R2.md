# Blind-test round 2 — examiner merge (Opus 5, 2026-09-13)

Owner rule: the workflow passes only if blind TEST models (Gemini 3.8 Flash High, GPT 5.6 Terra) build good
models through it. Examiners fix the WORKFLOW for any model.

## Runs examined
| run | seat | result | evidence |
|---|---|---|---|
| building P2 (fire escape) from start-P2 9ac3119934779ba1 | Gemini | FAIL, close: two landings + flight + drop ladder + roof ladder on the side wall read like the target | `out/blind/facade_brick/agy/P2/` (attempt-1, attempt-2, repair.md) |
| building P2 | Terra | NO RESULT: two transport drops (77.6 s, 108 s), transcript not kept | `out/blind/logs/facade-P2-terra.log`; diagnosis in `out/blind/diag/terra-P2.*` |
| pickup P1 | Gemini, Terra | running | `out/blind/logs/pickup-P1-*.log` |

Gemini building P2 detail: attempt 1 gate = V11_LADDER_ACCESS (a baluster across the drop-ladder head);
likeness = iron hue 28° (#878787 vs #887768) on both landings + lower landing value 0.72×. The repair moved the
ladder 10 cm and opened a 0.668 m hole in the lower landing's front rail → attempt 2 gate = V11_LANDING_GUARD;
likeness 3 rows (lower landing value 0.77×, glass area 0.58×, grey area 1.80×). The repair reply reasons at
length about street-left/right versus screen-right and x signs.

## Examiner job 3 (after the pickup blind tests finish — it edits the harness they run through)
| # | Gap | Change |
|---|---|---|
| C1 | Repair swapped one gate code for another with equal row counts and was kept | pass.mjs guard: a repair that introduces a gate CODE the pre-repair result did not have is worse, even at equal counts; record `{introduced:[codes]}` in repair-reverted.md |
| C2 | Rule-heavy topology hand-built → ladder access and landing guard traded against each other | building P2 item + classes/building.md: landings, flights and ladders MUST be built with `K.assemble.landing({…, gateAt})`, `K.assemble.flight`, `K.assemble.ladder` (they pass V11 by construction); check-module or a gate advisory flags a module with role landing/stringer/ladder parts not produced by K.assemble (e.g. an `assembly` tag the helpers set on their parts) |
| C3 | Coordinate/handedness confusion (fractions + "street-left is +x") | pass.mjs MEASURED NUMBERS also prints ABSOLUTE metres for this start module: W, H, depth, and for every cited key with unit W/H the computed x/y value in the author frame (x from the massing's min x per the key's rule), e.g. `window.centreX: 0.231 / 0.808 W → x = -1.689 / +1.932 m`. Derived from the live start module's measured massing box. Same for vehicles (L along z, W along x) |
| C4 | Author-invented palette zone names skip calibration → iron hue 28° off | prompt lists the CLOSED palette zone keys of the class (from paletteZones) next to the role list; check-module (or V7_ROLE-style gate row `PALETTE_ZONE`) fails a part whose zone is not a paletteZones key; calibrate-palette keeps warning |
| C5 | Template-built parts fail final likeness rows charged to the ironwork author (glass area 0.58× from the storefront, grey area 1.80× from the AC) | template-building: consume storefront.bottom (measure it if the target supports it) and check the AC size against ac.w/ac.h; likeness: an LK_AREA family whose roles are all due in an EARLIER pass is judged at that pass (so the template's own P1 gate catches it), and at the final pass it is printed but attributed to the pass that owns it |
| C6 | Lower-landing iron value 0.72–0.77× in every run (run 4, v3 proof, blind Gemini) regardless of author | likeness/regions: re-derive `iron_landing_lower` target patch (it may sample lit deck top while renders show the shaded underside, or vice versa); ruling by measurement, not by widening the band |
| C7 | Terra transport drops | from `out/blind/diag/terra-P2.*`: fix the adapter (flag, image, stdin size, timeout) or document the channel limit; the runner must keep the seat transcript on a transport failure (pass.mjs writes transcript before exiting 2) |
| C8 | Runner archived a stale P2 folder as Terra's "result" when the seat never ran | blind-test.mjs: on exit 2 after retries, write `blind-run.json` with `result: "NO_RESULT"` and do not copy the pass folder |

## Protect
Gemini P2 attempt 2 geometry: two landings at the measured heights, flight inside the landing span, drop
ladder over the sign band, roof ladder on the side wall behind the corner; gate otherwise clean.

## Addendum — Terra building P2 (diagnostic run, gated with no repair; evidence `out/blind/facade_brick/terra/P2-diag/`)
Channel works: 129 s, 23 816 tokens, full module (the two blind-run drops were transient). Gate: 193 parts,
2740 tris, only V11_LANDING_GUARD on BOTH landings; likeness 8 rows. Terra built every ironwork piece with
`K.assemble.landing` (with `gateAt`), `K.assemble.flight`, `K.assemble.ladder` — so a helper-built landing fails
the guard rule. It passed `wallZ: 0`; the start module's front wall is not at z = 0, and nothing in the prompt
says where it is. All ironwork used zone `metal`, which paletteZones aliases to the AC region → iron #a2a2a2,
hue 28° off. These sharpen three rows:
- **C2 (now top priority):** reproduce `K.assemble.landing` with Terra's exact arguments against start-P2's wall
  plane and run V11_LANDING_GUARD. Either the helper builds the guard on the wrong side / wrong edge when wallZ
  is off, or the rule and the helper disagree about "front". Fix whichever is wrong; add a test that every
  helper output, placed against a start module's real wall, passes the full V11 family. Helpers should take
  the wall plane from a kernel query rather than a caller guess.
- **C3:** the prompt must print the start module's wall planes in metres (front face z, side face x, ground y,
  W/H/depth) next to MEASURED NUMBERS.
- **C4:** delete palette aliases that map a generic name (`metal`, `trim`, `parapet`) to an unrelated region;
  the closed zone list the prompt prints has exactly one key per material; unknown zone → gate row.

**Correction (examiner diagnostic):** Terra's `wallZ: 0` was RIGHT — start-P2's front face is z = 0, the helper
put the deck at z −1.1..0 in front of it, rails top out 0.94–1.0 m above the deck along the front with returns
to the wall, balusters only every ~0.8 m. A correctly placed helper landing still fails V11_LANDING_GUARD, so
C2's defect is inside the workflow (rule vs helper: how the rule finds the front edge/guard members, gate-gap
recognition, or baluster pitch vs the rule's hole limit ≤ 0.26 m). C3 still stands (print wall planes), but it
is not the cause here.

## Pickup P1 blind results (evidence `out/blind/pickup/{agy,terra}/P1/`)
| seat | result |
|---|---|
| Gemini | gate PASS; likeness FAIL: headlight zone renders #828282 vs #f2eba9 (value 0.54×, hue 54°), LK_VISIBLE wheel 2 of 3; lamp area UNVERIFIED; 291 s, 1 repair. Visually close: windshield, side window, mirrors, grille, lamps. Examiner row 3: FAIL on residuals (grey lamps, hidden far wheel). |
| Terra | FAIL: both the first module and the repair did not load — `build() threw: V5_THIN: cut leaves 0.0400 m of material on x-` (then 0.0500 m on z-); 231 s, 44 512 tokens. CHANGE lines: "shallow paired door lines", then "grille-slot side margins to 0.06 m". |

## New rows for examiner job 3
| # | Gap | Change |
|---|---|---|
| C9 | The groove rule ({GROOVE_DEPTH_MAX} 0.02 m) and the kernel's cut check (MIN_FEAT 0.06 m remaining material) contradict on any panel thinner than 0.08 m; and the kernel THROWS inside build(), so one thin cut destroys the whole module instead of producing a fixable row | (a) the kernel cut check becomes a recorded violation, not a throw: `K.cut` returns the result and registers `V5_THIN {part?, axis, remaining, tool bbox}` that the chain reports as a normal gate row with the location; check-module only rejects for import/syntax/contract. (b) Resolve the contradiction in the rules: grooves/recesses cut into a face must leave ≥ MIN_FEAT; the prompt states the implied minimum panel thickness `MIN_FEAT + GROOVE_DEPTH_MAX` (a token), and the vehicle template's cab/door panels are at least that thick. |
| C10 | Gemini's headlights and both models' ironwork used zone names that calibrate to the wrong region (headlight grey; iron = AC grey) | same fix as C4: closed per-class palette zone list printed in the prompt beside the roles, unknown zone = gate row, no cross-material aliases; for vehicles map lamp → headlight region explicitly |
| C11 | Gemini's P1 detail parts hid the far front wheel that the P0 template left visible (LK_VISIBLE wheel 2 of 3 at P1) | ACCEPTANCE block states the visible-instance requirement for already-built roles at every later pass ("3 wheels must stay visible at the solved camera"); likeness names the occluding part id when a previously visible instance disappears (compare with the previous pass idpass mask) |

## C12 (from the Astra round-2 audit's partial log, 2026-09-14)
| # | Gap | Change |
|---|---|---|
| C12 | Gates reward skipping hard instructions: pickup P1 requires recessed grille slots; Gemini built a solid grille panel and PASSED the gate; Terra built the slots and crashed (V5_THIN throw). An appearance instruction that is not gated is not a requirement. | Every appearance instruction in a pass item maps to a gate or likeness row, or it is removed from the item. For the grille: a `grille.slots` count key (measured on the target) and a V12 rule counting slot cuts/members; pass.mjs lists, per pass, instruction → row, and warns (examiner-side) about item sentences with no row. |

Examiner note: the first Astra round-2 audit read unrelated repo docs (docs/COOPERATION.md) and timed out before writing; the retry gets every artifact bundled into its prompt and runs from an empty temp folder with no repo access.

## C13–C18 (Astra round-2 audit, bundled-evidence retry — `out/blind/exam/astra-round2.md`)
| # | Gap | Change | Job |
|---|---|---|---|
| C13 | Placement anchors: `K.box` is bottom-anchored (y 0..h) but several measurements are centres; Terra placed its side window at the centre value so the pane reaches ~1.06 H (above the roof); its mirror head sits half a head high | kernel `boxFromBounds({min,max})` and `boxAtCentre(centre, dims)`; every layout key declares its anchor type (`bottom`, `centre`, `top`, `extent`); pass.mjs prints the matching constructor call per cited key; a gate row fails a pane not contained in its host face | 4 |
| C14 | Advertised vs executing minimum feature disagree: the pickup prompt says MIN_FEAT 0.04 m (vehicle style floor) while the kernel cut check enforced 0.06 m | one configuration source: the kernel reads MIN_FEAT from the subject's class style floor before build; prompt, build and validation share a config digest; a mismatch is a harness error (exit 3), never an author repair | 3 |
| C15 | Missing datum/endpoint definitions: same input gave roof-ladder tops 0.43 m apart (Gemini `H − 0.037 H`, Terra `H + crownH − 0.037 H`), different roof-ladder bottoms, different windshield tops | every key names its datum (e.g. `ladder.topBelowCoping` measured from the coping TOP y) and endpoint; new keys `roofLadder.bottom` (measure) and `window.front.top` (resolve or approved fallback) before dispatch | 4 |
| C16 | Flight helper endpoint/width conventions unstated (centre vs edge, width axis); models computed landing gates differently | document anchors; `K.assemble.flight` returns the landing intersection intervals that `K.assemble.landing({gateAt})` consumes directly — no author gate arithmetic | 4 |
| C17 | Target has ink outlines, renders have none | DEFERRED by owner ruling 2026-09-12 ("assets stay outline-free"); likeness must not penalise outlines (it does not) | — |
| C18 | Lamps sit on the nose while likeness areas use the flank face → `LK_AREA lamp 0.0% vs 0.0%` proves nothing | per-feature measured face/region (nose features in a nose quad); a row is advertised only when the target has enough pixels | 4 |

Protect (both models): building front "-Z", two landing calls + one flight + two ladders, roof ladder on the side at 0.177 W, landing span 0.577 W / centre 0.627 W reused exactly; pickup four wheel assemblies, open bed, mirrored details, separate mirror heads/arms.
