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
# ── BEGIN giant block (example/gallery/giant.*) — additive; leave the lines above alone ──
# The loop above already builds every gallery spec; this block pins the giant by
# name, so renaming or dropping it fails loudly, and judges it against its own
# claims: the fist is the signature, the clips exist, and it stays in budget.
prints  "giant: builds with no BLOCK"     '"ok":true'   node engine/cli.js example/gallery/giant.json "$T/giant.glb"
ok      "giant: glbcheck (fresh build)"   node harness/glbcheck.mjs "$T/giant.glb"
cat > "$T/giant_claims.json" <<'EOF'
{"name": "giant", "claims": [
 {"type": "part_exists", "part": "fist"},
 {"type": "part_signature", "part": "fist", "view": "front", "min_share": 0.12, "or_min_span": 0.12},
 {"type": "rig_skinned"}, {"type": "anim_named", "names": ["idle", "move", "attack"]},
 {"type": "saturation_area", "view": "hero", "min": 0.10, "max": 0.50},
 {"type": "tri_budget", "min": 4000, "max": 9000}]}
EOF
prints  "giant: claims (fist, clips, tri budget)" "all claims pass" \
        node harness/judge.mjs "$T/giant.glb" "$T/giant_j" giant --spec "$T/giant_claims.json"
# ── END giant block ──
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
prints  "outline.py: 4 legacy views"      "4 views"     python3 harness/outline.py "$T/wolf.glb" "$T/ol" --views legacy
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

# ── fourth pass: junction skin, membrane colours, host_part, open_end ─────────
# (appended as one block; the fixtures are derived from the gallery raven-wyvern,
# which example_copy does not guard, so a modified copy builds)
echo "== 5. fourth-pass features and checks"
RW=example/gallery/raven_wyvern.json
prints  "junction skin blend is reported"  "junction skin: [0-9]* vertices" \
        node engine/cli.js example/wolf.json "$T/wolf_js.glb"
prints  "junction_skin: 0 opts out"        '"ok":true' \
        bash -c "python3 - '$T/noskin.json' <<'PY' && node engine/cli.js '$T/noskin.json' '$T/noskin.glb' 2>&1 | grep -v 'junction skin'
import json, sys
s = json.load(open('$RW')); s.setdefault('shading', {}).setdefault('normals', {})['junction_skin'] = 0
json.dump(s, open(sys.argv[1], 'w'))
PY"
prints  "membrane colours: gallery wing"   'membrane "wing_skin": colours' \
        node engine/cli.js "$RW" "$T/rw_mc.glb"
# a spec error is thrown by the compiler (no BLOCK line), so these two assert on
# the message rather than going through `refuses`, which treats a stack as a crash
ok      "membrane arc in degrees is refused" \
        bash -c "python3 - '$T/mdeg.json' <<'PY' && ! node engine/cli.js '$T/mdeg.json' '$T/mdeg.glb' 2>'$T/mdeg.err'; grep -q 'not in degrees' '$T/mdeg.err'
import json, sys
s = json.load(open('$RW'))
w = [p for p in s['parts'] if p['name'] == 'wing_skin'][0]
w['colors'] = {'arcs': [{'from': 0, 'to': 90, 'color': '#000000'}]}
json.dump(s, open(sys.argv[1], 'w'))
PY"
prints  "host_part: claws seated on curve toes" "seated on part \"toe_mid\"" \
        node engine/cli.js "$RW" "$T/rw_hp.glb"
refuses "host_part: a floating claw blocks against its host part" 'part_attachment: "claw_mid" never meets its host part "toe_mid"' \
        bash -c "python3 - '$T/hpfloat.json' <<'PY' && node engine/cli.js '$T/hpfloat.json' '$T/hpfloat.glb'
import json, sys
s = json.load(open('$RW'))
c = [p for p in s['parts'] if p['name'] == 'claw_mid'][0]; c['offset'] = [0, 0.12, 0.05]
json.dump(s, open(sys.argv[1], 'w'))
PY"
ok      "host_part: a host listed after its part is refused" \
        bash -c "python3 - '$T/hporder.json' <<'PY' && ! node engine/cli.js '$T/hporder.json' '$T/hporder.glb' 2>'$T/hporder.err'; grep -q 'is listed AFTER this part' '$T/hporder.err'
import json, sys
s = json.load(open('$RW')); parts = s['parts']
i = [k for k, p in enumerate(parts) if p['name'] == 'toe_mid'][0]; parts.append(parts.pop(i))
json.dump(s, open(sys.argv[1], 'w'))
PY"
refuses "open_end: a body left open at the chest blocks" "open_end: volume \"body\" is left open" \
        bash -c "python3 - '$T/openend.json' <<'PY' && node engine/cli.js '$T/openend.json' '$T/openend.glb'
