"""abpair.py <dirA> <dirB> <out.jpg> [labelA labelB] [--sheet]: two candidates' renders, rows A/B, same views
(+ the concept sheet's four views as a referee row with --sheet)."""
import sys, os
from PIL import Image, ImageDraw, ImageFont
args = [a for a in sys.argv[1:] if not a.startswith('--')]
a, b, out = args[:3]
la, lb = (args[3], args[4]) if len(args) > 4 else ('A', 'B')
V = ['h000', 'h045', 'h090', 'h180', 'hero', 'top', 'u090', 'face_34']
T = 300
try:
    F = ImageFont.truetype('arial.ttf', 26)
except Exception:
    F = ImageFont.load_default()
rows = [(a, la), (b, lb)]
H = 2 * (T + 36) + (T + 36 if '--sheet' in sys.argv else 0)
im = Image.new('RGB', (T * len(V), H), 'white')
d = ImageDraw.Draw(im)
for r, (dd, lab) in enumerate(rows):
    d.text((8, r * (T + 36) + 4), lab + '   (views: ' + ', '.join(V) + ')', fill='black', font=F)
    for i, v in enumerate(V):
        p = os.path.join(dd, v + '.png')
        if os.path.exists(p):
            im.paste(Image.open(p).convert('RGB').resize((T, T)), (i * T, r * (T + 36) + 36))
if '--sheet' in sys.argv:
    ref = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'reference')
    y = 2 * (T + 36)
    d.text((8, y + 4), 'CONCEPT SHEET (referee): side, front, rear, top', fill='black', font=F)
    for i, v in enumerate(['side', 'front', 'rear', 'top']):
        im.paste(Image.open(os.path.join(ref, v + '.png')).convert('RGB').resize((T, T)), (i * T, y + 36))
im.save(out, quality=90)
print(out)
