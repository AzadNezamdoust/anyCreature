import os, sys, math, hashlib
import bpy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'kit'))
sys.path.insert(0, HERE)
from bmkit import *
from carve import carve_base, colour_from_sheet, load_ref
import numpy as np
from masks import KEEP

# setting c1 "carve + detail": the carapace and the claws are carved from reference/ (a visual
# hull of the clipped masks, see masks.py); the eight walking legs are extruded by hand.
META = dict(creature='crab', model='opus', engine_glb='')


def _inside(P, A, Bv):
    P = np.array(P)
    ins = np.zeros(A.shape, bool)
    for i in range(len(P)):
        (a1, b1), (a2, b2) = P[i], P[i - 1]
        c = ((b1 > Bv) != (b2 > Bv)) & (A < (a2 - a1) * (Bv - b1) / (b2 - b1 + 1e-12) + a1)
        ins ^= c
    return ins


def fix_masks(k):
    views = load_ref(k.dir)
    for name, polys in KEEP.items():
        v = views[name]
        H, W = v.mask.shape
        R, C = np.mgrid[0:H, 0:W].astype(np.float64)
        R += v.r0; C += v.c0
        if name == 'side':
            A, Bv = (C - v.cmid) * v.s, (v.ground - R) * v.s
        elif name == 'front':
            A, Bv = np.abs(C - v.axis) * v.s, (v.ground - R) * v.s
        else:
            A, Bv = np.abs(R - v.axis) * v.s, (C - v.cmid) * v.s
        keep = np.zeros((H, W), bool)
        for P in polys:
            keep |= _inside(P, A, Bv)
        m = v.mask & keep
        if name == 'side':
            global LIFT
            LIFT = float(Bv[m].min())        # carve_base puts its lowest point on z = 0
        m[0] = m[-1] = False; m[:, 0] = m[:, -1] = False
        v.mask = m
        I = np.zeros((H + 1, W + 1), np.float64)
        I[1:, 1:] = m.astype(np.float64).cumsum(0).cumsum(1)
        v.I = I


LIFT = 0.0
CARVE = dict(target_tris=(500, 800))


def carve(k):
    key = hashlib.sha256(repr((KEEP, CARVE)).encode()).hexdigest()
    kf, cf = os.path.join(k.dir, 'carve_mask.key'), os.path.join(k.dir, 'carve_base.json')
    if not os.path.exists(kf) or open(kf).read() != key:
        if os.path.exists(cf):
            os.remove(cf)
        open(kf, 'w').write(key)
    fix_masks(k)
    return carve_base(k, **CARVE)


# ---------------------------------------------------------------------------
# hand edits on the carve (stage 1)
# 1. underbody: the hull fills the space under the rim out to the rim (front view claws cover it);
#    a crab's rim overhangs a narrower belly bowl. Below RIM_Z, behind the claw arm, x scales to
#    the bowl read off the front view (half width 0.17 at the belly bottom, 0.29 under the rim).
RIM_Z, BELLY_Z, DISC_W = 0.235, 0.09, 0.315


def bowl(z):
    t = max(0.0, min(1.0, (z - BELLY_Z) / (RIM_Z - BELLY_Z)))
    return 0.17 + 0.12 * t ** 0.6


def squeeze_underbody(bm):
    for v in bm.verts:
        c = v.co
        if c.z >= RIM_Z or c.y < -0.20:
            continue
        w = min(1.0, (c.y + 0.20) / 0.06)               # blend in behind the claw arm root
        s = bowl(c.z) / DISC_W
        c.x *= 1.0 - w * (1.0 - min(1.0, s))


# 1b. carapace dome: the hull's top is the min of the side and front outlines, a flat roof with a
#     vertical front wall. Clamp the carapace top under a dome z = 0.385 - 0.08 r^2 (r: the plan
#     ellipse radius, 1 at the rim), read off the side view (peak 0.385, rim 0.30).
DISC_C, DISC_R = (0.0, 0.045), (0.315, 0.34)


def disc_r(c):
    return math.hypot(c.x / DISC_R[0], (c.y - DISC_C[1]) / DISC_R[1])


def dome(bm):
    moved = []
    for v in bm.verts:
        c = v.co
        if c.z <= RIM_Z or c.y < -0.33:
            continue
        r = disc_r(c)
        if r > 1.08:
            continue
        z0 = c.z
        c.z = min(c.z, max(RIM_Z + 0.02, 0.385 - 0.105 * r * r))
        if z0 - c.z > 1e-4:
            moved.append((round(c.x, 2), round(c.y, 2), round(z0 - c.z, 3)))
    say('CRAB dome moved', len(moved), moved[:20])


