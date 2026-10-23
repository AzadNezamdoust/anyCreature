import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kit')))
from bmkit import *
import parts as PT

# t7 hand box model (zoo workflow v2), template zoo/elephant: one spine loft of 14-vertex half rings (tail tip -> rear
# wall -> hind-leg window -> barrel -> fore-leg window -> neck -> head -> beak). Under the shell the loft is the body
# dome (hidden) over a short skin/plastron band; the four column legs are extruded from BROAD 4 x 4-face windows on
# the plastron edge through a 45 %-inset transition ring (elephant's leg-root trick). The carapace is a SEATED piece
# (stage 3) built on its own hexagon-plate topology: a centre hexagon, a ring of six plates and 18 marginals, each
# plate a groove ring + a raised plateau, so every colour border runs along a plate's own edge loop.
META = dict(creature='turtle', model='opus', stage1_tris=(1600, 4200), total_tris=(2200, 6000),
            closeups=[('head', (0.0, -0.62, 0.63), 0.20, 'hero'),
                      ('shell rim + fore leg', (0.33, -0.22, 0.28), 0.22, 'hero'),
                      ('hind leg', (0.33, 0.56, 0.22), 0.22, 'back34'),
                      ('tail', (0.0, 0.76, 0.25), 0.15, 'back34')])

# the skeleton (x >= 0 half; .L on +X), fitted to reference/side.png + front.png (height 0.9 m, length 1.47 m)
J = dict(
    hips=(0.0, 0.62, 0.40), chest=(0.0, 0.15, 0.44), chest2=(0.0, -0.30, 0.46),
    neck=(0.0, -0.36, 0.47), neck1=(0.0, -0.45, 0.56), head=(0.0, -0.53, 0.62), face=(0.0, -0.735, 0.625),
    tail0=(0.0, 0.745, 0.25), tail1=(0.0, 0.785, 0.20), tail2=(0.0, 0.83, 0.13),
    shoulder=(0.275, -0.245, 0.26), wrist=(0.275, -0.25, 0.08), ftoe=(0.28, -0.37, 0.0),
    hipL=(0.275, 0.55, 0.24), hock=(0.275, 0.56, 0.08), htoe=(0.28, 0.45, 0.0),
)

NV = 14


def lerp_tab(tab, y):
    if y <= tab[0][0]:
        return tab[0][1]
    for (a, va), (b, vb) in zip(tab, tab[1:]):
        if y <= b:
            return va + (vb - va) * (y - a) / (b - a)
    return tab[-1][1]


# ---------------------------------------------------------------- the carapace as an analytic dome (side + plan)
ZTOP = [(-0.33, 0.655), (-0.30, 0.69), (-0.25, 0.735), (-0.20, 0.78), (-0.153, 0.81), (-0.063, 0.845), (0.006, 0.875),
        (0.117, 0.897), (0.241, 0.888), (0.33, 0.862), (0.414, 0.818), (0.519, 0.73), (0.605, 0.615), (0.67, 0.49),
        (0.71, 0.40), (0.735, 0.335)]                                           # shell top line (side view)
ZRIM = [(-0.33, 0.655), (-0.30, 0.605), (-0.25, 0.525), (-0.20, 0.465), (-0.15, 0.415), (-0.10, 0.375), (0.0, 0.325),
        (0.10, 0.305), (0.25, 0.295), (0.40, 0.295), (0.55, 0.305), (0.65, 0.318), (0.735, 0.335)]   # rim height
SY0, SYF, SYR, SW, SEF, SER = 0.16, -0.33, 0.735, 0.405, 2.8, 3.2   # s4 r27: fuller rear (was 2.4)
PD = 2.3                                                                        # dome section exponent
FLARE = 0.03                                                                    # marginals flare out at the rim


def Wr(y):
    """Plan half-width of the shell's dome at y (the rim before the flare)."""
    if y <= SYF or y >= SYR:
        return 0.0
    a, e = (SY0 - SYF, SEF) if y < SY0 else (SYR - SY0, SER)
    d = abs(y - SY0) / a
    return SW * max(0.0, 1 - d ** e) ** (1 / e)


def Zt(y):
    return lerp_tab(ZTOP, y)


def Zr(y):
    return lerp_tab(ZRIM, y)


def zs(x, y):
    """Shell (outer) dome height over the plan point (x, y)."""
    w = Wr(y)
    zr, zt = Zr(y), Zt(y)
    if w <= 1e-6:
        return zr
    u = min(1.0, abs(x) / w)
    return zr + (zt - zr) * max(0.0, 1 - u ** PD) ** (1 / PD)


# ---------------------------------------------------------------- body sections
def resample(poly, n):
    """n points evenly spaced by arc length along a polyline (ends kept)."""
    L = [0.0]
    for a, b in zip(poly, poly[1:]):
        L.append(L[-1] + math.dist(a, b))
    out = []
    for k in range(n):
        s = L[-1] * k / (n - 1)
        for i in range(len(poly) - 1):
            if s <= L[i + 1] + 1e-12:
                t = (s - L[i]) / max(L[i + 1] - L[i], 1e-12)
                out.append(tuple(poly[i][c] + (poly[i + 1][c] - poly[i][c]) * t for c in range(2)))
                break
    return out


LOWX = (0.93, 0.78, 0.62, 0.46, 0.33, 0.16, 0.0)    # s4 r4: j7 off j6 (r3: 6 mm strip)


