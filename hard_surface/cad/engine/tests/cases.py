"""Equivalence cases: op journals run through BOTH the Python kit (cadkit.tools.Model) and the C++ engine.
Each case = list of (op, params). Units: metres for op tests, mm for the L1 replica journal."""
import math

CASES = {}

CASES["prims"] = [
    ("box", {"name": "b", "size": [0.6, 0.4, 0.3], "at": [0.1, 0, 0]}),
    ("box", {"name": "bm", "size": [0.2, 0.2, 0.2], "align": "min", "at": [1, 1, 0]}),
    ("box", {"name": "bb", "size": [0.2, 0.3, 0.1], "align": "base", "plane": "XZ"}),
    ("cylinder", {"name": "c", "radius": 0.1, "height": 0.5, "plane": "YZ", "at": [0.2, 0.1, 0.3]}),
    ("cone", {"name": "k", "radius1": 0.2, "radius2": 0.05, "height": 0.3, "at": [0, 0, 1]}),
    ("sphere", {"name": "s", "radius": 0.15, "at": [2, 0, 0]}),
    ("torus", {"name": "t", "major": 0.3, "minor": 0.05, "plane": {"origin": [0, 2, 0], "normal": [1, 1, 0]}}),
]

CASES["fillet_chamfer"] = [
    ("box", {"name": "b", "size": [0.6, 0.4, 0.3]}),
    ("fillet", {"body": "b", "edges": {"parallel": "z"}, "radius": 0.05}),
    ("fillet", {"body": "b", "edges": {"pick": "max"}, "radius": 0.02}),
    ("box", {"name": "c", "size": [0.3, 0.3, 0.3], "at": [1, 0, 0]}),
    ("chamfer", {"body": "c", "edges": {"of_faces": {"normal": "+z"}}, "distance": 0.03}),
]

CASES["booleans"] = [
    ("box", {"name": "a", "size": [1, 1, 1]}),
    ("cylinder", {"name": "h", "radius": 0.2, "height": 2}),
    ("boolean", {"kind": "cut", "target": "a", "tools": ["h"]}),
    ("box", {"name": "u", "size": [0.5, 0.5, 0.5], "at": [0.5, 0.5, 0.5]}),
    ("boolean", {"kind": "union", "target": "a", "tools": "u"}),
    ("sphere", {"name": "s", "radius": 0.7}),
    ("boolean", {"kind": "intersect", "target": "a", "tools": ["s"], "keep_tools": True}),
    ("cylinder", {"name": "p1", "radius": 0.05, "height": 3, "plane": "YZ", "at": [0.3, 0.3, 0]}),
    ("cylinder", {"name": "p2", "radius": 0.05, "height": 3, "plane": "XZ", "at": [-0.3, -0.3, 0]}),
    ("boolean", {"kind": "cut", "target": "a", "tools": ["p1", "p2"]}),
]

CASES["sketch_extrude"] = [
    ("rectangle", {"name": "r", "width": 0.4, "height": 0.2, "corner_radius": 0.03}),
    ("extrude", {"name": "e", "profile": "r", "distance": 0.1, "distance2": 0.05}),
    ("circle", {"name": "c", "radius": 0.04, "center": [0.1, 0], "plane": {"origin": [0, 0, 0.1], "normal": "z"}}),
    ("extrude", {"name": "hole", "profile": "c", "distance": -0.3, "mode": "cut", "target": "e"}),
    ("polygon", {"name": "hx", "sides": 6, "radius": 0.05, "center": [-0.1, 0], "plane": {"origin": [0, 0, 0.1]}}),
    ("extrude", {"name": "boss", "profile": "hx", "distance": 0.04, "mode": "union", "target": "e"}),
    ("line", {"name": "l", "points": [[0, 0], [0.3, 0], [0.3, 0.1], [0.1, 0.2], [0, 0.2]], "closed": True,
              "plane": {"origin": [1, 0, 0]}}),
    ("extrude", {"name": "e2", "profile": "l", "distance": 0.05, "thickness": 0.01}),
    ("offset_curve", {"name": "ro", "curve": "r", "distance": 0.02}),
    ("fillet_curve", {"name": "lf", "curve": "l", "radius": 0.02}),
    ("regions", {"curves": ["ro", "r"], "prefix": "rg"}),
    ("prism", {"name": "pr", "region": "rg2", "height": 0.02}),
]

