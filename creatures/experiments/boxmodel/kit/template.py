"""template.py: kit-owned topology templates for the stage-1 cage (research/topology_aaa_*.md).

    tm = body_template('quadruped', counts)          # ALL connectivity, by box operations only
    body = fit_template(tm, k, guide, spec)          # every named vertex placed from the guide

The creature program authors no topology. It supplies J, the plan, counts, landmarks and a small table of named
offsets; the template owns the faces.

CONNECTIVITY (body_template). One segmented box per body, then `grow` (inset, then extrude) per branch:
  trunk    a 4 x 3 box along the body: 14 sides. Half-ring vertices 0..7 from the top seam to the bottom seam:
           0 topline, 1 back, 2 back edge (box corner), 3 flank, 4 upper flank (the top of the limb blocks),
           5 lower flank (box corner), 6 belly line (the bottom of the limb blocks: armpit and groin), 7 keel. Rows run rump -> chest front; rows 1-3 carry the haunch block, the last-but-three
           to last-but-one the scapula block.
  limbs    8 sides, from a 2 x 2 block of flank faces (columns 4 and 5: four columns stay above it for the back and
           one below for the belly, so a narrow chest between the legs is one face wide, not two slivers). The block is inset once (the SOCKET loop,
           all valence 4 once the limb is extruded from it); the block's own border stays on the trunk as the
           scapula / haunch border, its four corners are the only poles, one ring outside the crease. The block
           itself travels to the sole and closes the paw with 2 x 2 quads.
  neck     12 sides, from the upper 4 x 2 of the box's front face (the lower row stays: the brisket); it runs on
           as the head box (12). Head half-ring: 0 top, 1, 2 brow line, 3 cheek / mouth line, 4 jaw line, 5, 6 chin.
  muzzle   8 sides, from the middle 2 x 2 of the head's front face (the stop); its cap is the nose plane.
  eye      an 8-vertex loop: a 1 x 3 block that turns the head's front corner (two faces of the upper side row behind
           the stop and the front face beside the muzzle), inset once. No eye geometry.
  ear      6 sides, from a 1 x 2 block on the skull's top corner.     tail  6 sides, from the top-middle 2 x 1 of the rump.
Every vertex has a name (part, ring, point); rings, loops and lengthwise lines are named lists (tm.rings, tm.loops,
tm.lines). tm.signature() is the template's identity (counts, valence histogram, loop lengths, a hash of the faces);
template_signatures.json stores the reviewed one per (kind, counts) and bmkit's gate compares.

FIT (fit_template). Ring stations from carve.part_rings; ring vertices on the corners of the guide's section there
(carve.section_corners: polyline simplification of the rays' section; limb sections read by rays, so off-axis mass
stays off axis); socket loops between their border on the trunk and the limb's first free ring, on the guide;
eye and ear loops pinned to META['landmarks']; hinge rings converge on the flexion side; then the named offsets
(clamped) and a light relax-and-project of the vertices no section placed. No generic shrink-wrap.
"""
import hashlib, json, math, os

SIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'template_signatures.json')
SIDES = dict(quadruped=dict(trunk=14, neck=12, head=12, muzzle=8, limb=8, tail=6, ear=6, eye=8))
COUNTS = dict(quadruped=dict(
    trunk_mid=3,             # trunk rows between the haunch block and the scapula block (loin, waist, rear rib)
    neck=4,                  # neck rings after the neck's socket loop
    head=4,                  # head rings: occiput, ear line, brow, the stop (4 is the least: ear and eye blocks)
    muzzle=3,                # muzzle rings after its socket loop; the last is the nose end
    tail=5, ear=2,           # rings after the socket loop
    fore=dict(hinge=(3, 2), mass=(1, 1)),        # per inner joint: rings (3 = converging hinge, 2 = wrist / ankle); per bone
    hind=dict(hinge=(3, 3), mass=(1, 1, 1)),     # before it: mass rings (the last bone's is the cannon); + paw and sole rings
))
OFFSET_CLAMP = 0.25          # a named offset is at most this x the local width


# ---------------------------------------------------------------- connectivity (no Blender needed)
class Topo:
    """A half mesh (x >= 0, open on the mirror seam) as named vertices and quads, built only by box and grow."""

    def __init__(self, kind, counts):
        self.kind, self.counts = kind, counts
        self.names, self.id, self.seam, self.F, self.fid = [], {}, set(), [], {}
        self.rings, self.loops, self.lines, self.limbs = {}, {}, {}, {}
        self.hinges, self.joint_rings, self.corners, self.co, self.pinned = {}, {}, {}, {}, set()

    def v(self, name, seam=False):
        i = len(self.names)
        self.names.append(name); self.id[name] = i
        if seam:
            self.seam.add(i)
        return i

    def f(self, vs, key=None):
        self.F.append(list(vs))
        if key is not None:
            self.fid[key] = len(self.F) - 1

    def rename(self, old, new):
        i = self.id.pop(old)
        self.names[i] = new; self.id[new] = i
        return i

    def grow(self, faces, part, r, start=None, reverse=False):
        """Inset / extrude of a block of faces (the two are one operation on the connectivity): every vertex of the
        block's border gets a copy named (part, r, k), the block moves onto the copies and a ring of quads joins the
        old border to the new. Returns (new ring, old border), both in ring order; the path is closed, or runs
        seam to seam on a block that touches the mirror seam. reverse: number the path from its other end."""
        patch = set(faces)
        twin = set()
        for fi, f in enumerate(self.F):
            if fi not in patch:
                twin.update(zip(f, f[1:] + f[:1]))
        nxt = {}
        for fi in faces:
            f = self.F[fi]
            for a, b in zip(f, f[1:] + f[:1]):
                if (b, a) in twin:
                    nxt[a] = b
        heads = [x for x in nxt if x not in set(nxt.values())]
        a = heads[0] if heads else (start if start is not None else min(nxt))
        path = [a]
        while path[-1] in nxt and (len(path) == 1 or path[-1] != path[0]):
            path.append(nxt[path[-1]])
        closed = len(path) > 1 and path[-1] == path[0]
        if closed:
            path.pop()
        assert len(path) == len(nxt) + (0 if closed else 1), 'the block border is not one path'
        order = path[::-1] if reverse else path
        new = {o: self.v((part, r, k_), seam=o in self.seam) for k_, o in enumerate(order)}
        for fi in faces:
            self.F[fi] = [new.get(x, x) for x in self.F[fi]]
        pos = {o: k_ for k_, o in enumerate(order)}
        for a, b in list(zip(path, path[1:])) + ([(path[-1], path[0])] if closed else []):
            ka, kb = pos[a], pos[b]
            self.f([a, b, new[b], new[a]], key=(part, r, min(ka, kb) if abs(ka - kb) == 1 else max(ka, kb)))
        ring = [new[o] for o in order]
        self.rings[(part, r)] = ring
        return ring, order

    def neighbours(self):
        nb = [set() for _ in self.names]
        for f in self.F:
            for a, b in zip(f, f[1:] + f[:1]):
                nb[a].add(b); nb[b].add(a)
        return nb

    def valence(self):
        """Valence of every vertex in the mirrored mesh."""
        return [sum(1 if (j in self.seam or i not in self.seam) else 2 for j in s) for i, s in enumerate(self.neighbours())]

    def check(self):
        """Raises unless the half mesh is all quads, manifold, consistently wound and open only on the seam."""
        seen, und = set(), {}
        for f in self.F:
            assert len(f) == 4 and len(set(f)) == 4, 'not a quad'
            for a, b in zip(f, f[1:] + f[:1]):
                assert (a, b) not in seen, 'winding / duplicate edge'
                seen.add((a, b)); und[frozenset((a, b))] = und.get(frozenset((a, b)), 0) + 1
        for e, n in und.items():
            assert n == 2 or (n == 1 and e <= self.seam), 'open edge off the seam'
        used = {v for f in self.F for v in f}
        assert len(used) == len(self.names), 'unused vertex'

    def signature(self):
        """(description, hash): counts, the valence histogram of the mirrored mesh, the named loops' lengths, the
        branch side counts and a hash of the face list by vertex name."""
        val = self.valence()
        hist = {}
        for x in val:
            hist[str(x)] = hist.get(str(x), 0) + 1
        faces = sorted(sorted(str(self.names[v]) for v in f) for f in self.F)
        d = dict(kind=self.kind, verts=len(self.names), seam=len(self.seam), faces=len(self.F), valence=hist,
                 loops={n: len(v) for n, v in sorted(self.loops.items())}, sides=SIDES[self.kind],
                 rings=len(self.rings), conn=hashlib.sha256(json.dumps(faces).encode()).hexdigest()[:16])
        return d, hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()[:16]

    def key(self):
        return self.kind + ':' + json.dumps(self.counts, sort_keys=True)

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


