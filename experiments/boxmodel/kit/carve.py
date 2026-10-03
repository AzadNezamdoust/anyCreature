"""carve.py — carve a stage-1 base from the reference sheet, and colour faces from it.

Import it inside Blender from a creature program (the kit folder is on sys.path):

    from carve import carve_base, colour_from_sheet
    def stage1(k): return carve_base(k)                    # mirrored, closed, one shell, low poly
    def stage3(k, body): colour_from_sheet(k, [body]); return []

It reads <creature>/reference/ as kit/refs.py wrote it from a 2 x 2 turnaround (sheet.png, refs.json:
the figure boxes, metres per pixel, background and threshold). Conventions are refs.py's and the
kit's: metres, Z up, head at -Y, left flank +X, feet on z = 0, side/top bboxes centred on y = 0.

carve_base(k, target_tris=(600, 1400), ...)
  1. masks: each view's figure (side, front, top) is re-segmented from sheet.png with refs.py's
     foreground rule inside its traced box; enclosed holes under 2% of the figure are filled.
  2. visual hull: a voxel grid (voxel = height / voxel_div) where each voxel's occupancy is the
     MIN of the three views' coverage over its footprint (side: y/z, front: x/z, top: x/y). The
     front and top coverages are averaged with their mirror, so the hull is symmetric about x = 0.
  3. surface: the occupancy is blurred (`blur` passes of a [1,2,1] kernel) and contoured at 0.5
     with naive surface nets (smooth, no stair-steps), then voxel-remeshed (a closed manifold),
     the largest shell kept, `smooth` light Laplacian passes.
  4. low poly: Decimate (collapse, X symmetry, triangulated), the ratio searched so the mirrored
     triangle count lands in target_tris; then bisected at x = 0 (the +X half kept, seam vertices
     snapped onto x = 0), needle/cap triangles fixed (short-edge collapse, long-edge flip), feet
     put on z = 0. The half goes through bmkit.object_from_bm (live Mirror, clipping, merge).
  5. cache: the half mesh is written to <creature>/carve_base.json keyed by the inputs; a later
     run rebuilds from it, so the stage-1 lock reproduces exactly.

colour_from_sheet(k, objs, n_colours=(4, 8), ...)
  Each face picks the reference view its normal faces most (side for +-X, the left flank mirrored
  for -X; front for -Y; rear for +Y; top for +Z), skipping a view where its own mesh hides the face
  (a BVH ray toward that camera); a few points across the face are projected with the same pixel
  mapping and the median of the figure's pixels around them is the face colour. All face colours
  are clustered (area-weighted k-means in Lab, k = n_colours max, then the closest clusters merged
  while dE < merge_de and more than n_colours min remain), a majority filter over face neighbours
  removes speckle, and one bmkit.material per cluster is assigned. Returns {name: '#rrggbb'}.

KNOWN LIMITS (a visual hull sees silhouettes only)
  - Concavities are invisible: the space between the forelegs seen from neither side, under the
    jaw, inside a cupped ear, between the arm and the torso where the front view shows no gap.
  - Thin parts that overlap the body in two views come out fat or merged (a tail against the
    rump, a hanging arm in the side view, claws, tusks, fingers below the voxel size). The builder
    refines them in stage 2 with vertex moves, or adds them as stage-3 pieces.
  - The three views must agree: a sheet whose plan view is shorter than its side view (refs.py
    warns past 10%) trims the longer one. Perspective in a generated sheet rounds the corners.
  - Colour comes from a lit render: the cluster colours carry the sheet's average lighting, and
    shading bands on a single region can split into two clusters (raise merge_de).
  - Faces nothing in the sheet sees (the belly, inner legs) borrow the nearest view's colour.
"""
import bpy, bmesh, json, hashlib, math, os
from collections import deque
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import bmkit as B

VERSION = 'carve-1'


# ---------------------------------------------------------------- the sheet
def _load_rgb(path):
    """sheet.png -> float32 (H, W, 3) in 0..255 sRGB, row 0 at the top (bpy reads bottom-up)."""
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    a = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)[::-1, :, :3] * 255.0


def _foreground(rgb, bg, thresh):
    """refs.py's rule: far from the background colour, or clearly saturated."""
    diff = np.abs(rgb - bg).max(axis=2)
    sat = rgb.max(axis=2) - rgb.min(axis=2)
    return (diff > thresh) | (sat > max(28.0, thresh * 0.8))


def _outside(bgm):
    """Background pixels 4-connected to the border."""
    out = np.zeros_like(bgm)
    out[0], out[-1], out[:, 0], out[:, -1] = bgm[0], bgm[-1], bgm[:, 0], bgm[:, -1]
    n = -1
    while True:
        for _ in range(16):
            g = out.copy()
            g[1:] |= out[:-1]; g[:-1] |= out[1:]; g[:, 1:] |= out[:, :-1]; g[:, :-1] |= out[:, 1:]
            out = g & bgm
        c = int(out.sum())
        if c == n:
            return out
        n = c


