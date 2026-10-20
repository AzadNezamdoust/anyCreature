"""partkit — workflow v4: the t7r hand loft as a part kit (research/workflow_v4_plan.md).

A creature is DATA: a spine loft of half-ring sections (tail tip -> nose), limbs grown from socket faces of the
loft, and a face module (eyeball first, a bulging socket, a wrapped lid piece). Body plans live in
kit/plans/<plan>.json (sockets, bones, clips, loops); the creature program fills the numbers from its sheet.
Every call below is deterministic from data, and the t7r code paths are reproduced exactly: the wolf_t7 tree
rebuilt through partkit hashes to its lock (abc/v4/wolf/migrate).

Conventions are bmkit's: metres, Z up, the creature faces -Y, model the +X half (x >= 0), seam on x = 0.

SECTIONS AND LOFTS (t7r wolf.py tb / sec_pts / stage1)
  section(nm, top, bot, W, prof)        a section from its top and bottom seam points (y, z) off the side view
  vsection(nm, y, ztop, zbot, W, prof)  the same, vertical
  fit_sections(bp, stations)            T/B from the side outline, W from the front or plan outline (no bpy);
                                        returns the sections and a report of what was read
  Loft(secs).build(bm)                  rings, bridges, end caps; loft.pts(nm), loft.centre(nm), loft.surf(a, b, t, jf)
  socket(loft, span, j0, n)             the n faces j0.. of span `span` + their (u, s) roles (u by profile x, s rear/front)
  grow(bm, faces, roles, secs, corner)  extrude a face region section by section (t7r grow, 2+ faces = 6/8-sided limbs)
  build_body(tree, k=None)              the stage-1 shell from a tree dict; faces carry an int layer 'pk' (tags)

TAGS AND COLOUR
  tag_info(loft, tree, code)            -> dict(part, span, sec, j): what a face's 'pk' code means
  paint_regions(ob, loft, tree, palette, rule)   rule(info, centre, normal) -> palette key (bmkit.paint underneath)
  palette_from_sheet(cdir, probes, k)   kmeans palette of the sheet figures (carve._kmeans) and, per region, the
                                        cluster nearest the sheet colour under that region's probe points

FACE MODULE (never remeshed; body edits logged with k.topo)
  eye_frame / eyeball(...)              a closed low-poly sphere, gaze converged `converge` degrees, iris/pupil faces
  eye_socket(k, bm, face, c, r, ...)    rim inset pushed out (bulge), floor inset projected onto the ball + gap
  lids(...)                             an almond lid band wrapped on the ball (closed, with thickness), its own piece

DETAIL PIECES
  mass(bm, centre, axes, ...)           a chunky smooth lump (low lat-long ellipsoid, laid back): ruff, bib, brush
  clump / clumps / surf                 t7r fur clumps
  lens                                  t7r eye lens (legacy face path)
  nails(bm, soles, ...)                 wolf_t7 blunt nails

RIG
  bones_from_plan(plan, J)              bmkit.armature list from the plan's bone table
  clips_from_plan(rig, plan)            the plan's default clips
  trot(rig, ...)                        a root-motion trot whose stance paws stay planted (ftest foot_contact)
  best_of(k, trees, bp, J, plan)        build N candidate shells, rank by mean IoU vs the sheet masks minus
                                        proportion misses, keep the winner (S1 best-of-N)
"""
import json, math, os

try:                                   # the pure helpers (fit_sections) also work outside Blender
    import bpy, bmesh
    from mathutils import Vector, Matrix
    import bmkit as B
    from bmkit import (ring, bridge, cap, extrude, inset, move, scale, flatten, face_near, vert_near, edge_near,
                       snap_seam, recalc_normals, object_from_bm, paint, edit, commit, loopcut, armature, clip)
except ImportError:
    bpy = None

KIT = os.path.dirname(os.path.abspath(__file__))

# half-ring profiles, top seam -> bottom seam: (x as a fraction of W, h as a fraction of T / B). The 6-vertex
# set is t7r's (wolf.py:21-27); the 8-vertex set gives a rounder, chunkier section at the same plane logic.
PROFILES = dict(
    BODY=[(0, 1), (0.6, 0.92), (1, 0.3), (0.85, -0.35), (0.45, -0.8), (0, -1)],
    CHEST=[(0, 1), (0.62, 0.9), (1, 0.35), (0.8, -0.3), (0.35, -0.8), (0, -1)],
    HEADB=[(0, 1), (0.75, 0.97), (1, 0.4), (0.85, -0.4), (0.5, -0.85), (0, -1)],
    HEAD=[(0, 1), (0.75, 0.93), (1, 0.3), (0.85, -0.4), (0.5, -0.85), (0, -1)],
    HEADF=[(0, 1), (0.75, 0.88), (1, 0.1), (0.85, -0.45), (0.5, -0.85), (0, -1)],
    MUZ=[(0, 1), (0.62, 0.95), (1, 0.4), (0.95, -0.3), (0.6, -0.85), (0, -1)],
    TAIL=[(0, 1), (0.7, 0.7), (1, 0.1), (0.85, -0.5), (0.45, -0.9), (0, -1)],
    # 8-vertex half rings (7 quads): back plane, upper flank, flank, lower flank, keel/belly
    BODY8=[(0, 1), (0.52, 0.96), (0.88, 0.72), (1, 0.22), (0.96, -0.3), (0.78, -0.68), (0.42, -0.94), (0, -1)],
    CHEST8=[(0, 1), (0.55, 0.95), (0.9, 0.7), (1, 0.25), (0.92, -0.25), (0.7, -0.66), (0.34, -0.93), (0, -1)],
    NECK8=[(0, 1), (0.55, 0.96), (0.9, 0.72), (1, 0.25), (0.95, -0.25), (0.8, -0.65), (0.45, -0.93), (0, -1)],
    HEAD8=[(0, 1), (0.6, 0.97), (0.92, 0.72), (1, 0.25), (0.93, -0.22), (0.76, -0.6), (0.42, -0.92), (0, -1)],
    STOP8=[(0, 1), (0.5, 0.95), (0.78, 0.66), (0.95, 0.2), (1, -0.2), (0.84, -0.6), (0.45, -0.92), (0, -1)],
    MUZ8=[(0, 1), (0.62, 0.98), (0.93, 0.74), (1, 0.25), (0.98, -0.25), (0.85, -0.65), (0.5, -0.95), (0, -1)],
    TAIL8=[(0, 1), (0.55, 0.92), (0.9, 0.6), (1, 0.1), (0.92, -0.4), (0.7, -0.75), (0.36, -0.95), (0, -1)],
    # rounded trunk sections (round 2): a near-circle, a deep keel chest, a rounded rump
    ROUND8=[(0, 1), (0.45, 0.9), (0.8, 0.62), (0.98, 0.22), (0.98, -0.22), (0.8, -0.62), (0.45, -0.9), (0, -1)],
    KEEL8=[(0, 1), (0.48, 0.93), (0.85, 0.66), (1, 0.25), (0.92, -0.2), (0.68, -0.6), (0.3, -0.9), (0, -1)],
    RUMP8=[(0, 1), (0.55, 0.95), (0.9, 0.7), (1, 0.25), (0.95, -0.2), (0.75, -0.6), (0.38, -0.9), (0, -1)],
)

