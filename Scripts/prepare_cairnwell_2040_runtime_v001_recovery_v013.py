"""Offline incident contract for guarded Cairnwell v013 validation-only recovery."""

from __future__ import annotations

import argparse
import copy
import fnmatch
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCRIPTS = PROJECT / "Scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import prepare_cairnwell_2040_runtime_v001_recovery_v012 as prior


BASE = prior.BASE
RecoveryError = prior.RecoveryError
OUTPUT = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v013_contract.json"
OUTPUT_SHA = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v013_contract.sha256"
V012_CONTRACT = prior.OUTPUT
V012_SIDECAR = prior.OUTPUT_SHA
V012_CONTRACT_SHA256 = (
    "975A59EED82A8CC0574406ACEE707262C23A173259B1504D4E370586E6E126CB"
)
V012_CONTRACT_BYTES = 173097
V012_SIDECAR_SHA256 = (
    "BB7D7ECC2C0C4E6649D2574C6FA3AA442FE3BDE5C1D375FB38A008788A3FCF4A"
)
V012_SIDECAR_BYTES = 122
V012_SIDECAR_TEXT = f"{V012_CONTRACT_SHA256}  {V012_CONTRACT.name}\n"
V012_RUN_ID = "20260815T163553Z-3dabbd20"
V012_RUN = prior.RECOVERY_AUDIT_ROOT / V012_RUN_ID
V012_PROCESS_ID = 20804
V012_RECEIPT = "fresh_process_validation_receipt_recovery_v012.json"
V012_SUMMARY = "lane_summary_recovery_v012.json"
V012_RECEIPT_SHA256 = (
    "4C6ADEB0C3C94AD227EDAACB735552895BB1B1C2B08077C3A1F9566E18FD0F65"
)
V012_SUMMARY_SHA256 = (
    "5BDB57399DE607028E2A5E57B127374D25718E4F73B1FEF69379A55B057BB596"
)
V012_RUN_FILES = {
    V012_RECEIPT: (61921, V012_RECEIPT_SHA256),
    "fresh_process_validation_recovery_v012.log": (
        407827, "64CF30231E4A9A6FDEBDF9641CEDF199AE9A7933C6250391F78F3E37EC67F8F6"),
    "fresh_process_validation_recovery_v012.stderr.log": (
        0, "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"),
    "fresh_process_validation_recovery_v012.stdout.log": (
        409151, "4731EA273E95A2917DCC3902D4DC2C1CAA663DC8DA76898AAB244D7B0DA4192C"),
    V012_SUMMARY: (2392, V012_SUMMARY_SHA256),
}
V012_SUMMARY_STATUS = (
    "FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012_VALIDATION_ONLY_LANE"
)
V012_SUMMARY_ERROR = (
    "V012 validator failed strict exit/log/zero-UBT gate: exit=0 "
    "fatal=CleanupOrphanedCacheFiles (PostWrite)"
)

RECOVERY_AUDIT_ROOT = PROJECT / (
    "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "UnrealImportLane_v001/Recovery_v013"
)
ACK_TOKEN = "FREEZE_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V013_ONCE"
RUN_ACK_TOKEN = "VALIDATE_CAIRNWELL_2040_RUNTIME_V001_V009_IMPORT_V013_ONCE"
STATUS = (
    "FROZEN__CAIRNWELL_2040_RUNTIME_V001_INCIDENT_CHAINED_RECOVERY_V013__"
    "READY_FOR_ONE_SHOT_VALIDATION_ONLY_OF_V009_PASS_IMPORT"
)
V013_ADDITIONS = {
    "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V013.md",
    "Scripts/prepare_cairnwell_2040_runtime_v001_recovery_v013.py",
    "Scripts/validate_cairnwell_2040_runtime_recovery_v013.py",
    "Scripts/run_cairnwell_2040_runtime_validation_recovery_v013.ps1",
    "Scripts/tests/test_cairnwell_2040_runtime_validation_recovery_v013.py",
    "Scripts/cairnwell_2040_runtime_v001_recovery_v012_contract.json",
    "Scripts/cairnwell_2040_runtime_v001_recovery_v012_contract.sha256",
}
VALIDATION_PREFIX = "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v013/"
VALIDATION_RECEIPT = "fresh_process_validation_receipt_recovery_v013.json"
VALIDATION_FAILURE = "fresh_process_validation_failure_recovery_v013.json"
SUMMARY_NAME = "lane_summary_recovery_v013.json"
VALIDATOR_LOGS = [
    "fresh_process_validation_recovery_v013.log",
    "fresh_process_validation_recovery_v013.stdout.log",
    "fresh_process_validation_recovery_v013.stderr.log",
]
VALIDATION_PASS = (
    "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V013_DISTINCT_FRESH_PROCESS__"
    "READ_ONLY_RELOAD_OF_V009_PASS_IMPORT__EXACT_PERSISTED_DEPENDENCIES__"
    "ZERO_CACHE_DELETION_OR_WRITE__11_PACKAGE_HASHES_UNCHANGED"
)
SUMMARY_PASS = (
    "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V013_GUARDED_"
    "VALIDATION_ONLY_OF_V009_PASS_IMPORT"
)
PRE_VALIDATION_PASS = (
    "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V013_PRE_VALIDATION_REVERIFIED"
)
POST_VALIDATION_PASS = (
    "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V013_POST_VALIDATION_REVERIFIED"
)
FINAL_PASS = (
    "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V013_FINAL_FIVE_FILE_REVERIFIED"
)

