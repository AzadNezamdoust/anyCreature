import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *

META = dict(creature='crab', model='opus')

# ---------------------------------------------------------------- carapace plan
# stations along Y (head at -Y); sections alternate leg socket / spacer
YS = [-0.185, -0.14, -0.10, -0.065, -0.04, -0.005, 0.02, 0.055, 0.08, 0.115, 0.14, 0.18, 0.235]
WS = [0.12, 0.175, 0.212, 0.23, 0.237, 0.24, 0.24, 0.236, 0.228, 0.212, 0.19, 0.15, 0.07]    # rim half-width
ZT = [0.315, 0.34, 0.355, 0.362, 0.366, 0.368, 0.368, 0.366, 0.362, 0.352, 0.34, 0.322, 0.28]  # top seam
ZB = [0.19, 0.165, 0.155, 0.15, 0.148, 0.147, 0.147, 0.148, 0.15, 0.155, 0.16, 0.175, 0.195]    # belly seam
CLAW_SEC, LEG_SEC = 0, (2, 4, 6, 8)
R_SHELL, R_RIDGE, R_BELLY, R_LEG, R_TIP = 0, 1, 2, 3, 4


def zr(y):
    return 0.30 - (y - YS[0]) / (YS[-1] - YS[0]) * 0.045


def section(i):
    """Half ring (x >= 0) from the top seam to the belly seam: shell plane, rim, ridge, socket band, belly."""
    y, w, zt, zb = YS[i], WS[i], ZT[i], ZB[i]
    r = zr(y)
    return [(0.0, y, zt), (0.55 * w, y, zt - 0.012), (w, y, r), (0.86 * w, y, r - 0.022),
            (0.66 * w, y, zb + 0.035), (0.0, y, zb)]


def socket_centre(s):
    a, b = section(s), section(s + 1)
    return Vector(tuple(sum(c) / 4 for c in zip(a[3], a[4], b[3], b[4])))


# ---------------------------------------------------------------- limb paths
LEG_TH = (-12.0, 14.0, 40.0, 64.0)        # plan angle from +X (negative = forward)
LEG_L = (1.0, 1.08, 1.1, 1.1)


def leg_path(i):
    S = socket_centre(LEG_SEC[i])
    th = math.radians(LEG_TH[i]); L = LEG_L[i]
    dh = Vector((math.cos(th), math.sin(th), 0.0))
    at = lambda r, z: Vector((S.x + dh.x * r, S.y + dh.y * r, z))
    #         centre                         half-height  half-width
    return S, dh, [(Vector((S.x + 0.03, S.y + dh.y * 0.01, S.z - 0.004)), 0.027, 0.019),  # coxa: out along the socket normal first
                   (at(0.118 * L, 0.25), 0.021, 0.016),         # knee
                   (at(0.168 * L, 0.10), 0.016, 0.013),         # second bend (dark tip starts)
                   (at(0.18 * L, 0.004), 0.004, 0.004)]         # tip


def claw_path():
    S = socket_centre(CLAW_SEC)
    return S, [(Vector((0.15, -0.185, 0.212)), 0.026, 0.022),   # coxa
               (Vector((0.232, -0.205, 0.2)), 0.030, 0.024),     # elbow
               (Vector((0.25, -0.235, 0.19)), 0.025, 0.021),     # wrist
               (Vector((0.24, -0.255, 0.178)), 0.046, 0.034),    # palm heel
               (Vector((0.18, -0.31, 0.158)), 0.050, 0.036),     # palm end
               (Vector((0.14, -0.332, 0.128)), 0.016, 0.016),    # fixed finger
               (Vector((0.105, -0.34, 0.118)), 0.004, 0.004)]    # finger tip


def _joints():
    J = dict(body=(0.0, 0.0, 0.26))
    for i in range(4):
        S, dh, P = leg_path(i)
        J[f'leg{i}_hip'] = tuple(S)
        J[f'leg{i}_knee'], J[f'leg{i}_bend'], J[f'leg{i}_tip'] = (tuple(P[k][0]) for k in (1, 2, 3))
    S, P = claw_path()
    J['claw_hip'] = tuple(S)
    J['claw_elbow'], J['claw_wrist'], J['claw_heel'], J['claw_end'], J['claw_tip'] = \
        (tuple(P[k][0]) for k in (1, 2, 3, 4, 6))
    J['dactyl'] = (0.19, -0.302, 0.188)
    J['dactyl_tip'] = (0.11, -0.345, 0.165)
    return J


