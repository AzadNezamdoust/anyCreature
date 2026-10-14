#!/usr/bin/env python3
"""Graft — transplant a part from one creature's GLB onto another, at SPEC level.

Every anyCreature GLB carries its authored spec inside (`asset.extras.
source_spec`). Grafting therefore never touches meshes: it copies the part's
spec block (plus everything it depends on) from the donor into the recipient's
spec, rescales it by the two creatures' declared heights, and writes a fused
spec. YOU then compile it — and the normal gates (part_seat, part_attachment,
touch, anim_integrity) judge the transplant like any other build. A graft that
does not seat gets BLOCKED, not shipped.

    python3 harness/graft.py <donor.glb> <recipient.glb> \\
            --part <name-or-material> --host <recipient joint> \\
            [--out fused_spec.json] [--offset x,y,z] [--scale N]

Then:  node engine/cli.js fused_spec.json out/fused.glb

Covers automatically: hosted parts (curve / spike / hand / paw / fin / eye) and
membranes (their rib chains, joints, attach entries, mirror registration and
matching animation tracks come along, rebased onto the new host). Anchored
parts are copied with a TODO printed — re-aim the anchor at a recipient chain.
"""
import sys, os, json, struct, copy

def load_spec(path):
    d = open(path, 'rb').read()
    if d[:4] != b'glTF':
        return json.load(open(path))          # a bare spec.json also works
    jl, = struct.unpack('<I', d[12:16])
    g = json.loads(d[20:20 + jl])
    src = (g.get('asset', {}).get('extras', {}) or {}).get('source_spec')
    if not src:
        sys.exit(f'[graft] {os.path.basename(path)} has no embedded spec '
                 '(built before 1.3.0?) — recompile it, or pass its spec.json instead')
    return src

def resolve_joints(spec):
    """Mini mirror of engine/core/relative.js — absolute positions for rebasing."""
    J = copy.deepcopy(spec.get('joints', {}))
    pending = [n for n, v in J.items() if not isinstance(v, list)]
    guard = len(pending) + 1
    while pending and guard > 0:
        guard -= 1
        nxt = []
        for n in pending:
            d = J[n]; base = J.get(d.get('from'))
            if not isinstance(base, list):
                nxt.append(n); continue
            if 'dir' in d and 'len' in d:
                dx = d['dir']; L = (dx[0]**2 + dx[1]**2 + dx[2]**2) ** 0.5 or 1
                p = [base[k] + dx[k] / L * d['len'] for k in range(3)]
            else:
                p = [base[0] + d.get('side', 0), base[1] + d.get('up', 0), base[2] + d.get('fwd', 0)]
            if 'ground' in d: p[1] = d['ground']
            J[n] = p
        pending = nxt
    return J

