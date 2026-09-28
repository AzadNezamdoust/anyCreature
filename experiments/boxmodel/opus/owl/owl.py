"""Owl: a stylised horned owl perched upright, box-modelled for the staged experiment.

Build plan (stage 1): one trunk of 6-vert half-rings bent through a right angle,
from the tail tip (vertical slices) through the rump and belly (diagonal slices)
to the chest, neck and head (horizontal slices). Each ring is a slice between a
dorsal point T (the back) and a ventral point B (the belly / face front) of the
side profile; the four side verts are BK (back), SD (side), FC (front corner,
on the head: the facial-disc rim) and FF (front face). The crown closes on an
inner ring so the head top has quads away from the seam. Out of the trunk:
  - each ear tuft is extruded from the crown's outer-front quad (up and out);
  - each leg (4-sided feathered 'trousers') is extruded from the belly-underside
    quad, then a foot box; four toes come out of the foot-box walls
    (2 forward, 2 back);
  - each folded wing is extruded from a 2-face patch on the upper flank under
    the head (6-sided sections: shoulder, then crescents hugging the flank
    down and back, the tip over the tail).
"""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'kit'))
from bmkit import *
from bmkit import _bone_segments, _seg_dist

META = dict(creature='owl', model='opus', engine_glb='')

# ----------------------------------------------------------------------------- skeleton
J = dict(
    hips=(0.0, 0.05, 0.15), chest=(0.0, 0.0, 0.27), neck=(0.0, -0.005, 0.345), head=(0.0, -0.01, 0.38),
    crown=(0.0, -0.01, 0.56),
    tail0=(0.0, 0.12, 0.12), tail1=(0.0, 0.27, 0.055),
    hipL=(0.075, 0.01, 0.12), kneeL=(0.075, -0.012, 0.075), ankleL=(0.075, -0.02, 0.03), toeL=(0.075, -0.09, 0.01),
    shoulderL=(0.12, 0.01, 0.345), wristL=(0.16, 0.03, 0.25), handL=(0.135, 0.08, 0.165), tipL=(0.045, 0.255, 0.15),
    tuftL=(0.10, -0.045, 0.565), tufttipL=(0.16, -0.035, 0.635),
)

# ----------------------------------------------------------------------------- trunk rings
# half-ring = [T (back seam), BK, SD, FC, FF, B (front seam)]
# shape: four (fraction of W, s along T->B) for the side verts
TAIL = ((0.90, 0.22), (1.00, 0.50), (0.90, 0.78), (0.50, 0.95))
BODY = ((0.72, 0.13), (1.00, 0.45), (0.90, 0.75), (0.52, 0.94))
HEAD = ((0.80, 0.12), (1.00, 0.42), (0.97, 0.80), (0.56, 0.96))

RINGS = [  # name, T (y, z), B (y, z), W, shape
    ('t0', (0.270, 0.075), (0.265, 0.035), 0.045, TAIL),
    ('t1', (0.170, 0.125), (0.140, 0.055), 0.070, TAIL),
    ('r0', (0.135, 0.175), (0.030, 0.075), 0.100, BODY),
    ('b0', (0.135, 0.225), (-0.080, 0.095), 0.115, BODY),
    ('b1', (0.125, 0.270), (-0.135, 0.180), 0.125, BODY),
    ('b2', (0.110, 0.310), (-0.130, 0.270), 0.130, BODY),
    ('n0', (0.090, 0.345), (-0.110, 0.335), 0.125, BODY),
    ('k0', (0.100, 0.380), (-0.125, 0.370), 0.135, HEAD),
    ('k1', (0.110, 0.440), (-0.130, 0.440), 0.145, HEAD),
    ('k2', (0.100, 0.500), (-0.125, 0.505), 0.140, HEAD),
    ('k3', (0.070, 0.550), (-0.100, 0.550), 0.125, HEAD),
]
CROWN_IN, CROWN_DZ = 0.5, 0.012          # the inner crown ring: k3 pulled in by half, a touch up


def ring_pts(T, B, W, shape):
    T = Vector((0.0, T[0], T[1])); B = Vector((0.0, B[0], B[1]))
    pts = [T]
    for fx, s in shape:
        p = T.lerp(B, s)
        pts.append(Vector((fx * W, p.y, p.z)))
    pts.append(B)
    return pts


def crown_pts():
    n, T, B, W, shape = next(r for r in RINGS if r[0] == 'k3')
    k3 = ring_pts(T, B, W, shape)
    c = sum(k3, Vector()) / len(k3)
    return [Vector((p.x * CROWN_IN, c.y + (p.y - c.y) * CROWN_IN, p.z + CROWN_DZ)) for p in k3]


# hand moves on single ring vertices (ring, index) -> offset
TWEAK = {
    # the crown dips in a V between the tufts (front view), the brow line runs down to the beak
    ('k3', 5): (0, 0, -0.030), ('k3', 4): (0, 0, -0.018), ('k4', 5): (0, 0, -0.026), ('k4', 4): (0, 0, -0.014),
    ('k4', 0): (0, 0, -0.008), ('k4', 1): (0, 0, -0.006),
    # the facial disc: a dish per eye — FF (dish centre) pushed back, FC (the rim) forward and out,
    # the seam B (beak ridge) left standing between the two dishes
    ('k0', 4): (0, 0.014, 0), ('k1', 4): (0, 0.026, 0), ('k2', 4): (0, 0.018, 0),
    ('k0', 3): (0.004, -0.012, 0), ('k1', 3): (0.006, -0.014, 0), ('k2', 3): (0.004, -0.012, 0),
    ('k3', 3): (0.0, -0.006, 0),
}


def rp(name, i=None):
    """The stage-1 position of vertex i (0 T .. 5 B) of trunk ring `name` (all if i is None)."""
    if name == 'k4':
        pts = crown_pts()
    else:
        n, T, B, W, shape = next(r for r in RINGS if r[0] == name)
        pts = ring_pts(T, B, W, shape)
    pts = [p + Vector(TWEAK.get((name, j), (0, 0, 0))) for j, p in enumerate(pts)]
    return pts if i is None else pts[i]


