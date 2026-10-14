"""Shared helpers for the low-poly lab: load, normalize (y-up, ground y=0,
height 1), write polygon OBJ (keeps quads), stats."""
import numpy as np

ANIMALS = ['wolf', 'horse', 'elephant', 'giraffe', 'crocodile', 'eagle',
           'shark', 'frog', 'tortoise', 'kangaroo']
BUDGETS = [1500, 5000]


def load_tri(path):
    import trimesh
    m = trimesh.load(path, force='mesh', process=True)
    m.remove_unreferenced_vertices()
    return m


def normalize(V):
    """Inputs are already y-up; recentre xz, ground y=0, height 1."""
    V = np.asarray(V, float).copy()
    lo, hi = V.min(0), V.max(0)
    V[:, 0] -= (lo[0] + hi[0]) / 2
    V[:, 2] -= (lo[2] + hi[2]) / 2
    V[:, 1] -= lo[1]
    V /= max(hi[1] - lo[1], 1e-9)
    return V


def read_obj_polys(path):
    V, P = [], []
    for line in open(path, encoding='utf-8', errors='ignore'):
        p = line.split()
        if not p:
            continue
        if p[0] == 'v':
            V.append([float(x) for x in p[1:4]])
        elif p[0] == 'f':
            P.append([int(t.split('/')[0]) - 1 for t in p[1:]])
    V = np.array(V)
    P = [[i if i >= 0 else len(V) + i + 1 for i in f] for f in P]
    return V, P


def write_obj_polys(path, V, P):
    with open(path, 'w') as f:
        for v in V:
            f.write('v %.6f %.6f %.6f\n' % tuple(v))
        for p in P:
            f.write('f ' + ' '.join(str(i + 1) for i in p) + '\n')


def stats(P):
    n = len(P)
    q = sum(1 for p in P if len(p) == 4)
    t = sum(1 for p in P if len(p) == 3)
    return dict(faces=n, quads=q, tris=t, quad_pct=100.0 * q / max(n, 1),
                tri_equiv=sum(len(p) - 2 for p in P))
