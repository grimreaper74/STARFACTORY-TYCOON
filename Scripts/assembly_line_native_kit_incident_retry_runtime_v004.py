"""Read-only Assembly v004 runtime with chronology separated from live Source."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import unreal

SCRIPTS = Path(unreal.Paths.project_dir()).resolve() / "Scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import assembly_line_native_kit_incident_retry_runtime_v003 as v003


PROJECT = v003.PROJECT
EXPECTED_PROJECT = v003.EXPECTED_PROJECT
BASELINE = PROJECT / "Scripts/assembly_line_native_kit_incident_retry_baseline_v004.json"
EXPECTED_BASELINE_SHA256 = "15E08E11108B4877F97DFC507F27840050352FF44F19833E7FCA2EEDC9D2EAEC"
EXPECTED_STATUS = (
    "FROZEN__ASSEMBLY_NATIVE_KIT_V001_INCIDENT_RETRY_BASELINE_V004__"
    "CHRONOLOGY_SEPARATED_FROM_CURRENT_SOURCE"
)
AUDIT_ROOT = PROJECT / "Saved/Audits/AssemblyShop/AssemblyLineNativeKit_v001/IncidentRecovery_v004"
RUN_ROOT_ENV = "LINEBOSS_ASSEMBLY_NATIVE_KIT_INCIDENT_RECOVERY_V004_RUN_ROOT"
ACK_ENV = "LINEBOSS_ASSEMBLY_NATIVE_KIT_INCIDENT_RECOVERY_V004_ACK"
ACK_TOKEN = "REVALIDATE_EXISTING_ASSEMBLY_NATIVE_KIT_V001_INCIDENT_V004_ONCE"
PASS_RECEIPT = "fresh_load_recovery_validation_receipt_v004.json"
FAIL_RECEIPT = "fresh_load_recovery_validation_failure_v004.json"
SUMMARY = "incident_recovery_summary_v004.json"
RESULT_NAMES = {PASS_RECEIPT, FAIL_RECEIPT, SUMMARY}
FAILED_V003_RUN = PROJECT / (
    "Saved/Audits/AssemblyShop/AssemblyLineNativeKit_v001/IncidentRecovery_v003/20260815T032759Z-6c42095d"
)
FAILED_V003_HASHES = {
    "fresh_load_recovery_validation_failure_v003.json":
        "6483892E83834472030E513B401B86DD5FA2E2A69B0C43FFA553DFEAAF6B2143",
    "fresh_load_recovery_validation.log":
        "896C9EC609C5D268334C00BA3D6C977C303EBC04E044BA3293C1CE7B1E51C25F",
    "fresh_load_recovery_validation.stderr.log":
        "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
    "fresh_load_recovery_validation.stdout.log":
        "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
    "incident_recovery_summary_v003.json":
        "046F877BF247055C7739A29FE8BC9D37C0A6FEB2EB5452977CDD4641915EFA1F",
}
HISTORICAL_BRIDGE_HASHES = dict(v003.v002.SOURCE_ADDITIONS)
CURRENT_BRIDGE_HASHES = {
    "Source/LineBossCarFactory/LBOneFactoryCaptureBridge.h":
        "2C5442B15B94504CEA085A3F46F4740BCC4FD0A83CDE70DB37E3C7D0FC04673B",
    "Source/LineBossCarFactory/LBOneFactoryCaptureBridge.cpp":
        "849C7E1ACD6A02B27126831202E774E8C922E422050904EC3DF5349C6D01CA30",
}

library = v003.library
sha256 = v003.sha256
relative = v003.relative
file_row = v003.file_row
verify_source = v003.verify_source
verify_protected = v003.verify_protected
namespace_inventory = v003.namespace_inventory
validate_mesh = v003.validate_mesh
DEST = v003.DEST
DEST_DISK = v003.DEST_DISK
ORIGINAL_IMPORT_RECEIPT = v003.ORIGINAL_IMPORT_RECEIPT
EXPECTED_IMPORT_RECEIPT_SHA256 = v003.EXPECTED_IMPORT_RECEIPT_SHA256


def fail(message: str) -> None:
    raise RuntimeError("ASSEMBLY_NATIVE_KIT_INCIDENT_RETRY_V004_FAIL: " + message)


def run_root() -> Path:
    raw = os.environ.get(RUN_ROOT_ENV, "").strip()
    if not raw or os.environ.get(ACK_ENV, "").strip() != ACK_TOKEN:
        fail("guarded v004 runner environment/acknowledgement absent")
    path = Path(raw).resolve()
    if path == AUDIT_ROOT.resolve() or not v003.v002.original.inside(path, AUDIT_ROOT) or not path.is_dir():
        fail("v004 run root escapes or is absent")
    return path


def load_baseline() -> dict:
    if PROJECT != EXPECTED_PROJECT or str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("project/game identity drift")
    if not BASELINE.is_file() or sha256(BASELINE) != EXPECTED_BASELINE_SHA256:
        fail("v004 baseline absent or changed")
    payload = json.loads(BASELINE.read_text(encoding="utf-8-sig"))
    command = payload.get("command_line_contract", {})
    if (payload.get("$schema") != "lineboss/assembly-native-kit-v001/incident-retry-baseline/v4" or
            payload.get("status") != EXPECTED_STATUS or
            payload.get("destination", {}).get("namespace") != DEST or
            command.get("execute_python_path_separator") != "/" or
            command.get("backslash_or_control_character_authorized") is not False):
        fail("v004 baseline identity/command contract drift")
    policy = payload.get("policy", {})
    if (policy.get("importer_authorized") is not False or
            policy.get("content_writes_authorized") is not False or
            policy.get("asset_or_level_saves_authorized") is not False or
            policy.get("v003_retry_authorized") is not False or
            policy.get("v004_retry_authorized") is not True or
            policy.get("historical_hashes_applied_to_live_files") is not False):
        fail("v004 read-only/chronology policy drift")
    return payload


def prior_results() -> list[str]:
    if not AUDIT_ROOT.is_dir():
        return []
    return sorted(relative(path) for path in AUDIT_ROOT.rglob("*")
                  if path.is_file() and path.name in RESULT_NAMES)


def _exact_evidence(root: Path, expected: dict[str, str], label: str) -> dict:
    actual = {path.name: path for path in root.iterdir() if path.is_file()}
    if set(actual) != set(expected):
        fail(label + " evidence inventory drift")
    rows = {}
    for name, digest in expected.items():
        item = file_row(actual[name])
        if item["sha256"] != digest:
            fail(label + " evidence changed: " + name)
        rows[name] = item
    return rows


def verify_chronology_and_current(baseline: dict) -> dict:
    if sha256(ORIGINAL_IMPORT_RECEIPT) != EXPECTED_IMPORT_RECEIPT_SHA256:
        fail("original PASS import receipt changed")
    imported = json.loads(ORIGINAL_IMPORT_RECEIPT.read_text(encoding="utf-8-sig"))
    if (imported.get("status") !=
            "PASS__HASH_GUARDED_FRESH_IMPORT__8_ASSETS__24_AUTHORED_LODS__ASSEMBLY_NATIVE_KIT_V001" or
            imported.get("asset_count") != 8 or imported.get("lod_count_per_asset") != 3 or
            imported.get("custom_lods_appended") != 16):
        fail("original PASS import contract drift")

    historical_rows = baseline["incident"]["exact_added_files"]
    recorded_historical = {rel: historical_rows[rel]["sha256"] for rel in HISTORICAL_BRIDGE_HASHES}
    if recorded_historical != HISTORICAL_BRIDGE_HASHES:
        fail("historical CaptureBridge chronology drift")
    successor_rows = {item["path"]: item["sha256"]
                      for item in baseline["settled_concurrent_source"]["files"]}
    if successor_rows != CURRENT_BRIDGE_HASHES:
        fail("successor baseline current CaptureBridge hashes drift")
    current = {}
    for rel, expected in CURRENT_BRIDGE_HASHES.items():
        item = file_row(PROJECT / rel)
        if item["sha256"] != expected:
            fail("current frozen CaptureBridge changed: " + rel)
        current[rel] = item
    source_paths = {relative(path) for path in (PROJECT / "Source").rglob("*") if path.is_file()}
    if len(source_paths) != 278:
        fail("current Source file count is not 278")

    target = namespace_inventory()
    wanted = {item["path"]: {key: item[key] for key in ("bytes", "mtime_ns", "sha256")}
              for item in baseline["incident"]["target_packages"]}
    if target != wanted or target != imported["namespace_disk_files"]:
        fail("existing eight-package import hash/metadata drift")

    v002_evidence = _exact_evidence(v003.FAILED_V002_RUN, v003.FAILED_V002_HASHES, "failed v002")
    v002_log = v003.FAILED_V002_RUN / "fresh_load_recovery_validation.log"
    if b"Scripts" + bytes([13]) + b"evalidate_assembly_line_native_kit_incident_v002.py" not in v002_log.read_bytes():
        fail("failed v002 carriage-return proof drift")
    v003_evidence = _exact_evidence(FAILED_V003_RUN, FAILED_V003_HASHES, "failed v003")
    v003_failure = json.loads(
        (FAILED_V003_RUN / "fresh_load_recovery_validation_failure_v003.json").read_text(encoding="utf-8-sig")
    )
    if (v003_failure.get("status") != "FAIL_CLOSED__ASSEMBLY_NATIVE_KIT_INCIDENT_RETRY_V003" or
            "exact incident Source addition changed" not in v003_failure.get("error", "") or
            v003_failure.get("content_writes") != [] or v003_failure.get("importer_launched") is not False):
        fail("failed v003 chronology receipt drift")
    return {"source_count": len(source_paths), "historical_bridge_hashes": recorded_historical,
            "current_bridge_files": current, "target_packages": target,
            "original_import_receipt_sha256": EXPECTED_IMPORT_RECEIPT_SHA256,
            "original_import_process_id": imported["process_id"],
            "failed_v002_evidence": v002_evidence, "failed_v003_evidence": v003_evidence,
            "historical_hashes_applied_to_current_files": False}