TAG = 'pk'                     # int face layer: what part a face belongs to
T_SPINE, T_CAP, T_LIMB = 1, 9000, 10000


def load_plan(name):
    """kit/plans/<name>.json -> dict."""
    return json.load(open(os.path.join(KIT, 'plans', f'{name}.json')))


# ============================================================ sections (pure python)
def section(nm, top, bot, W, prof):
    """A section from its top and bottom seam points (y, z) read off the side view (== t7r tb())."""
    (yt, zt), (yb, zb) = top, bot
    c = ((yt + yb) / 2, (zt + zb) / 2)
    h = math.hypot(yt - yb, zt - zb) / 2
    a = math.degrees(math.atan2(yt - yb, zt - zb))
    return (nm, c, round(a, 2), h, h, W, prof)


def vsection(nm, y, ztop, zbot, W, prof, zc=None):
    """A vertical section at y; zc moves the centre (T and B then differ)."""
    if zc is None:
        return section(nm, (y, ztop), (y, zbot), W, prof)
    return (nm, (y, zc), 0.0, ztop - zc, zc - zbot, W, prof)


def _cross(poly, axis, value):
    """Where the closed polygon crosses the line axis=value: the other coordinate, sorted."""
    out, n = [], len(poly)
    o = 1 - axis
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a[axis] <= value) != (b[axis] <= value):
            t = (value - a[axis]) / (b[axis] - a[axis])
            out.append(a[o] + t * (b[o] - a[o]))
    return sorted(out)


def outline_runs(bp, view, axis, value):
    """The inside runs [(lo, hi)] of a blueprint outline along the line axis=value (front/top halves mirrored)."""
    pts = [list(p) for p in bp[view]['outline']]
    if view != 'side' and all(p[0] >= -1e-9 for p in pts):
        pts = pts + [[-p[0], p[1]] for p in reversed(pts)]
    c = _cross(pts, axis, value)
    return list(zip(c[::2], c[1::2]))


def fit_sections(bp, stations, top_scale=None):
    """stations: [dict(nm, y, prof, top=None|z, bot=None|z, zc=None, W=None|m, wsrc='top'|'front', wk=1.0)].
    top / bot default to the side outline's run through (y, near the previous centre); W defaults to the plan
    outline's half width at y (its y rescaled to the side view's length) or the front outline's half width at the
    section's mid height, times wk. Returns (sections, report rows)."""
    sy = [p[0] for p in bp['side']['outline']]
    ty = [p[1] for p in bp['top']['outline']]
    k_y = (max(ty) - min(ty)) / (max(sy) - min(sy)) if top_scale is None else top_scale
    secs, rep = [], []
    for st in stations:
        y = st['y']
        runs = outline_runs(bp, 'side', 0, y)
        top = st.get('top')
        bot = st.get('bot')
        if top is None or bot is None:
            want = st.get('near', 0.7)
            r = min(runs, key=lambda ab: 0 if ab[0] <= want <= ab[1] else min(abs(ab[0] - want), abs(ab[1] - want))) \
                if runs else (0.5, 0.7)
            top = r[1] if top is None else top
            bot = r[0] if bot is None else bot
        top += st.get('dtop', 0.0)
        bot += st.get('dbot', 0.0)
        W = st.get('W')
        src = 'given'
        if W is None:
            if st.get('wsrc', 'top') == 'top':
                rr = outline_runs(bp, 'top', 1, -y * k_y)
                W = max((max(abs(a), abs(b)) for a, b in rr), default=0.1)
                src = 'top'
            else:
                zm = st.get('wz', (top + bot) / 2)
                rr = outline_runs(bp, 'front', 1, zm)
                W = max((max(abs(a), abs(b)) for a, b in rr), default=0.1)
                src = 'front@%.3f' % zm
            W *= st.get('wk', 1.0)
        zc = st.get('zc')
        sec = vsection(st['nm'], y, round(top, 4), round(bot, 4), round(W, 4), st['prof'], zc)
        if st.get('tilt'):                                    # lean the section (deg, top forward = +)
            nm, c, a, T, Bb, W_, p = sec
            sec = (nm, c, st['tilt'], T, Bb, W_, p)
        secs.append(sec)
        rep.append(dict(nm=st['nm'], y=y, top=round(top, 3), bot=round(bot, 3), W=round(W, 3), wsrc=src))
    return secs, rep


def sec_pts(sec, profiles=PROFILES):
    nm, (y0, z0), a, T, Bb, W, prof = sec
    prof = profiles[prof] if isinstance(prof, str) else prof
    s, co = math.sin(math.radians(a)), math.cos(math.radians(a))
    out = []
    for fx, fh in prof:
        h = fh * (T if fh >= 0 else Bb)
        out.append((fx * W, y0 + h * s, z0 + h * co))
    return out


# ============================================================ the loft (bpy)
def _tags(bm):
    L = bm.faces.layers.int
    return L.get(TAG) or L.new(TAG)


class Loft:
    """A spine of sections (tail tip -> nose): == t7r stage1's rings / spans / caps."""

    def __init__(self, secs, profiles=PROFILES):
        self.secs = list(secs)
        self.profiles = profiles
        self.idx = {s[0]: i for i, s in enumerate(self.secs)}
        self.rings = self.spans = None

    def sec(self, nm):
        return self.secs[self.idx[nm]]

    def pts(self, nm):
        return [Vector(q) for q in sec_pts(self.sec(nm), self.profiles)]

    def centre(self, nm):
        c = self.sec(nm)[1]
        return Vector((0.0, c[0], c[1]))

    def build(self, bm):
        tl = _tags(bm)
        self.rings = [ring(bm, sec_pts(s, self.profiles)) for s in self.secs]
        self.spans = [bridge(bm, self.rings[i], self.rings[i + 1]) for i in range(len(self.rings) - 1)]
        for i, sp in enumerate(self.spans):
            for j, f in enumerate(sp):
                f[tl] = T_SPINE + 64 * i + j
        c0 = cap(bm, self.rings[0]); c1 = cap(bm, self.rings[-1])
        c0[tl], c1[tl] = T_CAP, T_CAP + 1
        recalc_normals(bm)
        return self

    def surf(self, a, b, t, jf):
        """A point on the loft between sections a and b (t from a to b) at fractional ring index jf, and its
        outward normal (radial from the interpolated section centre) == t7r surf()."""
        A, Bq = self.pts(a), self.pts(b)
        j0 = min(int(jf), len(A) - 2); f = jf - j0
        pa, pb = A[j0].lerp(A[j0 + 1], f), Bq[j0].lerp(Bq[j0 + 1], f)
        p = pa.lerp(pb, t)
        c = self.centre(a).lerp(self.centre(b), t)
        return p, (p - c).normalized()


def kfac(u, corner):
    """How far a limb vertex sits out front/back: t7r's 1 at u = 0 and `corner` at |u| = 1, eased between."""
    if u == 0:
        return 1.0
    if abs(u) == 1:
        return corner
    return 1.0 - (1.0 - corner) * u * u