Z = Vector((0, 0, 1))


def palm_frame():
    """The palm-end ring frame exactly as tube() built it, and the knuckle point on its upper half."""
    S, P = claw_path()
    E = P[4][0]
    D = ((E - P[3][0]).normalized() + (P[5][0] - E).normalized()).normalized()
    Sv = Vector((D.x, D.y, 0)).normalized().cross(Z).normalized()
    Up = Sv.cross(D).normalized()
    # the palm-end ring was extruded into the fixed finger, so ahead of it the surface tapers down at ~45 deg:
    # the knuckle sits at the ring's top edge and the finger starts above that taper
    H = E + Up * 0.05
    F0 = H + D * 0.006 + Up * 0.012
    F1 = F0 + D * 0.034 + Up * 0.004
    F2 = F1 + D * 0.03 - Up * 0.016
    return E, D, Up, Sv, H, (F0, F1, F2)


J = _joints()
_E, _D, _U, _S, _H, _F = palm_frame()
J['dactyl'], J['dactyl_tip'] = tuple(_H), tuple(_F[2])


def _frame(D, dh):
    D = D.normalized()
    Sv = dh.cross(Z).normalized()
    Up = Sv.cross(D).normalized()
    return Up, Sv


def tube(bm, face, start, path, dh=None, region=None, tip_from=None, reg=None):
    """Extrude `face` along path [(centre, h, w), ...]. dh: fixed horizontal leg
    direction (else the horizontal part of each ring's direction)."""
    pts = [start] + [p[0] for p in path]
    f = face
    prevC = face.calc_center_median()
    prevUp = prevSv = None
    for k, (P, h, w) in enumerate(path):
        a = (pts[k + 1] - pts[k]).normalized()
        b = (pts[k + 2] - pts[k + 1]).normalized() if k + 2 < len(pts) else a
        D = (a + b).normalized()
        dhk = dh if dh is not None else Vector((D.x, D.y, 0.0)).normalized()
        Up, Sv = _frame(D, dhk)
        r = extrude(bm, [f])
        f = r['faces'][0]
        for v in f.verts:
            o = v.co - prevC
            if prevUp is None:
                sa, sb = (1 if o.z > 0 else -1), (1 if -o.y > 0 else -1)
            else:
                sa, sb = (1 if o.dot(prevUp) > 0 else -1), (1 if o.dot(prevSv) > 0 else -1)
            v.co = P + Up * (sa * h) + Sv * (sb * w)
        rg = R_TIP if (tip_from is not None and k >= tip_from) else R_LEG
        for g in r['sides'] + [f]:
            g[reg] = rg
        prevC, prevUp, prevSv = P, Up, Sv
    return f


def stage1(k):
    bm = bmesh.new()
    reg = bm.faces.layers.int.new('region')
    rows = [ring(bm, section(i)) for i in range(len(YS))]
    secs = []
    for i in range(len(YS) - 1):
        fs = bridge(bm, rows[i], rows[i + 1])
        for j, f in enumerate(fs):
            f[reg] = (R_SHELL, R_SHELL, R_RIDGE, R_BELLY, R_BELLY)[j]
        secs.append(fs)
    # front and rear plates: a seam vertex at the under-rim level splits shell from belly
    for i in (0, len(YS) - 1):
        r_ = rows[i]
        m = bm.verts.new((0.0, YS[i], r_[3].co.z))
        A = bm.faces.new([r_[0], r_[1], r_[2], r_[3], m])
        B = bm.faces.new([m, r_[3], r_[4], r_[5]])
        A[reg], B[reg] = R_SHELL, R_BELLY
    recalc_normals(bm)
    # eight walking legs out of the socket band, two bends each
    for i, s in enumerate(LEG_SEC):
        S, dh, P = leg_path(i)
        tube(bm, secs[s][3], S, P, dh=dh, tip_from=3, reg=reg)
    # the cheliped: arm, wrist, big palm, the fixed finger (the movable one is a stage-3 piece)
    S, P = claw_path()
    tube(bm, secs[CLAW_SEC][3], S, P, tip_from=6, reg=reg)
    return object_from_bm('body', bm)


