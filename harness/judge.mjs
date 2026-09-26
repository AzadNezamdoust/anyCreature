// Generic creature mechanical judge (engine layer, L1) — pure numeric measurement, zero LLM, zero browser.
// The engine contains no creature-specific vocabulary; all identity claims live in the spec JSON.
//
// usage:  node judge.mjs <model.glb> <outDir> <name> [--spec creature.json] [--stage LOW|MID|HIGH]
//   no --spec = measure only, emit metrics JSON (for humans or for scoring)
//   with --spec = check every claim in the spec; any failure exits 1 (symptom-first messages)
//
// WHERE THE NUMBERS COME FROM. This used to launch a headless Chromium, load the
// model into three.js, render five views, and read the pixels back. Every number
// it wanted was already in the file: part shares are a z-buffer, the palette
// and the baked colour are both in it, and the clip list and skin count are in the glTF header. So the
// measuring moved to harness/outline.py — the tool that already owns every other
// geometry measure in this harness — and this file does what is left: check the
// claims. One measure, one definition, in one place.
//
// Two conventions changed with the move, both toward the tool that survived:
//   · `side` is the LONG profile (outline.py picks the axis), not a fixed +X.
//     Judge's old fixed camera showed a spread-winged creature edge-on and
//     called it a side view.
//   · `tq` and `reartq` are gone; the three-quarter view is `hero`. The two
//     cameras sit within a few degrees of each other and the shares agree to
//     ~1 percentage point, so a band calibrated on `tq` still means what it meant.
//
// spec JSON = { "name": "...", "claims": [ {type, ...params, "label": "plain-language description"} ] }
// Supported claim types (add a new one in CHECKS; keep the engine creature-agnostic):
//   part_exists     {part}                      — a material/part with this name must exist
//   part_visible    {part, view?, min_share}    — minimum share of body pixels the part holds in a given view
//   part_signature  {part, view?, min_share, or_min_span} — signature part: share OR span ratio must clear its bar
//   style_dark      {view?, max_median_lum}     — dark styling: the creature's OWN colour must not be brighter
//   style_light     {view?, min_median_lum}     — light styling: must not fall below the floor
//   rig_skinned     {}                          — must be skinned (bones move nothing without skin weights)
//   anim_named      {names:[...]}               — these named animations must be present
//   tri_budget      {min, max}                  — triangle budget band
//   share_hierarchy {primary:[..],secondary:[..],tertiary:[..],view?,tolerance?} — primary/secondary/tertiary shares ≈6:3:1
//   focal_contrast  {a, b, view?, min_ratio?}   — the two focal parts' shares must differ by ≥N× (default 2)
//   saturation_area {view?, min?, max?}         — how much of the view carries colour, read on the PALETTE
//                                                 (albedo before lighting): min bounds the share at HSV
//                                                 S ≥ 0.30 (default 0.10), max the share at S ≥ 0.50.
//   orbit_consistent {kinds?}                   — no flank of the 8+2 orbit collapses into a blob its
//                                                 neighbours are not (outline.py's `blob` flags)
//   head_reads      {kinds?}                    — the head is visible from every azimuth, is its own mass
//                                                 on the front half, and is not small from everywhere
//                                                 (outline.py's head_merged / head_hidden / head_small)
//
// Views: az000…az315 (az000 = the face, az090 = the creature's left), top, bottom — the
// orbit — plus the legacy four, front / side / top / hero (tq = hero), whose cameras are
// unchanged so a claim written against them still reads the same pixels.
import path from 'path'; import fs from 'fs';
import { spawnSync } from 'child_process';
import { fileURLToPath } from 'url';

const args = process.argv.slice(2);
const si = args.indexOf('--spec');
const specFile = si >= 0 ? args.splice(si, 2)[1] : null;
const sti = args.indexOf('--stage');
const stageFilter = sti >= 0 ? args.splice(sti, 2)[1].toUpperCase() : null; // LOW/MID/HIGH; none = check all
const [src, outDir, name] = args;
if (!src || !outDir || !name) { console.error('usage: node judge.mjs <model> <outDir> <name> [--spec spec.json]'); process.exit(2); }
const root = path.dirname(fileURLToPath(import.meta.url));
const abs = path.resolve(src);
fs.mkdirSync(outDir, { recursive: true });

