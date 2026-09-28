"""Crab: a chunky stylised game crab, box-modelled in four stages.

Built as the left half (x >= 0) under the live mirror. The shell is a stack of
concentric half rings (16 vertices each, front seam -> round the left flank ->
back seam): the carapace top plateau, its shoulder ring, the toothed rim, the
rim underside, and three body rings under the overhang, closed by the sternum.
The sectors between ring vertices are laid out for the limbs: the claw comes
out of two stacked body quads at the front corner (a hexagonal arm), the four
walking legs out of single quads of the lower body band (diamond sections),
with narrow spacer sectors between them.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'kit'))
from bmkit import *

META = dict(creature='crab', model='opus', engine_glb='', stage1_tris=(400, 1500), total_tris=(500, 3000))

# ----------------------------------------------------------------------------- the skeleton the model is built on
# legs: coxa end, knee (merus/carpus), ankle (propodus/dactyl), tip. Claw: coxa, elbow, wrist, palm, finger.
def leg_plane(coxa, theta, mid, knee, ankle, tip, sweep=0.0):
    """A walking leg laid out in the vertical plane through its coxa at theta degrees from +X (+ = backward):
    mid/knee/ankle are (s, z) in that plane (s = horizontal distance from the coxa), tip is s at z = 0.
    sweep (AD r3): the tip moved off the plane, sideways (+ = backward), so the dactyl's bend shows side-on."""
    import math as _m
    h = (_m.cos(_m.radians(theta)), _m.sin(_m.radians(theta)))
    at_ = lambda s, z, t=0.0: (round(coxa[0] + h[0] * s - h[1] * t, 4), round(coxa[1] + h[1] * s + h[0] * t, 4), z)
    return dict(coxa=coxa, mid=at_(*mid), knee=at_(*knee), ankle=at_(*ankle), tip=at_(tip, 0.0, sweep))


# AD r3 note 1 (stage-1 unlock: body height + walking legs): the whole body (shell, claws, eyes) sits DZ lower,
# so the underside is ~15 % of the body height off the ground. Every body height below is written at the old
# height and shifted by DZ; the walking-leg knees/ankles are written at their final world height.
DZ = -0.075
_dz = lambda p: (p[0], p[1], round(p[2] + DZ, 4))
CZ = 0.175 + DZ                                  # the coxa height of every walking leg
J = dict(
    body=_dz((0.0, 0.10, 0.22)), body_end=_dz((0.0, -0.18, 0.22)),
    # AD r3 note 1: short legs with two bends. The knee sits between the rim and the carapace top (z .27-.31),
    # the carpus/propodus drops steeply out (~24 % shorter below the knee than r2), and the dactyl angles back IN
    # under the body (tip s < ankle s): a second bend at ~70 % of the leg. Pairs splayed: front 20 deg further
    # forward, rear 22 deg further back (-45 / -12 / +20 / +55 deg).
    l1=leg_plane((0.36, -0.085, CZ), -45, (0.16, CZ + 0.030), (0.26, 0.285), (0.35, 0.100), 0.320, -0.030),
    l2=leg_plane((0.37, 0.012, CZ), -12, (0.12, CZ + 0.053), (0.26, 0.31), (0.37, 0.110), 0.335, -0.045),
    l3=leg_plane((0.36, 0.105, CZ), 20, (0.12, CZ + 0.053), (0.26, 0.30), (0.37, 0.105), 0.335, 0.045),
    l4=leg_plane((0.32, 0.20, CZ), 55, (0.105, CZ + 0.050), (0.23, 0.27), (0.34, 0.090), 0.310, 0.035),
    claw={n: _dz(p) for n, p in dict(
              coxa=(0.30, -0.21, 0.20), elbow=(0.43, -0.28, 0.25), wrist=(0.44, -0.37, 0.30),
              palm0=(0.42, -0.42, 0.33), palm1=(0.365, -0.49, 0.35), palm2=(0.30, -0.55, 0.35),
              dac0=(0.265, -0.595, 0.40), dac1=(0.205, -0.635, 0.415), dac_tip=(0.13, -0.665, 0.385),
              pol0=(0.27, -0.59, 0.30), pol1=(0.21, -0.63, 0.295), pol_tip=(0.14, -0.66, 0.33)).items()},
    eye=_dz((0.12, -0.30, 0.33)), eye_end=_dz((0.13, -0.31, 0.46)),
)
LEGS = ['l1', 'l2', 'l3', 'l4']
# AD r2 note 2 (stage 2): the knee lowered, the ankle out and up (a second bend), the tip further out, graded
# front -> back: (knee dz, ankle ds, ankle dz, tip ds) in each leg's vertical plane. Stage 2 moves the mesh
# joints by these; LEG2 is the moved skeleton that paint and the rig use (J itself stays the stage-1 skeleton).
# AD r3: the second bend now lives in stage 1, so stage 2 no longer moves the leg joints.
LEG_D = dict(l1=(0.0, 0.0, 0.0, 0.0), l2=(0.0, 0.0, 0.0, 0.0),
             l3=(0.0, 0.0, 0.0, 0.0), l4=(0.0, 0.0, 0.0, 0.0))


LEG_F = 1.0                                     # the fraction of LEG_D the IoU > 0.9 floor allows


def leg_h(leg):
    L = J[leg]
    return Vector((L['tip'][0] - L['coxa'][0], L['tip'][1] - L['coxa'][1], 0.0)).normalized()


def leg_delta(leg, joint):
    dk, das, daz, dts = (x * LEG_F for x in LEG_D[leg])
    h = leg_h(leg)
    return {'knee': Vector((0, 0, dk)), 'ankle': h * das + Vector((0, 0, daz)), 'tip': h * dts}.get(joint, Vector())


LEG2 = {leg: {j: tuple(Vector(p) + leg_delta(leg, j)) for j, p in J[leg].items()} for leg in LEGS}
LEG_SECTOR = dict(l1=6, l2=8, l3=10, l4=12)     # body sector j..j+1 (lower band) each leg grows from
LABEL, PART = {}, []                            # stage 1 part label of every base vertex (paint and rig use them)
BUILT = {}                                      # stage 1 records its limb section positions here (stage 2 finds them)
CLAW_SECTOR = 4                                 # both body bands, sector 4..5

# ----------------------------------------------------------------------------- outlines (x, y), 16 per half ring
# S: the carapace outline without teeth, front seam -> left flank -> back seam
S = [(0.000, -0.325), (0.070, -0.325), (0.135, -0.315), (0.195, -0.305), (0.255, -0.280), (0.315, -0.245),
     (0.365, -0.200), (0.410, -0.150), (0.440, -0.100), (0.455, -0.050), (0.440, 0.030), (0.395, 0.110),
     (0.325, 0.185), (0.235, 0.245), (0.125, 0.290), (0.000, 0.305)]
