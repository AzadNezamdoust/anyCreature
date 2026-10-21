"""Demo: filleted sci-fi crate built only with cadkit.tools ops (journal replayable).

venv_cad python examples/tools_crate_demo.py [--no-render]
-> out/tools_runs/crate_demo/ (journal.json, model.step, model_hq.glb, render/sheet.png smooth+clay+zebra)
"""
import json
import os
import sys
import time

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CAD)
from cadkit.tools import Model, render, write_run  # noqa: E402

L, W, H = 0.80, 0.56, 0.50
m = Model()
r = m.run
t0 = time.time()
# body: box, vertical blends, tangent-chain top/bottom blends
r("box", name="crate", size=[L, W, H], align="base")
r("fillet", body="crate", edges={"parallel": "z"}, radius=0.05)
r("tag", tag="top_loop", ref={"obj": "crate", "edges": {"of_faces": {"normal": "+z"}, "loop": "outer"}})
r("fillet", body="crate", edges={"tag": "top_loop", "tangent_chain": True}, radius=0.02)
r("fillet", body="crate", edges={"of_faces": {"normal": "-z"}, "tangent_chain": True}, radius=0.012)
# recessed lid: rounded rect region on the top cplane, cut 6 mm, chamfer its rim
r("cplane", cname="top", face={"obj": "crate", "faces": {"normal": "+z", "pick": "largest"}})
r("rectangle", name="lid", width=L - 0.14, height=W - 0.14, corner_radius=0.04, plane="top")
r("extrude", name="lid_cut", profile="lid", distance=-0.006, mode="cut", target="crate")
# hatch: circle on the lid + radial bolt ring (union array)
r("circle", name="hatch", radius=0.09, center=[0.12, 0], plane={"origin": [0, 0, H - 0.006]})
r("extrude", name="hatch_boss", profile="hatch", distance=0.012, draft=8, mode="union", target="crate")
r("cylinder", name="bolt", radius=0.008, height=0.01, at=[0.12 + 0.07, 0, H + 0.009])
r("radial_array", name="bolts", body="bolt", count=8, axis_origin=[0.12, 0, 0], union=True)
r("boolean", kind="union", target="crate", tools=["bolts"])
# vents: slot cutter, linear array, cut into the lid
r("box", name="slot", size=[0.012, 0.16, 0.02], at=[-0.25, 0, H])
r("fillet", body="slot", edges={"parallel": "z"}, radius=0.0055)
r("linear_array", name="vents", body="slot", count=6, step=[0.03, 0, 0], union=False)
r("boolean", kind="cut", target="crate", tools=["vents"])
# side panel lines: imprint two rounded rects on the +Y flank, then push one panel out 4 mm
r("rectangle", name="pan_a", width=0.28, height=0.30, center=[-0.17, 0.22], corner_radius=0.025, plane="XZ")
r("rectangle", name="pan_b", width=0.28, height=0.30, center=[0.17, 0.22], corner_radius=0.025, plane="XZ")
r("move", obj="pan_a", by=[0, 0.5, 0])
r("move", obj="pan_b", by=[0, 0.5, 0])
r("imprint", body="crate", curves=["pan_a", "pan_b"], direction="-y")
r("offset_face", body="crate", faces={"normal": "+y", "near": [0.17, 0.28, 0.22]}, distance=0.004)
r("mirror", name="crate_m", body="crate", plane="XZ", keep=True, union=False)
r("delete", obj="crate_m")
# lofted handle on the -X end: guided loft (ellipse-ish sections along an arch), mirrored to +X
X0 = -L / 2 + 0.015  # ends sink 15 mm into the wall (no coplanar caps)
r("spline", name="arch", points=[[X0, -0.14, 0.36], [-L / 2 - 0.05, -0.09, 0.37], [-L / 2 - 0.065, 0, 0.375],
                                 [-L / 2 - 0.05, 0.09, 0.37], [X0, 0.14, 0.36]], tangents=["-x", "x"])
r("circle", name="h0", radius=0.017, plane={"origin": [X0, -0.14, 0.36], "normal": "-x"})
r("circle", name="h1", radius=0.011, plane={"origin": [-L / 2 - 0.065, 0, 0.375], "normal": "y"})
r("circle", name="h2", radius=0.017, plane={"origin": [X0, 0.14, 0.36], "normal": "x"})
r("loft", name="handle", profiles=["h0", "h1", "h2"], guide="arch")
r("mirror", name="handle_mx", body="handle", plane="YZ", union=False)
r("boolean", kind="union", target="crate", tools=["handle", "handle_mx"])
# feet: one chamfered foot, linked instances at the corners
r("box", name="foot", size=[0.12, 0.08, 0.02], at=[-0.27, -0.19, -0.01])
r("chamfer", body="foot", edges={"of_faces": {"normal": "-z"}}, distance=0.006)
r("instance", name="foot2", source="foot", move=[0.54, 0, 0])
r("instance", name="foot3", source="foot", move=[0, 0.38, 0])
r("instance", name="foot4", source="foot", move=[0.54, 0.38, 0])
for k, c in (("crate", "#5b6770"), ("foot", "#c9a227"), ("foot2", "#c9a227"), ("foot3", "#c9a227"),
             ("foot4", "#c9a227")):
    m.objects[k].meta["colour"] = c
build_s = time.time() - t0

out = os.path.join(CAD, "out", "tools_runs", "crate_demo")
os.makedirs(out, exist_ok=True)
json.dump(m.to_json(), open(os.path.join(out, "journal.json"), "w"), indent=1)
st = m.state()
print(json.dumps({"build_s": round(build_s, 1), "ops": len(m.nodes), "ops_used": sorted({n["op"] for n in m.nodes}),
                  "crate": st["objects"]["crate"]}, indent=1))
if "--no-render" in sys.argv:
    write_run(m, out, tris=6000)
else:
    print("sheet:", render(m, out))
