"""reference/side_mask.npz from the sheet's side pixels (reference/side.png), opened by 3 px so the dorsal
knob tips do not pull the fit: mask[r, c] is the pixel centred at y = y0 + c px, z = z0 - r px."""
import os
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 0.000856
ref = np.array(Image.open(os.path.join(HERE, 'reference', 'side.png')).convert('RGB')).astype(float)
m = (np.abs(ref - 254).max(2) > 40) | (ref.max(2) - ref.min(2) > 32)
yy, xx = np.mgrid[-3:4, -3:4]
m = ndimage.binary_opening(m, structure=(xx ** 2 + yy ** 2) <= 9)
np.savez_compressed(os.path.join(HERE, 'reference', 'side_mask.npz'), mask=m, y0=-328 * S, z0=620 * S, px=S)
print('side_mask', m.shape, m.mean())
