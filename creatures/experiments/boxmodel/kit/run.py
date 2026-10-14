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
             view next to the model's beauty render from the matching angle. A cage build also gets
             6_topology.jpg: the quad wire of the base as modelled (never the export triangles) with the
             poles, the density heatmap, and the topology table with the triangle budget per region and piece.
--blockout   the blockout sign-off packet of a cage build (META['cage']), blockout/: 1_grey.jpg and
             1_thumbs.jpg (four grey views, full size and 256 px), 2_silhouette.jpg (model | reference
             | difference, with the IoU), 3_proportions.jpg, 4_wire.jpg (joints and their loop counts),
             4_topology.jpg (quad wire over flat grey from six views and four close views, poles as dots),
             4_density.jpg and 4_aspect.jpg (heatmaps), 4_topology_table.jpg, topology.json,
             0_guide.jpg (the guide alone, grey: the base form before any cage),
             5_profiles.jpg and profiles.json (head, arm and leg profiles against the reference; 'guide' = the guide's own),
             5_rom.jpg (three range-of-motion poses on a proxy rig), blockout.json.
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
    for f in ('techqa.json', 'topology.json'):
        if os.path.exists(os.path.join(s4, f)):
            shutil.copy(os.path.join(s4, f), os.path.join(out, f))
    if os.path.exists(os.path.join(s4, 'topology.json')):               # a cage build: the base's faces as modelled
        topology_sheets(s4, json.load(open(os.path.join(s4, 'topology.json'))), name, out, '6_', final=True)
    print('BMK review packet:', os.path.relpath(out, ROOT))
    return 0


# ---------------------------------------------------------------- topology and part profiles
TOPO_LEGEND = [('quad', (200, 200, 196)), ('triangle', (245, 185, 110)), ('n-gon', (185, 150, 235)),
               ('piece', (170, 182, 198)), ('pole: valence 3', (20, 110, 255)), ('pole: valence 5', (255, 110, 0)),
               ('pole: valence 6+ (fan)', (215, 0, 190))]
DENSITY_LEGEND = [('8x smaller than the median face (dense)', (30, 70, 220)), ('median', (200, 200, 196)),
                  ('8x larger (sparse)', (220, 40, 30))]
ASPECT_LEGEND = [('up to 2:1', (200, 200, 196)), ('3:1', (240, 220, 60)), ('5:1 and over', (215, 25, 25))]


def strip(w, items, title=None):
    im = Image.new('RGB', (w, 34), (250, 250, 248))
    d = ImageDraw.Draw(im)
    x = 8
    if title:
        d.text((x, 6), title, fill=(20, 20, 20), font=font(18)); x += int(d.textlength(title, font=font(18))) + 24
    for name, c in items:
        d.rectangle([x, 9, x + 16, 25], fill=c, outline=(60, 60, 60))
        d.text((x + 22, 8), name, fill=(20, 20, 20), font=font(15))
        x += 40 + int(d.textlength(name, font=font(15)))
    return im


def grid(tiles, cols, tile):
    """[(png, label)] -> a labelled Image (missing files are skipped)."""
    tiles = [(p, l) for p, l in tiles if os.path.exists(p)]
    if not tiles:
        return None
    rows = (len(tiles) + cols - 1) // cols
    im = Image.new('RGB', (cols * tile, rows * (tile + 22)), (245, 245, 243))
    d = ImageDraw.Draw(im)
    for i, (p, l) in enumerate(tiles):
        x, y = (i % cols) * tile, (i // cols) * (tile + 22)
        im.paste(Image.open(p).convert('RGB').resize((tile, tile), Image.LANCZOS), (x, y + 22))
        d.text((x + 6, y + 3), l, fill=(30, 30, 30), font=font(15))
    return im


def vstack(ims, out=None):
    ims = [i for i in ims if i is not None]
    im = Image.new('RGB', (max(i.width for i in ims), sum(i.height for i in ims)), (250, 250, 248))
    y = 0
    for i in ims:
        im.paste(i, (0, y)); y += i.height
    if out:
        im.save(out, quality=88)
    return im


def text_image(lines, w=2400, size=17):
    """[(text, colour)] -> Image, long lines wrapped."""
    import textwrap
    rows = []
    for t, c in lines:
        rows += [(x, c) for x in (textwrap.wrap(t, int(w / (size * 0.52)), subsequent_indent='        ') or [''])]
    im = Image.new('RGB', (w, 16 + (size + 7) * len(rows)), (252, 252, 250))
    d = ImageDraw.Draw(im)
    for i, (t, c) in enumerate(rows):
        d.text((10, 8 + i * (size + 7)), t, fill=c, font=font(size))
    return im


def check_lines(checks, what):
    out = []
    for c in checks:
        gate = c['kind'] == 'gate'
        why = c.get('intended') if not c['ok'] else None                # META['intended'] waiver (bmkit.cage_gates)
        col = (20, 20, 20) if c['ok'] else ((200, 30, 30) if gate and not why else (170, 110, 0))
        out.append((f"{'GATE' if gate else 'warn'} {'PASS' if c['ok'] else 'INTENDED' if why else 'FAIL'}  {what}: {c['name']}  —  {c['detail']}"
                    + (f'  (intended: {why})' if why else ''), col))
    return out


def topology_table(T, name):
    K, G = (20, 20, 20), (90, 90, 90)
    L = [(f"{name}: topology of the cage's own faces  ({T['faces']} faces, {T['tris']} triangles; gates block the stage-1 lock)", K)]
    L += check_lines(T['checks'], 'topology') + [('', K)]
    L.append(('region        faces  tris  tri%  area%  density   edge p10 / p50 / p90 (m)    p90/p10   >3:1   >5:1   tris  n-gons', G))
    for n, r in T['regions'].items():
        e = r['edge']
        L.append((f"{n:<12} {r['faces']:>5} {r['tris']:>6} {100 * r['tri_share']:>5.0f} {100 * r['area_share']:>6.0f} {r['density']:>8.2f}x"
                  f"     {e['p10']:.3f} / {e['p50']:.3f} / {e['p90']:.3f}       {e['ratio']:>5.2f}  {r['gt3_pct']:>5.1f}% {r['gt5_pct']:>5.1f}%"
                  f"  {r['tris_n']:>4} {r['ngons']:>6}", K))
    s, a, q, p = T['size'], T['aspect'], T['nonquad'], T['poles']
    L.append((f"body: edge p90/p10 {s['edge']['ratio']:g}, face area p90/p10 {s['area']['ratio']:g}; faces over 3:1 {a['gt3_pct']:g}%, over 5:1 "
              f"{a['gt5_pct']:g}% (worst {a['worst']:g}:1); non-quads {q['tris']} triangles + {q['ngons']} n-gons ({100 * q['share']:.1f}%)", K))
    L.append((f"poles: {p['n3']} of valence 3, {p['n5']} of valence 5, {p['n6']} of valence 6+; {p['in_joint']} in joint bands {p['by_joint'] or ''}, "
              f"{p['at_roots']} at limb roots, {p['elsewhere']} elsewhere", K))
    L.append(('joints: ' + '; '.join(f"{n} {j['loops']} loops ({j['rings']} rings, spacing {j['spacing_over_width']} x width)"
                                     for n, j in T['joints'].items()), K))
    L.append(('limb roots: ' + '; '.join(f"{n}: loop {'yes' if r['loop'] else 'NO'}, {'over' if r['over_joint'] else 'below'} the joint (t {r.get('t')}), "
                                         f"flow {r['flow']:g}, {r['fans']} fans, {r['caps']} non-quads, {r['rings']} rings"
                                         for n, r in T['roots'].items()), K))
    L.append(('ring-band stacks: ' + ('; '.join(f"{x['chain']} {x['rings']} rings at {x['spacing_over_width']:g} x width" for x in T['ring_stacks']) or 'none')
              + '   face loops: ' + ', '.join(f'{n} {v}' for n, v in T['face_loops'].items()), K))
    if T.get('budget'):
        B = T['budget']
        L += [('', K), (f"triangle budget of the final model ({B['total']} triangles, pieces {100 * B['pieces_share']:.0f}%):  "
                        + ',  '.join(f"{n} {r['tris']} ({100 * r['share']:.0f}%)" for n, r in B['rows'].items()), K)]
    return text_image(L)


def topology_sheets(src, T, name, out, prefix, tag='topo', final=False):
    """Compose the topology pictures of a run: <prefix>topology.jpg (and, for a blockout, the two heatmaps and the table)."""
    lab = json.load(open(os.path.join(src, f'{tag}_shots.json')))['close'] if os.path.exists(os.path.join(src, f'{tag}_shots.json')) else []
    full = grid([(os.path.join(src, f'{tag}_wire_{v}.png'), l) for v, l in
                 (('hero', 'hero'), ('az090', 'side'), ('az000', 'front'), ('top', 'top'), ('back34', 'back 3/4'), ('under', 'under-belly'))], 3, 800)
    close = grid([(os.path.join(src, f'{tag}_close_{i}.png'), l) for i, l in enumerate(lab)], 4, 600)
    if full is None:
        return
    head = strip(2400, TOPO_LEGEND, f"{name}: quad wire, the faces as modelled (no triangulation)")
    dens = vstack([strip(2100, DENSITY_LEGEND, f'{name}: density, face area against the median'),
                   grid([(os.path.join(src, f'{tag}_density_{v}.png'), v) for v in ('hero', 'az090', 'top')], 3, 700)])
    asp = vstack([strip(2100, ASPECT_LEGEND, f'{name}: face aspect, longest / shortest edge'),
                  grid([(os.path.join(src, f'{tag}_aspect_{v}.png'), v) for v in ('hero', 'az090', 'top')], 3, 700)])
    table = topology_table(T, name)
    if final:
        vstack([head, full, close, dens, table], os.path.join(out, f'{prefix}topology.jpg'))
    else:
        vstack([head, full, close], os.path.join(out, f'{prefix}topology.jpg'))
        dens.save(os.path.join(out, f'{prefix}density.jpg'), quality=88)
        asp.save(os.path.join(out, f'{prefix}aspect.jpg'), quality=88)
        table.save(os.path.join(out, f'{prefix}topology_table.jpg'), quality=90)


def profiles_sheet(cdir, raw, P, frame, name, out):
    """5_profiles.jpg: per part the reference crop | the model crop (side view, the station cuts drawn) | the depth
    and width curves along the part (reference black, model red)."""
    sheet_png = os.path.join(cdir, 'reference', 'sheet.png')
    mp = os.path.join(raw, 'grey_side_ortho.png')
    ref = Image.open(sheet_png).convert('RGB') if os.path.exists(sheet_png) and P.get('sheet_map') else None
    mod = Image.open(mp).convert('RGB') if os.path.exists(mp) and frame else None
    S, K, R = 420, (20, 20, 20), (215, 30, 30)
    rows = []
    for pn, part in P['parts'].items():
        st = [r for r in part['stations']]
        ys = [r['at'][1] for r in st]; zs = [r['at'][2] for r in st]
        half = 0.5 * max(max(ys) - min(ys), max(zs) - min(zs)) + 0.6 * max([r['model']['depth'] for r in st if 'model' in r] or [0.1])
        cy, cz = (max(ys) + min(ys)) / 2, (max(zs) + min(zs)) / 2
        row = Image.new('RGB', (4 * S, S + 26), (252, 252, 250))
        d = ImageDraw.Draw(row)
        d.text((6, 4), f"{pn}: reference (sheet, side view)", fill=K, font=font(15))
        d.text((S + 6, 4), 'model (side view)', fill=K, font=font(15))

        def crop(img, to_px, key, col):
            (x0, y0), (x1, y1) = to_px((cy - half, cz + half)), to_px((cy + half, cz - half))
            c = img.crop((int(x0), int(y0), int(x1), int(y1))).resize((S, S), Image.LANCZOS)
            dd = ImageDraw.Draw(c)
            k = S / max(1e-9, x1 - x0)
            for r in st:
                src = r.get(key) or {}
                if 'depth' not in src:
                    continue
                cen = (r.get('guide') or r['model'])['centre'] if key == 'ref' else r['model']['centre']
                h = src['depth'] / 2
                a = to_px((cen[1] - r['w'][1] * h, cen[2] - r['w'][2] * h)); b = to_px((cen[1] + r['w'][1] * h, cen[2] + r['w'][2] * h))
                dd.line([((a[0] - x0) * k, (a[1] - y0) * k), ((b[0] - x0) * k, (b[1] - y0) * k)], fill=col, width=3)
            return c

        if ref is not None:
            m_ = P['sheet_map']['side']
            row.paste(crop(ref, lambda q: (m_['cmid'] + q[0] / m_['s'], m_['ground'] - q[1] / m_['s']), 'ref', (20, 60, 220)), (0, 26))
        if mod is not None:
            mp_, _ = _mapper('side', frame, mod.width)
            row.paste(crop(mod, mp_, 'model', R), (S, 26))
        for ci, key in enumerate(('depth', 'width')):
            ox, oy, W, H = (2 + ci) * S + 46, 26 + 30, S - 66, S - 80
            vals = [r[k_][key] for r in st for k_ in ('model', 'ref') if key in r.get(k_, {})]
            top = 1.15 * max(vals or [0.1])
            D = part['dims'][key]
            d.text(((2 + ci) * S + 8, 4), f"{'depth (side view)' if key == 'depth' else 'width (front / top view)'}, m along the part", fill=K, font=font(15))
            d.rectangle([ox, oy, ox + W, oy + H], outline=(150, 150, 150))
            d.text((ox - 40, oy - 6), f'{top:.2f}', fill=(90, 90, 90), font=font(12)); d.text((ox - 16, oy + H - 8), '0', fill=(90, 90, 90), font=font(12))
            for k_, col in (('ref', K), ('model', R)):
                pts = [(ox + r['s'] * W, oy + H - r[k_][key] / top * H) for r in st if key in r.get(k_, {}) and key in r.get('ref', {})]
                if len(pts) > 1:
                    d.line(pts, fill=col, width=3)
                for x, y in pts:
                    d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=col)
            for r in st:                                                # hidden or fused stations: a grey tick on the axis
                if r['fused'] or r['src'].get(key) == 'hidden':
                    x = ox + r['s'] * W
                    d.line([(x, oy + H - 8), (x, oy + H)], fill=(150, 150, 150), width=3)
            t = (f"taper model {D['taper_model']:g} ref {D['taper_ref']:g} ({D['taper_diff_pct']:+g}%)  tube {D['tube_model']:g} / {D['tube_ref']:g}  RMS {D['rms_pct']:g}%"
                 if 'taper_model' in D else f"no reference: {D['hidden']} stations hidden in every view")
            d.text(((2 + ci) * S + 8, 26 + S - 44), t, fill=K, font=font(13))
            d.text(((2 + ci) * S + 8, 26 + S - 24), f"{D['stations']} stations: {D['sources']['sheet']} sheet, {D['sources']['guide']} guide, {D['hidden']} hidden", fill=(90, 90, 90), font=font(13))
        rows.append(row)
        g = part['guide']
        rows.append(text_image([(f"{pn} ({' > '.join(part['joints'])}): RMS {part.get('rms_pct')}% of length, max {part.get('max_pct')}%;  the guide alone: {g['stations']} of {g['of']} stations cut cleanly"
                                 + (f", taper {g['taper']:g}, tube score {g['tube']:g}, section fill {g['fill']:g} (0.79 ellipse, 1.00 box), width/depth {g['aspect']:g}" if 'taper' in g else '')
                                 + f";  model section fill {part['model_fill']}", K)], w=4 * S, size=14))
    head = text_image([(f"{name}: part profiles: reference black / blue cuts, model red; grey ticks = station fused with the body or hidden in every view", K)]
                      + check_lines(P['checks'], 'form'), w=4 * S, size=14)
    vstack([head] + rows, out)


# ---------------------------------------------------------------- blockout sign-off
GUIDE_TILES = [('hero', 'hero'), ('az090', 'side'), ('az000', 'front'), ('top', 'top'), ('back34', 'back34')]


def blockout(cdir, scr):
    """Compose blockout/ from the raw renders of a --blockout run (bmkit.blockout_packet)."""
    import numpy as np
    raw, out = os.path.join(scr, 'blockout'), os.path.join(cdir, 'blockout')
    ip = os.path.join(out, 'blockout.json')
    if not os.path.exists(ip):
        print("no blockout.json: the program needs META['cage'] = True, META['J'] and META['plan']"); return 2
    info = json.load(open(ip))
    name = info.get('creature') or os.path.basename(cdir)
    views = ['hero', 'az090', 'az000', 'back34']
    grey = [(os.path.join(raw, f'grey_{v}_clay.png'), v) for v in views]
    sheet([(os.path.join(raw, f'guide_{v}_clay.png'), l) for v, l in GUIDE_TILES], os.path.join(out, '0_guide.jpg'), cols=3,
          tile=640, title=f'{name}: the guide alone (the base form, before any cage)')
    sheet(grey, os.path.join(out, '1_thumbs.jpg'), cols=4, tile=256)
    sheet(grey, os.path.join(out, '1_grey.jpg'), cols=2, tile=768, title=f'{name}: grey blockout (stage-1 cage)')
    # silhouettes: model | reference | difference
    sp = os.path.join(raw, 'sil.npz')
    if os.path.exists(sp):
        Z = np.load(sp)
        res = Z['model_side'].shape[0]
        vs = [v for v in ('side', 'front', 'top') if f'ref_{v}' in Z]
        im = Image.new('RGB', (3 * res, len(vs) * (res + 26) + 34), (255, 255, 255))
        d = ImageDraw.Draw(im)
        d.text((8, 6), f'{name}: silhouette  model | reference sheet | difference (red = model only, blue = sheet only)',
               fill=(20, 20, 20), font=font(20))
        for r, v in enumerate(vs):
            m, f = Z[f'model_{v}'], Z[f'ref_{v}']
            y = 34 + r * (res + 26)
            diff = np.full((res, res, 3), 255, np.uint8)
            diff[m & f] = (120, 120, 120); diff[m & ~f] = (225, 40, 40); diff[~m & f] = (40, 90, 225)
            for c, a in enumerate((np.where(m, 0, 255).astype(np.uint8), np.where(f, 0, 255).astype(np.uint8), diff)):
                im.paste(Image.fromarray(a).convert('RGB'), (c * res, y + 26))
            d.text((8, y + 4), f"{v}   IoU {info['iou'].get(v)}   (floor {info['iou_floor'].get(v)})",
                   fill=(20, 20, 20), font=font(17))
        im.save(os.path.join(out, '2_silhouette.jpg'), quality=88)
    # the proportion table
    prop = info.get('proportions') or {}
    if prop:
        lim, intended = info['limits']['proportion_pct'], info.get('intended', {})
        W, rh = 1100, 30
        im = Image.new('RGB', (W, 70 + rh * (len(prop) + 1) + 24 * len(intended) + 16), (252, 252, 250))
        d = ImageDraw.Draw(im)
        d.text((10, 8), f'{name}: proportions, model against the reference sheet (limit {lim:g}%)', fill=(20, 20, 20), font=font(20))
        for x, t in ((10, 'ratio'), (520, 'model'), (650, 'sheet'), (780, 'difference'), (930, 'verdict')):
            d.text((x, 44), t, fill=(90, 90, 90), font=font(17))
        y = 44 + rh
        for n, r in prop.items():
            bad = abs(r['diff_pct']) > lim
            verdict = 'ok' if not bad else ('intended' if n in intended else 'OFF')
            col = (20, 20, 20) if not bad else ((170, 110, 0) if n in intended else (200, 30, 30))
            for x, t in ((10, n), (520, f"{r['model']:.3f}"), (650, f"{r['sheet']:.3f}"), (780, f"{r['diff_pct']:+.1f}%"),
                         (930, verdict)):
                d.text((x, y), t, fill=col, font=font(17))
            y += rh
        for n, why in intended.items():
            d.text((10, y + 6), f'intended: {n}: {why}', fill=(170, 110, 0), font=font(15)); y += 24
        im.save(os.path.join(out, '3_proportions.jpg'), quality=90)
    # wire: the side view with the joints and their loop counts, and two 3/4 views
    wp = os.path.join(raw, 'wire_side_ortho.png')
    tiles = []
    if os.path.exists(wp) and info.get('frame'):
        im = Image.open(wp).convert('RGB')
        d = ImageDraw.Draw(im)
        m, _ = _mapper('side', info['frame'], im.width)
        for n, p in info['joints'].items():
            x, y = m((p[1], p[2]))
            d.ellipse([x - 7, y - 7, x + 7, y + 7], outline=(220, 30, 30), width=3)
            d.text((x + 10, y - 10), f"{n}: {info['loops'].get(n)} loops", fill=(200, 20, 20), font=font(18))
        jp = os.path.join(raw, 'wire_side_joints.png'); im.save(jp)
        tiles.append((jp, 'side (orthographic): joints from J and the edge loops counted at each'))
    tiles += [(os.path.join(raw, f'grey_{v}_wire.png'), f'{v} wire') for v in ('hero', 'back34')]
    sheet(tiles, os.path.join(out, '4_wire.jpg'), cols=3, tile=768,
          title=f"{name}: cage wire  {info['tris']} triangles, quad share {100 * info['quad_share']:.0f}%")
    if os.path.exists(os.path.join(out, 'topology.json')):               # quad wire sheet, heatmaps, the table
        topology_sheets(raw, json.load(open(os.path.join(out, 'topology.json'))), name, out, '4_')
    if os.path.exists(os.path.join(out, 'profiles.json')):               # head, arms, legs against the reference
        profiles_sheet(cdir, raw, json.load(open(os.path.join(out, 'profiles.json'))), info.get('frame'), name,
                       os.path.join(out, '5_profiles.jpg'))
    # range of motion
    tiles = []
    for pn in info.get('poses', {}):
        tiles += [(os.path.join(raw, f'rom_{pn}_{v}_{mode}.png'), f'{pn} {v} {mode}')
                  for v, mode in (('hero', 'clay'), ('az090', 'clay'), ('hero', 'wire'), ('az090', 'wire'))]
    rom = info.get('rom', {})
    sheet(tiles, os.path.join(out, '5_rom.jpg'), cols=4, tile=512,
          title=f"{name}: range of motion on a proxy rig  ({rom.get('flip_tris')} of {rom.get('triangles')} triangles "
                f"fold over, {rom.get('flip_area_pct')}% of area)")
    print('BMK blockout packet:', os.path.relpath(out, ROOT), '— gates', 'PASS' if info.get('gates_ok') else 'FAIL')
    return 0 if info.get('gates_ok') else 1


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
    ap.add_argument('--blockout', action='store_true')
    a = ap.parse_args()
    prog = os.path.abspath(a.program)
    cdir = os.path.dirname(prog)
    scr = scratch_for(cdir)

    if a.blueprint:
        print('blueprint:', blueprint_png(cdir))
        return 0

    if a.review:
        return review(cdir, scr)

    if a.blockout:
        rc, lines, tb = blender(prog, ['--out', cdir, '--scratch', scr, '--stage', '1', '--blockout'],
                                os.path.join(scr, 'blockout.log'))
        for l in lines:
            print(l)
        if tb:
            print('\n'.join(tb)); return 2
        return blockout(cdir, scr)

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
