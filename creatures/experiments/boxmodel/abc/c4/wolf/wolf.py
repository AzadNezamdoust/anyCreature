import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from carve import part_guide
from template import body_template, quadruped_spec, fit_template

# wolf, stage-1 cage on the kit's quadruped TEMPLATE (c4). This program authors no topology: J, the plan, counts,
# landmarks and the named offsets below; every face comes from kit/template.py and every vertex from the guide.
J = dict(
    pelvis=(0.0, 0.33, 0.60), spine=(0.0, -0.05, 0.62), chest=(0.0, -0.19, 0.66), neck=(0.0, -0.41, 0.73),
    head=(0.0, -0.62, 0.87), snout=(0.0, -0.845, 0.79),
    tail0=(0.0, 0.46, 0.55), tail1=(0.0, 0.62, 0.38), tail2=(0.0, 0.83, 0.17),
    shoulderL=(0.106, -0.29, 0.56), elbowL=(0.106, -0.285, 0.345), wristL=(0.112, -0.31, 0.135),
    pawL=(0.117, -0.42, 0.03),
    hipL=(0.105, 0.30, 0.56), kneeL=(0.105, 0.285, 0.345), hockL=(0.105, 0.415, 0.235),
    toeL=(0.108, 0.36, 0.03),
)
PLAN = dict(spine=['pelvis', 'spine', 'chest', 'neck', 'head', 'snout'],
            limbs=dict(fore=['shoulderL', 'elbowL', 'wristL', 'pawL'], hind=['hipL', 'kneeL', 'hockL', 'toeL']),
            extra=[['tail0', 'tail1', 'tail2']])
COUNTS = dict(neck=1, head=4, muzzle=2, tail=6, ear=2, trunk_mid=3,
              fore=dict(hinge=(3, 2), mass=(0, 1), cap=2), hind=dict(hinge=(3, 3), mass=(0, 0, 1), cap=2))
META = dict(creature='wolf', model='opus', cage=True, template='quadruped', J=J, plan=PLAN, intended={},
            landmarks=dict(eye=(0.062, -0.705, 0.845), mouth=(0.030, -0.775, 0.765),
                           ear=(0.072, -0.600, 0.975), ear_tip=(0.090, -0.570, 1.120)),
            iou_floor=dict(front=0.83))                  # as c3: the sheet's front view draws the ruff wider than its top view
# the planes broken on purpose, x the local width (clamped by the kit)
OFFSETS = dict(withers=0.03, scapula=0.06, scapula_edge=0.04, haunch=0.06, haunch_edge=0.04, belly_tuck=0.03,
               ruff=0.06, cheek=0.08, brow=0.05, jaw=0.04)


def stage1(k):
    guide = part_guide(k, torso_fill=True)
    tm = body_template('quadruped', COUNTS)
    spec = quadruped_spec(tm, k, offsets=OFFSETS, ear=dict(a=0.16, b=0.19, f=[0.5, 0.96], s=[0.95, 0.3]))
    return fit_template(tm, k, guide, spec)


run(META, stage1)
