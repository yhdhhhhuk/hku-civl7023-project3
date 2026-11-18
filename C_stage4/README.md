# C stage-4 handoff and remaining group actions

Date: 19 November 2026. Integration baseline: 628a189. C's deliverables are in English. A and B source deliverables have not been edited.

## Completed technical work

- Scanned all 331 tracked C-scoped files across the available stages, templates, historical evidence and copied submission sources. Initial audit: 157 paths and 125 text/Office files contained Han characters. See the machine-readable audit for the exact scope.
- Translated C narrative handoffs, technical chapters, reproduction records, issue table, speaker notes and templates. Stage-2 and stage-3 editable slides are supplied in English, including chart labels and speaker notes.
- Prepared four English C presentation slides for the final group presentation and PDF backups.
- Verified the 161-file formal package and 10 lossless logs. Six local feedback tests passed. A new Windows stage-4 single run completed from zero with 11300 continuous rows, position error 0.0399591 mm, orientation error 0.000977302 degrees and 236 verified video frames. All independent checks passed. This is a new single run, not another full 16-component experiment.
- Exported the selected B compensation-on physical video at 8x: 3036 frames, 40 fps, 75.9 s. English overlay states the 607.13 s continuous physical source. See video_lineage.json for SHA256 values.
- Added run_stage3.py and run_C_stage4.cmd as ASCII-named launchers. The new launcher defaults to a headless single run. The original B launcher was inspected, not executed: it requires a different environment path and forces --gui. It remains unchanged because it is B's file.

## Language and evidence boundary

Historical raw logs, frozen source snapshots, provenance hashes, dependency paths and B/A copies of evidence remain byte-preserved. Some contain legacy Chinese path identifiers or frozen comments. They are not rewritten and presented as original evidence. Compatibility filenames remain where A/B links or executable imports depend on them. English-named delivery copies and the mapping allow reviewers to use C's material without reading Chinese. This is not a claim that every byte in the repository or Git history is English.

## Group actions still required

A's three personal English slides are not present in the checked-out latest repository. C's four slides and B's four main slides plus one backup are ready for integration; a final 10–11-slide group deck cannot be labelled complete until A's material is supplied. Do not invent A's approval, material adoption or student names/UIDs.

Two live 10-minute group rehearsals are not yet recorded. Use rehearsal_log.csv to record actual times. The planned split is A 3:00, B 3:30 and C 3:30, including the 75.9 s C video. Planned timing is not an observed rehearsal.

C technical material does not certify the final Word report, similarity scores, material approval, CAD sign-off or course submission. Those remain member-owned actions.

## Restore new C evidence

From the repository root, run `python C_stage4/restore_evidence.py --verify-only` to verify the two new compressed logs, or omit the option to restore them. The existing shared index and B publication manifest are unchanged.