// ── measure: one call to the one measuring tool ──
// Which views to measure. With no spec, everything: the 8+2 orbit AND the
// legacy four (claims written before the orbit name `side`, `front` and `tq`, and
// those keep their legacy cameras). With a spec, only what its claims read —
// plus hero for the summary line — and the orbit whenever a claim reads it,
// so a colour-only check (calibrate.py) does not pay for ten views.
const ORBIT_CLAIMS = new Set(['orbit_consistent', 'head_reads']);
const VIEW = v => (v === 'tq' || v === 'reartq') ? 'hero' : v;
let wantViews = 'orbit,legacy';
if (specFile) {
  const pre = JSON.parse(fs.readFileSync(specFile, 'utf8'));
  const cl = (pre.claims || []).filter(c => !stageFilter || !c.stage || c.stage.toUpperCase() === stageFilter);
  const vs = new Set(['hero']);
  const DEFAULT_VIEW = { saturation_area: 'hero' };
  for (const c of cl) if (!ORBIT_CLAIMS.has(c.type)) vs.add(VIEW(c.view || DEFAULT_VIEW[c.type] || 'side'));
  // any orbit claim anywhere in the claims file, whatever the stage filter: a HIGH run still writes
  // orbit_sheet.png for the final look (card 03), it just does not judge LOW claims
  if ((pre.claims || []).some(c => ORBIT_CLAIMS.has(c.type)) || [...vs].some(v => /^az\d{3}$|^bottom$/.test(v))) vs.add('orbit');
  wantViews = [...vs].join(',');
}
const outline = path.join(root, 'outline.py');
const run = spawnSync('python3', [outline, abs, outDir, '--views', wantViews], { encoding: 'utf8' });
if (run.status !== 0) {
  console.error('[judge] outline.py failed — it owns every measurement here, so nothing can be judged:\n'
    + (run.stderr || run.stdout || '').trim());
  process.exit(2);
}
const M = JSON.parse(fs.readFileSync(path.join(outDir, 'metrics.json'), 'utf8'));

// `tq`/`reartq` were judge's own camera names; the surviving three-quarter view is `hero`.
const view = v => M.views[VIEW(v)] || {};
const orbit = M.orbit || null;
const names = M.materials || [];
const parts = M.parts || {};
const share = (v, mat) => (view(v).share || {})[mat] ?? 0;
const stats = M.stats || { triangles: M.triangles, skinnedMeshes: 0, animations: [] };

const m = { name, stats, names,
  lum: Object.fromEntries(Object.entries(M.views).map(([vn, d]) => [vn, d.median_lum])),
  hi_sat_share: Object.fromEntries(Object.entries(M.views).map(([vn, d]) => [vn, d.saturated_area])),
  coloured_share: Object.fromEntries(Object.entries(M.views).map(([vn, d]) => [vn, d.coloured_area])),
  palette_source: Object.fromEntries(Object.entries(M.views).map(([vn, d]) => [vn, d.palette_source])),
  parts, whole: M.whole, facing: M.facing,
  orbit: orbit && { flags: orbit.flags, read_set: orbit.read_set, head_best: orbit.head_best,
    head_distinct_views: orbit.head_distinct_views, most_blobby: orbit.most_blobby } };
const metricsPath = path.join(outDir, `${name}_metrics.json`);
fs.writeFileSync(metricsPath, JSON.stringify(m, null, 1));

