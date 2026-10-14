import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from carve import carve_guide, hull_sections, fit_to_guide
import parts as P

REST = {}       # the toes and claws of the welded library paws (stage-3 pieces)

# wolf, cage method: the hull of reference/ is a hidden guide; the base is a quad cage box-modelled on J.
# Sections are half rings (top seam -> bottom seam) that TILT with the form: vertical through the skull,
# leaning back through the neck and shoulder (the ruff tiers and the shoulder blade), square to the tail.

# the skeleton (metres, faces -Y, left flank +X, feet on z = 0), read off the reference side and front views
J = dict(
    pelvis=(0.0, 0.33, 0.60), spine=(0.0, -0.05, 0.62), neck=(0.0, -0.37, 0.71),
    head=(0.0, -0.62, 0.87), snout=(0.0, -0.845, 0.79),
    tail0=(0.0, 0.46, 0.55), tail1=(0.0, 0.62, 0.38), tail2=(0.0, 0.83, 0.17),
    shoulderL=(0.094, -0.29, 0.56), elbowL=(0.094, -0.285, 0.345), wristL=(0.100, -0.31, 0.135),
    pawL=(0.105, -0.42, 0.03),
    hipL=(0.105, 0.30, 0.56), kneeL=(0.105, 0.285, 0.345), hockL=(0.105, 0.415, 0.235),
    toeL=(0.108, 0.36, 0.03),
)
PLAN = dict(spine=['pelvis', 'spine', 'neck', 'head', 'snout'],
            limbs=dict(fore=['shoulderL', 'elbowL', 'wristL', 'pawL'], hind=['hipL', 'kneeL', 'hockL', 'toeL']),
            extra=[['tail0', 'tail1', 'tail2']])
META = dict(creature='wolf', model='opus', cage=True, J=J, plan=PLAN, intended={},
            keep_valleys=lambda c: c.z > 0.95 and abs(c.x) > 0.06)       # the ear cup stays a dent


def sec(T, B, w, zw=None, up=None, lo=None, sweep=(0.0, 0.0, 0.0)):
    """A half section from the top seam point T = (y, z) to the bottom seam point B = (y, z): 5 vertices,
    so the whole section is 8-sided. The side vertices lie in the (tilted) plane through T and B.
    up / lo: the upper and lower corner as (x, z); zw: the height of the widest vertex."""
    (yt, zt), (yb, zb) = T, B
    h = zt - zb
    yy = lambda z: yt + (yb - yt) * (zt - z) / h
    zw = zw if zw is not None else zb + 0.5 * h
    up = up or (0.6 * w, zt - 0.08 * h)
    lo = lo or (0.55 * w, zb + 0.08 * h)
    # sweep: the up / widest / lo vertex pushed back (+y) out of the plane, so a ruff tier's edge is a chevron
    return [(0.0, yt, zt), (up[0], yy(up[1]) + sweep[0], up[1]), (w, yy(zw) + sweep[1], zw),
            (lo[0], yy(lo[1]) + sweep[2], lo[1]), (0.0, yb, zb)]


