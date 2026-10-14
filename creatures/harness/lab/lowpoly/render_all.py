"""Render shape + topology sheets for every <method>/<animal>_<budget>.obj.
  python render_all.py <method> [<out-root>]      (system python)"""
import sys, os, glob, subprocess
LAB = 'E:/Github/anyCreature/harness/lab'
root = sys.argv[2] if len(sys.argv) > 2 else 'E:/gen3d/lowpoly'
for obj in sorted(glob.glob(os.path.join(root, sys.argv[1], '*.obj'))):
    b = obj[:-4]
    subprocess.run([sys.executable, f'{LAB}/render.py', obj, b + '.png'])
    subprocess.run([sys.executable, f'{LAB}/wire.py', obj, b + '_wire.png'])
