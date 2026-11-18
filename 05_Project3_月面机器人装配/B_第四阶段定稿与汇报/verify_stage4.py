"""Stage 4 B verification: parameter/dependency freeze, XY-vs-Z error decomposition, and cross-reproduction audit."""
from pathlib import Path
import csv
import datetime
import gzip
import hashlib
import json
import math
import os
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "05_Project3_月面机器人装配"
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT / ".cache/matplotlib"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT_DIR = Path(__file__).resolve().parent
FIG_DIR = OUT_DIR / "图表"
REPRO_DIR = PROJECT / "运行验证/B_第四阶段复现_2026-11-17"
STAGE3_DIR = PROJECT / "运行验证/B_第三阶段_2026-11-10"
# Pin the independently recorded pre-revision environment and raw-log identity.
ARCHIVED_BASELINE_SHA256 = "a89eb1518549f61b13683789fe84cd0939113a2fa68ac5fd2c97a6197f68f7fd"
HK = datetime.timezone(datetime.timedelta(hours=8))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_urdf_chain(urdf_path: Path):
    tree = ET.parse(urdf_path).getroot()
    joints = []
    for j in tree.findall("joint"):
        name = j.get("name")
        jtype = j.get("type")
        parent = j.find("parent").get("link")
        child = j.find("child").get("link")
        origin_el = j.find("origin")
        xyz = [float(x) for x in origin_el.get("xyz", "0 0 0").split()] if origin_el is not None else [0.0, 0.0, 0.0]
        rpy = [float(x) for x in origin_el.get("rpy", "0 0 0").split()] if origin_el is not None else [0.0, 0.0, 0.0]
        axis_el = j.find("axis")
        axis = [float(x) for x in axis_el.get("xyz").split()] if axis_el is not None else None
        limit_el = j.find("limit")
        limits = None
        if limit_el is not None:
            lo = float(limit_el.get("lower"))
            hi = float(limit_el.get("upper"))
            limits = {
                "lower": lo,
                "upper": hi,
                "lower_deg_if_revolute": round(math.degrees(lo), 6) if jtype == "revolute" else None,
                "upper_deg_if_revolute": round(math.degrees(hi), 6) if jtype == "revolute" else None,
                "effort_api_param": float(limit_el.get("effort")),
                "velocity_limit": float(limit_el.get("velocity")),
            }
        joints.append({
            "name": name,
            "type": jtype,
            "parent_link": parent,
            "child_link": child,
            "origin_xyz_m": xyz,
            "origin_rpy_rad": rpy,
            "axis_local": axis,
            "limits": limits,
        })
    return joints