// A SUMMARY, not the blob. Tool output lands in the conversation permanently and
// the conversation is re-read on every turn afterwards, so a 2KB dump at round 3
// is still being paid for at round 30. `--json` restores the full object.
if (process.argv.includes('--json')) console.log(JSON.stringify(m));
else {
  const v = 'hero';
  console.log(`[judge] ${name}: ${stats.triangles} tris · ${names.length} materials · `
    + `clips ${stats.animations.join('/') || 'none'} · skinned ${stats.skinnedMeshes}`);
  console.log(`        ${v} view: luminance ${m.lum[v]} · coloured area `
    + `${((m.coloured_share[v] || 0) * 100).toFixed(1)}% · saturated area `
    + `${((m.hi_sat_share[v] || 0) * 100).toFixed(1)}% (${m.palette_source[v] === 'albedo' ? 'on the palette' : 'on the baked colour — no palette record'})`);
  const top = Object.entries(parts).sort((a, b) => (share(v, b[0])) - (share(v, a[0]))).slice(0, 3);
  console.log('        biggest in view: ' + top.map(([n]) => `${n} ${(share(v, n) * 100).toFixed(0)}%`).join(' · '));
  if (orbit) console.log(`        orbit (8+2): ${orbit.flags.length ? orbit.flags.length + ' advisory flag(s) — '
    + [...new Set(orbit.flags.map(f => `${f.view} ${f.kind}`))].join(', ') : 'holds from every side'}`
    + ` · sheet ${path.join(outDir, 'orbit_sheet.png')}`);
  console.log(`        full numbers: ${metricsPath}`);
}

