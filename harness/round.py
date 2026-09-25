#!/usr/bin/env python3
"""One round, ONE command — build, render, measure, and pre-check.

    python3 harness/round.py <outdir> rN --spec a.json [b.json]
                             [--prev rM] [--gate ID|PUNCH] [--brief brief.md]

WHY THIS EXISTS. A round used to be five or six separate commands: build, then
a silhouette pass, then a measure pass, then roundcheck --preflight, then (after the
read) --record and --check. Each of those is a TURN, and a turn is the unit
that actually costs money here — every one re-reads the whole conversation so
far, which keeps growing, so the same command issued at round 20 costs several
times what it cost at round 3.

Split across separate commands, the measure phase is most of a run's round
trips. The tools themselves are trivial — a compile is 1.4s and a view 0.5s —
so the machine is never the bottleneck. The round trips are.

This collapses the whole measure phase into one invocation and prints ONE
consolidated report. Give it TWO specs and it treats them as card 01 §4b's two
poles, building each into out/rN/vK/ and judging the round by the better of
them. Give it one spec and it is an ordinary repair round.

AT r1 IT ALSO CHECKS THE BRIEF, because r1 is the last moment anything there is
cheap to change. Two things, both from harness/brief.py: every slot a later
stage actually reads is filled in, and the two poles are really two designs
rather than one design built twice. The second one exists because of a failure
mode with teeth — r1, r2 and r3 come out as three separate rounds of one design,
0.08 to 0.20 apart on the mass-layout ruler when two different creatures are
typically 0.63 apart, and nobody compares any of them until r4. Three builds,
three renders, three turns, zero comparisons.

Python and stdlib only, so it behaves the same on Windows, macOS and Linux —
the harness ships to other people and cannot assume a shell.
"""
import sys, os, json, subprocess, shutil, itertools

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brief as briefmod

H = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(H)


def run(cmd):
    # Run from the CALLER's directory, with the tools addressed absolutely: the
    # spec, glb and outdir paths the user typed are relative to where they
    # stand. This used to run with cwd=<repo root>, so any relative path from
    # anywhere else failed with the engine's ENOENT stack trace.
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or '') + (p.stderr or '')


def die(msg, code=2):
    print('BLOCK: ' + msg)
    sys.exit(code)


def find_brief(outdir):
    for d in (outdir, os.path.dirname(os.path.abspath(outdir)), '.'):
        p = os.path.join(d, 'brief.md')
        if os.path.isfile(p):
            return p
    return None


