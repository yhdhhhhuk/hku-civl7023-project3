# C stage-2 Windows reproduction record

Historical baseline: 430bbe22746fe3493b62877bf22e9fcd2406d7bc; 5 November integration package; branch c-stage2-20261107. At the original capture time the work had not been committed, pushed or messaged. Later publication is documented in CHANGELOG. Sparse checkout omitted old baseline videos; 347 imported files, 75 mesh references and B's source evidence verified.

Windows, Python 3.12 and PyBullet 3.2.7 were used, with the environment at E:/7023/.venv. Dependency checking passed. Exact versions and source differences are retained with the run. ASCII asset caching and output paths solved two Windows path failures without changing physics. Optional XY grasp-offset compensation subsequently changed transfer/lowering commands while preserving nominal component targets and collision thresholds.

| Check | Result |
|---|---:|
| Calibration | 6/6 |
| Single | single04_compensated, exit 0, 1/1 |
| Full | full02_compensated, exit 0, 16/16 |
| Start mode | From zero; no restore or concatenation |
| Simulated time | 607.183333 s |
| Wall time | 4110.67 s |
| Maximum final position / orientation error | 0.350763 mm / 0.586786 degrees |
| Motion segments | 96 |
| Quintic-grid direct / vertical sampled DLS | 64 / 32 |
| Recorded out-of-definition collisions | 0 |
| Continuous telemetry | 145724 rows at 240 Hz |
| Snapshots | 96, each with 15 obstacles |
| Inventory samples | 1214, each with 16 components |
| 3 N release escalations | 0 |
| Physical video | 3036 frames, 5 fps, 640x480 |

Loaded mass was 0.07260666666667 kg, COM [0,0,0.010566253098888994] m and centroidal inertia [7.554717961655561e-6,1.8706254628322218e-5,2.0403439999999998e-5] kg·m². See loaded_payload.json for actual imported values.

The historical B reference errors were 0.935791 mm and 0.155598 degrees. C differed by -0.585028 mm and +0.431188 degrees. C enabled compensation while the reference did not; this is not a platform-only repeatability comparison. Original C full01 stopped before lowering component 10 after completing nine components. Its evidence remains separate.

Evidence is in runs/C_stage2/full02_compensated and single04_compensated, with calibration and failures retained in the project validation area. Each manifest preserves exact command, start time and exit status. Raw trajectories, full-rate joint logs, release diagnostics, result, source manifest, loaded payload, physical checkpoints and video are retained. Statistics, figures and video checks derive from that run. Independent checks cover hashes, inventory, contacts, zero attachment displacement and release gating.

Candidate uniform material awaits adoption. Assisted grasping is not pure friction. Components remain dynamic after release. Collision evidence is discrete; last-substep equivalent torque does not cover every 960 Hz peak or manufacturer safety limit. Corner gaps and absent side connections prevent structural-reliability claims. This was C's stage-2 handoff for the 8 November meeting, not completion of formal stage-3 experiments or the whole course project. A integrates, B reviews and reproduces, and the members provide their own approval.
