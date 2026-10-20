"""boxlib5: shared box-model helpers for the r20 octopus / scorpion / crocodile / tortoise / horse builds.

Same construction as opus/wolf: one chain of half rings (top seam -> bottom seam) bridged into a body,
limbs extruded from 1-3 flank quads and carried through placed sections (rotation-minimising frame from the
root), spikes (ears, horn nubs) pulled out of one quad. Every number lives in the creature's PARAMS block.
"""
import math
import bpy, bmesh
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree
from bmkit import *

SHAPE5 = [(0, 1), (0.72, 0.62), (1, -0.05), (0.72, -0.66), (0, -1)]
SHAPE7 = [(0, 1), (0.55, 0.88), (0.92, 0.45), (1, -0.02), (0.9, -0.48), (0.5, -0.9), (0, -1)]


def hring(c, d, w, ht, hb=None, shape=SHAPE5, sq=None, up=None):
    """Half ring at centre c=(y, z), perpendicular to d=(dy, dz) in the y-z plane. w half width, ht / hb
    half heights above / below. shape: [(across, up)] factors seam -> seam. sq: per-point width factors."""
    hb = ht if hb is None else hb
    dy, dz = d
    L = math.hypot(dy, dz); dy, dz = dy / L, dz / L
    uy, uz = -dz, dy
    if up is not None:
        if uy * up[0] + uz * up[1] < 0:
            uy, uz = -uy, -uz
    elif uz < 0 or (uz == 0 and uy > 0):
        uy, uz = -uy, -uz
    y, z = c
    out = []
    for i, (a, b) in enumerate(shape):
        h = ht if b > 0 else hb
        ww = w * (sq[i] if sq else 1.0)
        out.append((a * ww, y + uy * b * h, z + uz * b * h))
    return out


def quad(*vs):
    s = set(vs[0].link_faces)
    for v in vs[1:]:
        s &= set(v.link_faces)
    assert len(s) == 1, 'quad lookup: %d faces' % len(s)
    return s.pop()


def build_chain(bm, chain):
    R = [ring(bm, pts) for pts in chain]
    for a, b in zip(R, R[1:]):
        bridge(bm, a, b)
    cap(bm, R[0])
    cap(bm, list(reversed(R[-1])))
    recalc_normals(bm)
    return R


def _clean(bm):
    wire = [e for e in bm.edges if not e.link_faces]
    if wire:
        bmesh.ops.delete(bm, geom=wire, context='EDGES')


def _profile(nb, ff, fb):
    """(width factor along u, depth factor along f) per column k."""
    if nb == 1:
        return [(1.0, 1.0), (1.0, -1.0)]
    if nb == 2:
        return [(ff, 1.0), (1.0, 0.0), (fb, -1.0)]
    out = []
    for k in range(nb + 1):
        t = 1 - 2 * k / nb
        out.append((math.sqrt(max(0.0, 1 - 0.55 * t * t)), t))
    return out