# 2. walking legs: the hull cannot carve them (round 1: walls). Four per side, extruded from the
#    underbody, paths read off reference/top.png (plan) and side.png (heights):
#    root, hip, knee a, knee b, second bend, tip ring (the dark-tip border), tip.
LEGS = [
    [(0.235, -0.08, 0.175), (0.315, -0.115, 0.175), (0.385, -0.150, 0.262), (0.415, -0.168, 0.262), (0.49, -0.22, 0.14), (0.515, -0.25, 0.07), (0.535, -0.28, 0.0)],
    [(0.250, 0.06, 0.175), (0.335, 0.065, 0.175), (0.415, 0.060, 0.272), (0.450, 0.062, 0.272), (0.53, 0.08, 0.14), (0.565, 0.095, 0.07), (0.60, 0.11, 0.0)],
    [(0.225, 0.18, 0.175), (0.305, 0.215, 0.175), (0.365, 0.250, 0.272), (0.395, 0.268, 0.272), (0.46, 0.32, 0.14), (0.495, 0.35, 0.07), (0.53, 0.38, 0.0)],
    [(0.165, 0.27, 0.175), (0.225, 0.315, 0.175), (0.250, 0.365, 0.262), (0.278, 0.405, 0.258), (0.31, 0.485, 0.135), (0.322, 0.53, 0.065), (0.33, 0.57, 0.0)],
]
LEG_DIMS = [(0.070, 0.074), (0.064, 0.068), (0.062, 0.066), (0.050, 0.052), (0.038, 0.040), (0.0, 0.0)]


def centre_of(vs):
    return sum((v.co for v in vs), Vector()) / len(vs)


def limb(bm, face, pts, afix):
    """Extrude `face` through pts = [(point, (width, depth)), ...]; each new section is the old
    one re-scaled into a frame perpendicular to the path (k3's limb). (0, 0) = a point."""
    cur, prev, steps = face, None, []
    for i, (p, (w, h)) in enumerate(pts):
        p = Vector(p)
        back = Vector(pts[i - 1][0]) if i else cur.calc_center_median()
        din = (p - back).normalized()
        dout = (Vector(pts[i + 1][0]) - p).normalized() if i + 1 < len(pts) else din
        d = (din + dout).normalized()
        a = Vector(afix)
        b = d.cross(a).normalized()
        a = b.cross(d).normalized()
        pa, pb = prev if prev else (a, b)
        r = extrude(bm, [cur])
        f = r['faces'][0]
        vs = list(f.verts)
        c = centre_of(vs)
        if w == 0:
            bmesh.ops.pointmerge(bm, verts=vs, merge_co=p)
            steps.append((None, r['sides']))
            break
        # a designed section: the ring's verts, in angle order, go onto the corners of a w x h
        # box (n = 4) or an n-gon on its inscribed ellipse; the rotation that moves them least
        ang = [math.atan2((v.co - c).dot(pb), (v.co - c).dot(pa)) for v in vs]
        # keep the face's own cyclic order (CCW about its normal; theta runs CCW about d), so a
        # root quad seen edge-on never maps to a bow-tie
        f.normal_update()
        order = list(range(len(vs))) if f.normal.dot(d) > 0 else list(reversed(range(len(vs))))
        n = len(vs)
        base = [math.pi / 4 + 2 * math.pi * j / n for j in range(n)] if n == 4 else                [2 * math.pi * j / n for j in range(n)]
        def cost(s):
            return sum(abs(math.remainder(ang[order[j]] - base[(j + s) % n], 2 * math.pi)) for j in range(n))
        sh = min(range(n), key=cost)
        rr = math.sqrt(2) if n == 4 else 1.0
        for j in range(n):
            t = base[(j + sh) % n]
            vs[order[j]].co = p + a * math.cos(t) * rr * w / 2 + b * math.sin(t) * rr * h / 2
        prev = (a, b)
        steps.append((f, r['sides']))
        cur = f
    return steps


def root_quad(bm, p, out, pool):
    """The carve face nearest p that faces `out`, joined with its neighbour across its longest
    edge (two triangles -> one quad: a 4-sided leg)."""
    out = Vector(out).normalized()
    cands = [f for f in pool if f.is_valid and f.normal.dot(out) > 0.55]
    f = min(cands, key=lambda f: (f.calc_center_median() - Vector(p)).length)
    e = max(f.edges, key=lambda e: e.calc_length())
    g = [x for x in e.link_faces if x is not f][0]
    assert g in pool
    r = bmesh.ops.dissolve_faces(bm, faces=[f, g])
    q = r['region'][0]
    say('CRAB root', tuple(round(c, 3) for c in p), '->', tuple(round(c, 3) for c in q.calc_center_median()), len(q.verts), len(r['region']))
    q.normal_update()
    return q


def add_legs(bm):
    bm.normal_update()
    pool = set(bm.faces)                                # carve faces only: never a leg's own side
    for P in LEGS:
        root = Vector(P[0])
        rad = Vector((P[-1][0] - P[0][0], P[-1][1] - P[0][1], 0)).normalized()
        f = root_quad(bm, root, rad, pool)
        a = Vector((0, 0, 1)).cross(rad).normalized()       # across the leg plane
        limb(bm, f, list(zip(P[1:], LEG_DIMS)), afix=a)


