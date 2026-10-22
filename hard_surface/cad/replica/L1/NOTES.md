# L1 replica - RPi 4 official case (red/white) + ISO 4017 M8x40
Build: `PYTHONPATH=. venv_cad python -m cadkit.worker replica/L1/model.py out/replica/L1/rN --tris 4000 --hq`, render with cadkit/render_hq.py, compare with `replica/L1/iou.py <glb> <outdir>`.

## Rounds
- r1: all ops OK (6 fillets, 30 booleans, 0 fuzzy/manifold fallbacks), all solids valid. Helical thread sweep worked. Defects: bolt too close to case, no recessed port frame.
- r2: added recessed rounded port frame (R3), moved bolt clear. All valid, 0 failed fillets/booleans. IoU tool written; first run exposed glTF Y-up axis bug in the tool (fixed) and flood-fill seeding bug (fixed).

## IoU per view (r2)
| view | ref | IoU |
|---|---|---|
| bolt side | B1 drawing (registered by k+l = 45.3 mm) | 0.735 |
| bolt end (hex) | B1 drawing (registered by s = 13) | 0.946 |
| case top / side / end | R1 envelope (97x70x25 rounded rect) | 0.997 / 0.991 / 0.989 |
Caveat: B1 is a generic, not-to-scale DIN 933 schematic (its d/l and e/k ratios do not match M8x40), so bolt-side IoU is capped by the ref, not the model. Case IoU is vs spec envelope only (no ortho blueprint of the case found) - it checks dimensions, not form.

## Dimension errors
| dim | ref | model | err |
|---|---|---|---|
| case L x W x H | 97 x 70 x 25 (R1) | 97.0 x 70.0 x 25.0 | 0 (but sources disagree: 96x70x30) |
| board/port positions | R2 | from R2 | 0 (board-in-case offset 6/7/4 mm estimated) |
| bolt s / k / e / dw / P / l | 13 / 5.3 / 14.38+ / 11.63 / 1.25 / 40 | same | 0 (head e = 15.0 sharp hex, then 30 deg chamfer) |

## Fillet / boolean failures
None (r1, r2): fillets plan R6, lid top R5, base R1.5, recess R3, pcb R3 all applied at full radius.

## Kit gaps
- No silhouette-IoU / ref-overlay tool in cadkit; implemented locally (replica/L1/iou.py). Note glb is Y-up.
- No PDF rasteriser in venv_cad (pymupdf absent) - board drawing read by eye.

## Remaining defects (honest)
- Case radii (R6 plan, R5 lid), wall 2 mm, split heights (7 / 18 mm) and S-curve position are photo estimates, not measured.
- Missing: embossed raspberry logo on lid, lid/base snap seam gap, LED light-pipe holes, GPIO/camera slots of the removable lid, internal standoffs/clips, underside feet; SD notch position estimated (not visible in R3).
- Port cut-outs are plain rectangles (real ones have rounded corners/lead-ins); connectors are simple blocks.
- Bolt: thread is a swept 60 deg triangle (approximate ISO 68 profile, no root radius); no thread run-out under head; head corners not trimmed to e-min ring exactly.
