#!/usr/bin/env python3
"""Round gatekeeper — iron law 3, taken out of the session's own hands.

usage:
  python3 harness/roundcheck.py <outdir> --preflight rN ID|PUNCH   BEFORE spawning the reader
  python3 harness/roundcheck.py <outdir> --record rN ID|PUNCH pass|fail "<reader's noun>"
  python3 harness/roundcheck.py <outdir> --check  ID|PUNCH         after recording

Law 2 exists because a session cannot grade its own thumbnails. Law 3 —
"same symptom failed twice = no third tweak" — has exactly the same problem and
was left to the session to apply to itself, so it did not hold: one measured run
spent rounds 6 through 15 nudging the same head and the same ears eight times
before restarting the concept at r16, and eight of those rounds bought nothing.
The rule was right; nobody was counting.

This counts. It reads what the round actually produced rather than what the
session says it did:

  · the verdict, from out/rN/round.json (written by --record; no record means
    the round did not happen and the next check refuses to pass it)
  · whether the round was a TWEAK or a real restart, from iou_vs_prev in
    out/rN/metrics.json — a nudged silhouette stays >0.85 similar to the last
    one no matter what the session calls it. Run silmetrics with
    `--prev out/r<N-1>` or this number is null and the guard is blind.
  · whether the feature being argued about is even visible at reading size,
    from thinnest_px48 — the blind read happens on a 48px thumbnail.

Exit 1 with a BLOCK: line = the next round may not be another tweak.
"""
import sys, os, json, glob, re

TWEAK_IOU = 0.85      # above this, the silhouette did not really change
RESTART_IOU = 0.70    # a repair after an IDENTITY failure must clear this
MIN_PX48 = 3.0        # thinner than this cannot be read at thumbnail size
MAX_TWEAKS = 2        # iron law 3: two failures, then no third tweak
MAX_FAILS_TOTAL = 5   # hard ceiling per gate, counted regardless of iou

# Two different bars, for two different situations, and the gap between them is
# the point.
#
# TWEAK_IOU is the nudge detector: above 0.85 the shape did not really move, and
# law 3 refuses a third of those. RESTART_IOU is a FLOOR on a repair, and it only
# applies to the identity gate after a reader has failed it. The reason they
# differ: "a fox, not a dragon" is not a fine-tuning verdict. Nothing between
# 0.70 and 0.85 — a moved ear, a longer tail — changes what a stranger calls the
# animal, so a repair in that band is a round spent to be told the same noun
# again.
#
# The number is enforceable now because `outline.py` computes iou from the
# geometry rather than from a rasterised picture, so it is exact and free.

# Why the hard ceiling exists on top of the nudge detector. The detector walks
# backwards and STOPS at the first round whose silhouette really moved, on the
# theory that a real change is a fresh start deserving a fresh count. A measured
# run defeated that without trying: rounds 5–9 each moved one variable — claw
# height, then tail angle, then leg thickness — and the sizes of those moves
# alternated, so one of them always scored under the threshold and reset the
# streak. Eleven rounds on one gate, and the counter never reached three.
#
# iou is a good detector of "did the shape move". It is a bad detector of "is
# this a different idea", and only the second one is what law 3 is about. So the
# streak logic stays for what it is good at, and a plain total — which nothing
# can alternate its way around — carries the rest. The card budgets 2 repair
# rounds; 5 leaves room for one honest concept restart and refuses the eleventh.


def rounds(outdir):
    out = []
    for d in sorted(glob.glob(os.path.join(outdir, 'r*')),
                    key=lambda p: int(re.sub(r'\D', '', os.path.basename(p)) or 0)):
        if not os.path.isdir(d):
            continue
        r = {'dir': d, 'n': int(re.sub(r'\D', '', os.path.basename(d)) or 0),
             'round': None, 'metrics': None}
        for key, fn in (('round', 'round.json'), ('metrics', 'metrics.json')):
            p = os.path.join(d, fn)
            if os.path.exists(p):
                try:
                    r[key] = json.load(open(p, encoding='utf-8'))
                except Exception:
                    pass
        out.append(r)
    return out


