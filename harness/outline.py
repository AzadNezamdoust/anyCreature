#!/usr/bin/env python3
"""Silhouettes straight from the geometry — no browser, no renderer, no images to read.

    python3 harness/outline.py <model.glb> <outdir> [--prev <dir>] [--views orbit]
                               [--hero hero.png] [--no-colour]

    --views   orbit (default: az000 … az315 every 45°, top, bottom), legacy
              (front, side, top, hero), azimuths, or any comma list of names
    writes    per view: mask_<v>.npy, sil_<v>.png, sil_<v>_thumb24/48.png and a
              colour render col_<v>.png; with the full orbit, orbit_sheet.png and
              orbit_sil_sheet.png; and metrics.json (views, facing, orbit)

WHY. The silhouette is the single most-used measurement in this harness, and
until now getting one meant launching a headless Chromium, loading three.js,
uploading the mesh to a GPU, drawing it black-on-white, and reading the pixels
back. That is a lot of machinery to answer a question the vertices already
contain: this is low-poly, a few thousand triangles, and the outline of a solid
under a known camera is arithmetic.

So this projects the triangles and fills them. Same camera the renderer used
(perspective, 30 degrees, distance = longest dimension x 2.4, 640x640, same view
directions and up vectors), same mask convention, same metrics. The point is not
only speed — it is that the numbers stop being *estimates read off a picture*
and become the thing itself.

WHAT THIS DOES NOT REPLACE. It cannot tell you WHAT the shape looks like. "Is
this a bison" is a judgment about resemblance and it needs eyes; that is the
blind reader's job and no amount of coordinate data does it. What this removes
is everything AROUND that question — aspect, protrusions, thinnest feature,
round-to-round similarity — so the reader can be handed one picture and one
question instead of thirteen pictures and a questionnaire.
"""
import sys, os, json, struct, math, time

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print('BLOCK: outline.py needs numpy and pillow — run setup.sh')
    sys.exit(2)

RES = 640
FOV = 30.0


# ── GLB ────────────────────────────────────────────────────────────────────
def read_glb(path):
    b = open(path, 'rb').read()
    if b[:4] != b'glTF':
        raise ValueError('not a GLB')
    jlen, = struct.unpack('<I', b[12:16])
    g = json.loads(b[20:20 + jlen])
    bin_off = 20 + jlen + 8
    return g, b, bin_off


def accessor(g, b, base, idx):
    a = g['accessors'][idx]
    bv = g['bufferViews'][a['bufferView']]
    off = base + bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    ct = a['componentType']
    fmt, size = {5126: ('f', 4), 5125: ('I', 4), 5123: ('H', 2), 5121: ('B', 1)}[ct]
    stride = bv.get('byteStride') or size * n
    if stride == size * n:
        # Tightly packed (every file this engine writes): one read, not one
        # struct.unpack per element. Same values, same dtypes as the loop below.
        dt = np.dtype('<' + fmt)
        raw = np.frombuffer(b, dtype=dt, count=a['count'] * n, offset=off)
        return raw.reshape(a['count'], n).astype(np.float64 if ct == 5126 else np.int64)
    out = np.empty((a['count'], n), dtype=np.float64 if ct == 5126 else np.int64)
    for i in range(a['count']):
        out[i] = struct.unpack_from('<' + fmt * n, b, off + i * stride)
    return out


def triangles_by_material(path, want_colour=False):
    """Triangles grouped by material name, so a share can be attributed.

    With want_colour, also returns the baked (shipped) colour: per-vertex COLOR_0
    and the per-material baseColorFactor. COLOUR = baseColorFactor x COLOR_0,
    ALWAYS BOTH — the engine splits the baked colour, the hue into
    baseColorFactor and the per-vertex ratio (<=1) into COLOR_0, so reading
    either alone measures half a colour. Both are linear; the sRGB encode
    happens at measurement time. This is the colour AFTER the shading stack;
    the palette before it is albedo_of()."""
    g, b, base = read_glb(path)
    mats = [m.get('name', f'mat{i}') for i, m in enumerate(g.get('materials', []))]
    basecol = np.array([(m.get('pbrMetallicRoughness', {}) or {}).get('baseColorFactor', [1, 1, 1, 1])[:3]
                        for m in g.get('materials', [])], dtype=np.float64) if g.get('materials') else np.zeros((0, 3))
    V, F, MID, C, N = [], [], [], [], []
    for mesh in g.get('meshes', []):
        for pr in mesh.get('primitives', []):
            at = pr.get('attributes', {})
            if 'POSITION' not in at:
                continue
            off = sum(len(x) for x in V)
            pos = accessor(g, b, base, at['POSITION'])
            V.append(pos)
            if want_colour:
                N.append(accessor(g, b, base, at['NORMAL']).astype(np.float64)
                         if 'NORMAL' in at else np.zeros((len(pos), 3)))
                if 'COLOR_0' in at:
                    c = accessor(g, b, base, at['COLOR_0'])[:, :3].astype(np.float64)
                    a0 = g['accessors'][at['COLOR_0']]
                    if a0['componentType'] == 5123:      # normalised ushort
                        c = c / 65535.0
                    elif a0['componentType'] == 5121:    # normalised ubyte
                        c = c / 255.0
                else:
                    c = np.ones((len(pos), 3))
                C.append(c)
            if 'indices' in pr:
                f = accessor(g, b, base, pr['indices']).reshape(-1, 3) + off
            else:
                n = len(pos) - len(pos) % 3
                f = np.arange(n).reshape(-1, 3) + off
            F.append(f)
            mi = pr.get('material', -1)
            MID.append(np.full(len(f), mi, dtype=np.int64))
    if not V:
        raise ValueError('no geometry in the file')
    if want_colour:
        return np.vstack(V), np.vstack(F), np.concatenate(MID), mats, np.vstack(C), basecol, np.vstack(N)
    return np.vstack(V), np.vstack(F), np.concatenate(MID), mats


def albedo_of(path, V):
    """The PALETTE per vertex, or None: what the designer chose, before light.

    The engine ships it in asset.extras.albedo — 8-bit sRGB triplets, base64,
    one run per part_spans row, counts[k] long. It is the colour after the seam
    blend, the pattern and the hardware bleed, and BEFORE the ramp, the top
    boost and the shadows. counts[k] is the row's vertex count BEFORE the
    crease split that writeGLB does on the way out: the split appends copies
    after a mesh's own vertices, so the row's first counts[k] shipped vertices
    are the recorded ones, in order, and every later one is placed by its
    position (a split copy sits exactly on its original).

    Returned LINEAR and indexed like the vertex array triangles_by_material
    stacks, so it rasterises exactly like COLOR_0. Anything missing or
    inconsistent returns None and the caller falls back to the shipped colour —
    a washed or foreign file has no palette record, and a partial one is worse
    than none."""
    import base64
    try:
        g, _b, _base = read_glb(path)
        x = (g.get('asset', {}) or {}).get('extras', {}) or {}
        rec, spans = x.get('albedo'), x.get('part_spans')
        if not isinstance(rec, dict) or rec.get('encoding') != 'srgb8' or not spans:
            return None
        counts = rec.get('counts') or []
        meshes = g.get('meshes', [])
        if len(meshes) != 1 or len(counts) != len(spans):
            return None
        offs, o = [], 0
        for pr in meshes[0].get('primitives', []):
            offs.append(o)
            o += g['accessors'][pr['attributes']['POSITION']]['count']
        if o != len(V):
            return None
        raw = np.frombuffer(base64.b64decode(rec['data']), dtype=np.uint8)
        if raw.size != 3 * sum(int(n) for n in counts):
            return None
        srgb = raw.reshape(-1, 3).astype(np.float64) / 255.0
        lin = np.where(srgb <= 0.04045, srgb / 12.92, np.power((srgb + 0.055) / 1.055, 2.4))
        out = np.full((len(V), 3), np.nan)
        k = 0
        for s, n0 in zip(spans, counts):
            n, at = int(s['count']), offs[int(s['primitive'])] + int(s['first'])
            n0 = int(n0)
            if n0 > n:
                return None
            out[at:at + n0] = lin[k:k + n0]
            if n > n0:
                own = {tuple(V[at + i]): at + i for i in range(n0)}
                for j in range(at + n0, at + n):
                    src = own.get(tuple(V[j]))
                    if src is None:
                        return None
                    out[j] = out[src]
            k += n0
        return None if np.isnan(out).any() else out
    except Exception:
        return None


