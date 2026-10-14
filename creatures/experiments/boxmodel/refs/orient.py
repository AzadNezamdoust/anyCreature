#!/usr/bin/env python3
"""Fix the view directions of a generated 2 x 2 turnaround sheet before it is traced.

    py -3.11 experiments/boxmodel/refs/orient.py <sheet.png> <out.png> [--side flip] [--top rot90cw|rot90ccw|rot180|flip|flipv]
                                                                    [--front flip] [--rear flip]

The prompt asks for: SIDE with the head pointing LEFT, TOP (plan) with the head pointing LEFT. Generators, Gemini
most often, sometimes draw a side view facing right or a plan view turned 90 degrees. The creatures are left-right
symmetric, so a mirrored side view is still a correct side view once flipped back; a turned plan view is still a correct
plan view once rotated back. Nothing is resized: every view keeps its pixel scale, so the views stay comparable.

The views are cut on the sheet's white gutters (kit/refs.py split_views), transformed, and laid out again as a 2 x 2
sheet (side, front / rear, top) with square cells and wide white gutters; side, front and rear share one ground line.
The ops go to <out>.json next to the output.
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'kit'))
import refs as R

OPS = {
    'none': lambda im: im,
    'flip': lambda im: im.transpose(Image.FLIP_LEFT_RIGHT),
    'flipv': lambda im: im.transpose(Image.FLIP_TOP_BOTTOM),
    'rot90cw': lambda im: im.transpose(Image.ROTATE_270),
    'rot90ccw': lambda im: im.transpose(Image.ROTATE_90),
    'rot180': lambda im: im.transpose(Image.ROTATE_180),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('sheet')
    ap.add_argument('out')
    for v in ('side', 'front', 'rear', 'top'):
        ap.add_argument(f'--{v}', default='none', choices=list(OPS))
    ap.add_argument('--thresh', type=float, default=40.0)
    ap.add_argument('--fit', action='store_true', help='make the views agree as one orthographic set (see main)')
    ap.add_argument('--aspect', type=float, help='with --fit: the brief length / height; the side and plan views are '
                    'stretched along the body so the side view has it (generators draw bodies 15-45%% short)')
    a = ap.parse_args()

    src = Image.open(a.sheet).convert('RGB')
    rgb = np.asarray(src)
    H, W = rgb.shape[:2]
    bg = R.background_colour(rgb)
    views, cells, _ = R.split_views(R.foreground(rgb, bg, a.thresh))
    if views is None or views[0] == 'front':
        sys.exit(f'orient.py: FAIL: needs a 2 x 2 sheet (found figures per row {cells})')
    M = 8
    crops = {}
    for name, (r0, r1, c0, c1) in zip(views, cells):
        box = (max(0, c0 - M), max(0, r0 - M), min(W, c1 + M), min(H, r1 + M))
        crops[name] = OPS[getattr(a, name)](src.crop(box))
    fit = {}
    if a.fit:
        # a true orthographic set shares its extents: front/rear height = side height (uniform scale),
        # top length = side length and top width = front width (per-axis scale). The side view is the master.
        def ext(im):
            m = R.foreground(np.asarray(im), bg, a.thresh)
            ys, xs = np.nonzero(m)
            return xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
        Ls, Hs = ext(crops['side'])
        for name in ('front', 'rear'):
            w, h = ext(crops[name])
            k = Hs / h
            fit[name] = round(k, 3)
            if abs(k - 1) > 0.005:
                im = crops[name]
                crops[name] = im.resize((max(1, round(im.size[0] * k)), max(1, round(im.size[1] * k))), Image.LANCZOS)
        Wf, _ = ext(crops['front'])
        Lt, Wt = ext(crops['top'])
        kx, ky = Ls / Lt, Wf / Wt
        fit['top'] = [round(kx, 3), round(ky, 3)]
        if abs(kx - 1) > 0.005 or abs(ky - 1) > 0.005:
            im = crops['top']
            crops['top'] = im.resize((max(1, round(im.size[0] * kx)), max(1, round(im.size[1] * ky))), Image.LANCZOS)
        kl = 1.0
        if a.aspect:
            # the brief sets the size: height is already the master, so length follows from length/height.
            # Only the body axis is stretched (side and plan views, image x); width is left to the sheet,
            # because brief widths are pose extents ("with the feet", "across the arms").
            kl = a.aspect * Hs / Ls
            fit['length'] = round(kl, 3)
            if abs(kl - 1) > 0.005:
                for name in ('side', 'top'):
                    im = crops[name]
                    crops[name] = im.resize((max(1, round(im.size[0] * kl)), im.size[1]), Image.LANCZOS)
        fit['largest'] = round(max(abs(fit['front'] - 1), abs(fit['rear'] - 1), abs(kx - 1), abs(ky - 1), abs(kl - 1)), 3)
    S = max(max(im.size) for im in crops.values())
    G = max(40, S // 6)                                   # gutter
    sheet = Image.new('RGB', (2 * S + 3 * G, 2 * S + 3 * G), (255, 255, 255))
    slots = {'side': (0, 0), 'front': (0, 1), 'rear': (1, 0), 'top': (1, 1)}
    ground = G + S                                        # the upper row's ground line
    for name, (row, col) in slots.items():
        im = crops[name]
        x = G + col * (S + G) + (S - im.size[0]) // 2
        if name == 'top':                                 # the plan view has no ground: centre it
            y = G + row * (S + G) + (S - im.size[1]) // 2
        elif row == 0:
            y = ground - im.size[1]                       # feet on the upper row's ground line
        else:
            y = G + S + G + S - im.size[1]                # the lower row's own ground line
        sheet.paste(im, (x, y))
    sheet.save(a.out)
    ops = {v: getattr(a, v) for v in ('side', 'front', 'rear', 'top')}
    json.dump(dict(source=os.path.basename(a.sheet), ops=ops, fit=fit), open(os.path.splitext(a.out)[0] + '.json', 'w'), indent=1)
    print('orient: wrote', a.out, {k: v for k, v in ops.items() if v != 'none'} or 'no direction change',
          f'fit {fit}' if fit else '')


if __name__ == '__main__':
    main()