T_, BK, SD, FC, FF, B_ = range(6)


def face_of(vs):
    s = set(vs)
    return next(f for f in vs[0].link_faces if set(f.verts) == s)


def ext(bm, faces, old, new_pts):
    """E then G/S/R: extrude the region, place the copies of `old` (its boundary,
    in my order) at new_pts. Returns (new boundary verts in the same order, new faces)."""
    pos = [v.co.copy() for v in old]
    r = extrude(bm, faces)
    nv = r['verts']
    new = [min(nv, key=lambda v: (v.co - p).length) for p in pos]
    assert len(set(new)) == len(new), 'ext: ambiguous vertex match'
    for v, p in zip(new, new_pts):
        v.co = Vector(p)
    return new, r['faces']


def quad(c, hy, hx, rot=0.0):
    """A 4-sided limb section at centre c (horizontal): [BI, BO, FO, FI]."""
    c = Vector(c)
    a = math.radians(rot)
    ex, ey = Vector((math.cos(a), math.sin(a), 0)), Vector((-math.sin(a), math.cos(a), 0))
    return [c - ex * hx + ey * hy, c + ex * hx + ey * hy, c + ex * hx - ey * hy, c - ex * hx - ey * hy]


def toe(bm, wall, dirn, L, w1, h1, w2, h2):
    """Extrude one toe out of a foot-box wall [P, Q, Q', P'] (top, top, sole, sole)."""
    P, Q, Qs, Ps = wall
    f = face_of(wall)
    t = Vector((dirn[0], dirn[1], 0.0)).normalized()
    s = Vector((-t.y, t.x, 0.0))
    if s.dot(Q.co - P.co) < 0:
        s = -s
    c0 = (P.co + Q.co + Qs.co + Ps.co) / 4
    c0.z = 0.0
    old = [P, Q, Qs, Ps]
    faces = [f]
    for frac, w, h in ((0.5, w1, h1), (1.0, w2, h2)):
        c = c0 + t * L * frac
        pts = [c - s * w + Vector((0, 0, h)), c + s * w + Vector((0, 0, h)), c + s * w, c - s * w]
        old, faces = ext(bm, faces, old, pts)
    return old


LEG = [quad((0.080, -0.006, 0.066), 0.042, 0.036),        # fluffy feathered trousers under the belly
       quad(J['ankleL'], 0.026, 0.024),                     # ankle / foot top
       quad((0.075, -0.022, 0.0), 0.024, 0.022)]            # sole: a compact base for the toes

TOES = [  # foot-box wall (quad indices), direction, length, knuckle w/h, tip w/h
    (2, 3, (0.0, -1.0), 0.068, 0.014, 0.030, 0.010, 0.020),      # front (middle) toe
    (3, 0, (-0.55, -0.85), 0.060, 0.013, 0.028, 0.009, 0.019),   # inner forward toe
    (1, 2, (0.9, 0.35), 0.052, 0.013, 0.028, 0.009, 0.019),      # outer toe, reversed (sideways-back)
    (0, 1, (0.1, 1.0), 0.046, 0.013, 0.028, 0.009, 0.019)]       # hind toe


def toe_tip(i):
    a_, b_, dirn, L = TOES[i][:4]
    c0 = (LEG[1][a_] + LEG[1][b_] + LEG[2][a_] + LEG[2][b_]) / 4
    c0.z = 0.0
    t = Vector((dirn[0], dirn[1], 0.0)).normalized()
    return c0 + t * L, t


def sect(Fo, Mo, Bo, th, axis=(0.0, 0.02)):
    """A folded-wing section wrapping the body: outer points Fo (front edge on the
    flank), Mo (the back-side corner), Bo (the back edge near the spine); the inner
    points sit th closer to the body axis (0, axis). Returns [FO, O, BO, BI, I, FI]."""
    def inn(p):
        p = Vector(p)
        d = Vector((-p.x, axis[1] - p.y, 0.0)).normalized()
        return p + d * th
    return [Vector(Fo), Vector(Mo), Vector(Bo), inn(Bo), inn(Mo), inn(Fo)]


WING = [
    # shoulder: out from the flank under the head, its top sloping down from the head's corner
    [(0.146, -0.065, 0.330), (0.156, 0.005, 0.338), (0.136, 0.085, 0.335),
     (0.130, 0.090, 0.303), (0.146, 0.005, 0.298), (0.140, -0.068, 0.298)],
    # down the flank and over the back, the back edge near the spine
    sect((0.170, -0.070, 0.262), (0.138, 0.098, 0.255), (0.045, 0.160, 0.250), 0.022),
    sect((0.176, -0.030, 0.165), (0.145, 0.118, 0.188), (0.042, 0.180, 0.205), 0.024),   # the turn begins
    sect((0.138, 0.065, 0.118), (0.104, 0.160, 0.140), (0.035, 0.205, 0.162), 0.018),    # round the rump
    sect((0.060, 0.240, 0.145), (0.048, 0.255, 0.150), (0.032, 0.262, 0.158), 0.012, axis=(0.0, 0.26)),  # tips
]


# stage 2 (AD note 2): the tip section reshaped into one blunt tip, 5 cm wide and 2 cm thick
WING_TIP = sect((0.104, 0.188, 0.128), (0.068, 0.236, 0.142), (0.030, 0.262, 0.158), 0.020, axis=(0.0, 0.26))
WING3_OUT = 0.010
TAIL_IN = 0.35                     # the tail tip ring slides this far toward t1: ~25% shorter, blunter
TAIL_THIN, TAIL_THIN1 = 0.42, 0.78  # R2 note 4: tip / t1 thickness below the top ridge (a tapered fan)
TAIL_TIP = {0: (0, 0.016, 0.0), 1: (0.002, 0.008, -0.002), 2: (0.004, -0.008, -0.006),
            3: (0.002, -0.006, -0.004), 4: (0, 0.004, 0), 5: (0, 0.014, 0.0)}   # blunt point; outer feathers drop


