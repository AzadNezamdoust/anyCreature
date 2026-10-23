"""ov.py <stage_dir> : the model's ortho silhouette (red outline) over reference/front.png and side.png at the sheet's
scale (refs.json crops, 0.004202 m/px), so mass and proportion read against the concept, not only the IoU."""
import sys, os, json
import numpy as np
from PIL import Image, ImageFilter
here = os.path.dirname(os.path.abspath(__file__))
sd = os.path.join(here, sys.argv[1] if len(sys.argv) > 1 else 'stage1')
oj = json.load(open(os.path.join(sd, 'ortho.json')))
fr = oj['frame']; res = oj['res']; mpp = fr['ortho'] / res
MR = 0.004202
REF = {'front': ('front.png', 312.0, 546.0, 'x'), 'side': ('side.png', 267.5, 505.0, 'y')}
outs = []
for v, (fn, c0, r0, ax) in REF.items():
    ref = Image.open(os.path.join(here, 'reference', fn)).convert('RGB')
    W, H = ref.size
    mo = np.asarray(Image.open(os.path.join(sd, oj['files'][v])).convert('RGB')).astype(int)
    bg = mo[2, 2]
    mask = (np.abs(mo - bg).sum(2) > 30)
    # model pixel (col, row) -> world (u, z): u = (col - res/2) * mpp + cu, z = cz - (row - res/2) * mpp
    cu = fr['centre'][0] if ax == 'x' else fr['centre'][1]
    cz = fr['centre'][2]
    jj, ii = np.meshgrid(np.arange(W), np.arange(H))
    u = (jj - c0) * MR
    z = (r0 - ii) * MR
    mc = np.round((u - cu) / mpp + res / 2).astype(int)
    mr = np.round((cz - z) / mpp + res / 2).astype(int)
    ok = (mc >= 0) & (mc < res) & (mr >= 0) & (mr < res)
    m2 = np.zeros((H, W), bool)
    m2[ok] = mask[mr[ok], mc[ok]]
    mi = Image.fromarray((m2 * 255).astype(np.uint8))
    edge = np.asarray(mi.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(3))) > 0
    a = np.asarray(ref).copy()
    a[m2] = (a[m2] * 0.75 + np.array([60, 90, 200]) * 0.25).astype(np.uint8)
    a[edge] = (230, 20, 20)
    outs.append(Image.fromarray(a))
S = Image.new('RGB', (sum(o.size[0] for o in outs), max(o.size[1] for o in outs)), 'white')
x = 0
for o in outs:
    S.paste(o, (x, 0)); x += o.size[0]
p = os.path.join(sd, 'ov_front_side.jpg')
S.save(p, quality=90)
print(p)