def along(bm, A, B):
    """The edge running from near A to near B, and its vertex on A's side."""
    A, B = Vector(A), Vector(B)
    best = None
    for e in bm.edges:
        a, b = e.verts
        for x, y in ((a, b), (b, a)):
            sc = (x.co - A).length + (y.co - B).length
            if best is None or sc < best[0]:
                best = (sc, e, x)
    return best[1], best[2]


# hexagonal plan: straight front-lateral margin to the corner at station 3, straight posterolateral margin from station 8
W2 = [0.12, 0.163, 0.201, 0.235, 0.238, 0.24, 0.24, 0.237, 0.232, 0.195, 0.169, 0.128, 0.07]
PLANES = [(0, 1, 2), (3, 4, 5, 6, 7, 8), (9, 10, 11, 12)]      # front plate, central plate, rear plate


def stage2(k, body):
    bm = edit(body)
    # rim rows and top rows by their stage-1 positions (before anything moves)
    rows = []
    for i in range(len(YS)):
        sec = section(i)
        rows.append([vert_near(bm, p) for p in sec[:4]])
    # joints: loops that let the knees and the claw bend
    for i in range(4):
        S, dh, P = leg_path(i)
        with k.topo(bm, 'loop', f'leg {i}: loop on the thigh side of the knee (the bend)'):
            e, nv = along(bm, P[0][0], P[1][0]); loopcut(bm, e, t=0.78, near=nv)
        with k.topo(bm, 'loop', f'leg {i}: loop on the shin side of the knee (the bend)'):
            e, nv = along(bm, P[1][0], P[2][0]); loopcut(bm, e, t=0.2, near=nv)
    S, P = claw_path()
    with k.topo(bm, 'loop', 'claw: elbow loop (the arm raise bends here)'):
        e, nv = along(bm, P[0][0], P[1][0]); loopcut(bm, e, t=0.75, near=nv)
    with k.topo(bm, 'loop', 'claw: mid-palm loop (swell the palm)'):
        e, nv = along(bm, P[3][0], P[4][0]); palm = loopcut(bm, e, t=0.5, near=nv)
    scale(palm, 1.14)
    # blunt the needle tips a little: a 0.008 tip over a 0.1 shin makes 4-degree slivers
    tips = [leg_path(i)[2][3][0] for i in range(4)] + [P[6][0]]
    for t in tips:
        tv = [v for v in bm.verts if (v.co - t).length < 0.012]
        scale(tv, 1.9, pivot=t)
    # carapace: hexagonal plan and three flat plates on top
    for i in range(1, len(YS) - 1):
        dx = W2[i] - WS[i]
        rows[i][2].co.x += dx
        rows[i][3].co.x += 0.86 * dx
        rows[i][1].co.x += 0.55 * dx
    for grp in PLANES:
        flatten([rows[i][j] for i in grp for j in (0, 1)])
    # eye orbits on the front plate, and a recessed mouth plate under the front rim
    with k.topo(bm, 'inset', 'eye orbit: the stalk sits in a socket on the front plate'):
        f = face_near(bm, (0.035, -0.163, 0.315), n=(0, 0, 1))
        inset(bm, [f], 0.35, -0.006)
    with k.topo(bm, 'inset', 'mouth plate: a recessed frame under the front rim'):
        f = face_near(bm, (0.05, -0.185, 0.24), n=(0, -1, 0))
        inset(bm, [f], 0.28, -0.008)
    commit(body, bm)


from mathutils import Quaternion
from mathutils.bvhtree import BVHTree as _BVH

PAL = {'shell': '#c8502e', 'ridge': '#8e3420', 'belly': '#efc9a0', 'tip': '#2a1c18',
       'eye': '#111111', 'barnacle': '#9a8474'}


