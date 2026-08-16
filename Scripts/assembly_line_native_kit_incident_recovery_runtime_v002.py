"""Shared read-only runtime for the Assembly native-kit incident recovery v002."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import unreal

SCRIPTS = Path(unreal.Paths.project_dir()).resolve() / "Scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import assembly_line_native_kit_unreal_runtime_v001 as original


PROJECT = original.PROJECT
EXPECTED_PROJECT = original.EXPECTED_PROJECT
BASELINE = PROJECT / "Scripts/assembly_line_native_kit_incident_recovery_baseline_v002.json"
EXPECTED_BASELINE_SHA256 = "CDD41027FCBB556ED3A3EF472B804275677F023CDCCA8D394DC454BBF94C1520"
EXPECTED_STATUS = "FROZEN__ASSEMBLY_NATIVE_KIT_V001_INCIDENT_RECOVERY_BASELINE_V002__READ_ONLY_REVALIDATION_ONLY"
AUDIT_ROOT = PROJECT / "Saved/Audits/AssemblyShop/AssemblyLineNativeKit_v001/IncidentRecovery_v002"
RUN_ROOT_ENV = "LINEBOSS_ASSEMBLY_NATIVE_KIT_INCIDENT_RECOVERY_V002_RUN_ROOT"
ACK_ENV = "LINEBOSS_ASSEMBLY_NATIVE_KIT_INCIDENT_RECOVERY_V002_ACK"
ACK_TOKEN = "REVALIDATE_EXISTING_ASSEMBLY_NATIVE_KIT_V001_INCIDENT_V002_ONCE"
PASS_RECEIPT = "fresh_load_recovery_validation_receipt_v002.json"
FAIL_RECEIPT = "fresh_load_recovery_validation_failure_v002.json"
SUMMARY = "incident_recovery_summary_v002.json"
RESULT_NAMES = {PASS_RECEIPT, FAIL_RECEIPT, SUMMARY}
ORIGINAL_IMPORT_RECEIPT = PROJECT / (
    "Saved/Audits/AssemblyShop/AssemblyLineNativeKit_v001/UnrealImportLane_v001/"
    "20260815T025138Z-2b421583/import_receipt_v001.json"
)
EXPECTED_IMPORT_RECEIPT_SHA256 = "C0E1F8D3E7B6EEBB2780067671AF408C53368DEA9370B3AA56B9F7F3AAFD49F7"
SOURCE_ADDITIONS = {
    "Source/LineBossCarFactory/LBOneFactoryCaptureBridge.h": "5D24296B0FF7239276793DCA0232DBFB239E6C393B0ED7EA2D767F15BFF7F8C8",
    "Source/LineBossCarFactory/LBOneFactoryCaptureBridge.cpp": "447C04E64A2F322754C6F78523A34A59D9E133B3D949B766064D9FD112F15ECD",
}

library = original.library
sha256 = original.sha256
relative = original.relative
file_row = original.file_row
canonical_hash = original.canonical_hash
verify_source = original.verify_source
verify_protected = original.verify_protected
namespace_inventory = original.namespace_inventory
validate_mesh = original.validate_mesh
DEST = original.DEST
DEST_DISK = original.DEST_DISK


def fail(message: str) -> None:
    raise RuntimeError("ASSEMBLY_NATIVE_KIT_INCIDENT_RECOVERY_V002_FAIL: " + message)


def run_root() -> Path:
    raw = os.environ.get(RUN_ROOT_ENV, "").strip()
    if not raw or os.environ.get(ACK_ENV, "").strip() != ACK_TOKEN:
        fail("guarded successor runner environment/acknowledgement absent")
    path = Path(raw).resolve()
    if path == AUDIT_ROOT.resolve() or not original.inside(path, AUDIT_ROOT) or not path.is_dir():
        fail("successor run root escapes or is absent")
    return path


def load_baseline() -> dict:
    if PROJECT != EXPECTED_PROJECT or str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("project/game identity drift")
    if not BASELINE.is_file() or sha256(BASELINE) != EXPECTED_BASELINE_SHA256:
        fail("successor baseline absent or changed")
    payload = json.loads(BASELINE.read_text(encoding="utf-8-sig"))
    if (payload.get("$schema") != "lineboss/assembly-native-kit-v001/incident-recovery-baseline/v2" or
            payload.get("status") != EXPECTED_STATUS or payload.get("destination", {}).get("namespace") != DEST or
            payload.get("destination", {}).get("state") != "EXISTING_EXACT_PASS_IMPORT__READ_ONLY"):
        fail("successor baseline identity/destination drift")
    policy = payload.get("policy", {})
    if (policy.get("importer_authorized") is not False or policy.get("content_writes_authorized") is not False or
            policy.get("asset_or_level_saves_authorized") is not False or
            policy.get("reimport_delete_overwrite_authorized") is not False or
            policy.get("independent_fresh_process_required") is not True):
        fail("successor read-only policy drift")
    return payload


def prior_results() -> list[str]:
    if not AUDIT_ROOT.is_dir():
        return []
    return sorted(relative(path) for path in AUDIT_ROOT.rglob("*") if path.is_file() and path.name in RESULT_NAMES)


def verify_incident(baseline: dict) -> dict:
    if sha256(ORIGINAL_IMPORT_RECEIPT) != EXPECTED_IMPORT_RECEIPT_SHA256:
        fail("original PASS import receipt changed")
    imported = json.loads(ORIGINAL_IMPORT_RECEIPT.read_text(encoding="utf-8-sig"))
    incident = baseline["incident"]
    if (imported.get("status") != "PASS__HASH_GUARDED_FRESH_IMPORT__8_ASSETS__24_AUTHORED_LODS__ASSEMBLY_NATIVE_KIT_V001" or
            imported.get("asset_count") != 8 or imported.get("lod_count_per_asset") != 3 or
            imported.get("custom_lods_appended") != 16):
        fail("original PASS import receipt contract drift")
    additions = {}
    for rel, expected in SOURCE_ADDITIONS.items():
        actual = file_row(PROJECT / rel)
        if actual["sha256"] != expected:
            fail("exact incident Source addition changed: " + rel)
        additions[rel] = actual
    source_paths = {relative(path) for path in (PROJECT / "Source").rglob("*") if path.is_file()}
    if len(source_paths) != 278 or set(incident["exact_added_files"]) != set(additions):
        fail("settled 278-file Source incident identity drift")
    target = namespace_inventory()
    wanted_rows = {item["path"]: {key: item[key] for key in ("bytes", "mtime_ns", "sha256")}
                   for item in incident["target_packages"]}
    if target != wanted_rows or target != imported["namespace_disk_files"]:
        fail("existing eight-package import hash/metadata drift")
    return {"source_count": len(source_paths), "exact_source_additions": additions,
            "target_packages": target, "original_import_receipt_sha256": EXPECTED_IMPORT_RECEIPT_SHA256,
            "original_import_process_id": imported["process_id"]}
