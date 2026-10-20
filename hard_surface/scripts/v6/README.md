# WF v6 — multi-view pipeline: the per-subject contract (V6-2)

A subject opts in by adding `subjects/<s>/turnaround/views.json`; `scripts/loop.mjs` then runs the v6 path
(`scripts/v6/loop6.mjs`), everything else keeps v4/v5. Modeller's eyes: `node scripts/v6/view.mjs --subject <s> --module <m.mjs> [--out <dir>]`.

## subjects/<s>/turnaround/views.json
```json
{ "views":   { "<name>": { "file": "side_right.png", "right": [0,0,-1], "up": [0,1,0] }, ... },
  "anchor":  { "dim": "W" | "L" | "H", "m": 2.44 },
  "origin?": { "x": "centre" | "min" | "max", "y": ..., "z": ... },
  "families?": { "body": "<regions.json zone>", "table?": { "<family>": "#rrggbb" | ["#hex", ...] },
                 "viewTable?": { "<view>": { "<family>": "#rrggbb" | ["#hex", ...] } },
                 "fgMax?": 235, "enclosedFg?": false, "holes?": { "<view>" | "concept": [[x, y], ...] }, "spanOpen?": 2 },
  "drift?":  { "audited?": "<who, when>",
               "<view>" | "concept": [{ "id": "D1", "rect": [x0, y0, x1, y1], "decides": "<view> | concept", "why": "..." }] } }
```
- `right` / `up`: the author-frame unit axes the image's +X / −Y run along (axis-aligned); `right × up` points at the
  camera. Optional per view `shift: {right, up}` (m, measured on the reference, with a `_shift` evidence note): moves
  that view's origin when an asymmetric body-colour attachment skews the span rule (delivery_truck rear: +0.11). Pixel map: `X = s·(p·right) + ox`, `Y = −s·(p·up) + oy`, one px/m `s` for all views. Any view names; the
  order is the sheet's column order. Optional per view `scale: {right: k}` (WF v8 WP3; measured, with a `_scale` note;
  0.5 < k < 2): the drawing's right axis is drawn k x too long — its right-axis spans count 1 / k in the residuals, s and
  dims, the model is rasterised k x longer along right (`basisOf`), `pxToView` / `comps` / `profile` divide by it, a
  `shift.right` moves k x as many px. Absent = byte-identical (the v6 loop's `viewRows` ignore it). `scale: {up: k}`
  (2026-09-28; the same contract along the up axis, `_scale` note, 0.5 < k < 2; `{right, up}` may be combined): a view drawn
  k x too long along its UP axis (a top view uniformly stretched across, e.g. the ambulance top's 1.148) — its up-axis spans
  and bbox count 1 / k, `basisOf` scales `up`, `pxToView` / `comps` / `profile` / the doctor's centring row / hull.mjs divide
  by it, a `shift.up` moves k x as many px. Absent = byte-identical (view.mjs on taxi + school_bus: JSON and sheet PNG
  identical; `gold.mjs eyes-check` clean on all ten subjects).
  Note: scale.right / scale.up = k means the drawing is k x TOO LONG along that axis (a view drawn 15% too wide gets
  k = 1.15, never 0.87); verify every proposed scale with a doctor run (the view's residual must shrink) before writing it.
- **Class author frames.** Vehicle: nose **+z**, near flank **+x**, **y** up, ground y = 0, x and z centred (bus views:
  side `right [0,0,-1]`, front `[1,0,0]`, rear `[-1,0,0]`, top `right [0,0,-1] up [-1,0,0]`). Building
  (`scripts/template-building.mjs`, `meta.front "-Z"`): x centred, ground y = 0, **front face at z = 0 facing −z**, depth
  toward +z ⇒ front view `right [-1,0,0] up [0,1,0]` (camera on −z), origin `z: "min"`.
- **Dimensions** per world axis: x→W, y→H, z→L. Each view measures its right-axis and up-axis dimension: y = the
  foreground bbox (ground to top), x / z = the span of the **body** colour family. Views sharing an axis share that
  dimension; `reg.residuals[D][view]` = px/mean − 1 (target ±3 %), `Wbbox`/`Lbbox` = overall bboxes (reported only).
  `s` = mean px of `anchor.dim` / `anchor.m`; `reg.dims` = the turnaround's dimensions at that scale.
- **origin**: where the author origin sits on each axis ("min" = the edge where that coordinate is least); default = the
  class frame from the rules registry (vehicle `{x:"centre", y:"min", z:"centre"}`).
- **Colour families** (never hard-coded): the concept palette = median colour of each `regions.json` zone's rects on the
  concept; zones closer than `MERGE_RGB` (40) join one family; the family holding `families.body` (default: first zone
  named `body*`) is `"body"`. Pixels: bg if the darkest channel ≥ 235, else the nearest family (> `FAR_RGB` = "other").
  A module zone's family = the family nearest its palette colour. `families.table` replaces the derived table (subjects
  without regions.json; then `families.body` names a table key).
- **Per-view colours** (optional, `families.viewTable`, with a `_viewTable` note): for ONE turnaround image, the colours
  of the named families (a generator draws a view a little lighter / darker than the concept). `ortho.mjs viewFamilyTable`
  classifies that image (readImage in loadTurnaround / hull.mjs, measure.mjs `sample` / `runs --view`) with the family
  names and indices unchanged; a family not named keeps its colours; "_" keys are notes; a key that is not a view or a
  name that is not a family throws; absent = byte-identical (view.mjs on taxi / school_bus and the taxi doctor were
  unchanged by it). Written by `node scripts/v7/turnaround.mjs families --subject <s> --apply` (per view: foreground
  colour clusters matched to the families with ONE colour offset, every family's colours moved by it plus the view's own
  unambiguous clusters; ambiguous / far clusters are only reported — a human sets them); measured on the live images, so
  `hull.mjs --views-dir` ignores it and turnaround.mjs re-derives it for every other image set (and `install` writes it for
  the installed one).
- **Span opening** (optional, `families.spanOpen: n`, an integer 2..16 px, with a `_spanOpen` note): the x / z body spans
  (`spanOf`: every column / row holding >= 5 % of the densest line's body px) are counted on the body-family mask after a
  morphological opening with an n x n square (`openMask`: erosion then dilation, the union of every n x n square inside
  the mask). A dark outline's anti-alias greys classify as body; their 1-px halo columns / rows (mirror heads, lamps) pass
  the 5 % cut and widen W / L (ambulance front 313..712 = 399 px around a 332-px box; icecream_van front from col 283, the
  body at 337); n = 2 drops every line thinner than 2 px. Only the registration's spans (residuals, s, dims, origins,
  the doctor's residual-* rows, hull.mjs / turnaround.mjs registration) see it; classification, IoU, masks and the
  measure tools are unchanged; absent = byte-identical (view.mjs on taxi and `gold.mjs eyes-check` unchanged).
- **Mask rule** (orthos + concept): bg = darkest channel ≥ `families.fgMax` (235). Opt-in `families.enclosedFg: true`: bg
  = only the near-white 4-connected to the image border (enclosed white parts are fg, nearest family) or to a
  `families.holes` seed (`{"<view>" | "concept": [[x, y], ...]}`, that image's px, on a see-through opening's white).
- **Drift** (WF v8, research/v7/WF-V8-PLAN.md): each rect marks where that image disagrees with the others (`decides` =
  the image that decides there), in that image's own px, half-open (a px X is inside when x0 ≤ X + 0.5 < x1) — the
  coordinates of the pages and measure.mjs. Drift px are don't-care for **agree** = the silhouette IoU with them in
  neither I nor U (orthos: `viewTarget().care` on the judge raster; concept: `targetState(…, {dontCare})` → OCCLUDED).
  The raw `iou`, `score`, sigma, the frame fit and the measure tools never see them (`maskOptions` never carries them).
  Bound: ≤ 5 % (`DRIFT_MAX`) of a view's reference foreground; above it view.mjs / variants.mjs print a WARN line
  (regenerate the view instead; a whole-view proportion disagreement is a setup ruling, not drift). Non-array keys
  (`audited`) are notes; a bad rect or an unknown view throws. Only `gold.mjs drift add|rm` edits them, at a round
  boundary (WP5). No `drift` key: sheets, pages and IoU numbers are unchanged and agree = iou.
- **View JSON** (`<module>-view.json`): per view `iou`, `agree`, `drift` (the reference-foreground share under its
  rects), `zone`, `fam`; `minOrtho`, `minView`, `minAgree`, `score`, `checks`, `placementRows`, `tris`, `blobs` (the blob
  table, scripts/v7/README.md). The v6 loop's `viewRows` (judge() still returns them) are not written there.

## subjects/<s>/prior.json (schema = the bus card)
`{ class, real: {source, W, H: [lo,hi], L: [lo,hi], ...}, anchor: {dim, m, why}, stylisation: {LoverW, HoverW, ...measured
on the turnaround}, softRanges: { <KNOB name>: [min, max] } }`. `softRanges` are the only machine-read field (loop START:
those knobs get these ranges, `locked` dropped); the rest is evidence for seats/owner.

## Rules registry (`scripts/v6/rules.mjs`)
`registerRules(cls, { frame: {origin}, groups, checks(parts) → {groups:[{name, parts, float, why}], clips:[{a,b,volume}],
pass}, rows(checks) → ["PLACEMENT: ..."], symmetry?: {view, exclude: RegExp}, axisWords?: {"+z": "forward", ...} })`;
`await rulesFor(cls)` returns it, importing `scripts/v6/rules-<cls>.mjs` on first use (that file calls `registerRules`);
an unknown class gets a no-rule entry. `classFrame(cls)` is the sync frame lookup. Vehicle is registered in rules.mjs.

## Loop (v6 path) and judge
START template (or `--from`) + frame knobs, stretched per axis to `reg.dims`, `softRanges` applied → multi-view FIT
(`mvfit.mjs`: body stage, then features; a knob without `group`: frame knobs / `rc_*` = feature / else body) → BUILD
(READY calls) → re-FIT → LOOP ≤ K with view-tagged rows (`judge.mjs viewRows`) + placement rows. Guard: loads; tris;
gate; placement rows not more / no new; min per-view IoU not lower (±0.002); score (concept×2 + orthos)/(2+n) ≥ best +
0.001. Target: gate PASS, no placement row, every ortho ≥ 0.92, concept ≥ 0.96. `--v5-detail on` adds the V5 per-feature
FIT, per-face palette and exactness stop (default off); `--no-v6` forces the v4/v5 path. Each step's `sheet.png` = the
6-view judge sheet (true-colour cel: facing 100 %, sides 85 %, tops 105 %); wall clock 30 min (`LLMM_LOOP_TIME_MS`).
