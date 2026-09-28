import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *

META = dict(creature='character', model='opus')

# the skeleton the model is built on (left half, faces -Y)
J = dict(
    hips=(0.0, -0.01, 0.70), spine=(0.0, -0.012, 0.88), chest=(0.0, -0.01, 1.04),
    neck=(0.0, -0.005, 1.15), head=(0.0, 0.0, 1.235), top=(0.0, 0.0, 1.58),
    clav=(0.03, 0.0, 1.12), shoulder=(0.15, 0.020, 1.064), elbow=(0.352, 0.042, 1.100),
    wrist=(0.565, 0.047, 1.092), fingers=(0.70, 0.050, 1.07),
    hip=(0.075, -0.006, 0.66), knee=(0.100, -0.004, 0.35), ankle=(0.113, 0.010, 0.095),
    toe=(0.14, -0.15, 0.02),
)

HEAD_C = Vector((0.0, 0.0, 1.40))
HEAD_R = 0.20


def half_ring(z, cy, hw, df, db, k=0.78):
    """Torso half-octagon: front seam, front-side, side, back-side, back seam."""
    return [(0.0, cy - df, z), (hw * k, cy - df * 0.78, z), (hw, cy, z),
            (hw * k, cy + db * 0.78, z), (0.0, cy + db, z)]


HEAD_TH = (0, 14, 40, 68, 98, 138, 180)          # eye face between 14 and 40 degrees


def head_ring(phi, sx=1.0, sy=1.0):
    p = math.radians(phi)
    r, z = HEAD_R * math.cos(p), HEAD_C.z + HEAD_R * math.sin(p)
    return [(r * math.sin(math.radians(t)) * sx, HEAD_C.y - r * math.cos(math.radians(t)) * sy, z) for t in HEAD_TH]


def stitch(bm, a, b, steps):
    """Join row a to a longer row b: steps is a list of 'q' (both advance) / 't' (b only)."""
    i = j = 0
    for s in steps:
        if s == 'q':
            bm.faces.new([a[i], a[i + 1], b[j + 1], b[j]]); i += 1; j += 1
        else:
            bm.faces.new([a[i], b[j + 1], b[j]]); j += 1


def section(verts, c, u, w, ru, rw, off=0.0, n=6):
    """Place a limb ring: each vertex keeps its angular slot (snapped to n slots
    starting at off degrees) around centre c in the (u, w) plane."""
    u, w, c = Vector(u), Vector(w), Vector(c)
    cc = centre(verts)
    step = 360.0 / n
    used = set()
    for v in verts:
        d = v.co - cc
        a = math.degrees(math.atan2(d.dot(w), d.dot(u)))
        s = round((a - off) / step) % n
        assert s not in used, 'section: two verts in one slot'
        used.add(s)
        aa = math.radians(off + s * step)
        v.co = c + u * (ru * math.cos(aa)) + w * (rw * math.sin(aa))


def facing(faces, d):
    for q in faces:
        q.normal_update()
    return max(faces, key=lambda q: q.normal.dot(Vector(d)))


