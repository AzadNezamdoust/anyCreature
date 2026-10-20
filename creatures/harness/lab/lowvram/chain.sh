#!/bin/bash
# full <8 GB chain: bash chain.sh <animal> <prompt_index> <seed>
set -e; a=$1; k=$2; s=$3; G=/e/gen3d; L=$G/lowvram; D=$L/$a; mkdir -p $D
export HF_HOME=E:/gen3d/hf PYTHONIOENCODING=utf-8 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True CAP=1
cd $G; PY=./venv/Scripts/python
sed -i "s/prompts('wolf')\[3\]/prompts(sys.argv[5])[int(sys.argv[6])]/; s/manual_seed(103)/manual_seed(int(sys.argv[7]))/" $L/tests/t2i.py
T=$(date +%s); echo "[$a] t2i";   $PY $L/tests/t2i.py offload $D/ref.png 1024 25 $a $k $s 2>&1 | grep -E '^(gen|PEAK)'
echo "[$a] mask";  $PY $L/tests/mask.py $D/ref.png $D/ref_rgba.png
echo "[$a] shape"; $PY $L/tests/shape.py $D/ref_rgba.png $D/raw.obj 380 8000 1 50 0 2>&1 | grep -E '^(gen|PEAK gen|faces)'
echo "[$a] clean"; $PY clean8.py $D/raw.obj $D/final.obj
echo "[$a] quadriflow"; (cd lowpoly && CUDA_VISIBLE_DEVICES= ../venv_lp/Scripts/python run_classic.py quadriflow --in-root $L --out-root $L/_lp --animals $a --budgets 5000 | tail -2)
cp $L/_lp/quadriflow/${a}_5000.obj $D/lowpoly_quad.obj; cp $D/lowpoly_quad.obj $D/lowpoly_$a.obj
echo "[$a] paint"; $PY $L/tests/paint.py $D/final.obj $D/ref_rgba.png $D/tex v=6 off=1 tile=256 vt=1 2>&1 | grep -E '^(paint|PEAK paint|glb)|Error'
cp $D/tex/textured.glb $D/textured.glb
echo "[$a] rig";   mkdir -p $D/rig; CUDA_VISIBLE_DEVICES= $PY $L/tests/rigrun.py $a $D/lowpoly_%s.obj $D/rig
(cd rig && node export_glb.js $D/rig/out/${a}_build.json $D/rigged.glb)
echo "[$a] total $(( $(date +%s) - T ))s"
for m in final lowpoly_quad; do python E:/Github/anyCreature/harness/lab/render.py $D/$m.obj $D/$m.png; done
python E:/Github/anyCreature/harness/lab/render.py $D/rigged.glb $D/rigged.png
