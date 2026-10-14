# LOOK checklist — P1

Fable fills the Verdict column in from `compare.png` in this directory and
`refs/tenement-iso.png`, then writes the same table into `review.md`. A row marked
FAIL is quoted verbatim into the next pass's prompt; the item wording already tells
the author it may reopen earlier work to clear one.

Only rows no script can measure are left here (r2 A5). Bearing, census, landing
gap and clashes are validator rows; colour, proportion and visibility are
`likeness.json`.

r3 C2.4 / Astra C10 — row 3 is MANDATORY input to the verdict, and it outranks
the numbers:

> A numeric PASS cannot overrule a visible mismatch; cite the mismatch and reopen its parameter or mark the measurement invalid.

Judge row 3 on the TOP row of `compare.png`: the two FRONT FACES, cropped to
their own face quads and scaled to the same pixels per face width W. Until row 3
of `review.md` says PASS, the final pass's verdict is `PASS-numeric, review pending`.

Validator gate for this pass: **PASS**.
Likeness for this pass: **PASS**.

| # | Row | What passes | Verdict | Note |
|---|---|---|---|---|
| 1 | orientation | the populated face is the one turned toward the camera, and its horizontal edges RISE toward screen-right, as in refs/tenement-iso.png |  |  |
| 2 | door side | the shop entrance is on the same side of the storefront as the target's, and it is RECTANGULAR and glazed — there is no arch anywhere on this building |  |  |
| 3 | reads as the target | at a glance, next to compare.png, this is the same building in the same idiom — not a different building that passes every rule |  |  |

## Validator report (measured, not looked at)

```
PASS: V0-V7 + V10 clean.
```

## Likeness (measured, not looked at)

```
PASS: likeness clean (LK_VALUE, LK_HUE, LK_AREA, LK_OVERLAP, LK_VISIBLE).
(partial pass: colour rows only — LK_AREA / LK_OVERLAP / LK_VISIBLE are judged on the finished assembly)
```

| zone | role | target | render | value ratio | d hue | whole-picture share r/t (informational) |
|---|---|---|---|---|---|---|
| brick_front | massing | #a85643 V0.659 | #b3412f V0.702 | 1.06 | 3° | 67.8% / 28.9% |
| brick_side_strip | massing | #843b2e V0.518 | #8a2f21 V0.541 | 1.04 | 1° | 67.8% / 13.8% |
| roof | roof | #918680 V0.569 | #8f8883 V0.561 | 0.99 | 4° | 8.3% / 20.2% |
| coping | parapet | #a77b6f V0.655 | #af3f2d V0.686 | 1.05 | 5° | 2.5% / 5.5% |
| glass | window | #80a9ac V0.675 | #7ca4a7 V0.655 | 0.97 | 0° | 3.0% / 1.6% |
| frame | window | #8b7e73 V0.545 | #96755f V0.588 | 1.08 | 4° | 3.0% / 3.6% |
| sill | sill | #be9589 V0.745 | #a87c64 V0.659 | 0.88 | 8° | 0.1% / 5.1% |
| iron_landing_upper | landing | #887768 V0.533 | — | — | — | 0.0% / 1.5% |
| iron_landing_lower | landing | #887568 V0.533 | — | — | — | 0.0% / 4.7% |
| awning | awning | #538c54 V0.549 | #518a4f V0.541 | 0.99 | 3° | 6.3% / 6.1% |
| signbox | signbox | #668865 V0.533 | #4f874d V0.529 | 0.99 | 0° | 2.0% / 3.7% |
| ac | ac | #c0c0bf V0.753 | #babab9 V0.729 | 0.97 | 0° | 1.3% / 0.8% |
| door | door | #81acaf V0.686 | #7ca4a7 V0.655 | 0.95 | 0° | 1.1% / 1.6% |
| storefront | storefront | #85adb2 V0.698 | #7ca4a7 V0.655 | 0.94 | 3° | 2.0% / 3.0% |

front brick #b3412f vs palette: 0.989x (limit 0.90–1.05); side #8a2f21 / front: 0.771x (band 0.736–0.836, = target 0.786 ± 0.05)

LK_AREA — share of the FRONT FACE quad, same classifier both sides:
| family | target share | render share | ratio | verdict |
|---|---|---|---|---|
| brick | 55.8% | 2.5% | 0.05x | FAIL |
| glass | 11.5% | 26.9% | 2.34x | FAIL |
| iron | 12.3% | 2.7% | 0.22x | FAIL |
| green | 19.4% | 62.8% | 3.24x | FAIL |
| grey | 1.0% | 5.1% | 4.86x | FAIL |

target quad: FALLBACK — no measured face quad in subjects/facade_brick/layout.measured.json; Fable r3 audit x 556-764, wall top y 345, ground y 895 at x 556; parallelogram, face slope 0.521 px/px taken from the render's own front quad

LK_VISIBLE — separate blobs of ≥ 50 id-pass px, against the frozen census:
| role | instances seen | census | verdict |
|---|---|---|---|
| window | 4 | 4 | PASS |
| storefront | 1 | 1 | PASS |
| door | 1 | 1 | PASS |
| landing | 0 | 2 | FAIL |
| stringer | 0 | 1 | FAIL |
| ladder | 0 | 2 | FAIL |
| signbox | 1 | 1 | PASS |
| ac | 1 | 1 | PASS |
| roof_fixture | 3 | 3 | PASS |
