"""rig_robust.py - rig.py (untouched) + robust leg detection + body-plan gate.

    python rig_robust.py <name> <src_pattern with %s> <here_dir> [--classify-only]

Adds on top of rig.py / lowvram/tests/rigrun.py:
  * leak-proof voxel fill (same as rigrun.py).
  * legs from FOOT CONTACTS, not from the 0.04-0.12 slab: connected blobs of the lowest 3 cm of the
    solid (projected to x/z) are the feet; a merged foot pair is split with 2-means. Slab voxels are then
    assigned to the nearest foot (x/z) and anything farther than LEG_R from every foot (a low tail touching
    the hind legs, belly drape) is dropped. Fixes "expected 4 leg blobs, got 3".
  * body-plan gate: rig.py's skeleton is the wolf quadruped spec. If the contacts are not a 2x2 quadruped
    stance (biped / kangaroo, perched bird, legless shark / fish, frog crouch on 2 blobs), we do NOT emit a
    wrong rig: write <here>/out/<name>_rigskip.json with the reason and exit 3 (run_inbox reports "rig
    skipped: <plan>").
"""
import sys, os, json, types
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, trimesh, rig
from scipy import ndimage

CONTACT_H = 0.03     # foot-contact layer height (model height = 1)
LEG_R = 0.09         # slab voxel must be within this x/z distance of a foot centre
MIN_FOOT = 8         # voxels; smaller contact blobs are noise
ST = {}


class NotQuadruped(Exception):
    pass


def voxelize(V, T):  # == rigrun.py
    vg = trimesh.Trimesh(V, T, process=False).voxelized(rig.P); shell = vg.matrix.copy()
    solid = ndimage.binary_fill_holes(shell)
    if solid.sum() < 2 * shell.sum():
        solid = ndimage.binary_fill_holes(ndimage.binary_closing(shell, iterations=2)) | shell
        print('voxelize: shell leaked -> closed gaps', flush=True)
    org = vg.transform[:3, 3]
    ST.update(solid=solid, org=org)
    return solid, org


def kmeans2(X, it=30):
    a = np.argsort(X[:, 0] if np.ptp(X[:, 0]) > np.ptp(X[:, 1]) else X[:, 1])
    c = np.array([X[a[: len(a) // 2]].mean(0), X[a[len(a) // 2:]].mean(0)])
    for _ in range(it):
        l = np.argmin(((X[:, None] - c[None]) ** 2).sum(-1), 1)
        c = np.array([X[l == k].mean(0) if (l == k).any() else c[k] for k in range(2)])
    return l


def feet(solid, org):
    """foot centres (x, z) from the lowest CONTACT_H of the solid; raises NotQuadruped."""
    P = rig.P
    idx = np.argwhere(solid); C = org + idx * P
    ymin = C[:, 1].min(); Lz = np.ptp(C[:, 2])
    low = C[:, 1] < ymin + CONTACT_H
    proj = np.zeros((solid.shape[0], solid.shape[2]), bool); proj[idx[low, 0], idx[low, 2]] = True
    lab, n = ndimage.label(proj)
    blobs = []
    for i in range(1, n + 1):
        xs, zs = np.nonzero(lab == i)
        if len(xs) >= MIN_FOOT: blobs.append(np.c_[org[0] + xs * P, org[2] + zs * P])
    blobs.sort(key=len, reverse=True)
    info = dict(contacts=len(blobs), sizes=[len(b) for b in blobs])
    # split merged pairs: while < 4, 2-means the most elongated big blob
    tries = 0
    while 2 <= len(blobs) < 4 and tries < 2:
        k = max(range(len(blobs)), key=lambda i: np.ptp(blobs[i], 0).max() * len(blobs[i]) ** 0.5)
        l = kmeans2(blobs[k]); b = blobs.pop(k)
        blobs += [b[l == 0], b[l == 1]]; tries += 1
        info['split'] = info.get('split', 0) + 1
    blobs = sorted(blobs, key=len, reverse=True)[:4]
    if len(blobs) < 4:
        raise NotQuadruped(dict(info, plan='no-leg' if len(blobs) == 0 else 'biped/other', why=f'{len(blobs)} foot contacts'))
    cen = np.array([b.mean(0) for b in blobs])
    o = np.argsort(cen[:, 1]); back, front = cen[o[:2]], cen[o[2:]]
    gap = front[:, 1].mean() - back[:, 1].mean()
    dz = max(abs(np.diff(back[:, 1]))[0], abs(np.diff(front[:, 1]))[0])
    dx = min(abs(np.diff(back[:, 0]))[0], abs(np.diff(front[:, 0]))[0])
    info.update(gap=round(gap / Lz, 3), pair_dz=round(dz / Lz, 3), pair_dx=round(float(dx), 3))
    # 2x2 stance: pairs well separated along the body, each pair side-by-side (not front/back of one foot)
    if gap < 0.25 * Lz or dz > 0.6 * gap or dx < 0.02:
        raise NotQuadruped(dict(info, plan='biped/other', why='contacts are not a 2x2 quadruped stance'))
    sz = [len(b) for b in blobs]
    if min(sz) < 0.15 * max(sz):
        raise NotQuadruped(dict(info, plan='biped/other', why='one contact much smaller than the others (tail/ tip, not a foot)'))
    print('feet', info, flush=True)
    return cen


def label(mask, *a, **k):
    """replacement for ndimage.label on rig.py's leg slab: one label per foot, tail voxels dropped."""
    cen = feet(ST['solid'], ST['org'])
    P = rig.P; org = ST['org']
    idx = np.argwhere(mask)
    xz = np.c_[org[0] + idx[:, 0] * P, org[2] + idx[:, 2] * P]
    d = np.linalg.norm(xz[:, None] - cen[None], axis=-1)
    near = np.argmin(d, 1); ok = d[np.arange(len(d)), near] < LEG_R
    out = np.zeros(mask.shape, np.int32)
    out[tuple(idx[ok].T)] = near[ok] + 1
    print(f'legs: {ok.sum()} slab voxels on 4 feet, {(~ok).sum()} dropped (tail/body)', flush=True)
    return out, 4


def classify(src):
    V0, F = rig.load_obj(src); T = rig.tris_of(F); V, _ = rig.orient(V0, T)
    s, o = voxelize(V, T); return feet(s, o)


if __name__ == '__main__':
    name, src, here = sys.argv[1:4]
    rig.SRC = src; rig.HERE = here; rig.voxelize = voxelize
    nd = types.ModuleType('ndimage_shim'); nd.__dict__.update(ndimage.__dict__); nd.label = label
    rig.ndimage = nd
    try:
        if '--classify-only' in sys.argv: classify(src % name if '%s' in src else src); print('plan: quadruped'); sys.exit(0)
        rig.main(name)
    except NotQuadruped as e:
        r = dict(e.args[0], name=name, rigged=False,
                 note='rig.py skeleton is the wolf quadruped spec; non-quadruped body plans are skipped, not mis-rigged')
        os.makedirs(os.path.join(here, 'out'), exist_ok=True)
        json.dump(r, open(os.path.join(here, 'out', name + '_rigskip.json'), 'w'), indent=1)
        print('RIGSKIP', json.dumps(r), flush=True); sys.exit(3)