def body_xz(st):
    """A body half ring (x, z), top seam -> bottom seam, 14 points: j0..j6 the dome (hidden under the shell) and the
    tuck under the rim, resampled by arc length; j6 = (ws, zs) the flank under the rim (the colour border loop); j7..j13
    the plastron edge quarter to the bottom seam (the leg windows are j7..j11)."""
    zt, zr, wd, ws, zs_, zb = st['zt'], st['zr'], st['wd'], st['ws'], st['zs'], st['zb']
    p, q = st.get('p', PD), st.get('q', 2.0)
    up = []
    for k in range(25):
        t = (math.pi / 2) * k / 24
        up.append((wd * math.sin(t) ** (2 / p), zr + (zt - zr) * math.cos(t) ** (2 / p)))
    if st.get('tuck'):
        up.append((wd + 0.01, zr - st['tuck']))
    if st.get('bulge'):                 # s4 r13: a convex shoulder between the dome edge and the flank point
        up.append((wd + 0.70 * (ws - wd), zr - 0.30 * (zr - zs_)))
    up.append((ws, zs_))
    pts = resample(up, 7)
    for f in LOWX:              # s4 r2: placed x fractions, so the leg window j7..j11 spans the leg (0.13-0.39)
        pts.append((ws * f, zs_ - (zs_ - zb) * (1 - f ** q) ** (1 / q)))
    pts[0] = (0.0, pts[0][1])
    return pts


def shell_st(y, ws, zs_, zb=0.19, tuck=None, bulge=None, **kw):
    """A station under the shell: dome 2.5 cm inside the shell top, 3.5 cm inside its rim."""
    st = dict(zt=Zt(y) - 0.025, zr=Zr(y), wd=Wr(y) - 0.035, ws=ws, zs=zs_, zb=zb)
    if tuck:
        st['tuck'] = tuck
    if bulge:
        st['bulge'] = bulge
    st.update(kw)
    return st


def bsec(nm, y, st):
    return ('B', nm, y, st)


def prof(nt, nb, taper=1.0, nv=NV):
    """A superellipse half ring, top seam -> bottom seam (elephant's)."""
    out = []
    for j in range(nv):
        t = math.pi * j / (nv - 1)
        c, s = math.cos(t), math.sin(t)
        n = nt if c >= 0 else nb
        fx = abs(s) ** (2 / n) if j not in (0, nv - 1) else 0.0
        fh = math.copysign(abs(c) ** (2 / n), c)
        if c < 0:
            fx *= 1 - (1 - taper) * abs(c)
        out.append((round(fx, 4), round(fh, 4)))
    return out


NECK = prof(2.4, 2.3, 0.85)
HEAD = prof(2.6, 2.4, 0.80)
TAIL = prof(2.2, 2.2, 0.85, nv=6)


def tb(nm, top, bot, W, pr):
    (yt, zt), (yb, zb) = top, bot
    c = ((yt + yb) / 2, (zt + zb) / 2)
    h = math.hypot(yt - yb, zt - zb) / 2
    a = math.degrees(math.atan2(yt - yb, zt - zb))
    return ('T', nm, c, round(a, 2), h, h, W, pr)


def tc(nm, c, a, h, W, pr):
    return ('T', nm, c, a, h, h, W, pr)


def sec_pts(s):
    if s[0] == 'S':
        _k, _nm, src, cz, kx, kz, (py, pz), a = s
        sn, co = math.sin(math.radians(a)), math.cos(math.radians(a))
        return [(x * kx, py + (z - cz) * kz * sn, pz + (z - cz) * kz * co) for x, y, z in sec_pts(SECS[NAMES.index(src)])]
    if s[0] == 'M':
        _k, _nm, a, b, t = s
        A, B = sec_pts(SECS[NAMES.index(a)]), sec_pts(SECS[NAMES.index(b)])
        return [tuple(p + (q - p) * t for p, q in zip(u, v)) for u, v in zip(A, B)]
    if s[0] == 'B':
        _k, _nm, y, st = s
        return [(x, y, z) for x, z in body_xz(st)]
    _k, _nm, c, a, T, B, W, pr = s
    y0, z0 = c
    sn, co = math.sin(math.radians(a)), math.cos(math.radians(a))
    out = []
    for fx, fh in pr:
        h = fh * (T if fh >= 0 else B)
        out.append((fx * W, y0 + h * sn, z0 + h * co))
    return out


SECS = [
    # the tail, tip -> root: a short cone pointing back and down under the rear rim (6-vertex rings)
    # s4 r22: the rump closes as ONE flat skin wall under the rear rim: RW, RW2 (in-between) and RX (RW scaled 0.25
    # about the tail root) in the plane y 0.733, closed with a fan; the short tail is a seated cone piece (stage 3).
    # r17-r21: every lofted tail root (14 -> 6 bridge, oval or round rings) left thin creased triangles on the wall.
    ('S', 'RX', 'RW', 0.240, 0.25, 0.25, (0.733, 0.240), 0),
    ('M', 'RW2', 'RW', 'RX', 0.5),
    bsec('RW', 0.733, dict(zt=0.305, zr=0.262, wd=0.252, ws=0.280, zs=0.234, zb=0.170, p=2.2)),   # r21 oval; r25 narrower
    # hind-leg window rings (rear -> front): the thigh tops tuck under the rim, then bulge out
    bsec('P4', 0.700, shell_st(0.700, 0.355, 0.230, 0.195, tuck=0.05)),
    bsec('P3', 0.625, shell_st(0.625, 0.385, 0.232, 0.19, tuck=0.05)),
    bsec('P2', 0.550, shell_st(0.550, 0.390, 0.235, 0.19, tuck=0.05)),
    bsec('P1', 0.475, shell_st(0.475, 0.390, 0.238, 0.19, tuck=0.05)),
    bsec('P0', 0.400, shell_st(0.400, 0.385, 0.242, 0.19, tuck=0.05)),
]
for _y in (0.33, 0.257, 0.184, 0.111, 0.038, -0.035):
    _w = Wr(_y) - 0.035
    SECS.append(bsec(f'M{len(SECS)}', _y, shell_st(_y, _w + 0.012, Zr(_y) - 0.05)))
