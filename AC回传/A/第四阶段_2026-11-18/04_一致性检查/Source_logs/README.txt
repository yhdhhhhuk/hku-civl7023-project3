Original formal-experiment logs for offline traceability

Each directory contains the original B same-host condition. The files are lossless gzip CSV archives from repository commit 628a189f8787efc51759d31595615c4c476aa8fb.

joint_full_trace.csv.gz records every 240 Hz external sample of joint positions, velocities, raw motor feedback, reactions, and phase identity. b_control_trace.csv.gz records the control samples and commanded/actual task states. The raw motor feedback is converted by the independently calibrated factor 4 for the last-internal-substep equivalent under this build.

Use Python gzip.open(filename, 'rt', encoding='utf-8-sig') to read either file directly, or decompress using any gzip-compatible utility. Offline_Log_SHA256.json gives both compressed and restored byte hashes, verified against the published manifests. Preserve the original archives when deriving plots.

The report's paired comparison uses compensation_off versus compensation_on. Full-run torque includes initialization and final settling. Original component errors, targets and scene logs are recorded in the corresponding Result.json files under Source_Evidence. The C Windows reproduction has its own source summary, independent audit and video hashes in Source_Evidence and Video_Identity_Map.json.
