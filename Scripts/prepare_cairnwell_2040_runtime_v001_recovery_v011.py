"""Offline incident contract for guarded Cairnwell v011 validation-only recovery."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCRIPTS = PROJECT / "Scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import prepare_cairnwell_2040_runtime_v001_recovery_v010 as prior


BASE = prior.BASE
RecoveryError = prior.RecoveryError
OUTPUT = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v011_contract.json"
OUTPUT_SHA = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v011_contract.sha256"
V010_CONTRACT = prior.OUTPUT
V010_SIDECAR = prior.OUTPUT_SHA
V010_CONTRACT_SHA256 = (
    "CBE1DA417B4009F188E9D35D13402AEA1C7D0CAB9A3EED041ED57F20DA4ADF45"
)
V010_CONTRACT_BYTES = 155045
V010_SIDECAR_SHA256 = (
    "0FAA9591022AB275E88BE0DFBDD201BC39FA2BDB69200AA4C345DFBED5ED1C5A"
)
V010_SIDECAR_BYTES = 122
V010_SIDECAR_TEXT = f"{V010_CONTRACT_SHA256}  {V010_CONTRACT.name}\n"
V009_QUARANTINE_RECEIPT_BYTES = 8403
RECOVERY_AUDIT_ROOT = PROJECT / (
    "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "UnrealImportLane_v001/Recovery_v011"
)
ACK_TOKEN = "FREEZE_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V011_ONCE"
RUN_ACK_TOKEN = "VALIDATE_CAIRNWELL_2040_RUNTIME_V001_V009_IMPORT_V011_ONCE"
STATUS = (
    "FROZEN__CAIRNWELL_2040_RUNTIME_V001_INCIDENT_CHAINED_RECOVERY_V011__"
    "READY_FOR_ONE_SHOT_VALIDATION_ONLY_OF_V009_PASS_IMPORT"
)
V011_ADDITIONS = {
    "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V011.md",
    "Scripts/prepare_cairnwell_2040_runtime_v001_recovery_v011.py",
    "Scripts/validate_cairnwell_2040_runtime_recovery_v011.py",
    "Scripts/run_cairnwell_2040_runtime_validation_recovery_v011.ps1",
    "Scripts/tests/test_cairnwell_2040_runtime_validation_recovery_v011.py",
    "Scripts/cairnwell_2040_runtime_v001_recovery_v010_contract.json",
    "Scripts/cairnwell_2040_runtime_v001_recovery_v010_contract.sha256",
}
VALIDATION_PREFIX = "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v011/"
VALIDATION_RECEIPT = "fresh_process_validation_receipt_recovery_v011.json"
VALIDATION_FAILURE = "fresh_process_validation_failure_recovery_v011.json"
SUMMARY_NAME = "lane_summary_recovery_v011.json"
VALIDATOR_LOGS = [
    "fresh_process_validation_recovery_v011.log",
    "fresh_process_validation_recovery_v011.stdout.log",
    "fresh_process_validation_recovery_v011.stderr.log",
]
VALIDATION_PASS = (
    "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V011_DISTINCT_FRESH_PROCESS__"
    "READ_ONLY_RELOAD_OF_V009_PASS_IMPORT__11_PACKAGE_HASHES_UNCHANGED"
)
SUMMARY_PASS = (
    "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V011_GUARDED_"
    "VALIDATION_ONLY_OF_V009_PASS_IMPORT"
)
PRE_VALIDATION_PASS = (
    "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V011_PRE_VALIDATION_REVERIFIED"
)
POST_VALIDATION_PASS = (
    "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V011_POST_VALIDATION_REVERIFIED"
)
FINAL_PASS = (
    "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V011_FINAL_FIVE_FILE_REVERIFIED"
)
ENGINE_VERSION_PREFIX = "5.8."


def object_hash(value: object) -> str:
    return prior.object_hash(value)


def strict_json_text(text: str) -> object:
    return prior.strict_json_text(text)


def strict_json_file(path: Path) -> object:
    return prior.strict_json_file(path)


def serialized_payload(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def payload_file_sha256(payload: dict) -> str:
    return hashlib.sha256(serialized_payload(payload)).hexdigest().upper()


def exact_iso_utc(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise RecoveryError(label + " timestamp type drift")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise RecoveryError(label + " timestamp is not ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise RecoveryError(label + " timestamp is not exact UTC")
    return value


def exact_v010_pair() -> tuple[dict, dict, dict]:
    if (not V010_CONTRACT.is_file()
            or V010_CONTRACT.stat().st_size != V010_CONTRACT_BYTES
            or BASE.sha256(V010_CONTRACT) != V010_CONTRACT_SHA256):
        raise RecoveryError("stale/unexecuted v010 contract bytes drift")
    if (not V010_SIDECAR.is_file()
            or V010_SIDECAR.stat().st_size != V010_SIDECAR_BYTES
            or BASE.sha256(V010_SIDECAR) != V010_SIDECAR_SHA256
            or V010_SIDECAR.read_text(encoding="ascii") != V010_SIDECAR_TEXT):
        raise RecoveryError("stale/unexecuted v010 sidecar bytes/text drift")
    payload, state = prior.load_frozen()
    if payload.get("$schema") != (
            "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v10"):
        raise RecoveryError("stale/unexecuted v010 contract schema drift")
    if prior.RECOVERY_AUDIT_ROOT.exists():
        raise RecoveryError("Recovery_v010 must remain absent/unexecuted")
    return payload, state, {
        "classification": (
            "V010_OFFLINE_CONTRACT_CUT_AFTER_INITIAL_GO__LATE_INDEPENDENT_AUDIT_"
            "FOUND_UNDERCONSTRAINED_FINAL_RECEIPT_AND_SUMMARY__UNEXECUTED_"
            "SUPERSEDED_BY_V011"
        ),
        "contract": BASE.file_row(V010_CONTRACT),
        "sidecar": BASE.file_row(V010_SIDECAR),
        "contract_sha256": V010_CONTRACT_SHA256,
        "sidecar_sha256": V010_SIDECAR_SHA256,
        "recovery_v010_result_root": BASE.relative(prior.RECOVERY_AUDIT_ROOT),
        "recovery_v010_result_root_absent": True,
        "unreal_or_ubt_was_launched_by_v010_freeze": False,
        "content_was_mutated_by_v010_freeze": False,
        "late_audit_findings": [
            "FINAL_SUMMARY_IDENTITY_FIELDS_WERE_NOT_ALL_EXACTLY_BOUND",
            "FRESH_RECEIPT_ORIGINAL_AND_INCIDENT_CHRONOLOGY_FIELDS_WERE_NOT_ALL_EXACTLY_BOUND",
            "TAMPER_REGRESSIONS_FOR_MISSING_ACK_AND_WRONG_RECEIPT_PATH_WERE_ABSENT",
        ],
    }


def v011_lane_snapshot(v010: dict) -> dict:
    paths = {row["path"] for row in v010["lane"]["files"]} | V011_ADDITIONS
    snapshot = BASE.inventory([PROJECT / path for path in paths])
    if (snapshot["file_count"] != 55
            or {row["path"] for row in snapshot["files"]} != paths):
        raise RecoveryError("v011 prepared-lane exact 55-file path closure drift")
    return snapshot


def result_topology() -> dict:
    return {
        "audit_root": BASE.relative(RECOVERY_AUDIT_ROOT),
        "run_root_pattern": BASE.relative(RECOVERY_AUDIT_ROOT) + "/<UTC>-<GUID8>",
        "validation": {
            "receipt_filename": VALIDATION_RECEIPT,
            "failure_filename": VALIDATION_FAILURE,
            "$schema": VALIDATION_PREFIX + "fresh-process-validation/v11",
            "pass_status": VALIDATION_PASS,
            "package_hash_fields": [
                "package_sha256_before_loads", "package_sha256_after_loads"],
        },
        "summary": {
            "filename": SUMMARY_NAME,
            "$schema": VALIDATION_PREFIX + "validation-only-lane-summary/v11",
            "pass_status": SUMMARY_PASS,
            "package_hash_field": "post_exit_package_sha256",
        },
        "validator_logs": list(VALIDATOR_LOGS),
        "unreal_process_count": 1,
        "import_process_count": 0,
    }


def authority_state() -> dict:
    v010, state, stale = exact_v010_pair()
    lane = v011_lane_snapshot(v010)
    return {**state, "v010": v010, "stale_v010": stale, "v011_lane": lane}


def candidate_generated_utc(state: dict) -> str:
    latest = max(int(row["mtime_ns"]) for row in state["v011_lane"]["files"])
    return datetime.fromtimestamp(
        latest / 1_000_000_000, tz=timezone.utc).isoformat()


def build_candidate_payload(state: dict, generated_utc: str) -> dict:
    v010 = state["v010"]
    stale = copy.deepcopy(state["stale_v010"])
    stale["binding_sha256"] = object_hash(stale)
    return {
        "$schema": "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v11",
        "status": STATUS,
        "generated_utc": generated_utc,
        "acknowledgement": RUN_ACK_TOKEN,
        "project_root": str(PROJECT),
        "original_authorities": copy.deepcopy(v010["original_authorities"]),
        "approved_source": copy.deepcopy(v010["approved_source"]),
        "protected_project": copy.deepcopy(v010["protected_project"]),
        "incident_chain": copy.deepcopy(v010["incident_chain"]),
        "stale_preliminary_v007": copy.deepcopy(v010["stale_preliminary_v007"]),
        "stale_preliminary_v008": copy.deepcopy(v010["stale_preliminary_v008"]),
        "exact_prior_all_file_closures": copy.deepcopy(
            v010["exact_prior_all_file_closures"]),
        "prior_quarantines": copy.deepcopy(v010["prior_quarantines"]),
        "partial_packages": copy.deepcopy(v010["partial_packages"]),
        "slot_normalization": copy.deepcopy(v010["slot_normalization"]),
        "runtime_uv_sanitization": copy.deepcopy(v010["runtime_uv_sanitization"]),
        "runtime_bounds_coordinate_conversion": copy.deepcopy(
            v010["runtime_bounds_coordinate_conversion"]),
        "exact_ue_enum_validation": copy.deepcopy(v010["exact_ue_enum_validation"]),
        "material_input_name_canonicalization": copy.deepcopy(
            v010["material_input_name_canonicalization"]),
        "completed_v009_import": copy.deepcopy(v010["completed_v009_import"]),
        "stale_unexecuted_v010": stale,
        "ubt_startup_suppression": copy.deepcopy(v010["ubt_startup_suppression"]),
        "late_audit_corrections": {
            "final_summary_exact_identity_binding_required": True,
            "fresh_receipt_exact_chronology_binding_required": True,
            "strict_exact_top_level_key_sets_required": True,
            "timestamp_type_iso_timezone_validation_required": True,
            "tamper_regressions": [
                "MISSING_SUMMARY_ACKNOWLEDGEMENT_MUST_FAIL",
                "WRONG_SUMMARY_VALIDATION_RECEIPT_PATH_MUST_FAIL",
                "DRIFTED_RECEIPT_WRAPPER_INCIDENT_BINDING_MUST_FAIL",
            ],
        },
        "visual_revision_policy": {
            "game_build_integration_status": (
                "PROVISIONAL_GAME_BUILD__REVISIONABLE_BEFORE_FINAL_RELEASE"),
            "runtime_asset_identity_decoupled_from_visual_geometry_revision": True,
            "current_package_validation_does_not_claim_final_release_visual_lock": True,
            "future_geometry_replacement_requires_a_new_explicit_authority_revision": True,
        },
        "lane": copy.deepcopy(state["v011_lane"]),
        "result_topology": result_topology(),
        "policy": {
            **copy.deepcopy(v010["policy"]),
            "unreal_launch_authorized_by_freeze": False,
            "validation_only_recovery": True,
            "existing_v009_packages_are_immutable": True,
            "current_visual_geometry_is_provisional_and_revisionable": True,
            "final_release_visual_lock_claimed": False,
            "v010_pair_is_immutable_stale_unexecuted_evidence": True,
            "v010_execution_authorized": False,
            "quarantine_move_authorized": False,
            "delete_copy_import_reimport_save_authorized": False,
            "importer_process_authorized": False,
            "exactly_one_read_only_validator_process_required": True,
            "powershell_5_1_compatible_runner_required": True,
            "powershell_full_v009_or_v011_receipt_parse_forbidden": True,
            "python_exact_empty_key_receipt_validation_required": True,
            "exact_final_summary_and_receipt_key_sets_required": True,
            "ubt_validate_platforms_must_be_suppressed": True,
            "ubt_log_tokens_are_fatal": True,
            "post_exit_all_file_and_package_hash_closure_required": True,
            "no_write_full_candidate_payload_preflight_required": True,
        },
    }


def exact_v011_run_root(raw: str, require_exists: bool = True) -> Path:
    path = Path(raw).resolve()
    if (path.parent != RECOVERY_AUDIT_ROOT.resolve()
            or not re.fullmatch(r"\d{8}T\d{6}Z-[0-9a-f]{8}", path.name)
            or (require_exists and not path.is_dir())):
        raise RecoveryError("v011 run root identity/path drift: " + str(path))
    return path


def expected_lane_identity(contract: dict) -> dict:
    return {
        "file_count": contract["lane"]["file_count"],
        "inventory_sha256": contract["lane"]["inventory_sha256"],
    }


def receipt_fixture(
        contract: dict, state: dict, run_root: Path, validator_pid: int,
        generated_utc: str = "2026-08-15T15:00:00+00:00",
        engine_version: str = "5.8.0-test") -> dict:
    completed = contract["completed_v009_import"]
    receipt = run_root / VALIDATION_RECEIPT
    failure = run_root / VALIDATION_FAILURE
    return {
        "$schema": result_topology()["validation"]["$schema"],
        "generated_utc": generated_utc,
        "process_id": validator_pid,
        "destination_namespace": (
            "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/"
            "Cairnwell2040Runtime_v001"),
        "asset_mutations": [],
        "editor_bootstrap_world": "/Engine/Maps/Entry.Entry",
        "project_maps_loaded_or_saved": [],
        "writes_authorized": [str(receipt), str(failure)],
        "status": VALIDATION_PASS,
        "engine_version": engine_version,
        "import_process_id": 36612,
        "validator_process_id": validator_pid,
        "distinct_process_verified": True,
        "contract_sha256": state["contract_digest"],
        "baseline_sha256": state["baseline_digest"],
        "recovery_contract_sha256": payload_file_sha256(contract),
        "v010_recovery_contract_sha256": V010_CONTRACT_SHA256,
        "v009_recovery_contract_sha256": prior.V009_CONTRACT_SHA256,
        "v009_import_receipt_sha256": prior.V009_IMPORT_RECEIPT_SHA256,
        "v009_wrapper_failure_summary_sha256": prior.V009_SUMMARY_SHA256,
        "v009_quarantine_receipt_sha256": prior.V009_QUARANTINE_RECEIPT_SHA256,
        "v009_wrapper_failure_classification": completed["classification"],
        "v009_wrapper_incident_binding_sha256": completed["binding_sha256"],
        "incident_chain_sha256": contract["incident_chain"]["binding_sha256"],
        "quarantine_receipt": {
            "path": BASE.relative(prior.V009_RUN / "quarantine_receipt_v009.json"),
            "bytes": V009_QUARANTINE_RECEIPT_BYTES,
            "sha256": prior.V009_QUARANTINE_RECEIPT_SHA256,
            "status": state["quarantined"]["status"],
        },
        "source_before": copy.deepcopy(completed["source_snapshot"]),
        "source_after": copy.deepcopy(completed["source_snapshot"]),
        "protected_before": copy.deepcopy(completed["protected_snapshot"]),
        "protected_after": copy.deepcopy(completed["protected_snapshot"]),
        "prepared_lane_before": expected_lane_identity(contract),
        "prepared_lane_after": expected_lane_identity(contract),
        "package_sha256_before_loads": copy.deepcopy(completed["package_sha256"]),
        "package_sha256_after_loads": copy.deepcopy(completed["package_sha256"]),
        "namespace_before": copy.deepcopy(completed["namespace_disk_files"]),
        "namespace_after": copy.deepcopy(completed["namespace_disk_files"]),
        "asset_registry_packages_before": copy.deepcopy(
            completed["asset_registry_packages"]),
        "asset_registry_packages_after": copy.deepcopy(
            completed["asset_registry_packages"]),
        "assets": prior.expected_fresh_assets(state["imported"]),
        "mesh_count": 4,
        "authored_lod_count": 12,
        "texture_count": 3,
        "material_count": 4,
        "package_count": 11,
        "all_package_hashes_unchanged": True,
        "persisted_asset_registry_dependency_closure_verified": True,
        "asset_mutation_count": 0,
        "import_or_reimport_process_count": 0,
        "ubt_startup_guard_environment": {
            "name": "UE_SKIP_UBT_SDK_SETUP",
            "required_value": "1",
            "observed_value": "1",
        },
        "failures": [],
    }


def validate_v011_receipt(
        payload: dict, contract: dict, state: dict, run_root: Path) -> None:
    if prior.empty_key_paths(payload) != [prior.V009_EMPTY_KEY_PATH]:
        raise RecoveryError("v011 validation receipt empty-key path closure drift")
    exact_iso_utc(payload.get("generated_utc"), "v011 receipt generated_utc")
    engine_version = payload.get("engine_version")
    if not isinstance(engine_version, str) or not engine_version.startswith(
            ENGINE_VERSION_PREFIX):
        raise RecoveryError("v011 receipt engine version is not exact UE 5.8 authority")
    validator_pid = payload.get("validator_process_id")
    if (type(validator_pid) is not int or validator_pid <= 0
            or validator_pid == 36612
            or payload.get("process_id") != validator_pid):
        raise RecoveryError("v011 validator/import process identity drift")
    exact_receipt_integers = {
        "process_id": validator_pid,
        "import_process_id": 36612,
        "validator_process_id": validator_pid,
        "mesh_count": 4,
        "authored_lod_count": 12,
        "texture_count": 3,
        "material_count": 4,
        "package_count": 11,
        "asset_mutation_count": 0,
        "import_or_reimport_process_count": 0,
    }
    if any(type(payload.get(key)) is not int or payload[key] != value
           for key, value in exact_receipt_integers.items()):
        raise RecoveryError("v011 receipt exact integer field/type drift")
    expected = receipt_fixture(
        contract, state, run_root, validator_pid,
        payload["generated_utc"], engine_version)
    if object_hash(payload) != object_hash(expected):
        raise RecoveryError("v011 fresh validation receipt exact chronology/content drift")


def process_fixture(
        process_id: int, log_sha256: str, stdout_sha256: str,
        stderr_sha256: str, attempts: tuple[int, int, int] = (1, 1, 1)) -> dict:
    return {
        "process_id": process_id,
        "exit_code": 0,
        "fatal_or_build_tool_log_patterns": [],
        "log_sha256": log_sha256,
        "stdout_sha256": stdout_sha256,
        "stderr_sha256": stderr_sha256,
        "redirected_log_read_open_retry": {
            "log_attempts": attempts[0],
            "stdout_attempts": attempts[1],
            "stderr_attempts": attempts[2],
            "bounded_timeout_milliseconds": 15000,
        },
    }


def summary_fixture(
        contract: dict, state: dict, run_root: Path, receipt: dict,
        receipt_sha256: str, process: dict,
        generated_utc: str = "2026-08-15T15:01:00+00:00") -> dict:
    recovery_sha = payload_file_sha256(contract)
    return {
        "$schema": result_topology()["summary"]["$schema"],
        "generated_utc": generated_utc,
        "status": SUMMARY_PASS,
        "acknowledgement": RUN_ACK_TOKEN,
        "run_root": str(run_root),
        "destination": str(prior.DEST),
        "contract_sha256": state["contract_digest"],
        "baseline_sha256": state["baseline_digest"],
        "v009_recovery_contract_sha256": prior.V009_CONTRACT_SHA256,
        "v010_recovery_contract_sha256": V010_CONTRACT_SHA256,
        "recovery_contract_sha256": recovery_sha,
        "v009_run_id": prior.V009_RUN_ID,
        "v009_import_receipt_sha256": prior.V009_IMPORT_RECEIPT_SHA256,
        "v009_wrapper_failure_summary_sha256": prior.V009_SUMMARY_SHA256,
        "preflight_reverify": PRE_VALIDATION_PASS + "\n" + recovery_sha,
        "post_exit_reverify": POST_VALIDATION_PASS + "\n" + receipt_sha256,
        "validation_process": copy.deepcopy(process),
        "validation_receipt": {
            "path": str(run_root / VALIDATION_RECEIPT),
            "sha256": receipt_sha256,
            "status": VALIDATION_PASS,
        },
        "post_exit_package_sha256": copy.deepcopy(
            contract["completed_v009_import"]["package_sha256"]),
        "editor_process_count": 1,
        "import_process_count": 0,
        "content_move_count": 0,
        "no_build_tool_invoked": True,
        "exact_ubt_command_line_matches": 0,
        "environment_restoration_verified": True,
        "strict_exit_zero_no_fatal_and_no_ubt_log_required": True,
        "error": None,
    }


def validate_v011_summary(
        summary: dict, contract: dict, state: dict, run_root: Path,
        receipt: dict, receipt_sha256: str, log_hashes: dict) -> None:
    if prior.empty_key_paths(summary) != []:
        raise RecoveryError("v011 final summary unexpectedly contains an empty key")
    exact_iso_utc(summary.get("generated_utc"), "v011 summary generated_utc")
    process = summary.get("validation_process")
    if not isinstance(process, dict):
        raise RecoveryError("v011 final summary validation process missing")
    expected_process_keys = set(process_fixture(1, "A", "B", "C"))
    if set(process) != expected_process_keys:
        raise RecoveryError("v011 validation process exact key-set drift")
    if (type(process.get("process_id")) is not int
            or type(process.get("exit_code")) is not int):
        raise RecoveryError("v011 validation process integer type drift")
    exact_summary_integers = {
        "editor_process_count": 1,
        "import_process_count": 0,
        "content_move_count": 0,
        "exact_ubt_command_line_matches": 0,
    }
    if any(type(summary.get(key)) is not int or summary[key] != value
           for key, value in exact_summary_integers.items()):
        raise RecoveryError("v011 summary exact integer field/type drift")
    retry = process.get("redirected_log_read_open_retry")
    if (not isinstance(retry, dict)
            or set(retry) != {
                "log_attempts", "stdout_attempts", "stderr_attempts",
                "bounded_timeout_milliseconds"}
            or type(retry.get("bounded_timeout_milliseconds")) is not int
            or retry.get("bounded_timeout_milliseconds") != 15000
            or any(type(retry.get(key)) is not int or retry[key] <= 0
                   for key in ("log_attempts", "stdout_attempts", "stderr_attempts"))):
        raise RecoveryError("v011 log read-open retry evidence drift")
    expected_process = process_fixture(
        receipt["validator_process_id"],
        log_hashes[VALIDATOR_LOGS[0]],
        log_hashes[VALIDATOR_LOGS[1]],
        log_hashes[VALIDATOR_LOGS[2]],
        (retry["log_attempts"], retry["stdout_attempts"], retry["stderr_attempts"]),
    )
    expected = summary_fixture(
        contract, state, run_root, receipt, receipt_sha256,
        expected_process, summary["generated_utc"])
    if object_hash(summary) != object_hash(expected):
        raise RecoveryError("v011 final summary exact identity/receipt/process binding drift")


def expect_rejected(callback, label: str) -> None:
    try:
        callback()
    except RecoveryError:
        return
    raise RecoveryError("v011 synthetic tamper regression was accepted: " + label)


def run_synthetic_binding_regressions(contract: dict, state: dict) -> None:
    fake_root = exact_v011_run_root(
        str(RECOVERY_AUDIT_ROOT / "20260815T150000Z-deadbeef"),
        require_exists=False)
    receipt = receipt_fixture(contract, state, fake_root, 424242)
    validate_v011_receipt(receipt, contract, state, fake_root)
    drifted_receipt = copy.deepcopy(receipt)
    drifted_receipt["v009_wrapper_incident_binding_sha256"] = "0" * 64
    expect_rejected(
        lambda: validate_v011_receipt(
            drifted_receipt, contract, state, fake_root),
        "receipt chronology binding")
    boolean_pid = copy.deepcopy(receipt)
    boolean_pid["process_id"] = True
    boolean_pid["validator_process_id"] = True
    expect_rejected(
        lambda: validate_v011_receipt(boolean_pid, contract, state, fake_root),
        "receipt boolean-for-process-id")
    receipt_sha = object_hash(receipt)
    logs = {name: str(index) * 64 for index, name in enumerate(VALIDATOR_LOGS, 1)}
    process = process_fixture(424242, *(logs[name] for name in VALIDATOR_LOGS))
    summary = summary_fixture(contract, state, fake_root, receipt, receipt_sha, process)
    validate_v011_summary(
        summary, contract, state, fake_root, receipt, receipt_sha, logs)
    missing_ack = copy.deepcopy(summary)
    missing_ack.pop("acknowledgement")
    expect_rejected(
        lambda: validate_v011_summary(
            missing_ack, contract, state, fake_root, receipt, receipt_sha, logs),
        "missing summary acknowledgement")
    wrong_path = copy.deepcopy(summary)
    wrong_path["validation_receipt"]["path"] += ".wrong"
    expect_rejected(
        lambda: validate_v011_summary(
            wrong_path, contract, state, fake_root, receipt, receipt_sha, logs),
        "wrong summary receipt path")
    boolean_count = copy.deepcopy(summary)
    boolean_count["editor_process_count"] = True
    expect_rejected(
        lambda: validate_v011_summary(
            boolean_count, contract, state, fake_root, receipt, receipt_sha, logs),
        "summary boolean-for-editor-count")
    boolean_retry = copy.deepcopy(summary)
    boolean_retry["validation_process"][
        "redirected_log_read_open_retry"]["log_attempts"] = True
    expect_rejected(
        lambda: validate_v011_summary(
            boolean_retry, contract, state, fake_root, receipt, receipt_sha, logs),
        "summary boolean-for-log-retry-count")
    expect_rejected(
        lambda: strict_json_text('{"a":1,"a":2}'), "duplicate normal key")
    expect_rejected(
        lambda: strict_json_text('{"":1,"":2}'), "duplicate empty key")


def validate_candidate_payload(payload: dict, state: dict) -> None:
    generated = exact_iso_utc(payload.get("generated_utc"), "v011 generated_utc")
    if generated != candidate_generated_utc(state):
        raise RecoveryError("v011 generated timestamp is not exact lane-state timestamp")
    if object_hash(payload) != object_hash(build_candidate_payload(state, generated)):
        raise RecoveryError("v011 full candidate payload differs from reconstruction")
    stale = copy.deepcopy(payload["stale_unexecuted_v010"])
    declared = stale.pop("binding_sha256", None)
    if declared != object_hash(stale):
        raise RecoveryError("v011 stale-v010 chronology binding hash drift")
    if (payload["lane"]["file_count"] != 55
            or payload["result_topology"]["unreal_process_count"] != 1
            or payload["result_topology"]["import_process_count"] != 0
            or payload["policy"]["v010_execution_authorized"] is not False
            or payload["policy"]["quarantine_move_authorized"] is not False
            or payload["policy"]["importer_process_authorized"] is not False):
        raise RecoveryError("v011 lane/process/no-import safety closure drift")
    if (type(payload["lane"]["file_count"]) is not int
            or type(payload["result_topology"]["unreal_process_count"]) is not int
            or type(payload["result_topology"]["import_process_count"]) is not int):
        raise RecoveryError("v011 candidate exact integer field/type drift")
    run_synthetic_binding_regressions(payload, state)


def dry_build_payload(require_output_absent: bool = True) -> tuple[dict, str, int]:
    if require_output_absent and (OUTPUT.exists() or OUTPUT_SHA.exists()):
        raise RecoveryError("v011 dry-build requires absent contract and sidecar")
    if RECOVERY_AUDIT_ROOT.exists():
        raise RecoveryError("v011 dry-build requires absent result root")
    state = authority_state()
    payload = build_candidate_payload(state, candidate_generated_utc(state))
    validate_candidate_payload(payload, state)
    serialized = serialized_payload(payload)
    validate_candidate_payload(strict_json_text(serialized.decode("utf-8")), state)
    return payload, hashlib.sha256(serialized).hexdigest().upper(), len(serialized)


def create_contract(acknowledgement: str) -> None:
    if acknowledgement != ACK_TOKEN:
        raise RecoveryError("exact v011 recovery-freeze acknowledgement missing")
    if OUTPUT.exists() or OUTPUT_SHA.exists():
        raise RecoveryError("refusing to overwrite v011 recovery contract or sidecar")
    payload, expected_digest, expected_size = dry_build_payload()
    serialized = serialized_payload(payload)
    if len(serialized) != expected_size:
        raise RecoveryError("v011 serialized size changed after no-write preflight")
    OUTPUT.write_text(serialized.decode("utf-8"), encoding="utf-8", newline="\n")
    digest = BASE.sha256(OUTPUT)
    if digest != expected_digest:
        raise RecoveryError("v011 written contract hash differs from dry-build")
    OUTPUT_SHA.write_text(
        f"{digest}  {OUTPUT.name}\n", encoding="ascii", newline="\n")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V011_CONTRACT_FROZEN")
    print(digest)


def load_frozen() -> tuple[dict, dict]:
    state = authority_state()
    if not OUTPUT.is_file() or not OUTPUT_SHA.is_file():
        raise RecoveryError("v011 recovery contract/sidecar absent")
    digest = BASE.sha256(OUTPUT)
    if OUTPUT_SHA.read_text(encoding="ascii") != f"{digest}  {OUTPUT.name}\n":
        raise RecoveryError("v011 recovery sidecar drift")
    payload = strict_json_file(OUTPUT)
    validate_candidate_payload(payload, state)
    BASE.verify_snapshot(payload["lane"], "v011 prepared validation-only lane")
    return payload, state


def verify_pre_validation() -> None:
    payload, state = load_frozen()
    if RECOVERY_AUDIT_ROOT.exists():
        raise RecoveryError("v011 result root already exists; one-use validation consumed")
    prior.verify_destination(state["imported"])
    prior.exact_v009_run_snapshot()
    prior.verify_v009_quarantine(state["v009"])
    exact_v010_pair()
    print(PRE_VALIDATION_PASS)
    print(BASE.sha256(OUTPUT))


def exact_run_children(run_root: Path, expected_names: set[str], label: str) -> dict:
    children = list(run_root.iterdir())
    if any(not path.is_file() or path.is_symlink() for path in children):
        raise RecoveryError(label + " contains a directory/link/non-file child")
    actual = {path.name: path for path in children}
    if set(actual) != expected_names or len(actual) != len(expected_names):
        raise RecoveryError(label + " exact file closure drift: " + repr(sorted(actual)))
    return actual


def forbidden_log_tokens(combined: str) -> list[str]:
    tokens = (
        "Fatal error:", "Assertion failed:", "Unhandled Exception:",
        "appError called", "Ensure condition failed", "ModeManager",
        "Launching UnrealBuildTool", "UnrealBuildTool", "Build.bat",
        "-Mode=ValidatePlatforms", "AutoSDKInfo.txt", "UBT AutoSDK ReturnCode",
    )
    return [token for token in tokens if token in combined]


def verify_post_validation(run_root_raw: str) -> None:
    contract, state = load_frozen()
    run_root = exact_v011_run_root(run_root_raw)
    expected = set(VALIDATOR_LOGS) | {VALIDATION_RECEIPT}
    actual = exact_run_children(run_root, expected, "v011 post-validator run")
    receipt_path = actual[VALIDATION_RECEIPT]
    receipt = strict_json_file(receipt_path)
    validate_v011_receipt(receipt, contract, state, run_root)
    combined = "\n".join(
        actual[name].read_text(encoding="utf-8", errors="replace")
        for name in VALIDATOR_LOGS)
    found = forbidden_log_tokens(combined)
    if found:
        raise RecoveryError("v011 validator fatal/build-tool log token drift: " + repr(found))
    if ("LINE_BOSS_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V011_VALIDATION_PASS"
            not in combined or "Editor shut down" not in combined):
        raise RecoveryError("v011 validation PASS/natural-exit marker drift")
    prior.verify_destination(state["imported"])
    prior.exact_v009_run_snapshot()
    prior.verify_v009_quarantine(state["v009"])
    exact_v010_pair()
    print(POST_VALIDATION_PASS)
    print(BASE.sha256(receipt_path))


def verify_final(run_root_raw: str) -> None:
    contract, state = load_frozen()
    run_root = exact_v011_run_root(run_root_raw)
    expected = set(VALIDATOR_LOGS) | {VALIDATION_RECEIPT, SUMMARY_NAME}
    actual = exact_run_children(run_root, expected, "v011 final run")
    receipt_path = actual[VALIDATION_RECEIPT]
    receipt = strict_json_file(receipt_path)
    validate_v011_receipt(receipt, contract, state, run_root)
    summary = strict_json_file(actual[SUMMARY_NAME])
    receipt_sha = BASE.sha256(receipt_path)
    log_hashes = {name: BASE.sha256(actual[name]) for name in VALIDATOR_LOGS}
    validate_v011_summary(
        summary, contract, state, run_root, receipt, receipt_sha, log_hashes)
    prior.verify_destination(state["imported"])
    prior.exact_v009_run_snapshot()
    prior.verify_v009_quarantine(state["v009"])
    exact_v010_pair()
    print(FINAL_PASS)
    print(BASE.sha256(actual[SUMMARY_NAME]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acknowledgement", default="")
    parser.add_argument("--run-root", default="")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-build", action="store_true")
    group.add_argument("--verify-pre-validation", action="store_true")
    group.add_argument("--verify-post-validation", action="store_true")
    group.add_argument("--verify-final", action="store_true")
    args = parser.parse_args()
    if args.dry_build:
        _, digest, size = dry_build_payload()
        print(
            "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V011_"
            "NO_WRITE_FULL_PAYLOAD_PREFLIGHT")
        print(digest)
        print(size)
    elif args.verify_pre_validation:
        verify_pre_validation()
    elif args.verify_post_validation:
        if not args.run_root:
            raise RecoveryError("--verify-post-validation requires --run-root")
        verify_post_validation(args.run_root)
    elif args.verify_final:
        if not args.run_root:
            raise RecoveryError("--verify-final requires --run-root")
        verify_final(args.run_root)
    else:
        create_contract(args.acknowledgement)


if __name__ == "__main__":
    main()
