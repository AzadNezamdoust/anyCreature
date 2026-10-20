import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from carve import carve_guide, hull_sections, fit_to_guide
import parts as P

# goblin, cage method: the hull of reference/ is a hidden guide; the base is a quad cage box-modelled on J.
# Masses: a pelvis-to-shoulder torso column (8-sided, stacked rings), a short hidden neck, the head as its OWN
# mass (rings front -> back, 10-sided, the neck enters its underside), a face plate round the nose root, the
# hooked nose, swept ears, 6-sided arms and legs extruded out of the torso's side and underside faces.

# the skeleton (metres, faces -Y, left flank +X, feet on z = 0), read off the reference side and front views
J = dict(
    pelvis=(0.0, 0.045, 0.42), spine=(0.0, 0.04, 0.57), neck=(0.0, 0.005, 0.745),
    head=(0.0, -0.07, 0.93), snout=(0.0, -0.29, 0.735),
    shoulderL=(0.172, 0.05, 0.660), elbowL=(0.261, 0.072, 0.492), wristL=(0.299, -0.004, 0.364), handL=(0.305, -0.10, 0.12),
    hipL=(0.108, 0.035, 0.40), kneeL=(0.098, -0.017, 0.253), ankleL=(0.080, 0.043, 0.131), toeL=(0.135, -0.09, 0.03),
    earL=(0.17, 0.02, 0.92), earTipL=(0.555, 0.29, 0.94),
)
PLAN = dict(spine=['pelvis', 'spine', 'neck', 'head', 'snout'],
            limbs=dict(arm=['shoulderL', 'elbowL', 'wristL', 'handL'], leg=['hipL', 'kneeL', 'ankleL', 'toeL']),
            extra=[['earL', 'earTipL']])
META = dict(creature='goblin', model='opus', cage=True, J=J, plan=PLAN, intended={
    'leg length / body height': "the sheet's centre-line clearance is the loincloth's tip (z 0.20); the loincloth is a stage-3 piece "
                                "(brief). The body's crotch is at 0.32, where the sheet's inner thigh ends (0.31)"},
    # the plan view contradicts the side view (ears straight sideways vs swept back, hands 0.13 further forward, toe lumps
    # drawn behind the heels): the side view wins (BRIEF 3), so the plan view cannot be matched past ~0.5
    iou_floor={'top': 0.50})

# torso column, bottom -> top. Half ring: P0 front seam, P1 front corner, P2 side, P3 back corner, P4 back seam
TORSO = [
    ('C',  [(0, -0.030, 0.332), (0.045, -0.030, 0.324), (0.052, 0.035, 0.316), (0.045, 0.104, 0.318), (0, 0.122, 0.324)]),   # crotch strip
    ('BT', [(0, -0.058, 0.375), (0.085, -0.048, 0.370), (0.170, 0.040, 0.365), (0.095, 0.147, 0.348), (0, 0.164, 0.346)]),   # wrapped pelvis block (cloth border)
    ('HP', [(0, -0.060, 0.425), (0.092, -0.036, 0.420), (0.166, 0.040, 0.410), (0.090, 0.140, 0.420), (0, 0.156, 0.430)]),   # hips
    ('BL', [(0, -0.070, 0.500), (0.100, -0.046, 0.500), (0.160, 0.035, 0.510), (0.085, 0.130, 0.545), (0, 0.146, 0.560)]),   # belt, pot belly (review fix 2: wider; the side view caps how far forward)
    ('BE', [(0, -0.040, 0.600), (0.076, -0.022, 0.598), (0.130, 0.035, 0.600), (0.078, 0.108, 0.625), (0, 0.117, 0.635)]),   # waist
    ('CH', [(0, -0.052, 0.648), (0.070, -0.034, 0.648), (0.116, 0.035, 0.650), (0.072, 0.090, 0.675), (0, 0.098, 0.690)]),   # chest sunk, armpit (narrow: a pear)
    ('SH', [(0, -0.058, 0.696), (0.064, -0.042, 0.702), (0.150, 0.030, 0.748), (0.066, 0.088, 0.745), (0, 0.094, 0.750)]),   # sloped shoulders, hump
    ('N1', [(0, -0.066, 0.706), (0.062, -0.052, 0.714), (0.135, 0.012, 0.765), (0.062, 0.074, 0.768), (0, 0.080, 0.770)]),   # neck, lower loop
    ('N2', [(0, -0.078, 0.722), (0.070, -0.060, 0.730), (0.125, 0.005, 0.776), (0.065, 0.066, 0.787), (0, 0.068, 0.790)]),   # neck, upper loop
]

# head, front -> back. Half ring: T top seam, A crown corner, B temple, C cheekbone / ear line, D jaw line, U bottom seam
HEAD = [
    ('F',  [(0, -0.230, 0.920), (0.070, -0.230, 0.932), (0.142, -0.188, 0.926), (0.152, -0.138, 0.836), (0.100, -0.165, 0.740), (0, -0.189, 0.692)]),  # brow rim -> chin
    ('G',  [(0, -0.176, 1.019), (0.066, -0.165, 1.008), (0.152, -0.115, 0.955), (0.165, -0.090, 0.855), (0.112, -0.115, 0.750), (0, -0.150, 0.712)]),  # forehead, jaw
    ('G2', [(0, -0.125, 1.076), (0.082, -0.115, 1.056), (0.158, -0.075, 0.990), (0.172, -0.055, 0.870), (0.125, -0.065, 0.765), (0, -0.105, 0.740)]),  # dome front, throat
    ('HD', [(0, -0.045, 1.100), (0.084, -0.040, 1.077), (0.160, -0.015, 0.998), (0.172, 0.000, 0.878), (0.125, 0.000, 0.782), (0, -0.030, 0.770)]),    # dome top (U goes with the neck hole)
    ('K',  [(0, 0.030, 1.066), (0.075, 0.035, 1.040), (0.125, 0.050, 0.970), (0.130, 0.055, 0.895), (0.095, 0.050, 0.815), (0, 0.052, 0.808)]),      # back of the skull
]
BACK = [(0, 0.074, 0.985), (0, 0.068, 0.890)]                       # the skull's rear seam points
# nose: root ring in the face plate, then down the hook. NT top seam, S1, S2, NU under seam
NOSE = [
    [(0, -0.222, 0.893), (0.050, -0.190, 0.868), (0.058, -0.196, 0.798), (0, -0.214, 0.778)],
    [(0, -0.275, 0.838), (0.030, -0.258, 0.818), (0.034, -0.248, 0.788), (0, -0.245, 0.782)],
    [(0, -0.299, 0.755), (0.016, -0.291, 0.748), (0.018, -0.281, 0.728), (0, -0.268, 0.740)],
    [(0, -0.296, 0.722), (0.012, -0.292, 0.720), (0.012, -0.287, 0.713), (0, -0.284, 0.714)],
]


