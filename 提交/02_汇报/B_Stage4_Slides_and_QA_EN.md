# Part B Stage 4 Presentation Slides, 3.5-Min Script & 5-Min Q&A Pack

- **Course Assessment**: HKU CIVL 7023 Oral Presentation (20% of course grade; **10 minutes presentation + 5 minutes Q&A**, assessed by all course lecturers: Prof. Li Xiao, Dr. Bai Songnan, Dr. Shi Xiongtao, Dr. Wang Kun).
- **Recommended 10-Minute Team Time Allocation**:
  - **Part A (~3 min 00 s, Slides 1–3)**: Lunar construction background, `P3-GrooveKey-v2` geometry/interfaces, 16-block octagonal layout & nominal bearing check.
  - **Part B (~3 min 30 s, Slides 4–7 → `B_Stage4_Slides_EN.pptx` Slides 1–4)**: PiPER 6-DoF kinematics & Jacobian reachability, 60 Hz DLS closed-loop control & XY grasp-offset compensation, paired horizontal placement accuracy and orientation trade-off, calibrated lunar-gravity joint torque evaluation.
  - **Part C (~3 min 30 s, Slides 8–11)**: Preloaded 19-body scene, guarded motion planning (`64` direct quintic + `32` vertical IK/DLS), release gate, accelerated continuous assembly video demo (`compensation_on`), limitations & conclusions.

---

## 1. Slide-by-Slide Content & Word-for-Word 3.5-Minute English Script

