"""Offline incident contract for guarded Cairnwell v012 validation-only recovery."""

from __future__ import annotations

import argparse
import copy
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
import prepare_cairnwell_2040_runtime_v001_recovery_v011 as prior


BASE = prior.BASE
RecoveryError = prior.RecoveryError
OUTPUT = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v012_contract.json"
OUTPUT_SHA = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v012_contract.sha256"
V011_CONTRACT = prior.OUTPUT
V011_SIDECAR = prior.OUTPUT_SHA
V011_CONTRACT_SHA256 = (
    "09A223675EC26F93F85EA2BE8B97568014AA9073681094C46EE04BDADC18719F"
)
V011_CONTRACT_BYTES = 159507
V011_SIDECAR_SHA256 = (
    "B8343772ABCDF81909067CF8B9594B0817B7766AC53177716B2F8AA65385B8B4"
)
V011_SIDECAR_BYTES = 122
V011_SIDECAR_TEXT = f"{V011_CONTRACT_SHA256}  {V011_CONTRACT.name}\n"
V011_RUN_ID = "20260815T154711Z-18d3ce40"
V011_RUN = prior.RECOVERY_AUDIT_ROOT / V011_RUN_ID
V011_PROCESS_ID = 40420
V011_FAILURE = "fresh_process_validation_failure_recovery_v011.json"
V011_SUMMARY = "lane_summary_recovery_v011.json"
V011_RUN_FILES = {
    V011_FAILURE: (65920, "92594B9EED92D7FF1DEBC6210FE2956E5FD84B46B108D71EAC05C7617FA0CAB4"),
    "fresh_process_validation_recovery_v011.log": (
        385536, "F0A395A69A2FBFF6813DF6EDDB6FA8CFDC6225426BDE77C19056EDE7BAE7871C"),
    "fresh_process_validation_recovery_v011.stderr.log": (
        0, "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"),
    "fresh_process_validation_recovery_v011.stdout.log": (
        386887, "CFB42DA3E098E695CB77AF6019D74364A14BF0D2E093D5DB8184C923EA7612CA"),
    V011_SUMMARY: (3344, "A5A995A7D4C4ADE69577CCBEF464283F191C359713213CD30309F33920B5733A"),
}
V011_FAILURE_ERROR = "v011 fresh validation receipt exact chronology/content drift"
V011_FAILURE_STATUS = (
    "FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V011_"
    "FRESH_PROCESS_VALIDATION"
)
V011_SUMMARY_STATUS = (
    "FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V011_VALIDATION_ONLY_LANE"
)
ACTUAL_FRESH_ASSETS_SHA256 = (
    "7E8A56991C48F8AEC017C0B4308E220729388A076ABC17C731F70405243B985B"
)
RECOVERY_AUDIT_ROOT = PROJECT / (
    "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "UnrealImportLane_v001/Recovery_v012"
)
ACK_TOKEN = "FREEZE_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012_ONCE"
RUN_ACK_TOKEN = "VALIDATE_CAIRNWELL_2040_RUNTIME_V001_V009_IMPORT_V012_ONCE"
STATUS = (
    "FROZEN__CAIRNWELL_2040_RUNTIME_V001_INCIDENT_CHAINED_RECOVERY_V012__"
    "READY_FOR_ONE_SHOT_VALIDATION_ONLY_OF_V009_PASS_IMPORT"
)
V012_ADDITIONS = {
    "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012.md",
    "Scripts/prepare_cairnwell_2040_runtime_v001_recovery_v012.py",
    "Scripts/validate_cairnwell_2040_runtime_recovery_v012.py",
    "Scripts/run_cairnwell_2040_runtime_validation_recovery_v012.ps1",
    "Scripts/tests/test_cairnwell_2040_runtime_validation_recovery_v012.py",
    "Scripts/cairnwell_2040_runtime_v001_recovery_v011_contract.json",
    "Scripts/cairnwell_2040_runtime_v001_recovery_v011_contract.sha256",
}
VALIDATION_PREFIX = "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v012/"
VALIDATION_RECEIPT = "fresh_process_validation_receipt_recovery_v012.json"
VALIDATION_FAILURE = "fresh_process_validation_failure_recovery_v012.json"
SUMMARY_NAME = "lane_summary_recovery_v012.json"
VALIDATOR_LOGS = [
    "fresh_process_validation_recovery_v012.log",
    "fresh_process_validation_recovery_v012.stdout.log",
    "fresh_process_validation_recovery_v012.stderr.log",
]
VALIDATION_PASS = (
    "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012_DISTINCT_FRESH_PROCESS__"
    "READ_ONLY_RELOAD_OF_V009_PASS_IMPORT__EXACT_PERSISTED_DEPENDENCIES__"
    "11_PACKAGE_HASHES_UNCHANGED"
)
SUMMARY_PASS = (
    "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012_GUARDED_"
    "VALIDATION_ONLY_OF_V009_PASS_IMPORT"
)
PRE_VALIDATION_PASS = (
    "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012_PRE_VALIDATION_REVERIFIED"
)
POST_VALIDATION_PASS = (
    "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012_POST_VALIDATION_REVERIFIED"
)
FINAL_PASS = (
    "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012_FINAL_FIVE_FILE_REVERIFIED"
)
TEXTURE_DEPENDENCIES = [
    "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040Runtime_v001/"
    "Textures/T_LB_C2040_Emerald_BaseColor_v001",
    "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040Runtime_v001/"
    "Textures/T_LB_C2040_Emerald_MRBodyMask_v001",
    "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040Runtime_v001/"
    "Textures/T_LB_C2040_Emerald_Normal_v001",
]
MODULE_DEPENDENCIES = {
    "BIW_AutomotiveSkeleton": [
        "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040Runtime_v001/"
        "Materials/M_LB_C2040_BIWGalvanized_v001"],
    "BIW_UnderbodySubset": [
        "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040Runtime_v001/"
        "Materials/M_LB_C2040_EDCoat_v001"],
    "EmeraldBodyVisualAuthority": [
        "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040Runtime_v001/"
        "Materials/M_LB_C2040_BodyPaintTintPBR_v001"],
    "EmeraldRollingGearVisualAuthority": [
        "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040Runtime_v001/"
        "Materials/M_LB_C2040_RollingGearPBR_v001"],
}
CACHE_ROOT = PROJECT / "Intermediate/CachedAssetRegistry"
CACHE_ROWS = {
    "Intermediate/CachedAssetRegistry/CachedAssetRegistry_0.ref": {
        "bytes": 58,
        "mtime_ns": 1786808934146707100,
        "sha256": "F1D36ED33E1EBDD230A174483A7CA079E22E0EB800DC88458A1B0769BBAA9D03",
    },
    ("Intermediate/CachedAssetRegistry/"
     "CachedAssetRegistry_0_73F8A5E94BBCC96BE62C7B8A7E6D74B0.bin"): {
        "bytes": 1152845102,
        "mtime_ns": 1786808934144699900,
        "sha256": "2166ECE1DA59AF67C8202B93624E110FB647DDA5F93A28773368D47D1C1A8F40",
    },
}
ASSET_GATHERER_SOURCE = Path(
    r"C:\Program Files\Epic Games\UE_5.8\Engine\Source\Runtime\AssetRegistry\Private\AssetDataGatherer.cpp"
)
ASSET_GATHERER_SOURCE_BYTES = 245235
ASSET_GATHERER_SOURCE_SHA256 = (
    "9B62B0B7AFF852029CA82576570B5F9A9F3791E605667B1D20F0B7896511D6CC"
)
VEHICLE_MODEL_ID = "CAIRNWELL_2040"
DEVELOPMENT_RECIPE_ID = "CAIRNWELL_2040_DEVELOPMENT_RECIPE_V001"
CURRENT_GEOMETRY_AUTHORITY_ID = "Cairnwell2040Runtime_v001_V009ImportedGeometry"


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


