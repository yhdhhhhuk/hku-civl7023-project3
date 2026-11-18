# C: Simulation, Motion Planning and Continuous Assembly

English edition, 19 November 2026. The stage-3 baseline is 9806992. B's paired experiments and C's Windows reproduction are reported separately. This document does not record approval on behalf of another team member.

## Scene and assembly sequence

A fixed-base six-axis PiPER arm and parallel gripper operate under lunar gravity of 1.62 m/s². The external step is 1/240 s with four internal substeps. All 16 V2 components exist before the first physics step. The scene contains 19 bodies. Stock and assembled components remain dynamic rigid bodies, supported by the common ground plane. The tray is a coplanar visual surface, not a raised fixture.

The target is a two-layer octagonal enclosure centred at (260, 30) mm, with a 76 mm centreline radius and 22 mm layer spacing. Each layer follows sector order 0, 1, 7, 2, 6, 3, 5, 4. The original interfaces are retained, but corner gaps remain and no lateral connection is modelled.

Each component uses 34 convex collision subshapes with a 50 μm margin. The A-candidate mass is 0.07260666666666667 kg, with centre of mass 0.010566253098888994 m above the bottom origin. The centroidal inertia diagonal is [7.554717961655561e-6, 1.8706254628322218e-5, 2.0403439999999998e-5] kg·m². These values assume a uniform candidate density and are not measured material properties. An unchanged robot URDF does not establish that Bullet's imported inertia is a manufacturer-calibrated tensor.

## Planning, trajectories and collision checks

Each cycle comprises approach, descent, closing, lift, transfer, lowering, release, retreat and settling. Before each motion segment, all component poses are recorded and the other 15 components are included as obstacles. Collision guards cover the robot, gripper, ground, carried component and remaining stock and assembled components. AABB rejection is only a conservative broad phase; potentially interacting pairs receive detailed checks.

Nonvertical segments first attempt a joint-space direct connection, checked at 5 mrad edge resolution. The actual quintic command grid is checked before execution. The transition is h(u)=10u³−15u⁴+6u⁵, with timing derived from displacement, velocity and acceleration settings. RRT-Connect is available when a direct route is blocked. Both B formal runs actually used 64 checked direct segments and 32 checked vertical segments, with no RRT attempt or execution.

Descent and lowering use 2 mm Cartesian sampling, continuous IK seeds and 1 mrad joint-edge checking, followed by damped least-squares feedback and an online guard before each command. The 96 segments must therefore not all be described as quintic-grid preflight checks.

Planning requires nonpenetration of the carried payload. Execution tolerances distinguish approximately 0.1 mm robot penetration, 0.2 mm component/ground penetration and 0.5 mm designated finger-core contact. Ground/base and permitted grasp contacts have explicit exemptions. Zero out-of-definition collisions is a statement about these objects, stages, exemptions and sampled checks. It is not a continuous-time collision-free proof or evidence of an unmeasured minimum-clearance margin.

## Assisted grasping, release and compensation

Closing uses a 1 N per-finger command and a 0.02 m/s speed cap. A fixed assist constraint is created only after both fingers establish positive contact on the permitted core faces. Displacement at constraint creation is recorded. This stabilises the demonstration but does not validate purely frictional grasping.

During release, assistance is retained while the fingers open at 1 N and 0.01 m/s. The prescribed fallback permits 3 N, with up to 3 s per force stage. Detachment requires opening above 35.5 mm, no effective finger contact, linear speed below 2 mm/s and angular speed below 0.02 rad/s for five consecutive 50 ms samples. The component then settles dynamically. The relative contact-breaking factor is 1e-5; it is not a penetration distance in metres. Actual force escalation must be read from the run evidence.

