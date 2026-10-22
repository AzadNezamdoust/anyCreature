# cadengine - C++ / GPU CAD engine (Phase 1, 2026-10-22)

Fast backend for the LLM CAD app. The Python kit (`cadkit/`, build123d + OCP 8.0.1) stays the **reference
implementation**; the engine runs the same ops, ref grammar and journal JSON, behaviour-matched and checked by
equivalence tests.

## Build
Needs VS 2026 (18) Community C++ tools (CMake + Ninja ship with it) and the OCCT SDK in `E:\gen3d\occt`.
```
engine\build.bat            -> engine\bin\cadengine.exe (+ TK*.dll copied next to it)
```
- OCCT 8.0.1 SDK = conda-forge `occt-8.0.1-novtk_h6bfc850_101.conda` unpacked to `E:\gen3d\occt\Library`
  (source, size, licence: `E:\gen3d\occt\SOURCE.txt`). LGPL-2.1 + exception, linked **dynamically**. No system install.
- Header deps in `E:\gen3d\occt\thirdparty`: nlohmann/json 3.11.3 (MIT), stb_image / stb_image_write (PD/MIT).
- `FreeImage.dll` / `freetype.dll` (imported by TKService through TKDESTEP -> TKXCAF, never called) are copied from the
  cadquery-ocp wheel's `.libs` folder by `copy_dlls.cmake`.
- Paths are CMake cache vars: `OCCT_ROOT`, `DEPS_DIR`, `OCPLIBS`. Incremental rebuild ~10-40 s (PCH on `common.hpp`).

## Architecture
```
Python / MCP  --JSON lines-->  cadengine.exe (persistent, CREATE_NO_WINDOW)
                                 sessions: Model = journal tree + head + per-op result cache
                                 ops.cpp      op registry (same names/params as cadkit.tools)
                                 model.cpp    journal, cache, state/diff, ref resolver (same JSON ref grammar)
                                 kernels.cpp  risky kernels: round (fillet/chamfer), boolean, shell, offset_face
                                 isolate.cpp  -> cadengine.exe --worker (child, CREATE_NO_WINDOW, timeout)
                                 gpu.cpp      OpenGL 4.5 (hidden WGL window): tess cache, sheets, IoU, deviation
```
- **Journal + cache.** Every node's cache key = hash(parent key, op, params JSON). Editing op N (`set_param`) reuses
  the cached state of op N-1 and replays N..end only; reverting an edit, or re-running any previously seen chain, is
  a pure cache hit (0 ops). Undo/redo/checkout = same mechanism. Journal JSON is identical to `cadkit.tools.Model`
  (`{"version":1,"nodes":[{id,parent,op,params}],"head"}`) - sessions move between backends.
- **Per-op diff** (`added/removed/changed` with from/to/delta) on every run / set_param, like the Python kit.
  Object summaries are cached per shape identity, so unchanged objects are never re-measured.
- **Isolation.** fillet/chamfer, boolean, shell, offset_face run in ONE persistent child (`--worker`); shapes go as
  BinTools files in a private temp dir, sub-shapes by TopExp index. Crash / hang (`CADENGINE_OP_TIMEOUT`, default
  120 s) kills only the child (by handle); the op fails with `data.crashed`, engine state is intact, child restarts
  on the next call. `CADENGINE_ISOLATE=0` runs kernels in-process (~25 % faster on fillet-heavy builds).
- **Engine stdout** is a private dup of fd 1; fd 1 is pointed at stderr so OCCT printf noise (STEP writer) can't
  corrupt the protocol. Exit via `_exit` (no OCCT teardown, ticket T7).

### Protocol (`cadkit/engine_client.py`)
`{"id":n,"method":m,"params":{...}}` -> `{"id":n,"result":...}` or `{"id":n,"error":{message,hint,data}}`.
Methods: `ping new close run undo redo checkout set_param state journal load select measure brep render
register_ref iou deviation gpu_info stats describe_ops shutdown`. `session` param (default `"default"`).

```python
from cadkit.engine_client import Engine     # no build123d import (load the file by path to skip cadkit/__init__)
e = Engine()
e.run("box", name="crate", size=[0.6, 0.4, 0.4])
e.run("fillet", body="crate", edges={"parallel": "z"}, radius=0.03)
e.set_param(0, "size", [0.7, 0.4, 0.4])     # -> {"replayed_ops": 2, "ms": ..., "diff": ...}
e.render("out/sheet.png", modes=["clay", "zebra", "curvature"])
e.register_ref("front", "refs/front.png", view="front", m_per_px=0.0002)   # or normalised (height-fit)
e.iou()                                     # {"refs": {"front": {"iou": ..., ...}}}
e.deviation("model", "ref_step", heatmap="out/dev.png")
```
MCP: `CADKIT_BACKEND=cpp` routes `cad_new/run/op_*/state/journal/select/undo/redo/checkout/set_param/measure/render`
to the engine (`mcp_tools.cpp_dispatch`; engine_client loaded by path, so no build123d in that path). Journals are
saved to `out/tools_sessions/<s>.json` as before. Other tools (curvature, draft, suggest_refs, game_mesh, export glb,
compare_to_ref) still go to the Python worker. Note: `mcp_server.py` itself still imports `cadkit` (build123d) at start.

