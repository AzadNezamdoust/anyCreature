import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from carve import part_guide, part_rings, fit_to_guide

# wolf, stage-1 cage on the PART GUIDE (c3). Form and topology only.
#   spine    10-sided half rings (top seam -> bottom seam), each sized by part_rings and slid onto the guide; they
#            lean with the neck and the shoulder blade, stand square through the waist, lean again into the tail
#   limbs    6-sided, grown out of a 1 x 2 patch of lower-flank faces (col 3: they face down and out) (the shoulder / hip loop is the patch's border,
#            round the joint); every ring = part_rings centre, width and depth at its station, mitred at joints
#   muzzle   6-sided, out of the middle of the face cap (the stop); tail 6-sided out of the middle of the rump cap
#   ears     two tiers out of one skull face (the outline cue)
J = dict(
    pelvis=(0.0, 0.33, 0.60), spine=(0.0, -0.05, 0.62), chest=(0.0, -0.19, 0.66), neck=(0.0, -0.41, 0.73),
    head=(0.0, -0.62, 0.87), snout=(0.0, -0.845, 0.79),
    tail0=(0.0, 0.46, 0.55), tail1=(0.0, 0.62, 0.38), tail2=(0.0, 0.83, 0.17),
    shoulderL=(0.106, -0.29, 0.56), elbowL=(0.106, -0.285, 0.345), wristL=(0.112, -0.31, 0.135),
    pawL=(0.117, -0.42, 0.03),
    hipL=(0.105, 0.30, 0.56), kneeL=(0.105, 0.285, 0.345), hockL=(0.105, 0.415, 0.235),
    toeL=(0.108, 0.36, 0.03),
)
PLAN = dict(spine=['pelvis', 'spine', 'chest', 'neck', 'head', 'snout'],
            limbs=dict(fore=['shoulderL', 'elbowL', 'wristL', 'pawL'], hind=['hipL', 'kneeL', 'hockL', 'toeL']),
            extra=[['tail0', 'tail1', 'tail2']])
META = dict(creature='wolf', model='opus', cage=True, J=J, plan=PLAN, intended={},
            landmarks=dict(eye=(0.062, -0.705, 0.845), mouth=(0.030, -0.775, 0.765)),
            # waiver: the sheet's front view draws the cheek ruff 0.40 m wide, its top view 0.345 m (the profile and the
            # neck / head ratio come from the top view), and has no tail between the legs (the side view has one)
            iou_floor=dict(front=0.83))

X = Vector((1, 0, 0))


class Tab:
    """A part's stations from part_rings (dense), read at any t or at a centre y."""

    def __init__(self, gp, part, label=None):
        self.R = part_rings(gp, part, 81, ends=True)
        self.t = np.array([r['t'] for r in self.R])
        self.c = np.array([r['centre'] for r in self.R])
        self.w = np.array([r['width'] for r in self.R])
        self.d = np.array([r['depth'] for r in self.R])
        self.p = np.array([r['p'] for r in self.R])
        if part == 'torso':                              # the part base reads no torso width where a limb root or the ruff
            bad = self.w < 0.15                          # covers the plan view (0.001): a design width there, the guide fit sets it
            self.w = np.where(bad, np.where(self.c[:, 1] > 0, 0.30, 0.35), self.w)
        if label:
            for i in range(0, 81, 8):
                say('tab %s t %.3f c (%.3f %.3f %.3f) w %.3f d %.3f p %.2f' % (label, self.t[i], *self.c[i], self.w[i], self.d[i], self.p[i]))

    def at(self, t):
        f = lambda a: float(np.interp(t, self.t, a))
        return dict(c=Vector((f(self.c[:, 0]), f(self.c[:, 1]), f(self.c[:, 2]))), w=f(self.w), d=f(self.d), p=f(self.p))

    def at_y(self, y):
        i = int(np.argmin(np.abs(self.c[:, 1] - y)))
        j = min(max(i + (1 if (self.c[min(i + 1, 80), 1] - self.c[i, 1]) * (y - self.c[i, 1]) > 0 else -1), 0), 80)
        if i == j or abs(self.c[j, 1] - self.c[i, 1]) < 1e-9:
            return self.at(self.t[i])
        f = (y - self.c[i, 1]) / (self.c[j, 1] - self.c[i, 1])
        return self.at(self.t[i] + min(max(f, 0.0), 1.0) * (self.t[j] - self.t[i]))


