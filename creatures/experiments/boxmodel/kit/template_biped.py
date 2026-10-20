"""template_biped.py: the kit-owned BIPED topology template for the stage-1 cage (research/topology_aaa_*.md, 2.1 / 2.2),
the counterpart of the quadruped in template.py (whose Topo, Tab and quad_warp it imports read-only).

    tm = body_template('biped', counts)              # ALL connectivity, by box operations only
    spec = biped_spec(tm, k, offsets=OFFSETS)        # what the fit reads besides the guide (defaults from J, landmarks)
    body = fit_template(tm, k, guide, spec)          # every named vertex placed from the guide

The creature program authors no topology: J, the plan (limbs named 'arm' and 'leg'), COUNTS, OFFSETS and landmarks.

CONNECTIVITY (body_template). Two boxes (torso, head) joined by a bridge; every branch by `grow` (inset, then extrude):
  torso  16 sides. Rows bottom -> top: 0 the hip loop, 1 belt, trunk_mid rows (belly, waist, chest), armpit, shoulder,
         crest. Half-ring 0..8: 0 sternum / belly seam, 1 rectus edge, 2 pec side, 3 front-side corner (box corner),
         4 lateral line, 5 back-side corner (box corner), 6 scapula line, 7 spine flank, 8 spine seam.
         Bottom cap 3 x 2 per half (the pelvis floor): its seam column is the crotch strip, its outer 2 x 2 the leg
         block. Top cap 3 x 2 per half: its seam column is the neck hole, its outer two columns the trapezius.
  leg    8 sides from the pelvis floor's outer 2 x 2, inset once (the hip loop: its groin and crotch-glute corners are
         the only poles, the box corners take the other two). Rings: cap, thigh mass, knee x3, calf mass, ankle x2,
         then the ring turns forward: heel (45 degrees), arch, ball, toe; the block closes the toe with 2 x 2.
  arm    8 sides from the 2 x 2 block on the side face under the crest (the shoulder loop: its top edge is the crest,
         so the trapezius columns run on into the deltoid; pec-armpit and lat-armpit corners are the poles). Rings:
         deltoid cap, upper-arm mass, elbow x3, forearm mass, wrist x2, palm x2, knuckle, finger; the block closes
         the finger end with 2 x 2.
  thumb  4 sides from one palm face (the medial-front face between the last two palm rings).
  neck   8 sides: the crest's hole bridged to the head's hole (the rear 1 x 2 of the jaw floor per half).
  head   18 sides. Half-ring 0..9: 0 front seam, 1 nose / mouth side, 2, 3 the eye line (box corner), 4, 5, 6 back
         corner, 7, 8, 9 back seam. Level rings bottom -> top: 0 jaw line, 1 lower lip, 2 mouth line, 3 upper lip,
         4 cheek line, 5 eye line, 6 brow line, forehead rings, crown; caps 3 x 3 per half (the jaw floor carries the
         neck hole). The lower rings lean (front low): the jaw line rises from the chin to the nape.
  eye    an 8-vertex loop: the 2 x 2 block (columns 2-3, rings 4-6) inset once. No eye geometry.
  mouth  an 8-vertex loop: the seam column's 1 x 2 block on rings 1-3, inset once. The jaw chain: ring 2 (the mouth
         line) runs from the loop's corner round the cheek to the nape, ring 0 (the jaw line) from the chin to the
         nape under the ear; the cheek line (ring 4) joins the nose root to the ear's lower corner.
  nose   8 sides from the seam column's 1 x 2 block on rings 4-6 (its top edge on the brow line), `nose` rings.
  ear    6 sides from the 1 x 2 block on the side (column 5, rings 5-7), `ear` rings to the tip.
Every vertex has a name (part, ring, point); rings and loops are named lists (tm.rings, tm.loops). tm.signature() is
the template's identity; template_biped_signatures.json stores the reviewed one per (kind, counts).

FIT (fit_template). Torso and head rings on the corners of the guide's level sections (carve.section_corners, half
rings from the front seam), limb rings on the corners of the limb sections in a frame carried down the chain (each
ring's vertex k takes the section slot whose angle matches the socket border's vertex k), hinge rings converging on
the flexion side, socket and cap rings fanned from the border to the first free ring on the guide, the neck bridge on
the guide, caps by Coons patch then projected, eye / mouth / ear loops pinned to META['landmarks'], then the named
offsets (clamped) and a capped planarity pass. No generic shrink-wrap.

KNOBS (the program's module-level COUNTS and OFFSETS dict literals; what a sweep varies; sensible ranges):
  COUNTS  trunk_mid 2-4 (rows between the belt and the armpit)   neck 1-3 (bridge rings)   head 9-11 (9 is the floor:
          jaw, 2 lip rings and the mouth line, cheek, eye, brow, forehead, crown; more = forehead / cranium rings)
          nose 2-4   ear 3-6
          arm / leg: cap 0-2 (rings between the socket and the first free ring: deltoid / thigh top), mass (upper,
          lower) 0-1 each, hinge (3, 2) (3 converging rings at elbow / knee, 2 at wrist / ankle), arm palm 2-3,
          finger 1-2, thumb 1-3 (rings), leg arch 1-2
  OFFSETS plane breaks, x the local width, clamped to +-OFFSET_CLAMP: brow 0-0.08, cheek 0-0.08, jaw 0-0.06,
          chin 0-0.08, trapezius 0-0.08, deltoid 0-0.12, pec 0-0.06, scapula 0-0.06, belly 0-0.08, glute 0-0.08
          form knobs (FORM below; not clamped):
          ear_cup    0-0.4    the ear's middle line pushed back x the ear's height: a cupped, chevron section
          ear_thin   0.5-2.0  the ear's thickness x the guide's
          neck_in    0.75-1.0 the neck rings x the guide's section (a thinner neck than its two holes)
          head_lean  0-1.5    the lower head rings' lean x the default (the jaw line's rise to the nape)
          mouth_in   0-0.03   metres the mouth's centre line sinks behind the lip loop
          ear_size   0.8-1.5  the ear's height (its broad side) x the guide's
          shoulder_drop 0-0.06 metres the crest ring drops toward the shoulder tip (the trapezius slope from the neck)
          hand_scale 0.8-1.6  palm, knuckle and finger rings x the guide's hand section (the guide reads one finger row)
          toe_spread 0.9-1.3  the ball and toe rings' width x the guide's (splayed toes)
          (arm fingers 0 or 2: the hand's end block grown as two 6-sided finger blocks, finger_rings rings each)
          leg_root, arm_root 1.0-1.4  the first mass ring (thigh / upper arm) x this in its plane, easing to x 1 at the
                              last fair ring (ankle / forearm): the reference's taper from a thick thigh to a thin ankle
          thumb_len  0.8-1.5  the thumb's length x its socket face's size
          finger_len 0.03-0.1 metres the finger blocks run past the hand's last ring
          finger_split 0-0.6  the finger ring's two broad-side middles pulled in: two finger bundles, not a mitten
          neck_flare 0.34-0.7 how far out the jaw floor's neck hole sits (x the floor's half width): the neck's top
                              flares into the skull instead of leaving a flat shelf round it
          torso_fair 0-4      shrink-free (Taubin) passes along the torso's lengthwise lines: adjacent rings fair into
                              one convex progression instead of alternating light / dark bands
          jaw_tuck   0-1      the lower head rings behind the ear pulled in toward the neck's width: the jaw line
                              closes under the chin and runs back to the ear, the nape runs on into the neck (no collar)
          crown_round 0-1     the rings above the brow and the skull cap on an ellipsoid from the brow ring to the
                              guide's top (a round cranium; the guide's visual hull is flat-topped)
          limb_fair  0-1      the limb rings from the first mass ring to the wrist / ankle: no ring dips under the line
                              of its neighbours (per slot), so no pinch at the knee or elbow and a straight shin column
"""
import hashlib, json, math, os
from template import Topo, Tab, quad_warp

SIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'template_biped_signatures.json')
SIDES = dict(biped=dict(torso=16, neck=8, head=18, limb=8, thumb=4, nose=8, ear=6, eye=8, mouth=8))
COUNTS = dict(biped=dict(
    trunk_mid=3,             # torso rows between the belt and the armpit (belly, waist, chest)
    neck=2,                  # bridge rings between the crest's hole and the head's
    head=9,                  # head level rings (9 is the floor, see KNOBS)
    nose=3, ear=4,           # rings after the socket loop
    arm=dict(cap=1, mass=(1, 1), hinge=(3, 2), palm=2, finger=1, thumb=2),
    leg=dict(cap=1, mass=(1, 1), hinge=(3, 2), arch=1),
))
OFFSET_CLAMP = 0.25
FORM = dict(ear_cup=0.0, ear_thin=1.0, ear_size=1.0, neck_in=1.0, head_lean=1.0, mouth_in=0.012, shoulder_drop=0.0,
            hand_scale=1.0, toe_spread=1.0, finger_split=0.0, neck_flare=0.34,
            torso_fair=0.0, jaw_tuck=0.0, crown_round=0.0, limb_fair=0.0, finger_len=0.05,
            leg_root=1.0, arm_root=1.0, thumb_len=1.5)


class BTopo(Topo):
    """Topo with the biped's side table and its own signature file (template.py stays untouched)."""

    def signature(self):
        val = self.valence()
        hist = {}
        for x in val:
            hist[str(x)] = hist.get(str(x), 0) + 1
        faces = sorted(sorted(str(self.names[v]) for v in f) for f in self.F)
        d = dict(kind=self.kind, verts=len(self.names), seam=len(self.seam), faces=len(self.F), valence=hist,
                 loops={n: len(v) for n, v in sorted(self.loops.items())}, sides=SIDES[self.kind],
                 rings=len(self.rings), conn=hashlib.sha256(json.dumps(faces).encode()).hexdigest()[:16])
        return d, hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()[:16]

    def stored_signature(self):
        if os.path.exists(SIG_FILE):
            return json.load(open(SIG_FILE)).get(self.key(), {}).get('hash')
        return None

    def store_signature(self):
        S = json.load(open(SIG_FILE)) if os.path.exists(SIG_FILE) else {}
        d, h = self.signature()
        S[self.key()] = dict(d, hash=h)
        with open(SIG_FILE, 'w') as f:
            json.dump(S, f, indent=1, sort_keys=True)
        return h


def limb_roles(c, end):
    """Ring roles of a limb after its socket loop: [cap], per inner joint [mass] + hinge rings, then the hand or foot."""
    out = ['cap'] * c.get('cap', 1)
    for b, h in enumerate(c['hinge']):
        out += ['mass'] * c['mass'][b] + [('hinge', b, i) for i in range(h)]
    if end == 'hand':
        out += ['palm'] * c.get('palm', 2) + ['knuckle'] + ['finger'] * c.get('finger', 1)
    else:
        out += ['heel'] + ['arch'] * c.get('arch', 1) + ['ball', 'toe']
    return out


def _cap(t, part, ring, na, nb, top, skip=()):
    """A half grid na (across) x nb (front -> back) whose border is the half ring (front seam .. back seam); skip:
    grid faces left out (a hole). Interior vertices are (part, a, b)."""
    path = [(a, 0) for a in range(na + 1)] + [(na, b) for b in range(1, nb + 1)] + [(a, nb) for a in range(na - 1, -1, -1)]
    assert len(path) == len(ring)
    g = dict(zip(path, ring))
    cells = [(a, b) for a in range(na) for b in range(nb) if (a, b) not in skip]
    for a, b in cells:
        for p in ((a, b), (a + 1, b), (a + 1, b + 1), (a, b + 1)):
            if p not in g:
                g[p] = t.v((part, p[0], p[1]), seam=p[0] == 0)
    for a, b in cells:
        q = [g[(a, b)], g[(a + 1, b)], g[(a + 1, b + 1)], g[(a, b + 1)]]
        t.f(q if top else [q[0], q[3], q[2], q[1]], key=(part, a, b))
    t.caps[part] = dict(grid=g, na=na, nb=nb)
    return g


def body_template(kind='biped', counts=None):
    """The biped topology template. counts overrides COUNTS['biped'] (one level deep for arm / leg)."""
    if kind != 'biped':
        raise ValueError("template_biped builds 'biped' only (the quadruped is kit/template.py)")
    if (counts or {}).get('sides'):
        raise ValueError(f"side counts are fixed by the template: {SIDES[kind]}")
    C = {}
    for k_, v in COUNTS[kind].items():
        o = (counts or {}).get(k_)
        C[k_] = dict(v, **o) if isinstance(v, dict) and isinstance(o, dict) else (v if o is None else o)
    assert C['head'] >= 9, 'the head needs 9 rings (jaw, lips and mouth line, cheek, eye, brow, forehead, crown)'
    assert C['neck'] >= 1 and C['arm'].get('palm', 2) >= 2, 'neck >= 1 ring; palm >= 2 rings (the thumb socket sits between them)'
    t = BTopo(kind, C)
    t.caps = {}
    R = 5 + C['trunk_mid']
    t.rows = dict(n=R, arm=R - 2)
    V = lambda i, j: t.id[('torso', i, j)]
    for i in range(R):
        for j in range(9):
            t.v(('torso', i, j), seam=j in (0, 8))
    for i in range(R - 1):
        for j in range(8):
            t.f([V(i, j), V(i, j + 1), V(i + 1, j + 1), V(i + 1, j)], key=('torso', i, j))
    for i in range(R):
        t.rings[('torso', i)] = [V(i, j) for j in range(9)]
    gpv = _cap(t, 'pelvis', t.rings[('torso', 0)], 3, 2, top=False)
    gc = _cap(t, 'crest', t.rings[('torso', R - 1)], 3, 2, top=True, skip={(0, 0), (0, 1)})
    NH = C['head']
    W = lambda L, j: t.id[('head', L, j)]
    for L in range(NH):
        for j in range(10):
            t.v(('head', L, j), seam=j in (0, 9))
    for L in range(NH - 1):
        for j in range(9):
            t.f([W(L, j), W(L, j + 1), W(L + 1, j + 1), W(L + 1, j)], key=('head', L, j))
    for L in range(NH):
        t.rings[('head', L)] = [W(L, j) for j in range(10)]
    _cap(t, 'skull', t.rings[('head', NH - 1)], 3, 3, top=True)
    gj = _cap(t, 'jaw', t.rings[('head', 0)], 3, 3, top=False, skip={(0, 1), (0, 2)})
    # the neck: a bridge of quads between the crest's hole and the jaw floor's hole (both seam -> seam, front -> back)
    A = [gc[(0, 0)], gc[(1, 0)], gc[(1, 1)], gc[(1, 2)], gc[(0, 2)]]
    Bp = [gj[(0, 1)], gj[(1, 1)], gj[(1, 2)], gj[(1, 3)], gj[(0, 3)]]
    rows = [A] + [[t.v(('neck', q, k_), seam=k_ in (0, 4)) for k_ in range(5)] for q in range(C['neck'])] + [Bp]
    for q in range(len(rows) - 1):
        a, b = rows[q], rows[q + 1]
        for k_ in range(4):
            t.f([a[k_], a[k_ + 1], b[k_ + 1], b[k_]], key=('neck', q, k_))
    for q in range(C['neck']):
        t.rings[('neck', q)] = rows[q + 1]
    t.loops.update({'neck.border': A, 'neck.socket': rows[1], 'neck.head': Bp})
    F = lambda *key: t.fid[key]

    def branch(name, faces, n, start=None):
        ring, border = t.grow(faces, name, 0, start)
        t.loops[name + '.border'], t.loops[name + '.socket'] = border, ring
        for r in range(1, n + 1):
            ring, _ = t.grow(faces, name, r, ring[0])
        return ring

    roles = limb_roles(C['leg'], 'foot')
    t.limbs['leg'] = dict(roles=roles, end='foot', inner=[gpv[(1, 1)], V(0, 1), V(0, 7)])
    branch('leg', [F('pelvis', 1, 0), F('pelvis', 2, 0), F('pelvis', 1, 1), F('pelvis', 2, 1)], len(roles), V(0, 4))
    t.rename(('pelvis', 2, 1), ('leg', 'cap', 0))
    roles = limb_roles(C['arm'], 'hand')
    t.limbs['arm'] = dict(roles=roles, end='hand', inner=[V(R - 3, 3), V(R - 3, 4), V(R - 3, 5)])
    branch('arm', [F('torso', R - 3, 3), F('torso', R - 3, 4), F('torso', R - 2, 3), F('torso', R - 2, 4)], len(roles), V(R - 1, 4))
    t.rename(('torso', R - 2, 4), ('arm', 'cap', 0))
    rp = roles.index('palm') + C['arm'].get('palm', 2)                 # ring index of the last palm ring
    bd = t.loops['arm.border']
    ka, kb = bd.index(V(R - 3, 4)), bd.index(V(R - 3, 3))               # the armpit's medial-front edge, carried down
    branch('thumb', [F('arm', rp, min(ka, kb) if abs(ka - kb) == 1 else max(ka, kb))], C['arm'].get('thumb', 2))
    t.fingers = []
    for q, blk in enumerate(([(R - 3, 3), (R - 2, 3)], [(R - 3, 4), (R - 2, 4)])[:C['arm'].get('fingers', 0)]):
        branch('finger%d' % q, [F('torso', *rc) for rc in blk], C['arm'].get('finger_rings', 2))   # the hand's end block, split
        t.fingers.append('finger%d' % q)
    # the face: mouth and eye loops (inset once), the nose and the ear (inset, then extruded)
    ring, border = t.grow([F('head', 1, 0), F('head', 2, 0)], 'mouth', 0)
    t.loops['mouth.border'], t.loops['mouth'] = border, ring
    t.rename(('head', 2, 0), ('mouth', 'centre', 0))
    branch('nose', [F('head', 4, 0), F('head', 5, 0)], C['nose'])
    t.rename(('head', 5, 0), ('nose', 'cap', 0))
    ring, border = t.grow([F('head', 4, 2), F('head', 4, 3), F('head', 5, 2), F('head', 5, 3)], 'eye', 0)
    t.loops['eye.border'], t.loops['eye'] = border, ring
    t.rename(('head', 5, 3), ('eye', 'centre', 0))
    branch('ear', [F('head', 5, 5), F('head', 6, 5)], C['ear'])
    t.ear_mid = [W(6, 5), W(6, 6)]                                      # the ear's middle line (front, back) on its border
    t.lines = dict(jaw=t.rings[('head', 0)], mouth=t.rings[('head', 2)], cheek=t.rings[('head', 4)], brow=t.rings[('head', 6)],
                   lateral=[t.rings[("torso", i)][4] for i in range(R)], sternum=[V(i, 0) for i in range(R)], spine=[V(i, 8) for i in range(R)])
    t.check()
    return t