# nose -> tail tip
STATIONS = [
    # head: muzzle box, stop, brow, skull with the cheek plane
    ('H0', sec((-0.851, 0.806), (-0.851, 0.776), 0.027, up=(0.022, 0.804), lo=(0.022, 0.778))),          # nose tip
    ('H1', sec((-0.800, 0.828), (-0.795, 0.750), 0.040, zw=0.790, up=(0.031, 0.824), lo=(0.035, 0.756))),  # muzzle
    ('H2', sec((-0.735, 0.868), (-0.745, 0.733), 0.053, zw=0.800, up=(0.038, 0.862), lo=(0.047, 0.742))),  # before the stop
    ('H3', sec((-0.693, 0.928), (-0.700, 0.737), 0.088, zw=0.850, up=(0.060, 0.918), lo=(0.070, 0.758))),  # brow
    ('H4', sec((-0.600, 0.995), (-0.640, 0.747), 0.124, zw=0.890, up=(0.045, 0.995), lo=(0.105, 0.780))),  # skull, cheek
    ('H5', sec((-0.450, 0.985), (-0.625, 0.660), 0.165, zw=0.850, up=(0.045, 0.985), lo=(0.110, 0.720), sweep=(0.0, 0.03, 0.0))),  # back of skull
    # neck: ONE mane wedge (blockout review 4): it swells behind the jaw, ends in a single back edge that runs
    # from the withers down to the bib point at the elbow line, then one step in
    ('N1', sec((-0.320, 0.968), (-0.595, 0.570), 0.200, zw=0.800, up=(0.100, 0.950), lo=(0.100, 0.610))),
    ('N2', sec((-0.165, 0.800), (-0.490, 0.400), 0.207, zw=0.640, up=(0.115, 0.780), lo=(0.130, 0.460), sweep=(0.0, 0.02, 0.0))),  # mane edge
    ('N2s', sec((-0.150, 0.782), (-0.465, 0.412), 0.187, zw=0.620, up=(0.100, 0.762), lo=(0.115, 0.470))),                        # the step
    # chest: sections lean with the shoulder blade; the fore leg leaves the lower flank between C0..C2
    ('C0', sec((-0.105, 0.772), (-0.400, 0.385), 0.193, zw=0.510, up=(0.100, 0.750), lo=(0.050, 0.400), sweep=(0.0, 0.05, 0.0))),
    ('C1', sec((-0.040, 0.760), (-0.300, 0.378), 0.180, zw=0.500, up=(0.095, 0.738), lo=(0.050, 0.395))),
    ('C2', sec((0.030, 0.754), (-0.200, 0.396), 0.158, zw=0.500, up=(0.090, 0.735), lo=(0.050, 0.410))),
    ('B0', sec((0.100, 0.754), (-0.050, 0.440), 0.135, zw=0.600, up=(0.080, 0.735), lo=(0.070, 0.460))),   # rib cage end
    ('B1', sec((0.238, 0.755), (0.074, 0.477), 0.128, zw=0.620, up=(0.075, 0.735), lo=(0.065, 0.495))),    # waist, tuck-up
    # hips (review 5: a second mass in the plan view): the hind leg leaves the lower flank between D0..D2
    ('D0', sec((0.310, 0.730), (0.170, 0.455), 0.185, zw=0.560, up=(0.085, 0.710), lo=(0.050, 0.450))),
    ('D1', sec((0.390, 0.700), (0.290, 0.445), 0.205, zw=0.560, up=(0.085, 0.680), lo=(0.050, 0.440))),
    ('D2', sec((0.455, 0.665), (0.405, 0.430), 0.172, zw=0.550, up=(0.075, 0.650), lo=(0.050, 0.435))),
    # tail: a deep, narrow brush carried low; sections square to it
    ('T0', sec((0.500, 0.635), (0.445, 0.380), 0.070, zw=0.520, up=(0.050, 0.615), lo=(0.040, 0.400))),
    ('T1', sec((0.596, 0.556), (0.494, 0.298), 0.080, up=(0.055, 0.535), lo=(0.050, 0.320))),
    ('T2', sec((0.705, 0.446), (0.625, 0.213), 0.072)),
    ('T3', sec((0.805, 0.343), (0.740, 0.153), 0.050)),
    ('T4', sec((0.851, 0.223), (0.823, 0.108), 0.020)),
]


def lring(cx, rx, yf, yb, zf, zb=None):
    """A 6-sided limb ring: flat front and back faces, a chamfer vertex on each side."""
    zb = zf if zb is None else zb
    ym, zm = (yf + yb) / 2, (zf + zb) / 2
    return dict(OF=(cx + 0.8 * rx, yf, zf), OM=(cx + rx, ym, zm), OB=(cx + 0.8 * rx, yb, zb),
                IB=(cx - 0.8 * rx, yb, zb), IM=(cx - rx, ym, zm), IF=(cx - 0.8 * rx, yf, zf))


