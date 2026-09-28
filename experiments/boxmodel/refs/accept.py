#!/usr/bin/env python3
"""Acceptance check for generated turnaround sheets (refs/PLAN.md: the first attempt that passes is used).

    py -3.11 experiments/boxmodel/refs/accept.py [--provider gemini,gpt] [--creatures a,b]

A sheet passes when:
  1. kit/refs.py ingests it as a 2 x 2 sheet (side, front, rear, top) without error;
  2. the front view is left-right symmetric: mirror IoU of its mask >= 0.85 (a three-quarter view fails);
  3. refs.py did not have to rescale front/rear to the side height (they agree within 10%);
  4. the views agree as a true orthographic set: top length vs side length and top width vs front width
     within PROP_TOL (15%). Added 2026-09-28 after the owner saw stretched GPT views.
Writes refs/accept.json: per provider / creature / attempt the verdict and the numbers; prints a table.
"""
import argparse, glob, json, os, re, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(HERE, '..', 'kit')
BRIEFS = json.load(open(os.path.join(HERE, 'briefs', 'briefs.json'), encoding='utf-8'))
PROP_TOL = 0.15     # top length vs side length, top width vs front width (orchestrator's proposal; owner may change)


def height_of(c):
    return float(re.search(r'height ([\d.]+) m', BRIEFS[c]['size']).group(1))


def mirror_iou(png):
    a = np.asarray(Image.open(png).convert('L')) < 235
    ys, xs = np.nonzero(a)
    if len(xs) == 0:
        return 0.0
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    b = a[:, ::-1]
    return float((a & b).sum() / max((a | b).sum(), 1))


def check(sheet, c):
    d = tempfile.mkdtemp(prefix='accept-')
    r = subprocess.run([sys.executable, os.path.join(KIT, 'refs.py'), sheet, d, '--height', str(height_of(c))],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = dict(ingest=r.returncode == 0)
    if r.returncode != 0:
        out['why'] = (r.stdout + r.stderr).strip().splitlines()[-1][:160] if (r.stdout + r.stderr).strip() else 'refs.py failed'
        shutil.rmtree(d, ignore_errors=True)
        return False, out
    meta = json.load(open(os.path.join(d, 'reference', 'refs.json'), encoding='utf-8'))
    layout = meta.get('layout') or meta.get('grid') or ''
    warns = meta.get('warnings', [])
    out['layout'] = layout
    out['warnings'] = warns
    front = os.path.join(d, 'reference', 'front.png')
    out['front_symmetry'] = round(mirror_iou(front), 3) if os.path.exists(front) else None
    rescaled = any('rescale' in w.lower() for w in warns)
    is2x2 = ('2' in str(layout) and 'x' in str(layout).lower()) or os.path.exists(os.path.join(d, 'reference', 'top.png'))
    # cross-view consistency of a true orthographic set: top length = side length, top width = front width
    wh = meta.get('figure_px_w_h', {})
    prop = None
    if all(v in wh for v in ('side', 'front', 'top')):
        prop = max(abs(wh['top'][0] / wh['side'][0] - 1), abs(wh['top'][1] / wh['front'][0] - 1))
        out['proportion_off'] = round(prop, 3)
    ok = is2x2 and (out['front_symmetry'] or 0) >= 0.85 and not rescaled and (prop is None or prop <= PROP_TOL)
    if not ok:
        out['why'] = ('not a 2x2 sheet' if not is2x2 else
                      f"front not symmetric ({out['front_symmetry']})" if (out['front_symmetry'] or 0) < 0.85 else
                      'front/rear height differs from side by more than 10%' if rescaled else
                      f'views disagree: top vs side/front off by {prop:.0%} (limit {PROP_TOL:.0%})')
    shutil.rmtree(d, ignore_errors=True)
    return ok, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--provider', default='gemini,gpt')
    ap.add_argument('--creatures', default=','.join(BRIEFS))
    a = ap.parse_args()
    res = json.load(open(os.path.join(HERE, 'accept.json'))) if os.path.exists(os.path.join(HERE, 'accept.json')) else {}
    for p in a.provider.split(','):
        for c in a.creatures.split(','):
            for s in sorted(glob.glob(os.path.join(HERE, p, c, 'sheet_*.png'))):
                n = os.path.basename(s)
                ok, info = check(s, c)
                res.setdefault(p, {}).setdefault(c, {})[n] = dict(ok=ok, **info)
                print(f"{p:6} {c:13} {n:12} {'PASS' if ok else 'FAIL'}  sym {info.get('front_symmetry')}  {info.get('why', '')}")
    json.dump(res, open(os.path.join(HERE, 'accept.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