SECS += [
    # fore-leg window rings (rear -> front): the shoulders bulge out of the front opening under the rim
    bsec('F0', -0.105, shell_st(-0.105, 0.385, 0.300, 0.19, tuck=0.06)),
    bsec('F1', -0.175, shell_st(-0.175, 0.390, 0.310, 0.19, bulge=1)),
    bsec('F2', -0.245, shell_st(-0.245, 0.390, 0.315, 0.19, bulge=1)),
    bsec('F3', -0.315, dict(zt=0.585, zr=0.312, wd=0.381, ws=0.385, zs=0.31, zb=0.195, p=2.0)),   # r13: arc
    bsec('F4', -0.385, dict(zt=0.635, zr=0.302, wd=0.366, ws=0.37, zs=0.30, zb=0.205, p=2.0)),   # r12: round shoulders
    # s1 r4: the chest front between the shoulders and the neck (r3: F4 -> N0 quads 0.37 -> 0.125 m: slivers)
    ('M', 'F5', 'F4', 'N0', 0.5),      # s4 r3: the chest front = a straight in-between of F4 and N0 (density rule 3.2)
    # the neck: thick, rising forward out of the front opening, the throat folds below
    # s4 r11: N0 a tall chest / neck-base ring (down to the plastron lobe, 0.21 wide): F4 -> N0 shrinks across its
    # rings, not along them (r10: the shoulder band's vertices slid along the ring tangent: 9 mm sheared strips)
    tb('N0', (-0.442, 0.677), (-0.428, 0.262), 0.205, prof(2.6, 2.6, 0.92)),
    tb('N1', (-0.478, 0.697), (-0.492, 0.420), 0.140, NECK),
    tb('N2', (-0.505, 0.707), (-0.535, 0.49), 0.108, NECK),
    # the head: a rounded skull, the eye on K2, the dark beak K4-K5
    tb('K0', (-0.548, 0.716), (-0.575, 0.508), 0.104, HEAD),
    tb('K1', (-0.598, 0.713), (-0.620, 0.522), 0.100, HEAD),
    tb('K2', (-0.648, 0.700), (-0.662, 0.535), 0.092, HEAD),
    tb('K3', (-0.690, 0.680), (-0.695, 0.550), 0.078, HEAD),
    tb('K4', (-0.720, 0.658), (-0.718, 0.565), 0.058, HEAD),
    tb('K5', (-0.735, 0.640), (-0.733, 0.592), 0.032, HEAD),
]
NAMES = [s[1] for s in SECS]

# leg sections: (cx, cy, z, rx, ry, exponent): level rounded boxes, short thick columns, the foot flaring
FORE = [(0.262, -0.242, 0.145, 0.121, 0.127, 2.4),    # s4 r8: top inside the window rim (2 x 45 deg)
        (0.262, -0.244, 0.118, 0.126, 0.134, 2.4),    # s1 r5: thicker columns (sheet front view 0.26 m wide)
        (0.263, -0.245, 0.092, 0.120, 0.130, 2.4),     # wrist
        (0.265, -0.252, 0.045, 0.130, 0.140, 2.3),
        (0.267, -0.258, 0.0, 0.136, 0.146, 2.3)]
HIND = [(0.262, 0.552, 0.145, 0.122, 0.132, 2.4),
        (0.262, 0.554, 0.118, 0.128, 0.140, 2.4),
        (0.263, 0.556, 0.092, 0.122, 0.134, 2.4),
        (0.265, 0.560, 0.045, 0.131, 0.143, 2.3),
        (0.267, 0.563, 0.0, 0.137, 0.149, 2.3)]
T1_LEG = 0.45
LJ = 7                           # leg windows: ring vertices j7 (outer) .. j11 (inner), 4 faces round, 4 spans long


def akey(t):
    return round(t if t < math.pi - 1e-6 else -math.pi, 4)


def role_pos(sec, u, s, amap=None):
    cx, cy, z, rx, ry, n = sec[:6]
    if abs(u) > 0.999 or abs(s) > 0.999:
        th = math.atan2(s, u)
        if amap:
            th = amap[akey(th)]
        c, sn = math.cos(th), math.sin(th)
        return Vector((cx + rx * math.copysign(abs(c) ** (2 / n), c), cy + ry * math.copysign(abs(sn) ** (2 / n), sn), z))
    return Vector((cx + u * rx * 0.85, cy + s * ry * 0.85, z))


def _step(bm, faces, roles, place):
    r = extrude(bm, faces)
    new = []
    for v in r['verts']:
        o = min(roles, key=lambda o_: (o_[0] - v.co).length)
        new.append((v, o))
    for v, (p0, ro) in new:
        v.co = place(p0, ro)
    return r['faces'], [(v.co.copy(), ro) for v, (p0, ro) in new]