def leg(bm, faces, cur, rings):
    """Extrude a 2-quad region down ring by ring (a 6-sided limb); cur maps role -> boundary vert."""
    out = []
    for rg in rings:
        r = extrude(bm, faces)
        nv = r['verts']
        m = {role: min(nv, key=lambda q: (q.co - v.co).length) for role, v in cur.items()}
        for role, p in lring(*rg).items():
            m[role].co = Vector(p)
        faces, cur = r['faces'], m
        out.append(list(m.values()))
    return faces, out


def stage1(k):
    guide = carve_guide(k)
    if os.environ.get('WOLF_SECTIONS'):
        hull_sections(guide, (0, -0.85, 0.6), (0, 0.85, 0.6), 18, 'spine')
        hull_sections(guide, J['elbowL'], J['wristL'], 4, 'forearm')
        hull_sections(guide, J['hockL'], J['toeL'], 4, 'metatarsus')
    bm = bmesh.new()
    idx, rings = {}, []
    for i, (nm, pts) in enumerate(STATIONS):
        idx[nm] = i
        rings.append(ring(bm, pts))
    FIT = [n for n in os.environ.get('WOLF_FIT', 'B0,B1').split(',') if n]
    if FIT:
        fit = fit_to_guide([rings[idx[n]] for n in FIT], guide, max_move=0.02)
        say('fit_to_guide (moved, capped):', fit)
    bands = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, list(reversed(rings[0])))
    cap(bm, rings[-1])
    R = lambda nm, j: rings[idx[nm]][j]

    # fore leg (review 3): a broad upper arm with the elbow point back, three elbow loops, a thin wrist, and the
    # paw set a little wider than the elbow (a slight A-frame)
    fore = [(0.103, 0.052, -0.392, -0.170, 0.362, 0.380),
            (0.100, 0.050, -0.388, -0.195, 0.322, 0.334),
            (0.098, 0.045, -0.380, -0.228, 0.280),
            (0.099, 0.036, -0.362, -0.258, 0.170),
            (0.102, 0.034, -0.362, -0.262, 0.130),
            (0.104, 0.039, -0.400, -0.275, 0.095, 0.090)]
    ff, fr_ = leg(bm, [bands[idx['C0']][2], bands[idx['C1']][2]],
        dict(OF=R('C0', 2), OM=R('C1', 2), OB=R('C2', 2), IB=R('C2', 3), IM=R('C1', 3), IF=R('C0', 3)), fore)

    # hind leg (review 1, 2): a wide thigh mass tapering to a forward knee (three loops), the shank raking back
    # to a hock point set back (two loops), a metatarsus slanting forward to the paw: a Z
    hind = [(0.102, 0.064, 0.135, 0.405, 0.415, 0.416),
            (0.102, 0.060, 0.180, 0.393, 0.372, 0.380),
            (0.102, 0.054, 0.220, 0.388, 0.328, 0.348),
            (0.103, 0.048, 0.255, 0.398, 0.285, 0.310),
            (0.104, 0.041, 0.325, 0.442, 0.235, 0.272),
            (0.105, 0.037, 0.350, 0.480, 0.190, 0.238),
            (0.107, 0.035, 0.345, 0.462, 0.140, 0.150),
            (0.108, 0.039, 0.322, 0.452, 0.095, 0.090)]
    hf, hr_ = leg(bm, [bands[idx['D0']][2], bands[idx['D1']][2]],
        dict(OF=R('D0', 2), OM=R('D1', 2), OB=R('D2', 2), IB=R('D2', 3), IM=R('D1', 3), IF=R('D0', 3)), hind)

    # paws: the library canine paw, its mound welded into the cage at the wrist / hock-end ring; the toes and
    # claws stay behind as '_rest_' objects and come back as stage-3 pieces
    REST.clear()
    for nm, faces, rr, ox, oy in (('paw_fore', ff, fr_[-1], 0.104, -0.3375), ('paw_hind', hf, hr_[-1], 0.108, 0.387)):
        bmesh.ops.delete(bm, geom=list(faces), context='FACES')
        pw = P.paw_canine((ox, oy, 0.066), width=0.126, height=0.066, toe_segs=1, claws=True, root=(0.078, 0.125),
                          open_root=True, name=nm, mats={'skin': 'sock', 'pad': 'black', 'claw': 'black'})
        REST[nm] = bridge_part(pw, rr, bm=bm)

    # ears: in the base (the wolf's defining outline cue; without them the front IoU is 0.82 against the 0.85 floor).
    # One extrusion of the skull-corner face to a small tip quad: a pointed pyramid whose FRONT face is the opening
    er = extrude(bm, [bands[idx['H4']][1]])
    tip = {'IF': (0.098, -0.556, 1.100), 'OF': (0.116, -0.554, 1.094), 'OB': (0.120, -0.522, 1.090), 'IB': (0.100, -0.516, 1.096)}
    src = {'IF': R('H4', 1), 'OF': R('H4', 2), 'OB': R('H5', 2), 'IB': R('H5', 1)}
    for role, v0 in src.items():
        min(er['verts'], key=lambda q: (q.co - v0.co).length).co = Vector(tip[role])

    # eye: a loop inside the brow-cheek plane between H3 and H4 (the socket), pushed in a little
    inset(bm, [bands[idx['H3']][1]], 0.38, -0.005)

    snap_seam(bm)
    return object_from_bm('body', bm)


