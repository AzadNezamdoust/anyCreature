import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from mathutils import Vector

META = dict(creature='stag', model='opus',
            keep_valleys=lambda c: abs(c.x) > 0.05 and -0.5 < c.y < -0.38 and 1.05 < c.z < 1.2)

# the skeleton the model is built on (x, y, z); -Y is forward
J = dict(
    pelvis=(0, 0.50, 0.78), spine=(0, 0.15, 0.82), chest=(0, -0.12, 0.80),
    neck=(0, -0.20, 0.84), neck2=(0, -0.27, 1.00), head=(0, -0.33, 1.13), snout=(0, -0.62, 1.04),
    shoulder=(0.10, -0.06, 0.72), elbow=(0.095, -0.07, 0.43), knee=(0.092, -0.075, 0.265),
    ffet=(0.09, -0.085, 0.075), ftoe=(0.09, -0.12, 0.0),
    hip=(0.11, 0.46, 0.74), stifle=(0.105, 0.47, 0.45), hock=(0.10, 0.59, 0.29),
    hfet=(0.10, 0.565, 0.075), htoe=(0.10, 0.53, 0.0),
    ear=(0.10, -0.30, 1.19), ear_tip=(0.235, -0.30, 1.235),
    ant=(0.07, -0.34, 1.27), ant_tip=(0.31, -0.13, 1.67),
    tail=(0, 0.62, 0.74), tail_tip=(0, 0.67, 0.60),
)

# a ring: (top (y, z), bottom (y, z), half width, profile [(s along top->bottom, x factor)])
TORSO = [(0, 0), (0.12, 0.75), (0.45, 1.0), (0.78, 0.72), (1, 0)]
NECK = [(0, 0), (0.15, 0.8), (0.5, 1.0), (0.85, 0.7), (1, 0)]
HEAD = [(0, 0), (0.05, 0.62), (0.3, 1.0), (0.75, 0.8), (1, 0)]
RINGS = [
    ((0.635, 0.76), (0.635, 0.60), 0.07, TORSO),     # R0 rump end (cap)
    ((0.56, 0.80), (0.56, 0.50), 0.13, TORSO),       # R1 buttock
    ((0.36, 0.86), (0.36, 0.50), 0.155, TORSO),      # R2 hip
    ((0.18, 0.87), (0.18, 0.545), 0.145, TORSO),     # R3 flank / tucked belly
    ((0.00, 0.88), (0.00, 0.45), 0.172, TORSO),      # R4 ribcage
    ((-0.13, 0.92), (-0.13, 0.435), 0.17, TORSO),     # R5 chest / shoulder
    ((-0.15, 0.96), (-0.30, 0.56), 0.16, NECK),      # R6 chest front, neck base
    ((-0.20, 1.03), (-0.37, 0.70), 0.135, NECK),     # N1
    ((-0.25, 1.13), (-0.41, 0.86), 0.11, NECK),      # N2
    ((-0.27, 1.20), (-0.41, 0.975), 0.085, HEAD),    # H1 skull back (ear strip H1-H2)
    ((-0.315, 1.235), (-0.44, 0.985), 0.09, HEAD),   # H2 (antler strip H2-H3)
    ((-0.37, 1.245), (-0.47, 0.99), 0.09, HEAD),     # H3
    ((-0.45, 1.22), (-0.51, 0.99), 0.085, HEAD),     # H4 brow / eye
    ((-0.52, 1.15), (-0.55, 0.99), 0.065, HEAD),     # H5 stop
    ((-0.595, 1.10), (-0.60, 0.99), 0.056, HEAD),    # H6 muzzle
    ((-0.64, 1.08), (-0.635, 0.995), 0.046, HEAD), # H7 nose (cap)
]
TOP, SHO, SIDE, LOW, BOT = range(5)

# limb sections: (centre, half width across, half depth, down/along direction hint)
FORE = [((0.095, -0.07, 0.43), 0.036, 0.062), ((0.094, -0.07, 0.33), 0.03, 0.046),
        ((0.092, -0.075, 0.265), 0.026, 0.034), ((0.09, -0.08, 0.16), 0.018, 0.022),
        ((0.09, -0.085, 0.075), 0.02, 0.028), ((0.09, -0.10, 0.045), 0.024, 0.036),
        ((0.09, -0.11, 0.0), 0.026, 0.046)]