PRELOAD_LINE = (
    "CleanupOrphanedCacheFiles (PreLoad): 1 .ref files found, "
    "1 referenced binaries"
)
POSTWRITE_LINE = (
    "CleanupOrphanedCacheFiles (PostWrite): 1 .ref files found, "
    "1 referenced binaries"
)
ZERO_MUTATION_SUMMARY_LINE = (
    "CleanupOrphanedCacheFiles: 1 total binaries, 1 referenced (kept), "
    "0 old-style pre-migration (kept), 0 orphans deleted, "
    "0 orphans locked (kept)"
)
ACTUAL_CACHE_MUTATION_TOKENS = (
    "Asset registry cache written as",
    "deleted (orphaned",
    "delete failed (orphaned",
    "CleanupOrphanedCacheFiles: legacy location",
)
LEGACY_CACHE_ROOT = PROJECT / "Intermediate"
LEGACY_CACHE_MONOLITHIC = "CachedAssetRegistry.bin"
LEGACY_CACHE_SHARD_PATTERN = "CachedAssetRegistry_*.bin"


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


def exact_v012_run_snapshot() -> dict:
    if not V012_RUN.is_dir():
        raise RecoveryError("exact consumed Recovery_v012 run is absent")
    children = list(V012_RUN.iterdir())
    if any(not path.is_file() or path.is_symlink() for path in children):
        raise RecoveryError("Recovery_v012 contains directory/link/non-file child")
    if {path.name for path in children} != set(V012_RUN_FILES):
        raise RecoveryError("Recovery_v012 exact five-file closure drift")
    rows = []
    for name, (size, digest) in V012_RUN_FILES.items():
        path = V012_RUN / name
        if path.stat().st_size != size or BASE.sha256(path) != digest:
            raise RecoveryError("Recovery_v012 evidence bytes drift: " + name)
        rows.append(BASE.file_row(path))
    return {
        "root": BASE.relative(V012_RUN),
        "file_count": 5,
        "files": sorted(rows, key=lambda row: row["path"].casefold()),
        "inventory_sha256": BASE.canonical_hash(rows),
    }


def exact_v012_pair() -> tuple[dict, dict]:
    if (not V012_CONTRACT.is_file()
            or V012_CONTRACT.stat().st_size != V012_CONTRACT_BYTES
            or BASE.sha256(V012_CONTRACT) != V012_CONTRACT_SHA256):
        raise RecoveryError("consumed v012 contract bytes drift")
    if (not V012_SIDECAR.is_file()
            or V012_SIDECAR.stat().st_size != V012_SIDECAR_BYTES
            or BASE.sha256(V012_SIDECAR) != V012_SIDECAR_SHA256
            or V012_SIDECAR.read_text(encoding="ascii") != V012_SIDECAR_TEXT):
        raise RecoveryError("consumed v012 sidecar bytes/text drift")
    payload, state = prior.load_frozen()
    if payload.get("$schema") != (
            "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v12"):
        raise RecoveryError("consumed v012 contract schema drift")
    return payload, state


def cleanup_log_evidence(
        paths: dict[str, Path], primary_names: tuple[str, str] | None = None,
        stderr_name: str | None = None) -> dict:
    if primary_names is None:
        primary_names = (VALIDATOR_LOGS[0], VALIDATOR_LOGS[1])
    if stderr_name is None:
        stderr_name = VALIDATOR_LOGS[2]
    if set(paths) != set(primary_names) | {stderr_name}:
        raise RecoveryError("cache cleanup evidence exact log-key closure drift")
    per_log = {}
    for name in primary_names:
        text = paths[name].read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        phase_indices = {
            "preload": [
                index for index, line in enumerate(lines)
                if line.endswith(PRELOAD_LINE)],
            "postwrite": [
                index for index, line in enumerate(lines)
                if line.endswith(POSTWRITE_LINE)],
        }
        if any(len(indices) != 1 for indices in phase_indices.values()):
            raise RecoveryError(
                "cache PreLoad/PostWrite informational line count drift: "
                + name + " " + repr({
                    phase: len(indices)
                    for phase, indices in phase_indices.items()}))
        for phase, indices in phase_indices.items():
            index = indices[0]
            if (index + 1 >= len(lines)
                    or not lines[index + 1].endswith(ZERO_MUTATION_SUMMARY_LINE)):
                raise RecoveryError(
                    "cache " + phase
                    + " zero-mutation result is not exact/adjacent: " + name)
        if sum(line.endswith(ZERO_MUTATION_SUMMARY_LINE) for line in lines) != 2:
            raise RecoveryError(
                "cache exact zero-mutation result count drift: " + name)
        actual_mutations = {
            token: text.count(token) for token in ACTUAL_CACHE_MUTATION_TOKENS
        }
        if any(actual_mutations.values()):
            raise RecoveryError(
                "cache write/deletion/locked/legacy mutation evidence present: "
                + name + " " + repr(actual_mutations))
        per_log[name] = {
            "preload_informational_occurrences": 1,
            "postwrite_informational_occurrences": 1,
            "adjacent_zero_mutation_summary_occurrences": 2,
            "cache_write_occurrences": 0,
            "orphan_deleted_occurrences": 0,
            "orphan_delete_failed_occurrences": 0,
            "legacy_cleanup_occurrences": 0,
        }
    if paths[stderr_name].stat().st_size != 0:
        raise RecoveryError("validator stderr is not exact empty file")
    return {
        "classification": (
            "UE58_CLEAR_CACHE_POSTWRITE_INFORMATIONAL_CLEANUP__ONE_REFERENCED_"
            "BINARY_KEPT__ZERO_ORPHANS_DELETED_OR_LOCKED__NO_CACHE_WRITE"),
        "per_primary_log": per_log,
        "generic_postwrite_text_is_not_a_failure_without_mutation_evidence": True,
        "actual_cache_write_or_deletion_tokens_are_fatal": True,
        "post_exit_exact_cache_snapshot_is_required": True,
    }


