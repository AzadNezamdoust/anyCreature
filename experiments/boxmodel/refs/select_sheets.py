#!/usr/bin/env python3
"""Pick each creature's reference sheet per provider (refs/PLAN.md), after fixing view directions.

    py -3.11 experiments/boxmodel/refs/select_sheets.py

Inputs: refs/audit.json (a blind vision audit of every sheet's view directions: side_head, top_head, front_ok,
rear_ok, layout_ok) and the sheets refs/<provider>/<creature>/sheet_<n>.png.
For each provider and creature, in attempt order:
  1. a sheet whose layout is broken or whose front view is not straight-on is rejected;
  2. wrong directions are fixed by orient.py (side facing right -> flip; plan view head right -> flip,
     up -> rot90ccw, down -> rot90cw); the fixed sheet is oriented_<n>.png;
  3. orient.py --fit makes the views agree as one orthographic set (front/rear scaled to the side height, the plan
     view scaled per axis to the side length and the front width; the side view is the master); a sheet that
     needs more than MAX_FIT (35%) on any view is rejected;
     Since 2026-09-28 --fit also gets the brief's length / height (--aspect): the side and plan views are stretched
     along the body to the brief's length (the 33 N/G/O builds came out 15-45% short where the sheet was);
  4. accept.py checks the fitted sheet; the first one that passes is chosen (fitted_<n>.png).
Writes refs/chosen.json and prints what still needs a new attempt.
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import accept

TOP = {'left': 'none', 'right': 'flip', 'up': 'rot90ccw', 'down': 'rot90cw'}
MAX_FIT = 0.35      # a sheet needing a larger per-view correction is too inconsistent to trust


def aspect_of(c):
    """The brief's length / height (None when the brief gives no length, e.g. the character's depth)."""
    m = re.search(r'length ([\d.]+) m', accept.BRIEFS[c]['size'])
    return round(float(m.group(1)) / accept.height_of(c), 4) if m else None


def main():
    audit = json.load(open(os.path.join(HERE, 'audit.json'), encoding='utf-8'))
    chosen, todo = {}, []
    for p in ('gemini', 'gpt'):
        for c in sorted(accept.BRIEFS):
            sheets = sorted(f for f in os.listdir(os.path.join(HERE, p, c)) if f.startswith('sheet_') and f.endswith('.png'))
            log = []
            for s in sheets:
                au = audit.get(p, {}).get(c, {}).get(s)
                if au is None:
                    log.append((s, 'not audited')); continue
                if not au.get('layout_ok', True) or not au.get('front_ok', True):
                    log.append((s, 'layout or front view wrong: ' + au.get('note', ''))); continue
                side = 'flip' if au.get('side_head') == 'right' else 'none'
                top = TOP.get(au.get('top_head'), 'none')
                if au.get('side_head') == 'unclear' or au.get('top_head') == 'unclear':
                    log.append((s, 'direction unclear')); continue
                src = os.path.join(HERE, p, c, s)
                use = os.path.join(HERE, p, c, s.replace('sheet_', 'fitted_'))
                asp = aspect_of(c)
                r = subprocess.run([sys.executable, os.path.join(HERE, 'orient.py'), src, use, '--side', side, '--top', top, '--fit']
                                   + (['--aspect', str(asp)] if asp else []), capture_output=True, text=True)
                if r.returncode:
                    log.append((s, 'orient failed: ' + (r.stdout + r.stderr).strip()[-120:])); continue
                fit = json.load(open(os.path.splitext(use)[0] + '.json'))['fit']
                raw_ok, raw = accept.check(src, c)
                ok, info = accept.check(use, c)
                tag = f"fit {fit['largest']:.0%}" + (f', side {side}' if side != 'none' else '') + (f', top {top}' if top != 'none' else '')
                if fit['largest'] > MAX_FIT:
                    ok, info = False, dict(why=f"needs a {fit['largest']:.0%} correction (limit {MAX_FIT:.0%})")
                log.append((s, ('PASS' if ok else 'FAIL ' + info.get('why', '')) + f' [{tag}]'))
                if ok:
                    chosen.setdefault(p, {})[c] = dict(sheet=os.path.basename(use), source=s, ops=dict(side=side, top=top), fit=fit,
                                                       attempts=len(sheets), raw_pass=raw_ok, raw_proportion_off=raw.get('proportion_off'))
                    break
            if c not in chosen.get(p, {}):
                todo.append((p, c))
            print(f'{p:6} {c:13} ' + ' | '.join(f'{s}: {m}' for s, m in log))
    old = json.load(open(os.path.join(HERE, 'chosen.json'))) if os.path.exists(os.path.join(HERE, 'chosen.json')) else {}
    for p, c in todo:                       # keep a recorded least-bad choice for a creature no attempt passes
        if old.get(p, {}).get(c, {}).get('over_limit'):
            chosen.setdefault(p, {})[c] = old[p][c]
    json.dump(chosen, open(os.path.join(HERE, 'chosen.json'), 'w'), indent=1)
    print('\nstill needs a new attempt:', todo or 'none')


if __name__ == '__main__':
    main()
