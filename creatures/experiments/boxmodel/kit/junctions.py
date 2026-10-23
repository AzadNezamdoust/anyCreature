"""junctions.py — the junction probe, the eye check and the membrane check, measured on a GLB.

Why it exists: every zoo creature passed the structural and tech-QA gates and the owner still
found the #1 visible flaw at the joins: narrow creased seam strips at the shoulder (ogre), knife
folds, slits, holes and white specks at arm/leg/ear/tail/wing roots, paper-thin wing membranes,
a tail clipping the hind legs in the trot (fox). None of that was measured where it shows: at
the root of each limb. This module finds every root from the rig and measures it.

Run it (one headless Blender; junction_gate.py wraps it and composes the crop sheet):

    blender -b --factory-startup -P junctions.py -- <glb> <outdir> [--tag s4_r01] [--no-render]
                                                           [--no-posed] [--res 480]

It writes <outdir>/<tag>_junctions.json, the zoomed crops <outdir>/<tag>_j<i>_<view>.png and
prints one 'BMK PASS|FAIL junction ...' line per gate. Exit 0 unless the probe crashed: the verdict
is the json's 'ok' (junction_gate.py turns it into its exit code).

JUNCTIONS. A junction is the root of a bone chain that branches off the trunk (the central
bones that are not a tail: hips, spine, chest, neck, head, jaw): every limb, ear, horn, tail,
tentacle. A centre-line bone named like an appendage (fin_dorsal, crest, a centre horn) is a
junction, not trunk. A big piece named like a wing / fin / sail that sits on the body is a junction too
(its contact patch), one per side. r = the chain's radius at its root (median distance of
its body vertices to the bone axis over the first half of the first bone; a mirrored pair, e.g.
thigh.L / thigh.R, shares one r over both sides' samples). The probe region is every triangle whose
centre is within REGION_K * r of the root and (bone roots) no further down the first bone than
ROOT_REACH of its length, minus the faces of OTHER chains (an ear rim inside a shoulder's 2r). Folds and strips count only where a review
camera sees them: a face is exposed when it faces and is unoccluded from >= EXPOSED of the
17 review views (8 azimuths level and at +35 deg, and the top).

MEASURES (per junction, on the exported triangles welded by position):
  open      open (boundary) or non-manifold edges in the region: a hole, a slit, white specks
  knife     concave (valley) edges folded more than KNIFE_DEG: a knife fold / hard crease
  strip     a narrow seam strip: a connected band of thin triangles (width < STRIP_W of the
            region's median face width, longer than STRIP_ASPECT x their width) that lies
            on a crease (an edge folded > STRIP_CREASE_DEG); gated by its length / r
  slit      a face whose normal ray hits another, non-neighbouring face of the body within
            SLIT_K * r: two surfaces pressed into a dark slit (arm against chest)
  poke      the body crosses itself in the region at rest (a limb root through the torso)
  gap       a piece shell near the root that hovers off the body (no contact, gap < r)
  pinch     (warn) a vertex whose angle sum departs from 2 pi by more than PINCH_RAD
  shelf     (arm roots) the troll T-bar: the largest patch of faces outboard of the arm root that
            face up within SHELF_DEG of level and are seen from the top; FAIL when its area >
            SHELF_AREA_K r^2 and it is wider than SHELF_W_K r across the limb (a round arm top is a line)
  clip      (posed, GLB with clips) the chain's triangles crossing ANOTHER chain (tail
            through a hind leg, arm through the other arm) in any sampled frame that did
            not cross at rest, as % of the chain's area; crossings with the trunk are
            reported as root_clip (warn)
EYE CHECK: the lens shells of every piece named *eye*, one eye per side: visible fraction of
its camera-facing area from the front (az000), the 3/4 (az045 / az315) and the side (az090 /
az270) views, ray-tested against every other surface; lens diameter / head length within
EYE_SIZE (head length = the extent of the skull's body faces: the head bone and its centre-line
children, never the ears / horns / tufts on it); round (PCA extents ratio >= EYE_ROUND); seated (part
of it inside the head) and proud (part of it outside).
SEAT CHECK: pieces named strap/belt/band/collar/harness/...: the share of the inner face (facing the
skin, within SEAT_FAR x size) lifted more than SEAT_LIFT x size off it, <= SEAT_PCT. WARN only:
not calibrated yet (the owner-accepted ogre belt reads 40-60%).
MEMBRANE CHECK: pieces named wing/fin/membrane/web/sail/frill/cape/flap, and body regions of
chains named wing/fin/ear: per triangle the thickness along the inward normal; area-weighted p10
must reach MEMBRANE_MIN (max of an absolute floor and a share of the creature's size); an open
single-sided plate is thickness 0.
"""
import bpy, sys, os, json, math, re
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

KIT = os.path.dirname(os.path.abspath(__file__))
if KIT not in sys.path:
    sys.path.insert(0, KIT)

LIMITS = dict(
    REGION_K=2.0,
    EXPOSED=2,               # a face counts when seen (facing, unoccluded) from >= this many review views            # probe radius = REGION_K x the chain's root radius
    WELD=1e-5,               # export vertices closer than this are one vertex (flat-shaded GLBs split them)
    KNIFE_DEG=90.0,          # an exposed concave fold sharper than this is a knife fold (a hard seam, not a blend)
    KNIFE_LEN_K=1.0,         # gate: total exposed knife-fold length in the region <= KNIFE_LEN_K x r
    STRIP_W=0.40,            # a strip triangle is narrower than this share of the region's median width
    STRIP_ASPECT=3.0,        # ... and longer than this many times its width
    STRIP_CREASE_DEG=30.0,   # ... and has an edge folded more than this (concave or convex)
    STRIP_LEN_K=1.0,         # gate: no strip longer than STRIP_LEN_K x r
    SLIT_K=0.10,             # a face whose normal hits another surface within SLIT_K x r is in a slit
    SLIT_PCT=1.5,            # gate: slit faces <= this % of the region's area
    GAP_K=1.0,               # a piece shell hovering within GAP_K x r of the body near a root is a gap
    PINCH_RAD=2.2,           # warn: |2 pi - angle sum| above this at a vertex
    CLIP_PCT=1.0,            # gate: posed chain-vs-chain clipping <= this % of the chain's area
    EYE_VIS=dict(front=0.15, threeq=0.35, side=0.40),  # visible projected lens area / lens disc area, per view
    EYE_SIZE=(0.06, 0.24),   # lens diameter / head length
    EYE_ROUND=0.70,          # lens: second / first PCA extent
    SEAT_LIFT=0.004,         # a band's inner face further than this x size off the skin is lifted
    SEAT_FAR=0.05,           # ... and nearer than this (further: not a seat, e.g. a hanging flap)
    SEAT_PCT=10.0,           # warn (not gated yet): lifted share of a band's inner face
    MEMBRANE_ABS=0.006,      # m
    MEMBRANE_REL=0.004,      # x the creature's largest dimension
    SHELF_DEG=20.0,          # shoulder shelf: an exposed face this close to level (normal within SHELF_DEG of +z) ...
    SHELF_AREA_K=0.5,        # gate: the largest level patch outboard of an arm root, seen from the top, <= SHELF_AREA_K x r^2 (synthetic troll T-bar 0.93, troll 0.0, ogre 3.45)
    SHELF_W_K=0.8,           # ... counted only when it is also this wide across the limb (x r): a round arm top is a line
)
L_ = LIMITS
TRUNK_RE = re.compile(r'^(root|hips?|pelvis|spine\w*|chest\w*|torso\w*|body\w*|neck\w*|head\w*|jaw\w*|abdomen\w*|'
                      r'thorax\w*|ribcage\w*|belly\w*|skull\w*|cranium\w*)$', re.I)
