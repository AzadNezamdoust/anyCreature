"""build.py (assault_rifle, t8 candidate B: CAD hybrid). Geometry = parts/<name>.stl from cad_parts.py (build123d
B-rep, exact booleans + CAD edge breaks, locked part tree + dimensional plan in plan.json, same numbers as the
baseline build). Blender side only: import, weld, materials (face predicates on the same plan), Freestyle marks,
sharp edges + Weighted Normal, box-projected UVs. build() -> (root, parts) for scripts/hs/run_pass.py.
"""
import math
import os
import struct

import bmesh
import bpy

import hs

SUBJECT = "assault_rifle"
HERE = os.path.dirname(os.path.abspath(__file__))
PDIR = os.path.join(HERE, "parts")

PALETTE = {"gunmetal": "#4e4e4e", "sight": "#4e4e4e", "steel": "#4e4e4e", "bolt": "#484848", "shadow": "#3a3a3a",
           "polymer": "#313131", "pad": "#404040", "trigger": "#2c2c2c", "lever": "#6c6c6c", "dark": "#141414",
           "accent": "#f8690b"}
S_PX = 887.2222222222222
BORE_Y = 0.2265


def Z(X):
    return (511.5 - X) / S_PX


def Y(Yp):
    return (653.0 - Yp) / S_PX


UP_HW, LO_HW, SEAM_Y = 0.033, 0.0295, 0.2172
CH_Y0, CH_Y1 = 0.2175, 0.2445
SLOT_Y, SLOT_R = 0.2355, 0.0075
MAG_O, MAG_A, MAG_P = (-0.0466, 0.183), (0.3217, -0.9468), (-0.9468, -0.3217)
MAG_TF, MAG_TR, MAG_HW, MAG_CL = -0.030, 0.032, 0.023, 0.0022
MAG_GROOVES = (-0.0070, 0.0175)


def mag_st(y, z):
    dz, dy = z - MAG_O[0], y - MAG_O[1]
    return dz * MAG_A[0] + dy * MAG_A[1], dz * MAG_P[0] + dy * MAG_P[1]


def near(y, z, yc, zc, r):
    return math.hypot(y - yc, z - zc) < r


