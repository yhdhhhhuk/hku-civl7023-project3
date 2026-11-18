# Part B Stage 4 Finalized English Report Module (Ready for Master Report Integration)

> **Integration Note for Part A (中文整合说明)**:
> 本文件提供 B 负责部分（机械臂运动学、缩放雅可比、阻尼最小二乘闭环控制、抓取偏置补偿、同机双工况位姿精度分解、轨迹可行性与月面重力下六轴力矩评价）的**定稿英文学术段落、完整 URDF 参数表、核心数学公式 (1)–(8)、结果统计表与标准 APA 第7版参考文献**。
> 已严格对齐 `2026 CIVL 7023_Course Overview.pdf` 第6页五章结构（`2. Literature Review`、`3. Research Methodology`、`4. Results and Discussion`、`5. Conclusions`、`References`），删除了所有“详见仓库外部文件”的内部交接用语，可直接按章节并入最终英文 Word 报告（`Times New Roman, 12 pt, 2.5 cm margins, Single spacing`）。所有嵌入图表原始坐标轴均为英文，可直接复用无需重绘。

---

## Section 2.2 (Insert into `2. Literature Review`) — Robotic Kinematics, Singularity-Robust Control, and Assembly Error Compensation

Robotic assembly of dry-stacked or interlocking masonry and modular construction units requires translating discrete structural target poses into smooth, collision-free joint motions under actuator and workspace limits (Bock & Linner, 2017; Giftthaler et al., 2017). For six-degree-of-freedom (6-DoF) serial manipulators, forward kinematics and the spatial or geometric Jacobian relate joint configurations and rates directly to end-effector linear and angular twists (Lynch & Park, 2017; Siciliano et al., 2009). Near wrist or elbow kinematic singularities, exact Jacobian inversion produces unbounded joint velocities. Nakamura and Hanafusa (1986) and Wampler (1986) independently established Damped Least Squares (DLS, or Levenberg–Marquardt) inverse kinematics, trading a bounded tracking regularization against joint-rate norm near ill-conditioned configurations. Furthermore, because translational and rotational task coordinates have heterogeneous physical units, task-space characteristic-length scaling is essential before singular-value conditioning analysis or DLS inversion (Siciliano et al., 2009).

In tight-clearance dry-joint assembly—such as tongue-and-groove or boss-and-socket sintered lunar regolith blocks—nominal open-loop pick-and-place trajectories remain vulnerable to sub-millimeter grasping offsets introduced during finger closure and contact settling. Terrestrial robotic bricklaying and on-site fabrication motivate feedback for placement and alignment (Dörfler et al., 2016; Giftthaler et al., 2017). Here we evaluate a post-lift correction under simulated lunar gravity using the known pose of the held block. In physics-based multi-body simulation, evaluating both kinematic tracking residuals and actuator torque demands under reduced lunar gravity ($1.62\text{ m/s}^2$) requires careful calibration of simulator motor-impulse feedback across internal solver substeps rather than relying solely on ideal kinematic playback (Coumans & Bai, 2016).

---

## Section 3.2 (Insert into `3. Research Methodology`) — PiPER Manipulator Kinematics, Scaled Jacobian, and Closed-Loop Control

### 3.2.1 Coordinate Frames and URDF Kinematic Chain

Six right-handed Cartesian frames are defined across the assembly system: the world frame $\{W\}$ ($+Z$ vertically upward, SI units $\text{m, rad, s}$), the fixed manipulator base frame $\{B\}$ (`base_link`, coincident with $\{W\}$), the gripper base frame $\{G\}$ (`gripper_base`, rigidly attached to `link6`), the declared nominal tool center point (TCP) frame $\{T\}$, the block geometric bottom-center frame $\{O\}$ (local $+X$ along the $50\text{ mm}$ length, $+Y$ along the $30\text{ mm}$ width, $+Z$ upward), and the block center-of-mass (COM) inertial frame $\{C\}$. Rather than substituting textbook Denavit–Hartenberg approximations, forward transforms are parsed directly from the supplied PiPER URDF tree (`piper_description_pybullet.urdf`), summarized in **Table B1**.

