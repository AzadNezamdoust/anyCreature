# Calibration: likeness_score.mjs vs expert judgement (2026-10-10)

Reproduce with `node scripts/hs/score/calibrate.mjs` and `node scripts/hs/score/sanity.mjs`. Outputs are in
`out/score/` (`items.json`, `features.json`, `calibration.json`, `sanity.json`).

## Ground truth used, and how small it is

| set | n | what | caveat |
|---|---|---|---|
| **J** | 9 | `out/blender-hs-exp/_judge`: pistol, pump_shotgun, ray_pistol × {haiku, sonnet, existing}, blind Opus rubric, `overall` /10 (3–8) | Only 3 subjects. The only **within-subject** comparisons available: 9 pairs, 3 of them within 0.5 points |
| **R** | 30 | `out/blender-hs/<s>/review_fable.md` likeness /10 (5.5–8) for the reviewed pass (pass from the header, 28; newest pass rendered before the review's mtime, 2: apc_8x8 → 16, rocket_truck → 9) | One build per subject, so every comparison is **across subjects**. Two reviewer populations: Fable (14, all vehicles and 4 guns, scores 5.5–6.5) and GPT-6 Astra (16 guns, 6.2–8). Reviewer identity alone explains most of the R variance |

Baselines: `agree4` = mean ortho agree from that pass's `stats.json` (judge_mesh). `agree5` adds the concept view.
`iou` = this script's own render silhouette IoU.

ρ = Spearman, p = two-sided permutation p (5000 shuffles). "c/d" = within-subject pairs in J ordered the same way /
the opposite way as the judge.

## Correlation table

| metric | J ρ (p) | R ρ (p) | R Fable only (n 14) | R GPT only (n 16) | J within-subject c/d |
|---|---|---|---|---|---|
| agree4 (current outline score) | 0.18 (0.63) | **−0.40** (0.03) | 0.03 | 0.36 | 3/6 |
| agree5 (+ concept) | 0.29 (0.44) | −0.29 (0.13) | 0.00 | 0.48 | 3/6 |
| render iou | 0.53 (0.15) | −0.48 (0.01) | 0.13 | 0.35 | 6/3 |
| **interior** (area-weighted, a-priori signal weights) | **0.76 (0.03)** | **0.48 (0.01)** | 0.40 | 0.21 | 7/2 |
| interiorEq (equal view weights) | 0.78 (0.02) | 0.28 (0.14) | 0.27 | 0.14 | 7/2 |
| **likeness** = interior × iou (shipped output) | **0.82 (0.01)** | −0.11 (0.55) | 0.43 | 0.39 | **8/1** |
| interior × agree4 | 0.87 (0.00) | 0.18 (0.35) | 0.33 | 0.59 (0.02) | 7/2 |
| edgeF1 (4-view mean) | 0.46 | −0.13 | 0.00 | −0.21 | 7/2 |
| ssim | 0.52 | 0.41 (0.03) | −0.13 | 0.49 | 6/3 |
| toneSim | 0.66 | 0.13 | 0.00 | 0.05 | 7/2 |
| colourSim | 0.76 | −0.42 | −0.27 | −0.02 | 8/1 |
| openF1 | 0.34 | 0.29 | 0.43 | 0.01 | 4/5 |
| edgeF1, side view only | 0.92 (0.00) | 0.01 | −0.36 | 0.07 | 8/1 |
| ssim, side view only | 0.82 (0.01) | 0.49 (0.01) | 0.03 | 0.54 (0.03) | **9/0** |
| openF1, side view only | 0.78 (0.02) | 0.29 | 0.63 (0.02) | 0.13 | 8/1 |

Fitted weights (non-negative simplex, step 0.1, objective = Spearman on pooled J+R of interior × agree4). In sample:
ρ 0.52, weights edge 0.2 / ssim 0.4 / tone 0.2 / colour 0 / open 0.2. **Leave-one-out: ρ 0.35 (p 0.03)**, below the
a-priori weights. Fitting does not help at this N, so the shipped weights stay a priori (edge 0.3, ssim 0.2, tone 0.2,
colour 0.1, open 0.2).

**Multiple comparisons.** Area weighting of the views was chosen after comparing 4 view weightings (equal, area,
√area, side only) on these same data. Treat the "interior" row as mildly optimistic. With roughly 30 metrics tested,
single p ≈ 0.02 cells (for example openF1 side on R Fable) are expected by chance.

## Which signals carry information

- **The outline score carries none on this data.** agree4 has J ρ 0.18 and 3/6 within-subject pairs. On R it is
  *negative* (−0.40), because the vehicles have high agree (0.88–0.96) and were all reviewed by the stricter Fable
  seat. Within each reviewer group it is about 0. This confirms the premise of the brief.
- **Interior signals carry the J-set information.** The Opus judge's rubric (J, n 9) correlates with side-view edgeF1
  at ρ 0.85–0.90 for part_shapes, part_positions and small_detail_readability. agree4 on those same rubric
  items: ρ 0.03–0.16. edgeF1 and ssim on the side view carry the most. Openings help on the side view (trigger guards
  and windows) but are noisy as a 4-view mean (4/5 within-subject).
- **Front/rear/top are weak, and equal view weighting dilutes them.** Small front/rear views are dominated by bore and
  ink pixels with little area. Area weighting fixed most of this (R ρ 0.28 → 0.48).
- **colourSim** ranks within subjects well (8/1) but is negative across subjects on R. It measures source palette
  difficulty more than build quality.
- **Within reviewer groups on R, nothing is reliably above noise** (best: likeness × agree on GPT n 16, ρ 0.59). The R
  range is narrow (5.5–8, mostly 6 or 7), reviewer-confounded and one item per subject. It cannot validate or refute a
  score with any strength.

## Sanity / game resistance (sanity.mjs: pistol, gatling_gun, apc_8x8)

| probe (on the source itself) | likeness | note |
|---|---|---|
| identity | 1.000 | |
| 8 px whole-image shift | 1.000 | registration forgiven, as reviewers do |
| **flat fill of the exact silhouette** | 0.36–0.48 | agree ≈ 0.99 for this cheat. The interior score collapses (edgeF1 0.03–0.08) |
| interior blurred 6 px | 0.60–0.77 | edges, ssim and openings drop; tone stays at 0.93–0.97 |
| all foreground +25 levels lighter | 0.81–0.82 | tone and colour drop to about 0.6; edges unchanged |
| all dark openings painted over | 0.93–0.98 | **weak**: closing every bore of a subject moves the score only 0.02–0.08 |

The real builds sit at 0.42 (haiku ray_pistol, judged 3/10) to 0.77. That range overlaps the flat-fill cheat at the
bottom: a gross failure scores about the same as a perfect blank silhouette, which is the right ordering.

## Failure cases

- **Near pairs in J**: pistol A (7.5) vs B (8.0) is ordered wrong (0.691 vs 0.685). pump_shotgun C (7.5) vs A (7.0) is
  ordered right by only 0.008, ray_pistol C vs B by 0.014. Every 0.5-point judge gap is decided by about 0.01 of score, which is inside the
  range that a render-style difference moves it.
- **Openings are under-weighted in effect.** The judge's top misses for pistol A/B are "bore ~22 % / 30 % of slide
  width vs 45 %". A bore is a few hundred pixels, so even removing every opening costs only 0.02–0.08.
- **Wall thickness and depth cues** (rims, counterbores) appear only as thin edge pairs in one view. The 2 px edge
  tolerance treats a 1 px and a 3 px wall as nearly equal.
- **Cross-subject scale is not comparable.** Busy sources (apc, tanks) have much lower edge and opening agreement for
  equally good builds. Compare scores within one subject only.
- The concept view is not used: the build's concept render is not pixel-registered to `refs/<s>.png` (about 15 %
  scale offset seen on gatling_gun).
