from PIL import Image, ImageDraw
poses=['arm_reach','arm_raise','leg_kick','crouch']; views=['hero','side']
W=320
im=Image.new('RGB',(W*4,W*len(poses)+30),'white'); d=ImageDraw.Draw(im)
for c,lab in enumerate(['A baseline (zoo/werewolf)','B joint_graph']):
    d.text((c*2*W+10,8),lab,fill='black')
for r,p in enumerate(poses):
    for c,dirn in enumerate(['baseline_rom','candidate_rom']):
        for v,vn in enumerate(views):
            im.paste(Image.open(f'{dirn}/pose_{p}_{vn}.png').convert('RGB').resize((W,W)),(c*2*W+v*W,30+r*W))
    d.text((5,30+r*W+5),p,fill='red')
im.save('ab_compare.jpg',quality=88)
for i,dirn in enumerate(['baseline_rom','candidate_rom']):
  im2=Image.new('RGB',(W*2,W*4),'white')
  for r,p in enumerate(poses):
    for v,vn in enumerate(views):
      im2.paste(Image.open(f'{dirn}/pose_{p}_{vn}.png').convert('RGB').resize((W,W)),(v*W,r*W))
  im2.save(f'posed_{"AB"[i]}.jpg',quality=88)