def limb_rings(c):
    """Ring roles of a limb after its socket loop, from counts: [cap], [mass], hinge rings per inner joint, [mass], paw, sole.
    cap=0 leaves the cap ring out where the first joint sits right under the body (the socket loop then meets the hinge)."""
    out = ['cap'] * c.get('cap', 1)
    for b, h in enumerate(c['hinge']):
        out += ['mass'] * c['mass'][b] + [('hinge', b, i) for i in range(h)]
    b = len(c['hinge'])
    out += ['mass'] * (c['mass'][b] if len(c['mass']) > b else 0) + ['paw', 'sole']
    return out


def body_template(kind='quadruped', counts=None):
    """The topology template of a body type. counts overrides COUNTS[kind] (ring counts only: the side counts of
    SIDES[kind] are fixed by the box and its blocks)."""
    if kind != 'quadruped':
        raise ValueError('only the quadruped template exists')        # MVP-STUB: the biped template is a later task
    C = dict(COUNTS[kind], **{k_: v for k_, v in (counts or {}).items() if k_ != 'sides'})
    if (counts or {}).get('sides') and any(SIDES[kind].get(k_) != v for k_, v in counts['sides'].items()):
        raise ValueError(f"side counts are fixed by the template: {SIDES[kind]}")
    assert C['head'] >= 4, 'the head needs 4 rings (occiput, ear line, brow, stop)'
    t = Topo(kind, C)
    R = 8 + C['trunk_mid']
    t.rows = dict(n=R, hip=2, shoulder=R - 3)
    V = lambda i, j: t.id[('trunk', i, j)]
    for i in range(R):
        for j in range(8):
            t.v(('trunk', i, j), seam=j in (0, 7))
    for i in range(R - 1):
        for j in range(7):
            t.f([V(i, j), V(i + 1, j), V(i + 1, j + 1), V(i, j + 1)], key=('trunk', i, j))
        t.rings[('trunk', i)] = [V(i, j) for j in range(8)]
    t.rings[('trunk', R - 1)] = [V(R - 1, j) for j in range(8)]
    for part, row, rear in (('rump', 0, True), ('chest', R - 1, False)):          # the two end faces of the box: 2 x 3 per half
        g = {(0, 3): V(row, 0), (1, 3): V(row, 1), (2, 3): V(row, 2), (2, 2): V(row, 3), (2, 1): V(row, 4), (2, 0): V(row, 5),
             (1, 0): V(row, 6), (0, 0): V(row, 7)}
        for a, b in ((0, 2), (0, 1), (1, 2), (1, 1)):
            g[(a, b)] = t.v((part, a, b), seam=a == 0)
        for a in range(2):
            for b in range(3):
                q = [g[(a, b)], g[(a + 1, b)], g[(a + 1, b + 1)], g[(a, b + 1)]]
                t.f([q[0], q[3], q[2], q[1]] if rear else q, key=(part, a, b))
    F = lambda *key: t.fid[key]

    def branch(name, faces, n, start=None, reverse=False):
        ring, border = t.grow(faces, name, 0, start, reverse)
        t.loops[name + '.border'], t.loops[name + '.socket'] = border, ring
        for r in range(1, n + 1):
            ring, _ = t.grow(faces, name, r, ring[0], reverse)
        return ring

    for name, mid in (('hind', t.rows['hip']), ('fore', t.rows['shoulder'])):
        roles = limb_rings(C[name])
        t.limbs[name] = dict(roles=roles, rows=(mid - 1, mid, mid + 1))
        branch(name, [F('trunk', mid - 1, 4), F('trunk', mid - 1, 5), F('trunk', mid, 4), F('trunk', mid, 5)], len(roles), V(mid, 4))
        t.rename(('trunk', mid, 5), (name, 'cap', 0))
    branch('tail', [F('rump', 0, 2)], C['tail'])
    neck = [F('chest', 0, 1), F('chest', 1, 1), F('chest', 0, 2), F('chest', 1, 2)]
    ring = branch('neck', neck, C['neck'], reverse=True)
    for r in range(C['head']):
        ring, _ = t.grow(neck, 'head', r, reverse=True)
    H = C['head'] - 1                                                    # the stop: the head's front ring
    branch('ear', [F('head', H - 2, 1), F('head', H - 1, 1)], C['ear'])   # a 1 x 2 socket on the skull's top corner, centred on ring H - 2
    # the eye block turns the head's front corner: two side faces behind the stop and the front face beside the muzzle
    ring, border = t.grow([F('head', H - 1, 2), F('head', H, 2), F('chest', 1, 2)], 'eye', 0)
    t.loops['eye.border'], t.loops['eye'] = border, ring
    branch('muzzle', [F('chest', 0, 1), F('chest', 0, 2)], C['muzzle'], reverse=True)
    t.rename(('chest', 1, 2), ('face', 'side', 0))
    t.rename(('chest', 0, 2), ('muzzle', 'cap', 0))
    N = lambda *n: t.id[n]
    nk = [N('neck', r, 0) for r in range(C['neck'] + 1)]
    hd = lambda k_: [N('head', r, k_) for r in range(C['head'])]
    t.lines = dict(
        topline=[V(i, 0) for i in range(R)] + nk + hd(0),
        back_edge=[V(i, 2) for i in range(R)] + [N('neck', r, 2) for r in range(C['neck'] + 1)] + hd(2),
        flank=[V(i, 3) for i in range(R)], upper_flank=[V(i, 4) for i in range(R)],
        belly=[V(i, 6) for i in range(R)], keel=[V(i, 7) for i in range(R)],
        brow=hd(2), jaw=hd(4) + [N('muzzle', r, 3) for r in range(C['muzzle'] + 1)],
        mouth=hd(3) + [N('face', 'side', 0)] + [N('muzzle', r, 2) for r in range(C['muzzle'] + 1)])
    t.check()
    return t


def quad_warp(a, b, c, d):
    """Degrees between the two triangles of the quad a b c d, split on its a - c diagonal (the one Blender renders and exports)."""
    n1, n2 = (b - a).cross(c - a), (c - a).cross(d - a)
    return math.degrees(n1.angle(n2)) if n1.length > 1e-12 and n2.length > 1e-12 else 0.0