def is_legacy_cache_deletion_candidate(name: str) -> bool:
    folded = name.casefold()
    return (folded == LEGACY_CACHE_MONOLITHIC.casefold()
            or fnmatch.fnmatchcase(
                folded, LEGACY_CACHE_SHARD_PATTERN.casefold()))


def verify_legacy_cache_deletion_surface_absent() -> dict:
    if not LEGACY_CACHE_ROOT.is_dir():
        raise RecoveryError("Intermediate root is absent for legacy cache check")
    matches = sorted(
        path for path in LEGACY_CACHE_ROOT.iterdir()
        if is_legacy_cache_deletion_candidate(path.name)
    )
    if matches:
        raise RecoveryError(
            "legacy AssetRegistry deletion-surface path is present: "
            + repr([BASE.relative(path) for path in matches]))
    return {
        "root": BASE.relative(LEGACY_CACHE_ROOT),
        "monolithic_path": BASE.relative(
            LEGACY_CACHE_ROOT / LEGACY_CACHE_MONOLITHIC),
        "legacy_shard_pattern": (
            BASE.relative(LEGACY_CACHE_ROOT) + "/" + LEGACY_CACHE_SHARD_PATTERN),
        "monolithic_absent": True,
        "legacy_shard_paths": [],
        "matching_path_count": 0,
        "windows_case_insensitive_name_match": True,
    }


def validate_v012_execution(v012: dict, state: dict) -> dict:
    snapshot = exact_v012_run_snapshot()
    receipt_path = V012_RUN / V012_RECEIPT
    summary_path = V012_RUN / V012_SUMMARY
    receipt = strict_json_file(receipt_path)
    summary = strict_json_file(summary_path)
    prior.validate_v012_receipt(receipt, v012, state, V012_RUN)
    if (receipt.get("status") != prior.VALIDATION_PASS
            or receipt.get("process_id") != V012_PROCESS_ID
            or receipt.get("validator_process_id") != V012_PROCESS_ID
            or receipt.get("asset_mutation_count") != 0
            or receipt.get("import_or_reimport_process_count") != 0
            or receipt.get("asset_registry_cache_mutation_count") != 0
            or receipt.get("asset_registry_cache_before")
            != receipt.get("asset_registry_cache_after")
            or receipt.get("asset_registry_cache_after")
            != state["asset_registry_cache"]
            or receipt.get("package_sha256_before_loads")
            != receipt.get("package_sha256_after_loads")
            or receipt.get("package_sha256_after_loads")
            != v012["completed_v009_import"]["package_sha256"]
            or receipt.get("namespace_before") != receipt.get("namespace_after")
            or receipt.get("source_before") != receipt.get("source_after")
            or receipt.get("protected_before") != receipt.get("protected_after")
            or receipt.get("prepared_lane_before")
            != receipt.get("prepared_lane_after")
            or receipt.get("failures") != []
            or receipt.get("all_package_hashes_unchanged") is not True
            or receipt.get("persisted_asset_registry_dependency_closure_verified")
            is not True
            or receipt.get("no_asset_registry_cache_write_command_line_verified")
            is not True):
        raise RecoveryError("Recovery_v012 PASS receipt semantic/cache/package drift")
    if (summary.get("$schema") != prior.result_topology()["summary"]["$schema"]
            or summary.get("status") != V012_SUMMARY_STATUS
            or summary.get("acknowledgement") != prior.RUN_ACK_TOKEN
            or summary.get("run_root") != str(V012_RUN)
            or summary.get("recovery_contract_sha256") != V012_CONTRACT_SHA256
            or summary.get("error") != V012_SUMMARY_ERROR
            or summary.get("environment_restoration_verified") is not False
            or summary.get("validation_process") is not None
            or summary.get("validation_receipt") is not None
            or summary.get("editor_process_count") != 0
            or summary.get("import_process_count") != 0
            or summary.get("content_move_count") != 0
            or summary.get("no_build_tool_invoked") is not False):
        raise RecoveryError("Recovery_v012 wrapper failure summary identity drift")
    paths = {name: V012_RUN / name for name in V012_RUN_FILES}
    v012_primary = (
        "fresh_process_validation_recovery_v012.log",
        "fresh_process_validation_recovery_v012.stdout.log")
    v012_stderr = "fresh_process_validation_recovery_v012.stderr.log"
    cleanup = cleanup_log_evidence(
        {name: paths[name] for name in (*v012_primary, v012_stderr)},
        v012_primary, v012_stderr)
    combined = "\n".join(
        paths[name].read_text(encoding="utf-8", errors="replace")
        for name in (
            "fresh_process_validation_recovery_v012.log",
            "fresh_process_validation_recovery_v012.stdout.log",
            "fresh_process_validation_recovery_v012.stderr.log"))
    forbidden = (
        "Fatal error:", "Assertion failed:", "Unhandled Exception:",
        "appError called", "Ensure condition failed", "ModeManager",
        "Launching UnrealBuildTool", "UnrealBuildTool", "Build.bat",
        "-Mode=ValidatePlatforms", "AutoSDKInfo.txt", "UBT AutoSDK ReturnCode",
    )
    found = [token for token in forbidden if token in combined]
    if (found
            or "LINE_BOSS_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012_VALIDATION_PASS"
            not in combined
            or "Editor shut down" not in combined):
        raise RecoveryError(
            "Recovery_v012 fatal/UBT/PASS/natural-exit log drift: " + repr(found))
    incident = {
        "classification": (
            "V012_FRESH_VALIDATION_PASS__WRAPPER_FALSE_POSITIVE_ON_INFORMATIONAL_"
            "POSTWRITE_CLEANUP__SEPARATE_NULL_TO_EMPTY_ENV_RESTORE_DEFECT__"
            "V013_VALIDATION_ONLY"),
        "run_id": V012_RUN_ID,
        "process_id": V012_PROCESS_ID,
        "run_snapshot": snapshot,
        "validation_receipt": BASE.file_row(receipt_path),
        "summary": BASE.file_row(summary_path),
        "logs": {
            name: BASE.file_row(V012_RUN / name)
            for name in (
                "fresh_process_validation_recovery_v012.log",
                "fresh_process_validation_recovery_v012.stdout.log",
                "fresh_process_validation_recovery_v012.stderr.log")
        },
        "unreal_exit_code": 0,
        "fresh_validation_receipt_semantic_pass": True,
        "package_source_protected_lane_unchanged": True,
        "asset_registry_cache_before_after_and_current_exact": True,
        "cache_cleanup": cleanup,
        "fatal_ensure_or_ubt_log_patterns": [],
        "natural_editor_exit_verified": True,
        "wrapper_failure": {
            "error": V012_SUMMARY_ERROR,
            "cleanup_token_was_informational_not_mutating": True,
            "environment_restoration_verified": False,
            "environment_root_cause": (
                "POWERSHELL_NULL_ARGUMENT_COERCED_TO_EMPTY_STRING__ABSENT_"
                "PROCESS_ENVIRONMENT_VALUES_REQUIRE_NULLSTRING_FOR_REMOVAL"),
        },
    }
    incident["binding_sha256"] = object_hash(incident)
    return incident