def corrected_fresh_assets(state: dict) -> dict:
    assets = prior.prior.expected_fresh_assets(state["imported"])
    assets["materials"]["body"]["texture_dependencies"] = copy.deepcopy(
        TEXTURE_DEPENDENCIES)
    assets["materials"]["rolling_gear"]["texture_dependencies"] = copy.deepcopy(
        TEXTURE_DEPENDENCIES)
    for role, dependencies in MODULE_DEPENDENCIES.items():
        assets["modules"][role]["persisted_runtime_dependencies"] = copy.deepcopy(
            dependencies)
    if object_hash(assets) != ACTUAL_FRESH_ASSETS_SHA256:
        raise RecoveryError("v012 corrected fresh dependency authority hash drift")
    return assets


def verify_asset_registry_cache_snapshot() -> dict:
    if not CACHE_ROOT.is_dir():
        raise RecoveryError("Intermediate CachedAssetRegistry root is absent")
    children = list(CACHE_ROOT.iterdir())
    if any(not path.is_file() or path.is_symlink() for path in children):
        raise RecoveryError("CachedAssetRegistry contains directory/link/non-file child")
    actual_paths = {BASE.relative(path) for path in children}
    if actual_paths != set(CACHE_ROWS):
        raise RecoveryError(
            "CachedAssetRegistry exact two-file path closure drift: "
            + repr(sorted(actual_paths)))
    rows = []
    for relative, expected in CACHE_ROWS.items():
        path = PROJECT / relative
        actual = BASE.file_row(path)
        if any(actual[key] != expected[key]
               for key in ("bytes", "mtime_ns", "sha256")):
            raise RecoveryError("CachedAssetRegistry byte/mtime/hash drift: " + relative)
        rows.append(actual)
    return {
        "root": BASE.relative(CACHE_ROOT),
        "file_count": 2,
        "files": sorted(rows, key=lambda row: row["path"].casefold()),
        "inventory_sha256": BASE.canonical_hash(rows),
    }


def verify_asset_registry_cache_source() -> dict:
    if (not ASSET_GATHERER_SOURCE.is_file()
            or ASSET_GATHERER_SOURCE.stat().st_size != ASSET_GATHERER_SOURCE_BYTES
            or BASE.sha256(ASSET_GATHERER_SOURCE)
            != ASSET_GATHERER_SOURCE_SHA256):
        raise RecoveryError("installed UE5.8 AssetDataGatherer source drift")
    text = ASSET_GATHERER_SOURCE.read_text(encoding="utf-8", errors="replace")
    if ('TEXT("NoAssetRegistryCacheWrite")' not in text
            or "bGatherCacheWriteEnabled = !bNoAssetRegistryCache"
            not in text
            or "EFeatureEnabledReadWrite::NeverWrite" not in text):
        raise RecoveryError("installed UE5.8 cache-write suppression source tokens drift")
    return {
        "path": str(ASSET_GATHERER_SOURCE),
        "bytes": ASSET_GATHERER_SOURCE_BYTES,
        "sha256": ASSET_GATHERER_SOURCE_SHA256,
        "command_line_flag": "-NoAssetRegistryCacheWrite",
        "parse_and_gather_write_disable_lines": "201-212",
        "discovery_cache_never_write_lines": "238-249",
    }


