"""parts — the kit's parts library: faces and extremities, authored once, reused on every creature.

Both artist reviews (experiments/boxmodel/research/artist_review_opus.md and artist_review_fable.md,
change 3) ask for the same thing: no builder models a paw, a hand or an eye from scratch again.
Every generator here returns ONE Blender mesh object in the project style (flat shaded, few large
planes), ready to be a stage-3 piece or a proxy on a blockout:

    import parts as P
    eye = P.eye_set((0.06, -0.31, 0.52), 0.022, forward=(0.5, -0.85, 0.1), expression='angry')
    paw = P.paw_canine((0.11, -0.28, 0.07), width=0.08, mats={'skin': 'fur_tan'})

FRAME. Every part is built in a local frame and placed with three arguments:
    origin / center / base   where the part sits (world, metres)
    forward                  the way the part points (toes, fingers, the eye's line of sight, a horn's growth)
    up                       the part's own up (the back of a hand, the top of an eye, the way a horn bends)
Local +x is forward x up. With the kit's convention (creature faces -Y, Z up, left flank +X) that
is the creature's RIGHT, so for a part on the LEFT side local +x points at the midline: the medial
side. Big toe, thumb and the inner eye corner are built on local +x. For the right flank pass the
mirrored origin / forward / up AND side=-1 (side flips local x, so the medial side stays medial).

MATERIAL SLOTS. Each face carries a named slot ('skin', 'pad', 'claw', 'iris' ...). A slot becomes
a material of that name (bmkit.material), with a neutral default colour from COLOURS.
    mats={'skin': 'fur_tan', 'pad': 'dark'}   send slots to the creature's own palette names
    colours={'iris': '#d8a020'}               set a slot's colour here
A material that already exists is reused as it is unless `colours` names its slot, so a part can
never repaint the creature's palette by accident. To recolour later: bmkit.material(name, bmkit.srgb(hex)).
The stage-3 gate counts distinct COLOURS (4-8), not names: map the part slots onto the palette
with `mats` (or give a slot a palette colour with `colours`) and a part adds nothing to the count.

ATTACH. Parts are closed shells whose root is buried in the body (the kit's piece rule: one entry
ring, no floating). Limb ends (paws, hooves, feet, hands) also take open_root=True: the root cap is
left out and attach(ob)['root_ring'] lists the open ring in order; bmkit.bridge_part(part, ring)
stitches it onto a cage's limb ring of any vertex count (stage 3: k.bridge_part, the part stays a
piece; stage 1: bridge_part(part, ring, bm=bm) welds it into the base before the lock).
attach(ob) returns every named point in world space (claw tips, toe tips, pupil, brow ends ...).
socket_frame(ring_points) turns an open ring or a socket face into origin / forward / radius.

An eye piece cannot dent a body it does not own: everything that shows sits above the skin, and the
depth comes from a raised rim round a lower eyeball. `center` is the point ON the skin.

TRIANGLES (defaults; every generator's docstring states its own, and its lite settings): see PARTS
at the end of the file. A creature with four paws, eyes, ears, teeth, a ruff and a tail spends
about 1,100 triangles on parts at the defaults and about 600 on the lite settings.

The claw (a tapering hook swept along an arc, taller than wide, root buried in the toe), the paw
(palm plus a toe row on an arc, returning claw roots) and the eye depth rule come from the ideas
noted in experiments/boxmodel/research/tpa_opus_transfer.md section 3.4 (an MIT-licensed project);
nothing was ported: the code below is written for this kit, low-sided and faceted where theirs is smooth.
"""
import bpy, bmesh, json, math
from mathutils import Vector, Matrix
import bmkit as k

COLOURS = dict(
    skin='#b58f66', pad='#3b2d2a', claw='#ece4cf', hoof='#3a2e29', scale='#d9a441',
    eye_rim='#9a7650', eye_socket='#1d1513', iris='#e0a12c', sclera='#f6f3ea', pupil='#0b0909',
    glint='#ffffff', outline='#15100f', lid='#8a6846',
    ear='#b58f66', ear_inner='#e3a79b', horn='#d9ccb0', horn_tip='#8f8168', antler='#c9b58f',
    tooth='#f3eddb', gum='#a24c4c', nose='#5a484a', nostril='#0d0909',
    fur='#b58f66', fur_tip='#efe4c8', fur_under='#8a6846')


# =============================================================================
# the builder: indexed points and slotted faces, compiled to one object
# =============================================================================
class _B:
    def __init__(self):
        self.P, self.F = [], []

    def v(self, p):
        self.P.append(Vector(p))
        return len(self.P) - 1

    def ring(self, pts):
        return [self.v(p) for p in pts]

    def face(self, idx, slot):
        self.F.append((tuple(idx), slot))
        return len(self.F) - 1

    def bridge(self, a, b, slot, closed=True, skip=()):
        """Quads between two rings; slot is a name or f(i) -> name."""
        n = len(a)
        for i in range(n if closed else n - 1):
            if i in skip:
                continue
            j = (i + 1) % n
            self.face((a[i], a[j], b[j], b[i]), slot(i) if callable(slot) else slot)

    def cap(self, ring, slot):
        return self.face(ring, slot)

    def fan(self, ring, tip, slot):
        n = len(ring)
        for i in range(n):
            self.face((ring[i], ring[(i + 1) % n], tip), slot(i) if callable(slot) else slot)

    def centre(self, idx):
        return sum((self.P[i] for i in idx), Vector()) / len(idx)

    def inset(self, fi, amount, depth, out, slot_side, slot_inner):
        """Replace face fi by a rim of quads and an inner face pushed `depth` against `out`."""
        idx, _ = self.F[fi]
        c = self.centre(idx)
        n = Vector(out).normalized()
        new = [self.v(self.P[i].lerp(c, amount) - n * depth) for i in idx]
        self.F[fi] = (tuple(new), slot_inner)
        self.bridge(list(idx), new, slot_side)


def _frame(origin, forward, up):
    f = Vector(forward).normalized()
    u = Vector(up) - f * Vector(up).dot(f)
    if u.length < 1e-6:
        u = Vector((0, 0, 1)) if abs(f.z) < 0.9 else Vector((0, -1, 0))
        u -= f * u.dot(f)
    u.normalize()
    x = f.cross(u)
    M = Matrix((x, f, u)).transposed().to_4x4()
    M.translation = Vector(origin)
    return M


def _finish(B, name, M, side=1, mats=None, colours=None, attach_pts=None):
    mats, colours = mats or {}, colours or {}
    T = M @ Matrix.Diagonal((float(side), 1.0, 1.0, 1.0))
    bm = bmesh.new()
    vs = [bm.verts.new(T @ p) for p in B.P]
    names, made = [], {}
    for idx, slot in B.F:
        nm = mats.get(slot, slot)
        if nm not in names:
            names.append(nm)
            m = bpy.data.materials.get(nm)
            if m is None or slot in colours:
                m = k.material(nm, k.srgb(colours.get(slot) or COLOURS.get(slot, '#b0a090')))
            made[nm] = m
        f = bm.faces.new([vs[i] for i in idx])
        f.material_index = names.index(nm)
    tris = sum(len(i) - 2 for i, _ in B.F)
    ob = k.object_from_bm(name, bm, mirror=False)
    bm.free()
    for nm in names:
        ob.data.materials.append(made[nm])
    k.white(ob)
    out = {}
    for key, p in (attach_pts or {}).items():
        if isinstance(p, list):
            out[key] = [[round(c, 5) for c in (T @ Vector(q))] for q in p]
        else:
            out[key] = [round(c, 5) for c in (T @ Vector(p))]
    ob['attach'] = json.dumps(out)
    ob['tris'] = tris
    return ob


def attach(ob):
    """The part's named attach points in world space: {name: Vector or [Vector, ...]}."""
    d = json.loads(ob.get('attach', '{}'))
    return {n: ([Vector(q) for q in p] if p and isinstance(p[0], list) else Vector(p)) for n, p in d.items()}


def socket_frame(ring_points):
    """An open ring (or the corners of a socket face) -> dict(origin, forward, radius, width, depth).
    forward is the ring's normal by the right-hand rule on the point order; flip it if it points
    into the body. Feed origin / forward to a generator and width / depth to its root size."""
    P = [Vector(p) for p in ring_points]
    c = sum(P, Vector()) / len(P)
    n = Vector()
    for i in range(len(P)):
        n += (P[i] - c).cross(P[(i + 1) % len(P)] - c)
    n.normalize()
    r = sum((p - c).length for p in P) / len(P)
    a = max(P, key=lambda p: (p - c).length) - c
    b = n.cross(a.normalized())
    return dict(origin=c, forward=n, radius=r, width=2 * a.length, depth=2 * max(abs((p - c).dot(b)) for p in P))


# =============================================================================
# shared geometry
# =============================================================================
def _sect(sides, w, h):
    """Cross-section offsets (across, up). 4: a box. 3: ridge on top, flat underneath. n: an ellipse."""
    if sides == 4:
        return [(-w / 2, h / 2), (w / 2, h / 2), (w / 2, -h / 2), (-w / 2, -h / 2)]
    if sides == 3:
        return [(0.0, h / 2), (w / 2, -h / 2), (-w / 2, -h / 2)]
    return [(w / 2 * math.sin(2 * math.pi * i / sides), h / 2 * math.cos(2 * math.pi * i / sides)) for i in range(sides)]


