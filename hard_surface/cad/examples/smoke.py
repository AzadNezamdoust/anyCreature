from cadkit import *

body = Box(0.4, 0.1, 0.1)
body = safe_fillet(body, body.edges().filter_by(Axis.X), 0.08, label="too big -> reduced")
hole = Cylinder(0.02, 0.2, rotation=(90, 0, 0))
body = cut(body, hole, label="bore")
tag("top", face_at(body, "z", "max"))
peg = Pos(0.25, 0, 0) * Cylinder(0.03, 0.1, rotation=(0, 90, 0))
PARTS = {"body": (body, "#3a3d42"), "peg": (peg, "#ff6a00")}
SPEC = {"L": 0.48}
