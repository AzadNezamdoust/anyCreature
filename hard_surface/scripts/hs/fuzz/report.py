"""
report.py -- tally a fuzz run (plain Python).

  python scripts/hs/fuzz/report.py out/fuzz/main [--out out/fuzz/main/report.md] [--top 20]

Definitions
  case fail  = any code in `fail` (fuzz_helpers.run_case): exception, empty_mesh, topo_* (run_pass.topology_report counters
               on the part after hs.end()), topo_edges_gt2 (edges with > 2 faces; run_pass's non_manifold_edges also counts
               boundary edges), mat_empty_slot (a None material slot), mat_oob_faces (a face pointing at a missing/None slot),
               neg_volume, freestyle_twice ("edge appears twice" in a Freestyle render), crash / hang (Blender died).
  core fail  = fail minus mat_empty_slot (which almost every boolean produces; tallied on its own).
  defect     = case-level: core minus topo_zero_area, plus zero_area_true (a triangle < 1e-10 m2). Scale-free: a 1e-8 m2
               triangle is a real defect on a 0.5 m part and a legitimately small triangle on a 10 mm one.
  hazard     = per evaluated step: P(state becomes defective | previous evaluated state was clean), measured on a hs.cleanup()
               copy of the part (what the builder sees after hs.end()). defect = nm / boundary / duplicate / loose != 0 or a
               triangle < 1e-10 m2; "strict" = additionally run_pass's zero_area_faces (< 1e-8 m2) != 0 (second column).
               A stacked group (hs.boolean x k, then one apply) is one step.
"""
import argparse
import collections
import glob
import json
import math
import os
import sys

TOPO_KEYS = ("non_manifold_edges", "boundary_edges", "zero_area_faces", "duplicate_faces", "loose")
INFO_ONLY = {"mat_empty_slot"}
NOT_DEFECT = {"mat_empty_slot", "topo_zero_area"}


def load(d):
    cases = {}
    for p in sorted(glob.glob(os.path.join(d, "chunk_*.jsonl"))):
        with open(p, encoding="utf-8") as f:
            for ln in f:
                try:
                    r = json.loads(ln)
                except ValueError:
                    continue
                b = (r.get("recipe") or {}).get("base") or {}
                if "mat_oob_faces" in r.get("fail", []) and b.get("bore") and b["bore"].get("mat") is not None                         and b["bore"]["mat"] >= len(b.get("mats", [])):
                    r["fail"] = [c for c in r["fail"] if c != "mat_oob_faces"]   # harness: old runs picked bore(mat=) past the slot list
                    r["harness_bore_mat"] = True
                cases[r["case"]] = r
    return [cases[k] for k in sorted(cases)]


def core(r):
    return [c for c in r.get("fail", []) if c not in INFO_ONLY]


def is_bad(t):
    return any(t)


def defect_codes(r):
    return [c for c in r.get("fail", []) if c not in NOT_DEFECT]


def step_defect(s):
    t = s["clean"]
    return bool(t[0] or t[1] or t[3] or t[4] or s.get("z10", 0))


def step_strict(s):
    return any(s["clean"]) or bool(s.get("z10", 0))


def bin_of(x, edges, labels):
    for e, lab in zip(edges, labels):
        if x <= e:
            return lab
    return labels[-1]


COP_E = [0.0, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2, math.inf]
COP_L = ["0 (exact)", "(0,1e-6]", "(1e-6,1e-5]", "(1e-5,1e-4]", "(1e-4,1e-3]", "(1e-3,1e-2]", ">1e-2"]
RATIO_E = [0.02, 0.05, 0.1, 0.2, 0.4, math.inf]
RATIO_L = ["<0.02", "0.02-0.05", "0.05-0.1", "0.1-0.2", "0.2-0.4", ">0.4"]
WIDTH_E = [0.001, 0.002, 0.005, 0.0101]
WIDTH_L = ["0.5-1 mm", "1-2 mm", "2-5 mm", "5-10 mm"]
S_E = [0.02, 0.05, 0.1, 0.2, 0.51]
S_L = ["10-20 mm", "20-50 mm", "50-100 mm", "100-200 mm", "200-500 mm"]
TILT_E = [0.0, 0.01, 0.1, 1.0, math.inf]
TILT_L = ["none", "<=0.01 deg", "0.01-0.1 deg", "0.1-1 deg", ">1 deg"]
GAP_E = [-1e-3, -1e-5, 1e-5, 1e-3, math.inf]
GAP_L = ["crosses x=0 (< -1 mm)", "(-1 mm,-0.01 mm]", "touches x=0 (|gap| <= 0.01 mm)", "(0.01 mm,1 mm]", "> 1 mm"]


