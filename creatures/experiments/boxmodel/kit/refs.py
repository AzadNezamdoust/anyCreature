#!/usr/bin/env python3
"""refs.py — ingest a generated turnaround sheet as a creature's reference and trace
blueprint.json from it (settings G/O of the reference-image test). Plain Python,
numpy + Pillow; runs outside Blender.

    py -3.11 experiments/boxmodel/kit/refs.py <sheet.png> <creature_dir> --height <m> [--length <m>]

The sheet (auto-detected by white gutters: rows first, then columns in each row):
- 2 x 2: SIDE (head LEFT, left flank to the viewer) | FRONT (left flank on the image right)
         REAR (left flank on the image left)        | TOP (plan: head LEFT, left flank at the image bottom)
- 1 x 4: FRONT, SIDE (facing LEFT), BACK, THREE-QUARTER FRONT.
Near-white background, one common scale, feet on one ground line per row. Anything else fails.

Writes
  <creature_dir>/blueprint.json      side + front (+ top from a 2 x 2) outlines in the kit's schema (BRIEF.md §3)
  <creature_dir>/reference/          sheet.png, the square crops (2 x 2: side, front, rear, top.png;
                                     1 x 4: front, side, back, threeq.png),
                                     trace.png (the traced outlines over the views), refs.json;
                                     top.png is turned 90 deg CW to the kit's top render (head up)

Coordinates (the kit's): metres, Z up, the creature faces -Y, its left flank is +X, feet on z = 0.
- side: the sheet's facing-left side view IS the kit's az090 view (head on the image's left =
  -Y), so y = (column - bbox centre) * scale, z = (ground row - row) * scale. The side
  bounding box is centred on y = 0: build the creature there, or the stage-1 IoU drops.
- front: the half outline (x >= 0), symmetrised by averaging the left and right half-widths
  of each row about the figure's axis.
- top (2 x 2): the plan view's half outline [x, y] (x >= 0), symmetrised about its long axis, at
  the side's scale with its bbox centred on y = 0; the length is cross-checked against the side
  (a warning past 10%). A 1 x 4 sheet has no plan view: top is omitted (optional in the schema).
  REAR / BACK and THREE-QUARTER are saved for display only.
Scale: the side figure's height = --height. FRONT and REAR/BACK use the side's metres-per-pixel
when their pixel heights agree within 10%, else they are rescaled to the side height and a
warning is recorded. --length only checks the traced side length (a warning past 10%).
"""
import argparse, json, math, os, shutil, sys
from collections import deque
import numpy as np
from PIL import Image, ImageDraw



# ---------------------------------------------------------------- masks
def background_colour(rgb):
    """The median of the sheet's border pixels (near-white, maybe off-white)."""
    b = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]]).astype(np.float32)
    return np.median(b, axis=0)


def foreground(rgb, bg, thresh):
    """Non-background pixels: far from the background colour, or clearly saturated.
    A faint grey shadow (a small, colourless drop in value) stays background."""
    f = rgb.astype(np.float32)
    diff = np.abs(f - bg).max(axis=2)
    sat = f.max(axis=2) - f.min(axis=2)
    return (diff > thresh) | (sat > max(28.0, thresh * 0.8))


def _label(mask):
    """4-connected component labels (pure Python BFS; fine for sheet-sized crops)."""
    h, w = mask.shape
    lab = np.zeros((h, w), np.int32)
    flat = mask.ravel()
    lf = lab.ravel()
    sizes = [0]
    n = 0
    for start in np.flatnonzero(flat):
        if lf[start]:
            continue
        n += 1
        lf[start] = n
        q = deque([start]); cnt = 0
        while q:
            i = q.popleft(); cnt += 1
            r, c = divmod(i, w)
            for j, ok in ((i - w, r > 0), (i + w, r < h - 1), (i - 1, c > 0), (i + 1, c < w - 1)):
                if ok and flat[j] and not lf[j]:
                    lf[j] = n; q.append(j)
        sizes.append(cnt)
    return lab, sizes