def structure(path):
    """What the file IS, from the JSON chunk: clips, skins, triangle count.

    This used to come from loading the model into three.js inside a headless
    browser and traversing the scene graph. It is written in the glTF header."""
    g, b, base = read_glb(path)
    tris = 0
    skinned = 0
    for mesh in g.get('meshes', []):
        for pr in mesh.get('primitives', []):
            at = pr.get('attributes', {})
            if 'indices' in pr:
                tris += g['accessors'][pr['indices']]['count'] // 3
            elif 'POSITION' in at:
                tris += g['accessors'][at['POSITION']]['count'] // 3
    for nd in g.get('nodes', []):
        if 'skin' in nd and 'mesh' in nd:
            skinned += 1
    return {'triangles': int(tris), 'skinnedMeshes': int(skinned),
            'animations': [a.get('name', f'anim{i}') for i, a in enumerate(g.get('animations', []))]}


def part_boxes(V, F, MID, mats):
    """Per-material bounding box, from the vertices its own triangles reference.

    Measure only the referenced vertices: glTF primitives routinely share one
    POSITION accessor, so scanning the attribute gives every material the bbox
    of the whole body."""
    whole = [float(V[:, k].max() - V[:, k].min()) for k in range(3)]
    dxz = lambda s: math.hypot(s[0], s[2])
    out = {}
    for mi in np.unique(MID):
        if mi < 0:
            continue
        idx = np.unique(F[MID == mi].reshape(-1))
        sub_v = V[idx]
        s = [float(sub_v[:, k].max() - sub_v[:, k].min()) for k in range(3)]
        name = mats[mi] if 0 <= mi < len(mats) else f'mat{mi}'
        out[name] = {'size': [round(x, 4) for x in s],
                     'span_ratio': round(dxz(s) / (dxz(whole) or 1), 4),
                     'height_ratio': round(s[1] / (whole[1] or 1), 4)}
    return out, [round(x, 4) for x in whole]


def triangles(path):
    """Every triangle in the file, as world-space vertex positions.

    Bind pose only, which is what a silhouette gate looks at: this engine writes
    inverse bind matrices that are pure translations of the joint's world
    position, so the stored POSITION values are already world-space at rest."""
    g, b, base = read_glb(path)
    V, F = [], []
    for mesh in g.get('meshes', []):
        for pr in mesh.get('primitives', []):
            at = pr.get('attributes', {})
            if 'POSITION' not in at:
                continue
            off = sum(len(x) for x in V)
            pos = accessor(g, b, base, at['POSITION'])
            V.append(pos)
            if 'indices' in pr:
                ix = accessor(g, b, base, pr['indices']).reshape(-1)
                F.append(ix.reshape(-1, 3) + off)
            else:
                n = len(pos) - len(pos) % 3
                F.append(np.arange(n).reshape(-1, 3) + off)
    if not V:
        raise ValueError('no geometry in the file')
    return np.vstack(V), np.vstack(F)


# ── the head, and which way it faces ───────────────────────────────────────
# The owner's complaint that started the orbit was "the head is not ok", and
# nothing measured a head: part shares are per MATERIAL, and a head is several
# materials (skull, jaw, eyes, ears, beak, tusks). What does know where the head
# is: the SKIN. Every vertex is bound to joints, and the joints carry the
# spec's names. So the head is every vertex whose strongest joint is the head
# joint or hangs below it — eyes, ears, jaw and beak included, whatever they
# are called, and the neck excluded, because a neck is not a head.
HEAD_NAMES = ('head', 'skull', 'cranium')


def _node_tree(g):
    names = [n.get('name', '') for n in g.get('nodes', [])]
    parent = {}
    for i, nd in enumerate(g.get('nodes', [])):
        for ch in nd.get('children', []):
            parent[ch] = i
    return names, parent


def _depth(i, parent):
    d = 0
    while i in parent:
        i, d = parent[i], d + 1
    return d


def head_root(g):
    """(node index, how it was found) of the head joint, or (None, reason).

    First the spec's own words: a chain the spec NAMES head (or skull) — its
    first joint called Head*/Skull*, else its first joint that exists in the
    file. Then any joint in the file called Head*/Skull*, the one nearest the
    root. The chain's joints are looked up by name in the glTF nodes; the
    engine keeps spec names for the head (it renames limb joints, not heads)."""
    names, parent = _node_tree(g)
    idx = {n: i for i, n in enumerate(names)}
    x = (g.get('asset', {}) or {}).get('extras', {}) or {}
    spec = x.get('source_spec') if isinstance(x.get('source_spec'), dict) else {}
    chains = (spec or {}).get('chains') or {}
    if isinstance(chains, dict):
        for cname in sorted(chains, key=lambda c: (c.lower() not in ('head', 'skull'), c)):
            if not any(k in cname.lower() for k in HEAD_NAMES):
                continue
            joints = [j for j in (chains[cname] or []) if isinstance(j, str)]
            named = [j for j in joints if j.lower().startswith(HEAD_NAMES) and j in idx]
            present = [j for j in joints if j in idx]
            if named:
                return idx[named[0]], f'spec chain "{cname}", joint {named[0]}'
            if present:
                return idx[present[0]], f'spec chain "{cname}", joint {present[0]}'
    cands = [i for i, n in enumerate(names) if n.lower().startswith(HEAD_NAMES)]
    if cands:
        i = min(cands, key=lambda k: (_depth(k, parent), k))
        return i, f'joint {names[i]}'
    return None, 'no chain or joint named head/skull'


def head_vertices(path, nverts):
    """Bool per vertex (stacked like triangles_by_material) — the head — plus a
    note saying how it was found; (None, why) when the file cannot say."""
    try:
        g, b, base = read_glb(path)
    except Exception as e:
        return None, str(e)
    root, how = head_root(g)
    if root is None:
        return None, how
    names, parent = _node_tree(g)
    under = set()
    for i in range(len(names)):
        j = i
        while True:
            if j == root:
                under.add(i)
                break
            if j not in parent:
                break
            j = parent[j]
    skin_of = {nd['mesh']: nd['skin'] for nd in g.get('nodes', [])
               if 'mesh' in nd and 'skin' in nd}
    out = []
    for mi, mesh in enumerate(g.get('meshes', [])):
        sk = skin_of.get(mi)
        jl = g['skins'][sk]['joints'] if sk is not None and g.get('skins') else None
        for pr in mesh.get('primitives', []):
            at = pr.get('attributes', {})
            if 'POSITION' not in at:
                continue
            n = g['accessors'][at['POSITION']]['count']
            if jl is None or 'JOINTS_0' not in at or 'WEIGHTS_0' not in at:
                out.append(np.zeros(n, dtype=bool))
                continue
            J = accessor(g, b, base, at['JOINTS_0'])
            W = accessor(g, b, base, at['WEIGHTS_0'])
            top = J[np.arange(n), np.argmax(W, axis=1)]
            node = np.array([jl[int(k)] if 0 <= int(k) < len(jl) else -1 for k in top])
            out.append(np.isin(node, list(under)))
    if not out:
        return None, 'no skinned geometry'
    h = np.concatenate(out)
    if len(h) != nverts or not h.any():
        return None, f'{how}: no vertex is bound to it'
    return h, how


def facing_of(V, head):
    """Which way the creature faces — a horizontal unit vector, and why.

    NOT the longest bounding-box axis: that is how the legacy views were picked
    and it is wrong for anything wider than it is long (an upright giant with
    its arms out, a wyvern with its wings spread). The head says where the
    front is: the horizontal direction from the body's centre to the head's,
    snapped to the nearest world axis, because the engine builds along axes and
    a head turned 30 degrees in a pose has not turned the body. With no head in
    the file, +Z, the engine's own convention (SYNTAX: "z forward")."""
    if head is None or not head.any():
        return np.array([0., 0., 1.]), 'engine convention (+Z) — no head found'
    lo, hi = V.min(axis=0), V.max(axis=0)
    centre = (lo + hi) / 2
    d = V[head].mean(axis=0) - centre
    d[1] = 0.0
    span = float(max(hi[0] - lo[0], hi[2] - lo[2]) or 1.0)
    if float(np.linalg.norm(d)) < 0.05 * span:
        return np.array([0., 0., 1.]), ('engine convention (+Z) — the head sits over '
                                        'the centre and says nothing about facing')
    k = int(np.argmax(np.abs([d[0], d[2]])))
    f = np.zeros(3)
    f[0 if k == 0 else 2] = math.copysign(1.0, d[0 if k == 0 else 2])
    ang = math.degrees(math.atan2(abs(d[2 if k == 0 else 0]), abs(d[0 if k == 0 else 2])))
    lab = ('+' if f.sum() > 0 else '-') + ('X' if k == 0 else 'Z')
    return f, f'head ({lab}, head off-axis {ang:.0f}°)'