def ring6(c, rx, ry, ty=0.0, tx=0.0):
    """A 6-sided limb section round c: O* outer (+X), I* inner, *F front (-Y), *B back. ty lifts the front,
    tx lifts the outer side (to set the ring square to a leaning limb)."""
    x, y, z = c
    return dict(OF=(x + 0.8 * rx, y - ry, z + ty + 0.8 * tx), OM=(x + rx, y, z + tx), OB=(x + 0.8 * rx, y + ry, z - ty + 0.8 * tx),
                IB=(x - 0.8 * rx, y + ry, z - ty - 0.8 * tx), IM=(x - rx, y, z - tx), IF=(x - 0.8 * rx, y - ry, z + ty - 0.8 * tx))


def limb(bm, faces, cur, rings):
    """Extrude a 2-quad region ring by ring (a 6-sided limb); cur maps role -> boundary vert. Ends in two quads."""
    for rg in rings:
        r = extrude(bm, faces)
        m = {role: min(r['verts'], key=lambda q: (q.co - v.co).length) for role, v in cur.items()}
        for role, p in rg.items():
            m[role].co = Vector(p)
        faces, cur = r['faces'], m
    return faces, cur


# blockout review fixes 2 + 5: sloped shoulders (deltoid lower and in), elbow out and back, forearm and hand forward and in
ARM = [ring6((0.174, 0.044, 0.655), 0.038, 0.050, 0.0, 0.024),      # deltoid
       ring6((0.213, 0.062, 0.585), 0.040, 0.042, 0.0, 0.016),      # upper arm
       ring6((0.253, 0.076, 0.515), 0.044, 0.048, 0.0, 0.010),      # elbow, upper loop
       ring6((0.269, 0.068, 0.470), 0.042, 0.050, 0.012, 0.008),    # elbow, lower loop
       ring6((0.287, 0.034, 0.420), 0.037, 0.042, 0.022, 0.006),    # forearm
       ring6((0.299, 0.004, 0.378), 0.031, 0.034, 0.016, 0.0),      # wrist, upper loop
       ring6((0.304, -0.010, 0.350), 0.031, 0.035, 0.010, 0.0)]     # wrist, lower loop: parts.hand_three_finger joins here
# blockout review fixes 1, 3, 4: the legs open into an A (knee out and forward, ankle out and back), thigh thicker than the
# shin, knee loops 0.04 apart, a long low foot toed out 20 degrees. The review asked for ankles at x 0.16; the sheet's front
# view keeps them near 0.08 and plants wide feet: ankle 0.112 is the compromise the front IoU allows (NOTES r11).
LEG = [ring6((0.106, 0.004, 0.330), 0.060, 0.068, 0.008, 0.022),    # thigh
       ring6((0.102, -0.020, 0.272), 0.050, 0.078, 0.014, 0.0),     # knee, upper loop
       ring6((0.094, -0.014, 0.234), 0.046, 0.080, -0.006, 0.0),    # knee, lower loop
       ring6((0.084, 0.004, 0.185), 0.041, 0.066, -0.014, 0.0),     # calf
       ring6((0.080, 0.040, 0.145), 0.037, 0.044, -0.006, 0.0),     # ankle, upper loop
       ring6((0.084, 0.046, 0.118), 0.040, 0.046, 0.0, 0.0)]        # ankle, lower loop: parts.foot_biped joins here
HAND = dict(origin=(0.304, -0.014, 0.326), width=0.126, forward=(-0.12, -0.44, -1.0), up=(0.55, -0.80, 0.0),
            curl=0.50, spread=18.0, finger_len=1.12, claw_len=0.40, knuckle=0.25, wrist=(0.070, 0.062))
FOOT = dict(origin=(0.098, 0.048, 0.096), width=0.180, forward=(0.38, -0.925, 0.0), height=0.096, length=0.255,
            toes=3, claws=True, claw_len=0.42, root=(0.084, 0.092))
REST = []            # stage 1 -> 3: the library hand's and foot's claw shells (they cannot join a one-shell base)


