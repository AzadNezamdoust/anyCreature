"""A wolf written from memory as an outline, stored as a Fourier series.

No mesh, no repo geometry: ~40 points I placed by picturing a wolf standing
side-on (facing left, y down, ground at y=60), turned into harmonics, then
drawn back from the harmonics alone.

python3 harness/fourier_wolf_hand.py out/blind
"""
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw

WOLF = [  # clockwise from nose tip
    (3, 18), (8, 15), (14, 13), (17, 11), (20, 8), (22, 6), (24, 0), (27, 7),
    (30, 9), (36, 13), (42, 14), (55, 15), (68, 15), (76, 16), (80, 17),
    (86, 22), (90, 30), (91, 38), (89, 45), (86, 46), (85, 38), (82, 28),
    (79, 24), (78, 28), (79, 34), (81, 44), (80, 58), (81, 60), (74, 60),
    (74, 57), (74, 45), (71, 36), (68, 32), (60, 30), (48, 31), (38, 33),
    (38, 58), (39, 60), (32, 60), (33, 57), (33, 40), (31, 30), (26, 24),
    (18, 22), (10, 21), (6, 20),
]


def resample(z, n=1024):
    zz = np.append(z, z[0])
    s = np.concatenate([[0], np.cumsum(np.abs(np.diff(zz)))])
    t = np.linspace(0, s[-1], n, endpoint=False)
    return np.interp(t, s, zz.real) + 1j * np.interp(t, s, zz.imag)


def coeffs(K):
    z = resample(np.array([complex(x, y) for x, y in WOLF]))
    C = np.fft.fft(z) / len(z)
    ks = list(range(-K, K + 1))
    return {k: C[k] for k in ks}


def draw(cs, path, n=600, px=512):
    t = np.arange(n) / n
    z = sum(c * np.exp(2j * np.pi * k * t) for k, c in cs.items())
    x, y = z.real, z.imag
    s = px * 0.85 / max(np.ptp(x), np.ptp(y))
    cx, cy = (x.max() + x.min()) / 2, (y.max() + y.min()) / 2
    pts = [(px / 2 + (a - cx) * s, px / 2 + (b - cy) * s) for a, b in zip(x, y)]
    img = Image.new('L', (px, px), 255)
    ImageDraw.Draw(img).polygon(pts, fill=0)
    img.save(path)


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    # neutral file names, order scrambled, so the reader learns nothing from them
    order = {'p': 3, 'q': 12, 'r': 6, 's': 24}
    for name, K in order.items():
        cs = coeffs(K)
        draw(cs, os.path.join(out, f'{name}.png'))
    key = {n: K for n, K in order.items()}
    cs = coeffs(12)
    json.dump({'key': key, 'harmonics_12': {str(k): [round(c.real, 3), round(c.imag, 3)]
                                            for k, c in cs.items()}},
              open(os.path.join(out, '..', 'blind_key.json'), 'w'), indent=1)
    print(key)


if __name__ == '__main__':
    main()
