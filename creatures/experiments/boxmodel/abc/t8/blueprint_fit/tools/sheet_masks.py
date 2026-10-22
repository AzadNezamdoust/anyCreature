"""Sheet silhouette masks on a fixed world grid (side y-z, front x-z, top x-y), from a refs.py 2x2 sheet.
usage: sheet_masks.py <sheet.png> <refs.json> <out.npz>   (top length rescaled to the side length: side wins y)"""
import sys, json, numpy as np
from PIL import Image
from scipy import ndimage as nd
G = 0.005
GRID = {'side': ((-1.5, 1.5), (-0.1, 1.8)), 'front': ((-0.7, 0.7), (-0.1, 1.8)), 'top': ((-0.7, 0.7), (-1.5, 1.5))}

def grid(view):
    (u0, u1), (v0, v1) = GRID[view]
    u = np.arange(u0, u1, G) + G / 2; v = np.arange(v0, v1, G) + G / 2
    return np.meshgrid(u, v)            # arrays [v, u]

def fg(sheet, box, bg):
    r0, r1, c0, c1 = box
    a = sheet[r0:r1 + 1, c0:c1 + 1]
    d = np.abs(a - bg).max(axis=2)
    m = d > 22                                   # ground shadow is a faint grey (< 22)
    m = nd.binary_closing(m, iterations=2)
    holes = nd.binary_fill_holes(m) & ~m         # fill only small holes (white feathers), not the gaps between legs
    lab, n = nd.label(holes)
    if n:
        sz = nd.sum(holes, lab, range(1, n + 1))
        m = m | np.isin(lab, [i + 1 for i, s_ in enumerate(sz) if s_ < 1500])
    m = nd.binary_opening(m, iterations=1)
    lab, n = nd.label(m)
    if n > 1:
        sz = nd.sum(m, lab, range(1, n + 1)); keep = [i + 1 for i, s in enumerate(sz) if s > 0.02 * sz.max()]
        m = np.isin(lab, keep)
    return m

def main(sheet_p, refs_p, out):
    R = json.load(open(refs_p)); S = np.asarray(Image.open(sheet_p).convert('RGB')).astype(float)
    bg = np.array(R['background_rgb']); mpp = R['metres_per_pixel']['side']
    res = {}
    for view in ('side', 'front', 'top'):
        box = R['crops'][view]['box_rows_cols']; r0, r1, c0, c1 = box
        m = fg(S, box, bg)
        U, V = grid(view)
        if view == 'side':           # col -> y (head left = -y), row -> z (bottom = 0)
            col = (U / mpp) + (c0 + c1) / 2 - c0; row = r1 - V / mpp - r0
        elif view == 'front':
            col = (U / mpp) + (c0 + c1) / 2 - c0; row = r1 - V / mpp - r0
        else:                        # original sheet: col -> y, row -> x; y scaled to the side length
            k = ((R['crops']['side']['box_rows_cols'][3] - R['crops']['side']['box_rows_cols'][2])) / (c1 - c0)
            col = (V / (mpp * k)) + (c0 + c1) / 2 - c0; row = (U / mpp) + (r0 + r1) / 2 - r0
        ci = np.round(col).astype(int); ri = np.round(row).astype(int)
        ok = (ci >= 0) & (ci < m.shape[1]) & (ri >= 0) & (ri < m.shape[0])
        g = np.zeros(U.shape, bool); g[ok] = m[ri[ok], ci[ok]]
        res[view] = g
    np.savez_compressed(out, **res)
    im = np.concatenate([np.pad(res[v], ((0, 380 - res[v].shape[0]), (0, 0)))[::-1] for v in ('side', 'front')], axis=1)
    Image.fromarray((~im * 255).astype(np.uint8)).save(out.replace('.npz', '_sf.png'))
    Image.fromarray((~res['top'][::-1] * 255).astype(np.uint8)).save(out.replace('.npz', '_top.png'))
    print({v: int(res[v].sum()) for v in res})

if __name__ == '__main__':
    main(*sys.argv[1:4])
