#!/usr/bin/env python3
"""Make a spec LEGAL before you spend a round on it.

    python3 harness/fit.py <spec.json> [-o fitted.json] [--dry]

WHAT THIS IS FOR. A spec is refused for two completely different reasons and
they deserve completely different treatment:

  · DESIGN — the silhouette does not read, the poles are the same idea twice,
    the creature is a bean. Those need a decision, and this tool never touches
    them.
  · LEGALITY — a root ring is not buried in its host, two neighbouring bones
    are the same length, the build does not land on its declared height. Those
    are arithmetic with one right answer, and nobody should be spending build
    rounds on them.

The engine already computes the exact correction for each of those and prints
it inside the BLOCK — "move joint X about 0.043m toward [0.00,-1.00,0.12]",
"multiply every joint coordinate by 1.3613". This reads those numbers back and
APPLIES them, then rebuilds, then reads again, until the legality set is clear
or a pass stops making progress.

WHY IT ITERATES. The fixes are coupled: burying a root ring moves a joint,
which changes two segment lengths, which can trip the proportion band, which
moves a joint again. One pass is not enough and neither is a human doing it by
hand — that is the loop this replaces.

WHAT IT WILL NOT DO. Anything where the correction is a design decision:

  · balance — moving the centre of mass means moving masses, and which mass
    moves is a design choice. Reported, never applied.
  · mesh_integrity, limb_clearance, touch, part_seat — these say a shape or a
    relationship is wrong, not by how much.
  · every style check — soft_mass, thinnest_px48, poles_apart, the identity
    gates. A tool that auto-satisfied a style threshold would be optimising the
    ruler instead of the creature.

So a clean run of this does not mean the creature is good. It means the round
you are about to spend is about the creature, not about arithmetic.
"""
import sys, os, json, re, subprocess, copy

H = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(H)
MAX_PASSES = 6

# Only these are auto-applied. Everything else is reported and left alone.
FIXABLE = ('root_containment', 'proportion', 'size')


def build(spec, tmp):
    json.dump(spec, open(tmp, 'w', encoding='utf-8'))
    p = subprocess.run(['node', os.path.join('engine', 'cli.js'), tmp,
                        os.path.join(os.path.dirname(tmp), '_fit.glb')],
                       capture_output=True, text=True, cwd=R)
    out = (p.stdout or '') + (p.stderr or '')
    return [l for l in out.splitlines() if l.startswith('BLOCK:')], out


def joint_axes(j):
    return [k for k in ('up', 'fwd', 'side', 'out') if k in j]


def apply_root(spec, line):
    """root_containment: move the named joint into its host by the stated metres."""
    m = re.search(r'Move joint "([^"]+)" about ([\d.]+)m(?: toward \[([-\d., ]+)\])?', line)
    if not m:
        return False
    jn, dist = m.group(1), float(m.group(2))
    if dist <= 0:
        return False
    d = [float(x) for x in m.group(3).split(',')] if m.group(3) else None
    j = (spec.get('joints') or {}).get(jn)
    if j is None:
        return False
    if isinstance(j, list):                      # absolute [x, y, z]
        if not d:
            return False
        for i in range(3):
            j[i] = round(j[i] + d[i] * dist, 4)
        return True
    if not isinstance(j, dict):
        return False
    # relational: push along whichever axes it already uses, toward the host
    ax = joint_axes(j)
    if not ax:
        return False
    # The direction the engine prints is already a unit world vector, so each
    # relational axis takes its own component of it directly. Dividing by the
    # sum of the components (the obvious-looking normalisation) under-shoots
    # every time and the loop then walks toward the target without arriving.
    comp = {'side': (d[0] if d else 0), 'up': (d[1] if d else -1),
            'fwd': (d[2] if d else 0), 'out': (d[0] if d else 0)}
    # `need` is the 80th-percentile overshoot — the move that lands the ring
    # exactly ON the boundary. Overshoot it slightly so the next pass is not
    # spent on the rounding.
    dist *= 1.25
    for a in ax:
        j[a] = round(j[a] + comp[a] * dist, 4)
    return True


def apply_proportion(spec, line):
    """proportion: break a 50:50 pair by shortening the SECOND bone."""
    m = re.search(r'chain "([^"]+)" segments (\S+)→(\S+)→(\S+) are 50:50 \(([\d.]+)\)', line)
    if not m:
        return False
    _, a, b, c, ratio = m.groups()
    j = (spec.get('joints') or {}).get(c)
    if not isinstance(j, dict):
        return False
    ax = joint_axes(j)
    if not ax:
        return False
    # aim for the middle of the 0.62-0.85 band rather than the edge of it, so
    # the next pass does not land back on the boundary
    k = 0.74
    for a_ in ax:
        j[a_] = round(j[a_] * k, 4)
    return True


def apply_size(spec, line):
    m = re.search(r'multiply every joint coordinate by ([\d.]+)', line)
    if not m:
        return False
    f = float(m.group(1))
    for jn, j in (spec.get('joints') or {}).items():
        if isinstance(j, list):
            spec['joints'][jn] = [round(v * f, 4) for v in j]
        elif isinstance(j, dict):
            for a in joint_axes(j) + ['len', 'ground']:
                if a in j:
                    j[a] = round(j[a] * f, 4)
    return True


APPLY = {'root_containment': apply_root, 'proportion': apply_proportion, 'size': apply_size}


def main():
    a = sys.argv[1:]
    if not a or a[0].startswith('-'):
        print(__doc__)
        return 2
    src = a[0]
    out = a[a.index('-o') + 1] if '-o' in a else None
    dry = '--dry' in a
    spec = json.load(open(src, encoding='utf-8'))
    tmp = os.path.join(os.path.dirname(os.path.abspath(src)), '_fit_spec.json')

    applied, history = [], []
    for p in range(1, MAX_PASSES + 1):
        blocks, _ = build(spec, tmp)
        kinds = [b.split(':')[1].strip() if ':' in b else b for b in blocks]
        legal = [b for b in blocks if any(b.startswith('BLOCK: ' + f) for f in FIXABLE)]
        history.append((p, len(blocks), len(legal)))
        if not blocks:
            print(f'[fit] pass {p}: green.')
            break
        if not legal:
            print(f'[fit] pass {p}: {len(blocks)} block(s) left, none of them arithmetic.')
            break
        if dry:
            print(f'[fit] pass {p}: {len(legal)} fixable of {len(blocks)} — dry run, stopping.')
            break
        moved = 0
        for b in legal:
            key = b[len('BLOCK: '):].split(':')[0]
            fn = APPLY.get(key)
            if fn and fn(spec, b):
                moved += 1
                applied.append(key)
        print(f'[fit] pass {p}: {len(blocks)} block(s), {len(legal)} arithmetic, applied {moved}')
        if not moved:
            print('[fit] nothing moved — the remaining ones need a decision.')
            break

    blocks, raw = build(spec, tmp)
    try:
        os.remove(tmp)
        os.remove(os.path.join(os.path.dirname(tmp), '_fit.glb'))
    except OSError:
        pass
    print()
    from collections import Counter
    if applied:
        print('  applied: ' + ', '.join(f'{k}x{v}' for k, v in Counter(applied).items()))
    if blocks:
        print(f'  {len(blocks)} block(s) remain — these are yours to decide:')
        for b in blocks:
            print('    ' + b[:150])
    else:
        print('  the spec is legal. The round you spend next is about the creature.')
    if out and not dry:
        json.dump(spec, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f'  written: {out}')
    return 1 if blocks else 0


if __name__ == '__main__':
    sys.exit(main())
