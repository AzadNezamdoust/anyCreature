import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from carve import part_guide, part_rings, fit_to_guide

# Stage 1 = a quad cage on the PART guide (carve.part_guide). c3: every ring is sized by part_rings and slid onto
# the guide; the torso is a 14-sided tube of near-square quads, the limbs are 8-sided rounded boxes out of a 2 x 2
# patch of flank faces (the patch boundary is the shoulder / hip loop), the muzzle grows out of the face plane
# of the cranium, limb ends close on the sole with four quads. No toes, no eye, no pieces.

# the skeleton (metres, faces -Y, left flank +X, feet on z = 0), read off the reference side and front views.
# Elbow / knee and wrist / hock sit low on a plantigrade column leg: their loops are below the armpit and groin.
J = dict(
    pelvis=(0.0, 0.60, 0.62), spine=(0.0, 0.10, 0.66), neck=(0.0, -0.43, 0.67),
    head=(0.0, -0.58, 0.60), snout=(0.0, -0.845, 0.47),
    tail0=(0.0, 0.74, 0.66), tail1=(0.0, 0.812, 0.64),
    shoulderL=(0.24, -0.05, 0.60), elbowL=(0.238, -0.045, 0.25), wristL=(0.232, -0.075, 0.115),
    pawL=(0.228, -0.265, 0.04),
    hipL=(0.24, 0.60, 0.60), kneeL=(0.238, 0.64, 0.245), hockL=(0.232, 0.71, 0.12),
    toeL=(0.228, 0.53, 0.04),
)
PLAN = dict(spine=['pelvis', 'spine', 'neck', 'head', 'snout'],
            limbs=dict(fore=['shoulderL', 'elbowL', 'wristL', 'pawL'], hind=['hipL', 'kneeL', 'hockL', 'toeL']),
            extra=[])                                   # the stub tail is a stage-3 piece; the rump carries a bump
META = dict(creature='bear', model='opus', cage=True, J=J, plan=PLAN, intended={})

# half-ring angles from the top seam: columns 0-3 the back (two loops each side of the spine over the hump), 4 the
# top of the shoulder / hip loop (up on the back, above the joint), 5 the flank loop (it runs through both limb
# roots and along the flank between them), 6 the armpit / groin line, 7 the belly seam.
NOSE = 1.3                                              # the last muzzle ring x this: a blunt nose block, not a point
EVEN = [0, 26, 52, 77, 103, 128, 154, 180]
NECK = [0, 24, 48, 72, 98, 126, 154, 180]
LEGA = [0, 16, 32, 48, 64, 108, 164, 180]
LEGH = [0, 16, 32, 46, 59, 112, 164, 180]
MID = [0, 22, 44, 66, 92, 124, 157, 180]
SPINE = [
    ('H2', 'head', ('t', 0.38), EVEN), ('H1', 'head', ('t', 0.19), EVEN), ('H0', 'head', ('t', 0.0), EVEN),
    # the neck: three rings off the guide's neck part, evenly spaced; N2 is the ruff (half the step from the neck
    # to the shoulders), so the head grows out of a soft collar and not a ledge
    ('K', 'neck', ('t', 0.68), EVEN, 0.0, dict(width=0.385)), ('N2', 'neck', ('t', 0.33), NECK, 0.15, dict(width=0.52)),
    ('N1', 'torso', ('y', -0.36), NECK, -0.40, dict(width=0.64)),     # the shoulder fronts: wide low, beside the neck
    # (the torso part is tucked between the leg masses at A, B and E: the rings start at the body's width and slide in)
    ('A', 'torso', ('y', -0.21), LEGA, 0.0, dict(width=0.56)), ('B', 'torso', ('y', -0.025), LEGA, 0.0, dict(width=0.60)), ('C', 'torso', ('y', 0.165), LEGA),
    ('M', 'torso', ('y', 0.28), MID),
    ('D', 'torso', ('y', 0.385), LEGH), ('E', 'torso', ('y', 0.565), LEGH, 0.0, dict(width=0.56, centre=(0.0, 0.565, 0.56), depth=0.52)),
    # the rump, by hand off the side and plan outlines: 4 = the hip loop's top-back corner, 5 = the back of the thigh
    ('F', dict(centre=(0.0, 0.72, 0.58), width=0.55, depth=0.33, p=2.4,
               xyz=[(0.0, 0.700, 0.748), (0.070, 0.704, 0.745), (0.140, 0.704, 0.737), (0.205, 0.700, 0.722),
                    (0.258, 0.690, 0.700), (0.268, 0.800, 0.500), (0.105, 0.775, 0.400), (0.0, 0.745, 0.430)]), None, LEGA),
]
NOFIT = ('N2', 'K', 'F')                         # the neck is sized by the sheet's plan (the guide's neck is blended fat)
HOLES = {('A', 'B'), ('B', 'C'), ('D', 'E'), ('E', 'F')}            # columns 4 and 5 there are the limb roots

