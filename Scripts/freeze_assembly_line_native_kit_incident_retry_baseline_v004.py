"""Freeze v004 after v003 applied an old chronological hash to live Source."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import freeze_assembly_line_native_kit_incident_retry_baseline_v003 as v003


PROJECT = v003.PROJECT
OUTPUT = PROJECT / "Scripts/assembly_line_native_kit_incident_retry_baseline_v004.json"
V003_BASELINE = PROJECT / "Scripts/assembly_line_native_kit_incident_retry_baseline_v003_final.json"
EXPECTED_V003_BASELINE_SHA256 = "A9BA9C499C5A30272BDEB2348A4D2912CEB41AD24396494F0468FA2D2B2C9276"
V004_AUDIT_RELATIVE = "Saved/Audits/AssemblyShop/AssemblyLineNativeKit_v001/IncidentRecovery_v004"
FAILED_V003_RUN_RELATIVE = (
    "Saved/Audits/AssemblyShop/AssemblyLineNativeKit_v001/IncidentRecovery_v003/20260815T032759Z-6c42095d"
)
FAILED_V003_RUN = PROJECT / FAILED_V003_RUN_RELATIVE
CURRENT_BRIDGE_HASHES = dict(v003.SETTLED_CAPTURE_BRIDGE_HASHES)
HISTORICAL_BRIDGE_HASHES = {
    "Source/LineBossCarFactory/LBOneFactoryCaptureBridge.h":
        "5D24296B0FF7239276793DCA0232DBFB239E6C393B0ED7EA2D767F15BFF7F8C8",
    "Source/LineBossCarFactory/LBOneFactoryCaptureBridge.cpp":
        "447C04E64A2F322754C6F78523A34A59D9E133B3D949B766064D9FD112F15ECD",
}
V003_STATIC_FILES = (
    "Scripts/assembly_line_native_kit_incident_retry_baseline_v003_final.json",
    "Scripts/assembly_line_native_kit_incident_retry_baseline_v003.json",
    "Scripts/freeze_assembly_line_native_kit_incident_retry_baseline_v003.py",
    "Scripts/assembly_line_native_kit_incident_retry_runtime_v003.py",
    "Scripts/revalidate_assembly_line_native_kit_incident_v003.py",
    "Scripts/run_assembly_line_native_kit_incident_retry_v003.ps1",
    "Scripts/tests/test_assembly_line_native_kit_incident_retry_v003.py",
    "Scripts/tests/test_assembly_line_native_kit_execute_python_path_v003.ps1",
    "Docs/AssemblyShop/ASSEMBLY_LINE_NATIVE_KIT_INCIDENT_RETRY_v003.md",
    "Saved/Audits/AssemblyShop/AssemblyLineNativeKit_v001/StaticPreparation_v003/incident_retry_static_freeze_v003.json",
)
EXPECTED_V003_STATIC_HASHES = dict(zip(V003_STATIC_FILES, (
    EXPECTED_V003_BASELINE_SHA256,
    "B465F68B5DC540B7C68EBCB6BD4C682271A2826A8841A902EC98FBAE3DCAA9B5",
    "A240118EF404682F7515F1CF3EA68064AFF3A873B1D499367CFD6EA3893DD96F",
    "09269AD61BFA49B11042DD1BDA63E7F7F1C10E0BDE2B4EFAC03BFD42D6CA1714",
    "FEEDE0765B6525C4847DDF6FFDCA229A5F6F0B865AA071D2D451DE0CF3807060",
    "EBD52D2C08A5B2E7B2F82075B559AB0956AAF91D20C51F77904127C889FE0F22",
    "9583873DFDE86E01A0B98181866297836F54483FCEF0C02EC5C6BA0B9D2A95D1",
    "5C6D87021F590D2E4FDDE96BF723DD9CBC0116FD7A203521EDFF5E09E1B38A43",
    "EEF27BF1D3F9408050D3B4673C1167FA2B9EEB22D359340F56D21EEB41DD13A1",
    "FCB7EB2528D90A89A9DFC42D314B9FC7A42BE0513D9C804DD1170E6BB65837F6",
)))
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


def fail(message: str) -> None:
    raise RuntimeError("ASSEMBLY_NATIVE_KIT_INCIDENT_RETRY_BASELINE_V004_FAIL: " + message)


def base_specs(payload: dict) -> tuple[dict, ...]:
    return tuple({"name": item["name"], "files": tuple(item.get("files", ())),
                  "roots": tuple(item.get("roots", ())), "allow_empty": bool(item.get("allow_empty", False))}
                 for item in payload["protected"]["groups"])


def verify_chronology(v003_payload: dict) -> dict:
    if v003.sha256(V003_BASELINE) != EXPECTED_V003_BASELINE_SHA256:
        fail("final v003 baseline changed")
    for rel, expected in EXPECTED_V003_STATIC_HASHES.items():
        if v003.sha256(PROJECT / rel) != expected:
            fail("v003 static authority changed: " + rel)
    old_rows = v003_payload["incident"]["exact_added_files"]
    if {rel: old_rows[rel]["sha256"] for rel in HISTORICAL_BRIDGE_HASHES} != HISTORICAL_BRIDGE_HASHES:
        fail("historical initial CaptureBridge hashes drifted in chronology")
    current_rows = {item["path"]: item["sha256"]
                    for item in v003_payload["settled_concurrent_source"]["files"]}
    if current_rows != CURRENT_BRIDGE_HASHES:
        fail("final v005 CaptureBridge authority drifted in successor baseline")
    for rel, expected in CURRENT_BRIDGE_HASHES.items():
        if v003.sha256(PROJECT / rel) != expected:
            fail("current frozen CaptureBridge file changed: " + rel)
    actual = {path.name: path for path in FAILED_V003_RUN.iterdir() if path.is_file()}
    if set(actual) != set(FAILED_V003_HASHES):
        fail("failed v003 evidence inventory drift")
    evidence = []
    for name, expected in FAILED_V003_HASHES.items():
        item = v003.row(actual[name])
        if item["sha256"] != expected:
            fail("failed v003 evidence changed: " + name)
        evidence.append(item)
    failure = json.loads(actual["fresh_load_recovery_validation_failure_v003.json"].read_text(encoding="utf-8-sig"))
    if (failure.get("status") != "FAIL_CLOSED__ASSEMBLY_NATIVE_KIT_INCIDENT_RETRY_V003" or
            "exact incident Source addition changed" not in failure.get("error", "") or
            failure.get("content_writes") != [] or failure.get("importer_launched") is not False):
        fail("failed v003 receipt identity drift")
    return {"classification": "V003_APPLIED_HISTORICAL_BRIDGE_HASH_TO_CURRENT_SOURCE",
            "failed_run": FAILED_V003_RUN_RELATIVE, "evidence": evidence,
            "evidence_inventory_sha256": v003.canonical_hash(evidence),
            "python_executed": True, "asset_validation_executed": False,
            "content_writes": [], "historical_bridge_hashes": HISTORICAL_BRIDGE_HASHES,
            "current_frozen_bridge_hashes": CURRENT_BRIDGE_HASHES}


def specs(payload: dict) -> tuple[dict, ...]:
    return base_specs(payload) + (
        {"name": "v003_retry_static_authority", "files": V003_STATIC_FILES},
        {"name": "failed_v003_recovery_run_exact_evidence", "roots": (FAILED_V003_RUN_RELATIVE,)},
    )


def build() -> dict:
    if Path.cwd().resolve() != PROJECT.resolve():
        fail("run from exact project root")
    if OUTPUT.exists():
        fail("refusing to overwrite v004 baseline")
    if (PROJECT / V004_AUDIT_RELATIVE).exists():
        fail("v004 result namespace already exists")
    predecessor = json.loads(V003_BASELINE.read_text(encoding="utf-8-sig"))
    retry = verify_chronology(predecessor)
    groups, rows = v003.protected_inventory(specs(predecessor))
    return {"$schema": "lineboss/assembly-native-kit-v001/incident-retry-baseline/v4",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "status": "FROZEN__ASSEMBLY_NATIVE_KIT_V001_INCIDENT_RETRY_BASELINE_V004__CHRONOLOGY_SEPARATED_FROM_CURRENT_SOURCE",
            "project": predecessor["project"], "incident": predecessor["incident"],
            "retry_incident": predecessor["retry_incident"], "retry_v003_incident": retry,
            "settled_concurrent_source": predecessor["settled_concurrent_source"],
            "source": predecessor["source"], "assets": predecessor["assets"],
            "import_contract": predecessor["import_contract"], "destination": predecessor["destination"],
            "protected": {"groups": groups, "files": rows, "file_count": len(rows),
                          "inventory_sha256": v003.canonical_hash(rows),
                          "maps": predecessor["protected"]["maps"]},
            "command_line_contract": predecessor["command_line_contract"],
            "policy": {**predecessor["policy"], "v003_retry_authorized": False,
                       "v004_retry_authorized": True, "historical_hashes_applied_to_live_files": False}}


def verify() -> dict:
    if not OUTPUT.is_file():
        fail("verify-only requires v004 baseline")
    payload = json.loads(OUTPUT.read_text(encoding="utf-8-sig"))
    predecessor = json.loads(V003_BASELINE.read_text(encoding="utf-8-sig"))
    verify_chronology(predecessor)
    groups, rows = v003.protected_inventory(specs(predecessor))
    wanted_groups = {item["name"]: item for item in payload["protected"]["groups"]}
    if {item["name"] for item in groups} != set(wanted_groups):
        fail("protected group inventory drift")
    for group in groups:
        if group["paths"] != wanted_groups[group["name"]]["paths"]:
            fail("protected group path drift: " + group["name"])
    wanted = {item["path"]: item for item in payload["protected"]["files"]}
    if {item["path"] for item in rows} != set(wanted):
        fail("protected union drift")
    for item in rows:
        expected = wanted[item["path"]]
        if any(item[key] != expected[key] for key in ("bytes", "mtime_ns", "sha256")):
            fail("protected file drift: " + item["path"])
    digest = v003.canonical_hash(rows)
    if digest != payload["protected"]["inventory_sha256"]:
        fail("protected inventory hash drift")
    return {"status": "PASS__V004_CHRONOLOGY_SEPARATED_BASELINE_FULL_REVERIFY",
            "baseline_sha256": v003.sha256(OUTPUT), "source_files": 278,
            "target_packages": 8, "protected_files": len(rows),
            "protected_inventory_sha256": digest, "failed_v002_evidence_files": 4,
            "failed_v003_evidence_files": 5}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        print(json.dumps(verify(), indent=2))
    else:
        payload = build()
        OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": payload["status"], "path": str(OUTPUT),
                          "sha256": v003.sha256(OUTPUT),
                          "protected_files": payload["protected"]["file_count"]}, indent=2))


if __name__ == "__main__":
    main()