TEETH = {1: 0.015, 3: 0.035, 5: 0.035, 7: 0.035, 9: 0.030}      # rim vertices pushed out: the toothed front edge
NOTCH = {2: 0.012, 4: 0.010, 6: 0.010, 8: 0.008}
# B: the body under the overhang; its sectors are the limb roots (claw 4-5, legs 6-7, 8-9, 10-11, 12-13)
B = [(0.000, -0.235), (0.070, -0.235), (0.130, -0.228), (0.180, -0.218), (0.215, -0.200), (0.265, -0.125),
     (0.285, -0.095), (0.300, -0.035), (0.305, -0.010), (0.305, 0.050), (0.300, 0.075), (0.285, 0.130),
     (0.270, 0.155), (0.235, 0.205), (0.125, 0.228), (0.000, 0.235)]
C0 = Vector((0.0, -0.01, 0.0))
CROWN = (0.0, 0.01, 0.49 + DZ)             # centre the carapace rings shrink toward


def outward(pts, i):
    """In-plane outward normal of a half outline at vertex i."""
    a = Vector(pts[max(0, i - 1)] + (0,)); b = Vector(pts[min(len(pts) - 1, i + 1)] + (0,))
    t = (b - a).normalized()
    return Vector((t.y, -t.x, 0.0))


def shrink(pts, s, z):
    return [(C0.x + (x - C0.x) * s, C0.y + (y - C0.y) * s, z) for x, y in pts]


RIM_Z = [0.325, 0.325, 0.323, 0.320, 0.315, 0.308, 0.300, 0.294, 0.290, 0.290, 0.290, 0.292, 0.295,
         0.298, 0.300, 0.300]                   # the rim line: high at the front, sweeping down to the flanks


def rim_ring(dz=0.0):
    out = []
    for i, (x, y) in enumerate(S):
        p = Vector((x, y, RIM_Z[i] + dz))
        if i in TEETH:
            p += outward(S, i) * TEETH[i]
        if i in NOTCH:
            p -= outward(S, i) * NOTCH[i]
        if i in (0, 15):
            p.x = 0.0
        out.append(tuple(p))
    return out


RINGS = [  # name, points (top -> bottom)
    ('top', shrink(S, 0.50, 0.455)),
    ('mid', [(x, y, 0.430 - 0.015 * max(0.0, (-y - 0.12) / 0.12)) for x, y, _ in shrink(S, 0.78, 0)]),
    ('rim', rim_ring()),
    ('under', [(x, y, RIM_Z[i] - 0.026) for i, (x, y, _) in enumerate(shrink(S, 0.90, 0))]),
    ('bt', [(x, y, 0.240) for x, y in B]),
    ('bm', [(x, y, 0.200) for x, y in B]),
    ('bb', [(x * 0.85, y * 0.88, 0.150) for x, y in B]),
    ('bot', [(x * 0.45, y * 0.55, 0.128) for x, y in B]),
]
RINGS = [(n, [_dz(p) for p in pts]) for n, pts in RINGS]       # AD r3: the body DZ lower


# ----------------------------------------------------------------------------- helpers
def ext_place(bm, faces, order, pts):
    """Extrude a face region (E) and place its new boundary vertices (G).
    order: the region's boundary verts in template order; pts: their new positions."""
    pos = [v.co.copy() for v in order]
    r = extrude(bm, faces)
    new = [min(r['verts'], key=lambda w: (w.co - p).length) for p in pos]
    for w, p in zip(new, pts):
        w.co = Vector(p)
    return r['faces'], new


def point(bm, faces, order, p):
    """Close a limb end with a point: delete the end region, fan the boundary to one tip vertex."""
    bmesh.ops.delete(bm, geom=list(faces), context='FACES_ONLY')
    t = bm.verts.new(Vector(p))
    n = len(order)
    for i in range(n):
        bm.faces.new([order[i], order[(i + 1) % n], t])
    return t


def dirs(root, cs):
    """Bisector direction at each section centre along root -> cs."""
    pts = [Vector(root)] + [Vector(c) for c in cs]
    out = []
    for i in range(1, len(pts)):
        din = (pts[i] - pts[i - 1]).normalized()
        out.append((din + (pts[i + 1] - pts[i]).normalized()).normalized() if i + 1 < len(pts) else din)
    return out


def frame_up(d):
    """Section axes for a limb running along d: U (up, perpendicular to d) and F = d x U
    (front for a limb pointing out of the left flank; outer for a limb pointing forward)."""
    d = Vector(d).normalized()
    U = Vector((0, 0, 1)); U = (U - d * U.dot(d))
    if U.length < 1e-4:
        U = Vector((0, -1, 0)) - d * d.y * -1
    U.normalize()
    return U, d.cross(U)


def sections(bm, faces, order, root, secs):
    """secs: [(centre, [(u, f), ...] absolute offsets in the section frame), ...]"""
    ds = dirs(root, [s[0] for s in secs])
    rows = []
    for (c, tm), d in zip(secs, ds):
        U, F = frame_up(d)
        pts = [Vector(c) + U * u + F * f for u, f in tm]
        faces, order = ext_place(bm, faces, order, pts)
        rows.append(order)
    return faces, order, rows


def diamond(hu, hf, lift=0.0):
    """Leg section: front, top, back, bottom (the dark/pale border runs along front and back)."""
    return [(lift, hf), (hu, 0.0), (lift, -hf), (-hu, 0.0)]


def hexa(hu, hs, mid=0.0):
    """Claw/arm section: top-inner, top-outer, mid-outer, bottom-outer, bottom-inner, mid-inner.
    In the frame U, F: for the claw F = d x U points INWARD, so outer = -F."""
    return [(hu, 0.8 * hs), (hu, -0.8 * hs), (mid, -hs), (-hu, -0.8 * hs), (-hu, 0.8 * hs), (mid, hs)]


def quadsec(hu, hf):
    """Finger section: top-inner, top-outer, bottom-outer, bottom-inner (F = inward on the claw)."""
    return [(hu, hf), (hu, -hf), (-hu, -hf), (-hu, hf)]


def label(rows, tip, kind, name):
    for r, row in enumerate(rows):
        for v in row:
            LABEL.setdefault(v, (kind, name, r))
    if tip is not None:
        LABEL[tip] = (kind, name, 'tip')


def face_of(bm, vs):
    s = set(vs)
    return next(f for f in bm.faces if set(f.verts) == s)


