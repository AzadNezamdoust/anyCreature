"""r20lib: shared box-model helpers for the r20 batch (no topology magic; every creature owns its PARAMS).

chain(bm, SECS)       one tube of 5-vertex half rings (top seam, upper corner, flank, lower corner, bottom seam)
limb(bm, R, faces, S) extrude a block of chain quads [(ring, strip), ...] through limb sections S
spike(bm, R, i, j, tip)  pull one chain quad out to a point (ears, crest blades)
pieces: pair() mirrors a parts.py part; recolor() sends every slot to a palette colour; sweep() closed tube piece.
"""
import math
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bmkit import *


def _yz_frame(d, front=False):
    d = Vector((0.0, d[0], d[1])).normalized()
    u = Vector((0.0, -d.z, d.y))
    if front:                          # an upright chain: the top seam is the front (-Y) seam
        if u.y > 0:
            u = -u
    elif u.z < -1e-6 or (abs(u.z) < 1e-6 and u.y > 0):
        u = -u
    return d, u


def half_ring(c, d, w, hu, hd, sq=0.78, lift=0.0, u=None, front=False):
    """c=(y, z); d=(dy, dz) chain direction; w half width; hu/hd above/below; sq corner squareness;
    lift moves the flank vertex along u (x hu/hd)."""
    _, uu = _yz_frame(d, front)
    if u is not None:
        uu = Vector((0.0, u[0], u[1])).normalized()
    C = Vector((0.0, c[0], c[1]))
    X = Vector((1, 0, 0))
    return [tuple(C + uu * hu), tuple(C + uu * (0.72 * hu) + X * (sq * w)),
            tuple(C + uu * (lift * (hu if lift > 0 else hd)) + X * w),
            tuple(C - uu * (0.72 * hd) + X * (sq * w)), tuple(C - uu * hd)]


def chain(bm, secs, front=False):
    """secs: dicts c=(y,z), w, hu, hd [, sq, lift, d, u]. Returns rings (lists of 5 BMVerts)."""
    pts = []
    for i, s in enumerate(secs):
        if 'd' in s:
            d = s['d']
        else:
            a = secs[max(i - 1, 0)]['c']; b = secs[min(i + 1, len(secs) - 1)]['c']
            d = (b[0] - a[0], b[1] - a[1])
        pts.append(half_ring(s['c'], d, s['w'], s['hu'], s['hd'], s.get('sq', 0.78), s.get('lift', 0.0), s.get('u'), front))
    R = [ring(bm, p) for p in pts]
    for a, b in zip(R, R[1:]):
        bridge(bm, a, b)
    cap(bm, R[0])
    cap(bm, list(reversed(R[-1])))
    recalc_normals(bm)
    return R


def quad(*vs):
    s = set(vs[0].link_faces)
    for v in vs[1:]:
        s &= set(v.link_faces)
    assert len(s) == 1, 'quad lookup: %d faces' % len(s)
    return s.pop()


def chain_face(R, i, j):
    return quad(R[i][j], R[i][j + 1], R[i + 1][j + 1], R[i + 1][j])


def _section_frame(b):
    b = Vector(b).normalized()
    ref = Vector((1, 0, 0)) if abs(b.x) < 0.7 else Vector((0, 0, 1))
    s = (ref - b * ref.dot(b)).normalized()
    f = b.cross(s).normalized()
    return b, s, f


def _se(t, e):
    return math.copysign(abs(t) ** (2.0 / e), t)


def limb(bm, faces, secs, tip=None, even=False):
    """Extrude `faces` once per section; each new ring keeps its vertices' angular order and is placed on a
    superellipse: dict(c=(x,y,z), w=lateral half, d=fore-aft half [, e=exponent, dir=bone dir]).
    tip: merge the last ring to this point. Returns [[verts of ring k], ...] (ring 0 = the root border)."""
    faces = list(faces)
    border = sorted({v for f in faces for v in f.verts if any(g not in faces for g in v.link_faces)}, key=lambda v: v.index)
    rings = [border]
    for j, sec in enumerate(secs):
        old_c = sum((v.co for v in rings[-1]), Vector()) / len(rings[-1])
        r = extrude(bm, faces)
        wire = [e for e in bm.edges if not e.link_faces]
        if wire:
            bmesh.ops.delete(bm, geom=wire, context='EDGES')
        faces = r['faces']
        nv = [v for v in r['verts'] if v.is_valid]
        c = Vector(sec['c'])
        if 'dir' in sec:
            b = Vector(sec['dir'])
        elif j + 1 < len(secs):
            b = Vector(secs[j + 1]['c']) - old_c
        else:
            b = c - old_c
        b, s, f = _section_frame(b)
        e = sec.get('e', 2.6)
        ang = {v: math.atan2((v.co - old_c).dot(f), (v.co - old_c).dot(s)) for v in nv}
        if even:                       # evenly spaced angles in the same cyclic order (no sliver sides)
            order = sorted(nv, key=lambda v: ang[v])
            n_ = len(order)
            cx = sum(math.cos(ang[v] - 2 * math.pi * i / n_) for i, v in enumerate(order))
            sy = sum(math.sin(ang[v] - 2 * math.pi * i / n_) for i, v in enumerate(order))
            ph = math.atan2(sy, cx)
            ang = {v: ph + 2 * math.pi * i / n_ for i, v in enumerate(order)}
        for v in nv:
            a = ang[v]
            v.co = c + s * (sec['w'] * _se(math.cos(a), e)) + f * (sec['d'] * _se(math.sin(a), e))
            if v.co.x < 0.004:
                v.co.x = 0.004
        rings.append(nv)
    if tip is not None:
        bmesh.ops.pointmerge(bm, verts=rings[-1], merge_co=Vector(tip))
    recalc_normals(bm)
    return rings


