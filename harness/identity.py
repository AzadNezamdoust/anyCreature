#!/usr/bin/env python3
"""The identity verdict, weighted and counted — not argued.

    python3 harness/identity.py --round 1 --noun scorpion \\
            --ranks front=none side=2 top=2 hero=1

Each view's rank is WHERE the brief's noun appeared in that reader's ranked
guesses (1 = its first guess), or `none` if it was not in the list at all.
Synonyms count as the noun; that judgment is yours, and it is the only one this
tool leaves you.

THE RULE. A rank of R passes if the noun reached R in at least R views:

    rank 1 in 1 view        one reader's FIRST guess is the creature — done
    rank 2 in 2 views       agreement at second place
    rank 3 in 3 views       broad agreement, weakly
    rank 4 in 4 views       every view has it somewhere in four — the floor

Rank 5 and beyond does not count. A noun that never gets above fifth is not
being recognised, it is being listed.

AND IT LOOSENS EACH ROUND. The required number of views drops by one per repair
round (never below one), because the cost of another round rises while the
information it buys does not:

    round 1     rank1:1  rank2:2  rank3:3  rank4:4
    round 2     rank1:1  rank2:1  rank3:2  rank4:3
    round 3     rank1:1  rank2:1  rank3:1  rank4:2

WHY WEIGHTED AT ALL. The bar used to be one word, exactly right. A 48px
silhouette is a genuinely ambiguous object, and that bar measured the reader's
confidence as much as the creature's clarity. A reader will answer "a generic
bat/moth/gargoyle silhouette" with the ordered noun sitting INSIDE that
sentence, and a one-word bar throws the whole read away. Recognition is not
binary and this scores it as what it is.
"""
import sys

MAX_RANK = 4


def needed(rank, rnd):
    """Views required at this rank, for this round."""
    return max(1, rank - (rnd - 1))


def verdict(ranks, rnd):
    """ranks: {view: int|None}. Returns (passed, rank_that_carried, detail)."""
    lines = []
    best = None
    for r in range(1, MAX_RANK + 1):
        hit = [v for v, k in ranks.items() if k is not None and k <= r]
        need = needed(r, rnd)
        ok = len(hit) >= need
        lines.append((r, len(hit), need, ok, hit))
        if ok and best is None:
            best = r
    return best is not None, best, lines


def main():
    a = sys.argv[1:]
    if '--ranks' not in a:
        print(__doc__)
        return 2
    rnd = int(a[a.index('--round') + 1]) if '--round' in a else 1
    noun = a[a.index('--noun') + 1] if '--noun' in a else 'the brief\'s noun'
    ranks = {}
    for x in a[a.index('--ranks') + 1:]:
        if x.startswith('--'):
            break
        if '=' not in x:
            print(f'BLOCK: "{x}" should look like  side=2  or  front=none')
            return 2
        v, k = x.split('=', 1)
        ranks[v] = None if k.lower() in ('none', 'no', '-', 'x') else int(k)
    if not ranks:
        print('BLOCK: --ranks needs at least one view')
        return 2

    passed, carried, lines = verdict(ranks, rnd)
    print(f'identity r{rnd} — "{noun}" across {len(ranks)} view(s)')
    for v, k in ranks.items():
        print(f'    {v:<7} {"not in the list" if k is None else f"guess {k}"}')
    print()
    for r, got, need, ok, hit in lines:
        mark = '✓' if ok else ' '
        print(f'  {mark} rank {r}: {got} view(s) at {r} or better, needs {need}'
              + (f'  [{", ".join(hit)}]' if hit else ''))
    print()
    if passed:
        note = ''
        if carried >= 3:
            note = ('  It reads, but not loudly — say so in the closing line.'
                    if carried == 3 else
                    '  This is the floor. It reads only just; the closing line should say so.')
        print(f'PASS — carried at rank {carried}.{note}')
        print(f'  record it:  roundcheck.py <out> --record r{rnd} ID pass "{noun} (rank {carried})"')
        return 0
    print(f'FAIL — "{noun}" did not reach any rank in enough views.')
    unread = [v for v in ('front', 'side', 'top', 'hero') if v not in ranks]
    if unread:
        print()
        print(f'  LOOK BEFORE YOU REBUILD. {len(unread)} view(s) of THIS shape have not been')
        print(f'  read yet: {", ".join(unread)}. Show them to one reader before you change')
        print('  a single number. Three more images inside one reader is a fraction of a')
        print('  round; a rebuild is a whole one, and it throws away a shape that may')
        print('  already work from another angle.')
        print('  Measured: a build failed on SIDE at r1 and r2, restarted the concept at')
        print('  r3, and at r5 its TOP view came back "a lizard, gecko, or SALAMANDER seen')
        print('  from above" — the ordered noun, first guess, unprompted. The creature was')
        print('  not wrong. The declared identity view was. Four reads and a concept')
        print('  restart to learn that, when one extra image would have said it at r1.')
        print('  If another view reads, CHANGE THE BRIEF\'s identity view and record why.')
        print()
    print('  The verdict IS the work order: repair the BIG masses, and remember a')
    print('  repair must clear roundcheck\'s minimum change or the next read is refused.')
    print(f'  record it:  roundcheck.py <out> --record r{rnd} ID fail "<what they saw instead>"')
    return 1


if __name__ == '__main__':
    sys.exit(main())
