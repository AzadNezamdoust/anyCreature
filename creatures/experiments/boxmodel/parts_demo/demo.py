#!/usr/bin/env python3
"""parts_demo: every part of kit/parts.py on a neutral stand, as one labelled contact sheet.

    py -3.11 experiments/boxmodel/parts_demo/demo.py [name filter]

Launches headless Blender on this same file, builds each part in two to four parameter variants,
runs the kit's checks on every one (closed shells and self-intersection with bmkit.report per
shell; slivers, pass-through, floating shells, z-fighting and open edges with techqa.measure
against the stand, at the part's own size so no small triangle is skipped), renders a flat-shaded
colour close-up and a wire close-up, and writes

    experiments/boxmodel/parts_demo/parts_sheet.jpg     one row per part: colour | wire per variant

It prints the check table. The stand is grey-tan; the ground under feet is a separate slab.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(HERE, '..', 'kit')
sys.path.insert(0, KIT)
try:
    import bpy
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False

RES = 420


# =============================================================================
# inside Blender: build, check, render
# =============================================================================
def blender_main(out, filt):
    import bmesh
    from mathutils import Vector, Matrix
    import bmkit as k, techqa as Q, parts as P

    def clear():
        for o in list(bpy.data.objects):
            if o.type == 'MESH':
                bpy.data.objects.remove(o, do_unlink=True)

    def stand(prims, name='stand', colour='#d6cdbd'):
        """prims: ('box', centre, size) | ('col', p0, p1, r0, r1, n) | ('ball', centre, radius, (sx, sy, sz))"""
        bm = bmesh.new()
        for pr in prims:
            if pr[0] == 'box':
                M = Matrix.Translation(Vector(pr[1])) @ Matrix.Diagonal((*pr[2], 1.0))
                bmesh.ops.create_cube(bm, size=1.0, matrix=M)
            elif pr[0] == 'col':
                p0, p1 = Vector(pr[1]), Vector(pr[2])
                M = P._frame((p0 + p1) / 2, (p1 - p0), (0.3, 0.2, 1)) @ Matrix.Rotation(-math.pi / 2, 4, 'X')
                bmesh.ops.create_cone(bm, cap_ends=True, segments=pr[5], radius1=pr[3], radius2=pr[4],
                                      depth=(p1 - p0).length, matrix=M)
            else:
                M = Matrix.Translation(Vector(pr[1])) @ Matrix.Diagonal((*pr[3], 1.0))
                bmesh.ops.create_icosphere(bm, subdivisions=2, radius=pr[2], matrix=M)
        ob = k.object_from_bm(name, bm, mirror=False)
        bm.free()
        ob.data.materials.append(k.material(name, k.srgb(colour)))
        k.white(ob)
        ob.color = (0.78, 0.78, 0.76, 1)
        return ob

    def ground(z=0.0, s=0.6):
        return stand([('box', (0, 0, z - 0.012), (s, s, 0.02))], 'ground', '#c2beb6')

    def limb(H, r, tilt=(0, 0.0)):
        """A leg stub ending at (0, 0, H), sunk a little into the part, plus the ground."""
        return [stand([('col', (0, 0, H - 0.15 * r), (tilt[0], tilt[1], H + 4.0 * r), 0.8 * r, 1.1 * r, 6)]), ground()]

    # ---- the catalogue: (row title, [(label, builder, yaw, pitch, zoom)]) ----------------------
    def eyes(r=0.02, **kw):
        def f():
            hd = stand([('box', (0, 2.6 * r, 0.1 * r), (9.2 * r, 5.2 * r, 6.6 * r))])
            L = P.eye_set((2.35 * r, 0, 0), r, side=1, name='eyeL', **kw)
            R = P.eye_set((-2.35 * r, 0, 0), r, side=-1, name='eyeR', **kw)
            return [L, R], [hd]
        return f

    def foot(fn, H, r, **kw):
        def f():
            return [fn((0, 0, H), **kw)], limb(H, r)
        return f

    def hand(fn, **kw):
        def f():
            W = kw.get('width', 0.09)
            st = stand([('col', (-0.12 * W, 0, 0), (0.9 * W, 0, 0), 0.12 * W, 0.17 * W, 6)])
            return [fn((0, 0, 0), forward=(-1, 0, 0), up=(0, -1, 0), **kw)], [st]
        return f

    def on_skull(fn, base_dir=(0, 0, 1), R=0.06, **kw):
        def f():
            c = Vector((0, 0, 0))
            st = stand([('ball', c, R, (1.0, 1.15, 0.9))])
            b = Vector(base_dir).normalized()
            base = Vector((b.x * R, b.y * R * 1.15, b.z * R * 0.9)) * 0.97
            return [fn(base, **kw)], [st]
        return f

    def muzzle(fn, **kw):
        def f():
            W = kw.get('width', 0.04)
            st = stand([('box', (0, 0.9 * W, -0.12 * W), (1.5 * W, 1.9 * W, 1.25 * W))])
            return [fn((0, 0, 0), **kw)], [st]
        return f

    def teeth(**kw):
        def f():
            st = stand([('box', (0, 0.0, -0.016 if kw.get('up', (0, 0, 1))[2] > 0 else 0.016), (0.09, 0.10, 0.026))])
            return [P.tooth_row(**kw)], [st]
        return f

    def tusks(**kw0):
        def f():
            kw = dict(kw0)
            st = stand([('box', (0, 0.03, -0.012), (0.07, 0.09, 0.05))])
            fw = kw.pop('forward')
            return [P.tusk((0.033, -0.008, -0.004), forward=fw, name='tuskL', **kw),
                    P.tusk((-0.033, -0.008, -0.004), forward=(-fw[0], fw[1], fw[2]), side=-1, name='tuskR', **kw)], [st]
        return f

    def tail(**kw):
        def f():
            L = kw.get('length', 0.16)
            st = stand([('col', (0, -0.6 * L, -0.02 * L), (0, 0.02 * L, 0), 0.085 * L, 0.10 * L, 6)])
            return [P.tail_tuft((0, 0, 0), **kw)], [st]
        return f

    BALL = (Vector((0, 0, -0.10)), Vector((0.115, 0.14375, 0.115)))

    def clumps(spec):
        """spec: [(y on the ball's top meridian, comb direction, fur_clump keywords)]"""
        def f():
            c, rad = BALL
            st = stand([('ball', c, 0.115, (1.0, 1.25, 1.0))])
            out = []
            for i, (y, fwd, kw) in enumerate(spec):
                b = Vector((0, y, c.z + rad.z * math.sqrt(max(1 - (y / rad.y) ** 2, 0)) * 0.985))
                n = Vector((b.x / rad.x ** 2, b.y / rad.y ** 2, (b.z - c.z) / rad.z ** 2)).normalized()
                fw = Vector(fwd) - n * Vector(fwd).dot(n)
                out.append(P.fur_clump(b, forward=fw, up=n, name=f'clump{i}', **kw))
            return out, [st]
        return f

    def bridged(fn, H, r, sides, **kw):
        """A limb end with `sides` vertices, and the part's open root ring bridged onto it (stage-3 form)."""
        def f():
            st = stand([('col', (0, 0, H + 0.6 * r), (0, 0, H + 4.6 * r), 0.85 * r, 1.1 * r, sides)])
            zs = [v.co.z for v in st.data.vertices]
            ring = sorted([v.co.copy() for v in st.data.vertices if v.co.z < min(zs) + 1e-5], key=lambda q: math.atan2(q.y, q.x))
            prt = fn((0, 0, H), open_root=True, **kw)
            k.bridge_part(prt, ring, reason='demo')
            return [prt], [st, ground()]
        return f

    cat = [
        ('eye_set  animal: the lid / brow wedge is the expression', [
            ('neutral', eyes(), -24, 6, 1.0), ('angry', eyes(expression='angry'), -24, 6, 1.0),
            ('friendly', eyes(expression='friendly'), -24, 6, 1.0), ('sleepy', eyes(expression='sleepy'), -24, 6, 1.0)]),
        ('eye_set  toon / pupils / lower lid', [
            ('toon neutral', eyes(r=0.03, style='toon'), -24, 6, 1.0),
            ('toon angry, look', eyes(r=0.03, style='toon', expression='angry', look=(0.12, -0.08)), -24, 6, 1.0),
            ('slit pupil, lower lid', eyes(pupil='slit', lower_lid=0.3, colours={'iris': '#9fc23a'}), -24, 6, 1.0),
            ('bar pupil, no brow', eyes(pupil='bar', brow_wedge=False, colours={'iris': '#c98a2b'}), -24, 6, 1.0)]),
        ('paw_canine', [
            ('default (4 toes)', foot(P.paw_canine, 0.064, 0.02, width=0.08), -38, 24, 1.0),
            ('lite: toe_segs=1, no claws', foot(P.paw_canine, 0.064, 0.02, width=0.08, toe_segs=1, claws=False), -38, 24, 1.0),
            ('underside: pads', foot(P.paw_canine, 0.064, 0.02, width=0.08), -150, -58, 1.0),
            ('bridge_part: 6-ring root on a 5-ring limb', bridged(P.paw_canine, 0.064, 0.02, 5, width=0.08), -128, 16, 1.0)]),
        ('paw_bear', [
            ('default (5 toes, long claws)', foot(P.paw_bear, 0.0715, 0.036, width=0.13), -38, 26, 1.0),
            ('big cat: toes=4, claw_len 0.45', foot(P.paw_bear, 0.0715, 0.036, width=0.13, toes=4, claw_len=0.45), -38, 26, 1.0),
            ('underside: pads', foot(P.paw_bear, 0.0715, 0.036, width=0.13), -150, -58, 1.0)]),
        ('foot_biped', [
            ('default (3 toes)', foot(P.foot_biped, 0.0558, 0.022, width=0.09), -50, 22, 1.0),
            ('toes=1: toe block', foot(P.foot_biped, 0.0558, 0.022, width=0.09, toes=1), -50, 22, 1.0),
            ('goblin: claws, toe_segs=2', foot(P.foot_biped, 0.0558, 0.022, width=0.09, claws=True, toe_segs=2), -50, 22, 1.0)]),
        ('hoof_cloven', [
            ('default', foot(P.hoof_cloven, 0.1456, 0.024, radius=0.028), -32, 16, 1.0),
            ('boar: short and wide', foot(P.hoof_cloven, 0.118, 0.024, radius=0.028, height=0.118, width=0.10, length=0.095), -32, 16, 1.0),
            ('deer: narrow, no dewclaws', foot(P.hoof_cloven, 0.16, 0.019, radius=0.022, height=0.16, width=0.062, length=0.10, dewclaws=False), -140, 10, 1.0)]),
        ('bird_foot', [
            ('default', foot(P.bird_foot, 0.063, 0.008, toe_length=0.07), -32, 30, 1.0),
            ('raptor: talon_len 0.6', foot(P.bird_foot, 0.063, 0.011, toe_length=0.07, talon_len=0.6, spread=40, radius=0.012), -32, 30, 1.0),
            ('hen: toe_sides=3, small talons', foot(P.bird_foot, 0.063, 0.007, toe_length=0.07, talon_len=0.25, hallux=0.35, toe_sides=3), -32, 30, 1.0)]),
        ('hand_three_finger', [
            ('default', hand(P.hand_three_finger), 12, 28, 1.0),
            ('fingers=4, spread 20', hand(P.hand_three_finger, fingers=4, spread=20, width=0.10), 12, 28, 1.0),
            ('goblin: claws, curl 0.22', hand(P.hand_three_finger, claw_len=0.32, curl=0.22, spread=18), 12, 28, 1.0)]),
        ('hand_mitten', [
            ('default', hand(P.hand_mitten), 12, 28, 1.0),
            ('curl 0.5', hand(P.hand_mitten, curl=0.5, thumb_curl=0.4), 12, 28, 1.0),
            ('palm side', hand(P.hand_mitten), 12, -150, 1.0)]),
        ('fist  (knuckle step)', [
            ('3 fingers', hand(P.fist), 20, 30, 1.0),
            ('fingers=4', hand(P.fist, fingers=4, width=0.10), 20, 30, 1.0),
            ('from the front: the thumb wrap', hand(P.fist), 78, -18, 1.0),
            ('palm side', hand(P.fist), 20, -150, 1.0)]),
        ('ear_cup', [
            ('round', on_skull(P.ear_cup, (0.5, 0, 0.86), kind='round', up=(0.35, 0, 1), length=0.05), -25, 8, 1.0),
            ('pointed', on_skull(P.ear_cup, (0.5, 0, 0.86), kind='pointed', up=(0.3, 0, 1), length=0.075), -25, 8, 1.0),
            ('leaf, width 0.5 length', on_skull(P.ear_cup, (0.9, 0, 0.4), kind='leaf', up=(1, 0.15, 0.45), length=0.11), -25, 8, 1.0),
            ('pointed: the back', on_skull(P.ear_cup, (0.5, 0, 0.86), kind='pointed', up=(0.3, 0, 1), length=0.075), 150, 8, 1.0)]),
        ('horn', [
            ('default: curve 70', on_skull(P.horn, (0.45, -0.2, 0.86), forward=(0.5, 0, 1), up=(0, -1, 0.2), length=0.11), -30, 8, 1.0),
            ('ram: ridges, curve 250, spiral 60', on_skull(P.horn, (0.6, 0.1, 0.75), forward=(0.4, 0.5, 1), up=(0, 1, -0.6),
                                                           length=0.26, radius=0.026, curve=250, spiral=60, segs=7, ridges=True, taper=1.6), -50, 8, 1.0),
            ('spike: sides=4, curve 12', on_skull(P.horn, (0, -0.5, 0.86), forward=(0, -0.5, 1), up=(0, -1, 0), length=0.09,
                                                  sides=4, curve=12, segs=2), -30, 8, 1.0)]),
        ('antler_beam', [
            ('stag', on_skull(P.antler_beam, (0.45, 0.1, 0.88)), -62, 4, 1.0),
            ('young', on_skull(P.antler_beam, (0.45, 0.1, 0.88), tines='young', length=0.16), -62, 4, 1.0),
            ('elk, tine_sides=4', on_skull(P.antler_beam, (0.45, 0.1, 0.88), tines='elk', length=0.28, tine_sides=4), -62, 4, 1.0)]),
        ('tusk', [
            ('boar pair', tusks(forward=(1, -0.55, 0.2), up=(0, 0, 1), length=0.08, curve=75), -24, 10, 1.0),
            ('sabre fangs: curve 25', tusks(forward=(0.05, -0.2, -1), up=(0, 1, 0), curve=25, length=0.08), -28, 0, 1.0)]),
        ('tooth_row', [
            ('front arc with fangs', teeth(start=(-0.03, -0.028, 0), end=(0.03, -0.028, 0), n=8, bulge=0.28,
                                           profile=(0.7, 0.7, 1.7, 0.62, 0.62, 1.7, 0.7, 0.7), height=0.009), -22, 22, 1.0),
            ('predator, straight side', teeth(start=(-0.036, -0.03, 0), end=(0.036, -0.03, 0), n=7, bulge=0.02, height=0.009), -22, 22, 1.0),
            ('upper jaw, jagged, no gum', teeth(start=(-0.03, -0.028, 0), end=(0.03, -0.028, 0), n=7, bulge=0.25, up=(0, 0, -1),
                                                profile='jagged', gum=False, height=0.012), -22, -18, 1.0)]),
        ('nose_pad', [
            ('canine', muzzle(P.nose_pad), -6, -10, 1.0), ('bear', muzzle(P.nose_pad, kind='bear', width=0.05), -20, -10, 1.0),
            ('button', muzzle(P.nose_pad, kind='button', width=0.03), -28, 6, 1.0),
            ('pig', muzzle(P.nose_pad, kind='pig', width=0.06), -28, 6, 1.0)]),
        ('fur_clump', [
            ('n=1: one lock', clumps([(0.0, (0, 1, 0), dict(length=0.09, n=1, radius=0.12))]), -60, 18, 1.0),
            ('ruff: n=5 (default)', clumps([(-0.03, (0, 1, 0), dict(length=0.10, radius=0.12))]), -60, 22, 1.0),
            ('crest: n=7, hook 0.3', clumps([(-0.04, (0, 1, 0), dict(length=0.10, n=7, hook=0.30, radius=0.12))]), -60, 22, 1.0),
            ('mane: three n=3 tufts in a row', clumps([(-0.085 + 0.055 * i, (0, 1, 0), dict(length=0.075, n=3, hook=0.22, radius=0.12))
                                                         for i in range(3)]), -75, 10, 1.0)]),
        ('tail_tuft', [
            ('brush', tail(), -70, 12, 1.0), ('tuft: lion', tail(kind='tuft', length=0.13, tiers=3), -70, 12, 1.0),
            ('flame, tiers=2, sides=5', tail(kind='flame', tiers=2, sides=5), -70, 12, 1.0)]),
    ]

    def shells_of(ob):
        bm = k.evaluated_bm(ob)
        seen, out = set(), []
        for f in bm.faces:
            if f in seen:
                continue
            comp, stack = [], [f]
            seen.add(f)
            while stack:
                x = stack.pop()
                comp.append(x)
                for e in x.edges:
                    for g in e.link_faces:
                        if g not in seen:
                            seen.add(g); stack.append(g)
            out.append(comp)
        res = []
        for comp in out:
            b2 = bmesh.new()
            vm = {}
            for f in comp:
                b2.faces.new([vm.setdefault(v, b2.verts.new(v.co)) for v in f.verts])
            tmp = k.object_from_bm('_shell', b2, mirror=False)
            b2.free()
            r = k.report(tmp)
            res.append((r['nonmanifold_edges'], r['self_intersections']))
            me = tmp.data
            bpy.data.objects.remove(tmp, do_unlink=True)
            bpy.data.meshes.remove(me)
        bm.free()
        return res

    def min_angle(ob):
        V, T, _ = Q._evaluated(ob)
        worst = 180.0
        for _, t in T:
            a, b, c = (V[i] for i in t)
            for x, y, z in ((a, b, c), (b, c, a), (c, a, b)):
                u, w = y - x, z - x
                if u.length > 1e-9 and w.length > 1e-9:
                    worst = min(worst, math.degrees(u.angle(w, 0)))
        return worst

    rows = []
    for title, variants in cat:
        if filt and filt not in title:
            continue
        row = dict(title=title, tiles=[])
        for vi, (label, build, yaw, pitch, zoom) in enumerate(variants):
            clear()
            prt, st = build()
            body = st[0]
            chk = dict(tris=0, shells=0, open=0, selfx=0, sliver=0, hit=0, float=0, zfight=0, min_angle=180.0)
            for p in prt:
                Q.triangulate_convex(p)
            fr = k.frame_of(prt)
            Lp = max(fr['size'])
            counts, _, tris = Q.measure(body, prt, [Lp] * 3)
            for p in prt:
                sh = shells_of(p)
                chk['tris'] += tris[p.name]
                chk['shells'] += len(sh)
                chk['open'] += sum(a for a, _ in sh) + counts[p.name]['open']
                chk['selfx'] += sum(b for _, b in sh)
                for key in ('sliver', 'hit', 'float', 'zfight'):
                    chk[key] += counts[p.name][key]
                chk['min_angle'] = round(min(chk['min_angle'], min_angle(p)), 1)
            chk['per_instance'] = chk['tris'] // len(prt)
            chk['ok'] = all(chk[key] == 0 for key in ('open', 'selfx', 'sliver', 'hit', 'float', 'zfight'))
            Rm = (Matrix.Rotation(math.radians(pitch), 4, 'X') @ Matrix.Rotation(math.radians(yaw), 4, 'Z'))
            if pitch < -40:                       # an underside view: the ground slab would hide it
                for o in [o for o in st if o.name.startswith('ground')]:
                    st.remove(o)
                    bpy.data.objects.remove(o, do_unlink=True)
            for o in prt + st:
                o.matrix_world = Rm @ o.matrix_world
            bpy.context.view_layer.update()
            fr = k.frame_of(prt)
            tag = f"r{len(rows):02d}_{vi}"
            k.shoot(out, tag, fr, views=['az000'], wire_views=['az000'], res=RES, objs=prt, fill=zoom,
                    modes_override=['colour'])
            row['tiles'].append(dict(label=label, colour=f'{tag}_az000_colour.png', wire=f'{tag}_az000_wire.png', **chk))
            k.say(f"part {title.split()[0]:18s} {label:34s} tris {chk['per_instance']:4d} "
                  f"{'PASS' if chk['ok'] else 'FAIL'}")
        rows.append(row)
    with open(os.path.join(out, 'rows.json'), 'w') as f:
        json.dump(rows, f, indent=1)


# =============================================================================
# outside Blender: launch, compose the sheet, print the table
# =============================================================================
def main():
    import run as kitrun
    from PIL import Image, ImageDraw
    filt = sys.argv[1] if len(sys.argv) > 1 else ''
    out = os.path.join(kitrun.ROOT, 'out', 'boxmodel', 'parts_demo')
    os.makedirs(out, exist_ok=True)
    rc, lines, tb = kitrun.blender(os.path.abspath(__file__), ['--out', out, '--filter', filt], os.path.join(out, 'demo.log'))
    if tb or rc:
        print('\n'.join(tb))
        return 2
    rows = json.load(open(os.path.join(out, 'rows.json')))
    T, pad, head, cols = 300, 6, 30, 4
    Wd = cols * (2 * T + pad) + pad
    strips = []
    for r in rows:
        im = Image.new('RGB', (Wd, head + 22 + T + pad), (246, 246, 244))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, Wd, head - 4], fill=(52, 52, 56))
        d.text((10, 4), r['title'], fill=(250, 250, 250), font=kitrun.font(18))
        for i, t in enumerate(r['tiles']):
            x = pad + i * (2 * T + pad)
            d.text((x + 4, head), f"{t['label']}   {t['per_instance']} tris   {'PASS' if t['ok'] else 'FAIL'}",
                   fill=(25, 25, 25) if t['ok'] else (190, 30, 30), font=kitrun.font(14))
            for j, key in enumerate(('colour', 'wire')):
                p = os.path.join(out, t[key])
                if os.path.exists(p):
                    im.paste(Image.open(p).convert('RGB').resize((T, T), Image.LANCZOS), (x + j * T, head + 22))
        im.save(os.path.join(out, 'row_%02d_%s.jpg' % (len(strips), r['title'].split()[0])), quality=88)
        strips.append(im)
    if not filt:
        sheet = Image.new('RGB', (Wd, sum(s.height for s in strips)), (246, 246, 244))
        y = 0
        for s in strips:
            sheet.paste(s, (0, y))
            y += s.height
        sheet.save(os.path.join(HERE, 'parts_sheet.jpg'), quality=86)
        print('sheet:', os.path.relpath(os.path.join(HERE, 'parts_sheet.jpg'), kitrun.ROOT).replace(os.sep, '/'))
    hdr = ('part', 'variant', 'tris', 'shells', 'open', 'selfX', 'sliver', 'hit', 'float', 'zfight', 'min deg', 'verdict')
    print('%-18s %-34s %5s %6s %5s %5s %6s %4s %5s %6s %7s  %s' % hdr)
    bad = 0
    for r in rows:
        for t in r['tiles']:
            bad += not t['ok']
            print('%-18s %-34s %5d %6d %5d %5d %6d %4d %5d %6d %7.1f  %s' % (
                r['title'].split()[0], t['label'], t['per_instance'], t['shells'], t['open'], t['selfx'], t['sliver'],
                t['hit'], t['float'], t['zfight'], t['min_angle'], 'PASS' if t['ok'] else 'FAIL'))
    print('ALL PASS' if not bad else f'{bad} variants FAIL')
    return 1 if bad else 0


if __name__ == '__main__':
    if IN_BLENDER:
        argv = sys.argv[sys.argv.index('--') + 1:]
        blender_main(argv[argv.index('--out') + 1], argv[argv.index('--filter') + 1] if '--filter' in argv else '')
    else:
        sys.exit(main())