CASES["revolve_sweep_loft"] = [
    ("line", {"name": "prof", "points": [[0.1, 0], [0.2, 0], [0.2, 0.1], [0.15, 0.3], [0.1, 0.3]], "closed": True,
              "plane": "XZ"}),
    ("revolve", {"name": "rv", "profile": "prof", "axis_dir": "z"}),
    ("revolve", {"name": "rv2", "profile": "prof", "axis_dir": "z", "angle": 90}),
    ("spline", {"name": "path", "points": [[0, 0, 0], [0.2, 0.1, 0.2], [0.4, 0, 0.4]], "tangents": [[0, 0, 1], [1, 0, 0]]}),
    ("circle", {"name": "pc", "radius": 0.03, "plane": {"origin": [0, 0, 0], "normal": "z"}}),
    ("sweep", {"name": "sw", "profile": "pc", "path": "path"}),
    ("arc", {"name": "a", "start": [0, 0, 0], "mid": [0.3, 0.3, 0], "end": [0.6, 0, 0], "plane": {"origin": [0, 1, 0]}}),
    ("pipe", {"name": "pp", "path": "a", "radius": 0.02, "inner_radius": 0.01}),
    ("circle", {"name": "l1", "radius": 0.1, "plane": {"origin": [2, 0, 0], "normal": "z"}}),
    ("circle", {"name": "l2", "radius": 0.05, "plane": {"origin": [2, 0, 0.3], "normal": "z"}}),
    ("loft", {"name": "lo", "profiles": ["l1", "l2"]}),
    ("rectangle", {"name": "q1", "width": 0.2, "height": 0.2, "plane": {"origin": [3, 0, 0]}}),
    ("rectangle", {"name": "q2", "width": 0.1, "height": 0.3, "plane": {"origin": [3, 0, 0.4]}}),
    ("loft", {"name": "lr", "profiles": ["q1", "q2"], "ruled": True}),
]

CASES["shell_offset_split"] = [
    ("box", {"name": "b", "size": [0.4, 0.3, 0.2]}),
    ("shell", {"body": "b", "thickness": 0.01, "open_faces": {"obj": "b", "faces": {"normal": "+z"}}}),
    ("box", {"name": "c", "size": [0.4, 0.3, 0.2], "at": [1, 0, 0]}),
    ("offset_face", {"body": "c", "faces": {"normal": "+x"}, "distance": 0.05}),
    ("box", {"name": "d", "size": [0.4, 0.3, 0.2], "at": [2, 0, 0]}),
    ("split", {"body": "d", "plane": {"origin": [2.05, 0, 0], "normal": "x"}}),
    ("box", {"name": "e", "size": [0.4, 0.3, 0.2], "at": [3, 0, 0]}),
    ("split", {"body": "e", "plane": {"origin": [3, 0, 0.03], "normal": "z"}, "keep": "above"}),
    ("box", {"name": "f", "size": [0.4, 0.3, 0.2], "at": [4, 0, 0]}),
    ("box", {"name": "g", "size": [0.1, 0.1, 0.1], "at": [4.2, 0, 0.1]}),
    ("boolean", {"kind": "union", "target": "f", "tools": ["g"]}),
    ("delete_face", {"body": "f", "faces": {"within": [[4.15, -0.06, 0.09], [4.26, 0.06, 0.16]]}}),
]