def v013_lane_snapshot(v012: dict) -> dict:
    paths = {row["path"] for row in v012["lane"]["files"]} | V013_ADDITIONS
    snapshot = BASE.inventory([PROJECT / path for path in paths])
    if (snapshot["file_count"] != 69
            or {row["path"] for row in snapshot["files"]} != paths):
        raise RecoveryError("v013 prepared-lane exact 69-file path closure drift")
    return snapshot


def result_topology() -> dict:
    return {
        "audit_root": BASE.relative(RECOVERY_AUDIT_ROOT),
        "run_root_pattern": BASE.relative(RECOVERY_AUDIT_ROOT) + "/<UTC>-<GUID8>",
        "validation": {
            "receipt_filename": VALIDATION_RECEIPT,
            "failure_filename": VALIDATION_FAILURE,
            "$schema": VALIDATION_PREFIX + "fresh-process-validation/v13",
            "pass_status": VALIDATION_PASS,
            "package_hash_fields": [
                "package_sha256_before_loads", "package_sha256_after_loads"],
        },
        "summary": {
            "filename": SUMMARY_NAME,
            "$schema": VALIDATION_PREFIX + "validation-only-lane-summary/v13",
            "pass_status": SUMMARY_PASS,
            "package_hash_field": "post_exit_package_sha256",
            "cache_snapshot_field": "post_exit_asset_registry_cache",
        },
        "validator_logs": list(VALIDATOR_LOGS),
        "unreal_process_count": 1,
        "import_process_count": 0,
    }


def authority_state() -> dict:
    v012, state = exact_v012_pair()
    incident = validate_v012_execution(v012, state)
    prior.prior.prior.verify_destination(state["imported"])
    cache = prior.verify_asset_registry_cache_snapshot()
    if cache != state["asset_registry_cache"]:
        raise RecoveryError("post-v012 current cache differs from frozen authority")
    lane = v013_lane_snapshot(v012)
    legacy_absence = verify_legacy_cache_deletion_surface_absent()
    return {
        **state, "v012": v012, "v012_incident": incident,
        "v013_lane": lane, "asset_registry_cache": cache,
        "legacy_cache_deletion_surface_absence": legacy_absence,
    }


def candidate_generated_utc(state: dict) -> str:
    latest = max(int(row["mtime_ns"]) for row in state["v013_lane"]["files"])
    return datetime.fromtimestamp(
        latest / 1_000_000_000, tz=timezone.utc).isoformat()