def build_limb(bm, R, i0, nb, j, secs, tip=None):
    """Extrude the nb quads between rings i0..i0+nb, ring vertices j / j+1, through sections.
    sec = dict(c=(x,y,z), w=half width along u (the o->i axis at the root), d=half depth along f (front->back),
    ff, fb (corner width factors), rot=deg twist about the bone). tip: point the last ring merges into.
    Returns per section {('o'|'i', k): BMVert}."""
    lab = {}
    for k in range(nb + 1):
        lab[('o', k)] = R[i0 + k][j]
        lab[('i', k)] = R[i0 + k][j + 1]
    faces = [quad(R[i0 + k][j], R[i0 + k][j + 1], R[i0 + k + 1][j + 1], R[i0 + k + 1][j]) for k in range(nb)]
    o = sum((lab[('o', k)].co for k in range(nb + 1)), Vector()) / (nb + 1)
    i_ = sum((lab[('i', k)].co for k in range(nb + 1)), Vector()) / (nb + 1)
    fr = (lab[('o', 0)].co + lab[('i', 0)].co) / 2
    bk = (lab[('o', nb)].co + lab[('i', nb)].co) / 2
    u = (o - i_).normalized()
    f = (fr - bk); f = (f - u * f.dot(u)).normalized()
    prev_c = sum((v.co for v in lab.values()), Vector()) / len(lab)
    b_prev = u.cross(f).normalized()
    if b_prev.dot(Vector(secs[0]['c']) - prev_c) < 0:
        b_prev = -b_prev
    out = []
    for s_i, sec in enumerate(secs):
        pos = {q: v.co.copy() for q, v in lab.items()}
        r = extrude(bm, faces)
        lab = {}
        for v in r['verts']:
            lab[min(pos, key=lambda q_: (pos[q_] - v.co).length)] = v
        faces = r['faces']
        _clean(bm)
        c = Vector(sec['c'])
        nxt = Vector(secs[s_i + 1]['c']) if s_i + 1 < len(secs) else (Vector(tip) if tip else c + (c - prev_c))
        b = (c - prev_c).normalized() + (nxt - c).normalized()
        b = b.normalized() if b.length > 1e-6 else (c - prev_c).normalized()
        if sec.get('dir'):
            b = Vector(sec['dir']).normalized()
        q = b_prev.rotation_difference(b)
        u = q @ u; f = q @ f
        if sec.get('rot'):
            qq = Quaternion(b, math.radians(sec['rot'])); u = qq @ u; f = qq @ f
        b_prev = b
        prof = _profile(nb, sec.get('ff', 0.6), sec.get('fb', 0.5))
        for (row, k), v in lab.items():
            wk, fk = prof[k]
            v.co = c + u * ((1 if row == 'o' else -1) * sec['w'] * wk) + f * (sec['d'] * fk)
        prev_c = c
        out.append(dict(lab))
    if tip:
        r = extrude(bm, faces)
        _clean(bm)
        bmesh.ops.pointmerge(bm, verts=r['verts'], merge_co=Vector(tip))
    return out


def spike(bm, a, b, c, d, tip):
    """Pull one quad (corners a b c d) out to a point (an ear, a nub)."""
    f = quad(a, b, c, d)
    r = extrude(bm, [f])
    _clean(bm)
    bmesh.ops.pointmerge(bm, verts=r['verts'], merge_co=Vector(tip))


def freeze(labs):
    return [{q: v.co.copy() for q, v in lab.items()} for lab in labs]


def limb_loop(bm, labs, a, t, key=('o', 0)):
    """A full loop round a limb between stage-1 sections a and a+1."""
    pa, pb = labs[a][key], labs[a + 1][key]
    return loopcut(bm, edge_near(bm, (pa + pb) / 2), t=t, near=vert_near(bm, pa))


