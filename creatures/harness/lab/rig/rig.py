"""RIG stage prototype: auto-fit an anyCreature-convention quadruped skeleton inside a
quad low-poly mesh, compute voxel-geodesic skin weights, emit an engine build JSON that
export_glb.js turns into a skinned+animated GLB with the engine's own writer/animations.

    python rig.py <name>     (reads E:/gen3d/lowpoly/quadriflow/<name>_5000.obj)

Frame: engine convention (x side, y up, +z = head/forward), ground y=0, height 1.
"""
import sys, json, os
import numpy as np, trimesh
from scipy import ndimage, sparse
from scipy.sparse.csgraph import dijkstra

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = 'E:/gen3d/lowpoly/quadriflow/%s_5000.obj'
WOLF = 'E:/Github/anyCreature/example/wolf.json'
P = 0.01  # voxel pitch


def load_obj(path):
    V, F = [], []
    for line in open(path):
        p = line.split()
        if not p: continue
        if p[0] == 'v': V.append([float(x) for x in p[1:4]])
        elif p[0] == 'f':
            F.append([int(q.split('/')[0]) - 1 for q in p[1:]])
    return np.array(V), F


def tris_of(F):
    return np.array([[f[0], f[k], f[k + 1]] for f in F for k in range(1, len(f) - 1)])


def winding(Q, V, T):
    """generalized winding number (robust inside test, works on non-watertight)."""
    out = []
    A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    for q in Q:
        a, b, c = A - q, B - q, C - q
        la, lb, lc = [np.linalg.norm(x, axis=1) for x in (a, b, c)]
        det = np.einsum('ij,ij->i', a, np.cross(b, c))
        den = la * lb * lc + np.einsum('ij,ij->i', a, b) * lc + np.einsum('ij,ij->i', b, c) * la \
            + np.einsum('ij,ij->i', c, a) * lb
        out.append(np.arctan2(det, den).sum() / (2 * np.pi))
    return np.array(out)


def orient(V, T):
    """long axis x -> engine +z with head forward. Head end = end whose top is higher."""
    x = V[:, 0]; lo, hi = x.min(), x.max(); L = hi - lo
    top_hi = V[x > hi - 0.15 * L, 1].max(); top_lo = V[x < lo + 0.15 * L, 1].max()
    s = 1.0 if top_hi > top_lo else -1.0
    R = np.array([[0, 0, -s], [0, 1, 0], [s, 0, 0]], float)  # x->s z, z->-s x
    W = V @ R.T
    W[:, 0] -= (W[:, 0].max() + W[:, 0].min()) / 2
    return W, s


def voxelize(V, T):
    m = trimesh.Trimesh(V, T, process=False)
    vg = m.voxelized(P)
    shell = vg.matrix.copy()
    solid = ndimage.binary_fill_holes(shell)
    origin = vg.transform[:3, 3]
    return solid, origin


