#!/usr/bin/env python3
"""sheetcheck — the S0 gate of workflow v4: do the side and front views of a 2x2 turnaround sheet agree?

    py -3.11 experiments/boxmodel/kit/sheetcheck.py <creature_dir> [--tol 0.02]

Reads <creature_dir>/reference/sheet.png and refs.json (kit/refs.py output) and measures, in metres in the kit
frame (feet on z = 0, the side figure's box centred on y = 0, the front figure on its symmetry axis):
  ground     the lowest figure row of each view
  eye        the centroid of the iris blobs (warm, saturated pixels in the upper head region): one in the side view
             (its y, z) and two in the front view (their x, z: the eye spacing)
  nose       the centroid of the darkest blob at the head end (side) / on the axis in the head region (front)
  skull top  side: the head outline's highest row in front of the ear (where the outline jumps up into the ear);
             front: the outline's top on the symmetry axis (the crown between the ears)
A landmark row passes when |z_side - z_front| <= tol x figure height (default 2%). Writes
<creature_dir>/s0_sheetcheck.json and prints a table; exit 0 when every row passes.
The numbers are also the face module's inputs (eye centre, spacing, nose)."""
import argparse, json, os, sys
import numpy as np
from PIL import Image


def _mask(rgb, bg, thresh):
    return np.abs(rgb - np.asarray(bg, np.float32)).max(2) > thresh


def _blobs(m, min_px=6):
    """Connected components (4-neighbour) of a boolean image: list of (rows, cols) arrays."""
    lab = np.zeros(m.shape, np.int32)
    out, nid = [], 0
    for r0, c0 in zip(*np.nonzero(m)):
        if lab[r0, c0]:
            continue
        nid += 1
        st, rr, cc = [(r0, c0)], [], []
        lab[r0, c0] = nid
        while st:
            r, c = st.pop()
            rr.append(r); cc.append(c)
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                a, b = r + dr, c + dc
                if 0 <= a < m.shape[0] and 0 <= b < m.shape[1] and m[a, b] and not lab[a, b]:
                    lab[a, b] = nid
                    st.append((a, b))
        if len(rr) >= min_px:
            out.append((np.array(rr), np.array(cc)))
    return out


def measure(cdir):
    R = json.load(open(os.path.join(cdir, 'reference', 'refs.json')))
    rgb = np.asarray(Image.open(os.path.join(cdir, 'reference', 'sheet.png')).convert('RGB'), np.float32)
    out = {}
    for name in ('side', 'front'):
        r0, r1, c0, c1 = R['crops'][name]['box_rows_cols']
        s = float(R['metres_per_pixel'][name])
        sub = rgb[r0:r1 + 1, c0:c1 + 1]
        m = _mask(sub, R['background_rgb'], float(R['thresh']))
        rows, cols = np.nonzero(m)
        ground = rows.max()
        H = (ground - rows.min() + 1) * s
        if name == 'side':
            cmid = (c1 - c0) / 2.0
            w2 = lambda r, c: ((c - cmid) * s, (ground - r) * s)
        else:
            mids = [(cs.min() + cs.max()) / 2.0 for r in np.unique(rows) for cs in [cols[rows == r]]]
            cmid = float(np.median(mids))
            w2 = lambda r, c: ((c - cmid) * s, (ground - r) * s)
        head_rows = ground - rows.min()
        top = rows.min()
        hr = (np.arange(m.shape[0])[:, None] < top + 0.42 * head_rows)          # the upper 42%: the head
        if name == 'side':                                                       # the head end is the image left
            hr = hr & (np.arange(m.shape[1])[None, :] < cols.min() + 0.30 * (cols.max() - cols.min()))
        R_, G_, B_ = sub[..., 0], sub[..., 1], sub[..., 2]
        iris = m & hr & (R_ > 120) & (R_ - B_ > 60) & (G_ > 70) & (G_ < R_ - 15) & (R_ < 235)
        # the amber iris is far more saturated than the tan muzzle: keep the most saturated blobs
        sat = (R_ - B_) / np.maximum(R_, 1)
        iris &= sat > 0.45
        bl = sorted(_blobs(iris, 4), key=lambda b: -len(b[0]))
        need = 1 if name == 'side' else 2
        eyes = [tuple(float(x) for x in w2(b[0].mean(), b[1].mean())) for b in bl[:need]]
        dark = m & hr & (sub.max(2) < 60)
        db = _blobs(dark, 10)
        if name == 'side':
            nb = min(db, key=lambda b: b[1].mean()) if db else None              # the leftmost dark blob
        else:
            near = [b for b in db if abs(b[1].mean() - cmid) * s < 0.03]
            nb = max(near, key=lambda b: len(b[0])) if near else None   # the biggest dark blob on the axis
        nose = tuple(float(x) for x in w2(nb[0].mean(), nb[1].mean())) if nb is not None else None
        if name == 'side':
            # outline top per column, from the head end back: the skull top is the highest row before the jump up
            # into the ear (a rise of > 4% of the height within 3 columns)
            tops = [(c, rows[cols == c].min()) for c in range(cols.min(), cols.min() + int(0.45 * (cols.max() - cols.min())))
                    if (cols == c).any()]
            sk = None
            for i in range(3, len(tops)):
                if tops[i - 3][1] - tops[i][1] > 0.04 * head_rows:
                    sk = tops[i - 3]
                    break
            skull = w2(sk[1], sk[0])[1] if sk else None
        else:
            cc = int(round(cmid))
            col = np.nonzero(m[:, cc - 2:cc + 3].any(1))[0]
            skull = (ground - col.min()) * s
        out[name] = dict(height=round(H, 4), ground=0.0, eyes=[[round(a, 4), round(b, 4)] for a, b in eyes],
                         nose=[round(nose[0], 4), round(nose[1], 4)] if nose else None,
                         skull_top=round(skull, 4) if skull is not None else None, axis_col=round(cmid, 1))
    return out