# ---------------------------------------------------------------- the fit (Blender)
class Tab:
    """A part's stations (part_rings, dense): read at any t (the centre runs on straight past the ends) or at a y."""

    def __init__(self, gp, part):
        import numpy as np
        from carve import part_rings
        self.np = np
        R = part_rings(gp, part, 81, ends=True)
        self.t = np.array([r['t'] for r in R]); self.c = np.array([r['centre'] for r in R])
        self.w = np.array([r['width'] for r in R]); self.d = np.array([r['depth'] for r in R])
        self.p = np.array([r['p'] for r in R]); self.uw = [(r['u'], r['w']) for r in R]

    def at(self, t):
        from mathutils import Vector
        np = self.np
        f = lambda a: float(np.interp(t, self.t, a))
        c = Vector((f(self.c[:, 0]), f(self.c[:, 1]), f(self.c[:, 2])))
        for e, i, j in ((self.t[0], 0, 4), (self.t[-1], -1, -5)):
            if (t < e and i == 0) or (t > e and i == -1):
                c += Vector((self.c[i] - self.c[j]) / (self.t[i] - self.t[j]) * (t - e))
        u, w = self.uw[int(np.argmin(np.abs(self.t - t)))]
        return dict(centre=c, width=f(self.w), depth=f(self.d), p=f(self.p), u=Vector(u), w=Vector(w))

    def at_y(self, y):
        i = int(self.np.argmin(self.np.abs(self.c[:, 1] - y)))
        return self.at(self.t[i])


def quadruped_spec(tm, k, **over):
    """What the fit reads besides the guide, with defaults from J and the part stations. A program overrides any of:
      rows     trunk rows rump -> chest front: [(y of the row's centre, lean degrees: + = the top leans back)]
      neck     t on the neck part: the neck border, the neck socket loop, then the neck rings
      head     t on the head part (0 = the head joint, 1 = the snout joint) of the head rings; the last is the stop
      muzzle   t of the muzzle's socket loop and rings
      tail     t on the tail part: socket loop, rings; tail_border (row, border): how far from the haunch's rear row toward
               the tail's socket loop the rump row and the tail's border sit (0..1)
      hip_lean   degrees (rear, middle, front) of the haunch block's rows: negative = the top leans forward, so the rows
               radiate from a tail root that sits on top of the rump
      span     per limb (front, rear): the block's reach either side of the root joint, x its default (a wolf's haunch ends
               where its rump does: the rear reach is cut so the rump keeps a row)
      top / pad / root   per limb: how far up the flank the scapula / haunch border sits (0 = the root joint, 1 = the
               back), the border's margin round the limb root (x the limb's width), where on the first bone the first
               free ring sits
      nose     the t whose section the last muzzle ring takes (a blunt nose block); head_fracs: where the head's
               half-ring points sit along the section (0 top seam .. 1 chin)
      eye, ear  loop sizes (x the head's width); offsets  {name: amount x the local width}, clamped"""
    from mathutils import Vector
    import bmkit as B
    (J, plan), gp = B.cage_plan(k.meta), k.guide_parts
    C, R = tm.counts, tm.rows['n']
    T = {n: Tab(gp, n) for n in ('torso', 'neck', 'head')}
    lm = k.meta.get('landmarks') or {}
    S = dict(top=dict(fore=0.4, hind=0.4), pad=dict(fore=0.15, hind=0.15), span=dict(fore=(1.0, 1.0), hind=(1.0, 1.0)), root=dict(fore=0.62, hind=0.62),
             block=dict(fore=0.32, hind=0.38),
             socket=(0.4, 0.75), hinge_ratio=0.55, paw=0.62, eye=0.13, tail_border=(0.4, 0.75), ear=dict(a=0.16, b=0.07, f=None, s=None), offsets={})
    for k_ in ('pad', 'span', 'top', 'root', 'block'):
        S[k_].update(over.get(k_, {}))
    dn = (Vector(J[plan['head']]) - Vector(J[plan['neck']])).normalized()
    Ln = math.degrees(math.atan2(dn.z, -dn.y))                           # the neck's rise: its rings lean back by this
    rows = [None] * R
    lean = [0.0] * R
    for name, mid in (('hind', tm.rows['hip']), ('fore', tm.rows['shoulder'])):
        c = plan['limbs'][name]
        L = Tab(gp, name)
        r = L.at(0.3 * (Vector(J[c[1]]) - Vector(J[c[0]])).length / sum((Vector(J[b]) - Vector(J[a])).length for a, b in zip(c, c[1:])))
        ry = max(0.5 * r['depth'] + S['pad'][name] * r['width'],        # the block spans the UPPER limb's mass (scapula, thigh),
                 S['block'][name] * T['torso'].at_y(J[c[0]][1])['depth'])   # not the leg under it: x the trunk's depth at the root
        for i, sg in ((mid - 1, S['span'][name][1]), (mid, 0), (mid + 1, -S['span'][name][0])):
            rows[i] = J[c[0]][1] + sg * ry
        S.setdefault('limb', {})[name] = dict(width=r['width'], depth=r['depth'], ry=ry)
    sh = tm.rows['shoulder']
    for i, f in ((sh - 2, 0.1), (sh - 1, 0.3), (sh, 0.6), (sh + 1, 0.9), (sh + 2, 1.0)):
        if 0 <= i < R:
            lean[i] = f * Ln
    for i, l in zip((tm.rows['hip'] - 1, tm.rows['hip'], tm.rows['hip'] + 1), over.get('hip_lean', (0.0, 0.0, 0.0))):
        lean[i] = l
    for name, mid in (('hind', tm.rows['hip']), ('fore', tm.rows['shoulder'])):       # a leaning row crosses the root joint's height at its y
        for i in (mid - 1, mid, mid + 1):
            rows[i] -= (J[plan['limbs'][name][0]][2] - T['torso'].at_y(rows[i])['centre'].z) * math.tan(math.radians(lean[i]))
    a, b = tm.rows['hip'] + 1, sh - 1
    for i in range(a + 1, b):
        rows[i] = rows[a] + (rows[b] - rows[a]) * (i - a) / (b - a)
    rows[0] = rows[1] + 0.45 * S['limb']['hind']['ry']
    rows[R - 1] = min(rows[R - 2] - 0.4 * S['limb']['fore']['ry'], T['neck'].at(0.03)['centre'].y + 0.25 * S['limb']['fore']['ry'])
    S['rows'] = list(zip(rows, lean))
    # head rings from the landmarks: the stop, the brow ring as far behind the eye as the stop is ahead of it, the ear line
    # on the ear, the occiput one step behind; neck rings evenly from the neck's border to the occiput
    hp = gp['head']
    h0, h1 = Vector(J[plan['head']]), Vector(J[plan['snout']])
    tl = lambda p: (Vector(p) - h0).dot(h1 - h0) / (h1 - h0).length_squared
    stop = hp['stations'][hp.get('cut', 3)]['s']
    ty = tl(lm['eye']) if 'eye' in lm else stop - 0.12
    te = tl(lm['ear']) if 'ear' in lm else ty - 0.4
    stop = max(stop, ty + 0.1)
    n = C['head']
    hs = [0.0] * n
    hs[n - 1] = stop
    hs[n - 2] = ty - min(stop - ty, 0.16)
    hs[n - 3] = min(te, hs[n - 2] - 0.12)
    step = min(0.3, max(0.18, hs[n - 2] - hs[n - 3]))
    for q in range(n - 4, -1, -1):
        hs[q] = hs[q + 1] - step
    S['head'] = hs

    def afrac(p, t):                                                     # a landmark's place round the head's section (0 top seam .. 1 chin)
        c = T['head'].at(t)['centre']
        return (math.pi / 2 - math.atan2(p[2] - c.z, max(1e-6, p[0]))) / math.pi

    fe = afrac(lm['ear'], hs[n - 3]) if 'ear' in lm else 0.2
    fy = afrac(lm['eye'], ty) if 'eye' in lm else 0.36
    he, hy = over.get('ear_block', 0.11), over.get('eye_block', 0.10)
    HF = []
    for q in range(n):                                                   # half-ring points: the ear block's two lines either side of the
        f = [0.0, 0.09, 0.30, 0.5, 0.69, 0.86, 1.0]                      # ear (rings n-4 .. n-2), the brow and cheek lines either side of
        ear_r, eye_r = n - 4 <= q <= n - 2, q >= n - 3                   # the eye (rings n-3 .. n-1)
        if ear_r:
            f[1] = max(0.04, fe - he)
        if ear_r and eye_r:
            wg = 0.65 if q == n - 3 else 0.35
            f[2] = wg * (fe + he) + (1 - wg) * (fy - hy)
        elif ear_r:
            f[2] = fe + he
        elif eye_r:
            f[2] = fy - hy
        if eye_r:
            f[3] = fy + hy
        if q == n - 1:
            f[1], f[5] = 0.15, 0.85
        f[1] = min(f[1], 0.16)
        f[2] = min(max(f[2], f[1] + 0.09), 0.42)
        f[3] = min(max(f[3], f[2] + 0.1), 0.6)
        f[4] = max(f[4], f[3] + 0.1)
        f[5] = max(f[5], f[4] + 0.08)
        HF.append(f)
    S['head_fracs'] = HF
    n = C['neck']
    t_end = 1.0 + hs[0] * (h1 - h0).length / max(1e-6, (h0 - Vector(J[plan['neck']])).length)
    S['neck'] = [0.03 + (t_end - 0.03) * i / (n + 2) for i in range(n + 2)]
    n = C['muzzle']
    S['muzzle'] = [stop + 0.07] + [stop + (0.97 - stop) * (i + 1) / n for i in range(n)]
    S['nose'] = 0.85                                                    # the nose end is sized as the muzzle at this t: a blunt block
    n = C['tail']
    S['tail'] = [0.14] + [0.14 + 0.78 * (i + 1) / n for i in range(n)]
    for k_, v in over.items():
        if isinstance(v, dict) and isinstance(S.get(k_), dict):
            S[k_].update(v)
        else:
            S[k_] = v
    return S