After lifting, exact simulated TCP and component-bottom poses give d_T=R_WTᵀ(p_WO−p_WT). The desired TCP XY position is p_target,XY−(R_WT* d_T)_XY. The existing Z release height remains unchanged. The 2 mm XY limit triggers an error; it is not a fixed correction. Nominal component targets, physics and collision thresholds are unchanged. Orientation, sensor noise and delay are not compensated. This method uses ideal simulated state, not a validated vision system.

## Formal comparison and historical failures

B ran compensation off and on from zero on the same macOS ARM64 system. Both runs completed 16/16 components, 96 motion targets and 16 releases, with zero recorded out-of-definition collisions. Maximum final position error changed from 0.935791 to 0.261732 mm; maximum orientation error changed from 0.155598° to 0.186519°. Position improved while orientation and some torque measures incurred a cost. B's full-run J6 equivalent RMS increased by 2.271%. The result does not show universal improvement.

C's earlier Windows full01 stopped before lowering component 10 because the command prediction found approximately 0.158 mm penetration against component 9. Nine components had been completed; the rejected lowering was not executed. The subsequent compensated run completed 16. This history must not be substituted for the successful off condition in B's formal paired comparison. The two historical geometry-scan cases differed in height by 21.609 mm, so their clearance difference does not prove a pure XY effect at equal height.

Windows also exposed non-ASCII URDF and Bullet-checkpoint path failures. The existing fixes use an ASCII asset cache and ASCII output directories, preserving model bytes and relative mesh references. These path changes do not change physics or collision thresholds. Failed runs remain available.

## Recording and verification

The entry point explicitly selects A-candidate, telemetry and compensation. Each new run starts in a separate directory. Six local feedback calibration cases precede interpretation of four-substep motor feedback. Source hashes, commands, dependencies, actual loaded payload, continuous 240 Hz logs, results and physical video are retained.

Independent checks cover continuous step numbering, a constant 19-body scene, all 16 components at each inventory sample, 15 obstacles per segment, bilateral attachment with zero instantaneous displacement, release gating, planning records, unchanged runtime source hashes and final placements. Internal acceptance uses position below 3 mm, orientation below 0.05 rad, speed below 5 mm/s and lower support contact. These are engineering checks, not official course marking thresholds.

Motor feedback multiplied by four is the calibrated last-internal-substep equivalent at the 240 Hz sampled external steps. It is neither the maximum of every 960 Hz internal step nor an average over four substeps. Joint reaction and assist-constraint wrenches must not be treated as motor torque or added to it indiscriminately.

The 640×480, 5 fps video is rendered directly from physics, including an initial frame at step 24 and subsequent frames every 48 external steps. The oblique view uses 53° yaw, 40° pitch and 1.25 m distance, without slot labels. Accelerated copies have separate source hashes and speed records. Checkpoint concatenation or log-interpolated views are not described as uninterrupted physical runs.

## C stage-3 Windows reproduction

On 15 November, the compensated run completed 16/16 from zero without restart: 607.183333 s, 145724 continuous telemetry rows, maximum final position error 0.350763 mm and orientation error 0.586786°. All 96 segments completed: 64 direct and 32 vertical. All 1214 inventory samples contained 16 components; every scene snapshot included 15 obstacles. No out-of-definition collision or 3 N release escalation was recorded. All 12 independent checks passed; the physical video contained 3036 frames. All 69 resources matched B's frozen hashes.

Cross-platform configuration coordinates are compared with a 1e-12 absolute tolerance for floating-point evaluation; a single-component run compares only its requested target subset. This audit tolerance does not alter the simulation thresholds. B's paired results remain the formal comparison, while C's values provide a separate Windows reproduction.

## Scope and handoff

The conclusions remain conditional on uniform candidate material, rigid bodies, assisted grasping, ideal simulated pose and discrete collision checks. Strength, overturning resistance, sealing, lateral connections and real-hardware reliability were not verified. Material adoption, final group approval and live rehearsals require the responsible members. See the run manifests, independent audits and B's formal technical module for traceable evidence.