WPS_E = [0.00015, 0.0003, 0.0006, 0.0012, 0.0101]
WPS_L = ["<0.15 mm", "0.15-0.3 mm", "0.3-0.6 mm", "0.6-1.2 mm", ">1.2 mm"]


class Tab:
    def __init__(self, title, note=""):
        self.title, self.note = title, note
        self.d = collections.OrderedDict()

    def add(self, key, event, strict=None):
        v = self.d.setdefault(key, [0, 0, 0])
        v[0] += 1
        v[1] += 1 if event else 0
        v[2] += 1 if (event if strict is None else strict) else 0

    def md(self, order=None, minn=1):
        out = [f"### {self.title}", ""]
        if self.note:
            out += [self.note, ""]
        out += ["| bin | n | defect | rate | strict (incl. <1e-8 m2) |", "|---|---:|---:|---:|---:|"]
        keys = order or list(self.d)
        for k in keys:
            if k not in self.d or self.d[k][0] < minn:
                continue
            n, e, e2 = self.d[k]
            out.append(f"| {k} | {n} | {e} | {100.0 * e / n:.1f}% | {100.0 * e2 / n:.1f}% |")
        return "\n".join(out) + "\n"


def walk_groups(r):
    """yield (step_index, group_ops, step, prev_evaluated_step) for every evaluated step after the base."""
    steps = r.get("steps") or []
    ops = (r.get("recipe") or {}).get("ops") or []
    if not steps:
        return
    prev = steps[0]
    group = []
    for i in range(1, len(steps)):
        if i - 1 >= len(ops):
            break
        group.append(ops[i - 1])
        s = steps[i]
        if s.get("pending"):
            continue
        yield i, list(group), s, prev
        prev = s
        group = []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--out")
    ap.add_argument("--top", type=int, default=20)
    a = ap.parse_args()
    cases = load(a.dir)
    N = len(cases)
    if not N:
        sys.exit("no cases")
    md = []
    W = md.append
    done = [r for r in cases if not r.get("crash")]
    crashes = [r for r in cases if r.get("crash")]
    W(f"# Fuzz report: {a.dir}\n")
    W(f"cases {N} (ids {cases[0]['case']}..{cases[-1]['case']}), completed {len(done)}, crash/hang {len(crashes)}, "
      f"harness errors {sum(1 for r in cases if r.get('harness_error'))}, "
      f"mean wall {sum(r.get('t', 0) for r in done) / max(1, len(done)):.2f} s/case\n")

    # ------------------------------------------------------------------ 1 overall
    anyf = sum(1 for r in cases if r["fail"])
    corf = sum(1 for r in cases if core(r))
    deff = sum(1 for r in cases if defect_codes(r))
    softf = sum(1 for r in cases if r.get("soft"))
    W("## 1. Overall\n")
    W(f"- any failure (incl. empty material slot): **{anyf}/{N} = {100 * anyf / N:.1f}%**")
    W(f"- core failure, run_pass verbatim (topology incl. zero_area_faces < 1e-8 m2 / Freestyle / exception / empty / mat index / neg volume / crash): **{corf}/{N} = {100 * corf / N:.1f}%**")
    W(f"- true defect (core minus the 1e-8 m2 zero-area rule, plus a triangle < 1e-10 m2): **{deff}/{N} = {100 * deff / N:.1f}%**")
    W(f"- soft flags only (sliver tris < 0.1 mm high, volume sanity): {softf}/{N}\n")
    cc = collections.Counter(c for r in cases for c in r["fail"])
    sc = collections.Counter(c for r in cases for c in r.get("soft", []))
    W("| code | cases | rate |\n|---|---:|---:|")
    for c, n in cc.most_common():
        W(f"| {c} | {n} | {100 * n / N:.1f}% |")
    tz = sum(1 for r in done if r.get("final") and r["final"].get("zero_1e10", 0) > 0)
    W(f"| (of topo_zero_area: truly degenerate tri, area < 1e-10 m2) | {tz} | {100 * tz / N:.1f}% |")
    for c, n in sc.most_common():
        W(f"| (soft) {c} | {n} | {100 * n / N:.1f}% |")
    W("")
    # cases with no boolean at all
    nob = [r for r in done if r.get("recipe") and not any(o["op"] == "cut" for o in r["recipe"]["ops"])]
    wb = [r for r in done if r.get("recipe") and any(o["op"] == "cut" for o in r["recipe"]["ops"])]
    W(f"No boolean in the case: {len(nob)} cases, core fail {100 * sum(1 for r in nob if core(r)) / max(1, len(nob)):.1f}% (defect {100 * sum(1 for r in nob if defect_codes(r)) / max(1, len(nob)):.1f}%), "
      f"empty-slot {100 * sum(1 for r in nob if 'mat_empty_slot' in r['fail']) / max(1, len(nob)):.1f}%. "
      f"With >= 1 boolean: {len(wb)} cases, core fail {100 * sum(1 for r in wb if core(r)) / max(1, len(wb)):.1f}% (defect {100 * sum(1 for r in wb if defect_codes(r)) / max(1, len(wb)):.1f}%), "
      f"empty-slot {100 * sum(1 for r in wb if 'mat_empty_slot' in r['fail']) / max(1, len(wb)):.1f}%.\n")

    # ------------------------------------------------------------------ 2 per helper
    W("## 2. Failure rate per helper (case involvement)\n")
    W("A case counts for every helper it used (`begin/finish/end/cleanup` are in all cases and omitted). Confounded: a case with "
      "several helpers counts for each, see the hazard tables (section 3) for the per-call rate.\n")
    ht = collections.OrderedDict()
    for r in done:
        for h in r.get("helpers", []):
            if h in ("begin", "finish", "end", "cleanup"):
                continue
            v = ht.setdefault(h, [0, 0, 0, collections.Counter()])
            v[0] += 1
            v[1] += 1 if core(r) else 0
            dc = defect_codes(r)
            v[2] += 1 if dc else 0
            for c in dc:
                v[3][c] += 1
    W("| helper | cases | defect | defect rate | strict rate | top defect codes |\n|---|---:|---:|---:|---:|---|")
    for h, (n, e, d, cs) in sorted(ht.items(), key=lambda kv: -kv[1][2] / max(1, kv[1][0])):
        W(f"| hs.{h} | {n} | {d} | {100 * d / n:.1f}% | {100 * e / n:.1f}% | {', '.join(f'{c} {k}' for c, k in cs.most_common(3))} |")
    W("")

    # ------------------------------------------------------------------ 3 hazards
    base_t = Tab("3a. Base primitive: unclean right after construction (no booleans / bevel yet)",
                 "hs primitive called with the sampled parameters; state measured after hs.cleanup (== after hs.end).")
    base_raw = Tab("3a'. Same, raw (before any cleanup)")
    base_exc = collections.Counter()
    op_t = Tab("3b. Per-step hazard by operation (previous state clean -> this step unclean)")
    op_raw = Tab("3b'. Same on the RAW mesh (what the cleanup in hs.end has to repair)")
    mat_first = collections.Counter()
    for r in done:
        st = r.get("steps") or []
        rec = r.get("recipe") or {}
        if st:
            bk = rec.get("base", {}).get("kind", "?")
            base_t.add(bk, step_defect(st[0]), step_strict(st[0]))
            base_raw.add(bk, is_bad(st[0]["raw"]))
        if r.get("exc") and r["exc"].get("op_index", 0) == 0 and not st:
            base_exc[(r["exc"]["type"], r["exc"]["msg"][:70], rec.get("base", {}).get("kind", "?") if rec else "?")] += 1
    cut_shape = Tab("3c. Cutter shape (groups with one or more booleans)")
    cut_mode = Tab("3d. Cutter placement mode")
    cut_kind = Tab("3e. Boolean operation")
    cut_via = Tab("3f. hs.cut one-shot vs stacked hs.boolean + apply")
    cut_cop = Tab("3g. Cutter / target coplanar distance (min |cutter bound - target bound| on any axis)",
                  "per group with a boolean; plane_cutter has no cop and is excluded.")
    cut_cop_d = Tab("3g'. ... DIFFERENCE only")
    cut_cop_u = Tab("3g''. ... UNION only")
    cut_tilt = Tab("3h. Cutter tilt (near-coplanar tilted faces)")
    cut_after_bevel = Tab("3i. Order: boolean on a part that already went through bevel_mod vs an un-bevelled part")
    bev_ratio = Tab("3j. bevel_mod width / smallest part dimension", "groups that contain a bevel_mod (bevel applied alone or stacked).")
    bev_width = Tab("3k. bevel_mod absolute width")
    bev_wps = Tab("3k'. bevel_mod width per segment (width / segments)", "a bevel strip narrower than ~0.2 mm makes triangles under run_pass's 1e-8 m2 zero-area threshold.")
    bev_seg = Tab("3l. bevel_mod segments")
    bev_ang = Tab("3m. bevel_mod angle limit (deg)")
    bev_after_cut = Tab("3n. Order: bevel_mod after booleans vs on a primitive")
    bev_tris = Tab("3o. bevel_mod on a part with many triangles (tris before the bevel)")
    bev_ratio_seg = Tab("3p. bevel ratio x segments (ratio > 0.2 and segments)")
    mir_gap = Tab("3q. mirror_x: inner face gap to x=0")
    mir_via = Tab("3r. mirror_x apply vs stacked")
    size_t = Tab("3s. Part size S (largest base dimension)", "case-level core failure.")
    ncut_t = Tab("3t. Number of booleans in the case", "case-level core failure.")
    for r in done:
        rec = r.get("recipe") or {}
        if not rec:
            continue
        size_t.add(bin_of(rec["S"], S_E, S_L), bool(defect_codes(r)), bool(core(r)))
        ncut_t.add(sum(1 for o in rec["ops"] if o["op"] == "cut"), bool(defect_codes(r)), bool(core(r)))
        seen_cut = False
        seen_bev = False
        steps = r.get("steps") or []
        for i, group, s, prev in walk_groups(r):
            if step_defect(prev):
                if any(o["op"] == "cut" for o in group):
                    seen_cut = True
                if any(o["op"] == "bevel" for o in group):
                    seen_bev = True
                continue
            bad = step_defect(s)
            strict = step_strict(s)
            badraw = is_bad(s["raw"])
            cuts = [o for o in group if o["op"] == "cut"]
            bevs = [o for o in group if o["op"] == "bevel"]
            mirs = [o for o in group if o["op"] == "mirror_x"]
            if len(group) == 1:
                o = group[0]
                lab = o["op"] + (":" + o["op_kind"] + " via " + o["via"] if o["op"] == "cut" else "")
                if o["op"] == "mirror_x":
                    lab += " " + o["via"]
            else:
                lab = "stacked group (" + "+".join(sorted({(o["op"] + (":" + o["op_kind"] if o["op"] == "cut" else "")) for o in group})) + ")"
            op_t.add(lab, bad, strict)
            op_raw.add(lab, badraw)
            if s.get("mat") and prev.get("mat") and s["mat"][1] > prev["mat"][1]:
                mat_first[lab] += 1
            if cuts:
                c0 = min(cuts, key=lambda o: (o["cop"] if o.get("cop") is not None else 9))
                for o in cuts:
                    cut_shape.add(o["cutter"]["k"], bad, strict)
                    cut_mode.add(o["mode"], bad, strict)
                    cut_kind.add(o["op_kind"], bad, strict)
                    cut_via.add(o["via"], bad, strict)
                    cut_tilt.add(bin_of(o.get("tilt", 0.0), TILT_E, TILT_L), bad, strict)
                cops = [o["cop"] for o in cuts if o.get("cop") is not None]
                if cops:
                    cm = min(cops)
                    cut_cop.add(bin_of(cm, COP_E, COP_L), bad, strict)
                    if all(o["op_kind"] == "DIFFERENCE" for o in cuts):
                        cut_cop_d.add(bin_of(cm, COP_E, COP_L), bad, strict)
                    if all(o["op_kind"] == "UNION" for o in cuts):
                        cut_cop_u.add(bin_of(cm, COP_E, COP_L), bad, strict)
                if not bevs:
                    cut_after_bevel.add("after bevel_mod" if seen_bev else "no bevel yet", bad, strict)
            if bevs:
                b0 = max(bevs, key=lambda o: o["ratio"])
                bev_ratio.add(bin_of(b0["ratio"], RATIO_E, RATIO_L), bad, strict)
                bev_width.add(bin_of(b0["width"], WIDTH_E, WIDTH_L), bad, strict)
                bev_wps.add(bin_of(b0["width"] / b0["segments"], WPS_E, WPS_L), bad, strict)
                bev_seg.add(str(b0["segments"]), bad, strict)
                bev_ang.add(str(b0["angle"]), bad, strict)
                if not cuts:
                    bev_after_cut.add("after boolean(s)" if seen_cut else "on a primitive", bad, strict)
                    tr = prev.get("tris", 0)
                    bev_tris.add("<=100" if tr <= 100 else "101-400" if tr <= 400 else "401-1000" if tr <= 1000 else ">1000", bad, strict)
                bev_ratio_seg.add(f"{bin_of(b0['ratio'], RATIO_E, RATIO_L)} / seg {b0['segments']}", bad, strict)
            for o in mirs:
                mir_gap.add(bin_of(o["gap"], GAP_E, GAP_L), bad, strict)
                mir_via.add(o["via"], bad, strict)
            if any(o["op"] == "cut" for o in group):
                seen_cut = True
            if bevs:
                seen_bev = True
    W("## 3. Hazard tables (per call, previous state clean)\n")
    W("defect = the part became defective at this step (nm / boundary / duplicate / loose != 0, or a triangle < 1e-10 m2, after hs.cleanup); "
      "'strict' also counts run_pass's zero_area_faces (< 1e-8 m2). Rows with n < 15 are noisy.\n")
    W(base_t.md())
    W(base_raw.md())
    if base_exc:
        W("Exceptions while building a base primitive:\n")
        for k, n in base_exc.most_common():
            W(f"- {n} x {k}")
        W("")
    W(op_t.md())
    W(op_raw.md())
    for t, order in ((cut_shape, None), (cut_mode, None), (cut_kind, None), (cut_via, None)):
        W(t.md(order))
    W(cut_cop.md(COP_L))
    W(cut_cop_d.md(COP_L))
    W(cut_cop_u.md(COP_L))
    W(cut_tilt.md(TILT_L))
    W(cut_after_bevel.md())
    W(bev_ratio.md(RATIO_L))
    W(bev_width.md(WIDTH_L))
    W(bev_wps.md(WPS_L))
    W(bev_seg.md(["1", "2", "3"]))
    W(bev_ang.md(["10", "25", "30", "45", "60"]))
    W(bev_after_cut.md())
    W(bev_tris.md(["<=100", "101-400", "401-1000", ">1000"]))
    W(bev_ratio_seg.md(minn=15))
    W(mir_gap.md(GAP_L))
    W(mir_via.md())
    W(size_t.md(S_L))
    W(ncut_t.md())
    if mat_first:
        W("### 3u. First step that adds an empty (None) material slot\n")
        W("| step | cases |\n|---|---:|")
        for k, n in mat_first.most_common():
            W(f"| {k} | {n} |")
        W("")

    # ------------------------------------------------------------------ 4 order
    W("## 4. Failure rate per operation order (case level, core failures)\n")
    ct = Tab("4a. Order class")
    tt = Tab("4b. Exact token sequence (B = bevel_mod, C = boolean, M = mirror_x)")
    for r in done:
        if not r.get("recipe"):
            continue
        ct.add(r["cls"] + (" + mirror_x" if "M" in r["tokens"] else ""), bool(defect_codes(r)), bool(core(r)))
        tt.add(r["tokens"], bool(defect_codes(r)), bool(core(r)))
    W(ct.md())
    W(tt.md(minn=20))

    # ------------------------------------------------------------------ 5 first break
    W("## 5. Which step first made a failing case unclean\n")
    fb = collections.Counter()
    nostep = 0
    for r in done:
        tf = [c for c in defect_codes(r) if c.startswith("topo_") or c == "zero_area_true"]
        if not tf or not r.get("steps"):
            continue
        st = r["steps"]
        if step_defect(st[0]):
            fb["base primitive: " + r["recipe"]["base"]["kind"]] += 1
            continue
        found = False
        for i, group, s, prev in walk_groups(r):
            if step_defect(s):
                lab = "+".join(sorted({(o["op"] + (":" + o["op_kind"] if o["op"] == "cut" else "")) for o in group}))
                fb[lab] += 1
                found = True
                break
        if not found:
            fb["only after hs.end / not visible per step"] += 1
    W("| first step that is unclean | cases |\n|---|---:|")
    for k, n in fb.most_common():
        W(f"| {k} | {n} |")
    W("")

    # ------------------------------------------------------------------ 6 topology detail
    W("## 6. Final topology counters (after hs.end), cases with any topology failure\n")
    tc = collections.Counter()
    for r in done:
        t = r["final"].get("totals") if r.get("final") else None
        if not t:
            continue
        key = tuple(k.replace("_edges", "").replace("_faces", "") for k, v in zip(TOPO_KEYS, t) if v)
        if key:
            tc["+".join(key)] += 1
    W("| counters nonzero | cases |\n|---|---:|")
    for k, n in tc.most_common():
        W(f"| {k} | {n} |")
    W("")
    z = [r for r in done if r.get("final") and r["final"].get("totals") and r["final"]["totals"][2] > 0]
    if z:
        true0 = sum(1 for r in z if r["final"].get("zero_1e10", 0) > 0)
        W(f"zero_area_faces > 0 in {len(z)} cases; in {true0} of them at least one triangle is truly degenerate (area < 1e-10 m2), "
          f"in {len(z) - true0} the smallest triangle is valid but under run_pass's 1e-8 m2 threshold (tiny, not broken). "
          f"Median part size S of the zero-area cases {sorted(r['recipe']['S'] for r in z)[len(z) // 2]:.3f} m.\n")
        zt = Tab("6a. zero_area_faces > 0 by part size S, over cases whose bevel/booleans ran (core zero-area rate)")
        for r in done:
            if r.get("final") and r["final"].get("totals") and r.get("recipe"):
                zt.add(bin_of(r["recipe"]["S"], S_E, S_L), r["final"]["totals"][2] > 0)
        W(zt.md(S_L))
        zt2 = Tab("6b. ... truly degenerate triangle (area < 1e-10 m2) by part size S")
        for r in done:
            if r.get("final") and r["final"].get("totals") and r.get("recipe"):
                zt2.add(bin_of(r["recipe"]["S"], S_E, S_L), r["final"].get("zero_1e10", 0) > 0)
        W(zt2.md(S_L))

    # ------------------------------------------------------------------ 7 freestyle
    W("## 7. Freestyle \"edge appears twice\"\n")
    fsr = [r for r in done if r.get("fs")]
    tw = [r for r in fsr if r["fs"]["twice"]]
    isbad = lambda r: any(c.startswith("topo_") or c == "zero_area_true" for c in defect_codes(r))
    topo_clean = [r for r in fsr if not isbad(r)]
    topo_bad = [r for r in fsr if isbad(r)]
    W(f"Freestyle probed on {len(fsr)} cases; warning in {len(tw)} ({100 * len(tw) / max(1, len(fsr)):.1f}%). "
      f"Among topology-clean cases: {sum(1 for r in topo_clean if r['fs']['twice'])}/{len(topo_clean)} "
      f"({100 * sum(1 for r in topo_clean if r['fs']['twice']) / max(1, len(topo_clean)):.1f}%); among topology-failing cases: "
      f"{sum(1 for r in topo_bad if r['fs']['twice'])}/{len(topo_bad)} "
      f"({100 * sum(1 for r in topo_bad if r['fs']['twice']) / max(1, len(topo_bad)):.1f}%).\n")
    ft = Tab("7a. Freestyle warning by which run_pass counter is nonzero")
    for k, lab in zip(range(5), ("non_manifold_edges", "boundary_edges", "zero_area_faces", "duplicate_faces", "loose")):
        for r in fsr:
            t = r["final"].get("totals")
            if t:
                ft.add(lab + (" > 0" if t[k] else " == 0"), bool(r["fs"]["twice"]))
    for r in fsr:
        ft.add("edges with > 2 faces " + ("> 0" if r["final"].get("edges_gt2") else "== 0"), bool(r["fs"]["twice"]))
    W(ft.md())
    ot = collections.Counter()
    for r in fsr:
        if r["fs"]["other"]:
            for o in r["fs"]["other"]:
                ot[o[:100]] += 1
    if ot:
        W("Other Freestyle/render warnings seen: " + "; ".join(f"{k} x{n}" for k, n in ot.most_common(5)) + "\n")
    fb2 = collections.Counter()
    for r in tw:
        if isbad(r):
            continue
        rec = r.get("recipe") or {}
        fb2[(rec.get("cls", "?"), rec.get("base", {}).get("kind", "?"))] += 1
    if fb2:
        W("Freestyle-only failures (topology clean) by class / base: " + "; ".join(f"{k[0]}/{k[1]} x{n}" for k, n in fb2.most_common(8)) + "\n")

    # ------------------------------------------------------------------ 8 exceptions / crashes
    W("## 8. Exceptions, crashes\n")
    ex = collections.Counter()
    for r in done:
        if r.get("exc"):
            e = r["exc"]
            ex[(e["type"], e["msg"][:80], e["where"][-1] if e.get("where") else "")] += 1
    if ex:
        W("| type | message | where | cases |\n|---|---|---|---:|")
        for (t, m, w), n in ex.most_common():
            W(f"| {t} | {m} | {w} | {n} |")
    else:
        W("No exceptions.")
    W("")
    if crashes:
        W("Crash/hang cases (replay with `--seed <id> --n 1`): " + ", ".join(f"{r['case']}{'(hang)' if r.get('hang') else ''}" for r in crashes) + "\n")
    W(f"Soft: volume sanity violations {sc.get('volume_violation', 0)}, sliver tris {sc.get('sliver', 0)}.\n")

    # ------------------------------------------------------------------ 9 smallest failing replayable
    W(f"## 9. The {a.top} smallest replayable failing cases (true defects, fewest operations then fewest calls)\n")
    fl = [r for r in done if defect_codes(r) and r.get("recipe") and r["recipe"].get("base")]
    fl.sort(key=lambda r: (len(r["recipe"]["ops"]), len(r["calls"]), r.get("final", {}).get("tris", 0), r["case"]))
    # prefer one per distinct (fail signature, op signature)
    shown, sigs = [], set()
    for r in fl:
        sig = (tuple(defect_codes(r)), r["tokens"], r["recipe"]["base"]["kind"])
        if sig in sigs and len(shown) < a.top and len(fl) > 3 * a.top:
            continue
        sigs.add(sig)
        shown.append(r)
        if len(shown) >= a.top:
            break
    for r in shown:
        W(f"**case {r['case']}** `{'+'.join(defect_codes(r))}` base {r['recipe']['base']['kind']} S={r['recipe']['S']:.4f} tokens {r['tokens']} "
          f"final counters {r['final'].get('totals')} tris {r['final'].get('tris')} {('fs twice ' + str(r['fs']['twice'])) if r.get('fs', {}).get('twice') else ''}")
        W("")
        W("```")
        W(f'blender -b --factory-startup --python scripts/hs/fuzz/fuzz_helpers.py -- --replay {os.path.relpath(a.dir).replace(chr(92), "/")}/{chunk_of(r["case"], a.dir)} --case {r["case"]}')
        for c in r["calls"]:
            W("  " + c[:260])
        W("```\n")
    txt = "\n".join(md)
    out = a.out or os.path.join(a.dir, "report.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(txt)
    print(txt)
    print(f"\nwritten {out}")


def chunk_of(cid, d):
    for p in sorted(glob.glob(os.path.join(d, "chunk_*.jsonl"))):
        s = int(os.path.basename(p)[6:13])
        if s <= cid < s + 100000:
            pass
    # chunk files are named by start; find the greatest start <= cid
    starts = sorted(int(os.path.basename(p)[6:13]) for p in glob.glob(os.path.join(d, "chunk_*.jsonl")))
    s = max(x for x in starts if x <= cid)
    return f"chunk_{s:07d}.jsonl"


if __name__ == "__main__":
    main()
