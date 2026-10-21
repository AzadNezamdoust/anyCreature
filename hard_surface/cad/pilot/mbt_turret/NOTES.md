# mbt_turret pilot - notes

- start: 2026-10-21T17:28:13+03:00  end: 2026-10-21T17:30:59+03:00  (wall ~2 min 46 s, per Get-Date)
- rounds used: 2 (0 failed); final round: 2
- final tris: 1112 (budget 6000); LOD1 ~556, LOD2 ~274; 6 parts, all valid; bbox 9.65 x 3.60 x 1.75 m (0% vs SPEC)
- final round ops: fillet/chamfer 4 calls, 0 reduced, 0 failed, 0 retries; booleans 29, 0 fuzzy, 0 manifold, 0 failed
- earlier round 1: roof-edge chamfer 0.06 reduced to ~0.051 (7 bisection retries); no CadOpError in any round
- parts: turret (olive, incl. bustle + loader hatch), gun (mantlet + stepped 8-gon barrel, fume extractor, muzzle, bore; separate for elevation, trunnion ~x=-1.8 z=0.65), cupola, cupola_windows (#a8b4bd), roof_mg, smoke_launchers

## Kit bugs / pain points
- No kit bugs hit. rounds.jsonl is fine, but PowerShell-written tools may add BOM issues reading it (not a kit bug).
- No pivot metadata in the contract: the gun part has no way to declare its elevation pivot (only noted here / PIV var).
- Edge selection for chamfers is coarse (edges_on_plane max-Z picked the whole roof outline incl. short bustle edges, which forced the reduced chamfer in r1).
- Each round ~40 s (model ~20 s, mesh+render ~20 s), dominated by many small fuse calls.

## build123d easy / hard
- Easy: loft between symmetric planform polygons gave the sloped cheeks + wedge front in 2 lines; RegularPolygon+extrude for low-poly barrels/cupola; Pos/Rot algebra placement.
- Hard: no direct "prism along X" (needed Rot wrapper); orientation of rotated tubes (smoke launchers) is trial-and-error; group_by edge selection needs care.

## Remaining likeness misses
- Smoke-launcher tubes read a bit messy; mantlet could be taller/more wedge; no roof detail beyond hatch/cupola.