def role_pos(sec, u, s, corner=0.55):
    c, rx, ry = sec[0], sec[1], sec[2]
    dz = sec[3] if len(sec) > 3 else 0.0
    k = kfac(u, corner)
    return (c[0] + u * rx, c[1] + s * ry * k, c[2] - u * dz)


def socket(loft, span, j0, n):
    """The n faces j0..j0+n-1 of the span that starts at section `span`, and their vertex roles: u runs from +1
    (the vertex with the largest profile x) to -1 (the smallest), s is -1 on the front ring and +1 on the rear."""
    i = loft.idx[span]
    rr, rf = loft.rings[i], loft.rings[i + 1]
    js = list(range(j0, j0 + n + 1))
    prof = loft.sec(loft.secs[i + 1][0])[6]
    prof = loft.profiles[prof] if isinstance(prof, str) else prof
    order = sorted(js, key=lambda j: -prof[j][0])
    us = {j: (1.0 - 2.0 * order.index(j) / n) for j in js}
    for j in js:                       # exact t7r values for the 2-face case
        us[j] = float(round(us[j])) if abs(us[j] - round(us[j])) < 1e-9 else us[j]
    roles = {}
    for j in js:
        roles[rf[j]] = (us[j], -1)
    for j in js:
        roles[rr[j]] = (us[j], 1)
    return [loft.spans[i][j] for j in range(j0, j0 + n)], roles


def grow(bm, faces, roles, secs, corner=0.55, tag0=None):
    """Extrude a face region section by section; each new vertex keeps the role (u across, s front/back) of the
    vertex it was extruded from (== t7r grow). tag0: the side faces of section q get tag0 + q."""
    tl = _tags(bm)
    for q, sec in enumerate(secs):
        r = extrude(bm, faces)
        new = {}
        for v in r['verts']:
            ov = min(roles, key=lambda o: (o.co - v.co).length)
            new[v] = roles[ov]
        for v, (u, s) in new.items():
            v.co = Vector(role_pos(sec, u, s, corner))
        if tag0 is not None:
            for f in r['sides']:
                f[tl] = tag0 + q
            for f in r['faces']:
                f[tl] = tag0 + 99
        faces, roles = r['faces'], new
    return faces, roles


def build_body(tree):
    """tree = dict(spine=[sections], limbs=[dict(name, span, j0, n, secs, corner=0.55)], profiles=None).
    Returns (body object, loft). Limbs grow in list order (the order is part of the shape)."""
    bm = bmesh.new()
    loft = Loft(tree['spine'], tree.get('profiles') or PROFILES).build(bm)
    for li, L in enumerate(tree.get('limbs', [])):
        faces, roles = socket(loft, L['span'], L['j0'], L['n'])
        grow(bm, faces, roles, L['secs'], L.get('corner', 0.55), tag0=T_LIMB * (li + 1))
    snap_seam(bm)
    ob = object_from_bm('body', bm)
    return ob, loft


def tag_info(loft, tree, code):
    """What a 'pk' code means: dict(part='spine'|'cap'|limb name|'', span=section name, j=ring quad, sec=limb section)."""
    if code >= T_LIMB:
        li, q = divmod(code, T_LIMB)
        L = tree['limbs'][li - 1]
        return dict(part=L['name'], sec=q if q != 99 else len(L['secs']), tip=q == 99, span=None, j=None)
    if code >= T_CAP:
        return dict(part='cap', end=code - T_CAP, span=None, j=None, sec=None)
    if code >= T_SPINE:
        i, j = divmod(code - T_SPINE, 64)
        return dict(part='spine', span=loft.secs[i][0], i=i, j=j, sec=None)
    return dict(part='', span=None, j=None, sec=None)


def retag(bm):
    """Faces a topology op made without a tag (inset rings) take the most common tag of their neighbours."""
    tl = _tags(bm)
    for _ in range(3):
        for f in bm.faces:
            if f[tl] == 0:
                ns = [g[tl] for e in f.edges for g in e.link_faces if g is not f and g[tl]]
                if ns:
                    f[tl] = max(set(ns), key=ns.count)


def paint_regions(ob, loft, tree, palette, rule):
    """bmkit.paint with the region rule: rule(info, centre, normal) -> palette key; info = tag_info(...)."""
    att = ob.data.attributes.get(TAG)
    codes = [d.value for d in att.data] if att else [0] * len(ob.data.polygons)
    paint(ob, palette, lambda c, n, i: rule(tag_info(loft, tree, codes[i]), c, n))


def palette_from_sheet(cdir, probes, k=7, views=('side', 'front'), exact=()):
    """A kmeans palette of the sheet figures (carve._kmeans in Lab, area = pixel count), then per region the
    cluster nearest to the median sheet colour under that region's world probe points.
    probes = {region: [(x, y, z), ...]} -> ({region: '#rrggbb'}, {'clusters': [...], 'samples': {...}})."""
    import numpy as np
    import carve as C
    V = C.load_ref(cdir)
    X = []
    for v in views:
        m = V[v].mask
        X.append(V[v].rgb[m][::7])
    X = np.concatenate(X)
    lab = C._lab(X)
    cent, _ = C._kmeans(lab, np.ones(len(lab)), k)
    clusters = C._srgb_of_lab(cent)
    out, samples = {}, {}
    for reg, pts in probes.items():
        got = []
        for p in pts:
            for v in views:
                col = V[v].colour([p], 3)
                if col is not None:
                    got.append(col)
                    break
        if not got:
            continue
        med = np.median(np.array(got), 0)
        L = C._lab(med[None])[0]
        j = int(np.argmin(((cent - L) ** 2).sum(1)))
        c = med if reg in exact else clusters[j]          # small regions (an iris, a nose) keep their own sample
        out[reg] = '#%02x%02x%02x' % tuple(int(round(max(0, min(255, x)))) for x in c)
        samples[reg] = '#%02x%02x%02x' % tuple(int(x) for x in med)
    return out, dict(clusters=['#%02x%02x%02x' % tuple(int(round(x)) for x in c) for c in clusters], samples=samples)


# ============================================================ face module
def eye_frame(gaze, up=(0, 0, 1)):
    f = Vector(gaze).normalized()
    u = f.cross(Vector(up))
    u = u.normalized() if u.length > 1e-6 else Vector((1, 0, 0))
    w = u.cross(f).normalized()
    return f, u, w


def converge(forward, side, deg):
    """The gaze turned `deg` toward the midline (side = +1 for the left eye on +X)."""
    R = Matrix.Rotation(math.radians(-deg * side), 3, 'Z')    # the +X eye turns toward -X
    return (R @ Vector(forward)).normalized()