def exact_v011_run_snapshot() -> dict:
    if not V011_RUN.is_dir():
        raise RecoveryError("exact consumed Recovery_v011 run is absent")
    children = list(V011_RUN.iterdir())
    if any(not path.is_file() or path.is_symlink() for path in children):
        raise RecoveryError("Recovery_v011 contains directory/link/non-file child")
    if {path.name for path in children} != set(V011_RUN_FILES):
        raise RecoveryError("Recovery_v011 exact five-file closure drift")
    rows = []
    for name, (size, digest) in V011_RUN_FILES.items():
        path = V011_RUN / name
        if path.stat().st_size != size or BASE.sha256(path) != digest:
            raise RecoveryError("Recovery_v011 evidence bytes drift: " + name)
        rows.append(BASE.file_row(path))
    return {
        "root": BASE.relative(V011_RUN),
        "file_count": 5,
        "files": sorted(rows, key=lambda row: row["path"].casefold()),
        "inventory_sha256": BASE.canonical_hash(rows),
    }


def exact_v011_pair() -> tuple[dict, dict]:
    if (not V011_CONTRACT.is_file()
            or V011_CONTRACT.stat().st_size != V011_CONTRACT_BYTES
            or BASE.sha256(V011_CONTRACT) != V011_CONTRACT_SHA256):
        raise RecoveryError("consumed v011 contract bytes drift")
    if (not V011_SIDECAR.is_file()
            or V011_SIDECAR.stat().st_size != V011_SIDECAR_BYTES
            or BASE.sha256(V011_SIDECAR) != V011_SIDECAR_SHA256
            or V011_SIDECAR.read_text(encoding="ascii") != V011_SIDECAR_TEXT):
        raise RecoveryError("consumed v011 sidecar bytes/text drift")
    payload, state = prior.load_frozen()
    if payload.get("$schema") != (
            "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v11"):
        raise RecoveryError("consumed v011 contract schema drift")
    return payload, state


def validate_v011_execution(v011: dict, state: dict) -> dict:
    snapshot = exact_v011_run_snapshot()
    failure = strict_json_file(V011_RUN / V011_FAILURE)
    summary = strict_json_file(V011_RUN / V011_SUMMARY)
    if (failure.get("$schema") != prior.result_topology()["validation"]["$schema"]
            or failure.get("status") != V011_FAILURE_STATUS
            or failure.get("error") != V011_FAILURE_ERROR
            or failure.get("process_id") != V011_PROCESS_ID
            or failure.get("validator_process_id") != V011_PROCESS_ID
            or failure.get("asset_mutation_count") != 0
            or failure.get("import_or_reimport_process_count") != 0
            or failure.get("failures") != []
            or failure.get("all_package_hashes_unchanged") is not True
            or failure.get("persisted_asset_registry_dependency_closure_verified")
            is not True
            or failure.get("namespace_before") != failure.get("namespace_after")
            or failure.get("package_sha256_before_loads")
            != failure.get("package_sha256_after_loads")
            or failure.get("package_sha256_before_loads")
            != v011["completed_v009_import"]["package_sha256"]
            or failure.get("source_before") != failure.get("source_after")
            or failure.get("protected_before") != failure.get("protected_after")
            or failure.get("prepared_lane_before") != failure.get("prepared_lane_after")):
        raise RecoveryError("Recovery_v011 semantic/package/source evidence drift")
    expected = prior.receipt_fixture(
        v011, state, V011_RUN, V011_PROCESS_ID,
        failure["generated_utc"], failure["engine_version"])
    expected["assets"] = corrected_fresh_assets(state)
    observed = {key: copy.deepcopy(failure[key]) for key in expected}
    observed["status"] = prior.VALIDATION_PASS
    if object_hash(observed) != object_hash(expected):
        raise RecoveryError("Recovery_v011 pre-exception receipt has non-dependency drift")
    expected_extra = {
        "error", "traceback", "package_hashes_before",
        "namespace_preserved_for_recovery", "automatic_cleanup"}
    if set(failure) - set(expected) != expected_extra:
        raise RecoveryError("Recovery_v011 failure-receipt extra key closure drift")
    if (V011_FAILURE_ERROR not in str(failure.get("traceback", ""))
            or failure.get("package_hashes_before")
            != v011["completed_v009_import"]["package_sha256"]
            or failure.get("namespace_preserved_for_recovery")
            != v011["completed_v009_import"]["namespace_disk_files"]
            or failure.get("automatic_cleanup")
            != "NOT_PERFORMED__READ_ONLY_VALIDATOR"):
        raise RecoveryError("Recovery_v011 exact failure wrapper evidence drift")
    process = summary.get("validation_process", {})
    if (summary.get("$schema") != prior.result_topology()["summary"]["$schema"]
            or summary.get("status") != V011_SUMMARY_STATUS
            or summary.get("acknowledgement") != prior.RUN_ACK_TOKEN
            or summary.get("run_root") != str(V011_RUN)
            or summary.get("recovery_contract_sha256") != V011_CONTRACT_SHA256
            or summary.get("environment_restoration_verified") is not True
            or summary.get("editor_process_count") != 1
            or summary.get("import_process_count") != 0
            or summary.get("content_move_count") != 0
            or summary.get("error")
            != "V011 read-only validator emitted a failure receipt despite strict exit gate"
            or process.get("process_id") != V011_PROCESS_ID
            or process.get("exit_code") != 0
            or process.get("fatal_or_build_tool_log_patterns") != []
            or process.get("log_sha256") != V011_RUN_FILES[
                "fresh_process_validation_recovery_v011.log"][1]
            or process.get("stdout_sha256") != V011_RUN_FILES[
                "fresh_process_validation_recovery_v011.stdout.log"][1]
            or process.get("stderr_sha256") != V011_RUN_FILES[
                "fresh_process_validation_recovery_v011.stderr.log"][1]):
        raise RecoveryError("Recovery_v011 wrapper/process identity drift")
    combined = "\n".join(
        (V011_RUN / name).read_text(encoding="utf-8", errors="replace")
        for name in (
            "fresh_process_validation_recovery_v011.log",
            "fresh_process_validation_recovery_v011.stdout.log",
            "fresh_process_validation_recovery_v011.stderr.log"))
    forbidden = (
        "Fatal error:", "Assertion failed:", "Unhandled Exception:",
        "appError called", "Ensure condition failed", "Launching UnrealBuildTool",
        "UnrealBuildTool", "Build.bat", "-Mode=ValidatePlatforms",
        "AutoSDKInfo.txt", "UBT AutoSDK ReturnCode")
    found = [token for token in forbidden if token in combined]
    if found or "Editor shut down" not in combined:
        raise RecoveryError("Recovery_v011 fatal/UBT/natural-exit log drift: " + repr(found))
    cache_log_occurrences = {}
    for name in (
            "fresh_process_validation_recovery_v011.log",
            "fresh_process_validation_recovery_v011.stdout.log"):
        log_text = (V011_RUN / name).read_text(encoding="utf-8", errors="replace")
        occurrences = {
            "asset_registry_cache_written": log_text.count(
                "Asset registry cache written as"),
            "orphan_cache_deleted": log_text.count("deleted (orphaned"),
            "post_write_cleanup": log_text.count(
                "CleanupOrphanedCacheFiles (PostWrite)"),
        }
        if occurrences != {
                "asset_registry_cache_written": 1,
                "orphan_cache_deleted": 1,
                "post_write_cleanup": 2}:
            raise RecoveryError(
                "Recovery_v011 AssetRegistry-cache side-effect evidence drift: "
                + name + " " + repr(occurrences))
        cache_log_occurrences[name] = occurrences
    dependency_diff = {
        "materials": {
            role: {"field": "texture_dependencies", "expected": [],
                   "actual": copy.deepcopy(TEXTURE_DEPENDENCIES)}
            for role in ("body", "rolling_gear")
        },
        "modules": {
            role: {"field": "persisted_runtime_dependencies", "expected": [],
                   "actual": copy.deepcopy(dependencies)}
            for role, dependencies in MODULE_DEPENDENCIES.items()
        },
        "exact_changed_field_count": 6,
        "corrected_fresh_assets_canonical_sha256": ACTUAL_FRESH_ASSETS_SHA256,
    }
    incident = {
        "classification": (
            "V011_READ_ONLY_VALIDATION_SEMANTIC_PASS__OFFLINE_RECEIPT_FIXTURE_"
            "OMITTED_EXACT_PERSISTED_DEPENDENCY_LISTS__V012_VALIDATION_ONLY"),
        "run_id": V011_RUN_ID,
        "process_id": V011_PROCESS_ID,
        "run_snapshot": snapshot,
        "failure_receipt": BASE.file_row(V011_RUN / V011_FAILURE),
        "summary": BASE.file_row(V011_RUN / V011_SUMMARY),
        "logs": {
            name: BASE.file_row(V011_RUN / name)
            for name in VALIDATOR_LOGS_FROM_V011
        },
        "unreal_exit_code": 0,
        "semantic_asset_validation_completed": True,
        "package_hashes_unchanged": True,
        "source_protected_lane_unchanged": True,
        "import_reimport_or_content_mutation_count": 0,
        "fatal_ensure_or_ubt_log_patterns": [],
        "natural_editor_exit_verified": True,
        "asset_registry_cache_side_effect": {
            "classification": (
                "V011_READ_ONLY_CONTENT_VALIDATION_WROTE_PROJECT_ASSET_REGISTRY_"
                "CACHE_AND_DELETED_ONE_ORPHAN__V012_MUST_SUPPRESS_AND_PROVE_"
                "EXACT_CACHE_INVARIANCE"),
            "pre_v011_cache_snapshot_preserved": False,
            "post_v011_current_snapshot_is_v012_pre_validation_authority": True,
            "per_primary_log_exact_occurrences": cache_log_occurrences,
        },
        "dependency_fixture_diff": dependency_diff,
    }
    incident["binding_sha256"] = object_hash(incident)
    return incident


