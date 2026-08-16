"""Shared read-only runtime for command-line-safe Assembly recovery v003."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import unreal

SCRIPTS = Path(unreal.Paths.project_dir()).resolve() / "Scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import assembly_line_native_kit_incident_recovery_runtime_v002 as v002


PROJECT = v002.PROJECT
EXPECTED_PROJECT = v002.EXPECTED_PROJECT
BASELINE = PROJECT / "Scripts/assembly_line_native_kit_incident_retry_baseline_v003_final.json"
EXPECTED_BASELINE_SHA256 = "A9BA9C499C5A30272BDEB2348A4D2912CEB41AD24396494F0468FA2D2B2C9276"
EXPECTED_STATUS = "FROZEN__ASSEMBLY_NATIVE_KIT_V001_INCIDENT_RETRY_BASELINE_V003__FORWARD_SLASH_EXECUTE_PATH"
AUDIT_ROOT = PROJECT / "Saved/Audits/AssemblyShop/AssemblyLineNativeKit_v001/IncidentRecovery_v003"
RUN_ROOT_ENV = "LINEBOSS_ASSEMBLY_NATIVE_KIT_INCIDENT_RECOVERY_V003_RUN_ROOT"
ACK_ENV = "LINEBOSS_ASSEMBLY_NATIVE_KIT_INCIDENT_RECOVERY_V003_ACK"
ACK_TOKEN = "REVALIDATE_EXISTING_ASSEMBLY_NATIVE_KIT_V001_INCIDENT_V003_ONCE"
PASS_RECEIPT = "fresh_load_recovery_validation_receipt_v003.json"
FAIL_RECEIPT = "fresh_load_recovery_validation_failure_v003.json"
SUMMARY = "incident_recovery_summary_v003.json"
RESULT_NAMES = {PASS_RECEIPT, FAIL_RECEIPT, SUMMARY}
FAILED_V002_RUN = PROJECT / (
    "Saved/Audits/AssemblyShop/AssemblyLineNativeKit_v001/IncidentRecovery_v002/20260815T030646Z-e8c9a5eb"
)
FAILED_V002_HASHES = {
    "fresh_load_recovery_validation.log": "9BC7F87884532B794F4FB49D9B13082A6ED4C48D0C46325730E2DBB4E78E9B72",
    "fresh_load_recovery_validation.stderr.log": "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
    "fresh_load_recovery_validation.stdout.log": "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
    "incident_recovery_summary_v002.json": "CEBFD5239081C66FFCEEE84FCDB593DE5D588D01C06B4B6B5F89CEE7FD3362EC",
}

library = v002.library
sha256 = v002.sha256
relative = v002.relative
file_row = v002.file_row
verify_source = v002.verify_source
verify_protected = v002.verify_protected
namespace_inventory = v002.namespace_inventory
validate_mesh = v002.validate_mesh
DEST = v002.DEST
DEST_DISK = v002.DEST_DISK
ORIGINAL_IMPORT_RECEIPT = v002.ORIGINAL_IMPORT_RECEIPT
EXPECTED_IMPORT_RECEIPT_SHA256 = v002.EXPECTED_IMPORT_RECEIPT_SHA256


def fail(message: str) -> None:
    raise RuntimeError("ASSEMBLY_NATIVE_KIT_INCIDENT_RETRY_V003_FAIL: " + message)


def run_root() -> Path:
    raw = os.environ.get(RUN_ROOT_ENV, "").strip()
    if not raw or os.environ.get(ACK_ENV, "").strip() != ACK_TOKEN:
        fail("guarded v003 runner environment/acknowledgement absent")
    path = Path(raw).resolve()
    if path == AUDIT_ROOT.resolve() or not v002.original.inside(path, AUDIT_ROOT) or not path.is_dir():
        fail("v003 run root escapes or is absent")
    return path


def load_baseline() -> dict:
    if PROJECT != EXPECTED_PROJECT or str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("project/game identity drift")
    if not BASELINE.is_file() or sha256(BASELINE) != EXPECTED_BASELINE_SHA256:
        fail("v003 retry baseline absent or changed")
    payload = json.loads(BASELINE.read_text(encoding="utf-8-sig"))
    command = payload.get("command_line_contract", {})
    if (payload.get("$schema") != "lineboss/assembly-native-kit-v001/incident-retry-baseline/v3" or
            payload.get("status") != EXPECTED_STATUS or payload.get("destination", {}).get("namespace") != DEST or
            command.get("execute_python_path_separator") != "/" or
            command.get("backslash_or_control_character_authorized") is not False):
        fail("v003 baseline identity/command-line contract drift")
    policy = payload.get("policy", {})
    if (policy.get("importer_authorized") is not False or policy.get("content_writes_authorized") is not False or
            policy.get("asset_or_level_saves_authorized") is not False or
            policy.get("v002_retry_authorized") is not False or policy.get("v003_retry_authorized") is not True):
        fail("v003 read-only/one-use policy drift")
    return payload


def prior_results() -> list[str]:
    if not AUDIT_ROOT.is_dir():
        return []
    return sorted(relative(path) for path in AUDIT_ROOT.rglob("*") if path.is_file() and path.name in RESULT_NAMES)


def verify_retry_incident(baseline: dict) -> dict:
    inherited = v002.verify_incident(baseline)
    actual_files = {path.name: path for path in FAILED_V002_RUN.iterdir() if path.is_file()}
    if set(actual_files) != set(FAILED_V002_HASHES):
        fail("failed v002 evidence inventory drift")
    evidence = {}
    for name, expected in FAILED_V002_HASHES.items():
        item = file_row(actual_files[name])
        if item["sha256"] != expected:
            fail("failed v002 evidence changed: " + name)
        evidence[name] = item
    log_bytes = actual_files["fresh_load_recovery_validation.log"].read_bytes()
    control_fragment = b"Scripts" + bytes([13]) + b"evalidate_assembly_line_native_kit_incident_v002.py"
    if b"Could not load Python file" not in log_bytes or control_fragment not in log_bytes:
        fail("v002 command-line carriage-return evidence drift")
    return {**inherited, "failed_v002_recovery_evidence": evidence,
            "failed_v002_python_executed": False, "failed_v002_content_writes": []}