> **Editable PowerPoint Deck**: `05_Project3_月面机器人装配/B_第四阶段定稿与汇报/B_Stage4_Slides_EN.pptx` (4 main slides and 1 Q&A backup in 16:9, using Part C's slide master).

### Slide B1 — PiPER 6-DoF Kinematics, Scaled Jacobian & Reachability (~50 seconds)
- **Visuals and supporting details**:
  - Coordinate chain $\{W\} \to \{B\} \to \{G\} \to \{T\}$ (`TCP_OFFSET = [0, 0, 0.1358] m`), decoupled symmetric jaw opening $w \in [0, 70]\text{ mm}$ ($q_7 = +w/2, q_8 = -w/2$), block origin recovery $p_O = p_C - R_{WO} r_{OC}$.
  - World-frame geometric Jacobian $J_i(q) = [a_i \times (p_T - o_i);\ a_i]$, characteristic length scaling $W_s = \mathrm{diag}(L^{-1}I_3, I_3)$ ($L = 0.3\text{ m}$), multi-seed projected DLS IK ($2^\circ$ inward limit margin, FK residual $<10\ \mu\text{m},\ 10^{-4}\text{ rad}$).
  - Key results: **96 / 96** actual poses solved · **$\ge 3.75^\circ$** min joint margin (J5) · **$\sigma_{\min}(\bar{J}) \ge 0.273$** at targets (`0.0294` full run, rank 6 throughout).
  - Embedded Figure: `compensation_on/limits_singularity.png`.
- **English Oral Script (~115 words, 50 s)**:
  > "Thank you, [Part A's Name]. Building on the GrooveKey-v2 block design, I will present the manipulator kinematics, control, and lunar-gravity evaluation.
  > First, we parse the six-axis PiPER kinematic chain directly from its URDF and define the nominal TCP 135.8 millimeters ahead of the gripper base, decoupling symmetric jaw opening from six-DoF arm motion. To avoid unit mismatch between meters and radians, we scale the world-frame geometric Jacobian with a 0.3-meter characteristic length and solve inverse kinematics via projected damped least squares within a two-degree joint-limit buffer. Across all 96 pick-and-place targets and 145,712 full-run physics steps, the scaled Jacobian maintains full rank six, with a minimum joint margin of 3.75 degrees at wrist joint five."
- **中文衔接与演讲提示**：承接 A 的构件抓持槽与 16 件目标位姿；用手势指向右侧奇异值曲线底部，强调全程数值满秩（无奇异失控），最小裕度发生在腕部俯仰轴 `J5`（`3.75°`）。

---

### Slide B2 — Closed-Loop Control & Post-Lift XY Grasp-Offset Compensation (~55 seconds)
- **Visuals and supporting details**:
  - Dual-loop architecture:
    - Non-vertical transitions: collision-checked quintic joint profile $h(s)=10s^3-15s^4+6s^5$; vertical descent/insertion: $2\text{ mm}$ sampled-IK + guarded Cartesian DLS.
    - Outer loop ($60\text{ Hz}$): $SO(3)$ log orientation error, $v_c = [3e_p; 3e_R]$, DLS ($\lambda = 0.02$), integrated position reference $q_{\text{ref}}$ opposing lunar gravity; convergence gate $<0.1\text{ mm}, <0.1^\circ, <0.02\text{ rad/s}$ for 15 samples.
    - Inner loop ($240\text{ Hz}$ external / $960\text{ Hz}$ internal substeps): `POSITION_CONTROL` ($K_p=0.15, K_v=1.0$).
  - Post-lift XY compensation at $z_T = 82\text{ mm}$: $r_{TO} = R_{WT}^T(p_O - p_T)$, $\delta p_{xy} = -[R_{WT,d} r_{TO}]_{xy}$ ($2\text{ mm}$ safety bound; adjusts `transfer`/`lower` XY only, using exact simulated poses).
  - Key results: **$0.0476\text{ mm}$** max TCP endpoint error · **$0.0574\text{ mm}$** `FK(q_command)` RMS · **$0.826\text{ mm}$** max XY shift applied.
  - Embedded Figure: `compensation_on/command_tracking.png`.
- **English Oral Script (~125 words, 55 s)**:
  > "Second, for motion execution under lunar gravity, non-vertical transfers follow smooth quintic joint trajectories, while vertical pick-and-insertion segments use dense two-millimeter IK checks followed by a 60-Hertz damped-least-squares outer feedback loop. Crucially, we integrate the joint position reference across cycles rather than resetting it to the measured angle, which provides the steady servo offset needed to counter gravity and achieves a command-tracking RMS of 0.057 millimeters.
  > However, even sub-tenth-millimeter TCP tracking cannot eliminate small block shifts caused during finger closure. Because our octagonal corners leave only a 0.49-millimeter nominal gap, we measure the held block's offset in the TCP frame after lifting and apply a bounded horizontal XY correction—up to 0.83 millimeters in our run—to the transfer and lowering commands."
- **中文演讲提示**：点出两个核心工程巧思：① 外环保留积分位置参考 $q_{\text{ref}}$ 抵消月面重力静差；② 区分“末端伺服精度（`0.057 mm`）”与“夹取偏置引起的构件对准误差”，自然引出下一页双工况对照。

---

### Slide B3 — XY Compensation Improves Horizontal Placement (~55 seconds)

- **On-slide evidence**: one chart compares horizontal error for each of the 16 blocks. The two same-host runs completed 16/16 blocks and 96/96 moves, with 16 gated releases and zero out-of-definition collisions in each.
- **Primary result**: maximum XY error dropped from $0.927$ to $0.227\text{ mm}$ ($-75.5\%$).
- **Trade-off**: maximum 3D error fell from $0.936$ to $0.262\text{ mm}$ ($-72.0\%$), and maximum orientation error increased from $0.156^\circ$ to $0.187^\circ$ ($+0.031^\circ$).
- **English oral script (~105 words, 55 s)**:

  > We ran both configurations on the same machine with the same block model. Each run assembled all sixteen blocks from scratch. The chart shows the horizontal error of each block after the complete run. Enabling XY compensation reduced the maximum from 0.927 to 0.227 millimeters, a 75.5 percent reduction. Maximum three-dimensional error also fell by 72 percent. In both runs, average height offsets were about 0.040 millimeters in the lower layer and 0.130 in the upper layer at the fixed contact settings. Maximum orientation error rose from 0.156 to 0.187 degrees. We chose compensation because horizontal clearance was our priority.

- **中文提示**：指向逐件 XY 图和最大误差，随后说明姿态增加 $0.031^\circ$。竖向均值是固定接触设置下的观察结果。

---

### Slide B4 — Lunar-Gravity ($1.62\text{ m/s}^2$) Joint Torque Calibration & Evaluation (~50 seconds)
- **Visuals and supporting details**:
  - Substep feedback calibration (`verify_feedback.py`, 6/6 passed): with 4 substeps per $240\text{ Hz}$ step, PyBullet's raw motor field reports final-substep impulse / $\Delta t_p$, so $\tau_j^* = 4 u_j$ recovers the exact last-substep equivalent torque (verified against $0.162\text{ N·m}$ static gravity hold & zero-$g$ acceleration).
  - Full-run 6-axis torque summary (`compensation_on`):
    - Peak $|\tau_j^*|$: **`J1 = 15.196 N·m`** (Item 11 `transfer`), **`J2 = 13.13 N·m`** (Item 16 `lift`), **`J3 = 8.38 N·m`** (Item 3 `lift`), `J4 = 2.59`, `J5 = 1.46`, `J6 = 0.10 N·m`.
    - Full-run RMS: `J1 = 2.13`, `J2 = 1.84`, `J3 = 1.17`, `J4 = 0.39`, `J5 = 0.13`, `J6 = 0.0179 N·m` (`+2.27%` vs. off).
  - Scope: loaded robot and gripper mass totals $4.67\text{ kg}$, including the fixed $1.02\text{ kg}$ base. Sampled drive effort includes gravity, inertia, and contact effects. The feedback records the last internal substep at $240\text{ Hz}$.
  - Embedded figure: `compensation_on/joint_motion_torque.png`.
- **English oral script (~103 words, 50 s)**:

  > To evaluate joint torque under lunar gravity, we checked the motor feedback in six independent tests. With four internal substeps, multiplying the raw output by four recovers the last-substep equivalent torque. During the 607-second assembly, the highest sampled value was 15.196 Newton-meters on joint one during transfer of block eleven. Joint two peaked at 13.133 Newton-meters during lifting. The feedback combines gravity, inertia, and contact effects. Compensation increased joint six RMS torque by about 0.0004 Newton-meters. I will now pass to Part C for motion planning and the full assembly simulation.

- **中文提示**：指出 J1 峰值发生于第 11 件转运。说明采样及校准口径，再交接给 C。

---

### Slide B5 (Backup / Q&A Appendix Slide) — Cross-Reproduction & Modeling Boundaries
- Stage 4 fresh launch (`calibrate` 6/6 + `single01_compensated` 11,300 rows, 236 frames): **$0.0\text{ m}$ numerical difference** vs. the first placement event in Stage 3 ($0.039958\text{ mm}$, $0.000977^\circ$).
- Explicit boundary matrix: URDF vs. Bullet imported link inertias (`link2` $I_{yy}: 0.0679 \to 0.0133\text{ kg·m}^2$), bilateral-contact-gated fixed grasp vs. pure friction hold, exact simulation pose compensation vs. noisy vision feedback.

---

## 2. Five-Minute Q&A Preparation Bank (10 High-Probability Examiner Questions)

### Q1 (Dr. Wang — Kinematics & Scaling): *Why did you choose a characteristic length $L = 0.3\text{ m}$ in the scaled Jacobian $\bar{J} = W_s J$, and why not use standard DH parameters?*
- **English Answer**:
  > "First, an unscaled $6\times 6$ Jacobian mixes linear velocity in $\text{m/s}$ with angular velocity in $\text{rad/s}$, making singular values unit-dependent. Choosing $L = 0.3\text{ m}$ matches PiPER's typical assembly reach ($0.26\text{ m}$ octagon center, $\sim 0.3\text{ m}$ lever arm), so a $1\text{ rad}$ rotation and a $0.3\text{ m}$ translation receive balanced weight in SVD conditioning and DLS inversion. Second, parsing the exact URDF joint origins and axes directly avoids introducing DH frame conversion approximations on offset joints like `joint2` and `joint4`, and cross-checked against PyBullet's Jacobian and central finite differences to $2 \times 10^{-10}$."
- **中文要点**：$L=0.3\text{ m}$ 对应八边形工作半径量级，消除米与弧度量纲混杂；直接解析 URDF 避免非正交偏置关节手工转 DH 出错，且有限差分核对达 $2\times 10^{-10}$。

### Q2 (Dr. Wang — Control): *Your outer controller is kinematic DLS without an explicit gravity feedforward torque term. How did it achieve $0.048\text{ mm}$ steady-state TCP accuracy under lunar gravity?*
- **English Answer**:
  > "If we updated the position command as $q_{\text{measured}} + \Delta t_c \dot{q}_c$ every cycle, the inner proportional-derivative position servo (`positionGain = 0.15`) would suffer a permanent steady-state droop against lunar gravity. Instead, our outer loop integrates an internal joint reference $q_{\text{ref},k+1} = q_{\text{ref},k} + \Delta t_c \dot{q}_c$ clamped within $\pm 0.03\text{ rad}$ of actual $q_k$. This acts as an integral action in task space, automatically building up the exact servo position offset required to balance lunar gravity while keeping `FK(q_command)` tracking RMS at $0.057\text{ mm}$."
- **中文要点**：见 `controller.py` 第146–150行，保留积分参考 $q_{\text{ref}}$ 相当于外环积分器，自动建立抗月面重力所需的内环位置偏置（限幅 $\pm 0.03\text{ rad}$ 防积分饱和）。

### Q3 — *What can the observed height difference between the two layers tell us?*

- **English answer**:

  > With compensation off, the mean signed vertical offsets were +0.039943 millimeters in the lower layer and +0.129918 in the upper layer. With compensation on, they were +0.039939 and +0.129902 millimeters. Both runs used a 50-micrometer collision margin with the same support geometry. We observed a repeatable layer difference across these two conditions at that setting. A separate margin sweep would be needed to estimate how much the margin contributes. Maximum horizontal error fell by 75.5 percent when we enabled the XY correction.

- **中文要点**：两组均有约 0.040／0.130 mm 下／上层平均竖向偏差。裕度固定，需单独改变该参数才能量化其贡献。

### Q4 — *How did orientation change when you enabled XY compensation?*

- **English answer**:

  > Maximum orientation error rose from 0.156 to 0.187 degrees. The correction only shifts horizontal commands and keeps the nominal orientation command. Each block settles after release, so a separate contact analysis would be needed to explain the increase. We selected the compensated condition for its improved horizontal placement in the tight corner gaps and report the orientation increase alongside that result.

- **中文要点**：XY 指令修正伴随最大姿态误差增加 $0.031^\circ$。两次运行的结果支持本配置的取舍，具体接触机理待单独分析。

### Q5 (Dr. Wang / Dr. Shi — Torque Calibration): *Why do you multiply PyBullet's motor torque output by 4, and can $15.2\text{ N·m}$ be compared directly against real PiPER actuator limits?*
- **English Answer**:
  > "We run four internal physics substeps per $240\text{ Hz}$ external step (`960 Hz` internal solver) for stable multi-convex contact release. Through six independent single-link static gravity and zero-gravity saturation tests (`verify_feedback.py`), we proved that PyBullet 3.2.7 reports the last substep impulse divided by the external $\Delta t_p$, so multiplying by $n_s = 4$ recovers the exact physical torque in $\text{N·m}$. However, we do not claim hardware safety certification for two reasons: $240\text{ Hz}$ logging samples one of every four $960\text{ Hz}$ substeps, and PyBullet recomputes robot link inertias from collision meshes unless overridden (`robot_loaded_dynamics.json`)."
- **中文要点**：6组校准实验严格证明了 4 子步下 `motor × 4` 等于物理等效力矩；同时诚实声明两点边界：240 Hz 采样未捕获全部 960 Hz 子步尖峰，且机器人本体沿用了 Bullet 导入惯量。

### Q6 (Dr. Shi — Grasping): *You used an assisted fixed constraint during transport. Isn't that teleporting or faking the grasp?*
- **English Answer**:
  > "No teleportation or pose resetting occurs at any point after step zero—all 16 attach events verified zero instantaneous displacement (`0.0 m`). The gripper closes physically at $1\text{ N}$ per finger into the side slots, and the fixed constraint is created at the exact live relative pose only after both fingers establish positive normal forces inside the $38 \times 4 \times 12\text{ mm}$ slot core. Similarly, release requires five consecutive $50\text{ ms}$ clear samples ($>35.5\text{ mm}$ opening, zero effective finger contact, $<2\text{ mm/s}$) before detaching and letting the block settle dynamically. We explicitly state that this models form-closed carrying rather than pure Coulomb friction margin."
- **中文要点**：绝无瞬移（16次建约束位移均为 `0.0 m`），必须双指在槽核心区产生正法向接触才按实时相对位姿建约束，释放也须满足 5 次连续稳定无接触门控后自由沉降。

### Q7 (Dr. Shi — Motion Planning): *You implemented RRT-Connect, yet your table reports 0 RRT segments in both 16-piece runs. Does that mean collision planning wasn't needed?*
- **English Answer**:
  > "Collision checking was active on every single segment, updating all 15 non-active blocks dynamically. Our planner follows a hierarchical 'direct-first, RRT-fallback' strategy: because all pick and place approaches pass through a clear overhead plane at $z_T = 82\text{ mm}$ (well above the $47\text{ mm}$ two-layer structure), direct quintic joint interpolation passed $5\text{ mrad}$ edge checks and exact command-grid preflight on all 64 non-vertical segments. Equally important, in Part C's earlier uncompensated Windows run (`full01`), that exact preflight guard caught a $0.158\text{ mm}$ predicted penetration on Item 10 and safely halted before collision—proving the guard is genuinely active."
- **中文要点**：先直连预检、受阻才调 RRT；`82 mm` 安全高空平面使 64 段直连全部通过命令网格预检，且 C 第二阶段 `full01` 第10件被预检成功拦截（预测穿透 `0.158 mm`）恰恰证明避碰守卫真实有效。

### Q8 (Dr. Bai — Material & Lunar Environment): *How does lunar gravity ($1.62\text{ m/s}^2$) affect your assembly compared to Earth gravity ($9.81\text{ m/s}^2$), and how realistic is the $2,500\text{ kg/m}^3$ material model?*
- **English Answer**:
  > "First, lunar gravity reduces both manipulator self-weight holding torques and inter-block normal contact forces to one-sixth of Earth values—lowering nominal bearing stress to just $117\text{ Pa}$ between layers and $180\text{ Pa}$ at the base, which saves actuator energy on `J2` and `J3` but also reduces frictional resistance against lateral nudges during release, making clean non-contact jaw opening critical. Second, $2,500\text{ kg/m}^3$ ($72.6\text{ g}$ per block) is adopted from Ginés-Palomares et al. (2023) for sintered EAC-1A lunar regolith simulant near $1120\ ^\circ\text{C}$; shrinkage tolerances, surface roughness, and regolith dust abrasion remain physical extensions beyond rigid-body simulation."
- **中文要点**：月面 1/6 重力显著降低了 `J2/J3` 抗重力矩和层间承压（`117/180 Pa`），但也减小了层间摩擦抗滑力，因此释放门控避免手指刮蹭尤为关键；`2500 kg/m³` 源自 EAC-1A 烧结文献。

### Q9 (Prof. Li — DfMA & Scalability): *From an Industrialized Construction / DfMA perspective, why has your octagonal ring left $0.49\text{ mm}$ corner gaps without lateral interlocking, and how would this scale to a real lunar shelter?*
- **English Answer**:
  > "This reflects a deliberate Design-for-Manufacture-and-Assembly trade-off for a single fixed-base 6-DoF arm with a parallel jaw gripper: reusing one identical rectangular GrooveKey-v2 module across eight $45^\circ$ sectors eliminates part-type proliferation, while side slots keep fingers outside the ring footprint and $0.49\text{ mm}$ corner clearance prevents over-constrained jamming during vertical insertion. Scaling to a full lunar vault would combine trapezoidalvoussoir blocks with lateral shear keys, mobile base repositioning as shown in Dr. Bai's lecture, and visual servoing."
- **中文要点**：体现 DfMA 单一标准件复用与固定单臂平行夹爪可达性折中；扩展到真实月面穹顶需引入楔形互锁砌块、移动底盘重定位与视觉伺服。

### Q10 (All Lecturers — Sensing Realism): *Your grasp-offset compensation uses exact simulator poses. What happens under real camera calibration and pose-estimation noise?*
- **English Answer**:
  > "We explicitly highlight that boundary. Because our nominal corner clearance is $0.493\text{ mm}$ and boss-socket lateral clearance is $1.0\text{ mm}$ per side, a real wrist-mounted RGB-D or fiducial marker system would need sub-$0.2\text{ mm}$ relative pose precision between the gripper and held block—achievable via close-range in-hand visual inspection right after lifting—combined with impedance or admittance force control during the final $3\text{ mm}$ socket insertion."
- **中文要点**：手眼近距视觉标定（抬升后固定视距拍构件基准边，精度可达 `<0.2 mm`）配合最后 `3 mm` 插合阶段的阻抗/导纳柔顺控制，即可替代仿真理想位姿。