S = dict(STATIONS)
FORE_Z = 0.328      # the sock border ring on the fore leg (elbow, second loop)
EAR_TIP = {'IF': (0.098, -0.556, 1.100), 'OF': (0.116, -0.554, 1.094)}


def _mean(pts):
    return tuple(sum(p[i] for p in pts) / len(pts) for i in range(3))


EAR_FRONT = _mean([S['H4'][1], S['H4'][2], EAR_TIP['OF'], EAR_TIP['IF']])


def stage2(k, body):
    """Secondary forms: the mane broken into a ridge and a cheek ruff (two logged loops), a cupped ear (inset),
    brow / stop / cheek planes, hip and shoulder corners, jagged colour borders on the sock rings and the tail."""
    bm = edit(body)
    sv = lambda nm, j: vert_near(bm, S[nm][j])
    h2t, h3u, h3w, h4w, h5w, h5l = sv('H2', 0), sv('H3', 1), sv('H3', 2), sv('H4', 2), sv('H5', 2), sv('H5', 3)
    n2 = [sv('N2', j) for j in range(5)]; n2s = [sv('N2s', j) for j in range(5)]
    d1u, d0w, c0w = sv('D1', 1), sv('D0', 2), sv('C0', 2)
    t1 = [sv('T1', j) for j in range(5)]; t2 = [sv('T2', j) for j in range(5)]; t3 = [sv('T3', j) for j in range(5)]
    fsock = verts_where(bm, lambda c: c.y < -0.15 and c.x > 0.03 and 0.318 < c.z < 0.338 and c.x < 0.16)
    hsock = verts_where(bm, lambda c: 0.24 < c.y < 0.41 and c.x > 0.04 and 0.28 < c.z < 0.315 and c.x < 0.16)
    with k.topo(bm, 'loop', 'mane ridge between the jaw tier and the mane edge: breaks the barrel, carries the bib border'):
        mr = loopcut(bm, edge_near(bm, _mean([S['N1'][0], S['N2'][0]])), t=0.5)
    with k.topo(bm, 'loop', 'cheek ruff ring behind the skull: the step from the head into the mane'):
        ck = loopcut(bm, edge_near(bm, _mean([S['H5'][0], S['N1'][0]])), t=0.4)
    with k.topo(bm, 'inset', 'inner ear: a loop inside the front face of the ear, sunk (the cup)'):
        ef = inset(bm, [face_near(bm, EAR_FRONT)], 0.42, -0.012)
    say('sock rings', len(fsock), len(hsock), 'mane ring', len(mr), 'cheek ring', len(ck))
    # mane ridge: the side of the ring stands proud and its vertices alternate along the neck, so the ridge is a
    # row of fur points, not a hoop
    for i, v in enumerate(sorted(mr, key=lambda q: -q.co.z)):
        if v.co.x > 1e-4:
            v.co.x += 0.016
            v.co.y += 0.022 if i % 2 else -0.012
            v.co.z += -0.012 if i % 2 else 0.010
    # cheek ruff: flares out and forward under the ear, the skull's own cheek tucks in in front of it
    for v in ck:
        c = v.co
        if c.x > 0.08 and c.z < 0.92:
            c.x += 0.024; c.y -= 0.018
        elif c.x > 1e-4:
            c.x += 0.008
    h5w.co.x -= 0.012; h5l.co.x -= 0.010
    # mane edge: a chevron on the shoulder
    for rg in (n2, n2s):                                  # (edge and step move together: the step band keeps its width)
        rg[1].co.y += 0.022; rg[2].co.y -= 0.012; rg[3].co.y += 0.018; rg[3].co.z -= 0.010
    # face: the brow overhangs the eye, a deeper stop, a cheekbone corner
    h3u.co += Vector((0.010, -0.012, 0.006))
    h2t.co.z -= 0.010
    h3w.co += Vector((0.004, 0.0, -0.006))
    h4w.co += Vector((0.006, 0.0, -0.010))
    # hip bone and the point of the shoulder: one clear corner each
    d1u.co += Vector((0.010, 0.0, 0.006)); d0w.co += Vector((0.006, -0.010, 0.006)); c0w.co += Vector((0.006, 0.0, 0.0))
    # tail: the tier rings zigzag along the brush (fur tips; T2 is the dark tip's border)
    ax = Vector((0.0, 0.74, -0.67))
    for rg, a in ((t1, 0.018), (t2, 0.028), (t3, 0.018)):
        for i, v in enumerate(rg):
            v.co += ax * (a if i % 2 else -a * 0.6)
    # sock borders: the ring's vertices alternate up and down
    for rg in (fsock, hsock):
        for i, v in enumerate(sorted(rg, key=lambda q: math.atan2(q.co.y - sum(w.co.y for w in rg) / len(rg), q.co.x - sum(w.co.x for w in rg) / len(rg)))):
            v.co.z += 0.012 if i % 2 else -0.012
    snap_seam(bm)
    commit(body, bm)
    bm.free()


