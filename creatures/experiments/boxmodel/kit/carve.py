"""carve.py — carve a stage-1 base from the reference sheet, and colour faces from it.

Import it inside Blender from a creature program (the kit folder is on sys.path):

    from carve import carve_base, colour_from_sheet        (stage 1 of a cage build: part_guide, part_rings; see below)
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


# ---------------------------------------------------------------- the guide (stage 1 = a cage over the hull)
# The hull is a sculpt, not a mesh: carve_guide() returns it as a hidden object that nothing renders
# or exports, and the builder box-models a quad cage over it (BRIEF stage 1). Everything below this
# line is outside carve_base's cache key, so builds that use the hull as their base are not re-carved.
_TREES = {}


def carve_guide(k, tris=4000, voxel_div=90, blur=1, smooth=24, roundness=2.0, mask_blur=3, plan_roundness=0,
                name='_guide'):
    """The visual hull of <creature>/reference/ as a GUIDE: a dense-ish (about `tris` triangles), whole
    (both flanks) triangle mesh, feet on z = 0, hidden from every render and never exported (its name
    starts with '_'). Cached in <creature>/carve_guide.npz keyed by the inputs. Also set as k.guide."""
    cdir = k.dir
    rdir = os.path.join(cdir, 'reference')
    params = dict(v=VERSION, guide=1, tris=tris, voxel_div=voxel_div, blur=blur, smooth=smooth, roundness=roundness,
                  mask_blur=mask_blur, plan_roundness=plan_roundness)
    h = hashlib.sha256(json.dumps(params, sort_keys=True).encode())
    for f in (os.path.join(rdir, 'refs.json'), os.path.join(rdir, 'sheet.png')):
        h.update(open(f, 'rb').read())
    key = h.hexdigest()
    cpath = os.path.join(cdir, 'carve_guide.npz')
    V = F = None
    if os.path.exists(cpath):
        z = np.load(cpath)
        if str(z['key']) == key:
            V, F = z['verts'], z['faces']
    if V is None:
        views = load_ref(cdir)
        sd = views['side']
        vs = (sd.ground - sd.r0 - 1) * sd.s / voxel_div
        dense = dense_surface(views, vs, blur, smooth, roundness=roundness, mask_blur=mask_blur,
                              plan_roundness=plan_roundness)
        n0 = sum(len(p.vertices) - 2 for p in dense.data.polygons)
        md = dense.modifiers.new('dec', 'DECIMATE')
        md.decimate_type = 'COLLAPSE'
        md.ratio = min(1.0, tris / max(1, n0))
        md.use_collapse_triangulate = True
        _apply(dense, md)
        me = dense.data
        V = np.array([v.co[:] for v in me.vertices], np.float32)
        V[:, 2] -= V[:, 2].min()
        F = np.array([p.vertices[:] for p in me.polygons], np.int32)
        _drop(dense)
        np.savez_compressed(cpath, key=key, verts=V, faces=F)
        B.say(f'carve_guide: voxel {vs:.4f} m, {n0} -> {len(F)} triangles')
    me = bpy.data.meshes.new(name)
    me.from_pydata(V.tolist(), [], F.tolist())
    me.update()
    ob = B.link(bpy.data.objects.new(name, me))
    ob.hide_render = True
    ob.display_type = 'WIRE'
    k.guide = ob
    return ob


def _tree(guide):
    key = (guide.name, len(guide.data.polygons))
    if key not in _TREES:
        me = guide.data
        _TREES[key] = BVHTree.FromPolygons([tuple(v.co) for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    return _TREES[key]


def _plane_axes(d):
    """In-plane axes of the section plane with normal d: u is the one nearest world X (the creature's
    width), or nearest Y when the plane's normal is X itself; w completes it."""
    d = Vector(d).normalized()
    ref = Vector((1, 0, 0)) if abs(d.x) < 0.9 else Vector((0, 1, 0))
    u = (ref - d * ref.dot(d)).normalized()
    w = d.cross(u).normalized()
    if (abs(w.z) > 0.5 and w.z < 0) or (abs(w.z) <= 0.5 and w.y > 0):
        w = -w                                   # w points up, or toward the head for a horizontal cut
    return u, w


def hull_sections(guide, a, b, n=5, label=None):
    """The guide's cross-section at n stations along the segment a -> b (two joint positions), each cut
    square to the segment. Per station a dict: t (0..1), at (the point on the segment), centre (xyz of
    the section's bounding-box middle), width (extent along `u`, the in-plane axis nearest world X),
    depth (extent along `w`, the other in-plane axis: height for a spine cut, front-to-back for a leg
    cut), lo/hi (the two corners of that box as (u, w) offsets from `at`), inside (the segment point
    lies inside the section). Where several outlines are cut (two legs, a leg and the belly) the one
    round the segment point is taken, else the nearest. With label, the table is printed.
    A ring is then placed from numbers: centre +- width/2 along u, +- depth/2 along w."""
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    u, w = _plane_axes(d)
    out = []
    for i in range(n):
        t = i / (n - 1) if n > 1 else 0.5
        p = a.lerp(b, t)
        bm = bmesh.new()
        bm.from_mesh(guide.data)
        r = bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), dist=1e-7,
                                   plane_co=p, plane_no=d, clear_inner=False, clear_outer=False)
        cut = [g for g in r['geom_cut'] if isinstance(g, bmesh.types.BMEdge)]
        nb = {}
        for e in cut:
            nb.setdefault(e.verts[0], []).append(e.verts[1]); nb.setdefault(e.verts[1], []).append(e.verts[0])
        seen, comps = set(), []
        for v in nb:
            if v in seen:
                continue
            comp, st = [], [v]
            seen.add(v)
            while st:
                x = st.pop(); comp.append(x)
                for y in nb[x]:
                    if y not in seen:
                        seen.add(y); st.append(y)
            comps.append(comp)
        best = None
        for comp in comps:
            P = np.array([((v.co - p).dot(u), (v.co - p).dot(w)) for v in comp])
            ang = np.sort(np.arctan2(P[:, 1], P[:, 0]))
            gap = np.max(np.diff(np.concatenate([ang, ang[:1] + 2 * math.pi]))) if len(ang) > 2 else 7.0
            inside = bool(gap < math.pi)                    # the outline goes all the way round the point
            near = float(np.min(np.hypot(P[:, 0], P[:, 1])))
            score = (0 if inside else 1, near)
            if best is None or score < best[0]:
                best = (score, P, inside)
        bm.free()
        if best is None:
            out.append(dict(t=round(t, 3), at=tuple(p), centre=None, width=0.0, depth=0.0, inside=False))
            continue
        _, P, inside = best
        lo, hi = P.min(0), P.max(0)
        c = p + u * float((lo[0] + hi[0]) / 2) + w * float((lo[1] + hi[1]) / 2)
        out.append(dict(t=round(t, 3), at=tuple(round(x, 4) for x in p), centre=tuple(round(x, 4) for x in c),
                        width=round(float(hi[0] - lo[0]), 4), depth=round(float(hi[1] - lo[1]), 4),
                        lo=(round(float(lo[0]), 4), round(float(lo[1]), 4)),
                        hi=(round(float(hi[0]), 4), round(float(hi[1]), 4)), inside=inside))
    if label:
        B.say(f'sections {label}: u = ({u.x:+.2f}, {u.y:+.2f}, {u.z:+.2f}) width, w = ({w.x:+.2f}, {w.y:+.2f}, {w.z:+.2f}) depth')
        for s in out:
            if s['centre'] is None:
                B.say(f"  t {s['t']:.2f}  no section"); continue
            B.say("  t %.2f  centre (%+.3f, %+.3f, %+.3f)  width %.3f  depth %.3f%s"
                  % (s['t'], *s['centre'], s['width'], s['depth'], '' if s['inside'] else '  (segment point outside)'))
    return out


def fit_to_guide(verts, guide, max_move=0.05, mode='plane', centre=None):
    """Shrinkwrap cage vertices onto the guide, each by at most max_move (metres).
    verts: one ring (a list of BMVerts) or a list of rings.
    mode 'plane': each vertex slides in its ring's own best-fit plane, along the ray from the ring's
      centre (on x = 0 when the ring touches the seam; or `centre`) through the vertex, to the guide
      crossing nearest its present position: the ring keeps its plane and its vertex order.
    mode 'nearest': each vertex goes to the nearest point of the guide surface.
    Seam vertices (x = 0) stay on x = 0. Returns (vertices moved, vertices that hit max_move)."""
    verts = list(verts)
    rings = verts if verts and isinstance(verts[0], (list, tuple)) else [verts]
    tree = _tree(guide)
    moved = capped = 0
    for rg in rings:
        if not rg:
            continue
        seamv = {v for v in rg if abs(v.co.x) < B.SEAM}
        planar = mode == 'plane' and len(rg) >= 3
        if planar:
            P = np.array([v.co[:] for v in rg], np.float64)
            c = Vector(centre) if centre is not None else Vector(P.mean(0))
            if seamv and centre is None:
                c.x = 0.0
            n = Vector(np.linalg.svd(P - P.mean(0))[2][-1])
        for v in rg:
            target = None
            if planar:
                o = c + n * (v.co - c).dot(n)                 # the ray stays in the vertex's own plane
                r = v.co - o
                if v in seamv:
                    r.x = 0.0
                if r.length > 1e-9:
                    r.normalize()
                    org, bestd = o.copy(), None
                    for _ in range(8):                        # every crossing along the ray: take the nearest to v
                        hit = tree.ray_cast(org, r)
                        if hit[0] is None:
                            break
                        dd = (hit[0] - v.co).length
                        if bestd is None or dd < bestd:
                            bestd, target = dd, hit[0].copy()
                        org = hit[0] + r * 1e-5
            if target is None:
                target = tree.find_nearest(v.co)[0]
            if target is None:
                continue
            dv = target - v.co
            if v in seamv:
                dv.x = 0.0
            if dv.length > max_move:
                dv *= max_move / dv.length
                capped += 1
            if dv.length > 1e-7:
                v.co += dv
                moved += 1
            if v in seamv:
                v.co.x = 0.0
    B._fresh([v for rg in rings for v in rg])
    return moved, capped


