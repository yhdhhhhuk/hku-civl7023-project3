# C stage-3 Windows reproduction

15 November 2026; baseline 9806992; A-candidate, telemetry and compensation enabled. All 16 components completed from zero without interruption.

| Metric | Result |
|---|---:|
| Simulated time | 607.183333 s |
| Maximum final position error | 0.350763 mm |
| Maximum final orientation error | 0.586786 degrees |
| Continuous 240 Hz rows | 145724 |
| Inventory sampling times | 1214 |
| Checked direct / vertical segments | 64 / 32 |
| Out-of-definition collisions | 0 |
| Release escalations to 3 N | 0 |

All independent checks passed. All 69 resources matched B's frozen hashes and the runtime source hashes matched the local files. Configuration coordinates use a 1e-12 absolute comparison tolerance; single runs compare the requested target subset. This does not change physics or collision thresholds.

Original and 4x video provenance is in runs/C_stage3/full01/video_lineage.json. The original video contains 3036 frames. Full analysis and independent torque recomputation are retained. B's formal compensated result is 0.261732 mm and 0.186519 degrees; this Windows result is reported separately and does not establish a statistical success rate or bitwise cross-platform reproducibility.

The exact commands, environment, calibration and run manifests are retained in runs/C_stage3. Initial package checks failed because sparse checkout omitted directories; after completing checkout, 161 files and 10 lossless logs verified. The audit implementation was corrected for UTF-8 BOM and single-target subsets without changing the simulation source. Candidate material, assisted grasping and ideal simulated pose assumptions remain in force.
