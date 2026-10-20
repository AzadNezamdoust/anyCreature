#!/usr/bin/env python3
"""sweep.py — build many knob variants of one stage-1 cage program and rank them with score.py.

    py -3.11 kit/sweep.py <program.py> --knobs knobs.json --n 200 --jobs 4 --seed 0 --out <dir> [--top 6] [--resume]

knobs.json maps a dotted path inside one of the program's module-level dicts (COUNTS.trunk_mid, COUNTS.fore.hinge.0,
OFFSETS.scapula) to a list of choices, or to {"lo": a, "hi": b} (a float drawn uniformly). Variant i draws its knobs
with random.Random(seed + i). The path walks dict(...) calls, {...} literals, and tuples / lists (an integer step).

Layout under <out> (the programs import the kit three folders up, so the variants sit three deep beside one kit):
    <out>/kit/                       one shared copy of this kit
    <out>/abc/c4/<name>_v####/       the build folder copy: program (knobs rewritten), blueprint.json, reference/, part_guide.npz
    <out>/scratch/v####/             the Blender scratch of that variant
    <out>/results.jsonl              one row per variant, appended as it finishes (a killed run keeps its rows)
    <out>/top.jpg                    --top K: hero | az090 grey panels of the K best, from a full-render rerun

Each variant is built with BMK_NORENDER=1 (every picture skipped; the stage-1 gates, the silhouette masks and the
range-of-motion measure still run, so s1.glb and blockout/blockout.json are written), then scored by score.py.
A crash or a timeout (300 s) is recorded as status 'crash' with its last error line; no retries.
"""
import argparse, ast, concurrent.futures as cf, glob, json, os, random, re, shutil, subprocess, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import score as S                                            # noqa: E402

TIMEOUT = 300
KEEP = ('blueprint.json', 'part_guide.npz', 'reference')


def blender_exe():
    if os.environ.get('BLENDER'):
        return os.environ['BLENDER']
    found = sorted(glob.glob(os.path.join(os.environ.get('ProgramFiles', ''), 'Blender*', 'Blender 5*', 'blender.exe')))
    return found[-1] if found else (shutil.which('blender') or S.BLENDER)


# ---------------------------------------------------------------------------- knobs: draw and rewrite
def draw(knobs, rng):
    out = {}
    for path, spec in knobs.items():
        if isinstance(spec, dict):
            out[path] = round(rng.uniform(float(spec['lo']), float(spec['hi'])), 4)
        else:
            out[path] = rng.choice(spec)
    return out