def stage1(k):
    guide = carve_guide(k)
    if os.environ.get('GOB_SECTIONS'):
        hull_sections(guide, (0, 0.04, 0.34), (0, 0.04, 0.80), 10, 'torso')
        hull_sections(guide, (0, -0.22, 0.90), (0, 0.07, 0.90), 7, 'head')
        hull_sections(guide, J['elbowL'], J['wristL'], 4, 'forearm')
        hull_sections(guide, J['kneeL'], J['ankleL'], 4, 'shin')
    bm = bmesh.new()

    # torso column
    ti, tr = {}, []
    for i, (nm, pts) in enumerate(TORSO):
        ti[nm] = i
        tr.append(ring(bm, pts))
    tb = [bridge(bm, tr[i], tr[i + 1]) for i in range(len(tr) - 1)]
    cap(bm, list(reversed(tr[0])))
    TR = lambda nm, j: tr[ti[nm]][j]

    # head mass
    hi, hr = {}, []
    for i, (nm, pts) in enumerate(HEAD):
        hi[nm] = i
        hr.append(ring(bm, pts))
    hb = [bridge(bm, hr[i], hr[i + 1]) for i in range(len(hr) - 1)]
    HR = lambda nm, j: hr[hi[nm]][j]
    # the back of the skull: three quads onto two rear seam points
    m1, m2 = ring(bm, BACK)
    kq = hr[hi['K']]
    bm.faces.new([kq[0], kq[1], kq[2], m1])
    bm.faces.new([m1, kq[2], kq[3], m2])
    bm.faces.new([m2, kq[3], kq[4], kq[5]])
    # the neck enters the underside: the two jaw-to-seam quads under G2..K open into a 5-vertex half hole
    bmesh.ops.delete(bm, geom=[hb[hi['G2']][4], hb[hi['HD']][4]], context='FACES')
    bridge(bm, tr[-1], [HR('G2', 5), HR('G2', 4), HR('HD', 4), HR('K', 4), HR('K', 5)])

    # face plate: four quads from the brow-to-chin rim F onto the nose root (brow centre, eye plane, cheek, mouth)
    nr = [ring(bm, pts) for pts in NOSE]
    f = hr[hi['F']]
    n0 = nr[0]
    bm.faces.new([n0[0], n0[1], f[1], f[0]])
    eye_plane = bm.faces.new([n0[1], f[3], f[2], f[1]])
    bm.faces.new([n0[2], f[4], f[3], n0[1]])
    bm.faces.new([n0[3], f[5], f[4], n0[2]])
    for a, b in zip(nr, nr[1:]):
        bridge(bm, b, a)
    cap(bm, nr[-1])
    recalc_normals(bm)

    # arm: out of the whole side of the shoulder band CH..SH (front corner to back corner)
    REST[:] = []
    ORDER = ('OF', 'OM', 'OB', 'IB', 'IM', 'IF')
    for band, lo, RINGS, gen, kw in (('CH', 'CH', ARM, P.hand_three_finger, HAND), ('C', 'C', LEG, P.foot_biped, FOOT)):
        top = 'SH' if band == 'CH' else 'BT'
        ef, cur = limb(bm, [tb[ti[band]][1], tb[ti[band]][2]],
                       dict(OF=TR(top, 1), OM=TR(top, 2), OB=TR(top, 3), IB=TR(lo, 3), IM=TR(lo, 2), IF=TR(lo, 1)), RINGS)
        # the limb ends in an open 6-ring; the library part (open root) is welded onto it: digits in the base
        bmesh.ops.delete(bm, geom=ef, context='FACES')
        part = gen(open_root=True, name=gen.__name__, mats={'skin': 'skin', 'claw': 'claw'}, **kw)
        rest_ = bridge_part(part, [cur[r] for r in ORDER], bm=bm)
        if rest_ is not None:
            REST.append(rest_)

    # ear: a long blade out of the temple-to-cheekbone quad between HD and K, swept back as the side view draws it
    corners = dict(ft=HR('HD', 2), fb=HR('HD', 3), bb=HR('K', 3), bt=HR('K', 2))
    fq = hb[hi['HD']][2]
    for step in (dict(ft=(0.195, -0.010, 0.962), fb=(0.166, 0.000, 0.814), bb=(0.150, 0.072, 0.826), bt=(0.170, 0.070, 0.974)),
                 dict(ft=(0.360, 0.130, 0.950), fb=(0.352, 0.140, 0.874), bb=(0.335, 0.185, 0.910), bt=(0.343, 0.180, 0.966)),
                 dict(ft=(0.555, 0.280, 0.942), fb=(0.553, 0.282, 0.933), bb=(0.548, 0.297, 0.936), bt=(0.550, 0.296, 0.944))):
        e = extrude(bm, [fq])
        corners = {r: min(e['verts'], key=lambda q: (q.co - v.co).length) for r, v in corners.items()}
        for r, p in step.items():
            corners[r].co = Vector(p)
        fq = e['faces'][0]

    recalc_normals(bm)
    snap_seam(bm)
    say('feet: inner side at x', round(min(v.co.x for v in bm.verts if v.co.z < 0.105), 4), '(must clear the seam: two feet, not one)')
    return object_from_bm('body', bm)


def put(new, table):
    """Place the verts of a fresh loop: {rest midpoint: target}; the nearest new vert to each midpoint moves."""
    for mid, tgt in table.items():
        v = min(new, key=lambda q: (q.co - Vector(mid)).length)
        assert (v.co - Vector(mid)).length < 0.02, (mid, tuple(v.co))
        v.co = Vector(tgt)
    _fresh_all(new)


def _fresh_all(vs):
    for f in {f for v in vs for f in v.link_faces}:
        f.normal_update()