def stage1(k):
    body = carve(k)
    bm = edit(body)
    # the clipped hull has no feet: its lowest point (the claw) went onto z = 0. Lift it back to
    # the height the side view shows it at.
    say('CRAB lift', round(LIFT, 4))
    for v in bm.verts:
        v.co.z += LIFT
    squeeze_underbody(bm)
    dome(bm)
    front_wall(bm)
    add_legs(bm)
    snap_seam(bm, 1e-6)
    commit(body, bm)
    debug_hits(body)
    debug_slivers(body, 's2')
    debug_slivers(body, 's1')
    return body


# 1c. front wall (team round, STAGE-1 UNLOCK, AD must-fix 1): the carve's wall between the claw arms
#     is a strip of needle triangles whose verts zigzag 2.5 cm in y (stripes at az000). Its six faces
#     are replaced by a 2-row x 3-column grid per half on a shallow arc (bulge 1.5 cm at the seam,
#     radius ~ body half-width); the boundary verts keep their rows and slide onto the arc.
WALL_Y0, WALL_BULGE, WALL_W = -0.279, 0.015, 0.12


def front_wall(bm):
    bm.normal_update()
    faces = [f for f in bm.faces if f.normal.y < -0.4 and
             all(v.co.y < -0.24 and abs(v.co.x) < 0.12 and 0.08 < v.co.z < 0.275 for v in f.verts)]
    vs = {v for f in faces for v in f.verts}
    mid_z = sum(v.co.z for v in vs) / len(vs)
    top = sorted((v for v in vs if v.co.z > mid_z), key=lambda v: v.co.x)
    bot = sorted((v for v in vs if v.co.z <= mid_z), key=lambda v: v.co.x)
    say('CRAB wall faces', len(faces), 'top', [tuple(round(c, 3) for c in v.co) for v in top],
        'bot', [tuple(round(c, 3) for c in v.co) for v in bot])
    assert len(faces) == 6 and len(top) == 4 and len(bot) == 4, (len(faces), len(top), len(bot))
    bmesh.ops.delete(bm, geom=faces, context='FACES_ONLY')
    xs = [0.0, 0.037, 0.074, 0.11]
    arc = lambda x: WALL_Y0 + WALL_BULGE * (x / WALL_W) ** 2
    zt = lambda x: 0.270 - 0.030 * x / 0.11          # the rim lip row (0.270 at the seam)
    zb = lambda x: 0.094 + 0.020 * x / 0.11          # the belly row
    mid = []
    for j, x in enumerate(xs):
        top[j].co = Vector((x, arc(x), zt(x)))
        bot[j].co = Vector((x, arc(x), zb(x)))
        if j == 3:      # the outer edge keeps its face beside the claw: split it (no T-junction)
            e = bm.edges.get((top[j], bot[j]))
            _, m = bmesh.utils.edge_split(e, bot[j], 0.5)
            m.co = (x, arc(x), 0.5 * (zt(x) + zb(x)))
            mid.append(m)
        else:
            mid.append(bm.verts.new((x, arc(x), 0.5 * (zt(x) + zb(x)))))
    for j in range(3):
        for a, b, c, d in ((bot[j], bot[j + 1], mid[j + 1], mid[j]), (mid[j], mid[j + 1], top[j + 1], top[j])):
            f = bm.faces.new((a, b, c, d))
            f.normal_update()
            if f.normal.y > 0:
                f.normal_flip()
    loose = [e for e in bm.edges if not e.link_faces]      # the old diagonals and verticals
    bmesh.ops.delete(bm, geom=loose, context='EDGES')
    bm.normal_update()
    for e in bm.edges:
        if len(e.link_faces) != 2 and not all(abs(v.co.x) < 1e-6 for v in e.verts):
            say('CRAB open edge', [tuple(round(c, 3) for c in v.co) for v in e.verts], len(e.link_faces))


def debug_wall(bm):
    bm.verts.index_update()
    vs = [v for v in bm.verts if v.co.y < -0.10 and abs(v.co.x) < 0.2 and v.co.z < 0.33]
    for v in sorted(vs, key=lambda v: (round(v.co.z, 2), v.co.x)):
        say('CRAB wallv', v.index, tuple(round(c, 3) for c in v.co), [f.index for f in v.link_faces])
    fs = {f for v in vs for f in v.link_faces}
    bm.faces.index_update()
    for f in sorted(fs, key=lambda f: f.index):
        f.normal_update()
        say('CRAB wallf', f.index, [v.index for v in f.verts], tuple(round(c, 2) for c in f.normal))