def _fill_small_holes(m, frac=0.02):
    """Enclosed background regions smaller than frac of the figure become figure (a highlight, an
    eye); bigger ones stay open (a real gap between an arm and the body)."""
    holes = ~m & ~_outside(~m)
    if not holes.any():
        return m
    m = m.copy()
    h, w = m.shape
    seen = np.zeros_like(m)
    lim = frac * m.sum()
    for start in zip(*np.nonzero(holes)):
        if seen[start]:
            continue
        q, comp = deque([start]), [start]
        seen[start] = True
        while q:
            r, c = q.popleft()
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= rr < h and 0 <= cc < w and holes[rr, cc] and not seen[rr, cc]:
                    seen[rr, cc] = True; q.append((rr, cc)); comp.append((rr, cc))
        if len(comp) < lim:
            rs, cs = zip(*comp)
            m[list(rs), list(cs)] = True
    return m


class View:
    """One figure of the sheet: its mask, its pixels and the world -> sheet pixel mapping."""

    def __init__(self, name, rgb, R):
        self.name = name
        r0, r1, c0, c1 = R['crops'][name]['box_rows_cols']          # the traced figure box, inclusive
        self.r0, self.c0 = r0 - 1, c0 - 1
        self.rgb = rgb[r0 - 1:r1 + 2, c0 - 1:c1 + 2]
        m = _foreground(self.rgb, np.array(R['background_rgb'], np.float32), float(R['thresh']))
        m[0] = m[-1] = False; m[:, 0] = m[:, -1] = False
        self.mask = _fill_small_holes(m)
        self.s = float(R['metres_per_pixel'][name])
        self.ground = r1                                           # sheet row of z = 0
        self.cmid = (c0 + c1) / 2.0                                # sheet column of y = 0 (side, top)
        rows, cols = np.nonzero(self.mask)
        if name in ('front', 'rear'):                              # symmetry axis: refs.py's median row mid
            mids = [(c[0] + c[-1]) / 2.0 for c in (cols[rows == r] for r in np.unique(rows))]
            self.axis = float(np.median(mids)) + self.c0
        elif name == 'top':                                        # the long axis: median column mid (rows)
            mids = [(r[0] + r[-1]) / 2.0 for r in (rows[cols == c] for c in np.unique(cols))]
            self.axis = float(np.median(mids)) + self.r0
        I = np.zeros((self.mask.shape[0] + 1, self.mask.shape[1] + 1), np.float64)
        I[1:, 1:] = self.mask.astype(np.float64).cumsum(0).cumsum(1)
        self.I = I

    def pix(self, x, y, z):
        """World -> (row, col) in this view's crop (floats; numpy broadcasting)."""
        s = self.s
        if self.name == 'side':
            R, C = self.ground - z / s, self.cmid + y / s
        elif self.name == 'front':
            R, C = self.ground - z / s, self.axis + x / s
        elif self.name == 'rear':
            R, C = self.ground - z / s, self.axis - x / s
        else:
            R, C = self.axis + x / s, self.cmid + y / s
        return R - self.r0, C - self.c0

    def cover(self, R, C, h):
        """Fraction of figure pixels in the (2h)^2 window round (R, C)."""
        H, W = self.mask.shape
        a0, a1 = np.floor(R - h + 0.5).astype(int), np.floor(R + h + 0.5).astype(int)
        b0, b1 = np.floor(C - h + 0.5).astype(int), np.floor(C + h + 0.5).astype(int)
        area = np.maximum((a1 - a0) * (b1 - b0), 1)
        a0, a1, b0, b1 = (np.clip(t, 0, n) for t, n in ((a0, H), (a1, H), (b0, W), (b1, W)))
        I = self.I
        return (I[a1, b1] - I[a0, b1] - I[a1, b0] + I[a0, b0]) / area

    def colour(self, pts, patch=2):
        """Median sheet colour (sRGB 0..255) of the figure pixels round the projected points."""
        H, W = self.mask.shape
        got = []
        for p in pts:
            r, c = self.pix(p[0], p[1], p[2])
            r, c = int(round(r)), int(round(c))
            a0, a1, b0, b1 = max(0, r - patch), min(H, r + patch + 1), max(0, c - patch), min(W, c + patch + 1)
            if a0 >= a1 or b0 >= b1:
                continue
            m = self.mask[a0:a1, b0:b1]
            if m.any():
                got.append(self.rgb[a0:a1, b0:b1][m])
        if not got:
            return None
        g = np.concatenate(got)
        return np.median(g, axis=0) if len(g) >= 3 else None


_REF = {}


def load_ref(cdir):
    rdir = os.path.join(cdir, 'reference')
    if rdir in _REF:
        return _REF[rdir]
    R = json.load(open(os.path.join(rdir, 'refs.json')))
    if R.get('layout') != '2x2':
        raise ValueError('carve.py needs a 2 x 2 reference sheet (side, front, rear, top); got ' + str(R.get('layout')))
    rgb = _load_rgb(os.path.join(rdir, 'sheet.png'))
    _REF[rdir] = {v: View(v, rgb, R) for v in ('side', 'front', 'rear', 'top')}
    return _REF[rdir]