def tuft_sections():
    """The stage-1 positions of the three tuft sections, each [outer-side, outer-front, inner-front,
    inner-side] (from the crown quad k3 SD, k3 FC, k4 FC, k4 SD)."""
    base = [rp('k3', SD), rp('k3', FC), rp('k4', FC), rp('k4', SD)]
    c = centre_pts(base)
    tip = Vector(J['tufttipL'])
    out = []
    for f_, sx, sy in TUFT:
        cc = c.lerp(tip, f_)
        out.append([cc + Vector(((p.x - c.x) * sx, (p.y - c.y) * sy, (p.z - c.z) * sx)) for p in base])
    return out


def centre_pts(ps):
    return sum(ps, Vector()) / len(ps)


TUFT = ((0.22, 0.85, 0.45), (0.62, 0.6, 0.32), (1.0, 0.16, 0.1))   # a flat blade: wide from the front


def stage1(k):
    bm = bmesh.new()
    R = {}
    rows = []
    for name, *_ in RINGS:
        R[name] = ring(bm, rp(name))
        rows.append(R[name])
    R['k4'] = ring(bm, rp('k4'))
    rows.append(R['k4'])
    for a, b in zip(rows, rows[1:]):
        bridge(bm, a, b)
    cap(bm, rows[0])
    cap(bm, list(reversed(rows[-1])))
    recalc_normals(bm)

    # ---- ear tufts: the crown's outer-front quad, up and out to a blade tip
    k3, k4 = R['k3'], R['k4']
    old = [k3[SD], k3[FC], k4[FC], k4[SD]]
    faces = [face_of(old)]
    c = centre(old)
    tip = Vector(J['tufttipL'])
    base = [v.co.copy() for v in old]
    for f_, sx, sy in TUFT:
        cc = c.lerp(tip, f_)
        pts = [cc + Vector(((p.x - c.x) * sx, (p.y - c.y) * sy, (p.z - c.z) * sx)) for p in base]
        old, faces = ext(bm, faces, old, pts)

    # ---- legs: the belly-underside quad between r0 and b0 (FF..FC)
    r0, b0 = R['r0'], R['b0']
    old = [r0[FF], r0[FC], b0[FC], b0[FF]]                      # BI BO FO FI
    faces = [face_of(old)]
    for pts in LEG:
        top = old
        old, faces = ext(bm, faces, old, pts)
    ftop, fbot = top, old
    wall = lambda a, b: [ftop[a], ftop[b], fbot[b], fbot[a]]
    for a_, b_, dirn, L, tw1, th1, tw2, th2 in TOES:
        toe(bm, wall(a_, b_), dirn, L, tw1, th1, tw2, th2)

    # ---- wings: 2-face patch on the upper flank (rings b2 n0, faces FC..SD..BK)
    b2, n0 = R['b2'], R['n0']
    old = [n0[FC], n0[SD], n0[BK], b2[BK], b2[SD], b2[FC]]        # FO O BO BI I FI
    faces = [face_of([n0[FC], n0[SD], b2[SD], b2[FC]]), face_of([n0[SD], n0[BK], b2[BK], b2[SD]])]
    for pts in WING:
        old, faces = ext(bm, faces, old, pts)

    recalc_normals(bm)
    ob = object_from_bm('body', bm)
    if os.environ.get('OWL_DBG'):
        _dbg_hits(ob)
    return ob


def _dbg_hits(ob):
    from mathutils.bvhtree import BVHTree
    from bmkit import evaluated_bm
    b = evaluated_bm(ob)
    b.faces.ensure_lookup_table()
    t = BVHTree.FromBMesh(b)
    for i, j in t.overlap(t):
        if i < j and not (set(b.faces[i].verts) & set(b.faces[j].verts)):
            ci, cj = b.faces[i].calc_center_median(), b.faces[j].calc_center_median()
            say('HIT', tuple(round(x, 3) for x in ci), tuple(round(x, 3) for x in cj))


def vn(bm, name, i):
    return vert_near(bm, rp(name, i))


def en(bm, name, i, j):
    """The edge between vertices i and j of ring `name`."""
    a, b = vn(bm, name, i), vn(bm, name, j)
    return next(e for e in a.link_edges if e.other_vert(a) is b)


