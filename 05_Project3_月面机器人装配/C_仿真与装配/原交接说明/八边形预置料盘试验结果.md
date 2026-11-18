# Preloaded-tray octagonal assembly: historical result

Run date: 2 November 2026. All 16 components were present before the first physics step; the loop did not create, delete or teleport replacement stock. The original sequential-feeding baseline was kept separately.

## Result and scene

All 16 components completed successfully, without a reported error, using exact-state checkpoint continuation and joined physical video segments. This was not one uninterrupted run. The creation audit records 16 components at step zero with matching IDs. Physical body count stayed 19; planning-client geometry copies are outside that physical count.

Tray rows have radii 200/265/330 mm and counts 5/5/6, with component long axes tangent to each arc. All 48 nominal grasp, approach and intermediate checks (14 mm, 82 mm and an additional 50 mm height) passed IK. Static endpoint checks conservatively included future ring geometry. Minimum initial stock separation was about 14.909 mm. These are preliminary checks, not complete motion validation.

The dark tray is a coplanar visual surface. A common horizontal plane supplies physical support; no unvalidated raised rim or pocket fixture was added. Physical ground height is zero; its visual background is lowered by 0.2 mm to avoid flicker. Slot IDs are overlay labels.

Each segment reads all 16 actual poses and checks the other 15 components. Transfers use joint-edge and actual quintic-command checks, with RRT-Connect when direct motion is blocked. Revised vertical motion uses 2 mm Cartesian IK sampling, 1 mrad joint edges and per-command checking. Conservative AABB rejection excludes only definitely separated pairs. Completing 96 segments does not mean RRT was needed for every segment.

The old release displaced component 9 by about 3 mm. Low-force, low-speed opening under assistance, followed by 0.25 s clear stable contact before detachment, reduced that same-component placement error to 0.178 mm. Targets were not moved to conceal error.

## Measured evidence

Simulated duration: 596.783 s. Four segments actually used RRT. Recorded out-of-definition collisions: zero. Internal checks use 3 mm position, 0.05 rad orientation, 5 mm/s speed and support contact; these are not official marking thresholds. Dense checks and rendering may take much longer than physical time.

| Component | Final position error (mm) | Orientation error (degrees) | Final speed (m/s) |
|---|---:|---:|---:|
| 1 | 0.055 | 0.070 | 6.97e-08 |
| 2 | 0.063 | 0.256 | 9.44e-08 |
| 3 | 0.151 | 0.021 | 1.88e-07 |
| 4 | 0.242 | 0.038 | 7.85e-09 |
| 5 | 0.055 | 0.007 | 7.88e-08 |
| 6 | 0.207 | 0.007 | 5.65e-09 |
| 7 | 0.073 | 0.116 | 4.6e-11 |
| 8 | 0.094 | 0.080 | 5.25e-09 |
| 9 | 0.271 | 0.018 | 6.92e-08 |
| 10 | 0.339 | 0.248 | 3.96e-07 |
| 11 | 0.139 | 0.141 | 1.63e-07 |
| 12 | 0.257 | 0.006 | 2.34e-07 |
| 13 | 0.231 | 0.038 | 2.42e-07 |
| 14 | 0.156 | 0.020 | 6.58e-08 |
| 15 | 0.296 | 0.048 | 1.24e-07 |
| 16 | 0.163 | 0.075 | 3.27e-07 |


Initial inventory and first frame record all 16 components. Creation audit records client and step. Inventory logs sample COM-frame poses at 2 Hz in metres and XYZW quaternion order. Trajectory logs contain the current component/TCP and scene count. Control logs retain executed motion. Original assembly.mp4 segments are combined into assembly_complete.mp4; source ranges and checkpoint SHA values are in video_lineage.json. The 4x viewing copy is separate. Source snapshots, scenes and physical checkpoints remain archived.

## Limitations and reproduction

The two-layer segmented enclosure retains the original interfaces but has corner gaps and no side connections. It is not a sealed or load-bearing building validation. Historical 70 g mass, COM and inertia were temporary. Contact-gated assistance does not establish friction-only grasping. Lunar joint torque evaluation and material/structure adoption were subsequent work.

Historical commands: run simulation/run_preloaded_tray_assembly_fast.py with --video and a new output directory, then simulation/summarize_preloaded_tray.py and simulation/document_preloaded_tray.py on that directory. The original launcher is retained in the historical package.

## Viewing changes

Slot labels S01–S16 were hidden at the user's request without changing stock positions or physics. The original labelled evidence video remains. assembly_no_slot_labels_4x.mp4 used fixed-region label removal documented in slot_label_removal.json; later runs omit labels directly.

The alternate oblique view is 149.2 s at 4x, with yaw 53 degrees, pitch 40 degrees and distance 1.25 m. It is reconstructed from verified logs using linear position/joint interpolation, quaternion SLERP and symmetric finger reconstruction. It is not a new physical acceptance run. side_camera_replay.json records method and source SHA; original evidence is unchanged.
