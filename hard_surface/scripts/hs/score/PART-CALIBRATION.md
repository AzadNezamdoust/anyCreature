# Part calibration: part_score.mjs on controlled single-part variants (2026-10-10)

Reproduce:

```powershell
# from hard_surface
node scripts/hs/score/variants.mjs --make            # out/score/variants/<s>/<key>/build.py, base_a, base_b
node scripts/hs/score/variants.mjs --run --jobs 4    # part_pass.py = run_pass.py + ID pass, per variant (~2-6 min each)
node scripts/hs/score/part_calibrate.mjs             # -> out/score/part_calibration.json (+ .md table)
node scripts/hs/score/part_calibrate.mjs --own-shift # same without the registration lock -> part_calibration_ownshift.json
```

## What was tested

There are no human judgements on part variants yet, so this uses the only honest ground truth available: **20
controlled degradations** of 3 existing builds (out/blender-hs/pistol, pump_shotgun, gatling_gun). Each copies the
subject's `build.py` and edits ONE part: a bore closed, a wall thickened, an opening shrunk or closed, a groove count
cut, a part scaled 110 % or moved 5–15 mm. Each is expected to be worse than BASELINE. The subject's build is rendered
twice (base_a, base_b) to measure re-render noise. All renders use `run_pass.py --build <variant> --out-dir
out/score/variants/<s>/<key>`, so no subject folder was written.

Columns:
- **whole Δ** = `likeness_score.mjs` likeness (variant − mean of the bases)
- **part Δ** = `part_score.mjs` score of the edited part, over the union region of {base_a, base_b, variant}, views
  weighted by region area (the shipped default). The variants reuse base_a's registration shift.
- **equal views** = the same score with the four views weighted equally (shown for comparison, not shipped)
- **re-render noise** = |part(base_a) − part(base_b)|
- **max other-part |Δ|** = the largest change the edit caused in the score of any OTHER part (spill-over)
- **correct** = direction (part Δ < 0) / beyond the nuisance floor (see below)

## Table

| subject | variant (expected worse) | part | whole Δ | part Δ | part Δ, equal views | re-render noise | max other-part \|Δ\| | correct (direction / beyond floor 0.0039) |
|---|---|---|---|---|---|---|---|---|
| pistol | muzzle bore closed | barrel | −0.0017 | **−0.0637** | −0.0374 | 0 | 0.0041 (slide) | y / y |
| pistol | barrel wall 2.4 → 4.5 mm (bore 11.6 → 7.4 mm) | barrel | −0.0005 | **−0.0315** | −0.0185 | 0 | 0.0022 (slide) | y / y |
| pistol | rear-sight notch closed | sight | −0.0000 | **−0.0176** | −0.0204 | 0 | 0.0007 (slide) | y / y |
| pistol | slide serrations 6 → 3 | slide | −0.0090 | **−0.0118** | −0.0076 | 0 | 0.0008 (receiver) | y / y |
| pistol | trigger moved 5 mm forward | trigger | −0.0055 | **−0.4085** | −0.4085 | 0 | 0.0122 (receiver) | y / y |
| pistol | thumb safety moved 5 mm down | selector | −0.0030 | **−0.0239** | +0.0225 | 0 | 0.0150 (slide_stop) | y / y |
| pistol | magazine (floor plate) scaled 110 % | magazine | −0.0184 | **−0.2240** | −0.1654 | 0 | 0.0034 (receiver) | y / y |
| pump_shotgun | muzzle bore closed | barrel | −0.0003 | −0.0001 | −0.0002 | 0 | 0.0040 (sight) | y / **n** |
| pump_shotgun | barrel wall 2 → 6 mm | barrel | −0.0001 | −0.0001 | −0.0004 | 0 | 0.0029 (sight) | y / **n** |
| pump_shotgun | trigger-guard opening shrunk to 70 % | trigger_guard | −0.0028 | **−0.0681** | −0.0681 | 0 | 0.0477 (trigger) | y / y |
| pump_shotgun | pump grooves 4 → 2 | pump | −0.0068 | **−0.0062** | −0.0032 | 0 | 0.0001 (barrel) | y / y |
| pump_shotgun | stock scaled 110 % | stock | −0.0024 | −0.0018 | +0.0006 | 0 | 0.0285 (grip) | y / **n** |
| pump_shotgun | grip moved 10 mm back | grip | −0.0059 | **−0.1574** | −0.0830 | 0 | 0.0334 (trigger_guard) | y / y |
| pump_shotgun | trigger moved 5 mm forward | trigger | −0.0004 | **−0.0949** | −0.0949 | 0 | 0.0166 (trigger_guard) | y / y |
| gatling_gun | all six bores closed | barrel_cluster | −0.0018 | **−0.0069** | −0.0138 | 0 | 0.0044 (receiver) | y / y |
| gatling_gun | bore dia 23 → 14 mm | barrel_cluster | −0.0001 | **−0.0043** | −0.0086 | 0 | 0.0028 (receiver) | y / y (by 0.0004) |
| gatling_gun | spade-grip opening shrunk to 70 % | grip | −0.0052 | **−0.0800** | −0.0515 | 0 | 0.1732 (trigger) | y / y |
| gatling_gun | carry handle moved 15 mm up | handle | −0.0187 | **−0.2443** | −0.2234 | 0 | 0.0100 (grip) | y / y |
| gatling_gun | drum scaled 110 % | drum | −0.0648 | **−0.2068** | −0.1646 | 0 | 0.0185 (receiver) | y / y |
| gatling_gun | trigger moved 10 mm forward | trigger | −0.0015 | **−0.1969** | −0.1969 | 0 | 0.0186 (grip) | y / y |