HIND = [((0.105, 0.49, 0.44), 0.046, 0.09), ((0.10, 0.565, 0.34), 0.034, 0.064),
        ((0.10, 0.578, 0.28), 0.028, 0.046), ((0.10, 0.575, 0.15), 0.018, 0.022),
        ((0.10, 0.565, 0.075), 0.02, 0.028), ((0.10, 0.55, 0.045), 0.024, 0.036),
        ((0.10, 0.535, 0.0), 0.026, 0.046)]
EAR = [((0.13, -0.30, 1.21), 0.013, 0.038), ((0.195, -0.305, 1.245), 0.013, 0.058),
       ((0.255, -0.31, 1.27), 0.004, 0.007)]
BEAM = [((0.08, -0.33, 1.29), 0.025, 0.025), ((0.16, -0.27, 1.36), 0.02, 0.02),
        ((0.25, -0.20, 1.44), 0.017, 0.017), ((0.29, -0.16, 1.55), 0.014, 0.014),
        ((0.30, -0.13, 1.66), 0.006, 0.006)]


def ring_pts(top, bot, w, prof):
    t, b = Vector((0, *top)), Vector((0, *bot))
    return [(w * fx, *(t.lerp(b, s)).yz) for s, fx in prof]


def strip_face(bm, rows, i, a, b):
    """the quad between rows i and i+1, points a..b of the half ring"""
    vs = {rows[i][a], rows[i][b], rows[i + 1][a], rows[i + 1][b]}
    return next(f for f in rows[i][a].link_faces if set(f.verts) == vs)


def section(verts, c, u, v, hu, hv):
    """place a 4-vert face as a rectangle about c: +-hu along u, +-hv along v, keeping its winding"""
    c, u, v = Vector(c), Vector(u).normalized(), Vector(v).normalized()
    m = centre(verts)
    srt = sorted(verts, key=lambda q: (q.co - m).dot(u))
    lo, hi = sorted(srt[:2], key=lambda q: (q.co - m).dot(v)), sorted(srt[2:], key=lambda q: (q.co - m).dot(v))
    lo[0].co = c - u * hu - v * hv; lo[1].co = c - u * hu + v * hv
    hi[0].co = c + u * hu - v * hv; hi[1].co = c + u * hu + v * hv


def limb(bm, face, secs, u_of, v_of):
    """chain of extrusions from a face through rectangular sections"""
    pts = [Vector(s[0]) for s in secs]
    for i, (c, hu, hv) in enumerate(secs):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        r = extrude(bm, [face])
        face = r['faces'][0]
        section(list(face.verts), c, u_of(d), v_of(d), hu, hv)
    return face


def perp(a, d):
    a = Vector(a); return (a - d * a.dot(d)).normalized()


def stage1(k):
    bm = bmesh.new()
    rows = [ring(bm, ring_pts(*r)) for r in RINGS]
    for a, b in zip(rows, rows[1:]):
        bridge(bm, a, b)
    cap(bm, list(reversed(rows[0])))
    cap(bm, rows[-1])
    recalc_normals(bm)
    # legs from the lower flank (side-low strip)
    leg_u = lambda d: perp((1, 0, 0), d)
    leg_v = lambda d: perp((0, 1, 0), d)
    limb(bm, strip_face(bm, rows, 4, SIDE, LOW), FORE, leg_u, leg_v)
    limb(bm, strip_face(bm, rows, 1, SIDE, LOW), HIND, leg_u, leg_v)
    # leaf ears: thin along Y, broad along Z, pointing out
    limb(bm, strip_face(bm, rows, 9, SHO, SIDE), EAR, lambda d: perp((0, 1, 0), d), lambda d: perp((0, 0, 1), d))
    # antler main beams from the top of the skull, up, out and back
    limb(bm, strip_face(bm, rows, 10, SHO, SIDE), BEAM, lambda d: perp((1, 0, 0), d), lambda d: perp((0, 1, 0), d))
    snap_seam(bm)
    recalc_normals(bm)
    return object_from_bm('body', bm)