def stage1(k):
    bm = bmesh.new()
    # ---- torso column: hip bottom -> neck top (half octagons) ----
    T = [  # z, cy, half width, front depth, back depth
        (0.680, -0.008, 0.118, 0.070, 0.072),   # R0 hip bottom (leg sockets under it)
        (0.770, -0.012, 0.114, 0.074, 0.070),   # R1 hip
        (0.880, -0.016, 0.100, 0.078, 0.060),   # R2 waist
        (0.975, -0.012, 0.114, 0.092, 0.070),   # R3 rib cage
        (1.050, -0.008, 0.128, 0.092, 0.080),   # R4 chest / armpit
        (1.132, -0.004, 0.126, 0.066, 0.074),   # R5 shoulder top
        (1.165, -0.004, 0.064, 0.058, 0.054),   # R6 neck base
        (1.215, -0.002, 0.056, 0.054, 0.050),   # R7 neck top
    ]
    R = [ring(bm, half_ring(*t)) for t in T]
    for a, b in zip(R, R[1:]):
        bridge(bm, a, b)
    # ---- head: faceted sphere, 12-gon latitude rings ----
    PHI = (-62, -38, -6, 22, 46, 66, 82)
    H = [ring(bm, head_ring(p)) for p in PHI]
    stitch(bm, R[-1], H[0], ['t', 'q', 'q', 't', 'q', 'q'])
    for a, b in zip(H, H[1:]):
        bridge(bm, a, b)
    cap(bm, H[-1])
    # ---- pelvis floor: seam crotch + one hexagonal leg socket ----
    F0, FS, S, BS, B0 = R[0]
    C = bm.verts.new((0.0, -0.008, 0.645))
    Mf = bm.verts.new((0.048, -0.058, 0.668))
    Mi = bm.verts.new((0.026, -0.008, 0.655))
    Mb = bm.verts.new((0.048, 0.050, 0.668))
    bm.faces.new([F0, FS, Mf, C]); bm.faces.new([C, Mf, Mi]); bm.faces.new([C, Mi, Mb])
    bm.faces.new([C, Mb, BS, B0])
    leg = bm.faces.new([FS, S, BS, Mb, Mi, Mf])
    recalc_normals(bm)
    X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
    L = [  # z, cx, cy, rx, ry
        (0.600, 0.072, -0.008, 0.062, 0.066),
        (0.500, 0.084, -0.006, 0.055, 0.060),
        (0.410, 0.095, -0.006, 0.047, 0.052),
        (0.350, 0.100, -0.004, 0.046, 0.051),
        (0.290, 0.104, 0.004, 0.045, 0.056),
        (0.215, 0.108, 0.008, 0.040, 0.050),
        (0.105, 0.113, 0.010, 0.031, 0.038),
        (0.000, 0.117, 0.014, 0.040, 0.054),
    ]
    f = [leg]
    for z, cx, cy, rx, ry in L:
        r = extrude(bm, f)
        section(r['verts'], (cx, cy, z), X, Y, rx, ry / 0.88)   # hex: flat front/back faces sit at .87 ry
        f = r['faces']
    # foot: the front face of the ankle-to-sole segment goes forward
    front = facing(r['sides'], (0, -1, 0))
    for yy, xib, xob, xit, xot, zt in ((-0.100, 0.074, 0.186, 0.092, 0.162, 0.050),
                                        (-0.198, 0.086, 0.180, 0.100, 0.164, 0.026)):
        e = extrude(bm, [front])
        for v in e['verts']:
            top = v.co.z > 0.01
            inner = v.co.x < 0.117
            x = (xit if inner else xot) if top else (xib if inner else xob)
            v.co = Vector((x, yy, zt if top else 0.0))
        front = e['faces'][0]
    # ---- arm: the two side quads between R4 and R5 ----
    fa = [face_near(bm, (0.12, -0.03, 1.09), n=X), face_near(bm, (0.12, 0.03, 1.09), n=X)]
    assert fa[0] is not fa[1]
    A = [  # x, cy, cz, ry, rz
        (0.170, 0.008, 1.096, 0.050, 0.046),
        (0.240, 0.014, 1.098, 0.042, 0.040),
        (0.315, 0.018, 1.100, 0.036, 0.034),
        (0.352, 0.020, 1.100, 0.035, 0.032),
        (0.392, 0.021, 1.099, 0.038, 0.034),
        (0.495, 0.024, 1.096, 0.032, 0.028),
        (0.565, 0.025, 1.092, 0.025, 0.021),
        (0.618, 0.026, 1.088, 0.050, 0.021),
        (0.668, 0.028, 1.082, 0.048, 0.019),
        (0.706, 0.029, 1.064, 0.042, 0.016),
        (0.724, 0.030, 1.034, 0.034, 0.012),
    ]
    f = fa
    arm = []
    for i, (x, cy, cz, ry, rz) in enumerate(A):
        r = extrude(bm, f)
        cy += 0.012 if i == 0 else 0.022
        ry *= 1.08 if i == 0 else 1.15
        section(r['verts'], (x, cy, cz), Y, Z, ry, rz, off=30)
        f = r['faces']
        arm.append(r)
    # thumb: the front face of the wrist-to-palm segment
    th = facing(arm[7]['sides'], (0, -1, 0))
    for d, s in (((0.014, -0.026, -0.010), 0.8), ((0.020, -0.018, -0.018), 0.65)):
        e = extrude(bm, [th], offset=d)
        scale(e['verts'], s)
        th = e['faces'][0]
    snap_seam(bm)
    recalc_normals(bm)
    return object_from_bm('body', bm)


