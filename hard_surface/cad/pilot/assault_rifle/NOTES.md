# assault_rifle pilot

- Start 2026-10-21T17:28:16+03:00, end 17:31:42 (~3.5 min wall-clock).
- Rounds used: 4 (r1, r2 failed; r3, r4 ok). Final round: 4. Final tris: 2348 (budget 8000).
- Final round ops: chamfer/fillet calls 11 (0 fillets): 10 ok, 1 reduced, 0 failed, 7 retries.
  Booleans 20: 20 plain ok, 0 fuzzy, 0 manifold, 0 failed.
- CadOpErrors in failed rounds: r1 `fuse 'rail_ridges'` (tool given as a list); r2 `fuse 'stock'` (tool given as a list).

## Kit bugs / pain points
- `fuse(a, [b, c])` with a list tool always fails: safe_boolean forces TypeError on the plain path for lists,
  then fuzzy and Manifold both fail ("Null TopoDS_Shape object"). Workaround: wrap in `Compound(list)` or
  chain fuses sequentially. The error hint (coplanar faces) is misleading for this case.
- rounds.jsonl lives in pilot/<asset>/, not out/ (minor, just unexpected).

## build123d easy / hard
- Easy: side-profile `Plane.XZ * Polygon` + symmetric extrude covers most rifle parts; RegularPolygon for octagonal
  handguard/brake; SlotCenterToCenter for vents; edge filtering by axis for chamfers.
- Hard: remembering Plane.XZ orientation (local y -> world Z, normal -Y); no curved magazine without splines, so a
  raked polygon stands in.
