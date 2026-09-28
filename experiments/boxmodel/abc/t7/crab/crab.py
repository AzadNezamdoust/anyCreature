import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *

META = dict(creature='crab', model='opus',
            keep_valleys=lambda c: c.y < -0.29 and abs(c.x) < 0.16 and c.z > 0.1)

# ---------------------------------------------------------------------------
# carapace stations: (y, rim half-width W, top-seam z, rim z)
# the front margin zig-zags (tooth / notch) along the anterolateral rim
ST = [
    (-0.32, 0.15, 0.215, 0.180),
    (-0.29, 0.22, 0.235, 0.182),   # tooth
    (-0.26, 0.218, 0.250, 0.185),  # notch
    (-0.22, 0.3, 0.265, 0.188),   # tooth
    (-0.18, 0.31, 0.278, 0.190),   # notch   | claw segment
    (-0.13, 0.415, 0.290, 0.192),   # tooth   |
    (-0.08, 0.44, 0.298, 0.192),   #         | leg 1
    (-0.02, 0.44, 0.303, 0.192),   #         |
    (0.02, 0.425, 0.303, 0.192),   #         | leg 2
    (0.08, 0.39, 0.298, 0.190),   #         |
    (0.11, 0.36, 0.292, 0.188),   #         | leg 3
    (0.16, 0.3, 0.280, 0.186),   #         |
    (0.19, 0.26, 0.268, 0.184),   #         | leg 4
    (0.23, 0.2, 0.248, 0.182),   #         |
    (0.28, 0.13, 0.215, 0.178),
]
CLAW_SEG, LEG_SEGS = 4, (6, 8, 10, 12)


def station(i):
    y, W, zt, zr = ST[i]
    return [(0.0, y, zt), (0.55 * W, y, zt - 0.022), (W, y, zr),
            (0.82 * W, y, 0.122), (0.45 * W, y, 0.096), (0.0, y, 0.090)]


def seg_face_centre(s, a=2, b=3):
    p = station(s) + station(s + 1)
    q = [p[a], p[b], p[6 + a], p[6 + b]]
    return tuple(sum(v[k] for v in q) / 4 for k in range(3))


# walking leg profile: (distance along heading, z, hu, hw); hu is in the leg plane (tall), hw across it
LEG_PROF = [(0.060, 0.168, 0.042, 0.034), (0.130, 0.240, 0.050, 0.032), (0.180, 0.286, 0.043, 0.030),
            (0.212, 0.298, 0.036, 0.027), (0.248, 0.282, 0.040, 0.028), (0.310, 0.200, 0.034, 0.025),
            (0.340, 0.160, 0.028, 0.022), (0.385, 0.085, 0.021, 0.017), (0.425, 0.000, 0.008, 0.008)]
LEGS = [(-32.0, 0.86), (-6.0, 0.9), (20.0, 0.88), (46.0, 0.8)]   # heading (deg, + = back), reach scale


def leg_chain(i):
    a, s = LEGS[i]
    c0 = seg_face_centre(LEG_SEGS[i])
    hd = (math.cos(math.radians(a)), math.sin(math.radians(a)))
    out = []
    for r, z, hu, hw in LEG_PROF:
        out.append(((c0[0] + hd[0] * r * s, c0[1] + hd[1] * r * s, z * (0.93 if i == 3 else 1.0)), hu, hw))
    return c0, out


CLAW = [((0.385, -0.195, 0.172), 0.038, 0.032), ((0.445, -0.245, 0.185), 0.044, 0.034),
        ((0.470, -0.295, 0.195), 0.038, 0.032), ((0.440, -0.340, 0.205), 0.044, 0.038),
        ((0.400, -0.380, 0.205), 0.038, 0.034), ((0.370, -0.410, 0.205), 0.080, 0.062),
        ((0.310, -0.470, 0.215), 0.095, 0.075), ((0.250, -0.520, 0.205), 0.085, 0.066)]
DACTYL = [((0.180, -0.590, 0.265), 0.034, 0.042), ((0.130, -0.635, 0.250), 0.024, 0.032),
          ((0.100, -0.665, 0.228), 0.014, 0.020), ((0.090, -0.680, 0.206), 0.006, 0.008)]
