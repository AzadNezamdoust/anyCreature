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
| variable_fillet | spec 1 Fillet: variable radius (points along the edge, each with its own radius) |

## Known limits / NOTES
- Fillet 'smooth' = OCCT polynomial approx, not true G2/conic; conic profile not available in OCCT.
- Guided loft = pipe-shell along one spine (OCCT has no multi-rail guide loft).
- offset_face: OCCT per-face offset often fails; falls back to planar push/pull (non-planar faces unsupported).
- refillet finds healed edges by bbox proximity; ambiguous on dense blends - fillet explicitly then.
- imprint = curves projected along one direction; imprint by body not done. Trim/join/bridge curves, slot, text, helix, deformers, face rotate/draft, patterns of faces: not done.
- MCP ops run in-process (journal saved per call); an OCCT segfault kills the server, the journal survives.
- cadkit/ops.py untouched (other lane). Wrapped: safe_boolean/safe_fillet/safe_chamfer; CadOpError -> ToolError with data.max_feasible.