def swell(rg, c, sw, sd):
    """The sheet's own size where the guide reads it smaller (the ruff): widths x sw, in-plane heights x sd about c."""
    for v in rg:
        v.co.x *= sw
        v.co.y = c.y + (v.co.y - c.y) * sd
        v.co.z = c.z + (v.co.z - c.z) * sd


def sring(bm, r, lean, angs, sw=1.0, sd=1.0):
    """A spine half ring in the plane through r['c'] whose top leans back by `lean` degrees: seam top, the
    vertices at `angs` (degrees from the top) on the part's superellipse, seam bottom."""
    c, W, D, p = r['c'], r['w'] * sw, r['d'] * sd, r['p']
    ph = math.radians(lean)
    wy, wz = math.sin(ph), math.cos(ph)
    pts = []
    for a in [0.0] + list(angs) + [180.0]:
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        x = 0.0 if a in (0.0, 180.0) else W / 2 * abs(sa) ** (2 / p)
        h = D / 2 * math.copysign(abs(ca) ** (2 / p), ca)
        pts.append((x, c.y + wy * h, c.z + wz * h))
    return ring(bm, pts)


def fit(rg, guide, c, mm=0.06, keep=()):
    old = {i: rg[i].co.copy() for i in keep}
    out = fit_to_guide(rg, guide, max_move=mm, centre=c)
    for i, co in old.items():
        rg[i].co = co
    return out


def lring(bm, tab, chain, t, shear=0.0, sw=1.0, sd=1.0, a=0.6, zmin=None, dc=(0, 0, 0), fan=0.0):
    """A 6-sided limb ring at station t of the part: centre, width and depth from part_rings, in the plane
    square to the bone (mitred within 7 cm of a joint). Roles OF OM OB IB IM IF (outer / inner, front / back).
    shear lifts the outer side and drops the inner side (the first ring under the body); fan lifts the front edge
    and drops the back edge (the rings of a joint open like a fan on its flexion side, so the bend has slack)."""
    P = [Vector(J[n]) for n in chain]
    L = [(b - a_).length for a_, b in zip(P, P[1:])]
    D_ = [(b - a_).normalized() for a_, b in zip(P, P[1:])]
    tot = sum(L)
    cum = [0.0]
    for l in L:
        cum.append(cum[-1] + l)
    dist = t * tot
    bi = max(i for i in range(len(L)) if dist >= cum[i] - 1e-9)
    d = D_[bi]
    tau = d.copy()
    for ji in range(1, len(P) - 1):
        dj = dist - cum[ji]
        if abs(dj) < 0.07:
            other = D_[ji - 1] if dj >= 0 else D_[ji]
            wgt = 0.5 * (1 - abs(dj) / 0.07)
            tau = (d * (1 - wgt) + other * wgt).normalized()
    u = (X - tau * X.dot(tau)).normalized()
    w = tau.cross(u).normalized()                       # forward on a hanging bone; never flipped along the limb
    r = tab.at(t)
    c = r['c'] + Vector(dc)
    W, Dp = r['w'] * sw, r['d'] * sd / max(0.8, tau.dot(d))
    pts = []
    for uc, wc in ((a, 1), (1, 0), (a, -1), (-a, -1), (-1, 0), (-a, 1)):
        q = c + u * (uc * W / 2) + w * (wc * Dp / 2) - tau * (shear * uc + fan * wc)
        if zmin is not None and q.z < zmin + 0.012:
            q.z = zmin
        pts.append(q)
    return ring(bm, pts)


def limb(bm, root, rings, cap_at=None):
    """root -> rings (each 6 in role order), closed bands; the end closed with two quads."""
    seq = [root] + rings
    for a_, b in zip(seq, seq[1:]):
        bridge(bm, a_, b, closed=True)
    e = seq[-1]
    bm.faces.new([e[1], e[2], e[3], e[4]])
    bm.faces.new([e[1], e[4], e[5], e[0]])
    return seq


def between(bm, a_, b, f, do=(0.03, 0, 0), di=(0, 0, -0.04)):
    """The shoulder / haunch ring between the root loop and the first free ring: outer side proud, inner side low."""
    pts = []
    for i, (p, q) in enumerate(zip(a_, b)):
        m = p.co.lerp(q.co, f) + Vector(do if i < 3 else di)
        if i >= 3:
            m.x = p.co.x + (q.co.x - p.co.x) * 0.8       # the inner side comes in under the body at once
        pts.append(m)
    return ring(bm, pts)


