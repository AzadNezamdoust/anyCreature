# Visual-hull baseline — scripts/v7/hull.mjs on the live and drifted turnarounds (Opus 5.5, 2026-09-27)

Measured at 3dbdf91 (subjects/ and refs/ clean before and after the runs: the parallel semantic-fix worker had landed nothing
there): `node scripts/v7/hull.mjs --subject <s> [--views-dir subjects/<s>/turnaround-0-drifted]`, res 0.02 m (the 6 M voxel
cap: 0.021–0.024 m for bus, fire truck, garbage truck, ice-cream van), sub-cells ≤ 1 view px; PNG + JSON per set in the
session scratchpad (hull/). pickup's older `turnaround-1-drifted` added. residual = the largest |W / L / H| registration
residual (doctor residual-* rows); viewOnly = % of a view's foreground the other views carve away; conceptOnly = % of the
concept foreground outside the hull at the IoU-fitted frame (brackets: in ≥ 20 px blobs after the 1 px opening); hullOnly =
hull-only % (concavities no axis view carves); frame = fitted frameScale frameX frameY; s = wall time.

| set | residual max | viewOnly side / front / rear / top % | concept IoU | conceptOnly % | hullOnly % | frame | s |
|---|---|---|---|---|---|---|---|
| school_bus | W rear +0.5 | 0.0 / 4.0 / 2.9 / 1.0 | .946 | 2.9 (2.9) | 2.6 | 0.807 −22.7 +22.6 | 4.6 |
| pickup | W front −1.7 | 0.0 / 9.2 / 3.8 / 1.0 | .948 | 3.7 (3.6) | 1.7 | 1.006 +4.0 −9.5 | 4.0 |
| delivery_truck | W rear +7.4 | 0.0 / 2.7 / 2.9 / 0.2 | .957 | 1.8 (1.4) | 2.6 | 0.986 +3.5 −2.9 | 4.6 |
| taxi | W top −9.3 | 0.0 / 7.1 / 3.8 / 0.0 | .949 | 3.0 (2.8) | 2.2 | 0.986 +14.5 −2.8 | 3.6 |
| tractor | W rear −6.8 | 0.9 / 12.5 / 5.3 / 2.2 | .803 | 5.5 (5.4) | 17.8 | 0.985 +4.4 +3.9 | 4.2 |
| ambulance | W top −3.9 | 0.0 / 1.4 / 4.4 / 0.0 | .951 | 2.1 (1.8) | 3.0 | 0.982 −2.8 +5.0 | 3.4 |
| fire_truck | W rear +2.3 | 0.0 / 5.4 / 5.4 / 0.0 | .938 | 3.7 (3.3) | 2.8 | 0.977 +5.3 +1.9 | 3.0 |
| garbage_truck | W top −4.1 | 0.3 / 4.3 / 2.9 / 0.4 | .917 | 5.5 (5.4) | 3.0 | 0.956 −22.8 −4.5 | 3.5 |
| forklift | W rear +9.6 | 0.0 / 10.7 / 14.1 / 6.2 | .798 | 7.5 (7.4) | 15.8 | 0.990 +10.0 −1.5 | 3.6 |
| icecream_van | W top +15.5 | 0.1 / 1.3 / 4.7 / 7.6 | .925 | 4.5 (4.5) | 3.1 | 0.965 +2.3 +12.2 | 5.4 |
| garbage_truck 0-drifted | W front −9.1 | 2.3 / 4.0 / 4.2 / 7.9 | .914 | 5.3 (5.2) | 3.6 | 0.866 −39.4 +4.7 | 4.7 |
| icecream_van 0-drifted | W top +4.8 | 0.0 / 1.4 / 4.5 / 0.3 | .906 | 4.1 (4.0) | 5.8 | 1.087 +21.8 −10.4 | 4.4 |
| pickup 1-drifted | W top −15.7 | 0.1 / 7.2 / 16.2 / 0.5 | .876 | 7.6 (7.5) | 5.5 | 1.077 +20.2 −25.6 | 3.5 |

- Views vs views: the side view is carved ≤ 0.3 % in 9 of 10 live sets; the contradictions sit in front / rear, which must be
  mirror silhouettes in an orthographic set but are drawn independently (taxi front 7.1 %: the lower valance and tyre sides
  the rear lacks; tractor front 12.5 %: canopy posts at x ±0.6 m and rear fenders ±1.12 m vs ±0.5 / ±1.0 m in the rear). The
  residual rows are a poor proxy: the taxi's top W −9.3 % carves nothing (a body-colour span artefact, Wbbox 0.0 %).
- Views vs concept: every live set contradicts its concept by 1.4–7.4 % in blobs — garbage truck one 3.4 % blob (the concept's
  rear loader juts further back than any view allows: the audited hopper), forklift fork tines, mast top and rear wheel.
