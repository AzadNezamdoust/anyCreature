"""meas.py <stage_dir> : half-width (front) and front/back y (side) of the model and of the sheet trace per height."""
import sys, os, json
import numpy as np
from PIL import Image
here = os.path.dirname(os.path.abspath(__file__))
sd = os.path.join(here, sys.argv[1] if len(sys.argv) > 1 else 'stage1')
oj = json.load(open(os.path.join(sd, 'ortho.json')))
fr = oj['frame']; res = oj['res']; mpp = fr['ortho'] / res
def mask(v):
    mo = np.asarray(Image.open(os.path.join(sd, oj['files'][v])).convert('RGB')).astype(int)
    return np.abs(mo - mo[2, 2]).sum(2) > 30
F, S = mask('front'), mask('side')
for z in [0.1, 0.3, 0.45, 0.6, 0.75, 0.9, 1.05, 1.2, 1.35, 1.5, 1.6, 1.7, 1.8, 1.9]:
    r = int(round((fr['centre'][2] - z) / mpp + res / 2))
    cols = np.where(F[r])[0]
    xs = (cols - res / 2) * mpp + fr['centre'][0]
    runs = []
    if len(cols):
        st = cols[0]; pv = cols[0]
        for c in cols[1:]:
            if c != pv + 1:
                runs.append((st, pv)); st = c
            pv = c
        runs.append((st, pv))
    fr_ = ' '.join(f'[{(a - res / 2) * mpp:+.2f},{(b - res / 2) * mpp:+.2f}]' for a, b in runs if (b - res / 2) * mpp > 0)
    sc = np.where(S[r])[0]
    ys = (sc - res / 2) * mpp + fr['centre'][1]
    print(f'z {z:.2f}  front {fr_:40s} side y {ys.min() if len(ys) else 0:+.2f}..{ys.max() if len(ys) else 0:+.2f}')
