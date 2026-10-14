import numpy as np
from PIL import Image
from scipy import ndimage
def remove_bg8(img, erode=1):
    a = np.asarray(img.convert("RGB")).astype(np.int16)
    H, W = a.shape[:2]
    mn, mx = a.min(-1), a.max(-1); sat = mx - mn
    yy = np.arange(H)[:, None] * np.ones((1, W))
    # rough fg extent from strict bg to find the creature bottom zone
    rough = ~((mn >= 235))
    rows = np.where(rough.mean(1) > 0.01)[0]; top, bot = (rows[0], rows[-1]) if len(rows) else (0, H)
    low_zone = yy > top + 0.55 * (bot - top)
    L = a.mean(-1).astype(np.float32)
    std = np.sqrt(np.maximum(ndimage.uniform_filter(L*L, 7) - ndimage.uniform_filter(L, 7)**2, 0))
    smooth = std < 6.0
    foot_zone = yy > top + 0.8 * (bot - top)
    bluegray = (a[..., 2] >= a[..., 0]) & (sat <= 40) & (mn >= 130)
    cand = (foot_zone & bluegray) | (mn >= 236) | ((mn >= 195) & (sat <= 20) & smooth) | (low_zone & (mn >= 120) & (sat <= 26) & smooth)
    lab, _ = ndimage.label(cand)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(border))
    sz = ndimage.sum(np.ones_like(mn), lab, range(1, lab.max() + 1))
    cy = ndimage.center_of_mass(np.ones_like(mn), lab, range(1, lab.max() + 1))
    big = [i + 1 for i in range(len(sz)) if sz[i] > 600 and cy[i][0] > top + 0.5 * (bot - top)]
    bg |= np.isin(lab, big) & (mn >= 200)   # enclosed bg windows (between legs) are bg too
    fg = ndimage.binary_opening(~bg, structure=np.ones((3, 3)), iterations=3)
    lab2, n = ndimage.label(fg)
    if n > 1:
        s = ndimage.sum(fg, lab2, range(1, n + 1)); big = s.max()
        keep = [i + 1 for i in range(n) if s[i] >= 0.02 * big]   # keep detached legs/tips, drop specks
        fg = np.isin(lab2, keep)
    filled = ndimage.binary_fill_holes(fg); holes, nh = ndimage.label(filled & ~fg)
    for i in range(1, nh + 1):
        h = holes == i
        bright = (mn[h] >= 225).mean() > 0.6 or ((mn[h] >= 150) & (sat[h] <= 26)).mean() > 0.8
        if not (bright and h.sum() > 200): fg |= h   # small/dark holes = creature; big bright holes = bg gaps
    if erode: fg = ndimage.binary_erosion(fg, iterations=erode)
    alpha = (ndimage.gaussian_filter(fg.astype(np.float32), 0.8) * 255).astype(np.uint8)
    return Image.fromarray(np.dstack([a.astype(np.uint8), alpha]), "RGBA")
if __name__ == "__main__":
    import sys
    picks = dict(crocodile=4, eagle=3, elephant=8, frog=3, giraffe=2, horse=3, kangaroo=1, shark=2, tortoise=1, wolf=3)
    tiles = []
    if len(sys.argv) > 1: picks = {k: picks[k] for k in sys.argv[1].split(",")}
    for an, k in picks.items():
        im = Image.open(f"r7/{an}/c{k}.png"); r = remove_bg8(im)
        import os; os.makedirs(f"r8/{an}", exist_ok=True); r.save(f"r8/{an}/ref_rgba_v2.png")
        old = Image.open(f"r7/{an}/ref_rgba.png")
        for x in (old, r):
            bgc = Image.new("RGBA", x.size, (255, 0, 255, 255)); bgc.alpha_composite(x); tiles.append(bgc.convert("RGB").resize((256, 256)))
    sheet = Image.new("RGB", (256 * 4, 256 * ((len(tiles) + 3) // 4)))
    for i, t in enumerate(tiles): sheet.paste(t, ((i % 4) * 256, (i // 4) * 256))
    sheet.save("r8/masks.png")
