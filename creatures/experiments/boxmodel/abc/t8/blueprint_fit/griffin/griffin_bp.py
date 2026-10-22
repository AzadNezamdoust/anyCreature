"""Griffin typed blueprint tables (bpy-free). The hand-read baseline numbers (t7x/zoo/griffin r23 lock) and
the loader that replaces them with the fitted blueprint (blueprint_fit.json) when present."""
import math, json, os
def dens(p):
    """The 2x density rule: a point on the straight midpoint of every span of the 7-point profile (13 points),
    so the added rings of vertices lie on the flat planes of the base section."""
    out = []
    for a, b in zip(p, p[1:]):
        out += [a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)]
    return out + [p[-1]]


# half-ring profiles, top seam -> bottom seam: (x as a fraction of W, h as a fraction of T / B)
BODY = dens([(0, 1), (0.55, 0.95), (0.9, 0.62), (1, 0.12), (0.94, -0.38), (0.62, -0.82), (0, -1)])
HAUNCH = dens([(0, 1), (0.5, 0.95), (0.84, 0.66), (0.98, 0.18), (1.04, -0.32), (0.76, -0.8), (0, -1)])   # r10: low wide haunch
CHEST = dens([(0, 1), (0.55, 0.95), (0.9, 0.62), (1, 0.1), (0.95, -0.4), (0.6, -0.85), (0, -1)])
NECK = dens([(0, 1), (0.6, 0.93), (0.93, 0.55), (1, 0.0), (0.93, -0.5), (0.6, -0.88), (0, -1)])
HEAD = dens([(0, 1), (0.45, 0.96), (0.82, 0.76), (1, 0.32), (1, -0.15), (0.78, -0.66), (0, -1)])   # r8: flat cheek plane, domed crown
BEAK = dens([(0, 1), (0.6, 0.86), (0.95, 0.42), (1, -0.08), (0.82, -0.55), (0.45, -0.9), (0, -1)])
TAIL = dens([(0, 1), (0.6, 0.85), (0.95, 0.4), (1, -0.05), (0.92, -0.45), (0.55, -0.85), (0, -1)])


def tb(nm, top, bot, W, prof):
    """A section from its top and bottom seam points (y, z) read off reference/side.png."""
    (yt, zt), (yb, zb) = top, bot
    c = ((yt + yb) / 2, (zt + zb) / 2)
    h = math.hypot(yt - yb, zt - zb) / 2
    a = math.degrees(math.atan2(yt - yb, zt - zb))
    return (nm, c, round(a, 2), h, h, W, prof)


def ax(nm, c, d, h, W, prof=TAIL):
    """A tail section from its centre and the tail's direction (y, z) in the side view."""
    l = math.hypot(*d)
    py, pz = d[1] / l, -d[0] / l
    if pz < 0:
        py, pz = -py, -pz
    return tb(nm, (c[0] + py * h, c[1] + pz * h), (c[0] - py * h, c[1] - pz * h), W, prof)


# the tail stem (centre y, z, half size), tuft end -> root; the tuft piece hides the end
TAILC = [('T0', 0.885, 0.395, 0.034), ('T1', 0.835, 0.432, 0.038), ('T2', 0.785, 0.47, 0.042),
         ('T3', 0.735, 0.515, 0.047), ('T4', 0.69, 0.565, 0.053), ('T5', 0.65, 0.62, 0.062)]


def tail_secs():
    out = []
    for i, (nm, y, z, h) in enumerate(TAILC):
        p = TAILC[max(0, i - 1)]; q = TAILC[min(len(TAILC) - 1, i + 1)]
        out.append(ax(nm, (y, z), (p[1] - q[1], p[2] - q[2]), h, h * 1.05))
    return out