def debug_slivers(ob, tag):
    import bmkit
    bm = bmkit.evaluated_bm(ob)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    out = []
    for f in bm.faces:
        a, b, c = (v.co for v in f.verts)
        if max((a - b).length, (b - c).length, (c - a).length) < 0.012:
            continue
        angs = [math.degrees((y - x).angle(z - x, 0)) for x, y, z in ((a, b, c), (b, c, a), (c, a, b))]
        if min(angs) < 6.0 and f.calc_center_median().x >= 0:
            out.append(tuple(round(q, 3) for q in f.calc_center_median()))
    say('CRAB slivers', tag, len(out), sorted(out))
    bm.free()


def debug_hits(ob):
    from mathutils.bvhtree import BVHTree
    import bmkit
    bm = bmkit.evaluated_bm(ob)
    bm.faces.ensure_lookup_table()
    t = BVHTree.FromBMesh(bm)
    for i, j in t.overlap(t):
        if i < j and not (set(bm.faces[i].verts) & set(bm.faces[j].verts)):
            say('CRAB hit', tuple(round(c, 3) for c in bm.faces[i].calc_center_median()),
                  tuple(round(c, 3) for c in bm.faces[j].calc_center_median()))
    bm.free()

def body_zone(c):
    """the carapace and belly (not the claw arm, not the legs)"""
    return disc_r(c) < 1.15 and c.y > -0.34 and not (c.x > 0.17 and c.y < -0.12)


BELLY_TOP = 0.175       # team AD must-fix 2: the cream strip's top (was the rim, 0.235)
TIP_TAPER = 0.5
CLAW_TIP_Y = -0.58    # team AD must-fix 4: the dark finger cap = the last ~20% of the fingers (was -0.555)


def belly_box(c):
    """the bowl under the rim only: not the leg roots' side faces (their hip rings sit out past it)"""
    return body_zone(c) and abs(c.x) <= bowl(c.z) + 0.012 and c.z < RIM_Z


# colour borders as planar loops: (point, normal, faces whose verts all satisfy box)
CUTS = {
    'rim underside border: rim band above, red shell below': ((0, 0, RIM_Z), (0, 0, 1), body_zone),
    'belly border (team AD 2): cream only in a low strip under the rim, as on the sheet': ((0, 0, BELLY_TOP), (0, 0, 1), lambda c: belly_box(c)),
    'ridge border: the rim band (dark red) under the dome': ((0, 0, 0.272), (0, 0, 1), lambda c: body_zone(c) and disc_r(c) > 0.72),
    'claw tip border: the dark finger tips': ((0, CLAW_TIP_Y, 0), (0, -1, 0), lambda c: c.y < -0.46 and abs(c.x) > 0.03),
}


def cut(k, bm, co, no, box, reason, dist=1e-5, snap=0.012):
    """bisect the faces in `box` with a plane; verts within `snap` go onto it first (the wolf's
    rule: no sliver strips beside the border)"""
    faces = [f for f in bm.faces if all(box(v.co) for v in f.verts)]
    p, n = Vector(co), Vector(no).normalized()
    for v in {v for f in faces for v in f.verts}:
        d = (v.co - p).dot(n)
        if abs(d) < snap and abs(v.co.x) > 1e-6 or (abs(d) < snap and abs(n.x) < 1e-9):
            v.co -= n * d
    geom = list({v for f in faces for v in f.verts}) + list({e for f in faces for e in f.edges}) + faces
    with k.topo(bm, 'loop', reason):
        bmesh.ops.bisect_plane(bm, geom=geom, dist=dist, plane_co=Vector(co), plane_no=Vector(no).normalized())


EYE = (0.12, -0.275, 0.305)          # the stalk root on the front rim (front view x 0.12-0.13)
SOCKET = []


# team AD 5: legs reach further and arch. Per path point (root, hip, knee a, knee b, bend, tip ring,
# tip): out = along the leg's azimuth, up = +z. Tips stay on z = 0 and go 11 cm out.
LEG_OUT = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.045)     # second pass: the tip only (the tip ring's 1.5 cm cost 3 IoU points)
LEG_UP = (0.0, 0.0, 0.028, 0.028, 0.0, 0.0, 0.0)     # second pass: knees 2.8 cm up (was 1.2), above the rim
# second pass (AD 5 + should-fix taper): each ring's section scales about the leg path:
# the tibia and tarsus taper toward the tip, so the knee reads as a joint and not a constant box
LEG_SC = (1.0, 1.0, 1.0, 1.0, 0.90, 0.87, 1.0)


def leg_rad(P):
    return Vector((P[-1][0] - P[0][0], P[-1][1] - P[0][1], 0)).normalized()


LEG_S = 1.0     # the AD's full move (knees +4/+3, tips +11 cm) cost IoU .69 (r21), 30% of it .85
#                 (r22): a thin leg shifted by its own width loses its overlap. r23: only the tarsus
#                 lengthens (tip +6 cm along the reach) and the knees lift 1.5 cm.


def leg_off(P, i):
    return (leg_rad(P) * LEG_OUT[i] + Vector((0, 0, LEG_UP[i]))) * LEG_S