def stage2(k, body):
    """Secondary forms. Three logged loops:
    A  the grin loop: chin seam -> mouth -> cheek -> through the eye plane -> over the cranium between the crown corner
       and the temple -> rear seam. It carries the lower lip (the mouth's colour border), the smile crease, the eye's
       vertical centre line and a rounder dome.
    B  the eye-line loop: brow seam -> across the eye plane -> temple -> down the ear's front face, over its tip, up its
       back -> rear seam. It carries the socket's depth (where it crosses loop A), the temple and the ear's cup / spine.
    C  the pot-belly ring between the belt and the waist.
    Then vertex moves: brow overhang, cheekbone, jaw, pectoral corner, hump."""
    bm = edit(body)
    with k.topo(bm, 'loop', 'grin loop: lower lip and mouth border, smile crease, eye centre line, a rounder cranium'):
        A = loopcut(bm, edge_near(bm, (0.0, -0.2015, 0.735)), t=0.5)
    put(A, {
        (0.0, -0.2015, 0.735): (0.0, -0.203, 0.722),            # lower lip, centre
        (0.079, -0.1805, 0.769): (0.098, -0.166, 0.770),        # mouth corner: wide and turned up (the grin)
        (0.101, -0.164, 0.852): (0.110, -0.166, 0.842),         # under the eye: the lower lid / cheekbone top
        (0.106, -0.209, 0.929): (0.108, -0.222, 0.926),         # mid brow, pushed over the eye
        (0.109, -0.140, 0.9815): (0.122, -0.146, 0.992),        # forehead
        (0.120, -0.095, 1.023): (0.134, -0.098, 1.034),         # dome front
        (0.122, -0.0275, 1.0375): (0.136, -0.030, 1.050),       # dome top
        (0.100, 0.0425, 1.005): (0.110, 0.044, 1.014),          # back of the skull
        (0.0, 0.052, 1.0255): (0.0, 0.060, 1.030),
    })
    with k.topo(bm, 'loop', 'eye-line loop: socket depth across the eye plane, temple, the ear cup and its back spine'):
        B = loopcut(bm, edge_near(bm, (0.0, -0.226, 0.9065)), t=0.5)
    put(B, {
        (0.0, -0.226, 0.9065): (0.0, -0.234, 0.900),            # glabella knot between the brows
        (0.060, -0.210, 0.900): (0.056, -0.204, 0.892),         # inner eye corner, under the brow's inner end
        (0.109, -0.194, 0.884): (0.108, -0.176, 0.884),         # socket centre: dented in (the eye piece sits here)
        (0.147, -0.163, 0.881): (0.153, -0.152, 0.884),         # outer eye corner / temple front
        (0.1585, -0.1025, 0.905): (0.170, -0.100, 0.908),       # temple
        (0.165, -0.065, 0.930): (0.176, -0.062, 0.932),
        (0.1805, -0.005, 0.888): (0.170, 0.012, 0.890),         # ear cup, root
        (0.356, 0.135, 0.912): (0.347, 0.147, 0.912),           # ear cup, mid blade
        (0.339, 0.1825, 0.938): (0.335, 0.189, 0.938),          # ear back: a spine down the blade
        (0.160, 0.071, 0.900): (0.156, 0.078, 0.900),
    })
    with k.topo(bm, 'loop', 'pot-belly ring between the belt and the waist: the belly is a round mass, not a cone'):
        C = loopcut(bm, edge_near(bm, (0.0, -0.055, 0.550)), t=0.5)
    put(C, {
        (0.0, -0.055, 0.550): (0.0, -0.068, 0.556),
        (0.088, -0.034, 0.549): (0.096, -0.042, 0.556),
        (0.145, 0.035, 0.555): (0.156, 0.035, 0.560),
        (0.0815, 0.119, 0.585): (0.086, 0.124, 0.588),
        (0.0, 0.1315, 0.5975): (0.0, 0.136, 0.600),
    })
    mv = lambda p, d: move([vert_near(bm, p)], d)
    # brow: the rim leans over the eye (outer end up, inner end low = the scowl), cheekbone out, jaw corner out and down
    mv((0.070, -0.230, 0.932), (0.0, -0.008, -0.004))
    mv((0.142, -0.188, 0.926), (0.004, -0.008, 0.006))
    mv((0.152, -0.138, 0.836), (0.006, -0.004, -0.004))
    mv((0.100, -0.165, 0.740), (0.008, 0.0, -0.004))
    # chest: the pectoral corner forward (a ledge over the pinch), the waist corner in
    mv((0.070, -0.034, 0.648), (0.004, -0.008, 0.004))
    mv((0.076, -0.022, 0.598), (-0.006, 0.004, 0.0))
    snap_seam(bm)
    commit(body, bm)
    bm.free()


if '--lock' not in sys.argv:        # (kit: the lock dumps META as JSON; a lambda in it breaks the dump and leaves a corrupt lock)
    META['keep_valleys'] = lambda c: c.z > 0.70 and (c.y < -0.12 or abs(c.x) > 0.16)      # eye sockets, mouth, ear cups

# palette: from the concept. Values: light (belly, cream) / mid (skin, tan) / dark (leather, dark); one accent (yellow eyes)
PAL = dict(skin='#86ad4a', belly='#c8d68c', tan='#a9764f', leather='#4b3327', dark='#221614', yellow='#f4c61c',
           cream='#efe7c9')
MIR = lambda v: (-v[0], v[1], v[2])
MOUTH_C = Vector((0.039, -0.195, 0.767))


def mirrored(ob, name, grow=1.0, twist=0.0):
    """A left-side part -> one piece with a live Mirror (both flanks), materials kept. grow scales every shell
    about its own centre (a claw's sides then stand proud of the finger's instead of lying in its planes)."""
    bm = edit(ob)
    bm.transform(ob.matrix_world)
    if grow != 1.0:
        seen = set()
        for v0 in bm.verts:
            if v0 in seen:
                continue
            comp, todo = [], [v0]
            seen.add(v0)
            while todo:
                v = todo.pop()
                comp.append(v)
                for e in v.link_edges:
                    w = e.other_vert(v)
                    if w not in seen:
                        seen.add(w); todo.append(w)
            c = sum((v.co for v in comp), Vector()) / len(comp)
            tip = max(comp, key=lambda v: (v.co - c).length).co
            ax = (tip - c).normalized()
            R = Matrix.Rotation(math.radians(twist), 3, ax)
            for v in comp:
                d = v.co - c
                al = ax * d.dot(ax)
                v.co = c + (al * (1.0 if twist else grow)) + R @ ((d - al) * grow)      # twisted claws thicken, not lengthen
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
    ax, sx = abs(c.x), (1.0 if c.x >= 0 else -1.0)
    if (Vector((ax, c.y, c.z)) - MOUTH_C).length < 0.030 and n.y < -0.3:
        return 'dark'                                        # the open mouth: under the nose, down to the lower-lip loop
    if ax > 0.185 and c.z > 0.8 and (0.65 * n.x * sx - 0.76 * n.y) > 0.35:
        return 'tan'                                         # the ear's cupped front face
    if ax < 0.10 and c.y < 0 and n.y < -0.3 and 0.50 < c.z < 0.70:
        return 'belly'                                       # belly and chest: the seam-to-front-corner column
    return 'skin'


def band(name, stations, t_out, t_in, h):
    """A box-section strap swept along stations [(point, outward)], seam to seam (mirrored): the belt."""
    bm = bmesh.new()
    rs = []
    for p, o in stations:
        p, o, u = Vector(p), Vector(o).normalized(), Vector((0, 0, 1))
        rs.append(ring(bm, [p + o * t_out + u * (h / 2), p + o * t_out - u * (h / 2), p - o * t_in - u * (h / 2), p - o * t_in + u * (h / 2)]))
    for a, b in zip(rs, rs[1:]):
        bridge(bm, a, b, closed=True)
    recalc_normals(bm)
    snap_seam(bm)
    ob = object_from_bm(name, bm)
    bm.free()
    return ob