EYE_D = Vector((0.09, -0.176, 0.028)).normalized()     # eye centre direction from the head centre
EYE_C = HEAD_C + EYE_D * HEAD_R * 0.97
META['keep_valleys'] = lambda c: (Vector((abs(c[0]), c[1], c[2])) - EYE_C).length < 0.045


def stage2(k, body):
    bm = edit(body)
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye face; the eye lens sits in it'):
        ef = face_near(bm, EYE_C, n=EYE_D)
        inner = inset(bm, [ef], 0.3, 0.0)
    for v in inner[0].verts:
        v.co -= EYE_D * 0.008
    with k.topo(bm, 'loop', 'shoulder loop: the arm drops and swings here'):
        loopcut(bm, edge_near(bm, (0.148, 0.008, 1.137)), t=0.5)
    # planes: knee cap forward, calf back, pecs forward, seat back
    move(verts_where(bm, lambda c: abs(c.z - 0.35) < 0.004 and c.y < -0.02 and c.x > 0.04), (0, -0.008, 0))
    move(verts_where(bm, lambda c: abs(c.z - 0.29) < 0.004 and c.y > 0.03 and c.x > 0.04), (0, 0.006, 0))
    move(verts_where(bm, lambda c: 0.96 < c.z < 1.06 and c.y < -0.07 and c.x < 0.11), (0, -0.006, 0))
    move(verts_where(bm, lambda c: abs(c.z - 0.77) < 0.004 and c.y > 0.04), (0, 0.008, 0))
    # hip: the hip rings widen into the thigh tops, so the torso runs into the legs without a shelf
    for zz, f in ((0.68, 1.085), (0.77, 1.05)):
        for v in verts_where(bm, lambda c: abs(c.z - zz) < 0.004 and c.x > 0.01):
            v.co.x *= f
    # the pelvis front: the floor quad under the belly tips forward so it reads as the belly running down
    for p0, p1 in (((0.0, -0.078, 0.68), (0.0, -0.078, 0.662)), ((0.048, -0.058, 0.668), (0.050, -0.068, 0.652)),
                   ((0.0, -0.008, 0.645), (0.0, -0.016, 0.638))):
        v = vert_near(bm, p0)
        assert (v.co - Vector(p0)).length < 0.004, p0
        v.co = Vector(p1)
    head_planes(bm)
    hand(bm)
    foot(k, bm)
    commit(body, bm)


def head_planes(bm):
    """Break the ring bands: a jaw plane (lowest rings down, chin forward), a brow plane
    above the eyes and a cheek plane each side. The crown is left alone."""
    def hv(phi, ti):
        q = Vector(head_ring(phi)[ti])
        v = vert_near(bm, q)
        assert (v.co - q).length < 1e-4, (phi, ti)
        return v
    brow = [hv(p, ti) for p in (22, 46) for ti in (0, 1, 2)]
    cheek = [hv(p, ti) for p in (-38, -6) for ti in (2, 3)]
    for ti in range(7):
        hv(-62, ti).co.z -= 0.004
        v = hv(-38, ti); v.co.z -= 0.010
        if ti < 2:
            v.co.y -= 0.008
    flatten(brow)
    flatten(cheek)