def main(name):
    V0, F = load_obj(SRC % name)
    T = tris_of(F)
    V, s = orient(V0, T)
    solid, org = voxelize(V, T)
    idx = np.argwhere(solid)
    C = org + idx * P                                  # voxel centres
    edt = ndimage.distance_transform_edt(solid) * P
    lin = -np.ones(solid.shape, int); lin[tuple(idx.T)] = np.arange(len(idx))
    D = edt[tuple(idx.T)]
    # 26-neighbour graph, medial-preferring cost
    rows, cols, w = [], [], []
    for d in np.argwhere(np.ones((3, 3, 3))) - 1:
        if (d == 0).all() or tuple(d) < (0, 0, 0): continue
        n = idx + d
        ok = (n >= 0).all(1) & (n < solid.shape).all(1)
        j = np.full(len(idx), -1); j[ok] = lin[tuple(n[ok].T)]
        k = j >= 0
        L = np.linalg.norm(d) * P
        rows.append(np.nonzero(k)[0]); cols.append(j[k]); w.append(np.full(k.sum(), L))
    rows, cols, w = map(np.concatenate, (rows, cols, w))
    Gd = sparse.coo_matrix((w, (rows, cols)), shape=(len(idx),) * 2).tocsr()   # geodesic
    med = w * (1.0 / (0.5 * (D[rows] + D[cols]) + 0.004)) ** 2
    Gm = sparse.coo_matrix((med, (rows, cols)), shape=(len(idx),) * 2).tocsr()  # medial path

    def path(a, b):
        _, pred = dijkstra(Gm, directed=False, indices=a, return_predecessors=True)
        p = [b]
        while p[-1] != a: p.append(pred[p[-1]])
        return C[p[::-1]]          # a -> b

    def nearest(pt):
        return int(np.argmin(np.linalg.norm(C - pt, axis=1)))

    def at_y(pth, y):   # first point along path (from start) reaching height y
        i = np.argmax(pth[:, 1] >= y) if (pth[:, 1] >= y).any() else len(pth) - 1
        return pth[i]

    def by_arc(pth, f):
        seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pth, axis=0), axis=1))]
        return pth[np.argmin(abs(seg - f * seg[-1]))]

    zmin, zmax = C[:, 2].min(), C[:, 2].max(); Lz = zmax - zmin
    # ---- legs: connected blobs in a low slab
    slab = (C[:, 1] < 0.12) & (C[:, 1] > 0.04)
    lab, n = ndimage.label(solid & (np.arange(solid.shape[1])[None, :, None] * P + org[1] < 0.12)
                           & (np.arange(solid.shape[1])[None, :, None] * P + org[1] > 0.04))
    comp = lab[tuple(idx.T)]
    sizes = [(comp == i).sum() for i in range(1, n + 1)]
    legs = [i + 1 for i in np.argsort(sizes)[::-1][:4]]
    assert n >= 4, 'expected 4 leg blobs, got %d' % n
    cent = {l: C[comp == l].mean(0) for l in legs}
    zs = sorted(legs, key=lambda l: cent[l][2])
    back, front = zs[:2], zs[2:]
    leg_ids = {}
    for tag, pair in (('Back', back), ('Front', front)):
        a, b = sorted(pair, key=lambda l: cent[l][0])
        leg_ids['R' + tag], leg_ids['L' + tag] = a, b        # L = +x (engine mirror flips x)
    # belly height: lowest torso point between front/back legs
    zb, zf = np.mean([cent[l][2] for l in back]), np.mean([cent[l][2] for l in front])
    mid = (abs(C[:, 0]) < 0.05) & (C[:, 2] > zb + 0.25 * (zf - zb)) & (C[:, 2] < zf - 0.25 * (zf - zb))
    belly = C[mid, 1].min(); backtop = C[mid, 1].max()

    def torso_centre(z):
        m = (abs(C[:, 2] - z) < P * 0.6) & (C[:, 1] > belly)
        k = np.argmax(D * m)
        return C[k]
    hips = torso_centre(zb); chest = torso_centre(zf)
    # ---- extremities
    nose_i = int(np.argmax(C[:, 2])); tail_i = int(np.argmin(C[:, 2]))
    head_path = path(nearest(chest), nose_i)
    tail_path = path(nearest(hips), tail_i)
    spine_path = path(nearest(hips), nearest(chest))
    J = {}
    J['Hips'] = hips; J['Chest'] = chest
    J['Spine'] = by_arc(spine_path, 0.5)
    J['Rump'] = by_arc(tail_path, 0.0) + [0, 0, 0]
    rz = hips[2] - 0.5 * (hips[2] - zmin) * 0.25
    J['Rump'] = torso_centre(min(hips[2] - 0.06, max(rz, zmin + 0.05)))
    # neck/head: along chest->nose medial path. head starts where cross-section narrows
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(head_path, axis=0), axis=1))]
    Dp = np.array([D[nearest(p)] for p in head_path])
    for nm, f in (('NeckB', 0.22), ('Neck2', 0.45), ('HeadRoot', 0.6), ('Skull', 0.7),
                  ('Brow', 0.8), ('Muzzle', 0.9), ('Nose', 0.97)):
        J[nm] = by_arc(head_path, f)
    # tail chain
    for nm, f in (('TailRoot', 0.18), ('Tail1', 0.4), ('Tail2', 0.68), ('TailTip', 0.93)):
        J[nm] = by_arc(tail_path, f)
    # legs: paw (lowest/foremost voxel of blob column) -> torso centre
    for side in 'LR':
        for tag, host in (('Front', chest), ('Back', hips)):
            l = leg_ids[side + tag]
            foot = (C[:, 1] < 0.06) & (np.abs(C[:, 0] - cent[l][0]) < 0.06) & (np.abs(C[:, 2] - cent[l][2]) < 0.12)
            fk = np.nonzero(foot)[0]
            toe = fk[np.argmax(C[fk, 2] + 0.5 * D[fk])]
            heel = fk[np.argmax(D[fk])]
            hp = host.copy(); hp[0] = cent[l][0] * 0.8
            pth = path(heel, nearest(hp))
            hb = belly
            if tag == 'Front':
                J[side + 'FrontToe'] = C[toe]
                J[side + 'FrontWrist'] = at_y(pth, 0.38 * hb)
                J[side + 'FrontElbow'] = at_y(pth, 0.92 * hb)
                J[side + 'FrontRoot'] = at_y(pth, hb + 0.45 * (backtop - hb))
            else:
                J[side + 'BackToe'] = C[toe]
                J[side + 'BackHock'] = at_y(pth, 0.42 * hb)
                J[side + 'BackKnee'] = at_y(pth, 0.95 * hb)
                J[side + 'BackRoot'] = at_y(pth, hb + 0.45 * (backtop - hb))
    # ears: highest voxels on each side in the head zone
    hz = J['Neck2'][2]
    for side, sg in (('L', 1), ('R', -1)):
        m = (C[:, 2] > hz - 0.05) & (sg * C[:, 0] > 0.005)
        tip = np.nonzero(m)[0][np.argmax(C[m, 1])]
        J[side + 'Ear'] = by_arc(path(nearest(J['Skull']), tip), 0.55)
    # jaw hinge: below/behind skull, on the lower half of the head section
    jz = J['HeadRoot'][2]
    m = (abs(C[:, 2] - J['Skull'][2]) < 0.6 * P + 0.01) & (abs(C[:, 0]) < 0.03) & (C[:, 1] < J['Skull'][1])
    J['Jaw'] = C[np.nonzero(m)[0][np.argmax(D[m] - 0.3 * abs(C[m, 1] - (J['Skull'][1] - 0.6 * D[nearest(J['Skull'])])))]] \
        if m.any() else J['Skull'] - [0, 0.02, 0]
    # any joint whose voxel sits on the shell (non-watertight input) -> nearest deep voxel
    deep = np.nonzero(D >= 2.5 * P)[0]
    wn0 = winding(np.array(list(J.values())), V, T)
    for (k0, p0), w0 in zip(list(J.items()), wn0):
        if w0 < 0.5:
            J[k0] = C[deep[np.argmin(np.linalg.norm(C[deep] - p0, axis=1))]]
    names = list(J)
    Jp = np.array([J[k] for k in names])
    wn = winding(Jp, V, T)
    inside = {k: float(round(w, 3)) for k, w in zip(names, wn)}
    bad = [k for k, w in inside.items() if w < 0.5]
    print(name, 'head sign', s, 'belly %.3f back %.3f' % (belly, backtop), 'joints outside:', bad)

    # ---- spec in engine conventions (wolf names, chains, attach, mirror, anims)
    wolf = json.load(open(WOLF))
    k = 1.0 / wolf['height']
    anims = json.loads(json.dumps(wolf['animations']))
    for a in anims.values():
        a['tracks'].pop('Rump', None)  # wolf-specific ground correction offset
        for tr in a['tracks'].values():
            for ax in ('tx', 'ty', 'tz'):
                if ax in tr: tr[ax] = [[t, v * k] for t, v in tr[ax]]
    # jaw + ears in idle, so every new bone moves at least once
    anims['idle']['tracks']['Jaw'] = {'rx': [[0, 0], [0.4, 0], [0.55, 12], [0.7, 0], [1, 0]]}
    anims['idle']['tracks']['LEar'] = {'rz': [[0, 0], [0.3, 8], [0.4, 0], [1, 0]]}
    anims['idle']['tracks']['REar'] = {'rz': [[0, 0], [0.6, -8], [0.7, 0], [1, 0]]}
    anims['walk'] = anims.pop('move')
    chains = {k2: v for k2, v in wolf['chains'].items()}
    joints = {n: [round(float(c), 5) for c in J[n]] for n in names if not (n[0]=='R' and n[1].isupper())}
    joints_R = {n: [round(float(c), 5) for c in J[n]] for n in names if n[0]=='R' and n[1].isupper()}
    spec = {'name': name, 'height': 1.0, 'joints': joints, 'joints_R': joints_R, 'chains': chains,
            'attach': dict(wolf['attach'], LEar='Skull', Jaw='Skull'), 'mirror': wolf['mirror'],
            'animations': anims}

    # ---- skin weights: voxel-geodesic distance to each bone segment
    order = ['Rump', 'Hips', 'Spine', 'Chest', 'NeckB', 'Neck2', 'HeadRoot', 'Skull', 'Brow', 'Muzzle', 'Nose',
             'TailRoot', 'Tail1', 'Tail2', 'TailTip']
    parent = {}
    for ch, js in chains.items():
        for a, b in zip(js, js[1:]): parent[b] = a
    for ch, host in wolf['attach'].items():
        parent[chains[ch][0]] = host
    for side in 'R':
        for ch in ('LFront', 'LBack'):
            js = chains[ch]
            parent['R' + js[0][1:]] = parent[js[0]]
            for a, b in zip(js, js[1:]): parent['R' + b[1:]] = 'R' + a[1:]
    parent.update(LEar='Skull', REar='Skull', Jaw='Skull')
    parent.pop('Rump', None); parent['Hips'] = 'Rump'
    children = {n: [c for c, p in parent.items() if p == n] for n in names}
    # bone segments owned by joint n: n->each child (excluding side branches for torso/head joints)
    branchy = {'Hips', 'Chest', 'Skull'}
    seg_of = {}
    for n in names:
        ch = [c for c in children[n] if not (n in branchy and (c[0] in 'LR' or c == 'Jaw'))]
        if n == 'Hips': ch = ['Spine']
        if n == 'Rump': ch = []
        if n == 'Skull': ch = ['Brow']
        seg_of[n] = [(J[n], J[c]) for c in ch] or [(J[n], J[n])]
    seg_of['Rump'] = [(J['Rump'], J['Hips'])]
    # Jaw owns hinge->Nose-bottom segment; ears own base->tip
    def seeds(segs):
        out = set()
        for a, b in segs:
            for t in np.linspace(0, 1, 12):
                p = a + t * (b - a)
                out.add(nearest(p))
        return list(out)
    vox_of_vert = np.array([nearest(v) for v in V])
    # snap verts to nearest interior voxel
    dist = np.zeros((len(names), len(V)))
    for i, n in enumerate(names):
        segs = seg_of[n]
        if n == 'Jaw':
            segs = [(J['Jaw'], J['Nose'] - [0, 0.6 * D[nearest(J['Nose'])], 0])]
        d = dijkstra(Gd, directed=False, indices=seeds(segs), min_only=True)
        dist[i] = d[vox_of_vert] + np.linalg.norm(V - C[vox_of_vert], axis=1)
    dist = np.maximum(dist, 1e-4)
    # jaw: only lower-snout verts may use it (cheap mouth-line split)
    ji = names.index('Jaw')
    mouth_y = J['Muzzle'][1] - 0.15 * D[nearest(J['Muzzle'])]
    lower = (V[:, 2] > J['Jaw'][2]) & (V[:, 1] < mouth_y)
    dist[ji, ~lower] = np.inf
    W = 1.0 / dist ** 4
    # smooth across the mesh 1-ring (kills single-vertex spikes), then top-4 normalise
    E = np.array([(f[i], f[(i + 1) % len(f)]) for f in F for i in range(len(f))])
    A = sparse.coo_matrix((np.ones(len(E)), (E[:, 0], E[:, 1])), shape=(len(V),) * 2)
    A = ((A + A.T) > 0).astype(float)
    A = sparse.diags(1 / np.asarray(A.sum(1)).ravel()) @ A
    W = W / W.sum(0)
    for _ in range(3): W = 0.5 * W + 0.5 * (A @ W.T).T
    top = np.argsort(-W, axis=0)[:4]
    skin = []
    for vi in range(len(V)):
        ws = W[top[:, vi], vi]; ws = ws / ws.sum()
        skin.append([[names[j], round(float(w), 5)] for j, w in zip(top[:, vi], ws) if w > 1e-4])
    build = {'spec': spec, 'V': V.round(6).tolist(), 'F': F, 'skin': skin,
             'inside_winding': inside}
    os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
    json.dump(build, open(os.path.join(HERE, 'out', name + '_build.json'), 'w'))
    # debug: skeleton obj (joint octahedra) for overlay renders
    return inside


if __name__ == '__main__':
    for nm in sys.argv[1:]: main(nm)