import json, sys
s = json.load(open('$RW'))
b = [v for v in s['volumes'] if v['chain'] == 'body'][0]; b['caps'] = ['dome', 'none']
json.dump(s, open(sys.argv[1], 'w'))
PY"
prints  "gates.py lists open_end"          "open_end"     python3 harness/gates.py
ok      "checks stamp carries open_end"    bash -c "grep -q '\"name\": \"open_end\"' '$T/rw_hp.checks.json'"

# ── fifth pass: the head from every angle (sections, eyelids, curve sections) ──
echo "== 6. fifth-pass head features"
ok      "section taper is a wedge (wider above than below)" \
        node -e "const s=require('./engine/core/section.js');const a=s.sectionPoint(0.4,1,1,2,0,0.4,0)[0],b=s.sectionPoint(-0.4,1,1,2,0,0.4,0)[0];process.exit(a>b*1.2?0:1)"
ok      "section cup lifts the edges, holds the middle" \
        node -e "const s=require('./engine/core/section.js');const e=s.sectionPoint(0,1,1,2,0,0,0.5)[1],m=s.sectionPoint(Math.PI/2,1,1,2,0,0,0.5)[1];process.exit(e>0.2&&m<1?0:1)"
prints  "eyelids ship as eye.lid.L / eye.lid.R" "eye.lid.L, eye.lid.R" \
        node engine/cli.js example/wolf.json "$T/wolf_lid.glb"
ok      "a lid in the host's material does not trip contrast_adjacent" \
        bash -c "! grep -q 'contrast_adjacent: part \"eye.lid' '$T/wolf_lid.checks.json'"
prints  "lower lid, cupped crest and a per-segment bill section build" '"ok":true' \
        bash -c "python3 - '$T/lid2.json' <<'PY' && node engine/cli.js '$T/lid2.json' '$T/lid2.glb'
import json, sys
s = json.load(open('$RW'))
e = [p for p in s['parts'] if p['name'] == 'eye'][0]; e['lid'] = {'angle': 50, 'lower': 30}
[p for p in s['parts'] if p['name'] == 'crest_mid'][0]['section'] = {'cup': 0.6, 'exp': 2.5}
[p for p in s['parts'] if p['name'] == 'upper_bill'][0]['segments'][1]['section'] = {'exp': 4, 'taper': 0.2}
[v for v in s['volumes'] if v['chain'] == 'head'][0]['profile'][1][3]['cup'] = 0.2
json.dump(s, open(sys.argv[1], 'w'))
PY"
ok      "the lids are closed shells (no open edge on the hood)" \
        node -e "
const {compile}=require('./engine/core/compile.js');const s=JSON.parse(require('fs').readFileSync('example/wolf.json'));
require('./engine/core/relative.js').resolveJoints(s);
for(const m of compile(s)){ if(m.sub!=='lid')continue; const e=new Map();
  for(const f of m.F)for(let i=0;i<3;i++){const a=f[i],b=f[(i+1)%3];const k=a<b?a+'_'+b:b+'_'+a;e.set(k,(e.get(k)||0)+1);}
  const open=[...e.values()].filter(n=>n!==2).length; if(open>m.F.length/3){console.error(m.part,'open edges',open);process.exit(1);} }"

# ── BEGIN orbit block (8+2 views, the head) — additive; leave the lines above alone ──
echo "== 7. the 8+2 orbit"
prints  "outline.py: default is the 10-view orbit" "10 views" \
        python3 harness/outline.py "$T/wolf.glb" "$T/orb"
ok      "orbit: sheets, colour renders, thumbs" \
        test -s "$T/orb/orbit_sheet.png" -a -s "$T/orb/orbit_sil_sheet.png" -a -s "$T/orb/col_az045.png" \
             -a -s "$T/orb/sil_az135_thumb48.png" -a -s "$T/orb/sil_bottom_thumb24.png"
