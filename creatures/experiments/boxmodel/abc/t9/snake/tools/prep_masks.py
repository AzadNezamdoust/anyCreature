"""Unsymmetrised sheet masks (kit coords) + plan-view centreline for the t9 snake. Plain python.
Writes reference/side_mask.npz, top_mask.npz, front_mask.npz, plan_centre.json, tools/plan_centre.png"""
import json, os, numpy as np
from PIL import Image, ImageDraw
from skimage.morphology import skeletonize
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
im = np.asarray(Image.open(os.path.join(HERE, 'reference', 'sheet.png')).convert('RGB')).astype(float)
m = np.abs(im - 253).max(axis=2) > 40
S = 0.001538
# side: y = (col - 417.5) S, z = (465 - row) S
r0, r1, c0, c1 = 130, 481, 24, 812
side = ndi.binary_fill_holes(m[r0:r1, c0:c1])
np.savez_compressed(os.path.join(HERE, 'reference', 'side_mask.npz'), mask=side, y0=(c0 - 417.5) * S, z0=(465 - r0) * S, px=S)
# top: x = (row - 715) S, y = (col - 824) S - 0.542   (rows down = +x, the left flank)
r0, r1, c0, c1 = 524, 915, 771, 1493
top = ndi.binary_fill_holes(m[r0:r1, c0:c1])
lab, n = ndi.label(top); big = np.argmax(np.bincount(lab.ravel())[1:]) + 1; top = lab == big
np.savez_compressed(os.path.join(HERE, 'reference', 'top_mask.npz'), mask=top, x0=(r0 - 715) * S, y0=(c0 - 824) * S - 0.542, px=S)
# front: x = (col - 1138) S, z = (470 - row) S
r0, r1, c0, c1 = 130, 481, 894, 1471
fr = ndi.binary_fill_holes(m[r0:r1, c0:c1])
np.savez_compressed(os.path.join(HERE, 'reference', 'front_mask.npz'), mask=fr, x0=(c0 - 1138) * S, z0=(470 - r0) * S, px=S)
# plan centreline: skeleton of the top mask (tongue cut off), longest path
t2 = top.copy(); t2[:, :824 - 771] = False
sk = skeletonize(ndi.binary_opening(t2, iterations=3))
pts = set(zip(*np.nonzero(sk)))
nb = lambda p: [(p[0] + a, p[1] + b) for a in (-1, 0, 1) for b in (-1, 0, 1) if (a or b) and (p[0] + a, p[1] + b) in pts]
def far(src):
    from collections import deque
    D = {src: 0}; P = {src: None}; q = deque([src])
    while q:
        u = q.popleft()
        for v in nb(u):
            if v not in D: D[v] = D[u] + 1; P[v] = u; q.append(v)
    e = max(D, key=D.get); path = []
    while e is not None: path.append(e); e = P[e]
    return path
a = far(next(iter(pts)))[0]; path = far(a)[::-1]
path = [(int(r) + 524, int(c) + 771) for r, c in path]
if path[0][1] > path[-1][1]: path = path[::-1]          # head (left) first
dt = ndi.distance_transform_edt(top)
w = [2 * dt[r - 524, c - 771] * S for r, c in path]
xy = [((r - 715) * S, (c - 824) * S - 0.542) for r, c in path]
json.dump(dict(px=path[::4], xy=[[round(x, 4), round(y, 4)] for x, y in xy[::4]], width=[round(v, 4) for v in w[::4]]),
          open(os.path.join(HERE, 'reference', 'plan_centre.json'), 'w'))
img = Image.open(os.path.join(HERE, 'reference', 'sheet.png')).convert('RGB').crop((771, 524, 1493, 915))
d = ImageDraw.Draw(img)
for i, (r, c) in enumerate(path[::4]):
    d.ellipse((c - 771 - 2, r - 524 - 2, c - 771 + 2, r - 524 + 2), fill=(255, 0, 0))
    if i % 10 == 0: d.text((c - 771 + 4, r - 524), str(i), fill=(0, 0, 255))
img.save(os.path.join(HERE, 'tools', 'plan_centre.png'))
L = sum(np.hypot(xy[i + 1][0] - xy[i][0], xy[i + 1][1] - xy[i][1]) for i in range(len(xy) - 1))
print('skeleton path', len(path), 'length m', round(L, 3), 'start', path[0], 'end', path[-1])
print('widths p50 %.3f max %.3f' % (np.median(w), max(w)))
for i in range(0, len(path), 40): print(i, path[i], xy[i], round(w[i], 3))
