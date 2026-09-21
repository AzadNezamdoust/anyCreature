#!/usr/bin/env python3
"""The identity verdict, weighted and counted — not argued.

    python3 harness/identity.py --brief brief.md --round 1 \\
            --guesses side="t-rex,dinosaur,velociraptor,dragon,lizard" \\
                      hero="four-legged animal,dog,goat,boar,bear"

You hand over THE WORDS THE READER SAID, in order. This tool decides whether any
of them is the creature, by matching against the accepted list the brief wrote
down before any money was spent.

IT USED TO ASK YOU FOR THE RANK, and that was a hole straight through iron law 2.
The rank depends on one judgment — "does "hound" count as "wolf"?" — and the only
party available to make it was the party being graded. The accepted list was
already in the brief and nothing compared against
it. Now the machine compares.

Widening the list is still allowed and still the designer's call. It just has to
happen in the BRIEF, in writing, before the geometry exists — not here, after
four rounds have been paid for and there is a shape to defend.

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
confidence as much as the creature's clarity — a read can name the target inside
a hedged list ("a generic bat/moth/gargoyle silhouette": the ordered noun IS in
that sentence), and a creature can take several rounds to move from "in the list"
to "first". Recognition is not binary and this scores it as what it is.
"""
import sys, os, re

MAX_RANK = 4


def norm(s):
    return re.sub(r'[^a-z0-9 ]+', ' ', s.lower()).strip()


def accepted_from_brief(path):
    """The identity slot's noun plus every synonym it declared, normalised."""
    txt = open(path, encoding='utf-8').read()
    for line in txt.splitlines():
        s = line.strip()
        if not s.startswith('|'):
            continue
        cells = [c.strip() for c in s.strip('|').split('|')]
        if len(cells) < 2 or norm(cells[0]) != 'identity':
            continue
        val = cells[1]
        m = re.search(r'reads as\s*[:：]?\s*\**([^*|(]+)', val, re.I)
        noun = (m.group(1) if m else val).strip().strip('*` ')
        syn = []
        ms = re.search(r'\(([^)]*)\)', val)
        if ms:
            # longest alternative first, or "synonyms accepted:" leaves "accepted"
            # behind as a word and the list quietly gains a member nobody wrote
            body = re.sub(r'^\s*(?:synonyms?\s+accepted|accepted\s+synonyms?|synonyms?|accept(?:ed)?|also)\s*[:：]?',
                          '', ms.group(1), flags=re.I)
            syn = [x.strip() for x in re.split(r'[,、/]', body) if x.strip()]
        out, seen = [], set()
        for w in [noun] + syn:
            n = norm(w)
            if n and n not in seen:
                seen.add(n)
                out.append(n)
        return noun.strip(), out
    return None, []


def rank_of(guess_list, accepted):
    """1-based position of the first guess that IS one of the accepted words.

    A guess is often a phrase — "crouching four-legged animal (dog/boar)" — so an
    accepted word counts when it appears in the phrase as a whole word. Nothing
    looser than that: "boarhound" is not "boar", and "bison" is not "buffalo"
    unless the brief said so."""
    for i, g in enumerate(guess_list, 1):
        gn = ' ' + norm(g) + ' '
        for a in accepted:
            if ' ' + a + ' ' in gn:
                return i, a
    return None, None


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


def collect(a, flag):
    out = {}
    if flag not in a:
        return out
    for x in a[a.index(flag) + 1:]:
        if x.startswith('--'):
            break
        if '=' not in x:
            print(f'BLOCK: "{x}" should look like  side=...  ')
            sys.exit(2)
        k, v = x.split('=', 1)
        out[k] = v
    return out


def main():
    a = sys.argv[1:]
    if '--ranks' not in a and '--guesses' not in a:
        print(__doc__)
        return 2
    rnd = int(a[a.index('--round') + 1]) if '--round' in a else 1
    brief = a[a.index('--brief') + 1] if '--brief' in a else None
    noun, accepted = (None, [])
    if brief:
        if not os.path.exists(brief):
            print(f'BLOCK: no brief at {brief}')
            return 2
        noun, accepted = accepted_from_brief(brief)
        if not accepted:
            print('BLOCK: the brief has no identity slot, so there is nothing to match '
                  'against. Fix the brief (harness/brief.py will tell you how).')
            return 2

    # ── the judgment is not yours ────────────────────────────────────────────
    if '--guesses' in a:
        if not brief:
            print('BLOCK: --guesses needs --brief. The accepted words live in the brief, '
                  'written down before the geometry existed; that is the whole point.')
            return 2
        said = collect(a, '--guesses')
        if not said:
            print('BLOCK: --guesses needs at least one view, e.g. side="a,b,c,d,e"')
            return 2
        ranks, matched, verbatim = {}, {}, {}
        for v, blob in said.items():
            gs = [g.strip() for g in blob.split(',') if g.strip()][:MAX_RANK + 1]
            verbatim[v] = gs
            k, hit = rank_of(gs, accepted)
            ranks[v] = k
            matched[v] = hit
        passed, carried, lines = verdict(ranks, rnd)
        print(f'identity r{rnd} — accepted: {", ".join(accepted)}')
        for v, gs in verbatim.items():
            k = ranks[v]
            tail = (f'guess {k} = "{matched[v]}"' if k else 'nothing accepted')
            print(f'    {v:<7} {tail}')
            print(f'            reader said: {", ".join(gs)}')
        print()
        for r, got, need, ok, hit in lines:
            print(f'  {"✓" if ok else " "} rank {r}: {got} view(s) at {r} or better, needs {need}'
                  + (f'  [{", ".join(hit)}]' if hit else ''))
        print()
        if passed:
            print(f'PASS — carried at rank {carried}.')
            print(f'  record it:  roundcheck.py <out> --record r{rnd} ID pass '
                  f'"{noun} (rank {carried})"')
            return 0
        near = sorted({g for gs in verbatim.values() for g in gs})[:8]
        print(f'FAIL — none of the accepted words reached a rank in enough views.')
        print()
        print('  WHAT THE READERS ACTUALLY SAID: ' + ', '.join(near))
        print(f'  WHAT THE BRIEF WILL ACCEPT:     {", ".join(accepted)}')
        print()
        print('  If one of those words genuinely IS the creature you ordered, that is a')
        print('  decision about the ORDER, and it is made in the brief — add the word to')
        print('  the identity slot and say why in the closing DEVLOG. You may not add it')
        print('  here. This tool exists because the party being graded kept making that')
        print('  call for itself, and the brief already had the answer written down.')
        print()
        print('  Otherwise the verdict IS the work order: repair the BIG masses, and')
        print('  remember a repair must clear roundcheck\'s minimum change.')
        print(f'  record it:  roundcheck.py <out> --record r{rnd} ID fail "<what they saw>"')
        return 1

    if brief:
        print('BLOCK: --ranks says WHERE you decided the noun landed. With a brief on')
        print('  disk there is no reason to decide it — pass the reader\'s words instead:')
        print('     --guesses side="first,second,third,fourth,fifth"')
        return 2
    print('WARN: no --brief, so the synonym judgment is yours and nothing checked it.')
    print('      This is the hole iron law 2 exists to close. Pass --brief.')
    print()
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