def prism(bm, path, dh=None, n=4):
    """A closed low-poly tube through [(centre, h, w), ...] (4 or 6 sides), capped both ends."""
    pts = [Vector(p[0]) for p in path]
    rings = []
    for k_, (P, h, w) in enumerate(path):
        a = (pts[min(k_ + 1, len(pts) - 1)] - pts[max(k_ - 1, 0)]).normalized()
        d = dh if dh is not None else Vector((a.x, a.y, 0)).normalized()
        Up, Sv = _frame(a, d)
        ang = [math.radians(45 + 90 * j) for j in range(4)] if n == 4 else [math.radians(60 * j) for j in range(6)]
        rings.append(ring(bm, [Vector(P) + Up * (h * math.sin(t)) * (1.41 if n == 4 else 1) +
                               Sv * (w * math.cos(t)) * (1.41 if n == 4 else 1) for t in ang]))
    for r0, r1 in zip(rings, rings[1:]):
        bridge(bm, r0, r1, closed=True)
    cap(bm, rings[0]); cap(bm, list(reversed(rings[-1])))
    return bm


def gem(bm, c, r, rz, n=6):
    c = Vector(c)
    eq = ring(bm, [c + Vector((r * math.cos(2 * math.pi * j / n), r * math.sin(2 * math.pi * j / n), 0)) for j in range(n)])
    top, bot = bm.verts.new(c + Vector((0, 0, rz))), bm.verts.new(c - Vector((0, 0, rz)))
    for j in range(n):
        bm.faces.new([eq[j], eq[(j + 1) % n], top]); bm.faces.new([eq[(j + 1) % n], eq[j], bot])


def egg(bm, c, r, rz, n=7):
    """A chunky faceted bulb: three latitude rings, a flat top facet, a point below."""
    c = Vector(c)
    rows = []
    for zf, rf, tw in ((-0.55, 0.72, 0.0), (0.15, 1.0, 0.5), (0.7, 0.62, 0.0)):
        rows.append(ring(bm, [c + Vector((r * rf * math.cos(2 * math.pi * (j + tw) / n),
                                          r * rf * math.sin(2 * math.pi * (j + tw) / n), rz * zf)) for j in range(n)]))
    for a_, b_ in zip(rows, rows[1:]):
        for j in range(n):
            bm.faces.new([a_[j], a_[(j + 1) % n], b_[(j + 1) % n]]) if a_ is rows[0] else None
            bm.faces.new([a_[j], b_[(j + 1) % n], b_[j]]) if a_ is rows[0] else None
            if a_ is not rows[0]:
                bm.faces.new([a_[j], a_[(j + 1) % n], b_[j]]); bm.faces.new([a_[(j + 1) % n], b_[(j + 1) % n], b_[j]])
    bot = bm.verts.new(c - Vector((0, 0, rz)))
    for j in range(n):
        bm.faces.new([rows[0][(j + 1) % n], rows[0][j], bot])
    bm.faces.new(rows[2])


def tet(bm, p, out, along_, size, length):
    p, out, along_ = Vector(p), Vector(out).normalized(), Vector(along_).normalized()
    b = p - out * 0.008
    vs = ring(bm, [b + along_ * size, b - along_ * size, b + Vector((0, 0, size * 0.9)), p + out * length - Vector((0, 0, 0.004))])
    for f in ((0, 1, 3), (1, 2, 3), (2, 0, 3), (0, 2, 1)):
        bm.faces.new([vs[i] for i in f])


def dactyl_bm(sx):
    """Movable finger on a knuckle pin: the pin is seated half in the palm-end face on the
    hinge axis; the finger sits just outside the face, held by the pin (it never touches the skin)."""
    E, D, Up, Sv, H, (F0, F1, F2) = palm_frame()
    bm = bmesh.new()
    prism(bm, [(H - Sv * 0.018, 0.014, 0.014), (H + Sv * 0.018, 0.014, 0.014)], n=6)
    prism(bm, [(F0, 0.009, 0.009), (F1, 0.014, 0.012), (F2, 0.006, 0.006)])
    if sx < 0:
        for v in bm.verts:
            v.co.x = -v.co.x
    return bm