VALIDATOR_LOGS_FROM_V011 = [
    "fresh_process_validation_recovery_v011.log",
    "fresh_process_validation_recovery_v011.stdout.log",
    "fresh_process_validation_recovery_v011.stderr.log",
]


def v012_lane_snapshot(v011: dict) -> dict:
    paths = {row["path"] for row in v011["lane"]["files"]} | V012_ADDITIONS
    snapshot = BASE.inventory([PROJECT / path for path in paths])
    if (snapshot["file_count"] != 62
            or {row["path"] for row in snapshot["files"]} != paths):
        raise RecoveryError("v012 prepared-lane exact 62-file path closure drift")
    return snapshot


def result_topology() -> dict:
    return {
        "audit_root": BASE.relative(RECOVERY_AUDIT_ROOT),
        "run_root_pattern": BASE.relative(RECOVERY_AUDIT_ROOT) + "/<UTC>-<GUID8>",
        "validation": {
            "receipt_filename": VALIDATION_RECEIPT,
            "failure_filename": VALIDATION_FAILURE,
            "$schema": VALIDATION_PREFIX + "fresh-process-validation/v12",
            "pass_status": VALIDATION_PASS,
            "package_hash_fields": [
                "package_sha256_before_loads", "package_sha256_after_loads"],
        },
        "summary": {
            "filename": SUMMARY_NAME,
            "$schema": VALIDATION_PREFIX + "validation-only-lane-summary/v12",
            "pass_status": SUMMARY_PASS,
            "package_hash_field": "post_exit_package_sha256",
        },
        "validator_logs": list(VALIDATOR_LOGS),
        "unreal_process_count": 1,
        "import_process_count": 0,
    }


