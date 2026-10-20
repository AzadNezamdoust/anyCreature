"""PNG <-> numpy via bpy (Blender's python has numpy but no PIL). Arrays are HxWx{3,4} float 0..1, row 0 = top."""
import bpy, numpy as np

def load(path):
    im = bpy.data.images.load(path, check_existing=False)
    w, h = im.size
    a = np.empty(w * h * 4, dtype=np.float32)
    im.pixels.foreach_get(a)
    bpy.data.images.remove(im)
    return a.reshape(h, w, 4)[::-1].copy()

def save(path, arr):
    arr = np.asarray(arr, dtype=np.float32)
    if arr.shape[2] == 3:
        arr = np.concatenate([arr, np.ones(arr.shape[:2] + (1,), np.float32)], axis=2)
    h, w = arr.shape[:2]
    im = bpy.data.images.new("tmp_save", w, h, alpha=True)
    im.pixels.foreach_set(np.ascontiguousarray(arr[::-1]).ravel())
    im.filepath_raw = path
    im.file_format = 'PNG'
    im.save()
    bpy.data.images.remove(im)

def fg_mask(arr, thr=215 / 255):
    """Foreground = any pixel whose darkest channel is below thr (white page background)."""
    rgb = arr[..., :3]
    m = rgb.min(axis=2) < thr
    if arr.shape[2] == 4:
        m &= arr[..., 3] > 0.5
    return m

def resize_nearest(arr, w, h):
    H, W = arr.shape[:2]
    yi = np.minimum((np.arange(h) + 0.5) * H / h, H - 1).astype(int)
    xi = np.minimum((np.arange(w) + 0.5) * W / w, W - 1).astype(int)
    return arr[yi][:, xi]

def resize_area(arr, w, h):
    """Box-filter downscale (integer-ish factors) for nicer sheets."""
    H, W = arr.shape[:2]
    ys = np.linspace(0, H, h + 1).astype(int); xs = np.linspace(0, W, w + 1).astype(int)
    c = np.cumsum(np.cumsum(np.pad(arr, ((1, 0), (1, 0), (0, 0))), 0), 1)
    y0, y1 = ys[:-1], np.maximum(ys[1:], ys[:-1] + 1); x0, x1 = xs[:-1], np.maximum(xs[1:], xs[:-1] + 1)
    S = c[y1][:, x1] - c[y0][:, x1] - c[y1][:, x0] + c[y0][:, x0]
    return S / ((y1 - y0)[:, None, None] * (x1 - x0)[None, :, None])