def _step(node, key):
    """(getter, setter) of one step into a dict(...) call, a {...} literal, or a tuple / list."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'dict':
        for kw in node.keywords:
            if kw.arg == key:
                return (lambda: kw.value), (lambda v: setattr(kw, 'value', v))
    elif isinstance(node, ast.Dict):
        for i, k in enumerate(node.keys):
            if isinstance(k, ast.Constant) and str(k.value) == key:
                return (lambda: node.values[i]), (lambda v: node.values.__setitem__(i, v))
    elif isinstance(node, (ast.Tuple, ast.List)) and key.lstrip('-').isdigit():
        i = int(key)
        if -len(node.elts) <= i < len(node.elts):
            return (lambda: node.elts[i]), (lambda v: node.elts.__setitem__(i, v))
    raise KeyError(f'no step {key!r} into a {type(node).__name__}')


def _node(value, like):
    if isinstance(value, list):
        value = tuple(value) if isinstance(like, ast.Tuple) else value
        if isinstance(value, tuple):
            value = tuple(tuple(x) if isinstance(x, list) else x for x in value)
    return ast.parse(repr(value), mode='eval').body


def rewrite(src, values):
    """src with every knob path set to its value; the assignments that hold knobs are regenerated from the ast."""
    tree = ast.parse(src)
    assigns = {}
    for st in tree.body:
        if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name):
            assigns[st.targets[0].id] = st
    touched = set()
    for path, value in values.items():
        head, *rest = path.split('.')
        if head not in assigns:
            raise KeyError(f'{path}: no module-level assignment to {head}')
        node = assigns[head].value
        get = lambda n=node: n                                   # noqa: E731
        set_ = lambda v, a=assigns[head]: setattr(a, 'value', v)  # noqa: E731
        for key in rest:
            get, set_ = _step(get(), key)
        set_(_node(value, get()))
        touched.add(head)
    lines = src.split('\n')
    for head in sorted(touched, key=lambda h: -assigns[h].lineno):
        st = assigns[head]
        lines[st.lineno - 1:st.end_lineno] = [ast.unparse(st)]
    return '\n'.join(lines)


# ---------------------------------------------------------------------------- one variant
def last_error(text):
    ls = [l.rstrip() for l in text.splitlines() if l.strip()]
    tb = next((i for i, l in enumerate(ls) if 'Traceback' in l), None)
    if tb is not None:
        tail = [l for l in ls[tb:] if not l.startswith((' ', '\t'))]
        return tail[-1][:300] if tail else ls[-1][:300]
    return ls[-1][:300] if ls else 'no output'


def blender_build(prog, cdir, scr, render):
    env = dict(os.environ)
    env.pop('BMK_NORENDER', None)
    if not render:
        env['BMK_NORENDER'] = '1'
    cmd = [blender_exe(), '-b', '--factory-startup', '-t', '2', '--python-exit-code', '3', '-P', prog, '--',
           '--out', cdir, '--scratch', scr, '--stage', '1', '--blockout']
    p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', env=env,
                       timeout=TIMEOUT)
    with open(os.path.join(scr, 'build.log'), 'w', encoding='utf-8') as f:
        f.write(p.stdout + '\n--- stderr ---\n' + p.stderr)
    return p


def make_variant(a, vid, values):
    """Copy the build folder to <out>/abc/c4/<name>_<vid>/ with the knobs rewritten; return (program, dir, scratch)."""
    src_dir = os.path.dirname(os.path.abspath(a.program))
    name = os.path.basename(src_dir)
    cdir = os.path.join(a.out, 'abc', 'c4', f'{name}_{vid}')
    if os.path.isdir(cdir):
        shutil.rmtree(cdir)
    os.makedirs(cdir)
    for item in KEEP:
        s = os.path.join(src_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, os.path.join(cdir, item))
        elif os.path.isfile(s):
            shutil.copy2(s, cdir)
    prog = os.path.join(cdir, os.path.basename(a.program))
    with open(a.program, encoding='utf-8') as f:
        src = f.read()
    with open(prog, 'w', encoding='utf-8', newline='\n') as f:
        f.write(rewrite(src, values))
    scr = os.path.join(a.out, 'scratch', vid)
    if os.path.isdir(scr):
        shutil.rmtree(scr)
    os.makedirs(scr)
    return prog, cdir, scr


def run_variant(a, i, knobs):
    vid = 'v%04d' % i
    values = draw(knobs, random.Random(a.seed + i))
    row = dict(id=vid, knobs=values, status='crash')
    t0 = time.time()
    try:
        prog, cdir, scr = make_variant(a, vid, values)
        try:
            p = blender_build(prog, cdir, scr, render=False)
        except subprocess.TimeoutExpired:
            row['error'] = f'timeout after {TIMEOUT} s'
            return row
        s1, bo = os.path.join(cdir, 'stage1', 's1.glb'), os.path.join(cdir, 'blockout', 'blockout.json')
        if not (os.path.isfile(s1) and os.path.isfile(bo)):
            row['error'] = last_error(p.stdout + '\n' + p.stderr)
            return row
        r = S.score_build(cdir)
        row.update(status='ok', score=r['score'], gate_fail=r['gate_fail'], raw=r['raw'], mapped=r['mapped'],
                   build_gates_ok=json.load(open(bo)).get('gates_ok'))
    except Exception as e:                                       # a crash of the harness side, recorded like any other
        row['error'] = (str(e).strip().splitlines() or [type(e).__name__])[-1][:300]
    finally:
        row['secs'] = round(time.time() - t0, 1)
    return row


# ---------------------------------------------------------------------------- top K: full renders and top.jpg
def rerun_full(a, row):
    vid = row['id']
    name = os.path.basename(os.path.dirname(os.path.abspath(a.program)))
    cdir = os.path.join(a.out, 'abc', 'c4', f'{name}_{vid}')
    prog = os.path.join(cdir, os.path.basename(a.program))
    scr = os.path.join(a.out, 'scratch', vid)
    os.makedirs(scr, exist_ok=True)
    try:
        blender_build(prog, cdir, scr, render=True)
    except subprocess.TimeoutExpired:
        return None
    return cdir, scr


def compose_top(a, rows):
    from PIL import Image, ImageDraw
    sys.path.insert(0, os.path.join(a.out, 'kit'))
    import run as R                                              # the shared kit copy: blockout() composes 1_grey.jpg
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        done = list(ex.map(lambda r: rerun_full(a, r), rows))
    tiles = []
    for r, d in zip(rows, done):
        if not d:
            continue
        cdir, scr = d
        try:
            R.blockout(cdir, scr)
        except Exception as e:
            print('blockout composing failed for', r['id'], str(e)[:120])
        gp = os.path.join(cdir, 'blockout', '1_grey.jpg')
        if os.path.isfile(gp):
            tiles.append((r, Image.open(gp).convert('RGB')))
    if not tiles:
        print('top.jpg: no renders')
        return None
    T, head, lab = 480, 34, 26
    im = Image.new('RGB', (2 * T, head + len(tiles) * (T + lab)), (245, 245, 243))
    d = ImageDraw.Draw(im)
    d.text((8, 8), f'top {len(tiles)} of the sweep: hero | az090', fill=(20, 20, 20), font=R.font(18))
    for k, (r, g) in enumerate(tiles):
        y = head + k * (T + lab)
        gate = ('  GATE ' + ','.join(r['gate_fail'])) if r['gate_fail'] else ''
        d.text((8, y + 4), '%s   score %.2f%s' % (r['id'], r['score'], gate), fill=(20, 20, 20), font=R.font(16))
        for c, x0 in enumerate((0, 768)):                        # 1_grey.jpg: 2 x 2 tiles of 768 under a 34 px title, 22 px labels
            panel = g.crop((x0, 34 + 22, x0 + 768, 34 + 22 + 768)).resize((T, T))
            im.paste(panel, (c * T, y + lab))
    out = os.path.join(a.out, 'top.jpg')
    im.save(out, quality=88)
    return out


# ---------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('program')
    ap.add_argument('--knobs', required=True)
    ap.add_argument('--n', type=int, default=200)
    ap.add_argument('--jobs', type=int, default=4)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--out', required=True)
    ap.add_argument('--top', type=int, default=0)
    ap.add_argument('--resume', action='store_true')
    a = ap.parse_args()
    a.out = os.path.abspath(a.out)
    knobs = json.load(open(a.knobs, encoding='utf-8'))
    with open(a.program, encoding='utf-8') as f:
        rewrite(f.read(), draw(knobs, random.Random(a.seed)))   # a bad knob path fails here, before any Blender run
    os.makedirs(a.out, exist_ok=True)
    kit = os.path.join(a.out, 'kit')
    if not (a.resume and os.path.isdir(kit)):
        if os.path.isdir(kit):
            shutil.rmtree(kit)
        shutil.copytree(HERE, kit, ignore=shutil.ignore_patterns('__pycache__', 'selftest', '*.pyc'))
    resfile = os.path.join(a.out, 'results.jsonl')
    done = {}
    if a.resume and os.path.isfile(resfile):
        for l in open(resfile, encoding='utf-8'):
            if l.strip():
                r = json.loads(l)
                done[r['id']] = r
    else:
        open(resfile, 'w').close()
    todo = [i for i in range(a.n) if 'v%04d' % i not in done]
    lock, rows = threading.Lock(), dict(done)
    t0 = time.time()

    def work(i):
        r = run_variant(a, i, knobs)
        with lock:
            rows[r['id']] = r
            with open(resfile, 'a', encoding='utf-8') as f:
                f.write(json.dumps(r) + '\n')
            print('%s %-5s %s%s  (%d/%d)' % (r['id'], r['status'],
                  ('%.2f' % r['score']) if 'score' in r else r.get('error', ''),
                  ('  GATE ' + ','.join(r['gate_fail'])) if r.get('gate_fail') else '', len(rows), a.n), flush=True)

    with cf.ThreadPoolExecutor(a.jobs) as ex:
        list(ex.map(work, todo))
    wall = time.time() - t0

    allr = sorted(rows.values(), key=lambda r: r['id'])
    ok = [r for r in allr if r['status'] == 'ok']
    clean = sorted((r for r in ok if not r['gate_fail']), key=lambda r: -r['score'])
    gated = sorted((r for r in ok if r['gate_fail']), key=lambda r: -r['score'])
    print('\n%d variants: %d ok, %d crash, %d gate_fail (of the ok); %.0f s for %d new' % (
        len(allr), len(ok), len(allr) - len(ok), len(gated), wall, len(todo)))
    best = clean[:5] or gated[:5]
    print('best 5%s:' % ('' if clean else ' (all gated)'))
    for r in best:
        print('  %s %6.2f %s %s' % (r['id'], r['score'], ','.join(r['gate_fail']), json.dumps(r['knobs'])))
    if a.top and ok:
        pick = (clean + gated)[:a.top]                           # gated ones only fill in when too few are clean
        out = compose_top(a, pick)
        print('top.jpg:', out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
