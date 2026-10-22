"""cadkit.tools - direct-modelling op library (clean-room, from docs/plasticity_spec.md only).

    from cadkit.tools import Model
    m = Model()
    m.run("box", name="crate", size=[0.6, 0.4, 0.4])
    m.run("fillet", body="crate", edges={"parallel": "z"}, radius=0.03)
    m.undo(); m.set_param(0, "size", [0.7, 0.4, 0.4]); json = m.to_json(); Model.from_json(json)

See docs/TOOLS.md for the op list + provenance, describe_ops() for live docs.
"""
from .core import Model, ToolError, OPS, describe, describe_ops, resolve, tangent_chain  # noqa: F401
from . import geom, solids, edit, pattern, surfacing, advanced, query, importer  # noqa: F401  (registers ops)
from .export import export_file, write_run, game_mesh, render  # noqa: F401


def select(model, ref):
    """Query (no journal entry): describe what a ref resolves to."""
    r = resolve(model, ref)
    return describe(r if isinstance(r, (list,)) or hasattr(r, "filter_by") else [r])