# ----------------------------------------------------------------------------- stage 1
def stage1(k):
    bm = bmesh.new()
    R = {}
    for name, pts in RINGS:
        R[name] = ring(bm, pts)
    names = [n for n, _ in RINGS]
    for a, b in zip(names, names[1:]):
        bridge(bm, R[a], R[b])
    crown = bm.verts.new(Vector(CROWN))           # the top is a low pyramid fanned to one crown vertex
    for a, b in zip(R['top'], R['top'][1:]):
        bm.faces.new([a, b, crown])
    cap(bm, list(reversed(R['bot'])))

    bt, bmid, bb = R['bt'], R['bm'], R['bb']
    # --- walking legs: one lower-band quad each, diamond sections: coxa, merus, knee, ankle, pointed dactyl
    for leg in LEGS:
        j = LEG_SECTOR[leg]
        order = [bmid[j], bmid[j + 1], bb[j + 1], bb[j]]          # front-top, back-top, back-bottom, front-bottom
        f = face_of(bm, order)
        root = centre(order)
        L = J[leg]
        secs = [(L['coxa'], diamond(0.038, 0.030)),
                (L['mid'], diamond(0.055, 0.032)),
                (L['knee'], diamond(0.042, 0.030)),
                (L['ankle'], diamond(0.030, 0.024))]
        faces, order, rows = sections(bm, [f], order, root, secs)
        t = point(bm, faces, order, L['tip'])
        BUILT[leg] = [[tuple(v.co) for v in r] for r in rows]
        label(rows, t, 'leg', leg)

    # --- claw: two stacked quads at the front corner -> hexagonal arm -> swollen palm -> two fingers
    j = CLAW_SECTOR
    order = [bt[j], bt[j + 1], bmid[j + 1], bb[j + 1], bb[j], bmid[j]]
    fs = [face_of(bm, [bt[j], bt[j + 1], bmid[j + 1], bmid[j]]), face_of(bm, [bmid[j], bmid[j + 1], bb[j + 1], bb[j]])]
    root = centre(order)
    C = J['claw']
    secs = [(C['coxa'], hexa(0.042, 0.040)),
            (C['elbow'], hexa(0.050, 0.046)),
            (C['wrist'], hexa(0.042, 0.040)),
            (C['palm0'], hexa(0.110, 0.085)),
            (C['palm1'], hexa(0.140, 0.100)),
            (C['palm2'], hexa(0.110, 0.080))]
    faces, P, rows = sections(bm, fs, order, root, secs)
    BUILT['claw'] = [[tuple(v.co) for v in r] for r in rows]
    label(rows, None, 'claw', 'claw')
    up = next(f for f in faces if P[0] in f.verts)
    lo = next(f for f in faces if P[3] in f.verts)
    # movable finger (dactyl) on top, fixed finger (pollex) below; they share the middle edge, the gape opens from it
    fsecs = [(C['dac0'], quadsec(0.045, 0.055)), (C['dac1'], quadsec(0.035, 0.042))]
    uf, uo, rows = sections(bm, [up], [P[0], P[1], P[2], P[5]], centre([P[0], P[1], P[2], P[5]]), fsecs)
    BUILT['dac'] = [[tuple(v.co) for v in r] for r in rows]
    label(rows, point(bm, uf, uo, C['dac_tip']), 'finger', 'dac')
    fsecs = [(C['pol0'], quadsec(0.040, 0.055)), (C['pol1'], quadsec(0.030, 0.040))]
    lf, lo_, rows = sections(bm, [lo], [P[5], P[2], P[3], P[4]], centre([P[5], P[2], P[3], P[4]]), fsecs)
    BUILT['pol'] = [[tuple(v.co) for v in r] for r in rows]
    label(rows, point(bm, lf, lo_, C['pol_tip']), 'finger', 'pol')

    for name, _ in RINGS:
        for i, v in enumerate(R[name]):
            LABEL[v] = ('ring', name, i)
    LABEL[crown] = ('crown', 'crown', 0)
    snap_seam(bm, 1e-4)
    # by base id - 1. The r3 lock is canonical: the kit stamps ids in position order (bmkit.canonical_order)
    r_ = lambda c: (round(c.x, 5), round(c.y, 5), round(c.z, 5))
    PART[:] = [LABEL.get(v) for v in sorted(bm.verts, key=lambda v: r_(v.co))]
    recalc_normals(bm)
    ob = object_from_bm('body', bm)
    if os.environ.get('CRAB_DBG'):
        debug_hits(ob)
    return ob


def close_ups(k, tag, objs=None):
    """Debug only (CRAB_CLOSE=1): closer renders of the whole crab into the scratch folder."""
    d = os.path.join(k.a.scratch, 'close')
    fr = dict(centre=[0.0, -0.10, 0.20], size=[1.55, 1.55, 1.55])
    shoot(d, tag, fr, views=['hero', 'az000', 'az045', 'az090', 'back34', 'top'], wire_views=['hero'], res=640, objs=objs,
          colour=any(o.type == 'MESH' and len(o.data.materials) > 0 for o in (objs or bpy.context.scene.objects)))
    say('CLOSE', d)


def debug_hits(ob):
    """Print the centres of self-intersecting face pairs (evaluated mesh)."""
    eb = evaluated_bm(ob)
    eb.faces.ensure_lookup_table()
    t = BVHTree.FromBMesh(eb)
    for i, j in t.overlap(t):
        if i < j and not (set(eb.faces[i].verts) & set(eb.faces[j].verts)):
            ci, cj = eb.faces[i].calc_center_median(), eb.faces[j].calc_center_median()
            say('HIT', tuple(round(x, 3) for x in ci), tuple(round(x, 3) for x in cj))


RING = {n: pts for n, pts in RINGS}
OPPART = {}                                     # stage-2 op number -> part label of the vertices it added


def at(bm, p, r=1e-4):
    """The base vertex at locked position p."""
    v = vert_near(bm, p)
    assert (v.co - Vector(p)).length < r, ('no vertex at', p, tuple(v.co))
    return v


def rv(bm, name, idx):
    return [at(bm, RING[name][i]) for i in idx]


def near_ring(bm, c, n=4):
    """The n base vertices nearest a limb section centre (its ring)."""
    return sorted(bm.verts, key=lambda v: (v.co - Vector(c)).length)[:n]


def plane_fit(free, pins, w=12.0):
    """Project `free` onto the least-squares plane of free + pins (pins weighted w, never moved).
    Seam vertices stay on the seam."""
    P = np.array([v.co[:] for v in free] + [v.co[:] for v in pins])
    W = np.array([1.0] * len(free) + [w] * len(pins))
    c = (P * W[:, None]).sum(0) / W.sum()
    n = np.linalg.svd((P - c) * np.sqrt(W)[:, None])[2][-1]
    for v in free:
        q = np.array(v.co[:])
        seam = abs(q[0]) < 1e-6
        q = q - np.dot(q - c, n) * n
        v.co = Vector(q)
        if seam:
            v.co.x = 0.0


def flat(vs):
    """flatten() that keeps mirror-seam vertices on the seam."""
    seam = [v for v in vs if abs(v.co.x) < 1e-6]
    flatten(vs)
    for v in seam:
        v.co.x = 0.0



def pole_ring(k, bm, pole, outer, t, reason, inner=None):
    """A logged ring round a pole: split every spoke pole -> outer[i] (or inner[i] -> outer[i]) at t from the inner
    end and join the new points across each face. Returns {i: new vert}."""
    rows = []
    for i, o in enumerate(outer):
        a = pole if inner is None else inner[i]
        e = next(e for e in o.link_edges if e.other_vert(o) is a)
        rows.append((i, e, a))
    with k.topo(bm, 'loop', reason):
        ms = {}
        for i, e, a in rows:
            _, m = bmesh.utils.edge_split(e, a, t)
            ms[i] = m
        for i in range(len(outer) - 1):
            m, n = ms[i], ms[i + 1]
            if set(m.link_faces) & set(n.link_faces):
                bmesh.ops.connect_verts(bm, verts=[m, n])
    OPPART[len(k.log.ops)] = ('ring', 'top', -1)
    return ms