## Ported ops (behaviour-matched to cadkit.tools)
box cylinder cone sphere torus prism | line arc spline(+end tangents) circle rectangle(+corner_radius) polygon
offset_curve fillet_curve regions cplane | extrude (distance2, thickness, mode new/union/cut/intersect, +draft along
+normal only) revolve sweep (frenet, transitions, holes) loft (ruled) pipe (hollow) | boolean (plain -> fuzzy
1e-6..1e-4, volume sanity + **no-op probe**, UnifySameDomain like build123d, **no mesh fallback**) | fillet / chamfer
(full radius or **fail** with `data.max_feasible` + bad edges; never shrinks) | shell (arc -> intersection -> simple,
validated) offset_face thicken delete_face split(plane) tag | mirror linear_array radial_array duplicate move rotate
scale delete | import_step export_step. Refs: names, tags, faces/edges/vertices/solids/wires with
normal/geom/parallel/longer/shorter/within/near(+radius)/pick/axis/tol/of_faces+loop/tangent_chain/first/expect.
Queries: select, measure, state.

### Not ported yet
variable_fillet, refillet, remove_fillets, push_pull, boolean_fillet, symmetrize, draft_face, imprint, split by
curve, project_curve, offset_curve_on_face, instance/realize, loft guide / rail_loft, fillet shape smooth/
quasi_angular, asymmetric chamfer, extrude draft off-normal / negative, shell strategies thick_tol/offset_cut/
sections/manifold (manifold intentionally never), all surfacing (patch, coons, curve_network/Gordon, blend_surface,
bridge_curve, cap_round, sew, helix, join/trim curves), queries curvature/draft_analysis/suggest_refs/
explain_failure, game mesh/glb export, model-script (build123d .py) runner. Unported op -> ToolError naming the
Python kit as fallback.

## Equivalence (engine/tests/equiv.py, pytest engine/tests)
9 journals (`tests/cases.py`): prims, fillet/chamfer, booleans, sketch+extrude+regions, revolve/sweep/loft/pipe,
shell/offset/split/delete_face, pattern/transforms, refs/tags/cplane, and **replica L1** as an op journal (Pi 4 case
with all port cuts + red/white split + PCB, ISO M8x40 bolt head/point; the S-curve side panel and the helical
thread are left out). Compared per object vs the Python kit: kind, volume/area/length (rel 1e-5), bbox, face/edge
counts, validity, errors. **Result: 57/57 objects match, 0 error mismatches.** pytest: 14 passed (also fillet
rejection, cache replay counts, crash + hang isolation, render/IoU/deviation smoke).

## Benchmarks (engine/tests/bench.py, RTX PRO 6000 dev box, L1 journal 53 ops, 5k tris)
| | Python kit | C++ engine |
|---|---|---|
| cold start | `import cadkit.tools` 2.0 s (41 s on the loaded box, T1) | 41 ms (process up + ready) |
| full build L1 | 8.0 s | 3.1 s (2.3 s no isolation) |
| late edit (last op) | 0.7 ms | 1.2 ms |
| mid edit (pcb fillet) | 65 ms | 101 ms (isolation round trip) |
| early edit (op 1, 47 ops replay) | 3.3 s | 2.3 s (1.9 s no isolation) |
| revert an edit | 3.4 s (replay) | 0.4 ms (cache hit) |
| 6-view clay sheet 900x600 | fast loop 0.6-0.9 s | 17 ms (GPU 1.3 ms, PNG 16 ms) |
| 18 tiles clay+zebra+curvature (jpg) | - | 12 ms |
| first render incl. tess + GL init | - | 119 ms |
| silhouette IoU vs ref (600 px) | 0.65 s | 0.14 ms (iou 0.9996 vs py 0.9909 on same mask) |
| deviation heatmap (3.3 M pt-tri pairs) | - | 9 ms (GPU 1 ms) |
Fast-loop reference numbers (cadkit/fast, model scripts): L3 late edit 10.8 s, L4 26 s. Kernel-bound replays (OCCT
fillets) are the same OCCT code in both, so the edit win comes from caching + no Python/build123d overhead, not
from faster kernels. Render/IoU/deviation are now ms-level.