// ── Spec mode: check every claim, symptom first ──
if (specFile) {
  const S = JSON.parse(fs.readFileSync(specFile, 'utf8'));
  const bad = [];
  const pct = x => (x * 100).toFixed(2) + '%';
  const CHECKS = {
    part_exists(c){ if(!names.includes(c.part))
      bad.push(`Part "${c.part}" not measurable: no material by that name in the model (part missing, or naming convention not followed)`); },
    part_visible(c){ if(!names.includes(c.part)) return CHECKS.part_exists(c);
      const v=c.view||'side'; const s=share(v,c.part);
      if(s<c.min_share) bad.push(`Part "${c.part}" is nearly invisible in the ${v} view (share ${pct(s)} < ${pct(c.min_share)}) — occluded, too small, or in the wrong place`); },
    part_signature(c){ if(!names.includes(c.part)) return CHECKS.part_exists(c);
      const v=c.view||'side'; const s=share(v,c.part); const sp=(parts[c.part]||{}).span_ratio ?? 0;
      if(!(s>=c.min_share||sp>=c.or_min_span))
        bad.push(`Signature part "${c.part}" is not exaggerated enough: ${v}-view share ${pct(s)} (need ≥${pct(c.min_share)}) and span ratio ${sp} (need ≥${c.or_min_span}) — right now it is just another part; it cannot carry this creature's identity`); },
    // Dark/light now read the creature's OWN colour, not a studio render of it.
    // The old number was the median luminance of a lit beauty pass, which made
    // the verdict a property of a lighting rig nobody ships. This is the unlit
    // baked colour — the palette after the shading stack, AO and shadow
    // included, because brightness is about what ships. The two correlate at
    // r≈0.96 but are not the same scale — the baked colour runs darker — so a
    // threshold carried over from a pre-1.3.2 spec needs re-picking once.
    style_dark(c){ const v=c.view||'side'; const L=view(v).median_lum;
      if(L>c.max_median_lum) bad.push(`Declared dark but its own colour is not dark: ${v}-view median albedo luminance ${L.toFixed(0)}/255 (need ≤${c.max_median_lum}) — push the material colour values darker`); },
    style_light(c){ const v=c.view||'side'; const L=view(v).median_lum;
      if(L<c.min_median_lum) bad.push(`Declared light but its own colour is too dark: ${v}-view median albedo luminance ${L.toFixed(0)}/255 (need ≥${c.min_median_lum})`); },
    // Colour AREA, read on the PALETTE — the albedo the engine records before
    // any lighting (outline.py, palette_source). Two bars, two questions:
    //   floor  share at HSV S ≥ 0.30 — is there any colour, or is this a grey mass
    //   ceiling share at HSV S ≥ 0.50 — is the LOUD colour a spotlight or the base
    // Not the baked colour: the shading stack ramps, boosts and shadows it, and
    // until its shadows became a true multiply they raised S, so the old band on
    // the baked colour was a band on the stack. Do NOT name which surfaces carry
    // it — where the colour goes is the designer's call, only how much.
    saturation_area(c){ const v=c.view||'tq';
      const d=view(v), s=d.saturated_area, col=d.coloured_area ?? s; if(s==null) return;
      const src=d.palette_source==='albedo' ? 'palette' : 'baked colour (no palette record in this file)';
      // The ceiling applies only when a spec asks for it by name. Dropping `max`
      // from claims.json once did not remove the old 0.34, because it lived here
      // as a fallback and went on refusing creatures after it was retired. The
      // floor keeps its default: "reads as a grey lump" is a real failure and
      // nobody has to opt into catching it.
      const lo=(c.min??0.10)*100, p=col*100, q=s*100;
      if(p<lo) bad.push(`Too little colour: only ${p.toFixed(1)}% of the ${VIEW(v)} view carries a nameable colour (HSV S ≥ 0.30 in the ${src}; need ≥${lo.toFixed(0)}%) — the creature reads as a grey mass. Raise the saturation of a mass that deserves the attention, do not tint everything.`);
      if(c.max!=null && q>c.max*100) bad.push(`Too much loud colour: ${q.toFixed(1)}% of the ${VIEW(v)} view is highly saturated (HSV S ≥ 0.50 in the ${src}; need ≤${(c.max*100).toFixed(0)}%) — saturation stops reading as a spotlight when it is the base colour. Quiet the supporting masses and keep the loud colour on the signature.`); },
    rig_skinned(){ if(stats.skinnedMeshes<1)
      bad.push('Model is not skinned: the rig is not bound to the mesh, so animating the bones moves nothing'); },
    anim_named(c){ for(const a of c.names) if(!stats.animations.includes(a))
      bad.push(`Missing named animation ${a} (present: ${stats.animations.join(',')||'none'})`); },
    tri_budget(c){ const t=stats.triangles;
      if(t<c.min||t>c.max) bad.push(`Triangle count ${t} is outside the budget band ${c.min}–${c.max}`); },
    // 6:3:1 hierarchy: the primary / secondary / tertiary part groups must hold roughly
    // 6:3:1 of the frame. An even spread reads as no hierarchy at all — a silhouette needs
    // one mass that clearly leads, one that supports, and detail that stays detail.
    share_hierarchy(c){ const v=c.view||'side';
      const grp=g=>g.reduce((a,p)=>a+(names.includes(p)?share(v,p):0),0);
      const [P,Sc,T]=[grp(c.primary||[]),grp(c.secondary||[]),grp(c.tertiary||[])];
      const tot=P+Sc+T; if(!tot){ bad.push(`631 hierarchy not measurable: primary/secondary/tertiary parts are all 0 in the ${v} view`); return; }
      const tol=c.tolerance??0.15, want=[0.6,0.3,0.1], got=[P/tot,Sc/tot,T/tot];
      const off=got.map((g,i)=>Math.abs(g-want[i]));
      if(Math.max(...off)>tol) bad.push(`Hierarchy ratio off: primary/secondary/tertiary = ${got.map(x=>(x*100).toFixed(0)).join(':')} (target 60:30:10, tolerance ±${tol*100}%) — no dominance; the frame is split evenly`); },
    // No equal-weight focal points: two focal parts of the same size make the eye ping-pong
    // between them and neither one wins. The declared pair's shares must differ by ≥ratio×.
    focal_contrast(c){ const v=c.view||'side';
      for(const p of [c.a,c.b]) if(!names.includes(p)) return CHECKS.part_exists({part:p});
      const A=share(v,c.a), B=share(v,c.b); const hi=Math.max(A,B), lo=Math.min(A,B);
      const ratio=c.min_ratio??2;
      if(lo>0 && hi/lo<ratio) bad.push(`Two focal points of equal weight compete: "${c.a}" ${(A*100).toFixed(1)}% vs "${c.b}" ${(B*100).toFixed(1)}% (need ≥${ratio}× apart) — the eye ping-pongs between them; open up the dominance gap`); },
    // THE ORBIT (8 azimuths + top + bottom, outline.py). Both read the flags
    // outline.py already computed — one definition of each bar, in one place —
    // and they offer options, never an order: which mass to move is the designer's call.
    //   orbit_consistent  no azimuth collapses into a lump its neighbours do not
    //   head_reads        the head is visible, and its own mass, from the front half
    orbit_consistent(c){ if(!orbit){ bad.push('Orbit not measured: outline.py wrote no orbit block (was it run with --views orbit?)'); return; }
      const kinds=c.kinds||['blob'];
      const hits=orbit.flags.filter(f=>kinds.includes(f.kind));
      if(hits.length) bad.push(`The creature falls apart between its main views: ${[...new Set(hits.map(f=>f.view))].join(', ')} — `
        + hits.map(f=>`${f.view}: ${f.why}`).join('; ') + `. Look at orbit_sheet.png; a pose that only reads from the side and the front is a pose built for two cameras`); },
    head_reads(c){ if(!orbit){ bad.push('Orbit not measured: outline.py wrote no orbit block, so the head was never looked at'); return; }
      if(!M.facing || /^none/.test(M.facing.head||'')){ bad.push(`No head found (${(M.facing&&M.facing.head)||'no facing record'}) — name a chain "head" or a joint Head*/Skull* so the head can be measured`); return; }
      const kinds=c.kinds||['head_merged','head_hidden','head_small'];
      const hits=orbit.flags.filter(f=>kinds.includes(f.kind));
      if(hits.length) bad.push(`The head does not read from every side: `
        + hits.map(f=>`${f.view} ${f.kind.replace('head_','')}: ${f.why}`).join('; ') + ` — lift it clear of the shoulder line, give it a neck, or make it bigger; see orbit_sheet.png`); },
  };
  const claims=(S.claims||[]).filter(c=>!stageFilter || !c.stage || c.stage.toUpperCase()===stageFilter);
  // enforce: "block" stops the build; "advise" measures and reports and never
  // stops it. Taste is advice — a number that says the eye will ping-pong is
  // worth reading and is not worth a rebuild. Correctness is a gate: a rig that
  // does not deform or a clip that does not exist is broken, not debatable.
  // Every claim carries the tag explicitly; see harness/gates.json for the map
  // of the whole system, and for `when` (allocate up front vs verify after).
  const advice=[];
  for(const c of claims){
    const fn=CHECKS[c.type];
    if(!fn){ bad.push(`Spec contains a claim type the engine does not recognise: "${c.type}"`); continue; }
    const before=bad.length; fn(c);
    if(bad.length===before) continue;
    const mine=bad.splice(before);
    if(c.label) mine[mine.length-1] += ` [${c.label}]`;
    if((c.enforce||'block')==='advise') advice.push(...mine); else bad.push(...mine);
  }
  if(advice.length){ console.log('\n'+'-'.repeat(68));
    console.log('ADVICE — measured, not blocking. Your judgment, your call:');
    for(const a of advice) console.log('  · '+a);
    console.log('-'.repeat(68)); }
  if(bad.length){ console.log('\n'+'='.repeat(68));
    console.log(`BLOCKING — against spec "${S.name||path.basename(specFile)}", the following fail and must be fixed:`);
    for(const b of bad) console.log('  ✗ '+b);
    console.log('='.repeat(68)+`\n${bad.length} blocking item(s). exit 1 — cannot ship.`);
    process.exit(1); }
  console.log(advice.length
    ? `[judge] Spec "${S.name||''}" — nothing blocking. ${advice.length} advisory item(s) above; read them, then decide.`
    : `[judge] Spec "${S.name||''}" — all claims pass.`);
}
