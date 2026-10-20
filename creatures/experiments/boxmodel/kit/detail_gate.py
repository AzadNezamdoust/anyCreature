#!/usr/bin/env python3
"""detail_gate.py — the chunky-detail gate: are fingers, toes, claws, nails, horns, spines, antennae,
tail tips, fin rays, beak tips and teeth big enough to read at GAME camera distance?

Why it exists (owner 2026-10-21): the zoo creatures are for games. On the frog and others the
fingers, toes and small details were thin sticks that vanish at game distance. Details must be
chunky, visible and understandable at a small on-screen size: 3-4 fat toes beat 5 sticks.
Bigger creatures are seen bigger on screen, so they carry MORE details (tiers, below).

Run (plain Python; it drives one headless Blender):

    py -3.11 creatures/experiments/boxmodel/kit/detail_gate.py <glb> <outdir> [--tag s4_r01] [--tier 1|2|3]
                                                                 [--prog creature.py] [--no-render] [--title frog]
    run.py <prog> --stage N --details      (gates the round, like --junctions)
    run.py <prog> --details                (probe the latest stage GLB, no rebuild)

Writes <outdir>/<tag>_details.json, <tag>_game_*.png (game-distance thumbnails), <tag>_dflag_*.png
(detail flag views), <tag>_dcrop_*.png (worst-detail crops) and <tag>_detail_sheet.jpg. Prints one
'BMK PASS|FAIL detail ...' line per gated detail. Exit 0 only when the gate passed.

WHAT IS A DETAIL. Every mesh shell is measured as a branching shape:
  - a piece shell's ROOT is where it is buried in (or touches) other geometry; a body's root is
    every vertex weighted to a trunk bone (hips/spine/chest/neck/head/...).
  - geodesic distance d from the root over the surface; the protrusions are the persistent maxima
    of d (0-dim persistence on the superlevel sets, elder rule): each tip's branch runs down to the
    level where it merges with a significant sibling (a toe fork, a finger split) or reaches the root.
    Maxima that persist less than PERSIST (x size, x shell reach) are corner noise, not branches.
  - along each branch, cross-section RINGS (level sets of d) give the min caliper width (thickness)
    and the mean caliper width (perimeter / pi) of each section; the branch's thickness is the p10
    of the ring min widths over its visible length up to WINDOW (0.70 for pointed kinds, 0.85 for
    blunt), its length the geodesic length outside other geometry.
  - kind from the piece name (claw/talon/nail, finger/hand, toe/foot/feet/paw, horn/tusk/tine/spike/
    spine/fang/mandible/tooth/beak/crest, antenna/barbel/tongue/whisker/tail, ear/fin/wing/feather/
    gill/fur/mane/tuft = plates, scute/plate/sucker/nostril/nose/shell = knobs, belt/strap/cape/... =
    gear) or, on the body, from the bone at the branch tip (tail, ear, horn, antenna, claw/finger/
    dactyl/fang, fin/pec/lobe/wing, else limb tip).

GATES (per detail item; H = creature height, S = largest bbox dimension):
  floor F = max(THICK_H x TIER_MUL[tier] x H,  PX_MIN px with the creature GAME_PX px tall)
  digit (finger/toe)  thickness >= F, length >= DIGIT_LEN_H x H, length/thickness <= DIGIT_ASPECT[tier]
                      (a long thin digit is a stick, however thick its root)
  claw/nail, pointed (horn, spine, tooth, beak ...), blunt (antenna, tail tip ...), limb tip: thickness >= F
  plate (ear, fin, wing, feather): mean caliper width >= F (a flat fin reads by its face)
  knob, gear, eye: counted as features, not gated. A 'blob' item (length < 1.5 x width) is chunky by shape.
FEATURE COUNT per tier: distinct readable feature groups (each piece object stem once, mirrored pairs
once; each body appendage kind once; each body paint region beyond the base colour once; the eye).
A group is readable when at least half of its gated items pass. Count < COUNT[tier][0] = FAIL,
> COUNT[tier][1] = WARN (tier 1 must stay few and chunky).
TIERS (owner 2026-10-21): tier 1 small (frog, imp, insects, koi, crab ...): few (3-6) very chunky,
exaggerated details; tier 2 medium (wolf, fox, goblin, knight, tiger ...): 6-12; tier 3 large/heavy
(hippo, elephant, rhino, troll, ogre, golem, dragon): 12-25, still chunky, flat colour, box-model
geometry. Auto tier from the body's mass size m = cbrt(volume): m < TIER_SIZE[0] -> 1, m > TIER_SIZE[1]
-> 3, else 2. Override: META = dict(..., detail_tier=N) in the creature .py, or --tier.

GAME DISTANCE: 8 level azimuths + 4 at +35 deg, orthographic, the creature fitted into GAME_RES px
(192): judge readability on these thumbnails at native size (the sheet also shows six at 2x nearest).
"""
import json, math, os, re, sys

KIT = os.path.dirname(os.path.abspath(__file__))
if KIT not in sys.path:
    sys.path.insert(0, KIT)
try:
    import bpy  # noqa: F401
    HAS_BPY = True
except ImportError:
    HAS_BPY = False