CASES["pattern_transform"] = [
    ("box", {"name": "b", "size": [0.1, 0.1, 0.1]}),
    ("linear_array", {"name": "arr", "body": "b", "count": 3, "step": [0.15, 0, 0], "count2": 2, "step2": [0, 0.15, 0]}),
    ("cylinder", {"name": "c", "radius": 0.02, "height": 0.1, "at": [0.3, 0, 1]}),
    ("radial_array", {"name": "ra", "body": "c", "count": 6, "axis_origin": [0, 0, 1], "union": False}),
    ("box", {"name": "m", "size": [0.2, 0.1, 0.1], "at": [0.15, 2, 0]}),
    ("mirror", {"name": "mm", "body": "m", "plane": {"origin": [0.06, 2, 0], "normal": "x"}}),
    ("box", {"name": "n", "size": [0.1, 0.1, 0.1], "at": [0, 3, 0]}),
    ("mirror", {"name": "nc", "body": "n", "plane": "XZ", "union": False}),
    ("box", {"name": "t", "size": [0.3, 0.1, 0.05], "at": [0, 4, 0]}),
    ("move", {"obj": "t", "by": [0.1, 0.2, 0.3]}),
    ("rotate", {"obj": "t", "axis_dir": "z", "angle": 30}),
    ("scale", {"obj": "t", "factor": 1.5}),
    ("duplicate", {"name": "t2", "source": "t"}),
    ("move", {"obj": "t2", "by": [0, 0, 1]}),
    ("delete", {"obj": "t2"}),
]

CASES["refs_tags"] = [
    ("box", {"name": "b", "size": [0.6, 0.4, 0.3]}),
    ("cylinder", {"name": "h", "radius": 0.08, "height": 1}),
    ("boolean", {"kind": "cut", "target": "b", "tools": ["h"]}),
    ("tag", {"tag": "top", "ref": {"obj": "b", "faces": {"normal": "+z", "expect": 1}}}),
    ("fillet", {"body": "b", "edges": {"of_faces": {"tag": "top"}, "loop": "inner"}, "radius": 0.01}),
    ("fillet", {"body": "b", "edges": {"parallel": "z", "longer": 0.2}, "radius": 0.03}),
    ("chamfer", {"body": "b", "edges": {"of_faces": {"normal": "-z"}, "loop": "outer", "tangent_chain": True},
                 "distance": 0.01}),
    ("cplane", {"cname": "side", "face": {"obj": "b", "faces": {"pick": "max", "axis": "x"}}}),
    ("circle", {"name": "sc", "radius": 0.03, "plane": "side"}),
    ("extrude", {"name": "sb", "profile": "sc", "distance": 0.05, "mode": "union", "target": "b"}),
]


