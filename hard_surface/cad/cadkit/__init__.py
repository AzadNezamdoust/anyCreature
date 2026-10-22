"""cadkit - LLM-drivable build123d helpers (Phase 1 prototype).

Model script contract (one file = whole model, re-run = undo):
    from cadkit import *
    body = Box(...) ...
    PARTS = {"receiver": (body, "#2b2d30"), ...}   # name -> shape or (shape, hex colour)
    # or MODEL = shape
    SPEC = {"L": 0.90, "W": 0.07, "H": 0.26}       # optional: overall bbox targets (m) for the measure table
    TRI_BUDGET = 8000                                # optional
"""
from build123d import *  # noqa: F401,F403
from .ops import safe_fillet, safe_chamfer, variable_fillet, safe_boolean, cut, fuse, common, CadOpError, LOG  # noqa: F401
from .refs import tag, tagged, face_at, edges_of_face, edges_parallel, edges_on_plane, edges_near, \
    edges_longer, edges_circular, new_edges  # noqa: F401
from .surf import robust_shell, robust_offset_face, cap_round, rail_loft, patch, coons_patch, bridge_curve, \
    blend_surface, trim_curve, join_curves, helix, inset_face, inset_wire  # noqa: F401