def stage2(k, body):
    bm = edit(body)
    # ---- facial disc: a loop just inside the rim (FC) from the cheek to the brow; the rim lip
    # stands forward of it, the dish (FF) sinks behind it: the ruff ring round each eye
    with k.topo(bm, 'partial_loop', 'facial-disc rim: a loop inside the rim, terminators in the cheek (k0-k1) and brow (k2-k3)'):
        rim = partial_loop(bm, en(bm, 'k0', FF, FC), en(bm, 'k3', FF, FC), t=0.28, near=vn(bm, 'k0', FC))
    for v in rim:
        v.co += Vector((0.004, -0.012, 0.0))
    # ---- neck: a full loop round the n0-k0 band so the head swivel has a middle ring; its front
    # half flares forward and out as the ruff under the disc, the back half is the nape
    with k.topo(bm, 'loop', 'neck loop between n0 and k0: the swivel ring and the ruff under the disc'):
        neck = loopcut(bm, edge_near(bm, (rp('n0', SD) + rp('k0', SD)) / 2), t=0.5)
    # fill the notch under the head so the head grows out of the body: the neck loop takes the
    # head's lower section (k0), the n0 ring swells toward it
    k0 = [vn(bm, 'k0', i) for i in range(6)]
    for v in neck:
        w = min(k0, key=lambda q: (q.co.xy - v.co.xy).length)
        v.co.x, v.co.y = v.co.x + (w.co.x - v.co.x) * 0.85, v.co.y + (w.co.y - v.co.y) * 0.85
    for i, d in ((T_, (0, 0.008, 0)), (BK, (0.006, 0.006, 0)), (SD, (0.006, 0, 0)), (FC, (0.006, -0.008, 0)),
                 (FF, (0.004, -0.010, 0)), (B_, (0, -0.010, 0))):
        vn(bm, 'n0', i).co += Vector(d)
    # ---- breast: the belly swells forward below the ruff and tucks under toward the legs; the
    # front of b1/b2 flattened to one breast plane each side (a deliberate facet, the belly colour)
    for nm, i, d in (('b1', B_, (0, -0.014, 0)), ('b1', FF, (0.004, -0.012, 0)), ('b2', B_, (0, -0.008, 0)),
                     ('b2', FF, (0.004, -0.006, 0)), ('b0', B_, (0, -0.006, 0.006)), ('b0', FF, (0, -0.004, 0.006))):
        vn(bm, nm, i).co += Vector(d)
    flatten([vn(bm, nm, i) for nm in ('b1', 'b2') for i in (FF, FC)])
    # ---- wing root (AD note 1): a loop half-way between the root patch and the shoulder section,
    # so the spread in the attack bends over two bands (weights blended in stage 4), not one
    with k.topo(bm, 'loop', 'wing-root loop: the shoulder bend, blended body/wing weights'):
        a_, b_ = vn(bm, 'n0', SD), vert_near(bm, WING[0][1])
        e = next(e for e in a_.link_edges if e.other_vert(a_) is b_)
        wl = loopcut(bm, e, t=0.5, near=a_)
    for v in wl:                     # the under-side strips are 1.7 cm deep: bulge the loop out so they
        if v.co.z < 0.315:           # do not split into needle triangles
            v.co += Vector((-0.002, 0.0, -0.004))
    # ---- AD note 2: blunt wing tips and a shorter, blunter tail (no needle slivers)
    tip = [vert_near(bm, p) for p in WING[-1]]
    for v, p in zip(tip, WING_TIP):
        v.co = Vector(p)
    for p in WING[3][:2]:            # the rump section's outer front/corner out 1 cm: a thicker lower edge
        v = vert_near(bm, p)
        d = Vector((v.co.x, v.co.y - 0.02, 0.0)).normalized()
        v.co += d * WING3_OUT
    # ---- AD note 4: the head is a box from behind — round the back corners onto an ellipse through
    # the back seam and the widest side, drop the top-back edge, dish the disc centre further back
    for nm in ('k0', 'k1', 'k2', 'k3'):
        v = vn(bm, nm, BK)
        v.co.x *= 0.88
    for nm, i, d in (('k3', T_, (0, -0.010, -0.012)), ('k3', BK, (0, -0.008, -0.010)),
                     ('k2', T_, (0, 0.004, 0)), ('k1', T_, (0, 0.004, 0))):
        vn(bm, nm, i).co += Vector(d)
    for i in (T_, BK):
        vert_near(bm, rp('k4', i)).co += Vector((0, -0.006, -0.008))
    for nm in ('k0', 'k1', 'k2'):
        vn(bm, nm, FF).co.y += 0.008
    # ---- AD note 5: tufts — a notch splits each blade tip in two (a feather clump, not a cat ear),
    # the tip thickened to 1.1 cm (no needle), the blade tilted 10 deg out
    S = [[vert_near(bm, p) for p in sec] for sec in tuft_sections()]
    for i, dy in ((0, 0.004), (1, -0.004), (2, -0.004), (3, 0.004)):
        S[2][i].co.y += dy
    edge = lambda a, b: next(e for e in a.link_edges if e.other_vert(a) is b)
    with k.topo(bm, 'partial_loop', 'tuft notch: a loop down the blade splits the tip in two; '
                'terminators in the flat of the blade (section 0.22-0.62), nothing bends there'):
        ms = partial_loop(bm, edge(S[0][1], S[0][2]), edge(S[0][0], S[0][3]), t=0.5)
    s1 = [m for m in ms if (m.co - centre_pts([v.co for v in S[1]])).length < (m.co - centre_pts([v.co for v in S[2]])).length]
    s2 = [m for m in ms if m not in s1]
    for m in s2:
        m.co = m.co.lerp(centre_pts([v.co for v in s1]), 0.45)
    piv = centre_pts([rp('k3', SD), rp('k3', FC), rp('k4', FC), rp('k4', SD)])
    rotate(S[0], (0, 1, 0), 5, piv)
    rotate(S[1] + S[2] + ms, (0, 1, 0), 10, piv)
    # R2 should-fix O3: in profile the tuft stood as one vertical horn — tilt it 15 deg back (the
    # first section half that) and shorten it 15% toward its root
    rotate(S[0], (1, 0, 0), -7, piv)
    rotate(S[1] + S[2] + ms, (1, 0, 0), -15, piv)
    scale(S[1] + S[2] + ms, 0.85, piv)
    # ---- AD note 6: feet — the toes narrowed (knuckle 0.75x, tip 0.6x: a taper) and the tips
    # lowered, so they read as digits, not a mitt
    for i, (a_, b_, dirn, L, w1, h1, w2, h2) in enumerate(TOES):
        c0 = (LEG[1][a_] + LEG[1][b_] + LEG[2][a_] + LEG[2][b_]) / 4
        c0.z = 0.0
        t = Vector((dirn[0], dirn[1], 0.0)).normalized()
        sv = Vector((-t.y, t.x, 0.0))
        if sv.dot(LEG[1][b_] - LEG[1][a_]) < 0:
            sv = -sv
        for frac, w, h, kw, kh in ((0.5, w1, h1, 0.75, 1.0), (1.0, w2, h2, 0.6, 0.8)):
            c = c0 + t * L * frac
            for p, sg, up in ((c - sv * w + Vector((0, 0, h)), -1, 1), (c + sv * w + Vector((0, 0, h)), 1, 1),
                              (c + sv * w, 1, 0), (c - sv * w, -1, 0)):
                v = vert_near(bm, p)
                assert (v.co - p).length < 1e-4, ('toe vert not found', i, frac)
                v.co = c + sv * (sg * w * kw) + Vector((0, 0, h * kh * up))
    t0, t1 = [vn(bm, 't0', i) for i in range(6)], [vn(bm, 't1', i) for i in range(6)]
    for a_, b_ in zip(t0, t1):
        a_.co = a_.co.lerp(b_.co, TAIL_IN)
    # ---- R2 note 4: the tail brick becomes a tapered fan — the tip ring thinned toward the top ridge
    # (T), the t1 ring a little; the centre ridge (T) stands, the outer feathers (SD) drop, and the
    # end is chamfered to a blunt point (the seam feather longer): 3 top facets, centre + 2 outer
    for ring_, k_ in ((t0, TAIL_THIN), (t1, TAIL_THIN1)):
        top = ring_[T_].co.z
        for v in ring_[1:]:
            v.co.z = top - (top - v.co.z) * k_
    for i, d in TAIL_TIP.items():
        t0[i].co += Vector(d)
    commit(body, bm)