**Table B1. Supplied PiPER 6-DoF Manipulator and Parallel Gripper URDF Kinematic Specification**

| Joint Name | Type | Parent $\rightarrow$ Child | Origin $xyz$ (m) | Origin $rpy$ (rad) | Local Axis | Position Limits | URDF Effort / Speed Param. |
|---|---|---|---|---|---|---|---|
| `base_to_dummy` | Fixed | `dummy_link` $\rightarrow$ `base_link` | $[0,\ 0,\ 0]$ | $[0,\ 0,\ 0]$ | — | Fixed | — |
| `joint1` | Revolute | `base_link` $\rightarrow$ `link1` | $[0,\ 0,\ 0.123]$ | $[0,\ 0,\ 0]$ | $[0,0,1]$ | $[-150.00^\circ,\ +150.00^\circ]$ | $100$ / $5.0\text{ rad/s}$ |
| `joint2` | Revolute | `link1` $\rightarrow$ `link2` | $[0,\ 0,\ 0]$ | $[1.5708,\ -0.1359,\ -3.1416]$ | $[0,0,1]$ | $[0.00^\circ,\ +179.91^\circ]$ | $100$ / $5.0\text{ rad/s}$ |
| `joint3` | Revolute | `link2` $\rightarrow$ `link3` | $[0.28503,\ 0,\ 0]$ | $[0,\ 0,\ -1.7939]$ | $[0,0,1]$ | $[-170.00^\circ,\ 0.00^\circ]$ | $100$ / $5.0\text{ rad/s}$ |
| `joint4` | Revolute | `link3` $\rightarrow$ `link4` | $[-0.021984,\ -0.25075,\ 0]$ | $[1.5708,\ 0,\ 0]$ | $[0,0,1]$ | $[-99.98^\circ,\ +99.98^\circ]$ | $100$ / $5.0\text{ rad/s}$ |
| `joint5` | Revolute | `link4` $\rightarrow$ `link5` | $[0,\ 0,\ 0]$ | $[-1.5708,\ 0,\ 0]$ | $[0,0,1]$ | $[-69.90^\circ,\ +69.90^\circ]$ | $100$ / $5.0\text{ rad/s}$ |
| `joint6` | Revolute | `link5` $\rightarrow$ `link6` | $[8.8259\times 10^{-5},\ -0.091,\ 0]$ | $[1.5708,\ 0,\ 0]$ | $[0,0,1]$ | $[-120.00^\circ,\ +120.00^\circ]$ | $100$ / $3.0\text{ rad/s}$ |
| `joint6_to_gripper_base` | Fixed | `link6` $\rightarrow$ `gripper_base` | $[0,\ 0,\ 0]$ | $[0,\ 0,\ 0]$ | — | Fixed | — |
| `joint7` | Prismatic | `gripper_base` $\rightarrow$ `link7` | $[0,\ 0,\ 0.1358]$ | $[1.5708,\ 0,\ 0]$ | $[0,0,1]$ | $[0.000,\ +0.035]\text{ m}$ | $10$ / $1.0\text{ m/s}$ |
| `joint8` | Prismatic | `gripper_base` $\rightarrow$ `link8` | $[0,\ 0,\ 0.1358]$ | $[1.5708,\ 0,\ -3.1416]$ | $[0,0,-1]$ | $[-0.035,\ 0.000]\text{ m}$ | $10$ / $1.0\text{ m/s}$ |

The nominal TCP is declared at $r_{GT} = [0, 0, 0.1358]^T\text{ m}$ in $\{G\}$ (the midpoint of the two prismatic finger origins), while symmetric jaw opening $w \in [0, 0.070]\text{ m}$ is commanded via $q_7 = +w/2$ and $q_8 = -w/2$. Because symmetric finger translation does not alter $r_{GT}$, the 6-DoF arm task kinematics decouple cleanly from jaw opening. For joint configuration $q \in \mathbb{R}^6$, the forward TCP pose is:

$$
T_{WT}(q) = T_{WB} \left( \prod_{k=1}^{m} F_k M_k(q) \right) \mathrm{Trans}(r_{GT}) \tag{1}
$$