def leg_path(P):
    """the path as stage 2 leaves it before legs_out: knee b slid 2 cm toward the bend"""
    Q = [Vector(p) for p in P]
    Q[3] = Q[3] + (Q[4] - Q[3]).normalized() * 0.02
    return Q


def legs_out(bm):
    n = 0
    for v in bm.verts:
        if v.co.x < 0.1:
            continue
        best = None
        for P in LEGS:
            Q = leg_path(P)
            for i in range(1, 6):
                a, b = Q[i], Q[i + 1]
                ab = b - a
                t = max(0.0, min(1.0, (v.co - a).dot(ab) / ab.length_squared))
                d = (v.co - (a + ab * t)).length
                if d < 0.065 and (best is None or d < best[0]):
                    best = (d, P, i, t, a + ab * t)
        if best:
            _, P, i, t, ax = best
            sc = LEG_SC[i] * (1 - t) + LEG_SC[i + 1] * t
            v.co = ax + (v.co - ax) * sc + leg_off(P, i) * (1 - t) + leg_off(P, i + 1) * t
            n += 1
    say('CRAB legs_out verts', n)


def stage2(k, body):
    bm = edit(body)
    for reason, (co, no, box) in CUTS.items():
        cut(k, bm, co, no, box, reason)
    # knees: the short knee segment (knee a -> b) folds into needle triangles at the bend; slide
    # each knee-b ring 2 cm on toward the second bend (a longer, straighter knee block)
    for P in LEGS:
        kb, bend, ka = Vector(P[3]), Vector(P[4]), Vector(P[2])
        dirn = (bend - kb).normalized()
        ring_b = sorted(bm.verts, key=lambda v: (v.co - kb).length)[:4]
        say('CRAB knee b ring', [round((v.co - kb).length, 3) for v in ring_b])
        assert len(ring_b) == 4, len(ring_b)
        move(ring_b, tuple(dirn * 0.02))
    legs_out(bm)
    # claw fingers (team AD 4): the gap opens as a wedge toward the tips (the dactyl's verts up, the
    # pollex's down, 0 at the gap root y -0.48, full 1.2 cm at y -0.56), the dactyl's top edge up
    # with it, so the two fingers read apart from the hero and az000
    n_f = 0
    for v in bm.verts:
        c = v.co
        if c.x < 0.10 or c.y > -0.48:
            continue
        t = min(1.0, (-0.48 - c.y) / 0.08)
        if 0.135 <= c.z:
            c.z += 0.012 * t
        elif 0.075 <= c.z < 0.13:
            c.z -= 0.010 * t
        else:
            continue
        n_f += 1
    say('CRAB finger verts moved', n_f)
    # team AD 4, second pass: the fingers end blunt (the dactyl's section on the tip loop is 10 x 5 cm),
    # so the dark cap shows as a big wedge from the front. Each finger's ring on the tip loop shrinks
    # toward its own centre (TIP_TAPER): pointed fingers, a small dark cap.
    for lo, hi, tt in ((0.13, 0.30, TIP_TAPER), (0.0, 0.13, 0.7)):
        ring = [v for v in bm.verts if abs(v.co.y - CLAW_TIP_Y) < 1e-4 and v.co.x > 0.03 and lo <= v.co.z < hi]
        c0 = centre_of(ring)
        for v in ring:
            v.co = c0 + (v.co - c0) * tt
        say('CRAB tip ring', len(ring), tuple(round(q, 3) for q in c0))
    # carapace crown: the seam row on the dome rises into a low keel; the dome planes meet on it
    for v in bm.verts:
        if abs(v.co.x) < 1e-6 and v.co.z > 0.33 and -0.2 < v.co.y < 0.3:
            v.co.z += 0.010
    commit(body, bm)
    debug_hits(body)
    debug_slivers(body, 's2')


BRIEF = {'shell': '#c8502e', 'ridge': '#8e3420', 'belly': '#efc9a0', 'tip': '#2a1c18',
         'eye': '#111111', 'barnacle': '#9a8474'}


def _rgb(h):
    h = h.lstrip('#'); return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def sheet_palette(k, body):
    """the bear's rule: colour_from_sheet's clusters, each brief role taking its nearest sheet
    colour (the sheet's own values) when one is near; the paint itself follows the stage-2 loops"""
    sheet = colour_from_sheet(k, [body], chroma=1.2)
    say(f'CRAB sheet clusters: {sheet}')
    pal = {}
    for role, h in BRIEF.items():
        best = min(sheet.values(), key=lambda s: sum((p - q) ** 2 for p, q in zip(_rgb(s), _rgb(h))))
        d = sum((p - q) ** 2 for p, q in zip(_rgb(best), _rgb(h))) ** 0.5
        pal[role] = best if d < 40 and best not in pal.values() else h
    say(f'CRAB palette: {pal}')
    return pal