def build_candidate_payload(state: dict, generated_utc: str) -> dict:
    payload = copy.deepcopy(state["v012"])
    payload.update({
        "$schema": "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v13",
        "status": STATUS,
        "generated_utc": generated_utc,
        "acknowledgement": RUN_ACK_TOKEN,
        "failed_v012_wrapper": copy.deepcopy(state["v012_incident"]),
        "cache_cleanup_adjudication": {
            "installed_engine_source": copy.deepcopy(
                payload["asset_registry_cache_write_suppression"][
                    "installed_engine_source"]),
            "clear_cache_read_or_write_enabled_gate_lines": "5318-5326",
            "unconditional_best_effort_postwrite_cleanup_lines": "5367-5371",
            "accepted_exact_preload_line": PRELOAD_LINE,
            "accepted_exact_postwrite_line": POSTWRITE_LINE,
            "required_adjacent_zero_mutation_line": ZERO_MUTATION_SUMMARY_LINE,
            "actual_mutation_tokens_are_fatal": list(ACTUAL_CACHE_MUTATION_TOKENS),
            "post_exit_cache_snapshot_must_equal_pre_validation": True,
        },
        "legacy_asset_registry_cache_deletion_surface": {
            "installed_engine_source": copy.deepcopy(
                payload["asset_registry_cache_write_suppression"][
                    "installed_engine_source"]),
            "silent_tmp_deletion_lines": "437-443",
            "legacy_shard_deletion_lines": "496-526",
            "legacy_monolithic_silent_delete_lines": "536-537",
            "exact_pre_validation_absence": copy.deepcopy(
                state["legacy_cache_deletion_surface_absence"]),
            "exact_post_exit_absence_required": True,
        },
        "environment_restoration_correction": {
            "classification": (
                "ABSENT_PROCESS_ENVIRONMENT_VALUES_REQUIRE_POWERSHELL_"
                "NULLSTRING_VALUE_TO_REMOVE_WITHOUT_EMPTY_STRING_DRIFT"),
            "absent_restore_value": (
                "[System.Management.Automation.Language.NullString]::Value"),
            "non_absent_values_restored_exactly": True,
            "strict_null_or_ordinal_string_equality_required": True,
            "all_three_values": [
                "LINEBOSS_CAIRNWELL_2040_RUNTIME_V001_RUN_ROOT",
                "LINEBOSS_CAIRNWELL_2040_RUNTIME_V001_ACK",
                "UE_SKIP_UBT_SDK_SETUP",
            ],
        },
        "lane": copy.deepcopy(state["v013_lane"]),
        "result_topology": result_topology(),
    })
    payload["policy"].update({
        "unreal_launch_authorized_by_freeze": False,
        "validation_only_recovery": True,
        "existing_v009_packages_are_immutable": True,
        "v012_pair_and_run_are_immutable_failed_wrapper_evidence": True,
        "v012_rerun_authorized": False,
        "quarantine_move_authorized": False,
        "delete_copy_import_reimport_save_authorized": False,
        "importer_process_authorized": False,
        "exactly_one_read_only_validator_process_required": True,
        "generic_postwrite_cleanup_token_is_not_fatal": True,
        "exact_zero_deletion_cleanup_result_required": True,
        "actual_cache_write_or_delete_tokens_are_fatal": True,
        "legacy_cache_deletion_surface_absence_required": True,
        "intermediate_cached_asset_registry_exact_invariance_required": True,
        "nullstring_absent_environment_restoration_required": True,
        "strict_environment_restoration_equality_required": True,
        "post_exit_all_file_and_package_hash_closure_required": True,
        "no_write_full_candidate_payload_preflight_required": True,
    })
    return payload


def exact_v013_run_root(raw: str, require_exists: bool = True) -> Path:
    path = Path(raw).resolve()
    if (path.parent != RECOVERY_AUDIT_ROOT.resolve()
            or not re.fullmatch(r"\d{8}T\d{6}Z-[0-9a-f]{8}", path.name)
            or (require_exists and not path.is_dir())):
        raise RecoveryError("v013 run root identity/path drift: " + str(path))
    return path


def receipt_fixture(
        contract: dict, state: dict, run_root: Path, validator_pid: int,
        generated_utc: str = "2026-08-15T17:00:00+00:00",
        engine_version: str = "5.8.0-test") -> dict:
    receipt = prior.receipt_fixture(
        contract, state, run_root, validator_pid, generated_utc, engine_version)
    receipt["$schema"] = result_topology()["validation"]["$schema"]
    receipt["writes_authorized"] = [
        str(run_root / VALIDATION_RECEIPT), str(run_root / VALIDATION_FAILURE)]
    receipt["status"] = VALIDATION_PASS
    receipt["v012_recovery_contract_sha256"] = V012_CONTRACT_SHA256
    receipt["v012_validation_receipt_sha256"] = V012_RECEIPT_SHA256
    receipt["v012_wrapper_failure_summary_sha256"] = V012_SUMMARY_SHA256
    receipt["v012_wrapper_incident_binding_sha256"] = state[
        "v012_incident"]["binding_sha256"]
    receipt["legacy_asset_registry_cache_absence_before"] = copy.deepcopy(
        state["legacy_cache_deletion_surface_absence"])
    receipt["legacy_asset_registry_cache_absence_after"] = copy.deepcopy(
        state["legacy_cache_deletion_surface_absence"])
    receipt["legacy_asset_registry_cache_mutation_count"] = 0
    return receipt