# r15: the nape's top seam bulges back (sheet ruff), its stations ~0.055 apart (thin quads at the back of the neck)
# the spine loft, tail stem -> beak tip. Torso stations 0.065-0.07 apart (about one face width: near-square quads);
# the neck stations fan from the back of the ruff to the chest front; the head stations fan over the crown
SECS = [
    *tail_secs()[:-1],
    tb('T5', (0.688, 0.668), (0.635, 0.556), 0.075, TAIL),            # r7: root ring tilted back (no fold under the root)
    tb('R0t', (0.615, 0.738), (0.605, 0.568), 0.13, BODY),           # r13: wider, underside on the stem's line (knife fold)
    tb('R0', (0.575, 0.81), (0.575, 0.562), 0.19, HAUNCH),
    tb('R0b', (0.52, 0.875), (0.52, 0.555), 0.24, HAUNCH),          # rump
    tb('R1', (0.45, 0.92), (0.45, 0.555), 0.265, HAUNCH),           # hind region rear ring
    tb('R1b', (0.38, 0.945), (0.38, 0.56), 0.27, HAUNCH),
    tb('R2', (0.31, 0.96), (0.31, 0.57), 0.262, HAUNCH),
    tb('R2b', (0.24, 0.968), (0.24, 0.585), 0.24, BODY),          # hind region front ring (groin)
    tb('W0', (0.17, 0.972), (0.17, 0.592), 0.224, BODY),
    tb('W0b', (0.10, 0.976), (0.10, 0.588), 0.218, BODY),
    tb('M0', (0.03, 0.98), (0.03, 0.578), 0.216, BODY),
    tb('M0b', (-0.04, 0.985), (-0.04, 0.566), 0.218, BODY),
    tb('M1', (-0.11, 0.992), (-0.11, 0.554), 0.222, BODY),
    tb('M1b', (-0.18, 1.0), (-0.18, 0.543), 0.228, BODY),
    tb('M2', (-0.25, 1.01), (-0.25, 0.535), 0.236, BODY),
    tb('M2b', (-0.32, 1.022), (-0.32, 0.529), 0.245, BODY),
    tb('C0', (-0.38, 1.036), (-0.38, 0.525), 0.252, CHEST),
    tb('C0b', (-0.44, 1.052), (-0.44, 0.522), 0.258, CHEST),       # fore region rear ring
    tb('C1', (-0.50, 1.07), (-0.505, 0.52), 0.262, CHEST),
    tb('C1b', (-0.52, 1.115), (-0.565, 0.522), 0.262, CHEST),
    tb('C2', (-0.535, 1.165), (-0.635, 0.53), 0.258, CHEST),       # fore region front ring
    tb('C3', (-0.545, 1.22), (-0.71, 0.55), 0.254, NECK),
    tb('N0', (-0.555, 1.275), (-0.785, 0.59), 0.25, NECK),          # the ruff: chest front up to the throat
    tb('N1', (-0.57, 1.33), (-0.85, 0.665), 0.25, NECK),
    tb('N2', (-0.595, 1.38), (-0.90, 0.77), 0.245, NECK),
    tb('N3', (-0.63, 1.42), (-0.935, 0.895), 0.232, NECK),
    tb('N4', (-0.675, 1.452), (-0.952, 1.02), 0.225, HEAD),
    tb('H0', (-0.73, 1.48), (-0.96, 1.115), 0.215, HEAD),          # the head fan over the crown
    tb('H1', (-0.785, 1.50), (-0.965, 1.175), 0.208, HEAD),
    tb('H2', (-0.855, 1.487), (-0.97, 1.212), 0.196, HEAD),
    tb('H3', (-0.915, 1.452), (-0.975, 1.232), 0.172, HEAD),
    tb('H4', (-0.962, 1.405), (-0.982, 1.243), 0.118, BEAK),        # cere: the beak's root
    tb('B0', (-1.0, 1.365), (-1.0, 1.235), 0.072, BEAK),
    tb('B1', (-1.04, 1.333), (-1.03, 1.222), 0.055, BEAK),
    tb('B2', (-1.075, 1.30), (-1.06, 1.203), 0.045, BEAK),
    tb('B3', (-1.103, 1.262), (-1.085, 1.18), 0.034, BEAK),
    tb('B4', (-1.12, 1.215), (-1.098, 1.155), 0.022, BEAK),         # the hook, tipped down
]

# limb sections: (centre xyz, rx, ry); a rounded box (superellipse p 3), flat front, back and sides
FORE = [((0.20, -0.595, 0.55), 0.112, 0.09), ((0.20, -0.603, 0.465), 0.104, 0.094), ((0.20, -0.61, 0.395), 0.098, 0.094),
        ((0.198, -0.618, 0.35), 0.092, 0.09),                                       # feathered trouser
        ((0.192, -0.628, 0.295), 0.068, 0.062), ((0.19, -0.643, 0.215), 0.062, 0.056),   # scaled tarsus
        ((0.19, -0.66, 0.135), 0.064, 0.058)]