def shape_ring(vs, d, su, sf, lift=0.0):
    """Scale a limb ring in its own section frame: su across the limb in the vertical plane, sf front-back;
    lift moves it along the section's up axis (an arch)."""
    U, F = frame_up(d)
    c = centre(vs)
    for v in vs:
        o = v.co - c
        v.co = c + U * (o.dot(U) * su + lift) + F * (o.dot(F) * sf) + d * o.dot(d)


RIDGES = (3, 7, 13)                              # spokes the carapace sector creases run along (per half)
PLATE_Z, PLATE_T = 0.492 + DZ, {3: 0.52, 7: 0.52, 13: 0.62}   # the flat central plate: height, corner fraction pole -> top ring
MID_S = {0: 0.80, 1: 0.80, 2: 0.81}              # shoulder ring slid out (default 0.85 of S): a shorter side wall


def _hz(pl, x, y):
    """Height of plane pl = (point, normal) at (x, y)."""
    p, n = pl
    return p.z - (n.x * (x - p.x) + n.y * (y - p.y)) / n.z


def _plane(a, b, q):
    n = (b - a).cross(q - a).normalized()
    return (a.copy(), n if n.z > 0 else -n)


def _ray_hit(o, t, a, b):
    """Where the horizontal ray o -> t meets the line a b (xy only); returns the xy point."""
    d, e = (t - o).to_2d(), (b - a).to_2d()
    den = d.x * e.y - d.y * e.x
    s = ((a.x - o.x) * e.y - (a.y - o.y) * e.x) / den
    return o.to_2d() + d * s


def crown_planes(crown, A, Bv, T, M):
    """AD r2 note 1: the carapace crown as a few big planes. A level central plate (the pole fan + the inner
    ring) and four sector planes per half (front plateau and back across the seam, a front side and a back side),
    each through its own straight plate edge; the creases between sectors run exactly along the ridge spokes
    (RIDGES), so no ring or spoke shades inside a sector. The shoulder ring is slid out and down onto the planes,
    which shortens the pleated side wall under it."""
    mir = lambda v: Vector((-v.x, v.y, v.z))
    c = Vector((crown.co.x, crown.co.y, PLATE_Z))
    crown.co = c
    txy = {i: T[i].co.copy() for i in T}
    corner = {b: Vector((*(c.to_2d().lerp(txy[b].to_2d(), PLATE_T[b])), PLATE_Z)) for b in RIDGES}
    # the plate edge: front line (mirror corner 3 -> corner 3), the two side chords, the back line
    edges = [(0, RIDGES[0], mir(corner[RIDGES[0]]), corner[RIDGES[0]])]
    edges += [(a, b, corner[a], corner[b]) for a, b in zip(RIDGES, RIDGES[1:])]
    edges += [(RIDGES[-1], 15, corner[RIDGES[-1]], mir(corner[RIDGES[-1]]))]
    # the shoulder ring: out along its spoke, its target height on the old profile (lerp mid -> rim), a touch fuller
    old_m = dict(enumerate(RING['mid'])); old_r = dict(enumerate(RING['rim']))
    mxy, mz = {}, {}
    for i in range(16):
        s = MID_S.get(i, 0.85)
        mxy[i] = C0.to_2d() + (Vector(S[i]) - C0.to_2d()) * s
        f = (s - 0.78) / 0.22
        mz[i] = old_m[i][2] * (1 - f) + (RIM_Z[i] + DZ) * f + 0.012
    # ridge lines corner -> shoulder point on the ridge spoke. The middle ridge keeps its profile height; the
    # outer ridges take the height of the side planes through it, so each pair of sector planes meets exactly
    # along a ridge spoke (front and back sectors are symmetric trapezoids: always planar)
    r0, r1, r2 = RIDGES
    rp = {b: Vector((*mxy[b], mz[b])) for b in RIDGES}
    fs = _plane(corner[r0], corner[r1], rp[r1])
    rp[r0].z = _hz(fs, rp[r0].x, rp[r0].y)
    bs = _plane(corner[r1], corner[r2], rp[r1])
    rp[r2].z = _hz(bs, rp[r2].x, rp[r2].y)
    planes = [((0, r0), _plane(mir(corner[r0]), corner[r0], rp[r0])), ((r0, r1), fs), ((r1, r2), bs),
              ((r2, 15), _plane(corner[r2], mir(corner[r2]), rp[r2]))]
    say('RIDGE z', {b: round(rp[b].z, 3) for b in RIDGES}, 'profile', {b: round(mz[b], 3) for b in RIDGES})
    for s_, ((lo, hi), pl) in enumerate(planes):
        a, b = edges[s_][2], edges[s_][3]
        for i in range(lo, hi + 1):
            if i in RIDGES and i != lo:
                continue                                    # a ridge spoke belongs to the crease (next sector)
            if i in RIDGES:
                A[i].co = corner[i].copy()
            else:
                p = _ray_hit(c, txy[i], a, b)
                A[i].co = Vector((p.x, p.y, PLATE_Z))
            if abs(txy[i].x) < 1e-6:
                A[i].co.x = 0.0
            for v, xy in ((Bv[i], A[i].co.to_2d().lerp(txy[i].to_2d(), 0.45)), (T[i], txy[i].to_2d()), (M[i], mxy[i])):
                v.co = Vector((xy.x, xy.y, _hz(pl, xy.x, xy.y)))
    # ridge spokes: on the crease line of the two sector planes, through the plate corner
    for b in RIDGES:
        d = rp[b] - corner[b]
        for v in (Bv[b], T[b], M[b]):
            t_ = (v.co.to_2d() - corner[b].to_2d()).dot(d.to_2d()) / d.to_2d().length_squared
            v.co = corner[b] + d * t_
    say('CROWN', {i: tuple(round(x, 3) for x in M[i].co) for i in range(16)})