# ---------------------------------------------------------------- the hull
def _blur(F, passes):
    for _ in range(passes):
        for ax in range(3):
            P = np.pad(F, [(1, 1) if a == ax else (0, 0) for a in range(3)], mode='edge')
            sl = lambda a, b: tuple(slice(a, P.shape[ax] - b) if i == ax else slice(None) for i in range(3))
            F = 0.25 * P[sl(0, 2)] + 0.5 * P[sl(1, 1)] + 0.25 * P[sl(2, 0)]
    return F


def _runs(H, ax):
    """For every voxel: the first and last index of the run of H it sits in, along axis ax."""
    n = H.shape[ax]
    shp = [1, 1, 1]; shp[ax] = n
    i = np.arange(n).reshape(shp)
    prev = np.concatenate([np.zeros_like(np.take(H, [0], ax)), np.take(H, range(n - 1), ax)], ax)
    nxt = np.concatenate([np.take(H, range(1, n), ax), np.zeros_like(np.take(H, [0], ax))], ax)
    a = np.maximum.accumulate(np.where(H & ~prev, i, -1), axis=ax)
    b = np.flip(np.minimum.accumulate(np.flip(np.where(H & ~nxt, i, n), ax), axis=ax), ax)
    return a, b


def _seg_max(A, H, ax, a, b):
    """For every voxel of H: the max of A over the run of H it sits in along axis ax (a, b: the
    run's first and last index from _runs)."""
    n = H.shape[ax]
    shp = [1, 1, 1]; shp[ax] = n
    i = np.arange(n).reshape(shp)
    rid = np.cumsum(H & (i == a), axis=ax).astype(np.float64)          # run id along the axis
    big = float(A.max()) + 1.0
    fw = np.maximum.accumulate(np.where(H, rid * big + A, -1.0), axis=ax)
    end = np.clip(b, 0, n - 1)
    return np.take_along_axis(fw, end, axis=ax) - rid * big


def _depth2d(M, steps):
    """How many 3 x 3 erosions each pixel of a 2D mask survives (capped at steps)."""
    D = np.zeros(M.shape, np.float32)
    cur = M.copy()
    for _ in range(steps):
        D += cur
        P = np.pad(cur, 1)
        nxt = cur.copy()
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                nxt &= P[1 + di:P.shape[0] - 1 + di, 1 + dj:P.shape[1] - 1 + dj]
        cur = nxt
    return D


def round_sections(F, p=2.5, soft=0.15, keep=None, ysmooth=8):
    """The cross-section prior: three orthographic silhouettes cut box sections (a flat flank from
    the plan, a flat back from the side, a sharp crease where they meet). In every x-z section each
    voxel is kept only inside the superellipse |u|^p + |v|^p <= 1 inscribed in its own x-run (u) and
    z-run (v); a z-run that stands on the ground is not rounded below its middle (flat soles).
    p: 2 = elliptic sections, larger = boxier. Returns the soft occupancy."""
    H = F > 0.5
    xa, xb = _runs(H, 0)
    za, zb = _runs(H, 2)
    i = np.arange(F.shape[0])[:, None, None].astype(np.float32)
    k = np.arange(F.shape[2])[None, None, :].astype(np.float32)
    W = np.where(H, (xb - xa + 1) / 2.0, 0.0)              # own x-run half width
    Hh = np.where(H, (zb - za + 1) / 2.0, 0.0)             # own z-run half height
    # normalise by the widest run met along the other axis, so a section that is already round
    # (an ellipse) passes unchanged and only box corners are cut
    u = np.abs(i - (xa + xb) / 2.0) / np.maximum(_seg_max(W, H, 2, za, zb), 0.5)
    v = (k - (za + zb) / 2.0) / np.maximum(_seg_max(Hh, H, 0, xa, xb), 0.5)
    v = np.where((za == 0) & (v < 0), 0.0, np.abs(v))
    s = u ** p + v ** p
    G = np.clip(0.5 + (1.0 - s) / (2 * soft), 0.0, 1.0)
    # the run normalisers jump from slice to slice (a leg column starts): smooth the cut along Y,
    # or the flank shows a vertical rib at every jump
    G = np.where(H, G, 1.0)
    for _ in range(ysmooth):
        P = np.pad(G, ((0, 0), (1, 1), (0, 0)), mode='edge')
        G = 0.25 * P[:, :-2] + 0.5 * P[:, 1:-1] + 0.25 * P[:, 2:]
    if keep is not None:
        G = np.maximum(G, keep)
    return np.where(H, np.minimum(F, G), F).astype(np.float32)