LIMITS = dict(
    THICK_H=0.012,             # thickness floor: share of the creature's height (tier 2/3)
    TIER_MUL={1: 2.0, 2: 1.0, 3: 1.0},    # tier 1: exaggerated, chunkier than life (2.4% H)
    GAME_PX=256,               # the game frame: the creature 256 px tall ...
    PX_MIN=3.0,                # ... and a detail must be at least 3 px across in it
    DIGIT_LEN_H=0.04,          # finger / toe visible length >= this x H
    DIGIT_ASPECT={1: 4.5, 2: 6.0, 3: 6.0},  # finger / toe length / thickness <= this (a stick above it)
    TIER_SIZE=(0.45, 1.0),     # mass size cbrt(body volume), m: < -> tier 1, > -> tier 3
    COUNT={1: (3, 8), 2: (6, 16), 3: (12, 30)},   # readable feature groups per tier (min FAIL, max WARN)
    DIGITS_PER_GROUP_T1=4,     # warn: a tier-1 hand/foot with more digits than this
    PERSIST=(0.012, 0.06),     # branch persistence floor: x S, x the shell's geodesic reach (max of both)
    BUMP=1.0,                  # a branch shorter than this x its mean width is a bump, not a detail
    BLOB=1.5,                  # an item shorter than this x its mean width is a chunky blob
    WINDOW=dict(pointed=0.70, blunt=0.85),
    RINGS=14,                  # cross-section stations per branch
    INSIDE_EPS=0.0015,         # x S: a vertex this close to / inside other geometry is buried (root)
    GAME_RES=192,
)
L_ = LIMITS

# (kind, class, words) - first match wins; classes: digit claw pointed blunt plate knob gear eye
PIECE_KINDS = [
    ('eye', 'eye', {'eye', 'lens', 'pupil'}),
    ('gear', 'gear', {'belt', 'buckle', 'vest', 'loincloth', 'kilt', 'cape', 'tabard', 'strap', 'flap', 'shield',
                      'sword', 'pauldron', 'knee', 'cop', 'visor', 'harness', 'collar', 'bracer', 'sash', 'armour',
                      'armor', 'helmet', 'weapon', 'club', 'spear', 'axe', 'cloth', 'cuff'}),
    ('claw', 'claw', {'claw', 'talon', 'nail', 'dactyl', 'hoof'}),
    ('finger', 'digit', {'finger', 'hand', 'thumb'}),
    ('toe', 'digit', {'toe', 'foot', 'feet', 'paw', 'digit'}),
    ('horn', 'pointed', {'horn', 'tusk', 'tine', 'antler', 'spike', 'spine', 'fang', 'mandible', 'crest', 'thorn',
                         'quill', 'stinger', 'barb'}),
    ('tooth', 'pointed', {'tooth', 'teeth', 'fangs'}),
    ('beak', 'pointed', {'beak', 'bill'}),
    ('antenna', 'blunt', {'antenna', 'antennae', 'barbel', 'tongue', 'whisker', 'tendril', 'feeler', 'tail'}),
    ('plate', 'plate', {'ear', 'fin', 'wing', 'feather', 'primarie', 'tailfeather', 'gill', 'fur', 'mane', 'tuft',
                        'frill', 'sail', 'membrane', 'web'}),
    ('knob', 'knob', {'scute', 'plate', 'sucker', 'nostril', 'nose', 'wart', 'bump', 'shell', 'boss', 'stud'}),
]
BONE_KINDS = [
    ('tail', 'blunt', re.compile(r'tail|tentacle', re.I)),
    ('antenna', 'blunt', re.compile(r'antenna|feeler|barbel', re.I)),
    ('ear', 'plate', re.compile(r'^ear|tuft', re.I)),
    ('horn', 'pointed', re.compile(r'horn|antler|tusk|fang', re.I)),
    ('claw', 'claw', re.compile(r'finger|dactyl|claw|pincer|chela', re.I)),
    ('fin', 'plate', re.compile(r'fin|pec|lobe|wing', re.I)),
]
GATED = {'digit', 'claw', 'pointed', 'blunt', 'plate', 'limb'}


def _words(name):
    w = re.split(r'[^A-Za-z]+|(?<=[a-z])(?=[A-Z])', name)
    return {x.lower().rstrip('s') if len(x) > 3 else x.lower() for x in w if len(x) > 1}


def piece_kind(name):
    w = _words(name) | {x.lower() for x in re.split(r'[^A-Za-z]+', name) if x}
    for kind, cls, words in PIECE_KINDS:
        if w & words:
            return kind, cls
    return 'other', 'other'


def stem(name):
    """'piece_kilt3R' -> 'kilt', 'piece_toes_L' -> 'toes', 'piece_footL' -> 'foot' (mirrored pairs once)."""
    s = re.sub(r'^piece_+', '', name)
    s = re.sub(r'\.\d+$', '', s)
    s = re.sub(r'([._]?[LR])$', '', s)
    s = re.sub(r'[._]?\d+$', '', s)
    s = re.sub(r'([._]?[LR])$', '', s)
    return s.strip('_.').lower() or name


def tier_from_prog(prog):
    if prog and os.path.exists(prog):
        m = re.search(r"detail_tier\s*=\s*([123])", open(prog, encoding='utf-8', errors='replace').read())
        if m:
            return int(m.group(1))
    return None


def find_prog(glb):
    """<creature>/stageN/x.glb -> <creature>/<creature>.py when it exists."""
    cdir = os.path.dirname(os.path.dirname(os.path.abspath(glb)))
    p = os.path.join(cdir, os.path.basename(cdir) + '.py')
    return p if os.path.exists(p) else None


