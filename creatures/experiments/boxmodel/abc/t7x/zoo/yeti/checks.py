"""Every-round checks wrapper: runs checks_blender.py on a GLB, composes orbit18_sheet.jpg, face/separation sheet.
    py -3.11 checks.py <glb> <outdir> [title]"""
import sys, os, subprocess, glob
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'kit'))
import run as R
glb, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
title = sys.argv[3] if len(sys.argv) > 3 else 'yeti'
here = os.path.dirname(os.path.abspath(__file__))
p = subprocess.run([R.blender_exe(), '-b', '--factory-startup', '-P', os.path.join(here, 'checks_blender.py'), '--', glb, out],
                   capture_output=True, text=True, encoding='utf-8', errors='replace')
print('\n'.join(l for l in p.stdout.splitlines() if l.startswith('SEPARATION') or 'Error' in l))
lab = dict(h000='az0 front', h045='az45', h090='az90 left side', h135='az135', h180='az180 rear', h225='az225', h270='az270 right side', h315='az315',
           top='top', bottom='bottom', u000='+45 az0', u090='+45 az90', u180='+45 az180', u270='+45 az270',
           l000='-45 az0', l090='-45 az90', l180='-45 az180', l270='-45 az270')
tiles = [(os.path.join(out, f'{k}.png'), v) for k, v in lab.items()]
R.sheet(tiles, os.path.join(out, 'orbit18_sheet.jpg'), cols=6, tile=360, title=f'{title}: 18-view sphere orbit')
R.sheet([(os.path.join(out, 'face_34.png'), 'face 3/4 close-up'), (os.path.join(out, 'sep_rear_low.png'), 'separation: rear low'),
         (os.path.join(out, 'sep_side_low.png'), 'separation: side low'), (os.path.join(out, 'sep_front_low.png'), 'separation: front low')],
        os.path.join(out, 'face_separation.jpg'), cols=4, tile=480, title=open(os.path.join(out, 'separation.json')).read().replace('\n', ' '))
print('sheets:', os.path.join(out, 'orbit18_sheet.jpg'))
ref = os.path.join(here, 'reference')
R.sheet([(os.path.join(ref, 'side.png'), 'reference side'), (os.path.join(out, 'h090.png'), 'model az90'),
         (os.path.join(ref, 'front.png'), 'reference front'), (os.path.join(out, 'h000.png'), 'model az0'),
         (os.path.join(ref, 'rear.png'), 'reference rear'), (os.path.join(out, 'h180.png'), 'model az180')],
        os.path.join(here, 'side_by_side_sheet.jpg'), cols=2, tile=420, title='yeti: reference sheet | stage-4 model')