def validate_v013_receipt(
        payload: dict, contract: dict, state: dict, run_root: Path) -> None:
    if prior.prior.prior.empty_key_paths(payload) != [
            prior.prior.prior.V009_EMPTY_KEY_PATH]:
        raise RecoveryError("v013 validation receipt empty-key path closure drift")
    prior.prior.exact_iso_utc(payload.get("generated_utc"), "v013 receipt generated_utc")
    engine = payload.get("engine_version")
    if not isinstance(engine, str) or not engine.startswith(prior.prior.ENGINE_VERSION_PREFIX):
        raise RecoveryError("v013 receipt engine version is not exact UE 5.8 authority")
    pid = payload.get("validator_process_id")
    if (type(pid) is not int or pid <= 0
            or pid in (36612, prior.V011_PROCESS_ID, V012_PROCESS_ID)
            or payload.get("process_id") != pid):
        raise RecoveryError("v013 validator/import/prior-validator process identity drift")
    integers = {
        "process_id": pid, "import_process_id": 36612,
        "validator_process_id": pid, "mesh_count": 4,
        "authored_lod_count": 12, "texture_count": 3,
        "material_count": 4, "package_count": 11,
        "asset_mutation_count": 0, "import_or_reimport_process_count": 0,
        "asset_registry_cache_mutation_count": 0,
        "legacy_asset_registry_cache_mutation_count": 0,
    }
    if any(type(payload.get(key)) is not int or payload[key] != value
           for key, value in integers.items()):
        raise RecoveryError("v013 receipt exact integer field/type drift")
    expected = receipt_fixture(
        contract, state, run_root, pid, payload["generated_utc"], engine)
    if object_hash(payload) != object_hash(expected):
        raise RecoveryError("v013 fresh validation receipt exact content drift")


def process_fixture(
        process_id: int, log_sha256: str, stdout_sha256: str,
        stderr_sha256: str, cleanup: dict,
        attempts: tuple[int, int, int] = (1, 1, 1)) -> dict:
    process = prior.process_fixture(
        process_id, log_sha256, stdout_sha256, stderr_sha256, attempts)
    process["asset_registry_cache_cleanup"] = copy.deepcopy(cleanup)
    return process


def summary_fixture(
        contract: dict, state: dict, run_root: Path, receipt: dict,
        receipt_sha256: str, process: dict,
        generated_utc: str = "2026-08-15T17:01:00+00:00") -> dict:
    recovery_sha = payload_file_sha256(contract)
    return {
        "$schema": result_topology()["summary"]["$schema"],
        "generated_utc": generated_utc,
        "status": SUMMARY_PASS,
        "acknowledgement": RUN_ACK_TOKEN,
        "run_root": str(run_root),
        "destination": str(prior.prior.prior.DEST),
        "contract_sha256": state["contract_digest"],
        "baseline_sha256": state["baseline_digest"],
        "v009_recovery_contract_sha256": prior.prior.prior.V009_CONTRACT_SHA256,
        "v010_recovery_contract_sha256": prior.prior.V010_CONTRACT_SHA256,
        "v011_recovery_contract_sha256": prior.V011_CONTRACT_SHA256,
        "v012_recovery_contract_sha256": V012_CONTRACT_SHA256,
        "recovery_contract_sha256": recovery_sha,
        "v009_run_id": prior.prior.prior.V009_RUN_ID,
        "v011_run_id": prior.V011_RUN_ID,
        "v012_run_id": V012_RUN_ID,
        "v009_import_receipt_sha256": prior.prior.prior.V009_IMPORT_RECEIPT_SHA256,
        "v009_wrapper_failure_summary_sha256": prior.prior.prior.V009_SUMMARY_SHA256,
        "v011_failure_receipt_sha256": prior.V011_RUN_FILES[prior.V011_FAILURE][1],
        "v012_validation_receipt_sha256": V012_RECEIPT_SHA256,
        "v012_wrapper_failure_summary_sha256": V012_SUMMARY_SHA256,
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
        "post_exit_asset_registry_cache": copy.deepcopy(
            state["asset_registry_cache"]),
        "post_exit_legacy_asset_registry_cache_absence": copy.deepcopy(
            state["legacy_cache_deletion_surface_absence"]),
        "vehicle_model_id": prior.VEHICLE_MODEL_ID,
        "production_recipe_id": prior.DEVELOPMENT_RECIPE_ID,
        "current_geometry_authority_id": prior.CURRENT_GEOMETRY_AUTHORITY_ID,
        "editor_process_count": 1,
        "import_process_count": 0,
        "content_move_count": 0,
        "no_build_tool_invoked": True,
        "exact_ubt_command_line_matches": 0,
        "environment_restoration_verified": True,
        "strict_exit_zero_no_fatal_and_no_ubt_log_required": True,
        "error": None,
    }


