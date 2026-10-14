# school_bus — round 2 critiques merged (orchestrator; rules: research/WF-V7-GOLD.md "Merge")
Verdicts: Fable ACCEPT (7 MINOR) · Opus NOT YET (3 MAJOR, 7 MINOR) → round 3.

## A — both flagged (do it)
A1. concept, side · stop arm — sign centre z 2.40 → 2.13 (Fable) / 2.15 (Opus), y 1.345 → 1.28 / 1.29; post + hinge with it
    (post z 2.67–2.75 → ≈2.41–2.49). Reference: the concept puts the whole sign under the first regular pane, clear of the
    mirror head and the tyre, its top just over the band's lower frame (the side turnaround's z 2.37 is drift, concept wins).
    Also clears the 3 V6_CLASH_UNDECLARED gate rows (declare the post/hinge contacts in `touches`).
A2. concept (front, rear, top) · mirror heads too boxy — depth 0.20 → 0.13 (Fable) / 0.07 (Opus), keep y 1.63–2.18 and the
    brackets; width: Fable 0.25 → 0.18, Opus keep 0.25 — measure the concept page (the heads should read ≈20 px wide there,
    with the bracket arms visible between head and windshield frame). TRIED r2: moving heads outboard cost front/rear IoU.
A3. front, concept · windshield top frame bar 0.14 → 0.09 with a yellow gap (≈0.05–0.065 m) between the frame and the
    marker pods. See CONFLICT K2 for where the glass sits.
A4. front, side, concept · front bumper — depth 0.08 → 0.11 (Opus) / 0.12 (Fable); bottom edge 0.315 → 0.28 (Opus) /
    0.255 (Fable); top stays 0.615.
A5. side, concept · hubs smaller — hub R 0.26 → 0.23 (Fable) / 0.235 (Opus). Tyre size: CONFLICT K1.

## B — one critic, MAJOR (verify on the reference page, then do it)
B1. concept · wheel wells (Opus) — the concept camera sees a dark-ochre block beside/behind each tyre (≈580 / 650 px² of
    well colour vs ≈140 / 160 on the concept); fix: tyre outer face ≈0.04 m inside the flank (tyreF.inset 0.105 → 0.04,
    tyreR.inset 0.085 → 0.04; the front/rear orthos draw ≈0.1 m — concept wins) and arch clearance 0.045 → 0.02
    (aHalf = R + 0.02, aTop = 2R + 0.025).

## CONFLICT — measure the reference and decide
K1. tyre radius — Opus (MAJOR): R 0.53 → 0.48 (side ortho tyre top 0.96, arch top 0.98; concept R ≈ 0.46); Fable: keep 0.53
    or trim to 0.51 (concept front tyre 137 px vs the model's 144). History: r1 critic asked for bigger wheels, r2 set 0.53.
    Measure the tyre on the concept (measure.mjs unproject at the tyre's top/bottom edges on the near-flank plane) and on
    the side ortho (measure.mjs comps --view side --family tyre); take the concept value.
K2. windshield glass position — Fable: keep the glass 1.53–2.27 (frame top 2.41 → 2.36, pods stay 2.42–2.66); Opus: glass
    1.46–2.22, pods yc 2.555 → 2.505 (front ortho: frame top 2.32, glass 1.46–2.22, pods 2.38–2.63; concept glass 66 px
    tall vs the model's 61).
K3. cowl under the windshield — Fable: flatten (≤0.02 m step at y ≈1.23: cowl y0 1.21, y1 1.25, back 0.02; concept shows
    flat yellow ≈0.2 m under the frame then one thin seam); Opus: deepen (back 0.05 → 0.10, y 1.22–1.36; top ortho shows a
    0.09 m ledge z 3.02 → 3.11, the concept's frame corners sit 8–11 px behind the lamp panel edges).

## C — one critic, MINOR (do it when cheap)
C1. concept · side window band (Opus) — band top 2.445 → 2.39, regular panes 1.63..2.28 → 1.61..2.22 (a flat yellow strip
    under the roof edge; side ortho 2.425 / 2.29 — concept wins).
C2. concept · door pane (Fable) — its top ≈0.07 m above the regular panes' top line (2.28 → 2.35 today; with C1 ≈2.29),
    bottom on the same line.
C3. side, front · roof caps (Opus) — cap.tail 0.12 → 0.18, cap.run 0.24 → 0.20, cap.drop 0.30 → 0.22 (side ortho corners
    ≈0.18–0.20 × 0.20–0.21). History: r1 asked for a crisper rear cap; r2 set tail 0.12.
C4. concept · front cap marker inboard lens (Opus) — orange #e95f0f (sampled #eb6110 / #e75c0f), redder than the amber turn
    lamps #f28e13; rear pods stay amber. History: r1 asked for amber; r2 made it amber.

## GATE (orchestrator)
3 × V6_CLASH_UNDECLARED (stopArm_rim / stopArm_border × stopArm_post / stopArm_hinge) — must be 0 at the end of the round.
PALETTE_ZONE rows (well, mirror, white) are a class-config gap — leave them.