# ---- the spine: (name, part, where, lean, angles, vertices NOT fitted) front -> back
A10 = (35, 72, 110, 152)
A10P = (35, 68, 101, 152)                                       # patch rings: the limb's upper edge higher, over the joint
SPINE = [
    ('HC', 'head', 0.34, -12, (30, 62, 112, 150), (), (1.02, 0.88)),        # brow / cheek ring: the face cap closes it
    ('HC2', 'head', 0.06, 4, (35, 70, 110, 150), (), (1.14, 1.0)),         # cranium, widest
    ('N1', 'neck', 0.72, 24, A10, (), (1.02, 1.0)),              # back of the skull / jaw ruff
    ('N2', 'neck', 0.50, 30, A10, (), (1.02, 1.03)),
    ('A', 'neck', 0.30, 30, A10, (), (1.05, 1.08)),               # neck loops: A and B either side of the joint, 0.13 m apart
    ('B', 'torso', -0.385, 29, A10, (), (1.10, 1.06)),
    ('C1', 'torso', -0.306, 28, (34, 63, 90, 152), (4, 5), (1.15, 1.0)),     # shoulder patch C1..C3 (col 3); its front corner (the pole) up on the blade
    ('C2', 'torso', -0.210, 28, (35, 67, 98, 152), (4, 5), (1.10, 1.0)),
    ('C3', 'torso', -0.115, 24, A10P, (4, 5)),
    ('W1', 'torso', -0.030, 12, A10, ()),
    ('W2', 'torso', 0.050, 3, A10, ()),
    ('D0', 'torso', 0.110, -2, A10P, (4, 5)),                    # hip patch D0..D2 (col 3), 6 cm forward: one plain face between it and the tail collar
    ('D1', 'torso', 0.220, 4, A10P, (4, 5)),
    ('D2', 'torso', 0.325, 2, A10P, (4, 5)),
    ('R', 'extra0', 0.10, 30, (30, 65, 115, 150), (3, 4, 5)),          # rump collar, square to the tail: the tail leaves its middle
]
MUZZLE = [(0.95, 0.80, 0.0), (0.74, 1.0, 0.004), (0.52, 1.0, 0.028)]               # head t (nose end sized as t - 0.07: blunt), front -> back
TAIL = [(0.33, 0.33, 1.0), (0.56, 0.56, 1.0), (0.76, 0.76, 1.0), (0.93, 0.93, 1.0), (1.05, 0.93, 0.65)]   # centre t, size t, scale
# t, shear, width x, depth x[, fan].  fore: upper-arm ring, 3 elbow loops (0.297 / 0.371 / 0.445), forearm, 2 wrist loops, paw
FORE = [(0.17, 0.03, 0.92, 1.13), (0.297, 0, 0.95, 1, -0.012), (0.371, 0, 1, 1), (0.445, 0, 1, 1, 0.012), (0.659, 0, 1, 1, -0.01), (0.806, 0, 1, 1, 0.01), (0.93, 0, 1.12, 1), (1.06, 0, 0.85, 0.75)]
# hind: thigh ring, 3 stifle loops, 3 hock loops, metatarsus, paw. Joint rings sit TIGHT on the flexion side (fan):
# the crease faces of an 80 degree bend fold whatever their size, so they are kept small
HIND = [(0.17, 0.02, 1, 0.95), (0.265, 0.0, 1, 1.12, 0.012), (0.36, 0, 1, 0.85), (0.455, 0, 1, 0.93, -0.012), (0.585, 0, 1, 0.9), (0.645, 0, 1, 0.88), (0.705, 0, 1, 0.94), (0.85, 0, 1, 1), (0.94, 0, 1.12, 1), (1.0, 0, 1.12, 1)]


