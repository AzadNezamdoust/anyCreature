"""
build_from_mesh.py -- a build.py that loads a mesh.json (judge_mesh.mjs --export) as-is: one Blender object per part,
material = the part's zone, source winding kept (no weld / normal recalc), so the harness can score a model.mjs's own
geometry (the scoring round-trip check in README "Verification"). The path comes from the environment:

  $env:HS_MESH = "<abs path>/mesh.json"
  & blender -b --factory-startup --python-exit-code 1 --python scripts/hs/run_pass.py -- `
      --subject <s> --pass 0 --build scripts/hs/build_from_mesh.py --out-dir <scratch dir>
"""
import json
import os

import bmesh
import bpy

import hs
from hs import A


def _hex(entry):
    """= scripts/v6/ortho.mjs paletteHex(entry) (no face): a string, else side ?? front ?? the first value."""
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        return entry.get("side") or entry.get("front") or next(iter(entry.values()))
    return "#ff00ff"


def build():
    path = os.environ.get("HS_MESH")
    if not path or not os.path.exists(path):
        raise SystemExit("build_from_mesh.py: set HS_MESH to a mesh.json (node scripts/hs/judge_mesh.mjs --module ... --export ...)")
    with open(path, encoding="utf-8") as f:
        mesh = json.load(f)
    zones = sorted({p.get("zone") or "default" for p in mesh["parts"]})
    pal = {z: _hex(mesh.get("palette", {}).get(z)) for z in zones}
    root = hs.begin("mesh", pal)
    parts = []
    for p in mesh["parts"]:
        bm = bmesh.new()
        pos = p["pos"]
        vs = [bm.verts.new(A(pos[i], pos[i + 1], pos[i + 2])) for i in range(0, len(pos), 3)]
        t = p["tris"]
        for i in range(0, len(t), 3):
            try:
                bm.faces.new((vs[t[i]], vs[t[i + 1]], vs[t[i + 2]]))
            except ValueError:  # a duplicate / degenerate tri
                pass
        me = bpy.data.meshes.new(p["id"])
        bm.to_mesh(me)
        bm.free()
        me.materials.append(hs.MATS[p.get("zone") or "default"])
        ob = bpy.data.objects.new(p["id"], me)
        ob["part"] = p.get("role") or p["id"]
        parts.append(hs.link(ob))
    return root, parts
