#!/usr/bin/env python3
"""The 2D Fourier silhouette method, in 3D: a creature as a set of Fourier tubes.

    python3 fourier3d.py <sketch.json> <outdir> [--N 12] [--M 8]

THE METHOD. In 2D an outline is a closed curve, so it is one Fourier series.
A creature body is not one closed surface you can write that way (legs make it
non-star-shaped), but it IS a few tubes: torso, neck+head, legs, tail, ears.
Each tube is two Fourier series:

  centre line  c(t) = a0 + sum_n a_n cos(n pi t)         t in [0,1], n <= N
  section      r(t, th) = sum_m [A_m(t) cos m th + B_m(t) sin m th],  m <= M
               where every A_m(t), B_m(t) is itself a cosine series in t (n <= N)

Cosine series along t because a tube is open (two ends); a full Fourier
series around th because a section is closed. N = detail along the tube,
M = detail around it. The creature IS the coefficient file; everything drawn
is evaluated from the coefficients only.

SKETCH. You imagine samples, the tool fits coefficients — exactly as in 2D:
  {"tubes": [{"name": "leg_front", "mirror": true,
              "points": [[x,y,z], ...],          # centre line, head-end first
              "radii":  [r | [rw, rh] | [r0..rK-1 around th], ...]}]}
Axes: x along the body (head toward -x), y up, z left/right. "mirror": true
also builds the copy at -z (pairs: legs, ears). Units are free.

OUTPUT. coeffs.json (the creature), mesh.obj, sheet.png (orthographic side,
front, top silhouettes + one shaded 3/4 view).
"""
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw

S, R = 64, 32        # fit samples along / around
T, TH = 96, 40       # evaluation samples along / around


# ── series ─────────────────────────────────────────────────────────────────
def dct_fit(f, N):
    """f: (S, ...) samples at t_j = (j+.5)/S  ->  (N+1, ...) cosine coefficients."""
    t = (np.arange(len(f)) + 0.5) / len(f)
    B = np.cos(np.pi * np.outer(np.arange(N + 1), t))          # (N+1, S)
    a = (2.0 / len(f)) * np.tensordot(B, f, axes=1)
    a[0] /= 2
    return a


def dct_eval(a, t):
    B = np.cos(np.pi * np.outer(t, np.arange(len(a))))         # (len t, N+1)
    return np.tensordot(B, a, axes=1)


def resample_line(P, n=S):
    P = np.asarray(P, float)
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    t = (np.arange(n) + 0.5) / n * s[-1]
    return np.stack([np.interp(t, s, P[:, i]) for i in range(3)], 1), s / s[-1]


def radial(r):
    """One radii entry -> R samples of radius around th (0 = up, then toward +z)."""
    th = 2 * np.pi * np.arange(R) / R
    if np.isscalar(r):
        return np.full(R, float(r))
    r = list(map(float, r))
    if len(r) == 2:                                            # ellipse rw (side), rh (up)
        rw, rh = r
        return rw * rh / np.sqrt((rw * np.cos(th)) ** 2 + (rh * np.sin(th)) ** 2)
    k = np.arange(len(r)) * R / len(r)
    return np.interp(np.arange(R), np.append(k, R), r + [r[0]])


def fit_tube(tube, N, M):
    P, u = resample_line(tube['points'])
    rad = np.array([radial(r) for r in tube['radii']])          # (K, R)
    tj = (np.arange(S) + 0.5) / S
    rad = np.stack([np.interp(tj, u, rad[:, i]) for i in range(R)], 1)   # (S, R)
    F = np.fft.rfft(rad, axis=1) / R                            # (S, R/2+1) around
    F = F[:, :M + 1]
    return {'name': tube.get('name', ''), 'mirror': bool(tube.get('mirror')),
            'center': dct_fit(P, N).tolist(),
            'section_re': dct_fit(F.real, N).tolist(),
            'section_im': dct_fit(F.imag, N).tolist()}


# ── evaluate: coefficients only ────────────────────────────────────────────
def frames(C):
    Tg = np.gradient(C, axis=0)
    Tg /= np.linalg.norm(Tg, axis=1, keepdims=True) + 1e-12
    up = np.array([0., 1., 0.])
    n = up - Tg[0] * (Tg[0] @ up)
    if np.linalg.norm(n) < 1e-6:
        n = np.array([1., 0., 0.]) - Tg[0] * Tg[0][0]
    n /= np.linalg.norm(n)
    Ns = [n]
    for i in range(1, len(C)):                                  # parallel transport
        n = Ns[-1] - Tg[i] * (Tg[i] @ Ns[-1])
        Ns.append(n / (np.linalg.norm(n) + 1e-12))
    Ns = np.array(Ns)
    return Ns, np.cross(Tg, Ns)