# ── camera, matching the renderer this replaced, exactly ───────────────────
#
# THE ORBIT. Four views left the in-between angles and the head unmeasured, and
# that is exactly where creatures went wrong: a wolf that reads from the side
# and the front can still collapse into a lump at 45 degrees, and nothing ever
# looked. So the default set is a CYLINDER around the creature — eight
# horizontal azimuths at 45-degree steps, az000 on the creature's face — plus
# the two poles, top and bottom. Same pinhole, same distance rule, same 640
# grid as the four legacy views, so every number means what it meant.
#
#   az000   the camera in front of the creature, looking at its face
#   az090   the creature's LEFT flank (the +X side, where the L chains live,
#           when it faces +Z — the engine's convention)
#   az180   behind it
#   az270   its right flank
#   top     looking down, the creature's front at the top of the image
#   bottom  looking up at the belly, front at the top of the image
#
# The legacy names keep their legacy definitions EXACTLY, so every claim and
# every calibration that names them still reads the same pixels: `side` is the
# LONG profile and `front` the other horizontal axis (picked by the bounding
# box, which is not always where the face is — an upright giant with its arms
# out is wider than it is deep, so its legacy `side` looks at its chest), and
# `hero` is the raised three-quarter shot. Only `top` changed: it used to put
# the long axis at the top of the image and now puts the FACE there, which is
# the same picture for every long-bodied creature.
AZIMUTHS = [f'az{d:03d}' for d in range(0, 360, 45)]
ORBIT = AZIMUTHS + ['top', 'bottom']
LEGACY = ['front', 'side', 'top', 'hero']
VIEW_SETS = {'orbit': ORBIT, 'legacy': LEGACY, 'azimuths': AZIMUTHS}

# Which way the creature faces, as a horizontal unit vector. main() sets it from
# facing_of(); until then +Z, the engine's own convention (SYNTAX: "z forward").
FACING = np.array([0., 0., 1.])


def expand_views(arg):
    """'orbit,hero' -> ['az000', ..., 'bottom', 'hero'], order kept, no repeats."""
    out = []
    for v in arg.split(','):
        v = v.strip()
        for x in VIEW_SETS.get(v, [v] if v else []):
            if x not in out:
                out.append(x)
    return out


def is_azimuth(view):
    return len(view) == 5 and view.startswith('az') and view[2:].isdigit()


def view_dir(view, size):
    long_axis = 'x' if size[0] > size[2] else 'z'
    fwd = np.array([FACING[0], 0., FACING[2]], dtype=np.float64)
    fwd = fwd / (np.linalg.norm(fwd) or 1.0)
    if is_azimuth(view):
        # rotate the facing about +Y: az090 lands on +X for a creature facing +Z
        t = math.radians(int(view[2:]))
        c, s = round(math.cos(t), 12), round(math.sin(t), 12)
        d = np.array([fwd[0] * c + fwd[2] * s, 0., -fwd[0] * s + fwd[2] * c])
        return d, np.array([0., 1., 0.])
    if view == 'top':
        return np.array([0., 1., 0.]), fwd
    if view == 'bottom':
        return np.array([0., -1., 0.]), fwd
    if view == 'hero':
        return np.array([1., 0.5, 1.]), np.array([0., 1., 0.])
    if view == 'side':
        d = [0., 0., 1.] if long_axis == 'x' else [1., 0., 0.]
    elif view == 'front':
        d = [1., 0., 0.] if long_axis == 'x' else [0., 0., 1.]
    else:
        raise ValueError(f'unknown view "{view}" — use az000..az315, top, bottom, '
                         f'front, side, hero, or a set: {", ".join(VIEW_SETS)}')
    return np.array(d), np.array([0., 1., 0.])


def camera(V, view):
    """(eye, right, trueup, fwd) for one view, framed on the model's bounds."""
    lo, hi = V.min(axis=0), V.max(axis=0)
    centre, size = (lo + hi) / 2, hi - lo
    d, up = view_dir(view, size)
    rad = float(size.max())
    # NOT normalised, deliberately. three.js does
    #     cam.position = centre + new Vector3(...dir) * (rad * 2.4)
    # on the raw vector, and the hero direction [1, 0.5, 1] has length 1.5 — so
    # the hero camera really does sit 1.5x further out than the axis views. A
    # pixel-level comparison caught this: front/side/top matched at IoU 0.98+
    # because their directions are already unit, and hero came back at 0.39.
    # The orbit directions are unit too, so every azimuth sits at the same
    # distance and their areas compare directly.
    eye = centre + d * rad * 2.4
    fwd = centre - eye
    fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, up)
    if np.linalg.norm(right) < 1e-9:        # looking straight down the up axis
        right = np.cross(fwd, np.array([0., 0., 1.]))
    right /= np.linalg.norm(right)
    trueup = np.cross(right, fwd)
    return eye, right, trueup, fwd


def render_mask(V, F, view):
    px, py, _z = project(V, view)
    img = Image.new('1', (RES, RES), 0)
    drw = ImageDraw.Draw(img)
    for a, b_, c in F:
        drw.polygon([(px[a], py[a]), (px[b_], py[b_]), (px[c], py[c])], fill=1)
    return np.array(img, dtype=bool)