def main():
    args = sys.argv[1:]
    def opt(flag, default=None):
        if flag in args:
            i = args.index(flag)
            if i + 1 >= len(args):
                sys.exit(f'[graft] {flag} needs a value')
            v = args[i + 1]; del args[i:i + 2]; return v
        return default
    part_key = opt('--part'); new_host = opt('--host')
    out = opt('--out', 'fused_spec.json')
    off = opt('--offset'); scale_opt = opt('--scale')
    if len(args) < 2 or not part_key:
        sys.exit(__doc__)
    donor, recip = load_spec(args[0]), load_spec(args[1])
    fused = copy.deepcopy(recip)
    todos = []

    # ── find the part in the donor ──
    cand = [p for p in donor.get('parts', [])
            if p.get('name') == part_key or p.get('material') == part_key]
    if not cand:
        names = [(p.get('name') or p.get('material') or p.get('type')) for p in donor.get('parts', [])]
        sys.exit(f'[graft] no part "{part_key}" in donor. Available: {", ".join(names)}')
    part = copy.deepcopy(cand[0])

    # ── scale: declared heights, unless overridden ──
    if scale_opt:
        k = float(scale_opt)
    elif donor.get('height') and recip.get('height'):
        k = recip['height'] / donor['height']
    else:
        k = 1.0
        todos.append('no height declared on both sides — grafted at 1:1, check the size by eye')
    def sc(v):  # scalars, and the [w, h] pairs curve radii accept
        return [sc(x) for x in v] if isinstance(v, list) else round(v * k, 5)

    # ── palette entries travel with the part ──
    fused.setdefault('palette', {})
    for mat in {part.get('material')} - {None}:
        if mat in fused['palette'] and fused['palette'][mat] != donor['palette'].get(mat):
            nm = mat + '_g'
            todos.append(f'material name "{mat}" already exists — grafted copy renamed "{nm}"')
            part['material'] = nm; mat = nm
        fused['palette'][mat] = copy.deepcopy(donor['palette'][cand[0]['material']])

    dJ = resolve_joints(donor); rJ = resolve_joints(recip)

    if part.get('type') == 'membrane':
        # membranes ride chains: copy each rib chain + joints, rebased onto the new host
        if not new_host: sys.exit('[graft] a membrane graft needs --host <recipient joint>')
        if new_host not in rJ: sys.exit(f'[graft] recipient has no joint "{new_host}"')
        anchor_old = None
        rename = {}          # donor JOINT name -> name in the fused spec
        for rib in part.get('ribs', []):
            cn = rib.get('chain')
            if not cn: continue
            names = donor['chains'][cn]
            if anchor_old is None:
                anchor_old = dJ[names[0]]           # first rib root = old shoulder
            cn2 = cn if cn not in fused.get('chains', {}) else cn + 'G'
            fused.setdefault('chains', {})[cn2] = []
            for n in names:
                n2 = n if n not in fused.get('joints', {}) else n + 'G'
                if n2 != n: rename[n] = n2
                p0 = dJ[n]
                fused.setdefault('joints', {})[n2] = [
                    round(rJ[new_host][0] + (p0[0] - anchor_old[0]) * k, 5),
                    round(rJ[new_host][1] + (p0[1] - anchor_old[1]) * k, 5),
                    round(rJ[new_host][2] + (p0[2] - anchor_old[2]) * k, 5)]
                fused['chains'][cn2].append(n2)
            fused.setdefault('attach', {})[cn2] = new_host
            if cn in donor.get('mirror', []) and cn2 not in fused.setdefault('mirror', []):
                fused['mirror'].append(cn2)
            rib['chain'] = cn2
            # matching animation tracks come along (same-named clips only)
            for an, clip in (donor.get('animations') or {}).items():
                dst = (fused.get('animations') or {}).get(an)
                if not dst: continue
                for jn, tr in (clip.get('tracks') or {}).items():
                    if jn in names:
                        # keyed by the joint's FUSED name: the old code looked the
                        # joint up in the chain-rename table, so a renamed joint's
                        # track landed on the recipient's own joint of that name
                        dst.setdefault('tracks', {})[rename.get(jn, jn)] = copy.deepcopy(tr)
            # 1.3.2: an animated joint with no joint_range is a BLOCK, so the
            # donor's declared limits travel with its joints
            for n in names:
                lim = (donor.get('joint_range') or {}).get(n)
                if lim is not None:
                    fused.setdefault('joint_range', {})[rename.get(n, n)] = copy.deepcopy(lim)
            fn = (donor.get('function') or {}).get(cn)
            if fn and cn2 not in (fused.get('function') or {}):
                fused.setdefault('function', {})[cn2] = fn
        todos.append('membrane grafted: check rib pose (the wing carries its old pose, rebased) and clearance')
    else:
        # hosted part: rescale local numbers, point it at the new host
        if not new_host: sys.exit('[graft] --host <recipient joint> is required')
        if new_host not in rJ: sys.exit(f'[graft] recipient has no joint "{new_host}"')
        part['host'] = new_host
        if 'offset' in part: part['offset'] = [sc(v) for v in part['offset']]
        if off: part['offset'] = [float(x) for x in off.split(',')]
        if 'size' in part:
            part['size'] = sc(part['size']) if isinstance(part['size'], (int, float)) \
                else [sc(v) for v in part['size']]
        for seg in part.get('segments', []) or []:
            if 'len' in seg: seg['len'] = sc(seg['len'])
            if 'r' in seg: seg['r'] = sc(seg['r'])
        if 'thickness' in part: part['thickness'] = sc(part['thickness'])
        if 'points' in part: part['points'] = [[sc(u), sc(v)] for u, v in part['points']]
        if 'anchor' in part:
            todos.append(f'part is anchored to donor chain "{part["anchor"].get("chain")}" — '
                         're-aim "anchor" at a recipient chain (or remove it and place by offset)')

    # 1.3.2: part names are required and unique (part_names BLOCKs a clash).
    # Grafting "ear" onto a creature that already has an "ear" must not
    # produce a spec the engine refuses for a reason graft itself created.
    taken = {p.get('name') for p in fused.get('parts', [])}
    if part.get('name') in taken or not part.get('name'):
        base = part.get('name') or part.get('material') or part.get('type') or 'part'
        nm, i = base + '_graft', 2
        while nm in taken:
            nm, i = f'{base}_graft{i}', i + 1
        todos.append(f'part name "{part.get("name")}" is taken in the recipient — grafted copy named "{nm}"')
        part['name'] = nm
    fused.setdefault('parts', []).append(part)
    json.dump(fused, open(out, 'w'), indent=1)
    print(f'[graft] "{part_key}" → host "{new_host}" · scale ×{k:.3f} · wrote {out}')
    for t in todos: print('[graft] TODO: ' + t)
    print(f'[graft] next: node engine/cli.js {out} out/fused.glb   (the gates judge the transplant)')

if __name__ == '__main__':
    main()