def eyeball(name, centre, r, gaze, segs=8, polar=(0, 24, 48, 80, 125, 180), iris_deg=52, pupil_deg=20,
            keys=('iris', 'pupil', 'iris')):
    """A closed low-poly ball (lat-long, poles on the gaze): faces within pupil_deg of the gaze -> keys[1],
    within iris_deg -> keys[0], the rest keys[2]. Returns (bmesh, face key list) — the caller makes the object."""
    bm = bmesh.new()
    f, u, w = eye_frame(gaze)
    c = Vector(centre)
    rows = []
    for pd in polar:
        th = math.radians(pd)
        if pd in (0, 180):
            rows.append([bm.verts.new(c + f * r * math.cos(th))])
        else:
            rows.append([bm.verts.new(c + f * r * math.cos(th) + (u * math.cos(a) + w * math.sin(a)) * r * math.sin(th))
                         for a in [2 * math.pi * q / segs for q in range(segs)]])
    keyof = []
    for ri in range(len(rows) - 1):
        A, Bv = rows[ri], rows[ri + 1]
        mid = (polar[ri] + polar[ri + 1]) / 2
        key = keys[1] if mid < pupil_deg else (keys[0] if mid < iris_deg else keys[2])
        for q in range(segs):
            q1 = (q + 1) % segs
            if len(A) == 1:
                bm.faces.new([A[0], Bv[q], Bv[q1]])
            elif len(Bv) == 1:
                bm.faces.new([A[q], Bv[0], A[q1]])
            else:
                bm.faces.new([A[q], Bv[q], Bv[q1], A[q1]])
            keyof.append(key)
    return bm, keyof


def eye_socket(k, bm, face, c, r, rim=0.22, bulge=0.12, floor=0.42, gap=0.0012, reason='', axis=None,
               diamond=None, tilt=0.0, project=True, sink=0.0):
    """The socket in one body face (stage 2): an inset ring pushed OUT along the face normal by bulge*r (the
    rim), then a second inset whose ring is projected onto the ball sphere (centre c, radius r) + gap, so the
    skin wraps the eyeball (ftest eye_fit 0-2 mm). diamond = (half width, up, down) degrees round `axis`: the four
    floor vertices go to the front / top / back / bottom of that almond diamond on the ball (radius r + gap)
    instead, so the opening is an eye shape; gap must keep the chords between them outside the ball (no
    crossing: chord factor cos(half the angle between neighbours) x (r + gap) >= r).
    Returns dict(rim=verts, floor=verts, inner=face)."""
    tl = _tags(bm)
    code = face[tl]
    n = face.normal.copy()
    with k.topo(bm, 'inset', 'eye socket rim: a loop inside the eye face, pushed out round the ball' + reason):
        f1 = inset(bm, [face], rim, 0.0)[0]
    rimv = list(f1.verts)
    move(rimv, n * bulge * r)
    with k.topo(bm, 'inset', 'eye socket floor: a second loop wrapped onto the eyeball' + reason):
        f2 = inset(bm, [f1], floor, 0.0)[0]
    flo = list(f2.verts)
    c = Vector(c)
    if not project:                          # the floor stays a flat ring, sunk; eye_dome() fits the eye to it
        move(flo, -n * sink)
    elif diamond is None:
        for v in flo:
            d = (v.co - c)
            v.co = c + d.normalized() * (r + gap)
    else:
        o, h, w = eye_frame(axis if axis is not None else n)
        hw, up_, lo_ = (math.tan(math.radians(x)) for x in diamond)
        ct, st = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
        rot = lambda x, y: (x * ct - y * st, x * st + y * ct)
        targets = {0: rot(hw, 0), 1: rot(0, up_), 2: rot(-hw, 0), 3: rot(0, -lo_)}
        ang = {v: math.atan2((v.co - c).dot(w), (v.co - c).dot(h)) for v in flo}
        free = dict(targets)
        for v in sorted(flo, key=lambda v: ang[v]):
            best = min(free, key=lambda q: abs(math.remainder(ang[v] - math.atan2(free[q][1], free[q][0]), 2 * math.pi)))
            x, y = free.pop(best)
            v.co = c + (o + h * x + w * y).normalized() * (r + gap)
    for f in bm.faces:
        if f[tl] == 0:
            f[tl] = code
    B._fresh(rimv + flo)
    return dict(rim=rimv, floor=flo, inner=f2)


def lids(centre, r, axis, up=(0, 0, 1), half_w=40.0, up_h=20.0, lo_h=24.0, tilt=8.0, out=1.45, gap=0.0009,
         thick=0.0032, n=12, point=0.6, floor_pts=None, beyond=1.12, lip=1.25, outer_circle=None, bm=None):
    """An almond lid band wrapped on the ball (centre, r): the opening is the almond of angular half width half_w
    (deg, along the head) and half heights up_h / lo_h (deg) round `axis` (the socket's look direction), its
    front corner tilted `tilt` deg up (negative: the outer corner up). The band is closed: an inner skin on the
    ball at r + gap and an outer skin at r + thick, with a lip row at `lip` x the opening (the dark lid edge).
    Its outer edge runs `out` x the opening, or - with floor_pts (the body's socket floor ring) - `beyond` x
    that ring in the ball's tangent plane, so the band dives under the socket wall along ONE closed loop
    (techqa: a piece enters the body once). Returns (bmesh, per-face keys 'lip' | 'lid')."""
    bm = bm or bmesh.new()
    o, h, v = eye_frame(axis, up)
    c = Vector(centre)
    ct, st = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))

    def almond(t):
        x = math.copysign(abs(math.cos(t)) ** point, math.cos(t)) * math.tan(math.radians(half_w))
        y = math.sin(t) * math.tan(math.radians(up_h if math.sin(t) >= 0 else lo_h))
        return x * ct - y * st, x * st + y * ct

    poly = None
    if floor_pts:
        poly = []
        for p in floor_pts:
            d = Vector(p) - c
            poly.append((d.dot(h) / d.dot(o), d.dot(v) / d.dot(o)))      # gnomonic (tangent-plane) coordinates

    def ray_poly(dx, dy):
        best = None
        for i in range(len(poly)):
            (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % len(poly)]
            ex, ey = x1 - x0, y1 - y0
            den = dx * ey - dy * ex
            if abs(den) < 1e-12:
                continue
            tt = (x0 * ey - y0 * ex) / den
            uu = (x0 * dy - y0 * dx) / den
            if tt > 0 and -1e-9 <= uu <= 1 + 1e-9:
                best = tt if best is None else min(best, tt)
        return best

    def to_dir(x, y):
        return (o + h * x + v * y).normalized()
    ts = [2 * math.pi * q / n for q in range(n)]
    A = [almond(t) for t in ts]
    O = []
    for (x, y) in A:
        if outer_circle:                      # gnomonic radius: the band ends on a circle of the ball
            L = math.hypot(x, y)
            O.append((x * outer_circle / L, y * outer_circle / L))
            continue
        if poly:
            L = math.hypot(x, y)
            d = ray_poly(x / L, y / L)
            s_ = max((d or L * out) * beyond / L, lip * 1.15)
        else:
            s_ = out
        O.append((x * s_, y * s_))
    R0 = [bm.verts.new(c + to_dir(*a) * (r + gap)) for a in A]
    R1 = [bm.verts.new(c + to_dir(*q) * (r + gap)) for q in O]
    R2 = [bm.verts.new(c + to_dir(*q) * (r + thick)) for q in O]
    R2m = [bm.verts.new(c + to_dir(a[0] * lip, a[1] * lip) * (r + thick)) for a in A]
    R3 = [bm.verts.new(c + to_dir(*a) * (r + thick * 0.8)) for a in A]
    keys = []
    for q in range(n):
        q1 = (q + 1) % n
        for Ar, Br, key in ((R0, R1, 'lid'), (R1, R2, 'lid'), (R2, R2m, 'lid'), (R2m, R3, 'lip'), (R3, R0, 'lip')):
            bm.faces.new([Ar[q], Ar[q1], Br[q1], Br[q]])
            keys.append(key)
    recalc_normals(bm)
    return bm, keys