def round_plan(F, p=2.5, soft=0.15, zsmooth=8):
    """The same prior in plan (x-y) sections: rounds the flat chest and back planes that the front
    view extrudes along Y (an upright biped's box torso, a cube head). Off unless asked for."""
    H = F > 0.5
    xa, xb = _runs(H, 0)
    ya, yb = _runs(H, 1)
    i = np.arange(F.shape[0])[:, None, None].astype(np.float32)
    j = np.arange(F.shape[1])[None, :, None].astype(np.float32)
    W = np.where(H, (xb - xa + 1) / 2.0, 0.0)
    D = np.where(H, (yb - ya + 1) / 2.0, 0.0)
    u = np.abs(i - (xa + xb) / 2.0) / np.maximum(_seg_max(W, H, 1, ya, yb), 0.5)
    v = np.abs(j - (ya + yb) / 2.0) / np.maximum(_seg_max(D, H, 0, xa, xb), 0.5)
    G = np.where(H, np.clip(0.5 + (1.0 - (u ** p + v ** p)) / (2 * soft), 0.0, 1.0), 1.0)
    for _ in range(zsmooth):
        P = np.pad(G, ((0, 0), (0, 0), (1, 1)), mode='edge')
        G = 0.25 * P[:, :, :-2] + 0.5 * P[:, :, 1:-1] + 0.25 * P[:, :, 2:]
    return np.where(H, np.minimum(F, G), F).astype(np.float32)


def _blur2d(A, passes):
    for _ in range(passes):
        for ax in (0, 1):
            P = np.pad(A, [(1, 1) if a == ax else (0, 0) for a in (0, 1)], mode='edge')
            n = P.shape[ax]
            A = 0.25 * np.take(P, range(0, n - 2), ax) + 0.5 * np.take(P, range(1, n - 1), ax)                 + 0.25 * np.take(P, range(2, n), ax)
    return A


def hull_field(views, vs, blur=1, roundness=2.0, protect=0, mask_blur=3, plan_roundness=0):
    """Occupancy (nx, ny, nz) of the visual hull and the world position of voxel (0, 0, 0)."""
    sd, fr, tp = views['side'], views['front'], views['top']
    Ly = (sd.mask.shape[1] - 3) / 2.0 * sd.s
    Hz = (sd.ground - sd.r0 - 1) * sd.s
    fx = np.nonzero(fr.mask)[1] + fr.c0 - fr.axis
    tx = np.nonzero(tp.mask)[0] + tp.r0 - tp.axis
    X = max(np.abs(fx).max() * fr.s, np.abs(tx).max() * tp.s)
    xh = (np.arange(int(math.ceil(X / vs)) + 2) + 0.5) * vs
    ys = np.arange(-Ly - 2 * vs, Ly + 2 * vs, vs)
    zs = (np.arange(int(math.ceil(Hz / vs)) + 2) + 0.5) * vs
    half = lambda v, s: 0.5 * vs / s                      # half a voxel in this view's pixels
    S = sd.cover(*sd.pix(0, ys[:, None], zs[None, :]), half(0, sd.s))                         # (ny, nz)
    Fh = 0.5 * (fr.cover(*fr.pix(xh[:, None], 0, zs[None, :]), half(0, fr.s))
                + fr.cover(*fr.pix(-xh[:, None], 0, zs[None, :]), half(0, fr.s)))            # (nxh, nz)
    Th = 0.5 * (tp.cover(*tp.pix(xh[:, None], ys[None, :], 0), half(0, tp.s))
                + tp.cover(*tp.pix(-xh[:, None], ys[None, :], 0), half(0, tp.s)))            # (nxh, ny)
    S, Fh, Th = (_blur2d(A, mask_blur) for A in (S, Fh, Th))   # a polygonal outline corner becomes a crease
    Ff, Tf = np.concatenate([Fh[::-1], Fh]), np.concatenate([Th[::-1], Th])
    F = np.minimum(np.minimum(Ff[:, None, :], S[None, :, :]), Tf[:, :, None]).astype(np.float32)
    if roundness:
        # a box corner of the hull lies deep inside the front silhouette (it is a phantom of the plan
        # and side views); an ear or a shoulder on the front outline is real: keep what lies within
        # `protect` voxels of the front outline
        # (off by default: on the bear it kept flat slabs along the flank, and ears sit inside the
        # front outline anyway)
        keep = None
        if protect:
            D = _depth2d(Ff > 0.5, protect + 1)
            keep = np.clip(1.0 - (D - 1.0) / protect, 0.0, 1.0)[:, None, :]
        F = round_sections(F, roundness, keep=keep)
    if plan_roundness:
        F = round_plan(F, plan_roundness)
    F = _blur(F, blur)
    F = np.pad(F, 2)
    org = np.array([-xh[-1] - 2 * vs, ys[0] - 2 * vs, zs[0] - 2 * vs])
    return F, org


