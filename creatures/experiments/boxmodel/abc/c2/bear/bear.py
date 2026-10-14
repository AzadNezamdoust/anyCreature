import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from carve import carve_guide, hull_sections, fit_to_guide

# Stage 1 = a quad cage box-modelled on J over the hidden hull of reference/ (carve_guide). v2 of the pilot:
# the head is a box with a face plane and a muzzle block, the limbs root at the shoulder and hip points
# (upper arm and thigh are masses on the flank), the flank rings are sheared so no band is a vertical stripe.

# the skeleton (metres, faces -Y, left flank +X, feet on z = 0), read off the reference side and front views
J = dict(
    pelvis=(0.0, 0.60, 0.62), spine=(0.0, 0.10, 0.66), neck=(0.0, -0.36, 0.68),
    head=(0.0, -0.58, 0.60), snout=(0.0, -0.845, 0.47),
    tail0=(0.0, 0.74, 0.66), tail1=(0.0, 0.812, 0.64),
    shoulderL=(0.24, -0.05, 0.60), elbowL=(0.238, -0.030, 0.300), wristL=(0.23, -0.066, 0.172),
    pawL=(0.228, -0.30, 0.03),
    hipL=(0.24, 0.58, 0.60), kneeL=(0.238, 0.56, 0.320), hockL=(0.23, 0.715, 0.180),
    toeL=(0.228, 0.50, 0.03),
)
PLAN = dict(spine=['pelvis', 'spine', 'neck', 'head', 'snout'],
            limbs=dict(fore=['shoulderL', 'elbowL', 'wristL', 'pawL'], hind=['hipL', 'kneeL', 'hockL', 'toeL']),
            extra=[['tail0', 'tail1']])
META = dict(creature='bear', model='opus', cage=True, J=J, plan=PLAN, intended={})


def sec(y, zt, zb, w, zw=None, up=None, lo=None, dy=(0, 0, 0)):
    """A half section, top seam -> bottom seam: 5 vertices (an 8-sided whole section).
    up / lo: the upper and lower corner as (x, z). dy: y shear of (upper corner, widest, lower corner),
    so a ring leans along the shoulder blade or the thigh instead of standing as a vertical slice."""
    h = zt - zb
    zw = zw if zw is not None else zb + 0.45 * h
    up = up or (0.55 * w, zt - 0.10 * h)
    lo = lo or (0.50 * w, zb + 0.08 * h)
    return [(0.0, y, zt), (up[0], y + dy[0], up[1]), (w, y + dy[1], zw), (lo[0], y + dy[2], lo[1]), (0.0, y, zb)]