def frustum(bm, a, b, ra, rb, n, rot=0.0):
    """closed n-sided frustum (rb = 0: a cone) from point a to point b (k3)"""
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    ref = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
    e1 = d.cross(ref).normalized(); e2 = d.cross(e1).normalized()
    ang = [math.radians(rot) + 2 * math.pi * i / n for i in range(n)]
    ra_ = [bm.verts.new(a + (e1 * math.cos(t) + e2 * math.sin(t)) * ra) for t in ang]
    bm.faces.new(list(reversed(ra_)))
    if rb == 0:
        tip = bm.verts.new(b)
        for i in range(n):
            bm.faces.new([ra_[i], ra_[(i + 1) % n], tip])
        return ra_, None
    rb_ = [bm.verts.new(b + (e1 * math.cos(t) + e2 * math.sin(t)) * rb) for t in ang]
    bridge(bm, ra_, rb_, closed=True)
    return ra_, bm.faces.new(rb_)


def ball(bm, c, r, n):
    """k3's low-poly ball: n-sided equator, rings at +-0.7r and +-0.95r, small caps"""
    c = Vector(c)
    rows = []
    for zf in (-0.95, -0.7, 0.0, 0.7, 0.95):
        rf = math.sqrt(max(0.0, 1 - zf * zf))
        rows.append([bm.verts.new(c + Vector((math.cos(2 * math.pi * (i + 0.5) / n) * r * rf,
                                              math.sin(2 * math.pi * (i + 0.5) / n) * r * rf, zf * r)))
                     for i in range(n)])
    bm.faces.new(list(reversed(rows[0])))
    for a_, b_ in zip(rows, rows[1:]):
        bridge(bm, a_, b_, closed=True)
    bm.faces.new(rows[-1])


def plan_r(c):
    return math.hypot(c.x, c.y - DISC_C[1])


def stage3(k, body):
    from mathutils.bvhtree import BVHTree
    PAL = sheet_palette(k, body)
    me = body.data

    def rule(c, n, i):
        zs = [me.vertices[v].co.z for v in me.polygons[i].vertices]
        q = Vector((abs(c.x), c.y, c.z))
        if min(zs) < 0.003 and plan_r(q) > 0.36:
            return 'tip'                                   # walking-leg tips: the cone below the tip ring
        ys = [me.vertices[v].co.y for v in me.polygons[i].vertices]
        if max(ys) <= CLAW_TIP_Y + 0.002 and q.x > 0.03:
            return 'tip'                                   # finger tips: wholly past the claw-tip loop
        if body_zone(q):
            if max(zs) <= BELLY_TOP + 0.002:
                return 'belly'
            if min(zs) >= RIM_Z - 0.002 and max(zs) <= 0.2745 and disc_r(q) > 0.72:
                return 'ridge'
        return 'shell'
    paint(body, {k_: PAL[k_] for k_ in ('shell', 'ridge', 'belly', 'tip')}, rule)

    ebm = evaluated_bm(body)
    tree = BVHTree.FromBMesh(ebm)

    def hit(o, d):
        loc, nrm, _, _ = tree.ray_cast(Vector(o), Vector(d).normalized())
        return loc, nrm

    pieces = []
    # ---- eye stalks on the front rim, black bulb eyes (front view: x 0.13, ball centre z 0.385)
    bm = bmesh.new()
    root, rn = hit((0.122, -0.240, 0.6), (0, 0, -1))
    say('CRAB eye root', tuple(round(c, 3) for c in root))
    # team AD 3: a short stalk (~2 cm above the rim, 40% of before) socketed 1 cm into the rim,
    # +30% wide; the ball +25% sits about one radius above the rim, as on the sheet
    top = root + Vector((0.004, -0.012, 0.020))
    frustum(bm, root - Vector((0, 0, 0.022)), top, 0.022, 0.017, 6)     # second pass: socket 2.2 cm deep (the base cap crossed the skin in a pose)
    ball(bm, top + Vector((0, -0.003, 0.015)), 0.0325, 10)
    eye = object_from_bm('eyes', bm)
    zt = top.z
    paint(eye, {'shell': PAL['shell'], 'eye': PAL['eye']}, lambda c, n, i: 'eye' if c.z > zt - 0.006 else 'shell')
    pieces.append(eye)

    # ---- toothed front rim: blunt pyramids round the front half of the rim band, pointing out
    #      and a little down; skipped beside the eye stalk and over the claw arm
    bm = bmesh.new()
    zz = Vector((0, 0, 1))
    n_t = 0
    rim = [v.co.copy() for v in ebm.verts if v.co.x > -1e-6 and 0.22 < v.co.z < 0.33 and v.co.y > -0.36 and plan_r(v.co) < 0.37]
    for deg, bw in ((5, 0.036), (33, 0.046), (45, 0.050), (57, 0.050), (69, 0.046), (81, 0.040), (93, 0.034)):
        a_ = math.radians(deg)
        o = Vector((math.sin(a_), -math.cos(a_), 0))
        # the rim edge in this direction: the outermost rim-band vertex within +-7 deg
        near = [p for p in rim if Vector((p.x, p.y - DISC_C[1], 0)).normalized().dot(o) > math.cos(math.radians(7))]
        if not near:
            say('CRAB tooth skipped', deg)
            continue
        e = max(near, key=lambda p: Vector((p.x, p.y - DISC_C[1], 0)).dot(o))
        loc = Vector((0, DISC_C[1], 0)) + o * Vector((e.x, e.y - DISC_C[1], 0)).dot(o)
        loc.z = min(max(e.z, RIM_Z + 0.012), 0.285)
        tg = zz.cross(o).normalized()
        h, bd = 0.75 * bw, 0.7 * bw
        bc = loc - o * 0.4 * h
        vs = [bm.verts.new(bc + tg * sx * bw / 2 + zz * sz)
              for sx, sz in ((-1, -0.55 * bd), (1, -0.55 * bd), (1, 0.45 * bd), (-1, 0.45 * bd))]
        tip = bm.verts.new(bc + (o * math.cos(math.radians(12)) - zz * math.sin(math.radians(12))) * h)
        bm.faces.new(vs)
        for j in range(4):
            bm.faces.new([vs[(j + 1) % 4], vs[j], tip])
        n_t += 1
    say('CRAB teeth per side', n_t)
    teeth = object_from_bm('rim_teeth', bm)
    paint(teeth, {'shell': PAL['shell']}, lambda c, n, i: 'shell')
    pieces.append(teeth)

    # ---- barnacle cluster on the rear slope (k3's cones with a crater, off-centre like the sheet)
    bm = bmesh.new()
    craters = []
    for x, z, r in ((0.004, 0.300, 0.028), (0.050, 0.292, 0.021), (-0.042, 0.298, 0.023),
                    (0.022, 0.326, 0.017), (-0.018, 0.276, 0.017)):
        loc, nrm = hit((x, 0.9, z + 0.57), (0, -0.6, -0.57))
        if loc is None:
            continue
        h = 1.1 * r
        sink = 0.45 if r < 0.018 else 0.3
        _, topf = frustum(bm, loc - nrm * sink * h, loc + nrm * (1 - sink) * h, r, r * 0.6, 8, rot=x * 900)
        craters.append((loc + nrm * (1 - sink) * h, r))
        inset(bm, [topf], 0.4, -h * 0.3)
    bar = object_from_bm('barnacles', bm, mirror=False)
    paint(bar, {'barnacle': PAL['barnacle'], 'tip': PAL['tip']},
          lambda c, n, i: 'tip' if any((c - p).length < 0.4 * r_ for p, r_ in craters) else 'barnacle')
    pieces.append(bar)
    ebm.free()
    return pieces