def surface_nets(F, org, vs, iso=0.5):
    """Naive surface nets: one vertex per sign-changing cell at the mean edge crossing, one quad
    per sign-changing grid edge (wound outward). -> verts (n, 3), quads (m, 4)."""
    ins = F > iso
    NX, NY, NZ = F.shape
    offs = [(a, b, c) for a in (0, 1) for b in (0, 1) for c in (0, 1)]
    sl = lambda o: (slice(o[0], NX - 1 + o[0]), slice(o[1], NY - 1 + o[1]), slice(o[2], NZ - 1 + o[2]))
    Fc = [F[sl(o)] for o in offs]
    Ic = [ins[sl(o)] for o in offs]
    act = np.logical_or.reduce(Ic) & ~np.logical_and.reduce(Ic)
    acc = np.zeros(act.shape + (3,), np.float32)
    cnt = np.zeros(act.shape, np.float32)
    for i in range(8):
        for j in range(i + 1, 8):
            d = np.subtract(offs[j], offs[i])
            if np.abs(d).sum() != 1:
                continue
            ch = Ic[i] != Ic[j]
            den = Fc[j] - Fc[i]
            t = np.where(ch, (iso - Fc[i]) / np.where(np.abs(den) > 1e-9, den, 1.0), 0.0)
            acc += ch[..., None] * (np.array(offs[i], np.float32) + t[..., None] * d.astype(np.float32))
            cnt += ch
    ijk = np.argwhere(act)
    idx = -np.ones(act.shape, np.int64)
    idx[act] = np.arange(len(ijk))
    verts = org + (ijk + acc[act] / cnt[act][:, None]) * vs
    quads = []
    for ax in range(3):
        a1, a2 = (ax + 1) % 3, (ax + 2) % 3
        lo = [slice(None)] * 3; hi = [slice(None)] * 3
        lo[ax] = slice(0, -1); hi[ax] = slice(1, None)
        e_in, e_out = ins[tuple(lo)], ins[tuple(hi)]
        ch = e_in != e_out
        P = np.argwhere(ch)
        P = P[(P[:, a1] >= 1) & (P[:, a2] >= 1) & (P[:, a1] < F.shape[a1] - 1) & (P[:, a2] < F.shape[a2] - 1)]
        if not len(P):
            continue
        out_dir = e_in[tuple(P.T)]                         # inside at the low end: the normal points +ax
        cyc = []
        for d1, d2 in ((-1, -1), (0, -1), (0, 0), (-1, 0)):
            Q = P.copy(); Q[:, a1] += d1; Q[:, a2] += d2
            cyc.append(idx[tuple(Q.T)])
        q = np.stack(cyc, 1)
        q[~out_dir] = q[~out_dir][:, ::-1]
        quads.append(q)
    quads = np.concatenate(quads)
    return verts, quads[(quads >= 0).all(1)]


# ---------------------------------------------------------------- the mesh
def _tmp_object(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    return B.link(bpy.data.objects.new(name, me))


def _apply(ob, md):
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]):
        bpy.ops.object.modifier_apply(modifier=md.name)


def _drop(ob):
    me = ob.data
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)


def _largest_shell(bm):
    seen, best = set(), []
    for v in bm.verts:
        if v in seen:
            continue
        comp, st = [], [v]
        seen.add(v)
        while st:
            x = st.pop(); comp.append(x)
            for e in x.link_edges:
                w = e.other_vert(x)
                if w not in seen:
                    seen.add(w); st.append(w)
        if len(comp) > len(best):
            best = comp
    keep = set(best)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v not in keep], context='VERTS')


def dense_surface(views, vs, blur=1, smooth=24, remesh=0.5, roundness=2.0, protect=0, mask_blur=3, plan_roundness=0):
    """The hull as a dense closed mesh (a temporary object)."""
    F, org = hull_field(views, vs, blur, roundness, protect, mask_blur, plan_roundness)
    verts, quads = surface_nets(F, org, vs)
    me = bpy.data.meshes.new('_carve_nets')
    me.from_pydata(verts.tolist(), [], quads.tolist())
    me.update()
    ob = B.link(bpy.data.objects.new('_carve_nets', me))
    md = ob.modifiers.new('rm', 'REMESH')
    md.mode = 'VOXEL'
    md.voxel_size = vs * remesh
    md.adaptivity = 0.0
    _apply(ob, md)
    bm = B.edit(ob)
    _largest_shell(bm)
    for _ in range(smooth):
        bmesh.ops.smooth_vert(bm, verts=list(bm.verts), factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    B.commit(ob, bm)
    bm.free()
    return ob


def _on_seam(v):
    return abs(v.co.x) < 1e-6


def _half(dense, ratio, snap=0.0):
    """Decimate a copy of the dense mesh, cut it at x = 0 and keep the +X half."""
    ob = dense.copy(); ob.data = dense.data.copy(); ob.name = '_carve_dec'
    B.link(ob)
    md = ob.modifiers.new('dec', 'DECIMATE')
    md.decimate_type = 'COLLAPSE'
    md.ratio = ratio
    md.use_collapse_triangulate = True                     # no X symmetry: it kept the seam dense; the -X half goes anyway
    _apply(ob, md)
    bm = B.edit(ob)
    _drop(ob)
    for v in bm.verts:                                     # near-seam vertices onto it: no sliver at the cut
        if abs(v.co.x) < snap:
            v.co.x = 0.0
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), dist=1e-6,
                           plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_inner=True)
    for v in bm.verts:
        if v.co.x < 1e-4:
            v.co.x = 0.0
    flat = [f for f in bm.faces if all(_on_seam(v) for v in f.verts)]      # a face in the mirror plane
    bmesh.ops.delete(bm, geom=flat, context='FACES_ONLY')
    bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces], context='EDGES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_edges], context='VERTS')
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    _largest_shell(bm)
    return bm


