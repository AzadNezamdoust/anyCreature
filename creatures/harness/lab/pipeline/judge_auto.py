"""judge_auto.py - one-command blind judge round: render -> cheap gates -> blind pack -> Opus judge -> delta vs control -> RESULTS.

    python judge_auto.py --round wolf_r1 --species wolf --ref E:/gen3d/inbox/wolf/work/ref_rgba.png \
        [--cands a.obj b.obj ... | --candidates-json E:/gen3d/inbox/wolf/work/candidates.json] [--judges 2] [--no-judge]

Fixed every round (outside git, E:/gen3d/judge_auto/fixed/):
  anchor_<species>.png   AAA anchor sheet (Azad supplies; judged blind as one more id - sanity: must score high)
  control_<species>.obj  frozen control mesh (default: first run copies E:/gen3d/assets/<species>/hi.obj; sha1 logged)
Steps: render.py sheet (GPU path) per mesh -> gates.py (venv) -> only PASSING candidates + control + anchor are copied
as <rand id>.png (no titles, no metadata) into E:/gen3d/judge_auto/<round>/blind/ ; key.json stays one level up.
Judge: Claude Code headless Opus (`claude -p --model opus`, Read only) scores every id 1-10 vs AAA game-asset quality.
--judges K repeats with independently shuffled ids and averages (judge noise ~0.7 per read; delta < 1.0 = noise).
Report: per-candidate mean, delta vs control, anchor score; appended to harness/lab/RESULTS.md '## Auto-judge log'.
"""
import argparse, hashlib, json, os, random, re, shutil, subprocess, sys, time
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(HERE)
G = 'E:/gen3d'; VENV = f'{G}/venv/Scripts/python.exe'; ROOT = f'{G}/judge_auto'; FIX = f'{ROOT}/fixed'
CLAUDE = os.environ.get('CLAUDE_BIN') or shutil.which('claude') or os.path.expanduser('~/.local/bin/claude.exe')
NOISE = 0.7

PROMPT = """You are judging 3D creature assets for a AAA game, blind. Use the Read tool to open EVERY image below.
Each image is a render sheet of one untextured mesh (top row shaded 3/4 front, side, 3/4 back; bottom row silhouettes
side/front/top) - except possibly one that is a reference AAA asset. Intended creature: {species}.
Score each image 1-10 for geometry quality vs a shipped AAA game asset of that creature (anatomy, proportions,
silhouette, surface cleanliness, limb separation, detail). 10 = AAA. Be consistent across images; use the full range.
Images:
{imgs}
Reply ONLY with lines exactly like:
<id>: <score> | <main defect in <=12 words>
one line per image, nothing else."""


def sha(p): return hashlib.sha1(open(p, 'rb').read()).hexdigest()[:12]


def render(mesh, out):
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(mesh):
        subprocess.run([sys.executable, f'{LAB}/render.py', mesh, out], cwd=LAB, check=True, capture_output=True)
    return out


def judge_once(blind, ids, species):
    imgs = '\n'.join(f'{blind}/{i}.png'.replace('\\', '/') for i in ids)
    r = subprocess.run([CLAUDE, '-p', PROMPT.format(species=species, imgs=imgs), '--model', 'opus', '--allowedTools', 'Read',
                        '--add-dir', blind], capture_output=True, text=True, encoding='utf-8', timeout=1800)
    if r.returncode or 'Not logged in' in r.stdout:   # headless Claude unavailable -> leave the prompt for an Opus lane
        open(f'{blind}/PROMPT.txt', 'w', encoding='utf-8').write(PROMPT.format(species=species, imgs=imgs))
        print(f'judge unavailable ({r.stdout.strip()[:80]}); prompt -> {blind}/PROMPT.txt; put the answers in '
              f'{os.path.dirname(os.path.dirname(blind))}/judge_{os.path.basename(blind)}.txt and rerun with --score', flush=True)
        return None, r.stdout
    return parse(r.stdout), r.stdout


