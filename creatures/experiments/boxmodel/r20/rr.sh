#!/bin/sh
# usage: rr.sh <creature> <stage> <round> [extra]
cd /e/Github/anyCreature/creatures
export BLENDER='E:\gen3d\blender\blender-5.2.2-windows-x64\blender.exe'
c=$1; shift; s=$1; shift; r=$1; shift
python experiments/boxmodel/kit/run.py experiments/boxmodel/r20/$c/$c.py --stage $s --round $r "$@" 2>&1 | grep -E "FAIL|PASS|LOCK|Error|error|Traceback|line [0-9]|SUMMARY|warn" | head -40