- Tractor: IoU .80 is mostly hullOnly 17.8 %, phantom volume beside the hood (the front view is filled there by the rear
  fenders, the top by the front tyres, the side by the hood), not a contradiction. Its conceptOnly is real: the exhaust stack
  stands elsewhere in the views (1.6 %), the concept's tyres reach lower and its canopy roof higher (3.0 %: it is taller).
- Regenerations: garbage truck 0-drifted → live cut the view contradictions (top 7.9 → 0.4 %, residual 9.1 → 4.1 %), not the
  concept one (5.2 → 5.4 %); pickup 1-drifted → live cut both (rear 16.2 → 3.8 %, concept 7.5 → 3.6 %); the ice-cream van's
  live top view is carved more (7.6 % vs 0.3 %: its near-side awning reaches x +1.51 m, 0.3 m past front and rear).
- Calibration: synthetic consistent set (hull.test.mjs) viewOnly 0.00 %, conceptOnly 0.28 % raw / 0 in blobs (the IoU fit
  shrinks a superset hull a little); hull frames match the gold modules' own within a few px (bus 0.807 vs 0.817) bar taxi / tractor.

## aspect — `hull.mjs --aniso`: the views' proportions against the concept's (Opus 5.5, 2026-09-28)

conceptOnly is one-sided: a hull too big or too tall still covers the concept (the fire truck's new set: conceptOnlyBlob
1.2 %, yet taller than its concept). `--aniso` fits the SAME hull to the concept with per-axis scales s = {W, H, L} (the views'
object over the concept's; H's coordinates divided by them about its bbox centre before the camera projection; frameScale
1, frameX / frameY free) and reports `aspect` = sH / sW - 1 (H/W), sL / sW - 1 (L/W), + = the views draw it taller / longer.

- Objective and search: the concept IoU of the scaled hull. The coordinate search of fitFrame (the first version) stalled at
  arbitrary points of a flat valley: an oblique concept camera (theta 21-25 deg from the flank) sees W foreshortened, so W
  against (H, L) is weakly determined — garbage_truck aH 0.91 .. 0.96 within 0.001 IoU, and five fits of one set gave H/W
  +6.1 / +7.9 / +5.3 / -5.0 / +2.7 %. Now: Nelder-Mead (log-scales + shifts, a restart per stage) on the IoU - lambda
  (ln^2 aH + ln^2 aL), lambda 0.25 (0.0023 IoU per 10 % of aspect: the least distortion that explains the concept inside a
  flat valley), point splats of the hull's camera-facing surface on a downsampled concept grid (coarse cells, then the
  refined sub-cells), 2-6 s; the reported IoU / conceptOnly are the exact footprint splat. A warm start (the set before a
  repair) holds sigma (the W scale): the before -> after change is then the new view's (turnaround.mjs repair / rejudge).
- Calibration (truth known): the synthetic set of hull.test.mjs H/W +1.0 %, L/W -0.4 %; stretched 10 % in H: +10.0 / -1.2 %
  (unit test, +-1.5 %). The five golds' own four views rendered from model.mjs vs their own concept renders (truth 0): H/W
  taxi -0.1, school_bus -1.7, delivery_truck +0.1, tractor -1.3, pickup -0.2 %; L/W -1.2 / -1.1 / -0.8 / -0.4 / -1.3 %. The
  taxi's views stretched 10 % in H: +8.5 % (the W valley takes 1.5 pts). The same live set at res 0.02 / 0.025 / 0.03 moves
  by up to 2 pts (garbage_truck H/W +2.5 / +0.4 / +1.1, L/W -8.6 / -10.1 / -10.7 %). Read aspect to about +-2 pts; the
  set-level KEEP rule's 0.5 pt aspect clause is below that spread (the warm start with sigma held keeps a one-view repair's
  before / after pair comparable: garbage_truck repair-2's candidate H/W -0.8 -> -1.5 % warm-started without the hold, a REVERT
  by 0.2 pts over the clause; -0.8 -> -1.0 % with sigma held, KEEP).
- The five new subjects' live sets before the 2026-09-28 pass (turnaround.mjs status, cold fits): H/W / L/W (H/L) ambulance
  +2.1 / -1.1 (+3.2) %, fire_truck +7.2 / -3.8 (+11.4) %, garbage_truck +2.5 / -8.6 (+12.2) %, forklift +2.0 / +2.2 (-0.2) %,
  icecream_van -6.2 / -3.7 (-2.6) % — the fire truck is drawn taller and the garbage truck shorter than their concepts;
  aniso concept IoU .950 / .944 / .954 / .822 / .955 vs isotropic .948 / .925 / .922 / .822 / .948.