where $F_k$ denotes each URDF origin homogeneous transform ($\mathrm{Trans}(x,y,z) R_z(\psi) R_y(\theta) R_x(\phi)$) and $M_k(q)$ is the local joint rotation for revolute joints (or $I_4$ for fixed joints). During simulation, the live URDF link pose is reconstructed from PyBullet's double-precision inertial COM state via $T_{WG} = T_{WC,G} T_{GC,G}^{-1}$ before applying $r_{GT}$. Analogously, because PyBullet reports each dynamic block's inertial COM position $p_C$ and orientation $R_{WO}$, the block's geometric bottom-center origin is recovered as:

$$
p_O = p_C - R_{WO} r_{OC}, \qquad r_{OC} = [0,\ 0,\ 0.0105663]^T\text{ m} \tag{2}
$$

### 3.2.2 Geometric Jacobian, Task Scaling, and Projected DLS Inverse Kinematics

Let $a_i(q) \in \mathbb{R}^3$ and $o_i(q) \in \mathbb{R}^3$ denote the unit rotation axis and axis origin of revolute joint $i$ ($i=1,\dots,6$) expressed in $\{W\}$, and let $p_T(q)$ be the world TCP position. Stacking linear velocity above angular velocity yields the $6 \times 6$ world-frame geometric Jacobian:

$$
J_i(q) = \begin{bmatrix} a_i(q) \times \bigl(p_T(q) - o_i(q)\bigr) \\ a_i(q) \end{bmatrix}, \qquad \begin{bmatrix} v_T \\ \omega_T \end{bmatrix} = J(q)\dot{q} \tag{3}
$$

Given a desired TCP pose $(p_d, R_d)$ and measured TCP pose $(p_T, R_T)$, the 6D task residual uses the exact $SO(3)$ matrix logarithm (shortest axis-angle vector, singularity-safe at $\theta \to 0$ and $\theta \to \pi$):

$$
e_p = p_d - p_T, \qquad e_R = \bigl(\mathrm{Log}(R_d R_T^T)\bigr)^\vee, \qquad e = \begin{bmatrix} e_p \\ e_R \end{bmatrix} \tag{4}
$$

To homogenize translational ($\text{m}$) and rotational ($\text{rad}$) dimensions on the workspace scale of PiPER, a task-space scaling matrix $W_s = \mathrm{diag}(L^{-1}I_3, I_3)$ with characteristic length $L = 0.3\text{ m}$ is introduced, defining $\bar{J}(q) = W_s J(q)$ and $\bar{e} = W_s e$. Kinematic conditioning is monitored throughout execution via the minimum singular value $\sigma_{\min}(\bar{J})$ and condition number $\kappa(\bar{J}) = \sigma_{\max}(\bar{J})/\sigma_{\min}(\bar{J})$.

Inverse kinematics (IK) solves for feasible target configurations using multi-seed projected DLS iterations with damping $\lambda_{\text{IK}} = 0.015$, per-step infinity-norm clamping $\|\delta q\|_\infty \le 0.15\text{ rad}$, backtracking line search $\alpha \in \{1.0, 0.5, 0.25, 0.1\}$, and box projection onto a $2^\circ$-inward safety margin $[q_{\min}+2^\circ, q_{\max}-2^\circ]$:

$$
\delta q = \bar{J}^T \bigl(\bar{J}\bar{J}^T + \lambda^2 I_6\bigr)^{-1} \bar{b} \tag{5}
$$

where $\bar{b} = W_s e$ in IK iterations. A candidate solution is accepted if and only if independent forward-kinematics verification satisfies $\|e_p\|_2 < 10^{-5}\text{ m}$ ($10\ \mu\text{m}$) and $\|e_R\|_2 < 10^{-4}\text{ rad}$ within the limit of 250 iterations per seed, with up to four posture seeds.

### 3.2.3 Quintic Joint Transitions, 60 Hz DLS Outer-Loop Control, and Post-Lift XY Compensation

