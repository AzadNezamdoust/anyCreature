# tenement_green pilot

- Start 2026-10-21T17:28:17+03:00, end 2026-10-21T17:32:30+03:00 (~4 min wall clock)
- Rounds used: 3 (r1 failed), final round 3; final tris 4804 (budget 10000)
- Final round ops: fillet/chamfer 5 calls, 0 reduced, 0 failed, 0 retries; booleans 8, 0 fuzzy, 0 manifold, 0 failed
- Failed round r1: 1 CadOpError (boolean cut 'window_recesses', 4 retries, manifold_error "Null TopoDS_Shape object")

## Kit bugs
1. `ops._occ_bool` imports `TopTools_ListOfShape` from `OCP.TopTools`; not present in this OCP build -> ImportError,
   so the fuzzy path ALWAYS fails silently (any plain-boolean failure goes straight to Manifold).
2. `safe_boolean` with a list/tuple tool forces `raise TypeError` -> skips plain OCCT, hits bug 1, then Manifold.
3. `_manifold_bool` -> `_sew` returns a null shape (MakeSolid fails, fallback `Shape.cast` of null) on a simple box cut.
   Net: list-tool booleans never work. Workaround: pass `Compound([...])` as the tool (plain `a - Compound` succeeds).

## build123d
- Easy: Polygon+extrude slabs with offset footprints (cornice/bands/parapet), one window module placed via Location
  with Z rotation (instancing is trivial), edge selection via filter_by/group_by for chamfers.
- Hard/awkward: offsetting a chamfered polygon by hand; no direct "instance" in export (copies are real geometry).
