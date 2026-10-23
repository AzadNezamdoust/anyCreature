"""detail_pieces.py - chunky stage-3 detail pieces for the zoo detail pass (2026-10-23).

Box-model method only: every detail is a SEPARATE seated low-poly piece (geometry steps, no noise):
  band()  a skin fold / ridge / lip line: a keel sunk in the body, a raised asymmetric ridge on top, both ends
          tapered into the skin (or left open on the x = 0 seam so the live mirror joins the halves). The keel
          makes the surface crossing ONE connected loop (techqa 'hit' counts crossing clusters).
  knob()  a wart, brow knob, nostril mound, kneecap, knuckle: a low dome with its base ring sunk.
  fan()   a tail tuft / bristle brush: a flattened tapered slab, root sunk.
  plate() a seated slab following the surface (moss cap, armour plate, sole pad).
Surface samplers cast rays on the body's BVH (the stage-2 half mesh, x >= 0).
"""
import math
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def body_tree(body):
    bm = bmesh.new()
    bm.from_mesh(body.data)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def hit(tree, o, d, far=6.0):
    """First surface hit from o along d; returns (point, outward normal) or None. The normal is the face normal
    turned to face the ray's origin side (outward when casting from outside in; flipped when casting from inside)."""
    d = Vector(d).normalized()
    loc, nrm, _i, _dist = tree.ray_cast(Vector(o), d, far)
    if loc is None:
        return None
    return loc, nrm.normalized()


def cast_in(tree, o, d):
    """Cast from outside (o) along d; normal facing back toward o (outward)."""
    r = hit(tree, o, d)
    if r is None:
        return None
    p, n = r
    if n.dot(Vector(d)) > 0:
        n = -n
    return p, n


def cast_out(tree, c, d):
    """Cast from inside (c) outward along d; the normal faces along d (outward)."""
    r = hit(tree, c, d)
    if r is None:
        return None
    p, n = r
    if n.dot(Vector(d)) < 0:
        n = -n
    return p, n


def _smooth(vs, it=1):
    for _ in range(it):
        vs = [vs[0]] + [((vs[i - 1] + vs[i] * 2 + vs[i + 1]) / 4) for i in range(1, len(vs) - 1)] + [vs[-1]]
    return vs


def stations_from_hits(hits, blend=0.5, side_hint=None):
    """(points, normals) -> stations (p, n, along, across). Normals smoothed along the path; across = n x along,
    turned toward side_hint when given."""
    P = [h[0] for h in hits]
    N = _smooth([h[1] for h in hits], 2)
    N = [n.normalized() for n in N]
    out = []
    for i, p in enumerate(P):
        a = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)])
        a = a.normalized() if a.length > 1e-9 else Vector((0, 0, 1))
        n = N[i]
        x = n.cross(a)
        x = x.normalized() if x.length > 1e-9 else Vector((0, 1, 0))
        if side_hint is not None and x.dot(Vector(side_hint)) < 0:
            x = -x
        out.append((p.copy(), n, a, x))
    return out


# ridge profile across the band (across fraction, height fraction): steep front edge (-), long back slope (+)
FOLD = [(-0.45, 0.45), (-0.30, 1.0), (0.10, 0.85), (0.45, 0.40)]
ROUND = [(-0.45, 0.45), (-0.25, 0.95), (0.25, 0.95), (0.45, 0.45)]
STEP = [(-0.5, 0.12), (-0.15, 0.6), (0.3, 1.0), (0.5, 0.18)]   # a broad blended skin step (judge 10-23: raised ridges read as straps)


def band(bm, st, width, height, sink=None, prof=FOLD, open_start=False, open_end=False, taper=0.45,
         wscale=None, hscale=None):
    """A ridge band over stations st = [(p, n, along, across)]. Each section: a keel sunk `sink` under the
    surface + the profile points raised along n. Ends taper (to `taper` of the size) and close on a sunk tip,
    or stay open on the x = 0 seam (open_start / open_end: those section verts snap to x = 0)."""
    sink = sink if sink is not None else max(0.6 * height, 0.012)
    m = len(st)
    secs = []
    for i, (p, n, a, x) in enumerate(st):
        t = i / max(m - 1, 1)
        f = 1.0
        if not open_start:
            f = min(f, taper + (1 - taper) * min(1.0, t * (m - 1) / 1.5))
        if not open_end:
            f = min(f, taper + (1 - taper) * min(1.0, (1 - t) * (m - 1) / 1.5))
        w = width * f * (wscale[i] if wscale else 1.0)
        h = height * f * (hscale[i] if hscale else 1.0)
        sec = [p - n * (sink * max(f, 0.6))]
        for u, v in prof:
            sec.append(p + x * (u * w) + n * (v * h))
        if (i == 0 and open_start) or (i == m - 1 and open_end):
            sec = [Vector((0.0, q.y, q.z)) for q in sec]
        secs.append([bm.verts.new(q) for q in sec])
    k = len(secs[0])
    for A, B in zip(secs, secs[1:]):
        for j in range(k):
            bm.faces.new([A[j], A[(j + 1) % k], B[(j + 1) % k], B[j]])
    for end, opn, sgn in ((0, open_start, -1), (m - 1, open_end, 1)):
        if opn:
            continue
        p, n, a, x = st[end]
        tip = bm.verts.new(p - n * (0.5 * sink) + a * sgn * 0.22 * width)   # a short blunt end (no needle tris)
        S = secs[end]
        for j in range(k):
            f = [S[j], S[(j + 1) % k], tip]
            bm.faces.new(f if sgn > 0 else list(reversed(f)))
    return bm