def _at_z(tab, z):
    import numpy as np
    zs = tab.c[:, 2]
    o = np.argsort(zs)
    return tab.at(float(np.interp(z, zs[o], tab.t[o])))


def biped_spec(tm, k, **over):
    """What the fit reads besides the guide, defaults from J, the guide's parts and META['landmarks']. A program
    overrides any of:
      torso        [(z, lean degrees)] per torso ring (lean +: the front lower)
      torso_fracs  per torso ring: the 9 half-ring points' arc fractions (0 front seam .. 1 back seam)
      head         [(z at the front seam, lean)] per head ring
      face         dict(f1 nose side, fm mouth side, fy eye line, he eye half block, fe ear line, hw ear half block):
                   arc fractions that set the head's columns
      eye, mouth   loop sizes: eye x the head's width; mouth (half width, half height) in metres
      arm / leg    root: where on the first bone the first free ring sits (x the bone)
      nose         t of the nose rings on the nose part; ear: t of the ear rings on the ear part
      offsets      {name: amount x the local width} (clamped) and the FORM knobs"""
    from mathutils import Vector
    import bmkit as B
    (J, plan), gp = B.cage_plan(k.meta), k.guide_parts
    lm = k.meta.get('landmarks') or {}
    C, R, NH = tm.counts, tm.rows['n'], tm.counts['head']
    arm, leg = plan['limbs']['arm'], plan['limbs']['leg']
    zh, zs = J[leg[0]][2], J[arm[0]][2]
    aw = Tab(gp, 'arm').at(0.02)['width']
    z_arm = zs - 0.95 * aw
    z_belt = J[plan['spine'][0]][2] + 0.02
    mids = [z_belt + (z_arm - z_belt) * (q + 1) / (C['trunk_mid'] + 1) for q in range(C['trunk_mid'])]
    S = dict(torso=[(zh, 0.0), (z_belt, 0.0)] + [(z, 0.0) for z in mids] + [(z_arm, 0.0), (zs - 0.005, 8.0), (zs + 0.07, 20.0)])
    base = [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0]
    S['torso_fracs'] = [base] * (R - 1) + [[0.0, 0.18, 0.3, 0.41, 0.5, 0.59, 0.7, 0.82, 1.0]]
    ht = Tab(gp, 'head')
    top = float(max(ht.c[:, 2])) + 0.5 * float(ht.d[-1]) * 0.3
    ze = lm['eye'][2] if 'eye' in lm else float(ht.c[len(ht.c) // 2, 2])
    zm = lm['mouth'][2] if 'mouth' in lm else ze - 0.12
    zf = [zm - 0.07, zm - 0.02, zm, zm + 0.022, 0.5 * (zm + ze) + 0.005, ze, ze + 0.04]
    crown = top - 0.055
    nf = NH - 1 - 7
    zf += [zf[-1] + (crown - zf[-1]) * (q + 1) / (nf + 1) for q in range(nf)] + [crown]
    S['head'] = [(z, None if i < 7 else 0.0) for i, z in enumerate(zf)]
    S['nape'] = 0.10                 # metres the jaw line rises from the chin to the nape (x head_lean)

    def frac(p):                                                         # a point's arc fraction round the head (by angle)
        st = _at_z(ht, p[2])
        return math.atan2(p[0], st['centre'].y - p[1]) / math.pi

    ear = lm.get('ear') or (J[plan['extra'][0][0]] if plan.get('extra') else None)
    S['face'] = dict(f1=0.085, fm=0.17, fy=frac(lm['eye']) if 'eye' in lm else 0.2, he=0.065,
                     fe=frac(ear) if ear else 0.56, hw=0.065)
    S['eye'], S['mouth'] = 0.12, (0.07, 0.022)
    S['arm'], S['leg'] = dict(root=0.55), dict(root=0.62)
    S['hinge_ratio'] = 0.55
    S['nose'] = [0.5 + (0.93 - 0.5) * q / max(1, C['nose'] - 1) for q in range(C['nose'])]
    S['ear'] = [0.12 + (0.94 - 0.12) * (q + 1) / C['ear'] for q in range(C['ear'])]
    S['offsets'] = {}
    for k_, v in over.items():
        if isinstance(v, dict) and isinstance(S.get(k_), dict):
            S[k_] = dict(S[k_], **v)
        else:
            S[k_] = v
    S['form'] = dict(FORM, **{k_: v for k_, v in (S.get('offsets') or {}).items() if k_ in FORM})
    S['offsets'] = {k_: v for k_, v in (S.get('offsets') or {}).items() if k_ not in FORM}
    return S


def _head_fracs(face, NH):
    """Per head ring: the 10 half-ring points' arc fractions from the face's columns. The mouth rings (0-3) take a
    wider front (the grin), the cheek ring blends, the eye rings and above take the nose / eye / ear columns."""
    f = face
    tail = lambda a: [a + (1.0 - a) * (q + 1) / 4 for q in range(3)] + [1.0]
    hi = [0.0, f['f1'], f['fy'] - f['he'], f['fy'], f['fy'] + f['he'], f['fe'] - f['hw'], f['fe'] + f['hw']] + tail(f['fe'] + f['hw'])[:3]
    m0 = f['fm']
    lo = [0.0, m0, m0 + 0.07, m0 + 0.14, m0 + 0.21, f['fe'] - f['hw'], f['fe'] + f['hw']] + tail(f['fe'] + f['hw'])[:3]
    lo[4] = min(lo[4], lo[5] - 0.05)
    mid = [(a + b) / 2 for a, b in zip(lo, hi)]
    out = [lo] * 4 + [mid] + [hi] * (NH - 5)
    return [r[:9] + [1.0] for r in out]


def fit_template(tm, k, guide, spec=None):
    """Place every named vertex of the biped template on the guide and return the body object (mirrored half).
    tm.co then maps every vertex name to its position: bmkit's gates find the named sets by it."""
    import numpy as np
    from mathutils import Vector
    import bmesh
    import bmkit as B
    from carve import section_corners, _tree
    assert tm.kind == 'biped'
    S = spec or biped_spec(tm, k)
    FM = S.get('form') or dict(FORM)
    (J, plan), gp = B.cage_plan(k.meta), k.guide_parts
    lm = k.meta.get('landmarks') or {}
    C, R, NH = tm.counts, tm.rows['n'], tm.counts['head']
    tree = _tree(guide)
    X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
    P = [None] * len(tm.names)
    owner, co0 = {}, {}
    N = lambda *n: tm.id[n]
    dbg = bool(os.environ.get('BMK_TMPL_DBG'))

    def put(i, p):
        P[i] = Vector(p)
        owner[i] = None

    def near(p, mm=0.08):
        q = tree.find_nearest(p)[0]
        return q.copy() if q is not None and (q - p).length <= mm else p.copy()

    def section(key, ids, r, n, half=False, fracs=None, lim=(0.6, 1.3), snap=0.4, order=None):
        sc = section_corners(guide, r, n, half=half, fracs=fracs, lim=lim, snap=snap)
        pts = sc['points'] if order is None else [sc['points'][o] for o in order]
        for i, p in zip(ids, pts):
            P[i] = p.copy()
            owner[i] = key
            co0[i] = tuple(p)
        tm.corners[key] = dict(ids=list(ids), corners=[tuple(c) for c in sc['corners']], width=math.sqrt(max(1e-9, r['width'] * r['depth'])))
        return sc

    lean_w = lambda deg: Vector((0, -math.cos(math.radians(deg)), -math.sin(math.radians(deg))))

    def coons(part, proj=True, smap=None):
        """The cap's interior from its border (Coons patch over the ring and the seam chord), projected on the guide."""
        cp = tm.caps[part]
        g, na, nb = cp['grid'], cp['na'], cp['nb']
        P00, Pa0, P0b, Pab = P[g[(0, 0)]], P[g[(na, 0)]], P[g[(0, nb)]], P[g[(na, nb)]]
        for (a, b), i in g.items():
            if a == na or b in (0, nb):
                continue
            s_, t_ = (smap[a] if smap else a / na), b / nb
            p = (P[g[(a, 0)]] * (1 - t_) + P[g[(a, nb)]] * t_ + P00.lerp(P0b, t_) * (1 - s_) + P[g[(na, b)]] * s_
                 - (P00 * (1 - s_) * (1 - t_) + Pa0 * s_ * (1 - t_) + P0b * (1 - s_) * t_ + Pab * s_ * t_))
            if a == 0:
                p.x = 0.0
            q = near(p, 0.07) if proj else p
            if a == 0:
                q.x = 0.0
            put(i, q)
        return [i for (a, b), i in g.items() if not (a == na or b in (0, nb))]

    # ---- torso rings: level (or leaning) sections from the front seam round +x to the back seam
    tors = Tab(gp, 'torso')
    rowr = []
    for i, (z, ln) in enumerate(S['torso']):
        st = _at_z(tors, z)
        r = dict(st, centre=Vector((0.0, st['centre'].y, z)), u=X, w=lean_w(ln))
        rowr.append(r)
        section(('torso', i), tm.rings[('torso', i)], r, 8, half=True, fracs=S['torso_fracs'][i], lim=(0.6, 1.25))
    top_ = tm.rings[('torso', R - 1)]
    xm = max(P[i].x for i in top_)
    for i in top_:
        P[i].z -= FM['shoulder_drop'] * (P[i].x / xm) ** 1.5
    cap_free = coons('pelvis')
    cg = tm.caps['crest']['grid']
    for p_, i in cg.items():                                             # the trapezius: the cap's inner points stay up at the neck
        if p_[0] not in (0, 3) and p_[1] not in (0, 2):
            fa, ba = P[top_[p_[0]]], P[top_[8 - p_[0]]]
            put(i, Vector((0.5 * (fa.x + ba.x), 0.5 * (fa.y + ba.y), 0.5 * (fa.z + ba.z) + 0.15 * FM['shoulder_drop'] * (3 - p_[0]))))
            cap_free.append(i)
    # ---- head rings: level sections, the lower ones leaning (front low); the face's columns from the landmarks
    ht = Tab(gp, 'head')
    HF = _head_fracs(S['face'], NH)
    hc0 = _at_z(ht, S['head'][5][0])['centre']
    hit = tree.ray_cast(Vector((0.0, hc0.y, S['head'][5][0])), Z)
    ztop = hit[0].z if hit[0] is not None else S['head'][-1][0] + 0.05
    if hit[0] is not None and not S.get('head_fixed'):                  # the crown ring under the guide's top; forehead rings between
        crown = hit[0].z - 0.05
        hz = [z for z, _ in S['head']]
        for q in range(7, NH):
            hz[q] = hz[6] + (crown - hz[6]) * (q - 6) / (NH - 7)
        S['head'] = [(z, l) for z, (_, l) in zip(hz, S['head'])]
    headr = []
    zf0, zf6 = S['head'][0][0], S['head'][6][0]
    zb0 = zf0 + S['nape'] * FM['head_lean']
    for L, (zf, ln) in enumerate(S['head']):
        st = _at_z(ht, zf)
        if ln is None:                                                   # the back of the ring evenly between the nape and the brow
            zb = zb0 + (zf6 - zb0) * L / 6
            ln = math.degrees(math.asin(max(-0.9, min(0.9, (zb - zf) / max(1e-6, st['depth'])))))
        zc = zf + math.sin(math.radians(ln)) * 0.5 * st['depth']
        st = _at_z(ht, zc)
        r = dict(st, centre=Vector((0.0, st['centre'].y, zc)), u=X, w=lean_w(ln))
        headr.append(r)
        section(('head', L), tm.rings[('head', L)], r, 9, half=True, fracs=HF[L], lim=(0.6, 1.05 if L >= 1 else 1.12), snap=0.2)
    if FM['jaw_tuck'] > 0:                                               # behind the ear the lower rings tuck in to the neck's width
        xn = max(P[i].x for i in tm.loops['neck.border'])
        for L, s_ in ((0, 1.0), (1, 0.8), (2, 0.5)):
            for j, wj in ((5, 0.3), (6, 0.65), (7, 0.9), (8, 1.0)):
                i = tm.rings[('head', L)][j]
                tg = max(1.25 * xn, 0.5 * P[i].x)
                if tg < P[i].x:
                    P[i].x += (tg - P[i].x) * FM['jaw_tuck'] * s_ * wj
    cr_ = FM['crown_round']
    skull_free = []
    if cr_ > 0:                                                          # the cranium on an ellipsoid from the brow ring to the top
        r6 = tm.rings[('head', 6)]
        z6 = sum(P[i].z for i in r6) / len(r6)
        ce = Vector((0.0, headr[6]['centre'].y, z6))
        Hc = max(0.02, ztop - z6)
        ang6 = [math.atan2(P[i].x, -(P[i].y - ce.y)) for i in r6]
        rad6 = [math.hypot(P[i].x, P[i].y - ce.y) for i in r6]

        def R6(th):
            for q in range(len(r6) - 1):
                if ang6[q] <= th <= ang6[q + 1] or q == len(r6) - 2:
                    f = (th - ang6[q]) / max(1e-6, ang6[q + 1] - ang6[q])
                    return rad6[q] + (rad6[q + 1] - rad6[q]) * max(0.0, min(1.0, f))
        for L in range(7, NH):
            ph = (L - 6) / (NH - 6 + 0.6) * math.pi / 2
            for kk, i in enumerate(tm.rings[('head', L)]):
                o = r6[kk]
                q_ = Vector((P[o].x * math.cos(ph), ce.y + (P[o].y - ce.y) * math.cos(ph), z6 + Hc * math.sin(ph)))
                P[i] = P[i].lerp(q_, cr_)
                if i in tm.seam:
                    P[i].x = 0.0
        skull_free = coons('skull', proj=False)
        for i in skull_free:
            dx, dy = P[i].x, P[i].y - ce.y
            rho = math.hypot(dx, dy) / max(1e-6, R6(math.atan2(dx, -dy)))
            zt = z6 + Hc * math.sqrt(max(0.0, 1.0 - rho * rho))
            P[i].z += (zt - P[i].z) * cr_
    else:
        cap_free += coons('skull')
    jaw_free = coons('jaw', proj=False, smap=[0.0, FM['neck_flare'], 0.5 + 0.5 * FM['neck_flare'], 1.0])
    if FM['jaw_tuck'] > 0:                                               # the floor's back row up against the nape: no shelf round the neck
        gj_, nb_j = tm.caps['jaw']['grid'], tm.caps['jaw']['nb']
        for (a, b), i in gj_.items():
            if b == nb_j - 1 and a in (1, 2):
                P[i] = P[i].lerp(P[gj_[(a, nb_j)]], 0.85 * FM['jaw_tuck'])
    hw = headr[5]['width']
    # ---- the neck: bridge rings between the crest's hole and the jaw floor's hole, on the guide
    A, Bp = tm.loops['neck.border'], tm.loops['neck.head']
    cA = sum((P[i] for i in A), Vector()) / len(A)
    cB = sum((P[i] for i in Bp), Vector()) / len(Bp)
    cA.x = cB.x = 0.0
    nn = C['neck']
    for q in range(nn):
        f = (q + 1) / (nn + 1)
        ax = cA.lerp(cB, f)
        for kk, i in enumerate(tm.rings[('neck', q)]):
            m_ = P[A[kk]].lerp(P[Bp[kk]], f)
            d_ = m_ - ax
            hit = tree.ray_cast(ax, d_.normalized()) if d_.length > 1e-6 else (None,)
            p = hit[0].copy() if hit[0] is not None and 0.6 * d_.length <= hit[3] <= 1.6 * d_.length else m_
            p = m_.lerp(p, min(1.0, 5 * f * (1 - f)) * (1 - 0.3 * f))
            p = ax + (p - ax) * FM['neck_in']
            if i in tm.seam:
                p.x = 0.0
            put(i, p)
    tm.joint_rings[plan['neck']] = [('neck', q) for q in range(nn)]

    # ---- limbs
    def frame_of(tau):
        u = (X - tau * X.dot(tau)).normalized()
        return u, tau.cross(u).normalized()

    tm.order = {}
    for name in ('leg', 'arm'):
        c = plan['limbs'][name]
        tab = Tab(gp, name)
        Jp = [Vector(J[n]) for n in c]
        seg = [(b - a).length for a, b in zip(Jp, Jp[1:])]
        tot = sum(seg)
        cum = [0.0]
        for l in seg:
            cum.append(cum[-1] + l)
        dirs = [(b - a).normalized() for a, b in zip(Jp, Jp[1:])]
        sgn = -1.0 if name == 'leg' else 1.0
        roles = tm.limbs[name]['roles']
        hinge_n = C[name]['hinge']
        size = lambda d: (lambda r: math.sqrt(r['width'] * r['depth']))(tab.at(min(d, cum[-2] - 1e-3) / tot))
        HG = {}
        for b, hn in enumerate(hinge_n):
            dj = cum[b + 1]
            if hn == 3:
                e = min(0.5 * size(dj), 0.4 * min(seg[b], seg[b + 1]))
                fl = S['hinge_ratio'] * e
                flex = sgn * (1 if b % 2 == 0 else -1)
                HG[b] = [(dj - (e + fl) / 2, +(e - fl) / 2 * flex), (dj, 0.0), (dj + (e + fl) / 2, -(e - fl) / 2 * flex)]
            else:
                g = min(0.45 * size(dj), 0.5 * min(seg[b], seg[b + 1]))
                sh_ = g / 2 if (name == 'leg' and b == len(hinge_n) - 1) else 0.0
                HG[b] = [(dj - g / 2 - sh_, 0.0), (dj + g / 2 - sh_, 0.0)][:hn]

        def frame(d):
            bi = max(i for i in range(len(seg)) if d >= cum[i] - 1e-9)
            tau = dirs[bi].copy()
            for ji in range(1, len(Jp) - 1):
                dj = d - cum[ji]
                rng = 0.6 * min(seg[ji - 1], seg[ji])
                if abs(dj) < rng:
                    other = dirs[ji - 1] if dj >= 0 else dirs[ji]
                    tau = (dirs[bi] * (1 - 0.5 * (1 - abs(dj) / rng)) + other * 0.5 * (1 - abs(dj) / rng)).normalized()
            return tau

        ring_d, prev_end, bone = [], S[name]['root'] * seg[0], 0
        for ri, role in enumerate(roles):
            if role == 'cap':
                ring_d.append(None)
            elif role == 'mass':
                nxt = next((x for x in roles[ri + 1:] if x != 'mass'), None)
                if bone == 0:
                    d = min(prev_end, HG[0][0][0] - 0.6 * (HG[0][1][0] - HG[0][0][0])) if len(HG[0]) > 1 else prev_end
                elif isinstance(nxt, tuple):
                    d = 0.5 * (prev_end + HG[nxt[1]][0][0])
                else:
                    d = prev_end + 0.4 * (tot - prev_end)
                ring_d.append((d, 0.0))
                prev_end = d
            elif isinstance(role, tuple):
                d, shr = HG[role[1]][role[2]]
                ring_d.append((d, shr))
                prev_end = d
                bone = role[1] + 1
                tm.joint_rings.setdefault(c[role[1] + 1], []).append((name, ri + 1))
            else:
                ring_d.append(role)
        ends = [ri for ri, x in enumerate(ring_d) if isinstance(x, str)]
        # where each ring sits: (centre, tau, station) ; the hand / foot rings past the last joint
        geo = {}
        for ri, rd in enumerate(ring_d):
            if rd is None or isinstance(rd, str):
                continue
            d, shr = rd
            tau = frame(d)
            if name == 'leg' and d > cum[-2]:                            # the ankle's lower ring stays on the shin
                tau = dirs[-2].copy()
                st = dict(tab.at(cum[-2] / tot - 1e-3))
                st['centre'] = Jp[-2] + tau * (d - cum[-2])
            else:
                st = tab.at(d / tot)
            geo[ri] = (Vector(st['centre']), tau, st, shr)
        if name == 'arm':
            fs = S.get('hand_fs', [0.18, 0.36, 0.58, 0.82])[:len(ends)] if len(ends) <= 4 else [0.18 + 0.68 * q / (len(ends) - 1) for q in range(len(ends))]
            for ri, f in zip(ends, fs):
                d = cum[-2] + f * seg[-1]
                st = tab.at(d / tot)
                geo[ri] = (Vector(st['centre']), frame(d), st, 0.0)
        else:
            ft = Tab(gp, name + '_foot')
            fa, fb = ft.at(0.0)['centre'], ft.at(1.0)['centre']
            tf = Vector((fb.x - fa.x, fb.y - fa.y, 0.0)).normalized()
            na_ = sum(1 for x in ring_d if x == 'arch')
            ts = {'ball': 0.76, 'toe': 0.9}
            q = 0
            for ri in ends:
                role = ring_d[ri]
                if role == 'heel':
                    a2 = geo[ri - 1][0]
                    st = ft.at(0.25)
                    cc = Vector((a2.x, a2.y + 0.15 * st['depth'], 0.48 * st['depth']))
                    geo[ri] = (cc, (dirs[-2] + tf).normalized(), dict(st, width=st['width'], depth=st['depth']), 'heel')
                    continue
                t_ = ts.get(role) if role in ts else 0.56 + 0.1 * q / max(1, na_ - 1)
                if role == 'arch':
                    q += 1
                st = ft.at(t_)
                geo[ri] = (Vector(st['centre']), tf.copy(), st, 'foot')
        # the slot order: ring vertex k takes the section slot whose angle matches the socket border's vertex k
        first = min(geo)
        cf, tf0 = geo[first][0], geo[first][1]
        uf, wf = frame_of(tf0)
        bd = tm.loops[name + '.border']
        th = [math.atan2((P[o] - cf).dot(wf), (P[o] - cf).dot(uf)) for o in bd]
        wrap = lambda a: (a + math.pi) % (2 * math.pi) - math.pi
        s0, dr = min(((s_, d_) for s_ in range(8) for d_ in (1, -1)),
                     key=lambda sd: sum(abs(wrap(t_ - 2 * math.pi * ((sd[0] + sd[1] * k_) % 8) / 8)) for k_, t_ in enumerate(th)))
        order = [(s0 + dr * k_) % 8 for k_ in range(8)]
        kos = {s_: k_ for k_, s_ in enumerate(order)}
        tm.order[name] = order
        frames = {}
        for ri in sorted(geo):
            cc, tau, st, shr = geo[ri]
            ids = tm.rings[(name, ri + 1)]
            u, w = frame_of(tau)
            r = dict(st, centre=cc, u=u, w=w)
            section((name, ri + 1), ids, r, 8, lim=(0.7, 1.3) if shr != 'heel' else (0.5, 1.6), order=order)
            if shr == 'heel':                                            # the heel: the back-bottom slots go to the guide's heel
                hy = ft.at(0.0)['centre'].y
                for sl, (dz, dy) in ((6, (0.0, 0.0)), (5, (0.03, 0.015)), (7, (0.03, 0.015))):
                    i = ids[kos[sl]]
                    P[i].z = min(P[i].z, dz)
                    P[i].y = max(P[i].y, hy - dy)
            elif shr == 'foot':                                          # a flat sole
                for sl in (5, 6, 7):
                    i = ids[kos[sl]]
                    if P[i].z < 0.03:
                        P[i].z = 0.0
            elif shr:
                rw = max(1e-6, max(abs((P[i] - cc).dot(w)) for i in ids))
                for i in ids:
                    P[i] += tau * (shr * (P[i] - cc).dot(w) / rw)
            sc_ = FM['hand_scale'] if (name == 'arm' and ring_d[ri] in ('palm', 'knuckle', 'finger')) else 1.0
            if name == 'arm' and ring_d[ri] == 'finger' and FM['finger_split'] > 0:
                for sl in (2, 6):
                    i = ids[kos[sl]]
                    P[i] = P[i].lerp(cc, FM['finger_split'])
            if name == 'leg' and ring_d[ri] in ('ball', 'toe'):
                for i in ids:
                    P[i].x = cc.x + (P[i].x - cc.x) * FM['toe_spread']
            if sc_ != 1.0:
                for i in ids:
                    d_ = P[i] - cc
                    P[i] = cc + u * (d_.dot(u) * sc_) + w * (d_.dot(w) * sc_ ** 0.5) + tau * d_.dot(tau)
            for i in ids:
                P[i].z = max(P[i].z, 0.0)
            frames[ri + 1] = (cc, tau, w)
        chain = [ri for ri in sorted(geo) if not isinstance(ring_d[ri], str)]
        if name == 'arm':                                                # the arm: down to the forearm (the wrist feeds the hand)
            chain = [ri for ri in chain if ri <= max(q for q in chain if ring_d_role(roles[q]) != 'wrist')]
        if FM['limb_fair'] > 0 and len(chain) >= 3:                     # no ring dips under the line of its neighbours (per slot)
            def inpl(ri, k_):
                cc, tau, _w = frames[ri + 1]
                d_ = P[tm.rings[(name, ri + 1)][k_]] - cc
                return d_ - tau * d_.dot(tau)
            for k_ in range(8):
                rad = [inpl(ri, k_).length for ri in chain]
                tg = rad[:]
                for _ in range(len(chain)):
                    for q in range(1, len(chain) - 1):
                        tg[q] = max(tg[q], 0.5 * (tg[q - 1] + tg[q + 1]))
                for q, ri in enumerate(chain):
                    if rad[q] > 1e-6 and tg[q] > rad[q]:
                        P[tm.rings[(name, ri + 1)][k_]] += inpl(ri, k_) * (FM['limb_fair'] * (tg[q] / rad[q] - 1))
            rs = FM[name + '_root']
            for q, ri in enumerate(chain):
                f_ = 1.0 + (rs - 1.0) * (1.0 - q / (len(chain) - 1))
                for k_ in range(8):
                    P[tm.rings[(name, ri + 1)][k_]] += inpl(ri, k_) * (f_ - 1.0)
        if name == 'arm':                                                # the hand's rings each ahead of the one before (no fold)
            seq = [ends[0] - 1] + ends
            for qa, qb in zip(seq, seq[1:]):
                for a_, b_ in zip(tm.rings[(name, qa + 1)], tm.rings[(name, qb + 1)]):
                    s_ = (P[b_] - P[a_]).dot(dirs[-1])
                    if s_ < 0.008:
                        P[b_] += dirs[-1] * (0.008 - s_)
        lr = tm.rings[(name, len(roles))]
        lc = sum((P[i] for i in lr), Vector()) / 8
        lt = geo[len(roles) - 1][1]
        tip = lc + lt * 0.3 * max((P[i] - lc).length for i in lr)        # a blunt end (curled fingers, the toes' front)
        put(N(name, 'cap', 0), Vector((tip.x, tip.y, max(0.012, tip.z))))
        # hinges: the flexion side's ring indices, and the fan set to the ratio as the gate measures it
        for b, hn in enumerate(hinge_n):
            if hn != 3:
                continue
            rr = [ri + 1 for ri, x in enumerate(roles) if isinstance(x, tuple) and x[1] == b]
            flex = sgn * (1 if b % 2 == 0 else -1)
            fs_, es_ = ([1, 2, 3], [5, 6, 7]) if flex > 0 else ([5, 6, 7], [1, 2, 3])
            h = dict(limb=name, rings=rr, flex=[kos[s_] for s_ in fs_], ext=[kos[s_] for s_ in es_])
            tm.hinges[c[b + 1]] = h
            R3 = [tm.rings[(name, r)] for r in rr]
            for _ in range(3):
                gap = lambda ks: sum((P[R3[q][k_]] - P[R3[q + 1][k_]]).length for q in (0, 1) for k_ in ks) / 6
                fl_, ex_ = gap(h['flex']), gap(h['ext'])
                x = (fl_ - S['hinge_ratio'] * ex_) / (1 + S['hinge_ratio']) / 0.8
                for r, dirn in ((rr[0], 1.0), (rr[2], -1.0)):
                    cc, tau, w = frames[r]
                    ids = tm.rings[(name, r)]
                    rw = max(1e-6, max(abs((P[i] - cc).dot(w)) for i in ids))
                    for i in ids:
                        P[i] += tau * (dirn * flex * x * (P[i] - cc).dot(w) / rw)
        # the socket loop and the cap rings: fanned from the border on the body to the first free ring, on the guide
        free = tm.rings[(name, first + 1)]
        n_between = first + 1
        inner = [bd.index(i) for i in tm.limbs[name]['inner']]
        for k_ in inner:                                                 # under the body the first free ring stays below the border
            P[free[k_]].z = min(P[free[k_]].z, P[bd[k_]].z - 0.02)
            P[free[k_]].x = max(P[free[k_]].x, P[bd[k_]].x + 0.01 * (n_between + 1))
        SOCK = {1: (0.45,), 2: (0.35, 0.7), 3: (0.22, 0.5, 0.78)}
        fr_ = SOCK.get(n_between) or [(q + 1) / (n_between + 1) for q in range(n_between)]
        a0, a1 = Jp[0], Jp[1]
        for q in range(n_between):
            f = fr_[q]
            for k_, i in enumerate(tm.rings[(name, q)]):
                m_ = P[bd[k_]].lerp(P[free[k_]], f)
                if k_ in inner:
                    p = near(m_, 0.015)
                    p.x = max(p.x, P[bd[k_]].x + 0.01 * (q + 1))
                    put(i, p)
                    continue
                ax = a0 + (a1 - a0) * min(1.0, max(0.0, (m_ - a0).dot(a1 - a0) / (a1 - a0).length_squared))
                d_ = m_ - ax
                hit = tree.ray_cast(ax, d_.normalized()) if d_.length > 1e-6 else (None,)
                put(i, hit[0].copy() if hit[0] is not None and 0.7 * d_.length <= hit[3] <= 1.8 * d_.length else near(m_, 0.06))
            tm.pinned.update(tm.rings[(name, q)])
    # ---- the thumb: out of its palm face, forward and down, tapering
    tb = tm.loops['thumb.border']
    c0 = sum((P[i] for i in tb), Vector()) / 4
    nrm = (P[tb[2]] - P[tb[0]]).cross(P[tb[3]] - P[tb[1]]).normalized()
    pc = sum((P[i] for i in tm.rings[('arm', tm.limbs['arm']['roles'].index('palm') + 1)]), Vector()) / 8
    if nrm.dot(c0 - pc) < 0:
        nrm = -nrm
    dth = (nrm + Vector((0, -0.6, -0.5))).normalized()
    Lth = FM['thumb_len'] * max((P[a] - P[b]).length for a in tb for b in tb)
    nt = C['arm'].get('thumb', 2)
    for q in range(nt + 1):
        sc_ = 0.8 if q == 0 else 0.8 - 0.35 * q / nt
        cc = c0 + nrm * 0.004 if q == 0 else c0 + dth * Lth * q / nt
        for i, o in zip(tm.rings[('thumb', q)], tb):
            put(i, cc + (P[o] - c0) * sc_)
    if tm.fingers:                                                       # the finger blocks: out of the hand's end, tapering, a little spread
        ja = plan['limbs']['arm']
        hdir = (Vector(J[ja[-1]]) - Vector(J[ja[-2]])).normalized()
        lr = tm.rings[('arm', len(tm.limbs['arm']['roles']))]
        put(N('arm', 'cap', 0), sum((P[i] for i in lr), Vector()) / len(lr) + hdir * 0.004)
        nr_ = C['arm'].get('finger_rings', 2)
        cs = [sum((P[i] for i in tm.loops[nm + '.border']), Vector()) / 6 for nm in tm.fingers]
        cm_ = sum(cs, Vector()) / len(cs)
        for nm, c0 in zip(tm.fingers, cs):
            bd_ = tm.loops[nm + '.border']
            aw_ = c0 - cm_
            aw_ -= hdir * aw_.dot(hdir)
            dfin = (hdir + aw_.normalized() * 0.3).normalized() if aw_.length > 1e-6 else hdir
            for r in range(nr_ + 1):
                cc = c0 + dfin * (0.004 + FM['finger_len'] * r / nr_)
                for i, o in zip(tm.rings[(nm, r)], bd_):
                    put(i, cc + (P[o] - c0) * (0.85 - 0.35 * r / nr_))
                tm.pinned.update(tm.rings[(nm, r)])
    # ---- the face: eye loop and mouth loop pinned to the landmarks
    def loop_on(ids, border, centre, a, b, axis, normal=None):
        """ids round `centre` on the guide, an ellipse (a along axis, b across), evenly spaced, turned to line up with the
        border. normal: the surface normal there, given (then the points are not projected on the guide)."""
        if normal is None:
            hit = tree.find_nearest(centre)
            c, n = hit[0], hit[1]
        else:
            c, n = centre.copy(), normal.normalized()
        t1 = (axis - n * axis.dot(n)).normalized()
        t2 = n.cross(t1)
        m = len(border)
        cb = sum((P[o] for o in border), Vector()) / m
        ang = [math.atan2((P[o] - cb).dot(t2), (P[o] - cb).dot(t1)) for o in border]
        sg = 1.0 if sum(((ang[(q + 1) % m] - ang[q] + math.pi) % (2 * math.pi)) - math.pi for q in range(m)) > 0 else -1.0
        th0 = math.atan2(sum(math.sin(ang[q] - sg * 2 * math.pi * q / m) for q in range(m)),
                         sum(math.cos(ang[q] - sg * 2 * math.pi * q / m) for q in range(m)))
        room = min(math.hypot((P[o] - c).dot(t1) / a, (P[o] - c).dot(t2) / b) for o in border)
        if room < 1.25:
            a, b = a * room / 1.25, b * room / 1.25
        for q, i in enumerate(ids):
            th = th0 + sg * 2 * math.pi * q / m
            p = c + t1 * (a * math.cos(th)) + t2 * (b * math.sin(th))
            put(i, near(p, 0.04) if normal is None else p)
        tm.pinned.update(ids)
        return c, n

    if 'eye' in lm:
        loop_on(tm.loops['eye'], tm.loops['eye.border'], Vector(lm['eye']), 1.25 * S['eye'] * hw, 0.8 * S['eye'] * hw, X)
        put(N('eye', 'centre', 0), near(Vector(lm['eye']), 0.04))
    mb, ml = tm.loops['mouth.border'], tm.loops['mouth']
    if 'mouth' in lm:
        mc = Vector((0.0, lm['mouth'][1], lm['mouth'][2]))
        a_, b_ = S['mouth']
        a_ = min(a_, 0.85 * P[mb[2]].x)
        top_first = P[mb[0]].z > P[mb[-1]].z
        ths = [0, 45, 90, 135, 180] if top_first else [180, 135, 90, 45, 0]
        for i, th in zip(ml, ths):
            p = mc + X * (a_ * math.sin(math.radians(th))) + Z * (b_ * math.cos(math.radians(th)))
            q_ = near(p, 0.04)
            if th in (0, 180):
                q_.x = 0.0
            put(i, q_)
        tm.pinned.update(ml)
    else:
        cb = sum((P[o] for o in mb), Vector()) / len(mb)
        for i, o in zip(ml, mb):
            put(i, cb.lerp(P[o], 0.6))
    cm = sum((P[i] for i in ml), Vector()) / len(ml)
    put(N('mouth', 'centre', 0), Vector((0.0, cm.y + FM['mouth_in'], 0.5 * (P[ml[1]].z + P[ml[3]].z) if len(ml) == 5 else cm.z)))
    # ---- the nose: rings on the nose part, its socket between the face and the first ring
    if 'nose' in gp:
        nt_ = Tab(gp, 'nose')
        nb_ = tm.loops['nose.border']
        rev = P[nb_[0]].z < P[nb_[-1]].z
        od = [4, 3, 2, 1, 0] if rev else None
        for q, t_ in enumerate(S['nose']):
            st = nt_.at(t_)
            section(('nose', q + 1), tm.rings[('nose', q + 1)], dict(st, u=X), 4, half=True, lim=(0.6, 1.4), snap=0.3, order=od)
        for i, o, f_ in zip(tm.rings[('nose', 0)], nb_, tm.rings[('nose', 1)]):
            p = P[o].lerp(P[f_], 0.3)
            put(i, p if i not in tm.seam else Vector((0.0, p.y, p.z)))
        tipn = nt_.at(1.0)['centre']
        lastn = tm.rings[('nose', C['nose'])]
        put(N('nose', 'cap', 0), Vector((0.0, tipn[1], tipn[2])) + (Vector(tipn) - Vector(nt_.at(0.9)['centre'])).normalized() * 0.006)
        for q in range(0, C['nose'] + 1):                                # every ring ahead of the one before (no fold at the root)
            pr, nx = (nb_ if q == 0 else tm.rings[('nose', q - 1)]), tm.rings[('nose', q)]
            dvec = (sum((P[i] for i in nx), Vector()) - sum((P[i] for i in pr), Vector())) / 5
            if dvec.length > 1e-6:
                dvec.normalize()
                for a_, b_ in zip(pr, nx):
                    s_ = (P[b_] - P[a_]).dot(dvec)
                    if s_ < 0.006:
                        P[b_] += dvec * (0.006 - s_)
    # ---- the ear: socket loop round the root, rings along the ear part, scaled from the socket (a blade), cupped
    eb = tm.loops['ear.border']
    root = Vector(lm['ear']) if 'ear' in lm else Vector(J[plan['extra'][0][0]])
    et = Tab(gp, 'extra0') if 'extra0' in gp else None
    s0_ = et.at(0.0) if et else dict(width=0.03, depth=0.15, u=Y, w=Z, centre=root)
    cb_ = sum((P[o] for o in eb), Vector()) / len(eb)
    hc = _at_z(ht, cb_.z)['centre']
    nr = Vector((cb_.x, cb_.y - hc.y, 0.0)).normalized()                # the head's side, square to the ring (not the ear blade)
    c, n = loop_on(tm.loops['ear.socket'], eb, cb_ + nr * 0.004, 0.42 * s0_['depth'], max(0.012, 0.9 * s0_['width']), Z, normal=nr)
    u0, w0 = Vector(s0_['u']).normalized(), Vector(s0_['w']).normalized()
    mids = [eb.index(i) for i in tm.ear_mid]
    sock_h = max(1e-6, max((P[i] - c).dot(w0) for i in tm.loops['ear.socket']) - min((P[i] - c).dot(w0) for i in tm.loops['ear.socket']))
    sock_t = max(1e-6, max((P[i] - c).dot(u0) for i in tm.loops['ear.socket']) - min((P[i] - c).dot(u0) for i in tm.loops['ear.socket']))
    for q, t_ in enumerate(S['ear']):
        st = et.at(t_) if et else dict(centre=root + X * 0.3 * t_, width=0.03, depth=0.15 * (1 - t_))
        su = max(0.3, st['width'] / max(1e-6, sock_t)) * FM['ear_thin']
        sw = max(0.05, st['depth'] * FM['ear_size'] / max(1e-6, sock_h))
        cc = Vector(st['centre'])
        ids = tm.rings[('ear', q + 1)]
        for kk, (i, o) in enumerate(zip(ids, tm.loops['ear.socket'])):
            d_ = P[o] - c
            p = cc + u0 * (d_.dot(u0) * su) + w0 * (d_.dot(w0) * sw)
            if kk in mids:
                p -= u0 * (FM['ear_cup'] * st['depth'])
            put(i, p)
        tm.pinned.update(ids)
    # ---- the named offsets: planes broken on purpose (each clamped to OFFSET_CLAMP x the local width)
    Hr = lambda L, js: [(N('head', L, j), hw) for j in js if tm.names[N('head', L, j)][0] == 'head']
    Tr = lambda rows_, js: [(N('torso', i, j), rowr[i]['depth']) for i in rows_ for j in js if tm.names[N('torso', i, j)][0] == 'torso']
    aw = math.sqrt(Tab(gp, 'arm').at(0.05)['width'] * Tab(gp, 'arm').at(0.05)['depth'])
    mid_rows = list(range(2, R - 3))
    cr = tm.caps['crest']['grid']
    OFF = dict(
        brow=(Hr(6, (1, 2, 3, 4)), Vector((0, -0.8, 0.6))),
        cheek=(Hr(4, (2, 3, 4)), Vector((0.75, -0.65, 0))),
        jaw=(Hr(0, (2, 3, 4, 5)), Vector((0.6, 0, -0.8))),
        chin=(Hr(0, (0, 1)) + Hr(1, (0,)), Vector((0, -1, -0.2))),
        trapezius=([(cr[(2, 1)], rowr[-1]['depth']), (cr[(1, 1)], 0.5 * rowr[-1]['depth'])], Z),
        deltoid=([(i, aw) for q in range(2) for i in tm.rings[('arm', q)] if bd_ok(i, tm)], None),
        pec=(Tr((R - 4, R - 3), (1, 2)), Vector((0, -1, 0))),
        scapula=(Tr((R - 3, R - 2), (6, 7)), Vector((0, 1, 0))),
        belly=([(i, wd * math.sin(math.pi * (mid_rows.index(tm.names[i][1]) + 1) / (len(mid_rows) + 1)) ** 0.5)
                for i, wd in Tr(mid_rows, (0, 1, 2))], Vector((0, -1, 0))),
        glute=(Tr((0, 1), (6, 7, 8)), Vector((0, 1, -0.2))),
    )
    arm_axis = (Vector(J[plan['limbs']['arm'][0]]), Vector(J[plan['limbs']['arm'][1]]))
    for name_, amt in (S.get('offsets') or {}).items():
        if name_ not in OFF:
            raise KeyError(f'no named offset {name_!r}: {sorted(OFF)}')
        vs, d = OFF[name_]
        amt = max(-OFFSET_CLAMP, min(OFFSET_CLAMP, amt))
        for i, wd in vs:
            if d is None:                                                # radial from the arm's first bone (the deltoid)
                a0, a1 = arm_axis
                ax = a0 + (a1 - a0) * max(0.0, min(1.0, (P[i] - a0).dot(a1 - a0) / (a1 - a0).length_squared))
                dd = (P[i] - ax).normalized()
                if dd.z < -0.3:                                          # not the armpit
                    continue
            else:
                dd = d.normalized()
            P[i] = P[i] + dd * (amt * wd)
            if i in tm.seam:
                P[i].x = 0.0
            tm.pinned.add(i)
    # ---- a light relax of the caps' inner points (Coons placed them), projected
    nbs = tm.neighbours()
    for q in range(3):
        for i in cap_free:
            avg = sum((P[j] for j in nbs[i]), Vector()) / len(nbs[i])
            p = P[i].lerp(avg, 0.5)
            p = near(p, 0.03)
            if i in tm.seam:
                p.x = 0.0
            P[i] = p
    tm.co0 = {tm.names[i]: co0.get(i, tuple(P[i])) for i in range(len(P))}
    # ---- planarity: every quad outside the hinges settles toward its own plane (a capped move)
    hinge_v = {i for keys in tm.joint_rings.values() for key in keys if key[0] in tm.limbs for i in tm.rings[key]}
    fixed = set(hinge_v) | set(tm.loops['eye']) | set(tm.loops['mouth']) | set(tm.loops['ear.socket'])
    for q in range(C['ear'] + 1):
        fixed |= set(tm.rings[('ear', q)])
    for nm in tm.fingers:
        for q in range(C['arm'].get('finger_rings', 2) + 1):
            fixed |= set(tm.rings[(nm, q)])
    for name in tm.limbs:
        fixed |= set(tm.rings[(name, len(tm.limbs[name]['roles']))]) | {N(name, 'cap', 0)}
    hingeF = [all(v in hinge_v for v in f) for f in tm.F]
    home = [p.copy() for p in P]
    mm = S.get('planar', 0.14) * rowr[len(rowr) // 2]['depth']
    for _ in range(S.get('planar_iters', 60)):
        acc = {}
        for fi, f in enumerate(tm.F):
            if hingeF[fi]:
                continue
            a_, b_, c_, d_ = (P[i] for i in f)
            n_ = (c_ - a_).cross(d_ - b_)
            if n_.length < 1e-12:
                continue
            n_.normalize()
            ce = (a_ + b_ + c_ + d_) / 4
            for i in f:
                if i not in fixed:
                    e = acc.setdefault(i, [Vector(), 0])
                    e[0] -= n_ * (P[i] - ce).dot(n_)
                    e[1] += 1
        for i, (dv, cnt) in acc.items():
            q_ = P[i] + dv / cnt
            if i in tm.seam:
                q_.x = 0.0
            d_ = q_ - home[i]
            P[i] = home[i] + d_ * (mm / d_.length) if d_.length > mm else q_
    tfix = set(tm.loops['arm.border']) | set(tm.rings[('torso', 0)]) | set(tm.rings[('torso', R - 1)])
    for it in range(int(2 * FM['torso_fair'])):                         # Taubin: lambda then mu, along each lengthwise line
        lam = 0.5 if it % 2 == 0 else -0.53
        for j in range(9):
            col = [tm.rings[('torso', i)][j] for i in range(R)]
            Q = [P[i].copy() for i in col]
            for q in range(1, R - 1):
                if col[q] in tfix or tm.names[col[q]][0] != 'torso':     # the arm block's centre is the hand's cap
                    continue
                P[col[q]] = Q[q] + ((Q[q - 1] + Q[q + 1]) * 0.5 - Q[q]) * lam
                if j in (0, 8):
                    P[col[q]].x = 0.0
    for i in range(len(P)):
        P[i].x = 0.0 if i in tm.seam else max(P[i].x, 0.004)
        P[i].z = max(P[i].z, 0.0)
    for key, c_ in tm.corners.items():                                   # a vertex counts for the section that placed it last
        c_['ids'] = [i for i in c_['ids'] if owner.get(i) == key and i not in tm.pinned]
        c_['names'] = [tm.names[i] for i in c_['ids']]
    # ---- the mesh
    bm = bmesh.new()
    bv = [bm.verts.new(p) for p in P]
    warped = 0
    for fi, f in enumerate(tm.F):                                        # a quad splits on its SHORTER diagonal
        if (P[f[0]] - P[f[2]]).length > (P[f[1]] - P[f[3]]).length + 1e-6:
            f = f[1:] + f[:1]
        bm.faces.new([bv[i] for i in f])
        warped += (not hingeF[fi]) and quad_warp(*[P[i] for i in f]) > 12.0
    B.say('template fit (biped): non-planar quads (over 12 degrees) outside the hinges: %d of %d' % (warped, len(tm.F) - sum(hingeF)))
    B.snap_seam(bm)
    if dbg:
        from mathutils.bvhtree import BVHTree
        bm.faces.ensure_lookup_table()
        t_ = BVHTree.FromBMesh(bm)
        cnt = {}
        for i, j in t_.overlap(t_):
            if i < j and not (set(tm.F[i]) & set(tm.F[j])):
                key = (str(tm.names[tm.F[i][0]][:2]), str(tm.names[tm.F[j][0]][:2]))
                cnt[key] = cnt.get(key, 0) + 1
        for key, n_ in sorted(cnt.items(), key=lambda x: -x[1])[:20]:
            B.say('DBG hit', n_, key)
        for nm in ('leg', 'arm'):
            B.say('DBG order', nm, tm.order[nm])
    tm.co = {tm.names[i]: tuple(bv[i].co) for i in range(len(P))}
    k.template = tm
    if os.environ.get('BMK_TEMPLATE_STORE'):
        B.say('template signature stored:', tm.store_signature(), tm.key())
    return B.object_from_bm('body', bm)


def ring_d_role(role):
    """'wrist' for a hinge ring of the arm's second joint, else the role's name."""
    return 'wrist' if isinstance(role, tuple) and role[1] == 1 else (role if isinstance(role, str) else 'hinge')


def bd_ok(i, tm):
    """The deltoid offset moves the arm's socket and cap rings, not their border on the torso."""
    return tm.names[i][0] == 'arm'
