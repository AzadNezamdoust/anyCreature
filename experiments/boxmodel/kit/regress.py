#!/usr/bin/env python3
"""regress.py: rerun every locked build to stage 4 with no renders, in scratch copies, after a kit change.

    py -3.11 experiments/boxmodel/kit/regress.py <tag> [path filter]      (J=5 parallel Blenders)

Each build's program runs from its own folder, but --out is out/boxmodel/regress/<tag>/<build>/, which gets
copies of the build's stage1_lock.json and blueprint.json, so no build folder is touched. BMK_NORENDER=1 skips
every picture: the gates and the tech QA still run.
Writes out/boxmodel/regress/<tag>.json: per build the PASS/FAIL/WARN lines and the stage-4 techqa totals.
Run it once before the change and once after, and diff the two."""
import glob, json, os, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
KIT = os.path.dirname(os.path.abspath(__file__)); BOX = os.path.dirname(KIT); ROOT = os.path.dirname(os.path.dirname(BOX))
sys.path.insert(0, KIT); import run as kitrun
tag = sys.argv[1]; filt = sys.argv[2] if len(sys.argv) > 2 else ''
progs = []
for lock in glob.glob(os.path.join(BOX, '**', 'stage1_lock.json'), recursive=True):
    d = os.path.dirname(lock); c = os.path.basename(d)
    p = os.path.join(d, c + '.py')
    if not os.path.exists(p):
        cand = [x for x in glob.glob(os.path.join(d, '*.py'))]
        if len(cand) != 1: print('skip', d, cand); continue
        p = cand[0]
    rel = os.path.relpath(d, BOX).replace(os.sep, '/')
    if filt in rel: progs.append((rel, p, d))
env = dict(os.environ, BMK_NORENDER='1')
def one(x):
    rel, p, d = x
    out = os.path.join(ROOT, 'out', 'boxmodel', 'regress', tag, rel)
    shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
    for f in ('stage1_lock.json', 'blueprint.json'):
        if os.path.exists(os.path.join(d, f)): shutil.copy(os.path.join(d, f), out)
    cmd = [kitrun.blender_exe(), '-b', '--factory-startup', '--python-exit-code', '3', '-P', p, '--',
           '--out', out, '--scratch', out, '--stage', '4']
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', env=env, timeout=1800)
    lines = [l[4:] for l in r.stdout.splitlines() if l.startswith(('BMK PASS', 'BMK FAIL', 'BMK WARN'))]
    tq = os.path.join(out, 'stage4', 'techqa.json')
    tot = json.load(open(tq))['totals'] if os.path.exists(tq) else None
    tb = [l for l in (r.stdout + r.stderr).splitlines() if 'Error' in l or 'Traceback' in l][-3:]
    print(rel, 'rc', r.returncode, sum(l.startswith('FAIL') for l in lines), 'FAIL', flush=True)
    return rel, dict(rc=r.returncode, gates=lines, totals=tot, err=tb)
with ThreadPoolExecutor(int(os.environ.get('J', '5'))) as ex:
    res = dict(ex.map(one, sorted(progs)))
json.dump(res, open(os.path.join(ROOT, 'out', 'boxmodel', 'regress', tag + '.json'), 'w'), indent=1)