def foot(k, bm):
    """A short foot: instep rising from the toes, a ball row, and a blunt toe block."""
    with k.topo(bm, 'loop', 'ball of the foot: the break between the instep and the toe block'):
        loopcut(bm, edge_near(bm, (0.183, -0.149, 0.0)), t=0.5)
    rows = ((-0.100, (-0.078, 0.074, 0.180, 0.090, 0.160, 0.074)),
            (-0.149, (-0.122, 0.080, 0.178, 0.094, 0.164, 0.042)),
            (-0.198, (-0.162, 0.086, 0.172, 0.098, 0.162, 0.034)))
    for y0, (yy, xib, xob, xit, xot, zt) in rows:
        rv = verts_where(bm, lambda c: abs(c.y - y0) < 0.004 and c.z < 0.09 and c.x > 0.05)
        assert len(rv) == 4, (y0, len(rv))
        xm = sum(v.co.x for v in rv) / 4
        for v in rv:
            top, inner = v.co.z > 0.01, v.co.x < xm
            v.co = Vector(((xit if inner else xot) if top else (xib if inner else xob), yy, zt if top else 0.0))


def hand(bm):
    """Mitten with thickness: boxier hand rings, the thumb laid along the palm edge,
    the finger ring curled down."""
    for hx in (0.618, 0.668, 0.706, 0.724):
        rv = verts_where(bm, lambda c: abs(c.x - hx) < 2e-4 and c.z > 0.95)
        assert len(rv) == 6, (hx, len(rv))
        cz = sum(v.co.z for v in rv) / 6
        top = max(abs(v.co.z - cz) for v in rv)
        for v in rv:
            dz = v.co.z - cz
            v.co.z = cz + (math.copysign(0.72 * top, dz) if abs(dz) < 0.75 * top else dz * 1.1)
    # the thumb: a lobe along the palm's front edge (root at the wrist), tip against the mitten
    for (x0, y0), (x1, y1, dz) in (((0.5843, -0.0063), (0.584, -0.009, 0.0)), ((0.6267, -0.0254), (0.634, -0.007, 0.0)),
                                   ((0.6117, -0.0276), (0.626, -0.022, 0.008)), ((0.6393, -0.0401), (0.652, -0.016, 0.008))):
        vs = verts_where(bm, lambda c: abs(c.x - x0) < 1e-3 and abs(c.y - y0) < 1e-3 and c.z > 1.0)
        assert len(vs) == 2, (x0, len(vs))
        for v in vs:
            v.co.x, v.co.y, v.co.z = x1, y1, v.co.z + dz
    r9 = verts_where(bm, lambda c: abs(c.x - 0.706) < 2e-4 and c.z > 0.95)
    rotate(verts_where(bm, lambda c: abs(c.x - 0.724) < 2e-4 and c.z > 0.95), (0, 1, 0), 20, centre(r9))


PAL = {'skin': '#f0b477', 'eye_white': '#f7f7f5', 'black': '#151515', 'brow': '#3a2f2a'}


def frame_at(n):
    n = Vector(n).normalized()
    u = Vector((0, 0, 1)).cross(n).normalized()
    return n, u, n.cross(u).normalized()


def proj(tree, e):
    """The outer surface of tree along the ray from the head centre through e."""
    e = Vector(e).normalized()
    return tree.ray_cast(HEAD_C + e * 0.5, -e)[0]


def disc(name, tree, c0, n, u, w, r, h, rb, hb, dome, sides=12):
    """A lens: its rim follows the surface under it at +h, the back sits at hb (buried)."""
    bm = bmesh.new()
    A = [2 * math.pi * i / sides for i in range(sides)]

    def at(rr, hh):
        out = []
        for a in A:
            e = (c0 + (u * math.cos(a) + w * math.sin(a)) * rr - HEAD_C).normalized()
            out.append(proj(tree, e) + e * hh)
        return out
    F = ring(bm, at(r, h)); B = ring(bm, at(rb, hb))
    bridge(bm, F, B, closed=True)
    tip = bm.verts.new(centre(F) + n * dome)
    for i in range(sides):
        bm.faces.new([F[i], F[(i + 1) % sides], tip])
    bm.faces.new(list(reversed(B)))
    return object_from_bm(name, bm, mirror=False)