def stage2(k, body):
    bm = edit(body)
    orbit_vs = rv(bm, 'mid', (1, 2)) + rv(bm, 'rim', (1, 2))      # (found before anything moves)
    # ---------------------------------------------------------------- carapace: plate, ring and panels (AD note 2)
    # the crown fan (one pole, 15 spokes a side) is locked topology; two logged rings round the pole turn it into
    # a flat central plate (inner ring) and a band (outer ring). The plate is one plane per side, tilted a little
    # off the seam (a soft mid ridge); the band + top + shoulder rings are cut into five big panels per side,
    # each hinged on the plate edge, with a soft crease along the outer ring.
    crown = at(bm, CROWN)
    T = dict(enumerate(rv(bm, 'top', range(16))))
    M = dict(enumerate(rv(bm, 'mid', range(16))))
    R = dict(enumerate(rv(bm, 'rim', range(16))))
    A = pole_ring(k, bm, crown, [T[i] for i in range(16)], 0.52, 'carapace plate: a ring round the crown pole, '
                  'the edge of a flat central plate (the fan inside it shades as one plane)')
    Bv = pole_ring(k, bm, None, [T[i] for i in range(16)], 0.45, 'carapace band: a second ring between the plate '
                   'edge and the top ring, the soft crease of the side panels', inner=A)
    crown_planes(crown, A, Bv, T, M)
    # the toothed front edge (AD note 3): four teeth a side, 4-6 % of the shell width, notches between
    for i, d in ((3, 0.022), (5, 0.026), (7, 0.026), (9, 0.004)):     # AD r3: tooth 9 small (l2 merus passes under it)
        R[i].co += outward(S, i) * d
    for i, d in ((4, 0.010), (6, 0.010), (8, 0.008)):
        R[i].co -= outward(S, i) * d

    # ---------------------------------------------------------------- legs (AD note 1): a paddle merus, a pinched
    # knee, a swollen propodus, a pinched ankle
    rings_ = {leg: [near_ring(bm, J[leg][j]) for j in ('mid', 'knee', 'ankle')] for leg in LEGS}
    for leg in LEGS:
        L = J[leg]
        md, kn, an = rings_[leg]
        e = next(e for v in md for e in v.link_edges if e.other_vert(v) in kn)
        with k.topo(bm, 'loop', f'{leg}: a ring in the merus between the rim and the knee: the paddle'):
            new = loopcut(bm, e, t=0.5, near=next(v for v in e.verts if v in md))
        OPPART[len(k.log.ops)] = ('leg', leg, 'loop')
        d = (Vector(L['knee']) - Vector(L['mid'])).normalized()
        shape_ring(new, d, 1.65, 1.15, lift=0.012)
        merus_new = new
        e = next(e for v in kn for e in v.link_edges if e.other_vert(v) in an)
        with k.topo(bm, 'loop', f'{leg}: a ring in the lower leg (carpus/propodus): the segment swells between two joints'):
            new = loopcut(bm, e, t=0.45, near=next(v for v in e.verts if v in kn))
        OPPART[len(k.log.ops)] = ('leg', leg, 'loop')
        scale(new, dict(l1=1.45, l2=1.42, l3=1.32, l4=1.22)[leg])   # chunkier propodus, graded front -> back
        scale(kn, 0.88)
        scale(an, 0.85)
        # AD r2 note 2: lower knee, ankle out and up, tip out: a shorter lower leg and a dactyl bent out-and-down
        tip = at(bm, L['tip'])
        dK, dA, dT = leg_delta(leg, 'knee'), leg_delta(leg, 'ankle'), leg_delta(leg, 'tip')
        move(merus_new, dK * 0.5)
        move(kn, dK)
        move(new, dK * 0.55 + dA * 0.45)
        move(an, dA)
        tip.co += dT
    # ---------------------------------------------------------------- claw: a glove, not a lemon
    C = J['claw']
    cl = [[at(bm, p) for p in row] for row in BUILT['claw']]     # coxa, elbow, wrist, palm0, palm1, palm2
    scale(cl[3], 0.62)                                            # the palm heel tapers hard into the wrist
    scale(cl[2], 0.90)
    for r, (pinch, bulge) in ((3, (0.72, 1.05)), (4, (0.66, 1.14)), (5, (0.74, 1.04))):
        # hexa order: top-in, top-out, mid-out, bottom-out, bottom-in, mid-in. The flat top and bottom pinch
        # toward their middles and the side corners push out: a swollen, rounded mitt instead of a prism
        row = cl[r]
        c0 = centre(row)
        for a, b in ((0, 1), (3, 4)):
            m = (row[a].co + row[b].co) / 2
            for v in (row[a], row[b]):
                v.co = m + (v.co - m) * pinch
        for v in (row[2], row[5]):
            v.co = c0 + (v.co - c0) * bulge
    # the palm's outer face (hexa verts top-out, mid-out, bottom-out) cut into two planes (AD note 5)
    plane_fit([r[i] for r in cl[3:6] for i in (1, 2)], [])
    plane_fit([r[3] for r in cl[3:6]], [r[2] for r in cl[3:6]])
    # movable finger (dactyl): arches up off the palm and hooks down at the tip, clearly curved
    dac = [[at(bm, p) for p in row] for row in BUILT['dac']]
    dtip, ptip = at(bm, C['dac_tip']), at(bm, C['pol_tip'])
    move(dac[0], (0.0, 0.0, 0.012))
    move(dac[1], (-0.012, -0.010, 0.040))
    scale(dac[1], 0.90)
    dtip.co += Vector((-0.040, -0.022, -0.035))
    move(dac[0], (centre(cl[5]) - centre(dac[0])) * 0.20)          # the hinge seated 20 % deeper in the palm
    # fixed finger (pollex): tapers straight forward, tip turning up to meet the dactyl's hook
    pol = [[at(bm, p) for p in row] for row in BUILT['pol']]
    scale(pol[0], 0.88)
    scale(pol[1], 0.66)
    move(pol[1], (-0.010, -0.008, -0.012))
    ptip.co += Vector((-0.032, -0.018, 0.010))
    # the gape: the dactyl swings up 9 deg and the pollex down 6 deg about their roots (~15 deg of daylight)
    f_ = (dtip.co - centre(dac[0])).normalized()
    rotate(dac[1] + [dtip], f_.cross(Vector((0, 0, 1))), 9, pivot=centre(dac[0]))
    g_ = (ptip.co - centre(pol[0])).normalized()
    rotate(pol[1] + [ptip], g_.cross(Vector((0, 0, 1))), -6, pivot=centre(pol[0]))
    k.dac_tip, k.pol_tip = dtip.co.copy(), ptip.co.copy()
    # ---------------------------------------------------------------- eye orbits: a socket in the front slope
    f = face_of(bm, orbit_vs)
    with k.topo(bm, 'inset', 'eye orbit: a loop inside the frontal shoulder face, where the eye stalk sits'):
        sock = inset(bm, [f], 0.28, 0.0)[0]
    OPPART[len(k.log.ops)] = ('socket', 'socket', 0)
    n = sock.normal.copy()
    # the orbit floor: a compact quad in the middle of the (tall, narrow) face, so the socket walls are broad
    # bevels (no needle triangles at the stalk root), sunk into the shell
    c_ = sock.calc_center_median()
    oc = centre(orbit_vs)
    for v in sock.verts:
        w = min(orbit_vs, key=lambda o: (o.co.lerp(oc, 0.28) - v.co).length)
        a_ = w.co - oc
        v.co = c_ + Vector((a_.x * 0.55, a_.y * 0.30, a_.z * 0.30)) - n * 0.018
    k.eye = (sock.calc_center_median(), n)
    snap_seam(bm, 1e-4)
    commit(body, bm)
    if os.environ.get('CRAB_DBG'):
        debug_hits(body)
    if os.environ.get('CRAB_CLOSE'):
        close_ups(k, 's2')


PALETTE = {'shell': '#c8502e', 'ridge': '#8e3420', 'belly': '#efc9a0', 'tip': '#2a1c18', 'eye': '#111111',
           'shine': '#d8d0c0',
           'barnacle': '#966856'}      # AD r3 note 2: the r2 #9a8474 tinted 35 % toward the shadow red 'ridge'


def piece(name, bm, key, mirror=True):
    ob = object_from_bm(name, bm, mirror=mirror)
    paint(ob, {key: PALETTE[key]}, lambda c, n, i: key)
    return ob


def part_of(v, bid, bop):
    return PART[v[bid] - 1] if v[bid] > 0 else OPPART.get(v[bop])