Physics simulation advances at $\Delta t_p = 1/240\text{ s}$ with $n_s = 4$ internal solver substeps ($\Delta t_{\text{sub}} = 1/960\text{ s}$, 100 solver iterations) under lunar gravity $g = [0, 0, -1.62]^T\text{ m/s}^2$. Non-vertical segments (`approach`, `lift`, `transfer`, `retreat`) execute collision-checked joint-space paths time-parameterized by a zero-endpoint-velocity/acceleration quintic polynomial over duration $T = \max\bigl(1.0\text{ s},\ 1.875\|\Delta q\|_\infty / 0.35,\ \sqrt{5.8\|\Delta q\|_\infty / 0.6}\bigr)$:

$$
q_{\text{cmd}}(t) = q_a + \bigl(10s^3 - 15s^4 + 6s^5\bigr)(q_b - q_a), \qquad s = t / T \in [0, 1] \tag{6}
$$

Vertical approach/insertion segments (`descend` to $z_T = 14\text{ mm}$; `lower` to $z_{\text{target}} + 16.0\text{ mm}$ on Layer 1 and $z_{\text{target}} + 14.5\text{ mm}$ on Layer 2) pre-validate $2\text{ mm}$-spaced Cartesian IK waypoints at $1\text{ mrad}$ joint-edge resolution, then track the terminal pose under online collision guarding.

Terminal convergence on every motion segment is governed by a $60\text{ Hz}$ ($\Delta t_c = 4\Delta t_p = 1/60\text{ s}$) Cartesian DLS outer loop driving PyBullet `POSITION_CONTROL` joint servos ($K_p = 0.15$, $K_v = 1.0$, configured `force = 100`, `maxVelocity` $= \min(0.6\text{ rad/s}, \dot{q}_{\text{URDF}})$). Using proportional task velocity $v_c = [3e_p^T, 3e_R^T]^T$ saturated at $\|v_c\| \le 0.04\text{ m/s}$ and $\|\omega_c\| \le 0.3\text{ rad/s}$, Eq. (5) with $\lambda_c = 0.02$ and uniform joint-rate scaling $\|\dot{q}_c\|_\infty \le 0.35\text{ rad/s}$ updates an integrated joint position reference $q_{\text{ref},k+1} = \mathrm{clip}\bigl(q_{\text{ref},k} + \Delta t_c \dot{q}_{c,k},\ q_k \pm 0.03\text{ rad}\bigr)$. Retaining $q_{\text{ref}}$ across cycles provides the steady servo position offset needed to counter lunar gravity without steady-state droop. Convergence requires 15 consecutive $60\text{ Hz}$ samples ($0.25\text{ s}$) simultaneously satisfying $\|e_p\|_2 < 0.1\text{ mm}$, $\|e_R\|_2 < 0.1^\circ$, and $\|\dot{q}\|_\infty < 0.02\text{ rad/s}$.

To evaluate alignment sensitivity across the $0.4934\text{ mm}$ nominal octagon corner gap without modifying nominal block targets or contact thresholds, an optional post-lift XY grasp-offset compensation is formulated after each block reaches `lift` ($z_T = 82\text{ mm}$). Expressing the held block's geometric origin offset in the measured TCP frame and projecting it to the target tool orientation $R_{WT,d}(\psi) = R_z(\psi)\mathrm{diag}(-1, 1, -1)$ gives:

$$
r_{TO} = R_{WT}^T(p_O - p_T), \qquad \delta p_{xy} = -\bigl[R_{WT,d}(\psi)\, r_{TO}\bigr]_{xy}, \qquad p_{T,\text{cmd},xy} = p_{O,\text{target},xy} + \delta p_{xy} \tag{7}
$$

Only `transfer` and `lower` XY TCP commands are shifted (aborting if $\|\delta p_{xy}\|_2 > 2.0\text{ mm}$); `retreat` retains nominal XY, and orientation is uncompensated.

### 3.2.4 Substep Motor-Feedback Calibration for Lunar-Gravity Joint Torque Evaluation

