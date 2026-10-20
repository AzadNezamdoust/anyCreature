"""Stage-4 checks: runs checks_blender.py on the GLB, composes orbit18_sheet.jpg and side_by_side.jpg (sheet views | model).
    py -3.11 checks.py <glb> <outdir>"""
import sys, os, subprocess, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'kit'))
import run as R
here = os.path.dirname(os.path.abspath(__file__))
glb, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
p = subprocess.run([R.blender_exe(), '-b', '--factory-startup', '-P', os.path.join(here, 'checks_blender.py'), '--', glb, out],
                   capture_output=True, text=True, encoding='utf-8', errors='replace')
print('\n'.join(l for l in p.stdout.splitlines() if l.startswith('SEPARATION') or 'Error' in l))
lab = dict(h000='az0 front', h045='az45', h090='az90 left side', h135='az135', h180='az180 rear', h225='az225', h270='az270 right side',
           h315='az315', top='top', bottom='bottom', u000='+45 az0', u090='+45 az90', u180='+45 az180', u270='+45 az270',
           l000='-45 az0', l090='-45 az90', l180='-45 az180', l270='-45 az270')
R.sheet([(os.path.join(out, f'{k}.png'), v) for k, v in lab.items()], os.path.join(here, 'orbit18_sheet.jpg'), cols=6, tile=360,
        title='stag: 18-view sphere orbit (stage-4 GLB)')
ref = os.path.join(here, 'reference')
tiles = []
for r, m, t in (('side', 'h090', 'side'), ('front', 'h000', 'front'), ('rear', 'h180', 'rear'), ('top', 'top', 'top')):
    tiles += [(os.path.join(ref, f'{r}.png'), f'sheet {t}'), (os.path.join(out, f'{m}.png'), f'model {t}')]
tiles += [(os.path.join(out, 'hero.png'), 'model hero'), (os.path.join(out, 'face_34.png'), 'model face 3/4')]
R.sheet(tiles, os.path.join(here, 'side_by_side.jpg'), cols=4, tile=440, title='stag: reference sheet | final (stage 4)')
print('separation:', open(os.path.join(out, 'separation.json')).read().replace('\n', ' '))
