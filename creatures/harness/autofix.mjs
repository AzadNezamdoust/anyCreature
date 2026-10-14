#!/usr/bin/env node
// ACS harness — automatic animation corrections.
//
// Three things the engine BLOCKS on are pure arithmetic: the animator should not be
// hand-solving them, and every creature's animation is different so they cannot be
// hardcoded. fit.py runs this before a round is spent.
//
//   ground_clip  -> measure the penetration per frame, add it to the ROOT's ty.
//                   Chasing it with joint angles does not converge: a contact point
//                   rotating about a joint above it always dips below the tangent plane.
//   clip_closes  -> give every track a final key equal to its first key.
//   carrier compensation -> a joint that must keep its own world aim while the body
//                   turns for some OTHER purpose gets the parent's inverse rotation
//                   written into it. Do NOT iterate on angles: once the parent passes
//                   vertical the atan2 jumps and the correction diverges (measured: the
//                   head ended up facing backwards and the neck tore).
//                   The compensation is SUBORDINATE to the action's purpose — a head
//                   aimed forward pushes its muzzle out front, and if that overtakes the
//                   declared effector the strike reads as a head-butt. So the share is
//                   solved for, not assumed.
//
//   usage: node harness/autofix.mjs <spec.json> [out.json]
// .mjs in this harness means ESM; the engine is CommonJS, so pull it in with createRequire.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const EP = path.join(__dirname, '..', 'engine', 'core') + path.sep;

function closeLoop(tracks){
  for(const tr of Object.values(tracks))
    for(const [ax,k] of Object.entries(tr)){
      if(!k.length) continue;
      const v0=k[0][1];
      if(k[k.length-1][0]>=0.999) k[k.length-1][1]=v0; else k.push([1,v0]);
    }
  return tracks;
}


function groundFix(spec, rootBone){
  const { compile }=require(EP+'compile.js');
  const { buildSkeleton, localTranslations }=require(EP+'skeleton.js');
  const { skinVerts, jointWorlds }=require(EP+'checks.js');
  const mirrorName=n=>n.startsWith('L')?'R'+n.slice(1):n;
  const work=JSON.parse(JSON.stringify(spec));
  require(EP+'relative.js').resolveJoints(work);
  const sk=buildSkeleton(work), meshes=compile(work);
  try{ require(EP+'compile.js').drainInfo(); }catch(e){}
  const locals=localTranslations(sk);
  const GROUND=Math.min(...meshes.flatMap(m=>m.V).map(v=>v[1]));
  const N=24;
  for(const [name,a0] of Object.entries(work.animations)){
    const tracks={...a0.tracks}, ph=a0.mirror_phase??0;
    for(const cn of work.mirror||[]) for(const jn of (work.chains[cn]||[])){
      if(!tracks[jn]||tracks[mirrorName(jn)]) continue; const d={};
      for(const [ax,k] of Object.entries(tracks[jn])){ const f=(ax==='ry'||ax==='rz'||ax==='tx')?-1:1;
        d[ax]=k.map(([t,v])=>[(t+ph)%1,v*f]).sort((p,q)=>p[0]-q[0]); }
      tracks[mirrorName(jn)]=d; }
    const a={name,tracksResolved:tracks};
    const lift=[];
    for(let s=0;s<=N;s++){ const w=jointWorlds(sk,locals,a,s/N);
      let mn=1e9;
      for(const m of meshes){ const V2=skinVerts(m,sk,w); for(const v of V2) if(v[1]<mn) mn=v[1]; }
      lift.push(Math.max(0, GROUND-mn)); }
    // 平滑一點，免得補償本身變成抖動
    const sm=lift.map((v,i)=>Math.max(v,lift[(i+N)%(N+1)],lift[(i+1)%(N+1)],lift[(i-1+N+1)%(N+1)]));
    if(Math.max(...sm)<0.005) continue;
    const T=spec.animations[name].tracks;
    T[rootBone]=T[rootBone]||{};
    const base=T[rootBone].ty||[];
    const at2=(k,t)=>{ if(!k.length) return 0; t=((t%1)+1)%1;
      for(let i=0;i<k.length-1;i++){const [t0,v0]=k[i],[t1,v1]=k[i+1];
        if(t>=t0&&t<=t1) return v0+(v1-v0)*(t1===t0?0:(t-t0)/(t1-t0));}
      return k[k.length-1][1]; };
    T[rootBone].ty = sm.map((v,i)=>[+(i/N).toFixed(3), +(at2(base,i/N)+v+0.004).toFixed(4)]);
  }
  return spec;
}


