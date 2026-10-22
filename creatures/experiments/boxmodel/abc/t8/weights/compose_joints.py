# joint crop sheet: compose_joints.py <dirL> <tagL> <dirR> <tagR> <out.jpg> [labelL labelR]
import sys, os
from PIL import Image, ImageDraw, ImageFont
dL, tL, dR, tR, out = sys.argv[1:6]
labs = sys.argv[6:8] if len(sys.argv) > 7 else ['LEFT', 'RIGHT']
J = ['upperarm.L', 'forearm.L', 'hand.L', 'thigh.L', 'shin.L', 'foot.L']
T = 300
try:
    F = ImageFont.truetype('arial.ttf', 20)
except Exception:
    F = ImageFont.load_default()
im = Image.new('RGB', (4 * T + 30, 36 + len(J) * (T + 26)), 'white')
d = ImageDraw.Draw(im)
d.text((10, 6), labs[0], fill='black', font=F)
d.text((2 * T + 30, 6), labs[1], fill='black', font=F)
for i, j in enumerate(J):
    y = 36 + i * (T + 26)
    d.text((10, y), f'{j} at flex limit', fill='black', font=F)
    for k, (dd, tt) in enumerate(((dL, tL), (dR, tR))):
        for m, v in enumerate(('out', 'front')):
            f = os.path.join(dd, f'{tt}_joint_{j}_flex_{v}.png')
            if os.path.exists(f):
                im.paste(Image.open(f).convert('RGB').resize((T, T)), (k * (2 * T + 30) + m * T, y + 24))
im.save(out, quality=90)
print(out)