def stage3(k, body):
    ra = body.data.attributes['region'].data

    def rule(c, n, i):
        r = ra[i].value
        if c.y < -0.17 and c.z < 0.275 and n.y < -0.5 and c.x < 0.11:
            return 'belly'
        return ('shell', 'ridge', 'belly', 'shell', 'tip')[r]
    paint(body, PAL, rule)
    ebm = evaluated_bm(body)
    tree = _BVH.FromBMesh(ebm)
    zs = lambda x, y: tree.ray_cast(Vector((x, y, 1.0)), Vector((0, 0, -1)))[0].z
    pieces = []
    # eye stalks in the orbits, bulb eyes on top
    zb = zs(0.036, -0.163)
    st = object_from_bm('stalk', prism(bmesh.new(), [((0.036, -0.163, zb - 0.012), 0.01, 0.01),
                                                     ((0.042, -0.172, zb + 0.03), 0.008, 0.008),
                                                     ((0.047, -0.182, zb + 0.066), 0.008, 0.008)], dh=Vector((1, 0, 0))))
    paint(st, {'shell': PAL['shell']}, lambda c, n, i: 'shell')
    eb = bmesh.new(); egg(eb, (0.048, -0.184, zb + 0.075), 0.019, 0.022)
    ey = object_from_bm('eye', eb)
    paint(ey, {'eye': PAL['eye']}, lambda c, n, i: 'eye')
    # toothed front-lateral margin
    tb = bmesh.new()
    rim = [(WS2, y, zr(y)) for WS2, y in zip([0.12, 0.163, 0.201, 0.235], YS[:4])]
    for a_, b_ in zip(rim, rim[1:]):
        A, B = Vector(a_), Vector(b_)
        t = (B - A).normalized(); o = Vector((-t.y, t.x, 0)).normalized()
        o = o if o.x > 0 else -o
        for f_, L in ((0.33, 0.02), (0.72, 0.024)):
            tet(tb, A.lerp(B, f_), o, t, 0.011, L)
    tet(tb, Vector(rim[3]) + Vector((0.004, 0.004, 0)), (1, -0.25, 0), (0.25, 1, 0), 0.012, 0.03)   # the corner spine
    tet(tb, (0.095, -0.185, zr(-0.185)), (0.1, -1, 0), (1, 0, 0), 0.011, 0.018)
    th = object_from_bm('teeth', tb)
    paint(th, {'ridge': PAL['ridge']}, lambda c, n, i: 'ridge')
    # movable fingers (one per side, each rigid to its own bone)
    for side, sx in (('L', 1), ('R', -1)):
        d = object_from_bm('dactyl_' + side, dactyl_bm(sx), mirror=False)
        paint(d, {'shell': PAL['shell'], 'tip': PAL['tip']}, lambda c, n, i: 'tip' if (c - (_F[1] if sx > 0 else Vector((-_F[1].x, _F[1].y, _F[1].z)))).dot(_D if sx > 0 else Vector((-_D.x, _D.y, _D.z))) > -0.01 else 'shell')
        pieces.append(d)
    # barnacles on the rear-left rim (asymmetric)
    bb = bmesh.new()
    for (x, y, r, h) in ((0.13, 0.13, 0.014, 0.02), (0.105, 0.155, 0.011, 0.016), (0.145, 0.105, 0.009, 0.013),
                         (0.118, 0.108, 0.008, 0.012)):
        z = zs(x, y)
        prism(bb, [((x, y, z - 0.008), r, r), ((x, y, z + h * 0.6), r * 0.85, r * 0.85), ((x, y, z + h), r * 0.5, r * 0.5)],
              dh=Vector((1, 0.3, 0)).normalized(), n=6)
    ba = object_from_bm('barnacles', bb, mirror=False)
    paint(ba, {'barnacle': PAL['barnacle']}, lambda c, n, i: 'barnacle')
    return [st, ey, th, ba] + pieces


