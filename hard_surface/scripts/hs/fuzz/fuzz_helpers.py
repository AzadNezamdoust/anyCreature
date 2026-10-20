"""
fuzz_helpers.py -- seeded stress test of scripts/hs/hs.py (Blender 5.1, background).

  cd D:\\Git\\anyCreature\\hard_surface
  "C:\\Program Files\\Blender Foundation\\Blender 5.1\\blender.exe" -b --factory-startup --python-exit-code 1 ^
      --python scripts/hs/fuzz/fuzz_helpers.py -- --seed S --n N --out <jsonl> [--no-freestyle]
  ... -- --replay <jsonl> --case ID        # re-run a recorded case from its recipe (not from the rng) and compare
  [--guards]      run with hs.begin(..., guards=True) (the hs.py guards, 2026-10-10)

Case ids S .. S+N-1; case id = the rng seed, so any case is regenerated from its id alone. Each case is a random
composition typical of weapon / vehicle parts: one base (box / chamfered box / cylinder / frustum / loft / prism /
profile_object / bore / tyre / hub / torus / wire cage) built with the hs primitives, then 0-4 booleans (box / cylinder /
plane cutters, incl. near-coplanar and near-tangent ones, DIFFERENCE / UNION / INTERSECT, hs.cut one-shot or stacked
hs.boolean + apply) and bevel_mod (0.5-10 mm, 1-3 segments) in several orders, optional mirror_x (apply or stacked).

Checks: run_pass.topology_report -- the function is lifted VERBATIM from scripts/hs/run_pass.py (ast, not a copy) so the
counters are exactly the harness's; evaluated per step (raw, and on a hs.cleanup copy) and on the final part after
hs.end(); material index sanity; Freestyle "edge appears twice" (C-level stdout of a 48 px Freestyle render captured
with dup2); volume sanity; sliver triangles. One JSON line per case.
"""
import ast
import hashlib
import json
import math
import os
import random
import sys
import tempfile
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
HSDIR = os.path.dirname(HERE)
sys.path.insert(0, HSDIR)
sys.dont_write_bytecode = True

import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import hs  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def _arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default


# variant switches (defaults = the wide, unguarded sampling that the main run uses)
POLICY = _arg("--policy", "wide")                   # wide | safe (constrained sampling, thresholds from --safe-json)
SAFE = json.load(open(_arg("--safe-json"), encoding="utf-8")) if _arg("--safe-json") else {}
FIX = set(x for x in (_arg("--fix", "") or "").split(",") if x)   # execution fixes under test: cutmats, weld, popnone
GUARDS = "--guards" in argv                          # hs.begin(..., guards=True): the hs.py guards (2026-10-10)


def _safe(key):
    return SAFE.get(key) if POLICY == "safe" else None


# ------------------------------------------------------------------------------------------ topology_report, verbatim
def _load_topology_report():
    path = os.path.join(HSDIR, "run_pass.py")
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "topology_report")
    seg = ast.get_source_segment(src, fn)
    ns = {"bmesh": bmesh}
    exec(compile(seg, path + ":topology_report", "exec"), ns)
    return ns["topology_report"], hashlib.sha1(seg.encode()).hexdigest()[:10]


topology_report, TOPO_SHA = _load_topology_report()
TOPO_KEYS = ("non_manifold_edges", "boundary_edges", "zero_area_faces", "duplicate_faces", "loose")
PALETTE = {"body": "#737750", "dark": "#1c1d1b", "metal": "#4a4c4d"}
MATNAMES = list(PALETTE)


# ------------------------------------------------------------------------------------------ small utils
def lu(rng, a, b):
    return math.exp(rng.uniform(math.log(a), math.log(b)))


def wchoice(rng, pairs):
    tot = sum(w for _, w in pairs)
    r = rng.random() * tot
    for k, w in pairs:
        r -= w
        if r <= 0:
            return k
    return pairs[-1][0]