def stage1(k):
    guide = part_guide(k)
    gp = k.guide_parts
    dbg = bool(os.environ.get('WOLF_TAB'))
    T = {n: Tab(gp, n, n if dbg else None) for n in ('torso', 'neck', 'head', 'fore', 'hind', 'extra0')}
    if dbg:
        for n, P in gp.items():
            if isinstance(P, dict):
                say('part', n, P.get('kind'), P.get('joints'), [(k_, v) for k_, v in P.items() if k_ != 'stations'])
            else:
                say('part', n, P)
            if isinstance(P, dict) and 'stations' in P:
                part_rings(gp, n, label=n)
    bm = bmesh.new()

    # ---- spine rings
    idx, rings = {}, []
    for i, spec in enumerate(SPINE):
        nm, part, where, lean, angs, keep = spec[:6]
        r = T[part].at_y(where) if part == 'torso' else T[part].at(where)
        rg = sring(bm, r, lean, angs, *((1.2, 0.85) if nm == 'R' else (1.0, 1.0)))
        if keep and nm != 'R':                           # under a limb patch: the keel / groin by design
            zb = rg[5].co.z
            rg[4].co = Vector((0.050, rg[5].co.y + 0.01, zb + 0.060))
        res = fit(rg, guide, r['c'], 0.03 if nm == 'R' else 0.06, keep)
        if len(spec) > 6:
            swell(rg, r['c'], *spec[6])
        if dbg:
            say('ring', nm, res, [tuple(round(q, 3) for q in v.co) for v in rg])
        idx[nm] = i
        rings.append(rg)
    bands = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    R = lambda nm, j: rings[idx[nm]][j]

    # ---- muzzle: 6-sided, out of the middle of the face cap
    mz = []
    for t, s, jaw in MUZZLE:
        r = T['head'].at(t)
        if s != 1.0:
            r = dict(T['head'].at(t - 0.07), c=r['c'])
        rg = sring(bm, r, -19.5, (45, 112))
        fit(rg, guide, r['c'], 0.03)
        swell(rg, r['c'], 1.15 if s == 1.0 else 1.0, 1.0)
        rg[2].co.z -= jaw * 0.6                          # the lower jaw: a plane of its own under the muzzle root
        rg[3].co.z -= jaw
        mz.append(rg)
    bm.faces.new(mz[0])                                  # nose end: one quad per half
    for a_, b in zip(mz, mz[1:]):
        bridge(bm, a_, b)
    HC = rings[idx['HC']]
    f1 = bm.verts.new(HC[0].co.lerp(mz[-1][0].co, 0.5))
    f2 = bm.verts.new(HC[5].co.lerp(mz[-1][3].co, 0.5))
    bm.faces.new([HC[0], HC[1], HC[2], f1])              # forehead
    bm.faces.new([f2, HC[3], HC[4], HC[5]])              # under the jaw
    bridge(bm, mz[-1], [f1, HC[2], HC[3], f2])           # the stop; its side face is the eye plane (the eye loop is a stage-2 inset)

    # ---- tail: 6-sided, out of the middle of the rump cap
    tl = []
    for t, ts, sc in TAIL:
        r = dict(T['extra0'].at(ts), c=T['extra0'].at(t)['c'])
        rg = sring(bm, r, 46, (55, 125), sc, sc)
        if sc == 1.0:
            fit(rg, guide, r['c'], 0.03)
        tl.append(rg)
    RR = rings[idx['R']]
    s1 = bm.verts.new(RR[0].co.lerp(tl[0][0].co, 0.3))
    s2 = bm.verts.new(RR[5].co.lerp(tl[0][3].co, 0.3))
    bm.faces.new([RR[0], RR[1], RR[2], s1])
    bm.faces.new([s2, RR[3], RR[4], RR[5]])
    bridge(bm, [s1, RR[2], RR[3], s2], tl[0])
    for a_, b in zip(tl, tl[1:]):
        bridge(bm, a_, b)
    bm.faces.new(tl[-1])

    # ---- limbs: out of the flank patch (col 2 of two bands); the patch border is the shoulder / hip loop
    def grow(names, part, chain, specs, zmin):
        a_, b, c = names
        bmesh.ops.delete(bm, geom=[bands[idx[a_]][3], bands[idx[b]][3]], context='FACES')
        root = [R(a_, 3), R(b, 3), R(c, 3), R(c, 4), R(b, 4), R(a_, 4)]
        rs = [lring(bm, T[part], chain, sp[0], shear=sp[1], sw=sp[2], sd=sp[3], zmin=zmin, fan=sp[4] if len(sp) > 4 else 0.0) for sp in specs]
        return limb(bm, root, rs)

    fore = grow(('C1', 'C2', 'C3'), 'fore', PLAN['limbs']['fore'], FORE, 0.0)
    hind = grow(('D0', 'D1', 'D2'), 'hind', PLAN['limbs']['hind'], HIND, None)
    if dbg:
        for nm_ in ('B', 'C1', 'C2', 'C3'):
            say('sp', nm_, [tuple(round(q, 3) for q in v.co) for v in rings[idx[nm_]]])
        for rg in fore[:3]:
            say('fore', [tuple(round(q, 3) for q in v.co) for v in rg])
        for rg in hind:
            say('hind', [tuple(round(q, 3) for q in v.co) for v in rg])
    sole = [v for v in hind[-1]]
    for v in sole:                                       # hind sole: the last ring flat on the ground
        v.co.z = 0.0

    # ---- ears: two tiers out of the skull face behind the brow corner
    bmesh.ops.delete(bm, geom=[bands[idx['HC2']][1]], context='FACES')
    e0 = [R('HC2', 1), R('HC2', 2), R('N1', 2), R('N1', 1)]
    e1 = ring(bm, [(0.052, -0.590, 1.035), (0.120, -0.580, 1.010), (0.122, -0.505, 1.020), (0.058, -0.500, 1.045)])
    e2 = ring(bm, [(0.074, -0.562, 1.100), (0.110, -0.556, 1.091), (0.112, -0.519, 1.089), (0.079, -0.517, 1.098)])
    bridge(bm, e0, e1, closed=True)
    bridge(bm, e1, e2, closed=True)
    bm.faces.new(e2)

    snap_seam(bm)
    body = object_from_bm('body', bm)
    if os.environ.get('WOLF_ROM'):
        dbg_rom(k, body)
    if os.environ.get('WOLF_DBG'):
        dbg_loops(body, os.environ['WOLF_DBG'])
    return body


