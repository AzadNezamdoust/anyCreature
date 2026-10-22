"""Register the official Logitech G502 HERO product shots to mm and extract outlines.

venv_cad python -I replica/L2/ref_extract.py
-> refs/L2/registered.npz (top + side masks on a 0.25 mm grid) and replica/L2/ref_profiles.json (station table).
Registration: top view length (front button tips -> rear) = 132 mm (Logitech spec); side view length = 132 mm,
side height: flat-pad line -> crest = 40 mm (spec). Cable removed by a 31 px morphological opening.
Convention: X length (front -X), Y width (left -Y), Z up, mm.
"""
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "..", "refs", "L2")
L_SPEC, W_SPEC, H_SPEC = 132.0, 75.0, 40.0
G = 0.25  # mm grid


def mask(name):
    a = np.array(Image.open(os.path.join(REF, name)).convert("RGBA"))
    m = (a[..., 3] > 128) & (a[..., :3].min(-1) < 200)
    st = np.zeros((31, 31), bool)
    yy, xx = np.mgrid[-15:16, -15:16]
    st[xx ** 2 + yy ** 2 <= 225] = True
    m = ndimage.binary_opening(m, st)
    lab, n = ndimage.label(m)
    big = np.argmax(ndimage.sum(m, lab, range(1, n + 1))) + 1
    return ndimage.binary_fill_holes(lab == big)


# ---- top view (gallery-1): image up = front (-X), image left = mouse left (-Y)
mt = mask("top-angle-gallery-1.png")
ys, xs = np.where(mt)
y0, y1 = ys.min(), ys.max()
s_t = L_SPEC / (y1 - y0)
# centre line = scroll-wheel axis column (mean column of the mask's narrow front third, symmetric buttons)
front = mt[y0 + int(0.15 * (y1 - y0)):y0 + int(0.40 * (y1 - y0))]
cols = [np.where(r)[0] for r in front]
xc = float(np.mean([(c.min() + c.max()) / 2 for c in cols]))

# ---- side view (gallery-6, right profile): image right = front
ms = mask("profile-right-angle-gallery-6.png")
ys2, xs2 = np.where(ms)
x0s, x1s = xs2.min(), xs2.max()
s_s = L_SPEC / (x1s - x0s)
pad = np.percentile([np.where(ms[:, x])[0].max() for x in range(x0s + 50, x1s - 50)], 95)  # flat pad line
crest = ys2.min()
v_s = H_SPEC / (pad - crest)

# ---- stations
st = []
for X in np.arange(-64.0, 64.01, 4.0):
    r = int(round(y0 + (X + 66) / s_t))
    c = np.where(mt[r])[0]
    xi = int(round(x1s - (X + 66) / s_s))
    cz = np.where(ms[:, xi])[0]
    st.append(dict(X=float(X), yl=float((c.min() - xc) * s_t), yr=float((c.max() - xc) * s_t),
                   ztop=float((pad - cz.min()) * v_s), zbot=float(max(0.0, (pad - cz.max()) * v_s))))

# ---- registered masks on mm grids
def regrid_top():
    Xg = np.arange(-70, 70, G); Yg = np.arange(-45, 45, G)
    XX, YY = np.meshgrid(Xg, Yg, indexing="ij")
    r = np.round(y0 + (XX + 66) / s_t).astype(int); c = np.round(xc + YY / s_t).astype(int)
    ok = (r >= 0) & (r < mt.shape[0]) & (c >= 0) & (c < mt.shape[1])
    out = np.zeros_like(XX, bool); out[ok] = mt[r[ok], c[ok]]
    return out


def regrid_side():
    Xg = np.arange(-70, 70, G); Zg = np.arange(-5, 50, G)
    XX, ZZ = np.meshgrid(Xg, Zg, indexing="ij")
    c = np.round(x1s - (XX + 66) / s_s).astype(int); r = np.round(pad - ZZ / v_s).astype(int)
    ok = (r >= 0) & (r < ms.shape[0]) & (c >= 0) & (c < ms.shape[1])
    out = np.zeros_like(XX, bool); out[ok] = ms[r[ok], c[ok]]
    return out


top, side = regrid_top(), regrid_side()
np.savez_compressed(os.path.join(REF, "registered.npz"), top=top, side=side, grid=G)
width_mm = (np.where(mt)[1].max() - np.where(mt)[1].min()) * s_t
info = dict(s_top_mm_px=s_t, s_side_mm_px=s_s, v_side_mm_px=v_s, centre_col=xc, top_width_mm=width_mm,
            side_aspect_note="side shot is elevated: vertical scale fitted to 40 mm separately", stations=st)
json.dump(info, open(os.path.join(HERE, "ref_profiles.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in info.items() if k != "stations"}, indent=1))
for s in st:
    print("({X:6.1f}, {yl:6.1f}, {yr:6.1f}, {ztop:5.1f}, {zbot:4.1f}),".format(**s))