def authority_state() -> dict:
    v011, state = exact_v011_pair()
    incident = validate_v011_execution(v011, state)
    prior.prior.verify_destination(state["imported"])
    lane = v012_lane_snapshot(v011)
    cache_snapshot = verify_asset_registry_cache_snapshot()
    cache_source = verify_asset_registry_cache_source()
    return {
        **state, "v011": v011, "v011_incident": incident,
        "v012_lane": lane, "asset_registry_cache": cache_snapshot,
        "asset_registry_cache_source": cache_source,
    }


def candidate_generated_utc(state: dict) -> str:
    latest = max(int(row["mtime_ns"]) for row in state["v012_lane"]["files"])
    return datetime.fromtimestamp(
        latest / 1_000_000_000, tz=timezone.utc).isoformat()


def build_candidate_payload(state: dict, generated_utc: str) -> dict:
    v011 = state["v011"]
    return {
        "$schema": "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v12",
        "status": STATUS,
        "generated_utc": generated_utc,
        "acknowledgement": RUN_ACK_TOKEN,
        "project_root": str(PROJECT),
        "original_authorities": copy.deepcopy(v011["original_authorities"]),
        "approved_source": copy.deepcopy(v011["approved_source"]),
        "protected_project": copy.deepcopy(v011["protected_project"]),
        "incident_chain": copy.deepcopy(v011["incident_chain"]),
        "stale_preliminary_v007": copy.deepcopy(v011["stale_preliminary_v007"]),
        "stale_preliminary_v008": copy.deepcopy(v011["stale_preliminary_v008"]),
        "exact_prior_all_file_closures": copy.deepcopy(
            v011["exact_prior_all_file_closures"]),
        "prior_quarantines": copy.deepcopy(v011["prior_quarantines"]),
        "partial_packages": copy.deepcopy(v011["partial_packages"]),
        "slot_normalization": copy.deepcopy(v011["slot_normalization"]),
        "runtime_uv_sanitization": copy.deepcopy(v011["runtime_uv_sanitization"]),
        "runtime_bounds_coordinate_conversion": copy.deepcopy(
            v011["runtime_bounds_coordinate_conversion"]),
        "exact_ue_enum_validation": copy.deepcopy(v011["exact_ue_enum_validation"]),
        "material_input_name_canonicalization": copy.deepcopy(
            v011["material_input_name_canonicalization"]),
        "completed_v009_import": copy.deepcopy(v011["completed_v009_import"]),
        "stale_unexecuted_v010": copy.deepcopy(v011["stale_unexecuted_v010"]),
        "failed_v011_validation": copy.deepcopy(state["v011_incident"]),
        "corrected_fresh_dependency_authority": {
            "material_texture_dependencies": {
                "body": copy.deepcopy(TEXTURE_DEPENDENCIES),
                "rolling_gear": copy.deepcopy(TEXTURE_DEPENDENCIES),
            },
            "module_persisted_runtime_dependencies": copy.deepcopy(
                MODULE_DEPENDENCIES),
            "exact_corrected_field_count": 6,
            "fresh_assets_canonical_sha256": ACTUAL_FRESH_ASSETS_SHA256,
            "derived_from_frozen_v009_assets_plus_exact_persisted_registry_closure": True,
        },
        "asset_registry_cache_write_suppression": {
            "required_command_line_flag": "-NoAssetRegistryCacheWrite",
            "installed_engine_source": copy.deepcopy(
                state["asset_registry_cache_source"]),
            "exact_pre_validation_snapshot": copy.deepcopy(
                state["asset_registry_cache"]),
            "exact_post_validation_snapshot_must_equal_pre_validation": True,
            "cache_write_or_orphan_delete_log_tokens_are_fatal": True,
        },
        "vehicle_model_identity": {
            "model_id": VEHICLE_MODEL_ID,
            "production_recipe_id": DEVELOPMENT_RECIPE_ID,
            "current_geometry_authority_id": CURRENT_GEOMETRY_AUTHORITY_ID,
            "lifecycle": "DEVELOPMENT__APPROVED_FOR_GAME_BUILD__NOT_FINAL_ART",
            "runtime_asset_authority": "Cairnwell2040Runtime_v001",
            "model_identity_is_independent_of_current_asset_paths": True,
            "current_asset_paths_are_revision_specific_bindings": True,
            "multiple_future_models_and_recipes_supported": True,
            "final_release_visual_lock_claimed": False,
        },
        "ubt_startup_suppression": copy.deepcopy(v011["ubt_startup_suppression"]),
        "visual_revision_policy": copy.deepcopy(v011["visual_revision_policy"]),
        "lane": copy.deepcopy(state["v012_lane"]),
        "result_topology": result_topology(),
        "policy": {
            **copy.deepcopy(v011["policy"]),
            "unreal_launch_authorized_by_freeze": False,
            "validation_only_recovery": True,
            "existing_v009_packages_are_immutable": True,
            "v011_pair_and_run_are_immutable_failed_validation_evidence": True,
            "v011_rerun_authorized": False,
            "quarantine_move_authorized": False,
            "delete_copy_import_reimport_save_authorized": False,
            "importer_process_authorized": False,
            "exactly_one_read_only_validator_process_required": True,
            "exact_six_persisted_dependency_lists_required": True,
            "no_asset_registry_cache_write_flag_required": True,
            "intermediate_cached_asset_registry_exact_invariance_required": True,
            "vehicle_model_identity_decoupled_from_asset_paths": True,
            "development_model_not_final_art": True,
            "powershell_5_1_compatible_runner_required": True,
            "exact_final_summary_and_receipt_key_sets_required": True,
            "ubt_validate_platforms_must_be_suppressed": True,
            "ubt_log_tokens_are_fatal": True,
            "post_exit_all_file_and_package_hash_closure_required": True,
            "no_write_full_candidate_payload_preflight_required": True,
        },
    }