PAL = {'body': '#8a6a48', 'dark': '#5e4632', 'wing': '#6e5238', 'disc': '#c9ad84', 'rim': '#3e2e22',
       'belly': '#d8c4a0', 'eye': '#f09a20', 'pupil': '#111111'}   # beak/talons share the rim's dark (8-colour cap)


def spike(bm, root, tip, side, w, t, mid=0.45, midw=1.1, bend=(0, 0, 0), tipw=0.0):
    """A faceted blade / claw / beak: diamond section at the root, a wider diamond at `mid`
    (pushed by `bend` for a curve), one point at the tip. Returns its faces."""
    root, tip = Vector(root), Vector(tip)
    ax = (tip - root).normalized()
    th = ax.cross(Vector(side)).normalized()
    sd = th.cross(ax).normalized()
    m = root.lerp(tip, mid) + Vector(bend)
    b = ring(bm, [root + sd * w, root + th * t, root - sd * w, root - th * t])
    mm = ring(bm, [m + sd * w * midw, m + th * t * midw, m - sd * w * midw, m - th * t * midw])
    fs = bridge(bm, b, mm, closed=True)
    if tipw:                         # a blunt end: a small diamond cap, not a needle point
        tp = ring(bm, [tip + sd * w * tipw, tip + th * t * tipw, tip - sd * w * tipw, tip - th * t * tipw])
        fs += bridge(bm, mm, tp, closed=True)
        fs.append(bm.faces.new(tp))
    else:
        tp = bm.verts.new(tip)
        fs += [bm.faces.new([mm[i], mm[(i + 1) % 4], tp]) for i in range(4)]
    fs.append(bm.faces.new(list(reversed(b))))
    return fs


def prism(bm, c, nrm, r, depth, n=8, up=(0, 0, 1), taper=0.9):
    """An n-sided disc facing nrm (front face at c, back face depth behind)."""
    c, nrm = Vector(c), Vector(nrm).normalized()
    u = Vector(up) - nrm * Vector(up).dot(nrm)
    u.normalize()
    w = nrm.cross(u)
    ang = [math.radians(90 + 360.0 * i / n) for i in range(n)]
    front = ring(bm, [c + (u * math.sin(a) + w * math.cos(a)) * r for a in ang])
    back = ring(bm, [c - nrm * depth + (u * math.sin(a) + w * math.cos(a)) * r * taper for a in ang])
    fs = bridge(bm, front, back, closed=True)
    fs.append(bm.faces.new(front))
    fs.append(bm.faces.new(list(reversed(back))))
    return fs


def piece(name, bm, keymap, mirror=True):
    """keymap: list of (faces, key). Object from bm, painted by face membership."""
    idx = {}
    bm.faces.index_update()
    for fs, key in keymap:
        for f in fs:
            idx[f.index] = key
    ob = object_from_bm(name, bm, mirror=mirror)
    paint(ob, {k_: PAL[k_] for k_ in sorted(set(idx.values()))}, lambda c, n, i: idx[i])
    return ob


def flood(bm, seed, stop):
    """Faces connected to `seed` without crossing an edge whose two verts are both in `stop`."""
    out, todo = {seed}, [seed]
    while todo:
        f = todo.pop()
        for e in f.edges:
            if e.verts[0] in stop and e.verts[1] in stop:
                continue
            for g in e.link_faces:
                if g not in out:
                    out.add(g)
                    todo.append(g)
    return out


WING_ROOT = [('n0', FC), ('n0', SD), ('n0', BK), ('b2', BK), ('b2', SD), ('b2', FC)]
LEG_ROOT = [('r0', FF), ('r0', FC), ('b0', FC), ('b0', FF)]
TUFT_ROOT = [('k3', SD), ('k3', FC), ('k4', FC), ('k4', SD)]


def regions(bm, mirror_x=1):
    """Face sets of the wing, leg and tuft on one side (x sign mirror_x)."""
    m = lambda p: Vector((p.x * mirror_x, p.y, p.z))
    stop = lambda root: {vert_near(bm, m(rp(r, i))) for r, i in root}
    tip = Vector(WING[-1][1])
    wing = flood(bm, face_near(bm, m(tip)), stop(WING_ROOT))
    leg = flood(bm, face_near(bm, m(Vector((0.075, -0.022, 0.0))), n=(0, 0, -1)), stop(LEG_ROOT))
    tuft = flood(bm, face_near(bm, m(Vector(J['tufttipL']))), stop(TUFT_ROOT))
    return wing, leg, tuft, stop(WING_ROOT) | stop(LEG_ROOT) | stop(TUFT_ROOT)