POLLEX = [((0.180, -0.590, 0.140), 0.032, 0.042), ((0.130, -0.630, 0.148), 0.022, 0.030),
          ((0.105, -0.660, 0.165), 0.013, 0.018), ((0.095, -0.672, 0.182), 0.006, 0.008)]

# the claw is held low, below the front rim, so the toothed margin and the eyes read from the front
CLAW = [((c[0], c[1], c[2] - (0.03 if i >= 3 else 0.012 * i)), hu, hw) for i, (c, hu, hw) in enumerate(CLAW)]
DACTYL = [((c[0], c[1], c[2] - 0.03), hu, hw) for c, hu, hw in DACTYL]
POLLEX = [((c[0], c[1], c[2] - 0.03), hu, hw) for c, hu, hw in POLLEX]

# the skeleton the model is built on
J = dict(body_h=(0.0, 0.14, 0.19), body_t=(0.0, -0.22, 0.19),
         claw_root=seg_face_centre(CLAW_SEG), claw_elbow=CLAW[2][0], claw_wrist=CLAW[4][0],
         claw_palm=CLAW[7][0], dactyl_root=(0.225, -0.545, 0.220), dactyl_tip=DACTYL[3][0],
         pollex_root=(0.225, -0.545, 0.130), pollex_tip=POLLEX[3][0])
for _i in range(4):
    _c0, _ch = leg_chain(_i)
    J[f'leg{_i + 1}_root'] = _c0
    J[f'leg{_i + 1}_knee'] = _ch[3][0]
    J[f'leg{_i + 1}_bend'] = _ch[6][0]
    J[f'leg{_i + 1}_tip'] = _ch[8][0]


def grow(bm, face, chain, ground=False):
    """Extrude `face` through a chain of (centre, hu, hw) sections. Each new
    section is the previous one projected onto the plane across the limb at
    that joint (the bisector of the in/out directions), then sized."""
    f = face
    prev = centre(list(f.verts))
    Z = Vector((0, 0, 1))
    for k, (c, hu, hw) in enumerate(chain):
        c = Vector(c)
        din = (c - prev).normalized()
        d = din if k == len(chain) - 1 else (din + (Vector(chain[k + 1][0]) - c).normalized()).normalized()
        w = Z.cross(d)
        w = w.normalized() if w.length > 1e-4 else Vector((1, 0, 0))
        u = d.cross(w).normalized()
        r = extrude(bm, [f])
        f = r['faces'][0]
        vs = list(f.verts)
        c_old = centre(vs)
        offs = []
        for v in vs:
            o = v.co - c_old
            o = o - o.dot(d) * d
            offs.append((o.dot(u), o.dot(w)))
        A = max(abs(a) for a, _ in offs) or 1.0
        B = max(abs(b) for _, b in offs) or 1.0
        for v, (a, b) in zip(vs, offs):
            v.co = c + u * (a * hu / A) + w * (b * hw / B)
        if ground and k == len(chain) - 1:
            mz = min(v.co.z for v in vs)
            for v in vs:
                v.co.z -= mz
        prev = c
    return f


def split_fingers(bm, f):
    """Cut the palm's end face across into an upper (dactyl) and a lower (pollex) face."""
    vs = sorted(f.verts, key=lambda v: v.co.z)
    lo, hi = set(vs[:2]), set(vs[2:])
    sides = [e for e in f.edges if (e.verts[0] in lo) != (e.verts[1] in lo)]
    mids = []
    for e in sides:
        a = e.verts[0]
        _, m = bmesh.utils.edge_split(e, a, 0.5)
        mids.append(m)
    bmesh.ops.connect_verts(bm, verts=mids)
    fs = [g for g in mids[0].link_faces if mids[1] in g.verts]
    top = next(g for g in fs if any(v in hi for v in g.verts))
    bot = next(g for g in fs if any(v in lo for v in g.verts))
    return top, bot