# palette (concept_2): three value groups and one accent. dark = saddle / tail tip / ear backs; mid = grey fur;
# light = cream bib, muzzle, belly and the tan legs; accent = the amber eyes
PAL = dict(fur='#8f8c8b', saddle='#56565e', light='#b8b1a8', cream='#f1e8d6', sock='#dcb990', black='#1d1c1f', iris='#eda01f')
MIR = lambda v: (-v[0], v[1], v[2])


def behind(nm, c):
    """Signed distance of c behind (toward the tail of) station nm's section plane."""
    (_, yt, zt), (_, yb, zb) = S[nm][0], S[nm][4]
    p = Vector((-(zb - zt), yb - yt)).normalized()
    if p.x < 0:
        p = -p
    return (c.y - yt) * p.x + (c.z - zt) * p.y


def body_rule(c, n, i):
    x = abs(c.x)
    if c.z > 0.955 and x > 0.06 and c.y < -0.44:                       # ear: tan cup, light rim, dark back
        if (Vector((x, c.y, c.z)) - Vector(EAR_FRONT)).length < 0.022:
            return 'sock'
        return 'light' if n.y < -0.5 else 'saddle'
    if c.z < 0.012 and n.z < -0.5:
        return 'black'                                                 # the palm pads
    if c.y < -0.15 and c.z < 0.326 and behind('N2s', c) > 0:
        return 'sock'                                                  # fore leg below the zigzag ring
    if 0.1 < c.y < 0.5 and x > 0.045 and c.z < 0.283 + 0.17 * (c.y - 0.27):
        return 'sock'                                                  # hind leg below the zigzag ring
    if c.y > 0.44 and x < 0.1 and behind('T0', c) > 0:                 # tail: dark tip past the zigzag T2 ring
        if behind('T2', c) > 0:
            return 'saddle'
        return 'light' if n.z < -0.2 else 'fur'
    if behind('H5', c) < 0:                                            # head: cream muzzle sides, jaw and cheeks
        if (c.y < -0.70 and c.z < 0.800) or (c.y >= -0.70 and c.z < 0.845):
            return 'cream'
        return 'fur'
    if behind('N2s', c) < 0.004:                                       # mane: cream bib, light sides, grey top
        if x < 0.10 and n.y < -0.15 and n.z < 0.5:
            return 'cream'
        return 'fur' if c.z > 0.985 - 0.65 * (c.y + 0.45) - 0.15 else 'light'      # grey within 15 cm of the neck's top line
    if n.z < -0.35 and c.z > 0.36:
        return 'cream'                                                 # belly
    if c.y < 0.28:
        if c.z > 0.60 and n.z > -0.1:
            return 'saddle'                                            # the dark saddle
        if 0.40 < c.z < 0.585 and -0.12 < c.y and n.z < 0.2:
            return 'light'                                             # lower flank
    elif n.z > 0.8:
        return 'saddle'                                                # the saddle's point over the croup
    return 'fur'