def surface(body, p, d):
    """First hit of a ray from p along d on the body (the evaluated, mirrored mesh)."""
    from mathutils.bvhtree import BVHTree
    from bmkit import evaluated_bm
    b = evaluated_bm(body)
    t = BVHTree.FromBMesh(b)
    hit, n, i, dist = t.ray_cast(Vector(p), Vector(d).normalized())
    b.free()
    return hit, n


def stage3(k, body):
    bm = edit(body)
    wing, leg, tuft, _ = regions(bm)
    key = {}
    for f in bm.faces:
        c, n = f.calc_center_median(), f.normal
        if f in wing:
            key[f.index] = 'wing'
        elif f in tuft:
            key[f.index] = 'dark'
        elif f in leg:
            key[f.index] = 'belly'
        elif c.z > 0.34 and n.y < -0.3:                       # the face
            if c.z < 0.368:                                   # under the disc: the rim's lower corners,
                # R2 should-fix O2: no full-width pale band — a narrow bib point under the beak, the
                # disc colour closing the disc above it, the dark rim corners wider (a rounded bottom)
                key[f.index] = 'rim' if c.x > 0.095 else ('belly' if c.x < 0.045 else 'disc')   # AD note 7: outer corners,
                # continuing the side rim down the cheek; the pale throat bib runs between them
            elif c.z > 0.505:
                key[f.index] = 'rim'                           # brow V above
            elif c.x < 0.122:
                key[f.index] = 'disc'
            else:
                key[f.index] = 'rim'                           # the rim lip round each dish
        elif c.z <= 0.34 and (n.y < -0.35 or n.z < -0.55) and c.y < 0.06:
            key[f.index] = 'belly'
        elif c.z <= 0.34 and (n.y > 0.3 or c.y > 0.15):
            key[f.index] = 'dark'                              # back between the wings, the tail
        else:
            key[f.index] = 'body'
    bm.free()
    paint(body, {k_: PAL[k_] for k_ in sorted(set(key.values()))}, lambda c, n, i: key[i])
    pieces = []

    # ---- eyes: huge orange discs on the dish, black pupil ahead and a touch down, a pale glint
    b = bmesh.new()
    ex, ez = 0.066, 0.462
    hit, hn = surface(body, (ex, -0.4, ez), (0, 1, 0))
    look = Vector((0.10, -1.0, -0.04)).normalized()
    # AD note 3: seated in the dish — the iris 4 mm proud (clear of z-fight), its back 12 mm in; the
    # pupil 2 mm proud of the iris, rooted in it; the glint sunk half into the pupil
    ec = hit + look * 0.007           # r67: 7 mm proud so the deeper dish (note 4) does not bury the ring
    iris = prism(b, ec, look, 0.044, 0.019, n=8)
    pc = ec + look * 0.002 + Vector((0.002, 0, -0.003))
    pup = prism(b, pc, look, 0.025, 0.005, n=8)
    glint = prism(b, pc + look * 0.0015 + Vector((0.010, 0, 0.010)), look, 0.007, 0.003, n=4)
    pieces.append(piece('eye', b, [(iris, 'eye'), (pup, 'pupil'), (glint, 'belly')]))

    # ---- beak: a small hooked wedge pointing down between the eyes, its root buried in the ridge
    b = bmesh.new()
    hit, _ = surface(body, (0.0005, -0.4, 0.44), (0, 1, 0))
    root = Vector((0.0, hit.y + 0.012, 0.448))
    bk = spike(b, root, root + Vector((0, -0.028, -0.064)), (1, 0, 0), 0.016, 0.02, mid=0.4, midw=1.0,
               bend=(0, -0.020, 0.006))       # AD note 7: the mid bulges forward, the tip curls back: a hook
    pieces.append(piece('beak', b, [(bk, 'rim')], mirror=False))

    # ---- brow: a dark wedge per eye from the beak root up and out to the tuft, front end low
    # AD note 5: tucked 60% into the brow (centre line 2-3 mm off the surface, 12 mm thick) and
    # 25% shorter, so it reads as a brow ridge, not a horn, in az090
    b = bmesh.new()
    h0, _ = surface(body, (0.014, -0.4, 0.478), (0, 1, 0))
    # R2 note 3: seated into the disc (centre line 3-4 mm INSIDE the surface: ~40% more buried), the
    # outer end pulled in to x 0.092 (inside the disc edge) and blunted to a 30%-wide cap (20% split into slivers)
    h1, _ = surface(body, (0.092, -0.4, 0.519), (0, 1, 0))
    br = spike(b, h0 + Vector((0, 0.003, 0)), h1 + Vector((0, 0.004, 0)), (0, 0, 1), 0.014, 0.012,
               mid=0.58, midw=1.2, bend=(0, -0.002, 0.003), tipw=0.3)
    pieces.append(piece('brow', b, [(br, 'rim')]))

    # ---- talons: one hooked claw per toe
    b = bmesh.new()
    cl = []
    for i in range(4):
        tp, t = toe_tip(i)
        r0 = tp + Vector((0, 0, 0.012)) - t * 0.010
        cl += spike(b, r0, r0 + t * 0.035 + Vector((0, 0, -0.014)), (0, 0, 1), 0.009, 0.009, mid=0.45,
                    midw=0.9, bend=(0, 0, 0.008))
    pieces.append(piece('talons', b, [(cl, 'rim')]))
    return pieces


BONES = [('hips', J['hips'], J['chest'], None),
         ('chest', J['chest'], J['neck'], 'hips', True),
         ('neck', J['neck'], J['head'], 'chest', True),
         ('head', J['head'], J['crown'], 'neck', True),
         ('tail', J['tail0'], J['tail1'], 'hips'),
         ('thigh.L', J['hipL'], J['kneeL'], 'hips'),
         ('shin.L', J['kneeL'], J['ankleL'], 'thigh.L', True),
         ('foot.L', J['ankleL'], J['toeL'], 'shin.L', True),
         ('arm.L', J['shoulderL'], J['wristL'], 'chest'),
         ('hand.L', J['wristL'], J['handL'], 'arm.L', True),
         ('tip.L', J['handL'], J['tipL'], 'hand.L', True)]