def largest_component(mask):
    lab, sizes = _label(mask)
    if len(sizes) < 2:
        return mask
    return lab == int(np.argmax(sizes[1:]) + 1)


def fill_holes(mask):
    """Every background region not reached from the border becomes foreground."""
    pad = np.pad(mask, 1, constant_values=False)
    lab, _ = _label(~pad)
    outside = lab == lab[0, 0]
    return (~outside)[1:-1, 1:-1]


# ---------------------------------------------------------------- split
LAYOUTS = {(1, 4): ('front', 'side', 'back', 'threeq'),        # the old one-row turnaround
           (2, 2): ('side', 'front', 'rear', 'top')}           # rows: side | front, rear | top


def _runs(profile, n, min_gap_frac=0.006, min_mass_frac=0.04):
    """Runs of 'on' entries of a foreground projection separated by background gutters
    -> kept [(a, b)], dropped [(a, b)] (under min_mass_frac of the largest: labels, specks)."""
    on = profile > 0
    runs, c = [], 0
    while c < n:
        if on[c]:
            s = c
            while c < n and on[c]:
                c += 1
            runs.append([s, c])
        else:
            c += 1
    gap = max(2, int(min_gap_frac * n))
    merged = []
    for r in runs:                             # a figure with a thin break (a hanging tail tip) stays one
        if merged and r[0] - merged[-1][1] < gap:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    mass = [int(profile[a:b].sum()) for a, b in merged]
    if not mass:
        return [], []
    keep = [(a, b) for (a, b), m in zip(merged, mass) if m >= min_mass_frac * max(mass)]
    drop = [(a, b) for (a, b), m in zip(merged, mass) if m < min_mass_frac * max(mass)]
    return keep, drop


def split_views(fg):
    """Rows by horizontal gutters, then columns inside each row
    -> (view names or None, [(r0, r1, c0, c1)] or figures per row, dropped runs)."""
    h, w = fg.shape
    rp = fg.sum(axis=1)
    rp = np.where(rp > max(1, int(0.002 * w)), rp, 0)
    rows, dropped = _runs(rp, h)
    dropped = [('rows', a, b) for a, b in dropped]
    cells = []
    for r0, r1 in rows:
        cp = fg[r0:r1].sum(axis=0)
        cp = np.where(cp > max(1, int(0.004 * (r1 - r0))), cp, 0)
        cols, d = _runs(cp, w)
        dropped += [('cols', a, b) for a, b in d]
        cells.append([(r0, r1, a, b) for a, b in cols])
    shape = (len(cells), len(cells[0]) if cells else 0)
    if shape not in LAYOUTS or any(len(c) != shape[1] for c in cells):
        return None, [len(c) for c in cells], dropped
    return LAYOUTS[shape], [b for row in cells for b in row], dropped


# ---------------------------------------------------------------- contour
_NB = [(0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1)]   # clockwise (rows down)


def trace(mask):
    """Moore-neighbour trace of the outer boundary of one component -> [(row, col)] pixel centres."""
    m = np.pad(mask, 1, constant_values=False)
    rows, cols = np.nonzero(m)
    if len(rows) == 0:
        return []
    k = np.lexsort((cols, rows))[0]
    s = (int(rows[k]), int(cols[k]))
    out = [s]
    cur, back = s, 0                           # entered from the west (background)
    first = None
    for _ in range(8 * m.size):
        nxt = None
        for i in range(1, 9):
            d = (back + i) % 8
            p = (cur[0] + _NB[d][0], cur[1] + _NB[d][1])
            if m[p]:
                nxt, nd = p, d
                break
        if nxt is None:                        # an isolated pixel
            break
        if first is None:
            first = (cur, nxt)
        elif (cur, nxt) == first:
            break
        pd = (nd - 1) % 8                      # the last background neighbour checked, seen from nxt
        pb = (cur[0] + _NB[pd][0] - nxt[0], cur[1] + _NB[pd][1] - nxt[1])
        back = _NB.index(pb)
        cur = nxt
        out.append(cur)
    if len(out) > 1 and out[-1] == out[0]:
        out.pop()
    return [(r - 1, c - 1) for r, c in out]