# limb rings below the root loop: (z of the ring centre, z offsets per vertex k0..k7 or a tilt, explicit section or None, width scale)
# k: 0 front, 1 front-outer, 2 outer, 3 back-outer, 4 back, 5 back-inner, 6 inner, 7 front-inner
# the ring under the root loop follows its shape (high outside, low at the armpit), so the closing quads keep one height
UP = [-0.05, 0.12, 0.16, 0.12, -0.05, -0.14, -0.15, -0.14]           # the ring round the root: the shoulder / thigh mass
UP2 = [0.0, 0.03, 0.045, 0.03, 0.0, -0.025, -0.03, -0.025]           # the upper elbow / knee ring (a tight pair with the next:
#                                                                      the faces that close in a bend stay small)
PAW = [0.018, 0.012, 0.0, 0.0, 0.0, 0.0, 0.0, 0.012]                 # the paw block: its top rises a little to the knuckles
LIMBS = dict(
    fore=dict(rings=[(0.46, UP, None, 1.0), (0.295, UP2, None, 1.0), (0.215, 0.0, None, 1.0), (0.145, 0.0, None, 0.93),
                     (0.09, 0.0, None, 0.93), (0.055, PAW, (0.230, -0.130, 0.250, 0.345), 1.0)],
              sole=(0.230, -0.133, 0.240, 0.335), root=('A', 'B', 'C')),
    hind=dict(rings=[(0.46, UP, None, 1.0), (0.295, UP2, None, 1.0, 1.08), (0.215, 0.0, None, 1.0, 1.07), (0.15, 0.0, None, 0.93),
                     (0.095, 0.0, None, 0.93), (0.050, 0.0, (0.230, 0.683, 0.250, 0.325), 1.0)],
              sole=(0.230, 0.681, 0.240, 0.315), root=('D', 'E', 'F')),
)


def sgnpow(v, e):
    return math.copysign(abs(v) ** e, v)


def half_ring(s, angles):
    """A half ring (top seam -> bottom seam) on a part_rings station: a superellipse of the station's width,
    depth and exponent in its own section plane."""
    c, u, w, e = Vector(s['centre']), Vector(s['u']), Vector(s['w']), 2.0 / s['p']
    out = []
    for a in angles:
        sa, ca = math.sin(math.radians(a)), math.cos(math.radians(a))
        q = c + u * (0.5 * s['width'] * abs(sa) ** e) + w * (0.5 * s['depth'] * sgnpow(ca, e))
        if a in (0, 180):
            q.x = 0.0
        out.append(q)
    return out


def limb_ring(c, W, D, dz, p=2.0):
    """An 8-sided limb ring round c: width W along X, depth D along Y; dz: a tilt (outer side up) or 8 offsets."""
    e = 2.0 / p
    out = []
    for i in range(8):
        th = math.radians(45 * i)
        fx, fy = sgnpow(math.sin(th), e), sgnpow(math.cos(th), e)
        z = dz[i] if isinstance(dz, (list, tuple)) else dz * fx
        out.append(Vector((c[0] + 0.5 * W * fx, c[1] - 0.5 * D * fy, c[2] + z)))
    return out


