"""Silhouette -> Fourier series -> silhouette, at rising harmonic counts.

python3 harness/fourier_demo.py out/wolf.glb out/fourier_side.png [view]
"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import outline as O


def trace(mask):
    """Moore-neighbour boundary trace of the largest blob's outer edge."""
    m = np.pad(mask, 1)
    ys, xs = np.nonzero(m)
    i = np.lexsort((xs, ys))[0]
    start = (ys[i], xs[i])
    nb = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
    pts, cur, d = [start], start, 6
    while True:
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
    return p[:, 1] + 1j * p[:, 0]          # complex x + iy


def resample(z, n=2048):
    seg = np.abs(np.diff(np.append(z, z[0])))
    s = np.concatenate([[0], np.cumsum(seg)])
    t = np.linspace(0, s[-1], n, endpoint=False)
    zz = np.append(z, z[0])
    return np.interp(t, s, zz.real) + 1j * np.interp(t, s, zz.imag)


def rebuild(C, K):
    n = len(C)
    keep = np.zeros(n, complex)
    keep[0] = C[0]
    keep[1:K + 1] = C[1:K + 1]
    keep[n - K:] = C[n - K:]
    return np.fft.ifft(keep)


def main():
    glb, out = sys.argv[1], sys.argv[2]
    view = sys.argv[3] if len(sys.argv) > 3 else 'side'
    V, F = O.triangles(glb)
    mask = O.render_mask(V, F, view)
    z = resample(trace(mask))
    C = np.fft.fft(z)
    H = float(z.imag.max() - z.imag.min())

    # energy in each harmonic (pair ±k), excluding position (k=0)
    n = len(C)
    e = np.array([abs(C[k]) ** 2 + abs(C[n - k]) ** 2 for k in range(1, n // 2)])
    cum = np.cumsum(e) / e.sum()

    Ks = [1, 2, 4, 8, 16, 32, 64, 128]
    ys, xs = np.nonzero(mask)
    x0, x1, y0, y1 = xs.min() - 10, xs.max() + 10, ys.min() - 10, ys.max() + 10
    cw, ch = int(x1 - x0), int(y1 - y0)
    sc = 300 / max(cw, ch)
    pw, ph = int(cw * sc), int(ch * sc) + 40
    cols = 4
    img = Image.new('RGB', (pw * cols, ph * 2), (250, 250, 247))
    dr = ImageDraw.Draw(img)
    report = []
    for idx, K in enumerate(Ks):
        r = rebuild(C, K)
        err = np.abs(r - z).max() / H * 100
        report.append((K, err, cum[K - 1] * 100))
        ox, oy = (idx % cols) * pw, (idx // cols) * ph
        tf = lambda w: [(ox + (p.real - x0) * sc, oy + (p.imag - y0) * sc) for p in w]
        dr.polygon(tf(z), fill=(222, 222, 216))
        dr.line(tf(np.append(r, r[0])), fill=(200, 60, 40), width=2)
        dr.text((ox + 8, oy + ph - 34), f"harmonics {K}", fill=(20, 20, 20))
        dr.text((ox + 8, oy + ph - 20), f"max err {err:.2f}% of height", fill=(90, 90, 90))
    img.save(out)
    for K, err, en in report:
        print(f"K={K:4d}  max_err={err:6.2f}%  energy={en:6.2f}%")
    for tgt in (5.0, 1.0):
        K = next((k for k in range(1, n // 2) if np.abs(rebuild(C, k) - z).max() / H * 100 < tgt), None)
        print(f"harmonics for <{tgt}% error: {K}")


if __name__ == '__main__':
    main()