# nose -> tail
STATIONS = [
    # head: muzzle block, the stop, a broad boxy skull (the widest point at eye height, a broad flat top)
    ('H0', sec(-0.850, 0.494, 0.450, 0.044, up=(0.036, 0.492), lo=(0.036, 0.453))),                 # nose tip
    ('H1', sec(-0.805, 0.528, 0.408, 0.068, zw=0.470, up=(0.056, 0.523), lo=(0.058, 0.414))),       # muzzle
    ('H2', sec(-0.757, 0.560, 0.388, 0.085, zw=0.480, up=(0.070, 0.553), lo=(0.072, 0.396))),       # muzzle root, under the stop
    ('H3', sec(-0.738, 0.646, 0.390, 0.180, zw=0.500, up=(0.125, 0.642), lo=(0.105, 0.402), dy=(-0.012, 0.008, 0.0))),       # the stop: brow ridge, cheek front
    ('H4', sec(-0.675, 0.704, 0.412, 0.224, zw=0.545, up=(0.165, 0.690), lo=(0.125, 0.425))),       # eye line, cheek
    ('H5', sec(-0.610, 0.745, 0.412, 0.242, zw=0.575, up=(0.198, 0.742), lo=(0.130, 0.425))),       # skull, ear corner
    ('H6', sec(-0.535, 0.782, 0.420, 0.236, zw=0.600, up=(0.190, 0.776), lo=(0.125, 0.432))),       # back of skull
    # neck ruff (a step out from the skull), chest, hump: narrow at the top, the shoulder low and wide
    ('NK', sec(-0.468, 0.815, 0.422, 0.212, zw=0.600, up=(0.138, 0.780))),
    ('TN', sec(-0.360, 0.872, 0.378, 0.295, zw=0.590, up=(0.165, 0.835))),
    ('T1', sec(-0.290, 0.920, 0.333, 0.340, zw=0.530, up=(0.172, 0.868), dy=(0.035, -0.035, 0.0))),
    # fore leg root: the widest vertex is the shoulder (front, point, back of the upper arm)
    ('T2', sec(-0.185, 0.998, 0.292, 0.335, zw=0.580, up=(0.140, 0.918), lo=(0.105, 0.335), dy=(0.0, -0.025, 0.0))),
    ('T3', sec(-0.040, 0.990, 0.285, 0.332, zw=0.590, up=(0.140, 0.912), lo=(0.100, 0.335), dy=(0.0, -0.02, 0.0))),
    ('T4', sec(0.135, 0.905, 0.285, 0.278, zw=0.570, up=(0.165, 0.840), lo=(0.105, 0.335), dy=(-0.065, 0.025, 0.0))),
    ('T5', sec(0.270, 0.872, 0.268, 0.255, zw=0.560, up=(0.155, 0.808), dy=(0.02, 0.0, -0.02))),                                              # waist
    # hind leg root: thigh front, hip point, back of the thigh
    ('T6', sec(0.440, 0.866, 0.305, 0.335, zw=0.580, up=(0.200, 0.802), lo=(0.105, 0.345), dy=(0.06, -0.03, -0.01))),
    ('T7', sec(0.600, 0.810, 0.350, 0.352, zw=0.610, up=(0.215, 0.752), lo=(0.105, 0.375))),
    ('T8', sec(0.762, 0.705, 0.440, 0.275, zw=0.560, up=(0.175, 0.668), lo=(0.100, 0.455))),        # rump
    ('TA', sec(0.782, 0.730, 0.580, 0.085)),                                                        # stub tail: a ball
    ('TB', sec(0.812, 0.700, 0.592, 0.080)),
    ('TC', sec(0.824, 0.668, 0.620, 0.038)),
]


def hexring(cx, cy, z, rx, ry, tilt=0.0, roll=0.0):
    """A 6-sided limb ring. tilt: front up / back down; roll: outer side up / inner side down."""
    return dict(OF=(cx + 0.8 * rx, cy - ry, z + tilt + roll), OM=(cx + rx, cy, z + roll),
                OB=(cx + 0.8 * rx, cy + ry, z - tilt + roll), IB=(cx - 0.8 * rx, cy + ry, z - tilt - roll),
                IM=(cx - rx, cy, z - roll), IF=(cx - 0.8 * rx, cy - ry, z + tilt - roll))


def leg(bm, faces, cur, rings):
    """Extrude a 2-quad region ring by ring (a 6-sided limb); cur maps role -> boundary vert.
    Returns the end faces and the last ring in order (OF OM OB IB IM IF)."""
    for rg in rings:
        r = extrude(bm, faces)
        nv = r['verts']
        m = {role: min(nv, key=lambda q: (q.co - v.co).length) for role, v in cur.items()}
        for role, p in hexring(*rg).items():
            m[role].co = Vector(p)
        faces, cur = r['faces'], m
    return faces, [cur[r] for r in ('OF', 'OM', 'OB', 'IB', 'IM', 'IF')]


