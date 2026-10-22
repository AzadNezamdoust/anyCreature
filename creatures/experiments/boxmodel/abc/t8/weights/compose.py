# side-by-side extreme-pose sheets: compose.py <dirL> <tagL> <dirR> <tagR> <out.jpg> [labelL labelR]
import sys, os
from PIL import Image, ImageDraw, ImageFont
dL, tL, dR, tR, out = sys.argv[1:6]
labs = sys.argv[6:8] if len(sys.argv) > 7 else ['LEFT', 'RIGHT']
poses = sorted({f.split('_pose_')[1].rsplit('_', 1)[0] for f in os.listdir(dL) if f.startswith(tL + '_pose_')})
T = 360
try:
    F = ImageFont.truetype('arial.ttf', 22)
except Exception:
    F = ImageFont.load_default()
W = 4 * T + 30
im = Image.new('RGB', (W, 40 + len(poses) * (T + 30)), 'white')
d = ImageDraw.Draw(im)
d.text((10, 8), labs[0], fill='black', font=F)
d.text((2 * T + 30, 8), labs[1], fill='black', font=F)
for i, p in enumerate(poses):
    y = 40 + i * (T + 30)
    d.text((10, y), p, fill='black', font=F)
    for k, (dd, tt) in enumerate(((dL, tL), (dR, tR))):
        for j, v in enumerate(('hero', 'side')):
            f = os.path.join(dd, f'{tt}_pose_{p}_{v}.png')
            if os.path.exists(f):
                im.paste(Image.open(f).convert('RGB').resize((T, T)), (k * (2 * T + 30) + j * T, y + 26))
im.save(out, quality=90)
print(out)