def stage2(k, body):
    bm = edit(body)
    near = lambda p: vert_near(bm, p)
    # brow ridge overhangs the eye; cheek plane below it
    brow = near((0.053, -0.453, 1.209)); brow.co.x += 0.018; brow.co.z += 0.008
    for p, dx in (((0.09, -0.40, 1.168), 0.006), ((0.085, -0.468, 1.151), 0.012)):
        near(p).co.x += dx
    # the stop: the muzzle top dips in front of the brow
    near((0, -0.52, 1.15)).co.z -= 0.012
    # jaw line: the lower cheek corners flare slightly so the pale jaw reads as its own plane
    for p in ((0.068, -0.487, 1.047), (0.052, -0.545, 1.03), (0.045, -0.60, 1.01)):
        near(p).co.x += 0.008
    with k.topo(bm, 'inset', 'eye socket: a loop inside the cheek face under the brow'):
        f = face_near(bm, (0.085, -0.44, 1.12), n=(1, 0, 0))
        eye = inset(bm, [f], 0.35, -0.008)[0]
        move(eye.verts, (0, 0, 0.012))
    with k.topo(bm, 'inset', 'nose pad: a loop inside the nose cap for the black nose block'):
        f = face_near(bm, (0.02, -0.64, 1.04), n=(0, -1, 0))
        inset(bm, [f], 0.3, 0.006)
    with k.topo(bm, 'loop', 'mid-neck loop: the neck bends for grazing and the charge'):
        loopcut(bm, edge_near(bm, (0, -0.225, 1.08)), t=0.5)
    with k.topo(bm, 'loop', 'second hock loop: the hind leg bends at the hock'):
        loopcut(bm, edge_near(bm, (0.128, 0.60, 0.31)), t=0.5)
    # tips: a needle quad is a sliver; open the beam and ear tip sections into small blunt ends
    for c in ((0.30, -0.13, 1.66), (0.255, -0.31, 1.27)):
        tip = verts_where(bm, lambda q: (q - Vector(c)).length < 0.015)
        scale(tip, 2.2)
    # the head is the medium mass: size it up a little (ears and beams ride along)
    head = verts_where(bm, lambda q: (q.y < -0.35 and q.z > 0.96) or q.z > 1.25 or (q.x > 0.1 and q.z > 1.18))
    scale(head, 1.08, pivot=(0, -0.35, 1.12))
    snap_seam(bm)
    commit(body, bm)


PAL = {'body': '#8a5a3a', 'mane': '#6a4630', 'cream': '#d9c3a0', 'antler': '#d8c8a8',
       'hoof': '#231a16', 'eye': '#111111'}
HP = Vector((0, -0.35, 1.12))


def B(p):
    """a stage-1 head/antler point after the stage-2 head scale"""
    return HP + (Vector(p) - HP) * 1.08


def spike(bm, base, tip, half, hint=(0, 0, 1), half2=None):
    """a closed 4-sided tine/tuft: square root at base, point at tip"""
    base, tip = Vector(base), Vector(tip)
    d = (tip - base).normalized()
    u = perp(hint, d) if abs(Vector(hint).normalized().dot(d)) < 0.95 else perp((1, 0, 0), d)
    v = d.cross(u)
    h2 = half if half2 is None else half2
    q = ring(bm, [base + u * a * half + v * b * h2 for a, b in ((1, 1), (-1, 1), (-1, -1), (1, -1))])
    t = bm.verts.new(tip)
    cap(bm, list(reversed(q)))
    for i in range(4):
        bm.faces.new([q[i], q[(i + 1) % 4], t])


def body_rule(c, n, i):
    y, z = c.y, c.z
    head = -0.225 * (y + 0.27) + 0.14 * (z - 1.2) > 0
    neck = -0.40 * (y + 0.15) + 0.15 * (z - 0.96) > 0 and not head
    if z < 0.05:
        return 'hoof'
    if abs(c.x) > 0.11 and z < 1.31 and y < -0.28 and z > 1.15:
        return 'cream' if n.y < -0.45 else 'body'          # ear: pale inside
    if z > 1.31 or (z > 1.255 and abs(c.x) > 0.055):
        return 'antler'
    if head:
        if y < -0.645 and n.y < -0.6:
            return 'hoof'                                   # black nose block
        return 'cream' if n.z < -0.55 else 'body'           # pale jaw line
    if neck:
        return 'cream' if (n.y < -0.4 and z > 0.9) else 'mane'
    if y > 0.5 and n.y > 0.35 and z > 0.5:
        return 'cream'                                      # rump patch
    if n.z < -0.6 and 0.05 < y < 0.5:
        return 'cream'                                      # pale belly
    return 'body'