# ---------------------------------------------------------------------------
# skeleton: the leg paths the legs were extruded on, the claw read off the carved base
J = dict(body_a=(0.0, 0.16, 0.22), body_b=(0.0, -0.16, 0.22))
for _i, _P in enumerate(LEGS):
    _O = [tuple(Vector(_P[j]) + leg_off(_P, j)) for j in range(7)]      # the stage-2 leg moves
    J[f'l{_i}_root'], J[f'l{_i}_hip'], J[f'l{_i}_knee'] = _O[0], _O[1], _O[2]
    J[f'l{_i}_bend'], J[f'l{_i}_tip'] = _O[4], _O[6]
J.update(c_root=(0.22, -0.12, 0.205), c_elbow=(0.30, -0.22, 0.21), c_wrist=(0.33, -0.32, 0.20),
         c_palm=(0.27, -0.50, 0.15), c_ftip=(0.24, -0.59, 0.10),
         c_droot=(0.27, -0.45, 0.22), c_dtip=(0.14, -0.615, 0.17))
U = Vector((J['c_palm'][0] - J['c_wrist'][0], J['c_palm'][1] - J['c_wrist'][1], 0)).normalized()


def set_rolls(rig):
    """k3: local Z = the limb plane's normal (Z x the limb's horizontal reach), so +Z rotation
    swings every limb tip DOWN on both sides"""
    Zv = Vector((0, 0, 1))
    bpy.context.view_layer.objects.active = rig
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode='EDIT')
        for eb in rig.data.edit_bones:
            sx = -1 if eb.name.endswith('.R') else 1
            if eb.name == 'body':
                eb.align_roll(Zv)
                continue
            if eb.name.startswith('leg'):
                i = int(eb.name[3])
                r = Vector(J[f'l{i}_tip']) - Vector(J[f'l{i}_root'])
                r = Vector((r.x * sx, r.y, 0))
            elif 'dactyl' in eb.name or 'pollex' in eb.name:
                r = Vector((U.x * sx, U.y, 0))
            else:
                r = eb.tail - eb.head
                r = Vector((r.x, r.y, 0))
            eb.align_roll(Zv.cross(r.normalized()))
        bpy.ops.object.mode_set(mode='OBJECT')