def eye_dome(floor_pts, axis, gaze, height=0.006, shrink=0.975, n=8, back=((0.85, 0.003), (0.6, 0.007), (0.25, 0.010)),
             pupil=0.0045, lid_circle=0.92, follow=False):
    """The eye fitted to its socket (eyeball first: the ball is the sphere through the socket floor that bulges
    `height` above it; this is its visible cap). A closed n x n dome patch over the body's 4-vertex floor ring
    (shrunk `shrink` about its centre, edges kept straight so no body chord dips into it), interior vertices on
    the ball sphere, closed by a convex bowl `back` = [(scale, depth)] behind the floor plane; plus a 7-sided pupil
    cone (ring sunk in the ball, tip 1.2 mm proud) where the gaze meets it (a shell under 8 triangles: ftest eye_fit measures the
    ball). Faces are keyed 'iris' inside the lid circle (lid_circle x the floor's inscribed radius) and 'fur'
    outside it (the socket corners read as skin), 'pupil' on the disc.
    Returns (bmesh, keys, ball centre, ball radius, the floor's smallest inscribed half size)."""
    P = [Vector(p) for p in floor_pts]
    o = Vector(axis).normalized()
    m = sum(P, Vector()) / 4
    mids = [((P[i] + P[(i + 1) % 4]) / 2 - m).length for i in range(4)]
    db = sum(mids) / 4                                                             # inscribed half size
    dmin = min(mids)
    r = (db * db + height * height) / (2 * height)
    c = m - o * (r - height)
    Q = [m + (p - m) * shrink for p in P]
    g = Vector(gaze).normalized()
    bm = bmesh.new()
    lim = math.atan(lid_circle * dmin / (r - height))

    def grid(depth, sphere):
        G = []
        for i in range(n + 1):
            row = []
            for j in range(n + 1):
                u, v = i / n, j / n
                q = Q[0] * (1 - u) * (1 - v) + Q[1] * u * (1 - v) + Q[2] * u * v + Q[3] * (1 - u) * v
                if sphere and 0 < i < n and 0 < j < n:
                    s_ = c + (q - c).normalized() * r
                    if follow or (s_ - m).dot(o) > (q - m).dot(o):
                        q = s_
                elif not sphere and 0 < i < n and 0 < j < n:
                    q = q - o * depth
                row.append(q)
            G.append(row)
        return G
    F = grid(0, True)
    V = {}
    for i in range(n + 1):
        for j in range(n + 1):
            V[(i, j)] = bm.verts.new(F[i][j])
    keys = []
    for i in range(n):
        for j in range(n):
            f = bm.faces.new([V[(i, j)], V[(i + 1, j)], V[(i + 1, j + 1)], V[(i, j + 1)]])
            keys.append('iris' if (f.calc_center_median() - c).angle(o) < lim else 'fur')
    # the back: a convex bowl of rings (scale, depth) behind the boundary, closed by a fan (a rounded back keeps
    # the inside/outside sign of ftest's nearest-face test right all round)
    edge = [V[(i, 0)] for i in range(n)] + [V[(n, j)] for j in range(n)] + [V[(i, n)] for i in range(n, 0, -1)] +            [V[(0, j)] for j in range(n, 0, -1)]
    prev = edge
    for sc, dp in back:
        row = [bm.verts.new(m + (v.co - m) * sc - o * dp) for v in edge]
        for a_ in range(len(edge)):
            b_ = (a_ + 1) % len(edge)
            bm.faces.new([prev[b_], prev[a_], row[a_], row[b_]])
            keys.append('fur')
        prev = row
    tip = bm.verts.new(m - o * (back[-1][1] + 0.0015))
    for a_ in range(len(prev)):
        bm.faces.new([prev[(a_ + 1) % len(prev)], prev[a_], tip])
        keys.append('fur')
    # the pupil: a 7-gon disc on the gaze, 0.7 mm proud
    pc = c + g * (r - 0.0004)
    _, u, w = eye_frame(g)
    ring_ = [bm.verts.new(pc + (u * math.cos(t) + w * math.sin(t)) * pupil) for t in [2 * math.pi * q / 7 for q in range(7)]]
    cv = bm.verts.new(pc + g * 0.0016)                  # a low cone: its ring sits in the ball, its tip 1.2 mm proud
    for q in range(7):
        bm.faces.new([ring_[q], ring_[(q + 1) % 7], cv])
        keys.append('pupil')
    recalc_normals(bm)
    return bm, keys, c, r, dmin


# ============================================================ detail pieces
def mass(bm, centre, axes, segs=8, polar=(0, 40, 80, 120, 160, 180), lay=None, lay_k=0.0, squash=None):
    """A chunky smooth lump: a low lat-long ellipsoid. axes = (a, b, c) vectors (the c axis is the pole); lay: a
    direction the top half leans along by lay_k x |c| (fur laid back). squash(v_local) -> scale tweak (optional)."""
    a, b, cax = (Vector(x) for x in axes)
    C = Vector(centre)
    rows = []
    for pd in polar:
        th = math.radians(pd)
        if pd in (0, 180):
            rows.append([bm.verts.new(C + cax * math.cos(th) + (Vector(lay) * lay_k * cax.length * max(0, math.cos(th))
                                                                  if lay else Vector()))])
        else:
            row = []
            for q in range(segs):
                ph = 2 * math.pi * q / segs
                p = C + cax * math.cos(th) + (a * math.cos(ph) + b * math.sin(ph)) * math.sin(th)
                if lay:
                    p += Vector(lay) * lay_k * cax.length * max(0.0, math.cos(th)) ** 1.5
                row.append(bm.verts.new(p))
            rows.append(row)
    for ri in range(len(rows) - 1):
        A, Bv = rows[ri], rows[ri + 1]
        for q in range(segs):
            q1 = (q + 1) % segs
            if len(A) == 1:
                bm.faces.new([A[0], Bv[q], Bv[q1]])
            elif len(Bv) == 1:
                bm.faces.new([A[q], Bv[0], A[q1]])
            else:
                bm.faces.new([A[q], Bv[q], Bv[q1], A[q1]])
    return bm