# ============================================================================== Blender side
if HAS_BPY:
    import heapq
    import numpy as np
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree

    def say(*a):
        print('BMK', *a, flush=True)

    def _hull2(P):
        P = sorted(set((round(float(x), 7), round(float(y), 7)) for x, y in P))
        if len(P) < 3:
            return P
        cr = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
        lo, hi = [], []
        for p in P:
            while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0:
                lo.pop()
            lo.append(p)
        for p in reversed(P):
            while len(hi) >= 2 and cr(hi[-2], hi[-1], p) <= 0:
                hi.pop()
            hi.append(p)
        return lo[:-1] + hi[:-1]

    def ring_widths(pts):
        """3D ring points -> (min caliper width, mean caliper width = perimeter / pi, centre)."""
        P = np.asarray(pts)
        c = P.mean(0)
        if len(P) < 3:
            return None
        Q = P - c
        w, v = np.linalg.eigh(Q.T @ Q)
        a, b = v[:, 2], v[:, 1]
        H = _hull2(np.stack([Q @ a, Q @ b], 1))
        if len(H) < 3:
            ext = float(np.ptp(Q @ a)) if len(P) else 0.0
            return 0.0, 2 * ext / math.pi, c
        H = np.array(H)
        n = len(H)
        per = float(sum(np.linalg.norm(H[(i + 1) % n] - H[i]) for i in range(n)))
        mw = 1e9
        for i in range(n):
            e = H[(i + 1) % n] - H[i]
            ln = np.linalg.norm(e)
            if ln < 1e-12:
                continue
            nrm = np.array([-e[1], e[0]]) / ln
            mw = min(mw, float(np.max((H - H[i]) @ nrm) - np.min((H - H[i]) @ nrm)))
        return mw, per / math.pi, c

    class Shell:
        """One connected shell: welded vertices V, triangles T (local ids), edges, adjacency."""

        def __init__(self, g, tris):
            vid = np.unique(g.T[tris])
            loc = {int(v): i for i, v in enumerate(vid)}
            self.gid = vid
            self.V = g.V[vid]
            self.T = np.array([[loc[int(x)] for x in t] for t in g.T[tris]])
            self.tris = tris
            E = set()
            for t in self.T:
                for k in range(3):
                    i, j = int(t[k]), int(t[(k + 1) % 3])
                    E.add((min(i, j), max(i, j)))
            self.E = np.array(sorted(E)) if E else np.zeros((0, 2), int)
            self.adj = [[] for _ in range(len(self.V))]
            for i, j in self.E:
                ln = float(np.linalg.norm(self.V[i] - self.V[j]))
                self.adj[i].append((j, ln)); self.adj[j].append((i, ln))
            self.lo, self.hi = self.V.min(0), self.V.max(0)

        def bvh(self):
            return BVHTree.FromPolygons([tuple(p) for p in self.V], [tuple(int(i) for i in t) for t in self.T],
                                        all_triangles=True)

    PARITY_DIR = Vector((0.0, 0.28, 0.96)).normalized()     # in the YZ plane: mirror-symmetric

    def inside_parity(tree, p, L):
        """Point inside a closed shell: odd number of hits along a fixed ray."""
        o = Vector(p)
        n = 0
        for _ in range(64):
            hit = tree.ray_cast(o, PARITY_DIR, 3 * L)
            if hit[0] is None:
                break
            n += 1
            o = hit[0] + PARITY_DIR * (1e-6 * L)
        return n % 2 == 1

    def geodesic(sh, roots):
        d = np.full(len(sh.V), np.inf)
        hq = []
        for r in roots:
            d[r] = 0.0
            hq.append((0.0, int(r)))
        heapq.heapify(hq)
        while hq:
            dv, v = heapq.heappop(hq)
            if dv > d[v]:
                continue
            for u, ln in sh.adj[v]:
                nd = dv + ln
                if nd < d[u]:
                    d[u] = nd
                    heapq.heappush(hq, (nd, u))
        d[~np.isfinite(d)] = 0.0
        return d

    def branches(sh, d, thr):
        """0-dim persistence of the superlevel sets of d (vertices in decreasing d, union-find).
        Each component carries its highest tip and an 'open' flag. When components meet at a vertex,
        a younger one whose tip persists >= thr above the meeting level is a real branch: it and the
        elder end there (a toe fork). A younger one below thr is corner noise and is absorbed. A
        component reaching the root (d = 0) ends there. Returns [(tip, d_tip, d_base, members)]."""
        order = np.argsort(-d, kind='stable')
        parent = {}
        comp = {}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        out = []

        def end(r, dv):
            c = comp[r]
            if c['open']:
                out.append((c['tip'], c['dt'], dv, list(c['members'])))
                c['open'] = False
        for v in order:
            v = int(v)
            parent[v] = v
            rs = sorted({find(u) for u, _ in sh.adj[v] if u in parent and u != v}, key=lambda r: -comp[r]['dt'])
            dv = float(d[v])
            at_root = dv <= 1e-12
            if not rs:
                comp[v] = dict(tip=v, dt=dv, open=not at_root, members=[v])
                continue
            elder = rs[0]
            sig = [r for r in rs[1:] if comp[r]['dt'] - dv >= thr]
            if sig:
                for r in [elder] + sig:
                    end(r, dv)
            if at_root:
                end(elder, dv)
            big = elder
            for r in rs[1:]:
                if len(comp[r]['members']) > len(comp[big]['members']):
                    comp[r]['members'] += comp[big]['members']
                    comp[r].update(tip=comp[big]['tip'], dt=comp[big]['dt'], open=comp[big]['open'])
                    parent[big] = r
                    del comp[big]
                    big = r
                else:
                    comp[big]['members'] += comp[r]['members']
                    parent[r] = big
                    del comp[r]
            parent[v] = big
            comp[big]['members'].append(v)
        dmin = float(d.min())
        for r, c in comp.items():
            if c['open']:
                out.append((c['tip'], c['dt'], dmin, list(c['members'])))
        return out

    def _section(sh, tris, c, ax, rmax):
        """Plane cut of the given triangles through c with normal ax: (min caliper width, mean caliper
        width = perimeter / pi) of the section's convex hull, points within rmax of c only."""
        V = sh.V[sh.T[tris]]                          # (m, 3, 3)
        sd = (V - c) @ ax                             # (m, 3)
        pts = []
        for k in range(3):
            a_, b_ = V[:, k], V[:, (k + 1) % 3]
            sa, sb = sd[:, k], sd[:, (k + 1) % 3]
            x = (sa * sb) < 0
            if x.any():
                f = (sa[x] / (sa[x] - sb[x]))[:, None]
                pts.append(a_[x] + (b_[x] - a_[x]) * f)
        if not pts:
            return None
        P = np.concatenate(pts)
        P = P[np.linalg.norm(P - c, axis=1) < rmax]
        if len(P) < 3:
            return None
        u = np.cross(ax, [0, 0, 1.0])
        if np.linalg.norm(u) < 1e-6:
            u = np.cross(ax, [1.0, 0, 0])
        u /= np.linalg.norm(u)
        v = np.cross(ax, u)
        Hh = _hull2(np.stack([(P - c) @ u, (P - c) @ v], 1))
        if len(Hh) < 3:
            return 0.0, 0.0
        Hh = np.array(Hh)
        n = len(Hh)
        per = float(sum(np.linalg.norm(Hh[(i + 1) % n] - Hh[i]) for i in range(n)))
        mw = 1e9
        for i in range(n):
            e = Hh[(i + 1) % n] - Hh[i]
            ln = np.linalg.norm(e)
            if ln < 1e-12:
                continue
            nr_ = np.array([-e[1], e[0]]) / ln
            q = (Hh - Hh[i]) @ nr_
            mw = min(mw, float(q.max() - q.min()))
        return mw, per / math.pi

    def measure_branch(sh, d, b, inside, window, nr):
        """Stations along the branch's visible length: level-set ring centroids give the axis polyline;
        each section is the plane cut of the branch's own triangles perpendicular to that axis."""
        tip, dt, db, mem = b
        mem = np.array(mem)
        inM = np.zeros(len(sh.V), bool)
        inM[mem] = True
        # the base level's own vertices (ties at d_base, e.g. the whole root cap) belong to the branch
        lvl = d <= db + 1e-9
        for i_, j_ in sh.E:
            if inM[i_] and lvl[j_]:
                inM[j_] = True
            elif inM[j_] and lvl[i_]:
                inM[i_] = True
        mem = np.where(inM)[0]
        din = d[mem][inside[mem]]
        d0 = max(db, float(din.max())) if len(din) else db
        if d0 >= dt:
            d0 = db
        Lv = dt - d0
        EI, EJ = sh.E[:, 0], sh.E[:, 1]
        hiI = d[EI] >= d[EJ]
        A = np.where(hiI, EI, EJ)
        B = np.where(hiI, EJ, EI)
        st = []
        for k in range(nr):
            s_ = (k + 0.5) / nr
            t = d0 + s_ * Lv
            sel = inM[A] & (d[A] >= t) & (d[B] < t)
            if sel.sum() < 2:
                continue
            a, bb = A[sel], B[sel]
            f = ((t - d[bb]) / np.maximum(d[a] - d[bb], 1e-12))[:, None]
            P = sh.V[bb] + (sh.V[a] - sh.V[bb]) * f
            st.append((s_, P.mean(0), float(np.linalg.norm(P - P.mean(0), axis=1).max())))
        mtris = np.where(inM[sh.T].sum(1) >= 2)[0]
        rings = []
        C = np.array([x[1] for x in st]) if st else np.zeros((0, 3))
        span = (C[-1] - C[0]) if len(C) > 1 else (sh.V[tip] - sh.V[mem].mean(0))
        rmed = float(np.median([x[2] for x in st])) if st else 0.0
        for k, (s_, c, rr) in enumerate(st):
            W_ = C[max(0, k - 2):k + 3]                # the axis: PCA of the nearby section centroids
            if len(W_) >= 2:
                Q = W_ - W_.mean(0)
                ax = np.linalg.eigh(Q.T @ Q)[1][:, -1]
                if ax @ span < 0:
                    ax = -ax
            else:
                ax = span.copy()
            if np.linalg.norm(ax) < 1e-9:
                continue
            ax = ax / np.linalg.norm(ax)
            r = _section(sh, mtris, c, ax, 2.5 * max(rr, rmed) + 1e-6)
            if r:
                rings.append((s_, r[0], r[1]))
        win = [r for r in rings if r[0] <= window] or rings
        if win:
            mins = np.array([r[1] for r in win])
            means = np.array([r[2] for r in win])
            thick = float(np.percentile(mins, 10))
            meanw = float(np.median(means))
        else:
            thick = meanw = 0.0
        return dict(tip=sh.V[tip], length=float(Lv), thick=thick, meanw=meanw,
                    rings=[(round(r[0], 2), round(1000 * r[1], 1), round(1000 * r[2], 1)) for r in rings],
                    centre=sh.V[mem].mean(0), members=mem)

    def run_gate(glb, outdir, tag='probe', tier=None, render=True, res=480):
        import junctions as JN
        RG = JN._render_glb()
        meshes, frame = RG['load'](glb)
        m = JN.Model(meshes)
        allV = np.concatenate([g.V for g in m.geo.values()])
        lo, hi = allV.min(0), allV.max(0)
        size = hi - lo
        H, S = float(size[2]), float(size.max())
        gb = m.geo[m.body.name]
        a, b_, c_ = gb.V[gb.T[:, 0]], gb.V[gb.T[:, 1]], gb.V[gb.T[:, 2]]
        vol = abs(float(np.einsum('ij,ij->i', a, np.cross(b_, c_)).sum()) / 6)
        msize = vol ** (1 / 3)
        auto = 1 if msize < L_['TIER_SIZE'][0] else 3 if msize > L_['TIER_SIZE'][1] else 2
        tier_src = 'override' if tier else 'auto'
        tier = tier or auto
        F = max(L_['THICK_H'] * L_['TIER_MUL'][tier] * H, L_['PX_MIN'] * H / L_['GAME_PX'])
        px = lambda x: round(x / H * L_['GAME_PX'], 1)          # pixels at a 256 px creature height
        eps_in = L_['INSIDE_EPS'] * S
        # every shell of every object, with its BVH (the 'other geometry' a piece is buried in)
        shells = []
        for o in [m.body] + m.pieces:
            g = m.geo[o.name]
            for tris in g.shells():
                sh = Shell(g, tris)
                shells.append((o, g, sh))
        trees = [(o.name, i, sh.lo - eps_in * 4, sh.hi + eps_in * 4, sh.bvh()) for i, (o, g, sh) in enumerate(shells)]
        diag = [float(np.linalg.norm(sh.hi - sh.lo)) for o, g, sh in shells]
        items = []
        for si, (o, g, sh) in enumerate(shells):
            is_body = o is m.body
            if is_body:
                kind, cls = 'body', 'body'
            else:
                kind, cls = piece_kind(o.name)
            if cls == 'eye':
                items.append(dict(obj=o.name, kind='eye', cls='eye', shell=si, gated=False, ok=True, fail=[]))
                continue
            # buried / touching vertices
            inside = np.zeros(len(sh.V), bool)          # buried in another OBJECT (body or piece)
            inside_same = np.zeros(len(sh.V), bool)     # buried in another shell of the same object
            near = np.full(len(sh.V), np.inf)
            sub = False
            if not is_body:
                for (on, ti, tlo, thi, tr) in trees:
                    if ti == si:
                        continue
                    box = np.all((sh.V >= tlo) & (sh.V <= thi), 1)
                    for vi in np.where(box)[0]:
                        loc, nrm, _, dist = tr.find_nearest(Vector(sh.V[vi]))
                        if loc is None:
                            continue
                        if on != o.name:
                            near[vi] = min(near[vi], dist)
                        if dist < eps_in or inside_parity(tr, sh.V[vi], S):
                            if on != o.name:
                                inside[vi] = True
                            elif diag[ti] > diag[si]:        # buried in a BIGGER shell of its own piece
                                inside_same[vi] = True
                if (inside | inside_same).mean() > 0.9:  # a shell hidden inside another: nothing shows
                    continue
                roots = np.where(inside)[0]
                if not len(roots) and inside_same.any():
                    roots = np.where(inside_same)[0]      # a sub-part (a toe bulb in its toe): not its own detail
                    sub = True
                    inside = inside_same
                if not len(roots) and np.isfinite(near).any() and near.min() < 0.02 * S:
                    roots = [int(np.argmin(near))]        # seated a hair off the body: root at the contact
                if not len(roots):
                    roots = [int(np.argmin(near))] if np.isfinite(near).any() else [0]
                if sub:
                    kind, cls = 'knob', 'knob'
            else:
                dom = m.dom[o.name]
                trunk = np.array([bool(dom[int(gv)] and dom[int(gv)] in m.bones and m.trunk(dom[int(gv)]))
                                  for gv in sh.gid]) if m.bones else np.zeros(len(sh.V), bool)
                if not trunk.any():
                    cen = sh.V.mean(0)
                    trunk = np.linalg.norm(sh.V - cen, axis=1) < 0.25 * S
                roots = np.where(trunk)[0]
            d = geodesic(sh, roots)
            thr = max(L_['PERSIST'][0] * S, L_['PERSIST'][1] * float(d.max()))
            brs = branches(sh, d, thr)
            single = len(brs) <= 1
            for br in brs:
                # kind: piece name, or the body bone at the branch tip
                bk, bc = kind, cls
                bone = None
                if is_body:
                    bone = m.dom[o.name][int(sh.gid[br[0]])]
                    if not bone or bone not in m.bones or m.trunk(bone):
                        continue
                    bk, bc = 'limb', 'limb'
                    for k_, c2, rx in BONE_KINDS:
                        if rx.search(bone):
                            bk, bc = k_, c2
                            break
                win = L_['WINDOW']['pointed' if bc in ('pointed', 'claw') else 'blunt']
                r = measure_branch(sh, d, br, inside, win, L_['RINGS'])
                if r['length'] <= 0:
                    continue
                blob = r['length'] < L_['BLOB'] * max(r['meanw'], 1e-9)
                if not (single and not is_body) and r['length'] < L_['BUMP'] * max(r['meanw'], 1e-9):
                    continue                    # a bump on a palm / a corner of a cap
                if is_body and r['length'] < L_['DIGIT_LEN_H'] * H:
                    continue
                it = dict(obj=o.name, kind=bk, cls=bc, shell=si, bone=bone, side='L' if r['tip'][0] > 1e-4 else
                          'R' if r['tip'][0] < -1e-4 else 'C', tip=[round(float(x), 3) for x in r['tip']],
                          centre=[round(float(x), 3) for x in r['centre']],
                          length_mm=round(1000 * r['length'], 1), thick_mm=round(1000 * r['thick'], 1),
                          meanw_mm=round(1000 * r['meanw'], 1), thick_px=px(r['thick']), meanw_px=px(r['meanw']),
                          length_H=round(r['length'] / H, 3), thick_H=round(r['thick'] / H, 4),
                          aspect=round(r['length'] / max(r['thick'], 1e-9), 1), blob=bool(blob),
                          rings=r['rings'], _members=r['members'], _sh=si)
                f = []
                if bc in GATED:
                    if bc == 'plate':
                        if r['meanw'] < F:
                            f.append(f"mean width {it['meanw_mm']} mm ({it['meanw_px']} px) < {1000 * F:.1f} mm")
                    elif r['thick'] < F and not (blob and r['meanw'] >= 1.5 * F):
                        f.append(f"thickness {it['thick_mm']} mm ({it['thick_px']} px) < {1000 * F:.1f} mm")
                    if bc == 'digit' and not blob:
                        if r['length'] < L_['DIGIT_LEN_H'] * H:
                            f.append(f"length {it['length_mm']} mm = {it['length_H']} H < {L_['DIGIT_LEN_H']} H")
                        if it['aspect'] > L_['DIGIT_ASPECT'][tier]:
                            f.append(f"stick: length/thickness {it['aspect']} > {L_['DIGIT_ASPECT'][tier]}")
                it['gated'] = bc in GATED
                it['fail'] = f
                it['ok'] = not f
                it['margin'] = round((r['meanw'] if bc == 'plate' else r['thick']) / F, 2)
                items.append(it)
        # ---- feature groups
        groups = {}
        for it in items:
            if it['obj'] == m.body.name:
                key = f"body:{it['kind']}"
                if it['kind'] == 'limb':
                    key = 'body:limb tips'
            else:
                key = stem(it['obj'])
            groups.setdefault(key, []).append(it)
        feats = []
        for key, its in groups.items():
            g_ = [i for i in its if i.get('gated')]
            npass = sum(1 for i in g_ if i['ok'])
            readable = (not g_) or npass >= 0.5 * len(g_)
            counted = key != 'body:limb tips'
            feats.append(dict(group=key, items=len(its), gated=len(g_), passed=npass, readable=readable,
                              counted=counted))
        # body paint regions beyond the base colour
        me = m.body.data
        areas = {}
        for t, p in enumerate(gb.poly):
            mi = me.polygons[int(p)].material_index
            areas[mi] = areas.get(mi, 0.0) + float(gb.A[t])
        tot = sum(areas.values()) or 1.0
        regions = sorted(((a / tot, mi) for mi, a in areas.items()), reverse=True)
        for share, mi in regions[1:]:
            if share >= 0.02:
                nm = me.materials[mi].name if mi < len(me.materials) and me.materials[mi] else f'mat{mi}'
                feats.append(dict(group=f'paint:{nm}', items=1, gated=0, passed=0, readable=True, counted=True,
                                  share=round(share, 3)))
        n_read = sum(1 for f_ in feats if f_['readable'] and f_['counted'])
        lo_c, hi_c = L_['COUNT'][tier]
        count_ok = n_read >= lo_c
        count_warn = n_read > hi_c
        # tier-1 digit count per hand/foot (warn)
        warns = []
        if tier == 1:                         # digits per hand/foot: tips clustered within 0.12 S
            per = {}
            for it in items:
                if it['cls'] == 'digit' and not it['blob']:
                    per.setdefault((stem(it['obj']), it['side']), []).append(it)
            for (st, sd), its in per.items():
                P = np.array([i['tip'] for i in its])
                lab = list(range(len(its)))
                for x in range(len(its)):
                    for y in range(x):
                        if np.linalg.norm(P[x] - P[y]) < 0.12 * S:
                            a_, b2 = lab[x], lab[y]
                            lab = [b2 if q == a_ else q for q in lab]
                for cl in set(lab):
                    n_ = lab.count(cl)
                    if n_ > L_['DIGITS_PER_GROUP_T1']:
                        warns.append(f"{st} {sd}: {n_} digits on one hand/foot (tier 1: <= {L_['DIGITS_PER_GROUP_T1']} fat digits)")
        gated = [i for i in items if i.get('gated')]
        ok = all(i['ok'] for i in gated) and count_ok
        rep = dict(glb=glb, tag=tag, ok=ok, tier=tier, tier_source=tier_src, tier_auto=auto, mass_size_m=round(msize, 3),
                   body_volume_m3=round(vol, 4), H_m=round(H, 3), S_m=round(S, 3), size_m=[round(float(x), 3) for x in size],
                   floor_mm=round(1000 * F, 2), floor_px=px(F), limits={k: (v if not isinstance(v, dict) else
                                                                           {str(a): b for a, b in v.items()}) for k, v in LIMITS.items()},
                   count=dict(readable=n_read, min=lo_c, max=hi_c, ok=count_ok, warn=count_warn),
                   features=feats, warns=warns,
                   items=[{k: v for k, v in i.items() if not k.startswith('_')} for i in items])
        os.makedirs(outdir, exist_ok=True)
        if render:
            rep['renders'] = render_all(m, items, shells, frame, outdir, tag, RG, res, F)
        with open(os.path.join(outdir, f'{tag}_details.json'), 'w', encoding='utf-8') as f:
            json.dump(rep, f, indent=1, default=lambda o: o.tolist() if hasattr(o, 'tolist') else str(o))
        _report(rep)
        return rep

    def _report(rep):
        say(f"detail tier {rep['tier']} ({rep['tier_source']}; auto {rep['tier_auto']} from mass size "
            f"{rep['mass_size_m']} m), H {rep['H_m']} m, S {rep['S_m']} m, floor {rep['floor_mm']} mm = {rep['floor_px']} px")
        for i in sorted(rep['items'], key=lambda i: (i['ok'], i.get('margin', 9))):
            if not i.get('gated'):
                continue
            say(('PASS' if i['ok'] else 'FAIL') + f" detail {i['obj']}/{i['kind']} {i['side']} tip {i['tip']}: "
                f"len {i['length_mm']} mm ({i['length_H']} H), thick p10 {i['thick_mm']} mm ({i['thick_px']} px), "
                f"mean w {i['meanw_mm']} mm, aspect {i['aspect']}{' blob' if i['blob'] else ''}"
                + ('' if i['ok'] else '  <<  ' + '; '.join(i['fail'])))
        c = rep['count']
        say(('PASS' if c['ok'] else 'FAIL') + f" detail count: {c['readable']} readable feature groups "
            f"(tier {rep['tier']}: {c['min']}-{c['max']})" + (' WARN over max' if c['warn'] else '') + ': '
            + ', '.join(f['group'] + ('' if f['readable'] else ' (unreadable)') for f in rep['features'] if f['counted']))
        for w in rep['warns']:
            say('WARN detail', w)
        say('detail gate', 'PASS' if rep['ok'] else 'FAIL')

    # ------------------------------------------------------------------ renders
    DCOL = {'pass': (0.20, 0.75, 0.30), 'fail': (0.92, 0.12, 0.12), 'info': (0.35, 0.60, 0.95), 'none': (0.80, 0.80, 0.78)}

    def render_all(m, items, shells, frame, outdir, tag, RG, res, F):
        import bmkit as K
        files = {}
        RG['beauty_setup'](frame)
        sc = bpy.context.scene
        try:
            sc.eevee.taa_render_samples = 16
        except AttributeError:
            pass
        ground = bpy.data.objects.get('_ground')
        # game distance: orthographic, the creature fitted into GAME_RES px
        gv = []
        for az in range(0, 360, 45):
            t = math.radians(az)
            gv.append((f'g{az:03d}', (math.sin(t), -math.cos(t), 0.0)))
        for az in (45, 135, 225, 315):
            t, e = math.radians(az), math.radians(35)
            gv.append((f'g{az:03d}h', (math.sin(t) * math.cos(e), -math.cos(t) * math.cos(e), math.sin(e))))
        Ls = max(frame['size'])
        for name, dvec in gv:
            K.view('_dg', dvec)
            fr = dict(frame, ortho=Ls * 1.08)
            K.camera(fr, '_dg', ortho=True)
            if ground:
                ground.hide_render = False
            p = os.path.join(outdir, f'{tag}_game_{name}.png')
            K._render(p, L_['GAME_RES'])
            files.setdefault('game', []).append(p)
        sc.camera.data.type = 'PERSP'
        # worst failing details: zoomed beauty crops
        fails = sorted([i for i in items if i.get('gated') and not i['ok']], key=lambda i: i['margin'])
        cen = np.array(frame['centre'])
        for k, it in enumerate(fails[:4]):
            c = np.array(it['centre'])
            rad = max(0.75 * it['length_mm'] / 1000, 5 * it['thick_mm'] / 1000, 0.04 * Ls)
            out = c - cen
            out[2] = 0
            out = out / (np.linalg.norm(out) + 1e-9) + np.array([0, 0, 0.6])
            dist = rad / math.tan(K.FOV / 2)
            K.view('_dc', tuple(out))
            K.camera(dict(centre=list(c), size=[dist / K.DIST] * 3), '_dc')
            if ground:
                ground.hide_render = sc.camera.location.z < frame['floor'] + 0.01
            p = os.path.join(outdir, f'{tag}_dcrop_{k}.png')
            K._render(p, res)
            files.setdefault('crops', []).append((p, f"{it['obj']}/{it['kind']} {it['side']}: {'; '.join(it['fail'])}"))
        # flag views: green pass, red fail, blue counted-not-gated
        K._workbench('tech')
        fl = {}
        for it in items:
            if it['kind'] == 'eye' or '_members' not in it:
                cls = 'info'
                o, g, sh = shells[it['shell']]
                mem = set(range(len(sh.V)))
            else:
                cls = 'info' if not it.get('gated') else 'pass' if it['ok'] else 'fail'
                o, g, sh = shells[it['_sh']]
                mem = set(int(x) for x in it['_members'])
            for lt, gt in enumerate(sh.tris):
                if all(int(x) in mem for x in sh.T[lt]):
                    key = (o.name, int(g.poly[gt]))
                    cur = fl.get(key)
                    if cur is None or ['fail', 'pass', 'info'].index(cls) < ['fail', 'pass', 'info'].index(cur):
                        fl[key] = cls
        for o in [m.body] + m.pieces:
            me = o.data
            at = me.color_attributes.get('_dq') or me.color_attributes.new('_dq', 'BYTE_COLOR', 'CORNER')
            cols = []
            for p in me.polygons:
                c = DCOL[fl.get((o.name, p.index), 'none')]
                cols += [c[0], c[1], c[2], 1.0] * p.loop_total
            at.data.foreach_set('color', cols)
            me.color_attributes.active_color = at
        if ground:
            ground.hide_render = True
        for v in ('hero', 'az090', 'front34r', 'back34'):
            K.camera(frame, v, fill=1.1)
            p = os.path.join(outdir, f'{tag}_dflag_{v}.png')
            K._render(p, res)
            files.setdefault('flags', []).append(p)
        return files