# ---------------------------------------------------------------- the part guide (an implicit base, part by part)
# carve_guide intersects three whole-body silhouettes: limb sections come out as boxes, the top third of a leg has
# no shape (it is behind the body), and an arm takes its depth from the torso. part_guide builds the same hidden
# guide from PARTS placed on J: a torso, limb chains, a head, ears / tails, each a swept section sized from the
# view that can see it and from a mass prior where none can, joined with a small smooth union.
# An UPRIGHT BIPED (the spine runs up) is read differently from a quadruped: its torso is a stack of sections with
# the arms masked out (chest, belly and pelvis masses are named on it); its head is a stack of level sections from
# the chin to the crown, measured without the ears and the nose (cranium over the nose root, jaw under it, brow and
# cheek masses in the corners) and the nose is a part of its own ('nose', the head -> snout chain's thin end); a
# limb's depth is never read from a side run that crosses the torso or another limb.
# Everywhere: a limb whose tip joint is on the ground ends in a FOOT, a wedge along the ground from heel to toe
# ('<limb>_foot': height from the side view, width from the FRONT view, so a plan run through the claws cannot
# shrink a paw); a limb that hangs ends in a HAND, a tapered palm block; an ear (a chain whose joints are named
# ear*) is a thin tapered leaf; joints named tail* / ear* that the plan leaves out are added as extra chains.
# LIMITS: a silhouette is a union, so what overlaps in every view that sees a dimension comes out fat (a quadruped's
# leg width is fore + hind leg in the front view; the neck over the shoulders in plan). Ears and horns that J does
# not name are opened out of the masks and are not in the guide. Hidden stations (src 'prior') are anatomy by
# rule, not by the sheet; a leaf's thickness and a hand's are rules too (PART['leaf'], PART['hand_flat']).
PART = dict(
    blend=0.018,             # smooth-union radius between parts, x the creature's height (small: masses stay distinct)
    # section exponents: 2 = ellipse, larger = boxier. Limbs are rounded boxes (the low-poly study: 3 - 3.5), the
    # torso and the head stay rounder. A limb ring's front and back are flat edges limb_front x its width long
    # (part_rings 'pts').
    limb_front=0.5,
    torso_p=2.4, limb_p=3.2, head_p=2.3, muzzle_p=2.6, foot_p=3.0, hand_p=3.2, jaw_p=2.6,
    root_p=2.2,              # a hidden limb root is rounder than the limb (it is a mass under the skin, not a post)
    knuckle=0.07,            # swell of a limb section at an inner joint (elbow, knee, hock, wrist)
    root_gain=(1.15, 1.3),   # hidden limb root (upper arm / thigh): width, depth at the root x the nearest visible station
    root_gain_biped=(1.2, 1.25),   # the same for an upright biped (a deltoid, not a haunch)
    aspect=1.15,             # depth / width of a limb where only one of them can be seen and no station shows both
    aspect_max=2.2,          # a limb section is never flatter than this (two legs drawn as one silhouette)
    side_max=1.7,            # biped: a limb's side run over this x its front width is not the limb alone (dropped)
    tuck=0.94,               # quadruped torso width x this, so the shoulder and haunch masses stand proud of the flank
    per_bone=8, jump=2.5,    # stations per bone; a limb run over this x the limb's median run has left the limb
    open=0.045,              # ears / spikes thinner than 2 x this x height are opened out of the masks the trunk is read from
    stop=0.62,               # the muzzle is the tip end of the head whose width is under this x the widest station
    masses=True, mass=1.0,   # brow, cheek / jaw, scapula and haunch masses; the size of the brow and cheek masses
    foot_z=0.07,             # a limb whose tip joint is under this x height stands on a foot wedge; otherwise it ends in a hand
    hand_flat=0.6,           # palm thickness / width where no view shows the thickness; fingers taper to hand_tip x the palm
    hand_tip=0.55,
    leaf=0.2,                # ear thickness / ear breadth
    belly=0.35,              # biped pot belly: the dome stands this x its own depth proud of the side view's belly line (0 = no dome)
    neck=0.7,                # biped neck: at most this x the jaw's width and depth (the head hides the rest)
    nose=0.42,               # biped nose: its root is at most this x the skull's width
    chin=0.75,               # biped jaw: width at the chin x the width at the cheek
    head_deep=1.3,           # biped head: depth is at most this x the head's width (where the back of the skull is hidden)
    skull=0.3,               # biped skull behind an ear: the hidden outline bows out by this x the hidden height
    sides=dict(limb=6, extra=6, foot=6, nose=4, leaf=4, torso=8, neck=8, head=8),   # part_budget: ring side counts
    torso_fill=False,        # quadruped torso: True = its WIDTH under the limb roots (the plan run the limbs were painted out of)
                             # is the line between the nearest untouched stations, as its depth already is; False = as read
)
_SEEN = ('side', 'front', 'rear', 'top')
_VN = dict(side=np.array((1.0, 0, 0)), front=np.array((0, 1.0, 0)), top=np.array((0, 0, 1.0)))


def _axes(d):
    u, w = _plane_axes(d)
    return np.array(u), np.array(w)


def _span(view, M, p, ax, reach=0.03):
    """(lo, hi): the mask run through the world point p along ax, metres from p in the view plane; None when
    the axis points at the camera or p is over `reach` from the figure."""
    s = view.s
    r0, c0 = view.pix(p[0], p[1], p[2])
    r1, c1 = view.pix(p[0] + ax[0], p[1] + ax[1], p[2] + ax[2])
    dr, dc = (r1 - r0) * s, (c1 - c0) * s
    n = math.hypot(dr, dc)
    if n < 0.5:
        return None
    dr, dc = dr / n, dc / n
    H, W = M.shape
    ins = lambda t: 0 <= int(r0 + dr * t) < H and 0 <= int(c0 + dc * t) < W and bool(M[int(r0 + dr * t), int(c0 + dc * t)])
    t0 = next((t for k in range(int(reach / s) * 2) for t in (k * 0.5, -k * 0.5) if ins(t)), None)
    if t0 is None:
        return None
    a = b = t0
    while ins(a - 0.5):
        a -= 0.5
    while ins(b + 0.5):
        b += 0.5
    return ((a - 0.25) * s, (b + 0.25) * s)


def _stations(J, names, n, tip_over=0.0, root_over=0.0):
    """Stations along a joint chain: n per bone (at (i + 0.5) / n), one at every joint, and beyond either end
    (`*_over` metres; the caller drops the ones past the end of the drawing)."""
    P = [np.array(J[x], float) for x in names]
    L = [float(np.linalg.norm(b - a)) for a, b in zip(P, P[1:])]
    tot = sum(L)
    out, done = [], 0.0
    mk = lambda at, bi, s, joint=None, over=False: dict(at=at, bone=bi, s=s, joint=joint, over=over,
                                                         d=(P[bi + 1] - P[bi]) / L[bi])
    step = L[0] / n
    for j in range(int(root_over / step), 0, -1):
        out.append(mk(P[0] - (P[1] - P[0]) / L[0] * step * j, 0, -step * j / tot, over=True))
    for bi in range(len(L)):
        out.append(mk(P[bi], bi, done / tot, joint=names[bi]))
        out += [mk(P[bi] + (P[bi + 1] - P[bi]) * (i + 0.5) / n, bi, (done + L[bi] * (i + 0.5) / n) / tot) for i in range(n)]
        done += L[bi]
    out.append(mk(P[-1], len(L) - 1, 1.0, joint=names[-1]))
    step = L[-1] / n
    for j in range(1, int(tip_over / step) + 1):
        out.append(mk(P[-1] + (P[-1] - P[-2]) / L[-1] * step * j, len(L) - 1, 1.0 + step * j / tot, over=True))
    out = [st for st in out if not (st['over'] and st['at'][2] < 0.0)]
    D = [(b - a) / l for a, b, l in zip(P, P[1:], L)]
    for st in out:
        st['u'], st['w'] = _axes(st['d'])
        i = names.index(st['joint']) if st['joint'] else -1
        bend = math.acos(max(-1.0, min(1.0, float(np.dot(D[i - 1], D[i]))))) if 0 < i < len(D) else 0.0
        st['cap'] = min(1.0, 0.03 + 1.1 * math.tan(bend / 2))
    return out, tot


def _trim(view, M, p, ax, sp):
    """The run sp (found on the whole mask) with each end walked inward while it is off the painted mask M."""
    s = view.s
    r0, c0 = view.pix(p[0], p[1], p[2])
    r1, c1 = view.pix(p[0] + ax[0], p[1] + ax[1], p[2] + ax[2])
    dr, dc = (r1 - r0) * s, (c1 - c0) * s
    n = math.hypot(dr, dc)
    dr, dc = dr / n, dc / n
    H, W = M.shape
    ins = lambda t: 0 <= int(r0 + dr * t) < H and 0 <= int(c0 + dc * t) < W and bool(M[int(r0 + dr * t), int(c0 + dc * t)])
    a, b = sp[0] / s + 0.25, sp[1] / s - 0.25
    while a < b and not ins(a):
        a += 0.5
    while b > a and not ins(b):
        b -= 0.5
    return ((a - 0.25) * s, (b + 0.25) * s)


def _measure(views, M, st, thresh=0.5, M0=None):
    """Every view's run through a station, per dimension: st['raw'] = {dim: {view: (lo, hi)}}. A view sees a
    dimension when its plane holds both the bone and that axis (front and rear are one silhouette drawn twice:
    both are read); front / rear / top runs are averaged with their mirror. With M0 (the masks before other parts
    were painted out of M) the runs are found on M0 (st['raw0']) and st['raw'] is each of them with its ends
    walked inward off the paint (see _clean)."""
    st['raw'], raw0 = {}, {}
    mir = np.array((-1.0, 1, 1))
    for dim, ax in (('width', st['u']), ('depth', st['w'])):
        c = np.cross(st['d'], ax)
        got, got0 = {}, {}
        for v, nrm in _VN.items():
            if abs(float(np.dot(c, nrm))) < thresh:
                continue
            for vn in ((v,) if v != 'front' else ('front', 'rear')):
                cuts = [(st['at'], ax)] + ([(st['at'] * mir, ax * mir)] if v != 'side' else [])
                sp = [(_span(views[vn], (M if M0 is None else M0)[vn], p_, a_), p_, a_) for p_, a_ in cuts]
                sp = [x for x in sp if x[0]]
                if sp:
                    avg = lambda L_: (sum(x[0] for x in L_) / len(L_), sum(x[1] for x in L_) / len(L_))
                    got0[vn] = avg([x[0] for x in sp])
                    got[vn] = got0[vn] if M0 is None else avg([_trim(views[vn], M[vn], p_, a_, x) for x, p_, a_ in sp])
        st['raw'][dim], raw0[dim] = got, got0
    if M0 is not None:
        st['raw0'] = raw0
    st['spans'] = {k_: dict(v) for k_, v in st['raw'].items()}