# r11: thigh centre in (x 0.20 -> 0.24 at the hock) under the wider haunch, so the thigh is the body's side
# r9: the lion hind leg read off the sheet's near leg: a deep thigh (buttock to stifle), stifle forward, hock back
HIND = [((0.225, 0.44, 0.49), 0.11, 0.135),        # r17-20: first ring low, inner side out (x 0.115), back in line with
        ((0.225, 0.455, 0.43), 0.102, 0.128),      # R0: the groin and buttock slope into the leg (no 140-150 deg crease)
        ((0.23, 0.475, 0.37), 0.092, 0.108), ((0.235, 0.50, 0.31), 0.082, 0.095),
        ((0.24, 0.525, 0.245), 0.072, 0.085), ((0.24, 0.515, 0.165), 0.064, 0.07),
        ((0.24, 0.50, 0.095), 0.072, 0.088), ((0.24, 0.48, 0.04), 0.088, 0.115), ((0.24, 0.47, 0.0), 0.088, 0.122)]
SUPER = 3.0
def sec_pts(c, a, T, B, W, prof):
    y0, z0 = c
    s, co = math.sin(math.radians(a)), math.cos(math.radians(a))
    out = []
    for fx, fh in prof:
        h = fh * (T if fh >= 0 else B)
        out.append((fx * W, y0 + h * s, z0 + h * co))
    return out
# the folded wing, x >= 0: key stations along the wing (y, inner-top edge E0 (x, z), bulge E2, lower edge E4);
# the root station sits inside the shoulder, the rest rides over the back and flank, the tip hangs past the rump
WINGK = [(-0.60, (0.10, 1.07), (0.19, 1.02), (0.21, 0.93)),          # s3 r3: root deep in the ruff (no box end showing)
         (-0.44, (0.14, 1.18), (0.30, 1.12), (0.32, 0.93)),
         (-0.25, (0.09, 1.14), (0.33, 1.08), (0.35, 0.85)),
         (0.00, (0.06, 1.07), (0.335, 1.02), (0.355, 0.79)),
         (0.25, (0.07, 1.025), (0.325, 0.95), (0.345, 0.72)),
         (0.48, (0.10, 0.99), (0.305, 0.88), (0.325, 0.65)),
         (0.68, (0.15, 0.86), (0.28, 0.75), (0.295, 0.58)),
         (0.86, (0.235, 0.60), (0.255, 0.54), (0.262, 0.48))]
WT = 0.042            # slab thickness (membrane check: >= max(6 mm, 0.4 % of 2.25 m) = 9 mm)
WN = 15               # stations along the wing
TRANS = 0.45


# ---------------------------------------------------------------- typed blueprint + fit (t8 blueprint_fit)
REGIONS = {'fore': ('C1', 3, 8, 3), 'hind': ('R0', 4, 8, 3)}       # (first ring, spans, first point, faces)
PROFILES = dict(BODY=BODY, HAUNCH=HAUNCH, CHEST=CHEST, NECK=NECK, HEAD=HEAD, BEAK=BEAK, TAIL=TAIL)
BASE = dict(SECS=list(SECS), FORE=list(FORE), HIND=list(HIND), WINGK=list(WINGK))
NK = 9                                                              # knots along the spine per channel


def _prof_name(p):
    return next(k for k, v in PROFILES.items() if v is p)


def blueprint(secs=None, fore=None, hind=None, wingk=None):
    """The typed blueprint: spine samples (named rings, centre, tilt, half heights, width, profile), limb graph
    (root region on the loft + sections), wing keys, measured ratios."""
    secs, fore, hind, wingk = secs or BASE['SECS'], fore or BASE['FORE'], hind or BASE['HIND'], wingk or BASE['WINGK']
    ys = [s[1][0] for s in secs]
    L = max(ys) - min(ys)
    torso = [s for s in secs if s[0][0] in 'RWMC']
    return {
        'creature': 'griffin', 'units': 'm', 'axes': '+X left, -Y head, +Z up',
        'spine': [dict(name=n, centre=list(c), tilt_deg=a, top=T, bottom=B, width=W, profile=_prof_name(p)) for (n, c, a, T, B, W, p) in secs],
        'limbs': {
            'fore': dict(kind='eagle_foreleg', parent='chest', region=dict(zip(('ring', 'spans', 'point', 'faces'), REGIONS['fore'])),
                         sections=[dict(centre=list(c), rx=rx, ry=ry) for c, rx, ry in fore]),
            'hind': dict(kind='lion_hindleg', parent='hips', region=dict(zip(('ring', 'spans', 'point', 'faces'), REGIONS['hind'])),
                         sections=[dict(centre=list(c), rx=rx, ry=ry) for c, rx, ry in hind])},
        'wing': [dict(y=y, e0=list(a), e2=list(b), e4=list(c)) for y, a, b, c in wingk],
        'ratios': {'spine_length': round(L, 3),
                   'torso_max_width_over_length': round(2 * max(s[5] for s in torso) / L, 3),
                   'torso_max_depth_over_length': round(max(s[3] + s[4] for s in torso) / L, 3),
                   'head_width_over_torso_width': round(max(s[5] for s in secs if s[0][0] == 'H') / max(s[5] for s in torso), 3)}}


