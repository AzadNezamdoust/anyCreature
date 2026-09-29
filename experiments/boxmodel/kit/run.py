#!/usr/bin/env python3
"""run.py — one round of the staged box-model loop, from the shell.

    py -3.11 experiments/boxmodel/kit/run.py <creature.py> --stage N [--round R] [--lock]
    py -3.11 experiments/boxmodel/kit/run.py <creature.py> --blueprint
    py -3.11 experiments/boxmodel/kit/run.py <creature.py> --compare

--stage   rebuilds stages 1..N in headless Blender (bmkit enforces the gates and
          the lock), writes the stage's renders, and composes the round sheet
          rounds/sN_rRR.jpg (plus stageN/sheet.jpg, the latest). The harness
          orbit (harness/outline.py) runs on the stage GLB; at stage 4 glbcheck
          runs on the final GLB.
--blueprint  draws blueprint.json (the orthographic design) to blueprint.png.
--compare    side_by_side.jpg: the shipped engine creature | the stage-1 grey
             base | the final, each from the same three views.
--review     the art director's packet, review/: 1_beauty.jpg (four EEVEE views),
             2_closeups.jpg (head, limbs, body side: colour | wire), 3_tech.jpg
             (the tech-QA heatmap, legend on it), 4_posed.jpg, techqa.json; with a
             reference/ (refs.py, settings G/O) also 5_reference.jpg: each reference
             view next to the model's beauty render from the matching angle.
When <creature>/reference/ exists, the round sheets carry the reference views as
tiles next to the matching renders (side|az090, front|az000, rear or back|az180, top|top,
threeq|hero); a view with no matching render goes at the sheet's end.

Exit 0 only when every gate passed.
"""
import argparse, json, os, shutil, subprocess, sys, glob
from PIL import Image, ImageDraw, ImageFont

KIT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(KIT, '..', '..', '..'))


def blender_exe():
    if os.environ.get('BLENDER'):
        return os.environ['BLENDER']
    found = sorted(glob.glob(os.path.join(os.environ.get('ProgramFiles', ''), 'Blender*', 'Blender 5*', 'blender.exe')))
    return found[-1] if found else (shutil.which('blender') or 'blender')