def exact_v012_run_root(raw: str, require_exists: bool = True) -> Path:
    path = Path(raw).resolve()
    if (path.parent != RECOVERY_AUDIT_ROOT.resolve()
            or not re.fullmatch(r"\d{8}T\d{6}Z-[0-9a-f]{8}", path.name)
            or (require_exists and not path.is_dir())):
        raise RecoveryError("v012 run root identity/path drift: " + str(path))
    return path


def receipt_fixture(
        contract: dict, state: dict, run_root: Path, validator_pid: int,
        generated_utc: str = "2026-08-15T16:00:00+00:00",
        engine_version: str = "5.8.0-test") -> dict:
    receipt = prior.receipt_fixture(
        contract, state, run_root, validator_pid, generated_utc, engine_version)
    receipt["$schema"] = result_topology()["validation"]["$schema"]
    receipt["writes_authorized"] = [
        str(run_root / VALIDATION_RECEIPT), str(run_root / VALIDATION_FAILURE)]
    receipt["status"] = VALIDATION_PASS
    receipt["v011_recovery_contract_sha256"] = V011_CONTRACT_SHA256
    receipt["v011_failure_receipt_sha256"] = V011_RUN_FILES[V011_FAILURE][1]
    receipt["v011_incident_binding_sha256"] = state[
        "v011_incident"]["binding_sha256"]
    receipt["assets"] = corrected_fresh_assets(state)
    receipt["no_asset_registry_cache_write_command_line_verified"] = True
    receipt["asset_registry_cache_before"] = copy.deepcopy(
        state["asset_registry_cache"])
    receipt["asset_registry_cache_after"] = copy.deepcopy(
        state["asset_registry_cache"])
    receipt["asset_registry_cache_mutation_count"] = 0
    receipt["vehicle_model_id"] = VEHICLE_MODEL_ID
    receipt["production_recipe_id"] = DEVELOPMENT_RECIPE_ID
    receipt["current_geometry_authority_id"] = CURRENT_GEOMETRY_AUTHORITY_ID
    return receipt


def validate_v012_receipt(
        payload: dict, contract: dict, state: dict, run_root: Path) -> None:
    if prior.prior.empty_key_paths(payload) != [prior.prior.V009_EMPTY_KEY_PATH]:
        raise RecoveryError("v012 validation receipt empty-key path closure drift")
    prior.exact_iso_utc(payload.get("generated_utc"), "v012 receipt generated_utc")
    engine = payload.get("engine_version")
    if not isinstance(engine, str) or not engine.startswith(prior.ENGINE_VERSION_PREFIX):
        raise RecoveryError("v012 receipt engine version is not exact UE 5.8 authority")
    pid = payload.get("validator_process_id")
    if (type(pid) is not int or pid <= 0 or pid in (36612, V011_PROCESS_ID)
            or payload.get("process_id") != pid):
        raise RecoveryError("v012 validator/import/prior-validator process identity drift")
    integer_fields = {
        "process_id": pid, "import_process_id": 36612,
        "validator_process_id": pid, "mesh_count": 4,
        "authored_lod_count": 12, "texture_count": 3,
        "material_count": 4, "package_count": 11,
        "asset_mutation_count": 0, "import_or_reimport_process_count": 0,
        "asset_registry_cache_mutation_count": 0,
    }
    if any(type(payload.get(key)) is not int or payload[key] != value
           for key, value in integer_fields.items()):
        raise RecoveryError("v012 receipt exact integer field/type drift")
    expected = receipt_fixture(
        contract, state, run_root, pid, payload["generated_utc"], engine)
    if object_hash(payload) != object_hash(expected):
        raise RecoveryError("v012 fresh validation receipt exact content drift")


def process_fixture(
        process_id: int, log_sha256: str, stdout_sha256: str,
        stderr_sha256: str, attempts: tuple[int, int, int] = (1, 1, 1)) -> dict:
    return prior.process_fixture(
        process_id, log_sha256, stdout_sha256, stderr_sha256, attempts)