# per part: (materials, [(predicate(x, y, z) in author metres, material index), ...] applied in order)
PAINT = {
    "receiver": (["gunmetal", "dark", "lever", "polymer"], [
        (lambda x, y, z: (lambda s, t: s > -0.003 and abs(x) < MAG_HW + MAG_CL + 2e-4 and
                          MAG_TF - MAG_CL - 2e-4 < t < MAG_TR + MAG_CL + 2e-4)(*mag_st(y, z)) and abs(x) < LO_HW - 3e-4, 1),
        (lambda x, y, z: abs(x) < 0.0067 and abs(y - 0.170) < 0.0151 and Z(630) - 2e-4 < z < Z(607) + 2e-4, 1),
        (lambda x, y, z: abs(x) > 0.0262 and Z(581.7) < z < Z(576.3) and Y(538) < y < Y(505), 3),
        (lambda x, y, z: abs(x) > 0.024 and near(y, z, Y(469), Z(682), 0.0037), 2),
        (lambda x, y, z: x < -LO_HW + 2e-4 and abs(y - Y(478)) < 0.0062 and abs(z - Z(592)) < 0.0082, 2)]),
    "upper": (["gunmetal", "dark", "lever", "shadow"], [
        (lambda x, y, z: -UP_HW + 0.0015 < x < -0.0125 and CH_Y0 < y < CH_Y1 and -0.09 < z < -0.02, 1),
        (lambda x, y, z: 0.0283 < abs(x) < 0.0331 and y < SEAM_Y + 0.0001 and -0.2095 < z < -0.0015, 1),
        (lambda x, y, z: 0.0170 < x < UP_HW - 0.0002 and abs(y - SLOT_Y) < SLOT_R + 0.0015 and Z(610) < z < Z(515), 1),
        (lambda x, y, z: 0.0026 < z < 0.0106, 3),
        (lambda x, y, z: 0.0106 <= z < 0.0137, 1),
        (lambda x, y, z: abs(x) > 0.026 and near(y, z, Y(479), Z(505.5), 0.0046), 2),
        (lambda x, y, z: abs(x) > 0.0314 and near(y, z, Y(479), Z(505.5), 0.0019), 1)]),
    "bolt": (["bolt"], []),
    "handguard": (["polymer", "dark"], [
        (lambda x, y, z: 0.06 < z < 0.23 and abs(y - Y(451.2)) < 0.0088 and 0.0295 < abs(x) < 0.0388, 1)]),
    "handguard_band": (["accent"], []),
    "barrel": (["steel"], []),
    "muzzle_brake": (["steel", "dark"], [
        (lambda x, y, z: math.hypot(x, y - BORE_Y) < 0.0097 and z > 0.39, 1),
        (lambda x, y, z: math.hypot(x, y - BORE_Y) < 0.0192 and 0.402 < z < 0.443, 1)]),
    "front_sight": (["sight"], []),
    "rail": (["sight", "dark"], [(lambda x, y, z: abs(y - 0.2715) < 0.0002 and abs(x) < 0.0146, 1)]),
    "rear_sight": (["sight", "dark", "lever"], [
        (lambda x, y, z: math.hypot(x, y - 0.3045) < 0.0031 and abs(z - Z(684)) < 0.003, 1),
        (lambda x, y, z: abs(x) > 0.021 and near(y, z, Y(386), Z(684), 0.0057), 2),
        (lambda x, y, z: abs(x) > 0.0259 and near(y, z, Y(386), Z(684), 0.0021), 1)]),
    "stock": (["polymer", "pad"], [(lambda x, y, z: z < Z(877.0), 1)]),
    "grip": (["polymer"], []),
    "magazine": (["polymer", "accent", "dark"], [
        (lambda x, y, z: mag_st(y, z)[0] > 0.1583, 1),
        (lambda x, y, z: (lambda s, t: s < 0.158 and MAG_HW - 0.0011 < abs(x) < MAG_HW - 1e-4 and
                          any(abs(t - tg) < 0.0015 for tg in MAG_GROOVES))(*mag_st(y, z)), 2)]),
    "trigger_guard": (["polymer"], []),
    "trigger": (["trigger"], []),
    "charging_handle": (["accent"], []),
    "selector": (["lever"], []),
}
ROLE = {"receiver": "receiver", "upper": "receiver", "bolt": "bolt", "handguard": "handguard",
        "handguard_band": "handguard", "barrel": "barrel", "muzzle_brake": "muzzle_device", "front_sight": "sight",
        "rail": "rail", "rear_sight": "sight", "stock": "stock", "grip": "grip", "magazine": "magazine",
        "trigger_guard": "trigger_guard", "trigger": "trigger", "charging_handle": "charging_handle",
        "selector": "selector"}


def read_stl(path):
    data = open(path, "rb").read()
    n = struct.unpack_from("<I", data, 80)[0]
    if 84 + 50 * n == len(data):
        tris = []
        for i in range(n):
            v = struct.unpack_from("<12f", data, 84 + 50 * i)
            tris.append((v[3:6], v[6:9], v[9:12]))
        return tris
    tris, cur = [], []
    for ln in data.decode("ascii", "ignore").splitlines():
        p = ln.split()
        if p and p[0] == "vertex":
            cur.append(tuple(float(c) for c in p[1:4]))
            if len(cur) == 3:
                tris.append(tuple(cur))
                cur = []
    return tris