def stage1(k):
    guide = part_guide(k)
    GP = k.guide_parts
    ST = {p: part_rings(GP, p, 121, ends=True) for p in ('torso', 'neck', 'head', 'fore', 'hind')}

    if os.environ.get('BEAR_DIAG'):
        for p_ in GP:
            if isinstance(GP[p_], dict) and 'stations' in GP[p_]:
                part_rings(GP, p_, label=p_)
                say('joints', p_, GP[p_].get('joints'), GP[p_].get('kind'), [k_ for k_ in GP[p_] if k_ != 'stations'])
        part_rings(GP, 'fore', 25, ends=True, label='fore25'); part_rings(GP, 'hind', 25, ends=True, label='hind25')
        part_rings(GP, 'head', 13, ends=True, label='head13'); part_rings(GP, 'torso', 15, ends=True, label='torso15'); part_rings(GP, 'neck', 5, ends=True, label='neck5')

    def station(part, how):
        kind, val = how
        if kind == 't':
            return min(ST[part], key=lambda s: abs(s['t'] - val))
        return min(ST[part], key=lambda s: abs(s['centre'][1] - val))

    bm = bmesh.new()
    R, S = {}, {}
    for name, part, how, ang, *opt in SPINE:
        if isinstance(part, dict):
            s = dict(dict(u=(1.0, 0.0, 0.0), w=(0.0, 0.0, 1.0), t=0.0, src='sheet'), **part)
        else:
            s = dict(station(part, how))
            if len(opt) > 1:
                s.update(opt[1])
        S[name] = s
        say('ring %s: t %.2f centre (%.3f, %.3f, %.3f) width %.3f depth %.3f p %.2f %s'
            % (name, s['t'], *s['centre'], s['width'], s['depth'], s['p'], s['src']))
        pts = half_ring(s, ang)
        if 'xyz' in s:
            pts = [Vector(q) for q in s['xyz']]
        for q in pts:
            q.y += (opt[0] if opt else 0.0) * (q.z - s['centre'][2])
        R[name] = [None if (name in ('B', 'E') and j == 5) else bm.verts.new(q) for j, q in enumerate(pts)]
    # the spine rings slide onto the guide in their own planes (the shoulder and haunch masses come with it)
    for name in R:
        if name in NOFIT:
            continue
        # A, B, E: the guide's torso is a narrow ridge between the leg masses there (KIT), so the back of these rings
        # (columns 0-4: the hump, the croup) keeps its drawn dome and only the flank and belly slide on
        fit_to_guide([v for j, v in enumerate(R[name]) if v is not None and (j > 4 or name not in ('A', 'B', 'E'))], guide,
                     max_move=0.08 if name in ('A', 'B', 'E', 'N1') else 0.05)
    for v in R['H0']:                                   # the sheet's skull is 2 cm shallower than the guide here
        v.co.z = S['H0']['centre'][2] + 0.94 * (v.co.z - S['H0']['centre'][2])
        v.co.x *= 1.04                                  # ... and its cheeks a little wider (0.46)
    # the shoulder fronts stand beside the neck, low (the sheet's plan is 0.65 wide one ring behind the head): the
    # ruff ring N2 is narrow on top and wide low, the step down to the neck half the old wall's
    for name, fx in (('N1', (1.0, 1.0, 1.0, 1.04, 1.10, 1.12, 1.0, 1.0)), ('N2', (1.0, 1.0, 1.0, 0.90, 1.24, 1.36, 1.25, 1.0)),
                     ('K', (1.0, 1.0, 1.0, 1.0, 1.05, 1.08, 1.05, 1.0))):
        for v, f in zip(R[name], fx):
            v.co.x *= f
    R['K'][3].co.y += 0.024                             # the hollow behind the cheek
    R['N2'][3].co.y += 0.012                            # (the plan's neck row, y -0.505, stays clear of the shoulder fronts)
    # big planes on the skull: the corners of the three cranium rings pushed out to a boxier section (the extents stay)
    for name in ('H0', 'H1', 'H2'):
        c, w = Vector(S[name]['centre']), Vector(S[name]['w'])
        for j, (fx, fw) in ((1, (1.12, 1.03)), (2, (1.05, 1.09)), (5, (1.05, 1.09)), (6, (1.12, 1.03))):
            v = R[name][j]
            dw = (v.co - c).dot(w)
            v.co += w * (dw * (fw - 1.0))
            v.co.x *= fx
    # armpit / groin line: the inner edge of the limb root, on the chest underside just inside the leg
    for name, zmin in (('A', 0.345), ('B', 0.33), ('C', 0.325), ('D', 0.325), ('E', 0.335), ('F', 0.36)):
        v = R[name][6]
        v.co.x = 0.105
        v.co.z = max(v.co.z, zmin)
    for name in R:
        say('ring %s pts: %s' % (name, ' '.join('(%.3f %.3f %.3f)' % tuple(v.co) if v else '-' for v in R[name])))
    names = [n for n, *_ in SPINE]
    for a, b in zip(names, names[1:]):
        for j in range(7):
            if (a, b) in HOLES and j in (4, 5):
                continue
            bm.faces.new([R[a][j], R[a][j + 1], R[b][j + 1], R[b][j]])

    # rump: a cap of five quads (half), four seam vertices; the top one stands out a little (where the stub tail sits)
    F = R['F']
    cs = [bm.verts.new(q) for q in ((0.0, 0.795, 0.675), (0.0, 0.776, 0.620), (0.0, 0.762, 0.555), (0.0, 0.750, 0.490))]
    bm.faces.new([F[0], F[1], F[2], cs[0]]); bm.faces.new([cs[0], F[2], F[3], cs[1]]); bm.faces.new([cs[1], F[3], F[4], cs[2]])
    bm.faces.new([cs[2], F[4], F[5], cs[3]]); bm.faces.new([cs[3], F[5], F[6], F[7]])

    # face: the cranium ends in a face plane (brow row, chin row); the muzzle is a 10-sided block out of its middle
    H2 = R['H2']
    sm = station('head', ('t', 0.50))
    c, w = Vector(sm['centre']), Vector(sm['w'])
    c1 = bm.verts.new(c + w * (0.5 * sm['depth'])); c3 = bm.verts.new(c - w * (0.5 * sm['depth']))
    c1.co.x = c3.co.x = 0.0
    fit_to_guide([c1, c3], guide, max_move=0.03, mode='nearest')
    hw = Vector(S['H2']['w'])
    H2[0].co += hw * 0.016; H2[1].co += hw * 0.016      # the brow stands over the muzzle root: a stop, not one wedge
    c1.co -= hw * 0.010
    bm.faces.new([H2[0], H2[1], H2[2], c1]); bm.faces.new([c3, H2[5], H2[6], H2[7]])
    prev = [c1, H2[2], H2[3], H2[4], H2[5], c3]
    for t, k_ in ((0.66, 1.0), (0.90, NOSE)):
        s = dict(station('head', ('t', t)))
        s['width'] *= k_; s['depth'] *= k_
        cur = [bm.verts.new(q) for q in half_ring(s, [0, 36, 72, 108, 144, 180])]
        if k_ == 1.0:
            fit_to_guide(cur, guide, max_move=0.03)
        bridge(bm, prev, cur)
        prev = cur
    bm.faces.new([prev[0], prev[1], prev[4], prev[5]]); bm.faces.new([prev[1], prev[2], prev[3], prev[4]])   # a blunt nose block

    # limbs: the 2 x 2 patch boundary is the root loop (over the joint); rings sized by part_rings, slid onto the guide
    for lname, L in LIMBS.items():
        a, b, c_ = (R[n] for n in L['root'])
        prev = [a[5], a[4], b[4], c_[4], c_[5], c_[6], b[6], a[6]]
        chain = PLAN['limbs'][lname]
        P = [Vector(J[n]) for n in chain]
        tw = ((P[1] - P[0]).length + (P[2] - P[1]).length) / sum((q - p).length for p, q in zip(P, P[1:]))
        upper = [s for s in ST[lname] if 0.0 <= s['t'] <= tw and s['centre'][2] > 0.05]
        for zc, dz, sec, kx, *ky in L['rings']:
            if sec is None:
                s = min(upper, key=lambda q: abs(q['centre'][2] - zc))
                cen, W, D, p = (s['centre'][0], s['centre'][1], zc), s['width'], s['depth'], max(s['p'], 2.6)
                say('%s ring z %.3f: t %.2f centre (%.3f, %.3f) width %.3f depth %.3f p %.2f %s' % (lname, zc, s['t'], *cen[:2], W, D, p, s['src']))
            else:
                cen, W, D, p = (sec[0], sec[1], zc), sec[2], sec[3], 3.0
            cur = [bm.verts.new(q) for q in limb_ring(cen, W, D, dz, p)]
            mv = fit_to_guide(cur, guide, max_move=0.05, centre=cen) if sec is None else (0, 0)   # the paw is read off the sheet
            for v in cur:
                v.co.x = cen[0] + kx * (v.co.x - cen[0])
                v.co.y = cen[1] + (ky[0] if ky else 1.0) * (v.co.y - cen[1])
                if sec is not None:                     # a paw is broad at the toes and narrow at the heel
                    v.co.x = cen[0] + (v.co.x - cen[0]) * (0.92 - 0.16 * (v.co.y - cen[1]) / D)
            say('  fit', mv, 'extent x %.3f y %.3f' % (max(v.co.x for v in cur) - min(v.co.x for v in cur),
                                                         max(v.co.y for v in cur) - min(v.co.y for v in cur)))
            bridge(bm, prev, cur, closed=True)
            prev = cur
        sx, sy, W, D = L['sole']
        cur = [bm.verts.new(q) for q in limb_ring((sx, sy, 0.0), W, D, 0.0, 3.0)]
        for v in cur:
            v.co.x = sx + (v.co.x - sx) * (0.92 - 0.16 * (v.co.y - sy) / D)
        cur[3].co.y -= 0.035; cur[5].co.y -= 0.035          # a round heel (and its two poles clear of the wrist / hock band)
        bridge(bm, prev, cur, closed=True)
        mid = bm.verts.new((sx, sum(v.co.y for v in cur) / 8, 0.0))
        for i in (0, 2, 4, 6):
            bm.faces.new([cur[i], cur[i + 1], cur[(i + 2) % 8], mid])

    if os.environ.get('BEAR_DIAG'):
        for y0 in (-0.48, -0.495, -0.505, -0.515, -0.58):
            hits = []
            for e in bm.edges:
                a, b = e.verts[0].co, e.verts[1].co
                if (a.y - y0) * (b.y - y0) < 0:
                    q = a.lerp(b, (y0 - a.y) / (b.y - a.y))
                    hits.append((round(q.x, 3), round(q.z, 3)))
            say('DIAG plan y', y0, sorted(hits)[-3:])
    snap_seam(bm)
    return object_from_bm('body', bm)


if os.environ.get('BEAR_ROM'):                          # diagnostic only: where the range-of-motion folds are
    import techqa as _Q
    _m = _Q.measure

    def _measure(body, pieces, size, rig=None, acts=None):
        out = _m(body, pieces, size, rig, acts)
        try:
            fl = out[1]
            say('ROMDIAG type', type(fl), (list(fl.keys())[:3] if isinstance(fl, dict) else ''))
            d = fl.get(body.name, fl) if isinstance(fl, dict) else {}
            for pi, kinds in (d.items() if isinstance(d, dict) else []):
                if 'flip' in str(kinds):
                    c = body.data.polygons[pi].center
                    say('ROMDIAG flip poly %d at (%.2f %.2f %.2f) area %.4f' % (pi, c.x, c.y, c.z, body.data.polygons[pi].area))
        except Exception as e:
            say('ROMDIAG failed', repr(e))
        return out
    _Q.measure = _measure

run(META, stage1)
