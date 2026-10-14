# school_bus — round 4 critiques merged (orchestrator; rules: research/WF-V7-GOLD.md "Merge")
Verdicts: Opus ACCEPT (5 MINOR) · Fable NOT YET (3 MAJOR, 3 MINOR) → round 5 (the owner's extra round).
Rule for every structural change below (the v8 "concept-first" variant rule, research/v7/WF-V8-PLAN.md): build it as a
variant; a variant that drops any ortho view by > 0.01 is disqualified unless the ortho region is a logged drift; the
best concept IoU wins; BASE wins ties within 0.002. A disqualified structural item goes to the owner packet (not built).

## A — both flagged (do it)
A1. concept (visible in all views) · long roof edges tighter — today elliptical quadrants roofR 0.24 × drop 0.25 in 5
    segments (a soft faceted band 42–44 px); concept: roof colour to ONE crease ≈0.14 m below the roof top (flank plane
    y 2.64–2.66), then ≈0.25 m of flat flank above the band (2.38–2.40). Fable: roofR 0.10, long-edge drop 0.14, 3 segments;
    Opus: flank vertical to ≈2.64 then one bevel ≈0.20 (x) × 0.145 (y) (a ≈36° facet renders in the roof colour). Split
    the long-edge drop from cap.drop (the rear cap keeps tail 0.15 × 0.25). History: r4 C2 tried roofR 0.15 scored only on
    front / rear IoU (−0.001) — judge it on the concept page this time.
A2. concept, rear · rear bumper near-side end block shallower — depth 0.08 → 0.04 (Opus) / 0.05 (Fable); Fable also
    wrap 0.34 → 0.47 and out 0.04 → 0 (block front edge 0.13 m further forward, outer edge 0.07 m less far out).

## B — one critic, MAJOR (variants table first)
B1. concept · wheels vs body (Fable) — the concept hangs the same wheels (R 0.46) 0.05–0.07 m lower under the same body
    (rear tyre bottom arc 10 px lower at every column; sill, bumper bottoms and roof match): raise the shell (body, band,
    bumpers, lamps, sign — everything but wheels / axles) 0.05 m (sill 0.415 → 0.465, roof 2.78 → 2.83). The side ortho
    has the sill at 0.417 → variants BASE vs +0.03 vs +0.05, rule above.

## CONFLICT — measure and decide
K1. front cap + marker pods — Fable (MAJOR): the cap face near-vertical from the windshield frame top (2.45) up to the roof's
    front crease (cap run 0.2 → 0.16, drop 0.25 → 0.14), pod housings 0.26 → 0.33 m tall (2.45–2.78) laid flat on that
    face with the lenses facing forward (today they tilt up; the top turnaround shows no lenses at all); Opus: housing
    0.26 → 0.19 tall (2.54–2.73), lens d 0.17 → 0.14, a 7 px yellow gap above the frame. Measure the concept's far and near
    pod housing (rows / cols in both critiques) once, build the orientation fix (lenses facing forward) either way.
K2. overall length (both critics measured it; structural) — the concept's bus is ≈0.15 m shorter at the nose (window
    pitch 0.71 vs 0.732; nose landmarks 12–21 px behind the model's, rear matches): Fable L 6.26 → 6.11 with everything
    ahead of the rear axle 0.15 m back; Opus the same plus wheelbase 3.90 → 3.64 (front hub 0.19 back, rear hub 0.07
    forward). Opus's variant already measured: concept 0.9609 → 0.9628, side 0.970 → 0.940. By the rule this is
    disqualified (side −0.03) → do NOT build; it goes to the owner packet as the bus's proportion question (like the
    tractor's).

## C — one critic, MINOR (do it when cheap)
C1. concept · hood slope under the windshield (Opus) — cowl y1 1.385 → 1.43 (meets the frame bottom), y0 1.30 → 1.26,
    back 0.09 → 0.15 (a ≈48° lit slope ≈30 px tall directly under the frame). History: r2 K3 / r3 set 0.09.
C2. concept · rear plan corners (Fable) — 0.12 → 0.03 (the concept draws the rear corner as one line); front corners stay.

## GATE
Keep the chain clean (only PALETTE_ZONE). Stay ≤ 4000 triangles (3820 now).