def dbg_rom(k, body):
    """Debug only (WOLF_ROM=1): which faces fold over in each range-of-motion pose (rest centres)."""
    import techqa as Q
    Jc, plan = cage_plan(k.meta)
    cen = [tuple(round(q, 3) for q in p.center) for p in body.data.polygons]
    rig = proxy_rig(Jc, plan)
    skin(body, rig)
    for pn, keys in rom_poses(Jc, plan).items():
        act = clip(rig, 'rom_' + pn, {1: keys, 2: keys})
        counts, flags, tris = Q.measure(body, [], (1.7, 1.7, 1.1), rig, {pn: act})
        say('ROM', pn, {c: n for c, n in counts[body.name].items() if n}, sorted(cen[i] for i, c in flags[body.name].items() if c == 'flip' and i < len(cen)))


def dbg_loops(body, jn):
    e = evaluated_bm(body)
    c = next(c for c in [PLAN['spine']] + list(PLAN['limbs'].values()) if jn in c)
    i, j = c.index(jn), Vector(J[jn])
    ds = [j - Vector(J[c[i - 1]]), Vector(J[c[i + 1]]) - j]
    band = 0.4 * min(d.length for d in ds)
    for axis in [d.normalized() for d in ds] + [sum((d.normalized() for d in ds), Vector()).normalized()]:
        nb = {}
        for ed in e.edges:
            a_, b = ed.verts[0].co, ed.verts[1].co
            d = b - a_
            if d.length < 1e-9 or abs(d.dot(axis)) / d.length > 0.6 or abs(((a_ + b) / 2 - j).dot(axis)) > 2 * band:
                continue
            nb.setdefault(ed.verts[0], []).append(ed.verts[1]); nb.setdefault(ed.verts[1], []).append(ed.verts[0])
        seen = set()
        for v in nb:
            if v in seen:
                continue
            comp, st = [], [v]
            seen.add(v)
            while st:
                x = st.pop(); comp.append(x)
                for y in nb[x]:
                    if y not in seen:
                        seen.add(y); st.append(y)
            m = sum((x.co - j).dot(axis) for x in comp) / len(comp)
            cc = sum((x.co for x in comp), Vector()) / len(comp)
            say('DBG', jn, 'axis', tuple(round(q, 2) for q in axis), 'band %.3f' % band, 'comp', len(comp), 'mean %.3f' % m, 'at', tuple(round(q, 3) for q in cc))
            if len(comp) == 12 and cc.x > 0.05:
                cs = set(comp)
                for ed in e.edges:
                    if ed.verts[0] in cs and ed.verts[1] in cs:
                        d = ed.verts[1].co - ed.verts[0].co
                        if abs(d.dot(axis)) > 0.015:
                            say('DBGE', tuple(round(q, 3) for q in ed.verts[0].co), tuple(round(q, 3) for q in ed.verts[1].co), round(abs(d.dot(axis)) / d.length, 2))
    e.free()


run(META, stage1)