def part(name):
    mats, paints = PAINT[name]
    bm = bmesh.new()
    vid = {}

    def V(p):
        k = tuple(round(c, 7) for c in p)
        if k not in vid:
            vid[k] = bm.verts.new(hs.A(*p))
        return vid[k]
    for t in read_stl(os.path.join(PDIR, name + ".stl")):
        vs = [V(p) for p in t]
        if len(set(vs)) == 3:
            try:
                bm.faces.new(vs)
            except ValueError:
                pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=2e-6)
    for _ in range(3):   # CAD edge breaks meeting at a corner leave sub-0.2 mm slivers: weld them (baseline tidy())
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=2e-4)
        bmesh.ops.dissolve_degenerate(bm, dist=2e-4, edges=bm.edges[:])
        thin = [f for f in bm.faces if f.calc_area() < 2e-8]
        if not thin:
            break
        es = {min(f.edges, key=lambda e: e.calc_length()) for f in thin}
        bmesh.ops.collapse(bm, edges=list(es))
    # CAD tessellation fans coplanar faces into slivers: merge coplanar triangles back into n-gons (same tris on
    # export, cleaner wire) -- dissolve_limit at 0.1 deg, planar regions only, boundaries kept
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(0.1), use_dissolve_boundaries=False,
                             verts=bm.verts[:], edges=bm.edges[:])
    for f in bm.faces:
        c = f.calc_center_median()
        x, y, z = c.x, c.z, -c.y
        for pred, mi in paints:
            if pred(x, y, z):
                f.material_index = mi
    return hs.finish(bm, name, mats, ROLE[name])


MARKS = [("receiver", [(514, 486.5), (562, 486.5), (571, 493.4)], 0.0016, LO_HW + 0.002),
         ("stock", [(715, 436.4), (885, 422.4)], 0.0012, 0.0235)]


def mark_line(ob, pts_px, tol, xmin):
    seg = [(Z(x), Y(y)) for x, y in pts_px]

    def dist(z, y):
        best = 1e9
        for (z0, y0), (z1, y1) in zip(seg, seg[1:]):
            dz, dy = z1 - z0, y1 - y0
            t = max(0.0, min(1.0, ((z - z0) * dz + (y - y0) * dy) / (dz * dz + dy * dy)))
            best = min(best, math.hypot(z - z0 - t * dz, y - y0 - t * dy))
        return best
    me = ob.data
    at = None
    for e in me.edges:
        a, b = me.vertices[e.vertices[0]].co, me.vertices[e.vertices[1]].co
        if a.x * b.x <= 0 or min(abs(a.x), abs(b.x)) < xmin or abs(a.x - b.x) > 0.0006:
            continue
        if (a - b).length > 0.0015 and dist(-a.y, a.z) < tol and dist(-b.y, b.z) < tol:
            try:
                e.use_freestyle_mark = True
            except AttributeError:
                at = at or me.attributes.get("freestyle_edge") or me.attributes.new("freestyle_edge", "BOOLEAN", "EDGE")
                at.data[e.index].value = True


def blender_finish(ob):
    """Blender stage of the hybrid: sharp edges > 30 deg, smooth + Weighted Normal (face area, keep sharp) baked
    into custom normals; box-projected UVs (dominant axis, 1 m = 1 UV unit: a trim-sheet-ready texel density)."""
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    for e in bm.edges:
        e.smooth = not (len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(30.0))
    for f in bm.faces:
        f.smooth = True
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        u_i, v_i = [(1, 2), (0, 2), (0, 1)][ax]
        for lp in f.loops:
            lp[uv].uv = (lp.vert.co[u_i] * 2.0, lp.vert.co[v_i] * 2.0)
    bm.to_mesh(me)
    bm.free()
    m = ob.modifiers.new("wn", "WEIGHTED_NORMAL")
    m.mode = "FACE_AREA"
    m.keep_sharp = True
    m.weight = 50
    hs.apply_modifiers(ob)


def build():
    root = hs.begin(SUBJECT, PALETTE)
    parts = [part(n) for n in PAINT]
    hs.end(parts, weld=1e-5)
    for n, pts, tol, xmin in MARKS:
        mark_line(bpy.data.objects[n], pts, tol, xmin)
    for ob in parts:
        blender_finish(ob)
    bpy.context.view_layer.update()
    return root, parts
