# C runtime and reproduction guide

Use the current group main. Stage 2 was merged through PR #1. Statements that the work was unpublished describe the historical capture date only; CHANGELOG records subsequent publication. Do not re-import the old integration ZIP over current code.

Use Python 3.12 and install the project requirements in a local environment. Do not copy a virtual environment between machines. On Windows, use an ASCII parent and output directory. Every run needs a new output directory; archived runs must not be overwritten.

The repository entry points explicitly select A-candidate, telemetry and video. Stage 2 requires the compensation flag; the stage-3 entry enables compensation by default. The legacy main runner and old demonstration launcher may default to legacy70g and must not be mistaken for the selected candidate experiment. The stage-4 English launcher defaults to headless execution.

Order: verify package, calibrate all six cases, run one component, analyse and audit, then run all 16 only when required. Exact commands are in each execution manifest. Restore compressed evidence using `python restore_evidence.py --prefix runs/C_stage3/` from the repository root.

Windows path fixes: short-path lookup may still return non-ASCII text. The existing ASCII asset cache copies URDF and referenced meshes without changing bytes or relative references. Bullet checkpoints also require ASCII output paths. These fixes do not change mass, inertia, planning, control, contact thresholds or release conditions; the original failures remain.

The original full01 stopped before component 10 after nine placements. Optional `--compensate-grasp-offset` adjusts transfer/lowering TCP XY using exact simulated state after lift, with a 2 mm rejection limit. Nominal targets and physics remain unchanged. The compensated stage-2 run completed 16/16 with maximum errors 0.3508 mm and 0.5868 degrees and 145724 continuous rows. This change is not a platform-only comparison.

The mass is 72.6066667 g under a uniform 2500 kg/m³ candidate assumption. Bilateral contact gates an assisted constraint; released components remain dynamic. Torque is sampled at 240 Hz and interpreted only after local substep calibration. Corner gaps, absent side connections and discrete collision checks limit conclusions about strength and continuous collision avoidance.