# ---------------------------------------------------------------- pieces
def body_tree(body):
    """BVH of the evaluated (mirrored) body in world space."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    bm = bmesh.new()
    bm.from_mesh(ev.to_mesh())
    bm.transform(body.matrix_world)
    t = BVHTree.FromBMesh(bm)
    ev.to_mesh_clear()
    bm.free()
    return t


def on_skin(tree, p, out_dir):
    """The skin point hit by a ray from p + out_dir * 0.5 back toward p, and its normal."""
    dv = Vector(out_dir).normalized()
    hit = tree.ray_cast(Vector(p) + dv * 0.5, -dv, 2.0)
    if hit[0] is None:
        loc, n = tree.find_nearest(Vector(p))[:2]
        return loc, n
    return hit[0], hit[1]


def cone(bm, base, axis, r, L, sides=4, bury=0.3, bend=None, segs=1, taper=0.55, flat=1.0):
    """A closed faceted cone / claw / spine: root buried bury*L under base along axis; bend: a direction
    the tip curves toward. flat squashes the section along the second axis. Returns the faces."""
    ax = Vector(axis).normalized()
    s1 = ax.orthogonal().normalized(); s2 = ax.cross(s1)
    if bend is not None:
        bd = Vector(bend); bd = (bd - ax * bd.dot(ax)).normalized(); s1 = bd; s2 = ax.cross(s1)
    n = segs + 1
    rings = []
    for s in range(n):
        t = s / n
        c = Vector(base) + ax * (L * (t - bury))
        if bend is not None:
            c += s1 * (L * 0.35 * t * t)
        rr = r * (1 - t * taper)
        rings.append([bm.verts.new(c + (s1 * math.cos(a) * flat + s2 * math.sin(a)) * rr)
                      for a in [2 * math.pi * (q + 0.5) / sides for q in range(sides)]])
    tipc = Vector(base) + ax * (L * (1 - bury)) + (s1 * L * 0.35 if bend is not None else Vector())
    tip = bm.verts.new(tipc)
    fs = [bm.faces.new(list(reversed(rings[0])))]
    for A, B in zip(rings, rings[1:]):
        for q in range(sides):
            fs.append(bm.faces.new([A[q], A[(q + 1) % sides], B[(q + 1) % sides], B[q]]))
    for q in range(sides):
        fs.append(bm.faces.new([rings[-1][q], rings[-1][(q + 1) % sides], tip]))
    return fs


def mk(name, bm, palette, rule, mirror=True):
    recalc_normals(bm)
    ob = object_from_bm(name, bm, mirror=mirror)
    if mirror:
        ob.modifiers['mirror'].use_clip = False
    paint(ob, palette, rule)
    return ob


def eye_pair(tree, p, out_dir, radius, mats, **kw):
    """Two kit eyes (parts.eye_set), seated on the skin at the mirrored points."""
    import parts as P
    loc, n = on_skin(tree, p, out_dir)
    obs = []
    for side in (1, -1):
        c = Vector((loc.x * side, loc.y, loc.z))
        fw = Vector((n.x * side, n.y, n.z))
        obs.append(P.eye_set(tuple(c), radius, forward=tuple(fw), up=(0, 0, 1), side=side,
                             name='eye' + ('L' if side > 0 else 'R'), mats=mats, **kw))
    return obs


def both(d, centre=()):
    out = {}
    for kk, v in d.items():
        if kk.endswith('.L') or kk.endswith('.R') or kk in centre:
            out[kk] = v
        else:
            out[kk + '.L'] = v; out[kk + '.R'] = v
    return out


def tube(bm, pts, radii, sides=6, flat=None, cap0=True, cap1=True, tip=None):
    """A closed faceted tube through pts (world) with per-point radius (or (rx, ry) along the frame's
    side / up). Rotation-minimising frame; flat: per-point y squash. Returns the rings."""
    pts = [Vector(p) for p in pts]
    d0 = (pts[1] - pts[0]).normalized()
    s = d0.orthogonal().normalized()
    if abs(d0.x) < 0.9:
        s = Vector((1, 0, 0)); s = (s - d0 * s.dot(d0)).normalized()
    rings = []
    prev = d0
    for i, p in enumerate(pts):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        s = prev.rotation_difference(d) @ s
        prev = d
        t = d.cross(s)
        r = radii[i]
        rx, ry = (r, r) if not isinstance(r, (tuple, list)) else r
        rings.append([bm.verts.new(p + s * math.cos(a) * rx + t * math.sin(a) * ry)
                      for a in [2 * math.pi * (q + 0.5) / sides for q in range(sides)]])
    for A, B in zip(rings, rings[1:]):
        for q in range(sides):
            bm.faces.new([A[q], A[(q + 1) % sides], B[(q + 1) % sides], B[q]])
    if cap0:
        bm.faces.new(list(reversed(rings[0])))
    if tip is not None:
        tv = bm.verts.new(Vector(tip))
        for q in range(sides):
            bm.faces.new([rings[-1][q], rings[-1][(q + 1) % sides], tv])
    elif cap1:
        bm.faces.new(rings[-1])
    return rings


def crest(bm, base_pts, ups, heights, half_w, bury=0.02):
    """A mirrored-half blade along a seam line (mane, dorsal crest): per station a seam-bottom (buried),
    a side vertex and a seam-top vertex. Build on x >= 0; mirror merges the seam. Returns the faces."""
    rows = []
    for p, n, h, w in zip(base_pts, ups, heights, half_w):
        p, n = Vector(p), Vector(n).normalized()
        rows.append([bm.verts.new(Vector((0.0, *(p - n * bury).yz))),
                     bm.verts.new(p + n * (0.35 * h) + Vector((w, 0, 0))),
                     bm.verts.new(Vector((0.0, *(p + n * h).yz)))])
    fs = []
    for A, B in zip(rows, rows[1:]):
        fs.append(bm.faces.new([A[0], A[1], B[1], B[0]]))
        fs.append(bm.faces.new([A[1], A[2], B[2], B[1]]))
    fs.append(bm.faces.new([rows[0][0], rows[0][2], rows[0][1]]))
    fs.append(bm.faces.new([rows[-1][0], rows[-1][1], rows[-1][2]]))
    return fs
