#!/usr/bin/env python3
"""Side-view silhouettes as Fourier series — a target shape, and a ruler against it.

    python3 harness/fourier.py fit    <model.glb> <out.json> [--view side] [--K 32]
    python3 harness/fourier.py render <coeffs.json> <out.png> [--K 32]
    python3 harness/fourier.py score  <model.glb> <target.json> [--view side]

WHY. A silhouette brief in words ("deep chest, low tail") cannot be measured.
A silhouette as ~32 harmonics can: draw it once (from imagination, blind-read
it until it reads as the ordered animal), then score every build against it.
Low harmonics carry proportion and gesture; high ones carry ears, paws, tail
tips. So the score says not only HOW FAR the build is but WHICH SCALE is off.

ORTHOGRAPHIC, deliberately. outline.py renders through the perspective camera
the old browser renderer used; a target drawn as a model-sheet elevation has
no perspective, so the build is projected flat onto the view plane here. The
existing gates and their masks are untouched.

Coefficients JSON: {"coeffs": {"k": [re, im], ...}} for k = -K..K, image
coordinates (x right, y down). The artist files in this format load as-is.
"""
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import outline as O

RES = 1024
SAMPLES = 2048
BANDS = (4, 12, 32)   # gesture / proportion / features


# ── orthographic mask ──────────────────────────────────────────────────────
def ortho_mask(V, F, view='side', res=RES):
    lo, hi = V.min(axis=0), V.max(axis=0)
    d, up = O.view_dir(view, hi - lo)
    d = d / np.linalg.norm(d)
    right = np.cross(-d, up)
    if np.linalg.norm(right) < 1e-9:
        right = np.cross(-d, np.array([0., 0., 1.]))
    right /= np.linalg.norm(right)
    trueup = np.cross(right, -d)
    u, v = V @ right, V @ trueup
    span = max(np.ptp(u), np.ptp(v))
    s = res * 0.85 / span
    px = res / 2 + (u - (u.max() + u.min()) / 2) * s
    py = res / 2 - (v - (v.max() + v.min()) / 2) * s
    img = Image.new('1', (res, res), 0)
    drw = ImageDraw.Draw(img)
    for a, b, c in F:
        drw.polygon([(px[a], py[a]), (px[b], py[b]), (px[c], py[c])], fill=1)
    return np.array(img, dtype=bool)


# ── outline <-> coefficients ───────────────────────────────────────────────
def trace(mask):
    """Moore-neighbour trace of the outer boundary, as complex x + iy."""
    m = np.pad(mask, 1)
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        raise ValueError('empty mask')
    i = np.lexsort((xs, ys))[0]
    start = cur = (ys[i], xs[i])
    nb = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
    pts, d = [start], 6
    for _ in range(m.size):
        for k in range(8):
            dd = (d + k) % 8
            ny, nx = cur[0] + nb[dd][0], cur[1] + nb[dd][1]
            if m[ny, nx]:
                cur, d = (ny, nx), (dd + 5) % 8
                break
        if cur == start:
            break
        pts.append(cur)
    p = np.array(pts, float) - 1
    return p[:, 1] + 1j * p[:, 0]


def resample(z, n=SAMPLES):
    zz = np.append(z, z[0])
    s = np.concatenate([[0], np.cumsum(np.abs(np.diff(zz)))])
    t = np.linspace(0, s[-1], n, endpoint=False)
    return np.interp(t, s, zz.real) + 1j * np.interp(t, s, zz.imag)


def fit(z, K):
    C = np.fft.fft(resample(z)) / SAMPLES
    return {k: complex(C[k]) for k in range(-K, K + 1)}


def curve(cs, K=None, n=SAMPLES):
    t = np.arange(n) / n
    return sum(c * np.exp(2j * np.pi * k * t) for k, c in cs.items()
               if K is None or abs(k) <= K)


def load(path):
    j = json.load(open(path, encoding='utf-8'))
    return {int(k): complex(*v) for k, v in j['coeffs'].items()}


def save(cs, path, **meta):
    json.dump({**meta, 'coeffs': {str(k): [round(c.real, 5), round(c.imag, 5)]
                                  for k, c in sorted(cs.items())}},
              open(path, 'w', encoding='utf-8'), indent=1)


# ── distance ───────────────────────────────────────────────────────────────
def normalise(z):
    """Centre on the bounding box, scale to unit height (y-down kept)."""
    z = z - complex((z.real.max() + z.real.min()) / 2, (z.imag.max() + z.imag.min()) / 2)
    return z / np.ptp(z.imag)


def chamfer(a, b):
    """Mean nearest-point distance, both ways. Start point and winding free."""
    d = np.abs(a[:, None] - b[None, :])
    return float((d.min(axis=1).mean() + d.min(axis=0).mean()) / 2)


def score(built, target):
    """Per band K: distance of the K-harmonic outlines, % of height.
    The build may face either way; the better-matching facing is used."""
    out = {}
    for K in BANDS + (max(abs(k) for k in target),):
        a = normalise(curve(built, K, 512))
        b = normalise(curve(target, K, 512))
        flip = -a.real + 1j * a.imag
        out[K] = round(100 * min(chamfer(a, b), chamfer(flip, b)), 2)
    return out


def render(cs, path, K=None, res=RES):
    z = normalise(curve(cs, K))
    z *= res * 0.85 / max(np.ptp(z.real), np.ptp(z.imag))
    pts = [(res / 2 + p.real, res / 2 + p.imag) for p in z]
    img = Image.new('L', (res, res), 255)
    ImageDraw.Draw(img).polygon(pts, fill=0)
    img.save(path)


def from_model(model, view, K):
    V, F = O.triangles(model)
    return fit(trace(ortho_mask(V, F, view)), K)


def main():
    a = sys.argv[1:]
    if len(a) < 3:
        print(__doc__)
        return 2
    opt = lambda f, d: a[a.index(f) + 1] if f in a else d
    view, K = opt('--view', 'side'), int(opt('--K', 32))
    cmd = a[0]
    if cmd == 'fit':
        save(from_model(a[1], view, K), a[2], view=view, K=K, source=os.path.basename(a[1]))
        print(f'{a[2]}: {2 * K + 1} coefficients, {view} view, orthographic')
    elif cmd == 'render':
        render(load(a[1]), a[2], K)
        print(a[2])
    elif cmd == 'score':
        tgt = load(a[2])
        Kt = max(abs(k) for k in tgt)
        s = score(from_model(a[1], view, Kt), tgt)
        print(json.dumps({'view': view, 'dist_pct_of_height': s}))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