def _crosses(a, b, poly):
    """Does the 2D segment a-b cross the polyline?"""
    cr = lambda o, p, q: (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
    return any(cr(a, b, c) * cr(a, b, d) < 0 and cr(c, d, a) * cr(c, d, b) < 0 for c, d in zip(poly, poly[1:]))


def _visible(sts, lim, jump, spine=(), others=(), side_max=0.0):
    """Drop the runs of a limb that are not its own: a run over lim or over `jump` x the limb's median run in
    that view (the thigh inside the body outline), a width run that reaches the body's midline, a side-view run
    that crosses the spine (an arm in front of the torso) or another chain of `others` (a hand over a knee), and,
    with side_max, a side-view run over side_max x the station's front-view width. The outer end of a dropped
    width run is still the silhouette: st['outer'] keeps it."""
    polys = [[(float(p[1]), float(p[2])) for p in c] for c in (spine,) + tuple(others)]
    for dim in ('width', 'depth'):
        for v in ('side', 'front', 'rear', 'top'):
            runs = [b - a for a, b in (st['spans'][dim][v] for st in sts if v in st['spans'][dim]) if b - a <= lim]
            med = float(np.median(runs)) if runs else 0.0
            for st in sts:
                sp = st['spans'][dim].get(v)
                if sp is None:
                    continue
                ax, p = (st['u'] if dim == 'width' else st['w']), st['at']
                hid = sp[1] - sp[0] > lim or sp[1] - sp[0] > jump * med
                x = abs(p[0])
                if x > 0.02 and abs(ax[0]) > 0.5 and v != 'side':
                    sg = 1.0 if ax[0] * p[0] > 0 else -1.0
                    hid |= x + min(sg * sp[0], sg * sp[1]) * abs(ax[0]) < 0.15 * x
                    st['outer'] = min(st.get('outer', 9.0), max(sg * sp[0], sg * sp[1]))
                if v == 'side':
                    hid |= any(len(q) > 1 and _crosses(tuple((p + ax * sp[0])[1:]), tuple((p + ax * sp[1])[1:]), q) for q in polys)
                    if side_max:
                        fw = [b - a for o in ('width', 'depth') for w_, (a, b) in st['spans'][o].items() if w_ in ('front', 'rear')]
                        hid |= bool(fw) and sp[1] - sp[0] > side_max * min(fw)
                if hid:
                    del st['spans'][dim][v]


def _one_sided(sts, floor):
    """A head's section cut runs on into the neck or the chest on one side (the throat): walking tip -> root,
    a side whose extent steps up by 1.8 x and by over `floor` is held at its last own value from there on."""
    for dim in ('width', 'depth'):
        for v in ('side', 'front', 'rear', 'top'):
            for k_ in (0, 1):
                prev, held = None, False
                for st in reversed(sts):
                    sp = st['spans'][dim].get(v)
                    if sp is None:
                        continue
                    e = abs(sp[k_])
                    held |= prev is not None and e > 1.8 * prev and e - prev > floor
                    if held:
                        sp = list(sp); sp[k_] = math.copysign(prev, sp[k_]); st['spans'][dim][v] = tuple(sp)
                        st['held'] = True
                    else:
                        prev = e


def _clean(sts, px, mode='interp', dims=('width', 'depth'), bulge=0.0):
    """Runs read on masks with other parts painted out (st['spans']) against the same runs on the whole
    masks (st['raw0']): an end the paint moved is not the part's own outline. Such an end becomes, by mode,
    'interp': the line between the nearest untouched stations (a belly across the leg roots); 'trim': the painted
    end where that is plausible (it keeps over a quarter of the whole run's extent), else the line; 'max': the
    larger of the two. With neither, the whole run's end stays. mode may be a pair (the run's low end, its high end).
    bulge: the line bows out by bulge x the length of the gap it spans (a skull behind an ear is a dome)."""
    idx = np.arange(len(sts))
    for dim in dims:
        for v in ('side', 'front', 'rear', 'top'):
            have = [i for i, st in enumerate(sts) if v in st['raw0'].get(dim, {})]
            if not have:
                continue
            for k_, sg in ((0, -1.0), (1, 1.0)):
                mode_ = mode if isinstance(mode, str) else mode[k_]
                e0 = np.array([sg * sts[i]['raw0'][dim][v][k_] for i in have])
                e1 = np.array([sg * sts[i]['spans'][dim][v][k_] if v in sts[i]['spans'][dim] else np.nan for i in have])
                flag = np.isnan(e1) | (np.abs(e0 - e1) > 1.5 * px[v])
                if not flag.any():
                    continue
                okp = ~np.isnan(e1) & (e1 > 0.25 * e0) & (e1 > 0)
                line = np.interp(idx[have], np.array(have)[~flag], e0[~flag]) if (~flag).any() else None
                if line is not None and bulge:
                    ok_i = np.array(have)[~flag]
                    for j, i in enumerate(have):
                        lo_, hi_ = ok_i[ok_i < i], ok_i[ok_i > i]
                        if flag[j] and len(lo_) and len(hi_):
                            t = (i - lo_[-1]) / (hi_[0] - lo_[-1])
                            line[j] += bulge * float(np.linalg.norm(sts[hi_[0]]['at'] - sts[lo_[-1]]['at'])) * 4 * t * (1 - t)
                for j, i in enumerate(have):
                    if not flag[j]:
                        continue
                    c = [e1[j]] if okp[j] else []
                    if line is not None and not (mode_ == 'trim' and c):
                        c = [line[j]] if mode_ == 'interp' else c + [line[j]]
                    e = min(max(c), e0[j]) if c else e0[j]
                    sp = list(sts[i]['spans'][dim].get(v, sts[i]['raw0'][dim][v])); sp[k_] = sg * e
                    sts[i]['spans'][dim][v] = tuple(sp); sts[i]['held'] = True


def _occupancy(views, M, sts, mirror, only=('side', 'front', 'rear', 'top'), pad=1.5):
    """Paint a part's sections out of the masks M (in place), whatever view each dimension came from (an arm in
    front of the torso in the side view): per station, the section's longer projected axis as a thick stroke."""
    mir = np.array((-1.0, 1, 1))
    for a, b in zip(sts, sts[1:] + sts[-1:]):
        ca, cb = np.asarray(a['centre'], float), np.asarray(b['centre'], float)
        for v in only:
            n = _VN['front' if v == 'rear' else v]
            ax = sorted(((a['u'] - n * np.dot(a['u'], n)) * a['width'] / 2, (a['w'] - n * np.dot(a['w'], n)) * a['depth'] / 2),
                        key=lambda e: float(np.linalg.norm(e)))
            th = max(float(np.linalg.norm(ax[0])), 0.3 * float(np.linalg.norm(cb - ca))) / views[v].s + pad
            for f in (0.0, 0.34, 0.67):
                c = (1 - f) * ca + f * cb
                for m_ in ((1,) if v == 'side' or not mirror else (1, -1)):
                    (r0, c0), (r1, c1) = (views[v].pix(*((c + sg * ax[1]) * (mir if m_ < 0 else 1))) for sg in (-1, 1))
                    ra, rb = max(0, int(min(r0, r1) - th)), min(M[v].shape[0], int(max(r0, r1) + th) + 2)
                    ca_, cb_ = max(0, int(min(c0, c1) - th)), min(M[v].shape[1], int(max(c0, c1) + th) + 2)
                    if ra >= rb or ca_ >= cb_:
                        continue
                    R, C = np.mgrid[ra:rb, ca_:cb_]
                    er, ec = r1 - r0, c1 - c0
                    t = np.clip(((R - r0) * er + (C - c0) * ec) / max(1e-9, er * er + ec * ec), 0, 1)
                    M[v][ra:rb, ca_:cb_] &= np.hypot(R - r0 - t * er, C - c0 - t * ec) > th


def _resolve(sts):
    """Per station and dimension: the tightest of the runs left (an occluder only ever adds), its middle as the
    centre offset. -> arrays val (n, 2: width, depth; nan = unseen), off (n, 2), and st['src']."""
    n = len(sts)
    val, off = np.full((n, 2), np.nan), np.zeros((n, 2))
    for i, st in enumerate(sts):
        st['src'] = {}
        for k_, dim in enumerate(('width', 'depth')):
            sp = st['spans'][dim]
            if sp:
                v = min(sp, key=lambda q: sp[q][1] - sp[q][0])
                val[i, k_], off[i, k_] = sp[v][1] - sp[v][0], (sp[v][0] + sp[v][1]) / 2
                st['src'][dim] = v
    return val, off


def _open3(a, win=1):
    """Morphological opening along the stations (min then max): an ear or a horn crossing the cut is a spike."""
    P = np.pad(a, win, mode='edge')
    lo = np.min([P[i:i + len(a)] for i in range(2 * win + 1)], axis=0)
    P = np.pad(lo, win, mode='edge')
    return np.max([P[i:i + len(a)] for i in range(2 * win + 1)], axis=0)


def _open_mask(m, r):
    """Box opening of a mask (half size r pixels): ears, claws and fur spikes thinner than 2 r go; the bulk stays."""
    def box(a, n):
        I = np.zeros((a.shape[0] + 1, a.shape[1] + 1), np.int32)
        I[1:, 1:] = a.astype(np.int32).cumsum(0).cumsum(1)
        P = np.pad(I, ((r, r), (r, r)), mode='edge')
        H, W = a.shape
        return P[2 * r + 1:2 * r + 1 + H, 2 * r + 1:2 * r + 1 + W] - P[:H, 2 * r + 1:2 * r + 1 + W] \
            - P[2 * r + 1:2 * r + 1 + H, :W] + P[:H, :W]
    if r < 1:
        return m
    er = box(m, r) == (2 * r + 1) ** 2
    return box(er, r) > 0


def _smooth1(a, passes=1):
    for _ in range(passes):
        a = np.concatenate([a[:1], 0.25 * a[:-2] + 0.5 * a[1:-1] + 0.25 * a[2:], a[-1:]]) if len(a) > 2 else a
    return a


def _fill_nan(a, default):
    ok = ~np.isnan(a)
    if not ok.any():
        return np.full(len(a), default)
    idx = np.arange(len(a))
    return np.interp(idx, idx[ok], a[ok])


def _finish(sts, val, off, p, kind, joints, mirror):
    for i, st in enumerate(sts):
        st['width'], st['depth'] = float(max(val[i, 0], 1e-3)), float(max(val[i, 1], 1e-3))
        st['centre'] = st['at'] + st['u'] * off[i, 0] + st['w'] * off[i, 1]
        st.setdefault('p', p)
    return dict(kind=kind, joints=list(joints), mirror=mirror, stations=sts)


def _paint(views, M, sts, pad=2):
    """Remove a part's seen stations (each dimension in the view it was taken from) from the working masks, so the
    torso and the head are measured without it."""
    mir = np.array((-1.0, 1, 1))
    for v in M:
        Mv = M[v]
        for a, b in zip(sts, sts[1:] + sts[-1:]):
            for dim in ('width', 'depth'):
                sp = a['spans'][dim].get(v)
                if sp is None or a.get('src', {}).get(dim) != v:
                    continue
                ax = a['u'] if dim == 'width' else a['w']
                th = max(3.0, 1.6 * float(np.linalg.norm(b['at'] - a['at'])) / views[v].s) / 2 + pad
                for m_ in ((1,) if v == 'side' else (1, -1)):
                    (r0, c0), (r1, c1) = (views[v].pix(*((a['at'] + ax * (t + sg * pad * views[v].s)) * (mir if m_ < 0 else 1)))
                                          for t, sg in ((sp[0], -1), (sp[1], 1)))
                    ra, rb = max(0, int(min(r0, r1) - th)), min(Mv.shape[0], int(max(r0, r1) + th) + 2)
                    ca, cb = max(0, int(min(c0, c1) - th)), min(Mv.shape[1], int(max(c0, c1) + th) + 2)
                    if ra >= rb or ca >= cb:
                        continue
                    R, C = np.mgrid[ra:rb, ca:cb]
                    er, ec = r1 - r0, c1 - c0
                    t = np.clip(((R - r0) * er + (C - c0) * ec) / max(1e-9, er * er + ec * ec), 0, 1)
                    Mv[ra:rb, ca:cb] &= np.hypot(R - r0 - t * er, C - c0 - t * ec) > th


def _limb(views, M, J, names, K, H, spine, tip_over=None, others=(), biped=False, hand=False, skip=()):
    """A limb chain as a swept ellipse. Seen stations take width and depth from the masks; a dimension no view
    separates is the other one x the limb's own aspect; a station no view separates at all (the thigh inside the
    body outline, the upper arm on the torso) is the nearest seen station x a root gain (the widest part of a limb
    is its root mass). Inner joints get a knuckle. biped: see _visible (others, side_max). hand: the last bone is a
    tapered palm block (width capped at the palm's, thickness by rule where unseen, fingers closing to hand_tip)."""
    P = [np.array(J[x], float) for x in names]
    last = float(np.linalg.norm(P[-1] - P[-2]))
    sts, tot = _stations(J, names, K['per_bone'], tip_over=0.6 * last if tip_over is None else tip_over)
    for st in sts:
        _measure(views, M, st)
    while sts and sts[-1]['over'] and not any(sts[-1]['raw'].values()):
        sts.pop()                                                       # past the end of the drawing
    for st in sts:
        if st['joint'] and st['joint'] not in (names[0], names[-1]):
            st['spans'] = dict(width={}, depth={})                      # a cut at a bend is no section
        for v in skip:                                                  # a tail behind the body: the front view shows the legs' gap
            st['spans']['width'].pop(v, None); st['spans']['depth'].pop(v, None)
    _visible(sts, max(0.6 * tot, 0.3 * H), K['jump'], spine, others, K['side_max'] if biped else 0.0)
    val, off = _resolve(sts)
    both = ~np.isnan(val).any(1)
    n = len(sts)
    asp = float(np.median(val[both, 1] / val[both, 0])) if both.any() else K['aspect']
    for i in range(n):                                                  # one dimension seen: the other from the aspect
        if np.isnan(val[i, 0]) != np.isnan(val[i, 1]):
            a_ = asp
            k_ = 0 if np.isnan(val[i, 0]) else 1
            val[i, k_] = val[i, 1] / a_ if k_ == 0 else val[i, 0] * a_
            sts[i]['src'][('width', 'depth')[k_]] = 'aspect'
    seen = ~np.isnan(val[:, 0])
    if not seen.any():
        val[:] = (0.14 * tot, 0.14 * tot * K['aspect'])
        seen[:] = True
    first = int(np.argmax(seen))                                        # root side: the mass prior
    s0 = max(sts[first]['s'], 1e-6)
    nb = [i for i in range(n) if seen[i] and sts[i]['bone'] == sts[first]['bone'] and not sts[i]['joint']] or [first]
    base = np.median(val[nb], axis=0)                                   # the nearest seen bone, not its one root-most cut
    for i in range(first):
        tau = min(1.0, (s0 - sts[i]['s']) / s0) ** 0.7
        val[i] = base * (1 + (np.array(K['root_gain_biped' if biped else 'root_gain']) - 1) * tau)
        off[i] = off[first] * (1 - tau)
        sts[i]['src'] = dict(width='prior', depth='prior')
    for k_ in (0, 1):
        val[:, k_] = _fill_nan(val[:, k_], 0.1 * tot)
    for i, st in enumerate(sts):
        if st['src'].get('width') in ('prior', 'aspect') and st.get('outer', 9.0) < 9.0:
            val[i, 0] = min(val[i, 0], 2 * max(st['outer'], 0.25 * val[i, 0]))      # inside the plan / front outline
            if biped and st['src']['width'] == 'aspect' and i >= first:                # the bone runs down the limb's middle
                val[i, 0] = max(val[i, 0], min(2 * st['outer'], 1.6 * val[i, 0]))
        lo = min(val[i]) * K['aspect_max']                             # two legs or a loincloth in one silhouette
        if max(val[i]) > lo and not st['over']:
            val[i] = np.minimum(val[i], lo)
    e = max((i for i, st in enumerate(sts) if not st['over']), default=n - 1)
    for i in range(e + 1, n):                                           # the tip closes in both dimensions
        val[i] = val[e] * min(1.0, float(np.min(val[i] / val[e])))
    for k_ in (0, 1):
        val[:, k_] = _smooth1(val[:, k_])
        off[:, k_] = _smooth1(off[:, k_], 2)
    if hand:
        lb = len(names) - 2
        own = [i for i, st in enumerate(sts) if st['bone'] == lb and st['joint'] != names[lb]]
        palm = float(np.median([val[i, 0] for i in own if not sts[i]['over']] or [val[own[0], 0]]))
        while len(own) > 2 and sts[own[-1]]['over'] and sts[own[-1]]['src'].get('width') not in _SEEN:
            own.pop(); sts.pop(); val, off = val[:-1], off[:-1]         # past the fingertips: another part's silhouette
        n = len(sts)
        s0_, s1 = sts[own[0]]['s'], sts[-1]['s']
        s_f = s0_ + 0.67 * (s1 - s0_)
        for i in own:
            st = sts[i]
            val[i, 0] = min(val[i, 0], palm)
            if st['src'].get('depth') not in _SEEN:
                val[i, 1] = K['hand_flat'] * val[i, 0]; st['src']['depth'] = 'rule'
            f = (st['s'] - s_f) / max(1e-6, s1 - s_f)                    # the fingers: the last third closes to hand_tip
            if f > 0:
                val[i] *= 1 + (K['hand_tip'] - 1) * min(1.0, f)
            st['p'] = K['hand_p']; st['mass'] = 'hand'
    for i, st in enumerate(sts):                                        # knuckles
        if st['joint'] and 0 < i < n - 1 and st['joint'] not in (names[0], names[-1]):
            val[i] = 0.5 * (val[i - 1] + val[i + 1]) * (1 + K['knuckle'])
    e0 = max((st['s'] for st in sts if st['bone'] == 0), default=0.0)
    e1 = max((st['s'] for st in sts if st['bone'] <= 1), default=e0)
    a_, b_ = 0.4 * e0, e0 + 0.5 * (e1 - e0) if e1 > e0 else e0
    for st in sts:                                                      # the root bone is a mass, rounder; the box comes in below the first joint
        if 'p' not in st and st['s'] < b_ and b_ > a_:
            st['p'] = K['root_p'] + (K['limb_p'] - K['root_p']) * min(1.0, max(0.0, (st['s'] - a_) / (b_ - a_)))
    part = _finish(sts, val, off, K['limb_p'], 'limb', names, True)
    part['hidden_root'] = first
    return part


def _tube(views, M, J, names, K, H, p, kind, root_over=0.0, tip_over=0.0, tuck=1.0, M0=None, mode='interp',
          dims=('width', 'depth'), only=None):
    """A midline tube (the torso, the neck): sections sized from the masks M with the limbs painted out. M0 = the
    same masks unpainted: an end of a run the paint moved is rebuilt by _clean(mode, dims). only = {dim: views}: the
    views a dimension may be read from (an upright torso: width from the front and rear, depth from the side)."""
    sts, tot = _stations(J, names, K['per_bone'], tip_over=tip_over, root_over=root_over)
    for st in sts:
        _measure(views, M, st, 0.3, M0)
        for dim, vs_ in (only or {}).items():
            for g in ('raw', 'raw0', 'spans'):
                if g in st:
                    st[g][dim] = {v: x for v, x in st[g][dim].items() if v in vs_}
    raw = 'raw' if M0 is None else 'raw0'
    while sts and sts[-1]['over'] and not all(sts[-1][raw].values()):
        sts.pop()
    while sts and sts[0]['over'] and not all(sts[0][raw].values()):
        sts.pop(0)
    if M0 is not None:
        _clean(sts, {v: views[v].s for v in views}, mode, dims)
    val, off = _resolve(sts)
    for k_ in (0, 1):
        val[:, k_] = _fill_nan(val[:, k_], 0.2 * H)
        for i, st in enumerate(sts):
            if st['over'] and st['s'] > 1:
                val[i, k_] = min(val[i, k_], val[max(j for j, q in enumerate(sts) if not q['over']), k_])
        val[:, k_] = _smooth1(_open3(val[:, k_]), 2)
        off[:, k_] = _smooth1(off[:, k_], 3)
    off[:, 0] = 0.0
    val[:, 0] *= tuck
    return _finish(sts, val, off, p, kind, names, False)


def _foot(views, M, J, names, K, H, limb, digi=False):
    """The foot of a limb that stands on the ground: a wedge along the ground from heel to toe (stations along
    +-Y, sections upright). Heel and toe ends and the height at each station come from the side view (never over
    the ankle's height, and behind the shin's front never over the instep's: the shin is another part); the width is the FRONT view's run through the foot, held along
    the wedge (a plan run through claws or toes does not shrink it), eased at the heel and the toe tip.
    digi: the last bone stands (a dog's metatarsus): it stays in the limb, and the wedge is the paw under its tip."""
    an, toe = np.array(J[names[-2]], float), np.array(J[names[-1]], float)
    sd = views['side']
    if digi:                                                            # a paw under a near-upright last bone
        sg = -1.0 if toe[1] - an[1] < 0.25 * abs(toe[2] - an[2]) else 1.0
        az = min(float(an[2]), max(2.2 * float(toe[2]), 0.05 * H))
        an = np.array((toe[0], toe[1], az)); flen = 1.5 * az
    else:
        sg = 1.0 if toe[1] >= an[1] else -1.0
        az = max(float(an[2]), 0.035 * H)
        flen = max(abs(toe[1] - an[1]), 0.5 * az)
    ey, ex = np.array((0, 1.0, 0)), np.array((1.0, 0, 0))
    back, fwd = [], []
    for f in (0.2, 0.35, 0.5):
        sp = _span(sd, M['side'], np.array((an[0], an[1] + sg * 0.3 * flen, f * az)), ey, reach=0.05 * H)
        if sp:
            lo, hi = sorted((sg * sp[0] + 0.3 * flen, sg * sp[1] + 0.3 * flen))       # along the foot, from the ankle
            back.append(-lo); fwd.append(hi)
    heel = min(max(back), 1.0 * flen) if back else 0.35 * flen
    tip = min(max(fwd), 1.8 * flen) if fwd else 1.15 * flen
    xc = 0.5 * (an[0] + toe[0])
    Ws, mids = [], []
    for v in ('front', 'rear'):
        for f in (0.15, 0.3, 0.45, 0.6):
            for m_ in (1.0, -1.0):
                sp = _span(views[v], M[v], np.array((m_ * xc, 0.0, f * az)), ex * m_, reach=0.05 * H)
                if sp:
                    lo, hi = max(sp[0], -xc), sp[1]                                   # never past the midline
                    Ws.append(hi - lo); mids.append(xc + (lo + hi) / 2)
    seen = bool(Ws)
    W = float(np.median(Ws)) if seen else 1.3 * float(np.median([q['width'] for q in limb['stations'][-3:]]))
    xm = float(np.median(mids)) if seen else xc
    n = K['per_bone']
    sts, hs = [], []
    for i in range(n):
        f = i / (n - 1)
        y = an[1] + sg * (-heel + f * (heel + tip))
        sp = _span(sd, M['side'], np.array((xm, y, 0.012 * H)), np.array((0, 0, 1.0)), reach=0.02 * H)
        hs.append(min(0.012 * H + sp[1], 1.1 * az) if sp else np.nan)
        ease = min(1.0, 0.8 + 0.2 * f / 0.25, 0.82 + 0.18 * (1 - f) / 0.15)
        sts.append(dict(at=np.array((xm, y, 0.0)), bone=0, s=f, joint=None, over=False, d=ey * sg, u=ex, w=np.array((0, 0, 1.0)),
                        cap=0.3, width=W * ease, p=K['foot_p'], mass='foot', src=dict(width='front' if seen else 'prior', depth='side')))
    lw = float(limb['stations'][-1]['width'])
    if not digi and W < 1.25 * lw:                                      # a leg as wide as its paw: under the leg the wedge stays inside it (no cuff)
        for st in sts:
            if abs(st['at'][1] - an[1]) < 0.5 * float(limb['stations'][-1]['depth']):
                st['width'] = min(st['width'], 0.9 * lw)
    hs = _fill_nan(np.array(hs), 0.5 * az)
    shin = 0.5 * float(limb['stations'][-1]['depth'])                   # behind the shin's front the column runs up the leg:
    free = next((i for i, st in enumerate(sts) if sg * (st['at'][1] - an[1]) > shin + 0.01 * H), n - 1)
    hs[:free] = np.minimum(hs[:free], 1.15 * hs[free])                  # the instep's height holds back to the heel
    hs = np.maximum(_smooth1(hs), 0.012 * H)
    for st, h in zip(sts, hs):
        st['depth'] = float(h); st['centre'] = st['at'] + np.array((0, 0, h / 2))
    sts[0]['endcap'], sts[-1]['endcap'] = 0.12, 0.12
    return dict(kind='foot', joints=list(names[-2:]), mirror=True, stations=sts, ankle=heel / (heel + tip))


def _leaf(views, M, J, c, K, H, spine):
    """An ear: a thin tapered leaf. Its breadth is read from the sheet like a limb's; its thickness is
    PART['leaf'] x the breadth, along the section axis nearest the creature's front-back line."""
    P = _limb(views, M, J, c, dict(K, root_gain=(1.0, 1.0), root_gain_biped=(1.0, 1.0), knuckle=0.0, aspect_max=9.0, limb_p=2.0), H, spine,
              tip_over=0.5 * float(np.linalg.norm(np.array(J[c[-1]], float) - np.array(J[c[-2]], float))))
    for st in P['stations']:
        thin, broad, ab = ('width', 'depth', st['w']) if abs(st['u'][1]) >= abs(st['w'][1]) else ('depth', 'width', st['u'])
        if st['src'].get(broad) not in _SEEN and st['src'].get(thin) in _SEEN:
            st[broad] = st[thin]
        st[thin] = min(st[broad], max(K['leaf'] * st[broad], 0.012 * H))
        st['centre'] = st['at'] + ab * float(np.dot(st['centre'] - st['at'], ab))
        st['src'][thin] = 'rule'
    P['kind'] = 'leaf'
    return P


def _head(views, M, J, names, K, H):
    """The head -> snout chain: a cranium (the root end) and a muzzle / nose (the tip end, a boxier section),
    split where the width falls under K['stop'] x the widest station; a cut that runs on into the throat is held
    one-sided; plus brow and cheek / jaw masses sized from the stations they sit on."""
    sts, tot = _stations(J, names, K['per_bone'], tip_over=0.5 * H)
    for st in sts:
        _measure(views, M, st, 0.3)
    while sts and sts[-1]['over'] and not all(sts[-1]['raw'].values()):
        sts.pop()
    _one_sided(sts, 0.06 * H)
    val, off = _resolve(sts)
    for k_ in (0, 1):
        val[:, k_] = _fill_nan(val[:, k_], 0.15 * H)
        val[:, k_] = _smooth1(_open3(val[:, k_]))
        off[:, k_] = _smooth1(off[:, k_], 2)
    off[:, 0] = 0.0
    wmax = float(val[:, 0].max())
    cut = next((i for i in range(len(sts) - 1, -1, -1) if val[i, 0] >= K['stop'] * wmax), 0)
    for i, st in enumerate(sts):
        st['p'] = K['head_p'] if i <= cut else K['muzzle_p']
        st['mass'] = 'cranium' if i <= cut else 'muzzle'
    part = _finish(sts, val, off, K['head_p'], 'head', names, False)
    part['cut'] = cut
    c = sts[int(np.argmax(val[:cut + 1, 0]))]
    W, D, cc = c['width'], c['depth'], c['centre']
    part['cranium'] = dict(width=W, depth=D, centre=cc)
    masses = []
    if K['masses']:                                                     # they sit in the corners an elliptic section leaves
        fwd, m, b = (sts[cut]['s'] - c['s']) * tot, K['mass'], sts[cut]
        fr_ = dict(u=c['u'], w=c['w'], d=c['d'])
        Wb, Db = b['width'], b['depth']
        masses.append(dict(name='brow', mirror=True, centre=b['centre'] + c['w'] * 0.33 * Db + c['u'] * 0.25 * Wb, **fr_,
                           r=(0.20 * Wb * m, 0.12 * Db * m, 0.22 * Db)))
        k_ = min(range(cut + 1), key=lambda i: abs(sts[i]['s'] - (c['s'] + 0.5 * (b['s'] - c['s']))))
        ck = sts[k_]                                                    # the cheek: half way from the widest station to the stop
        masses.append(dict(name='cheek', mirror=True, centre=ck['centre'] - c['w'] * 0.20 * ck['depth'] + c['u'] * 0.30 * ck['width'], **fr_,
                           r=(0.18 * ck['width'] * m, 0.20 * ck['depth'] * m, 0.35 * fwd + 0.12 * ck['depth'])))
    return part, masses


def _head_up(views, M, M0, Mo, J, names, nj, K, H, ears=()):
    """An upright biped's head: a stack of level sections from the chin to the crown (width from the front and
    rear views, depth from the side view), read from masks with the ears and the nose painted out; the nose is the
    thin end of the head -> snout chain, a part of its own. Under the skull's widest and rear-most rows the
    section can only narrow (the shoulders and the back are not the head); the chin is where the front outline
    steps back to the throat. -> (head part, nose part or None, masses)."""
    hj, nj = np.array(J[names[0]], float), np.array(nj, float)
    Mh = {v: M[v].copy() for v in M}
    for e in ears:                                                      # the whole ear, in every view
        _occupancy(views, Mh, e['stations'], e['mirror'], pad=0.0)
    up, ex, wy = np.array((0, 0, 1.0)), np.array((1.0, 0, 0)), np.array((0, -1.0, 0))
    sp = _span(views['side'], M0['side'], hj, up)
    R = max(float(np.linalg.norm(hj - nj)), float(np.linalg.norm(np.array(J[names[-1]], float) - hj)))
    z_top = min(float(hj[2] + sp[1]) if sp else H, float(hj[2]) + 1.1 * R)   # a hump over the head is not its crown
    z_min = max(0.0, float(hj[2] - 1.3 * (z_top - hj[2])))
    nose, z_nr = None, float(hj[2])
    if len(names) > 1:
        Mn = {v: M0[v].copy() for v in M}                               # the nose is read on the sheet less the ears only
        for e in ears:
            _occupancy(views, Mn, e['stations'], e['mirror'], pad=0.0)
        old, _ = _head(views, Mn, J, names, dict(K, masses=False), H)
        cut = old['cut']
        if 0 < cut < len(old['stations']) - 2 and old['stations'][cut + 1]['depth'] < 0.8 * (z_top - hj[2]):   # thin: a nose, not the face
            ns = [dict(q) for q in old['stations'][cut:]]
            ns[0]['width'], ns[0]['depth'] = ns[1]['width'], ns[1]['depth']            # the root, inside the face
            ns[0]['centre'] = ns[0]['at'] + (ns[1]['centre'] - ns[1]['at'])
            wmax = K['nose'] * max(q['width'] for q in old['stations'])
            for q in ns:
                q['p'], q['mass'], q['width'] = K['muzzle_p'], 'nose', min(q['width'], wmax)
            nose = dict(kind='nose', joints=list(names), mirror=False, stations=ns)
            _occupancy(views, Mh, ns[1:], False, only=('side', 'top'))
            z_nr = float(ns[1]['centre'][2] + 0.5 * ns[1]['depth'])
    n = 3 * K['per_bone']
    zs = np.linspace(z_min, z_top - 0.035 * (z_top - z_min), n)           # the last row is under the crown: its cap is the dome
    sts = [dict(at=np.array((0.0, hj[1], z)), bone=0, s=0.0, joint=None, over=False, d=up, u=ex, w=wy, cap=0.3) for z in zs]
    for st in sts:
        _measure(views, Mh, st, 0.3, M0)
    px = {v: views[v].s for v in views}
    _clean(sts, px, 'max', ('width',))
    _clean(sts, px, ('max', 'trim'), ('depth',), bulge=K['skull'])                         # low end = the back (ears), high end = the face (nose)
    val, _ = _resolve(sts)
    get = lambda st, k_: st['spans']['depth'].get('side', (np.nan, np.nan))[k_]
    has = np.array(['side' in st['spans']['depth'] for st in sts])
    back = _fill_nan(np.array([hj[1] - get(st, 0) for st in sts]), hj[1])
    front = _fill_nan(np.array([hj[1] - get(st, 1) for st in sts]), hj[1])
    wid = _fill_nan(val[:, 0], 0.15 * H)
    ih = int(np.argmin(np.abs(zs - hj[2])))
    med = float(np.median(wid[ih:]))
    wid[wid > 1.35 * med] = np.nan                                      # an ear the paint missed is not the skull
    wid = _fill_nan(wid, med)
    tp = [x for x in (_span(views['top'], Mo['top'], hj * m_, ex * m_) for m_ in (1.0, np.array((-1.0, 1, 1)))) if x]
    if tp:                                                              # a head in front of the chest: the plan view has its width
        wid = np.minimum(wid, sum(x[1] - x[0] for x in tp) / len(tp))
    D = float(np.max((back - front)[ih:]))                              # for the crest's tolerance only

    def crest(a):                                                       # the first maximum walking down from the crown
        m = n - 1
        for i in range(n - 1, -1, -1):
            if a[i] > a[m]:
                m = i
            elif a[i] < a[m] - 0.04 * D:
                break
        return m
    for a in (back, wid):
        m = crest(a)
        for i in range(m - 1, -1, -1):
            a[i] = min(a[i], a[i + 1])
    back = np.minimum(back, front + K['head_deep'] * float(wid.max()))   # a skull that never clears the body behind it
    D = float(np.max((back - front)[ih:]))
    low = next((i + 1 for i in range(ih, -1, -1) if not has[i]), 0)     # under it no row is on the figure
    i0 = next((i + 1 for i in range(min(ih, n - 2), low - 1, -1) if front[i] - front[i + 1] > 0.25 * D), None)
    if i0 is None and nj[2] < hj[2] and low == 0:                       # no chin step: the neck's pinch
        lo = int(np.argmin(np.abs(zs - nj[2])))
        i0 = lo + int(np.argmin((back - front)[lo:ih + 1])) if ih > lo else lo
    i0 = low if i0 is None else i0
    i0 = min(i0, n - 4)
    sts, zs, back, front, wid = sts[i0:], zs[i0:], back[i0:], np.minimum(front[i0:], back[i0:] - 0.02 * D), wid[i0:]
    z_bot = float(zs[0])
    if nose:                                                            # the face behind the nose is no further out than the brow
        top = next((i for i in range(len(zs)) if zs[i] > z_nr), len(zs) - 1)
        front[:top] = np.maximum(front[:top], front[top])
        front = np.minimum(front, back - 0.02 * D)
    z_nr = min(max(z_nr, z_bot + 0.2 * (z_top - z_bot)), z_top)
    dep = _smooth1(back - front); mid = _smooth1((back + front) / 2); wid = _smooth1(wid)
    wraw = wid.copy()
    for i, st in enumerate(sts):
        f = min(1.0, max(0.0, (zs[i] - z_bot) / max(1e-6, z_nr - z_bot)))
        jaw = zs[i] < z_nr
        st.update(s=float((zs[i] - z_bot) / (z_top - z_bot)), width=float(max(wid[i] * (K['chin'] + (1 - K['chin']) * f ** 0.7), 1e-3)),
                  depth=float(max(dep[i], 1e-3)), centre=np.array((0.0, mid[i], zs[i])), p=K['jaw_p'] if jaw else K['head_p'],
                  mass='jaw' if jaw else 'cranium', src=dict(st.get('src', {})))
    sts[0]['endcap'], sts[-1]['endcap'] = 0.3, 0.5
    c = int(np.argmax(wid))
    part = dict(kind='head', up=True, joints=[names[0]], mirror=False, stations=sts, z_nose=z_nr,
                bottom=dict(width=float(wraw[0]), depth=float(dep[0]), back=float(back[0])),
                cranium=dict(width=float(wid[c]), depth=float(dep[c]), centre=sts[c]['centre']))
    masses = []
    if K['masses']:
        m, fr_ = K['mass'], dict(u=ex, w=wy, d=up)
        at = lambda z: int(np.argmin(np.abs(zs - z)))
        b = at(z_nr + 0.28 * (z_top - z_nr)); k_ = at(z_bot + 0.6 * (z_nr - z_bot))
        r1 = 0.11 * dep[b] * m
        masses.append(dict(name='brow', mirror=True, centre=np.array((0.23 * wid[b], front[b] + 0.45 * r1, zs[b])), **fr_,
                           r=(0.21 * wid[b] * m, r1, 0.075 * (z_top - z_bot))))
        r1 = 0.2 * dep[k_] * m
        masses.append(dict(name='cheek', mirror=True, centre=np.array((0.30 * wid[k_], front[k_] + 0.9 * r1, zs[k_])), **fr_,
                           r=(0.19 * wid[k_] * m, r1, 0.32 * (z_nr - z_bot))))
    return part, nose, masses


def _auto_extras(J, plan):
    """plan['extra'] plus the chains J names and the plan leaves out: tail* (in name order) and a pair of ear*
    joints (root = the one nearer the head joint)."""
    out = [list(c) for c in plan.get('extra', [])]
    used = set(plan['spine']) | {n for c in plan['limbs'].values() for n in c} | {n for c in out for n in c}
    tail = sorted(n for n in J if n.lower().startswith('tail') and n not in used)
    if len(tail) >= 2:
        out.append(tail)
    ears = [n for n in J if n.lower().startswith('ear') and n not in used]
    if len(ears) == 2 and plan.get('head') in J:
        hj = np.array(J[plan['head']], float)
        out.append(sorted(ears, key=lambda n: float(np.linalg.norm(np.array(J[n], float) - hj))))
    return out


def build_parts(views, J, plan, **knobs):
    """The part definitions of a creature from its sheet views, J and plan (bmkit.cage_plan): {'torso', 'neck',
    'head', 'nose' (upright bipeds), every limb, '<limb>_foot', 'extra0'.., 'masses', 'H', 'blend', 'quad',
    'biped', 'extras' (the chains behind extra0..)}. No Blender needed."""
    K = dict(PART, **knobs)
    sd = views['side']
    H = (sd.ground - sd.r0 - 1) * sd.s
    M0 = {v: views[v].mask for v in _SEEN}
    M = {v: M0[v].copy() for v in _SEEN}
    sp = plan['spine']
    ihead = sp.index(plan['head']) if plan.get('head') in sp else len(sp) - 1
    ineck = sp.index(plan['neck']) if plan.get('neck') in sp else max(ihead - 1, 0)
    Pn = np.array(J[sp[ineck]], float); P0 = np.array(J[sp[0]], float)
    sdir = (Pn - P0) / max(1e-9, np.linalg.norm(Pn - P0))
    quad = abs(sdir[1]) > 0.7
    biped = not quad and sdir[2] > 0.7
    parts, masses = {}, []
    SP = [np.array(J[x], float) for x in sp]
    extras = _auto_extras(J, plan)
    for i, c in enumerate(extras):                                      # tails, ears, horns: tapered parts
        if any(n.lower().startswith('ear') for n in c):
            parts[f'extra{i}'] = p_ = _leaf(views, M, J, c, K, H, SP)
        else:
            parts[f'extra{i}'] = p_ = _limb(views, M, J, c, dict(K, root_gain=(1.0, 1.0), root_gain_biped=(1.0, 1.0), knuckle=0.0,
                                                               aspect_max=9.0, limb_p=K['torso_p']), H, SP, tip_over=0.5 * H,
                                               skip=() if abs(J[c[0]][0]) > 1e-6 or abs(J[c[-1]][0]) > 1e-6 else ('front', 'rear'))
            p_['kind'] = 'extra'
            ss = p_['stations']                                         # a tail's root is not the rump it grows from
            for i in range(min(3, len(ss) - 2), -1, -1):
                for k_ in ('width', 'depth'):
                    ss[i][k_] = min(ss[i][k_], 1.1 * ss[i + 1][k_])
        p_['mirror'] = abs(J[c[0]][0]) > 1e-6 or abs(J[c[-1]][0]) > 1e-6
    feet = {}
    for name, c in plan['limbs'].items():
        foot = len(c) >= 3 and J[c[-1]][2] < K['foot_z'] * H
        lb = np.array(J[c[-1]], float) - np.array(J[c[-2]], float)
        digi = foot and abs(lb[2]) > 0.8 * float(np.hypot(lb[0], lb[1]))
        foot = foot and not digi
        oth = [[np.array(J[x], float) for x in o] for nm, o in plan['limbs'].items() if nm != name] if biped else ()
        parts[name] = _limb(views, M, J, c[:-1] if foot else c, K, H, SP, tip_over=0.0 if foot or digi else None, others=oth,
                            biped=biped, hand=not foot and not digi and len(c) >= 3)
        if foot or digi:
            feet[name] = (c, digi)
    for name, p_ in parts.items():
        _paint(views, M, p_['stations'])
    for name, (c, digi) in feet.items():                                # the foot wedge, and the limb's chain run on through it
        L = parts[name]
        F = parts[name + '_foot'] = _foot(views, M0, J, c, K, H, L, digi)
        _occupancy(views, M, F['stations'], True)
        if digi:
            continue
        P = [np.array(J[x], float) for x in c]
        t0 = sum(float(np.linalg.norm(b - a)) for a, b in zip(P[:-2], P[1:-1])); t1 = t0 + float(np.linalg.norm(P[-1] - P[-2]))
        for st in L['stations']:
            st['s'] *= t0 / t1
        an = L['stations'][-1]
        if len(L['stations']) > 1:                                      # no cuff: the ankle is the shin's own end,
            an['width'], an['depth'] = L['stations'][-2]['width'], L['stations'][-2]['depth']
        sole = dict(an, joint=None, s=an['s'] + 1e-4, sole=True, src=dict(an['src']))     # and the shin runs on down to the sole
        sole['at'] = an['at'] * np.array((1.0, 1, 0)); sole['centre'] = an['centre'] * np.array((1.0, 1, 0))
        sole['endcap'] = 0.1
        L['stations'].append(sole)
        fs = F['stations']
        for j in range(1, K['per_bone'] // 2 + 1):
            f = j / (K['per_bone'] // 2)
            q = fs[min(len(fs) - 1, int(round((F['ankle'] + f * (1 - F['ankle'])) * (len(fs) - 1))))]
            L['stations'].append(dict(q, bone=len(c) - 2, s=t0 / t1 + f * (1 - t0 / t1), joint=c[-1] if j == K['per_bone'] // 2 else None,
                                      foot=True, src=dict(q['src'])))
            L['stations'][-1].pop('endcap', None)
        L['joints'] = list(c)
    if biped:                                                           # limbs and ears also hide the trunk in the side view
        for name, p_ in parts.items():
            if p_['kind'] != 'foot':
                _occupancy(views, M, [q for q in p_['stations'] if not q.get('foot')], p_['mirror'], only=('side',), pad=0.0)
    if biped:                                                           # the torso stack ends where the spine leans over into the neck
        up_ = [abs(b[2] - a[2]) >= abs(b[1] - a[1]) for a, b in zip(SP[:ineck], SP[1:ineck + 1])]
        ineck = max(1, next((i for i, ok_ in enumerate(up_) if not ok_), ineck))
    r_open = {v: int(K['open'] * H / views[v].s) for v in M}
    Mo = {v: _open_mask(M0[v], r_open[v]) for v in M}                   # the trunk is read without ears and spikes
    if ihead < len(sp) - 1 or biped:
        if biped:
            parts['head'], nose, hm = _head_up(views, M, M0, Mo, J, sp[ihead:], J[sp[ineck]], K, H,
                                              ears=[p_ for p_ in parts.values() if p_['kind'] == 'leaf'])
            if nose:
                parts['nose'] = nose
        else:
            parts['head'], hm = _head(views, M, J, sp[ihead:], K, H)
            _paint(views, M, [q for q in parts['head']['stations'] if q['mass'] == 'muzzle'])
        masses += hm
    if biped and any(p_['kind'] == 'leaf' for p_ in parts.values() if 'kind' in p_):
        Mo = M0                                                         # the ears are parts: nothing to open away
    else:
        for v in M:
            M[v] = _open_mask(M[v], r_open[v])
    if ihead > ineck:
        a, b, c = (np.array(J[sp[i]], float) for i in (ineck, ihead, min(ihead + 1, len(sp) - 1)))
        bent = ihead == len(sp) - 1 or np.dot((b - a) / np.linalg.norm(b - a), (c - b) / np.linalg.norm(c - b)) < 0.87
        if biped:
            hd = parts['head']; hs = hd['stations']
            nk = _tube(views, M, J, sp[ineck:ihead + 1], K, H, K['head_p'], 'neck', M0=Mo, mode='max')
            ztop = hs[0]['centre'][2] + 0.3 * (hs[-1]['centre'][2] - hs[0]['centre'][2])
            nk['stations'] = [q for q in nk['stations'] if q['centre'][2] <= ztop]
            for q in nk['stations']:                                    # under the head the neck is no wider than the jaw
                bk = q['centre'][1] + q['depth'] / 2
                q['width'] = min(q['width'], K['neck'] * hd['bottom']['width'])
                q['depth'] = min(q['depth'], K['neck'] * hd['bottom']['depth'])
                q['centre'] = np.array((0.0, bk - q['depth'] / 2, q['centre'][2]))
            if len(nk['stations']) >= 2:
                parts['neck'] = nk
        else:
            parts['neck'] = _tube(views, M, J, sp[ineck:ihead + 1], K, H, K['head_p'], 'neck',
                                  tip_over=0.5 * H if bent else 0.0)
    if biped:
        hips = [parts[n]['stations'] for n, c in plan['limbs'].items() if n in feet]
        ro = max([P0[2] - s_[0]['at'][2] + 0.5 * float(np.median([q['width'] for q in s_[:3]])) for s_ in hips] or [0.0])
        T = parts['torso'] = _tube(views, M, J, sp[:ineck + 1], K, H, K['torso_p'], 'torso', root_over=max(ro, 0.0), M0=Mo, mode='max',
                                   only=dict(width=('front', 'rear'), depth=('side',)))
        ts = T['stations']
        ts[0]['endcap'] = 0.4
        arms = [J[c[0]] for n, c in plan['limbs'].items() if n not in feet]
        if arms:                                                        # the arms start at their shoulder joints: the torso ends there
            for q in ts:
                q['width'] = min(q['width'], 2.0 * max(abs(a_[0]) for a_ in arms))
        fy = [float((q['centre'] + q['w'] * q['depth'] / 2)[1]) for q in ts]
        nlow, nup = max(2, int(0.6 * len(ts))), max(2, int(0.45 * len(ts)))
        if K['masses'] and K['belly']:                                  # a pot belly: a dome on the belly's front
            bi = int(np.argmin(fy[:nlow])); q = ts[bi]
            r1 = 0.3 * q['depth']
            masses.append(dict(name='belly', mirror=False, centre=np.array((0.0, fy[bi] + r1 * (1 - K['belly']), q['centre'][2])),
                               u=np.array((1.0, 0, 0)), w=np.array((0, -1.0, 0)), d=np.array((0, 0, 1.0)),
                               r=(0.36 * q['width'], r1, 0.3 * (ts[-1]['centre'][2] - ts[0]['centre'][2]))))
        T['masses'] = dict(pelvis=next((i for i, q in enumerate(ts) if q['joint'] == sp[0]), 0), belly=int(np.argmin(fy[:nlow])),
                           chest=len(ts) - nup + int(np.argmax([q['width'] for q in ts[-nup:]])))
    else:
        parts['torso'] = _tube(views, M, J, sp[:ineck + 1], K, H, K['torso_p'], 'torso', root_over=0.5 * H,
                               tuck=K['tuck'], M0=Mo, mode='interp', dims=('depth', 'width') if K['torso_fill'] else ('depth',))
    if K['masses'] and quad:                                            # scapula over the foreleg root, haunch over the hind
        ts = parts['torso']['stations']
        for name, c in plan['limbs'].items():
            L = parts[name]
            if not L['hidden_root']:
                continue
            r = L['stations'][0]
            t = min(ts, key=lambda q: abs(q['at'][1] - r['at'][1]))
            hw = t['width'] / K['tuck'] / 2
            rx = 0.5 * r['width']
            cx = max(hw - rx, 0.3 * hw)
            top = t['centre'][2] + t['depth'] / 2 * (1 - min(0.95, cx / hw) ** K['torso_p']) ** (1 / K['torso_p'])
            cz = r['at'][2] + 0.3 * (top - r['at'][2])
            masses.append(dict(name=name + '_root', mirror=True, centre=np.array((cx, r['at'][1], cz)),
                               u=np.array((1.0, 0, 0)), w=np.array((0, 1.0, 0)), d=np.array((0, 0, 1.0)),
                               r=(rx, min(0.55 * r['depth'], 0.45 * t['depth']), max(top - cz, 0.3 * r['depth']))))
    parts['masses'] = masses
    parts['H'], parts['blend'], parts['quad'], parts['biped'] = H, K['blend'] * H, bool(quad), bool(biped)
    parts['extras'] = {f'extra{i}': list(c) for i, c in enumerate(extras)}
    parts['sides'], parts['limb_front'] = dict(K['sides']), K['limb_front']
    return parts


def _smin(a, b, k):
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k * 0.25


def _sub(G, lo, hi):
    return tuple(slice(max(0, int(np.searchsorted(g, a))), int(np.searchsorted(g, b))) for g, a, b in zip(G, lo, hi))


def _sweep(Dp, G, S, fu, caps, pad, sx):
    """One bone's stations S as ONE swept superellipse written into Dp by min: centre, half sizes and exponent
    are interpolated along the bone's axis (no cap between stations, so no rib where the section changes), the
    section stays in the bone's own (u, w) plane, and the two ends close with caps of caps[i] x the smaller half
    size. Distance is radial: |r| - R(direction), exact along rays from the axis. One station = an ellipsoid."""
    uu, ww, dh = fu
    C = np.array([np.asarray(q['centre'], float) for q in S])
    A = np.array([(q['width'] / 2, q['depth'] / 2, q.get('p', 2.0)) for q in S])
    R = float(A[:, :2].max()) + pad
    lo, hi = C.min(0) - R, C.max(0) + R
    if sx < 0:
        lo, hi = np.array((-hi[0], lo[1], lo[2])), np.array((-lo[0], hi[1], hi[2]))
    sl = _sub(G, lo, hi)
    if any(q.stop <= q.start for q in sl):
        return
    X = G[0][sl[0]][:, None, None] * sx - C[0, 0]
    Y = G[1][sl[1]][None, :, None] - C[0, 1]
    Z = G[2][sl[2]][None, None, :] - C[0, 2]
    zi = (C - C[0]) @ dh
    keep = np.concatenate([[True], np.diff(np.maximum.accumulate(zi)) > 1e-6])
    zi, C, A = zi[keep], C[keep], A[keep]
    ax = X * dh[0] + Y * dh[1] + Z * dh[2] + 0.0 * (X + Y + Z)
    zc = np.clip(ax, 0.0, zi[-1])
    f = lambda col: np.interp(zc.ravel(), zi, col).reshape(zc.shape) if len(zi) > 1 else col[0]
    du = X * uu[0] + Y * uu[1] + Z * uu[2] - f((C - C[0]) @ uu)
    dw = X * ww[0] + Y * ww[1] + Z * ww[2] - f((C - C[0]) @ ww)
    dz = ax - zc
    a, b, p = f(A[:, 0]), f(A[:, 1]), f(A[:, 2])
    c = np.maximum(np.where(dz < 0, caps[0], caps[1]) * np.minimum(a, b), 1e-4)
    q = (np.abs(du / a) ** p + np.abs(dw / b) ** p + np.abs(dz / c) ** p) ** (1.0 / p)
    rr = np.sqrt(du * du + dw * dw + dz * dz)
    Dp[sl] = np.minimum(Dp[sl], np.where(q > 1e-6, rr - rr / np.maximum(q, 1e-6), -np.minimum(a, b)))


def _bones(S):
    """A chain's stations split per bone: (stations from one joint to the next, the frame, the two cap factors).
    A joint's cap grows with its bend (it fills the outside of a knee and nothing on a straight run); the chain's
    root is round (it is buried in the body), its tip nearly flat."""
    out = []
    for bi in sorted({q['bone'] for q in S}):
        own = [q for q in S if q['bone'] == bi]
        if all(q.get('foot') for q in own):                             # the limb's run through its foot: swept as '<limb>_foot'
            continue
        nxt = next((q for q in S if q['bone'] == bi + 1 and not q.get('foot')), None)
        st = own + ([nxt] if nxt is not None else [])
        f = next((q for q in own if not q['joint']), own[0])
        cap = lambda q: q['endcap'] if 'endcap' in q else 1.0 if q is S[0] else 0.6 if q is S[-1] else q.get('cap', 0.3)
        out.append((st, tuple(np.asarray(f[x], float) for x in 'uwd'), (cap(st[0]), cap(st[-1]))))
    return out


def parts_field(parts, G, blend=None):
    """Signed pseudo-distance (metres, < 0 inside) of the blended parts on the grid G = (x >= 0, y, z)."""
    k = blend if blend is not None else parts['blend']
    pad = 2.5 * k + 3 * (G[2][1] - G[2][0])
    D = np.full((len(G[0]), len(G[1]), len(G[2])), 9.0, np.float32)
    for name, P in parts.items():
        if not isinstance(P, dict) or 'stations' not in P:
            continue
        Dp = np.full(D.shape, 9.0, np.float32)
        for sx in ((1.0, -1.0) if P['mirror'] else (1.0,)):
            for st, fu, caps in _bones(P['stations']):
                _sweep(Dp, G, st, fu, caps, pad, sx)
        D = _smin(D, Dp, k)
    for m_ in parts.get('masses', []):
        Dp = np.full(D.shape, 9.0, np.float32)
        one = [dict(centre=m_['centre'], width=2 * m_['r'][0], depth=2 * m_['r'][1])]
        cap = m_['r'][2] / min(m_['r'][:2])
        for sx in ((1.0, -1.0) if m_['mirror'] else (1.0,)):
            _sweep(Dp, G, one, tuple(np.asarray(m_[x], float) for x in 'uwd'), (cap, cap), pad, sx)
        D = _smin(D, Dp, k)
    return np.maximum(D, -G[2][None, None, :])                           # flat soles on z = 0


def _jsonable(o):
    if isinstance(o, dict):
        return {k_: _jsonable(v) for k_, v in o.items() if k_ not in ('raw', 'raw0', 'spans')}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, np.ndarray):
        return [round(float(x), 5) for x in o]
    if isinstance(o, (np.floating, np.integer, np.bool_)):
        return o.item()
    return o


def part_guide(k, J=None, plan=None, tris=6000, voxel_div=110, smooth=4, name='_guide', cache=None, **knobs):
    """The hidden guide built PART BY PART (see PART for the knobs; any of them as a keyword): a torso from the
    side and plan masks with the limbs removed (superellipse sections), every limb chain of J as a swept ellipse
    (seen stations from the masks, hidden ones from a mass prior, a knuckle at each joint), a head with cranium,
    brow, cheek / jaw and muzzle masses, ears / tails (plan['extra']) as tapered parts, joined by a smooth union
    of radius blend x height and contoured. Same kind of object as carve_guide (hidden, never exported, k.guide);
    the part definitions are k.guide_parts (part_rings and part_budget read them). Cached in <creature>/part_guide.npz;
    the key covers J, the plan, the knobs, the sheet and carve.py itself."""
    if J is None:
        J, plan = B.cage_plan(k.meta)
    else:
        J, plan = B.cage_plan(dict(J=J, plan=plan))
    cdir = k.dir
    rdir = os.path.join(cdir, 'reference')
    params = dict(v=VERSION, part=1, tris=tris, voxel_div=voxel_div, smooth=smooth, knobs=dict(PART, **knobs),
                  J={n: [round(float(x), 5) for x in p] for n, p in J.items()},
                  plan={a: plan[a] for a in ('spine', 'limbs', 'extra', 'neck', 'head')})
    h = hashlib.sha256(json.dumps(params, sort_keys=True, default=str).encode())
    for f in (os.path.join(rdir, 'refs.json'), os.path.join(rdir, 'sheet.png'), os.path.abspath(__file__)):
        h.update(open(f, 'rb').read())                                  # the sheet, and this file: a code change rebuilds the guide
    key = h.hexdigest()
    cpath = cache or os.path.join(cdir, 'part_guide.npz')
    V = F = parts = None
    if os.path.exists(cpath):
        z = np.load(cpath)
        if str(z['key']) == key:
            V, F, parts = z['verts'], z['faces'], json.loads(str(z['parts']))
    if V is None:
        parts = _jsonable(build_parts(load_ref(cdir), J, plan, **knobs))
        vs = parts['H'] / voxel_div
        ext = np.array([np.abs(np.asarray(s['centre'])) + max(s['width'], s['depth']) for P in parts.values()
                        if isinstance(P, dict) and 'stations' in P for s in P['stations']])
        G = ((np.arange(int(ext[:, 0].max() / vs) + 4) + 0.5) * vs,
             np.arange(-ext[:, 1].max() - 3 * vs, ext[:, 1].max() + 3 * vs, vs),
             np.arange(-2.5 * vs, ext[:, 2].max() + 3 * vs, vs))
        D = parts_field(parts, G)
        org = np.array([-G[0][-1], G[1][0], G[2][0]])
        verts, quads = surface_nets(-np.concatenate([D[::-1], D]), org, vs, iso=0.0)
        me = bpy.data.meshes.new('_part_nets')
        me.from_pydata(verts.tolist(), [], quads.tolist())
        me.update()
        ob = B.link(bpy.data.objects.new('_part_nets', me))
        md = ob.modifiers.new('rm', 'REMESH')
        md.mode, md.voxel_size, md.adaptivity = 'VOXEL', vs * 0.6, 0.0
        _apply(ob, md)
        bm = B.edit(ob)
        _largest_shell(bm)
        for _ in range(smooth):
            bmesh.ops.smooth_vert(bm, verts=list(bm.verts), factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
        B.commit(ob, bm)
        bm.free()
        n0 = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        md = ob.modifiers.new('dec', 'DECIMATE')
        md.decimate_type, md.ratio, md.use_collapse_triangulate = 'COLLAPSE', min(1.0, tris / max(1, n0)), True
        _apply(ob, md)
        V = np.array([v.co[:] for v in ob.data.vertices], np.float32)
        V[:, 2] -= V[:, 2].min()
        F = np.array([p.vertices[:] for p in ob.data.polygons], np.int32)
        _drop(ob)
        np.savez_compressed(cpath, key=key, verts=V, faces=F, parts=json.dumps(parts))
        B.say(f'part_guide: voxel {vs:.4f} m, {n0} -> {len(F)} triangles, parts ' + ', '.join(
            f"{n} {len(P['stations'])}" for n, P in parts.items() if isinstance(P, dict) and 'stations' in P))
    me = bpy.data.meshes.new(name)
    me.from_pydata(V.tolist(), [], F.tolist())
    me.update()
    ob = B.link(bpy.data.objects.new(name, me))
    ob.hide_render = True
    ob.display_type = 'WIRE'
    k.guide, k.guide_parts = ob, parts
    return ob


def _arc(S):
    """Metres along a part's stations (by their bone points)."""
    P = np.array([np.asarray(x['at'], float) for x in S])
    return np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])


def part_budget(guide_parts, part):
    """The ring budget of a part, after the low-poly study (research/video_abbitt_*.md): few sides, and rings only
    where the form or the bend needs them. -> dict(sides, t, kind):
      sides  the ring's side count (PART['sides']: limbs, feet and tails 6, a nose and an ear 4, torso / neck / head 8)
      t      where the rings go, as part_rings' t (it can pass 0 and 1: a part runs on past its end joints)
      kind   per ring: 'end' (the part's two ends), 'joint' (2 rings at each inner joint of a limb, 0.3 x the limb's
             size either side of it; 1 on a trunk joint), 'mass' (ONE per bone, where the profile leaves the straight
             line between the bone's ends the most: the swell of a forearm, a calf, a belly; 3 on a biped's head)."""
    P = guide_parts[part]
    S = P['stations']
    kind = P.get('kind', 'limb')
    s = np.array([x['s'] for x in S]); L = _arc(S)
    size = np.sqrt(np.array([x['width'] * x['depth'] for x in S]))
    bend = kind in ('limb', 'extra')
    rings = [(float(s[0]), 'end'), (float(s[-1]), 'end')]
    cuts = [0]
    for i, x in enumerate(S):
        if x.get('joint') and 0 < i < len(S) - 1 and x['joint'] not in (P['joints'][0], P['joints'][-1]):
            cuts.append(i)
            if bend:
                rings += [(float(np.interp(L[i] + sg * 0.3 * size[i], L, s)), 'joint') for sg in (-1, 1)]
            else:
                rings.append((float(s[i]), 'joint'))
    cuts.append(len(S) - 1)

    def swell(a, b, n):                                                  # the station(s) furthest off the a-b line
        if b - a < 2 or n < 1:
            return []
        dev = np.abs(size[a:b + 1] - np.interp(L[a:b + 1], [L[a], L[b]], [size[a], size[b]]))
        m = a + int(np.argmax(dev))
        if dev.max() < 0.03 * size[a:b + 1].max() or m in (a, b):
            m = a + int(np.argmin(np.abs(L[a:b + 1] - (L[a] + L[b]) / 2)))
        return [m] + swell(a, m, n // 2) + swell(m, b, (n - 1) // 2)
    for a, b in zip(cuts, cuts[1:]):
        rings += [(float(s[m]), 'mass') for m in swell(a, b, 3 if kind == 'head' and len(cuts) == 2 else 1)]
    rings.sort()
    keep = [rings[0]]
    for t, k_ in rings[1:]:                                             # two rings closer than 0.12 x the size are one
        near = np.interp(t, s, L) - np.interp(keep[-1][0], s, L) < 0.12 * float(np.interp(t, s, size))
        if near and k_ != 'end':
            continue
        if near and keep[-1][1] != 'end':
            keep.pop()
        keep.append((t, k_))
    sides = guide_parts.get('sides', PART['sides'])
    return dict(sides=sides.get(kind, 8), t=[round(t, 3) for t, _ in keep], kind=[k_ for _, k_ in keep])


def _super_r(th, a, b, p):
    """Radius of the superellipse (half axes a along u, b along w, exponent p) at the angle th from +u."""
    c, s = abs(math.cos(th)), abs(math.sin(th))
    return 1.0 / max(1e-12, (c / max(a, 1e-6)) ** p + (s / max(b, 1e-6)) ** p) ** (1.0 / p)


def section_radii(guide, centre, u, w, angles=8, r0=None, lim=(0.5, 1.6)):
    """Ray radii of the guide's section in the plane (u, w) through `centre`: the distance from the centre to the
    guide along each direction u cos(a) + w sin(a). angles: a count (evenly round, from +u) or a list of radians.
    r0: the expected radius per angle (a function of the angle, or a list): a ray that leaves the part (into the
    torso, down a leg) is held within lim x r0, and a ray that hits nothing returns r0. An off-axis mass (a calf to
    the back, a thigh to the front) comes out as unequal radii: a ring built on them is not a symmetric tube."""
    tree = _tree(guide)
    c, u, w = Vector(centre), Vector(u), Vector(w)
    ths = [2 * math.pi * i / angles for i in range(angles)] if isinstance(angles, int) else list(angles)
    out = []
    for i, th in enumerate(ths):
        d = (u * math.cos(th) + w * math.sin(th)).normalized()
        e = r0(th) if callable(r0) else (r0[i] if r0 is not None else None)
        hit = tree.ray_cast(c, d)
        r = hit[3] if hit[0] is not None else (e or 0.0)
        if e:
            r = min(max(r, lim[0] * e), lim[1] * e)
        out.append(float(r))
    return out


def section_corners(guide, r, n, half=False, fracs=None, pins=None, dense=96, lim=(0.5, 1.6), snap=0.4):
    """The corner rule: the vertices of an n-sided cage ring on the CORNERS of the guide's section at the ring r
    (a part_rings entry, or any dict with centre, u, w, width, depth, p). The section is read by `dense` rays from
    the centre (section_radii, held within lim x the part's own superellipse), simplified as a polyline to n
    vertices (the least-area vertex goes first), and each ring slot takes the corner that falls within snap x a
    slot of it; a slot with no corner takes the section's own point there, so the lengthwise lines stay straight.
      half=False  a closed ring: n points counter-clockwise from +u, slot i at the angle 2 pi i / n
      half=True   a midline part (u = world X, centre on x = 0): n + 1 points from the top seam (+w) round the +X
                  side to the bottom seam, slot i at the arc fraction fracs[i] (default i / n)
      pins        half only, {slot: ('z', value) | ('x', value)}: the slot sits where the section first drops to that
                  height (from the top) / first reaches that half width (from the bottom); the slots between pins
                  are spread evenly, and pinned slots are not snapped
    -> dict(points [Vector], corner [bool per point], corners [Vector: every simplification vertex], fracs)"""
    c, u, w = Vector(r['centre']), Vector(r['u']), Vector(r['w'])
    a, b, p = r['width'] / 2, r['depth'] / 2, max(r.get('p', 2.0), 1.0)
    ths = [math.pi / 2 - math.pi * i / dense for i in range(dense + 1)] if half else [2 * math.pi * i / dense for i in range(dense)]
    rad = section_radii(guide, c, u, w, ths, lambda t: _super_r(t, a, b, p), lim)
    P = np.array([(q * math.cos(t), q * math.sin(t)) for q, t in zip(rad, ths)])
    if half:
        P[0, 0] = P[-1, 0] = 0.0
    m = n + 1 if half else n
    keep = list(range(len(P)))
    tri = lambda i, j, k_: abs((P[j, 0] - P[i, 0]) * (P[k_, 1] - P[i, 1]) - (P[k_, 0] - P[i, 0]) * (P[j, 1] - P[i, 1]))
    while len(keep) > m:
        js = range(1, len(keep) - 1) if half else range(len(keep))
        j = min(js, key=lambda j: tri(keep[j - 1], keep[j], keep[(j + 1) % len(keep)]))
        keep.pop(j)
    xyz = lambda q: c + u * float(q[0]) + w * float(q[1])
    pts, isc = [None] * m, [False] * m
    if half:
        L = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
        L /= L[-1]
        at = lambda f: np.array([np.interp(f, L, P[:, 0]), np.interp(f, L, P[:, 1])])
        fr = list(fracs) if fracs is not None else [i / n for i in range(m)]
        fixed = {0, n}
        for sl, (ax, val) in (pins or {}).items():
            X3 = [xyz(q) for q in P]
            if ax == 'z':
                j = next((i for i, q in enumerate(X3) if q.z <= val), len(P) - 1)
            else:
                j = next((i for i in range(len(P) - 1, -1, -1) if X3[i].x >= val), 0)
            fr[sl] = float(L[j]); fixed.add(sl)
        if pins:
            fx = sorted(fixed)
            for s0, s1 in zip(fx, fx[1:]):
                for i in range(s0 + 1, s1):
                    fr[i] = fr[s0] + (fr[s1] - fr[s0]) * (i - s0) / (s1 - s0)
        best = {}
        for kj in keep[1:-1]:
            s = min(range(1, n), key=lambda i: abs(fr[i] - L[kj]))
            dev = abs(fr[s] - L[kj]) / max(1e-9, (fr[s + 1] - fr[s - 1]) / 2)
            if s not in fixed and dev <= snap and (s not in best or dev < best[s][0]):
                best[s] = (dev, kj)
        for i in range(m):
            if i in best:
                pts[i], isc[i] = xyz(P[best[i][1]]), True
            else:
                pts[i] = xyz(at(fr[i]))
        pts[0].x = pts[-1].x = 0.0
    else:
        fr = None
        best = {}
        for kj in keep:
            s = int(round(kj * n / dense)) % n
            dev = abs(((kj * n / dense) - s + n / 2) % n - n / 2)
            if dev <= snap and (s not in best or dev < best[s][0]):
                best[s] = (dev, kj)
        for i in range(n):
            pts[i] = xyz(P[best[i][1]] if i in best else P[(i * dense) // n])
            isc[i] = i in best
    return dict(points=pts, corner=isc, corners=[xyz(P[j]) for j in keep], fracs=fr)


def ring_points(r, sides=None, front=None, guide=None):
    """With guide: the ring's vertices on the corners of the guide's own section there (section_corners), so an
    asymmetric section stays asymmetric. Without: the superellipse ring below.
    The cage ring of one part_rings entry: `sides` points round its section, counter-clockwise from +u. A
    6-sided limb ring is a rounded box with FLAT front and back: two points on the front (+w) edge and two on the
    back, `front` x the width apart (PART['limb_front']), and one at each side; any other count puts the points on
    the section's superellipse (exponent r['p']), an edge (not a point) across the front and the back when the
    count is a multiple of 4."""
    n = sides or r.get('sides', 8)
    if guide is not None:
        return [tuple(round(float(q), 4) for q in v) for v in section_corners(guide, r, n)['points']]
    a, b, p = r['width'] / 2, r['depth'] / 2, max(r.get('p', 2.0), 1.0)
    ce, u, w = (np.asarray(r[k_], float) for k_ in ('centre', 'u', 'w'))
    if n == 6 and r.get('flat', False):
        f = r.get('front', 0.5) if front is None else front
        xy = [(a, 0.0), (f * a, b), (-f * a, b), (-a, 0.0), (-f * a, -b), (f * a, -b)]
    else:
        th = [2 * math.pi * (i + (0.5 if n % 4 == 0 else 0.0)) / n for i in range(n)]
        e = lambda c: math.copysign(abs(c) ** (2.0 / p), c)
        xy = [(a * e(math.cos(t)), b * e(math.sin(t))) for t in th]
        if n % 4 == 0:                                                  # the front / back edges and the flanks lie on the outline
            mx, my = max(abs(x) for x, _ in xy), max(abs(y) for _, y in xy)
            xy = [(x * a / mx, y * b / my) for x, y in xy]
    return [tuple(round(float(q), 4) for q in ce + u * x + w * y) for x, y in xy]


def part_rings(guide_parts, part, n=None, ends=False, label=None):
    """n stations of a part straight from its definition (never a cut of the mesh): t (0 = the chain's first
    joint, 1 = its last), centre, width (along u), depth (along w), u, w, p (the section's superellipse exponent:
    2 an ellipse, more = boxier), src (where each dimension came from: a view name, 'aspect', 'prior').
    part: 'torso', 'neck', 'head' (the head -> snout chain), a limb name of plan['limbs'], 'extra0'...
    ends=True runs over the part's whole extent (past its end joints, to the nose or the toe tips).
    Each ring also carries sides (the suggested side count), kind ('end' / 'joint' / 'mass' when n is None) and
    flat (a limb ring: flat front and back); ring_points(ring) gives its cage vertices.
    n=None: the rings of part_budget(guide_parts, part) (one mass ring per bone, 2 at each limb joint, the ends),
    over the part's whole extent. Parts: 'torso', 'neck', 'head' (quadruped: the head -> snout chain, t 0 = the
    head joint; upright biped: the level stack, t 0 = the chin, 1 = the crown), 'nose' (biped), a limb (its chain
    runs on through the foot: the last bone's rings are the foot wedge's), '<limb>_foot' (t 0 = heel, 1 = toe tip)."""
    P = guide_parts[part]
    S = P['stations']
    s = np.array([x['s'] for x in S])
    lo, hi = (s[0], s[-1]) if ends else (max(0.0, s[0]), min(1.0, s[-1]))
    bud = part_budget(guide_parts, part)
    ts = bud['t'] if n is None else [lo + (hi - lo) * (i / (n - 1) if n > 1 else 0.5) for i in range(n)]
    flat = P.get('kind', 'limb') in ('limb', 'foot')
    out = []
    for i, t in enumerate(ts):
        j = int(np.clip(np.searchsorted(s, t) - 1, 0, len(S) - 2))
        f = float(np.clip((t - s[j]) / max(1e-9, s[j + 1] - s[j]), 0, 1))
        a, b = S[j], S[j + 1]
        mix = lambda key: tuple(round(float(x), 4) for x in (1 - f) * np.asarray(a[key], float) + f * np.asarray(b[key], float))
        g = a if f < 0.5 else b
        out.append(dict(t=round(float(t), 3), centre=mix('centre'), width=round((1 - f) * a['width'] + f * b['width'], 4),
                        depth=round((1 - f) * a['depth'] + f * b['depth'], 4), u=tuple(g['u']), w=tuple(g['w']),
                        p=round((1 - f) * a.get('p', 2.0) + f * b.get('p', 2.0), 2), src=dict(g.get('src', {})),
                        sides=bud['sides'], flat=flat, front=guide_parts.get('limb_front', PART['limb_front'])))
        if n is None:
            out[-1]['kind'] = bud['kind'][i]
    if label:
        B.say(f'rings {label}:')
        for r in out:
            B.say("  t %.2f  centre (%+.3f, %+.3f, %+.3f)  width %.3f  depth %.3f  p %.2f  sides %d %s %s"
                  % (r['t'], *r['centre'], r['width'], r['depth'], r['p'], r['sides'], r.get('kind', ''), r['src']))
    return out