def summary_fixture(
        contract: dict, state: dict, run_root: Path, receipt: dict,
        receipt_sha256: str, process: dict,
        generated_utc: str = "2026-08-15T16:01:00+00:00") -> dict:
    recovery_sha = payload_file_sha256(contract)
    return {
        "$schema": result_topology()["summary"]["$schema"],
        "generated_utc": generated_utc,
        "status": SUMMARY_PASS,
        "acknowledgement": RUN_ACK_TOKEN,
        "run_root": str(run_root),
        "destination": str(prior.prior.DEST),
        "contract_sha256": state["contract_digest"],
        "baseline_sha256": state["baseline_digest"],
        "v009_recovery_contract_sha256": prior.prior.V009_CONTRACT_SHA256,
        "v010_recovery_contract_sha256": prior.V010_CONTRACT_SHA256,
        "v011_recovery_contract_sha256": V011_CONTRACT_SHA256,
        "recovery_contract_sha256": recovery_sha,
        "v009_run_id": prior.prior.V009_RUN_ID,
        "v011_run_id": V011_RUN_ID,
        "v009_import_receipt_sha256": prior.prior.V009_IMPORT_RECEIPT_SHA256,
        "v009_wrapper_failure_summary_sha256": prior.prior.V009_SUMMARY_SHA256,
        "v011_failure_receipt_sha256": V011_RUN_FILES[V011_FAILURE][1],
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


def validate_v012_summary(
        summary: dict, contract: dict, state: dict, run_root: Path,
        receipt: dict, receipt_sha256: str, log_hashes: dict) -> None:
    if prior.prior.empty_key_paths(summary) != []:
        raise RecoveryError("v012 final summary unexpectedly contains an empty key")
    prior.exact_iso_utc(summary.get("generated_utc"), "v012 summary generated_utc")
    process = summary.get("validation_process")
    if not isinstance(process, dict):
        raise RecoveryError("v012 final summary validation process missing")
    expected_process_keys = set(process_fixture(1, "A", "B", "C"))
    if set(process) != expected_process_keys:
        raise RecoveryError("v012 validation process exact key-set drift")
    if (type(process.get("process_id")) is not int
            or type(process.get("exit_code")) is not int):
        raise RecoveryError("v012 validation process integer type drift")
    integer_fields = {
        "editor_process_count": 1, "import_process_count": 0,
        "content_move_count": 0, "exact_ubt_command_line_matches": 0,
    }
    if any(type(summary.get(key)) is not int or summary[key] != value
           for key, value in integer_fields.items()):
        raise RecoveryError("v012 summary exact integer field/type drift")
    retry = process.get("redirected_log_read_open_retry")
    if (not isinstance(retry, dict)
            or set(retry) != {
                "log_attempts", "stdout_attempts", "stderr_attempts",
                "bounded_timeout_milliseconds"}
            or type(retry.get("bounded_timeout_milliseconds")) is not int
            or retry.get("bounded_timeout_milliseconds") != 15000
            or any(type(retry.get(key)) is not int or retry[key] <= 0
                   for key in ("log_attempts", "stdout_attempts", "stderr_attempts"))):
        raise RecoveryError("v012 log read-open retry evidence drift")
    expected_process = process_fixture(
        receipt["validator_process_id"],
        log_hashes[VALIDATOR_LOGS[0]], log_hashes[VALIDATOR_LOGS[1]],
        log_hashes[VALIDATOR_LOGS[2]],
        (retry["log_attempts"], retry["stdout_attempts"], retry["stderr_attempts"]),
    )
    expected = summary_fixture(
        contract, state, run_root, receipt, receipt_sha256,
        expected_process, summary["generated_utc"])
    if object_hash(summary) != object_hash(expected):
        raise RecoveryError("v012 final summary exact identity/process binding drift")


def expect_rejected(callback, label: str) -> None:
    try:
        callback()
    except RecoveryError:
        return
    raise RecoveryError("v012 synthetic tamper regression was accepted: " + label)


def run_synthetic_regressions(contract: dict, state: dict) -> None:
    root = exact_v012_run_root(
        str(RECOVERY_AUDIT_ROOT / "20260815T160000Z-deadbeef"),
        require_exists=False)
    receipt = receipt_fixture(contract, state, root, 424243)
    validate_v012_receipt(receipt, contract, state, root)
    missing_dependency = copy.deepcopy(receipt)
    missing_dependency["assets"]["materials"]["body"][
        "texture_dependencies"] = []
    expect_rejected(
        lambda: validate_v012_receipt(missing_dependency, contract, state, root),
        "missing body texture dependencies")
    wrong_module = copy.deepcopy(receipt)
    wrong_module["assets"]["modules"]["BIW_AutomotiveSkeleton"][
        "persisted_runtime_dependencies"] = MODULE_DEPENDENCIES[
            "BIW_UnderbodySubset"]
    expect_rejected(
        lambda: validate_v012_receipt(wrong_module, contract, state, root),
        "wrong module persisted dependency")
    changed_cache = copy.deepcopy(receipt)
    changed_cache["asset_registry_cache_after"]["files"][0]["sha256"] = "0" * 64
    expect_rejected(
        lambda: validate_v012_receipt(changed_cache, contract, state, root),
        "changed Intermediate CachedAssetRegistry snapshot")
    wrong_model = copy.deepcopy(receipt)
    wrong_model["vehicle_model_id"] = "Cairnwell2040_Development_v001"
    expect_rejected(
        lambda: validate_v012_receipt(wrong_model, contract, state, root),
        "revision-coupled vehicle model id")
    wrong_geometry = copy.deepcopy(receipt)
    wrong_geometry["current_geometry_authority_id"] = VEHICLE_MODEL_ID
    expect_rejected(
        lambda: validate_v012_receipt(wrong_geometry, contract, state, root),
        "geometry authority conflated with vehicle model id")
    bool_pid = copy.deepcopy(receipt)
    bool_pid["process_id"] = True
    bool_pid["validator_process_id"] = True
    expect_rejected(
        lambda: validate_v012_receipt(bool_pid, contract, state, root),
        "boolean receipt PID")
    receipt_sha = object_hash(receipt)
    logs = {name: str(index) * 64 for index, name in enumerate(VALIDATOR_LOGS, 1)}
    process = process_fixture(424243, *(logs[name] for name in VALIDATOR_LOGS))
    summary = summary_fixture(contract, state, root, receipt, receipt_sha, process)
    validate_v012_summary(summary, contract, state, root, receipt, receipt_sha, logs)
    missing_v011 = copy.deepcopy(summary)
    missing_v011.pop("v011_failure_receipt_sha256")
    expect_rejected(
        lambda: validate_v012_summary(
            missing_v011, contract, state, root, receipt, receipt_sha, logs),
        "missing v011 chronology")


def validate_candidate_payload(payload: dict, state: dict) -> None:
    generated = prior.exact_iso_utc(payload.get("generated_utc"), "v012 generated_utc")
    if generated != candidate_generated_utc(state):
        raise RecoveryError("v012 generated timestamp is not exact lane-state timestamp")
    if object_hash(payload) != object_hash(build_candidate_payload(state, generated)):
        raise RecoveryError("v012 full candidate payload differs from reconstruction")
    incident = copy.deepcopy(payload["failed_v011_validation"])
    declared = incident.pop("binding_sha256", None)
    if declared != object_hash(incident):
        raise RecoveryError("v012 failed-v011 incident binding hash drift")
    if (payload["lane"]["file_count"] != 62
            or payload["result_topology"]["unreal_process_count"] != 1
            or payload["result_topology"]["import_process_count"] != 0
            or payload["policy"]["v011_rerun_authorized"] is not False
            or payload["policy"]["quarantine_move_authorized"] is not False
            or payload["policy"]["importer_process_authorized"] is not False):
        raise RecoveryError("v012 lane/process/no-import safety closure drift")
    if (type(payload["lane"]["file_count"]) is not int
            or type(payload["result_topology"]["unreal_process_count"]) is not int
            or type(payload["result_topology"]["import_process_count"]) is not int):
        raise RecoveryError("v012 candidate exact integer field/type drift")
    run_synthetic_regressions(payload, state)


def dry_build_payload(require_output_absent: bool = True) -> tuple[dict, str, int]:
    if require_output_absent and (OUTPUT.exists() or OUTPUT_SHA.exists()):
        raise RecoveryError("v012 dry-build requires absent contract and sidecar")
    if RECOVERY_AUDIT_ROOT.exists():
        raise RecoveryError("v012 dry-build requires absent result root")
    state = authority_state()
    payload = build_candidate_payload(state, candidate_generated_utc(state))
    validate_candidate_payload(payload, state)
    serialized = serialized_payload(payload)
    validate_candidate_payload(strict_json_text(serialized.decode("utf-8")), state)
    return payload, hashlib.sha256(serialized).hexdigest().upper(), len(serialized)


def create_contract(acknowledgement: str) -> None:
    if acknowledgement != ACK_TOKEN:
        raise RecoveryError("exact v012 recovery-freeze acknowledgement missing")
    if OUTPUT.exists() or OUTPUT_SHA.exists():
        raise RecoveryError("refusing to overwrite v012 recovery contract or sidecar")
    payload, expected_digest, expected_size = dry_build_payload()
    serialized = serialized_payload(payload)
    if len(serialized) != expected_size:
        raise RecoveryError("v012 serialized size changed after no-write preflight")
    OUTPUT.write_text(serialized.decode("utf-8"), encoding="utf-8", newline="\n")
    digest = BASE.sha256(OUTPUT)
    if digest != expected_digest:
        raise RecoveryError("v012 written contract hash differs from dry-build")
    OUTPUT_SHA.write_text(
        f"{digest}  {OUTPUT.name}\n", encoding="ascii", newline="\n")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012_CONTRACT_FROZEN")
    print(digest)


def load_frozen() -> tuple[dict, dict]:
    state = authority_state()
    if not OUTPUT.is_file() or not OUTPUT_SHA.is_file():
        raise RecoveryError("v012 recovery contract/sidecar absent")
    digest = BASE.sha256(OUTPUT)
    if OUTPUT_SHA.read_text(encoding="ascii") != f"{digest}  {OUTPUT.name}\n":
        raise RecoveryError("v012 recovery sidecar drift")
    payload = strict_json_file(OUTPUT)
    validate_candidate_payload(payload, state)
    BASE.verify_snapshot(payload["lane"], "v012 prepared validation-only lane")
    return payload, state


def verify_pre_validation() -> None:
    payload, state = load_frozen()
    if RECOVERY_AUDIT_ROOT.exists():
        raise RecoveryError("v012 result root already exists; one-use validation consumed")
    prior.prior.verify_destination(state["imported"])
    exact_v011_pair()
    exact_v011_run_snapshot()
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
        "Asset registry cache written as", "deleted (orphaned",
        "CleanupOrphanedCacheFiles (PostWrite)",
    )
    return [token for token in tokens if token in combined]