In PyBullet 3.2.7 (`POSITION_CONTROL`), `getJointStates` returns a raw motor scalar $u_j$ after each external step $\Delta t_p$. Six independent single-body calibration experiments (comparing static lunar-gravity holding torque $mg\ell = 0.162\text{ N·m}$ and zero-gravity saturated rotational/prismatic accelerations across $n_s \in \{1, 4\}$ substeps) verified that this build reports the final internal substep impulse divided by $\Delta t_p$. Consequently, multiplying by $n_s = 4$ recovers the exact last-substep equivalent joint torque:

$$
\tau_j^*(k) = n_s\, u_j(k) = 4\, u_j(k), \qquad \tau_{j,\text{peak}}^* = \max_k |\tau_j^*(k)|, \qquad \tau_{j,\text{RMS}}^* = \sqrt{\frac{1}{N}\sum_{k=1}^N \tau_j^*(k)^2} \tag{8}
$$

Joint force/torque reaction wrenches and fixed-constraint wrenches are logged in separate telemetry channels and are never summed with motor effort $\tau_j^*$. Furthermore, while dynamic blocks are loaded with `URDF_USE_INERTIA_FROM_FILE` (matching candidate CAD inertia to $<10^{-14}$), the PiPER manipulator retains PyBullet's default collision-mesh inertia import (`Piper(self_collision=True)`), whose exact per-link principal inertias are archived in `robot_loaded_dynamics.json`.

---

## Section 4.2 & 4.3 (Insert into `4. Results and Discussion`) — Paired Pose Accuracy, Kinematic Feasibility, and Joint Torque Evaluation

### 4.2 Pose Accuracy, Vertical Offsets, and Kinematic Feasibility

Under identical macOS ARM64 hardware, frozen source code, preloaded 16-block inventory, and candidate sintered-regolith payload ($72.6067\text{ g}$ per block), both the uncompensated (`compensation_off`) and compensated (`compensation_on`) runs completed all 16 components, 96 motion segments, and 16 gated releases from step zero with zero out-of-definition collisions (**Table B2**). All 64 non-vertical segments passed direct joint-space quintic command-grid preflight, and all 32 vertical segments passed $2\text{ mm}$ sampled-IK checks (`0` RRT detours invoked).

**Table B2. Same-Host Paired 16-Component Assembly and Kinematic Performance Summary**

| Metric | Compensation Off | Compensation On (Adopted) | Change ($\text{On} - \text{Off}$) |
|---|---:|---:|---:|
| Completed components / reached segments / releases | 16/16 · 96/96 · 16/16 | 16/16 · 96/96 · 16/16 | Identical completion |
| Out-of-definition collisions / RRT detours | 0 / 0 | 0 / 0 | 0 / 0 |
| Simulated duration (s) / 240 Hz telemetry rows | $606.9833$ / $145,676$ | $607.1333$ / $145,712$ | $+0.1500\text{ s}$ ($+36$ rows) |
| Final 3D block position max error (mm) | $0.935791$ (Item 10) | $0.261732$ (Item 14) | $-0.674059$ ($-72.031\%$) |
| Final 3D block position RMS across 16 items (mm) | $0.422179$ | $0.142215$ | $-0.279964$ ($-66.314\%$) |
| Final horizontal XY block max error (mm) | $0.926721$ (Item 10) | $0.227289$ (Item 14) | $-0.699432$ ($-75.474\%$) |
| Final horizontal XY block RMS across 16 items (mm) | $0.411093$ | $0.104835$ | $-0.306259$ ($-74.499\%$) |
| Mean signed vertical $\Delta z$ (Layer 1 / Layer 2, mm) | $+0.039943$ / $+0.129918$ | $+0.039939$ / $+0.129902$ | $-0.000004$ / $-0.000016$ |
| Final block orientation max error ($^\circ$) | $0.155598$ (Item 6) | $0.186519$ (Item 15) | $+0.030921$ ($+19.872\%$) |
| Final block orientation RMS across 16 items ($^\circ$) | $0.069075$ | $0.082937$ | $+0.013862$ ($+20.068\%$) |
| Segment-end TCP max position / orientation error | $0.047565\text{ mm}$ / $0.000350^\circ$ | $0.047560\text{ mm}$ / $0.000350^\circ$ | $-0.000005\text{ mm}$ / $0.0^\circ$ |
| Inner-servo `FK(q_command)` tracking RMS / peak (mm) | $0.057412$ / $0.208732$ | $0.057415$ / $0.208732$ | $+0.000003\text{ mm}$ / $0.0$ |
| Minimum joint-limit margin across full run ($^\circ$) | $3.777857$ (J5, Item 10) | $3.753456$ (J5, Item 9) | $-0.024401^\circ$ |
| Minimum scaled singular value $\sigma_{\min}(\bar{J})$ (targets / full) | $0.273454$ / $0.029388$ | $0.273437$ / $0.029388$ | Rank 6 throughout |
| Maximum scaled condition number $\kappa(\bar{J})$ (targets / full) | $8.7196$ / $94.0872$ | $8.7201$ / $94.0872$ | $+0.0005$ at targets / $0.0000$ full-run |
| Peak actual joint speed across 6 axes (rad/s) | $0.600576$ (J6) | $0.600470$ (J6) | Within URDF $[5,5,5,5,5,3]$ |