def _at(tree, c0, u, w, rr, hh, sides=12):
    out = []
    for i in range(sides):
        a = 2 * math.pi * i / sides
        e = (c0 + (u * math.cos(a) + w * math.sin(a)) * rr - HEAD_C).normalized()
        out.append(proj(tree, e) + e * hh)
    return out


def outline(name, tree, c0, u, w, sides=12):
    """The eye outline: a static torus band seated in the skin; the front annulus
    black, the outer side skin (a thin dark edge from the side, not a disc)."""
    bm = bmesh.new()
    OB, OF = ring(bm, _at(tree, c0, u, w, 0.058, -0.006)), ring(bm, _at(tree, c0, u, w, 0.061, 0.004))
    IF, IB = ring(bm, _at(tree, c0, u, w, 0.050, 0.0105)), ring(bm, _at(tree, c0, u, w, 0.047, 0.0015))
    for a, b in ((OB, OF), (OF, IF), (IF, IB), (IB, OB)):
        bridge(bm, a, b, closed=True)
    recalc_normals(bm)
    ob = object_from_bm(name, bm, mirror=False)
    paint(ob, {'skin': PAL['skin'], 'black': PAL['black']}, lambda c, nn, i: 'black' if 12 <= i < 36 else 'skin')
    return ob


def sclera(name, tree, c0, n, u, w, sides=12):
    """The white dome inside the outline: its rim sits in the outline's inner wall and
    every vertex stays > 7 mm off the skin, so the blink can squash it without it
    riding over the skin (it hangs on the outline, not on the body)."""
    bm = bmesh.new()
    R1 = ring(bm, _at(tree, c0, u, w, 0.0505, 0.0097))
    R2 = ring(bm, _at(tree, c0, u, w, 0.040, 0.0125))
    RB = ring(bm, _at(tree, c0, u, w, 0.036, 0.0115))
    bridge(bm, R1, R2, closed=True); bridge(bm, RB, R1, closed=True)
    tip = bm.verts.new(centre(R2) + n * 0.008)
    e0 = (c0 - HEAD_C).normalized()
    back = bm.verts.new(proj(tree, e0) + e0 * 0.0115)
    for i in range(sides):
        bm.faces.new([R2[i], R2[(i + 1) % sides], tip])
        bm.faces.new([RB[(i + 1) % sides], RB[i], back])
    recalc_normals(bm)
    return solid(object_from_bm(name, bm, mirror=False), 'eye_white')


def strip(name, tree, dirs, out, inn, half, seam=False, mirror=False):
    """A thin bar laid on the surface along dirs (brow, mouth line)."""
    bm = bmesh.new()
    hits = [proj(tree, d) for d in dirs]
    secs = []
    for i, (d, p) in enumerate(zip(dirs, hits)):
        e = Vector(d).normalized()
        t = hits[min(i + 1, len(hits) - 1)] - hits[max(i - 1, 0)]
        up = e.cross(t).normalized()
        if up.z < 0:
            up = -up
        pts = [p + e * out + up * half, p + e * out - up * half, p + e * inn - up * half, p + e * inn + up * half]
        if seam and i == 0:
            pts = [Vector((0.0, q.y, q.z)) for q in pts]
        secs.append(ring(bm, pts))
    for a, b in zip(secs, secs[1:]):
        bridge(bm, a, b, closed=True)
    if not seam:
        bm.faces.new(list(reversed(secs[0])))
    bm.faces.new(secs[-1])
    return object_from_bm(name, bm, mirror=seam or mirror)


def solid(ob, key):
    paint(ob, {key: PAL[key]}, lambda c, n, i: key)
    return ob


def sph(th, ph):
    t, p = math.radians(th), math.radians(ph)
    return Vector((math.sin(t) * math.cos(p), -math.cos(t) * math.cos(p), math.sin(p)))


