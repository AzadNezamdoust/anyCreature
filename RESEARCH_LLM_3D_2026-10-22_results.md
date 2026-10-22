# A/B results vs our best (2026-10-22)
Results are under `creatures/experiments/boxmodel/abc/t8/` (four tests) and `hard_surface/experiments/t8_cad_hybrid/`.
The judge was one Opus seat, comparing A/B in both orders. A flip in preference counts as no preference, and a tie goes to the baseline.

| Test | Verdict | Key evidence |
|---|---|---|
| game_pack (LOD, hurtboxes, collision, sockets, glTF/FBX round-trip) | **ADOPT** | Round-trip: baseline glb 0/3 full pass, game pack 9/9 exports. LOD IoU ≥0.93, but LOD3 at 10% reads blocky, so try 15%. Clip QA found hippo feet sinking 5% of body height in `move`. |
| joint_graph loops (3 per hinge / 5 per twist joint) | REJECT loops, **ADOPT the ROM sweep gate** | Judge tie in both orders. ROM: baseline 30/42 poses pass, candidate 32/42. Same failures on both: elbow collapse, crouch pinch, groin knife fold, thin wrists. Cause is the skin weights, not the loop count. |
| checklist + champion fix loop | **ADOPT (leaning)** | Checklist beat free-form in both orders. Checklist vs baseline: one tie, one win, so it ties. Self-graded checklist score 14/16 vs baseline 7/16. The face visor is still unfixed. |
| blueprint + silhouette fit (griffin) | REJECT | Mean IoU went from 0.793 to 0.790. The tail junction failed. The fitter's stand-in silhouette does not predict the real mesh. Keep the tools `sheet_masks.py` and `glb_iou.py`. |
| hard-surface CAD hybrid (build123d) | REJECT | Assault rifle came out the same to 3 decimals. 9/10 checklist on both. Judge preference flipped with order. CAD cost about 1.5 h of tool problems. Only worth it for threads or fillets. |

Next:
- Weight fixes at elbow, hip and crotch, gated by the ROM sweep.
- Clip ground-penetration fixes.
- LOD3 at 15%.
- Checklist loop added to WORKFLOW.
- Targeted face fix for gorilla and yeti.
