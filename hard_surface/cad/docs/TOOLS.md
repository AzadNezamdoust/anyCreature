# cadkit.tools - direct-modelling ops (clean-room)

Spec source: docs/plasticity_spec.md ONLY (public-sourced functional spec). Generic op names, no Plasticity code/assets.
Package: cadkit/tools/ (core = Model + journal tree + ref specs; geom, solids, edit, pattern, export). MCP: mcp_tools.py (op_<name>, cad_*), registered at end of mcp_server.py.
Tests: tests/test_tools_*.py. Demo: examples/tools_crate_demo.py -> out/tools_runs/crate_demo/render/sheet.png.

## Provenance (op -> spec section)

| op | implements |
|---|---|
| arc | spec 1 Curves: Arc (3-pt) |
| boolean | spec 1 Booleans: Union/Difference/Intersect (keepTools); fallback fuzzy -> Manifold (cadkit.ops) |
| box | spec 1 Primitives: Box (width/length/height, base plane) |
| chamfer | spec 1 Fillet/chamfer: chamfer by distance, 2 distances, or distance+angle |
| circle | spec 1 Curves: Circle (center) |
| cone | spec 1 Primitives: Cone (radius1/radius2, height) |
| cplane | spec 1 Construction planes: custom cplane from face / 3 points / origin+normal |
| cylinder | spec 1 Primitives: Cylinder (radius, height) |
| delete | utility: delete object |
| delete_face | spec 1 Direct edit: delete face (heal) - neighbours extend to close |
| duplicate | spec 1 Duplicate |
| extrude | spec 1 Shape-from-profile: Extrude (distance1/2, draft per side, thickness1/2, operationType new/union/difference/intersect); spec 5.1/5.3 |
| fillet | spec 1 Fillet: constant radius, shape round|smooth (OCCT polynomial ~G2 approx)|quasi_angular; retry + max-radius hint (cadkit.ops.safe_fillet) |
| fillet_curve | spec 1 Curves edit: Fillet a curve vertex (radius) |
| imprint | spec 1 Imprint curves on faces (splits faces, solid unchanged); spec 5.5 imprint panel lines |
| instance | spec 1 Linked instances (CreateInstance) / realize (RealizeInstance) |
| line | spec 1 Curves: Polyline/line |
| linear_array | spec 1 Rectangular arrays (count, spacing); spec 5.6 |
| loft | spec 1 Shape-from-profile: Loft (ordered curves/regions, guides, closed, ruled) |
| mirror | spec 1 Mirror across a plane or face (keep or replace, auto-union across symmetry plane); spec 5.6 |
| move | spec 1 Transforms: Move (typed values) |
| offset_curve | spec 1 Curves edit: Offset planar curve (distance, side) |
| offset_face | spec 1 Offset face (push/pull, neighbours adapt) / Direct edit Move face; spec 5.3 |
| pipe | spec 1 Shape-from-profile: Pipe (path, radius, inner radius) |
| polygon | spec 1 Primitives: Polygon (sides) |
| prism | spec 1 Primitives / 3 Region extrude: prism from a region |
| project_curve | spec 1 Curves edit: Project curve onto body (ProjectCurveBody) |
| radial_array | spec 1 Radial arrays (count, angle); spec 5.6 |
| realize | spec 1 RealizeInstance: instance -> independent copy |
| rectangle | spec 1 Primitives: Rectangle (corner/center) |
| refillet | spec 1 Fillet: refillet an existing blend with a new radius (remove + re-apply); spec 5.2/2.5 re-fillet after edit |
| regions | spec 1 Curves: Regions (closed planar curves split automatically into fillable faces, no solver) |
| remove_fillets | spec 1 Fillet: remove fillets (detect + delete blends) |
| revolve | spec 1 Shape-from-profile: Revolve (axis, angle, thickness) |
| rotate | spec 1 Transforms: Rotate (pivot = given point / bbox centre) |
| scale | spec 1 Transforms: Scale (uniform, pivot) |
| shell | spec 1 Shell/hollow: faces to remove, thickness, inward/outward |
| sphere | spec 1 Primitives: Sphere (center, radius) |
| spline | spec 1 Curves: Curve (NURBS/cubic, CurveFactory) |
| split | spec 1 Cut or split by curve, face or plane (mode split vs cut away) |
| sweep | spec 1 Shape-from-profile: Sweep (profile, path, mode) |
| tag | spec 3 / 5.9: stable references re-resolved from geometry (named semantic query) |
| thicken | spec 1 Thicken sheet -> solid (thickness1/2) |
| torus | spec 1 Primitives (torus: generic revolve primitive; not in spec table) |
| bridge_curve | spec 1 Curves edit: Bridge / blend curve between two curve ends (G1 cubic, G2 quintic) |
| blend_surface | spec 1 Fillet 'smooth' / surfaces: blend surface between two face edges, G1 or true G2 (bridge-curve network -> B-spline surface) |
| cap_round | spec 1 Fillet: round a loft/sweep end cap (trim + quarter-round loft); fillet auto-routes cap rims here |
| coons_patch | spec 1 Surfaces: 4-sided boundary surface (Coons/curved/stretch; falls back to patch) |
| helix | spec 1 Curves: Helix / spiral |
| join_curves | spec 1 Curves edit: Join curves into one wire |
| patch | spec 1 Surfaces: N-sided boundary patch (GeomPlate / BRepFill_Filling), C0/G1/G2 to support faces |
| rail_loft | spec 1 Loft with guides: 2+ rails (blended sections fitted onto every rail) |
| sew | spec 1 Surfaces: sew sheets into shell/solid |
| trim_curve | spec 1 Curves edit: Trim / split curve (param range) |
| variable_fillet | spec 1 Fillet: variable radius (points along the edge, each with its own radius) |

