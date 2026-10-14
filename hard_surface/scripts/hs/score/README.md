# scripts/hs/score — interior likeness score for hard-surface builds

The outline score (`judge_mesh.mjs` agree / IoU) cannot see what reviewers mark down: part shapes, openings, grooves,
tone values, wall thickness, all of which sit inside the silhouette. `likeness_score.mjs` compares a build's four
ortho renders with `subjects/<s>/turnaround/*.png` inside the silhouette. It is image-only (it needs no Blender and no
mesh), deterministic, and costs about 1.5–3.5 s of CPU per build once the sources are cached.

Node rather than Python: the system Python has no numpy or PIL, and Blender's Python has numpy but no PNG decoder.
The repo already reads PNGs with `sharp` (`scripts/registered.mjs`).

## Use

```powershell
# from hard_surface
node scripts/hs/score/likeness_score.mjs --subject pistol                                  # out/blender-hs/pistol/{side,front,rear,top}.png
node scripts/hs/score/likeness_score.mjs --subject pistol --prefix pass8_                  # a given pass
node scripts/hs/score/likeness_score.mjs --subject pistol --build out/blender-hs-exp/haiku/pistol --json
```

In code, call `import { scoreBuild, scoreFiles } from "./likeness_score.mjs"`. Source views are cached for each
process, so a variant sweep should score many builds in one process.

Output: `likeness` = `interior` x `iou`, with `interior` in [0, 1] and a breakdown for each view.

| signal | what it measures | per view |
|---|---|---|
| `iou` | silhouette IoU after the best ±12 px shift (`iou0` = no shift). This is the gate. | |
| `edgeF1` | F1 of interior Sobel edges (L* gradient > 0.06), counted as matched within 2 px (4 canvas px), only inside the eroded overlap of both silhouettes: ink lines, grooves, panel splits, serrations | w 0.3 |
| `ssim` | SSIM on L* (7x7 windows) inside the overlap: local structure plus contrast | w 0.2 |
| `toneSim` | 1 − mean \|ΔL*\| / 25 over a grid of 16-canvas-px cells: regional values ("housing 10–25 levels too light") | w 0.2 |
| `colourSim` | 1 − mean ΔE76 / 30 over the same grid: hue accents | w 0.1 |
| `openF1` | F1, within 2 px, of "opening" pixels: see-through holes (background enclosed by the silhouette) plus dark recesses (open v2, 2026-10-10: L* < 25, < 60 % of the mean of the *foreground* in their 21x21 surround, < 0.65 × the image's own foreground median L* in its 96 px region, and wider than 2 working px, so ink lines, outline rims and dark-painted parts are not openings): bores, windows, guards, slots. `LIKENESS_OPEN_V1=1` reproduces the old rule. See CALIBRATION.md "Open signal v2" | w 0.2 |

The views are weighted by interior area. Drift rects in `views.json` are don't-care. The registration shift is
searched on the silhouette only, so reviewers' "2–3 mm registration offset" costs nothing.

## Per-part score (part_score.mjs): ranking variants of ONE part

The whole-view score moves only 0.001–0.01 when one part changes. `part_score.mjs` restricts the signals to the part's
own region, which it takes from a per-part ID pass of the build:

```powershell
# 1. render each candidate (BASELINE and its variants) = run_pass.py + an ID pass, one Blender run each, never into a subject folder
& "C:\Program Files\Blender Foundation\Blender 5.1lender.exe" -b --factory-startup --python-exit-code 1 `
    --python scripts/hs/score/part_pass.py -- --subject pistol --build out/score/x/v1/build.py --out-dir out/score/x/v1
# 2. rank them on one part: the FIRST --build is BASELINE (its registration shift is reused by all)
node scripts/hs/score/part_score.mjs --subject pistol --part barrel --build out/score/x/base --build out/score/x/v1 --build out/score/x/v2
node scripts/hs/score/part_score.mjs --subject pistol --build out/score/x/base --all-parts     # every part of one build
```

- **Region**: `part_pass.py` re-renders the four orthos (same frame.json camera, kr/ku and judge sigma as the pass)
  with Workbench flat object colours, one colour per `ob["part"]` role, no AA and no ink. The visible role per pixel is
  saved as `passN_ids_<view>.bin`. The ID map is moved by the view's silhouette registration shift, then
  closed, hole-filled (bores, guard openings) and padded. When candidates are ranked together, the region is the union of
  their regions.
- **Signals in the region**: `sil` (silhouette IoU), `edge` (Sobel edge F1 within 2 canvas px, outline included),
  `ssim`, `tone` (blurred |ΔL*|, two-sided), `value` (1 − |mean L* source − mean L* build| / 20: saturating, two-sided;
  overshooting the source's value costs as much as undershooting), `open` (openings: see-through holes, notches/slots
  open to one side and dark recesses darker than 0.65 × the image's own median L* in the region; mean of pixel F1,
  component F1 and area ratio). Weights: open 0.25, edge 0.22, sil 0.18, ssim 0.13, tone 0.12, value 0.10.
  edge / ssim / open run on the build's L* mapped affinely onto the source's (mean and spread in the region), so painting
  a part darker or lighter cannot buy edges or "recesses"; only tone and value see the raw value.
  Views are weighted by region area.
- **Concept view** (2026-10-10): `part_pass.py` also renders the ID pass in the judge's concept camera
  (`passN_ids_concept.bin`). The concept render is not pixel-aligned with the painting, so `alignLocal` searches a
  scale + shift of the painting per part on BASELINE (silhouette + gradient NCC, pulled toward the global registration)
  and every candidate reuses it. Weight 0.5 × region area; skipped when the alignment is weak (gradient NCC < 0.30 or
  silhouette NCC < 0.75; e.g. the gatling barrel cluster, which the concept paints thinner with daylight between).
  ranking.md says whether it was used.
- **Use**: rank candidates of the SAME part in one call, and treat |Δ| < 0.004 as a tie (ties go to BASELINE). It
  ranked BASELINE above 20/20 controlled single-part degradations, 17/20 beyond that floor, median margin 0.048 (the
  whole score: 8/20, median 0.0026). Limits and the table: **PART-CALIBRATION.md**.

## Files

- `likeness_score.mjs`: the score (library and CLI).
- `calibrate.mjs`: collects the ground truth (Opus judge set and blind reviews), scores it, and writes Spearman,
  permutation p, within-subject pair concordance and leave-one-out weight fits to `out/score/calibration.json`.
- `sanity.mjs`: synthetic probes on a subject's own turnaround (identity, flat fill, blurred interior, +25 lighter,
  openings closed, 8 px shift). Writes `out/score/sanity.json`.
- `CALIBRATION.md`: results, failure cases and the verdict. **Read it before ranking anything with this score.**
- `part_pass.py`: Blender. Runs run_pass.py's `main()` unchanged (loaded as closeups.py does), then the per-part ID pass
  (`passN_ids_<view>.bin` + `passN_ids.json`). `--ids-only` reuses an existing `passN_stats.json`.
- `part_score.mjs`: the per-part score (library: `loadCandidate`, `scorePart`, `partRegion`; and CLI).
- `variants.mjs`: the 20 controlled single-part variants of pistol / pump_shotgun / gatling_gun (`--make`, `--run`,
  at most 4 Blender runs at a time) under `out/score/variants/`.
- `part_calibrate.mjs`: scores them and writes `out/score/part_calibration.json`.
- `PART-CALIBRATION.md`: the variant table, noise, misses and the verdict for the per-part score.
