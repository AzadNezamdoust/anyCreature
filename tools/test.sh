#!/bin/bash
# anyCreature self-check suite — exactly what CI runs.
#
#     bash tools/test.sh          # exit 0 = every check passed
#
# Run it after `bash setup.sh` (deps). Every step runs even when an earlier one
# fails, so one run shows everything that is broken; the exit code is non-zero
# if anything was. Nothing here touches the network, ~/.anyCreature.json, or the
# tracked tree: all output goes to a temp dir that is removed on exit.
#
# What it proves, in order:
#   1. the tree is consistent       synccheck.py (versions, promises, dead refs, leaks)
#   2. the rulers separate          calibrate.py (green builds, reds refused for their
#                                   own faults, colour ruler both ways)
#   3. the chain works end to end   engine -> outline -> judge -> glbcheck -> deliver/ship,
#                                   and every example/gallery spec builds with no BLOCK
#   4. every harness tool runs      on the example, with its failure paths exercised
#                                   where a wrong exit code would hide a real problem
set -u
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
T="$(mktemp -d 2>/dev/null || mktemp -d -t actest)"
trap 'rm -rf "$T"' EXIT

PASS=0; FAIL=0; FAILED=()
LOG="$T/log.txt"

# ok NAME CMD...     — the command must exit 0
ok() {
  local name="$1"; shift
  if "$@" >"$LOG" 2>&1; then
    PASS=$((PASS + 1)); echo "  ok    $name"
  else
    local rc=$?
    FAIL=$((FAIL + 1)); FAILED+=("$name"); echo "  FAIL  $name (exit $rc)"
    tail -n 15 "$LOG" | sed 's/^/        /'
  fi
}
# refuses NAME PATTERN CMD...  — the command must exit non-zero AND print PATTERN.
# A refusal that is really a crash (a traceback, an ENOENT) does not count.
refuses() {
  local name="$1" pat="$2"; shift 2
  "$@" >"$LOG" 2>&1; local rc=$?
  if [ "$rc" -ne 0 ] && grep -q -- "$pat" "$LOG" && ! grep -q "Traceback\|at Object\.<anonymous>" "$LOG"; then
    PASS=$((PASS + 1)); echo "  ok    $name"
  else
    FAIL=$((FAIL + 1)); FAILED+=("$name")
    echo "  FAIL  $name (exit $rc, wanted non-zero with \"$pat\")"
    tail -n 15 "$LOG" | sed 's/^/        /'
  fi
}
# prints NAME PATTERN CMD...   — exit 0 AND the output contains PATTERN
prints() {
  local name="$1" pat="$2"; shift 2
  if "$@" >"$LOG" 2>&1 && grep -q -- "$pat" "$LOG"; then
    PASS=$((PASS + 1)); echo "  ok    $name"
  else
    FAIL=$((FAIL + 1)); FAILED+=("$name"); echo "  FAIL  $name (wanted exit 0 with \"$pat\")"
    tail -n 15 "$LOG" | sed 's/^/        /'
  fi
}

echo "== 1. tree consistency"
ok      "synccheck"                       python3 harness/synccheck.py

echo "== 2. calibration"
prints  "calibrate: rulers separate"      "\[calibrate\] OK"  python3 harness/calibrate.py

echo "== 3. end-to-end chain on the example"
prints  "engine builds example"           '"ok":true'   node engine/cli.js example/wolf.json "$T/wolf.glb"
ok      "engine wrote its checks stamp"   test -s "$T/wolf.checks.json"
refuses "engine refuses a recoloured copy (example_copy)"  "example_copy" \
        bash -c "cp example/wolf.json '$T/copy.json' && node engine/cli.js '$T/copy.json' '$T/copy.glb'"
refuses "engine refuses a sausage (soft_mass)" "soft_mass" \
        bash -c "python3 - '$T/sausage.json' <<'PY' && node engine/cli.js '$T/sausage.json' '$T/sausage.glb'
