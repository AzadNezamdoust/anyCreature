"""Model side/front silhouette (stage1/ortho_*.png) vs the sheet's own pixels (reference/*.png): red = model only,
blue = sheet only, grey = both. Prints the IoU against the sheet pixels (finer than the 43-point trace).
    py -3.11 tools/sidediff.py <out.png>"""
import json, os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 0.000856
o = json.load(open(os.path.join(HERE, 'stage1', 'ortho.json')))
fr, res = o['frame'], o['res']
ow = fr['ortho']
out = []
for name, origin, cmid in (('side', (-11, -20), 317), ('front', (591, -23), 929)):
    m = np.array(Image.open(os.path.join(HERE, 'stage1', f'ortho_{name}.png')).convert('L')) > 84
    ref = np.array(Image.open(os.path.join(HERE, 'reference', f'{name}.png')).convert('RGB')).astype(float)
    rm = (np.abs(ref - 254).max(2) > 40) | (ref.max(2) - ref.min(2) > 32)
    H = m.shape[0]
    rr, cc = np.mgrid[0:H, 0:H]
    a = (cc + 0.5) / res - 0.5
    u = (fr['centre'][1] if name == 'side' else 0.0) + a * ow
    z = fr['centre'][2] + (0.5 - (rr + 0.5) / res) * ow
    col = np.round(u / S + cmid - origin[0]).astype(int)
    row = np.round(600 - z / S - origin[1]).astype(int) if name == 'side' else np.round(616 - z / S - origin[1]).astype(int)
    ok = (col >= 0) & (col < rm.shape[1]) & (row >= 0) & (row < rm.shape[0])
    sm = np.zeros_like(m)
    sm[ok] = rm[row[ok], col[ok]]
    img = np.full(m.shape + (3,), 250, np.uint8)
    img[m & sm] = (150, 150, 150); img[m & ~sm] = (230, 40, 40); img[~m & sm] = (40, 80, 230)
    out.append(img)
    print(name, 'IoU vs sheet pixels %.3f' % ((m & sm).sum() / (m | sm).sum()))
Image.fromarray(np.concatenate(out, 1)).save(sys.argv[1])
