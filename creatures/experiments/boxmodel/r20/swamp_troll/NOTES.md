# swamp_troll (r20)
Design: hunched long-armed bog troll, green hide, long drooping nose over an underbite with tusks, dark weed clumps on the shoulders/hump, straw reed loincloth.
Base: copied from opus/giant/giant.py; PARAMS NOSE, PALETTE, WALK_STEP, LOIN_BLEND.
- s1 r00 baseline; r01 long nose: nose bottom crossed the jaw ledge; r02 nose tip raised -> PASS; r03 LOCK (1144 tris).
- s3 r01 palette + no rocks: PASS 2052 tris; hide too uniform with weeds -> lighter hide.
- s4 r01 drift (loincloth) - same FAIL reproduced on an unmodified giant copy (kit change since); r02 LOIN_BLEND 0.25 / r03 1.0: no effect; r04 drift debug: belt sides at the hip in move; r05 WALK_STEP 24->15: PASS; r06 final+orbit all PASS, glbcheck OK, 2052 tris.
Weakness: body is the giant's with a recolour; nose droop limited by the jaw ledge.
