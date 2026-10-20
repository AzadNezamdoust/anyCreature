# animal tile x0 y0 x1 y1
a=$1; shift
../venv/Scripts/python.exe closeup.py $a/textured.glb $a/closeup.png "$@" 2>&1 | tail -2
../venv/Scripts/python.exe closeup.py ../tex12/$a/textured.glb $a/closeup_r12.png "$@" 2>&1 | tail -2
