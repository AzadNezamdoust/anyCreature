"""Segment reference photos -> binary silhouettes, cropped to bbox (refs/L4/mask_*.png)."""
import numpy as np, os
from PIL import Image
from scipy import ndimage as nd
R = os.path.join(os.path.dirname(__file__), "..", "..", "refs", "L4")
def largest(m):
    lab, n = nd.label(m); s = nd.sum(m, lab, range(1, n + 1)); return lab == (1 + int(np.argmax(s)))
def save(m, name):
    ys, xs = np.nonzero(m); m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    Image.fromarray((m * 255).astype(np.uint8)).save(os.path.join(R, name)); print(name, m.shape[1], m.shape[0], "aspect w/h", round(m.shape[1] / m.shape[0], 4))
# plan (top-down photo of Carbon Black on granite)
a = np.asarray(Image.open(os.path.join(R, "Xbox_Series_Controller_Carbon_Black.jpg")).convert("RGB")).astype(float)
lum = a.mean(2)
mu = nd.uniform_filter(lum, 15); sd = np.sqrt(np.maximum(nd.uniform_filter(lum**2, 15) - mu**2, 0))
m = (mu < 70) & (sd < 22)          # controller = dark + smooth; granite = high local variance
m = nd.binary_opening(m, iterations=4); m = nd.binary_closing(m, iterations=8)
m = nd.binary_fill_holes(largest(m)); save(m, "mask_top.png")
# rear elevation (Gold Shadow 'top' photo = looking at the back/trigger end, white bg)
a = np.asarray(Image.open(os.path.join(R, "Xbox_Series_Controller_Gold_Shadow_Special_Edition_top.jpg")).convert("RGB")).astype(float)
m = a.min(2) < 200
m = nd.binary_opening(nd.binary_closing(m, iterations=3), iterations=2); m = nd.binary_fill_holes(largest(m))
m[int(0.62 * a.shape[0]):] &= (a.min(2) < 150)[int(0.62 * a.shape[0]):]  # drop soft floor shadow
m = nd.binary_fill_holes(largest(nd.binary_opening(m, iterations=2))); save(m, "mask_back.png")
# plan: segmentation on granite fails (dark specks) -> hand-traced outline of [P1] (px), anisotropically registered to
# the published 153 x 102 mm (photo is slightly oblique: raw trace aspect 988:705 = 1.40 vs 1.50 spec)
TRACE = [(380,185),(455,160),(495,162),(510,175),(700,170),(850,170),(860,160),(900,162),(970,185),(1010,215),
 (1050,270),(1090,350),(1120,450),(1140,540),(1155,620),(1160,700),(1150,780),(1130,820),(1100,845),(1070,850),
 (1040,830),(1000,790),(960,740),(920,700),(880,690),(700,690),(520,690),(470,700),(420,740),(370,790),(320,840),
 (280,865),(240,865),(200,840),(178,780),(172,700),(180,620),(195,540),(215,450),(245,360),(280,290),(320,240),(360,200)]
from PIL import ImageDraw
xs = [p[0] for p in TRACE]; ys = [p[1] for p in TRACE]
sx = 1000 / (max(xs) - min(xs)); sy = 1000 * (102 / 153) / (max(ys) - min(ys))
im = Image.new("L", (1001, int(1000 * 102 / 153) + 1), 0)
ImageDraw.Draw(im).polygon([((x - min(xs)) * sx, (y - min(ys)) * sy) for x, y in TRACE], fill=255)
im.save(os.path.join(R, "mask_top_trace.png")); print("mask_top_trace.png", im.size)