# limb rings: (cx, cy, z, rx, ry, tilt, roll), placed from the side sheet's front and back leg edges
FORE = [(0.243, -0.040, 0.415, 0.135, 0.165, 0.0, 0.090),    # shoulder / upper arm: a mass standing off the barrel
        (0.240, -0.028, 0.345, 0.128, 0.162, 0.0, 0.025),    # elbow: three loops, the point at the back
        (0.238, -0.027, 0.300, 0.122, 0.160, 0.0, 0.010),
        (0.236, -0.035, 0.258, 0.114, 0.150),                # forearm
        (0.232, -0.045, 0.205, 0.104, 0.140),                # wrist: three loops
        (0.230, -0.054, 0.172, 0.098, 0.134),
        (0.229, -0.066, 0.142, 0.096, 0.126),
        (0.229, -0.076, 0.118, 0.096, 0.121)]                # the paw starts one loop below the joint
HIND = [(0.245, 0.580, 0.440, 0.140, 0.195, -0.035, 0.070),  # thigh: a heavy mass, its front edge runs into the flank
        (0.240, 0.5825, 0.360, 0.132, 0.2075, -0.010, 0.020),# stifle: three loops, the knee forward under the belly
        (0.238, 0.6025, 0.315, 0.126, 0.2025),
        (0.236, 0.6425, 0.270, 0.118, 0.1875),               # shank: the front edge falls back to the hock
        (0.232, 0.684, 0.215, 0.106, 0.164),                 # hock: three loops, the point at the back
        (0.230, 0.699, 0.180, 0.100, 0.149),
        (0.229, 0.7015, 0.148, 0.098, 0.1365),
        (0.229, 0.702, 0.122, 0.098, 0.130)]                 # the paw starts one loop below the joint
PAWS = dict(fore=dict(origin=(0.229, -0.085, 0.100), width=0.225, height=0.100, forward=(0.10, -1.0, 0.0), root=(0.185, 0.215)),
            hind=dict(origin=(0.229, 0.702, 0.100), width=0.232, height=0.100, forward=(0.04, -1.0, 0.0), root=(0.188, 0.250)))
REST = []                                                    # what bridge_part leaves behind (the claws): stage-3 pieces


def weld_paw(bm, faces, ring_, which):
    """The library bear paw (parts.paw_bear, lite toes) welded onto the limb's last ring: one shell with the base."""
    import parts as P
    bmesh.ops.delete(bm, geom=list(faces), context='FACES')
    d = PAWS[which]
    paw = P.paw_bear(d['origin'], width=d['width'], height=d['height'], forward=d['forward'], toe_segs=1,
                     claws=True, claw_len=0.8, root=d['root'], open_root=True, name=f'paw_{which}',
                     mats={'skin': 'sock', 'pad': 'pad', 'claw': 'claw'},
                     colours={'skin': '#4a3229', 'pad': '#33241f', 'claw': '#2b2a2c'})
    rest = bridge_part(paw, ring_, bm=bm)
    if rest is not None:
        REST.append(rest)


def stage1(k):
    guide = carve_guide(k)
    del REST[:]
    bm = bmesh.new()
    idx, rings = {}, []
    for i, (nm, pts) in enumerate(STATIONS):
        idx[nm] = i
        rings.append(ring(bm, pts))
    # the planar free ring (neck ruff) slides onto the guide; the head is designed (broader than the
    # hull's lofted wedge) and the leg stations are placed by hand: the hull fuses leg and flank there
    fit = fit_to_guide([rings[idx[n]] for n in ('TN',)], guide, max_move=0.015)
    say('fit_to_guide (moved, capped):', fit)
    bands = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, list(reversed(rings[0])))
    cap(bm, rings[-1])
    R = lambda nm, j: rings[idx[nm]][j]
    eye_face = bands[idx['H3']][1]

    f, r = leg(bm, [bands[idx['T2']][2], bands[idx['T3']][2]],
               dict(OF=R('T2', 2), OM=R('T3', 2), OB=R('T4', 2), IB=R('T4', 3), IM=R('T3', 3), IF=R('T2', 3)), FORE)
    weld_paw(bm, f, r, 'fore')
    f, r = leg(bm, [bands[idx['T6']][2], bands[idx['T7']][2]],
               dict(OF=R('T6', 2), OM=R('T7', 2), OB=R('T8', 2), IB=R('T8', 3), IM=R('T7', 3), IF=R('T6', 3)), HIND)
    weld_paw(bm, f, r, 'hind')

    # eye: a loop inside the brow-cheek plane between H3 and H4 (the socket), pushed in a little
    for v in inset(bm, [eye_face], 0.50, -0.006)[0].verts:
        v.co += Vector((-0.004, 0.0, 0.020))             # small, up under the brow

    snap_seam(bm)
    return object_from_bm('body', bm)