def font(sz):
    for f in ('arial.ttf', 'DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(f, sz)
        except OSError:
            pass
    return ImageFont.load_default()


def scratch_for(cdir):
    rel = os.path.relpath(cdir, os.path.join(ROOT, 'experiments', 'boxmodel'))
    s = os.path.join(ROOT, 'out', 'boxmodel', rel)
    os.makedirs(s, exist_ok=True)
    return s


def blender(script, args, log):
    cmd = [blender_exe(), '-b', '--factory-startup', '--python-exit-code', '3', '-P', script, '--'] + args
    p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    with open(log, 'w', encoding='utf-8') as f:
        f.write(p.stdout + '\n--- stderr ---\n' + p.stderr)
    lines = [l for l in p.stdout.splitlines() if l.startswith('BMK ')]
    tb = []
    if p.returncode != 0 or 'Traceback' in p.stdout + p.stderr:
        txt = (p.stdout + '\n' + p.stderr).splitlines()
        i = next((k for k, l in enumerate(txt) if 'Traceback' in l), max(0, len(txt) - 25))
        tb = txt[i:i + 40]
    return p.returncode, lines, tb


def sheet(tiles, out, cols=4, tile=400, title=None):
    """tiles: [(png_path, label)] -> one labelled JPG."""
    tiles = [(p, l) for p, l in tiles if os.path.exists(p)]
    if not tiles:
        return None
    rows = (len(tiles) + cols - 1) // cols
    top = 34 if title else 0
    im = Image.new('RGB', (cols * tile, rows * (tile + 22) + top), (245, 245, 243))
    d = ImageDraw.Draw(im)
    if title:
        d.text((8, 6), title, fill=(20, 20, 20), font=font(20))
    for i, (p, l) in enumerate(tiles):
        t = Image.open(p).convert('RGB').resize((tile, tile), Image.LANCZOS)
        x, y = (i % cols) * tile, top + (i // cols) * (tile + 22)
        im.paste(t, (x, y + 22))
        d.text((x + 6, y + 3), l, fill=(30, 30, 30), font=font(15))
    im.save(out, quality=84)
    return out


# ---------------------------------------------------------------- reference (refs.py)
REF_PAIRS = (('side', 'az090'), ('front', 'az000'), ('rear', 'az180'), ('back', 'az180'), ('top', 'top'),
             ('threeq', 'hero'))            # 2 x 2 sheets: side, front, rear, top; 1 x 4: front, side, back, threeq


def ref_views(cdir):
    """{view: png} of the traced reference sheet (settings G/O); {} when there is none."""
    rdir = os.path.join(cdir, 'reference')
    return {v: os.path.join(rdir, f'{v}.png') for v, _ in REF_PAIRS if os.path.exists(os.path.join(rdir, f'{v}.png'))}


def with_refs(tiles, cdir):
    """Each reference view goes right after the first render from its angle; unmatched ones at the end."""
    refs = ref_views(cdir)
    if not refs:
        return tiles
    out, left = [], dict(refs)
    for p, l in tiles:
        out.append((p, l))
        for v, az in REF_PAIRS:
            if v in left and f'_{az}_' in os.path.basename(p) and os.path.exists(p):
                out.append((left.pop(v), f'REFERENCE {v}'))
    return out + [(left[v], f'REFERENCE {v}') for v, _ in REF_PAIRS if v in left]


# ---------------------------------------------------------------- blueprint
def _poly(pts, half):
    """A half outline (every x >= 0 in a front/top view) is mirrored into a closed shape."""
    if half and all(p[0] >= -1e-9 for p in pts):
        return [list(p) for p in pts] + [[-p[0], p[1]] for p in reversed(pts)]
    return [list(p) for p in pts]


def bp_frame(bp):
    ys = [p[0] for p in bp['side']['outline']]; zs = [p[1] for p in bp['side']['outline']]
    xs = [abs(p[0]) for p in bp.get('front', {}).get('outline', [[0.3, 0]])]
    size = [2 * max(xs), max(ys) - min(ys), max(zs) - min(zs)]
    cen = [0.0, (max(ys) + min(ys)) / 2, (max(zs) + min(zs)) / 2]
    return dict(centre=cen, size=size, ortho=max(size) * 1.2)


def _mapper(view, frame, res):
    ppm = res / frame['ortho']
    cx, cy, cz = frame['centre']
    if view == 'side':
        f = lambda p: (p[0], p[1]); cu, cv = cy, cz            # (y, z)
    elif view == 'front':
        f = lambda p: (p[0], p[1]); cu, cv = cx, cz            # (x, z)
    else:
        f = lambda p: (-p[0], -p[1]); cu, cv = -cx, -cy        # top: (x, y) -> (-x, -y)
    def m(p):
        u, v = f(p)
        return (res / 2 + (u - cu) * ppm, res / 2 - (v - cv) * ppm)
    return m, ppm


def draw_bp(d, bp, view, frame, res, colour=(200, 30, 30), grid=True):
    m, ppm = _mapper(view, frame, res)
    if grid:
        for k in range(-40, 41):
            g = k * 0.1
            a = m((g, g))
            col = (205, 205, 205) if k % 5 else (170, 170, 170)
            d.line([(a[0], 0), (a[0], res)], fill=col, width=1)
            d.line([(0, a[1]), (res, a[1])], fill=col, width=1)
    part = bp.get(view)
    if not part:
        return None
    poly = [m(p) for p in _poly(part['outline'], view != 'side')]
    d.line(poly + [poly[0]], fill=colour, width=3)
    for name, p in part.get('marks', {}).items():
        x, y = m(p)
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=colour)
        d.text((x + 6, y - 8), name, fill=colour, font=font(13))
    return poly


def blueprint_png(cdir):
    bp = json.load(open(os.path.join(cdir, 'blueprint.json')))
    fr, res = bp_frame(bp), 640
    panels = []
    for view in ('side', 'front', 'top'):
        im = Image.new('RGB', (res, res), (252, 252, 250))
        d = ImageDraw.Draw(im)
        draw_bp(d, bp, view, fr, res)
        d.text((8, 8), f'{view}  (grid 0.1 m)', fill=(20, 20, 20), font=font(18))
        panels.append(im)
    out = Image.new('RGB', (res * 3, res), (255, 255, 255))
    for i, p in enumerate(panels):
        out.paste(p, (i * res, 0))
    path = os.path.join(cdir, 'blueprint.png')
    out.save(path)
    return path


def blueprint_overlay(cdir, sdir):
    """The model's orthographic silhouettes with the blueprint drawn over them, and the IoU of each."""
    oj = os.path.join(sdir, 'ortho.json')
    if not os.path.exists(oj):
        return None, {}
    o = json.load(open(oj))
    bp = json.load(open(os.path.join(cdir, 'blueprint.json')))
    fr, res = o['frame'], o['res']
    panels, ious = [], {}
    for view in ('side', 'front', 'top'):
        a = Image.open(os.path.join(sdir, os.path.basename(o['files'][view]))).convert('RGBA').split()[3].point(lambda x: 255 if x > 127 else 0)
        base = Image.new('RGB', (res, res), (252, 252, 250))
        base.paste((150, 150, 150), mask=a)
        d = ImageDraw.Draw(base)
        poly = draw_bp(d, bp, view, fr, res)
        if poly:
            fill = Image.new('L', (res, res), 0)
            ImageDraw.Draw(fill).polygon(poly, fill=255)
            A = a.tobytes(); B = fill.tobytes()
            inter = sum(1 for x, y in zip(A, B) if x and y)
            uni = sum(1 for x, y in zip(A, B) if x or y)
            ious[view] = round(inter / uni, 3) if uni else 0.0
        d.text((8, 8), f'{view}  IoU {ious.get(view, "-")}', fill=(20, 20, 20), font=font(18))
        panels.append(base)
    out = Image.new('RGB', (res * 3, res), (255, 255, 255))
    for i, p in enumerate(panels):
        out.paste(p, (i * res, 0))
    path = os.path.join(sdir, 'blueprint_overlay.png')
    out.save(path)
    return path, ious


# ---------------------------------------------------------------- harness
def orbit(glb, dest, scr):
    tmp = os.path.join(scr, 'orbit_' + os.path.basename(os.path.dirname(dest.rstrip('/\\'))))
    shutil.rmtree(tmp, ignore_errors=True)
    p = subprocess.run([sys.executable, os.path.join(ROOT, 'harness', 'outline.py'), glb, tmp],
                       capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=ROOT)
    os.makedirs(dest, exist_ok=True)
    for f in ('orbit_sheet.png', 'orbit_sil_sheet.png', 'metrics.json'):
        if os.path.exists(os.path.join(tmp, f)):
            shutil.copy(os.path.join(tmp, f), os.path.join(dest, f))
    tail = [l for l in p.stdout.splitlines() if l.strip()][-6:]
    return p.returncode, tail


GLBCHECK_JS = """
import { checkGLB } from '%s';
import fs from 'fs';
const r = checkGLB(fs.readFileSync(process.argv[1]));
for (const e of r.errors) console.log(`FAIL [${e.code}] ${e.msg}`);
for (const w of r.warnings) console.log(`warn [${w.code}] ${w.msg}`);
console.log(r.ok ? `OK - ${r.info.anyCreature ? 'conforming anyCreature file' : 'well-formed GLB'}, `
  + `${r.info.chunks} chunks, ${r.info.images} image(s), anims: ${r.info.animations.join('/') || 'none'}`
  : `${r.errors.length} contract violation(s)`);
process.exit(r.ok ? 0 : 1);
"""


def glbcheck(glb, out):
    # harness/glbcheck.mjs's CLI guard compares import.meta.url with 'file://' + argv[1],
    # which never matches a Windows path: run as a CLI there it checks nothing and exits 0.
    # So import checkGLB and call it.
    from pathlib import Path
    url = Path(ROOT, 'harness', 'glbcheck.mjs').as_uri()
    p = subprocess.run(['node', '--input-type=module', '-e', GLBCHECK_JS % url, glb],
                       capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=ROOT)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(p.stdout + p.stderr)
    return p.returncode, (p.stdout + p.stderr).strip().splitlines()[-4:]


LEGEND = [('valley: pinched fold', (235, 26, 26)), ('fold > 25 deg', (255, 140, 26)), ('sliver', (255, 230, 38)),
          ('passes through twice', (235, 26, 217)), ('open plate', (26, 204, 242)), ('floating', (38, 77, 255)),
          ('z-fight', (26, 217, 77)), ('posed fold-over', (140, 38, 217)), ('drifts off when posed', (153, 97, 38)),
          ('clips through when posed', (255, 140, 178)),
          ('stretches when posed', (0, 128, 128))]


def legend_strip(w):
    im = Image.new('RGB', (w, 34), (250, 250, 248))
    d = ImageDraw.Draw(im)
    x = 8
    for name, c in LEGEND:
        d.rectangle([x, 9, x + 16, 25], fill=c)
        d.text((x + 22, 8), name, fill=(20, 20, 20), font=font(15))
        x += 30 + int(8.2 * len(name))
    return im


def review(cdir, scr):
    """The art director's packet for one creature, from its last stage-4 run."""
    s4 = os.path.join(cdir, 'stage4')
    glb = glob.glob(os.path.join(s4, '*.glb'))
    if not glb:
        print('no stage-4 GLB: run --stage 4 first'); return 2
    out = os.path.join(cdir, 'review')
    os.makedirs(out, exist_ok=True)
    views = ['hero', 'az090', 'az000', 'back34']
    refs = ref_views(cdir)
    rviews = views + (['az180'] if {'back', 'rear'} & set(refs) else []) + (['top'] if 'top' in refs else [])
    # shown at the idle clip's first frame, as a game shows it (a rest pose can differ: a stance keyed in every clip)
    jobs = [dict(glb=glb[0], out=os.path.join(scr, 'review'), prefix='final', mode='beauty', views=rviews, res=900,
                 pose='idle')]
    jp = os.path.join(scr, 'review_jobs.json')
    json.dump(jobs, open(jp, 'w'), indent=1)
    rc, lines, tb = blender(os.path.join(KIT, 'render_glb.py'), ['--jobs', jp], os.path.join(scr, 'review.log'))
    if tb:
        print('\n'.join(tb)); return 2
    name = os.path.basename(cdir)
    sheet([(os.path.join(scr, 'review', f'final_{v}.png'), v) for v in views], os.path.join(out, '1_beauty.jpg'),
          cols=2, tile=780, title=f'{name}: beauty (EEVEE, idle clip frame 1, as a game shows it)')
    cl = json.load(open(os.path.join(s4, 'closeups.json'))) if os.path.exists(os.path.join(s4, 'closeups.json')) else []
    tiles = []
    for c in cl:
        tiles += [(os.path.join(s4, c['colour']), f"{c['name']} colour"), (os.path.join(s4, c['wire']), f"{c['name']} wire")]
    sheet(tiles, os.path.join(out, '2_closeups.jpg'), cols=2, tile=640, title=f'{name}: close-ups')
    t = sheet([(os.path.join(s4, f's4_{v}_tech.png'), v) for v in views], os.path.join(out, '3_tech.jpg'),
              cols=2, tile=640, title=f'{name}: tech QA heatmap (grey = clean)')
    if t:
        im = Image.open(t); lg = legend_strip(im.width)
        both = Image.new('RGB', (im.width, im.height + lg.height), (255, 255, 255))
        both.paste(lg, (0, 0)); both.paste(im, (0, lg.height)); both.save(t, quality=86)
    if os.path.exists(os.path.join(s4, 'sheet.jpg')):
        posed = sorted(glob.glob(os.path.join(s4, 'posed', '*_hero_wire.png')))
        sheet([(p_, os.path.basename(p_)[:-4]) for p_ in posed], os.path.join(out, '4_posed.jpg'), cols=3, tile=480,
              title=f'{name}: posed frames (wire), deformation check')
    if refs:
        tiles = []
        for v, az in REF_PAIRS:
            if v in refs:
                tiles += [(refs[v], f'reference {v}'), (os.path.join(scr, 'review', f'final_{az}.png'), f'model {az}')]
        sheet(tiles, os.path.join(out, '5_reference.jpg'), cols=2, tile=640,
              title=f'{name}: reference sheet view | model (beauty) from the matching angle')
    for f in ('techqa.json',):
        if os.path.exists(os.path.join(s4, f)):
            shutil.copy(os.path.join(s4, f), os.path.join(out, f))
    print('BMK review packet:', os.path.relpath(out, ROOT))
    return 0


# ---------------------------------------------------------------- main
def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument('program')
    ap.add_argument('--stage', type=int, default=0)
    ap.add_argument('--round', type=int, default=0)
    ap.add_argument('--lock', action='store_true')
    ap.add_argument('--blueprint', action='store_true')
    ap.add_argument('--compare', action='store_true')
    ap.add_argument('--no-orbit', action='store_true')
    ap.add_argument('--review', action='store_true')
    a = ap.parse_args()
    prog = os.path.abspath(a.program)
    cdir = os.path.dirname(prog)
    scr = scratch_for(cdir)

    if a.blueprint:
        print('blueprint:', blueprint_png(cdir))
        return 0

    if a.review:
        return review(cdir, scr)

    if a.compare:
        lock = json.load(open(os.path.join(cdir, 'stage1_lock.json')))
        meta = lock['meta']
        final = glob.glob(os.path.join(cdir, 'stage4', '*.glb'))
        views = ['hero', 'az090', 'az000']
        eng = os.path.join(ROOT, meta['engine_glb']) if meta.get('engine_glb') else None
        cols = [('engine', eng, 'beauty', 'shipped engine creature'),
                ('stage1', os.path.join(cdir, 'stage1', 's1.glb'), 'clay', 'stage-1 grey base (locked)'),
                ('final', final[0] if final else None, 'beauty', 'final (stage 4)')]
        jobs = [dict(glb=g, out=os.path.join(scr, 'compare'), prefix=k, mode=m, views=views, res=640)
                for k, g, m, _ in cols if g and os.path.exists(g)]
        jp = os.path.join(scr, 'compare_jobs.json')
        json.dump(jobs, open(jp, 'w'), indent=1)
        rc, lines, tb = blender(os.path.join(KIT, 'render_glb.py'), ['--jobs', jp], os.path.join(scr, 'compare.log'))
        if tb:
            print('\n'.join(tb)); return 2
        cols = [c for c in cols if c[1] and os.path.exists(c[1])]
        tiles = [(os.path.join(scr, 'compare', f'{k}_{v}.png'), f'{lab} — {v}') for v in views for k, _, _, lab in cols]
        out = sheet(tiles, os.path.join(cdir, 'side_by_side.jpg'), cols=len(cols), tile=560,
                    title=f"{meta['creature']} ({meta.get('model', '?')}): engine | stage-1 base | final")
        print('BMK side-by-side:', out and os.path.relpath(out, ROOT))
        return 0

    N = a.stage
    if N < 1:
        ap.error('--stage N (1-4), --blueprint or --compare')
    args = ['--out', cdir, '--scratch', scr, '--stage', str(N), '--round', str(a.round)]
    if a.lock:
        args.append('--lock')
    log = os.path.join(scr, f's{N}_r{a.round:02d}.log')
    rc, lines, tb = blender(prog, args, log)
    for l in lines:
        print(l)
    if tb:
        print('--- Blender error (full log: %s) ---' % log)
        print('\n'.join(tb))
        return 2
    ok = any(l.startswith('BMK OK') for l in lines)
    sdir = os.path.join(cdir, f'stage{N}')

    extra = {}
    if N == 1 and os.path.exists(os.path.join(cdir, 'blueprint.json')):
        ov, ious = blueprint_overlay(cdir, sdir)
        if ov:
            extra['blueprint IoU'] = ious
            print('BMK blueprint IoU (side/front/top):', ious)

    glbs = {1: 's1.glb', 2: 's2.glb', 3: 's3.glb'}
    meta = {}
    if N == 4:
        cands = [g for g in glob.glob(os.path.join(sdir, '*.glb'))]
        glb = cands[0] if cands else None
    else:
        glb = os.path.join(sdir, glbs[N])
    if glb and os.path.exists(glb) and not a.no_orbit:
        orc, tail = orbit(glb, os.path.join(sdir, 'orbit'), scr)
        print(f'BMK orbit (harness/outline.py) rc={orc}: ' + ' | '.join(tail[-2:]))
    if N == 4 and glb:
        grc, tail = glbcheck(glb, os.path.join(sdir, 'glbcheck.txt'))
        print(f'BMK glbcheck rc={grc}: ' + ' | '.join(tail))
        ok &= grc == 0

    # the round sheet
    t = f's{N}'
    views = ['az000', 'az045', 'az090', 'az135', 'az180', 'top', 'hero']
    tiles = []
    if N == 4:
        tiles = [(os.path.join(sdir, f's4_{v}_colour.png'), f'{v} colour') for v in ('hero', 'az090', 'az000', 'back34')]
        tiles += [(os.path.join(sdir, f's4_{v}_tech.png'), f'{v} TECH QA') for v in ('hero', 'az090', 'az000', 'back34')]
        tiles += [(os.path.join(sdir, f'close_{i}_{m}.png'), f'close-up {i} {m}') for i in range(4) for m in ('colour', 'wire')]
        tiles += [(os.path.join(sdir, f's4_{v}_wire.png'), f'{v} wire') for v in ('hero', 'az090')]
        tiles += [(p, os.path.basename(p)[:-4]) for p in sorted(glob.glob(os.path.join(sdir, 'posed', '*_hero_colour.png')))]
        tiles += [(p, os.path.basename(p)[:-4]) for p in sorted(glob.glob(os.path.join(sdir, 'posed', '*_hero_wire.png')))]
    else:
        if N == 3:
            tiles += [(os.path.join(sdir, f's3_{v}_colour.png'), f'{v} colour') for v in ('hero', 'az090', 'az000', 'az135')]
        if N >= 2:
            tiles += [(os.path.join(sdir, f's{N}_{v}_tech.png'), f'{v} TECH QA') for v in ('hero', 'az090', 'az000', 'back34')]
        tiles += [(os.path.join(sdir, f'{t}_{v}_clay.png'), v) for v in views]
        tiles += [(os.path.join(sdir, f'{t}_{v}_wire.png'), f'{v} wire') for v in ('hero', 'az090', 'az000')]
        if N == 1:
            tiles.append((os.path.join(sdir, 'blueprint_overlay.png'), 'blueprint over ortho (side|front|top)'))
    tiles = with_refs(tiles, cdir)
    os.makedirs(os.path.join(cdir, 'rounds'), exist_ok=True)
    title = f'{os.path.basename(cdir)} stage {N} round {a.round}  ' + ('gates PASS' if ok else 'gates FAIL')
    s = sheet(tiles, os.path.join(cdir, 'rounds', f's{N}_r{a.round:02d}.jpg'), cols=4, tile=400, title=title)
    if s:
        shutil.copy(s, os.path.join(sdir, 'sheet.jpg'))
        print('BMK sheet:', os.path.relpath(s, ROOT))
    print('BMK round', 'OK' if ok else 'NOT OK')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
