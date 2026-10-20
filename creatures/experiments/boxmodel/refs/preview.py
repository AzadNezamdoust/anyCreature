#!/usr/bin/env python3
"""Preview of the chosen sheets per provider: refs/sheets_<provider>.jpg.

    py -3.11 experiments/boxmodel/refs/preview.py

Every sheet is FITTED into its tile with its aspect ratio kept (GPT returns 3:2 and square canvases; squeezing a
3:2 sheet into a square tile made the first preview look stretched, 2026-09-28). Oriented sheets (views flipped or
rotated by orient.py) are shown as the builder will see them.
"""
import json, os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'kit'))
import run as k


def main():
    ch = json.load(open(os.path.join(HERE, 'chosen.json')))
    for p, cs in ch.items():
        t = 420
        names = sorted(cs)
        rows = (len(names) + 4) // 5
        im = Image.new('RGB', (5 * t, rows * (t + 28)), (255, 255, 255))
        d = ImageDraw.Draw(im)
        for i, c in enumerate(names):
            x, y = (i % 5) * t, (i // 5) * (t + 28)
            ops = cs[c].get('ops', {})
            fix = ', '.join(f'{v} {o}' for v, o in ops.items() if o != 'none')
            d.text((x + 6, y + 5), c.replace('_', '-') + (f'  ({fix})' if fix else ''), fill=(0, 0, 0), font=k.font(16))
            s = Image.open(os.path.join(HERE, p, c, cs[c]['sheet'])).convert('RGB')
            s.thumbnail((t - 8, t - 8), Image.LANCZOS)
            im.paste(s, (x + (t - s.size[0]) // 2, y + 28 + (t - s.size[1]) // 2))
        im.save(os.path.join(HERE, f'sheets_{p}.jpg'), quality=84)
        print('wrote', f'sheets_{p}.jpg', len(names), 'sheets')


if __name__ == '__main__':
    main()
