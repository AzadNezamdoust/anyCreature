#!/usr/bin/env python3
"""Every MID part read, ONE command — build, render, and hand back one batch.

    python3 harness/partreads.py <outdir> --spec face.json claw.json tail.json
                                 [--colour hero.png]

The MID whitelist reads used to be two commands PER PART — a compile and a
silhouette render — issued one at a time, and then one reader per part. Card 02
already merged the reads into a single batch; this merges the building too, so
four parts cost one turn instead of eight.

The turn is the unit that costs. A compile is 1.4 seconds and a view is half a
second; a round-trip re-reads the entire conversation so far. A measured a run
build spent 150-odd turns on tool calls that could have been a handful.

Prints the shuffled batch the reader should see, and the answer key you keep to
yourself. Python and stdlib only — the harness ships to other people.
"""
import sys, os, json, subprocess, random, hashlib

H = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(H)
CANARY = os.path.join(H, 'canary')


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=R)
    return p.returncode, (p.stdout or '') + (p.stderr or '')


def main():
    a = sys.argv[1:]
    if len(a) < 2 or '--spec' not in a:
        print(__doc__)
        return 2
    outdir = a[0]
    si = a.index('--spec')
    specs = []
    for x in a[si + 1:]:
        if x.startswith('--'):
            break
        specs.append(x)
    if not specs:
        print('BLOCK: --spec needs at least one part spec')
        return 2
    colour = a[a.index('--colour') + 1] if '--colour' in a else None

    os.makedirs(outdir, exist_ok=True)
    images, key = [], {}
    for spec in specs:
        name = os.path.basename(spec).replace('.json', '')
        dest = os.path.join(outdir, name)
        os.makedirs(dest, exist_ok=True)
        glb = os.path.join(dest, 'part.glb')
        rc, out = run(['node', os.path.join('engine', 'cli.js'), spec, glb])
        if rc != 0:
            blocks = [l for l in out.splitlines() if l.startswith('BLOCK:')]
            print(f'  {name:<22} BUILD REFUSED')
            for b in (blocks or out.strip().splitlines()[-2:]):
                print('      ' + b[:140])
            continue
        # ONE tool reads geometry and produces measures, and it is outline.py.
        # This used to be silmetrics.mjs (launch a browser, render, read pixels)
        # followed by maskmetrics.py (letterbox and measure) — two commands, a
        # browser dependency, and a SECOND definition of every number outline.py
        # already computes. Two implementations of one measure have to be kept
        # in agreement by hand, and they were not: outline.py's first
        # thinnest_px48 took the global minimum of the distance transform and
        # read ~0.25px on every creature, because it was re-derived instead of
        # shared. Departments share their tools; synccheck.py lists any measure
        # that still has more than one definition.
        rc2, out2 = run(['python3', os.path.join('harness', 'outline.py'), glb, dest])
        if rc2 != 0:
            print(f'  {name:<22} silhouette failed: '
                  + (out2.strip().splitlines() or [''])[-1][:120])
            continue
        # a part is read from the 3/4 view; it shows depth that side flattens
        thumbs = [f'sil_{v}_thumb48.png' for v in ('hero', 'side', 'front', 'top')]
        pick = next((t for t in thumbs if os.path.exists(os.path.join(dest, t))), None)
        if not pick:
            print(f'  {name:<22} no thumb48 produced (maskmetrics did not run?)')
            continue
        p = os.path.join(dest, pick)
        images.append(p)
        key[p] = name
        print(f'  {name:<22} built and rendered')

    if colour:
        images.append(colour)
        key[colour] = 'COLOUR READ (describe the colouring, not the shape)'

    # one canary, as card 01 §4 requires — the batch is void without it
    if os.path.isdir(CANARY):
        cands = sorted(f for f in os.listdir(CANARY) if f.endswith('.png'))
        if cands:
            # deterministic pick, so a re-run of the same round is reproducible
            seed = int(hashlib.sha256(''.join(specs).encode()).hexdigest()[:8], 16)
            rnd = random.Random(seed)
            c = os.path.join(CANARY, rnd.choice(cands))
            images.append(c)
            key[c] = f'CANARY ({os.path.basename(c)}) — see canary/answers.json'
            rnd.shuffle(images)
        else:
            random.Random(0).shuffle(images)
    else:
        print('\nnote: harness/canary/ is missing — a batch without a canary is not '
              'a verified read (card 01 §4).')

    if not images:
        print('\nBLOCK: nothing rendered — no batch to read.')
        return 1

    print()
    print('SHOW THESE TO ONE READER, in this order, labelled IMG-A, IMG-B, ...')
    print('-' * 64)
    for i, p in enumerate(images):
        print(f'  IMG-{chr(65 + i)}  {p}')
    print()
    print('Ask, and nothing more:')
    print('  For each image: what is this? Answer with the name of the thing or')
    print('  body part you see. One line per image.')
    print('  (Plus the binding questions from card 01 §4, per image.)')
    print()
    print('ANSWER KEY — keep this to yourself:')
    for i, p in enumerate(images):
        print(f'  IMG-{chr(65 + i)}  {key[p]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