def _clean_weights(body, rig):
    """Bone heat bleeds the folded wing into the flank (1-2 cm apart) and the legs into the belly:
    wing bones only on wing verts, leg bones below the hip only on leg verts."""
    bm = edit(body)
    sets = {}
    for sx, sd in ((1, 'L'), (-1, 'R')):
        wing, leg, tuft, stop = regions(bm, sx)
        sets['wing.' + sd] = {v.index for f in wing for v in f.verts} - {v.index for v in stop}
        sets['leg.' + sd] = {v.index for f in leg for v in f.verts} - {v.index for v in stop}
    bm.free()
    wing_b = {s: {'arm.' + s, 'hand.' + s, 'tip.' + s} for s in 'LR'}
    leg_b = {s: {'shin.' + s, 'foot.' + s} for s in 'LR'}
    gname = {g.index: g.name for g in body.vertex_groups}
    segs = _bone_segments(rig)
    for v in body.data.vertices:
        allowed = set(segs)
        for s_ in 'LR':
            if v.index in sets['wing.' + s_]:
                allowed = wing_b[s_] | {'chest'}
                break
            if v.index in sets['leg.' + s_]:
                allowed = leg_b[s_] | {'thigh.' + s_, 'hips'}
                break
        else:
            allowed -= wing_b['L'] | wing_b['R'] | leg_b['L'] | leg_b['R']
        for g in list(v.groups):
            if gname[g.group] not in allowed and g.weight > 0:
                body.vertex_groups[gname[g.group]].remove([v.index])
        if sum(g.weight for g in v.groups if gname[g.group] in segs) <= 1e-4:
            p_ = body.matrix_world @ v.co
            nm = min(allowed & set(segs), key=lambda n: _seg_dist(p_, *segs[n]))
            vg = body.vertex_groups.get(nm) or body.vertex_groups.new(name=nm)
            vg.add([v.index], 1.0, 'REPLACE')


def _blend_wing_root(body):
    """AD note 1: the wing-root loop takes 50% wing / 50% chest, the shoulder section 80/20, so
    the spread bends across two bands instead of folding the one short band at the root."""
    bm = edit(body)
    rings = {}
    for sx, sd in ((1, 'L'), (-1, 'R')):
        m = lambda p: Vector((p.x * sx, p.y, p.z))
        root = {vert_near(bm, m(rp(r, i))) for r, i in WING_ROOT}
        wing = regions(bm, sx)[0]
        wv = {v for f in wing for v in f.verts} - root
        r1 = {e.other_vert(v) for v in root for e in v.link_edges} & wv
        r2 = ({e.other_vert(v) for v in r1 for e in v.link_edges} & wv) - r1
        rings[sd] = ([v.index for v in root], [v.index for v in r1], [v.index for v in r2])
    bm.free()
    for sd, (r0, r1, r2) in rings.items():
        for idx, w in ((r0, 0.0), (r1, 0.5), (r2, 0.8)):   # the root ring rides the chest only
            for g in body.vertex_groups:
                g.remove(idx)
            if w > 0:
                body.vertex_groups['arm.' + sd].add(idx, w, 'REPLACE')
            body.vertex_groups['chest'].add(idx, 1.0 - w, 'REPLACE')
    say('wing-root blend', {sd: tuple(len(x) for x in r) for sd, r in rings.items()})


def _blend_neck(body):
    """R2 note 2: bone heat left the neck loop 100% head and n0 100% chest, so the whole head turn
    folded the one band between them (flips at the nape and the shoulder). The neck loop now takes
    50% head / 50% neck and n0's free verts (T, FF, B) 20% neck / 80% chest; n0's wing-root verts
    (FC, SD, BK) keep riding the chest (AD r1 note 1)."""
    bm = edit(body)
    loop, low = set(), set()
    for sx in (1, -1):
        m = lambda p: Vector((p.x * sx, p.y, p.z))
        for i in range(6):
            kv = vert_near(bm, m(rp('k0', i)))
            loop.add(min((e.other_vert(kv) for e in kv.link_edges), key=lambda q: q.co.z).index)
        for i in (T_, FF, B_):
            nv = vert_near(bm, m(rp('n0', i)))
            assert (nv.co - m(rp('n0', i))).length < 0.02
            low.add(nv.index)
    bm.free()
    for idx, (wh, wn, wc) in ((sorted(loop), (0.5, 0.5, 0.0)), (sorted(low), (0.0, 0.2, 0.8))):
        for g in body.vertex_groups:
            g.remove(idx)
        for nm, w in (('head', wh), ('neck', wn), ('chest', wc)):
            if w > 0:
                (body.vertex_groups.get(nm) or body.vertex_groups.new(name=nm)).add(idx, w, 'REPLACE')
    say('neck blend', len(loop), 'loop verts', len(low), 'n0 verts')


def sym(keys):
    """Mirror every .L key onto .R (X kept, Y and Z negated) unless .R is given."""
    out = {}
    for f, d in keys.items():
        e = dict(d)
        for b_, r in d.items():
            if b_.endswith('.L') and b_[:-2] + '.R' not in d:
                e[b_[:-2] + '.R'] = (r[0], -r[1], -r[2])
        out[f] = e
    return out