## Robustness (2026-10-22)
- Crash isolation: all MCP tool calls run in a persistent kernel worker subprocess (cadkit/tools/sandbox.py). Segfault /
  abort / hang (timeout CADKIT_OP_TIMEOUT, default 300 s) -> ok:false, crashed:true + hint; worker restarts and rebuilds
  the session by replaying the on-disk journal (written atomically, only after a successful op). New tool cad_run(op).
  Test: tests/test_tools_crash.py (debug_crash segv/abort, debug_hang; ops exist only with CADKIT_DEBUG_OPS=1).
- shell: robust_shell chain arc -> intersection -> MakeThickSolid arc/intersection/loose tol -> closed offset + cut +
  punched openings -> re-loft shrunk loft sections -> Manifold minkowski erosion; each result validated
  (valid, wall vol ~ area*t). info.method reports which one; strategy= forces one.
- offset_face: per-face BRepOffset (intersection, arc join) -> thicken-face slab union/cut; works on curved faces.
- fillet: loft/sweep end-cap rims (closed edge of a 1-edge planar face next to a B-spline face) never go to OCCT
  (it segfaulted) -> cap_round. Failing edges of a set are staged one by one at a radius ladder (1..0.15x) on the
  evolving body; good edges keep the full radius.

## Known limits / NOTES
- Fillet 'smooth' = OCCT polynomial approx, not true G2/conic; conic profile not available in OCCT.
- loft guide= is a one-spine pipe-shell; rail_loft does 2+ rails by section fitting (exact on rails at stations, interpolated between).
- refillet finds healed edges by bbox proximity; ambiguous on dense blends - fillet explicitly then.
- imprint = curves projected along one direction; imprint by body not done. Slot, text, deformers, face rotate/draft, patterns of faces: not done.
- blend_surface G2 assumes ~zero cross-curvature of the support faces (exact for planar/ruled); result is a sheet (sew it).
- cap_round: G1 at the trim junction only to loft-fit accuracy; insets via 2D offset or point offset (convex-ish caps).
- cadkit/ops.py untouched (other lane). Wrapped: safe_boolean/safe_fillet/safe_chamfer; CadOpError -> ToolError with data.max_feasible.
