// Bridge: rig.py build JSON -> anyCreature engine skeleton/anim/GLB writer (no new writer).
const fs = require('fs');
const E = 'E:/Github/anyCreature/engine/core/';
const { buildSkeleton, inverseBindMatrices, exportNames } = require(E + 'skeleton.js');
const { compileAnims } = require(E + 'anim.js');
const { writeGLB } = require(E + 'glb.js');
const b = JSON.parse(fs.readFileSync(process.argv[2]));
const spec = b.spec;
const sk = buildSkeleton(spec);
const anims = compileAnims(spec, sk);
const names = exportNames(spec, sk);
const mesh = { material: 'skin', color: '#9a8f84', rough: 0.9, V: b.V, F: b.F, skin: b.skin, smoothAngle: 60 };
const n = writeGLB({ meshes: [mesh], skeleton: sk, ibm: inverseBindMatrices(sk), anims }, process.argv[3],
  { names, asset: { extras: { source_spec: spec } } });
console.log(process.argv[3], n, 'bytes', sk.joints.length, 'joints', anims.map(a => a.name).join(','));