Enabling post-lift XY grasp-offset compensation (maximum applied shift $0.825833\text{ mm}$ on Item 6, well below the $2.0\text{ mm}$ safety bound) reduced maximum 3D block placement error by $72.031\%$ and 3D RMS error by $66.314\%$, improving 14 of the 16 blocks (**Figure B-Err**). Crucially, segment-end TCP convergence ($\approx 0.0476\text{ mm}$) and `FK(q_command)` servo tracking RMS ($\approx 0.0574\text{ mm}$; joint tracking RMS $\le 0.0145^\circ$ on all six axes) remained virtually identical between the two runs. The placement improvement accompanies the post-lift geometric correction, with nearly identical inner-servo tracking across the two runs.

**Figure B-Decomp** reports horizontal error magnitude and signed vertical offset after the complete run. Lower-layer mean $\Delta z$ was $+0.039943\text{ mm}$ with compensation off and $+0.039939\text{ mm}$ with it on. Upper-layer means were $+0.129918\text{ mm}$ and $+0.129902\text{ mm}$, respectively. In both runs the 34-part block collision model used a $50\ \mu\text{m}$ PyBullet `collisionMargin`. The layer offsets were observed at that fixed setting. Quantifying the margin's contribution would require varying it while holding the support geometry and settling conditions fixed. Maximum horizontal error fell by $75.474\%$ ($0.926721 \to 0.227289\text{ mm}$), with four lower-layer blocks below $5\ \mu\text{m}$ in the compensated run. Maximum orientation error increased from $0.155598^\circ$ to $0.186519^\circ$ ($+0.030921^\circ$) alongside the XY-only command correction. For the $0.4934\text{ mm}$ nominal corner gaps, the horizontal clearance benefit justifies selecting the compensated condition for this configuration.

Across all $291,388$ logged $240\text{ Hz}$ states in both runs, $\bar{J}(q)$ maintained full numerical rank 6. The global minimum $\sigma_{\min}(\bar{J}) = 0.029388$ ($\kappa = 94.09$) occurred at the initial home transition ($t = 1/240\text{ s}$), while all 192 solved pick-and-place target postures maintained $\sigma_{\min}(\bar{J}) \ge 0.2734$ ($\kappa \le 8.72$) and joint-limit margins $\ge 3.753^\circ$ (tightest at wrist pitch `joint5`). Independent finite-difference Jacobian checks ($h = 10^{-6}\text{ rad}$) matched analytical $J(q)$ within $2.29 \times 10^{-10}$, and a fresh Stage 4 single-component cross-reproduction (`single01_compensated`, $11,300$ rows, $236$ video frames) matched the Stage 3 first placement event in both the compensation shift and the post-release error to $0.0\text{ m}$ numerical difference ($0.039958\text{ mm}$, $0.000977^\circ$).

### 4.3 Joint Torques Under Lunar Gravity

**Table B3** reports both raw motor feedback peaks and calibrated last-substep equivalent torques ($\tau_j^* = 4 u_j$) across the complete 16-component assembly, alongside peak timing and motion phase (**Figure B-Torque**, `compensation_on/joint_motion_torque.png`).