def mirrored(ob, name):
    """A left-side part -> one piece with a live Mirror (both flanks), materials kept."""
    bm = edit(ob)
    bm.transform(ob.matrix_world)
    new = object_from_bm(name, bm, mirror=True)
    new.modifiers[0].use_clip = False
    new.modifiers[0].use_mirror_merge = False
    for m in ob.data.materials:
        new.data.materials.append(m)
    bm.free()
    me = ob.data
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    white(new)
    return new


def stage3(k, body):
    paint(body, {q: PAL[q] for q in ('fur', 'saddle', 'light', 'cream', 'sock', 'black')}, body_rule)
    pieces = []
    # toes and claws: what the welded library paws (paw_canine, toe_segs=1) left behind in stage 1
    for nm in ('paw_fore', 'paw_hind'):
        pieces.append(mirrored(REST[nm], 'toes_' + nm[4:]))
    # eyes: library eye_set on the socket face of the cage; a stern, level brow (the concept's calm predator)
    me = body.data
    ef = min(me.polygons, key=lambda q: (q.center - Vector((0.088, -0.655, 0.910))).length)
    ec, en = ef.center.copy(), ef.normal.copy()
    fw = (en + Vector((0.35, -0.75, -0.25))).normalized()
    say('eye face', tuple(round(q, 3) for q in ec), tuple(round(q, 3) for q in en))
    em = dict(eye_rim='saddle', eye_socket='black', iris='iris', pupil='black', glint='cream', lid='saddle')
    for sd, nm in ((1, 'eye_L'), (-1, 'eye_R')):
        f = (lambda v: v) if sd > 0 else MIR
        pieces.append(P.eye_set(f(tuple(ec)), 0.023, forward=f(tuple(fw)), up=(0, 0, 1), side=sd, expression='angry',
                                brow=13.0, lid=0.26, pupil_size=0.55, name=nm, mats=em, colours=dict(iris=PAL['iris'])))
    # nose
    pieces.append(P.nose_pad((0.0, -0.850, 0.794), width=0.052, forward=(0, -1, -0.10), up=(0, 0, 1), kind='canine',
                             name='nose', mats=dict(nose='black', nostril='black')))
    # fur: three big clumps (lite, n=3), each one on a silhouette break of the concept
    # (a mirrored cheek clump was tried in rounds 1-2: it read as a lump stuck on the mane and came off the skin
    # between the head and neck bones in the attack; the cheek ruff is the stage-2 ring instead)
    pieces.append(P.fur_clump((0.0, -0.548, 0.500), length=0.17, width=0.19, forward=(0, 0.53, -0.85), up=(0, -0.85, -0.53),
                              n=3, hook=0.10, thickness=0.42, name='bib', mats=dict(fur='cream', fur_tip='cream')))
    pieces.append(P.fur_clump((0.0, -0.395, 0.978), length=0.15, width=0.19, forward=(0, 0.93, -0.36), up=(0, 0.30, 0.95),
                              n=3, hook=0.14, thickness=0.42, name='nape', mats=dict(fur='fur', fur_tip='light')))
    pieces.append(P.fur_clump((0.0, -0.262, 0.905), length=0.18, width=0.21, forward=(0, 0.68, -0.73), up=(0, 0.73, 0.68),
                              n=3, hook=0.14, thickness=0.42, name='withers', mats=dict(fur='fur', fur_tip='saddle')))
    return pieces


