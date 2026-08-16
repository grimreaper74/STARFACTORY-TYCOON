"""Dry-build, freeze, or verify Cairnwell validation-only recovery v010 offline."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import prepare_cairnwell_2040_runtime_v001_recovery_v009 as prior


BASE = prior.BASE
PROJECT = prior.PROJECT
CONTRACT = prior.CONTRACT
CONTRACT_SHA = prior.CONTRACT_SHA
BASELINE = prior.BASELINE
BASELINE_SHA = prior.BASELINE_SHA
V009_CONTRACT = prior.OUTPUT
V009_CONTRACT_SHA = prior.OUTPUT_SHA
OUTPUT = PROJECT / "Scripts/cairnwell_2040_runtime_v001_recovery_v010_contract.json"
OUTPUT_SHA = PROJECT / "Scripts/cairnwell_2040_runtime_v001_recovery_v010_contract.sha256"
DEST = prior.DEST
AUDIT_ROOT = prior.AUDIT_ROOT
RECOVERY_AUDIT_ROOT = AUDIT_ROOT / "Recovery_v010"
V009_RUN_ID = "20260815T141819Z-435fcd56"
V009_RUN = prior.RECOVERY_AUDIT_ROOT / V009_RUN_ID
V006_QUARANTINE = prior.V006_QUARANTINE
ACK_TOKEN = "FREEZE_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V010_ONCE"
RUN_ACK_TOKEN = "VALIDATE_CAIRNWELL_2040_RUNTIME_V001_V009_IMPORT_V010_ONCE"
STATUS = (
    "FROZEN__CAIRNWELL_2040_RUNTIME_V001_INCIDENT_CHAINED_RECOVERY_V010__"
    "READY_FOR_ONE_SHOT_VALIDATION_ONLY_OF_V009_PASS_IMPORT"
)
V009_CONTRACT_BYTES = 133106
V009_CONTRACT_SHA256 = (
    "BBDACD06A499240F8FA07D3CECFE661FD6B0C204DD834DB31CDC5B41D3204DAC"
)
V009_SIDECAR_BYTES = 122
V009_SIDECAR_SHA256 = (
    "CE356CCBE018F544E77AA20C9C00BF2A4AB150E3DF07072C75AC05212722A577"
)
V009_IMPORT_RECEIPT_SHA256 = (
    "F11952FD07E9B573E0882059C49DF474E166CAE9B25F2F677023260ACAA413A6"
)
V009_SUMMARY_SHA256 = (
    "10025897FA49CDFFB94B37C78B082E0D43391E2062BC15BC426BF52C0E6E9265"
)
V009_QUARANTINE_RECEIPT_SHA256 = (
    "AB17DB911591102E0EB01D0F3DEC56DE03DB51FCE05157739A642E4E796FD587"
)
V009_RUN_FILES = {
    "import_receipt_recovery_v009.json": (66735, V009_IMPORT_RECEIPT_SHA256),
    "lane_summary_recovery_v009.json": (4047, V009_SUMMARY_SHA256),
    "quarantine_receipt_v009.json": (8403, V009_QUARANTINE_RECEIPT_SHA256),
    "unreal_import_recovery_v009.log": (
        436401, "976AEC6978AC412C81124B17980907DB77C6025481F2BCC96C45424E7F08F58E"),
    "unreal_import_recovery_v009.stderr.log": (
        0, "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"),
    "unreal_import_recovery_v009.stdout.log": (
        437975, "FDEE3F83B570D7D42C0E79B7F341415C2E51EA35C9270EBDD2075AE1E4F0EA2C"),
}
V009_IMPORT_SCHEMA = (
    "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v009/unreal-import/v9"
)
V009_IMPORT_PASS = (
    "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_FRESH_IMPORT__4_MESHES__"
    "12_AUTHORED_LODS__3_TEXTURES__4_MATERIALS__EXACT_11_PACKAGE_CLOSURE"
)
V009_SUMMARY_SCHEMA = (
    "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v009/import-lane-summary/v9"
)
V009_SUMMARY_STATUS = (
    "FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_UNREAL_IMPORT_LANE"
)
V009_POWERSHELL_ERROR = (
    "The provided JSON includes a property whose name is an empty string, this is "
    "only supported using the -AsHashTable switch."
)
V009_EMPTY_KEY_PATH = 'assets.materials.body.graph.detail_clamp.inputs[""]'
TARGET_PLATFORM_SOURCE = Path(
    r"C:\Program Files\Epic Games\UE_5.8\Engine\Source\Developer\TargetPlatform\Private\TargetPlatformManagerModule.cpp"
)
TARGET_PLATFORM_SOURCE_BYTES = 61188
TARGET_PLATFORM_SOURCE_SHA256 = (
    "E86827925AECB8ED2250F5D7AB655269ED7FE6A83D6691B244FA36FAAD5A4E17"
)
V010_CHANGED = {"Scripts/tests/test_cairnwell_2040_runtime_import_lane_v001.py"}
V010_ADDITIONS = {
    "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V010.md",
    "Scripts/prepare_cairnwell_2040_runtime_v001_recovery_v010.py",
    "Scripts/validate_cairnwell_2040_runtime_recovery_v010.py",
    "Scripts/run_cairnwell_2040_runtime_validation_recovery_v010.ps1",
    "Scripts/tests/test_cairnwell_2040_runtime_validation_recovery_v010.py",
    "Scripts/cairnwell_2040_runtime_v001_recovery_v009_contract.json",
    "Scripts/cairnwell_2040_runtime_v001_recovery_v009_contract.sha256",
}


class RecoveryError(RuntimeError):
    pass


def object_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()


def strict_pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise RecoveryError("duplicate JSON property is forbidden: " + repr(key))
        result[key] = value
    return result


def strict_json_text(text: str) -> object:
    return json.loads(text, object_pairs_hook=strict_pairs)


def strict_json_file(path: Path) -> object:
    return strict_json_text(path.read_text(encoding="utf-8"))


def expected_fresh_assets(imported: dict) -> dict:
    assets = copy.deepcopy(imported["assets"])
    assets["persisted_asset_registry_dependency_closure_verified"] = True
    for group in ("modules", "textures", "materials"):
        for row in assets[group].values():
            row["persisted_dependency_check_required"] = True
    return assets


def empty_key_paths(value: object, path: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f'{path}[""]' if key == "" else (f"{path}.{key}" if path else key)
            if key == "":
                found.append(child_path)
            found.extend(empty_key_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(empty_key_paths(child, f"{path}[{index}]"))
    return found


def exact_v009_contract() -> dict:
    if (not V009_CONTRACT.is_file()
            or V009_CONTRACT.stat().st_size != V009_CONTRACT_BYTES
            or BASE.sha256(V009_CONTRACT) != V009_CONTRACT_SHA256):
        raise RecoveryError("executed v009 recovery contract byte/hash drift")
    expected_sidecar = f"{V009_CONTRACT_SHA256}  {V009_CONTRACT.name}\n"
    if (not V009_CONTRACT_SHA.is_file()
            or V009_CONTRACT_SHA.stat().st_size != V009_SIDECAR_BYTES
            or BASE.sha256(V009_CONTRACT_SHA) != V009_SIDECAR_SHA256
            or V009_CONTRACT_SHA.read_text(encoding="ascii") != expected_sidecar):
        raise RecoveryError("executed v009 recovery sidecar byte/hash/text drift")
    payload = strict_json_file(V009_CONTRACT)
    chain = copy.deepcopy(payload.get("incident_chain", {}))
    declared = chain.pop("binding_sha256", None)
    if (payload.get("$schema")
            != "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v9"
            or payload.get("status") != prior.STATUS
            or payload.get("acknowledgement") != prior.RUN_ACK_TOKEN
            or declared != object_hash(chain)
            or int(payload.get("lane", {}).get("file_count", -1)) != 41):
        raise RecoveryError("executed v009 recovery contract identity drift")
    return payload


def exact_v009_run_snapshot() -> dict:
    if not V009_RUN.is_dir():
        raise RecoveryError("exact executed v009 run root is absent")
    children = list(V009_RUN.iterdir())
    if any(not path.is_file() or path.is_symlink() for path in children):
        raise RecoveryError("executed v009 run contains a directory/link/non-file child")
    actual = {path.name: path for path in children}
    if set(actual) != set(V009_RUN_FILES) or len(actual) != 6:
        raise RecoveryError("executed v009 run all-file closure drift: " + repr(sorted(actual)))
    for name, (size, digest) in V009_RUN_FILES.items():
        path = actual[name]
        if path.stat().st_size != size or BASE.sha256(path) != digest:
            raise RecoveryError("executed v009 run file byte/hash drift: " + name)
    return BASE.inventory(list(actual.values()))


def validate_v009_receipts(v009: dict) -> tuple[dict, dict, dict]:
    import_path = V009_RUN / "import_receipt_recovery_v009.json"
    summary_path = V009_RUN / "lane_summary_recovery_v009.json"
    quarantine_path = V009_RUN / "quarantine_receipt_v009.json"
    imported = strict_json_file(import_path)
    summary = strict_json_file(summary_path)
    quarantined = strict_json_file(quarantine_path)
    if empty_key_paths(imported) != [V009_EMPTY_KEY_PATH]:
        raise RecoveryError("v009 import receipt empty-key path closure drift")
    clamp_inputs = imported["assets"]["materials"]["body"]["graph"][
        "detail_clamp"]["inputs"]
    if (list(clamp_inputs) != ["", "Max", "Min"]
            or imported.get("$schema") != V009_IMPORT_SCHEMA
            or imported.get("status") != V009_IMPORT_PASS
            or imported.get("recovery_contract_sha256") != V009_CONTRACT_SHA256
            or imported.get("process_id") != 36612
            or imported.get("failures") != []
            or imported.get("package_count") != 11
            or len(imported.get("package_sha256", {})) != 11
            or len(imported.get("namespace_disk_files", {})) != 11
            or imported.get("project_maps_loaded_or_saved") != []):
        raise RecoveryError("v009 PASS import receipt identity/evidence drift")
    if (summary.get("$schema") != V009_SUMMARY_SCHEMA
            or summary.get("status") != V009_SUMMARY_STATUS
            or summary.get("error") != V009_POWERSHELL_ERROR
            or summary.get("editor_process_count") != 1
            or summary.get("validation_process") is not None
            or summary.get("validation_receipt") is not None
            or summary.get("post_exit_reverify") is not None
            or summary.get("post_exit_package_sha256") is not None
            or summary.get("recovery_contract_sha256") != V009_CONTRACT_SHA256
            or summary.get("import_process", {}).get("process_id") != 36612
            or summary.get("import_process", {}).get("exit_code") != 0
            or summary.get("import_process", {}).get("fatal_log_patterns") != []):
        raise RecoveryError("v009 wrapper-failure summary identity drift")
    q_topology = v009.get("result_topology", {}).get("quarantine_receipt", {})
    if (quarantined.get("$schema") != q_topology.get("$schema")
            or quarantined.get("status") != q_topology.get("pass_status")
            or quarantined.get("recovery_contract_sha256") != V009_CONTRACT_SHA256
            or quarantined.get("operation") != "MOVE_DIRECTORY_ONLY__NO_DELETE"
            or quarantined.get("source_destination_absent_after_move") is not True
            or quarantined.get("quarantined_partial_packages")
            != v009.get("partial_packages")):
        raise RecoveryError("v009 quarantine receipt identity/hash drift")
    return imported, summary, quarantined


def verify_v009_quarantine(v009: dict) -> dict:
    if not V006_QUARANTINE.is_dir():
        raise RecoveryError("v009 preserved q6 quarantine root is absent")
    expected = v009.get("partial_packages", {})
    actual_paths = {
        BASE.relative(path) for path in V006_QUARANTINE.rglob("*") if path.is_file()
    }
    expected_paths = {row["quarantine_path"] for row in expected.values()}
    if actual_paths != expected_paths or len(actual_paths) != 11:
        raise RecoveryError("v009 q6 quarantine all-file closure drift")
    for row in expected.values():
        actual = BASE.file_row(PROJECT / row["quarantine_path"])
        if (actual["path"] != row["quarantine_path"]
                or any(actual[key] != row[key]
                       for key in ("bytes", "mtime_ns", "sha256"))):
            raise RecoveryError("v009 q6 quarantine package drift: " + row["quarantine_path"])
    return BASE.inventory([PROJECT / path for path in actual_paths])


def verify_destination(imported: dict) -> tuple[dict, dict]:
    expected_rows = imported.get("namespace_disk_files", {})
    actual_paths = {BASE.relative(path): path for path in DEST.rglob("*") if path.is_file()} \
        if DEST.is_dir() else {}
    if set(actual_paths) != set(expected_rows) or len(actual_paths) != 11:
        raise RecoveryError("v009 imported destination all-file closure drift")
    for rel, expected in expected_rows.items():
        actual = BASE.file_row(actual_paths[rel])
        if any(actual[key] != expected[key] for key in ("bytes", "mtime_ns", "sha256")):
            raise RecoveryError("v009 imported destination package drift: " + rel)
    disk = BASE.inventory(list(actual_paths.values()))
    package_hashes = dict(imported["package_sha256"])
    expected_package_hashes = {
        "/Game/" + Path(rel).relative_to("Content").with_suffix("").as_posix(): row["sha256"]
        for rel, row in expected_rows.items()
    }
    if package_hashes != expected_package_hashes:
        raise RecoveryError("v009 package-name/disk-hash mapping drift")
    return disk, package_hashes


def verify_v009_logs(summary: dict) -> dict:
    log_path = V009_RUN / "unreal_import_recovery_v009.log"
    stdout_path = V009_RUN / "unreal_import_recovery_v009.stdout.log"
    stderr_path = V009_RUN / "unreal_import_recovery_v009.stderr.log"
    combined = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in (log_path, stdout_path, stderr_path)
    )
    fatal = (
        "Fatal error:", "Assertion failed:", "Unhandled Exception:", "appError called",
        "Ensure condition failed", "ModeManagerInteractiveToolsContext",
    )
    found_fatal = [token for token in fatal if token in combined]
    if found_fatal:
        raise RecoveryError("v009 import log fatal/ensure drift: " + repr(found_fatal))
    if ("LINE_BOSS_CAIRNWELL_2040_RUNTIME_V001_IMPORT_PASS" not in combined
            or "Editor shut down" not in combined):
        raise RecoveryError("v009 import PASS/natural-exit marker drift")
    ubt_tokens = (
        "Launching UnrealBuildTool...", "Build.bat -Mode=ValidatePlatforms",
        "UBT AutoSDK ReturnCode: 0",
    )
    if any(token not in combined for token in ubt_tokens):
        raise RecoveryError("v009 observed startup UBT evidence drift")
    if summary.get("no_build_tool_invoked") is not True:
        raise RecoveryError("v009 summary no-build boolean chronology drift")
    return {
        "classification": (
            "V009_IMPORT_PASS__STARTUP_UBT_VALIDATEPLATFORMS_OBSERVED__"
            "SUMMARY_NO_BUILD_BOOLEAN_WAS_INCORRECT"),
        "observed_tokens": list(ubt_tokens),
        "summary_declared_no_build_tool_invoked": True,
        "actual_startup_ubt_validate_platforms_observed": True,
        "semantic_import_or_asset_failure": False,
        "v010_must_suppress_and_log_reject_ubt": True,
    }


def verify_target_platform_source() -> dict:
    if (not TARGET_PLATFORM_SOURCE.is_file()
            or TARGET_PLATFORM_SOURCE.stat().st_size != TARGET_PLATFORM_SOURCE_BYTES
            or BASE.sha256(TARGET_PLATFORM_SOURCE) != TARGET_PLATFORM_SOURCE_SHA256):
        raise RecoveryError("installed UE5.8 TargetPlatformManager source drift")
    return {
        "path": str(TARGET_PLATFORM_SOURCE),
        "bytes": TARGET_PLATFORM_SOURCE_BYTES,
        "sha256": TARGET_PLATFORM_SOURCE_SHA256,
        "skip_environment_variable": "UE_SKIP_UBT_SDK_SETUP",
        "skip_value": "1",
        "skip_guard_lines": "54;221-227",
        "validate_platforms_launch_lines": "366-400",
        "return_code_lines": "544-553",
    }


def verify_v009_lane_drift(v009: dict) -> None:
    changed = {
        row["path"] for row in v009["lane"]["files"]
        if BASE.file_row(PROJECT / row["path"]) != row
    }
    if changed != V010_CHANGED:
        raise RecoveryError(
            "v009 prepared-lane drift is not exact v010 patch: " + repr(sorted(changed)))


def v010_lane_snapshot(v009: dict) -> dict:
    paths = {row["path"] for row in v009["lane"]["files"]} | V010_ADDITIONS
    snapshot = BASE.inventory([PROJECT / path for path in paths])
    if (snapshot["file_count"] != 48
            or {row["path"] for row in snapshot["files"]} != paths):
        raise RecoveryError("v010 prepared-lane exact 48-file path closure drift")
    return snapshot


def result_topology() -> dict:
    prefix = "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v010/"
    return {
        "audit_root": BASE.relative(RECOVERY_AUDIT_ROOT),
        "run_root_pattern": BASE.relative(RECOVERY_AUDIT_ROOT) + "/<UTC>-<GUID8>",
        "validation": {
            "receipt_filename": "fresh_process_validation_receipt_recovery_v010.json",
            "failure_filename": "fresh_process_validation_failure_recovery_v010.json",
            "$schema": prefix + "fresh-process-validation/v10",
            "pass_status": (
                "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V010_DISTINCT_FRESH_PROCESS__"
                "READ_ONLY_RELOAD_OF_V009_PASS_IMPORT__11_PACKAGE_HASHES_UNCHANGED"),
            "package_hash_fields": [
                "package_sha256_before_loads", "package_sha256_after_loads"],
        },
        "summary": {
            "filename": "lane_summary_recovery_v010.json",
            "$schema": prefix + "validation-only-lane-summary/v10",
            "pass_status": (
                "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V010_GUARDED_"
                "VALIDATION_ONLY_OF_V009_PASS_IMPORT"),
            "package_hash_field": "post_exit_package_sha256",
        },
        "validator_logs": [
            "fresh_process_validation_recovery_v010.log",
            "fresh_process_validation_recovery_v010.stdout.log",
            "fresh_process_validation_recovery_v010.stderr.log",
        ],
        "unreal_process_count": 1,
        "import_process_count": 0,
    }


def authority_state() -> dict:
    inherited = prior.authority_state()
    v009 = exact_v009_contract()
    verify_v009_lane_drift(v009)
    run_snapshot = exact_v009_run_snapshot()
    imported, summary, quarantined = validate_v009_receipts(v009)
    q6_snapshot = verify_v009_quarantine(v009)
    destination_snapshot, package_hashes = verify_destination(imported)
    log_observation = verify_v009_logs(summary)
    target_source = verify_target_platform_source()
    return {
        **inherited,
        "v009": v009,
        "run_snapshot": run_snapshot,
        "imported": imported,
        "summary": summary,
        "quarantined": quarantined,
        "q6_snapshot": q6_snapshot,
        "destination_snapshot": destination_snapshot,
        "package_hashes": package_hashes,
        "log_observation": log_observation,
        "target_source": target_source,
    }


def candidate_generated_utc(state: dict) -> str:
    lane = v010_lane_snapshot(state["v009"])
    latest_mtime_ns = max(int(row["mtime_ns"]) for row in lane["files"])
    return datetime.fromtimestamp(
        latest_mtime_ns / 1_000_000_000, tz=timezone.utc).isoformat()


def build_candidate_payload(state: dict, generated_utc: str) -> dict:
    v009 = state["v009"]
    imported = state["imported"]
    summary = state["summary"]
    wrapper = {
        "classification": (
            "V009_UNREAL_IMPORT_PASS__POWERSHELL_WRAPPER_REJECTED_INTENTIONAL_"
            "EMPTY_JSON_PROPERTY__V010_VALIDATION_ONLY"),
        "failed_run_id": V009_RUN_ID,
        "run_snapshot": copy.deepcopy(state["run_snapshot"]),
        "import_receipt": BASE.file_row(V009_RUN / "import_receipt_recovery_v009.json"),
        "summary": BASE.file_row(V009_RUN / "lane_summary_recovery_v009.json"),
        "quarantine_receipt": BASE.file_row(V009_RUN / "quarantine_receipt_v009.json"),
        "import_receipt_schema": V009_IMPORT_SCHEMA,
        "import_receipt_status": V009_IMPORT_PASS,
        "import_process_id": 36612,
        "import_process_exit_code": 0,
        "import_process_fatal_patterns": [],
        "wrapper_error": V009_POWERSHELL_ERROR,
        "powershell_failure_line": 167,
        "intentional_empty_json_key_paths": [V009_EMPTY_KEY_PATH],
        "powershell_full_receipt_parse_forbidden": True,
        "python_exact_receipt_parser_required": True,
        "validator_was_launched": False,
        "semantic_import_failure": False,
        "package_sha256": copy.deepcopy(state["package_hashes"]),
        "namespace_disk_files": copy.deepcopy(imported["namespace_disk_files"]),
        "asset_registry_packages": copy.deepcopy(imported["asset_registry_packages"]),
        "import_assets_canonical_sha256": object_hash(imported["assets"]),
        "fresh_validation_assets_canonical_sha256": object_hash(
            expected_fresh_assets(imported)),
        "fresh_assets_transform": (
            "EXACT_V009_IMPORT_ASSETS_WITH_ONLY_ALL_PERSISTED_DEPENDENCY_"
            "CHECK_REQUIRED_FIELDS_AND_TOP_LEVEL_VERIFIED_SET_TRUE"),
        "source_snapshot": copy.deepcopy(imported["source_after"]),
        "protected_snapshot": copy.deepcopy(imported["protected_after"]),
        "destination_files": copy.deepcopy(state["destination_snapshot"]),
        "q6_quarantine": copy.deepcopy(state["q6_snapshot"]),
        "startup_build_tool_observation": copy.deepcopy(state["log_observation"]),
    }
    wrapper["binding_sha256"] = object_hash(wrapper)
    return {
        "$schema": "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v10",
        "status": STATUS,
        "generated_utc": generated_utc,
        "acknowledgement": RUN_ACK_TOKEN,
        "project_root": str(PROJECT),
        "original_authorities": copy.deepcopy(v009["original_authorities"]),
        "approved_source": copy.deepcopy(v009["approved_source"]),
        "protected_project": copy.deepcopy(v009["protected_project"]),
        "incident_chain": copy.deepcopy(v009["incident_chain"]),
        "stale_preliminary_v007": copy.deepcopy(v009["stale_preliminary_v007"]),
        "stale_preliminary_v008": copy.deepcopy(v009["stale_preliminary_v008"]),
        "exact_prior_all_file_closures": copy.deepcopy(
            v009["exact_prior_all_file_closures"]),
        "prior_quarantines": copy.deepcopy(v009["prior_quarantines"]),
        "partial_packages": copy.deepcopy(v009["partial_packages"]),
        "slot_normalization": copy.deepcopy(v009["slot_normalization"]),
        "runtime_uv_sanitization": copy.deepcopy(v009["runtime_uv_sanitization"]),
        "runtime_bounds_coordinate_conversion": copy.deepcopy(
            v009["runtime_bounds_coordinate_conversion"]),
        "exact_ue_enum_validation": copy.deepcopy(v009["exact_ue_enum_validation"]),
        "material_input_name_canonicalization": copy.deepcopy(
            v009["material_input_name_canonicalization"]),
        "completed_v009_import": wrapper,
        "ubt_startup_suppression": copy.deepcopy(state["target_source"]),
        "lane": v010_lane_snapshot(v009),
        "result_topology": result_topology(),
        "policy": {
            **copy.deepcopy(v009["policy"]),
            "unreal_launch_authorized_by_freeze": False,
            "validation_only_recovery": True,
            "existing_v009_packages_are_immutable": True,
            "quarantine_move_authorized": False,
            "delete_copy_import_reimport_save_authorized": False,
            "importer_process_authorized": False,
            "exactly_one_read_only_validator_process_required": True,
            "powershell_5_1_compatible_runner_required": True,
            "powershell_full_v009_or_v010_receipt_parse_forbidden": True,
            "python_exact_empty_key_receipt_validation_required": True,
            "ubt_validate_platforms_must_be_suppressed": True,
            "ubt_log_tokens_are_fatal": True,
            "post_exit_all_file_and_package_hash_closure_required": True,
            "no_write_full_candidate_payload_preflight_required": True,
        },
    }


def validate_candidate_payload(payload: dict, state: dict) -> None:
    generated = payload.get("generated_utc")
    if not isinstance(generated, str):
        raise RecoveryError("v010 generated timestamp type drift")
    try:
        datetime.fromisoformat(generated)
    except ValueError as exc:
        raise RecoveryError("v010 generated timestamp is not ISO-8601") from exc
    if generated != candidate_generated_utc(state):
        raise RecoveryError("v010 generated timestamp is not exact lane-state timestamp")
    if payload != build_candidate_payload(state, generated):
        raise RecoveryError("v010 full candidate payload differs from reconstructed authority")
    wrapper = copy.deepcopy(payload["completed_v009_import"])
    declared = wrapper.pop("binding_sha256", None)
    if declared != object_hash(wrapper):
        raise RecoveryError("v010 completed-v009-import binding hash drift")
    if (payload["lane"]["file_count"] != 48
            or payload["result_topology"]["unreal_process_count"] != 1
            or payload["result_topology"]["import_process_count"] != 0
            or payload["policy"]["quarantine_move_authorized"] is not False
            or payload["policy"]["importer_process_authorized"] is not False):
        raise RecoveryError("v010 lane/process/no-import safety closure drift")
    verify_target_platform_source()


def dry_build_payload(require_output_absent: bool = True) -> tuple[dict, str, int]:
    if require_output_absent and (OUTPUT.exists() or OUTPUT_SHA.exists()):
        raise RecoveryError("v010 dry-build requires absent contract and sidecar")
    if RECOVERY_AUDIT_ROOT.exists():
        raise RecoveryError("v010 dry-build requires absent result root")
    state = authority_state()
    payload = build_candidate_payload(state, candidate_generated_utc(state))
    validate_candidate_payload(payload, state)
    serialized = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    validate_candidate_payload(strict_json_text(serialized.decode("utf-8")), state)
    return payload, hashlib.sha256(serialized).hexdigest().upper(), len(serialized)


def create_contract(acknowledgement: str) -> None:
    if acknowledgement != ACK_TOKEN:
        raise RecoveryError("exact v010 recovery-freeze acknowledgement missing")
    if OUTPUT.exists() or OUTPUT_SHA.exists():
        raise RecoveryError("refusing to overwrite v010 recovery contract or sidecar")
    payload, expected_digest, expected_size = dry_build_payload()
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if len(serialized.encode("utf-8")) != expected_size:
        raise RecoveryError("v010 serialized size changed after no-write preflight")
    OUTPUT.write_text(serialized, encoding="utf-8", newline="\n")
    digest = BASE.sha256(OUTPUT)
    if digest != expected_digest:
        raise RecoveryError("v010 written contract hash differs from dry-build")
    OUTPUT_SHA.write_text(
        f"{digest}  {OUTPUT.name}\n", encoding="ascii", newline="\n")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V010_CONTRACT_FROZEN")
    print(digest)


def load_frozen() -> tuple[dict, dict]:
    state = authority_state()
    if not OUTPUT.is_file() or not OUTPUT_SHA.is_file():
        raise RecoveryError("v010 recovery contract/sidecar absent")
    digest = BASE.sha256(OUTPUT)
    if OUTPUT_SHA.read_text(encoding="ascii") != f"{digest}  {OUTPUT.name}\n":
        raise RecoveryError("v010 recovery sidecar drift")
    payload = strict_json_file(OUTPUT)
    validate_candidate_payload(payload, state)
    BASE.verify_snapshot(payload["lane"], "v010 prepared validation-only lane")
    return payload, state


def verify_pre_validation() -> None:
    payload, state = load_frozen()
    if RECOVERY_AUDIT_ROOT.exists():
        raise RecoveryError("v010 result root already exists; one-use validation consumed")
    verify_destination(state["imported"])
    exact_v009_run_snapshot()
    verify_v009_quarantine(state["v009"])
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V010_PRE_VALIDATION_REVERIFIED")
    print(BASE.sha256(OUTPUT))


def exact_v010_run_root(raw: str) -> Path:
    path = Path(raw).resolve()
    if (path.parent != RECOVERY_AUDIT_ROOT.resolve()
            or not re.fullmatch(r"\d{8}T\d{6}Z-[0-9a-f]{8}", path.name)
            or not path.is_dir()):
        raise RecoveryError("v010 run root identity/path drift: " + str(path))
    return path


def validate_v010_receipt(payload: dict, contract: dict, run_root: Path) -> None:
    topology = contract["result_topology"]["validation"]
    completed = contract["completed_v009_import"]
    expected_lane = {
        "file_count": contract["lane"]["file_count"],
        "inventory_sha256": contract["lane"]["inventory_sha256"],
    }
    if empty_key_paths(payload) != [V009_EMPTY_KEY_PATH]:
        raise RecoveryError("v010 validation receipt empty-key path closure drift")
    if (payload.get("$schema") != topology["$schema"]
            or payload.get("status") != topology["pass_status"]
            or payload.get("recovery_contract_sha256") != BASE.sha256(OUTPUT)
            or payload.get("v009_recovery_contract_sha256") != V009_CONTRACT_SHA256
            or payload.get("v009_import_receipt_sha256") != V009_IMPORT_RECEIPT_SHA256
            or payload.get("v009_wrapper_failure_summary_sha256") != V009_SUMMARY_SHA256
            or payload.get("import_process_id") != 36612
            or int(payload.get("validator_process_id", -1)) <= 0
            or payload.get("validator_process_id") == 36612
            or payload.get("distinct_process_verified") is not True
            or payload.get("destination_namespace")
            != "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040Runtime_v001"
            or payload.get("editor_bootstrap_world") != "/Engine/Maps/Entry.Entry"
            or payload.get("asset_mutations") != []
            or payload.get("mesh_count") != 4
            or payload.get("authored_lod_count") != 12
            or payload.get("texture_count") != 3
            or payload.get("material_count") != 4
            or payload.get("package_count") != 11
            or payload.get("package_sha256_before_loads")
            != completed["package_sha256"]
            or payload.get("package_sha256_after_loads")
            != completed["package_sha256"]
            or payload.get("namespace_before") != completed["namespace_disk_files"]
            or payload.get("namespace_after") != completed["namespace_disk_files"]
            or payload.get("asset_registry_packages_before")
            != completed["asset_registry_packages"]
            or payload.get("asset_registry_packages_after")
            != completed["asset_registry_packages"]
            or payload.get("source_before") != completed["source_snapshot"]
            or payload.get("source_after") != completed["source_snapshot"]
            or payload.get("protected_before") != completed["protected_snapshot"]
            or payload.get("protected_after") != completed["protected_snapshot"]
            or payload.get("prepared_lane_before") != expected_lane
            or payload.get("prepared_lane_after") != expected_lane
            or object_hash(payload.get("assets"))
            != completed["fresh_validation_assets_canonical_sha256"]
            or payload.get("all_package_hashes_unchanged") is not True
            or payload.get("persisted_asset_registry_dependency_closure_verified") is not True
            or payload.get("asset_mutation_count") != 0
            or payload.get("failures") != []
            or payload.get("project_maps_loaded_or_saved") != []
            or payload.get("import_or_reimport_process_count") != 0
            or payload.get("ubt_startup_guard_environment") != {
                "name": "UE_SKIP_UBT_SDK_SETUP",
                "required_value": "1",
                "observed_value": "1",
            }):
        raise RecoveryError("v010 fresh validation receipt identity/hash/safety drift")
    expected_writes = {
        str(run_root / topology["receipt_filename"]),
        str(run_root / topology["failure_filename"]),
    }
    if set(payload.get("writes_authorized", [])) != expected_writes:
        raise RecoveryError("v010 validation receipt write authority drift")


def verify_post_validation(run_root_raw: str) -> None:
    contract, state = load_frozen()
    run_root = exact_v010_run_root(run_root_raw)
    topology = contract["result_topology"]
    expected_names = set(topology["validator_logs"]) | {
        topology["validation"]["receipt_filename"]}
    children = list(run_root.iterdir())
    if any(not path.is_file() or path.is_symlink() for path in children):
        raise RecoveryError("v010 post-validator run contains a directory/link/non-file child")
    actual = {path.name: path for path in children}
    if set(actual) != expected_names or len(actual) != 4:
        raise RecoveryError("v010 post-validator exact four-file closure drift: " + repr(sorted(actual)))
    receipt_path = actual[topology["validation"]["receipt_filename"]]
    receipt = strict_json_file(receipt_path)
    validate_v010_receipt(receipt, contract, run_root)
    combined = "\n".join(
        actual[name].read_text(encoding="utf-8", errors="replace")
        for name in topology["validator_logs"]
    )
    forbidden = (
        "Fatal error:", "Assertion failed:", "Unhandled Exception:", "appError called",
        "Ensure condition failed", "ModeManager", "Launching UnrealBuildTool",
        "UnrealBuildTool", "Build.bat", "-Mode=ValidatePlatforms", "AutoSDKInfo.txt",
        "UBT AutoSDK ReturnCode",
    )
    found = [token for token in forbidden if token in combined]
    if found:
        raise RecoveryError("v010 validator fatal/build-tool log token drift: " + repr(found))
    if ("LINE_BOSS_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V010_VALIDATION_PASS"
            not in combined or "Editor shut down" not in combined):
        raise RecoveryError("v010 validation PASS/natural-exit marker drift")
    verify_destination(state["imported"])
    exact_v009_run_snapshot()
    verify_v009_quarantine(state["v009"])
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V010_POST_VALIDATION_REVERIFIED")
    print(BASE.sha256(receipt_path))


def verify_final(run_root_raw: str) -> None:
    contract, state = load_frozen()
    run_root = exact_v010_run_root(run_root_raw)
    topology = contract["result_topology"]
    expected_names = set(topology["validator_logs"]) | {
        topology["validation"]["receipt_filename"],
        topology["summary"]["filename"],
    }
    children = list(run_root.iterdir())
    if any(not path.is_file() or path.is_symlink() for path in children):
        raise RecoveryError("v010 final run contains a directory/link/non-file child")
    actual = {path.name: path for path in children}
    if set(actual) != expected_names or len(actual) != 5:
        raise RecoveryError("v010 final exact five-file closure drift: " + repr(sorted(actual)))
    receipt_path = actual[topology["validation"]["receipt_filename"]]
    receipt = strict_json_file(receipt_path)
    validate_v010_receipt(receipt, contract, run_root)
    summary = strict_json_file(actual[topology["summary"]["filename"]])
    process = summary.get("validation_process", {})
    if (empty_key_paths(summary) != []
            or summary.get("$schema") != topology["summary"]["$schema"]
            or summary.get("status") != topology["summary"]["pass_status"]
            or summary.get("recovery_contract_sha256") != BASE.sha256(OUTPUT)
            or summary.get("v009_recovery_contract_sha256") != V009_CONTRACT_SHA256
            or summary.get("v009_import_receipt_sha256") != V009_IMPORT_RECEIPT_SHA256
            or summary.get("v009_wrapper_failure_summary_sha256") != V009_SUMMARY_SHA256
            or summary.get("editor_process_count") != 1
            or summary.get("import_process_count") != 0
            or summary.get("content_move_count") != 0
            or summary.get("no_build_tool_invoked") is not True
            or summary.get("exact_ubt_command_line_matches") != 0
            or summary.get("environment_restoration_verified") is not True
            or summary.get("error") is not None
            or process.get("process_id") != receipt.get("validator_process_id")
            or process.get("exit_code") != 0
            or process.get("fatal_or_build_tool_log_patterns") != []
            or process.get("log_sha256") != BASE.sha256(
                actual["fresh_process_validation_recovery_v010.log"])
            or process.get("stdout_sha256") != BASE.sha256(
                actual["fresh_process_validation_recovery_v010.stdout.log"])
            or process.get("stderr_sha256") != BASE.sha256(
                actual["fresh_process_validation_recovery_v010.stderr.log"])
            or summary.get("validation_receipt", {}).get("sha256") != BASE.sha256(receipt_path)
            or summary.get("validation_receipt", {}).get("status")
            != topology["validation"]["pass_status"]
            or summary.get("post_exit_package_sha256")
            != contract["completed_v009_import"]["package_sha256"]
            or "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V010_POST_VALIDATION_REVERIFIED"
            not in str(summary.get("post_exit_reverify", ""))):
        raise RecoveryError("v010 final summary/receipt/process/log/package binding drift")
    verify_destination(state["imported"])
    exact_v009_run_snapshot()
    verify_v009_quarantine(state["v009"])
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V010_FINAL_FIVE_FILE_REVERIFIED")
    print(BASE.sha256(actual[topology["summary"]["filename"]]))


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
        print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V010_NO_WRITE_FULL_PAYLOAD_PREFLIGHT")
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
