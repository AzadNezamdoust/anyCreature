import os, sys, time
os.environ.setdefault("HF_HOME", r"E:\gen3d\hf")
sys.path.insert(0, r"E:\gen3d\Hunyuan3D-2")
import numpy as np, torch, trimesh
from PIL import Image
from scipy import ndimage

def log(*a): print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)

PROMPT_SUFFIX = (", single creature, full body, side three-quarter view, isolated on pure white background, "
                 "no ground, no floor, no shadow, no base, no pedestal, no text")

def remove_white_bg(img, thr=235, gray_thr=200, sat_thr=18, erode=2):
    """Flood-fill bg from border: near-white OR light low-saturation gray (floor shadows); erode edge."""
    a = np.asarray(img.convert("RGB")).astype(np.int16)
    mn, mx = a.min(-1), a.max(-1)
    cand = (mn >= thr) | ((mn >= gray_thr) & ((mx - mn) <= sat_thr))
    lab, _ = ndimage.label(cand)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(border))
    fg = ndimage.binary_opening(~bg, iterations=2)
    fg = ndimage.binary_fill_holes(fg)
    lab2, n = ndimage.label(fg)
    if n > 1:
        sizes = ndimage.sum(fg, lab2, range(1, n + 1)); fg = lab2 == (1 + int(np.argmax(sizes)))
    if erode: fg = ndimage.binary_erosion(fg, iterations=erode)
    alpha = (ndimage.gaussian_filter(fg.astype(np.float32), 1.0) * 255).astype(np.uint8)
    return Image.fromarray(np.dstack([a.astype(np.uint8), alpha]), "RGBA")

def largest_component(m):
    parts = m.split(only_watertight=False)
    return max(parts, key=lambda p: len(p.faces)) if len(parts) > 1 else m

def section_area(m, y):
    s = m.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if s is None: return 0.0
    try:
        p, _ = s.to_2D()
        return float(sum(abs(0.5 * np.sum(d[:-1, 0] * d[1:, 1] - d[1:, 0] * d[:-1, 1])) for d in p.discrete))
    except Exception:
        return 0.0

def remove_base_plate(m):
    """If a thin flat plate sits at the lowest y (wide cross-section that collapses upward), cut it off."""
    lo, hi = m.bounds; H = hi[1] - lo[1]
    ext = hi - lo; xz_area = ext[0] * ext[2]
    ys = lo[1] + H * np.linspace(0.005, 0.15, 30)
    A = np.array([section_area(m, y) for y in ys])
    if A[0] < 0.25 * xz_area: return m, 0.0          # no wide plate at the bottom
    drop = np.where(A < 0.35 * A[0])[0]
    if len(drop) == 0: return m, 0.0                  # wide all the way up: not a plate
    cut = ys[drop[0]] + 0.003 * H
    try: m2 = m.slice_plane([0, cut, 0], [0, 1, 0], cap=True)
    except Exception: m2 = m.slice_plane([0, cut, 0], [0, 1, 0], cap=False)
    return largest_component(m2), cut - lo[1]

def remove_floor_sheet(m, band=0.03, min_frac=0.08):
    """Delete a thin (possibly zero-thickness, open) horizontal sheet at the lowest y, iterating
    since a sheet may have stacked layers. Feet soles alone stay under min_frac of the xz bbox."""
    total = 0
    for _ in range(4):
        lo, hi = m.bounds; H = hi[1] - lo[1]; ext = hi - lo
        c = m.triangles_center; n = m.face_normals
        flat = (c[:, 1] < lo[1] + band * H) & (np.abs(n[:, 1]) > 0.85)
        area = m.area_faces[flat].sum() * 0.5  # sheet has two sides when closed
        if flat.sum() == 0 or area < min_frac * ext[0] * ext[2]: break
        # grow: faces whose vertices all sit in the band are sheet rim too
        vb = m.vertices[:, 1] < lo[1] + band * H
        rim = vb[m.faces].all(1)
        keep = ~(flat | rim)
        m = largest_component(trimesh.Trimesh(m.vertices, m.faces[keep], process=True))
        total += 1
    return m, total

def finalize(m, target=100_000, head_dir=True):
    m = largest_component(m)
    m, nsheet = remove_floor_sheet(m)
    m, plate = remove_base_plate(m)
    if len(m.faces) > target:
        import fast_simplification
        v, f = fast_simplification.simplify(m.vertices.astype(np.float32), m.faces.astype(np.int32),
                                             target_reduction=1 - target / len(m.faces))
        m = trimesh.Trimesh(v, f, process=True)
        m = largest_component(m)
    # Hunyuan output is already y-up. Align long horizontal axis to x (PCA on xz).
    v = m.vertices - m.vertices.mean(0)
    c = np.cov(v[:, [0, 2]].T); w, e = np.linalg.eigh(c); ax = e[:, np.argmax(w)]
    ang = np.arctan2(ax[1], ax[0])
    R = trimesh.transformations.rotation_matrix(ang, [0, 1, 0])  # rotates long axis onto x
    m.apply_transform(R)
    if head_dir:  # head end = the x-extreme whose top is higher -> put it at -x
        x, y = m.vertices[:, 0], m.vertices[:, 1]; lo, hi = x.min(), x.max(); L = hi - lo
        yneg = y[x < lo + 0.2 * L].max(); ypos = y[x > hi - 0.2 * L].max()
        if ypos > yneg: m.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [0, 1, 0]))
    b = m.bounds; m.apply_translation([-(b[0][0] + b[1][0]) / 2, -b[0][1], -(b[0][2] + b[1][2]) / 2])
    return m, (plate, nsheet)

def main():
    prompt, out = sys.argv[1], sys.argv[2]
    seeds = [int(s) for s in (sys.argv[3] if len(sys.argv) > 3 else "0").split(",")]
    from hy3dgen.text2image import HunyuanDiTPipeline
    t2i = HunyuanDiTPipeline("Tencent-Hunyuan/HunyuanDiT-v1.1-Diffusers-Distilled")
    imgs = {s: t2i(prompt + PROMPT_SUFFIX, seed=s) for s in seeds}
    del t2i; torch.cuda.empty_cache()
    from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline, FloaterRemover, DegenerateFaceRemover
    shp = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained("tencent/Hunyuan3D-2", subfolder="hunyuan3d-dit-v2-0")
    for s in seeds:
        d = out if len(seeds) == 1 else os.path.join(out, f"s{s}")
        os.makedirs(d, exist_ok=True)
        imgs[s].save(os.path.join(d, "ref.png"))
        rgba = remove_white_bg(imgs[s]); rgba.save(os.path.join(d, "ref_rgba.png"))
        mesh = shp(image=rgba, num_inference_steps=50, octree_resolution=380, generator=torch.manual_seed(s))[0]
        mesh = FloaterRemover()(mesh); mesh = DegenerateFaceRemover()(mesh)
        mesh.export(os.path.join(d, "mesh.obj"))
        fm, plate = finalize(trimesh.Trimesh(mesh.vertices, mesh.faces, process=True))
        fm.export(os.path.join(d, "final.obj"))
        log(f"seed {s}: raw tris {len(mesh.faces)} -> final {len(fm.faces)}; plate cut/sheets {plate}; ext {np.round(fm.extents,3)}")

if __name__ == "__main__":
    main()