def plate(name, xs, top, bot, th):
    """A thick jagged cloth plate: columns at xs (seam first), outer-surface rows top / bot [(y, z)], thickness th (a
    y offset toward the body). Mirrored; closed along the top, the outer side and the zigzag hem."""
    bm = bmesh.new()
    T = ring(bm, [(x, y, z) for x, (y, z) in zip(xs, top)]); Bo = ring(bm, [(x, y, z) for x, (y, z) in zip(xs, bot)])
    T2 = ring(bm, [(x, y + th, z) for x, (y, z) in zip(xs[:-1], top)]) + [T[-1]]      # the outer edge thins to a wedge
    B2 = ring(bm, [(x, y + th, z) for x, (y, z) in zip(xs[:-1], bot)]) + [Bo[-1]]
    dd = lambda vs: [v for i, v in enumerate(vs) if v not in vs[:i]]
    for i in range(len(xs) - 1):
        bm.faces.new([T[i], T[i + 1], Bo[i + 1], Bo[i]])         # outer
        bm.faces.new([T2[i + 1], T2[i], B2[i], B2[i + 1]])       # inner
        bm.faces.new(dd([T[i + 1], T[i], T2[i], T2[i + 1]]))     # top
        bm.faces.new(dd([Bo[i], Bo[i + 1], B2[i + 1], B2[i]]))   # hem
    recalc_normals(bm)
    snap_seam(bm)
    ob = object_from_bm(name, bm)
    bm.free()
    return ob


def stage3(k, body):
    paint(body, {q: PAL[q] for q in ('skin', 'belly', 'tan', 'dark')}, body_rule)
    pieces = []
    one = lambda key: ({key: PAL[key]}, lambda c, n, j: key)
    # claws: what the welded library hand and foot left behind in stage 1
    for i, r in enumerate(REST):
        ob = mirrored(r, 'claws_%d' % i, grow=1.5 if i == 0 else 1.3, twist=18.0 if i == 0 else 0.0)   # the twist: no claw side lies in a finger plane
        paint(ob, *one('leather'))
        pieces.append(ob)
    # eyes (library): big yellow eyes under a scowling brow wedge, seated on the socket centre of the two stage-2 loops
    me = body.data
    ev = min(me.vertices, key=lambda q: (q.co - Vector((0.108, -0.176, 0.884))).length)
    en = Vector((0.36, -0.90, 0.10)).normalized()
    ec = ev.co + en * 0.004
    say('eye vertex', tuple(round(q, 3) for q in ev.co), tuple(round(q, 3) for q in ev.normal))
    em = dict(eye_rim='skin', eye_socket='dark', iris='yellow', pupil='dark', glint='cream', lid='skin')
    ecol = dict(iris=PAL['yellow'], glint=PAL['cream'], eye_socket=PAL['dark'], pupil=PAL['dark'])
    for sd, nm in ((1, 'eye_L'), (-1, 'eye_R')):
        f = (lambda v: v) if sd > 0 else MIR
        pieces.append(P.eye_set(f(tuple(ec)), 0.034, forward=f(tuple(en)), up=(0, 0, 1), side=sd, expression='angry',
                                aspect=1.15, pupil_size=0.42, look=(0.0, -0.1), name=nm, mats=em, colours=ecol))
    # teeth (library): big upper fangs under the lip, a short lower row on the lower-lip loop
    tm = dict(tooth='cream', gum='dark')
    tc = dict(tooth=PAL['cream'], gum=PAL['dark'])
    pieces.append(P.tooth_row((0.088, -0.166, 0.776), (-0.088, -0.166, 0.776), out=(0, -1, 0), up=(0, 0.12, -1), n=6,
                              height=0.022, bulge=0.25, profile=(0.8, 1.3, 0.7, 0.7, 1.3, 0.8), gum=True, name='teeth_up',
                              mats=tm, colours=tc))
    pieces.append(P.tooth_row((0.086, -0.168, 0.760), (-0.086, -0.168, 0.760), out=(0, -0.66, -0.75), up=(0, 0.1, 1), n=5,
                              height=0.014, bulge=0.29, profile=(1.25, 0.6, 0.8, 0.6, 1.25), gum=True, name='teeth_lo',
                              mats=tm, colours=tc))
    # belt: a thick leather strap on the HP..BL band
    belt = band('belt', [((0, -0.066, 0.462), (0, -1, 0)), ((0.097, -0.042, 0.462), (0.5, -0.87, 0)), ((0.1305, -0.002, 0.465), (0.77, -0.64, 0)),
                         ((0.164, 0.038, 0.468), (1, 0, 0)), ((0.126, 0.087, 0.478), (0.79, 0.61, 0)), ((0.088, 0.136, 0.488), (0.5, 0.87, 0)),
                         ((0, 0.152, 0.492), (0, 1, 0))], 0.024, -0.005, 0.056)   # clear of the skin: no cut
    paint(belt, *one('leather'))
    pieces.append(belt)
    # buckle: a bone frame on the belt front
    bm = bmesh.new()
    x, y0, y1, z0, z1 = 0.037, -0.0865, -0.102, 0.426, 0.498
    lo = ring(bm, [(-x, y1, z0), (x, y1, z0), (x, y0, z0), (-x, y0, z0)])
    hi = ring(bm, [(-x, y1, z1), (x, y1, z1), (x, y0, z1), (-x, y0, z1)])
    bridge(bm, lo, hi, closed=True)
    cap(bm, list(reversed(lo))); cap(bm, hi)
    recalc_normals(bm)
    inset(bm, [face_near(bm, (0, y1, 0.462))], 0.42, -0.005)
    bk = object_from_bm('buckle', bm, mirror=False)
    bm.free()
    paint(bk, {'cream': PAL['cream'], 'leather': PAL['leather']},
          lambda c, n, j: 'leather' if (abs(c.x) < 0.015 and abs(c.z - 0.462) < 0.015 and c.y < -0.09) else 'cream')
    pieces.append(bk)
    # loincloth: two thick jagged plates hanging from under the belt
    xs = (0.0, 0.034, 0.062, 0.088, 0.112)
    cf = plate('cloth_front', xs, [(-0.086, 0.470), (-0.0795, 0.470), (-0.073, 0.470), (-0.067, 0.470), (-0.054, 0.470)],
               [(-0.094, 0.215), (-0.102, 0.315), (-0.124, 0.262), (-0.110, 0.335), (-0.118, 0.300)], 0.013)
    xb = (0.0, 0.036, 0.066, 0.094, 0.120)
    cb = plate('cloth_back', xb, [(0.1735, 0.494), (0.167, 0.494), (0.162, 0.492), (0.157, 0.488), (0.126, 0.482)],
               [(0.198, 0.250), (0.196, 0.330), (0.194, 0.275), (0.188, 0.340), (0.158, 0.300)], -0.013)
    for ob in (cf, cb):
        paint(ob, *one('tan'))
        pieces.append(ob)
    return pieces


