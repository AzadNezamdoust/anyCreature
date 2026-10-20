"""Contact sheet: python montage.py <method> <budget> [suffix] [root]
Tiles the top-left (3/4 shaded) + side panels of each animal's sheet."""
import sys, os
from PIL import Image
import lp_common as C
m, b = sys.argv[1], sys.argv[2]
suf = sys.argv[3] if len(sys.argv) > 3 else ''
root = sys.argv[4] if len(sys.argv) > 4 else 'E:/gen3d/lowpoly'
tiles = []
for an in C.ANIMALS:
    p = os.path.join(root, m, f'{an}_{b}{suf}.png')
    if os.path.exists(p):
        im = Image.open(p).convert('RGB')
        tiles.append(im.crop((0, 0, im.width * 2 // 3, im.height // 2)).resize((512, 256)))
W = Image.new('RGB', (1024, 256 * ((len(tiles) + 1) // 2)), 'white')
for i, t in enumerate(tiles):
    W.paste(t, ((i % 2) * 512, (i // 2) * 256))
W.save(os.path.join(root, m, f'_montage_{b}{suf}.png'))