function aimCompensate(spec, clipName, bone, share){
  // 補償 = 直接寫入「父關節世界旋轉的反轉」。
  // 骨頭的世界旋轉 = R_parent(t) · R_anim(t)；令 R_anim = R_parent(t)⁻¹，
  // 世界旋轉就回到單位（＝休息時的朝向），頭就一直盯著前方。
  // 不要用角度迭代：父關節越過垂直時 atan2 會跳，補償跟著發散（實測頭會翻到背面、脖子被扯破）。
  const { compile }=require(EP+'compile.js');
  const { buildSkeleton, localTranslations }=require(EP+'skeleton.js');
  const { jointWorlds }=require(EP+'checks.js');
  const k=share??1, N=16;
  const work=JSON.parse(JSON.stringify(spec));
  require(EP+'relative.js').resolveJoints(work);
  const sk=buildSkeleton(work); compile(work);
  try{ require(EP+'compile.js').drainInfo(); }catch(e){}
  const locals=localTranslations(sk);
  const anim={name:clipName, tracksResolved:work.animations[clipName].tracks};
  const bi=sk.index[bone]; if(bi==null) return;
  const pi=sk.joints[bi].parent; if(pi<0) return;
  // 欄位優先的 4x4：m[col*4+row]。轉置＝旋轉的反轉。
  const eulXYZ=(m)=>{                       // 對照 three.js Euler 'XYZ'
    const m11=m[0],m12=m[4],m13=m[8],m22=m[5],m23=m[9],m32=m[6],m33=m[10];
    const c=v=>Math.max(-1,Math.min(1,v));
    let x,y,z;
    y=Math.asin(c(m13));
    if(Math.abs(m13)<0.9999999){ x=Math.atan2(-m23,m33); z=Math.atan2(-m12,m11); }
    else { x=Math.atan2(m32,m22); z=0; }
    return [x*57.29578,y*57.29578,z*57.29578];
  };
  const rx=[],ry=[],rz=[];
  for(let i=0;i<=N;i++){
    const t=i/N, w=jointWorlds(sk,locals,anim,t), P=w[pi];
    // 取出旋轉並轉置（列變欄）
    const T=[P[0],P[4],P[8],0, P[1],P[5],P[9],0, P[2],P[6],P[10],0, 0,0,0,1];
    const [ex,ey,ez]=eulXYZ(T);
    rx.push([+t.toFixed(3), +(ex*k).toFixed(2)]);
    ry.push([+t.toFixed(3), +(ey*k).toFixed(2)]);
    rz.push([+t.toFixed(3), +(ez*k).toFixed(2)]);
  }
  spec.animations[clipName].tracks[bone]={rx,ry,rz};
}