Per-view and per-signal deltas are in `out/score/part_calibration.json` (rows[].views, rows[].signals) and the `.md`
printout.

## Noise

- **Re-render noise is exactly 0.** run_pass.py renders are deterministic: base_a and base_b give the same pixels,
  sigma and scores. So "direction correct" alone is trivially true for any score that sees the change (the whole
  score also gets 20/20 by direction). The margin has to be judged against a nuisance floor instead.
- **Nuisance floor = 0.0039**: the largest |Δ| that any edit caused in a part whose region does not touch the
  edited part's region (75 such pairs, p95 0.0002, max 0.0039). This is the change in score you get for a part that
  was not edited, so a Δ below it cannot be attributed to the part. Parts whose regions touch (trigger in the guard,
  grip next to the guard) spill much more, median 0.0007 and up to 0.17 (gatling: shrinking the grip opening cuts
  into the trigger's view). That is real: the trigger's surroundings did change.
- **Registration shift flips are a second noise source.** A one-part edit flipped the whole-view silhouette shift by
  1 working px (2 canvas px) in 4 of 20 builds (notch_closed, mag_scale110, grip_move10, drum_scale110). Without the
  lock, such a flip moves every part's score by about 0.005 to 0.015, which was the size of pistol notch_closed (−0.0068
  unlocked, −0.0176 locked). `part_score.mjs` therefore reuses the first `--build`'s (BASELINE's) shift for every
  candidate by default (`--own-shift` turns it off; that table is in `out/score/part_calibration_ownshift.*`).
  Unlocked, the nuisance floor rises to p95 0.0051 / max 0.0090, and 16 / 20 variants clear the max floor instead of 17.

## Summary

| | part score | whole likeness |
|---|---|---|
| direction correct | 20 / 20 | 20 / 20 |
| beyond the nuisance floor (0.0039) | **17 / 20** | 8 / 20 |
| median Δ | **−0.048** | −0.0026 |
| median Δ / floor | **12x** | 0.7x |

Severity order within one part is also right where it was testable: pistol barrel, bore closed (−0.064) worse than
wall thickened (−0.032); gatling, bores closed (−0.0069) worse than bores narrowed (−0.0043).

**Openings now count.** Closing the pistol's muzzle bore moves the part's opening signal by −0.20 and the part score
by −0.064, 37 times the whole score's change. In the whole score, painting over every opening of a subject moved it
only 0.02–0.08. The front view alone moves −0.11 (pistol), −0.04 (gatling).

## The three misses, and the weak ones

1. **pump_shotgun bore closed / wall thickened (Δ −0.0001).** This is not a scorer failure. The current build's bore
   does not read as a bore: in the front render it is a mid-grey disc, because the cut runs through to the
   receiver's lit bolt channel. Closing it changes almost no pixel (the source draws a black bore). The scorer
   correctly reports "no visible change". Side-find for the shotgun build: its bore reads closed in every view.
2. **pump_shotgun stock 110 % (−0.0018; equal views +0.0006).** It is worse in side/front/rear (−0.038, −0.025,
   −0.010) but **better in top (+0.076)**. top.png draws the butt 0.104 wide against the build's 0.068 (the build
   followed rear.png, FEATURES.md). The source views disagree with each other, so "known-worse" is not true in every
   view. The pistol safety moved down shows the same pattern (side −0.16, front +0.16, rear +0.09). Area weighting
   ranks both right, equal view weighting does not.
3. **Weak: gatling bores (−0.0069 / −0.0043, 1.1–1.8x the floor).** The bores are visible only in the front view.
   The barrel cluster's side and top regions are 5x larger and do not change, so area weighting dilutes a change
   that is −0.04 in the front view. This does not change the ORDER of candidates (the unchanged views add the same
   amount to every candidate), only the margin over the floor.

## Verdict: can it rank single-part variants? **Yes**, with conditions