def compute_xy_z_decomposition():
    off_res = json.loads((STAGE3_DIR / "compensation_off/result.json").read_text(encoding="utf8"))
    on_res = json.loads((STAGE3_DIR / "compensation_on/result.json").read_text(encoding="utf8"))
    expected_items = list(range(1, 17))
    for condition, result in (("off", off_res), ("on", on_res)):
        if result["success"] is not True or [row["item"] for row in result["final"]] != expected_items:
            raise ValueError(f"Incomplete Stage 3 final inventory for compensation {condition}")
    rows = []
    for r_off, r_on in zip(off_res["final"], on_res["final"]):
        if r_off["target"] != r_on["target"]:
            raise ValueError(f"Stage 3 targets differ for item {r_off['item']}")
        item = r_off["item"]
        layer = 1 if item <= 8 else 2
        d_off = (np.array(r_off["origin"]) - np.array(r_off["target"])) * 1000.0
        d_on = (np.array(r_on["origin"]) - np.array(r_on["target"])) * 1000.0
        xy_off = float(math.hypot(d_off[0], d_off[1]))
        xy_on = float(math.hypot(d_on[0], d_on[1]))
        xyz_off = float(np.linalg.norm(d_off))
        xyz_on = float(np.linalg.norm(d_on))
        rot_off = math.degrees(float(r_off["orientation_error_rad"]))
        rot_on = math.degrees(float(r_on["orientation_error_rad"]))
        rows.append({
            "item": item,
            "layer": layer,
            "off_dx_mm": float(d_off[0]),
            "off_dy_mm": float(d_off[1]),
            "off_dz_mm": float(d_off[2]),
            "off_xy_norm_mm": xy_off,
            "off_xyz_norm_mm": xyz_off,
            "off_orientation_deg": rot_off,
            "on_dx_mm": float(d_on[0]),
            "on_dy_mm": float(d_on[1]),
            "on_dz_mm": float(d_on[2]),
            "on_xy_norm_mm": xy_on,
            "on_xyz_norm_mm": xyz_on,
            "on_orientation_deg": rot_on,
        })

    csv_path = OUT_DIR / "XY与竖向误差分解.csv"
    with csv_path.open("w", newline="", encoding="utf8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    items = np.array([r["item"] for r in rows])
    off_xy = np.array([r["off_xy_norm_mm"] for r in rows])
    on_xy = np.array([r["on_xy_norm_mm"] for r in rows])
    xy_reduction_pct = (1 - on_xy.max() / off_xy.max()) * 100
    dz_by_condition = {
        condition: np.array([row[f"{condition}_dz_mm"] for row in rows])
        for condition in ("off", "on")
    }
    layer_statistics = {}
    for condition, dz in dz_by_condition.items():
        layer_statistics[condition] = {
            f"layer{layer}": {
                "items": len(values),
                "min_mm": float(values.min()),
                "max_mm": float(values.max()),
                "mean_mm": float(values.mean()),
            }
            for layer, values in enumerate((dz[:8], dz[8:]), start=1)
        }

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    width = 0.38
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.4), dpi=300)

    ax = axes[0]
    ax.bar(items - width / 2, [r["off_xy_norm_mm"] for r in rows], width, label="Compensation off (XY)", color="#1f77b4")
    ax.bar(items + width / 2, [r["on_xy_norm_mm"] for r in rows], width, label="Compensation on (XY)", color="#ff7f0e")
    ax.axvline(8.5, color="#666666", linestyle="--", linewidth=0.9)
    ax.set_xticks(items)
    ax.set_xlabel("Component ID")
    ax.set_ylabel("Horizontal XY error (mm)")
    ax.set_title(
        f"(a) Horizontal placement error (max. {off_xy.max():.3f} → "
        f"{on_xy.max():.3f} mm, −{xy_reduction_pct:.1f}%)",
        fontsize=10.5,
    )
    ax.legend(frameon=True, fontsize=8.5)
    ax.grid(axis="y", alpha=0.25)

    ax2 = axes[1]
    for condition, offset, color, marker in (
        ("off", -0.12, "#1f77b4", "o"),
        ("on", 0.12, "#ff7f0e", "s"),
    ):
        ax2.scatter(items + offset, dz_by_condition[condition], marker=marker,
                    color=color, s=21, label=f"Compensation {condition}")
    ax2.axvline(8.5, color="#666666", linestyle="--", linewidth=0.9)
    ax2.set_xticks(items)
    ax2.set_xlabel("Component ID")
    ax2.set_ylabel("Signed vertical error Δz (mm)")
    ax2.set_title("(b) Observed vertical placement deviation", fontsize=10.5)
    ax2.legend(frameon=True, fontsize=8.0)
    ax2.grid(axis="y", alpha=0.25)

    layer_means = "   |   ".join(
        f"Layer {layer} mean Δz: off {layer_statistics['off'][f'layer{layer}']['mean_mm']:+.6f} mm, "
        f"on {layer_statistics['on'][f'layer{layer}']['mean_mm']:+.6f} mm"
        for layer in (1, 2)
    )
    fig.text(0.5, 0.025, layer_means, ha="center", fontsize=8.5)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig_path = FIG_DIR / "layer_dz_xy_decomposition.png"
    fig.savefig(fig_path, bbox_inches="tight")
    plt.close(fig)

    return {
        "csv_path": str(csv_path.relative_to(ROOT)),
        "figure_path": str(fig_path.relative_to(ROOT)),
        "off_max_xy_mm": float(off_xy.max()),
        "on_max_xy_mm": float(on_xy.max()),
        "xy_max_reduction_pct": float(xy_reduction_pct),
        "off_rms_xy_mm": float(np.sqrt(np.mean(off_xy ** 2))),
        "on_rms_xy_mm": float(np.sqrt(np.mean(on_xy ** 2))),
        "xy_rms_reduction_pct": float((np.sqrt(np.mean(off_xy ** 2)) - np.sqrt(np.mean(on_xy ** 2))) / np.sqrt(np.mean(off_xy ** 2)) * 100.0),
        "vertical_error_definition": "Signed final block bottom-origin z minus target z after settling.",
        "vertical_error_by_condition_and_layer": layer_statistics,
        "interpretation": "Observed settled values for these two runs. The configured collision margin was fixed, so its effect on vertical error is not isolated by this comparison.",
    }