def stage4(k, body, pieces):
    rig = armature([
        ('pelvis', J['pelvis'], J['spine'], None),
        ('spine', J['spine'], J['neck'], 'pelvis'),
        ('neck', J['neck'], J['head'], 'spine'),
        ('head', J['head'], J['snout'], 'neck'),
        ('tail0', J['tail0'], J['tail1'], 'pelvis'),
        ('tail1', J['tail1'], J['tail2'], 'tail0'),
        ('upperarm.L', J['shoulderL'], J['elbowL'], 'spine'),
        ('forearm.L', J['elbowL'], J['wristL'], 'upperarm.L'),
        ('paw.L', J['wristL'], J['pawL'], 'forearm.L'),
        ('thigh.L', J['hipL'], J['kneeL'], 'pelvis'),
        ('shin.L', J['kneeL'], J['hockL'], 'thigh.L'),
        ('foot.L', J['hockL'], J['toeL'], 'shin.L'),
    ], roll='auto')
    skin(body, rig)
    for p in pieces:
        n = p.name
        if 'toes' in n:
            bind(p, rig)                                    # each toe rigid on its own paw bone
        elif 'eye' in n or 'nose' in n:
            bind(p, rig, bone='head')
        else:
            bind(p, rig, body=body)                         # fur clumps ride the skin under them

    # signs (roll='auto'): limb and tail bones +X = tip forward; pelvis / spine / neck / head +X = tip up
    idle = {1: {}, 13: {'spine': (1.5, 0, 0), 'neck': (-2, 0, 2), 'head': (3, 0, 5), 'tail0': (0, 0, 7), 'tail1': (0, 0, 6)},
            25: {'spine': (2.2, 0, 0), 'neck': (-3, 0, 0), 'head': (-2, 0, 0), 'tail0': (0, 0, -7), 'tail1': (0, 0, -6)},
            37: {'spine': (1.0, 0, 0), 'neck': (-1, 0, -2), 'head': (3, 0, -5), 'tail0': (0, 0, 5), 'tail1': (0, 0, 4)}, 49: {}}
    clip(rig, 'idle', idle)

    def step(ph):
        """One leg's keys at phase ph (0 = contact in front, 1 = mid stance, 2 = push-off, 3 = swing): (upper, lower, end)."""
        fore = [((24, 0, 0), (-6, 0, 0), (8, 0, 0)), ((0, 0, 0), (0, 0, 0), (0, 0, 0)),
                ((-24, 0, 0), (8, 0, 0), (-14, 0, 0)), ((4, 0, 0), (36, 0, 0), (-32, 0, 0))]
        hind = [((20, 0, 0), (-4, 0, 0), (6, 0, 0)), ((0, 0, 0), (0, 0, 0), (0, 0, 0)),
                ((-22, 0, 0), (8, 0, 0), (-10, 0, 0)), ((10, 0, 0), (-30, 0, 0), (-8, 0, 0))]
        return fore[ph % 4], hind[ph % 4]
    move, mloc = {}, {}
    for i, f in enumerate((1, 7, 13, 19, 25)):
        fa, ha = step(i)            # left fore + right hind (a trot: diagonal pairs)
        fb, hb = step(i + 2)
        move[f] = {'upperarm.L': fa[0], 'forearm.L': fa[1], 'paw.L': fa[2],
                   'thigh.R': ha[0], 'shin.R': ha[1], 'foot.R': ha[2],
                   'upperarm.R': fb[0], 'forearm.R': fb[1], 'paw.R': fb[2],
                   'thigh.L': hb[0], 'shin.L': hb[1], 'foot.L': hb[2],
                   'head': ((3, 0, 0) if i % 2 else (-2, 0, 0)), 'neck': ((-3, 0, 0) if i % 2 else (1, 0, 0)),
                   'tail0': ((-8, 0, 0) if i % 2 else (-14, 0, 0)), 'tail1': (-8, 0, 0)}
        mloc[f] = {'pelvis': (0, 0, 0.012 if i % 2 else -0.012)}
    clip(rig, 'move', move, loc=mloc)

    # attack: a pounce. Coil (chest down, rump up, head low), launch (front end thrown up and forward, fore paws
    # reaching, hind legs driving, tail streaming), bite down, recover
    coil = {'pelvis': (-9, 0, 0), 'spine': (-4, 0, 0), 'neck': (12, 0, 0), 'head': (-6, 0, 0),
            'upperarm.L': (-20, 0, 0), 'upperarm.R': (-20, 0, 0), 'forearm.L': (34, 0, 0), 'forearm.R': (34, 0, 0),
            'paw.L': (-8, 0, 0), 'paw.R': (-8, 0, 0),
            'thigh.L': (16, 0, 0), 'thigh.R': (16, 0, 0), 'shin.L': (-14, 0, 0), 'shin.R': (-14, 0, 0),
            'tail0': (-6, 0, 0), 'tail1': (10, 0, 0)}
    leap = {'pelvis': (20, 0, 0), 'spine': (8, 0, 0), 'neck': (-14, 0, 0), 'head': (-12, 0, 0),
            'upperarm.L': (48, 0, 0), 'upperarm.R': (34, 0, 0), 'forearm.L': (8, 0, 0), 'forearm.R': (22, 0, 0),
            'paw.L': (-30, 0, 0), 'paw.R': (-34, 0, 0),
            'thigh.L': (-34, 0, 0), 'thigh.R': (-30, 0, 0), 'shin.L': (14, 0, 0), 'shin.R': (10, 0, 0),
            'foot.L': (-14, 0, 0), 'foot.R': (-10, 0, 0), 'tail0': (-34, 0, 0), 'tail1': (-14, 0, 0)}
    bite = {'pelvis': (6, 0, 0), 'spine': (-2, 0, 0), 'neck': (-20, 0, 0), 'head': (-16, 0, 0),
            'upperarm.L': (26, 0, 0), 'upperarm.R': (20, 0, 0), 'forearm.L': (-4, 0, 0), 'forearm.R': (-2, 0, 0),
            'paw.L': (-6, 0, 0), 'paw.R': (-6, 0, 0),
            'thigh.L': (-18, 0, 0), 'thigh.R': (-16, 0, 0), 'shin.L': (8, 0, 0), 'shin.R': (6, 0, 0),
            'foot.L': (-8, 0, 0), 'foot.R': (-6, 0, 0), 'tail0': (-18, 0, 0), 'tail1': (-6, 0, 0)}
    clip(rig, 'attack', {1: {}, 8: coil, 15: leap, 18: leap, 23: bite, 33: {}},
         loc={1: {'pelvis': (0, 0, 0)}, 8: {'pelvis': (0, -0.05, -0.05)}, 15: {'pelvis': (0, 0.10, 0.03)},
              18: {'pelvis': (0, 0.12, 0.03)}, 23: {'pelvis': (0, 0.10, -0.02)}, 33: {'pelvis': (0, 0, 0)}})
    return rig


if os.environ.get('WOLF_DIAG'):                 # where the tech-QA flags sit (rest centres), for NOTES
    import techqa as _Q
    _m = _Q.measure

    def _diag(body, pieces, size, rig=None, acts=None):
        out = _m(body, pieces, size, rig, acts)
        for o in [body] + list(pieces):
            for op, cls in sorted(out[1].get(o.name, {}).items()):
                if cls in os.environ['WOLF_DIAG'].split(','):
                    c = o.data.polygons[op].center
                    say('DIAG', o.name, cls, op, round(c.x, 3), round(c.y, 3), round(c.z, 3))
        return out
    _Q.measure = _diag

run(META, stage1, stage2, stage3, stage4)