def main():
    a = sys.argv[1:]
    if len(a) < 3 or '--spec' not in a:
        print(__doc__)
        return 2
    outdir, rn = a[0], a[1]
    si = a.index('--spec')
    # everything after --spec until the next flag
    specs = []
    for x in a[si + 1:]:
        if x.startswith('--'):
            break
        specs.append(x)
    if not specs:
        die('--spec needs at least one spec file')
    prev = None
    if '--prev' in a:
        prev = a[a.index('--prev') + 1]
    gate = a[a.index('--gate') + 1] if '--gate' in a else 'ID'
    brief_path = a[a.index('--brief') + 1] if '--brief' in a else find_brief(outdir)
    first = rn.lower() in ('r1', 'r01')

    # ── the brief, before anything is built on it ──────────────────────────
    # r1 only. Presence, never content: any height, any identity, any palette
    # passes — a BLANK does not, and only for the slots a later stage reads.
    facts = {}
    if first:
        print('brief')
        print('-' * 64)
        if not brief_path:
            die('no brief.md found (looked next to the spec, in ' + outdir +
                ', and in the working directory). Card 01 §2 fills nine slots '
                'before anything is built; pass --brief <path> if it lives '
                'somewhere else. This is the cheapest place in the whole run to '
                'fix any of them.')
        blocks, notes, facts = briefmod.check(brief_path, specs[0])
        if briefmod.report(blocks, notes, facts, 'brief') != 0:
            print()
            die('fix the brief first — every one of those is a text edit now and '
                'a rebuilt creature later.')
        print()

    rdir = os.path.join(outdir, rn)
    os.makedirs(rdir, exist_ok=True)
    multi = len(specs) > 1
    prev_dir = os.path.join(outdir, prev) if prev else None
    if prev_dir and not os.path.isdir(prev_dir):
        print(f'note: --prev {prev} does not exist yet; iou_vs_prev will be null '
              f'and the tweak detector is blind for this round.')
        prev_dir = None

    rows = []
    for i, spec in enumerate(specs):
        tag = f'v{i + 1}' if multi else None
        dest = os.path.join(rdir, tag) if tag else rdir
        os.makedirs(dest, exist_ok=True)
        glb = os.path.join(dest, 'creature.glb')

        rc, out = run(['node', os.path.join(R, 'engine', 'cli.js'), spec, glb])
        blocks = [l for l in out.splitlines() if l.startswith('BLOCK:')]
        if rc != 0:
            print(f'--- {tag or rn}: BUILD REFUSED ({spec})')
            for b in blocks or out.strip().splitlines()[-3:]:
                print('    ' + b)
            rows.append({'tag': tag or rn, 'built': False})
            continue
        # the compiler's own narration is worth seeing once, not five times
        shade = [l for l in out.splitlines() if 'shade class' in l or l.startswith('info: shade')]

        # Silhouettes come from the GEOMETRY, not from a browser. Same camera,
        # same masks (verified against the rendered ones at IoU 0.980-0.989 on
        # all four views; the remainder is the renderer's antialiased edge), and
        # no Chromium in the LOW loop at all.
        cmd = ['python3', os.path.join(H, 'outline.py'), glb, dest]
        if prev_dir:
            cmd += ['--prev', prev_dir]
        rc2, out2 = run(cmd)
        if rc2 != 0:
            print(f'--- {tag or rn}: silhouette failed')
            print('    ' + (out2.strip().splitlines() or [''])[-1][:160])
            rows.append({'tag': tag or rn, 'built': True, 'rendered': False})
            continue

        m = {}
        mp = os.path.join(dest, 'metrics.json')
        if os.path.exists(mp):
            try:
                m = json.load(open(mp, encoding='utf-8'))
            except Exception:
                pass
        thin = m.get('thinnest_px48')
        if thin is None:
            vals = [v.get('thinnest_px48') for v in m.values()
                    if isinstance(v, dict) and v.get('thinnest_px48') is not None]
            thin = min(vals) if vals else None
        rows.append({'tag': tag or rn, 'built': True, 'rendered': True,
                     'spec': spec, 'iou': m.get('iou_vs_prev'), 'thin': thin,
                     'shade': shade, 'metrics': m})

    # ── one report ─────────────────────────────────────────────────────────
    print()
    print(f'round {rn} — {len(specs)} attempt(s)')
    print('-' * 64)
    for r in rows:
        if not r.get('rendered'):
            print(f"  {r['tag']:<4} {'build refused' if not r.get('built') else 'render failed'}")
            continue
        iou = 'n/a' if r['iou'] is None else f"{r['iou']:.3f}"
        thin = 'n/a' if r['thin'] is None else f"{r['thin']:.1f}px"
        note = ''
        if r['thin'] is not None and r['thin'] < 3.0:
            note = '  <- thinnest feature is invisible at reading size'
        elif r['iou'] is not None and r['iou'] > 0.85:
            note = '  <- barely moved from the previous round'
        print(f"  {r['tag']:<4} iou {iou:<7} thinnest {thin:<8}{note}")
    good = [r for r in rows if r.get('rendered')]
    if not good:
        die('no attempt in this round produced a silhouette — nothing to read.')

    if rows and rows[0].get('shade'):
        print()
        for l in rows[0]['shade']:
            print('  ' + l)

    # ── are these really two poles, or one idea built twice? ───────────────
    # Checked on the identity view, because that is the ONE image each pole is
    # shown to the reader as. iou cannot answer this: it counts overlapping
    # pixels, so a proportion change moves it a long way while the design stands
    # still — the failing r1-r3 scored iou 0.609 and 0.703 and were the same
    # creature three times.
    if multi and len(good) > 1:
        view = facts.get('identity_view') if first else None
        pairs = [(x, y, briefmod.poles_apart(x['metrics'], y['metrics'], view)[0])
                 for x, y in itertools.combinations(good, 2)]
        pairs = [p for p in pairs if p[2] is not None]
        if pairs:
            print()
            worst = min(pairs, key=lambda p: p[2])
            for x, y, d in sorted(pairs, key=lambda p: p[2]):
                print(f'  {x["tag"]} vs {y["tag"]}: mass-layout distance {d:.2f}'
                      + ('' if d >= briefmod.POLE_MIN else '   <- the same design twice'))
            for r in good:
                f = briefmod.fill_of(r['metrics'], view)
                if f is not None and f >= briefmod.FILL_BLOB:
                    print(f'  note  {r["tag"]} fills {f:.2f} of its own box — that is a '
                          f'blob, not a pose; something has folded flat onto the body.')
            if worst[2] < briefmod.POLE_MIN:
                print()
                die(f'{worst[0]["tag"]} and {worst[1]["tag"]} are {worst[2]:.2f} apart and '
                    f'{briefmod.POLE_MIN:.2f} is the floor. Do not spend a reader on them: '
                    f'shown two versions of one design, a reader tells you what it would '
                    f'have told you about either. Name the axis — coiled/released, '
                    f'reared/flattened, front-loaded/rear-loaded — and push BOTH ends of '
                    f'it. Moving the signature part is usually enough; folding it flat '
                    f'onto the body is not a pose, it is a blob.', 1)

    print()
    rc3, out3 = run(['python3', os.path.join(H, 'roundcheck.py'),
                     outdir, '--preflight', rn, gate])
    print(out3.rstrip())
    if rc3 != 0:
        print()
        print('  -> do NOT spawn a reader. Change the shape and run this again.')
        return 1
    print()
    def thumbs_of(d):
        return sorted(os.path.join(d, f) for f in os.listdir(d)
                      if f.endswith('_thumb48.png'))
    if multi:
        # ONE image per pole: the identity view. Everything the other views were
        # shown for is computed above, from the geometry. Card 01 §4b.
        print('  -> show these to ONE reader, shuffled, with a canary')
        print('     (identity view only — the other views are measured, not read):')
        # The brief NAMES the view that carries the creature, and Gate 1 requires
        # that view to be one of the ones that read — so it is the view each pole
        # is shown as. Falling back to hero when the brief did not say was a bug:
        # a creature whose identity view is "side" was being read on its hero.
        want = facts.get('identity_view') or 'hero'
        for r in good:
            ts = thumbs_of(os.path.join(rdir, r['tag']))
            pick = next((t for t in ts if want in os.path.basename(t)), None) \
                or next((t for t in ts if 'hero' in t), None) or (ts[0] if ts else None)
            if pick:
                print(f'       {pick}   ({want} — the brief\'s identity view)')
        print('  -> then copy the winner up:  python3 harness/round.py '
              f'{outdir} {rn} --promote vK')
    else:
        print('  -> show these to ONE reader, shuffled, with a canary:')
        for t in thumbs_of(rdir):
            print(f'       {t}')
    print(f'  -> then:  python3 harness/roundcheck.py {outdir} --record {rn} {gate} '
          f'pass|fail "<noun>"')
    return 0


def promote(outdir, rn, tag):
    """Make one variant THE output of its round, so the iou chain follows it."""
    rdir = os.path.join(outdir, rn)
    src = os.path.join(rdir, tag)
    if not os.path.isdir(src):
        die(f'{src} does not exist')
    for f in os.listdir(src):
        s, d = os.path.join(src, f), os.path.join(rdir, f)
        if os.path.isfile(s):
            shutil.copy2(s, d)
    print(f'[round] promoted {tag} to {rn} — the next round\'s --prev is this shape.')
    return 0


if __name__ == '__main__':
    if '--promote' in sys.argv:
        i = sys.argv.index('--promote')
        sys.exit(promote(sys.argv[1], sys.argv[2], sys.argv[i + 1]))
    sys.exit(main())
