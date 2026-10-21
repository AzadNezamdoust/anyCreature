# cad - LLM-first B-rep CAD (Phase 1 prototype, 2026-10-21)

Plan: `../research/LLM_CAD_PLAN.md`. Venv: `E:\gen3d\venv_cad` (PyPI only). Blender: `E:\gen3d\blender\blender-5.2.2-windows-x64\blender.exe` (override `CADKIT_BLENDER`).

## Versions / licences (pip metadata, checked 2026-10-21)
| pkg | version | licence |
|---|---|---|
| build123d | 0.13.0 | Apache-2.0 |
| cadquery-ocp-novtk (OCP) | 8.0.1.1.0 | Apache-2.0 bindings; bundled OpenCASCADE = LGPL-2.1 + exception (dynamic libs) |
| manifold3d | 3.5.4 | Apache-2.0 |
| mcp | 2.3.0 (FastMCP is `MCPServer` in 2.x) | MIT |
| trimesh 5.1.1, numpy 2.5.4 | | MIT / BSD |
Python 3.12.10. Blender runs as a separate process (no GPL linking).

## Layout
- `cadkit/worker.py` subprocess: exec model script -> `state.json` (bodies, volume, bbox, faces/edges, valid, tags, op log, spec err), `model.step`, `mesh.npz` (tessellation with B-rep face ids, auto-coarsened to TRI_BUDGET).
- `cadkit/ops.py` `safe_fillet/safe_chamfer` (bisect max feasible radius, apply if >=15 %, else CadOpError naming bad edges + max r); `cut/fuse/common` (plain -> fuzzy OCCT -> Manifold mesh fallback sewn to B-rep).
- `cadkit/refs.py` `tag()/tagged()`, `face_at`, `edges_parallel/on_plane/near/longer/circular`.
- `cadkit/blender_mesh.py` weld, UV seams = B-rep face boundaries, sharp = boundaries > 30 deg, angle-based unwrap per island (or `--smart-uv`), LOD1/2 decimate, glb + blend.
- `cadkit/render.py` any glb -> 6 ortho views + `sheet.png` (iso,left,right / front,back,top), Workbench.
- `cadkit/runner.py` host API (run_model with timeout, mesh, render, measure table).
- `mcp_server.py` stdio tools run_model, get_state, render, measure, export(step|glb). Test: `examples/mcp_smoke.py`.
- `pilot/<asset>/model.py, rounds.jsonl, NOTES.md`; `pilot/round.py` one render-compare round. Outputs in `out/` (not for git).

Model contract: `from cadkit import *`; `PARTS = {name: (shape, "#rrggbb")}`; optional `SPEC`, `TRI_BUDGET`. X length (front -X), Y width (left -Y), Z up, metres.

## Register MCP (not done automatically)
```
claude mcp add cadkit -- E:\gen3d\venv_cad\Scripts\python.exe E:\Github\anyCreature\hard_surface\cad\mcp_server.py
```
