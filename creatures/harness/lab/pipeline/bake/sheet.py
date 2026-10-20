"""Comparison sheets: rows = LOD, cols = no normal | baked | baked+detail. usage: sheet.py <r19 wolf dir>"""
import sys, json, os
from PIL import Image, ImageDraw
d = sys.argv[1]; lods = [l for l in (1500, 5000, 15000) if os.path.exists(f'{d}/sheets/lod{l}_full_none.png')]
cols = [('none', 'no normal map'), ('baked', 'baked hi->lo'), ('detail', 'baked + Marigold detail')]
for shot in ('full', 'head'):
    ims = [[Image.open(f'{d}/sheets/lod{l}_{shot}_{c}.png').convert('RGB') for c, _ in cols] for l in lods]
    w, h = ims[0][0].size; S = Image.new('RGB', (w * 3, (h + 28) * len(lods) + 28), (20, 20, 22)); D = ImageDraw.Draw(S)
    for j, (_, t) in enumerate(cols): D.text((j * w + 10, 8), t, fill=(230, 230, 230))
    for i, l in enumerate(lods):
        f = json.load(open(f'{d}/lod{l}/bake_bl.json'))['faces']
        D.text((10, 28 + i * (h + 28) + 6), f'LOD QuadriFlow {l} ({f} faces)', fill=(230, 200, 120))
        for j in range(3): S.paste(ims[i][j], (j * w, 28 + i * (h + 28) + 28))
    S.save(f'{d}/compare_{shot}.png'); print(f'{d}/compare_{shot}.png')
