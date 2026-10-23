import json, sys
o = sys.argv[1]
s = json.load(open(o + r'\push_a.json'))
k = lambda *pts: [list(p) for p in pts]
s['animations'] = {
 'idle': {'duration': 2.6, 'loop': True, 'tracks': {
   'Hips': {'ty': k((0, 0), (0.5, 0.01), (1, 0))},
   'Chest': {'rx': k((0, 0), (0.5, 1.5), (1, 0))},
   'Skull': {'rx': k((0, 1), (0.5, -2), (1, 1)), 'ry': k((0, 0), (0.3, 4), (0.7, -3), (1, 0))},
   'JawRoot': {'rx': k((0, 0), (0.4, 0), (0.55, 6), (0.7, 0), (1, 0))},
   'Tail1': {'ry': k((0, 6), (0.5, -6), (1, 6))},
   'Tail2': {'ry': k((0, -4), (0.25, 5), (0.75, -7), (1, -4))},
   'Tail3': {'ry': k((0, -5), (0.5, 7), (1, -5))}}},
 'move': {'duration': 1.0, 'loop': True, 'mirror_phase': 0.5, 'tracks': {
   'LFShoulder': {'ry': k((0, -25), (0.5, 20), (1, -25)), 'rz': k((0, 0), (0.5, 0), (0.7, 14), (0.9, 0), (1, 0))},
   
   'LBHip': {'ry': k((0, 20), (0.5, -25), (1, 20)), 'rz': k((0, 0), (0.2, 14), (0.4, 0), (1, 0))},
   
   'Loin': {'ry': k((0, 5), (0.5, -5), (1, 5))},
   'Skull': {'ry': k((0, -4), (0.5, 4), (1, -4))},
   'Tail1': {'ry': k((0, -10), (0.5, 10), (1, -10))},
   'Tail2': {'ry': k((0, -8), (0.25, 4), (0.5, 8), (0.75, -4), (1, -8))},
   'Tail3': {'ry': k((0, 6), (0.5, -10), (1, 6))}}},
 'attack': {'duration': 0.9, 'loop': False, 'tracks': {
   'Rump': {'tz': k((0, 0), (0.3, -0.1), (0.52, 0.5), (0.75, 0.18), (1, 0)),
            'ty': k((0, 0), (0.3, 0), (0.5, 0.05), (0.7, 0.01), (1, 0))},
   'Chest': {'rx': k((0, 0), (0.3, -6), (0.52, 4), (1, 0))},
   'Skull': {'rx': k((0, 0), (0.3, -16), (0.48, -10), (0.56, 2), (1, 0))},
   'JawRoot': {'rx': k((0, 0), (0.3, 13), (0.48, 15), (0.56, 0), (1, 0))},
   'LFShoulder': {'ry': k((0, 0), (0.3, 12), (0.52, -18), (0.75, -6), (1, 0))},
   'LBHip': {'ry': k((0, 0), (0.3, 10), (0.52, -14), (0.75, -4), (1, 0))},
   'Tail1': {'ry': k((0, 0), (0.3, 14), (0.55, -12), (1, 0))},
   'Tail2': {'ry': k((0, 0), (0.3, 10), (0.55, -10), (1, 0))}}},
}
R = lambda a, b: [a, b]
s['joint_range'] = {
 'Rump': {'rx': R(-20, 20), 'rz': R(-15, 15)}, 'Hips': {'rx': R(-20, 20), 'rz': R(-15, 15)},
 'Loin': {'rx': R(-20, 20), 'ry': R(-25, 25), 'rz': R(-15, 15)}, 'Chest': {'rx': R(-20, 20), 'ry': R(-20, 20), 'rz': R(-15, 15)},
 'Shoulders': {'rx': R(-20, 20), 'ry': R(-20, 20)}, 'Neck': {'rx': R(-25, 25), 'ry': R(-30, 30)},
 'HeadRoot': {'rx': R(-25, 25), 'ry': R(-30, 30)}, 'Skull': {'rx': R(-30, 25), 'ry': R(-30, 30), 'rz': R(-15, 15)},
 'Snout': {'rx': R(-5, 5)}, 'Snout2': {'rx': R(-5, 5)}, 'NoseTip': {'rx': R(-5, 5)},
 'JawRoot': {'rx': R(-5, 45)}, 'Jaw1': {'rx': R(-5, 5)}, 'JawTip': {'rx': R(-5, 5)},
 'TailRoot': {'rx': R(-30, 30), 'ry': R(-35, 35)}, 'Tail1': {'rx': R(-30, 30), 'ry': R(-40, 40)},
 'Tail2': {'rx': R(-30, 30), 'ry': R(-40, 40)}, 'Tail3': {'rx': R(-30, 30), 'ry': R(-40, 40)}, 'TailTip': {'rx': R(-30, 30), 'ry': R(-40, 40)},
 'LFShoulder': {'rx': R(-50, 50), 'ry': R(-30, 30), 'rz': R(-30, 30)}, 'LFElbow': {'rx': R(-10, 90)},
 'LFWrist': {'rx': R(-40, 40)}, 'LFToe': {'rx': R(-30, 30)},
 'LBHip': {'rx': R(-50, 55), 'ry': R(-30, 30), 'rz': R(-30, 30)}, 'LBKnee': {'rx': R(-20, 80)},
 'LBHock': {'rx': R(-40, 60)}, 'LBToe': {'rx': R(-30, 30)},
}
# HIGH colour: lift foot value off the leg (contrast_adjacent), tooth below highlight
s['palette']['hide_foot']['color'] = '#8b9a64'
s['palette']['tooth']['color'] = '#e2d6ad'
json.dump(s, open(o + r'\crocodile.json', 'w'), indent=1)

