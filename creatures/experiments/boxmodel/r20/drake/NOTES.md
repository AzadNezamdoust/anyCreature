# drake (r20)
Design: low-slung wingless green dragon; long flat wedge snout, two bone horns swept far back, rust-red dorsal spines from neck to tail tip, heavy tapering tail, cream belly plates.
Base: copied from opus/wolf/wolf.py; PARAMS (SNOUT, TAIL, HEAD_SCALE, ZS height scale, SPIKES, SPIKE_H).
- s1 r01 snout/tail/horns: reads dog (long legs); r02 ZS=0.76: self-intersection (J double-scaled); r03 threshold: same; r04 J0 unscaled tables: hind intersect; r05 thinner thigh: same; r06 straighter stifle: same; r07 ZS 0.82: same; r08 thinner lower thigh: same; r09 lower-thigh section moved back: PASS; r10 horns swept lower/back -> LOCK.
- s2 r01 IoU min 0.954. s3 r01 7 colours PASS 1490 tris (spikes small); s4 r01 spikes x1.9 PASS; r02 final+orbit all PASS, glbcheck OK, 1490 tris (spikes enlarged).
Weakness: head/legs still canine-derived (wolf cage); horns are the extruded ear fins, broad at base.