def leg_up(leg, c):
    """The local 'up' of the leg segment nearest c (for the dark-top / pale-underside split)."""
    L = LEG2[leg]
    pts = [Vector(p) for p in (L['coxa'], L['mid'], L['knee'], L['ankle'], L['tip'])]

    def dist(s_):
        a, b = s_
        t = max(0.0, min(1.0, (c - a).dot(b - a) / (b - a).length_squared))
        return (a + (b - a) * t - c).length
    a, b = min(zip(pts, pts[1:]), key=dist)
    return frame_up(b - a)[0]


CARAPACE = {'crown', 'top', 'mid', 'rim'}


def face_key(f, bid, bop):
    parts = [part_of(v, bid, bop) for v in f.verts]
    kinds = {p[0] for p in parts if p}
    n, c = f.normal, f.calc_center_median()
    if 'socket' in kinds:
        return 'tip' if all(p and p[0] == 'socket' for p in parts) else 'ridge'
    if 'finger' in kinds:
        return 'tip' if any(p and p[0] == 'finger' and p[2] != 0 for p in parts) else 'shell'
    if 'claw' in kinds:
        return 'belly' if n.z < -0.45 else 'shell'
    if 'leg' in kinds:
        leg = next(p[1] for p in parts if p and p[0] == 'leg')
        if any(p and p[0] == 'leg' and p[2] == 'tip' for p in parts):
            return 'tip'
        return 'ridge' if n.dot(leg_up(leg, c)) > 0 else 'belly'
    names = {p[1] for p in parts if p}
    if names <= CARAPACE:
        # the teeth: shoulder-band faces meeting a tooth vertex of the rim take the darker ridge colour
        if 'rim' in names and any(p[1] == 'rim' and p[2] in TEETH and p[2] != 1 for p in parts):
            return 'ridge'
        return 'shell'
    return 'belly'


def tube(bm, rows_c, rads, sides):
    """A tapered low-poly stalk through centres rows_c with radii rads; closed at both ends."""
    rows = []
    cs = [Vector(c) for c in rows_c]
    for i, (c, r) in enumerate(zip(cs, rads)):
        d = (cs[min(i + 1, len(cs) - 1)] - cs[max(i - 1, 0)]).normalized()
        u = Vector((1, 0, 0)); u = (u - d * u.dot(d)).normalized(); w = d.cross(u)
        rows.append(ring(bm, [c + (u * math.cos(2 * math.pi * j / sides + 0.4) + w * math.sin(2 * math.pi * j / sides + 0.4)) * r
                              for j in range(sides)]))
    for a, b in zip(rows, rows[1:]):
        bridge(bm, a, b, closed=True)
    cap(bm, list(reversed(rows[0]))); cap(bm, rows[-1])
    return rows


def gem(bm, c, r, h):
    """An eye bead: a 6-sided bipyramid (h = half height)."""
    c = Vector(c)
    mid = ring(bm, [c + Vector((math.cos(a) * r, math.sin(a) * r, 0)) for a in [i * math.pi / 3 + 0.3 for i in range(6)]])
    top, bot = bm.verts.new(c + Vector((0, 0, h))), bm.verts.new(c - Vector((0, 0, h)))
    for i in range(6):
        bm.faces.new([mid[i], mid[(i + 1) % 6], top])
        bm.faces.new([mid[(i + 1) % 6], mid[i], bot])


def bulb(bm, c, axis, r, h, sides=6):
    """A rounded low-poly eye bulb along axis: three rings (r x 0.72, r, r x 0.82) and two poles at +-h."""
    c, axis = Vector(c), Vector(axis).normalized()
    u = (Vector((1, 0, 0)) - axis * axis.x).normalized(); w = axis.cross(u)
    rows = []
    for off, rr in ((-0.55 * h, 0.72 * r), (0.0, r), (0.50 * h, 0.82 * r)):
        rows.append(ring(bm, [c + axis * off + (u * math.cos(2 * math.pi * j / sides + 0.3) +
                                                w * math.sin(2 * math.pi * j / sides + 0.3)) * rr for j in range(sides)]))
    for a_, b_ in zip(rows, rows[1:]):
        bridge(bm, a_, b_, closed=True)
    lo, hi = bm.verts.new(c - axis * h), bm.verts.new(c + axis * h)
    for j in range(sides):
        bm.faces.new([rows[0][(j + 1) % sides], rows[0][j], lo])
        bm.faces.new([rows[-1][j], rows[-1][(j + 1) % sides], hi])
    recalc_normals(bm)


def barnacle(bm, c, n, r, seed=0):
    """AD r2 note 3: a low barnacle cone (7 sides, slightly irregular), its base sunk 40 % of r under the surface
    point c, a low shoulder, a lip and a dark pit sunk into the top. Returns the pit faces."""
    c, n = Vector(c), Vector(n).normalized()
    u = (Vector((1, 0, 0)) - n * n.x).normalized(); w = n.cross(u)
    ang = [i * 2 * math.pi / 7 + 0.37 * seed for i in range(7)]
    jit = [1.0 + 0.09 * math.sin(3.1 * i + seed) for i in range(7)]
    rg = lambda h, rr: ring(bm, [c + n * (h * r) + (u * math.cos(a) + w * math.sin(a)) * rr * r * j for a, j in zip(ang, jit)])
    # AD r3 note 2: a lower truncated cone, its base sunk a further 25 % (0.40 -> 0.65 r under the surface)
    base, sh, lip, pit = rg(-0.65, 1.0), rg(0.16, 0.80), rg(0.36, 0.52), rg(0.16, 0.30)
    bridge(bm, base, sh, closed=True); bridge(bm, sh, lip, closed=True)
    cap(bm, list(reversed(base)))
    before = set(bm.faces)
    bridge(bm, lip, pit, closed=True); cap(bm, pit)
    return set(bm.faces) - before