def stage4(k, body, pieces):
    rig = armature([
        ('pelvis', J['pelvis'], J['spine'], None),
        ('spine', J['spine'], J['neck'], 'pelvis'),
        ('neck', J['neck'], J['head'], 'spine'),
        ('head', J['head'], J['snout'], 'neck'),
        ('ear.L', J['earL'], J['earTipL'], 'head'),
        ('upperarm.L', J['shoulderL'], J['elbowL'], 'spine'),
        ('forearm.L', J['elbowL'], J['wristL'], 'upperarm.L'),
        ('hand.L', J['wristL'], J['handL'], 'forearm.L'),
        ('thigh.L', J['hipL'], J['kneeL'], 'pelvis'),
        ('shin.L', J['kneeL'], J['ankleL'], 'thigh.L'),
        ('foot.L', J['ankleL'], J['toeL'], 'shin.L'),
    ], roll='auto')
    skin(body, rig)
    smooth_weights(body, passes=SMOOTH)                 # the bend spreads over the joint's loops and their neighbours
    # hands (below the wrist loops) and feet (below the ankle loops) are rigid on their bone: the claws sit on them
    sd = lambda c: '.L' if c.x > 0 else '.R'
    hand = island(body, (0.30, -0.04, 0.28), lambda c: c.z < 0.338) | island(body, (-0.30, -0.04, 0.28), lambda c: c.z < 0.338)
    say('hand island', len(hand), 'verts')
    for g in body.vertex_groups:
        g.remove(sorted(hand))
    for i in hand:
        body.vertex_groups['hand' + sd(body.data.vertices[i].co)].add([i], 1.0, 'REPLACE')
    rigid(body, lambda c: ('foot' + sd(c)) if c.z < 0.105 else None)
    for p in pieces:
        n = p.name
        if 'claws' in n:
            bind(p, rig)
            end = 'hand' if n.endswith('0') else 'foot'     # each claw rigid on its own hand / foot bone
            rigid(p, lambda c: end + ('.L' if c.x > 0 else '.R'))
        elif 'eye' in n:
            bind(p, rig, bone='head')
        else:
            bind(p, rig, body=body)                         # teeth, belt, buckle and cloth ride the skin under them

    def mix(*ds):
        out = {}
        for d in ds:
            for b, r in d.items():
                o = out.get(b, (0, 0, 0))
                out[b] = (o[0] + r[0], o[1] + r[1], o[2] + r[2])
        return out

    def both(d):
        """{'thigh': (x, y, z)} -> .L and .R; the sideways (z) and twist (y) angles mirror."""
        out = {}
        for b, (x, y, z) in d.items():
            out[b + '.L'] = (x, y, z)
            out[b + '.R'] = (x, -y, -z)
        return out

    # the stance every clip stands in: legs opened into an A (the blockout review's stance; the sheet's front view, and so
    # the cage, keeps the shins close), knees a little bent, elbows out, hands forward: the concept's stalking crouch
    A, KN = SPLAY, 8.0
    STANCE = mix(both({'thigh': (KN, 0, A), 'shin': (-2 * KN, 0, 0), 'foot': (KN - 3, 0, -A),
                       'upperarm': (-6, 0, 8), 'forearm': (16, 0, 0), 'hand': (10, 0, 0)}),
                 {'spine': (4, 0, 0), 'neck': (-3, 0, 0)})
    DROP = (0, -0.019, 0)
    st = lambda *ds: mix(STANCE, *ds)
    frames_loc = lambda fs, extra=None: {f: {'pelvis': tuple(a + b for a, b in zip(DROP, (extra or {}).get(f, (0, 0, 0))))} for f in fs}

    idle = {1: st(), 13: st({'spine': (2, 0, 0), 'head': (3, 0, 5), 'ear.L': (0, 0, 6), 'ear.R': (0, 0, -3)},
                            both({'upperarm': (-3, 0, 2), 'forearm': (5, 0, 0)})),
            25: st({'spine': (3, 0, 0), 'neck': (-2, 0, 0), 'head': (-2, 0, 0)}, both({'hand': (10, 0, 0)})),
            37: st({'spine': (1.5, 0, 0), 'head': (3, 0, -5), 'ear.R': (0, 0, -6), 'ear.L': (0, 0, 3)},
                   both({'upperarm': (-3, 0, 2), 'forearm': (5, 0, 0)})), 49: st()}
    acts = {'idle': clip(rig, 'idle', idle, loc=frames_loc(idle))}

    # move: a hunched scurry. One leg's additions over the cycle (thigh, shin, foot); flat foot = the three sum to 0
    LEG = [((24, 0, 0), (-6, 0, 0), (-12, 0, 0)),          # contact in front, heel first
           ((0, 0, 0), (0, 0, 0), (0, 0, 0)),              # mid stance
           ((-22, 0, 0), (-8, 0, 0), (20, 0, 0)),          # push off, heel up
           ((22, 0, 0), (-40, 0, 0), (10, 0, 0))]          # swing: knee lifted, shin folded under
    ARMS = [((-16, 0, 0), (4, 0, 0)), ((0, 0, 0), (10, 0, 0)), ((20, 0, 0), (18, 0, 0)), ((0, 0, 0), (10, 0, 0))]
    move, mloc = {}, {}
    for i, f in enumerate((1, 7, 13, 19, 25)):
        l, r = LEG[i % 4], LEG[(i + 2) % 4]
        al, ar = ARMS[i % 4], ARMS[(i + 2) % 4]            # the arm swings against its own leg
        tw = (6, 0, -6, 0)[i % 4]
        move[f] = st({'thigh.L': l[0], 'shin.L': l[1], 'foot.L': l[2], 'thigh.R': r[0], 'shin.R': r[1], 'foot.R': r[2],
                      'upperarm.L': al[0], 'forearm.L': al[1], 'upperarm.R': ar[0], 'forearm.R': ar[1],
                      'spine': (9, tw, 0), 'neck': (-4, -tw * 0.5, 0), 'head': (4 if i % 2 else 0, 0, 0),
                      'ear.L': (0, 0, 5 if i % 2 else -2), 'ear.R': (0, 0, -5 if i % 2 else 2)})
        mloc[f] = (0, -0.004 if i % 2 else -0.024, 0)
    acts['move'] = clip(rig, 'move', move, loc=frames_loc(move, mloc))

    # attack: a pounce. Wind up low with both arms drawn back, rear up with the claws flung wide under the ears (the
    # thumbnail frame: a wide X, ears and arms spread), then lunge and rake both claws forward and down. (An arm
    # raised over the head was tried first: it passes through the ear, which spans x 0.17-0.55 at shoulder-up height.)
    Rr = lambda x, y, z: (x, -y, -z)
    wind = st({'spine': (-6, -10, 0), 'neck': (4, 0, 0), 'head': (6, 0, 0),
               'thigh.L': (12, 0, 0), 'shin.L': (-24, 0, 0), 'foot.L': (12, 0, 0),
               'thigh.R': (12, 0, 0), 'shin.R': (-24, 0, 0), 'foot.R': (12, 0, 0),
               }, both({'upperarm': (-46, 0, 18), 'forearm': (40, 0, 0), 'hand': (-20, 0, 0)}))
    apex = st({'spine': (-14, -6, 0), 'neck': (2, 0, 0), 'head': (14, 0, 0),
               'thigh.L': (-8, 0, 0), 'shin.L': (16, 0, 0), 'foot.L': (-8, 0, 0),
               'thigh.R': (10, 0, 0), 'shin.R': (-30, 0, 0), 'foot.R': (-6, 0, 0),
               }, both({'upperarm': (24, 0, 62), 'forearm': (34, 0, 0), 'hand': (-28, 0, 0)}),   # claws flung wide, under the ears
              {               'ear.L': (0, 0, 10), 'ear.R': (0, 0, -10)})
    slash = st({'spine': (26, 10, 0), 'neck': (2, 0, 0), 'head': (16, 0, 0),
                'thigh.L': (-14, 0, 0), 'shin.L': (-6, 0, 0), 'foot.L': (20, 0, 0),
                'thigh.R': (34, 0, 0), 'shin.R': (-30, 0, 0), 'foot.R': (-4, 0, 0),
                }, both({'upperarm': (58, 0, 4), 'forearm': (8, 0, 0), 'hand': (22, 0, 0)}),       # both claws rake forward
               {                'ear.L': (0, 0, -8), 'ear.R': (0, 0, 8)})
    follow = st({'spine': (30, 14, 0), 'head': (12, 0, 0),
                 'thigh.L': (-10, 0, 0), 'shin.L': (-6, 0, 0), 'foot.L': (16, 0, 0),
                 'thigh.R': (30, 0, 0), 'shin.R': (-34, 0, 0), 'foot.R': (4, 0, 0),
                 }, both({'upperarm': (30, 0, -10), 'forearm': (20, 0, 0), 'hand': (10, 0, 0)}))
    attack = {1: st(), 8: wind, 14: apex, 16: apex, 20: slash, 24: follow, 33: st()}
    aloc = {8: (0, -0.028, 0), 14: (0, 0.030, 0), 16: (0, 0.030, 0), 20: (0, -0.020, 0), 24: (0, -0.022, 0)}
    acts['attack'] = clip(rig, 'attack', attack, loc=frames_loc(attack, aloc))
    if os.environ.get('GOB_W'):
        from mathutils.bvhtree import BVHTree
        me = body.data
        tree = BVHTree.FromPolygons([v.co for v in me.vertices], [tuple(q.vertices) for q in me.polygons])
        cl = next(q for q in pieces if q.name.endswith('claws_0'))
        for v in cl.data.vertices:
            c = cl.matrix_world @ v.co
            if (c - Vector((0.195, -0.04, 0.172))).length < 0.035:
                loc, nrm, idx, d = tree.find_nearest(c)
                ws = {body.vertex_groups[g.group].name for i in me.polygons[idx].vertices for g in me.vertices[i].groups if g.weight > 0.01}
                say('NEAR', tuple(round(q, 3) for q in c), tuple(round(q, 3) for q in loc), round(d, 4), sorted(ws))
        for v in body.data.vertices:
            if v.co.z < 0.105:
                ws = [(body.vertex_groups[g.group].name, round(g.weight, 2)) for g in v.groups]
                if len(ws) != 1 or not ws[0][0].startswith('foot') or (ws[0][0].endswith('L') != (v.co.x > 0)):
                    say('FOOTW', v.index, tuple(round(q, 3) for q in v.co), ws)
        import techqa as Q
        V0, T0, P0 = Q._evaluated(body)
        C0 = Q._evaluated(cl)[0]
        rig.animation_data.action = acts['idle']
        bpy.context.scene.frame_set(13)
        V1, T1, P1 = Q._evaluated(body)
        C1 = Q._evaluated(cl)[0]
        say('TRI same', sum(1 for a, b in zip(T0, T1) if tuple(a[1]) == tuple(b[1])), len(T0), len(T1))
        tr = BVHTree.FromPolygons(V0, [t for _, t in T0], all_triangles=True)
        worst = []
        for i in range(len(C0)):
            loc, nrm, ti, d = tr.find_nearest(C0[i])
            a, b, c = T0[ti][1]
            g = (C1[i] - V1[a]).length - (C0[i] - V0[a]).length
            worst.append((round(abs(g), 4), i, tuple(round(q, 3) for q in C0[i]), tuple(round(q, 3) for q in V0[a]), [(body.vertex_groups[gg.group].name, round(gg.weight, 2)) for gg in body.data.vertices[a].groups] if a < len(body.data.vertices) else None))
        for w in sorted(worst)[-5:]:
            say('WORST', w)
        rig.animation_data.action = None
        rest(rig)
        bpy.context.scene.frame_set(1)
        for ob in [body] + [q for q in pieces if 'claws' in q.name]:
            for tgt in ((0.161, -0.084, 0.0), (0.221, -0.079, 0.023), (0.186, -0.039, 0.168)):
                v = min(ob.data.vertices, key=lambda q: (ob.matrix_world @ q.co - Vector(tgt)).length)
                say('W', ob.name, tuple(round(q, 3) for q in ob.matrix_world @ v.co), [(ob.vertex_groups[g.group].name, round(g.weight, 2)) for g in v.groups], [m.type for m in ob.modifiers], ob.parent and ob.parent.name)
    probe(rig, acts)
    shots(k, rig, acts, body, pieces)
    return rig