def _dp(pts, eps):
    """Douglas-Peucker on an open polyline (numpy array Nx2)."""
    if len(pts) < 3:
        return pts
    keep = np.zeros(len(pts), bool); keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1:
            continue
        p, q = pts[a], pts[b]
        seg = q - p
        L = math.hypot(*seg)
        rel = pts[a + 1:b] - p
        d = np.abs(seg[0] * rel[:, 1] - seg[1] * rel[:, 0]) / L if L > 1e-9 else np.hypot(rel[:, 0], rel[:, 1])
        i = int(np.argmax(d))
        if d[i] > eps:
            keep[a + 1 + i] = True
            stack += [(a, a + 1 + i), (a + 1 + i, b)]
    return pts[keep]


def simplify(pts, closed, lo=40, hi=80, target=60):
    """Douglas-Peucker with the tolerance searched so the result has lo..hi points."""
    pts = np.asarray(pts, float)
    if closed:
        far = int(np.argmax(np.hypot(*(pts - pts[0]).T)))
        run = lambda e: np.vstack([_dp(pts[:far + 1], e)[:-1], _dp(np.vstack([pts[far:], pts[:1]]), e)[:-1]])
    else:
        run = lambda e: _dp(pts, e)
    a, b = 0.05, max(2.0, float(np.ptp(pts, axis=0).max()))
    best = run(a)
    if len(best) <= hi:
        return best
    for _ in range(40):
        e = (a + b) / 2
        r = run(e)
        if len(r) > hi or (len(r) > target and b - a > 0.02):
            a = e
        else:
            b = e; best = r
            if lo <= len(r) <= target:
                break
    return best


# ---------------------------------------------------------------- per view
def view_mask(rgb, bg, thresh, pad):
    fg = foreground(rgb, bg, thresh)
    fg = np.pad(fg, pad, constant_values=False)
    return fill_holes(largest_component(fg))


def bbox(mask):
    r = np.flatnonzero(mask.any(axis=1)); c = np.flatnonzero(mask.any(axis=0))
    return int(r[0]), int(r[-1]), int(c[0]), int(c[-1])


def symmetric_half(mask):
    """Half mask (column 0 = the symmetry axis) with each row's left and right half-widths
    averaged: runs on either side paired and their ends averaged; unpaired rows take the union."""
    h, w = mask.shape
    mids = []
    for r in range(h):
        c = np.flatnonzero(mask[r])
        if len(c):
            mids.append((c[0] + c[-1]) / 2.0)
    axis = float(np.median(mids))
    half_w = int(math.ceil(max(axis, w - 1 - axis))) + 2
    H = np.zeros((h, half_w), bool)

    def runs(row):
        c = np.flatnonzero(row)
        if not len(c):
            return []
        br = np.flatnonzero(np.diff(c) > 1)
        starts = np.r_[c[0], c[br + 1]]; ends = np.r_[c[br], c[-1]]
        return list(zip(starts, ends))

    for r in range(h):
        R, Lf = [], []
        for s, e in runs(mask[r]):             # pixel run [s, e] -> distances from the axis
            s0, e1 = s - 0.5 - axis, e + 0.5 - axis
            if e1 > 0:
                R.append((max(0.0, s0), e1))
            if s0 < 0:
                Lf.append((max(0.0, -e1), -s0))
        Lf.sort()
        if len(R) == len(Lf):
            iv = [((a0 + b0) / 2, (a1 + b1) / 2) for (a0, a1), (b0, b1) in zip(R, Lf)]
        else:
            iv = R + Lf
        for a0, a1 in iv:
            c0, c1 = int(round(a0)), int(round(a1))
            if c1 > c0:
                H[r, c0:c1] = True
    return H, axis


