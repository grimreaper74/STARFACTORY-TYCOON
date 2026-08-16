"""Offline result verifier/finalizer for validation-only panel Recovery_v002."""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import cairnwell_2040_panel_modules_recovery_v002 as recovery


PROJECT = recovery.PROJECT
BASELINE_TOOL = PROJECT / "Scripts/prepare_cairnwell_2040_panel_modules_v001_baseline.py"
BASELINE = PROJECT / "Scripts/cairnwell_2040_panel_modules_v001_import_baseline_v002.json"
PASS_STATUS = (
    "PASS__CAIRNWELL_2040_PANEL_MODULES_V001_RECOVERY_V002__"
    "DISTINCT_FRESH_READ_ONLY_RELOAD__11_MESHES__33_AUTHORED_LODS__"
    "EXACT_PERSISTED_RUNTIME_MATERIAL_DEPENDENCIES__11_PANEL_AND_11_RUNTIME_"
    "PACKAGE_HASHES_UNCHANGED"
)
SUMMARY_PASS = (
    "PASS__CAIRNWELL_2040_PANEL_MODULES_V001_RECOVERY_V002__"
    "GUARDED_VALIDATION_ONLY_OF_PRESERVED_V001_PACKAGES"
)
STEM = "fresh_process_validation_recovery_v002"
RECEIPT_KEYS = {
    "$schema", "generated_utc", "status", "process_id", "incident_v001_run_id",
    "asset_mutations", "project_maps_loaded_or_saved", "writes_authorized",
    "vehicle_model_id", "development_geometry_revisionable",
    "final_release_visual_lock_claimed", "engine_version", "editor_bootstrap_world",
    "contract_sha256", "panel_contract_sha256", "panel_baseline_v002_sha256",
    "incident_v001_files", "distinct_from_v001_importer_process", "source_before",
    "source_after", "protected_before", "protected_after", "prepared_lane_before",
    "prepared_lane_after", "runtime_before", "runtime_after",
    "asset_registry_cache_before", "asset_registry_cache_after",
    "legacy_asset_registry_cache_absence_before",
    "legacy_asset_registry_cache_absence_after", "exact_ten_incidental_files_before",
    "exact_ten_incidental_files_after", "panel_package_files_before_loads",
    "panel_package_files_after_loads", "asset_registry_packages_before",
    "asset_registry_packages_after", "assets", "mesh_count", "authored_lod_count",
    "package_count", "new_texture_count", "new_material_count",
    "persisted_runtime_material_dependencies_verified",
    "asset_registry_dependency_options", "all_panel_package_hashes_unchanged",
    "all_runtime_package_hashes_unchanged", "asset_mutation_count",
    "existing_incidental_file_content_mutation_count",
    "no_asset_registry_cache_write_command_line_verified",
    "read_only_startup_write_suppression", "ubt_startup_guard_environment", "failures",
}
CRC_KEYS = {
    "$schema", "generated_utc", "status", "completed_editor_process_id",
    "observed_exact_monitors", "unbound_crc_monitor_count", "kill_count",
    "natural_exit_only", "deadline_seconds", "wait_elapsed_milliseconds",
    "zero_process_stabilization_milliseconds", "deadline_exceeded",
    "crash_reporter_config_delta",
}
SUMMARY_KEYS = {
    "$schema", "generated_utc", "status", "run_root", "contract_sha256",
    "incident_v001_run_id", "validator_process", "validation_receipt",
    "normal_crc_monitor_wait", "post_exit_panel_package_files",
    "post_exit_incidental_file_delta", "crash_reporter_config_delta",
    "runtime_package_sha256", "content_write_count",
    "content_move_delete_reimport_count", "editor_process_count",
    "no_build_tool_invoked", "environment_restoration_verified", "error",
}


class VerifyError(RuntimeError):
    """Fail-closed offline verification error."""