def _sweep(B, pts, sizes, up, slot, sides=4, start=None, cap0=True, end='cap', sect=None):
    """A tube through pts with mitred joints. sizes[i] = (width, height) at pts[i].
    start: an existing ring (indices) used as the first ring. end: 'cap' or 'point' (the last
    point is the tip). slot: name or f(band, side). Returns the rings (lists of indices)."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    d = [(pts[i + 1] - pts[i]).normalized() for i in range(n - 1)]
    u = [None] * (n - 1)
    u0 = Vector(up) - d[0] * Vector(up).dot(d[0])
    u[0] = u0.normalized()
    for i in range(1, n - 1):
        u[i] = (d[i - 1].rotation_difference(d[i]) @ u[i - 1]).normalized()
    rings, tip = [], None
    for i in range(n):
        if i == 0 and start is not None:
            rings.append(list(start))
            continue
        if i == n - 1 and end == 'point':
            tip = B.v(pts[i])
            break
        j = min(max(i - 1, 0), n - 2)
        s = d[j].cross(u[j])
        w, h = sizes[i]
        sec = sect(i, w, h) if sect else _sect(sides, w, h)
        P = [pts[i] + s * a + u[j] * b for a, b in sec]
        if 0 < i < n - 1:
            bis = d[i - 1] + d[i]
            if bis.length > 1e-6:
                bis.normalize()
                den = max(d[i - 1].dot(bis), 0.35)
                P = [p - d[i - 1] * ((p - pts[i]).dot(bis) / den) for p in P]
        rings.append(B.ring(P))
    sl = (lambda b: (lambda i: slot(b, i))) if callable(slot) else (lambda b: slot)
    for b in range(len(rings) - 1):
        B.bridge(rings[b], rings[b + 1], sl(b))
    if cap0 and start is None:
        B.cap(rings[0], slot(0, -1) if callable(slot) else slot)
    last = len(rings) - 1
    if end == 'point':
        B.fan(rings[-1], tip, sl(last))
    else:
        B.cap(rings[-1], slot(last - 1, -1) if callable(slot) else slot)
    return rings


def _rot(v, axis, deg):
    return Matrix.Rotation(math.radians(deg), 3, Vector(axis).normalized()) @ Vector(v)


def _claw(B, root, fwd, down, L, w, h, curve=55.0, segs=2, sides=3, slot='claw', bury=0.3):
    """A thick hook: an arc from `root` along `fwd` bending toward `down`, section taller than wide,
    ridge on the outer curve, tapering to the tip; the root is buried `bury` x L behind `root`.
    Returns the tip point."""
    fwd, down = Vector(fwd).normalized(), Vector(down).normalized()
    axis = fwd.cross(down)
    if axis.length < 1e-6:
        axis = fwd.orthogonal()
    pts = [Vector(root) - fwd * (bury * L)]
    sizes = [(w, h)]
    p = Vector(root)
    for j in range(segs):
        if j == 0 and segs > 2:
            pts.append(p.copy())
            sizes.append((w, h))
        dj = _rot(fwd, axis, curve * (j + 0.5) / segs)
        p = p + dj * (L / segs)
        t = (j + 1) / segs
        pts.append(p.copy())
        sizes.append((w * (1 - 0.7 * t), h * (1 - 0.7 * t)))
    _sweep(B, pts, sizes, -down, slot, sides=sides, end='point')
    return pts[-1]


def _rows(B, top, bot):
    """A limb-end ring made of a top row and a bottom row (both left to right, n+1 points):
    indices t0..tn, bn..b0. Quad i of a bridge is top (i < n), the +x side (n), bottom, the -x side."""
    t, b = B.ring(top), B.ring(bot)
    return t + b[::-1], t, b


def _bounds(widths, W):
    tot = float(sum(widths))
    xs, x = [-W / 2], -W / 2
    for w in widths:
        x += W * w / tot
        xs.append(x)
    return xs


# =============================================================================
# EYES
# =============================================================================
EXPRESSIONS = dict(neutral=dict(brow=0.0, lid=0.16, arch=0.22),
                   angry=dict(brow=22.0, lid=0.30, arch=0.0),
                   friendly=dict(brow=-9.0, lid=-0.12, arch=0.50),
                   sleepy=dict(brow=-6.0, lid=0.56, arch=0.06))


def eye_set(center, radius, forward=(0, -1, 0), up=(0, 0, 1), side=1, expression='neutral', style='animal',
            aspect=None, pupil='round', pupil_size=None, look=(0.0, 0.0), brow=None, lid=None, arch=None,
            brow_wedge=True, lower_lid=0.0, glint=True, sides=None, name='eye', mats=None, colours=None):
    """One eye: socket rim, eyeball seated below the rim, pupil, catchlight facet, upper lid / brow wedge.

    center      point ON the skin; forward = the eye's line of sight (the skin normal); up = head up
    radius      half the height of the eye opening (metres). Typical: 0.07-0.10 of head length
                (animal), 0.16-0.22 (toon)
    side        +1 left eye (inner corner on local +x), -1 right eye
    style       'animal': almond hexagon, coloured iris fills the eye, dark socket ring round it
                'toon':   big white sclera dome, black outline ring, large pupil
    aspect      opening width / height (animal 1.3, toon 0.85)
    expression  'neutral' | 'angry' | 'friendly' | 'sleepy': presets for the three numbers below
    brow        degrees; + drops the inner end of the lid/brow wedge (angry), - raises it (worried)
    lid         0..1 how much of the eye the upper lid covers (below 0 lifts the brow off the eye)
    arch        0..1 how much the lid edge arcs over the eye (0 = a straight bar)
    brow_wedge  False leaves the wedge out (a bird, a fish)
    lower_lid   0..1 height of an optional lower lid (0 = none)
    pupil       'round' | 'slit' (cat, reptile) | 'bar' (goat, deer); pupil_size in radii
    look        (x, z) pupil shift in radii, the same way for both eyes (x + = the creature's left)
    glint       the catchlight facet (upper outer side of the pupil, same side on both eyes)
    sides       ring sides (animal 6, toon 8)
    Slots: eye_rim, eye_socket, iris | outline, sclera; pupil, glint, lid.
    Attach: center, pupil, brow_inner, brow_outer.
    Triangles: animal 80 (94 with a lower lid), toon 100; 20 less without the brow wedge.
    Depth rule kept: the front of the eyeball is 0.28 r (animal) / 0.4 r (toon) off the skin, inside
    the 1.3 r limit, and below the rim crest so the rim casts the socket shadow."""
    r = float(radius)
    toon = style == 'toon'
    n = sides or (8 if toon else 6)
    asp = aspect or (0.85 if toon else 1.3)
    b = r * (1.12 if toon else 1.0)
    a = r * asp * (1.12 if toon else 1.0)
    ex = dict(EXPRESSIONS[expression])
    for key, val in (('brow', brow), ('lid', lid), ('arch', arch)):
        if val is not None:
            ex[key] = val
    B = _B()

    def ell(sa, sb, y, cx=0.0, cz=0.0):
        return [Vector((cx + sa * math.cos(2 * math.pi * i / n), y, cz + sb * math.sin(2 * math.pi * i / n)))
                for i in range(n)]

    lx, lz = look[0] * r * side, look[1] * r
    if toon:
        pr = (pupil_size or 0.46) * r
        yc, yf = 0.14 * r, 0.40 * r                       # rim crest, eyeball front
        R = [B.ring(ell(1.30 * a, 1.30 * b, -0.22 * r)), B.ring(ell(1.24 * a, 1.24 * b, 0.10 * r)),
             B.ring(ell(1.05 * a, 1.05 * b, yc)), B.ring(ell(0.74 * a, 0.76 * b, 0.34 * r, lx * 0.3, lz * 0.3))]
        slots = ['outline', 'outline', 'sclera', 'sclera']
        back = 'outline'
    else:
        pr = (pupil_size or 0.40) * r
        yc, yf = 0.30 * r, 0.28 * r
        R = [B.ring(ell(1.58 * a, 1.62 * b, -0.22 * r)), B.ring(ell(1.28 * a, 1.30 * b, yc)),
             B.ring(ell(1.02 * a, 1.02 * b, 0.07 * r)), B.ring(ell(0.64 * a, 0.68 * b, 0.25 * r, lx * 0.3, lz * 0.3))]
        slots = ['eye_rim', 'eye_socket', 'iris', 'iris']
        back = 'eye_rim'
    pw, ph = {'round': (1.0, 1.0), 'slit': (0.46, 1.40), 'bar': (1.45, 0.50)}[pupil]
    R.append(B.ring(ell(pr * pw, pr * ph, yf, lx, lz)))
    B.cap(R[0], back)
    for i in range(4):
        B.bridge(R[i], R[i + 1], slots[i])
    B.cap(R[4], 'pupil')
    if glint:
        gx, gz = lx - 0.30 * r * side, lz + 0.30 * r
        g = 0.19 * r * (1.25 if toon else 1.0)
        base = B.ring([Vector((gx + g * math.cos(t), yf - 0.05 * r, gz + g * math.sin(t)))
                       for t in (math.radians(100), math.radians(220), math.radians(340))])
        B.cap(base, 'glint')
        B.fan(base, B.v((gx, yf + 0.07 * r, gz)), 'glint')

    xe = 1.30 * a
    tb = math.tan(math.radians(ex['brow']))

    def edge(x):
        return max(b * (1 - 2 * ex['lid']) - ex['arch'] * b * (x / xe) ** 2 - tb * x, -0.35 * b)

    def top(x):
        cover = 1.10 * b * math.sqrt(max(0.0, 1 - (x / (1.04 * a)) ** 2))
        return max(edge(x) + b * (0.62 - 0.26 * (x / xe) ** 2), cover + 0.06 * b)

    pts = dict(center=(0, 0, 0), pupil=(lx, yf, lz), brow_inner=(xe, yc, top(xe)), brow_outer=(-xe, yc, top(-xe)))
    if brow_wedge:
        rows = []
        for x in (-xe, -0.42 * xe, 0.42 * xe, xe):
            endf = abs(x) > 0.9 * xe
            yb = yc + (0.04 if endf else 0.24) * r + (0.10 * r if toon and not endf else 0.0)
            rows.append(B.ring([(x, -0.20 * r, top(x)), (x, yb, top(x) - 0.12 * b), (x, yb + 0.07 * r, edge(x))]))
        for i in range(3):
            B.bridge(rows[i], rows[i + 1], 'lid')
        B.cap(rows[0], 'lid')
        B.cap(rows[-1], 'lid')
    if lower_lid > 0:
        rows = []
        for x in (-0.95 * a, 0.0, 0.95 * a):
            f = 0.25 if x else 1.0
            zb = -1.30 * b * math.sqrt(max(0.0, 1 - (x / xe) ** 2)) - 0.04 * b
            ze = -b * (1 - 2 * lower_lid * f)
            yb = yc + (0.0 if x else 0.14) * r
            rows.append(B.ring([(x, -0.20 * r, zb), (x, yb, zb + 0.04 * b), (x, yb + 0.05 * r, max(ze, zb + 0.34 * b))]))
        for i in range(2):
            B.bridge(rows[i], rows[i + 1], 'lid')
        B.cap(rows[0], 'lid')
        B.cap(rows[-1], 'lid')
    return _finish(B, name, _frame(center, forward, up), side, mats, colours, pts)


# =============================================================================
# FEET: paws, the biped foot, the hoof, the bird foot
# =============================================================================
def _foot(B, W, H, heel, reach, root, toe_w, toe_len, Lt, toe_h, arc, slant, splay, instep, toe_segs,
          pads, claws, claw_len, claw_curve, open_root, lift=0.18):
    """Root ring at the origin (the ankle / wrist, z = 0); the ground is z = -H.
    One shell: palm from the root ring to the knuckle line, each toe extruded from its own quad."""
    n = len(toe_w)
    xs = _bounds(toe_w, W)
    u = [2 * x / W for x in xs]
    rw, rd = root
    sole = 'pad' if pads else 'skin'
    R0, _, _ = _rows(B, [(x * rw / W, rd / 2 * math.sqrt(1 - 0.55 * q * q), 0.0) for x, q in zip(xs, u)],
                     [(x * rw / W, -rd / 2 * math.sqrt(1 - 0.55 * q * q), 0.0) for x, q in zip(xs, u)])
    zi = -H + toe_h + (H - toe_h) * instep
    y1 = rd / 2 + 0.45 * max(reach - rd / 2, 0.0)          # ahead of the root's front edge: no undercut under the leg
    R1, _, _ = _rows(B, [(x * 0.94, y1 + 0.3 * arc * (1 - q * q), zi) for x, q in zip(xs, u)],
                     [(x * 0.80, -heel * (1 - 0.28 * q * q), -H) for x, q in zip(xs, u)])
    yk = [reach + arc * (1 - q * q) + slant * q for q in u]
    R2, t2, b2 = _rows(B, [(x, y, -H + toe_h) for x, y in zip(xs, yk)], [(x, y, -H) for x, y in zip(xs, yk)])
    side_slot = lambda i: sole if n < i < 2 * n + 1 else 'skin'
    B.bridge(R0, R1, 'skin')
    B.bridge(R1, R2, side_slot)
    if not open_root:
        B.cap(R0, 'skin')
    tips, claw_tips = [], []
    Lmax = max(toe_len)
    for i in range(n):
        w = xs[i + 1] - xs[i]
        cx = (xs[i] + xs[i + 1]) / 2
        yaw = math.radians(splay * 2 * cx / W)
        d = Vector((math.sin(yaw), math.cos(yaw), 0.0))
        c0 = Vector((cx, (yk[i] + yk[i + 1]) / 2, -H + toe_h / 2))
        L = Lt * toe_len[i] / Lmax
        tip_h = 0.66 * toe_h
        p2 = Vector((c0.x, c0.y, -H + tip_h / 2)) + d * L
        if toe_segs >= 2:
            p1 = c0 + d * (0.52 * L) + Vector((0, 0, lift * toe_h))
            pts, sizes = [c0, p1, p2], [(w, toe_h), (0.90 * w, 1.04 * toe_h), (0.70 * w, tip_h)]
        else:
            pts, sizes = [c0, p2], [(w, toe_h), (0.70 * w, tip_h)]
        pad_from = len(pts) - 2                      # toe pads sit under the last joint only: a skin gap to the palm pad
        _sweep(B, pts, sizes, (0, 0, 1), lambda b_, s: sole if s == 2 and b_ >= pad_from else 'skin', sides=4,
               start=[t2[i], t2[i + 1], b2[i + 1], b2[i]])
        tips.append(p2)
        if claws:
            cl = claw_len * Lt * (0.8 + 0.2 * toe_len[i] / Lmax)
            root_pt = p2 + Vector((0, 0, 0.16 * tip_h)) - d * (0.05 * L)
            claw_tips.append(_claw(B, root_pt, _rot(d, d.cross(Vector((0, 0, -1))), -12), (0, 0, -1), cl,
                                   0.46 * w, 0.74 * tip_h, curve=claw_curve))
    pts = dict(root=(0, 0, 0), ground=(0, reach * 0.4, -H), toe_tips=tips)
    if claw_tips:
        pts['claw_tips'] = claw_tips
    if open_root:
        pts['root_ring'] = [B.P[i] for i in R0]
    return pts


def _bean(i, w, h):
    """Toe section: a rounded top, the widest point at mid height, a narrower flat pad underneath."""
    return [(-0.27 * w, h / 2), (0.27 * w, h / 2), (w / 2, 0.02 * h), (0.33 * w, -h / 2), (-0.33 * w, -h / 2), (-w / 2, 0.02 * h)]


def paw_canine(origin, width=0.08, forward=(0, -1, 0), up=(0, 0, 1), side=1, height=None, toes=4, toe_segs=2,
               claws=True, claw_len=0.70, pads=True, splay=14.0, root=None, open_root=False,
               name='paw', mats=None, colours=None):
    """Dog / wolf / fox / cat paw, on its toes: a narrow wrist that flares into a soft compact
    mound, four rounded toe beans on an arc in front of it (the middle pair ahead), a short blunt
    claw out of the top of each bean, a palm pad and toe pads underneath.

    origin   the wrist / hock end of the leg (centre of the limb's end ring); the ground is `height` below
    width    across the toes (the paw is about 1.15 width long)
    height   root to ground (default 0.8 width: the slanted metacarpus)
    toes     4 (5 gives a cat-like spread); toe_segs 2 = a full bean, 1 = a two-fan bean (10 fewer per toe)
    claws / claw_len (of toe length); pads = the palm pad and the toe pads in the 'pad' slot
    splay    degrees the outer toes turn out; root = (width, depth) of the wrist ring (default
             0.50 x 0.46 width: half the paw, so the wrist taper shows)
    The mound is one shell with the root ring; each toe is its own closed bean sunk into the mound.
    Slots: skin, pad, claw. Attach: root, ground, toe_tips, claw_tips, root_ring (open_root; 6 points).
    Triangles: 184 (4 toes, claws, pads). Lite: toe_segs=1, claws=False gives 104 (92 with pads=False)."""
    W = float(width)
    H = height or 0.80 * W
    rw, rd = root or (0.50 * W, 0.46 * W)
    n = int(toes)
    prof = {4: (0.84, 1.0, 1.0, 0.84), 5: (0.74, 0.92, 1.0, 0.92, 0.74), 3: (0.88, 1.0, 0.88)}.get(n, (1.0,) * n)
    B = _B()

    def oval(w, d, cy, z):
        return B.ring([(w / 2 * math.sin(math.radians(30 + 60 * i)), cy + d / 2 * math.cos(math.radians(30 + 60 * i)), z)
                       for i in range(6)])

    R0 = oval(rw, rd, 0.0, 0.0)
    R1 = oval(0.52 * W + 0.1 * rw, 0.50 * W + 0.1 * rd, 0.01 * W, -0.40 * H)       # the wrist: still narrow
    R2 = oval(0.98 * W, 0.88 * W, 0.04 * W, -0.76 * H)                             # the mound
    R3 = oval(0.86 * W, 0.76 * W, 0.03 * W, -H)
    B.bridge(R0, R1, 'skin')
    B.bridge(R1, R2, 'skin')
    B.bridge(R2, R3, 'skin')
    if not open_root:
        B.cap(R0, 'skin')
    if pads:
        c = Vector((0, -0.05 * W, -H))
        Ri = B.ring([c + (B.P[i] - c) * 0.62 for i in R3])
        B.bridge(R3, Ri, 'skin')
        B.cap(Ri, 'pad')
    else:
        B.cap(R3, 'skin')
    tw, th, Lt = 1.06 * W / n, 0.38 * W, 0.34 * W
    tips, ctips = [], []
    for i in range(n):
        q = (i + 0.5) / n * 2 - 1
        yaw = math.radians(splay * q)
        d = Vector((math.sin(yaw), math.cos(yaw), 0.0))
        L = Lt * prof[i]
        b = Vector((q * 0.5 * W, (0.27 - 0.17 * q * q) * W, -H))          # under the mound's front edge
        c1 = b + d * (0.10 * W + 0.66 * L) + Vector((0, 0, 0.5 * th))     # the bean's fullest section
        tip = b + d * (0.10 * W + L) + Vector((0, 0, 0.30 * th))          # a short steep nose: blunt, not a spike
        slot = lambda b_, s_: 'pad' if pads and s_ == 3 and b_ >= 1 else 'skin'
        if toe_segs >= 2:
            _sweep(B, [b + Vector((0, 0, 0.50 * th)), c1, tip], [(0.84 * tw, 0.80 * th), (tw, th), (0, 0)], (0, 0, 1),
                   slot, end='point', sect=_bean)
        else:                                        # lite: one section, a fan back into the mound and a fan to the nose
            ring = B.ring([c1 + Vector((a * d.y, -a * d.x, h_)) for a, h_ in _bean(0, tw, th)])
            B.fan(ring, B.v(b + Vector((0, 0, 0.5 * th))), 'skin')
            B.fan(ring, B.v(tip), lambda s_: 'pad' if pads and s_ == 3 else 'skin')
        tips.append(tip)
        if claws:
            cr = c1.lerp(tip, 0.50) + Vector((0, 0, 0.10 * th))
            ctips.append(_claw(B, cr, _rot(d, d.cross(Vector((0, 0, -1))), -4), (0, 0, -1),
                               claw_len * Lt * (0.8 + 0.2 * prof[i]), 0.34 * tw, 0.36 * th, curve=40.0))
    pts = dict(root=(0, 0, 0), ground=(0, 0.2 * W, -H), toe_tips=tips)
    if ctips:
        pts['claw_tips'] = ctips
    if open_root:
        pts['root_ring'] = [B.P[i] for i in R0]
    return _finish(B, name, _frame(origin, forward, up), side, mats, colours, pts)


def paw_bear(origin, width=0.13, forward=(0, -1, 0), up=(0, 0, 1), side=1, height=None, toes=5, toe_segs=2,
             claws=True, claw_len=0.85, pads=True, splay=20.0, root=None, open_root=False,
             name='paw', mats=None, colours=None):
    """Bear paw, flat on the ground: a broad long sole with a heel, five short blunt toes in a shallow
    arc and long graded hooks (the middle claw longest). Also a badger, a big cat's forepaw
    (claw_len 0.5), a troll's foot.

    origin / width / height as paw_canine (height default 0.55 width: plantigrade)
    toes 5; claw_len of toe length (bears: long, 0.8-1.0); pads paints the sole; root (width, depth)
    Slots: skin, pad, claw. Attach: root, ground, toe_tips, claw_tips, root_ring (open_root).
    Triangles: 198 (5 toes, arched, claws); 148 without claws; 108 with toe_segs=1 and no claws."""
    W = float(width)
    H = height or 0.55 * W
    prof = {5: (0.80, 0.94, 1.0, 0.94, 0.80), 4: (0.85, 1.0, 1.0, 0.85)}.get(toes, (1.0,) * toes)
    B = _B()
    pts = _foot(B, W, H, heel=0.62 * W, reach=0.56 * W, root=root or (0.66 * W, 0.66 * W), toe_w=(1.0,) * toes,
                toe_len=prof, Lt=0.36 * W, toe_h=0.34 * W, arc=0.13 * W, slant=0.0, splay=splay, instep=0.42,
                toe_segs=toe_segs, pads=pads, claws=claws, claw_len=claw_len, claw_curve=62.0, open_root=open_root)
    return _finish(B, name, _frame(origin, forward, up), side, mats, colours, pts)


def foot_biped(origin, width=0.09, forward=(0, -1, 0), up=(0, 0, 1), side=1, height=None, length=None, toes=3,
               toe_segs=1, claws=False, claw_len=0.5, pads=False, root=None, open_root=False,
               name='foot', mats=None, colours=None):
    """Biped foot: heel behind the ankle, a rising instep, the ball, and a toe block stepped down
    from the instep. toes=3 cuts the block into a big toe (inner side, local +x) and two more;
    toes=1 keeps one block (a shoe or a mitten foot).

    origin   the ankle end of the shin; width = across the ball; height = ankle to ground (0.62 width)
    length   heel to toe tips (default 2.5 width; real feet are about 2.6)
    claws    hooks on the toes (goblin, troll); pads paints the sole
    Slots: skin, pad, claw. Attach: root, ground, toe_tips, claw_tips, root_ring (open_root).
    Triangles: 68 (3 toes); 28 (one block); +10 per claw, +8 per toe with toe_segs=2."""
    W = float(width)
    H = height or 0.62 * W
    Lf = length or 2.5 * W
    tw, prof = {1: ((1.0,), (1.0,)), 2: ((0.5, 0.5), (0.9, 1.0)), 3: ((0.27, 0.31, 0.42), (0.72, 0.86, 1.0)),
                4: ((0.2, 0.22, 0.24, 0.34), (0.66, 0.78, 0.9, 1.0))}.get(toes, ((1.0,) * toes, (1.0,) * toes))
    Lt, heel = 0.20 * Lf, 0.26 * Lf
    reach = Lf - heel - Lt
    B = _B()
    pts = _foot(B, W, H, heel=heel, reach=reach, root=root or (0.60 * W, 0.72 * W), toe_w=tw, toe_len=prof, Lt=Lt,
                toe_h=0.36 * W, arc=0.02 * W, slant=0.07 * W, splay=6.0, instep=0.34, toe_segs=toe_segs, pads=pads,
                claws=claws, claw_len=claw_len, claw_curve=45.0, open_root=open_root, lift=0.10)
    return _finish(B, name, _frame(origin, forward, up), side, mats, colours, pts)


def hoof_cloven(origin, radius=0.028, forward=(0, -1, 0), up=(0, 0, 1), side=1, height=None, width=None,
                length=None, cleft=0.30, dewclaws=True, open_root=False, name='hoof', mats=None, colours=None):
    """Cloven hoof with its fetlock: cannon end, the fetlock joint bulge, a slanted pastern, the
    coronet step, and two toes that split at the coronet and end in two points. Deer, boar, goat, cow.

    origin   the end of the cannon bone (centre of the limb's end ring); radius = its half width
    height   root to ground (default 5.2 radius); width / length = the hoof on the ground
             (defaults 3.1 / 3.9 radius; a deer's is longer and narrower, a boar's shorter)
    cleft    gap between the toe tips, as a fraction of the hoof width
    dewclaws two small hooks behind the fetlock
    Slots: skin (fetlock, pastern), hoof. Attach: root, ground, toe_tips, root_ring (open_root).
    Triangles: 68 with dewclaws, 60 without."""
    rc = float(radius)
    H = height or 5.2 * rc
    W = width or 3.1 * rc
    Lh = length or 3.9 * rc
    B = _B()

    def hexring(w, d, cy, z):
        f = [(-w, cy + d * 0.80, z), (0.0, cy + d * 1.12, z), (w, cy + d * 0.80, z)]
        bk = [(-w, cy - d * 0.80, z), (0.0, cy - d * 1.12, z), (w, cy - d * 0.80, z)]
        return _rows(B, f, bk)

    R0, _, _ = hexring(rc, rc * 0.95, 0.0, 0.0)
    R1, _, _ = hexring(1.22 * rc, 1.30 * rc, -0.22 * rc, -0.24 * H)
    R2, _, _ = hexring(0.94 * rc, 0.92 * rc, 0.42 * rc, -0.52 * H)
    yc = 0.85 * rc
    R3, f3, b3 = hexring(0.41 * W, 0.33 * Lh, yc, -0.71 * H)
    B.bridge(R0, R1, 'skin')
    B.bridge(R1, R2, 'skin')
    B.bridge(R2, R3, 'skin')
    if not open_root:
        B.cap(R0, 'skin')
    tips = []
    g = cleft * W / 2
    for i, sg in ((0, -1), (1, 1)):
        outer_f = (sg * W / 2, yc + 0.30 * Lh, -H)
        inner_f = (sg * g * 0.5, yc + 0.74 * Lh, -H)
        inner_b = (sg * g * 0.35, yc - 0.34 * Lh, -H)
        outer_b = (sg * W * 0.44, yc - 0.34 * Lh, -H)
        quad = [f3[i], f3[i + 1], b3[i + 1], b3[i]]
        low = [outer_f, inner_f, inner_b, outer_b] if sg < 0 else [inner_f, outer_f, outer_b, inner_b]
        ring = B.ring(low)
        B.bridge(quad, ring, 'hoof')
        B.cap(ring, 'hoof')
        tips.append(Vector(inner_f))
    if dewclaws:
        for sg in (-1, 1):
            c = Vector((sg * 0.72 * rc, -1.25 * rc, -0.30 * H))
            s = 0.42 * rc
            base = B.ring([c + Vector((-s, 0.5 * s, 0.5 * s)), c + Vector((s, 0.5 * s, 0.5 * s)), c + Vector((0, 0.9 * s, -1.3 * s))])
            B.cap(base, 'hoof')
            B.fan(base, B.v(c + Vector((sg * 0.25 * s, -1.2 * s, -1.5 * s))), 'hoof')
    pts = dict(root=(0, 0, 0), ground=(0, yc, -H), toe_tips=tips)
    if open_root:
        pts['root_ring'] = [B.P[i] for i in R0]
    return _finish(B, name, _frame(origin, forward, up), side, mats, colours, pts)


def bird_foot(origin, toe_length=0.07, forward=(0, -1, 0), up=(0, 0, 1), side=1, height=None, radius=None,
              spread=34.0, hallux=0.6, talons=True, talon_len=0.42, toe_sides=4, name='birdfoot',
              mats=None, colours=None):
    """Bird foot: a scaled shank widening into the foot knuckle, three forward toes (the middle one
    longest) and one back toe, each arched with a hooked talon. Raptor: talon_len 0.6, spread 40.
    Songbird / raven: defaults. Chicken or wading bird: talon_len 0.25, hallux 0.35.

    origin      the end of the feathered leg (centre of the limb's end ring)
    toe_length  the middle toe; height = root to ground (default 0.9 toe_length); radius = shank half width
    spread      degrees between neighbouring front toes; hallux = back toe length as a fraction (0 = none)
    toe_sides   4 = flat-topped toes, 3 = ridge-topped (saves 4 per toe)
    Slots: scale, claw. Attach: root, ground, toe_tips, claw_tips.
    Triangles: 148 (4 toes, talons); 108 without talons; 124 with toe_sides=3."""
    Lt = float(toe_length)
    H = height or 0.9 * Lt
    r = radius or 0.13 * Lt
    tw, th = 0.26 * Lt, 0.20 * Lt
    B = _B()
    hub = Vector((0, 0, -H + 0.62 * th))
    _sweep(B, [(0, 0, 0), (0, 0.02 * Lt, -0.62 * H), hub + Vector((0, 0, 0.25 * th)), (0, 0, -H + 0.05 * th)],
           [(2 * r, 2 * r), (1.8 * r, 1.8 * r), (1.5 * tw, 1.5 * tw), (1.15 * tw, 1.15 * tw)], (0, 1, 0), 'scale')
    toes = [(-spread, 0.84), (0.0, 1.0), (spread, 0.84)] + ([(180.0, hallux)] if hallux > 0 else [])
    tips, ctips = [], []
    for yaw, f in toes:
        d = _rot((0, 1, 0), (0, 0, -1), yaw)
        L = Lt * f
        p0 = Vector((0, 0, -H + th / 2))
        p1 = p0 + d * (0.50 * L) + Vector((0, 0, 0.30 * th))
        p2 = p0 + d * L + Vector((0, 0, -0.14 * th))
        _sweep(B, [p0, p1, p2], [(tw, th), (0.86 * tw, 0.95 * th), (0.62 * tw, 0.72 * th)], (0, 0, 1), 'scale',
               sides=toe_sides)
        tips.append(p2)
        if talons:
            ctips.append(_claw(B, p2 + Vector((0, 0, 0.06 * th)), _rot(d, d.cross(Vector((0, 0, -1))), -18), (0, 0, -1),
                               talon_len * Lt * (0.8 + 0.2 * f), 0.36 * tw, 0.62 * th, curve=70.0))
    pts = dict(root=(0, 0, 0), ground=(0, 0, -H), toe_tips=tips)
    if ctips:
        pts['claw_tips'] = ctips
    return _finish(B, name, _frame(origin, forward, up), side, mats, colours, pts)


# =============================================================================
# HANDS
# =============================================================================
def _hand(B, W, T, palm, finger_w, finger_len, Lf, curl, spread, thumb, thumb_len, thumb_curl, wrist, knuckle,
          claw_len, open_root):
    """Wrist ring at the origin; +y to the fingertips, +z the back of the hand, the thumb on +x.
    One shell: palm, each finger extruded from its own knuckle quad, the thumb from the palm's side quad."""
    n = len(finger_w)
    xs = _bounds(finger_w, W)
    u = [2 * x / W for x in xs]
    ww, wt = wrist
    R0, t0, b0 = _rows(B, [(x * ww / W, 0.0, wt / 2 * math.sqrt(1 - 0.4 * q * q)) for x, q in zip(xs, u)],
                       [(x * ww / W, 0.0, -wt / 2 * math.sqrt(1 - 0.4 * q * q)) for x, q in zip(xs, u)])
    R1, t1, b1 = _rows(B, [(x, 0.50 * palm, T / 2) for x in xs], [(x, 0.50 * palm, -T / 2) for x in xs])
    yk = [palm + 0.07 * W * (1 - q * q) for q in u]
    R2, t2, b2 = _rows(B, [(x, y, T / 2 + knuckle) for x, y in zip(xs, yk)], [(x, y, -T / 2) for x, y in zip(xs, yk)])
    B.bridge(R0, R1, 'skin', skip=(n,) if thumb is True else ())
    B.bridge(R1, R2, 'skin')
    if not open_root:
        B.cap(R0, 'skin')
    tips, ctips = [], []
    Lmax = max(finger_len)
    h0 = T + knuckle
    th1 = 8 + 80 * curl
    th2 = th1 + 14 + 78 * curl
    for i in range(n):
        w = xs[i + 1] - xs[i]
        cx = (xs[i] + xs[i + 1]) / 2
        yaw = math.radians(spread * (1 - curl) * 2 * cx / W)
        dy = Vector((math.sin(yaw), math.cos(yaw), 0.0))
        dirv = lambda deg: dy * math.cos(math.radians(deg)) - Vector((0, 0, 1)) * math.sin(math.radians(deg))
        L = Lf * finger_len[i] / Lmax
        fk = 1 - 0.30 * curl                         # a curled finger is drawn thinner: the two mitres need room
        la = 0.55 * L * (1 - curl) + (0.56 * T + 0.30 * fk * h0 + knuckle / 2) * curl
        lb = 0.45 * L * (1 - 0.30 * curl)
        c0 = Vector((cx, (yk[i] + yk[i + 1]) / 2, knuckle / 2))
        a0 = c0 + dy * (max(0.30 * T, 0.17 * w) + 0.36 * fk * h0 * math.tan(math.radians(th1 / 2)) + 0.30 * T * curl)
        p1 = a0 + dirv(th1) * la
        p2 = p1 + dirv(th2) * lb
        _sweep(B, [c0, a0, p1, p2], [(w, h0), (0.86 * w, 0.70 * fk * h0), (0.78 * w, 0.60 * fk * h0), (0.56 * w, 0.42 * h0)],
               (0, 0, 1), 'skin', start=[t2[i], t2[i + 1], b2[i + 1], b2[i]])
        tips.append(p2)
        if i == n - 1:                               # the index finger: where a wrapped thumb lies
            wrap_y, wrap_z = max(a0.y, p1.y) + 0.30 * fk * h0, a0.z + (p1.z - a0.z) * 0.62
        if claw_len > 0:
            dd = dirv(th2)
            ctips.append(_claw(B, p2 - dd * (0.04 * L), dd, dirv(th2 + 90), claw_len * L,
                               0.42 * w, 0.40 * h0, curve=35.0))
    pts = dict(root=(0, 0, 0), palm=(0, 0.55 * palm, -T / 2), finger_tips=tips, grip=(0, 0.75 * palm, -T))
    if thumb == 'wrap':
        # a fist: the thumb is its own closed shell, rooted in the heel of the palm, running up the
        # index side and folded ACROSS the front of the curled fingers, pressed into them (no gap)
        tw = 0.30 * W
        dep = 0.74 * tw
        yt = wrap_y + 0.06 * dep
        q = [Vector((W / 2 - 0.30 * tw, 0.30 * palm, -0.10 * T)), Vector((W / 2 + 0.24 * tw, 0.66 * palm, 0.55 * wrap_z)),
             Vector((W / 2 + 0.16 * tw, yt, wrap_z)), Vector((W / 2 - 0.60 * W, yt - 0.03 * W, wrap_z - 0.04 * T))]
        _sweep(B, q, [(0.90 * tw, 0.90 * tw), (0.95 * tw, tw), (0.84 * tw, 0.92 * tw), (0.52 * dep, 0.52 * tw)],
               (0, 0, 1), 'skin')
        pts['thumb_tip'] = q[3]
    elif thumb:
        tw, tt = 0.27 * W, 0.72 * T
        c0 = B.centre([t1[n], t0[n], b0[n], b1[n]])
        a = 60 + 26 * thumb_curl
        drop = 0.22 + 0.5 * thumb_curl
        d1 = Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), -drop)).normalized()
        d2 = Vector((math.cos(math.radians(a + 24)), math.sin(math.radians(a + 24)), -drop - 0.25 - 0.3 * thumb_curl)).normalized()
        p1 = Vector((W / 2 + 0.5 * tw + 0.04 * W, c0.y + 0.08 * palm, c0.z - 0.04 * T))
        p2 = p1 + d1 * (0.55 * thumb_len)
        p3 = p2 + d2 * (0.45 * thumb_len)
        _sweep(B, [c0, p1, p2, p3], [(tw, tt), (0.92 * tw, 0.90 * tt), (0.80 * tw, 0.80 * tt), (0.58 * tw, 0.56 * tt)],
               (0, 0, 1), 'skin', start=[t1[n], t0[n], b0[n], b1[n]])
        pts['thumb_tip'] = p3
        if claw_len > 0:
            ctips.append(_claw(B, p3 - d2 * (0.04 * thumb_len), d2, (0, 0, -1), claw_len * thumb_len, 0.40 * tw,
                               0.40 * tt, curve=35.0))
    if ctips:
        pts['claw_tips'] = ctips
    if open_root:
        pts['root_ring'] = [B.P[i] for i in R0]
    return pts


def hand_three_finger(origin, width=0.09, forward=(0, -1, 0), up=(0, 0, 1), side=1, fingers=3, curl=0.12,
                      spread=13.0, finger_len=1.0, thumb=True, thumb_curl=0.0, knuckle=0.10, claw_len=0.0,
                      wrist=None, open_root=False, name='hand', mats=None, colours=None):
    """Stylised hand: a palm, a stepped knuckle row, three thick two-joint fingers and an opposed thumb.

    origin     the wrist end of the forearm; forward = wrist to fingertips; up = the back of the hand
    width      across the knuckles. Palm length 0.85 width, fingers `finger_len` x width (real: about 0.9)
    side       +1 left hand (thumb on local +x: toward the body's front in a palm-down A-pose), -1 right
    fingers    3 (4 gives a human hand, 2 a claw hand); curl 0 flat .. 1 fist; spread = fan degrees
    thumb / thumb_curl ; knuckle = knuckle step as a fraction of palm thickness
    claw_len   > 0 puts a hook on every fingertip (goblin, troll, raptor arm)
    wrist      (width, thickness) of the root ring (default 0.62 width, 0.9 palm thickness)
    Slots: skin, claw. Attach: root, palm, grip, finger_tips, thumb_tip, claw_tips, root_ring (open_root).
    Triangles: 140 (3 fingers and thumb); 176 (4 fingers); 180 (3 fingers, claws)."""
    W = float(width)
    T = 0.34 * W
    prof = {3: (0.88, 1.0, 0.93), 4: (0.78, 0.94, 1.0, 0.92), 2: (0.95, 1.0)}.get(fingers, (1.0,) * fingers)
    B = _B()
    pts = _hand(B, W, T, 0.85 * W, (1.0,) * fingers, prof, finger_len * W, curl, spread, thumb, 0.62 * W, thumb_curl,
                wrist or (0.62 * W, 0.90 * T), knuckle * T, claw_len, open_root)
    return _finish(B, name, _frame(origin, forward, up), side, mats, colours, pts)


def hand_mitten(origin, width=0.09, forward=(0, -1, 0), up=(0, 0, 1), side=1, curl=0.15, finger_len=0.85,
                thumb_curl=0.0, knuckle=0.10, wrist=None, open_root=False, name='hand', mats=None, colours=None):
    """Mitten hand for a toon character: a soft palm with bevelled sides, one broad finger slab
    that bends at two joints and narrows in three steps to a rounded tip, and a thick separate
    thumb standing off the palm at an angle (the notch between thumb and slab is what reads as a hand).

    Parameters as hand_three_finger (no finger count, no claws). curl 0 flat .. 0.7 cupped;
    thumb_curl 0 open .. 1 folded toward the palm.
    The mitten is one shell with the root ring; the thumb is its own closed shell rooted in the palm.
    Slots: skin. Attach: root, palm, grip, finger_tips, thumb_tip, root_ring (open_root; 6 points).
    Triangles: 96."""
    W = float(width)
    T = 0.36 * W
    palm, Lf = 0.85 * W, finger_len * W
    ww, wt = wrist or (0.62 * W, 0.90 * T)
    c = min(max(curl, 0.0), 0.8)
    kn = knuckle * T
    B = _B()
    hexs = lambda i, w, h: [(-0.33 * w, h / 2), (0.33 * w, h / 2), (w / 2, 0.0), (0.33 * w, -h / 2), (-0.33 * w, -h / 2), (-w / 2, 0.0)]
    dirv = lambda deg: Vector((0, math.cos(math.radians(deg)), -math.sin(math.radians(deg))))
    th1 = 6 + 62 * c
    th2 = th1 + 12 + 56 * c
    th3 = th2 + 10 + 24 * c
    P = [Vector((0, 0, 0)), Vector((0, 0.48 * palm, 0)), Vector((0, palm, kn / 2))]
    P.append(P[2] + dirv(th1) * (0.48 * Lf))
    P.append(P[3] + dirv(th2) * (0.36 * Lf))
    P.append(P[4] + dirv(th3) * (0.16 * Lf))
    S = [(ww, wt), (1.0 * W, T), (1.04 * W, T + kn), (0.98 * W, 0.80 * T), (0.80 * W, 0.64 * T), (0.46 * W, 0.42 * T)]
    rings = _sweep(B, P, S, (0, 0, 1), 'skin', cap0=not open_root, sect=hexs)
    tw, tt, tl = 0.34 * W, 0.86 * T, 0.60 * W
    a1 = math.radians(50 - 20 * thumb_curl)
    a2 = math.radians(28 - 46 * thumb_curl)
    d1 = Vector((math.sin(a1), math.cos(a1), -0.12 - 0.30 * thumb_curl)).normalized()
    d2 = Vector((math.sin(a2), math.cos(a2), -0.20 - 0.60 * thumb_curl)).normalized()
    q0 = Vector((W / 2 - 0.62 * tw, 0.24 * palm, -0.05 * T))
    q1 = q0 + d1 * (0.62 * tw + 0.46 * tl)
    q2 = q1 + d2 * (0.38 * tl)
    q3 = q2 + d2 * (0.16 * tl)
    _sweep(B, [q0, q1, q2, q3], [(0.95 * tw, 0.95 * tt), (tw, tt), (0.84 * tw, 0.82 * tt), (0.48 * tw, 0.48 * tt)],
           (0, 0, 1), 'skin')
    pts = dict(root=(0, 0, 0), palm=(0, 0.55 * palm, -T / 2), finger_tips=[P[5]], grip=(0, 0.75 * palm, -T), thumb_tip=q3)
    if open_root:
        pts['root_ring'] = [B.P[i] for i in rings[0]]
    return _finish(B, name, _frame(origin, forward, up), side, mats, colours, pts)


def fist(origin, width=0.09, forward=(0, -1, 0), up=(0, 0, 1), side=1, fingers=3, knuckle=0.22, wrist=None,
         open_root=False, name='fist', mats=None, colours=None):
    """A closed fist: the hand curled shut. The knuckle row stands above the back of the hand (the
    knuckle step), the fingers fold down the front and back underneath, and the thumb runs up the
    index side and wraps ACROSS the front of the index and middle fingers, pressed into them.
    For a punch, a grip on a club (attach 'grip'), a giant's resting hand.

    Parameters as hand_three_finger. The thumb is its own closed shell (it has to lie in the fingers).
    Slots: skin. Attach: root, palm, grip, finger_tips, thumb_tip, root_ring (open_root).
    Triangles: 144 (3 fingers), 180 (4)."""
    W = float(width)
    T = 0.40 * W
    prof = {3: (0.94, 1.0, 0.96), 4: (0.9, 0.98, 1.0, 0.95)}.get(fingers, (1.0,) * fingers)
    B = _B()
    pts = _hand(B, W, T, 0.82 * W, (1.0,) * fingers, prof, 1.0 * W, 1.0, 0.0, 'wrap', 0.62 * W, 1.0,
                wrist or (0.64 * W, 0.92 * T), knuckle * T, 0.0, open_root)
    return _finish(B, name, _frame(origin, forward, up), side, mats, colours, pts)


# =============================================================================
# EARS
# =============================================================================
EAR_OUTLINES = dict(
    round=[(-0.34, -0.16), (-0.52, 0.36), (-0.34, 0.84), (0.0, 1.0), (0.34, 0.84), (0.52, 0.36), (0.34, -0.16)],
    pointed=[(-0.32, -0.16), (-0.50, 0.26), (-0.26, 0.70), (0.06, 1.0), (0.26, 0.66), (0.46, 0.26), (0.32, -0.16)],
    leaf=[(-0.22, -0.12), (-0.50, 0.20), (-0.40, 0.56), (-0.02, 1.0), (0.34, 0.54), (0.46, 0.20), (0.22, -0.12)])


def ear_cup(base, length=0.07, width=None, forward=(0, -1, 0), up=(0, 0, 1), side=1, kind='round', cup=0.22,
            thickness=0.16, inner=0.30, name='ear', mats=None, colours=None):
    """A cupped ear with real thickness: a rim, a sunken inner face in its own colour, a solid back.

    base       where the ear leaves the skull; up = the ear's own axis (base to tip); forward = the
               way the cup opens. The lowest 0.16 of the length is the buried root
    kind       'round' (bear, mouse, lion), 'pointed' (wolf, fox, cat), 'leaf' (goblin, deer, donkey:
               long, tip swept toward local -x: pass width about 0.5 length)
    width      default 0.95 length (round), 0.8 (pointed), 0.55 (leaf)
    cup        how far the side edges curl forward, as a fraction of width
    thickness  back to rim, as a fraction of width; inner = width of the rim band (0..1)
    Slots: ear, ear_inner. Attach: base, tip.
    Triangles: 38."""
    L = float(length)
    W = width or L * dict(round=0.95, pointed=0.80, leaf=0.55)[kind]
    out = EAR_OUTLINES[kind]
    cz = 0.40
    B = _B()
    F = B.ring([(x * W, cup * W * (2 * x) ** 2, z * L) for x, z in out])
    I = B.ring([(x * (1 - inner) * W, -0.30 * thickness * W, (cz + (z - cz) * (1 - inner * (1.25 if z < cz else 1.0))) * L)
                for x, z in out])
    K = B.ring([(x * 0.72 * W, -thickness * W, (cz + (z - cz) * 0.84) * L) for x, z in out])
    B.bridge(F, I, 'ear')
    B.cap(I, 'ear_inner')
    B.bridge(F, K, 'ear')
    B.cap(K, 'ear')
    tip = max(out, key=lambda p: p[1])
    return _finish(B, name, _frame(base, forward, up), side, mats, colours,
                   dict(base=(0, 0, 0), tip=(tip[0] * W, 0, tip[1] * L)))


# =============================================================================
# HORNS, ANTLERS, TUSKS
# =============================================================================
def _arc_points(L, segs, curve, spiral, bury):
    """Local frame: grows along +y, bends toward +z, spirals out along +x."""
    pts = [Vector((0, -bury * L, 0))]
    p = Vector((0, 0, 0))
    dirs = []
    for j in range(segs):
        d = _rot((0, 1, 0), (1, 0, 0), curve * (j + 0.5) / segs)
        d = _rot(d, (0, 1, 0), -spiral * (j + 0.5) / segs)
        if j == 0:
            pts.append(p.copy())
        p = p + d * (L / segs)
        pts.append(p.copy())
        dirs.append(d)
    return pts, dirs


def horn(base, length=0.12, radius=None, forward=(0, 0, 1), up=(0, 1, 0), side=1, curve=70.0, spiral=0.0, segs=4,
         sides=5, ridges=False, taper=1.0, tip_from=0.6, name='horn', mats=None, colours=None):
    """A tapered horn swept along an arc.

    base     where the horn leaves the skull (the root is buried 0.15 length below it)
    forward  the way it starts to grow; up = the way it bends; curve = total bend in degrees
    spiral   degrees it winds out of that plane toward local +x (a ram: curve 250, spiral 60, segs 7)
    radius   at the base (default 0.16 length: thick; a thin horn reads as a nail)
    segs / sides  arc segments and section sides (5 = faceted round, 4 = square, 3 = blade)
    ridges   growth rings: every station steps out and back in (ram, ibex, goat)
    taper    > 1 keeps the horn thick for longer; tip_from = where the 'horn_tip' colour starts (1 = never)
    Slots: horn, horn_tip. Attach: base, tip.
    Triangles: 48 (5 sides, 4 segs); 78 with ridges; 22 as a 4-sided 2-segment spike."""
    L = float(length)
    r0 = radius or 0.16 * L
    pts, dirs = _arc_points(L, segs, curve, spiral, 0.15)
    rad = lambda t: r0 * max(max(1 - t, 0.0) ** (1.0 / taper), 0.24)
    P, S, tt = [pts[0], pts[1]], [(2 * r0, 2 * r0), (2 * r0, 2 * r0)], [0.0, 0.0]
    for j in range(1, segs):
        t = j / segs
        if ridges:
            P.append(pts[j + 1] - dirs[j - 1] * (0.34 * L / segs)); S.append((2.3 * rad(t), 2.3 * rad(t))); tt.append(t)
        P.append(pts[j + 1]); S.append((2 * rad(t), 2 * rad(t))); tt.append(t)
    P.append(pts[-1]); tt.append(1.0)
    B = _B()
    _sweep(B, P, S + [(0, 0)], (0, 0, 1), lambda b_, s: 'horn_tip' if tt[min(b_, len(tt) - 1)] >= tip_from else 'horn',
           sides=sides, end='point')
    return _finish(B, name, _frame(base, forward, up), side, mats, colours, dict(base=(0, 0, 0), tip=pts[-1]))


def tusk(base, length=0.07, radius=None, forward=(0, -1, 0), up=(0, 0, 1), side=1, curve=60.0, segs=3, sides=4,
         name='tusk', mats=None, colours=None):
    """A short thick tusk or fang: a horn with a blunt taper and a square section, bending toward `up`.
    Boar: forward = out and forward from the lip, up = (0, 0, 1). Sabre fang: forward down, curve 25.

    radius default 0.15 length. Slots: tooth. Attach: base, tip. Triangles: 15."""
    L = float(length)
    r0 = radius or 0.15 * L
    pts, _ = _arc_points(L, segs, curve, 0.0, 0.2)
    S = [(2 * r0, 2 * r0)] * 2 + [(2 * r0 * (1 - j / segs) ** 0.55,) * 2 for j in range(1, segs)] + [(0, 0)]
    B = _B()
    _sweep(B, pts, S, (0, 0, 1), 'tooth', sides=sides, end='point',
           sect=lambda i, w, h: [(0.0, h / 2), (w / 2, 0.0), (0.0, -h / 2), (-w / 2, 0.0)] if sides == 4 else _sect(sides, w, h))
    return _finish(B, name, _frame(base, forward, up), side, mats, colours, dict(base=(0, 0, 0), tip=pts[-1]))


ANTLER_TINES = dict(          # (position along the beam 0..1, length / beam length, degrees off the beam)
    stag=[(0.10, 0.46, 72.0), (0.32, 0.30, 66.0), (0.55, 0.36, 60.0), (0.80, 0.28, 44.0)],
    young=[(0.14, 0.36, 68.0), (0.68, 0.30, 46.0)],
    elk=[(0.08, 0.48, 74.0), (0.24, 0.40, 68.0), (0.42, 0.30, 64.0), (0.60, 0.40, 58.0), (0.82, 0.28, 44.0)])


def antler_beam(base, length=0.22, radius=None, forward=(0, 0.45, 1), up=(0, -1, 0.3), side=1, curve=62.0,
                spiral=14.0, tines='stag', fan=12.0, tine_sides=3, tine_segs=2, segs=5, name='antler',
                mats=None, colours=None):
    """One antler: a main beam that sweeps back, curves up-forward (most of the bend low down, the
    top nearly straight) and thins to under half its base, with tines on its front side. Each tine
    leaves the beam through a flared root, heads forward and then turns up along the beam; the
    brow tine is the longest, the rest grade down, and the last one forks with the beam's own tip.

    base     the pedicle on the skull; forward = the way the beam starts (up and back);
             up = the side the beam curls toward and the tines grow from (the creature's front)
    length   of the beam; radius at the base (default 0.085 length: a beam, not a rod)
    curve / spiral   beam bend toward `up`, and lean out toward local +x
    tines    'stag' | 'young' | 'elk', or a list of (position 0..1, length / beam length, degrees off the beam)
    fan      degrees alternate tines lean out of the beam's plane
    tine_sides 3 (ridge-fronted) or 4; tine_segs 2 = curved tines, 1 = straight spikes (6 fewer each)
    Slots: antler, horn_tip (the outer part of every tine). Attach: base, tip, tine_tips.
    Triangles: 110 (stag, 4 tines); 78 (young); 126 (elk). Lite: tine_segs=1 gives 86 / 66 / 96."""
    L = float(length)
    r0 = radius or 0.085 * L
    spec = ANTLER_TINES[tines] if isinstance(tines, str) else list(tines)
    bend = lambda u_: u_ ** 0.62                     # most of the curve in the lower beam
    pts, dirs = [Vector((0, -0.12 * L, 0)), Vector((0, 0, 0))], []
    p = Vector((0, 0, 0))
    for j in range(segs):
        m = (bend(j / segs) + bend((j + 1) / segs)) / 2
        d = _rot((0, 1, 0), (1, 0, 0), curve * m)
        d = _rot(d, (0, 1, 0), -spiral * (j + 0.5) / segs)
        p = p + d * (L / segs)
        pts.append(p.copy())
        dirs.append(d)
    rad = lambda t: r0 * (1 - 0.60 * t)
    diamond = lambda i, w, h: [(0.0, h / 2), (w / 2, 0.0), (0.0, -h / 2), (-w / 2, 0.0)]
    B = _B()
    S = [(2 * r0, 2 * r0)] * 2 + [(2 * rad(j / segs),) * 2 for j in range(1, segs)] + [(0, 0)]
    _sweep(B, pts, S, (0, 0, 1), lambda b_, s: 'horn_tip' if b_ >= segs - 1 else 'antler', end='point', sect=diamond)
    tips = []
    for q, (t, fl, ang) in enumerate(spec):
        x = t * segs
        j = min(int(x), segs - 1)
        c = pts[j + 1].lerp(pts[j + 2], x - j)
        tan = dirs[j]
        front = Vector((0, 0, 1)) - tan * tan.z
        front.normalize()
        axis = tan.cross(front)
        d1 = _rot(_rot(tan, axis, ang), tan, fan * (1 if q % 2 else -1))
        rt = 0.66 * rad(t)
        tl = fl * L
        if tine_segs >= 2:
            d2 = _rot(d1, d1.cross(tan), 0.42 * ang)                 # the outer half turns up along the beam
            p1 = c + d1 * (0.50 * tl)
            P = [c - d1 * (0.3 * rt), c + d1 * min(rad(t) + 0.10 * tl, 0.34 * tl), p1, p1 + d2 * (0.50 * tl)]
            S = [(2.3 * rt, 2.3 * rt), (1.9 * rt, 1.9 * rt), (1.35 * rt, 1.35 * rt), (0, 0)]
        else:
            P = [c - d1 * (0.3 * rt), c + d1 * (0.45 * tl), c + (d1 + tan * 0.35).normalized() * tl]
            S = [(2.6 * rt, 2.4 * rt), (1.5 * rt, 1.5 * rt), (0, 0)]
        nb = len(P) - 2
        _sweep(B, P, S, tan, lambda b_, s: 'horn_tip' if b_ >= nb else 'antler', sides=tine_sides, end='point')
        tips.append(P[-1])
    return _finish(B, name, _frame(base, forward, up), side, mats, colours,
                   dict(base=(0, 0, 0), tip=pts[-1], tine_tips=tips))


# =============================================================================
# TEETH, NOSE
# =============================================================================
TOOTH_PROFILES = dict(predator=(0.55, 0.62, 1.6, 0.6, 0.75, 0.85, 0.7), even=(1.0,), jagged=(1.0, 0.6),
                      tusked=(0.6, 0.6, 0.7, 1.9, 0.7))


def tooth_row(start, end, out=(0, -1, 0), up=(0, 0, 1), n=6, height=0.012, bulge=0.25, profile='predator',
              gum=True, lean=0.15, name='teeth', mats=None, colours=None):
    """A row of wedge teeth on a gum strip, along a jaw arc.

    start, end  the two ends of the row on the jaw (world); out = the way the arc bows (and the teeth
                face); up = the way the teeth point (down for the upper jaw)
    n           teeth; height = an ordinary tooth (the profile scales each one)
    bulge       how far the arc bows out, as a fraction of the row length (0 = straight)
    profile     'predator' (small incisors, a big canine third from `start`, cheek teeth), 'even',
                'jagged' (alternating), 'tusked', or a list of scales repeated along the row
    gum         the strip the teeth stand in (bury it in the lip line); lean tilts the tips back in
    Teeth are four-sided pyramids at most 1.9 times as tall as their base (a big tooth takes a wider base): wedges, not needles.
    Slots: tooth, gum. Attach: start, end, tooth_tips.
    Triangles: 6 per tooth + 20 for a straight gum, 28-68 for a bowed one (bulge 0.28: 44); 7 teeth, straight: 62."""
    A, E = Vector(start), Vector(end)
    o = Vector(out).normalized()
    upv = Vector(up).normalized()
    chord = (E - A).length
    C = (A + E) / 2 + o * (2 * bulge * chord)
    pos = lambda t: A * (1 - t) ** 2 + C * (2 * t * (1 - t)) + E * t * t
    tan = lambda t: ((C - A) * (2 * (1 - t)) + (E - C) * (2 * t)).normalized()
    prof = TOOTH_PROFILES[profile] if isinstance(profile, str) else tuple(profile)
    sp = chord * (1 + 2.2 * bulge * bulge) / n
    B = _B()
    gh, gd = 0.9 * height, 0.80 * sp
    if gum:
        # the strip is built from sections square to the arc at each station (no mitre, so no kink),
        # and a bowed row gets enough stations to turn about 20 degrees at each
        ng = 2 if bulge < 0.04 else max(3, min(8, int(math.ceil(abs(bulge) * 16))))
        gr = []
        for q in range(ng + 1):
            t = q / ng
            tg = tan(t)
            nr = tg.cross(upv).normalized()
            if nr.dot(o) < 0:
                nr = -nr
            c = pos(t) - upv * (gh / 2) + tg * (0.3 * sp * (-1 if q == 0 else 1 if q == ng else 0))
            gr.append(B.ring([c + nr * (gd / 2) + upv * (gh / 2), c - nr * (gd / 2) + upv * (gh / 2),
                              c - nr * (gd / 2) - upv * (gh / 2), c + nr * (gd / 2) - upv * (gh / 2)]))
        for q in range(ng):
            B.bridge(gr[q], gr[q + 1], 'gum')
        B.cap(gr[0], 'gum')
        B.cap(gr[-1], 'gum')
    tips = []
    for i in range(n):
        t = (i + 0.5) / n
        s = prof[i % len(prof)]
        w = min(1.45 * sp, max(0.62 * sp, height * s / 1.9))
        h = min(height * s, 1.9 * w)
        dp = min(gd * 0.9, w)
        tg = tan(t)
        nrm = tg.cross(upv).normalized()
        if nrm.dot(o) < 0:
            nrm = -nrm
        c = pos(t) - upv * (0.35 * height)
        base = B.ring([c - tg * (w / 2) + nrm * (dp / 2), c + tg * (w / 2) + nrm * (dp / 2),
                       c + tg * (w / 2) - nrm * (dp / 2), c - tg * (w / 2) - nrm * (dp / 2)])
        tipp = pos(t) + upv * h - nrm * (lean * h)
        B.cap(base, 'tooth')
        B.fan(base, B.v(tipp), 'tooth')
        tips.append(tipp)
    return _finish(B, name, Matrix.Identity(4), 1, mats, colours, dict(start=A, end=E, tooth_tips=tips))


NOSE_OUTLINES = dict(
    canine=[(-0.36, 0.30), (0.36, 0.30), (0.52, 0.06), (0.20, -0.40), (-0.20, -0.40), (-0.52, 0.06)],
    bear=[(-0.40, 0.36), (0.40, 0.36), (0.52, 0.02), (0.26, -0.38), (-0.26, -0.38), (-0.52, 0.02)],
    button=[(-0.30, 0.26), (0.30, 0.26), (0.50, 0.02), (0.16, -0.34), (-0.16, -0.34), (-0.50, 0.02)])


def nose_pad(center, width=0.04, forward=(0, -1, 0), up=(0, 0, 1), kind='canine', depth=None, nostrils=True,
             name='nose', mats=None, colours=None):
    """The nose leather at the tip of a muzzle.

    center   the point on the muzzle tip the nose grows from; forward = the muzzle's direction
    kind     'canine' (wolf, fox, dog: a broad top narrowing to the lip), 'bear' (bigger, squarer),
             'button' (a small toon nose, no nostrils), 'pig' (a flat oval snout disc, two nostrils)
    width    across; depth = how far it stands off the muzzle (default 0.5 width; pig 0.3)
    nostrils two dark facets cut into the lower front planes (pig: two sunken ovals)
    Slots: nose, nostril. Attach: center, tip.
    Triangles: canine / bear 48 (32 without nostrils), button 32, pig 68."""
    W = float(width)
    B = _B()
    if kind == 'pig':
        D = depth or 0.30 * W
        n = 8
        ell = lambda s, y: [(s * 0.5 * W * math.cos(2 * math.pi * i / n + math.pi / n), y,
                             s * 0.41 * W * math.sin(2 * math.pi * i / n + math.pi / n)) for i in range(n)]
        R = [B.ring(ell(1.0, -0.35 * D)), B.ring(ell(1.0, 0.8 * D)), B.ring(ell(0.80, D))]
        B.cap(R[0], 'nose')
        B.bridge(R[0], R[1], 'nose')
        B.bridge(R[1], R[2], 'nose')
        B.cap(R[2], 'nose')
        if nostrils:
            for sg in (-1, 1):
                c = Vector((sg * 0.17 * W, D, 0.02 * W))
                ring = lambda s, y: [c + Vector((sg * s * 0.07 * W * a, y, s * 0.12 * W * b_))
                                     for a, b_ in ((0, 1), (1, 0.2), (0.6, -1), (-0.8, -0.3))]
                r0, r1 = B.ring(ring(1.0, -0.3 * D)), B.ring(ring(1.0, 0.035 * W))
                B.cap(r0, 'nostril')
                B.bridge(r0, r1, 'nostril')
                B.cap(r1, 'nostril')
        return _finish(B, name, _frame(center, forward, up), 1, mats, colours, dict(center=(0, 0, 0), tip=(0, D, 0)))
    out = NOSE_OUTLINES[kind]
    D = depth or 0.5 * W
    ring = lambda s, y, dz=0.0: [(x * s * W, y, (z * s + dz) * W) for x, z in out]
    if kind == 'button':
        R = [B.ring(ring(1.0, -0.35 * D)), B.ring(ring(0.92, 0.55 * D)), B.ring(ring(0.50, D, 0.03))]
    else:
        R = [B.ring(ring(1.04, -0.40 * D)), B.ring(ring(1.0, 0.50 * D)), B.ring(ring(0.60, D, 0.02))]
    B.cap(R[0], 'nose')
    B.bridge(R[0], R[1], 'nose')
    first = len(B.F)
    B.bridge(R[1], R[2], 'nose')
    B.cap(R[2], 'nose')
    if nostrils and kind != 'button':
        for q, sg in ((2, 1), (4, -1)):          # the two lower front bevels
            B.inset(first + q, 0.58, 0.05 * W, (sg * 0.6, 0.7, -0.4), 'nose', 'nostril')
    return _finish(B, name, _frame(center, forward, up), 1, mats, colours, dict(center=(0, 0, 0), tip=(0, D, 0)))


# =============================================================================
# FUR: stepped clumps (mass, never cards)
# =============================================================================
_FUR_VARY = (0.0, 0.80, 0.30, 1.0, 0.50, 0.90, 0.15, 0.65)


def fur_clump(base, length=0.08, width=None, forward=(0, 1, 0), up=(0, 0, 1), side=1, n=5, radius=None,
              thickness=0.50, hook=0.12, lean=0.0, fan=16.0, vary=0.30, name='clump', mats=None, colours=None):
    """A fur tuft as `n` LARGE overlapping locks (5-7 for a ruff, a mane patch, a crest, a cheek
    tuft; n=1 for one lock). Every lock is a closed, chunky wedge (a ridge down its back, a flat
    belly, three stations so it arcs) with its root buried under the skin. The locks are combed one
    way and laid like shingles in two staggered rows: the rear row rides over the roots of the front
    row; lengths vary lock to lock and the outer locks fan out a little. Volumes, never cards.

    base       the middle of the tuft's root line on the skin; forward = the way the fur is combed;
               up = the skin's outward normal there
    length     of the longest lock; width = across the whole tuft (default 0.5 length for one lock,
               about 0.36 length per lock in the wider row)
    radius     the body's radius of curvature under the tuft: the locks then wrap a sphere of that
               radius, so the tuft hugs a skull, a neck or a rump instead of standing off it (None = flat)
    thickness  of a lock, as a fraction of its width (never thinner than 0.35)
    hook       how far the tips lift off the skin, as a fraction of length (0 = lying flat)
    lean       swings every tip sideways toward local +x (fraction of length); fan = degrees the
               outermost locks turn out; vary 0..0.5 = how much the lock lengths differ
    Slots: fur, fur_tip (the last third of each lock). Attach: base, tip (the longest lock), tips.
    Triangles: 16 per lock: 80 (n=5), 112 (n=7), 16 (n=1)."""
    L = float(length)
    n = max(1, int(n))
    rows = [n] if n <= 2 else [(n + 1) // 2, n // 2]
    m0 = max(rows)
    Wp = width or (0.5 * L if n == 1 else 0.36 * L * (0.72 * m0 + 0.28))
    w = Wp / (0.72 * m0 + 0.28)
    T = max(thickness, 0.35) * w
    R = float(radius) if radius else None
    B = _B()
    ridge = lambda i, ww, hh: [(0.0, 0.62 * hh), (ww / 2, -0.38 * hh), (-ww / 2, -0.38 * hh)]

    def wrap(x, y, h):
        """Flat tuft coordinates (across, along the comb, height off the skin) -> local point, and the skin normal."""
        if R is None:
            return Vector((x, y, h)), Vector((0, 0, 1))
        r = math.hypot(x, y)
        if r < 1e-9:
            return Vector((0, 0, h)), Vector((0, 0, 1))
        a = min(r / R, 1.4)
        nrm = Vector((x / r * math.sin(a), y / r * math.sin(a), math.cos(a)))
        return nrm * (R + h) - Vector((0, 0, R)), nrm

    tips, k_, best = [], 0, None
    for r_, m in enumerate(rows):
        shift = 0.36 * w if (len(rows) > 1 and r_ == 1 and m == rows[0]) else 0.0
        for i in range(m):
            x0 = (i - (m - 1) / 2) * 0.72 * w + shift
            q = x0 / max(Wp / 2, 1e-9)
            Lk = L * (1.0 - vary * _FUR_VARY[k_ % 8]) * (1.0 - 0.12 * abs(q)) * (0.80 if r_ == 1 else 1.0)
            yaw = math.radians(fan * q)
            ln = lean + 0.07 * vary / 0.3 * (1 if k_ % 2 else -1)
            y0 = 0.32 * L * r_
            lift = 0.30 * T if (r_ == 0 and len(rows) > 1) else 0.0     # the rear row rides over the front row
            st = []
            for f, hh, sx in ((-0.16, -0.30 * T - 0.05 * L, 0.0), (0.30, 0.36 * T + lift, 0.10), (0.68, 0.34 * T + 0.8 * lift + 0.35 * hook * Lk, 0.50),
                              (1.0, 0.10 * T + hook * Lk, 1.0)):
                s_ = f * Lk
                xs = x0 + math.sin(yaw) * s_ + ln * Lk * sx * math.cos(yaw)
                ys = y0 + math.cos(yaw) * s_ - ln * Lk * sx * math.sin(yaw)
                st.append(wrap(xs, ys, hh))
            _sweep(B, [a for a, _ in st], [(0.60 * w, 0.60 * T), (w, T), (0.70 * w, 0.66 * T), (0, 0)], st[1][1],
                   lambda b_, s_: 'fur_tip' if b_ >= 2 else 'fur', end='point', sect=ridge)
            tips.append(st[-1][0])
            if best is None or Lk > best[0]:
                best = (Lk, st[-1][0])
            k_ += 1
    return _finish(B, name, _frame(base, forward, up), side, mats, colours, dict(base=(0, 0, 0), tip=best[1], tips=tips))


TAIL_ENV = dict(          # (fraction along the tail, radius as a fraction of the widest)
    brush=[(0.0, 0.42), (0.28, 0.90), (0.50, 1.0), (0.75, 0.80), (1.0, 0.10)],
    tuft=[(0.0, 0.26), (0.36, 0.36), (0.62, 0.96), (0.82, 0.84), (1.0, 0.12)],
    flame=[(0.0, 0.80), (0.24, 1.0), (0.60, 0.72), (1.0, 0.12)])


def tail_tuft(base, length=0.16, radius=None, forward=(0, 1, 0), up=(0, 0, 1), side=1, tiers=3, sides=6,
              curve=25.0, kind='brush', jag=0.30, name='tuft', mats=None, colours=None):
    """A tail end as ONE soft mass in one closed shell: a full teardrop built from two to four big
    overlapping tiers of fur. Each tier swells to a belly and ends in an uneven edge of lock tips
    (long and short, slightly flared); the next tier starts tucked under that edge and swells out
    again, so the outline stays one smooth brush and the steps read as clumps laid over each
    other. The last tier runs to an off-centre tip.

    base     the end of the tail stem (the root is buried); forward = the way the tail runs;
             up = the side the tip curls toward (curve degrees over the length)
    kind     'brush' (fox, wolf: fullest past the middle), 'tuft' (lion, cow: a thin stem flaring
             late into a teardrop), 'flame' (fullest at the root, tapering: a squirrel, a mane lock)
    radius   the widest point (default 0.30 length: a tail thinner than 0.25 reads as a rope)
    tiers    2-4; sides 5-6; jag = how deep the tier edges zigzag, as a fraction of a tier (0 = even)
    Slots: fur, fur_under (the step faces, in shadow), fur_tip (the last tier). Attach: base, tip.
    Triangles: 94 (3 tiers, 6 sides; a tier boundary where the mass is still swelling has no step, 12 fewer).
    Lite: tiers=2 gives 58; tiers=2, sides=5 gives 48."""
    L = float(length)
    Rm = radius or 0.30 * L
    pts_ = TAIL_ENV[kind]

    def env(s):
        s = min(max(s, 0.0), 1.0)
        for (a, ra), (b, rb) in zip(pts_, pts_[1:]):
            if s <= b:
                return Rm * (ra + (rb - ra) * (s - a) / (b - a))
        return Rm * pts_[-1][1]

    def station(s):
        """Point and frame at arc fraction s of a circular arc bending toward +z (straight before s = 0)."""
        a = math.radians(curve)
        if abs(a) < 1e-4 or s <= 0:
            return Vector((0, s * L, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
        rr = L / a
        th = a * s
        return (Vector((0, rr * math.sin(th), rr * (1 - math.cos(th)))),
                Vector((0, math.cos(th), math.sin(th))), Vector((0, -math.sin(th), math.cos(th))))

    zz = (0.0, 1.0, 0.40, 0.85, 0.15, 0.65)             # how far each lock tip of an edge falls short

    def ring(s, rad, phase, zig=0.0, zlen=0.0):
        out = []
        for i in range(sides):
            z_ = zz[i % 6]
            c, tg, nz = station(min(s - zlen * z_, 1.0))
            ang = 2 * math.pi * (i + phase) / sides
            rv = rad * (1.0 - zig * z_)
            out.append(c + Vector((1, 0, 0)) * (rv * math.sin(ang)) + nz * (rv * math.cos(ang)))
        return B.ring(out)

    B = _B()
    seg = 1.0 / tiers
    start = ring(-0.12, env(0.0), 0.0)
    B.cap(start, 'fur')
    for q in range(tiers):
        last = q == tiers - 1
        slot = 'fur_tip' if last else 'fur'
        sb = (q + (0.36 if last else 0.50)) * seg
        belly = ring(sb, env(sb), 0.0, zig=0.05)
        B.bridge(start, belly, slot)
        if last:
            c, tg, nz = station(1.0)
            tip = c + nz * (0.08 * L)
            B.fan(belly, B.v(tip), slot)
        else:
            se = (q + 1) * seg
            re_ = env(se)
            nb = env((q + 1 + (0.36 if q + 1 == tiers - 1 else 0.50)) * seg)
            if nb > 1.12 * re_:                      # the mass is still swelling here (a lion's stem): no step, one skin
                start = ring(se, re_, 0.0)
                B.bridge(belly, start, slot)
                continue
            edge = ring(se, re_, 0.0, zig=0.14, zlen=jag * seg)
            B.bridge(belly, edge, slot)
            # the next tier starts tucked under this edge, behind the shortest lock tip, and never so
            # wide that its swell to the next belly would come out through the tips
            start = ring(se - (jag + 0.12) * seg, max(min(0.70 * re_, (0.88 * re_ - 0.46 * nb) / 0.54), 0.3 * re_), 0.0)
            B.bridge(edge, start, 'fur_under')
    return _finish(B, name, _frame(base, forward, up), side, mats, colours, dict(base=(0, 0, 0), tip=tip))


# name -> (default triangles, the parameters a builder sets)
PARTS = dict(
    eye_set=(80, 'radius, side, expression | brow, lid, arch, style animal|toon, pupil round|slit|bar, look, lower_lid, glint'),
    paw_canine=(184, 'width, height, toes, toe_segs, claws, claw_len, pads, splay, root, open_root'),
    paw_bear=(198, 'width, height, toes, toe_segs, claws, claw_len, pads, splay, root, open_root'),
    foot_biped=(68, 'width, height, length, toes, toe_segs, claws, pads, root, open_root'),
    hoof_cloven=(68, 'radius, height, width, length, cleft, dewclaws, open_root'),
    bird_foot=(148, 'toe_length, height, radius, spread, hallux, talons, talon_len, toe_sides'),
    hand_three_finger=(140, 'width, fingers, curl, spread, finger_len, thumb, thumb_curl, knuckle, claw_len, wrist, open_root'),
    hand_mitten=(96, 'width, curl, finger_len, thumb_curl, knuckle, wrist, open_root'),
    fist=(144, 'width, fingers, knuckle, wrist, open_root'),
    ear_cup=(38, 'length, width, kind round|pointed|leaf, cup, thickness, inner'),
    horn=(48, 'length, radius, curve, spiral, segs, sides, ridges, taper, tip_from'),
    antler_beam=(110, 'length, radius, curve, spiral, tines stag|young|elk|list, fan, tine_sides, tine_segs, segs'),
    tusk=(15, 'length, radius, curve, segs, sides'),
    tooth_row=(62, 'start, end, out, n, height, bulge, profile, gum, lean'),
    nose_pad=(48, 'width, kind canine|bear|button|pig, depth, nostrils'),
    fur_clump=(80, 'length, width, n, radius, thickness, hook, lean, fan, vary'),
    tail_tuft=(94, 'length, radius, tiers, sides, curve, kind brush|tuft|flame, jag'))