def stage1(k):
    bm = bmesh.new()
    rings = [ring(bm, station(i)) for i in range(len(ST))]
    segs = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(ST) - 1)]
    cap(bm, rings[0])
    cap(bm, list(reversed(rings[-1])))
    recalc_normals(bm)
    for i, s in enumerate(LEG_SEGS):
        grow(bm, segs[s][2], leg_chain(i)[1], ground=True)
    palm = grow(bm, segs[CLAW_SEG][2], CLAW)
    top, bot = split_fingers(bm, palm)
    grow(bm, top, DACTYL)
    grow(bm, bot, POLLEX)
    snap_seam(bm)
    ob = object_from_bm('body', bm)
    if os.environ.get('CRAB_DBG'):
        eb = evaluated_bm(ob)
        eb.faces.ensure_lookup_table()
        t = BVHTree.FromBMesh(eb)
        for i, j in t.overlap(t):
            if i < j and not (set(eb.faces[i].verts) & set(eb.faces[j].verts)):
                a, b = eb.faces[i].calc_center_median(), eb.faces[j].calc_center_median()
                say('HIT', tuple(round(x, 3) for x in a), tuple(round(x, 3) for x in b))
    return ob


def stage2(k, body):
    bm = edit(body)
    row = lambda idx, ks: [vert_near(bm, station(i)[j]) for i in idx for j in ks]
    # the front cap splits into two eye sockets either side of a rostrum ridge
    with k.topo(bm, 'inset', 'eye sockets: a recessed orbit on the front face for the stalk bases'):
        inner = inset(bm, [face_near(bm, (0.06, -0.32, 0.15), n=(0, -1, 0))], 0.28, 0.0)
    for v in inner[0].verts:
        v.co.y += 0.016
    # the carapace as a few big planes: front slope, dorsal plate, rear slope
    flatten(row(range(0, 4), (0, 1)))
    flatten(row(range(4, 11), (0, 1)))
    flatten(row(range(11, 15), (0, 1)))
    # the side slopes behind the teeth: a mid-lateral and a rear-lateral facet
    flatten(row(range(6, 10), (1, 2)))
    flatten(row(range(11, 15), (1, 2)))
    commit(body, bm)


PAL = {'shell': '#c8502e', 'ridge': '#8e3420', 'belly': '#efc9a0', 'tip': '#2a1c18',
       'eye': '#111111', 'barnacle': '#9a8474'}


def W_at(y):
    if y <= ST[0][0]:
        return ST[0][1]
    for (y0, w0, *_), (y1, w1, *_) in zip(ST, ST[1:]):
        if y <= y1:
            return w0 + (w1 - w0) * (y - y0) / (y1 - y0)
    return ST[-1][1]


def body_rule(c, n, i):
    x = abs(c.x)
    if -0.325 < c.y < 0.285 and x <= W_at(c.y) + 0.012 and c.z > 0.085:      # carapace
        if n.z < -0.35:
            return 'belly'
        if c.y < -0.300 and x < 0.16 and c.z < 0.2:
            return 'ridge'                                                    # eye sockets
        if c.z < 0.172:
            return 'ridge'
        if -0.20 < c.y < 0.17 and x < 0.52 * W_at(c.y) and n.z > 0.75:
            return 'ridge'                                                    # dorsal saddle plate
        return 'shell'
    if c.y < -0.17 and x < 0.52:                                              # claw
        for t in (DACTYL[-1][0], POLLEX[-1][0]):
            if (Vector((x, c.y, c.z)) - Vector(t)).length < 0.05:
                return 'tip'
        return 'belly' if n.z < -0.05 else 'shell'                            # cream underside of the claw
    if c.z < 0.075:
        return 'tip'                                                          # dark leg tips
    if n.z < -0.15:
        return 'belly'
    return 'ridge' if c.z > 0.272 else 'shell'                                # knuckles


def tube(name, path, radii, sides=5, mirror=True, phase=0.0):
    """A low-poly prism along a path: one ring per point, capped."""
    bm = bmesh.new()
    rings, P = [], [Vector(p) for p in path]
    Z = Vector((0, 0, 1))
    for i, (c, r) in enumerate(zip(P, radii)):
        d = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
        w = Z.cross(d)
        w = w.normalized() if w.length > 1e-3 else Vector((1, 0, 0))
        u = d.cross(w).normalized()
        a = [phase + 2 * math.pi * j / sides for j in range(sides)]
        rings.append(ring(bm, [c + (u * math.cos(t) + w * math.sin(t)) * r for t in a]))
    for a_, b_ in zip(rings, rings[1:]):
        bridge(bm, a_, b_, closed=True)
    cap(bm, rings[0]); cap(bm, list(reversed(rings[-1])))
    return object_from_bm(name, bm, mirror=mirror)