# ============================================================================== plain-Python side
def compose(rep, outdir, tag, title):
    import run as R
    from PIL import Image, ImageDraw
    W = 2304
    ims = []
    t = Image.new('RGB', (W, 92), (255, 255, 255))
    d = ImageDraw.Draw(t)
    c = rep['count']
    d.text((8, 6), f"{title}: detail gate {'PASS' if rep['ok'] else 'FAIL'}  ({tag})   tier {rep['tier']} "
                   f"({rep['tier_source']}, auto {rep['tier_auto']}; mass size {rep['mass_size_m']} m)   H {rep['H_m']} m",
           fill=(0, 110, 0) if rep['ok'] else (190, 0, 0), font=R.font(26))
    d.text((8, 40), f"floor {rep['floor_mm']} mm = {rep['floor_px']} px of a {LIMITS['GAME_PX']} px frame; "
                    f"readable feature groups {c['readable']} (tier {rep['tier']}: {c['min']}-{c['max']})"
                    + (' WARN over max' if c['warn'] else '') + '   green pass / red fail / blue counted', fill=(0, 0, 0),
           font=R.font(17))
    d.text((8, 64), ('features: ' + ', '.join(f['group'] for f in rep['features'] if f['counted'] and f['readable']))[:260],
           fill=(60, 60, 60), font=R.font(15))
    ims.append(t)
    rows = sorted([i for i in rep['items'] if i.get('gated')], key=lambda i: (i['ok'], i['margin']))
    lines = [f"{'PASS' if i['ok'] else 'FAIL'} {i['obj'][:22]}/{i['kind']} {i['side']}: len {i['length_mm']} mm "
             f"({i['length_H']} H), thick {i['thick_mm']} mm ({i['thick_px']} px), aspect {i['aspect']}"
             + ('' if i['ok'] else ' << ' + '; '.join(i['fail'])) for i in rows[:16]]
    if len(rows) > 16:
        lines.append(f'... {len(rows) - 16} more gated items ({sum(1 for i in rows[16:] if not i["ok"])} FAIL)')
    lines += ['WARN ' + w for w in rep.get('warns', [])]
    tb = Image.new('RGB', (W, 12 + 21 * len(lines)), (255, 255, 255))
    d = ImageDraw.Draw(tb)
    for k, l in enumerate(lines):
        d.text((8, 6 + 21 * k), l[:230], fill=(0, 110, 0) if l.startswith('PASS') else (190, 0, 0), font=R.font(16))
    ims.append(tb)
    rr = rep.get('renders', {})
    g = rr.get('game', [])
    if g:
        hdr = Image.new('RGB', (W, 26), (255, 255, 255))
        ImageDraw.Draw(hdr).text((8, 4), f"GAME DISTANCE: {LIMITS['GAME_RES']} px thumbnails, native size (8 level azimuths, "
                                         f"4 at +35 deg); below: six of them at 2x nearest", fill=(0, 0, 0), font=R.font(16))
        ims.append(hdr)
        row = Image.new('RGB', (W, LIMITS['GAME_RES']), (255, 255, 255))
        for k, p in enumerate(g[:12]):
            if os.path.exists(p):
                row.paste(Image.open(p).convert('RGB'), (k * LIMITS['GAME_RES'], 0))
        ims.append(row)
        row2 = Image.new('RGB', (W, 2 * LIMITS['GAME_RES']), (255, 255, 255))
        for k, p in enumerate([g[i] for i in (0, 1, 2, 4, 9, 11) if i < len(g)]):
            if os.path.exists(p):
                im = Image.open(p).convert('RGB')
                row2.paste(im.resize((2 * im.width, 2 * im.height), Image.NEAREST), (k * 2 * LIMITS['GAME_RES'], 0))
        ims.append(row2)
    tile = W // 4 - 6
    for key, lab in (('flags', 'detail flags'), ('crops', 'worst details')):
        fs = rr.get(key, [])
        if not fs:
            continue
        row = Image.new('RGB', (W, tile + 30), (255, 255, 255))
        d = ImageDraw.Draw(row)
        for k, p in enumerate(fs[:4]):
            cap = lab
            if isinstance(p, (list, tuple)):
                p, cap = p
            if os.path.exists(p):
                row.paste(Image.open(p).convert('RGB').resize((tile, tile)), (k * (tile + 6), 28))
            d.text((k * (tile + 6) + 4, 4), cap[:70], fill=(0, 0, 0), font=R.font(15))
        ims.append(row)
    path = os.path.join(outdir, f'{tag}_detail_sheet.jpg')
    R.vstack(ims, path)
    return path