def stage4(k, body, pieces):
    rig = armature(BONES)
    skin(body, rig)
    _clean_weights(body, rig)
    _blend_wing_root(body)
    _blend_neck(body)
    P = {p.name.replace('piece_', ''): p for p in pieces}
    for nm in ('eye', 'beak', 'brow'):
        bind(P[nm], rig, body=body)      # R2 note 1: the face skin's own weights (no drift)
    bind(P['talons'], rig, body=body)

    # idle: the owl's head swivel — a long look over the left shoulder, hold, back, a tilt the
    # other way, a quick bob (the blink beat); breathing in the chest
    clip(rig, 'idle', {1: {},
                       8: {'neck': (0, 4, 0), 'head': (0, 64, 0), 'chest': (-2, 0, 0)},
                       18: {'neck': (0, 4, 0), 'head': (0, 70, 4), 'chest': (-3, 0, 0)},
                       26: {'chest': (-1, 0, 0)},
                       32: {'neck': (0, -4, 0), 'head': (0, -20, -6), 'chest': (-2, 0, 0)},
                       38: {'neck': (0, -4, 0), 'head': (8, -20, -6)},
                       42: {'head': (0, 0, 0), 'chest': (-1, 0, 0)},
                       48: {}})

    # move: a sidestep hop along the perch and back, wings flicking out for balance
    def hop(crouch, wing):
        return sym({0: {'thigh.L': (-crouch, 0, 0), 'shin.L': (crouch * 1.4, 0, 0), 'foot.L': (-crouch * 0.4, 0, 0),
                        'chest': (crouch * 0.3, 0, 0), 'arm.L': (0, 0, -wing), 'hand.L': (0, 0, -wing * 0.5)}})[0]
    keys = {1: {}, 4: hop(18, 0), 7: hop(-4, 28), 10: hop(16, 6), 13: {},
            16: hop(18, 0), 19: hop(-4, 28), 22: hop(16, 6), 25: {}}
    loc = {1: {'hips': (0, 0, 0)}, 4: {'hips': (0, -0.012, 0)}, 7: {'hips': (0.035, 0.04, 0)},
           10: {'hips': (0.07, -0.01, 0)}, 13: {'hips': (0.07, 0, 0)}, 16: {'hips': (0.07, -0.012, 0)},
           19: {'hips': (0.035, 0.04, 0)}, 22: {'hips': (0.0, -0.01, 0)}, 25: {'hips': (0, 0, 0)}}
    clip(rig, 'move', keys, loc=loc)

    # attack: rear up with the wings flaring open, then a forward lunge with the talons thrown
    # forward, wings still spread; recover
    clip(rig, 'attack', sym({1: {},
                             8: {'chest': (-12, 0, 0), 'head': (8, 0, 0), 'arm.L': (0, 0, -18), 'hand.L': (0, 0, -45),
                                 'tip.L': (0, 0, -15), 'tail': (-12, 0, 0)},
                             14: {'hips': (8, 0, 0), 'chest': (5, 0, 0), 'neck': (-4, 0, 0), 'head': (-8, 0, 0),
                                  'arm.L': (0, 10, -25), 'hand.L': (0, 0, -60), 'tip.L': (0, 0, -25),
                                  'thigh.L': (-70, 0, 0), 'shin.L': (20, 0, 0), 'foot.L': (-30, 0, 0),
                                  'tail': (15, 0, 0)},
                             20: {'hips': (6, 0, 0), 'chest': (4, 0, 0), 'head': (-6, 0, 0),
                                  'arm.L': (0, 5, -22), 'hand.L': (0, 0, -50), 'tip.L': (0, 0, -15),
                                  'thigh.L': (-40, 0, 0), 'shin.L': (15, 0, 0), 'foot.L': (-15, 0, 0)},
                             32: {}}),
         loc={1: {'hips': (0, 0, 0)}, 8: {'hips': (0, 0.0, 0.02)}, 14: {'hips': (0, 0.045, 0.06)},
              20: {'hips': (0, 0.02, 0.05)}, 32: {'hips': (0, 0, 0)}})   # local Y = up, local Z = forward
    if os.environ.get('OWL_FLIPDBG'):
        _flip_dbg(k, body, pieces, rig)
    return rig


def _flip_dbg(k, body, pieces, rig):
    """Debug only (env OWL_FLIPDBG): posed fold-overs per clip and where they are, then exit."""
    import techqa as Q
    _dbg_hits(body)
    for o in [body] + list(pieces):
        Q.triangulate_convex(o, keep=k.meta.get('keep_valleys'))
    acts = {a_.name: a_ for a_ in bpy.data.actions}
    vf = frame_of([body] + list(pieces), k.frame)
    V = [body.matrix_world @ v.co for v in body.data.vertices]
    for nm in ('idle', 'move', 'attack'):
        rest(rig); bpy.context.scene.frame_set(1)
        counts, flags, tris = Q.measure(body, pieces, vf['size'], rig, {nm: acts[nm]})
        say('FLIPDBG', nm, {o: c['flip'] for o, c in counts.items() if c['flip']},
            'sliver', {o: c['sliver'] for o, c in counts.items() if c['sliver']})
        for p, cls in sorted(flags['body'].items()):
            if cls == 'flip':
                c = sum((V[i] for i in body.data.polygons[p].vertices), Vector()) / len(body.data.polygons[p].vertices)
                say('   flip', p, tuple(round(x, 3) for x in c))
                for vi in body.data.polygons[p].vertices:
                    say('      v', vi, tuple(round(x, 3) for x in V[vi]),
                        {body.vertex_groups[g.group].name: round(g.weight, 2) for g in body.data.vertices[vi].groups if g.weight > 0.01})
    rest(rig); bpy.context.scene.frame_set(1)
    counts, flags, tris = Q.measure(body, pieces, vf['size'])
    for o in flags:
        ob = bpy.data.objects[o]
        for p, cls in sorted(flags[o].items()):
            if cls in ('sliver', 'float'):
                pv = ob.data.polygons[p].vertices
                c = sum((ob.matrix_world @ ob.data.vertices[i].co for i in pv), Vector()) / len(pv)
                say('   ', cls, o, p, tuple(round(x, 3) for x in c),
                    [tuple(round(x, 3) for x in ob.matrix_world @ ob.data.vertices[i].co) for i in pv])
    sys.stdout.flush()
    os._exit(0)


run(META, stage1, stage2, stage3, stage4)