def stage3(k, body):
    from mathutils.bvhtree import BVHTree
    paint(body, PAL, body_rule)
    pieces = []
    # eyes: a low bipyramid lens sitting proud in the socket
    est = B((0.085, -0.44, 1.132))
    me = body.data
    cand = [p for p in me.polygons if p.normal.x > 0.5 and (Vector(p.center) - est).length < 0.035]
    f = min(cand, key=lambda p: p.area)
    c, n = Vector(f.center), Vector(f.normal)
    bm = bmesh.new()
    u = perp((0, 0, 1), n); v = n.cross(u)
    rim = ring(bm, [c + n * 0.003 + (u * math.cos(a) * 0.017 + v * math.sin(a) * 0.012)
                    for a in [i * math.pi / 3 for i in range(6)]])
    fr, bk = bm.verts.new(c + n * 0.011), bm.verts.new(c - n * 0.012)
    for i in range(6):
        bm.faces.new([rim[i], rim[(i + 1) % 6], fr]); bm.faces.new([rim[(i + 1) % 6], rim[i], bk])
    eye = object_from_bm('eye', bm); paint(eye, {'eye': PAL['eye']}, lambda c, n, i: 'eye'); pieces.append(eye)
    # antler tines: brow and bez tines forward, trez, and a three-point crown
    A = [B(s[0]) for s in BEAM]
    L = lambda i, t: A[i].lerp(A[i + 1], t)
    tines = [(L(0, 0.15), B((0.12, -0.49, 1.40)), 0.02), (L(0, 0.85), B((0.19, -0.42, 1.45)), 0.017),
             (L(2, 0.15), B((0.29, -0.32, 1.54)), 0.016), (L(3, 0.25), B((0.37, -0.20, 1.64)), 0.014),
             (L(3, 0.7), B((0.24, -0.24, 1.72)), 0.012), (L(3, 0.55), B((0.36, -0.07, 1.70)), 0.012)]
    bm = bmesh.new()
    for base, tip, h in tines:
        spike(bm, base, tip, h)
    ant = object_from_bm('antlers', bm); paint(ant, {'antler': PAL['antler']}, lambda c, n, i: 'antler'); pieces.append(ant)
    # mane: shaggy tufts rooted in the neck, a dark V bib hanging on the throat and chest
    dg = bpy.context.evaluated_depsgraph_get()
    tree = BVHTree.FromObject(body, dg)
    bm = bmesh.new()
    def tuft(o, d, down, length, half, lift=0.3):
        loc, nn, _, _ = tree.ray_cast(Vector(o), Vector(d).normalized())
        if loc is None:
            return
        dirn = (nn * lift + Vector(down)).normalized()
        spike(bm, loc - nn * 0.018, loc + dirn * length, 0.013, hint=nn, half2=half * 1.5)
    for j, z in enumerate((0.95, 0.88, 0.81, 0.74, 0.68, 0.62)):
        tuft((0.035, -0.9, z), (0, 1, 0), (0, 0.1, -0.8), 0.08 + 0.016 * j, 0.026)
        if j < 5:
            tuft((0.085, -0.9, z + 0.03), (0, 1, 0), (0, 0.15, -0.8), 0.07 + 0.01 * j, 0.024)
    for y, z in ((-0.30, 0.98), (-0.25, 0.88), (-0.20, 0.78), (-0.33, 1.07)):
        tuft((0.5, y, z), (-1, 0, 0), (0, 0.25, -0.7), 0.085, 0.028, 0.45)
    for y in (-0.18, -0.23):
        tuft((0.03, y, 1.6), (0, 0, -1), (0, 0.7, 0.1), 0.07, 0.022, 0.4)
    mane = object_from_bm('mane', bm); paint(mane, {'mane': PAL['mane']}, lambda c, n, i: 'mane'); pieces.append(mane)
    # short hanging tail: body brown on top, cream beneath
    bm = bmesh.new()
    full = lambda h: [h[0], h[1], h[2], h[3]] + [(-x, y, z) for x, y, z in (h[2], h[1])]
    r0 = ring(bm, full([(0, 0.615, 0.745), (0.03, 0.618, 0.735), (0.03, 0.628, 0.70), (0, 0.628, 0.69)]))
    r1 = ring(bm, full([(0, 0.665, 0.70), (0.028, 0.668, 0.69), (0.026, 0.672, 0.64), (0, 0.672, 0.635)]))
    r2 = ring(bm, full([(0, 0.678, 0.625), (0.012, 0.68, 0.62), (0.01, 0.68, 0.595), (0, 0.68, 0.59)]))
    bridge(bm, r0, r1, closed=True); bridge(bm, r1, r2, closed=True); cap(bm, list(reversed(r0))); cap(bm, r2)
    tail = object_from_bm('tail', bm, mirror=False)
    paint(tail, {'body': PAL['body'], 'cream': PAL['cream']}, lambda c, n, i: 'cream' if n.y > 0.3 or n.z < -0.3 else 'body')
    pieces.append(tail)
    return pieces