def spike(bm, face, tip):
    r = extrude(bm, [face])
    wire = [e for e in bm.edges if not e.link_faces]
    if wire:
        bmesh.ops.delete(bm, geom=wire, context='EDGES')
    bmesh.ops.pointmerge(bm, verts=[v for v in r['verts'] if v.is_valid], merge_co=Vector(tip))


def limb_edge(rings, a):
    """Midpoint of a lengthwise edge between ring a and a+1 (for a stage-2 joint loopcut)."""
    for v in rings[a + 1]:
        for e in v.link_edges:
            o = e.other_vert(v)
            if o in rings[a]:
                return tuple((v.co + o.co) / 2), tuple(o.co)
    raise RuntimeError('no lengthwise edge')


# ---------------------------------------------------------------- pieces
def recolor(ob, mapping, default):
    """Every material slot of a part -> a palette material (by slot name)."""
    me = ob.data
    for i, m in enumerate(me.materials):
        nm = m.name.split('.')[0] if m else ''
        key = mapping.get(nm, default)
        me.materials[i] = bpy.data.materials[key]
    return ob


def mirror_v(v):
    return (-v[0], v[1], v[2])


def pair(fn, base, forward, up, mapping, default, name, **kw):
    L = fn(base, forward=forward, up=up, side=1, name=name + '_L', **kw)
    R = fn(mirror_v(base), forward=mirror_v(forward), up=mirror_v(up), side=-1, name=name + '_R', **kw)
    return [recolor(L, mapping, default), recolor(R, mapping, default)]


def pair_kw(fn, mapping, default, name, pos_key, **kw):
    """Like pair() for parts whose position argument is not the first positional one."""
    p = kw.pop(pos_key)
    f, u = kw.pop('forward'), kw.pop('up')
    L = fn(**{pos_key: p}, forward=f, up=u, side=1, name=name + '_L', **kw)
    R = fn(**{pos_key: mirror_v(p)}, forward=mirror_v(f), up=mirror_v(u), side=-1, name=name + '_R', **kw)
    return [recolor(L, mapping, default), recolor(R, mapping, default)]


def sweep(name, cs, sizes, up=(0, 0, 1), sides=4, key='a', keys=None, mirror=False, point=False, rot=0.0):
    """A closed tube piece: centres cs, sizes [(half w, half h)], section oriented by `up`.
    keys: per-segment palette key list (len(cs)-1) or None -> key. point: last ring merged to a tip."""
    bm = bmesh.new()
    cs = [Vector(c) for c in cs]
    R = []
    for i, c in enumerate(cs):
        d = (cs[min(i + 1, len(cs) - 1)] - cs[max(i - 1, 0)]).normalized()
        u = Vector(up) - d * Vector(up).dot(d)
        if u.length < 1e-6:
            u = Vector((1, 0, 0)) - d * d.x
        u.normalize()
        s = d.cross(u)
        w, h = sizes[i]
        pts = []
        for q in range(sides):
            a = 2 * math.pi * q / sides + math.radians(rot) + (math.pi / sides if sides == 4 else 0)
            pts.append(c + s * (w * math.cos(a)) + u * (h * math.sin(a)))
        R.append([bm.verts.new(p) for p in pts])
    fk = []
    for i, (a, b) in enumerate(zip(R, R[1:])):
        if point and i == len(R) - 2:
            tipv = bm.verts.new(cs[-1])
            for q in range(sides):
                bm.faces.new([a[q], a[(q + 1) % sides], tipv]); fk.append(keys[i] if keys else key)
            for v in b:
                bm.verts.remove(v)
            break
        for q in range(sides):
            bm.faces.new([a[q], a[(q + 1) % sides], b[(q + 1) % sides], b[q]]); fk.append(keys[i] if keys else key)
    bm.faces.new(list(reversed(R[0]))); fk.append(keys[0] if keys else key)
    if not point:
        bm.faces.new(R[-1]); fk.append(keys[-1] if keys else key)
    recalc_normals(bm)
    ob = object_from_bm(name, bm, mirror=mirror)
    if mirror:
        ob.modifiers['mirror'].use_clip = False
    ob['_keys'] = ','.join(fk)
    return ob


def paint_keys(ob, palette):
    keys = ob['_keys'].split(',')
    paint(ob, {k_: palette[k_] for k_ in dict.fromkeys(keys)}, lambda c, n, i: keys[i])
    return ob


def body_tree(body):
    bm = evaluated_bm(body)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def on_skin(tree, p, d, back=0.3):
    """First hit of the ray from p - d*back along d (the skin point), and its normal."""
    d = Vector(d).normalized()
    o = Vector(p) - d * back
    loc, n, _, _ = tree.ray_cast(o, d, 2 * back + 1.0)
    if loc is None:
        loc, n, _, _ = tree.find_nearest(Vector(p))
    return loc, n


def both(d, centre=()):
    out = {}
    for k_, v in d.items():
        if k_.endswith('.L') or k_.endswith('.R') or k_ in centre:
            out[k_] = v
        else:
            out[k_ + '.L'] = v; out[k_ + '.R'] = v
    return out