def M(rot):           # the .R twin of a bone-local rotation: yaw (X) and twist (Y) flip
    return (-rot[0], -rot[1], rot[2])


def K(**kw):
    out = {}
    for nm, rot in kw.items():
        out[nm + '.L'] = rot
        out[nm + '.R'] = M(rot)
    return out


def stage4(k, body, pieces):
    bones = [('body', J['body_a'], J['body_b'], None)]
    for i in range(4):
        q = lambda n_, i=i: J[f'l{i}_{n_}']
        bones += [(f'leg{i}_coxa.L', q('root'), q('hip'), 'body'),
                  (f'leg{i}_femur.L', q('hip'), q('knee'), f'leg{i}_coxa.L', True),
                  (f'leg{i}_tibia.L', q('knee'), q('bend'), f'leg{i}_femur.L', True),
                  (f'leg{i}_tarsus.L', q('bend'), q('tip'), f'leg{i}_tibia.L', True)]
    bones += [('claw_arm.L', J['c_root'], J['c_elbow'], 'body'),
              ('claw_wrist.L', J['c_elbow'], J['c_wrist'], 'claw_arm.L', True),
              ('claw_palm.L', J['c_wrist'], J['c_palm'], 'claw_wrist.L', True),
              ('claw_pollex.L', J['c_palm'], J['c_ftip'], 'claw_palm.L', True),
              ('claw_dactyl.L', J['c_droot'], J['c_dtip'], 'claw_palm.L')]
    rig = armature(bones)
    set_rolls(rig)
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
    # idle: two claw clicks, a slow breath
    clip(rig, 'idle', {1: K(claw_dactyl=(0, 0, 0), claw_arm=(0, 0, 0)),
                       8: K(claw_dactyl=(0, 0, -30), claw_arm=(0, 0, -2)),
                       12: K(claw_dactyl=(0, 0, 2), claw_arm=(0, 0, -3)),
                       20: K(claw_dactyl=(0, 0, -30), claw_arm=(0, 0, -4)),
                       24: K(claw_dactyl=(0, 0, 2), claw_arm=(0, 0, -4)),
                       36: K(claw_dactyl=(0, 0, 0), claw_arm=(0, 0, -2)),
                       48: K(claw_dactyl=(0, 0, 0), claw_arm=(0, 0, 0))},
         loc={1: {'body': (0, 0, 0)}, 24: {'body': (0, 0, 0.006)}, 48: {'body': (0, 0, 0)}})
    # move: sideways scuttle, alternating leg sets (A: L0 L2 R1 R3; B: the others)
    A = {('leg0', 'L'), ('leg2', 'L'), ('leg1', 'R'), ('leg3', 'R')}
    lift = dict(coxa=(0, 0, -12), tibia=(0, 0, -7))
    push = dict(coxa=(0, 0, 3), tibia=(0, 0, 4))

    def legs(pa, pb):
        out = {}
        for i in range(4):
            for sd in 'LR':
                ph = pa if (f'leg{i}', sd) in A else pb
                for seg in ('coxa', 'tibia'):
                    r = ph.get(seg, (0, 0, 0))
                    out[f'leg{i}_{seg}.{sd}'] = r if sd == 'L' else M(r)
        out.update(K(claw_arm=(0, 0, -4)))
        return out
    clip(rig, 'move', {1: legs({}, {}), 7: legs(lift, push), 13: legs({}, {}), 19: legs(push, lift), 25: legs({}, {})},
         loc={1: {'body': (0, 0, 0)}, 7: {'body': (-0.014, 0, 0.008)}, 13: {'body': (0, 0, 0)},
              19: {'body': (0.014, 0, 0.008)}, 25: {'body': (0, 0, 0)}})
    # attack: claws rise and open, lunge, snap shut, recover
    clip(rig, 'attack', {1: K(claw_arm=(0, 0, 0), claw_wrist=(0, 0, 0), claw_dactyl=(0, 0, 0)),
                         8: K(claw_arm=(0, 0, -14), claw_wrist=(0, 0, -6), claw_dactyl=(0, 0, -22)),
                         14: K(claw_arm=(0, 0, 4), claw_wrist=(0, 0, 4), claw_dactyl=(0, 0, -22)),
                         16: K(claw_arm=(0, 0, 5), claw_wrist=(0, 0, 4), claw_dactyl=(0, 0, 2)),
                         24: K(claw_arm=(0, 0, 2), claw_wrist=(0, 0, 2), claw_dactyl=(0, 0, 1)),
                         32: K(claw_arm=(0, 0, 0), claw_wrist=(0, 0, 0), claw_dactyl=(0, 0, 0))},
         loc={1: {'body': (0, 0, 0)}, 8: {'body': (0, -0.02, 0.01)}, 14: {'body': (0, 0.03, 0)},
              24: {'body': (0, 0.01, 0)}, 32: {'body': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