**Table B3. Full-Run Six-Axis Motor Torque Statistics Under Lunar Gravity ($g = 1.62\text{ m/s}^2$, $n_s = 4$)**

| Joint | Raw peak magnitude $\lvert u_j\rvert$ Off / On | Equivalent peak magnitude $\lvert\tau_j^*\rvert$ Off / On (N·m) | Equiv. Full-Run RMS Off / On (N·m) | Active-Only RMS$^\dagger$ Off / On (N·m) | Peak Occurrence in Adopted Run (`time / item / phase`) |
|---|---:|---:|---:|---:|---|
| `J1` | $3.7994$ / $3.7991$ | $15.1975$ / $15.1964$ | $2.1261$ / $2.1261$ | $2.1349$ / $2.1349$ | $421.80\text{ s}$ / Item 11 / `transfer` |
| `J2` | $3.2831$ / $3.2834$ | $13.1324$ / $13.1334$ | $1.8402$ / $1.8404$ | $1.8476$ / $1.8479$ | $577.97\text{ s}$ / Item 16 / `lift` |
| `J3` | $2.0944$ / $2.0947$ | $8.3777$ / $8.3790$ | $1.1675$ / $1.1674$ | $1.1710$ / $1.1709$ | $109.27\text{ s}$ / Item 3 / `lift` |
| `J4` | $0.6467$ / $0.6465$ | $2.5869$ / $2.5862$ | $0.3914$ / $0.3914$ | $0.3930$ / $0.3930$ | $421.80\text{ s}$ / Item 11 / `transfer` |
| `J5` | $0.3655$ / $0.3656$ | $1.4622$ / $1.4622$ | $0.1336$ / $0.1335$ | $0.1339$ / $0.1338$ | $169.75\text{ s}$ / Item 5 / `lift` |
| `J6` | $0.0251$ / $0.0251$ | $0.1002$ / $0.1002$ | $0.0175$ / $0.0179$ | $0.0176$ / $0.0180$ | $472.64\text{ s}$ / Item 13 / `approach` |

*Note:* $^\dagger$Active-only RMS excludes the $2\text{ s}$ `initialize` and $3\text{ s}$ `final_settle` windows ($144,476$ vs. $144,512$ samples). Configured PyBullet `force = 100` is an API clamp parameter rather than a certified hardware rating.

In the adopted run, the largest sampled equivalent torque was $15.196\text{ N·m}$ on `J1` at Item 11 transfer. The next-largest joint peaks were $13.133\text{ N·m}$ on `J2` (Item 16 lift) and $8.379\text{ N·m}$ on `J3` (Item 3 lift). Bullet's loaded robot and gripper mass total was $4.67\text{ kg}$, including the fixed $1.02\text{ kg}$ base. The remaining links totalled $3.65\text{ kg}$, and each candidate block weighed approximately $0.118\text{ N}$ at the simulated gravity. The measured torques combine gravity, inertia, and contact effects. Their individual contributions would require a torque decomposition. Enabling XY compensation changed individual joint peak magnitudes by at most $0.0013\text{ N·m}$ across axes and increased `J6` RMS by $2.271\%$ (approximately $0.00040\text{ N·m}$).

---

## Section 5 Excerpt (Insert into `5. Conclusions`) — Control Scope and Limitations

1. Under the frozen 16-component octagonal layout and candidate sintered EAC-1A regolith payload ($2,500\text{ kg/m}^3$, $72.61\text{ g}$), scaled DLS kinematics and $60\text{ Hz}$ feedback control achieved $16/16$ collision-checked assembly in both conditions; adopting post-lift XY grasp-offset compensation reduced maximum 3D placement error by $72.03\%$ ($0.9358 \to 0.2617\text{ mm}$) and horizontal XY error by $75.47\%$ ($0.9267 \to 0.2273\text{ mm}$) at a minor trade-off in orientation error ($+0.031^\circ$ max) and wrist RMS torque ($+2.27\%$ on `J6`).
2. Engineering boundaries are explicitly retained: block transport uses a bilateral-contact-gated fixed constraint rather than pure friction grasping; XY compensation reads noise-free simulation poses rather than vision estimates; collision verification is discrete in time and configuration; and calibrated $240\text{ Hz}$ last-substep equivalent torques reflect PyBullet's imported link inertias rather than all $960\text{ Hz}$ substep extrema or physical actuator thermal/rated limits.