def fl(v):
    if isinstance(v, (list, tuple)):
        return [fl(x) for x in v]
    if isinstance(v, Vector):
        return [float(x) for x in v]
    if isinstance(v, (np.floating, float)):
        return float(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    return v


def author_co(me):
    n = len(me.vertices)
    co = np.empty(n * 3, dtype=np.float64)
    if n:
        me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    return np.stack([co[:, 0], co[:, 2], -co[:, 1]], axis=1) if n else co  # Blender -> author (x, y, z)


def bbox_of(ob):
    a = author_co(ob.data)
    if len(a) == 0:
        return None
    return a.min(axis=0).tolist(), a.max(axis=0).tolist()


def bm_bbox(bm):
    a = np.array([[v.co.x, v.co.z, -v.co.y] for v in bm.verts])
    return a.min(axis=0).tolist(), a.max(axis=0).tolist()


def totals_of(rep):
    return [rep["totals"][k] for k in TOPO_KEYS]


def cleaned_totals(ob):
    """run_pass counters on a hs.cleanup copy (== the part after hs.end) + tris, truly degenerate tris (< 1e-10 m2), min tri area."""
    me2 = ob.data.copy()
    ob2 = bpy.data.objects.new("tmp_clean", me2)
    try:
        hs.cleanup(ob2)
        tot = totals_of(topology_report([ob2]))
        bm = bmesh.new()
        bm.from_mesh(me2)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        ar = [f.calc_area() for f in bm.faces]
        bm.free()
        return tot, len(me2.polygons), sum(1 for a in ar if a < 1e-10), (min(ar) if ar else None)
    finally:
        bpy.data.objects.remove(ob2)
        bpy.data.meshes.remove(me2)


def volume_of(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    try:
        return float(bm.calc_volume(signed=True))
    finally:
        bm.free()


def mesh_extras(ob):
    """sliver tris (height < 0.1 mm), shortest edge, edges with > 2 faces, signed volume, empty flag."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    gt2 = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    vol = float(bm.calc_volume(signed=True)) if len(bm.faces) else 0.0
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    sliver = 0
    min_edge = None
    min_area = None
    zero10 = 0
    for f in bm.faces:
        ar = f.calc_area()
        min_area = ar if min_area is None else min(min_area, ar)
        zero10 += ar < 1e-10
        ls = [e.calc_length() for e in f.edges]
        lm = max(ls) if ls else 0.0
        if lm > 0 and 2.0 * f.calc_area() / lm < 1e-4:
            sliver += 1
    for e in bm.edges:
        L = e.calc_length()
        min_edge = L if min_edge is None else min(min_edge, L)
    n = len(bm.faces)
    bm.free()
    return {"edges_gt2": gt2, "sliver_tris": sliver, "min_edge": min_edge, "min_area": min_area, "zero_1e10": zero10,
            "volume": vol, "tris": n}


def mat_check(ob):
    me = ob.data
    n = len(me.materials)
    none_slots = sum(1 for m in me.materials if m is None)
    idx = [p.material_index for p in me.polygons]
    oob = sum(1 for i in idx if i >= n or (i < n and me.materials[i] is None))
    used = set(idx)
    unused = sum(1 for i in range(n) if i not in used)
    return {"slots": n, "none_slots": none_slots, "oob_faces": oob, "unused_slots": unused, "faces": len(idx)}


# ------------------------------------------------------------------------------------------ Freestyle probe
_FS_READY = False


def freestyle_setup():
    global _FS_READY
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x = sc.render.resolution_y = 48
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    try:
        sc.eevee.taa_render_samples = 1
    except AttributeError:
        pass
    sc.render.use_freestyle = True
    fs = sc.view_layers[0].freestyle_settings
    fs.crease_angle = math.radians(134)
    ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new("ink")
    ls.select_by_edge_types = True
    ls.select_silhouette = ls.select_border = ls.select_crease = True
    _FS_READY = True


def freestyle_probe(ob):
    """Render the part once with Freestyle (same line set as run_pass) and capture the C-level warnings."""
    if not _FS_READY:
        freestyle_setup()
    sc = bpy.context.scene
    bb = bbox_of(ob)
    if bb is None:
        return {"twice": 0, "other": [], "skipped": "empty"}
    lo, hi = np.array(bb[0]), np.array(bb[1])
    ctr = (lo + hi) / 2
    diag = float(np.linalg.norm(hi - lo)) or 0.01
    cam = bpy.data.cameras.new("fcam")
    cam.type = "ORTHO"
    cam.ortho_scale = diag * 1.3
    cam.clip_start, cam.clip_end = 0.001, diag * 20
    co = bpy.data.objects.new("fcam", cam)
    sc.collection.objects.link(co)
    co.location = hs.A(ctr[0] + diag * 0.3, ctr[1] + diag * 0.4, ctr[2] + diag * 5)
    direction = hs.A(*ctr) - co.location
    co.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    sc.camera = co
    tf = tempfile.TemporaryFile(mode="w+b")
    sys.stdout.flush()
    sys.stderr.flush()
    o1, o2 = os.dup(1), os.dup(2)
    os.dup2(tf.fileno(), 1)
    os.dup2(tf.fileno(), 2)
    err = None
    try:
        bpy.ops.render.render()
    except Exception as e:  # noqa: BLE001
        err = f"{type(e).__name__}: {e}"[:200]
    finally:
        os.dup2(o1, 1)
        os.dup2(o2, 2)
        os.close(o1)
        os.close(o2)
    tf.seek(0)
    txt = tf.read().decode(errors="replace")
    tf.close()
    bpy.data.objects.remove(co)
    bpy.data.cameras.remove(cam)
    lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]
    twice = sum(1 for ln in lines if "appears twice" in ln)
    other = [ln[:160] for ln in lines if ("Warning" in ln or "Error" in ln or "error" in ln) and "appears twice" not in ln][:3]
    return {"twice": twice, "other": other, "render_error": err}


# ------------------------------------------------------------------------------------------ base shapes
def rect_ring(cx, cz, y, hx, hz):
    return [hs.A(cx - hx, y, cz - hz), hs.A(cx + hx, y, cz - hz), hs.A(cx + hx, y, cz + hz), hs.A(cx - hx, y, cz + hz)]


def build_base_bm(p, calls=None):
    """p -> (bm, cap_face_or_None, extra). All author coordinates are local + p['off']."""
    k = p["k"]
    ox, oy, oz = p["off"]
    bm = bmesh.new()
    cap = None
    log = calls.append if calls is not None else (lambda s: None)
    log("bm = bmesh.new()")
    if k == "box":
        faces = hs.box(bm, (ox, oy, oz), tuple(p["size"]), mat=0, chamfer=p["chamfer"])
        cap = faces[-1]
        log(f"faces = hs.box(bm, {(ox, oy, oz)!r}, {tuple(p['size'])!r}, mat=0, chamfer={p['chamfer']!r})")
    elif k == "cyl":
        c0 = (p["c0"][0] + ox, p["c0"][1] + oy, p["c0"][2] + oz)
        c1 = (p["c1"][0] + ox, p["c1"][1] + oy, p["c1"][2] + oz)
        vs, faces = hs.cylinder(bm, c0, c1, p["r"], p["n"], mat=0, r1=p["r1"])
        cap = faces[-1]
        log(f"vs, faces = hs.cylinder(bm, {c0!r}, {c1!r}, {p['r']!r}, {p['n']!r}, mat=0, r1={p['r1']!r})")
    elif k == "loft_rect":
        rings = [rect_ring(r["cx"] + ox, r["cz"] + oz, r["y"] + oy, r["hx"], r["hz"]) for r in p["rings"]]
        vs, faces = hs.loft(bm, rings)
        cap = faces[-1]
        log(f"vs, faces = hs.loft(bm, [rect_ring(...) for r in {p['rings']!r}])  # off={p['off']!r}")
    elif k == "loft_oct":
        rings = [hs.octagon(r["cx"] + ox, r["cz"] + oz, r["y"] + oy, r["hf"], r["hr"], r["hx"], r["ch"]) for r in p["rings"]]
        vs, faces = hs.loft(bm, rings)
        cap = faces[-1]
        log(f"vs, faces = hs.loft(bm, [hs.octagon(cx,cz,y,hf,hr,hx,ch) for r in {p['rings']!r}])  # off={p['off']!r}")
    elif k == "prism":
        poly, ax = p["poly"], p["axis"]
        ou, ov, ow = {"x": (oz, oy, ox), "z": (ox, oy, oz), "y": (ox, oz, oy)}[ax]
        poly2 = [(u + ou, v + ov) for u, v in poly]
        vs, faces = hs.prism(bm, poly2, ax, p["a0"] + ow, p["a1"] + ow)
        cap = faces[-1]
        log(f"vs, faces = hs.prism(bm, {poly2!r}, {ax!r}, {p['a0'] + ow!r}, {p['a1'] + ow!r})")
    elif k == "tyre":
        hs.tyre(bm, (ox, oy, oz), p["r"], p["hw"], tread_h=p["tread_h"], nseg=p["nseg"])
        log(f"hs.tyre(bm, {(ox, oy, oz)!r}, {p['r']!r}, {p['hw']!r}, tread_h={p['tread_h']!r}, nseg={p['nseg']!r})")
    elif k == "hub":
        hs.hub(bm, (ox, oy, oz), p["hw"], n=p["n"], bolts=p["bolts"], scale=p["scale"])
        log(f"hs.hub(bm, {(ox, oy, oz)!r}, {p['hw']!r}, n={p['n']!r}, bolts={p['bolts']!r}, scale={p['scale']!r})")
    elif k == "torus":
        hs.torus_x_y(bm, (ox, oy, oz), p["R"], p["r"], nu=p["nu"], nv=p["nv"])
        log(f"hs.torus_x_y(bm, {(ox, oy, oz)!r}, {p['R']!r}, {p['r']!r}, nu={p['nu']!r}, nv={p['nv']!r})")
    elif k == "cage":
        rings = [rect_ring(r["cx"] + ox, r["cz"] + oz, r["y"] + oy, r["hx"], r["hz"]) for r in p["rings"]]
        vs, faces = hs.loft(bm, rings, cap0=False, cap1=False)
        log(f"hs.loft(bm, [rect_ring(...) for r in {p['rings']!r}], cap0=False, cap1=False)  # off={p['off']!r}")
    else:
        raise ValueError(k)
    if p.get("bore") and cap is not None:
        b = p["bore"]
        hs.bore(bm, cap, wall=b["wall"], depth=b["depth"], mat=b["mat"])
        log(f"hs.bore(bm, faces[-1], wall={b['wall']!r}, depth={b['depth']!r}, mat={b['mat']!r})")
    return bm


def gen_base(rng, S, mirror_gap):
    """Concrete base parameters. mirror_gap = x of the part's inner face (None = unconstrained)."""
    kind = wchoice(rng, [("box", .14), ("box_chamfer", .12), ("cyl", .12), ("frustum", .05), ("cyl_bore", .06),
                         ("box_bore", .05), ("loft_rect", .07), ("loft_oct", .08), ("prism", .08), ("profile", .08),
                         ("tyre", .05), ("hub", .02), ("torus", .03), ("cage", .03), ("cyl_bevel_tiny", .02)])
    dims = [S * rng.uniform(0.25, 1.0) for _ in range(3)]
    dims[rng.randrange(3)] = S
    if rng.random() < 0.15:  # thin plate
        dims[rng.randrange(3)] = S * rng.uniform(0.04, 0.2)
    off = [rng.uniform(-S, S), rng.uniform(S * 0.5, S * 2), rng.uniform(-S, S)]
    p = {"off": off, "kind": kind}
    if kind in ("box", "box_chamfer", "box_bore"):
        ch = 0.0
        if kind == "box_chamfer":
            ch = lu(rng, 0.0005, 0.01) if rng.random() < 0.7 else rng.uniform(0.02, 0.6) * min(dims)
        p.update(k="box", size=dims, chamfer=ch)
        if kind == "box_bore":
            half = min(dims[0], dims[2]) / 2
            p["bore"] = {"wall": half * lu(rng, 0.03, 1.1), "depth": dims[1] * lu(rng, 0.05, 1.3), "mat": rng.choice([None, 0, 1])}
    elif kind in ("cyl", "frustum", "cyl_bore", "cyl_bevel_tiny"):
        axis = rng.choice(["x", "y", "z", "x", "z", "y", "tilt"])
        L = dims[0] if axis != "tilt" else S
        if axis == "tilt":
            v = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
            v = v.normalized() if v.length > 1e-3 else Vector((0, 1, 0))
        else:
            v = Vector({"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[axis])
        r = min(dims[1], dims[2]) / 2 * rng.uniform(0.3, 1.0)
        if kind == "cyl_bevel_tiny":
            r = lu(rng, 0.004, 0.02)
        c0 = (-v * L / 2)
        c1 = (v * L / 2)
        p.update(k="cyl", c0=fl(c0), c1=fl(c1), r=r, n=rng.choice([6, 8, 12, 16, 24, 32, 6, 8, 12, 3, 4, 5, 48]),
                 r1=(r * rng.uniform(0.2, 1.6) if kind == "frustum" else None))
        if kind == "cyl_bore":
            p["bore"] = {"wall": r * lu(rng, 0.03, 1.1), "depth": L * lu(rng, 0.05, 1.3), "mat": rng.choice([None, 0, 1])}
    elif kind in ("loft_rect", "cage"):
        nr = rng.choice([2, 2, 3, 4])
        y0 = 0.0
        rings = []
        hx, hz = dims[0] / 2, dims[2] / 2
        for i in range(nr):
            s = rng.uniform(0.4, 1.2)
            r = {"cx": rng.uniform(-0.1, 0.1) * dims[0], "cz": rng.uniform(-0.1, 0.1) * dims[2],
                 "y": y0, "hx": hx * s, "hz": hz * s}
            rings.append(r)
            y0 += dims[1] / (nr - 1)
        if rng.random() < 0.08:  # collapsed end ring (wedge / pyramid)
            rings[-1]["hx" if rng.random() < 0.5 else "hz"] = 0.0
        p.update(k=("cage" if kind == "cage" else "loft_rect"), rings=rings)
        if kind == "cage":
            p["thickness"] = lu(rng, 0.001, 0.03)
    elif kind == "loft_oct":
        nr = rng.choice([2, 3, 3, 4])
        rings = []
        y0 = 0.0
        for i in range(nr):
            s = rng.uniform(0.5, 1.2)
            rings.append({"cx": 0.0, "cz": 0.0, "y": y0, "hf": dims[2] / 2 * s, "hr": dims[2] / 2 * s * rng.uniform(0.6, 1.2),
                          "hx": dims[0] / 2 * s, "ch": rng.choice([0.0, 0.15, 0.38, 0.5, rng.uniform(0, 0.5)])})
            y0 += dims[1] / (nr - 1)
        p.update(k="loft_oct", rings=rings)
    elif kind == "prism":
        n = rng.randint(3, 8)
        angs = sorted(rng.uniform(0, 2 * math.pi) for _ in range(n))
        R = min(dims) / 2 * 1.3
        poly = [(math.cos(a) * R * rng.uniform(0.5, 1.0), math.sin(a) * R * rng.uniform(0.5, 1.0)) for a in angs]
        a0 = -dims[0] / 2
        p.update(k="prism", poly=poly, axis=rng.choice(["x", "y", "z"]), a0=a0, a1=a0 + max(dims))
    elif kind == "profile":
        n = rng.randint(2, 6)
        w = dims[0] / 2
        ys = sorted(rng.uniform(0, dims[1]) for _ in range(n))
        half = [(w * rng.uniform(0.3, 1.0), y) for y in ys]
        p.update(k="profile", half=half, axis=rng.choice(["x", "y", "z"]), a0=-dims[2] / 2, a1=dims[2] / 2,
                 bevel=(lu(rng, 0.0005, 0.01) if rng.random() < 0.7 else 0.0), angle=rng.choice([10, 25, 30, 45, 60]))
    elif kind == "tyre":
        r = lu(rng, 0.05, 0.5)
        p.update(k="tyre", r=r, hw=lu(rng, 0.02, 0.22), tread_h=r * rng.uniform(0.02, 0.12), nseg=rng.choice([6, 8, 12, 16, 24]))
    elif kind == "hub":
        r = lu(rng, 0.05, 0.5)
        p.update(k="hub", hw=lu(rng, 0.02, 0.22), n=rng.choice([6, 8, 10, 12]), bolts=rng.choice([4, 6, 8]), scale=r / 0.468)
    elif kind == "torus":
        R = lu(rng, 0.02, 0.3)
        p.update(k="torus", R=R, r=R * rng.uniform(0.05, 0.6), nu=rng.choice([3, 4, 6, 8, 12]), nv=rng.choice([3, 4, 6]))
    p["S"] = S
    if POLICY == "safe":
        if p.get("k") == "tyre" and _safe("tyre_hw_min"):
            p["hw"] = max(p["hw"], _safe("tyre_hw_min"))
        if p.get("k") == "box" and _safe("chamfer_ratio_max"):
            p["chamfer"] = min(p["chamfer"], _safe("chamfer_ratio_max") * min(p["size"]))
        if p.get("k") == "cage" and _safe("cage_ratio_max"):
            wmin = min(max(rg["hx"] for rg in p["rings"]) * 2, max(rg["hz"] for rg in p["rings"]) * 2)
            p["thickness"] = min(p["thickness"], _safe("cage_ratio_max") * max(wmin, 1e-6))
        if p.get("k") in ("loft_rect", "cage") and _safe("no_collapse"):
            for rg in p["rings"]:
                rg["hx"] = max(rg["hx"], 0.15 * max(r2["hx"] for r2 in p["rings"]))
                rg["hz"] = max(rg["hz"], 0.15 * max(r2["hz"] for r2 in p["rings"]))
        if p.get("k") == "profile" and _safe("profile_bevel_ratio_max"):
            p["bevel"] = min(p["bevel"], _safe("profile_bevel_ratio_max") * (p["a1"] - p["a0"]))
    if mirror_gap is not None:
        if p["k"] == "profile":
            bm = bmesh.new()
            ou, ov, ow = {"x": (off[2], off[1], 0.0), "z": (0.0, off[1], off[2]), "y": (0.0, off[2], off[1])}[p["axis"]]
            hs.prism(bm, [(u + ou, v + ov) for u, v in hs.mirror_profile([tuple(x) for x in p["half"]])], p["axis"], p["a0"] + ow, p["a1"] + ow)
        else:
            bm = build_base_bm(dict(p, off=[0.0, off[1], off[2]]))
        lo0 = bm_bbox(bm)[0][0]
        bm.free()
        p["off"][0] = mirror_gap - lo0
    nm = rng.choice([1, 1, 2, 3])
    p["mats"] = MATNAMES[:nm]
    if p.get("bore") and p["bore"]["mat"] is not None:   # harness: a bore material index past the slot list is caller error, not an hs defect
        p["bore"]["mat"] = min(p["bore"]["mat"], nm - 1)
    p["mat_rate"] = rng.choice([0.0, 0.0, 0.25, 0.5]) if nm > 1 else 0.0
    p["mat_seed"] = rng.randrange(1 << 30)
    return p


# ------------------------------------------------------------------------------------------ cutters
IDENT = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


def gen_over(rng):
    cm = _safe("cop_min")
    if cm:
        m = lu(rng, cm, max(cm * 10, 1e-2))
        return m if rng.random() < 0.5 else -m
    if rng.random() < 0.15:
        return 0.0
    m = lu(rng, 1e-7, 1e-2)
    return m if rng.random() < 0.5 else -m


def cyl_n(rng):
    return rng.choice([6, 8, 12, 16, 24, 32, 8, 16, 4, 48])


def ranges_to_cutter(rng, rngs, shape, axis):
    lo = [r[0] for r in rngs]
    hi = [r[1] for r in rngs]
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]
    size = [hi[i] - lo[i] for i in range(3)]
    if shape == "box":
        return {"k": "box", "c": c, "size": size, "axes": IDENT}
    o = [i for i in range(3) if i != axis]
    r = min(size[o[0]], size[o[1]]) / 2
    c0, c1 = list(c), list(c)
    c0[axis], c1[axis] = lo[axis], hi[axis]
    return {"k": "cyl", "c0": c0, "c1": c1, "r": r, "n": cyl_n(rng), "r1": None}


def tilt_cutter(rng, cu):
    ang = lu(rng, 0.001, 3.0)
    if _safe("tilt_min"):
        ang = lu(rng, _safe("tilt_min"), max(3.0, _safe("tilt_min") * 3))
    ax = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
    if ax.length < 1e-3:
        ax = Vector((0, 0, 1))
    R = Matrix.Rotation(math.radians(ang), 3, ax.normalized())
    if cu["k"] == "box":
        cu["axes"] = [fl(R @ Vector(a)) for a in cu["axes"]]
    elif cu["k"] == "cyl":
        m = (Vector(cu["c0"]) + Vector(cu["c1"])) / 2
        cu["c0"] = fl(m + R @ (Vector(cu["c0"]) - m))
        cu["c1"] = fl(m + R @ (Vector(cu["c1"]) - m))
    return ang


def build_cutter_bm(cu, calls=None):
    bm = bmesh.new()
    log = calls.append if calls is not None else (lambda s: None)
    log("cbm = bmesh.new()")
    if cu["k"] == "box":
        hs.oriented_box(bm, tuple(cu["c"]), [tuple(a) for a in cu["axes"]], tuple(cu["size"]))
        log(f"hs.oriented_box(cbm, {tuple(cu['c'])!r}, {[tuple(a) for a in cu['axes']]!r}, {tuple(cu['size'])!r})")
    elif cu["k"] == "cyl":
        hs.cylinder(bm, tuple(cu["c0"]), tuple(cu["c1"]), cu["r"], cu["n"], r1=cu["r1"])
        log(f"hs.cylinder(cbm, {tuple(cu['c0'])!r}, {tuple(cu['c1'])!r}, {cu['r']!r}, {cu['n']!r}, r1={cu['r1']!r})")
    elif cu["k"] == "plane":
        hs.plane_cutter(bm, tuple(cu["p0"]), tuple(cu["p1"]), tuple(cu["p2"]), tuple(cu["out"]), half=cu["half"], depth=cu["depth"])
        log(f"hs.plane_cutter(cbm, {tuple(cu['p0'])!r}, {tuple(cu['p1'])!r}, {tuple(cu['p2'])!r}, {tuple(cu['out'])!r}, half={cu['half']!r}, depth={cu['depth']!r})")
    else:
        raise ValueError(cu["k"])
    return bm


def cop_of(cu_bb, bb):
    """smallest distance between a cutter bound and a target bound on the same axis (coplanar / touching)."""
    best = None
    for i in range(3):
        for a in (cu_bb[0][i], cu_bb[1][i]):
            for b in (bb[0][i], bb[1][i]):
                d = abs(a - b)
                best = d if best is None else min(best, d)
    return best


def gen_cut(rng, bb, S, op_kind):
    lo, hi = bb
    d = [max(hi[i] - lo[i], 1e-6) for i in range(3)]
    mid = [(hi[i] + lo[i]) / 2 for i in range(3)]
    modes = [("through", .26), ("pocket", .22), ("flush_side", .12), ("tangent", .10), ("inside", .05), ("random", .10),
             ("plane", .05)]
    if op_kind == "UNION":
        modes = [("attach", .45), ("random", .15), ("flush_side", .1), ("inside", .05), ("pocket", .1), ("through", .1),
                 ("plane", .05)]
    mode = wchoice(rng, modes)
    shape = "box" if rng.random() < 0.55 else "cyl"
    a = rng.randrange(3)
    b, c = [i for i in range(3) if i != a]
    side = rng.choice([-1, 1])
    over = gen_over(rng)
    m1, m2 = lu(rng, 0.0005, 0.15) * S, lu(rng, 0.0005, 0.15) * S
    if _safe("cop_min"):
        m1, m2 = max(m1, _safe("cop_min") * 1.5), max(m2, _safe("cop_min") * 1.5)
    frac = lambda: rng.uniform(0.08, 0.7)

    def sub(i):  # random sub-range strictly inside the target on axis i
        h = d[i] * frac() / 2
        cc = rng.uniform(lo[i] + h, hi[i] - h) if hi[i] - h > lo[i] + h else mid[i]
        return (cc - h, cc + h)

    rngs = [None, None, None]
    cu = None
    if mode == "through":
        rngs[a] = (lo[a] - m1, hi[a] + m2)
        rngs[b], rngs[c] = sub(b), sub(c)
    elif mode == "pocket":
        plane = hi[a] if side > 0 else lo[a]
        depth = d[a] * rng.uniform(0.1, 0.7)
        out_edge = plane + side * over
        in_edge = plane - side * depth
        rngs[a] = (min(out_edge, in_edge), max(out_edge, in_edge))
        rngs[b], rngs[c] = sub(b), sub(c)
    elif mode == "flush_side":
        rngs[a] = (lo[a] - m1, hi[a] + m2)
        rngs[b] = sub(b)
        rngs[c] = sub(c)
        s2 = rng.choice([-1, 1])
        h = d[c] * frac()
        if s2 > 0:
            rngs[c] = (hi[c] + over - h, hi[c] + over)
        else:
            rngs[c] = (lo[c] - over, lo[c] - over + h)
        if rng.random() < 0.4:  # second flush plane
            s3 = rng.choice([-1, 1])
            h = d[b] * frac()
            ov2 = gen_over(rng)
            rngs[b] = (hi[b] + ov2 - h, hi[b] + ov2) if s3 > 0 else (lo[b] - ov2, lo[b] - ov2 + h)
    elif mode == "tangent":
        shape = "cyl"
        r = min(d[b], d[c]) * rng.uniform(0.15, 0.45)
        pl = hi[b] if side > 0 else lo[b]
        cb = pl - side * (r - over)
        cc = rng.uniform(lo[c] + r, hi[c] - r) if hi[c] - r > lo[c] + r else mid[c]
        rngs[a] = (lo[a] - m1, hi[a] + m2)
        rngs[b] = (cb - r, cb + r)
        rngs[c] = (cc - r, cc + r)
    elif mode == "inside":
        for i in range(3):
            rngs[i] = sub(i)
    elif mode == "random":
        for i in range(3):
            h = d[i] * rng.uniform(0.1, 0.8) / 2
            cc = rng.uniform(lo[i] - 0.3 * d[i], hi[i] + 0.3 * d[i])
            rngs[i] = (cc - h, cc + h)
    elif mode == "attach":
        plane = hi[a] if side > 0 else lo[a]
        ext = d[a] * rng.uniform(0.1, 0.8)
        near = plane - side * over   # over > 0 = overlap into the target, 0 = touching faces, < 0 = gap
        far = plane + side * ext
        rngs[a] = (min(near, far), max(near, far))
        rngs[b], rngs[c] = sub(b), sub(c)
        if rng.random() < 0.3:
            rngs[b] = (lo[b] + gen_over(rng), hi[b] + gen_over(rng))
    if mode == "plane":
        sx = [rng.choice([lo[i], hi[i]]) for i in range(3)]
        t = [d[i] * rng.uniform(0.1, 0.6) for i in range(3)]
        p0 = [sx[0] - (t[0] if sx[0] == hi[0] else -t[0]), sx[1], sx[2]]
        p1 = [sx[0], sx[1] - (t[1] if sx[1] == hi[1] else -t[1]), sx[2]]
        p2 = [sx[0], sx[1], sx[2] - (t[2] if sx[2] == hi[2] else -t[2])]
        out = [sx[i] - mid[i] for i in range(3)]
        mx = max(d)
        cu = {"k": "plane", "p0": p0, "p1": p1, "p2": p2, "out": out, "half": mx * 1.5, "depth": mx * 2.0}
        tilt = 0.0
    else:
        cu = ranges_to_cutter(rng, rngs, shape, a)
        tilt = 0.0
        if rng.random() < 0.2:
            tilt = tilt_cutter(rng, cu)
    return {"op": "cut", "op_kind": op_kind, "cutter": cu, "mode": mode, "over": over, "tilt": tilt, "axis": a,
            "via": ("cut" if _safe("no_stack") else rng.choice(["cut", "cut", "stack"])), "cutter_mats": rng.choice([0, 0, 1, 2]), "cutter_facemat": rng.random() < 0.3}


def gen_bevel(rng, bb, apply_flag):
    w = lu(rng, 0.0005, 0.01)
    md = min(max(bb[1][i] - bb[0][i], 1e-6) for i in range(3))
    seg = rng.choice([1, 1, 1, 2, 3])
    if _safe("seg_max"):
        seg = min(seg, _safe("seg_max"))
    ang = rng.choice([10, 25, 30, 30, 45, 60])
    skip = False
    if _safe("ratio_max"):
        w = min(w, _safe("ratio_max") * md)
    if _safe("wps_min"):
        while seg > 1 and w / seg < _safe("wps_min"):
            seg -= 1
        skip = w / seg < _safe("wps_min")
    return {"op": "bevel", "width": w, "segments": seg, "angle": ang, "apply": apply_flag, "ratio": w / md, "skip": skip}


# ------------------------------------------------------------------------------------------ state + execution
class State:
    def __init__(self):
        self.ob = None
        self.pending = []
        self.calls = []

    def kill_pending(self):
        for c in self.pending:
            try:
                hs.kill(c)
            except Exception:  # noqa: BLE001
                pass
        self.pending = []


def exec_base(st, p):
    calls = st.calls
    if p["k"] == "profile":
        poly = hs.mirror_profile([tuple(x) for x in p["half"]])
        ox, oy, oz = p["off"]
        ou, ov, ow = {"x": (oz, oy, ox), "z": (ox, oy, oz), "y": (ox, oz, oy)}[p["axis"]]
        poly = [(u + ou, v + ov) for u, v in poly]
        ob = hs.profile_object("part", poly, p["axis"], p["a0"] + ow, p["a1"] + ow, p["mats"], "fuzz", bevel=p["bevel"], angle_deg=p["angle"])
        calls.append(f"ob = hs.profile_object('part', {poly!r}, {p['axis']!r}, {p['a0'] + ow!r}, {p['a1'] + ow!r}, {p['mats']!r}, 'fuzz', bevel={p['bevel']!r}, angle_deg={p['angle']!r})")
        st.ob = ob
        return
    bm = build_base_bm(p, calls)
    if p["mat_rate"] > 0 and len(p["mats"]) > 1:
        mr = random.Random(p["mat_seed"])
        for f in bm.faces:
            if mr.random() < p["mat_rate"]:
                f.material_index = mr.randrange(len(p["mats"]))
        calls.append(f"# random face material_index (rate {p['mat_rate']}, seed {p['mat_seed']}) over {len(p['mats'])} slots")
    st.ob = hs.finish(bm, "part", p["mats"], "fuzz")
    calls.append(f"ob = hs.finish(bm, 'part', {p['mats']!r}, 'fuzz')")
    if "precut" in FIX:
        hs.cleanup(st.ob)
        calls.append("hs.cleanup(ob)  # FIX precut: weld the base before it is a boolean target")
    if p["k"] == "cage":
        hs.wire_cage(st.ob, p["thickness"])
        hs.apply_modifiers(st.ob)
        calls.append(f"hs.wire_cage(ob, {p['thickness']!r}); hs.apply_modifiers(ob)")


def _weld_dist():
    """weld (1e-5, hs.cleanup's default), weld4 (1e-4) or weld=<dist>."""
    if "weld4" in FIX:
        return 1e-4
    for f in FIX:
        if f.startswith("weld="):
            return float(f[5:])
    return 1e-5 if "weld" in FIX else None


def mirror_x_safe(ob, tol=2e-5):
    """PROPOSED hs.mirror_x: mirror across x = 0; when the part touches the plane (inner face within `tol` of x = 0) the two
    halves would share a doubled internal wall (4 faces on its border edges), so snap the inner verts onto x = 0, weld, and
    delete the faces that lie in the plane."""
    if ob.modifiers:
        hs.apply_modifiers(ob)
    hs.add_mirror_x(ob)
    me = ob.data
    near = [v for v in me.vertices if abs(v.co.x) < tol]
    if not near:
        return hs.apply_modifiers(ob)
    for v in near:
        v.co.x = 0.0
    hs.apply_modifiers(ob)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=2 * tol)
    wall = [f for f in bm.faces if all(abs(v.co.x) < tol for v in f.verts)]
    bmesh.ops.delete(bm, geom=wall, context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(ob.data)
    bm.free()
    return ob


def _post_apply(st):
    """execution fixes under test, run after every apply."""
    ob = st.ob
    if "popnone" in FIX:
        me = ob.data
        for i in reversed(range(len(me.materials))):
            if me.materials[i] is None:
                me.materials.pop(index=i)
        st.calls.append("# FIX popnone: dropped None material slots")
    wd = _weld_dist()
    if wd:
        hs.cleanup(ob, wd)
        st.calls.append(f"hs.cleanup(ob, {wd!r})  # FIX weld")
    if "dissolve" in FIX:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(1.0), verts=bm.verts[:], edges=bm.edges[:])
        bm.to_mesh(ob.data)
        bm.free()
        st.calls.append("dissolve_limited(1 deg)  # FIX dissolve")


def exec_op(st, op):
    ob = st.ob
    k = op["op"]
    calls = st.calls
    if k == "bevel":
        if op.get("skip"):
            calls.append(f"# bevel skipped (safe policy: width {op['width']!r} / {op['segments']} seg too thin)")
            return
        if (_weld_dist() or "dissolve" in FIX) and ob.modifiers:
            hs.apply_modifiers(ob)
            st.kill_pending()
            calls.append("hs.apply_modifiers(ob)  # FIX weld: flush the stack before bevel")
            _post_apply(st)
        hs.bevel_mod(ob, op["width"], op["angle"], op["segments"])
        calls.append(f"hs.bevel_mod(ob, {op['width']!r}, {op['angle']!r}, {op['segments']!r})")
        if op["apply"]:
            hs.apply_modifiers(ob)
            st.kill_pending()
            calls.append("hs.apply_modifiers(ob)")
            _post_apply(st)
    elif k == "cut":
        bm = build_cutter_bm(op["cutter"], calls)
        if "precut" in FIX:
            bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
            calls.append("bmesh.ops.remove_doubles(cbm, verts=cbm.verts[:], dist=1e-5)  # FIX precut")
        if op["via"] == "cut":
            if "cutmats" in FIX:
                c = hs.temp_object(bm, "cutter")
                for m in ob.data.materials:
                    c.data.materials.append(m)
                hs.boolean(ob, c, op["op_kind"])
                hs.apply_modifiers(ob)
                hs.kill(c)
                calls.append(f"# FIX cutmats: cutter carries the target's slots; boolean {op['op_kind']!r} + apply")
            else:
                hs.cut(ob, bm, op["op_kind"])
                calls.append(f"hs.cut(ob, cbm, {op['op_kind']!r})")
            st.kill_pending()
            _post_apply(st)
        else:
            nmats = op["cutter_mats"]
            if op["cutter_facemat"] and nmats > 1:
                for i, f in enumerate(bm.faces):
                    if i % 3 == 0:
                        f.material_index = min(1, len(ob.data.materials) - 1) if "cutmats" in FIX else 1
            c = hs.temp_object(bm, "cutter")
            if "cutmats" in FIX:
                for m in ob.data.materials:
                    c.data.materials.append(m)
            else:
                for mn in MATNAMES[:nmats]:
                    c.data.materials.append(hs.MATS[mn])
            hs.boolean(ob, c, op["op_kind"])
            st.pending.append(c)
            calls.append(f"c = hs.temp_object(cbm, 'cutter')  # {nmats} material slot(s); hs.boolean(ob, c, {op['op_kind']!r})  # stacked")
    elif k == "apply":
        hs.apply_modifiers(ob)
        st.kill_pending()
        calls.append("hs.apply_modifiers(ob)")
        _post_apply(st)
    elif k == "mirror_x":
        if op["via"] == "apply":
            if "mirrorfix" in FIX:
                mirror_x_safe(ob)
                calls.append("mirror_x_safe(ob)  # FIX mirrorfix (proposed hs.mirror_x)")
            else:
                hs.mirror_x(ob)
                calls.append("hs.mirror_x(ob)")
            st.kill_pending()
            _post_apply(st)
        else:
            hs.add_mirror_x(ob)
            calls.append("hs.add_mirror_x(ob)  # stacked")
    else:
        raise ValueError(k)


def plan_for(rng):
    cls = wchoice(rng, [("cuts_bevel", .38), ("bevel_cuts", .27), ("interleaved", .15), ("cuts_only", .10), ("bevel_only", .05), ("cut_cut_bevel_cut", .05)])
    ncut = rng.choice([1, 2, 2, 3, 4])
    if cls == "cuts_bevel":
        toks = ["C"] * ncut + ["B"]
    elif cls == "bevel_cuts":
        toks = ["B"] + ["C"] * ncut
    elif cls == "interleaved":
        ncut = max(ncut, 2)
        k = rng.randint(1, ncut - 1)
        toks = ["C"] * k + ["B"] + ["C"] * (ncut - k)
    elif cls == "cuts_only":
        toks = ["C"] * ncut
    elif cls == "bevel_only":
        toks = ["B"]
    else:
        toks = ["C", "C", "B", "C"]
    if _safe("bevel_first"):
        toks = [t for t in toks if t == "B"] + [t for t in toks if t != "B"]
    mir = None
    if rng.random() < 0.35:
        mir = rng.choice(["start", "end"])
        toks = (["M"] + toks) if mir == "start" else (toks + ["M"])
    return cls, toks


def group_features(ops):
    f = {}
    cuts = [o for o in ops if o["op"] == "cut"]
    bev = [o for o in ops if o["op"] == "bevel"]
    if cuts:
        f["cop_min"] = min(o["cop"] for o in cuts if o.get("cop") is not None) if any(o.get("cop") is not None for o in cuts) else None
        f["n_cut"] = len(cuts)
    if bev:
        f["ratio_max"] = max(o["ratio"] for o in bev)
        f["width"] = max(o["width"] for o in bev)
        f["segments"] = max(o["segments"] for o in bev)
    return f


def run_case(cid, recipe=None, freestyle=True):
    t0 = time.perf_counter()
    rng = random.Random(cid)
    rng_S = lu(rng, 0.01, 0.5)
    hs.begin("fuzz", PALETTE, guards=GUARDS)
    st = State()
    ops_done = []
    steps = []
    exc = None
    cls = toks = None
    result = {"case": cid}
    try:
        if recipe is None:
            cls, toks = plan_for(rng)
            mir_gap = None
            if "M" in toks:
                pol = wchoice(rng, [("clear", .4), ("touch", .3), ("cross", .3)])
                if pol == "clear":
                    mir_gap = lu(rng, 0.0005, rng_S)
                    if _safe("mirror_gap_min"):
                        mir_gap = max(mir_gap, _safe("mirror_gap_min") * 1.2)
                elif pol == "touch":
                    mir_gap = gen_over(rng)
                    if _safe("mirror_gap_min"):
                        mir_gap = _safe("mirror_gap_min") * rng.uniform(1.0, 3.0)
                else:
                    mir_gap = -rng_S * rng.uniform(0.05, 0.5)
            base = gen_base(rng, rng_S, mir_gap)
            recipe = {"S": rng_S, "class": cls, "tokens": toks, "mirror_gap_target": mir_gap, "base": base, "ops": []}
            live = True
        else:
            live = False
            cls, toks = recipe["class"], recipe["tokens"]
            base = recipe["base"]
        result.update(S=recipe["S"], cls=cls, tokens="".join(toks), base_kind=base["kind"])
        exec_base(st, base)
        bb = bbox_of(st.ob)
        rep0 = topology_report([st.ob])
        mc0 = mat_check(st.ob)
        ct0 = cleaned_totals(st.ob)
        steps.append({"op": "base", "mat": [mc0["slots"], mc0["none_slots"], mc0["oob_faces"]], "raw": totals_of(rep0), "clean": ct0[0],
                      "z10": ct0[2], "minA": ct0[3], "tris": rep0["tris"], "vol": volume_of(st.ob)})
        group = []
        if live:
            # tokens -> concrete ops one at a time (they depend on the live bbox); every op is recorded before it runs
            seq = [("C", wchoice(rng, [("DIFFERENCE", .68), ("UNION", .27), ("INTERSECT", .05)])) if tk == "C" else (tk, None)
                   for tk in toks]
            for si, (tk, ok) in enumerate(seq):
                bb = bbox_of(st.ob) or bb
                if tk == "C":
                    op = gen_cut(rng, bb, rng_S, ok)
                    cb = build_cutter_bm(op["cutter"])
                    op["cop"] = cop_of(bm_bbox(cb), bb) if op["cutter"]["k"] != "plane" else None
                    cb.free()
                elif tk == "B":
                    nxt_is_stack = si + 1 < len(seq) and seq[si + 1][0] == "C"
                    op = gen_bevel(rng, bb, apply_flag=(True if _safe("no_stack") else not (nxt_is_stack and rng.random() < 0.3)))
                else:
                    op = {"op": "mirror_x", "via": ("apply" if _safe("no_stack") else rng.choice(["apply", "apply", "stack"])), "gap": bb[0][0]}
                recipe["ops"].append(op)
                _run_one(st, op, group, steps, ops_done)
        else:
            for op in recipe["ops"]:
                _run_one(st, op, group, steps, ops_done)
        if st.ob.modifiers:
            op = {"op": "apply", "auto": True}
            if live:
                recipe["ops"].append(op)
            _run_one(st, op, group, steps, ops_done)
    except Exception as e:  # noqa: BLE001
        tb = traceback.extract_tb(sys.exc_info()[2])
        frames = [f"{os.path.basename(f.filename)}:{f.name}:{f.lineno}" for f in tb[-3:]]
        exc = {"type": type(e).__name__, "msg": str(e)[:240], "where": frames, "op_index": len(ops_done)}
    result["recipe"] = recipe
    result["variant"] = {"policy": POLICY, "fix": sorted(FIX), "safe": SAFE if POLICY == "safe" else None,
                         "guards": GUARDS}
    result["guard_warn"] = list(hs.GUARD_WARN)
    result["calls"] = st.calls
    result["steps"] = steps
    result["exc"] = exc
    result["helpers"] = helpers_used(recipe) if recipe else []
    ob = st.ob
    final = {}
    fail, soft = [], []
    if exc:
        fail.append("exception")
    if ob is not None and exc is None:
        try:
            if ob.modifiers:
                hs.apply_modifiers(ob)
            st.kill_pending()
            raw = topology_report([ob])
            result["raw_totals"] = totals_of(raw)
            hs.end([ob])
            rep = topology_report([ob])
            tot = rep["totals"]
            final = {"tris": rep["tris"], "totals": [tot[k] for k in TOPO_KEYS], "coincident": tot["coincident_faces_across_objects"]}
            ex = mesh_extras(ob)
            final.update(ex)
            result["mat"] = mat_check(ob)
            if rep["tris"] == 0 or len(ob.data.vertices) == 0:
                fail.append("empty_mesh")
            for key, code in zip(TOPO_KEYS, ("nonmanifold", "boundary", "zero_area", "duplicate", "loose")):
                if tot[key]:
                    fail.append("topo_" + code)
            if ex["edges_gt2"]:
                fail.append("topo_edges_gt2")
            if ex["zero_1e10"]:
                fail.append("zero_area_true")
            if result["mat"]["none_slots"]:
                fail.append("mat_empty_slot")
            if result["mat"]["oob_faces"]:
                fail.append("mat_oob_faces")
            if ex["volume"] < 0:
                fail.append("neg_volume")
            if ex["sliver_tris"]:
                soft.append("sliver")
            if any(s.get("vol_bad") for s in steps):
                soft.append("volume_violation")
            if freestyle and rep["tris"] > 0:
                fsr = freestyle_probe(ob)
                result["fs"] = fsr
                if fsr["twice"]:
                    fail.append("freestyle_twice")
                if fsr.get("render_error"):
                    soft.append("freestyle_error")
        except Exception as e:  # noqa: BLE001
            tb = traceback.extract_tb(sys.exc_info()[2])
            result["exc"] = {"type": type(e).__name__, "msg": str(e)[:240], "where": [f"{os.path.basename(f.filename)}:{f.name}:{f.lineno}" for f in tb[-3:]], "op_index": -1, "phase": "check"}
            fail.append("exception")
    result["final"] = final
    result["fail"] = fail
    result["soft"] = soft
    result["t"] = round(time.perf_counter() - t0, 3)
    return result


def helpers_used(recipe):
    h = {"begin", "finish", "end", "cleanup"}
    b = recipe["base"]
    kmap = {"box": "box", "cyl": "cylinder", "loft_rect": "loft", "loft_oct": "loft", "prism": "prism", "profile": "profile_object",
            "tyre": "tyre", "hub": "hub", "torus": "torus_x_y", "cage": "wire_cage"}
    h.add(kmap[b["k"]])
    if b["k"] == "loft_oct":
        h.add("octagon")
    if b["k"] == "box" and b.get("chamfer", 0) > 0:
        h.add("box_chamfer")
    if b.get("bore"):
        h.add("bore")
    if b["k"] == "cyl" and b.get("r1") is not None:
        h.add("cylinder_frustum")
    if b["k"] in ("prism",):
        h.add("loft")
    if b["k"] == "profile":
        h.update(["mirror_profile", "prism", "bevel_mod", "apply_modifiers"])
    for o in recipe["ops"]:
        if o["op"] == "bevel":
            h.update(["bevel_mod", "apply_modifiers"])
        elif o["op"] == "cut":
            h.update(["oriented_box" if o["cutter"]["k"] == "box" else ("cylinder" if o["cutter"]["k"] == "cyl" else "plane_cutter")])
            if o["via"] == "cut":
                h.update(["cut", "temp_object", "boolean", "apply_modifiers"])
            else:
                h.update(["boolean", "temp_object", "apply_modifiers"])
            h.add("bool_" + o["op_kind"])
        elif o["op"] == "mirror_x":
            h.update(["mirror_x" if o["via"] == "apply" else "add_mirror_x", "apply_modifiers"])
        elif o["op"] == "apply":
            h.add("apply_modifiers")
    return sorted(h)


def _run_one(st, op, group, steps, ops_done):
    ob = st.ob
    before_vol = steps[-1]["vol"] if steps else None
    exec_op(st, op)
    ops_done.append(op)
    group.append(op)
    pend = len(st.ob.modifiers) > 0
    step = {"op": op["op"] + (":" + op["op_kind"] if op["op"] == "cut" else ""), "pending": pend, "vol": before_vol}
    if op["op"] == "cut":
        step["via"] = op["via"]
    if not pend:
        # evaluation point: topology (raw + on a cleaned copy), tris, volume
        rep = topology_report([st.ob])
        step["raw"] = totals_of(rep)
        ct = cleaned_totals(st.ob)
        step["clean"], step["z10"], step["minA"] = ct[0], ct[2], ct[3]
        step["tris"] = rep["tris"]
        vol = volume_of(st.ob)
        step["vol"] = vol
        step["empty"] = rep["tris"] == 0
        mc = mat_check(st.ob)
        step["mat"] = [mc["slots"], mc["none_slots"], mc["oob_faces"]]
        kinds = [o["op_kind"] for o in group if o["op"] == "cut"]
        has_bev = any(o["op"] == "bevel" for o in group)
        has_mir = any(o["op"] == "mirror_x" for o in group)
        tol = 1e-3 * abs(before_vol or 0) + 1e-9
        if before_vol is not None and not has_mir:
            if kinds and all(k == "DIFFERENCE" for k in kinds) and not has_bev and vol > before_vol + tol:
                step["vol_bad"] = True
            if kinds and all(k == "UNION" for k in kinds) and not has_bev and vol < before_vol - tol:
                step["vol_bad"] = True
            if not kinds and has_bev and vol > before_vol + tol:
                step["vol_bad"] = True
        step["group"] = [o["op"] for o in group]
        step["gfeat"] = group_features(group)
        group.clear()
    steps.append(step)


def main():
    global GUARDS
    out = _arg("--out")
    nofs = "--no-freestyle" in argv
    if _arg("--replay"):
        want = int(_arg("--case"))
        with open(_arg("--replay"), encoding="utf-8") as f:
            for ln in f:
                r = json.loads(ln)
                if r.get("case") == want and r.get("recipe"):
                    FIX.clear()
                    FIX.update((r.get("variant") or {}).get("fix", []))
                    GUARDS = bool((r.get("variant") or {}).get("guards", False))
                    res = run_case(want, recipe=r["recipe"], freestyle=not nofs)
                    print("REPLAY case", want)
                    print("recorded  fail", r["fail"], "final", r["final"].get("totals"), "tris", r["final"].get("tris"))
                    print("replayed  fail", res["fail"], "final", res["final"].get("totals"), "tris", res["final"].get("tris"))
                    for c in res["calls"]:
                        print("  ", c)
                    return
        raise SystemExit("case not found")
    seed, n = int(_arg("--seed", "0")), int(_arg("--n", "10"))
    if not out:
        raise SystemExit("--out <jsonl> required")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    cur = out + ".cur"
    with open(out, "a", encoding="utf-8") as fo:
        for cid in range(seed, seed + n):
            with open(cur, "w") as fc:
                fc.write(str(cid))
            try:
                res = run_case(cid, freestyle=not nofs)
            except Exception as e:  # noqa: BLE001 -- harness bug, not a helper failure
                res = {"case": cid, "harness_error": f"{type(e).__name__}: {e}"[:300], "tb": traceback.format_exc()[-800:], "fail": ["harness_error"], "soft": []}
            res["topo_sha"] = TOPO_SHA
            fo.write(json.dumps(res, default=fl) + "\n")
            fo.flush()
    try:
        os.remove(cur)
    except OSError:
        pass
    print(f"FUZZ done seeds {seed}..{seed + n - 1} -> {out}")


main()