def stage3(k, body):
    from mathutils.bvhtree import BVHTree
    solid(body, 'skin')
    tb = BVHTree.FromBMesh(evaluated_bm(body))
    pieces = []
    for sgn, sd in ((1, 'L'), (-1, 'R')):
        d = Vector((sgn * EYE_D.x, EYE_D.y, EYE_D.z))
        n, u, w = frame_at(d)
        c0 = HEAD_C + d * HEAD_R
        rim = outline(f'outline.{sd}', tb, c0, u, w)
        white = sclera(f'eye.{sd}', tb, c0, n, u, w)
        bpy.context.view_layer.update()
        tw = BVHTree.FromBMesh(evaluated_bm(white))
        pc = c0 + u * (-sgn * 0.004) - w * 0.002
        pupil = solid(disc(f'pupil.{sd}', tw, pc, n, u, w, 0.022, 0.003, 0.018, -0.004, 0.004, sides=10), 'black')
        pieces += [rim, white, pupil]
    brow = strip('brow', tb, [sph(t, p) for t, p in ((10, 33), (20, 36.5), (31, 37.5), (42, 35))],
                 0.0042, -0.008, 0.0045, mirror=True)
    mouth = strip('mouth', tb, [sph(t, -24.5) for t in (0, 6, 11.5)], 0.0038, -0.008, 0.0035, seam=True)
    pieces += [solid(brow, 'brow'), solid(mouth, 'brow')]
    # nose: a small half pyramid, its base buried in the face
    nc = proj(tb, sph(0, -10))
    bm = bmesh.new()
    top, s1, s2, bot = ring(bm, [nc + Vector(q) for q in ((0, 0.012, 0.020), (0.014, 0.010, 0.005),
                                                             (0.011, 0.008, -0.012), (0, 0.006, -0.015))])
    tip = bm.verts.new(nc + Vector((0, -0.026, -0.004)))
    for a, b in ((top, s1), (s1, s2), (s2, bot)):
        bm.faces.new([a, b, tip])
    bm.faces.new([top, bot, s2, s1])
    pieces.append(solid(object_from_bm('nose', bm, mirror=True), 'skin'))
    return pieces


def clip_s(rig, name, keys, loc=None, scl=None):
    """kit clip() plus scale keys (the blink)."""
    act = clip(rig, name, keys, loc=loc)
    if scl:
        ad = rig.animation_data
        ad.action = act
        if hasattr(ad, 'action_slot') and len(getattr(act, 'slots', [])):
            ad.action_slot = act.slots[0]
        pb = rig.pose.bones
        for f in sorted(scl):
            for b, sv in scl[f].items():
                pb[b].scale = sv
                pb[b].keyframe_insert('scale', frame=f)
        rest(rig)
        ad.action = None
    return act


def P(**kw):
    """A full pose: arms dropped to a relaxed A, elbows soft; kw overrides (use _L/_R for .L/.R)."""
    d = {'upperarm.L': (0, 0, -38), 'upperarm.R': (0, 0, 38), 'forearm.L': (12, 0, 0), 'forearm.R': (12, 0, 0),
         'clav.L': (0, 0, -12), 'clav.R': (0, 0, 12), 'chest': (0, 0, 0), 'spine': (0, 0, 0), 'head': (0, 0, 0),
         'neck': (0, 0, 0), 'hips': (0, 0, 0), 'thigh.L': (0, 0, 0), 'thigh.R': (0, 0, 0),
         'shin.L': (0, 0, 0), 'shin.R': (0, 0, 0)}
    for kk, v in kw.items():
        d[kk.replace('_L', '.L').replace('_R', '.R')] = v
    return d