---

## Standard APA 7th References (Part B Contribution for Master Reference List)

- Bock, T., & Linner, T. (2017). *Construction robots: Elementary technologies and single-task construction robots*. Cambridge University Press. https://doi.org/10.1017/CBO9781139872041
- Coumans, E., & Bai, Y. (2016). *PyBullet, a Python module for physics simulation for games, robotics and machine learning*. http://pybullet.org
- Dörfler, K., Sandy, T., Giftthaler, M., Gramazio, F., Kohler, M., & Buchli, J. (2016). Mobile robotic brickwork: Automation of a discrete robotic fabrication process using an autonomous mobile robot. In D. Reinhardt, R. Saunders, & J. Burry (Eds.), *Robotic Fabrication in Architecture, Art and Design 2016* (pp. 204–217). Springer. https://doi.org/10.1007/978-3-319-26378-6_15
- Giftthaler, M., Sandy, T., Dörfler, K., Brooks, I., Buckingham, M., Rey, G., Kohler, M., Gramazio, F., & Buchli, J. (2017). Mobile robotic fabrication at 1:1 scale: The In situ Fabricator. *Construction Robotics*, *1*(1–4), 3–14. https://doi.org/10.1007/s41693-017-0003-5
- Lynch, K. M., & Park, F. C. (2017). *Modern robotics: Mechanics, planning, and control*. Cambridge University Press.
- Nakamura, Y., & Hanafusa, H. (1986). Inverse kinematic solutions with singularity robustness for robot manipulator control. *Journal of Dynamic Systems, Measurement, and Control*, *108*(3), 163–171. https://doi.org/10.1115/1.3143764
- Siciliano, B., Sciavicco, L., Villani, L., & Oriolo, G. (2009). *Robotics: Modelling, planning and control*. Springer. https://doi.org/10.1007/978-1-84628-642-1
- Wampler, C. W. (1986). Manipulator inverse kinematic solutions based on vector formulations and damped least-squares methods. *IEEE Transactions on Systems, Man, and Cybernetics*, *16*(1), 93–101. https://doi.org/10.1109/TSMC.1986.289285

---

## Recommended Figures for Master Report Mapping

| Suggested Master Figure | File Path in Repository | Suggested English Caption |
|---|---|---|
| Structure & Interface Drawing | `AC回传/A/第三阶段_2026-11-13/图表/A03_Stage3_Engineering_EN.png` | Two-layer 16-component octagonal assembly layout, P3-GrooveKey-v2 dimensions, and boss-socket interface tolerances (units: mm). |
| Kinematic Conditioning | `05_Project3_月面机器人装配/运行验证/B_第三阶段_2026-11-10/compensation_on/limits_singularity.png` | Full-run joint-limit margin (top) and scaled Jacobian minimum singular value $\sigma_{\min}(\bar{J})$ (bottom) for the adopted compensated assembly ($607.13\text{ s}$). |
| Paired Final Pose Errors | `05_Project3_月面机器人装配/运行验证/B_第三阶段_2026-11-10/comparison_final_errors.png` | Same-host paired comparison of final 3D component position error (left) and orientation error (right) across all 16 components. |
| Horizontal Error and Signed Vertical Offset | `05_Project3_月面机器人装配/B_第四阶段定稿与汇报/图表/layer_dz_xy_decomposition.png` | Per-block horizontal error (maximum reduced by $75.5\%$) and observed layer offsets at fixed contact settings (mean $+0.040\text{ mm}$ lower and $+0.130\text{ mm}$ upper in both runs). |
| Joint Motion & Lunar Torque Trace | `05_Project3_月面机器人装配/运行验证/B_第三阶段_2026-11-10/compensation_on/joint_motion_torque.png` | Continuous $240\text{ Hz}$ joint angles, angular velocities, and calibrated last-substep equivalent torques $\tau_j^*$ under lunar gravity ($1.62\text{ m/s}^2$). |