def surf_mass(bm, loft, a, b, t, jf, sa, sb, sn, lay=None, lay_k=0.0, sink=0.45, **kw):
    """A mass seated on the loft surface between sections a and b (t, jf as Loft.surf): sa along the spine, sb
    round the ring, sn out of the surface (the pole); its centre sunk sink x sn under the surface."""
    p, n = loft.surf(a, b, t, jf)
    ax = (loft.centre(b) - loft.centre(a)).normalized()
    ta = (ax - n * ax.dot(n)).normalized()
    tb = n.cross(ta).normalized()
    return mass(bm, p - n * sink * sn, (ta * sa, tb * sb, n * sn), lay=lay, lay_k=lay_k, **kw)


def frame3(n):
    n = Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)))
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    return n, u, n.cross(u)


def lens(bm, c, n, r, h):
    """t7r's low-poly eye: back cone, iris ring, pupil fan. Returns the pupil faces."""
    n, u, w = frame3(n)
    ring_ = lambda rad, off: [bm.verts.new(c + n * off + (u * math.cos(t) + w * math.sin(t)) * rad)
                              for t in [k_ * math.pi / 3 for k_ in range(6)]]
    R, I = ring_(r, 0.0), ring_(r * 0.5, h * 0.65)
    A, Bv = bm.verts.new(c + n * h), bm.verts.new(c - n * h * 1.2)
    pup = []
    for j in range(6):
        a, b = j, (j + 1) % 6
        bm.faces.new([Bv, R[b], R[a]])
        bm.faces.new([R[a], R[b], I[b], I[a]])
        pup.append(bm.faces.new([I[a], I[b], A]))
    return pup