def validate_trace(path, expected):
    """Hash original bytes and check every CSV sample index without writing a file."""
    open_trace = gzip.open if path.suffix == ".gz" else Path.open
    digest = hashlib.sha256()
    byte_count = 0
    row_count = 0
    with open_trace(path, "rb") as trace:
        header = trace.readline()
        if not header.startswith((b"step,", b"\xef\xbb\xbfstep,")):
            raise ValueError(f"{path.name}: CSV step header is missing")
        digest.update(header)
        byte_count += len(header)
        for row_count, line in enumerate(trace, start=1):
            step, separator, _ = line.partition(b",")
            if not separator or step != str(row_count).encode("ascii"):
                raise ValueError(f"{path.name}: expected contiguous step {row_count}")
            digest.update(line)
            byte_count += len(line)
    actual = {"raw_sha256": digest.hexdigest(), "raw_bytes": byte_count, "rows": row_count}
    if actual != expected:
        raise ValueError(f"{path.name}: original SHA/bytes/rows mismatch: expected {expected}, got {actual}")
    return actual


def audit_reproduction(baseline):
    single_dir = REPRO_DIR / "single01_compensated"
    cal_file = REPRO_DIR / "calibration01/反馈字段独立核对.json"
    calibration = json.loads(cal_file.read_text(encoding="utf8"))
    tests = calibration.get("tests") if isinstance(calibration, dict) else None
    if not isinstance(tests, list) or len(tests) != 6:
        raise ValueError("Feedback calibration must contain exactly 6 archived tests")
    failed = [i for i, test in enumerate(tests, start=1)
              if not isinstance(test, dict) or test.get("passed") is not True]
    if failed:
        raise ValueError(f"Feedback calibration requires Boolean passed=true for all 6 tests; invalid tests: {failed}")

    run_record = json.loads((single_dir / "执行命令与环境.json").read_text(encoding="utf8"))
    if not run_record.get("runtime_env") or calibration.get("runtime_env") != run_record["runtime_env"]:
        raise ValueError("Archived single-run environment disagrees with the archived calibration")
    historical_environment = baseline["runtime_environment"]
    recorded_environment = run_record["runtime_env"]
    if (recorded_environment["python"] != historical_environment["python"]
            or recorded_environment["machine"] != historical_environment["machine"]
            or recorded_environment["pybullet"] != historical_environment["packages"]["pybullet"]):
        raise ValueError("Archived single-run environment disagrees with the historical environment freeze")
    single_res = json.loads((single_dir / "result.json").read_text(encoding="utf8"))
    c_audit = json.loads((single_dir / "C独立证据核对.json").read_text(encoding="utf8"))
    vid_audit = json.loads((single_dir / "视频核对.json").read_text(encoding="utf8"))
    s3_on = json.loads((STAGE3_DIR / "compensation_on/result.json").read_text(encoding="utf8"))
    if (single_res["success"] is not True or single_res["exit_code"] != 0 or run_record["exit_code"] != 0
            or c_audit["status"] != "PASS" or c_audit["completed_items"] != 1 or c_audit["source_hashes_match"] is not True
            or single_res["payload_config"] != "A-candidate" or single_res["grasp_offset_compensation"] is not True):
        raise ValueError("Archived single-run result or independent audit did not pass the Stage 4 configuration checks")

    # Compare Item 1 deterministic trajectory milestones against Stage 3 compensation_on Item 1
    s4_comp = [e for e in single_res["events"] if e["phase"] == "grasp_offset_compensation"][0]
    s3_comp = [e for e in s3_on["events"] if e["phase"] == "grasp_offset_compensation" and e["item"] == 1][0]
    comp_diff_m = float(np.linalg.norm(np.array(s4_comp["tcp_xy_correction_m"]) - np.array(s3_comp["tcp_xy_correction_m"])))
    item1_settle_diff_m = abs(single_res["item_results"][0]["position_error_m"] - s3_on["item_results"][0]["position_error_m"])

    raw_trace = single_dir / "joint_full_trace.csv"
    gz_trace = single_dir / "joint_full_trace.csv.gz"
    expected = baseline["single_run_trace"]
    if expected["rows"] != single_res["telemetry_rows"] or expected["rows"] != c_audit["telemetry_rows"]:
        raise ValueError("Archived row count disagrees with the single-run result or independent audit")
    trace = validate_trace(gz_trace, expected)
    if raw_trace.exists():
        validate_trace(raw_trace, expected)

    return {
        "verified_at_HK": datetime.datetime.now(HK).isoformat(),
        "archived_run_started_HK": run_record["started"],
        "archived_run_environment": recorded_environment,
        "calibration_passed_6_of_6": len(tests) == 6 and not failed,
        "calibration_json": str(cal_file.relative_to(ROOT)),
        "single_run_dir": str(single_dir.relative_to(ROOT)),
        "exit_code": single_res["exit_code"],
        "success": single_res["success"],
        "payload_config": single_res["payload_config"],
        "grasp_offset_compensation": single_res["grasp_offset_compensation"],
        "simulated_seconds": single_res["simulated_seconds"],
        "telemetry_rows_240Hz": single_res["telemetry_rows"],
        "video_frames_5fps": vid_audit["frames"],
        "moves_reached": len(single_res["moves"]),
        "planner_methods": c_audit["planner_methods"],
        "final_position_error_mm": c_audit["max_position_error_mm"],
        "final_orientation_error_deg": c_audit["max_orientation_error_deg"],
        "xy_compensation_applied_mm": c_audit["maximum_xy_compensation_mm"],
        "item1_compensation_vector_diff_vs_stage3_m": comp_diff_m,
        "item1_post_settle_error_diff_vs_stage3_m": item1_settle_diff_m,
        "source_hashes_match_frozen": c_audit["source_hashes_match"],
        "lossless_gzip_trace": {
            "compressed_path": str(gz_trace.relative_to(ROOT)),
            "compressed_bytes": gz_trace.stat().st_size,
            **trace,
            "baseline_json": str((REPRO_DIR / "历史环境与日志基准.json").relative_to(ROOT)),
            "baseline_sha256": ARCHIVED_BASELINE_SHA256,
        },
    }


