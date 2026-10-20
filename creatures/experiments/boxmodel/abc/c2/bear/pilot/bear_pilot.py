import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from carve import carve_guide, hull_sections, fit_to_guide

# pilot of the cage-over-guide stage 1: the hull of reference/ is a hidden guide; the base is a quad cage
# box-modelled on J (rings, bridges, extrusions), fitted to the guide, and that cage is what gets locked.

# the skeleton (metres, faces -Y, left flank +X, feet on z = 0), read off the reference side and front views
J = dict(
    pelvis=(0.0, 0.60, 0.62), spine=(0.0, 0.10, 0.66), neck=(0.0, -0.36, 0.68),
    head=(0.0, -0.58, 0.60), snout=(0.0, -0.845, 0.47),
    tail0=(0.0, 0.74, 0.64), tail1=(0.0, 0.812, 0.63),
    shoulderL=(0.235, -0.05, 0.60), elbowL=(0.235, -0.035, 0.25), wristL=(0.23, -0.07, 0.11),
    pawL=(0.228, -0.30, 0.03),
    hipL=(0.235, 0.58, 0.60), kneeL=(0.235, 0.62, 0.285), hockL=(0.23, 0.71, 0.12),
    toeL=(0.228, 0.50, 0.03),
)
PLAN = dict(spine=['pelvis', 'spine', 'neck', 'head', 'snout'],
            limbs=dict(fore=['shoulderL', 'elbowL', 'wristL', 'pawL'], hind=['hipL', 'kneeL', 'hockL', 'toeL']),
            extra=[['tail0', 'tail1']])
META = dict(creature='bear', model='opus', cage=True, J=J, plan=PLAN, intended={})


def sec(y, zt, zb, w, zw=None, up=None, lo=None):
    """A half section, top seam -> bottom seam: 5 vertices, so the whole section is 8-sided.
    up / lo: the upper and lower corner as (x, z); defaults make a keeled, flat-backed octagon."""
    h = zt - zb
    zw = zw if zw is not None else zb + 0.45 * h
    up = up or (0.55 * w, zt - 0.10 * h)
    lo = lo or (0.50 * w, zb + 0.08 * h)
    return [(0.0, y, zt), (up[0], y, up[1]), (w, y, zw), (lo[0], y, lo[1]), (0.0, y, zb)]


# nose -> tail
STATIONS = [
    ('H0', sec(-0.848, 0.495, 0.450, 0.035, up=(0.028, 0.492), lo=(0.028, 0.453))),      # nose tip
    ('H1', sec(-0.800, 0.535, 0.405, 0.058, up=(0.045, 0.528), lo=(0.045, 0.412))),      # muzzle
    ('H2', sec(-0.745, 0.585, 0.388, 0.082, up=(0.062, 0.575), lo=(0.060, 0.398))),      # muzzle at the stop
    ('H3', sec(-0.700, 0.675, 0.400, 0.138, zw=0.53, up=(0.092, 0.655))),                # brow
    ('H4', sec(-0.620, 0.740, 0.412, 0.198, zw=0.55, up=(0.125, 0.722))),                # skull, cheek
    ('H5', sec(-0.530, 0.780, 0.420, 0.208, zw=0.58, up=(0.130, 0.762))),                # back of skull
    ('T0', sec(-0.430, 0.835, 0.405, 0.212, zw=0.60)),                                    # neck
    ('TN', sec(-0.360, 0.875, 0.375, 0.275, zw=0.60)),                                    # neck base
    ('T1', sec(-0.290, 0.915, 0.335, 0.355, zw=0.56)),                                    # chest front
    ('T2', sec(-0.185, 0.997, 0.292, 0.368, zw=0.47, up=(0.19, 0.90), lo=(0.105, 0.315))),   # fore leg front, hump
    ('T3', sec(-0.040, 0.990, 0.285, 0.350, zw=0.46, up=(0.19, 0.895), lo=(0.100, 0.310))),  # hump, fore leg
    ('T4', sec(0.105, 0.905, 0.285, 0.298, zw=0.46, up=(0.17, 0.83), lo=(0.105, 0.310))),    # behind the shoulder
    ('T5', sec(0.270, 0.872, 0.268, 0.290, zw=0.55)),                                     # waist
    ('T6', sec(0.440, 0.866, 0.305, 0.365, zw=0.52, up=(0.19, 0.80), lo=(0.105, 0.345))),    # hind leg front, hip
    ('T7', sec(0.600, 0.810, 0.350, 0.362, zw=0.50, up=(0.18, 0.745), lo=(0.105, 0.375))),   # haunch
    ('T8', sec(0.765, 0.700, 0.440, 0.270, zw=0.52, up=(0.14, 0.655), lo=(0.100, 0.455))),    # rump
    ('T9', sec(0.792, 0.715, 0.585, 0.075)),                                              # tail root
    ('T10', sec(0.822, 0.680, 0.600, 0.055)),                                             # tail tip
]


def hexring(cx, cy, z, rx, ry, tilt=0.0):
    return dict(OF=(cx + 0.8 * rx, cy - ry, z + tilt), OM=(cx + rx, cy, z), OB=(cx + 0.8 * rx, cy + ry, z - tilt),
                IB=(cx - 0.8 * rx, cy + ry, z - tilt), IM=(cx - rx, cy, z), IF=(cx - 0.8 * rx, cy - ry, z + tilt))


