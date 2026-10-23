"""Fast posed-mass check outside Blender: bend the numpy loft, rasterise side / top / front, IoU vs the sheet masks,
write tools/design.png (sheet mask grey, model red outline overlay). py -3.11 tools/design.py"""
import os, sys, importlib
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import snake_shape as SS


def raster(polys, shape, f):
    img = Image.new('L', (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(img)
    for p in polys:
        d.polygon([f(q) for q in p], fill=255)
    return np.asarray(img) > 0


def main():
    V, F, ST = SS.mesh_np()
    P = np.array([SS.bend(v) for v in V])
    out = {}
    tiles = []
    for view, (a, b) in dict(side=(1, 2), top=(1, 0), front=(0, 2)).items():
        d = np.load(os.path.join(HERE, 'reference', f'{view}_mask.npz'))
        m, px = d['mask'], float(d['px'])
        if view == 'side':
            f = lambda q: ((q[1] - float(d['y0'])) / px, (float(d['z0']) - q[2]) / px)
        elif view == 'top':                            # the plan drawn 10 % small: compare in the scaled frame
            sc = SS.PLAN_SCALE
            x0, y0 = float(d['x0']) * sc, SS.SNOUT_Y + sc * (float(d['y0']) - SS.SNOUT_Y)
            pxs = px * sc
            f = lambda q: ((q[1] - y0) / pxs, (q[0] - x0) / pxs)
        else:
            f = lambda q: ((q[0] - float(d['x0'])) / px, (float(d['z0']) - q[2]) / px)
        mm = raster([[P[i] for i in fc] for fc in F], m.shape, f)
        iou = (mm & m).sum() / max(1, (mm | m).sum())
        out[view] = round(float(iou), 3)
        rgb = np.full(m.shape + (3,), 255, np.uint8)
        rgb[m] = (190, 190, 190)
        rgb[mm & ~m] = (240, 120, 120)
        rgb[mm & m] = (120, 120, 200)
        tiles.append(Image.fromarray(rgb))
    W = sum(t.width for t in tiles) + 20
    H = max(t.height for t in tiles) + 20
    sheet = Image.new('RGB', (W, H), 'white')
    x = 0
    for t in tiles:
        sheet.paste(t, (x, 20)); x += t.width + 10
    ImageDraw.Draw(sheet).text((4, 4), 'posed IoU ' + str(out) + '  (grey sheet only, red model only, blue both)', fill=(0, 0, 0))
    sheet.save(os.path.join(HERE, 'tools', 'design.png'))
    # self gap: vertices far apart along the spine that come close in the pose
    sv = np.repeat([s['s'] for s in ST], SS.NV)
    sv = np.r_[sv, sv]
    from scipy.spatial import cKDTree
    kd = cKDTree(P)
    pairs = kd.query_pairs(0.03, output_type='ndarray')
    far = pairs[np.abs(sv[pairs[:, 0]] - sv[pairs[:, 1]]) > 0.4]
    gap = min((np.linalg.norm(P[i] - P[j]) for i, j in far), default=None)
    print('posed IoU', out, 'stations', len(ST), 'verts', len(V), 'plan L %.3f' % SS.PLAN.L,
          'self-gap<3cm pairs', len(far), 'min', gap)


main()