def load_baseline_tool():
    spec = importlib.util.spec_from_file_location("panel_baseline_recovery_result", BASELINE_TOOL)
    if spec is None or spec.loader is None:
        raise VerifyError("cannot load panel baseline verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def checked_root(value: Path) -> Path:
    root = value.resolve()
    if root.parent != recovery.RECOVERY_AUDIT_ROOT.resolve() or not root.is_dir():
        raise VerifyError("Recovery_v002 result root is absent/not a direct child")
    return root


def exact_int(value, label: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise VerifyError(f"{label} must be exact integer >= {minimum}")
    return value


def exact_files(root: Path, names: set[str], label: str) -> None:
    actual = {path.name for path in root.iterdir() if path.is_file()}
    if actual != names or any(path.is_dir() for path in root.iterdir()):
        raise VerifyError(f"{label} exact file closure drift: {sorted(actual)}")


def inventory_identity(snapshot: dict) -> dict:
    return {
        "file_count": snapshot["file_count"],
        "inventory_sha256": snapshot["inventory_sha256"],
    }


def verify_preflight() -> None:
    contract, _ = recovery.load_contract()
    recovery.verify_preflight_topology()
    recovery.verify_incident(contract)
    recovery.verify_packages(contract)
    recovery.verify_incidental_content(contract)
    recovery.verify_crash_config_preflight(contract)
    load_baseline_tool().verify_post_import_immutable()
    print("PASS__CAIRNWELL_2040_PANEL_MODULES_RECOVERY_V002_PREFLIGHT_REVERIFIED")


def verify_result(root_value: Path, allow_summary: bool = False) -> dict:
    root = checked_root(root_value)
    recovery.verify_result_topology(root)
    wanted = {
        recovery.RECEIPT,
        f"{STEM}.log",
        f"{STEM}.stdout.log",
        f"{STEM}.stderr.log",
        recovery.CRC_EVIDENCE,
    }
    if allow_summary:
        wanted.add(recovery.SUMMARY)
    exact_files(root, wanted, "Recovery_v002 validation result")
    contract, contract_digest = recovery.load_contract()
    recovery.verify_incident(contract)
    packages = recovery.verify_packages(contract)
    baseline_tool = load_baseline_tool()
    baseline_tool.verify_post_import_immutable()
    baseline = recovery.strict_json(BASELINE, "panel baseline v002")
    receipt_path = root / recovery.RECEIPT
    receipt = recovery.strict_json(receipt_path, "Recovery_v002 validation receipt")
    crc = recovery.strict_json(root / recovery.CRC_EVIDENCE, "CRC monitor wait evidence")
    process_id = exact_int(receipt.get("process_id"), "validator process_id", 1)
    wait_elapsed = exact_int(
        crc.get("wait_elapsed_milliseconds"), "CRC wait_elapsed_milliseconds", 1000
    )
    if (
        set(receipt) != RECEIPT_KEYS
        or receipt.get("$schema")
        != (
            "lineboss/audit/cairnwell-2040-panel-modules-v001/"
            "recovery-v002/fresh-process-validation/v2"
        )
        or receipt.get("status") != PASS_STATUS
        or receipt.get("contract_sha256") != contract_digest
        or receipt.get("panel_contract_sha256")
        != contract["panel_contract"]["payload"]["sha256"]
        or receipt.get("panel_baseline_v002_sha256")
        != contract["panel_baseline_v002"]["payload"]["sha256"]
        or receipt.get("incident_v001_run_id") != "20260815T182842Z-0205ac3e"
        or receipt.get("incident_v001_files") != contract["incident_v001"]["files"]
        or receipt.get("writes_authorized") != [
            str(root / recovery.RECEIPT), str(root / recovery.FAILURE)
        ]
        or receipt.get("vehicle_model_id") != "CAIRNWELL_2040"
        or receipt.get("development_geometry_revisionable") is not True
        or receipt.get("final_release_visual_lock_claimed") is not False
        or not str(receipt.get("engine_version", "")).startswith("5.8")
        or receipt.get("distinct_from_v001_importer_process") is not True
        or process_id == contract["incident_v001"]["importer_process_id"]
        or receipt.get("mesh_count") != 11
        or receipt.get("authored_lod_count") != 33
        or receipt.get("package_count") != 11
        or receipt.get("new_texture_count") != 0
        or receipt.get("new_material_count") != 0
        or receipt.get("asset_mutation_count") != 0
        or receipt.get("asset_mutations") != []
        or receipt.get("project_maps_loaded_or_saved") != []
        or receipt.get("persisted_runtime_material_dependencies_verified") is not True
        or receipt.get("asset_registry_dependency_options") != {
            "include_soft_package_references": True,
            "include_hard_package_references": True,
            "include_game_package_references": True,
            "include_editor_only_package_references": False,
            "include_searchable_names": False,
            "include_soft_management_references": False,
            "include_hard_management_references": False,
        }
        or receipt.get("all_panel_package_hashes_unchanged") is not True
        or receipt.get("all_runtime_package_hashes_unchanged") is not True
        or receipt.get("panel_package_files_before_loads") != packages
        or receipt.get("panel_package_files_after_loads") != packages
        or receipt.get("source_before") != contract["baseline_authority"]["source"]
        or receipt.get("source_after") != contract["baseline_authority"]["source"]
        or receipt.get("protected_before") != contract["baseline_authority"]["protected"]
        or receipt.get("protected_after") != contract["baseline_authority"]["protected"]
        or receipt.get("prepared_lane_before") != contract["baseline_authority"]["lane"]
        or receipt.get("prepared_lane_after") != contract["baseline_authority"]["lane"]
        or receipt.get("runtime_before") != contract["baseline_authority"]["runtime"]
        or receipt.get("runtime_after") != contract["baseline_authority"]["runtime"]
        or receipt.get("asset_registry_cache_before")
        != contract["baseline_authority"]["asset_registry_cache"]
        or receipt.get("asset_registry_cache_after")
        != contract["baseline_authority"]["asset_registry_cache"]
        or receipt.get("legacy_asset_registry_cache_absence_before")
        != contract["baseline_authority"]["legacy_asset_registry_cache_absence"]
        or receipt.get("legacy_asset_registry_cache_absence_after")
        != contract["baseline_authority"]["legacy_asset_registry_cache_absence"]
        or receipt.get("existing_incidental_file_content_mutation_count") != 0
        or receipt.get("no_asset_registry_cache_write_command_line_verified") is not True
        or receipt.get("read_only_startup_write_suppression") != {
            "required_switches": [
                *contract["recovery"]["required_editor_command_line_tokens"],
                contract["recovery"][
                    "uncontrolled_changelist_write_suppression_override"
                ],
                contract["recovery"]["python_stub_write_suppression_override"],
                str(PROJECT / "Scripts/validate_cairnwell_2040_panel_modules_recovery_v002.py"),
                str(root / "fresh_process_validation_recovery_v002.log"),
            ],
            "all_required_switches_observed": True,
            "python_dont_write_bytecode_environment": {
                "name": "PYTHONDONTWRITEBYTECODE",
                "observed_value": "1",
            },
        }
        or receipt.get("ubt_startup_guard_environment", {}).get("observed_value") != "1"
        or receipt.get("editor_bootstrap_world") != "/Engine/Maps/Entry.Entry"
        or receipt.get("failures") != []
    ):
        raise VerifyError("Recovery_v002 receipt identity/package/immutable/safety drift")
    expected_incidental_content = recovery.incidental_content_rows(
        contract["original_v001_incidental_project_writes"]
    )
    for label in (
        "exact_ten_incidental_files_before", "exact_ten_incidental_files_after"
    ):
        snapshot = receipt.get(label)
        if (
            not isinstance(snapshot, dict)
            or snapshot.get("file_count") != 10
            or recovery.incidental_content_rows(snapshot) != expected_incidental_content
        ):
            raise VerifyError(f"Recovery_v002 {label} path/byte/hash drift")
    expected_registry = set(baseline["destination"]["expected_package_paths"])
    if (
        set(receipt.get("asset_registry_packages_before", [])) != expected_registry
        or set(receipt.get("asset_registry_packages_after", [])) != expected_registry
    ):
        raise VerifyError("Recovery_v002 exact asset-registry closure drift")
    assets = receipt.get("assets", {})
    panels = assets.get("panels", {}) if isinstance(assets, dict) else {}
    if set(panels) != set(baseline["modules"]) or assets.get("panel_count") != 11:
        raise VerifyError("Recovery_v002 measured panel closure drift")
    for panel_id, panel in panels.items():
        expected_material = baseline["modules"][panel_id]["material_bindings"]["default"].split(
            ".", 1
        )[0]
        if (
            panel.get("lod_count") != 3
            or panel.get("strict_monotonic_triangles") is not True
            or panel.get("persisted_dependency_check_required") is not True
            or panel.get("persisted_relevant_dependencies") != [expected_material]
            or panel.get("nanite_enabled") is not False
            or panel.get("has_navigation_data") is not False
            or panel.get("simple_collision_count") != 0
            or panel.get("convex_collision_count") != 0
        ):
            raise VerifyError("Recovery_v002 panel geometry/dependency drift: " + panel_id)
    if (
        set(crc) != CRC_KEYS
        or crc.get("$schema")
        != (
            "lineboss/audit/cairnwell-2040-panel-modules-v001/"
            "recovery-v002/normal-crc-monitor-wait/v2"
        )
        or crc.get("status")
        != "PASS__ONLY_EXACT_COMPLETED_EDITOR_BOUND_CRC_MONITORS_EXITED_NATURALLY"
        or crc.get("completed_editor_process_id") != process_id
        or crc.get("unbound_crc_monitor_count") != 0
        or crc.get("kill_count") != 0
        or crc.get("natural_exit_only") is not True
        or crc.get("deadline_seconds") != 15
        or crc.get("zero_process_stabilization_milliseconds") != 1000
        or wait_elapsed > 15000
        or crc.get("deadline_exceeded") is not False
    ):
        raise VerifyError("Recovery_v002 CRC wait evidence drift")
    observed = crc.get("observed_exact_monitors")
    if not isinstance(observed, list):
        raise VerifyError("Recovery_v002 CRC observed-monitor list missing")
    for item in observed:
        if (
            not isinstance(item, dict)
            or set(item) != {
                "process_name", "process_id", "parent_process_id",
                "creation_date_utc", "command_line", "monitor_process_id",
                "command_line_exact_monitor_binding",
            }
            or type(item.get("process_id")) is not int
            or item.get("process_id") <= 0
            or item.get("monitor_process_id") != process_id
            or item.get("command_line_exact_monitor_binding") is not True
            or item.get("process_name") not in (
                "CrashReportClient.exe", "CrashReportClientEditor.exe"
            )
            or type(item.get("parent_process_id")) is not int
            or not isinstance(item.get("creation_date_utc"), str)
            or not item.get("creation_date_utc")
            or not isinstance(item.get("command_line"), str)
            or f"-MONITOR={process_id}" not in item.get("command_line", "")
        ):
            raise VerifyError("Recovery_v002 observed CRC monitor binding drift")
    crash_delta = recovery.verify_crash_config_post(contract)
    if crc.get("crash_reporter_config_delta") != crash_delta:
        raise VerifyError("Recovery_v002 CRC config delta evidence drift")
    logs = baseline_tool.process_log_evidence(
        root,
        STEM,
        "LINE_BOSS_CAIRNWELL_2040_PANEL_MODULES_RECOVERY_V002_VALIDATION_PASS",
    )
    incidental_delta = recovery.incidental_post_delta(contract)
    return {
        "contract": contract,
        "contract_sha256": contract_digest,
        "receipt": receipt,
        "receipt_file": recovery.file_row(receipt_path),
        "crc": crc,
        "crc_file": recovery.file_row(root / recovery.CRC_EVIDENCE),
        "crash_config_delta": crash_delta,
        "incidental_post_delta": incidental_delta,
        "logs": logs,
        "packages": packages,
    }


def finalize(root_value: Path, validator_exit_code: int) -> None:
    root = checked_root(root_value)
    if validator_exit_code != 0:
        raise VerifyError("refusing PASS summary for nonzero validator exit")
    result = verify_result(root, allow_summary=False)
    summary_path = root / recovery.SUMMARY
    if summary_path.exists():
        raise VerifyError("refusing to overwrite Recovery_v002 summary")
    summary = {
        "$schema": (
            "lineboss/audit/cairnwell-2040-panel-modules-v001/"
            "recovery-v002/validation-only-lane-summary/v2"
        ),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": SUMMARY_PASS,
        "run_root": str(root),
        "contract_sha256": result["contract_sha256"],
        "incident_v001_run_id": "20260815T182842Z-0205ac3e",
        "validator_process": {
            "process_id": result["receipt"]["process_id"],
            "exit_code": 0,
            **result["logs"],
        },
        "validation_receipt": result["receipt_file"],
        "normal_crc_monitor_wait": result["crc_file"],
        "post_exit_panel_package_files": result["packages"],
        "post_exit_incidental_file_delta": result["incidental_post_delta"],
        "crash_reporter_config_delta": result["crash_config_delta"],
        "runtime_package_sha256": result["contract"]["baseline_authority"]["runtime"][
            "package_sha256"
        ],
        "content_write_count": 0,
        "content_move_delete_reimport_count": 0,
        "editor_process_count": 1,
        "no_build_tool_invoked": True,
        "environment_restoration_verified": True,
        "error": None,
    }
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("PASS__CAIRNWELL_2040_PANEL_MODULES_RECOVERY_V002_SUMMARY_FINALIZED")
    print(recovery.sha256(summary_path))


def verify_final(root_value: Path) -> None:
    root = checked_root(root_value)
    result = verify_result(root, allow_summary=True)
    summary = recovery.strict_json(root / recovery.SUMMARY, "Recovery_v002 summary")
    if (
        set(summary) != SUMMARY_KEYS
        or summary.get("$schema")
        != (
            "lineboss/audit/cairnwell-2040-panel-modules-v001/"
            "recovery-v002/validation-only-lane-summary/v2"
        )
        or summary.get("status") != SUMMARY_PASS
        or summary.get("run_root") != str(root)
        or summary.get("incident_v001_run_id") != "20260815T182842Z-0205ac3e"
        or summary.get("contract_sha256") != result["contract_sha256"]
        or summary.get("validation_receipt") != result["receipt_file"]
        or summary.get("normal_crc_monitor_wait") != result["crc_file"]
        or summary.get("post_exit_panel_package_files") != result["packages"]
        or summary.get("post_exit_incidental_file_delta")
        != result["incidental_post_delta"]
        or summary.get("crash_reporter_config_delta")
        != result["crash_config_delta"]
        or summary.get("runtime_package_sha256")
        != result["contract"]["baseline_authority"]["runtime"]["package_sha256"]
        or summary.get("content_write_count") != 0
        or summary.get("content_move_delete_reimport_count") != 0
        or summary.get("editor_process_count") != 1
        or summary.get("no_build_tool_invoked") is not True
        or summary.get("environment_restoration_verified") is not True
        or summary.get("error") is not None
    ):
        raise VerifyError("Recovery_v002 final summary drift")
    validator_process = summary.get("validator_process")
    expected_validator = {
        "process_id": result["receipt"]["process_id"],
        "exit_code": 0,
        **result["logs"],
    }
    if validator_process != expected_validator:
        raise VerifyError("Recovery_v002 final validator-process/log evidence drift")
    print("PASS__CAIRNWELL_2040_PANEL_MODULES_RECOVERY_V002_FINAL_SIX_FILE_REVERIFIED")
    print(recovery.sha256(root / recovery.SUMMARY))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-result", type=Path)
    parser.add_argument("--verify-preflight", action="store_true")
    parser.add_argument("--finalize", type=Path)
    parser.add_argument("--verify-final", type=Path)
    parser.add_argument("--validator-exit-code", type=int, default=-1)
    args = parser.parse_args()
    if args.verify_preflight:
        verify_preflight()
    elif args.verify_final is not None:
        verify_final(args.verify_final)
    elif args.finalize is not None:
        finalize(args.finalize, args.validator_exit_code)
    elif args.verify_result is not None:
        verify_result(args.verify_result)
        print("PASS__CAIRNWELL_2040_PANEL_MODULES_RECOVERY_V002_RESULT_REVERIFIED")
    else:
        raise VerifyError("one exact Recovery_v002 verification mode is required")


if __name__ == "__main__":
    main()