def stage4(k, body, pieces):
    eL = tuple(EYE_C); eR = (-EYE_C.x, EYE_C.y, EYE_C.z)
    rig = armature([
        ('hips', J['hips'], J['spine'], None),
        ('spine', J['spine'], J['chest'], 'hips', True),
        ('chest', J['chest'], J['neck'], 'spine', True),
        ('neck', J['neck'], J['head'], 'chest', True),
        ('head', J['head'], J['top'], 'neck', True),
        ('clav.L', J['clav'], J['shoulder'], 'chest'),
        ('upperarm.L', J['shoulder'], J['elbow'], 'clav.L', True),
        ('forearm.L', J['elbow'], J['wrist'], 'upperarm.L', True),
        ('hand.L', J['wrist'], J['fingers'], 'forearm.L', True),
        ('thigh.L', J['hip'], J['knee'], 'hips'),
        ('shin.L', J['knee'], J['ankle'], 'thigh.L', True),
        ('foot.L', J['ankle'], J['toe'], 'shin.L', True),
        ('eye.L', eL, tuple(EYE_C + EYE_D * 0.04), 'head'),
    ], roll='auto')
    for b in ('eye.L', 'eye.R'):
        rig.data.bones[b].use_deform = False     # the skin never follows the blink
    skin(body, rig)
    for b in ('eye.L', 'eye.R'):
        rig.data.bones[b].use_deform = True
    for p in pieces:
        nm = p.name
        if nm.startswith('outline'):
            bind(p, rig, bone='head')              # static, seated in the skin
        elif 'eye' in nm or 'pupil' in nm:
            bind(p, rig, bone='eye.L' if nm.endswith('.L') else 'eye.R')   # blinks, hangs on the outline
        else:
            bind(p, rig, body=body)
    one = (1, 1, 1); shut = (1, 1, 0.35)
    clip_s(rig, 'idle', {
        1: P(), 24: P(chest=(-2.5, 0, 0), spine=(-1, 0, 0), head=(3, 0, 0), neck=(-1, 0, 0),
                      upperarm_L=(0, 0, -35), upperarm_R=(0, 0, 35)), 48: P()},
        scl={1: {'eye.L': one, 'eye.R': one}, 41: {'eye.L': one, 'eye.R': one},
             43: {'eye.L': shut, 'eye.R': shut}, 45: {'eye.L': one, 'eye.R': one},
             48: {'eye.L': one, 'eye.R': one}})
    sw, st = 20, 22
    walk = {
        1: P(thigh_L=(st, 0, 0), thigh_R=(-st, 0, 0), shin_L=(-5, 0, 0), shin_R=(-15, 0, 0),
             upperarm_L=(-sw, 0, -40), upperarm_R=(sw, 0, 40), hips=(0, 5, 0), chest=(0, -7, 0), spine=(3, 0, 0)),
        9: P(shin_L=(-8, 0, 0), shin_R=(-50, 0, 0), spine=(3, 0, 0), upperarm_L=(0, 0, -40), upperarm_R=(0, 0, 40)),
        17: P(thigh_L=(-st, 0, 0), thigh_R=(st, 0, 0), shin_L=(-15, 0, 0), shin_R=(-5, 0, 0),
              upperarm_L=(sw, 0, -40), upperarm_R=(-sw, 0, 40), hips=(0, -5, 0), chest=(0, 7, 0), spine=(3, 0, 0)),
        25: P(shin_L=(-50, 0, 0), shin_R=(-8, 0, 0), spine=(3, 0, 0), upperarm_L=(0, 0, -40), upperarm_R=(0, 0, 40)),
    }
    walk[33] = walk[1]
    bob = {f: {'hips': (0, z, 0)} for f, z in ((1, 0.0), (9, 0.014), (17, 0.0), (25, 0.014), (33, 0.0))}
    clip_s(rig, 'move', walk, loc=bob)
    guard = dict(forearm_L=(45, 0, 0), forearm_R=(45, 0, 0))
    clip_s(rig, 'attack', {
        1: P(**guard),
        7: P(forearm_L=(45, 0, 0), upperarm_R=(-25, 0, 36), forearm_R=(80, 0, 0), chest=(0, -12, 0)),
        11: P(forearm_L=(45, 0, 0), clav_R=(24, 0, 10), upperarm_R=(52, 0, 6), forearm_R=(4, 0, 0), chest=(3, 24, 0), spine=(0, 8, 0)),
        16: P(forearm_L=(45, 0, 0), clav_R=(18, 0, 10), upperarm_R=(46, 0, 12), forearm_R=(14, 0, 0), chest=(2, 18, 0), spine=(0, 6, 0)),
        25: P(**guard)})
    return rig


run(META, stage1, stage2, stage3, stage4)