def leg(bm, faces, cur, rings):
    """Extrude a 2-quad region down ring by ring (a 6-sided limb); cur maps role -> boundary vert.
    Returns the last faces and every ring's vertices."""
    out = []
    for rg in rings:
        r = extrude(bm, faces)
        nv = r['verts']
        m = {role: min(nv, key=lambda q: (q.co - v.co).length) for role, v in cur.items()}
        for role, p in hexring(*rg).items():
            m[role].co = Vector(p)
        faces, cur = r['faces'], m
        out.append(list(m.values()))
    return faces, out


def stage1(k):
    guide = carve_guide(k)
    if os.environ.get('BEAR_SECTIONS'):
        hull_sections(guide, (0, -0.85, 0.6), (0, 0.85, 0.6), 18, 'spine')
        hull_sections(guide, J['elbowL'], J['wristL'], 4, 'forearm')
        hull_sections(guide, J['kneeL'], J['hockL'], 4, 'shin')
    bm = bmesh.new()
    idx, rings = {}, []
    for i, (nm, pts) in enumerate(STATIONS):
        idx[nm] = i
        rings.append(ring(bm, pts))
    # head and neck rings onto the guide, each in its own plane (the legs and the leg stations are placed by hand:
    # the hull fuses leg and flank there, and the side view wins over the plan view for the legs)
    fit = fit_to_guide([rings[idx[n]] for n in ('H1', 'H2', 'H3', 'H4', 'H5', 'T5')], guide, max_move=0.025)
    say('fit_to_guide (moved, capped):', fit)
    bands = [bridge(bm, rings[i], rings[i + 1]) for i in range(len(rings) - 1)]
    cap(bm, list(reversed(rings[0])))
    cap(bm, rings[-1])
    R = lambda nm, j: rings[idx[nm]][j]

    # fore leg: out of the lower flank between T2..T4. Loops: two at the elbow, two at the wrist, paw, sole
    fore = [(0.235, -0.040, 0.280, 0.132, 0.145),
            (0.232, -0.045, 0.220, 0.126, 0.138),
            (0.230, -0.060, 0.140, 0.108, 0.125),
            (0.230, -0.075, 0.085, 0.104, 0.122),
            (0.228, -0.165, 0.050, 0.118, 0.170, 0.028),
            (0.228, -0.172, 0.000, 0.120, 0.170)]
    leg(bm, [bands[idx['T2']][2], bands[idx['T3']][2]],
        dict(OF=R('T2', 2), OM=R('T3', 2), OB=R('T4', 2), IB=R('T4', 3), IM=R('T3', 3), IF=R('T2', 3)), fore)

    # hind leg: out of the lower flank between T6..T8. Two loops at the stifle, two at the hock, paw, sole
    hind = [(0.235, 0.615, 0.310, 0.132, 0.180),
            (0.232, 0.650, 0.255, 0.126, 0.178),
            (0.230, 0.693, 0.155, 0.108, 0.155),
            (0.230, 0.710, 0.090, 0.104, 0.140),
            (0.228, 0.670, 0.045, 0.118, 0.180),
            (0.228, 0.650, 0.000, 0.120, 0.175)]
    leg(bm, [bands[idx['T6']][2], bands[idx['T7']][2]],
        dict(OF=R('T6', 2), OM=R('T7', 2), OB=R('T8', 2), IB=R('T8', 3), IM=R('T7', 3), IF=R('T6', 3)), hind)

    # round ear: a base block raised out of the skull's upper plane between H4 and H5, then two steps up
    corners = dict(fi=R('H4', 1), fo=R('H4', 2), bo=R('H5', 2), bi=R('H5', 1))
    f = bands[idx['H4']][1]
    up = lambda v, d: tuple(v.co + Vector(d))          # the inner base corners sit just outside the fitted skull corners
    for step in (dict(fi=up(corners['fi'], (0.012, 0.012, 0.016)), fo=(0.212, -0.607, 0.700), bo=(0.212, -0.553, 0.705),
                      bi=up(corners['bi'], (0.012, -0.022, 0.012))),
                 dict(fi=(0.126, -0.606, 0.782), fo=(0.232, -0.606, 0.752), bo=(0.232, -0.552, 0.756), bi=(0.126, -0.552, 0.788)),
                 dict(fi=(0.150, -0.600, 0.806), fo=(0.216, -0.600, 0.794), bo=(0.216, -0.560, 0.796), bi=(0.150, -0.560, 0.808))):
        e = extrude(bm, [f])
        corners = {r: min(e['verts'], key=lambda q: (q.co - v.co).length) for r, v in corners.items()}
        for r, p in step.items():
            corners[r].co = Vector(p)
        f = e['faces'][0]

    # eye: a loop inside the brow-cheek plane between H3 and H4 (the socket), pushed in a little
    inset(bm, [bands[idx['H3']][1]], 0.38, -0.006)

    # planarize() was tried on the torso bands (round 4): 24 faces settled into 17 facets, the side IoU fell
    # 0.972 -> 0.963 and a neck ring left its plane (3 loops -> 2). The rings already give planar bands; not used.

    snap_seam(bm)
    return object_from_bm('body', bm)


run(META, stage1)
