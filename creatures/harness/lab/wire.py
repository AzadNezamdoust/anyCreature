#!/usr/bin/env python3
"""Topology sheet for low-poly judging: shaded views with the mesh's own
polygon edges drawn on top (quads stay quads), plus face stats.

    python wire.py <mesh.obj> <wire.png>
"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R


def load_polys(path):
    V, P = [], []
    for line in open(path, encoding='utf-8', errors='ignore'):
        p = line.split()
        if not p:
            continue
        if p[0] == 'v':
            V.append([float(x) for x in p[1:4]])
        elif p[0] == 'f':
            idx = [int(q.split('/')[0]) for q in p[1:]]
            P.append([i - 1 if i > 0 else len(V) + i for i in idx])
    return np.array(V, float), P


def view(V, F, P, rot, res):
    img = R.draw_gl(V, F, rot, res, True).convert('RGB')
    W = V @ rot.T
    s = 0.86 * 2 / max(np.ptp(W[:, 0]), np.ptp(W[:, 1]))
    c = (W.max(0) + W.min(0)) / 2
    x = res / 2 + (W[:, 0] - c[0]) * s * res / 2
    y = res / 2 - (W[:, 1] - c[1]) * s * res / 2
    # visibility: an edge is drawn if its midpoint depth is near the front
    d = ImageDraw.Draw(img)
    seen = set()
    for poly in P:
        n = len(poly)
        for k in range(n):
            a, b = poly[k], poly[(k + 1) % n]
            e = (min(a, b), max(a, b))
            if e in seen:
                continue
            seen.add(e)
            d.line([(x[a], y[a]), (x[b], y[b])], fill=(20, 60, 160), width=1)
    return img


def main(src, out, res=768):
    V, P = load_polys(src)
    F = np.array([[p[0], p[k], p[k + 1]] for p in P for k in range(1, len(p) - 1)])
    V = R.canon(V)
    # back faces would clutter the wire: keep only front-facing polygons per view
    sheet = Image.new('RGB', (res * 2, res + 40), 'white')
    for i, rot in enumerate([R.rot(-35, -20), R.rot(0, 0)]):
        W = V @ rot.T
        fn = np.cross(W[F[:, 1]] - W[F[:, 0]], W[F[:, 2]] - W[F[:, 0]])[:, 2]
        front_tri = fn < 0                     # camera at -z
        # polygon is front if its first fan triangle is front-facing
        ti, Pf = 0, []
        for p in P:
            if front_tri[ti]:
                Pf.append(p)
            ti += len(p) - 2
        sheet.paste(view(V, F, Pf, rot, res), (i * res, 0))
    q = sum(len(p) == 4 for p in P)
    t = sum(len(p) == 3 for p in P)
    o = len(P) - q - t
    ImageDraw.Draw(sheet).text((10, res + 12),
        f'{len(P)} faces  quads {q} ({100 * q / max(1, len(P)):.0f}%)  tris {t}  ngons {o}  verts {len(V)}',
        fill='black')
    sheet.save(out)
    print(out, len(P), 'faces', q, 'quads', t, 'tris')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