def knob(bm, c, n, r, h, sides=6, sink=None, sq=(1.0, 1.0), up=None, top=0.45):
    """A low dome: base ring sunk under c, a shoulder ring, a flat top ring, capped. sq scales the two
    in-surface axes (u along `up` projected, w across)."""
    n = Vector(n).normalized()
    up = Vector(up) if up is not None else Vector((0, 0, 1))
    u = (up - n * up.dot(n))
    if u.length < 1e-6:
        u = n.orthogonal()
    u = u.normalized()
    w = n.cross(u)
    sink = sink if sink is not None else 0.5 * h + 0.004
    c = Vector(c)
    rings = []
    for off, rad in ((-sink, 1.0), (0.55 * h, 0.85), (h, top)):
        rings.append([bm.verts.new(c + n * off + (u * math.cos(t) * sq[0] + w * math.sin(t) * sq[1]) * r * rad)
                      for t in [2 * math.pi * (k_ + 0.5) / sides for k_ in range(sides)]])
    bm.faces.new(list(reversed(rings[0])))
    for A, B in zip(rings, rings[1:]):
        for j in range(sides):
            bm.faces.new([A[j], A[(j + 1) % sides], B[(j + 1) % sides], B[j]])
    bm.faces.new(rings[-1])
    return rings


def fan(bm, root, d, side, length, width, thick, sink=0.02, spread=1.6, tip=0.55, sides=6):
    """A flattened brush (tail tuft, bristle fan): rounded-rectangle sections along d, wide across `side`,
    thin along d x side; root section sunk `sink` back along d."""
    d = Vector(d).normalized()
    s = Vector(side)
    s = (s - d * s.dot(d)).normalized()
    t = d.cross(s).normalized()
    root = Vector(root)
    secs = []
    for f, wf, tf in ((-sink / length, 0.55, 1.0), (0.35, 1.0, 1.0), (0.75, spread * 0.8, 0.8), (1.0, spread * 0.55 * tip / 0.55, 0.45)):
        c = root + d * (f * length)
        ring_ = []
        for k_ in range(sides):
            a = 2 * math.pi * (k_ + 0.5) / sides
            cx, cy = math.cos(a), math.sin(a)
            ex = math.copysign(abs(cx) ** 0.6, cx)
            ey = math.copysign(abs(cy) ** 0.6, cy)
            ring_.append(bm.verts.new(c + s * ex * width * wf / 2 + t * ey * thick * tf / 2))
        secs.append(ring_)
    bm.faces.new(list(reversed(secs[0])))
    for A, B in zip(secs, secs[1:]):
        for j in range(sides):
            bm.faces.new([A[j], A[(j + 1) % sides], B[(j + 1) % sides], B[j]])
    bm.faces.new(secs[-1])
    return secs


def ring_stations(tree, centre, axis, ref, a0, a1, n, tilt=0.0):
    """Stations round a limb or the trunk: rays from `centre` (inside) outward, perpendicular to `axis`, from
    angle a0 to a1 (deg, 0 = along `ref`, positive toward axis x ref); tilt (deg) leans each ray along axis."""
    axis = Vector(axis).normalized()
    ref = Vector(ref)
    ref = (ref - axis * ref.dot(axis)).normalized()
    oth = axis.cross(ref)
    hits = []
    for i in range(n):
        a = math.radians(a0 + (a1 - a0) * i / (n - 1))
        d = ref * math.cos(a) + oth * math.sin(a) + axis * math.tan(math.radians(tilt))
        h = cast_out(tree, Vector(centre), d)
        if h is not None:
            hits.append(h)
    return hits


def path_stations(tree, pts, d):
    """Stations from points projected onto the surface along direction d (cast from outside)."""
    d = Vector(d).normalized()
    hits = []
    for q in pts:
        h = cast_in(tree, Vector(q) - d * 2.0, d)
        if h is not None:
            hits.append(h)
    return hits


def section_centre(tree, y, x=0.002, zlo=-0.5, zhi=6.0):
    """The trunk's mid point at y on the midline: halfway between the top and the bottom surface hits."""
    a = cast_in(tree, (x, y, zhi), (0, 0, -1))
    b = cast_in(tree, (x, y, zlo), (0, 0, 1))
    if a is None or b is None:
        return None
    return Vector((0.0, y, (a[0].z + b[0].z) / 2)), a[0].z, b[0].z