def rigid_shells(ob):
    """each shell of a piece moves as one: every vertex gets the shell's mean weights"""
    me = ob.data
    par = list(range(len(me.vertices)))
    def f(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    for e in me.edges:
        par[f(e.vertices[0])] = f(e.vertices[1])
    comps = {}
    for v in me.vertices:
        comps.setdefault(f(v.index), []).append(v.index)
    for vs in comps.values():
        acc = {}
        for vi in vs:
            for g in me.vertices[vi].groups:
                acc[g.group] = acc.get(g.group, 0.0) + g.weight / len(vs)
        for gi, w in acc.items():
            ob.vertex_groups[gi].add(vs, w, 'REPLACE')


def stage4(k, body, pieces):
    g = lambda n: J[n]
    rig = armature([
        ('spine', (0, 0.45, 0.80), (0, 0.05, 0.82), None),
        ('chest', (0, 0.05, 0.82), g('neck'), 'spine', True),
        ('neck', g('neck'), g('neck2'), 'chest', True),
        ('neck2', g('neck2'), g('head'), 'neck', True),
        ('head', g('head'), tuple(B(J['snout'])), 'neck2', True),
        ('ear.L', tuple(B(J['ear'])), tuple(B(J['ear_tip'])), 'head'),
        ('antler.L', tuple(B(J['ant'])), tuple(B(J['ant_tip'])), 'head'),
        ('tail', g('tail'), g('tail_tip'), 'spine'),
        ('upperarm.L', g('shoulder'), g('elbow'), 'chest'),
        ('forearm.L', g('elbow'), g('knee'), 'upperarm.L', True),
        ('cannon.L', g('knee'), g('ffet'), 'forearm.L', True),
        ('hoof.L', g('ffet'), g('ftoe'), 'cannon.L', True),
        ('thigh.L', g('hip'), g('stifle'), 'spine'),
        ('shin.L', g('stifle'), g('hock'), 'thigh.L', True),
        ('hcannon.L', g('hock'), g('hfet'), 'shin.L', True),
        ('hhoof.L', g('hfet'), g('htoe'), 'hcannon.L', True),
    ], roll='auto')
    skin(body, rig)
    for p in pieces:
        bind(p, rig, body=body)
        if 'mane' in p.name or 'antler' in p.name:
            rigid_shells(p)
    graze = {'neck': (34, 0, 0), 'neck2': (22, 0, 0), 'head': (8, 0, 0), 'chest': (4, 0, 0)}
    clip(rig, 'idle', {1: {}, 14: graze, 24: {**graze, 'ear.L': (0, 0, 22)}, 28: {**graze, 'ear.L': (0, 0, -8)},
                       34: graze, 48: {}})
    def stride(s):
        a, b = ('L', 'R') if s > 0 else ('R', 'L')
        return {f'upperarm.{a}': (18, 0, 0), f'upperarm.{b}': (-16, 0, 0),
                f'thigh.{b}': (14, 0, 0), f'thigh.{a}': (-14, 0, 0), f'shin.{a}': (-6, 0, 0),
                'neck': (3, 0, 0)}
    def lift(s):
        a, b = ('R', 'L') if s > 0 else ('L', 'R')
        return {f'forearm.{a}': (-40, 0, 0), f'cannon.{a}': (-15, 0, 0), f'upperarm.{a}': (4, 0, 0),
                f'thigh.{b}': (6, 0, 0), f'shin.{b}': (-22, 0, 0), f'hcannon.{b}': (30, 0, 0), 'neck': (-2, 0, 0)}
    clip(rig, 'move', {1: stride(1), 7: lift(1), 13: stride(-1), 19: lift(-1), 25: stride(1)})
    wind = {'neck': (-10, 0, 0), 'head': (-6, 0, 0), 'thigh.L': (8, 0, 0), 'thigh.R': (8, 0, 0)}
    ram = {'neck': (30, 0, 0), 'neck2': (16, 0, 0), 'head': (-14, 0, 0), 'chest': (6, 0, 0),
           'upperarm.L': (-14, 0, 0), 'upperarm.R': (-14, 0, 0), 'thigh.L': (-10, 0, 0), 'thigh.R': (-10, 0, 0)}
    clip(rig, 'attack', {1: {}, 8: wind, 16: ram, 22: ram, 32: {}},
         loc={1: {'spine': (0, 0, 0)}, 8: {'spine': (0, -0.03, 0)}, 16: {'spine': (0, 0.07, 0)},
              22: {'spine': (0, 0.07, 0)}, 32: {'spine': (0, 0, 0)}})
    return rig


run(META, stage1, stage2, stage3, stage4)