import json, sys
s = json.load(open('calibration/wolf_green.json'))
# every profile row at the middle row's radius: tubes of one radius. Joints
# scaled so the example_copy check does not see wolf_green with its numbers moved.
for v in s['volumes']:
    r = v['profile'][len(v['profile']) // 2]
    v['profile'] = [[0, r[1], r[2]], [1, r[1], r[2]]]
for k, j in s['joints'].items():
    if isinstance(j, list): s['joints'][k] = [x * 1.12 for x in j]
    else:
        for a in ('up', 'fwd', 'side'):
            if a in j: j[a] *= 1.12
json.dump(s, open(sys.argv[1], 'w'))
PY"
# the gallery: every showcase spec must build with no BLOCK (the engine exits
# non-zero on one), and the GLB shipped beside it must still conform. The wolf
# is one quadruped; these are the proof that the engine generalises past it.
for g in example/gallery/*.json; do
  case "$g" in *.checks.json) continue ;; esac
  [ -e "$g" ] || continue
  n="$(basename "$g" .json)"
  prints "gallery builds, no BLOCK: $n"   '"ok":true'   node engine/cli.js "$g" "$T/gallery_$n.glb"
  ok     "glbcheck: shipped gallery $n.glb" node harness/glbcheck.mjs "example/gallery/$n.glb"
done
ok      "glbcheck: fresh build"           node harness/glbcheck.mjs "$T/wolf.glb"
ok      "glbcheck: shipped example/wolf.glb" node harness/glbcheck.mjs example/wolf.glb
# a cut file must be called CUT, not "bytes outside the declared file": that
# message sends the reader hunting for a smuggled payload that is not there
refuses "glbcheck: truncated in JSON is [truncated]" "\[truncated\].*inside the JSON chunk" \
        bash -c "head -c 4000 '$T/wolf.glb' > '$T/trunc.glb' && node harness/glbcheck.mjs '$T/trunc.glb'"
refuses "glbcheck: truncated in BIN is [truncated]" "\[truncated\].*inside the BIN chunk" \
        bash -c "head -c \$(( \$(wc -c < '$T/wolf.glb') - 64 )) '$T/wolf.glb' > '$T/trunc2.glb' && node harness/glbcheck.mjs '$T/trunc2.glb'"
refuses "glbcheck: appended bytes are [trailing_bytes]" "\[trailing_bytes\]" \
        bash -c "cat '$T/wolf.glb' > '$T/trail.glb' && printf 'PK' >> '$T/trail.glb' && node harness/glbcheck.mjs '$T/trail.glb'"
prints  "outline.py: 4 views"             "4 views"     python3 harness/outline.py "$T/wolf.glb" "$T/ol"
ok      "outline.py: hero shot"           python3 harness/outline.py "$T/wolf.glb" "$T/ol" --hero "$T/ol/hero.png"
ok      "outline.py wrote metrics + thumbs" test -s "$T/ol/metrics.json" -a -s "$T/ol/sil_side_thumb48.png" -a -s "$T/ol/hero.png"
prints  "judge.mjs: measure only"         "saturated area" node harness/judge.mjs "$T/wolf.glb" "$T/j" wolf
cat > "$T/claims.json" <<'EOF'
{"name": "suite", "claims": [
 {"type": "rig_skinned"}, {"type": "anim_named", "names": ["idle", "move"]},
 {"type": "part_exists", "part": "fur_body"}, {"type": "saturation_area", "view": "hero", "min": 0.10}]}
EOF
prints  "judge.mjs: claims pass"          "all claims pass" node harness/judge.mjs "$T/wolf.glb" "$T/j" wolf --spec "$T/claims.json"
sed 's/"idle", "move"/"idle", "fly"/' "$T/claims.json" > "$T/claims_fly.json"
refuses "judge.mjs: a missing clip blocks" "Missing named animation fly" \
        node harness/judge.mjs "$T/wolf.glb" "$T/j" wolf --spec "$T/claims_fly.json"
prints  "deliver.py: package"             "\[deliver\] done" \
        python3 harness/deliver.py "$T/wolf.glb" "$T/del" wolf --title "Suite Wolf" --gate "$T/wolf.checks.json"
ok      "deliver.py: stamped file conforms" node harness/glbcheck.mjs "$T/del/wolf.glb"
refuses "deliver.py: refuses a foreign GLB" "not built by this engine" \
        bash -c "python3 harness/wash.py '$T/wolf.glb' '$T/foreign.glb' >/dev/null && python3 - '$T/foreign.glb' <<'PY' && python3 harness/deliver.py '$T/foreign.glb' '$T/del2' x
import json, struct, sys
p = sys.argv[1]; d = open(p, 'rb').read()
jl, = struct.unpack('<I', d[12:16]); g = json.loads(d[20:20 + jl])
g['asset'] = {'version': '2.0', 'generator': 'someone else'}
js = json.dumps(g).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
out = b'glTF' + struct.pack('<II', 2, 0) + struct.pack('<II', len(js), 0x4E4F534A) + js + d[20 + jl:]
open(p, 'wb').write(out[:8] + struct.pack('<I', len(out)) + out[12:])
PY"
prints  "ship.py --help"                  "ONE command"  python3 harness/ship.py --help
prints  "ship.py: package only"           "not published" \
        python3 harness/ship.py "$T/wolf.glb" --name "Suite Wolf" --out "$T/ship"

echo "== 4. every harness tool"
ok      "gates.py"                        python3 harness/gates.py
prints  "gates.py LOW"                    "decidable before the build" python3 harness/gates.py LOW
prints  "gates.py --by dept"              "BY DEPARTMENT" python3 harness/gates.py --by dept
ok      "gates.py --by counts every check" bash -c "! python3 harness/gates.py --by kind | grep -q ' 0 of 0 '"
cat > "$T/brief.md" <<'EOF'
| Slot | Value |
|---|---|
| identity | reads as: wolf (accepted: dog, hound, canine) |
| feel | fast |
| height | 1.45 m |
| signature | the long muzzle — carried by the SIDE view, silhouette: yes  chains: head |
| mass hierarchy | body primary, head secondary, legs detail |
| two focals | dominant = the head · runner-up = the tail  chains: head, tail |
| stance | four legs planted, head low |
| attack | the jaws lunge forward |
| value plan | warm grey dominant, cream belly, amber eye accent, light |

## Exaggeration
The muzzle, much longer than a real wolf's.

## Discarded
1. howling timber wolf
2. werewolf
3. fox
EOF
prints  "brief.py: complete brief"        "every slot"  python3 harness/brief.py "$T/brief.md" --spec example/wolf.json
refuses "brief.py: blank slot blocks"     "not filled in" \
        bash -c "sed 's/^| feel | fast |/| feel | |/' '$T/brief.md' > '$T/blank.md' && python3 harness/brief.py '$T/blank.md'"
refuses "brief.py: two identical poles block" "one idea built twice" \
        python3 harness/brief.py "$T/brief.md" --poles "$T/ol/metrics.json" "$T/ol/metrics.json"
prints  "identity.py: counted verdict"    "PASS" \
        python3 harness/identity.py --brief "$T/brief.md" --round 1 \
          --guesses side="dog,wolf,fox" hero="fox,wolf" front="wolf" top="lizard"
# round.py from a DIFFERENT directory, with paths relative to it — the case that
# used to die with the engine's ENOENT because the tools ran from the repo root
mkdir -p "$T/work"
prints  "round.py r1 (from another cwd)"  "spawn the reader" \
        bash -c "cd '$T/work' && python3 '$ROOT/harness/round.py' out r1 --spec '$ROOT/example/wolf.json' --brief ../brief.md"
prints  "roundcheck.py --record"          "recorded r1" \
        python3 harness/roundcheck.py "$T/work/out" --record r1 ID pass "wolf (rank 1)"
ok      "roundcheck.py --check"           python3 harness/roundcheck.py "$T/work/out" --check ID
prints  "round.py r2 --prev r1"           "iou" \
        bash -c "cd '$T/work' && python3 '$ROOT/harness/round.py' out r2 --spec '$ROOT/example/wolf.json' --prev r1"
refuses "round.py: r1 without a brief blocks" "no brief.md" \
        bash -c "mkdir -p '$T/nob' && cd '$T/nob' && python3 '$ROOT/harness/round.py' o r1 --spec '$ROOT/example/wolf.json'"
prints  "partreads.py (from another cwd)" "ANSWER KEY" \
        bash -c "cd '$T/work' && python3 '$ROOT/harness/partreads.py' pr --spec '$ROOT/example/wolf.json'"
# fit.py on a copy of red_5050: proportion is arithmetic, so it must come out green,
# and it must leave nothing behind next to the spec it was given
mkdir -p "$T/fit" && cp calibration/red_5050.json "$T/fit/spec.json"
prints  "fit.py fixes proportion"         "the spec is legal" python3 harness/fit.py "$T/fit/spec.json" -o "$T/fit/fitted.json"
ok      "fit.py leaves no scratch behind" bash -c "[ \"\$(ls '$T/fit')\" = \"$(printf 'fitted.json\nspec.json')\" ]"
prints  "fitted spec builds"              '"ok":true'   node engine/cli.js "$T/fit/fitted.json" "$T/fit/fitted.glb"
ok      "autofix.mjs"                     node harness/autofix.mjs calibration/wolf_green.json "$T/autofix.json"
prints  "graft.py: part"                  "wrote" \
        python3 harness/graft.py "$T/wolf.glb" "$T/wolf.glb" --part ear --host Skull --out "$T/fused.json"
ok      "graft.py: grafted name is unique" python3 -c "
import json, sys; n = [p['name'] for p in json.load(open(sys.argv[1]))['parts']]
sys.exit(len(n) != len(set(n)))" "$T/fused.json"
refuses "graft.py: unknown part"          "no part" \
        python3 harness/graft.py "$T/wolf.glb" "$T/wolf.glb" --part nosuch --host Skull --out "$T/x.json"
prints  "wash.py"                         '"ok": true'  python3 harness/wash.py "$T/wolf.glb" "$T/washed.glb"
ok      "washed file conforms"            node harness/glbcheck.mjs "$T/washed.glb"

echo
echo "$PASS passed, $FAIL failed"
if [ "$FAIL" -ne 0 ]; then
  printf '  - %s\n' "${FAILED[@]}"
  exit 1
fi
