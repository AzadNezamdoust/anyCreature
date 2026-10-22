"""cadkit.game - CAD solid -> game-ready asset (high/low/LOD meshes, UVs, Cycles bakes, glTF/FBX, preview sheet).

Host side (this package, OCCT python): tess.build_meshes() -> meshes.npz (hi + per-LOD B-rep re-tessellations, face ids).
Blender side (bl_game.py, run as a script): low-poly variants (retess / decimate / quadriflow), seams, sharp edges,
weighted normals, UVs, bakes, export, preview.  Orchestration: pipeline.run().  CLI: hard_surface/cad/game_export.py.
"""
from .tess import build_meshes, retess_to_budget  # noqa: F401
from .uvstats import uv_report, curvature_from_normal  # noqa: F401