def gate(glb, outdir, scr, tag='probe', title='', render=True, tier=None, prog=None):
    """Run the gate in headless Blender; returns (ok, BMK lines, report dict or None, sheet path or None)."""
    import run as R
    os.makedirs(outdir, exist_ok=True)
    prog = prog or find_prog(glb)
    tier = tier or tier_from_prog(prog)
    args = [glb, outdir, '--tag', tag] + ([] if render else ['--no-render']) + (['--tier', str(tier)] if tier else [])
    rc, lines, tb = R.blender(os.path.abspath(__file__), args, os.path.join(scr, f'details_{tag}.log'))
    jp = os.path.join(outdir, f'{tag}_details.json')
    if tb or not os.path.exists(jp):
        return False, lines + tb, None, None
    rep = json.load(open(jp, encoding='utf-8'))
    sheet = compose(rep, outdir, tag, title or os.path.splitext(os.path.basename(glb))[0]) if render else None
    return bool(rep['ok']), lines, rep, sheet


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__); return 2
    glb, out = os.path.abspath(a[0]), os.path.abspath(a[1])
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    tier = int(opt('--tier')) if opt('--tier') else None
    ok, lines, rep, sheet = gate(glb, out, out, opt('--tag', 'probe'), opt('--title', ''), render='--no-render' not in a,
                                 tier=tier, prog=opt('--prog'))
    for l in lines:
        print(l)
    if sheet:
        print('BMK detail sheet:', sheet)
    return 0 if ok else 1


def _blender_main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if len(argv) < 2:
        print(__doc__); sys.exit(2)
    glb, outdir = os.path.abspath(argv[0]), os.path.abspath(argv[1])
    tag = argv[argv.index('--tag') + 1] if '--tag' in argv else 'probe'
    tier = int(argv[argv.index('--tier') + 1]) if '--tier' in argv else None
    run_gate(glb, outdir, tag, tier=tier, render='--no-render' not in argv)


if __name__ == '__main__':
    if HAS_BPY:
        _blender_main()
    else:
        sys.exit(main())