def stage4(k, body, pieces):
    bones = [('body', (0.0, 0.12, 0.25), (0.0, -0.12, 0.25), None)]
    for i in range(4):
        bones += [(f'leg{i}a.L', J[f'leg{i}_hip'], J[f'leg{i}_knee'], 'body'),
                  (f'leg{i}b.L', J[f'leg{i}_knee'], J[f'leg{i}_bend'], f'leg{i}a.L', True),
                  (f'leg{i}c.L', J[f'leg{i}_bend'], J[f'leg{i}_tip'], f'leg{i}b.L', True)]
    bones += [('arm.L', J['claw_hip'], J['claw_elbow'], 'body'),
              ('wrist.L', J['claw_elbow'], J['claw_heel'], 'arm.L', True),
              ('palm.L', J['claw_heel'], J['claw_tip'], 'wrist.L', True),
              ('dactyl.L', J['dactyl'], J['dactyl_tip'], 'palm.L')]
    rig = armature(bones, roll='auto')
    skin(body, rig)
    # the dactyl bones drive only the movable finger: bone heat gave the palm-end skin some of their
    # weight; hand it to the palm so the knuckle's socket does not move under the pin
    for sd in 'LR':
        gd, gp = body.vertex_groups.get(f'dactyl.{sd}'), body.vertex_groups.get(f'palm.{sd}')
        if gd is not None:
            gp = gp or body.vertex_groups.new(name=f'palm.{sd}')
            for v in body.data.vertices:
                for g in v.groups:
                    if g.group == gd.index and g.weight > 0:
                        gp.add([v.index], g.weight, 'ADD')
            body.vertex_groups.remove(gd)
    for p in pieces:
        for sd in 'LR':
            if p.name.endswith('dactyl_' + sd):
                bind(p, rig, bone=f'dactyl.{sd}')
                pin = list(range(12))                 # dactyl_bm builds the 12-vertex pin first
                p.vertex_groups[f'dactyl.{sd}'].remove(pin)
                p.vertex_groups.new(name=f'palm.{sd}').add(pin, 1.0, 'REPLACE')
        if 'dactyl' in p.name:
            continue
        bind(p, rig, body=body)
    B = rig.data.bones

    def rot(bone, axis, deg):
        """A rotation about a WORLD axis, as the bone-local XYZ euler (degrees) clip() wants."""
        la = B[bone].matrix_local.to_3x3().inverted() @ Vector(axis).normalized()
        e = Quaternion(la, math.radians(deg)).to_euler('XYZ')
        return tuple(math.degrees(x) for x in e)

    def vec(bone, v):
        return tuple(B[bone].matrix_local.to_3x3().inverted() @ Vector(v))

    def lift_axis(bone):             # +deg about it raises/opens the bone's tip in its own vertical plane
        d = B[bone].tail_local - B[bone].head_local
        return Vector((d.x, d.y, 0)).normalized().cross(Vector((0, 0, 1)))

    def legs(group_lift, sides):
        out = {}
        for i in range(4):
            for sd in 'LR':
                deg = group_lift if ((i % 2 == 0) == (sd == 'L')) == sides else 0.0
                if deg:
                    out[f'leg{i}a.{sd}'] = rot(f'leg{i}a.{sd}', lift_axis(f'leg{i}a.{sd}'), deg)
                    out[f'leg{i}b.{sd}'] = rot(f'leg{i}b.{sd}', lift_axis(f'leg{i}a.{sd}'), -deg * 0.5)
        return out

    def claws(raise_, open_, sides='LR'):
        out = {}
        for sd in sides:
            out[f'arm.{sd}'] = rot(f'arm.{sd}', lift_axis(f'arm.{sd}'), raise_)
            out[f'dactyl.{sd}'] = rot(f'dactyl.{sd}', lift_axis(f'dactyl.{sd}'), open_)
        return out

    # idle: two claw clicks and a slow breath
    clip(rig, 'idle', {1: {}, 8: claws(3, 16), 12: claws(3, 0), 18: claws(3, 16), 22: claws(0, 0),
                       34: claws(4, 8, 'L'), 48: {}},
         loc={1: {'body': (0, 0, 0)}, 24: {'body': vec('body', (0, 0, -0.006))}, 48: {'body': (0, 0, 0)}})
    # move: sideways scuttle, alternating leg groups, the shell sways toward +X and back
    clip(rig, 'move', {1: {}, 7: {**legs(14, True), **claws(4, 0)}, 13: {}, 19: {**legs(14, False), **claws(4, 0)}, 25: {}},
         loc={1: {'body': (0, 0, 0)}, 7: {'body': vec('body', (0.02, 0, 0.008))}, 13: {'body': (0, 0, 0)},
              19: {'body': vec('body', (-0.02, 0, 0.008))}, 25: {'body': (0, 0, 0)}})
    # attack: rear up, claws high and open, then snap shut on the strike
    ax = Vector((1, 0, 0))
    clip(rig, 'attack', {1: {}, 9: {**claws(30, 18), 'body': rot('body', ax, 6)},
                         15: {**claws(34, 20), 'body': rot('body', ax, 8)},
                         19: {**claws(4, -2), 'body': rot('body', ax, -3)},
                         26: {**claws(6, 0), 'body': rot('body', ax, -2)}, 33: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