def stage3(k, body):
    paint(body, PAL, body_rule)
    dg = bpy.context.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(body, dg)
    pieces = []
    # eye stalks out of the sockets, a black bulb on top
    st = tube('stalk', [(0.070, -0.290, 0.140), (0.075, -0.326, 0.190), (0.082, -0.345, 0.270),
                        (0.088, -0.350, 0.336)], [0.022, 0.019, 0.015, 0.012], sides=5)
    paint(st, PAL, lambda c, n, i: 'ridge' if c.z < 0.2 else 'shell')
    eye = tube('eye', [(0.088, -0.350, 0.318), (0.091, -0.353, 0.348), (0.094, -0.356, 0.382)],
               [0.013, 0.034, 0.010], sides=6, phase=0.5)
    paint(eye, PAL, lambda c, n, i: 'eye')
    pieces += [st, eye]
    # a few bold teeth on the inner edges of the fingers
    bmt = bmesh.new()
    for g, up in (((0.150, -0.612, 0.140), 1), ((0.118, -0.648, 0.150), 1),
                  ((0.150, -0.612, 0.140), -1), ((0.118, -0.648, 0.150), -1)):
        loc, nrm, _, _ = bvh.ray_cast(Vector(g), Vector((0, 0, up)))
        if loc is None:
            say('tooth ray missed', g, up); continue
        w = Vector((0, 0, 1)).cross(nrm)
        w = w.normalized() if w.length > 1e-3 else Vector((1, 0, 0))
        u = nrm.cross(w).normalized()
        base = [loc - nrm * 0.005 + (u * a + w * b) * 0.011 for a, b in ((1, 0), (0, 1), (-1, 0), (0, -1))]
        vs = ring(bmt, base + [loc + nrm * 0.017])
        for j in range(4):
            bmt.faces.new([vs[j], vs[(j + 1) % 4], vs[4]])
        bmt.faces.new(vs[:4])
    teeth = object_from_bm('teeth', bmt)
    paint(teeth, PAL, lambda c, n, i: 'belly')
    pieces.append(teeth)
    # a small barnacle cluster on the rear rim (one side only)
    bmb = bmesh.new()
    for (x, y), h in (((0.055, 0.250), 0.032), ((0.112, 0.228), 0.026), ((0.098, 0.272), 0.021)):
        loc, nrm, _, _ = bvh.ray_cast(Vector((x, y, 0.6)), Vector((0, 0, -1)))
        w = Vector((0, 1, 0)).cross(nrm).normalized()
        u = nrm.cross(w).normalized()
        R = h * 1.05
        rs = []
        for r, off in ((R, -0.008), (R * 0.55, h), (R * 0.3, h * 0.6)):
            rs.append(ring(bmb, [loc + nrm * off + (u * math.cos(t) + w * math.sin(t)) * r
                                 for t in [2 * math.pi * j / 6 + 0.3 for j in range(6)]]))
        bridge(bmb, rs[0], rs[1], closed=True); bridge(bmb, rs[1], rs[2], closed=True)
        cap(bmb, rs[0]); cap(bmb, list(reversed(rs[2])))
    barn = object_from_bm('barnacles', bmb, mirror=False)
    paint(barn, PAL, lambda c, n, i: 'barnacle')
    pieces.append(barn)
    return pieces


LA = ('leg1.L', 'leg3.L', 'leg2.R', 'leg4.R')        # scuttle gait: two alternating groups
LB = ('leg2.L', 'leg4.L', 'leg1.R', 'leg3.R')


def both(d):
    """{bone.L: v} -> the same bone-local values on .R (roll='auto' mirrors the motion)."""
    out = dict(d)
    for b, v in d.items():
        if b.endswith('.L'):
            out[b[:-2] + '.R'] = v
    return out