def stage3(k, body):
    bm = edit(body)                                 # read only: never committed
    bid, bop = bm.verts.layers.int.get('bid'), bm.verts.layers.int.get('bop')
    keys = {f.index: face_key(f, bid, bop) for f in bm.faces}
    bm.free()
    paint(body, {kk: PALETTE[kk] for kk in ('shell', 'ridge', 'belly', 'tip')}, lambda c, n, i: keys[i])

    pieces = []
    # eye stalks (AD note 6): out of the orbit sockets, a flared root 1.5x thicker than before, leaning 18 deg out
    # and a little forward; a rounded black bulb 1.3x the stalk top, with a small shine
    sc, sn = k.eye
    base = sc - sn * 0.012
    ax = Vector((0.31, -0.14, 0.94)).normalized()
    top = base + ax * 0.105
    bmS = bmesh.new(); tube(bmS, [base, base + ax * 0.05, top], [0.034, 0.023, 0.019], 5)
    pieces.append(piece('stalk', bmS, 'shell'))
    k.eye_top = top
    er, eh = 0.025, 0.030
    ec = top + ax * (eh * 0.55)
    bmE = bmesh.new(); bulb(bmE, ec, ax, er, eh)
    pieces.append(piece('eye', bmE, 'eye'))
    sd = (ax * 0.5 + Vector((0.25, -0.85, 0.0))).normalized()
    bmH = bmesh.new(); gem(bmH, ec + sd * er * 0.92, 0.008, 0.007)
    pieces.append(piece('shine', bmH, 'shine'))
    # barnacles (AD r2 note 3): four low cones clustered on the rear edge of the left back sector (mixed sizes
    # 1-1.8x), one small stray on the right rear edge; a muted tint (not pale), dark pits; none on the top centre
    ev = evaluated_bm(body)
    tree = BVHTree.FromBMesh(ev)
    bmB = bmesh.new()
    pits = set()
    # AD r3 note 2: four cones on the left rear rim only (1-1.8x), no stray
    for sd, (x, y, r) in enumerate(((0.125, 0.262, 0.040), (0.185, 0.232, 0.029), (0.075, 0.284, 0.025),
                                    (0.165, 0.266, 0.022))):
        hit = tree.ray_cast(Vector((x, y, 1.0)), Vector((0, 0, -1)))
        n = (hit[1].normalized() + Vector((0, 0, 0.6))).normalized()     # sit up a little on the steep back wall
        pits |= barnacle(bmB, hit[0], n, r, seed=sd)
    ev.free()
    bmB.faces.index_update()
    pit_idx = {f.index for f in pits}
    ob = object_from_bm('barnacles', bmB, mirror=False)
    paint(ob, {kk: PALETTE[kk] for kk in ('barnacle', 'tip')}, lambda c, n, i: 'tip' if i in pit_idx else 'barnacle')
    pieces.append(ob)
    if os.environ.get('CRAB_CLOSE'):
        close_ups(k, 's3')
    return pieces


def sym(d):
    """Mirror a pose dict: .L keys also drive .R (same bone-local X, Y/Z flipped) unless .R is given."""
    out = dict(d)
    for b_, (x, y, z) in d.items():
        if b_.endswith('.L') and b_[:-2] + '.R' not in d:
            out[b_[:-2] + '.R'] = (x, -y, -z)
    return out


def set_rolls(rig):
    """Every bone's local Z toward world up (perpendicular to the bone; forward for near-vertical bones), so
    +X always swings a bone's tip up, on both sides."""
    with bpy.context.temp_override(object=rig, active_object=rig, selected_objects=[rig]):
        bpy.ops.object.mode_set(mode='EDIT')
        for eb in rig.data.edit_bones:
            d = (eb.tail - eb.head).normalized()
            up = Vector((0, 0, 1)) if abs(d.z) < 0.985 else Vector((0, -1, 0))   # steep carpus bones (~0.96) keep the leg plane
            eb.align_roll(up - d * d.dot(up))
        bpy.ops.object.mode_set(mode='OBJECT')


def leg_ik(leg, side, off, lift=0.0, reach=0.0, tf=None):
    """Bone-local X angles (deg) for merus and carpus so the leg tip lands on its rest spot (+ lift up, + reach out)
    while the body is offset by `off` (world). Planar two-bone IK in the leg's vertical plane (set_rolls makes
    +X swing a bone's tip up on both sides); the knee stays on the upper branch."""
    L = LEG2[leg]; sx = 1 if side == 'L' else -1
    mv = lambda p_: Vector((p_[0] * sx, p_[1], p_[2]))
    co, kn, tp = mv(L['coxa']), mv(L['knee']), mv(L['tip'])
    h = Vector((kn.x - co.x, kn.y - co.y, 0.0)).normalized()     # the knee plane (AD r3: the tip is swept off it)
    rz = lambda p_: ((p_ - co).dot(h), (p_ - co).z)
    rk, zk = rz(kn); rt, zt = rz(tp)
    L1, L2 = math.hypot(rk, zk), math.hypot(rt - rk, zt - zk)
    tf = tf or (lambda p_: p_ - Vector(off))        # world target -> the body's rest frame
    r, z = rz(tf(tp + h * reach + Vector((0, 0, lift))))
    D = min(max(math.hypot(r, z), abs(L1 - L2) + 1e-4), L1 + L2 - 1e-4)
    a1 = math.atan2(z, r) + math.acos((L1 * L1 + D * D - L2 * L2) / (2 * L1 * D))
    kx, kz = L1 * math.cos(a1), L1 * math.sin(a1)
    a2 = math.atan2(z - kz, r - kx)
    a0 = math.atan2(zk, rk)
    d1 = a1 - a0
    d2 = (a2 - math.atan2(zt - zk, rt - rk)) - d1
    # the part of the target off the leg plane: a yaw of the whole leg about world vertical through the coxa.
    # World up in the merus rest frame is (0, sin a0, cos a0), so the yaw is Euler (0, phi sin a0, phi cos a0)
    tgt = tf(tp + h * reach)
    pp = Vector((0, 0, 1)).cross(h)
    phi = (tgt - tp).dot(pp) / max(r, 1e-3)
    return (math.degrees(d1), math.degrees(phi * math.sin(a0)), math.degrees(phi * math.cos(a0))), math.degrees(d2)


