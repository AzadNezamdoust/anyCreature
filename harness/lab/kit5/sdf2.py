"""mesh utilities for kit.py: clean, taubin smoothing, vertex-clustering decimation"""
import numpy as np
import scipy.sparse as sp


def clean(V, F):
    F = F[(F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 0] != F[:, 2])]
    used = np.unique(F)
    remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))
    return V[used], remap[F]


def _lap(V, F):
    n = len(V)
    i = np.concatenate([F[:, 0], F[:, 1], F[:, 2], F[:, 1], F[:, 2], F[:, 0]])
    j = np.concatenate([F[:, 1], F[:, 2], F[:, 0], F[:, 0], F[:, 1], F[:, 2]])
    A = sp.coo_matrix((np.ones(len(i)), (i, j)), shape=(n, n)).tocsr()
    A.data[:] = 1.0
    d = np.asarray(A.sum(1)).ravel(); d[d == 0] = 1
    return sp.diags(1 / d) @ A


def taubin(V, F, it=10, lam=0.5, mu=-0.53):
    W = _lap(V, F); V = V.copy()
    for _ in range(it):
        V = V + lam * (W @ V - V)
        V = V + mu * (W @ V - V)
    return V


def _cluster(V, F, h):
    key = np.floor((V - V.min(0)) / h).astype(np.int64)
    k = key[:, 0] * 1000003 * 1009 + key[:, 1] * 1000003 + key[:, 2]
    u, inv = np.unique(k, return_inverse=True)
    inv = inv.ravel()
    cnt = np.bincount(inv)
    Vn = np.stack([np.bincount(inv, V[:, a]) / cnt for a in range(3)], 1)
    Fn = inv[F]
    Fn = Fn[(Fn[:, 0] != Fn[:, 1]) & (Fn[:, 1] != Fn[:, 2]) & (Fn[:, 0] != Fn[:, 2])]
    s = np.sort(Fn, 1); _, idx = np.unique(s, axis=0, return_index=True)
    return clean(Vn, Fn[np.sort(idx)])


def decimate(V, F, target):
    e = np.linalg.norm(V[F[:, 0]] - V[F[:, 1]], axis=1).mean()
    lo, hi = e * 0.5, e * 8
    best = None
    for _ in range(14):
        h = (lo + hi) / 2
        Vn, Fn = _cluster(V, F, h)
        if len(Fn) > target: lo = h
        else:
            hi = h; best = (Vn, Fn)
    return best if best is not None else _cluster(V, F, hi)
