CIVL7023 Project 3 | Part A | 18 November 2026
Revision incorporating the published B Stage 4 submission
Git revision 628a189f8787efc51759d31595615c4c476aa8fb
https://github.com/yhdhhhhuk/hku-civl7023-project3/tree/628a189f8787efc51759d31595615c4c476aa8fb

READ AND PRESENT

01_Report contains the integrated English report in editable Word and print PDF formats, together with its English figures.
02_CAD contains the V2 block and 16-block assembly, editable DWG and FreeCAD files, STEP and STL exports, and the dimensioned English A3 drawing. A reconciled the geometry files and the English engineering sheet against B's published revision. The CAD README explains the millimetre and metre STL variants.
03_A汇报 contains A's editable slides, PDF backup, English speaking guide and English Q&A. A's allotted time is 3 minutes. The published team allocation gives B and C 3 minutes 30 seconds each, including transitions and video within the 10-minute total.
04_一致性检查 contains the checked run records, logs, CAD mapping, video identities and report checks. The file Consistency_Check_Record.txt describes the numerical checks and how to trace a result to its source.
05_B_Handoff_EN contains B's original English report module, editable PowerPoint and speaking notes for the team, plus its full-speed 16-component demonstration video. B's deck has four speaking slides and one backup slide. Source_Files.json identifies the Git paths and file hashes.

WHICH RUN SUPPORTS EACH CLAIM

10 November | B, same host, full assembly | 16/16 components in each of two runs (compensation off/on). Maximum 3D placement error fell from 0.935791 to 0.261732 mm. Maximum horizontal error fell from 0.926721 to 0.227289 mm. Maximum orientation error rose from 0.155598 to 0.186519 degrees and J6 full-run RMS torque increased by 2.27%. One run was recorded per condition. B's Stage 4 submission adds a per-component decomposition of these existing runs. The observed mean signed vertical displacement was approximately +0.040 mm in the lower layer and +0.130 mm in the upper layer in both conditions.

Published 15 November | C, Windows, full assembly | Independent compensated reproduction with 16/16 components, maximum 3D error 0.350763 mm and maximum orientation error 0.586786 degrees.

17 November | B, macOS ARM64, representative single component | Six calibration checks passed. One component completed all six motion targets in 47.0833 s, with 11,300 external-step samples, 236 video frames, and final position/orientation errors of 0.039958 mm and 0.000977 degrees. This run checks the published startup, control, release and analysis workflow. Use the separate full runs above for whole-assembly performance.

Group playback | The formal compensated 16-part video belongs to the 10 November B experiment; the Windows full-run video and the 17 November single-part recording each have their own result records. The full-speed B compensated video is in 05_B_Handoff_EN. The Stage 4 single-component video is in 04_一致性检查/B_Stage4_Evidence/single01. The complete team simulation and original recordings are also available under the pinned repository revision.

BEFORE TEAM SUBMISSION

Add the three authors' English names, HKU IDs and group number when supplied. A has retained 2500 kg/m3 (72.6067 g per block) as a candidate material assumption. All values reported for this payload refer to the simulated model. Formal material adoption requires A's decision.

The repository at this revision includes B's Stage 4 handoff and C's earlier Windows full assembly evidence. The team still needs to supply any subsequent C Stage 4 Windows return, combined group deck, actual rehearsal records and final review. Course Overview, page 6, specifies a Turnitin similarity limit of 10% and an AI similarity limit of 10%, excluding references. Confirm both scores through the course submission system.

PACKAGE_SHA256.json records the size and SHA-256 digest of each delivered file other than the manifest itself.