def main():
    baseline_path = REPRO_DIR / "历史环境与日志基准.json"
    if sha256_file(baseline_path) != ARCHIVED_BASELINE_SHA256:
        raise ValueError("Historical environment and trace baseline SHA mismatch")
    baseline = json.loads(baseline_path.read_text(encoding="utf8"))
    repro = audit_reproduction(baseline)
    urdf_path = PROJECT / "PiPER_Load_URDF/piper_description/piper_description_pybullet.urdf"
    candidate_path = PROJECT / "A_结构设计与CAD/04_构件参数与文献/质量惯量_候选参数.json"
    candidate = json.loads(candidate_path.read_text(encoding="utf8"))
    decomp = compute_xy_z_decomposition()
    package_freeze = {
        "schema_version": 2,
        "created_HK": baseline["created_HK"],
        "regenerated_at_HK": repro["verified_at_HK"],
        "role": "Part B Stage 4 Finalized Control, Kinematics, Torque & Environment Freeze",
        "runtime_environment": baseline["runtime_environment"],
        "runtime_environment_source": {
            "path": str(baseline_path.relative_to(ROOT)),
            "sha256": ARCHIVED_BASELINE_SHA256,
            "note": "Historical 17 November freeze. Regeneration uses the recorded environment values.",
        },
        "robot_kinematics_and_urdf": {
            "urdf_path": str(urdf_path.relative_to(ROOT)),
            "urdf_sha256": sha256_file(urdf_path),
            "declared_tcp_offset_in_gripper_base_m": [0.0, 0.0, 0.1358],
            "gripper_command_mapping": "joint7 = +w/2, joint8 = -w/2, w in [0.0, 0.07] m",
            "joints": extract_urdf_chain(urdf_path),
            "loaded_inertia_note": "Robot loaded with Piper(self_collision=True) without URDF_USE_INERTIA_FROM_FILE; exact Bullet imported link principal inertias archived in 05_Project3_月面机器人装配/运行验证/B_第三阶段_2026-11-10/robot_loaded_dynamics.json",
        },
        "candidate_component_payload": {
            "component_version": candidate["component_version"],
            "source_json": str(candidate_path.relative_to(ROOT)),
            "source_sha256": sha256_file(candidate_path),
            "density_kg_m3": candidate["material_density_kg_m3"],
            "actual_CAD_volume_m3": candidate["actual_CAD_volume_m3"],
            "mass_kg": candidate["mass_kg"],
            "com_in_bottom_origin_frame_m": candidate["centre_of_mass_in_geometry_frame_m"],
            "inertia_diagonal_about_com_kg_m2": [
                candidate["inertia_about_COM_expressed_in_geometry_axes_kg_m2"][i][i] for i in range(3)
            ],
            "convex_collision_parts": 34,
            "collision_margin_m": 0.00005,
            "lateral_friction": 0.6,
            "restitution": 0.0,
            "material_signoff_status": "Candidate 2500 kg/m^3 uniform sintered EAC-1A simulant model; formal report adoption wording awaiting Part A sign-off",
        },
        "controller_and_simulation_parameters": {
            "lunar_gravity_m_s2": [0.0, 0.0, -1.62],
            "external_physics_dt_s": 1.0 / 240.0,
            "physics_substeps": 4,
            "internal_physics_dt_s": 1.0 / 960.0,
            "outer_control_dt_s": 4.0 / 240.0,
            "characteristic_length_L_m": 0.3,
            "ik_dls_damping_lambda": 0.015,
            "ik_joint_limit_margin_deg": 2.0,
            "ik_acceptance_residuals": {"position_m": 1e-5, "orientation_rad": 1e-4},
            "outer_dls_feedback": {
                "gain_Kp_KR": 3.0,
                "damping_lambda": 0.02,
                "linear_speed_cap_m_s": 0.04,
                "angular_speed_cap_rad_s": 0.3,
                "joint_rate_scale_cap_rad_s": 0.35,
                "reference_windup_clamp_rad": 0.03,
            },
            "inner_position_servo": {
                "mode": "POSITION_CONTROL",
                "positionGain": 0.15,
                "velocityGain": 1.0,
                "arm_maxVelocity_rad_s": 0.6,
                "arm_force_api_param": 100.0,
                "calibrated_last_substep_factor": 4,
            },
            "convergence_gate_60Hz": {
                "consecutive_samples": 15,
                "tcp_position_error_mm": 0.1,
                "tcp_orientation_error_deg": 0.1,
                "max_joint_speed_rad_s": 0.02,
            },
            "grasp_and_release": {
                "approach_open_width_m": 0.036,
                "close_target_width_m": 0.022,
                "closing_force_api_N": 1.0,
                "assisted_constraint": "JOINT_FIXED created only after bilateral positive normal-force core_contact; maxForce=30",
                "lower_tcp_height_above_target_z_m": {"layer1": 0.016, "layer2": 0.0145, "tray_pick": 0.014},
                "release_gate": "opening > 35.5 mm, no finger contact > 1e-4 N, |v| < 2 mm/s, |omega| < 0.02 rad/s for 5 consecutive 50 ms samples",
                "contact_breaking_relative_factor": 1e-5,
            },
            "grasp_offset_compensation": {
                "enabled_in_recommended_mode": True,
                "measured_after_phase": "lift (TCP Z = 0.082 m)",
                "state_source": "exact simulated TCP and reconstructed block bottom-center pose",
                "adjusted_phases": ["transfer", "lower"],
                "unadjusted_phases": ["approach", "descend", "lift", "retreat"],
                "max_xy_bound_m": 0.002,
            },
        },
        "xy_and_vertical_placement_error_decomposition": decomp,
        "stage4_cross_reproduction": repro,
        "explicit_modeling_limitations": [
            "Candidate homogeneous rigid-body density (2500 kg/m^3) is a literature-based simulation input, not sintered specimen testing or structural strength/airtightness certification.",
            "Carrying uses a contact-gated fixed constraint rather than pure Coulomb friction hold.",
            "Post-lift XY grasp-offset compensation reads exact simulation poses without camera/calibration noise or latency.",
            "Collision checking is discrete (joint/command grids + 240 Hz step observer) with explicit contact exemptions and penetration tolerances (0.1/0.2/0.5 mm).",
            "Calibrated motor torque (4x raw getJointStates motor field) represents the last-substep equivalent effort at 240 Hz external sampling, not all 960 Hz internal substep extrema or manufacturer rated hardware limits.",
            "Single-run deterministic pairing per condition supports conditional engineering comparison, not statistical significance.",
        ],
    }
    (OUT_DIR / "参数与环境定稿包.json").write_text(
        json.dumps(package_freeze, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
    )
    (REPRO_DIR / "第四阶段交叉复现与核对结果.json").write_text(
        json.dumps(repro, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
    )
    print("Stage 4 verification and freeze complete:", json.dumps(decomp, indent=2))
    print("Item 1 diff vs Stage 3 (m):", repro["item1_compensation_vector_diff_vs_stage3_m"], repro["item1_post_settle_error_diff_vs_stage3_m"])
    print(f"Archived feedback calibration: 6/6 passed. Verified raw trace SHA and {repro['telemetry_rows_240Hz']:,} rows.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, EOFError, KeyError, IndexError, TypeError) as exc:
        print(f"Stage 4 verification failed: {exc}", file=sys.stderr)
        sys.exit(1)