def half_outline(H):
    """Outer boundary of the half mask as an open polyline from the axis round the +x side
    back to the axis (the seam run along column 0 is cut out). Points are (row, col).
    Only the largest piece is traced: averaging the two halves row by row can leave a detached
    one-pixel spur, and the trace started on it gave the GPT giant a two-point plan outline."""
    pts = trace(fill_holes(largest_component(H)))
    n = len(pts)
    seam = [i for i, (r, c) in enumerate(pts) if c == 0]
    if not seam:
        return pts
    best, cur = None, None                     # the longest cyclic run of seam points
    on = set(seam)
    for i in seam:
        if (i - 1) % n in on:
            continue
        j = i
        while (j + 1) % n in on and (j + 1) % n != i:
            j = (j + 1) % n
        L = (j - i) % n
        if best is None or L > best[0]:
            best = (L, i, j)
    _, i, j = best
    # walk from the end of the seam round the body to its start
    out, k = [], j
    while True:
        out.append(pts[k])
        if k == i:
            break
        k = (k + 1) % n
    return out


# ---------------------------------------------------------------- main
def square_crop(img, box, cell, pad_frac=0.06):
    """A white square round one figure; only its own sheet cell (r0, r1, c0, c1) is copied."""
    white = Image.new('RGB', img.size, (255, 255, 255))
    keep = Image.new('L', img.size, 0)
    ImageDraw.Draw(keep).rectangle([cell[2], cell[0], cell[3] - 1, cell[1] - 1], fill=255)
    img = Image.composite(img, white, keep)
    r0, r1, c0, c1 = box
    side = int(max(r1 - r0, c1 - c0) * (1 + 2 * pad_frac)) + 2
    cy, cx = (r0 + r1) / 2, (c0 + c1) / 2
    out = Image.new('RGB', (side, side), (255, 255, 255))
    x0, y0 = int(round(cx - side / 2)), int(round(cy - side / 2))
    out.paste(img, (-x0, -y0))
    return out, (x0, y0)


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('sheet')
    ap.add_argument('creature_dir')
    ap.add_argument('--height', type=float, required=True, help='the side figure height in metres')
    ap.add_argument('--length', type=float, help='the expected side length in metres (a check only)')
    ap.add_argument('--thresh', type=float, default=40.0, help='background distance (0-255) for foreground')
    ap.add_argument('--force', action='store_true', help='overwrite a blueprint.json refs.py did not write')
    a = ap.parse_args()

    src = Image.open(a.sheet).convert('RGB')
    rgb = np.asarray(src)
    H_, W_ = rgb.shape[:2]
    bg = background_colour(rgb)
    fg = foreground(rgb, bg, a.thresh)
    warnings = []
    if bg.min() < 200:
        warnings.append(f'background is not near-white (median border colour {bg.round().tolist()})')
    views, cells, dropped = split_views(fg)
    if dropped:
        warnings.append(f'ignored {len(dropped)} small run(s) (labels/specks): {dropped}')
    if views is None:
        sys.exit(f'refs.py: FAIL: found figures per row {cells}; expected a 1 x 4 row (FRONT, SIDE, BACK, '
                 f'THREE-QUARTER) or a 2 x 2 grid (SIDE, FRONT / REAR, TOP) separated by white gutters. '
                 f'Crop or regenerate the sheet, or adjust --thresh.')
    layout = '1x4' if views[0] == 'front' else '2x2'

    pad, M = 2, 8
    info = {}
    for name, (r0, r1, c0, c1) in zip(views, cells):
        R0, R1, C0, C1 = max(0, r0 - M), min(H_, r1 + M), max(0, c0 - M), min(W_, c1 + M)
        mask = view_mask(rgb[R0:R1, C0:C1], bg, a.thresh, pad)
        b = bbox(mask)
        info[name] = dict(mask=mask, off=(C0 - pad, R0 - pad), box=b, hpx=b[1] - b[0], wpx=b[3] - b[2],
                          cell=(R0, R1, C0, C1))

    s_side = a.height / info['side']['hpx']
    scale = {n: s_side for n in views}
    for name in ('front', 'back', 'rear'):
        if name in info:
            ratio = info[name]['hpx'] / info['side']['hpx']
            if abs(ratio - 1) > 0.10:
                scale[name] = a.height / info[name]['hpx']
                warnings.append(f'{name} height is {ratio:.2f} x the side height: rescaled to the side height')
    by_row = {}                                # one ground line per sheet row (the plan view has none)
    for n in views:
        if n != 'top':
            by_row.setdefault(info[n]['cell'][0], {})[n] = info[n]['box'][1] + info[n]['off'][1]
    for g in by_row.values():
        if len(g) > 1 and max(g.values()) - min(g.values()) > 0.03 * info['side']['hpx']:
            warnings.append(f'the feet are not on one ground line (sheet rows {g})')

    # side: (row, col) -> (y, z); head (the image's left) at -Y, as the kit's az090 view
    sm = info['side']
    r0, r1, k0, k1 = sm['box']
    cyp = (k0 + k1) / 2
    side_px = simplify(trace(sm['mask']), closed=True)
    side = [[round((c - cyp) * s_side, 3), round((r1 - r) * s_side, 3)] for r, c in side_px]
    L = (k1 - k0) * s_side
    if a.length and abs(L / a.length - 1) > 0.10:
        warnings.append(f'traced side length {L:.2f} m vs --length {a.length:.2f} m ({L / a.length:.2f} x)')
    head_z = min(side, key=lambda p: p[0])[1]

    # front: symmetrised half outline (x >= 0); the image right is +X, as the kit's az000 view
    fm = info['front']
    Hf, f_axis = symmetric_half(fm['mask'])
    sf = scale['front']
    front_px = simplify(half_outline(Hf), closed=False, lo=20, hi=50, target=40)
    front = [[round(max(0.0, c) * sf, 3), round((fm['box'][1] - r) * sf, 3)] for r, c in front_px]
    front[0][0] = front[-1][0] = 0.0
    W = 2 * max(p[0] for p in front)

    # top (2 x 2 only): plan view, head on the image's left (-Y), left flank at the image bottom (+X).
    # Symmetrised about its long axis on the transposed mask (rows of T = sheet columns = y,
    # columns of T = sheet rows = +X downwards); the side's metres per pixel; bbox centred on y = 0.
    top = top_px = t_axis = None
    if 'top' in info:
        tm = info['top']
        Ht, t_axis = symmetric_half(tm['mask'].T)
        top_px = simplify(half_outline(Ht), closed=False, lo=20, hi=50, target=40)
        tcy = (tm['box'][2] + tm['box'][3]) / 2
        top = [[round(max(0.0, c) * s_side, 3), round((r - tcy) * s_side, 3)] for r, c in top_px]
        top[0][0] = top[-1][0] = 0.0
        if len(top) < 6 or max(p[0] for p in top) <= 0:
            warnings.append(f'top trace degenerate ({len(top)} points): omitted; redraw it by hand or regenerate the sheet')
            top = top_px = None
    if top:
        Lt = tm['wpx'] * s_side
        if abs(Lt / L - 1) > 0.10:
            warnings.append(f'top-view length {Lt:.2f} m vs side length {L:.2f} m ({Lt / L:.2f} x)')
        Wt = 2 * max(p[0] for p in top)
        if abs(Wt / W - 1) > 0.10:
            warnings.append(f'top-view width {Wt:.2f} m vs front width {W:.2f} m ({Wt / W:.2f} x)')

    cdir = os.path.abspath(a.creature_dir)
    os.makedirs(cdir, exist_ok=True)
    bpath = os.path.join(cdir, 'blueprint.json')
    if os.path.exists(bpath) and not a.force:
        old = json.load(open(bpath))
        if old.get('source') != 'refs.py':
            sys.exit(f'refs.py: {bpath} exists and was not traced by refs.py; pass --force to overwrite')
    bp = {'side': {'outline': side, 'marks': {}}, 'front': {'outline': front}}
    if top:
        bp['top'] = {'outline': top}
    bp['source'] = 'refs.py'
    bp['note'] = ('traced from reference/sheet.png; side and top bboxes centred on y = 0, feet on z = 0; '
                  + ('top traced from the plan view; ' if top else 'top omitted (no plan view); ')
                  + 'add marks by hand from the reference views')
    json.dump(bp, open(bpath, 'w'))

    # reference/: the sheet, square crops, the trace overlay, refs.json
    rdir = os.path.join(cdir, 'reference')
    os.makedirs(rdir, exist_ok=True)
    if os.path.abspath(a.sheet) != os.path.join(rdir, 'sheet.png'):
        src.save(os.path.join(rdir, 'sheet.png'))
    crops = {}
    for name in views:
        r0_, r1_, k0_, k1_ = info[name]['box']
        ox, oy = info[name]['off']
        box = (r0_ + oy, r1_ + oy, k0_ + ox, k1_ + ox)
        im, origin = square_crop(src, box, info[name]['cell'])
        im.save(os.path.join(rdir, f'{name}.png'))
        crops[name] = dict(box_rows_cols=list(box), crop_origin=list(origin), crop_size=im.width)

    # trace.png: the traced outlines drawn back over their views
    panels = []
    for name, pts in (('side', side_px), ('front', front_px), ('top', top_px)):
        if pts is None:
            continue
        ox, oy = info[name]['off']
        x0, y0 = crops[name]['crop_origin']
        im = Image.open(os.path.join(rdir, f'{name}.png')).convert('RGB')
        d = ImageDraw.Draw(im)
        if name == 'front':                    # the half (image right = +X) and its mirror
            ax = f_axis + ox - x0
            poly = [(ax + c, r + oy - y0) for r, c in pts]
            poly = poly + [(2 * ax - x, y) for x, y in reversed(poly)]
        elif name == 'top':                    # the half (image down = +X) and its mirror
            ay = t_axis + oy - y0
            poly = [(r + ox - x0, ay + c) for r, c in pts]
            poly = poly + [(x, 2 * ay - y) for x, y in reversed(poly)]
        else:
            poly = [(c + ox - x0, r + oy - y0) for r, c in pts]
        wline = max(2, im.width // 220)
        d.line(poly + [poly[0]], fill=(220, 20, 20), width=wline)
        for x, y in poly:
            d.ellipse([x - wline, y - wline, x + wline, y + wline], fill=(20, 20, 220))
        panels.append(im.resize((600, 600), Image.LANCZOS))
    tr = Image.new('RGB', (600 * len(panels), 600), (255, 255, 255))
    for i, p in enumerate(panels):
        tr.paste(p, (600 * i, 0))
    tr.save(os.path.join(rdir, 'trace.png'))
    if 'top' in views:                         # shown as the kit's top render shows it: head up, +X on the left
        tp = os.path.join(rdir, 'top.png')
        Image.open(tp).rotate(-90).save(tp)
        crops['top']['rotated'] = 'CW 90 (head up, left flank on the image left, as the kit top view)'

    meta = dict(source=os.path.basename(a.sheet), layout=layout, views=list(views), sheet_size=list(src.size),
                background_rgb=bg.round().tolist(), thresh=a.thresh, height_m=a.height, length_arg=a.length,
                metres_per_pixel={k: round(v, 6) for k, v in scale.items()},
                figure_px_w_h={n: [info[n]['wpx'], info[n]['hpx']] for n in views},
                cells_rows_cols={n: list(map(int, info[n]['cell'])) for n in views},
                traced=dict(side_points=len(side), front_points=len(front), top_points=len(top) if top else 0,
                            length_m=round(L, 3), width_m=round(W, 3), head_end_z=head_z),
                crops=crops, warnings=warnings)
    json.dump(meta, open(os.path.join(rdir, 'refs.json'), 'w'), indent=1)
    print(f'refs: {layout} sheet ({", ".join(views)}); side {len(side)} pts, front {len(front)} pts'
          + (f', top {len(top)} pts' if top else '') + f'; height {a.height:.3f} m, length {L:.3f} m, width {W:.3f} m')
    for w_ in warnings:
        print('refs WARNING:', w_)
    def _rel(p):                    # relpath fails across drives (a C: temp dir from a D: checkout)
        try:
            return os.path.relpath(p)
        except ValueError:
            return p
    print('refs: wrote', _rel(bpath), 'and', _rel(rdir))
    return 0


if __name__ == '__main__':
    sys.exit(main())