def grow(bm, rings, spans, i0, j0, A, B, secs, t1):
    """Extrude the A x B face window section by section (elephant's grow): the first new ring slopes from the window
    rim t1 of the way to secs[0] (the broad transition), then one ring per section."""
    faces = [spans[i0 + a][j0 + b] for a in range(A) for b in range(B)]
    G = [[rings[i0 + a][j0 + b] for b in range(B + 1)] for a in range(A + 1)]
    su = 1 if G[A // 2][0].co.x > G[A // 2][B].co.x else -1
    ss = 1 if G[0][B // 2].co.y > G[A][B // 2].co.y else -1
    roles = [(G[a][b].co.copy(), (su * (1 - 2 * b / B), ss * (1 - 2 * a / A))) for a in range(A + 1) for b in range(B + 1)]
    th = sorted({akey(math.atan2(s_, u_)) for _p, (u_, s_) in roles if abs(u_) > 0.999 or abs(s_) > 0.999})
    N = len(th)
    off = 0.0 if any(abs(t) < 1e-6 for t in th) else math.pi / N
    base = min(range(N), key=lambda i: abs(th[i] - (-math.pi + off)))
    amap = {th[(base + i) % N]: -math.pi + off + 2 * math.pi * i / N for i in range(N)}
    rp = lambda sec, u_, s_: role_pos(sec, u_, s_, amap)

    def first(p0, ro):
        q = role_pos(secs[0], *ro)
        return p0 + (q - p0) * t1
    faces, roles = _step(bm, faces, roles, first)
    for sec in secs:
        faces, roles = _step(bm, faces, roles, lambda p0, ro, sec=sec: rp(sec, *ro))
    return faces


def bridge_rows(bm, a, b):
    """Quads and triangles between two OPEN rows of different lengths (elephant's)."""
    na, nb = len(a) - 1, len(b) - 1
    i = j = 0
    out = []
    while i < na or j < nb:
        ta = (i + 1) / na if i < na else 9.0
        tq = (j + 1) / nb if j < nb else 9.0
        if abs(ta - tq) < 0.3 / max(na, nb):
            out.append(bm.faces.new([a[i], a[i + 1], b[j + 1], b[j]])); i += 1; j += 1
        elif j >= nb or (i < na and (a[i + 1].co - b[j].co).length <= (a[i].co - b[j + 1].co).length):
            out.append(bm.faces.new([a[i], a[i + 1], b[j]])); i += 1
        else:
            out.append(bm.faces.new([a[i], b[j + 1], b[j]])); j += 1
    return out


def P(nm):
    return [Vector(q) for q in sec_pts(SECS[NAMES.index(nm)])]


PLASTRON_V = set()        # rounded positions of the plastron-band vertices (stage 3 colour border)


def vkey(co):
    return (round(abs(co[0]), 4), round(co[1], 4), round(co[2], 4))


def stage1(k):
    bm = bmesh.new()
    rings = [ring(bm, sec_pts(s)) for s in SECS]
    spans = [bridge(bm, rings[i], rings[i + 1]) if len(rings[i]) == len(rings[i + 1]) else bridge_rows(bm, rings[i], rings[i + 1])
             for i in range(len(rings) - 1)]
    c0 = bm.verts.new(sum((v.co for v in rings[0]), Vector()) / len(rings[0]) * 1.0)
    c0.co.x = 0.0
    for i in range(len(rings[0]) - 1):          # s4 r21: the tail tip a fan (r20: a 14-gon cap = slivers)
        bm.faces.new([c0, rings[0][i + 1], rings[0][i]])
    cap(bm, rings[-1])
    recalc_normals(bm)
    PLASTRON_V.clear()
    # s4 r10: the plastron is the bridge band BETWEEN the leg windows (rings P0..F0, from the j6 loop down) and the
    # underside inside the j11 loop (window inner rims) from the rump to the chest lobe; leg tops, shoulders and
    # the rump sides stay skin (r9: tan wrapped over every leg top)
    for nm in NAMES[NAMES.index('P0'):NAMES.index('F0') + 1]:
        for v in rings[NAMES.index(nm)][6:]:
            PLASTRON_V.add(vkey(v.co))
    for nm in NAMES[NAMES.index('RW'):NAMES.index('F5') + 1]:
        for v in rings[NAMES.index(nm)][11:]:
            PLASTRON_V.add(vkey(v.co))
    grow(bm, rings, spans, NAMES.index('P4'), LJ, 4, 4, HIND, T1_LEG)
    grow(bm, rings, spans, NAMES.index('F0'), LJ, 4, 4, FORE, T1_LEG)
    snap_seam(bm)
    recalc_normals(bm)
    return object_from_bm('body', bm)


# ---------------------------------------------------------------- stage 2
EYE = Vector((0.0, -0.626, 0.660))   # the eye point on the side view (y, z); x from a ray on the head side
SOCKET = []


def stage2(k, body):
    bm = edit(body)
    tree = BVHTree.FromBMesh(bm)
    hit = tree.ray_cast(Vector((1.0, EYE.y, EYE.z)), Vector((-1, 0, 0)), 2.0)[0]
    f = face_near(bm, hit, n=(1, 0, 0))
    fn = f.normal.copy()
    with k.topo(bm, 'inset', 'eye socket: a loop inside the eye face, under the brow'):
        inner = inset(bm, [f], 0.25, 0.0)
    ev = list(inner[0].verts)
    move(ev, -fn * 0.005)
    sc = sum((v.co for v in ev), Vector()) / len(ev)
    SOCKET[:] = [Vector((abs(sc.x), sc.y, sc.z)), fn.copy()]
    ec0 = SOCKET[0].copy()
    k.meta['keep_valleys'] = lambda c: (abs(abs(c.x) - ec0.x) < 0.03 and abs(c.y - ec0.y) < 0.03 and abs(c.z - ec0.z) < 0.03)
    neck_head(k, bm)
    commit(body, bm)


# ---------------------------------------------------------------- weakfix 2026-10-23: neck folds, jaw, beak hook
MOUTH_V = set()          # vkeys of the mouth-line row (stage 3 paints the band under it dark)
BEAK_V = set()           # vkeys of the upper-beak vertices (stage 3 dark cap)
MOUTHB_V = set()         # the row under the mouth line


def ring_frame(nm):
    """Centre and along-axis of a T-section (neck / head rings)."""
    s = SECS[NAMES.index(nm)]
    if s[0] != 'T':
        pts = P(nm)
        c = sum(pts, Vector()) / len(pts)
        return Vector((0.0, c.y, c.z)), Vector((0, -1, 0))
    _k, _nm, (y0, z0), a, *_ = s
    sn, co = math.sin(math.radians(a)), math.cos(math.radians(a))
    up = Vector((0.0, sn, co))                     # the ring's own 'up' (top seam direction)
    return Vector((0.0, y0, z0)), Vector((0.0, co, -sn))   # axis is perpendicular to up in the yz plane


def neck_head(k, bm):
    """Stage-2 vertex moves (+ 2 logged neck loops): thick folded neck, chin step, jaw line, hooked beak."""
    names = ('N0', 'N1', 'N2', 'K0', 'K1', 'K2', 'K3', 'K4', 'K5')
    idx = {}
    for nm in names:
        for j, p in enumerate(P(nm)):
            idx[vkey(p)] = (nm, j)
    RV = {}
    for v in bm.verts:
        key = vkey(v.co)
        if key in idx:
            RV[idx[key]] = v
    get = lambda nm, j: RV.get((nm, j))

    def out_dir(nm, v):
        c, ax = ring_frame(nm)
        d = v.co - c
        d -= ax * d.dot(ax)
        return d.normalized() if d.length > 1e-6 else Vector((0, 0, 1))
    # 1. two fold loops in the neck (between N0-N1 and N1-N2): ridges, the original rings sink a little = grooves
    folds = []
    for a, b in (('N0', 'N1'), ('N1', 'N2')):
        va, vb = get(a, 9), get(b, 9)
        e = next((e for e in va.link_edges if e.other_vert(va) is vb), None)
        if e is None:
            continue
        with k.topo(bm, 'loop', f'neck fold ridge between {a} and {b} (sheet: wrinkled neck)'):
            nv = loopcut(bm, e, t=0.5, near=va)
        folds.append((a, b, nv))
    for a, b, nv in folds:
        ca, axa = ring_frame(a)
        cb, axb = ring_frame(b)
        c = (ca + cb) / 2
        ax = (axa + axb).normalized()
        for v in nv:
            d = v.co - c
            d -= ax * d.dot(ax)
            if d.length < 1e-6:
                continue
            w = 0.45 + 0.55 * max(0.0, -d.normalized().z)     # stronger on the throat, still a ridge on the nape
            v.co += d.normalized() * 0.011 * w
    for nm, amt in (('N1', 0.004), ('N2', 0.004)):
        for j in range(NV):
            v = get(nm, j)
            if v is None:
                continue
            od = out_dir(nm, v)
            w = 0.4 + 0.6 * max(0.0, -od.z)
            v.co -= od * amt * w
    # 2. chin step: the head's underside drops, the throat ring under it sits back and up
    for nm, dz in (('K1', -0.006), ('K2', -0.008), ('K3', -0.006)):
        for j in (11, 12, 13):
            v = get(nm, j)
            if v is not None:
                v.co.z += dz
    for j in (11, 12, 13):
        v = get('N2', j)
        if v is not None:
            v.co.z += 0.008
            v.co.y += 0.006
    # 3. jaw line: the j8 row of K1..K5 sinks 5 mm (a crease), the lower jaw rows sit a little out
    MOUTH_V.clear(); BEAK_V.clear()
    for nm, depth in (('K1', 0.002), ('K2', 0.004), ('K3', 0.005), ('K4', 0.004)):
        for j in range(NV):
            v = get(nm, j)
            if v is None:
                continue
            od = out_dir(nm, v)
            if j == 8:
                v.co -= od * depth
                MOUTH_V.add(vkey(v.co))
            elif j in (9, 10) and nm in ('K2', 'K3', 'K4'):
                v.co += od * 0.002
    # 4. beak hook: the upper beak (K5 and K4 top half) reaches forward and down over the lower jaw, which sits back
    # a shear linear in z keeps the K5 cap planar: top forward, bottom back = the overbite of a hooked beak
    for nm, fy in (('K4', 0.006), ('K5', 0.013)):
        zz = [get(nm, j).co.z for j in range(NV) if get(nm, j) is not None]
        zc, hh = (max(zz) + min(zz)) / 2, max(1e-4, (max(zz) - min(zz)) / 2)
        for j in range(NV):
            v = get(nm, j)
            if v is not None:
                v.co.y -= fy * (v.co.z - zc) / hh + fy * 0.25
    for nm in ('K4', 'K5'):
        for j in range(0, 9):
            v = get(nm, j)
            if v is not None:
                BEAK_V.add(vkey(v.co))
    MOUTH_V.clear(); MOUTHB_V.clear()
    for nm in ('K2', 'K3', 'K4', 'K5'):
        for j, S_ in ((8, MOUTH_V), (9, MOUTHB_V)):
            v = get(nm, j)
            if v is not None:
                S_.add(vkey(v.co))
    # the K5 cap's own centre (n-gon) has no vertex; BEAK_V covers its rim


# ---------------------------------------------------------------- stage 3
PAL = {'skin': '#b49e80', 'plastron': '#a8874f', 'scute': '#6f5638', 'groove': '#9e8253', 'dark': '#4a4541',   # s4 r29: EEVEE
       'eye': '#3a2414', 'pupil': '#121010'}


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h, sides=8):
    """A low-poly eye lens: back cone, iris ring, pupil cap (elephant's)."""
    n, u, w = frame3(n)
    ring_ = lambda rad, off: [bm.verts.new(c + n * off + (u * math.cos(t) + w * math.sin(t)) * rad)
                              for t in [k_ * 2 * math.pi / sides for k_ in range(sides)]]
    R, I = ring_(r, 0.0), ring_(r * 0.55, h * 0.7)
    A, Bv = bm.verts.new(c + n * h), bm.verts.new(c - n * h * 1.4)
    for j in range(sides):
        a, b = j, (j + 1) % sides
        bm.faces.new([Bv, R[b], R[a]])
        bm.faces.new([R[a], R[b], I[b], I[a]])
        bm.faces.new([I[a], I[b], A])


def nail(bm, base, out, w, hgt, d):
    """A blunt nail: an arched 6-sided section swept out of the foot, root sunk in (elephant's)."""
    out = Vector(out).normalized()
    side = out.cross(Vector((0, 0, 1))).normalized()
    up = Vector((0, 0, 1))
    SEC = [(-1, 0), (1, 0), (0.85, 0.6), (0.4, 1.0), (-0.4, 1.0), (-0.85, 0.6)]
    rows = []
    for off, sw, sh in ((-0.015, 1.0, 1.0), (d * 0.6, 0.9, 0.85), (d, 0.55, 0.5)):
        c = base + out * off + up * 0.004
        rows.append([bm.verts.new(c + side * su * w * sw / 2 + up * (sz * hgt * sh)) for su, sz in SEC])
    n = len(SEC)
    bm.faces.new(list(reversed(rows[0])))
    for a, b in zip(rows, rows[1:]):
        for j in range(n):
            bm.faces.new([a[j], a[(j + 1) % n], b[(j + 1) % n], b[j]])
    bm.faces.new(rows[-1])


# ---- the carapace: hexagon plates on the analytic dome, polar layout about the plan centre (0, YC)
YC = 0.17
PM = 1.8                 # meridian spacing exponent (even arc steps on the dome)
RHO1, RHOM = 0.27, 0.55  # centre hexagon corners; mid vertex on the radial grooves
R2 = {0: 0.80, 10: 0.82, 30: 0.845, 50: 0.82}   # inner edge of the marginals by phi mod 60
RIMT = 0.03              # rim thickness
RAISE = 0.007            # plateau lift over the groove
KI = 0.19                # groove ring width (share of the way to the plate centre); s4 r30 0.24 -> 0.19 (0.15: slivers 2.6 %)


def rim_R(phi):
    s, c = math.sin(phi), math.cos(phi)
    lo, hi = 0.0, 1.5
    for _ in range(48):
        t = (lo + hi) / 2
        x, y = t * abs(s), YC - t * c
        if x >= Wr(y) - 1e-12:
            hi = t
        else:
            lo = t
    return (lo + hi) / 2


def flare_k(phi):
    return FLARE * (0.25 + 0.75 * math.sin(phi) ** 2)


def S(rho, phi):
    """The carapace's outer surface at polar (rho 0 apex .. 1 rim, phi 0 front, +90 deg the left flank)."""
    R = rim_R(phi)
    s = math.sin(min(rho, 1.0) * math.pi / 2) ** (2 / PM)
    x, y = s * R * math.sin(phi), YC - s * R * math.cos(phi)
    p = Vector((x, y, zs(x, y)))
    if rho > 0.80:
        f = flare_k(phi) * ((rho - 0.80) / 0.20) ** 1.5
        p += Vector((math.sin(phi), -math.cos(phi), -0.3)) * f
    return p


def Sn(rho, phi):
    if rho < 0.02:
        return Vector((0, 0, 1))
    e = 0.01
    a = S(min(rho + e, 1.0), phi) - S(max(rho - e, 0.0), phi)
    b = S(rho, phi + e) - S(rho, phi - e)
    n = b.cross(a)
    if n.length < 1e-9:
        return Vector((0, 0, 1))
    n.normalize()
    if n.dot(S(rho, phi) - Vector((0, YC, 0.35))) < 0:
        n = -n
    return n


def disc(rho, phi):
    return (rho * math.sin(phi), -rho * math.cos(phi))


def undisc(d):
    rho = math.hypot(d[0], d[1])
    return rho, math.atan2(d[0], -d[1])


def r2(ph):
    m = int(round(ph)) % 60
    return R2[m] if m in R2 else R2[60 - m]


def plates():
    """The plate polygons as (kind, [(rho, phi_deg), ...]) - groove corners."""
    out = [('vert', [(RHO1, a) for a in range(0, 360, 60)])]
    for a in range(0, 360, 60):
        out.append(('cost', [(RHO1, a), (RHOM, a), (r2(a), a), (r2(a + 10), a + 10), (r2(a + 30), a + 30),
                             (r2(a + 50), a + 50), (r2(a + 60), a + 60), (RHOM, a + 60), (RHO1, a + 60)]))
    for c in range(0, 360, 20):
        inner = [(r2(c - 10), c - 10)] + ([(r2(c), c)] if c % 60 == 0 else []) + [(r2(c + 10), c + 10)]
        out.append(('marg', inner + [(1.0, c + 10), (1.0, c), (1.0, c - 10)]))
    return out


def build_shell(btree=None):
    bm = bmesh.new()
    V = {}

    def gv(rho, ph):
        key = (round(rho, 4), int(round(ph)) % 360 if rho > 1e-6 else 0)
        if key not in V:
            V[key] = bm.verts.new(S(rho, math.radians(ph)))
        return V[key]
    kinds = []
    for kind, poly in plates():
        cs = [gv(r, p) for r, p in poly]
        D = [disc(r, math.radians(p)) for r, p in poly]
        cd = (sum(d[0] for d in D) / len(D), sum(d[1] for d in D) / len(D))
        area = sum(D[i][0] * D[(i + 1) % len(D)][1] - D[(i + 1) % len(D)][0] * D[i][1] for i in range(len(D)))
        if area < 0:
            cs, D = cs[::-1], D[::-1]
        pl = []
        for d in D:
            q = (d[0] + (cd[0] - d[0]) * KI, d[1] + (cd[1] - d[1]) * KI)
            r, ph = undisc(q)
            pl.append(bm.verts.new(S(r, ph) + Sn(r, ph) * RAISE))
        r, ph = undisc(cd)
        m = bm.verts.new(S(r, ph) + Sn(r, ph) * RAISE * 1.6)
        n = len(cs)
        for i in range(n):
            bm.faces.new([cs[i], cs[(i + 1) % n], pl[(i + 1) % n], pl[i]]); kinds.append('groove')
        for i in range(n):
            bm.faces.new([pl[i], pl[(i + 1) % n], m]); kinds.append('scute')
    # rim band, underside band, hidden inner cap (inside the body)
    rim = [V[(1.0, p)] for p in range(0, 360, 10)]
    lo, inn = [], []
    for p in range(0, 360, 10):
        ph = math.radians(p)
        q = V[(1.0, p)].co
        lp = q - Vector((0, 0, RIMT)) + Vector((math.sin(ph), -math.cos(ph), 0)) * 0.004
        if btree is not None:          # s4 r23: seat the rim on the skin where the skin bulges up close under it
            h = btree.ray_cast(lp + Vector((0, 0, 0.001)), Vector((0, 0, -1)), 0.07)[0]
            if h is not None:          # r28: a smooth falloff (r27: all-or-nothing drops = a saw-tooth edge)
                gap = lp.z - h.z
                w = max(0.0, min(1.0, (0.06 - gap) / 0.035))
                lp = Vector((lp.x, lp.y, lp.z - max(0.0, gap - 0.004) * w))
        lo.append(bm.verts.new(lp))
        R = rim_R(ph)
        x, y = 0.86 * R * math.sin(ph), YC - 0.86 * R * math.cos(ph)
        inn.append(bm.verts.new(Vector((x, y, Zr(y) + 0.015))))
    cc = bm.verts.new(Vector((0.0, YC, 0.42)))
    n = len(rim)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([rim[j], rim[i], lo[i], lo[j]]); kinds.append('scute')
        bm.faces.new([lo[j], lo[i], inn[i], inn[j]]); kinds.append('groove')
        bm.faces.new([inn[j], inn[i], cc]); kinds.append('groove')
    bm.faces.ensure_lookup_table()
    ob = object_from_bm('shell', bm, mirror=False)
    mats = ['groove', 'scute']
    me = ob.data
    me.materials.clear()
    for kk in mats:
        me.materials.append(material(kk, srgb(PAL[kk])))
    for p_, kd in zip(me.polygons, kinds):
        p_.material_index = mats.index(kd)
        p_.use_smooth = False
    white(ob)
    return ob


def stage3(k, body):
    me = body.data
    def body_rule(c, n, i):
        ks = [vkey(me.vertices[v].co) for v in me.polygons[i].vertices]
        if all(q in PLASTRON_V for q in ks):
            return 'plastron'
        if len(ks) >= 10 and c.y < -0.70:                       # the beak's front cap
            return 'dark'
        if all(q in BEAK_V for q in ks):                         # weakfix: the upper beak only (the jaw stays skin)
            return 'dark'
        if (all(q in MOUTH_V or q in MOUTHB_V for q in ks) and sum(q in MOUTH_V for q in ks) >= 2
                and sum(q in MOUTHB_V for q in ks) >= 2):
            return 'dark'                                        # weakfix: the mouth line
        return 'skin'
    paint(body, {kk: PAL[kk] for kk in ('skin', 'plastron', 'dark')}, body_rule)
    bmb = edit(body)
    tree = BVHTree.FromBMesh(bmb)
    bmb.free()
    ebm = evaluated_bm(body)
    etree = BVHTree.FromBMesh(ebm)
    ebm.free()
    pieces = [build_shell(etree)]
    # eye: a small round lens in the socket, a dark pupil disc
    c, n = SOCKET[0].copy(), SOCKET[1].normalized()
    n = n if n.x > 0 else -n
    n = (n + Vector((0.0, -0.25, 0.05))).normalized()
    bm = bmesh.new()
    lens(bm, c + n * 0.002, n, 0.013, 0.007)
    eye = object_from_bm('eye', bm)
    paint(eye, {'eye': PAL['eye'], 'pupil': PAL['pupil']},
          lambda c_, n_, i: 'pupil' if ((c_ - c) - n * (c_ - c).dot(n)).length < 0.006 and n_.dot(n) > 0.5 else 'eye')
    pieces.append(eye)
    # nails: five round the front of each fore foot, four on each hind foot
    bm = bmesh.new()
    for sec, angs in ((FORE[-2], (-140, -115, -90, -65, -40)), (HIND[-2], (-128, -103, -77, -52))):
        cx, cy, z, rx, ry, nn = sec
        for ang in angs:
            th = math.radians(ang)
            d = Vector((math.cos(th), math.sin(th), 0.0))
            o = Vector((cx, cy, 0.02)) + d * 0.4
            hit = tree.ray_cast(o, -d, 0.6)[0]
            base = Vector((hit.x, hit.y, 0.0)) if hit is not None else Vector((cx, cy, 0.0)) + d * ry
            nail(bm, base - d * 0.004, d, 0.034, 0.03, 0.028)
    nails = object_from_bm('nails', bm)
    # s4 r22: the tail, a short blunt cone seated 1 cm into the rump wall, hanging back and down (sheet rear view)
    bm = bmesh.new()
    path = [(Vector((0.0, 0.723, 0.240)), 0.046, 0.038), (Vector((0.0, 0.748, 0.232)), 0.042, 0.035),
            (Vector((0.0, 0.772, 0.205)), 0.031, 0.027), (Vector((0.0, 0.790, 0.170)), 0.019, 0.017),
            (Vector((0.0, 0.800, 0.138)), 0.008, 0.008)]
    rows = []
    for i, (c_, rx, rz) in enumerate(path):
        d = (path[min(i + 1, 4)][0] - path[max(i - 1, 0)][0]).normalized()
        up = Vector((0, 0, 1)) - d * d.z
        up.normalize()
        sd = d.cross(up)
        rows.append([bm.verts.new(c_ + sd * rx * math.cos(t) + up * rz * math.sin(t))
                     for t in [k_ * math.pi / 4 for k_ in range(8)]])
    for r0, r1 in zip(rows, rows[1:]):
        for j in range(8):
            bm.faces.new([r0[j], r0[(j + 1) % 8], r1[(j + 1) % 8], r1[j]])
    bm.faces.new(list(reversed(rows[0])))
    tip = bm.verts.new(path[-1][0] + (path[-1][0] - path[-2][0]).normalized() * 0.008)
    for j in range(8):
        bm.faces.new([rows[-1][j], rows[-1][(j + 1) % 8], tip])
    recalc_normals(bm)
    tail = object_from_bm('tail', bm, mirror=False)
    paint(tail, {'skin': PAL['skin']}, lambda c_, n_, i: 'skin')
    pieces.append(tail)
    paint(nails, {'dark': PAL['dark']}, lambda c_, n_, i: 'dark')
    pieces.append(nails)
    return pieces


# ---------------------------------------------------------------- stage 4
def stage4(k, body, pieces):
    B = [('hips', J['hips'], J['chest'], None),
         ('chest', J['chest'], J['chest2'], 'hips', True),
         ('neck', J['neck'], J['neck1'], 'chest'),
         ('neck1', J['neck1'], J['head'], 'neck', True),
         ('head', J['head'], J['face'], 'neck1', True),
         ('tail0', J['tail0'], J['tail1'], 'hips'),
         ('tail1', J['tail1'], J['tail2'], 'tail0', True),
         ('upperarm.L', J['shoulder'], J['wrist'], 'chest'),
         ('hand.L', J['wrist'], J['ftoe'], 'upperarm.L', True),
         ('thigh.L', J['hipL'], J['hock'], 'hips'),
         ('foot.L', J['hock'], J['htoe'], 'thigh.L', True)]
    rig = armature(B, roll='auto')
    skin(body, rig)
    for p in pieces:
        if p.name.startswith('piece_shell'):
            bind(p, rig, bone='chest')
        else:
            bind(p, rig, body=body)
    clip(rig, 'idle', {1: {}, 12: {'neck': (-3, 0, 0), 'neck1': (-2, 0, 4), 'head': (3, 0, 4), 'tail0': (0, 0, 6)},
                       24: {'neck': (0, 0, 0), 'neck1': (0, 0, 0), 'head': (-2, 0, 0)},
                       36: {'neck': (-3, 0, 0), 'neck1': (-2, 0, -4), 'head': (3, 0, -4), 'tail0': (0, 0, -6)},
                       48: {}})
    A = 9                     # night fix r36: shorter stride (was 12): the thigh roots stay off the rump
    # night fix 10-23: after --fix-clips (leg aim IK) the rump faces on tail0 crossed the thigh roots at move@7/@19
    # (posed clip 3.3%; tail swing 0 changed nothing, so it is the rump, not the swing): the tail is carried lifted in
    # the trot (TLX on tail0), pulling its rump faces up and back off the thigh roots
    TSW, TLX = 5, 18
    clip(rig, 'move', {
        1: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0),
            'neck': (0, 0, 3), 'tail0': (TLX, 0, TSW)},
        7: {'hand.R': (-10, 0, 0), 'foot.L': (8, 0, 0), 'head': (2, 0, 0), 'tail0': (TLX, 0, 0)},
        13: {'upperarm.L': (-A, 0, 0), 'upperarm.R': (A, 0, 0), 'thigh.L': (A, 0, 0), 'thigh.R': (-A, 0, 0),
             'neck': (0, 0, -3), 'tail0': (TLX, 0, -TSW)},
        19: {'hand.L': (-10, 0, 0), 'foot.R': (8, 0, 0), 'head': (2, 0, 0), 'tail0': (TLX, 0, 0)},
        25: {'upperarm.L': (A, 0, 0), 'upperarm.R': (-A, 0, 0), 'thigh.L': (-A, 0, 0), 'thigh.R': (A, 0, 0),
             'neck': (0, 0, 3), 'tail0': (TLX, 0, TSW)}},
        loc={1: {'hips': (0, 0, 0)}, 7: {'hips': (0, 0, 0.006)}, 13: {'hips': (0, 0, 0)}, 19: {'hips': (0, 0, 0.006)},
             25: {'hips': (0, 0, 0)}})
    clip(rig, 'attack', {
        1: {},
        10: {'neck': (12, 0, 0), 'neck1': (8, 0, 0), 'head': (-10, 0, 0), 'upperarm.L': (-5, 0, 0), 'upperarm.R': (-5, 0, 0)},
        16: {'neck': (-14, 0, 0), 'neck1': (-10, 0, 0), 'head': (12, 0, 0)},
        22: {'neck': (-6, 0, 0), 'neck1': (-4, 0, 0), 'head': (4, 0, 0)},
        32: {}})
    return rig


run(META, stage1, stage2, stage3, stage4)
