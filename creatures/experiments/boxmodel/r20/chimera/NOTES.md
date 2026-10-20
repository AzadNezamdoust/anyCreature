# chimera (r20)
Design: maned lion (broad short head, dark red-brown mane) with a grey goat head on a neck rising from mid-back with ridged horns, and a green snake for a tail that rises in an S and ends in a snake head.
Base: copied from opus/wolf/wolf.py; PARAMS (STAIL snake rings, HEAD_SCALE, GOAT, GOAT_HORN, SNAKE_HEAD, MANE_T).
- s1 r01 snake tail: twist (tail_ring up-flip) -> self-intersection + inside-out; r02 snake_ring without flip: PASS, ears cat-tall; r03 ears lower -> LOCK.
- s2 r01 IoU min 0.968. s3 r01 crash (ring index); r02 PASS 8 colours; r03 (in s4 r01) snake head larger.
- s4 r01 PASS; r02 final+orbit all PASS, glbcheck OK, 1928 tris.
Weakness: goat neck is a thin tube; snake head small and plain (no eyes).