def stage2(k, body):
    """Secondary forms: a forehead / cheekbone ring, a neck-ruff ring (the third neck loop), and one ring per
    lower leg that carries the dark sock's zigzag colour border. Then vertex moves for the face planes."""
    bm = edit(body)
    hv = lambda rg, role: vert_near(bm, hexring(*rg)[role])
    # (found before any cut) the lower-leg rings next to the sock loops, the inner columns of the leg roots
    fr = [{r: hv(rg, r) for r in ('OF', 'OM', 'OB', 'IB', 'IM', 'IF')} for rg in FORE[:5]]
    hr = [{r: hv(rg, r) for r in ('OF', 'OM', 'OB', 'IB', 'IM', 'IF')} for rg in HIND[:5]]
    lo = {n: vert_near(bm, STATIONS[[q[0] for q in STATIONS].index(n)][1][3]) for n in ('T2', 'T3', 'T4', 'T6', 'T7', 'T8')}
    with k.topo(bm, 'loop', 'forehead / cheekbone ring between the eye line and the skull: the brow-to-forehead plane break'):
        hd = loopcut(bm, edge_near(bm, (0.0, -0.6425, 0.7245)), t=0.45)
    with k.topo(bm, 'loop', 'neck ruff ring behind the skull: third neck loop, the ruff step'):
        nk = loopcut(bm, edge_near(bm, (0.0, -0.414, 0.8435)), t=0.35)
    with k.topo(bm, 'loop', 'fore sock border: a ring on the forearm between the elbow and wrist loops'):
        fs = loopcut(bm, edge_near(bm, (0.343, -0.040, 0.2315)), t=0.5)
    with k.topo(bm, 'loop', 'hind sock border: a ring on the shank between the stifle and hock loops'):
        hs = loopcut(bm, edge_near(bm, (0.346, 0.663, 0.2425)), t=0.5)
    bm.verts.ensure_lookup_table()
    # sock border: a zigzag (alternate ring vertices up and down) so the colour edge reads as fur tips
    # (the rings above and below make room first: 7.7 cm between them, still inside each joint's band)
    # ring spacing down the lower leg: no band thinner than 2.3 cm (needle triangles), the paw root band the widest
    for rr, lg, dz in ((fr, FORE, (0.014, -0.005, 0.005, 0.011, 0.011)), (hr, HIND, (0.006, -0.006, 0.004, 0.011, 0.012))):
        low = rr + [{r: hv(rg, r) for r in rr[0]} for rg in lg[5:]]
        for i, d in zip(range(3, 8), dz):
            for v in low[i].values():
                v.co.z += d
    for ring_ in (fs, hs):
        zm = sum(v.co.z for v in ring_) / len(ring_)
        for i, v in enumerate(ring_):
            v.co.z = zm + (0.011 if i % 2 == 0 else -0.011)
    # leg roots, inner side: the armpit and groin columns spaced evenly (they were 0.5-1 cm slivers)
    for n in ('T2', 'T3', 'T4'):
        lo[n].co.z = 0.385
    for role in ('IF', 'IM', 'IB'):
        for i, z in enumerate((0.358, 0.326, 0.296)):
            fr[i][role].co.z = z
    lo['T6'].co.z, lo['T7'].co.z = 0.372, 0.425
    for role, zs in (('IF', (0.365, 0.333, 0.303)), ('IM', (0.372, 0.342, 0.312)), ('IB', (0.405, 0.365, 0.322))):
        for i, z in enumerate(zs):
            hr[i][role].co.z = z
    # forehead ring: a broad flat forehead with a corner the ear stands on, a cheekbone under it
    for v in hd:
        c = v.co
        if c.x < 1e-4 and c.z > 0.6:
            c.z += 0.006
        elif c.z > 0.66:
            c.x, c.z = 0.192, c.z + 0.014
        elif 0.5 < c.z <= 0.66:
            c.x, c.z = 0.240, 0.548
        elif c.x > 1e-4:
            c.x -= 0.006
    # neck ruff ring: a step out right behind the skull
    for v in nk:
        c = v.co
        if 0.5 < c.z < 0.7 and c.x > 0.1:
            c.x, c.y = 0.268, c.y - 0.012
        elif c.z >= 0.7 and c.x > 0.05:
            c.x += 0.018
    # brow: the ridge overhangs the eye plane; the cheek front tucks in under it
    b = vert_near(bm, (0.125, -0.745, 0.642)); b.co += Vector((0.010, -0.010, 0.004))
    ck = vert_near(bm, (0.170, -0.725, 0.500)); ck.co += Vector((-0.006, 0.006, -0.006))
    # hip bone and shoulder point: one clear corner each on the flank
    hp = vert_near(bm, (0.352, 0.600, 0.610)); hp.co += Vector((0.008, 0.0, 0.012))
    tu = vert_near(bm, (0.047, 0.782, 0.715)); tu.co.x, tu.co.z = 0.078, 0.700
    # stub tail: the ball stands 2 cm further off the rump (its root band was a needle strip)
    for v in verts_where(bm, lambda c: c.y > 0.775 and c.x < 0.09 and c.z > 0.57):
        v.co.y += 0.02
    snap_seam(bm)
    commit(body, bm)
    bm.free()