def _defects(bm):
    """(open edges off the seam, edges with > 2 faces, seam edges with 2 faces)."""
    off = sum(1 for e in bm.edges if len(e.link_faces) == 1 and not all(_on_seam(v) for v in e.verts))
    many = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    fin = sum(1 for e in bm.edges if len(e.link_faces) == 2 and all(_on_seam(v) for v in e.verts))
    return off, many, fin


def _fix_slivers(bm, L, min_deg=8.0, passes=6):
    """Needles (one short edge) collapse their short edge; caps (one wide angle) flip their long
    edge. Seam vertices stay on x = 0; a collapse that would pinch the surface is skipped."""
    for _ in range(passes):
        bad = 0
        for f in list(bm.faces):
            if not f.is_valid or len(f.verts) != 3:
                continue
            es = list(f.edges)
            ls = [e.calc_length() for e in es]
            if max(ls) < 0.01 * L:
                continue
            angs = [math.degrees(l.calc_angle()) for l in f.loops]
            if min(angs) >= min_deg:
                continue
            bad += 1
            emax, emin = es[ls.index(max(ls))], es[ls.index(min(ls))]
            if max(angs) > 120.0 and len(emax.link_faces) == 2 and not all(_on_seam(v) for v in emax.verts):
                bmesh.ops.rotate_edges(bm, edges=[emax], use_ccw=False)
                continue
            a, b = emin.verts
            na = {e.other_vert(a) for e in a.link_edges}
            nb = {e.other_vert(b) for e in b.link_edges}
            if len(na & nb) != len(emin.link_faces):
                continue
            sa, sb = _on_seam(a), _on_seam(b)
            co = a.co.copy() if sa and not sb else b.co.copy() if sb and not sa else (a.co + b.co) / 2
            bmesh.ops.pointmerge(bm, verts=[a, b], merge_co=co)
        bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=1e-6)
        if not bad:
            break


def _tris(bm):
    return 2 * sum(len(f.verts) - 2 for f in bm.faces)


def carve_base(k, target_tris=(600, 1400), voxel_div=90, blur=1, smooth=24, roundness=2.0, protect=0, mask_blur=3, plan_roundness=0, sliver_deg=8.0,
               name='body'):
    """Stage 1 from the reference sheet: see the module docstring. Returns the body object
    (the +X half under a live Mirror)."""
    cdir = k.dir
    rdir = os.path.join(cdir, 'reference')
    params = dict(v=VERSION, target_tris=list(target_tris), voxel_div=voxel_div, blur=blur, smooth=smooth, roundness=roundness, protect=protect,
                  mask_blur=mask_blur, **({'plan_roundness': plan_roundness} if plan_roundness else {}),
                  sliver_deg=sliver_deg)
    h = hashlib.sha256(json.dumps(params, sort_keys=True).encode())
    for f in (os.path.join(rdir, 'refs.json'), os.path.join(rdir, 'sheet.png')):
        h.update(open(f, 'rb').read())
    src = open(os.path.abspath(__file__), 'rb').read()
    h.update(src[:src.find(b'# ---------------------------------------------------------------- colour')])
    # the inputs and the carving code: any change to them re-carves (and a locked stage 1 then fails its gate)
    key = h.hexdigest()
    cpath = os.path.join(cdir, 'carve_base.json')
    cache = json.load(open(cpath)) if os.path.exists(cpath) else None
    if not cache or cache.get('key') != key:
        views = load_ref(cdir)
        sd = views['side']
        H = (sd.ground - sd.r0 - 1) * sd.s
        vs = H / voxel_div
        dense = dense_surface(views, vs, blur, smooth, roundness=roundness, protect=protect, mask_blur=mask_blur,
                              plan_roundness=plan_roundness)
        n0 = sum(len(p.vertices) - 2 for p in dense.data.polygons)
        lo, hi = target_tris
        want = 0.5 * (lo + hi)
        ratio, bm = want / n0, None
        for it in range(6):
            if bm:
                bm.free()
            bm = _half(dense, min(1.0, ratio), snap=0.12 * 0.5 * vs * (n0 / want) ** 0.5)  # 12% of a low-poly edge
            _fix_slivers(bm, max(H, 2 * Ly_of(views)), sliver_deg)
            t = _tris(bm)
            B.say(f'carve: voxel {vs:.4f} m, dense {n0} tris, ratio {ratio:.4f} -> {t} tris (mirrored); '
                  f'defects (open, >2 faces, seam fins) {_defects(bm)}')
            if lo <= t <= hi and abs(t - want) < 0.2 * (hi - lo):
                break
            ratio *= want / max(t, 1)
        _drop(dense)
        zmin = min(v.co.z for v in bm.verts)
        for v in bm.verts:
            v.co.z -= zmin
        bm.verts.index_update()
        cache = dict(key=key, params=params, voxel=vs, tris=_tris(bm),
                     verts=[[round(c, 6) for c in v.co] for v in bm.verts],
                     faces=[[v.index for v in f.verts] for f in bm.faces])
        bm.free()
        with open(cpath, 'w') as fh:
            json.dump(cache, fh)
    bm = bmesh.new()
    vv = [bm.verts.new(p) for p in cache['verts']]
    for f in cache['faces']:
        bm.faces.new([vv[i] for i in f])
    return B.object_from_bm(name, bm)


