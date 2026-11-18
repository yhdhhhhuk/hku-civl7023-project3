# C-to-B grasp and placement handoff, 2 November 2026

This historical handoff addresses B's 15-item checklist with code, models, targets, raw logs and video for the two-layer, 16-component octagon. Paths below describe the original unpacked package, not a newly executed run.

## Verified scope and lineage

The checkpoint chain completed 16/16 in 596.783 simulated seconds, with maximum final position error 0.3387 mm and orientation error 0.2564 degrees, and no recorded out-of-definition collision. Mass properties were temporary and grasping used a bilateral-contact-gated assist constraint.

This was a chain of exact physics checkpoint continuations: the original first eight components, a release-fixed ninth component, and the final seven using the fast runner. It is not proof that the final unified program completed a fresh uninterrupted run. Runtime source snapshots and video_lineage.json record the individual segments. The unified entry includes the later release/vertical-path fixes and camera setting.

## Environment and source (checklist 1–3)

The original environment was Python 3.12.10 with requirements.txt. Unpack to an ASCII directory, create a virtual environment and install requirements. Run `simulation/run_preloaded_tray_assembly_fast.py --gui --output outputs/b_review_run`, adding `--video` for recording. Run `simulation/summarize_preloaded_tray.py outputs/b_review_run` afterwards. Dense full-scene checking may take substantially longer than simulated time.

The handoff excludes virtual environments and caches. The first run creates its mesh cache. The historical package uses project-relative paths and a Windows path helper. This packaging pass checked files and hashes only; it did not rerun physics or validate a newly installed environment.

B's original robot, controller, workspace and model files remain in the 30 October handoff tree. The P3-GrooveKey-v2 component is 50×30×25 mm, with 22 mm main-body height and layer spacing, and 34 convex pieces. C combines the collision shapes into a single rigid body to realise a 50 μm margin; the earlier fixed-multilink representation was unreliable. C extends collision guards, trajectories, four physics steps per control step, gripper force and release logic without directly rewriting B's original controller.

## Coordinates and settings (checklist 4–8)

- The initial/target pose CSV lists nominal source and target bottom-origin poses, sequence and layer in world coordinates: metres, radians with degree columns, and XYZW quaternions. Actual settled stock poses are in the logs.
- The fixed robot root is at (0,0,0) with quaternion (0,0,0,1). B's nominal TCP is gripper_base-local (0,0,0.1358) m, not a calibrated TCP.
- Nominal grasp TCP is 14 mm above the component bottom origin, with world rotation Rz(component yaw)·diag(-1,1,-1). Lower-layer release TCP is 16 mm above the bottom target; upper-layer release is 14.5 mm above its bottom target. Release allowance does not redefine the grasp point.
- The assist transform is computed from the actual contact pose; no forced alignment or attachment teleport is applied. Temporary COM is (0,0,0.011) m. trajectory.csv uses the bottom origin, while inventory_trace.csv uses body COM. Rotate and subtract the COM offset when converting.
- Opening/closing targets are 36/22 mm. Historical closing uses 5 N per finger and 0.02 m/s. The corrected release opens at 1 N and 0.01 m/s while assisted, then detaches after opening exceeds 35.5 mm, finger force clears and stability persists for 0.25 s. The first eight components used the old release logic; components 9–16 used the corrected logic.
- Both finger core faces must show positive contact before a fixed assist connects robot link 7 to the component base, with a 30 N maxForce setting. Finger contact links are 8/9. Released and previously placed components remain dynamic.
- Gravity is (0,0,-1.62) m/s²; physics 240 Hz, control 60 Hz, solver iterations 100. Ground/component friction is 0.6 and component restitution is zero. The tray is a coplanar visual surface over the common support plane.
- Historical mass is 0.07 kg. COM and inertia are temporary bounding-box values for 50×30×25 mm, using Ixx=m(y²+z²)/12 and analogous formulas, not an approved material or CAD-volume distribution.

## Data, motion and collision evidence (checklist 9–13)

| File | Content and sampling |
|---|---|
| b_control_trace.csv | Approximately 60 Hz during motion; commanded/actual joints, velocity and TCP pose. Waiting intervals are not continuously sampled. |
| trajectory.csv | 20 Hz current component, phase, bottom pose, TCP, measured opening, attachment and finger contacts. |
| inventory_trace.csv | 2 Hz poses of all 16 COM frames and stock/carried/placed states. |
| result.json | Events, planning records, final errors/speeds/support contacts, exemptions and collision records. |
| final_errors.csv, metrics.json | Final placement and control metrics. |
| preloaded_checks.json | Preloading, constant 19-body scene and segment snapshots. |
| assembly_complete.mp4 | Original physical checkpoint segments joined in their verified order; see video_lineage.json. |
| assembly_complete_4x.mp4 | Four-times-speed copy of that physical sequence. |
| assembly_side_view_4x.mp4 | Log-interpolated alternate camera view, not a new physical validation. |

An additional robot log preserves original columns and appends an explicitly inferred component ID matched backward in time against object logs. Gripper opening commands were not separately measured as a time series; policy settings are not measurements. Measured opening is in trajectory.csv.

The planning record contains component, target pose, start/end joints, path, method and duration. Ordinary segments use quintic joint trajectories and feedback, with RRT-Connect when needed. Revised vertical segments use 2 mm Cartesian IK sampling, 1 mrad edge checks, per-command guards and DLS feedback. Ordinary planning scales are 0.35 rad/s and 0.6 rad/s²; old descent scales are 0.2/0.4. These are planning settings, not guarantees for every measured derivative.

Each physics step monitors defined contact violations and each control command is guarded. All other 15 components remain obstacles. Robot self-collision, ground, gripper/payload and stock/placed interactions are checked subject to explicit exemptions. Carried-payload planning requires nonpenetration; the execution tolerance is 0.2 mm. An empty collisions array means no monitored violation, not absence of every possible contact category.

After release, wait 1 s, retreat and settle another second; after all components, settle 3 s. Maximum final speed was 3.96e-7 m/s and every component had lower support. No slip or overturn occurred in this assisted sequence, which is not proof of friction-only grasp or structural reliability. Inventory quaternions are sampled before/after the final evaluation time; the final table reports orientation error without inventing exact terminal quaternion data.

## Torque interface and remaining work (checklist 14–15)

Actual motor torques and constraint reaction torques were not recorded in this historical run and cannot be reconstructed as measurements. URDF effort, 5/1 N finger settings and the 30 N assist limit are settings, not actual torque.

B can record getJointState(...)[3] for each revolute arm joint after every physics step in observe(), in N·m. For reaction wrench [2], enable the corresponding joint sensor and document coordinates. Assist getConstraintState must be logged separately. This requires new acquisition; missing historical measurements cannot be recovered.

The planned follow-up was torque logging, independent opening command/measurement columns, full waiting-phase joint records and exact final quaternion/release velocity windows. Material confirmation remained A's responsibility. These were future actions at the handoff date.

Retained failures include approximately 3 mm ninth-component displacement with the old release, subsequent RRT exhaustion at component 15, and a separate resume-index diagnostic. Later low-force release and vertical-path fixes enabled the checkpoint chain. Corner gaps, missing lateral connections, temporary inertia, assistance, exemptions, checkpoint continuation and interpolated viewing copies are disclosed.

Suggested review order: target and parameter tables, original logs, physical videos and source snapshots, environment setup and current entry point, then extended torque/gripper acquisition. The handoff SHA manifest and the original engineering manifest remain distinct.
