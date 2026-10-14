#!/usr/bin/env python3
"""Blind judging material for the N/G/O test (refs/PLAN.md).

    py -3.11 experiments/boxmodel/refs/eval_prep.py

For every creature the three builds (abc/<id>/<creature>) get random labels A/B/C; their review packets
(1_beauty, 2_closeups, 3_tech, 4_posed, techqa.json) are copied to out/boxmodel/judge/ngo/<creature>/<label>/.
5_reference.jpg and side_by_side.jpg are NOT copied: they would show which builds had a reference.
Silhouette sheets for the identity read go to out/boxmodel/judge/ngo_sil/sheet_<n>.jpg under shuffled numbers.
The key (label -> setting, sheet -> build) goes to out/boxmodel/judge/ngo_key.json, which no judge opens.
"""
import json, os, random, shutil, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
BOX = os.path.join(HERE, '..')
ROOT = os.path.abspath(os.path.join(BOX, '..', '..'))
sys.path.insert(0, os.path.join(BOX, 'kit'))
import run as kitrun

OUT = os.path.join(ROOT, 'out', 'boxmodel', 'judge')
READ = ['az000', 'az045', 'az090', 'az135', 'az180', 'top']


def main():
    key = json.load(open(os.path.join(BOX, 'abc', 'key.json')))['settings']      # id -> N/G/O
    creatures = sorted(json.load(open(os.path.join(HERE, 'briefs', 'briefs.json'), encoding='utf-8')))
    rng = random.Random(20260929)
    ngo = os.path.join(OUT, 'ngo'); sil = os.path.join(OUT, 'ngo_sil')
    shutil.rmtree(ngo, ignore_errors=True); shutil.rmtree(sil, ignore_errors=True)
    os.makedirs(sil)
    out_key = dict(labels={}, sheets={}, missing=[])
    builds = []
    for c in creatures:
        ids = list(key)
        rng.shuffle(ids)
        for lab, i in zip('ABC', ids):
            src = os.path.join(BOX, 'abc', i, c, 'review')
            if not os.path.exists(os.path.join(src, '1_beauty.jpg')):
                out_key['missing'].append(f'{i}/{c}'); continue
            dst = os.path.join(ngo, c, lab)
            os.makedirs(dst)
            for f in ('1_beauty.jpg', '2_closeups.jpg', '3_tech.jpg', '4_posed.jpg', 'techqa.json'):
                if os.path.exists(os.path.join(src, f)):
                    shutil.copy(os.path.join(src, f), os.path.join(dst, f))
            out_key['labels'][f'{c}/{lab}'] = dict(id=i, setting=key[i])
            builds.append((c, i))
    order = list(range(len(builds)))
    rng.shuffle(order)
    for n, bi in enumerate(order, 1):
        c, i = builds[bi]
        src = os.path.join(ROOT, 'out', 'boxmodel', 'abc', i, c, 'orbit_stage4')
        if not os.path.exists(os.path.join(src, 'sil_az000.png')):
            out_key['missing'].append(f'sil {i}/{c}'); continue
        t = 320
        im = Image.new('RGB', (3 * t, 2 * (t + 30)), (255, 255, 255)); d = ImageDraw.Draw(im)
        for k, v in enumerate(READ):
            x, y = (k % 3) * t, (k // 3) * (t + 30)
            d.text((x + 8, y + 4), v, fill=(0, 0, 0), font=kitrun.font(20))
            im.paste(Image.open(os.path.join(src, f'sil_{v}.png')).convert('RGB').resize((t, t), Image.LANCZOS), (x, y + 30))
        name = f'sheet_{n:02d}.jpg'
        im.save(os.path.join(sil, name), quality=88)
        out_key['sheets'][name] = dict(creature=c, id=i, setting=key[i])
    json.dump(out_key, open(os.path.join(OUT, 'ngo_key.json'), 'w'), indent=1)
    print(len(out_key['labels']), 'packets,', len(out_key['sheets']), 'silhouette sheets; missing:', out_key['missing'] or 'none')


if __name__ == '__main__':
    main()