ok      "orbit: metrics carry facing, head and ring" python3 -c "
import json, sys; m = json.load(open(sys.argv[1]))
assert m['facing']['forward'] == [0.0, 0.0, 1.0], m['facing']
assert m['facing']['head'].startswith('spec chain'), m['facing']
o = m['orbit']; assert len(o['ring']) == 8 and o['read_set'][0] == 'az000' and o['read_set'][-1] == 'top'
assert all('head_share' in m['views'][v] for v in ('az000', 'az090', 'top', 'bottom'))
assert m['views']['az090']['head_distinct'] is True" "$T/orb/metrics.json"
ok      "orbit: sheet is 5x2 tiles"      python3 -c "
from PIL import Image; import sys; w, h = Image.open(sys.argv[1]).size; sys.exit(not (w == 5 * 256 and h == 2 * 278))" "$T/orb/orbit_sheet.png"
# facing comes from the head, not the bounding box: the wolf turned to face +X
# must say +X, and its az000 must look at its face
ok      "orbit: facing follows the head, not the bbox" python3 -c "
import sys; sys.path.insert(0, 'harness'); import numpy as np, outline as o
V, F = o.triangles(sys.argv[1]); h, _ = o.head_vertices(sys.argv[1], len(V))
R = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]], float)   # +Z -> +X
f, how = o.facing_of(V @ R.T, h); assert list(f) == [1, 0, 0], (f, how)
o.FACING = f; px, py, z = o.project(V @ R.T, 'az000')
assert z[h].mean() < z[~h].mean(), 'az000 does not look at the face'" "$T/wolf.glb"
# the vectorised z-buffer must give the per-triangle loop's answer, pixel for pixel
ok      "orbit: z-buffer matches the reference loop" python3 -c "
import sys, math; sys.path.insert(0, 'harness'); import numpy as np, outline as o
o.RES = 160; V, F, MID, mats = o.triangles_by_material(sys.argv[1])
px, py, z = o.project(V, 'az045'); got = o.zbuffer(px, py, z, F)
depth = np.full((o.RES, o.RES), np.inf); own = np.full((o.RES, o.RES), -1)
for t, (a, b, c) in enumerate(F):
    xs, ys = px[[a, b, c]], py[[a, b, c]]
    x0, x1 = int(max(0, math.floor(xs.min()))), int(min(o.RES - 1, math.ceil(xs.max())))
    y0, y1 = int(max(0, math.floor(ys.min()))), int(min(o.RES - 1, math.ceil(ys.max())))
    if x1 < x0 or y1 < y0: continue
    if abs((ys[1]-ys[2])*(xs[0]-xs[2]) + (xs[2]-xs[1])*(ys[0]-ys[2])) < 1e-12: continue
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    l0, l1, l2, zz = o._bary(px, py, z, a, b, c, gx, gy)
    w =(l0 >= 0) & (l1 >= 0) & (l2 >= 0) & (zz < depth[y0:y1+1, x0:x1+1])
    depth[y0:y1+1, x0:x1+1][w] = zz[w]; own[y0:y1+1, x0:x1+1][w] = t
sys.exit(not np.array_equal(own, got))" "$T/wolf.glb"
cat > "$T/orbit_claims.json" <<'EOF'
{"name": "orbit", "claims": [
 {"type": "head_reads", "enforce": "advise"}, {"type": "orbit_consistent", "enforce": "advise"}]}
EOF
prints  "judge.mjs: orbit claims pass on the wolf" "all claims pass" \
        node harness/judge.mjs "$T/wolf.glb" "$T/oj" wolf --spec "$T/orbit_claims.json"
prints  "judge.mjs: a sunk head is ADVICE, not a block" "head does not read" \
        bash -c "python3 -c \"import sys; sys.path.insert(0, 'harness'); import calibrate; calibrate.sink_head(sys.argv[1], sys.argv[2])\" '$T/wolf.glb' '$T/headless.glb' && node harness/judge.mjs '$T/headless.glb' '$T/hj' headless --spec '$T/orbit_claims.json'"
prints  "gates.py lists the orbit checks" "head_reads" python3 harness/gates.py LOW
# Gate 1 on the orbit: the counted rule, plus an oblique that reads
sed 's/carried by the SIDE view/carried by the az090 view/' "$T/brief.md" > "$T/brief_orbit.md"
prints  "brief.py: an orbit identity view"  "identity_view=az090" python3 harness/brief.py "$T/brief_orbit.md"
prints  "identity.py: orbit read passes with a live oblique" "PASS" \
        python3 harness/identity.py --brief "$T/brief_orbit.md" --round 1 \
          --guesses az000="dog,wolf" az045="wolf,dog" az090="wolf" az135="fox,dog,wolf" az180="bear" top="lizard"
refuses "identity.py: a dead oblique fails the orbit" "orbit does not hold" \
        python3 harness/identity.py --brief "$T/brief_orbit.md" --round 1 \
          --guesses az000="wolf" az045="lamp,chair" az090="wolf" az135="rock,blob" az180="wolf" top="wolf"
refuses "identity.py: a dead identity view fails the orbit" "identity view (az090)" \
        python3 harness/identity.py --brief "$T/brief_orbit.md" --round 1 \
          --guesses az000="wolf" az045="wolf" az090="lamp" az135="wolf" az180="wolf" top="wolf"
ok      "deliver.py: the pack carries the orbit sheets" \
        test -s "$T/del/orbit_sheet.png" -a -s "$T/del/orbit_sil_sheet.png"
# ── END orbit block ──

echo
echo "$PASS passed, $FAIL failed"
if [ "$FAIL" -ne 0 ]; then
  printf '  - %s\n' "${FAILED[@]}"
  exit 1
fi