def rigid(ob, which):
    """Every vertex for which which(co) names a bone gets weight 1 on it and nothing else."""
    for v in ob.data.vertices:
        b = which(ob.matrix_world @ v.co)
        if not b:
            continue
        for g in ob.vertex_groups:
            g.remove([v.index])
        (ob.vertex_groups.get(b) or ob.vertex_groups.new(name=b)).add([v.index], 1.0, 'REPLACE')


def smooth_weights(body, passes=3, rate=0.5):
    """Each pass moves every vertex's weights halfway to the mean of its edge neighbours', renormalised: a knee or
    elbow bend is shared by the rings next to the joint loops instead of folding the 4 cm band between them."""
    me = body.data
    nb = [[] for _ in me.vertices]
    for e in me.edges:
        a, b = e.vertices
        nb[a].append(b); nb[b].append(a)
    W = [{g.group: g.weight for g in v.groups} for v in me.vertices]
    for _ in range(passes):
        new = []
        for i, w in enumerate(W):
            acc = {g: (1 - rate) * x for g, x in w.items()}
            for j in nb[i]:
                for g, x in W[j].items():
                    acc[g] = acc.get(g, 0.0) + rate * x / len(nb[i])
            s = sum(acc.values()) or 1.0
            new.append({g: x / s for g, x in acc.items() if x / s > 1e-3})
        W = new
    for vg in body.vertex_groups:
        vg.remove(list(range(len(me.vertices))))
    for i, w in enumerate(W):
        for g, x in w.items():
            body.vertex_groups[g].add([i], x, 'REPLACE')