def parse(out):
    sc = {}
    for m in re.finditer(r'^\s*(\d{3,4})\s*:\s*([\d.]+)\s*\|?\s*(.*)$', out, re.M): sc[m.group(1)] = (float(m.group(2)), m.group(3).strip())
    return sc


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--round', required=True); ap.add_argument('--species', required=True)
    ap.add_argument('--ref'); ap.add_argument('--cands', nargs='*', default=[]); ap.add_argument('--candidates-json')
    ap.add_argument('--anchor'); ap.add_argument('--control'); ap.add_argument('--judges', type=int, default=1)
    ap.add_argument('--no-judge', action='store_true', help='stop after gates + blind pack (judge it with an Opus lane by hand)')
    ap.add_argument('--no-log', action='store_true')
    ap.add_argument('--score', action='store_true', help='re-score an existing round from its key_j*.json + judge_j*.txt (manual Opus lane answers)')
    a = ap.parse_args(); t0 = time.time()
    if a.score: return report(a, f'{ROOT}/{a.round}', t0)
    os.makedirs(FIX, exist_ok=True); rd = f'{ROOT}/{a.round}'; blind = f'{rd}/blind'
    shutil.rmtree(blind, ignore_errors=True); os.makedirs(blind); os.makedirs(f'{rd}/sheets', exist_ok=True)
    cands = {}
    if a.candidates_json:
        for k in json.load(open(a.candidates_json))['candidates']:
            if 'error' not in k: cands[k['name']] = k['clean']
    for p in a.cands: cands[os.path.splitext(os.path.basename(p))[0] + '_' + sha(p)[:4]] = p
    control = a.control or f'{FIX}/control_{a.species}.obj'
    if not os.path.exists(control):
        src = f'{G}/assets/{a.species}/hi.obj'
        if not os.path.exists(src): sys.exit(f'no control mesh: pass --control or put one at {control}')
        shutil.copy(src, control); print('froze control', src, '->', control)
    anchor = a.anchor or f'{FIX}/anchor_{a.species}.png'
    if not os.path.exists(anchor): print(f'WARNING: no AAA anchor at {anchor} (Azad supplies) - round runs without it'); anchor = None
    # 1 render
    sheets = {n: f'{rd}/sheets/{n}.png' for n in cands}; sheets['CONTROL'] = f'{FIX}/control_{a.species}.png'
    meshes = dict(cands, CONTROL=control)
    stale = [x for n in sheets if not os.path.exists(sheets[n]) or os.path.getmtime(sheets[n]) < os.path.getmtime(meshes[n]) for x in (meshes[n], sheets[n])]
    if stale: subprocess.run([sys.executable, f'{LAB}/render.py', *stale], cwd=LAB, check=True, capture_output=True)   # one GL context
    t_render = time.time() - t0
    # 2 gates (control is gated too, for the record, but always judged)
    gj = f'{rd}/gates.json'
    subprocess.run([VENV, f'{HERE}/gates.py', *cands.values(), control] + (['--ref', a.ref] if a.ref else []) + ['--json', gj], check=True, capture_output=True)
    gates = {r['mesh']: r for r in json.load(open(gj))}
    passing = [n for n, p in cands.items() if gates[p]['pass']]
    for n, p in cands.items(): print(f"gate {'PASS' if gates[p]['pass'] else 'FAIL'} {n}: {gates[p]['fails'] or ''} sym {gates[p]['symmetry']} sil {gates[p].get('sil_iou')} thin {gates[p]['thin_parts']}")
    t_gate = time.time() - t0 - t_render
    pool = passing + ['CONTROL'] + (['ANCHOR'] if anchor else [])
    if anchor: sheets['ANCHOR'] = anchor
    # 3 blind pack(s) + judge
    for j in range(max(1, a.judges)):
        bj = f'{blind}/j{j}'; os.makedirs(bj)
        ids = random.SystemRandom().sample(range(100, 1000), len(pool)); key = dict(zip(map(str, ids), pool))
        for i, n in key.items(): Image.open(sheets[n]).convert('RGB').save(f'{bj}/{i}.png')   # re-encode: no metadata, no names
        json.dump(key, open(f'{rd}/key_j{j}.json', 'w'), indent=1)
        if a.no_judge: continue
        sc, out = judge_once(bj, list(key), a.species)
        if sc is not None: open(f'{rd}/judge_j{j}.txt', 'w', encoding='utf-8').write(out)
    json.dump(dict(control=control, anchor=anchor, gates=gates, cands=cands, passing=passing), open(f'{rd}/round.json', 'w'), indent=1)
    if a.no_judge or any(not os.path.exists(f'{rd}/judge_j{k}.txt') for k in range(max(1, a.judges))):
        print(f'blind pack ready: {blind} (keys in {rd}); render {t_render:.0f}s gates {t_gate:.0f}s'); return
    report(a, rd, t0)


def report(a, rd, t0):
    R0 = json.load(open(f'{rd}/round.json')); control, anchor, gates, cands, passing = (R0[k] for k in ('control', 'anchor', 'gates', 'cands', 'passing'))
    res = {}
    for kf in sorted(f for f in os.listdir(rd) if re.fullmatch(r'key_j\d+\.json', f)):
        jf = f'{rd}/judge_{kf[4:-5]}.txt'
        if not os.path.exists(jf): continue
        sc = parse(open(jf, encoding='utf-8').read())
        for i, n in json.load(open(f'{rd}/{kf}')).items():
            res.setdefault(n, [])
            if i in sc: res[n].append(sc[i])
    pool = list(res)
    mean = lambda L: sum(x[0] for x in L) / len(L) if L else float('nan')
    ctl = mean(res['CONTROL'])
    rows = []
    for n in pool:
        m = mean(res[n]); d = m - ctl
        flag = '' if n in ('CONTROL', 'ANCHOR') else ('BETTER' if d >= 1.0 else 'WORSE' if d <= -1.0 else 'noise')
        rows.append((n, m, d, flag, res[n][0][1] if res[n] else ''))
    rows.sort(key=lambda r: -r[1] if r[1] == r[1] else 99)
    rep = [f'### {a.round} ({time.strftime("%Y-%m-%d %H:%M")}, {a.species}, Opus x{len(next(iter(res.values()), []))}, control {os.path.basename(control)} sha {sha(control)}, '
           f'anchor {"none" if not anchor else os.path.basename(anchor)})',
           f'gates: {len(passing)}/{len(cands)} pass; failed: ' + (', '.join(f"{n} ({'; '.join(gates[p]['fails'])})" for n, p in cands.items() if not gates[p]['pass']) or 'none'),
           '| id | mean | delta vs control | verdict | defect |', '|---|---|---|---|---|']
    rep += [f'| {n} | {m:.2f} | {d:+.2f} | {f} | {df} |' for n, m, d, f, df in rows]
    rep.append(f'(delta under +-1.0 is inside judge noise ~{NOISE}; wall {time.time() - t0:.0f}s)')
    print('\n'.join(rep))
    json.dump(dict(rows=rows, gates=gates, keys_dir=rd), open(f'{rd}/report.json', 'w'), indent=1)
    if not a.no_log:
        R = f'{LAB}/RESULTS.md'; txt = open(R, encoding='utf-8').read()
        if '## Auto-judge log' not in txt: txt += '\n\n## Auto-judge log (pipeline/judge_auto.py)\n'
        open(R, 'w', encoding='utf-8').write(txt.rstrip('\n') + '\n\n' + '\n'.join(rep) + '\n')


if __name__ == '__main__':
    main()