def clump(bm, a, n, lay, s, L):
    """t7r's chunky fur clump: a sunk square base, a narrower mid ring, a tip laid back along `lay`."""
    n, lay = Vector(n).normalized(), Vector(lay).normalized()
    u = n.cross(lay).normalized(); w = u.cross(n)
    b = a - n * 0.025
    base = [bm.verts.new(b + u * su * s + w * sw * s) for su, sw in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    m = a + n * 0.018 + lay * L * 0.4
    mid = [bm.verts.new(m + u * su * s * 0.6 + w * sw * s * 0.5) for su, sw in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    tip = bm.verts.new(a + n * L * 0.3 + lay * L)
    bm.faces.new(list(reversed(base)))
    for j in range(4):
        bm.faces.new([base[j], base[(j + 1) % 4], mid[(j + 1) % 4], mid[j]])
        bm.faces.new([mid[j], mid[(j + 1) % 4], tip])


def clumps(loft, spec):
    """spec: [(a, b, t, jf, lay, s, L)] -> a bmesh of t7r clumps on the loft surface."""
    bm = bmesh.new()
    for a, b, t, jf, lay, s_, L_ in spec:
        p, n_ = loft.surf(a, b, t, jf)
        clump(bm, p, n_, Vector(lay), s_, L_)
    return bm


def nails(bm, soles, offsets=(-0.036, -0.012, 0.012, 0.036), root=(0.011, 0.010), mid=(0.009, 0.008),
          tip=(0.006, 0.005), z=(0.017, 0.013, 0.009), lead=0.004):
    """wolf_t7's blunt nails: a tapered 4-sided box per toe, root buried in the toe, square blunt end.
    soles: [((cx, cy, cz), rx, ry), ...] (the paw's ground section)."""
    for (cx, cy, _), rx, ry in soles:
        for d in offsets:
            yf = cy - ry * (1 - 0.40 * (abs(d) / rx) ** 2) + 0.004
            x = cx + d
            ld = lead if abs(d) < 0.02 else 0.0
            box = lambda y, zz, hw, hh: [bm.verts.new(p_) for p_ in ((x - hw, y, zz - hh), (x + hw, y, zz - hh),
                                                                     (x + hw, y, zz + hh), (x - hw, y, zz + hh))]
            r0 = box(yf + 0.012, z[0], *root)
            r1 = box(yf - 0.012 - ld, z[1], *mid)
            r2 = box(yf - 0.024 - ld, z[2], *tip)
            bm.faces.new(list(reversed(r0)))
            for ra, rb in ((r0, r1), (r1, r2)):
                for j in range(4):
                    bm.faces.new([ra[j], ra[(j + 1) % 4], rb[(j + 1) % 4], rb[j]])
            bm.faces.new(r2)
    return bm


def piece(name, bm, palette, rule, mirror=True):
    """object_from_bm + paint in one call."""
    ob = object_from_bm(name, bm, mirror=mirror)
    paint(ob, palette, rule)
    return ob


# ============================================================ rig
def bones_from_plan(plan, J):
    """The plan's bone table [name, head joint, tail joint, parent, connect] -> the bmkit.armature list."""
    out = []
    for b in plan['bones']:
        nm, h, t, par = b[:4]
        con = bool(b[4]) if len(b) > 4 else False
        row = (nm, J[h], J[t], par) + ((True,) if con else ())
        out.append(row)
    return out


def _frames(d):
    return {int(f): {b: tuple(v) for b, v in keys.items()} for f, keys in d.items()}


def clips_from_plan(rig, plan, names=('idle', 'move', 'attack')):
    for nm in names:
        c = plan['clips'][nm]
        clip(rig, nm, _frames(c['rot']), loc=_frames(c['loc']) if c.get('loc') else None)


def trot(rig, name='move', frames=24, A=16.0, L=0.58, step=2, flex=None, tail='tail1', tail_deg=5.0, root='hips',
         ground=None, lift_pow=1.0, sign=None, v=None, flight=None, pre=0.0, hold=0.0):
    """A root-motion trot: diagonal pairs (LF + RH, then RF + LH), each leg's swing bone sweeping linearly from
    +A (forward, roll='auto') to -A through its stance while the root moves forward at the stance foot's speed
    (2 L sin A per half cycle), so stance paws stay planted; swing legs flex (flex = {bone: deg at mid-swing}).
    The last frame repeats the first pose (the clip loops; the root travels)."""
    flex = flex or {}
    half = frames / 2.0
    v = 2 * L * math.sin(math.radians(A)) / half if v is None else v
    legs = {'upperarm.L': 0.0, 'thigh.R': 0.0, 'upperarm.R': 0.5, 'thigh.L': 0.5}
    pair = {'upperarm.L': ('.L', 'fore'), 'upperarm.R': ('.R', 'fore'), 'thigh.L': ('.L', 'hind'), 'thigh.R': ('.R', 'hind')}
    keys, loc = {}, {}
    for f in range(1, frames + 2, step):
        ph = ((f - 1) / frames) % 1.0
        K = {}
        for bone, off in legs.items():
            p = (ph + off) % 1.0
            sd, kind = pair[bone]
            if p < 0.5:                                                   # stance: +A -> -A
                th = A * (1 - 4 * p)
                fl = 0.0 if (pre <= 0 or p < 0.5 - pre) else 0.6 * (p - 0.5 + pre) / pre    # toe-off: the paw folds before the swing
            else:                                                         # swing: -A -> +A, flexing
                q = (p - 0.5) * 2
                qs = max(0.0, (q - hold) / (1 - hold))                   # lift first, then swing forward
                th = A * (-1 + 2 * qs)
                fl = math.sin(math.pi * q) ** lift_pow           # < 1: the paw lifts at once, lands late
            sg = sign or {}
            K[bone] = (sg.get(bone, 1) * th, 0, 0)
            for fb, deg in flex.get(kind, {}).items():
                K[fb + sd] = (sg.get(fb + sd, 1) * deg * fl, 0, 0)
        K[tail] = (0, 0, tail_deg * math.sin(2 * math.pi * ph))
        keys[f] = K
        loc[f] = {root: (0.0, v * (f - 1), 0.0)}
    if ground is not None:
        return grounded(rig, ground, name, keys, loc=loc, root=root, flight=flight)
    return clip(rig, name, keys, loc=loc)


def lowest_z(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    z = 1e9
    for o in objs:
        oe = o.evaluated_get(dg)
        me = oe.to_mesh()
        mw = o.matrix_world
        z = min(z, min((mw @ v.co).z for v in me.vertices))
        oe.to_mesh_clear()
    return z


def grounded(rig, objs, name, keys, loc=None, root='hips', flight=None):
    """clip() whose root height is solved per key so the lowest vertex of objs touches z = 0 (a stance paw that
    rotates about the shoulder digs its toes in at the back of the stride; the body rises over it instead)."""
    act = clip(rig, name, keys, loc=loc)
    ad = rig.animation_data
    frames = sorted(set(keys) | set(loc or {}))
    dz = {}
    for f in frames:
        B.pose(rig, act, f)
        dz[f] = -lowest_z(objs)
    ad.action = None
    B.rest(rig)
    bpy.context.scene.frame_set(1)
    for tr in list(ad.nla_tracks):
        if tr.name == name:
            ad.nla_tracks.remove(tr)
    bpy.data.actions.remove(act)
    loc2 = {}
    for f in frames:
        base = dict((loc or {}).get(f, {}))
        x, y, z = base.get(root, (0.0, 0.0, 0.0))
        base[root] = (x, y, z + dz[f] + (flight or {}).get(f, 0.0))
        loc2[f] = base
    say_ = getattr(B, 'say')
    say_('GROUNDED', name, {f: round(d, 4) for f, d in dz.items()})
    return clip(rig, name, keys, loc=loc2)


def drop_clip(rig, name):
    """Remove a clip made by clip() (its NLA track and action)."""
    ad = rig.animation_data
    ad.action = None
    for tr in list(ad.nla_tracks):
        if tr.name == name:
            ad.nla_tracks.remove(tr)
    if name in bpy.data.actions:
        bpy.data.actions.remove(bpy.data.actions[name])
    B.rest(rig)
    bpy.context.scene.frame_set(1)


def foot_drift(rig, body, act, group, frames):
    """World-y drift per frame of the vertex of `group` (weight >= 0.5) lowest at the middle frame, over `frames`."""
    gi = {g.index: g.name for g in body.vertex_groups}
    ix = [v.index for v in body.data.vertices if any(gi.get(g.group) == group and g.weight >= 0.5 for g in v.groups)]
    dg = bpy.context.evaluated_depsgraph_get()

    def pos(f):
        B.pose(rig, act, f)
        oe = body.evaluated_get(dg)
        me = oe.to_mesh()
        P = {i: body.matrix_world @ me.vertices[i].co for i in ix}
        oe.to_mesh_clear()
        return P
    mid = pos(frames[len(frames) // 2])
    k = min(ix, key=lambda i: mid[i].z)
    a, b = pos(frames[0])[k], pos(frames[-1])[k]
    return (b.y - a.y) / (frames[-1] - frames[0])


def swing_signs(rig, names, deg=10.0):
    """For each bone: +1 if a +X rotation moves its tail forward (-Y), else -1. Clip angles written as 'positive =
    tip forward' are multiplied by this, so both sides of a mirrored rig agree whatever their rolls."""
    out = {}
    for nm in names:
        pb = rig.pose.bones[nm]
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)
        bpy.context.view_layer.update()
        t0 = (rig.matrix_world @ pb.tail).copy()
        pb.rotation_euler = (math.radians(deg), 0, 0)
        bpy.context.view_layer.update()
        t1 = (rig.matrix_world @ pb.tail).copy()
        pb.rotation_euler = (0, 0, 0)
        bpy.context.view_layer.update()
        out[nm] = 1 if t1.y < t0.y else -1
    return out


def signed(keys, sgn):
    """keys {frame: {bone: (rx, ry, rz)}} with each bone X angle multiplied by sgn[bone] (default 1)."""
    return {f: {b: (v[0] * sgn.get(b, 1), v[1], v[2]) for b, v in d.items()} for f, d in keys.items()}


def self_hits(ob, top=8):
    """Diagnostic: crossing triangle pairs of the evaluated mesh (pairs sharing a vertex excluded) and where."""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    oe = ob.evaluated_get(dg)
    me = oe.to_mesh()
    me.calc_loop_triangles()
    V = [ob.matrix_world @ v.co for v in me.vertices]
    T = [tuple(t.vertices) for t in me.loop_triangles]
    oe.to_mesh_clear()
    tr = BVHTree.FromPolygons(V, T, all_triangles=True)
    pr = [(i, j) for i, j in tr.overlap(tr) if i < j and not set(T[i]) & set(T[j])]
    cen = lambda t: tuple(round(x, 3) for x in sum((V[k] for k in t), Vector()) / 3)
    return len(pr), [(cen(T[i]), cen(T[j])) for i, j in pr[:top]]


def sweep_mass(bm, pts, sides, norms, a, b, segs=10, sink=0.35, cap=0.6):
    """ONE smooth tube mass along a path: at each point an ellipse of half width a[i] along sides[i] and half
    depth b[i] along norms[i] (outward), its centre sunk sink x b under the path point; the ends close in a
    soft point cap x a beyond the end rings. Returns the bmesh."""
    C = [Vector(p) - Vector(nv).normalized() * sink * bb for p, nv, bb in zip(pts, norms, b)]
    rings = []
    for c_, sv, nv, aa, bb in zip(C, sides, norms, a, b):
        sv, nv = Vector(sv).normalized(), Vector(nv).normalized()
        rings.append([bm.verts.new(c_ + sv * aa * math.cos(2 * math.pi * q / segs) + nv * bb * math.sin(2 * math.pi * q / segs))
                      for q in range(segs)])
    for i in range(len(rings) - 1):
        A_, B_ = rings[i], rings[i + 1]
        for q in range(segs):
            bm.faces.new([A_[q], A_[(q + 1) % segs], B_[(q + 1) % segs], B_[q]])
    t0 = (C[0] - C[1]).normalized(); t1 = (C[-1] - C[-2]).normalized()
    p0 = bm.verts.new(C[0] + t0 * cap * a[0]); p1 = bm.verts.new(C[-1] + t1 * cap * a[-1])
    for q in range(segs):
        bm.faces.new([rings[0][(q + 1) % segs], rings[0][q], p0])
        bm.faces.new([rings[-1][q], rings[-1][(q + 1) % segs], p1])
    recalc_normals(bm)
    return bm


def eye_pad(body, c, r, axis, floor_pts, almond, tilt=0.0, n=20, steps=(0.0, 0.14, 0.4, 0.7, 1.0), outer=1.1,
            lift=0.0038, gap=0.0014, dive=0.002, point=0.6, up=(0, 0, 1)):
    """The lids as one rounded pad (replaces lids()): an almond opening on the ball (centre c, radius r), a dark
    lip, and a skin that follows the body surface out to a circle `outer` x the socket floor corner radius,
    where it dives `dive` under the skin. Inside the floor ring the pad lies on the ball, outside it on the body
    (ray cast), `lift` proud on its outer skin and `gap` on its inner skin, so it crosses the body along ONE loop
    and hides the 4-sided socket rim. almond = (half width, half height up, half height down) as tangents round
    `axis`. Returns (bmesh, per-face keys 'lip' | 'lid')."""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    tree = BVHTree.FromObject(body, dg)
    bm = bmesh.new()
    o, h, v = eye_frame(axis, up)
    c = Vector(c)
    poly = []
    for p in floor_pts:
        d = Vector(p) - c
        poly.append((d.dot(h) / d.dot(o), d.dot(v) / d.dot(o)))
    Rout = outer * max(math.hypot(*q) for q in poly)
    m = sum((Vector(p) for p in floor_pts), Vector()) / len(floor_pts)
    ct, st = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
    hw, uh, lh = almond

    def alm(t):
        x = math.copysign(abs(math.cos(t)) ** point, math.cos(t)) * hw
        y = math.sin(t) * (uh if math.sin(t) >= 0 else lh)
        return x * ct - y * st, x * st + y * ct

    def inside(x, y):
        ins = False
        for i in range(len(poly)):
            (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % len(poly)]
            if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
                ins = not ins
        return ins

    def surf(x, y):
        d = (o + h * x + v * y).normalized()
        if not inside(x, y):
            loc, nrm, idx, dist = tree.ray_cast(c + d * 0.08, -d, 0.2)
            if loc is not None:
                return Vector(loc), d
        tp = (m - c).dot(o) / max(1e-6, d.dot(o))              # the floor plane along d: never under the dome corners
        return c + d * max(r, tp), d
    ts = [2 * math.pi * q / n for q in range(n)]
    OUT, INN = [], []
    for k_, s_ in enumerate(steps):
        ro, ri = [], []
        for t in ts:
            ax_, ay_ = alm(t)
            L = math.hypot(ax_, ay_)
            x, y = ax_ * (1 - s_) + ax_ / L * Rout * s_, ay_ * (1 - s_) + ay_ / L * Rout * s_
            base, d = surf(x, y)
            if s_ >= 1.0:
                e = bm.verts.new(base - d * dive)
                ro.append(e); ri.append(e)
            else:
                ro.append(bm.verts.new(base + d * (lift * (0.8 if k_ == 0 else 1.0))))
                ri.append(bm.verts.new(base + d * gap))
        OUT.append(ro); INN.append(ri)
    keys = []
    for k_ in range(len(steps) - 1):
        for q in range(n):
            q1 = (q + 1) % n
            for R, rev in ((OUT, False), (INN, True)):
                a_, b_ = R[k_], R[k_ + 1]
                f = [a_[q], a_[q1], b_[q1], b_[q]]
                if rev:
                    f = f[::-1]
                if len(set(f)) == 4:
                    bm.faces.new(f)
                    keys.append('lip' if (R is OUT and k_ == 0) else 'lid')
    for q in range(n):                                          # the lip wall round the opening
        q1 = (q + 1) % n
        bm.faces.new([INN[0][q], INN[0][q1], OUT[0][q1], OUT[0][q]])
        keys.append('lip')
    recalc_normals(bm)
    return bm, keys


# ============================================================ S1 gates (v4)
V4_IOU = dict(side=0.76, front=0.84, top=0.80)


def s1_gates(k, body, J, plan, floors=V4_IOU, pct=10.0, intended=None, res=512):
    """The v4 stage-1 shape gates: silhouette IoU against the sheet masks (side / front / top floors) and the
    proportion table within pct % (a ratio named in `intended` is reported, not gated). Prints BMK PASS/FAIL
    lines and writes stage1/v4_gates.json. Returns ok."""
    bp = json.load(open(k.path('blueprint.json')))
    fr = B.bp_frame(bp)
    mm, rm = B.ortho_masks(fr, res), B.ref_masks(bp, fr, res)
    ious = {v: round(B.iou(mm[v], rm[v]), 3) for v in ('side', 'front', 'top')}
    prop = B.proportions(body, J, bp, plan, res=res, masks_=(mm, rm))
    intended = intended or {}
    ok = True
    for v, f in floors.items():
        ok &= B._gate(f's1 v4 IoU {v} >= {f}', ious[v] >= f, f'{ious[v]}')
    bad = {n: d['diff_pct'] for n, d in prop.items() if abs(d['diff_pct']) > pct and n not in intended}
    ok &= B._gate(f's1 v4 proportions within {pct:g}% of the sheet', not bad,
                  ', '.join(f'{n} {d:+.1f}%' for n, d in bad.items()) or 'all within')
    B._dump(k.path('stage1', 'v4_gates.json'), dict(iou=ious, floors=floors, proportions=prop, intended=intended, ok=bool(ok)))
    return ok


# ============================================================ best-of-N (S1)
def best_of(k, trees, bp_path, J, plan, res=256, miss_pct=10.0, keep=None):
    """Build each candidate shell, measure IoU (side / front / top) against the sheet masks and the proportion
    table; score = mean IoU - 0.02 x (proportions off by more than miss_pct). Writes stage1/bestof.json, deletes
    the losers and returns (winner object, loft, index). keep: force an index (after the choice is fixed)."""
    bp = json.load(open(bp_path))
    fr = B.bp_frame(bp)
    rm = B.ref_masks(bp, fr, res)
    rows, cands = [], []
    for i, tree in enumerate(trees):
        for o, _ in cands:
            o.hide_render = True
        ob, loft = build_body(tree)
        mm = B.ortho_masks(fr, res)
        ious = {v: round(B.iou(mm[v], rm[v]), 3) for v in ('side', 'front', 'top')}
        prop = B.proportions(ob, J, bp, plan, res=res, masks_=(mm, rm))
        miss = [n for n, d in prop.items() if abs(d['diff_pct']) > miss_pct]
        rep = B.report(ob, intersections=True)
        score = sum(ious.values()) / 3 - 0.02 * len(miss) - (1.0 if rep['self_intersections'] else 0.0)
        rows.append(dict(i=i, label=tree.get('label', str(i)), iou=ious, score=round(score, 4), miss=miss,
                         proportions=prop, tris=rep['tris'], hits=rep['self_intersections']))
        cands.append((ob, loft))
        B.say('BESTOF', i, tree.get('label', ''), ious, 'score', round(score, 4), 'miss', miss, 'tris', rep['tris'])
    win = max(rows, key=lambda r: r['score'])['i'] if keep is None else keep
    B._dump(k.path('stage1', 'bestof.json'), dict(rows=rows, winner=win))
    ob, loft = cands[win]
    for j, (o, _) in enumerate(cands):
        if j != win:
            bpy.data.objects.remove(o, do_unlink=True)
    ob.hide_render = False
    return ob, loft, win