It ranked BASELINE above the variant in 20 / 20 controlled single-part degradations. In 17 / 20 the margin is beyond
the nuisance floor of 0.0039, with a median margin of 0.048 (12x the floor). The whole likeness score
clears that floor in 8 / 20, with a median of 0.0026. It separates the part changes the whole score could not:
a bore closed (−0.064 vs −0.0017), a trigger moved 5 mm (−0.41 vs −0.0055), a guard opening shrunk (−0.068 vs
−0.003), a sight notch closed (−0.018 vs 0.0000).

Conditions and limits:
- **Rank candidates of the same part together** (`--part <role> --build BASELINE --build v1 ...`), so they share one
  region and BASELINE's registration. Treat |Δ| < 0.004 as a tie, and a tie goes to BASELINE.
- **The ground truth is synthetic.** Every variant is a pure degradation of one part. It has not been tested on
  plausible alternatives ("different, maybe better" variants), on human pairwise judgements, or on real Haiku/Sonnet
  part edits. The next step from CALIBRATION.md still stands: collect 30–50 blind pairwise judgements on real part
  variants and measure concordance at the deltas those variants produce.
- **When the source views disagree** (stock, safety), the score follows the area-weighted majority of views. A
  reviewer who trusts one view more may disagree.
- **Changes visible in one small view only** (bores of big guns) clear the floor by only 1–2x. Use the per-view
  breakdown (`--json`, rows[].views) when a decision hangs on such a change.
- Overlapping parts share pixels. An edit to the guard also changes the trigger's score, so rank the edited part,
  not its neighbours.
- Cost: one Blender run per candidate (run_pass + ID pass: about 100–350 s with 4 runs in parallel on this machine),
  then about 10–30 s of Node to score a candidate set. The ID pass is part_pass.py. run_pass.py is unchanged.

## 2026-10-10 revision: tone extremes, concept view, guarded search renders

Why: the first Haiku wave (out/search/*/batch_*) showed the score rewarding a value extreme. gatling v03 painted the
barrels near-black and won (+0.047). Measured in the part region, the source's mean L* is 29.4, BASELINE 35.0 and
v03 22.3, so v03 overshoots the source by more than BASELINE misses it. `tone` was already two-sided (|ΔL*|) and had
penalised v03 (−0.126). The win came from the structure signals. Near-black barrels counted as "dark recesses" in
`open` (+0.165), and the higher contrast bought Sobel edges (+0.134).

Changes (part_score.mjs):
- `value`: 1 − |mean L* source − mean L* build| / 20 over each image's own foreground in the region. It saturates and
  is two-sided, weight 0.10. meanLS / meanLB are reported per view and in ranking.md.
- Dark recess = L* < 30, < 0.65 × the 21×21 surround, AND < 0.65 × the image's own median L* in the region. A uniformly
  dark part is no longer a recess.
- edge / ssim / open run on the build's L* mapped affinely onto the source's mean and spread in the region (gain
  0.5..2). Only `tone` and `value` see the raw value.
- Concept view: an ID pass in the concept camera (part_pass.py) plus a per-part local alignment of the painting
  (`alignLocal`: scale 0.80..1.20, shift ±40 working px, silhouette + gradient NCC with a pull toward the global
  registration), computed on BASELINE and reused by every candidate. Weight 0.5 × area. Skipped when gradient NCC < 0.30
  or silhouette NCC < 0.75.
- Weights: open 0.25, edge 0.22, sil 0.18, ssim 0.13, tone 0.12, value 0.10.

Recalibration (same 20 variants; the concept ID pass was added with `part_pass.py --ids-only`, and the ortho renders
are unchanged):

| | before | after (concept on) | after, `--no-concept` |
|---|---|---|---|
| direction correct | 20 / 20 | 19 / 20 | 19 / 20 |
| beyond the nuisance floor (re-measured p95) | 17 / 20 (floor 0.0039) | 19 / 20 (floor 0.0004) | 19 / 20 (floor 0.0005) |
| beyond the OLD floor 0.0039 | 17 / 20 | **18 / 20** | 18 / 20 |
| median part Δ | −0.048 | −0.038 | −0.044 |
| max far-part spill (nuisance max) | 0.0039 | 0.0028 | 0.0038 |

The miss is pump_shotgun bore_wall_thick (+0.0001). It was −0.0001 before. Both are the "bore does not read as a bore in
this build" case from the first table, so the score sees no visible change. pump bore_closed stays at −0.0006.
Concept alignment held for 14 of 20 variants. The concept term alone ranked 12 of those 14 correctly. The two it got
wrong are pump guard_small (+0.022) and trigger_move5 (+0.016): trigger and guard overlap, and the painting draws the
guard differently. It was skipped for the gatling barrel cluster (gradient NCC 0.25; the painting draws thinner tubes
with daylight between them), the pump barrel (0.21) and the pistol safety (too small to align).
Tables: out/score/part_calibration.md / .json (concept on), part_calibration_noconcept.md / .json.
