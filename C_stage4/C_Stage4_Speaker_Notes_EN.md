# C stage-4 speaking script and timing plan

Planned total: 210 seconds. No live rehearsal is claimed.

1. Scene (45 s): All 16 components are preloaded, making 19 physical bodies with the robot, ground and visual tray. The other 15 components are obstacles in every motion. Contact gates assisted grasping; components remain dynamic after stable release.
2. Planning (45 s): Formal runs used 64 checked direct segments and 32 vertical sampled segments. RRT was available but not executed. Explain 5 mrad direct edges, 2 mm Cartesian sampling, 1 mrad vertical edges and online guards. Zero recorded violations is bounded by discrete checks and explicit contact exemptions.
3. Demonstration (76 s): Play B_formal_compensation_on_8x.mp4. State that the footage comes from B's selected continuous 607.13 s compensation-on run, accelerated eightfold. Do not quote C Windows metrics over this video.
4. Conclusion (44 s): B's paired maximum position error changed from 0.9358 to 0.2617 mm while orientation changed from 0.1556 to 0.1865 degrees. C independently reproduced a full run in stage 3 and a fresh single run in stage 4. Candidate material, assisted grasping, exact simulated pose and discrete collision sampling bound the conclusions.

Keep B's four main slides before C's four. B's fifth page is a Q&A backup. Add A's three approved slides before B when received. A's slides and two measured team rehearsal records are still missing. Never prefill their completion.

Q&A: RRT execution, historical failure versus formal paired results, ideal pose versus sensing, feedback substeps, material assumptions and structural limitations are addressed in the C report. B's original Q&A file remains available in the group submission folder.