def verify_post_validation(run_root_raw: str) -> None:
    contract, state = load_frozen()
    run_root = exact_v012_run_root(run_root_raw)
    expected = set(VALIDATOR_LOGS) | {VALIDATION_RECEIPT}
    actual = exact_run_children(run_root, expected, "v012 post-validator run")
    receipt_path = actual[VALIDATION_RECEIPT]
    receipt = strict_json_file(receipt_path)
    validate_v012_receipt(receipt, contract, state, run_root)
    combined = "\n".join(
        actual[name].read_text(encoding="utf-8", errors="replace")
        for name in VALIDATOR_LOGS)
    found = forbidden_log_tokens(combined)
    if found:
        raise RecoveryError("v012 validator fatal/build-tool log token drift: " + repr(found))
    if ("LINE_BOSS_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012_VALIDATION_PASS"
            not in combined or "Editor shut down" not in combined):
        raise RecoveryError("v012 validation PASS/natural-exit marker drift")
    prior.prior.verify_destination(state["imported"])
    verify_asset_registry_cache_snapshot()
    exact_v011_pair()
    exact_v011_run_snapshot()
    print(POST_VALIDATION_PASS)
    print(BASE.sha256(receipt_path))


def verify_final(run_root_raw: str) -> None:
    contract, state = load_frozen()
    run_root = exact_v012_run_root(run_root_raw)
    expected = set(VALIDATOR_LOGS) | {VALIDATION_RECEIPT, SUMMARY_NAME}
    actual = exact_run_children(run_root, expected, "v012 final run")
    receipt_path = actual[VALIDATION_RECEIPT]
    receipt = strict_json_file(receipt_path)
    validate_v012_receipt(receipt, contract, state, run_root)
    summary = strict_json_file(actual[SUMMARY_NAME])
    receipt_sha = BASE.sha256(receipt_path)
    log_hashes = {name: BASE.sha256(actual[name]) for name in VALIDATOR_LOGS}
    validate_v012_summary(
        summary, contract, state, run_root, receipt, receipt_sha, log_hashes)
    prior.prior.verify_destination(state["imported"])
    verify_asset_registry_cache_snapshot()
    exact_v011_pair()
    exact_v011_run_snapshot()
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
            "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012_"
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