def tube_mesh(tc, flip=False):
    t = np.linspace(0, 1, T)
    C = dct_eval(np.array(tc['center']), t)
    F = dct_eval(np.array(tc['section_re']), t) + 1j * dct_eval(np.array(tc['section_im']), t)
    th = 2 * np.pi * np.arange(TH) / TH
    m = np.arange(F.shape[1])
    w = np.where(m == 0, 1, 2)
    r = np.real((F * w) @ np.exp(1j * np.outer(m, th)))         # (T, TH)
    r = np.maximum(r, 1e-4)
    Nn, Bn = frames(C)
    V = (C[:, None, :] + r[..., None] * (np.cos(th)[None, :, None] * Nn[:, None, :]
                                         + np.sin(th)[None, :, None] * Bn[:, None, :]))
    V = V.reshape(-1, 3)
    Fc = []
    for i in range(T - 1):
        for j in range(TH):
            a, b = i * TH + j, i * TH + (j + 1) % TH
            Fc += [(a, b, b + TH), (a, b + TH, a + TH)]
    c0, c1 = len(V), len(V) + 1
    V = np.vstack([V, C[0], C[-1]])
    for j in range(TH):
        Fc += [(c0, (j + 1) % TH, j), (c1, (T - 1) * TH + j, (T - 1) * TH + (j + 1) % TH)]
    Fc = np.array(Fc)
    if flip:
        V = V * np.array([1, 1, -1])
        Fc = Fc[:, ::-1]
    return V, Fc


def build(coeffs):
    Vs, Fs, off = [], [], 0
    for tc in coeffs['tubes']:
        for flip in ([False, True] if tc['mirror'] else [False]):
            V, F = tube_mesh(tc, flip)
            Vs.append(V); Fs.append(F + off); off += len(V)
    return np.vstack(Vs), np.vstack(Fs)


# ── pictures ───────────────────────────────────────────────────────────────
def view(V, F, axes, res, shade=None):
    P = V[:, axes]
    lo, hi = P.min(0), P.max(0)
    s = res * 0.85 / (hi - lo).max()
    x = res / 2 + (P[:, 0] - (lo[0] + hi[0]) / 2) * s
    y = res / 2 - (P[:, 1] - (lo[1] + hi[1]) / 2) * s
    img = Image.new('L', (res, res), 255)
    d = ImageDraw.Draw(img)
    order = range(len(F)) if shade is None else np.argsort(shade[0])
    for i in order:
        a, b, c = F[i]
        g = 0 if shade is None else int(shade[1][i])
        d.polygon([(x[a], y[a]), (x[b], y[b]), (x[c], y[c])], fill=g)
    return img


def sheet(V, F, path, res=512):
    side = view(V, F, [0, 1], res)
    front = view(V, F, [2, 1], res)
    top = view(V, F, [0, 2], res)
    # 3/4: rotate 35 deg about y, 20 deg down; painter's sort, lambert grey
    a, e = math.radians(35), math.radians(-20)
    Ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(e), -math.sin(e)], [0, math.sin(e), math.cos(e)]])
    W = V @ Ry.T @ Rx.T
    n = np.cross(W[F[:, 1]] - W[F[:, 0]], W[F[:, 2]] - W[F[:, 0]])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    lam = np.clip(n @ np.array([-0.4, 0.6, -0.7]) / np.linalg.norm([-0.4, 0.6, -0.7]), 0, 1)
    depth = -W[F].mean(1)[:, 2]
    hero = view(W, F, [0, 1], res, (depth, 60 + 170 * lam))
    out = Image.new('L', (res * 2, res * 2), 255)
    for im, (ox, oy) in zip([side, front, top, hero], [(0, 0), (res, 0), (0, res), (res, res)]):
        out.paste(im, (ox, oy))
    d = ImageDraw.Draw(out)
    for txt, (ox, oy) in zip(['side', 'front', 'top', '3/4'], [(0, 0), (res, 0), (0, res), (res, res)]):
        d.text((ox + 8, oy + 8), txt, fill=120)
    out.save(path)


def write_obj(V, F, path):
    with open(path, 'w') as f:
        f.writelines(f'v {a:.5f} {b:.5f} {c:.5f}\n' for a, b, c in V)
        f.writelines(f'f {a + 1} {b + 1} {c + 1}\n' for a, b, c in F)


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__)
        return 2
    opt = lambda k, d: int(a[a.index(k) + 1]) if k in a else d
    N, M = opt('--N', 12), opt('--M', 8)
    sk, out = json.load(open(a[0], encoding='utf-8')), a[1]
    os.makedirs(out, exist_ok=True)
    coeffs = {'N': N, 'M': M, 'tubes': [fit_tube(t, N, M) for t in sk['tubes']]}
    json.dump(coeffs, open(os.path.join(out, 'coeffs.json'), 'w'))
    V, F = build(json.load(open(os.path.join(out, 'coeffs.json'))))   # coefficients only
    write_obj(V, F, os.path.join(out, 'mesh.obj'))
    sheet(V, F, os.path.join(out, 'sheet.png'))
    n = sum((2 if t['mirror'] else 1) for t in coeffs['tubes'])
    k = sum(3 * (N + 1) + 2 * (N + 1) * (M + 1) for _ in coeffs['tubes'])
    print(f'{len(coeffs["tubes"])} tubes ({n} with mirrors), {k} numbers, '
          f'{len(V)} verts -> {out}/coeffs.json mesh.obj sheet.png')
    return 0


if __name__ == '__main__':
    sys.exit(main())