- Per-part crops (closeups.py) were not tried: they need Blender per build, which breaks the cost target.

## Is it good enough to rank part variants? **No, not as the sole ranker.**

Why:
1. The only within-subject evidence is 9 pairs on 3 weapons. Its result is 8/1, but the pairs it gets right are mostly
   the easy ones (haiku vs the rest, 1.5–4 point gaps). On the three 0.5-point pairs it gets 1 wrong (by 0.006) and 2
   right, by 0.008 and 0.014.
2. A part variant changes far less of the image than closing every bore of the subject, which moves the score
   0.02–0.08. Variant deltas will be about 0.001–0.01, the same size as the margins it already gets wrong.
3. The R set cannot support a cross-subject claim (reviewer-confounded, ρ about 0 to 0.4 within groups).

What it **is** good for now: (a) a regression gate that rejects a variant whose `interior` drops more than about 0.02
vs BASELINE, or whose `iou` drops; (b) triage of gross failures, since it separates the haiku builds and the
flat-fill cheat where agree cannot; (c) a coarse pre-filter that sends the top k variants to a visual judge. It beats
agree clearly on the only within-subject data there is (J ρ 0.82 vs 0.18; pairs 8/1 vs 3/6).

To make it a ranker: collect about 30–50 blind pairwise judgements on real part variants of 3–5 subjects (one
changed part each). Then measure pair concordance at the size of delta Haiku will actually produce, and re-fit with
leave-one-subject-out. Separately, add a per-part signal (edges, openings and tone inside each part's projected box,
from the build's part-ID pass) so a single part's change is not averaged away over the whole view.

**Update 2026-10-10:** the per-part signal now exists: `part_score.mjs` (see PART-CALIBRATION.md). It ranks controlled
single-part degradations correctly in 20/20 cases (17/20 beyond the 0.004 nuisance floor), where this whole score clears that floor in 8/20.

## Open signal v2 (2026-10-10)

The tables above are the v1 run (R n 30). v1 counted a "dark recess" as any foreground px with L* < 25 and < 0.6 × the
plain 21×21 mean. That surround includes the white page, so the dark rim / ink band along every outline, every ink
seam and every dark-painted part counted as an opening (it_grapple source side view: 12.9k "open" px, most of them
outline band). A build then scored higher the more near-black px it had near the source's outlines. Evidence:
it_grapple polish pass10 → 16 lifted recess and buckle tones toward the source and likeness fell 0.426 → 0.399, all
of it in open (side .462 → .312, rear .494 → .314).

v2 (`openMap()` in likeness_score.mjs; port of the part_score fix in PART-CALIBRATION.md, plus a thin-line filter):
- surround mean over **foreground px only** (21×21), recess < 0.6 × that;
- recess < min(0.25, **0.65 × the image's own foreground median L*** in its region): 32 px tiles, 3×3 neighbourhood
  (96 working px = 192 canvas px). A uniformly dark part is not a recess;
- recess mask morphologically opened with r 1 (working px): ink lines and rims ≤ 2 px wide drop out; bores, slots and
  windows stay (checked by mask overlays on it_grapple side and it_gatling front: the six barrel bores survive).
- see-through holes (enclosed background) unchanged. `LIKENESS_OPEN_V1=1` reproduces v1. A cap of 0.30 (part_score's)
  instead of 0.25 changes the six it_* scores by ≤ 0.001, so 0.25 is kept.

Calibration on the same items (J 9, R 34; v1 re-run with `LIKENESS_OPEN_V1=1 node calibrate.mjs --rescore`, outputs in
`out/score/pre-open-fix/v1-same-items/`; v2 in `out/score/*.json`; the original v1 R-30 run is in `out/score/pre-open-fix/`):

| metric | J ρ v1 → v2 | R ρ v1 → v2 | R Fable v1 → v2 | R GPT v1 → v2 | J within c/d v1 → v2 |
|---|---|---|---|---|---|
| **likeness** (shipped) | 0.82 → **0.81** (p 0.01) | 0.12 → 0.21 | 0.43 → 0.46 | 0.39 → 0.52 | 8/1 → 8/1 |
| interior | 0.76 → 0.92 | 0.62 → 0.66 | 0.40 → 0.43 | 0.21 → 0.14 | 7/2 → 8/1 |
| likeness × agree | 0.87 → 0.87 | 0.39 → 0.47 | 0.33 → 0.43 | 0.59 → 0.40 | 7/2 → 8/1 |
| openF1 (4 views) | 0.34 → 0.25 | 0.37 → 0.63 | 0.43 → 0.66 | 0.01 → 0.26 | 4/5 → 6/3 |
| openF1 side | 0.78 → 0.75 | 0.31 → 0.25 | 0.63 → 0.37 | 0.13 → 0.12 | 8/1 → 7/2 |
| LOO fit, pooled | 0.46 → 0.61 | | | | |

Gate (J ρ ≥ 0.75 for the shipped likeness) holds: 0.81. Weights unchanged (a priori).

Sanity (sanity.mjs) v1 → v2: close_openings now costs 0.06–0.15 (pistol 0.939 → 0.906, gatling 0.925 → 0.846, apc
0.975 → 0.864; was 0.02–0.08), flat_fill 0.36–0.44 (pistol 0.480 → 0.443). New weakness: lighter_25 also costs open
(apc open 0.66 → 0.01, likeness 0.806 → 0.676), because a +25-level lift pushes the apc's recesses over L* 25. A
whole-image value miss of that size is a real miss, but tone already charges it.

Re-score of the three polish pairs (likeness / interior / openF1 4-view; side open):

| build | v1 likeness | v2 likeness | v1 interior | v2 interior | v1 open | v2 open | side open v1 → v2 |
|---|---|---|---|---|---|---|---|
| it_grapple pass10 | 0.426 | 0.376 | 0.480 | 0.423 | 0.350 | 0.065 | 0.462 → 0.160 |
| it_grapple pass16 | 0.399 | 0.373 | 0.457 | 0.427 | 0.244 | 0.092 | 0.312 → 0.198 |
| it_gatling pass7 | 0.501 | 0.478 | 0.533 | 0.509 | 0.423 | 0.303 | 0.554 → 0.481 |
| it_gatling pass13 | 0.554 | 0.515 | 0.595 | 0.554 | 0.522 | 0.316 | 0.688 → 0.497 |
| it_rotary_drill pass7 | 0.444 | 0.422 | 0.513 | 0.487 | 0.405 | 0.276 | 0.508 → 0.722 |
| it_rotary_drill pass12 | 0.467 | 0.440 | 0.535 | 0.504 | 0.430 | 0.278 | 0.646 → 0.727 |

it_grapple: the polish no longer loses on open (0.065 → 0.092; v1 0.350 → 0.244), and interior now rises
(0.423 → 0.427; v1 fell 0.480 → 0.457). Likeness is a near tie (0.376 → 0.373): the remaining gap is the silhouette
IoU (0.887 → 0.873, claw tips per the drawings), not openings. it_gatling and it_rotary_drill keep their order (polish
ahead by 0.037 and 0.018). Absolute v2 scores are lower than v1 (the free outline-band credit is gone), so compare
v2 numbers only with v2 numbers.

## v11 gate (2026-10-12, research/WORKFLOW-V11.md §5 calibration; implementer seat, phase 1)
Commands: `node --test scripts/hs/spec_build.test.mjs scripts/hs/score/specgate.test.mjs scripts/hs/score/bands.test.mjs
scripts/hs/score/heroratio.test.mjs` (unit, all pass), `scripts/hs/tests/test_run_pass_v11.ps1` (refusals 9/9 pass),
`scripts/hs/tests/test_camera_v11.ps1` (camera checks + `tests/mutants.py`; tallies in out/blender-hs/_v11_mutants/summary.json).
Specs written: it_smg (subjects/it_smg/spec.in.json, 11 parts) and it_thumper (8 parts, central column + feet).

**Live-gate condition (§5.4) NOT met.** Must-PASS rows fail:
- it_thumper pass 18 (owner-approved) as is: GATE FAIL, 14 SPEC keys + BANDS side & top. Largest: cap.L spec .0754
  (side and front views agree: ~.075) vs build .045 (-40 %); housing.D (hero-resolved .2225) vs .32 (+44 %);
  striker.L +36 %; ratios cap.D/housing.D -42 %. BANDS side: all 20 bands 1.25x (the build's tripod spans .886 m in z,
  the turnaround side .77 m). The approved thumper follows its hero, not its turnaround; its turnaround is internally
  inconsistent (README: front viewOnly 19 %). It is not an anchor for an ortho-led spec.
- Uniform x1.02: it_thumper (identity already FAIL) FAIL; it_smg block-out x1.02 adds no key (rel PASS); it_smg_A x1.02
  adds `sigma` (A's sigma .988 -> < .98) and hero.top_rail.h.
Must-FAIL rows (new hard keys over the same base's identity):
| base | (a) axial x0.8 | (b) width x0.8 | (c) diameter x1.3 | (e) drop | (f) fill opening |
|---|---|---|---|---|---|
| it_smg block-out (SPEC PASS by construction) | muzzle.L FAIL | receiver.W FAIL | muzzle.D FAIL | magazine.match FAIL | n/a (box guard) |
| it_smg_A | muzzle.L FAIL | receiver.W NOT new (A is +14 % wide; x0.8 -> -9 %) | muzzle.D FAIL | magazine.match FAIL | hero.trigger_guard.open FAIL |
| it_thumper pass 18 | housing.L FAIL | housing.D NOT new (already +44 %) | bellows.D FAIL | tbar.match FAIL | n/a (no opening row) |
(d) round part as a box: no new key (known phase-1 hole, as planned). 1-band wobble (magazine z x1.03): no new key.

**BANDS distribution (§5.2, bands-only vs own turnaround, the 9 it_* folders with final renders):** 9 / 9 FAIL
(top view: longest failing run 2..10 bands; side 1..20). Top rule raised to 3 adjacent (the plan's only allowed
change): still 8 / 9 FAIL, including both owner-accepted builds checked (it_thumper, it_glide_pack). Threshold not
loosened. Per-item: out/blender-hs/_v11_scratch/bands_dist/summary.txt.

**Hero check through the frozen camera:** it_smg camera_contested = grip, lamp, magazine, muzzle (their hero rows are
advisory). The muzzle x0.8 mutant's HERO muzzle w row is -4.1 % (pass, advisory); it_smg_A as is: +10.0 %. A spec with
muzzle.L x0.8 re-solves to FOV 29.2 deg (from 18.3) at a LOWER RMS (17.7 vs 18.0 px): the hero cannot pin the FOV of an
SMG (flat FOV profile, no twins, no vertical circle), so the camera absorbs near-part length.

## v11.1 (hero-led, 2026-10-12, research/WORKFLOW-V11.md §11; implementer seat)
Setup loop: `bash scripts/hs/tests/v11_freeze.sh <s> <ortho base cam> <out cam> 4 [--absorb-test p.d]` (logs in
`<out dir>/freeze_log/`). Acceptance: `scripts/hs/tests/test_camera_v11.ps1` (+ `tests/mutants.py`).

**FOV pin (§11.2):**
| item | method | pin | band (+2 px) | pinned | twins / ellipse / edges | notes |
|---|---|---|---|---|---|---|
| it_smg (final) | twins+ellipse | 31 deg | 24..37 | **no** (band 13 > 10) | 31 / 29 / 29 | round 1 (ortho spec): twins 34 vs ellipse 24 -> disagree > 8; the led spec moves the FOV each round (24 -> 31 -> 35 -> 32 -> 31); lead max move 30.7 / 25.0 / 16.2 / 7.7 %: NOT converged (< 1 %) in 4 rounds |
| it_thumper | twins (pads) | 8 deg (floor) | 8..16 | yes | 8 / - / 15 | elevation held 16.15 (ellipses); every proxy part camera-contested, RMS without them 20.19 > 20 -> hero_gate ADVISORY (look-only): nothing is hero-led, the spec stays the turnaround |

**Absorb test (it_smg, muzzle_tube.L x0.8 at the held FOV):** final camera RMS 16.88 -> 17.24 px (+0.36), part edge
residual 11.2 px -> ABSORBED (rule: +2 px or 20 px). Rounds 1 / 3 / 4 said WORSE (23.0 / 24.3 / 25.8 px), round 2
ABSORBED: the verdict flips with the FOV. Not met.

**Hero-led it_smg values move with the FOV:** muzzle.L / receiver.L 0.305 (FOV 23.7) / 0.290 (34.7) / 0.285 (31.0, final
spec) / 0.2725 (final camera with muzzle_tube led: tube L 0.036 < its own D 0.059, implausible); turnaround 0.30;
it_smg_A 0.284. The hero-led method does not lengthen the muzzle; at FOV ~30 it shortens it.

**Mutants under the hero-led spec (new hard keys over identity):** block-out a / b / c / e all FAIL on their key;
it_smg_A identity FAILs on muzzle_tube.D +24 % (A builds the device as one object at collar diameter) and on
muzzle_tube.L / muzzle_collar.L (the one object matched by both split rows: a naming artefact), while the group
muzzle.L is +9.9 % (pass) and muzzle.L / receiver.L -0.3 % (pass); A b (width x0.8) and c (diameter x1.3) add no new
target key (A's base faults already fail them; c adds the D/receiver.H ratios); thumper b adds nothing (housing.D
already -14 % against the turnaround median); uniform x1.02 rel rows add hero.top_rail.h (block-out) / sigma (A).
it_thumper pass 18: GATE FAIL, 12 SPEC keys (all `led_by ortho`: cap.L -40 %, tbar.L -33 %, striker.L +36 %, ...).

**HBANDS calibration (`hbands.mjs --calibrate`, the 9 finished builds' concept.png through their OWN pre-v11 cameras):**
FAIL at 2-adjacent 7 / 9, at 3-adjacent 4 / 9; it_glide_pack PASS (both rules), it_thumper FAIL (both; longest run 7).
The hard condition (thumper + glide_pack pass) is not met: HBANDS stays ADVISORY.

**Live-gate condition (§11.4): NOT met** (it_smg pin, it_smg absorb, it_thumper identity).