def Ly_of(views):
    sd = views['side']
    return (sd.mask.shape[1] - 3) / 2.0 * sd.s


# ---------------------------------------------------------------- colour
VIEW_DIRS = {'front': Vector((0, -1, 0)), 'rear': Vector((0, 1, 0)), 'top': Vector((0, 0, 1))}


def _lab(rgb):
    c = np.asarray(rgb, np.float64) / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = lin @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[:, 1] - 16, 500 * (f[:, 0] - f[:, 1]), 200 * (f[:, 1] - f[:, 2])], 1)


def _srgb_of_lab(lab):
    lab = np.atleast_2d(np.asarray(lab, np.float64))
    fy = (lab[:, 0] + 16) / 116
    f = np.stack([fy + lab[:, 1] / 500, fy, fy - lab[:, 2] / 200], 1)
    xyz = np.where(f > 0.2069, f ** 3, (f - 16 / 116) / 7.787) * np.array([0.95047, 1.0, 1.08883])
    M = np.array([[3.2406, -1.5372, -0.4986], [-0.9689, 1.8758, 0.0415], [0.0557, -0.2040, 1.0570]])
    lin = np.clip(xyz @ M.T, 0, 1)
    c = np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * lin ** (1 / 2.4) - 0.055)
    return c * 255.0


def _kmeans(X, w, k, iters=40, seed=0):
    rng = np.random.default_rng(seed)
    C = [X[int(np.argmax(w))]]
    for _ in range(1, min(k, len(X))):
        d = np.min([((X - c) ** 2).sum(1) for c in C], 0)
        p = w * d
        if p.sum() <= 0:
            break
        C.append(X[rng.choice(len(X), p=p / p.sum())])
    C = np.array(C)
    for _ in range(iters):
        lab = np.argmin(((X[:, None] - C[None]) ** 2).sum(2), 1)
        N = np.array([np.average(X[lab == j], 0, w[lab == j]) if (lab == j).any() else C[j] for j in range(len(C))])
        if np.allclose(N, C):
            break
        C = N
    return C, np.argmin(((X[:, None] - C[None]) ** 2).sum(2), 1)


def _occluder(objs):
    """One BVH over the evaluated (mirrored) objects, world space."""
    dg = bpy.context.evaluated_depsgraph_get()
    V, P = [], []
    for o in objs:
        oe = o.evaluated_get(dg)
        me = oe.to_mesh()
        n = len(V)
        V += [tuple(o.matrix_world @ v.co) for v in me.vertices]
        P += [[n + i for i in p.vertices] for p in me.polygons]
        oe.to_mesh_clear()
    return BVHTree.FromPolygons(V, P)