# ── measures, on the mask ──────────────────────────────────────────────────
def measures(mask):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return {'empty': True}
    w = int(xs.max() - xs.min() + 1)
    h = int(ys.max() - ys.min() + 1)
    area = int(mask.sum())
    m = {
        'W_over_H': round(w / h, 3),
        'fill': round(area / (w * h), 3),
        'px': [w, h],
    }
    # WHERE THE MASS SITS, in thirds of its own bounding box. Same definition as
    # the measure pass it replaced, on the cropped mask, to the decimal.
    #
    # This is the number that tells two DESIGNS apart, which iou_vs_prev does
    # not: iou counts overlapping pixels, so a proportion change moves it a lot
    # while the design stays put. Read off a shipped 13-round build, iou swung
    # 0.476-0.873 while thirds_cols never left [~0.23, ~0.33, ~0.44] — thirteen
    # rounds, one layout, including both rounds the log calls concept restarts.
    crop = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    m['thirds_cols'] = [round(float(crop[:, i * w // 3:(i + 1) * w // 3].sum() / area), 2)
                        for i in range(3)]
    m['thirds_rows'] = [round(float(crop[i * h // 3:(i + 1) * h // 3].sum() / area), 2)
                        for i in range(3)]
    try:
        from scipy import ndimage
    except ImportError:
        # Silence here is dangerous: thinnest_px48 gates legibility and protrusions
        # gates boldness, so a missing dependency would drop two BLOCKING measures and
        # every build would pass them by not having them. Say so, once, loudly.
        print('WARN: scipy missing — protrusions, thinnest_px48, convexity and mirror_sym '
              'are NOT computed, so the legibility and boldness gates have nothing to read. '
              'Run setup.sh.', file=sys.stderr)
        return m
    # Protrusions and thinnest_px48 keep the original definitions EXACTLY —
    # erode hard to get a core, subtract to get appendages, and measure each
    # appendage's own thickness as twice its maximum inscribed radius, scaled to
    # the 48px thumbnail the reader actually sees. Two implementations of the
    # same number must agree or one of them is lying; the first version here
    # took the global minimum of the distance transform instead, which is the
    # one-pixel boundary and therefore always ~1px, on every creature.
    H, W = mask.shape
    it = max(2, int(min(H, W) * 0.06))
    core = ndimage.binary_erosion(mask, iterations=it)
    app = mask & ~ndimage.binary_dilation(core, iterations=it)
    la, na = ndimage.label(app)
    protr = []
    for i in range(1, na + 1):
        blob = la == i
        s = int(blob.sum())
        if s < area * 0.01:
            continue
        dt = ndimage.distance_transform_edt(blob)
        protr.append(round(2 * float(dt.max()) * 48.0 / max(H, W), 1))
    m['protrusions'] = len(protr)
    m['thinnest_px48'] = min(protr) if protr else None
    return m


def project(V, view):
    """World vertices -> screen x, y and camera depth, for one view."""
    eye, right, trueup, fwd = camera(V, view)
    rel = V - eye
    cam = np.stack([rel @ right, rel @ trueup, rel @ fwd], axis=1)
    z = np.maximum(cam[:, 2], 1e-6)
    f = 1.0 / math.tan(math.radians(FOV) / 2)
    px = ((cam[:, 0] / z) * f * 0.5 + 0.5) * RES
    py = (0.5 - (cam[:, 1] / z) * f * 0.5) * RES
    return px, py, z


def _bary(px, py, z, a, b, c, gx, gy):
    """Screen-space barycentrics and perspective-correct depth at (gx, gy).

    Vectorised over any broadcastable shape; the arithmetic is written in the
    same order as the per-triangle loop it replaced, so it returns the same
    floats to the last bit."""
    xa, xb, xc = px[a], px[b], px[c]
    ya, yb, yc = py[a], py[b], py[c]
    det = (yb - yc) * (xa - xc) + (xc - xb) * (ya - yc)
    l0 = ((yb - yc) * (gx - xc) + (xc - xb) * (gy - yc)) / det
    l1 = ((yc - ya) * (gx - xc) + (xa - xc) * (gy - yc)) / det
    l2 = 1.0 - l0 - l1
    iz = l0 / z[a] + l1 / z[b] + l2 / z[c]
    iz = np.where(np.abs(iz) < 1e-12, 1e-12, iz)
    return l0, l1, l2, 1.0 / iz


def zbuffer(px, py, z, F):
    """The winning triangle per pixel (-1 = background), with a depth test.

    This is the rasteriser every measure shares. It used to be a Python loop,
    one numpy call chain per triangle — 1.3s a view, fine for four views and
    not for ten. The same test in batches: triangles are grouped by the size of
    their pixel box, each group's boxes are evaluated at once, and the nearest
    fragment wins, ties going to the EARLIER triangle — exactly what the loop's
    strict `zz < depth` did. Checked pixel-for-pixel against the loop on the
    shipped creatures (owner, colour, normal and albedo buffers identical)."""
    n = len(F)
    best_z = np.full(RES * RES, np.inf)
    best_t = np.full(RES * RES, -1, dtype=np.int64)
    if not n:
        return best_t.reshape(RES, RES)
    a, b, c = F[:, 0], F[:, 1], F[:, 2]
    X = np.stack([px[a], px[b], px[c]], axis=1)
    Y = np.stack([py[a], py[b], py[c]], axis=1)
    x0 = np.maximum(0, np.floor(X.min(axis=1)))
    x1 = np.minimum(RES - 1, np.ceil(X.max(axis=1)))
    y0 = np.maximum(0, np.floor(Y.min(axis=1)))
    y1 = np.minimum(RES - 1, np.ceil(Y.max(axis=1)))
    det = (Y[:, 1] - Y[:, 2]) * (X[:, 0] - X[:, 2]) + (X[:, 2] - X[:, 1]) * (Y[:, 0] - Y[:, 2])
    keep = (x1 >= x0) & (y1 >= y0) & (np.abs(det) >= 1e-12)
    idx = np.nonzero(keep)[0]
    if not len(idx):
        return best_t.reshape(RES, RES)
    x0i, y0i = x0[idx].astype(np.int64), y0[idx].astype(np.int64)
    w = x1[idx].astype(np.int64) - x0i + 1
    h = y1[idx].astype(np.int64) - y0i + 1
    pw = 1 << np.ceil(np.log2(np.maximum(w, 1))).astype(np.int64)
    ph = 1 << np.ceil(np.log2(np.maximum(h, 1))).astype(np.int64)
    key = pw * (RES * 4) + ph
    CELLS = 1 << 22                          # fragments evaluated per batch
    for k in np.unique(key):
        sel = np.nonzero(key == k)[0]
        BW, BH = int(k // (RES * 4)), int(k % (RES * 4))
        step = max(1, CELLS // (BW * BH))
        for s0 in range(0, len(sel), step):
            ss = sel[s0:s0 + step]
            t = idx[ss]
            ax = np.arange(BW)[None, None, :]
            ay = np.arange(BH)[None, :, None]
            gxi = x0i[ss][:, None, None] + ax
            gyi = y0i[ss][:, None, None] + ay
            valid = (ax < w[ss][:, None, None]) & (ay < h[ss][:, None, None])
            ta, tb, tc = (a[t][:, None, None], b[t][:, None, None], c[t][:, None, None])
            l0, l1, l2, zz = _bary(px, py, z, ta, tb, tc, gxi + 0.5, gyi + 0.5)
            inside = valid & (l0 >= 0) & (l1 >= 0) & (l2 >= 0)
            if not inside.any():
                continue
            tt = np.broadcast_to(t[:, None, None], inside.shape)[inside]
            pix = (gyi * RES + gxi)
            pix = np.broadcast_to(pix, inside.shape)[inside]
            zv = zz[inside]
            # nearest first, then the earliest triangle — one winner per pixel
            o = np.lexsort((tt, zv, pix))
            pix, zv, tt = pix[o], zv[o], tt[o]
            first = np.ones(len(pix), dtype=bool)
            first[1:] = pix[1:] != pix[:-1]
            pix, zv, tt = pix[first], zv[first], tt[first]
            cz, ct = best_z[pix], best_t[pix]
            win = (zv < cz) | ((zv == cz) & (ct >= 0) & (tt < ct))
            best_z[pix[win]] = zv[win]
            best_t[pix[win]] = tt[win]
    return best_t.reshape(RES, RES)


def material_shares(V, F, MID, mats, view, C=None, basecol=None, N=None, A=None,
                    want_tri=False):
    """Which material OWNS each silhouette pixel, with a depth test.

    The share of the frame a part holds is a geometry question, and it was being
    answered by a browser: render every material in a distinct colour, read the
    pixels back, count them. That needs a GPU only because of occlusion — a wing
    behind the torso must not be counted — and occlusion is a z-buffer, which is
    thirty lines. So: rasterise every triangle with a depth test, keep the
    winning material per pixel, and count.

    A (per-vertex LINEAR albedo, already a whole colour — no baseColorFactor)
    rides along in the same pass when given, and is returned last.

    With want_tri, the winning TRIANGLE index per pixel (-1 = background) is
    returned after everything else — the head measures attribute pixels by
    triangle, not by material, because a head is several materials."""
    px, py, z = project(V, view)
    win_tri = zbuffer(px, py, z, F)
    body = win_tri >= 0
    owner = np.full((RES, RES), -1, dtype=np.int64)
    owner[body] = MID[win_tri[body]]
    # The colour buffer rides along in the SAME rasteriser. A second pass would be
    # a second definition of "which pixel does this triangle win", and two of those
    # have to be kept in agreement by hand.
    colour = np.zeros((RES, RES, 3)) if C is not None else None
    normal = np.zeros((RES, RES, 3)) if N is not None else None
    albedo = np.zeros((RES, RES, 3)) if A is not None else None
    if body.any() and (C is not None or N is not None or A is not None):
        yy, xx = np.nonzero(body)
        t = win_tri[yy, xx]
        a, b, c = F[t, 0], F[t, 1], F[t, 2]
        l0, l1, l2, zz = _bary(px, py, z, a, b, c, xx + 0.5, yy + 0.5)
        # PERSPECTIVE-CORRECT interpolation, not affine. l0/l1/l2 are barycentric
        # in SCREEN space, and screen space is already divided by depth — so
        # blending a per-vertex quantity with them directly is only right for an
        # orthographic camera. This one is a pinhole at 30 degrees. The textbook
        # correction: blend 1/z, take the reciprocal for depth, and divide any
        # other attribute back out by it.
        w0, w1, w2 = (l0 / z[a])[:, None], (l1 / z[b])[:, None], (l2 / z[c])[:, None]
        zc = zz[:, None]
        if colour is not None:
            cc = (w0 * C[a] + w1 * C[b] + w2 * C[c]) * zc
            if basecol is not None and len(basecol):
                mi = MID[t]
                ok = (mi >= 0) & (mi < len(basecol))
                cc[ok] = cc[ok] * basecol[mi[ok]]
            colour[yy, xx] = cc
        if normal is not None:
            normal[yy, xx] = (w0 * N[a] + w1 * N[b] + w2 * N[c]) * zc
        if albedo is not None:
            albedo[yy, xx] = (w0 * A[a] + w1 * A[b] + w2 * A[c]) * zc
    total = int((owner >= 0).sum())
    out = {}
    if total:
        for mi in np.unique(owner):
            if mi < 0:
                continue
            name = mats[mi] if 0 <= mi < len(mats) else f'mat{mi}'
            out[name] = round(float((owner == mi).sum()) / total, 5)
    ret = (out, owner >= 0)
    if colour is not None:
        ret += (colour,)
    if normal is not None:
        ret += (normal,)
    if albedo is not None:
        ret += (albedo,)
    if want_tri:
        ret += (win_tri,)
    return ret


# The studio rig, as (world direction, colour, amplitude). It was placed for the
# hero camera; every other view gets the SAME rig turned with its camera, so the
# key always falls on the side facing the viewer. A fixed world rig lit the
# back view with the rim alone and it came out a black cut-out — useless for
# the one question the orbit sheet exists to answer.
RIG = (((2.2, 3.6, 3.0), (1.0, 0.96, 0.90), 2.5),    # warm key
       ((-4.0, 1.2, 1.5), (0.80, 0.86, 1.0), 0.7),   # cool fill
       ((-1.5, 2.5, -4.0), (0.85, 0.90, 1.0), 1.4))  # rim


def shade_rgba(V, F, colour, nrm, mask, view, shadow=True):
    """Light the rasterised colour and composite it — RGBA uint8 at RES.

    Studio rig, Lambert only — these are matte low-poly surfaces with the
    specular story already painted into the vertex colour, so a full PBR
    evaluation would be re-deriving what is baked. The old rig summed a 1.5x
    hemisphere and three lamps to ~5.5 and divided by pi: everything sat near
    white and the form flattened out. This one keeps the ambient low so the key
    models the volume, and a cool rim from behind picks the silhouette off the
    background.

    Evaluated on the body's pixels only: off the body the colour buffer is
    zero, so the lit value there is exactly zero anyway."""
    body = np.nonzero(mask)
    nrm_b = nrm[body]
    ln = np.linalg.norm(nrm_b, axis=1, keepdims=True)
    n = np.divide(nrm_b, np.where(ln > 1e-9, ln, 1.0))
    up = n[:, 1:2]
    sky, ground = np.array([0.86, 0.90, 1.0]), np.array([0.46, 0.42, 0.36])
    irr = 0.95 * (sky * (0.5 + 0.5 * up) + ground * (0.5 - 0.5 * up))
    turn = None
    if view != 'hero':
        _e, r1, u1, f1 = camera(V, view)
        _e, r0, u0, f0 = camera(V, 'hero')
        turn = np.stack([r1, u1, f1], axis=1) @ np.stack([r0, u0, f0], axis=0)
    for pos, col, amp in RIG:
        d = np.array(pos, dtype=np.float64); d /= np.linalg.norm(d)
        if turn is not None:
            d = turn @ d
        lam = np.clip((n * d).sum(axis=1, keepdims=True), 0.0, 1.0)
        if amp > 2:                       # the key wraps a little, like a soft box
            lam = np.clip((lam + 0.15) / 1.15, 0.0, 1.0)
        irr = irr + np.array(col) * amp * lam
    # Exposure. This constant touches the PICTURE only — no gate reads it.
    lin = np.clip(colour[body] * irr * (1.4 / np.pi), 0.0, 1.0)
    srgb = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1 / 2.4) - 0.055)
    rgb = np.zeros(mask.shape + (3,))
    rgb[body] = srgb * 255.0
    alpha = np.where(mask, 255.0, 0.0)
    # Contact shadow. A creature floating on transparency reads as a cut-out;
    # the same triangles squashed onto the ground plane, projected through the
    # same camera and blurred, put it on a floor. It is drawn only where the
    # body is not, on the alpha channel, so it costs nothing where the page
    # background is dark.
    if shadow:
        try:
            from scipy import ndimage
            lo = V.min(axis=0)
            Vg = V.copy(); Vg[:, 1] = lo[1]
            # project() frames the camera from the points it is given; the
            # squashed copy shares the model's bounds only when both are passed
            px, py, z = project(np.vstack([V, Vg]), view)
            px, py = px[len(V):], py[len(V):]
            sh = Image.new('L', (RES, RES), 0)
            drw = ImageDraw.Draw(sh)
            # only triangles the camera can see the underside of matter; simpler
            # to draw them all — the union is the footprint either way
            for a, b_, c in F:
                drw.polygon([(px[a], py[a]), (px[b_], py[b_]), (px[c], py[c])], fill=255)
            shd = np.array(sh, dtype=np.float64) / 255.0
            shd = ndimage.gaussian_filter(shd, sigma=RES * 0.02)
            shd = np.clip(shd * 1.2, 0.0, 1.0) * 0.32
            # Note: the model's own pixels stay opaque; the shadow fills in outside.
            alpha = np.maximum(alpha, np.where(mask, 0.0, shd * 255.0))
            rgb = np.where(mask[..., None], rgb, np.array([28.0, 26.0, 30.0]))
        except Exception:
            pass
    return np.dstack([np.clip(rgb, 0, 255), np.clip(alpha, 0, 255)]).astype(np.uint8)


def square_window(mask, margin=1.10):
    """(x0, y0, side) — a square around what is drawn, with a margin."""
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return 0, 0, mask.shape[0]
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    half = max(xs.max() - xs.min(), ys.max() - ys.min()) / 2 * margin
    return int(round(cx - half)), int(round(cy - half)), max(1, int(round(half * 2)))


def frame_down(rgba, res, window=None):
    """Crop RGBA to a square window and box-filter it down to res x res.

    Frame it. The measuring camera fits the whole bounding sphere so that a
    silhouette is comparable between rounds; a picture has no such duty and a
    creature sitting in a third of the frame reads as a small creature. Crop to
    what is drawn (or to the window given — the orbit sheet crops every
    azimuth to ONE window, so the tiles share a scale), keep it square."""
    if window is None:
        window = square_window(rgba[..., 3] > 8) if (rgba[..., 3] > 8).any() else None
    if window is not None:
        x0, y0, side = window
        H, W = rgba.shape[:2]
        pad = np.zeros((side, side, 4), dtype=np.uint8)
        sx0, sy0 = max(0, x0), max(0, y0)
        sx1, sy1 = min(W, x0 + side), min(H, y0 + side)
        if sx1 > sx0 and sy1 > sy0:
            pad[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = rgba[sy0:sy1, sx0:sx1]
        rgba = pad
    # Premultiply before the downsample so transparent pixels never bleed
    # their (undefined) colour into the edge — and stay in FLOAT through
    # it. The first version rounded the premultiplied picture to 8 bits
    # and resized that with a Lanczos kernel: in the soft rim of the
    # contact shadow, where alpha is 5-20, the (28,26,30) shadow colour
    # premultiplied to 1-2 counts per channel, rounded unevenly, and came
    # back from the un-premultiply as a pink-purple ring around the
    # shadow. A box filter over float channels has neither the rounding
    # nor the Lanczos overshoot on the alpha edge.
    f = rgba.astype(np.float32)
    a = f[..., 3] / 255.0
    chans = [f[..., k] * a for k in range(3)] + [a]
    small = [np.array(Image.fromarray(c, 'F').resize((res, res), Image.BOX), dtype=np.float64)
             for c in chans]
    sa = small[3]
    out = np.zeros((res, res, 4), dtype=np.float64)
    for k in range(3):
        out[..., k] = np.where(sa > 1e-6, small[k] / np.maximum(sa, 1e-6), 0.0)
    out[..., 3] = sa * 255.0
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)


def hero_png(model, out_png, view='hero', res=1024):
    """The delivery's hero shot, rasterised — no browser, no renderer, no lights.

    This is the last thing Chromium was kept alive for, and it did not need to be
    alive for it: the whole L1-L8 shading stack is BAKED into COLOR_0 at build
    time, so the flat albedo already carries the gradient, the seams, the ambient
    occlusion and the rim. Rendering it again with three-point studio lighting was
    lighting a photograph. The z-buffer here decides occlusion exactly as it does
    for every other measure, and the background is alpha rather than a grey card.

    Resolution is raised for this one pass because a thumbnail is looked at by a
    person, not measured; every gate keeps reading the 640 grid."""
    global RES
    keep = RES
    # Rasterised at twice the output size and averaged down: the z-buffer has no
    # anti-aliasing of its own, and a 1024 hero with stair-stepped edges looked
    # like a screenshot of a bug, not a picture of a creature.
    SS = 2
    try:
        RES = res * SS
        V, F, MID, mats, C, basecol, Nv = triangles_by_material(model, want_colour=True)
        _, mask, colour, nrm = material_shares(V, F, MID, mats, view, C, basecol, Nv)
        rgba = shade_rgba(V, F, colour, nrm, mask, view)
        Image.fromarray(frame_down(rgba, res), 'RGBA').save(out_png)
    finally:
        RES = keep
    return out_png


# Two bars, because the colour norm asks two different questions.
#   COLOUR_BAR  "is there colour here at all" — a hue you can name. The floor
#               counts this. Muted naturalistic palettes live at S 0.30-0.40
#               (the example wolf's legs are #98815f, S 0.38); a plain grey-beige
#               palette sits near 0.17 and a grey mass at 0.
#   SAT_BAR     "is this LOUD" — the spotlight colour. The ceiling counts this.
# One bar cannot do both: at 0.50 the floor refuses every muted palette, and at
# 0.30-0.35 a dusky #6e5a98 wing (S 0.41) and a vivid one (S 0.80) measure the
# same, so the ceiling stops being about loudness.
COLOUR_BAR = 0.30
SAT_BAR = 0.50


def _srgb255(lin):
    lin = np.clip(lin, 0.0, 1.0)
    srgb = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1 / 2.4) - 0.055)
    return np.clip(srgb * 255.0, 0, 255)


def _hsv_s(d):
    mx, mn = d.max(axis=1), d.min(axis=1)
    return np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-9), 0.0)


def colour_measures(body, colour, albedo=None):
    """The colour numbers, off the file — no renderer, no lights.

    They used to come from a headless browser: render the model, read the pixels,
    count. Rendering was never what made them true — the colour is in the file,
    and the z-buffer above already decides which surface each pixel sees.

    median_lum              how bright the SHIPPED colour is, 0-255 sRGB — the
                            baked COLOR_0 x baseColorFactor, ramp, AO and shadow
                            included, because "do not crush to black" is about
                            what ships
    coloured_area           share of the view whose PALETTE colour has
                            HSV S >= COLOUR_BAR (0.30): the floor's number
    saturated_area          share whose PALETTE colour has HSV S >= SAT_BAR
                            (0.50): the ceiling's number
    palette_source          'albedo' when the file carries the engine's palette
                            record (asset.extras.albedo); 'shipped' when it does
                            not and both areas fell back to the baked colour
    saturated_area_shipped  S >= 0.50 on the baked colour, for comparison only

    The two areas read the PALETTE — the albedo before any lighting — because
    that is what the designer chose and what the claim tells them to change.
    The baked colour is a different number: the shading stack ramps it, boosts
    chroma up top (L4, x1.25) and shadows it, and each of those moves HSV S.
    Until the stack's shadows became a true multiply they RAISED S (L scaled at
    constant a, b): the example wolf's grey-brown legs measured 21.3% "highly
    saturated" while its palette measured 0.1%, and a #6e5a98 membrane (S 0.41)
    shipped 64% of its vertices over 0.50. A band calibrated on the baked colour
    is a band on the shading stack, and it moves every time the stack does.

    Unlit on purpose: lights move saturation too — a white key washes colour
    out, a blue rim invents it — and nobody ships the lighting rig."""
    if not body.any():
        return {}
    d = _srgb255(colour[body])
    lum = 0.2126 * d[:, 0] + 0.7152 * d[:, 1] + 0.0722 * d[:, 2]
    s_ship = _hsv_s(d)
    s = _hsv_s(_srgb255(albedo[body])) if albedo is not None else s_ship
    return {'median_lum': round(float(np.median(lum)), 1),
            'coloured_area': round(float((s >= COLOUR_BAR).mean()), 4),
            'saturated_area': round(float((s >= SAT_BAR).mean()), 4),
            'palette_source': 'albedo' if albedo is not None else 'shipped',
            'saturated_area_shipped': round(float((s_ship >= SAT_BAR).mean()), 4)}


def exaggeration(mask):
    """The numbers that answer 'is this bold enough' — no reader required.

    Every one of these used to be a thing someone squinted at. They are all
    properties of a set of pixels, and the pixels are a projection of vertices,
    so they were always arithmetic."""
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return {}
    w = float(xs.max() - xs.min() + 1)
    h = float(ys.max() - ys.min() + 1)
    area = float(mask.sum())
    m = {
        'box_fill': round(area / (w * h), 3),         # spindly vs blobby
        'sq_fill': round(area / (max(w, h) ** 2), 3),  # volume in a 1:1 frame
        'extent': round(max(w, h) / min(w, h), 3),     # how far from square
    }
    try:
        from scipy import ndimage
        from scipy.spatial import ConvexHull
        pts = np.stack([xs, ys], axis=1).astype(float)
        if len(pts) >= 3:
            try:
                hull = ConvexHull(pts)
                # bites taken out of the outline: 1.0 = a blob, lower = real
                # negative space
                m['convexity'] = round(area / max(hull.volume, 1.0), 3)
            except Exception:
                pass
        half = mask[:, :mask.shape[1] // 2]
        other = np.fliplr(mask[:, mask.shape[1] - half.shape[1]:])
        m['mirror_sym'] = round(float((half == other).mean()), 3)
    except ImportError:
        pass
    return m


def iou(a, b):
    if a.shape != b.shape:
        return None
    u = int((a | b).sum())
    return round(int((a & b).sum()) / u, 4) if u else None


def thumb(mask, px, path):
    """Letterboxed, as the measure pass always was: the proportion the reader sees is
    the proportion the file records."""
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        Image.new('L', (px, px), 255).resize((240, 240), Image.NEAREST).save(path)
        return
    sub = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    im = Image.fromarray(np.where(sub, 0, 255).astype(np.uint8), 'L')
    W, H = im.size
    w = px if W >= H else max(1, round(px * W / H))
    h = px if H > W else max(1, round(px * H / W))
    box = Image.new('L', (px, px), 255)
    box.paste(im.resize((w, h), Image.LANCZOS), ((px - w) // 2, (px - h) // 2))
    box.resize((240, 240), Image.NEAREST).save(path)


def _fill(px, py, F, res):
    """Union of the given triangles' projections — no depth test, a coverage mask."""
    img = Image.new('1', (res, res), 0)
    drw = ImageDraw.Draw(img)
    for a, b_, c in F:
        drw.polygon([(px[a], py[a]), (px[b_], py[b_]), (px[c], py[c])], fill=1)
    return np.array(img, dtype=bool)


# ── the head, per view ─────────────────────────────────────────────────────
# Three numbers, because "is the head ok from here" is more than one question:
#   head_share    share of the silhouette's pixels the head OWNS after the
#                 depth test — is it there at all from this side
#   head_out      share of the head's own outline that lies OUTSIDE the rest
#                 of the body's — does it read as a separate mass, or is it
#                 swallowed by the chest / shoulders / hump in front of it
#                 (1.0 = clear of the body, as in a profile; 0 = inside it)
#   head_px48     the head's size at reading size: the diameter of a disc with
#                 its projected area, on the 48px thumbnail
# A head can be present and still unreadable — a skull sitting inside the
# shoulder line from the front can own a fair share of the pixels and 0% of
# the outline.
#
# The bars, and where they come from — every azimuth of the three shipped
# creatures and the calibration wolf (wolf_green):
#   HEAD_OUT_MIN  0.15   front half of the ring: the wolves and the raven never
#                        go under 0.18; the giant, whose skull sits inside its
#                        shoulders, reads 0.000-0.006 at az315/az000/az045
#   HEAD_HIDDEN   0.01   the least-visible azimuth of the wolves and the raven
#                        is 2.8-4.5%; the giant's head is 0.0% at az135-az225
#   HEAD_SMALL    0.05   the head's BEST azimuth: raven 9.5%, wolves 17-29%,
#                        giant 2.5%
HEAD_OUT_MIN = 0.15
HEAD_HIDDEN = 0.01
HEAD_SMALL = 0.05
HEAD_VISIBLE = 0.02      # a head needs this much of the view to count as distinct


def head_measures(px, py, F, headtri, win_tri, mask):
    area = int(mask.sum())
    if headtri is None or not area:
        return {}
    owned = int(headtri[win_tri[mask]].sum())
    hp = _fill(px, py, F[headtri], mask.shape[0])
    rp = _fill(px, py, F[~headtri], mask.shape[0])
    hproj = int(hp.sum())
    only = int((hp & ~rp).sum())
    ys, xs = np.nonzero(mask)
    span = max(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1)
    m = {'head_share': round(owned / area, 4),
         'head_out': round(only / hproj, 3) if hproj else 0.0,
         'head_px48': round(2 * math.sqrt(hproj / math.pi) * 48.0 / span, 1)}
    m['head_distinct'] = bool(m['head_share'] >= HEAD_VISIBLE and m['head_out'] >= HEAD_OUT_MIN)
    return m


# ── the orbit, read as one object ──────────────────────────────────────────
# Per-view numbers cannot see the failure the owner named: "the views in
# between are not ok". A creature is not bad at 45 degrees in absolute terms,
# it is bad when an azimuth falls apart while the views either side of it
# hold. So the blob flag compares each azimuth with its two neighbours on the
# ring — except az000 and az180. Looking down the body's long axis is
# compact by nature (every wolf ever measured here is ~0.1 more convex
# end-on than at 45 degrees), so an end-on view that is lumpier than its
# neighbours is the form, not a fault.
#
#   blob         an OBLIQUE collapse that holds on a whole FLANK. Per azimuth,
#                the convexity deficiency cd = 1 - area / hull area (the bites
#                the limbs, head and tail take out of the outline), measured
#                on the eight masks cut to ONE window and reduced to 96 px and
#                to 48 px on its long side. Per oblique, the ratio of its cd to
#                the SMALLER of its two ring neighbours', the larger of the two
#                resolutions' ratios (the drop has to hold at both sizes). A
#                flank (az045 + az135, or az315 + az225) is a blob when BOTH its
#                obliques are at or under BLOB_RATIO — the front quarter and the
#                back quarter both close up, so it is the body, not one ear, one
#                tail brush or one wing tip landing on the outline.
#                Why not the old rule (convexity +0.07 over both neighbours, or
#                2 fewer protrusions than both): a protrusion COUNT jumps with
#                incidental features — the wolf held az090 only because its
#                ears counted as one more lump, a softer tail brush tipped it
#                to 5 against 7 and flagged it, and a raven with a tail 25 cm
#                shorter flagged az135/az225 on 4 against 6 and 9 while it
#                looked the same. The count is still in the ring table as
#                information; nothing is flagged on it. Bars and the stability
#                table (every shipped creature, the calibration wolves, the
#                pre-sixth-pass giant, ±20% ears / tail / brush / crest / tusks)
#                are in the CHANGELOG ("Orbit blob rule").
#   head_merged  front half of the ring (az270 through az000 to az090, where a
#                viewer looks for the face): under HEAD_OUT_MIN of the head's
#                outline clears the body
#   head_hidden  any azimuth where the head owns under HEAD_HIDDEN of the view
#   head_small   the head's best azimuth is under HEAD_SMALL — it is small
#                from everywhere, not hidden from one side
#
# All four are ADVICE (harness/gates.json: orbit_consistent, head_reads). Four
# creatures, one of them flagged, is enough to say where to look and not
# enough to refuse a build over; the numbers are in the CHANGELOG.
BLOB_RATIO = 0.68         # oblique cd / smaller neighbour's cd, on both obliques of a flank
BLOB_RES = (96, 48)       # the ring window's long side, px, for the cd measure
BLOB_FLANKS = (('az045', 'az135'), ('az315', 'az225'))
END_ON = ('az000', 'az180')
FRONT_HALF = ('az270', 'az315', 'az000', 'az045', 'az090')
MIRRORS = (('az045', 'az315'), ('az090', 'az270'), ('az135', 'az225'))
MIRROR_SAME = 0.90       # a pair this similar is one silhouette, shown once


def ring_cd(masks, n):
    """Convexity deficiency (1 - area / hull area) per azimuth, all eight cut to
    ONE window (the union of their boxes, squared) and reduced to n px on its
    long side — the same grid for every view of a creature, at a size where a
    two-pixel ear is not a feature. None without scipy."""
    try:
        from scipy import ndimage
        from scipy.spatial import ConvexHull
    except ImportError:
        return None
    u = None
    for v in AZIMUTHS:
        u = masks[v].copy() if u is None else (u | masks[v])
    ys, xs = np.nonzero(u)
    if len(xs) == 0:
        return None
    side = int(max(ys.max() - ys.min(), xs.max() - xs.min())) + 1
    y0 = int((ys.min() + ys.max() + 1) // 2 - side // 2)
    x0 = int((xs.min() + xs.max() + 1) // 2 - side // 2)
    out = {}
    for v in AZIMUTHS:
        m = masks[v]
        win = np.zeros((side, side), bool)
        sy, sx = max(y0, 0), max(x0, 0)
        crop = m[sy:y0 + side, sx:x0 + side]
        win[sy - y0:sy - y0 + crop.shape[0], sx - x0:sx - x0 + crop.shape[1]] = crop
        z = ndimage.zoom(win.astype(float), n / side, order=1) > 0.5
        py, px = np.nonzero(z)
        if len(px) < 3:
            out[v] = None
            continue
        try:
            hull = ConvexHull(np.stack([px, py], 1).astype(float)).volume
        except Exception:
            out[v] = None
            continue
        out[v] = round(1.0 - float(z.sum()) / max(hull, 1.0), 4)
    return out


def blob_ratios(masks):
    """Per oblique: its cd over the smaller of its two neighbours' cd, the larger
    of the ratios at the BLOB_RES sizes (a drop has to hold at every size), plus
    the cd per azimuth at each size. None without scipy."""
    cds = {n: ring_cd(masks, n) for n in BLOB_RES}
    if any(c is None for c in cds.values()):
        return None, None
    ratio = {}
    for i, v in enumerate(AZIMUTHS):
        if v in END_ON:
            continue
        L, R = AZIMUTHS[i - 1], AZIMUTHS[(i + 1) % len(AZIMUTHS)]
        rs = []
        for c in cds.values():
            if None in (c[v], c[L], c[R]):
                break
            rs.append(c[v] / max(min(c[L], c[R]), 0.01))
        else:
            ratio[v] = round(max(rs), 3)
    return ratio, cds


def orbit_report(views, masks):
    if not all(v in views and not views[v].get('empty') for v in AZIMUTHS):
        return None
    bratio, bcd = blob_ratios(masks)
    ring = []
    amax = max(views[v].get('area_px', 0) for v in AZIMUTHS) or 1
    for v in AZIMUTHS:
        d = views[v]
        ring.append({'view': v, 'area_rel': round(d.get('area_px', 0) / amax, 3),
                     'W_over_H': d.get('W_over_H'), 'convexity': d.get('convexity'),
                     'protrusions': d.get('protrusions'), 'thinnest_px48': d.get('thinnest_px48'),
                     'cd96': (bcd or {}).get(96, {}).get(v), 'cd48': (bcd or {}).get(48, {}).get(v),
                     'blob_ratio': (bratio or {}).get(v),
                     'head_share': d.get('head_share'), 'head_out': d.get('head_out'),
                     'head_distinct': d.get('head_distinct')})
    flags = []
    if bratio:
        for front, back in BLOB_FLANKS:
            rf, rb = bratio.get(front), bratio.get(back)
            if None in (rf, rb) or max(rf, rb) > BLOB_RATIO + 1e-9:
                continue
            for v, rv in ((front, rf), (back, rb)):
                i = AZIMUTHS.index(v)
                L, R = AZIMUTHS[i - 1], AZIMUTHS[(i + 1) % len(AZIMUTHS)]
                c = bcd[BLOB_RES[0]]
                flags.append({'view': v, 'kind': 'blob',
                              'why': f"the outline has {rv:.2f}x the bites of its smaller neighbour "
                                     f"(cd {c[v]:.2f} against {c[L]:.2f} {L} / {c[R]:.2f} {R}), and "
                                     f"the other oblique on this flank ({back if v == front else front}) "
                                     f"closes too — limbs and head fold into the body from this side"})
    for i, r in enumerate(ring):
        hs = r['head_share']
        if hs is None:
            continue
        if hs < HEAD_HIDDEN:
            flags.append({'view': r['view'], 'kind': 'head_hidden',
                          'why': f"the head owns {hs * 100:.1f}% of the view — from here the "
                                 f"creature has no head"})
        elif r['view'] in FRONT_HALF and r['head_out'] is not None and r['head_out'] < HEAD_OUT_MIN:
            flags.append({'view': r['view'], 'kind': 'head_merged',
                          'why': f"only {r['head_out'] * 100:.0f}% of the head's outline clears the body "
                                 f"(head {hs * 100:.1f}% of the view) — it does not read as its own mass"})
    shares = [r['head_share'] for r in ring if r['head_share'] is not None]
    if shares and max(shares) < HEAD_SMALL:
        best = max(ring, key=lambda r: r['head_share'] or 0)
        flags.append({'view': best['view'], 'kind': 'head_small',
                      'why': f"the head's BEST view is {best['view']} at {max(shares) * 100:.1f}% of "
                             f"the silhouette — it is small from everywhere"})
    mirror = {}
    for a, b in MIRRORS:
        mirror[f'{a}/{b}'] = iou(masks[a], np.fliplr(masks[b]))
    # What the blind reader is shown for Gate 1: the five azimuths from face to
    # tail plus the top. The other three azimuths are the mirror images of three
    # of those for a bilaterally symmetric creature — reading them is paying
    # twice for one silhouette — so they are added only when they differ.
    read = ['az000', 'az045', 'az090', 'az135', 'az180']
    for a, b in MIRRORS:
        if (mirror[f'{a}/{b}'] or 0) < MIRROR_SAME:
            read.append(b)
    read = [v for v in AZIMUTHS if v in read] + ['top']
    if bratio:
        worst = min((r for r in ring if r['blob_ratio'] is not None), key=lambda r: r['blob_ratio'])
    else:
        worst = max((r for r in ring if r['view'] not in END_ON), key=lambda r: (r['convexity'] or 0))
    return {'ring': ring, 'flags': flags, 'mirror_iou': mirror, 'read_set': read,
            'area_rel_min': min(r['area_rel'] for r in ring),
            'most_blobby': worst['view'],
            'blob_flanks': {f'{a}+{b}': (max(bratio[a], bratio[b])
                                         if bratio and a in bratio and b in bratio else None)
                            for a, b in BLOB_FLANKS},
            'head_best': max(shares) if shares else None,
            'head_distinct_views': [r['view'] for r in ring if r['head_distinct']]}


# ── the contact sheets ─────────────────────────────────────────────────────
SHEET_TILE = 256
SHEET_LABEL = 22


def _font(size):
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def _group_window(masks, names, margin=1.08):
    u = None
    for v in names:
        if v in masks:
            u = masks[v] if u is None else (u | masks[v])
    if u is None or not u.any():
        return None
    return square_window(u, margin)


def orbit_windows(masks):
    """One window for the eight azimuths (they share a camera distance, so a
    shared crop keeps them at one scale and a view that shrinks LOOKS smaller)
    and one for the two poles."""
    wa = _group_window(masks, AZIMUTHS)
    wp = _group_window(masks, ('top', 'bottom'))
    return {v: (wa if is_azimuth(v) else wp if v in ('top', 'bottom') else None) for v in masks}


def sheet(tiles, labels, warn, path, bg):
    cols, rows = 5, 2
    W = cols * SHEET_TILE
    H = rows * (SHEET_TILE + SHEET_LABEL)
    im = Image.new('RGB', (W, H), bg)
    drw = ImageDraw.Draw(im)
    font = _font(14)
    for k, v in enumerate(ORBIT):
        x, y = (k % cols) * SHEET_TILE, (k // cols) * (SHEET_TILE + SHEET_LABEL)
        t = tiles.get(v)
        if t is not None:
            if t.mode == 'RGBA':
                im.paste(t, (x, y + SHEET_LABEL), t)
            else:
                im.paste(t, (x, y + SHEET_LABEL))
        drw.rectangle([x, y, x + SHEET_TILE - 1, y + SHEET_LABEL - 1],
                      fill=(150, 30, 30) if warn.get(v) else (40, 40, 44))
        drw.text((x + 6, y + 3), labels.get(v, v), fill=(255, 255, 255), font=font)
        drw.rectangle([x, y, x + SHEET_TILE - 1, y + SHEET_TILE + SHEET_LABEL - 1],
                      outline=(120, 120, 124))
    im.save(path)
    return path


def _sil_tile(mask, window):
    x0, y0, side = window if window else square_window(mask)
    H, W = mask.shape
    pad = np.zeros((side, side), dtype=bool)
    sx0, sy0 = max(0, x0), max(0, y0)
    sx1, sy1 = min(W, x0 + side), min(H, y0 + side)
    if sx1 > sx0 and sy1 > sy0:
        pad[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = mask[sy0:sy1, sx0:sx1]
    im = Image.fromarray(np.where(pad, 0, 255).astype(np.uint8), 'L')
    return im.resize((SHEET_TILE, SHEET_TILE), Image.BOX)


def main():
    global FACING
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__)
        return 2
    model, outdir = a[0], a[1]
    prev = a[a.index('--prev') + 1] if '--prev' in a else None
    hero_out = a[a.index('--hero') + 1] if '--hero' in a else None
    views = expand_views(a[a.index('--views') + 1] if '--views' in a else 'orbit')
    no_colour = '--no-colour' in a
    os.makedirs(outdir, exist_ok=True)
    t0 = time.time()

    if hero_out:
        hero_png(model, hero_out)
        print(f'hero: {hero_out}')
    V, F, MID, mats, C, basecol, Nv = triangles_by_material(model, want_colour=True)
    A = albedo_of(model, V)
    head, head_how = head_vertices(model, len(V))
    headtri = (head[F].sum(axis=1) >= 2) if head is not None else None
    if headtri is not None and (not headtri.any() or headtri.all()):
        headtri = None
    FACING, facing_how = facing_of(V, head)
    boxes, whole = part_boxes(V, F, MID, mats)
    report = {'vertices': int(len(V)), 'triangles': int(len(F)),
              'materials': mats, 'stats': structure(model),
              'parts': boxes, 'whole': {'size': whole},
              'facing': {'forward': [float(x) for x in FACING], 'from': facing_how,
                         'head': head_how if headtri is not None else f'none — {head_how}'},
              'views': {}}
    thin_all = []
    masks, rgbas = {}, {}
    for v in views:
        shares, mask, colour, nrm, *rest = material_shares(
            V, F, MID, mats, v, C, basecol, Nv, A=A, want_tri=True)
        win_tri = rest[-1]
        alb = rest[0] if len(rest) == 2 else None
        masks[v] = mask
        np.save(os.path.join(outdir, f'mask_{v}.npy'), mask)
        Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), 'L').save(
            os.path.join(outdir, f'sil_{v}.png'))
        for px in (24, 48):
            thumb(mask, px, os.path.join(outdir, f'sil_{v}_thumb{px}.png'))
        mm = measures(mask)
        mm['area_px'] = int(mask.sum())
        mm.update(exaggeration(mask))
        mm.update(colour_measures(mask, colour, alb))
        px_, py_, _z = project(V, v)
        mm.update(head_measures(px_, py_, F, headtri, win_tri, mask))
        mm['share'] = shares
        if not no_colour:
            rgbas[v] = shade_rgba(V, F, colour, nrm, mask, v, shadow=(v != 'bottom'))
        if mm.get('thinnest_px48') is not None:
            thin_all.append(mm['thinnest_px48'])
        if prev:
            p = os.path.join(prev, f'mask_{v}.npy')
            if os.path.exists(p):
                mm['iou_vs_prev'] = iou(mask, np.load(p))
        for name, sh in shares.items():
            if name in report['parts']:
                report['parts'][name].setdefault('share', {})[v] = sh
        report['views'][v] = mm

    # colour per view, cropped like the sheet so a reviewer flipping through
    # the files sees one scale
    wins = orbit_windows(masks)
    for v, rgba in rgbas.items():
        Image.fromarray(frame_down(rgba, 384, wins.get(v)), 'RGBA').save(
            os.path.join(outdir, f'col_{v}.png'))

    orbit = orbit_report(report['views'], masks)
    if orbit:
        report['orbit'] = orbit
        warn = {}
        for f in orbit['flags']:
            warn.setdefault(f['view'], []).append(f['kind'])
        labels = {}
        for v in ORBIT:
            d = report['views'].get(v, {})
            hs = d.get('head_share')
            lab = v + (f'  head {hs * 100:.0f}%' if hs is not None else '')
            if warn.get(v):
                lab += '  ' + '/'.join(sorted(set(warn[v]))).upper()
            labels[v] = lab
        if rgbas:
            tiles = {}
            for v in ORBIT:
                if v in rgbas:
                    tiles[v] = Image.fromarray(frame_down(rgbas[v], SHEET_TILE, wins.get(v)), 'RGBA')
            sheet(tiles, labels, warn, os.path.join(outdir, 'orbit_sheet.png'), (206, 206, 210))
        sheet({v: _sil_tile(masks[v], wins.get(v)) for v in ORBIT}, labels, warn,
              os.path.join(outdir, 'orbit_sil_sheet.png'), (255, 255, 255))

    if thin_all:
        report['thinnest_px48'] = min(thin_all)
    ious = {v: d['iou_vs_prev'] for v, d in report['views'].items()
            if d.get('iou_vs_prev') is not None}
    if ious:
        # The round moved as much as its most-changed view says it did — over
        # the views the 0.85 tweak bar was calibrated on (front, side, top and
        # the three-quarter view; on the orbit, az000, az090, top and az045).
        # Ten views give ten chances for one small view to swing, and a bar set
        # on four would quietly stop catching nudges.
        core = [ious[v] for v in ('front', 'side', 'top', 'hero', 'az000', 'az045', 'az090')
                if v in ious]
        report['iou_vs_prev'] = min(core or ious.values())
        report['iou_vs_prev_all'] = min(ious.values())
    report['seconds'] = round(time.time() - t0, 2)

    mpath = os.path.join(outdir, 'metrics.json')
    merged = {}
    if os.path.exists(mpath):
        try:
            prevj = json.load(open(mpath, encoding='utf-8'))
            if isinstance(prevj, dict):
                merged = prevj
        except Exception:
            pass
    merged.update(report)
    if not orbit:
        merged.pop('orbit', None)
    json.dump(merged, open(mpath, 'w', encoding='utf-8'), indent=1)

    print(f"{report['triangles']} triangles, {len(views)} views, no browser, "
          f"{report['seconds']}s — facing {facing_how}")
    for v, d in report['views'].items():
        bits = [f"W/H {d.get('W_over_H')}"]
        if d.get('thinnest_px48') is not None:
            bits.append(f"thinnest {d['thinnest_px48']}px")
        if d.get('protrusions') is not None:
            bits.append(f"{d['protrusions']} protrusion(s)")
        if d.get('head_share') is not None:
            bits.append(f"head {d['head_share'] * 100:.0f}%"
                        + ('' if d.get('head_distinct') else ' (merged)'))
        if d.get('iou_vs_prev') is not None:
            bits.append(f"iou {d['iou_vs_prev']}")
        print(f'  {v:<6} ' + '  '.join(bits))
    if orbit:
        print(f"  orbit: sheets {os.path.join(outdir, 'orbit_sheet.png')} · orbit_sil_sheet.png")
        if headtri is None:
            print(f'  advise  no head found ({head_how}) — the head measures are off')
        for f in orbit['flags']:
            print(f"  advise  {f['view']}: {f['kind']} — {f['why']}")
        if not orbit['flags']:
            print('  orbit holds: no azimuth collapses against its neighbours, the head reads')
    return 0


if __name__ == '__main__':
    sys.exit(main())