def iou_of(m):
    """metrics.json is either the silmetrics shape (flat) or the maskmetrics
    shape (keyed by image name). Only silmetrics computes iou_vs_prev."""
    if not isinstance(m, dict):
        return None
    if 'iou_vs_prev' in m:
        return m['iou_vs_prev']
    for v in m.values():
        if isinstance(v, dict) and 'iou_vs_prev' in v:
            return v['iou_vs_prev']
    return None


def thinnest_of(m):
    if not isinstance(m, dict):
        return None
    vals = []
    if 'thinnest_px48' in m and m['thinnest_px48'] is not None:
        vals.append(m['thinnest_px48'])
    for v in m.values():
        if isinstance(v, dict) and v.get('thinnest_px48') is not None:
            vals.append(v['thinnest_px48'])
    return min(vals) if vals else None


def record(outdir, rn, gate, verdict, noun):
    d = os.path.join(outdir, rn)
    os.makedirs(d, exist_ok=True)
    rec = {'round': rn, 'gate': gate, 'verdict': verdict, 'reader_noun': noun}
    json.dump(rec, open(os.path.join(d, 'round.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f'[roundcheck] recorded {rn}: {gate} {verdict} — reader said "{noun}"')


def variant_metrics(rdir):
    """metrics.json for each variant of a round: out/rN/v*/metrics.json."""
    out = []
    for d in sorted(glob.glob(os.path.join(rdir, 'v*'))):
        p = os.path.join(d, 'metrics.json')
        if os.path.isdir(d) and os.path.exists(p):
            try:
                out.append(json.load(open(p, encoding='utf-8')))
            except Exception:
                pass
    return out


def preflight(outdir, rn, gate):
    """Is this round worth a reader AT ALL? Run BEFORE spawning one.

    The order used to be: spend the reader, record what it said, then ask
    whether another round was allowed. So the thing that stops waste sat AFTER
    the thing that costs money, and a round that could never have read
    differently still paid full price for being told so.

    A reader is not free, and its price is almost entirely the cost of the
    subagent EXISTING rather than the pictures inside it.

    Two ways a read is knowably wasted before it happens, and both are facts
    the machine already has:
      · the silhouette is the one that was rejected last round. A reader that
        said "Horse" to a shape is going to say "Horse" to the same shape.
      · the thing being argued about is under 3px at reading size, twice
        running. Nobody can see it, so nobody can report on it.
    """
    rs = rounds(outdir)
    cur = next((r for r in rs if os.path.basename(r['dir']) == rn), None)
    if cur is None:
        print(f'[roundcheck] {rn} has no directory yet — nothing to pre-check.')
        return 0

    # the most recent recorded FAILURE on this gate, before this round
    prev_fail = None
    for r in rs:
        if r is cur:
            break
        rec = r['round']
        if rec and rec.get('gate') == gate and rec.get('verdict') == 'fail':
            prev_fail = r

    problems, notes_thin = [], []
    # A repair round builds three variants (card 01 §4b), so "this round's
    # silhouette" is not one file — it is whichever variant is least like the
    # shape that was already rejected. Judge the round by its BEST attempt:
    # blocking a round because two of its three tries were near-copies would
    # punish exactly the behaviour this is meant to encourage.
    ious = [iou_of(v) for v in variant_metrics(cur['dir'])]
    ious = [i for i in ious if i is not None]
    own = iou_of(cur['metrics'])
    if own is not None:
        ious.append(own)
    iou = min(ious) if ious else None
    nvar = len(variant_metrics(cur['dir']))
    if nvar:
        print(f'[roundcheck] {rn} has {nvar} variant(s); judging the round by its '
              f'least-similar one (iou {iou}).')

    bar = RESTART_IOU if gate.upper() == 'ID' else TWEAK_IOU
    if prev_fail is not None and iou is not None and iou > bar:
        pn = os.path.basename(prev_fail['dir'])
        noun = prev_fail['round'].get('reader_noun', '?')
        if gate.upper() == 'ID':
            problems.append(
                f'do not spend a reader on {rn}: its best attempt is still {iou} similar to '
                f'{pn}, which a reader called "{noun}". An IDENTITY repair has to clear '
                f'{RESTART_IOU} — a reader is naming the ANIMAL, and nothing in the '
                f'{RESTART_IOU}-{TWEAK_IOU} band (a moved ear, a longer tail) changes which '
                f'animal a stranger says. Move the big masses: proportion, stance, the '
                f'signature part\'s size relative to the body.')
        else:
            problems.append(
                f'do not spend a reader on {rn}: its silhouette is {iou} similar to {pn}, '
                f'which a reader has ALREADY rejected ("{noun}"). The same shape gets the '
                f'same answer, and a read costs tokens to be told so. Change the shape '
                f'first, then read it.')

    # same for legibility: the round is as legible as its most legible attempt
    ts = [thinnest_of(v) for v in variant_metrics(cur['dir'])]
    ts = [x for x in ts if x is not None]
    own_t = thinnest_of(cur['metrics'])
    if own_t is not None:
        ts.append(own_t)
    t = max(ts) if ts else None
    prev_t = thinnest_of(prev_fail['metrics']) if prev_fail is not None else None
    # thinnest_px48 NO LONGER BLOCKS. It was a gate; it is now a note, and the
    # reason is a measurement, not a change of mind. Run across every creature
    # this harness has ever shipped: 10 of 10 come in under the 3px bar on at
    # least one view, including one that a blind reader named at rank 1, first
    # guess, unprompted. A bar nothing has ever passed is not measuring quality,
    # it is measuring the fact that a 48px thumbnail of a four-limbed animal has
    # thin limbs. On one measured build it refused EIGHT readers, the session
    # thickened a different feature each time, and the file that finally shipped
    # still measures 0.8-1.8px. Eight round-trips, no change in the outcome —
    # and worse, "thicken it" is the wrong instruction for a creature whose idea
    # IS a thin thing: that build's signature was a rib CAGE, and thickening the
    # bars until they passed closed the cage into a solid lump.
    if t is not None and t < MIN_PX48:
        notes_thin.append(
            f'thinnest feature is {t} px at reading size. The reader may not resolve it — '
            f'worth knowing, not worth a round. Every creature on the shelf ships under '
            f'this number; do NOT thicken a feature whose thinness is the design.')

    if iou is None and cur['n'] > 1:
        print('[roundcheck] iou_vs_prev is null — run silmetrics with `--prev out/r<N-1>` '
              'or this pre-check is blind and every round pays for its reader.')

    for n in notes_thin:
        print('  note   ' + n)
    for p in problems:
        print('BLOCK: ' + p)
    if not problems:
        print(f'[roundcheck] {rn} is worth reading — spawn the reader.')
    return 1 if problems else 0


def check(outdir, gate):
    rs = rounds(outdir)
    if not rs:
        print(f'[roundcheck] no rounds under {outdir}/ yet — first build, nothing to enforce.')
        return 0

    latest = rs[-1]
    problems, notes = [], []

    # ── legibility, on the newest round — INFORMATION, never a gate ────────
    # This used to advise once and block on the second consecutive reading. It
    # was wrong, and the measurement that says so is simple: run the number over
    # every creature this harness has ever shipped and 10 of 10 are under the
    # bar on at least one view. Nothing has ever passed it. One shipped build
    # was refused a reader EIGHT times over it, thickened a different feature
    # each time, and still measures 0.8-1.8px in the delivered file — while its
    # blind reader named the creature at rank 1, first guess, from a view whose
    # thinnest feature was 1.8px.
    #
    # It also gives the wrong instruction when the design IS thin. That build's
    # signature was a rib CAGE; "thicken it" closed the bars into a solid lump
    # and the idea died to satisfy a number no creature has ever satisfied.
    t = thinnest_of(latest['metrics'])
    prev_t = thinnest_of(rs[-2]['metrics']) if len(rs) > 1 else None
    if t is not None:
        if t < MIN_PX48:
            notes.append(f'thinnest feature is {t} px at reading size. The reader may not '
                         f'resolve it. Every creature on the shelf ships under this number, '
                         f'so it is information, not a verdict — and do NOT thicken a feature '
                         f'whose thinness is the design.')
        else:
            notes.append(f'thinnest feature {t} px at reading size — readable.')

    # ── iron law 3, counted ────────────────────────────────────────────────
    # walk backwards over rounds of THIS gate until a pass or a real restart
    streak, blind = [], False
    for r in reversed(rs):
        rec = r['round']
        if rec is None:
            continue
        if rec.get('gate') != gate:
            continue
        if rec.get('verdict') == 'pass':
            break
        iou = iou_of(r['metrics'])
        if iou is None:
            # round 1 has nothing to compare against — that is not a blind spot,
            # it is the start. Only a later round with a null iou means --prev
            # was forgotten.
            if r['n'] > 1:
                blind = True
        elif iou <= TWEAK_IOU:
            streak.append((r, iou))     # a real change — count it and stop
            break
        streak.append((r, iou))

    # the plain total: every recorded failure on this gate since the last pass,
    # with no opinion about whether the shape moved
    total_fails, seen_pass = 0, False
    for r in reversed(rs):
        rec = r['round']
        if rec is None or rec.get('gate') != gate:
            continue
        if rec.get('verdict') == 'pass':
            seen_pass = True
            break
        total_fails += 1
    if total_fails:
        notes.append(f'{gate} round budget: {total_fails} failed round(s) so far'
                     f'{"" if seen_pass else " (none passed yet)"} — the card budgets 2 '
                     f'repairs, the hard ceiling is {MAX_FAILS_TOTAL}.')
    if total_fails >= MAX_FAILS_TOTAL:
        problems.append(
            f'round ceiling: {gate} has now failed {total_fails} times. The card budgets TWO '
            f'repair rounds and allows one concept restart after that; {MAX_FAILS_TOTAL} is the '
            f'ceiling and you are at it. Whatever this is, it is not converging — and every '
            f'further round costs more than the one before it, because the context it rides on '
            f'keeps growing. Ship your best version of this gate and write one honest DEVLOG '
            f'line about what did not land.')

    fails = len(streak)
    if fails:
        shown = ', '.join(f"{os.path.basename(r['dir'])}"
                          f"{'' if i is None else f' (iou {i})'}" for r, i in reversed(streak))
        notes.append(f'{gate} has failed {fails} time(s) in a row: {shown}')

    if blind:
        problems.append('iou_vs_prev is null — silmetrics was run without `--prev out/r<N-1>`, '
                        'so the tweak detector is switched off and law 3 cannot be enforced. '
                        'Re-run the measure step with --prev.')

    if fails >= MAX_TWEAKS and not blind:
        nudges = [i for _, i in streak if i is not None and i > TWEAK_IOU]
        if len(nudges) >= MAX_TWEAKS:
            problems.append(
                f'iron law 3: {gate} has failed {fails} times and every one of those rounds left the '
                f'silhouette more than {TWEAK_IOU} similar to the round before it (iou '
                f'{", ".join(str(n) for n in reversed(nudges))}) — that is the same shape nudged, not a '
                f'different answer tried. A third tweak is not allowed. Restart this view or element '
                f'from a DIFFERENT concept; if the restart also fails, ship your best version and write '
                f'one honest DEVLOG line.')

    for n in notes:
        print(f'[roundcheck] {n}')
    for p in problems:
        print(f'BLOCK: {p}')
    if not problems:
        print(f'[roundcheck] OK — another repair round on {gate} is allowed.')
    return 1 if problems else 0


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__)
        return 2
    outdir = a[0]
    if a[1] == '--record':
        if len(a) < 6:
            print('usage: roundcheck.py <outdir> --record rN ID|PUNCH pass|fail "<noun>"')
            return 2
        record(outdir, a[2], a[3], a[4], a[5])
        return 0
    if a[1] == '--preflight':
        if len(a) < 3:
            print('usage: roundcheck.py <outdir> --preflight rN ID|PUNCH')
            return 2
        return preflight(outdir, a[2], a[3] if len(a) > 3 else 'ID')
    if a[1] == '--check':
        return check(outdir, a[2] if len(a) > 2 else 'ID')
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