def stage4(k, body, pieces):
    bones = [('body', J['body_h'], J['body_t'], None)]
    for i in range(1, 5):
        bones += [(f'leg{i}_a.L', J[f'leg{i}_root'], J[f'leg{i}_knee'], 'body'),
                  (f'leg{i}_b.L', J[f'leg{i}_knee'], J[f'leg{i}_bend'], f'leg{i}_a.L', True),
                  (f'leg{i}_c.L', J[f'leg{i}_bend'], J[f'leg{i}_tip'], f'leg{i}_b.L', True)]
    bones += [('claw_a.L', J['claw_root'], J['claw_elbow'], 'body'),
              ('claw_b.L', J['claw_elbow'], J['claw_wrist'], 'claw_a.L', True),
              ('claw_hand.L', J['claw_wrist'], J['claw_palm'], 'claw_b.L', True),
              ('claw_dactyl.L', J['dactyl_root'], J['dactyl_tip'], 'claw_hand.L'),
              ('claw_pollex.L', J['pollex_root'], J['pollex_tip'], 'claw_hand.L')]
    rig = armature(bones, roll='auto')
    skin(body, rig)
    for p in pieces:
        if p.name.endswith('eye'):
            bind(p, rig, bone='body')
        else:
            bind(p, rig, body=body)
    # idle: two claw clicks and a slow breath
    op, sh = (0, 0, -18), (0, 0, 0)
    clip(rig, 'idle', {1: both({'claw_dactyl.L': sh, 'claw_hand.L': sh}),
                       8: both({'claw_dactyl.L': op, 'claw_hand.L': (0, 0, 3)}),
                       12: both({'claw_dactyl.L': sh, 'claw_hand.L': (0, 0, 3)}),
                       18: both({'claw_dactyl.L': op, 'claw_hand.L': (0, 0, 3)}),
                       22: both({'claw_dactyl.L': sh, 'claw_hand.L': sh}),
                       48: both({'claw_dactyl.L': sh, 'claw_hand.L': sh})},
         loc={1: {'body': (0, 0, 0)}, 24: {'body': (0, 0, 0.006)}, 48: {'body': (0, 0, 0)}})
    # move: sideways scuttle, two leg groups lift in turn while the body sways across
    up = lambda g: {f'{b[:4]}_a{b[4:]}': (0, 0, 22) for b in g} | {f'{b[:4]}_c{b[4:]}': (0, 0, -12) for b in g}
    rest0 = {f'{b[:4]}_{s}{b[4:]}': (0, 0, 0) for b in LA + LB for s in 'ac'}
    clip(rig, 'move', {1: dict(rest0), 7: rest0 | up(LA), 13: dict(rest0), 19: rest0 | up(LB), 25: dict(rest0)},
         loc={1: {'body': (0, 0, 0)}, 7: {'body': (-0.025, 0, 0.008)}, 13: {'body': (0, 0, 0)},
              19: {'body': (0.025, 0, 0.008)}, 25: {'body': (0, 0, 0)}})
    # attack: rear up, claws wide open, lunge and snap shut
    z = {'claw_dactyl.L': (0, 0, 0), 'claw_hand.L': (0, 0, 0), 'claw_b.L': (0, 0, 0), 'body': (0, 0, 0)}
    clip(rig, 'attack', {1: both(z),
                         9: both({'claw_dactyl.L': (0, 0, -30), 'claw_hand.L': (0, 0, 12), 'claw_b.L': (0, 0, 8),
                                  'body': (5, 0, 0)}),
                         14: both({'claw_dactyl.L': (0, 0, -32), 'claw_hand.L': (0, 0, 14), 'claw_b.L': (0, 0, 10),
                                   'body': (6, 0, 0)}),
                         17: both({'claw_dactyl.L': (0, 0, 3), 'claw_hand.L': (0, 0, -6), 'claw_b.L': (0, 0, -4),
                                   'body': (-2, 0, 0)}),
                         24: both({'claw_dactyl.L': (0, 0, 3), 'claw_hand.L': (0, 0, -4), 'claw_b.L': (0, 0, -2),
                                   'body': (0, 0, 0)}),
                         32: both(z)},
         loc={1: {'body': (0, 0, 0)}, 14: {'body': (0, -0.02, 0)}, 17: {'body': (0, 0.035, 0)},
              24: {'body': (0, 0.02, 0)}, 32: {'body': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