PAL = dict(fur='#a2683f', sock='#55372a', cream='#e0c39a', dark='#26221f', iris='#c98a2e', glint='#ffffff')
MIR = lambda v: (-v[0], v[1], v[2])


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


def body_rule(c, n, i):
    if c.z < 0.240:
        return 'sock'                                        # below the zigzag ring: sock, paw and sole
    if c.z < 0.272 and abs(c.x) > 0.12:                      # the band above it: every other facet dark, so the border is
        cy = -0.035 if c.y < 0.3 else 0.6425                 # a row of fur points on the ring's edges, not a level line
        ang = math.degrees(math.atan2(c.y - cy, abs(c.x) - 0.236))
        if int((ang + 180.0) // 60.0) % 2 == 0:
            return 'sock'
    if c.y < -0.742 and c.z < 0.60:
        return 'cream'                                       # the muzzle block, up to the stop
    if -0.56 < c.y < -0.26 and c.z < 0.50 and abs(c.x) < 0.21 and n.z < 0.25:
        return 'cream'                                       # the chest bib under the neck
    return 'fur'


def stage3(k, body):
    import parts as P
    paint(body, {q: PAL[q] for q in ('fur', 'sock', 'cream')}, body_rule)
    pieces = []
    # claws: what the welded library paws left behind in stage 1
    for i, r in enumerate(REST):
        ob = mirrored(r, 'claws_%d' % i)
        paint(ob, {'dark': PAL['dark']}, lambda c, n, j: 'dark')
        pieces.append(ob)
    # eyes: on the socket face of the cage (the inset loop under the brow), a stern brow
    me = body.data
    ef = min(me.polygons, key=lambda q: (q.center - Vector((0.170, -0.708, 0.612))).length)
    ec, en = ef.center.copy(), ef.normal.copy()
    say('eye face', tuple(round(q, 3) for q in ec), tuple(round(q, 3) for q in en))
    em = dict(eye_rim='fur', eye_socket='dark', iris='iris', pupil='dark', glint='glint', lid='sock')
    ecol = dict(iris=PAL['iris'], glint=PAL['glint'], eye_socket=PAL['dark'], pupil=PAL['dark'])
    for sd, nm in ((1, 'eye_L'), (-1, 'eye_R')):
        f = (lambda v: v) if sd > 0 else MIR
        pieces.append(P.eye_set(f(tuple(ec)), 0.021, forward=f(tuple(en)), up=(0, 0, 1), side=sd, expression='angry',
                                pupil_size=0.62, name=nm, mats=em, colours=ecol))
    # ears: round cups on the skull corners
    for sd, nm in ((1, 'ear_L'), (-1, 'ear_R')):
        f = (lambda v: v) if sd > 0 else MIR
        pieces.append(P.ear_cup(f((0.186, -0.588, 0.742)), length=0.135, width=0.145, forward=f((0.25, -1.0, 0.05)),
                                up=f((0.42, 0.10, 1.0)), side=sd, kind='round', name=nm,
                                mats=dict(ear='fur', ear_inner='sock')))
    # nose
    pieces.append(P.nose_pad((0.0, -0.850, 0.478), width=0.074, forward=(0, -1, -0.12), up=(0, 0, 1), kind='bear',
                             name='nose', mats=dict(nose='dark', nostril='dark')))
    # fur: a few big clumps
    fm = dict(fur='fur', fur_tip='fur')
    # (round 1 had five clumps: a hump crest, elbow and haunch tufts read as spikes glued on and broke the hump
    # outline; the concept is a clean faceted bear, so only the jowl ruff and the chest ruff stay, lying flat)
    # (a chest ruff was tried in rounds 1-3: it cut through the chest keel twice from any angle; the bib is painted)
    pieces.append(mirrored(P.fur_clump((0.232, -0.600, 0.560), length=0.19, width=0.24, forward=(0.30, 0.80, -0.52),
                                       up=(1, -0.15, 0.05), n=3, radius=0.26, hook=0.04, thickness=0.38, name='cheek_', mats=fm), 'cheek'))
    return pieces




def stage4(k, body, pieces):
    rig = armature([
        ('pelvis', J['pelvis'], J['spine'], None),
        ('spine', J['spine'], J['neck'], 'pelvis'),
        ('neck', J['neck'], J['head'], 'spine'),
        ('head', J['head'], J['snout'], 'neck'),
        ('tail', J['tail0'], J['tail1'], 'pelvis'),
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
        if 'claws' in n:
            bind(p, rig)                                    # each claw rigid on its own paw bone
        elif 'eye' in n or 'nose' in n:
            bind(p, rig, bone='head')
        else:
            bind(p, rig, body=body)                         # ears and jowl ruff ride the skin under them

    # signs (roll='auto'): limb bones +X = tip forward; spine / neck / head / paw / foot bones +X = tip up
    idle = {1: {}, 13: {'spine': (1.2, 0, 0), 'neck': (-2, 0, 3), 'head': (2, 0, 4), 'tail': (0, 0, 8)},
            25: {'spine': (2.0, 0, 0), 'neck': (-3, 0, 0), 'head': (-2, 0, 0), 'tail': (0, 0, -8)},
            37: {'spine': (1.0, 0, 0), 'neck': (-1, 0, -3), 'head': (2, 0, -4), 'tail': (0, 0, 6)}, 49: {}}
    clip(rig, 'idle', idle)

    def step(ph):
        """One leg's keys over the cycle at phase ph (0 = contact in front): (upper, lower, end)."""
        fore = [((20, 0, 0), (-4, 0, 0), (6, 0, 0)), ((0, 0, 0), (0, 0, 0), (0, 0, 0)),
                ((-20, 0, 0), (6, 0, 0), (-10, 0, 0)), ((2, 0, 0), (34, 0, 0), (-28, 0, 0))]
        hind = [((18, 0, 0), (-4, 0, 0), (4, 0, 0)), ((0, 0, 0), (0, 0, 0), (0, 0, 0)),
                ((-18, 0, 0), (4, 0, 0), (-8, 0, 0)), ((8, 0, 0), (-26, 0, 0), (-6, 0, 0))]
        return fore[ph % 4], hind[ph % 4]
    move = {}
    for i, f in enumerate((1, 9, 17, 25, 33)):
        fa, ha = step(i)            # left fore + right hind
        fb, hb = step(i + 2)        # right fore + left hind
        move[f] = {'upperarm.L': fa[0], 'forearm.L': fa[1], 'paw.L': fa[2],
                   'thigh.R': ha[0], 'shin.R': ha[1], 'foot.R': ha[2],
                   'upperarm.R': fb[0], 'forearm.R': fb[1], 'paw.R': fb[2],
                   'thigh.L': hb[0], 'shin.L': hb[1], 'foot.L': hb[2],
                   'head': ((2.5, 0, 0) if i % 2 else (-1.5, 0, 0)), 'neck': ((-2, 0, 0) if i % 2 else (1, 0, 0)),
                   'spine': (0, 0, 2.5 * (1 if i % 4 == 0 else -1 if i % 4 == 2 else 0))}
    clip(rig, 'move', move)

    # attack: sink back, rear the front end up with the right paw cocked high, slam it down
    wind = {'pelvis': (-3, 0, 0), 'spine': (-4, 0, 0), 'neck': (8, 0, 0), 'head': (-6, 0, 0),
            'upperarm.L': (-8, 0, 0), 'upperarm.R': (-12, 0, 0), 'forearm.L': (10, 0, 0), 'forearm.R': (14, 0, 0),
            'thigh.L': (3, 0, 0), 'thigh.R': (3, 0, 0)}
    rear = {'pelvis': (11, 0, 0), 'spine': (15, 0, 0), 'neck': (10, 0, 0), 'head': (16, 0, 0),
            'thigh.L': (-11, 0, 0), 'thigh.R': (-11, 0, 0),
            'upperarm.R': (58, 0, -12), 'forearm.R': (-18, 0, 0), 'paw.R': (-20, 0, 0),
            'upperarm.L': (-14, 0, 0), 'forearm.L': (30, 0, 0), 'paw.L': (-26, 0, 0), 'tail': (10, 0, 0)}
    slam = {'pelvis': (-2, 0, 0), 'spine': (-5, 0, 0), 'neck': (-8, 0, 0), 'head': (-10, 0, 0),
            'thigh.L': (2, 0, 0), 'thigh.R': (2, 0, 0),
            'upperarm.R': (26, 0, 0), 'forearm.R': (-14, 0, 0), 'paw.R': (8, 0, 0),
            'upperarm.L': (-4, 0, 0), 'forearm.L': (6, 0, 0)}
    clip(rig, 'attack', {1: {}, 7: wind, 15: rear, 19: rear, 23: slam, 33: {}})
    return rig


if os.environ.get('BEAR_DIAG'):                 # where the range-of-motion fold-overs sit (rest centres), for NOTES
    import techqa as _Q
    _m = _Q.measure

    def _diag(body, pieces, size, rig=None, acts=None):
        out = _m(body, pieces, size, rig, acts)
        for op, cls in sorted(out[1][body.name].items()):
            if cls in ('flip', 'stretch', 'sliver'):
                c = body.data.polygons[op].center
                say('DIAG', cls, op, round(c.x, 3), round(c.y, 3), round(c.z, 3))
                if cls == 'sliver' and c.x > 0:
                    say('DIAGV', [tuple(round(q, 3) for q in body.data.vertices[i].co) for i in body.data.polygons[op].vertices])
        return out
    _Q.measure = _diag

run(META, stage1, stage2, stage3, stage4)