# ---------------------------------------------------------------- replica L1 as an op journal (mm)
def l1_journal():
    CL, CW, CH, RP, RT, RB, WALL = 97.0, 70.0, 25.0, 6.0, 5.0, 1.5, 2.0
    BX0, BY0, BZ, PCB = -CL / 2 + 6.0, -CW / 2 + 7.0, 4.0, 1.4
    ZT = BZ + PCB
    Z_SPLIT = 7.0
    J = [
        ("box", {"name": "outer", "size": [CL, CW, CH], "align": "base"}),
        ("fillet", {"body": "outer", "edges": {"parallel": "z"}, "radius": RP}),
        ("fillet", {"body": "outer", "edges": {"pick": "max"}, "radius": RT}),
        ("fillet", {"body": "outer", "edges": {"pick": "min"}, "radius": RB}),
        ("box", {"name": "inner", "size": [CL - 2 * WALL, CW - 2 * WALL, CH - 2 * WALL], "align": "base",
                 "at": [0, 0, WALL]}),
        ("fillet", {"body": "inner", "edges": {"parallel": "z"}, "radius": RP - WALL}),
        ("fillet", {"body": "inner", "edges": {"pick": "max"}, "radius": RT - WALL}),
        ("boolean", {"kind": "cut", "target": "outer", "tools": ["inner"]}),
    ]
    x0, x1 = BX0 + 3.5 + 7.7 - 8.0, BX0 + 53.5 + 6.0
    J += [("box", {"name": "rec", "size": [x1 - x0, 1.6, 11.0], "at": [(x0 + x1) / 2, -CW / 2, ZT + 2.0]}),
          ("fillet", {"body": "rec", "edges": {"parallel": "y"}, "radius": 3.0}),
          ("boolean", {"kind": "cut", "target": "outer", "tools": ["rec"]})]
    side = [(3.5 + 7.7, 9.6, 3.6, ZT + 1.6, "usbc"), (3.5 + 7.7 + 14.8, 7.5, 3.4, ZT + 1.5, "hdmi0"),
            (3.5 + 7.7 + 14.8 + 13.5, 7.5, 3.4, ZT + 1.5, "hdmi1"), (53.5, 6.6, 6.6, ZT + 3.0, "audio")]
    for xb, w, h, zc, k in side:
        if k == "audio":
            J.append(("cylinder", {"name": k, "radius": w / 2, "height": 3 * WALL,
                                   "plane": {"origin": [BX0 + xb, -CW / 2, zc], "normal": "-y"}}))
        else:
            J.append(("box", {"name": k, "size": [w, 3 * WALL, h], "at": [BX0 + xb, -CW / 2, zc]}))
        J.append(("boolean", {"kind": "cut", "target": "outer", "tools": [k]}))
    for yb, w, h, k in [(9.0, 14.6, 16.4, "usb0"), (27.0, 14.6, 16.4, "usb1"), (45.75, 16.6, 13.9, "eth")]:
        J += [("box", {"name": k, "size": [3 * WALL, w, h], "at": [CL / 2, BY0 + yb, ZT + h / 2 - 0.2]}),
              ("boolean", {"kind": "cut", "target": "outer", "tools": [k]})]
    J += [("box", {"name": "sd", "size": [3 * WALL, 14, 3], "at": [-CL / 2, BY0 + 28, BZ - 1.0]}),
          ("boolean", {"kind": "cut", "target": "outer", "tools": ["sd"]}),
          ("duplicate", {"name": "white", "source": "outer"}),
          ("box", {"name": "region", "size": [2 * CL, 2 * CW, Z_SPLIT + 1], "at": [0, 0, Z_SPLIT - (Z_SPLIT + 1) / 2]}),
          ("boolean", {"kind": "intersect", "target": "outer", "tools": ["region"], "keep_tools": True}),
          ("boolean", {"kind": "cut", "target": "white", "tools": ["region"]}),
          ("box", {"name": "pcb", "size": [85, 56, PCB], "align": "base", "at": [BX0 + 42.5, BY0 + 28, BZ]}),
          ("fillet", {"body": "pcb", "edges": {"parallel": "z"}, "radius": 3.0})]
    # ISO 4017 M8x40 bolt (no helix thread: L1 keeps a fallback for it too)
    D, P, LEN, S, K, E, DW, C = 8.0, 1.25, 40.0, 13.0, 5.3, 14.38, 11.63, 0.4
    D1 = D - 1.226869 * P
    r_ch = S / 2 * 0.95
    zc = K - C - (E - r_ch) * math.tan(math.radians(30))
    J += [("polygon", {"name": "hexp", "sides": 6, "radius": S / 2 / math.cos(math.pi / 6), "rotation": 30}),
          ("extrude", {"name": "head", "profile": "hexp", "distance": K - C}),
          ("line", {"name": "chp", "points": [[0, 0], [E, 0], [E, zc], [r_ch, K - C], [0, K - C]], "closed": True,
                    "plane": "XZ"}),
          ("revolve", {"name": "cone", "profile": "chp", "axis_dir": "z"}),
          ("boolean", {"kind": "intersect", "target": "head", "tools": ["cone"]}),
          ("move", {"obj": "head", "by": [0, 0, C]}),
          ("cylinder", {"name": "wf", "radius": DW / 2, "height": C, "at": [0, 0, C / 2]}),
          ("boolean", {"kind": "union", "target": "head", "tools": ["wf"]}),
          ("cylinder", {"name": "bolt", "radius": D / 2, "height": LEN, "at": [0, 0, -LEN / 2]}),
          ("line", {"name": "ptp", "points": [[0, -LEN], [D1 / 2 - 0.3, -LEN], [D / 2 + 0.5, -LEN + (D - D1) / 2 + 0.8],
                                              [D / 2 + 0.5, 1], [0, 1]], "closed": True, "plane": "XZ"}),
          ("revolve", {"name": "pt", "profile": "ptp", "axis_dir": "z"}),
          ("boolean", {"kind": "intersect", "target": "bolt", "tools": ["pt"]}),
          ("boolean", {"kind": "union", "target": "bolt", "tools": ["head"]}),
          ("rotate", {"obj": "bolt", "axis_dir": "y", "angle": 90, "pivot": [0, 0, 0]}),
          ("move", {"obj": "bolt", "by": [-LEN / 2, CW / 2 + 40, E / 2]})]
    return J


CASES["replica_L1"] = l1_journal()