TAILLIKE_RE = re.compile(r'tail|tentacle|antenna|trunk_?tip', re.I)
MEMBRANE_WORDS = {'wing', 'fin', 'membrane', 'web', 'sail', 'frill', 'cape', 'flap', 'ear', 'dorsal', 'pectoral', 'caudal', 'patagium'}
PIECE_JUNCTION_WORDS = {'wing', 'fin', 'sail', 'membrane', 'frill', 'dorsal', 'pectoral', 'patagium'}
# a bone on the centre line is trunk unless it is an appendage: a dorsal fin, a crest, a centre horn (kit bug
# 2026-10-23: the seahorse's fin_dorsal was trunk, so it was never probed nor membrane-checked)
APPENDAGE_WORDS = PIECE_JUNCTION_WORDS | {'caudal', 'crest', 'horn', 'antler', 'tusk', 'ear', 'lobe', 'tuft'}
# shoulder shelf check (top view): front-limb roots only (a hip's top is the haunch, a flat back is not a shelf)
ARM_WORDS = {'upperarm', 'arm', 'shoulder', 'clavicle', 'humerus', 'foreleg', 'scapula', 'flipper'}
SHELF_HANG = -0.5        # ... and only a hanging arm (bone axis z below this): a sprawling croc leg, a crab or scorpion
                         # pincer, an octopus arm or a koi fin is level along its top by design


def _words(name):
    """'piece_wingL' -> {'piece', 'wing'}; 'forearm.L' -> {'forearm'} (so 'forearm' is no ear, 'finger' no fin)."""
    w = re.split(r'[^A-Za-z]+|(?<=[a-z])(?=[A-Z])', name)
    return {x.lower().rstrip('s') if len(x) > 3 else x.lower() for x in w if len(x) > 1}


def has_word(name, words):
    return bool(_words(name) & words)
FLAG_COL = {'ok': (0.80, 0.80, 0.78), 'open': (0.10, 0.80, 0.95), 'knife': (0.92, 0.10, 0.10),
            'strip': (1.0, 0.85, 0.10), 'slit': (1.0, 0.50, 0.05), 'poke': (0.92, 0.10, 0.85),
            'gap': (0.15, 0.30, 1.0), 'clip': (1.0, 0.55, 0.70), 'thin': (0.0, 0.55, 0.55),
            'pinch': (0.55, 0.15, 0.85), 'shelf': (0.35, 0.80, 0.20), 'region': (0.93, 0.93, 0.90)}
FLAG_PRI = ['open', 'poke', 'gap', 'knife', 'strip', 'slit', 'shelf', 'clip', 'thin', 'pinch', 'region']


def say(*a):
    print('BMK', *a, flush=True)


# ------------------------------------------------------------------------------------------- geometry
class Geo:
    """One mesh object's exported triangles, welded by position (a flat-shaded GLB splits every
    vertex per face). V: (n, 3) welded world positions; T: (m, 3) welded triangle ids; poly: the
    original polygon of each triangle; rep: original vertex index of each welded vertex; wid:
    welded id of each original vertex."""

    def __init__(self, ob):
        self.ob = ob
        co, tv, tp = _eval(ob)
        key = np.round(co / L_['WELD']).astype(np.int64)
        _, rep, wid = np.unique(key, axis=0, return_index=True, return_inverse=True)
        self.rep, self.wid = rep, wid.reshape(-1)
        self.V = co[rep]
        T = self.wid[tv]
        ok = (T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])
        self.T, self.poly = T[ok], tp[ok]
        self.tri_ok = ok
        self._derive()

    def _derive(self):
        V, T = self.V, self.T
        a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
        n = np.cross(b - a, c - a)
        ln = np.linalg.norm(n, axis=1)
        self.A = ln / 2
        self.N = n / np.maximum(ln, 1e-15)[:, None]
        self.C = (a + b + c) / 3
        e = np.stack([np.linalg.norm(b - a, axis=1), np.linalg.norm(c - b, axis=1), np.linalg.norm(a - c, axis=1)], 1)
        self.longest = e.max(1)
        self.width = 2 * self.A / np.maximum(self.longest, 1e-15)

    def posed(self):
        """Welded positions of the current (posed) evaluation."""
        co, _, _ = _eval(self.ob)
        return co[self.rep]

    def bvh(self, V=None):
        V = self.V if V is None else V
        return BVHTree.FromPolygons([tuple(p) for p in V], [tuple(int(i) for i in t) for t in self.T], all_triangles=True)

    def edges(self):
        """{(i, j): [tri, ...]} over the welded triangles."""
        if not hasattr(self, '_E'):
            E = {}
            for ti, t in enumerate(self.T):
                for k in range(3):
                    i, j = int(t[k]), int(t[(k + 1) % 3])
                    E.setdefault((min(i, j), max(i, j)), []).append(ti)
            self._E = E
        return self._E

    def vtris(self):
        if not hasattr(self, '_VT'):
            VT = [[] for _ in range(len(self.V))]
            for ti, t in enumerate(self.T):
                for v in t:
                    VT[int(v)].append(ti)
            self._VT = VT
        return self._VT

    def near_ring(self, tris, rings=2):
        """For each triangle in tris: the set of triangles within `rings` vertex rings of it."""
        VT = self.vtris()
        out = {}
        for ti in tris:
            s = {ti}
            for _ in range(rings):
                s = set().union(*(VT[int(v)] for x in s for v in self.T[x]))
            out[ti] = s
        return out

    def shells(self):
        """Connected components of triangles (by shared welded vertex): list of tri index arrays."""
        parent = list(range(len(self.V)))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        for t in self.T:
            r0 = find(int(t[0]))
            for v in t[1:]:
                r = find(int(v))
                if r != r0:
                    parent[r] = r0
        groups = {}
        for ti, t in enumerate(self.T):
            groups.setdefault(find(int(t[0])), []).append(ti)
        return [np.array(g) for g in groups.values()]