// 補償要「服從動作的目的」。頭轉正 → 吻端往前吐；吻端一旦超過作用端，
// 這個動作就從踢變成頭撞。所以補償的幅度不是常數，是解出來的：
// 從 1.0 往下找，找到最大的 share，使得峰值幀時作用端仍在最前面。
function aimSubordinate(spec, clipName, bone, effRe, marginFrac){
  const { compile }=require(EP+'compile.js');
  const { buildSkeleton, localTranslations }=require(EP+'skeleton.js');
  const { skinVerts, jointWorlds }=require(EP+'checks.js');
  const lab=m=>`${m.material}@${m.chain||m.part||'?'}`;
  const test=(share)=>{
    const t=JSON.parse(JSON.stringify(spec));
    aimCompensate(t, clipName, bone, share);
    const work=JSON.parse(JSON.stringify(t));
    require(EP+'relative.js').resolveJoints(work);
    const sk=buildSkeleton(work), meshes=compile(work);
    try{ require(EP+'compile.js').drainInfo(); }catch(e){}
    const locals=localTranslations(sk);
    const a={name:clipName, tracksResolved:work.animations[clipName].tracks};
    // 取樣密度要跟驗證端一致（48）。之前解算器用 32、驗證用 48，
    // 峰值幀不同、結論就相反 —— 解出來的東西過不了自己的驗收。
    const N=48; const glob=[];
    for(let f=0;f<=N;f++){ const w=jointWorlds(sk,locals,a,f/N);
      let z=-1e9; for(const m of meshes){ const V=skinVerts(m,sk,w); for(const v of V) if(v[2]>z)z=v[2]; }
      glob.push(z); }
    const bz=Math.max(...glob);
    // 不只看峰值那一幀：峰值附近 5% 帶內的每一幀都要成立，才不會因為取樣位置不同而翻盤
    let worst=1e9, effAt=0, othAt=0, top='';
    for(let f=0;f<=N;f++){
      if(glob[f] < bz-0.05*Math.abs(bz)) continue;
      const w=jointWorlds(sk,locals,a,f/N);
      let effZ=-1e9, othZ=-1e9, who='';
      for(const m of meshes){ const V=skinVerts(m,sk,w); let z=-1e9; for(const v of V) if(v[2]>z)z=v[2];
        if(effRe.test(lab(m))){ if(z>effZ) effZ=z; } else if(z>othZ){ othZ=z; who=lab(m); } }
      const d=effZ-othZ;
      if(d<worst){ worst=d; effAt=effZ; othAt=othZ; top=who; }
    }
    return {ok: worst > (marginFrac??0.02), effZ:effAt, othZ:othAt, top};
  };
  let best=0, r=null;
  for(const sh of [1.0,0.85,0.7,0.55,0.4,0.25,0.1,0]){
    const q=test(sh);
    if(q.ok){ best=sh; r=q; break; }
  }
  aimCompensate(spec, clipName, bone, best);
  console.error(`    ${bone} 補償 share=${best}${r?`（作用端 ${r.effZ.toFixed(2)} > 其餘最前 ${r.top} ${r.othZ.toFixed(2)}）`:'（找不到可行值）'}`);
}

function autofix(spec) {
  const axis = Object.keys(spec.chains || {})[0];
  const root = (spec.chains[axis] || [])[0];
  const eff = new Set(Object.entries(spec.function || {}).filter(([, v]) => v === 'effector').map(([k]) => k));
  for (const [name, clip] of Object.entries(spec.animations || {})) {
    if (clip.loop === false) closeLoop(clip.tracks);
  }
  // Compensate any chain that is NOT on the path to the effector but carries an eye:
  // the thing that has to keep watching where the action is going. Derived, not configured.
  if (eff.size) {
    const eyed = new Set();
    for (const p of spec.parts || []) if (p.type === 'eye' && p.host) {
      for (const [cn, js] of Object.entries(spec.chains || {})) if (js.includes(p.host)) eyed.add(cn);
    }
    for (const cn of eyed) {
      if (eff.has(cn)) continue;
      const bone = (spec.chains[cn] || [])[0];
      if (!bone) continue;
      for (const name of Object.keys(spec.animations || {})) {
        if (name !== 'attack') continue;
        aimSubordinate(spec, name, bone, new RegExp([...eff].join('|')), 0.03);
      }
    }
  }
  if (root) groundFix(spec, root);
  return spec;
}
export { autofix, closeLoop, groundFix, aimCompensate, aimSubordinate };
if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  const inp = process.argv[2], outp = process.argv[3] || inp;
  if (!inp) { console.error('usage: node harness/autofix.mjs <spec.json> [out.json]'); process.exit(2); }
  const spec = JSON.parse(fs.readFileSync(inp, 'utf8'));
  fs.writeFileSync(outp, JSON.stringify(autofix(spec), null, 1));
  console.error(`[autofix] ${path.basename(inp)} -> ${path.basename(outp)}`);
}