def gate(M, tol=0.02):
    H = M['side']['height']
    rows = {}
    ez_s = np.mean([e[1] for e in M['side']['eyes']]) if M['side']['eyes'] else None
    ez_f = np.mean([e[1] for e in M['front']['eyes']]) if M['front']['eyes'] else None
    pairs = {'ground': (0.0, 0.0), 'eye line': (ez_s, ez_f), 'skull top': (M['side']['skull_top'], M['front']['skull_top']),
             'nose': (M['side']['nose'][1] if M['side']['nose'] else None, M['front']['nose'][1] if M['front']['nose'] else None),
             'height': (M['side']['height'], M['front']['height'])}
    for n, (a, b) in pairs.items():
        if a is None or b is None:
            rows[n] = dict(side=a, front=b, diff_pct=None, ok=False)
            continue
        d = 100.0 * abs(a - b) / H
        rows[n] = dict(side=round(float(a), 4), front=round(float(b), 4), diff_pct=round(d, 2), ok=bool(d <= 100 * tol))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cdir')
    ap.add_argument('--tol', type=float, default=0.02)
    a = ap.parse_args()
    M = measure(a.cdir)
    rows = gate(M, a.tol)
    ok = all(r['ok'] for r in rows.values())
    sp = None
    if len(M['front']['eyes']) == 2:
        sp = round(abs(M['front']['eyes'][0][0] - M['front']['eyes'][1][0]), 4)
    json.dump(dict(measures=M, rows=rows, eye_spacing=sp, tol=a.tol, ok=ok),
              open(os.path.join(a.cdir, 's0_sheetcheck.json'), 'w'), indent=1)
    print('S0 sheet check (side vs front, tol %.0f%% of height)' % (100 * a.tol))
    for n, r in rows.items():
        print('  %-10s %-4s side %-8s front %-8s diff %s%%' % (n, 'PASS' if r['ok'] else 'FAIL', r['side'], r['front'], r['diff_pct']))
    print('  eyes side', M['side']['eyes'], 'front', M['front']['eyes'], 'spacing', sp)
    print('  nose side', M['side']['nose'], 'front', M['front']['nose'])
    print('S0', 'PASS' if ok else 'FAIL')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
