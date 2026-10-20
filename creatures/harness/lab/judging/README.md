# Blind-judging evidence

key_rN.json: shuffle key (sheet id -> method, animal) per round.
rN/o_answers.txt, rN/f_answers.txt: Opus / Fable judge answers (id: animal | quality | defect).
Score with: python harness/lab/blind.py --score harness/lab/judging/key_rN.json harness/lab/judging/rN/o_answers.txt
Render sheets and meshes are not in git (size).