def validate_v013_summary(
        summary: dict, contract: dict, state: dict, run_root: Path,
        receipt: dict, receipt_sha256: str, log_hashes: dict,
        cleanup: dict) -> None:
    if prior.prior.prior.empty_key_paths(summary) != []:
        raise RecoveryError("v013 final summary unexpectedly contains an empty key")
    prior.prior.exact_iso_utc(summary.get("generated_utc"), "v013 summary generated_utc")
    process = summary.get("validation_process")
    if not isinstance(process, dict):
        raise RecoveryError("v013 final summary validation process missing")
    retry = process.get("redirected_log_read_open_retry")
    if (not isinstance(retry, dict)
            or set(retry) != {
                "log_attempts", "stdout_attempts", "stderr_attempts",
                "bounded_timeout_milliseconds"}
            or type(retry.get("bounded_timeout_milliseconds")) is not int
            or retry["bounded_timeout_milliseconds"] != 15000
            or any(type(retry.get(key)) is not int or retry[key] <= 0
                   for key in ("log_attempts", "stdout_attempts", "stderr_attempts"))):
        raise RecoveryError("v013 log read-open retry evidence drift")
    integer_fields = {
        "editor_process_count": 1, "import_process_count": 0,
        "content_move_count": 0, "exact_ubt_command_line_matches": 0,
    }
    if any(type(summary.get(key)) is not int or summary[key] != value
           for key, value in integer_fields.items()):
        raise RecoveryError("v013 summary exact integer field/type drift")
    expected_process = process_fixture(
        receipt["validator_process_id"], log_hashes[VALIDATOR_LOGS[0]],
        log_hashes[VALIDATOR_LOGS[1]], log_hashes[VALIDATOR_LOGS[2]], cleanup,
        (retry["log_attempts"], retry["stdout_attempts"], retry["stderr_attempts"]),
    )
    expected = summary_fixture(
        contract, state, run_root, receipt, receipt_sha256,
        expected_process, summary["generated_utc"])
    if object_hash(summary) != object_hash(expected):
        raise RecoveryError("v013 final summary exact identity/process binding drift")


def expect_rejected(callback, label: str) -> None:
    try:
        callback()
    except RecoveryError:
        return
    raise RecoveryError("v013 synthetic tamper regression was accepted: " + label)


def run_synthetic_regressions(contract: dict, state: dict) -> None:
    root = exact_v013_run_root(
        str(RECOVERY_AUDIT_ROOT / "20260815T170000Z-deadbeef"),
        require_exists=False)
    receipt = receipt_fixture(contract, state, root, 424244)
    validate_v013_receipt(receipt, contract, state, root)
    wrong_v012 = copy.deepcopy(receipt)
    wrong_v012["v012_validation_receipt_sha256"] = "0" * 64
    expect_rejected(
        lambda: validate_v013_receipt(wrong_v012, contract, state, root),
        "drifted v012 receipt chronology")
    receipt_sha = object_hash(receipt)
    logs = {name: str(index) * 64 for index, name in enumerate(VALIDATOR_LOGS, 1)}
    v012_cleanup = state["v012_incident"]["cache_cleanup"]
    v012_primary_rows = list(v012_cleanup["per_primary_log"].values())
    cleanup = {
        **{
            key: copy.deepcopy(value) for key, value in v012_cleanup.items()
            if key != "per_primary_log"
        },
        "per_primary_log": {
            VALIDATOR_LOGS[index]: copy.deepcopy(v012_primary_rows[index])
            for index in range(2)
        },
    }
    process = process_fixture(
        424244, *(logs[name] for name in VALIDATOR_LOGS), cleanup)
    summary = summary_fixture(contract, state, root, receipt, receipt_sha, process)
    validate_v013_summary(
        summary, contract, state, root, receipt, receipt_sha, logs, cleanup)
    deletion = copy.deepcopy(summary)
    deletion["validation_process"]["asset_registry_cache_cleanup"][
        "per_primary_log"][VALIDATOR_LOGS[0]]["orphan_deleted_occurrences"] = 1
    expect_rejected(
        lambda: validate_v013_summary(
            deletion, contract, state, root, receipt, receipt_sha, logs, cleanup),
        "accepted cache deletion")
    no_restore = copy.deepcopy(summary)
    no_restore["environment_restoration_verified"] = False
    expect_rejected(
        lambda: validate_v013_summary(
            no_restore, contract, state, root, receipt, receipt_sha, logs, cleanup),
        "unrestored environment")


def validate_candidate_payload(payload: dict, state: dict) -> None:
    generated = prior.prior.exact_iso_utc(
        payload.get("generated_utc"), "v013 generated_utc")
    if generated != candidate_generated_utc(state):
        raise RecoveryError("v013 generated timestamp is not exact lane-state timestamp")
    if object_hash(payload) != object_hash(build_candidate_payload(state, generated)):
        raise RecoveryError("v013 full candidate payload differs from reconstruction")
    incident = copy.deepcopy(payload["failed_v012_wrapper"])
    declared = incident.pop("binding_sha256", None)
    if declared != object_hash(incident):
        raise RecoveryError("v013 failed-v012 incident binding hash drift")
    if (type(payload["lane"]["file_count"]) is not int
            or payload["lane"]["file_count"] != 69
            or type(payload["result_topology"]["unreal_process_count"]) is not int
            or payload["result_topology"]["unreal_process_count"] != 1
            or type(payload["result_topology"]["import_process_count"]) is not int
            or payload["result_topology"]["import_process_count"] != 0
            or payload["policy"]["v012_rerun_authorized"] is not False
            or payload["policy"]["quarantine_move_authorized"] is not False
            or payload["policy"]["importer_process_authorized"] is not False):
        raise RecoveryError("v013 lane/process/no-import safety closure drift")
    run_synthetic_regressions(payload, state)


def dry_build_payload(require_output_absent: bool = True) -> tuple[dict, str, int]:
    if require_output_absent and (OUTPUT.exists() or OUTPUT_SHA.exists()):
        raise RecoveryError("v013 dry-build requires absent contract and sidecar")
    if RECOVERY_AUDIT_ROOT.exists():
        raise RecoveryError("v013 dry-build requires absent result root")
    state = authority_state()
    payload = build_candidate_payload(state, candidate_generated_utc(state))
    validate_candidate_payload(payload, state)
    serialized = serialized_payload(payload)
    validate_candidate_payload(strict_json_text(serialized.decode("utf-8")), state)
    return payload, hashlib.sha256(serialized).hexdigest().upper(), len(serialized)


