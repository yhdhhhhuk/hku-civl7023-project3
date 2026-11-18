# C stage-2 speaker notes and questions

## Scene (30 seconds)
Our contribution connects the structure and controller to continuous assembly. All 16 components exist at the start, under lunar gravity with dynamic rigid bodies and a fixed-base PiPER. Material properties remain modelling assumptions.

## Continuous workflow (40 seconds)
Each component is approached, grasped, lifted, transferred, lowered and released before retreat. The other 15 components are updated as obstacles. Both fingers must establish contact before the assist constraint is created. Release requires sufficient opening, cleared contact and consecutive stable samples.

## Planning (40 seconds)
The formal runs used 64 direct segments and 32 vertical sampled segments. RRT is available but was not executed. Collision checks are discrete and stage-dependent, so zero recorded violations is not a continuous-time proof.

## Formal comparison (45 seconds)
B completed two full runs on one machine. Compensation reduced maximum position error but increased maximum orientation error and some torque measures. C's historical failure explains the motivation; it is not the off run in this comparison.

## Windows reproduction (40 seconds)
Show C's separate physical run and metrics, with its own environment, hashes, logs and video. Read the values from the verified result table. Do not label a Windows frame with B's paired-run values.

## Scope (30 seconds)
Compensation uses exact simulated pose without visual noise. Fixed constraints assist grasping. Material, corner gaps, absent lateral connections and discrete sampling limit the conclusions. This is not evidence of real-hardware or structural reliability.

## Questions
- Why no RRT? Direct paths were feasible in this run. A historical obstacle demonstration is not a statistic for the formal run.
- Why do platforms differ? Report both outcomes and inspect model, environment and numerical differences. One reproduction does not estimate a success-rate distribution.
- Why multiply motor feedback by four? Six calibration cases support a last-substep equivalent for this four-substep configuration, not all internal extrema.
- Were objects teleported? After initial placement, physics executes the motion. Attachment displacement and inventory are audited. Compensation changes TCP XY commands only.
- Is the group project finished? Technical delivery, material approval, final integration and rehearsals are separate milestones.

Historical stage-2 note: the original Windows run completed nine components before a preflight rejection; its compensated successor completed 16. Comparing the successor against an uncompensated B reference confounds method and platform effects. Stage-3 paired results were not yet available at that stage.