def _interp(knots, t):
    x = t * (len(knots) - 1); i = min(int(x), len(knots) - 2); f = x - i
    return knots[i] * (1 - f) + knots[i + 1] * f


def _region_centre(secs, which):
    nm, S, j0, F = REGIONS[which]
    i0 = [s[0] for s in secs].index(nm)
    pts = [sec_pts(*secs[i][1:]) [j] for i in range(i0, i0 + S + 1) for j in range(j0, j0 + F + 1)]
    return [sum(p[k] for p in pts) / len(pts) for k in range(3)]


def apply(par):
    """par: kW, kT, kB (NK knots each, multipliers along the spine), fr/hr (fore/hind leg radius multipliers),
    wz (wing lift, m). Topology is fixed: same stations, profiles, regions, section counts."""
    n = len(BASE['SECS'])
    secs = []
    for i, (nm, c, a, T, B, W, p) in enumerate(BASE['SECS']):
        t = i / (n - 1)
        secs.append((nm, c, a, T * _interp(par['kT'], t), B * _interp(par['kB'], t), W * _interp(par['kW'], t), p))
    legs = {}
    for which, base, rk in (('fore', BASE['FORE'], 'fr'), ('hind', BASE['HIND'], 'hr')):
        c0, c1 = _region_centre(BASE['SECS'], which), _region_centre(secs, which)
        dx, dz = c1[0] - c0[0], c1[2] - c0[2]
        m = len(base)
        # radius growth goes outward: the inner wall stays where the region's inner edge is (s1 r1: a 1.3x foreleg
        # grown about its centre ran into the belly between the legs, 14 self-intersecting pairs at x 0.056)
        legs[which] = [((c[0] + dx + rx * (par[rk] - 1), c[1], c[2] + dz * max(0.0, 1 - i / (m - 2)) if c[2] > 0.06 else c[2]),
                        rx * par[rk], ry * par[rk]) for i, (c, rx, ry) in enumerate(base)]
    # the wing rides the fitted back: x by the local width multiplier, z by the local top change
    def local(y):
        best = min(range(n), key=lambda i: abs(BASE['SECS'][i][1][0] - y) if BASE['SECS'][i][0][0] in 'RWMCN' else 9)
        b, s = BASE['SECS'][best], secs[best]
        return s[5] / b[5], (s[3] - b[3])
    wk = []
    for y, e0, e2, e4 in BASE['WINGK']:
        mw, dt = local(y)
        dz = dt + par.get('wz', 0.0)
        wk.append((y, (e0[0] * mw, e0[1] + dz), (e2[0] * mw, e2[1] + dz), (e4[0] * mw, e4[1] + dz * 0.5)))
    return secs, legs['fore'], legs['hind'], wk


FIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'blueprint_fit.json')


def load_fit():
    """Replace the hand tables with the fitted blueprint, if blueprint_fit.json exists."""
    global SECS, FORE, HIND, WINGK
    if not os.path.exists(FIT):
        return False
    bp = json.load(open(FIT))
    SECS = [(s['name'], tuple(s['centre']), s['tilt_deg'], s['top'], s['bottom'], s['width'], PROFILES[s['profile']]) for s in bp['spine']]
    FORE = [(tuple(s['centre']), s['rx'], s['ry']) for s in bp['limbs']['fore']['sections']]
    HIND = [(tuple(s['centre']), s['rx'], s['ry']) for s in bp['limbs']['hind']['sections']]
    WINGK = [(w['y'], tuple(w['e0']), tuple(w['e2']), tuple(w['e4'])) for w in bp['wing']]
    return True


load_fit()