def _eval(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    oe = ob.evaluated_get(dg)
    me = oe.to_mesh()
    me.calc_loop_triangles()
    n = len(me.vertices)
    co = np.empty(n * 3)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    M = np.array(ob.matrix_world)
    co = co @ M[:3, :3].T + M[:3, 3]
    m = len(me.loop_triangles)
    tv = np.empty(m * 3, dtype=np.int64)
    me.loop_triangles.foreach_get('vertices', tv)
    tp = np.empty(m, dtype=np.int64)
    me.loop_triangles.foreach_get('polygon_index', tp)
    oe.to_mesh_clear()
    return co, tv.reshape(-1, 3), tp


def _dominant_bone(ob):
    """Name of the vertex group with the largest weight, per original vertex (None if unweighted)."""
    names = [g.name for g in ob.vertex_groups]
    out = []
    for v in ob.data.vertices:
        best, bw = None, 0.0
        for g in v.groups:
            if g.weight > bw and g.group < len(names):
                best, bw = names[g.group], g.weight
        out.append(best)
    return out


# --------------------------------------------------------------------------------------------- model
class Model:
    def __init__(self, meshes):
        self.rig = next((o for o in bpy.context.scene.objects if o.type == 'ARMATURE'), None)
        self.body = next((o for o in meshes if o.name.lower().startswith('body')), None)
        if self.body is None:
            self.body = max(meshes, key=lambda o: len(o.data.polygons))
        self.pieces = [o for o in meshes if o is not self.body]
        self.geo = {o.name: Geo(o) for o in meshes}
        allV = np.concatenate([g.V for g in self.geo.values()])
        self.lo, self.hi = allV.min(0), allV.max(0)
        self.L = float((self.hi - self.lo).max())
        self.bones = {}
        if self.rig:
            M = self.rig.matrix_world
            for b in self.rig.data.bones:
                self.bones[b.name] = dict(head=np.array(M @ b.head_local), tail=np.array(M @ b.tail_local),
                                          parent=b.parent.name if b.parent else None,
                                          children=[c.name for c in b.children])
        self.dom = {}
        for o in meshes:
            d = _dominant_bone(o)
            g = self.geo[o.name]
            self.dom[o.name] = [d[i] for i in g.rep]          # per welded vertex

    def trunk(self, name):
        b = self.bones[name]
        central = abs(b['head'][0]) < 0.01 * self.L and abs(b['tail'][0]) < 0.01 * self.L
        return central and not TAILLIKE_RE.search(name) and not has_word(name, APPENDAGE_WORDS)

    def subtree(self, name):
        out, todo = set(), [name]
        while todo:
            n = todo.pop()
            out.add(n)
            todo += self.bones[n]['children']
        return out


def _seg_dist(P, a, b):
    ab = b - a
    t = np.clip(((P - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1), t


def find_junctions(m):
    J = []
    for name, b in m.bones.items():
        p = b['parent']
        if p is None or not m.trunk(p) or m.trunk(name):
            continue
        sub = m.subtree(name)
        w = _words(name)
        kind = ('tail' if TAILLIKE_RE.search(name) else 'ear' if 'ear' in w else
                'horn' if w & {'horn', 'antler', 'tusk'} else 'wing' if 'wing' in w else
                'fin' if w & (PIECE_JUNCTION_WORDS - {'wing'}) else 'limb')
        head, tail = b['head'], b['tail']
        r, rs = None, None
        for o in [m.body] + m.pieces:
            g, dom = m.geo[o.name], m.dom[o.name]
            idx = np.array([i for i, d in enumerate(dom) if d in sub])
            if len(idx) < 6:
                continue
            d, t = _seg_dist(g.V[idx], head, tail)
            sel = d[t < 0.5]
            if len(sel) >= 6:
                r, rs = float(np.median(sel)), sel
                break
        r = r or 0.04 * m.L
        # outward: from the parent bone's axis to the root (a tail: along its bone)
        pb = m.bones[p]
        d0, _ = _seg_dist(head[None], pb['head'], pb['tail'])
        ab = pb['tail'] - pb['head']
        t0 = np.clip((head - pb['head']) @ ab / max(ab @ ab, 1e-12), 0, 1)
        out = head - (pb['head'] + t0 * ab)
        if np.linalg.norm(out) < 0.5 * r:
            out = tail - head
        J.append(dict(name=name, kind=kind, root=head, axis=_unit(tail - head), out=_unit(out), r=r,
                      reach=ROOT_REACH * float(np.linalg.norm(tail - head)),
                      bones=sorted(sub), parent=p, source='bone', r_samples=rs))
    _mirror_radius(m, J)
    # big membrane-like pieces on the body: one junction per side at the contact patch
    bt = m.geo[m.body.name].bvh()
    for o in m.pieces:
        if not has_word(o.name, PIECE_JUNCTION_WORDS):
            continue
        g = m.geo[o.name]
        for side in (1, -1):
            idx = np.where(np.sign(g.V[:, 0] + 1e-9) == side)[0]
            if len(idx) < 4:
                continue
            dist = np.array([bt.find_nearest(Vector(g.V[i]))[3] or 1e9 for i in idx])
            near = idx[dist < 0.01 * m.L]
            if len(near) < 3:
                near = idx[np.argsort(dist)[:6]]
            root = g.V[near].mean(0)
            span = np.linalg.norm(g.V[near] - root, axis=1)
            r = float(max(np.percentile(span, 75), 0.02 * m.L))
            far = g.V[idx].mean(0)
            J.append(dict(name=f"{o.name}.{'L' if side > 0 else 'R'}", kind='wing' if 'wing' in _words(o.name) else 'fin',
                          root=root, axis=_unit(far - root), out=_unit(np.array([side, 0, 0.3])), r=r,
                          bones=[], parent=None, source='piece', piece=o.name, side=side))
    return J


ROOT_REACH = 0.6         # the probe stops this far down the chain's first bone: the root, not the knee


def _mirror_radius(m, J):
    """A mirrored pair (thigh.L / thigh.R) gets ONE radius: the median over both sides' samples (the
    distances to each side's own bone axis, i.e. measured on the union of the geometry and its mirror).
    Kit bug 2026-10-23: the eagle's thigh.L read r 72.2 mm and thigh.R 67.4 mm from a few vertices the
    weights gave to one side only, so the same 69 mm seam strip passed on one side (0.96 r) and failed
    on the other (1.03 r). Pairs: same kind, roots mirrored across x = 0 within 2% of the size."""
    used = set()
    for a, ja in enumerate(J):
        if a in used or ja['source'] != 'bone' or abs(ja['root'][0]) < 0.01 * m.L:
            continue
        mir = ja['root'] * np.array([-1.0, 1, 1])
        best = None
        for b, jb in enumerate(J):
            if b == a or b in used or jb['source'] != 'bone' or jb['kind'] != ja['kind']:
                continue
            d = float(np.linalg.norm(jb['root'] - mir))
            if d < 0.02 * m.L and (best is None or d < best[0]):
                best = (d, b)
        if best is None:
            continue
        jb = J[best[1]]
        used |= {a, best[1]}
        ra, rb = ja.get('r_samples'), jb.get('r_samples')
        if ra is not None and rb is not None:
            r = float(np.median(np.concatenate([ra, rb])))
        else:
            r = 0.5 * (ja['r'] + jb['r'])
        ja['r_side'], jb['r_side'] = ja['r'], jb['r']
        ja['r'] = jb['r'] = r
        ja['mirror'], jb['mirror'] = jb['name'], ja['name']
    for j in J:
        j.pop('r_samples', None)


def region(g, j):
    """Body triangles of a junction: centre within REGION_K x r of the root and, for a bone root, no
    further down the first bone than ROOT_REACH of its length (a big thigh radius would reach the knee)."""
    d = g.C - j['root']
    sel = np.linalg.norm(d, axis=1) < L_['REGION_K'] * j['r']
    if j.get('reach'):
        sel &= (d @ j['axis']) < j['reach']
    return np.where(sel)[0]


def _unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else np.array([1.0, 0, 0])


# --------------------------------------------------------------------------------------------- probe
def _fold_angles(g, tris):
    """For every edge touching `tris` with exactly two triangles: (edge, angle deg, concave?)."""
    E = g.edges()
    tri_set = set(int(t) for t in tris)
    out = []
    for e, ts in E.items():
        if len(ts) != 2 or (ts[0] not in tri_set and ts[1] not in tri_set):
            continue
        t1, t2 = ts
        n1, n2 = g.N[t1], g.N[t2]
        ang = math.degrees(math.acos(max(-1.0, min(1.0, float(n1 @ n2)))))
        w = [int(v) for v in g.T[t2] if v not in e][0]
        concave = float((g.V[w] - g.V[e[0]]) @ n1) > 1e-7
        out.append((e, ang, concave, t1, t2))
    return out


def _expo_dirs():
    D = []
    for el in (0, 35):
        for az in range(0, 360, 45):
            a, e = math.radians(az), math.radians(el)
            D.append(np.array([math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)]))
    D.append(np.array([0, 0, 1.0]))
    return D


EXPO_DIRS = _expo_dirs()      # the review cameras: 8 azimuths level and at +35 deg, and the top


def exposure(m, g, tris, trees):
    """For each triangle: in how many review views (EXPO_DIRS) its centre faces the camera unoccluded.
    A fold nobody can see (deep in an armpit, under the belly) is not what the owner flags."""
    out = {}
    eps = 1e-4 * m.L
    for t in tris:
        n = 0
        for d in EXPO_DIRS:
            if float(g.N[t] @ d) <= 0.1:
                continue
            o = Vector(g.C[t] + d * eps)
            if not any(tr.ray_cast(o, Vector(d), 3 * m.L)[0] is not None for tr in trees):
                n += 1
        out[int(t)] = n
    return out


def probe(m, J, posed=True):
    g = m.geo[m.body.name]
    bt = g.bvh()
    trees = [bt] + [m.geo[o.name].bvh() for o in m.pieces]
    E = g.edges()
    open_e = [e for e, ts in E.items() if len(ts) == 1]
    nonman = [e for e, ts in E.items() if len(ts) > 2]
    flags = {o: {} for o in m.geo}

    def flag(oname, poly, cls):
        cur = flags[oname].get(poly)
        if cur is None or FLAG_PRI.index(cls) < FLAG_PRI.index(cur):
            flags[oname][poly] = cls

    # per-vertex chain label (index into J) for the posed clip test
    lab = {}
    for o, dom in m.dom.items():
        L = np.full(len(dom), -1)
        for ji, j in enumerate(J):
            if j['source'] == 'bone':
                bs = set(j['bones'])
                L[[i for i, d in enumerate(dom) if d in bs]] = ji
            elif j.get('piece') == o:
                L[np.sign(m.geo[o].V[:, 0] + 1e-9) == j['side']] = ji
        lab[o] = L

    def tri_lab(o):
        Lv = lab[o][m.geo[o].T]
        same = (Lv[:, 0] == Lv[:, 1]) | (Lv[:, 0] == Lv[:, 2])
        return np.where(same, Lv[:, 0], Lv[:, 1])
    tlab = {o: tri_lab(o) for o in m.geo}
    bl = tlab[m.body.name]

    res = []
    for ji, j in enumerate(J):
        R = L_['REGION_K'] * j['r']
        reg = region(g, j)
        # another appendage's own faces are not this root's join (kit bug 2026-10-23: the elephant's ear rim
        # lay inside the 2r shoulder region and was flagged as a shoulder seam strip): keep the trunk's faces
        # and this chain's faces only
        n_all = len(reg)
        reg = reg[(bl[reg] < 0) | (bl[reg] == ji)]
        rset = set(int(t) for t in reg)
        out = dict(name=j['name'], kind=j['kind'], source=j['source'], r_mm=round(1000 * j['r'], 1),
                   root=[round(float(x), 3) for x in j['root']], region_tris=int(len(reg)),
                   other_chain_tris=int(n_all - len(reg)))
        if 'r_side' in j:
            out['r_side_mm'] = round(1000 * j['r_side'], 1)
        for t in reg:
            flag(m.body.name, int(g.poly[t]), 'region')
        # open / non-manifold edges
        ro = [e for e in open_e + nonman if any(t in rset for t in E[e])]
        out['open_edges'] = len(ro)
        for e in ro:
            for t in E[e]:
                flag(m.body.name, int(g.poly[t]), 'open')
        # folds
        folds = _fold_angles(g, reg)
        ex = exposure(m, g, set(int(t) for t in reg) | {t for f in folds for t in (f[3], f[4])}, trees)
        seen = lambda t: ex.get(int(t), 0) >= L_['EXPOSED']
        # a fold shows when either of its faces is seen from EXPOSED review views
        conc = [f for f in folds if f[2] and (seen(f[3]) or seen(f[4]))]
        out['max_concave_deg'] = round(max((f[1] for f in conc), default=0.0), 1)
        out['hidden_max_concave_deg'] = round(max((f[1] for f in folds if f[2]), default=0.0), 1)
        knives = [f for f in conc if f[1] > L_['KNIFE_DEG']]
        klen = sum(float(np.linalg.norm(g.V[f[0][0]] - g.V[f[0][1]])) for f in knives)
        out['knife_edges'] = len(knives)
        out['knife_len_r'] = round(klen / j['r'], 2)
        for f in knives:
            flag(m.body.name, int(g.poly[f[3]]), 'knife'); flag(m.body.name, int(g.poly[f[4]]), 'knife')
        # seam strips
        if len(reg):
            medw = float(np.median(np.sqrt(2 * g.A[reg])))
            creased = {}
            for e, ang, cc, t1, t2 in folds:
                if ang > L_['STRIP_CREASE_DEG']:
                    creased[t1] = creased[t2] = True
            thin = [int(t) for t in reg if seen(t) and g.width[t] < L_['STRIP_W'] * medw
                    and g.longest[t] > L_['STRIP_ASPECT'] * g.width[t] and creased.get(int(t))]
            comps = _components(g, thin)
            strips = []
            for c in comps:
                # strip length: the extent of its vertices along their main direction
                P = g.V[np.unique(g.T[c])]
                ln = float(np.ptp((P - P.mean(0)) @ _pca1(P))) if len(P) > 2 else 0.0
                strips.append((ln, float(g.width[c].min()), c))
            strips.sort(key=lambda s: -s[0])
            out['strip_max_len_r'] = round(strips[0][0] / j['r'], 2) if strips else 0.0
            out['strip_min_width_mm'] = round(1000 * strips[0][1], 1) if strips else None
            out['strip_count'] = sum(1 for s in strips if s[0] > L_['STRIP_LEN_K'] * j['r'])
            out['median_face_mm'] = round(1000 * medw, 1)
            for ln, w, c in strips:
                if ln > L_['STRIP_LEN_K'] * j['r']:
                    for t in c:
                        flag(m.body.name, int(g.poly[t]), 'strip')
        # slits: a face's normal ray hits a non-neighbouring body face very close
        near = g.near_ring(reg, 2)
        slit_a = 0.0
        eps = 1e-5 * m.L
        for t in reg:
            hit = bt.ray_cast(Vector(g.C[t] + g.N[t] * eps), Vector(g.N[t]), L_['SLIT_K'] * j['r'])
            if hit[0] is not None and hit[2] not in near[int(t)]:
                slit_a += g.A[t]
                flag(m.body.name, int(g.poly[t]), 'slit')
        out['slit_pct'] = round(100 * slit_a / max(float(g.A[reg].sum()), 1e-12), 2) if len(reg) else 0.0
        # poke: body crossing itself in the region (rest)
        sub = [int(t) for t in reg]
        poke = 0
        if sub:
            st = BVHTree.FromPolygons([tuple(p) for p in g.V], [tuple(int(i) for i in g.T[t]) for t in sub], all_triangles=True)
            for a, b in st.overlap(bt):
                ta = sub[a]
                if b not in near[ta]:
                    poke += 1
                    flag(m.body.name, int(g.poly[ta]), 'poke')
        out['poke_tris'] = poke
        # pinches (warn)
        VT = g.vtris()
        pv = set(int(v) for v in np.unique(g.T[reg])) if len(reg) else set()
        pinch = 0
        for v in pv:
            s = 0.0
            for t in VT[v]:
                tt = g.T[t]
                k = list(tt).index(v)
                a, b = g.V[tt[(k + 1) % 3]] - g.V[v], g.V[tt[(k + 2) % 3]] - g.V[v]
                s += math.acos(max(-1, min(1, float(a @ b) / max(np.linalg.norm(a) * np.linalg.norm(b), 1e-15))))
            boundary = any(len(E[(min(v, int(u)), max(v, int(u)))]) == 1 for t in VT[v] for u in g.T[t] if int(u) != v)
            if not boundary and abs(2 * math.pi - s) > L_['PINCH_RAD']:
                pinch += 1
                for t in VT[v]:
                    flag(m.body.name, int(g.poly[t]), 'pinch')
        out['pinch_verts'] = pinch
        # shoulder shelf (top view)
        if j['source'] == 'bone' and j['kind'] == 'limb' and has_word(j['name'], ARM_WORDS) \
                and abs(j['root'][0]) > 0.01 * m.L and j['axis'][2] < SHELF_HANG:
            sh = _shelf(m, g, j, reg, trees)
            out.update(sh['out'])
            for t in sh['tris']:
                flag(m.body.name, int(g.poly[t]), 'shelf')
        # pieces near the root: hovering shells (gap) and seat lift
        gaps = []
        for o in m.pieces:
            if re.search(r'eye', o.name, re.I):
                continue
            pg = m.geo[o.name]
            for sh in pg.shells():
                vi = np.unique(pg.T[sh])
                dr = np.linalg.norm(pg.V[vi] - j['root'], axis=1)
                if dr.min() > R:
                    continue
                dist = []
                inside = 0
                for v in vi:
                    loc, nrm, _, d = bt.find_nearest(Vector(pg.V[v]))
                    if loc is None:
                        continue
                    sgn = float((pg.V[v] - np.array(loc)) @ np.array(nrm))
                    inside += sgn < 0
                    dist.append(d)
                if not dist:
                    continue
                gmin = min(dist)
                if inside == 0 and 0.002 * m.L < gmin < L_['GAP_K'] * j['r']:
                    gaps.append(dict(piece=o.name, gap_mm=round(1000 * gmin, 1)))
                    for t in sh:
                        flag(o.name, int(pg.poly[t]), 'gap')
        out['gaps'] = gaps
        res.append(out)

    # posed clipping, chain against chain
    if posed and m.rig and bpy.data.actions:
        _posed_clip(m, J, res, tlab, flag)
    return res, flags, dict(open_edges=len(open_e), nonmanifold_edges=len(nonman))


def _shelf(m, g, j, reg, trees):
    """The troll T-bar: seen from above, the shoulder is a level shelf that runs out from the torso over
    the arm root (the arm's top WAS the shoulder top, levelled out past the torso side) and drops into a
    vertical outer wall. Measured on the region's faces outboard of the root (|x| beyond the arm bone's
    head) that face up within SHELF_DEG of +z and are unoccluded from the top view; the largest
    edge-connected patch of them: its area / r^2 and its width across the limb (/ r). A round arm top is
    a line of faces one or two columns wide; a shelf is a level slab at least as wide as the arm."""
    side = 1.0 if j['root'][0] > 0 else -1.0
    up = np.array([0, 0, 1.0])
    cz = math.cos(math.radians(L_['SHELF_DEG']))
    eps = 1e-4 * m.L
    cand = []
    for t in reg:
        if g.N[t][2] < cz or side * g.C[t][0] < side * j['root'][0]:
            continue
        o = Vector(g.C[t] + up * eps)
        if any(tr.ray_cast(o, Vector(up), 3 * m.L)[0] is not None for tr in trees):
            continue
        cand.append(int(t))
    best, area, wid, lat = [], 0.0, 0.0, 0.0
    for c in _components(g, cand):
        a = float(g.A[c].sum())
        if a > area:
            P = g.V[np.unique(g.T[c])]
            best, area = c, a
            lat = float(np.ptp(P[:, 0]))                 # along the shoulder line (out from the torso)
            wid = float(np.ptp(P[:, 1]))                 # across it, front to back
    r2 = j['r'] ** 2
    out = dict(shelf_area_r2=round(area / r2, 2), shelf_width_r=round(wid / j['r'], 2),
               shelf_len_r=round(lat / j['r'], 2))
    is_shelf = area > L_['SHELF_AREA_K'] * r2 and wid > L_['SHELF_W_K'] * j['r']
    out['shelf'] = bool(is_shelf)
    return dict(out=out, tris=best if is_shelf else [])


def _pca1(P):
    Q = P - P.mean(0)
    w, v = np.linalg.eigh(Q.T @ Q)
    return v[:, -1]


def _components(g, tris):
    """Connected groups of the given triangles (sharing an edge)."""
    ts = set(tris)
    E = g.edges()
    adj = {t: set() for t in ts}
    for e, l in E.items():
        if len(l) == 2 and l[0] in ts and l[1] in ts:
            adj[l[0]].add(l[1]); adj[l[1]].add(l[0])
    seen, comps = set(), []
    for t in ts:
        if t in seen:
            continue
        c, todo = [], [t]
        seen.add(t)
        while todo:
            x = todo.pop()
            c.append(x)
            for y in adj[x]:
                if y not in seen:
                    seen.add(y); todo.append(y)
        comps.append(np.array(c))
    return comps


def _posed_clip(m, J, res, tlab, flag):
    import techqa as Q
    rig = m.rig
    rig.data.pose_position = 'POSE'
    if rig.animation_data is None:
        rig.animation_data_create()
    objs = [m.body] + [p for p in m.pieces if not re.search(r'eye', p.name, re.I)]
    gb = m.geo[m.body.name]
    nearb = gb.near_ring(range(len(gb.T)), 2)

    def crossings(Vs):
        """{(obj, tri)} pairs crossing another label: returns {obj: {tri: partner_label}}"""
        trees = {o.name: m.geo[o.name].bvh(Vs[o.name]) for o in objs}
        out = {o.name: {} for o in objs}
        bn = m.body.name
        for a, b in trees[bn].overlap(trees[bn]):
            if a == b or b in nearb[a]:
                continue
            la, lb = tlab[bn][a], tlab[bn][b]
            if la != lb:
                out[bn][a] = lb
        for o in objs[1:]:
            for a, b in trees[o.name].overlap(trees[bn]):
                la, lb = tlab[o.name][a], tlab[bn][b]
                if la != lb:
                    out[o.name][a] = lb
                    out[bn][b] = la
        return out
    rest = crossings({o.name: m.geo[o.name].V for o in objs})
    area = {ji: sum(float(m.geo[o.name].A[tlab[o.name] == ji].sum()) for o in objs) for ji in range(len(J))}
    worst = {ji: dict(clip_pct=0.0, root_clip_pct=0.0, at=None, partners=set()) for ji in range(len(J))}
    for act in bpy.data.actions:
        Q._zero_pose(rig)
        rig.animation_data.action = act
        try:
            if getattr(act, 'slots', None) and len(act.slots) and rig.animation_data.action_slot is None:
                rig.animation_data.action_slot = act.slots[0]
        except Exception:
            pass
        for f in Q.sample_frames(act):
            bpy.context.scene.frame_set(f)
            Vs = {o.name: m.geo[o.name].posed() for o in objs}
            cr = crossings(Vs)
            acc = {ji: [0.0, 0.0, set()] for ji in range(len(J))}
            hits = []
            for on, d in cr.items():
                pg = m.geo[on]
                for t, partner in d.items():
                    if t in rest[on]:
                        continue
                    own = int(tlab[on][t])
                    if own < 0:
                        continue
                    if partner < 0:
                        acc[own][1] += float(pg.A[t])
                    else:
                        acc[own][0] += float(pg.A[t]); acc[own][2].add(J[partner]['name'])
                        hits.append((on, t))
            for ji, (a_c, a_r, ps) in acc.items():
                A = max(area[ji], 1e-12)
                w = worst[ji]
                if 100 * a_c / A > w['clip_pct']:
                    w['clip_pct'] = 100 * a_c / A; w['at'] = f'{act.name}@{f}'
                w['root_clip_pct'] = max(w['root_clip_pct'], 100 * a_r / A)
                w['partners'] |= ps
            for on, t in hits:
                flag(on, int(m.geo[on].poly[t]), 'clip')
    Q._zero_pose(rig)
    rig.animation_data.action = None
    rig.data.pose_position = 'REST'
    bpy.context.view_layer.update()
    for ji, r in enumerate(res):
        w = worst[ji]
        r['clip_pct'] = round(w['clip_pct'], 2)
        r['clip_at'] = w['at']
        r['clip_with'] = sorted(w['partners'])
        r['root_clip_pct'] = round(w['root_clip_pct'], 2)


def judge(r):
    """Gate one junction's numbers: list of failure strings (empty = PASS)."""
    f = []
    if r['open_edges']:
        f.append(f"open edges {r['open_edges']}")
    if r['knife_len_r'] > L_['KNIFE_LEN_K']:
        f.append(f"knife folds {r['knife_edges']} ({r['knife_len_r']} r, max {r['max_concave_deg']} deg)")
    if r.get('strip_count'):
        f.append(f"seam strip {r['strip_max_len_r']} r long, {r['strip_min_width_mm']} mm wide")
    if r['slit_pct'] > L_['SLIT_PCT']:
        f.append(f"slit {r['slit_pct']}% of region")
    if r['poke_tris']:
        f.append(f"poke-through {r['poke_tris']} tris")
    if r['gaps']:
        f.append('gap ' + ', '.join(f"{g['piece']} {g['gap_mm']} mm" for g in r['gaps']))
    if r.get('clip_pct', 0) > L_['CLIP_PCT']:
        f.append(f"posed clip {r['clip_pct']}% with {'/'.join(r['clip_with'])} at {r['clip_at']}")
    if r.get('shelf'):
        f.append(f"shoulder shelf {r['shelf_area_r2']} r^2 level from the top, {r['shelf_width_r']} r wide")
    return f


# ------------------------------------------------------------------------------------------- the eye
def eye_check(m):
    eyes = [o for o in m.pieces if re.search(r'eye', o.name, re.I)]
    out = []
    if not eyes:
        return [dict(side='-', ok=False, fail=['no piece named *eye*'])]
    others = [o for o in m.geo if o not in [e.name for e in eyes]]
    trees = {o: m.geo[o].bvh() for o in others}
    head = None
    hb = next((b for b in ('head', 'skull', 'cranium') if b in m.bones), None)
    if hb:
        # the skull: the head bone and its centre-line (trunk) children such as the jaw or snout; NOT the
        # ears, horns, tufts or lobes (kit bug 2026-10-23: the head length took the bbox with the ears, so a
        # tall-eared head forced a big eye) nor a proboscis
        keep, todo = set(), [hb]
        while todo:                              # only bones reachable through kept bones
            n = todo.pop()
            if n == hb or (m.trunk(n) and not has_word(n, {'trunk', 'proboscis'})):
                keep.add(n)
                todo += m.bones[n]['children']
        idx = [i for i, d in enumerate(m.dom[m.body.name]) if d in keep]
        if len(idx) > 8:
            P = m.geo[m.body.name].V[idx]
            head = float(np.ptp(P, 0).max())
    for side in (1, -1):
        shells = []
        for e in eyes:
            g = m.geo[e.name]
            for sh in g.shells():
                c = g.C[sh].mean(0)
                if np.sign(c[0] + 1e-9) == side:
                    shells.append((e, g, sh))
        if not shells:
            continue
        # the lens: the largest shell; the pupil and highlight shells sit on it
        e, g, lens = max(shells, key=lambda s: float(s[1].A[s[0 + 2]].sum()))
        P = g.V[np.unique(g.T[lens])]
        cen = P.mean(0)
        Q_ = P - cen
        ext = np.sort(np.ptp(Q_ @ np.linalg.eigh(Q_.T @ Q_)[1], 0))[::-1]
        diam = float(ext[0])
        rnd = float(ext[1] / max(ext[0], 1e-9))
        r = dict(side='L' if side > 0 else 'R', centre=[round(float(x), 3) for x in cen], diam_mm=round(1000 * diam, 1),
                 round=round(rnd, 2))
        if head:
            r['diam_head'] = round(diam / head, 3)
        # seated and proud: signed distance of the lens vertices to the body
        bt = trees[m.body.name]
        sd = []
        for p in P:
            loc, nrm, _, d = bt.find_nearest(Vector(p))
            if loc is not None:
                sd.append(math.copysign(d, float((p - np.array(loc)) @ np.array(nrm))))
        r['embed_mm'] = round(-1000 * min(min(sd), 0), 1) if sd else None
        r['proud_mm'] = round(1000 * max(max(sd), 0), 1) if sd else None
        # visibility from the named views
        vis, unocc = {}, {}
        for vname, az in (('front', 0), ('threeq', 45 if side > 0 else 315), ('side', 90 if side > 0 else 270)):
            t = math.radians(az)
            d = np.array([math.sin(t), -math.cos(t), 0.0])
            tot = seen = 0.0
            for ti in lens:
                f = float(g.N[ti] @ d)
                if f <= 0.02:
                    continue
                a = float(g.A[ti]) * f
                tot += a
                tv = g.V[g.T[ti]]
                pts = [g.C[ti]] + [(g.C[ti] + p) / 2 for p in tv]
                for q in pts:                   # 4 samples per triangle, each a quarter of its projected area
                    o = q + d * 1e-4 * m.L
                    if not any(tr.ray_cast(Vector(o), Vector(d), 2 * m.L)[0] is not None for tr in trees.values()):
                        seen += a / len(pts)
            # shown: visible projected lens area / the lens disc (pi d^2 / 4): how much eye the view gets
            vis[vname] = round(seen / (math.pi * diam * diam / 4), 2)
            unocc[vname] = round(seen / tot, 2) if tot > 0 else 0.0
        r['visible'] = vis
        r['unoccluded'] = unocc
        fail = []
        for k, lim in L_['EYE_VIS'].items():
            if vis[k] < lim:
                fail.append(f'{k} view {vis[k]:.2f} < {lim}')
        lo, hi = L_['EYE_SIZE']
        if head and not lo <= r['diam_head'] <= hi:
            fail.append(f"size {r['diam_head']} of head length (allowed {lo}-{hi})")
        if rnd < L_['EYE_ROUND']:
            fail.append(f'not round ({rnd:.2f})')
        if r['embed_mm'] is not None and r['embed_mm'] <= 0.0:
            fail.append('not seated in the head (no part inside)')
        if r['proud_mm'] is not None and r['proud_mm'] < 0.5:
            fail.append('not proud of the socket (< 0.5 mm out)')
        r['fail'] = fail
        r['ok'] = not fail
        out.append(r)
    return out


# -------------------------------------------------------------------------------------- the membrane
def membrane_check(m, J, flags):
    floor = max(L_['MEMBRANE_ABS'], L_['MEMBRANE_REL'] * m.L)
    out = []
    targets = []
    for o in m.pieces:
        if has_word(o.name, MEMBRANE_WORDS) and not re.search(r'eye', o.name, re.I):
            g = m.geo[o.name]
            targets.append((o.name, o.name, np.arange(len(g.T))))
    gb = m.geo[m.body.name]
    for j in J:
        if j['source'] == 'bone' and has_word(j['name'], MEMBRANE_WORDS):
            bs = set(j['bones'])
            Lv = np.array([d in bs for d in m.dom[m.body.name]])
            tris = np.where(Lv[gb.T].all(1))[0]
            if len(tris):
                targets.append((f"body:{j['name']}", m.body.name, tris))
    for label, on, tris in targets:
        g = m.geo[on]
        bt = g.bvh()
        E = g.edges()
        th = np.zeros(len(tris))
        open_n = 0
        for k, t in enumerate(tris):
            d = -g.N[t]
            hit = bt.ray_cast(Vector(g.C[t] + d * 1e-6 * m.L), Vector(d), m.L)
            th[k] = hit[3] if hit[0] is not None else 0.0
        open_n = sum(1 for e, ts in E.items() if len(ts) == 1 and any(x in set(tris.tolist()) for x in ts))
        A = g.A[tris]
        o = np.argsort(th)
        cum = np.cumsum(A[o]) / max(A.sum(), 1e-15)
        p10 = float(th[o][np.searchsorted(cum, 0.10)]) if len(o) else 0.0
        p50 = float(th[o][np.searchsorted(cum, 0.50)]) if len(o) else 0.0
        thin = th < floor
        for t in tris[thin]:
            flags[on][int(g.poly[t])] = flags[on].get(int(g.poly[t])) if flags[on].get(int(g.poly[t])) in ('open', 'poke', 'gap', 'knife') else 'thin'
        r = dict(target=label, p10_mm=round(1000 * p10, 1), p50_mm=round(1000 * p50, 1), floor_mm=round(1000 * floor, 1),
                 thin_area_pct=round(100 * float(A[thin].sum()) / max(float(A.sum()), 1e-15), 1), open_edges=open_n)
        r['fail'] = ([f"p10 thickness {r['p10_mm']} mm < {r['floor_mm']} mm"] if p10 < floor else []) + \
                    ([f'{open_n} open edges (single-sided plate)'] if open_n else [])
        r['ok'] = not r['fail']
        out.append(r)
    return out


# ---------------------------------------------------------------------------------- straps and bands
BAND_WORDS = {'strap', 'belt', 'band', 'collar', 'harness', 'sash', 'bracer', 'loincloth', 'cuff', 'ring'}


def seat_check(m, flags):
    """Straps, belts and bands: the share of a band's inner face (the side facing the body) that lifts
    off the skin by more than SEAT_LIFT x size — the dark slit under a belt, the specks along a strap."""
    bt = m.geo[m.body.name].bvh()
    out = []
    for o in m.pieces:
        if not has_word(o.name, BAND_WORDS):
            continue
        g = m.geo[o.name]
        inner = lifted = 0.0
        for t in range(len(g.T)):
            loc, nrm, _, d = bt.find_nearest(Vector(g.C[t]))
            if loc is None or d > L_['SEAT_FAR'] * m.L:
                continue
            to_body = np.array(loc) - g.C[t]
            if float(g.N[t] @ to_body) <= 0:          # an outer face
                continue
            inner += g.A[t]
            outside = float((g.C[t] - np.array(loc)) @ np.array(nrm)) > 0     # sunk into the skin is seated, not lifted
            if outside and d > L_['SEAT_LIFT'] * m.L:
                lifted += g.A[t]
                flags[o.name][int(g.poly[t])] = 'gap'
        pct = round(100 * lifted / max(inner, 1e-15), 1)
        r = dict(piece=o.name, lifted_pct=pct, ok=pct <= L_['SEAT_PCT'])
        r['fail'] = [] if r['ok'] else [f'{pct}% of the inner face lifts off the skin (> {L_["SEAT_PCT"]}%)']
        out.append(r)
    return out


# ------------------------------------------------------------------------------------------- renders
def _views_for(j):
    o = j['out']
    s = np.array([0, -1.0, 0]) if abs(o[0]) > 0.5 else np.array([1.0, 0, 0])
    s = _unit(s - (s @ o) * o)
    z = np.array([0, 0, 1.0])
    return [('A', _unit(o + 0.7 * s + 0.35 * z)), ('B', _unit(o - 0.7 * s + 0.35 * z)), ('C', _unit(0.8 * o + 0.5 * s - 0.8 * z))]


def render_crops(m, J, eyes, outdir, tag, flags, res=480, RG=None):
    import bmkit as K
    files = []
    frame = dict(centre=list((m.lo + m.hi) / 2), size=list(m.hi - m.lo), floor=float(m.lo[2]))
    RG['beauty_setup'](frame)
    try:
        bpy.context.scene.eevee.taa_render_samples = 16      # crops: 16 samples read the same, 4x faster
    except AttributeError:
        pass
    ground = bpy.data.objects.get('_ground')
    shots = []
    for ji, j in enumerate(J):
        rad = 2.4 * j['r']
        for vn, d in _views_for(j):
            shots.append((f'j{ji}_{vn}', j['root'], rad, d))
    for e in eyes:
        if 'centre' not in e:
            continue
        rad = max(3.0 * e['diam_mm'] / 1000, 0.02 * m.L)
        sd = 1 if e['side'] == 'L' else -1
        for vn, az in (('front', 0), ('threeq', 45 * sd), ('side', 90 * sd)):
            t = math.radians(az)
            shots.append((f"eye{e['side']}_{vn}", np.array(e['centre']), rad, np.array([math.sin(t), -math.cos(t), 0.08])))

    def shoot(name, c, rad, d, mode):
        dist = rad / math.tan(K.FOV / 2)
        fr = dict(centre=list(c), size=[dist / K.DIST] * 3)
        K.view('_jv', tuple(d))
        cam = K.camera(fr, '_jv')
        if ground:
            ground.hide_render = cam.location.z < frame['floor'] + 0.01
        p = os.path.join(outdir, f'{tag}_{name}_{mode}.png')
        K._render(p, res)
        return p
    for name, c, rad, d in shots:
        files.append(shoot(name, c, rad, d, 'beauty'))
    # the flag heatmap from the same three angles (workbench: fast)
    K._workbench('tech')
    act = {}
    for o in [m.body] + m.pieces:
        me = o.data
        act[o.name] = me.color_attributes.active_color.name if me.color_attributes.active_color else None
        at = me.color_attributes.get('_jq') or me.color_attributes.new('_jq', 'BYTE_COLOR', 'CORNER')
        fl = flags.get(o.name, {})
        cols = []
        for p in me.polygons:
            c = FLAG_COL[fl.get(p.index, 'ok')]
            cols += [c[0], c[1], c[2], 1.0] * p.loop_total
        at.data.foreach_set('color', cols)
        me.color_attributes.active_color = at
    if ground:
        ground.hide_render = True
    for ji, j in enumerate(J):
        for vn, d in _views_for(j):
            files.append(shoot(f'j{ji}_{vn}', j['root'], 2.4 * j['r'], d, 'flags'))
    for o in [m.body] + m.pieces:
        me = o.data
        if act.get(o.name):
            me.color_attributes.active_color = me.color_attributes[act[o.name]]
    return files


# ---------------------------------------------------------------------------------------------- main
def _render_glb():
    sys_argv = sys.argv
    src = open(os.path.join(KIT, 'render_glb.py'), encoding='utf-8').read().replace('\nmain()\n', '\n')
    RG = {'__file__': os.path.join(KIT, 'render_glb.py'), '__name__': 'render_glb'}
    exec(compile(src, 'render_glb', 'exec'), RG)
    sys.argv = sys_argv
    return RG


def run_probe(glb, outdir, tag='probe', render=True, posed=True, res=480):
    RG = _render_glb()
    meshes, frame = RG['load'](glb)
    m = Model(meshes)
    J = find_junctions(m)
    res_j, flags, glob_ = probe(m, J, posed=posed)
    for r in res_j:
        r['fail'] = judge(r)
        r['ok'] = not r['fail']
    eyes = eye_check(m)
    mem = membrane_check(m, J, flags)
    seats = seat_check(m, flags)
    os.makedirs(outdir, exist_ok=True)
    files = render_crops(m, J, eyes, outdir, tag, flags, res=res, RG=RG) if render else []
    ok = all(r['ok'] for r in res_j) and all(e['ok'] for e in eyes) and all(x['ok'] for x in mem) \
        and glob_['open_edges'] == 0 and glob_['nonmanifold_edges'] == 0
    rep = dict(glb=glb, tag=tag, ok=ok, size_m=round(m.L, 3), limits=LIMITS, body=glob_, junctions=res_j, eyes=eyes,
               membranes=mem, seats=seats, crops=[os.path.basename(f) for f in files],
               views={f'j{ji}': [vn for vn, _ in _views_for(j)] for ji, j in enumerate(J)})
    with open(os.path.join(outdir, f'{tag}_junctions.json'), 'w', encoding='utf-8') as f:
        json.dump(rep, f, indent=1, default=lambda o: o.tolist() if hasattr(o, 'tolist') else str(o))
    _report(rep)
    return rep


def _report(rep):
    b = rep['body']
    say(('PASS' if b['open_edges'] == 0 and b['nonmanifold_edges'] == 0 else 'FAIL') +
        f" junction body: open edges {b['open_edges']}, non-manifold {b['nonmanifold_edges']}")
    for r in rep['junctions']:
        nums = (f"r {r['r_mm']} mm; open {r['open_edges']}; knife {r['knife_edges']} ({r['knife_len_r']} r, max concave "
                f"{r['max_concave_deg']} deg); strip {r.get('strip_max_len_r', 0)} r/{r.get('strip_min_width_mm')} mm; "
                f"slit {r['slit_pct']}%; poke {r['poke_tris']}; gaps {len(r['gaps'])}; pinch {r['pinch_verts']}"
                + (f"; clip {r['clip_pct']}% {'/'.join(r['clip_with'])} {r['clip_at'] or ''}; root clip {r['root_clip_pct']}%"
                   if 'clip_pct' in r else '')
                + (f"; shelf {r['shelf_area_r2']} r2 x {r['shelf_width_r']} r" if 'shelf_area_r2' in r else ''))
        say(('PASS' if r['ok'] else 'FAIL') + f" junction {r['name']} ({r['kind']}): {nums}"
            + ('' if r['ok'] else '  <<  ' + '; '.join(r['fail'])))
    for e in rep['eyes']:
        say(('PASS' if e['ok'] else 'FAIL') + f" eye {e['side']}: " +
            (f"visible front/3q/side {e['visible']['front']}/{e['visible']['threeq']}/{e['visible']['side']}; "
             f"diam {e['diam_mm']} mm = {e.get('diam_head')} head; round {e['round']}; embed {e['embed_mm']} mm, proud {e['proud_mm']} mm"
             if 'visible' in e else '') + ('' if e['ok'] else '  <<  ' + '; '.join(e['fail'])))
    for x in rep['membranes']:
        say(('PASS' if x['ok'] else 'FAIL') + f" membrane {x['target']}: p10 {x['p10_mm']} mm, p50 {x['p50_mm']} mm "
            f"(floor {x['floor_mm']}), thin {x['thin_area_pct']}% of area, open {x['open_edges']}"
            + ('' if x['ok'] else '  <<  ' + '; '.join(x['fail'])))
    for x in rep.get('seats', []):
        say(('PASS' if x['ok'] else 'WARN') + f" band seat {x['piece']}: {x['lifted_pct']}% of the inner face lifted"
            + ('' if x['ok'] else '  <<  ' + '; '.join(x['fail'])))
    say('junction probe', 'PASS' if rep['ok'] else 'FAIL')


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if len(argv) < 2:
        print(__doc__); sys.exit(2)
    glb, outdir = os.path.abspath(argv[0]), os.path.abspath(argv[1])
    tag = argv[argv.index('--tag') + 1] if '--tag' in argv else 'probe'
    res = int(argv[argv.index('--res') + 1]) if '--res' in argv else 480
    run_probe(glb, outdir, tag, render='--no-render' not in argv, posed='--no-posed' not in argv, res=res)
    # exit 0: the verdict is in the json and the BMK lines (a non-zero exit means the probe itself crashed)


if __name__ == '__main__':
    main()
