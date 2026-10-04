import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kit'))
from bmkit import *
from carve import part_guide
from template import body_template, quadruped_spec, fit_template

# bear, stage-1 cage on the kit's quadruped TEMPLATE (c4). This program authors no topology: J, the plan, counts,
# landmarks and the named offsets below; every face comes from kit/template.py and every vertex from the guide.
J = dict(
    pelvis=(0.0, 0.60, 0.62), spine=(0.0, 0.10, 0.66), neck=(0.0, -0.43, 0.67),
    head=(0.0, -0.58, 0.60), snout=(0.0, -0.845, 0.47),
    tail0=(0.0, 0.74, 0.66), tail1=(0.0, 0.812, 0.64),
    shoulderL=(0.24, -0.05, 0.60), elbowL=(0.238, -0.045, 0.25), wristL=(0.232, -0.075, 0.115),
    pawL=(0.228, -0.265, 0.04),
    hipL=(0.24, 0.60, 0.60), kneeL=(0.238, 0.64, 0.245), hockL=(0.232, 0.71, 0.12),
    toeL=(0.228, 0.53, 0.04),
)
PLAN = dict(spine=['pelvis', 'spine', 'neck', 'head', 'snout'],
            limbs=dict(fore=['shoulderL', 'elbowL', 'wristL', 'pawL'], hind=['hipL', 'kneeL', 'hockL', 'toeL']),
            extra=[])                                   # the stub tail: J names it, so the guide and the template carry it
# a plantigrade column leg: two cap rings carry the shoulder and the thigh down to the elbow and the knee, the hock is
# the heel (2 rings); a stub tail; one row between the blocks (they are as long as the trunk is deep); no neck ring
# after the socket loop (the neck is shorter than it is wide)
COUNTS = dict(neck=0, head=4, muzzle=2, tail=1, ear=2, trunk_mid=1,
              fore=dict(hinge=(3, 2), mass=(0, 0), cap=2), hind=dict(hinge=(3, 2), mass=(0, 0, 0), cap=2))
META = dict(creature='bear', model='opus', cage=True, template='quadruped', J=J, plan=PLAN, intended={},
            landmarks=dict(eye=(0.105, -0.700, 0.605), mouth=(0.045, -0.80, 0.455),
                           ear=(0.140, -0.625, 0.705), ear_tip=(0.168, -0.620, 0.790)))
# the planes broken on purpose, x the local width (clamped by the kit)
OFFSETS = dict(withers=0.04, scapula=0.05, scapula_edge=0.03, haunch=0.05, haunch_edge=0.03, belly_tuck=0.02,
               brow=0.04, jaw=0.03)


def stage1(k):
    guide = part_guide(k, torso_fill=True)
    tm = body_template('quadruped', COUNTS)
    spec = quadruped_spec(tm, k, offsets=OFFSETS, span=dict(hind=(1.0, 0.7)), paw=0.45,
                          ear=dict(a=0.2, b=0.12, f=[0.5, 0.9], s=[0.95, 0.6]))
    return fit_template(tm, k, guide, spec)


run(META, stage1)
