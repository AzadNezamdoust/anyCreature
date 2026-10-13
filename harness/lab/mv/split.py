import sys, numpy as np
sys.path.insert(0, r"E:\gen3d")
from PIL import Image
from scipy import ndimage
from mask8 import remove_bg8
# animal: (seed, side panel idx, front panel idx or None)
picks = dict(wolf=(1,(0,560),None), horse=(3,(40,850),(840,1240)), eagle=(1,(0,560),None), frog=(3,(60,470),(540,1040)))
def panels(im):
    a = np.asarray(im.convert("RGB")).min(-1) < 170
    col = a[: int(a.shape[0] * 0.85)].mean(0) > 0.004
    lab, n = ndimage.label(ndimage.binary_closing(col, iterations=4))
    out = []
    for i in range(1, n + 1):
        xs = np.where(lab == i)[0]
        if len(xs) > 80: out.append((xs[0], xs[-1]))
    return out
def lcc(r):
    a = np.array(r); lab, n = ndimage.label(a[..., 3] > 128)
    if n > 1:
        s = ndimage.sum(np.ones(lab.shape), lab, range(1, n + 1)); a[..., 3][lab != 1 + int(np.argmax(s))] = 0
    return Image.fromarray(a)
def square(im, x0, x1):
    c = im.crop((max(0, x0 - 20), 0, min(im.width, x1 + 20), im.height))
    s = int(max(c.size) * 1.1); b = Image.new("RGB", (s, s), "white")
    b.paste(c, ((s - c.width) // 2, (s - c.height) // 2)); return b.resize((1024, 1024), Image.LANCZOS)
for an, (s, si, fi) in picks.items():
    im = Image.open(f"E:/gen3d/mv/{an}/sheet_s{s}.png"); 
    side = lcc(remove_bg8(square(im, *si))); side.save(f"E:/gen3d/mv/{an}/side.png")
    side.transpose(Image.FLIP_LEFT_RIGHT).save(f"E:/gen3d/mv/{an}/side_mirror.png")
    if fi is not None: lcc(remove_bg8(square(im, *fi))).save(f"E:/gen3d/mv/{an}/front.png")