def create_contract(acknowledgement: str) -> None:
    if acknowledgement != ACK_TOKEN:
        raise RecoveryError("exact v013 recovery-freeze acknowledgement missing")
    if OUTPUT.exists() or OUTPUT_SHA.exists():
        raise RecoveryError("refusing to overwrite v013 recovery contract or sidecar")
    payload, expected_digest, expected_size = dry_build_payload()
    serialized = serialized_payload(payload)
    if len(serialized) != expected_size:
        raise RecoveryError("v013 serialized size changed after no-write preflight")
    OUTPUT.write_text(serialized.decode("utf-8"), encoding="utf-8", newline="\n")
    digest = BASE.sha256(OUTPUT)
    if digest != expected_digest:
        raise RecoveryError("v013 written contract hash differs from dry-build")
    OUTPUT_SHA.write_text(
        f"{digest}  {OUTPUT.name}\n", encoding="ascii", newline="\n")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V013_CONTRACT_FROZEN")
    print(digest)


def load_frozen() -> tuple[dict, dict]:
    state = authority_state()
    if not OUTPUT.is_file() or not OUTPUT_SHA.is_file():
        raise RecoveryError("v013 recovery contract/sidecar absent")
    digest = BASE.sha256(OUTPUT)
    if OUTPUT_SHA.read_text(encoding="ascii") != f"{digest}  {OUTPUT.name}\n":
        raise RecoveryError("v013 recovery sidecar drift")
    payload = strict_json_file(OUTPUT)
    validate_candidate_payload(payload, state)
    BASE.verify_snapshot(payload["lane"], "v013 prepared validation-only lane")
    return payload, state


def verify_pre_validation() -> None:
    _payload, state = load_frozen()
    if RECOVERY_AUDIT_ROOT.exists():
        raise RecoveryError("v013 result root already exists; one-use validation consumed")
    prior.prior.prior.verify_destination(state["imported"])
    prior.verify_asset_registry_cache_snapshot()
    verify_legacy_cache_deletion_surface_absent()
    exact_v012_pair()
    exact_v012_run_snapshot()
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
    ) + ACTUAL_CACHE_MUTATION_TOKENS
    return [token for token in tokens if token in combined]


def verify_post_validation(run_root_raw: str) -> None:
    contract, state = load_frozen()
    run_root = exact_v013_run_root(run_root_raw)
    expected = set(VALIDATOR_LOGS) | {VALIDATION_RECEIPT}
    actual = exact_run_children(run_root, expected, "v013 post-validator run")
    receipt_path = actual[VALIDATION_RECEIPT]
    receipt = strict_json_file(receipt_path)
    validate_v013_receipt(receipt, contract, state, run_root)
    cleanup_log_evidence({name: actual[name] for name in VALIDATOR_LOGS})
    combined = "\n".join(
        actual[name].read_text(encoding="utf-8", errors="replace")
        for name in VALIDATOR_LOGS)
    found = forbidden_log_tokens(combined)
    if found:
        raise RecoveryError("v013 validator fatal/build/cache-mutation token drift: " + repr(found))
    if ("LINE_BOSS_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V013_VALIDATION_PASS"
            not in combined or "Editor shut down" not in combined):
        raise RecoveryError("v013 validation PASS/natural-exit marker drift")
    prior.prior.prior.verify_destination(state["imported"])
    if prior.verify_asset_registry_cache_snapshot() != state["asset_registry_cache"]:
        raise RecoveryError("v013 post-exit cache snapshot drift")
    if (verify_legacy_cache_deletion_surface_absent()
            != state["legacy_cache_deletion_surface_absence"]):
        raise RecoveryError("v013 post-exit legacy cache deletion-surface drift")
    exact_v012_pair()
    exact_v012_run_snapshot()
    print(POST_VALIDATION_PASS)
    print(BASE.sha256(receipt_path))


def verify_final(run_root_raw: str) -> None:
    contract, state = load_frozen()
    run_root = exact_v013_run_root(run_root_raw)
    expected = set(VALIDATOR_LOGS) | {VALIDATION_RECEIPT, SUMMARY_NAME}
    actual = exact_run_children(run_root, expected, "v013 final run")
    receipt_path = actual[VALIDATION_RECEIPT]
    receipt = strict_json_file(receipt_path)
    validate_v013_receipt(receipt, contract, state, run_root)
    cleanup = cleanup_log_evidence({name: actual[name] for name in VALIDATOR_LOGS})
    summary = strict_json_file(actual[SUMMARY_NAME])
    receipt_sha = BASE.sha256(receipt_path)
    log_hashes = {name: BASE.sha256(actual[name]) for name in VALIDATOR_LOGS}
    validate_v013_summary(
        summary, contract, state, run_root, receipt, receipt_sha,
        log_hashes, cleanup)
    prior.prior.prior.verify_destination(state["imported"])
    if prior.verify_asset_registry_cache_snapshot() != state["asset_registry_cache"]:
        raise RecoveryError("v013 final cache snapshot drift")
    if (verify_legacy_cache_deletion_surface_absent()
            != state["legacy_cache_deletion_surface_absence"]):
        raise RecoveryError("v013 final legacy cache deletion-surface drift")
    exact_v012_pair()
    exact_v012_run_snapshot()
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
            "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V013_"
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