def colour_from_sheet(k, objs, n_colours=(4, 8), merge_de=14.0, majority=2, patch=2, delight=1.0,
                      lift=8.0, min_l=24.0, chroma=1.12, prefix="sheet"):
    """Colour every face of objs from the reference sheet: see the module docstring.
    Returns the palette {material name: '#rrggbb'}, largest region first."""
    views = load_ref(k.dir)
    tree = _occluder(objs)
    L = max(max(o.dimensions) for o in objs)
    eps = 2e-3 * L
    faces = []                                              # (obj, poly index, area, rgb or None)
    stats = {}
    for o in objs:
        me, mw = o.data, o.matrix_world
        m3 = mw.to_3x3()
        for p in me.polygons:
            c = mw @ p.center
            n = (m3 @ p.normal).normalized()
            pts = [c] + [c.lerp(mw @ me.vertices[i].co, 0.55) for i in p.vertices]
            cand = [('side', abs(n.x), Vector((1.0 if n.x >= 0 else -1.0, 0, 0))),
                    ('front', -n.y, VIEW_DIRS['front']), ('rear', n.y, VIEW_DIRS['rear']),
                    ('top', n.z, VIEW_DIRS['top'])]
            cand.sort(key=lambda t: -t[1])
            col = None
            for strict in (True, False):
                for v, sc, d in cand:
                    if strict and sc < 0.05:
                        continue
                    if strict and tree.ray_cast(c + n * eps + d * eps, d, 10 * L)[0] is not None:
                        continue                            # its own mesh hides the face in this view
                    col = views[v].colour(pts, patch)
                    if col is not None:
                        break
                if col is not None:
                    break
            faces.append([o, p.index, p.area, col, n.copy()])
            used_v = v if col is not None else 'none'
            stats.setdefault(used_v, []).append(col if col is not None else np.zeros(3))
    B.say('colour_from_sheet views:', {v: (len(c), '#%02x%02x%02x' % tuple(int(x) for x in np.median(c, 0)))
                                        for v, c in sorted(stats.items())})
    known = [f for f in faces if f[3] is not None]
    X = _lab(np.array([f[3] for f in known]))
    w = np.array([f[2] for f in known]) + 1e-9
    if delight:
        # the sheet is a lit render: a facet turned from its key light is darker there, and our own
        # renderer shades it again. Fit L = c0 + c.n over the faces (area-weighted) and remove the
        # normal-dependent part, so shadowed fur does not cluster with a dark region.
        N = np.array([tuple(f[4]) for f in known])
        A = np.hstack([np.ones((len(N), 1)), N]) * np.sqrt(w)[:, None]
        c = np.linalg.lstsq(A, X[:, 0] * np.sqrt(w), rcond=None)[0]
        nbar = np.average(N, 0, w)
        X[:, 0] -= delight * (N - nbar) @ c[1:]
        B.say('colour_from_sheet: delight L = %.1f + n.(%.1f, %.1f, %.1f)' % tuple(c))
    for f, x in zip(known, X):
        f[3] = x                                            # from here on the face colour is corrected Lab
    lo, hi = n_colours
    C, lab = _kmeans(X, w, hi)
    groups = [[i] for i in range(len(C))]
    while True:                                             # merge the closest clusters while close
        live = [g for g in groups if g]
        if len(live) <= lo:
            break
        cen = [np.average(X[np.isin(lab, g)], 0, w[np.isin(lab, g)]) if np.isin(lab, g).any() else None for g in live]
        best = None
        for a in range(len(live)):
            for b in range(a + 1, len(live)):
                if cen[a] is None or cen[b] is None:
                    continue
                d = float(np.linalg.norm(cen[a] - cen[b]))
                if best is None or d < best[0]:
                    best = (d, a, b)
        if best is None or best[0] > merge_de:
            break
        live[best[1]] += live[best[2]]
        live[best[2]].clear()
        groups = [g for g in live if g]
    gid = {c: gi for gi, g in enumerate(groups) for c in g}
    for f, l in zip(known, lab):
        f.append(gid[int(l)])
    for f in faces:
        if f[3] is None:
            f.append(None)
    # majority filter over edge neighbours (per object), and unknown faces take their neighbours' label
    for o in objs:
        fs = {f[1]: f for f in faces if f[0] is o}
        bm = B.edit(o)
        nb = {fa.index: [g.index for e in fa.edges for g in e.link_faces if g is not fa] for fa in bm.faces}
        bm.free()
        before = {i: f[5] for i, f in fs.items()}
        for it in range(majority + 20):
            new = {}
            for i, f in fs.items():
                votes = {}
                if f[5] is not None:
                    votes[f[5]] = 1.0 + 1e-3
                for j in nb[i]:
                    if fs[j][5] is not None:
                        votes[fs[j][5]] = votes.get(fs[j][5], 0) + 1.0
                if votes and (f[5] is None or it < majority):
                    new[i] = max(votes, key=lambda x: (votes[x], x == f[5]))
            for i, l in new.items():
                fs[i][5] = l
            if it >= majority and all(f[5] is not None for f in fs.values()):
                break
        kept = {f[5] for f in fs.values()}
        for i, f in fs.items():                             # the filter may not erase a region
            if before[i] is not None and before[i] not in kept:
                f[5] = before[i]
    # palette: the area-weighted median sheet colour of each region, largest region first
    used = sorted({f[5] for f in faces if f[5] is not None},
                  key=lambda g: -sum(f[2] for f in faces if f[5] == g))
    pal = {}
    for r, g in enumerate(used):
        cols = np.array([f[3] for f in faces if f[5] == g and f[3] is not None])
        if len(cols):
            # the kit renders shade the colour again: lift it (the sheet's lit average reads darker),
            # keep dark regions off black (BRIEF lesson: dark but not black), a touch more chroma
            lab_ = np.median(cols, 0)
            lab_ = np.array([max(lab_[0] + lift, min_l), lab_[1] * chroma, lab_[2] * chroma])
            rgb = _srgb_of_lab(lab_)[0]
        else:
            rgb = np.array([128, 128, 128])
        pal[g] = (f'{prefix}{r + 1}', '#%02x%02x%02x' % tuple(int(round(min(255, max(0, x)))) for x in rgb))
    for o in objs:
        me = o.data
        me.materials.clear()
        mine = [g for g in used if any(f[0] is o and f[5] == g for f in faces)]
        for g in mine:
            me.materials.append(B.material(pal[g][0], B.srgb(pal[g][1])))
        for f in faces:
            if f[0] is o:
                p = me.polygons[f[1]]
                p.material_index = mine.index(f[5]) if f[5] in mine else 0
                p.use_smooth = False
        B.white(o)
    out = {pal[g][0]: pal[g][1] for g in used}
    B.say('colour_from_sheet:', json.dumps(out))
    return out