def fit_template(tm, k, guide, spec=None):
    """Place every named vertex of the template on the guide and return the body object (mirrored half).
    tm.co then maps every vertex name to its position: bmkit's gates find the named sets by it."""
    import numpy as np
    from mathutils import Vector
    import bmesh
    import bmkit as B
    from carve import section_corners, _tree, _super_r
    assert tm.kind == 'quadruped'
    S = spec or quadruped_spec(tm, k)
    import bmkit as B
    (J, plan), gp = B.cage_plan(k.meta), k.guide_parts
    lm = k.meta.get('landmarks') or {}
    C, R = tm.counts, tm.rows['n']
    tree = _tree(guide)
    X = Vector((1, 0, 0))
    P = [None] * len(tm.names)
    N = lambda *n: tm.id[n]
    TT = {n: Tab(gp, n) for n in ('torso', 'neck', 'head')}
    lean_w = lambda deg: Vector((0, math.sin(math.radians(deg)), math.cos(math.radians(deg))))

    owner = {}

    def near(p, mm=0.08):
        q = tree.find_nearest(p)[0]
        return q if q is not None and (q - p).length <= mm else p

    def section(key, ids, r, n, low=None, **kw):
        """low: under a limb root the rays run down into the leg; the lower half comes back to low x the part's own section."""
        sc = section_corners(guide, r, n, **kw)
        moved = set()
        if low:
            c, u, w = Vector(r['centre']), Vector(r['u']), Vector(r['w'])
            for q, p in enumerate(sc['points']):
                x, y = (p - c).dot(u), (p - c).dot(w)
                rr = math.hypot(x, y)
                if y < 0 and rr > 1e-6:
                    e = low * _super_r(math.atan2(y, x), r['width'] / 2, r['depth'] / 2, max(r.get('p', 2.0), 1.0))
                    if rr > e:
                        p.xyz = c + (p - c) * (e / rr)
                        moved.add(q)
        for q, (i, p) in enumerate(zip(ids, sc['points'])):
            P[i] = p.copy()
            owner[i] = None if q in moved else key
        tm.corners[key] = dict(ids=list(ids), corners=[tuple(c) for c in sc['corners']], width=math.sqrt(max(1e-9, r['width'] * r['depth'])))
        return sc

    # ---- trunk rows: the scapula / haunch block rows first (their upper-flank and lower-flank lines are pinned), then the rest
    tors = TT['torso']
    rowr = []
    for y, ln in S['rows']:
        st = tors.at_y(y)
        rowr.append(dict(st, u=X, w=lean_w(ln)))
    pins = {}
    for name, c in plan['limbs'].items():
        Jr = Vector(J[c[0]])
        lw = S['limb'][name]
        for i in tm.limbs[name]['rows']:
            st = rowr[i]
            top = st['centre'].z + st['depth'] / 2
            pins[i] = {4: ('z', Jr.z + S['top'][name] * (top - Jr.z)), 6: ('x', max(Jr.x - 0.5 * lw['width'] - 0.3 * lw['width'], 0.4 * Jr.x))}
    fr = {}
    for i in sorted(pins):
        fr[i] = section(('trunk', i), tm.rings[('trunk', i)], rowr[i], 7, half=True, pins=pins[i], lim=(0.6, 1.25), low=S.get('low', 1.03))['fracs']
    hip, sh = tm.rows['hip'], tm.rows['shoulder']
    for m_ in (hip, sh):                                                 # the block's middle row cuts through the limb: its belly-line
        i = N('trunk', m_, 6)                                            # point is read off the rows either side of the limb
        P[i] = (P[N('trunk', m_ - 1, 6)] + P[N('trunk', m_ + 1, 6)]) / 2
        owner[i] = None
    for i in range(R):
        if i in pins:
            continue
        if i <= hip:
            f = fr[hip - 1]
        elif i >= sh:
            f = fr[sh + 1]
        else:
            q = (i - (hip + 1)) / (sh - 1 - (hip + 1))
            f = [(1 - q) * a + q * b for a, b in zip(fr[hip + 1], fr[sh - 1])]
        section(('trunk', i), tm.rings[('trunk', i)], rowr[i], 7, half=True, fracs=f, lim=(0.6, 1.25))

    def tube(part, tab, ts, ids_of, n, leans=None, lim=(0.5, 1.6), fracs=None, size_t=None, snap=0.4):
        """Midline rings of a part at ts; leans (degrees) override the stations' own planes."""
        out = []
        for q, t in enumerate(ts):
            st = tab.at(t)
            if leans is not None:
                st = dict(st, w=lean_w(leans[q]))
            st['u'] = X
            if size_t and size_t[q] is not None:                         # sized as another station (a blunt nose block)
                s2 = tab.at(size_t[q])
                st = dict(s2, u=X, w=st['w'], centre=s2['centre'])
                sc = section_corners(guide, st, n, half=True, lim=lim)
                mv = tab.at(t)['centre'] - s2['centre']
                for i, p in zip(ids_of(q), sc['points']):
                    P[i] = p + mv
                    owner[i] = None
                out.append(sc)
                continue
            out.append(section((part, q), ids_of(q), st, n, half=True, lim=lim, fracs=fracs[q] if fracs else None, snap=snap))
        return out

    def smooth_leans(tabs_ts):
        ls = []
        for tab, t in tabs_ts:
            w = tab.at(t)['w']
            ls.append(math.degrees(math.atan2(w.y, w.z)))
        for _ in range(2):
            ls = [ls[0]] + [0.25 * ls[i - 1] + 0.5 * ls[i] + 0.25 * ls[i + 1] for i in range(1, len(ls) - 1)] + [ls[-1]]
        return ls

    # ---- neck and head: the neck's border is the chest row's upper five points and the two chest-front points
    nb = [N('trunk', R - 1, j) for j in range(5)] + [N('chest', 1, 1), N('chest', 0, 1)]
    seq = [(TT['neck'], t) for t in S['neck']] + [(TT['head'], t) for t in S['head']]
    nn = len(S['neck'])
    lean_of = lambda w: math.degrees(math.atan2(w.y, w.z))
    l0, l1 = lean_of(TT['neck'].at(S['neck'][0])['w']), lean_of(TT['head'].at(0.3)['w'])
    ls = S.get('leans') or [l0 + (l1 - l0) * min(1.0, max(0.0, (q - nn + 1) / 4)) for q in range(len(seq))]     # the neck's rings keep
    #                                                         the neck's plane; the head's fan from it to the head's own by the fourth
    tube('neck', TT['neck'], S['neck'], lambda q: nb if q == 0 else tm.rings[('neck', q - 1)], 6, ls[:nn])
    tube('head', TT['head'], S['head'], lambda q: tm.rings[('head', q)], 6, ls[nn:], fracs=S.get('head_fracs'), snap=0.2)
    hw = TT['head'].at(0.0)['width']

    def keep_ahead(prev, nxt, gap):
        """Every vertex of the ring nxt lies at least gap ahead of its vertex on prev (along the line between the rings'
        centres): two rings of a chain never cross, however their planes lean."""
        d = sum((P[i] for i in nxt), Vector()) / len(nxt) - sum((P[i] for i in prev), Vector()) / len(prev)
        d.x = 0.0
        if d.length < 1e-6:
            return
        d.normalize()
        for a_, b_ in zip(prev, nxt):
            s_ = (P[b_] - P[a_]).dot(d)
            if s_ < gap:
                P[b_] = P[b_] + d * (gap - s_)

    chain = [nb] + [tm.rings[('neck', q)] for q in range(C['neck'] + 1)] + [tm.rings[('head', q)] for q in range(C['head'])]
    for a_, b_ in zip(chain, chain[1:]):
        keep_ahead(a_, b_, 0.07 * hw)
    H = C['head'] - 1
    tm.joint_rings[plan['neck']] = [('neck', q) for q in range(C['neck'] + 1)]
    # ---- muzzle: socket loop and rings on the head part; the nose plane closes it
    mz = tube('muzzle', TT['head'], S['muzzle'], lambda q: tm.rings[('muzzle', q)], 4, lim=(0.6, 1.4),
              size_t=[None] * C['muzzle'] + [S['nose']])
    P[N('face', 'side', 0)] = section_corners(guide, dict(TT['head'].at((S['head'][-1] + S['muzzle'][0]) / 2), u=X), 4, half=True,
                                              lim=(0.6, 1.4))['points'][2]
    chain = [tm.loops['muzzle.border']] + [tm.rings[('muzzle', q)] for q in range(C['muzzle'] + 1)]
    for a_, b_ in zip(chain, chain[1:]):
        keep_ahead(a_, b_, 0.05 * hw)
    last = tm.rings[('muzzle', C['muzzle'])]
    hd = (Vector(J[plan['snout']]) - Vector(J[plan['head']])).normalized()
    P[N('muzzle', 'cap', 0)] = (P[last[0]] + P[last[-1]]) / 2 + hd * 0.1 * (P[last[0]] - P[last[-1]]).length
    # ---- tail: border on the rump (row 0's top two points and two rump points), socket loop, rings
    if 'extra0' in gp:
        tl = Tab(gp, 'extra0')
        tb = [N('trunk', 0, 0), N('trunk', 0, 1), N('rump', 1, 2), N('rump', 0, 2)]
        tls = smooth_leans([(tl, t) for t in S['tail']])
        tls[0] *= 0.75
        tube('tail', tl, S['tail'], lambda q: tm.rings[('tail', q)], 3, tls, lim=(0.6, 1.4))
    else:                                                                # MVP-STUB: no tail in J: a short stub off the rump
        raise ValueError('the quadruped template needs a tail chain in J (tail0, tail1)')
    # the rump: row 0 and the tail's border are straight blends from the haunch's rear row to the tail's socket loop (two
    # nested loops: their blends cannot fold over each other), each pushed OUT to the guide where the guide bulges past
    # the blend (a bear's rump) and left alone where the guide has a crevice there (between a wolf's thigh and tail)
    O = rowr[1]['centre'] + Vector((0, -0.25 * rowr[1]['depth'], 0))
    ts_ = [P[o] for o in tm.rings[('tail', 0)]]
    r1 = [P[N('trunk', 1, j)] for j in range(8)]

    def fan(a, b, f):
        q = a.lerp(b, f)
        d = (q - O).normalized()
        hit = tree.ray_cast(q, d)
        return hit[0] if hit[0] is not None and hit[3] < 0.12 and hit[1].dot(d) > 0 else q

    tgt = {2: ts_[1], 3: ts_[1], 4: ts_[2], 5: ts_[2], 6: (ts_[2] + ts_[3]) / 2, 7: ts_[3]}
    f0, f1 = S['tail_border']
    for j in range(2, 8):
        i = N('trunk', 0, j)
        P[i] = fan(r1[j], tgt[j], f0)
        owner[i] = None
    dt = (Vector(J[gp['extras']['extra0'][1]]) - Vector(J[gp['extras']['extra0'][0]])).normalized()
    behind = lambda q, *ids: q + dt * max([0.0] + [(P[i] - q).dot(dt) + 0.02 for i in ids])     # further along the tail than these
    for i, a_, b_, ids in ((tb[0], r1[0], ts_[0], [N('trunk', 1, 0)]), (tb[1], (r1[1] + r1[2]) / 2, ts_[1], [N('trunk', 1, 1), N('trunk', 0, 2)]),
                           (tb[2], (r1[4] + r1[5]) / 2, ts_[2], [N('trunk', 0, 4), N('trunk', 0, 5)]), (tb[3], r1[7], ts_[3], [N('trunk', 0, 7)])):
        P[i] = behind(fan(a_, b_, f1), *ids)
        owner[i] = None
        if i in tm.seam:
            P[i].x = 0.0
    for q in range(C['tail'] + 1):                                       # the tail leaves the rump behind its border, ring after ring
        for i, o in zip(tm.rings[('tail', q)], tb if q == 0 else tm.rings[('tail', q - 1)]):
            P[i] = behind(P[i], o)
    for a in (1, 0):
        P[N('rump', a, 1)] = P[N('rump', a, 2)].lerp(P[N('trunk', 0, 6 if a else 7)], 0.5)
    # ---- limbs
    for name, c in plan['limbs'].items():
        tab = Tab(gp, name)
        Jp = [Vector(J[n]) for n in c]
        seg = [(b - a).length for a, b in zip(Jp, Jp[1:])]
        tot = sum(seg)
        cum = [0.0]
        for l in seg:
            cum.append(cum[-1] + l)
        dirs = [(b - a).normalized() for a, b in zip(Jp, Jp[1:])]
        s = -1.0 if name.lower().startswith(('hind', 'leg', 'rear', 'back')) else 1.0        # rom_poses' own rule
        roles = tm.limbs[name]['roles']
        hinge_n = C[name]['hinge']
        # where each ring sits (metres along the chain), its shear and its tangent
        size = lambda d: (lambda r: math.sqrt(r['width'] * r['depth']))(tab.at(d / tot))
        HG = {}
        for b, hn in enumerate(hinge_n):
            dj = cum[b + 1]
            e = min(0.5 * size(dj), 0.4 * min(seg[b], seg[b + 1]))
            fl = S['hinge_ratio'] * e
            flex = s * (1 if b % 2 == 0 else -1)                         # +1: the joint closes at the front
            if hn == 3:
                HG[b] = [(dj - (e + fl) / 2, +(e - fl) / 2 * flex), (dj, 0.0), (dj + (e + fl) / 2, -(e - fl) / 2 * flex)]
            else:
                g = min(0.45 * size(dj), 0.5 * min(seg[b], seg[b + 1]))
                HG[b] = [(dj - g / 2, 0.0), (dj + g / 2, 0.0)][:hn]
        zl = None
        ring_d = []
        prev_end = S['root'][name] * seg[0]
        bone = 0
        for ri, role in enumerate(roles):
            if role == 'cap':
                ring_d.append(None)
            elif role == 'mass':
                nxt = next((x for x in roles[ri + 1:] if x != 'mass'), None)
                if bone == 0:
                    d = min(prev_end, HG[0][0][0] - 0.6 * (HG[0][1][0] - HG[0][0][0])) if HG else prev_end
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
                if hinge_n[role[1]] == 3:
                    tm.hinges.setdefault(c[role[1] + 1], dict(limb=name, rings=[], flex=[1, 2, 3] if s * (1 if role[1] % 2 == 0 else -1) > 0 else [5, 6, 7],
                                                              ext=[5, 6, 7] if s * (1 if role[1] % 2 == 0 else -1) > 0 else [1, 2, 3]))['rings'].append(ri + 1)
            else:
                ring_d.append(role)
        first_free = next(i for i, x in enumerate(ring_d) if x is not None)

        def frame(d):
            bi = max(i for i in range(len(seg)) if d >= cum[i] - 1e-9)
            tau = dirs[bi].copy()
            for ji in range(1, len(Jp) - 1):
                dj = d - cum[ji]
                rng = 0.6 * min(seg[ji - 1], seg[ji])
                if abs(dj) < rng:
                    other = dirs[ji - 1] if dj >= 0 else dirs[ji]
                    tau = (dirs[bi] * (1 - 0.5 * (1 - abs(dj) / rng)) + other * 0.5 * (1 - abs(dj) / rng)).normalized()
            u = (X - tau * X.dot(tau)).normalized()
            w = tau.cross(u).normalized()
            return tau, u, w

        planti = any(q.get('foot') for q in gp[name]['stations'])
        foot = gp.get(name + '_foot')
        fs = foot['stations'] if foot else None
        fc = (Vector(fs[0]['centre']) + Vector(fs[-1]['centre'])) / 2 if fs else Jp[-1].copy()
        flen = (Vector(fs[0]['centre']) - Vector(fs[-1]['centre'])).length + 0.5 * fs[0]['depth'] if fs else seg[-1]
        lastc = None
        frames = {}
        for ri, rd in enumerate(ring_d):
            ids = tm.rings[(name, ri + 1)]
            if rd is None:
                continue
            if rd == 'paw':
                continue
            if rd == 'sole':                                             # the footprint, read off the guide just above the ground;
                cc = Vector((fc.x, fc.y, max(0.012, 0.25 * fc.z)))       # the paw ring is the same outline lifted: a block, toes lower
                r = dict(centre=cc, u=X, w=Vector((0, -1, 0)), width=1.5 * flen, depth=1.5 * flen, p=2.0)
                section((name, ri + 1), ids, r, 8, lim=(0.05, 1.0))
                tm.corners.pop((name, ri + 1))
                if os.environ.get('BMK_TMPL_DBG'):
                    B.say('DBG sole', name, 'centre', tuple(round(q, 3) for q in cc), 'flen', round(flen, 3), 'last', tuple(round(q, 3) for q in lastc),
                          [tuple(round(q, 3) for q in P[i]) for i in ids])
                ext = max(1e-6, max(cc.y - P[i].y for i in ids))
                for i, i2 in zip(ids, tm.rings[(name, ri)]):
                    P[i].z = 0.0
                    fwd = max(0.0, (cc.y - P[i].y) / ext)
                    P[i2] = Vector((cc.x + (P[i].x - cc.x) * 0.94, cc.y + (P[i].y - cc.y) * 0.94, S['paw'] * lastc.z * (1 - 0.45 * fwd)))
                    owner[i2] = None
                P[N(name, 'cap', 0)] = sum((P[i] for i in ids), Vector()) / 8
                continue
            d, shr = rd
            st = tab.at(d / tot)
            if planti and d > cum[-2]:                                   # a plantigrade limb's stations run into the foot wedge
                st = dict(tab.at(cum[-2] / tot - 1e-3))                  # below the last joint: the ring stays on the bone
                st['centre'] = Jp[-2] + dirs[-1] * (d - cum[-2]) + (st['centre'] - Jp[-2])
            tau, u, w = frame(d)
            r = dict(st, u=u, w=w)
            section((name, ri + 1), ids, r, 8, lim=(0.7, 1.3))
            if shr:
                rw = max(1e-6, max(abs((P[i] - st['centre']).dot(w)) for i in ids))
                for i in ids:
                    P[i] += tau * (shr * (P[i] - st['centre']).dot(w) / rw)
            lastc = st['centre']
            frames[ri + 1] = (st['centre'], tau, w)
        for h in tm.hinges.values():                                     # the hinge fan, measured as the gate measures it, set to the ratio
            if h['limb'] != name:
                continue
            R3 = [tm.rings[(name, r)] for r in h['rings']]
            sg = 1.0 if h['flex'][0] == 1 else -1.0
            for _ in range(3):
                gap = lambda ks: sum((P[R3[q][k_]] - P[R3[q + 1][k_]]).length for q in (0, 1) for k_ in ks) / 6
                fl_, ex_ = gap(h['flex']), gap(h['ext'])
                x = (fl_ - S['hinge_ratio'] * ex_) / (1 + S['hinge_ratio']) / 0.8
                for r, dirn in ((h['rings'][0], 1.0), (h['rings'][2], -1.0)):
                    cc, tau, w = frames[r]
                    ids = tm.rings[(name, r)]
                    rw = max(1e-6, max(abs((P[i] - cc).dot(w)) for i in ids))
                    for i in ids:
                        P[i] += tau * (dirn * sg * x * (P[i] - cc).dot(w) / rw)
        # the socket loop and the cap ring: between the border on the trunk and the first free ring, on the guide
        bd = tm.loops[name + '.border']
        free = tm.rings[(name, first_free + 1)]
        n_between = first_free + 1                                       # socket loop + the 'cap' rings before the first free ring
        for k_ in (3, 4, 5):                                             # under the body the first free ring stays below the border
            P[free[k_]].z = min(P[free[k_]].z, P[bd[k_]].z - 0.02)
        lastj = len(hinge_n) - 1                                         # below the last joint a ring never dips under the next one
        q0 = next(ri for ri, x in enumerate(roles) if isinstance(x, tuple) and x[1] == lastj)
        for q in range(len(roles) - 1, q0, -1):
            for a_, b_ in zip(tm.rings[(name, q)], tm.rings[(name, q + 1)]):
                if P[a_].z < P[b_].z + 0.004:
                    P[a_].z = P[b_].z + 0.004
        # the upper limb: the socket loop and the cap rings fan from the border on the body's side to the first free ring.
        # The outer five lines take the guide's surface as seen from the first bone (the scapula / thigh mass swells, then
        # tapers to the hinge); the three armpit lines stay a straight blend (they keep their order under the body)
        SOCK = {1: (0.5,), 2: (0.4, 0.75), 3: (0.22, 0.5, 0.78)}
        fr_ = (S.get('fan') or {}).get(name) or SOCK.get(n_between) or [(q + 1) / (n_between + 1) for q in range(n_between)]
        a0, a1 = Jp[0], Jp[1]
        for q in range(n_between):
            f = fr_[q]
            for k_, i in enumerate(tm.rings[(name, q)]):
                m_ = P[bd[k_]].lerp(P[free[k_]], f)
                if k_ in (3, 4, 5):
                    P[i] = near(m_, 0.015)
                    continue
                ax = a0 + (a1 - a0) * min(1.0, max(0.0, (m_ - a0).dot(a1 - a0) / (a1 - a0).length_squared))
                d_ = m_ - ax
                hit = tree.ray_cast(ax, d_.normalized()) if d_.length > 1e-6 else (None,)
                P[i] = hit[0].copy() if hit[0] is not None and 0.7 * d_.length <= hit[3] <= 1.8 * d_.length else near(m_, 0.06)
            tm.pinned.update(tm.rings[(name, q)])
    # ---- the eye loop and the ear, pinned to the landmarks
    hw = TT['head'].at(0.0)['width']

    def loop_on(ids, border, centre, a, b, axis):
        """ids round `centre` on the guide, an ellipse (a along axis, b across), evenly spaced, turned to line up with the border."""
        hit = tree.find_nearest(centre)
        c, n = hit[0], hit[1]
        t1 = (axis - n * axis.dot(n)).normalized()
        t2 = n.cross(t1)
        m = len(border)
        cb = sum((P[o] for o in border), Vector()) / m
        ang = [math.atan2((P[o] - cb).dot(t2), (P[o] - cb).dot(t1)) for o in border]
        sg = 1.0 if sum(((ang[(q + 1) % m] - ang[q] + math.pi) % (2 * math.pi)) - math.pi for q in range(m)) > 0 else -1.0
        th0 = math.atan2(sum(math.sin(ang[q] - sg * 2 * math.pi * q / m) for q in range(m)),
                         sum(math.cos(ang[q] - sg * 2 * math.pi * q / m) for q in range(m)))
        room = min(math.hypot((P[o] - c).dot(t1) / a, (P[o] - c).dot(t2) / b) for o in border)
        if os.environ.get('BMK_TMPL_DBG'):
            B.say('DBG loop', tm.names[ids[0]][0], 'centre', tuple(round(q, 3) for q in c), 'n', tuple(round(q, 2) for q in n), 'a b room', round(a, 3), round(b, 3), round(room, 2),
                  'border', [tuple(round(q, 3) for q in P[o]) for o in border])
        if room < 1.25:                                                   # the loop stays inside its block
            a, b = a * room / 1.25, b * room / 1.25
        for q, i in enumerate(ids):                                       # evenly round the centre, turned to face the border
            th = th0 + sg * 2 * math.pi * q / m
            P[i] = near(c + t1 * (a * math.cos(th)) + t2 * (b * math.sin(th)), 0.04)
        tm.pinned.update(ids)
        return c, n

    if 'eye' in lm:
        loop_on(tm.loops['eye'], tm.loops['eye.border'], Vector(lm['eye']), 1.25 * S['eye'] * hw, 0.8 * S['eye'] * hw, hd)
    else:                                                                # no landmark: the loop sits inside its block
        cb = sum((P[o] for o in tm.loops['eye.border']), Vector()) / 8
        for i, o in zip(tm.loops['eye'], tm.loops['eye.border']):
            P[i] = near(cb + (P[o] - cb) * 0.5, 0.04)
    E = S['ear']
    eb = tm.loops['ear.border']
    if 'ear' in lm and 'ear_tip' in lm:
        root, tip = Vector(lm['ear']), Vector(lm['ear_tip'])
    else:
        root = sum((P[o] for o in eb), Vector()) / len(eb)
        tip = root + Vector((0.15, 0, 1)).normalized() * 0.5 * hw
    c, n = loop_on(tm.loops['ear.socket'], eb, root, E['a'] * hw, E['b'] * hw, Vector((0, 1, 0)))
    ne = C['ear']
    ef = E['f'] or [(q + 1) / ne * 0.92 for q in range(ne)]
    es = E['s'] or [1.0 - 0.75 * (q + 1) / ne for q in range(ne)]
    for q in range(ne):
        cc = c.lerp(tip, ef[q])
        for i, o in zip(tm.rings[('ear', q + 1)], tm.loops['ear.socket']):
            P[i] = cc + (P[o] - c) * es[q]
        tm.pinned.update(tm.rings[('ear', q + 1)])
    # ---- the named offsets: planes broken on purpose (each clamped to OFFSET_CLAMP x the local width)
    mid = (hip + 1 + sh - 1) // 2
    lw = lambda name: S['limb'][name]['width']
    tw = lambda i: rowr[i]['depth']
    nkw = TT['neck'].at(0.4)['width']
    OFF = dict(
        withers=([(N('trunk', i, j), tw(i)) for i in (sh - 1, sh, sh + 1) for j in (0, 1)], Vector((0, 0, 1))),
        scapula=([(i, lw('fore')) for q in (0, 1) for k_, i in enumerate(tm.rings[('fore', q)]) if k_ in (7, 0, 1)], Vector((1, 0, 0))),
        scapula_edge=([(N('trunk', i, 4), lw('fore')) for i in tm.limbs['fore']['rows']], Vector((0.95, 0, 0.3))),
        haunch=([(i, lw('hind')) for q in (0, 1) for k_, i in enumerate(tm.rings[('hind', q)]) if k_ in (7, 0, 1)], Vector((1, 0, 0))),
        haunch_edge=([(N('trunk', i, 4), lw('hind')) for i in tm.limbs['hind']['rows']], Vector((0.95, 0, 0.3))),
        belly_tuck=([(N('trunk', i, j), tw(i)) for i in (mid, mid + 1) for j in (6, 7)], Vector((0, 0, 1))),
        ruff=([(N('neck', q, k_), nkw) for q in range(1, min(2, C['neck']) + 1) for k_ in (3, 4, 5, 6)], None),
        ruff_side=([(N('neck', q, k_), nkw) for q in range(C['neck'] + 1) for k_ in (2, 3)], Vector((1, 0, 0))),
        cheek=([(N('head', q, 3), hw) for q in range(1, H + 1)], Vector((1, 0, 0))),
        brow=([(N('head', q, 2), hw) for q in (H - 1, H)], Vector((0.5, 0, 0.85))),
        jaw=([(N('head', q, 4), hw) for q in range(1, H + 1)], Vector((0.4, 0, -0.9))),
    )
    for name, amt in (S.get('offsets') or {}).items():
        if name not in OFF:
            raise KeyError(f'no named offset {name!r}: {sorted(OFF)}')
        vs, d = OFF[name]
        amt = max(-OFFSET_CLAMP, min(OFFSET_CLAMP, amt))
        for i, wd in vs:
            dd = d if d is not None else (Vector((0, 0, -1)) if i in tm.seam else Vector((P[i].x, 0, -abs(P[i].x))).normalized())
            P[i] = P[i] + dd.normalized() * (amt * wd)
            tm.pinned.add(i)
    # ---- a light relax-and-project of what no section, socket or landmark placed (the two end faces' inner points)
    placed = {i for c_ in tm.corners.values() for i in c_['ids']} | tm.pinned | {N(n, 'cap', 0) for n in ('fore', 'hind', 'muzzle')}
    free = [i for i in range(len(P)) if i not in placed]
    nbs = tm.neighbours()
    for i in free:
        if P[i] is None:
            P[i] = sum((P[j] for j in nbs[i] if P[j] is not None), Vector()) / max(1, sum(1 for j in nbs[i] if P[j] is not None))
    for q in range(4):
        for i in free:
            avg = sum((P[j] for j in nbs[i]), Vector()) / len(nbs[i])
            P[i] = P[i].lerp(avg, 0.5)
            if q == 3 and tm.names[i][0] != 'rump':                      # (the rump's two inner points stay a flat cap under the tail)
                P[i] = near(P[i], 0.03)
    tm.co0 = {tm.names[i]: tuple(P[i]) for i in range(len(P))}           # as the sections placed them (the corner gate reads these)
    # ---- lengthwise lines run straight between landmarks: a vertex slides ALONG ITS RING toward the chord of its line
    hinge_v = {i for keys in tm.joint_rings.values() for key in keys if key[0] in tm.limbs for i in tm.rings[key]}
    lock = set(tm.pinned) | hinge_v | set(tm.rings[('trunk', R - 1)]) | {N(n_, 'cap', 0) for n_ in ('fore', 'hind')}
    for name in tm.limbs:
        lock |= set(tm.loops[name + '.border'])
    ringnb = {}
    for ids in [tm.rings[('trunk', i)] for i in range(R)] + [tm.rings[('neck', q)] for q in range(C['neck'] + 1)] + \
               [tm.rings[('tail', q)] for q in range(C['tail'] + 1)]:
        for q in range(1, len(ids) - 1):
            ringnb[ids[q]] = (ids[q - 1], ids[q + 1])
    lines = [[tm.rings[('trunk', i)][j] for i in range(R)] for j in range(1, 7)]
    lines += [[nb[k_]] + [tm.rings[('neck', q)][k_] for q in range(C['neck'] + 1)] + [tm.rings[('head', 0)][k_]] for k_ in range(1, 6)]
    lines += [[tb[k_]] + [tm.rings[('tail', q)][k_] for q in range(C['tail'] + 1)] for k_ in (1, 2)]

    def on_ring(q_, i):                                                  # the nearest point of the ring's own polyline at i
        a_, b_ = ringnb[i]
        best = None
        for s0, s1 in ((P[a_], P[i]), (P[i], P[b_])):
            e = s1 - s0
            t_ = min(1.0, max(0.0, (q_ - s0).dot(e) / max(1e-12, e.length_squared)))
            c_ = s0 + e * t_
            if best is None or (c_ - q_).length < (best - q_).length:
                best = c_
        return best

    for _ in range(S.get('fair', 3)):
        for ln in lines:
            for q in range(1, len(ln) - 1):
                i = ln[q]
                if i in lock or i not in ringnb:
                    continue
                a_, b_ = ringnb[i]
                t_ = P[b_] - P[a_]
                if t_.length < 1e-9:
                    continue
                t_.normalize()
                s_ = ((P[ln[q - 1]] + P[ln[q + 1]]) / 2 - P[i]).dot(t_)
                lm_ = 0.35 * min((P[a_] - P[i]).length, (P[b_] - P[i]).length)
                P[i] = on_ring(P[i] + t_ * max(-lm_, min(lm_, 0.5 * s_)), i)
    # ---- planarity: every quad outside the hinges settles toward its own plane (a capped move), so the flat-shaded
    # cage shows planes and plane breaks, not the diagonals of warped quads
    fixed = set(hinge_v) | set(tm.loops['eye'])
    for q in range(C['ear'] + 1):
        fixed |= set(tm.rings[('ear', q)])
    for name in tm.limbs:
        fixed |= set(tm.rings[(name, len(tm.limbs[name]['roles']))]) | {N(name, 'cap', 0)}
    hingeF = [all(v in hinge_v for v in f) for f in tm.F]
    home = [p.copy() for p in P]
    mm = S.get('planar', 0.04) * rowr[mid]['depth']
    for _ in range(S.get('planar_iters', 40)):
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
    for i in range(len(P)):
        P[i].x = 0.0 if i in tm.seam else max(P[i].x, 0.004)             # only seam vertices lie on the mirror plane
        P[i].z = max(P[i].z, 0.0)
    for name in ('fore', 'hind'):
        owner[N(name, 'cap', 0)] = None
    for key, c_ in tm.corners.items():                                   # a vertex counts for the section that placed it last
        c_['ids'] = [i for i in c_['ids'] if owner.get(i) == key and i not in tm.pinned]
        c_['names'] = [tm.names[i] for i in c_['ids']]
    if os.environ.get('BMK_TMPL_DBG'):
        ed = sorted({(round((P[a] - P[b]).length, 4), str(tm.names[a]), str(tm.names[b])) for f in tm.F for a, b in zip(f, f[1:] + f[:1])})
        for e in ed[:14]:
            B.say('DBG short edge', e)
        for f in tm.F:
            ls = [(P[a] - P[b]).length for a, b in zip(f, f[1:] + f[:1])]
            if max(ls) / max(1e-9, min(ls)) > 4.5:
                B.say('DBG long face %.1f' % (max(ls) / max(1e-9, min(ls))), [str(tm.names[i]) for i in f])
    # ---- the mesh
    bm = bmesh.new()
    bv = [bm.verts.new(p) for p in P]
    warped = 0
    for fi, f in enumerate(tm.F):                                        # the diagonal rule: a quad splits on its SHORTER diagonal
        if (P[f[0]] - P[f[2]]).length > (P[f[1]] - P[f[3]]).length + 1e-6:   # (its first and third vertex; the mirror keeps it)
            f = f[1:] + f[:1]
        bm.faces.new([bv[i] for i in f])
        warped += (not hingeF[fi]) and quad_warp(*[P[i] for i in f]) > 12.0
    B.say('template fit: non-planar quads (over 12 degrees) outside the hinges: %d of %d' % (warped, len(tm.F) - sum(hingeF)))
    B.snap_seam(bm)
    if os.environ.get('BMK_TMPL_DBG'):
        from mathutils.bvhtree import BVHTree
        bm.faces.ensure_lookup_table()
        t_ = BVHTree.FromBMesh(bm)
        cnt = {}
        for i, j in t_.overlap(t_):
            if i < j and not (set(tm.F[i]) & set(tm.F[j])):
                key = (str(tm.names[tm.F[i][0]][:2]), str(tm.names[tm.F[j][0]][:2]))
                cnt[key] = cnt.get(key, 0) + 1
        for key, n_ in sorted(cnt.items(), key=lambda x: -x[1])[:16]:
            B.say('DBG hit', n_, key)
    tm.co = {tm.names[i]: tuple(bv[i].co) for i in range(len(P))}
    k.template = tm
    if os.environ.get('BMK_TEMPLATE_STORE'):
        B.say('template signature stored:', tm.store_signature(), tm.key())
    return B.object_from_bm('body', bm)