SMOOTH = int(os.environ.get('GOB_SMOOTH', '3'))


def island(ob, seed, ok):
    """The vertex indices reached from the vertex nearest `seed` along edges whose ends all pass ok(co)."""
    me = ob.data
    nb = {}
    for e in me.edges:
        a, b = e.vertices
        nb.setdefault(a, []).append(b); nb.setdefault(b, []).append(a)
    s = min(me.vertices, key=lambda q: (q.co - Vector(seed)).length).index
    out, todo = {s}, [s]
    while todo:
        for j in nb.get(todo.pop(), ()):
            if j not in out and ok(me.vertices[j].co):
                out.add(j); todo.append(j)
    return out


def probe(rig, acts):
    """GOB_POSE=clip:frame,... prints where the joints are in a pose (signs, planted feet)."""
    if not os.environ.get('GOB_POSE'):
        return
    for item in os.environ['GOB_POSE'].split(','):
        nm, f = item.split(':')
        rig.animation_data.action = acts[nm]
        bpy.context.scene.frame_set(int(f))
        bpy.context.view_layer.update()
        for b in ('thigh.L', 'shin.L', 'foot.L', 'foot.R', 'forearm.L', 'hand.L', 'hand.R', 'head'):
            pb = rig.pose.bones[b]
            say('POSE', nm, f, b, tuple(round(q, 3) for q in pb.head), tuple(round(q, 3) for q in pb.tail))
    rig.animation_data.action = None
    rest(rig)
    bpy.context.scene.frame_set(1)


def shots(k, rig, acts, body, pieces):
    """GOB_SHOT=clip:frame,... renders those frames (front, hero, side) to stage4/dbg for the pose check."""
    if not os.environ.get('GOB_SHOT'):
        return
    objs = [body] + list(pieces)
    for item in os.environ['GOB_SHOT'].split(','):
        nm, f = item.split(':')
        rig.animation_data.action = acts[nm]
        bpy.context.scene.frame_set(int(f))
        bpy.context.view_layer.update()
        fr = frame_of(objs)
        shoot(k.path('stage4', 'dbg'), '%s_%s' % (nm, f), fr, views=['az000', 'hero', 'az090'], wire_views=[], colour=True, res=384, objs=objs)
    rig.animation_data.action = None
    rest(rig)
    bpy.context.scene.frame_set(1)


SPLAY = float(os.environ.get('GOB_SPLAY', '12'))


if os.environ.get('GOB_DIAG'):                 # where the tech-QA flags sit (rest centres), for NOTES
    import techqa as _Q
    _m = _Q.measure

    def _diag(body, pieces, size, rig=None, acts=None):
        out = _m(body, pieces, size, rig, acts)
        for ob in [body] + list(pieces):
            for op, cls in sorted(out[1].get(ob.name, {}).items()):
                if cls in os.environ['GOB_DIAG'].split(','):
                    c = ob.data.polygons[op].center
                    say('DIAG', ob.name, cls, op, round(c.x, 3), round(c.y, 3), round(c.z, 3))
        return out
    _Q.measure = _diag

run(META, stage1, stage2, stage3, stage4)