def stage4(k, body, pieces):
    C = J['claw']
    dac_tip, pol_tip = k.dac_tip, k.pol_tip                                # as moved in stage 2
    hinge = (Vector(C['palm2']) + Vector(C['dac0'])) / 2 + Vector((0, 0, 0.02))
    bones = [('body', J['body'], J['body_end'], None)]
    for leg in LEGS:
        L = LEG2[leg]
        bones += [(f'{leg}_merus.L', L['coxa'], L['knee'], 'body'),
                  (f'{leg}_carpus.L', L['knee'], L['ankle'], f'{leg}_merus.L', True),
                  (f'{leg}_dactyl.L', L['ankle'], L['tip'], f'{leg}_carpus.L', True)]
    bones += [('arm.L', C['coxa'], C['elbow'], 'body'),
              ('fore.L', C['elbow'], C['wrist'], 'arm.L', True),
              ('claw.L', C['wrist'], tuple(pol_tip), 'fore.L', True),
              ('finger.L', tuple(hinge), tuple(dac_tip), 'claw.L'),
              ('eye.L', tuple(k.eye[0]), tuple(k.eye_top), 'body')]
    rig = armature(bones)
    set_rolls(rig)
    skin(body, rig)
    for p in pieces:
        nm = p.name.replace('piece_', '')
        if nm in ('stalk', 'eye', 'shine'):
            bind(p, rig, bone=None)                # nearest of eye.L / eye.R per vertex (mirrored pieces)
        else:
            bind(p, rig, bone='body')

    DROP = 0.0                      # AD r3: the body is lowered at the source (stage 1, DZ); no clip crouch

    def planted(d, off):
        """All eight tips held on their rest spots (IK) while the body is offset by `off` (world) and pitched by
        its keyed bone-local X (world -X: + lifts the front) about its head."""
        hd = Vector(J['body'])
        R = Matrix.Rotation(math.radians(-d.get('body', (0, 0, 0))[0]), 3, 'X')
        tf = lambda p_: hd + R.inverted() @ (p_ - hd - Vector(off))
        for leg in LEGS:
            for s_ in 'LR':
                m_, c_ = leg_ik(leg, s_, off, tf=tf)
                d[f'{leg}_merus.{s_}'] = m_; d[f'{leg}_carpus.{s_}'] = (c_, 0, 0)
        return d

    # idle (48): claws open and close slowly, the body bobs in its low crouch, the eye stalks twitch
    IDLE = {1: (0, 0, 0.0), 12: (22, 8, 0.012), 20: (24, 8, 0.004), 22: (24, -6, 0.0), 24: (20, -6, -0.004),
            32: (4, -6, 0.006), 36: (2, -3, 0.010), 40: (0, 0, 0.006), 48: (0, 0, 0.0)}
    keys, locs = {}, {}
    for f, (op, eye, bob) in IDLE.items():
        keys[f] = planted(sym({'finger.L': (op, 0, 0), 'claw.L': (op * 0.25, 0, 0), 'body': (0, 0, 0),
                               'eye.L': (0, 0, eye)}), (0, 0, bob + DROP))
        locs[f] = {'body': (0, 0, bob + DROP)}
    clip(rig, 'idle', keys, loc=locs)
    # move (24, AD note 4): an alternating tetrapod gait. L1 R2 L3 R4 swing in the first half, L2 R1 L4 R3 in the
    # second; a swinging tip lifts 0.11 m (~14 % of the leg) and reaches out a little, while the body sways 3 cm
    # sideways and bobs. Planted tips are held fixed in world space by a two-bone planar IK (merus + carpus, the
    # dactyl rigid) solved per key from the J skeleton.
    SWING = dict(l1=20.0, l2=19.0, l3=19.0, l4=21.0)             # deg at the coxa: the tip rises ~0.10 m (15 %)
    A = [('l1', 'L'), ('l3', 'L'), ('l2', 'R'), ('l4', 'R')]
    B = [('l2', 'L'), ('l4', 'L'), ('l1', 'R'), ('l3', 'R')]
    keys, locs = {}, {}
    for f in range(1, 26):
        # AD r2 F3: two steps per 24 frames, phased so set A peaks at f6.5 and set B at f12.5 (and f18.5 / f24.5)
        sw = math.sin(4 * math.pi * (f - 1) / 24.0 - 1.309)
        dx, dz = 0.03 * sw, 0.010 * sw ** 2
        # AD r3 note 3: the body rolls 3 deg down toward the side it sways onto (the loaded side). Body bone-local
        # Y is world -Y, so bone ry = -b rolls the body by b about world +Y (+b lowers the +X side). The IK maps
        # every target through the rolled, shifted body so planted tips stay fixed in world space.
        roll = 3.0 * sw
        Rw = Matrix.Rotation(math.radians(roll), 3, 'Y')
        hd, off = Vector(J['body']), Vector((dx, 0.0, dz + DROP))
        tf = lambda p_, Rw=Rw, off=off: hd + Rw.inverted() @ (p_ - hd - off)
        d = {}
        for grp, lift in ((A, max(0.0, sw)), (B, max(0.0, -sw))):
            for leg, s_ in grp:
                # AD r3: a swinging leg lifts as a whole from the coxa (merus +X, the carpus keeps its planted
                # angle), so it keeps both bends in the air instead of opening the knee into a hanging blade.
                # At lift 0 this is exactly the planted IK pose, so touch-down is seamless.
                m_, c_ = leg_ik(leg, s_, off, tf=tf)
                d[f'{leg}_merus.{s_}'] = (m_[0] + SWING[leg] * lift, m_[1], m_[2]); d[f'{leg}_carpus.{s_}'] = (c_, 0, 0)
        d['arm.L'] = (5 * abs(sw), 0, 0); d['arm.R'] = (5 * abs(sw), 0, 0)
        d['body'] = (0, -roll, 0)
        keys[f] = d
        locs[f] = {'body': (-dx, 0.0, dz + DROP)}              # body bone-local X is world -X (the bone points -Y)
    clip(rig, 'move', keys, loc=locs)
    # attack (32): both claws rise and open, then snap forward and shut
    rest0 = sym({'arm.L': (0, 0, 0), 'fore.L': (0, 0, 0), 'claw.L': (0, 0, 0), 'finger.L': (0, 0, 0), 'body': (0, 0, 0)})
    up = sym({'arm.L': (30, 0, 0), 'fore.L': (12, 0, 0), 'claw.L': (4, 0, 0), 'finger.L': (32, 0, 0), 'body': (6, 0, 0)})
    snap = sym({'arm.L': (6, 0, 0), 'fore.L': (-6, 0, 0), 'claw.L': (-8, 0, 0), 'finger.L': (-3, 0, 0), 'body': (-3, 0, 0)})
    ATT = {1: (rest0, 0.0), 9: (up, 0.02), 14: (up, 0.02), 18: (snap, -0.01), 23: (snap, -0.005), 32: (rest0, 0.0)}
    clip(rig, 'attack', {f: planted(dict(p_), (0, 0, z + DROP)) for f, (p_, z) in ATT.items()},
         loc={f: {'body': (0, 0, z + DROP)} for f, (p_, z) in ATT.items()})
    if os.environ.get('CRAB_POSE'):
        acts = {a_.name: a_ for a_ in bpy.data.actions}
        tips = [f'{l_}_dactyl.{s_}' for l_ in LEGS for s_ in 'LR']
        seq = {}
        for fr in range(1, 26):
            pose(rig, acts['move'], fr); bpy.context.view_layer.update()
            seq[fr] = {b: rig.matrix_world @ rig.pose.bones[b].tail for b in tips}
        planted_mv = max((seq[f + 1][b] - seq[f][b]).length for f in range(1, 25) for b in tips
                         if seq[f][b].z < 0.002 and seq[f + 1][b].z < 0.002)
        say('GAIT planted max step (m)', round(planted_mv, 5), 'tip z f6', {b: round(seq[6][b].z, 3) for b in tips},
            'tip z f12', {b: round(seq[12][b].z, 3) for b in tips})
        for cn, fr in (('attack', 9), ('move', 1), ('move', 7), ('move', 19)):
            pose(rig, acts[cn], fr)
            say('BODY', cn, fr, tuple(round(x, 3) for x in rig.pose.bones['body'].head), tuple(round(x, 3) for x in rig.pose.bones['l2_merus.L'].head),
                tuple(round(x, 3) for x in rig.pose.bones['l2_merus.L'].tail), [round(x,3) for x in rig.pose.bones['l2_merus.L'].rotation_euler],
                [round(x,3) for x in rig.pose.bones['body'].location], tuple(round(x,3) for x in rig.data.bones['l2_merus.L'].matrix_local.col[0][:3]))
            say('POSE', cn, fr, {b: tuple(round(x, 3) for x in rig.pose.bones[b].tail)
                                 for b in ('l1_dactyl.L', 'l2_dactyl.L', 'l3_dactyl.L', 'l4_dactyl.L', 'l1_dactyl.R', 'l2_dactyl.R')})
        rig.animation_data.action = None
        rest(rig)
        bpy.context.view_layer.update()
        say('REST', {b: tuple(round(x, 3) for x in rig.pose.bones[b].tail)
                     for b in ('l1_dactyl.L', 'l2_dactyl.L', 'l3_dactyl.L', 'l4_dactyl.L', 'l1_dactyl.R', 'l2_dactyl.R')})
    return rig


run(META, stage1, stage2, stage3, stage4)
