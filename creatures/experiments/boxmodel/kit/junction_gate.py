#!/usr/bin/env python3
"""junction_gate.py — the junction probe, eye check and membrane check on a GLB, plus the zoomed
junction crop sheet the reviewer reads every round (kit/junctions.py does the measuring in Blender).

    py -3.11 creatures/experiments/boxmodel/kit/junction_gate.py <glb> <outdir> [--tag s4_r03] [--no-render]
                                                                   [--no-posed] [--title fox]

Writes <outdir>/<tag>_junctions.json, the crops <outdir>/<tag>_j<i>_<A|B|C>_beauty.png (and _flags),
and <outdir>/<tag>_junction_sheet.jpg: one row per junction root (three zoomed beauty angles, then the
flag heatmap from the same three angles), then the eyes (front, 3/4, side). run.py <prog> --stage N --junctions calls gate().
Exit 0 only when every junction, eye and membrane gate passed.

Flag colours (heatmap tile): cyan open edge, red knife fold, yellow seam strip, orange slit,
magenta poke-through, blue gap, pink posed clip, teal thin membrane, green shoulder shelf,
purple pinch (warn),
off-white = the probed region.
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw

KIT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, KIT)
import run as R

LEGEND = [('open edge', (26, 204, 242)), ('knife fold', (235, 26, 26)), ('seam strip', (255, 217, 26)),
          ('slit', (255, 128, 13)), ('poke-through', (235, 26, 217)), ('gap', (38, 77, 255)),
          ('posed clip', (255, 140, 178)), ('thin membrane', (0, 140, 140)), ('shoulder shelf', (89, 204, 51)),
          ('pinch (warn)', (140, 38, 217)),
          ('probed region', (237, 237, 230))]


def _legend(w):
    im = Image.new('RGB', (w, 30), (255, 255, 255))
    d = ImageDraw.Draw(im)
    x = 8
    for name, c in LEGEND:
        d.rectangle([x, 8, x + 14, 22], fill=c, outline=(60, 60, 60))
        d.text((x + 19, 7), name, fill=(0, 0, 0), font=R.font(14))
        x += 26 + int(R.font(14).getlength(name)) + 12
    return im


def compose(rep, outdir, tag, title, tile=260):
    rows = []
    for i, j in enumerate(rep['junctions']):
        tiles = [os.path.join(outdir, f'{tag}_j{i}_{v}_{m}.png') for m in ('beauty', 'flags') for v in rep['views'][f'j{i}']]
        head = (f"{'PASS' if j['ok'] else 'FAIL'}  {j['name']} ({j['kind']}, r {j['r_mm']} mm): knife {j['knife_edges']} "
                f"(max {j['max_concave_deg']} deg), strip {j.get('strip_max_len_r', 0)} r, slit {j['slit_pct']}%, "
                f"open {j['open_edges']}, poke {j['poke_tris']}, gaps {len(j['gaps'])}"
                + (f", clip {j['clip_pct']}%" if 'clip_pct' in j else '')
                + (f", shelf {j['shelf_area_r2']} r2/{j['shelf_width_r']} r" if 'shelf_area_r2' in j else ''))
        rows.append((head, j['fail'], tiles, j['ok']))
    for e in rep['eyes']:
        if 'visible' not in e:
            rows.append((f"FAIL eye: {'; '.join(e['fail'])}", [], [], False))
            continue
        tiles = [os.path.join(outdir, f"{tag}_eye{e['side']}_{v}_beauty.png") for v in ('front', 'threeq', 'side')]
        head = (f"{'PASS' if e['ok'] else 'FAIL'}  eye {e['side']}: visible front/3q/side {e['visible']['front']}/"
                f"{e['visible']['threeq']}/{e['visible']['side']}, diam {e['diam_mm']} mm = {e.get('diam_head')} head, "
                f"round {e['round']}, proud {e['proud_mm']} mm")
        rows.append((head, e['fail'], tiles, e['ok']))
    W = 6 * tile + 7 * 6
    ims = []
    t = Image.new('RGB', (W, 64), (255, 255, 255))
    d = ImageDraw.Draw(t)
    d.text((8, 6), f"{title}: junction probe {'PASS' if rep['ok'] else 'FAIL'}  ({tag})", fill=(0, 0, 0), font=R.font(24))
    mem = '; '.join(f"{'PASS' if x['ok'] else 'FAIL'} membrane {x['target']} p10 {x['p10_mm']} mm (floor {x['floor_mm']})"
                    for x in rep['membranes']) or 'no membranes'
    mem += ''.join(f"; {'PASS' if x['ok'] else 'WARN'} band {x['piece']} lifted {x['lifted_pct']}%" for x in rep.get('seats', []))
    d.text((8, 38), f"body open edges {rep['body']['open_edges']}, non-manifold {rep['body']['nonmanifold_edges']}; {mem}"[:200],
           fill=(0, 0, 0), font=R.font(15))
    ims += [t, _legend(W)]
    for head, fail, tiles, ok in rows:
        hh = 26 + (20 if fail else 0)
        im = Image.new('RGB', (W, hh + (tile + 6 if tiles else 0)), (255, 255, 255))
        d = ImageDraw.Draw(im)
        d.text((8, 4), head[:170], fill=(0, 110, 0) if ok else (190, 0, 0), font=R.font(16))
        if fail:
            d.text((8, 24), ('<< ' + '; '.join(fail))[:180], fill=(190, 0, 0), font=R.font(15))
        for k, p in enumerate(tiles):
            if os.path.exists(p):
                im.paste(Image.open(p).convert('RGB').resize((tile, tile)), (6 + k * (tile + 6), hh))
        ims.append(im)
    path = os.path.join(outdir, f'{tag}_junction_sheet.jpg')
    R.vstack(ims, path)
    return path


def gate(glb, outdir, scr, tag='probe', title='', render=True, posed=True):
    """Run the probe in headless Blender; returns (ok, BMK lines, report dict or None, sheet path or None)."""
    os.makedirs(outdir, exist_ok=True)
    args = [glb, outdir, '--tag', tag] + ([] if render else ['--no-render']) + ([] if posed else ['--no-posed'])
    rc, lines, tb = R.blender(os.path.join(KIT, 'junctions.py'), args, os.path.join(scr, f'junctions_{tag}.log'))
    jp = os.path.join(outdir, f'{tag}_junctions.json')
    if tb or not os.path.exists(jp):
        return False, lines + tb, None, None
    rep = json.load(open(jp, encoding='utf-8'))
    sheet = compose(rep, outdir, tag, title or os.path.splitext(os.path.basename(glb))[0]) if render else None
    return bool(rep['ok']), lines, rep, sheet


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__); return 2
    glb, out = os.path.abspath(a[0]), os.path.abspath(a[1])
    tag = a[a.index('--tag') + 1] if '--tag' in a else 'probe'
    title = a[a.index('--title') + 1] if '--title' in a else ''
    ok, lines, rep, sheet = gate(glb, out, out, tag, title, render='--no-render' not in a, posed='--no-posed' not in a)
    for l in lines:
        print(l)
    if sheet:
        print('BMK junction sheet:', sheet)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
