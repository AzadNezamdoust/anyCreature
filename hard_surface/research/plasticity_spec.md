# Plasticity functional spec (for an LLM-friendly hard-surface CAD tool)

Sources: plasticity-mcp source (E:\Github\plasticity-mcp, targets Plasticity 26.1.3; command-factory names
read from src/plasticity/*.ts and docs/tool-reference.md), plus public Plasticity docs, release notes and
tutorials, and the MIT Blender bridge add-on (nkallen/plasticity-blender-addon), as remembered from public
material. No binaries were inspected.
Tags: (mcp) = confirmed by names in the plasticity-mcp source. (pub) = public/community knowledge, NOT
re-verified online in this pass. Check (pub) items against doc.plasticity.xyz before you rely on them.

## 0. What Plasticity is
- An Electron/TypeScript + three.js desktop app by Nick Kallen. Kernel: **Parasolid** (Siemens) in current
  versions (earlier builds used C3D). Precise NURBS B-rep. Aimed at artists rather than engineers: "CAD with
  Blender ergonomics".
- **Direct (history-free) modelling.** There is no parametric feature tree, only an undo/redo stack. A command
  you just finished stays "hot": you can re-open and adjust it until you run the next op, and Space repeats the
  last command. Newer versions add limited editable/"live" features (pub), but the core model is still direct.
  plasticity-mcp adds its own journal (docs/construction-history.md) because the app has none.
- Why artists love it: a gizmo on every parameter, a Blender-style keymap, fast modal tools, no sketch
  constraint solver to fight, regions found automatically from any closed curves, robust Parasolid fillets and
  booleans, a one-click live link to Blender, and a cheap perpetual licence.

## 1. Command list with parameters (Factory = internal command class, mcp)

### Primitives
| Tool | Params |
|---|---|
| Box (2-pt / 3-pt / center) | width, length, height, base plane (set_block_dimensions, mcp) |
| Sphere | center, radius |
| Cylinder / Cone | radius (radius1/radius2 for cone), height (mcp) |
| Rectangle (corner/center/3-pt), Polygon, Slot | dims, sides, slot width (SlotFactory) |
| Text | string, font, size -> planar curves/regions (TextFactory) |

### Curves / sketch (2D on a construction plane, or 3D)
- Create: Polyline/line, Curve (NURBS/cubic; CurveFactory, degree), Circle (center / 2-pt / 3-pt / tangent:
  CircleFactory, CenterCircleFactory, TangentCircleFactory), Arc (center / 3-pt / tangent: TangentArcFactory),
  Ellipse, Spiral/Helix (SpiralFactory: radius, pitch/turns, taper angle).
- Edit: Trim (TrimFactory, click a fragment to remove it), Join/Unjoin, Fillet/chamfer a curve vertex (radius),
  Offset planar curve (distance, side), Bridge curves (BridgeCurveCommand, continuity), Extend endpoints, Split
  segment (SplitSegmentFactory), Insert knot, Raise degree, Rebuild (RebuildCurveFactory: point count/degree),
  Subdivide, Planarize, Reverse, Project curve onto body or curve (ProjectCurveBodyFactory,
  ProjectCurveCurveFactory), Body outlines and body-body intersection curves (ProjectOutlineFromShellsFactory,
  ProjectBodyBodyFactory), Extract edges, Isoparam curves (IsoparamCommand).
- Control points: move/rotate/scale/slide (MultiSlideControlPointFactory, MultiScaleControlPointFactory, ...),
  delete, convert vertices to control points.
- Import SVG/DXF curves (VectorImportFactory).
- **Regions**: any set of closed planar curves is split automatically into fillable faces, with no constraint
  solver. Region ops: boolean regions, offset region (OffsetRegionFactory), patch region -> sheet
  (PatchRegionFactory), curves from regions.

### Shape-from-profile
| Tool | Params |
|---|---|
| Extrude (regions, faces, curves) | distance1, distance2 (both directions), draft angle per side, thickness1/2 (thin wall), operationType (new/union/difference/intersect; auto-booleans onto the solid it touches) (ExtrudeFactory, mcp) |
| Revolve | axis, angle/degrees, thickness (RevolveFactory, mcp) |
| Sweep | profile(s), path, twist/scale, mode (SweepFactory) |
| Loft | ordered curves/regions/faces, guides, closed, end tangency (RegionLoftFactory; loft_curves/faces) |
| Pipe | path, radius, inner radius / profile (PipeFactory) |
| Rib, Bridge surface, Constrained surface | (mcp tool names) |

### Booleans / cutting
- Union / Difference / Intersect (BooleanFactory: keepTools, operationType). Cut or split by curve, face or plane
  (CutFactory; mode = split vs cut away). Imprint curves on faces and imprint bodies (splits faces without
  changing the solid). Auto-boolean while extruding or moving.

### Fillet / chamfer
- Fillet edges (pub, with shape/cornerType fields seen in mcp): radius/distance; **variable radius** (you add
  points along the edge, each with its own radius); shape = round / conic / chamfer; chamfer by 2 distances or
  distance + angle; curvature-continuous (G2/conic) option. Face-face fillet. Refillet an existing blend with a
  new radius (RefilletFaceFactory). Remove fillets: detect and delete blends (RemoveFilletsFromShellFactory).
  Curve-vertex fillet.

### Shell / thicken / offset
- Shell/hollow a solid: pick the faces to remove, thickness, inward/outward (hollow_solids/faces).
- Thicken sheet -> solid (ThickenFaceFactory: thickness1/2).
- Offset face (push/pull, neighbours adapt), offset face loop, offset edge, offset vertex
  (OffsetFaceLoopFactory, OffsetEdgeFactory, OffsetVertexFactory). Offset region/curve.

### Direct face/edge editing (the core of the workflow)
- Move/Rotate/Scale faces (MultiRotateFaceFactory etc.), draft face, match faces, delete face (heal), dissolve
  faces, delete edges, move edges, slide, unjoin faces/shells, extract faces, rebuild face, raise surface degree,
  untrim (UntrimFactory), insert isoparam edges, unwrap/flatten face (UnwrapFactory).
- Deform bodies/curves between faces (bend/twist/taper-style deformers).
- Patch holes in a sheet, solid or wire (PatchHoleInSheet/Solid/WireFactory), cap sheet holes, join sheets ->
  solid, reverse sheet normals (ReverseSheetFactory), extend sheet edges, insert sheet.

### Mirror / patterns / instances
- Mirror across a plane or face (keep or replace, auto-union across the symmetry plane) (pub).
- Radial and rectangular arrays of bodies/faces (RadialArrayFacesFactory, RectangularArrayFacesFactory: count,
  spacing, angle), curve pattern along a path. Linked instances (CreateInstanceFactory, realize instances back to
  independent copies with RealizeInstanceFactory). Duplicate (DuplicateCommand).

### Transforms and gizmos
- Move G / Rotate R / Scale S (MoveFactory, RotateFactory, ProjectingScaleItemAndEmptyFactory; the
  ...ItemAndEmpty variants also move pivots/empties). You can type a value while dragging, lock to an axis with
  X/Y/Z, and pick the pivot (selection center, bbox, world, or a picked point). Align tools: align planar faces,
  cylindrical faces, linear edges, vertices (mcp align_*).
- Every tool shows a **gizmo**: arrows for distances, arcs for angles, rings for radius/thickness. You drag it,
  or click it and type a number. The dialog panel mirrors the same values.

### Selection modes (pub)
- Control point / edge / face / body / curve modes, which can be combined. Click to select, Shift to add, Ctrl to
  remove; box select; X-ray select-through; loop and tangent-chain select; select adjacent; select by type.
  Works both ways: select first and then run the command, or start the command and it asks for picks.

### Snaps (pub)
- Grid, end/vertex, midpoint, center, on-edge, on-face, normal, tangent, perpendicular, curve-curve intersection,
  axis lock, angle increments, circle quadrants. Snap markers preview where a point will land, and a modifier
  key turns snapping off temporarily.

### Construction planes / datums
- Orthographic views set the active cplane automatically (Top/Front/Right). Custom cplane from a face, 3 points
  or the view (set_workplane, create_construction_plane, mcp). Datum point/axis (mcp define_datum_*). Curve
  tools draw on and project to the active cplane.

### Utility / analysis
- Measure distance/radius (MeasureDistanceCommand, MeasureRadiusCommand), section analysis
  (SectionAnalysisFactory), validate bodies, interference check, continuity/curvature analysis, groups,
  visibility/lock, viewport materials.

## 2. Interaction model (why it is fast)
1. **Modal tools, Blender keymap.** Press a key, the tool goes live, drag the gizmo or type a value, then
   Enter/click commits and Esc cancels. Space repeats the last command. A searchable command palette covers
   everything else.
2. **The gizmo is the parameter UI.** No dialog comes first: every numeric parameter has a handle on the model.
   Tab cycles between fields, and Parasolid updates the preview live, even for fillets and booleans.
3. **Contextual verbs.** Which op a key gives you depends on what is selected (region -> extrude, face ->
   offset/extrude, edge -> fillet).
4. **No constraints.** A sketch is just free curves: regions are found automatically, trimming is a click, and
   snaps do the job constraints would.
5. **Forgiving direct edits**: you can push/pull faces on a body that is already filleted and Parasolid
   rebuilds the blends; refillet changes radii afterwards.
6. Cheap undo, fast viewport (matcap, X-ray, isolate, frame selection).
7. **Live Blender bridge**: refacet and send in one click.

## 3. Data model
- Kernel: Parasolid B-rep. Object types: **Solid** (closed manifold), **Sheet** (open surface body), **Curve**
  (NURBS/polyline curves that can be joined), **Region** (planar face derived from closed curves, not stored as
  a body). Also Group, Instance, Empty, construction plane, measurement, section analysis.
- Topology: body > shell > face > loop > edge > vertex. Each face carries a surface type (plane, cylinder,
  cone, sphere, torus, NURBS, blend).
- **Topology naming is not stable.** IDs change between operations. plasticity-mcp uses "revision-bound
  references": a body/face/edge ref stops being valid after the next mutation. An LLM tool therefore has to
  re-resolve picks from geometry (position, normal, area, adjacency), not from IDs.
- Native file: `.plasticity`, a proprietary container holding Parasolid data plus scene metadata (pub).
- Import: STEP, IGES, Parasolid x_t/x_b (ParasolidImportFactory), OBJ/STL reference meshes, SVG/DXF curves.
- Export: STEP / IGES / Parasolid (ExportCadFactory), OBJ (OBJExportFactory), STL, 3MF (ThreeMfExportFactory),
  SVG and hidden-line SVG.
- **Mesh facet settings** (export and bridge, pub): presets (coarse/medium/fine) plus advanced controls: curve
  chord tolerance (sag), surface plane tolerance, plane angle (normal deviation), min/max facet width, max
  sides (triangles vs convex n-gons), and match topology (watertight across edges). Normals are smooth within a
  face and split at hard edges.
- **Blender bridge** (MIT add-on, pub; the field list is from memory, so re-read the repo before you implement
  it): Plasticity runs a local WebSocket server (default localhost:8980) and sends binary little-endian
  messages, each with a message type and id.
  - Message types: TRANSACTION_FILE, TRANSACTION_ALL, ADD, UPDATE, DELETE, MOVE, ATTRIBUTE, NEW_VERSION,
    NEW_FILE, LIST_ALL, LIST_SOME, LIST_VISIBLE, SUBSCRIBE_ALL, SUBSCRIBE_SOME, UNSUBSCRIBE_ALL, REFACET_SOME.
  - Per-object payload: type (SOLID/SHEET/WIRE/GROUP/EMPTY), id, version, name, visibility/selectability flags,
    material, parent group, then float32 vertices, triangle indices, float32 normals, and **per-CAD-face groups
    / face_ids**. Blender uses the face groups to select by CAD face, mark sharp edges and place UV seams.
  - A refacet request carries the tolerance params above. Live link = subscribe, after which the server pushes
    an update on every transaction.

## 4. Pain points users report (forums/Discord/reviews, pub)
- **No parametric history**: you cannot go back and change a fillet radius from 20 ops ago. This is the most
  requested feature.
- Mesh export is triangles or n-gons, not clean quads. Games need cleanup or retopo, facet tuning is trial and
  error, fillets produce long thin triangles, and you need Blender for UVs and bakes.
- Fillets fail at complex corners where 3+ blends meet, with no automatic fallback, and the order of fillets
  matters.
- No UV or texture tooling, no real materials, no rendering.
- No dimension-driven constraints, which hurts precise parts.
- No official scripting API (hence workarounds over Chrome DevTools Protocol, like plasticity-mcp).
- No assemblies/joints, no SubD, Class-A surfacing weaker than Rhino/Alias, proprietary file format,
  slowdowns on very heavy scenes.

## 5. Ranked must-haves for game hard-surface (hero props, weapons, vehicles)
1. Robust **booleans** (union/diff/intersect, cut by plane/curve), with auto-boolean during extrude.
2. **Fillet/chamfer** including variable radius and G2/conic, plus refillet / remove fillet and robust corner
   blends.
3. **Extrude / push-pull faces**, with region extrude from free curves (no solver) and draft angle.
4. **Game-ready meshing**: tolerance controls, quad-dominant output, CAD-face IDs carried through to sharp
   edges, UV seams, smoothing groups and weighted normals, LOD presets, and a target triangle budget (RTX 2070
   baseline).
5. Curves: polyline/arc/NURBS, trim, offset, vertex fillet, project onto body, imprint panel lines.
6. **Mirror/symmetry, radial and linear arrays, instances** (bolts, vents, treads).
7. Gizmo per parameter, typed values, snaps (vertex/mid/center/edge/face/grid), and cplanes from faces.
8. Shell / thicken / offset face (armour plates, housings).
9. Selection: loops, tangent chains, by type, and **stable references based on geometry** for LLM use.
10. Loft / sweep / pipe (cables, hoses, grips) and revolve (barrels, wheels).
11. Deformers (bend/twist/taper between faces) for stylised shapes.
12. **Editable history**: our differentiator. An op log native to the LLM gives parametric replay, which
    Plasticity lacks.
13. Exports: glTF/FBX/OBJ with normals and face groups, STEP for interchange, and a live DCC bridge.

Low priority for games: measurement, FEM, fastener and print tooling, hidden-line SVG, continuity analysis.

## LLM-friendly design takeaways
- Make each command a pure function: {op, input refs, params} -> new revision. Store the journal as a tree you
  can replay.
- Refs are semantic queries (for example "largest +Z face on body 'receiver'"), re-resolved on every replay.
- Plasticity's flat, contextual command vocabulary (~150 ops, listed above) already works well as an LLM API.
  Copy it.
